# Persona 3 Reload (P3R) MP3 Player — 项目主状态与架构计划 (`plan.md`)

> 本文件作为长任务唯一真相源（Single Source of Truth），与代码、CAD 与 BOM 同步更新。

## 1. 当前硬件采购与复用状态 (Rev 2.7)
- **屏幕（已确认型号）**：优信电子 `2.25寸 TFT裸屏_8PIN插接`（ST7789P3, 76×284, `17.90 × 62.50 × 2.36 mm`，AA `14.80 × 55.30 mm`，顶边框 `1.61mm`，底COF边框 `5.595mm`，0.5mm 8Pin 21–23mm 排线背折接入 `J4 FPC-05F-8PH20 C2856797`）。
- **主控**：Waveshare `ESP32-S3-Zero` / `-M`（`23.5 × 18.0 × 1.6mm`，USB-C 悬伸至 `Z≈109.5mm`；主板布 `2×9P Φ0.95–1.0mm` / `Φ1.40mm` 偏内焊盘兼容已购 `-M` 不拆排针直插，双排底面剪平磨平＋全覆双层 `0.08mm` Kapton，与 `14.50mm` `J2` `[-6.20,+8.30]` 固定焊盘错开防重叠；⚠️ **上板前齐根剪断 `ME6217` 第 5 脚 `VOUT` 并测通断！** 底部 `GP14` & `GP15` 各开 `Φ1.4mm / Φ2.0mm` 过孔，`-M` 先预焊 `1.5cm` 短丝再穿孔）。
- **Hi-Fi 音频链**：`U2: PCM5102APWR (C107671)` + **`U5: TPA6132A2RTER (C69901, -6dB 增益 + R19/C26 100ms 软启动)`** + `J3: PJ-320D-SMT (C22459515)`（集成于主板 Top `-X` 侧翼 `Z=92.8..108.2mm, cx=-13.10, cy=+2.40`，距 `S3-Zero` 焊盘净空 `0.60..0.90mm`）。
- **电源与电量遥测**：`U3: TP4056 (C16581, R1=4.7k -> 255mA, LED1 置 -X 翼 J3 下方露空 Z=92.8..94.0mm)` + `U4: AP2112K-3.3TRG1 (C51118, 600mA LDO -> 3V3_ALWAYS)` + `Q2: AO3401A 理想二极管 + R12=1k/C17=1uF 防拔线塌陷` + `Q3: AO3401A 外设总开关 (GP14)` + **`R21/R22 100kΩ (Basic C25803) + C27 100nF (C14663) -> GP15 (ADC2_CH4)`**。
- **推荐电芯**：**`551255 3.7V 350–400mAh`**（`55×12×5.5mm`，含 +10% 鼓包 `6.05mm` 仍留 `+0.50mm` 净空；亦可兼容标称 `6.0mm` `601260`）。
- **结构外观**：`Φ24.0mm × 117.5mm`（含居中挂绳耳 `122.0mm`）1:1 比例圆柱形（深色帽 `25.0mm` : 银主体 `74.5mm` = `0.336`）、`+Y/-Y` 分瓣止口、`-X` 侧肩兜腔 `R1.30mm`（`Φ2.5mm` 铣刀）与上段让位槽、`R1.20mm` 圆角 `02` 扁平盖板、`01` 兜槽 `15.80×58.52mm`（底槽 `15.76×58.48mm`, `+0.16mm`/边）、`04/05` **真圆 `Φ1.280mm` `M1.6` 孔**（CNC 铝建议 `Φ1.30mm` 平底机攻 `M1.6×0.35`，配头下螺纹长 `L=2.0~2.2mm` 短机丝即 `M1.6×2`）、背面 `R1.35mm (3.10×3.56mm)` 药丸按键 (`K1@Z62..K4@Z38`)、`06` `0.60mm` 承托台肩（`Z>84.5mm` 全退至 `Y<=-2.05mm` 零压 `-7.62mm` 焊点）。

## 2. 关键文件路径（Rev 2.7）
- CAD 模型生成器（Rev 2.7）：[generate_cad_models.py](cad/scripts/generate_cad_models.py)
- BOM 生成脚本（Rev 2.7）：[generate_hardware_files.py](hardware/generate_hardware_files.py)
- 立创商城基础 BOM（Rev 2.7, 22 项）：[BOM_JLCPCB_Persona3_MP3.csv](hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv)
- Rev 2.7 正式制板 & Top 经济型 SMT 制造包（`0` DRC）：
  - Gerber + 钻孔压缩包：[Gerber_Persona3_MP3_Rev27.zip](hardware/rev27_fab/Gerber_Persona3_MP3_Rev27.zip)（`148,960` B，2 层 `1.000mm`，PTH `0.2997×2 / 0.3002×183 / 0.8001×2 / 0.9500×18`；NPTH `0.5499×13 / 1.0000×2 / 1.4000×2 / 2.0000×4`）
  - Top-Only SMT BOM：[BOM_JLCPCB_TOP_SMT_Rev27.csv](hardware/rev27_fab/BOM_JLCPCB_TOP_SMT_Rev27.csv)（21 行 / 64 颗，100% 含 LCSC 料号）
  - Top-Only SMT 坐标：[CPL_JLCPCB_TOP_SMT_Rev27.csv](hardware/rev27_fab/CPL_JLCPCB_TOP_SMT_Rev27.csv)（64 颗，全部 `Layer=T`，已剔除 `U1/J2/BT*/TP*`）
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
- [x] Rev 2.7 全部 7 个 STL (`00..06`) 重新生成并经过拓扑、`Z-ray`、真圆 `Φ1.280mm` `M1.6`、`06 Z>84.5` 全退让、实板 `1.6mm` `-M` 与 `14.50mm J2` 角包络全检 **PASS**。
- [x] 立创 EDA Pro `Persona3_MP3_Rev27 | PCB1` 全板实盘布线、铺铜（185 过孔/4 铜皮/0 孤岛）、`1.000mm` 层叠与丝印完成，API 与编辑器 UI 双检 **`DRC Total = 0`**（141 项全通过，2D/3D 检视完成），Formal 制造包导出至 `hardware/rev27_fab/` 并核对 BOM/CPL 64/64 零差异。
- [x] 三维猴 `jlc-3dp.cn` 清空 5 件旧 Rev 1 购物车并完成 `06_internal_zero_solder_sled.stl`（`PA12` 黑色 `¥5.90`）加车；记录 `02` 屏幕透明镜片（`0.80mm` 低于 DFM `>=1.2mm`）改走定制 `0.8mm` PMMA 激光切割，以及 `jlc-cnc.com` 须转 B-rep `.step/.stp` 后上传 `01/03/04/05`。
- [ ] 待用户人工接力下单项（均未提交付款）：`jlc.com`（`¥30` PCB 已载入待选 5 项个人选项并提交后方可传 `jlc-smt.com` BOM/CPL，或登录国际站 `cart.jlcpcb.com`）；`jlc-cnc.com` 传 `.step`；`taobao.com`（已完成购物车核对，搜索页待人工滑块验证后补齐 `M1.6×2` 机丝 / `0.08mm` Kapton / `30AWG` 线 / `551255` 锂电 / `S3-Zero`）。
- [x] `generate_hardware_files.py` (22项 BOM, `\n` 行尾)、`REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md`、`README.md`、`ui_preview/index.html`、`plan.md` 同步至 Rev 2.7。
- [x] 固件 `firmware/src/main.cpp`（锁库 + 全异常音频保护 + 熄屏防锁 + OTA亮屏 + NVS + 按需刷新）经 PlatformIO 编译通过 (`0 error, 0 warning`)。
- [x] 已完成多轮独立 zero-trust 回归审计与所有 Major/Minor 闭环。
