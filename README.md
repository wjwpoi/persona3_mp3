# 🎧 Persona 3 Reload (P3R) 主角 MP3 随身听 1:1 复刻开源工程 (Rev 2.2)

[![License: MIT](https://img.shields.io/badge/License-MIT-00e5ff.svg)](LICENSE)
[![Revision: Rev 2.2 Audited](https://img.shields.io/badge/Hardware%20%26%20CAD-Rev%202.2%20Verified-10b981.svg)](plan.md)
[![Manufacturing: JLCPCB Economic SMT + CNC](https://img.shields.io/badge/Manufacturing-嘉立创单面经济型SMT%20%2B%20CNC-1e90ff.svg)](docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)

> **"MEMENTO MORI // FULL MOON FULL LIFE"**
> 本项目严格按 **P3R 官方片头长条比例（`Φ24.0mm × 123.0mm`，含挂绳耳 `127.0mm`）** 复刻结城理胸前标志性的深蓝顶帽＋银色圆柱 MP3 随身听，搭配 **2.25 寸 `76×284` 竖条 IPS LCD (`ST7789P3`)** 与 **Sony NW-S200 风格 Hi-Fi 无损解码耳放链路**。
> **Rev 2.2 已通过独立全量复审与 3D 截面防碰撞扫描（0 非流形 / 0 退化 / 全包络 0 碰撞）。**

---

## ✨ 核心架构 (Rev 2.2)

1. **1:1 官方长条比例圆柱外观（`Φ24.0mm × 123.0mm`）**
   - **CNC 6061 喷砂银主体筒 (`01`)**：正交平面视窗 (`15.00 × 56.50mm`) ＋ 4 边 `1.08mm` 实心铝台肩兜槽＋背面 4 颗独立弹性槽药丸按键 (`03`)＋隐藏式 `M1.6` 同轴锁孔 (`Z=20.0 / 90.5mm`)。
   - **深蓝阳极氧化顶帽 (`04`) ＋ 银色半椭球底盖 (`05`)**：上下均配备 **`4.0mm` 真正柱形止口 (`OD=21.20 / ID=19.00mm`)** 及同轴 `M1.6` 锁孔。
   - **正交内托支架 (`06`)**：`1.00mm` 实心水平隔离桥隔开背面 `6.0mm` 按键子板与 `551255`（兼容 `601260`）锂电仓。
2. **Hi-Fi 音频链与超低待机双级电源树**
   - **主控**：Waveshare `ESP32-S3-Zero`（拆板载 `ME6217`，原生 USB MSC U 盘免拆卡传歌 + `2.8mm GP14` 助焊孔）。
   - **DAC ＋ 直推耳放**：`PCM5102APWR (C107671)` + **`TPA6132A2RTER (C69901, -6dB 增益 + 100ms 软启动消爆音)`** + `PJ-320D-SMT`（置于 `1.0mm` 台阶音频子板，与顶盖 `Φ8.4mm` 耳机孔同心并完全避让 Type-C 插头）。
   - **电源**：`TP4056 (255mA)` + `Q2 AO3401A` 理想二极管 + `AP2112K-3.3` + `Q3 (GP14)` 外设总断电＋外部 `10k` 按键上拉（深睡可由 `K1 RTC_GPIO1` 稳定唤醒）。
3. **2.25 寸 `ST7789P3` (`76×284`) P3R 片头主题 UI**
   - `60fps` 纵滚切换、`HELLO!` 渐入、双主题（动画灰冷屏 / 官方蓝屏）、动态频谱与 2 步确认安全退出 U 盘模式。

---

## 📂 仓库目录结构 (Repository Layout)

```text
persona3_mp3/
├── cad/
│   ├── scripts/
│   │   └── generate_cad_models.py              # Rev 2.2 参数化正交 CAD/STL 生成脚本
│   └── stl/                                    # 嘉立创 CNC / 3D 打印下单用闭合流形 STL
│       ├── 00_full_assembled_p3r_mp3.stl       # 整机总装预览模型
│       ├── 01_cnc_main_shell_6061_silver.stl   # [CNC 6061银] 主机身筒
│       ├── 02_flat_screen_lens_clear.stl       # [高透亚克力/玻璃] 15.44x58.14x0.80mm 盖板
│       ├── 03_rear_pill_button_strip_silver.stl# [CNC/光固化银] 4颗背面弹性药丸按键条
│       ├── 04_top_navy_collar_lanyard_cap.stl  # [CNC深蓝/树脂] 顶帽+挂绳耳 (Z=92.5..123mm)
│       ├── 05_bottom_rounded_dome_cap_silver.stl # [CNC 6061银] 底部子弹头半球封盖
│       └── 06_internal_zero_solder_sled.stl    # [高韧性树脂] 正交内托+刚性按键隔离桥
├── hardware/
│   ├── generate_hardware_files.py              # Rev 2.2 BOM 生成脚本 (共21项立创基础/常用件)
│   └── gerber_and_smt/
│       └── BOM_JLCPCB_Persona3_MP3.csv         # 权威立创商城 PCBA SMT BOM
├── firmware/
│   ├── platformio.ini                          # ESP32-S3-Zero (qio_qspi, PSRAM, TinyUSB MSC)
│   ├── include/
│   │   └── p3r_ui_assets.h                     # P3R UI 资源、字模与歌单元信息
│   └── src/
│       └── main.cpp                            # 主程序（深睡 RTC 锁定 / 音频 / 显示 / USB MSC）
├── docs/
│   └── REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md   # 立创EDA原理图网表、台阶子板布局与装配顺序
├── ui_preview/
│   └── index.html                              # 浏览器端 UI 交互仿真器
└── plan.md                                     # 项目主状态与工程变更跟踪
```

---

## 🛠️ 制造与开发入口

- **原理图、PCB 画板与装配指南**：请严格按 **[`docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md`](docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)** 在立创 EDA 完成布板并 `DRC 零报错` 后导出 Gerber / CPL，切勿跳过指南中的「`S3-Zero` 先焊 → `GP14` 测通断 → 最后焊 `J2 (TF-01A)`」装配顺序。
- **固件编译**：在 `firmware/` 目录执行 `pio run`（基于 PlatformIO `espressif32 @ 6.9.0`）。
- **外壳加工**：直接上传 [`cad/stl/`](cad/stl/) 中的 6 个分件模型下单。

---

## 📜 开源协议 (License)

本项目采用 **MIT License** 开源，欢迎各位 S.E.E.S. 成员自由复刻与改进。
