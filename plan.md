# Persona 3 Reload (P3R) MP3 Player — 项目主状态与架构计划 (`plan.md`)

> 更新时间：2026-11-15（Rev 2 原理图网表、BOM 与立创 EDA 设计指南定稿）

## 1. 当前硬件采购与复用状态
- **已取消 / 研发损耗核销**：
  - 原 Rev 1 PCB + SMT 贴片单：**已取消**（重做 Rev 2 原生集成 `8-Pin 0.5mm` FPC 接口及新版电源/背光电路）。
  - 原 `0.91"` OLED 与 `02` 黑色半透弧面镜片：**计入研发损耗**。
  - 原淘宝已下单通用插件（`ESP32-S3-Zero`、梵想 `32GB TF 卡` 等）：**继续保留**用于 Rev 2 装配。
- **待定稿重下**：
  - **Rev 2 主板（+ 按键子板拼版）**：按 [REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md) 与 [BOM_JLCPCB_Persona3_MP3.csv](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv) 在立创 EDA 绘板通过 DRC 后下单嘉立创 `1.0mm` 单面经济型 SMT。
  - **CNC `01 / 03 / 04 / 05` + `02` 平面窗 + `06` 内托**：待立创 EDA 完成 PCB 3D 尺寸核对（特别是确认 `04` 顶部耳机孔 `cy` 改为 `+1.50mm` 或保持 `0mm` 改用沉板耳机座）后最终下 CNC 单。

## 2. 关键文件路径
- **Rev 2 立创 EDA 权威设计指南（原理图全网表 + BOM + 布局规则）**：[REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md)
- **Rev 2 权威立创 BOM CSV**：[BOM_JLCPCB_Persona3_MP3.csv](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv)
- BOM 生成与参考草稿脚本（**勿直接用脚本 Gerber 下单**）：[generate_hardware_files.py](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/hardware/generate_hardware_files.py)
- CAD / STL 生成脚本与输出：[generate_cad_models.py](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/cad/scripts/generate_cad_models.py) / `cad/stl/`
- 固件源码与引脚定义：[main.cpp](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/src/main.cpp) / [p3r_ui_assets.h](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/include/p3r_ui_assets.h)
- 外观审批意见参考：`C:\Users\wjwpo\.gemini\antigravity\brain\2badea8e-dc7f-48fe-a9d5-3f2d56a03dfe\p3r_mp3_cad_review.md`

## 3. Rev 2 已锁定核心件与关键电气修正
- **屏幕**：**`优信电子 2.25寸 TFT裸屏_8PIN插接`**（`ST7789P3`, `76×284`, 4 线 SPI，玻璃 `17.90×62.50×2.36mm`，可视区 `14.80×55.30mm`；客服确认是否有 IPS 改版，电气与 8PIN 下接脚位兼容）。
  - 排线引脚（`1..8`）：`1:LEDA, 2:GND(兼LEDK), 3:RESET, 4:RS(DC), 5:SDA, 6:SCL, 7:VDD, 8:CS`；对应 `C2856800` 下接翻盖 FPC 座（背面 180° 折弯后金手指正对 PCB Top 面）。
- **背光驱动修正**：因 8PIN 裸屏内部已将 `LEDK` 短接至 `Pin 2 GND`，不可使用低边 NPN 三极管，Rev 2 已全面切换为 **高边 P-MOS `AO3401A (C15127)`** + `R4 (10k)` 上拉 + `R10 (1k)` + `R9 (10Ω)`；[main.cpp](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/src/main.cpp#L73) 已同步设 `cfg.invert = true`（`GP44` 低电平点亮）。
- **DAC 引脚核准（TI PCM5102APWR `TSSOP-20`）**：`Pin 12 = XSMT`（`R7 10k` 上拉 `3V3` 解静音），`Pin 17 = SCK`（**直接接地 `GND`** 启用内部 PLL），`Pin 10/11/13 = FLT/DEMP/FMT` 接地，`Pin 19 = LDOO` 仅接 `100nF` 到地。
- **电源与充电**：`TP4056 (C16581)` 配 `R1 = 3.3k`（`~364mA` 适配 `601260 420mAh` 锂电），`LED1 (C2286)` 仅由 `USB_5V` 驱动（拔线零耗电），`D1/D2 (1N5819WS)` 实现 USB/电池无缝切换至 `RT9013-33GB (C47773)`。
- **结构与按键协同**：主板 `1.0mm` 厚（`66×17.6mm` 主区 + `28×15.8mm` 上延舌伸入 `04` 直连 `PJ-320D` / `TF-01A` / USB-C）+ 邮票孔同板拼出 **`32×4mm` 按键子板**（`4× TS263065A C49023761` `0.65mm` 超薄开关，总厚 `1.65mm` 无干涉卡入 `601260` 电池与 `03` 药丸按键之间 `1.80mm` 仓位）。

## 4. 当前进度清单
- [x] **元件锁定与网表核准**：完成 2.25" 8PIN TFT + `601260` + `PCM5102A` + `TP4056` + `RT9013` + `ESP32-S3-Zero` 全脚位逐一查证。
- [x] **Rev 2 CAD（V2.0 初版已完成）**：`01~05` 均已验证 `non_manifold = 0`（待随 PCB 确定是否微调 `04` 耳机孔 `cy = +1.5mm`）。
- [x] **Rev 2 固件（已完成）**：`LovyanGFX` 适配 `ST7789P3 284×76` 及 `AO3401A` 反相 PWM 调光/熄屏，待新板回板烧录编译实测。
- [x] **Rev 2 立创 EDA 设计指南与完整 BOM（已完成）**：输出 [REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/docs/REV2_LCEDA_SCHEMATIC_AND_PCB_GUIDE.md) 及同步更新后的 `BOM_JLCPCB_Persona3_MP3.csv`（20 项 35 颗贴片料）。
- [ ] **下一步用户执行**：在立创 EDA 依文档画原理图 -> 布局布线并过 DRC -> 导出 Gerber/BOM/CPL 下单嘉立创 `1.0mm` 单面 SMT，同步微调/确认 `04` 耳机孔偏移后下 CNC 单。
