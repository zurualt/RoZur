import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
_SEP = {}
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "herramientas", "separar_capas.py"), encoding="utf-8") as _fh:
    exec(compile(_fh.read(), "separar_capas.py", "exec"), _SEP)
if len(sys.argv) > 1 and os.path.isdir(sys.argv[-1]):
    OUT = sys.argv[-1]

# Cabeza: bola algo aplastada, mas llena por abajo (mofletes). Centro, radio, fondo y medias alturas.
HC, HR, HD, HZB, HZT = 3.03, 0.98, 0.93, 0.80, 0.90
ZE = 3.01
ZROOT, ZWAIST, ZNECK, ZTOP = 1.05, 1.32, 2.12, HC + HZT
HOMBRO, CODO, MUNECA = Vector((0.47, 0.0, 1.92)), Vector((0.58, 0.0, 1.56)), Vector((0.70, 0.0, 1.26))
CADERA, RODILLA, TOBILLO = Vector((0.25, 0.0, 0.95)), Vector((0.26, 0.0, 0.55)), Vector((0.27, 0.0, 0.20))
HRP_Z = CADERA.z + 1.0
Z_CINTURON = 1.22

PALETTE = {
    "body": (0, (1.0, 1.0, 1.0, 0.0)),
    "black": (1, "1B1B21"),
    "orange": (2, "F27B2B"),
    "teal": (3, "1FA6A0"),
    "sole": (4, "4A3F3A"),
    "gold": (5, "F0B73A"),
    "cream": (6, "FFF4E0"),
    "belt": (7, "5A3B2A"),
    "boot": (8, "2E2A2C"),
    "white": (9, "F7F7F2"),
    "mouth": (10, "2B1219"),
    "tongue": (11, "E85A78"),
    "navy": (12, "2C3A5E"),
    "blush": (13, "FF8F7E"),
    "guante": (14, ("FAFAF5", "A4ABC6")),
    "puno": (15, ("2CBAB2", "147A75")),
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


def swatch_uv(role, sombra=None):
    i = PALETTE[role][0]
    if sombra is None:
        return ((i % 4 + 0.5) / 4.0, (i // 4 + 0.5) / 4.0)
    # Casillas con degradado (16 filas): sombra 0 = claro, 1 = oscuro, sin tocar el borde de la casilla.
    return ((i % 4 + 0.5) / 4.0, (i // 4 * 16 + 1.5 + 13.0 * min(1.0, max(0.0, sombra))) / 64.0)


def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def sp(c, e):
    return math.copysign(abs(c) ** (2.0 / e), c)


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
    t1 = ss(ZWAIST - 0.14, ZWAIST + 0.14, z)
    t2 = ss(ZNECK - 0.06, ZNECK + 0.10, z)
    w = {"LowerTorso": 1.0 - t1, "UpperTorso": t1 * (1.0 - t2), "Head": t2}
    return {k: v for k, v in w.items() if v > 1e-4}


def core_part(c):
    return "LowerTorso" if c.z < ZWAIST else "UpperTorso"


class Prim:
    def __init__(self, bm, role, part, weights, s_layer=False, angle=50.0, sombra=None):
        self.bm = bm
        self.role = role
        self.part = part
        self.weights = weights
        self.s_layer = s_layer
        self.angle = angle
        self.sombra = sombra


PRIMS = []


def add(bm, role, part, weights, s_layer=False, angle=50.0, sombra=None):
    PRIMS.append(Prim(bm, role, part, weights, s_layer, angle, sombra))


def ellipsoid(radii, mat=Matrix(), u=20, v=10):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.transform(bm, matrix=mat @ Matrix.Diagonal((*radii, 1.0)), verts=bm.verts)
    return bm


def cylinder(radius, depth, mat=Matrix(), seg=32):
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
        out.append(points[-1].copy())
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


def tube(ctrl, radius_fn, k=20, steps=8, closed=False, up=None, caps=True, cap_rings=6, cap=(1.0, 1.0), expo=2.0):
    """Tubo por una curva. radius_fn(u) da un radio o (radio en la normal, radio en la binormal); expo > 2 lo hace mas cuadrado.
    cap = largo de las tapas de cada punta respecto al radio (1 = media esfera, 0,3 = dobladillo chato)."""
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

    def radios(u):
        r = radius_fn(u)
        return (r, r) if isinstance(r, (int, float)) else r

    def anillo(c, i, ra, rb, s):
        b = tangents[i].cross(normals[i]).normalized()
        ring = []
        for j in range(k):
            a = 2 * math.pi * j / k
            v = bm.verts.new(c + normals[i] * (sp(math.cos(a), expo) * ra) + b * (sp(math.sin(a), expo) * rb))
            v[sl] = s
            ring.append(v)
        return ring

    bm = bmesh.new()
    sl = bm.verts.layers.float.new("s")
    rings = []
    for i in range(n):
        u = seglen[i] / total if total > 0 else 0.0
        ra, rb = radios(u)
        rings.append(anillo(path[i], i, ra, rb, seglen[i]))
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
    for a_i, b_i in pairs:
        ra_, rb_ = rings[a_i], rings[b_i]
        for j in range(k):
            bm.faces.new((ra_[j], ra_[(j + 1) % k], rb_[(j + 1) % k], rb_[j]))
    if caps and not closed:
        for end, largo in ((0, cap[0]), (n - 1, cap[1])):
            d = -tangents[0] if end == 0 else tangents[-1]
            ra, rb = radios(0.0 if end == 0 else 1.0)
            prev = rings[end]
            for c in range(1, cap_rings + 1):
                phi = (math.pi / 2) * c / cap_rings
                center = path[end] + d * (0.5 * (ra + rb) * largo * math.sin(phi))
                if c == cap_rings:
                    pole = bm.verts.new(center)
                    pole[sl] = seglen[end]
                    for j in range(k):
                        bm.faces.new((prev[j], prev[(j + 1) % k], pole))
                    break
                f = math.cos(phi)
                ring = anillo(center, end, ra * f, rb * f, seglen[end])
                for j in range(k):
                    bm.faces.new((prev[j], prev[(j + 1) % k], ring[(j + 1) % k], ring[j]))
                prev = ring
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ctrl_s = []
    for p in ctrl:
        best = min(range(n), key=lambda i: (path[i] - p).length)
        ctrl_s.append(seglen[best])
    return bm, ctrl_s


def revolucion(prof, m=48, n=2.0):
    bm = bmesh.new()
    rings = []
    for z, rx, ry in prof:
        if rx < 1e-5:
            rings.append([bm.verts.new((0, 0, z))])
            continue
        ring = []
        for j in range(m):
            th = -math.pi / 2 + 2 * math.pi * j / m
            ring.append(bm.verts.new((rx * sp(math.cos(th), n), ry * sp(math.sin(th), n), z)))
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


def suave(prof, steps=3):
    pts = catmull([Vector(p) for p in prof], steps)
    return [tuple(p) for p in pts]


def redondeado(radii, mat, u=24, v=14, p=0.5):
    bm = ellipsoid((1.0, 1.0, 1.0), Matrix(), u, v)
    for vert in bm.verts:
        vert.co = Vector([math.copysign(abs(c) ** p, c) for c in vert.co])
    bmesh.ops.transform(bm, matrix=mat @ Matrix.Diagonal((*radii, 1.0)), verts=bm.verts)
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


def build_head():
    prof = []
    nb, nt = 13, 17
    for i in range(nb):
        a = -math.pi / 2 + (math.pi / 2) * i / nb
        c = max(0.0, math.cos(a)) ** 0.8
        prof.append((HC + HZB * math.sin(a), HR * c, HR * HD * c))
    for i in range(nt + 1):
        a = (math.pi / 2) * i / nt
        c = max(0.0, math.cos(a))
        prof.append((HC + HZT * math.sin(a), HR * c, HR * HD * c))
    return revolucion(prof, 44)


# Cuerpo rechoncho: camisa arriba, pantalon corto abajo (cambia de color en el cinturon). (z, radio x, radio y)
CUERPO = [(0.70, 0.0, 0.0), (0.712, 0.20, 0.16), (0.76, 0.35, 0.28), (0.84, 0.445, 0.35), (0.96, 0.505, 0.395), (1.10, 0.54, 0.425),
          (1.24, 0.56, 0.44), (1.38, 0.572, 0.452), (1.53, 0.572, 0.452), (1.68, 0.555, 0.44), (1.81, 0.52, 0.41), (1.92, 0.47, 0.37),
          (2.01, 0.39, 0.31), (2.07, 0.29, 0.24), (2.11, 0.17, 0.15), (2.13, 0.0, 0.0)]


def build_mouth(hit):
    cols, rows, w = 21, 6, 0.135
    bm = bmesh.new()
    ls = bm.verts.layers.float.new("ws")
    li = bm.verts.layers.float.new("wi")
    grid = []
    zm = ZE - 0.33
    for ri in range(rows + 1):
        v = ri / rows
        row = []
        for ci in range(cols + 1):
            u = -1.0 + 2.0 * ci / cols
            zt = zm + 0.04 * u * u
            t = 0.012 + 0.03 * math.sqrt(max(0.0, 1.0 - u * u))
            loc, n = hit(u * w, zt - v * t)
            vert = bm.verts.new(loc + n * 0.03)
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
    return bm, zm


OJO_RADIO = 0.095
OJO_X = 0.33
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
        add(ellipsoid((0.21 * e2, 0.21 * e2 * alto, 0.04), fr @ Matrix.Translation((0, 0, 0.07)), 32, 14), "black", parte, {"Head": 1.0})
        add(ellipsoid((0.185 * e2, 0.185 * e2 * alto, 0.065), fr @ Matrix.Translation((0, 0, 0.1)), 32, 14), "white", parte, {"Head": 1.0})
        r = OJO_RADIO * e2
        add(ellipsoid((0.08 * e2 * pup, 0.08 * e2 * pup * alto, 0.025), fr @ Matrix.Translation((-sx * adentro * r, arriba * r * alto, 0.165)), 20, 10), "black", parte, {"Head": 1.0})


LADOS = {"Left": "Izq", "Right": "Der"}
BONES_MANOS = []
AGARRE = Vector()
# Manopla: largo del cuerpo (sin la punta redonda), nudillo (Manopla1) y segunda doblez (Manopla2) medidos desde la muneca.
MANOPLA_LARGO, NUDILLO, DOBLEZ = 0.30, 0.13, 0.23


def build_mano(side, sx):
    """Manopla blanca de pala ancha y algo plana, pulgar gordito y puno turquesa abombado.
    La sombra (casillas con degradado) oscurece los lados, la palma, la base del pulgar y la entrada del puno,
    asi que vista desde el dorso en primera persona tiene el borde un poco mas oscuro y se lee sobre cualquier suelo."""
    hp = side + "Hand"
    lado = LADOS[side]
    c = Vector((sx * CODO.x, 0, CODO.z))
    w = Vector((sx * MUNECA.x, 0, MUNECA.z))
    a = (w - c).normalized()
    pn = Vector((-sx, 0, 0))
    pn = (pn - a * a.dot(pn)).normalized()
    f = Vector((0, -1, 0))
    dorso = -pn

    def lados(n, fuerza=0.55):
        t = n.dot(dorso)
        return fuerza * (1.0 - ss(-0.3, 0.95, t)) + 0.12 * ss(-0.2, -0.9, t)

    def sombra_puno(co, n, s):
        return min(1.0, lados(n, 0.5) + 0.45 * abs(n.dot(a)) ** 2)

    puno, _ = tube([w - a * 0.045, w + a * 0.055], lambda u: (0.128 + 0.02 * math.sin(math.pi * u), 0.146 + 0.02 * math.sin(math.pi * u)),
                   k=32, steps=6, up=pn, cap_rings=4, cap=(0.55, 0.55))
    add(puno, "puno", hp, {hp: 1.0}, angle=89.0, sombra=sombra_puno)

    dt = (f * 0.80 + a * 0.46 + pn * 0.34).normalized()
    base = w + a * 0.10 + f * 0.07 + pn * 0.02
    raiz_pulgar = base + dt * 0.03

    def seccion(u):
        return (0.082 + 0.024 * ss(0.12, 0.42, u) - 0.008 * ss(0.75, 1.0, u),
                0.1 + 0.086 * ss(0.12, 0.5, u) - 0.012 * ss(0.8, 1.0, u))

    def sombra_manopla(co, n, s):
        v = lados(n) + 0.3 * (1.0 - ss(0.02, 0.12, s)) + 0.32 * (1.0 - ss(0.07, 0.16, (co - raiz_pulgar).length))
        return min(1.0, v)

    ctrl = [w + a * 0.0, w + a * 0.16 + pn * 0.012, w + a * MANOPLA_LARGO + pn * 0.045]
    cuerpo, _ = tube(ctrl, seccion, k=32, steps=10, up=pn, cap_rings=8, cap=(0.5, 1.0), expo=2.4)
    b1, b2 = lado + "Manopla1", lado + "Manopla2"
    punta = w + a * (MANOPLA_LARGO + 0.13) + pn * 0.05
    BONES_MANOS.append((b1, hp, tuple(w + a * NUDILLO), tuple(w + a * DOBLEZ + pn * 0.018)))
    BONES_MANOS.append((b2, b1, tuple(w + a * DOBLEZ + pn * 0.018), tuple(punta)))
    add(cuerpo, "guante", hp, chain_weights([hp, b1, b2], [NUDILLO, DOBLEZ], 0.045), s_layer=True, angle=89.0, sombra=sombra_manopla)

    def sombra_pulgar(co, n, s):
        return min(1.0, lados(n, 0.5) + 0.35 * (1.0 - ss(0.03, 0.1, s)))

    tpts = [base, base + dt * 0.10 + a * 0.014, base + dt * 0.19 + a * 0.034]
    pulgar, ts = tube(tpts, lambda u: 0.08 - 0.016 * u + 0.008 * ss(0.55, 1.0, u), k=24, steps=6, cap_rings=6, cap=(0.6, 1.0))
    p1, p2 = lado + "Pulgar1", lado + "Pulgar2"
    BONES_MANOS.append((p1, hp, tuple(base + dt * 0.06), tuple(base + dt * 0.135)))
    BONES_MANOS.append((p2, p1, tuple(base + dt * 0.135), tuple(tpts[-1] + dt * 0.07)))
    add(pulgar, "guante", hp, chain_weights([hp, p1, p2], [0.06, 0.135], 0.03), s_layer=True, angle=89.0, sombra=sombra_pulgar)
    if side == "Right":
        AGARRE.xyz = w + a * 0.17 + pn * 0.23


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

    add(cabeza, "body", "Head", {"Head": 1.0}, angle=89.0)
    cuello, _ = tube([Vector((0, 0, 1.96)), Vector((0, 0, 2.42))], lambda u: 0.2, k=20, steps=1, cap_rings=2)
    add(cuello, "body", "Head", "core", angle=89.0)

    cuerpo = revolucion(suave(CUERPO, 2), 40, 2.25)
    ttree = BVHTree.FromBMesh(cuerpo)

    def frente(x, z, lado=-1):
        loc, nrm, _, _ = ttree.ray_cast(Vector((x, lado * 5.0, z)), Vector((0, -lado, 0)))
        return loc, nrm

    def arriba(x, y=0.0):
        loc, nrm, _, _ = ttree.ray_cast(Vector((x, y, 5.0)), Vector((0, 0, -1)))
        return loc, nrm

    add(cuerpo, lambda c, s: "navy" if c.z < Z_CINTURON else "cream", core_part, "core", angle=70.0)

    cin = []
    for j in range(36):
        th = 2 * math.pi * j / 36
        d = Vector((math.cos(th), math.sin(th), 0.0))
        loc, _, _, _ = ttree.ray_cast(Vector((0, 0, Z_CINTURON)) + d * 3.0, -d)
        cin.append(loc + d * 0.012)
    cinturon, _ = tube(cin, lambda u: (0.026, 0.058), k=8, steps=1, closed=True, up=Vector((0, 0, 1)), expo=3.0)
    add(cinturon, "belt", "LowerTorso", {"LowerTorso": 1.0}, angle=60.0)
    lb, nb_ = frente(0.0, Z_CINTURON)
    add(redondeado((0.085, 0.04, 0.066), Matrix.Translation(lb + Vector((0, -0.045, 0))), 16, 8), "gold", "LowerTorso", {"LowerTorso": 1.0}, angle=60.0)

    lk, _ = frente(0.0, 2.03)
    add(ellipsoid((0.07, 0.055, 0.065), Matrix.Translation(lk + Vector((0, -0.035, 0))), 14, 8), "teal", "UpperTorso", "core", angle=89.0)
    tie = []
    for z in (2.0, 1.86, 1.72, 1.58, 1.46):
        l2, n2 = frente(0.0, z)
        tie.append(l2 + n2 * 0.034)
    corbata, _ = tube(tie, lambda u: (0.02, 0.048 + 0.04 * ss(0.0, 0.85, u)), k=14, steps=4, up=Vector((0, -1, 0)), cap_rings=4, cap=(0.3, 0.9), expo=2.4)
    add(corbata, "teal", core_part, "core", angle=70.0)
    for sx in (-1, 1):
        lc, nc = frente(sx * 0.09, 2.05)
        mat = Matrix.Translation(lc + nc * 0.02) @ Matrix.Rotation(math.radians(-sx * 38), 4, "Y") @ Matrix.Rotation(math.radians(-25), 4, "X")
        add(redondeado((0.11, 0.022, 0.06), mat, 14, 8, 0.7), "cream", "UpperTorso", "core", angle=70.0)


    loc, n = frente(0.27, 1.80)
    fr = Matrix.Translation(loc + n * 0.025) @ frame_from_normal(n)
    add(cylinder(0.05, 0.04, fr, 16), "gold", "UpperTorso", "core", angle=40.0)
    for sx in (-1, 1):
        wm = fr @ Matrix.Translation((sx * 0.09, 0.01, 0.0)) @ Matrix.Rotation(math.radians(sx * 14), 4, "Z")
        add(ellipsoid((0.085, 0.028, 0.016), wm, 12, 6), "gold", "UpperTorso", "core", angle=89.0)
    loc, n = frente(-0.27, 1.74)
    fr = Matrix.Translation(loc + n * 0.02) @ frame_from_normal(n)
    add(redondeado((0.12, 0.05, 0.022), fr @ Matrix.Translation((0, 0.06, 0)), 14, 8, 0.6), "cream", "UpperTorso", "core", angle=70.0)
    add(redondeado((0.026, 0.1, 0.024), fr @ Matrix.Translation((0.06, 0.08, 0.014)) @ Matrix.Rotation(math.radians(-8), 4, "Z"), 8, 6, 0.7),
        "orange", "UpperTorso", "core", angle=60.0)

    for sx in (-1, 1):
        lo, no = hit(sx * OJO_X, ZE)
        ne = (no + Vector((0, -1, 0))).normalized()
        OJOS_MARCO.append((sx, dict(OJOS)[sx], lo + ne * 0.036, ne))

    for sx, ceja, mej in ((1, "CejaIzq", "MejillaIzq"), (-1, "CejaDer", "MejillaDer")):
        pts = []
        for x, z in ((0.20, ZE + 0.29), (0.33, ZE + 0.335), (0.46, ZE + 0.30)):
            l2, n2 = hit(sx * x, z)
            pts.append(l2 + n2 * 0.03)
        brow, _ = tube(pts, lambda u: 0.042 * (0.65 + 0.35 * math.sin(math.pi * u)), k=12, steps=4, cap_rings=3)
        add(brow, "black", "Head", {ceja: 1.0}, angle=89.0)
        BONES_CARA.append((ceja, "Head", tuple(pts[1]), tuple(pts[1] + Vector((0, 0, 0.08)))))
        lc, nc = hit(sx * 0.56, ZE - 0.24)
        add(ellipsoid((0.13, 0.095, 0.05), Matrix.Translation(lc - nc * 0.012) @ frame_from_normal(nc), 18, 9), "blush", "Head", {mej: 1.0}, angle=89.0)
        BONES_CARA.append((mej, "Head", tuple(lc), tuple(lc + nc * 0.1)))

    ln, nn = hit(0.0, ZE - 0.15)
    add(ellipsoid((0.085, 0.075, 0.08), Matrix.Translation(ln + nn * 0.035) @ frame_from_normal(nn), 18, 10), "body", "Head", {"Nariz": 1.0}, angle=89.0)
    BONES_CARA.append(("Nariz", "Head", tuple(ln - nn * 0.04), tuple(ln + nn * 0.12)))

    boca, zm = build_mouth(hit)
    lt, nt_ = hit(0.035, zm - 0.03)
    frd = Matrix.Translation(lt + nt_ * 0.045) @ frame_from_normal(nt_) @ Matrix.Rotation(math.radians(-6), 4, "Z")
    add(redondeado((0.034, 0.036, 0.02), frd, 12, 8), "white", "Head", {"BocaSup": 1.0}, angle=70.0)

    lm, _ = hit(0.0, zm)
    piv = Vector((0.0, lm.y, zm - 0.03))
    tpts = [piv + Vector((0, 0.46, 0)), piv + Vector((0, 0.26, 0)), piv + Vector((0, 0.1, 0))]
    lengua, _ = tube(tpts, lambda u: (0.032, 0.054 + 0.032 * ss(0.45, 1.0, u)), k=16, steps=4, up=Vector((0, 0, 1)), cap_rings=4, cap=(0.6, 1.0), expo=2.2)
    add(lengua, "tongue", "Head", {"Lengua": 1.0}, angle=89.0)
    BONES_CARA.append(("Lengua", "BocaInf", tuple(piv), tuple(piv + Vector((0, -0.12, 0)))))
    BONES_CARA.insert(0, ("BocaInf", "Head", (0.0, lm.y, zm - 0.02), (0.0, lm.y, zm - 0.12)))
    BONES_CARA.insert(0, ("BocaSup", "Head", (0.0, lm.y, zm + 0.02), (0.0, lm.y, zm + 0.12)))

    for variante in VARIANTES_OJOS:
        ojos_render(variante)

    add(boca, "mouth", "Head", "mouth", angle=80.0)

    for side, sx in (("Left", 1), ("Right", -1)):
        h, c, w = Vector((sx * HOMBRO.x, 0, HOMBRO.z)), Vector((sx * CODO.x, 0, CODO.z)), Vector((sx * MUNECA.x, 0, MUNECA.z))
        dh = (c - h).normalized()
        arm, cs = tube([h, c, w], lambda u: 0.122 - 0.012 * u, k=20, steps=6, cap_rings=3)
        s_el, s_wr = cs[1], cs[2]
        wf = chain_weights([side + "UpperArm", side + "LowerArm", side + "Hand"], [s_el, s_wr - 0.03], 0.09)
        add(arm, "body", (lambda c_, s_, se=s_el, sd=side: sd + ("UpperArm" if s_ < se else "LowerArm")), wf, s_layer=True, angle=89.0)
        ua = side + "UpperArm"
        manga, ms = tube([h - dh * 0.06, h + dh * 0.08, h + dh * 0.21], lambda u: 0.168 + 0.012 * u, k=24, steps=3, cap_rings=3, cap=(1.0, 0.32))
        fin = ms[-1]
        add(manga, (lambda c_, s_, f_=fin: "teal" if s_ > f_ - 0.035 else "cream"), ua, {ua: 1.0}, s_layer=True, angle=70.0)
        mtree = BVHTree.FromBMesh(manga)
        pts = []
        for x in (0.29, 0.44, 0.59):
            o = Vector((sx * x, 0.0, 5.0))
            zs = [r[0].z for r in (mtree.ray_cast(o, Vector((0, 0, -1))), ttree.ray_cast(o, Vector((0, 0, -1)))) if r[0] is not None]
            pts.append(Vector((sx * x, 0.0, max(zs) + 0.036)))
        hombrera, hs = tube(pts, lambda u: (0.03, 0.11), k=12, steps=6, up=Vector((0, 0, 1)), cap_rings=3, cap=(0.6, 0.6), expo=3.2)
        largo = hs[-1]
        franjas = ((largo - 0.12, largo - 0.09), (largo - 0.07, largo - 0.04))
        mitad = (lambda s_, u_=ua: {"UpperTorso": 1.0 - 0.5 * ss(0.06, 0.26, s_), u_: 0.5 * ss(0.06, 0.26, s_)})
        add(hombrera, (lambda c_, s_, fr=franjas: "gold" if any(a <= s_ <= b for a, b in fr) else "navy"), "UpperTorso", mitad, s_layer=True, angle=60.0)
        boton = pts[0].lerp(pts[1], 0.3)
        add(ellipsoid((0.03, 0.03, 0.022), Matrix.Translation(boton + Vector((0, 0, 0.03))), 10, 6), "gold", "UpperTorso", {"UpperTorso": 1.0}, angle=89.0)

        build_mano(side, sx)

        k_, a_ = Vector((sx * RODILLA.x, 0, RODILLA.z)), Vector((sx * TOBILLO.x, 0, TOBILLO.z))
        hip = Vector((sx * CADERA.x, 0, CADERA.z))
        lctrl = [hip + Vector((0, 0, -0.14)), k_, a_ - Vector((0, 0, 0.02))]
        leg, lcs = tube(lctrl, lambda u: 0.148 + 0.012 * ss(0.55, 0.75, u), k=20, steps=9, cap_rings=3)
        s_kn, s_an = lcs[1], lcs[2]
        lw = chain_weights([side + "UpperLeg", side + "LowerLeg", side + "Foot"], [s_kn, s_an - 0.06], 0.1)

        def calcetin(c_, s_):
            if c_.z > 0.505:
                return "body"
            if 0.445 < c_.z < 0.475 or 0.395 < c_.z < 0.425:
                return "teal" if c_.z > 0.44 else "orange"
            return "white"
        add(leg, calcetin, (lambda c_, s_, sk=s_kn, sd=side: sd + ("UpperLeg" if s_ < sk else "LowerLeg")), lw, s_layer=True, angle=89.0)
        ul = side + "UpperLeg"
        pierna, _ = tube([hip + Vector((-sx * 0.03, 0, 0.10)), hip + Vector((sx * 0.005, 0, -0.3))], lambda u: 0.198 + 0.016 * u,
                         k=24, steps=3, cap_rings=3, cap=(1.0, 0.3))
        add(pierna, "navy", ul, {ul: 1.0}, angle=70.0)

        fp = side + "Foot"
        cana, _ = tube([Vector((sx * 0.27, 0.0, 0.36)), Vector((sx * 0.27, -0.03, 0.10))], lambda u: 0.178 + 0.012 * u, k=24, steps=2, cap_rings=3, cap=(0.4, 0.6))
        add(cana, "boot", fp, {fp: 1.0}, angle=70.0)
        bota = ellipsoid((0.205, 0.315, 0.165), Matrix.Translation((sx * 0.27, -0.11, 0.155)), 28, 14)
        for v in bota.verts:
            v.co.z = max(v.co.z, 0.075)
        add(bota, "boot", fp, {fp: 1.0}, angle=50.0)
        suela = ellipsoid((0.222, 0.335, 0.07), Matrix.Translation((sx * 0.27, -0.11, 0.055)), 28, 9)
        for v in suela.verts:
            v.co.z = max(v.co.z, 0.0)
        add(suela, "sole", fp, {fp: 1.0}, angle=50.0)


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
        vmaps = {}
        for f in bm.faces:
            c = f.calc_center_median()
            s = sum(v[sl] for v in f.verts) / len(f.verts) if sl else 0.0
            if callable(pr.part):
                part = pr.part(c, s) if sl else pr.part(c)
            else:
                part = pr.part
            role = pr.role(c, s) if callable(pr.role) else pr.role
            uv = swatch_uv(role)
            gradiente = pr.sombra is not None and isinstance(PALETTE[role][1], tuple) and isinstance(PALETTE[role][1][0], str)
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
                a["uv"].append(swatch_uv(role, pr.sombra(v.co, v.normal, v[sl] if sl else 0.0)) if gradiente else uv)
            a["f"].append(tuple(idx))
    return acc


def make_palette_image():
    size = 64
    img = bpy.data.images.new("TripulantePalette", size, size, alpha=True)
    px = [0.0] * (size * size * 4)
    for role, (i, col) in PALETTE.items():
        gx, gy = i % 4, i // 4
        for y in range(gy * 16, gy * 16 + 16):
            if isinstance(col, str):
                rgba = (*hex_rgb(col), 1.0)
            elif isinstance(col[0], str):
                t = min(1.0, max(0.0, (y - gy * 16 - 1.0) / 13.0))
                c0, c1 = hex_rgb(col[0]), hex_rgb(col[1])
                rgba = (*(c0[k] + (c1[k] - c0[k]) * t for k in range(3)), 1.0)
            else:
                rgba = col
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
    tex.interpolation = "Linear"
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
        (_lado + "Hand", _lado + "LowerArm", _w, (_sx * (MUNECA.x + 0.1), 0, MUNECA.z - 0.42)),
    ]
for _lado, _sx in (("Left", 1), ("Right", -1)):
    _h, _k, _a = (_sx * CADERA.x, 0, CADERA.z), (_sx * RODILLA.x, 0, RODILLA.z), (_sx * TOBILLO.x, 0, TOBILLO.z)
    BONES += [
        (_lado + "UpperLeg", "LowerTorso", _h, _k),
        (_lado + "LowerLeg", _lado + "UpperLeg", _k, _a),
        (_lado + "Foot", _lado + "LowerLeg", _a, (_sx * 0.27, -0.42, 0.08)),
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


def cara(boca=0.0, cejas=0.0, giro=0.0, lengua=0.0, lado=0.0, mejillas=0.0, flop=0.0, fase=0.0):
    # La lengua gira alrededor de la boca (su hueso nace en el labio) y luego sale en la direccion a la que apunta,
    # como CFrame.fromEulerAnglesYXZ(...) * CFrame.new(...) en Cara.luau. flop = lengua de perro al viento al gritar.
    f1 = min(flop, 1.0)
    fuera = (0.07 * boca + 0.14 * lengua) * (1.0 - f1) + 0.4 * flop
    caida = 0.35 * lengua * (1.0 - f1) + flop * (0.45 + 0.18 * math.sin(fase * 17))
    vuelta = lado * 0.44 + flop * (0.55 * math.sin(fase * 23) + 0.25 * math.sin(fase * 11.3))
    torsion = flop * 0.35 * math.sin(fase * 19 + 1)
    giro_l = Matrix.Rotation(vuelta, 3, "Z") @ Matrix.Rotation(caida, 3, "X") @ Matrix.Rotation(torsion, 3, "Y")
    r = [
        ("BocaSup", "T", (0.0, 0.0, 0.065 * boca)),
        ("BocaInf", "T", (lado * 0.04, -0.06 * boca, -0.25 * boca)),
        ("Lengua", "Y", math.degrees(torsion)),
        ("Lengua", "X", math.degrees(caida)),
        ("Lengua", "Z", math.degrees(vuelta)),
        ("Lengua", "T", tuple(giro_l @ Vector((lado * 0.03, -fuera, -0.03 * lengua)))),
    ]
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


# Manopla (doblez del nudillo, doblez de la punta) y pulgar (base, punta, apertura), en grados. Igual que POSES en Manos.luau.
POSES_MANO = {
    "abierta": (-12, -8, -10, -4, 30),
    "relajada": (26, 28, 24, 20, -6),
    "agarre": (40, 60, 30, 26, -6),
    "puno": (88, 98, 46, 44, -10),
    "pulsar": (-4, -2, 40, 38, -12),
    "palma": (4, 6, -8, 0, 12),
    "primera": (10, 14, 14, 10, 4),
    "bofetada": (-16, -10, -14, -6, 32),
    "dos": (34, 46, 22, 18, 0),
    "sosten": (18, 24, 26, 22, -8),
}


# Primera persona (Camara.luau): en tu propia vista no se ven los brazos, solo las manoplas, y cada una se coloca en el
# espacio de la camara (X derecha, Y arriba, -Z delante, como en Roblox). Cada postura es x e y como fraccion de media
# pantalla a esa profundidad, profundidad z, y en grados cabeceo (dedos hacia arriba), guinada hacia dentro, alabeo sobre los
# dedos e inclinacion en la pantalla (mano derecha; la izquierda es su espejo). Los mismos numeros que VISTA en Camara.luau.
VISTA = {
    "reposo": (0.54, -0.78, 0.86, 50, 0, -22, 30),
    "alcance": (0.2, -0.46, 1.1, 68, 6, -12, 16),
    "pulsar": (0.1, -0.42, 1.0, 74, 0, -6, 10),
    "bofetadaAtras": (0.8, -0.5, 0.8, 64, 40, -10, -10),
    "bofetadaGolpe": (-0.02, -0.36, 0.92, 74, 28, 0, 22),
    "lanzar": (0.24, -0.44, 1.2, 66, 8, -30, 12),
    "puno": (0.32, -0.66, 0.92, 62, 0, -18, 12),
    "vaso": (0.32, -0.64, 0.92, 64, 0, -18, 12),
    "palma": (0.3, -0.66, 1.0, 32, 10, -180, 8),
    "colgar": (0.46, -0.7, 0.95, 58, 4, -60, 8),
    "abrazo": (-0.06, 0.75, 0.1, 78, 35, 0, 0),
}
TAN_REF = math.tan(math.radians(40))
# Lo que sube un objeto llevado en la palma sobre el punto de agarre, ademas de su media altura (Manos.desfase).
DESFASE_PALMA = -0.12
Q3 = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))
Q4 = Q3.to_4x4()


def base_mano(signo):
    dedos = Vector((0.12 * signo, -0.3, 0)).normalized()
    palma = Vector((-signo, 0, 0))
    palma = (palma - dedos * dedos.dot(palma)).normalized()
    h = Matrix((dedos, palma, dedos.cross(palma))).transposed()
    v = Matrix(((0, 0, -1), (0, -1, 0), (-1, 0, 0))).transposed()
    return v @ h.inverted()


def giro_vista(p, signo):
    return (Matrix.Rotation(signo * math.radians(p[6]), 3, "Z") @ Matrix.Rotation(signo * math.radians(p[4]), 3, "Y")
            @ Matrix.Rotation(math.radians(p[3]), 3, "X") @ Matrix.Rotation(signo * math.radians(p[5]), 3, "Z") @ base_mano(signo))


def en_vista(p, signo, tv, ancho):
    z = p[2] * math.sqrt(TAN_REF / tv)
    m = giro_vista(p, signo).to_4x4()
    m.translation = (signo * p[0] * ancho * tv * z, p[1] * tv * z, -z)
    return m


def abrazo(signo, caja_r, tam, cam_r, tv, ancho):
    """Como abrazo() de Camara.luau: las manoplas van a los lados del objeto en un marco centrado en el y girado solo con la
    camara (sin cabeceo), asi que se quedan pegadas aunque mires abajo; luego se meten en la pantalla si se salen."""
    frente = cam_r.to_3x3() @ Vector((0, 0, -1))
    frente.y = 0
    frente.normalize()
    derecha = frente.cross(Vector((0, 1, 0))).normalized()
    marco = Matrix((derecha, derecha.cross(frente), -frente)).transposed().to_4x4()
    marco.translation = caja_r.translation
    r = (marco.inverted() @ caja_r).to_3x3()
    h = tam / 2

    def ext(eje):
        return sum(abs(r.col[i].dot(eje)) * h[i] for i in range(3))
    p = VISTA["abrazo"]
    sitio = Matrix.Translation((signo * (ext(Vector((1, 0, 0))) + p[0]), ext(Vector((0, 1, 0))) * p[1], ext(Vector((0, 0, 1))) + p[2]))
    l = cam_r.inverted() @ marco @ sitio @ giro_vista(p, signo).to_4x4()
    fondo = max(0.6, -l.translation.z)
    x = min(0.85 * ancho * tv * fondo, max(-0.85 * ancho * tv * fondo, l.translation.x))
    y = min(0.6 * tv * fondo, max(-0.85 * tv * fondo, l.translation.y))
    l.translation = (x, y, -fondo)
    return l


def pose_mano(rig, side, vals):
    sx = 1 if side == "Left" else -1
    lado = LADOS[side]
    palma = Vector((-sx, 0, 0))
    cierre = Vector((-sx, 0.3, -0.2)).normalized()
    frente = Vector((0, -1, 0))
    bones = rig.data.bones
    for nombre, i, abre in (("Manopla", 0, 0), ("Pulgar", 2, 1)):
        b1, b2 = bones[lado + nombre + "1"], bones[lado + nombre + "2"]
        d = (b2.head_local - b1.head_local).normalized()
        eje = d.cross(cierre if nombre == "Pulgar" else palma).normalized()
        giro = Quaternion(d.cross(frente).normalized(), math.radians(abre * vals[4])) @ Quaternion(eje, math.radians(vals[i]))
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


def caja(ob):
    vs = [v.co for v in ob.data.vertices]
    mn = Vector([min(v[i] for v in vs) for i in range(3)])
    mx = Vector([max(v[i] for v in vs) for i in range(3)])
    return mn, mx


def material_color(nombre, hexa, rugosidad=0.5):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(hex_rgb(hexa)), 1.0)
    b.inputs["Roughness"].default_value = rugosidad
    return m


def objeto_malla(nombre, bm, mat, coll):
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    for pol in me.polygons:
        pol.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    coll.objects.link(ob)
    return ob


def primera_persona(scene, coll, rig, objs, mats, rdir):
    """Renders de primera persona con la camara del juego (ojos a 3,01, 0,5 por detras, 80 grados de campo vertical,
    mirando 10 grados hacia abajo) y las manoplas colocadas como en Camara.luau. Sin brazos, como en tu propia vista."""
    cajas = {o.name[:-4]: caja(o) for o in objs}

    def centro(side):
        mn, mx = cajas[side + "Hand"]
        return Q3 @ ((mn + mx) / 2)

    def opcion(nombre, defecto):
        return float(sys.argv[sys.argv.index(nombre) + 1]) if nombre in sys.argv else defecto

    # --fov y --aspecto solo para comprobar el encuadre (el slider de Ajustes va de 60 a 100; un movil apaisado es 19,5:9).
    fov = opcion("--fov", 80.0)
    aspecto = opcion("--aspecto", 16 / 9)
    tv = math.tan(math.radians(fov / 2))
    ancho = min(1.78, max(1.2, aspecto))
    cam_r = Matrix.Translation((0, ZE, 0.5)) @ Matrix.Rotation(math.radians(-10), 4, "X")
    rapido = "--rapido" in sys.argv
    suelo = bpy.data.materials["Ground"].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
    taza = material_color("Taza", "D9443A", 0.4)
    tapa = material_color("Tapa", "FFF4E0", 0.5)
    carton = material_color("Carton", "E6C8A0", 0.8)
    boton = material_color("Boton", "F27B2B", 0.4)

    def escena(nombre, der, izq, res, cosas=None, fondo="6B7A8F"):
        r2 = clone(rig, objs, coll, mats["Lavanda"], (0, 0, 0), solo={"RightHand_Geo", "LeftHand_Geo"})
        bpy.context.view_layer.update()
        for side, signo, (pv, mano) in (("Right", 1, der), ("Left", -1, izq)):
            m = pv if isinstance(pv, Matrix) else en_vista(VISTA[pv], signo, tv, ancho)
            d = Q4 @ cam_r @ m @ Matrix.Translation(-centro(side)) @ Q4
            r2.pose.bones[side + "Hand"].matrix = d @ r2.data.bones[side + "Hand"].matrix_local
            bpy.context.view_layer.update()
            pose_mano(r2, side, POSES_MANO[mano])
        extra = cosas(r2) if cosas else []
        suelo.default_value = (*lin(hex_rgb(fondo)), 1.0)
        cd = bpy.data.cameras.new("CamPrimera")
        cd.sensor_fit = "VERTICAL"
        cd.angle = math.radians(fov)
        cd.clip_start = 0.05
        co = bpy.data.objects.new("CamPrimera", cd)
        coll.objects.link(co)
        co.matrix_world = Q4 @ cam_r
        scene.camera = co
        scene.render.resolution_x, scene.render.resolution_y = round(res[1] * aspecto), res[1]
        scene.render.resolution_percentage = 50 if rapido else 100
        scene.cycles.samples = 16 if rapido else 48
        ruta = os.path.join(rdir, nombre + ".png")
        scene.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        for ch in list(r2.children):
            bpy.data.objects.remove(ch)
        bpy.data.objects.remove(r2)
        for ob in extra:
            bpy.data.objects.remove(ob)
        bpy.data.objects.remove(co)
        suelo.default_value = (*lin(hex_rgb("EFE9DC")), 1.0)
        return ruta

    def palma(r2):
        m = r2.pose.bones["RightHand"].matrix @ r2.data.bones["RightHand"].matrix_local.inverted()
        return m @ AGARRE, m.to_3x3() @ (Q3 @ Vector((-0.929, -0.371, 0.0)))

    def agarre(r2):
        c, n = palma(r2)
        c = c + n * (0.25 - 0.1)
        vaso = objeto_malla("Vaso", cylinder(0.23, 0.62, Matrix.Translation(c), 32), taza, coll)
        lid = objeto_malla("Tapa", cylinder(0.245, 0.06, Matrix.Translation(c + Vector((0, 0, 0.32))), 32), tapa, coll)
        return [vaso, lid]

    ojo_r = cam_r.translation
    mirada = cam_r.to_3x3() @ Vector((0, 0, -1))
    caja_r = Matrix.Translation(ojo_r + mirada * 2.5 - Vector((0, 1.85, 0)))
    tam = Vector((2.0, 2.0, 2.0))

    def caja_grande(r2):
        bm = redondeado((1.0, 1.0, 1.0), Q4 @ caja_r, 16, 10, 0.12)
        return [objeto_malla("Caja", bm, carton, coll)]

    def pulsador(r2):
        frente = Q3 @ (cam_r.to_3x3() @ Vector((0, 0, -1)))
        punta = Vector(r2.pose.bones["DerManopla2"].tail)
        m = Matrix.Translation(punta + frente * 0.12) @ frame_from_normal(-frente)
        return [objeto_malla("Pulsador", cylinder(0.2, 0.1, m, 32), boton, coll)]

    def en_mano(r2, radio, altura, giro):
        # Igual que Manos.marco y Manos.desfase: el objeto va derecho (o inclinado si es herramienta) sobre el punto de agarre,
        # separado de la palma lo que haga falta para que la manopla no se meta dentro (Manos.separacion).
        c, n = palma(r2)
        c = c + n * max(0.0, radio - 0.1)
        g = Q3 @ giro @ Q3
        return Matrix.Translation(c + g @ Vector((0, 0, altura))) @ g.to_4x4()

    def bandeja(r2):
        m = en_mano(r2, 0.0, 0.05 + DESFASE_PALMA, Matrix.Identity(3))
        return [objeto_malla("Bandeja", redondeado((0.6, 0.42, 0.05), m, 20, 8, 0.25), material_color("Metal", "A9B0B8", 0.3), coll),
                objeto_malla("Hamburguesa", redondeado((0.2, 0.2, 0.12), m @ Matrix.Translation((0.1, 0.0, 0.16)), 16, 8, 0.7), boton, coll)]

    def extintor(r2):
        m = en_mano(r2, 0.35, -0.6 * 0.9, Matrix.Rotation(math.radians(-20), 3, "X"))
        return [objeto_malla("Extintor", cylinder(0.3, 1.5, m, 32), taza, coll),
                objeto_malla("Asa", redondeado((0.12, 0.2, 0.08), m @ Matrix.Translation((0, 0, 0.82)), 12, 6, 0.6), material_color("Negro", "2E2A2C", 0.5), coll)]

    if "--encuadre" in sys.argv:
        escena("encuadre_%d_%.2f" % (fov, aspecto), ("reposo", "primera"), ("reposo", "primera"), (1600, 900))
        escena("encuadre_vaso_%d_%.2f" % (fov, aspecto), ("vaso", "sosten"), ("reposo", "primera"), (1600, 900), agarre)
        return
    escena("primera_reposo", ("reposo", "primera"), ("reposo", "primera"), (1600, 900))
    escena("primera_agarre", ("vaso", "sosten"), ("reposo", "primera"), (1600, 900), agarre)
    piezas = [
        escena("_p_bofetada", ("bofetadaGolpe", "bofetada"), ("reposo", "primera"), (800, 450)),
        escena("_p_pulsar", ("pulsar", "pulsar"), ("reposo", "primera"), (800, 450), pulsador),
        escena("_p_abrazo", (abrazo(1, caja_r, tam, cam_r, tv, ancho), "dos"), (abrazo(-1, caja_r, tam, cam_r, tv, ancho), "dos"), (800, 450), caja_grande),
        escena("_p_bandeja", ("palma", "palma"), ("reposo", "primera"), (800, 450), bandeja),
        escena("_p_extintor", ("puno", "sosten"), ("reposo", "primera"), (800, 450), extintor),
        escena("_p_claro", ("reposo", "primera"), ("reposo", "primera"), (800, 450), None, "F4F1EA"),
    ]
    imgs = [bpy.data.images.load(r) for r in piezas]
    w, h = imgs[0].size
    hoja = bpy.data.images.new("PrimeraAcciones", w * 3, h * 2, alpha=True)
    px = [0.0] * (w * 3 * h * 2 * 4)
    for k, im in enumerate(imgs):
        ox, oy = (k % 3) * w, (1 - k // 3) * h
        src = list(im.pixels[:])
        for y in range(h):
            o = ((oy + y) * w * 3 + ox) * 4
            px[o:o + w * 4] = src[y * w * 4:(y + 1) * w * 4]
    hoja.pixels = px
    hoja.filepath_raw = os.path.join(rdir, "primera_acciones.png")
    hoja.file_format = "PNG"
    hoja.save()
    for r in piezas:
        os.remove(r)


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
    print("SEPARAR_CAPAS", sum(_SEP["separar_capas"](o) for o in objs))
    for o in build_meshes(coll, rig, acc, mat, ["Ojos_" + v for v in VARIANTES_OJOS]):
        OJOS_OBJ[o.name[5:-4]] = o
        o.hide_render = True
        o.hide_set(True)
    tc = {o.name[:-4]: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}
    print("BONES", len(todos_huesos()), [b[0] for b in BONES_CARA + BONES_MANOS])
    for sx, e, c, n in OJOS_MARCO:
        if sx < 0:
            print("OJO CENTRO (%.3f, %.3f, %.3f) NORMAL (%.3f, %.3f, %.3f) z %.3f" % (-c.x, c.z - HRP_Z, c.y, -n.x, n.z, n.y, c.z))
    m1 = next(b for b in BONES_MANOS if b[0] == "DerManopla1")
    d = AGARRE - Vector(m1[2])
    print("CameraOffset Y %.3f" % (ZE - HRP_Z - 1.5))
    print("AGARRE_MANO (%.3f, %.3f, %.3f)" % (-d.x, d.z, d.y))
    alto = 0.0
    for o in objs:
        mn, mx = caja(o)
        alto = max(alto, mx.z)
        cen = (mn + mx) / 2
        print("PARTE %-14s tris %5d centro (%.3f, %.3f, %.3f) tamano (%.3f, %.3f, %.3f)" % (o.name[:-4], tc[o.name[:-4]], cen.x, cen.y, cen.z, *(mx - mn)))
    print("ALTO %.3f" % alto)
    print("TRIS", sum(tc.values()), "MAX", max(tc.values()))
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
    for i, nm in enumerate(("abierta", "relajada", "agarre", "puno", "pulsar", "palma")):
        r2 = clone(rig, objs, coll, mats["Lavanda"], (i * 0.85, 0, 0), solo={"RightHand_Geo", "RightLowerArm_Geo"})
        bpy.context.view_layer.update()
        pose_mano(r2, "Right", POSES_MANO[nm])
        hechos.append(r2)
        if nm == "agarre":
            c = r2.matrix_world @ AGARRE
            bm = cylinder(0.11, 0.55, Matrix.Translation(c) @ Matrix.Rotation(math.radians(90), 4, "X"), 24)
            me = bpy.data.meshes.new("Barra")
            bm.to_mesh(me)
            me.materials.append(cm)
            bo = bpy.data.objects.new("Barra", me)
            coll.objects.link(bo)
            hechos.append(bo)
    cielo = scene.world.node_tree.nodes["Background"].inputs[0]
    cielo.default_value = (*lin(hex_rgb("51607A")), 1.0)
    for nombre, loc in (("manos_prueba", (1.4, -6.0, 1.15)), ("manos_prueba_palma", (5.0, -4.6, 1.2))):
        co = camera(scene, loc=loc, target=(1.4, 0, 1.15), ortho=5.0)
        scene.render.resolution_x, scene.render.resolution_y = 1600, 520
        scene.cycles.samples = 48
        scene.render.filepath = os.path.join(rdir, nombre + ".png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(co)
    cielo.default_value = (*lin(hex_rgb("BFE3F2")), 1.0)
    for r2 in hechos:
        for ch in list(r2.children):
            bpy.data.objects.remove(ch)
        bpy.data.objects.remove(r2)
    if "--render" in sys.argv or "--primera" in sys.argv:
        primera_persona(scene, coll, rig, objs, mats, rdir)
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
        ("Lima", (-3.3, 0, 0), 12, wave + boca(0.55)),
        ("Lavanda", (-1.1, 0, 0), 4, []),
        ("Chicle", (1.1, 0, 0), -4, carry + boca(1.0)),
        ("Sol", (3.3, 0, 0), -14, run + boca(0.3)),
    ], dict(loc=(0.5, -12.5, 4.0), target=(0, 0, 1.85), lens=42), (1600, 900), 96)
    shot("turnaround", [("Lavanda", (-3.6 + 2.4 * i, 0, 0), rz, []) for i, rz in enumerate((0, -40, -90, 180))],
         dict(loc=(0, -20, 2.0), target=(0, 0, 2.0), ortho=10.6), (1600, 640), 96)
    cam_caras = dict(loc=(0, -6.6, 3.2), target=(0, 0, 2.95), lens=38)
    shot("caras_voz", [
        ("Lima", (-2.2, 0, 0), 0, []),
        ("Lavanda", (0.0, 0, 0), 0, cara(boca=0.55, cejas=0.4, lengua=0.1, mejillas=0.5)),
        ("Chicle", (2.2, 0, 0), 0, cara(boca=1.15, cejas=1.2, giro=-0.5, lengua=0.5, mejillas=0.3), "grande"),
    ], cam_caras, (1600, 700), 64)
    shot("caras_eventos", [
        ("Sol", (-3.3, 0, 0), 0, cara(boca=0.6, cejas=1.4), "grande"),
        ("Lavanda", (-1.1, 0, 0), 0, cara(boca=0.35, cejas=0.9, giro=-1.0, mejillas=0.2) + [("Head", "Y", -6)], "susto"),
        ("Lima", (1.1, 0, 0), 0, cara(boca=0.4, cejas=0.3, giro=0.4, lengua=1.0, lado=1.0) + [("CejaIzq", "T", (0, 0, 0.07)), ("Head", "Y", 12)], "mareo"),
        ("Chicle", (3.3, 0, 0), 0, cara(boca=0.5, cejas=0.6, giro=-0.3, mejillas=1.0), "feliz"),
    ], dict(loc=(0, -9.2, 3.2), target=(0, 0, 2.95), lens=38), (1600, 560), 64)
    shot("caras_grito", [
        ("Sol", (-2.2, 0, 0), 8, cara(boca=1.15, cejas=1.2, giro=-0.5, mejillas=1.5, flop=1.0, fase=0.068), "grande"),
        ("Lima", (0.0, 0, 0), 8, cara(boca=1.15, cejas=1.3, giro=-0.6, mejillas=1.5, flop=1.0, fase=0.0), "susto"),
        ("Chicle", (2.2, 0, 0), 8, cara(boca=1.15, cejas=1.2, giro=-0.5, mejillas=1.5, flop=1.0, fase=0.21), "grande"),
    ], dict(loc=(1.6, -6.4, 2.6), target=(0, 0, 2.8), lens=38), (1600, 700), 64)
    shot("caras_enfado", [
        ("Sol", (-1.1, 0, 0), 0, cara(boca=0.12, cejas=-0.8, giro=1.0), "enfado"),
        ("Lima", (1.1, 0, 0), 20, cara(boca=0.5, cejas=0.5, lengua=0.4, mejillas=0.5)),
    ], dict(loc=(0, -5.8, 3.2), target=(0, 0, 2.95), lens=38), (1200, 600), 64)
    shot("brazos_prueba", [
        ("Sol", (-3.3, 0, 0), 20, [("LeftUpperArm", "Y", -150), ("RightUpperArm", "Y", 150)] + boca(0.6)),
        ("Lima", (-1.1, 0, 0), 30, [("LeftUpperArm", "X", -75), ("RightUpperArm", "X", -75), ("LeftLowerArm", "X", -35), ("RightLowerArm", "X", -35)]),
        ("Lavanda", (1.1, 0, 0), 30, [("LeftUpperArm", "Y", -88), ("RightUpperArm", "Y", 88), ("LeftLowerArm", "X", -90), ("RightLowerArm", "X", -90)]),
        ("Chicle", (3.3, 0, 0), 25, [("UpperTorso", "X", 15), ("LeftUpperArm", "X", 60), ("RightUpperArm", "X", 60), ("LeftLowerArm", "X", -40), ("RightLowerArm", "X", -40), ("LeftUpperLeg", "X", -60), ("RightUpperLeg", "X", -60), ("LeftLowerLeg", "X", 80), ("RightLowerLeg", "X", 80)]),
    ], dict(loc=(0.5, -12.5, 4.0), target=(0, 0, 1.85), lens=42), (1600, 900), 64)


main()
