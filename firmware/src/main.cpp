/**
 * Persona 3 Reload (P3R) Opening Animation 1:1 Screen-Accurate Hi-Fi MP3 Player Firmware (Rev 2)
 * Hardware (Rev 2 Long-Body):
 *   - Waveshare ESP32-S3-Zero-M (Dual-Core 240MHz + Native USB 2.0 OTG)
 *   - PCM5102A 32-Bit/384kHz DirectPath Stereo I2S Hi-Fi DAC
 *   - 2.25" 76x284 ST7789P3 SPI Bar IPS/TFT Display (8-Pin 0.5mm FPC, 1:1 Anime Light-Grey LCD)
 *   - TF-01A MicroSD Card Slot (Permanent internal card -> USB Flash Drive via USBMSC)
 *   - 601260 420mAh Polymer LiPo Battery + GP44 Backlight Sleep Shutoff
 */

#include <Arduino.h>
#include <vector>
#include <algorithm>
#include <SPI.h>
#include <SD.h>
#include <Update.h>
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
            cfg.spi_mode = 0;
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
            cfg.invert      = false; // NPN S8050 high-active backlight switch
            cfg.freq        = 12000;
            cfg.pwm_channel = 7;
            _light_instance.config(cfg);
            _panel_instance.setLight(&_light_instance);
        }
        setPanel(&_panel_instance);
    }
};

static LGFX_P3R tft;
static LGFX_Sprite canvas(&tft); // Offscreen 284x76 double-buffer for tear-free 60fps roll

Audio audio;
#if defined(CONFIG_IDF_TARGET_ESP32S3)
USBMSC msc;
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
static int32_t onUSBRead(uint32_t lba, uint32_t offset, void* buffer, uint32_t bufsize) {
    uint32_t count = bufsize / SD.sectorSize();
    for (uint32_t i = 0; i < count; i++) {
        if (!SD.readRAW((uint8_t*)buffer + (i * SD.sectorSize()), lba + i)) {
            return -1;
        }
    }
    return bufsize;
}

static int32_t onUSBWrite(uint32_t lba, uint32_t offset, uint8_t* buffer, uint32_t bufsize) {
    uint32_t count = bufsize / SD.sectorSize();
    for (uint32_t i = 0; i < count; i++) {
        if (!SD.writeRAW(buffer + (i * SD.sectorSize()), lba + i)) {
            return -1;
        }
    }
    return bufsize;
}

static bool onUSBStartStop(uint8_t power_condition, bool start, bool load_eject) {
    if (load_eject && !start) {
        currentMode = MODE_SD_HIFI_PLAYER;
    }
    return true;
}

void enableUSBDiskMode() {
    if (!sdMounted) return;
    audio.stopSong();
    currentMode = MODE_USB_FLASH_DRIVE;
    if (!usbMscActive) {
        msc.vendorID("S.E.E.S");
        msc.productID("P3R_WALKMAN");
        msc.productRevision("2.0");
        msc.onRead(onUSBRead);
        msc.onWrite(onUSBWrite);
        msc.onStartStop(onUSBStartStop);
        msc.mediaPresent(true);
        msc.begin(SD.numSectors(), SD.sectorSize());
        USB.begin();
        usbMscActive = true;
    }
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

        tft.setBrightness(bright);
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
        canvas.pushSprite(0, 0);
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

void updateAudioReactiveBars(uint32_t nowMs) {
    if (!isPlaying) {
        for (int i = 0; i < 8; i++) audioBars[i] = 3;
        return;
    }
    uint16_t vu = audio.getVUlevel();
    uint8_t baseLvl = (vu > 0) ? (uint8_t)constrain((vu >> 8) / 8 + 4, 4, 18) : 8;
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
    canvas.fillRect(251, 15 + yOff, 18, 6, ink);

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
        canvas.drawString("U S B   D I S K", 42, 16);
        canvas.setFont(&fonts::FreeSans9pt7b);
        canvas.drawString("PC FILE TRANSFER", 58, 46);
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

void handleSide4Buttons(uint32_t nowMs) {
    static uint32_t lastBtnMs = 0;
    static uint32_t k4PendingTapMs = 0;

    if (k4PendingTapMs != 0 && (nowMs - k4PendingTapMs >= 300)) {
        k4PendingTapMs = 0;
        currentEQIdx = (currentEQIdx + 1) % 4;
        const HiFiEQPreset& eq = P3R_HIFI_EQ_PRESETS[currentEQIdx];
        audio.setTone(eq.bassDb, eq.midDb, eq.trebleDb);
    }

    if (nowMs - lastBtnMs < 120) return;

    if (digitalRead(PIN_BTN_PLAY_PAUSE) == LOW || digitalRead(PIN_BTN_NEXT) == LOW ||
        digitalRead(PIN_BTN_PREV) == LOW || digitalRead(PIN_BTN_MODE_REPEAT) == LOW) {
        lastUserActivityMs = nowMs;
        if (isDisplaySleeping) {
            isDisplaySleeping = false;
            tft.wakeup();
            tft.setBrightness(160);
            lastBtnMs = nowMs;
            return;
        }
    }

    // Button 1 (K1): PLAY / PAUSE (or exit USB Disk Mode back to Player & re-scan SD)
    if (digitalRead(PIN_BTN_PLAY_PAUSE) == LOW) {
        lastBtnMs = nowMs;
        if (currentMode == MODE_USB_FLASH_DRIVE) {
            currentMode = MODE_SD_HIFI_PLAYER;
            scanSDPlaylist();
            triggerTrackSwitch(0, +1);
            return;
        }
        isPlaying = !isPlaying;
        audio.pauseResume();
    }

    // Button 2 (K2): Short=NEXT TRACK, Hold=VOLUME UP
    if (digitalRead(PIN_BTN_NEXT) == LOW) {
        lastBtnMs = nowMs;
        uint32_t t0 = millis();
        while (digitalRead(PIN_BTN_NEXT) == LOW) {
            if (millis() - t0 > 350) {
                if (currentVolume < 21) currentVolume++;
                audio.setVolume(currentVolume);
                lastVolChangeMs = millis();
                delay(110);
            }
            delay(10);
        }
        if (millis() - t0 <= 350) {
            triggerTrackSwitch(pickNextTrackIndex(+1), +1);
        }
    }

    // Button 3 (K3): Short=PREV TRACK, Hold=VOLUME DOWN
    if (digitalRead(PIN_BTN_PREV) == LOW) {
        lastBtnMs = nowMs;
        uint32_t t0 = millis();
        while (digitalRead(PIN_BTN_PREV) == LOW) {
            if (millis() - t0 > 350) {
                if (currentVolume > 0) currentVolume--;
                audio.setVolume(currentVolume);
                lastVolChangeMs = millis();
                delay(110);
            }
            delay(10);
        }
        if (millis() - t0 <= 350) {
            triggerTrackSwitch(pickNextTrackIndex(-1), -1);
        }
    }

    // Button 4 (K4):
    // - Short single-click (<350ms): Cycle Hi-Fi DSP EQ Preset
    // - Short double-click (<300ms): Toggle Sequential Loop (↻) vs. Shuffle (⇄)
    // - Medium press (350..900ms): Toggle Anime Grey LCD / Official Cyan-Blue LCD
    // - Long press (>900ms): Enter USB Flash Drive (U盘直传) Mode
    if (digitalRead(PIN_BTN_MODE_REPEAT) == LOW) {
        lastBtnMs = nowMs;
        uint32_t t0 = millis();
        while (digitalRead(PIN_BTN_MODE_REPEAT) == LOW) {
            if (millis() - t0 > 900) {
                k4PendingTapMs = 0;
#if defined(CONFIG_IDF_TARGET_ESP32S3)
                enableUSBDiskMode();
#else
                playHelloBootAnimation();
#endif
                return;
            }
            delay(10);
        }
        uint32_t heldMs = millis() - t0;
        if (heldMs > 350) {
            k4PendingTapMs = 0;
            currentUIMode = (currentUIMode == UI_P3R_ANIME_GREY_LCD)
                ? UI_P3R_OFFICIAL_BLUE
                : UI_P3R_ANIME_GREY_LCD;
        } else if (k4PendingTapMs != 0 && (millis() - k4PendingTapMs < 300)) {
            k4PendingTapMs = 0;
            isShuffleMode = !isShuffleMode;
        } else {
            k4PendingTapMs = millis();
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
    pinMode(PIN_BTN_PLAY_PAUSE, INPUT_PULLUP);
    pinMode(PIN_BTN_NEXT, INPUT_PULLUP);
    pinMode(PIN_BTN_PREV, INPUT_PULLUP);
    pinMode(PIN_BTN_MODE_REPEAT, INPUT_PULLUP);

    tft.init();
    tft.setRotation(1); // Landscape 284x76
    canvas.createSprite(284, 76);

    sdSPI.begin(PIN_SD_SCK, PIN_SD_MISO, PIN_SD_MOSI, PIN_SD_CS);
    sdMounted = SD.begin(PIN_SD_CS, sdSPI, 20000000UL);

    checkAndApplySDCardFirmwareUpdate();
    playHelloBootAnimation();

    audio.setPinout(PIN_I2S_BCK, PIN_I2S_WS, PIN_I2S_DOUT);
    audio.setVolume(currentVolume);
    const HiFiEQPreset& eq = P3R_HIFI_EQ_PRESETS[currentEQIdx];
    audio.setTone(eq.bassDb, eq.midDb, eq.trebleDb);

#if defined(CONFIG_IDF_TARGET_ESP32S3)
    if (digitalRead(PIN_BTN_MODE_REPEAT) == LOW && sdMounted) {
        enableUSBDiskMode();
    }
#endif

    if (currentMode == MODE_SD_HIFI_PLAYER) {
        scanSDPlaylist();
        triggerTrackSwitch(0, +1);
    }
    lastUserActivityMs = millis();
    setCpuFrequencyMhz(80);
}

void loop() {
    uint32_t nowMs = millis();
    if (currentMode == MODE_SD_HIFI_PLAYER) {
        audio.loop();
    }
    handleSide4Buttons(nowMs);

    // Auto-sleep TFT + cut 80mA backlight after 15s idle (any button wakes immediately)
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
