# Persona 3 Reload (P3R) MP3 Player — 项目主状态与架构计划 (`plan.md`)

> 本文件作为长任务唯一真相源（Single Source of Truth），与代码、CAD 与 BOM 同步更新。

## 1. 当前硬件采购与复用状态 (Rev 2.4)
- **屏幕（已确认型号）**：优信电子 `2.25寸 TFT裸屏_8PIN插接`（ST7789P3, 76×284, `17.90 × 62.50 × 2.36 mm`，AA `14.80 × 55.30 mm`，顶边框 `1.61mm`，底COF边框 `5.595mm`，0.5mm 8Pin 21–23mm 排线背折接入 `J4 FPC-05F-8PH20 C2856797`）。
- **主控**：Waveshare `ESP32-S3-Zero` 无排针裸板版（`23.5 × 18.0mm`；⚠️ **务必拆除板载 `ME6217` 5脚 LDO 后再焊上主板！** 底部 `GP14` & `GP15` 各开 `Φ1.4mm` 镀铜过孔 / `Φ2.0mm` 焊盘，保 `0.54mm` 绿油阻焊桥）。
- **Hi-Fi 音频链**：`U2: PCM5102APWR (C107671)` + **`U5: TPA6132A2RTER (C69901, -6dB 增益 + R19/C26 100ms 软启动)`** + `J3: PJ-320D-SMT (C22459515)`（集成于主板 Top `-X` 侧翼 `Z=92.8..108.2mm, cx=-13.10, cy=+2.40`，距 `S3-Zero` 焊盘净空 `0.60..0.90mm`）。
- **电源与电量遥测**：`U3: TP4056 (C16581, R1=4.7k -> 255mA)` + `U4: AP2112K-3.3TRG1 (C51118, 600mA LDO -> 3V3_ALWAYS)` + `Q2: AO3401A 理想二极管 + R12=1k/C17=1uF 防拔线塌陷` + `Q3: AO3401A 外设总开关 (GP14)` + **`R21/R22 470kΩ (Basic C23178) + C27 100nF (C14663) -> GP15 (ADC2_CH4)`** 1:1 真实电池采样。
- **推荐电芯**：**`551255 3.7V 350–400mAh`**（`55×12×5.5mm`，含 +10% 鼓包 `6.05mm` 仍留 `+0.50mm` 净空；亦可兼容标称 `6.0mm` `601260`）。
- **结构外观**：`Φ24.0mm × 117.5mm`（含居中挂绳耳 `122.0mm`）1:1 比例圆柱形（深色帽 `25.0mm` : 银主体 `74.5mm` = `0.336`）、`+Y/-Y` 分瓣止口、`-X` 侧肩 3.5mm 耳机突起与上段让位槽、`R1.20mm` 圆角 `02` 扁平盖板、`01` 正交 4 面铝止口、背面 `R1.35mm` 圆角药丸按键 (`K1..K4`)、`06` 每侧 `0.60mm` 主板承托台肩。

## 2. 关键文件路径
- CAD 模型生成器（Rev 2.4）：[generate_cad_models.py](cad/scripts/generate_cad_models.py)
- BOM 生成脚本（Rev 2.4）：[generate_hardware_files.py](hardware/generate_hardware_files.py)
- 立创商城 SMT BOM（Rev 2.4, 22 项）：[BOM_JLCPCB_Persona3_MP3.csv](hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv)
- 立创 EDA 原理图网表、`-X` 侧翼单框拼版与下单指南：[REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md](docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)
- 固件主程序 & 引脚定义：[main.cpp](firmware/src/main.cpp) / [p3r_ui_assets.h](firmware/include/p3r_ui_assets.h)

## 3. Rev 2.3 → Rev 2.4 独立 Pre-Production Review 全面返修摘要
1. **5 Blocker 全部清零 (`B-01..B-05`)**：
   - `04` 深蓝帽盖彻底重构为单个闭合水密流形 (`Shells=1`, `0` 隔板/`Z` 向射线全通, `0` 多壳嵌套), 底部分瓣止口 (`+Y[42°..138°] & -Y[222°..318°]`) 让出 `±X` 通路令 `S3-Zero` 与 `J2 TF-01A` 零干涉插入；`-X` 内兜腔扩宽至 `X∈[-17.15,+2.00], Y∈[-1.75,+6.50], R1.05mm` 适配 `Φ2.0mm` CNC 铣刀且拐角全通；`04/05` M1.6 锁孔精准注入节点至 `1.360mm` 宽度。
2. **7 Major Risks 全部解决 (`M-01..M-07`)**：
   - `01` 消除 40,000:1 斜三角形、`01/02/03` 引入 `R0.55/R1.00/R1.20/R1.35/R1.50mm` CNC 圆角、`06` 增加 `0.60mm` 主板承托台肩、`04` 挂绳耳增高增厚至 `122.0mm (1.25mm 桥厚 / 4.0mm² 截面积)`、`J3` 移至 `cx=-13.10mm` 并把 `GP14/GP15` 过孔收细至 `Φ1.4mm / 盘 Φ2.0mm`（保 `0.54mm` 阻焊桥）、`R21/R22`+固件 `GP15 ADC2_CH4` 实现动态电量条及低电保护、`firmware/*` & `ui_preview/index.html` 注释版本与实装完全对齐。
3. **可制造性权衡 (`O-01..O-03`)**：证实不可将 `01` 改用单一 `Φ21.40mm` 纯圆车孔（会切穿 `Y=+8.00mm` 毁坏上下铝台肩），保留内平肩方案并文档化 CNC 工艺；采纳单框两板内铣槽＋邮票孔拼版 (`O-03`)。

## 4. 当前进度清单
- [x] Rev 2.4 全部 7 个 STL (`00..06`) 重新生成并经过拓扑、Z-ray、M1.6、06台肩与 25 项角包络碰撞全检 **PASS**。
- [x] `generate_hardware_files.py` (22项 BOM, `\n` 行尾)、`REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md`、`README.md`、`ui_preview/index.html` 同步至 Rev 2.4。
- [x] 固件 `firmware/src/main.cpp`（`GP15 VBAT ADC` + 版本对齐）经 PlatformIO 编译通过 (`0 error, 0 warning`)。
- [x] 已完成双独立 Agent Pre-Production Review 并按最终细化建议闭环（含 `GP14/GP15` `Φ2.0mm` 盘与 `S3-Zero` 阶梯包络校验）。
