#pragma once
#include <Arduino.h>

// ============================================================================
// PERSONA 3 / P3R MP3 PLAYER - PIN DEFINITIONS (ESP32-PICO-MINI-02)
// ============================================================================
#define PIN_OLED_SDA        21
#define PIN_OLED_SCL        22

#define PIN_I2S_BCK         26
#define PIN_I2S_WS          25
#define PIN_I2S_DOUT        27
#define PIN_DAC_MUTE        32   // PCM5102A XSMT (Soft Mute: High = Unmute, Low = Mute)

#define PIN_SD_CS            5
#define PIN_SD_SCK          18
#define PIN_SD_MISO         19
#define PIN_SD_MOSI         23

#define PIN_JOG_NEXT        33   // SLLB510100 Jog CW (Active Low)
#define PIN_JOG_PREV        14   // SLLB510100 Jog CCW (Active Low)
#define PIN_JOG_PUSH        12   // SLLB510100 Center Push (Active Low)
#define PIN_SW_MODE_HOLD    13   // MSK-12C02 Slide Switch
#define PIN_BAT_ADC         35   // Battery Voltage Divider Input (100k/100k)

// ============================================================================
// P3 / P3R CANON DEFAULT PLAYLIST & PIXEL BITMAPS (128x32 SSD1306)
// ============================================================================
struct TrackInfo {
    const char* trackNum;
    const char* title;
    const char* artist;
    uint16_t durationSec;
};

static const TrackInfo P3R_DEFAULT_PLAYLIST[] = {
    {"01", "BURN MY DREAD",              "Shoji Meguro / Lotus Juice", 96},
    {"02", "Full Moon Full Life",        "Azumi Takahashi / Lotus Juice", 292},
    {"03", "It's Going Down Now",        "Azumi Takahashi / Lotus Juice", 186},
    {"04", "Mass Destruction -Reload-",  "Lotus Juice / Yumi Kawamura", 204},
    {"05", "Color Your Night",           "Azumi Takahashi / Lotus Juice", 227},
    {"06", "When The Moon's Reaching",   "Yumi Kawamura / Azumi Takahashi", 156},
    {"07", "Want To Be Close -Reload-",  "Azumi Takahashi / Shoji Meguro", 153},
    {"08", "Changing Seasons -Reload-",  "Azumi Takahashi / Lotus Juice", 181},
    {"09", "Iwatodai Dorm -Reload-",     "Lotus Juice / Shoji Meguro", 162},
    {"10", "Aria of the Soul (Velvet)",  "Shoji Meguro", 338},
    {"11", "The Battle for Everyone's",  "Shoji Meguro", 334},
    {"12", "Memories of You (Kimi no)",  "Yumi Kawamura / Azumi Takahashi", 358}
};

static const size_t P3R_PLAYLIST_COUNT = sizeof(P3R_DEFAULT_PLAYLIST) / sizeof(P3R_DEFAULT_PLAYLIST[0]);

// S.E.E.S. / DARK HOUR Crest 16x16 XBM Icon
static const uint8_t SEES_CREST_16X16[] PROGMEM = {
    0xE0, 0x07, 0x18, 0x18, 0x04, 0x20, 0xE2, 0x47,
    0x12, 0x48, 0x89, 0x91, 0x49, 0x92, 0x29, 0x94,
    0x29, 0x94, 0x49, 0x92, 0x89, 0x91, 0x12, 0x48,
    0xE2, 0x47, 0x04, 0x20, 0x18, 0x18, 0xE0, 0x07
};

// Moon Phase Icons (8x8 XBM) - Full Moon, Half Moon, Crescent Moon
static const uint8_t ICON_FULL_MOON_8X8[] PROGMEM = {
    0x3C, 0x7E, 0xFF, 0xFF, 0xFF, 0xFF, 0x7E, 0x3C
};

static const uint8_t ICON_CRESCENT_MOON_8X8[] PROGMEM = {
    0x3C, 0x78, 0xF0, 0xE0, 0xE0, 0xF0, 0x78, 0x3C
};
