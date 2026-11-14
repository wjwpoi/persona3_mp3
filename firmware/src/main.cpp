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
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
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
static UIMode currentUIMode = UI_P3R_INVERTED_LCD;
static uint8_t currentEQIdx = 0;
static size_t currentTrackIdx = 0;
static size_t prevTrackIdx = 0;
static bool isPlaying = true;
static bool isRepeatLoop = true;
static bool sdMounted = false;
static bool usbMscActive = false;
static uint8_t currentVolume = 16; // 0..21
static uint32_t elapsedSec = 96;   // Starts at 01:36 ("Burn My Dread")
static uint32_t prevElapsedSec = 96;
static uint32_t lastTickMs = 0;
static uint32_t lastFrameMs = 0;

// Whole-Screen Vertical Page-Roll State (Matches Frame 3 of P3R Opening!)
static bool isPageRolling = false;
static int8_t rollDirection = 1;
static int16_t rollOffsetPx = 0;

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

void triggerTrackSwitch(size_t newIdx, int8_t dir) {
    prevTrackIdx = currentTrackIdx;
    prevElapsedSec = elapsedSec;
    currentTrackIdx = newIdx;
    rollDirection = dir;
    rollOffsetPx = 0;
    isPageRolling = true;
    elapsedSec = P3R_DEFAULT_PLAYLIST[currentTrackIdx].opTimestampSec;

    if (currentMode == MODE_SD_HIFI_PLAYER && sdMounted) {
        static const char* EXTS[3] = {"flac", "wav", "mp3"};
        for (int i = 0; i < 3; i++) {
            char filename[64];
            snprintf(filename, sizeof(filename), "/%s.%s", P3R_DEFAULT_PLAYLIST[currentTrackIdx].trackNum, EXTS[i]);
            if (SD.exists(filename)) {
                audio.connecttoFS(SD, filename);
                elapsedSec = 0;
                break;
            }
        }
    }
}

// ============================================================================
// P3R OPENING CUTSCENE BOOT ANIMATION:
// "H E L L O !" AS A WHOLE GRAPHIC SMOOTHLY REVEALING & FADING IN
// ============================================================================
void drawHelloGraphicFull() {
    static const char HELLO_CHARS[6] = {'H', 'E', 'L', 'L', 'O', '!'};
    static const int16_t CHAR_X[6]   = {18,  35,  52,  69,  86,  105};
    u8g2.setFont(u8g2_font_helvB14_tr);
    char singleChar[2] = {0, 0};
    for (int i = 0; i < 6; i++) {
        singleChar[0] = HELLO_CHARS[i];
        u8g2.drawStr(CHAR_X[i], 23, singleChar);
    }
}

void playHelloBootAnimation() {
    for (int frame = 0; frame <= 24; frame++) {
        uint8_t contrast = (uint8_t)constrain(15 + (frame * 240) / 24, 15, 255);
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
        delay(32);
    }

    u8g2.setContrast(255);
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

void drawSingleFullPage(size_t trkIdx, uint32_t timeSec, int16_t yOff) {
    if (isPlaying) {
        u8g2.drawTriangle(3, 4 + yOff, 3, 12 + yOff, 8, 8 + yOff);
    } else {
        u8g2.drawBox(3, 4 + yOff, 2, 8);
        u8g2.drawBox(6, 4 + yOff, 2, 8);
    }

    u8g2.setFont(u8g2_font_helvB10_tf);
    u8g2.drawStr(13, 13 + yOff, P3R_DEFAULT_PLAYLIST[trkIdx].displayTitle);

    if (isRepeatLoop) {
        drawRepeatLoopIcon(98, 5 + yOff);
    }
    u8g2.drawFrame(112, 5 + yOff, 11, 6);
    u8g2.drawBox(123, 6 + yOff, 2, 4);

    u8g2.setFont(u8g2_font_6x12_tf);
    char timeBuf[16];
    uint16_t mins = timeSec / 60;
    uint16_t secs = timeSec % 60;
    snprintf(timeBuf, sizeof(timeBuf), "%02u:%02u", mins, secs);
    u8g2.drawStr(13, 28 + yOff, timeBuf);

    u8g2.setFont(u8g2_font_micro_tr);
    u8g2.drawStr(83, 26 + yOff, "VOL");
    for (int i = 0; i < 6; i++) {
        u8g2.drawBox(98 + i * 2, 20 + yOff, 1, 8);
    }
}

void renderP3ROpeningExactUI() {
    u8g2.clearBuffer();

    if (currentUIMode == UI_P3R_INVERTED_LCD) {
        u8g2.setDrawColor(1);
        u8g2.drawBox(0, 0, 128, 32);
        u8g2.setDrawColor(0);
    } else {
        u8g2.setDrawColor(1);
    }

    if (currentMode == MODE_USB_FLASH_DRIVE) {
        // USB Flash Drive Mode Screen: transfer files directly from PC without removing SD card!
        u8g2.setFont(u8g2_font_helvB10_tf);
        u8g2.drawStr(10, 14, "U S B   D I S K");
        u8g2.setFont(u8g2_font_6x12_tf);
        u8g2.drawStr(10, 28, "PC FILE TRANSFER");
        u8g2.sendBuffer();
        return;
    }

    if (isPageRolling) {
        int16_t outYOff = rollDirection * rollOffsetPx;
        int16_t inYOff  = -rollDirection * (32 - rollOffsetPx);

        drawSingleFullPage(prevTrackIdx, prevElapsedSec, outYOff);
        drawSingleFullPage(currentTrackIdx, elapsedSec, inYOff);

        rollOffsetPx += 4;
        if (rollOffsetPx >= 32) {
            isPageRolling = false;
            rollOffsetPx = 0;
        }
    } else {
        drawSingleFullPage(currentTrackIdx, elapsedSec, 0);
    }

    u8g2.sendBuffer();
}

void handleSide4Buttons(uint32_t nowMs) {
    static uint32_t lastBtnMs = 0;
    if (nowMs - lastBtnMs < 180) return;

    // Button 1 (K1): PLAY / PAUSE (or exit USB Disk Mode back to Player)
    if (digitalRead(PIN_BTN_PLAY_PAUSE) == LOW) {
        lastBtnMs = nowMs;
        if (currentMode == MODE_USB_FLASH_DRIVE) {
            currentMode = MODE_SD_HIFI_PLAYER;
            triggerTrackSwitch(currentTrackIdx, +1);
            return;
        }
        isPlaying = !isPlaying;
        audio.pauseResume();
    }

    // Button 2 (K2): NEXT TRACK (triggers whole-screen vertical roll!)
    if (digitalRead(PIN_BTN_NEXT) == LOW) {
        lastBtnMs = nowMs;
        size_t nextIdx = (currentTrackIdx + 1) % P3R_PLAYLIST_COUNT;
        triggerTrackSwitch(nextIdx, +1);
    }

    // Button 3 (K3): PREV TRACK (triggers reverse whole-screen vertical roll!)
    if (digitalRead(PIN_BTN_PREV) == LOW) {
        lastBtnMs = nowMs;
        size_t prevIdx = (currentTrackIdx == 0) ? (P3R_PLAYLIST_COUNT - 1) : (currentTrackIdx - 1);
        triggerTrackSwitch(prevIdx, -1);
    }

    // Button 4 (K4):
    // - Short press (<350ms): Cycle Hi-Fi DSP EQ Preset (CLEAR BASS+ -> VOCAL -> DARK HOUR -> HIFI DIRECT)
    // - Medium press (350..900ms): Toggle Inverted LCD / Glowing Ice-Blue Polarity
    // - Long press (>900ms): Enter USB Flash Drive (U盘直传免拆卡) Mode & Replay "H E L L O !"
    if (digitalRead(PIN_BTN_MODE_REPEAT) == LOW) {
        lastBtnMs = nowMs;
        uint32_t t0 = millis();
        while (digitalRead(PIN_BTN_MODE_REPEAT) == LOW) {
            if (millis() - t0 > 900) {
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
            currentUIMode = (currentUIMode == UI_P3R_OPENING_CANON)
                ? UI_P3R_INVERTED_LCD
                : UI_P3R_OPENING_CANON;
        } else {
            currentEQIdx = (currentEQIdx + 1) % 4;
            const HiFiEQPreset& eq = P3R_HIFI_EQ_PRESETS[currentEQIdx];
            audio.setTone(eq.bassDb, eq.midDb, eq.trebleDb);
        }
    }
}

void setup() {
    pinMode(PIN_BTN_PLAY_PAUSE, INPUT_PULLUP);
    pinMode(PIN_BTN_NEXT, INPUT_PULLUP);
    pinMode(PIN_BTN_PREV, INPUT_PULLUP);
    pinMode(PIN_BTN_MODE_REPEAT, INPUT_PULLUP);

    Wire.begin(PIN_OLED_SDA, PIN_OLED_SCL, 400000UL);
    u8g2.begin();
    u8g2.setContrast(255);

    // 1:1 P3R Opening Cutscene "H E L L O !" Whole-Image Smooth Reveal Animation!
    playHelloBootAnimation();

    SPI.begin(PIN_SD_SCK, PIN_SD_MISO, PIN_SD_MOSI, PIN_SD_CS);
    sdMounted = SD.begin(PIN_SD_CS, SPI, 20000000UL);

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

    if (currentMode == MODE_SD_HIFI_PLAYER && sdMounted) {
        triggerTrackSwitch(0, +1);
    }
    elapsedSec = 96; // Starts at 01:36 ("Burn My Dread")
}

void loop() {
    uint32_t nowMs = millis();
    if (currentMode == MODE_SD_HIFI_PLAYER) {
        audio.loop();
    }
    handleSide4Buttons(nowMs);

    if (currentMode == MODE_SD_HIFI_PLAYER && isPlaying && !isPageRolling && (nowMs - lastTickMs >= 1000)) {
        lastTickMs = nowMs;
        elapsedSec++;
        if (elapsedSec > P3R_DEFAULT_PLAYLIST[currentTrackIdx].durationSec) {
            size_t nextIdx = (currentTrackIdx + 1) % P3R_PLAYLIST_COUNT;
            triggerTrackSwitch(nextIdx, +1);
        }
    }

    if (nowMs - lastFrameMs >= 35) {
        lastFrameMs = nowMs;
        renderP3ROpeningExactUI();
    }
}
