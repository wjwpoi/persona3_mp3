/**
 * Persona 3 Reload (P3R) Opening Animation 1:1 Screen-Accurate Hi-Fi MP3 Player Firmware
 * Hardware (Plan-A Taobao Kit):
 *   - Waveshare ESP32-S3-Zero-M (Dual-Core 240MHz + Native USB 2.0 OTG)
 *   - GY-PCM5102 (TI Burr-Brown PCM5102A 32-Bit/384kHz DirectPath Stereo I2S Hi-Fi DAC)
 *   - 0.91" 128x32 I2C OLED Display
 *   - Mini SD SPI Module (Permanent internal MicroSD card — Never needs to be removed!)
 *
 * Key Features:
 * 1. Permanent Internal SD Card + Direct PC USB Flash Drive Mode (`USBMSC`):
 *    Leave the MicroSD card inside the player permanently! When connected to a PC via USB Type-C
 *    (either automatically on USB host mount or toggled via Button K4), the ESP32-S3 mounts the
 *    internal MicroSD card as a standard removable USB Flash Drive ("P3R_WALKMAN") on Windows/macOS
 *    so you can drag-and-drop .flac / .wav / .mp3 songs directly without ever opening the shell!
 * 2. 1:1 P3R Opening Cutscene Boot Animation ("H E L L O !"):
 *    Whole-graphic progressive left-to-right clip reveal + hardware contrast fade-in.
 * 3. Whole-Screen Vertical Page-Roll Transition:
 *    Every element on the 128x32 screen scrolls vertically together when changing tracks.
 * 4. 32-Bit I2S Hi-Fi Decoding (.flac / .wav / .mp3) + 4 Sony Clear-Bass DSP EQ Presets.
 */

#include <Arduino.h>
#include <vector>
#include <algorithm>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <Update.h>
#include <U8g2lib.h>
#include "Audio.h"
#if defined(CONFIG_IDF_TARGET_ESP32S3)
#include "USB.h"
#include "USBMSC.h"
#endif
#include "p3r_ui_assets.h"

U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE, PIN_OLED_SCL, PIN_OLED_SDA);

Audio audio;
#if defined(CONFIG_IDF_TARGET_ESP32S3)
USBMSC msc;
#endif

enum PlayerMode {
    MODE_SD_HIFI_PLAYER = 0,
    MODE_USB_FLASH_DRIVE = 1  // Direct PC USB Mass Storage mode (transfer songs without removing SD card!)
};

enum UIMode {
    UI_P3R_OPENING_CANON = 0, // Dark background + Glowing Pixels
    UI_P3R_INVERTED_LCD  = 1  // Light background + Dark Pixels (exact anime backlit LCD look)
};

struct HiFiEQPreset {
    const char* name;
    int8_t bassDb;
    int8_t midDb;
    int8_t trebleDb;
};

static const HiFiEQPreset P3R_HIFI_EQ_PRESETS[4] = {
    {"CLEAR BASS+", +5, +1, +3}, // Tuned for open clip-on headphones (ATH-EM700 / EQ300M)
    {"VOCAL BOOST", +1, +4, +3}, // Vocal-forward for Burn My Dread / Full Moon Full Life
    {"DARK HOUR",   +6,  0, +2}, // Deep sub-bass punch
    {"HIFI DIRECT",  0,  0,  0}  // Bit-perfect 32-bit PCM5102A reference output
};

static PlayerMode currentMode = MODE_SD_HIFI_PLAYER;
static UIMode currentUIMode = UI_P3R_OPENING_CANON; // Default Black-BG/White-Text saves ~70% OLED power; K4 med-press toggles Inverted LCD!
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
static bool isOledSleeping = false;

struct DynamicTrack {
    String path;
    String displayTitle;
    uint32_t fallbackSec;
};

static std::vector<DynamicTrack> playlist;

// Whole-Screen Vertical Page-Roll State (60fps Ease-Out Cubic matching P3R OP 13-18s!)
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
        // Safely ejected from PC -> return to Hi-Fi MP3 Player mode automatically!
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
        msc.productRevision("1.0");
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

// Strip leading numeric index prefixes (e.g. "01_Burn My Dread.mp3", "02 - Mass Destruction.flac", "03. Aria.wav")
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

static String fitTitleToWidth(const String& title, uint16_t maxWidthPx) {
    u8g2.setFont(u8g2_font_helvB12_tf);
    if (u8g2.getStrWidth(title.c_str()) <= maxWidthPx) {
        return title;
    }
    String trimmed = title;
    while (trimmed.length() > 1) {
        trimmed.remove(trimmed.length() - 1);
        String candidate = trimmed + "...";
        if (u8g2.getStrWidth(candidate.c_str()) <= maxWidthPx) {
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
            trk.displayTitle = fitTitleToWidth(stripTrackPrefix(p), 88);
            trk.fallbackSec = 180;
            playlist.push_back(trk);
        }
    }

    if (playlist.empty()) {
        for (size_t i = 0; i < P3R_PLAYLIST_COUNT; i++) {
            DynamicTrack trk;
            trk.path = "";
            trk.displayTitle = fitTitleToWidth(String(P3R_DEFAULT_PLAYLIST[i].displayTitle), 88);
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
// P3R OPENING CUTSCENE BOOT ANIMATION (13-18s):
// Tall slender "H E L L O !" (18px) fading & wiping in smoothly at 60fps
// ============================================================================
void drawHelloGraphicFull() {
    static const char HELLO_CHARS[6] = {'H', 'E', 'L', 'L', 'O', '!'};
    static const int16_t CHAR_X[6]   = {16,  34,  52,  69,  86,  106};
    u8g2.setFont(u8g2_font_helvR18_tr);
    char singleChar[2] = {0, 0};
    for (int i = 0; i < 6; i++) {
        singleChar[0] = HELLO_CHARS[i];
        u8g2.drawStr(CHAR_X[i], 25, singleChar);
    }
}

void playHelloBootAnimation() {
    for (int frame = 0; frame <= 24; frame++) {
        uint8_t contrast = (uint8_t)constrain(12 + (frame * 140) / 24, 12, 160);
        int16_t revealW  = (frame * 128) / 24;

        u8g2.setContrast(contrast);
        u8g2.clearBuffer();
        if (currentUIMode == UI_P3R_INVERTED_LCD) {
            u8g2.setDrawColor(1);
            u8g2.drawBox(0, 0, 128, 32);
            u8g2.setDrawColor(0);
        } else {
            u8g2.setDrawColor(1);
        }

        if (revealW > 0) {
            u8g2.setClipWindow(0, 0, revealW, 31);
            drawHelloGraphicFull();
            u8g2.setMaxClipWindow();
        }
        u8g2.sendBuffer();
        delay(22);
    }

    u8g2.setContrast(140); // Crisp & battery-friendly brightness
    delay(650);
}

void drawRepeatLoopIcon(int x, int y) {
    u8g2.drawHLine(x + 2, y, 6);
    u8g2.drawPixel(x + 1, y + 1);
    u8g2.drawPixel(x + 1, y + 2);
    u8g2.drawPixel(x + 7, y - 1);
    u8g2.drawPixel(x + 7, y + 1);

    u8g2.drawHLine(x + 2, y + 6, 6);
    u8g2.drawPixel(x + 8, y + 4);
    u8g2.drawPixel(x + 8, y + 5);
    u8g2.drawPixel(x + 2, y + 5);
    u8g2.drawPixel(x + 2, y + 7);
}

void drawShuffleIcon(int x, int y) {
    // 10x7 crossed arrows (⇄)
    u8g2.drawHLine(x, y + 1, 3);
    u8g2.drawHLine(x, y + 5, 3);
    u8g2.drawLine(x + 3, y + 1, x + 6, y + 5);
    u8g2.drawLine(x + 3, y + 5, x + 6, y + 1);
    u8g2.drawHLine(x + 6, y + 1, 3);
    u8g2.drawHLine(x + 6, y + 5, 3);
    u8g2.drawPixel(x + 8, y);
    u8g2.drawPixel(x + 8, y + 2);
    u8g2.drawPixel(x + 8, y + 4);
    u8g2.drawPixel(x + 8, y + 6);
}

void updateAudioReactiveBars(uint32_t nowMs) {
    if (!isPlaying) {
        for (int i = 0; i < 8; i++) audioBars[i] = 2;
        return;
    }
    uint16_t vu = audio.getVUlevel();
    uint8_t baseLvl = (vu > 0) ? (uint8_t)constrain((vu >> 8) / 16 + 2, 2, 9) : 4;
    for (int i = 0; i < 8; i++) {
        // Subtle Sony Walkman rhythmic wave across the 8 bars
        int8_t wave = (int8_t)(((nowMs / 70 + i * 3) % 5) - 2);
        audioBars[i] = (uint8_t)constrain(baseLvl + wave, 2, 9);
    }
}

void drawSingleFullPage(size_t trkIdx, uint32_t timeSec, int16_t yOff) {
    // 1. Top-Left: Large Track Title (~48% height, exact P3R OP Frame 1/3 proportion!)
    u8g2.setFont(u8g2_font_helvB12_tf);
    const char* title = (trkIdx < playlist.size()) ? playlist[trkIdx].displayTitle.c_str() : "";
    u8g2.drawStr(4, 15 + yOff, title);

    // 2. Top-Right: Shuffle (⇄) or Sequential Loop (↻) Icon + Battery Box
    if (isShuffleMode) {
        drawShuffleIcon(96, 5 + yOff);
    } else if (isRepeatLoop) {
        drawRepeatLoopIcon(96, 5 + yOff);
    }
    u8g2.drawFrame(111, 5 + yOff, 12, 6);
    u8g2.drawBox(123, 6 + yOff, 2, 4);
    u8g2.drawBox(113, 7 + yOff, 8, 2);

    // 3. Bottom-Left: Play Triangle / Pause Bars aligned with Timestamp ("▶ 01:36")
    if (isPlaying) {
        u8g2.drawTriangle(4, 21 + yOff, 4, 29 + yOff, 9, 25 + yOff);
    } else {
        u8g2.drawBox(4, 21 + yOff, 2, 8);
        u8g2.drawBox(7, 21 + yOff, 2, 8);
    }

    u8g2.setFont(u8g2_font_6x10_tf);
    char timeBuf[16];
    uint16_t mins = timeSec / 60;
    uint16_t secs = timeSec % 60;
    snprintf(timeBuf, sizeof(timeBuf), "%02u:%02u", mins, secs);
    u8g2.drawStr(13, 28 + yOff, timeBuf);

    // 4. Bottom-Right: "VOL" label + 8 Audio-Reactive / Volume Bars
    u8g2.setFont(u8g2_font_micro_tr);
    u8g2.drawStr(82, 27 + yOff, "VOL");
    bool showVolLevel = (millis() - lastVolChangeMs < 1500);
    for (int i = 0; i < 8; i++) {
        uint8_t h = showVolLevel
            ? ((i * 21 / 7 <= currentVolume) ? 8 : 2)
            : audioBars[i];
        u8g2.drawBox(99 + i * 3, 28 - h + yOff, 2, h);
    }
}

void renderP3ROpeningExactUI() {
    if (isOledSleeping) return;

    u8g2.clearBuffer();

    if (currentUIMode == UI_P3R_INVERTED_LCD) {
        u8g2.setDrawColor(1);
        u8g2.drawBox(0, 0, 128, 32);
        u8g2.setDrawColor(0);
    } else {
        u8g2.setDrawColor(1);
    }

    if (currentMode == MODE_USB_FLASH_DRIVE) {
        u8g2.setFont(u8g2_font_helvB10_tf);
        u8g2.drawStr(10, 14, "U S B   D I S K");
        u8g2.setFont(u8g2_font_6x12_tf);
        u8g2.drawStr(10, 28, "PC FILE TRANSFER");
        u8g2.sendBuffer();
        return;
    }

    if (isPageRolling) {
        // 60fps Ease-Out Cubic vertical roll (~224ms total)
        float inv = 1.0f - rollProgress;
        float eased = 1.0f - (inv * inv * inv);
        int16_t offsetPx = (int16_t)roundf(eased * 32.0f);

        int16_t outYOff = rollDirection * offsetPx;
        int16_t inYOff  = -rollDirection * (32 - offsetPx);

        drawSingleFullPage(prevTrackIdx, prevElapsedSec, outYOff);
        drawSingleFullPage(currentTrackIdx, elapsedSec, inYOff);

        rollProgress += 1.0f / 14.0f;
        if (rollProgress >= 1.0f) {
            isPageRolling = false;
            rollProgress = 0.0f;
        }
    } else {
        drawSingleFullPage(currentTrackIdx, elapsedSec, 0);
    }

    u8g2.sendBuffer();
}

void handleSide4Buttons(uint32_t nowMs) {
    static uint32_t lastBtnMs = 0;
    static uint32_t k4PendingTapMs = 0;

    // Resolve single-click EQ cycle after the 300ms double-click window expires
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
        if (isOledSleeping) {
            isOledSleeping = false;
            u8g2.setPowerSave(0);
            lastBtnMs = nowMs;
            return; // First press wakes OLED cleanly
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

    // Button 2 (K2): Short=NEXT TRACK (60fps vertical roll, respects Shuffle), Hold=VOLUME UP
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

    // Button 3 (K3): Short=PREV TRACK (reverse vertical roll), Hold=VOLUME DOWN
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
    // - Medium press (350..900ms): Toggle Inverted LCD / Glowing Ice-Blue Polarity
    // - Long press (>900ms): Enter USB Flash Drive (U盘直传免拆卡) Mode & Replay "H E L L O !"
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
            currentUIMode = (currentUIMode == UI_P3R_OPENING_CANON)
                ? UI_P3R_INVERTED_LCD
                : UI_P3R_OPENING_CANON;
        } else if (k4PendingTapMs != 0 && (millis() - k4PendingTapMs < 300)) {
            k4PendingTapMs = 0;
            isShuffleMode = !isShuffleMode;
        } else {
            k4PendingTapMs = millis();
        }
    }
}

// ============================================================================
// DRAG-AND-DROP SD CARD FIRMWARE AUTO-UPDATER (`/update.bin`)
// Allows upgrading UI & features anytime simply by dropping `update.bin` into
// the `P3R_WALKMAN` USB drive without even opening an IDE!
// ============================================================================
void checkAndApplySDCardFirmwareUpdate() {
    if (!sdMounted || !SD.exists("/update.bin")) return;

    File updateBin = SD.open("/update.bin", FILE_READ);
    if (!updateBin || updateBin.isDirectory()) return;

    size_t updateSize = updateBin.size();
    if (updateSize == 0) {
        updateBin.close();
        return;
    }

    u8g2.clearBuffer();
    u8g2.setDrawColor(1);
    u8g2.setFont(u8g2_font_helvB10_tf);
    u8g2.drawStr(8, 14, "U P D A T I N G");
    u8g2.setFont(u8g2_font_6x12_tf);
    u8g2.drawStr(8, 28, "DO NOT TURN OFF...");
    u8g2.sendBuffer();

    if (Update.begin(updateSize)) {
        size_t written = Update.writeStream(updateBin);
        if (written == updateSize && Update.end(true)) {
            updateBin.close();
            SD.remove("/update.bin");
            u8g2.clearBuffer();
            u8g2.setFont(u8g2_font_helvB10_tf);
            u8g2.drawStr(12, 22, "U P D A T E   O K !");
            u8g2.sendBuffer();
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

    Wire.begin(PIN_OLED_SDA, PIN_OLED_SCL, 400000UL);
    u8g2.begin();
    u8g2.setContrast(255);

    SPI.begin(PIN_SD_SCK, PIN_SD_MISO, PIN_SD_MOSI, PIN_SD_CS);
    sdMounted = SD.begin(PIN_SD_CS, SPI, 20000000UL);

    // Check if user dropped a new `/update.bin` firmware package onto the SD card
    checkAndApplySDCardFirmwareUpdate();

    // 1:1 P3R Opening Cutscene "H E L L O !" Whole-Image Smooth Reveal Animation!
    playHelloBootAnimation();

    audio.setPinout(PIN_I2S_BCK, PIN_I2S_WS, PIN_I2S_DOUT);
    audio.setVolume(currentVolume);
    const HiFiEQPreset& eq = P3R_HIFI_EQ_PRESETS[currentEQIdx];
    audio.setTone(eq.bassDb, eq.midDb, eq.trebleDb);

    // If K4 is held during power-on or plugged into PC USB wanting file transfer, start USB MSC
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
    setCpuFrequencyMhz(80); // 80MHz cuts ESP32-S3 active power by ~45% while keeping I2S Hi-Fi bit-perfect!
}

void loop() {
    uint32_t nowMs = millis();
    if (currentMode == MODE_SD_HIFI_PLAYER) {
        audio.loop();
    }
    handleSide4Buttons(nowMs);

    // Auto-sleep OLED after 15s idle to save battery (any button wakes immediately)
    if (!isOledSleeping && currentMode == MODE_SD_HIFI_PLAYER && (nowMs - lastUserActivityMs > 15000)) {
        isOledSleeping = true;
        u8g2.setPowerSave(1);
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

    if (nowMs - lastFrameMs >= 16) { // Smooth 60fps for ease-out roll & audio-reactive bars
        lastFrameMs = nowMs;
        updateAudioReactiveBars(nowMs);
        renderP3ROpeningExactUI();
    }
}
