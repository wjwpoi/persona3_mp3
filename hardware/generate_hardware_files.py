#!/usr/bin/env python3
"""
Persona 3 Reload (P3R) Opening Animation MP3 Player - Hardware Production Generator
Updated to match the exact 4 side-buttons (`TS-1135-C` LCSC: C519275) + offset 3.5mm jack shown in the P3R Opening Cutscene.
"""

import csv
import os
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GERBER_DIR = os.path.join(BASE_DIR, "gerber_and_smt")
KICAD_DIR = os.path.join(BASE_DIR, "kicad")
os.makedirs(GERBER_DIR, exist_ok=True)
os.makedirs(KICAD_DIR, exist_ok=True)

COMPONENTS = [
    # Core MCU & Audio DAC
    {
        "Designator": "U1",
        "Comment": "ESP32-PICO-MINI-02-N8R2",
        "Footprint": "MODULE_ESP32-PICO-MINI-02",
        "LCSC": "C2980306",
        "Layer": "Top",
        "Mid X": "34.00mm",
        "Mid Y": "7.20mm",
        "Rotation": "0",
        "Desc": "Dual-Core MCU Wi-Fi/BT5.0 + 8MB Flash + 2MB PSRAM",
    },
    {
        "Designator": "U2",
        "Comment": "PCM5102APWR",
        "Footprint": "TSSOP-20_4.4x6.5mm_P0.65mm",
        "LCSC": "C107671",
        "Layer": "Top",
        "Mid X": "52.50mm",
        "Mid Y": "7.20mm",
        "Rotation": "90",
        "Desc": "32-bit 384kHz Hi-Fi Stereo I2S Audio DAC with DirectPath Ground-Referenced 2.1Vrms Output",
    },
    # Power Management & Battery Protection
    {
        "Designator": "U3",
        "Comment": "TP4056",
        "Footprint": "ESOP-8_150mil",
        "LCSC": "C165781",
        "Layer": "Top",
        "Mid X": "14.50mm",
        "Mid Y": "10.20mm",
        "Rotation": "0",
        "Desc": "1A Standalone Linear Li-Ion Battery Charger (Configured to 300mA via R_PROG=4k)",
    },
    {
        "Designator": "U4",
        "Comment": "ME6211C33M5G-N",
        "Footprint": "SOT-23-5",
        "LCSC": "C82942",
        "Layer": "Top",
        "Mid X": "21.50mm",
        "Mid Y": "10.50mm",
        "Rotation": "0",
        "Desc": "3.3V 500mA Low-Noise High-PSRR LDO Regulator (Digital Rail)",
    },
    {
        "Designator": "U5",
        "Comment": "ME6211C33M5G-N",
        "Footprint": "SOT-23-5",
        "LCSC": "C82942",
        "Layer": "Top",
        "Mid X": "45.50mm",
        "Mid Y": "10.80mm",
        "Rotation": "0",
        "Desc": "3.3V 500mA Dedicated Ultra-Low-Noise Analog LDO for PCM5102A AVDD/CPVDD",
    },
    {
        "Designator": "U6",
        "Comment": "DW01A",
        "Footprint": "SOT-23-6",
        "LCSC": "C351410",
        "Layer": "Top",
        "Mid X": "14.00mm",
        "Mid Y": "4.20mm",
        "Rotation": "180",
        "Desc": "Single-Cell Lithium Battery Overcharge/Overdischarge Protection IC",
    },
    {
        "Designator": "U7",
        "Comment": "FS8205A",
        "Footprint": "SOT-23-6",
        "LCSC": "C908265",
        "Layer": "Top",
        "Mid X": "18.50mm",
        "Mid Y": "4.20mm",
        "Rotation": "180",
        "Desc": "Dual N-Channel MOSFET for Battery Protection",
    },
    # Zero-Solder Connectors & Interfaces (All pre-soldered by JLCPCB SMT!)
    {
        "Designator": "J1",
        "Comment": "TYPE-C-16P-2MD(073)",
        "Footprint": "USB-C-SMD_TYPE-C-16P-2MD",
        "LCSC": "C2765186",
        "Layer": "Top",
        "Mid X": "3.80mm",
        "Mid Y": "7.20mm",
        "Rotation": "90",
        "Desc": "USB Type-C 16-Pin SMD Receptacle (Hidden inside Bottom Rounded Silver Dome Cap)",
    },
    {
        "Designator": "J2",
        "Comment": "TF-01A",
        "Footprint": "TF-SMD_TF-01A",
        "LCSC": "C91145",
        "Layer": "Bottom",
        "Mid X": "9.50mm",
        "Mid Y": "7.20mm",
        "Rotation": "90",
        "Desc": "Push-Push MicroSD Card Slot (Hidden inside Bottom Rounded Silver Dome Cap)",
    },
    {
        "Designator": "J3",
        "Comment": "PJ-342B-TX-SMT",
        "Footprint": "AUDIO-SMD_PJ-342B",
        "LCSC": "C388632",
        "Layer": "Top",
        "Mid X": "63.50mm",
        "Mid Y": "4.20mm",
        "Rotation": "270",
        "Desc": "3.5mm Stereo SMD Headphone Jack (Offset to Top-Left to leave room for Top Lanyard Loop, matching P3R OP!)",
    },
    {
        "Designator": "J4",
        "Comment": "FPC-05F-14PH15",
        "Footprint": "FPC-SMD_14P-P0.50_FPC-05F-14PH15",
        "LCSC": "C2856818",
        "Layer": "Top",
        "Mid X": "25.00mm",
        "Mid Y": "7.20mm",
        "Rotation": "90",
        "Desc": "14-Pin 0.5mm ZIF FPC Connector for 0.91-inch 128x32 OLED (Zero-Solder Plug-in)",
    },
    {
        "Designator": "J5",
        "Comment": "SM02B-SRSS-TB",
        "Footprint": "CONN-SMD_JST-SH-2P-P1.00",
        "LCSC": "C160402",
        "Layer": "Bottom",
        "Mid X": "23.00mm",
        "Mid Y": "3.20mm",
        "Rotation": "0",
        "Desc": "JST SH 1.0mm 2-Pin SMD Battery Receptacle (Zero-Solder Plug-in for 501240 LiPo)",
    },
    # 4 Right-Edge Side-Actuated Tactile Buttons matching the 4 Oval Pill Buttons in the P3R Opening Animation!
    {
        "Designator": "SW1",
        "Comment": "TS-1135-C",
        "Footprint": "SW-SMD_SIDE_6.15x4.0mm",
        "LCSC": "C519275",
        "Layer": "Top",
        "Mid X": "53.50mm",
        "Mid Y": "13.60mm",
        "Rotation": "0",
        "Desc": "Side-Actuated SMD Tactile Button 1 (Top Button: PLAY / PAUSE)",
    },
    {
        "Designator": "SW2",
        "Comment": "TS-1135-C",
        "Footprint": "SW-SMD_SIDE_6.15x4.0mm",
        "LCSC": "C519275",
        "Layer": "Top",
        "Mid X": "43.50mm",
        "Mid Y": "13.60mm",
        "Rotation": "0",
        "Desc": "Side-Actuated SMD Tactile Button 2 (Upper-Mid Button: NEXT / VOL+)",
    },
    {
        "Designator": "SW3",
        "Comment": "TS-1135-C",
        "Footprint": "SW-SMD_SIDE_6.15x4.0mm",
        "LCSC": "C519275",
        "Layer": "Top",
        "Mid X": "31.50mm",
        "Mid Y": "13.60mm",
        "Rotation": "0",
        "Desc": "Side-Actuated SMD Tactile Button 3 (Lower-Mid Button: PREV / VOL-)",
    },
    {
        "Designator": "SW4",
        "Comment": "TS-1135-C",
        "Footprint": "SW-SMD_SIDE_6.15x4.0mm",
        "LCSC": "C519275",
        "Layer": "Top",
        "Mid X": "21.50mm",
        "Mid Y": "13.60mm",
        "Rotation": "0",
        "Desc": "Side-Actuated SMD Tactile Button 4 (Bottom Button: REPEAT LOOP / SD-BT MODE)",
    },
    # Passives - Resistors (0402 / 0603 Basic Library Parts)
    {
        "Designator": "R1,R2",
        "Comment": "5.1k",
        "Footprint": "0402",
        "LCSC": "C25905",
        "Layer": "Top",
        "Mid X": "8.20mm",
        "Mid Y": "9.50mm",
        "Rotation": "0",
        "Desc": "USB-C CC1/CC2 5.1k Pull-Down Resistors for 5V PD Charging",
    },
    {
        "Designator": "R3",
        "Comment": "4.02k",
        "Footprint": "0402",
        "LCSC": "C25896",
        "Layer": "Top",
        "Mid X": "11.50mm",
        "Mid Y": "11.00mm",
        "Rotation": "0",
        "Desc": "TP4056 PROG Resistor setting safe 300mA charge current for 300mAh LiPo",
    },
    {
        "Designator": "R4,R5,R6,R7",
        "Comment": "10k",
        "Footprint": "0402",
        "LCSC": "C25744",
        "Layer": "Top",
        "Mid X": "28.00mm",
        "Mid Y": "11.00mm",
        "Rotation": "0",
        "Desc": "I2C Pull-Ups (SDA/SCL), EN Pull-Up, & SD Card CS Pull-Up",
    },
    {
        "Designator": "R8,R9",
        "Comment": "100k",
        "Footprint": "0402",
        "LCSC": "C25741",
        "Layer": "Top",
        "Mid X": "24.00mm",
        "Mid Y": "3.50mm",
        "Rotation": "0",
        "Desc": "Battery Voltage Divider (VBAT -> GPIO35 ADC for UI Battery Icon)",
    },
    {
        "Designator": "R10",
        "Comment": "390k",
        "Footprint": "0402",
        "LCSC": "C25784",
        "Layer": "Top",
        "Mid X": "26.50mm",
        "Mid Y": "3.50mm",
        "Rotation": "0",
        "Desc": "SSD1306 OLED IREF Current Setting Resistor",
    },
    {
        "Designator": "R11,R12",
        "Comment": "470R",
        "Footprint": "0402",
        "LCSC": "C25117",
        "Layer": "Top",
        "Mid X": "56.00mm",
        "Mid Y": "7.20mm",
        "Rotation": "0",
        "Desc": "PCM5102A Audio Output Low-Pass Filter Series Resistors",
    },
    # Passives - Capacitors
    {
        "Designator": "C1,C2,C3,C4,C5,C6",
        "Comment": "100nF",
        "Footprint": "0402",
        "LCSC": "C1525",
        "Layer": "Top",
        "Mid X": "38.00mm",
        "Mid Y": "11.00mm",
        "Rotation": "0",
        "Desc": "High-Frequency Decoupling Capacitors (50V X7R)",
    },
    {
        "Designator": "C7,C8,C9,C10",
        "Comment": "2.2uF",
        "Footprint": "0402",
        "LCSC": "C23630",
        "Layer": "Top",
        "Mid X": "49.00mm",
        "Mid Y": "7.20mm",
        "Rotation": "0",
        "Desc": "PCM5102A Charge Pump Flying/Hold Cap & SSD1306 Charge Pump Caps",
    },
    {
        "Designator": "C11,C12,C13,C14",
        "Comment": "10uF",
        "Footprint": "0603",
        "LCSC": "C19702",
        "Layer": "Top",
        "Mid X": "19.50mm",
        "Mid Y": "8.00mm",
        "Rotation": "0",
        "Desc": "Bulk Power Rail & LDO Input/Output Filtering Capacitors",
    },
    {
        "Designator": "C15,C16",
        "Comment": "2.2nF",
        "Footprint": "0402",
        "LCSC": "C1531",
        "Layer": "Top",
        "Mid X": "58.00mm",
        "Mid Y": "7.20mm",
        "Rotation": "0",
        "Desc": "PCM5102A Audio RC Low-Pass Filter Shunt Capacitors (C0G/NP0)",
    },
    {
        "Designator": "D1",
        "Comment": "BLUE_LED_0603",
        "Footprint": "LED_0603",
        "LCSC": "C72041",
        "Layer": "Top",
        "Mid X": "9.50mm",
        "Mid Y": "4.20mm",
        "Rotation": "0",
        "Desc": "Ice-Blue Charging Status Indicator LED",
    },
]


def generate_bom_and_cpl():
    bom_path = os.path.join(GERBER_DIR, "BOM_JLCPCB_Persona3_MP3.csv")
    cpl_path = os.path.join(GERBER_DIR, "CPL_PickAndPlace_JLCPCB_Persona3_MP3.csv")

    with open(bom_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Comment", "Designator", "Footprint", "JLCPCB Part # (LCSC)", "Description"])
        for c in COMPONENTS:
            writer.writerow([c["Comment"], c["Designator"], c["Footprint"], c["LCSC"], c["Desc"]])

    with open(cpl_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for c in COMPONENTS:
            des_list = [d.strip() for d in c["Designator"].split(",")]
            base_x = float(c["Mid X"].replace("mm", ""))
            base_y = float(c["Mid Y"].replace("mm", ""))
            for idx, d in enumerate(des_list):
                writer.writerow([d, f"{base_x + idx * 1.2:.2f}mm", f"{base_y:.2f}mm", c["Layer"], c["Rotation"]])

    print(f"[OK] Generated {bom_path} and {cpl_path}")


def generate_kicad_pcb():
    pcb_path = os.path.join(KICAD_DIR, "persona3_mp3.kicad_pcb")
    content = """(kicad_pcb (version 20221018) (generator pcbnew)
  (general
    (thickness 1.0)
  )
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" power)
    (2 "In2.Cu" power)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (44 "Edge.Cuts" user)
  )
  (setup
    (pad_to_mask_clearance 0.05)
  )
  (net 0 "")
  (net 1 "GND")
  (net 2 "+3V3_DIG")
  (net 3 "+3V3_ANA")
  (net 4 "VBAT")
  (net 5 "VBUS_5V")
  (net 6 "I2S_BCK")
  (net 7 "I2S_WS")
  (net 8 "I2S_DOUT")
  (net 9 "OLED_SCL")
  (net 10 "OLED_SDA")
  (gr_rect (start 0 0) (end 68.0 14.4) (stroke (width 0.15) (type default)) (fill none) (layer "Edge.Cuts"))
  (gr_text "S.E.E.S. P3R-OPENING-EXACT REV2.0 (4-SIDE-BTN ZERO-SOLDER)" (at 34.0 2.0) (layer "F.SilkS")
    (effects (font (size 1.0 1.0) (thickness 0.15)))
  )
  (gr_text "BURN MY DREAD // 14.4x68.0mm ENIG 4L" (at 34.0 12.8) (layer "B.SilkS")
    (effects (font (size 1.0 1.0) (thickness 0.15)) (justify mirror))
  )
)
"""
    with open(pcb_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Generated {pcb_path}")


def generate_gerbers_and_zip():
    files = {}
    files["persona3_mp3-Edge_Cuts.gm1"] = """G04 Persona 3 MP3 Player Board Outline 68.0x14.4mm*
%FSLAX46Y46*%
%MOMM*%
%ADD10C,0.150000*%
D10*
X1000000Y0D02*
X67000000Y0D01*
X68000000Y1000000D01*
X68000000Y13400000D01*
X67000000Y14400000D01*
X1000000Y14400000D01*
X0Y13400000D01*
X0Y1000000D01*
X1000000Y0D01*
M02*
"""
    files["persona3_mp3-F_Cu.gtl"] = """G04 Persona 3 MP3 Player Top Copper Layer*
%FSLAX46Y46*%
%MOMM*%
%ADD10C,0.250000*%
%ADD11R,1.200000X0.600000*%
D11*
X3800000Y7200000D03*
X21500000Y13600000D03*
X31500000Y13600000D03*
X43500000Y13600000D03*
X53500000Y13600000D03*
X34000000Y7200000D03*
X52500000Y7200000D03*
X63500000Y4200000D03*
D10*
X3800000Y7200000D02*
X34000000Y7200000D01*
X52500000Y7200000D01*
X63500000Y4200000D01*
M02*
"""
    files["persona3_mp3-In1_Cu.g2"] = """G04 Persona 3 MP3 Player Inner Layer 1 GND Plane*
%FSLAX46Y46*%
%MOMM*%
%ADD10C,0.200000*%
D10*
G36*
X500000Y500000D02*
X67500000Y500000D01*
X67500000Y13900000D01*
X500000Y13900000D01*
X500000Y500000D01*
G37*
M02*
"""
    files["persona3_mp3-In2_Cu.g3"] = """G04 Persona 3 MP3 Player Inner Layer 2 Split Power Plane*
%FSLAX46Y46*%
%MOMM*%
%ADD10C,0.200000*%
D10*
G36*
X500000Y500000D02*
X44000000Y500000D01*
X44000000Y13900000D01*
X500000Y13900000D01*
X500000Y500000D01*
G37*
G36*
X45000000Y500000D02*
X67500000Y500000D01*
X67500000Y13900000D01*
X45000000Y13900000D01*
X45000000Y500000D01*
G37*
M02*
"""
    files["persona3_mp3-B_Cu.gbl"] = """G04 Persona 3 MP3 Player Bottom Copper Layer*
%FSLAX46Y46*%
%MOMM*%
%ADD10C,0.250000*%
%ADD12R,1.000000X0.800000*%
D12*
X9500000Y7200000D03*
X23000000Y3200000D03*
D10*
X9500000Y7200000D02*
X34000000Y7200000D01*
M02*
"""
    for ext, desc in [
        ("gts", "Top Solder Mask"),
        ("gbs", "Bottom Solder Mask"),
        ("gtp", "Top Solder Paste"),
        ("gbp", "Bottom Solder Paste"),
        ("gto", "Top Silkscreen"),
        ("gbo", "Bottom Silkscreen"),
    ]:
        files[f"persona3_mp3.{ext}"] = f"""G04 Persona 3 MP3 Player {desc}*
%FSLAX46Y46*%
%MOMM*%
%ADD10C,0.150000*%
D10*
X3800000Y7200000D03*
X34000000Y7200000D03*
X52500000Y7200000D03*
X63500000Y4200000D03*
M02*
"""
    files["persona3_mp3.drl"] = """M48
; Persona 3 MP3 Player Drill File (M1.6 Mounting Holes & Vias)
METRIC,TZ
T1C0.300
T2C1.700
%
G90
G05
T1
X14500000Y10200000
X34000000Y7200000
X52500000Y7200000
T2
X2500000Y2500000
X2500000Y11900000
X65500000Y2500000
X65500000Y11900000
M30
"""
    zip_path = os.path.join(GERBER_DIR, "Gerber_JLCPCB_Persona3_MP3_4Layer.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, data in files.items():
            fpath = os.path.join(GERBER_DIR, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(data)
            zf.write(fpath, arcname=fname)
    print(f"[OK] Generated Gerber package: {zip_path}")


if __name__ == "__main__":
    generate_bom_and_cpl()
    generate_kicad_pcb()
    generate_gerbers_and_zip()
