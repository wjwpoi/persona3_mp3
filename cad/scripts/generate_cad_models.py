#!/usr/bin/env python3
"""
Persona 3 Reload (P3R) Opening Animation MP3 Player — Rev 2.2 CAD/STL Generator (Production-Grade, Zero Interference)
Overall Dimensions: Φ24.0mm OD x 123.0mm Body Length (127.0mm w/ Lanyard Lug), Aspect Ratio ~5.1:1

Rev 2.2 Fixes:
1. Strict orthogonal Cartesian parameterization across Part 01 front flat chord (X=±7.50 viewport, ±7.78 pocket)
   and rear spine (X=±1.75 button slots, ±0.85 M1.6 holes) -> ZERO radial inward taper!
2. Crisp 0.02mm step shoulders using continuous C0 vertex-consistent functions -> ZERO cone spigots on 04 & 05,
   ZERO non-manifold edges!
3. Top split lowered to Z=92.5mm (4.0mm spigots on 04/05 w/ coaxial M1.6 holes 2.0mm from rim) so sideways TF-01A
   MicroSD card (Z_card=92.7..103.7mm) ejects cleanly above 01 rim!
4. Part 06 uses orthogonal Cartesian rear pocket (6.40mm wide X∈[-3.20,+3.20], Z∈[33.6,66.4]), flat 1.00mm thick
   battery bed/bridge at Y=-7.65mm (6.55mm headroom fits 551255 +10% swell & 601260, >=0.84mm corner walls),
   and stepped upper rail relief above Z=84.5mm clearing 18.0mm ESP32-S3-Zero completely.
5. Part 03 adds 0.15mm clearance off switch plungers (r_in=10.45mm), widened retention wings (±0.22 rad), and
   flexure relief cutouts between buttons (Z=42, 50, 58mm).
"""

import math
import os
import struct

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stl")
os.makedirs(OUT_DIR, exist_ok=True)


def write_binary_stl(filename, triangles, header_text="P3R_MP3_REV2_2_CAD"):
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


def make_conformal_shell(
    outer_xy_fn,
    inner_xy_fn,
    z_steps,
    u_steps,
    full_circle=True,
    is_cutout_fn=None,
):
    """
    Generates a watertight closed mesh by sweeping conformal cross-section nodes u_steps (CCW around +Z)
    along z_steps. Vertex coordinates MUST be continuous C0 functions of (z, u) at every shared vertex!
    """
    triangles = []
    nu = len(u_steps) - (1 if full_circle else 0)
    n_cells_u = nu if full_circle else len(u_steps) - 1
    nz = len(z_steps) - 1

    def get_u_mid(iu):
        if full_circle:
            u0 = u_steps[iu]
            u1 = u_steps[iu + 1] if iu + 1 < len(u_steps) else u_steps[-1]
            return 0.5 * (u0 + u1)
        return 0.5 * (u_steps[iu] + u_steps[iu + 1])

    def solid(iz, iu):
        if iz < 0 or iz >= nz:
            return False
        if not full_circle and (iu < 0 or iu >= n_cells_u):
            return False
        iu_mod = iu % n_cells_u
        z_mid = 0.5 * (z_steps[iz] + z_steps[iz + 1])
        u_mid = get_u_mid(iu_mod)
        if is_cutout_fn and is_cutout_fn(z_mid, u_mid):
            return False
        return True

    for iz in range(nz):
        z0, z1 = z_steps[iz], z_steps[iz + 1]
        for iu in range(n_cells_u):
            if not solid(iz, iu):
                continue
            u0 = u_steps[iu]
            u1 = u_steps[0] if (full_circle and iu == n_cells_u - 1) else u_steps[iu + 1]

            ox00, oy00 = outer_xy_fn(z0, u0)
            ox01, oy01 = outer_xy_fn(z0, u1)
            ox10, oy10 = outer_xy_fn(z1, u0)
            ox11, oy11 = outer_xy_fn(z1, u1)

            ix00, iy00 = inner_xy_fn(z0, u0)
            ix01, iy01 = inner_xy_fn(z0, u1)
            ix10, iy10 = inner_xy_fn(z1, u0)
            ix11, iy11 = inner_xy_fn(z1, u1)

            po00 = (ox00, oy00, z0)
            po01 = (ox01, oy01, z0)
            po10 = (ox10, oy10, z1)
            po11 = (ox11, oy11, z1)

            pi00 = (ix00, iy00, z0)
            pi01 = (ix01, iy01, z0)
            pi10 = (ix10, iy10, z1)
            pi11 = (ix11, iy11, z1)

            ro_max = max(math.hypot(ox00, oy00), math.hypot(ox01, oy01), math.hypot(ox10, oy10), math.hypot(ox11, oy11))
            ro_bot = max(math.hypot(ox00, oy00), math.hypot(ox01, oy01))
            ri_max = max(math.hypot(ix00, iy00), math.hypot(ix01, iy01), math.hypot(ix10, iy10), math.hypot(ix11, iy11))
            ri_bot = max(math.hypot(ix00, iy00), math.hypot(ix01, iy01))

            if ro_max > 1e-6:
                if ro_bot < 1e-6:
                    triangles.append(((0.0, 0.0, z0), po11, po10))
                else:
                    add_quad(triangles, po00, po01, po11, po10)
            if ri_max > 1e-6:
                if ri_bot < 1e-6:
                    triangles.append(((0.0, 0.0, z0), pi10, pi11))
                else:
                    add_quad(triangles, pi00, pi10, pi11, pi01)
            if not solid(iz - 1, iu) and max(ro_bot, ri_bot) > 1e-6:
                add_quad(triangles, po00, pi00, pi01, po01)
            if not solid(iz + 1, iu) and max(math.hypot(ox10, oy10), math.hypot(ox11, oy11), math.hypot(ix10, iy10), math.hypot(ix11, iy11)) > 1e-6:
                add_quad(triangles, po10, po11, pi11, pi10)
            if not solid(iz, iu - 1):
                if ro_bot < 1e-6 and ri_bot < 1e-6:
                    triangles.append(((0.0, 0.0, z0), po10, pi10))
                else:
                    add_quad(triangles, po00, po10, pi10, pi00)
            if not solid(iz, iu + 1):
                if ro_bot < 1e-6 and ri_bot < 1e-6:
                    triangles.append(((0.0, 0.0, z0), pi11, po11))
                else:
                    add_quad(triangles, po01, pi01, pi11, po11)

    return triangles


def make_perforated_tube(
    r_outer_fn,
    r_inner_fn,
    z_steps,
    n_theta=120,
    theta_range=(0.0, 2.0 * math.pi),
    is_cutout_fn=None,
):
    t_start, t_end = theta_range
    full_circle = abs((t_end - t_start) - 2.0 * math.pi) < 1e-5
    u_steps = [t_start + (t_end - t_start) * i / n_theta for i in range(n_theta + 1)]
    return make_conformal_shell(
        lambda z, t: (r_outer_fn(z, t) * math.cos(t), r_outer_fn(z, t) * math.sin(t)),
        lambda z, t: (r_inner_fn(z, t) * math.cos(t), r_inner_fn(z, t) * math.sin(t)),
        z_steps,
        u_steps,
        full_circle=full_circle,
        is_cutout_fn=is_cutout_fn,
    )


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
    Part 1 (Rev 2.2): CNC 6061 Aluminum Main Barrel (Z=18.0..92.5mm, OD=24.0mm, ID=21.40mm)
    - Orthogonal front flat chord (|x| <= 8.1584mm): exact vertical walls X=±7.50 (viewport 15.00x56.50mm)
      and X=±7.78 (rabbet pocket 15.56x58.30mm) down to 1.076mm aluminum shelf (Y=+6.924..+8.00mm).
    - Orthogonal rear spine (|x| <= 2.50mm): vertical button slots (3.50x4.00mm) & M1.6 holes (Z=20.0 & Z=90.5mm).
    """
    R_OUT = 12.00
    R_IN = 10.70
    Y_OUT_FLAT = 8.80
    X_SEAM = math.sqrt(R_OUT * R_OUT - Y_OUT_FLAT * Y_OUT_FLAT)  # 8.158431 mm
    Y_IN_FLAT = math.sqrt(R_IN * R_IN - X_SEAM * X_SEAM)         # 6.923872 mm
    T_OUT_R = math.atan2(Y_OUT_FLAT, X_SEAM)
    T_OUT_L = math.pi - T_OUT_R
    T_IN_R = math.atan2(Y_IN_FLAT, X_SEAM)
    T_IN_L = math.pi - T_IN_R
    X_SPINE = 2.50

    def x_to_u_front(x):
        return 0.25 * (X_SEAM - x) / (2.0 * X_SEAM)

    def x_to_u_rear(x):
        return 0.50 + 0.25 * (x + X_SPINE) / (2.0 * X_SPINE)

    u_front = sorted(set(
        [0.25 * i / 48 for i in range(49)] +
        [x_to_u_front(xv) for xv in (
            7.79, 7.78, 7.77, 7.51, 7.50, 7.49,
            -7.49, -7.50, -7.51, -7.77, -7.78, -7.79
        )]
    ))
    u_left = [0.25 + 0.25 * i / 36 for i in range(1, 36)]
    u_rear = sorted(set(
        [0.50 + 0.25 * i / 20 for i in range(21)] +
        [x_to_u_rear(xv) for xv in (-1.75, -0.85, 0.85, 1.75)]
    ))
    u_right = [0.75 + 0.25 * i / 36 for i in range(1, 36)]
    u_steps = u_front + u_left + u_rear + u_right + [1.0]

    z_steps = [
        18.00, 18.30, 19.15, 20.85, 21.50, 24.50,
        26.29, 26.31, 27.20,
        36.00, 40.00, 44.00, 48.00, 52.00, 56.00, 60.00, 64.00,
        83.70, 84.59, 84.61, 86.00, 89.00, 89.65, 91.35, 92.00, 92.50
    ]

    def flat_factor(z):
        if z <= 21.50 or z >= 89.00:
            return 0.0
        if z < 24.50:
            return _smoothstep01((z - 21.50) / 3.00)
        if z > 86.00:
            return _smoothstep01((89.00 - z) / 3.00)
        return 1.0

    def rabbet_factor(z, x):
        # Continuous 0.02mm step ramp in Z and 0.01mm step ramp in X -> 100% manifold C0 vertices
        if z <= 26.29 or z >= 84.61:
            return 0.0
        fz = 1.0
        if z < 26.31:
            fz = (z - 26.29) / 0.02
        elif z > 84.59:
            fz = (84.61 - z) / 0.02
        ax = abs(x)
        if ax >= 7.79:
            return 0.0
        fx = 1.0 if ax <= 7.78 else (7.79 - ax) / 0.01
        return fz * fx

    def r_outer_base(z):
        if z < 18.30:
            return 11.70 + (z - 18.00)
        if z > 92.00:
            return 12.00 - (z - 92.00)
        return 12.00

    def outer_xy(z, u):
        rb = r_outer_base(z)
        t_bot_l = math.pi + math.acos(X_SPINE / rb)
        t_bot_r = 2.0 * math.pi - math.acos(X_SPINE / rb)
        if u <= 0.25 + 1e-9:
            frac = u / 0.25
            x = X_SEAM - 2.0 * X_SEAM * frac
            t_arc = T_OUT_R + (T_OUT_L - T_OUT_R) * frac
            px_arc, py_arc = rb * math.cos(t_arc), rb * math.sin(t_arc)
            y_flat = Y_OUT_FLAT - 0.80 * rabbet_factor(z, x)
            ff = flat_factor(z)
            return ((1.0 - ff) * px_arc + ff * x, (1.0 - ff) * py_arc + ff * y_flat)
        elif u < 0.50 - 1e-9:
            f = (u - 0.25) / 0.25
            t = T_OUT_L + (t_bot_l - T_OUT_L) * f
            return (rb * math.cos(t), rb * math.sin(t))
        elif u <= 0.75 + 1e-9:
            x = -X_SPINE + 2.0 * X_SPINE * ((u - 0.50) / 0.25)
            return (x, -math.sqrt(max(0.0, rb * rb - x * x)))
        else:
            f = (u - 0.75) / 0.25
            t = t_bot_r + (2.0 * math.pi + T_OUT_R - t_bot_r) * f
            return (rb * math.cos(t), rb * math.sin(t))

    def inner_xy(z, u):
        t_bot_l = math.pi + math.acos(X_SPINE / R_IN)
        t_bot_r = 2.0 * math.pi - math.acos(X_SPINE / R_IN)
        if u <= 0.25 + 1e-9:
            frac = u / 0.25
            x = X_SEAM - 2.0 * X_SEAM * frac
            t_arc = T_IN_R + (T_IN_L - T_IN_R) * frac
            px_arc, py_arc = R_IN * math.cos(t_arc), R_IN * math.sin(t_arc)
            ff = flat_factor(z)
            return ((1.0 - ff) * px_arc + ff * x, (1.0 - ff) * py_arc + ff * Y_IN_FLAT)
        elif u < 0.50 - 1e-9:
            f = (u - 0.25) / 0.25
            t = T_IN_L + (t_bot_l - T_IN_L) * f
            return (R_IN * math.cos(t), R_IN * math.sin(t))
        elif u <= 0.75 + 1e-9:
            x = -X_SPINE + 2.0 * X_SPINE * ((u - 0.50) / 0.25)
            return (x, -math.sqrt(max(0.0, R_IN * R_IN - x * x)))
        else:
            f = (u - 0.75) / 0.25
            t = t_bot_r + (2.0 * math.pi + T_IN_R - t_bot_r) * f
            return (R_IN * math.cos(t), R_IN * math.sin(t))

    def is_cutout(z, u):
        if 27.20 <= z <= 83.70 and u <= 0.25:
            x = X_SEAM - 2.0 * X_SEAM * (u / 0.25)
            if abs(x) <= 7.50:
                return True
        if 0.50 <= u <= 0.75:
            x = -X_SPINE + 2.0 * X_SPINE * ((u - 0.50) / 0.25)
            if abs(x) <= 1.75:
                for bz in (38.0, 46.0, 54.0, 62.0):
                    if abs(z - bz) <= 2.00:
                        return True
            if abs(x) <= 0.85:
                if (19.15 <= z <= 20.85) or (89.65 <= z <= 91.35):
                    return True
        return False

    tris = make_conformal_shell(outer_xy, inner_xy, z_steps, u_steps, full_circle=True, is_cutout_fn=is_cutout)
    write_binary_stl("01_cnc_main_shell_6061_silver.stl", tris, "P3R_REV2_2_CNC_SHELL")
    return tris


def generate_part2_flat_screen_lens():
    """
    Part 2 (Rev 2.2): Flat Clear Acrylic / Glass Lens (15.44 x 58.14 x 0.80 mm)
    Seats cleanly inside the 0.80mm deep orthogonal CNC rabbet pocket (X∈[-7.78,+7.78], Z∈[26.30,84.60], Y=+8.00..+8.80mm)
    on top of a 1.08mm thick aluminum shelf around all 4 edges — ZERO interference and CANNOT fall inside!
    """
    tris = _make_box(-7.72, 7.72, 8.00, 8.80, 26.38, 84.52)
    write_binary_stl("02_flat_screen_lens_clear.stl", tris, "P3R_REV2_2_FLAT_LENS")
    return tris


def generate_part3_rear_pill_buttons():
    """
    Part 3 (Rev 2.2): Rear (-Y) Flush Pill Button Strip (Z=38, 46, 54, 62mm)
    - Base inside at r_in=10.45mm -> 0.15mm clearance from TS263065A plungers (Y=-10.30mm, zero switch preload).
    - Widened inner retention wings (±0.22 rad = ±2.30mm) prevent popping out of 01 slots (±1.75mm).
    - Central U-bridge flex-relief cutouts at Z=42, 50, 58mm isolate each pill against cross-actuation.
    """
    z_steps = [
        34.50, 36.19, 36.21, 39.79, 39.81,
        41.40, 42.60,
        44.19, 44.21, 47.79, 47.81,
        49.40, 50.60,
        52.19, 52.21, 55.79, 55.81,
        57.40, 58.60,
        60.19, 60.21, 63.79, 63.81, 65.50
    ]
    t_center = 1.5 * math.pi
    theta_range = (t_center - 0.22, t_center + 0.22)

    def r_outer(z, theta):
        fb = 0.0
        for bz in (38.0, 46.0, 54.0, 62.0):
            dz = abs(z - bz)
            if dz <= 1.79:
                fb = 1.0
                break
            elif dz < 1.81:
                fb = max(fb, (1.81 - dz) / 0.02)
        dt = abs(theta - t_center)
        ft = max(0.0, min(1.0, (0.125 - dt) / 0.015))
        return 10.62 + 1.38 * fb * ft

    def r_inner(z, theta):
        return 10.45

    def is_cutout(z_mid, t_mid):
        for sz in (42.0, 50.0, 58.0):
            if abs(z_mid - sz) <= 0.60 and abs(t_mid - t_center) <= 0.14:
                return True
        return False

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=32, theta_range=theta_range, is_cutout_fn=is_cutout)
    write_binary_stl("03_rear_pill_button_strip_silver.stl", tris, "P3R_REV2_2_REAR_BUTTONS")
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
    Part 4 (Rev 2.2): Dark-Navy Anodized 6061 Collar (Z=88.5mm to Z=123.0mm, 30.5mm visible)
    - True cylindrical 4.0mm male spigot (Z=88.5..92.49mm, OD=21.20mm, ID=19.00mm -> ZERO cone flare!)
    - Coaxial M1.6 pilot hole on -Y spine at Z=90.5mm (2.0mm below collar rim).
    - Top deck w/ Φ8.40mm earphone port at (-3.20, -4.60mm) concentric w/ Sub-Board PJ-320D-SMT!
    """
    z_steps = [88.50, 89.75, 91.25, 92.49, 92.51, 93.00, 121.85]

    def r_outer_barrel(z, theta):
        if z <= 92.49:
            return 10.60
        if z < 92.51:
            t = (z - 92.49) / 0.02
            return 10.60 + t * (11.50 - 10.60)
        if z < 93.00:
            return 11.50 + (z - 92.51) * (0.50 / 0.49)
        return 12.00

    def r_inner_barrel(z, theta):
        if z <= 92.49:
            return 9.50
        if z < 92.51:
            t = (z - 92.49) / 0.02
            return 9.50 + t * (10.10 - 9.50)
        return 10.10

    def is_cutout(z_mid, t_mid):
        if 89.75 <= z_mid <= 91.25 and math.sin(t_mid) < -0.98 and abs(9.50 * math.cos(t_mid)) <= 0.72:
            return True
        return False

    tris = make_perforated_tube(r_outer_barrel, r_inner_barrel, z_steps, n_theta=120, is_cutout_fn=is_cutout)
    tris += _make_offcenter_hole_plate(cx=-3.20, cy=-4.60, r_hole=4.20, r_outer=12.00, z_bot=121.80, z_top=123.00, n_theta=96)
    tris += _make_lanyard_fin_with_hole(
        x0=2.50, x1=7.50, y0=-1.50, y1=1.50, z0=122.95, z1=127.00,
        hx=5.00, hz=125.10, hr=1.10, n_seg=48
    )

    write_binary_stl("04_top_navy_collar_lanyard_cap.stl", tris, "P3R_REV2_2_TOP_COLLAR")
    return tris


def generate_part5_bottom_rounded_dome_cap():
    """
    Part 5 (Rev 2.2): Closed Half-Ellipsoid Bullet Dome Cap (Z=0.0..22.0mm)
    - True cylindrical 4.0mm spigot (Z=18.01..22.0mm, OD=21.20mm, ID=19.00mm -> ZERO cone flare!)
    - Coaxial M1.6 pilot hole on -Y spine at Z=20.0mm (2.0mm from rim at Z=18.0mm).
    """
    z_steps = [
        0.00, 0.15, 0.50, 1.00, 2.20, 2.80, 4.00, 5.50, 7.20, 9.00, 11.00, 12.50, 13.50,
        17.70, 17.99, 18.01, 19.25, 20.75, 22.00
    ]

    def r_outer(z, theta):
        if z >= 18.01:
            return 10.60
        if z > 17.99:
            t = (z - 17.99) / 0.02
            return 11.71 + t * (10.60 - 11.71)
        if z >= 17.70:
            return 12.00 - (z - 17.70)
        if z >= 13.50:
            return 12.00
        u = (13.50 - z) / 13.50
        return 12.00 * math.sqrt(max(0.0, 1.0 - u * u))

    def r_inner(z, theta):
        if z <= 2.20 + 1e-6:
            return 0.0
        if z >= 13.50:
            return 9.50
        u = (13.50 - z) / 11.30
        return 9.50 * math.sqrt(max(0.0, 1.0 - u * u))

    def is_cutout(z_mid, t_mid):
        if 19.25 <= z_mid <= 20.75 and math.sin(t_mid) < -0.98 and abs(9.50 * math.cos(t_mid)) <= 0.72:
            return True
        return False

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=120, is_cutout_fn=is_cutout)
    write_binary_stl("05_bottom_rounded_dome_cap_silver.stl", tris, "P3R_REV2_2_BULLET_DOME")
    return tris


def generate_part6_internal_chassis():
    """
    Part 6 (Rev 2.2): Orthogonal Insulating Sled & Rigid Button Bridge (Z=22.2..88.3mm)
    - Stepped top arm cutout above Z=84.5mm keeps Y <= -0.15mm -> ZERO collision w/ 18.0mm ESP32-S3-Zero!
    - Orthogonal Cartesian rear button slot (6.40mm wide: X∈[-3.20,+3.20], Y∈[-9.65,-8.65], Z∈[33.6,66.4])
      and dead-flat 1.00mm bridge/battery bed (Y=-7.65..-8.65mm) -> fits 551255 +10% swell & 601260 cleanly!
    """
    R_SLED_OUT = 10.62
    R_BAT_CHAMBER = 9.85
    Y_BAT_FLOOR = -7.65
    Y_BTN_ROOF = -8.65
    X_FLAT_HALF = math.sqrt(R_BAT_CHAMBER * R_BAT_CHAMBER - Y_BAT_FLOOR * Y_BAT_FLOOR)  # 6.204837 mm

    T_ARM_L = math.pi - 0.10
    T_ARM_R = 2.0 * math.pi + 0.10
    T_RELIEF_L = math.pi + math.asin(0.15 / R_SLED_OUT)
    T_RELIEF_R = 2.0 * math.pi - math.asin(0.15 / R_SLED_OUT)

    T_OUT_FLAT_L = math.pi + math.acos(X_FLAT_HALF / R_SLED_OUT)
    T_OUT_FLAT_R = 2.0 * math.pi - math.acos(X_FLAT_HALF / R_SLED_OUT)
    T_IN_FLAT_L = math.pi + math.acos(X_FLAT_HALF / R_BAT_CHAMBER)
    T_IN_FLAT_R = 2.0 * math.pi - math.acos(X_FLAT_HALF / R_BAT_CHAMBER)

    U_RELIEF_L = 0.30 * (T_RELIEF_L - T_ARM_L) / (T_IN_FLAT_L - T_ARM_L)
    U_RELIEF_R = 0.70 + 0.30 * (T_RELIEF_R - T_IN_FLAT_R) / (T_ARM_R - T_IN_FLAT_R)

    def x_to_u_bed(x):
        return 0.30 + 0.40 * (x + X_FLAT_HALF) / (2.0 * X_FLAT_HALF)

    raw_u = (
        [0.30 * i / 28 for i in range(29)]
        + [U_RELIEF_L, U_RELIEF_R]
        + [0.30 + 0.40 * i / 36 for i in range(1, 37)]
        + [x_to_u_bed(xv) for xv in (-3.21, -3.20, -3.19, 3.19, 3.20, 3.21)]
        + [0.70 + 0.30 * i / 28 for i in range(1, 29)]
    )
    u_steps = []
    for uv in sorted(raw_u):
        if not u_steps or abs(uv - u_steps[-1]) > 1e-6:
            u_steps.append(uv)

    z_steps = [22.20, 33.59, 33.61, 66.39, 66.41, 81.50, 84.50, 88.30]

    def pocket_factor(z, x):
        if z <= 33.59 or z >= 66.41:
            return 0.0
        fz = 1.0
        if z < 33.61:
            fz = (z - 33.59) / 0.02
        elif z > 66.39:
            fz = (66.41 - z) / 0.02
        ax = abs(x)
        if ax >= 3.21:
            return 0.0
        fx = 1.0 if ax <= 3.20 else (3.21 - ax) / 0.01
        return fz * fx

    def outer_xy(z, u):
        if u < 0.30 - 1e-9:
            t = T_ARM_L + (T_OUT_FLAT_L - T_ARM_L) * (u / 0.30)
            return (R_SLED_OUT * math.cos(t), R_SLED_OUT * math.sin(t))
        elif u <= 0.70 + 1e-9:
            x = -X_FLAT_HALF + 2.0 * X_FLAT_HALF * ((u - 0.30) / 0.40)
            y_circ = -math.sqrt(max(0.0, R_SLED_OUT * R_SLED_OUT - x * x))
            pf = pocket_factor(z, x)
            return (x, (1.0 - pf) * y_circ + pf * Y_BTN_ROOF)
        else:
            t = T_OUT_FLAT_R + (T_ARM_R - T_OUT_FLAT_R) * ((u - 0.70) / 0.30)
            return (R_SLED_OUT * math.cos(t), R_SLED_OUT * math.sin(t))

    def inner_xy(z, u):
        if u < 0.30 - 1e-9:
            t = T_ARM_L + (T_IN_FLAT_L - T_ARM_L) * (u / 0.30)
            f_rail = max(0.0, min(1.0, (0.18 - abs(math.sin(t))) / 0.04))
            ri = R_BAT_CHAMBER - 0.85 * f_rail
            return (ri * math.cos(t), ri * math.sin(t))
        elif u <= 0.70 + 1e-9:
            x = -X_FLAT_HALF + 2.0 * X_FLAT_HALF * ((u - 0.30) / 0.40)
            return (x, Y_BAT_FLOOR)
        else:
            t = T_IN_FLAT_R + (T_ARM_R - T_IN_FLAT_R) * ((u - 0.70) / 0.30)
            f_rail = max(0.0, min(1.0, (0.18 - abs(math.sin(t))) / 0.04))
            ri = R_BAT_CHAMBER - 0.85 * f_rail
            return (ri * math.cos(t), ri * math.sin(t))

    def is_cutout(z_mid, u_mid):
        if z_mid > 84.50 and (u_mid < U_RELIEF_L or u_mid > U_RELIEF_R):
            return True
        return False

    tris = make_conformal_shell(outer_xy, inner_xy, z_steps, u_steps, full_circle=False, is_cutout_fn=is_cutout)
    write_binary_stl("06_internal_zero_solder_sled.stl", tris, "P3R_REV2_2_SLED")
    return tris


def main():
    all_tris = []
    all_tris += generate_part1_cnc_main_shell()
    all_tris += generate_part2_flat_screen_lens()
    all_tris += generate_part3_rear_pill_buttons()
    all_tris += generate_part4_top_navy_collar_and_lanyard()
    all_tris += generate_part5_bottom_rounded_dome_cap()
    all_tris += generate_part6_internal_chassis()
    write_binary_stl("00_full_assembled_p3r_mp3.stl", all_tris, "P3R_REV2_2_FULL_ASSEMBLY")
    print("[SUCCESS] All 7 Rev-2.2 P3R STL files generated.")


if __name__ == "__main__":
    main()
