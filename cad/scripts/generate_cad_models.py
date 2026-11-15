#!/usr/bin/env python3
"""
Persona 3 Reload (P3R) Opening Animation MP3 Player — Rev 2 CAD/STL Generator (1:1 Anime Long-Body)
Overall Dimensions: Φ24.0mm OD x 123.0mm Body Length (127.0mm w/ Lanyard Lug), Aspect Ratio ~5.1:1

Rev 2 Upgrades (per p3r_mp3_cad_review.md):
- Part 01 (Z=18.0..95.0mm, 77mm): Φ24mm CNC 6061 Aluminum with Front (+Y=9.5mm) D-Cut Flat Face + 14.8x57mm Window
  for 2.25" 76x284 ST7789P3 Bar IPS TFT (17.90x62.50x2.36mm, AA 14.80x55.30mm), plus Rear (-Y) flush pill button slots.
- Part 02 (Flat Lens): 14.70 x 56.80 x 1.00mm Flat Clear Acrylic/Glass Window flush with D-Cut face (+Y=9.5mm).
- Part 03 (Rear Pill Buttons): Flush/recessed on -Y back face so front/side silhouettes stay 100% clean.
- Part 04 (Z=95.0..123.0mm, 28mm): Dark-Navy Anodized 6061 Collar, 0.5mm seam chamfer, flat top, recessed 3.5mm
  earphone port (no protrusion), and compact 5x3x4mm lanyard lug.
- Part 05 (Z=0.0..18.0mm): Closed Half-Ellipsoid Bullet Dome (r(0)=0, NO bottom hole) + 0.3mm V-groove seam chamfer.
- Part 06 (Z=21.5..91.5mm, 70mm): Internal Insulating Sled cradling 2.25" TFT + Rev2 PCB + 601260 (420mAh) LiPo Battery.
"""

import math
import os
import struct

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stl")
os.makedirs(OUT_DIR, exist_ok=True)


def write_binary_stl(filename, triangles, header_text="P3R_MP3_REV2_CAD"):
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
            ro10 = r_outer_fn(z1, t0)
            ro11 = r_outer_fn(z1, t1)

            ri00 = r_inner_fn(z0, t0)
            ri01 = r_inner_fn(z0, t1)
            ri10 = r_inner_fn(z1, t0)
            ri11 = r_inner_fn(z1, t1)

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
    Part 1: CNC 6061 Aluminum Main Barrel (Z=18.0mm to Z=95.0mm, Length 77.0mm, OD=24.0mm, ID=21.6mm)
    - V-groove chamfer at Z=18.0..18.3mm (0.3mm x 45 deg) and collar chamfer at Z=94.5..95.0mm (0.5mm x 45 deg)
    - Front (+Y=9.50mm) D-Cut Flat Face (Z=23.0..90.0mm) with smooth end transitions
    - Screen window opening: 14.80mm wide x 57.0mm tall (Z=28.0..85.0mm) for 2.25" 76x284 TFT
    - Rear (-Y) flush pill button slots at Z=36, 46, 56, 66mm
    """
    z_steps = [
        18.0, 18.3, 23.0, 24.5, 26.0, 27.0, 28.0,
        44.0, 48.0, 52.0, 56.0, 60.0, 64.0, 68.0, 72.0,
        85.0, 86.0, 87.5, 89.0, 90.0, 94.5, 95.0
    ]

    def y_flat_limit(z):
        if z <= 23.0 or z >= 90.0:
            return 12.00
        if z < 27.0:
            t = (z - 23.0) / 4.0
            # Smooth ease into flat Y=9.10 (15.64mm flat width -> 0.42mm bezel beside 14.8mm window)
            return 12.00 - 2.90 * (t * t * (3.0 - 2.0 * t))
        if z > 86.0:
            t = (90.0 - z) / 4.0
            return 12.00 - 2.90 * (t * t * (3.0 - 2.0 * t))
        return 9.10

    def r_outer(z, theta):
        r_base = 12.00
        if z < 18.3:
            r_base = 11.70 + (z - 18.0)
        elif z > 94.5:
            r_base = 12.00 - (z - 94.5)
        s = math.sin(theta)
        if s > 0.15:
            y_lim = y_flat_limit(z)
            if y_lim < r_base:
                return min(r_base, y_lim / s)
        return r_base

    def r_inner(z, theta):
        return 10.80  # Φ21.6mm ID -> chord width 18.22mm at y=+5.8mm (clears 17.90mm TFT!)

    def is_cutout(z, theta):
        s = math.sin(theta)
        c = math.cos(theta)
        # Front Screen Window (+Y): 14.80mm wide x 57.0mm tall (Z=28.0..85.0) on Y=9.10 flat face
        if 28.0 <= z <= 85.0 and s > 0.60:
            x_at_face = 9.10 * (c / s)
            if abs(x_at_face) <= 7.40:
                return True
        # Rear 4 Flush Pill Button Slots (-Y): Z=46, 54, 62, 70 (+/- 2.0mm) aligned with PCB X=34,42,50,58
        if s < -0.92 and abs(12.0 * c) <= 1.60:
            for bz in (46.0, 54.0, 62.0, 70.0):
                if abs(z - bz) <= 2.0:
                    return True
        return False

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=240, is_cutout_fn=is_cutout)
    write_binary_stl("01_cnc_main_shell_6061_silver.stl", tris, "P3R_REV2_CNC_SHELL")
    return tris


def generate_part2_flat_screen_lens():
    """
    Part 2 (Rev 2): Flat Clear Acrylic / Glass Lens (14.70 x 56.80 x 1.00 mm)
    Sits at Y=+8.10..+9.10mm, flush inside the D-Cut window (+Y=9.10mm).
    """
    tris = _make_box(-7.35, 7.35, 8.10, 9.10, 28.10, 84.90)
    write_binary_stl("02_flat_screen_lens_clear.stl", tris, "P3R_REV2_FLAT_LENS")
    return tris


def generate_part3_rear_pill_buttons():
    """
    Part 3 (Rev 2): Rear (-Y) Flush Pill Button Strip
    Sits flush with rear cylinder (R=12.0mm) so front/side silhouettes remain 100% clean.
    """
    z_steps = [43.0, 44.0, 48.0, 52.0, 56.0, 60.0, 64.0, 68.0, 72.0, 73.0]
    t_center = 1.5 * math.pi
    theta_range = (t_center - 0.14, t_center + 0.14)

    def r_outer(z, theta):
        for bz in (46.0, 54.0, 62.0, 70.0):
            if abs(z - bz) <= 1.75 and abs(theta - t_center) < 0.11:
                return 12.00  # Flush with R=12.0mm outer surface!
        return 10.70

    def r_inner(z, theta):
        return 9.90

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=20, theta_range=theta_range)
    write_binary_stl("03_rear_pill_button_strip_silver.stl", tris, "P3R_REV2_REAR_BUTTONS")
    return tris


def _make_offcenter_hole_plate(cx, cy, r_hole, r_outer, z_bot, z_top, n_theta=96):
    tris = []
    inner_pts, outer_pts = [], []
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
    Part 4 (Rev 2): Dark-Navy Anodized 6061 Collar (Z=92.0mm to Z=123.0mm, 28mm visible = 22.8%)
    - 0.5mm seam chamfer at Z=95.0..95.5mm matching Part 01
    - Flat top at Z=123.0mm with recessed (non-protruding) 3.5mm earphone port (cx=-4.5mm, r=3.8mm)
    - Compact lanyard lug (5.0 x 3.0 x 4.0mm) at X=+2.5..+7.5mm, Z=122.95..127.0mm with Φ2.2mm keyring hole
    """
    z_steps = [92.0, 95.0, 95.5, 121.55]

    def r_outer_barrel(z, theta):
        if z < 95.0:
            return 10.70  # Spigot fits into Part 01 (10.80mm ID)
        if z < 95.5:
            return 11.50 + (z - 95.0)
        return 12.00

    def r_inner_barrel(z, theta):
        return 9.30

    tris = make_perforated_tube(r_outer_barrel, r_inner_barrel, z_steps, n_theta=96)
    # Flat top deck (Z=121.5 .. 123.0mm) with recessed Φ7.6mm earphone port at cx=-4.5mm
    tris += _make_offcenter_hole_plate(cx=-4.5, cy=0.0, r_hole=3.8, r_outer=12.0, z_bot=121.5, z_top=123.0, n_theta=96)
    # Compact lanyard lug (5.0 x 3.0 x 4.0mm) with Φ2.2mm keyring hole
    tris += _make_lanyard_fin_with_hole(
        x0=2.5, x1=7.5, y0=-1.5, y1=1.5, z0=122.95, z1=127.0,
        hx=5.0, hz=125.1, hr=1.1, n_seg=48
    )

    write_binary_stl("04_top_navy_collar_lanyard_cap.stl", tris, "P3R_REV2_TOP_COLLAR")
    return tris


def generate_part5_bottom_rounded_dome_cap():
    """
    Part 5 (Rev 2): Closed Half-Ellipsoid Bullet Dome Cap (Z=0.0mm to Z=18.0mm + spigot to 21.0mm)
    - Closed solid tip: r(0)=0, NO bottom hole!
    - Half-ellipsoid radial semi-axis 12.0mm, axial semi-axis 13.5mm (Z=0..13.5mm)
    - Straight cylinder Z=13.5..17.7mm, then 0.3mm x 45 deg V-groove chamfer at Z=17.7..18.0mm
    """
    z_steps = [
        0.0, 0.15, 0.5, 1.0, 2.2, 2.8, 4.0, 5.5, 7.2, 9.0, 11.0, 12.5, 13.5,
        17.7, 18.0, 21.0
    ]

    def r_outer(z, theta):
        if z > 18.0:
            return 10.70  # Slip-fit spigot into Part 01 (10.80mm ID)
        if z >= 17.7:
            return 12.00 - (z - 17.7)  # 0.3mm V-groove chamfer
        if z >= 13.5:
            return 12.00
        u = (13.5 - z) / 13.5
        return 12.00 * math.sqrt(max(0.0, 1.0 - u * u))

    def r_inner(z, theta):
        if z <= 2.2 + 1e-6:
            return 0.0  # Closed solid tip! Exact apex at z=2.2mm
        if z >= 13.5:
            return 9.20
        u = (13.5 - z) / 11.3
        return 9.20 * math.sqrt(max(0.0, 1.0 - u * u))

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=96)
    write_binary_stl("05_bottom_rounded_dome_cap_silver.stl", tris, "P3R_REV2_BULLET_DOME")
    return tris


def generate_part6_internal_chassis():
    """
    Part 6 (Rev 2): Internal Insulating Sled (Z=21.5mm to Z=91.5mm, Length 70.0mm)
    Cradles 2.25" TFT (+Y), Rev 2 PCB (center), and 601260 420mAh Battery (-Y).
    """
    z_steps = [21.5, 35.0, 75.0, 91.5]
    theta_range = (math.pi / 2 + 0.52, 2 * math.pi + math.pi / 2 - 0.52)

    def r_outer(z, theta):
        return 10.65  # Slip-fit inside Part 01 (10.80mm ID)

    def r_inner(z, theta):
        if math.sin(theta) < -0.35:
            return 8.40  # Thickened lower cradle supporting 601260 battery
        return 9.15      # 18.30mm ID guide slot for 17.5mm Rev 2 PCB

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=48, theta_range=theta_range)
    write_binary_stl("06_internal_zero_solder_sled.stl", tris, "P3R_REV2_SLED")
    return tris


def main():
    all_tris = []
    all_tris += generate_part1_cnc_main_shell()
    all_tris += generate_part2_flat_screen_lens()
    all_tris += generate_part3_rear_pill_buttons()
    all_tris += generate_part4_top_navy_collar_and_lanyard()
    all_tris += generate_part5_bottom_rounded_dome_cap()
    all_tris += generate_part6_internal_chassis()
    write_binary_stl("00_full_assembled_p3r_mp3.stl", all_tris, "P3R_REV2_FULL_ASSEMBLY")
    print("[SUCCESS] All 7 Rev-2 1:1 Long-Body P3R STL files generated.")


if __name__ == "__main__":
    main()
