# Persona 3 Reload (P3R) MP3 Player — 项目主状态与架构计划 (`plan.md`)

> 本文件作为长任务唯一真相源（Single Source of Truth），与代码、CAD 与 BOM 同步更新。

## 1. 当前硬件采购与复用状态 (Rev 2.5)
- **屏幕（已确认型号）**：优信电子 `2.25寸 TFT裸屏_8PIN插接`（ST7789P3, 76×284, `17.90 × 62.50 × 2.36 mm`，AA `14.80 × 55.30 mm`，顶边框 `1.61mm`，底COF边框 `5.595mm`，0.5mm 8Pin 21–23mm 排线背折接入 `J4 FPC-05F-8PH20 C2856797`）。
- **主控**：Waveshare `ESP32-S3-Zero` / `-M`（`23.5 × 18.0mm`；主板布 `2×9P Φ1.0mm` 通孔兼容已购 `-M` 不拆排针直插底面剪平；⚠️ **去掉板载 `ME6217` 5脚 LDO 后再焊上主板！** 底部 `GP14` & `GP15` 各开 `Φ1.4mm` 过孔 / `Φ2.0mm` 焊盘，保 `0.54mm` 阻焊桥，`-M` 先预焊 `1.5cm` 短丝再穿孔）。
- **Hi-Fi 音频链**：`U2: PCM5102APWR (C107671)` + **`U5: TPA6132A2RTER (C69901, -6dB 增益 + R19/C26 100ms 软启动)`** + `J3: PJ-320D-SMT (C22459515)`（集成于主板 Top `-X` 侧翼 `Z=92.8..108.2mm, cx=-13.10, cy=+2.40`，距 `S3-Zero` 焊盘净空 `0.60..0.90mm`）。
- **电源与电量遥测**：`U3: TP4056 (C16581, R1=4.7k -> 255mA, LED1 近 USB-C Top Z=93..106mm)` + `U4: AP2112K-3.3TRG1 (C51118, 600mA LDO -> 3V3_ALWAYS)` + `Q2: AO3401A 理想二极管 + R12=1k/C17=1uF 防拔线塌陷` + `Q3: AO3401A 外设总开关 (GP14)` + **`R21/R22 100kΩ (Basic C25803) + C27 100nF (C14663) -> GP15 (ADC2_CH4)`** 1:1 真实电池采样（`50kΩ` 等效采样源阻 + `~20uA` 分压电流）。
- **推荐电芯**：**`551255 3.7V 350–400mAh`**（`55×12×5.5mm`，含 +10% 鼓包 `6.05mm` 仍留 `+0.50mm` 净空；亦可兼容标称 `6.0mm` `601260`）。
- **结构外观**：`Φ24.0mm × 117.5mm`（含居中挂绳耳 `122.0mm`）1:1 比例圆柱形（深色帽 `25.0mm` : 银主体 `74.5mm` = `0.336`）、`+Y/-Y` 分瓣止口、`-X` 侧肩 3.5mm 耳机突起与上段让位槽、`R1.20mm` 圆角 `02` 扁平盖板、`01` 视窗兜槽 `15.72×58.44mm` (`+0.14mm`/边适配阳极氧化)、`04/05` M1.6 紧咬孔 `1.280mm`、背面 `R1.35mm` 圆角药丸按键 (`K1..K4`)、`06` 每侧 `0.60mm` 主板承托台肩。

## 2. 关键文件路径
- CAD 模型生成器（Rev 2.5）：[generate_cad_models.py](cad/scripts/generate_cad_models.py)
- BOM 生成脚本（Rev 2.5）：[generate_hardware_files.py](hardware/generate_hardware_files.py)
- 立创商城 SMT BOM（Rev 2.5, 22 项）：[BOM_JLCPCB_Persona3_MP3.csv](hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv)
- 立创 EDA 原理图网表、`-X` 侧翼单框拼版与下单指南：[REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md](docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)
- 固件主程序 & 引脚定义：[main.cpp](firmware/src/main.cpp) / [p3r_ui_assets.h](firmware/include/p3r_ui_assets.h)

## 3. Rev 2.3 → Rev 2.5 独立评审与可制造性打磨摘要
1. **5 Blocker 全部清零 (`B-01..B-05`)**：
   - `04` 深蓝帽盖彻底重构为单个闭合水密流形 (`Shells=1`, `0` 隔板/`Z` 向射线全通, `0` 多壳嵌套), 底部分瓣止口 (`+Y[42°..138°] & -Y[222°..318°]`) 让出 `±X` 通路令 `S3-Zero` 与 `J2 TF-01A` 零干涉插入；`-X` 内兜腔扩宽至 `X∈[-17.15,+2.00], Y∈[-1.75,+6.50], R1.05mm` 适配 `Φ2.0mm` CNC 铣刀且拐角全通；`04/05` M1.6 锁孔注点优化至 `1.280mm`（自攻牙满咬合）。
2. **7 Major Risks + Rev 2.5 实用化微调**：
   - `01` 消除斜三角形、扩宽视窗兜槽至 `15.72×58.44mm`（`+0.14mm` 单边余量兼容阳极氧化膜）、`01/02/03` CNC 圆角、`06` `0.60mm` 主板承托台肩、`04` `122.0mm` 居中挂绳耳、`LED1` 移近 USB-C (`Z=93..106mm`)、`R21/R22 100kΩ C25803` 提升 SAR 采样精度。
   - 固件 `2.5.0-REV25-POLISHED` 新增 `-DCORE_DEBUG_LEVEL=0`、NVS (`Preferences`) 参数断点记忆（音量/EQ/主题/随机/曲目）、`audio.getAudioCurrentTime()` 真实时长同步、`3.18V` 迟滞关机阈值与按需状态驱动 SPI 刷新。
3. **可制造性权衡 (`O-01..O-03`)**：证实不可将 `01` 改用单一 `Φ21.40mm` 纯圆车孔（会切穿 `Y=+8.00mm` 毁坏上下铝台肩），保留内平肩方案并文档化 CNC 工艺；采纳单框两板内铣槽＋邮票孔拼版 (`O-03`)，兼容 `ESP32-S3-Zero-M` 不拆排针直插。

## 4. 当前进度清单
- [x] Rev 2.5 全部 7 个 STL (`00..06`) 重新生成并经过拓扑、Z-ray、M1.6 (`1.280mm`)、06台肩与角包络碰撞全检 **PASS**。
- [x] `generate_hardware_files.py` (22项 BOM, `\n` 行尾, `R21/R22 100kΩ C25803`)、`REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md`、`README.md`、`ui_preview/index.html` 同步至 Rev 2.5。
- [x] 固件 `firmware/src/main.cpp`（NVS 记忆 / `getAudioCurrentTime` / 按需刷屏 / `3180mV` / `CORE_DEBUG_LEVEL=0`）经 PlatformIO 编译通过 (`0 error, 0 warning`)。
- [x] 已完成双独立 Agent Pre-Production Review 与 Adversarial Practical Review 全部闭环落实。
