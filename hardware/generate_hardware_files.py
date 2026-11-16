#!/usr/bin/env python3
"""
Persona 3 Reload (P3R) Opening Animation MP3 Player — Rev 2.4 Official JLCPCB BOM Generator
Architecture ("Single-Side Top-Only Economic SMT Motherboard w/ -X Audio Shoulder Wing + 6mm Button Strip"):
- Main PCB: 85.90mm x 17.60mm main body (Z=22.3..108.2mm) PLUS sculpted -X audio wing (X∈[-16.35,-8.80], Z=92.8..108.2mm)
  above Part 01 rim (Z=92.5mm); terminates cleanly at Z=108.2mm below ESP32-S3-Zero USB-C top edge so commercial 12.0x6.4mm
  USB-C plugs have 100% open clearance when Part 04 is removed! 2-Layer FR-4, 1.0mm Thickness, HASL (JLCPCB Top-Only SMT).
- Eliminates the separate stepped Audio Sub-Board from Rev 2.2 (3 PCBs -> 2 PCBs!):
  J3 (PJ-320D-SMT) mounts directly on Main PCB Top -X Wing (Y=-0.10..+4.90mm, Z=94.0..108.2mm, cx=-13.10, cy=+2.40mm)
  inside Part 04's sculpted -X headphone jack shoulder (`0.60..0.90mm` solder-pad clearance to centered S3-Zero), feeding
  axially (+Z) through a Phi7.40mm deck port & Phi8.70mm concave upper plug channel!
- Breakaway Rear Button Strip (6.0mm x 32.0mm, 1.0mm FR-4, bridged inside the same board outline via internal milled slots +
  stamp holes so JLCPCB bills 1 single design w/o multi-panel surcharge):
  mounts SW1..SW4 (TS263065A 3.0x2.6x0.65mm) at Z=38, 46, 54, 62mm in Part 06 orthogonal bridge pocket (Y=-8.65..-9.65mm).
- Rev 2.4 Battery Telemetry: R21/R22 470kΩ (Basic C23178) 1:1 divider + C27 100nF (Basic C14663) on VBAT -> GP15 (ADC2_CH4)
  (only 4.25uA drain, zero feeder fee); GP14 & GP15 underside access vias refined to Φ1.4mm (pad Φ2.0mm -> 0.54mm solder mask bridge at 2.54mm pitch)!
- Pre-soldered by JLCPCB Top-Only Economic SMT (note: J2 TF-01A is hand-soldered LAST on Bottom after GP14 continuity check;
  J3 PJ-320D-SMT is on Top -X Wing and can be JLCPCB SMT or hand-soldered alongside U1):
  * U2: PCM5102APWR (LCSC: C107671) - 32-Bit/384kHz TI Burr-Brown I2S Audio DAC (TSSOP-20)
  * U5: TPA6132A2RTER (LCSC: C69901) - DirectPath Stereo Headphone Amp (WQFN-16-EP, -6dB Gain G1=0 G0=0, 100ms EN soft-start)
  * U3: TP4056 (LCSC: C16581) - 1A Li-Ion Battery Charger (I_CHG=255mA via R1=4.7k for 551255 350mAh / 601260 420mAh)
  * U4: AP2112K-3.3TRG1 (LCSC: C51118) - 3.3V 600mA Low-Dropout LDO Regulator (SOT-23-5)
  * Q1, Q2, Q3: AO3401A (LCSC: C15127, Basic) - Q1: GP44 Backlight P-MOS; Q2: ~20mV Ideal-Diode Battery ORing; Q3: GP14 Power Gate
  * D1: 1N5819WS (LCSC: C191023, Basic) - USB 5V Input Schottky Diode
  * LED1: KT-0603R (LCSC: C2286, Basic) - TP4056 CHRG Red Indicator LED (USB_5V powered)
  * J4: FPC-05F-8PH20 (LCSC: C2856797) - 8-Pin 0.5mm Pitch Bottom-Contact Flip FPC Socket (Top at Z=34.0..35.5mm)
  * J2 (Bottom Hand-Solder LAST after GP14 test): TF-01A (LCSC: C91145) - Push-Push MicroSD (Z=90.8..105.6mm, eject +X above Z=92.5mm)
  * J3 (Main PCB Top -X Wing): PJ-320D-SMT (LCSC: C22459515) - 3.5mm Stereo SMD Jack (cx=-13.10, cy=+2.40mm, Z=94.0..108.2mm)
  * SW1..SW4: TS263065A (LCSC: C49023761) - 3.0x2.6x0.65mm Ultra-Thin Rear Tactile Switches

IMPORTANT: Export your final Gerber, BOM, and Pick-and-Place (CPL) directly from EasyEDA (立创EDA) after
completing full schematic capture, copper pours, and DRC! This script generates ONLY the verified JLCPCB BOM CSV.
"""

import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GERBER_DIR = os.path.join(BASE_DIR, "gerber_and_smt")
os.makedirs(GERBER_DIR, exist_ok=True)

COMPONENTS = [
    {
        "Designator": "U2",
        "Comment": "PCM5102APWR",
        "Footprint": "TSSOP-20_4.4x6.5mm_P0.65mm",
        "LCSC": "C107671",
        "Desc": "32-bit 384kHz Hi-Fi Stereo I2S Audio DAC (TI Burr-Brown, SLAS859)",
    },
    {
        "Designator": "U5",
        "Comment": "TPA6132A2RTER",
        "Footprint": "WQFN-16-EP_3.0x3.0mm_P0.50mm",
        "LCSC": "C69901",
        "Desc": "25mW DirectPath Stereo Headphone Amplifier (-6dB Gain G1=0 G0=0; EN 100ms RC soft-start via R19/C26)",
    },
    {
        "Designator": "U3",
        "Comment": "TP4056",
        "Footprint": "ESOP-8_150mil",
        "LCSC": "C16581",
        "Desc": "Linear Li-Ion Battery Charger IC (I_CHG=255mA via R1=4.7k for 551255 350mAh / 601260 420mAh)",
    },
    {
        "Designator": "U4",
        "Comment": "AP2112K-3.3TRG1",
        "Footprint": "SOT-23-5",
        "LCSC": "C51118",
        "Desc": "3.3V 600mA Low-Dropout Regulator (1=VIN, 2=GND, 3=EN, 4=NC, 5=VOUT)",
    },
    {
        "Designator": "Q1,Q2,Q3",
        "Comment": "AO3401A",
        "Footprint": "SOT-23",
        "LCSC": "C15127",
        "Desc": "P-MOS (Basic): Q1=GP44 Backlight PWM, Q2=Ideal-Diode VBAT ORing, Q3=GP14 3V3_PERI Gate",
    },
    {
        "Designator": "D1",
        "Comment": "1N5819WS",
        "Footprint": "SOD-323",
        "LCSC": "C191023",
        "Desc": "USB 5V Input Schottky Diode (Basic)",
    },
    {
        "Designator": "LED1",
        "Comment": "KT-0603R",
        "Footprint": "0603",
        "LCSC": "C2286",
        "Desc": "TP4056 Charging Red Indicator LED connected to USB_5V only (Basic)",
    },
    {
        "Designator": "J2",
        "Comment": "TF-01A",
        "Footprint": "TF-SMD_TF-01A",
        "LCSC": "C91145",
        "Desc": "Push-Push MicroSD Slot (Bottom Hand-Solder LAST at Z=90.8..105.6mm, ejects +X above Z=92.5mm)",
    },
    {
        "Designator": "J3",
        "Comment": "PJ-320D-SMT",
        "Footprint": "AUDIO-SMD_PJ-320D",
        "LCSC": "C22459515",
        "Desc": "3.5mm Stereo Jack (on Main PCB Top -X Shoulder Wing Z=94.0..108.2mm, cx=-13.10mm, cy=+2.40mm)",
    },
    {
        "Designator": "J4",
        "Comment": "FPC-05F-8PH20",
        "Footprint": "FPC-SMD_8P-P0.50",
        "LCSC": "C2856797",
        "Desc": "8-Pin 0.5mm Pitch Bottom-Contact Flip FPC Socket for 2.25in TFT (Top at Z=34.0..35.5mm)",
    },
    {
        "Designator": "SW1,SW2,SW3,SW4",
        "Comment": "TS263065A",
        "Footprint": "KEY-SMD_3.0x2.6x0.65",
        "LCSC": "C49023761",
        "Desc": "3.0x2.6x0.65mm Tactile Switches on 6.0mm-wide Breakaway Button Strip (use 5mm tooling rails for JLC SMT)",
    },
    {
        "Designator": "R1",
        "Comment": "4.7k",
        "Footprint": "0603",
        "LCSC": "C23162",
        "Desc": "TP4056 PROG Resistor setting safe 255mA Charge Current for 551255 350mAh / 601260 420mAh (Basic)",
    },
    {
        "Designator": "R2,R3,R4,R7,R8,R13,R14,R15,R16,R17,R18,R19",
        "Comment": "10k",
        "Footprint": "0603",
        "LCSC": "C25804",
        "Desc": "10k (Basic): R2=TFT_RST, R3=TFT_CS, R4=Q1_G, R7=XSMT, R8=SD_CS, R13=Q3_G->3V3_ALWAYS, R14=SCLK, R15..R18=K1..K4->3V3_ALWAYS pull-ups, R19=TPA6132_EN RC",
    },
    {
        "Designator": "R5,R6,R20",
        "Comment": "470R",
        "Footprint": "0603",
        "LCSC": "C23179",
        "Desc": "470R (Basic): R5,R6=PCM5102A Post-DAC LPF; R20=GP43(TX)->TFT_DC UART isolation",
    },
    {
        "Designator": "R9",
        "Comment": "10R",
        "Footprint": "0603",
        "LCSC": "C22859",
        "Desc": "TFT 4-LED Backlight Current-Limiting Resistor Q1 Drain -> LEDA (Basic)",
    },
    {
        "Designator": "R10,R11,R12",
        "Comment": "1k",
        "Footprint": "0603",
        "LCSC": "C21190",
        "Desc": "1k (Basic): R10=GP44->Q1_G, R11=LED1 CHRG, R12=Q2_G->GND (1ms unplug decay w/ C17=1uF)",
    },
    {
        "Designator": "R21,R22",
        "Comment": "470k",
        "Footprint": "0603",
        "LCSC": "C23178",
        "Desc": "470k (Basic): 1:1 VBAT ADC divider -> GP15 (ADC2_CH4) for real battery level telemetry (4.25uA drain)",
    },
    {
        "Designator": "C1,C2,C3,C4,C12,C13,C14,C15,C23,C27",
        "Comment": "100nF",
        "Footprint": "0603",
        "LCSC": "C14663",
        "Desc": "Decoupling 100nF 50V X7R (Basic): PCM5102(C1..C4), TP4056(C12), U4(C13), TF01A(C14), TFT(C15), TPA6132(C23), VBAT_ADC(C27)",
    },
    {
        "Designator": "C5,C6,C24,C25",
        "Comment": "4.7uF",
        "Footprint": "0603",
        "LCSC": "C19666",
        "Desc": "4.7uF 16V X5R Low-Derating Charge-Pump Caps (Basic): PCM5102(C5,C6); TPA6132 HPVDD/HPVSS(C24,C25)",
    },
    {
        "Designator": "C7,C8,C16,C22,C26",
        "Comment": "10uF",
        "Footprint": "0603",
        "LCSC": "C19702",
        "Desc": "10uF 10V X5R (Basic): VSYS(C7), 3V3_ALWAYS(C8), VBAT+ 20uF(C16,C22), TPA6132_EN 100ms soft-start(C26)",
    },
    {
        "Designator": "C9,C10",
        "Comment": "2.2nF",
        "Footprint": "0603",
        "LCSC": "C93190",
        "Desc": "2.2nF 50V X7R (Basic): PCM5102A Post-DAC LPF Shunt Caps (154kHz fc w/ 470R)",
    },
    {
        "Designator": "C11,C17,C18,C19,C20,C21",
        "Comment": "1uF",
        "Footprint": "0603",
        "LCSC": "C15849",
        "Desc": "1uF 50V X5R (Basic): TFT_RST(C11), USB_5V(C17), INL-/INR-(C18,C19), CPP-CPN(C20), TPA6132_VDD(C21)",
    },
]


def generate_bom():
    bom_path = os.path.join(GERBER_DIR, "BOM_JLCPCB_Persona3_MP3.csv")
    with open(bom_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["型号", "位号", "封装", "立创商城编号"])
        for c in COMPONENTS:
            writer.writerow([c["Comment"], c["Designator"], c["Footprint"], c["LCSC"]])
    print(f"[OK] Generated Rev 2.4 JLCPCB BOM ({len(COMPONENTS)} line items): {bom_path}")


if __name__ == "__main__":
    generate_bom()
