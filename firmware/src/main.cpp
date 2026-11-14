/**
 * Persona 3 Reload (P3R) Opening Animation 1:1 Screen-Accurate MP3 Player Firmware
 * Hardware: ESP32-PICO-MINI-02 + PCM5102A 32-Bit I2S DAC + 0.91" 128x32 OLED
 *
 * 1:1 P3R Opening Cutscene Complete Animation & UI Specification (v3.0 Exact):
 * -------------------------------------------------------------------------
 * 1. Power-On Splash ("H E L L O !"):
 *    "H E L L O !" is rendered as a single complete graphic that smoothly reveals/wipes
 *    from left to right (via progressive horizontal clip window 0 -> 128px) while
 *    simultaneously fading in OLED contrast (`u8g2.setContrast(0 -> 255)`).
 * 2. Whole-Screen Vertical Page-Roll Transition (Matches Frame 3 of P3R Opening!):
 *    When switching tracks, the ENTIRE 128x32 screen (including `▶`, `01:36`/`02:33`,
 *    `Burn My Dread`/`Want To Be Cl...`, `↻`, `[Battery]`, and `VOL ||||||`) scrolls
 *    vertically as a unified full-screen page (`dy = 0..32px`)!
 */

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <U8g2lib.h>
#include "Audio.h"
#include "BluetoothA2DPSink.h"
#include "p3r_ui_assets.h"

U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE, PIN_OLED_SCL, PIN_OLED_SDA);

Audio audio;
BluetoothA2DPSink a2dp_sink;

enum PlayerMode {
    MODE_SD_LOCAL = 0,
    MODE_BLUETOOTH_DAC = 1
};

enum UIMode {
    UI_P3R_OPENING_CANON = 0, // Dark background + Glowing Ice-Blue Pixels
    UI_P3R_INVERTED_LCD  = 1  // Light background + Dark Pixels (exact anime backlit LCD look)
};

// Sony Walkman Clear-Bass & Clip-On Headphone (ATH-EM700/EQ300M) Hi-Fi DSP Presets
struct HiFiEQPreset {
    const char* name;
    int8_t bassDb;    // Low shelf (Clear Bass compensation for clip-on earhook headphones)
    int8_t midDb;     // Vocal presence (Yumi Kawamura / Azumi Takahashi / Lotus Juice)
    int8_t trebleDb;  // Air & brass sparkle
};

static const HiFiEQPreset P3R_HIFI_EQ_PRESETS[4] = {
    {"CLEAR BASS+", +5, +1, +3}, // Tuned for open clip-on headphones (ATH-EM700 / EQ300M)
    {"VOCAL BOOST", +1, +4, +3}, // Vocal-forward for Burn My Dread / Full Moon Full Life
    {"DARK HOUR",   +6,  0, +2}, // Deep sub-bass punch
    {"HIFI DIRECT",  0,  0,  0}  // Bit-perfect 32-bit PCM5102A reference output
};

static PlayerMode currentMode = MODE_SD_LOCAL;
static UIMode currentUIMode = UI_P3R_INVERTED_LCD;
static uint8_t currentEQIdx = 0; // Default: CLEAR BASS+ for clip-on headphones
static size_t currentTrackIdx = 0;
static size_t prevTrackIdx = 0;
static bool isPlaying = true;
static bool isRepeatLoop = true;
static uint8_t currentVolume = 16; // 0..21
static uint32_t elapsedSec = 96;   // Starts at 01:36 ("Burn My Dread")
static uint32_t prevElapsedSec = 96;
static uint32_t lastTickMs = 0;
static uint32_t lastFrameMs = 0;

// Whole-Screen Vertical Page-Roll State (Matches Frame 3 of P3R Opening!)
static bool isPageRolling = false;
static int8_t rollDirection = 1;   // +1 = Next (entire screen rolls vertically), -1 = Prev
static int16_t rollOffsetPx = 0;   // 0..32 pixels full-screen vertical transition

static String btTrackTitle = "Burn My Dread";

void avrc_metadata_callback(uint8_t id, const uint8_t *text) {
    if (id == ESP_AVRC_MD_ATTR_TITLE && text != nullptr) {
        btTrackTitle = String((const char*)text);
    }
}

void triggerTrackSwitch(size_t newIdx, int8_t dir) {
    prevTrackIdx = currentTrackIdx;
    prevElapsedSec = elapsedSec;
    currentTrackIdx = newIdx;
    rollDirection = dir;
    rollOffsetPx = 0;
    isPageRolling = true;
    elapsedSec = P3R_DEFAULT_PLAYLIST[currentTrackIdx].opTimestampSec;

    if (currentMode == MODE_SD_LOCAL && SD.begin(PIN_SD_CS)) {
        // Auto-detect Lossless FLAC (.flac), Uncompressed WAV (.wav), or 320kbps MP3 (.mp3)
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
    // Smooth 24-frame continuous graphic wipe + contrast fade-in (0 -> 128px, contrast 15 -> 255)
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

        // Clip progressively across the whole "H E L L O !" graphic so it emerges smoothly as a unified image
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

// Draw the Repeat Loop Icon `↻` (two opposing arrows, 10x7 px) at (x, y)
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

// Render a single full-screen page at vertical offset `yOff` (-32..+32 px)
// Every single element on the screen shifts together by `yOff`!
void drawSingleFullPage(size_t trkIdx, uint32_t timeSec, int16_t yOff) {
    // 1. UPPER-LEFT PLAY / PAUSE ICON (X: 3..8, Y: 4..12 + yOff)
    if (isPlaying) {
        u8g2.drawTriangle(3, 4 + yOff, 3, 12 + yOff, 8, 8 + yOff);
    } else {
        u8g2.drawBox(3, 4 + yOff, 2, 8);
        u8g2.drawBox(6, 4 + yOff, 2, 8);
    }

    // 2. UPPER-CENTER TRACK TITLE (X: 13..95, Y: 13 + yOff)
    const char* titleStr = (currentMode == MODE_SD_LOCAL)
        ? P3R_DEFAULT_PLAYLIST[trkIdx].displayTitle
        : btTrackTitle.c_str();
    u8g2.setFont(u8g2_font_helvB10_tf);
    u8g2.drawStr(13, 13 + yOff, titleStr);

    // 3. UPPER-RIGHT REPEAT LOOP ICON `↻` + BATTERY OUTLINE (X: 98..125, Y + yOff)
    if (isRepeatLoop) {
        drawRepeatLoopIcon(98, 5 + yOff);
    }
    u8g2.drawFrame(112, 5 + yOff, 11, 6);
    u8g2.drawBox(123, 6 + yOff, 2, 4);

    // 4. LOWER-LEFT ELAPSED TIME (`01:36` / `02:33`) (X: 13, Y: 28 + yOff)
    u8g2.setFont(u8g2_font_6x12_tf);
    char timeBuf[16];
    uint16_t mins = timeSec / 60;
    uint16_t secs = timeSec % 60;
    snprintf(timeBuf, sizeof(timeBuf), "%02u:%02u", mins, secs);
    u8g2.drawStr(13, 28 + yOff, timeBuf);

    // 5. LOWER-RIGHT TINY "VOL" INDICATOR + 6 VERTICAL BARCODE STRIPES (`||||||`) (Y + yOff)
    u8g2.setFont(u8g2_font_micro_tr);
    u8g2.drawStr(83, 26 + yOff, "VOL");
    for (int i = 0; i < 6; i++) {
        u8g2.drawBox(98 + i * 2, 20 + yOff, 1, 8);
    }
}

// Render 1:1 Screen-Accurate P3R Opening Cutscene UI (with Whole-Screen Vertical Roll!)
void renderP3ROpeningExactUI() {
    u8g2.clearBuffer();

    if (currentUIMode == UI_P3R_INVERTED_LCD) {
        u8g2.setDrawColor(1);
        u8g2.drawBox(0, 0, 128, 32);
        u8g2.setDrawColor(0);
    } else {
        u8g2.setDrawColor(1);
    }

    if (isPageRolling) {
        // Whole-screen vertical scroll: outgoing page and incoming page both move across all 32px height!
        // When rollDirection == +1 (scrolling down so new page enters from top, matching Frame 3):
        // Incoming page is at yOff = -32 + rollOffsetPx (top half of title clipped at top edge, bottom half visible!)
        // Outgoing page is at yOff = +rollOffsetPx (pushed down so its top elements sit at the bottom edge!)
        int16_t outYOff = rollDirection * rollOffsetPx;
        int16_t inYOff  = -rollDirection * (32 - rollOffsetPx);

        drawSingleFullPage(prevTrackIdx, prevElapsedSec, outYOff);
        drawSingleFullPage(currentTrackIdx, elapsedSec, inYOff);

        rollOffsetPx += 4; // Smooth 8-frame whole-screen vertical roll
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

    // Button 1 (Top Oval Pill Button): PLAY / PAUSE
    if (digitalRead(PIN_BTN_PLAY_PAUSE) == LOW) {
        lastBtnMs = nowMs;
        isPlaying = !isPlaying;
        if (currentMode == MODE_SD_LOCAL) audio.pauseResume();
        else {
            if (isPlaying) a2dp_sink.play();
            else a2dp_sink.pause();
        }
    }

    // Button 2 (Upper-Mid Oval Pill Button): NEXT TRACK (triggers whole-screen vertical roll!)
    if (digitalRead(PIN_BTN_NEXT) == LOW) {
        lastBtnMs = nowMs;
        size_t nextIdx = (currentTrackIdx + 1) % P3R_PLAYLIST_COUNT;
        triggerTrackSwitch(nextIdx, +1);
        if (currentMode == MODE_BLUETOOTH_DAC) a2dp_sink.next();
    }

    // Button 3 (Lower-Mid Oval Pill Button): PREV TRACK (triggers reverse whole-screen vertical roll!)
    if (digitalRead(PIN_BTN_PREV) == LOW) {
        lastBtnMs = nowMs;
        size_t prevIdx = (currentTrackIdx == 0) ? (P3R_PLAYLIST_COUNT - 1) : (currentTrackIdx - 1);
        triggerTrackSwitch(prevIdx, -1);
        if (currentMode == MODE_BLUETOOTH_DAC) a2dp_sink.previous();
    }

    // Button 4 (Bottom Oval Pill Button):
    // - Short press: Cycle Hi-Fi DSP EQ Preset (CLEAR BASS+ -> VOCAL -> DARK HOUR -> HIFI DIRECT)
    // - Double/Medium press (>350ms): Toggle Inverted LCD / Glowing Ice-Blue Polarity
    // - Long press (>800ms): Replay "H E L L O !" Boot Animation
    if (digitalRead(PIN_BTN_MODE_REPEAT) == LOW) {
        lastBtnMs = nowMs;
        uint32_t t0 = millis();
        while (digitalRead(PIN_BTN_MODE_REPEAT) == LOW) {
            if (millis() - t0 > 800) {
                playHelloBootAnimation();
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
    Serial.begin(115200);

    pinMode(PIN_BTN_PLAY_PAUSE, INPUT_PULLUP);
    pinMode(PIN_BTN_NEXT, INPUT_PULLUP);
    pinMode(PIN_BTN_PREV, INPUT_PULLUP);
    pinMode(PIN_BTN_MODE_REPEAT, INPUT_PULLUP);
    pinMode(PIN_BAT_ADC, INPUT);
    pinMode(PIN_DAC_MUTE, OUTPUT);
    digitalWrite(PIN_DAC_MUTE, HIGH);

    Wire.begin(PIN_OLED_SDA, PIN_OLED_SCL, 400000UL);
    u8g2.begin();
    u8g2.setContrast(255);

    // 1:1 P3R Opening Cutscene "H E L L O !" Whole-Image Smooth Reveal Animation!
    playHelloBootAnimation();

    SPI.begin(PIN_SD_SCK, PIN_SD_MISO, PIN_SD_MOSI, PIN_SD_CS);
    audio.setPinout(PIN_I2S_BCK, PIN_I2S_WS, PIN_I2S_DOUT);
    audio.setVolume(currentVolume);
    // Apply default Hi-Fi Clear Bass+ DSP preset for clip-on earhook headphones
    const HiFiEQPreset& eq = P3R_HIFI_EQ_PRESETS[currentEQIdx];
    audio.setTone(eq.bassDb, eq.midDb, eq.trebleDb);
    elapsedSec = 96; // Starts at 01:36 ("Burn My Dread")
}

void loop() {
    uint32_t nowMs = millis();
    if (currentMode == MODE_SD_LOCAL) {
        audio.loop();
    }
    handleSide4Buttons(nowMs);

    if (isPlaying && !isPageRolling && (nowMs - lastTickMs >= 1000)) {
        lastTickMs = nowMs;
        elapsedSec++;
        if (currentMode == MODE_SD_LOCAL && elapsedSec > P3R_DEFAULT_PLAYLIST[currentTrackIdx].durationSec) {
            size_t nextIdx = (currentTrackIdx + 1) % P3R_PLAYLIST_COUNT;
            triggerTrackSwitch(nextIdx, +1);
        }
    }

    if (nowMs - lastFrameMs >= 35) {
        lastFrameMs = nowMs;
        renderP3ROpeningExactUI();
    }
}
