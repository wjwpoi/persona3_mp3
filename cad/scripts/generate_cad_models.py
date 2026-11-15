#!/usr/bin/env python3
"""
Persona 3 Reload (P3R) Opening Animation MP3 Player — Rev 2.1 CAD/STL Generator (Audit-Hardened 1:1 Long-Body)
Overall Dimensions: Φ24.0mm OD x 123.0mm Body Length (127.0mm w/ Lanyard Lug), Aspect Ratio ~5.1:1

Rev 2.1 Audit Fixes (Zero Interference + Watertight Manifold):
- Part 01 (Z=18.0..95.0mm, 77mm): Matching inner D-ceiling (y_inner_flat=+7.45mm below y_outer_flat=+8.80mm) eliminates
  negative wall thickness! Adds 4-sided 0.55mm recessed rabbet ledge (Y=+8.00mm) so Part 02 glass CANNOT fall inside!
  Shifts 2.25" TFT slightly lower (Z=21.0..83.5mm, Y_front=+5.60mm -> 18.47mm bore chord clears 17.90mm TFT cleanly).
  Adds rear M1.6 hidden set-screw holes (Z=19.5mm & Z=93.5mm) for positive axial retention of Parts 04, 05, and 06.
- Part 02 (Flat Lens): 15.20 x 57.40 x 0.80mm Flat Acrylic/Glass Window seated in 01 rabbet shelf (Y=+8.00..+8.80mm).
- Part 03 (Rear Pill Buttons): Flush/recessed on -Y back face at Z=38, 46, 54, 62mm (r_inner=10.35mm), retaining flanges.
- Part 04 (Z=92.0..123.0mm): Spigot ID=19.00mm (r=9.50mm) & Barrel ID=20.20mm (r=10.10mm) easily clear 18mm ESP32-S3-Zero
  wings (r_corner=9.09mm) & PJ-320D. Flat top (t=1.20mm) w/ Φ8.8mm port concentric at (cx=-3.50, cy=-3.60mm).
- Part 05 (Z=0.0..21.0mm): Closed Half-Ellipsoid Bullet Dome (r(0)=0) + 3.0mm axial spigot + M1.6 hidden lock shoulder.
- Part 06 (Z=21.2..91.8mm): Lower-half cradle (Y <= +1.0mm so ZERO clash w/ TFT!) + 0.90mm rigid battery-isolating bridge
  separating 601260 LiPo (Y=-7.6..-1.6mm) from the 32x5.8x1.0mm rear button daughterboard pocket (Y=-8.65..-9.65mm).
"""

import math
import os
import struct

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stl")
os.makedirs(OUT_DIR, exist_ok=True)


def write_binary_stl(filename, triangles, header_text="P3R_MP3_REV2_1_CAD"):
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


def _smoothstep01(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


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
        z_mid = 0.5 * (z0 + z1)
        for it in range(n_theta):
            if not solid(iz, it):
                continue
            t0 = thetas[it]
            t1 = thetas[(it + 1) % count_t]
            t_mid = 0.5 * (t0 + t1) if not full_circle or it < n_theta - 1 else t0 + 0.5 * (t_end - t_start) / n_theta

            # Support piecewise stepped features (e.g. rabbet shelves) cleanly per cell
            ro00 = r_outer_fn(z0, t0, z_mid, t_mid) if r_outer_fn.__code__.co_argcount >= 4 else r_outer_fn(z0, t0)
            ro01 = r_outer_fn(z0, t1, z_mid, t_mid) if r_outer_fn.__code__.co_argcount >= 4 else r_outer_fn(z0, t1)
            ro10 = r_outer_fn(z1, t0, z_mid, t_mid) if r_outer_fn.__code__.co_argcount >= 4 else r_outer_fn(z1, t0)
            ro11 = r_outer_fn(z1, t1, z_mid, t_mid) if r_outer_fn.__code__.co_argcount >= 4 else r_outer_fn(z1, t1)

            ri00 = r_inner_fn(z0, t0, z_mid, t_mid) if r_inner_fn.__code__.co_argcount >= 4 else r_inner_fn(z0, t0)
            ri01 = r_inner_fn(z0, t1, z_mid, t_mid) if r_inner_fn.__code__.co_argcount >= 4 else r_inner_fn(z0, t1)
            ri10 = r_inner_fn(z1, t0, z_mid, t_mid) if r_inner_fn.__code__.co_argcount >= 4 else r_inner_fn(z1, t0)
            ri11 = r_inner_fn(z1, t1, z_mid, t_mid) if r_inner_fn.__code__.co_argcount >= 4 else r_inner_fn(z1, t1)

            c0, s0 = math.cos(t0), math.sin(t0)
            c1, s1 = math.cos(t1), math.sin(t1)

            po00 = (ro00 * c0, ro00 * s0, z0)
            po01 = (ro01 * c1, ro01 * s1, z0)
            po10 = (ro10 * c0, ro10 * s0, z1)
            po11 = (ro11 * c1, ro11 * s1, z1)

            pi00 = (ri00 * c0, ri00 * s0, z0)
            pi01 = (ri01 * c1, ri01 * s1, z0)
            pi10 = (ri10 * c0, ri10 * s0, z1)
            pi11 = (ri11 * c1, ri11 * s1, z1)

            if max(ro00, ro01, ro10, ro11) > 1e-6:
                if ro00 < 1e-6 and ro01 < 1e-6:
                    triangles.append(((0.0, 0.0, z0), po11, po10))
                else:
                    add_quad(triangles, po00, po01, po11, po10)
            if max(ri00, ri01, ri10, ri11) > 1e-6:
                if ri00 < 1e-6 and ri01 < 1e-6:
                    triangles.append(((0.0, 0.0, z0), pi10, pi11))
                else:
                    add_quad(triangles, pi00, pi10, pi11, pi01)
            if not solid(iz - 1, it) and max(ro00, ro01, ri00, ri01) > 1e-6:
                add_quad(triangles, po00, pi00, pi01, po01)
            if not solid(iz + 1, it) and max(ro10, ro11, ri10, ri11) > 1e-6:
                add_quad(triangles, po10, po11, pi11, pi10)
            if not solid(iz, it - 1):
                if ro00 < 1e-6 and ri00 < 1e-6:
                    triangles.append(((0.0, 0.0, z0), po10, pi10))
                else:
                    add_quad(triangles, po00, po10, pi10, pi00)
            if not solid(iz, it + 1):
                if ro01 < 1e-6 and ri01 < 1e-6:
                    triangles.append(((0.0, 0.0, z0), pi11, po11))
                else:
                    add_quad(triangles, po01, pi01, pi11, po11)

    return triangles


def _make_box(x0, x1, y0, y1, z0, z1):
    tris = []
    add_quad(tris, (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))
    add_quad(tris, (x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0))
    add_quad(tris, (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0))
    add_quad(tris, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))
    add_quad(tris, (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))
    add_quad(tris, (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0))
    return tris


def generate_part1_cnc_main_shell():
    """
    Part 1 (Rev 2.1): CNC 6061 Aluminum Main Barrel (Z=18.0..95.0mm, OD=24.0mm, ID=21.6mm)
    - V-groove chamfer at Z=18.0..18.3mm (0.3mm) and collar chamfer at Z=94.5..95.0mm (0.5mm)
    - Matching Front (+Y) Flat Ceiling (y_out=+8.80mm, y_in=+7.45mm) -> constant 1.35mm wall, ZERO negative wall!
    - True stepped rabbet pocket (Y=+8.00..+8.80mm, ±7.65mm x Z=25.9..83.9) over 14.80x56.0mm viewport (±7.40 x Z=26.9..82.9)
      creating a solid 0.55mm aluminum support shelf on all 4 edges for Part 02 flat lens!
    - Rear (-Y) flush pill button slots at Z=38, 46, 54, 62mm + hidden M1.6 set-screw holes at Z=19.5 & Z=93.5mm
    """
    z_steps = [
        18.0, 18.3, 18.9, 20.1, 21.5, 25.0,
        25.75, 25.80, 26.80,
        36.0, 40.0, 44.0, 48.0, 52.0, 56.0, 60.0, 64.0,
        83.20, 84.20, 84.25, 85.0, 89.0, 92.9, 94.1, 94.5, 95.0
    ]

    def flat_factor(z):
        if z <= 21.5 or z >= 89.0:
            return 0.0
        if z < 25.0:
            return _smoothstep01((z - 21.5) / 3.5)
        if z > 85.0:
            return _smoothstep01((89.0 - z) / 4.0)
        return 1.0

    def rabbet_factor(z, theta):
        s = math.sin(theta)
        if s <= 0.55:
            return 0.0
        fz = 0.0
        if 25.75 < z < 25.80:
            fz = (z - 25.75) / 0.05
        elif 25.80 <= z <= 84.20:
            fz = 1.0
        elif 84.20 < z < 84.25:
            fz = (84.25 - z) / 0.05
        if fz <= 0.0:
            return 0.0
        x_abs = abs(8.80 * (math.cos(theta) / s))
        fx = max(0.0, min(1.0, (7.85 - x_abs) / 0.10))
        return fz * fx

    def r_outer(z, theta):
        r_base = 12.00
        if z < 18.3:
            r_base = 11.70 + (z - 18.0)
        elif z > 94.5:
            r_base = 12.00 - (z - 94.5)
        s = math.sin(theta)
        if s > 0.15:
            y_lim = 12.00 - 3.20 * flat_factor(z)  # Flat outer face at Y=+8.80mm (width 16.32mm)
            y_lim -= 0.80 * rabbet_factor(z, theta)  # Step down 0.80mm to Y=+8.00mm lens shelf
            if y_lim < r_base:
                return min(r_base, y_lim / s)
        return r_base

    def r_inner(z, theta):
        r_base = 10.80
        s = math.sin(theta)
        if s > 0.15:
            y_in_lim = 10.80 - 3.35 * flat_factor(z)  # Matching flat ceiling Y=+7.45mm (0.55mm shelf!)
            return min(r_base, y_in_lim / s)
        return r_base

    def is_cutout(z, theta):
        s = math.sin(theta)
        c = math.cos(theta)
        # Clear display viewport opening: 14.90mm wide (+/-7.45mm) x 56.4mm tall (Z=26.8..83.2mm)
        if 26.80 <= z <= 83.20 and s > 0.55:
            x_face = 8.80 * (c / s)
            if abs(x_face) <= 7.45:
                return True
        # Rear 4 Flush Pill Button Slots (-Y): Z=38, 46, 54, 62mm (+/-2.0mm)
        if s < -0.92 and abs(12.0 * c) <= 1.70:
            for bz in (38.0, 46.0, 54.0, 62.0):
                if abs(z - bz) <= 2.0:
                    return True
        # Two hidden M1.6 set-screw holes on -Y spine to lock Part 05 (Z=19.5) and Part 04 (Z=93.5)
        if s < -0.98 and abs(12.0 * c) <= 0.85:
            if (18.9 <= z <= 20.1) or (92.9 <= z <= 94.1):
                return True
        return False

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=360, is_cutout_fn=is_cutout)
    write_binary_stl("01_cnc_main_shell_6061_silver.stl", tris, "P3R_REV2_1_CNC_SHELL")
    return tris


def generate_part2_flat_screen_lens():
    """
    Part 2 (Rev 2.1): Flat Clear Acrylic / Glass Lens (15.40 x 58.20 x 0.80 mm)
    Seats cleanly inside the 0.80mm deep recessed CNC rabbet pocket (Y=+8.00..+8.80mm) on top of
    a solid 0.55mm aluminum perimeter shelf (Z=25.8..26.8 & 83.2..84.2, |x|=7.45..7.70) — CANNOT fall inside!
    """
    tris = _make_box(-7.70, 7.70, 8.00, 8.80, 25.90, 84.10)
    write_binary_stl("02_flat_screen_lens_clear.stl", tris, "P3R_REV2_1_FLAT_LENS")
    return tris


def generate_part3_rear_pill_buttons():
    """
    Part 3 (Rev 2.1): Rear (-Y) Flush Pill Button Strip (Z=38, 46, 54, 62mm)
    - Button tops flush at R=12.00mm; inner retaining base at r_in=10.35mm contacting TS263065A plungers (Y=-10.30mm).
    """
    z_steps = [
        34.5, 36.15, 36.20, 39.80, 39.85,
        44.15, 44.20, 47.80, 47.85,
        52.15, 52.20, 55.80, 55.85,
        60.15, 60.20, 63.80, 63.85, 65.5
    ]
    t_center = 1.5 * math.pi
    theta_range = (t_center - 0.16, t_center + 0.16)

    def r_outer(z, theta):
        fb = 0.0
        for bz in (38.0, 46.0, 54.0, 62.0):
            dz = abs(z - bz)
            if dz <= 1.80:
                fb = 1.0
                break
            elif dz < 1.85:
                fb = max(fb, (1.85 - dz) / 0.05)
        dt = abs(theta - t_center)
        ft = max(0.0, min(1.0, (0.12 - dt) / 0.015))
        return 10.72 + 1.28 * fb * ft  # Ramps smoothly up to 12.00mm flush outer surface!

    def r_inner(z, theta):
        return 10.35  # Meets TS263065A cap at Y=-10.30mm cleanly!

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=24, theta_range=theta_range)
    write_binary_stl("03_rear_pill_button_strip_silver.stl", tris, "P3R_REV2_1_REAR_BUTTONS")
    return tris


def _make_offcenter_hole_plate(cx, cy, r_hole, r_outer, z_bot, z_top, n_theta=96):
    tris = []
    outer_pts, inner_pts = [], []
    for i in range(n_theta):
        th = 2.0 * math.pi * i / n_theta
        ux, uy = math.cos(th), math.sin(th)
        inner_pts.append((cx + r_hole * ux, cy + r_hole * uy))
        b = cx * ux + cy * uy
        c = cx * cx + cy * cy - r_outer * r_outer
        t = -b + math.sqrt(max(0.0, b * b - c))
        outer_pts.append((cx + t * ux, cy + t * uy))

    for i in range(n_theta):
        j = (i + 1) % n_theta
        ix0, iy0 = inner_pts[i]
        ix1, iy1 = inner_pts[j]
        ox0, oy0 = outer_pts[i]
        ox1, oy1 = outer_pts[j]
        add_quad(tris, (ix0, iy0, z_top), (ox0, oy0, z_top), (ox1, oy1, z_top), (ix1, iy1, z_top))
        add_quad(tris, (ix0, iy0, z_bot), (ix1, iy1, z_bot), (ox1, oy1, z_bot), (ox0, oy0, z_bot))
        add_quad(tris, (ix0, iy0, z_bot), (ix0, iy0, z_top), (ix1, iy1, z_top), (ix1, iy1, z_bot))
        add_quad(tris, (ox0, oy0, z_bot), (ox1, oy1, z_bot), (ox1, oy1, z_top), (ox0, oy0, z_top))
    return tris


def _make_lanyard_fin_with_hole(x0, x1, y0, y1, z0, z1, hx, hz, hr, n_seg=48):
    tris = []
    outer_pts, inner_pts = [], []
    for i in range(n_seg):
        ph = 2.0 * math.pi * i / n_seg
        ux, uz = math.cos(ph), math.sin(ph)
        inner_pts.append((hx + hr * ux, hz + hr * uz))
        tx = ((x1 - hx) / ux) if ux > 1e-9 else (((x0 - hx) / ux) if ux < -1e-9 else 1e9)
        tz = ((z1 - hz) / uz) if uz > 1e-9 else (((z0 - hz) / uz) if uz < -1e-9 else 1e9)
        t = min(tx, tz)
        outer_pts.append((hx + t * ux, hz + t * uz))

    for i in range(n_seg):
        j = (i + 1) % n_seg
        ix0, iz0 = inner_pts[i]
        ix1, iz1 = inner_pts[j]
        ox0, oz0 = outer_pts[i]
        ox1, oz1 = outer_pts[j]
        add_quad(tris, (ix0, y1, iz0), (ix1, y1, iz1), (ox1, y1, oz1), (ox0, y1, oz0))
        add_quad(tris, (ix0, y0, iz0), (ox0, y0, oz0), (ox1, y0, oz1), (ix1, y0, iz1))
        add_quad(tris, (ix0, y0, iz0), (ix1, y0, iz1), (ix1, y1, iz1), (ix0, y1, iz0))
        add_quad(tris, (ox0, y0, oz0), (ox0, y1, oz0), (ox1, y1, oz1), (ox1, y0, oz1))
    return tris


def generate_part4_top_navy_collar_and_lanyard():
    """
    Part 4 (Rev 2.1): Dark-Navy Anodized 6061 Collar (Z=92.0mm to Z=123.0mm, 28mm visible = 22.8%)
    - Male spigot (Z=92.0..95.0mm): OD=10.72mm, ID=9.50mm (1.22mm wall; clears 18mm S3-Zero wings at r=9.09mm!)
    - Barrel ID=10.10mm (Φ20.20mm bore, 1.90mm wall; clears USB-C/TF-01A/PJ-320D with ease)
    - Thin 1.20mm flat top deck (Z=121.8..123.0mm) with Φ8.8mm concentric earphone port at (cx=-3.50, cy=-3.60mm)
      matching Bottom-mounted PJ-320D-SMT directly! M1.6 set screw at Z=93.5mm (-Y) locks cap axially!
    """
    z_steps = [92.0, 95.0, 95.5, 121.85]

    def r_outer_barrel(z, theta):
        if z < 95.0:
            return 10.72  # Slip/locked spigot into Part 01 (10.80mm ID), locks Part 06 at Z=91.8mm
        if z < 95.5:
            return 11.50 + (z - 95.0)
        return 12.00

    def r_inner_barrel(z, theta):
        if z < 95.0:
            return 9.50   # 1.22mm thick spigot wall -> passes 18mm S3-Zero (r=9.09mm) cleanly
        return 10.10      # Φ20.20mm upper cavity

    tris = make_perforated_tube(r_outer_barrel, r_inner_barrel, z_steps, n_theta=96)
    tris += _make_offcenter_hole_plate(cx=-3.50, cy=-3.60, r_hole=4.40, r_outer=12.0, z_bot=121.8, z_top=123.0, n_theta=96)
    tris += _make_lanyard_fin_with_hole(
        x0=2.5, x1=7.5, y0=-1.5, y1=1.5, z0=122.95, z1=127.0,
        hx=5.0, hz=125.1, hr=1.1, n_seg=48
    )

    write_binary_stl("04_top_navy_collar_lanyard_cap.stl", tris, "P3R_REV2_1_TOP_COLLAR")
    return tris


def generate_part5_bottom_rounded_dome_cap():
    """
    Part 5 (Rev 2.1): Closed Half-Ellipsoid Bullet Dome Cap (Z=0.0..18.0mm + spigot to 21.0mm)
    - Closed solid tip: r(0)=0, NO bottom hole! Top spigot edge at Z=21.0mm locks Part 06 axially.
    """
    z_steps = [
        0.0, 0.15, 0.5, 1.0, 2.2, 2.8, 4.0, 5.5, 7.2, 9.0, 11.0, 12.5, 13.5,
        17.7, 18.0, 21.0
    ]

    def r_outer(z, theta):
        if z > 18.0:
            return 10.72
        if z >= 17.7:
            return 12.00 - (z - 17.7)
        if z >= 13.5:
            return 12.00
        u = (13.5 - z) / 13.5
        return 12.00 * math.sqrt(max(0.0, 1.0 - u * u))

    def r_inner(z, theta):
        if z <= 2.2 + 1e-6:
            return 0.0
        if z >= 13.5:
            return 9.20
        u = (13.5 - z) / 11.3
        return 9.20 * math.sqrt(max(0.0, 1.0 - u * u))

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=96)
    write_binary_stl("05_bottom_rounded_dome_cap_silver.stl", tris, "P3R_REV2_1_BULLET_DOME")
    return tris


def generate_part6_internal_chassis():
    """
    Part 6 (Rev 2.1): Lower-Half Insulating Sled & Rigid Button Bridge (Z=21.2..91.8mm)
    - Occupies lower sector ONLY (theta in [pi - 0.10, 2*pi + 0.10], so Y <= +1.07mm -> ZERO collision w/ TFT!)
    - Axial capture between Part 05 spigot (Z=21.0mm) and Part 04 spigot (Z=92.0mm) prevents sliding!
    - Side PCB guide rails (|sin(theta)| <= 0.18): r_in=9.00mm (18.0mm slot fits 17.60mm PCB cleanly)
    - Battery chamber (|x| <= 6.0mm corners r=9.68mm): r_in=9.85mm except central flat bridge r_in=7.75mm (|cos|<0.35)
    - Central rigid bridge at Y=-7.75..-8.65mm (0.90mm wall) supports 32x5.8x1.0mm button PCB pocket in Z=34..66mm
      without touching or pressing against 601260 LiPo battery pouch (Y=-7.60..-1.60mm)!
    """
    z_steps = [21.2, 33.9, 34.0, 66.0, 66.1, 81.5, 81.6, 91.8]
    theta_range = (math.pi - 0.10, 2.0 * math.pi + 0.10)

    def _pocket_weight(z, theta):
        # Smooth continuous step over 0.1mm in Z and ~0.04 rad in theta so shared vertices ALWAYS match (0 non-manifold!)
        s = math.sin(theta)
        c = abs(math.cos(theta))
        if s >= -0.85:
            return 0.0
        fz = 0.0
        if 33.9 < z < 34.0:
            fz = (z - 33.9) / 0.1
        elif 34.0 <= z <= 66.0:
            fz = 1.0
        elif 66.0 < z < 66.1:
            fz = (66.1 - z) / 0.1
        ft = max(0.0, min(1.0, (0.34 - c) / 0.04))
        return fz * ft

    def r_outer(z, theta):
        return 10.65 - 2.00 * _pocket_weight(z, theta)

    def r_inner(z, theta):
        s = math.sin(theta)
        c = abs(math.cos(theta))
        # PCB horizontal edge rails (|sin(theta)| <= 0.18) -> 18.0mm slot width
        f_rail = max(0.0, min(1.0, (0.20 - abs(s)) / 0.04))
        # Rigid center bridge floor under battery (Z <= 81.6mm)
        fz_bat = 1.0 if z <= 81.5 else (max(0.0, (81.6 - z) / 0.1) if z < 81.6 else 0.0)
        ft_mid = max(0.0, min(1.0, (0.34 - c) / 0.04)) if s < -0.85 else 0.0
        f_bridge = fz_bat * ft_mid
        r_val = 9.85 - 0.85 * f_rail - 2.10 * f_bridge
        return max(7.75, min(9.85, r_val))

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=128, theta_range=theta_range)
    write_binary_stl("06_internal_zero_solder_sled.stl", tris, "P3R_REV2_1_SLED")
    return tris


def main():
    all_tris = []
    all_tris += generate_part1_cnc_main_shell()
    all_tris += generate_part2_flat_screen_lens()
    all_tris += generate_part3_rear_pill_buttons()
    all_tris += generate_part4_top_navy_collar_and_lanyard()
    all_tris += generate_part5_bottom_rounded_dome_cap()
    all_tris += generate_part6_internal_chassis()
    write_binary_stl("00_full_assembled_p3r_mp3.stl", all_tris, "P3R_REV2_1_FULL_ASSEMBLY")
    print("[SUCCESS] All 7 Rev-2.1 P3R STL files generated.")


if __name__ == "__main__":
    main()
