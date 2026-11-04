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
    ("sand", "F2D9A0"), ("dsand", "D9B877"), ("sea", "2FB3C4"), ("dsea", "1F8A9E"),
    ("trunk", "9C6B3E"), ("dwood", "6E4A2B"), ("leaf", "6DBE45"), ("dleaf", "3D9447"),
    ("coco", "7A4A2A"), ("rock", "9AA0A6"), ("drock", "6B7178"), ("red", "D9443A"),
    ("cream", "FFF4E0"), ("orange", "F27B2B"), ("teal", "1FA6A0"), ("black", "1B1B21"),
    ("yellow", "F6C445"), ("white", "F7F7F2"), ("metal", "A9B0B8"), ("glass", "8FD3F4"),
    ("dteal", "157F7B"), ("pink", "F29BB2"), ("lgrass", "8DC85C"), ("wsand", "C9A866"),
]
IDX = {n: i for i, (n, _) in enumerate(PAL)}


def suv(n):
    i = IDX[n]
    return ((i % 8 + 0.5) / 8.0, (i // 8 + 0.5) / 4.0)


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
    w = st
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
    img = bpy.data.images.new("isla_palette", 128, 64, alpha=True)
    px = [0.0] * (128 * 64 * 4)
    for i, (_, hx) in enumerate(PAL):
        r, g, b = hex_rgb(hx)
        gx, gy = i % 8, i // 8
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * 128 + x) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "isla_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def palette_material(img):
    mat = bpy.data.materials.new("Isla_Palette")
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



def fit_camera(st, pts, el, az, lens):
    scene = bpy.context.scene
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    f = -d
    right = f.cross(Vector((0, 0, 1))).normalized()
    upv = right.cross(f).normalized()
    tx = 18.0 / lens
    ty = tx * scene.render.resolution_y / scene.render.resolution_x
    c = sum(pts, Vector()) / len(pts)
    for _ in range(5):
        q = [(p - c).dot(right) for p in pts], [(p - c).dot(upv) for p in pts], [(p - c).dot(d) for p in pts]
        D = max(max(z + abs(x) / (tx * 0.92) for x, z in zip(q[0], q[2])), max(z + abs(y) / (ty * 0.9) for y, z in zip(q[1], q[2])))
        sxs = [x / (D - z) for x, z in zip(q[0], q[2])]
        sys_ = [y / (D - z) for y, z in zip(q[1], q[2])]
        c = c + right * ((max(sxs) + min(sxs)) / 2 * D) + upv * ((max(sys_) + min(sys_)) / 2 * D)
    q = [(p - c).dot(right) for p in pts], [(p - c).dot(upv) for p in pts], [(p - c).dot(d) for p in pts]
    D = max(max(z + abs(x) / (tx * 0.92) for x, z in zip(q[0], q[2])), max(z + abs(y) / (ty * 0.9) for y, z in zip(q[1], q[2])))
    return st.camera(c + d * D, c, lens)


def sheet_catalog(st, rows, gap):
    st.quad(-400, 400, -400, 400, 0.0, mat_rgb("D6EEF7", 0.95))
    ycur = 0.0
    made = []
    for row in rows:
        items = [(nm, st.objs[nm].dimensions.x, st.objs[nm].dimensions.y) for nm in row]
        total = sum(i[1] for i in items) + gap * (len(items) - 1)
        rd = max(i[2] for i in items)
        if made:
            ycur += rd / 2
        x = -total / 2
        for nm, w, dd in items:
            made.append(st.put(nm, x + w / 2, ycur, -24))
            x += w + gap
        ycur += rd / 2 + gap * 1.5
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in made for c in o.bound_box]
    fit_camera(st, pts, math.radians(28), math.radians(-12), 50)



def palo(p0, p1, r, seg=6, r2=None, cap0=True, cap1=True):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    m = Matrix.Translation(p0) @ q.to_matrix().to_4x4()
    return lathe([(r, 0.0), (r if r2 is None else r2, d.length)], seg, m, cap0=cap0, cap1=cap1)


def hoja(spine, anchos, caida=0.35, grosor=0.05):
    bm = bmesh.new()
    n = len(spine)
    capas = []
    for capa in (0, 1):
        off = Vector((0, 0, -grosor * capa))
        mid, izq, der = [], [], []
        for i, p in enumerate(spine):
            t = (spine[min(i + 1, n - 1)] - spine[max(i - 1, 0)]).normalized()
            lado = t.cross(Vector((0, 0, 1)))
            if lado.length < 1e-4:
                lado = Vector((1, 0, 0))
            lado.normalize()
            w = anchos[i]
            mid.append(bm.verts.new(p + off))
            izq.append(bm.verts.new(p + lado * w - Vector((0, 0, caida * w)) + off))
            der.append(bm.verts.new(p - lado * w - Vector((0, 0, caida * w)) + off))
        capas.append((mid, izq, der))
    for capa, (mid, izq, der) in enumerate(capas):
        for i in range(n - 1):
            a = (mid[i], izq[i], izq[i + 1], mid[i + 1])
            b = (mid[i], mid[i + 1], der[i + 1], der[i])
            if capa:
                a, b = a[::-1], b[::-1]
            for f in (a, b):
                try:
                    bm.faces.new(f)
                except ValueError:
                    pass
    return bm


def estrella_pts(cx, cy, r0, r1, n=5, giro=90.0):
    return [(cx + (r0 if k % 2 == 0 else r1) * math.cos(math.radians(giro + 180.0 * k / n)), cy + (r0 if k % 2 == 0 else r1) * math.sin(math.radians(giro + 180.0 * k / n))) for k in range(2 * n)]


def mancha(cx, cy, r, semilla, n=9, irregular=0.35):
    rnd = random.Random(semilla)
    ctrl = [Vector((cx + r * (1 + rnd.uniform(-irregular, irregular)) * math.cos(2 * math.pi * k / n), cy + r * (1 + rnd.uniform(-irregular, irregular)) * math.sin(2 * math.pi * k / n), 0)) for k in range(n)]
    return [(v.x, v.y) for v in catmull(ctrl, 3, closed=True)]


def abanico(pts, centro, w):
    bm = bmesh.new()
    c = bm.verts.new((centro[0], centro[1], w))
    vs = [bm.verts.new((x, y, w)) for x, y in pts]
    giro = area2(pts) < 0
    for i in range(len(vs)):
        a, b = vs[i], vs[(i + 1) % len(vs)]
        try:
            bm.faces.new((c, b, a) if giro else (c, a, b))
        except ValueError:
            pass
    return bm


def piedra(c, r, h, semilla, seg=6):
    rnd = random.Random(semilla)
    pts = [(c[0] + r * (1 + rnd.uniform(-0.25, 0.2)) * math.cos(2 * math.pi * k / seg + rnd.uniform(-0.2, 0.2)), c[1] + r * 0.8 * (1 + rnd.uniform(-0.25, 0.2)) * math.sin(2 * math.pi * k / seg)) for k in range(seg)]
    return prism(pts, h, None, z0=c[2] if len(c) > 2 else 0.0)


def roca(radios, loc, semilla, sub=2, jit=0.22):
    bm = blob(radios, loc, sub, jit, semilla)
    for v in bm.verts:
        if v.co.z < 0:
            v.co.z = 0.0
    return bm


def rol_roca(alto, musgo=False):
    def f(c, n):
        if n.z < -0.25 or c.z < alto * 0.12:
            return "drock"
        if musgo and n.z > 0.72 and c.z > alto * 0.72:
            return "leaf"
        return "rock"
    return f


def p_terreno():
    p = Prop("IslaTerreno", (520.371, 518.908, 8.089), 7000)

    def R(a):
        return 257 + 7 * math.sin(3 * a + 0.4) + 4 * math.sin(5 * a + 1.3) + 2.5 * math.sin(8 * a + 2.1)
    N = 120
    angs = [2 * math.pi * k / N for k in range(N)]
    bm = bmesh.new()
    centro = bm.verts.new((0.0, 0.0, 0.0))
    anillos = []
    for f in (0.3, 0.55, 0.78, 1.0):
        anillos.append([bm.verts.new(((R(a) - 22) * f * math.cos(a), (R(a) - 22) * f * math.sin(a), 0.0)) for a in angs])
    for t, z in ((0.12, -0.45), (0.3, -1.6), (0.55, -3.6), (0.8, -6.0), (1.0, -8.0)):
        anillos.append([bm.verts.new(((R(a) - 22 + 22 * t) * math.cos(a), (R(a) - 22 + 22 * t) * math.sin(a), z)) for a in angs])
    for j in range(N):
        bm.faces.new((centro, anillos[0][j], anillos[0][(j + 1) % N]))
    for a, b in zip(anillos, anillos[1:]):
        for j in range(N):
            j2 = (j + 1) % N
            bm.faces.new((a[j], b[j], b[j2], a[j2]))

    def rol(c, n):
        if c.z > -0.2:
            return "sand"
        if c.z > -1.2:
            return "wsand"
        if c.z > -4.0:
            return "sea"
        return "dsea"
    p.add(bm, rol, 30)
    rnd = random.Random(11)
    capa = [0.02]

    def w():
        capa[0] += 0.0016
        return capa[0]
    for k in range(7):
        a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(20, 140)
        cx, cy = r * math.cos(a), r * math.sin(a)
        tam = rnd.uniform(18, 34)
        p.add(abanico(mancha(cx, cy, tam, 100 + k, 9, 0.2), (cx, cy), w()), "lgrass")
        ix, iy = cx + rnd.uniform(-4, 4), cy + rnd.uniform(-4, 4)
        p.add(abanico(mancha(ix, iy, tam * 0.55, 200 + k, 9, 0.2), (ix, iy), w()), "leaf")
    for k in range(9):
        a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(150, 205)
        mx, my = r * math.cos(a), r * math.sin(a)
        p.add(abanico(mancha(mx, my, rnd.uniform(6, 11), 300 + k, 8, 0.25), (mx, my), w()), "dsand")
    for k in range(14):
        a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(185, 222)
        x, y = r * math.cos(a), r * math.sin(a)
        if k % 2 == 0:
            p.add(decal(estrella_pts(x, y, 1.4, 0.55, 5, rnd.uniform(0, 72)), None, w()), "orange" if k % 4 == 0 else "pink")
        else:
            g = rnd.uniform(0, 360)
            concha = [(x + 0.9 * math.cos(math.radians(g + 180 * i / 6)), y + 0.9 * math.sin(math.radians(g + 180 * i / 6))) for i in range(7)] + [(x, y)]
            p.add(decal(concha, None, w()), "cream")
    for k in range(6):
        a, r = rnd.uniform(0, 2 * math.pi), rnd.uniform(205, 224)
        mx, my = r * math.cos(a), r * math.sin(a)
        p.add(abanico(mancha(mx, my, rnd.uniform(1.5, 3), 400 + k, 7, 0.3), (mx, my), w()), "dleaf")
    return p


def palmera(nombre, tam, alto, semilla, frondas=8, budget=1600):
    p = Prop(nombre, tam, budget)
    rnd = random.Random(semilla)
    ctrl = [(0, 0, 0), (0.9, 0.2, alto * 0.3), (0.6, 0.1, alto * 0.62), (-0.2, 0.0, alto * 0.86), (-0.5, 0.0, alto)]
    p.add(tube(ctrl, lambda u: 0.62 - 0.28 * u, 8, 3, caps=False), lambda c, n: "dwood" if int(c.z / 1.1) % 2 else "trunk", 60)
    path = catmull([Vector(c) for c in ctrl], 6)
    for k in range(1, 6):
        q = path[int(len(path) * k / 6.5)]
        ring(p, (q.x, q.y, q.z), 0.66 - 0.28 * k / 6.5, 0.09, 8, "dwood", n=3)
    cima = Vector(ctrl[-1])
    p.add(ellipsoid((0.75, 0.75, 0.6), Matrix.Translation(cima), 8, 5), "dwood")
    for k in range(frondas):
        a = 2 * math.pi * k / frondas + rnd.uniform(-0.15, 0.15)
        largo = (12.0 if nombre == "Palmera1" else 10.0) * 0.54 * rnd.uniform(0.9, 1.0)
        sube = rnd.uniform(0.8, 1.8)
        spine = []
        anchos = []
        for i in range(11):
            t = i / 10
            r = largo * t
            z = cima.z + 0.3 + sube * t - (sube + 4.2) * t * t
            spine.append(Vector((cima.x + r * math.cos(a), cima.y + r * math.sin(a), z)))
            w = 1.35 * math.sin(math.pi * min(1.0, t * 1.08)) ** 0.7 + 0.05
            anchos.append(w * (1.0 if i % 2 == 0 else 0.62))
        p.add(hoja(spine, anchos, 0.4, 0.05), lambda c, n: "leaf" if n.z > 0 else "dleaf", 70)
        p.add(tube([spine[0], spine[4], spine[8]], lambda u: 0.07, 3, 1, caps=False), "dleaf")
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        p.add(ellipsoid((0.5, 0.5, 0.56), Matrix.Translation(cima + Vector((0.62 * math.cos(a), 0.62 * math.sin(a), -0.55))), 7, 5), "coco")
    return p


def p_roca_grande():
    p = Prop("RocaGrande", (14.408, 11.625, 9.411), 1200)
    p.add(roca((5.5, 5.2, 6.2), (0.8, 0.0, 2.2), 21, 3), rol_roca(9.0, True), 18)
    p.add(roca((3.2, 3.0, 3.6), (-3.6, 1.8, 0.8), 22, 2), rol_roca(9.0), 18)
    p.add(roca((2.2, 1.9, 2.1), (4.4, -3.6, 0.0), 23, 2), rol_roca(9.0), 18)
    return p


def p_roca_pequena():
    p = Prop("RocaPequena", (5.202, 4.322, 3.005), 400)
    p.add(roca((2.4, 1.9, 2.0), (0.0, 0.0, 0.6), 31, 3, 0.25), rol_roca(3.0), 18)
    return p


def p_arbusto():
    p = Prop("ArbustoTropical", (5.03, 5.055, 2.99), 600)
    rnd = random.Random(41)
    for k in range(7):
        a = 2 * math.pi * k / 7 + rnd.uniform(-0.2, 0.2)
        inclin = rnd.uniform(0.5, 0.9)
        largo = rnd.uniform(2.5, 2.95)
        spine, anchos = [], []
        for i in range(7):
            t = i / 6
            r = largo * t * math.cos(inclin * (1 - t * 0.7))
            z = 0.2 + largo * 1.7 * t * math.sin(inclin) - 1.0 * t * t
            spine.append(Vector((r * math.cos(a), r * math.sin(a), z)))
            anchos.append(0.75 * math.sin(math.pi * t) ** 0.8 + 0.04)
        p.add(hoja(spine, anchos, 0.25, 0.04), lambda c, n: "lgrass" if n.z > 0 else "dleaf", 70)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        c = Vector((1.0 * math.cos(a), 1.0 * math.sin(a), 2.2 + 0.3 * k))
        p.add(ellipsoid((0.32, 0.32, 0.26), Matrix.Translation(c), 6, 4), "red" if k != 1 else "orange")
        p.add(ellipsoid((0.12, 0.12, 0.12), Matrix.Translation(c + Vector((0, 0, 0.22))), 5, 3), "yellow")
    return p


def p_hoguera():
    p = Prop("Hoguera", (5.88, 5.845, 3.066), 1200)
    p.add(decal(circ(0, 0, 2.0, 16), None, 0.01), "black")
    p.add(decal(circ(0, 0, 1.3, 14), None, 0.02), "dwood")
    for k in range(11):
        a = 2 * math.pi * k / 11
        p.add(roca((0.48, 0.42, 0.42), (2.55 * math.cos(a), 2.55 * math.sin(a), 0.1), 50 + k, 1, 0.2), rol_roca(0.6), 18)
    apice = Vector((0, 0, 3.0))
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.25
        base = Vector((1.45 * math.cos(a), 1.45 * math.sin(a), 0.0))
        p.add(palo(base, base.lerp(apice, 0.98), 0.17, 6, 0.12), lambda c, n: "trunk" if int(c.z / 0.5) % 2 else "dwood", 40)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.9
        p0 = Vector((0.9 * math.cos(a), 0.9 * math.sin(a), 0.08))
        p1 = Vector((0.2 * math.cos(a + 1.2), 0.2 * math.sin(a + 1.2), 0.25))
        p.add(palo(p0, p1, 0.06, 4), "dwood")
    for k in range(3):
        a = 2 * math.pi * k / 3
        p.add(ellipsoid((0.3, 0.3, 0.12), Matrix.Translation((0.7 * math.cos(a), 0.7 * math.sin(a), 0.1)), 5, 3), "drock")
    return p


def p_tronco():
    p = Prop("Tronco", (4.016, 1.222, 1.271), 300)
    prof = [(0.0, -2.0), (0.42, -2.0), (0.6, -1.92), (0.6, 1.92), (0.42, 2.0), (0.0, 2.0)]
    bm = lathe(prof, 10, M((0, 0, 0.6), (0, 90, 0)))

    def rol(c, n):
        if abs(n.x) > 0.85:
            return "dsand" if math.hypot(c.y, c.z - 0.6) < 0.3 else "trunk"
        ang = math.atan2(c.z - 0.6, c.y)
        return "dwood" if int((ang + math.pi) / (2 * math.pi) * 10) % 2 else "trunk"
    p.add(bm, rol, 35)
    for x in (-2.004, 2.004):
        s = 1 if x > 0 else -1
        p.add(decal(circ(0, 0, 0.22, 10), frame((x, 0, 0.6), (0, s, 0), (0, 0, 1)), 0.004), "trunk")
    p.add(palo((0.6, 0.3, 0.95), (1.0, 0.55, 1.18), 0.11, 5), "dwood")
    return p


def p_coco():
    p = Prop("Coco", (1.141, 1.2, 1.34), 200)
    p.add(ellipsoid((0.6, 0.6, 0.65), Matrix.Translation((0, 0, 0.65)), 10, 8), lambda c, n: "dwood" if c.z > 1.15 else "coco", 50)
    for k in range(3):
        a = 2 * math.pi * k / 3
        p.add(ellipsoid((0.07, 0.07, 0.05), Matrix.Translation((0.12 * math.cos(a), 0.12 * math.sin(a), 1.29)), 5, 3), "black")
    return p


def p_cangrejo():
    p = Prop("Cangrejo", (2.414, 1.891, 1.238), 700)
    p.add(ellipsoid((0.82, 0.6, 0.36), Matrix.Translation((0, 0.12, 0.5)), 8, 6), lambda c, n: "orange" if n.z < -0.3 else "red", 40)
    for s in (-1, 1):
        base = Vector((0.26 * s, -0.25, 0.75))
        top = Vector((0.32 * s, -0.4, 1.05))
        p.add(palo(base, top, 0.05, 5), "red")
        p.add(ellipsoid((0.14, 0.14, 0.14), Matrix.Translation(top + Vector((0, 0, 0.04))), 6, 4), "white")
        p.add(ellipsoid((0.07, 0.05, 0.07), Matrix.Translation(top + Vector((0, -0.11, 0.05))), 5, 3), "black")
        hombro = Vector((0.62 * s, -0.25, 0.48))
        codo = Vector((0.92 * s, -0.55, 0.62))
        p.add(tube([hombro, codo, Vector((0.84 * s, -0.72, 0.66))], lambda u: 0.08, 5, 2, caps=False), "red")
        pinza = Vector((0.78 * s, -0.78, 0.66))
        p.add(ellipsoid((0.3, 0.2, 0.17), Matrix.Translation(pinza), 7, 5), "red")
        p.add(ellipsoid((0.2, 0.09, 0.09), Matrix.Translation(pinza + Vector((-0.12 * s, -0.17, 0.08))), 5, 3), "red")
        p.add(ellipsoid((0.17, 0.08, 0.07), Matrix.Translation(pinza + Vector((-0.12 * s, -0.16, -0.09))), 5, 3), "orange")
        for k in range(3):
            y = 0.05 + 0.3 * k
            a = Vector((0.68 * s, y, 0.42))
            b = Vector((1.05 * s, y + 0.12, 0.38))
            c2 = Vector((1.18 * s, y + 0.2, 0.0))
            p.add(tube([a, b, c2], lambda u: 0.05 - 0.02 * u, 4, 2, caps=False), "red")
    p.add(decal(pill(0, 0, 0.18, 0.04), frame((0, -0.495, 0.5), (1, 0, 0), (0, 0.45, 0.89)), 0.002), "black")
    return p


def p_antena():
    p = Prop("RadioAntena", (1.0, 1.02, 4.0), 500)
    p.add(bb(-0.5, 0.5, -0.5, 0.5, 0.0, 0.55, 0.08, 1), "red")
    p.add(bb(-0.32, 0.32, -0.52, -0.5, 0.15, 0.4), "yellow")
    p.add(cyl(0.16, 0.35, (0, 0, 0.55), seg=8), "black")
    p.add(cyl(0.07, 3.0, (0, 0, 0.9), seg=6, r2=0.05, cap0=False), "metal")
    for k, z in enumerate((1.5, 2.3, 3.05)):
        ring(p, (0, 0, z), 0.13 - 0.02 * k, 0.05, 8, "yellow", n=3)
    p.add(ellipsoid((0.2, 0.2, 0.2), Matrix.Translation((0, 0, 3.8)), 8, 6), "red")
    return p


def p_bateria():
    p = Prop("RadioBateria", (1.64, 1.047, 1.18), 500)
    p.add(bb(-0.8, 0.8, -0.5, 0.5, 0.0, 0.95, 0.08, 2), "orange")
    p.add(bb(-0.82, 0.82, -0.52, 0.52, 0.32, 0.5), "black")
    p.add(bb(-0.78, 0.78, -0.48, 0.48, 0.95, 1.0), "black")
    rayo = [(-0.12, 0.62), (0.16, 0.62), (0.0, 0.42), (0.18, 0.42), (-0.14, 0.08), (0.0, 0.32), (-0.18, 0.32)]
    p.add(decal(rayo, fr((0, -0.521, 0), "-y"), 0.006), "yellow")
    for x, c in ((-0.42, "red"), (0.42, "metal")):
        p.add(cyl(0.12, 0.18, (x, 0, 1.0), seg=8), c)
    p.add(decal(rect(-0.5, -0.34, 0.27, 0.33), None, 1.002), "white")
    p.add(decal(rect(-0.45, -0.39, 0.22, 0.38), None, 1.004), "white")
    p.add(decal(rect(0.34, 0.5, 0.27, 0.33), None, 1.002), "white")
    return p


def p_radio():
    p = Prop("RadioCaja", (2.0, 1.28, 1.36), 500)
    p.add(bb(-1.0, 1.0, -0.6, 0.6, 0.0, 1.0, 0.1, 2), "teal")
    cara = fr((0, -0.6, 0), "-y")
    p.add(decal(rrect(0, 0.5, 1.8, 0.82, 0.08, 1), cara, 0.006), "cream")
    for i in range(4):
        for j in range(4):
            p.add(decal(circ(-0.72 + 0.14 * i, 0.27 + 0.14 * j, 0.045, 6), cara, 0.012), "dwood")
    p.add(decal(circ(0.42, 0.56, 0.27, 14), cara, 0.012), "white")
    p.add(decal(circ(0.42, 0.56, 0.23, 14), cara, 0.016), "yellow")
    p.add(decal(rect(0.4, 0.44, 0.38, 0.74), cara, 0.02), "red")
    for x in (0.0, 0.18):
        p.add(cyl(0.07, 0.1, (x - 0.1, -0.58, 0.24), (90, 0, 0), seg=8), "black")
    for s in (-1, 1):
        p.add(bar((0.62 * s, 0, 1.0), (0.62 * s, 0, 1.3), 0.09, 0.12), "black")
    p.add(bar((-0.66, 0, 1.3), (0.66, 0, 1.3), 0.09, 0.12), "black")
    p.add(cyl(0.035, 0.36, (0.82, 0.38, 1.0), (0, 18, 0), seg=5), "metal")
    return p


def p_estacion():
    p = Prop("EstacionRadio", (6.059, 2.381, 3.75), 1200)
    for x in (-2.0, 2.0):
        p.add(bb(x - 0.9, x + 0.9, -0.9, 0.9, 0.0, 1.8, 0.06, 1), "trunk")
        for z in (0.6, 1.2):
            p.add(decal(rect(x - 0.86, x + 0.86, z - 0.03, z + 0.03), fr((0, -0.901, 0), "-y"), 0.004), "dwood")
        p.add(bar((x - 0.8, -0.905, 0.12), (x + 0.8, -0.905, 1.68), 0.12, 0.05), "dwood")
    p.add(bb(-3.0, 3.0, -1.15, 1.15, 1.8, 2.1, 0.05, 1), "dsand")
    for k in range(5):
        p.add(decal(rect(-3.0 + 1.2 * k + 0.04, -3.0 + 1.2 * k + 0.08, -1.1, 1.1), None, 2.102), "trunk")
    for x, c in ((-1.9, "red"), (0.0, "orange"), (1.9, "teal")):
        p.add(decal(rrect(x, -0.15, 1.5, 1.3, 0.16, 2), None, 2.106), c)
        p.add(decal(rrect(x, -0.15, 1.24, 1.04, 0.12, 2), None, 2.11), "dwood")
    p.add(cyl(0.07, 3.75, (-2.75, 0.95, 0.0), seg=6), "dwood")
    bandera = [(-2.72, 3.75), (-1.5, 3.55), (-1.65, 3.25), (-1.45, 2.95), (-2.72, 3.05)]
    for s in (1, -1):
        m = fr((0, 0.95 + 0.012 * s, 0), "-y" if s > 0 else "+y")
        pts = bandera if s > 0 else [(-x, y) for x, y in bandera]
        p.add(decal(pts, m, 0.0), "orange")
    p.add(decal([(-2.7, 3.55), (-1.95, 3.45), (-2.0, 3.3), (-2.7, 3.35)], fr((0, 0.957, 0), "-y"), 0.0), "teal")
    p.add(tube([(2.6, 1.2, 0.1), (3.0, 0.4, 0.1), (2.8, -0.3, 0.1), (2.3, 0.2, 0.1), (2.5, 0.9, 0.1)], lambda u: 0.06, 4, 3, caps=False), "black")
    return p


def p_bengala():
    p = Prop("Bengala", (0.4, 0.4, 1.6), 150)
    p.add(lathe([(0.0, 0.0), (0.17, 0.0), (0.17, 0.55), (0.17, 0.75), (0.17, 1.3)], 8), lambda c, n: "white" if 0.55 < c.z < 0.75 and abs(n.z) < 0.5 else "red", 40)
    p.add(cyl(0.2, 0.3, (0, 0, 1.3), seg=8), "black")
    p.add(cyl(0.09, 0.05, (0, 0, 1.55), seg=6), "yellow")
    return p


def p_hidroavion():
    p = Prop("Hidroavion", (40.0, 31.5, 11.8), 4500)
    rot_y = Matrix.Rotation(math.radians(90), 4, "X")
    fus = [(1.7, 0.0), (1.1, 2.0), (0.55, 6.0), (0.15, 11.0), (0.0, 15.0), (0.0, 22.0), (0.25, 26.0), (0.9, 28.6), (1.6, 30.0), (2.05, 30.6)]
    bm = rr_loft(4.6, 4.4, 1.6, 3, fus, Matrix.Translation((0, 15.5, 6.4)) @ rot_y)

    def rol_fus(c, n):
        if c.z < 5.3:
            return "teal"
        if 5.6 < c.z < 6.1:
            return "orange"
        if c.y < -11.5 and c.z > 7.0 and n.z > 0.2:
            return "glass"
        return "cream"
    p.add(bm, rol_fus, 50)
    for y in (-6.0, -2.0, 2.0, 6.0):
        for s in (-1, 1):
            p.add(decal(rrect(y, 6.9, 1.6, 1.0, 0.3, 2), fr((2.31 * s, 0, 0), "+x" if s > 0 else "-x"), 0.004), "glass")
    p.add(decal(rrect(-8.5, 6.3, 2.4, 3.4, 0.2, 2), fr((-2.31, 0, 0), "-x"), 0.006), "dteal")
    p.add(decal(rect(-7.65, -7.35, 6.1, 6.4), fr((-2.31, 0, 0), "-x"), 0.01), "yellow")
    ala = [(-20.0, -1.6), (20.0, -1.6), (19.4, 2.6), (-19.4, 2.6)]
    p.add(prism(ala, 0.6, Matrix.Translation((0, -3.0, 0)), 0.18, 1, 8.7), lambda c, n: "orange" if abs(c.x) > 16.5 else ("dteal" if n.z < -0.5 else "cream"), 40)
    for s in (-1, 1):
        p.add(bar((2.1 * s, -4.0, 5.0), (9.5 * s, -3.6, 8.7), 0.3, 0.18), "metal")
        mot = Vector((7.2 * s, -6.2, 8.4))
        p.add(lathe([(0.0, -2.9), (0.65, -2.6), (1.05, -1.6), (1.1, 1.6), (0.7, 3.4), (0.0, 3.6)], 10, Matrix.Translation(mot) @ rot_y), lambda c, n: "orange" if c.y < mot.y - 1.2 else "cream", 50)
        cubo = mot + Vector((0, -3.75, 0))
        p.add(ellipsoid((0.38, 0.5, 0.38), Matrix.Translation(cubo), 8, 5), "red")
        for k in range(3):
            a = math.radians(90 + 120 * k + 15 * s)
            punta = cubo + Vector((2.6 * math.cos(a), -0.12, 2.6 * math.sin(a)))
            p.add(bar(cubo, punta, 0.42, 0.08, up=(0, 1, 0)), "black")
        flot = [(0.7, 0.0), (0.2, 1.6), (0.0, 4.0), (0.0, 19.0), (0.25, 23.0), (0.55, 25.5), (0.7, 26.4)]
        p.add(rr_loft(1.9, 1.7, 0.7, 2, flot, Matrix.Translation((6.0 * s, 12.0, 0.85)) @ rot_y), lambda c, n: "orange" if n.z > 0.55 else ("dteal" if n.z < -0.55 else "cream"), 50)
        for y in (-6.0, 4.0):
            p.add(bar((6.0 * s, y, 1.6), (2.0 * s, y + 0.6, 4.4), 0.26, 0.16), "metal")
    p.add(prism([(12.6, 7.6), (16.4, 7.6), (16.0, 11.8), (14.6, 11.8)], 0.5, yzx((0, 0, 0)), 0.1, 1), lambda c, n: "teal" if c.z < 10.6 else "orange", 40)
    p.add(prism([(-6.0, 13.6), (6.0, 13.6), (5.6, 16.0), (-5.6, 16.0)], 0.35, None, 0.1, 1, 7.0), "cream")
    logo(p, frame((0.27, 15.0, 9.4), (0, 1, 0), (0, 0, 1)), 0.72, step=0.006)
    logo(p, frame((-0.27, 15.0, 9.4), (0, -1, 0), (0, 0, 1)), 0.72, step=0.006)
    return p


def p_restos_ala():
    p = Prop("RestosAla", (27.074, 9.6, 3.707), 1200)
    rot = Matrix.Rotation(math.radians(-4.5), 4, "Y")
    rnd = random.Random(61)
    plan = [(-12.8, 3.6), (12.4, 1.6), (13.0, 0.6), (13.0, -1.2), (12.6, -2.2), (-12.8, -3.6)]
    for k in range(1, 6):
        plan.append((-12.8 + rnd.uniform(-0.9, 0.6), -3.6 + 1.2 * k))
    bm = prism(plan, 0.9, rot @ Matrix.Translation((0, 0, 0)), 0.2, 1, 0.9)

    def rol(c, n):
        if n.x < -0.6 and c.x < -11.0:
            return "black"
        if n.z > 0.4:
            return "cream" if c.y > -2.6 else "orange"
        return "orange" if n.y < -0.6 else "cream"
    p.add(bm, rol, 30)
    for k in range(4):
        y = -3.0 + 1.9 * k
        p.add(bar((-13.6, y, 1.35 + 0.1 * k), (-11.6, y + 0.2, 1.4), 0.18, 0.14), "metal")
    for x in (-6.0, 0.0, 6.0):
        p.add(decal(rect(x - 0.06, x + 0.06, -2.3, 2.6), rot @ Matrix.Translation((0, 0, 1.81)), 0.004), "dteal")
    p.add(decal([(-12.2, -3.45), (12.5, -2.15), (12.7, -1.4), (-12.2, -2.5)], rot @ Matrix.Translation((0, 0, 1.81)), 0.006), "orange")
    p.add(decal([(-12.2, 2.5), (11.0, 1.55), (11.0, 1.25), (-12.2, 2.15)], rot @ Matrix.Translation((0, 0, 1.81)), 0.006), "dsand")
    p.add(ellipsoid((2.6, 4.8, 0.9), Matrix.Translation((-11.6, 0, 0.0)), 8, 4), lambda c, n: "dsand" if c.z < 0.4 else "sand", 40)
    return p


def p_restos_motor():
    p = Prop("RestosMotor", (5.706, 6.327, 5.699), 1200)
    eje = Matrix.Translation((0.2, 0.3, 1.8)) @ Matrix.Rotation(math.radians(-62), 4, "X") @ Matrix.Rotation(math.radians(20), 4, "Z")
    p.add(lathe([(1.9, -2.6), (2.25, -2.0), (2.3, 1.2), (1.7, 2.6), (0.9, 3.1)], 12, eje, cap0=False, cap1=False), lambda c, n: "orange" if c.z > 3.6 else "cream", 40)
    p.add(lathe([(0.0, -2.45), (1.85, -2.45)], 12, eje, cap0=False, cap1=False), "black")
    for k in range(6):
        a = 2 * math.pi * k / 6
        p.add(bar(eje @ Vector((0, 0, -2.4)), eje @ Vector((1.7 * math.cos(a), 1.7 * math.sin(a), -2.35)), 0.36, 0.08), "metal")
    p.add(ellipsoid((0.42, 0.42, 0.5), eje @ Matrix.Translation((0, 0, -2.5)), 8, 5), "metal")
    p.add(ellipsoid((3.0, 2.8, 1.2), Matrix.Translation((0, 0, 0.0)), 10, 4), lambda c, n: "dsand" if c.z < 0.35 else "sand", 40)
    p.add(decal([(-0.6, 0.4), (0.3, 0.9), (0.0, 0.2), (0.7, 0.0), (-0.2, -0.3)], eje @ frame((2.31, 0, 0), (0, 0, 1), (0, 1, 0)), 0.01), "black")
    return p


def p_cajon():
    p = Prop("Cajon", (3.477, 3.477, 3.0), 400)
    p.add(bb(-1.5, 1.5, -1.5, 1.5, 0.0, 3.0, 0.08, 1), "trunk")
    for side in ("-y", "+y", "+x", "-x"):
        o = {"-y": (0, -1.501, 0), "+y": (0, 1.501, 0), "+x": (1.501, 0, 0), "-x": (-1.501, 0, 0)}[side]
        m = fr(o, side)
        for z in (1.0, 2.0):
            p.add(decal(rect(-1.4, 1.4, z - 0.03, z + 0.03), m, 0.003), "dwood")
        p.add(decal([(-1.3, 0.2), (-1.0, 0.1), (1.3, 2.7), (1.0, 2.85)], m, 0.006), "dwood")
    p.add(tube([(-1.56, -1.56, 1.5), (0.0, -1.58, 1.58), (1.56, -1.56, 1.6), (1.58, 0.0, 1.52), (1.56, 1.56, 1.45), (0.0, 1.58, 1.5), (-1.56, 1.56, 1.55), (-1.58, 0.0, 1.5)], lambda u: 0.07, 4, 2, closed=True, caps=False), "dsand")
    return p


def p_sos():
    p = Prop("SenalSOS", (22.961, 8.852, 0.55), 1000)
    rnd = random.Random(71)

    def poner(pts):
        for i, (x, y) in enumerate(pts):
            p.add(piedra((x, y, 0.0), rnd.uniform(0.42, 0.58), rnd.uniform(0.35, 0.55), 80 + len(p.parts)), rol_roca(0.6) if i % 3 else (lambda c, n: "cream"), 20)

    def ese(cx):
        ctrl = [Vector((cx + 2.4, 3.4, 0)), Vector((cx, 4.1, 0)), Vector((cx - 2.3, 2.6, 0)), Vector((cx, 0.1, 0)), Vector((cx + 2.3, -2.2, 0)), Vector((cx, -4.0, 0)), Vector((cx - 2.5, -3.2, 0))]
        path = catmull(ctrl, 6)
        L = [0.0]
        for a, b in zip(path, path[1:]):
            L.append(L[-1] + (b - a).length)
        out = []
        for k in range(14):
            d = L[-1] * k / 13
            j = max(i for i in range(len(L)) if L[i] <= d + 1e-6)
            j = min(j, len(path) - 2)
            t = (d - L[j]) / max(L[j + 1] - L[j], 1e-6)
            q = path[j].lerp(path[j + 1], t)
            out.append((q.x, q.y))
        return out
    poner(ese(-8.6))
    poner([(2.6 * math.cos(2 * math.pi * k / 13), 4.0 * math.sin(2 * math.pi * k / 13)) for k in range(13)])
    poner(ese(8.6))
    return p


def p_muelle():
    p = Prop("Muelle", (7.79, 30.64, 3.3), 1500)
    rnd = random.Random(81)
    for k in range(15):
        y = -14.4 + k * 2.06
        z = 2.55 + rnd.uniform(-0.03, 0.03)
        p.add(bb(-3.8 + rnd.uniform(-0.1, 0.1), 3.8 + rnd.uniform(-0.1, 0.1), y - 0.9, y + 0.9, z, z + 0.25, 0.04, 1), "trunk" if k % 3 else "dsand")
    for s in (-1, 1):
        p.add(bb(3.0 * s - 0.25, 3.0 * s + 0.25, -15.0, 15.0, 2.05, 2.55), "dwood")
        for y in (-14.0, -7.0, 0.0, 7.0, 14.0):
            p.add(cyl(0.36, 3.0, (3.55 * s, y, 0.0), seg=7), lambda c, n: "dwood" if c.z < 1.2 else "trunk", 40)
            p.add(decal(circ(0, 0, 0.26, 7), Matrix.Translation((3.55 * s, y, 3.001)), 0.0), "dsand")
    p.add(tube([(-3.55, -14.0, 2.9), (-3.55, -7.0, 2.6), (-3.55, 0.0, 2.9), (-3.55, 7.0, 2.6), (-3.55, 14.0, 2.9)], lambda u: 0.07, 4, 4, caps=False), "dsand")
    p.add(cyl(0.3, 0.5, (2.2, 13.2, 2.8), seg=8), "black")
    p.add(cyl(0.42, 0.12, (2.2, 13.2, 3.18), seg=8), "black")
    return p


BUILDERS = [p_terreno, lambda: palmera("Palmera1", (12.36, 12.184, 21.907), 21.2, 91), lambda: palmera("Palmera2", (9.954, 10.287, 17.732), 17.0, 92, 7),
            p_roca_grande, p_roca_pequena, p_arbusto, p_hoguera, p_tronco, p_coco, p_cangrejo, p_antena, p_bateria, p_radio,
            p_estacion, p_bengala, p_hidroavion, p_restos_ala, p_restos_motor, p_cajon, p_sos, p_muelle]


def sheet_terreno(st):
    o = st.put("IslaTerreno", 0, 0)
    top = st.objs["IslaTerreno"].dimensions.z
    st.quad(-900, 900, -900, 900, top - 1.0, mat_rgb("2FB3C4", 0.15, alpha=0.55))
    st.quad(-900, 900, -900, 900, top - 9.0, mat_rgb("1F8A9E", 0.9))
    for nm, x, y, r in (() if arg("--solo-terreno") else (("Palmera1", -60, 40, 10), ("Palmera2", -48, 52, 60), ("Palmera1", 90, -70, 200), ("RocaGrande", 120, 80, 30), ("Muelle", 0, -232, 0), ("Hidroavion", 0, -262, 0), ("SenalSOS", -40, -60, 0), ("Hoguera", 40, 60, 0), ("EstacionRadio", 10, -20, 0), ("RestosAla", -90, -20, 25))):
        st.put(nm, x, y, r, top)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    fit_camera(st, pts, math.radians(42), math.radians(-18), 50)


SHEETS = [("isla_kit.png", lambda st: sheet_catalog(st, [["Coco", "Bengala", "RadioAntena", "RadioBateria", "RadioCaja", "Tronco", "Cangrejo", "RocaPequena", "ArbustoTropical"], ["Cajon", "Hoguera", "EstacionRadio", "RestosMotor", "SenalSOS"], ["Palmera2", "Palmera1", "RocaGrande", "RestosAla", "Muelle"]], 1.6)),
          ("isla_hidro.png", lambda st: sheet_catalog(st, [["Hidroavion"]], 2.0)),
          ("isla_terreno.png", sheet_terreno),
          ("isla_piezas.png", lambda st: sheet_catalog(st, [["Coco", "Bengala", "RadioAntena", "RadioBateria", "RadioCaja"], ["Tronco", "Cangrejo", "RocaPequena", "ArbustoTropical"], ["Cajon", "Hoguera", "EstacionRadio", "RestosMotor"]], 0.8))]


def render_sheets(objs, which, threads, outdir):
    scene = bpy.context.scene
    render_setup(scene, threads)
    for o in objs.values():
        o.hide_render = True
    for si, (fname, fn) in enumerate(SHEETS):
        if (which and str(si + 1) not in which) or False:
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
    if not arg("--no-export"):
        ruta = os.path.join(OUT, "manifest.json")
        if only and os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as fh:
                manifest = [e for e in json.load(fh) if e["nombre"] not in only] + manifest
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
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
