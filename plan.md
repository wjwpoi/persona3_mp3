# Persona 3 Reload (P3R) MP3 Player — 项目主状态与架构计划 (`plan.md`)

> 本文件作为长任务唯一真相源（Single Source of Truth），与代码、CAD 与 BOM 同步更新。

## 1. 当前硬件采购与复用状态 (Rev 2.7)
- **屏幕（已确认型号）**：优信电子 `2.25寸 TFT裸屏_8PIN插接`（ST7789P3, 76×284, `17.90 × 62.50 × 2.36 mm`，AA `14.80 × 55.30 mm`，顶边框 `1.61mm`，底COF边框 `5.595mm`，0.5mm 8Pin 21–23mm 排线背折接入 `J4 FPC-05F-8PH20 C2856797`）。
- **主控**：Waveshare `ESP32-S3-Zero` / `-M`（`23.5 × 18.0 × 1.6mm`，USB-C 悬伸至 `Z≈109.5mm`；主板布 `2×9P Φ0.95–1.0mm` / `Φ1.40mm` 偏内焊盘兼容已购 `-M` 不拆排针直插，双排底面剪平磨平＋全覆双层 `0.08mm` Kapton，与 `14.50mm` `J2` `[-6.20,+8.30]` 固定焊盘错开防重叠；⚠️ **上板前齐根剪断 `ME6217` 第 5 脚 `VOUT` 并测通断！** 底部 `GP14` & `GP15` 各开 `Φ1.4mm / Φ2.0mm` 过孔，`-M` 先预焊 `1.5cm` 短丝再穿孔）。
- **Hi-Fi 音频链**：`U2: PCM5102APWR (C107671)` + **`U5: HT4832 (C130779, -6dB 增益 Pin-to-Pin 替代 TPA6132A2, Rotation=270 + R19/C26 100ms 软启动)`** + `J3: PJ-320D-SMT (C22459515, 集成于主板 Top -X 侧翼 Z=92.8..108.2mm, 已从 SMT BOM 剔除改手焊免 ¥30 费)`。
- **电源与电量遥测**：`U3: TP4056 (C16581, R1=4.7k -> 255mA, LED1 0603 置 -X 翼 J3 下方)` + `U4: AP2112K-3.3TRG1 (C51118, 600mA LDO -> 3V3_ALWAYS)` + `Q2: AO3401A 理想二极管 + R12=1k/C17=1uF 防拔线塌陷` + `Q3: AO3401A 外设总开关 (GP14)` + **`R21/R22 100kΩ (Basic C25803) + C27 100nF (C14663) -> GP15 (ADC2_CH4)`** + `C9/C10 切换 Basic 库 2.2nF (C1604)`。
- **推荐电芯**：**`551255 3.7V 350–400mAh`**（`55×12×5.5mm`，含 +10% 鼓包 `6.05mm` 仍留 `+0.50mm` 净空；亦可兼容标称 `6.0mm` `601260`）。
- **结构外观**：`Φ24.0mm × 117.5mm`（含居中挂绳耳 `122.0mm`）1:1 比例圆柱形（深色帽 `25.0mm` : 银主体 `74.5mm` = `0.336`）、`+Y/-Y` 分瓣止口、`-X` 侧肩兜腔 `R1.30mm`（`Φ2.5mm` 铣刀）与上段让位槽、`R1.20mm` 圆角 `02` 扁平盖板、`01` 兜槽 `15.80×58.52mm`（底槽 `15.76×58.48mm`, `+0.16mm`/边）、`04/05` **真圆 `Φ1.280mm` `M1.6` 孔**（配 `M1.6×2` 短机丝）、背面解析级光滑药丸按键 **`03` (`3.06×3.52mm R1.20mm` 倒角至 `R12.60mm`, 狗骨式上下限位耳 `4.30×4.90mm`, 最薄处 `>=0.5278mm`, 并额外输出 2 套 8 颗双排连筋版 `03_rear_pill_button_2sets_runner_silver.stl`)**、`06` `0.60mm` 承托台肩（`Z>84.5mm` 全退至 `Y<=-2.05mm`）。

## 2. 关键文件路径（Rev 2.7）
- CAD 模型生成器（Rev 2.7）：[generate_cad_models.py](cad/scripts/generate_cad_models.py)
- BOM 生成脚本（Rev 2.7）：[generate_hardware_files.py](hardware/generate_hardware_files.py)
- 立创商城基础 BOM（Rev 2.7, 22 项）：[BOM_JLCPCB_Persona3_MP3.csv](hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv)
- Rev 2.7 正式制板 & Top 经济型 SMT 制造包（`0` DRC）：
  - Gerber + 钻孔压缩包：[Gerber_Persona3_MP3_Rev27.zip](hardware/rev27_fab/Gerber_Persona3_MP3_Rev27.zip)（`150,349` B，2 层 `1.000mm`，`39.45 × 85.90 mm` 无 V-CUT 邮票孔拼板，PTH `0.2997×2 / 0.3002×183 / 0.8001×2 / 0.9500×18`；NPTH `0.5499×22 / 1.0000×2 / 1.4000×2 / 2.0000×4`）
  - Top-Only SMT BOM：[BOM_JLCPCB_TOP_SMT_Rev27.csv](hardware/rev27_fab/BOM_JLCPCB_TOP_SMT_Rev27.csv)（`1,902` B，20 行 / 63 颗，100% 含 LCSC 料号：剔除 `J3` 改手焊，`U5=C130779`，`C9/C10=C1604`，`LED1=0603`）
  - Top-Only SMT 坐标：[CPL_JLCPCB_TOP_SMT_Rev27.csv](hardware/rev27_fab/CPL_JLCPCB_TOP_SMT_Rev27.csv)（`10,932` B，63 颗 `Layer=T`，`U5 Rotation=270` 与 Pin 1 左上零偏移一致）
- CAD STL 交付件（全 8 件 `degen=0, bnd=0, nm=0, shells=1 (00为6)`）：
  - 单套及整机：[00..06 STL](cad/stl/)（其中 [03_rear_pill_button_strip_silver.stl](cad/stl/03_rear_pill_button_strip_silver.stl) 为 `1,604` 三角面 / `111.92 mm³`）
  - 2 套连筋排模打印件：[03_rear_pill_button_2sets_runner_silver.stl](cad/stl/03_rear_pill_button_2sets_runner_silver.stl)（`3,280` 三角面 / `237.21 mm³`，双列 `X=±4.20mm`，`Z=42/58 ± 0.65mm` 横连筋，列间距 `4.10mm` / Z 间距 `3.10mm`）
- 立创 EDA Pro 工程 UUID：`projUuid=ec1d50236e4c422090f2bd1c0903354a` / `schUuid=ea1f62d13efab3dd` / `pcbUuid=030c6ed78afbe5f5`
- 立创 EDA 原理图网表、`-X` 侧翼单框拼版与下单指南：[REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md](docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)
- 固件主程序 & 引脚定义：[main.cpp](firmware/src/main.cpp) / [p3r_ui_assets.h](firmware/include/p3r_ui_assets.h)

## 3. Rev 2.3 → Rev 2.7 独立评审与投产清障摘要
1. **5 Blocker 全部清零 (`B-01..B-05`)**：
   - `04` 单壳流形 (`Shells=1`, `0` 隔板/`Z` 向射线全通), `+Y/-Y` 分瓣止口避让 `±X` 实板 `1.6mm` `S3-Zero(-M)` 与 `14.50mm` `J2 TF-01A`；`04/05` 为 **16 边形真圆 `Φ1.280mm` 径向通孔**并规范 CNC 机攻 `M1.6×0.35`。
2. **Rev 2.5 → Rev 2.7 零信任审计闭环修正**：
   - `06` 内托在 `Z>84.5mm` 切净上沿至 `Y<=-2.05mm`（彻底避开 `±7.62mm` 焊点）、`docs` 补全 `J2/C14/R8/SW1..4` 全套网表并锁定 `K1@Z62..K4@Z38` 顺位、优化 `U1` 焊盘与 `14.50mm` `J2` 避让方案、修正 USB-C 悬伸与按键实体尺寸，并升级 [index.html](ui_preview/index.html) 至 `284×76` 全套 P3R UI。
   - 固件 `2.7.0-REV27-RELEASE` 锁定依赖库 (`1.3.0 / 2.3.0`)，修复**熄屏切歌锁死 (`isPageRolling = !isDisplaySleeping`)**，并加入 **全链路异常音频保护（`connecttoFS()` 失败、24-bit WAV/FLAC、截断 stub/`!audio.isRunning()` 与卡死检测顺序跳曲及 `SD READ ERR`）**、OTA 亮屏提示与 USB 模式防误触屏蔽。
3. **可制造性权衡 (`O-01..O-03`)**：证实 `01` 须采用「两端车孔 + T型槽刀内镗平肩 `Y=+6.924`」；采纳单框两板加 `5mm` 工艺边与 `>=3.85mm` 边距 Mark 点经济型 SMT 拼版 (`O-03`)。

## 4. 当前进度清单
- [x] Rev 2.7 全部 STL（`00..06` 及 `03_rear_pill_button_2sets_runner_silver.stl`）生成并通过拓扑（`degen=0, bnd=0, nm=0, shells=1 (00为6)`）、垂直厚度与装配间隙全检 **PASS**：`03` 重构为狗骨式上下限位耳 + 36 顶点解析光滑 `R1.20mm` 药丸头（最薄处 `0.5278mm >= 0.50mm`，`01` 槽口间隙 `0.2200mm`，`06` 槽侧隙 `>=0.6077mm` / 名义 `1.0500mm`，`0` 开关侵占，并输出 2 套连筋排模供水口钳/剪弦器分切）。
- [x] 立创 EDA Pro `Persona3_MP3_Rev27 | PCB1` 全板实盘布线、铺铜（185 过孔 / 4/4 实心铺铜 / 0 孤岛）、`1.000mm` 层叠、去 V-CUT 全 `2.00mm` CNC 锣槽 + `22` 孔 `Φ0.55mm` 邮票孔工艺边（`39.45 × 85.90 mm`）与丝印完成，API 复检 **`Final DRC Total = 0`**；Formal Top SMT 文件已定版更新（`20` 项 / `63` 颗：`J3` 改手焊、`U5=HT4832 C130779 Rotation=270`、`C9/C10=C1604`、`LED1=0603`）。
- [x] 嘉立创国内站 PCB + 经济型顶层 SMT 订单 **`Y8`**（5 片全贴，`3.95×8.59cm`, `1.0mm`）已完成 BOM/CPL 实盘匹配（`20/20` 全现货，`U5` 左上 Pin 1 零偏移，含 `¥50` 拼板费总计 `¥310.68`）并由用户下单；`Y6` 旧单号已由 `Y8` 取代。
- [x] 嘉立创三维猴 `jlc-3dp.cn/shoppingCart` 已将旧 `03` 替换为 2 套 8 颗光滑药丸连筋件 `03_rear_pill_button_2sets_runner_silver.stl`（`6061` 哑光本色，`0.27×1.27×2.89cm / 0.24cm³`，DFM 零告警，`¥40.00`）；全套 6 件总价维持 `168h ¥179.96` / `216h ¥172` 待用户确认下单。
- [ ] 待收尾项：确认三维猴 6 件下单；淘宝/自备散件补齐 `PJ-320D 贴片 4脚 3.5mm 耳机座`、`M1.6×2` 机丝、`0.08mm` Kapton、`30AWG` 硅胶线、`551255` 锂电与 `ESP32-S3-Zero(-M)`。
- [x] `generate_hardware_files.py` (22项 BOM, `\n` 行尾)、`REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md`、`README.md`、`ui_preview/index.html`、`plan.md` 同步至 Rev 2.7。
- [x] 固件 `firmware/src/main.cpp`（锁库 + 全异常音频保护 + 熄屏防锁 + OTA亮屏 + NVS + 按需刷新）经 PlatformIO 编译通过 (`0 error, 0 warning`)。
- [x] 已完成多轮独立 zero-trust 回归审计与所有 Major/Minor 闭环。
