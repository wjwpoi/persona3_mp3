#pragma once
#include <Arduino.h>

// ============================================================================
// PERSONA 3 RELOAD (P3R) OPENING ANIMATION EXACT MP3 PLAYER - REV 2.5 PINOUT
// Hardware: Waveshare ESP32-S3-Zero + PCM5102A + TPA6132A2 + 2.25" 76x284 ST7789P3 TFT + TF-01A + Rear 4-Key
// ============================================================================
#define PIN_TFT_MOSI         8   // GP8  -> ST7789P3 SDA (Pin 5)
#define PIN_TFT_SCLK         9   // GP9  -> ST7789P3 SCL (Pin 6) [10k PU: keep HIGH at strapping]
#define PIN_TFT_DC          43   // GP43 (TX) -> ST7789P3 RS/DC (Pin 4)
#define PIN_TFT_CS          -1   // Hardware CS pulled to GND via 10k (dedicated SPI bus)
#define PIN_TFT_RST         -1   // Hardware RC Power-On Reset (10k + 1uF)
#define PIN_TFT_BLK         44   // GP44 (RX) -> Q1 (AO3401A P-MOS) Backlight PWM / Sleep Shutoff (Pin 1 LEDA)

#define PIN_PERI_PWR_EN     14   // GP14 -> Q3 (AO3401A P-MOSFET) Gate: LOW = Peripherals ON, 10k PU = Sleep OFF
#define PIN_VBAT_ADC        15   // GP15 (ADC2_CH4) -> 1:1 100k/100k VBAT divider (+100nF C27)

#define PIN_I2S_BCK          4   // GP4 -> PCM5102A BCK
#define PIN_I2S_WS           5   // GP5 -> PCM5102A LRCK (WS)
#define PIN_I2S_DOUT         6   // GP6 -> PCM5102A DIN

#define PIN_SD_CS           10   // GP10 -> TF-01A CS
#define PIN_SD_MOSI         11   // GP11 -> TF-01A MOSI
#define PIN_SD_SCK          12   // GP12 -> TF-01A SCK
#define PIN_SD_MISO         13   // GP13 -> TF-01A MISO

// 4 Rear Flush Pill Buttons (TS263065A K1..K4)
#define PIN_BTN_PLAY_PAUSE   1   // GP1 -> K1 (Short=Play/Pause, Hold 2.5s=Deep Sleep Power-Off!)
#define PIN_BTN_NEXT         2   // GP2 -> K2 (Short=Next Track, Hold=Vol Up)
#define PIN_BTN_PREV         3   // GP3 -> K3 (Short=Prev Track, Hold=Vol Down)
#define PIN_BTN_MODE_REPEAT  7   // GP7 -> K4 (Short=EQ/Loop, Med 350..1000ms=Polarity, Long >=1000ms=USB MSC Reboot / Exit!)

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
