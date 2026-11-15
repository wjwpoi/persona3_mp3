# 🎧 Persona 3 Reload (P3R) 主角 MP3 随身听 1:1 复刻开源工程 (Rev 2.3)

[![License: MIT](https://img.shields.io/badge/License-MIT-00e5ff.svg)](LICENSE)
[![Revision: Rev 2.3 Verified](https://img.shields.io/badge/Hardware%20%26%20CAD-Rev%202.3%20Verified-10b981.svg)](plan.md)
[![Manufacturing: JLCPCB Economic SMT + CNC](https://img.shields.io/badge/Manufacturing-嘉立创单面经济型SMT%20%2B%20CNC-1e90ff.svg)](docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)

> **"MEMENTO MORI // FULL MOON FULL LIFE"**
> 本项目严格按 **P3R 官方片头与剧场版 1:1 比例（`Φ24.0mm × 117.5mm` 主筒，含居中挂绳耳 `121.5mm`；深色帽/银筒比 `25.0 / 74.5 = 0.336`，精准还原 `0.327..0.350` 官模比例）** 复刻结城理胸前标志性的深色顶帽（带 **`-X` 侧肩 3.5mm 耳机台阶突起** ＋ 银色主体筒）MP3 随身听，搭配 **2.25 寸 `76×284` 竖条 IPS LCD (`ST7789P3`)** 与 **Sony NW-S200 风格 Hi-Fi 无损解码耳放链路**。
> **Rev 2.3 已通过 3D 流形与全包络防碰撞检查（0 非流形 / 0 退化 / 全包络 0 碰撞）。**

---

## ✨ 核心架构 (Rev 2.3)

1. **1:1 官方外观比例与 `-X` 侧肩耳机台阶（`Φ24.0mm × 117.5mm`）**
   - **深色阳极氧化/树脂顶帽 (`04`)**：配备 `-X` 侧边台阶凸耳（`Z=92.5..109.4mm`，内藏真实可用 `PJ-320D-SMT` 耳机插座，实心壁厚 `>=1.70mm`）、顶阶 **`Φ7.40mm` 轴向耳机孔**、上段 **`Φ8.70mm` 弧形让位槽**（容纳 `Φ8.3mm` 耳机插头胶壳并保留 `>=1.65mm` 背壁）及**顶端正中挂绳耳 (`Z=117.5..121.5mm`)**；底部带 **`4.0mm` 真正柱形止口 (`OD=21.20 / ID=19.00mm`)** 与隐蔽 `M1.6` 同轴锁孔。
   - **CNC 6061 喷砂银/香槟钛银主体筒 (`01`) ＋ 半椭球底盖 (`05`)**：正交平面视窗 (`15.00 × 56.50mm`) ＋ 4 边 `1.08mm` 实心铝台肩兜槽＋背面 4 颗独立弹性槽药丸按键 (`03`)＋隐藏式 `M1.6` 同轴锁孔 (`Z=20.0 / 90.5mm`)。
   - **正交内托支架 (`06`)**：`1.00mm` 实心水平隔离桥隔开背面 `6.0mm` 按键子板与 `551255`（兼容 `601260`）锂电仓。
2. **Hi-Fi 音频链与降复杂度单主板集成**
   - **主控**：Waveshare `ESP32-S3-Zero`（拆板载 `ME6217`，原生 USB MSC U 盘免拆卡传歌 + `2.8mm GP14` 助焊孔）。
   - **DAC ＋ 直推耳放**：`PCM5102APWR (C107671)` + **`TPA6132A2RTER (C69901, -6dB 增益 + 100ms 软启动消爆音)`** + **`PJ-320D-SMT (C22459515)` 直接集成于主板 Top `-X` 侧翼 (`Z=94.0..108.2mm`)**，彻底省去旧版独立台阶音频子板，拼版板数从 3 块简化为 **2 块**，免去半孔叠焊飞线。
   - **电源**：`TP4056 (255mA)` + `Q2 AO3401A` 理想二极管 + `AP2112K-3.3` + `Q3 (GP14)` 外设总断电＋外部 `10k` 按键上拉（深睡可由 `K1 RTC_GPIO1` 稳定唤醒）。
3. **2.25 寸 `ST7789P3` (`76×284`) P3R 片头主题 UI**
   - `60fps` 纵滚切换、`HELLO!` 渐入、双主题（动画灰冷屏 / 官方蓝屏）、动态频谱与 2 步确认安全退出 U 盘模式。

---

## 📂 仓库目录结构 (Repository Layout)

```text
persona3_mp3/
├── cad/
│   ├── scripts/
│   │   └── generate_cad_models.py              # Rev 2.3 参数化正交 CAD/STL 生成脚本
│   └── stl/                                    # 嘉立创 CNC / 3D 打印下单用闭合流形 STL
│       ├── 00_full_assembled_p3r_mp3.stl       # 整机总装预览模型
│       ├── 01_cnc_main_shell_6061_silver.stl   # [CNC 6061银] 主机身筒
│       ├── 02_flat_screen_lens_clear.stl       # [高透亚克力/玻璃] 15.44x58.14x0.80mm 盖板
│       ├── 03_rear_pill_button_strip_silver.stl# [CNC/光固化银] 4颗背面弹性药丸按键条
│       ├── 04_top_navy_collar_lanyard_cap.stl  # [CNC深蓝/深枪灰] -X 耳机侧肩+居中挂绳顶帽 (Z=92.5..121.5mm)
│       ├── 05_bottom_rounded_dome_cap_silver.stl # [CNC 6061银] 底部子弹头半球封盖
│       └── 06_internal_zero_solder_sled.stl    # [高韧性树脂] 正交内托+刚性按键隔离桥
├── hardware/
│   ├── generate_hardware_files.py              # Rev 2.3 BOM 生成脚本 (共21项立创基础/常用件)
│   └── gerber_and_smt/
│       └── BOM_JLCPCB_Persona3_MP3.csv         # 权威立创商城 PCBA SMT BOM
├── firmware/
│   ├── platformio.ini                          # ESP32-S3-Zero (qio_qspi, PSRAM, TinyUSB MSC)
│   ├── include/
│   │   └── p3r_ui_assets.h                     # P3R UI 资源、字模与歌单元信息
│   └── src/
│       └── main.cpp                            # 主程序（深睡 RTC 锁定 / 音频 / 显示 / USB MSC）
├── docs/
│   └── REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md   # 立创EDA原理图网表、-X 侧翼单板布局与装配顺序
├── ui_preview/
│   └── index.html                              # 浏览器端 UI 交互仿真器
└── plan.md                                     # 项目主状态与工程变更跟踪
```

---

## 🛠️ 制造与开发入口

- **原理图、PCB 画板与装配指南**：请严格按 **[`docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md`](docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)** 在立创 EDA 完成两板拼版布线并 `DRC 零报错` 后导出 Gerber / CPL，严格遵循「`S3-Zero` 先焊 → `GP14` 测通断 → 贴高温胶带 → 最后焊 `J2 (TF-01A)`」装配顺序。
- **固件编译**：在 `firmware/` 目录执行 `pio run`（基于 PlatformIO `espressif32 @ 6.9.0`）。
- **外壳加工**：直接上传 [`cad/stl/`](cad/stl/) 中的 6 个分件模型下单；若参照剧场版配色，可将 `01/05` 选暖香槟钛银磨砂阳极氧化、`04` 选深枪灰或深海蓝，配黑色细绳扣＋天青色织带颈绳。

---

## 📜 开源协议 (License)

本项目采用 **MIT License** 开源，欢迎各位 S.E.E.S. 成员自由复刻与改进。
