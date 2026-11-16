# 🎧 Persona 3 Reload (P3R) 主角 MP3 随身听 1:1 复刻开源工程 (Rev 2.6)

[![License: MIT](https://img.shields.io/badge/License-MIT-00e5ff.svg)](LICENSE)
[![Revision: Rev 2.6 Verified](https://img.shields.io/badge/Hardware%20%26%20CAD-Rev%202.6%20Verified-10b981.svg)](plan.md)
[![Manufacturing: JLCPCB Economic SMT + CNC](https://img.shields.io/badge/Manufacturing-嘉立创单面经济型SMT%20%2B%20CNC-1e90ff.svg)](docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)

> **"MEMENTO MORI // FULL MOON FULL LIFE"**
> 本项目严格按 **P3R 官方片头与剧场版 1:1 比例（`Φ24.0mm × 117.5mm` 主筒，含加固居中挂绳耳 `122.0mm`；深色帽/银筒比 `25.0 / 74.5 = 0.336`，精准还原 `0.327..0.350` 官模比例）** 复刻结城理胸前标志性的深色顶帽（带 **`-X` 侧肩 3.5mm 耳机台阶突起** ＋ 银色主体筒）MP3 随身听，搭配 **2.25 寸 `76×284` 竖条 IPS LCD (`ST7789P3`)** 与 **Sony NW-S200 风格 Hi-Fi 无损解码耳放链路**。
> **Rev 2.6 已完成多轮零信任 Pre-Production & Practical 审计闭环：真圆 `Φ1.280mm` `M1.6` 螺孔、宽容度 `15.80×58.52mm` 视窗兜槽、`R1.30mm` `04` 内角、`5mm` SMT 拼版工艺边指引、`connecttoFS()` 坏文件跳曲保护与版本锁库。**

---

## ✨ 核心架构 (Rev 2.6)

1. **1:1 官方外观比例与 `-X` 侧肩耳机台阶（`Φ24.0mm × 117.5mm`）**
   - **深色阳极氧化/树脂顶帽 (`04`)**：单个水密闭合流形 (`Shells=1`)，配备 `-X` 侧边台阶凸耳（`Z=92.5..109.4mm`，内藏真实可用 `PJ-320D-SMT` 耳机插座，实心壁厚 `>=1.65mm`，内部 **`R1.30mm` 圆角兜腔适配 `Φ2.5mm` CNC 铣刀**）；顶阶通透 **`Φ7.40mm` 轴向耳机孔 (`cx=-13.10, cy=+2.40`)** ＋ 上段 **`Φ8.70mm` 弧形让位槽**及**加厚居中挂绳耳 (`Z=117.5..122.0mm`, `1.25mm` 桥厚)**；底部采用 **`+Y/-Y` 分瓣式 `4.0mm` 柱形止口 (`OD=21.20 / ID=19.00mm`)**，留空 `±X` 彻底避让真实 `1.6mm` `S3-Zero(-M)` 与 `J2` MicroSD 卡槽并配 **真圆 `Φ1.280mm` `M1.6` 锁孔**。
   - **CNC 6061 喷砂银/香槟钛银主体筒 (`01`) ＋ 半椭球底盖 (`05`)**：`R0.55mm` 圆角视窗 (`15.00 × 56.50mm`) ＋ **`R1.00mm` 铝台肩兜槽 (`15.80 × 58.52mm` 外口 / `15.76 × 58.48mm` 底槽，单边 `+0.16mm` 适配阳极氧化与切边公差)** ＋ 背面 `R1.50mm` 圆角槽配 `R1.35mm` 药丸按键 (`03`) ＋ **真圆 `Φ1.280mm` `M1.6` 锁孔 (`Z=20.0 / 90.5mm`，CNC 铝须机攻 `M1.6×0.35` 机丝)**。
   - **正交内托支架 (`06`)**：每侧增设 **`0.60mm` 水平承托台肩 (`|X|=8.20mm`)** 托住主板防止电芯下压形变，`1.00mm` 实心隔离桥隔开背面 `6.0mm` 按键子板与 `551255`（兼容 `601260`）锂电仓。
2. **Hi-Fi 音频链、电池电量监测与单框两板集成**
   - **主控**：Waveshare `ESP32-S3-Zero` / `ESP32-S3-Zero-M` 两版通吃（主板设 `2×9P Φ1.0mm` 通孔兼容 `-M` 不拆排针直插、底面剪平磨平配双层 `0.08mm` Kapton；水口钳剪断 `ME6217` 第 5 脚后原生 USB MSC 传歌 + `Φ1.4mm / Φ2.0mm` `GP14` & `GP15` 过孔，保 `0.54mm` 阻焊桥）。
   - **DAC ＋ 直推耳放 ＋ 电量检测**：`PCM5102APWR (C107671)` + **`TPA6132A2RTER (C69901, -6dB 增益 + 100ms 软启动消爆音)`** + **`PJ-320D-SMT (C22459515, cx=-13.10, cy=+2.40)` 直接集成于主板 Top `-X` 侧翼 (`Z=92.8..108.2mm`)**，与 `6×32mm` 按键子板采用 **内铣槽＋邮票孔＋`5mm` 工艺边单框两板拼版**；`R21/R22 100kΩ (Basic C25803)` + `C27 100nF (C14663)` 至 `GP15 (ADC2_CH4)` 实现精准低噪电池电压采样，`LED1` 置主板 Top 近 USB-C 口 (`Z=93..106mm`) 拔帽充电即见。
   - **电源**：`TP4056 (255mA)` + `Q2 AO3401A` 理想二极管 + `AP2112K-3.3` + `Q3 (GP14)` 外设总断电＋外部 `10k` 按键上拉（深睡可由 `K1 RTC_GPIO1` 稳定唤醒）。
3. **2.25 寸 `ST7789P3` (`76×284`) P3R 片头主题 UI**
   - `60fps` 纵滚切换、`HELLO!` 渐入、双主题（动画灰冷屏 / 官方蓝屏）、动态频谱、**按需状态驱动 SPI 刷新（暂停静止时停刷省电）**、**NVS (`Preferences`) 掉电记忆音量/EQ/主题/随机/曲目**、**真实解码时间轴 (`getAudioCurrentTime()`)**、**`connecttoFS()` 坏文件自动跳过与全盘异常 `SD READ ERR` 保护**、**`<3.18V` 迟滞防误关机保护**与 `-DCORE_DEBUG_LEVEL=0`、2 步确认安全退出 U 盘模式。

---

## 📂 仓库目录结构 (Repository Layout)

```text
persona3_mp3/
├── cad/
│   ├── scripts/
│   │   └── generate_cad_models.py              # Rev 2.6 参数化正交 CAD/STL 生成脚本
│   └── stl/                                    # 嘉立创 CNC / 3D 打印下单用闭合流形 STL
│       ├── 00_full_assembled_p3r_mp3.stl       # 整机总装预览模型
│       ├── 01_cnc_main_shell_6061_silver.stl   # [CNC 6061银] 主机身筒 (R0.55视窗/15.80x58.52兜槽/0斜条)
│       ├── 02_flat_screen_lens_clear.stl       # [高透亚克力/玻璃] 15.44x58.14x0.80mm (R1.20圆角)
│       ├── 03_rear_pill_button_strip_silver.stl# [CNC/光固化银] 4颗圆角药丸按键条 (R1.35)
│       ├── 04_top_navy_collar_lanyard_cap.stl  # [CNC深蓝/深枪灰] 分瓣止口+R1.30兜腔+Φ1.28圆孔 (Z=92.5..122.0mm)
│       ├── 05_bottom_rounded_dome_cap_silver.stl # [CNC 6061银] 底部子弹头半球封盖 (Φ1.280mm真圆M1.6孔)
│       └── 06_internal_zero_solder_sled.stl    # [高韧性树脂] 正交内托+0.60mm主板台肩+刚性按键桥
├── hardware/
│   ├── generate_hardware_files.py              # Rev 2.6 BOM 生成脚本 (共22项立创基础/常用件)
│   └── gerber_and_smt/
│       └── BOM_JLCPCB_Persona3_MP3.csv         # 权威立创商城 PCBA SMT BOM
├── firmware/
│   ├── platformio.ini                          # ESP32-S3-Zero (2.6.0-REV26-RC, 锁库 1.3.0 / 2.3.0, DEBUG=0)
│   ├── include/
│   │   └── p3r_ui_assets.h                     # P3R UI 资源、字模、Rev 2.6 引脚定义与歌单元信息
│   └── src/
│       └── main.cpp                            # 主程序（NVS记忆 / 解码计时 / 坏文件保护 / 按需SPI / 3.18V保护）
├── docs/
│   └── REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md   # 立创EDA原理图网表、-X 侧翼单框拼版与装配顺序
├── ui_preview/
│   └── index.html                              # 浏览器端 UI 交互仿真器
└── plan.md                                     # 项目主状态与工程变更跟踪
```

---

## 🛠️ 制造与开发入口

- **原理图、PCB 画板与装配指南**：请严格按 **[`docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md`](docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)** 在立创 EDA 完成单框两板拼版布线并 `DRC 零报错` 后导出 Gerber / CPL，严格遵循「`S3-Zero` 先焊 → 测通 `GP14/GP15` → 贴高温胶带 → 最后焊 `J2 (TF-01A)`」装配顺序。
- **固件编译**：在 `firmware/` 目录执行 `pio run`（基于 PlatformIO `espressif32 @ 6.9.0`）。
- **外壳加工**：直接上传 [`cad/stl/`](cad/stl/) 中的 6 个分件模型下单；若参照剧场版配色，可将 `01/05` 选暖香槟钛银磨砂阳极氧化、`04` 选深枪灰或深海蓝，配黑色细绳扣＋天青色织带颈绳。

---

## 📜 开源协议 (License)

本项目采用 **MIT License** 开源，欢迎各位 S.E.E.S. 成员自由复刻与改进。
