import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if len(sys.argv) > 1 and os.path.isdir(sys.argv[-1]):
    OUT = sys.argv[-1]

HZB, HZT, HRB, HRT, HCB, HCT, HD = 3.98, 4.50, 0.56, 0.47, 0.50, 0.46, 0.92
ZE = 4.32
DZ = ZE - 4.04
ZROOT, ZWAIST, ZNECK, ZTOP = 2.30, 2.70, 3.42, 4.96
HOMBRO, CODO, MUNECA = Vector((0.62, 0.0, 3.17)), Vector((0.76, 0.0, 2.62)), Vector((0.84, 0.0, 2.00))
CADERA, RODILLA, TOBILLO = Vector((0.27, 0.0, 2.18)), Vector((0.27, 0.0, 1.24)), Vector((0.28, 0.0, 0.34))
HRP_Z = CADERA.z + 1.0

PALETTE = {
    "body": (0, (1.0, 1.0, 1.0, 0.0)),
    "black": (1, "1B1B21"),
    "vest": (2, "F27B2B"),
    "teal": (3, "1FA6A0"),
    "dark": (4, "34383F"),
    "gold": (5, "F0B73A"),
    "cream": (6, "FFF4E0"),
    "shoe": (7, "4A3428"),
    "sole": (8, "EDE3CF"),
    "white": (9, "F7F7F2"),
    "mouth": (10, "2B1219"),
    "tongue": (11, "E85A78"),
    "navy": (12, "2C3A5E"),
}

PLAYER_COLORS = {
    "Lima": "8BD24C",
    "Lavanda": "A07CF2",
    "Chicle": "F27BB5",
    "Sol": "F5CD3D",
}

PARTS = [
    "Head", "UpperTorso", "LowerTorso",
    "LeftUpperArm", "LeftLowerArm", "LeftHand",
    "RightUpperArm", "RightLowerArm", "RightHand",
    "LeftUpperLeg", "LeftLowerLeg", "LeftFoot",
    "RightUpperLeg", "RightLowerLeg", "RightFoot",
]


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def swatch_uv(role):
    i = PALETTE[role][0]
    return ((i % 4 + 0.5) / 4.0, (i // 4 + 0.5) / 4.0)


def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def r_cabeza(z):
    if z < HZB:
        return HRB * math.sqrt(max(0.0, 1.0 - ((HZB - z) / HCB) ** 2))
    if z > HZT:
        return HRT * math.sqrt(max(0.0, 1.0 - ((z - HZT) / HCT) ** 2))
    return HRB + (HRT - HRB) * (z - HZB) / (HZT - HZB)


def frame_from_normal(n):
    n = n.normalized()
    x = Vector((0, 0, 1)).cross(n)
    if x.length < 1e-4:
        x = Vector((1, 0, 0))
    x.normalize()
    y = n.cross(x).normalized()
    m = Matrix((x, y, n)).transposed()
    return m.to_4x4()


def core_weights(z):
    t1 = ss(2.55, 2.85, z)
    t2 = ss(3.38, 3.56, z)
    w = {"LowerTorso": 1.0 - t1, "UpperTorso": t1 * (1.0 - t2), "Head": t2}
    return {k: v for k, v in w.items() if v > 1e-4}


def core_part(c):
    if c.z < 2.70:
        return "LowerTorso"
    return "UpperTorso"


class Prim:
    def __init__(self, bm, role, part, weights, s_layer=False, angle=50.0):
        self.bm = bm
        self.role = role
        self.part = part
        self.weights = weights
        self.s_layer = s_layer
        self.angle = angle


PRIMS = []


def add(bm, role, part, weights, s_layer=False, angle=50.0):
    PRIMS.append(Prim(bm, role, part, weights, s_layer, angle))


def ellipsoid(radii, mat=Matrix(), u=20, v=14):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.transform(bm, matrix=mat @ Matrix.Diagonal((*radii, 1.0)), verts=bm.verts)
    return bm


def cylinder(radius, depth, mat=Matrix(), seg=20):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=radius, radius2=radius, depth=depth)
    bmesh.ops.transform(bm, matrix=mat, verts=bm.verts)
    return bm


def catmull(points, steps, closed=False):
    n = len(points)
    if n < 3 and not closed:
        out = []
        for i in range(n - 1):
            for k in range(steps):
                out.append(points[i].lerp(points[i + 1], k / steps))
        out.append(points[-1])
        return out
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


def tube(ctrl, radius_fn, k=12, steps=6, closed=False, up=None, caps=True, cap_rings=4):
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
    sl = bm.verts.layers.float.new("s")
    rings = []
    for i in range(n):
        u = seglen[i] / total if total > 0 else 0.0
        r = radius_fn(u)
        b = tangents[i].cross(normals[i]).normalized()
        ring = []
        for j in range(k):
            a = 2 * math.pi * j / k
            v = bm.verts.new(path[i] + (normals[i] * math.cos(a) + b * math.sin(a)) * r)
            v[sl] = seglen[i]
            ring.append(v)
        rings.append(ring)
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
    for a_i, b_i in pairs:
        ra, rb = rings[a_i], rings[b_i]
        for j in range(k):
            bm.faces.new((ra[j], ra[(j + 1) % k], rb[(j + 1) % k], rb[j]))
    if caps and not closed:
        for end in (0, n - 1):
            d = -tangents[0] if end == 0 else tangents[-1]
            r_end = radius_fn(0.0 if end == 0 else 1.0)
            b = tangents[end].cross(normals[end]).normalized()
            prev = rings[end]
            for c in range(1, cap_rings + 1):
                phi = (math.pi / 2) * c / cap_rings
                center = path[end] + d * r_end * math.sin(phi)
                if c == cap_rings:
                    pole = bm.verts.new(center)
                    pole[sl] = seglen[end]
                    for j in range(k):
                        bm.faces.new((prev[j], prev[(j + 1) % k], pole))
                    break
                rr = r_end * math.cos(phi)
                ring = []
                for j in range(k):
                    a = 2 * math.pi * j / k
                    v = bm.verts.new(center + (normals[end] * math.cos(a) + b * math.sin(a)) * rr)
                    v[sl] = seglen[end]
                    ring.append(v)
                for j in range(k):
                    bm.faces.new((prev[j], prev[(j + 1) % k], ring[(j + 1) % k], ring[j]))
                prev = ring
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ctrl_s = []
    for p in ctrl:
        best = min(range(n), key=lambda i: (path[i] - p).length)
        ctrl_s.append(seglen[best])
    return bm, ctrl_s


def revolucion(prof, m=24, n=2.0):
    bm = bmesh.new()
    rings = []
    for z, rx, ry in prof:
        if rx < 1e-5:
            rings.append([bm.verts.new((0, 0, z))])
            continue
        ring = []
        for j in range(m):
            th = -math.pi / 2 + 2 * math.pi * j / m
            c, sn = math.cos(th), math.sin(th)
            ring.append(bm.verts.new((rx * math.copysign(abs(c) ** (2 / n), c), ry * math.copysign(abs(sn) ** (2 / n), sn), z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        if len(a) == 1:
            for j in range(m):
                bm.faces.new((a[0], b[(j + 1) % m], b[j]))
        elif len(b) == 1:
            for j in range(m):
                bm.faces.new((a[j], a[(j + 1) % m], b[0]))
        else:
            for j in range(m):
                bm.faces.new((a[j], a[(j + 1) % m], b[(j + 1) % m], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def build_head():
    prof = []
    nb, nm, nt = 9, 5, 12
    for i in range(nb):
        a = math.radians(-90 + 90 * i / nb)
        prof.append((HZB + HCB * math.sin(a), HRB * math.cos(a), HRB * math.cos(a) * HD))
    for i in range(nm):
        z = HZB + (HZT - HZB) * i / nm
        prof.append((z, r_cabeza(z), r_cabeza(z) * HD))
    for i in range(nt + 1):
        a = math.radians(90 * i / nt)
        prof.append((HZT + HCT * math.sin(a), HRT * math.cos(a), HRT * math.cos(a) * HD))
    return revolucion(prof, 24)


CAMISA = [(2.34, 0.43, 0.30), (2.50, 0.445, 0.315), (2.72, 0.47, 0.33), (2.92, 0.53, 0.345), (3.10, 0.585, 0.35), (3.22, 0.60, 0.34),
          (3.31, 0.56, 0.31), (3.38, 0.44, 0.26), (3.43, 0.27, 0.20), (3.455, 0.0, 0.0)]
PELVIS = [(1.97, 0.0, 0.0), (2.00, 0.20, 0.15), (2.07, 0.36, 0.26), (2.18, 0.44, 0.31), (2.32, 0.46, 0.325), (2.46, 0.455, 0.32)]


def build_mouth(hit):
    cols, rows, w = 15, 5, 0.25
    bm = bmesh.new()
    ls = bm.verts.layers.float.new("ws")
    li = bm.verts.layers.float.new("wi")
    grid = []
    for ri in range(rows + 1):
        v = ri / rows
        row = []
        for ci in range(cols + 1):
            u = -1.0 + 2.0 * ci / cols
            zt = 3.69 + DZ + 0.055 * u * u
            t = 0.014 + 0.04 * math.sqrt(max(0.0, 1.0 - u * u))
            loc, n = hit(u * w, zt - v * t)
            vert = bm.verts.new(loc + n * 0.012)
            c = max(0.0, 1.0 - u * u) ** 0.6
            vert[ls] = (1.0 - v) * c
            vert[li] = v * c
            row.append(vert)
        grid.append(row)
    for ri in range(rows):
        for ci in range(cols):
            bm.faces.new((grid[ri][ci], grid[ri][ci + 1], grid[ri + 1][ci + 1], grid[ri + 1][ci]))
    bm.normal_update()
    if sum(f.normal.y for f in bm.faces) > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.normal_update()
    return bm


def chain_weights(bones, bounds, blend):
    def fn(s):
        w = {bones[0]: 1.0}
        for i, b in enumerate(bounds):
            t = ss(b - blend, b + blend, s)
            carry = w[bones[i]]
            w[bones[i]] = carry * (1.0 - t)
            w[bones[i + 1]] = carry * t
        return {k: v for k, v in w.items() if v > 1e-4}
    return fn


def redondeado(radii, mat, u=10, v=7, p=0.5):
    bm = ellipsoid((1.0, 1.0, 1.0), Matrix(), u, v)
    for vert in bm.verts:
        vert.co = Vector([math.copysign(abs(c) ** p, c) for c in vert.co])
    bmesh.ops.transform(bm, matrix=mat @ Matrix.Diagonal((*radii, 1.0)), verts=bm.verts)
    return bm


OJO_RADIO = 0.095
OJOS = ((-1, 1.12), (1, 0.92))
OJOS_MARCO = []
VARIANTES_OJOS = {
    "normal": (1.0, 1.0, 1.0, (0.3, -0.85), (0.3, -0.85)),
    "grande": (1.32, 1.0, 0.7, (0.0, 0.0), (0.0, 0.0)),
    "susto": (1.2, 1.0, 0.55, (0.0, -0.4), (0.0, -0.4)),
    "mareo": (1.0, 0.85, 1.0, (-0.8, 0.5), (0.6, -0.7)),
    "feliz": (1.05, 1.0, 1.3, (0.0, 0.1), (0.0, 0.1)),
    "enfado": (1.0, 0.62, 1.0, (0.45, -0.3), (0.45, -0.3)),
}
BONES_CARA = []


def ojos_render(variante):
    esc, alto, pup, pi, pd = VARIANTES_OJOS[variante]
    parte = "Ojos_" + variante
    for (sx, e, c, n), (adentro, arriba) in zip(OJOS_MARCO, (pi, pd)):
        fr = Matrix.Translation(c) @ frame_from_normal(n)
        e2 = e * esc
        add(ellipsoid((0.21 * e2, 0.21 * e2 * alto, 0.04), fr @ Matrix.Translation((0, 0, 0.07)), 20, 10), "black", parte, {"Head": 1.0})
        add(ellipsoid((0.185 * e2, 0.185 * e2 * alto, 0.065), fr @ Matrix.Translation((0, 0, 0.1)), 20, 10), "white", parte, {"Head": 1.0})
        r = OJO_RADIO * e2
        add(ellipsoid((0.08 * e2 * pup, 0.08 * e2 * pup * alto, 0.025), fr @ Matrix.Translation((-sx * adentro * r, arriba * r * alto, 0.165)), 14, 8), "black", parte, {"Head": 1.0})


LADOS = {"Left": "Izq", "Right": "Der"}
DEDOS = (("Indice", -0.195, 0.21), ("Medio", -0.065, 0.23), ("Anular", 0.065, 0.22), ("Menique", 0.195, 0.18))
PALMA = (0.13, 0.26, 0.19)
BONES_MANOS = []
AGARRE = Vector()


def seglen_hasta(camino, i):
    return sum((camino[j] - camino[j - 1]).length for j in range(1, i + 1))


def en_camino(camino, s):
    acc = 0.0
    for i in range(1, len(camino)):
        seg = (camino[i] - camino[i - 1]).length
        if acc + seg >= s:
            return camino[i - 1].lerp(camino[i], (s - acc) / seg)
        acc += seg
    return camino[-1] + (camino[-1] - camino[-2]).normalized() * (s - acc)


def falange(camino, s_punta, s_k, mano, base):
    s_m = (s_k + s_punta) / 2
    b1, b2 = base + "1", base + "2"
    BONES_MANOS.append((b1, mano, tuple(en_camino(camino, s_k)), tuple(en_camino(camino, s_m))))
    BONES_MANOS.append((b2, b1, tuple(en_camino(camino, s_m)), tuple(en_camino(camino, s_punta))))
    return chain_weights([mano, b1, b2], [s_k, s_m], 0.024)


def build_character():
    PRIMS.clear()
    BONES_MANOS.clear()
    BONES_CARA.clear()
    OJOS_MARCO.clear()
    cabeza = build_head()
    tree = BVHTree.FromBMesh(cabeza)

    def hit(x, z):
        loc, nrm, _, _ = tree.ray_cast(Vector((x, -5.0, z)), Vector((0, 1, 0)))
        return loc, nrm

    def rayo(d, z, y=0.0):
        d = Vector(d).normalized()
        loc, nrm, _, _ = tree.ray_cast(Vector((0, y, z)) + d * 3.0, -d)
        return loc, nrm

    add(cabeza, "body", "Head", {"Head": 1.0})
    add(cylinder(0.16, 0.36, Matrix.Translation((0, 0, 3.45)), 12), "body", "Head", "core")

    camisa = revolucion(CAMISA, 24, 2.6)
    ttree = BVHTree.FromBMesh(camisa)

    def frente(x, z):
        loc, nrm, _, _ = ttree.ray_cast(Vector((x, -5.0, z)), Vector((0, 1, 0)))
        return loc, nrm

    add(camisa, "cream", core_part, "core", angle=60.0)
    add(revolucion(PELVIS, 24, 2.6), "navy", "LowerTorso", "core", angle=60.0)
    cin = []
    for j in range(20):
        th = -math.pi / 2 + 2 * math.pi * j / 20
        c, sn = math.cos(th), math.sin(th)
        cin.append(Vector((0.475 * math.copysign(abs(c) ** (2 / 2.6), c), 0.34 * math.copysign(abs(sn) ** (2 / 2.6), sn), 2.43)))
    cinturon, _ = tube(cin, lambda u: 0.045, k=5, steps=1, closed=True)
    add(cinturon, "shoe", "LowerTorso", {"LowerTorso": 1.0})
    add(redondeado((0.075, 0.025, 0.055), Matrix.Translation((0, -0.375, 2.43)), 8, 5), "gold", "LowerTorso", {"LowerTorso": 1.0})

    lk, _ = frente(0.0, 3.355)
    add(ellipsoid((0.065, 0.05, 0.06), Matrix.Translation(lk + Vector((0, -0.03, 0))), 8, 6), "teal", "UpperTorso", "core")
    corbata = ellipsoid((1.0, 1.0, 1.0), Matrix(), 8, 10)
    for v in corbata.verts:
        t = v.co.z
        z = 2.96 + t * 0.34
        lf, _ = frente(0.0, z)
        v.co = Vector((v.co.x * 0.1 * (0.55 - 0.45 * t), lf.y - 0.03 + v.co.y * 0.022, z))
    add(corbata, "teal", core_part, "core")
    for sx in (-1, 1):
        lc, _ = frente(sx * 0.1, 3.39)
        mat = Matrix.Translation(lc + Vector((0, -0.02, 0))) @ Matrix.Rotation(math.radians(-sx * 35), 4, "Y")
        add(ellipsoid((0.10, 0.025, 0.055), mat, 6, 5), "cream", "UpperTorso", "core")
        mat = Matrix.Translation((sx * 0.40, 0.0, 3.40)) @ Matrix.Rotation(math.radians(sx * 32), 4, "Y")
        add(redondeado((0.15, 0.10, 0.03), mat, 8, 5), "vest", "UpperTorso", "core")

    loc, n = frente(0.30, 3.02)
    fr = Matrix.Translation(loc + n * 0.03) @ frame_from_normal(n)
    add(cylinder(0.055, 0.03, fr, 8), "gold", "UpperTorso", "core", angle=40.0)
    for sx in (-1, 1):
        wm = fr @ Matrix.Translation((sx * 0.095, 0.012, 0.0)) @ Matrix.Rotation(math.radians(sx * 14), 4, "Z")
        add(ellipsoid((0.09, 0.03, 0.015), wm, 6, 4), "gold", "UpperTorso", "core")

    for sx in (-1, 1):
        lo, no = hit(sx * 0.226, ZE)
        ne = (no + Vector((0, -1, 0))).normalized()
        OJOS_MARCO.append((sx, dict(OJOS)[sx], lo + ne * 0.036, ne))

    for sx, ceja, mej in ((1, "CejaIzq", "MejillaIzq"), (-1, "CejaDer", "MejillaDer")):
        pts = []
        for x, z in ((0.09, 4.33), (0.23, 4.385), (0.38, 4.35)):
            l2, n2 = hit(sx * x, z + DZ)
            pts.append(l2 + n2 * 0.035)
        brow, _ = tube(pts, lambda u: 0.056 * (0.6 + 0.4 * math.sin(math.pi * u)), k=8, steps=4, cap_rings=2)
        add(brow, "black", "Head", {ceja: 1.0})
        BONES_CARA.append((ceja, "Head", tuple(pts[1]), tuple(pts[1] + Vector((0, 0, 0.08)))))
        lc, nc = hit(sx * 0.40, 3.70 + DZ)
        add(ellipsoid((0.135, 0.115, 0.1), Matrix.Translation(lc - nc * 0.03) @ frame_from_normal(nc), 12, 8), "body", "Head", {mej: 1.0})
        BONES_CARA.append((mej, "Head", tuple(lc), tuple(lc + nc * 0.1)))

    ln, nn = hit(0.0, 3.80 + DZ)
    add(ellipsoid((0.125, 0.105, 0.12), Matrix.Translation(ln + nn * 0.05) @ frame_from_normal(nn), 14, 9), "body", "Head", {"Nariz": 1.0})
    BONES_CARA.append(("Nariz", "Head", tuple(ln - nn * 0.04), tuple(ln + nn * 0.12)))

    for sx, ang in ((-1, 4), (1, -7)):
        lt, nt_ = hit(sx * 0.05, 3.655 + DZ)
        fr = Matrix.Translation(lt + nt_ * 0.012) @ frame_from_normal(nt_) @ Matrix.Rotation(math.radians(ang), 4, "Z")
        add(redondeado((0.043, 0.045, 0.022), fr), "white", "Head", {"BocaSup": 1.0})

    lm, _ = hit(0.0, 3.68 + DZ)
    ym, zl = lm.y + 0.683, 3.67 + DZ
    tpts = [Vector((0, ym - 0.44, zl + 0.005)), Vector((0, ym - 0.53, zl)), Vector((0, ym - 0.60, zl - 0.005))]
    lengua, tls = tube(tpts, lambda u: 0.085 + 0.01 * math.sin(math.pi * u), k=10, steps=3, cap_rings=3)
    for v in lengua.verts:
        v.co.z = zl + 0.005 + (v.co.z - zl) * 0.5
    add(lengua, "tongue", "Head", chain_weights(["BocaInf", "Lengua"], [tls[1]], 0.05), s_layer=True)
    BONES_CARA.append(("Lengua", "BocaInf", tuple(tpts[1]), (0.0, ym - 0.66, zl)))
    BONES_CARA.insert(0, ("BocaInf", "Head", (0.0, lm.y, 3.66 + DZ), (0.0, lm.y, 3.56 + DZ)))
    BONES_CARA.insert(0, ("BocaSup", "Head", (0.0, lm.y, 3.71 + DZ), (0.0, lm.y, 3.81 + DZ)))

    for variante in VARIANTES_OJOS:
        ojos_render(variante)

    add(build_mouth(hit), "mouth", "Head", "mouth", angle=80.0)

    zc = 4.21
    band_pts = []
    for i in range(13):
        a = math.pi * i / 12
        d = Vector((math.cos(a), 0.0, math.sin(a)))
        l2, _ = rayo(d, zc, 0.05)
        band_pts.append(l2 + d * 0.07)
    band, _ = tube(band_pts, lambda u: 0.05, k=8, steps=2, up=Vector((0, 1, 0)))
    add(band, "dark", "Head", {"Head": 1.0})
    for sx in (-1, 1):
        lx, _ = rayo((sx, 0, 0), zc, 0.05)
        rot = Matrix.Rotation(math.radians(90), 4, "Y")
        add(cylinder(0.2, 0.15, Matrix.Translation((lx.x + sx * 0.06, 0.05, zc)) @ rot, 16), "dark", "Head", {"Head": 1.0}, angle=40.0)
        add(cylinder(0.14, 0.05, Matrix.Translation((lx.x + sx * 0.15, 0.05, zc)) @ rot, 16), "teal", "Head", {"Head": 1.0}, angle=40.0)

    mic_pts = []
    for th, z in ((184, 4.15), (205, 4.02), (228, 3.86), (246, 3.80)):
        d = Vector((math.cos(math.radians(th)), math.sin(math.radians(th)), 0.0))
        l2, _ = rayo(d, z)
        mic_pts.append(l2 + d * 0.075)
    mic, ms = tube(mic_pts, lambda u: 0.024, k=6, steps=4, cap_rings=2)
    add(mic, "dark", "Head", {"Head": 1.0})
    add(ellipsoid((0.065, 0.065, 0.065), Matrix.Translation(mic_pts[-1]), 10, 6), "black", "Head", {"Head": 1.0})

    for side, sx in (("Left", 1), ("Right", -1)):
        h, c, w = Vector((sx * HOMBRO.x, 0, HOMBRO.z)), Vector((sx * CODO.x, 0, CODO.z)), Vector((sx * MUNECA.x, 0, MUNECA.z))
        dh = (c - h).normalized()
        ctrl = [h, c, w]
        arm, cs = tube(ctrl, lambda u: 0.104 - 0.018 * u, k=8, steps=4, cap_rings=2)
        s_el, s_wr = cs[1], cs[2]
        wf = chain_weights([side + "UpperArm", side + "LowerArm", side + "Hand"], [s_el, s_wr - 0.04], 0.11)
        add(arm, "body", (lambda c_, s_, se=s_el, sd=side: sd + ("UpperArm" if s_ < se else "LowerArm")), wf, s_layer=True)
        ua = side + "UpperArm"
        manga, _ = tube([h - dh * 0.03, h + dh * 0.17, h + dh * 0.36], lambda u: 0.15 + 0.022 * u, k=10, steps=1, cap_rings=1)
        add(manga, "cream", ua, {ua: 1.0})
        add(cylinder(0.178, 0.05, Matrix.Translation(h + dh * 0.345) @ Vector((0, 0, 1)).rotation_difference(dh).to_matrix().to_4x4(), 10), "teal", ua, {ua: 1.0}, angle=40.0)

        hp = side + "Hand"
        lado = LADOS[side]
        guante, _ = tube([w + Vector((0, 0, 0.04)), w + Vector((sx * 0.015, 0, -0.10))], lambda u: 0.11 + 0.035 * u, k=12, steps=1, cap_rings=1)
        add(guante, "white", hp, {hp: 1.0})
        pc = w + Vector((sx * 0.04, 0, -0.19))
        add(ellipsoid(PALMA, Matrix.Translation(pc), 14, 9), "white", hp, {hp: 1.0})
        for nombre, fy_, largo in DEDOS:
            fondo = pc.z - PALMA[2] * math.sqrt(1.0 - (fy_ / PALMA[1]) ** 2)
            fpts = [Vector((pc.x, fy_ * 0.9, pc.z - 0.06)), Vector((pc.x + sx * 0.03, fy_ * 1.05, fondo - largo * 0.45)), Vector((pc.x - sx * 0.03, fy_ * 1.2, fondo - largo))]
            fbm, fs = tube(fpts, lambda u: 0.064 - 0.004 * u, k=8, steps=3, cap_rings=2)
            camino = catmull(fpts, 3)
            s_k = next(seglen_hasta(camino, i) for i in range(len(camino)) if camino[i].z <= fondo + 0.03)
            add(fbm, "white", hp, falange(camino, fs[-1] + 0.06, s_k, hp, lado + nombre), s_layer=True)
        tpts = [Vector((pc.x - sx * 0.01, -0.17, pc.z + 0.05)), Vector((pc.x - sx * 0.05, -0.33, pc.z - 0.06))]
        tbm, ts = tube(tpts, lambda u: 0.07, k=8, steps=2, cap_rings=2)
        add(tbm, "white", hp, falange(catmull(tpts, 2), ts[-1] + 0.07, 0.06, hp, lado + "Pulgar"), s_layer=True)
        if side == "Right":
            AGARRE.xyz = pc + Vector((-sx * 0.13, -0.03, -0.15))

        k_, a_ = Vector((sx * RODILLA.x, 0, RODILLA.z)), Vector((sx * TOBILLO.x, 0, TOBILLO.z))
        lctrl = [Vector((sx * CADERA.x, 0, CADERA.z + 0.1)), k_, a_ - Vector((0, 0, 0.06))]
        leg, lcs = tube(lctrl, lambda u: 0.165 - 0.02 * u + 0.022 * ss(0.8, 1.0, u), k=12, steps=6, cap_rings=3)
        s_kn, s_an = lcs[1], lcs[2]
        lw = chain_weights([side + "UpperLeg", side + "LowerLeg", side + "Foot"], [s_kn, s_an - 0.1], 0.15)
        add(leg, "navy", (lambda c_, s_, sk=s_kn, sd=side: sd + ("UpperLeg" if s_ < sk else "LowerLeg")), lw, s_layer=True)
        fp = side + "Foot"
        shoe = ellipsoid((0.25, 0.48, 0.19), Matrix.Translation((sx * 0.30, -0.18, 0.18)), 14, 9)
        for v in shoe.verts:
            v.co.z = max(v.co.z, 0.03)
        add(shoe, "shoe", fp, {fp: 1.0})
        sole = ellipsoid((0.26, 0.49, 0.06), Matrix.Translation((sx * 0.30, -0.18, 0.05)), 14, 6)
        for v in sole.verts:
            v.co.z = max(v.co.z, 0.0)
        add(sole, "sole", fp, {fp: 1.0})


def assemble():
    acc = {p: {"v": [], "w": [], "f": [], "uv": [], "n": []} for p in PARTS + ["Ojos_" + v for v in VARIANTES_OJOS]}
    for pid, pr in enumerate(PRIMS):
        bm = pr.bm
        bm.verts.index_update()
        bm.normal_update()
        sl = bm.verts.layers.float.get("s") if pr.s_layer else None
        lws = bm.verts.layers.float.get("ws")
        lwi = bm.verts.layers.float.get("wi")
        cos_lim = math.cos(math.radians(pr.angle))
        uv = swatch_uv(pr.role)
        vmaps = {}
        for f in bm.faces:
            c = f.calc_center_median()
            if callable(pr.part):
                s = sum(v[sl] for v in f.verts) / len(f.verts) if sl else 0.0
                part = pr.part(c, s) if sl else pr.part(c)
            else:
                part = pr.part
            a = acc[part]
            vm = vmaps.setdefault(part, {})
            idx = []
            for lp in f.loops:
                v = lp.vert
                if v.index not in vm:
                    vm[v.index] = len(a["v"])
                    a["v"].append(v.co.copy())
                    if pr.weights == "core":
                        w = core_weights(v.co.z)
                    elif pr.weights == "mouth":
                        w = {"Head": max(0.0, 1.0 - v[lws] - v[lwi]), "BocaSup": v[lws], "BocaInf": v[lwi]}
                        w = {k: x for k, x in w.items() if x > 1e-4}
                    elif callable(pr.weights):
                        w = pr.weights(v[sl])
                    else:
                        w = dict(pr.weights)
                    tot = sum(w.values())
                    a["w"].append({k: x / tot for k, x in w.items()})
                idx.append(vm[v.index])
                nsum = Vector()
                for lf in v.link_faces:
                    if lf.normal.dot(f.normal) >= cos_lim:
                        nsum += lf.normal * lf.calc_area()
                a["n"].append(tuple(nsum.normalized() if nsum.length > 1e-9 else f.normal))
                a["uv"].append(uv)
            a["f"].append(tuple(idx))
    return acc


def make_palette_image():
    size = 64
    img = bpy.data.images.new("TripulantePalette", size, size, alpha=True)
    px = [0.0] * (size * size * 4)
    for role, (i, col) in PALETTE.items():
        rgba = col if isinstance(col, tuple) else (*hex_rgb(col), 1.0)
        gx, gy = i % 4, i // 4
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * size + x) * 4
                px[o:o + 4] = rgba
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "tripulante_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def palette_material(name, img, player_hex):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    rgb = nt.nodes.new("ShaderNodeRGB")
    rgb.name = "PlayerColor"
    rgb.label = "PlayerColor"
    rgb.outputs[0].default_value = (*lin(hex_rgb(player_hex)), 1.0)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    cin = [i for i in mix.inputs if i.type == "RGBA"]
    cout = [o for o in mix.outputs if o.type == "RGBA"][0]
    nt.links.new(tex.outputs["Alpha"], mix.inputs[0])
    nt.links.new(rgb.outputs[0], cin[0])
    nt.links.new(tex.outputs["Color"], cin[1])
    nt.links.new(cout, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.62
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return mat


def export_material(img):
    mat = bpy.data.materials.new("Tripulante_Export")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


BONES = [
    ("Root", None, (0, 0, 0), (0, 0, 0.4)),
    ("HumanoidRootNode", "Root", (0, 0, ZROOT), (0, 0, ZROOT + 0.4)),
    ("LowerTorso", "HumanoidRootNode", (0, 0, ZROOT), (0, 0, ZWAIST)),
    ("UpperTorso", "LowerTorso", (0, 0, ZWAIST), (0, 0, ZNECK)),
    ("Head", "UpperTorso", (0, 0, ZNECK), (0, 0, ZTOP)),
]
for _lado, _sx in (("Left", 1), ("Right", -1)):
    _h, _c, _w = (_sx * HOMBRO.x, 0, HOMBRO.z), (_sx * CODO.x, 0, CODO.z), (_sx * MUNECA.x, 0, MUNECA.z)
    BONES += [
        (_lado + "UpperArm", "UpperTorso", _h, _c),
        (_lado + "LowerArm", _lado + "UpperArm", _c, _w),
        (_lado + "Hand", _lado + "LowerArm", _w, (_sx * (MUNECA.x + 0.03), 0, MUNECA.z - 0.45)),
    ]
for _lado, _sx in (("Left", 1), ("Right", -1)):
    _h, _k, _a = (_sx * CADERA.x, 0, CADERA.z), (_sx * RODILLA.x, 0, RODILLA.z), (_sx * TOBILLO.x, 0, TOBILLO.z)
    BONES += [
        (_lado + "UpperLeg", "LowerTorso", _h, _k),
        (_lado + "LowerLeg", _lado + "UpperLeg", _k, _a),
        (_lado + "Foot", _lado + "LowerLeg", _a, (_sx * 0.29, -0.45, 0.12)),
    ]


def todos_huesos():
    return BONES + BONES_CARA + BONES_MANOS


def build_armature(coll):
    arm = bpy.data.armatures.new("Tripulante_Rig")
    obj = bpy.data.objects.new("Tripulante", arm)
    coll.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = {}
    for name, parent, h, t in todos_huesos():
        eb = arm.edit_bones.new(name)
        eb.head = h
        eb.tail = t
        eb.roll = 0.0
        if parent:
            eb.parent = ebs[parent]
            eb.use_connect = False
        ebs[name] = eb
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.display_type = "STICK"
    return obj


def build_meshes(coll, rig, acc, mat, partes):
    objs = []
    for part in partes:
        a = acc[part]
        me = bpy.data.meshes.new(part + "_Geo")
        me.from_pydata([tuple(v) for v in a["v"]], [], a["f"])
        me.update()
        uvl = me.uv_layers.new(name="UVMap")
        for i, uv in enumerate(a["uv"]):
            uvl.data[i].uv = uv
        try:
            me.shade_smooth()
        except AttributeError:
            for p in me.polygons:
                p.use_smooth = True
        me.normals_split_custom_set(a["n"])
        me.materials.append(mat)
        ob = bpy.data.objects.new(part + "_Geo", me)
        coll.objects.link(ob)
        ob.parent = rig
        for bone, _, _, _ in todos_huesos():
            if bone in ("Root", "HumanoidRootNode"):
                continue
            ob.vertex_groups.new(name=bone)
        for vi, w in enumerate(a["w"]):
            for bone, val in w.items():
                ob.vertex_groups[bone].add([vi], val, "REPLACE")
        mod = ob.modifiers.new("Armature", "ARMATURE")
        mod.object = rig
        objs.append(ob)
    return objs


OJOS_OBJ = {}


def cara(boca=0.0, cejas=0.0, giro=0.0, lengua=0.0, lado=0.0, mejillas=0.0):
    r = [
        ("BocaSup", "T", (0.0, 0.0, 0.065 * boca)),
        ("BocaInf", "T", (lado * 0.04, -0.06 * boca, -0.25 * boca)),
        ("Lengua", "T", (lado * 0.03, -(0.07 * boca + 0.14 * lengua), -0.03 * lengua)),
    ]
    if lado:
        r.append(("Lengua", "Z", lado * 25))
    for nombre, sx in (("CejaIzq", 1), ("CejaDer", -1)):
        r.append((nombre, "T", (0.0, -0.05 * max(0.0, -cejas) - 0.03 * max(0.0, giro), 0.06 * cejas)))
        r.append((nombre, "Y", -sx * giro * 22))
    for nombre, sx in (("MejillaIzq", 1), ("MejillaDer", -1)):
        p = 0.02 + 0.04 * mejillas + 0.03 * boca
        r.append((nombre, "T", (sx * 0.4 * p, -0.8 * p, 0.035 * mejillas)))
    return r


def pose(rig, rots):
    for bone, axis, deg in rots:
        bpy.context.view_layer.update()
        pb = rig.pose.bones[bone]
        m = pb.matrix.copy()
        if axis == "T":
            pb.matrix = Matrix.Translation(Vector(deg)) @ m
            continue
        h = m.translation.copy()
        r = Matrix.Rotation(math.radians(deg), 4, axis)
        pb.matrix = Matrix.Translation(h) @ r @ Matrix.Translation(-h) @ m
    bpy.context.view_layer.update()


POSES_MANO = {
    "abierta": (-8, -6, -8, -6, -25, -5, 14),
    "relajada": (18, 22, 22, 28, 8, 10, 0),
    "agarre": (60, 70, 60, 70, 35, 30, 0),
    "puno": (85, 95, 85, 95, 40, 45, 0),
    "pulsar": (0, 0, 85, 95, 40, 45, 0),
}


PRIMERA = (
    ("reposo", (64, 96, -14), (64, 96, 14), "relajada"),
    ("agarre", (90, 27, 12), (64, 96, 14), "agarre"),
)


def pose_mano(rig, side, vals):
    sx = 1 if side == "Left" else -1
    lado = LADOS[side]
    palma = Vector((-sx, 0, 0))
    cierre = Vector((-sx, 0.3, -0.2)).normalized()
    frente = Vector((0, -1, 0))
    bones = rig.data.bones
    for nombre, i, abre in (("Indice", 0, 1), ("Medio", 2, 0.3), ("Anular", 2, -0.3), ("Menique", 2, -1), ("Pulgar", 4, 0)):
        b1, b2 = bones[lado + nombre + "1"], bones[lado + nombre + "2"]
        d = (b2.head_local - b1.head_local).normalized()
        eje = d.cross(cierre if nombre == "Pulgar" else palma).normalized()
        giro = Quaternion(d.cross(frente).normalized(), math.radians(abre * vals[6])) @ Quaternion(eje, math.radians(vals[i]))
        for b, q in ((b1, giro), (b2, Quaternion(eje, math.radians(vals[i + 1])))):
            r = b.matrix_local.to_quaternion()
            pb = rig.pose.bones[b.name]
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = r.inverted() @ q @ r
    bpy.context.view_layer.update()


def clone(rig, objs, coll, mat, loc, rot_z=0.0, solo=None, ojos=None):
    r2 = rig.copy()
    r2.data = rig.data
    r2.animation_data_clear()
    coll.objects.link(r2)
    r2.location = loc
    r2.rotation_euler = (0, 0, math.radians(rot_z))
    r2.hide_render = False
    for ob in objs + ([OJOS_OBJ[ojos]] if ojos else []):
        if solo and ob.name not in solo:
            continue
        o2 = ob.copy()
        coll.objects.link(o2)
        o2.parent = r2
        o2.modifiers["Armature"].object = r2
        o2.material_slots[0].link = "OBJECT"
        o2.material_slots[0].material = mat
        o2.hide_render = False
    return r2


def render_setup(scene, res):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 96
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    scene.cycles.max_bounces = 6
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    world = bpy.data.worlds.new("Sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (*lin(hex_rgb("BFE3F2")), 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.85
    scene.world = world
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.2
    sun.angle = math.radians(14)
    so = bpy.data.objects.new("Sun", sun)
    so.rotation_euler = (math.radians(48), math.radians(8), math.radians(-28))
    scene.collection.objects.link(so)
    gm = bpy.data.materials.new("Ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin(hex_rgb("EFE9DC")), 1.0)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60)
    gme = bpy.data.meshes.new("Ground")
    bm.to_mesh(gme)
    gme.materials.append(gm)
    go = bpy.data.objects.new("Ground", gme)
    scene.collection.objects.link(go)


def camera(scene, loc, target, lens=None, ortho=None):
    cd = bpy.data.cameras.new("Cam")
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    co = bpy.data.objects.new("Cam", cd)
    scene.collection.objects.link(co)
    co.location = loc
    d = Vector(target) - Vector(loc)
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    scene.camera = co
    return co


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    coll = scene.collection
    build_character()
    acc = assemble()
    img = make_palette_image()
    mat = palette_material("Tripulante_Palette", img, PLAYER_COLORS["Lavanda"])
    exp = export_material(img)
    rig = build_armature(coll)
    objs = build_meshes(coll, rig, acc, mat, PARTS)
    for o in build_meshes(coll, rig, acc, mat, ["Ojos_" + v for v in VARIANTES_OJOS]):
        OJOS_OBJ[o.name[5:-4]] = o
        o.hide_render = True
        o.hide_set(True)
    tc = {o.name[:-4]: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}
    print("BONES", len(todos_huesos()), [b[0] for b in BONES_CARA])
    for sx, e, c, n in OJOS_MARCO:
        if sx < 0:
            print("OJO CENTRO (%.3f, %.3f, %.3f) NORMAL (%.3f, %.3f, %.3f) z %.3f" % (-c.x, c.z - HRP_Z, c.y, -n.x, n.z, n.y, c.z))
    m1 = next(b for b in BONES_MANOS if b[0] == "DerMedio1")
    d = AGARRE - Vector(m1[2])
    print("CameraOffset Y %.3f" % (ZE - HRP_Z - 1.5))
    print("AGARRE_MANO (%.3f, %.3f, %.3f)" % (-d.x, d.z, d.y))
    budget = {"Head": (["Head"], 4000), "Torso": (["UpperTorso", "LowerTorso"], 1750)}
    for sd in ("Left", "Right"):
        budget[sd + "Arm"] = ([sd + "UpperArm", sd + "LowerArm", sd + "Hand"], 1248)
        budget[sd + "Leg"] = ([sd + "UpperLeg", sd + "LowerLeg", sd + "Foot"], 1248)
    for k, (ps, lim) in budget.items():
        n = sum(tc[x] for x in ps)
        print("BUDGET", k, n, "/", lim, "OK" if n <= lim else "OVER")
    print("TRIS", sum(tc.values()), "/ 10742")
    for o in objs:
        o.data.materials[0] = exp
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, "tripulante.fbx"),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        use_mesh_modifiers=False,
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="Z",
        axis_up="Y",
        mesh_smooth_type="OFF",
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        armature_nodetype="NULL",
        bake_anim=False,
        path_mode="COPY",
        embed_textures=True,
    )
    for o in objs:
        o.data.materials[0] = mat
    img.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "tripulante.blend"))

    if "--render" not in sys.argv and "--manos" not in sys.argv and "--primera" not in sys.argv:
        return
    rdir = os.path.join(OUT, "renders")
    os.makedirs(rdir, exist_ok=True)
    rig.hide_render = True
    for o in objs:
        o.hide_render = True
    render_setup(scene, (1600, 900))
    mats = {nm: palette_material("Tripulante_" + nm, img, hx) for nm, hx in PLAYER_COLORS.items()}

    cm = bpy.data.materials.new("Barra")
    cm.use_nodes = True
    cm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin(hex_rgb("F0B73A")), 1.0)
    hechos = []
    for i, nm in enumerate(POSES_MANO):
        r2 = clone(rig, objs, coll, mats["Lavanda"], (i * 0.85, 0, 0), solo={"RightHand_Geo", "RightLowerArm_Geo"})
        bpy.context.view_layer.update()
        pose_mano(r2, "Right", POSES_MANO[nm])
        hechos.append(r2)
        if nm == "agarre":
            c = r2.matrix_world @ AGARRE
            bm = cylinder(0.08, 0.55, Matrix.Translation(c) @ Matrix.Rotation(math.radians(90), 4, "X"), 16)
            me = bpy.data.meshes.new("Barra")
            bm.to_mesh(me)
            me.materials.append(cm)
            bo = bpy.data.objects.new("Barra", me)
            coll.objects.link(bo)
            hechos.append(bo)
    for nombre, loc in (("manos_prueba", (0.4, -6.0, 1.9)), ("manos_prueba_palma", (3.6, -4.6, 2.2))):
        co = camera(scene, loc=loc, target=(0.82, 0, 1.68), ortho=3.9)
        scene.render.resolution_x, scene.render.resolution_y = 1600, 520
        scene.cycles.samples = 48
        scene.render.filepath = os.path.join(rdir, nombre + ".png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(co)
    for r2 in hechos:
        for ch in list(r2.children):
            bpy.data.objects.remove(ch)
        bpy.data.objects.remove(r2)
    brazos = {p + "_Geo" for p in PARTS if "Arm" in p or "Hand" in p}
    for nombre, der, izq, mano in PRIMERA:
        if "--render" not in sys.argv and "--primera" not in sys.argv:
            break
        r2 = clone(rig, objs, coll, mats["Lavanda"], (0, 0, 0), solo=brazos)
        bpy.context.view_layer.update()
        p = []
        for lado, (hombro, codo, giro) in (("Right", der), ("Left", izq)):
            p += [(lado + "LowerArm", "X", -codo), (lado + "UpperArm", "X", -hombro), (lado + "UpperArm", "Z", giro)]
        pose(r2, p)
        pose_mano(r2, "Right", POSES_MANO[mano])
        pose_mano(r2, "Left", POSES_MANO["relajada"])
        zc = ZE
        suelo = bpy.data.materials["Ground"].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
        suelo.default_value = (*lin(hex_rgb("6B7A8F")), 1.0)
        co = camera(scene, loc=(0, 0, zc), target=(0, -5, zc), lens=20)
        co.data.sensor_fit = "VERTICAL"
        co.data.angle = math.radians(80)
        scene.render.resolution_x, scene.render.resolution_y = 1600, 900
        scene.cycles.samples = 48
        scene.render.filepath = os.path.join(rdir, "primera_" + nombre + ".png")
        bpy.ops.render.render(write_still=True)
        for ch in list(r2.children):
            bpy.data.objects.remove(ch)
        bpy.data.objects.remove(r2)
        bpy.data.objects.remove(co)
        suelo.default_value = (*lin(hex_rgb("EFE9DC")), 1.0)
    if "--render" not in sys.argv:
        return

    def boca(k):
        return cara(boca=k)

    def shot(name, cast, cam, res, samples):
        made = []
        for c in cast:
            nm, loc, rz, p = c[:4]
            made.append((clone(rig, objs, coll, mats[nm], loc, rot_z=rz, ojos=c[4] if len(c) > 4 else "normal"), p))
        bpy.context.view_layer.update()
        for r2, p in made:
            pose(r2, p)
        co = camera(scene, **cam)
        scene.render.resolution_x, scene.render.resolution_y = res
        scene.cycles.samples = samples
        scene.render.filepath = os.path.join(rdir, name + ".png")
        bpy.ops.render.render(write_still=True)
        for r2, _ in made:
            for ch in list(r2.children):
                bpy.data.objects.remove(ch)
            bpy.data.objects.remove(r2)
        bpy.data.objects.remove(co)

    wave = [("RightUpperArm", "Y", 150), ("RightLowerArm", "Y", 25), ("Head", "Y", 8)]
    carry = [("LeftUpperArm", "X", -55), ("RightUpperArm", "X", -55), ("LeftLowerArm", "X", -45), ("RightLowerArm", "X", -45)]
    run = [("UpperTorso", "X", 8), ("LeftUpperLeg", "X", -38), ("LeftLowerLeg", "X", 45), ("RightUpperLeg", "X", 28), ("RightLowerLeg", "X", 20), ("RightUpperArm", "X", -40), ("RightLowerArm", "X", -50), ("LeftUpperArm", "X", 35), ("LeftLowerArm", "X", -30)]
    shot("lineup", [
        ("Lima", (-4.2, 0, 0), 12, wave + boca(0.55)),
        ("Lavanda", (-1.4, 0, 0), 4, []),
        ("Chicle", (1.4, 0, 0), -4, carry + boca(1.0)),
        ("Sol", (4.2, 0, 0), -14, run + boca(0.3)),
    ], dict(loc=(0.6, -15.5, 5.4), target=(0, 0, 2.5), lens=42), (1600, 900), 96)
    shot("turnaround", [("Lavanda", (-4.5 + 3.0 * i, 0, 0), rz, []) for i, rz in enumerate((0, -40, -90, 180))],
         dict(loc=(0, -20, 2.6), target=(0, 0, 2.6), ortho=13.6), (1600, 640), 96)
    cam_caras = dict(loc=(0, -6.4, 4.2), target=(0, 0, 4.08), lens=38)
    shot("caras_voz", [
        ("Lima", (-2.0, 0, 0), 0, []),
        ("Lavanda", (0.0, 0, 0), 0, cara(boca=0.55, cejas=0.4, lengua=0.1, mejillas=0.5)),
        ("Chicle", (2.0, 0, 0), 0, cara(boca=1.15, cejas=1.2, giro=-0.5, lengua=0.5, mejillas=0.3), "grande"),
    ], cam_caras, (1600, 700), 64)
    shot("caras_eventos", [
        ("Sol", (-3.0, 0, 0), 0, cara(boca=0.6, cejas=1.4), "grande"),
        ("Lavanda", (-1.0, 0, 0), 0, cara(boca=0.35, cejas=0.9, giro=-1.0, mejillas=0.2) + [("Head", "Y", -6)], "susto"),
        ("Lima", (1.0, 0, 0), 0, cara(boca=0.4, cejas=0.3, giro=0.4, lengua=1.0, lado=1.0) + [("CejaIzq", "T", (0, 0, 0.07)), ("Head", "Y", 12)], "mareo"),
        ("Chicle", (3.0, 0, 0), 0, cara(boca=0.5, cejas=0.6, giro=-0.3, mejillas=1.0), "feliz"),
    ], dict(loc=(0, -8.6, 4.2), target=(0, 0, 4.08), lens=38), (1600, 560), 64)
    shot("caras_enfado", [
        ("Sol", (-1.0, 0, 0), 0, cara(boca=0.12, cejas=-0.8, giro=1.0), "enfado"),
        ("Lima", (1.0, 0, 0), 20, cara(boca=0.5, cejas=0.5, lengua=0.4, mejillas=0.5)),
    ], dict(loc=(0, -5.4, 4.2), target=(0, 0, 4.08), lens=38), (1200, 600), 64)
    shot("brazos_prueba", [
        ("Sol", (-4.2, 0, 0), 20, [("LeftUpperArm", "Y", -150), ("RightUpperArm", "Y", 150)] + boca(0.6)),
        ("Lima", (-1.4, 0, 0), 30, [("LeftUpperArm", "X", -75), ("RightUpperArm", "X", -75), ("LeftLowerArm", "X", -35), ("RightLowerArm", "X", -35)]),
        ("Lavanda", (1.4, 0, 0), 30, [("LeftUpperArm", "Y", -88), ("RightUpperArm", "Y", 88), ("LeftLowerArm", "X", -90), ("RightLowerArm", "X", -90)]),
        ("Chicle", (4.2, 0, 0), 25, [("UpperTorso", "X", 15), ("LeftUpperArm", "X", 60), ("RightUpperArm", "X", 60), ("LeftLowerArm", "X", -40), ("RightLowerArm", "X", -40), ("LeftUpperLeg", "X", -60), ("RightUpperLeg", "X", -60), ("LeftLowerLeg", "X", 80), ("RightLowerLeg", "X", 80)]),
    ], dict(loc=(0.6, -15.5, 5.4), target=(0, 0, 2.5), lens=42), (1600, 900), 64)

main()
