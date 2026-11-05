import bpy
import bmesh
import math
import os
import sys
import json
from mathutils import Vector, Matrix, Euler

_SEP = {}
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "herramientas", "separar_capas.py"), encoding="utf-8") as _fh:
    exec(compile(_fh.read(), "separar_capas.py", "exec"), _SEP)

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]


def arg(name, default=None):
    if name in ARGS:
        i = ARGS.index(name)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return default


PAL = [
    ("cream", "FFF4E0"), ("orange", "F27B2B"), ("teal", "1FA6A0"), ("dark", "34383F"),
    ("black", "1B1B21"), ("white", "F7F7F2"), ("red", "D9443A"), ("wood", "C98B4E"),
    ("dwood", "8A5A33"), ("bun", "E9A64B"), ("patty", "6B3A22"), ("lettuce", "79C043"),
    ("cheese", "F6C445"), ("metal", "A9B0B8"), ("glass", "8FD3F4"), ("gold", "F0B73A"),
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


def burger(p, m, lod=False):
    seg = 10 if lod else 12
    if lod:
        p.add(lathe([(0.28, 0.0), (0.33, 0.05), (0.31, 0.12)], seg, m, cap1=False), "bun")
        p.add(lathe([(0.33, 0.11), (0.36, 0.16), (0.33, 0.21)], seg, m, cap0=False), "patty")
        top = [(0.31, 0.23), (0.34, 0.31), (0.26, 0.47), (0.0, 0.55)]
    else:
        p.add(lathe([(0.27, 0.0), (0.32, 0.03), (0.33, 0.09), (0.31, 0.12)], seg, m, cap1=False), "bun")
        p.add(lathe([(0.33, 0.11), (0.355, 0.13), (0.355, 0.19), (0.33, 0.21)], seg, m, cap0=False), "patty")
        top = [(0.31, 0.23), (0.345, 0.3), (0.31, 0.43), (0.2, 0.52), (0.0, 0.55)]
    s = 0.3
    p.add(slab_grid(3, s, 0.022, lambda x, y: 0.232 - 0.075 * (abs(x) / s) ** 2 * (abs(y) / s) ** 2, m), "cheese")
    bm = bmesh.new()
    nn = seg * 2
    ct = bm.verts.new((0, 0, 0.262))
    cb = bm.verts.new((0, 0, 0.238))
    rim = []
    for k in range(nn):
        a = 2 * math.pi * k / nn
        r = 0.352 if k % 2 == 0 else 0.33
        z = 0.222 if k % 2 == 0 else 0.25
        rim.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
    for k in range(nn):
        k2 = (k + 1) % nn
        bm.faces.new((ct, rim[k], rim[k2]))
        bm.faces.new((cb, rim[k2], rim[k]))
    p.add(xf(bm, m), "lettuce", 70)
    p.add(lathe(top, seg, m, cap0=False), "bun")
    up = [q for q in top if q[0] <= 0.311]
    seeds = ((0.14, 25, 30), (0.17, 150, 100), (0.12, 265, 160)) if not lod else ((0.15, 40, 20), (0.15, 210, 110))
    for r, a, rz in seeds:
        for (r0, z0), (r1, z1) in zip(up, up[1:]):
            if r1 <= r <= r0:
                t = (r0 - r) / (r0 - r1)
                z = z0 + (z1 - z0) * t
                sl = (z1 - z0) / (r1 - r0)
                break
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        nrm = Vector((-sl * ca, -sl * sa, 1.0)).normalized()
        pos = Vector((r * ca, r * sa, z)) + nrm * 0.006
        fm = Matrix.Translation(pos) @ frame_from_normal(nrm) @ Matrix.Rotation(math.radians(rz), 4, "Z")
        p.add(xf(ellipsoid((0.036, 0.018, 0.011), fm, 5, 3), m), "cream", 70)


def p_asiento():
    p = Prop("Asiento", (2.2, 2.4, 4.2), 900)
    for sx in (-1, 1):
        x = sx * 0.7
        p.add(bar((x, -0.72, 0.0), (x, 0.95, 0.0), 0.2, 0.07, 0.025, up=(0, 0, 1)), "dark")
        p.add(bar((x, -0.6, 0.03), (x, -0.6, 1.02), 0.16, 0.22, 0.05, up=(0, 1, 0)), "dark")
        p.add(bar((x, 0.85, 0.03), (x, 0.22, 1.02), 0.16, 0.18, 0.05, up=(0, 1, 0)), "dark")
    for y in (-0.6, 0.3):
        p.add(bar((-0.72, y, 0.9), (0.72, y, 0.9), 0.12, 0.12, 0.035, caps=False), "dark")
    p.add(bb(-0.92, 0.92, -1.05, 0.7, 1.0, 1.14, 0.04), "dark")
    p.add(rbox((1.78, 1.85, 0.5), (0, -0.275, 1.35), 0.17, 2), "teal")
    a = math.radians(8)
    ax = Vector((0, math.sin(a), math.cos(a)))
    nb = Vector((0, math.cos(a), -math.sin(a)))
    B = Vector((0, 0.53, 1.15))
    p.add(rbox((1.78, 0.46, 2.6), B + ax * 1.3, 0.16, 2, rot=(-8, 0, 0)), "teal")
    p.add(rbox((1.86, 0.54, 0.74), B + ax * 2.66, 0.18, 2, rot=(-8, 0, 0)), "orange")
    p.add(rbox((1.3, 0.06, 0.95), B + ax * 1.75 + nb * 0.23, 0.03, 1, rot=(-8, 0, 0)), "dark")
    p.add(rbox((0.24, 0.05, 0.08), B + ax * 2.28 + nb * 0.27, 0.0, rot=(-8, 0, 0)), "cream")
    for sx in (-1, 1):
        x = sx * 1.0
        p.add(rbox((0.2, 1.55, 0.18), (x, -0.22, 2.22), 0.07, 1), "dark")
        p.add(bar((x, -0.72, 1.08), (x, -0.64, 2.18), 0.16, 0.17, 0.045, up=(0, 1, 0)), "dark")
    return p


def p_bandeja():
    p = Prop("Bandeja", (1.6, 1.1, 0.5), 900)
    p.add(rr_loft(1.6, 1.1, 0.16, 2, [(0.0, 0.0), (0.0, 0.1), (0.025, 0.125), (0.05, 0.11), (0.09, 0.05)]), "metal")
    for x, y, a in ((-0.42, 0.18, 20), (0.42, 0.18, -35), (0.0, -0.21, 70)):
        burger(p, M((x, y, 0.05), (0, 0, a), (0.78, 0.78, 0.78)), lod=True)
    return p


def p_hamburguesa():
    p = Prop("Hamburguesa", (0.7, 0.7, 0.55), 400)
    burger(p, Matrix())
    return p


def p_cafe():
    p = Prop("Cafe", (0.4, 0.4, 0.6), 250)
    p.add(lathe([(0.13, 0.0), (0.142, 0.018), (0.175, 0.5)], 12, cap1=False), "cream")
    p.add(lathe([(0.148, 0.15), (0.161, 0.16), (0.176, 0.36), (0.163, 0.37)], 12, cap0=False, cap1=False), "red")
    p.add(lathe([(0.168, 0.485), (0.2, 0.5), (0.2, 0.54), (0.165, 0.558), (0.15, 0.6)], 12, cap0=False), "red")
    p.add(decal(circ(0.0, -0.085, 0.035, 6), M((0, 0, 0.6005))), "black")
    return p


def p_agua():
    p = Prop("Agua", (0.3, 0.3, 0.8), 250)
    prof = [(0.12, 0.0), (0.145, 0.03), (0.15, 0.2), (0.137, 0.245), (0.15, 0.29), (0.15, 0.5), (0.11, 0.61), (0.066, 0.665), (0.063, 0.705)]
    p.add(lathe(prof, 10, cap1=False), lambda c, n: "white" if 0.29 < c.z < 0.5 else "glass")
    p.add(cyl(0.074, 0.1, (0, 0, 0.7), seg=10, bev=0.016), "teal")
    return p


def p_extintor():
    p = Prop("Extintor", (0.6, 0.6, 1.7), 600)
    prof = [(0.22, 0.0), (0.25, 0.045), (0.25, 0.45), (0.25, 0.85), (0.25, 1.1), (0.23, 1.22), (0.155, 1.31), (0.075, 1.35)]

    def role(c, n):
        if c.z < 0.05:
            return "black"
        if 0.45 < c.z < 0.85 and c.y < -0.15:
            return "cream"
        return "red"
    p.add(lathe(prof, 14, cap1=False), role)
    p.add(cyl(0.07, 0.14, (0, 0, 1.32), seg=10), "metal")
    p.add(rbox((0.17, 0.22, 0.15), (0, 0, 1.53), 0.035, 1), "black")
    p.add(cyl(0.055, 0.035, (0, -0.105, 1.54), rot=(90, 0, 0), seg=10), lambda c, n: "cream" if n.y < -0.9 else "metal")
    p.add(decal([(-0.008, -0.006), (0.008, -0.006), (0.028, 0.03)], frame((0, -0.1405, 1.54), (1, 0, 0), (0, 0, 1))), "red")
    p.add(bar((0, 0.04, 1.625), (0, 0.35, 1.70), 0.085, 0.035, 0.012, up=(0, 0, 1)), "metal")
    p.add(bar((0, 0.03, 1.585), (0, 0.33, 1.585), 0.08, 0.04, 0.012, up=(0, 0, 1)), "black")
    p.add(lathe([(0.026, -0.008), (0.044, 0.0), (0.026, 0.008)], 8, M((-0.085, 0.02, 1.585), (0, 90, 0)), closed=True), "gold")
    hose = tube([(0.08, 0, 1.52), (0.2, -0.01, 1.47), (0.305, -0.03, 1.25), (0.31, -0.05, 0.9), (0.295, -0.06, 0.66)], lambda u: 0.034, k=6, steps=2, caps=False)
    p.add(hose, "black", 70)
    p.add(cyl(0.045, 0.16, (0.295, -0.06, 0.70), rot=(180, 0, 0), seg=8, r2=0.028), "black")
    return p


def p_llave():
    p = Prop("Llave", (0.5, 0.15, 1.8), 400)
    p.add(lathe([(0.1, -0.062), (0.205, -0.075), (0.225, 0.0), (0.205, 0.075), (0.1, 0.062)], 12, M((0, 0, 0.225), (90, 0, 0)), closed=True), "metal")
    p.add(rbox((0.15, 0.085, 1.04), (0, 0, 0.88), 0.03, 1), "metal")
    p.add(rr_loft(0.21, 0.125, 0.05, 2, [(0.035, 0.5), (0.0, 0.55), (0.0, 1.13), (0.035, 1.18)], cap0=False, cap1=False), "orange")
    cx, cz, R, hw = 0.0, 1.56, 0.245, 0.095
    tl = math.radians(-15)
    d = (math.sin(tl), math.cos(tl))
    nn = (math.cos(tl), -math.sin(tl))
    tt = math.sqrt(R * R - hw * hw)
    tipR = (cx + hw * nn[0] + tt * d[0], cz + hw * nn[1] + tt * d[1])
    tipL = (cx - hw * nn[0] + tt * d[0], cz - hw * nn[1] + tt * d[1])
    aR = math.atan2(tipR[1] - cz, tipR[0] - cx)
    aL = math.atan2(tipL[1] - cz, tipL[0] - cx)
    if aL > aR:
        aL -= 2 * math.pi
    pts = []
    na = 13
    for k in range(na):
        a = aR + (aL - aR) * k / (na - 1)
        pts.append((cx + R * math.cos(a), cz + R * math.sin(a)))
    a_l = math.atan2(-nn[1], -nn[0])
    for k in range(5):
        a = a_l + math.pi * k / 4
        pts.append((cx + hw * math.cos(a), cz + hw * math.sin(a)))
    p.add(prism(pts, 0.13, M(rot=(90, 0, 0)), bev=0.016), "metal")
    return p


def crate(p, S, braces=True, battens=True):
    e = S / 2
    k = S / 3.0
    c = e - 0.07 * k
    fw = 0.11 * S
    ch = 0.03 * k
    g = 0.035 * k
    prof = [(0.0, 0.02)]
    for i in (1, 2):
        zb = fw + (S - 2 * fw) * i / 3
        prof += [(0.0, zb - g), (g, zb), (0.0, zb + g)]
    prof.append((0.0, S - 0.03 * k))
    p.add(rr_loft(2 * c, 2 * c, 0, 0, prof), "wood")
    rim = [(ch, 0.0), (0.0, ch), (0.0, fw - ch), (ch, fw), (fw, fw), (fw, 0.0)]
    p.add(rr_loft(S, S, 0, 0, rim, closed=True), "dwood")
    p.add(rr_loft(S, S, 0, 0, [(i, z + S - fw) for i, z in rim], closed=True), "dwood")
    q = e - fw / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.add(bar((sx * q, sy * q, fw), (sx * q, sy * q, S - fw), fw, fw, ch, caps=False), "dwood")
    cs = fw * 1.3
    o = 0.02 * k
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (0, 1):
                xs = sorted((sx * (e - cs), sx * (e + o)))
                ys = sorted((sy * (e - cs), sy * (e + o)))
                zs = (S - cs, S + o) if sz else (0.0, cs)
                bm = bb(xs[0], xs[1], ys[0], ys[1], zs[0], zs[1])
                tgt = Vector((sx * 9, sy * 9, 9 if sz else -9))
                v = max(bm.verts, key=lambda vv: vv.co.dot(tgt))
                bmesh.ops.bevel(bm, geom=[v], offset=0.13 * k, offset_type="OFFSET", segments=1, profile=0.5, affect="VERTICES", clamp_overlap=True)
                p.add(bm, "metal", 30)
    tb = 0.06 * k
    dentro = 0.4 * fw
    lo, hi = -(e - fw + dentro), e - fw + dentro
    if braces:
        for nrm, f in (((0, -1, 0), 1), ((0, 1, 0), -1), ((-1, 0, 0), -1), ((1, 0, 0), 1)):
            nv = Vector(nrm)
            base = nv * (c + tb / 2)
            if abs(nv.y) > 0.5:
                a0 = base + Vector((lo * f, 0, fw - dentro))
                a1 = base + Vector((hi * f, 0, S - fw + dentro))
            else:
                a0 = base + Vector((0, lo * f, fw - dentro))
                a1 = base + Vector((0, hi * f, S - fw + dentro))
            p.add(bar(a0, a1, 0.75 * fw, tb, 0.02 * k, up=nrm, caps=True), "dwood")
    if battens:
        for y in (-S / 5, S / 5):
            p.add(bar((-(e - fw), y, S - 0.03 * k + tb / 2), (e - fw, y, S - 0.03 * k + tb / 2), 0.7 * fw, tb, 0.02 * k, caps=True), "dwood")
    return c


def p_caja():
    p = Prop("Caja", (3.0, 3.0, 3.0), 600)
    crate(p, 3.0)
    return p


def p_caja_fragil():
    p = Prop("CajaFragil", (2.0, 2.0, 2.0), 600)
    c = crate(p, 2.0, braces=False, battens=False)
    gob = [(0.3, 0.5), (0.29, 0.32), (0.22, 0.17), (0.09, 0.09), (0.045, 0.06), (0.045, -0.3), (0.2, -0.36), (0.2, -0.45),
           (-0.2, -0.45), (-0.2, -0.36), (-0.045, -0.3), (-0.045, 0.06), (-0.09, 0.09), (-0.22, 0.17), (-0.29, 0.32), (-0.3, 0.5),
           (-0.08, 0.5), (-0.02, 0.36), (0.03, 0.44), (0.07, 0.5)]
    s = 1.15
    gob = [(x * s, y * s) for x, y in gob]
    for ry, sy in ((0, -1), (180, 1)):
        m = M((0, sy * c, 1.0), (90, 0, ry))
        p.add(prism(gob, 0.035, m, z0=0.0), "red")
        p.add(decal(rect(-0.47, 0.47, -0.62, 0.7), m, 0.006), "cream")
    arrow = [(-0.09, -0.32), (0.09, -0.32), (0.09, 0.04), (0.21, 0.04), (0.0, 0.32), (-0.21, 0.04), (-0.09, 0.04)]
    for rz, sx in ((90, 1), (-90, -1)):
        m = M((sx * c, 0, 1.0), (90, 0, rz))
        p.add(prism(arrow, 0.035, m, z0=0.0), "red")
    return p


def p_maleta(name, body, strap):
    p = Prop(name, (1.6, 0.7, 1.2), 400)
    W, H = 1.6, 0.96
    zc = 0.13 + H / 2
    m = M((0, 0, zc), (90, 0, 0))
    p.add(rr_loft(W, H, 0.16, 2, [(0.06, -0.32), (0.0, -0.26), (0.0, -0.025)], m, cap1=False), body)
    p.add(rr_loft(W, H, 0.16, 2, [(0.0, 0.025), (0.0, 0.26), (0.06, 0.32)], m, cap0=False), body)
    p.add(rr_loft(W, H, 0.16, 2, [(0.025, -0.035), (0.025, 0.035)], m, cap0=False, cap1=False), "dark")
    p.add(rr_loft(0.64, H, 0.06, 1, [(0.0, -0.07), (-0.018, -0.06), (-0.018, 0.06), (0.0, 0.07)], yzx((0, 0, zc)), cap0=False, cap1=False), strap)
    p.add(bb(-0.09, 0.09, -0.364, -0.334, zc - 0.075, zc + 0.075), "gold")
    top = zc + H / 2
    p.add(tube([(-0.3, 0, top - 0.03), (-0.25, 0, top + 0.06), (0.25, 0, top + 0.06), (0.3, 0, top - 0.03)], lambda u: 0.04, k=6, steps=2, caps=False), "dark", 70)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.add(cyl(0.065, 0.06, (sx * 0.64, sy * 0.22, 0.065), rot=(0, 90, 0), seg=8, center=True), "black")
    return p


def p_jaula():
    p = Prop("Jaula", (3.0, 7.0, 2.6), 1200)
    W, L, H = 3.0, 7.0, 2.6
    p.add(rr_loft(W, L, 0, 0, [(0.04, 0.0), (0.0, 0.04), (0.0, 0.22)]), "dwood")
    for i in range(5):
        x = -1.12 + 0.56 * i
        p.add(bar((x, -3.38, 0.26), (x, 3.38, 0.26), 0.52, 0.08, 0.02), "wood")
    t = 0.14
    p.add(rr_loft(W, L, 0, 0, [(0.0, 0.22), (0.0, 0.36), (t, 0.36), (t, 0.22)], closed=True), "dark")
    p.add(rr_loft(W, L, 0, 0, [(0.03, H - 0.16), (0.0, H - 0.13), (0.0, H - 0.03), (0.03, H), (t, H), (t, H - 0.16)], closed=True), "dark")
    px, py = W / 2 - t / 2, L / 2 - t / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.add(bar((sx * px, sy * py, 0.36), (sx * px, sy * py, H - 0.16), t, t, 0.03, caps=False), "dark")
    z0, z1 = 0.36, H - 0.16
    rb = 0.042

    def vbar(x, y):
        p.add(lathe([(rb, z0), (rb, z1)], 6, M((x, y, 0)), cap0=False, cap1=False), "dark", 70)
    n_long = 15
    for i in range(n_long):
        y = -py + 2 * py * (i + 1) / (n_long + 1)
        vbar(-px, y)
        vbar(px, y)
    n_end = 6
    for i in range(n_end):
        x = -px + 2 * px * (i + 1) / (n_end + 1)
        vbar(x, -py)
        vbar(x, py)
    n_top = 11
    for i in range(n_top):
        y = -py + 2 * py * (i + 1) / (n_top + 1)
        p.add(lathe([(rb, -px), (rb, px)], 6, M((0, y, H - 0.08), (0, 90, 0)), cap0=False, cap1=False), "dark", 70)
    for sx in (-1, 1):
        p.add(bar((sx * px, -py, 1.45), (sx * px, py, 1.45), 0.1, 0.12, 0.025, up=(0, 0, 1), caps=False), "dark")
    p.add(bar((-px, -py, 1.45), (px, -py, 1.45), 0.12, 0.1, 0.025, caps=False), "dark")
    p.add(rbox((0.22, 0.09, 0.32), (0.95, -L / 2 - 0.02, 1.45), 0.03, 1), "gold")
    for z in (0.7, 2.1):
        p.add(bb(-1.35, -1.12, -L / 2 - 0.05, -L / 2 + 0.05, z - 0.1, z + 0.1), "metal")
    return p


def gauge(p, m, r=0.17, seg=12, ang=40):
    p.add(lathe([(r, 0.0), (r * 1.08, 0.035), (r * 0.9, 0.058), (r * 0.8, 0.03)], seg, m, cap0=False, cap1=False), "metal")
    p.add(lathe([(r * 0.81, 0.03), (0.0, 0.03)], seg, m, cap0=False, cap1=False), "cream")
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    tip = (r * 0.7 * ca, r * 0.7 * sa)
    side = (-sa * 0.018, ca * 0.018)
    p.add(decal([(side[0], side[1]), (-side[0], -side[1]), tip], m, 0.032), "red")


def p_cuadro():
    p = Prop("Cuadro", (10.0, 2.2, 3.2), 3000)
    body = [(0.6, 0.0), (2.2, 0.0), (2.2, 2.74), (0.72, 2.74), (0.33, 1.38), (0.1, 1.3), (0.1, 1.13), (0.6, 0.98)]
    p.add(bevel_sharp(prism(body, 9.9, yzx()), 0.05, 1, 25), "dark")
    hood = [(0.08, 2.72), (0.08, 2.9), (0.2, 3.02), (1.75, 3.02), (2.2, 2.86), (2.2, 2.72)]
    p.add(bevel_sharp(prism(hood, 10.0, yzx()), 0.045, 2, 25), "black")
    PM = frame((0, 0.33, 1.38), (1, 0, 0), (0, 0.39, 1.36))
    for sx in (-1, 1):
        cu = sx * 3.0
        p.add(rbox((2.9, 1.02, 0.06), (cu, 0.8, 0.03), 0.025, 1, m=PM), "black")
        U = cu + sx * 0.45
        p.add(decal(rect(U - 0.41, U + 0.41, 0.82, 1.22), PM, 0.062), "glass")
        p.add(decal(rect(U - 0.41, U + 0.41, 0.42, 0.82), PM, 0.062), "wood")
        p.add(decal([(U - 0.24, 0.84), (U - 0.06, 0.84), (U, 0.78), (U + 0.06, 0.84), (U + 0.24, 0.84), (U + 0.24, 0.8), (U + 0.07, 0.8), (U, 0.74), (U - 0.07, 0.8), (U - 0.24, 0.8)], PM, 0.065), "gold")
        p.add(decal(rect(U - 0.41, U - 0.31, 0.42, 1.22), PM, 0.064), "dark")
        p.add(decal(rect(U + 0.31, U + 0.41, 0.42, 1.22), PM, 0.064), "dark")
        U = cu - sx * 0.47
        p.add(decal(rect(U - 0.41, U + 0.41, 0.42, 1.22), PM, 0.062), "dark")
        p.add(arc_strip(U, 0.55, 0.3, 0.33, 25, 155, 8, PM, 0.064), "teal")
        p.add(decal([(U - 0.05, 0.5), (U + 0.05, 0.5), (U, 0.62)], PM, 0.065), "white")
        p.add(decal([(U - 0.012, 0.62), (U + 0.012, 0.62), (U + 0.17, 1.02), (U + 0.146, 1.02)], PM, 0.065), "lettuce")
        p.add(decal(circ(U + 0.16, 1.03, 0.03, 4), PM, 0.066), "gold")
        for v in (1.03, 0.58):
            gauge(p, PM @ Matrix.Translation((cu + sx * 1.18, v, 0.06)), ang=35 + 70 * v)
            gauge(p, PM @ Matrix.Translation((cu - sx * 1.18, v, 0.06)), ang=200 - 60 * v)
        for i, col in enumerate(("orange", "teal", "gold", "cream")):
            p.add(rbox((0.2, 0.13, 0.06), (cu + sx * (0.95 - 0.38 * i), 0.15, 0.03), 0.018, 1, m=PM), col)
    p.add(rbox((2.3, 1.02, 0.06), (0, 0.8, 0.03), 0.025, 1, m=PM), "black")
    p.add(decal(rect(-1.0, 0.3, 0.42, 1.22), PM, 0.062), "dark")
    for u in (-0.67, -0.03):
        p.add(arc_strip(u, 0.95, 0.15, 0.19, -40, 220, 8, PM, 0.064), "teal")
        p.add(decal([(u - 0.012, 0.95), (u + 0.012, 0.95), (u + 0.1, 1.07)], PM, 0.065), "white")
    for i, col in enumerate(("orange", "orange", "lettuce", "lettuce")):
        u = -0.85 + 0.27 * i
        p.add(decal(rect(u, u + 0.2, 0.5, 0.6 + 0.04 * (i % 3)), PM, 0.064), col)
    p.add(rbox((0.42, 0.78, 0.04), (0.72, 0.8, 0.08), 0.015, 1, m=PM), "dark")
    p.add(bar(PM @ Vector((0.72, 0.7, 0.09)), PM @ Vector((0.72, 0.78, 0.3)), 0.05, 0.05, 0.012), "metal")
    p.add(cyl(0.09, 0.07, (0.72, 0.785, 0.31), rot=(0, 90, 0), seg=10, center=True, m=PM), "white")
    for i, col in enumerate(("red", "orange", "teal", "gold")):
        p.add(rbox((0.2, 0.13, 0.06), (-0.57 + 0.38 * i, 0.15, 0.03), 0.018, 1, m=PM), col)
    GM = frame((0, 0.08, 2.72), (1, 0, 0), (0, 0, 1))
    p.add(rbox((3.4, 0.16, 0.03), (0, 0.11, 0.015), 0.01, 1, m=GM), "dark")
    for u in (-1.2, -0.4, 0.4, 1.2):
        p.add(cyl(0.045, 0.05, (u, 0.11, 0.03), seg=8, m=GM, cap0=False), "black")
        p.add(decal(rect(u + 0.08, u + 0.3, 0.075, 0.145), GM, 0.031), "glass")
    for sx in (-1, 1):
        p.add(rbox((0.22, 0.14, 0.05), (sx * 2.2, 0.11, 0.025), 0.016, 1, m=GM), "red")
        p.add(rbox((0.22, 0.14, 0.05), (sx * 2.52, 0.11, 0.025), 0.016, 1, m=GM), "gold")
    p.add(rbox((0.32, 0.26, 0.2), (0, 0.55, 3.1), 0.05, 1), "black")
    p.add(decal(circ(0, 0, 0.07, 8), frame((0, 0.419, 3.1), (1, 0, 0), (0, 0, 1))), "cream")
    return p


def p_volante():
    p = Prop("Volante", (1.4, 1.2, 1.4), 600)
    p.add(rbox((0.5, 0.56, 0.08), (0, 0.55, 0.04), 0.03, 1), "dark")
    p.add(cyl(0.15, 0.2, (0, 0.55, 0.06), seg=10, r2=0.09, cap0=False), "black")
    p.add(tube([(0, 0.55, 0.12), (0, 0.52, 0.55), (0, 0.36, 0.86), (0, 0.06, 0.93), (0, -0.12, 0.93)], lambda u: 0.07, k=8, steps=2, caps=False), "dark", 70)
    p.add(rbox((0.36, 0.2, 0.26), (0, -0.2, 0.92), 0.07, 2), "dark")
    p.add(cyl(0.07, 0.03, (0, -0.3, 0.94), rot=(90, 0, 0), seg=8), "gold")
    horns = [(-0.6, 1.3), (-0.62, 1.06), (-0.44, 0.88), (0.0, 0.88), (0.44, 0.88), (0.62, 1.06), (0.6, 1.3)]
    hb = tube([(x, -0.24, z) for x, z in horns], lambda u: 0.066 + 0.03 * abs(2 * u - 1) ** 3, k=8, steps=2, cap_rings=2)
    p.add(hb, lambda c, n: "black" if abs(c.x) > 0.47 else "dark", 70)
    return p


def p_gases():
    p = Prop("Gases", (1.2, 1.6, 1.167), 500)
    prof = [(-0.8, 0.0), (0.8, 0.0), (0.8, 0.92), (0.58, 0.95), (-0.62, 0.8), (-0.8, 0.66)]
    p.add(bevel_sharp(prism(prof, 1.2, yzx()), 0.04, 1, 20), "dark")
    TM = frame((0, -0.62, 0.8), (1, 0, 0), (0, 1.2, 0.15))
    p.add(rbox((0.66, 0.95, 0.1), (0, 0.6, 0.05), 0.03, 1, m=TM), "black")
    for u in (-0.15, 0.15):
        p.add(decal(rect(u - 0.025, u + 0.025, 0.2, 1.0), TM, 0.101), "dark")
        p.add(rbox((0.09, 0.09, 0.03), (u, 0.56, 0.11), 0.012, 1, m=TM), "black")
    for u, col in ((0.44, "cream"), (-0.44, "black")):
        p.add(bar(TM @ Vector((u, 0.5, 0.0)), TM @ Vector((u, 0.42, 0.26)), 0.04, 0.04, 0.01, up=(0, 1, 0)), "metal")
        p.add(rbox((0.1, 0.09, 0.07), (u, 0.415, 0.28), 0.025, 1, m=TM), col)
    FM = frame((0, -0.8, 0.66), (1, 0, 0), (0, 0.18, 0.14))
    for u, col in ((-0.3, "red"), (0.3, "teal")):
        p.add(cyl(0.05, 0.03, (u, 0.114, 0.0), seg=8, m=FM, cap0=False), col)
    return p


def p_palanca_gases():
    p = Prop("PalancaGases", (0.13, 0.17, 0.42), 160)
    p.add(bar((0, 0, 0.0), (0, 0, 0.34), 0.05, 0.05, 0.012, up=(0, 1, 0)), "metal")
    p.add(rbox((0.13, 0.17, 0.11), (0, 0, 0.365), 0.035, 1), "orange")
    return p


def p_asiento_piloto():
    p = Prop("AsientoPiloto", (2.4, 2.6, 4.6), 1000)
    for sx in (-1, 1):
        p.add(bar((sx * 0.55, -1.05, 0.0), (sx * 0.55, 1.05, 0.0), 0.18, 0.12, 0.04), "metal")
    p.add(rbox((0.7, 0.9, 0.85), (0, -0.1, 0.5), 0.06, 1), "metal")
    p.add(bb(-1.0, 1.0, -1.2, 0.85, 0.9, 1.06, 0.04), "black")
    p.add(rbox((0.86, 1.95, 0.44), (0, -0.3, 1.28), 0.14, 2), "teal")
    for sx in (-1, 1):
        p.add(rbox((0.58, 2.05, 0.56), (sx * 0.71, -0.27, 1.32), 0.16, 1), "dark")
    a = math.radians(10)
    ax = Vector((0, math.sin(a), math.cos(a)))
    nb = Vector((0, math.cos(a), -math.sin(a)))
    B = Vector((0, 0.47, 1.2))
    p.add(rbox((0.86, 0.42, 2.4), B + ax * 1.25 - nb * 0.04, 0.14, 2, rot=(-10, 0, 0)), "teal")
    for sx in (-1, 1):
        p.add(rbox((0.58, 0.56, 2.5), B + ax * 1.25 + Vector((sx * 0.71, 0, 0)), 0.16, 1, rot=(-10, 0, 0)), "dark")
        p.add(bar(B + ax * 2.4 + Vector((sx * 0.32, 0, 0)), B + ax * 2.72 + Vector((sx * 0.32, 0, 0)), 0.07, 0.07, 0.02, up=nb, caps=False), "metal")
    p.add(rbox((1.3, 0.5, 0.8), B + ax * 3.0, 0.18, 2, rot=(-10, 0, 0)), "dark")
    for sx in (-1, 1):
        p.add(rbox((0.24, 1.3, 0.16), (sx * 1.08, -0.35, 2.15), 0.06, 1), "dark")
        p.add(bar((sx * 1.08, -0.75, 1.0), (sx * 1.08, -0.6, 2.1), 0.14, 0.14, 0.035, up=(0, 1, 0)), "dark")
        p.add(bar(B + ax * 2.42 - nb * 0.27 + Vector((sx * 0.28, 0, 0)), B + ax * 0.42 - nb * 0.27 + Vector((sx * 0.2, 0, 0)), 0.12, 0.03, 0.0, up=-nb), "orange")
    p.add(bar(B + ax * 0.36 - nb * 0.28 + Vector((-0.43, 0, 0)), B + ax * 0.36 - nb * 0.28 + Vector((0.43, 0, 0)), 0.13, 0.03, 0.0, up=-nb), "orange")
    p.add(rbox((0.24, 0.05, 0.18), B + ax * 0.36 - nb * 0.3, 0.0, rot=(-10, 0, 0)), "gold")
    return p


def p_carrito():
    p = Prop("Carrito", (1.6, 2.6, 3.2), 600)
    p.add(bb(-0.78, 0.78, -1.2, 1.2, 0.28, 3.04, 0.07, 2), "metal")
    p.add(rr_loft(1.6, 2.48, 0, 0, [(0.0, 2.98), (0.0, 3.2), (0.07, 3.2), (0.07, 3.06)], closed=True), "dark")
    for z0, z1 in ((0.42, 1.28), (1.36, 2.12), (2.2, 2.92)):
        p.add(rbox((1.36, 0.06, z1 - z0), (0, -1.21, (z0 + z1) / 2), 0.025, 1), "orange")
        p.add(bar((-0.28, -1.265, z1 - 0.14), (0.28, -1.265, z1 - 0.14), 0.07, 0.05, 0.015, up=(0, -1, 0)), "dark")
    p.add(rbox((1.36, 0.06, 2.5), (0, 1.21, 1.67), 0.025, 1), "orange")
    for sx in (-1, 1):
        p.add(bb(sx * 0.78 - 0.015, sx * 0.78 + 0.015, -1.02, 1.02, 2.55, 2.75), "orange")
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 0.52, sy * 0.95
            p.add(cyl(0.12, 0.1, (x, y, 0.12), rot=(0, 90, 0), seg=8, center=True), "black")
            p.add(bb(x - 0.075, x + 0.075, y - 0.05, y + 0.05, 0.14, 0.29), "dark")
    return p


def p_cafetera():
    p = Prop("Cafetera", (1.4, 1.0, 1.6), 500)
    p.add(bb(-0.7, 0.7, -0.5, 0.5, 0.0, 0.16, 0.04, 1), "dark")
    p.add(bb(-0.34, 0.34, -0.44, 0.12, 0.16, 0.2), "metal")
    p.add(bb(-0.64, 0.64, 0.06, 0.48, 0.14, 1.26, 0.06, 1), "metal")
    p.add(bb(-0.7, 0.7, -0.465, 0.5, 1.2, 1.6, 0.1, 2), "orange")
    FM = frame((0, -0.465, 1.4), (1, 0, 0), (0, 0, 1))
    p.add(decal(rect(-0.52, -0.08, -0.08, 0.08), FM, 0.004), "black")
    p.add(decal(rect(-0.48, -0.26, -0.045, 0.045), FM, 0.006), "glass")
    for u, col in ((0.12, "teal"), (0.3, "red"), (0.48, "cream")):
        p.add(cyl(0.055, 0.035, (u, 0, 0), seg=8, m=FM, cap0=False), col)
    p.add(cyl(0.08, 0.12, (0, -0.14, 1.08), seg=10, cap1=False), "dark")
    s = 1.25
    prof = [(0.17, 0.0), (0.23, 0.05 * s), (0.245, 0.24 * s), (0.2, 0.44 * s), (0.165, 0.52 * s)]
    p.add(lathe(prof, 10, M((0, -0.14, 0.2)), cap1=False), lambda c, n: "patty" if c.z < 0.2 + 0.24 * s else "glass")
    p.add(cyl(0.172, 0.07, (0, -0.14, 0.2 + 0.52 * s - 0.01), seg=10, r2=0.09, cap0=False), "black")
    p.add(tube([(0.15, -0.14, 0.8), (0.33, -0.14, 0.75), (0.36, -0.14, 0.5), (0.22, -0.14, 0.33)], lambda u: 0.035, k=5, steps=2, caps=False), "black", 70)
    return p


def p_nevera():
    p = Prop("Nevera", (1.8, 1.2, 1.3), 400)
    p.add(rr_loft(1.7, 1.1, 0.2, 2, [(0.06, 0.0), (0.0, 0.07), (0.0, 0.6), (0.0, 0.72), (0.0, 1.0)], cap1=False),
          lambda c, n: "white" if 0.6 < c.z < 0.72 and abs(n.z) < 0.5 else "teal")
    p.add(rr_loft(1.8, 1.2, 0.24, 2, [(0.0, 0.96), (0.0, 1.17), (0.05, 1.26), (0.16, 1.3)]), "white")
    for sx in (-1, 1):
        p.add(rbox((0.08, 0.5, 0.14), (sx * 0.86, 0, 0.82), 0.03, 1), "white")
    p.add(rbox((0.26, 0.07, 0.24), (0, -0.585, 1.0), 0.03, 1), "white")
    for x in (-0.5, 0.5):
        p.add(decal(circ(x, -0.22, 0.12, 8), M((0, 0, 1.3005))), "teal")
    return p


def p_inodoro():
    p = Prop("Inodoro", (1.4, 2.0, 2.2), 600)
    by, sy = -0.32, 1.12
    bowl = [(0.34, 0.0), (0.4, 0.05), (0.41, 0.3), (0.52, 0.61), (0.585, 0.8), (0.44, 0.8), (0.28, 0.58), (0.0, 0.54)]
    p.add(lathe(bowl, 14, M((0, by, 0)), sy=sy, cap1=False),
          lambda c, n: "glass" if 0.4 < c.z < 0.62 and (c.x ** 2 + ((c.y - by) / sy) ** 2) < 0.3 ** 2 else "white")
    p.add(lathe([(0.4, 0.8), (0.6, 0.8), (0.6, 0.865), (0.42, 0.865)], 16, M((0, by, 0)), sy=sy, closed=True), "teal")
    hy = by + 0.6 * sy
    lid = lathe([(0.585, 0.0), (0.6, 0.035), (0.575, 0.07), (0.0, 0.075)], 16, None, sy=sy)
    xf(lid, Matrix.Translation((0, hy, 0.865)) @ Matrix.Rotation(math.radians(-95), 4, "X") @ Matrix.Translation((0, -0.6 * sy, 0)))
    p.add(lid, "teal")
    p.add(bb(-0.32, 0.32, 0.12, 0.62, 0.0, 0.8, 0.05, 1), "white")
    p.add(rr_loft(1.34, 0.4, 0.08, 2, [(0.0, 0.8), (0.0, 1.9)], M((0, 0.8, 0)), cap0=False, cap1=False), "white")
    p.add(rr_loft(1.4, 0.46, 0.1, 2, [(0.0, 1.88), (0.0, 1.96), (0.05, 2.0)], M((0, 0.8, 0))), "white")
    p.add(cyl(0.1, 0.045, (0, 0.8, 2.0), seg=10, cap0=False), "red")
    return p


def p_boton():
    p = Prop("Boton", (0.8, 0.8, 0.4), 200)
    p.add(lathe([(0.4, 0.0), (0.4, 0.1), (0.35, 0.15), (0.28, 0.15)], 12, cap1=False), "dark")
    p.add(lathe([(0.27, 0.13), (0.295, 0.165), (0.255, 0.19)], 12, cap0=False, cap1=False), "metal")
    p.add(lathe([(0.24, 0.17), (0.24, 0.3), (0.17, 0.38), (0.0, 0.4)], 12, cap0=False), "red")
    return p


def contorno_dentro(pts, ins):
    n = len(pts)
    out = []
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        n1 = Vector((b[1] - a[1], -(b[0] - a[0]))).normalized()
        n2 = Vector((c[1] - b[1], -(c[0] - b[0]))).normalized()
        mi = n1 + n2
        mi = mi.normalized() if mi.length > 1e-6 else n1
        k = max(mi.dot(n1), 0.35)
        out.append((b[0] - mi.x * ins / k, b[1] - mi.y * ins / k))
    return out


def loft_contorno(pts, prof, m=None, cap0=True, cap1=True):
    if area2(pts) < 0:
        pts = pts[::-1]
    bm = bmesh.new()
    rings = [[bm.verts.new((x, y, z)) for x, y in contorno_dentro(pts, ins)] for ins, z in prof]
    N = len(pts)
    for a, b in zip(rings, rings[1:]):
        for j in range(N):
            j2 = (j + 1) % N
            bm.faces.new((a[j], a[j2], b[j2], b[j]))
    if cap0:
        bm.faces.new(list(reversed(rings[0])))
    if cap1:
        bm.faces.new(rings[-1])
    return xf(bm, m)


def recortar_y(pts, y0):
    out = []
    n = len(pts)
    for i in range(n):
        p, q = pts[i], pts[(i + 1) % n]
        if p[1] >= y0:
            out.append(p)
        if (p[1] >= y0) != (q[1] >= y0):
            t = (y0 - p[1]) / (q[1] - p[1])
            out.append((p[0] + (q[0] - p[0]) * t, y0))
    return out


PIANO_CURVA = [(1.7, -0.75), (1.62, -0.35), (1.27, 0.15), (0.78, 0.62), (0.44, 1.2), (0.3, 1.78), (-0.05, 2.22), (-0.7, 2.38),
               (-1.32, 2.22), (-1.64, 1.78), (-1.7, 1.0)]


def contorno_piano():
    r = 0.16
    pts = [(1.7 - r + r * math.cos(math.radians(a)), -1.45 + r + r * math.sin(math.radians(a))) for a in (-90, -60, -30, 0)]
    pts += [(q.x, q.y) for q in catmull([Vector(c) for c in PIANO_CURVA], 3)]
    pts += [(-1.7, -0.2)]
    pts += [(-1.7 + r + r * math.cos(math.radians(a)), -1.45 + r + r * math.sin(math.radians(a))) for a in (180, 210, 240, 270)]
    return pts


def y_cola(pts, x):
    ys = []
    n = len(pts)
    for i in range(n):
        p, q = pts[i], pts[(i + 1) % n]
        if (p[0] - x) * (q[0] - x) <= 0 and p[0] != q[0]:
            t = (x - p[0]) / (q[0] - p[0])
            ys.append(p[1] + (q[1] - p[1]) * t)
    return max(ys)


def p_piano():
    p = Prop("Piano", (3.52, 4.68, 2.97), 4600)
    out = contorno_piano()
    p.add(loft_contorno(out, [(0.08, 0.95), (0.0, 1.04), (0.0, 1.12), (0.0, 1.17), (0.0, 1.87), (0.035, 1.95), (0.1, 1.95), (0.135, 1.9), (0.135, 1.76)], cap0=True),
          lambda c, n: "gold" if (n.z > 0.9 and c.z < 1.85) or (abs(n.z) < 0.3 and 1.12 < c.z < 1.17) else "black")
    for k in range(9):
        x = -1.42 + k * 0.3
        y1 = y_cola(out, x) - 0.24
        if y1 > -0.5:
            p.add(lathe([(0.014, -0.9), (0.014, y1)], 5, M((x, 0, 1.805), (-90, 0, 0)), cap0=False, cap1=False), "white", 80)
    for x, y in ((-1.1, -0.7), (0.9, -0.7), (-0.2, 1.4)):
        p.add(cyl(0.07, 0.06, (x, y, 1.76), seg=8), "dwood")
    p.add(bb(-1.6, 1.6, -1.38, -0.95, 1.7, 2.0, 0.025), "black")
    bisagra = Vector((-1.73, 0.0, 1.95))
    ml = Matrix.Translation(bisagra) @ Matrix.Rotation(math.radians(-16), 4, "Y") @ Matrix.Translation(-bisagra)
    tapa = recortar_y(contorno_dentro(out, -0.03), -0.72)
    p.add(loft_contorno(tapa, [(0.0, 1.955), (0.0, 1.995), (0.03, 2.025)], ml), lambda c, n: "dark" if n.z < -0.5 else "black")
    p.add(bar((1.05, 0.0, 1.74), ml @ Vector((1.05, 0.0, 1.98)), 0.07, 0.07, 0.02, caps=True), "dark")
    p.add(bb(-1.5, 1.5, -2.14, -1.4, 1.08, 1.36, 0.03), "black")
    for sx in (-1, 1):
        xs = sorted((sx * 1.5, sx * 1.72))
        p.add(bb(xs[0], xs[1], -2.2, -1.38, 1.04, 1.62, 0.05, 2), "black")
    nb = 14
    w = 3.0 / nb
    for i in range(nb):
        x0 = -1.5 + i * w + 0.012
        p.add(bb(x0, x0 + w - 0.024, -2.1, -1.52, 1.36, 1.46, 0.012), "white", 60)
    for o in (0, 7):
        for i in (0, 1, 3, 4, 5):
            xc = -1.5 + (o + i + 1) * w
            p.add(bb(xc - 0.065, xc + 0.065, -1.84, -1.5, 1.46, 1.57, 0.018), "black", 60)
    p.add(bb(-1.5, 1.5, -1.52, -1.4, 1.36, 1.66, 0.025), "black")
    p.add(rbox((0.46, 0.08, 0.07), (0, -1.535, 1.56), 0.02, 1), "gold")
    md = M((0, -1.12, 1.98), (-12, 0, 0))
    p.add(rbox((1.7, 0.07, 0.58), (0, 0, 0.29), 0.025, 1, m=md), "black")
    p.add(rbox((1.0, 0.03, 0.44), (0, -0.085, 0.31), 0.0, m=md), "cream")
    for x, z, s in ((-0.32, 0.22, 1), (-0.1, 0.36, -1), (0.12, 0.27, 1), (0.32, 0.41, -1)):
        p.add(xf(ellipsoid((0.045, 0.02, 0.034), M((x, -0.13, z), (0, 20 * s, 0)), 6, 4), md), "black", 70)
        p.add(bar(md @ Vector((x + 0.038, -0.15, z)), md @ Vector((x + 0.038, -0.15, z + 0.16)), 0.016, 0.012, 0.0, up=md.to_3x3() @ Vector((0, -1, 0))), "black")

    def pata(x, y):
        p.add(lathe([(0.13, 0.36), (0.17, 0.4), (0.17, 0.48), (0.115, 0.57), (0.13, 0.7), (0.19, 0.84), (0.22, 0.94), (0.22, 1.12)], 12, M((x, y, 0)), cap1=False), "black")
        p.add(bb(x - 0.15, x + 0.15, y - 0.09, y + 0.09, 0.3, 0.34, 0.012), "gold")
        for sx in (-1, 1):
            xs = sorted((x + sx * 0.12, x + sx * 0.15))
            p.add(bb(xs[0], xs[1], y - 0.08, y + 0.08, 0.13, 0.31, 0.01), "gold")
        p.add(cyl(0.15, 0.12, (x, y, 0.15), (0, 90, 0), seg=12, center=True, bev=0.025), "black")
        p.add(cyl(0.055, 0.4, (x, y, 0.15), (0, 90, 0), seg=8, center=True), "gold")
    for x, y in ((-1.28, -1.08), (1.28, -1.08), (-0.55, 1.72)):
        pata(x, y)
    for sx in (-1, 1):
        p.add(bar((sx * 0.14, -1.0, 0.5), (sx * 0.14, -1.0, 1.08), 0.07, 0.07, 0.02, caps=False), "black")
    p.add(rbox((0.5, 0.22, 0.13), (0, -1.0, 0.46), 0.04, 1), "black")
    for x in (-0.13, 0.0, 0.13):
        p.add(bar((x, -1.08, 0.43), (x, -1.32, 0.42), 0.06, 0.035, 0.012), "gold")
    tag = [(x * 1.4, y * 1.4) for x, y in ((-0.13, -0.22), (0.13, -0.22), (0.13, 0.12), (0.05, 0.2), (-0.05, 0.2), (-0.13, 0.12))]
    mt = M((1.6, -2.1, 0.72), (90, 0, 8))
    p.add(prism(tag, 0.03, mt, bev=0.01), "orange")
    p.add(prism(rect(-0.13, 0.13, -0.12, 0.03), 0.06, mt, z0=0.035), "cream")
    for k in range(2):
        p.add(prism(rect(-0.1, 0.1 - 0.07 * k, -0.04 - 0.05 * k, -0.02 - 0.05 * k), 0.07, mt, z0=0.088), "black")
    p.add(tube([(1.6, -2.06, 1.1), (1.62, -2.12, 1.04), (1.6, -2.11, 0.99)], lambda u: 0.014, k=5, steps=2, caps=False), "black", 80)
    return p


def p_bombona():
    p = Prop("Bombona", (0.824, 0.944, 1.98), 1300)
    seg = 16
    a0 = math.pi / seg
    prof = [(0.0, 0.1), (0.2, 0.105), (0.33, 0.14), (0.4, 0.21), (0.42, 0.32), (0.42, 0.9), (0.42, 1.12), (0.42, 1.3), (0.4, 1.4),
            (0.35, 1.5), (0.26, 1.58), (0.14, 1.63), (0.1, 1.64)]

    def cuerpo(c, n):
        return "white" if 0.9 < c.z < 1.12 and abs(n.z) < 0.5 else "red"
    p.add(lathe(prof, seg, cap1=False, a0=a0), cuerpo)
    p.add(lathe([(0.31, 0.0), (0.37, 0.0), (0.38, 0.03), (0.38, 0.15), (0.36, 0.17), (0.31, 0.17)], seg, closed=True, a0=a0), "dark")
    p.add(cyl(0.1, 0.2, (0, 0, 1.6), seg=10), "gold")
    p.add(rbox((0.16, 0.16, 0.14), (0, 0, 1.78), 0.035, 1), "gold")
    p.add(cyl(0.05, 0.16, (0.06, 0, 1.76), rot=(0, 90, 0), seg=8), "gold")
    p.add(cyl(0.065, 0.05, (0.22, 0, 1.76), rot=(0, 90, 0), seg=8, bev=0.012), "gold")
    p.add(cyl(0.03, 0.12, (0, 0, 1.84), seg=6), "metal")
    p.add(lathe([(0.09, -0.025), (0.15, -0.03), (0.165, 0.0), (0.15, 0.03), (0.09, 0.025)], 12, M((0, 0, 1.95)), closed=True), "dark")
    for k in range(2):
        a = math.radians(45 + 90 * k)
        p.add(bar((0.105 * math.cos(a), 0.105 * math.sin(a), 1.95), (-0.105 * math.cos(a), -0.105 * math.sin(a), 1.95), 0.03, 0.025, 0.008), "dark")
    p.add(lathe([(0.27, -0.06), (0.31, -0.07), (0.33, 0.0), (0.31, 0.07), (0.27, 0.06)], seg, M((0, 0, 1.72)), closed=True, a0=a0), "metal")
    for k in range(3):
        a = math.radians(90 + 120 * k)
        b0 = Vector((0.27 * math.cos(a), 0.27 * math.sin(a), 1.48))
        b1 = Vector((0.29 * math.cos(a), 0.29 * math.sin(a), 1.7))
        p.add(bar(b0, b1, 0.06, 0.05, 0.015, up=(math.cos(a), math.sin(a), 0)), "metal")
    ap = 0.42 * math.cos(math.pi / seg)
    md = M((0, -ap, 0.6), (90, 0, 0))
    rombo = [(0.0, -0.17), (0.17, 0.0), (0.0, 0.17), (-0.17, 0.0)]
    p.add(prism(rombo, 0.1, md, bev=0.012, z0=-0.04), "white")
    llama = [(0.0, -0.11), (0.07, -0.08), (0.09, -0.02), (0.07, 0.04), (0.03, 0.12), (0.025, 0.05), (0.0, 0.08), (-0.035, 0.02),
             (-0.05, 0.08), (-0.08, 0.0), (-0.075, -0.07)]
    p.add(prism(llama, 0.06, md @ M((0, 0, 0.06)), z0=0.0), "orange")
    return p


BUILDERS = [
    p_asiento, p_bandeja, p_hamburguesa, p_cafe, p_agua, p_extintor, p_llave, p_caja, p_caja_fragil,
    lambda: p_maleta("Maleta1", "orange", "cream"),
    lambda: p_maleta("Maleta2", "teal", "orange"),
    lambda: p_maleta("Maleta3", "red", "cream"),
    p_jaula, p_cuadro, p_volante, p_gases, p_palanca_gases, p_asiento_piloto, p_carrito, p_cafetera, p_nevera, p_inodoro, p_boton,
    p_piano, p_bombona,
]


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
    return verts, faces, uvs, nrms, tris, raw, sc


def palette_image():
    img = bpy.data.images.new("props_palette", 64, 64, alpha=True)
    px = [0.0] * (64 * 64 * 4)
    for i, (_, hx) in enumerate(PAL):
        r, g, b = hex_rgb(hx)
        gx, gy = i % 4, i // 4
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * 64 + x) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "props_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def palette_material(img):
    mat = bpy.data.materials.new("Props_Palette")
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
    verts, faces, uvs, nrms, tris, raw, sc = finalize(p)
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
    return ob, tris, raw, sc


def export_fbx(ob):
    _SEP["separar_capas"](ob)
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


SHEETS = [
    ("props_1.png", [["Caja", "Nevera", "CajaFragil", "Inodoro"], ["Asiento", "AsientoPiloto", "Carrito", ("Jaula", -80)]], 1.0, 0.34),
    ("props_2.png", [["Volante", "Gases", "Boton", "Extintor", "Cafetera"], [("Cuadro", -6)]], 0.7, 0.19),
    ("props_3.png", [["Bandeja", "Hamburguesa", "Cafe", "Agua"], ["Maleta1", "Maleta2", "Maleta3", "Llave"]], 0.42, 0.105),
    ("props_4.png", [["Piano", ("Piano", 150), ("Bombona", -30)]], 0.7, 0.2),
    ("props_5.png", [[("Bombona", -30), ("Bombona", 160)]], 0.25, 0.08),
]


def render_setup(scene, threads):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    scene.cycles.max_bounces = 4
    scene.render.threads_mode = "FIXED"
    scene.render.threads = threads
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    world = bpy.data.worlds.new("Sky")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*lin(hex_rgb("BFE3F2")), 1.0)
    bg.inputs[1].default_value = 0.75
    scene.world = world
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.6
    sun.angle = math.radians(12)
    so = bpy.data.objects.new("Sun", sun)
    so.rotation_euler = (math.radians(46), 0.0, math.radians(-32))
    scene.collection.objects.link(so)
    gm = bpy.data.materials.new("Ground")
    gm.use_nodes = True
    gb = gm.node_tree.nodes["Principled BSDF"]
    gb.inputs["Base Color"].default_value = (*lin(hex_rgb("D6EEF7")), 1.0)
    gb.inputs["Roughness"].default_value = 0.95
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=200)
    gme = bpy.data.meshes.new("Ground")
    bm.to_mesh(gme)
    gme.materials.append(gm)
    scene.collection.objects.link(bpy.data.objects.new("Ground", gme))
    tm = bpy.data.materials.new("Label")
    tm.use_nodes = True
    tm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin(hex_rgb("34383F")), 1.0)
    return tm


def fit_camera(scene, pts, el, az, lens):
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    f = -d
    right = f.cross(Vector((0, 0, 1))).normalized()
    upv = right.cross(f).normalized()
    tx = math.tan(math.atan(18.0 / lens))
    ty = tx * scene.render.resolution_y / scene.render.resolution_x
    c = sum(pts, Vector()) / len(pts)
    for _ in range(4):
        q = [(p - c).dot(right) for p in pts], [(p - c).dot(upv) for p in pts], [(p - c).dot(d) for p in pts]
        D = max(max(z + abs(x) / (tx * 0.92) for x, z in zip(q[0], q[2])), max(z + abs(y) / (ty * 0.9) for y, z in zip(q[1], q[2])))
        sxs = [x / (D - z) for x, z in zip(q[0], q[2])]
        sys_ = [y / (D - z) for y, z in zip(q[1], q[2])]
        c = c + right * ((max(sxs) + min(sxs)) / 2 * D) + upv * ((max(sys_) + min(sys_)) / 2 * D)
    q = [(p - c).dot(right) for p in pts], [(p - c).dot(upv) for p in pts], [(p - c).dot(d) for p in pts]
    D = max(max(z + abs(x) / (tx * 0.92) for x, z in zip(q[0], q[2])), max(z + abs(y) / (ty * 0.9) for y, z in zip(q[1], q[2])))
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.clip_end = 1000
    co = bpy.data.objects.new("Cam", cd)
    scene.collection.objects.link(co)
    co.location = c + d * D
    co.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    scene.camera = co
    return co


def render_sheets(objs, which, threads, outdir):
    scene = bpy.context.scene
    tm = render_setup(scene, threads)
    for o in objs.values():
        o.hide_render = True
    el, az = math.radians(30), math.radians(-10)
    for si, (fname, rows, gap, lsize) in enumerate(SHEETS):
        if which and str(si + 1) not in which:
            continue
        made = []
        ycur = 0.0
        for row in rows:
            items = []
            for it in row:
                nm, rz = (it if isinstance(it, tuple) else (it, -24))
                o = objs[nm]
                w, d = o.dimensions.x, o.dimensions.y
                a = math.radians(rz)
                fw = abs(w * math.cos(a)) + abs(d * math.sin(a))
                fd = abs(w * math.sin(a)) + abs(d * math.cos(a))
                items.append((nm, rz, fw, fd))
            total = sum(i[2] for i in items) + gap * (len(items) - 1)
            rd = max(i[3] for i in items)
            if made:
                ycur += rd / 2
            x = -total / 2
            for nm, rz, fw, fd in items:
                cx, cy = x + fw / 2, ycur
                inst = bpy.data.objects.new(nm + "_v", objs[nm].data)
                scene.collection.objects.link(inst)
                inst.location = (cx, cy, 0)
                inst.rotation_euler = (0, 0, math.radians(rz))
                made.append(inst)
                cu = bpy.data.curves.new(nm + "_t", "FONT")
                cu.body = nm
                cu.align_x = "CENTER"
                cu.size = lsize
                cu.materials.append(tm)
                lo = bpy.data.objects.new(nm + "_t", cu)
                scene.collection.objects.link(lo)
                lo.location = (cx, cy - fd / 2 - lsize * 0.9 - gap * 0.15, lsize * 0.3)
                lo.rotation_euler = (math.radians(90) - el, 0, 0)
                made.append(lo)
                x += fw + gap
            hmax = max(objs[i[0]].dimensions.z for i in items)
            ycur += rd / 2 + gap + lsize * 2.2 + 0.75 * hmax / math.tan(el)
        bpy.context.view_layer.update()
        pts = []
        for o in made:
            for corner in o.bound_box:
                pts.append(o.matrix_world @ Vector(corner))
        co = fit_camera(scene, pts, el, az, 50)
        scene.render.filepath = os.path.join(outdir, fname)
        bpy.ops.render.render(write_still=True)
        print("RENDER", scene.render.filepath)
        for o in made:
            data = o.data
            bpy.data.objects.remove(o)
            if isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)
        bpy.data.objects.remove(co)


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
        ob, tris, raw, sc = make_object(p, mat)
        objs[p.name] = ob
        flag = "OK" if tris <= p.budget else "OVER"
        if tris > p.budget:
            ok = False
        warn = " SCALE!" if any(abs(s - 1.0) > 0.08 for s in sc) else ""
        print("PROP %-14s tris %5d / %5d %s  raw %.3f x %.3f x %.3f  fit %.3f %.3f %.3f%s" % (p.name, tris, p.budget, flag, raw.x, raw.y, raw.z, sc[0], sc[1], sc[2], warn))
        if not arg("--no-export"):
            export_fbx(ob)
        dim = ob.dimensions
        manifest.append({"nombre": p.name, "archivo": p.name + ".fbx", "tamano": [round(dim.x, 3), round(dim.z, 3), round(dim.y, 3)], "triangulos": tris})
    if not arg("--no-export"):
        ruta = os.path.join(OUT, "manifest.json")
        if only and os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as fh:
                manifest = [e for e in json.load(fh) if e["nombre"] not in objs] + manifest
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("ALL BUDGETS OK" if ok else "SOME PROPS OVER BUDGET")
    if arg("--no-render"):
        return
    which = arg("--sheets")
    which = set(which.split(",")) if isinstance(which, str) else None
    outdir = arg("--render-dir")
    outdir = outdir if isinstance(outdir, str) else OUT
    threads = arg("--threads")
    render_sheets(objs, which, int(threads) if isinstance(threads, str) else 2, outdir)


main()
