#pragma once
#include <Arduino.h>

// ============================================================================
// PERSONA 3 RELOAD (P3R) OPENING ANIMATION EXACT MP3 PLAYER - PINOUT
// ============================================================================
#define PIN_OLED_SDA        21
#define PIN_OLED_SCL        22

#define PIN_I2S_BCK         26
#define PIN_I2S_WS          25
#define PIN_I2S_DOUT        27
#define PIN_DAC_MUTE        32   // PCM5102A XSMT (High = Unmute)

#define PIN_SD_CS            5
#define PIN_SD_SCK          18
#define PIN_SD_MISO         19
#define PIN_SD_MOSI         23

// 4 Right-Edge Side-Actuated Tactile Buttons (`TS-1135-C`, matching Makoto's thumb buttons in P3R OP!)
#define PIN_BTN_PLAY_PAUSE  33   // SW1 (Top Oval Side Button)
#define PIN_BTN_NEXT        14   // SW2 (Upper-Mid Oval Side Button)
#define PIN_BTN_PREV        12   // SW3 (Lower-Mid Oval Side Button)
#define PIN_BTN_MODE_REPEAT 13   // SW4 (Bottom Oval Side Button: Short = Polarity, Long = Replay HELLO!)

#define PIN_BAT_ADC         35   // Battery Voltage Divider Input (100k/100k)

// ============================================================================
// P3R CANON PLAYLIST (Matches P3R OP sequence & exact clipped display strings!)
// ============================================================================
struct TrackInfo {
    const char* trackNum;
    const char* title;        // Full title
    const char* displayTitle; // Exact P3R OP truncated display string (e.g. "Want To Be Cl...")
    const char* artist;
    uint16_t durationSec;
    uint16_t opTimestampSec;  // Exact timestamp shown in P3R OP ("01:36", "02:33", etc.)
};

static const TrackInfo P3R_DEFAULT_PLAYLIST[] = {
    {"01", "Burn My Dread",              "Burn My Dread",    "Shoji Meguro / Lotus Juice",    96,  96}, // 01:36
    {"02", "Want To Be Close",           "Want To Be Cl...", "Azumi Takahashi / Shoji Meguro", 153, 153}, // 02:33
    {"03", "Full Moon Full Life",        "Full Moon Ful...", "Azumi Takahashi / Lotus Juice", 292, 292}, // 04:52
    {"04", "It's Going Down Now",        "It's Going Do...", "Azumi Takahashi / Lotus Juice", 186, 186}, // 03:06
    {"05", "Mass Destruction",           "Mass Destruct...", "Lotus Juice / Yumi Kawamura",   204, 204}, // 03:24
    {"06", "Color Your Night",           "Color Your Ni...", "Azumi Takahashi / Lotus Juice", 227, 227}, // 03:47
    {"07", "When The Moon's Reaching",   "When The Moon...", "Yumi Kawamura / Azumi Takahashi", 156, 156}, // 02:36
    {"08", "Changing Seasons",           "Changing Seas...", "Azumi Takahashi / Lotus Juice", 181, 181}, // 03:01
    {"09", "Iwatodai Dorm",              "Iwatodai Dorm",    "Lotus Juice / Shoji Meguro",    162, 162}, // 02:42
    {"10", "Aria of the Soul",           "Aria of the S...", "Shoji Meguro",                  338, 338}, // 05:38
    {"11", "The Battle for Everyone's",  "The Battle fo...", "Shoji Meguro",                  334, 334}, // 05:34
    {"12", "Memories of You",            "Memories of Y...", "Yumi Kawamura / Azumi Takahashi", 358, 358}  // 05:58
};

static const size_t P3R_PLAYLIST_COUNT = sizeof(P3R_DEFAULT_PLAYLIST) / sizeof(P3R_DEFAULT_PLAYLIST[0]);
