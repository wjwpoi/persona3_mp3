/**
 * Persona 3 Reload (P3R) Opening Animation 1:1 Screen-Accurate Hi-Fi MP3 Player Firmware (Rev 2.4)
 * Hardware (Rev 2.4 Short-Body):
 *   - Waveshare ESP32-S3-Zero (No-Header Bare Board, Dual-Core 240MHz, 4MB QIO Flash, 2MB QSPI PSRAM, Native USB 2.0 OTG)
 *   - PCM5102A 32-Bit/384kHz I2S DAC + TPA6132A2 DirectPath Headphone Amp (-6dB Gain Stage) on Main PCB -X Wing
 *   - 2.25" 76x284 ST7789P3 SPI Bar IPS/TFT Display (8-Pin 0.5mm FPC -> C2856797)
 *   - TF-01A MicroSD Card Slot + AO3401A Q3 GP14 Peripheral Power Gate + GP15 (ADC2_CH4) 1:1 VBAT Divider
 *   - 551255 350-400mAh (compat 601260) Polymer LiPo Battery + K1 Long-Press Deep-Sleep Off / Wakeup
 */

#include <Arduino.h>
#include <vector>
#include <algorithm>
#include <SPI.h>
#include <SD.h>
#include <Update.h>
#include <Preferences.h>
#include "esp_sleep.h"
#include "driver/gpio.h"
#include "driver/rtc_io.h"
#include <LovyanGFX.hpp>
#include "Audio.h"
#if defined(CONFIG_IDF_TARGET_ESP32S3)
#include "USB.h"
#include "USBMSC.h"
#endif
#include "p3r_ui_assets.h"

// ============================================================================
// LOVYANGFX 2.25" 76x284 ST7789P3 BAR IPS/TFT CONFIGURATION (SPI2 / FSPI)
// ============================================================================
class LGFX_P3R : public lgfx::LGFX_Device {
    lgfx::Panel_ST7789 _panel_instance;
    lgfx::Bus_SPI      _bus_instance;
    lgfx::Light_PWM    _light_instance;

public:
    LGFX_P3R() {
        {
            auto cfg = _bus_instance.config();
            cfg.spi_host = SPI2_HOST;
            cfg.spi_mode = 3; // ST7789P3 requires SPI Mode 3 (CPOL=1, CPHA=1) when CS is tied LOW
            cfg.freq_write = 40000000;
            cfg.freq_read  = 16000000;
            cfg.spi_3wire  = false;
            cfg.use_lock   = true;
            cfg.dma_channel = SPI_DMA_CH_AUTO;
            cfg.pin_sclk = PIN_TFT_SCLK;
            cfg.pin_mosi = PIN_TFT_MOSI;
            cfg.pin_miso = -1;
            cfg.pin_dc   = PIN_TFT_DC;
            _bus_instance.config(cfg);
            _panel_instance.setBus(&_bus_instance);
        }
        {
            auto cfg = _panel_instance.config();
            cfg.pin_cs          = PIN_TFT_CS;
            cfg.pin_rst         = PIN_TFT_RST;
            cfg.pin_busy        = -1;
            cfg.panel_width     = 76;
            cfg.panel_height    = 284;
            cfg.offset_x        = 82;
            cfg.offset_y        = 18;
            cfg.offset_rotation = 0;
            cfg.dummy_read_pixel = 8;
            cfg.dummy_read_bits  = 1;
            cfg.readable        = false;
            cfg.invert          = true;  // Standard for ST7789P3 IPS bar panels
            cfg.rgb_order       = false;
            cfg.dlen_16bit      = false;
            cfg.bus_shared      = false;
            _panel_instance.config(cfg);
        }
        {
            auto cfg = _light_instance.config();
            cfg.pin_bl      = PIN_TFT_BLK;
            cfg.invert      = true;  // High-side P-MOS (Q1 AO3401A) active-LOW backlight switch
            cfg.freq        = 32000; // >20kHz ultrasonic PWM eliminates acoustic coil/MLCC whine
            cfg.pwm_channel = 7;
            _light_instance.config(cfg);
            _panel_instance.setLight(&_light_instance);
        }
        setPanel(&_panel_instance);
    }
};

static LGFX_P3R tft;
static LGFX_Sprite canvas(&tft); // Offscreen 284x76 double-buffer for tear-free 60fps roll
static Preferences p3rPrefs;

Audio audio;
#if defined(CONFIG_IDF_TARGET_ESP32S3)
USBMSC msc;
static volatile bool usbExitRequested = false;
static bool usbExitConfirmPending = false;
static uint32_t usbExitConfirmExpireMs = 0;
#endif

// Note: MicroSD uses SPI3_HOST so it never contends with TFT's SPI2_HOST!
static SPIClass sdSPI(HSPI);

enum PlayerMode {
    MODE_SD_HIFI_PLAYER = 0,
    MODE_USB_FLASH_DRIVE = 1
};

enum UIMode {
    UI_P3R_ANIME_GREY_LCD = 0, // 1:1 P3R Opening Light-Grey LCD (#D4DCE0 bg, #12161A ink)
    UI_P3R_OFFICIAL_BLUE  = 1  // Official Model Cyan-Blue LCD (#A4CDD9 bg, #0C1820 ink)
};

struct HiFiEQPreset {
    const char* name;
    int8_t bassDb;
    int8_t midDb;
    int8_t trebleDb;
};

static const HiFiEQPreset P3R_HIFI_EQ_PRESETS[4] = {
    {"CLEAR BASS+", +5, +1, +3},
    {"VOCAL BOOST", +1, +4, +3},
    {"DARK HOUR",   +6,  0, +2},
    {"HIFI DIRECT",  0,  0,  0}
};

static PlayerMode currentMode = MODE_SD_HIFI_PLAYER;
static UIMode currentUIMode = UI_P3R_ANIME_GREY_LCD;
static uint8_t currentEQIdx = 0;
static size_t currentTrackIdx = 0;
static size_t prevTrackIdx = 0;
static bool isPlaying = true;
static bool isRepeatLoop = true;
static bool isShuffleMode = false; // false = Sequential Loop (↻), true = Shuffle (⇄)
static bool sdMounted = false;
static bool usbMscActive = false;
static volatile bool trackFinishedFlag = false;
static uint8_t currentVolume = 16; // 0..21
static uint32_t elapsedSec = 96;   // Starts at 01:36 ("Burn My Dread")
static uint32_t prevElapsedSec = 96;
static uint32_t lastTickMs = 0;
static uint32_t lastFrameMs = 0;
static uint32_t lastUserActivityMs = 0;
static uint32_t lastVolChangeMs = 0;
static bool isDisplaySleeping = false;
static uint32_t vbatMv = 0;
static bool vbatValid = false;
static uint8_t batFillPx = 18;
static uint32_t lastBatSampleMs = 0;
static uint8_t lowBatStreak = 0;

struct DynamicTrack {
    String path;
    String displayTitle;
    uint32_t fallbackSec;
};

static std::vector<DynamicTrack> playlist;

// Whole-Screen Vertical Page-Roll State (60fps Ease-Out Cubic across 76px height)
static bool isPageRolling = false;
static int8_t rollDirection = 1;
static float rollProgress = 0.0f;
static uint8_t audioBars[8] = {5, 7, 4, 8, 6, 7, 3, 5};

// ============================================================================
// ESP32-S3 NATIVE USB MASS STORAGE (U盘直传免拆卡模式) CALLBACKS
// ============================================================================
#if defined(CONFIG_IDF_TARGET_ESP32S3)
static bool usbSectorTransfer(bool isWrite, uint32_t lba, uint32_t offset, uint8_t* buffer, uint32_t bufsize) {
    const uint32_t secSize = SD.sectorSize();
    const uint64_t totalSectors = SD.numSectors();
    if (secSize == 0 || secSize > 512 || buffer == nullptr || bufsize == 0) return false;

    uint64_t byteOffset = (uint64_t)offset;
    uint32_t remaining = bufsize;
    uint8_t* ptr = buffer;
    uint8_t scratch[512];

    while (remaining > 0) {
        uint64_t curLba = (uint64_t)lba + (byteOffset / secSize);
        uint32_t inSecOff = (uint32_t)(byteOffset % secSize);
        if (curLba >= totalSectors) return false;

        uint32_t chunk = secSize - inSecOff;
        if (chunk > remaining) chunk = remaining;

        if (inSecOff == 0 && chunk == secSize) {
            bool ok = isWrite ? SD.writeRAW(ptr, (uint32_t)curLba) : SD.readRAW(ptr, (uint32_t)curLba);
            if (!ok) return false;
        } else {
            if (!SD.readRAW(scratch, (uint32_t)curLba)) return false;
            if (isWrite) {
                memcpy(scratch + inSecOff, ptr, chunk);
                if (!SD.writeRAW(scratch, (uint32_t)curLba)) return false;
            } else {
                memcpy(ptr, scratch + inSecOff, chunk);
            }
        }
        ptr += chunk;
        byteOffset += chunk;
        remaining -= chunk;
    }
    return true;
}

static int32_t onUSBRead(uint32_t lba, uint32_t offset, void* buffer, uint32_t bufsize) {
    return usbSectorTransfer(false, lba, offset, (uint8_t*)buffer, bufsize) ? (int32_t)bufsize : -1;
}

static int32_t onUSBWrite(uint32_t lba, uint32_t offset, uint8_t* buffer, uint32_t bufsize) {
    return usbSectorTransfer(true, lba, offset, buffer, bufsize) ? (int32_t)bufsize : -1;
}

static bool onUSBStartStop(uint8_t power_condition, bool start, bool load_eject) {
    if (load_eject && !start) {
        usbExitRequested = true;
    }
    return true;
}
#endif

// ============================================================================
// SD CARD PLAYLIST SCANNING, SORTING & "01_" PREFIX STRIPPING
// ============================================================================
static String getBasename(const String& path) {
    int slashIdx = path.lastIndexOf('/');
    return (slashIdx >= 0) ? path.substring(slashIdx + 1) : path;
}

static bool isAudioFile(const String& name) {
    String base = getBasename(name);
    if (base.startsWith(".") || base.equalsIgnoreCase("update.bin")) return false;
    String lower = base;
    lower.toLowerCase();
    return lower.endsWith(".mp3") || lower.endsWith(".flac") || lower.endsWith(".wav");
}

static String stripTrackPrefix(const String& rawPath) {
    String name = getBasename(rawPath);
    int dotIdx = name.lastIndexOf('.');
    if (dotIdx > 0) {
        name = name.substring(0, dotIdx);
    }

    size_t i = 0;
    while (i < name.length() && isdigit((unsigned char)name[i])) {
        i++;
    }
    if (i > 0 && i < name.length()) {
        char sep = name[i];
        if (sep == '_' || sep == '-' || sep == '.' || sep == ' ') {
            while (i < name.length() && (name[i] == '_' || name[i] == '-' || name[i] == '.' || name[i] == ' ')) {
                i++;
            }
            if (i < name.length()) {
                name = name.substring(i);
            }
        }
    }
    return name;
}

static String fitTitleToWidth(const String& title, int32_t maxWidthPx) {
    canvas.setFont(&fonts::FreeSansBold12pt7b);
    if (canvas.textWidth(title) <= maxWidthPx) {
        return title;
    }
    String trimmed = title;
    while (trimmed.length() > 1) {
        trimmed.remove(trimmed.length() - 1);
        String candidate = trimmed + "...";
        if (canvas.textWidth(candidate) <= maxWidthPx) {
            return candidate;
        }
    }
    return "...";
}

static void scanDirectoryForAudio(const char* dirPath, std::vector<String>& outPaths) {
    File dir = SD.open(dirPath);
    if (!dir || !dir.isDirectory()) return;

    while (true) {
        File entry = dir.openNextFile();
        if (!entry) break;
        if (!entry.isDirectory()) {
            String entryName = String(entry.name());
            if (isAudioFile(entryName)) {
                String base = getBasename(entryName);
                String fullPath = (strcmp(dirPath, "/") == 0)
                    ? ("/" + base)
                    : (String(dirPath) + "/" + base);
                outPaths.push_back(fullPath);
            }
        }
        entry.close();
    }
    dir.close();
}

void scanSDPlaylist() {
    playlist.clear();
    std::vector<String> paths;

    if (sdMounted) {
        scanDirectoryForAudio("/", paths);
        if (SD.exists("/music")) {
            scanDirectoryForAudio("/music", paths);
        }
        std::sort(paths.begin(), paths.end(), [](const String& a, const String& b) {
            String ba = getBasename(a);
            String bb = getBasename(b);
            ba.toLowerCase();
            bb.toLowerCase();
            return ba < bb;
        });
        for (const String& p : paths) {
            DynamicTrack trk;
            trk.path = p;
            trk.displayTitle = fitTitleToWidth(stripTrackPrefix(p), 210);
            trk.fallbackSec = 180;
            playlist.push_back(trk);
        }
    }

    if (playlist.empty()) {
        for (size_t i = 0; i < P3R_PLAYLIST_COUNT; i++) {
            DynamicTrack trk;
            trk.path = "";
            trk.displayTitle = fitTitleToWidth(String(P3R_DEFAULT_PLAYLIST[i].displayTitle), 210);
            trk.fallbackSec = P3R_DEFAULT_PLAYLIST[i].durationSec;
            playlist.push_back(trk);
        }
    }
}

size_t pickNextTrackIndex(int8_t dir) {
    size_t count = playlist.size();
    if (count <= 1) return 0;
    if (isShuffleMode && dir > 0) {
        size_t r = currentTrackIdx;
        while (r == currentTrackIdx) {
            r = (size_t)(esp_random() % count);
        }
        return r;
    }
    if (dir >= 0) return (currentTrackIdx + 1) % count;
    return (currentTrackIdx == 0) ? (count - 1) : (currentTrackIdx - 1);
}

void audio_eof_mp3(const char *info) {
    (void)info;
    trackFinishedFlag = true;
}

void triggerTrackSwitch(size_t newIdx, int8_t dir) {
    if (playlist.empty()) return;
    newIdx = newIdx % playlist.size();
    prevTrackIdx = currentTrackIdx;
    prevElapsedSec = elapsedSec;
    currentTrackIdx = newIdx;
    rollDirection = dir;
    rollProgress = 0.0f;
    isPageRolling = true;
    trackFinishedFlag = false;

    if (currentMode == MODE_SD_HIFI_PLAYER && sdMounted && !playlist[currentTrackIdx].path.isEmpty()) {
        elapsedSec = 0;
        audio.connecttoFS(SD, playlist[currentTrackIdx].path.c_str());
    } else {
        elapsedSec = (currentTrackIdx < P3R_PLAYLIST_COUNT)
            ? P3R_DEFAULT_PLAYLIST[currentTrackIdx].opTimestampSec
            : 0;
    }
}

// ============================================================================
// P3R OPENING CUTSCENE UI (284x76 LIGHT-GREY LCD + BLACK INK)
// ============================================================================
static inline uint16_t getLcdBgColor() {
    return (currentUIMode == UI_P3R_ANIME_GREY_LCD)
        ? tft.color565(212, 220, 224)  // #D4DCE0 Anime Light-Grey LCD
        : tft.color565(164, 205, 217); // #A4CDD9 Official Cyan-Blue LCD
}

static inline uint16_t getLcdInkColor() {
    return tft.color565(18, 22, 26);   // #12161A Crisp LCD Ink
}

void playHelloBootAnimation() {
    uint16_t bg = getLcdBgColor();
    uint16_t ink = getLcdInkColor();
    static const char HELLO_CHARS[6] = {'H', 'E', 'L', 'L', 'O', '!'};
    static const int16_t CHAR_X[6]   = {36,  76,  116, 152, 188, 232};

    for (int frame = 0; frame <= 24; frame++) {
        uint8_t bright = (uint8_t)constrain(16 + (frame * 164) / 24, 16, 180);
        int16_t revealW = (frame * 284) / 24;

        canvas.fillScreen(bg);
        if (revealW > 0) {
            canvas.setClipRect(0, 0, revealW, 76);
            canvas.setTextColor(ink, bg);
            canvas.setFont(&fonts::FreeSansBold18pt7b);
            char singleChar[2] = {0, 0};
            for (int i = 0; i < 6; i++) {
                singleChar[0] = HELLO_CHARS[i];
                canvas.drawString(singleChar, CHAR_X[i], 22);
            }
            canvas.clearClipRect();
        }
        // Push clean frame to ST7789 GRAM BEFORE lighting backlight so frame 0 never flashes random pixels
        canvas.pushSprite(0, 0);
        tft.setBrightness(bright);
        delay(22);
    }
    tft.setBrightness(160); // Crisp & battery-friendly IPS brightness
    delay(650);
}

void drawRepeatLoopIcon(int x, int y, uint16_t ink) {
    canvas.drawFastHLine(x + 3, y + 1, 12, ink);
    canvas.drawFastHLine(x + 3, y + 2, 12, ink);
    canvas.fillRect(x + 1, y + 3, 2, 4, ink);
    canvas.fillTriangle(x + 14, y - 1, x + 14, y + 4, x + 18, y + 1, ink);

    canvas.drawFastHLine(x + 3, y + 11, 12, ink);
    canvas.drawFastHLine(x + 3, y + 12, 12, ink);
    canvas.fillRect(x + 15, y + 7, 2, 4, ink);
    canvas.fillTriangle(x + 4, y + 9, x + 4, y + 14, x, y + 11, ink);
}

void drawShuffleIcon(int x, int y, uint16_t ink) {
    canvas.drawFastHLine(x, y + 2, 5, ink);
    canvas.drawFastHLine(x, y + 10, 5, ink);
    canvas.drawLine(x + 5, y + 2, x + 12, y + 10, ink);
    canvas.drawLine(x + 5, y + 10, x + 12, y + 2, ink);
    canvas.drawFastHLine(x + 12, y + 2, 5, ink);
    canvas.drawFastHLine(x + 12, y + 10, 5, ink);
    canvas.fillTriangle(x + 15, y, x + 15, y + 4, x + 18, y + 2, ink);
    canvas.fillTriangle(x + 15, y + 8, x + 15, y + 12, x + 18, y + 10, ink);
}

static volatile uint16_t liveAudioPeak = 0;

void audio_process_extern(int16_t* buff, uint16_t len, bool *continueI2S) {
    *continueI2S = true;
    if (!buff || len == 0) return;
    uint16_t peak = 0;
    for (uint16_t i = 0; i < len; i += 8) {
        int32_t s = buff[i];
        uint16_t a = (uint16_t)(s < 0 ? -s : s);
        if (a > peak) peak = a;
    }
    liveAudioPeak = (uint16_t)((liveAudioPeak * 3U + peak) / 4U);
}

void updateAudioReactiveBars(uint32_t nowMs) {
    if (!isPlaying) {
        for (int i = 0; i < 8; i++) audioBars[i] = 3;
        return;
    }
    uint16_t vu = liveAudioPeak;
    liveAudioPeak = (uint16_t)((liveAudioPeak * 7U) / 8U);
    uint8_t baseLvl = (vu > 64) ? (uint8_t)constrain((vu >> 8) / 6 + 4, 4, 18) : 8;
    for (int i = 0; i < 8; i++) {
        int8_t wave = (int8_t)(((nowMs / 70 + i * 3) % 7) - 3);
        audioBars[i] = (uint8_t)constrain(baseLvl + wave, 3, 18);
    }
}

void drawSingleFullPage(size_t trkIdx, uint32_t timeSec, int16_t yOff, uint16_t bg, uint16_t ink) {
    // 1. Top-Left: Large Track Title (1:1 P3R OP scale on 284x76)
    canvas.setTextColor(ink, bg);
    canvas.setFont(&fonts::FreeSansBold12pt7b);
    const char* title = (trkIdx < playlist.size()) ? playlist[trkIdx].displayTitle.c_str() : "";
    canvas.drawString(title, 10, 10 + yOff);

    // 2. Top-Right: Shuffle (⇄) or Sequential Loop (↻) + Battery Icon
    if (isShuffleMode) {
        drawShuffleIcon(222, 12 + yOff, ink);
    } else if (isRepeatLoop) {
        drawRepeatLoopIcon(222, 12 + yOff, ink);
    }
    canvas.drawRect(248, 12 + yOff, 24, 12, ink);
    canvas.fillRect(272, 15 + yOff, 3, 6, ink);
    canvas.fillRect(251, 15 + yOff, batFillPx, 6, ink);

    // 3. Bottom-Left: Play Triangle / Pause Bars + Timestamp ("▶ 01:36")
    if (isPlaying) {
        canvas.fillTriangle(10, 48 + yOff, 10, 64 + yOff, 21, 56 + yOff, ink);
    } else {
        canvas.fillRect(10, 48 + yOff, 4, 16, ink);
        canvas.fillRect(17, 48 + yOff, 4, 16, ink);
    }

    canvas.setFont(&fonts::FreeSansBold9pt7b);
    char timeBuf[16];
    snprintf(timeBuf, sizeof(timeBuf), "%02lu:%02lu", (unsigned long)(timeSec / 60), (unsigned long)(timeSec % 60));
    canvas.drawString(timeBuf, 28, 49 + yOff);

    // 4. Bottom-Right: "VOL" label + 8 Audio-Reactive / Volume Bars
    canvas.setFont(&fonts::Font0);
    canvas.drawString("VOL", 196, 56 + yOff);
    bool showVolLevel = (millis() - lastVolChangeMs < 1500);
    for (int i = 0; i < 8; i++) {
        uint8_t h = showVolLevel
            ? ((i * 21 / 7 <= currentVolume) ? 18 : 4)
            : audioBars[i];
        canvas.fillRect(220 + i * 7, 64 - h + yOff, 5, h, ink);
    }
}

void renderP3ROpeningExactUI() {
    if (isDisplaySleeping) return;

    uint16_t bg = getLcdBgColor();
    uint16_t ink = getLcdInkColor();
    canvas.fillScreen(bg);

    if (currentMode == MODE_USB_FLASH_DRIVE) {
        canvas.setTextColor(ink, bg);
        canvas.setFont(&fonts::FreeSansBold12pt7b);
#if defined(CONFIG_IDF_TARGET_ESP32S3)
        if (usbExitConfirmPending) {
            canvas.drawString("EJECT USB FIRST", 30, 14);
            canvas.setFont(&fonts::FreeSans9pt7b);
            canvas.drawString("K1/K4 AGAIN: EXIT", 46, 46);
        } else
#endif
        {
            canvas.drawString("U S B   D I S K", 42, 16);
            canvas.setFont(&fonts::FreeSans9pt7b);
            canvas.drawString("PC FILE TRANSFER", 58, 46);
        }
        canvas.pushSprite(0, 0);
        return;
    }

    if (isPageRolling) {
        // 60fps Ease-Out Cubic vertical roll across 76px height (~224ms total)
        float inv = 1.0f - rollProgress;
        float eased = 1.0f - (inv * inv * inv);
        int16_t offsetPx = (int16_t)roundf(eased * 76.0f);

        int16_t outYOff = rollDirection * offsetPx;
        int16_t inYOff  = -rollDirection * (76 - offsetPx);

        drawSingleFullPage(prevTrackIdx, prevElapsedSec, outYOff, bg, ink);
        drawSingleFullPage(currentTrackIdx, elapsedSec, inYOff, bg, ink);

        rollProgress += 1.0f / 14.0f;
        if (rollProgress >= 1.0f) {
            isPageRolling = false;
            rollProgress = 0.0f;
        }
    } else {
        drawSingleFullPage(currentTrackIdx, elapsedSec, 0, bg, ink);
    }

    canvas.pushSprite(0, 0);
}

#if defined(CONFIG_IDF_TARGET_ESP32S3)
void mountUSBMSCOnBoot() {
    if (!sdMounted) return;
    currentMode = MODE_USB_FLASH_DRIVE;
    if (!usbMscActive) {
        msc.vendorID("S.E.E.S");
        msc.productID("P3R_WALKMAN");
        msc.productRevision("2.4");
        msc.onRead(onUSBRead);
        msc.onWrite(onUSBWrite);
        msc.onStartStop(onUSBStartStop);
        msc.mediaPresent(true);
        msc.begin(SD.numSectors(), SD.sectorSize());
        USB.begin();
        usbMscActive = true;
    }
    renderP3ROpeningExactUI();
    tft.setBrightness(160);
}

void requestUSBDiskReboot() {
    if (!sdMounted) return;
    uint16_t bg = getLcdBgColor();
    uint16_t ink = getLcdInkColor();
    canvas.fillScreen(bg);
    canvas.setTextColor(ink, bg);
    canvas.setFont(&fonts::FreeSansBold12pt7b);
    canvas.drawString("U S B   M O D E", 46, 16);
    canvas.setFont(&fonts::FreeSans9pt7b);
    canvas.drawString("REBOOTING...", 74, 46);
    canvas.pushSprite(0, 0);

    audio.stopSong();
    SD.end();
    sdMounted = false;

    p3rPrefs.begin("p3r", false);
    p3rPrefs.putBool("usb_msc", true);
    p3rPrefs.end();

    delay(150);
    ESP.restart();
}

void exitUSBDiskModeSafely() {
    usbExitRequested = false;
    uint16_t bg = getLcdBgColor();
    uint16_t ink = getLcdInkColor();
    canvas.fillScreen(bg);
    canvas.setTextColor(ink, bg);
    canvas.setFont(&fonts::FreeSansBold12pt7b);
    canvas.drawString("R E M O U N T", 54, 16);
    canvas.setFont(&fonts::FreeSans9pt7b);
    canvas.drawString("LOADING TRACKS...", 56, 46);
    canvas.pushSprite(0, 0);

    if (usbMscActive) {
        msc.mediaPresent(false);
        delay(150);
        msc.end();
        usbMscActive = false;
    }
    if (sdMounted) {
        SD.end();
        sdMounted = false;
    }
    delay(120);
    ESP.restart();
}
#endif

static bool pendingDeepSleep = false;

static void enterDeepSleepPowerOff() {
    tft.setBrightness(0);
    tft.sleep();
    audio.stopSong();
    if (sdMounted) {
        SD.end();
        sdMounted = false;
    }

    // Float peripheral pins before cutting 3V3_PERI to prevent phantom backfeeding
    const int periPins[] = {
        PIN_TFT_MOSI, PIN_TFT_SCLK, PIN_TFT_DC, PIN_TFT_BLK, PIN_VBAT_ADC,
        PIN_I2S_BCK, PIN_I2S_WS, PIN_I2S_DOUT,
        PIN_SD_CS, PIN_SD_MOSI, PIN_SD_SCK, PIN_SD_MISO
    };
    for (int pin : periPins) {
        if (pin >= 0) pinMode(pin, INPUT);
    }

    // Drive GP14 HIGH + latch GPIO hold so Q3 AO3401A stays OFF across deep sleep
    digitalWrite(PIN_PERI_PWR_EN, HIGH);
    gpio_hold_en((gpio_num_t)PIN_PERI_PWR_EN);
    gpio_deep_sleep_hold_en();

    // Keep RTC peripheral domain powered and enforce internal RTC_GPIO pull-up on K1 (GPIO1)
    esp_sleep_pd_config(ESP_PD_DOMAIN_RTC_PERIPH, ESP_PD_OPTION_ON);
    rtc_gpio_init((gpio_num_t)PIN_BTN_PLAY_PAUSE);
    rtc_gpio_set_direction((gpio_num_t)PIN_BTN_PLAY_PAUSE, RTC_GPIO_MODE_INPUT_ONLY);
    rtc_gpio_pullup_en((gpio_num_t)PIN_BTN_PLAY_PAUSE);
    rtc_gpio_pulldown_dis((gpio_num_t)PIN_BTN_PLAY_PAUSE);

    // Wake on K1 press (active LOW via RTC_GPIO1)
    esp_sleep_enable_ext0_wakeup((gpio_num_t)PIN_BTN_PLAY_PAUSE, 0);
    delay(20);
    esp_deep_sleep_start();
}

static void updateBatteryTelemetry(uint32_t nowMs, bool force = false) {
    if (!force && (nowMs - lastBatSampleMs < 2000)) return;
    lastBatSampleMs = nowMs;

    uint32_t mvSum = 0;
    for (int i = 0; i < 4; i++) {
        mvSum += analogReadMilliVolts(PIN_VBAT_ADC);
    }
    uint32_t rawVbatMv = (mvSum / 4) * 2;
    if (rawVbatMv < 2400) {
        // Bench USB-only test without external VBAT divider populated -> display full bar cleanly without shutdown
        vbatValid = false;
        vbatMv = 0;
        batFillPx = 18;
        lowBatStreak = 0;
        return;
    }

    vbatValid = true;
    vbatMv = (vbatMv == 0) ? rawVbatMv : (vbatMv * 3 + rawVbatMv) / 4;
    int32_t fill = constrain(((int32_t)vbatMv - 3300) * 18 / (4150 - 3300), 1, 18);
    batFillPx = (uint8_t)fill;

    if (vbatMv < 3280) {
        if (++lowBatStreak >= 5 && !pendingDeepSleep) {
            pendingDeepSleep = true;
            enterDeepSleepPowerOff();
        }
    } else {
        lowBatStreak = 0;
    }
}

#if defined(CONFIG_IDF_TARGET_ESP32S3)
static void handleUSBButtonExitPrompt(uint32_t nowMs) {
    if (!usbExitConfirmPending) {
        usbExitConfirmPending = true;
        usbExitConfirmExpireMs = nowMs + 4000;
    } else {
        usbExitConfirmPending = false;
        usbExitRequested = true;
    }
}
#endif

struct BtnState {
    bool down = false;
    uint32_t downMs = 0;
    uint32_t lastRepeatMs = 0;
    bool longHandled = false;
    bool suppressRelease = false;
};

void handleSide4Buttons(uint32_t nowMs) {
    static BtnState b1, b2, b3, b4;
    static uint32_t k4PendingTapMs = 0;

    if (k4PendingTapMs != 0 && (nowMs - k4PendingTapMs >= 300)) {
        k4PendingTapMs = 0;
        currentEQIdx = (currentEQIdx + 1) % 4;
        const HiFiEQPreset& eq = P3R_HIFI_EQ_PRESETS[currentEQIdx];
        audio.setTone(eq.bassDb, eq.midDb, eq.trebleDb);
    }

    auto samplePressed = [](int pin) -> bool { return digitalRead(pin) == LOW; };
    bool p1 = samplePressed(PIN_BTN_PLAY_PAUSE);
    bool p2 = samplePressed(PIN_BTN_NEXT);
    bool p3 = samplePressed(PIN_BTN_PREV);
    bool p4 = samplePressed(PIN_BTN_MODE_REPEAT);

    if (p1 || p2 || p3 || p4) {
        lastUserActivityMs = nowMs;
        if (isDisplaySleeping) {
            isDisplaySleeping = false;
            tft.wakeup();
            tft.setBrightness(160);
            if (p1) { b1.down = true; b1.downMs = nowMs; b1.suppressRelease = true; }
            if (p2) { b2.down = true; b2.downMs = nowMs; b2.suppressRelease = true; }
            if (p3) { b3.down = true; b3.downMs = nowMs; b3.suppressRelease = true; }
            if (p4) { b4.down = true; b4.downMs = nowMs; b4.suppressRelease = true; }
            return;
        }
    }

    // Button 1 (K1): Short = PLAY/PAUSE (or exit USB Disk Mode), Hold 2.5s = Deep Sleep Power-Off
    if (p1) {
        if (!b1.down) {
            b1.down = true;
            b1.downMs = nowMs;
            b1.longHandled = false;
        } else if (!b1.suppressRelease && !b1.longHandled && (nowMs - b1.downMs >= 2500)) {
            b1.longHandled = true;
            if (currentMode == MODE_SD_HIFI_PLAYER) {
                pendingDeepSleep = true;
                audio.stopSong();
                uint16_t bg = getLcdBgColor();
                uint16_t ink = getLcdInkColor();
                canvas.fillScreen(bg);
                canvas.setTextColor(ink, bg);
                canvas.setFont(&fonts::FreeSansBold12pt7b);
                canvas.drawString("P O W E R   O F F", 36, 16);
                canvas.setFont(&fonts::FreeSans9pt7b);
                canvas.drawString("RELEASE KEY...", 68, 46);
                canvas.pushSprite(0, 0);
            }
        }
    } else if (b1.down) {
        uint32_t heldMs = nowMs - b1.downMs;
        bool suppressed = b1.suppressRelease;
        bool longDone = b1.longHandled;
        b1.down = false;
        b1.suppressRelease = false;
        b1.longHandled = false;
        if (pendingDeepSleep) {
            enterDeepSleepPowerOff();
            return;
        }
        if (!suppressed && !longDone && heldMs >= 30) {
            if (currentMode == MODE_USB_FLASH_DRIVE) {
#if defined(CONFIG_IDF_TARGET_ESP32S3)
                handleUSBButtonExitPrompt(nowMs);
#endif
                return;
            }
            isPlaying = !isPlaying;
            audio.pauseResume();
        }
    }

    // Button 2 (K2): Short = NEXT TRACK, Non-blocking Hold (>=350ms) = VOLUME UP
    if (p2) {
        if (!b2.down) {
            b2.down = true;
            b2.downMs = nowMs;
            b2.lastRepeatMs = 0;
            b2.longHandled = false;
        } else if (!b2.suppressRelease && (nowMs - b2.downMs >= 350)) {
            b2.longHandled = true;
            if (nowMs - b2.lastRepeatMs >= 110) {
                b2.lastRepeatMs = nowMs;
                if (currentVolume < 21) currentVolume++;
                audio.setVolume(currentVolume);
                lastVolChangeMs = nowMs;
            }
        }
    } else if (b2.down) {
        uint32_t heldMs = nowMs - b2.downMs;
        bool suppressed = b2.suppressRelease;
        bool longDone = b2.longHandled;
        b2.down = false;
        b2.suppressRelease = false;
        b2.longHandled = false;
        if (!suppressed && !longDone && heldMs >= 30 && currentMode == MODE_SD_HIFI_PLAYER) {
            triggerTrackSwitch(pickNextTrackIndex(+1), +1);
        }
    }

    // Button 3 (K3): Short = PREV TRACK, Non-blocking Hold (>=350ms) = VOLUME DOWN
    if (p3) {
        if (!b3.down) {
            b3.down = true;
            b3.downMs = nowMs;
            b3.lastRepeatMs = 0;
            b3.longHandled = false;
        } else if (!b3.suppressRelease && (nowMs - b3.downMs >= 350)) {
            b3.longHandled = true;
            if (nowMs - b3.lastRepeatMs >= 110) {
                b3.lastRepeatMs = nowMs;
                if (currentVolume > 0) currentVolume--;
                audio.setVolume(currentVolume);
                lastVolChangeMs = nowMs;
            }
        }
    } else if (b3.down) {
        uint32_t heldMs = nowMs - b3.downMs;
        bool suppressed = b3.suppressRelease;
        bool longDone = b3.longHandled;
        b3.down = false;
        b3.suppressRelease = false;
        b3.longHandled = false;
        if (!suppressed && !longDone && heldMs >= 30 && currentMode == MODE_SD_HIFI_PLAYER) {
            triggerTrackSwitch(pickNextTrackIndex(-1), -1);
        }
    }

    // Button 4 (K4):
    // - Short single-click (<350ms): Cycle Hi-Fi DSP EQ Preset
    // - Short double-click (<300ms): Toggle Sequential Loop vs. Shuffle
    // - Medium press (350..1000ms): Toggle Anime Grey LCD / Official Cyan-Blue LCD
    // - Long press (>=1000ms): Enter USB Flash Drive (reboot to MSC) or Exit USB Disk Mode
    if (p4) {
        if (!b4.down) {
            b4.down = true;
            b4.downMs = nowMs;
            b4.longHandled = false;
        } else if (!b4.suppressRelease && !b4.longHandled && (nowMs - b4.downMs >= 1000)) {
            b4.longHandled = true;
            k4PendingTapMs = 0;
#if defined(CONFIG_IDF_TARGET_ESP32S3)
            if (currentMode == MODE_USB_FLASH_DRIVE) {
                handleUSBButtonExitPrompt(nowMs);
            } else {
                requestUSBDiskReboot();
            }
#else
            playHelloBootAnimation();
#endif
            return;
        }
    } else if (b4.down) {
        uint32_t heldMs = nowMs - b4.downMs;
        bool suppressed = b4.suppressRelease;
        bool longDone = b4.longHandled;
        b4.down = false;
        b4.suppressRelease = false;
        b4.longHandled = false;
        if (!suppressed && !longDone && heldMs >= 30) {
            if (heldMs > 350) {
                k4PendingTapMs = 0;
                currentUIMode = (currentUIMode == UI_P3R_ANIME_GREY_LCD)
                    ? UI_P3R_OFFICIAL_BLUE
                    : UI_P3R_ANIME_GREY_LCD;
            } else if (k4PendingTapMs != 0 && (nowMs - k4PendingTapMs < 300)) {
                k4PendingTapMs = 0;
                isShuffleMode = !isShuffleMode;
            } else {
                k4PendingTapMs = nowMs;
            }
        }
    }
}

void checkAndApplySDCardFirmwareUpdate() {
    if (!sdMounted || !SD.exists("/update.bin")) return;

    File updateBin = SD.open("/update.bin", FILE_READ);
    if (!updateBin || updateBin.isDirectory()) return;

    size_t updateSize = updateBin.size();
    if (updateSize == 0) {
        updateBin.close();
        return;
    }

    uint16_t bg = getLcdBgColor();
    uint16_t ink = getLcdInkColor();
    canvas.fillScreen(bg);
    canvas.setTextColor(ink, bg);
    canvas.setFont(&fonts::FreeSansBold12pt7b);
    canvas.drawString("U P D A T I N G", 40, 14);
    canvas.setFont(&fonts::FreeSans9pt7b);
    canvas.drawString("DO NOT TURN OFF...", 50, 44);
    canvas.pushSprite(0, 0);

    if (Update.begin(updateSize)) {
        size_t written = Update.writeStream(updateBin);
        if (written == updateSize && Update.end(true)) {
            updateBin.close();
            SD.remove("/update.bin");
            canvas.fillScreen(bg);
            canvas.setFont(&fonts::FreeSansBold12pt7b);
            canvas.drawString("U P D A T E   O K !", 34, 26);
            canvas.pushSprite(0, 0);
            delay(800);
            ESP.restart();
        }
    }
    updateBin.close();
}

void setup() {
    gpio_hold_dis((gpio_num_t)PIN_PERI_PWR_EN);
    gpio_deep_sleep_hold_dis();
    rtc_gpio_deinit((gpio_num_t)PIN_BTN_PLAY_PAUSE);

    // Cold power-cycle 3V3_PERI via Q3 (AO3401A) so ST7789P3 & SD always get a clean POR
    pinMode(PIN_PERI_PWR_EN, OUTPUT);
    digitalWrite(PIN_PERI_PWR_EN, HIGH);
    delay(25);
    digitalWrite(PIN_PERI_PWR_EN, LOW);
    delay(130); // Wait >=120ms for ST7789P3 POR RC (10k + 1uF) & TF card power-up settle

    pinMode(PIN_BTN_PLAY_PAUSE, INPUT_PULLUP);
    pinMode(PIN_BTN_NEXT, INPUT_PULLUP);
    pinMode(PIN_BTN_PREV, INPUT_PULLUP);
    pinMode(PIN_BTN_MODE_REPEAT, INPUT_PULLUP);
    pinMode(PIN_VBAT_ADC, INPUT);
    analogSetPinAttenuation(PIN_VBAT_ADC, ADC_11db);
    updateBatteryTelemetry(millis(), true);

    p3rPrefs.begin("p3r", false);
    bool reqUsbMsc = p3rPrefs.getBool("usb_msc", false);
    if (reqUsbMsc) {
        p3rPrefs.putBool("usb_msc", false);
    }
    p3rPrefs.end();

    bool k4HeldAtBoot = (digitalRead(PIN_BTN_MODE_REPEAT) == LOW);

    tft.init();
    tft.setBrightness(0); // Keep backlight dark until first clean frame is pushed
    tft.setRotation(1);   // Landscape 284x76
    canvas.createSprite(284, 76);

    sdSPI.begin(PIN_SD_SCK, PIN_SD_MISO, PIN_SD_MOSI, PIN_SD_CS);
    sdMounted = SD.begin(PIN_SD_CS, sdSPI, 20000000UL);

#if defined(CONFIG_IDF_TARGET_ESP32S3)
    if ((reqUsbMsc || k4HeldAtBoot) && sdMounted) {
        mountUSBMSCOnBoot();
        lastUserActivityMs = millis();
        setCpuFrequencyMhz(160);
        return;
    }
#endif

    checkAndApplySDCardFirmwareUpdate();
    playHelloBootAnimation();

    audio.setPinout(PIN_I2S_BCK, PIN_I2S_WS, PIN_I2S_DOUT);
    audio.setVolume(currentVolume);
    const HiFiEQPreset& eq = P3R_HIFI_EQ_PRESETS[currentEQIdx];
    audio.setTone(eq.bassDb, eq.midDb, eq.trebleDb);

    scanSDPlaylist();
    triggerTrackSwitch(0, +1);
    lastUserActivityMs = millis();
    setCpuFrequencyMhz(160);
}

void loop() {
    uint32_t nowMs = millis();

#if defined(CONFIG_IDF_TARGET_ESP32S3)
    if (usbExitConfirmPending && (int32_t)(nowMs - usbExitConfirmExpireMs) >= 0) {
        usbExitConfirmPending = false;
    }
    if (currentMode == MODE_USB_FLASH_DRIVE && usbExitRequested) {
        exitUSBDiskModeSafely();
        return;
    }
#endif

    if (currentMode == MODE_SD_HIFI_PLAYER && !pendingDeepSleep) {
        audio.loop();
        updateBatteryTelemetry(nowMs);
    }
    handleSide4Buttons(nowMs);

    if (pendingDeepSleep) return;

    // Auto-sleep TFT + cut backlight after 15s idle (any button wakes immediately)
    if (!isDisplaySleeping && currentMode == MODE_SD_HIFI_PLAYER && (nowMs - lastUserActivityMs > 15000)) {
        isDisplaySleeping = true;
        tft.setBrightness(0);
        tft.sleep();
    }

    if (currentMode == MODE_SD_HIFI_PLAYER && trackFinishedFlag && !isPageRolling) {
        trackFinishedFlag = false;
        triggerTrackSwitch(pickNextTrackIndex(+1), +1);
    }

    if (currentMode == MODE_SD_HIFI_PLAYER && isPlaying && !isPageRolling && (nowMs - lastTickMs >= 1000)) {
        lastTickMs = nowMs;
        elapsedSec++;
        if (!playlist.empty() && playlist[currentTrackIdx].path.isEmpty() &&
            elapsedSec > playlist[currentTrackIdx].fallbackSec) {
            triggerTrackSwitch(pickNextTrackIndex(+1), +1);
        }
    }

    if (nowMs - lastFrameMs >= 16) {
        lastFrameMs = nowMs;
        updateAudioReactiveBars(nowMs);
        renderP3ROpeningExactUI();
    }
}
