# Persona 3 Reload (P3R) MP3 Player — 项目主状态与架构计划 (`plan.md`)

> 本文件作为长任务唯一真相源（Single Source of Truth），与代码、CAD 与 BOM 同步更新。

## 1. 当前硬件采购与复用状态
- **屏幕（已确认型号）**：优信电子 `2.25寸 TFT裸屏_8PIN插接`（ST7789P3, 76×284, `17.90 × 62.50 × 2.36 mm`，AA `14.80 × 55.30 mm`，顶边框 `1.61mm`，底COF边框 `5.595mm`，0.5mm 8Pin 21–23mm 排线背折接入 `J4 FPC-05F-8PH20 C2856797`）。
- **主控**：Waveshare `ESP32-S3-Zero`（`23.5 × 18.0mm`；⚠️ **务必拆除板载 `ME6217` 5脚 LDO 后再焊上主板！**）。
- **Hi-Fi 音频链**：`U2: PCM5102APWR (C107671)` + **`U5: TPA6132A2RTER (C69901, -6dB 增益 + R19/C26 100ms 软启动)`** + `J3: PJ-320D-SMT (C22459515)`。
- **电源与充电**：`U3: TP4056 (C16581, R1=4.7k -> 255mA)` + `U4: AP2112K-3.3TRG1 (C51118, 600mA LDO -> 3V3_ALWAYS)` + `Q2: AO3401A 理想二极管 + R12=1k/C17=1uF 防拔线塌陷` + `Q3: AO3401A 外设总开关 (GP14)`。
- **推荐电芯**：**`551255 3.7V 350–400mAh`**（`55×12×5.5mm`，含 +10% 鼓包 `6.05mm` 仍留 `+0.50mm` 净空；亦可兼容标称 `6.0mm` `601260`）。
- **结构外观**：`Φ24.0mm × 123.0mm`（含挂绳耳 `127.0mm`）1:1 长条圆柱形、`02` 无弧度扁平盖板、`01` 正交 4 面实心铝内止口防跌落、背面 4 颗独立弹性槽药丸按键 (`K1..K4`)。

## 2. 关键文件路径
- CAD 模型生成器（Rev 2.2）：[generate_cad_models.py](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/cad/scripts/generate_cad_models.py)
- BOM 生成脚本（Rev 2.2）：[generate_hardware_files.py](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/hardware/generate_hardware_files.py)
- 立创商城 SMT BOM（Rev 2.2）：[BOM_JLCPCB_Persona3_MP3.csv](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv)
- 立创 EDA 原理图网表、台阶音频子板与下单指南：[REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)
- 固件主程序：[main.cpp](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/src/main.cpp)

## 3. Rev 2.2 核心返修摘要（对照 Rev 2.1 独立审计报告 7 红 + 7 黄 100% 闭环）
1. **CAD 01 窗口与 02 盖板彻底正交化 (`±7.50 / ±7.78mm`)**：消除极坐标径向内收导致的 `TFT AA` 遮挡与 `02` `14` 处啃咬干涉；实测 `Y=6.98..7.95` 内框全宽恒为 `15.00mm`，`1.08mm` 4 边铝止口全完整。
2. **CAD 04/05 `4.0mm` 真正柱形止口 + 同轴 `M1.6` 锁孔**：`0.02mm` Z 轴阶跃消除锥形喇叭口胀裂（切片实测 `OD=21.20mm / ID=19.00mm` 上下恒定），`M1.6` 孔内缩至距接缝 `2.0mm`（`Z=20.0 & 90.5mm`）并在 `04/05` 止口内同轴预开螺纹引导孔。
3. **CAD 06 正交后按键槽 (`6.40mm`) + 实心 `1.00mm` 平桥 (`Y=-7.65..-8.65mm`)**：消除 `0.32mm` 薄壁与电池挤压；电池仓底面平直达 `6.55mm` 高度，顶导轨在 `Z>84.5mm` 让位 `18.0mm S3-Zero`；`03` 按键条增设 `0.15mm` 预紧间隙、加宽翼边及 `Z=42/50/58mm` 抗连按凹槽。
4. **主板截断 `Z=108.2mm` + 台阶音频子板（Bottom `Y=-2.10..-1.10mm`）**：`12.0×6.4mm` 市售 USB-C 插头在 `Z>108.2mm` 零阻挡；`J3 (PJ-320D-SMT)` 位于台阶子板 `(-3.20, -4.60)` 与 `04` 顶 `Φ8.4mm` 孔同心。
5. **顶帽接缝下移 `Z=92.5mm` + `J2 (TF-01A)` 侧向抽插 (`Z=90.8..105.6mm`)**：卡口 `Z=92.7..103.7mm` 完全高出 `01` 铝环上缘（取帽后直接 `+X` 侧插拔）；`J4` 下移 `Z=34.0..35.5mm` 增加排线余量；增加 `GP14` 背面 `2.8mm` 助焊孔并确立「先拆 `ME6217` → 焊 `S3-Zero` + 测通断 → 贴高温胶带 → 最后焊 `J2`」工艺顺序。
6. **电路 & 固件防隐患加固**：`K1..K4` (`R15..R18`) 增加外部 `10k -> 3V3_ALWAYS` 上拉、`enterDeepSleepPowerOff()` 启用 `RTC_PERIPH` + `rtc_gpio_pullup_en` 锁定 `GPIO1` 唤醒；`R12=1k/C17=1uF` 消除拔线塌陷；`TPA6132 EN` 增加 `10k+10uF (R19/C26)` `100ms` 消爆音软启；`R20=470R` 隔离 `GP43(TX)->TFT_DC`；`R1=4.7k` 匹配 `551255`；`ST7789` 上电等待 `130ms` 且首帧刷屏后开背光；U盘模式 `onUSBRead/Write` 支持偏移分包并对按键退出增加 2 次确认防丢数据；清除旧版 Rev 1 过时文档与 KiCad 残留。

## 4. 当前进度清单
- [x] Rev 2.2 全套 7 个 STL 重新生成，网格检查（0 非流形 / 0 退化）与全 3D 截面+包络防碰撞检查 **100% PASS**。
- [x] `BOM_JLCPCB_Persona3_MP3.csv` 与 `REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md` 同步更新至 Rev 2.2，并清理旧版 Rev 1 文件。
- [x] `firmware/src/main.cpp` 完成 Rev 2.2 固件加固并在本地 `PlatformIO` 环境零警告编译通过，最终提交推送 GitHub。
