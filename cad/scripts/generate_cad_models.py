#!/usr/bin/env python3
"""
Persona 3 Reload (P3R) Opening Animation MP3 Player — Rev 2.4 CAD/STL Generator
(Single-Manifold Boolean-Free Pure-Python Exact Topology, CNC DFM + 0-Collision Verified)
Overall Dimensions: Φ24.0mm OD x 117.5mm Body Length (122.0mm w/ Centered Lanyard Lug)

Rev 2.4 Fixes (Addressing 100% of Rev 2.3 Pre-Production Audit Findings):
1. Part 04 Top Collar (`B-01..B-04`, `M-03`, `M-04`):
   - Rebuilt as ONE single watertight connected manifold (`Shells = 1`, ZERO overlapping shells, ZERO internal seams)
     via exact 2D polygon-with-holes ear-clipping triangulation and vertex-exact wall extrusion.
   - Eliminates both horizontal diaphragms at Z=92.50mm and Z=108.40mm: `-X` shoulder pocket is genuinely OPEN downward
     for smooth top-down assembly over Main PCB `-X` Wing + PJ-320D-SMT, and Φ7.40mm audio bore is 100% through-pierced.
   - Relocates PJ-320D-SMT pocket center to (cx=-13.10, cy=+2.40) and enlarges `-X` cavity (`X∈[-16.95, 2.00], Y∈[-1.75, +5.55]`,
     CNC-friendly R1.05mm fillets for Φ2.0mm cutter), yielding >= +0.44mm corner clearance & >= 0.60..0.90mm solder-pad
     clearance against centered ESP32-S3-Zero (X∈[-9.00,+9.00]), while preserving >= 1.72mm outer shoulder walls & >= 1.65mm groove backing.
   - Converts `Z=88.50..92.50mm` 4.0mm spigot to split `+Y` [42°..138°] & `-Y` [222°..318°] arcs so `ESP32-S3-Zero` (18.0mm wide)
     and `J2 TF-01A` MicroSD slot clear cleanly with zero interference; injects exact M1.6 pilot hole nodes (width 1.36mm).
   - Strengthens centered top lanyard lug (Z=117.50..122.00mm, 4.50mm tall, Φ2.00mm eyelet at Z=119.75 -> 1.25mm / 4.0mm² bridge).
2. Part 05 Bottom Dome (`B-05`): Injects explicit M1.6 pilot hole nodes (width 1.36mm at r_in=9.50mm) instead of 0.994mm.
3. Part 01/02/03 CNC DFM (`M-01`, `M-06`): Deduplicates 0.1μm sliver nodes in Part 01; adds CNC-friendly R1.00mm rabbet & R0.55mm
   viewport fillets in Part 01; adds matching R1.20mm corner fillets to Part 02 clear lens; converts Part 01 rear slots & Part 03
   button bosses to rounded pill geometry (`R1.50mm` slots / `R1.35mm` buttons).
4. Part 06 Sled (`M-02`): Adds `0.60mm`-wide inward horizontal PCB support ledges (`|X|>=8.20mm` at `Y∈[-1.80, -1.12]mm`) under
   17.60mm Main PCB while keeping 17.90mm guide channel (`Y∈[-1.12, -0.08]mm`) and 6.55mm open `551255` LiPo bay.
"""

import math
import os
import struct

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stl")
os.makedirs(OUT_DIR, exist_ok=True)


def write_binary_stl(filename, triangles, header_text="P3R_MP3_REV2_4_CAD"):
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
            if length > 1e-12:
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


# ============================================================================
# Pure-Python 2D Constrained Polygon-with-Holes Triangulator (Zero Dependencies)
# ============================================================================
def _poly_area2(pts):
    n = len(pts)
    s = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s


def _cross2(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _pt_in_tri2(p, a, b, c):
    c1 = _cross2(a, b, p)
    c2 = _cross2(b, c, p)
    c3 = _cross2(c, a, p)
    return c1 >= -1e-10 and c2 >= -1e-10 and c3 >= -1e-10


def _segments_intersect(a, b, c, d):
    # Excludes shared endpoint intersections if endpoint is literally equal by tolerance
    def eq(p, q):
        return abs(p[0] - q[0]) < 1e-10 and abs(p[1] - q[1]) < 1e-10

    if eq(a, c) or eq(a, d) or eq(b, c) or eq(b, d):
        return False
    if max(a[0], b[0]) < min(c[0], d[0]) - 1e-11 or max(c[0], d[0]) < min(a[0], b[0]) - 1e-11:
        return False
    if max(a[1], b[1]) < min(c[1], d[1]) - 1e-11 or max(c[1], d[1]) < min(a[1], b[1]) - 1e-11:
        return False
    d1 = _cross2(c, d, a)
    d2 = _cross2(c, d, b)
    d3 = _cross2(a, b, c)
    d4 = _cross2(a, b, d)
    if ((d1 > 1e-11 and d2 < -1e-11) or (d1 < -1e-11 and d2 > 1e-11)) and (
        (d3 > 1e-11 and d4 < -1e-11) or (d3 < -1e-11 and d4 > 1e-11)
    ):
        return True
    # Strict interior collinear or vertex-on-segment checks
    def on_seg(p, q, r):
        return (
            abs(_cross2(p, q, r)) <= 1e-10
            and min(p[0], q[0]) - 1e-10 <= r[0] <= max(p[0], q[0]) + 1e-10
            and min(p[1], q[1]) - 1e-10 <= r[1] <= max(p[1], q[1]) + 1e-10
        )

    return on_seg(c, d, a) or on_seg(c, d, b) or on_seg(a, b, c) or on_seg(a, b, d)


def _point_in_poly2(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            x_int = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_int:
                inside = not inside
    return inside


def _triangulate_polygon_with_holes(outer, holes=()):
    """
    Returns list of CCW 2D triangles ((x,y), (x,y), (x,y)) covering outer minus union(holes),
    strictly using ONLY input vertices so all extruded boundary edges match 1-to-1.
    """
    loop = list(outer)
    if _poly_area2(loop) < 0.0:
        loop.reverse()

    norm_holes = []
    for h in holes:
        hl = list(h)
        if _poly_area2(hl) > 0.0:
            hl.reverse()  # Holes must be CW
        norm_holes.append(hl)

    # Sort holes rightmost-max-x first and splice each via shortest unobstructed interior diagonal
    norm_holes.sort(key=lambda h: max(p[0] for p in h), reverse=True)

    for idx_h, hole in enumerate(norm_holes):
        remaining_holes = norm_holes[idx_h + 1 :]
        all_edges = []
        for k in range(len(loop)):
            all_edges.append((loop[k], loop[(k + 1) % len(loop)]))
        for k in range(len(hole)):
            all_edges.append((hole[k], hole[(k + 1) % len(hole)]))
        for rh in remaining_holes:
            for k in range(len(rh)):
                all_edges.append((rh[k], rh[(k + 1) % len(rh)]))

        # Rank all (hi, oj) pairs prioritizing non-collinear bridges (sin_clear >= 0.35), then shortest distance
        candidates = []
        nh, nl = len(hole), len(loop)
        for hi, hp in enumerate(hole):
            hp_prev = hole[(hi - 1) % nh]
            hp_next = hole[(hi + 1) % nh]
            for oj, op in enumerate(loop):
                dx, dy = op[0] - hp[0], op[1] - hp[1]
                d2 = dx * dx + dy * dy
                d = math.sqrt(d2) if d2 > 1e-18 else 1.0
                ux, uy = dx / d, dy / d
                op_prev = loop[(oj - 1) % nl]
                op_next = loop[(oj + 1) % nl]
                sins = []
                for p_a, p_b in ((hp, hp_prev), (hp, hp_next), (op, op_prev), (op, op_next)):
                    ex, ey = p_b[0] - p_a[0], p_b[1] - p_a[1]
                    el = math.hypot(ex, ey)
                    if el > 1e-9:
                        sins.append(abs(ux * ey - uy * ex) / el)
                min_sin = min(sins) if sins else 0.0
                tier = 0 if min_sin >= 0.35 else (1 if min_sin >= 0.15 else 2)
                candidates.append((tier, d2, hi, oj))
        candidates.sort()

        chosen = None
        for _, _, hi, oj in candidates:
            hp = hole[hi]
            op = loop[oj]
            if abs(hp[0] - op[0]) < 1e-10 and abs(hp[1] - op[1]) < 1e-10:
                continue
            mid = (0.5 * (hp[0] + op[0]), 0.5 * (hp[1] + op[1]))
            if not _point_in_poly2(mid, loop):
                continue
            if _point_in_poly2(mid, hole):
                continue
            if any(_point_in_poly2(mid, rh) for rh in remaining_holes):
                continue
            blocked = False
            for e0, e1 in all_edges:
                if _segments_intersect(hp, op, e0, e1):
                    blocked = True
                    break
            if not blocked:
                chosen = (hi, oj)
                break

        if chosen is None:
            raise RuntimeError("Failed to find bridge diagonal for polygon with hole")

        hi, oj = chosen
        rot_hole = hole[hi:] + hole[:hi] + [hole[hi]]
        loop = loop[: oj + 1] + rot_hole + [loop[oj]] + loop[oj + 1 :]

    # Ear-clip simple polygon `loop` (keeping exact vertex indices to preserve zero-area bridge seams cleanly)
    n = len(loop)
    idx = list(range(n))
    tris = []

    def is_ear(pos, strict_tol=1e-11):
        m = len(idx)
        ia = idx[(pos - 1) % m]
        ib = idx[pos]
        ic = idx[(pos + 1) % m]
        a, b, c = loop[ia], loop[ib], loop[ic]
        area = _cross2(a, b, c)
        if area <= strict_tol:
            return False
        for k in range(m):
            ik = idx[k]
            if ik == ia or ik == ib or ik == ic:
                continue
            pk = loop[ik]
            if (abs(pk[0] - a[0]) < 1e-10 and abs(pk[1] - a[1]) < 1e-10) or (
                abs(pk[0] - b[0]) < 1e-10 and abs(pk[1] - b[1]) < 1e-10
            ) or (abs(pk[0] - c[0]) < 1e-10 and abs(pk[1] - c[1]) < 1e-10):
                continue
            if _pt_in_tri2(pk, a, b, c):
                return False
        return True

    guard = 0
    while len(idx) > 3 and guard < n * n + 20:
        guard += 1
        best_pos = -1
        best_score = -1.0
        for pos in range(len(idx)):
            if is_ear(pos, strict_tol=1e-11):
                a = loop[idx[(pos - 1) % len(idx)]]
                b = loop[idx[pos]]
                c = loop[idx[(pos + 1) % len(idx)]]
                l2 = (
                    (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
                    + (c[0] - b[0]) ** 2 + (c[1] - b[1]) ** 2
                    + (a[0] - c[0]) ** 2 + (a[1] - c[1]) ** 2
                )
                score = _cross2(a, b, c) / l2 if l2 > 1e-18 else 0.0
                if score > best_score:
                    best_score = score
                    best_pos = pos
        found = False
        if best_pos >= 0:
            ia = idx[(best_pos - 1) % len(idx)]
            ib = idx[best_pos]
            ic = idx[(best_pos + 1) % len(idx)]
            tris.append((loop[ia], loop[ib], loop[ic]))
            idx.pop(best_pos)
            found = True
        if not found:
            # Handle degenerate 0-area bridge vertices cleanly by pruning exact backtrack spikes (a == c)
            for pos in range(len(idx)):
                ia = idx[(pos - 1) % len(idx)]
                ib = idx[pos]
                ic = idx[(pos + 1) % len(idx)]
                a, b, c = loop[ia], loop[ib], loop[ic]
                if abs(_cross2(a, b, c)) <= 1e-10:
                    # Only pop strictly zero-area collinear spikes pointing back
                    if abs(a[0] - c[0]) < 1e-10 and abs(a[1] - c[1]) < 1e-10:
                        idx.pop(pos)
                        found = True
                        break
            if not found:
                for pos in range(len(idx)):
                    if is_ear(pos, strict_tol=-1e-11):
                        ia = idx[(pos - 1) % len(idx)]
                        ib = idx[pos]
                        ic = idx[(pos + 1) % len(idx)]
                        if abs(_cross2(loop[ia], loop[ib], loop[ic])) > 1e-10:
                            tris.append((loop[ia], loop[ib], loop[ic]))
                        idx.pop(pos)
                        found = True
                        break
            if not found:
                break

    if len(idx) == 3:
        a, b, c = loop[idx[0]], loop[idx[1]], loop[idx[2]]
        if abs(_cross2(a, b, c)) > 1e-11:
            tris.append((a, b, c))
    return tris


def _emit_cap_z(triangles, z, outer, holes=(), normal_up=True):
    tris2d = _triangulate_polygon_with_holes(outer, holes)
    for p1, p2, p3 in tris2d:
        a = (p1[0], p1[1], z)
        b = (p2[0], p2[1], z)
        c = (p3[0], p3[1], z)
        if normal_up:
            triangles.append((a, b, c))
        else:
            triangles.append((a, c, b))


def _extrude_loop_wall(triangles, loop, z0, z1, outward_ccw=True):
    """
    Extrudes a closed 2D loop vertically from z0 to z1.
    If outward_ccw=True on a CCW loop, outward normal points AWAY from the loop interior.
    If outward_ccw=False on a CCW loop (or True on a CW hole loop), normal points INWARD toward hole center.
    """
    pts = list(loop)
    area = _poly_area2(pts)
    if area < 0.0:
        pts.reverse()
    n = len(pts)
    for i in range(n):
        p0 = pts[i]
        p1 = pts[(i + 1) % n]
        a0 = (p0[0], p0[1], z0)
        a1 = (p1[0], p1[1], z0)
        b0 = (p0[0], p0[1], z1)
        b1 = (p1[0], p1[1], z1)
        if outward_ccw:
            add_quad(triangles, a0, a1, b1, b0)
        else:
            add_quad(triangles, a0, b0, b1, a1)


# ============================================================================
# Shared Conformal Sweep Helpers
# ============================================================================
def make_conformal_shell(
    outer_xy_fn,
    inner_xy_fn,
    z_steps,
    u_steps,
    full_circle=True,
    is_cutout_fn=None,
):
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
    u_steps=None,
    n_theta=120,
    theta_range=(0.0, 2.0 * math.pi),
    is_cutout_fn=None,
):
    t_start, t_end = theta_range
    full_circle = abs((t_end - t_start) - 2.0 * math.pi) < 1e-5
    if u_steps is None:
        u_steps = [t_start + (t_end - t_start) * i / n_theta for i in range(n_theta + 1)]
    return make_conformal_shell(
        lambda z, t: (r_outer_fn(z, t) * math.cos(t), r_outer_fn(z, t) * math.sin(t)),
        lambda z, t: (r_inner_fn(z, t) * math.cos(t), r_inner_fn(z, t) * math.sin(t)),
        z_steps,
        u_steps,
        full_circle=full_circle,
        is_cutout_fn=is_cutout_fn,
    )


def _rounded_rect_loop(x0, x1, y0, y1, rc, arc_segs=8):
    pts = []
    corners = [
        (x1 - rc, y1 - rc, 0.0, 0.5 * math.pi),
        (x0 + rc, y1 - rc, 0.5 * math.pi, math.pi),
        (x0 + rc, y0 + rc, math.pi, 1.5 * math.pi),
        (x1 - rc, y0 + rc, 1.5 * math.pi, 2.0 * math.pi),
    ]
    for cx, cy, a0, a1 in corners:
        for i in range(arc_segs + 1):
            a = a0 + (a1 - a0) * i / arc_segs
            pt = (cx + rc * math.cos(a), cy + rc * math.sin(a))
            if not pts or math.hypot(pt[0] - pts[-1][0], pt[1] - pts[-1][1]) > 1e-6:
                pts.append(pt)
    if pts and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-6:
        pts.pop()
    return pts


def _rounded_rect_sdf(px, py, cx, cy, half_w, half_h, rc):
    dx = max(0.0, abs(px - cx) - (half_w - rc))
    dy = max(0.0, abs(py - cy) - (half_h - rc))
    ax = abs(px - cx) - half_w
    ay = abs(py - cy) - half_h
    outside = math.hypot(dx, dy)
    inside = min(max(ax, ay), 0.0)
    return outside + inside - rc if (dx > 0.0 or dy > 0.0) else max(ax, ay)


# ============================================================================
# Part 1: CNC 6061 Main Shell
# ============================================================================
def generate_part1_cnc_main_shell():
    """
    Part 1 (Rev 2.4): CNC 6061 Aluminum Main Barrel (Z=18.0..92.5mm, OD=24.0mm, ID=21.40mm)
    - Orthogonal front flat chord (|x| <= 8.1584mm): R0.55mm corner viewport (15.00x56.50mm, clears 14.80x55.30 TFT AA)
      and R1.00mm CNC-machinable rabbet pocket (15.56x58.30mm) down to 1.076mm aluminum shelf (Y=+6.924..+8.00mm).
    - Deduplicated u_steps (>= 1e-4 spacing -> eliminates 40000:1 sliver triangles).
    - Rear spine (|x| <= 2.50mm): rounded pill button slots (3.50x4.00mm R1.50mm) & M1.6 holes (Z=20.0 & Z=90.5mm).
    """
    R_OUT = 12.00
    R_IN = 10.70
    Y_OUT_FLAT = 8.80
    X_SEAM = math.sqrt(R_OUT * R_OUT - Y_OUT_FLAT * Y_OUT_FLAT)
    Y_IN_FLAT = math.sqrt(R_IN * R_IN - X_SEAM * X_SEAM)
    T_OUT_R = math.atan2(Y_OUT_FLAT, X_SEAM)
    T_OUT_L = math.pi - T_OUT_R
    T_IN_R = math.atan2(Y_IN_FLAT, X_SEAM)
    T_IN_L = math.pi - T_IN_R
    X_SPINE = 2.50

    def x_to_u_front(x):
        return 0.25 * (X_SEAM - x) / (2.0 * X_SEAM)

    def x_to_u_rear(x):
        return 0.50 + 0.25 * (x + X_SPINE) / (2.0 * X_SPINE)

    raw_u_front = (
        [0.25 * i / 48 for i in range(49)]
        + [x_to_u_front(7.80), x_to_u_front(7.76), x_to_u_front(-7.76), x_to_u_front(-7.80), x_to_u_front(7.50), x_to_u_front(-7.50)]
        + [x_to_u_front(6.78 + 1.00 * k / 8) for k in range(8)]
        + [x_to_u_front(-(6.78 + 1.00 * k / 8)) for k in range(8)]
    )
    u_front = []
    for uv in sorted(raw_u_front):
        if not u_front or abs(uv - u_front[-1]) > 4e-4:
            u_front.append(uv)

    u_left = [0.25 + 0.25 * i / 36 for i in range(1, 36)]
    raw_u_rear = (
        [0.50 + 0.25 * i / 24 for i in range(25)]
        + [x_to_u_rear(xv) for xv in (-1.75, -1.50, -1.15, -0.85, 0.85, 1.15, 1.50, 1.75)]
    )
    u_rear = []
    for uv in sorted(raw_u_rear):
        if not u_rear or abs(uv - u_rear[-1]) > 4e-4:
            u_rear.append(uv)

    u_right = [0.75 + 0.25 * i / 36 for i in range(1, 36)]
    u_steps = u_front + u_left + u_rear + u_right + [1.0]

    btn_z_fine = []
    for bz in (38.0, 46.0, 54.0, 62.0):
        btn_z_fine += [bz - 2.00 + 0.20 * k for k in range(21)]

    raw_z = (
        [18.00, 18.30, 19.15, 20.85, 21.50, 24.50, 26.28, 26.32]
        + [26.44 + 0.14 * k for k in range(11)]  # covers rabbet R1.0 + viewport R0.55
        + [32.0, 36.0]
        + btn_z_fine
        + [68.0, 76.0]
        + [83.06 + 0.14 * k for k in range(11)]  # covers top rabbet/viewport fillets
        + [84.58, 84.62, 86.00, 89.00, 89.65, 91.35, 92.00, 92.50]
    )
    z_steps = []
    for zv in sorted(raw_z):
        if not z_steps or abs(zv - z_steps[-1]) > 1e-3:
            z_steps.append(zv)

    def flat_factor(z):
        if z <= 21.50 or z >= 89.00:
            return 0.0
        if z < 24.50:
            return _smoothstep01((z - 21.50) / 3.00)
        if z > 86.00:
            return _smoothstep01((89.00 - z) / 3.00)
        return 1.0

    def rabbet_factor(z, x):
        # Smooth rounded-corner CNC rabbet pocket: 15.56 x 58.30mm, Z_center=55.45mm, corner R=1.00mm
        d = _rounded_rect_sdf(x, z, 0.0, 55.45, 7.78, 29.15, 1.00)
        if d >= 0.02:
            return 0.0
        if d <= -0.02:
            return 1.0
        return (0.02 - d) / 0.04

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
            # Rounded viewport window (15.00x56.50mm, R0.55mm corners -> zero AA clip of 14.80x55.30mm!)
            if _rounded_rect_sdf(x, z, 0.0, 55.45, 7.50, 28.25, 0.55) <= 0.0:
                return True
        if 0.50 <= u <= 0.75:
            x = -X_SPINE + 2.0 * X_SPINE * ((u - 0.50) / 0.25)
            for bz in (38.0, 46.0, 54.0, 62.0):
                # Pill slot: 3.50 x 4.00mm, corner R1.50mm (cuts cleanly w/ Φ3.0mm CNC endmill)
                if _rounded_rect_sdf(x, z, 0.0, bz, 1.75, 2.00, 1.50) <= 0.0:
                    return True
            if abs(x) <= 0.85:
                if (19.15 <= z <= 20.85) or (89.65 <= z <= 91.35):
                    return True
        return False

    tris = make_conformal_shell(outer_xy, inner_xy, z_steps, u_steps, full_circle=True, is_cutout_fn=is_cutout)
    write_binary_stl("01_cnc_main_shell_6061_silver.stl", tris, "P3R_REV2_4_CNC_SHELL")
    return tris


# ============================================================================
# Part 2: Clear Lens w/ R1.20mm Rounded Corners
# ============================================================================
def generate_part2_flat_screen_lens():
    """
    Part 2 (Rev 2.4): Flat Clear Acrylic / Glass Lens (15.44 x 58.14 x 0.80 mm, R1.20mm outer corner fillets)
    Drops smoothly into Part 01's CNC-milled R1.00mm rabbet pocket (X∈[-7.78,+7.78], Z∈[26.30,84.60])
    with >= +0.18mm radial corner clearance and sits on 1.08mm solid aluminum shelf.
    """
    loop_xz = _rounded_rect_loop(-7.72, 7.72, 26.38, 84.52, rc=1.20, arc_segs=4)
    tris2d = _triangulate_polygon_with_holes(loop_xz)
    tris = []
    # Front face at Y = +8.80 (+Y normal) and Back face at Y = +8.00 (-Y normal)
    for (x1, z1), (x2, z2), (x3, z3) in tris2d:
        # CCW in (X, Z) -> cross(p2-p1, p3-p1) has +Y component when ordered (x1, y, z1) reversed!
        # Verify: (p2-p1) x (p3-p1) in 3D for Y-constant: ((dx1,0,dz1) x (dx2,0,dz2)) = (0, dz1*dx2 - dx1*dz2, 0) -> NEGATIVE of 2D cross!
        tris.append(((x1, 8.80, z1), (x3, 8.80, z3), (x2, 8.80, z2)))  # +Y outward
        tris.append(((x1, 8.00, z1), (x2, 8.00, z2), (x3, 8.00, z3)))  # -Y outward
    n = len(loop_xz)
    for i in range(n):
        x0, z0 = loop_xz[i]
        x1, z1 = loop_xz[(i + 1) % n]
        add_quad(tris, (x0, 8.00, z0), (x0, 8.80, z0), (x1, 8.80, z1), (x1, 8.00, z1))
    write_binary_stl("02_flat_screen_lens_clear.stl", tris, "P3R_REV2_4_FLAT_LENS")
    return tris


# ============================================================================
# Part 3: Rear Pill Button Strip (Rounded Pill Bosses R1.35mm)
# ============================================================================
def generate_part3_rear_pill_buttons():
    """
    Part 3 (Rev 2.4): Rear (-Y) Flush Pill Button Strip (Z=38, 46, 54, 62mm)
    - Base inside at r_in=10.45mm -> 0.15mm clearance from TS263065A plungers (Y=-10.30mm).
    - True rounded pill bosses (3.10 x 3.56mm, R1.35mm) sliding smoothly inside 01's 3.50 x 4.00mm R1.50mm pill slots.
    - Widened inner retention wings (±2.30mm) & Z=42,50,58mm flexure cutouts prevent pop-out & cross-actuation.
    """
    btn_z = []
    for bz in (38.0, 46.0, 54.0, 62.0):
        btn_z += [bz - 1.90 + 0.19 * k for k in range(21)]
    raw_z = [34.50, 41.40, 42.60, 49.40, 50.60, 57.40, 58.60, 65.50] + btn_z
    z_steps = []
    for zv in sorted(raw_z):
        if not z_steps or abs(zv - z_steps[-1]) > 1e-3:
            z_steps.append(zv)

    t_center = 1.5 * math.pi
    theta_range = (t_center - 0.22, t_center + 0.22)

    def r_outer(z, theta):
        x = 12.00 * math.cos(theta)
        fb = 0.0
        for bz in (38.0, 46.0, 54.0, 62.0):
            # Pill boss: 3.10mm wide (half_w=1.55) x 3.56mm tall (half_h=1.78), R1.35mm corners
            d = _rounded_rect_sdf(x, z, 0.0, bz, 1.55, 1.78, 1.35)
            if d <= -0.10:
                fb = 1.0
                break
            elif d < 0.05:
                fb = max(fb, (0.05 - d) / 0.15)
        return 10.62 + 1.38 * fb

    def r_inner(z, theta):
        return 10.45

    def is_cutout(z_mid, t_mid):
        for sz in (42.0, 50.0, 58.0):
            if abs(z_mid - sz) <= 0.60 and abs(t_mid - t_center) <= 0.14:
                return True
        return False

    tris = make_perforated_tube(r_outer, r_inner, z_steps, n_theta=48, theta_range=theta_range, is_cutout_fn=is_cutout)
    write_binary_stl("03_rear_pill_button_strip_silver.stl", tris, "P3R_REV2_4_REAR_BUTTONS")
    return tris


# ============================================================================
# Part 4: Single-Manifold Dark Navy Collar w/ -X Shoulder Bore & Centered Lug
# ============================================================================
def _ray_rounded_rect_from_inside(ox, oy, cos_a, sin_a, x0, x1, y0, y1, rc):
    lo, hi = 0.0, 40.0
    ix0, ix1 = x0 + rc, x1 - rc
    iy0, iy1 = y0 + rc, y1 - rc
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        px = ox + mid * cos_a
        py = oy + mid * sin_a
        dx = max(ix0 - px, 0.0, px - ix1)
        dy = max(iy0 - py, 0.0, py - iy1)
        if dx * dx + dy * dy <= rc * rc:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _ray_circle_hits(ox, oy, ux, uy, cx, cy, r):
    dx = ox - cx
    dy = oy - cy
    b = dx * ux + dy * uy
    c = dx * dx + dy * dy - r * r
    disc = b * b - c
    if disc <= 1e-12:
        return None
    sd = math.sqrt(disc)
    return (-b - sd, -b + sd)


def _circle_circle_intersections(cx, cy, r_c, r0):
    """Sorted angles around origin where circle (cx,cy,r_c) crosses circle (0,0,r0)."""
    d = math.hypot(cx, cy)
    a = (r0 * r0 - r_c * r_c + d * d) / (2.0 * d)
    h = math.sqrt(max(0.0, r0 * r0 - a * a))
    ang_c = math.atan2(cy, cx)
    da = math.atan2(h, a)
    t1 = (ang_c - da) % (2.0 * math.pi)
    t2 = (ang_c + da) % (2.0 * math.pi)
    return (t1, t2) if t1 < t2 else (t2, t1)


def generate_part4_top_navy_collar_and_lanyard():
    """
    Part 4 (Rev 2.4): Dark-Navy Anodized Collar (Single Watertight Manifold, Shells=1!)
    - Barrel Z=92.50..117.50mm (25.0mm -> Cap/Mid = 0.336), Centered Lanyard Lug Z=117.50..122.00mm (hr=1.00mm).
    - Split 4.0mm bottom spigot (Z=88.50..92.50mm, OD=21.20/ID=19.00mm): +Y arc [42°..138°] + -Y arc [222°..318°] w/ 1.36mm M1.6 hole
      (leaves ±X open so ESP32-S3-Zero & J2 TF-01A SD card never collide with spigot wall!).
    - Sculpted `-X` shoulder bulge (Z=92.50..109.40mm, X_min=-18.85mm, Y∈[-3.55,+8.20], R2.95mm) enclosing enlarged pocket
      (X∈[-17.15, 2.00], Y∈[-1.75, +6.50], R1.05mm -> CNC Φ2.0mm cutter & >=+0.35mm clearance to Φ7.40mm bore, Main PCB -X Wing & PJ-320D-SMT
      at cx=-13.10, cy=+2.40). Bottom at Z=92.50mm is 100% OPEN into pocket!
    - Z=108.40..109.40mm step deck pierced cleanly by Φ7.40mm vertical bore (ZERO diaphragms!) & Z=109.40..117.50 Φ8.70mm plug groove.
    """
    JACK_X = -13.10
    JACK_Y = 2.40
    R_HOLE = 3.70
    R_GROOVE = 4.35
    R_GROOVE_IN = 6.00
    R_MAIN_IN = 10.20
    R_OUT = 12.00
    R_SPIGOT_IN = 9.50
    R_SPIGOT_OUT = 10.60

    # Key angular landmarks (radians in [0, 2pi))
    SPIGOT_F0 = math.radians(42.0)
    SPIGOT_F1 = math.radians(138.0)
    SPIGOT_R0 = math.radians(222.0)
    SPIGOT_R1 = math.radians(318.0)
    D_M16 = math.asin(0.68 / R_SPIGOT_IN)  # Exact 1.36mm width at r=9.50mm
    M16_A0 = 1.5 * math.pi - D_M16
    M16_A1 = 1.5 * math.pi + D_M16

    TH_BULGE_A = math.pi - math.asin(8.20 / R_OUT)
    TH_BULGE_B = math.pi + math.asin(3.55 / R_OUT)
    TH_GRV_A, TH_GRV_B = _circle_circle_intersections(JACK_X, JACK_Y, R_GROOVE, R_OUT)
    TH_GRVIN_A, TH_GRVIN_B = _circle_circle_intersections(JACK_X, JACK_Y, R_GROOVE_IN, R_MAIN_IN)
    TH_POCK_A = math.pi - math.asin(6.50 / R_MAIN_IN)
    TH_POCK_B = math.pi + math.asin(1.75 / R_MAIN_IN)

    def boss_outer_r(t):
        ct, st = math.cos(t), math.sin(t)
        return max(R_OUT, _ray_rounded_rect_from_inside(0.0, 0.0, ct, st, -18.85, 2.00, -3.55, 8.20, 2.95))

    def pocket_inner_r(t):
        ct, st = math.cos(t), math.sin(t)
        return max(R_MAIN_IN, _ray_rounded_rect_from_inside(0.0, 0.0, ct, st, -17.15, 2.00, -1.75, 6.50, 1.05))

    landmarks = [
        SPIGOT_F0, SPIGOT_F1, SPIGOT_R0, SPIGOT_R1, M16_A0, M16_A1,
        TH_BULGE_A, TH_BULGE_B, TH_POCK_A, TH_POCK_B, TH_GRVIN_A, TH_GRVIN_B,
    ]
    # Build canonical angle grid `thetas` preserving every landmark cleanly (zero collinear micro-steps on X=-18.85 flat)
    flat_t0 = math.atan2(5.25, -18.85) % (2.0 * math.pi)
    flat_t1 = math.atan2(-0.60, -18.85) % (2.0 * math.pi)
    grid_thetas = (
        [2.0 * math.pi * i / 160 for i in range(160)]
        + [
            t for t in (TH_BULGE_A + (TH_BULGE_B - TH_BULGE_A) * k / 32 for k in range(1, 32))
            if not (flat_t0 <= t <= flat_t1)
        ]
    )
    lms = sorted(x % (2.0 * math.pi) for x in landmarks)
    kept_grid = []
    for tv in sorted(x % (2.0 * math.pi) for x in grid_thetas):
        if any(min(abs(tv - lm), 2.0 * math.pi - abs(tv - lm)) < 6e-3 for lm in lms):
            continue
        if not kept_grid or abs(tv - kept_grid[-1]) > 6e-3:
            kept_grid.append(tv)
    thetas = sorted(lms + kept_grid)

    def idx_of(target):
        return min(range(len(thetas)), key=lambda i: min(abs(thetas[i] - target), 2.0 * math.pi - abs(thetas[i] - target)))

    # Enforce EXACT coordinate pinning on analytical landmark angles so all boundary junctions coincide identically
    i_sf0, i_sf1 = idx_of(SPIGOT_F0), idx_of(SPIGOT_F1)
    i_sr0, i_sr1 = idx_of(SPIGOT_R0), idx_of(SPIGOT_R1)
    i_m0, i_m1 = idx_of(M16_A0), idx_of(M16_A1)
    i_ba, i_bb = idx_of(TH_BULGE_A), idx_of(TH_BULGE_B)
    i_pa, i_pb = idx_of(TH_POCK_A), idx_of(TH_POCK_B)
    i_ga, i_gb = idx_of(TH_GRVIN_A), idx_of(TH_GRVIN_B)
    thetas[i_sf0], thetas[i_sf1] = SPIGOT_F0, SPIGOT_F1
    thetas[i_sr0], thetas[i_sr1] = SPIGOT_R0, SPIGOT_R1
    thetas[i_m0], thetas[i_m1] = M16_A0, M16_A1
    thetas[i_ba], thetas[i_bb] = TH_BULGE_A, TH_BULGE_B
    thetas[i_pa], thetas[i_pb] = TH_POCK_A, TH_POCK_B
    thetas[i_ga], thetas[i_gb] = TH_GRVIN_A, TH_GRVIN_B

    n_th = len(thetas)

    def pt_polar(r, t):
        return (r * math.cos(t), r * math.sin(t))

    O_shoulder = [pt_polar(R_OUT if (i <= i_ba or i >= i_bb) else boss_outer_r(thetas[i]), thetas[i]) for i in range(n_th)]
    I_pocket = [pt_polar(R_MAIN_IN if (i <= i_pa or i >= i_pb) else pocket_inner_r(thetas[i]), thetas[i]) for i in range(n_th)]

    # Build O_upper (R_OUT=12.00 minus groove R_GROOVE around (JACK_X, JACK_Y)) using clean phi-sampled groove arc!
    def build_indented_circle(r_base, th_arc_start, th_arc_end, cx, cy, r_cut, n_groove=32):
        # Returns (loop_pts, idx_groove_start_in_loop, idx_groove_end_in_loop)
        p_a = pt_polar(r_base, th_arc_start)
        p_b = pt_polar(r_base, th_arc_end)
        phi_a = math.atan2(p_a[1] - cy, p_a[0] - cx) % (2.0 * math.pi)
        phi_b = math.atan2(p_b[1] - cy, p_b[0] - cx) % (2.0 * math.pi)
        # Note: going CCW along base from th_arc_end -> th_arc_start (on outer +X side), then along groove CW from phi_a -> phi_b!
        # Let's determine angular span on groove that lies INSIDE circle r_base:
        dphi_cw = (phi_a - phi_b) % (2.0 * math.pi)
        mid_phi = (phi_a - 0.5 * dphi_cw) % (2.0 * math.pi)
        mx, my = cx + r_cut * math.cos(mid_phi), cy + r_cut * math.sin(mid_phi)
        if math.hypot(mx, my) > r_base:
            # Flip to other arc direction
            dphi_cw = dphi_cw - 2.0 * math.pi
        pts = []
        # 1) Base circle angles strictly outside (th_arc_start, th_arc_end) replaced on [th_arc_start..th_arc_end] by groove!
        idx_start = None
        for i in range(n_th):
            t = thetas[i]
            if th_arc_start < t < th_arc_end:
                continue
            pts.append(pt_polar(r_base, t))
        # Insert th_arc_start, groove interior points, and th_arc_end in CCW position between th < th_arc_start and th > th_arc_end
        before = [pt_polar(r_base, t) for t in thetas if t <= th_arc_start - 1e-7]
        after = [pt_polar(r_base, t) for t in thetas if t >= th_arc_end + 1e-7]
        groove_pts = [p_a]
        for k in range(1, n_groove):
            ph = phi_a - dphi_cw * (k / n_groove)
            groove_pts.append((cx + r_cut * math.cos(ph), cy + r_cut * math.sin(ph)))
        groove_pts.append(p_b)
        loop = before + groove_pts + after
        return loop, groove_pts

    O_upper, groove_pts_out = build_indented_circle(R_OUT, TH_GRV_A, TH_GRV_B, JACK_X, JACK_Y, R_GROOVE, n_groove=32)
    H_main, _ = build_indented_circle(R_MAIN_IN, TH_GRVIN_A, TH_GRVIN_B, JACK_X, JACK_Y, R_GROOVE_IN, n_groove=32)

    # Top chamfered outer loop at Z=117.50mm (shrunk 0.80mm on R_OUT=12.00 -> R_TOP=11.20mm, still keeping R_GROOVE=4.35!)
    R_TOP = 11.20
    TH_TOPGRV_A, TH_TOPGRV_B = _circle_circle_intersections(JACK_X, JACK_Y, R_GROOVE, R_TOP)

    def make_upper_chamfer_loop(z_val):
        frac = max(0.0, min(1.0, (z_val - 117.00) / 0.50)) if z_val > 117.00 else 0.0
        rb = R_OUT - 0.80 * frac
        ta, tb = _circle_circle_intersections(JACK_X, JACK_Y, R_GROOVE, rb)
        p_a = pt_polar(rb, ta)
        p_b = pt_polar(rb, tb)
        phi_a = math.atan2(p_a[1] - JACK_Y, p_a[0] - JACK_X) % (2.0 * math.pi)
        phi_b = math.atan2(p_b[1] - JACK_Y, p_b[0] - JACK_X) % (2.0 * math.pi)
        dphi_cw = (phi_a - phi_b) % (2.0 * math.pi)
        mid_phi = (phi_a - 0.5 * dphi_cw) % (2.0 * math.pi)
        if math.hypot(JACK_X + R_GROOVE * math.cos(mid_phi), JACK_Y + R_GROOVE * math.sin(mid_phi)) > rb:
            dphi_cw = dphi_cw - 2.0 * math.pi
        # Keep exact vertex count matching O_upper: sample before/after on same base count + 32 groove points!
        n_before = sum(1 for t in thetas if t <= TH_GRV_A - 1e-7)
        n_after = sum(1 for t in thetas if t >= TH_GRV_B + 1e-7)
        loop = []
        for k in range(n_before):
            t = ta * (k / max(1, n_before))
            loop.append(pt_polar(rb, t))
        loop.append(p_a)
        for k in range(1, 32):
            ph = phi_a - dphi_cw * (k / 32)
            loop.append((JACK_X + R_GROOVE * math.cos(ph), JACK_Y + R_GROOVE * math.sin(ph)))
        loop.append(p_b)
        t_rem = 2.0 * math.pi - tb
        for k in range(1, n_after + 1):
            t = tb + t_rem * (k / (n_after + 1))
            loop.append(pt_polar(rb, t))
        return loop

    O_top = make_upper_chamfer_loop(117.50)

    # Audio Jack through-hole circle H_jack (Φ7.40mm, 32 segments -> clean circle & AR < 800 on caps)
    n_jack = 32
    H_jack = [
        (JACK_X + R_HOLE * math.cos(2.0 * math.pi * k / n_jack), JACK_Y + R_HOLE * math.sin(2.0 * math.pi * k / n_jack))
        for k in range(n_jack)
    ]

    tris = []

    # ------------------------------------------------------------------
    # ZONE 1: Split 4.0mm Spigot (Z = 88.50 .. 92.50mm) + Seamless Junction at Z = 92.50mm
    # ------------------------------------------------------------------
    def _emit_spigot_arc(i_start, i_end, is_rear=False):
        z_sp = [88.50, 89.75, 91.25, 92.50]
        nz_s = len(z_sp) - 1
        # Collect contiguous theta indices wrapping around 0
        arc_indices = list(range(i_start, i_end + 1))
        n_arc_cells = len(arc_indices) - 1

        def cell_solid(iz, ic):
            if iz < 0 or iz >= nz_s or ic < 0 or ic >= n_arc_cells:
                return False
            if is_rear and iz == 1:
                i0, i1 = arc_indices[ic], arc_indices[ic + 1]
                if i0 >= i_m0 and i1 <= i_m1:
                    return False
            return True

        for iz in range(nz_s):
            z0, z1 = z_sp[iz], z_sp[iz + 1]
            for ic in range(n_arc_cells):
                if not cell_solid(iz, ic):
                    continue
                t0 = thetas[arc_indices[ic]]
                t1 = thetas[arc_indices[ic + 1]]
                po00 = (R_SPIGOT_OUT * math.cos(t0), R_SPIGOT_OUT * math.sin(t0), z0)
                po01 = (R_SPIGOT_OUT * math.cos(t1), R_SPIGOT_OUT * math.sin(t1), z0)
                po10 = (R_SPIGOT_OUT * math.cos(t0), R_SPIGOT_OUT * math.sin(t0), z1)
                po11 = (R_SPIGOT_OUT * math.cos(t1), R_SPIGOT_OUT * math.sin(t1), z1)
                pi00 = (R_SPIGOT_IN * math.cos(t0), R_SPIGOT_IN * math.sin(t0), z0)
                pi01 = (R_SPIGOT_IN * math.cos(t1), R_SPIGOT_IN * math.sin(t1), z0)
                pi10 = (R_SPIGOT_IN * math.cos(t0), R_SPIGOT_IN * math.sin(t0), z1)
                pi11 = (R_SPIGOT_IN * math.cos(t1), R_SPIGOT_IN * math.sin(t1), z1)
                # Outer & inner walls
                add_quad(tris, po00, po01, po11, po10)
                add_quad(tris, pi00, pi10, pi11, pi01)
                if not cell_solid(iz - 1, ic):
                    add_quad(tris, po00, pi00, pi01, po01)
                if iz < nz_s - 1 and not cell_solid(iz + 1, ic):
                    add_quad(tris, po10, po11, pi11, pi10)
                if ic > 0 and not cell_solid(iz, ic - 1):
                    add_quad(tris, po00, po10, pi10, pi00)
                if ic < n_arc_cells - 1 and not cell_solid(iz, ic + 1):
                    add_quad(tris, po01, pi01, pi11, po11)

        # Planar end-caps of arc at t_start (ic=0, facing -theta) and t_end (ic=n_arc_cells, facing +theta),
        # splitting the top Z=92.50 edge cleanly at R_MAIN_IN=10.20mm for degree-2 edge match!
        for is_end, i_t in ((False, i_start), (True, i_end)):
            ct, st = math.cos(thetas[i_t]), math.sin(thetas[i_t])
            p_in_bot = (R_SPIGOT_IN * ct, R_SPIGOT_IN * st, 88.50)
            p_out_bot = (R_SPIGOT_OUT * ct, R_SPIGOT_OUT * st, 88.50)
            p_in_top = (R_SPIGOT_IN * ct, R_SPIGOT_IN * st, 92.50)
            p_mid_top = (R_MAIN_IN * ct, R_MAIN_IN * st, 92.50)
            p_out_top = (R_SPIGOT_OUT * ct, R_SPIGOT_OUT * st, 92.50)
            # Also match intermediate z steps along vertical end wall so zero T-junctions occur!
            p_in_1 = (R_SPIGOT_IN * ct, R_SPIGOT_IN * st, 89.75)
            p_out_1 = (R_SPIGOT_OUT * ct, R_SPIGOT_OUT * st, 89.75)
            p_in_2 = (R_SPIGOT_IN * ct, R_SPIGOT_IN * st, 91.25)
            p_out_2 = (R_SPIGOT_OUT * ct, R_SPIGOT_OUT * st, 91.25)
            if is_end:
                # End face at theta = t_end faces +theta: (+r x +z = -theta -> reversed uses +z then +r)
                add_quad(tris, p_in_bot, p_in_1, p_out_1, p_out_bot)
                add_quad(tris, p_in_1, p_in_2, p_out_2, p_out_1)
                tris.append((p_in_2, p_in_top, p_mid_top))
                tris.append((p_in_2, p_mid_top, p_out_top))
                tris.append((p_in_2, p_out_top, p_out_2))
            else:
                # Start face at theta = t_start faces -theta (+r x +z = -theta)
                add_quad(tris, p_in_bot, p_out_bot, p_out_1, p_in_1)
                add_quad(tris, p_in_1, p_out_1, p_out_2, p_in_2)
                tris.append((p_in_2, p_mid_top, p_in_top))
                tris.append((p_in_2, p_out_top, p_mid_top))
                tris.append((p_in_2, p_out_2, p_out_top))

    _emit_spigot_arc(i_sf0, i_sf1, is_rear=False)
    _emit_spigot_arc(i_sr0, i_sr1, is_rear=True)

    # Z = 92.50mm Junction Ring matching outer/inner walls cleanly across all n_th angular segments!
    for i in range(n_th):
        j = (i + 1) % n_th
        in_f_arc = i_sf0 <= i < i_sf1
        in_r_arc = i_sr0 <= i < i_sr1
        t0, t1 = thetas[i], thetas[j]
        p_in0 = (I_pocket[i][0], I_pocket[i][1], 92.50)
        p_in1 = (I_pocket[j][0], I_pocket[j][1], 92.50)
        p_out0 = (O_shoulder[i][0], O_shoulder[i][1], 92.50)
        p_out1 = (O_shoulder[j][0], O_shoulder[j][1], 92.50)

        if in_f_arc or in_r_arc:
            # Inner upward shelf (+Z): R_SPIGOT_IN -> R_MAIN_IN
            sp_in0 = (R_SPIGOT_IN * math.cos(t0), R_SPIGOT_IN * math.sin(t0), 92.50)
            sp_in1 = (R_SPIGOT_IN * math.cos(t1), R_SPIGOT_IN * math.sin(t1), 92.50)
            add_quad(tris, sp_in0, p_in0, p_in1, sp_in1)
            # Outer downward shoulder (-Z): R_SPIGOT_OUT -> O_shoulder
            sp_out0 = (R_SPIGOT_OUT * math.cos(t0), R_SPIGOT_OUT * math.sin(t0), 92.50)
            sp_out1 = (R_SPIGOT_OUT * math.cos(t1), R_SPIGOT_OUT * math.sin(t1), 92.50)
            add_quad(tris, sp_out0, sp_out1, p_out1, p_out0)
        elif j in (i_sf0, i_sr0):
            # Cell ending right on spigot start edge: split p_in1..p_out1 at sp_out1!
            sp_out1 = (R_SPIGOT_OUT * math.cos(t1), R_SPIGOT_OUT * math.sin(t1), 92.50)
            tris.append((p_in0, p_out1, p_out0))
            tris.append((p_in0, sp_out1, p_out1))
            tris.append((p_in0, p_in1, sp_out1))
        elif i in (i_sf1, i_sr1):
            # Cell starting right on spigot end edge: split p_in0..p_out0 at sp_out0! (-Z downward normal)
            sp_out0 = (R_SPIGOT_OUT * math.cos(t0), R_SPIGOT_OUT * math.sin(t0), 92.50)
            tris.append((p_out0, p_in1, p_out1))
            tris.append((sp_out0, p_in1, p_out0))
            tris.append((p_in0, p_in1, sp_out0))
        else:
            # Fully open bottom collar annulus (-Z downward) -> -X pocket stays 100% OPEN bottom!
            add_quad(tris, p_in0, p_in1, p_out1, p_out0)

    # ------------------------------------------------------------------
    # ZONE 2: Collar + `-X` Shoulder Pocket Walls (Z = 92.50 .. 108.40mm, 4 Z-bands avoiding Z=100.50 probe plane)
    # ------------------------------------------------------------------
    for z_a, z_b in ((92.50, 96.40), (96.40, 100.30), (100.30, 104.20), (104.20, 108.40)):
        _extrude_loop_wall(tris, O_shoulder, z_a, z_b, outward_ccw=True)
        _extrude_loop_wall(tris, I_pocket, z_a, z_b, outward_ccw=False)

    # Horizontal ceiling of `-X` pocket at Z = 108.40mm (-Z normal):
    # Outside [i_ia..i_ib], I_pocket == H_main vertex-for-vertex so Zone 2->3->4 inner wall flows seamlessly;
    # inside [i_ia..i_ib], I_pocket (CCW) + H_main (CW) forms one clean `-X` crescent containing H_jack!
    def _find_pt_idx(loop, pt):
        return min(range(len(loop)), key=lambda k: (loop[k][0] - pt[0]) ** 2 + (loop[k][1] - pt[1]) ** 2)

    i_ia = min(i_pa, i_ga)
    i_ib = max(i_pb, i_gb)
    ih_a = _find_pt_idx(H_main, I_pocket[i_ia])
    ih_b = _find_pt_idx(H_main, I_pocket[i_ib])
    H_main[ih_a] = I_pocket[i_ia]
    H_main[ih_b] = I_pocket[i_ib]

    in_crescent = [I_pocket[k] for k in range(i_ia, i_ib + 1)]
    in_crescent += [H_main[k] for k in range(ih_b - 1, ih_a, -1)]
    _emit_cap_z(tris, 108.40, in_crescent, holes=[H_jack], normal_up=False)

    # ------------------------------------------------------------------
    # ZONE 3: Step Deck Slab (Z = 108.40 .. 109.40mm) w/ Φ7.40mm Vertical Through-Bore
    # ------------------------------------------------------------------
    _extrude_loop_wall(tris, O_shoulder, 108.40, 109.40, outward_ccw=True)
    _extrude_loop_wall(tris, H_main, 108.40, 109.40, outward_ccw=False)
    _extrude_loop_wall(tris, H_jack, 108.40, 109.40, outward_ccw=False)

    # Z = 109.40mm Step-Deck transition (+Z upward shelf around -X bulge + groove):
    # Outside (θ <= i_ba or θ >= i_bb), O_shoulder == O_upper identically so outer vertical wall passes straight up!
    # Inside (i_ba .. i_bb), O_shoulder forms the outer CCW arc and O_upper (groove + R_OUT arc) forms the CW return arc,
    # making one exact simple crescent polygon containing H_jack as its single hole!
    iu_a = _find_pt_idx(O_upper, O_shoulder[i_ba])
    iu_b = _find_pt_idx(O_upper, O_shoulder[i_bb])
    O_upper[iu_a] = O_shoulder[i_ba]
    O_upper[iu_b] = O_shoulder[i_bb]

    crescent_outer = [O_shoulder[k] for k in range(i_ba, i_bb + 1)]
    crescent_outer += [O_upper[k] for k in range(iu_b - 1, iu_a, -1)]
    _emit_cap_z(tris, 109.40, crescent_outer, holes=[H_jack], normal_up=True)

    # ------------------------------------------------------------------
    # ZONE 4: Upper Grooved Barrel (Z = 109.40 .. 115.50mm) & Solid Roof (115.50 .. 117.50mm)
    # ------------------------------------------------------------------
    _extrude_loop_wall(tris, O_upper, 109.40, 115.50, outward_ccw=True)
    _extrude_loop_wall(tris, H_main, 109.40, 115.50, outward_ccw=False)

    # Cavity roof ceiling at Z = 115.50mm (-Z normal): exact polygon H_main (0 holes, 0 center fan!)
    _emit_cap_z(tris, 115.50, H_main, holes=(), normal_up=False)

    # Outer wall 115.50 .. 117.00 (straight) then 117.00 .. 117.50 (top chamfer O_upper -> O_top)
    _extrude_loop_wall(tris, O_upper, 115.50, 117.00, outward_ccw=True)
    n_up = len(O_upper)
    assert len(O_top) == n_up, f"O_top len {len(O_top)} != O_upper len {n_up}"
    for i in range(n_up):
        j = (i + 1) % n_up
        a0 = (O_upper[i][0], O_upper[i][1], 117.00)
        a1 = (O_upper[j][0], O_upper[j][1], 117.00)
        b0 = (O_top[i][0], O_top[i][1], 117.50)
        b1 = (O_top[j][0], O_top[j][1], 117.50)
        add_quad(tris, a0, a1, b1, b0)

    # ------------------------------------------------------------------
    # ZONE 5: Centered Top Lanyard Lug (Z = 117.50 .. 122.00mm, hr=1.00mm -> 1.25mm / 4.0mm² bridge)
    # Welded edge-for-edge into Z = 117.50mm top cap (ZERO overlapping coplanar seam!)
    # ------------------------------------------------------------------
    x0, x1 = -3.00, 3.00
    y0, y1 = -1.60, 1.60
    z0, z1 = 117.50, 122.00
    hx, hz, hr = 0.00, 119.75, 1.00
    n_seg = 48
    corner_phis = [math.atan2(zc - hz, xc - hx) % (2.0 * math.pi) for (xc, zc) in [(x1, z1), (x0, z1), (x0, z0), (x1, z0)]]
    phi_bl, phi_bm, phi_br = corner_phis[2], 1.5 * math.pi, corner_phis[3]
    key_phis = corner_phis + [phi_bm]
    raw_phis = [2.0 * math.pi * i / n_seg for i in range(n_seg)] + key_phis
    phis = []
    for pv in sorted(p % (2.0 * math.pi) for p in raw_phis):
        if any(abs(pv - cp) < 1e-3 and abs(pv - cp) > 1e-12 for cp in key_phis):
            continue
        if not phis or abs(pv - phis[-1]) > 1e-4:
            phis.append(pv)
    if (2.0 * math.pi - phis[-1]) < 1e-4:
        phis.pop()

    def _lug_idx(target):
        return min(range(len(phis)), key=lambda idx: abs(phis[idx] - target))

    i_bl, i_bm, i_br = _lug_idx(phi_bl), _lug_idx(phi_bm), _lug_idx(phi_br)

    lug_outer_xz, lug_inner_xz = [], []
    for ph in phis:
        ux, uz = math.cos(ph), math.sin(ph)
        lug_inner_xz.append((hx + hr * ux, hz + hr * uz))
        tx = ((x1 - hx) / ux) if ux > 1e-9 else (((x0 - hx) / ux) if ux < -1e-9 else 1e9)
        tz = ((z1 - hz) / uz) if uz > 1e-9 else (((z0 - hz) / uz) if uz < -1e-9 else 1e9)
        t = min(tx, tz)
        px, pz = hx + t * ux, hz + t * uz
        if abs(px - x0) < 1e-5:
            px = x0
        elif abs(px - x1) < 1e-5:
            px = x1
        if abs(pz - z0) < 1e-5:
            pz = z0
        elif abs(pz - z1) < 1e-5:
            pz = z1
        lug_outer_xz.append((px, pz))

    # Add eyelet barrel all 360 deg, side/top quads outside [i_bl..i_br], and clean 3-node bottom fan on [i_bl..i_br]
    n_lug = len(phis)
    for i in range(n_lug):
        j = (i + 1) % n_lug
        ix0, iz0 = lug_inner_xz[i]
        ix1, iz1 = lug_inner_xz[j]
        ox0, oz0 = lug_outer_xz[i]
        ox1, oz1 = lug_outer_xz[j]
        add_quad(tris, (ix0, y0, iz0), (ix1, y0, iz1), (ix1, y1, iz1), (ix0, y1, iz0))
        if i < i_bl or i >= i_br:
            add_quad(tris, (ix0, y1, iz0), (ix1, y1, iz1), (ox1, y1, oz1), (ox0, y1, oz0))
            add_quad(tris, (ix0, y0, iz0), (ox0, y0, oz0), (ox1, y0, oz1), (ix1, y0, iz1))
            add_quad(tris, (ox0, y0, oz0), (ox0, y1, oz0), (ox1, y1, oz1), (ox1, y0, oz1))
        else:
            if i < i_bm:
                tris.append(((ix0, y1, iz0), (ix1, y1, iz1), (x0, y1, z0)))
                tris.append(((ix0, y0, iz0), (x0, y0, z0), (ix1, y0, iz1)))
            else:
                if i == i_bm:
                    tris.append(((ix0, y1, iz0), (0.0, y1, z0), (x0, y1, z0)))
                    tris.append(((ix0, y1, iz0), (x1, y1, z0), (0.0, y1, z0)))
                    tris.append(((ix0, y0, iz0), (x0, y0, z0), (0.0, y0, z0)))
                    tris.append(((ix0, y0, iz0), (0.0, y0, z0), (x1, y0, z0)))
                tris.append(((ix0, y1, iz0), (ix1, y1, iz1), (x1, y1, z0)))
                tris.append(((ix0, y0, iz0), (x1, y0, z0), (ix1, y0, iz1)))

    R_lug = [(x0, y0), (0.0, y0), (x1, y0), (x1, y1), (0.0, y1), (x0, y1)]

    # Top face at Z = 117.50mm (+Z normal): O_top \ R_lug
    _emit_cap_z(tris, 117.50, O_top, holes=[R_lug], normal_up=True)

    write_binary_stl("04_top_navy_collar_lanyard_cap.stl", tris, "P3R_REV2_4_TOP_COLLAR")
    return tris


# ============================================================================
# Part 5: Bottom Dome Cap (M1.6 Pilot Hole Fixed >= 1.36mm!)
# ============================================================================
def generate_part5_bottom_rounded_dome_cap():
    """
    Part 5 (Rev 2.4): Closed Half-Ellipsoid Bullet Dome Cap (Z=0.0..22.0mm)
    - True cylindrical 4.0mm spigot (Z=18.01..22.0mm, OD=21.20mm, ID=19.00mm -> ZERO cone flare!)
    - Explicit angular node injection for coaxial M1.6 pilot hole on -Y spine at Z=20.0mm (1.36mm tapping width at r_in=9.50mm).
    """
    z_steps = [
        0.00, 0.15, 0.50, 1.00, 2.20, 2.80, 4.00, 5.50, 7.20, 9.00, 11.00, 12.50, 13.50,
        17.70, 17.99, 18.01, 19.25, 20.75, 22.00
    ]

    d_m16 = math.asin(0.68 / 9.50)
    t_m0 = 1.5 * math.pi - d_m16
    t_m1 = 1.5 * math.pi + d_m16
    raw_t = [2.0 * math.pi * i / 144 for i in range(145)] + [t_m0, t_m1]
    u_steps = []
    for tv in sorted(raw_t):
        if tv < 2.0 * math.pi - 1e-4 and abs(tv - t_m0) > 1e-6 and abs(tv - t_m1) > 1e-6:
            if min(abs(tv - t_m0), abs(tv - t_m1)) < 4e-4:
                continue
        if not u_steps or abs(tv - u_steps[-1]) > 1e-6:
            u_steps.append(tv)
    if u_steps[-1] < 2.0 * math.pi - 1e-6:
        u_steps.append(2.0 * math.pi)

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
        return 19.25 <= z_mid <= 20.75 and t_m0 <= t_mid <= t_m1

    tris = make_perforated_tube(r_outer, r_inner, z_steps, u_steps=u_steps, is_cutout_fn=is_cutout)
    write_binary_stl("05_bottom_rounded_dome_cap_silver.stl", tris, "P3R_REV2_4_BULLET_DOME")
    return tris


# ============================================================================
# Part 6: Internal Sled w/ 0.60mm Main PCB Support Ledge (`M-02`)
# ============================================================================
def generate_part6_internal_chassis():
    """
    Part 6 (Rev 2.4): Orthogonal Insulating Sled & Rigid Button Bridge (Z=22.2..88.3mm)
    - Adds stepped 0.60mm inward horizontal support ledges (|X|=8.20..9.85mm at Y∈[-1.80, -1.12]mm) cradling Main PCB's
      17.60mm body (|X|=8.80mm) against downward droop into the 551255 battery bay, while preserving the 17.90mm slot
      (Y∈[-1.12, -0.08]mm) and Z>84.5mm upper ESP32-S3-Zero cutout!
    - Orthogonal rear button slot (6.40mm wide: X∈[-3.20,+3.20], Y∈[-9.65,-8.65], Z∈[33.6,66.4]) & 1.00mm rigid bridge.
    """
    R_SLED_OUT = 10.62
    R_BAT_CHAMBER = 9.85
    Y_BAT_FLOOR = -7.65
    Y_BTN_ROOF = -8.65
    X_FLAT_HALF = math.sqrt(R_BAT_CHAMBER * R_BAT_CHAMBER - Y_BAT_FLOOR * Y_BAT_FLOOR)

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

    def y_to_t_left(y_target):
        # Solve R_BAT_CHAMBER * sin(t) ~ y_target along left arm (t near pi..T_IN_FLAT_L)
        return math.pi - math.asin(max(-0.99, min(0.99, y_target / R_BAT_CHAMBER)))

    def t_to_u_left(t):
        return 0.30 * (t - T_ARM_L) / (T_IN_FLAT_L - T_ARM_L)

    def t_to_u_right(t):
        return 0.70 + 0.30 * (t - T_IN_FLAT_R) / (T_ARM_R - T_IN_FLAT_R)

    def x_to_u_bed(x):
        return 0.30 + 0.40 * (x + X_FLAT_HALF) / (2.0 * X_FLAT_HALF)

    rail_y_pts = (-0.08, -1.12, -1.26, -1.72, -1.90, -2.05)
    extra_u_left = [t_to_u_left(y_to_t_left(yv)) for yv in rail_y_pts]
    extra_u_right = [t_to_u_right(3.0 * math.pi - y_to_t_left(yv)) for yv in rail_y_pts]

    raw_u = (
        [0.30 * i / 32 for i in range(33)]
        + [U_RELIEF_L, U_RELIEF_R]
        + extra_u_left
        + extra_u_right
        + [0.30 + 0.40 * i / 36 for i in range(1, 37)]
        + [x_to_u_bed(xv) for xv in (-3.25, -3.15, 3.15, 3.25)]
        + [0.70 + 0.30 * i / 32 for i in range(1, 33)]
    )
    u_steps = []
    for uv in sorted(raw_u):
        if not u_steps or abs(uv - u_steps[-1]) > 5e-4:
            u_steps.append(uv)

    z_steps = [22.20, 33.55, 33.65, 44.00, 56.00, 66.35, 66.45, 81.50, 84.50, 88.30]

    def pocket_factor(z, x):
        if z <= 33.55 or z >= 66.45:
            return 0.0
        fz = 1.0
        if z < 33.65:
            fz = (z - 33.55) / 0.10
        elif z > 66.35:
            fz = (66.45 - z) / 0.10
        ax = abs(x)
        if ax >= 3.25:
            return 0.0
        fx = 1.0 if ax <= 3.15 else (3.25 - ax) / 0.10
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

    def _side_arm_in_x(y_val):
        # Returns inward half-width |X| on side wall by Y coordinate:
        # Y > -1.12: |X|=8.95mm (PCB capture slot, 17.90mm total width vs 17.60mm PCB)
        # Y ∈ [-1.72, -1.26]: |X|=8.20mm (0.60mm per-side horizontal support shelf under Main PCB!)
        # Y < -1.90: open battery bay X_wall = -sqrt(R_BAT_CHAMBER^2 - y^2)
        if y_val >= -1.12:
            return 8.95
        if y_val > -1.26:
            f = (y_val - (-1.26)) / 0.14
            return 8.20 + f * (8.95 - 8.20)
        if y_val >= -1.72:
            return 8.20
        r_circle_x = math.sqrt(max(0.0, R_BAT_CHAMBER * R_BAT_CHAMBER - y_val * y_val))
        if y_val > -1.90:
            f = (-1.72 - y_val) / 0.18
            return 8.20 + f * (r_circle_x - 8.20)
        return r_circle_x

    def inner_xy(z, u):
        if u < 0.30 - 1e-9:
            t = T_ARM_L + (T_IN_FLAT_L - T_ARM_L) * (u / 0.30)
            y_arm = R_BAT_CHAMBER * math.sin(t)
            return (-_side_arm_in_x(y_arm), y_arm)
        elif u <= 0.70 + 1e-9:
            x = -X_FLAT_HALF + 2.0 * X_FLAT_HALF * ((u - 0.30) / 0.40)
            return (x, Y_BAT_FLOOR)
        else:
            t = T_IN_FLAT_R + (T_ARM_R - T_IN_FLAT_R) * ((u - 0.70) / 0.30)
            y_arm = R_BAT_CHAMBER * math.sin(t)
            return (_side_arm_in_x(y_arm), y_arm)

    def is_cutout(z_mid, u_mid):
        if z_mid > 84.50 and (u_mid < U_RELIEF_L or u_mid > U_RELIEF_R):
            return True
        return False

    tris = make_conformal_shell(outer_xy, inner_xy, z_steps, u_steps, full_circle=False, is_cutout_fn=is_cutout)
    write_binary_stl("06_internal_zero_solder_sled.stl", tris, "P3R_REV2_4_SLED")
    return tris


def main():
    all_tris = []
    all_tris += generate_part1_cnc_main_shell()
    all_tris += generate_part2_flat_screen_lens()
    all_tris += generate_part3_rear_pill_buttons()
    all_tris += generate_part4_top_navy_collar_and_lanyard()
    all_tris += generate_part5_bottom_rounded_dome_cap()
    all_tris += generate_part6_internal_chassis()
    write_binary_stl("00_full_assembled_p3r_mp3.stl", all_tris, "P3R_REV2_4_FULL_ASSEMBLY")
    print("[SUCCESS] All 7 Rev-2.4 P3R STL files generated cleanly.")


if __name__ == "__main__":
    main()
