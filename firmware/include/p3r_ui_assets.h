#pragma once
#include <Arduino.h>

// ============================================================================
// PERSONA 3 RELOAD (P3R) OPENING ANIMATION EXACT MP3 PLAYER - PINOUT
// Matches Plan-A Taobao Kit: Waveshare ESP32-S3-Zero-M + GY-PCM5102 + 0.91" OLED + Mini SD + 4-Key Keypad
// ============================================================================
#define PIN_OLED_SDA         8   // GP8 -> 0.91" OLED SDA
#define PIN_OLED_SCL         9   // GP9 -> 0.91" OLED SCL

#define PIN_I2S_BCK          4   // GP4 -> GY-PCM5102 BCK
#define PIN_I2S_WS           5   // GP5 -> GY-PCM5102 LCK (WS)
#define PIN_I2S_DOUT         6   // GP6 -> GY-PCM5102 DIN

#define PIN_SD_CS           10   // GP10 -> Mini SD CS
#define PIN_SD_MOSI         11   // GP11 -> Mini SD MOSI
#define PIN_SD_SCK          12   // GP12 -> Mini SD SCK
#define PIN_SD_MISO         13   // GP13 -> Mini SD MISO

// 4 Right-Edge Side Buttons (`4位独立键盘模块` K1..K4, matching Makoto's thumb buttons in P3R OP!)
#define PIN_BTN_PLAY_PAUSE   1   // GP1 -> K1 (Top Button: PLAY / PAUSE)
#define PIN_BTN_NEXT         2   // GP2 -> K2 (Upper-Mid Button: NEXT TRACK)
#define PIN_BTN_PREV         3   // GP3 -> K3 (Lower-Mid Button: PREV TRACK)
#define PIN_BTN_MODE_REPEAT  7   // GP7 -> K4 (Bottom Button: Short=HiFi EQ, Med=Polarity, Long=USB Disk Mode / HELLO!)

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
