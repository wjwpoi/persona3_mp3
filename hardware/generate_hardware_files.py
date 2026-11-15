#!/usr/bin/env python3
"""
Persona 3 Reload (P3R) Opening Animation MP3 Player — Rev 2.1 Official JLCPCB BOM Generator
Architecture ("Single-Side Top-Only Economic SMT Motherboard + Bottom Hand-Solder J2/J3 + 6mm Button Strip"):
- Main PCB: 99.00mm x 17.60mm (Z=21.5..120.5mm; steps to 8.0mm left finger X=-7.5..+0.5mm at Z=108..120.5mm
  for PJ-320D so USB-C plug corridor Z>108mm stays 100% open!), 2-Layer FR-4, 1.0mm Thickness, HASL (JLCPCB Top-Only Economic SMT)
- Breakaway Rear Button Strip (6.0mm x 32.0mm, 1.0mm FR-4, w/ 5mm V-cut / stamp-hole tooling rails for JLC SMT):
  mounts SW1..SW4 (TS263065A 3.0x2.6x0.65mm) at Z=38, 46, 54, 62mm in Part 06 rigid bridge pocket (Y=-8.65..-9.65mm).
- Pre-soldered by JLCPCB Top-Only Economic SMT (note: J2 TF-01A & J3 PJ-320D-SMT are placed on Bottom for compact layout & hand-soldered cleanly, saving extended-part feeder fees):
  * U2: PCM5102APWR (LCSC: C107671) - 32-Bit/384kHz TI Burr-Brown I2S Audio DAC (TSSOP-20)
  * U5: TPA6132A2RTER (LCSC: C69901) - DirectPath Stereo Headphone Amp (WQFN-16-EP, -6dB Gain G1=0 G0=0)
  * U3: TP4056 (LCSC: C16581) - 1A Li-Ion Battery Charger for 601260 420mAh Battery (ESOP-8)
  * U4: AP2112K-3.3TRG1 (LCSC: C51118) - 3.3V 600mA Low-Dropout LDO Regulator (SOT-23-5, pins 1=VIN..5=VOUT)
  * Q1, Q2, Q3: AO3401A (LCSC: C15127, Basic) - Q1: GP44 Backlight P-MOS; Q2: ~20mV Ideal-Diode Battery ORing; Q3: GP14 Peripheral Power Gate
  * D1: 1N5819WS (LCSC: C191023, Basic) - USB 5V Input Schottky Diode (D2 replaced by Q2)
  * LED1: KT-0603R (LCSC: C2286, Basic) - TP4056 CHRG Red Indicator LED
  * J4: FPC-05F-8PH20 (LCSC: C2856797) - 8-Pin 0.5mm Pitch Bottom-Contact Flip FPC Socket at Z=36..38mm
  * J2 (Bottom Hand-Solder): TF-01A (LCSC: C91145) - Push-Push MicroSD Card Slot (Z=84..99mm, opens +Z)
  * J3 (Bottom Hand-Solder): PJ-320D-SMT (LCSC: C22459515) - 3.5mm Stereo SMD Jack (Z=107.4..121.6mm, cx=-3.50mm)
  * SW1..SW4: TS263065A (LCSC: C49023761) - 3.0x2.6x0.65mm Ultra-Thin Rear Tactile Switches (8.0mm pitch)

IMPORTANT: Export your final Gerber, BOM, and Pick-and-Place (CPL) directly from EasyEDA (立创EDA) after
completing full schematic capture, copper pours, and DRC! This script generates ONLY the verified JLCPCB BOM CSV
so no misleading partial Gerbers or invalid CPL coordinates remain in the repository.
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
        "Desc": "25mW DirectPath Stereo Headphone Amplifier (-6dB Gain: G1=0, G0=0; HPVDD cap-only to PGND)",
    },
    {
        "Designator": "U3",
        "Comment": "TP4056",
        "Footprint": "ESOP-8_150mil",
        "LCSC": "C16581",
        "Desc": "Linear Li-Ion Battery Charger IC (I_CHG=364mA via R1=3.3k)",
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
        "Desc": "P-MOS (Basic): Q1=GP44 Backlight PWM, Q2=Ideal-Diode VBAT ORing (D=VBAT,S=VSYS,G=5V), Q3=GP14 3V3_PERI Gate",
    },
    {
        "Designator": "D1",
        "Comment": "1N5819WS",
        "Footprint": "SOD-323",
        "LCSC": "C191023",
        "Desc": "USB 5V Input Schottky Diode (Basic; D2 replaced by Q2 Ideal Diode)",
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
        "Desc": "Push-Push MicroSD Card Slot (Bottom Hand-Solder at Z=84..99mm, eject +Z)",
    },
    {
        "Designator": "J3",
        "Comment": "PJ-320D-SMT",
        "Footprint": "AUDIO-SMD_PJ-320D",
        "LCSC": "C22459515",
        "Desc": "3.5mm Stereo SMD Jack (Bottom Hand-Solder at Z=107.4..121.6mm, cx=-3.50mm; verify Pin4/pegs in EDA)",
    },
    {
        "Designator": "J4",
        "Comment": "FPC-05F-8PH20",
        "Footprint": "FPC-SMD_8P-P0.50",
        "LCSC": "C2856797",
        "Desc": "8-Pin 0.5mm Pitch Bottom-Contact Flip FPC Socket for 2.25in TFT (Top at Z=36..38mm)",
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
        "Comment": "3.3k",
        "Footprint": "0603",
        "LCSC": "C22978",
        "Desc": "TP4056 PROG Resistor setting safe 364mA Charge Current for 601260 420mAh (Basic)",
    },
    {
        "Designator": "R2,R3,R4,R7,R8,R12,R13,R14",
        "Comment": "10k",
        "Footprint": "0603",
        "LCSC": "C25804",
        "Desc": "10k Pulls (Basic): R2=TFT_RST->3V3_PERI, R3=TFT_CS->GND, R4=Q1_G->3V3_PERI, R7=XSMT->3V3_PERI, R8=SD_CS->3V3_PERI, R12=Q2_G->GND, R13=Q3_G->3V3_ALWAYS, R14=GP9_SCLK->3V3_PERI",
    },
    {
        "Designator": "R5,R6",
        "Comment": "470R",
        "Footprint": "0603",
        "LCSC": "C23179",
        "Desc": "PCM5102A Post-DAC RC Low-Pass Filter Series Resistors (Basic)",
    },
    {
        "Designator": "R9",
        "Comment": "10R",
        "Footprint": "0603",
        "LCSC": "C22859",
        "Desc": "TFT 4-LED Backlight Current-Limiting Resistor Q1 Drain -> LEDA (Basic; tune 4.7-10R per brightness test)",
    },
    {
        "Designator": "R10,R11",
        "Comment": "1k",
        "Footprint": "0603",
        "LCSC": "C21190",
        "Desc": "R10: GP44->Q1 Gate Damping; R11: LED1 CHRG Current Limit (Basic)",
    },
    {
        "Designator": "C1,C2,C3,C4,C12,C13,C14,C15,C23",
        "Comment": "100nF",
        "Footprint": "0603",
        "LCSC": "C14663",
        "Desc": "Decoupling 100nF 50V X7R (Basic): PCM5102(C1..C4), TP4056(C12), U4(C13), TF01A(C14), TFT(C15), TPA6132_VDD(C23)",
    },
    {
        "Designator": "C5,C6,C24,C25",
        "Comment": "4.7uF",
        "Footprint": "0603",
        "LCSC": "C19666",
        "Desc": "4.7uF 16V X5R Low-Derating Charge-Pump Caps (Basic): PCM5102 CAPP-CAPM(C5) & VNEG(C6); TPA6132 HPVDD Pin12(C24) & HPVSS Pin8(C25)",
    },
    {
        "Designator": "C7,C8,C16,C17",
        "Comment": "10uF",
        "Footprint": "0603",
        "LCSC": "C19702",
        "Desc": "Bulk Decoupling 10uF 10V X5R (Basic): VSYS(C7), 3V3_ALWAYS(C8), VBAT+(C16), USB_5V(C17)",
    },
    {
        "Designator": "C9,C10",
        "Comment": "2.2nF",
        "Footprint": "0603",
        "LCSC": "C93190",
        "Desc": "2.2nF 50V X7R (Basic): PCM5102A Post-DAC LPF Shunt Caps (154kHz fc w/ 470R)",
    },
    {
        "Designator": "C11,C18,C19,C20,C21",
        "Comment": "1uF",
        "Footprint": "0603",
        "LCSC": "C15849",
        "Desc": "1uF 50V X5R (Basic): TFT_RST POR(C11), DAC->AMP AC-Coupling INL-/INR-(C18,C19), TPA6132 CPP-CPN(C20), TPA6132 VDD(C21)",
    },
]


def generate_bom():
    bom_path = os.path.join(GERBER_DIR, "BOM_JLCPCB_Persona3_MP3.csv")
    with open(bom_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["型号", "位号", "封装", "立创商城编号"])
        for c in COMPONENTS:
            writer.writerow([c["Comment"], c["Designator"], c["Footprint"], c["LCSC"]])
    print(f"[OK] Generated Rev 2.1 JLCPCB BOM ({len(COMPONENTS)} line items): {bom_path}")


if __name__ == "__main__":
    generate_bom()
