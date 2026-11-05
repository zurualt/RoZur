import bpy
import bmesh
import math
import os
import sys
import json
import mathutils
from mathutils import Vector, Matrix, Euler

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ARTE = os.path.dirname(OUT)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
FUENTE = "C:/Windows/Fonts/seguibl.ttf"


def arg(name, default=None):
    if name in ARGS:
        i = ARGS.index(name)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return default


PAL = [
    ("cream", "FFF4E0"), ("ink", "1B1B21"), ("orange", "F27B2B"), ("teal", "1FA6A0"),
    ("yellow", "F5CD3D"), ("red", "D9443A"), ("grey", "34383F"), ("white", "F7F7F2"),
    ("dgrey", "26292F"), ("mgrey", "4A4F57"), ("lgrey", "6E7580"), ("metal", "A9B0B8"),
    ("lmetal", "D3D8DE"), ("wall", "F3EBDD"), ("wall2", "D9D0C0"), ("ceil", "FAF6EE"),
    ("navy", "1D2938"), ("navy2", "2C3E55"), ("sky", "4AB8F0"), ("earth", "C9773A"),
    ("green", "6DBE45"), ("pink", "F27BB0"), ("panel", "3E4A5A"), ("panel2", "56657A"),
    ("dred", "A3302A"), ("dyellow", "D4A422"), ("dorange", "C4581B"), ("dteal", "13716D"),
    ("dsky", "2C88BF"), ("amber", "F2A33A"), ("paper", "FBF7EC"), ("coffee", "6B3A22"),
]
IDX = {n: i for i, (n, _) in enumerate(PAL)}

ZC = -57.25
YC = 100.0


def suv(n):
    i = IDX[n]
    return ((i % 8 + 0.5) / 8.0, (i // 8 + 0.5) / 4.0)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def M(loc=(0, 0, 0), rot=(0, 0, 0), scl=None):
    m = Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot], "XYZ").to_matrix().to_4x4()
    if scl is not None:
        m = m @ Matrix.Diagonal((scl[0], scl[1], scl[2], 1.0))
    return m


def T(m, u=0.0, v=0.0, w=0.0):
    return m @ Matrix.Translation((u, v, w))


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
    ey = ez.cross(ex).normalized()
    m = Matrix((ex, ey, ez)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


def yzx(loc=(0, 0, 0)):
    m = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    m.translation = Vector(loc)
    return m


def eje(p, d):
    d = Vector(d).normalized()
    x = Vector((0, 0, 1)).cross(d)
    if x.length < 1e-4:
        x = Vector((1, 0, 0))
    x.normalize()
    y = d.cross(x).normalized()
    m = Matrix((x, y, d)).transposed().to_4x4()
    m.translation = Vector(p)
    return m


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


def rrect(cx, cy, w, h, r, cs=2):
    return [(cx + x, cy + y) for x, y in rr_pts(w, h, r, cs)]


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


def stick(p0, p1, r0, r1=None, seg=8, cap0=False, cap1=True):
    p0, p1 = Vector(p0), Vector(p1)
    L = (p1 - p0).length
    return lathe([(r0, 0.0), (r1 if r1 is not None else r0, L)], seg, eje(p0, p1 - p0), cap0=cap0, cap1=cap1)


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


def yprism(pts, x0, x1, bev=0.0, bseg=1):
    return prism(pts, x1 - x0, yzx(((x0 + x1) / 2, 0, 0)), bev, bseg)


def plate(outer, holes=(), t=0.1, m=None, z0=0.0):
    if area2(outer) < 0:
        outer = outer[::-1]
    hs = [h[::-1] if area2(h) > 0 else list(h) for h in holes]
    loops = [list(outer)] + hs
    flat = [p for L in loops for p in L]
    bm = bmesh.new()
    lo = [[bm.verts.new((x, y, z0)) for x, y in L] for L in loops]
    hi = [[bm.verts.new((x, y, z0 + t)) for x, y in L] for L in loops]
    vlo = [v for L in lo for v in L]
    vhi = [v for L in hi for v in L]
    tris = mathutils.geometry.tessellate_polygon([[Vector((x, y, 0.0)) for x, y in L] for L in loops])
    for a, b, c in tris:
        p0, p1, p2 = flat[a], flat[b], flat[c]
        cr = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
        if cr < 0:
            b, c = c, b
        bm.faces.new((vhi[a], vhi[b], vhi[c]))
        bm.faces.new((vlo[a], vlo[c], vlo[b]))
    for L0, L1 in zip(lo, hi):
        n = len(L0)
        for j in range(n):
            j2 = (j + 1) % n
            bm.faces.new((L0[j], L0[j2], L1[j2], L1[j]))
    return xf(bm, m)


def sweep(path, prof, m=None, closed=False):
    P = [Vector((p[0], p[1])) for p in path]
    n = len(P)

    def sn(a, b):
        t = (b - a).normalized()
        return Vector((-t.y, t.x))
    bm = bmesh.new()
    rings = []
    for i in range(n):
        if closed:
            n1, n2 = sn(P[i - 1], P[i]), sn(P[i], P[(i + 1) % n])
        else:
            n1 = sn(P[i - 1], P[i]) if i > 0 else sn(P[0], P[1])
            n2 = sn(P[i], P[i + 1]) if i < n - 1 else n1
        nm = n1 + n2
        nm = nm.normalized() if nm.length > 1e-6 else n1
        s = 1.0 / max(nm.dot(n1), 0.35)
        rings.append([bm.verts.new((P[i].x + nm.x * o * s, P[i].y + nm.y * o * s, d)) for o, d in prof])
    k = len(prof)
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
    for i, j in pairs:
        for q in range(k - 1):
            bm.faces.new((rings[i][q], rings[j][q], rings[j][q + 1], rings[i][q + 1]))
    return xf(bm, m)


def rev(bm):
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return bm


def cw(pts):
    return list(pts) if area2(pts) < 0 else list(pts)[::-1]


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


def stroke(p0, p1, w):
    a, b = Vector(p0), Vector(p1)
    d = (b - a).normalized()
    nn = Vector((-d.y, d.x)) * (w / 2)
    return [tuple(a - nn), tuple(b - nn), tuple(b + nn), tuple(a + nn)]


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
    nrm = Vector(hint) - tangents[0] * Vector(hint).dot(tangents[0])
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


def fillet(pts, rads, n=3):
    out = []
    N = len(pts)
    for i in range(N):
        r = rads[i] if isinstance(rads, (list, tuple)) else rads
        p = Vector(pts[i])
        if r <= 0:
            out.append((p.x, p.y))
            continue
        a, b = Vector(pts[i - 1]), Vector(pts[(i + 1) % N])
        d1, d2 = (a - p).normalized(), (b - p).normalized()
        ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        t = min(r / math.tan(ang / 2), (a - p).length * 0.45, (b - p).length * 0.45)
        r = t * math.tan(ang / 2)
        p1, p2 = p + d1 * t, p + d2 * t
        c = p + (d1 + d2).normalized() * (r / math.sin(ang / 2))
        a1 = math.atan2(p1.y - c.y, p1.x - c.x)
        a2 = math.atan2(p2.y - c.y, p2.x - c.x)
        da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        for k in range(n + 1):
            aa = a1 + da * k / n
            out.append((c.x + r * math.cos(aa), c.y + r * math.sin(aa)))
    return out


def teardrop(cx, cy, r, tip, lean=0.0, n=8):
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in [150 + 240 * k / n for k in range(n + 1)]]
    pts.append((cx + lean, cy + tip))
    return pts


FONT = []


def text_bm(body, cap_h, maxw=None):
    if not FONT:
        FONT.append(bpy.data.fonts.load(FUENTE))
    cu = bpy.data.curves.new("t", "FONT")
    cu.body = body
    cu.font = FONT[0]
    cu.size = 1.0
    cu.resolution_u = 2
    ob = bpy.data.objects.new("t", cu)
    bpy.context.scene.collection.objects.link(ob)
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    s = cap_h / h
    sx = s if maxw is None or w * s <= maxw else maxw / w
    bmesh.ops.transform(bm, matrix=Matrix.Diagonal((sx, s, 1.0, 1.0)) @ Matrix.Translation((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, 0)), verts=bm.verts)
    for v in bm.verts:
        v.co.z = 0.0
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    return bm


def mirror_x(pts):
    return [(-x, y) for x, y in reversed(pts)]


class Prop:
    def __init__(self, name, budget):
        self.name = name
        self.budget = budget
        self.parts = []

    def add(self, bm, role, ang=50.0):
        self.parts.append((bm, role, ang))
        return bm


def finalize(p, centrar=True):
    prims = []
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for bm, role, ang in p.parts:
        bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
        ng = [f for f in bm.faces if len(f.verts) > 4]
        if ng:
            bmesh.ops.triangulate(bm, faces=ng, quad_method="BEAUTY", ngon_method="BEAUTY")
        dead = [f for f in bm.faces if f.calc_area() < 1e-9]
        if dead:
            bmesh.ops.delete(bm, geom=dead, context="FACES_ONLY")
        if bm.edges and all(len(e.link_faces) == 2 for e in bm.edges):
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()
        roles = [role(f.calc_center_median(), f.normal.copy()) if callable(role) else role for f in bm.faces]
        for v in bm.verts:
            for i in range(3):
                mn[i] = min(mn[i], v.co[i])
                mx[i] = max(mx[i], v.co[i])
        prims.append((bm, roles, ang))
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)) if centrar else Vector()
    Tm = Matrix.Translation(-off)
    verts, faces, uvs, nrms = [], [], [], []
    for bm, roles, ang in prims:
        bmesh.ops.transform(bm, matrix=Tm, verts=bm.verts)
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
    return verts, faces, uvs, nrms, tris, mn, mx, off


def palette_image():
    img = bpy.data.images.new("cabina_palette", 128, 64, alpha=True)
    px = [0.0] * (128 * 64 * 4)
    for i, (_, hx) in enumerate(PAL):
        r, g, b = hex_rgb(hx)
        gx, gy = i % 8, i // 8
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * 128 + x) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "cabina_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def palette_material(img):
    mat = bpy.data.materials.new("Cabina_Palette")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.55
    if arg("--caras"):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (1.0, 0.0, 1.0, 1.0)
        mix = nt.nodes.new("ShaderNodeMixShader")
        out = nt.nodes.get("Material Output")
        nt.links.new(geo.outputs["Backfacing"], mix.inputs["Fac"])
        nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
        nt.links.new(em.outputs["Emission"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def make_object(p, mat, centrar=True):
    verts, faces, uvs, nrms, tris, mn, mx, off = finalize(p, centrar)
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
    return ob, tris, mn, mx, off


def export_fbx(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.hide_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    assert [o.name for o in bpy.context.view_layer.objects if o.select_get()] == [ob.name]
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


def mundo(p):
    return (round(p[0], 4), round(YC + p[2], 4), round(ZC - p[1], 4))


# ---------------------------------------------------------------- dashboard

PERFIL_CUADRO = [(3.72, 0.0), (3.30, 1.10), (3.22, 1.26), (3.62, 2.72), (3.17, 2.72), (3.44, 3.80), (4.93, 3.66), (4.93, 0.0)]
RADIOS_CUADRO = [0.0, 0.06, 0.03, 0.02, 0.06, 0.12, 0.0, 0.0]
XW = 5.45
PF = frame((0, 3.22, 1.26), (1, 0, 0), (0, 0.40, 1.46))
PF_L = Vector((0.40, 1.46)).length
BF = frame((0, 3.17, 2.72), (1, 0, 0), (0, 0.27, 1.08))
BF_L = Vector((0.27, 1.08)).length
LF = frame((0, 3.72, 0.0), (1, 0, 0), (0, -0.42, 1.10))
EJE_X, EJE_Z = -2.6, 2.2
BOTONES = [("BotonExtintor", "FIRE EXT.", "red", "dred"), ("BotonAuto", "AUTOPILOT", "sky", "dsky"),
           ("BotonMotor", "ENGINES", "yellow", "dyellow"), ("BotonCinturon", "SEATBELTS", "orange", "dorange"),
           ("BotonRampa", "RAMP", "teal", "dteal")]
BOTON_U = [-2.3, -1.15, 0.0, 1.15, 2.3]
BOTON_V = 0.665
MCP_W = 0.02
TAPA_BASE = 0.16
TAPA_R, TAPA_H = 0.2, 0.2
CAJA_R, CAJA_H, POZO_R = 0.29, 0.2, 0.215


def panel_v(bz):
    return (bz - 1.26) / (1.46 / PF_L)


def bezel(p, m, u, v, w, h, r=0.07, t=0.045, borde=0.06, rol="ink"):
    outer = [(u + x, v + y) for x, y in rr_pts(w + 2 * borde, h + 2 * borde, r + borde * 0.6, 3)]
    inner = [(u + x, v + y) for x, y in rr_pts(w, h, r, 3)]
    p.add(plate(outer, [inner], t, m), rol)
    p.add(decal(inner, m, 0.006), "navy")


def brillo(p, m, u0, v1, s, w):
    p.add(decal(stroke((u0, v1 - 0.12 * s), (u0 + 0.12 * s, v1), 0.03 * s), m, w), "navy2")
    p.add(decal(stroke((u0, v1 - 0.26 * s), (u0 + 0.26 * s, v1), 0.05 * s), m, w), "navy2")


def pantalla_pfd(p, m, u, v):
    W, H = 0.95, 0.85
    bezel(p, m, u, v, W, H)
    hw, hh = W / 2 - 0.05, H / 2 - 0.05
    t = math.tan(math.radians(9))
    p.add(decal(rect(u - hw + 0.11, u + hw - 0.11, v - hh, v + hh), m, 0.010), "sky")
    ground = [(u - hw + 0.11, v - 0.03 - (hw - 0.11) * t), (u + hw - 0.11, v - 0.03 + (hw - 0.11) * t), (u + hw - 0.11, v - hh), (u - hw + 0.11, v - hh)]
    p.add(decal(ground, m, 0.014), "earth")
    p.add(decal(stroke(ground[0], ground[1], 0.018), m, 0.018), "white")
    for k in (-2, -1, 1, 2):
        d = 0.085 * k
        L = 0.07 if k % 2 else 0.13
        c = Vector((u, v - 0.03)) + Vector((-math.sin(math.radians(9)), math.cos(math.radians(9)))) * d
        e = Vector((math.cos(math.radians(9)), math.sin(math.radians(9)))) * L
        p.add(decal(stroke(c - e, c + e, 0.012), m, 0.018), "white")
    p.add(arc_strip(u, v - 0.03, 0.27, 0.29, 50, 130, 8, m, 0.018), "white")
    p.add(decal([(u, v + 0.24), (u - 0.025, v + 0.29), (u + 0.025, v + 0.29)], m, 0.018), "yellow")
    for s in (-1, 1):
        p.add(decal(rect(u + s * 0.03, u + s * 0.17, v - 0.045, v - 0.015), m, 0.020), "ink")
        p.add(decal(rect(u + s * 0.04, u + s * 0.16, v - 0.038, v - 0.022), m, 0.024), "yellow")
        x0, x1 = (u - hw, u - hw + 0.1) if s < 0 else (u + hw - 0.1, u + hw)
        p.add(decal(rect(x0, x1, v - hh, v + hh), m, 0.010), "navy2")
        for k in range(7):
            yy = v - hh + 0.06 + k * (2 * hh - 0.12) / 6
            xa = x1 - 0.035 if s < 0 else x0
            p.add(decal(rect(xa, xa + 0.035, yy - 0.006, yy + 0.006), m, 0.014), "white")
        yb = v - 0.03
        p.add(decal(rect(x0 - 0.01, x1 + 0.01, yb - 0.035, yb + 0.035), m, 0.016), "ink")
        p.add(decal(rect(x0 + 0.015, x1 - 0.015, yb - 0.012, yb + 0.012), m, 0.020), "green")
    p.add(decal(circ(u, v - 0.03, 0.018, 6), m, 0.024), "yellow")


def pantalla_nd(p, m, u, v, espejo=1):
    W, H = 0.95, 0.85
    bezel(p, m, u, v, W, H)
    hw, hh = W / 2 - 0.05, H / 2 - 0.05
    isla = [(0.18, 0.2), (0.3, 0.26), (0.38, 0.2), (0.36, 0.08), (0.28, 0.02), (0.2, 0.06), (0.14, 0.12)]
    isla2 = [(-0.36, -0.1), (-0.28, -0.05), (-0.22, -0.12), (-0.25, -0.2), (-0.34, -0.22)]
    for pts in (isla, isla2):
        p.add(decal([(u + espejo * x, v + y) for x, y in pts], m, 0.010), "dteal")
    cy = v - hh + 0.06
    p.add(arc_strip(u, cy, 0.56, 0.58, 42, 138, 14, m, 0.014), "white")
    p.add(arc_strip(u, cy, 0.3, 0.315, 30, 150, 10, m, 0.014), "navy2")
    for k in range(9):
        a = math.radians(48 + 84 * k / 8)
        c = Vector((u, cy)) + Vector((math.cos(a), math.sin(a))) * 0.56
        e = Vector((math.cos(a), math.sin(a))) * (-0.04 if k % 2 else -0.06)
        p.add(decal(stroke(c, c + e, 0.012), m, 0.016), "white")
    wp = Vector((u + espejo * 0.24, v + 0.14))
    fin = Vector((u + espejo * 0.05, v + hh - 0.05))
    for a, b, n in ((Vector((u, cy + 0.16)), wp, 5), (wp, fin, 4)):
        for k in range(1, n):
            q = a.lerp(b, k / n)
            p.add(decal(circ(q.x, q.y, 0.018, 6), m, 0.016), "pink")
    for q in (wp, fin):
        p.add(decal([(q.x, q.y + 0.04), (q.x + 0.04, q.y), (q.x, q.y - 0.04), (q.x - 0.04, q.y)], m, 0.020), "white")
    p.add(decal([(u, cy + 0.12), (u - 0.05, cy + 0.02), (u, cy + 0.04), (u + 0.05, cy + 0.02)], m, 0.020), "yellow")
    brillo(p, m, u - hw, v + hh, 1.0, 0.026)


def pantalla_motor(p, m, u, v):
    W, H = 1.7, 0.85
    bezel(p, m, u, v, W, H)
    for s in (-1, 1):
        cx, cy = u + s * 0.42, v + 0.1
        p.add(arc_strip(cx, cy, 0.17, 0.19, -40, 200, 14, m, 0.012), "white")
        p.add(arc_strip(cx, cy, 0.19, 0.215, 140, 200, 5, m, 0.014), "green")
        p.add(arc_strip(cx, cy, 0.19, 0.215, -10, 30, 3, m, 0.014), "amber")
        p.add(arc_strip(cx, cy, 0.19, 0.215, -40, -10, 3, m, 0.014), "red")
        a = math.radians(95 + s * 18)
        tip = (cx + 0.16 * math.cos(a), cy + 0.16 * math.sin(a))
        p.add(decal(stroke((cx, cy), tip, 0.022), m, 0.018), "yellow")
        p.add(decal(circ(cx, cy, 0.03, 8), m, 0.022), "white")
        p.add(decal(rrect(cx + 0.02, cy - 0.27, 0.24, 0.09, 0.02, 1), m, 0.012), "ink")
        for k in range(3):
            p.add(decal(rect(cx - 0.07 + 0.065 * k, cx - 0.03 + 0.065 * k, cy - 0.295, cy - 0.245), m, 0.016), "green")
    for k, (col, f) in enumerate((("sky", 0.8), ("sky", 0.75), ("green", 0.55), ("amber", 0.3))):
        x = u - 0.1 + 0.067 * k
        p.add(decal(rect(x - 0.022, x + 0.022, v - 0.33, v + 0.08), m, 0.012), "navy2")
        p.add(decal(rect(x - 0.016, x + 0.016, v - 0.325, v - 0.325 + 0.4 * f), m, 0.016), col)
    brillo(p, m, u - W / 2 + 0.05, v + H / 2 - 0.05, 1.2, 0.026)


def dial(p, m, u, v, r, ang, cara="cream"):
    mm = T(m, u, v, 0.0)
    p.add(lathe([(r + 0.04, 0.0), (r + 0.045, 0.03), (r + 0.02, 0.06), (r - 0.01, 0.05), (r - 0.01, 0.04)], 16, mm, cap0=False, cap1=False), "lmetal")
    p.add(lathe([(r - 0.005, 0.045), (0.0, 0.045)], 16, mm, cap0=False, cap1=False), cara)
    for k in range(9):
        a = math.radians(225 - 270 * k / 8)
        c = Vector((math.cos(a), math.sin(a)))
        L = 0.08 if k % 2 == 0 else 0.05
        p.add(decal(stroke(c * (r - 0.02), c * (r - 0.02 - L * r / 0.27), 0.022 * r / 0.27), mm, 0.049), "ink")
    p.add(arc_strip(0, 0, r * 0.55, r * 0.62, -45, 10, 4, mm, 0.051), "red")
    a = math.radians(ang)
    c = Vector((math.cos(a), math.sin(a)))
    nn = Vector((-c.y, c.x))
    p.add(decal([tuple(-c * r * 0.18 + nn * 0.02 * r / 0.27), tuple(-c * r * 0.18 - nn * 0.02 * r / 0.27), tuple(c * r * 0.82)], mm, 0.053), "red")
    p.add(cyl(0.035 * r / 0.27, 0.012, (0, 0, 0.05), seg=8, m=mm, cap0=False), "ink")


def toggle(p, m, u, v, lado=1.0, punta="white", base="mgrey", largo=0.15, k=1.0):
    mm = T(m, u, v, 0.0)
    p.add(cyl(0.05 * k, 0.035 * k, seg=6, m=mm, cap0=False), base)
    p.add(cyl(0.032 * k, 0.03 * k, (0, 0, 0.035 * k), seg=8, m=mm, cap0=False), "metal")
    a = math.radians(28) * lado
    d = Vector((0, math.sin(a), math.cos(a)))
    p0 = mm @ Vector((0, 0, 0.05 * k))
    p1 = mm @ (Vector((0, 0, 0.05 * k)) + d * largo * k)
    p.add(stick(p0, p1, 0.016 * k, 0.022 * k, 6), "metal")
    p.add(ellipsoid((0.034 * k, 0.034 * k, 0.034 * k), Matrix.Translation(p1), 8, 5), punta)


def perilla(p, m, u, v, r=0.08, col="ink", marca="white"):
    mm = T(m, u, v, 0.0)
    p.add(lathe([(r * 1.2, 0.0), (r * 1.2, 0.02), (r, 0.03), (r, 0.08), (r * 0.85, 0.1), (0.0, 0.1)], 10, mm, cap0=False), col)
    p.add(decal(rect(-0.012, 0.012, 0.0, r * 0.85), mm, 0.103), marca)


def lampara(p, m, u, v, w, h, col, t=0.04, brillo=True):
    p.add(rr_loft(w, h, 0.03, 2, [(0.0, 0.0), (0.0, t - 0.012), (0.012, t)], T(m, u, v, 0.0), cap0=False), col)
    if brillo:
        p.add(decal(stroke((u - w / 2 + 0.06, v + h / 2 - 0.05), (u - w / 2 + 0.16, v + h / 2 - 0.05), 0.025), m, t + 0.003), "white")


def luz_aviso(p, m, u, v, r, col):
    mm = T(m, u, v, 0.0)
    p.add(lathe([(r + 0.05, 0.0), (r + 0.05, 0.025), (r + 0.03, 0.05), (r, 0.045)], 16, mm, cap0=False, cap1=False), "lmetal")
    p.add(lathe([(r, 0.045), (r * 0.92, 0.08), (r * 0.65, 0.105), (0.0, 0.115)], 16, mm, cap0=False, cap1=False), col)
    p.add(ellipsoid((r * 0.22, r * 0.12, 0.02), mm @ Matrix.Translation((-r * 0.35, r * 0.4, 0.093)) @ Matrix.Rotation(math.radians(35), 4, "Z"), 8, 4), "white")


def pedal(p, u):
    a = math.radians(18)
    top = Vector((u, 3.36, 0.62))
    d = Vector((0, math.sin(a), -math.cos(a)))
    mm = frame(top, (1, 0, 0), -d)
    p.add(rbox((0.28, 0.46, 0.05), (0, -0.23, 0.0), 0.02, 1, m=mm), "metal")
    for k in range(3):
        p.add(rbox((0.22, 0.04, 0.012), (0, -0.1 - 0.12 * k, 0.031), 0.0, m=mm), "ink")
    p.add(bar((u, 3.36, 0.62), (u, 3.6, 0.62), 0.07, 0.07, 0.02), "mgrey")


def caja_boton(p, m, u, v, peligro=False):
    mm = T(m, u, v, MCP_W)
    inv = mm.inverted()

    def rol(c, n):
        if not peligro:
            return "lmetal"
        l = inv @ c
        if l.z > CAJA_H - 0.03 or math.hypot(l.x, l.y) < CAJA_R - 0.01:
            return "lmetal"
        return "yellow" if int((math.degrees(math.atan2(l.y, l.x)) + 720.0) // 20) % 2 == 0 else "ink"
    p.add(lathe([(CAJA_R, 0.0), (CAJA_R, CAJA_H - 0.04), (CAJA_R - 0.02, CAJA_H - 0.005), (CAJA_R - 0.045, CAJA_H), (POZO_R + 0.012, CAJA_H),
                 (POZO_R, CAJA_H - 0.012), (POZO_R, 0.012)], 36, mm, cap0=False, cap1=False), rol)
    p.add(lathe([(POZO_R, 0.012), (0.0, 0.012)], 24, mm, cap0=False, cap1=False), "ink")


def pato(p, base):
    x, y, z = base
    p.add(ellipsoid((0.17, 0.22, 0.13), Matrix.Translation((x, y, z + 0.12)), 12, 8), "yellow")
    p.add(ellipsoid((0.08, 0.06, 0.06), Matrix.Translation((x, y + 0.2, z + 0.2)) @ Matrix.Rotation(math.radians(-35), 4, "X"), 8, 6), "yellow")
    p.add(ellipsoid((0.12, 0.12, 0.12), Matrix.Translation((x, y - 0.1, z + 0.32)), 12, 8), "yellow")
    p.add(ellipsoid((0.07, 0.07, 0.03), Matrix.Translation((x, y - 0.22, z + 0.3)), 8, 6), "orange")
    for s in (-1, 1):
        p.add(ellipsoid((0.025, 0.02, 0.03), Matrix.Translation((x + s * 0.055, y - 0.205, z + 0.36)), 6, 4), "ink")
        p.add(ellipsoid((0.04, 0.1, 0.07), Matrix.Translation((x + s * 0.15, y + 0.02, z + 0.15)) @ Matrix.Rotation(math.radians(s * 10), 4, "Y"), 8, 6), "dyellow")


def p_cuadro():
    p = Prop("CabinaCuadro", 16000)
    prof = fillet(PERFIL_CUADRO, RADIOS_CUADRO, 3)
    body = yprism(prof, -XW, XW)
    bevel_sharp(body, 0.035, 1, 60)

    def rol_cuerpo(c, n):
        if abs(n.x) > 0.7:
            return "grey"
        if c.z > 3.6 and n.z > 0.5:
            return "dgrey"
        if 2.7 < c.z and c.y < 3.6:
            return "dgrey"
        if c.z < 1.2 and n.y < -0.3:
            return "mgrey"
        return "grey"
    p.add(body, rol_cuerpo, 40)
    p.add(decal(rect(-XW + 0.05, XW - 0.05, 0.92, 0.98), LF, 0.004), "teal")
    for s in (-1, 1):
        p.add(decal(rect(s * 0.9 if s > 0 else -XW + 0.1, XW - 0.1 if s > 0 else -0.9, 0.22, 0.26), LF, 0.004), "ink")
        for x in (s * 2.28, s * 2.92):
            pedal(p, x)

    for s in (-1, 1):
        pantalla_pfd(p, PF, s * 3.6, 0.86)
        pantalla_nd(p, PF, s * 1.6, 0.86, s)
        dial(p, PF, s * 4.75, 1.13, 0.25, 140 - s * 30)
        dial(p, PF, s * 4.75, 0.5, 0.25, 80 + s * 40)
        for k, uu in enumerate((s * 2.43, s * 2.77)):
            p.add(rbox((0.14, 0.2, 0.012), (uu, 0.48, 0.006), 0.0, m=PF), "mgrey")
            toggle(p, PF, uu, 0.48, 1.0 if k == 0 else -1.0, "cream" if k == 0 else "orange", "ink", 0.12)
    pantalla_motor(p, PF, 0.0, 0.97)
    for k, col in enumerate(("green", "amber", "sky")):
        p.add(decal(circ(-0.3 + 0.3 * k, 0.36, 0.045, 10), PF, 0.005), "ink")
        p.add(decal(circ(-0.3 + 0.3 * k, 0.36, 0.032, 10), PF, 0.009), col)

    v_eje = panel_v(EJE_Z)
    mm = T(PF, EJE_X, v_eje, 0.0)
    p.add(lathe([(0.24, 0.0), (0.24, 0.025), (0.21, 0.045), (0.18, 0.045)], 20, mm, cap0=False, cap1=False), "lmetal")
    p.add(lathe([(0.18, 0.045), (0.0, 0.045)], 20, mm, cap0=False, cap1=False), "ink")
    yb = 3.22 + v_eje * (0.40 / PF_L)
    fuelle = [(0.19, 0.0), (0.16, 0.05), (0.19, 0.1), (0.15, 0.15), (0.17, 0.2), (0.13, 0.25), (0.135, 0.28), (0.105, 0.29), (0.093, 0.285), (0.093, 0.0)]
    p.add(lathe(fuelle, 16, eje((EJE_X, yb + 0.02, EJE_Z), (0, -1, 0)), cap0=False, cap1=False), "ink")
    dial(p, PF, EJE_X, 1.37, 0.08, 60, "white")
    dial(p, PF, 2.6, 1.02, 0.22, 100, "white")
    nota = T(PF, 3.98, 1.2, 0.05) @ Matrix.Rotation(math.radians(-8), 4, "Z")
    p.add(rbox((0.3, 0.3, 0.01), (0, 0, 0.005), 0.0, m=nota), "yellow")
    for k in range(3):
        p.add(decal(stroke((-0.11, 0.07 - 0.06 * k), (0.1 - 0.04 * k, 0.07 - 0.06 * k + 0.012), 0.022), nota, 0.012), "dsky")

    p.add(decal(rect(-2.95, 2.95, 0.09, 1.0), BF, 0.004), "lmetal")
    p.add(rbox((5.82, 0.85, MCP_W), (0, 0.545, MCP_W / 2), 0.008, 1, m=BF), "ink")
    for (nombre, texto, col, dcol), u in zip(BOTONES, BOTON_U):
        caja_boton(p, BF, u, BOTON_V, nombre == "BotonExtintor")
        p.add(rr_loft(1.0, 0.19, 0.04, 2, [(0.0, 0.0), (0.0, 0.01), (0.006, 0.016)], T(BF, u, 0.245, MCP_W), cap0=False), "cream")
        p.add(decal(rect(u - 0.44, u + 0.44, 0.165, 0.18), BF, MCP_W + 0.02), col)
        p.add(xf(text_bm(texto, 0.1, 0.88), T(BF, u, 0.262, MCP_W + 0.02)), "ink")
    for s in (-1, 1):
        p.add(rr_loft(1.02, 0.5, 0.08, 2, [(0.0, 0.0), (0.0, 0.02)], T(BF, s * 3.82, 0.56, 0.0), cap0=False), "ink")
        luz_aviso(p, T(BF, 0, 0, 0.02), s * 3.57, 0.56, 0.15, "red")
        luz_aviso(p, T(BF, 0, 0, 0.02), s * 4.07, 0.56, 0.15, "amber")
        p.add(rbox((0.48, 0.48, 0.03), (s * 4.88, 0.56, 0.015), 0.012, 1, m=BF), "dgrey")
        for k in range(4):
            p.add(decal(rrect(s * 4.88, 0.41 + 0.1 * k, 0.36, 0.04, 0.018, 1), BF, 0.034), "ink")
    top_y = 4.3
    top_z = 3.80 + (3.66 - 3.80) * (top_y - 3.44) / (4.93 - 3.44)
    pato(p, (4.55, top_y, top_z - 0.01))
    return p


# ---------------------------------------------------------------- yoke

def p_volante():
    p = Prop("CabinaVolante", 3000)
    x0, z0 = EJE_X, EJE_Z
    yh = 2.12
    p.add(stick((x0, yh + 0.1, z0), (x0, 3.9, z0), 0.085, 0.085, 16, cap0=True, cap1=True), "metal")
    p.add(lathe([(0.11, 0.0), (0.12, 0.02), (0.12, 0.08), (0.11, 0.1)], 16, eje((x0, 2.3, z0), (0, 1, 0))), "ink")
    p.add(rbox((0.44, 0.26, 0.38), (x0, yh, z0), 0.09, 2), "grey")
    cara = frame((x0, yh - 0.131, z0), (1, 0, 0), (0, 0, 1))
    p.add(decal(circ(0, 0, 0.12, 16), cara, 0.0), "orange")
    p.add(decal([(-0.08, -0.02), (0.02, 0.07), (0.09, 0.07), (-0.01, -0.03)], cara, 0.004), "cream")
    p.add(decal([(-0.06, -0.07), (0.01, -0.0), (0.06, -0.0), (-0.01, -0.07)], cara, 0.004), "cream")
    for s in (-1, 1):
        ctrl = [(x0 + s * 0.1, yh, z0 - 0.06), (x0 + s * 0.4, yh - 0.02, z0 - 0.19), (x0 + s * 0.62, yh - 0.05, z0 - 0.08),
                (x0 + s * 0.66, yh - 0.08, z0 + 0.22), (x0 + s * 0.6, yh - 0.1, z0 + 0.48)]
        p.add(tube(ctrl, lambda u: 0.075 + 0.012 * u, 10, 4, cap_rings=3), lambda c, n, s=s: "ink" if c.z > z0 - 0.02 and abs(c.x - x0) > 0.5 else "mgrey", 60)
        camino = catmull([Vector(c) for c in ctrl], 12)
        for zz in (z0 + 0.06, z0 + 0.32):
            i = min(range(2, len(camino) - 1), key=lambda j: abs(camino[j].z - zz) + (0 if abs(camino[j].x - x0) > 0.5 else 9))
            tg = (camino[i + 1] - camino[i - 1]).normalized()
            p.add(lathe([(0.088, -0.025), (0.098, 0.0), (0.088, 0.025)], 12, eje(camino[i], tg)), "orange")
        p.add(cyl(0.03, 0.04, (x0 + s * 0.6, yh - 0.1, z0 + 0.55), seg=8, rot=(0, 0, 0)), "red" if s < 0 else "yellow")
    clip = frame((x0, yh - 0.02, z0 + 0.19), (1, 0, 0), (0, 0.5, 1))
    p.add(rbox((0.36, 0.26, 0.012), (0, 0.11, 0.0), 0.0, m=clip), "paper")
    for k in range(4):
        p.add(decal(rect(-0.13, 0.13 - 0.05 * (k % 2), 0.17 - 0.045 * k, 0.185 - 0.045 * k), clip, 0.007), "lgrey")
    p.add(rbox((0.16, 0.05, 0.03), (0, 0.235, 0.014), 0.01, 1, m=clip), "metal")
    return p


# ---------------------------------------------------------------- pedestal / throttle

PERFIL_PEDESTAL = [(0.85, 0.0), (0.85, 1.15), (1.0, 1.30), (3.25, 1.48), (3.20, 1.26), (3.28, 1.10), (3.70, 0.0)]
RADIOS_PEDESTAL = [0.0, 0.1, 0.12, 0.03, 0.0, 0.0, 0.0]
PW = 0.8
TF = frame((0, 1.0, 1.30), (1, 0, 0), (0, 2.25, 0.18))
PALANCA_U, PALANCA_V, PALANCA_W = 0.17, 1.55, 0.2
JOROBA_H = 0.23


def p_gases():
    p = Prop("CabinaGases", 6000)
    prof = fillet(PERFIL_PEDESTAL, RADIOS_PEDESTAL, 3)
    body = yprism(prof, -PW, PW)
    bevel_sharp(body, 0.03, 1, 60)
    p.add(body, lambda c, n: "grey" if abs(n.x) > 0.7 else ("dgrey" if n.z > 0.5 else "grey"), 40)
    for s in (-1, 1):
        lado = frame((s * PW, 0, 0), (0, s, 0), (0, 0, 1))
        p.add(decal(rect(s * 0.95, s * 3.15, 0.9, 0.96) if s > 0 else rect(-3.15, -0.95, 0.9, 0.96), lado, 0.004), "teal")
        for k in range(4):
            yy = 1.25 + 0.1 * k
            p.add(decal(rrect(s * yy, 0.45, 0.05, 0.4, 0.022, 1), lado, 0.004), "ink")
        mm = eje((s * (PW - 0.01), 2.45, 0.92), (s, 0, 0))
        p.add(lathe([(0.0, 0.0), (0.33, 0.0), (0.36, 0.02), (0.36, 0.06), (0.33, 0.08), (0.12, 0.08), (0.0, 0.08)], 20, mm, cap0=False, cap1=False), "ink")
        for k in range(10):
            a = 2 * math.pi * k / 10
            p.add(rbox((0.08, 0.035, 0.02), (0.34 * math.cos(a), 0.34 * math.sin(a), 0.081), 0.0, rot=(0, 0, math.degrees(a)), m=mm), "white" if k == 0 else "mgrey")
        p.add(cyl(0.1, 0.03, (0, 0, 0.08), seg=12, m=mm, cap0=False), "cream")
    hump = rr_loft(0.84, 0.95, 0.12, 2, [(0.0, 0.0), (0.0, JOROBA_H - 0.04), (0.04, JOROBA_H)], T(TF, 0.0, PALANCA_V, 0.0), cap0=False)
    p.add(hump, lambda c, n: "dgrey" if n.dot(TF.col[2].to_3d()) > 0.7 else "mgrey", 40)
    for s in (-1, 1):
        u = s * PALANCA_U
        p.add(decal(rrect(u, PALANCA_V, 0.07, 0.72, 0.03, 2), TF, JOROBA_H + 0.003), "ink")
        for k in range(6):
            vv = PALANCA_V - 0.3 + 0.12 * k
            p.add(decal(rect(u + s * 0.06, u + s * 0.12, vv - 0.008, vv + 0.008), TF, JOROBA_H + 0.003), "white")
    p.add(decal(rect(-0.03, 0.03, PALANCA_V - 0.3, PALANCA_V + 0.3), TF, JOROBA_H + 0.003), "orange")
    p.add(decal(rrect(0.6, 0.95, 0.06, 0.5, 0.025, 1), TF, 0.004), "ink")
    for k in range(4):
        p.add(decal(rect(0.63, 0.7, 0.75 + 0.12 * k, 0.765 + 0.12 * k), TF, 0.006), "white")
    pv = TF @ Vector((0.6, 0.85, 0.0))
    tip = TF @ Vector((0.6, 0.95, 0.24))
    p.add(stick(pv, tip, 0.022, 0.022, 6), "metal")
    p.add(rbox((0.07, 0.2, 0.07), tuple(tip), 0.03, 2), "cream")
    p.add(decal(rrect(-0.6, 0.95, 0.06, 0.5, 0.025, 1), TF, 0.004), "ink")
    pv = TF @ Vector((-0.6, 0.78, 0.0))
    tip = TF @ Vector((-0.6, 0.7, 0.2))
    p.add(stick(pv, tip, 0.02, 0.02, 6), "metal")
    p.add(rbox((0.2, 0.06, 0.06), tuple(tip), 0.025, 1), "ink")
    radio = T(TF, -0.12, 0.38, 0.0)
    p.add(rr_loft(0.96, 0.5, 0.06, 2, [(0.0, 0.0), (0.0, 0.05), (0.012, 0.062)], radio, cap0=False), "mgrey")
    for k, uu in enumerate((-0.22, 0.14)):
        p.add(decal(rrect(uu, 0.07, 0.3, 0.12, 0.02, 1), radio, 0.066), "navy")
        for j in range(3):
            p.add(decal(rect(uu - 0.11 + 0.08 * j, uu - 0.05 + 0.08 * j, 0.04, 0.1), radio, 0.07), "green")
    for uu in (-0.3, -0.1, 0.1, 0.3):
        perilla(p, T(radio, 0.0, 0.0, 0.062), uu, -0.12, 0.045)
    taza = TF @ Vector((0.55, 0.36, 0.0))
    p.add(lathe([(0.13, 0.0), (0.14, 0.04), (0.11, 0.04), (0.11, 0.01)], 14, M(taza), cap0=False, closed=False), "ink")
    p.add(lathe([(0.0, 0.01), (0.085, 0.01), (0.095, 0.05), (0.1, 0.24), (0.085, 0.24), (0.085, 0.215), (0.0, 0.215)], 14, M(taza)),
          lambda c, n: "coffee" if c.z - taza.z > 0.2 and n.z > 0.5 else ("orange" if 0.11 < c.z - taza.z < 0.15 else "cream"))
    p.add(tube([(taza.x + 0.09, taza.y, taza.z + 0.19), (taza.x + 0.16, taza.y, taza.z + 0.17), (taza.x + 0.16, taza.y, taza.z + 0.08), (taza.x + 0.09, taza.y, taza.z + 0.07)],
               lambda u: 0.018, 6, 3, caps=False), "cream", 70)
    atras = frame((0, 0.85, 0.0), (1, 0, 0), (0, 0, 1))
    p.add(rr_loft(1.1, 0.7, 0.06, 2, [(0.0, 0.0), (0.0, 0.04)], T(atras, 0.0, 0.62, 0.0), cap0=False), "mgrey")
    for k, (dx, ang, col) in enumerate(((-0.12, -6, "paper"), (0.1, 5, "cream"), (0.32, -3, "yellow"))):
        p.add(rbox((0.42, 0.012, 0.36), (dx, 0.83, 0.92), 0.0, rot=(0, ang, 0)), col)
    return p


def p_palanca():
    p = Prop("CabinaPalanca", 600)
    p.add(cyl(0.035, 0.08, (0, 0, 0.0), seg=8, cap0=True), "mgrey")
    p.add(bar((0, 0, 0.06), (0, 0, 0.36), 0.05, 0.05, 0.015, up=(0, 1, 0)), "metal")
    p.add(rr_loft(0.16, 0.12, 0.05, 2, [(0.03, 0.34), (0.0, 0.37), (0.0, 0.45), (0.02, 0.49), (0.05, 0.5)]), "orange")
    p.add(rr_loft(0.165, 0.125, 0.05, 2, [(0.0, 0.39), (0.0, 0.42)], cap0=False, cap1=False), "ink")
    p.add(decal(rrect(0.0, 0.0, 0.08, 0.05, 0.02, 1), M((0, 0, 0.502))), "cream")
    return p


# ---------------------------------------------------------------- buttons

def icono_llama():
    return [(teardrop(0.0, -0.035, 0.07, 0.115, 0.012, 10), "cream", 0.0),
            (teardrop(0.0, -0.05, 0.035, 0.06, -0.005, 8), "yellow", 0.004),
            (teardrop(0.0, 0.0, 0.025, 0.05, 0.0, 6), "cream", 0.0)]


def icono_ventilador():
    out = [(circ(0, 0, 0.125, 20), "ink", 0.0), (circ(0, 0, 0.105, 20), "yellow", 0.004)]
    for k in range(8):
        a = math.radians(45 * k)
        pol = [(0.03, -0.22), (0.1, 0.08), (0.1, 0.3), (0.03, 0.12)]
        out.append(([(r * math.cos(a + t), r * math.sin(a + t)) for r, t in pol], "ink", 0.008))
    out.append((circ(0, 0, 0.042, 12), "ink", 0.008))
    out.append((circ(0, 0, 0.018, 8), "cream", 0.012))
    return out


def icono_hebilla():
    ca, sa = math.cos(math.radians(-14)), math.sin(math.radians(-14))
    resp = [(-0.035 + x * ca - y * sa, 0.03 + x * sa + y * ca) for x, y in rr_pts(0.06, 0.15, 0.025, 2)]
    return [(resp, "cream", 0.0), (rrect(0.02, -0.07, 0.15, 0.05, 0.022, 2), "cream", 0.0),
            (stroke((-0.075, 0.075), (0.075, -0.035), 0.026), "ink", 0.004),
            (rrect(0.02, 0.005, 0.045, 0.04, 0.008, 1), "ink", 0.008), (rrect(0.02, 0.005, 0.022, 0.018, 0.004, 1), "cream", 0.012)]


def icono_rampa():
    return [(rect(-0.11, -0.075, -0.06, 0.1), "cream", 0.0), (stroke((-0.09, -0.045), (0.105, -0.095), 0.035), "cream", 0.0),
            ([(0.02, 0.07), (0.1, 0.07), (0.1, -0.01)], "cream", 0.0), (stroke((0.09, 0.055), (0.0, -0.025), 0.03), "cream", 0.0)]


def p_tapa(nombre, col, dcol):
    p = Prop(nombre, 900)
    prof = [(TAPA_R, 0.0), (TAPA_R, 0.13), (TAPA_R - 0.004, 0.16), (TAPA_R - 0.018, 0.183), (TAPA_R - 0.042, 0.197), (TAPA_R - 0.07, TAPA_H), (0.0, TAPA_H)]
    p.add(lathe(prof, 24, cap0=True), lambda c, n: dcol if c.z < 0.125 and n.z < 0.5 else col, 40)
    top = M((0, 0, TAPA_H + 0.003)) @ Matrix.Rotation(math.pi, 4, "Z")
    if nombre == "BotonAuto":
        p.add(xf(text_bm("A", 0.15), top), "cream")
    else:
        capas = {"BotonExtintor": icono_llama, "BotonMotor": icono_ventilador, "BotonCinturon": icono_hebilla, "BotonRampa": icono_rampa}[nombre]()
        for pts, c, w in capas:
            p.add(decal(pts, top, w), c)
    p.add(arc_strip(0, 0, 0.115, 0.13, 110, 160, 5, M((0, 0, TAPA_H + 0.002)) @ Matrix.Rotation(math.pi, 4, "Z")), "white")
    return p


# ---------------------------------------------------------------- shell

WALL_X = 5.5
SHELL_Y0, SHELL_Y1 = -4.95, 4.95
FRAME_Y1 = 5.25
OF_A = Vector((0, 4.38, 7.02))
OF_B = Vector((0, 0.66, 7.68))
OF = frame((0, OF_A.y, OF_A.z), (1, 0, 0), tuple(OF_B - OF_A))
OF_L = (OF_B - OF_A).length
VENTANAS = [(3.15, 5.2, 2.1, 1.6, 0.4), (0.9, 5.25, 1.5, 1.4, 0.4)]
LAMP = (-0.5, 0.5, -0.75, 0.25)


def p_forro():
    p = Prop("CabinaForro", 16000)
    for s in (-1, 1):
        Fin = frame((s * WALL_X, 0, 0), (0, -s, 0), (0, 0, 1))

        def loc(y, z, s=s):
            return (-s * y, z)
        holes = []
        for cy_, cz_, ww, hh, rr in VENTANAS:
            holes.append([loc(cy_ + u, cz_ + v) for u, v in rr_pts(ww + 0.04, hh + 0.04, rr + 0.02, 3)])
        upper = [loc(SHELL_Y0, 1.25), loc(SHELL_Y1, 1.25), loc(SHELL_Y1, 7.0), loc(SHELL_Y0, 7.0)]
        p.add(plate(upper, holes, 0.3, Fin, z0=-0.3), "wall")
        lower = [loc(SHELL_Y0, 0.0), loc(SHELL_Y1, 0.0), loc(SHELL_Y1, 1.25), loc(SHELL_Y0, 1.25)]
        p.add(plate(lower, [], 0.3, Fin, z0=-0.3), "wall2")
        p.add(bar((s * (WALL_X - 0.05), SHELL_Y0, 1.25), (s * (WALL_X - 0.05), 2.85, 1.25), 0.1, 0.16, 0.04, up=(0, 0, 1)), "teal")
        for cy_, cz_, ww, hh, rr in VENTANAS:
            wp = cw([loc(cy_ + u, cz_ + v) for u, v in rr_pts(ww, hh, rr, 3)])
            p.add(sweep(wp, [(0.04, -0.3), (0.0, -0.3), (0.0, 0.08), (0.04, 0.12), (0.14, 0.12), (0.2, 0.0)], Fin, closed=True), "mgrey", 40)
        g = frame((s * (WALL_X - 0.004), 0, 0), (0, -s, 0), (0, 0, 1))
        for gy in (-1.4, 2.0):
            gm = T(g, -s * gy, 4.0, 0.0)
            p.add(lathe([(0.13, 0.0), (0.13, 0.03), (0.1, 0.06), (0.06, 0.07), (0.0, 0.07)], 12, gm, cap0=False), "lmetal")
            p.add(lathe([(0.05, 0.072), (0.0, 0.072)], 10, gm, cap0=False, cap1=False), "ink")
        bolsa = T(g, -s * (-0.3), 1.75, 0.0)
        p.add(rr_loft(1.1, 0.7, 0.08, 2, [(0.0, 0.0), (0.0, 0.1), (0.02, 0.12)], bolsa, cap0=False), "mgrey")
        for k, (dx, h, col, ang) in enumerate(((-0.25, 0.42, "paper", -4), (0.05, 0.5, "sky", 3), (0.3, 0.38, "yellow", -2))):
            p.add(rbox((0.3, h, 0.02), (dx, 0.45 - h / 2, 0.07), 0.0, rot=(0, 0, ang), m=bolsa), col)
    inner = [(WALL_X, 7.0), (5.42, 7.4), (5.2, 7.72), (4.85, 7.9), (4.5, 7.95)]
    poly = [(-(WALL_X + 0.3), 7.0)] + [(-x, z) for x, z in inner] + [(x, z) for x, z in reversed(inner)] + [(WALL_X + 0.3, 7.0), (WALL_X + 0.3, 8.0), (-(WALL_X + 0.3), 8.0)]
    p.add(prism(poly, SHELL_Y1 - SHELL_Y0, frame((0, SHELL_Y1, 0), (1, 0, 0), (0, 0, 1)), z0=0.0), "ceil")
    x0, x1, y0, y1 = LAMP
    outer = rr_pts(1.4, 1.4, 0.12, 2)
    hole = rr_pts(1.08, 1.08, 0.06, 2)
    lm = frame(((x0 + x1) / 2, (y0 + y1) / 2, 7.95), (1, 0, 0), (0, -1, 0))
    p.add(plate([(a, b) for a, b in outer], [[(a, b) for a, b in hole]], 0.17, lm, z0=0.0), "lmetal")
    for s in (-1, 1):
        p.add(lathe([(0.2, 0.0), (0.2, 0.06), (0.14, 0.13), (0.0, 0.15)], 12, frame((s * 2.6, 0.3, 7.95), (1, 0, 0), (0, -1, 0))), "lmetal")
        p.add(decal(circ(0, 0, 0.09, 10), frame((s * 2.6, 0.3, 7.95 - 0.152), (1, 0, 0), (0, -1, 0))), "cream")

    hole = rr_pts(11.04, 4.04, 0.32, 3)
    hole = [(x, z + 5.5) for x, z in hole]
    outer = [(-5.4, 0.0), (5.4, 0.0), (WALL_X + 0.3, 0.5), (WALL_X + 0.3, 7.6), (5.4, 8.0), (-5.4, 8.0), (-(WALL_X + 0.3), 7.6), (-(WALL_X + 0.3), 0.5)]
    wfm = frame((0, SHELL_Y1, 0), (-1, 0, 0), (0, 0, 1))
    p.add(plate(outer, [hole], FRAME_Y1 - SHELL_Y1, wfm, z0=0.0), "wall")
    lip = [(5.52, 3.75)]
    lip += [(5.2 + 0.32 * math.cos(math.radians(a)), 7.2 + 0.32 * math.sin(math.radians(a))) for a in (0, 22.5, 45, 67.5, 90)]
    lip += [(-5.2 + 0.32 * math.cos(math.radians(a)), 7.2 + 0.32 * math.sin(math.radians(a))) for a in (90, 112.5, 135, 157.5, 180)]
    lip += [(-5.52, 3.75)]
    lipm = frame((0, SHELL_Y1, 0), (1, 0, 0), (0, 0, 1))
    p.add(rev(sweep(lip, [(0.03, 0.0), (0.03, 0.08), (-0.01, 0.13), (-0.17, 0.15), (-0.23, 0.1), (-0.27, 0.0)], lipm)), "mgrey", 40)
    p.add(bevel_sharp(bb(-0.18, 0.18, 4.64, SHELL_Y1, 3.72, 7.62), 0.06, 2, 60), "mgrey", 40)
    p.add(rbox((0.3, 0.16, 0.22), (0, 4.56, 6.8), 0.05, 1), "ink")
    p.add(ellipsoid((0.11, 0.11, 0.11), Matrix.Translation((0, 4.47, 6.8)), 12, 8), lambda c, n: "cream" if n.y < -0.5 else "ink")
    p.add(decal(rect(-0.01, 0.01, -0.06, 0.06), frame((0, 4.355, 6.8), (1, 0, 0), (0, 0, 1)), 0.0), "red")
    for s in (-1, 1):
        vm = frame((s * 3.65, 4.25, 7.8), (1, 0, 0), (0, 1, 0.25))
        p.add(rbox((2.1, 0.66, 0.05), (0, 0, 0), 0.02, 1, m=vm), "navy2")
        for dx in (-0.8, 0.8):
            p.add(bar(vm @ Vector((dx, 0.25, 0.02)), (s * 3.65 + dx, 4.5, 7.95), 0.06, 0.06, 0.015), "mgrey")
    prof = [(OF_B.y - 0.06, 7.95), (OF_B.y - 0.06, OF_B.z + 0.02), (OF_B.y, OF_B.z), (OF_A.y, OF_A.z), (OF_A.y + 0.06, OF_A.z + 0.06), (OF_A.y + 0.06, 7.95)]
    box = yprism(prof, -1.85, 1.85)
    bevel_sharp(box, 0.04, 1, 30)
    p.add(box, lambda c, n: "panel" if n.dot(OF.col[2].to_3d()) > 0.9 else "dgrey", 35)
    overhead(p)
    return p


def overhead(p):
    m = OF
    L = OF_L
    grupos = [(-1.65, 1.65, 0.12, 0.62), (-1.65, -0.1, 0.72, 1.42), (0.1, 1.65, 0.72, 1.42), (-1.65, 1.65, 1.52, 2.2), (-1.65, 1.65, 2.3, 2.95), (-1.65, 1.65, 3.05, 3.62)]
    for u0, u1, v0, v1 in grupos:
        for r in (rect(u0, u1, v0, v0 + 0.018), rect(u0, u1, v1 - 0.018, v1), rect(u0, u0 + 0.018, v0, v1), rect(u1 - 0.018, u1, v0, v1)):
            p.add(decal(r, m, 0.006), "white")
    for k, u in enumerate((-1.2, -0.6, 0.0, 0.6, 1.2)):
        perilla(p, m, u, 0.37, 0.11, "ink", "white")
        p.add(arc_strip(u, 0.37, 0.15, 0.17, 200, 340, 6, m, 0.006), "panel2")
    for g, us in ((-1, (-1.45, -1.05, -0.65, -0.3)), (1, (0.3, 0.65, 1.05, 1.45))):
        for k, u in enumerate(us):
            toggle(p, m, u, 1.0, 1.0 if (k + g) % 3 else -1.0, ("cream", "orange", "teal", "cream")[k], "mgrey", 0.15, 1.5)
            p.add(decal(circ(u, 1.28, 0.04, 8), m, 0.006), "ink")
            p.add(decal(circ(u, 1.28, 0.028, 8), m, 0.01), ("green", "amber", "green", "green")[k] if g < 0 else ("green", "green", "red", "amber")[k])
    for k, (u, col) in enumerate(((-1.1, "amber"), (-0.37, "green"), (0.37, "sky"), (1.1, "green"))):
        lampara(p, m, u, 1.86, 0.5, 0.44, "ink", 0.05, False)
        p.add(decal(rrect(u, 1.86, 0.4, 0.34, 0.03, 2), m, 0.054), col)
        p.add(decal(rect(u - 0.12, u + 0.12, 1.84, 1.88), m, 0.058), "white")
    for k, u in enumerate((-1.4, -0.85, -0.3, 0.3, 0.85, 1.4)):
        guard = k in (0, 5)
        toggle(p, m, u, 2.62, -1.0 if k % 2 else 1.0, "red" if guard else "white", "mgrey", 0.15, 1.5)
        if guard:
            for s in (-1, 1):
                p.add(bar(m @ Vector((u + s * 0.14, 2.62 - 0.17, 0.0)), m @ Vector((u + s * 0.14, 2.62 - 0.17, 0.26)), 0.045, 0.045, 0.012), "red")
                p.add(bar(m @ Vector((u + s * 0.14, 2.62 + 0.17, 0.0)), m @ Vector((u + s * 0.14, 2.62 + 0.17, 0.26)), 0.045, 0.045, 0.012), "red")
                p.add(bar(m @ Vector((u + s * 0.14, 2.62 - 0.17, 0.26)), m @ Vector((u + s * 0.14, 2.62 + 0.17, 0.26)), 0.045, 0.045, 0.012), "red")
    for s in (-1, 1):
        perilla(p, m, s * 0.95, 3.33, 0.15, "ink", "orange")
        for j in range(7):
            a = math.radians(210 - 240 * j / 6)
            c = Vector((s * 0.95, 3.33)) + Vector((math.cos(a), math.sin(a))) * 0.23
            p.add(decal(circ(c.x, c.y, 0.016, 6), m, 0.006), "white")
    p.add(rr_loft(0.7, 0.3, 0.04, 2, [(0.0, 0.0), (0.0, 0.03)], T(m, 0.0, 3.33, 0.0), cap0=False), "ink")
    p.add(decal(rrect(0.0, 3.33, 0.6, 0.2, 0.03, 1), m, 0.034), "navy")
    for j in range(4):
        p.add(decal(rect(-0.24 + 0.13 * j, -0.16 + 0.13 * j, 3.27, 3.39), m, 0.038), "green")


BUILDERS = [p_forro, p_cuadro, p_volante, p_gases, p_palanca] + [
    (lambda n=n, c=c, d=d: p_tapa(n, c, d)) for n, _, c, d in BOTONES]
EN_SITIO = {"CabinaForro", "CabinaCuadro", "CabinaVolante", "CabinaGases"}


def colocaciones():
    out = {}
    n = BF.col[2].to_3d()
    up = BF.col[1].to_3d()
    for (nombre, _, _, _), u in zip(BOTONES, BOTON_U):
        base = BF @ Vector((u, BOTON_V, MCP_W + TAPA_BASE))
        m = Matrix((-BF.col[0].to_3d(), -up, n)).transposed().to_4x4()
        m.translation = base
        out[nombre] = m
    for s in (-1, 1):
        piv = TF @ Vector((s * PALANCA_U, PALANCA_V, PALANCA_W))
        m = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(-24), 4, "X") @ Matrix.Rotation(math.pi, 4, "Z")
        out["CabinaPalanca%+d" % s] = m
    return out


# ---------------------------------------------------------------- renders

MATS = {}


def mat_rgb(hx, rough=0.9, emit=0.0):
    key = (hx, rough, emit)
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
    MATS[key] = m
    return m


def render_setup(scene, threads):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = int(arg("--samples", "40"))
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
    bg.inputs[1].default_value = 0.9
    scene.world = world


def camera(loc, target, lens):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.clip_start = 0.05
    cd.clip_end = 500
    co = bpy.data.objects.new("Cam", cd)
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(co)
    bpy.context.scene.camera = co
    return co


def area(loc, size, power, rot=(0, 0, 0), sy=None, color=(1.0, 0.96, 0.9)):
    L = bpy.data.lights.new("A", "AREA")
    L.shape = "RECTANGLE"
    L.size = size
    L.size_y = sy if sy is not None else size
    L.energy = power
    L.color = color
    o = bpy.data.objects.new("A", L)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    bpy.context.scene.collection.objects.link(o)
    return o


def importar_asiento():
    ruta = os.path.join(ARTE, "props", "AsientoPiloto.fbx")
    if not os.path.exists(ruta):
        return None
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=ruta, axis_forward="Z", axis_up="Y")
    nuevos = [o for o in bpy.data.objects if o not in antes]
    malla = None
    for o in nuevos:
        if o.type == "MESH" and malla is None:
            malla = o
        elif o.type != "MESH":
            bpy.data.objects.remove(o)
    malla.parent = None
    malla.matrix_world = Matrix.Identity(4)
    malla.hide_render = True
    return malla


def montar(objs, offs):
    hechos = []
    for nombre in EN_SITIO:
        if nombre in objs:
            o = bpy.data.objects.new(nombre + "_i", objs[nombre].data)
            o.location = offs[nombre]
            bpy.context.scene.collection.objects.link(o)
            hechos.append(o)
    for clave, m in colocaciones().items():
        nombre = "CabinaPalanca" if clave.startswith("CabinaPalanca") else clave
        if nombre in objs:
            o = bpy.data.objects.new(clave + "_i", objs[nombre].data)
            o.matrix_world = m
            bpy.context.scene.collection.objects.link(o)
            hechos.append(o)
    asiento = importar_asiento()
    if asiento:
        for x in (-2.6, 2.6):
            o = bpy.data.objects.new("Asiento_i", asiento.data)
            o.matrix_world = Matrix.Translation((x, 0.25, 0.0)) @ Matrix.Rotation(math.pi, 4, "Z")
            bpy.context.scene.collection.objects.link(o)
            hechos.append(o)
    suelo = bpy.data.meshes.new("Suelo")
    suelo.from_pydata([(-5.8, -6, 0), (5.8, -6, 0), (5.8, 5.3, 0), (-5.8, 5.3, 0)], [], [(0, 1, 2, 3)])
    suelo.materials.append(mat_rgb("2B5459", 0.95))
    so = bpy.data.objects.new("Suelo", suelo)
    bpy.context.scene.collection.objects.link(so)
    lam = bpy.data.meshes.new("Lampara")
    x0, x1, y0, y1 = LAMP
    lam.from_pydata([(x0, y0, 7.8), (x1, y0, 7.8), (x1, y1, 7.8), (x0, y1, 7.8)], [], [(0, 3, 2, 1)])
    lam.materials.append(mat_rgb("F2E6CC", 0.5, 3.0))
    bpy.context.scene.collection.objects.link(bpy.data.objects.new("Lampara", lam))
    l = bpy.data.lights.new("Luz", "POINT")
    l.energy = 260
    l.color = (1.0, 0.93, 0.82)
    l.shadow_soft_size = 0.6
    lo = bpy.data.objects.new("Luz", l)
    lo.location = (0, -0.25, 6.9)
    bpy.context.scene.collection.objects.link(lo)
    area((0, -4.0, 6.0), 4.0, 400, rot=(-60, 0, 0), sy=2.0)
    return hechos


VISTAS = [
    ("cabina_kit_piloto.png", (-2.6, 0.05, 4.15), (-1.2, 4.2, 2.6), 15),
    ("cabina_kit_atras.png", (0.0, -4.6, 4.6), (0.0, 3.0, 2.6), 14),
    ("cabina_kit_techo.png", (0.6, -0.6, 3.6), (0.0, 2.6, 7.3), 14),
    ("cabina_kit_pedestal.png", (1.6, -0.2, 3.6), (0.0, 2.0, 1.4), 18),
    ("cabina_kit_mcp.png", (0.0, 1.2, 3.75), (0.0, 3.3, 3.25), 16),
    ("cabina_kit_yugo.png", (-1.3, 0.9, 3.0), (-2.6, 2.6, 2.2), 20),
]


def render_vistas(objs, offs, threads, outdir, which):
    scene = bpy.context.scene
    render_setup(scene, threads)
    for o in objs.values():
        o.hide_render = True
    montar(objs, offs)
    for i, (fname, loc, tgt, lens) in enumerate(VISTAS):
        if which and str(i + 1) not in which:
            continue
        camera(loc, tgt, lens)
        scene.render.filepath = os.path.join(outdir, fname)
        bpy.ops.render.render(write_still=True)
        print("RENDER", scene.render.filepath)


def revisar_caras(objs, offs):
    import random
    from mathutils.bvhtree import BVHTree
    verts, polys, dueno = [], [], []
    piezas = [(n, Matrix.Translation(offs[n])) for n in EN_SITIO if n in objs]
    piezas += [("CabinaPalanca" if c.startswith("CabinaPalanca") else c, m) for c, m in colocaciones().items()]
    for nombre, m in piezas:
        if nombre not in objs:
            continue
        me = objs[nombre].data
        base = len(verts)
        verts.extend(m @ v.co for v in me.vertices)
        for pg in me.polygons:
            polys.append([base + i for i in pg.vertices])
            dueno.append(nombre)
    arbol = BVHTree.FromPolygons(verts, polys)
    ojos = [(-2.6, 0.3, 4.1), (2.6, 0.3, 4.1), (0.0, -1.0, 4.0), (0.0, -4.2, 4.2), (0.0, 1.5, 3.8), (-1.2, 1.8, 3.2), (1.6, 2.0, 2.4), (3.5, -3.0, 3.0)]
    rnd = random.Random(1)
    malos, total = {}, 0
    for o in ojos:
        o = Vector(o)
        for _ in range(30000):
            d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
            loc, nrm, idx, dist = arbol.ray_cast(o, d)
            if idx is None:
                continue
            total += 1
            if nrm.dot(d) > 1e-4:
                clave = (dueno[idx], round(loc.x, 1), round(loc.y, 1), round(loc.z, 1))
                malos[clave] = malos.get(clave, 0) + 1
    n = sum(malos.values())
    print("CARAS impactos %d  traseras %d (%.4f%%)" % (total, n, 100.0 * n / max(total, 1)))
    for clave, c in sorted(malos.items(), key=lambda kv: -kv[1])[:40]:
        print("TRASERA %-14s en %6.1f %6.1f %6.1f  x%d" % (clave + (c,)))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    img = palette_image()
    mat = palette_material(img)
    only = arg("--only")
    only = set(only.split(",")) if isinstance(only, str) else None
    objs, offs = {}, {}
    manifest = []
    ok = True
    for b in BUILDERS:
        p = b()
        if only and p.name not in only:
            continue
        ob, tris, mn, mx, off = make_object(p, mat)
        objs[p.name] = ob
        offs[p.name] = off
        if tris > p.budget:
            ok = False
        dim = mx - mn
        print("PIECE %-14s tris %5d / %5d %s  size %.3f x %.3f x %.3f  min %.3f %.3f %.3f  max %.3f %.3f %.3f" % (
            p.name, tris, p.budget, "OK" if tris <= p.budget else "OVER", dim.x, dim.y, dim.z, mn.x, mn.y, mn.z, mx.x, mx.y, mx.z))
        if p.name in EN_SITIO:
            c = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)
            print("PLACE %-14s centro %s  base_y %.4f  (mundo x %.4f z %.4f)" % (p.name, mundo(c), YC + mn.z, c[0], ZC - c[1]))
        if not arg("--no-export"):
            export_fbx(ob)
        manifest.append({"nombre": p.name, "archivo": p.name + ".fbx", "tamano": [round(dim.x, 3), round(dim.z, 3), round(dim.y, 3)], "triangulos": tris})
    for clave, m in colocaciones().items():
        loc = m.translation
        up = m.col[2].to_3d()
        look = -m.col[1].to_3d()
        print("MOVIL %-16s base %s  up %s  look %s" % (clave, mundo(loc), tuple(round(c, 4) for c in (up.x, up.z, -up.y)), tuple(round(c, 4) for c in (look.x, look.z, -look.y))))
    if not arg("--no-export"):
        ruta = os.path.join(OUT, "manifest.json")
        if only and os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as fh:
                manifest = [e for e in json.load(fh) if e["nombre"] not in only] + manifest
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("ALL BUDGETS OK" if ok else "SOME PIECES OVER BUDGET")
    if arg("--rayos"):
        revisar_caras(objs, offs)
    if arg("--no-render"):
        return
    which = arg("--vistas")
    which = set(which.split(",")) if isinstance(which, str) else None
    outdir = arg("--render-dir")
    outdir = outdir if isinstance(outdir, str) else OUT
    threads = arg("--threads")
    render_vistas(objs, offs, int(threads) if isinstance(threads, str) else 12, outdir, which)


main()
