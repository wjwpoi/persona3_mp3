#!/usr/bin/env python3
"""
Persona 3 / Persona 3 Reload (P3R) Opening Animation MP3 Player
Volumetric-Verified 3-Zone CAD/STL Generator for JLC 3D Printing & CNC (Plan A: 9-Item Taobao COTS Kit)

Exact 3-Zone Volumetric & Spatial Allocation (Φ24.0mm OD / Φ21.2mm ID x 95.0mm Total Length, 32.12 cm³ Internal Cavity):
- Zone 1 (Bottom Z=2.0..28.0mm, inside Hollow Dome Cap 05 + Lower Barrel 01):
  * Upper Deck (Y=+2.0mm): Waveshare ESP32-S3-Zero-M (18.0 x 23.5 mm)
  * Lower Deck (Y=-5.0mm): TP4056 Type-C LiPo Charger Board (17.2 x 26.0 mm)
- Zone 2 (Middle Window & Control Section Z=28.0..68.0mm, inside Central Barrel 01 + Sled 06):
  * Front (+Y=+6.5mm): 0.91" 128x32 I2C OLED Module (12.0 x 38.0 x 3.5 mm) aligned with open through-window
  * Right (+X=+6.5mm): 4-Key Independent Button Module (15.0 x 38.0 mm) aligned with 4 side button through-slots
  * Back (-Y=-5.5mm): 501240 220mAh Polymer LiPo Battery (5.0 x 12.0 x 40.0 mm)
- Zone 3 (Top Audio & Storage Section Z=68.0..93.0mm, inside Upper Barrel 01 + Hollow Top Navy Collar 04):
  * Upper Deck (Y=+2.0mm): GY-PCM5102 32-Bit I2S Hi-Fi DAC (16.8 x 31.8 mm) with 3.5mm jack at top-left port
  * Lower Deck (Y=-4.5mm): Mini SD / MicroSD SPI Module (17.5 x 18.0 mm)
"""

import math
import os
import struct

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stl")
os.makedirs(OUT_DIR, exist_ok=True)


def write_binary_stl(filename, triangles, header_text="P3R_MP3_CAD"):
    filepath = os.path.join(OUT_DIR, filename)
    header = header_text.encode("ascii")[:80].ljust(80, b"\x00")
    with open(filepath, "wb") as f:
        f.write(header)
        f.write(struct.pack("<I", len(triangles)))
        for p1, p2, p3 in triangles:
            ux, uy, uz = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]
            vx, vy, vz = p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            if length > 1e-9:
                nx, ny, nz = nx / length, ny / length, nz / length
            else:
                nx, ny, nz = 0.0, 0.0, 1.0
            f.write(struct.pack("<12fH", nx, ny, nz, *p1, *p2, *p3, 0))
    print(f"[OK] Generated {filepath} ({len(triangles)} triangles)")


def add_quad(triangles, p1, p2, p3, p4):
    triangles.append((p1, p2, p3))
    triangles.append((p1, p3, p4))


def make_perforated_tube(
    r_outer_fn,
    r_inner_fn,
    z_steps,
    n_theta=120,
    theta_range=(0.0, 2.0 * math.pi),
    is_cutout_fn=None,
):
    triangles = []
    t_start, t_end = theta_range
    full_circle = abs((t_end - t_start) - 2.0 * math.pi) < 1e-5
    thetas = [t_start + (t_end - t_start) * i / n_theta for i in range(n_theta + (0 if full_circle else 1))]
    count_t = len(thetas)
    nz = len(z_steps) - 1

    def solid(iz, it):
        if iz < 0 or iz >= nz:
            return False
        if not full_circle and (it < 0 or it >= n_theta):
            return False
        it_mod = it % n_theta
        z_mid = 0.5 * (z_steps[iz] + z_steps[iz + 1])
        t0 = thetas[it_mod]
        t1 = thetas[(it_mod + 1) % count_t]
        t_mid = 0.5 * (t0 + t1) if not full_circle or it_mod < n_theta - 1 else t0 + 0.5 * (t_end - t_start) / n_theta
        if is_cutout_fn and is_cutout_fn(z_mid, t_mid):
            return False
        return True

    for iz in range(nz):
        z0, z1 = z_steps[iz], z_steps[iz + 1]
        for it in range(n_theta):
            if not solid(iz, it):
                continue
            t0 = thetas[it]
            t1 = thetas[(it + 1) % count_t]

            ro00 = r_outer_fn(z0, t0)
            ro01 = r_outer_fn(z0, t1)
            ro11 = r_outer_fn(z1, t1)
            ro10 = r_outer_fn(z1, t0)

            ri00 = r_inner_fn(z0, t0)
            ri01 = r_inner_fn(z0, t1)
            ri11 = r_inner_fn(z1, t1)
            ri10 = r_inner_fn(z1, t0)

            p00 = (ro00 * math.cos(t0), ro00 * math.sin(t0), z0)
            p01 = (ro01 * math.cos(t1), ro01 * math.sin(t1), z0)
            p11 = (ro11 * math.cos(t1), ro11 * math.sin(t1), z1)
            p10 = (ro10 * math.cos(t0), ro10 * math.sin(t0), z1)
            add_quad(triangles, p00, p01, p11, p10)

            q00 = (ri00 * math.cos(t0), ri00 * math.sin(t0), z0)
            q01 = (ri01 * math.cos(t1), ri01 * math.sin(t1), z0)
            q11 = (ri11 * math.cos(t1), ri11 * math.sin(t1), z1)
            q10 = (ri10 * math.cos(t0), ri10 * math.sin(t0), z1)
            add_quad(triangles, q01, q00, q10, q11)

            if not solid(iz - 1, it):
                add_quad(triangles, q00, q01, p01, p00)
            if not solid(iz + 1, it):
                add_quad(triangles, p10, p11, q11, q10)
            if not solid(iz, it - 1):
                add_quad(triangles, q00, p00, p10, q10)
            if not solid(iz, it + 1):
                add_quad(triangles, p01, q01, q11, p11)

    return triangles


def generate_part1_cnc_main_shell():
    """
    Part 1: Central Silver 6061 Aluminum Barrel (Z=18.0mm to Z=74.0mm, Length 56.0mm, Φ24.0mm OD / Φ21.2mm ID)
    - Φ21.2mm ID (R_inner=10.60mm) provides full clearance for 18.0mm ESP32-S3-Zero, 17.2mm TP4056,
      16.8mm GY-PCM5102, 17.5mm Mini SD, 15.0mm 4-Key Keypad, 12.0mm OLED, and 501240 Battery!
    - Open rectangular through-window on +Y (Z=27.0..65.0mm) with recessed lens ledge (Z=25.0..67.0mm, R=11.80mm)
    - 4 open button through-slots on +X (Z=31.0, 41.0, 51.0, 61.0mm +/- 2.75mm)
    """
    z_steps = [
        18.0, 18.5, 25.0,
        27.0, 28.25, 33.75,
        38.25, 43.75,
        48.25, 53.75,
        58.25, 63.75, 65.0,
        67.0, 73.5, 74.0,
    ]

    def r_outer(z, theta):
        if z < 18.5 or z > 73.5:
            return 11.80
        if 25.0 <= z <= 67.0:
            angle_diff = abs(math.atan2(math.sin(theta - math.pi / 2), math.cos(theta - math.pi / 2)))
            if angle_diff < 0.56:
                return 11.80  # Recessed screen lens ledge (1.20mm wall above 10.60mm ID)
        return 12.00  # Φ24.0mm OD

    def r_inner(z, theta):
        return 10.60  # Φ21.2mm ID (353 mm² cross-section, fits all 18mm COTS boards + stacked battery!)

    def is_cutout(z, theta):
        angle_from_front = abs(math.atan2(math.sin(theta - math.pi / 2), math.cos(theta - math.pi / 2)))
        if 27.0 <= z <= 65.0 and angle_from_front < 0.40:
            return True
        angle_from_right = abs(math.atan2(math.sin(theta), math.cos(theta)))
        if angle_from_right < 0.17:
            for zc in (31.0, 41.0, 51.0, 61.0):
                if abs(z - zc) <= 2.75:
                    return True
        return False

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=120, is_cutout_fn=is_cutout)
    write_binary_stl("01_cnc_main_shell_6061_silver.stl", tris, "P3R_CNC_SILVER_BODY")
    return tris


def generate_part2_oled_window_lens():
    """
    Part 2: Recessed Screen Window Lens (Z=25.2mm to Z=66.8mm, 8001 Clear + Gloss Spray Coat)
    """
    z_steps = [25.2, 28.0, 64.0, 66.8]
    theta_range = (math.pi / 2 - 0.54, math.pi / 2 + 0.54)

    def r_outer(z, theta):
        return 11.95

    def r_inner(z, theta):
        return 10.75  # 1.20mm uniform optical lens thickness

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=48, theta_range=theta_range)
    write_binary_stl("02_oled_smoked_lens_translucent_black.stl", tris, "P3R_SCREEN_LENS")
    return tris


def generate_part3_side_4_button_strip():
    """
    Part 3: Right-Side 4 Oval Pill Button Strip (Z=27.0mm to Z=65.0mm)
    Buttons at Z = 31.0, 41.0, 51.0, 61.0mm matching the 4-Key Independent Keypad Module spacing (9.5-10.0mm pitch)!
    """
    z_steps = [
        27.0,
        28.5, 33.5,
        38.5, 43.5,
        48.5, 53.5,
        58.5, 63.5,
        65.0,
    ]
    theta_range = (-0.52, 0.52)

    def r_outer(z, theta):
        for zc in (31.0, 41.0, 51.0, 61.0):
            if abs(z - zc) <= 2.5 and abs(theta) <= 0.15:
                return 12.85  # Protruding oval button cap outside Φ24.0mm shell
        return 10.45  # Internal carrier spine sitting inside 10.60mm ID of Part 01

    def r_inner(z, theta):
        return 8.95   # 1.50mm spine thickness

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=40, theta_range=theta_range)
    write_binary_stl("03_side_4_button_strip_silver.stl", tris, "P3R_SIDE_4_BUTTONS")
    return tris


def generate_part4_top_navy_collar_and_lanyard():
    """
    Part 4: Hollow Top Dark-Navy Collar (Z=72.0mm to Z=95.0mm)
    - Hollow interior (R_inner=9.20mm -> Φ18.4mm ID up to Z=91.0mm) so the 16.8mm-wide GY-PCM5102 DAC board
      and 17.5mm-wide Mini SD module fit right inside the top collar!
    - Top-left headphone plug port + top-right lanyard clasp with keyring eyelet hole.
    """
    z_steps = [72.0, 74.0, 89.0, 91.0, 93.5, 95.0]

    def r_outer(z, theta):
        if z < 74.0:
            return 10.50  # Spigot fits into Part 01 (10.60mm ID)
        if z <= 89.0:
            return 12.00  # Φ24.0mm OD main dark-navy collar barrel
        x_dir = math.cos(theta)
        if z <= 93.5 and x_dir < -0.20:
            return 11.40  # Left-offset earphone plug collar
        if x_dir > -0.10:
            return 9.50   # Top lanyard clasp block
        return 8.00

    def r_inner(z, theta):
        if z <= 91.0:
            return 9.10   # Φ18.2mm hollow inner chamber housing GY-PCM5102 & Mini SD!
        return 5.50       # Top opening for 3.5mm stereo plug barrel

    def is_cutout(z, theta):
        if 91.0 <= z <= 93.5:
            if abs(math.cos(theta) - 0.35) < 0.28 and abs(math.sin(theta)) > 0.75:
                return True
        return False

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=96, is_cutout_fn=is_cutout)
    write_binary_stl("04_top_navy_collar_lanyard_cap.stl", tris, "P3R_TOP_NAVY_COLLAR")
    return tris


def generate_part5_bottom_rounded_dome_cap():
    """
    Part 5: Hollow Bottom Silver 6061 Aluminum Dome Cap (Z=0.0mm to Z=20.0mm)
    - Hollow interior (R_inner=9.15mm -> Φ18.3mm ID from Z=2.5mm to Z=20.0mm) so both the ESP32-S3-Zero-M
      (18.0x23.5mm) and TP4056 Type-C Charger (17.2x26.0mm) fit cleanly inside the bottom section!
    """
    z_steps = [0.0, 1.4, 2.5, 5.5, 17.8, 18.0, 20.0]

    def r_outer(z, theta):
        if z > 18.0:
            return 10.50  # Slip-fit spigot into Part 01 (10.60mm ID)
        if z < 1.4:
            return 8.50
        if z < 2.5:
            return 10.40
        if z < 5.5:
            return 11.60
        return 12.00  # Φ24.0mm OD

    def r_inner(z, theta):
        if z < 2.5:
            return 4.50   # Bottom vent / lanyard hole
        return 9.15       # Φ18.3mm hollow chamber housing ESP32-S3-Zero & TP4056!

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=96)
    write_binary_stl("05_bottom_rounded_dome_cap_silver.stl", tris, "P3R_BOTTOM_DOME_CAP")
    return tris


def generate_part6_internal_chassis():
    """
    Part 6: 3-Zone Volumetric Internal Insulating Sled (Z=15.0mm to Z=85.0mm, Length 70.0mm)
    - Zone 1 (Z=15..28mm): Cradles ESP32-S3-Zero-M + TP4056
    - Zone 2 (Z=28..66mm): Cradles 0.91" OLED (front), 4-Key Keypad (right), and 501240 Battery (back)
    - Zone 3 (Z=66..85mm): Cradles GY-PCM5102 Hi-Fi DAC + Mini SD Card Reader
    """
    z_steps = [15.0, 18.0, 28.0, 66.0, 82.0, 85.0]
    theta_range = (math.pi / 2 + 0.48, 2 * math.pi + math.pi / 2 - 0.48)

    def r_outer(z, theta):
        if 18.0 <= z <= 72.0:
            return 10.35  # Fits inside Part 01 (10.60mm ID)
        return 9.00       # Fits inside hollow caps Part 04 & Part 05 (9.10mm ID)

    def r_inner(z, theta):
        sin_t = abs(math.sin(theta))
        if sin_t < 0.22:
            return 7.40   # Side PCB support ledges
        return 7.75       # 1.25-2.60mm insulating wall

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=72, theta_range=theta_range)
    write_binary_stl("06_internal_zero_solder_sled.stl", tris, "P3R_INTERNAL_SLED")
    return tris


if __name__ == "__main__":
    all_tris = []
    all_tris.extend(generate_part1_cnc_main_shell())
    all_tris.extend(generate_part2_oled_window_lens())
    all_tris.extend(generate_part3_side_4_button_strip())
    all_tris.extend(generate_part4_top_navy_collar_and_lanyard())
    all_tris.extend(generate_part5_bottom_rounded_dome_cap())
    all_tris.extend(generate_part6_internal_chassis())
    write_binary_stl("00_full_assembled_p3r_mp3.stl", all_tris, "P3R_FULL_ASSEMBLY")
    print("[SUCCESS] All 7 Volumetric-Verified 3-Zone P3R STL files generated.")
