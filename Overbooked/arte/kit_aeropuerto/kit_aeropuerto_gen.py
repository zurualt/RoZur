import bpy
import bmesh
import math
import os
import sys
import json
import bisect
import random
from mathutils import Vector, Matrix, Euler

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]


def arg(name, default=None):
    if name in ARGS:
        i = ARGS.index(name)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return default


PAL = [
    ("cream", "FFF4E0"), ("orange", "F27B2B"), ("teal", "1FA6A0"), ("dark", "34383F"),
    ("black", "1B1B21"), ("white", "F7F7F2"), ("red", "D9443A"), ("yellow", "F6C445"),
    ("metal", "A9B0B8"), ("glass", "8FD3F4"), ("leaf", "7CC24A"), ("dleaf", "3D9447"),
    ("trunk", "8A5A33"), ("tile", "E9DCC4"), ("dteal", "157F7B"), ("concrete", "CDD1D4"),
]
IDX = {n: i for i, (n, _) in enumerate(PAL)}


def suv(n):
    i = IDX[n]
    return ((i % 4 + 0.5) / 4.0, (i // 4 + 0.5) / 4.0)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def V(*a):
    return Vector(a[0] if len(a) == 1 else a)


def M(loc=(0, 0, 0), rot=(0, 0, 0), scl=None):
    m = Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot], "XYZ").to_matrix().to_4x4()
    if scl is not None:
        m = m @ Matrix.Diagonal((scl[0], scl[1], scl[2], 1.0))
    return m


def xf(bm, m):
    if m is None:
        return bm
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    if m.to_3x3().determinant() < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return bm


def frame(origin, ex, ey):
    ex = Vector(ex).normalized()
    ey = Vector(ey).normalized()
    ez = ex.cross(ey).normalized()
    m = Matrix((ex, ey, ez)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


def yzx(loc=(0, 0, 0)):
    m = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    m.translation = Vector(loc)
    return m


def frame_from_normal(n):
    n = Vector(n).normalized()
    x = Vector((0, 0, 1)).cross(n)
    if x.length < 1e-4:
        x = Vector((1, 0, 0))
    x.normalize()
    y = n.cross(x).normalized()
    return Matrix((x, y, n)).transposed().to_4x4()


def bevel_edges(bm, edges, off, seg=1):
    if edges:
        bmesh.ops.bevel(bm, geom=list(edges) + list({v for e in edges for v in e.verts}), offset=off, offset_type="OFFSET",
                        segments=seg, profile=0.5, affect="EDGES", clamp_overlap=True)
    return bm


def bevel_sharp(bm, off, seg=1, ang=50):
    bm.normal_update()
    es = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(ang)]
    return bevel_edges(bm, es, off, seg)


def rbox(size, loc=(0, 0, 0), bev=0.0, seg=1, rot=(0, 0, 0), m=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bev > 0:
        bevel_edges(bm, list(bm.edges), bev, seg)
    mm = M(loc, rot)
    return xf(bm, m @ mm if m is not None else mm)


def bb(x0, x1, y0, y1, z0, z1, bev=0.0, seg=1, m=None):
    return rbox((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), bev, seg, m=m)


def lathe(prof, seg=12, m=None, sx=1.0, sy=1.0, cap0=True, cap1=True, closed=False, a0=None):
    if a0 is None:
        a0 = math.pi / (2 * seg) if seg % 4 == 2 else 0.0
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r < 1e-6:
            rings.append([bm.verts.new((0.0, 0.0, z))])
        else:
            rings.append([bm.verts.new((sx * r * math.cos(a0 + 2 * math.pi * j / seg), sy * r * math.sin(a0 + 2 * math.pi * j / seg), z)) for j in range(seg)])
    n = len(rings)
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
    for i, k in pairs:
        a, b = rings[i], rings[k]
        if len(a) == 1 and len(b) == 1:
            continue
        for j in range(seg):
            j2 = (j + 1) % seg
            if len(a) == 1:
                bm.faces.new((a[0], b[j2], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[j], a[j2], b[0]))
            else:
                bm.faces.new((a[j], a[j2], b[j2], b[j]))
    if not closed:
        if cap0 and len(rings[0]) > 1:
            bm.faces.new(list(reversed(rings[0])))
        if cap1 and len(rings[-1]) > 1:
            bm.faces.new(rings[-1])
    return xf(bm, m)


def cyl(r, h, loc=(0, 0, 0), rot=(0, 0, 0), seg=12, r2=None, bev=0.0, center=False, m=None, cap0=True, cap1=True):
    z0 = -h / 2 if center else 0.0
    rt = r if r2 is None else r2
    if bev > 0:
        prof = [(r - bev, z0), (r, z0 + bev), (rt, z0 + h - bev), (rt - bev, z0 + h)]
    else:
        prof = [(r, z0), (rt, z0 + h)]
    mm = M(loc, rot)
    return lathe(prof, seg, m @ mm if m is not None else mm, cap0=cap0, cap1=cap1)


def rr_pts(w, d, r, cs):
    hw, hd = w / 2, d / 2
    if cs <= 0 or r <= 1e-6:
        return [(hw, hd), (-hw, hd), (-hw, -hd), (hw, -hd)]
    r = min(r, hw - 1e-3, hd - 1e-3)
    pts = []
    for cx, cy, a0 in ((hw - r, hd - r, 0), (-(hw - r), hd - r, 90), (-(hw - r), -(hd - r), 180), (hw - r, -(hd - r), 270)):
        for k in range(cs + 1):
            a = math.radians(a0 + 90.0 * k / cs)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def rr_loft(w, d, r, cs, prof, m=None, cap0=True, cap1=True, closed=False):
    bm = bmesh.new()
    rings = []
    for ins, z in prof:
        rr = max(r - ins, 0.004) if cs > 0 else 0.0
        rings.append([bm.verts.new((x, y, z)) for x, y in rr_pts(w - 2 * ins, d - 2 * ins, rr, cs)])
    N = len(rings[0])
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for a, b in pairs:
        for j in range(N):
            j2 = (j + 1) % N
            bm.faces.new((a[j], a[j2], b[j2], b[j]))
    if not closed:
        if cap0:
            bm.faces.new(list(reversed(rings[0])))
        if cap1:
            bm.faces.new(rings[-1])
    return xf(bm, m)


def bar(p0, p1, w, t, ch=0.0, up=(0, 0, 1), caps=True):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    z = d / L
    x = Vector(up).cross(z)
    if x.length < 1e-6:
        x = Vector((1, 0, 0)).cross(z) if abs(z.x) < 0.9 else Vector((0, 1, 0)).cross(z)
    x.normalize()
    y = z.cross(x).normalized()
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = p0
    if ch > 0:
        return rr_loft(w, t, ch, 1, [(0.0, 0.0), (0.0, L)], m, caps, caps)
    return rr_loft(w, t, 0.0, 0, [(0.0, 0.0), (0.0, L)], m, caps, caps)


def area2(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))


def prism(pts, t, m=None, bev=0.0, bseg=1, z0=None):
    if area2(pts) < 0:
        pts = pts[::-1]
    z0 = -t / 2 if z0 is None else z0
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]
    hi = [bm.verts.new((x, y, z0 + t)) for x, y in pts]
    n = len(pts)
    for j in range(n):
        j2 = (j + 1) % n
        bm.faces.new((lo[j], lo[j2], hi[j2], hi[j]))
    f0 = bm.faces.new(list(reversed(lo)))
    f1 = bm.faces.new(hi)
    if bev > 0:
        bevel_edges(bm, [e for e in bm.edges if f0 in e.link_faces or f1 in e.link_faces], bev, bseg)
    return xf(bm, m)


def decal(pts, m=None, w=0.0):
    if area2(pts) < 0:
        pts = pts[::-1]
    bm = bmesh.new()
    bm.faces.new([bm.verts.new((x, y, w)) for x, y in pts])
    return xf(bm, m)


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def circ(cx, cy, r, n=10, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * k / n), cy + r * math.sin(a0 + 2 * math.pi * k / n)) for k in range(n)]


def arc_strip(cx, cy, r0, r1, a0, a1, n, m=None, w=0.0):
    bm = bmesh.new()
    inner, outer = [], []
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        inner.append(bm.verts.new((cx + r0 * math.cos(a), cy + r0 * math.sin(a), w)))
        outer.append(bm.verts.new((cx + r1 * math.cos(a), cy + r1 * math.sin(a), w)))
    for k in range(n):
        bm.faces.new((inner[k], outer[k], outer[k + 1], inner[k + 1]))
    return xf(bm, m)


def ellipsoid(radii, mat=Matrix(), u=12, v=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.transform(bm, matrix=mat @ Matrix.Diagonal((*radii, 1.0)), verts=bm.verts)
    return bm


def catmull(points, steps, closed=False):
    n = len(points)
    out = []
    segs = n if closed else n - 1
    for i in range(segs):
        p0 = points[(i - 1) % n] if (closed or i > 0) else points[i]
        p1 = points[i % n]
        p2 = points[(i + 1) % n]
        p3 = points[(i + 2) % n] if (closed or i + 2 < n) else points[(i + 1) % n]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(points[-1].copy())
    return out


def tube(ctrl, rf, k=8, steps=4, closed=False, up=None, caps=True, cap_rings=2):
    ctrl = [Vector(c) for c in ctrl]
    path = catmull(ctrl, steps, closed)
    n = len(path)
    seglen = [0.0]
    for i in range(1, n):
        seglen.append(seglen[-1] + (path[i] - path[i - 1]).length)
    total = seglen[-1] + ((path[0] - path[-1]).length if closed else 0.0)
    tangents = []
    for i in range(n):
        if closed:
            t = path[(i + 1) % n] - path[(i - 1) % n]
        elif i == 0:
            t = path[1] - path[0]
        elif i == n - 1:
            t = path[-1] - path[-2]
        else:
            t = path[i + 1] - path[i - 1]
        tangents.append(t.normalized())
    hint = up if up is not None else Vector((0, 0, 1))
    nrm = hint - tangents[0] * hint.dot(tangents[0])
    if nrm.length < 1e-4:
        nrm = Vector((1, 0, 0)) - tangents[0] * tangents[0].x
    nrm.normalize()
    normals = [nrm]
    for i in range(1, n):
        q = tangents[i - 1].rotation_difference(tangents[i])
        normals.append((q @ normals[-1]).normalized())
    bm = bmesh.new()
    rings = []
    for i in range(n):
        u = seglen[i] / total if total > 0 else 0.0
        r = rf(u)
        b = tangents[i].cross(normals[i]).normalized()
        rings.append([bm.verts.new(path[i] + (normals[i] * math.cos(2 * math.pi * j / k) + b * math.sin(2 * math.pi * j / k)) * r) for j in range(k)])
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
    for a_i, b_i in pairs:
        ra, rb = rings[a_i], rings[b_i]
        for j in range(k):
            bm.faces.new((ra[j], ra[(j + 1) % k], rb[(j + 1) % k], rb[j]))
    if caps and not closed:
        for end in (0, n - 1):
            d = -tangents[0] if end == 0 else tangents[-1]
            r_end = rf(0.0 if end == 0 else 1.0)
            b = tangents[end].cross(normals[end]).normalized()
            prev = rings[end]
            for c in range(1, cap_rings + 1):
                phi = (math.pi / 2) * c / cap_rings
                center = path[end] + d * r_end * math.sin(phi)
                if c == cap_rings:
                    pole = bm.verts.new(center)
                    for j in range(k):
                        bm.faces.new((prev[j], prev[(j + 1) % k], pole))
                    break
                rr = r_end * math.cos(phi)
                ring = [bm.verts.new(center + (normals[end] * math.cos(2 * math.pi * j / k) + b * math.sin(2 * math.pi * j / k)) * rr) for j in range(k)]
                for j in range(k):
                    bm.faces.new((prev[j], prev[(j + 1) % k], ring[(j + 1) % k], ring[j]))
                prev = ring
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def slab_grid(n, s, t, zf, m=None):
    bm = bmesh.new()
    xs = [-s + 2 * s * i / (n - 1) for i in range(n)]
    top = [[bm.verts.new((x, y, zf(x, y))) for x in xs] for y in xs]
    bot = [[bm.verts.new((x, y, zf(x, y) - t)) for x in xs] for y in xs]
    for j in range(n - 1):
        for i in range(n - 1):
            bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
            bm.faces.new((bot[j][i], bot[j + 1][i], bot[j + 1][i + 1], bot[j][i + 1]))
    ring = [(i, 0) for i in range(n)] + [(n - 1, j) for j in range(1, n)] + [(i, n - 1) for i in range(n - 2, -1, -1)] + [(0, j) for j in range(n - 2, 0, -1)]
    for k in range(len(ring)):
        (ia, ja), (ib, jb) = ring[k], ring[(k + 1) % len(ring)]
        bm.faces.new((bot[ja][ia], bot[jb][ib], top[jb][ib], top[ja][ia]))
    return xf(bm, m)




class Prop:
    def __init__(self, name, size, budget):
        self.name = name
        self.size = size
        self.budget = budget
        self.parts = []

    def add(self, bm, role, ang=50.0):
        self.parts.append((bm, role, ang))
        return bm


FR = {"-y": ((1, 0, 0), (0, 0, 1)), "+y": ((-1, 0, 0), (0, 0, 1)), "+x": ((0, 1, 0), (0, 0, 1)),
      "-x": ((0, -1, 0), (0, 0, 1)), "+z": ((1, 0, 0), (0, 1, 0)), "-z": ((1, 0, 0), (0, -1, 0))}


def fr(o, side):
    ex, ey = FR[side]
    return frame(o, ex, ey)


def pill(cx, cy, L, h, a=0.0, n=3):
    pts = []
    for k in range(n + 1):
        t = -math.pi / 2 + math.pi * k / n
        pts.append((L / 2 + h * math.cos(t), h * math.sin(t)))
    for k in range(n + 1):
        t = math.pi / 2 + math.pi * k / n
        pts.append((-L / 2 + h * math.cos(t), h * math.sin(t)))
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def rrect(cx, cy, w, h, r, cs=2):
    return [(cx + x, cy + y) for x, y in rr_pts(w, h, r, cs)]


def logo(p, m, r, base=True, step=None, seg=20):
    st = step if step is not None else max(0.006, 0.004 * r)
    w = 0.0
    if base:
        p.add(decal(circ(0, 0, r, seg), m, w), "cream")
        w += st
    p.add(decal(circ(0, 0, r * 0.82, seg), m, w), "orange")
    w += st
    for ln, dy, dx in ((0.6, 0.3, -0.12), (0.46, 0.0, 0.02), (0.32, -0.3, 0.14)):
        p.add(decal(pill(dx * r, dy * r, ln * r, 0.085 * r, math.radians(24)), m, w), "cream")


def blob(r, loc, sub=2, jit=0.0, seed=0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    rnd = random.Random(seed)
    for v in bm.verts:
        v.co *= 1.0 + rnd.uniform(-jit, jit)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(loc)) @ Matrix.Diagonal((r[0], r[1], r[2], 1.0)), verts=bm.verts)
    return bm


def gridplane(xs, ys, z, m=None):
    bm = bmesh.new()
    vs = [[bm.verts.new((x, y, z)) for x in xs] for y in ys]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    return xf(bm, m)


def wheel(p, c, r, w, axis="x", tire="black", hub="metal", seg=12, rh=None, detail=True):
    m = M(c, (0, 90, 0) if axis == "x" else (90, 0, 0))
    rh = rh if rh is not None else r * 0.62
    if detail:
        prof = [(rh, -w / 2), (r * 0.93, -w / 2), (r, -w / 2 + 0.08 * w), (r, w / 2 - 0.08 * w), (r * 0.93, w / 2), (rh, w / 2)]
    else:
        prof = [(rh, -w / 2), (r, -w / 2 + 0.12 * w), (r, w / 2 - 0.12 * w), (rh, w / 2)]
    a0 = 0.0 if axis == "x" else math.radians(270.0 % (360.0 / seg))
    p.add(lathe(prof, seg, m, cap0=False, cap1=False, a0=a0), tire)
    p.add(cyl(rh, w * 0.86, seg=seg if detail else max(6, seg - 2), center=True, m=m), hub)


def ring(p, c, R, rt, seg, role, rot=(0, 0, 0), n=4):
    prof = [(R + rt * math.cos(2 * math.pi * k / n + math.pi / n), rt * math.sin(2 * math.pi * k / n + math.pi / n)) for k in range(n)]
    p.add(lathe(prof, seg, M(c, rot), closed=True), role)


TERM = {}


def p_terminal():
    p = Prop("Terminal", (54.0, 54.0, 15.0), 9000)
    H0, FL = 0.48, 0.5
    WO, WI = 26.5, 25.7
    FY0, FY1 = -25.4, -24.6
    SO, CE, DK = 12.6, 13.2, 14.2
    slab = [(-27, -27), (-8.6, -27), (-8.6, -25.4), (8.6, -25.4), (8.6, -27), (27, -27), (27, 27), (-27, 27)]
    p.add(prism(slab, H0, M((0, 0, H0 / 2)), bev=0.06), "concrete")
    p.add(prism([(-27, 0.0), (-25.4, 0.0), (-25.4, H0), (-27, 0.05)], 17.2, yzx((0, 0, 0))), "concrete")
    xc = [-WI] + [-25.0 + 50.0 * i / 12 for i in range(13)] + [WI]
    yc = [FY0, FY1, -23.9] + [-23.9 + 48.9 * i / 12 for i in range(1, 13)] + [WI]

    def tile(c, n):
        i = bisect.bisect(xc, c.x) - 1
        j = bisect.bisect(yc, c.y) - 1
        if i <= 0 or i >= len(xc) - 2 or j <= 1 or j >= len(yc) - 2:
            return "dteal"
        return "cream" if (i + j) % 2 else "tile"
    p.add(gridplane(xc, yc, FL), tile)
    p.add(decal(rrect(0, -21.6, 11.0, 3.0, 0.5), M((0, 0, FL + 0.01))), "dteal")
    p.add(decal(rrect(0, -21.6, 10.2, 2.2, 0.3), M((0, 0, FL + 0.02))), "teal")
    for s in (-1, 1):
        x0, x1 = sorted((s * WI, s * WO))
        p.add(bb(x0, x1, -26.6, 26.2, H0, 13.25), "cream")
    BX, BZ0, BZ1 = 9.3, 2.7, 12.3
    p.add(bb(-26.2, -BX, WI, WO, H0, 13.25), "cream")
    p.add(bb(BX, 26.2, WI, WO, H0, 13.25), "cream")
    p.add(bb(-BX, BX, WI, WO, H0, BZ0), "cream")
    p.add(bb(-BX, BX, WI, WO, BZ1, 13.25), "cream")
    p.add(bb(-10.2, 10.2, WO, 26.85, 1.9, SO, 0.14, 2), lambda c, n: "dark" if n.y < -0.5 else "teal")
    logo(p, fr((0, 26.85, 7.25), "+y"), 3.4, step=0.012)
    p.add(bb(-10.0, 10.0, WI - 0.14, WI, BZ0 - 0.5, BZ0, 0.05, 1), "orange")
    for sx in (-1, 1):
        for sy in (-1, 1):
            xs = sorted((sx * WI, sx * 26.9))
            ys = sorted((sy * WI, sy * 26.9))
            p.add(bb(xs[0], xs[1], ys[0], ys[1], H0, SO, 0.3, 2), "white")
    for s in (-1, 1):
        x0, x1 = sorted((s * WO, s * 26.85))
        for y in (-15.6, -5.2, 5.2, 15.6):
            p.add(bb(x0, x1, y - 0.5, y + 0.5, H0, SO, 0.12, 2), "white")
        x0, x1 = sorted((s * WO, s * 26.62))
        p.add(bb(x0, x1, -26.6, 26.6, H0, 1.5, 0.05, 1), "teal")
        p.add(bb(s * 17.9 - 0.5, s * 17.9 + 0.5, WO, 26.85, H0, SO, 0.12, 2), "white")
        p.add(cyl(2.2, 0.08, (s * WO, 0, 8.2), (0, s * 90, 0), seg=20), "cream")
        logo(p, fr((s * (WO + 0.08), 0, 8.2), "+x" if s > 0 else "-x"), 2.2, base=False, step=0.01)
    p.add(bb(-26.6, 26.6, WO, 26.62, H0, 1.5, 0.05, 1), "teal")
    for s in (-1, 1):
        x0, x1 = sorted((s * (WI - 0.1), s * WI))
        p.add(bb(x0, x1, FY1, WI, FL, 2.0), "teal")
        x0, x1 = sorted((s * (WI - 0.16), s * WI))
        p.add(bb(x0, x1, FY1, WI, 2.0, 2.18, 0.04, 1), "white")
    p.add(bb(-(WI - 0.1), WI - 0.1, WI - 0.1, WI, FL, 2.0), "teal")
    p.add(bb(-(WI - 0.16), WI - 0.16, WI - 0.16, WI, 2.0, 2.18, 0.04, 1), "white")

    def fm(x0, x1, z0, z1, col="dteal"):
        p.add(bb(x0, x1, FY0, FY1, z0, z1, 0.06, 1), col)
    fm(-WI, -8.2, 12.0, SO)
    fm(8.2, WI, 12.0, SO)
    panes = []
    for s in (-1, 1):
        x0, x1 = sorted((s * 8.2, s * WI))
        fm(x0, x1, FL, 1.2)
        fm(x0, x1, 10.0, 10.3)
        x0, x1 = sorted((s * 25.4, s * WI))
        fm(x0, x1, 1.2, 12.0)
        for k in range(1, 5):
            x = s * (8.2 + 3.5 * k - 0.15)
            fm(x - 0.15, x + 0.15, 1.2, 12.0)
        for b in range(5):
            u0, u1 = 8.2 + 3.5 * b, 8.2 + 3.5 * b + 3.2
            x0, x1 = sorted((s * u0, s * u1))
            panes.append((x0, x1, 1.2, 10.0))
            panes.append((x0, x1, 10.3, 12.0))
        x0, x1 = sorted((s * 7.5, s * 8.2))
        p.add(bb(x0, x1, -25.6, -24.4, FL, 10.0, 0.1, 2), "teal")
    TERM["panes"] = panes
    TERM["glass_y"] = -25.0
    p.add(bb(-8.2, 8.2, -25.6, -24.4, 10.0, SO, 0.1, 2), "teal")

    def canopy(c, n):
        if n.z < -0.6:
            return "white"
        return "cream" if n.z > 0.6 else "orange"
    p.add(bb(-9.4, 9.4, -27.0, -25.5, 10.0, 10.55, 0.2, 2), canopy)
    for x in (-6.0, -2.0, 2.0, 6.0):
        p.add(decal(circ(x, 0, 0.22, 8), fr((0, -26.25, 10.0), "-z"), 0.006), "yellow")
    for s in (-1, 1):
        p.add(bar((s * 8.8, -26.55, 10.5), (s * 8.8, -25.9, SO + 0.05), 0.12, 0.12), "dark")
    p.add(bb(-WO, WO, -26.3, -24.4, SO, CE), "white")
    p.add(bb(-26.4, 26.4, -26.4, 26.4, CE, DK), lambda c, n: "metal" if n.z > 0.5 else "tile")
    prof = [(0.0, SO), (0.0, 13.35), (0.0, 14.1), (0.0, 14.6), (0.07, 14.9), (0.25, 15.0), (0.45, 15.0), (0.6, 14.88), (0.6, SO)]

    def fascia(c, n):
        if n.z > 0.5 and c.z > 14.8:
            return "white"
        if n.z < -0.5:
            return "white"
        if max(abs(c.x), abs(c.y)) < 26.45:
            return "concrete"
        if 13.35 < c.z < 14.1:
            return "orange"
        return "cream"
    p.add(rr_loft(53.8, 53.8, 0.6, 2, prof, closed=True), fascia)
    p.add(cyl(1.05, 0.08, (0, -26.9, 13.72), (90, 0, 0), seg=20), "cream")
    logo(p, fr((0, -26.98, 13.72), "-y"), 1.05, base=False, step=0.005)
    for y in (-14.4, -4.2, 6.0, 16.2):
        p.add(bb(-WI, WI, y - 0.3, y + 0.3, 12.45, CE, 0.06, 1), "teal")
    for y in (-19.3, -9.3, 0.9, 11.1, 21.0):
        for x in (-18.0, -9.0, 0.0, 9.0, 18.0):
            p.add(decal(rrect(x, -y, 4.0, 1.4, 0.4), fr((0, 0, CE), "-z"), 0.01), "white")
    for x, y in ((-9.0, -11.0), (9.0, 11.0)):
        p.add(bb(x - 7.0, x + 7.0, y - 1.5, y + 1.5, DK, 14.5, 0.1, 1), lambda c, n: "glass" if n.z > 0.5 else "white")
    for x, y in ((-17.5, 9.0), (16.5, -9.5), (-4.0, 18.5)):
        p.add(bb(x - 1.6, x + 1.6, y - 1.1, y + 1.1, DK, 14.8, 0.12, 2), "white")
        p.add(decal(circ(x - 0.6, y, 0.62, 12), M((0, 0, 14.8)), 0.006), "dark")
        p.add(decal(circ(x - 0.6, y, 0.18, 6), M((0, 0, 14.8)), 0.012), "metal")
        p.add(decal(rrect(x + 0.95, y, 0.6, 1.4, 0.1, 1), M((0, 0, 14.8)), 0.006), "metal")
    return p


def p_mostrador():
    p = Prop("Mostrador", (6.0, 3.0, 3.5), 800)
    p.add(bb(-2.9, 0.9, -1.3, 1.4, 0.0, 0.25), "dark")
    p.add(bb(-3.0, 1.0, -1.4, 1.5, 0.22, 2.32, 0.12, 2), "teal")
    p.add(bb(-2.75, 0.75, -1.47, -1.36, 0.55, 1.98, 0.05, 1), "cream")
    logo(p, fr((-1.0, -1.47, 1.27), "-y"), 0.42, base=False, step=0.006)
    p.add(bb(-2.98, 0.98, -1.44, 1.48, 2.28, 2.42, 0.04, 1), "orange")
    p.add(bb(-3.0, 1.0, -0.55, 1.5, 2.4, 2.5, 0.04, 1), "white")
    p.add(bb(-3.0, 1.0, -1.5, -0.5, 2.4, 2.8, 0.1, 2), "white")
    p.add(bb(-1.5, -0.9, 0.15, 0.65, 2.5, 2.6, 0.04, 1), "dark")
    p.add(bb(-1.29, -1.11, 0.32, 0.48, 2.58, 2.8), "dark")
    p.add(bb(-1.95, -0.45, 0.32, 0.46, 2.75, 3.5, 0.05, 1), "dark")
    p.add(decal(rrect(0, 3.125, 1.3, 0.6, 0.06, 1), fr((-1.2, 0.46, 0), "+y"), 0.006), "glass")
    p.add(decal(rrect(-1.2, 1.0, 1.2, 0.36, 0.05, 1), M((0, 0, 2.5)), 0.006), "dark")
    p.add(bb(-2.75, -2.15, 0.6, 1.3, 2.5, 2.78, 0.04, 1), "metal")
    p.add(decal(rect(-2.68, -2.22, 0.6, 1.25), M((0, 0, 2.78)), 0.006), "dark")
    p.add(bb(1.05, 3.0, -1.45, 1.45, 0.0, 0.72, 0.08, 1), "dark")
    p.add(bb(1.2, 2.85, -1.42, 1.42, 0.7, 0.8), "black")
    for y in (-1.05, -0.6, -0.15, 0.3, 0.75, 1.2):
        p.add(decal(rect(1.22, 2.83, y - 0.03, y + 0.03), M((0, 0, 0.8)), 0.004), "dark")
    for x0, x1 in ((1.05, 1.22), (2.83, 3.0)):
        p.add(bb(x0, x1, -1.5, 1.5, 0.55, 0.98, 0.04, 1), "metal")
    p.add(bb(1.0, 1.08, -1.25, -0.25, 1.25, 1.95, 0.03, 1), "cream")
    p.add(decal(rect(-1.15, -0.35, 1.36, 1.84), fr((1.08, 0, 0), "+x"), 0.005), "black")
    p.add(decal(rect(-1.05, -0.45, 1.44, 1.76), fr((1.08, 0, 0), "+x"), 0.01), "glass")
    return p


def p_banco():
    p = Prop("BancoEspera", (10.0, 2.0, 2.2), 1200)
    p.add(bb(-4.95, 4.95, -0.15, 0.25, 0.78, 1.0, 0.06, 1), "metal")
    seat = [(-0.95, 1.14), (-0.2, 1.08), (0.36, 1.12), (0.58, 1.3), (0.8, 1.78), (0.95, 2.2), (0.76, 2.2),
            (0.6, 1.8), (0.4, 1.4), (0.2, 1.32), (-0.62, 1.34), (-0.86, 1.34), (-0.97, 1.27)]
    for i in range(5):
        c = -4.0 + 2.0 * i
        bm = prism(seat, 1.84, yzx((c, 0, 0)))
        bevel_sharp(bm, 0.05, 1, 30)
        p.add(bm, "orange", 40)
        p.add(bb(c - 0.35, c + 0.35, -0.28, 0.32, 0.98, 1.12), "dark")
    for x in (-3.0, 3.0):
        p.add(bb(x - 0.12, x + 0.12, -0.06, 0.16, 0.1, 0.8), "metal")
        p.add(bb(x - 0.15, x + 0.15, -1.0, 1.0, 0.0, 0.12, 0.05, 1), "dark")
    for x in (-4.92, -3.0, -1.0, 1.0, 3.0, 4.92):
        p.add(bar((x, 0.05, 0.98), (x, 0.05, 1.64), 0.1, 0.12, caps=False), "dark")
        p.add(bb(x - 0.08, x + 0.08, -0.72, 0.32, 1.62, 1.74, 0.04, 1), "dark")
    return p


def p_kiosko():
    p = Prop("Kiosko", (2.4, 2.4, 3.0), 600)
    p.add(bb(-1.2, 1.2, -1.2, 1.2, 0.0, 0.25, 0.08, 1), "dark")
    p.add(rr_loft(1.8, 1.8, 0.3, 2, [(0.0, 0.25), (0.0, 2.0)], cap0=False, cap1=False), "teal")
    p.add(rr_loft(1.86, 1.86, 0.32, 2, [(0.0, 1.62), (0.0, 1.78)], cap0=False, cap1=False), "orange")
    p.add(decal(rrect(0, 1.0, 0.9, 1.0, 0.12, 1), fr((0, -0.9, 0), "-y"), 0.006), "cream")
    logo(p, fr((0, -0.912, 1.12), "-y"), 0.3, base=False, step=0.005)
    p.add(decal(rrect(0, 0.62, 0.6, 0.08, 0.03, 1), fr((0, -0.9, 0), "-y"), 0.012), "black")
    head = [(-1.2, 1.95), (1.2, 1.95), (1.2, 3.0), (-0.84, 3.0), (-1.2, 2.45)]
    bm = prism(head, 2.4, yzx((0, 0, 0)))
    bevel_sharp(bm, 0.05, 2, 30)
    p.add(bm, lambda c, n: "dteal" if n.z < -0.5 else "cream", 40)
    a = Vector((0, 0.36, 0.55)).normalized()
    m = frame((0, -1.02, 2.725), (1, 0, 0), a)
    p.add(decal(rrect(0, 0, 2.05, 0.44, 0.06, 1), m, 0.006), "black")
    p.add(decal(rrect(0, 0, 1.85, 0.32, 0.04, 1), m, 0.012), "glass")
    return p


def p_marco():
    p = Prop("MarcoTablero", (18.6, 0.8, 9.6), 300)
    m = frame((0, 0.4, 4.8), (1, 0, 0), (0, 0, 1))
    prof = [(0.0, 0.0), (0.0, 0.72), (0.07, 0.8), (0.23, 0.8), (0.3, 0.72), (0.3, 0.0)]

    def role(c, n):
        return "orange" if n.y < -0.8 else "dark"
    p.add(rr_loft(18.6, 9.6, 0.3, 2, prof, m, closed=True), role)
    p.add(bb(-9.0, 9.0, 0.2, 0.4, 0.3, 9.3), "black")
    return p


def p_torre():
    p = Prop("TorreControl", (10.0, 10.0, 40.0), 3000)
    p.add(rr_loft(8.0, 8.0, 0.9, 2, [(0.0, 0.0), (0.0, 0.9), (0.0, 3.7), (0.12, 3.92), (0.4, 4.0)], cap0=False),
          lambda c, n: "concrete" if n.z > 0.9 else ("teal" if c.z < 0.9 else "cream"))
    md = fr((0, -4.0, 0), "-y")
    p.add(decal(rrect(0, 1.38, 1.9, 2.76, 0.2, 1), md, 0.01), "dteal")
    p.add(decal(rrect(0, 1.32, 1.5, 2.5, 0.15, 1), md, 0.02), "dark")
    p.add(bb(-1.4, 1.4, -4.65, -3.95, 2.9, 3.12, 0.06, 1), "orange")
    for sx, side in ((1, "+x"), (-1, "-x")):
        for y in (-1.8, 1.8):
            mw = fr((sx * 4.0, 0, 0), side)
            p.add(decal(rrect(y * sx, 2.3, 1.3, 1.1, 0.2, 1), mw, 0.01), "white")
            p.add(decal(rrect(y * sx, 2.3, 1.06, 0.86, 0.14, 1), mw, 0.02), "glass")
    for x in (-2.3, 2.3):
        p.add(decal(rrect(x, 2.3, 1.3, 1.1, 0.2, 1), md, 0.01), "white")
        p.add(decal(rrect(x, 2.3, 1.06, 0.86, 0.14, 1), md, 0.02), "glass")
    a0 = math.pi / 12
    prof = [(2.7, 3.95), (2.45, 4.6), (2.15, 5.4), (2.1, 6.2), (2.1, 25.4), (2.1, 26.4), (2.1, 28.2)]
    p.add(lathe(prof, 12, cap0=False, cap1=False, a0=a0),
          lambda c, n: "teal" if c.z < 6.2 else ("orange" if 25.4 < c.z < 26.4 else "cream"))
    ap = 2.1 * math.cos(math.pi / 12)
    for z in (8.5, 12.0, 15.5, 19.0, 22.5):
        p.add(decal(pill(0, z, 1.0, 0.2, math.pi / 2), fr((0, -ap, 0), "-y"), 0.012), "glass")
        p.add(decal(pill(0, z, 1.0, 0.2, math.pi / 2), fr((0, ap, 0), "+y"), 0.012), "glass")
    p.add(lathe([(2.1, 28.0), (2.6, 29.0), (3.6, 30.1), (4.4, 30.62)], 16, cap0=False, cap1=False), "teal")
    p.add(cyl(4.75, 0.4, (0, 0, 30.6), seg=16, bev=0.1), "cream")
    k8 = 8
    for i in range(k8):
        a = 2 * math.pi * (i + 0.5) / k8
        p.add(bar((4.55 * math.cos(a), 4.55 * math.sin(a), 31.0), (4.55 * math.cos(a), 4.55 * math.sin(a), 31.85), 0.1, 0.1, caps=False), "dark")
    p.add(lathe([(4.62, 31.82), (4.62, 31.96), (4.48, 31.96), (4.48, 31.82)], 16, closed=True), "orange")
    o8 = math.pi / 8
    p.add(lathe([(3.95, 31.0), (3.95, 31.5)], 8, cap0=False, cap1=False, a0=o8), "cream")
    p.add(lathe([(3.95, 31.5), (4.5, 34.3)], 8, cap0=False, cap1=False, a0=o8), "glass")
    p.add(lathe([(4.5, 34.3), (4.52, 34.8)], 8, cap0=False, cap1=False, a0=o8), "cream")
    for i in range(8):
        a = o8 + 2 * math.pi * i / 8
        p.add(bar((3.95 * math.cos(a), 3.95 * math.sin(a), 31.45), (4.5 * math.cos(a), 4.5 * math.sin(a), 34.35), 0.2, 0.2, caps=False), "dark")
    p.add(lathe([(4.4, 34.7), (5.0, 34.85), (5.0, 35.3), (4.6, 35.5), (3.0, 35.85), (0.0, 36.0)], 16, a0=0.0),
          lambda c, n: "white" if n.z < -0.5 else ("orange" if c.z < 35.35 else "cream"))
    p.add(cyl(0.1, 3.5, (0, 0, 35.95), seg=6), "white")
    p.add(lathe([(0.1, 39.4), (0.22, 39.55), (0.2, 39.85), (0.0, 40.0)], 8, cap0=False), "red")
    p.add(cyl(0.1, 1.6, (-2.3, 0.0, 35.6), seg=6), "dark")
    p.add(rbox((2.4, 0.26, 0.5), (-2.3, 0.0, 37.3), 0.08, 1, rot=(0, 0, 30)), "white")
    p.add(lathe([(0.7, 35.55), (0.66, 35.9), (0.45, 36.25), (0.0, 36.4)], 10, M((2.3, 0, 0)), cap0=False), "white")
    return p


def p_carro():
    p = Prop("CarroEquipaje", (7.0, 5.0, 1.9), 900)
    p.add(bb(-2.7, 3.5, -2.5, 2.5, 1.05, 1.3, 0.06, 1), lambda c, n: "metal" if n.z > 0.5 else "orange")
    for y in (-1.4, 1.4):
        p.add(bb(-2.5, 3.3, y - 0.15, y + 0.15, 0.75, 1.05), "dark")
    for x in (-1.6, 2.5):
        p.add(bb(x - 0.12, x + 0.12, -1.8, 1.8, 0.62, 0.8), "dark")
        p.add(bb(x - 0.08, x + 0.08, -1.95, 1.95, 0.38, 0.52), "dark")
        p.add(bb(x - 0.1, x + 0.1, -0.3, 0.3, 0.5, 0.64), "dark")
        for y in (-1.95, 1.95):
            wheel(p, (x, y, 0.45), 0.45, 0.34, axis="y", seg=10, detail=False)
    for y in (-2.38, 2.38):
        for x in (-2.56, 0.45, 3.36):
            p.add(bar((x, y, 1.3), (x, y, 1.82), 0.12, 0.12, caps=False), "dark")
        p.add(bar((-2.62, y, 1.82), (3.42, y, 1.82), 0.16, 0.16, 0.05), "teal")
        p.add(bar((-2.56, y, 1.56), (3.36, y, 1.56), 0.1, 0.1, caps=False), "teal")
    p.add(bar((-2.56, -2.38, 1.82), (-2.56, 2.38, 1.82), 0.16, 0.16, 0.05, up=(1, 0, 0)), "teal")
    p.add(bar((-2.56, -2.38, 1.56), (-2.56, 2.38, 1.56), 0.1, 0.1, caps=False, up=(1, 0, 0)), "teal")
    for s in (-1, 1):
        p.add(bar((-1.6, s * 0.9, 0.62), (-3.15, s * 0.12, 0.5), 0.14, 0.14), "dark")
    ring(p, (-3.5 + 0.13 + 0.05 * math.cos(math.pi / 4), 0, 0.5), 0.13, 0.05, 8, "orange")
    return p


def p_tractor():
    p = Prop("Tractor", (4.0, 7.0, 3.0), 1500)
    body = [(-3.32, 0.5), (3.32, 0.5), (3.32, 1.7), (-1.5, 1.7), (-3.32, 1.15)]
    bm = prism(body, 2.8, yzx((0, 0, 0)))
    bevel_sharp(bm, 0.12, 2, 30)
    p.add(bm, lambda c, n: "dark" if n.z < -0.5 else "orange", 40)
    for s in (-1, 1):
        p.add(decal(rect(-2.8, 2.8, 1.0, 1.16), fr((s * 1.4, 0, 0), "+x" if s > 0 else "-x"), 0.008), "cream")
    p.add(bb(-1.5, 1.5, -3.49, -3.22, 0.42, 0.95, 0.08, 1), "dark")
    p.add(bb(-1.5, 1.5, 3.22, 3.5, 0.42, 0.95, 0.08, 1), "dark")
    mf = fr((0, -3.49, 0), "-y")
    for k in range(5):
        x = -1.1 + 0.55 * k
        p.add(decal([(x - 0.12, 0.5), (x + 0.1, 0.5), (x + 0.3, 0.87), (x + 0.08, 0.87)], mf, 0.008), "yellow")
    for s in (-1, 1):
        p.add(bb(s * 0.95 - 0.28, s * 0.95 + 0.28, -3.42, -3.25, 1.0, 1.14, 0.03, 1), "yellow")
    p.add(bb(-0.22, 0.22, -3.62 + 0.12, -3.4, 0.58, 0.8, 0.04, 1), "metal")
    for x in (-1.7, 1.7):
        for y in (-2.1, 2.1):
            wheel(p, (x, y, 0.62), 0.62, 0.6, axis="x", seg=10)
            arc = [(y + 0.78 * math.cos(math.radians(a)), 0.62 + 0.78 * math.sin(math.radians(a))) for a in range(15, 166, 30)]
            arc += [(y + 0.9 * math.cos(math.radians(a)), 0.62 + 0.9 * math.sin(math.radians(a))) for a in range(165, 14, -30)]
            xs = sorted((math.copysign(1.35, x), math.copysign(2.0, x)))
            p.add(prism(arc, xs[1] - xs[0], yzx(((xs[0] + xs[1]) / 2, 0, 0))), "teal", 30)
    p.add(bb(-0.65, 0.65, 1.2, 2.15, 1.7, 1.95, 0.08, 1), "dark")
    p.add(bb(-0.65, 0.65, 2.0, 2.28, 1.95, 2.55, 0.08, 1), "teal")
    p.add(bb(-1.1, 1.1, -0.55, 0.15, 1.7, 2.05, 0.1, 1), "dark")
    p.add(bar((0, 0.0, 2.0), (0, 0.42, 2.3), 0.1, 0.1, caps=False), "dark")
    ring(p, (0, 0.45, 2.32), 0.3, 0.04, 10, "black", rot=(-55, 0, 0))
    for x in (-1.25, 1.25):
        p.add(bar((x, -0.35, 1.7), (x, -0.2, 2.72), 0.12, 0.12, caps=False), "dark")
        p.add(bar((x, 2.95, 1.7), (x, 2.95, 2.72), 0.12, 0.12, caps=False), "dark")
    p.add(bb(-1.4, 1.4, -0.45, 3.15, 2.7, 2.84, 0.06, 1), "teal")
    p.add(lathe([(0.17, 2.84), (0.16, 2.92), (0.1, 2.98), (0.0, 3.0)], 8, cap0=False), "yellow")
    return p


def p_escalera():
    p = Prop("Escalera", (3.0, 9.0, 9.0), 1200)
    p.add(bb(-1.2, 1.2, -4.5, 4.5, 0.55, 1.15, 0.1, 1), "teal")
    for x in (-1.35, 1.35):
        for y in (-3.3, 3.3):
            wheel(p, (x, y, 0.5), 0.5, 0.3, axis="x", seg=10, detail=False)
    y0, z0, y1, z1, N = -4.3, 1.15, 2.3, 7.4, 12
    run, rise = (y1 - y0) / N, (z1 - z0) / N
    for k in range(1, N):
        z = z0 + k * rise
        p.add(bb(-1.05, 1.05, y0 + (k - 1) * run, y0 + k * run + 0.06, z - 0.12, z), "metal")
    for x in (-1.12, 1.12):
        p.add(bar((x, y0, z0 + 0.05), (x, y1 + 0.1, z1 - 0.05), 0.55, 0.14, 0.04, up=(1, 0, 0)), "cream")
    p.add(bb(-1.25, 1.25, y1 - run, 4.5, 7.1, 7.4, 0.06, 1), lambda c, n: "metal" if n.z > 0.5 else "cream")
    for x in (-0.95, 0.95):
        for y in (2.9, 4.2):
            p.add(bar((x, y, 1.15), (x, y, 7.1), 0.18, 0.18, caps=False), "dark")
        p.add(bar((x, 2.9, 1.3), (x, 4.2, 6.9), 0.1, 0.1, caps=False, up=(1, 0, 0)), "dark")
        p.add(bar((x, 4.2, 1.3), (x, 2.9, 6.9), 0.1, 0.1, caps=False, up=(1, 0, 0)), "dark")
        p.add(bar((x, -1.2, 1.15), (x, -1.2, z0 + (-1.2 - y0) * (z1 - z0) / (y1 - y0) - 0.25), 0.16, 0.16, caps=False), "dark")
    for x in (-1.24, 1.24):
        for k in (1, 4, 7, 10):
            yy = y0 + (k - 0.5) * run
            zz = z0 + k * rise
            p.add(bar((x, yy, zz - 0.3), (x, yy, zz + 1.45), 0.08, 0.08, caps=False), "dark")
        p.add(bar((x, y0 + 0.5 * run, z0 + rise + 1.45), (x, 2.4, z1 + 1.5), 0.12, 0.12, 0.03, up=(1, 0, 0)), "orange")
        p.add(bar((x, y0 + 0.5 * run, z0 + rise + 0.75), (x, 2.4, z1 + 0.8), 0.08, 0.08, caps=False, up=(1, 0, 0)), "orange")
        for y in (2.4, 4.4):
            p.add(bar((x, y, 7.4), (x, y, 8.9), 0.08, 0.08, caps=False), "dark")
        p.add(bar((x, 2.4, 8.94), (x, 4.44, 8.94), 0.12, 0.12, 0.03), "orange")
        p.add(bar((x, 2.4, 8.2), (x, 4.44, 8.2), 0.08, 0.08), "orange")
    return p


def p_arbol():
    p = Prop("Arbol", (6.0, 6.0, 9.0), 500)
    p.add(lathe([(0.48, 0.0), (0.36, 0.45), (0.27, 2.6), (0.22, 4.8)], 7, cap0=False, cap1=False), "trunk", 70)
    p.add(tube([(0.0, 0.0, 3.0), (0.55, 0.15, 3.7), (1.1, 0.25, 4.2)], lambda u: 0.14 - 0.06 * u, k=5, steps=2, caps=False), "trunk", 70)
    p.add(blob((2.65, 2.65, 2.3), (0.0, 0.0, 6.4), jit=0.05, seed=1), "leaf", 180)
    p.add(blob((1.75, 1.75, 1.55), (-1.3, 1.15, 5.3), jit=0.05, seed=2), "dleaf", 180)
    p.add(blob((1.65, 1.65, 1.45), (1.35, -1.3, 5.2), jit=0.05, seed=3), "dleaf", 180)
    p.add(blob((1.55, 1.55, 1.4), (0.35, -0.2, 7.55), jit=0.05, seed=4), "leaf", 180)
    p.add(blob((1.5, 1.5, 1.3), (1.1, 1.45, 6.6), jit=0.05, seed=5), "leaf", 180)
    return p


def p_arbusto():
    p = Prop("Arbusto", (3.0, 3.0, 2.0), 250)
    p.add(blob((1.15, 1.2, 1.0), (-0.25, 0.25, 0.85), jit=0.05, seed=11), "leaf", 180)
    p.add(blob((0.85, 0.85, 0.75), (0.75, -0.4, 0.6), jit=0.05, seed=12), "dleaf", 180)
    p.add(blob((0.8, 0.8, 0.72), (-0.65, -0.65, 0.57), jit=0.05, seed=13), "dleaf", 180)
    return p


def p_valla():
    p = Prop("Valla", (8.0, 0.3, 2.4), 150)
    for x in (-3.88, 3.88):
        p.add(bb(x - 0.12, x + 0.12, -0.15, 0.15, 0.0, 2.3), "dteal")
        bm = bmesh.new()
        base = [bm.verts.new((x + dx, dy, 2.3)) for dx, dy in ((-0.12, -0.15), (0.12, -0.15), (0.12, 0.15), (-0.12, 0.15))]
        tip = bm.verts.new((x, 0.0, 2.4))
        for i in range(4):
            bm.faces.new((base[i], base[(i + 1) % 4], tip))
        p.add(bm, "dteal", 30)
    for z in (0.32, 2.05):
        p.add(bar((-3.76, 0, z), (3.76, 0, z), 0.1, 0.12, caps=False, up=(0, 1, 0)), "metal")
    for i in range(9):
        x = -3.2 + 0.8 * i
        p.add(bar((x, 0, 0.27), (x, 0, 2.18), 0.07, 0.07, caps=False), "metal")
    return p


def p_luz():
    p = Prop("LuzPista", (0.4, 0.4, 0.6), 60)
    p.add(bb(-0.2, 0.2, -0.2, 0.2, 0.0, 0.1), "dark")
    p.add(cyl(0.06, 0.3, (0, 0, 0.1), seg=6, cap0=False, cap1=False), "metal")
    p.add(lathe([(0.12, 0.38), (0.12, 0.46), (0.07, 0.56), (0.0, 0.6)], 6), lambda c, n: "metal" if c.z < 0.43 else "yellow", 60)
    return p


def p_cono():
    p = Prop("Cono", (1.0, 1.0, 1.6), 150)
    p.add(rr_loft(1.0, 1.0, 0.15, 1, [(0.0, 0.0), (0.0, 0.07), (0.05, 0.12)]), "orange")
    prof = [(0.36, 0.11), (0.29, 0.62), (0.245, 0.98), (0.12, 1.5), (0.065, 1.6), (0.0, 1.6)]
    p.add(lathe(prof, 10, cap0=False), lambda c, n: "white" if 0.62 < c.z < 0.98 else "orange", 40)
    return p


def p_manga():
    p = Prop("Manga", (1.2, 4.0, 7.0), 400)
    ym = -1.55
    p.add(cyl(0.45, 0.14, (0, ym, 0.0), seg=8), "dark")
    p.add(cyl(0.09, 6.75, (0, ym, 0.1), seg=8, cap0=False), lambda c, n: "red" if (c.z > 5.2 and c.z < 5.8) or c.z < 0.9 else "white", 60)
    p.add(lathe([(0.12, 6.82), (0.13, 6.92), (0.0, 7.0)], 8), "red")
    yr, zr = -1.25, 6.32
    prof = [(0.56, 0.0), (0.52, 0.65), (0.46, 1.3), (0.4, 1.95), (0.34, 2.6), (0.28, 3.25)]
    m = M((0, yr, zr), (-90, 0, 0))

    def droop(bm):
        for v in bm.verts:
            t = v.co.y - yr
            v.co.z -= 0.055 * t * t
        return bm

    def band(c, n):
        t = c.y - yr
        return "orange" if int(t / 0.65) % 2 == 0 else "white"
    p.add(droop(lathe(prof, 10, m, cap0=False, cap1=False)), band, 60)
    inner = droop(lathe([(r * 0.95, z) for r, z in prof], 10, m, cap0=False, cap1=False))
    bmesh.ops.reverse_faces(inner, faces=inner.faces)
    p.add(inner, band, 60)
    ring(p, (0, yr, zr), 0.58, 0.04, 12, "dark", rot=(90, 0, 0), n=3)
    p.add(bar((0, ym, 6.82), (0, yr, zr + 0.58), 0.06, 0.06, caps=False), "dark")
    p.add(bar((0, ym, 5.85), (0, yr, zr - 0.58), 0.06, 0.06, caps=False), "dark")
    return p


def arc_rib(R, zc, a0, a1, n, y, w, h):
    bm = bmesh.new()
    outer, inner = [], []
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        sx, cz = math.sin(a), math.cos(a)
        outer.append([bm.verts.new(((R + h) * sx, y + dy, zc + (R + h) * cz)) for dy in (-w / 2, w / 2)])
        inner.append([bm.verts.new((R * sx, y + dy, zc + R * cz)) for dy in (-w / 2, w / 2)])
    for k in range(n):
        o0, o1, i0, i1 = outer[k], outer[k + 1], inner[k], inner[k + 1]
        bm.faces.new((o0[0], o0[1], o1[1], o1[0]))
        bm.faces.new((i0[0], o0[0], o1[0], i1[0]))
        bm.faces.new((o0[1], i0[1], i1[1], o1[1]))
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if abs(f.normal.y) < 0.5:
            d = f.normal.dot(Vector((c.x, 0.0, c.z - zc)))
        else:
            d = f.normal.y * (c.y - y)
        if d < 0:
            f.normal_flip()
    return bm


def p_hangar():
    p = Prop("Hangar", (50.0, 40.0, 22.0), 2500)
    RH = 0.14
    AP = 22.0 - RH
    R = (25.0 ** 2 + (AP - 12.0) ** 2) / (2 * (AP - 12.0))
    zc = AP - R
    al = math.asin(25.0 / R)
    N = 20
    outer = [(R * math.sin(-al + 2 * al * k / N), zc + R * math.cos(-al + 2 * al * k / N)) for k in range(N + 1)]
    Ri = R - 0.55
    ali = math.asin(24.95 / Ri)
    inner = [(Ri * math.sin(ali - 2 * ali * k / N), zc + Ri * math.cos(ali - 2 * ali * k / N)) for k in range(N + 1)]
    mroof = frame((0, 0, 0), (1, 0, 0), (0, 0, 1))
    p.add(prism(outer + inner, 40.0, mroof), lambda c, n: "orange" if abs(n.y) > 0.9 else ("metal" if Vector((c.x, 0, c.z - zc)).dot(n) > 0 else "concrete"), 30)
    for y in (-13.3, -6.65, 0.0, 6.65, 13.3):
        p.add(arc_rib(R - 0.02, zc, -al + 0.012, al - 0.012, 16, y, 0.35, RH + 0.02), "concrete", 40)
    for s in (-1, 1):
        x0, x1 = sorted((s * 23.8, s * 24.4))
        p.add(bb(x0, x1, -19.4, 19.4, 0.0, 12.3), "cream")
        x0, x1 = sorted((s * 24.4, s * 24.56))
        p.add(bb(x0, x1, -19.0, 19.0, 0.0, 1.4, 0.04, 1), "teal")
        for y in (-13.0, -6.5, 0.0, 6.5, 13.0):
            mw = fr((s * 24.4, 0, 0), "+x" if s > 0 else "-x")
            p.add(decal(rrect(y * s, 9.2, 3.0, 1.9, 0.25, 1), mw, 0.02), "white")
            p.add(decal(rrect(y * s, 9.2, 2.6, 1.5, 0.18, 1), mw, 0.04), "glass")
        for sy in (-1, 1):
            xs = sorted((s * 23.9, s * 24.75))
            ys = sorted((sy * 19.0, sy * 19.85))
            p.add(bb(xs[0], xs[1], ys[0], ys[1], 0.0, 12.0, 0.15, 1), "teal")
    Rg = R - 0.3
    gab = [(-24.4, 0.0), (24.4, 0.0)] + [(Rg * math.sin(a), zc + Rg * math.cos(a)) for a in [math.asin(24.4 / Rg) - 2 * math.asin(24.4 / Rg) * k / N for k in range(N + 1)]]
    for s in (-1, 1):
        p.add(prism(gab, 0.6, frame((0, s * 19.1, 0), (1, 0, 0), (0, 0, 1))), "cream")
        if s > 0:
            p.add(bb(-24.0, 24.0, 19.4, 19.56, 0.0, 1.4, 0.04, 1), "teal")
    for x0, x1 in ((-24.0, -19.0), (19.0, 24.0)):
        p.add(bb(x0, x1, -19.56, -19.4, 0.0, 1.4, 0.04, 1), "teal")
    md = fr((0, -19.4, 0), "-y")
    p.add(decal(rect(-18.0, 18.0, 0.0, 14.8), md, 0.01), "dark")
    for k in range(6):
        x0 = -18.0 + 6.0 * k + 0.05
        x1 = x0 + 5.9
        p.add(bb(x0, x1, -19.78, -19.42, 0.15, 14.75, 0.08, 1), "teal" if k % 2 == 0 else "dteal")
        mp = fr((0, -19.78, 0), "-y")
        p.add(decal(rrect((x0 + x1) / 2, 11.2, 5.0, 1.3, 0.2, 1), mp, 0.01), "glass")
        p.add(decal(rect(x0 + 0.1, x1 - 0.1, 3.0, 3.6), mp, 0.01), "orange")
    for s in (-1, 1):
        x0, x1 = sorted((s * 18.0, s * 19.0))
        p.add(bb(x0, x1, -19.95, -19.4, 0.0, 15.8, 0.12, 1), "teal")
    p.add(bb(-19.0, 19.0, -19.95, -19.4, 14.8, 15.8, 0.12, 1), "teal")
    p.add(decal(rect(-18.6, 18.6, 15.12, 15.48), fr((0, -19.95, 0), "-y"), 0.01), "orange")
    p.add(bb(-19.0, 19.0, -20.0, -19.4, 0.0, 0.14), "dark")
    p.add(decal(rrect(21.6, 1.45, 2.1, 2.9, 0.2, 1), md, 0.01), "dteal")
    p.add(decal(rrect(21.6, 1.35, 1.7, 2.6, 0.15, 1), md, 0.02), "dark")
    p.add(bb(20.3, 22.9, -20.0, -19.4, 3.1, 3.3, 0.06, 1), "orange")
    p.add(cyl(1.7, 0.1, (0, -19.4, 18.4), (90, 0, 0), seg=20), "cream")
    logo(p, fr((0, -19.5, 18.4), "-y"), 1.7, base=False, step=0.01)
    for x, y in ((-9.0, -8.0), (9.0, 8.0)):
        zr = zc + math.sqrt(R * R - x * x)
        p.add(cyl(0.8, 1.05, (x, y, zr - 0.4), seg=8), "white")
        p.add(cyl(1.05, 0.22, (x, y, zr + 0.65), seg=8), "dark")
    return p


BUILDERS = [p_terminal, p_mostrador, p_banco, p_kiosko, p_marco, p_torre, p_carro, p_tractor, p_escalera,
            p_arbol, p_arbusto, p_valla, p_luz, p_cono, p_manga, p_hangar]


def finalize(p):
    prims = []
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for bm, role, ang in p.parts:
        ng = [f for f in bm.faces if len(f.verts) > 4]
        if ng:
            bmesh.ops.triangulate(bm, faces=ng, quad_method="BEAUTY", ngon_method="BEAUTY")
        bm.normal_update()
        roles = [role(f.calc_center_median(), f.normal.copy()) if callable(role) else role for f in bm.faces]
        for v in bm.verts:
            for i in range(3):
                mn[i] = min(mn[i], v.co[i])
                mx[i] = max(mx[i], v.co[i])
        prims.append((bm, roles, ang))
    raw = mx - mn
    sc = [p.size[i] / raw[i] for i in range(3)]
    T = Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)) @ Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)))
    verts, faces, uvs, nrms = [], [], [], []
    for bm, roles, ang in prims:
        bmesh.ops.transform(bm, matrix=T, verts=bm.verts)
        bm.normal_update()
        bm.verts.index_update()
        base = len(verts)
        verts.extend(v.co.copy() for v in bm.verts)
        cl = math.cos(math.radians(ang))
        for f, r in zip(bm.faces, roles):
            faces.append([base + v.index for v in f.verts])
            uv = suv(r)
            for lp in f.loops:
                ns = Vector()
                for lf in lp.vert.link_faces:
                    if lf.normal.dot(f.normal) >= cl:
                        ns += lf.normal * lf.calc_area()
                nrms.append(ns.normalized() if ns.length > 1e-12 else f.normal.copy())
                uvs.append(uv)
        bm.free()
    tris = sum(len(f) - 2 for f in faces)
    return verts, faces, uvs, nrms, tris, raw, sc, mn, mx


def palette_image():
    img = bpy.data.images.new("aero_palette", 64, 64, alpha=True)
    px = [0.0] * (64 * 64 * 4)
    for i, (_, hx) in enumerate(PAL):
        r, g, b = hex_rgb(hx)
        gx, gy = i % 4, i // 4
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * 64 + x) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "aero_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def palette_material(img):
    mat = bpy.data.materials.new("Aero_Palette")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.6
    return mat


def make_object(p, mat):
    verts, faces, uvs, nrms, tris, raw, sc, mn, mx = finalize(p)
    me = bpy.data.meshes.new(p.name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", [c for uv in uvs for c in uv])
    me.shade_smooth()
    me.normals_split_custom_set([tuple(n) for n in nrms])
    me.materials.append(mat)
    ob = bpy.data.objects.new(p.name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob, tris, raw, sc, mn, mx


def export_fbx(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, ob.name + ".fbx"),
        use_selection=True,
        object_types={"MESH"},
        use_mesh_modifiers=True,
        mesh_smooth_type="OFF",
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="Z",
        axis_up="Y",
        path_mode="COPY",
        embed_textures=True,
        bake_anim=False,
    )


def render_setup(scene, threads):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    scene.cycles.max_bounces = 5
    scene.render.threads_mode = "FIXED"
    scene.render.threads = threads
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    pct = arg("--pct")
    scene.render.resolution_percentage = int(pct) if isinstance(pct, str) else 100
    scene.render.image_settings.file_format = "PNG"
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    world = bpy.data.worlds.new("Sky")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*lin(hex_rgb("BFE3F2")), 1.0)
    bg.inputs[1].default_value = 0.8
    scene.world = world
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.6
    sun.angle = math.radians(10)
    so = bpy.data.objects.new("Sun", sun)
    so.rotation_euler = (math.radians(48), 0.0, math.radians(-34))
    scene.collection.objects.link(so)
    return so


MATS = {}


def mat_rgb(hx, rough=0.9, emit=0.0, alpha=1.0, spec=0.5):
    key = (hx, rough, emit, alpha)
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new("M_" + hx)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(hex_rgb(hx)), 1.0)
    b.inputs["Roughness"].default_value = rough
    if emit > 0:
        b.inputs["Emission Color"].default_value = (*lin(hex_rgb(hx)), 1.0)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
    MATS[key] = m
    return m


class Stage:
    def __init__(self, objs):
        self.objs = objs
        self.made = []

    def link(self, o):
        bpy.context.scene.collection.objects.link(o)
        self.made.append(o)
        return o

    def put(self, name, x, y, rz=0.0, z=0.0):
        o = bpy.data.objects.new(name + "_i", self.objs[name].data)
        o.location = (x, y, z)
        o.rotation_euler = (0, 0, math.radians(rz))
        return self.link(o)

    def box(self, x0, x1, y0, y1, z0, z1, mat, bev=0.0):
        bm = bb(x0, x1, y0, y1, z0, z1, bev, 2 if bev > 0 else 1)
        me = bpy.data.meshes.new("b")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        if bev > 0:
            me.shade_smooth()
        return self.link(bpy.data.objects.new("b", me))

    def quad(self, x0, x1, y0, y1, z, mat):
        me = bpy.data.meshes.new("q")
        me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
        me.materials.append(mat)
        return self.link(bpy.data.objects.new("q", me))

    def vquad(self, pts, mat):
        me = bpy.data.meshes.new("v")
        me.from_pydata(pts, [], [tuple(range(len(pts)))])
        me.materials.append(mat)
        return self.link(bpy.data.objects.new("v", me))

    def area(self, loc, size, power, sy=None, rot=(0, 0, 0), color=(1.0, 0.97, 0.9)):
        L = bpy.data.lights.new("A", "AREA")
        L.shape = "RECTANGLE"
        L.size = size
        L.size_y = sy if sy is not None else size
        L.energy = power
        L.color = color
        o = bpy.data.objects.new("A", L)
        o.location = loc
        o.rotation_euler = [math.radians(a) for a in rot]
        return self.link(o)

    def camera(self, loc, target, lens):
        cd = bpy.data.cameras.new("Cam")
        cd.lens = lens
        cd.clip_start = 0.1
        cd.clip_end = 2000
        co = bpy.data.objects.new("Cam", cd)
        co.location = loc
        co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.camera = co
        return self.link(co)

    def clear(self):
        for o in self.made:
            bpy.data.objects.remove(o)
        self.made = []


GRASS, ASPH, WALK, PAINT, YPAINT = "8DC85C", "4A4F57", "D8D4CA", "F4F1E8", "F2C14E"


def ground(st, x0=-400, x1=400, y0=-400, y1=400):
    st.quad(x0, x1, y0, y1, -0.002, mat_rgb(GRASS, 0.95))


def glass_panes(st, ox=0.0, oy=0.0):
    g = mat_rgb("B9E6F7", 0.05, alpha=0.22)
    gy = TERM["glass_y"] + oy
    for x0, x1, z0, z1 in TERM["panes"]:
        st.vquad([(ox + x0, gy, z0), (ox + x1, gy, z0), (ox + x1, gy, z1), (ox + x0, gy, z1)], g)


def sheet_exterior(st):
    ground(st)
    st.quad(-90, 90, -84, -33, 0.0, mat_rgb(ASPH, 0.85))
    st.quad(-34, 34, -33, -27, 0.004, mat_rgb(WALK, 0.9))
    st.box(-34, 34, -33.4, -33.0, 0.0, 0.25, mat_rgb("BDB8AE", 0.9))
    w = mat_rgb(PAINT, 0.8)
    for i in range(9):
        x = -7.0 + 1.75 * i
        st.quad(x - 0.55, x + 0.55, -42.0, -34.5, 0.01, w)
    for x in range(-80, 81, 10):
        st.quad(x - 2.2, x + 2.2, -58.3, -57.7, 0.01, w)
    st.put("Terminal", 0, 0)
    glass_panes(st)
    for x, y, r in ((-41, -22, 0), (-37, 2, 40), (-43, 21, 80), (-30, 40, 15), (-8, 42, 60), (16, 41, 30), (40, -16, 20), (42, 10, 70), (37, 32, 5)):
        st.put("Arbol", x, y, r)
    for x, y, r in ((-31, -29.5, 0), (-30, -12, 50), (-30.5, 9, 120), (31, -29.5, 30), (30.5, -10, 80), (-24, -30.5, 10), (24, -30.5, 70)):
        st.put("Arbusto", x, y, r)
    for k in range(12):
        st.put("Valla", -48.0, -40.0 + 8.0 * k + 4.0, 90)
    for k in range(6):
        st.put("Valla", -44.0 + 8.0 * k, 52.0, 0)
    for x, y in ((-10.5, -37.0), (-8.0, -38.6), (-5.5, -39.6), (5.5, -39.6), (8.0, -38.6), (10.5, -37.0), (22, -36.5), (24.2, -36.5)):
        st.put("Cono", x, y, 20)
    for k in range(9):
        st.put("LuzPista", -32.0 + 8.0 * k, -33.6)
    st.camera((-66, -84, 36), (0, -4, 5.0), 38)


def board_fill(st, x0, y, z0, w, h):
    navy = mat_rgb("1E2A3A", 0.6)
    st.vquad([(x0, y, z0), (x0 + w, y, z0), (x0 + w, y, z0 + h), (x0, y, z0 + h)], navy)
    rnd = random.Random(7)
    cols = [mat_rgb("FFF4E0", 0.5, emit=2.0), mat_rgb("F2A33A", 0.5, emit=2.0), mat_rgb("4FD1C5", 0.5, emit=2.0)]
    hdr = mat_rgb("F27B2B", 0.5, emit=1.6)
    yy = y - 0.01
    st.vquad([(x0 + 0.3, yy, z0 + h - 1.2), (x0 + w - 0.3, yy, z0 + h - 1.2), (x0 + w - 0.3, yy, z0 + h - 0.35), (x0 + 0.3, yy, z0 + h - 0.35)], hdr)
    for r in range(7):
        zc = z0 + h - 1.9 - r * 0.98
        xc = x0 + 0.6
        for k, (ln, c) in enumerate(((1.6, 0), (rnd.uniform(3.5, 6.0), 0), (1.8, 2), (rnd.uniform(1.6, 2.6), 1))):
            st.vquad([(xc, yy, zc - 0.22), (xc + ln, yy, zc - 0.22), (xc + ln, yy, zc + 0.22), (xc, yy, zc + 0.22)], cols[c])
            xc += ln + [0.7, 1.2, 1.2, 0.0][k] + (6.2 - ln if k == 1 else 0.0)


def sheet_interior(st):
    ground(st)
    st.quad(-90, 90, -84, -33, 0.0, mat_rgb(ASPH, 0.85))
    st.quad(-34, 34, -33, -27, 0.004, mat_rgb(WALK, 0.9))
    st.put("Terminal", 0, 0)
    glass_panes(st)
    st.put("MarcoTablero", 0, 26.1, 0, 2.7)
    board_fill(st, -9.0, 26.29, 3.0, 18.0, 9.0)
    red = mat_rgb("D9443A", 0.4)
    for x in (-6.5, 0.0, 6.5):
        st.put("Kiosko", x, 13.0)
        bm = lathe([(0.8, 0.0), (0.8, 0.2), (0.7, 0.34), (0.0, 0.38)], 24, M((x, 13.0, 3.0)))
        me = bpy.data.meshes.new("btn")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(red)
        me.shade_smooth()
        st.link(bpy.data.objects.new("btn", me))
    for y in (-12.0, -3.0, 6.0):
        st.put("Mostrador", 21.5, y, -90)
    for y in (-10.0, 2.0):
        st.put("BancoEspera", -16.0, y, 0)
        st.put("BancoEspera", -16.0, y + 2.3, 180)
    st.put("BancoEspera", -4.0, -8.0, 0)
    for x, y in ((-23.0, 22.5), (23.0, 22.5), (-23.0, -20.5), (13.0, 22.5), (-13.0, 22.5)):
        st.put("Arbusto", x, y, 30)
    for x, y in ((-3.0, -14.0), (3.0, -14.0)):
        st.put("Cono", x, y, 10)
    for y in (-19.3, -9.3, 0.9, 11.1, 21.0):
        for x in (-18.0, 0.0, 18.0):
            st.area((x, y, 12.9), 6.0, 900, sy=2.0)
    st.area((0, 20, 9), 14.0, 1200, sy=4.0, rot=(-90, 0, 0))
    st.camera((-3.0, -44.0, 6.4), (0.5, 8.0, 4.6), 24)


def sheet_ramp(st):
    ground(st)
    st.quad(-70, 70, -18, 70, 0.0, mat_rgb(ASPH, 0.85))
    y = mat_rgb(YPAINT, 0.8)
    w = mat_rgb(PAINT, 0.8)
    st.quad(-70, 70, -9.3, -8.7, 0.01, y)
    for x in range(-66, 67, 8):
        st.quad(x - 2.5, x + 2.5, -16.4, -15.9, 0.01, w)
    st.quad(-50, -6, 4.0, 4.5, 0.01, y)
    st.put("Hangar", -26.0, 34.0, 0)
    st.put("TorreControl", 34.0, 40.0, 0)
    st.put("Escalera", 12.0, 6.0, 90)
    st.put("Tractor", -12.0, -1.0, -25)
    ca = math.radians(-25)
    for k in (1, 2):
        d = 8.6 * k
        st.put("CarroEquipaje", -12.0 - math.sin(ca) * d * -1.0, -1.0 + math.cos(ca) * d, 90 - 25)
    for k in range(15):
        st.put("LuzPista", -42.0 + 6.0 * k, -18.6)
    st.put("Manga", 30.0, -26.0, -60)
    for x, yy in ((4.0, -2.0), (6.2, -3.2), (20.5, 1.5), (21.5, 10.5)):
        st.put("Cono", x, yy, 15)
    for x, yy, r in ((48, 14, 10), (56, 30, 40), (-58, 8, 0), (52, -30, 0)):
        st.put("Arbol", x, yy, r)
    for x, yy in ((24, -31), (36, -30), (44, -24)):
        st.put("Arbusto", x, yy, 10)
    for k in range(10):
        st.put("Valla", -40.0 + 8.0 * k, -36.0, 0)
    st.camera((-30, -72, 26), (4, 16, 9), 33)


SHEETS = [("aero_1.png", sheet_exterior), ("aero_2.png", sheet_interior), ("aero_3.png", sheet_ramp)]


def render_sheets(objs, which, threads, outdir):
    scene = bpy.context.scene
    render_setup(scene, threads)
    for o in objs.values():
        o.hide_render = True
    for si, (fname, fn) in enumerate(SHEETS):
        if which and str(si + 1) not in which:
            continue
        st = Stage(objs)
        fn(st)
        scene.render.filepath = os.path.join(outdir, fname)
        bpy.ops.render.render(write_still=True)
        print("RENDER", scene.render.filepath)
        st.clear()


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    img = palette_image()
    mat = palette_material(img)
    only = arg("--only")
    only = set(only.split(",")) if isinstance(only, str) else None
    objs = {}
    manifest = []
    ok = True
    for b in BUILDERS:
        p = b()
        if only and p.name not in only:
            continue
        ob, tris, raw, sc, mn, mx = make_object(p, mat)
        objs[p.name] = ob
        if tris > p.budget:
            ok = False
        warn = " SCALE!" if any(abs(s - 1.0) > 0.01 for s in sc) else ""
        print("PIECE %-14s tris %5d / %5d %s  raw %.3f x %.3f x %.3f  fit %.4f %.4f %.4f  min %.3f %.3f %.3f%s" % (
            p.name, tris, p.budget, "OK" if tris <= p.budget else "OVER", raw.x, raw.y, raw.z, sc[0], sc[1], sc[2], mn.x, mn.y, mn.z, warn))
        if not arg("--no-export"):
            export_fbx(ob)
        dim = ob.dimensions
        manifest.append({"nombre": p.name, "archivo": p.name + ".fbx", "tamano": [round(dim.x, 3), round(dim.z, 3), round(dim.y, 3)], "triangulos": tris})
    if not only and not arg("--no-export"):
        with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
    if "Terminal" in objs:
        print("GLASS y=%.2f panes=%d" % (TERM["glass_y"], len(TERM["panes"])))
    print("ALL BUDGETS OK" if ok else "SOME PIECES OVER BUDGET")
    if arg("--no-render"):
        return
    which = arg("--sheets")
    which = set(which.split(",")) if isinstance(which, str) else None
    outdir = arg("--render-dir")
    outdir = outdir if isinstance(outdir, str) else OUT
    threads = arg("--threads")
    render_sheets(objs, which, int(threads) if isinstance(threads, str) else 2, outdir)


main()
