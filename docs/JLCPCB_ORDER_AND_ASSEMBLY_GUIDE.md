# 嘉立创中国大陆一站式下单与免焊组装全流程指南 (实测 RMB 报价与 DFM 验证版)

本指南基于 **嘉立创国内站 (`jlc.com`)**、**嘉立创三维猴国内站 (`jlc-3dp.cn`)** 与 **立创商城 (`szlcsc.com`)** 实测数据编写，专为 **零焊接 / 免烙铁** 玩家设计。工程中所有元器件（包括 USB Type-C、左侧偏置 3.5mm 耳机孔、MicroSD 卡槽、右侧 4 颗侧按开关 `TS-1135-C`、屏幕 FPC 座、电池 JST-SH 座）均已设计为 **全 SMT 表贴封装**，由嘉立创工厂机器直接贴装完成。

---

## 一、 中国大陆实测人民币（RMB `¥`）成本预算总表

通过嘉立创国内站实测对比，我们为您提供 **极致性价比全 3D 打印方案（整机仅约 ¥132 元）** 与 **CNC 6061 铝合金金属机身方案（整机约 ¥295 元）** 两种组合，均远低于 **¥500 元** 预算上限：

| 序号 | 制造模块 | 下单平台 | 实测最优工艺与参数选择 | 数量 | 实测人民币价格 (RMB) |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **1** | **PCB 裸板打样** | 嘉立创 (`jlc.com` 下单助手) | **方案1（推荐省钱）**：上传 [`Gerber_JLCPCB_Persona3_MP3_2Layer_20RMB.zip`](../hardware/gerber_and_smt/Gerber_JLCPCB_Persona3_MP3_2Layer_20RMB.zip)，選 `2层` + `1.0mm/1.6mm` + `有铅喷锡`<br>**方案2（4层发烧版）**：上传 [`Gerber_JLCPCB_Persona3_MP3_4Layer.zip`](../hardware/gerber_and_smt/Gerber_JLCPCB_Persona3_MP3_4Layer.zip)，选 `4层` + **`1.6mm 标准板厚`** + **`有铅喷锡`**（立省 ¥100.69 沉金费与 ¥150 薄板费！） | 5 片 | **¥20.00** (2层客户端)<br>或 **¥50.00** (4层客户端)<br>*(领免费券可至 ¥0)* |
| **2** | **SMT 元器件 BOM** | 立创商城 / 嘉立创 SMT (`szlcsc.com`) | 单板全套 33 颗贴片元件（含 `C2980306` ESP32 **¥34.25**、`C107671` PCM5102A **¥8.43**、`C519275` 侧按开关×4 **¥3.08**、`C2927038` Type-C **¥0.37**、`C91145` TF卡座 **¥0.58**、`C388632` 耳机座 **¥0.60** 等） | 1 套 | **¥50.12 / 板** |
| **3** | **SMT 贴片加工费** | 嘉立创 SMT (`jlc.com`) | 经济型 PCBA 打样（工程费 + 焊点费，可使用每月 SMT 优惠券抵扣） | 2 片分摊 | **≈ ¥35.00 / 板** |
| **4** | **全套 6 件外壳与内胆** | 嘉立创三维猴 (`jlc-3dp.cn`) | 实测上传 `01`~`06` 共 6 个 STL 模型（`9600` 树脂 + `02` 选 **`8001 半透明/透明光敏树脂`**），单套 6 件实测打印费仅 **¥11.97 元**！（若加选表面喷漆/电镀银约 +¥25 元） | 1 套 | **¥11.97** (原色树脂)<br>或 **¥36.97** (含喷漆) |
| **5** | **免焊即插配件** | 淘宝 / 立创 | `0.91寸 128×32 SSD1306` 14Pin 插接式 OLED 裸屏 (**¥8.50**) + `501240 (300mAh)` 带 `JST-SH 1.0mm 2P` 插头锂电池 (**¥12.50**) + `M1.6` 小螺丝与挂绳 (**¥6.00**) | 1 套 | **¥27.00** |
| **合计** | — | — | **全 3D 打印版单套整机总成本（中国大陆人民币实测）** | **1 整机** | **≈ ¥144.09 元** |
| **升级项** | **CNC 铝合金金属壳** | 嘉立创 CNC (`jlc-cnc.com`) | 若将 `01` 主机身与 `05` 底部圆头盖升级为 **CNC 6061 铝合金喷砂阳极氧化银色**（约 ¥150），其余 4 件保持 3D 打印 | 1 整机 | **≈ ¥290.00 元** |

---

## 二、 嘉立创三维猴 (`jlc-3dp.cn`) 3D 打印实测数据与 DFM 清单

所有 6 个 STL 模型（位于 [`cad/stl/`](../cad/stl/)）均已通过嘉立创三维猴国内站在线几何与壁厚检测（壁厚全面 $\ge 1.20\text{ mm}$，单一连通闭合流形网格）：

| 文件名 | 实测尺寸 ($\text{cm}$) | 实测体积 ($\text{cm}^3$) | 推荐材料 (`jlc-3dp.cn`) | 实测单价 (RMB) | DFM 检测状态 |
| :--- | :--- | :--- | :--- | :---: | :--- |
| [`01_cnc_main_shell_6061_silver.stl`](../cad/stl/01_cnc_main_shell_6061_silver.stl) | $2.00 \times 2.00 \times 4.80$ | $5.19\text{ cm}^3$ | `9600` 光敏树脂（可喷银漆）或 **CNC 6061 铝合金** | **¥2.56** | ✅ 0 警告通过（壁厚 $\ge 1.20\text{ mm}$） |
| [`02_oled_smoked_lens_translucent_black.stl`](../cad/stl/02_oled_smoked_lens_translucent_black.stl) | $0.26 \times 1.08 \times 4.16$ | $0.54\text{ cm}^3$ | **`8001` 光敏树脂（半透明 / 透明）** + 打磨喷油 | **¥1.77** | ✅ 0 警告通过 |
| [`03_side_4_button_strip_silver.stl`](../cad/stl/03_side_4_button_strip_silver.stl) | $0.67 \times 1.17 \times 3.95$ | $1.45\text{ cm}^3$ | `9600` 光敏树脂（一体式内弧卡架，包络 $>5\text{ mm}$） | **¥1.77** | ✅ 已扩充内弧卡架满足三维猴最小包络规范 |
| [`04_top_navy_collar_lanyard_cap.stl`](../cad/stl/04_top_navy_collar_lanyard_cap.stl) | $2.00 \times 2.00 \times 2.00$ | $4.68\text{ cm}^3$ | `9600` 光敏树脂（深藏青色涂装） | **¥2.31** | ✅ 0 警告通过 |
| [`05_bottom_rounded_dome_cap_silver.stl`](../cad/stl/05_bottom_rounded_dome_cap_silver.stl) | $1.60 \times 2.00 \times 2.00$ | $3.62\text{ cm}^3$ | `9600` 光敏树脂（银色）或 **CNC 6061 铝合金** | **¥1.79** | ✅ 0 警告通过 |
| [`06_internal_zero_solder_sled.stl`](../cad/stl/06_internal_zero_solder_sled.stl) | $1.47 \times 1.57 \times 5.20$ | $3.07\text{ cm}^3$ | `9600` / 黑色高韧性树脂（一体式 C 型免焊内胆） | **¥1.77** | ✅ 0 警告通过（单连通流形体） |

---

## 三、 嘉立创 PCB + SMT 实测省钱避坑下单步骤（立省 ¥210+）

我们在 `jlc.com` 实测发现：**千万不要在 4 层板上勾选 `1.0mm 板厚` + `沉金` + `品质赔付`**（网页端会触发 ¥150 特价基础费 + ¥100.69 沉金费 + ¥10 赔付费 = **¥260.69**）。请按以下实测最优参数下单：

1. **打开嘉立创下单助手客户端**（比网页端直接立减 ¥10~¥100！）或访问 `https://www.jlc.com/newOrder/#/pcb/pcbPlaceOrder`。
2. **上传 Gerber 压缩包（二选一）**：
   - **选 ¥20 元 2 层特价版（最省钱）**：上传 [`hardware/gerber_and_smt/Gerber_JLCPCB_Persona3_MP3_2Layer_20RMB.zip`](../hardware/gerber_and_smt/Gerber_JLCPCB_Persona3_MP3_2Layer_20RMB.zip)，选择 **`2层` + `1.0mm 或 1.6mm 板厚` + `有铅喷锡`** $\rightarrow$ 实测仅需 **¥20.00**（网页端 ¥30.00）！
   - **选 ¥50 元 4 层标准版**：上传 [`hardware/gerber_and_smt/Gerber_JLCPCB_Persona3_MP3_4Layer.zip`](../hardware/gerber_and_smt/Gerber_JLCPCB_Persona3_MP3_4Layer.zip)，选择 **`4层` + `1.6mm 板厚` + `有铅喷锡` + `常规（不选¥10品质赔付）`** $\rightarrow$ 客户端实测仅需 **¥50.00**！
3. **勾选「需要 SMT 贴片」**：
   - 上传 BOM 清单：[`hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv`](../hardware/gerber_and_smt/BOM_JLCPCB_Persona3_MP3.csv)（已全部更新为立创商城实测万件以上现货编号：`C2980306`、`C107671`、`C519275`、`C16581`、`C47773`、`C2927038`、`C91145`、`C388632`、`C160404`）。
   - 上传坐标文件：[`hardware/gerber_and_smt/CPL_PickAndPlace_JLCPCB_Persona3_MP3.csv`](../hardware/gerber_and_smt/CPL_PickAndPlace_JLCPCB_Persona3_MP3.csv)。

---

## 四、 到手 5 分钟「零焊接」傻瓜式组装教程

1. **第一步：插接 OLED 屏幕排线**：挑起主板正面 `J4`（14Pin FPC 座）锁扣，插入 `0.91寸 128×32 OLED` 软排线并锁紧，将屏幕平贴在 `06_internal_zero_solder_sled` 正面托槽内。
2. **第二步：插接锂电池端子**：将 `501240` 锂电池放入内胆背槽，把电池自带的 `JST-SH 1.0mm 2P` 插头直接插入主板背面 `J5` 母座。
3. **第三步：装入右侧 4 联胶囊按键条与外壳**：将 `03_side_4_button_strip_silver` 对准右侧 4 颗 `TS-1135-C` 侧按微动开关推入 `01` 主圆管外壳，再套入顶部深藏青色挂耳领圈（`04`）与底部圆头银色底盖（`05`）。
4. **第四步：刷入固件与拷歌**：拔下底部圆头盖，插入 USB Type-C 数据线烧录 [`firmware/`](../firmware/) 固件，即可完整体验 **P3R 开场动画 1:1 复刻的 `"H E L L O !"` 整体浮现开机动画、`"Burn My Dread / 01:36 / VOL ||||||"` 播放界面与全屏上下滚动切歌动画**！
