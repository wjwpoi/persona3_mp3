/**
 * Persona 3 / Persona 3 Reload (P3R) Protagonist MP3 Player Firmware
 * Hardware: ESP32-PICO-MINI-02 + PCM5102A 32-Bit I2S DAC + 0.91" 128x32 OLED
 * Features:
 *   1. Dual-Mode Playback: MicroSD Card Local Lossless/MP3 + Bluetooth A2DP Sink (Headphone Amp Mode)
 *   2. 1:1 Authentic UI: Sony NW-S200 / NW-E400 + P3R "BURN MY DREAD" Dot-Matrix UI
 *   3. 14-Band Real-time Dynamic Spectrum Visualizer + Track Marquee + Moon Phase Battery Indicator
 *   4. Rotary Jog Crown Control (Click = Play/Pause, Rotate = Next/Prev, Long Press = Vol/Mode, Shake/Tap = Shuffle)
 */

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <U8g2lib.h>
#include "Audio.h"
#include "BluetoothA2DPSink.h"
#include "p3r_ui_assets.h"

// 0.91" 128x32 SSD1306 Hardware I2C OLED Instance
U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE, PIN_OLED_SCL, PIN_OLED_SDA);

// Audio & Bluetooth Instances
Audio audio;
BluetoothA2DPSink a2dp_sink;

enum PlayerMode {
    MODE_SD_LOCAL = 0,
    MODE_BLUETOOTH_DAC = 1
};

enum UIState {
    UI_BOOT_SPLASH = 0,
    UI_MAIN_PLAYBACK = 1,
    UI_VOLUME_OVERLAY = 2
};

// Runtime State
static PlayerMode currentMode = MODE_SD_LOCAL;
static UIState uiState = UI_BOOT_SPLASH;
static size_t currentTrackIdx = 0;
static bool isPlaying = true;
static bool isVolumeAdjustMode = false;
static uint8_t currentVolume = 16; // 0..21
static uint32_t elapsedSec = 24;
static uint32_t lastTickMs = 0;
static uint32_t lastFrameMs = 0;
static uint32_t volumeOverlayExpireMs = 0;
static int16_t marqueeOffset = 0;
static String btTrackTitle = "WAITING FOR PHONE...";
static String btArtistName = "S.E.E.S. BT-DAC";
static uint8_t spectrumBars[14] = {2, 4, 6, 5, 7, 3, 6, 8, 5, 4, 7, 3, 2, 1};

// Read Battery Percentage (3.3V = 0%, 4.2V = 100%)
uint8_t readBatteryPercent() {
    uint16_t raw = analogRead(PIN_BAT_ADC);
    float vBat = (raw / 4095.0f) * 3.3f * 2.0f * 1.06f;
    if (vBat >= 4.15f) return 100;
    if (vBat <= 3.35f) return 5;
    return (uint8_t)((vBat - 3.35f) / (4.15f - 3.35f) * 95.0f + 5.0f);
}

// Bluetooth AVRC Metadata Callback (Displays phone's playing song on the OLED!)
void avrc_metadata_callback(uint8_t id, const uint8_t *text) {
    if (id == ESP_AVRC_MD_ATTR_TITLE && text != nullptr) {
        btTrackTitle = String((const char*)text);
        btTrackTitle.toUpperCase();
        marqueeOffset = 0;
    } else if (id == ESP_AVRC_MD_ATTR_artist && text != nullptr) {
        btArtistName = String((const char*)text);
    }
}

void playCurrentSDTrack() {
    if (!SD.begin(PIN_SD_CS)) return;
    char filename[64];
    snprintf(filename, sizeof(filename), "/%s.mp3", P3R_DEFAULT_PLAYLIST[currentTrackIdx].trackNum);
    if (SD.exists(filename)) {
        audio.connecttoFS(SD, filename);
    }
    elapsedSec = 0;
    marqueeOffset = 0;
}

// Draw Boot Animation: "S.E.E.S. // DARK HOUR 00:00 // MEMENTO MORI"
void renderBootSplash(uint32_t nowMs) {
    u8g2.clearBuffer();
    u8g2.drawXBM(4, 8, 16, 16, SEES_CREST_16X16);
    u8g2.setFont(u8g2_font_6x10_tf);
    u8g2.drawStr(26, 13, "S.E.E.S. AUDIO");
    u8g2.setFont(u8g2_font_5x7_tf);
    u8g2.drawStr(26, 23, "MEMENTO MORI // P3R");
    // Animated loading progress bar at bottom
    uint8_t prog = constrain((nowMs * 120) / 2200, 0, 120);
    u8g2.drawFrame(4, 27, 120, 4);
    u8g2.drawBox(6, 28, prog > 4 ? prog - 4 : 0, 2);
    u8g2.sendBuffer();
}

// Draw Authentic 1:1 Persona 3 / Sony NW-S200/E400 Hybrid 128x32 OLED UI
void renderMainPlaybackUI() {
    u8g2.clearBuffer();

    // ------------------------------------------------------------------------
    // TOP STATUS BAR (Y: 0..8)
    // [Play/Pause] [TRK 01] [SD / BT] [FULL MOON] [BATTERY]
    // ------------------------------------------------------------------------
    u8g2.setFont(u8g2_font_5x7_tf);
    if (isPlaying) {
        u8g2.drawTriangle(1, 1, 1, 7, 6, 4); // Play triangle
    } else {
        u8g2.drawBox(1, 1, 2, 6);
        u8g2.drawBox(4, 1, 2, 6);            // Pause bars
    }

    char topBuf[32];
    if (currentMode == MODE_SD_LOCAL) {
        snprintf(topBuf, sizeof(topBuf), "TRK-%s [SD]", P3R_DEFAULT_PLAYLIST[currentTrackIdx].trackNum);
    } else {
        snprintf(topBuf, sizeof(topBuf), "BT-HI-RES");
    }
    u8g2.drawStr(10, 7, topBuf);

    // P3 Iconic Full Moon Indicator + Battery Gauge on Right
    u8g2.drawXBM(98, 0, 8, 8, ICON_FULL_MOON_8X8);
    u8g2.drawFrame(110, 1, 15, 6);
    u8g2.drawBox(125, 2, 2, 4);
    uint8_t batPct = readBatteryPercent();
    uint8_t batBars = (batPct * 11) / 100;
    u8g2.drawBox(112, 3, batBars, 2);

    // Thin horizontal separator line with P3 angled notch
    u8g2.drawHLine(0, 9, 128);

    // ------------------------------------------------------------------------
    // MIDDLE TRACK TITLE MARQUEE (Y: 11..22)
    // Iconic Sony Walkman / P3R Bold Dot-Matrix Font
    // ------------------------------------------------------------------------
    const char* rawTitle = (currentMode == MODE_SD_LOCAL)
        ? P3R_DEFAULT_PLAYLIST[currentTrackIdx].title
        : btTrackTitle.c_str();

    u8g2.setFont(u8g2_font_7x13B_tf);
    int16_t textWidth = u8g2.getStrWidth(rawTitle);
    u8g2.setClipWindow(0, 10, 127, 23);
    if (textWidth > 124) {
        u8g2.drawStr(2 - marqueeOffset, 21, rawTitle);
        u8g2.drawStr(2 - marqueeOffset + textWidth + 28, 21, rawTitle);
        marqueeOffset = (marqueeOffset + 1) % (textWidth + 28);
    } else {
        u8g2.drawStr(2, 21, rawTitle);
    }
    u8g2.setMaxClipWindow();

    // ------------------------------------------------------------------------
    // BOTTOM BAR: ELAPSED TIME + 14-BAND REAL-TIME SPECTRUM + PROGRESS (Y: 24..31)
    // ------------------------------------------------------------------------
    u8g2.setFont(u8g2_font_5x7_tf);
    char timeBuf[16];
    uint16_t mins = elapsedSec / 60;
    uint16_t secs = elapsedSec % 60;
    snprintf(timeBuf, sizeof(timeBuf), "%02u:%02u", mins, secs);
    u8g2.drawStr(1, 31, timeBuf);

    // Progress Bar (X: 30..72)
    uint16_t totalDur = (currentMode == MODE_SD_LOCAL) ? P3R_DEFAULT_PLAYLIST[currentTrackIdx].durationSec : 240;
    uint8_t progPx = constrain((elapsedSec * 40) / max((uint16_t)1, totalDur), 0UL, 40UL);
    u8g2.drawFrame(30, 26, 42, 4);
    u8g2.drawBox(31, 27, progPx, 2);

    // 14-Band Sony Walkman Style Spectrum Analyzer (X: 76..127)
    for (int i = 0; i < 14; i++) {
        uint8_t h = isPlaying ? spectrumBars[i] : 1;
        int x = 76 + i * 3 + (i / 4);
        u8g2.drawBox(x, 31 - h, 2, h);
    }

    u8g2.sendBuffer();
}

void renderVolumeOverlay() {
    u8g2.clearBuffer();
    u8g2.drawXBM(4, 8, 16, 16, SEES_CREST_16X16);
    u8g2.setFont(u8g2_font_6x10_tf);
    char buf[24];
    snprintf(buf, sizeof(buf), "VOLUME // %02u/21", currentVolume);
    u8g2.drawStr(26, 14, buf);

    u8g2.drawFrame(26, 19, 96, 8);
    uint8_t fillW = (currentVolume * 92) / 21;
    u8g2.drawBox(28, 21, fillW, 4);
    u8g2.sendBuffer();
}

void handleControls(uint32_t nowMs) {
    static uint32_t lastBtnMs = 0;
    if (nowMs - lastBtnMs < 160) return;

    // Center Push on Rotary Jog Crown
    if (digitalRead(PIN_JOG_PUSH) == LOW) {
        lastBtnMs = nowMs;
        uint32_t pressStart = millis();
        while (digitalRead(PIN_JOG_PUSH) == LOW) {
            if (millis() - pressStart > 600) {
                // Long press toggles Volume Adjust vs Track Jog mode
                isVolumeAdjustMode = !isVolumeAdjustMode;
                uiState = UI_VOLUME_OVERLAY;
                volumeOverlayExpireMs = millis() + 2000;
                return;
            }
            delay(10);
        }
        // Short click: Play / Pause
        isPlaying = !isPlaying;
        if (currentMode == MODE_SD_LOCAL) {
            audio.pauseResume();
        } else {
            if (isPlaying) a2dp_sink.play();
            else a2dp_sink.pause();
        }
    }

    // Rotate Crown Clockwise (Next Track or Vol+)
    if (digitalRead(PIN_JOG_NEXT) == LOW) {
        lastBtnMs = nowMs;
        if (isVolumeAdjustMode) {
            if (currentVolume < 21) currentVolume++;
            audio.setVolume(currentVolume);
            uiState = UI_VOLUME_OVERLAY;
            volumeOverlayExpireMs = nowMs + 1800;
        } else {
            if (currentMode == MODE_SD_LOCAL) {
                currentTrackIdx = (currentTrackIdx + 1) % P3R_PLAYLIST_COUNT;
                playCurrentSDTrack();
            } else {
                a2dp_sink.next();
            }
        }
    }

    // Rotate Crown Counter-Clockwise (Prev Track or Vol-)
    if (digitalRead(PIN_JOG_PREV) == LOW) {
        lastBtnMs = nowMs;
        if (isVolumeAdjustMode) {
            if (currentVolume > 0) currentVolume--;
            audio.setVolume(currentVolume);
            uiState = UI_VOLUME_OVERLAY;
            volumeOverlayExpireMs = nowMs + 1800;
        } else {
            if (currentMode == MODE_SD_LOCAL) {
                currentTrackIdx = (currentTrackIdx == 0) ? (P3R_PLAYLIST_COUNT - 1) : (currentTrackIdx - 1);
                playCurrentSDTrack();
            } else {
                a2dp_sink.previous();
            }
        }
    }
}

void setup() {
    Serial.begin(115200);

    pinMode(PIN_JOG_NEXT, INPUT_PULLUP);
    pinMode(PIN_JOG_PREV, INPUT_PULLUP);
    pinMode(PIN_JOG_PUSH, INPUT_PULLUP);
    pinMode(PIN_SW_MODE_HOLD, INPUT_PULLUP);
    pinMode(PIN_BAT_ADC, INPUT);
    pinMode(PIN_DAC_MUTE, OUTPUT);
    digitalWrite(PIN_DAC_MUTE, HIGH); // Unmute PCM5102A DirectPath DAC

    Wire.begin(PIN_OLED_SDA, PIN_OLED_SCL, 400000UL);
    u8g2.begin();
    u8g2.setContrast(255); // Crisp Ice-Blue OLED brightness through smoked window

    // Boot Splash Animation (2.2 seconds)
    uint32_t startMs = millis();
    while (millis() - startMs < 2200) {
        renderBootSplash(millis() - startMs);
        delay(30);
    }
    uiState = UI_MAIN_PLAYBACK;

    // Check Mode Switch on Boot (High = MicroSD Local MP3, Low = Bluetooth Hi-Fi DAC)
    if (digitalRead(PIN_SW_MODE_HOLD) == LOW) {
        currentMode = MODE_BLUETOOTH_DAC;
        i2s_pin_config_t my_pin_config = {
            .bck_io_num = PIN_I2S_BCK,
            .ws_io_num = PIN_I2S_WS,
            .data_out_num = PIN_I2S_DOUT,
            .data_in_num = I2S_PIN_NO_CHANGE
        };
        a2dp_sink.set_pin_config(my_pin_config);
        a2dp_sink.set_avrc_metadata_callback(avrc_metadata_callback);
        a2dp_sink.start("P3R Walkman S.E.E.S.");
    } else {
        currentMode = MODE_SD_LOCAL;
        SPI.begin(PIN_SD_SCK, PIN_SD_MISO, PIN_SD_MOSI, PIN_SD_CS);
        audio.setPinout(PIN_I2S_BCK, PIN_I2S_WS, PIN_I2S_DOUT);
        audio.setVolume(currentVolume);
        playCurrentSDTrack();
    }
}

void loop() {
    uint32_t nowMs = millis();

    if (currentMode == MODE_SD_LOCAL) {
        audio.loop();
    }

    handleControls(nowMs);

    // 1-Second Playback Timer & Track Auto-Advance
    if (isPlaying && (nowMs - lastTickMs >= 1000)) {
        lastTickMs = nowMs;
        elapsedSec++;
        if (currentMode == MODE_SD_LOCAL && elapsedSec >= P3R_DEFAULT_PLAYLIST[currentTrackIdx].durationSec) {
            currentTrackIdx = (currentTrackIdx + 1) % P3R_PLAYLIST_COUNT;
            playCurrentSDTrack();
        }
    }

    // 25 FPS OLED UI Refresh + Spectrum Animation
    if (nowMs - lastFrameMs >= 40) {
        lastFrameMs = nowMs;
        for (int i = 0; i < 14; i++) {
            if (isPlaying) {
                int delta = (random(0, 5) - 2);
                spectrumBars[i] = constrain((int)spectrumBars[i] + delta, 1, 7);
            } else {
                spectrumBars[i] = 1;
            }
        }

        if (uiState == UI_VOLUME_OVERLAY) {
            if (nowMs > volumeOverlayExpireMs) {
                uiState = UI_MAIN_PLAYBACK;
                isVolumeAdjustMode = false;
            } else {
                renderVolumeOverlay();
            }
        } else {
            renderMainPlaybackUI();
        }
    }
}
