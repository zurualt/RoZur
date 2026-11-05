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
    ("hpink", "E8457A"), ("purple", "9B6BD6"), ("bleach", "DCD2BF"), ("lrock", "C4C8CC"),
    ("straw", "E8CC7E"), ("vdleaf", "2C6E3A"), ("foam", "E9FBFF"), ("lsea", "7FDCE0"),
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
    size = p.size or tuple(raw)
    sc = [size[i] / raw[i] for i in range(3)]
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


def ring_en(p, c, t, R, rt, seg, role, n=3):
    prof = [(R + rt * math.cos(2 * math.pi * k / n + math.pi / n), rt * math.sin(2 * math.pi * k / n + math.pi / n)) for k in range(n)]
    p.add(lathe(prof, seg, Matrix.Translation(Vector(c)) @ frame_from_normal(t), closed=True), role)


def fronda(cima, a, largo, ang0, ang1, ancho, n=11, rasgado=0.35, caida=0.55):
    spine, anchos = [], []
    pos = Vector(cima)
    ds = largo / (n - 1)
    for i in range(n):
        t = i / (n - 1)
        spine.append(pos.copy())
        e = math.radians(ang0 + (ang1 - ang0) * t ** 1.3)
        pos = pos + Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))) * ds
        w = ancho * math.sin(math.pi * min(1.0, 0.05 + t * 0.97)) ** 0.55 + 0.04
        anchos.append(w * (1.0 if i % 2 == 0 else rasgado))
    return hoja(spine, anchos, caida, 0.05)


def palma(nombre, troncos, semilla, largo, n_inf=8, n_sup=5, cocos=3, seca=True, budget=2000, grosor=(0.62, 0.34), nf=11):
    p = Prop(nombre, None, budget)
    rnd = random.Random(semilla)
    for ti, ctrl in enumerate(troncos):
        ctrl = [Vector(c) for c in ctrl]
        r0, r1 = grosor if ti == 0 else (grosor[0] * 0.75, grosor[1] * 0.8)
        p.add(tube(ctrl, lambda u, r0=r0, r1=r1: r1 + (r0 - r1) * (1 - u) ** 1.2 + 0.22 * r0 * max(0.0, 1 - u * 9) ** 2, 8, 3, caps=False),
              lambda c, n: "dwood" if int(c.z / 1.05) % 2 else "trunk", 60)
        path = catmull(ctrl, 8)
        for k in range(1, 5):
            i = int(len(path) * k / 5.4)
            tg = (path[min(i + 1, len(path) - 1)] - path[i - 1]).normalized()
            ring_en(p, path[i], tg, r1 + (r0 - r1) * (1 - k / 5.4) ** 1.2 + 0.03, 0.08, 6, "dwood")
        cima = ctrl[-1]
        esc = 1.0 if ti == 0 else 0.75
        L = largo * esc
        p.add(ellipsoid((r1 * 1.8, r1 * 1.8, r1 * 1.4), Matrix.Translation(cima), 7, 4), "dwood")
        capas = ((n_inf, L, 18, -72, 1.3, "leaf", 0.0), (n_sup, L * 0.82, 50, -40, 1.12, "lgrass", 0.5), (2, L * 0.45, 82, 60, 0.4, "lgrass", 0.25))
        for capa, (n, Lc, a0, a1, w, col, fase) in enumerate(capas):
            for k in range(n if ti == 0 or capa < 2 else 0):
                a = 2 * math.pi * (k + fase) / n + rnd.uniform(-0.2, 0.2)
                p.add(fronda(cima + Vector((0, 0, 0.12 * capa)), a, Lc * rnd.uniform(0.86, 1.06), a0 + rnd.uniform(-8, 8), a1 + rnd.uniform(-10, 10),
                             w * (0.85 + 0.15 * esc), nf if capa < 2 else 6),
                      lambda c, nn, col=col: col if nn.z > 0 else "dleaf", 70)
        if seca and ti == 0:
            a = rnd.uniform(0, 2 * math.pi)
            p.add(fronda(cima + Vector((0, 0, -0.3)), a, L * 0.5, -55, -86, 0.85, 8, 0.5, 0.3), lambda c, nn: "trunk" if nn.z > 0 else "dwood", 70)
        for k in range(cocos if ti == 0 else 0):
            a = 2 * math.pi * k / cocos + 0.4
            p.add(ellipsoid((0.46, 0.46, 0.5), Matrix.Translation(cima + Vector((0.62 * math.cos(a), 0.62 * math.sin(a), -0.62 - 0.1 * k))), 6, 4), "coco")
    return p


def p_palmera1():
    return palma("Palmera1", [[(0, 0, 0), (0.9, 0.2, 6.5), (0.6, 0.1, 13.2), (-0.2, 0.0, 18.4), (-0.5, 0.0, 21.0)]], 91, 7.6, 9, 6, 3)


def p_palmera2():
    return palma("Palmera2", [[(0, 0, 0), (-0.8, 0.5, 5.0), (-1.1, 0.4, 10.2), (-0.4, 0.1, 14.6), (0.4, -0.2, 17.0)]], 92, 6.8, 8, 5, 4, grosor=(0.56, 0.3))


def p_palmera3():
    return palma("Palmera3", [[(0, 0, 0), (1.4, 0.4, 8.0), (1.3, 0.3, 16.0), (-0.4, 0.0, 22.0), (-1.1, 0.0, 25.2)]], 93, 8.0, 9, 6, 5, grosor=(0.66, 0.34))


def p_palmera_inclinada():
    return palma("PalmeraInclinada", [[(0, 0, 0), (0, -2.0, 3.0), (0, -5.4, 7.2), (0, -8.2, 11.6), (0, -9.6, 15.2), (0, -10.0, 17.0)]], 94, 7.2, 9, 6, 3)


def p_palmera_joven():
    return palma("PalmeraJoven", [[(0, 0, 0), (0.3, 0.1, 2.8), (0.2, 0.0, 5.8), (0.0, 0.0, 7.0)], [(0.4, 0.3, 0), (1.5, 1.1, 2.2), (2.3, 1.6, 4.2)]],
                 95, 4.6, 6, 4, 0, False, 2000, (0.4, 0.26), 9)


def p_platanera():
    p = Prop("Platanera", None, 1100)
    rnd = random.Random(301)
    p.add(lathe([(0.0, 0.0), (0.55, 0.0), (0.5, 1.5), (0.38, 4.5), (0.3, 6.2), (0.22, 6.6), (0.0, 6.7)], 8), lambda c, n: "dleaf" if int(c.z / 0.9) % 2 else "lgrass", 40)
    p.add(lathe([(0.0, 0.0), (0.3, 0.0), (0.24, 1.6), (0.15, 2.6), (0.0, 2.7)], 6, Matrix.Translation((0.9, 0.5, 0))), "lgrass", 40)
    for k in range(8):
        a = 2 * math.pi * k / 8 + rnd.uniform(-0.2, 0.2)
        z0 = 5.8 + 0.12 * k
        L = rnd.uniform(3.6, 4.5)
        sube = rnd.uniform(2.0, 3.0)
        spine, anchos = [], []
        for i in range(11):
            t = i / 10
            r = 0.3 + L * t
            spine.append(Vector((r * math.cos(a), r * math.sin(a), z0 + sube * t - (sube + 1.4) * t * t)))
            w = 0.95 * math.sin(math.pi * min(1.0, 0.08 + t * 0.95)) ** 0.5
            anchos.append(0.05 if (i == 0 or (k % 2 == 0 and i in (4, 7)) or (k % 3 == 1 and i == 6)) else w)
        p.add(hoja(spine, anchos, 0.16, 0.04), lambda c, nn, col=("leaf" if k % 2 else "lgrass"): col if nn.z > 0 else "dleaf", 60)
        p.add(tube([spine[0], spine[5], spine[10]], lambda u: 0.05, 3, 1, caps=False), "dleaf")
    p.add(palo((0.25, 0.0, 5.9), (0.95, 0.25, 4.3), 0.07, 5), "dleaf")
    for k in range(9):
        a = 2 * math.pi * k / 3 + (k // 3) * 0.6
        c = Vector((0.75 + 0.06 * (k // 3), 0.2, 5.4 - 0.32 * (k // 3))) + Vector((0.22 * math.cos(a), 0.22 * math.sin(a), 0))
        p.add(ellipsoid((0.1, 0.1, 0.32), Matrix.Translation(c) @ Matrix.Rotation(0.5, 4, Vector((math.sin(a), -math.cos(a), 0))), 5, 3), "yellow" if k < 6 else "lgrass")
    p.add(ellipsoid((0.22, 0.22, 0.38), Matrix.Translation((1.0, 0.27, 4.1)), 6, 4), "purple")
    return p


def p_helecho():
    p = Prop("Helecho", None, 800)
    rnd = random.Random(311)
    for k in range(8):
        a = 2 * math.pi * k / 8 + rnd.uniform(-0.15, 0.15)
        alto = k % 3 == 0
        p.add(fronda(Vector((0.1 * math.cos(a), 0.1 * math.sin(a), 0.05)), a, rnd.uniform(2.6, 3.2) * (0.8 if alto else 1.0), 72 if alto else 58, -10 if alto else -42,
                     0.55, 9, 0.16, 0.3), lambda c, nn, col=("lgrass" if k % 3 == 0 else "leaf"): col if nn.z > 0 else "vdleaf", 70)
    for k in range(2):
        a = 2 * math.pi * k / 2 + 0.7
        pts = [(0.15 * math.cos(a), 0.15 * math.sin(a), 0.1), (0.3 * math.cos(a), 0.3 * math.sin(a), 0.8), (0.5 * math.cos(a), 0.5 * math.sin(a), 1.1),
               (0.66 * math.cos(a), 0.66 * math.sin(a), 0.95), (0.54 * math.cos(a), 0.54 * math.sin(a), 0.8)]
        p.add(tube(pts, lambda u: 0.07 - 0.02 * u, 4, 2, caps=False), "lgrass")
    return p


def p_hojas_grandes():
    p = Prop("HojasGrandes", None, 800)
    rnd = random.Random(321)
    for k in range(6):
        a = 2 * math.pi * k / 6 + rnd.uniform(-0.3, 0.3)
        alto = 1.4 + 0.42 * ((k * 3) % 6) + rnd.uniform(-0.2, 0.2)
        tope = Vector((0.9 * math.cos(a), 0.9 * math.sin(a), alto))
        p.add(palo((0.15 * math.cos(a), 0.15 * math.sin(a), 0.0), tope, 0.09, 5, 0.06), "dleaf")
        L = rnd.uniform(2.3, 2.9)
        spine, anchos = [], []
        for i in range(9):
            t = -0.2 + 1.2 * i / 8
            r = L * t
            spine.append(tope + Vector((r * math.cos(a), r * math.sin(a), 0.25 * t - 1.25 * max(t, 0) ** 2 - (0.25 if t < 0 else 0))))
            anchos.append(0.03 + 1.2 * (1 - max(t, 0)) ** 0.75 * min(1.0, (t + 0.2) * 2.6))
        col = ("leaf", "vdleaf", "lgrass")[k % 3]
        p.add(hoja(spine, anchos, 0.2, 0.04), lambda c, nn, col=col: col if nn.z > 0 else "dleaf", 70)
        p.add(tube([s + Vector((0, 0, 0.035)) for s in spine[2:8]], lambda u: 0.035, 3, 1, caps=False), "lgrass" if col != "lgrass" else "leaf")
    return p


def flor(centro, normal, r, nped=5, giro=0.0):
    bm = bmesh.new()
    nn = nped * 3
    for capa, dz in ((0, 0.0), (1, -0.04 * r)):
        c = bm.verts.new((0, 0, -0.28 * r + dz))
        anillo = []
        for j in range(nn):
            ang = giro + 2 * math.pi * j / nn
            lob = abs(math.cos(nped * ang / 2))
            rad = r * (0.5 + 0.5 * lob)
            anillo.append(bm.verts.new((rad * math.cos(ang), rad * math.sin(ang), 0.12 * r * lob + dz)))
        for j in range(nn):
            f = (c, anillo[j], anillo[(j + 1) % nn])
            bm.faces.new(f if capa == 0 else f[::-1])
    return xf(bm, Matrix.Translation(Vector(centro)) @ frame_from_normal(normal))


def p_flores():
    p = Prop("Flores", None, 1000)
    rnd = random.Random(331)
    for k in range(15):
        a = 2 * math.pi * k / 15 * 2.3
        el = rnd.uniform(0.2, 1.2)
        d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
        base = Vector((0, 0, 0.9)) + d * 0.5
        spine = [base + d * (1.1 * i / 4) + Vector((0, 0, -0.25 * (i / 4) ** 2)) for i in range(5)]
        p.add(hoja(spine, [0.04, 0.3, 0.36, 0.26, 0.02], 0.2, 0.03), lambda c, nn, col=("leaf" if k % 2 else "dleaf"): col if nn.z > 0 else "vdleaf", 70)
    p.add(ellipsoid((1.05, 1.05, 0.85), Matrix.Translation((0, 0, 0.85)), 7, 4), "dleaf")
    cols = ["hpink", "hpink", "red", "yellow", "hpink", "orange", "red"]
    for k in range(7):
        a = 2 * math.pi * k / 7 + rnd.uniform(-0.2, 0.2)
        el = rnd.uniform(0.35, 1.2)
        d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
        c = Vector((0, 0, 0.85)) + Vector((d.x * 1.15, d.y * 1.15, d.z * 0.95))
        p.add(flor(c, d, 0.42, 5, rnd.uniform(0, 1)), cols[k], 30)
        p.add(palo(c - d * 0.08, c + d * 0.32, 0.03, 4), "yellow")
    return p


def p_hierba():
    p = Prop("Hierba", None, 340)
    rnd = random.Random(341)
    for k in range(13):
        a = 2 * math.pi * k / 13 + rnd.uniform(-0.2, 0.2)
        inc = rnd.uniform(0.25, 0.85)
        L = rnd.uniform(0.9, 1.6)
        base = Vector((0.18 * math.cos(a), 0.18 * math.sin(a), 0.0))
        spine = [base + Vector((math.cos(a) * L * inc * t * t, math.sin(a) * L * inc * t * t, L * t)) for t in (0.0, 0.34, 0.68, 1.0)]
        col = "straw" if k % 4 == 0 else ("lgrass" if k % 2 else "leaf")
        p.add(hoja(spine, [0.1, 0.075, 0.045, 0.006], 0.05, 0.02), lambda c, nn, col=col: col, 70)
    return p


def p_madera_deriva():
    p = Prop("MaderaDeriva", None, 520)
    p.add(tube([(-4.2, 0.2, 0.55), (-1.5, -0.1, 0.62), (1.2, 0.15, 0.6), (4.0, -0.3, 0.42)], lambda u: 0.6 - 0.32 * u, 7, 3, caps=True, cap_rings=1),
          lambda c, n: "bleach" if n.z > -0.3 else "lrock", 40)
    for a0, a1, r in (((1.0, 0.1, 0.8), (2.5, 1.3, 1.25), 0.16), ((-1.0, 0.0, 0.9), (-1.9, -1.2, 1.5), 0.14), ((2.6, -0.2, 0.62), (3.4, -1.1, 0.95), 0.1)):
        p.add(palo(a0, a1, r, 5, r * 0.55), "bleach")
    for k in range(5):
        a = 2 * math.pi * k / 5
        p.add(tube([(-4.1, 0.2, 0.55), (-4.6, 0.2 + 0.5 * math.cos(a), 0.55 + 0.5 * math.sin(a)), (-4.9, 0.2 + 0.95 * math.cos(a), max(0.05, 0.55 + 0.9 * math.sin(a)))],
                   lambda u: 0.13 - 0.08 * u, 4, 2, caps=False), "bleach")
    for x in (-2.4, 0.4, 2.2):
        p.add(ellipsoid((0.16, 0.12, 0.05), Matrix.Translation((x, 0.0, 0.62 + 0.55 - 0.32 * (x + 4.2) / 8.2)), 5, 3), "trunk")
    return p


def p_conchas():
    p = Prop("Conchas", None, 450)
    rnd = random.Random(351)
    for (x, y, r0, r1, g, col) in ((-0.6, 0.4, 0.75, 0.3, 10, "orange"), (0.85, -0.5, 0.55, 0.22, 50, "hpink")):
        p.add(prism(estrella_pts(x, y, r0, r1, 5, g), 0.14, None, 0.05, 1, 0.0), lambda c, n, col=col: col if n.z > 0.3 else "red", 40)
        for k in range(5):
            a = math.radians(g + 72 * k)
            p.add(ellipsoid((0.05, 0.05, 0.03), Matrix.Translation((x + r0 * 0.5 * math.cos(a), y + r0 * 0.5 * math.sin(a), 0.15)), 4, 2), "cream")
    for (x, y, g, col) in ((0.6, 0.7, 30, "pink"), (-0.9, -0.6, 200, "cream")):
        bm = ellipsoid((0.45, 0.4, 0.16), Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(math.radians(g), 4, "Z"), 10, 3)
        p.add(bm, lambda c, n, x=x, y=y, col=col: col if int((math.atan2(c.y - y, c.x - x) + math.pi) * 2.2) % 2 else "white", 30)
    p.add(lathe([(0.0, 0.0), (0.22, 0.12), (0.2, 0.45), (0.12, 0.65), (0.0, 0.8)], 7, M((0.1, -0.1, 0.15), (85, 0, 40))), lambda c, n: "cream" if n.z > -0.2 else "hpink", 40)
    for k in range(4):
        p.add(blob((0.14, 0.11, 0.08), (rnd.uniform(-1.2, 1.2), rnd.uniform(-1.2, 1.2), 0.03), 1, 0.2, 360 + k), "lrock")
    return p


def p_charca():
    p = Prop("Charca", None, 1100)
    rnd = random.Random(361)
    agua = [(1.25 * x, y) for x, y in mancha(0, 0, 2.6, 361, 10, 0.18)]
    p.add(decal(agua, None, 0.5), "lsea")
    p.add(decal([(1.25 * x * 0.7, y * 0.7) for x, y in mancha(0, 0, 2.6, 361, 10, 0.18)], None, 0.505), "sea")
    for k in range(12):
        a = 2 * math.pi * k / 12 + rnd.uniform(-0.12, 0.12)
        R = 3.2 + rnd.uniform(-0.3, 0.3)
        r = rnd.uniform(0.7, 1.15)
        p.add(roca((r * 1.2, r, r * rnd.uniform(0.7, 1.0)), (1.25 * R * math.cos(a), R * math.sin(a), 0.0), 370 + k, 1, 0.2), rol_roca(1.0, k % 3 == 0), 18)
    p.add(decal(estrella_pts(0.8, 0.4, 0.5, 0.2, 5, 15), None, 0.52), "orange")
    p.add(decal(estrella_pts(-1.1, -0.5, 0.36, 0.14, 5, 50), None, 0.52), "purple")
    for k in range(3):
        a = 2 * math.pi * k / 3 + 1.0
        b = Vector((1.6 * math.cos(a), 1.2 * math.sin(a), 0.2))
        p.add(hoja([b, b + Vector((0.1, 0.05, 0.5)), b + Vector((-0.05, 0.1, 0.95))], [0.12, 0.1, 0.02], 0.0, 0.02), "vdleaf")
    return p


def p_roca_media():
    p = Prop("RocaMedia", None, 700)
    p.add(roca((3.0, 2.6, 3.2), (0.4, 0.0, 1.0), 381, 2, 0.24), rol_roca(4.5, True), 18)
    p.add(roca((1.7, 1.5, 1.7), (-2.4, 0.9, 0.2), 382, 1, 0.22), rol_roca(4.5), 18)
    p.add(roca((1.1, 1.0, 0.9), (2.7, -1.6, 0.0), 383, 1, 0.22), rol_roca(4.5), 18)
    return p


def rol_estratos(alto, musgo=True):
    def f(c, n):
        if n.z < -0.35 or c.z < 1.6:
            return "drock"
        if musgo and n.z > 0.62 and c.z > alto * 0.55:
            return "leaf"
        if n.z > 0.55:
            return "lrock"
        return "rock" if int(c.z / 2.6) % 2 else "drock"
    return f


def p_acantilado():
    p = Prop("Acantilado", None, 1500)
    for k, (r, loc, sub) in enumerate((((6.2, 5.0, 4.0), (0.0, 0.0, 1.4), 2), ((4.8, 4.0, 3.6), (0.6, 0.4, 5.8), 2), ((3.9, 3.4, 3.4), (-0.3, 0.2, 9.8), 2),
                                       ((3.0, 2.6, 2.0), (0.2, -0.1, 13.2), 2), ((2.4, 2.0, 1.8), (4.2, -2.4, 0.6), 1), ((1.6, 1.4, 1.3), (-4.6, 1.8, 0.3), 1))):
        p.add(roca(r, loc, 401 + k, sub, 0.3), rol_estratos(15.0), 12)
    rnd = random.Random(409)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        b = Vector((0.2 + 1.1 * math.cos(a), -0.1 + 1.0 * math.sin(a), 14.6))
        p.add(hoja([b, b + Vector((0.5 * math.cos(a), 0.5 * math.sin(a), 0.8)), b + Vector((1.1 * math.cos(a), 1.1 * math.sin(a), 0.9)), b + Vector((1.5 * math.cos(a), 1.5 * math.sin(a), 0.6))],
                   [0.15, 0.3, 0.26, 0.02], 0.2, 0.03), "lgrass" if k % 2 else "leaf")
    return p


def p_rocas_planas():
    p = Prop("RocasPlanas", None, 650)
    rnd = random.Random(391)
    for k, (x, y, rx, ry, h) in enumerate(((0, 0, 3.2, 2.4, 1.1), (-3.2, 1.6, 1.8, 1.4, 0.8), (3.3, -1.2, 1.6, 1.5, 0.7), (1.2, 2.6, 1.2, 1.0, 0.5), (-2.0, -2.4, 1.3, 1.0, 0.55))):
        p.add(roca((rx, ry, h), (x, y, 0.0), 391 + k, 1 if k else 2, 0.18), lambda c, n: "drock" if c.z < 0.25 else ("lrock" if n.z > 0.75 else "rock"), 25)
    for k in range(7):
        a = rnd.uniform(0, 2 * math.pi)
        p.add(ellipsoid((0.09, 0.09, 0.07), Matrix.Translation((2.0 * math.cos(a), 1.6 * math.sin(a), 0.95 - 0.1 * k)), 4, 2), "white")
    for k in range(3):
        b = Vector((rnd.uniform(-3, 3), rnd.uniform(-2.5, 2.5), 0.1))
        p.add(hoja([b, b + Vector((0.2, 0.0, 0.5)), b + Vector((0.4, 0.1, 0.8))], [0.15, 0.1, 0.02], 0.0, 0.02), "vdleaf")
    return p


def p_asiento_roto():
    p = Prop("AsientoRoto", None, 800)
    T = Matrix.Rotation(math.radians(-68), 4, "X") @ Matrix.Rotation(math.radians(14), 4, "Y")
    p.add(xf(bb(-1.15, 1.15, -1.0, 1.0, 1.0, 1.55, 0.18, 2), T), "teal")
    p.add(xf(bb(-1.15, 1.15, 0.85, 1.35, 1.4, 4.0, 0.18, 2), T), "teal")
    p.add(xf(bb(-0.95, 0.95, 0.8, 1.38, 3.45, 4.0, 0.12, 1), T), "orange")
    for s in (-1, 1):
        p.add(xf(bb(1.2 * s - 0.15, 1.2 * s + 0.15, -0.6, 0.9, 1.9, 2.15, 0.06, 1), T), "black")
        p.add(xf(bar((1.0 * s, -0.6, 1.0), (1.0 * s, -0.8, 0.0), 0.16, 0.16), T), "metal")
        p.add(xf(bar((1.0 * s, 0.7, 1.0), (1.0 * s, 0.9, 0.0), 0.16, 0.16), T), "metal")
        p.add(xf(bar((1.0 * s, -0.85, 0.08), (1.0 * s, 0.95, 0.08), 0.18, 0.12), T), "metal")
    p.add(xf(blob((0.55, 0.45, 0.3), (0.3, -0.2, 1.58), 1, 0.25, 395), T), "yellow")
    p.add(xf(decal(mancha(0.3, -0.2, 0.62, 396, 8, 0.3), None, 1.552), T), "dteal")
    p.add(xf(tube([(-0.6, -0.9, 1.5), (-0.7, -1.4, 0.9), (-0.4, -1.8, 0.2)], lambda u: 0.08, 4, 2, caps=False), T), "black")
    p.add(xf(bb(-0.55, -0.15, -1.95, -1.65, 0.0, 0.35, 0.04, 1), T), "metal")
    p.add(xf(tube([(0.1, 1.2, 3.2), (0.35, 0.6, 3.5), (0.6, 0.1, 3.3)], lambda u: 0.09, 5, 2, caps=False), T), "metal")
    return p


def p_maleta_abierta():
    p = Prop("MaletaAbierta", None, 800)
    p.add(bb(-1.6, 1.6, -1.1, 1.1, 0.0, 0.6, 0.14, 2), "teal")
    p.add(bb(-1.45, 1.45, -0.95, 0.95, 0.6, 0.62), "dteal")
    tapa = Matrix.Translation((0, 1.1, 0.6)) @ Matrix.Rotation(math.radians(165), 4, "X") @ Matrix.Translation((0, -1.1, -0.6))
    p.add(xf(bb(-1.6, 1.6, -1.1, 1.1, 0.6, 1.0, 0.14, 2), tapa), "teal")
    p.add(xf(bb(-1.45, 1.45, -0.95, 0.95, 0.58, 0.6), tapa), "dteal")
    for k, (x, col) in enumerate(((-0.8, "pink"), (0.15, "yellow"), (0.95, "white"))):
        p.add(bb(x - 0.45, x + 0.45, -0.75, 0.6, 0.6, 0.92 - 0.05 * k, 0.08, 1), col)
        p.add(decal(rect(x - 0.42, x + 0.42, -0.1, 0.0), None, 0.925 - 0.05 * k), "red" if col != "red" else "white")
    camisa = [(-0.5, -0.4), (0.3, -0.6), (0.9, -0.2), (1.4, -1.6), (0.6, -2.1), (-0.3, -1.8), (-0.6, -1.2)]
    p.add(prism(camisa, 0.06, M((0.1, -0.2, 0.66), (8, 0, 0))), "orange")
    for (x, y) in ((0.3, -1.2), (0.8, -1.6), (-0.1, -0.8), (0.9, -0.7)):
        p.add(decal(circ(x, y, 0.13, 6), M((0.1, -0.2, 0.66), (8, 0, 0)), 0.035), "yellow")
    pato = Vector((-0.9, -1.75, 0.0))
    p.add(ellipsoid((0.38, 0.3, 0.26), Matrix.Translation(pato + Vector((0, 0, 0.26))), 8, 5), "yellow")
    p.add(ellipsoid((0.2, 0.2, 0.2), Matrix.Translation(pato + Vector((0.22, 0, 0.62))), 7, 5), "yellow")
    p.add(ellipsoid((0.12, 0.07, 0.05), Matrix.Translation(pato + Vector((0.44, 0, 0.6))), 5, 3), "orange")
    for s in (-1, 1):
        p.add(ellipsoid((0.04, 0.04, 0.04), Matrix.Translation(pato + Vector((0.32, 0.12 * s, 0.7))), 4, 3), "black")
    p.add(bar((-0.5, -1.12, 0.3), (0.5, -1.12, 0.3), 0.14, 0.1), "black")
    return p


def p_maleta_cerrada():
    p = Prop("MaletaCerrada", None, 600)
    p.add(bb(-1.2, 1.2, -1.6, 1.6, 0.0, 1.05, 0.2, 2), "red")
    for x in (-0.6, 0.0, 0.6):
        p.add(decal(rect(x - 0.06, x + 0.06, -1.42, 1.42), None, 1.052), "orange")
    p.add(bb(-1.22, 1.22, -1.62, 1.62, 0.5, 0.56), "black")
    p.add(bar((-0.45, 1.62, 0.52), (0.45, 1.62, 0.52), 0.14, 0.12), "black")
    for s in (-1, 1):
        p.add(bar((0.45 * s, 1.6, 0.52), (0.45 * s, 1.75, 0.52), 0.12, 0.12), "black")
        p.add(cyl(0.16, 0.14, (0.85 * s, -1.65, 0.16), (90, 0, 0), seg=8), "black")
    logo(p, Matrix.Translation((0.35, 0.5, 1.06)), 0.42, step=0.004)
    p.add(decal(rrect(-0.6, -0.8, 0.7, 0.45, 0.08, 1), None, 1.056), "yellow")
    p.add(decal(rrect(-0.6, -0.8, 0.5, 0.12, 0.04, 1), None, 1.06), "teal")
    p.add(bb(0.3, 0.95, 1.75, 1.82, 0.0, 0.42, 0.02, 1), "orange")
    p.add(tube([(0.3, 1.66, 0.52), (0.45, 1.78, 0.44), (0.6, 1.8, 0.4)], lambda u: 0.02, 3, 1, caps=False), "white")
    return p


def p_trozo_fuselaje():
    p = Prop("TrozoFuselaje", None, 1400)
    rnd = random.Random(401)
    R, n_a, giro = 3.6, 14, 22.0
    a0, a1 = math.radians(-25 + giro), math.radians(205 + giro)

    def librea(c, n):
        phi = (math.degrees(math.atan2(c.z - 2.6, c.y)) - giro) % 360
        if 125 < phi < 138:
            return "orange"
        if 100 < phi <= 125:
            return "teal"
        return "cream"
    for capa, (rr, inv) in enumerate(((R, False), (R - 0.22, True))):
        bm = bmesh.new()
        rnd2 = random.Random(402)
        bordes = [(-4.2 + rnd2.uniform(-0.7, 0.7), 4.2 + rnd2.uniform(-0.7, 0.7)) for _ in range(n_a + 1)]
        vs = []
        for j in range(n_a + 1):
            a = a0 + (a1 - a0) * j / n_a
            x0, x1 = bordes[j]
            vs.append([bm.verts.new((x0 + (x1 - x0) * i / 4, rr * math.cos(a), rr * math.sin(a) + 2.6)) for i in range(5)])
        for j in range(n_a):
            for i in range(4):
                f = (vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i])
                bm.faces.new(f[::-1] if inv else f)
        p.add(bm, librea if capa == 0 else (lambda c, n: "dteal" if n.z < 0.3 else "black"), 25)
    for k in range(4):
        a = math.radians(152 + giro)
        p.add(decal(rrect(0, 0, 0.8, 1.05, 0.3, 2), frame((-2.6 + 1.75 * k, (R + 0.02) * math.cos(a), (R + 0.02) * math.sin(a) + 2.6), (1, 0, 0), (0, -math.sin(a), math.cos(a))), 0.0), "glass")
    for k in range(5):
        p.add(blob((rnd.uniform(0.6, 1.0), rnd.uniform(0.5, 0.8), 0.4), (rnd.uniform(-4, 4), rnd.uniform(-3.6, 3.6), 0.0), 1, 0.25, 410 + k), "dsand")
    return p


def p_caja_abierta():
    p = Prop("CajaAbierta", None, 800)
    W, D, H = 1.5, 1.25, 2.2
    p.add(bb(-W, W, -D, D, 0.0, 0.18), "dwood")
    for s in (-1, 1):
        p.add(bb(-W, W, s * D - 0.09, s * D + 0.09, 0.0, H, 0.03, 1), "trunk")
        p.add(bb(s * W - 0.09, s * W + 0.09, -D, D, 0.0, H, 0.03, 1), "trunk")
        for z in (0.7, 1.45):
            p.add(decal(rect(-W + 0.05, W - 0.05, z - 0.03, z + 0.03), fr((0, s * (D + 0.092), 0), "-y" if s < 0 else "+y"), 0.0), "dwood")
    for x in (-W, W):
        for y in (-D, D):
            p.add(bb(x - 0.13, x + 0.13, y - 0.13, y + 0.13, 0.0, H + 0.05), "dwood")
    p.add(ellipsoid((W * 0.98, D * 0.98, 0.5), Matrix.Translation((0, 0, 1.2)), 9, 4), "straw")
    rnd = random.Random(421)
    for k in range(7):
        a = rnd.uniform(0, 2 * math.pi)
        c = Vector((0.9 * W * math.cos(a), 0.9 * D * math.sin(a), 1.55))
        p.add(bar(c, c + Vector((0.5 * math.cos(a + 0.4), 0.5 * math.sin(a + 0.4), 0.35)), 0.05, 0.03), "straw")
    tapa = Matrix.Translation((W + 0.55, 0.0, 0.0)) @ Matrix.Rotation(math.radians(-20), 4, "Y")
    p.add(xf(bb(-0.09, 0.09, -D - 0.1, D + 0.1, 0.0, 2.9, 0.03, 1), tapa), "trunk")
    for z in (0.5, 1.45, 2.4):
        p.add(xf(bb(0.09, 0.16, -D, D, z - 0.12, z + 0.12), tapa), "dwood")
    for k in range(2):
        p.add(decal([(-0.2 + 0.5 * k, 0.7), (0.0 + 0.5 * k, 1.05), (0.2 + 0.5 * k, 0.7), (0.07 + 0.5 * k, 0.7), (0.07 + 0.5 * k, 0.35), (-0.07 + 0.5 * k, 0.35), (-0.07 + 0.5 * k, 0.7)],
                      fr((-0.5, -(D + 0.095), 0), "-y"), 0.0), "black")
    p.add(decal(rect(-1.25, -0.55, 1.6, 1.85), fr((0, -(D + 0.095), 0), "-y"), 0.0), "red")
    return p


def p_caja_bengala():
    p = Prop("CajaBengala", None, 700)
    W, D, H = 1.2, 0.8, 0.9
    p.add(rr_loft(2 * W, 2 * D, 0.2, 2, [(0.0, 0.0), (0.0, H)], None, True, False), "orange")
    p.add(decal(rrect(0, 0, 2 * W - 0.2, 2 * D - 0.2, 0.15, 2), None, H - 0.02), "black")
    p.add(decal(pill(0, 0, 1.5, 0.2), None, H - 0.015), "dwood")
    p.add(decal(rect(-W + 0.1, W - 0.1, -0.06, 0.06), fr((0, -D - 0.005, 0), "-y"), 0.3), "white")
    bisagra = Matrix.Translation((0, D, H)) @ Matrix.Rotation(math.radians(-105), 4, "X")
    p.add(xf(rr_loft(2 * W, 2 * D, 0.2, 2, [(0.0, 0.0), (0.0, 0.35)], Matrix.Translation((0, -D, 0))), bisagra), "orange")
    p.add(xf(xf(decal(rrect(0, D, 2 * W - 0.24, 2 * D - 0.24, 0.15, 2), None, 0.01), Matrix.Rotation(math.pi, 4, "X")), bisagra), "cream")
    cruz = [(-0.12, -0.42), (0.12, -0.42), (0.12, -0.12), (0.42, -0.12), (0.42, 0.12), (0.12, 0.12), (0.12, 0.42), (-0.12, 0.42), (-0.12, 0.12), (-0.42, 0.12), (-0.42, -0.12), (-0.12, -0.12)]
    p.add(xf(xf(decal([(x, y + D) for x, y in cruz], None, 0.02), Matrix.Rotation(math.pi, 4, "X")), bisagra), "red")
    for s in (-1, 1):
        p.add(bb(s * 0.7 - 0.12, s * 0.7 + 0.12, -D - 0.1, -D, 0.45, 0.75, 0.03, 1), "black")
    p.add(bar((-0.45, -D - 0.12, 0.55), (0.45, -D - 0.12, 0.55), 0.1, 0.1), "black")
    return p


def p_bote():
    p = Prop("Bote", None, 1500)
    rnd = random.Random(431)
    L, B, H = 5.4, 1.9, 1.5
    secciones = 9
    perfil = 7
    for capa, (esc, inv) in enumerate(((1.0, False), (0.9, True))):
        bm = bmesh.new()
        filas = []
        for i in range(secciones):
            t = -1 + 2 * i / (secciones - 1)
            ancho = B * (1 - abs(t) ** 2.4) ** 0.5 * esc + 0.05
            sube = 0.35 * t * t
            fila = []
            for j in range(perfil):
                u = -1 + 2 * j / (perfil - 1)
                ang = u * math.pi / 2
                fila.append(bm.verts.new((L * t, ancho * math.sin(ang), (H + sube) - (H * esc) * math.cos(ang) * (1 - 0.6 * abs(t) ** 3) + (1 - esc) * 0.5)))
            filas.append(fila)
        for i in range(secciones - 1):
            for j in range(perfil - 1):
                f = (filas[i][j], filas[i + 1][j], filas[i + 1][j + 1], filas[i][j + 1])
                bm.faces.new(f[::-1] if inv else f)
        if capa == 0:
            p.add(bm, lambda c, n: "teal" if c.z > H - 0.25 else ("red" if c.z < 0.35 else "white"), 35)
        else:
            p.add(bm, "trunk", 35)
    for x in (-1.8, 1.6):
        p.add(bb(x - 0.3, x + 0.3, -1.65, 1.65, 0.85, 1.0), "dwood")
    p.add(bb(-L - 0.05, L + 0.05, -0.08, 0.08, 1.25, 1.75), "dwood")
    agujero = [(x * 0.9, y * 0.6) for x, y in mancha(0, 0, 0.6, 433, 8, 0.4)]
    T = Matrix.Rotation(math.radians(24), 4, "X")
    p.parts = [(girar(bm, T), girado(rol, T), ang) for bm, rol, ang in p.parts]
    p.add(decal(agujero, frame((0.8, -1.75, 0.95), (1, 0, 0), (0, 0.42, 0.9)), 0.0), "black")
    remo = Matrix.Translation((0.5, -3.6, 0.12)) @ Matrix.Rotation(math.radians(18), 4, "Z")
    p.add(xf(cyl(0.08, 4.4, (-2.2, 0, 0), (0, 90, 0), seg=6), remo), "trunk")
    p.add(xf(bb(2.2, 3.4, -0.32, 0.32, -0.05, 0.05, 0.02, 1), remo), "orange")
    ring(p, (-3.0, 2.4, 0.22), 0.62, 0.2, 10, lambda c, n: "white" if int((math.atan2(c.y - 2.4, c.x + 3.0) + math.pi) / (math.pi / 2)) % 2 else "orange", (12, 0, 0), 4)
    return p


def girar(bm, T):
    bmesh.ops.transform(bm, matrix=T, verts=bm.verts)
    return bm


def girado(rol, T):
    if not callable(rol):
        return rol
    Ti = T.inverted()
    R = Ti.to_3x3()
    return lambda c, n: rol(Ti @ c, R @ n)


def p_cascada():
    p = Prop("Cascada", None, 1500)
    nx, ny = 12, 14
    rnd = random.Random(441)
    rayas = [rnd.random() for _ in range(nx)]
    for capa in (0, 1):
        bm = bmesh.new()
        filas = []
        for j in range(-2, ny + 1):
            t = max(j, 0) / ny
            z = 15.0 - 14.4 * t + (0.25 * math.sin(j * 1.7) if 0 < j < ny else 0.0) - (0.06 * j if j < 0 else 0.0)
            w = 3.6 * (1 - 0.16 * math.sin(math.pi * t)) + 0.8 * t * t
            fila = []
            for i in range(nx + 1):
                u = -1 + 2 * i / nx
                if j < 0:
                    y = 0.6 - 1.3 * j - 0.35 * (1 - u * u) * 0.4 + capa * 0.2
                else:
                    y = 0.6 - 8.8 * t + 0.7 * math.sin(math.pi * t) + 0.16 * math.sin(u * 9.0 + t * 4.0) - 0.35 * (1 - u * u) * (1 - t) + capa * 0.2
                fila.append(bm.verts.new((u * w, y, z - (0.0 if j < 0 else capa * 0.12))))
            filas.append(fila)
        for j in range(ny + 2):
            for i in range(nx):
                f = (filas[j][i], filas[j][i + 1], filas[j + 1][i + 1], filas[j + 1][i])
                bm.faces.new(f[::-1] if capa else f)

        def agua(c, n, w=4.4):
            i = min(nx - 1, max(0, int((c.x / w + 1) / 2 * nx)))
            if c.z < 1.8 or (c.z > 14.4 and c.y < 1.3):
                return "foam"
            r = rayas[i]
            if r > 0.78:
                return "foam"
            return "lsea" if r > 0.3 else "sea"
        p.add(bm, agua if capa == 0 else "sea", 40)
    for k in range(10):
        a = math.pi * (k / 9)
        c = Vector((4.3 * math.cos(a) * 0.95, -8.6 - 1.6 * math.sin(a), 0.45))
        p.add(ellipsoid((rnd.uniform(0.7, 1.1), rnd.uniform(0.6, 0.9), rnd.uniform(0.4, 0.65)), Matrix.Translation(c), 7, 4), "foam")
    p.add(arc_strip(0, -8.4, 3.6, 5.2, 180, 360, 14, None, 0.62), "foam")
    p.add(arc_strip(0, -8.4, 5.9, 6.5, 195, 345, 12, None, 0.61), "white")
    for k in range(5):
        c = Vector((rnd.uniform(-2.6, 2.6), -9.0 + rnd.uniform(-0.6, 0.6), 1.4 + rnd.uniform(0, 1.4)))
        p.add(ellipsoid((0.55, 0.55, 0.45), Matrix.Translation(c), 6, 4), "white")
    return p


def p_mirador():
    p = Prop("Mirador", None, 2400)
    S = 6.0
    p.add(bb(-S, S, -S, S, 1.0, 1.3, 0.04, 1), "trunk")
    for k in range(12):
        x = -S + 1.0 * k + 0.5
        p.add(decal(rect(x + 0.44, x + 0.5, -S + 0.05, S - 0.05), None, 1.302), "dwood")
    for x in (-S + 0.4, 0.0, S - 0.4):
        for y in (-S + 0.4, 0.0, S - 0.4):
            p.add(cyl(0.26, 1.0, (x, y, 0.0), seg=6), "dwood")
    for s in (-1, 1):
        p.add(bb(-S, S, s * S - 0.15, s * S + 0.15, 0.7, 1.0), "dwood")
        p.add(bb(s * S - 0.15, s * S + 0.15, -S, S, 0.7, 1.0), "dwood")
    postes = [(-S + 0.2, y) for y in (-S + 0.2, -2.0, 2.0, S - 0.2)] + [(S - 0.2, y) for y in (-S + 0.2, -2.0, 2.0, S - 0.2)] + [(x, S - 0.2) for x in (-2.0, 2.0)]
    for x, y in postes:
        p.add(bb(x - 0.13, x + 0.13, y - 0.13, y + 0.13, 1.3, 2.55, 0.03, 1), "trunk")
    for a, b in (((-S + 0.2, -S + 0.2), (-S + 0.2, S - 0.2)), ((S - 0.2, -S + 0.2), (S - 0.2, S - 0.2)), ((-S + 0.2, S - 0.2), (S - 0.2, S - 0.2))):
        p.add(bar((a[0], a[1], 2.5), (b[0], b[1], 2.5), 0.2, 0.14), "dsand")
        p.add(tube([(a[0], a[1], 1.95), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 1.75), (b[0], b[1], 1.95)], lambda u: 0.05, 4, 3, caps=False), "straw")
    for k in range(2):
        p.add(bb(-1.6, 1.6, -S - 0.9 * (k + 1), -S - 0.9 * k, 0.0, 0.85 - 0.42 * k, 0.03, 1), "trunk" if k else "dwood")
    p.add(cyl(0.11, 9.3, (4.0, S + 0.9, 0.0), seg=6), "dwood")
    p.add(ellipsoid((0.22, 0.22, 0.22), Matrix.Translation((4.0, S + 0.9, 9.35)), 6, 4), "yellow")
    for k in range(5):
        a = 2 * math.pi * k / 5
        p.add(roca((0.5, 0.45, 0.4), (4.0 + 0.6 * math.cos(a), S + 0.9 + 0.6 * math.sin(a), 0.0), 450 + k, 1, 0.2), rol_roca(0.6), 18)
    bandera = [(4.05, 9.0), (6.4, 8.7), (6.0, 8.2), (6.5, 7.6), (4.05, 7.5)]
    gallo = [(4.05, 8.75), (5.3, 8.55), (5.2, 8.3), (4.05, 8.35)]
    for s in (1, -1):
        m = fr((0, S + 0.9 - 0.012 * s, 0), "-y" if s > 0 else "+y")
        p.add(decal([(x * s, y) for x, y in bandera], m, 0.0), "orange")
        p.add(decal([(x * s, y) for x, y in gallo], m, 0.004), "teal")
    tri = Vector((-4.2, -4.0, 1.3))
    for k in range(3):
        a = 2 * math.pi * k / 3
        p.add(palo(tri + Vector((0.55 * math.cos(a), 0.55 * math.sin(a), 0.0)), tri + Vector((0, 0, 1.4)), 0.05, 4), "black")
    cuerpo = Matrix.Translation(tri + Vector((0, 0, 1.55))) @ Matrix.Rotation(math.radians(70), 4, "X") @ Matrix.Rotation(math.radians(-25), 4, "Y")
    p.add(xf(lathe([(0.0, -0.9), (0.14, -0.9), (0.14, 0.2), (0.2, 0.25), (0.2, 0.9), (0.0, 0.9)], 8), cuerpo), lambda c, n: "metal" if c.z < tri.z + 1.5 else "yellow", 40)
    ring(p, (S - 0.2, 0.0, 2.0), 0.5, 0.15, 10, lambda c, n: "white" if int((math.atan2(c.z - 2.0, c.y) + math.pi) / (math.pi / 2)) % 2 else "orange", (0, 90, 0), 4)
    return p


def p_cartel():
    p = Prop("Cartel", None, 900)
    p.add(bb(-0.15, 0.15, -0.15, 0.15, 0.0, 5.6, 0.03, 1), "trunk")
    p.add(ellipsoid((0.28, 0.28, 0.12), Matrix.Translation((0, 0, 5.62)), 6, 3), "dwood")
    tablas = ((4.8, 1, 8, "teal", "radio"), (3.95, -1, -12, "orange", "fuego"), (3.1, 1, -6, "cream", "avion"))
    for z, s, g, col, icono in tablas:
        T = Matrix.Translation((0, 0, z)) @ Matrix.Rotation(math.radians(g), 4, "Z")
        flecha = [(0.2 * s, -0.32), (2.2 * s, -0.32), (2.75 * s, 0.0), (2.2 * s, 0.32), (0.2 * s, 0.32)]
        p.add(xf(prism(flecha, 0.12, Matrix.Rotation(math.radians(90), 4, "X"), 0.03, 1), T), col)
        for lado in (-1, 1):
            m = T @ (fr((0, -0.065, 0), "-y") if lado < 0 else fr((0, 0.065, 0), "+y"))
            cx = 1.35 * s * (1 if lado < 0 else -1)
            if icono == "radio":
                p.add(xf(decal(rrect(cx, -0.04, 0.6, 0.36, 0.06, 1), None, 0.002), m), "cream")
                p.add(xf(decal(rect(cx + 0.12, cx + 0.16, 0.14, 0.3), None, 0.004), m), "cream")
                p.add(xf(decal(circ(cx - 0.12, -0.04, 0.09, 6), None, 0.004), m), "teal")
            elif icono == "fuego":
                llama = [(cx - 0.22, -0.2), (cx + 0.22, -0.2), (cx + 0.26, 0.02), (cx + 0.08, 0.28), (cx + 0.04, 0.06), (cx - 0.06, 0.24), (cx - 0.26, 0.02)]
                p.add(xf(decal(llama, None, 0.002), m), "yellow")
                p.add(xf(decal([(cx - 0.1, -0.16), (cx + 0.1, -0.16), (cx + 0.08, 0.02), (cx - 0.08, 0.02)], None, 0.004), m), "red")
            else:
                p.add(xf(decal(rect(cx - 0.32, cx + 0.32, -0.04, 0.04), None, 0.002), m), "teal")
                p.add(xf(decal(rect(cx - 0.05, cx + 0.05, -0.24, 0.24), None, 0.004), m), "teal")
                p.add(xf(decal(rect(cx - 0.3, cx - 0.22, -0.12, 0.12), None, 0.004), m), "teal")
    ave = Vector((0.0, 0.0, 5.9))
    p.add(ellipsoid((0.32, 0.22, 0.22), Matrix.Translation(ave), 7, 5), "white")
    p.add(ellipsoid((0.16, 0.16, 0.16), Matrix.Translation(ave + Vector((0.28, 0, 0.22))), 6, 4), "white")
    p.add(ellipsoid((0.12, 0.05, 0.04), Matrix.Translation(ave + Vector((0.48, 0, 0.2))), 5, 3), "orange")
    for s in (-1, 1):
        p.add(ellipsoid((0.25, 0.04, 0.12), Matrix.Translation(ave + Vector((-0.05, 0.2 * s, 0.05))), 5, 3), "metal")
        p.add(ellipsoid((0.03, 0.03, 0.03), Matrix.Translation(ave + Vector((0.38, 0.09 * s, 0.3))), 4, 2), "black")
    return p


def p_refugio():
    p = Prop("Refugio", None, 1900)
    rnd = random.Random(461)
    Lx, A, H = 4.2, 3.4, 4.6
    for x in (-Lx, Lx):
        for s in (-1, 1):
            p.add(palo((x, s * A, 0.0), (x, -0.25 * s, H + 0.4), 0.14, 5), "trunk")
    p.add(palo((-Lx - 0.6, 0, H), (Lx + 0.6, 0, H), 0.13, 5), "dwood")
    for s in (-1, 1):
        for fila in range(2):
            for k in range(6):
                x = -Lx + 0.2 + (2 * Lx - 0.4) * (k + 0.5 * fila) / 5.5
                arriba = Vector((x, -0.05 * s, H + 0.15 - fila * 1.9))
                abajo = Vector((x + rnd.uniform(-0.3, 0.3), s * A * (0.55 + 0.45 * fila) * 1.05, max(0.25, H - (fila + 1) * 2.3)))
                spine = [arriba.lerp(abajo, t) + Vector((0, 0, 0.35 * math.sin(math.pi * t))) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
                p.add(hoja(spine, [0.15, 0.75, 0.85, 0.65, 0.05], 0.15, 0.05), lambda c, nn, col=("leaf" if (k + fila) % 2 else "dleaf"): col, 60)
    manta = [(-2.9, 0.0), (-0.4, 0.0), (-0.3, 3.3), (-0.9, 4.4), (-2.0, 2.2)]
    p.add(prism(manta, 0.06, frame((-Lx - 0.15, 0, 0), (0, 1, 0), (0, 0, 1))), "orange")
    p.add(prism([(-2.75, 0.5), (-0.5, 0.5), (-0.5, 0.75), (-2.65, 0.75)], 0.08, frame((-Lx - 0.15, 0, 0), (0, 1, 0), (0, 0, 1))), "teal")
    p.add(bb(-2.5, -0.5, -0.9, 0.9, 0.0, 0.5, 0.15, 2), "teal")
    p.add(bb(-2.4, -0.6, 0.5, 0.95, 0.4, 1.6, 0.12, 1), "teal")
    p.add(ellipsoid((0.45, 0.45, 0.48), Matrix.Translation((0.6, 0.4, 0.48)), 7, 5), "coco")
    p.add(bb(1.2, 2.6, 0.2, 1.4, 0.0, 1.0, 0.05, 1), "trunk")
    p.add(cyl(0.5, 0.04, (1.9, 0.8, 1.0), seg=8), "cream")
    p.add(tube([(-Lx, -0.4, H - 0.6), (-Lx + 0.1, -0.6, H - 1.6)], lambda u: 0.03, 3, 1, caps=False), "straw")
    p.add(rr_loft(0.9, 0.35, 0.12, 1, [(0.0, 0.0), (0.0, 1.1)], Matrix.Translation((-Lx + 0.1, -0.6, H - 2.7))), "orange")
    return p


def p_pila_lena():
    p = Prop("PilaLena", None, 900)
    prof = [(0.0, -1.1), (0.3, -1.1), (0.42, -1.05), (0.42, 1.05), (0.3, 1.1), (0.0, 1.1)]
    filas = ((3, 0.42), (2, 1.18), (1, 1.94))
    for n, z in filas:
        for k in range(n):
            y = (k - (n - 1) / 2) * 0.86
            p.add(lathe(prof, 8, M((-0.6, y, z), (0, 90, 4 * (k - 1)))), lambda c, nn: "dsand" if abs(nn.x) > 0.85 else ("trunk" if int((math.atan2(c.z, c.y) + math.pi) * 1.6) % 2 else "dwood"), 35)
    p.add(lathe([(0.0, 0.0), (0.85, 0.0), (0.7, 0.15), (0.65, 0.95), (0.0, 0.95)], 9, Matrix.Translation((1.75, 0.2, 0.0))), lambda c, nn: "dsand" if nn.z > 0.8 else "dwood", 40)
    p.add(decal(circ(1.75, 0.2, 0.4, 9), None, 0.952), "trunk")
    hacha = Matrix.Translation((1.8, 0.2, 0.95)) @ Matrix.Rotation(math.radians(-28), 4, "Y")
    p.add(xf(bar((0, 0, 0.0), (0, 0, 1.7), 0.12, 0.12), hacha @ Matrix.Translation((0.25, 0, -0.2))), "trunk")
    p.add(xf(prism([(-0.05, -0.25), (0.55, -0.4), (0.6, 0.4), (-0.05, 0.25)], 0.1, Matrix.Rotation(math.radians(90), 4, "X")), hacha @ Matrix.Translation((-0.2, 0, -0.1))), lambda c, nn: "metal" if c.x < 1.95 else "lrock", 30)
    for k in range(4):
        p.add(bar((1.0 + 0.3 * k, -0.9 - 0.15 * k, 0.04), (1.3 + 0.3 * k, -0.6 - 0.1 * k, 0.08), 0.18, 0.06), "straw")
    return p


def p_arbusto():
    p = Prop("ArbustoTropical", None, 1000)
    rnd = random.Random(41)
    for k in range(20):
        a = 2 * math.pi * k / 20 * 3.1 + rnd.uniform(-0.2, 0.2)
        el = 0.15 + 1.1 * (k % 5) / 4.0
        d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
        base = Vector((0, 0, 0.7)) + d * 0.3
        L = rnd.uniform(1.6, 2.2)
        spine = [base + d * (L * i / 4) + Vector((0, 0, -0.55 * (i / 4) ** 2)) for i in range(5)]
        col = ("leaf", "dleaf", "lgrass", "vdleaf")[k % 4]
        p.add(hoja(spine, [0.05, 0.42, 0.5, 0.36, 0.03], 0.22, 0.03), lambda c, nn, col=col: col if nn.z > 0 else "vdleaf", 70)
    p.add(ellipsoid((1.4, 1.4, 0.9), Matrix.Translation((0, 0, 0.75)), 8, 4), "dleaf")
    cols = ["hpink", "yellow", "white", "hpink", "orange"]
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.4
        d = Vector((math.cos(a) * 0.8, math.sin(a) * 0.8, 0.75)).normalized()
        c = Vector((0, 0, 0.7)) + d * 1.75
        p.add(flor(c, d, 0.3, 5, rnd.uniform(0, 1)), cols[k], 30)
        p.add(ellipsoid((0.07, 0.07, 0.07), Matrix.Translation(c + d * 0.05), 4, 3), "yellow")
    return p


def p_restos_motor():
    p = Prop("RestosMotor", None, 1500)
    rnd = random.Random(141)
    T = Matrix.Translation((0, 0, 1.55)) @ Matrix.Rotation(math.radians(-80), 4, "X") @ Matrix.Rotation(math.radians(12), 4, "Y")
    seg, n = 14, 6
    for capa, (r, inv) in enumerate(((2.0, False), (1.82, True))):
        bm = bmesh.new()
        anillos = []
        for j in range(n):
            t = j / (n - 1)
            z = -2.2 + 4.4 * t
            rr = r * (1.0 - 0.18 * t * t)
            anillo = []
            for i in range(seg):
                a = 2 * math.pi * i / seg
                corte = rnd.uniform(-0.5, 0.2) if j == n - 1 and capa == 0 else 0.0
                anillo.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z + corte)))
            anillos.append(anillo)
        if capa == 1:
            for i in range(seg):
                anillos[-1][i].co.z = anillos[-1][i].co.z - 0.05
        for j in range(n - 1):
            for i in range(seg):
                f = (anillos[j][i], anillos[j][(i + 1) % seg], anillos[j + 1][(i + 1) % seg], anillos[j + 1][i])
                bm.faces.new(f[::-1] if inv else f)
        p.add(xf(bm, T), (lambda c, n2: "black" if c.z < 0.25 else ("orange" if int((c.x + 9) * 0.8) % 3 == 0 else "cream")) if capa == 0 else "black", 30)
    ring(p, (0, 0, 0), 2.08, 0.16, seg, "orange", (0, 0, 0), 4)
    p.parts[-1] = (xf(p.parts[-1][0], T @ Matrix.Translation((0, 0, -2.2))), p.parts[-1][1], p.parts[-1][2])
    cubo = T @ Matrix.Translation((0, 0, -1.7))
    p.add(xf(ellipsoid((0.45, 0.45, 0.6), Matrix(), 8, 5), cubo), "metal")
    for k in range(9):
        a = 2 * math.pi * k / 9
        p.add(xf(bar((0, 0, 0), (1.75 * math.cos(a), 1.75 * math.sin(a), 0.15), 0.42, 0.06, up=(0, 0, 1)), cubo @ Matrix.Rotation(math.radians(18), 4, Vector((math.cos(a), math.sin(a), 0)))), "metal" if k % 3 else "black")
    p.add(ellipsoid((3.1, 2.8, 0.9), Matrix.Translation((0.3, 0.6, 0.0)), 10, 4), lambda c, n2: "dsand" if c.z < 0.3 else "sand", 30)
    for k in range(4):
        a = rnd.uniform(0, 6.28)
        p.add(decal(mancha(0, 0, 0.55, 150 + k, 7, 0.35), Matrix.Translation((2.3 * math.cos(a), 2.0 * math.sin(a), 0.86)), 0.0), "black")
    for k in range(3):
        a0 = Vector((rnd.uniform(-1.5, 1.5), rnd.uniform(-2.5, -1.2), 0.3))
        p.add(bar(a0, a0 + Vector((rnd.uniform(-1, 1), rnd.uniform(-0.6, 0.6), 0.35)), 0.5, 0.05), "metal")
    return p


def p_palmera_gigante():
    p = palma("PalmeraGigante", [[(0, 0, 0), (2.4, 0.5, 9.0), (1.0, 0.2, 18.0), (-2.2, 0.0, 27.0), (-3.0, 0.0, 33.0), (-1.8, 0.0, 37.0)]], 96, 12.0,
              11, 8, 6, True, 3200, (1.35, 0.66), 12)
    rama0 = Vector((-1.2, 0.0, 24.5))
    rama1 = rama0 + Vector((-0.4, -3.4, 1.4))
    p.add(palo(rama0, rama1, 0.28, 6, 0.18), "trunk")
    p.add(tube([rama1 + Vector((0.25, 0, 0)), rama1 + Vector((0.3, -0.05, -5.0)), rama1 + Vector((0.3, 0.0, -10.2))], lambda u: 0.07, 4, 2, caps=False), "straw")
    p.add(tube([rama1 + Vector((-0.25, 0, 0)), rama1 + Vector((-0.3, 0.05, -5.0)), rama1 + Vector((-0.3, 0.0, -10.2))], lambda u: 0.07, 4, 2, caps=False), "straw")
    ring(p, rama1 + Vector((0, 0, -11.0)), 0.95, 0.38, 14, "black", (90, 0, 0), 6)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        p.add(ellipsoid((0.55, 0.55, 0.6), Matrix.Translation((2.0 * math.cos(a), 2.0 * math.sin(a), 0.5 + 0.35 * (k % 2))), 7, 4), "coco")
    tabla = Matrix.Translation((1.2, -1.0, 5.5)) @ Matrix.Rotation(math.radians(-8), 4, "Y")
    p.add(xf(bb(-0.9, 0.9, -0.08, 0.08, -0.45, 0.45, 0.03, 1), tabla), "trunk")
    p.add(xf(decal([(-0.6, -0.2), (0.3, -0.2), (0.3, -0.35), (0.7, 0.0), (0.3, 0.35), (0.3, 0.2), (-0.6, 0.2)], fr((0, -0.085, 0), "-y"), 0.0), tabla), "orange")
    return p


def p_tiki():
    p = Prop("Tiki", None, 2200)
    rnd = random.Random(151)
    p.add(lathe([(0.0, 0.0), (1.55, 0.0), (1.45, 0.6), (0.0, 0.6)], 10), "dwood")
    cabezas = ((0.6, 3.2, 1.3, "trunk", "teal"), (3.2, 5.7, 1.18, "dwood", "orange"), (5.7, 8.4, 1.32, "trunk", "yellow"))
    for k, (z0, z1, r, col, pint) in enumerate(cabezas):
        p.add(rr_loft(2 * r, 1.8 * r, 0.5 * r, 2, [(0.0, z0), (0.08, z0 + 0.1), (0.0, z0 + 0.3), (0.0, z1 - 0.3), (0.1, z1)], None, k == 0, True),
              lambda c, n, z0=z0, z1=z1, col=col, pint=pint: pint if (z0 + 0.12 < c.z < z0 + 0.42 and n.z < 0.5) else col, 30)
        cara = fr((0, -0.9 * r - 0.005, 0), "-y")
        ojo = 0.36 + 0.06 * k
        for s in (-1, 1):
            ex = s * 0.5 * r
            ez = z0 + (z1 - z0) * 0.68
            tam = ojo * (1.15 if (s > 0) == (k == 1) else 0.9)
            p.add(decal(circ(ex, ez, tam, 10), cara, 0.0), "white")
            p.add(decal(circ(ex + 0.06 * s, ez - 0.04, tam * 0.45, 8), cara, 0.008), "black")
            p.add(xf(bar((ex - 0.35, 0, ez + tam + 0.12), (ex + 0.35, 0, ez + tam + 0.12 + 0.12 * s * (1 if k != 2 else -1)), 0.14, 0.18), Matrix.Translation((0, -0.9 * r - 0.02, 0))), "black")
        bz = z0 + (z1 - z0) * 0.27
        if k == 1:
            p.add(decal(circ(0, bz, 0.42, 12), cara, 0.0), "black")
            p.add(decal(circ(0, bz - 0.06, 0.22, 10), cara, 0.008), "red")
        else:
            boca = rrect(0, bz, 1.25 * r, 0.55, 0.18, 2)
            p.add(decal(boca, cara, 0.0), "black")
            for i in range(5):
                x = -0.48 * r + 0.24 * r * i
                p.add(decal(rect(x - 0.08, x + 0.08, bz + 0.05, bz + 0.24), cara, 0.008), "white")
            p.add(decal(pill(0, bz - 0.12, 0.35, 0.09), cara, 0.009), "red")
        p.add(prism([(-0.2, 0.0), (0.2, 0.0), (0.0, 0.55)], 0.35, frame((0, -0.9 * r - 0.17, z0 + (z1 - z0) * 0.45), (1, 0, 0), (0, 0, 1))), col)
        if k == 1:
            for s in (-1, 1):
                p.add(tube([(s * r * 0.95, 0, z0 + 1.0), (s * (r + 0.6), -0.2, z0 + 0.8), (s * (r + 0.7), -0.6, z0 + 1.4)], lambda u: 0.22 - 0.06 * u, 6, 2), col)
    cima = Vector((0, 0, 8.4))
    cols = ["orange", "yellow", "teal", "lgrass", "red", "teal", "yellow", "orange", "lgrass"]
    for k in range(9):
        a = math.radians(-70 + 140 * k / 8)
        d = Vector((math.sin(a) * 0.8, 0.25, math.cos(a))).normalized()
        spine = [cima + Vector((0, 0.2, 0)) + d * (1.9 * i / 4) + Vector((0, 0.15 * (i / 4) ** 2, 0)) for i in range(5)]
        p.add(hoja(spine, [0.08, 0.32, 0.38, 0.28, 0.03], 0.1, 0.04), cols[k], 60)
    return p


def p_roca_cangrejo():
    p = Prop("RocaCangrejo", None, 1700)
    def rol(c, n):
        if c.z < 0.7 or n.z < -0.4:
            return "drock"
        if n.z > 0.75 and c.z > 3.6:
            return "leaf"
        return "lrock" if int(c.z / 1.6) % 2 else "rock"
    p.add(roca((6.2, 4.6, 3.6), (0.0, 0.8, 0.9), 161, 2, 0.16), rol, 14)
    for s in (-1, 1):
        hombro = Vector((s * 5.0, -2.2, 2.2))
        codo = Vector((s * 7.0, -4.6, 3.6))
        p.add(tube([hombro, codo, codo + Vector((-s * 0.6, -1.6, 1.4))], lambda u: 1.0 - 0.3 * u, 7, 2), rol, 20)
        pinza = codo + Vector((-s * 0.8, -2.4, 2.4))
        p.add(roca((1.9, 1.5, 1.4), (pinza.x, pinza.y, pinza.z + 0.4), 170 + s, 1, 0.18), rol, 18)
        p.add(roca((1.5, 0.9, 0.7), (pinza.x - s * 0.3, pinza.y - 1.6, pinza.z + 1.5), 172 + s, 1, 0.15), rol, 18)
        p.add(roca((1.3, 0.8, 0.6), (pinza.x - s * 0.3, pinza.y - 1.6, pinza.z - 0.1), 174 + s, 1, 0.15), rol, 18)
        tallo0 = Vector((s * 1.4, -3.0, 3.4))
        tallo1 = Vector((s * 1.8, -3.4, 5.4))
        p.add(palo(tallo0, tallo1, 0.45, 6, 0.38), "rock")
        p.add(ellipsoid((0.75, 0.75, 0.75), Matrix.Translation(tallo1 + Vector((0, 0, 0.4))), 8, 6), "white")
        p.add(ellipsoid((0.34, 0.2, 0.36), Matrix.Translation(tallo1 + Vector((-s * 0.12, -0.62, 0.42))), 6, 4), "black")
        for k in range(3):
            y = -0.6 + 1.8 * k
            a = Vector((s * 5.4, y, 1.4))
            b = Vector((s * 7.6, y + 0.4, 1.6))
            p.add(tube([a, b, Vector((s * 8.6, y + 0.6, 0.0))], lambda u: 0.55 - 0.25 * u, 5, 2), rol, 20)
    p.add(decal(pill(0, 0, 1.6, 0.22, 0.0), frame((0, -3.75, 1.9), (1, 0, 0), (0, 0.3, 0.95)), 0.0), "black")
    rnd = random.Random(165)
    for k in range(10):
        a = rnd.uniform(0, 2 * math.pi)
        p.add(ellipsoid((0.16, 0.16, 0.12), Matrix.Translation((5.4 * math.cos(a), 0.8 + 3.8 * math.sin(a), 2.6 + rnd.uniform(-0.4, 0.8))), 4, 2), "white")
    p.add(decal(estrella_pts(2.2, 1.2, 0.8, 0.32, 5, 20), Matrix.Translation((0, 0, 4.48)), 0.0), "orange")
    return p


def p_santuario():
    p = Prop("SantuarioBotellas", None, 2000)
    rnd = random.Random(181)
    for x in (-1.9, 1.9):
        p.add(tube([(x, 0, 0), (x + 0.1, 0.05, 1.4), (x - 0.05, 0, 2.9)], lambda u: 0.16 - 0.04 * u, 6, 2), "bleach")
    for z in (1.1, 2.2):
        p.add(bb(-2.3, 2.3, -0.32, 0.32, z - 0.08, z + 0.08, 0.03, 1), "bleach")
    p.add(tube([(-2.4, 0, 3.0), (0.0, 0.05, 3.5), (2.4, 0, 3.0)], lambda u: 0.13, 6, 3), "bleach")
    cols = ["glass", "lsea", "lgrass", "teal", "glass", "lgrass", "lsea", "glass"]

    def botella(m, col, rollo=True):
        p.add(xf(lathe([(0.0, 0.0), (0.2, 0.0), (0.22, 0.08), (0.22, 0.45), (0.1, 0.62), (0.08, 0.78), (0.0, 0.78)], 8), m), col, 40)
        p.add(xf(cyl(0.085, 0.14, (0, 0, 0.76), seg=6), m), "trunk")
        if rollo:
            p.add(xf(cyl(0.05, 0.3, (0.0, 0.0, 0.84), (0, 12, 0), seg=5), m), "cream")
    for k in range(4):
        botella(Matrix.Translation((-1.6 + 1.05 * k, 0.0, 1.18)), cols[k], k % 2 == 0)
        botella(Matrix.Translation((-1.5 + 1.0 * k, 0.05, 2.28)), cols[k + 4], k % 2 == 1)
    for k in range(4):
        a = rnd.uniform(0, 6.28)
        botella(Matrix.Translation((rnd.uniform(-2.2, 2.2), -1.0 - rnd.uniform(0, 0.8), 0.18)) @ Matrix.Rotation(math.radians(88), 4, Vector((math.cos(a), math.sin(a), 0))), cols[k + 2], True)
    p.add(xf(bb(-0.7, 0.7, -0.06, 0.06, -0.4, 0.4, 0.03, 1), Matrix.Translation((0, -0.38, 3.15)) @ Matrix.Rotation(math.radians(6), 4, "Y")), "trunk")
    p.add(xf(prism(estrella_pts(0, 0, 0.3, 0.13, 5, 90), 0.04, Matrix.Rotation(math.radians(90), 4, "X")), Matrix.Translation((0, -0.46, 3.15))), "yellow")
    for k in range(6):
        a = 2 * math.pi * k / 6
        x, y = 2.6 * math.cos(a), -0.4 + 1.3 * math.sin(a)
        p.add(ellipsoid((0.28, 0.24, 0.12), Matrix.Translation((x, y, 0.05)) @ Matrix.Rotation(a, 4, "Z"), 7, 3), lambda c, n, x=x, y=y: "pink" if int((math.atan2(c.y - y, c.x - x) + math.pi) * 2.2) % 2 else "cream", 30)
    return p


def p_gaviota():
    p = Prop("Gaviota", None, 420)
    p.add(ellipsoid((0.3, 0.52, 0.3), Matrix.Translation((0, 0.0, 0.62)) @ Matrix.Rotation(math.radians(-12), 4, "X"), 8, 5), "white")
    p.add(ellipsoid((0.22, 0.24, 0.22), Matrix.Translation((0, -0.42, 0.98)), 7, 5), "white")
    p.add(lathe([(0.0, 0.0), (0.075, 0.0), (0.0, 0.3)], 5, Matrix.Translation((0, -0.62, 0.94)) @ Matrix.Rotation(math.radians(95), 4, "X")), "yellow")
    p.add(ellipsoid((0.04, 0.03, 0.03), Matrix.Translation((0, -0.83, 0.92)), 4, 2), "red")
    for s in (-1, 1):
        p.add(ellipsoid((0.04, 0.03, 0.045), Matrix.Translation((s * 0.17, -0.55, 1.03)), 4, 3), "black")
        p.add(ellipsoid((0.09, 0.5, 0.2), Matrix.Translation((s * 0.27, 0.12, 0.7)) @ Matrix.Rotation(math.radians(-10), 4, "X"), 6, 4), lambda c, n: "black" if c.y > 0.45 else "lrock", 30)
        p.add(palo((s * 0.1, 0.0, 0.36), (s * 0.12, -0.02, 0.0), 0.03, 4), "orange")
        p.add(prism([(-0.09, 0.0), (0.09, 0.0), (0.0, -0.16)], 0.02, Matrix.Translation((s * 0.12, -0.04, 0.0))), "orange")
    p.add(prism([(-0.14, 0.0), (0.14, 0.0), (0.0, 0.32)], 0.06, Matrix.Translation((0, 0.46, 0.6)) @ Matrix.Rotation(math.radians(-20), 4, "X")), "lrock")
    return p


def p_pilote():
    p = Prop("Pilote", None, 160)
    p.add(cyl(0.36, 10.0, (0, 0, 0), seg=7, r2=0.33), lambda c, n: "vdleaf" if c.z < 7.8 else ("dwood" if int(c.z / 1.4) % 2 else "trunk"), 40)
    for z in (8.6, 7.9):
        ring(p, (0, 0, z), 0.37, 0.05, 7, "dsand", (0, 0, 0), 3)
    return p


def p_espuma():
    p = Prop("Espuma", None, 260)
    rnd = random.Random(191)
    n = 18
    bm = bmesh.new()
    ext, intr = [], []
    for i in range(n + 1):
        x = -6.0 + 12.0 * i / n
        w = 0.6 + 0.35 * abs(math.sin(i * 1.3)) + 0.15 * math.sin(i * 0.5)
        y0 = 0.25 * math.sin(i * 0.9)
        intr.append(bm.verts.new((x, y0 + 0.3, 0.0)))
        ext.append(bm.verts.new((x, y0 - w, 0.08)))
    for i in range(n):
        bm.faces.new((intr[i], ext[i], ext[i + 1], intr[i + 1]))
    p.add(bm, "foam", 10)
    for k in range(7):
        x = -5.2 + 10.4 * k / 6 + rnd.uniform(-0.4, 0.4)
        p.add(abanico(circ(x, -1.55 - rnd.uniform(0.0, 0.5), rnd.uniform(0.14, 0.32), 7), (x, -1.7), 0.08), "foam")
    return p


def p_hierba_playa():
    p = Prop("HierbaPlaya", None, 520)
    rnd = random.Random(201)
    for k in range(17):
        a = 2 * math.pi * k / 17 + rnd.uniform(-0.25, 0.25)
        inc = rnd.uniform(0.3, 0.95)
        L = rnd.uniform(1.4, 2.5)
        base = Vector((0.25 * math.cos(a), 0.25 * math.sin(a), 0.0))
        spine = [base + Vector((math.cos(a) * L * inc * t * t, math.sin(a) * L * inc * t * t, L * t * (1 - 0.15 * t))) for t in (0.0, 0.34, 0.68, 1.0)]
        col = ("straw", "wsand", "lgrass", "straw", "leaf")[k % 5]
        p.add(hoja(spine, [0.09, 0.07, 0.04, 0.005], 0.04, 0.02), lambda c, nn, col=col: col, 70)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        tallo = Vector((0.3 * math.cos(a), 0.3 * math.sin(a), 0.0))
        p.add(palo(tallo, tallo + Vector((0.2 * math.cos(a), 0.2 * math.sin(a), 2.3)), 0.025, 4), "wsand")
        p.add(ellipsoid((0.07, 0.07, 0.24), Matrix.Translation(tallo + Vector((0.22 * math.cos(a), 0.22 * math.sin(a), 2.45))), 5, 3), "dwood")
    return p


BUILDERS = [p_terreno, p_palmera1, p_palmera2, p_palmera3, p_palmera_inclinada, p_palmera_joven, p_platanera, p_helecho,
            p_hojas_grandes, p_flores, p_hierba, p_madera_deriva, p_conchas, p_charca, p_roca_media, p_acantilado, p_rocas_planas,
            p_asiento_roto, p_maleta_abierta, p_maleta_cerrada, p_trozo_fuselaje, p_caja_abierta, p_caja_bengala, p_bote, p_cascada,
            p_mirador, p_cartel, p_refugio, p_pila_lena, p_palmera_gigante, p_tiki, p_roca_cangrejo, p_santuario, p_gaviota,
            p_espuma, p_hierba_playa, p_pilote,
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
          ("isla_piezas.png", lambda st: sheet_catalog(st, [["Coco", "Bengala", "RadioAntena", "RadioBateria", "RadioCaja"], ["Tronco", "Cangrejo", "RocaPequena", "ArbustoTropical"], ["Cajon", "Hoguera", "EstacionRadio", "RestosMotor"]], 0.8)),
          ("isla_vegetacion.png", lambda st: sheet_catalog(st, [["Hierba", "Conchas", "Helecho", "Flores", "HojasGrandes", "Charca"], ["PalmeraJoven", "Platanera", "MaderaDeriva", "RocaMedia", "RocasPlanas"], ["Palmera2", "Palmera1", "Palmera3", "PalmeraInclinada", "Acantilado"]], 1.2)),
          ("isla_restos.png", lambda st: sheet_catalog(st, [["MaletaCerrada", "MaletaAbierta", "AsientoRoto", "CajaBengala", "CajaAbierta", "PilaLena"], ["Cartel", "Bote", "TrozoFuselaje", "Cascada"], ["Refugio", "Mirador"]], 1.2)),
          ("isla_heroes.png", lambda st: sheet_catalog(st, [["Gaviota", "HierbaPlaya", "ArbustoTropical", "Espuma", "SantuarioBotellas", "RestosMotor"], ["Tiki", "RocaCangrejo", "PalmeraGigante"]], 1.4)),
          ("isla_heroes_detalle.png", lambda st: sheet_catalog(st, [["Gaviota", "HierbaPlaya", "ArbustoTropical", "Espuma"], ["SantuarioBotellas", "RestosMotor", "Tiki"], ["RocaCangrejo"]], 0.8))]


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
