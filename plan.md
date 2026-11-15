# Persona 3 Reload (P3R) MP3 Player — 项目主状态与架构计划 (`plan.md`)

> 本文件作为长任务唯一真相源（Single Source of Truth），与代码、CAD 与 BOM 同步更新。

## 1. 当前硬件采购与复用状态 (Rev 2.3)
- **屏幕（已确认型号）**：优信电子 `2.25寸 TFT裸屏_8PIN插接`（ST7789P3, 76×284, `17.90 × 62.50 × 2.36 mm`，AA `14.80 × 55.30 mm`，顶边框 `1.61mm`，底COF边框 `5.595mm`，0.5mm 8Pin 21–23mm 排线背折接入 `J4 FPC-05F-8PH20 C2856797`）。
- **主控**：Waveshare `ESP32-S3-Zero`（`23.5 × 18.0mm`；⚠️ **务必拆除板载 `ME6217` 5脚 LDO 后再焊上主板！**）。
- **Hi-Fi 音频链**：`U2: PCM5102APWR (C107671)` + **`U5: TPA6132A2RTER (C69901, -6dB 增益 + R19/C26 100ms 软启动)`** + `J3: PJ-320D-SMT (C22459515)`（已直接上移至主板 Top `-X` 侧翼 `Z=94.0..108.2mm`，取消独立音频子板）。
- **电源与充电**：`U3: TP4056 (C16581, R1=4.7k -> 255mA)` + `U4: AP2112K-3.3TRG1 (C51118, 600mA LDO -> 3V3_ALWAYS)` + `Q2: AO3401A 理想二极管 + R12=1k/C17=1uF 防拔线塌陷` + `Q3: AO3401A 外设总开关 (GP14)`。
- **推荐电芯**：**`551255 3.7V 350–400mAh`**（`55×12×5.5mm`，含 +10% 鼓包 `6.05mm` 仍留 `+0.50mm` 净空；亦可兼容标称 `6.0mm` `601260`）。
- **结构外观**：`Φ24.0mm × 117.5mm`（含居中挂绳耳 `121.5mm`）1:1 比例圆柱形（深色帽 `25.0mm` : 银主体 `74.5mm` = `0.336`）、`-X` 侧肩 3.5mm 耳机突起与上段让位槽、`02` 扁平盖板、`01` 正交 4 面铝止口、背面 4 颗独立弹性槽药丸按键 (`K1..K4`)。

## 2. 关键文件路径
- CAD 模型生成器（Rev 2.3）：[generate_cad_models.py](cad/scripts/generate_cad_models.py)
- BOM 生成脚本（Rev 2.3）：[generate_hardware_files.py](hardware/generate_hardware_files.py)
- 立创商城 SMT BOM（Rev 2.3）：[BOM_JLCPCB_Persona3_MP3.csv](hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv)
- 立创 EDA 原理图网表、`-X` 侧翼单板布局与下单指南：[REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md](docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)
- 固件主程序：[main.cpp](firmware/src/main.cpp)

## 3. Rev 2.2 → Rev 2.3 演进摘要
1. **Rev 2.2 独立复审 7 红 + 7 黄加固（已并入基线）**：`01/02` 彻底正交化、`04/05` 真正 `4.0mm` 柱形止口与同轴 `M1.6` 孔、`06` 刚性 `1.0mm` 平桥与 `03` 弹性槽、`J2` 侧插、`K1..K4` 外部上拉 + `RTC_PERIPH` 深睡唤醒锁定、`R12=1k/C17=1uF`、`TPA6132 100ms` 软启、`R20=470R` 串口隔离、`ST7789` 延时消残影、USB MSC 非整块传输与两步退出确认，并在 PlatformIO 零警告编译通过。
2. **Rev 2.3 外观 1:1 还原＋降本减复杂度升级**：
   - 将 `3.5mm` 耳机座（`PJ-320D-SMT`）从顶面下移至主板 Top `-X` 侧翼（`Z=94.0..108.2mm, cx=-12.70, cy=+2.40`），还原 `04` 深色帽盖左下 `-X` 耳机侧肩凸起与 **`Φ7.4mm` 轴向顶孔 + `Φ8.7mm` 上段让位弧槽 + 正中居中挂绳耳**。
   - **比例精准权衡**：将 `04` 筒身高度由 `30.5mm` 收缩 `5.5mm` 至 **`25.0mm`**（不盲目截短 `10mm`），使 **深色帽 / 银主体 = `25.0 / 74.5 = 0.336`** 精确居于剧场版实物 `0.327` 与 P3R 片头 `0.350` 之间；整机长 `117.5mm`（含挂绳耳 `121.5mm`）。
   - **结构强度与工程简併**：`-X` 侧翼呈 `14.9mm` 竖向 `FR-4` 深梁受剪并受 `04` 前套箍周圈保护，取消旧版独立台阶音频子板，全机由 3 块 PCB 缩减为 **2 块板**（`Main PCB` + `6mm Button Strip`），彻底免去半孔叠焊飞线。

## 4. 当前进度清单
- [x] Rev 2.3 `04` `-X` 侧肩+居中挂绳 STL 重新生成，网格检查（0 非流形 / 0 退化）与全 3D 截面+圆柱包络防碰撞检查 **100% PASS**。
- [x] `generate_hardware_files.py`、`BOM_JLCPCB_Persona3_MP3.csv`、`REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md` 与 `README.md` 同步更新至 Rev 2.3。
- [x] 固件 `firmware/src/main.cpp` 在硬件无引脚变动前提下维持 PlatformIO 洁净基线。
- [x] **Rev 2.3 已提交并推送至 `origin/main`**：待基于 GitHub 最新版完成全量跨学科 Review 后，即可按指引进入立创EDA绘制、导出 Gerber/CPL 与嘉立创打样下单。
