/**
 * Persona 3 Reload (P3R) Opening Animation 1:1 Screen-Accurate MP3 Player Firmware
 * Hardware: ESP32-PICO-MINI-02 + PCM5102A 32-Bit I2S DAC + 0.91" 128x32 OLED
 *
 * 1:1 P3R Opening Cutscene Complete Animation & UI Specification:
 * -------------------------------------------------------------------------
 * 1. Power-On Splash ("H E L L O !"):
 *    Characters 'H', 'E', 'L', 'L', 'O', '!' appear sequentially from left to right.
 * 2. Main Playback Screen ("Burn My Dread" / "Want To Be Cl..." / "Full Moon Ful..."):
 *    - Upper-Left: Play Triangle Icon `▶` (or Pause `❚❚`)
 *    - Upper-Center: Mixed-Case Bold Track Title with vertical roll transition on track switch!
 *      (During track change, the outgoing title rolls out vertically while the incoming title rolls in,
 *       clipped strictly to the title band Y: 1..15 so bottom letters get sliced in half just like Frame 3!)
 *    - Upper-Right: Repeat/Loop Arrows Icon `↻` + Outlined Battery Box `[  ]`
 *    - Lower-Left: Time Display (`01:36` -> `02:33` -> `04:52`)
 *    - Lower-Right: `VOL` vertical mini-label + 6 Vertical Barcode / Level Stripes `||||||`
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

static PlayerMode currentMode = MODE_SD_LOCAL;
static UIMode currentUIMode = UI_P3R_INVERTED_LCD;
static size_t currentTrackIdx = 0;
static size_t prevTrackIdx = 0;
static bool isPlaying = true;
static bool isRepeatLoop = true;
static uint8_t currentVolume = 16; // 0..21
static uint32_t elapsedSec = 96;   // Starts at 01:36 ("Burn My Dread")
static uint32_t lastTickMs = 0;
static uint32_t lastFrameMs = 0;

// Vertical Page-Flip / Drum-Roll Animation State (Matches Frame 3 of P3R Opening!)
static bool isPageRolling = false;
static int8_t rollDirection = 1;   // +1 = Next (scrolls up/down), -1 = Prev
static int16_t rollOffsetPx = 0;   // 0..16 pixels vertical transition

static String btTrackTitle = "Burn My Dread";

void avrc_metadata_callback(uint8_t id, const uint8_t *text) {
    if (id == ESP_AVRC_MD_ATTR_TITLE && text != nullptr) {
        btTrackTitle = String((const char*)text);
    }
}

void triggerTrackSwitch(size_t newIdx, int8_t dir) {
    prevTrackIdx = currentTrackIdx;
    currentTrackIdx = newIdx;
    rollDirection = dir;
    rollOffsetPx = 0;
    isPageRolling = true;
    elapsedSec = P3R_DEFAULT_PLAYLIST[currentTrackIdx].opTimestampSec;

    if (currentMode == MODE_SD_LOCAL && SD.begin(PIN_SD_CS)) {
        char filename[64];
        snprintf(filename, sizeof(filename), "/%s.mp3", P3R_DEFAULT_PLAYLIST[currentTrackIdx].trackNum);
        if (SD.exists(filename)) {
            audio.connecttoFS(SD, filename);
            elapsedSec = 0;
        }
    }
}

// ============================================================================
// P3R OPENING CUTSCENE BOOT ANIMATION: "H E L L O !" LEFT-TO-RIGHT REVEAL
// ============================================================================
void playHelloBootAnimation() {
    static const char HELLO_CHARS[6] = {'H', 'E', 'L', 'L', 'O', '!'};
    static const int16_t CHAR_X[6]   = {18,  35,  52,  69,  86,  105};

    u8g2.clearBuffer();
    if (currentUIMode == UI_P3R_INVERTED_LCD) {
        u8g2.setDrawColor(1);
        u8g2.drawBox(0, 0, 128, 32);
    }
    u8g2.sendBuffer();
    delay(220);

    for (int step = 1; step <= 6; step++) {
        u8g2.clearBuffer();
        if (currentUIMode == UI_P3R_INVERTED_LCD) {
            u8g2.setDrawColor(1);
            u8g2.drawBox(0, 0, 128, 32);
            u8g2.setDrawColor(0);
        } else {
            u8g2.setDrawColor(1);
        }

        u8g2.setFont(u8g2_font_helvB14_tr);
        char singleChar[2] = {0, 0};
        for (int i = 0; i < step; i++) {
            singleChar[0] = HELLO_CHARS[i];
            u8g2.drawStr(CHAR_X[i], 23, singleChar);
        }
        u8g2.sendBuffer();
        delay(180);
    }
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

// Render 1:1 Screen-Accurate P3R Opening Cutscene Playback UI (with Vertical Drum-Roll Page Animation!)
void renderP3ROpeningExactUI() {
    u8g2.clearBuffer();

    if (currentUIMode == UI_P3R_INVERTED_LCD) {
        u8g2.setDrawColor(1);
        u8g2.drawBox(0, 0, 128, 32);
        u8g2.setDrawColor(0);
    } else {
        u8g2.setDrawColor(1);
    }

    // 1. UPPER-LEFT PLAY / PAUSE ICON (X: 3..8, Y: 4..12)
    if (isPlaying) {
        u8g2.drawTriangle(3, 4, 3, 12, 8, 8);
    } else {
        u8g2.drawBox(3, 4, 2, 8);
        u8g2.drawBox(6, 4, 2, 8);
    }

    // 2. UPPER-CENTER TRACK TITLE WITH VERTICAL PAGE-ROLL ANIMATION (X: 13..95, Clip Y: 1..15)
    // Matches Frame 3 ("Want To Be Cl..." mid-vertical-scroll where letters are clipped horizontally!)
    u8g2.setFont(u8g2_font_helvB10_tf);
    u8g2.setClipWindow(12, 1, 95, 15);

    const char* curTitle = (currentMode == MODE_SD_LOCAL)
        ? P3R_DEFAULT_PLAYLIST[currentTrackIdx].displayTitle
        : btTrackTitle.c_str();

    if (isPageRolling) {
        const char* oldTitle = P3R_DEFAULT_PLAYLIST[prevTrackIdx].displayTitle;
        // Outgoing track slides vertically out; incoming track slides vertically in from the opposite edge!
        int16_t outY = 13 + rollDirection * rollOffsetPx;
        int16_t inY  = 13 - rollDirection * (16 - rollOffsetPx);
        u8g2.drawStr(13, outY, oldTitle);
        u8g2.drawStr(13, inY,  curTitle);

        rollOffsetPx += 3; // Smooth 5-frame vertical page flip
        if (rollOffsetPx >= 16) {
            isPageRolling = false;
            rollOffsetPx = 0;
        }
    } else {
        u8g2.drawStr(13, 13, curTitle);
    }
    u8g2.setMaxClipWindow();

    // 3. UPPER-RIGHT REPEAT LOOP ICON `↻` + BATTERY OUTLINE (X: 98..125)
    if (isRepeatLoop) {
        drawRepeatLoopIcon(98, 5);
    }
    u8g2.drawFrame(112, 5, 11, 6);
    u8g2.drawBox(123, 6, 2, 4);

    // 4. LOWER-LEFT ELAPSED TIME (`01:36` -> `02:33`) (X: 13, Y: 28)
    u8g2.setFont(u8g2_font_6x12_tf);
    char timeBuf[16];
    uint16_t mins = elapsedSec / 60;
    uint16_t secs = elapsedSec % 60;
    snprintf(timeBuf, sizeof(timeBuf), "%02u:%02u", mins, secs);
    u8g2.drawStr(13, 28, timeBuf);

    // 5. LOWER-RIGHT TINY "VOL" INDICATOR + 6 VERTICAL BARCODE STRIPES (`||||||`) (X: 92..112, Y: 20..28)
    // Notice in Frame 3 right above the 6 bars there is a tiny "VOL" micro-label!
    u8g2.setFont(u8g2_font_micro_tr);
    u8g2.drawStr(83, 26, "VOL");
    for (int i = 0; i < 6; i++) {
        u8g2.drawBox(98 + i * 2, 20, 1, 8);
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

    // Button 2 (Upper-Mid Oval Pill Button): NEXT TRACK (triggers vertical page-roll animation!)
    if (digitalRead(PIN_BTN_NEXT) == LOW) {
        lastBtnMs = nowMs;
        size_t nextIdx = (currentTrackIdx + 1) % P3R_PLAYLIST_COUNT;
        triggerTrackSwitch(nextIdx, +1);
        if (currentMode == MODE_BLUETOOTH_DAC) a2dp_sink.next();
    }

    // Button 3 (Lower-Mid Oval Pill Button): PREV TRACK (triggers reverse vertical page-roll animation!)
    if (digitalRead(PIN_BTN_PREV) == LOW) {
        lastBtnMs = nowMs;
        size_t prevIdx = (currentTrackIdx == 0) ? (P3R_PLAYLIST_COUNT - 1) : (currentTrackIdx - 1);
        triggerTrackSwitch(prevIdx, -1);
        if (currentMode == MODE_BLUETOOTH_DAC) a2dp_sink.previous();
    }

    // Button 4 (Bottom Oval Pill Button): Short press = Toggle Polarity, Long press = Replay "HELLO!"
    if (digitalRead(PIN_BTN_MODE_REPEAT) == LOW) {
        lastBtnMs = nowMs;
        uint32_t t0 = millis();
        while (digitalRead(PIN_BTN_MODE_REPEAT) == LOW) {
            if (millis() - t0 > 600) {
                playHelloBootAnimation();
                return;
            }
            delay(10);
        }
        currentUIMode = (currentUIMode == UI_P3R_OPENING_CANON)
            ? UI_P3R_INVERTED_LCD
            : UI_P3R_OPENING_CANON;
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

    // 1:1 P3R Opening Cutscene "H E L L O !" Left-to-Right Boot Animation!
    playHelloBootAnimation();

    SPI.begin(PIN_SD_SCK, PIN_SD_MISO, PIN_SD_MOSI, PIN_SD_CS);
    audio.setPinout(PIN_I2S_BCK, PIN_I2S_WS, PIN_I2S_DOUT);
    audio.setVolume(currentVolume);
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

    if (nowMs - lastFrameMs >= 40) {
        lastFrameMs = nowMs;
        renderP3ROpeningExactUI();
    }
}
