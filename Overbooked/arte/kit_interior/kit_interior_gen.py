import bpy
import bmesh
import math
import os
import sys
import json
import mathutils
from mathutils import Vector, Matrix, Euler

_SEP = {}
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "herramientas", "separar_capas.py"), encoding="utf-8") as _fh:
    exec(compile(_fh.read(), "separar_capas.py", "exec"), _SEP)

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
PROPS = os.path.join(os.path.dirname(OUT), "props")
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
    ("sand", "D9C6A3"), ("cream2", "F0E2C6"), ("dteal", "16766F"), ("lteal", "A3DED8"),
    ("dorange", "C95A1E"), ("green", "2FA552"), ("yellow", "FFD23F"), ("steel", "6E7782"),
    ("lmetal", "D3D9DE"), ("slate", "46525B"), ("light", "FFF9E8"), ("mirror", "C3E4F0"),
    ("hold", "C9C2B5"), ("navy", "2D3A4A"), ("peach", "F7B888"), ("grey", "8C939B"),
]
GRID = 8
IDX = {n: i for i, (n, _) in enumerate(PAL)}


def suv(n):
    i = IDX[n]
    return ((i % GRID + 0.5) / GRID, (i // GRID + 0.5) / GRID)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


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
    ey = ez.cross(ex).normalized()
    m = Matrix((ex, ey, ez)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


def yzx(loc=(0, 0, 0)):
    m = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    m.translation = Vector(loc)
    return m


def WF(y, x=0.0, z=0.0):
    return frame((x, y, z), (1, 0, 0), (0, 0, 1))


def WB(y, x=0.0, z=0.0):
    return frame((x, y, z), (-1, 0, 0), (0, 0, 1))


def DOWN(z, x=0.0, y=0.0):
    return frame((x, y, z), (1, 0, 0), (0, -1, 0))


def UP(z, x=0.0, y=0.0):
    return frame((x, y, z), (1, 0, 0), (0, 1, 0))


def bevel_edges(bm, edges, off, seg=1):
    if edges:
        bmesh.ops.bevel(bm, geom=list(edges) + list({v for e in edges for v in e.verts}), offset=off, offset_type="OFFSET",
                        segments=seg, profile=0.5, affect="EDGES", clamp_overlap=True)
    return bm


def bevel_where(bm, pred, off, seg=1, ang=30):
    bm.normal_update()
    es = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(ang) and pred(e)]
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


def yprism(pts, x0, x1, bev=0.0, bseg=1):
    return prism(pts, x1 - x0, yzx(((x0 + x1) / 2, 0, 0)), bev, bseg)


def xzprism(pts, y0, y1, bev=0.0, bseg=1):
    return prism(pts, y1 - y0, frame((0, y1, 0), (1, 0, 0), (0, 0, 1)), bev, bseg, z0=0.0)


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
    profs = [prof(i, P[i]) if callable(prof) else prof for i in range(n)]

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
        rings.append([bm.verts.new((P[i].x + nm.x * o * s, P[i].y + nm.y * o * s, d)) for o, d in profs[i]])
    k = len(profs[0])
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


def offset_pts(pts, cx, cy):
    return [(x + cx, y + cy) for x, y in pts]


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
    hint = Vector(up) if up is not None else Vector((0, 0, 1))
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


def grid_solid(rows, closed_u=False):
    bm = bmesh.new()
    V = [[bm.verts.new(p) for p in row] for row in rows]
    R, C = len(V), len(V[0])
    cs = C if closed_u else C - 1
    for i in range(R - 1):
        for j in range(cs):
            j2 = (j + 1) % C
            bm.faces.new((V[i][j], V[i][j2], V[i + 1][j2], V[i + 1][j]))
    return bm, V


class Piece:
    def __init__(self, name, size, budget):
        self.name = name
        self.size = size
        self.budget = budget
        self.parts = []

    def add(self, bm, role, ang=50.0):
        self.parts.append((bm, role, ang))
        return bm


def by_normal(front, back=None, side=None, axis=1, thr=0.5):
    def f(c, n):
        v = n[axis]
        if v < -thr:
            return front
        if v > thr and back is not None:
            return back
        return side if side is not None else front
    return f


WALL_ZOC = [(0.35, 0.0), (-0.06, 0.0), (-0.06, 0.3), (-0.1, 0.36), (-0.1, 3.3), (0.35, 3.3)]
WALL_RAIL = [(0.1, 3.22), (-0.13, 3.22), (-0.17, 3.26), (-0.19, 3.36), (-0.17, 3.48), (-0.13, 3.53), (0.1, 3.53)]


def wall_upper(z0):
    pts = [(0.35, z0)]
    for k in range(7):
        s = k / 6
        pts.append((0.05 - 0.4 * s * s, z0 + (10.0 - z0) * s))
    pts.append((0.35, 10.0))
    return pts


def zoc_role(c, n):
    return "dark" if c.z < 0.34 and n.y < -0.3 else "sand"


def wall_lower(p, x0, x1, bev=0.03):
    p.add(yprism(WALL_ZOC, x0, x1, bev), zoc_role)
    p.add(yprism(WALL_RAIL, x0, x1, bev * 0.7), "teal")


def p_panel_ventana():
    p = Piece("PanelVentana", (4.5, 0.7, 10.0), 900)
    W = 2.25
    wall_lower(p, -W, W)
    hole = offset_pts(rr_pts(1.6, 2.2, 0.62, 4), 0.0, 5.0)
    big = offset_pts(rr_pts(1.64, 2.24, 0.64, 4), 0.0, 5.0)
    band = plate(rect(-W, W, 3.45, 6.6), [big], 0.3, frame((0, 0.35, 0), (1, 0, 0), (0, 0, 1)))
    bevel_where(band, lambda e: all(abs(abs(v.co.x) - W) < 1e-4 and v.co.y < 0.1 for v in e.verts), 0.03)
    p.add(band, "cream")
    p.add(yprism(wall_upper(6.6), -W, W, 0.03), "cream")
    base = [(0.05, -0.3), (0.0, -0.3), (0.0, 0.07), (0.05, 0.11), (0.19, 0.11), (0.25, 0.0)]
    visor = [(0.05, -0.3), (0.0, -0.3), (0.0, 0.3), (0.05, 0.34), (0.14, 0.3), (0.25, 0.0)]
    path = cw(hole)

    def prof(i, P):
        w = min(1.0, max(0.0, (P.y - 5.05) / 1.05)) ** 1.6
        return [(a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w) for a, b in zip(base, visor)]
    p.add(sweep(path, prof, WF(0.05), closed=True), "white", 40)
    for k, z in enumerate((0.62, 0.8, 0.98)):
        p.add(decal(rr_pts(1.5 - 0.12 * k, 0.08, 0.04, 2), WF(-0.104, 0.0, z)), "dark")
    return p


def p_panel_salida():
    p = Piece("PanelSalida", (4.5, 0.7, 10.0), 700)
    W, hw, H, r = 2.25, 1.7, 6.5, 0.3
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (hw + 0.02), sx * W))
        wall_lower(p, x0, x1)
        p.add(yprism([(0.35, 3.45), (0.05, 3.45), (0.05, H + 0.04), (0.35, H + 0.04)], x0, x1, 0.03), "cream")
    p.add(yprism(wall_upper(H + 0.04), -W, W, 0.03), "cream")
    path = [(-hw, 0.0), (-hw, H - r)]
    for k in range(1, 4):
        a = math.radians(180 - 90 * k / 4)
        path.append((-hw + r + r * math.cos(a), H - r + r * math.sin(a)))
    path += [(-hw + r, H), (hw - r, H)]
    for k in range(1, 4):
        a = math.radians(90 - 90 * k / 4)
        path.append((hw - r + r * math.cos(a), H - r + r * math.sin(a)))
    path += [(hw, H - r), (hw, 0.0)]
    prof = [(0.05, -0.3), (0.0, -0.3), (0.0, 0.18), (0.04, 0.22), (0.2, 0.22), (0.27, 0.15), (0.27, 0.0)]
    p.add(sweep(path, prof, WF(0.05)), "white", 40)
    zc = 7.08
    sm = WF(-0.179, 0.0, zc)
    p.add(rbox((1.56, 0.24, 0.54), (0, -0.055, zc), 0.06, 1), lambda c, n: "green" if n.y < -0.6 else "dteal")
    p.add(decal(rect(-0.64, -0.44, -0.18, 0.18), sm, 0.0), "white")
    p.add(decal(rect(-0.6, -0.48, -0.14, 0.14), sm, 0.003), "green")
    p.add(decal(circ(-0.12, 0.15, 0.055, 6), sm, 0.0), "white")
    for a, b, w in (((-0.14, 0.08), (-0.2, -0.04), 0.07), ((-0.2, -0.04), (-0.3, -0.17), 0.055), ((-0.2, -0.04), (-0.08, -0.1), 0.055),
                    ((-0.08, -0.1), (-0.06, -0.19), 0.05), ((-0.15, 0.05), (-0.27, 0.0), 0.045), ((-0.15, 0.05), (-0.04, 0.0), 0.045)):
        p.add(decal(stroke(a, b, w), sm, 0.0), "white")
    p.add(decal([(0.08, 0.0), (0.24, 0.13), (0.24, 0.05), (0.58, 0.05), (0.58, -0.05), (0.24, -0.05), (0.24, -0.13)], sm, 0.0), "white")
    return p


def p_techo():
    p = Piece("Techo", (13.4, 4.5, 3.5), 1800)
    L = 2.25

    def S(pts, sx):
        return [(sx * x, z) for x, z in pts]

    def aisle(c, n):
        return n.x * (1 if c.x > 0 else -1) < -0.5
    for sx in (-1, 1):
        bot = S([(4.1, 0.5), (4.1, 0.43), (4.125, 0.36), (4.18, 0.315), (4.26, 0.3), (6.7, 0.3), (6.7, 0.5)], sx)
        p.add(xzprism(bot, -L, L), lambda c, n: "slate" if n.z > 0.9 and c.z > 0.45 else "cream")
        top = S([(4.24, 2.9), (6.7, 2.9), (6.7, 3.1), (4.1, 3.1), (4.1, 2.98), (4.115, 2.94), (4.16, 2.91)], sx)
        p.add(xzprism(top, -L, L), lambda c, n: "slate" if n.z < -0.9 and c.z < 2.95 else "cream")
        xa, xb = sorted((sx * 6.55, sx * 6.7))
        p.add(bb(xa, xb, -L, L, 0.5, 2.9), lambda c, n: "slate" if aisle(c, n) else "cream")
        for sy in (-1, 1):
            xa, xb = sorted((sx * 4.1, sx * 6.55))
            ya, yb = sorted((sy * 2.15, sy * L))
            p.add(bb(xa, xb, ya, yb, 0.5, 2.9), lambda c, n: "slate" if n.y * (1 if c.y > 0 else -1) < -0.5 else "cream")
        psu = S([(4.75, 0.31), (4.75, 0.17), (4.84, 0.08), (5.96, 0.08), (6.05, 0.17), (6.05, 0.31)], sx)
        p.add(xzprism(psu, -1.9, 1.9, 0.04), "cream2")
        for y in (-0.8, 0.8):
            for x in (5.0, 5.8):
                p.add(rev(lathe([(0.13, 0.081), (0.11, 0.03), (0.0, 0.0)], 8, M((sx * x, y, 0)), cap0=False)), "light")
            p.add(decal(circ(sx * 5.4, y, 0.065, 6), DOWN(0.075)), "orange")
        p.add(decal(rect(-0.3, 0.3, -0.04, 0.04), DOWN(0.075, sx * 5.4, 0.0)), "slate")
        lt = S([(2.35, 3.36), (2.35, 3.285), (2.38, 3.265), (2.82, 3.235), (2.85, 3.25), (2.85, 3.36)], sx)
        p.add(xzprism(lt, -L, L), "light")
    R = [(4.1, 3.1), (3.9, 3.155), (3.5, 3.21), (2.9, 3.26), (2.3, 3.3), (1.6, 3.33), (1.3, 3.335), (1.22, 3.3),
         (1.17, 3.17), (1.12, 3.06), (1.04, 2.99), (0.94, 2.96)]
    poly = [(6.7, 3.5), (6.7, 3.1)] + R + [(0.0, 2.96)] + [(-x, z) for x, z in reversed(R)] + [(-6.7, 3.1), (-6.7, 3.5)]

    def vrole(c, n):
        ax = abs(c.x)
        if 1.1 < ax < 1.25 and c.z < 3.32 and abs(n.x) > 0.4:
            return "teal"
        if ax < 1.0 and c.z < 2.99:
            return "white"
        return "cream"
    p.add(xzprism(poly, -L, L, 0.03), vrole)
    pod = [(-0.75, 2.97), (-0.71, 2.92), (-0.43, 2.66), (-0.36, 2.62), (0.36, 2.62), (0.43, 2.66), (0.71, 2.92), (0.75, 2.97)]
    p.add(yprism(pod, -0.9, 0.9, 0.035), "lmetal")
    for x in (-0.62, -0.22, 0.22, 0.62):
        p.add(rev(lathe([(0.11, 2.63), (0.11, 2.6), (0.065, 2.57), (0.0, 2.53)], 8, M((x, 0, 0)), cap0=False)),
              lambda c, n: "dark" if c.z > 2.585 else "metal")
    for sy in (-1, 1):
        A, B = Vector((0, sy * 0.71, 2.92)), Vector((0, sy * 0.43, 2.66))
        ey = (A - B).normalized()
        sm = frame((A + B) / 2, (sy, 0, 0), ey)
        if sm.col[2].y * sy < 0:
            sm = frame((A + B) / 2, (-sy, 0, 0), ey)
        p.add(decal(rr_pts(0.64, 0.25, 0.06, 2), sm, 0.004), "navy")
        p.add(decal(rect(-0.22, -0.05, -0.025, 0.025), sm, 0.008), "cream")
        p.add(decal(rect(0.05, 0.22, -0.025, 0.025), sm, 0.008), "cream")
        p.add(decal(rr_pts(0.11, 0.09, 0.02, 1), sm, 0.008), "orange")
        p.add(decal(rect(-0.022, 0.022, -0.018, 0.018), sm, 0.012), "navy")
    return p


def p_puerta_altillo():
    p = Piece("PuertaAltillo", (4.3, 0.15, 2.4), 250)
    H = 2.4

    def bow(z):
        t = max(0.0, min(1.0, z / H))
        return math.sin(math.pi * t ** 0.8)

    def yf(z):
        return -0.005 - 0.05 * bow(z)
    zs = [0.0, 0.05, 0.16, 0.45, 0.8, 1.15, 1.5, 1.85, 2.15, 2.35, 2.4]
    front = []
    for z in zs:
        y = yf(z)
        if z == 0.0 or z == H:
            y += 0.03
        front.append((y, z))
    back = [(yf(z) + 0.08, z) for z in (H, 1.8, 1.2, 0.6, 0.0)]
    p.add(yprism(front + back, -2.15, 2.15, 0.025), lambda c, n: "orange" if c.z < 0.17 else "cream")
    z = 0.42
    dz = 0.01
    sl = (yf(z + dz) - yf(z - dz)) / (2 * dz)
    ey = Vector((0, sl, 1)).normalized()
    hm = frame((0, yf(z), z), (1, 0, 0), ey)
    p.add(decal(rr_pts(1.0, 0.18, 0.08, 2), hm @ M((0, -0.07, 0)), 0.004), "slate")
    p.add(bb(-0.45, 0.45, -0.075, yf(0.46) + 0.012, 0.4, 0.5, 0.014), "lmetal")
    return p


def p_cocina():
    p = Piece("CocinaModulo", (7.4, 2.6, 10.0), 1800)
    p.add(bb(-3.7, -3.55, -1.2, 1.3, 0.0, 3.35, 0.03), "cream")
    p.add(bb(3.55, 3.7, -1.2, 1.3, 0.0, 3.35, 0.03), "cream")
    p.add(bb(-3.55, -1.75, 1.1, 1.3, 0.0, 3.35), "slate")
    p.add(bb(-1.75, -1.6, -1.2, 1.3, 0.0, 3.35, 0.03), "cream")
    p.add(bb(-1.6, 3.55, -1.15, 1.3, 0.25, 3.35), "cream")
    p.add(bb(-1.6, 3.55, -1.0, 1.3, 0.0, 0.25), "dark")
    for x0, x1 in ((-3.55, -3.5), (-1.8, -1.75)):
        p.add(bb(x0, x1, -1.05, 0.95, 0.45, 0.62), "orange")
        p.add(bb(x0, x1, -1.05, 0.95, 1.35, 1.52), "orange")
    p.add(rbox((0.34, 0.1, 0.16), (-2.65, -1.12, 3.2), 0.04, 1), "orange")
    for z in (1.1, 2.52):
        p.add(rbox((2.25, 0.08, 1.3), (-0.375, -1.17, z), 0.045, 1), "lmetal")
        om = WF(-1.214, -0.375, z)
        p.add(decal(rr_pts(1.5, 0.62, 0.12, 2), om, 0.0), "dark")
        p.add(decal(rr_pts(1.3, 0.1, 0.05, 1), om @ M((0, 0.06, 0)), 0.003), "slate")
        p.add(bar((-1.25, -1.24, z + 0.46), (0.5, -1.24, z + 0.46), 0.07, 0.06, 0.018), "dark")
        p.add(decal(circ(0.72, -0.48, 0.055, 6), om, 0.0), "orange")
        p.add(decal(circ(0.72, -0.3, 0.055, 6), om, 0.0), "teal")
    for z in (0.86, 1.84, 2.82):
        p.add(rbox((2.45, 0.08, 0.88), (2.225, -1.17, z), 0.045, 1), "teal")
        p.add(bar((1.8, -1.25, z + 0.26), (2.65, -1.25, z + 0.26), 0.075, 0.05, 0.018), "orange")
    p.add(bb(-3.7, 3.7, -1.3, 1.3, 3.35, 3.5, 0.035, 2), "metal")
    p.add(bb(-3.65, 3.65, 1.15, 1.3, 3.5, 6.0), "cream2")
    bm_ = WF(1.146)
    p.add(decal(rect(-3.65, 3.65, 4.3, 4.48), bm_), "teal")
    p.add(decal(rr_pts(0.62, 0.36, 0.06, 1), bm_ @ M((2.8, 3.9, 0))), "dark")
    for u in (2.65, 2.95):
        p.add(decal(circ(u, 3.9, 0.06, 6), bm_, 0.003), "orange")
    p.add(bar((-3.1, 1.1, 5.35), (-0.7, 1.1, 5.35), 0.05, 0.05, 0.012), "metal")
    p.add(bb(-3.7, 3.7, -0.15, 1.3, 6.0, 9.6), "cream")
    for x in (-2.7375, -0.9125, 0.9125, 2.7375):
        p.add(rbox((1.77, 0.06, 3.44), (x, -0.18, 7.8), 0.04, 1), "white")
        p.add(bar((x - 0.42, -0.24, 6.36), (x + 0.42, -0.24, 6.36), 0.08, 0.06, 0.018), "orange")
    p.add(decal(rect(-3.55, 3.55, -0.12, 0.12), DOWN(5.995)), "light")
    p.add(bb(-3.7, 3.7, -0.3, 1.3, 9.6, 10.0, 0.03), "cream")
    p.add(decal(rect(-3.68, 3.68, 9.73, 9.83), WF(-0.305)), "orange")
    return p


def door_path(hw, H, r, cs=4):
    path = [(-hw, 0.0), (-hw, H - r)]
    for k in range(1, cs):
        a = math.radians(180 - 90 * k / cs)
        path.append((-hw + r + r * math.cos(a), H - r + r * math.sin(a)))
    path += [(-hw + r, H), (hw - r, H)]
    for k in range(1, cs):
        a = math.radians(90 - 90 * k / cs)
        path.append((hw - r + r * math.cos(a), H - r + r * math.sin(a)))
    path += [(hw, H - r), (hw, 0.0)]
    return path


def u_outline(W, Z, hw, H, r, cs=4, grow=0.02):
    hole = door_path(hw + grow, H + grow, r + grow, cs)
    return [(-W, 0.0)] + hole + [(W, 0.0), (W, Z), (-W, Z)]


def logo(p, m, w0=0.0, s=1.0):
    p.add(decal(circ(0.0, 0.0, 0.42 * s, 14), m, w0), "orange")
    p.add(arc_strip(0.0, 0.0, 0.42 * s, 0.5 * s, 0, 360, 14, m, w0), "cream")
    pl = [(0.3, 0.12), (-0.26, 0.26), (-0.1, 0.06), (-0.2, -0.16), (-0.02, -0.02)]
    p.add(decal([(x * s, y * s) for x, y in pl], m, w0 + 0.004), "cream")
    p.add(arc_strip(-0.06 * s, -0.12 * s, 0.17 * s, 0.22 * s, 200, 320, 5, m, w0 + 0.004), "teal")


def bulkhead(name, hw, curtain, metal_back):
    p = Piece(name, (13.4, 0.6, 10.0), 900)
    W, H, r = 6.7, 7.5, 0.5
    back = "steel" if metal_back else "cream"
    p.add(prism(u_outline(W, 10.0, hw, H, r), 0.4, M((0, 0, 0), (90, 0, 0))), by_normal("cream", back, "cream"))
    tp = [(0.3, -0.2), (0.27, -0.29), (0.05, -0.3), (0.0, -0.25), (0.0, 0.25), (0.05, 0.3), (0.27, 0.29), (0.3, 0.2)]
    p.add(sweep(door_path(hw, H, r), tp, WF(0.0)), by_normal("white", "dark" if metal_back else "white", "white"), 40)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * W, sx * (hw + 0.27)))
        p.add(bb(x0, x1, -0.22, 0.22, 0.0, 0.5), by_normal("sand", "dark" if metal_back else "sand", "sand"))
        rail = [(0.15, 3.22), (0.23, 3.22), (0.27, 3.27), (0.28, 3.37), (0.27, 3.48), (0.23, 3.53), (0.15, 3.53)]
        p.add(yprism([(-y, z) for y, z in rail], x0, x1), "teal")
        if not metal_back:
            p.add(yprism(rail, x0, x1), "teal")
        else:
            for z in (3.3, 6.6):
                p.add(bb(x0, x1, 0.18, 0.27, z - 0.12, z + 0.12, 0.02), "steel")
            hm = WB(0.205, sx * (hw + 0.75), 0.0)
            p.add(decal(rect(-0.42, 0.42, 0.55, 2.1), hm), "yellow")
            for k in range(4):
                z0 = 0.62 + 0.38 * k
                p.add(decal([(-0.42, z0), (-0.42, z0 + 0.17), (0.42, z0 + 0.41), (0.42, z0 + 0.24)], hm, 0.003), "black")
    for side in (-1, 1):
        y = side * 0.235
        p.add(rbox((2.3, 0.07, 1.15), (0, y, 8.75), 0.05, 1), "dteal" if (metal_back and side > 0) else "teal")
        m = (WF(-0.274, 0.0, 8.75) if side < 0 else WB(0.274, 0.0, 8.75))
        logo(p, m)
    if curtain:
        p.add(bar((-hw + 0.02, 0.0, 7.36), (hw - 0.02, 0.0, 7.36), 0.06, 0.06, 0.0), "metal")
        zs = [7.3, 6.7, 5.9, 5.1, 4.62, 4.3, 3.4, 2.2, 1.0, 0.45]
        ws = [1.05, 0.95, 0.72, 0.46, 0.3, 0.34, 0.5, 0.62, 0.7, 0.72]
        C = 7
        x_j = -hw + 0.06
        rows_f, rows_b = [], []
        for z, w in zip(zs, ws):
            dz = max(0.0, z - (H - r))
            xe = -hw + (r - math.sqrt(max(r * r - dz * dz, 0.0))) if dz > 0 else -hw
            x0 = max(x_j, xe + 0.04)
            amp = 0.05 + 0.06 * (w / 1.05)
            rf, rb = [], []
            for j in range(C):
                u = j / (C - 1)
                x = x0 + w * u
                wave = amp * math.sin(u * math.pi * 3.0)
                th = 0.022 * math.sin(math.pi * u) if 0 < j < C - 1 else 0.0
                rf.append((x, wave - th, z))
                rb.append((x, wave + th, z))
            rows_f.append(rf)
            rows_b.append(rb)
        bmc = bmesh.new()
        Vf = [[bmc.verts.new(q) for q in row] for row in rows_f]
        Vb = []
        for i, row in enumerate(rows_b):
            vr = []
            for j, q in enumerate(row):
                vr.append(Vf[i][j] if j in (0, C - 1) else bmc.verts.new(q))
            Vb.append(vr)
        R = len(zs)
        for i in range(R - 1):
            for j in range(C - 1):
                bmc.faces.new((Vf[i][j], Vf[i][j + 1], Vf[i + 1][j + 1], Vf[i + 1][j]))
                bmc.faces.new((Vb[i][j], Vb[i + 1][j], Vb[i + 1][j + 1], Vb[i][j + 1]))
        for i in (0, R - 1):
            for j in range(1, C - 2):
                if i == 0:
                    bmc.faces.new((Vf[i][j], Vb[i][j], Vb[i][j + 1], Vf[i][j + 1]))
                else:
                    bmc.faces.new((Vf[i][j], Vf[i][j + 1], Vb[i][j + 1], Vb[i][j]))
        bmesh.ops.recalc_face_normals(bmc, faces=bmc.faces)
        p.add(bmc, "dteal", 70)
        tx = x_j + 0.15
        p.add(rbox((0.4, 0.3, 0.13), (tx + 0.02, 0.0, 4.62), 0.05, 1), "orange")
    return p


def p_mampara_cabina():
    return bulkhead("MamparaCabina", 2.0, True, False)


def p_mampara_bodega():
    return bulkhead("MamparaBodega", 2.5, False, True)


def toilet(p, x, y):
    by, sy = y, 1.12
    bowl = [(0.3, 0.0), (0.36, 0.05), (0.37, 0.3), (0.47, 0.58), (0.52, 0.76), (0.4, 0.76), (0.26, 0.56), (0.0, 0.52)]
    p.add(lathe(bowl, 12, M((x, by, 0)), sy=sy, cap1=False),
          lambda c, n: "glass" if 0.45 < c.z < 0.62 and ((c.x - x) ** 2 + ((c.y - by) / sy) ** 2) < 0.28 ** 2 else "white")
    p.add(lathe([(0.38, 0.76), (0.54, 0.76), (0.54, 0.82), (0.39, 0.82)], 12, M((x, by, 0)), sy=sy, closed=True), "teal")
    hy = by + 0.54 * sy
    lid = lathe([(0.53, 0.0), (0.54, 0.03), (0.0, 0.05)], 12, None, sy=sy)
    xf(lid, Matrix.Translation((x, hy, 0.82)) @ Matrix.Rotation(math.radians(-100), 4, "X") @ Matrix.Translation((0, -0.54 * sy, 0)))
    p.add(lid, "teal")
    p.add(bb(x - 0.26, x + 0.26, by + 0.15, by + 0.7, 0.0, 0.76, 0.04), "white")
    p.add(rbox((1.2, 0.42, 1.1), (x, 1.43, 1.35), 0.08, 1), "white")
    p.add(rbox((1.28, 0.5, 0.1), (x, 1.43, 1.93), 0.04, 1), "white")
    p.add(cyl(0.09, 0.04, (x, 1.43, 1.98), seg=8, cap0=False), "red")


def p_bano():
    p = Piece("Bano", (5.0, 3.7, 10.0), 1800)
    W, D = 2.5, 1.85
    hw, H = 1.2, 7.0
    fy0, fy1 = -1.75, -1.55
    inside = by_normal("cream", "white", "cream")
    fr = plate(u_outline(W, 10.0, hw, H, 0.2, 2), [], 0.2, frame((0, fy1, 0), (1, 0, 0), (0, 0, 1)))
    bevel_where(fr, lambda e: all(abs(abs(v.co.x) - W) < 1e-4 for v in e.verts), 0.03)
    p.add(fr, inside)
    p.add(bb(-W, W, 1.65, D, 0.0, 10.0, 0.03), by_normal("white", "cream", "cream"))
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 2.3, sx * W))
        p.add(bb(x0, x1, fy1, 1.65, 0.0, 10.0, 0.03), lambda c, n: "white" if n.x * (1 if c.x > 0 else -1) < -0.5 else "cream")
    tp = [(0.2, -0.1), (0.17, -0.13), (0.03, -0.13), (0.0, -0.1), (0.0, 0.16), (0.04, 0.2), (0.2, 0.2), (0.25, 0.17), (0.27, 0.1)]
    p.add(sweep(door_path(hw, H, 0.2, 2), tp, WF(-1.65)), lambda c, n: "white" if n.y > 0.4 else "teal", 40)
    sm = WF(-1.8105, 0.0, 7.95)
    p.add(rbox((1.3, 0.11, 0.8), (0, -1.75, 7.95), 0.05, 1), "teal")
    for cxx in (-0.28, 0.28):
        p.add(decal(circ(cxx, 0.21, 0.075, 8), sm), "white")
    p.add(decal(rr_pts(0.18, 0.24, 0.05, 1), sm @ M((-0.28, 0.0, 0))), "white")
    p.add(decal(rect(-0.35, -0.3, -0.3, -0.08), sm), "white")
    p.add(decal(rect(-0.26, -0.21, -0.3, -0.08), sm), "white")
    p.add(decal([(0.16, -0.16), (0.4, -0.16), (0.33, 0.12), (0.23, 0.12)], sm), "white")
    p.add(decal(rect(0.22, 0.26, -0.3, -0.15), sm), "white")
    p.add(decal(rect(0.3, 0.34, -0.3, -0.15), sm), "white")
    p.add(decal(rect(-0.015, 0.015, -0.3, 0.32), sm), "lteal")
    toilet(p, -1.05, 0.62)
    p.add(bb(0.6, 2.3, 0.4, 1.65, 0.0, 2.9, 0.04), "cream2")
    p.add(decal(rect(0.75, 2.15, 0.25, 2.65), WF(0.395)), "white")
    p.add(bar((1.2, 0.36, 2.35), (1.7, 0.36, 2.35), 0.06, 0.05, 0.015), "metal")
    p.add(bb(0.55, 2.3, 0.33, 1.65, 2.9, 3.05, 0.03), "white")
    sink = [(0.22, 3.05), (0.33, 3.12), (0.37, 3.3), (0.33, 3.3), (0.29, 3.15), (0.0, 3.12)]
    p.add(lathe(sink, 12, M((1.45, 0.98, 0)), sy=0.85, cap1=False), "teal")
    p.add(decal(circ(1.45, 0.98, 0.05, 6), UP(3.126)), "metal")
    p.add(tube([(1.45, 1.6, 3.05), (1.45, 1.6, 3.6), (1.45, 1.42, 3.75), (1.45, 1.26, 3.58)], lambda u: 0.045, k=5, steps=2, caps=False), "metal", 70)
    p.add(rbox((1.6, 0.06, 2.0), (1.45, 1.62, 5.0), 0.04, 1), "white")
    mm = WF(1.586, 1.45, 5.0)
    p.add(decal(rr_pts(1.4, 1.8, 0.12, 2), mm), "mirror")
    p.add(decal(stroke((-0.5, 0.2), (-0.05, 0.75), 0.09), mm, 0.003), "white")
    p.add(decal(stroke((-0.3, -0.05), (0.15, 0.5), 0.05), mm, 0.003), "white")
    p.add(rbox((0.14, 0.8, 0.9), (2.23, -0.25, 4.3), 0.04, 1), "lmetal")
    p.add(decal(rect(-0.25, 0.25, -0.03, 0.03), frame((2.155, -0.25, 3.95), (0, -1, 0), (0, 0, 1))), "dark")
    p.add(cyl(0.12, 0.42, (-2.2, -0.3, 2.2), rot=(90, 0, 0), seg=8, center=True), "white")
    p.add(bar((-2.3, -0.3, 2.2), (-2.12, -0.3, 2.2), 0.05, 0.05), "metal")
    return p


def p_cabina_piloto():
    p = Piece("CabinaPiloto", (11.6, 10.5, 8.0), 2400)
    W, L = 5.8, 5.25
    yf = -4.95
    hole = offset_pts(rr_pts(11.04, 4.04, 0.32, 3), 0.0, 5.5)
    p.add(plate(rect(-W, W, 0.0, 8.0), [hole], 0.3, WB(-L)), by_normal("dark", "cream2", "cream2"))
    path = cw(offset_pts(rr_pts(11.0, 4.0, 0.3, 3), 0.0, 5.5))
    p.add(sweep(path, [(0.05, -0.3), (0.0, -0.3), (0.0, 0.16), (0.04, 0.2), (0.22, 0.2), (0.3, 0.12), (0.3, 0.0)], WB(yf), closed=True), "dark", 40)
    p.add(rbox((0.36, 0.3, 4.1), (0, yf + 0.17, 5.5), 0.06, 1), "dark")
    for sx in (-1, 1):
        p.add(rbox((2.1, 0.05, 0.62), (sx * 2.75, yf + 0.33, 7.12), 0.02, 1, rot=(-28, 0, 0)), "slate")
        Fin = frame((sx * 5.5, 0, 0), (0, -sx, 0), (0, 0, 1))

        def loc(y, z):
            return (-sx * y, z)
        outer = [loc(-4.95, 0.0), loc(L, 0.0), loc(L, 6.6), loc(-4.75, 6.6), loc(-4.75, 3.2), loc(-4.95, 3.2)]
        wins = [(-3.6, 5.05, 2.0, 1.6, 0.3), (-1.55, 5.1, 1.35, 1.4, 0.3)]
        holes = []
        for cy_, cz_, ww, hh, rr in wins:
            holes.append([loc(cy_ + u, cz_ + v) for u, v in rr_pts(ww + 0.04, hh + 0.04, rr + 0.02, 2)])
        p.add(plate(outer, holes, 0.3, Fin, z0=-0.3), lambda c, n: "cream2")
        for cy_, cz_, ww, hh, rr in wins:
            wp = cw([loc(cy_ + u, cz_ + v) for u, v in rr_pts(ww, hh, rr, 2)])
            p.add(sweep(wp, [(0.04, -0.3), (0.0, -0.3), (0.0, 0.07), (0.03, 0.1), (0.1, 0.1), (0.14, 0.0)], Fin, closed=True), "slate", 40)
        xa, xb = sorted((sx * 5.48, sx * 5.5))
        p.add(bb(xa, xb, -4.75, L, 0.0, 3.3), "sand")
        xa, xb = sorted((sx * 5.36, sx * 5.5))
        p.add(bb(xa, xb, -4.75, L, 3.28, 3.5, 0.04), "teal")
        p.add(decal(rr_pts(0.9, 0.5, 0.1, 1), Fin @ M((-sx * 3.2, 2.4, 0.025))), "dark")
        p.add(bar((sx * 5.42, -4.2, 6.42), (sx * 5.42, -2.9, 6.42), 0.1, 0.12, 0.03), "orange")
    inner = [(5.5, 6.6), (5.42, 7.0), (5.15, 7.4), (4.75, 7.65), (4.4, 7.7)]
    poly = [(W, 6.6), (W, 8.0), (-W, 8.0), (-W, 6.6)] + [(-x, z) for x, z in inner] + [(x, z) for x, z in reversed(inner)]
    p.add(xzprism(poly, yf, L), "cream2")
    p.add(rev(lathe([(0.55, 7.7), (0.52, 7.64), (0.0, 7.6)], 12, M((0, 0.8, 0)), cap0=False)), "light")
    for y in (-1.9, 3.3):
        p.add(bb(-4.45, 4.45, y - 0.13, y + 0.13, 7.62, 7.71, 0.03), "lmetal")
    panel = [(-4.92, 7.72), (-2.45, 7.72), (-2.6, 7.48), (-4.92, 6.92)]
    p.add(yprism(panel, -2.3, 2.3, 0.04), "dark")
    A, B = Vector((0, -2.6, 7.48)), Vector((0, -4.92, 6.92))
    ey = (A - B).normalized()
    PM = frame(B, (1, 0, 0), ey)
    if PM.col[2].z > 0:
        PM = frame(B, (-1, 0, 0), ey)
    Lp = (A - B).length
    p.add(decal(rect(-2.15, 2.15, 0.12, Lp - 0.12), PM, 0.004), "navy")
    cols = ("cream", "cream", "orange", "cream", "teal", "cream", "cream")
    for row, v in enumerate((0.55, 1.15, 1.75)):
        for i in range(7):
            u = -1.8 + 0.6 * i
            if row < 2:
                p.add(decal(rect(u - 0.12, u + 0.12, v - 0.14, v + 0.14), PM, 0.008), "slate")
                tip = PM @ Vector((u, v + 0.05, 0.2))
                base = PM @ Vector((u, v - 0.02, 0.0))
                p.add(bar(base, tip, 0.07, 0.07, 0.0), cols[(i + row * 3) % 7])
            else:
                p.add(decal(rect(u - 0.16, u + 0.16, v - 0.1, v + 0.1), PM, 0.008), ("red", "gold", "teal", "orange", "lettuce", "gold", "red")[i])
    for i, col in enumerate(("lettuce", "red", "gold", "lettuce")):
        p.add(decal(circ(-0.9 + 0.6 * i, 2.15, 0.07, 6), PM, 0.008), col)
    return p


def p_puerta(name, Wd):
    p = Piece(name, (Wd, 0.3, 6.5), 300)
    hw, H, r = Wd / 2, 6.5, 0.3
    out = [(hw, 0.0)] + list(reversed(door_path(hw, H, r, 3)))[1:-1] + [(-hw, 0.0)]
    slab = prism(out, 0.22, M((0, 0, 0), (90, 0, 0)))
    bevel_sharp_simple(slab, 0.05)
    p.add(slab, lambda c, n: "cream" if abs(n.y) > 0.92 else "orange")
    wz = 4.85
    wpts = rr_pts(0.95, 1.3, 0.42, 2)
    p.add(sweep(cw(offset_pts(wpts, 0, wz)), [(0.0, -0.02), (0.0, 0.03), (0.06, 0.04), (0.17, 0.0)], WF(-0.11)), "white", 40)
    p.add(decal(wpts, WF(-0.114, 0.0, wz)), "glass")
    p.add(decal(wpts, WB(0.114, 0.0, wz)), "glass")
    p.add(decal(stroke((-0.25, -0.25), (0.15, 0.35), 0.07), WF(-0.117, 0.0, wz)), "white")
    hz = 3.3
    hx = hw - 0.55
    p.add(decal(rr_pts(0.5, 0.42, 0.1, 1), WF(-0.114, hx, hz)), "dark")
    p.add(rbox((0.62, 0.09, 0.14), (hx - 0.12, -0.105, hz), 0.035, 1, rot=(0, -12, 0)), "red")
    p.add(bar((hx - 0.25, 0.11, hz - 0.3), (hx - 0.25, 0.11, hz + 0.3), 0.08, 0.08, 0.0, up=(0, 1, 0)), "dark")
    p.add(bar((hx - 0.25, 0.13, hz - 0.25), (hx - 0.25, 0.13, hz + 0.25), 0.07, 0.04, 0.0, up=(0, 1, 0)), "dark")
    p.add(decal(rect(-hw + 0.25, hw - 0.25, 1.4, 1.52), WF(-0.114)), "orange")
    return p


def bevel_sharp_simple(bm, off, seg=1, ang=50):
    bm.normal_update()
    es = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(ang)]
    return bevel_edges(bm, es, off, seg)


def p_puerta_ala():
    return p_puerta("PuertaAla", 3.4)


def p_puerta_salida():
    return p_puerta("PuertaSalida", 3.0)


def p_puerta_bano():
    p = Piece("PuertaBano", (2.4, 0.15, 7.0), 300)
    slab = bb(-1.2, 1.2, -0.045, 0.045, 0.0, 7.0)
    bevel_sharp_simple(slab, 0.025)
    p.add(slab, "cream")
    for z0, z1 in ((4.0, 6.6), (1.5, 3.0)):
        p.add(rbox((1.8, 0.03, z1 - z0), (0, -0.05, (z0 + z1) / 2), 0.012, 1), "cream2")
    for k in range(4):
        z = 0.45 + 0.16 * k
        p.add(decal(rr_pts(1.4, 0.07, 0.035, 1), WF(-0.049, 0.0, z)), "slate")
    hx, hz = 0.85, 3.45
    for side in (-1, 1):
        y = side * 0.045
        p.add(cyl(0.08, 0.03, (hx, y, hz), rot=(-90 * side, 0, 0), seg=8), "metal")
        p.add(bar((hx, side * 0.06, hz), (hx - 0.32, side * 0.06, hz), 0.07, 0.03, 0.01, up=(0, 1, 0)), "metal")
    im = WF(-0.046, hx - 0.05, hz + 0.42)
    p.add(rbox((0.34, 0.02, 0.15), (hx - 0.05, -0.052, hz + 0.42), 0.0), "dark")
    p.add(decal(rect(-0.13, 0.0, -0.045, 0.045), WF(-0.065, hx - 0.05, hz + 0.42)), "red")
    p.add(decal(rect(0.02, 0.13, -0.045, 0.045), WF(-0.065, hx - 0.05, hz + 0.42)), "slate")
    return p


def strap(p0, p1, w, t, front=(0, -1, 0)):
    a, b = Vector(p0), Vector(p1)
    d = (b - a).normalized()
    f = Vector(front).normalized()
    sd = d.cross(f).normalized() * (w / 2)
    bk = -f * t
    bm = bmesh.new()
    A0, B0, B1, A1 = [bm.verts.new(q) for q in (a - sd, b - sd, b + sd, a + sd)]
    A0b, B0b, B1b, A1b = [bm.verts.new(q) for q in (a - sd + bk, b - sd + bk, b + sd + bk, a + sd + bk)]
    bm.faces.new((A1, B1, B0, A0))
    bm.faces.new((A1, A1b, B1b, B1))
    bm.faces.new((A0, B0, B0b, A0b))
    return bm


def clip_seg(p, d, x0, x1, y0, y1):
    t0, t1 = -1e9, 1e9
    for pc, dc, lo, hi in ((p[0], d[0], x0, x1), (p[1], d[1], y0, y1)):
        if abs(dc) < 1e-9:
            if pc < lo or pc > hi:
                return None
        else:
            ta, tb = (lo - pc) / dc, (hi - pc) / dc
            if ta > tb:
                ta, tb = tb, ta
            t0, t1 = max(t0, ta), min(t1, tb)
    if t1 - t0 < 1e-6:
        return None
    return (p[0] + d[0] * t0, p[1] + d[1] * t0), (p[0] + d[0] * t1, p[1] + d[1] * t1)


def p_bodega_pared():
    p = Piece("BodegaPared", (22.0, 0.7, 10.0), 1800)
    W = 11.0

    def ywall(z):
        if z <= 6.5:
            return 0.1
        s_ = (z - 6.5) / 3.5
        return 0.1 - 0.2 * s_ * s_
    curve = [(ywall(6.5 + 3.5 * k / 4), 6.5 + 3.5 * k / 4) for k in range(1, 5)]
    skin = [(0.35, 0.0), (0.1, 0.0), (0.1, 6.5)] + curve + [(0.35, 10.0)]
    p.add(yprism(skin, -W, W), "hold")
    p.add(yprism([(0.12, 0.0), (0.05, 0.0), (0.05, 0.55), (0.12, 0.6)], -W, W), "steel")
    for zc in (1.6, 2.9):
        p.add(yprism([(0.12, zc - 0.22), (0.04, zc - 0.22), (0.02, zc - 0.19), (0.02, zc + 0.19), (0.04, zc + 0.22), (0.12, zc + 0.22)], -W, W), "wood")
    for zc, h in ((0.42, 0.18), (4.45, 0.2)):
        p.add(yprism([(0.12, zc - h), (-0.04, zc - h), (-0.07, zc - h + 0.04), (-0.07, zc + h - 0.04), (-0.04, zc + h), (0.12, zc + h)], -W, W), "dark")
        for i in range(20):
            x = -W + 0.55 + 1.1 * i
            p.add(decal(rect(-0.11, 0.11, -0.035, 0.035), WF(-0.074, x, zc)), "black")
    ribs = [-9.9 + 2.2 * i for i in range(10)]
    path = [(0.1, 0.0), (0.1, 6.5)] + curve
    for x in ribs:
        rows = [[(x - 0.17, y + 0.02, z), (x - 0.17, y - 0.2, z), (x - 0.12, y - 0.25, z), (x + 0.12, y - 0.25, z), (x + 0.17, y - 0.2, z), (x + 0.17, y + 0.02, z)] for y, z in path]
        bmr, V = grid_solid(rows)
        bmr.faces.new(V[-1])
        bmesh.ops.recalc_face_normals(bmr, faces=bmr.faces)
        p.add(bmr, "steel", 40)
        for z in (1.2, 3.1, 5.6):
            p.add(decal(rect(-0.04, 0.04, -0.04, 0.04), WF(-0.154, x, z)), "metal")
    z0, z1 = 4.62, 9.3
    yb, yt = ywall(z0) - 0.1, ywall(z1) - 0.1

    def P3(u, v):
        return (u, yb + (yt - yb) * (v - z0) / (z1 - z0), v)
    for i in range(len(ribs) + 1):
        xa = -W + 0.05 if i == 0 else ribs[i - 1] + 0.17
        xb = W - 0.05 if i == len(ribs) else ribs[i] - 0.17
        for v, w in ((z0 + 0.05, 0.1), (z1 - 0.05, 0.1)):
            p.add(strap(P3(xa, v), P3(xb, v), w, 0.04), "orange", 70)
        a_ = 2.3
        H = z1 - z0
        for k in (-1, 1):
            d = (k / a_, 1.0)
            c = xa - H / a_
            while c < xb + H / a_:
                seg = clip_seg((c, z0), d, xa, xb, z0, z1)
                c += 0.7
                if not seg:
                    continue
                (u0, v0), (u1, v1) = seg
                if math.hypot(u1 - u0, v1 - v0) < 0.35:
                    continue
                p.add(strap(P3(u0, v0), P3(u1, v1), 0.06, 0.03), "orange", 70)
    return p


def p_torreta():
    p = Piece("Torreta", (3.0, 4.0, 1.2), 700)
    p.add(rr_loft(3.0, 4.0, 0.62, 3, [(0.04, 0.0), (0.0, 0.04), (0.0, 0.11), (0.04, 0.15)]),
          lambda c, n: "yellow" if abs(n.z) < 0.6 else "steel")
    for a in range(6):
        ang = math.radians(30 + 60 * a)
        p.add(cyl(0.08, 0.05, (1.15 * math.cos(ang) * 1.05, 1.62 * math.sin(ang), 0.15), seg=6, cap0=False), "metal")
    prof = [(1.18, 0.15), (1.22, 0.2), (1.22, 0.42), (1.08, 0.55), (0.78, 0.62), (0.7, 0.84), (0.92, 0.88), (0.98, 0.94), (0.94, 1.0), (0.0, 1.0)]
    p.add(lathe(prof, 14, cap0=False), lambda c, n: "orange" if c.z < 0.45 and n.z < 0.8 else ("steel" if c.z > 0.86 else "dark"))
    p.add(cyl(0.09, 0.84, (0, 1.66, 0.15), seg=8, cap0=False), "steel")
    p.add(bar((0, 0.75, 0.62), (0, 1.62, 0.9), 0.14, 0.1, 0.03), "steel")
    p.add(bb(-0.36, 0.36, 1.38, 1.95, 0.94, 1.02, 0.02), "dark")
    p.add(rbox((0.86, 0.62, 0.18), (0, 1.66, 1.11), 0.07, 2), "teal")
    return p


def p_torreta_canones():
    p = Piece("TorretaCanones", (3.0, 3.2, 2.2), 1300)
    p.add(lathe([(0.95, 0.0), (1.22, 0.0), (1.25, 0.04), (1.25, 0.21), (1.22, 0.25), (0.95, 0.25)], 14, closed=True), "teal")
    p.add(lathe([(1.0, 0.18), (1.0, 0.3), (0.0, 0.3)], 14, cap0=False), "dark")
    for sx in (-1, 1):
        p.add(rbox((0.14, 0.9, 0.95), (sx * 0.58, 0.2, 0.76), 0.04, 1), "steel")
    p.add(rbox((0.9, 1.1, 0.46), (0, 0.15, 1.25), 0.08, 1), "dark")
    p.add(rbox((0.5, 0.5, 0.16), (0, 0.25, 1.52), 0.05, 1), "steel")
    cx, cy, R, t = 0.0, 1.6, 2.2, 0.11
    amax = 35.0
    n = 8
    zr = [0.25, 1.52, 1.74]
    bm = bmesh.new()
    outer, inner = [], []
    for i in range(n + 1):
        a = math.radians(-amax + 2 * amax * i / n)
        u = a / math.radians(amax)
        ztop = 2.2 - 0.3 * u * u
        zs = zr + [ztop - 0.07, ztop]
        oc, ic = [], []
        for k, z in enumerate(zs):
            ro = R - (0.035 if k == len(zs) - 1 else 0.0)
            ri = R - t + (0.035 if k == len(zs) - 1 else 0.0)
            oc.append(bm.verts.new((cx + ro * math.sin(a), cy - ro * math.cos(a), z)))
            ic.append(bm.verts.new((cx + ri * math.sin(a), cy - ri * math.cos(a), z)))
        outer.append(oc)
        inner.append(ic)
    K = len(zr) + 2
    for i in range(n):
        for k in range(K - 1):
            bm.faces.new((outer[i][k], outer[i + 1][k], outer[i + 1][k + 1], outer[i][k + 1]))
            bm.faces.new((inner[i][k], inner[i][k + 1], inner[i + 1][k + 1], inner[i + 1][k]))
        bm.faces.new((outer[i][K - 1], outer[i + 1][K - 1], inner[i + 1][K - 1], inner[i][K - 1]))
        bm.faces.new((outer[i][0], inner[i][0], inner[i + 1][0], outer[i + 1][0]))
    for i in (0, n):
        for k in range(K - 1):
            bm.faces.new((outer[i][k], outer[i][k + 1], inner[i][k + 1], inner[i][k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    def srole(c, n_):
        if 1.52 < c.z < 1.74 and math.hypot(c.x - cx, c.y - cy) > R - 0.05:
            return "cream"
        return "orange"
    p.add(bm, srole, 30)
    p.add(decal(rr_pts(0.6, 0.08, 0.04, 1), WF(cy - R - 0.006, 0.0, 2.0)), "black")
    for sx in (-1, 1):
        x = sx * 0.3
        p.add(lathe([(0.12, 0.0), (0.12, 0.86), (0.16, 0.9), (0.16, 1.18), (0.14, 1.22), (0.08, 1.25), (0.0, 1.24)], 10, M((x, -0.35, 1.25), (90, 0, 0)), cap0=False),
              lambda c, n_: "black" if c.y < -1.585 else ("orange" if c.y < -1.2 else "dark"))
        yy = cy - math.sqrt(R * R - x * x) - 0.015
        p.add(lathe([(0.21, 0.0), (0.23, 0.05), (0.2, 0.12), (0.12, 0.13)], 10, M((x, yy, 1.25), (90, 0, 0)), cap0=False), "dark")
        p.add(rbox((0.44, 0.8, 0.62), (sx * 1.28, 0.32, 0.62), 0.05, 1), lambda c, n_: "gold" if c.z > 0.9 else "dteal")
        p.add(tube([(sx * 1.2, 0.3, 0.92), (sx * 0.95, 0.22, 1.3), (sx * 0.46, 0.15, 1.33)], lambda u: 0.07, k=4, steps=2, caps=False, up=(0, 1, 0)), "gold", 70)
        p.add(bar((sx * 0.33, 0.7, 1.2), (sx * 0.33, 1.48, 1.2), 0.09, 0.09, 0.0), "steel")
        p.add(bar((sx * 0.33, 1.5, 0.95), (sx * 0.33, 1.5, 1.42), 0.2, 0.14, 0.035), "black")
    p.add(bar((-0.28, 1.45, 1.2), (0.28, 1.45, 1.2), 0.06, 0.06, 0.0), "red")
    return p


def p_mascarilla():
    p = Piece("Mascarilla", (0.4, 0.4, 1.4), 150)
    m = M((0, -0.05, 0.2), (-60, 0, 0))
    k = 0.34 / 0.27
    p.add(lathe([(0.0, 0.18 * k), (0.165, 0.03), (0.2, 0.0), (0.19, 0.08 * k), (0.12, 0.21 * k), (0.0, 0.27 * k)], 8, m), "yellow", 60)
    apex = m @ Vector((0, 0, 0.27 * k - 0.02))
    ye = apex.y - 0.16
    p.add(tube([tuple(apex), (0.07, apex.y - 0.06, 0.62), (-0.07, apex.y - 0.12, 0.98), (0.0, ye, 1.37)], lambda u: 0.026, k=4, steps=2, caps=False), "lmetal", 70)
    p.add(cyl(0.045, 0.08, (0, ye, 1.347), seg=6), "white")
    return p


def p_astilla():
    p = Piece("Astilla", (0.8, 0.3, 0.2), 60)
    pts = [(-0.4, 0.02), (-0.33, -0.08), (-0.25, -0.15), (0.1, -0.15), (0.22, -0.1), (0.4, -0.04), (0.28, 0.02), (0.34, 0.09), (0.15, 0.15), (-0.2, 0.15), (-0.3, 0.08)]
    hts = [0.11, 0.15, 0.18, 0.2, 0.18, 0.1, 0.16, 0.13, 0.19, 0.2, 0.15]
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, 0.0)) for x, y in pts]
    hi = [bm.verts.new((x, y, h)) for (x, y), h in zip(pts, hts)]
    n = len(pts)
    for j in range(n):
        j2 = (j + 1) % n
        bm.faces.new((lo[j], lo[j2], hi[j2], hi[j]))
    bm.faces.new(list(reversed(lo)))
    ctr = bm.verts.new((-0.02, 0.0, 0.2))
    for j in range(n):
        bm.faces.new((hi[j], hi[(j + 1) % n], ctr))
    p.add(bm, lambda c, n_: "bun" if abs(c.x) > 0.2 and abs(n_.z) < 0.6 else ("dwood" if n_.z < -0.5 else "wood"), 25)
    return p


def p_esquirla():
    p = Piece("Esquirla", (0.5, 0.1, 0.4), 40)
    pts = [(-0.25, 0.0), (0.08, 0.0), (0.25, 0.12), (0.1, 0.4), (-0.12, 0.22)]
    bm = bmesh.new()
    cf = bm.verts.new((0.0, -0.05, 0.16))
    cb = bm.verts.new((0.0, 0.05, 0.16))
    ef = [bm.verts.new((x, -0.012, z)) for x, z in pts]
    eb = [bm.verts.new((x, 0.012, z)) for x, z in pts]
    n = len(pts)
    for j in range(n):
        j2 = (j + 1) % n
        bm.faces.new((cf, ef[j2], ef[j]))
        bm.faces.new((cb, eb[j], eb[j2]))
        bm.faces.new((ef[j], ef[j2], eb[j2], eb[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    p.add(bm, "glass", 15)
    return p


def p_bolso():
    p = Piece("Bolso", (1.6, 0.8, 1.0), 300)
    prof = [(0.1, -0.8), (0.0, -0.7), (0.0, -0.42), (0.0, -0.32), (0.0, 0.32), (0.0, 0.42), (0.0, 0.7), (0.1, 0.8)]
    body = rr_loft(0.8, 0.8, 0.28, 2, prof, yzx((0, 0, 0.4)))

    def role(c, n):
        ax = abs(c.x)
        if ax > 0.69:
            return "orange"
        if 0.31 < ax < 0.43:
            return "dteal"
        return "teal"
    p.add(body, role, 40)
    p.add(decal(rect(-0.6, 0.6, -0.022, 0.022), UP(0.804)), "black")
    p.add(rbox((0.08, 0.05, 0.03), (0.45, -0.04, 0.81), 0.0), "gold")
    for sy in (-1, 1):
        ctrl = [(-0.37, sy * 0.28, 0.66), (-0.33, sy * 0.19, 0.9), (0.0, sy * 0.1, 0.97), (0.33, sy * 0.19, 0.9), (0.37, sy * 0.28, 0.66)]
        p.add(tube(ctrl, lambda u: 0.035, k=5, steps=1, caps=False), "dteal", 70)
    return p


def p_calentador():
    p = Piece("Calentador", (1.6, 1.6, 0.9), 400)
    yf = -0.75
    p.add(bb(-0.8, 0.8, yf, 0.8, 0.0, 0.14, 0.03), lambda c, n: "slate" if n.z > 0.9 else ("dark" if c.z < 0.05 else "lmetal"))
    p.add(bb(-0.8, 0.8, yf, 0.8, 0.76, 0.9, 0.04), lambda c, n: "slate" if n.z < -0.9 else ("orange" if n.y < -0.9 else "lmetal"))
    p.add(bb(-0.8, -0.68, yf, 0.8, 0.14, 0.76), lambda c, n: "slate" if n.x > 0.9 else "lmetal")
    p.add(bb(0.38, 0.8, yf, 0.8, 0.14, 0.76), lambda c, n: "slate" if n.x < -0.9 else "lmetal")
    p.add(bb(-0.68, 0.38, 0.68, 0.8, 0.14, 0.76), lambda c, n: "slate" if n.y < -0.9 else "lmetal")
    p.add(decal(rect(-0.62, 0.32, -0.6, 0.55), DOWN(0.755)), "orange")
    p.add(bb(-0.62, 0.32, -0.55, 0.55, 0.14, 0.18), "metal")
    for x, y, z in ((-0.4, -0.15, 0.18), (0.1, -0.15, 0.18), (-0.15, 0.1, 0.37)):
        mm = M((x, y, z))
        p.add(lathe([(0.12, 0.0), (0.14, 0.045)], 6, mm, cap1=False), "bun")
        p.add(lathe([(0.15, 0.045), (0.15, 0.08)], 6, mm, cap0=False, cap1=False), "patty")
        p.add(lathe([(0.14, 0.08), (0.13, 0.15), (0.0, 0.19)], 6, mm, cap0=False), "bun")
    gm = WF(yf - 0.004)
    p.add(decal(stroke((-0.6, 0.22), (-0.38, 0.62), 0.04), gm), "white")
    p.add(decal(stroke((-0.48, 0.2), (-0.32, 0.48), 0.025), gm), "white")
    p.add(decal(rect(0.43, 0.75, 0.2, 0.72), gm), "slate")
    p.add(cyl(0.085, 0.03, (0.59, yf, 0.42), rot=(90, 0, 0), seg=8), "dark")
    p.add(bb(0.578, 0.602, -0.8, yf - 0.02, 0.42, 0.495, 0.0), "white")
    p.add(decal(circ(0.59, 0.62, 0.035, 6), gm), "red")
    return p


BUILDERS = [
    p_panel_ventana, p_panel_salida, p_techo, p_puerta_altillo, p_cocina, p_calentador, p_mampara_cabina, p_mampara_bodega,
    p_bano, p_cabina_piloto, p_puerta_ala, p_puerta_salida, p_puerta_bano, p_bodega_pared, p_torreta, p_torreta_canones,
    p_mascarilla, p_astilla, p_esquirla, p_bolso,
]


def finalize(p):
    prims = []
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for bm, role, ang in p.parts:
        bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
        ng = [f for f in bm.faces if len(f.verts) > 4]
        if ng:
            bmesh.ops.triangulate(bm, faces=ng, quad_method="BEAUTY", ngon_method="BEAUTY")
        dead = [f for f in bm.faces if f.calc_area() < 1e-8]
        if dead:
            bmesh.ops.delete(bm, geom=dead, context="FACES_ONLY")
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
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    return verts, faces, uvs, nrms, tris, raw, sc, off


def palette_image():
    img = bpy.data.images.new("kit_interior_palette", 64, 64, alpha=True)
    px = [0.5] * (64 * 64 * 4)
    cell = 64 // GRID
    for i in range(GRID * GRID):
        r, g, b = hex_rgb(PAL[i][1]) if i < len(PAL) else (0.5, 0.5, 0.5)
        gx, gy = i % GRID, i // GRID
        for y in range(gy * cell, gy * cell + cell):
            for x in range(gx * cell, gx * cell + cell):
                o = (y * 64 + x) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "kit_interior_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def palette_material(img):
    mat = bpy.data.materials.new("KitInterior_Palette")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.6
    if arg("--debug-backface"):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        lp = nt.nodes.new("ShaderNodeLightPath")
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(geo.outputs["Backfacing"], mul.inputs[0])
        nt.links.new(lp.outputs["Is Camera Ray"], mul.inputs[1])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        nt.links.new(mul.outputs[0], mix.inputs[0])
        nt.links.new(tex.outputs["Color"], mix.inputs[6])
        mix.inputs[7].default_value = (1.0, 0.0, 1.0, 1.0)
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        nt.links.new(mul.outputs[0], bsdf.inputs["Emission Strength"])
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.0, 1.0, 1.0)
    return mat


def make_object(p, mat):
    verts, faces, uvs, nrms, tris, raw, sc, off = finalize(p)
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
    return ob, tris, raw, sc, off


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
        ob, tris, raw, sc, off = make_object(p, mat)
        objs[p.name] = ob
        flag = "OK" if tris <= p.budget else "OVER"
        if tris > p.budget:
            ok = False
        warn = " SCALE!" if any(abs(s - 1.0) > 0.004 for s in sc) else ""
        print("PIECE %-15s tris %5d / %5d %s  raw %.3f x %.3f x %.3f  fit %.4f %.4f %.4f  off %.3f %.3f %.3f%s" % (
            p.name, tris, p.budget, flag, raw.x, raw.y, raw.z, sc[0], sc[1], sc[2], off.x, off.y, off.z, warn))
        if not arg("--no-export"):
            export_fbx(ob)
        dim = ob.dimensions
        manifest.append({"nombre": p.name, "archivo": p.name + ".fbx", "tamano": [round(dim.x, 3), round(dim.z, 3), round(dim.y, 3)], "triangulos": tris})
    if not only and not arg("--no-export"):
        with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("ALL BUDGETS OK" if ok else "SOME PIECES OVER BUDGET")
    if arg("--no-render"):
        return
    threads = arg("--threads")
    threads = int(threads) if isinstance(threads, str) else 2
    which = arg("--sheets")
    which = set(which.split(",")) if isinstance(which, str) else None
    outdir = arg("--render-dir")
    outdir = outdir if isinstance(outdir, str) else OUT
    render_all(objs, which, threads, outdir)


TEMP = []


def keep(o):
    TEMP.append(o)
    return o


def clear_temp():
    for o in TEMP:
        try:
            data = o.data
            bpy.data.objects.remove(o)
            if isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)
            elif isinstance(data, bpy.types.Light):
                bpy.data.lights.remove(data)
            elif isinstance(data, bpy.types.Camera):
                bpy.data.cameras.remove(data)
        except ReferenceError:
            pass
    TEMP.clear()


MATS = {}


def flat_mat(name, hexc, rough=0.85, emit=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(hex_rgb(hexc)), 1.0)
    b.inputs["Roughness"].default_value = rough
    if emit > 0:
        b.inputs["Emission Color"].default_value = (*lin(hex_rgb(hexc)), 1.0)
        b.inputs["Emission Strength"].default_value = emit
    MATS[name] = m
    return m


def plane(name, x0, x1, y0, y1, z, mat):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    bm.faces.new(vs)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return keep(o)


def inst(objs, name, loc=(0, 0, 0), rz=0.0, mw=None):
    o = bpy.data.objects.new(name + "_i", objs[name].data)
    bpy.context.scene.collection.objects.link(o)
    o.matrix_world = mw if mw is not None else M(loc, (0, 0, rz))
    return keep(o)


SEAT = []


def seat_data():
    if SEAT:
        return SEAT[0]
    path = os.path.join(PROPS, "Asiento.fbx")
    if not os.path.exists(path):
        SEAT.append(None)
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    me = next((o.data for o in new if o.type == "MESH"), None)
    for o in new:
        bpy.data.objects.remove(o)
    SEAT.append(me)
    return me


def seat(loc):
    me = seat_data()
    if me is None:
        return None
    o = bpy.data.objects.new("Seat_i", me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    return keep(o)


def render_setup(scene, threads, w, h, bounces=4):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 8 if arg("--fast") else 32
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    scene.cycles.max_bounces = bounces
    scene.render.threads_mode = "FIXED"
    scene.render.threads = threads
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    scene.view_settings.exposure = 0.0


def world(scene, hexc, strength):
    w = bpy.data.worlds.get("Sky") or bpy.data.worlds.new("Sky")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*lin(hex_rgb(hexc)), 1.0)
    bg.inputs[1].default_value = strength
    scene.world = w


def sun(energy=3.6, rot=(46, 0, -32), angle=12):
    d = bpy.data.lights.new("Sun", "SUN")
    d.energy = energy
    d.angle = math.radians(angle)
    o = bpy.data.objects.new("Sun", d)
    o.rotation_euler = [math.radians(a) for a in rot]
    bpy.context.scene.collection.objects.link(o)
    return keep(o)


def area(loc, size, size_y=None, power=100.0, rot=(0, 0, 0), color="FFF4E0"):
    d = bpy.data.lights.new("Area", "AREA")
    d.energy = power
    d.color = lin(hex_rgb(color))
    if size_y is None:
        d.shape = "SQUARE"
        d.size = size
    else:
        d.shape = "RECTANGLE"
        d.size = size
        d.size_y = size_y
    o = bpy.data.objects.new("Area", d)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    bpy.context.scene.collection.objects.link(o)
    return keep(o)


def point(loc, power=100.0, radius=0.3, color="FFF1DA"):
    d = bpy.data.lights.new("Pt", "POINT")
    d.energy = power
    d.shadow_soft_size = radius
    d.color = lin(hex_rgb(color))
    o = bpy.data.objects.new("Pt", d)
    o.location = loc
    bpy.context.scene.collection.objects.link(o)
    return keep(o)


def camera_look(loc, target, lens):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.clip_start = 0.05
    cd.clip_end = 2000
    co = bpy.data.objects.new("Cam", cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = co
    return keep(co)


def camera_fit(objs_list, el, az, lens, mx=0.9, my=0.86, extra=()):
    scene = bpy.context.scene
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs_list for c in o.bound_box] + [Vector(e) for e in extra]
    el, az = math.radians(el), math.radians(az)
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    f = -d
    right = f.cross(Vector((0, 0, 1))).normalized()
    upv = right.cross(f).normalized()
    tx = 18.0 / lens
    ty = tx * scene.render.resolution_y / scene.render.resolution_x
    c = sum(pts, Vector()) / len(pts)

    def dist(c):
        q = [((p - c).dot(right), (p - c).dot(upv), (p - c).dot(d)) for p in pts]
        return q, max(max(z + abs(x) / (tx * mx) for x, y, z in q), max(z + abs(y) / (ty * my) for x, y, z in q))
    for _ in range(6):
        q, D = dist(c)
        sx = [x / (D - z) for x, y, z in q]
        sy = [y / (D - z) for x, y, z in q]
        c = c + right * ((max(sx) + min(sx)) / 2 * D) + upv * ((max(sy) + min(sy)) / 2 * D)
    q, D = dist(c)
    return camera_look(c + d * D, c, lens)


def label(cam, text, w, h, px=26):
    lens = cam.data.lens
    half = 18.0 / lens
    size = 2 * half * px / w
    cu = bpy.data.curves.new("Lbl", "FONT")
    cu.body = text
    cu.size = size
    cu.align_x = "LEFT"
    cu.materials.append(flat_mat("LabelMat", "34383F", 1.0, 0.0))
    o = bpy.data.objects.new("Lbl", cu)
    bpy.context.scene.collection.objects.link(o)
    o.parent = cam
    o.location = (-half + 2 * half * 14 / w, -half * h / w + 2 * half * 14 / w, -1.0)
    o.visible_shadow = False
    keep(o)
    tw = size * 0.52 * len(text) + 2 * half * 20 / w
    bk = plane("LblBack", 0, tw, 0, size * 1.45, 0.0, flat_mat("LabelBack", "FFFFFF", 1.0, 0.85))
    bk.parent = cam
    bk.location = (-half + 2 * half * 6 / w, -half * h / w + 2 * half * 6 / w, -1.001)
    bk.visible_shadow = False
    return o


def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDER", path)


def composite(paths, cols, rows, W, H, out, gutter=4, gcol="F4F9FB"):
    import numpy as np
    canvas = np.zeros((H, W, 4), dtype=np.float32)
    g = hex_rgb(gcol)
    canvas[:, :, 0], canvas[:, :, 1], canvas[:, :, 2], canvas[:, :, 3] = g[0], g[1], g[2], 1.0
    tw = [W // cols + (1 if c < W % cols else 0) for c in range(cols)]
    th = H // rows
    for idx, pth in enumerate(paths):
        r, c = divmod(idx, cols)
        img = bpy.data.images.load(pth)
        a = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
        x0 = sum(tw[:c])
        y0 = H - th * (r + 1)
        hh, ww = a.shape[0], a.shape[1]
        canvas[y0:y0 + hh, x0:x0 + ww] = a
        bpy.data.images.remove(img)
    for c in range(1, cols):
        x = sum(tw[:c])
        canvas[:, x - gutter // 2:x + gutter // 2, :3] = g
    for r in range(1, rows):
        y = H - th * r
        canvas[y - gutter // 2:y + gutter // 2, :, :3] = g
    oi = bpy.data.images.new("Sheet", W, H, alpha=False)
    oi.pixels.foreach_set(canvas.ravel())
    oi.filepath_raw = out
    oi.file_format = "PNG"
    oi.save()
    bpy.data.images.remove(oi)
    print("SHEET", out)


def studio(ground="D6EEF7", sky="BFE3F2", strength=0.62, sun_e=3.0, sun_rot=(50, 0, -48)):
    world(bpy.context.scene, sky, strength)
    sun(sun_e, sun_rot)
    bpy.context.scene.view_settings.exposure = -0.25
    if ground:
        plane("Ground", -300, 300, -300, 300, 0.0, flat_mat("GroundMat", ground, 0.95))


def bin_door(objs, sx, y, open_deg=0.0):
    rz = -90 if sx > 0 else 90
    base = M((sx * 4.025, y, 7.0), (0, 0, rz))
    if open_deg:
        hinge = Vector((sx * 4.1, y, 9.4))
        ang = math.radians(open_deg) * sx
        R = Matrix.Translation(hinge) @ Matrix.Rotation(ang, 4, "Y") @ Matrix.Translation(-hinge)
        base = R @ base
    return inst(objs, "PuertaAltillo", mw=base)


def cabin_floor(y0, y1):
    plane("Floor", -7.4, 7.4, y0, y1, 0.0, flat_mat("Carpet", "2B5459", 0.95))
    plane("Aisle", -1.1, 1.1, y0, y1, 0.004, flat_mat("AisleMat", "F27B2B", 0.9))


def sheet_1(objs, threads, outdir):
    scene = bpy.context.scene
    W, H = 1600, 900
    render_setup(scene, threads, W, H, 6)
    world(scene, "CFE9F5", 1.2)
    rows = [0.0, 4.5, 9.0]
    cabin_floor(-6.0, 12.0)
    for i, y in enumerate(rows):
        inst(objs, "PanelSalida" if i == 1 else "PanelVentana", (-7.05, y, 0), 90)
        inst(objs, "PanelVentana", (7.05, y, 0), -90)
        inst(objs, "Techo", (0, y, 6.5))
        for sx in (-1, 1):
            bin_door(objs, sx, y, 92.0 if (i == 1 and sx > 0) else 0.0)
        for x in (-5.55, -3.35, 3.35, 5.55):
            if i == 1 and x < -5:
                continue
            seat((x, y, 0.0))
    inst(objs, "Bolso", (5.3, 4.2, 7.0), 90)
    inst(objs, "Bolso", (5.25, 5.3, 8.05), 84)
    inst(objs, "MamparaCabina", (0, 11.55, 0))
    for y in rows:
        for sx in (-1, 1):
            area((sx * 2.6, y, 9.6), 0.5, 4.3, 70.0, (0, 0, 0), "FFF1D6")
    area((0, -4.5, 5.0), 6.0, 4.0, 260.0, (90, 0, 0), "FFF6EA")
    point((0, 6.0, 4.0), 120.0, 1.0)
    cam = camera_look((1.15, -4.2, 4.35), (-0.9, 9.0, 5.75), 17.0)
    render_to(os.path.join(outdir, "kit_1.png"))
    clear_temp()


TILE_DIR = []


def tile_paths(outdir, tag, n):
    import tempfile
    if not TILE_DIR:
        TILE_DIR.append(tempfile.mkdtemp(prefix="kit_interior_tiles_"))
    d = TILE_DIR[0]
    return [os.path.join(d, "%s_%d.png" % (tag, i)) for i in range(n)]


TW, TH = 533, 450


def sheet_2(objs, threads, outdir):
    scene = bpy.context.scene
    paths = tile_paths(outdir, "k2", 6)

    def t_cocina():
        studio()
        o = inst(objs, "CocinaModulo", (0, 0, 0), -24)
        c = inst(objs, "Calentador", mw=o.matrix_world @ M((-2.2, -0.2, 3.5)))
        cam = camera_fit([o], 22, -24, 50)
        return cam, "CocinaModulo + Calentador"

    def t_mampara_c():
        studio()
        o = inst(objs, "MamparaCabina", (0, 0, 0), -22)
        cam = camera_fit([o], 18, -22, 50)
        return cam, "MamparaCabina"

    def t_mampara_b():
        studio()
        o = inst(objs, "MamparaBodega", (0, 0, 0), 180 + 24)
        cam = camera_fit([o], 18, -24, 50)
        return cam, "MamparaBodega (cara bodega)"

    def t_bano():
        studio(sun_rot=(38, 0, -20))
        o = inst(objs, "Bano", (0, 0, 0), -24)
        cam = camera_look(tuple(o.matrix_world @ Vector((1.0, -8.2, 5.4))), tuple(o.matrix_world @ Vector((-0.1, 0.3, 4.1))), 30.0)
        return cam, "Bano"

    def t_puertas():
        studio()
        a = inst(objs, "PanelSalida", (-4.2, 0.5, 0), 0)
        inst(objs, "PuertaAla", (-4.2, 0.5, 0), 0)
        b = inst(objs, "PuertaAla", (-0.3, 0, 0), -16)
        c = inst(objs, "PuertaSalida", (3.3, 0, 0), -16)
        d = inst(objs, "PuertaBano", (6.4, 0, 0), -16)
        cam = camera_fit([a, b, c, d], 14, -18, 50)
        return cam, "Puertas: Ala (en panel), Ala, Salida, Bano"

    def t_altillo():
        studio(ground=None, sky="C9E6F3")
        zt = 8.0
        t = inst(objs, "Techo", (0, 0, zt), 0)
        for sx, ang in ((-1, 0.0), (1, 92.0)):
            o = bin_door(objs, sx, 0.0, ang)
            o.matrix_world = M((0, 0, zt - 6.5)) @ o.matrix_world
        inst(objs, "Bolso", (5.3, -0.6, zt + 0.5), 90)
        inst(objs, "Bolso", (5.4, 1.1, zt + 0.5), 96)
        cam = camera_fit([t], -24, 212, 50, 0.92, 0.82)
        return cam, "Techo + PuertaAltillo (+ Bolso)"
    for i, fn in enumerate((t_cocina, t_mampara_c, t_mampara_b, t_bano, t_puertas, t_altillo)):
        render_setup(scene, threads, TW + (1 if i % 3 < 1600 % 3 else 0), TH)
        cam, txt = fn()
        label(cam, txt, scene.render.resolution_x, TH)
        render_to(paths[i])
        clear_temp()
    composite(paths, 3, 2, 1600, 900, os.path.join(outdir, "kit_2.png"))


def sheet_3(objs, threads, outdir):
    scene = bpy.context.scene
    paths = tile_paths(outdir, "k3", 6)

    def t_cab_in():
        world(scene, "CFE9F5", 1.4)
        plane("Floor", -6, 6, -6, 6, 0.0, flat_mat("Carpet", "2B5459", 0.95))
        inst(objs, "CabinaPiloto", (0, 0, 0), 0)
        area((0, 1.0, 7.3), 3.0, 3.0, 160.0, (0, 0, 0), "FFF1D6")
        area((0, 6.5, 4.5), 5.0, 3.0, 220.0, (-90, 0, 0), "FFF6EA")
        cam = camera_look((0.25, 3.9, 3.9), (0.0, -5.0, 5.3), 14.0)
        return cam, "CabinaPiloto (interior)"

    def t_cab_out():
        studio(sun_rot=(40, 0, 150))
        o = inst(objs, "CabinaPiloto", (0, 0, 0), 180 - 30)
        cam = camera_fit([o], 26, -30, 50)
        return cam, "CabinaPiloto (desde atras)"

    def t_bodega():
        studio()
        o = inst(objs, "BodegaPared", (0, 0, 0), -18)
        cam = camera_fit([o], 16, -18, 50)
        return cam, "BodegaPared"

    def t_torreta():
        studio()
        b = inst(objs, "Torreta", (0, 0, 0), -35)
        c = inst(objs, "TorretaCanones", mw=M((0, 0, 1.0), (0, 0, -35)))
        cam = camera_fit([b, c], 22, 12, 50)
        return cam, "Torreta + TorretaCanones (montada)"

    def t_torreta_x():
        studio()
        b = inst(objs, "Torreta", (-1.9, 0, 0), 30)
        c = inst(objs, "TorretaCanones", (1.9, 0, 0), 30 + 180)
        cam = camera_fit([b, c], 28, -20, 50)
        return cam, "Torreta (base) / TorretaCanones"

    def t_small():
        studio()
        a = inst(objs, "Bolso", (-1.4, 0.2, 0), -20)
        b = inst(objs, "Mascarilla", (0.2, 0.0, 0), -20)
        c = inst(objs, "Astilla", (1.05, -0.35, 0), 25)
        d = inst(objs, "Esquirla", (1.25, 0.35, 0), -30)
        e = inst(objs, "Esquirla", (0.75, 0.55, 0), 40)
        cam = camera_fit([a, b, c, d], 26, -15, 50)
        return cam, "Bolso, Mascarilla, Astilla, Esquirla"
    for i, fn in enumerate((t_cab_in, t_cab_out, t_bodega, t_torreta, t_torreta_x, t_small)):
        render_setup(scene, threads, TW + (1 if i % 3 < 1600 % 3 else 0), TH, 6 if i == 0 else 4)
        cam, txt = fn()
        label(cam, txt, scene.render.resolution_x, TH)
        render_to(paths[i])
        clear_temp()
    composite(paths, 3, 2, 1600, 900, os.path.join(outdir, "kit_3.png"))


def render_all(objs, which, threads, outdir):
    for o in objs.values():
        o.hide_render = True
    if not which or "1" in which:
        sheet_1(objs, threads, outdir)
    if not which or "2" in which:
        sheet_2(objs, threads, outdir)
    if not which or "3" in which:
        sheet_3(objs, threads, outdir)
    if TILE_DIR:
        import shutil
        shutil.rmtree(TILE_DIR[0], ignore_errors=True)


if __name__ == "__main__":
    main()
