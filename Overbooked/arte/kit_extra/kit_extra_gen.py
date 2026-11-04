import bpy
import bmesh
import math
import os
import sys
import json
import mathutils
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ARTE = os.path.dirname(OUT)
TRIP_BLEND = os.path.join(ARTE, "tripulante", "tripulante.blend")
PROPS = os.path.join(ARTE, "props")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]


def arg(name, default=None):
    if name in ARGS:
        i = ARGS.index(name)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return default


# Paleta 8x8. La ultima fila (casillas 56-63) son colores "que brillan" (pantalla, pilotos):
# en Roblox son solo colores claros; en los renders de Blender llevan algo de emision.
BASE = [
    ("cream", "FFF4E0"), ("orange", "F27B2B"), ("teal", "1FA6A0"), ("dark", "34383F"),
    ("black", "1B1B21"), ("white", "F7F7F2"), ("red", "D9443A"), ("yellow", "F6C445"),
    ("metal", "A9B0B8"), ("steel", "6E7782"), ("lmetal", "D3D9DE"), ("dteal", "157F7B"),
    ("dorange", "C95A1E"), ("gold", "F0B73A"), ("navy", "2D3A4A"), ("rubber", "2A2C31"),
    ("tan", "C98B4E"), ("dtan", "8A5A33"), ("duck", "FFD23F"), ("beak", "F28C28"),
    ("velvet", "C23B4A"), ("green", "2FA552"), ("lteal", "A3DED8"), ("grey", "8C939B"),
    ("card", "D9B27C"), ("dcard", "B88B54"), ("cream2", "F0E2C6"), ("pink", "F27BB5"),
    ("lilac", "A07CF2"), ("sky", "8FD3F4"), ("lime", "8BD24C"), ("ddark", "24272D"),
]
EMIT = [("screen", "B5F5EE"), ("lampr", "FF5A4E"), ("lampg", "6BEA8A"), ("glow", "FFF3C4")]
GRID = 8
PAL = BASE + [("_%d" % i, "808080") for i in range(len(BASE), 56)] + EMIT
PAL += [("_%d" % i, "808080") for i in range(len(PAL), GRID * GRID)]
IDX = {n: i for i, (n, _) in enumerate(PAL)}


def suv(n):
    i = IDX[n]
    return ((i % GRID + 0.5) / GRID, (i // GRID + 0.5) / GRID)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ---------------------------------------------------------------- geometria basica

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


FR = {"-y": ((1, 0, 0), (0, 0, 1)), "+y": ((-1, 0, 0), (0, 0, 1)), "+x": ((0, 1, 0), (0, 0, 1)),
      "-x": ((0, -1, 0), (0, 0, 1)), "+z": ((1, 0, 0), (0, 1, 0)), "-z": ((1, 0, 0), (0, -1, 0))}


def fr(o, side):
    ex, ey = FR[side]
    return frame(o, ex, ey)


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


def drop_faces(bm, pred):
    bm.normal_update()
    dead = [f for f in bm.faces if pred(f.calc_center_median(), f.normal)]
    if dead:
        bmesh.ops.delete(bm, geom=dead, context="FACES_ONLY")
    return bm


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


def elathe(prof, seg, k=1.0, cy=0.0, rmod=None, zmod=None, cap0=True, cap1=True, a0=0.0, m=None):
    """Torno de seccion eliptica: prof = [(r, z) o (r, z, k)], radio X = r, radio Y = k*r.
    rmod(i, a) multiplica el radio, zmod(i, a) suma altura (a = angulo, -90 grados = frente -Y)."""
    bm = bmesh.new()
    rings = []
    for i, pt in enumerate(prof):
        r, z = pt[0], pt[1]
        kk = pt[2] if len(pt) > 2 else k
        if r < 1e-6:
            rings.append([bm.verts.new((0.0, cy, z))])
            continue
        ring = []
        for j in range(seg):
            a = a0 + 2 * math.pi * j / seg
            rr = r * (rmod(i, a) if rmod else 1.0)
            zz = z + (zmod(i, a) if zmod else 0.0)
            ring.append(bm.verts.new((rr * math.cos(a), cy + kk * rr * math.sin(a), zz)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(seg):
            j2 = (j + 1) % seg
            if len(a) == 1:
                bm.faces.new((a[0], b[j2], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[j], a[j2], b[0]))
            else:
                bm.faces.new((a[j], a[j2], b[j2], b[j]))
    if cap0 and len(rings[0]) > 1:
        bm.faces.new(list(reversed(rings[0])))
    if cap1 and len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    return xf(bm, m)


def cyl(r, h, loc=(0, 0, 0), rot=(0, 0, 0), seg=12, r2=None, bev=0.0, center=False, m=None, cap0=True, cap1=True, a0=None):
    z0 = -h / 2 if center else 0.0
    rt = r if r2 is None else r2
    if bev > 0:
        prof = [(r - bev, z0), (r, z0 + bev), (rt, z0 + h - bev), (rt - bev, z0 + h)]
    else:
        prof = [(r, z0), (rt, z0 + h)]
    mm = M(loc, rot)
    return lathe(prof, seg, m @ mm if m is not None else mm, cap0=cap0, cap1=cap1, a0=a0)


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


def rrect(cx, cy, w, h, r, cs=2):
    return [(cx + x, cy + y) for x, y in rr_pts(w, h, r, cs)]


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


def ellipsoid(radii, mat=Matrix(), u=12, v=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.transform(bm, matrix=mat @ Matrix.Diagonal((*radii, 1.0)), verts=bm.verts)
    return bm


def ico(r, loc, sub=0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    return bm


def octa(radii, mat):
    bm = bmesh.new()
    P = [bm.verts.new(p) for p in ((1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0))]
    top = bm.verts.new((0, 0, 1))
    bot = bm.verts.new((0, 0, -1))
    for j in range(4):
        bm.faces.new((P[j], P[(j + 1) % 4], top))
        bm.faces.new((P[(j + 1) % 4], P[j], bot))
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


def tube(ctrl, rf, k=8, steps=4, closed=False, up=None, caps=True, phase=0.0):
    """Tubo por una curva. rf(u) da un radio o (radio en la normal, radio en la binormal).
    up = direccion de la normal al empezar. caps = tapas planas en los extremos."""
    ctrl = [Vector(c) for c in ctrl]
    path = catmull(ctrl, steps, closed) if steps > 1 else [c.copy() for c in ctrl]
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
        r = rf(seglen[i] / total if total > 0 else 0.0)
        rn, rb = r if isinstance(r, tuple) else (r, r)
        b = tangents[i].cross(normals[i]).normalized()
        rings.append([bm.verts.new(path[i] + normals[i] * (math.cos(2 * math.pi * (j + phase) / k) * rn)
                                   + b * (math.sin(2 * math.pi * (j + phase) / k) * rb)) for j in range(k)])
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
    for a_i, b_i in pairs:
        ra, rb_ = rings[a_i], rings[b_i]
        for j in range(k):
            bm.faces.new((ra[j], ra[(j + 1) % k], rb_[(j + 1) % k], rb_[j]))
    if caps and not closed:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    return bm


def sheet(rows, t, closed_u=False):
    """Lamina gruesa: rows = filas de puntos (la cara de arriba); la de abajo baja t en Z."""
    bm = bmesh.new()
    T = [[bm.verts.new(p) for p in row] for row in rows]
    B = [[bm.verts.new((p[0], p[1], p[2] - t)) for p in row] for row in rows]
    R, C = len(rows), len(rows[0])
    cs = C if closed_u else C - 1
    for i in range(R - 1):
        for j in range(cs):
            j2 = (j + 1) % C
            bm.faces.new((T[i][j], T[i + 1][j], T[i + 1][j2], T[i][j2]))
            bm.faces.new((B[i][j], B[i][j2], B[i + 1][j2], B[i + 1][j]))
    for i in (0, R - 1):
        for j in range(cs):
            j2 = (j + 1) % C
            bm.faces.new((T[i][j], T[i][j2], B[i][j2], B[i][j]))
    if not closed_u:
        for j in (0, C - 1):
            for i in range(R - 1):
                bm.faces.new((T[i][j], B[i][j], B[i + 1][j], T[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def wrap(bm, fn):
    for v in bm.verts:
        v.co = Vector(fn(v.co))
    return bm


class Prop:
    def __init__(self, name, size, budget, hat=None):
        self.name = name
        self.size = size
        self.budget = budget
        self.hat = hat
        self.parts = []

    def add(self, bm, role, ang=50.0):
        self.parts.append((bm, role, ang))
        return bm


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


def by_normal(front, back=None, side=None, axis=1, thr=0.5):
    def f(c, n):
        v = n[axis]
        if v < -thr:
            return front
        if v > thr and back is not None:
            return back
        return side if side is not None else front
    return f


# ---------------------------------------------------------------- 1. Piolet

def p_piolet():
    # Mango en Z, cabeza arriba: pico hacia -Y, azuela hacia +Y. Por eso la caja es 0,25 x 0,5 x 1,9
    # (X e Y cambiados respecto al encargo, que pedia 0,5 x 0,25 con el pico en Y).
    p = Prop("Piolet", (0.25, 0.5, 1.9), 300)
    p.add(lathe([(0.0, 0.0), (0.028, 0.06), (0.048, 0.15)], 6, cap1=False, a0=math.radians(30)), "metal", 60)
    p.add(rr_loft(0.13, 0.16, 0.05, 1, [(0.012, 0.13), (0.0, 0.17), (0.0, 0.56), (0.022, 0.62)]), "orange", 40)
    p.add(rr_loft(0.135, 0.165, 0.05, 1, [(0.0, 0.33), (0.0, 0.37)], cap0=False, cap1=False), "dorange", 40)
    p.add(rr_loft(0.08, 0.105, 0.032, 1, [(0.0, 0.6), (0.0, 1.74)], cap0=False, cap1=False), "teal", 40)
    p.add(rr_loft(0.1, 0.125, 0.04, 1, [(0.0, 0.64), (0.0, 0.72)]), "dark", 40)
    p.add(rr_loft(0.11, 0.15, 0.025, 1, [(0.0, 1.70), (0.0, 1.90)]), "metal", 40)
    cl = [Vector(c) for c in ((-0.04, 1.86), (-0.10, 1.853), (-0.16, 1.83), (-0.21, 1.787), (-0.25, 1.712))]
    hh = [0.038, 0.032, 0.025, 0.016, 0.0]
    top, bot = [], []
    for i, c in enumerate(cl):
        t = (cl[min(i + 1, 4)] - cl[max(i - 1, 0)]).normalized()
        nout = Vector((t.y, -t.x))
        if nout.y < 0:
            nout = -nout
        top.append(c + nout * hh[i])
        bot.append(c - nout * hh[i])
    teeth = []
    for i in (3, 2, 1):
        mid = (cl[i] + cl[i + 1]) / 2
        t = (cl[i + 1] - cl[i]).normalized()
        nout = Vector((t.y, -t.x))
        if nout.y < 0:
            nout = -nout
        teeth.append(mid - nout * ((hh[i] + hh[i + 1]) / 2 + 0.014))
        teeth.append(bot[i])
    pick = [tuple(v) for v in top[:4]] + [tuple(top[4])] + [tuple(v) for v in teeth] + [tuple(bot[0])]
    p.add(prism(pick, 0.05, yzx((0, 0, 0))), "metal", 35)
    bm = bmesh.new()
    st = [(0.05, 1.83, 1.885, 0.10), (0.15, 1.805, 1.86, 0.17), (0.25, 1.775, 1.825, 0.25)]
    rings = [[bm.verts.new((sx * w / 2, y, z)) for sx, z in ((-1, z0), (1, z0), (1, z1), (-1, z1))] for y, z0, z1, w in st]
    for a, b in zip(rings, rings[1:]):
        for j in range(4):
            bm.faces.new((a[j], b[j], b[(j + 1) % 4], a[(j + 1) % 4]))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    p.add(bm, "metal", 30)
    for sx, side in ((1, "+x"), (-1, "-x")):
        p.add(decal(circ(0.0, 1.80, 0.022, 6), fr((sx * 0.055, 0, 0), side), 0.004), "dark")
    loop = [(0.0, 0.06, 0.69), (0.0, 0.135, 0.63), (0.0, 0.19, 0.48), (0.0, 0.192, 0.33),
            (0.0, 0.15, 0.265), (0.0, 0.115, 0.32), (0.0, 0.112, 0.48), (0.0, 0.088, 0.63)]
    p.add(tube(loop, lambda u: (0.03, 0.009), k=4, steps=1, closed=True, up=(1, 0, 0), phase=0.5), "teal", 50)
    return p


# ---------------------------------------------------------------- 2. Escaner

SCAN = {"TX": 1.3, "TZ0": 1.0, "TZ1": 3.2, "HX": 1.75, "HY": 1.5, "HZ": 3.75, "BED": 0.72}


def p_escaner():
    p = Prop("Escaner", (4.0, 7.0, 4.2), 1800)
    TX, TZ0, TZ1, HX, HY, HZ, BED = (SCAN[k] for k in ("TX", "TZ0", "TZ1", "HX", "HY", "HZ", "BED"))
    R = 0.45
    outer = [(-HX, BED), (-TX, BED), (-TX, TZ1), (TX, TZ1), (TX, BED), (HX, BED)]
    for k in range(5):
        a = math.radians(90.0 * k / 4)
        outer.append((HX - R + R * math.cos(a), HZ - R + R * math.sin(a)))
    for k in range(5):
        a = math.radians(90.0 + 90.0 * k / 4)
        outer.append((-HX + R + R * math.cos(a), HZ - R + R * math.sin(a)))
    bm = plate(outer, (), 2 * HY, frame((0, HY, 0), (1, 0, 0), (0, 0, 1)))
    bevel_where(bm, lambda e: all(abs(v.co.y) > HY - 1e-3 for v in e.verts) and not any(abs(v.co.x) < TX + 0.01 and v.co.z < TZ1 + 0.01 for v in e.verts), 0.05, 1)

    def shell(c, n):
        if abs(c.x) < TX + 0.01 and c.z < TZ1 + 0.01 and abs(n.y) < 0.5:
            return "dark"
        return "cream"
    p.add(bm, shell, 35)
    p.add(bb(-HX, HX, -HY, HY, 0.0, BED + 0.02, 0.05, 1), lambda c, n: "steel" if n.z > 0.5 else "teal")
    for sy in (-1, 1):
        y0, y1 = sorted((sy * HY, sy * (HY + 0.1)))
        bz = [(-1.48, BED), (-TX, BED), (-TX, TZ1), (TX, TZ1), (TX, BED), (1.48, BED), (1.48, TZ1 + 0.18), (-1.48, TZ1 + 0.18)]
        p.add(plate(bz, (), y1 - y0, frame((0, y1, 0), (1, 0, 0), (0, 0, 1))), "rubber", 35)
        side = "-y" if sy < 0 else "+y"
        mf = fr((0, sy * (HY + 0.005), 0), side)
        p.add(decal(rect(-1.48, 1.48, 3.44, 3.64), mf, 0.0), "yellow")
        for i in range(10):
            u = -1.42 + 0.27 * i
            p.add(decal([(u, 3.44), (u + 0.12, 3.44), (u + 0.32, 3.64), (u + 0.2, 3.64)], mf, 0.004), "black")
        xs = [-TX + (2 * TX + 0.03) * i / 8 for i in range(9)]
        zb = [2.48, 2.56, 2.5, 2.58, 2.52, 2.47, 2.55, 2.5]
        ym = sy * (HY + 0.05)
        for i in range(8):
            x0, x1 = xs[i], xs[i + 1] - 0.03
            p.add(rr_loft(x1 - x0, 0.025, 0.0, 0, [(0.0, zb[i]), (0.0, TZ1)], M(((x0 + x1) / 2, ym, 0)), cap1=False), "grey")
    p.add(decal(rect(-0.9, 0.9, -HY + 0.1, HY - 0.1), fr((0, 0, TZ1 - 0.003), "-z")), "glow")
    for sx in (-1, 1):
        x0, x1 = sorted((sx * TX, sx * 1.44))
        p.add(bb(x0, x1, -3.5, 3.5, 0.78, 1.0), "steel")
    rr = 0.1
    cz = TZ0 - rr * math.cos(math.pi / 8)
    for i in range(20):
        y = -3.33 + 6.66 * i / 19
        p.add(lathe([(rr, -TX), (rr, TX)], 8, yzx((0, y, cz)), cap0=False, cap1=False, a0=math.pi / 8), "metal", 50)
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 3.42, sy * 3.496))
        p.add(bb(-1.44, 1.44, y0, y1, 0.66, 0.97), "yellow")
        side = "-y" if sy < 0 else "+y"
        mf = fr((0, sy * 3.496, 0), side)
        for i in range(6):
            u = -1.34 + 0.46 * i
            p.add(decal([(u, 0.68), (u + 0.14, 0.68), (u + 0.33, 0.95), (u + 0.19, 0.95)], mf, 0.004), "black")
        for yl in (sy * 3.25, sy * 1.78):
            for sx in (-1, 1):
                x = sx * 1.37
                p.add(drop_faces(bb(x - 0.05, x + 0.05, yl - 0.05, yl + 0.05, 0.0, 0.79), lambda c, n: n.z > 0.5), "dark")
            p.add(bar((-1.32, yl, 0.26), (1.32, yl, 0.26), 0.07, 0.07, caps=False), "dark")
        for sx in (-1, 1):
            p.add(bar((sx * 1.37, sy * 1.83, 0.26), (sx * 1.37, sy * 3.2, 0.26), 0.07, 0.07, caps=False), "dark")
    # generador de rayos en el lado -X
    p.add(bb(-1.99, -HX + 0.02, -1.0, 1.0, 0.0, 2.9, 0.08, 1), lambda c, n: "teal" if c.z < 0.4 else "cream")
    mg = fr((-1.99, 0, 0), "-x")
    for k in range(4):
        p.add(decal(pill(0.0, 1.55 + 0.22 * k, 1.1, 0.045), mg, 0.004), "dark")
    p.add(decal([(-0.22, 2.35), (0.22, 2.35), (0.0, 2.72)], mg, 0.004), "yellow")
    p.add(decal(rect(-0.022, 0.022, 2.47, 2.62), mg, 0.008), "black")
    p.add(decal(rect(-0.022, 0.022, 2.40, 2.44), mg, 0.008), "black")
    # franjas y logo en los lados
    for sx, side in ((1, "+x"), (-1, "-x")):
        ms = fr((sx * (HX + 0.004), 0, 0), side)
        p.add(decal(rect(-HY + 0.06, HY - 0.06, 2.5, 2.68), ms, 0.0), "orange")
    logo(p, fr((HX + 0.004, 0.0, 1.75), "+x"), 0.42, step=0.005)
    mt = fr((0, 0, HZ + 0.004), "+z")
    p.add(decal(rrect(0, 0, 2.2, 2.6, 0.12, 1), mt, 0.0), "lmetal")
    for k in range(5):
        p.add(decal(rect(-0.7, 0.7, -0.9 + 0.3 * k, -0.84 + 0.3 * k), mt, 0.004), "steel")
    # monitor en brazo (lado +X, delante)
    phi = math.radians(40)
    nrm = Vector((math.sin(phi), -math.cos(phi), 0))
    wv = Vector((math.cos(phi), math.sin(phi), 0))
    c = Vector((1.684, -1.95, 2.65))
    mm = frame(c, wv, (0, 0, 1))
    p.add(rbox((0.8, 0.56, 0.08), bev=0.025, m=mm), "dark", 40)
    p.add(decal(rrect(0, 0, 0.7, 0.46, 0.03, 1), mm, 0.045), "screen")
    back = c - nrm * 0.04
    p.add(bb(1.48, 1.66, -1.56, -1.5, 3.12, 3.42), "steel")
    p.add(bar((1.57, -1.53, 3.27), (1.66, -1.80, 3.12), 0.07, 0.06), "steel")
    p.add(bar((1.66, -1.80, 3.12), (back.x, back.y + 0.01, 2.8), 0.06, 0.05), "steel")
    p.add(rbox((0.2, 0.14, 0.03), m=frame(back - nrm * 0.0 + Vector((0, 0, 0.12)), wv, (0, 0, 1))), "steel")
    # piloto rojo / verde arriba
    lx, ly = 1.0, -0.95
    p.add(cyl(0.12, 0.07, (lx, ly, HZ), seg=10), "dark")
    p.add(cyl(0.09, 0.14, (lx, ly, HZ + 0.07), seg=10, cap0=False, cap1=False), "lampg")
    p.add(cyl(0.1, 0.03, (lx, ly, HZ + 0.21), seg=10), "dark")
    p.add(cyl(0.09, 0.14, (lx, ly, HZ + 0.24), seg=10, cap0=False, cap1=False), "lampr")
    p.add(lathe([(0.1, HZ + 0.38), (0.08, HZ + 0.42), (0.0, HZ + 0.45)], 10, M((lx, ly, 0))), "dark")
    return p


# ---------------------------------------------------------------- 3. Contenedor

def p_contenedor():
    p = Prop("Contenedor", (3.0, 3.0, 2.0), 400)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 1.28, sy * 1.28
            p.add(drop_faces(bb(x - 0.17, x + 0.17, y - 0.17, y + 0.17, 0.0, 0.1), lambda c, n: n.z > 0.5), "rubber")
    p.add(bb(-1.48, 1.48, -1.48, 1.48, 0.1, 0.34), lambda c, n: "steel" if n.z > 0.5 else ("dorange" if n.z < -0.5 else "orange"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, x1 = sorted((sx * 1.36, sx * 1.5))
            y0, y1 = sorted((sy * 1.36, sy * 1.5))
            p.add(drop_faces(bb(x0, x1, y0, y1, 0.1, 2.0), lambda c, n: n.z < -0.5), "orange")
    for s in (-1, 1):
        p.add(bar((-1.36, s * 1.43, 1.93), (1.36, s * 1.43, 1.93), 0.12, 0.14, caps=False), "orange")
        p.add(bar((s * 1.43, -1.36, 1.93), (s * 1.43, 1.36, 1.93), 0.12, 0.14, caps=False), "orange")
    wz0, wz1 = 0.34, 1.86
    rw = 0.022
    for s in (-1, 1):
        for i in range(5):
            u = -1.36 + 2.72 * (i + 1) / 6
            p.add(cyl(rw, wz1 - wz0, (u, s * 1.43, wz0), seg=3, cap0=False, cap1=False), "steel", 70)
            p.add(cyl(rw, wz1 - wz0, (s * 1.43, u, wz0), seg=3, cap0=False, cap1=False), "steel", 70)
        for j in range(3):
            z = wz0 + (wz1 - wz0) * (j + 1) / 4
            p.add(cyl(rw, 2.72, (0, s * 1.43, z), (0, 90, 0), seg=3, center=True, cap0=False, cap1=False), "steel", 70)
            p.add(cyl(rw, 2.72, (s * 1.43, 0, z), (90, 0, 0), seg=3, center=True, cap0=False, cap1=False), "steel", 70)
    p.add(bb(-0.62, 0.62, -1.475, -1.455, 0.66, 1.56), "yellow")
    m = fr((0, -1.475, 0), "-y")
    w = 0.004
    p.add(decal(rrect(0, 1.06, 0.5, 0.34, 0.05, 1), m, w), "black")
    p.add(decal(rect(-0.16, -0.1, 1.23, 1.33), m, w), "black")
    p.add(decal(rect(0.1, 0.16, 1.23, 1.33), m, w), "black")
    p.add(decal(rect(-0.16, 0.16, 1.3, 1.36), m, w), "black")
    p.add(decal(rect(-0.21, 0.21, 1.0, 1.04), m, w + 0.004), "yellow")
    for q in range(4):
        a0 = 45 + 90 * q + 6
        p.add(arc_strip(0.0, 1.11, 0.33, 0.39, a0, a0 + 78, 3, m, w), "black")
    p.add(decal(stroke((-0.235, 1.345), (0.235, 0.875), 0.12), m, w + 0.004), "yellow")
    p.add(decal(stroke((-0.235, 1.345), (0.235, 0.875), 0.06), m, w + 0.008), "black")
    return p


# ---------------------------------------------------------------- 4. Tienda

TIENDA = {"front": -0.8, "awning_min": None}


def p_tienda():
    p = Prop("Tienda", (8.0, 4.0, 5.0), 2000)
    FY = TIENDA["front"]
    # mostrador
    p.add(bb(-3.8, 3.8, FY + 0.13, -0.15, 0.0, 0.16), "dark")
    p.add(bb(-3.8, 3.8, FY + 0.05, -0.1, 0.16, 3.38), lambda c, n: "teal" if n.y < -0.5 else "dteal")
    p.add(bb(-3.82, 3.82, FY, -0.05, 3.38, 3.5, 0.03, 1), lambda c, n: "white" if n.z > 0.5 else "cream")
    mf = fr((0, FY + 0.05, 0), "-y")
    p.add(decal(rect(-3.8, 3.8, 2.95, 3.15), mf, 0.004), "orange")
    p.add(decal(rect(-3.8, 3.8, 0.5, 0.58), mf, 0.004), "cream")
    for x in (-2.55, 2.55):
        p.add(decal(rect(x - 0.03, x + 0.03, 0.58, 2.95), mf, 0.004), "dteal")
    logo(p, fr((0, FY + 0.05, 1.75), "-y"), 0.62, step=0.006)
    # caja registradora
    p.add(bb(2.75, 3.45, -0.6, -0.2, 3.5, 3.68, 0.03, 1), "dark")
    p.add(bar((3.1, -0.35, 3.66), (3.1, -0.35, 3.86), 0.06, 0.06), "dark")
    mr = frame((3.1, -0.4, 3.9), (1, 0, 0), (0, 0.8, 0.6))
    p.add(rbox((0.42, 0.28, 0.05), m=mr), "dark")
    p.add(decal(rrect(0, 0, 0.36, 0.22, 0.02, 1), mr, 0.027), "screen")
    # paredes laterales (frente naranja, zocalo turquesa por fuera y por dentro)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 3.8, sx * 3.996))
        p.add(bb(x0, x1, FY, 2.0, 0.0, 4.84, 0.04, 1), lambda c, n: "orange" if n.y < -0.5 else "cream")
        for xs_, side in ((sx * 4.0, "+x" if sx > 0 else "-x"), (sx * 3.796, "-x" if sx > 0 else "+x")):
            mw = fr((xs_, 0, 0), side)
            u0, u1 = sorted((FY + 0.05, 1.95)) if (side == "+x") else sorted((-1.95, -(FY + 0.05)))
            p.add(decal(rect(u0, u1, 0.0, 0.55), mw, 0.0), "teal")
    p.add(bb(-3.8, 3.8, 1.8, 1.996, 0.0, 4.84), lambda c, n: "lteal" if n.y < -0.5 else "cream")
    mb = fr((0, 2.0, 0), "+y")
    p.add(decal(rect(-3.8, 3.8, 0.0, 0.55), mb, 0.0), "teal")
    p.add(decal(rect(-3.8, 3.8, 3.9, 4.08), mb, 0.0), "orange")
    p.add(bb(-4.0, 4.0, FY - 0.05, 2.0, 4.82, 4.98, 0.03, 1), lambda c, n: "cream")
    p.add(decal(rect(-3.7, 3.7, -(FY + 0.17), -(FY + 0.05)), fr((0, 0, 4.816), "-z"), 0.0), "glow")
    # estanterias
    for sx in (-1, 0, 1):
        x = sx * 3.66
        p.add(drop_faces(bb(x - 0.06, x + 0.06, 1.2, 1.8, 0.0, 4.5), lambda c, n: n.y > 0.5 or n.z < -0.5), "white")
    for z in (1.35, 2.3, 3.2, 4.06):
        p.add(drop_faces(bb(-3.72, 3.72, 1.2, 1.8, z - 0.06, z), lambda c, n: n.y > 0.5), lambda c, n: "white" if n.z > 0.5 else "cream2")
    boxes = [
        (1.35, [(-3.3, 0.55, 0.42, "card"), (-2.65, 0.5, 0.55, "teal"), (-2.0, 0.6, 0.38, "dcard"), (-1.2, 0.55, 0.5, "orange"),
                (0.5, 0.6, 0.45, "card"), (1.3, 0.5, 0.6, "cream"), (2.2, 0.55, 0.4, "teal"), (3.05, 0.6, 0.5, "dcard")]),
        (2.3, [(-3.1, 0.5, 0.5, "orange"), (-2.4, 0.55, 0.36, "card"), (-1.0, 0.45, 0.45, "lteal"), (0.6, 0.55, 0.5, "dcard"),
               (1.5, 0.5, 0.38, "orange"), (2.9, 0.6, 0.55, "card")]),
        (3.2, [(-3.15, 0.55, 0.48, "teal"), (-2.4, 0.5, 0.36, "cream"), (-1.6, 0.6, 0.42, "card"), (1.6, 0.55, 0.45, "orange"),
               (2.35, 0.5, 0.36, "dcard"), (3.1, 0.55, 0.5, "teal")]),
    ]
    for z, row in boxes:
        for x, w, h, col in row:
            p.add(drop_faces(bb(x - w / 2, x + w / 2, 1.3, 1.72, z, z + h), lambda c, n: n.z < -0.5 or n.y > 0.5), col)
    A = [math.radians(a) for a in (200, 235, 270, 305, 340)]
    for x, col in zip((-3.0, -2.15, -1.3, 0.85, 1.7, 2.55), ("orange", "teal", "red", "teal", "orange", "lilac")):
        z = 4.06
        p.add(elathe([(0.19, z), (0.185, z + 0.06), (0.15, z + 0.13), (0.08, z + 0.18), (0.0, z + 0.195)], 8, k=0.92, cy=1.52, cap0=False, a0=math.pi / 8, m=M((x, 0, 0))), col, 50)
        vis = [(0.185 * math.cos(a), 0.17 * math.sin(a)) for a in A] + [(0.21 * math.cos(a), 0.325 * math.sin(a)) for a in reversed(A)]
        vis = [(x + u, 1.52 + v) for u, v in vis]
        p.add(prism(vis, 0.022, M((0, 0, z + 0.011))), col, 30)
        p.add(cyl(0.025, 0.02, (x, 1.52, z + 0.19), seg=6), "cream")
    # toldo de rayas naranja / turquesa
    prof = [(-0.86, 4.86), (-1.06, 4.96), (-1.36, 5.0), (-1.64, 4.97), (-1.87, 4.88), (-2.0, 4.76)]
    xs = [-4.0 + 0.8 * i for i in range(11)]
    rows = [[(x, y, z) for x in xs] for y, z in prof]
    aw = sheet(rows, 0.05)

    def stripe(c, n):
        i = int(math.floor((c.x + 4.0) / 0.8 + 1e-4))
        if abs(n.x) > 0.7:
            return "orange"
        return "orange" if i % 2 == 0 else "teal"
    p.add(aw, stripe, 40)
    # cartel colgante (sin texto)
    for x in (-0.8, 0.8):
        p.add(bar((x, -0.53, 4.6), (x, -0.53, 4.83), 0.03, 0.03, caps=False), "steel")
    p.add(bb(-1.1, 1.1, -0.56, -0.5, 4.1, 4.62, 0.02, 1), "teal")
    ms = fr((0, -0.56, 0), "-y")
    p.add(decal(rrect(0, 4.36, 2.06, 0.42, 0.06, 1), ms, 0.004), "cream")
    p.add(decal(rrect(0, 4.36, 1.96, 0.32, 0.04, 1), ms, 0.008), "teal")
    p.add(decal([(-0.17, 4.24), (0.17, 4.24), (0.14, 4.44), (-0.14, 4.44)], ms, 0.012), "orange")
    p.add(arc_strip(0.0, 4.44, 0.06, 0.09, 0, 180, 4, ms, 0.012), "orange")
    for sx in (-1, 1):
        p.add(decal(circ(sx * 0.62, 4.36, 0.05, 8), ms, 0.012), "cream")
        p.add(decal(circ(sx * 0.82, 4.36, 0.035, 8), ms, 0.012), "cream")
    return p


# ---------------------------------------------------------------- 5. Gorros
# Todos se modelan sobre la cabeza del tripulante (coordenadas del personaje en Blender: Z arriba,
# cara hacia -Y). La cabeza es la punta de la capsula: elipsoide de radios 0,8 (X), 0,688 (Y), 1,0 (Z)
# con centro en Z = 3,55; arriba llega a 4,55. La diadema de los cascos (y 0..0,1) sobresale 0,12
# de la piel y llega a 4,67. Cada gorro tiene un borde inferior plano a la altura zb; el borde
# encierra la diadema (en X) y la cabeza (en Y) y la parte de abajo va cerrada.

HEAD_CENTRE = Vector((0.0, -0.0405, 4.11))   # centro de la caja de Head_Geo (pivote de la MeshPart Head)


def hat_role(main, inner="ddark", zb=0.0):
    def f(c, n):
        if n.z < -0.95 and c.z < zb + 0.006:
            return inner
        return main
    return f


def front_y(prof, x, z, k=None):
    """y de la superficie frontal (-Y) de un elathe en (x, z)."""
    for (r0, z0, *k0), (r1, z1, *k1) in zip(prof, prof[1:]):
        if z0 <= z <= z1 and r0 > 1e-6:
            t = (z - z0) / (z1 - z0) if z1 > z0 else 0.0
            r = r0 + (r1 - r0) * t
            ka = k0[0] if k0 else k
            kb = k1[0] if k1 else ka
            kk = ka + (kb - ka) * t
            return -kk * r * math.sqrt(max(0.0, 1.0 - (x / r) ** 2))
    return None


def p_gorra_piloto():
    zb = 4.30
    p = Prop("GorraPiloto", (1.6, 1.8, 0.8), 600, hat={"zb": zb})
    prof = [(0.738, zb, 0.72), (0.742, zb + 0.24, 0.72), (0.752, zb + 0.29, 0.75), (0.80, zb + 0.56, 0.905),
            (0.79, zb + 0.68, 0.92), (0.56, zb + 0.765, 0.92), (0.0, zb + 0.80)]
    tilt = [0.0, 0.0, 0.015, 0.05, 0.05, 0.035, 0.0]

    def zm(i, a):
        return tilt[i] * (-math.sin(a))

    def role(c, n):
        if n.z < -0.95 and c.z < zb + 0.006:
            return "ddark"
        if c.z < zb + 0.24:
            return "navy"
        if c.z < zb + 0.30:
            return "gold"
        return "white"
    p.add(elathe(prof, 20, zmod=zm, a0=math.radians(-90)), role, 40)
    # visera
    A = [math.radians(a) for a in range(-162, -17, 14)]
    rows = []
    for t in (0.0, 0.5, 1.0):
        row = []
        for a in A:
            s = math.sin(math.pi * (a - A[0]) / (A[-1] - A[0])) ** 0.55
            xi, yi = 0.725 * math.cos(a), 0.725 * 0.72 * math.sin(a)
            xo, yo = 0.80 * math.cos(a), 1.075 * math.sin(a)
            x = xi + (xo - xi) * t * s
            y = yi + (yo - yi) * t * s
            z = zb + 0.036 + 0.05 * (1.0 - t * s) - 0.0 * t
            row.append((x, y, z))
        rows.append(row)
    p.add(sheet(rows, 0.036), "black", 35)
    # cordon dorado y botones
    cord = [(0.758 * math.cos(math.radians(a)), 0.758 * 0.72 * math.sin(math.radians(a)), zb + 0.12) for a in range(-155, -24, 13)]
    p.add(tube(cord, lambda u: 0.02, k=4, steps=1, up=(0, 0, 1), phase=0.5), "gold", 60)
    for a in (-155, -25):
        aa = math.radians(a)
        q = Vector((0.745 * math.cos(aa), 0.745 * 0.72 * math.sin(aa), zb + 0.12))
        nrm = Vector((math.cos(aa) / 0.745, math.sin(aa) / (0.745 * 0.72 ** 2), 0)).normalized()
        p.add(cyl(0.04, 0.03, m=Matrix.Translation(q) @ frame_from_normal(nrm), seg=6), "gold", 40)
    # insignia de alas
    zc = zb + 0.43
    yc = front_y(prof, 0.0, zc - 0.0)
    t = Vector((0, (front_y(prof, 0.0, zb + 0.5) - front_y(prof, 0.0, zb + 0.36)), 0.14)).normalized()
    mb = frame((0, yc, zc + 0.033), (1, 0, 0), t)

    def onto(co):
        return (co.x, front_y(prof, co.x, co.z - 0.033) - 0.012, co.z)
    wing = [(0.05, 0.03), (0.17, 0.065), (0.27, 0.07), (0.235, 0.04), (0.205, 0.03), (0.215, 0.005), (0.17, 0.0), (0.175, -0.025), (0.05, -0.03)]
    for sx in (-1, 1):
        pts = [(sx * x, y) for x, y in wing]
        p.add(wrap(decal(pts, mb, 0.0), onto), "gold")
    p.add(wrap(decal(circ(0, 0, 0.065, 10), mb, 0.0), onto), "gold")
    p.add(wrap(decal(circ(0, 0, 0.04, 8), mb, 0.0), lambda co: (co.x, onto(co)[1] - 0.004, co.z)), "teal")
    return p


def p_gorro_helice():
    zb = 4.35
    k = 0.72
    p = Prop("GorroHelice", (1.4, 1.4, 1.2), 600, hat={"zb": zb})
    prof = [(0.705, zb), (0.725, zb + 0.025), (0.725, zb + 0.08), (0.70, zb + 0.105), (0.67, zb + 0.21),
            (0.57, zb + 0.31), (0.38, zb + 0.39), (0.0, zb + 0.43)]
    gores = ["orange", "yellow", "teal", "red"]

    def role(c, n):
        if n.z < -0.95 and c.z < zb + 0.006:
            return "ddark"
        if c.z < zb + 0.104:
            return "teal"
        a = math.atan2(c.y / k, c.x)
        return gores[int(math.floor((a + math.pi) / (math.pi / 4))) % 4]
    p.add(elathe(prof, 16, k=k), role, 40)
    A = [math.radians(a) for a in range(-140, -39, 12)]
    inner = [(0.70 * math.cos(a), 0.70 * k * math.sin(a)) for a in A]
    outer = [(0.74 * math.cos(a), (0.70 * k + 0.2 * math.sin(math.pi * (a - A[0]) / (A[-1] - A[0])) ** 0.7) * math.sin(a)) for a in A]
    p.add(prism(inner + outer[::-1], 0.032, M((0, 0, zb + 0.016))), "teal", 35)
    top = zb + 0.43
    p.add(cyl(0.035, 0.3, (0, 0, top - 0.03), seg=6, cap0=False, cap1=False), "metal")
    hz = top + 0.27
    p.add(cyl(0.075, 0.08, (0, 0, hz - 0.04), seg=8), "red")
    blade = [(0.06, -0.04), (0.25, -0.085), (0.52, -0.075), (0.645, 0.0), (0.52, 0.075), (0.25, 0.085), (0.06, 0.04)]
    for sx, col in ((1, "orange"), (-1, "teal")):
        pts = [(sx * x, y) for x, y in blade]
        p.add(prism(pts, 0.024, M((0, 0, hz), (sx * 18, 0, 0))), col, 30)
    p.add(lathe([(0.05, hz + 0.04), (0.035, hz + 0.075), (0.0, hz + 0.09)], 8), "yellow")
    return p


def p_gorro_chef():
    zb = 4.33
    p = Prop("GorroChef", (1.3, 1.3, 1.4), 600, hat={"zb": zb})
    prof = [(0.712, zb, 0.74), (0.716, zb + 0.07, 0.74), (0.722, zb + 0.35, 0.75), (0.735, zb + 0.39, 0.76),
            (0.775, zb + 0.47, 0.84), (0.80, zb + 0.63, 0.87), (0.79, zb + 0.83, 0.88), (0.72, zb + 1.02, 0.88),
            (0.59, zb + 1.19, 0.88), (0.38, zb + 1.32, 0.88), (0.0, zb + 1.4)]
    amp = [0, 0, 0, 0, 0.018, 0.03, 0.03, 0.03, 0.03, 0.025, 0]

    def rm(i, a):
        return 1.0 + amp[i] * math.cos(12 * a)
    p.add(elathe(prof, 24, rmod=rm, a0=math.radians(-90)), hat_role("white", "cream2", zb), 55)
    zl = zb + 0.19
    yl = front_y(prof, 0.0, zl)
    ml = fr((0, yl - 0.008, zl), "-y")

    def onto(co):
        y = front_y(prof, co.x, co.z)
        return (co.x, y - (yl - co.y) if y is not None else co.y, co.z)
    p.add(elathe([(0.728, zb + 0.29, 0.745), (0.729, zb + 0.33, 0.745)], 24, cap0=False, cap1=False, a0=math.radians(-90)), "teal", 40)
    sub = Prop("_", None, 0)
    logo(sub, ml, 0.13, step=0.004, seg=14)
    for bm, r, a in sub.parts:
        p.add(wrap(bm, onto), r, a)
    return p


def p_sombrero_vaquero():
    zb = 4.28
    k = 0.73
    p = Prop("SombreroVaquero", (2.4, 2.2, 0.9), 600, hat={"zb": zb})
    prof = [(0.745, zb, k), (0.742, zb + 0.06, k), (0.735, zb + 0.22, 0.74), (0.715, zb + 0.58, 0.75),
            (0.66, zb + 0.79, 0.76), (0.50, zb + 0.90, 0.77), (0.25, zb + 0.87, 0.77), (0.0, zb + 0.81)]

    def rm(i, a):
        if i < 4:
            return 1.0
        d = min(abs(a - math.radians(-90 + s * 38)) for s in (-1, 1))
        return 1.0 - 0.07 * math.exp(-(d / 0.32) ** 2) * (1.0 if i < 6 else 0.6)

    def zm(i, a):
        return -0.05 * max(0.0, -math.sin(a)) if 4 <= i <= 6 else 0.0
    p.add(elathe(prof, 20, rmod=rm, zmod=zm, a0=math.radians(-90)), hat_role("tan", "dtan", zb), 62)
    p.add(elathe([(0.757, zb + 0.07, k), (0.753, zb + 0.2, 0.742)], 20, cap0=False, cap1=False, a0=math.radians(-90)), "teal", 40)
    p.add(decal(rrect(0, 0, 0.12, 0.1, 0.02, 1), fr((0.757, 0.0, zb + 0.135), "+x"), 0.006), "gold")
    rows = []
    for t in (0.0, 0.45, 1.0):
        row = []
        for j in range(20):
            a = math.radians(-90 + 18 * j)
            xi, yi = 0.73 * math.cos(a), 0.73 * k * math.sin(a)
            xo, yo = 1.2 * math.cos(a), 1.1 * math.sin(a)
            x, y = xi + (xo - xi) * t, yi + (yo - yi) * t
            z = zb + 0.04 + 0.3 * math.cos(a) ** 2 * t ** 1.8
            row.append((x, y, z))
        rows.append(row)
    p.add(sheet(rows, 0.04, closed_u=True), lambda c, n: "tan" if n.z > -0.3 else "dtan", 55)
    return p


def p_gorro_cono():
    zb = 4.42
    p = Prop("GorroCono", (1.2, 1.2, 1.4), 600, hat={"zb": zb})
    p.add(rr_loft(1.45, 1.45, 0.2, 2, [(0.0, zb), (0.0, zb + 0.05), (0.03, zb + 0.08)]), hat_role("orange", "dorange", zb), 40)
    z0, z1 = zb + 0.08, zb + 1.38
    r0, r1 = 0.6, 0.075

    def r_at(z):
        return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    zs = [z0, z0 + 0.03, zb + 0.5, zb + 0.66, zb + 0.84, zb + 0.97, zb + 1.33]
    prof = [(r_at(z) + (0.015 if i == 0 else 0.0), z) for i, z in enumerate(zs)] + [(0.05, zb + 1.375), (0.0, zb + 1.4)]

    def role(c, n):
        if zb + 0.5 < c.z < zb + 0.66 or zb + 0.84 < c.z < zb + 0.97:
            return "white"
        return "orange"
    p.add(lathe(prof, 14, cap0=False), role, 40)
    return p


def p_corona():
    zb = 4.40
    k = 0.804
    p = Prop("Corona", (1.3, 1.3, 0.7), 600, hat={"zb": zb})
    seg = 20
    bm = bmesh.new()
    ro0, ro1, th = 0.66, 0.69, 0.04
    cols = []

    def ztop(a):
        ph = ((a + math.pi / 2) / (2 * math.pi / 5)) % 1.0
        return zb + 0.32 + 0.3 * abs(1.0 - 2.0 * ph)
    for j in range(seg):
        a = -math.pi / 2 + 2 * math.pi * j / seg
        ca, sa = math.cos(a), math.sin(a)
        zt = ztop(a)
        pts = [(ro0, zb), (ro0 + 0.012, zb + 0.13), (ro1, zt), (ro1 - th, zt), (ro0 - th, zb)]
        cols.append([bm.verts.new((r * ca, k * r * sa, z)) for r, z in pts])
    for j in range(seg):
        a, b = cols[j], cols[(j + 1) % seg]
        for q in range(5):
            q2 = (q + 1) % 5
            bm.faces.new((a[q], b[q], b[q2], a[q2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    p.add(bm, "gold", 40)
    for m_ in range(5):
        a = -math.pi / 2 + 2 * math.pi * m_ / 5
        p.add(ico(0.048, (ro1 * math.cos(a), k * ro1 * math.sin(a), ztop(a) + 0.032)), "gold", 60)
        nrm = Vector((math.cos(a), math.sin(a) / k, 0)).normalized()
        q = Vector(((ro0 + 0.012) * math.cos(a), k * (ro0 + 0.012) * math.sin(a), zb + 0.075))
        p.add(octa((0.055, 0.075, 0.03), Matrix.Translation(q + nrm * 0.008) @ frame_from_normal(nrm)), "velvet" if m_ % 2 == 0 else "teal", 30)
    cush = [(0.625, zb, k), (0.615, zb + 0.13, k), (0.55, zb + 0.31, k), (0.35, zb + 0.45, k), (0.0, zb + 0.50)]
    p.add(elathe(cush, 16, k=k), hat_role("velvet", "ddark", zb), 50)
    p.add(ico(0.065, (0, 0, zb + 0.545), 1), "gold", 60)
    return p


def p_auriculares2():
    p = Prop("Auriculares2", (2.2, 0.8, 1.4), 600, hat={"zb": None})
    yc, zc = 0.05, 3.93
    tau = math.radians(12)
    for sx in (-1, 1):
        u = Vector((sx * math.cos(tau), 0, math.sin(tau)))
        org = Vector((sx * 0.742, yc, zc))
        m = frame(org, (0, 1, 0), u.cross(Vector((0, 1, 0))))
        p.add(lathe([(0.0, 0.215), (0.245, 0.215), (0.245, 0.0), (0.355, 0.0), (0.38, 0.05), (0.38, 0.115)], 12, m, cap0=False, cap1=False, a0=0.0), "rubber", 50)
        p.add(lathe([(0.38, 0.115), (0.40, 0.135), (0.40, 0.27)], 12, m, cap0=False, cap1=False, a0=0.0), "orange", 50)
        p.add(lathe([(0.40, 0.27), (0.30, 0.30), (0.0, 0.312)], 12, m, cap0=False, cap1=False, a0=0.0), "cream", 30)
        p.add(decal(circ(0, 0, 0.17, 12), m, 0.312), "teal")
    ax = 0.8 * math.sqrt(1 - (yc / 0.688) ** 2)

    def off_curve(dfn, a0, n):
        pts = []
        for i in range(n):
            a = a0 + (math.pi - 2 * a0) * i / (n - 1)
            ca, sa = math.cos(a), math.sin(a)
            nv = Vector((ca / ax, 0, sa)).normalized()
            pts.append(Vector((ax * ca, yc, 3.55 + sa)) + nv * dfn(a))
        return pts
    a0 = math.radians(35)
    strap = off_curve(lambda a: 0.185, a0, 9)
    p.add(tube(strap, lambda u: (0.15, 0.05), k=6, steps=1, up=(0, 1, 0), caps=False), "teal", 60)
    arc = off_curve(lambda a: 0.2 + 0.2 * math.sin(a) ** 2, a0, 9)
    p.add(tube(arc, lambda u: 0.026, k=4, steps=1, up=(0, 1, 0), caps=False, phase=0.5), "metal", 60)
    return p


def p_gorro_pato():
    zb = 4.35
    p = Prop("GorroPato", (1.4, 1.6, 1.2), 600, hat={"zb": zb})
    prof = [(0.705, zb, 0.72), (0.745, zb + 0.1, 0.82), (0.74, zb + 0.25, 0.90), (0.67, zb + 0.41, 0.94),
            (0.51, zb + 0.54, 0.95), (0.28, zb + 0.61, 0.95), (0.0, zb + 0.63)]
    bulge = [0.0, 0.04, 0.08, 0.08, 0.05, 0.0, 0.0]

    def rm(i, a):
        return 1.0 + bulge[i] * max(0.0, -math.sin(a)) ** 2
    p.add(elathe(prof, 14, rmod=rm, a0=math.radians(-90)), hat_role("duck", "yellow", zb), 60)
    hc = Vector((0.0, -0.2, zb + 0.92))
    hr = 0.40
    p.add(ellipsoid((hr, hr * 0.95, hr), Matrix.Translation(hc), 12, 6), "duck", 60)
    p.add(ellipsoid((0.22, 0.17, 0.075), Matrix.Translation((0, -0.62, zb + 0.85)) @ Matrix.Rotation(math.radians(-10), 4, "X"), 8, 5), "beak", 60)
    p.add(ellipsoid((0.22, 0.27, 0.12), Matrix.Translation((0, 0.55, zb + 0.43)) @ Matrix.Rotation(math.radians(42), 4, "X"), 6, 4), "duck", 60)
    for sx in (-1, 1):
        p.add(ellipsoid((0.08, 0.3, 0.17), Matrix.Translation((sx * 0.68, 0.1, zb + 0.27)) @ Matrix.Rotation(math.radians(14), 4, "X"), 6, 4), "duck", 60)
        az, el = math.radians(33), math.radians(20)
        d = Vector((sx * math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
        ec = hc + Vector((d.x * hr, d.y * hr * 0.95, d.z * hr)) * 0.99
        nrm = Vector((d.x, d.y / 0.95, d.z)).normalized()
        fm = Matrix.Translation(ec) @ frame_from_normal(nrm)
        p.add(ellipsoid((0.06, 0.08, 0.035), fm, 6, 4), "black", 60)
        p.add(ellipsoid((0.018, 0.018, 0.012), fm @ Matrix.Translation((0.018 * sx, 0.03, 0.028)), 4, 3), "white", 60)
    return p


BUILDERS = [p_piolet, p_escaner, p_contenedor, p_tienda,
            p_gorra_piloto, p_gorro_helice, p_gorro_chef, p_sombrero_vaquero, p_gorro_cono, p_corona, p_auriculares2, p_gorro_pato]
HATS = ["GorraPiloto", "GorroHelice", "GorroChef", "SombreroVaquero", "GorroCono", "Corona", "Auriculares2", "GorroPato"]


# ---------------------------------------------------------------- malla final, paleta, FBX

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
    size = p.size if p.hat is None else tuple(round(raw[i], 2) for i in range(3))
    p.final_size = size
    sc = [size[i] / raw[i] for i in range(3)]
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    T = Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)) @ Matrix.Translation(-off)
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
    return verts, faces, uvs, nrms, tris, raw, sc, off


def palette_image():
    img = bpy.data.images.new("kit_extra_palette", 64, 64, alpha=True)
    px = [0.5] * (64 * 64 * 4)
    cell = 64 // GRID
    for i in range(GRID * GRID):
        r, g, b = hex_rgb(PAL[i][1])
        gx, gy = i % GRID, i // GRID
        for y in range(gy * cell, gy * cell + cell):
            for x in range(gx * cell, gx * cell + cell):
                o = (y * 64 + x) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "kit_extra_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def palette_material(img):
    mat = bpy.data.materials.new("KitExtra_Palette")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.name = "PaletteTex"
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.6
    return mat


def preview_glow(mat, strength=1.6):
    """Solo para los renders (despues de exportar): la ultima fila de la paleta emite luz."""
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.get("PaletteTex")
    uvn = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = (GRID - 1) / GRID
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = strength
    nt.links.new(uvn.outputs["UV"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], gt.inputs[0])
    nt.links.new(gt.outputs[0], mul.inputs[0])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    nt.links.new(mul.outputs[0], bsdf.inputs["Emission Strength"])
    if arg("--debug-backface"):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        nt.links.new(geo.outputs["Backfacing"], mix.inputs[0])
        nt.links.new(tex.outputs["Color"], mix.inputs[6])
        mix.inputs[7].default_value = (1.0, 0.0, 1.0, 1.0)
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])


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


def rbx(v):
    """Blender (x, y, z) -> ejes de Roblox del manifest (x, y = arriba, z = fondo)."""
    return [round(v[0], 3), round(v[2], 3), round(v[1], 3)]


# ---------------------------------------------------------------- tripulante (para medir y para los renders)

TRIP = {}


def load_tripulante():
    if TRIP or not os.path.exists(TRIP_BLEND):
        return TRIP
    with bpy.data.libraries.load(TRIP_BLEND, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    objs = [o for o in dst.objects if o is not None]
    coll = bpy.data.collections.new("Tripulante")
    bpy.context.scene.collection.children.link(coll)
    for o in objs:
        coll.objects.link(o)
        o.hide_render = True
    TRIP["objs"] = objs
    TRIP["coll"] = coll
    TRIP["head"] = next(o for o in objs if o.name.startswith("Head_Geo"))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    h = TRIP["head"]
    me = h.evaluated_get(dg).to_mesh()
    TRIP["head_verts"] = [h.matrix_world @ v.co for v in me.vertices]
    TRIP["head_polys"] = [tuple(pl.vertices) for pl in me.polygons]
    h.evaluated_get(dg).to_mesh_clear()
    hv = TRIP["head_verts"]
    mn = Vector([min(v[i] for v in hv) for i in range(3)])
    mx = Vector([max(v[i] for v in hv) for i in range(3)])
    TRIP["head_centre"] = (mn + mx) / 2
    TRIP["head_bbox"] = (mn, mx)
    return TRIP


def fit_check(name, ob, zb):
    """Pone el gorro en su sitio y mira: puntos de la cabeza que quedan al aire por encima del borde,
    y distancia del borde a la cabeza (0 = apoyado; mucho = flotando)."""
    if not TRIP:
        return None
    hv = TRIP["head_verts"]
    me = ob.data
    vw = [ob.matrix_world @ v.co for v in me.vertices]
    hb = BVHTree.FromPolygons(vw, [tuple(pl.vertices) for pl in me.polygons])
    headb = BVHTree.FromPolygons(hv, TRIP["head_polys"])
    tested = exposed = 0
    worst = 0.0
    if zb is not None:
        for v in hv:
            if v.z <= zb + 0.004:
                continue
            tested += 1
            radial = Vector((v.x, v.y, 0.0))
            dirs = [Vector((0, 0, 1))] + ([radial.normalized()] if radial.length > 1e-6 else [])
            for d in dirs:
                if hb.ray_cast(v, d, 4.0)[0] is None:
                    exposed += 1
                    break
        rim = [v for v in vw if v.z < zb + 0.01]
    else:
        rim = vw
    ds = sorted((headb.find_nearest(v)[3] for v in rim))
    return {"tested": tested, "exposed": exposed, "rim_min": ds[0] if ds else None, "rim_med": ds[len(ds) // 2] if ds else None}


# ---------------------------------------------------------------- renders

TEMP = []


def keep(o):
    TEMP.append(o)
    return o


def clear_temp():
    for o in TEMP:
        try:
            bpy.data.objects.remove(o)
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


PROP_MESH = {}


def prop_mesh(name):
    if name in PROP_MESH:
        return PROP_MESH[name]
    path = os.path.join(PROPS, name + ".fbx")
    me = None
    if os.path.exists(path):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        src = next((o for o in new if o.type == "MESH"), None)
        if src is not None:
            me = src.data.copy()
            me.transform(src.matrix_world)
        for o in new:
            bpy.data.objects.remove(o)
    PROP_MESH[name] = me
    return me


def put_prop(name, mw):
    me = prop_mesh(name)
    if me is None:
        return None
    o = bpy.data.objects.new(name + "_p", me)
    bpy.context.scene.collection.objects.link(o)
    o.matrix_world = mw
    return keep(o)


PLAYER = {"Lima": "8BD24C", "Lavanda": "A07CF2", "Chicle": "F27BB5", "Sol": "F5CD3D"}


def trip_material(color):
    key = "TripMat_" + color
    if key in MATS:
        return MATS[key]
    base = next((m for m in bpy.data.materials if m.name.startswith("Tripulante_Palette")), None)
    if base is None:
        return None
    m = base.copy()
    m.name = key
    n = m.node_tree.nodes.get("PlayerColor")
    if n is not None:
        n.outputs[0].default_value = (*lin(hex_rgb(PLAYER[color])), 1.0)
    MATS[key] = m
    return m


def tripulante(mw=Matrix(), color="Lavanda"):
    """Copia del tripulante (en pose de reposo) colocada con mw."""
    if not TRIP:
        return []
    mat = trip_material(color)
    made = []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in TRIP["objs"]:
        if o.type != "MESH":
            continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        if mat is not None:
            me.materials.clear()
            me.materials.append(mat)
        c = bpy.data.objects.new(o.name + "_r", me)
        bpy.context.scene.collection.objects.link(c)
        c.matrix_world = mw @ o.matrix_world
        made.append(keep(c))
    return made


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
    pct = arg("--pct")
    scene.render.resolution_percentage = int(pct) if isinstance(pct, str) else 100
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


def camera_look(loc, target, lens):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cd.sensor_fit = "HORIZONTAL"
    cd.clip_start = 0.05
    cd.clip_end = 2000
    co = bpy.data.objects.new("Cam", cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = co
    return keep(co)


def camera_fit(objs_list, el, az, lens, mx=0.9, my=0.86, extra=(), pts=None):
    scene = bpy.context.scene
    bpy.context.view_layer.update()
    if pts is None:
        pts = [o.matrix_world @ Vector(c) for o in objs_list for c in o.bound_box]
    pts = list(pts) + [Vector(e) for e in extra]
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


def label(cam, text, w, h, px=24):
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
        hh, ww = min(a.shape[0], th), min(a.shape[1], tw[c])
        canvas[y0:y0 + hh, x0:x0 + ww] = a[:hh, :ww]
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


TILE_DIR = []


def tile_paths(tag, n):
    import tempfile
    if not TILE_DIR:
        TILE_DIR.append(tempfile.mkdtemp(prefix="kit_extra_tiles_"))
    return [os.path.join(TILE_DIR[0], "%s_%d.png" % (tag, i)) for i in range(n)]


def sheet_1(objs, threads, outdir):
    scene = bpy.context.scene
    paths = tile_paths("e1", 6)
    TW, TH = 533, 450

    def t_scan():
        studio(ground="DCE4E8", sun_rot=(48, 0, 30))
        o = inst(objs, "Escaner", (0, 0, 0), 0)
        put_prop("Maleta1", M((0.0, -2.7, 1.0), (90, 0, 8)) @ M((0, 0, 0)))
        put_prop("Maleta3", M((0.1, 2.5, 1.0), (90, 0, -5)))
        made = tripulante(M((2.75, 2.4, 0), (0, 0, 38)), "Lima")
        cam = camera_fit([o] + made, 20, 38, 50, 0.88, 0.84)
        return cam, "Escaner (+ tripulante y maletas para la escala)"

    def t_tunnel():
        studio(ground="DCE4E8", sun_rot=(60, 0, 15))
        inst(objs, "Escaner", (0, 0, 0), 0)
        put_prop("Maleta2", M((0.15, -0.3, 1.0), (90, 0, 4)))
        put_prop("Maleta1", M((-0.1, -3.0, 1.0), (90, 0, -6)))
        cam = camera_look((0.9, -9.4, 3.1), (0.0, 0.0, 2.05), 40)
        return cam, "Escaner: tunel libre 2,6 x 2,2, cintas cortas"

    def t_shop():
        studio(sun_rot=(46, 0, -28))
        o = inst(objs, "Tienda", (0, 0, 0), 0)
        made = tripulante(M((2.7, -1.4, 0), (0, 0, -26)), "Chicle")
        cam = camera_fit([o], 17, -26, 50, 0.86, 0.84)
        return cam, "Tienda (+ tripulante en la zona libre)"

    def t_bin():
        studio(sun_rot=(52, 0, -40))
        o = inst(objs, "Contenedor", (0, 0, 0), -20)
        put_prop("Maleta2", M((0, 0, 0), (0, 0, -20)) @ M((-0.55, -0.1, 0.34), (90, 0, 10)))
        put_prop("Maleta3", M((0, 0, 0), (0, 0, -20)) @ M((0.45, 0.45, 0.34), (90, 0, -78)))
        cam = camera_fit([o], 34, -20, 50, 0.9, 0.86)
        return cam, "Contenedor (+ maletas)"

    def t_axe():
        studio(sun_rot=(50, 0, -60))
        a = inst(objs, "Piolet", (-0.75, 0.45, 0), 0)
        b = inst(objs, "Piolet", mw=M((-0.25, -0.5, 0.125), (0, 90, 14)))
        cam = camera_fit([a, b], 26, 38, 50, 0.86, 0.84)
        return cam, "Piolet (pico a -Y, azuela a +Y)"

    def t_hats():
        studio(sun_rot=(52, 0, -36))
        lay = [("GorraPiloto", -2.9, 0.9), ("GorroHelice", -1.15, 0.9), ("GorroChef", 0.55, 0.9), ("SombreroVaquero", 2.7, 0.9),
               ("GorroCono", -2.9, -1.1), ("Corona", -1.15, -1.1), ("Auriculares2", 0.6, -1.1), ("GorroPato", 2.6, -1.1)]
        made = [inst(objs, n, (x, y, 0), -18) for n, x, y in lay]
        cam = camera_fit(made, 24, -12, 50, 0.94, 0.88)
        return cam, "Gorros (cosmeticos)"
    for i, fn in enumerate((t_scan, t_tunnel, t_shop, t_bin, t_axe, t_hats)):
        render_setup(scene, threads, TW + (1 if i % 3 < 1600 % 3 else 0), TH)
        cam, txt = fn()
        label(cam, txt, scene.render.resolution_x, TH)
        render_to(paths[i])
        clear_temp()
    composite(paths, 3, 2, 1600, 900, os.path.join(outdir, "extra_1.png"))


def sheet_2(objs, threads, outdir, anchors):
    scene = bpy.context.scene
    paths = tile_paths("e2", 8)
    cols = ["Lavanda", "Lima", "Chicle", "Sol", "Sol", "Lavanda", "Chicle", "Lima"]
    for i, name in enumerate(HATS):
        render_setup(scene, threads, 400, 450)
        studio(sun_rot=(50, 0, -40))
        made = tripulante(Matrix(), cols[i])
        hc = TRIP["head_centre"] if TRIP else HEAD_CENTRE
        org = hc + Vector((anchors[name][0], anchors[name][2], anchors[name][1]))
        h = inst(objs, name, tuple(org), 0)
        head = next((o for o in made if o.name.startswith("Head_Geo")), None)
        pts = [h.matrix_world @ Vector(c) for c in h.bound_box]
        if head is not None:
            pts += [head.matrix_world @ Vector(c) for c in head.bound_box]
        pts += [Vector((sx * 0.9, sy * 0.8, 3.0)) for sx in (-1, 1) for sy in (-1, 1)]
        cam = camera_fit([], 8, 30, 50, 0.86, 0.80, pts=pts)
        label(cam, name, 400, 450, px=22)
        render_to(paths[i])
        clear_temp()
    composite(paths, 4, 2, 1600, 900, os.path.join(outdir, "extra_2.png"))


# ---------------------------------------------------------------- main

def checks(objs):
    msgs = []
    if "Escaner" in objs:
        o = objs["Escaner"]
        TX, TZ0, TZ1 = SCAN["TX"], SCAN["TZ0"], SCAN["TZ1"]
        bad = 0
        flap = 0
        top = -1e9
        for pl in o.data.polygons:
            c = pl.center
            if abs(c.x) < TX - 0.005 and TZ0 + 0.005 < c.z < TZ1 - 0.005:
                if c.z > 2.44 and abs(abs(c.y) - (SCAN["HY"] + 0.05)) < 0.03:
                    flap += 1
                else:
                    bad += 1
        for v in o.data.vertices:
            if abs(v.co.x) <= TX + 1e-4 and v.co.z < TZ0 + 0.05:
                top = max(top, v.co.z)
        msgs.append("ESCANER tunel: caras dentro del hueco libre = %d (cintas %d), punto mas alto de la cinta = %.4f" % (bad, flap, top))
    if "Tienda" in objs:
        o = objs["Tienda"]
        zmin = min((v.co.z for v in o.data.vertices if v.co.y < TIENDA["front"] - 0.001), default=None)
        ymin = min(v.co.y for v in o.data.vertices if v.co.z < 4.6)
        msgs.append("TIENDA zona libre: lo mas bajo delante del mostrador z = %.3f; lo mas adelantado bajo z 4,6: y = %.3f" % (zmin, ymin))
    return msgs


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    img = palette_image()
    mat = palette_material(img)
    load_tripulante()
    if TRIP:
        hc = TRIP["head_centre"]
        mn, mx = TRIP["head_bbox"]
        print("HEAD_GEO bbox min %.4f %.4f %.4f max %.4f %.4f %.4f centre %.4f %.4f %.4f" % (*mn, *mx, *hc))
    hc = TRIP["head_centre"] if TRIP else HEAD_CENTRE
    only = arg("--only")
    only = set(only.split(",")) if isinstance(only, str) else None
    objs = {}
    manifest = []
    anchors = {}
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
        print("PIECE %-16s tris %5d / %5d %s  raw %.3f x %.3f x %.3f  fit %.4f %.4f %.4f  off %.3f %.3f %.3f%s" % (
            p.name, tris, p.budget, flag, raw.x, raw.y, raw.z, sc[0], sc[1], sc[2], off.x, off.y, off.z, warn))
        if not arg("--no-export"):
            export_fbx(ob)
        dim = ob.dimensions
        e = {"nombre": p.name, "archivo": p.name + ".fbx", "tamano": [round(dim.x, 3), round(dim.z, 3), round(dim.y, 3)], "triangulos": tris}
        if p.hat is not None:
            a = off - hc
            e["anclaje"] = rbx(a)
            e["anclaje_centro"] = rbx(a + Vector((0, 0, dim.z / 2)))
            anchors[p.name] = e["anclaje"]
            ob.location = off
            bpy.context.view_layer.update()
            fc = fit_check(p.name, ob, p.hat["zb"])
            if fc:
                print("FIT %-16s zb %s  head verts above rim %d, uncovered %d, rim->head min %.3f median %.3f" % (
                    p.name, p.hat["zb"], fc["tested"], fc["exposed"], fc["rim_min"], fc["rim_med"]))
            ob.location = (0, 0, 0)
        manifest.append(e)
    for m_ in checks(objs):
        print(m_)
    if not only and not arg("--no-export"):
        with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("ALL BUDGETS OK" if ok else "SOME PIECES OVER BUDGET")
    if arg("--no-render"):
        return
    for o in objs.values():
        o.hide_render = True
    preview_glow(mat)
    threads = arg("--threads")
    threads = int(threads) if isinstance(threads, str) else 2
    which = arg("--sheets")
    which = set(which.split(",")) if isinstance(which, str) else None
    outdir = arg("--render-dir")
    outdir = outdir if isinstance(outdir, str) else OUT
    if not which or "1" in which:
        sheet_1(objs, threads, outdir)
    if (not which or "2" in which) and all(h in anchors for h in HATS):
        sheet_2(objs, threads, outdir, anchors)
    if TILE_DIR:
        import shutil
        shutil.rmtree(TILE_DIR[0], ignore_errors=True)


if __name__ == "__main__":
    main()
