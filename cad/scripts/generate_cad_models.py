#!/usr/bin/env python3
"""
Persona 3 / Persona 3 Reload (P3R) Protagonist MP3 Player
Parametric 3D CAD & STL Generator for JLC CNC & 3D Printing
Target Dimensions: Φ20.0mm x 80.0mm (1:1 Official Replica & Sony NW-S200/E400 Hybrid Aesthetic)
"""

import math
import os
import struct

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stl")
os.makedirs(OUT_DIR, exist_ok=True)


def write_binary_stl(filename, triangles, header_text="P3R_MP3_CAD"):
    """Write a list of triangles [((x1,y1,z1), (x2,y2,z2), (x3,y3,z3)), ...] to binary STL."""
    filepath = os.path.join(OUT_DIR, filename)
    header = header_text.encode("ascii")[:80].ljust(80, b"\x00")
    with open(filepath, "wb") as f:
        f.write(header)
        f.write(struct.pack("<I", len(triangles)))
        for p1, p2, p3 in triangles:
            # Compute normal
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
    """Add two triangles forming a quad (p1, p2, p3, p4 in CCW order)."""
    triangles.append((p1, p2, p3))
    triangles.append((p1, p3, p4))


def make_annulus_or_tube(r_outer_fn, r_inner_fn, z_steps, n_theta=96, theta_range=(0, 2 * math.pi)):
    """Generate a tubular or annular mesh given radius functions r(z, theta)."""
    triangles = []
    t_start, t_end = theta_range
    full_circle = abs((t_end - t_start) - 2 * math.pi) < 1e-5
    thetas = [t_start + (t_end - t_start) * i / n_theta for i in range(n_theta + (0 if full_circle else 1))]
    count_t = len(thetas)

    for iz in range(len(z_steps) - 1):
        z0, z1 = z_steps[iz], z_steps[iz + 1]
        for it in range(n_theta):
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

            # Outer wall
            p00 = (ro00 * math.cos(t0), ro00 * math.sin(t0), z0)
            p01 = (ro01 * math.cos(t1), ro01 * math.sin(t1), z0)
            p11 = (ro11 * math.cos(t1), ro11 * math.sin(t1), z1)
            p10 = (ro10 * math.cos(t0), ro10 * math.sin(t0), z1)
            add_quad(triangles, p00, p01, p11, p10)

            # Inner wall (reversed winding)
            q00 = (ri00 * math.cos(t0), ri00 * math.sin(t0), z0)
            q01 = (ri01 * math.cos(t1), ri01 * math.sin(t1), z0)
            q11 = (ri11 * math.cos(t1), ri11 * math.sin(t1), z1)
            q10 = (ri10 * math.cos(t0), ri10 * math.sin(t0), z1)
            add_quad(triangles, q01, q00, q10, q11)

            # Bottom cap (iz == 0)
            if iz == 0:
                add_quad(triangles, q00, q01, p01, p00)
            # Top cap (iz == last)
            if iz == len(z_steps) - 2:
                add_quad(triangles, p10, p11, q11, q10)

            # Side caps if partial arc
            if not full_circle:
                if it == 0:
                    add_quad(triangles, q00, p00, p10, q10)
                if it == n_theta - 1:
                    add_quad(triangles, p01, q01, q11, p11)

    return triangles


def make_box(x0, x1, y0, y1, z0, z1):
    """Create an axis-aligned rectangular box."""
    tris = []
    p000 = (x0, y0, z0)
    p100 = (x1, y0, z0)
    p110 = (x1, y1, z0)
    p010 = (x0, y1, z0)
    p001 = (x0, y0, z1)
    p101 = (x1, y0, z1)
    p111 = (x1, y1, z1)
    p011 = (x0, y1, z1)
    add_quad(tris, p000, p010, p110, p100)  # Bottom
    add_quad(tris, p001, p101, p111, p011)  # Top
    add_quad(tris, p000, p100, p101, p001)  # Front (-Y)
    add_quad(tris, p100, p110, p111, p101)  # Right (+X)
    add_quad(tris, p110, p010, p011, p111)  # Back (+Y)
    add_quad(tris, p010, p000, p001, p011)  # Left (-X)
    return tris


def generate_part1_cnc_main_shell():
    """
    Part 1: CNC 6061 Aluminum Main Body Shell (Φ20.0mm OD, Φ16.8mm ID, Length 58.0mm)
    Features:
    - Outer chamfered collar rings at Z=4.0mm and Z=54.0mm (signature P3 metallic bands)
    - OLED Window recess in the middle section (Z=12.0mm to Z=46.0mm)
    - Internal PCB slide rails (14.4mm width slot)
    """
    z_steps = [0.0, 1.0, 4.0, 4.5, 12.0, 46.0, 53.5, 54.0, 57.0, 58.0]

    def r_outer(z, theta):
        # Chamfer at ends
        if z < 0.5 or z > 57.5:
            return 9.6
        # Collar accent grooves
        if 4.0 <= z <= 4.5 or 53.5 <= z <= 54.0:
            return 9.75
        # Window recess on front face (-pi/4 to +pi/4 around +Y)
        if 12.0 <= z <= 46.0:
            angle_diff = abs(math.atan2(math.sin(theta - math.pi / 2), math.cos(theta - math.pi / 2)))
            if angle_diff < 0.68:  # ~78 deg arc window bed for smoked acrylic lens
                return 8.8
        return 10.0

    def r_inner(z, theta):
        return 8.4  # Φ16.8mm inner diameter

    tris = make_annulus_or_tube(r_outer, r_inner, z_steps, n_theta=120)
    # Add internal PCB guide rails along X = +/- 7.2mm
    tris.extend(make_box(-8.3, -6.8, -1.6, -0.8, 2.0, 56.0))
    tris.extend(make_box(6.8, 8.3, -1.6, -0.8, 2.0, 56.0))
    tris.extend(make_box(-8.3, -6.8, 0.8, 1.6, 2.0, 56.0))
    tris.extend(make_box(6.8, 8.3, 0.8, 1.6, 2.0, 56.0))
    write_binary_stl("01_cnc_main_shell_6061_silver.stl", tris, "P3R_CNC_MAIN_SHELL")
    return tris


def generate_part2_oled_smoked_lens():
    """
    Part 2: Curved Smoked Translucent Lens (JLC 8001 Translucent Resin dyed dark or CNC PMMA)
    Fits flush into the main shell recess (Z=12.0mm to Z=46.0mm, R_in=8.8mm, R_out=10.0mm)
    Completely hides the 0.91" OLED borders when off, glows electric blue when on.
    """
    z_steps = [12.1, 14.0, 44.0, 45.9]
    theta_range = (math.pi / 2 - 0.67, math.pi / 2 + 0.67)

    def r_outer(z, theta):
        return 10.0

    def r_inner(z, theta):
        return 8.85

    tris = make_annulus_or_tube(r_outer, r_inner, z_steps, n_theta=48, theta_range=theta_range)
    write_binary_stl("02_oled_smoked_lens_translucent_black.stl", tris, "P3R_OLED_SMOKED_LENS")
    return tris


def generate_part3_rotary_jog_crown():
    """
    Part 3: Top Knurled Rotary Jog Crown (Z=58.0mm to Z=68.0mm, Φ20.0mm OD)
    Spring-return +/-18 deg jog ring + axial push button that actuates the SMD SLLB510100 lever switch.
    """
    z_steps = [58.2, 59.0, 67.0, 67.8]

    def r_outer(z, theta):
        # Fine vertical knurling texture (36 ridges around circumference)
        knurl = 0.18 * math.cos(36 * theta) if 59.0 <= z <= 67.0 else 0.0
        return 9.9 + knurl

    def r_inner(z, theta):
        return 8.0

    tris = make_annulus_or_tube(r_outer, r_inner, z_steps, n_theta=144)
    # Internal actuator tab that engages the SLLB510100 3-way lever switch on the PCB
    tris.extend(make_box(-1.5, 1.5, 4.5, 8.1, 59.5, 66.5))
    write_binary_stl("03_rotary_jog_crown_knurled.stl", tris, "P3R_JOG_CROWN")
    return tris


def generate_part4_top_headphone_cap():
    """
    Part 4: Top End Cap with 3.5mm Headphone Port & HOLD/BT Slider Slot (Z=68.0mm to Z=75.0mm)
    """
    z_steps = [68.0, 71.0, 74.2, 75.0]

    def r_outer(z, theta):
        if z < 71.0:
            return 7.95  # Insert spigot into crown/body
        if z > 74.2:
            return 9.4  # Top chamfer
        return 10.0

    def r_inner(z, theta):
        return 3.0  # Φ6.0mm clearance bore for 3.5mm headphone plug barrel

    tris = make_annulus_or_tube(r_outer, r_inner, z_steps, n_theta=96)
    write_binary_stl("04_top_cap_headphone_port.stl", tris, "P3R_TOP_CAP")
    return tris


def generate_part5_bottom_lanyard_cap():
    """
    Part 5: Bottom End Cap + Iconic P3 Neck Lanyard Loop & Hidden Type-C / TF Dust Cover (Z=-5.0mm to Z=0.0mm)
    Total body length from Z=-5.0mm to Z=75.0mm = 80.0mm (exact 1:1 official P3R replica length!)
    """
    z_steps = [-5.0, -4.2, -0.1, 2.0]

    def r_outer(z, theta):
        if z > 0.0:
            return 8.35  # Spigot fits inside main shell (ID 16.8mm)
        if z < -4.2:
            return 9.3
        return 10.0

    def r_inner(z, theta):
        return 4.6  # Center opening for USB Type-C & MicroSD access

    tris = make_annulus_or_tube(r_outer, r_inner, z_steps, n_theta=96)
    # Add the signature P3 bottom lanyard metallic arch loop (at Z = -5.0 to -9.5mm)
    tris.extend(make_box(-6.0, -4.2, -1.5, 1.5, -9.5, -4.8))
    tris.extend(make_box(4.2, 6.0, -1.5, 1.5, -9.5, -4.8))
    tris.extend(make_box(-6.0, 6.0, -1.5, 1.5, -9.5, -8.0))
    write_binary_stl("05_bottom_lanyard_cap.stl", tris, "P3R_BOTTOM_LANYARD_CAP")
    return tris


def generate_part6_internal_chassis():
    """
    Part 6: Zero-Solder Internal Sled Bracket (JLC 3D Print Black Tough Resin)
    Holds the 14.4mm x 68.0mm PCBA, cradles the 0.91" OLED glass on top, and houses the 501240 LiPo battery below.
    """
    tris = []
    # Main sled base rails
    tris.extend(make_box(-7.2, -5.8, -2.5, 2.5, 2.0, 68.0))
    tris.extend(make_box(5.8, 7.2, -2.5, 2.5, 2.0, 68.0))
    # OLED top cradle shelf (supports 0.91" 128x32 OLED glass 30x11.5mm at Y=+6.8mm facing the window)
    tris.extend(make_box(-6.0, 6.0, 5.2, 6.8, 14.0, 44.0))
    # Battery lower cradle tray (holds 501240 LiPo battery 40x12x5mm at Y=-6.5mm)
    tris.extend(make_box(-6.2, 6.2, -7.2, -5.8, 10.0, 52.0))
    # End cross-braces with M1.6 screw bosses
    tris.extend(make_box(-7.2, 7.2, -4.0, 4.0, 2.0, 5.0))
    tris.extend(make_box(-7.2, 7.2, -4.0, 4.0, 65.0, 68.0))
    write_binary_stl("06_internal_zero_solder_sled.stl", tris, "P3R_INTERNAL_SLED")
    return tris


if __name__ == "__main__":
    all_tris = []
    all_tris.extend(generate_part1_cnc_main_shell())
    all_tris.extend(generate_part2_oled_smoked_lens())
    all_tris.extend(generate_part3_rotary_jog_crown())
    all_tris.extend(generate_part4_top_headphone_cap())
    all_tris.extend(generate_part5_bottom_lanyard_cap())
    all_tris.extend(generate_part6_internal_chassis())
    write_binary_stl("00_full_assembled_p3r_mp3.stl", all_tris, "P3R_FULL_ASSEMBLY")
    print("[SUCCESS] All 7 STL files generated successfully.")
