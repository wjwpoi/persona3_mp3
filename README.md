# 🎧 Persona 3 / Persona 3 Reload (P3R) 主角 MP3 随身听 1:1 复刻开源工程

[![License: MIT](https://img.shields.io/badge/License-MIT-00e5ff.svg)](LICENSE)
[![Manufacturing: JLCPCB & JLC CNC](https://img.shields.io/badge/Manufacturing-嘉立创一站式制造-1e90ff.svg)](docs/JLCPCB_ORDER_AND_ASSEMBLY_GUIDE.md)
[![Assembly: Zero Solder](https://img.shields.io/badge/Assembly-0焊点全贴片免焊组装-10b981.svg)](docs/JLCPCB_ORDER_AND_ASSEMBLY_GUIDE.md)
[![Cost: ~366 RMB](https://img.shields.io/badge/BOM%20%2B%20CNC%20Cost-¥366%20(%3C500元)-f59e0b.svg)](docs/JLCPCB_ORDER_AND_ASSEMBLY_GUIDE.md)

> **"MEMENTO MORI // BURN MY DREAD"**
> 本项目旨在 **1:1 完美还原**《女神异闻录3 / 女神异闻录3 Reload》（Persona 3 / P3R）主人公（结城理 / Makoto Yuki）挂在胸前的标志性银黑圆柱形 MP3 随身听。
> 兼具 **P3R 官方 1:1 金属道具模型的外形尺寸（Φ20mm × 80mm）** 与 **索尼千禧年传奇 Walkman（NW-S200 运动棒 / NW-E400 香水瓶）的隐藏式冰蓝 OLED 点阵 UI**，并针对 **嘉立创（PCB + SMT 全贴片 + CNC 铝合金 + 3D 打印）** 进行了全套生产级免焊工程设计。

---

## ✨ 核心特性 (Key Highlights)

1. **1:1 严苛外观还原（Φ20.0mm × 80.0mm）**
   - 严格对齐 Atlus / Kadokawa 官方 P3R 1:1 道具尺寸（直径 `20.0mm`，总长 `80.0mm`）与索尼 `NW-S203F / NW-E405` 工业美学。
   - **CNC 6061 喷砂阳极氧化银铝管机身** + **顶部精密滚花旋钮环（Jog Crown）** + **底部一体式扁平挂绳金属环** + **深色半透隐藏式 OLED 弧面视窗**（熄屏纯黑无边框，亮屏浮现冰蓝点阵文字）。
2. **像素级还原 P3 / 索尼 Walkman 点阵 UI**
   - 采用 `0.91 寸 128×32 SSD1306` 冰蓝光 PMOLED，25FPS 高刷渲染：
   - **开机动画**：`S.E.E.S. AUDIO // MEMENTO MORI // P3R` 徽章与动态进度条。
   - **播放主界面**：左上角播放状态 + 曲目编号 (`TRK-01 [SD]` / `BT-HI-RES`) + **P3 标志性满月图标 (Full Moon)** + 实时电量槽；中区粗体点阵滚动歌名（内置 `BURN MY DREAD`、`Full Moon Full Life`、`It's Going Down Now`、`Mass Destruction` 等 12 首经典曲目元数据）；底部实时时间、进度条与 **14 段索尼经典动态频谱柱 (Spectrum Analyzer)**。
3. **真 Hi-Fi 双模音源（MicroSD 独立插卡 + 蓝牙解码耳放）**
   - **主控**：`ESP32-PICO-MINI-02-N8R2`（双核 240MHz + 8MB Flash + 2MB PSRAM）。
   - **独立 Hi-Fi DAC**：搭载德州仪器 `PCM5102APWR`（32-bit / 384kHz I2S 立体声 DAC，内置 DirectPath 负压电荷泵，2.1Vrms 免隔直电容直推铁三角 `ATH-EM700` / `EQ300M` 耳挂耳机，低频饱满、零底噪）。
   - **双模切换**：既可插 MicroSD 卡完全脱离手机重温 2006 年随身听体验，也可拨动开关变身 **蓝牙 A2DP 解码耳放**（并在 OLED 屏上实时同步显示手机当前播放的歌名！）。
4. **真正的「0 焊点」全贴片免焊设计（总成本 ≈ ¥366 元）**
   - 所有接口（USB Type-C、3.5mm 耳机孔、MicroSD 卡槽、Alps 三向旋钮拨杆、14P 0.5mm 屏幕 FPC 座、JST-SH 1.0mm 电池插座）全部采用 **嘉立创 SMT 机器预贴装**。
   - 玩家收到嘉立创寄来的 PCBA 和外壳后，**完全不需要电烙铁**，只需插上屏幕排线和电池插头、拧上 2 颗 M1.6 螺丝即可完成组装！

---

## 📂 仓库目录结构 (Repository Layout)

```text
persona3_mp3/
├── cad/
│   ├── scripts/
│   │   └── generate_cad_models.py                  # 参数化 3D 结构生成脚本 (Φ20x80mm)
│   └── stl/                                        # 嘉立创 CNC 与 3D 打印直接下单 STL 模型文件
│       ├── 00_full_assembled_p3r_mp3.stl           # 整机总装预览模型
│       ├── 01_cnc_main_shell_6061_silver.stl       # [CNC 6061铝] 主机身圆管壳体
│       ├── 02_oled_smoked_lens_translucent_black.stl # [3D打印 8001半透树脂] 隐藏式弧面滤光窗
│       ├── 03_rotary_jog_crown_knurled.stl         # [CNC 6061铝] 顶部滚花旋钮环 (Jog Shuttle)
│       ├── 04_top_cap_headphone_port.stl           # [CNC 6061铝] 顶部 3.5mm 耳机孔端盖
│       ├── 05_bottom_lanyard_cap.stl               # [CNC 6061铝] 底部 P3 挂绳环端盖
│       └── 06_internal_zero_solder_sled.stl        # [3D打印 黑色韧性树脂] 内部免焊一体固定内胆架
├── hardware/
│   ├── generate_hardware_files.py                  # 硬件生产文件自动化生成脚本
│   ├── kicad/
│   │   └── persona3_mp3.kicad_pcb                  # KiCad 4层沉金 PCB 源文件 (68.0 x 14.4 x 1.0mm)
│   └── gerber_and_smt/                             # 嘉立创 PCB + SMT 一键下单包
│       ├── Gerber_JLCPCB_Persona3_MP3_4Layer.zip   # 直接上传嘉立创的 4层板 Gerber + 钻孔压缩包
│       ├── BOM_JLCPCB_Persona3_MP3.csv             # 嘉立创 SMT 物料清单 (含验证过的立创 C 编号)
│       └── CPL_PickAndPlace_JLCPCB_Persona3_MP3.csv # 嘉立创 SMT 贴片坐标文件
├── firmware/
│   ├── platformio.ini                              # PlatformIO 工程配置文件
│   ├── include/
│   │   └── p3r_ui_assets.h                         # 引脚定义、P3R 歌单与 S.E.E.S. 像素图标字模
│   └── src/
│       └── main.cpp                                # ESP32 双模音频解码 + 128x32 OLED UI 完整源码
├── ui_preview/
│   └── index.html                                  # 浏览器端 1:1 外观与 OLED 像素级交互仿真器 (双击即开)
└── docs/
    └── JLCPCB_ORDER_AND_ASSEMBLY_GUIDE.md          # 嘉立创下单参数、成本明细与 5 分钟免焊组装指南
```

---

## 🖥️ 在线预览 UI 与交互（无需硬件即可体验）

你可以直接在浏览器中打开 [`ui_preview/index.html`](ui_preview/index.html)，实时体验 `128×32` 冰蓝点阵 OLED 的开机动画、滚花旋钮切歌、14 段动态频谱以及蓝牙/SD 模式切换效果。

---

## 🛠️ 快速开始：如何在嘉立创一键制造？

详细图文步骤与省钱技巧请参阅 👉 **[《嘉立创一站式下单与免焊组装全流程指南》](docs/JLCPCB_ORDER_AND_ASSEMBLY_GUIDE.md)**。

1. **PCB + SMT 下单**：将 [`Gerber_JLCPCB_Persona3_MP3_4Layer.zip`](hardware/gerber_and_smt/Gerber_JLCPCB_Persona3_MP3_4Layer.zip)、[`BOM_JLCPCB_Persona3_MP3.csv`](hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv)、[`CPL_PickAndPlace_JLCPCB_Persona3_MP3.csv`](hardware/gerber_and_smt/CPL_PickAndPlace_JLCPCB_Persona3_MP3.csv) 上传至嘉立创，选择 `1.0mm` 板厚。
2. **外壳下单**：将 [`cad/stl/`](cad/stl/) 下的模型上传至嘉立创 CNC（铝合金 6061 喷砂阳极银）与嘉立创 3D 打印（8001 半透树脂 + 黑色高韧性树脂）。
3. **免焊组装**：插上 0.91 寸 OLED 的 14Pin FPC 软排线与 501240 电池的 JST-SH 1.0mm 插头，推入铝管锁紧 2 颗 M1.6 螺丝即告完成！

---

## 📜 开源协议 (License)

本项目采用 **MIT License** 开源，欢迎各位 S.E.E.S. 特别课外活动部成员自由复刻、改装与分享！
