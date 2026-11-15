# Persona 3 Reload (P3R) MP3 Player — 项目主状态与架构计划 (`plan.md`)

> 更新时间：2026-11-15

## 1. 当前硬件采购与复用状态
- **已下单（保留/复用）**：
  - **PCB + SMT 贴片**：已下单（`68mm × 17.5mm`，含 `PCM5102A` DAC、`TF-01A` 卡座、`PJ-342B` 3.5mm 耳机座、`TP4056` 充电、`3.3V LDO`）。尺寸完全兼容 `Φ24` 新外壳内腔（D 形平面内腔弦长 `18.7mm`），可通过 `ESP32-S3-Zero` 排针引出 2~3 根飞线直接复用，无需强制重打板。
  - **淘宝 4 个插件 + 梵想 32GB TF 卡**：已下单（`0.91" OLED` 与 `02` 弧形镜片降级为桌面裸板/公差验证件）。
  - **3D 打印 `02` 透明镜片**：已下单（`8001 透明喷油`），保留作公差/透光验证件。
- **已暂停（未付款）**：
  - **CNC `01 / 03 / 04 / 05` + `06` 支架**：已按 `p3r_mp3_cad_review.md` 暂停下单，待按路线 B（1:1 动画修长比例 + 条形 IPS 屏）重做后下单。

## 2. 关键文件路径
- 硬件 PCB 生成与 DRC：[generate_hardware_files.py](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/hardware/generate_hardware_files.py)
- CAD / STL 生成脚本：[generate_cad_models.py](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/cad/scripts/generate_cad_models.py)
- STL 输出目录：`C:\Users\wjwpo\.gemini\antigravity\scratch\persona3_mp3\cad\stl\`
- 固件主程序：[main.cpp](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/src/main.cpp)
- 引脚与歌单头文件：[p3r_ui_assets.h](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/include/p3r_ui_assets.h)
- 外观审批意见参考：`C:\Users\wjwpo\.gemini\antigravity\brain\2badea8e-dc7f-48fe-a9d5-3f2d56a03dfe\p3r_mp3_cad_review.md`

## 3. 接口与尺寸约束（路线 B 目标）
- **总外形**：`Φ24.0mm` × 总长 `120–125mm`（长径比 ≈ `5.1:1`），主体 `01` 切出正面 D 形平面（`y = +9.5mm`，平面宽 `14.7mm`）+ 平板透明亚克力/玻璃窗。
- **端盖设计**：
  - `05` 底部：无大孔完整半椭球弹头（`r(0)=0`）+ 接缝 `0.3–0.4mm` V 形槽。
  - `04` 顶部：藏青哑光（`27–30mm`），平顶 + 下沉耳机孔 + 居中/偏后小挂耳 + 交界处倒角。
  - `03` 按键：移至背面 `-Y` 齐平药丸键（或精简按键），不破坏正面轮廓。
- **屏幕升级**：改用 **ST7789 SPI 条形 IPS TFT**（目标可视区 ~`14.5 × 55–65mm`，如 `76×284` 规格或实测尺寸），固件支持浅灰底黑字（动画版）/ 浅青蓝底。
- **ESP32-S3-Zero 引脚分配**：
  - I2S：`GP4(BCK), GP5(WS), GP6(DOUT)`
  - SD SPI：`GP10(CS), GP11(MOSI), GP12(SCK), GP13(MISO)`
  - 按钮：`GP1, GP2, GP3, GP7`
  - 原 OLED 接口：`GP8, GP9`（可复用作新屏幕 SPI 时钟/数据，另从 S3 排针引出 `DC / RES / BLK`）

## 4. 路线 B（Rev 2）已锁定元件参数
- **显示屏**：**金逸晨电子 2.25 寸 `76×284` IPS TFT 裸屏**（`ST7789P3`，4-Wire SPI）
  - 玻璃外框：`17.90±0.10 × 62.50±0.10 × 2.36±0.10 mm`
  - 有效显示区 (A.A.)：`14.797 × 55.295 mm`（上边距 `1.61mm`，左右边距 `1.55mm`）
  - FPC 排线：长 `23±0.3mm`，宽 `4.5±0.07mm`，**8-Pin `0.5mm` 间距**（接触面在背面）：
    `1:LEDA, 2:GND, 3:RESET, 4:RS(DC), 5:SDA, 6:SCL, 7:VDD(3.3V), 8:CS`
- **电池**：**`601260` 3.7V `420mAh` 聚合物锂电池**（`60 × 12 × 6 mm`）

## 5. 关键审计结论与当前进度
- [x] **元件锁定**：`2.25" 76×284 ST7789P3`（8-Pin `0.5mm` FPC）+ `601260 420mAh` 电池规格与引脚定义已完全确认。
- [x] **Rev 2 CAD（已完成）**：`Φ24 × 123mm` 1:1 动画修长机身（`01` D形平面 `y=+9.10mm`、`02` 平板透明窗、`03` 背面齐平按键、`04` 藏青平顶沉孔+小挂耳、`05` 无孔半椭球+V槽、`06` 加长内胆支架），`01~05` 均已验证 `non_manifold = 0`。
- [x] **Rev 2 固件（已完成）**：[platformio.ini](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/platformio.ini)、[p3r_ui_assets.h](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/include/p3r_ui_assets.h)、[main.cpp](file:///C:/Users/wjwpo/.gemini/antigravity/scratch/persona3_mp3/firmware/src/main.cpp) 已切至 `LovyanGFX` (`ST7789P3 284×76`) 浅灰底黑字 LCD UI，支持 `GP44` 息屏断背光（待实机板到位后 PlatformIO 编译烧录）。
- [ ] **Rev 2 PCB（⚠️ 关键安全阻塞点 — 不可直接用脚本 Gerber 下单 SMT）**：
  - 经审计，`hardware/generate_hardware_files.py` 中的 Gerber 仅含部分示意铜线且未经过立创 EDA 官方封装库原点校验（`TF-01A` / `PJ-320D` / `8P FPC` 等异形件绝不可靠手写坐标下单 SMT）。
  - 下一步需在 **立创 EDA（EasyEDA）** 或 **KiCad** 中按核定 BOM 与逐脚网络表建立原理图 -> 转 PCB -> 使用 LCSC 官方 C 编号封装完成全部走线、铺铜与 DRC 通过后，再导出 Gerber/BOM/CPL 下单。
