# Persona 3 Reload (P3R) MP3 Player — 项目主状态与架构计划 (`plan.md`)

> 更新时间：2026-11-15（Rev 2.1：依据 `rev2_preproduction_audit_report.md` 完成硬件、CAD 与固件全面返修定稿）

## 1. 当前硬件采购与复用状态
- **已取消 / 研发损耗核销**：
  - 原 Rev 1 PCB + SMT 贴片单：**已取消**。
  - 原 `0.91"` OLED 与 `02` 黑色半透弧面镜片：**计入研发损耗**。
  - 原淘宝已下单通用插件（`ESP32-S3-Zero`、梵想 `32GB TF 卡` 等）：**继续保留**用于 Rev 2.1 装配。
- **待立创绘板 / CNC 下单**：
  - **Rev 2.1 主板（`99.0×17.6mm, 1.0mm`）+ 按键子板（`32.0×6.0mm + 5mm 工艺边`）**：按 [REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md) 与 [BOM_JLCPCB_Persona3_MP3.csv](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv) 在立创 EDA 绘板过 DRC 后，将 `J2/J3` 从 CPL 剔除（改到手补焊）以下单嘉立创 **经济型单面（Top Only）SMT**。
  - **CNC `01 / 03 / 04 / 05` + `02` 扁平透明窗 + `06` 3D打印/CNC内托**：7 个 Rev 2.1 STL 已全部重新生成并实测 `non_manifold = 0`、15 项整机 3D 包络全通（0 碰撞）。

## 2. 关键文件路径
- **Rev 2.1 立创 EDA 权威设计指南（原理图全网表 + 21项BOM + 布局规则）**：[REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)
- **Rev 2.1 权威立创 BOM CSV（已清除全部错版历史草稿 Gerber/CPL）**：[BOM_JLCPCB_Persona3_MP3.csv](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv)
- BOM 生成脚本：[generate_hardware_files.py](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/hardware/generate_hardware_files.py)
- Rev 2.1 CAD / STL 生成脚本与 7 个无干涉 STL：[generate_cad_models.py](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/cad/scripts/generate_cad_models.py) / `cad/stl/`
- Rev 2.1 固件工程与引脚定义：[platformio.ini](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/platformio.ini) / [p3r_ui_assets.h](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/include/p3r_ui_assets.h) / [main.cpp](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/src/main.cpp)
- 投产前审计报告参考：`C:\Users\wjwpo\.gemini\antigravity\brain\2badea8e-dc7f-48fe-a9d5-3f2d56a03dfe\rev2_preproduction_audit_report.md`

## 3. Rev 2.1 核心返修摘要（对照审计报告全部闭环）
1. **音频链路纠正**：核对 TI `SLAS859` 修正 `PCM5102APWR` 第 `10..20` 脚定义；加入 TI DirectPath **`TPA6132A2RTER (C69901)`** 耳机功放（`-6 dB` 消除削波爆音、避免 4 极 CTIA 串音；`Pin 12 HPVDD` 严格独立接 `4.7uF C19666` 到地）；`C9/C10` 改回真 `2.2nF (C93190)`，`C5/C6/C24/C25` 升级 `4.7uF 16V (C19666)`。
2. **显示排线与 BOM 校对**：`J4` 纠正为真 8-Pin `FPC-05F-8PH20 (C2856797)`，移至 `Z=36..38mm` 对接 23mm 背折排线；`GP9 (TFT_SCLK)` 加 `R14 (10k)` 上拉至 `3V3_PERI` 配合 `SPI Mode 3`；背光 PWM 提频至 `32kHz`；`SW1..SW4` 改为 `6.0mm` 宽子板（+5mm 工艺边）。
3. **双 LDO 防倒灌 + 理想二极管 + 微安级关机**：焊前拆除 `ESP32-S3-Zero` 上 `ME6217C33M5G`；`U4` 升级 `600mA AP2112K-3.3TRG1 (C51118)`；`D2` 改由 `Q2 (AO3401A)` 实现 `~15mV` 理想二极管 ORing；新增 `Q3 (AO3401A)` 受 **`GP14 (PIN_PERI_PWR_EN)`** 门控，支撑 `K1` 长按 `2.5s` 彻底断开外设进入深度睡眠（按 `K1` 一键唤醒）。
4. **CAD 三维零干涉闭环**：`01` 改为 `y_inner_flat=+7.45mm`（消除了负壁厚），加入四面 `0.55mm` 止口台阶稳托 `02`（`15.40×58.20×0.80mm`），背面增设 `M1.6` 隐藏机米螺丝锁孔（`Z=19.5, 93.5`）；`04` 与 Bottom 焊装的 `PJ-320D-SMT` 在 `(-3.50, -3.60)` 完全同心且为 `+Y` USB-C 插头留空通道；`06` 退居下半区（`Y<=+1.06mm`）并在 `Y=-7.75..-8.65mm` 构筑刚性桥壁隔离 `601260` 电芯与 `Btn PCB`。
5. **固件稳定化**：锁定 `espressif32 @ 6.9.0` + `esphome/ESP32-audioI2S @ ^2.0.7` 与 `qio_qspi` PSRAM 配置；设 `ARDUINO_USB_CDC_ON_BOOT=0` 并采用 `Preferences ("p3r"/"usb_msc")` 重启切换原生 `USBMSC`（退出前干净 `msc.end() + SD.end() + ESP.restart()`）；设 `SPI Mode 3` + `32kHz PWM` + `160MHz` 主频 + 完全非阻塞四按键状态机 + `GP14` 上电冷复位 + `K1` 深睡开关机。

## 4. 当前进度清单
- [x] **Rev 2.1 CAD/STL 全检闭环**：7 份 STL 全部 `non_manifold = 0`，15 项 3D 包络干涉检测 `0` 碰撞。
- [x] **Rev 2.1 BOM 与历史错版文件清理**：仅保留权威 `BOM_JLCPCB_Persona3_MP3.csv`（21 项），删除误导性草稿 Gerber/CPL。
- [x] **Rev 2.1 立创 EDA 设计指南更新**：引脚定义（`PCM5102A`, `TPA6132A2`, `AP2112K`, `AO3401A`）、坐标与工艺规避说明全面对齐。
- [x] **Rev 2.1 固件代码返修与实机镜像编译通过**：完成 `platformio.ini`, `p3r_ui_assets.h`, `main.cpp`（已通过 `PlatformIO 6.2.0 / espressif32 @ 6.9.0` 清理全量编译，0 报错 0 告警，输出 `firmware.bin`，RAM `15.6%` / Flash `71.9%`，`qio_qspi` PSRAM 已启用）。
- [ ] **下一步用户执行**：按 [REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md) 在立创 EDA 原理图与 PCB 画板过 DRC（务必核对 `C22459515` 定位孔与 Pin 4 定义）-> 导出 Gerber/BOM/CPL（去掉 `J2/J3`）下嘉立创 SMT -> 确认后下 CNC 单 -> 硬件到手后直接 `pio run -t upload` 烧录测试。
