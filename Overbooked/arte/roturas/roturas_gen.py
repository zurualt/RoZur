import bpy
import bmesh
import math
import os
import sys
import json
import random
from mathutils import Vector, Matrix

OUT = os.path.dirname(os.path.abspath(__file__))
ARTE = os.path.dirname(OUT)
RAIZ = os.path.dirname(ARTE)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def cargar(rel):
    ruta = os.path.join(ARTE, rel)
    with open(ruta, encoding="utf-8") as fh:
        src = fh.read()
    src = src[:src.rstrip().rfind("\nmain()")]
    ns = {"__file__": ruta, "__name__": "generador"}
    exec(compile(src, ruta, "exec"), ns)
    ns["OUT"] = OUT
    return ns


A = cargar(os.path.join("avion", "avion_gen.py"))
P = cargar(os.path.join("pasajeros", "pasajeros_gen.py"))

CREAM, ORANGE, TEAL, DARK, BLACK, WHITE, RED, GLASS, SK1, SK2, SK3, SK4, GREEN, DGREEN, BLUE, YELLOW = range(16)
R0, ZC0 = A["R0"], A["ZC0"]
tube, ellipsoid, cylinder, loft, lathe, mirror_x = P["tube"], A["ellipsoid"], A["cylinder"], A["loft"], A["lathe"], A["mirror_x"]

CORTE_Y = -8.4
AMP_FUS = 0.5
CORTE_X = 27.0
CORTE_Z = 14.3
FILA_TECHO = -14.5
GONDOLA_H = 4.0

rnd = random.Random(7)
JAG_W = [rnd.uniform(0.5, 1.0) for _ in range(11)]
JAG_D = [rnd.uniform(0.5, 1.0) for _ in range(8)]
JAG_T = [rnd.uniform(0.3, 1.0) for _ in range(25)]


def alterno(i, amp, tabla):
    return amp * (1 if i % 2 == 0 else -1) * tabla[i]


def capa(bm, color):
    cl = bm.faces.layers.int.get("c") or bm.faces.layers.int.new("c")
    for f in bm.faces:
        f[cl] = color
    return cl


def caja(cx, cy, cz, sx, sy, sz, bev=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation((cx, cy, cz)) @ Matrix.Diagonal((sx, sy, sz, 1.0)), verts=bm.verts)
    if bev > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bev, segments=2, affect="EDGES", profile=0.5)
    return bm


def lamina(pts, n, grosor, ca, cb, lados=True):
    n = Vector(n).normalized()
    bm = bmesh.new()
    cl = bm.faces.layers.int.new("c")
    a = [bm.verts.new(Vector(p)) for p in pts]
    b = [bm.verts.new(Vector(p) - n * grosor) for p in pts]
    fa = bm.faces.new(a)
    fa.normal_update()
    if fa.normal.dot(n) < 0:
        fa.normal_flip()
    fa[cl] = ca
    fb = bm.faces.new(b)
    fb.normal_update()
    if fb.normal.dot(n) > 0:
        fb.normal_flip()
    fb[cl] = cb
    if lados:
        c = sum((Vector(p) for p in pts), Vector()) / len(pts)
        m = len(pts)
        for i in range(m):
            j = (i + 1) % m
            f = bm.faces.new((a[i], a[j], b[j], b[i]))
            f.normal_update()
            if f.normal.dot(f.calc_center_median() - c) < 0:
                f.normal_flip()
            f[cl] = cb
    return bm


def banda(exterior, interior, ca, cb, sep=0.03, normal=None):
    bm = bmesh.new()
    cl = bm.faces.layers.int.new("c")
    m = len(exterior)
    for lado, col in ((1, ca), (-1, cb)):
        off = Vector(normal) * sep * 0.5 * lado if normal else Vector()
        ex = [bm.verts.new(Vector(p) + off) for p in exterior]
        it = [bm.verts.new(Vector(p) + off) for p in interior]
        for i in range(m):
            j = (i + 1) % m
            f = bm.faces.new((ex[i], ex[j], it[j], it[i]) if lado == 1 else (ex[j], ex[i], it[i], it[j]))
            f[cl] = col
    return bm


def cable(pts, r, col, k=5):
    return (tube([Vector(p) for p in pts], lambda u: r * (1.0 - 0.3 * u), k=k, steps=3, cap_rings=1), col, 60.0)


def bbox_bm(bm):
    cs = [v.co for v in bm.verts]
    return (Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs))),
            Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs))))


def partir_bm(bm, eje, valor, jag):
    no = Vector((0.0, 0.0, 0.0))
    no[eje] = 1.0
    co = Vector((0.0, 0.0, 0.0))
    co[eje] = valor
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5, plane_co=co, plane_no=no)
    corte = [g for g in r["geom_cut"] if isinstance(g, bmesh.types.BMVert)]
    lado = [f.calc_center_median()[eje] > valor for f in bm.faces]
    jag(corte)
    out = []
    for mayor in (False, True):
        c = bm.copy()
        c.faces.ensure_lookup_table()
        bmesh.ops.delete(c, geom=[f for f, l in zip(c.faces, lado) if l != mayor], context="FACES")
        bmesh.ops.delete(c, geom=[v for v in c.verts if not v.link_faces], context="VERTS")
        out.append(c)
    return out[0], out[1], [v.co.copy() for v in corte]


def tapar(bm):
    cl = bm.faces.layers.int.get("c")
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    t = bmesh.ops.triangulate(bm, faces=r["faces"])
    for f in t["faces"]:
        f[cl] = DARK
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def jag_fus(verts):
    for v in verts:
        th = math.atan2(v.co.x, v.co.z - ZC0)
        v.co.y += AMP_FUS * (0.55 * math.cos(9 * th) + 0.45 * math.cos(17 * th))


def ordenar(pts, a, b):
    c = sum((Vector(p) for p in pts), Vector()) / len(pts)
    return sorted(pts, key=lambda p: math.atan2(p[b] - c[b], p[a] - c[a]))


def jag_lazo(eje, amp, tabla, a, b):
    def f(verts):
        if not verts:
            return
        c = sum((v.co for v in verts), Vector()) / len(verts)
        orden = sorted(verts, key=lambda v: math.atan2(v.co[b] - c[b], v.co[a] - c[a]))
        for k, v in enumerate(orden):
            d = alterno(k % len(tabla), amp, tabla)
            if eje == 0:
                d *= 1 if v.co.x > 0 else -1
            v.co[eje] += d
    return f


DESPIECE = {}


def despiece():
    if DESPIECE:
        return DESPIECE
    A["build_plane"]()
    p = {n: [] for n in ("RotBase", "RotPuntaIzq", "RotPuntaDer", "RotCola", "RotDeriva")}
    lazos = {}
    for bm, col, ang in A["PRIMS"]:
        mn, mx = bbox_bm(bm)
        c = (mn + mx) * 0.5
        es_deriva = mx.z > CORTE_Z + 0.5 and mn.z < CORTE_Z and abs(c.x) < 2
        es_ala = mx.x - mn.x > 20 and mn.x * mx.x > 0
        if col is not None and (es_deriva or es_ala):
            capa(bm, col)
            col = None
        if es_deriva:
            baja, alta, corte = partir_bm(bm, 2, CORTE_Z, jag_lazo(2, 0.45, JAG_D, 0, 1))
            p["RotCola"].append((tapar(baja), None, ang))
            p["RotDeriva"].append((tapar(alta), None, ang))
            lazos["deriva"] = corte
        elif mn.z > CORTE_Z - 0.5 and abs(c.x) < 3:
            p["RotDeriva"].append((bm, col, ang))
        elif es_ala:
            s = 1 if c.x > 0 else -1
            menor, mayor, corte = partir_bm(bm, 0, s * CORTE_X, jag_lazo(0, 0.6, JAG_W, 1, 2))
            dentro, punta = (menor, mayor) if s == 1 else (mayor, menor)
            p["RotBase"].append((tapar(dentro), None, ang))
            p["RotPuntaIzq" if s == 1 else "RotPuntaDer"].append((tapar(punta), None, ang))
            lazos["ala", s] = corte
        elif min(abs(mn.x), abs(mx.x)) > CORTE_X and mn.x * mx.x > 0:
            p["RotPuntaIzq" if c.x > 0 else "RotPuntaDer"].append((bm, col, ang))
        elif mn.y < CORTE_Y < mx.y and mx.x - mn.x > 10:
            delante, detras, corte = partir_bm(bm, 1, CORTE_Y, jag_fus)
            p["RotBase"].append((delante, col, ang))
            p["RotCola"].append((detras, col, ang))
            if len(corte) > len(lazos.get("cola", [])):
                lazos["cola"] = corte
        else:
            if mn.y < CORTE_Y < mx.y:
                print("AVISO pieza cruzando el corte sin cortar", mn, mx)
            p["RotCola" if c.y > CORTE_Y else "RotBase"].append((bm, col, ang))
    DESPIECE.update(p)
    DESPIECE["lazos"] = lazos
    return DESPIECE


def radial(p):
    return Vector((p.x, 0.0, p.z - ZC0)).normalized()


def angulo(p):
    return math.atan2(p.x, p.z - ZC0)


def cerca_de(ext, th):
    return min(range(len(ext)), key=lambda k: abs(math.atan2(math.sin(angulo(ext[k]) - th), math.cos(angulo(ext[k]) - th))))


def p_borde_cola():
    ext = sorted(despiece()["lazos"]["cola"], key=angulo)
    n = len(ext)
    out = []
    interior = [p - radial(p) * 0.34 for p in ext]
    out.append((banda(ext, interior, DARK, DARK, 0.05, (0, 1, 0)), None, 50.0))
    labio = [p + radial(p) * 0.06 for p in ext]
    out.append((banda(labio, ext, CREAM, CREAM, 0.05, (0, 1, 0)), None, 50.0))
    for i, th in enumerate((0.25, 0.8, 1.35, 1.9, 2.5)):
        for sx in (-1, 1):
            k = cerca_de(ext, sx * th)
            a, b = ext[k], ext[(k + 1) % n]
            nr = radial((a + b) * 0.5)
            punta = (a + b) * 0.5 + nr * 0.55 + Vector((0, 0.9 if i % 2 == 0 else -0.9, 0))
            out.append((lamina([a, b, punta], (b - a).cross(punta - a), 0.04, CREAM, DARK, False), None, 60.0))
    for i, (th, s) in enumerate(((0.6, 1), (1.6, -1), (2.7, 1))):
        for sx in (-1, 1):
            q = interior[cerca_de(ext, sx * th)]
            nr = radial(q)
            pts = [q, q - nr * 0.3 + Vector((0, s * 0.6, 0)), q - nr * 0.2 + Vector((0, s * 1.3, -0.5)), q - nr * 0.5 + Vector((0, s * 1.6, -1.2))]
            out.append(cable(pts, 0.07, (RED, YELLOW, BLUE)[i]))
    return out


def borde_seccion(secs, adentro, n_eje):
    interior = [adentro(Vector(p)) for p in secs]
    return (banda(secs, interior, DARK, DARK, 0.04, n_eje), None, 50.0)


def p_borde_ala(sx):
    sec = ordenar(despiece()["lazos"]["ala", 1], 1, 2)
    zc = sum(p.z for p in sec) / len(sec)
    c = sum((Vector(p) for p in sec), Vector()) / len(sec)
    out = [borde_seccion(sec, lambda p: Vector((p.x, p.y, p.z + (zc - p.z) * 0.6)), (1, 0, 0))]
    out.append((caja(CORTE_X + 0.5, c.y - 0.8, c.z, 1.2, 0.35, 0.22), DARK, 40.0))
    out.append((caja(CORTE_X + 0.3, c.y + 2.4, c.z + 0.05, 0.8, 0.25, 0.18), DARK, 40.0))
    out.append(cable([c + Vector((0, -2.0, 0)), c + Vector((0.6, -2.3, -0.2)), c + Vector((1.2, -2.0, -0.7)), c + Vector((1.5, -1.6, -1.3))], 0.06, RED))
    out.append(cable([c + Vector((0, 1.0, 0)), c + Vector((0.7, 1.2, -0.1)), c + Vector((1.1, 0.8, -0.6)), c + Vector((1.2, 1.1, -1.1))], 0.06, YELLOW))
    for k in (1, len(sec) // 2 + 1):
        a, b = sec[k], sec[(k + 1) % len(sec)]
        punta = (a + b) * 0.5 + Vector((0.8, 0, 0.25 if (a.z + b.z) / 2 > zc else -0.25))
        out.append((lamina([a, b, punta], (b - a).cross(punta - a), 0.03, CREAM, DARK, False), None, 60.0))
    if sx == 1:
        return out
    return [(mirror_x(bm), col, ang) for bm, col, ang in out]


def p_borde_deriva():
    sec = ordenar(despiece()["lazos"]["deriva"], 0, 1)
    out = [borde_seccion(sec, lambda p: Vector((p.x * 0.4, p.y, p.z)), (0, 0, 1))]
    c = sum((Vector(p) for p in sec), Vector()) / len(sec)
    for sx in (-1, 1):
        out.append(cable([c + Vector((sx * 0.1, -2.0, 0)), c + Vector((sx * 0.3, -2.2, 0.6)), c + Vector((sx * 0.7, -1.7, 1.0)), c + Vector((sx * 0.9, -1.9, 1.4))], 0.06, RED if sx < 0 else YELLOW))
    out.append((caja(0, c.y + 1.5, CORTE_Z + 0.4, 0.22, 0.4, 1.0), DARK, 40.0))
    n = len(sec)
    for k in (n // 4, 3 * n // 4):
        a, b = sec[k], sec[(k + 1) % n]
        nx = Vector((a.x + b.x, 0, 0))
        nx = nx.normalized() if nx.length > 1e-4 else Vector((1, 0, 0))
        punta = (a + b) * 0.5 + Vector((0, 0, 0.7)) + nx * 0.35
        out.append((lamina([a, b, punta], (b - a).cross(punta - a), 0.03, TEAL, DARK, False), None, 60.0))
    return out


def radio_gondola(h):
    if h <= 3.0:
        return 2.2
    if h <= 6.0:
        return 2.2 - 0.04 * (h - 3.0)
    return 2.08 - (0.28 / 1.9) * (h - 6.0)


def gondola_pt(th, h, off):
    r = radio_gondola(h) + off
    return Vector((r * math.sin(th), h - GONDOLA_H, r * math.cos(th)))


def rejilla(nu, nv, fn, color_fn, invertir=False):
    bm = bmesh.new()
    cl = bm.faces.layers.int.new("c")
    vs = [[bm.verts.new(fn(i / nu, k / nv)) for k in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for k in range(nv):
            q = (vs[i][k], vs[i + 1][k], vs[i + 1][k + 1], vs[i][k + 1])
            f = bm.faces.new(q[::-1] if invertir else q)
            f[cl] = color_fn((i + 0.5) / nu, (k + 0.5) / nv)
    return bm


def orientar(bm, ref):
    bm.normal_update()
    for f in bm.faces:
        if f.normal.dot(ref(f.calc_center_median())) < 0:
            f.normal_flip()
    return bm


def p_capo():
    th0, h0, h1 = math.radians(58), 1.5, 6.3
    fuera = lambda u, v: gondola_pt(-th0 + 2 * th0 * u, h0 + (h1 - h0) * v, 0.11)
    dentro = lambda u, v: gondola_pt(-th0 + 2 * th0 * u, h0 + (h1 - h0) * v, 0.03)
    radial_g = lambda c: Vector((c.x, 0, c.z))
    ext = orientar(rejilla(14, 8, fuera, lambda u, v: ORANGE if v < 0.08 else CREAM), radial_g)
    inn = orientar(rejilla(14, 8, dentro, lambda u, v: DARK), lambda c: -radial_g(c))
    out = [(ext, None, 50.0), (inn, None, 50.0)]
    for u in (0.0, 1.0):
        th = -th0 + 2 * th0 * u
        pts = [gondola_pt(th, h0 + (h1 - h0) * k / 8, 0.11) for k in range(9)] + [gondola_pt(th, h0 + (h1 - h0) * k / 8, 0.03) for k in range(8, -1, -1)]
        out.append((lamina(pts, (math.cos(th) * (1 if u else -1), 0, -math.sin(th) * (1 if u else -1)), 0.0, DARK, DARK, False), None, 30.0))
        for h in (2.5, 5.0):
            p = gondola_pt(th, h, 0.16)
            out.append((caja(p.x, p.y, p.z, 0.3, 0.45, 0.16), BLACK, 30.0))
    for v in (0.0, 1.0):
        h = h0 + (h1 - h0) * v
        pts = [gondola_pt(-th0 + 2 * th0 * k / 14, h, 0.11) for k in range(15)] + [gondola_pt(-th0 + 2 * th0 * k / 14, h, 0.03) for k in range(14, -1, -1)]
        out.append((lamina(pts, (0, -1 if v == 0 else 1, 0), 0.0, DARK, DARK, False), None, 30.0))
    return out


def p_motor_expuesto():
    th0, h0, h1 = math.radians(52), 1.7, 6.1
    radial_g = lambda c: Vector((c.x, 0, c.z))
    hueco = orientar(rejilla(12, 8, lambda u, v: gondola_pt(-th0 + 2 * th0 * u, h0 + (h1 - h0) * v, 0.025), lambda u, v: BLACK if 0.15 < u < 0.85 and 0.1 < v < 0.9 else DARK), radial_g)
    out = [(hueco, None, 50.0)]
    for th, col in ((-0.5, ORANGE), (0.0, ORANGE), (0.5, ORANGE)):
        pts = [gondola_pt(th, h, 0.17 + 0.08 * math.sin(h * 2.3 + th * 3)) for h in (1.9, 2.8, 3.8, 4.8, 5.9)]
        out.append(cable(pts, 0.13, col, 8))
    for th, col in ((-0.75, RED), (0.75, YELLOW), (0.25, BLUE)):
        pts = [gondola_pt(th + 0.15 * math.sin(h * 3.1), h, 0.12 + 0.12 * abs(math.sin(h * 1.7))) for h in (2.0, 2.9, 3.7, 4.6, 5.5)]
        out.append(cable(pts, 0.05, col))
    p = gondola_pt(0.0, 3.9, 0.35)
    out.append((caja(p.x, p.y, p.z, 1.0, 1.5, 0.4, 0.06), DARK, 40.0))
    p = gondola_pt(0.0, 3.9, 0.6)
    out.append((cylinder(0.28, 0.25, Matrix.Translation(p), 10), BLACK, 40.0))
    return out


def casco_pt(s, y, off):
    r = R0 + off
    th = math.pi / 2 + s / r
    return Vector((r * math.cos(th), y, ZC0 + r * math.sin(th)))


N_HUECO = 24


def hueco_param(k, f, extra=0.0):
    phi = 2 * math.pi * k / N_HUECO
    m = min(k % N_HUECO, (N_HUECO // 2 - k) % N_HUECO)
    rk = 1.0 + alterno(m, 0.16, JAG_T) + extra
    return f * rk * 5.2 * math.cos(phi), FILA_TECHO + f * rk * 2.1 * math.sin(phi)


def disco_hueco(off, col, hacia_fuera):
    bm = bmesh.new()
    cl = bm.faces.layers.int.new("c")
    centro = bm.verts.new(casco_pt(0.0, FILA_TECHO, off))
    anillos = []
    for f in (0.34, 0.67, 1.0):
        anillos.append([bm.verts.new(casco_pt(*hueco_param(k, f), off)) for k in range(N_HUECO)])
    for k in range(N_HUECO):
        k2 = (k + 1) % N_HUECO
        bm.faces.new((centro, anillos[0][k], anillos[0][k2]))[cl] = col
        for a, b in ((0, 1), (1, 2)):
            bm.faces.new((anillos[a][k], anillos[b][k], anillos[b][k2], anillos[a][k2]))[cl] = col
    signo = 1 if hacia_fuera else -1
    return orientar(bm, lambda c: radial(c) * signo)


def p_techo_roto():
    out = [(disco_hueco(0.06, BLACK, True), None, 80.0)]
    for k in range(0, N_HUECO, 2):
        sa, ya = hueco_param(k, 1.0)
        sb, yb = hueco_param(k + 1, 1.0)
        a = casco_pt(sa, ya, 0.06)
        b = casco_pt(sb, yb, 0.06)
        s, y = (sa + sb) / 2, (ya + yb) / 2
        punta = casco_pt(s * 1.15, FILA_TECHO + (y - FILA_TECHO) * 1.3, 0.75 + 0.25 * (k % 4 == 0))
        out.append((lamina([a, b, punta], radial((a + b) * 0.5), 0.05, CREAM, DARK, True), None, 60.0))
    for sx in (-1, 1):
        pts = [casco_pt(sx * 1.8, FILA_TECHO - 2.6, 0.08), casco_pt(sx * 1.8, FILA_TECHO - 1.4, 0.2), casco_pt(sx * 1.9, FILA_TECHO - 0.9, 0.9), casco_pt(sx * 2.0, FILA_TECHO - 0.8, 1.5)]
        out.append(cable(pts, 0.11, DARK, 6))
    return out


def p_borde_techo():
    out = []
    z0 = 10.0
    for ye, d in ((FILA_TECHO - 2.25, 1), (FILA_TECHO + 2.25, -1)):
        xs = [-6.5 + 13.0 * i / 12 for i in range(13)]
        arriba = [Vector((x, ye, z0 + 0.12)) for x in xs]
        abajo = [Vector((x, ye + d * (0.2 + 0.35 * JAG_T[i]), z0 - 0.15 - 0.6 * JAG_T[i + 6] * (i % 2 + 0.4))) for i, x in enumerate(xs)]
        for i in range(12):
            quad = [arriba[i], arriba[i + 1], abajo[i + 1], abajo[i]]
            out.append((lamina(quad, (0, d, 0.3), 0.04, WHITE, WHITE, False), None, 60.0))
        for sx in (-1, 1):
            pts = [(sx * 4.0, ye, 6.6), (sx * 4.0, ye, 10.0)] + [(sx * (4.0 + 2.7 * t), ye, 10.0 - 0.4 * (i % 2)) for i, t in enumerate((0.33, 0.66, 1.0))] + [(sx * 6.7, ye, 6.6)]
            pts = [Vector(p) + Vector((0, d * 0.02, 0)) for p in pts]
            out.append((lamina(pts, (0, d, 0), 0.04, CREAM, CREAM, False), None, 60.0))
    for x, col, largo in ((-2.2, RED, 1.6), (0.6, YELLOW, 2.1), (3.1, BLUE, 1.3)):
        ye = FILA_TECHO - 2.15 if x < 0 else FILA_TECHO + 2.15
        pts = [Vector((x, ye, z0 + 0.1)), Vector((x + 0.2, ye + 0.2, z0 - largo * 0.4)), Vector((x - 0.1, ye + 0.3, z0 - largo * 0.8)), Vector((x + 0.25, ye + 0.15, z0 - largo))]
        out.append(cable(pts, 0.05, col))
    return out


def p_tapa_techo():
    out = []
    ext = disco_hueco(0.0, CREAM, True)
    inn = disco_hueco(-0.14, DARK, False)
    out += [(ext, None, 80.0), (inn, None, 80.0)]
    borde = [casco_pt(*hueco_param(k, 1.0), 0.0) for k in range(N_HUECO)]
    borde_i = [casco_pt(*hueco_param(k, 1.0), -0.14) for k in range(N_HUECO)]
    out.append((banda(borde, borde_i, DARK, DARK, 0.0), None, 40.0))
    for y in (FILA_TECHO - 1.0, FILA_TECHO + 1.0):
        pts = [casco_pt(s, y, -0.3) for s in (-4.2, -2.1, 0.0, 2.1, 4.2)]
        out.append((tube(pts, lambda u: 0.14, k=4, steps=2, cap_rings=1), DARK, 30.0))
    out.append((caja(0, FILA_TECHO, 10.05, 8.2, 3.4, 0.3, 0.05), WHITE, 40.0))
    for sx in (-1, 1):
        for y in (FILA_TECHO - 1.0, FILA_TECHO + 1.0):
            top = casco_pt(sx * 2.6, y, -0.3)
            out.append((caja(top.x, y, (10.2 + top.z) / 2, 0.18, 0.18, top.z - 10.2), DARK, 30.0))
    out.append((caja(0, FILA_TECHO, 9.82, 1.0, 1.0, 0.12), YELLOW, 40.0))
    return out


def p_pollo():
    S = 1.6
    out = []
    out.append((ellipsoid((0.36, 1.05, 0.38), Matrix.Translation((0, 0.3, 0))), YELLOW, 50.0))
    out.append((tube([Vector((0, -0.6, 0.12)), Vector((0, -1.2, 0.35)), Vector((0, -1.75, 0.45))], lambda u: 0.13 - 0.05 * u, k=8, steps=3, cap_rings=1), YELLOW, 50.0))
    out.append((ellipsoid((0.18, 0.24, 0.2), Matrix.Translation((0, -1.95, 0.5)), 12, 8), YELLOW, 50.0))
    out.append((cylinder(0.09, 0.32, Matrix.Translation((0, -2.3, 0.46)) @ Matrix.Rotation(math.radians(90), 4, "X"), 8, r2=0.0), ORANGE, 40.0))
    for y, z, r in ((-2.05, 0.72, 0.07), (-1.94, 0.76, 0.08), (-1.83, 0.71, 0.06)):
        out.append((ellipsoid((0.045, r, r), Matrix.Translation((0, y, z)), 8, 6), RED, 50.0))
    out.append((ellipsoid((0.045, 0.06, 0.1), Matrix.Translation((0, -2.18, 0.3)), 8, 6), RED, 50.0))
    for sx in (-1, 1):
        out.append((ellipsoid((0.04, 0.04, 0.04), Matrix.Translation((sx * 0.12, -2.09, 0.58)), 6, 4), BLACK, 60.0))
        out.append((ellipsoid((0.08, 0.4, 0.2), Matrix.Translation((sx * 0.37, 0.2, 0.05)) @ Matrix.Rotation(math.radians(sx * 12), 4, "Y"), 10, 6), YELLOW, 50.0))
        pierna = [Vector((sx * 0.15, 0.6, -0.25)), Vector((sx * 0.2, 1.0, -0.75)), Vector((sx * 0.24, 1.25, -1.1))]
        out.append((tube(pierna, lambda u: 0.05, k=6, steps=3, cap_rings=1), ORANGE, 50.0))
        out.append((ellipsoid((0.13, 0.19, 0.04), Matrix.Translation((sx * 0.25, 1.4, -1.14)), 8, 4), ORANGE, 50.0))
    out.append((cylinder(0.2, 0.4, Matrix.Translation((0, 1.4, 0.2)) @ Matrix.Rotation(math.radians(-70), 4, "X"), 8, r2=0.02), YELLOW, 40.0))
    escala = Matrix.Diagonal((S, S, S, 1.0))
    for bm, _, _ in out:
        bmesh.ops.transform(bm, matrix=escala, verts=bm.verts)
    return out


TURISTA = dict(P["PASSENGERS"])["PasajeroTurista"]


def p_asiento_saludo():
    prims = P["passenger"](TURISTA)
    prims = [p for i, p in enumerate(prims) if i not in (1, 2, 3, 6, 7, 8)]
    prims += P["seat"](0.0)
    prims.append((caja(0, -0.62, 0.42, 1.95, 0.16, 0.2, 0.04), DARK, 40.0))
    prims.append((caja(0, -0.72, 0.42, 0.42, 0.06, 0.26, 0.03), YELLOW, 40.0))
    return prims


def hombro():
    s = TURISTA["scale"]
    return s * (3.0 - P["BOTTOM"])


def p_brazos_saludo():
    s = TURISTA["scale"]
    T = Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation((0, 0, -P["BOTTOM"]))
    skin, manga = TURISTA["skin"], TURISTA.get("arm_color", TURISTA["top"])
    out = []
    for sx in (-1, 1):
        ctrl = [Vector((sx * x, y, z)) for x, y, z in ((0.70, 0.02, 3.0), (0.95, 0.0, 3.25), (1.12, -0.05, 3.75), (1.22, -0.08, 4.3), (1.28, -0.08, 4.75))]
        out.append((tube(ctrl, lambda u: 0.13 - 0.025 * u, k=6, steps=2, cap_rings=1, color_fn=lambda u: manga if u < 0.3 else skin), None, 50.0))
        mano = Matrix.Translation((sx * 1.3, -0.1, 5.0)) @ Matrix.Rotation(math.radians(sx * -15), 4, "Y")
        out.append((ellipsoid((0.17, 0.07, 0.21), mano, 8, 5), skin, 60.0))
        out.append((ellipsoid((0.05, 0.05, 0.09), mano @ Matrix.Translation((-sx * 0.17, -0.02, -0.04)) @ Matrix.Rotation(math.radians(sx * 40), 4, "Y"), 5, 3), skin, 60.0))
    for bm, _, _ in out:
        bmesh.ops.transform(bm, matrix=T, verts=bm.verts)
    return out


PIEZAS = [
    ("RotBase", lambda: despiece()["RotBase"], "avion"),
    ("RotPuntaIzq", lambda: despiece()["RotPuntaIzq"], "avion"),
    ("RotPuntaDer", lambda: despiece()["RotPuntaDer"], "avion"),
    ("RotCola", lambda: despiece()["RotCola"], "avion"),
    ("RotDeriva", lambda: despiece()["RotDeriva"], "avion"),
    ("RotBordeAlaIzq", lambda: p_borde_ala(1), "avion"),
    ("RotBordeAlaDer", lambda: p_borde_ala(-1), "avion"),
    ("RotBordeDeriva", p_borde_deriva, "avion"),
    ("RotBordeCola", p_borde_cola, "avion"),
    ("RotTechoRoto", p_techo_roto, "avion"),
    ("RotBordeTecho", p_borde_techo, "avion"),
    ("RotTapaTecho", p_tapa_techo, "avion"),
    ("RotCapo", p_capo, "local"),
    ("RotMotorExpuesto", p_motor_expuesto, "local"),
    ("RotPolloGoma", p_pollo, "local"),
    ("RotAsientoSaludo", p_asiento_saludo, "local"),
    ("RotBrazosSaludo", p_brazos_saludo, "local"),
]


def caja_roblox(mn, mx, espacio):
    dy = 100.0 if espacio == "avion" else 0.0
    return [round(-mx[0], 3), round(mn[2] + dy, 3), round(mn[1], 3)], [round(-mn[0], 3), round(mx[2] + dy, 3), round(mx[1], 3)]


def v3(v):
    return "Vector3.new(%s, %s, %s)" % tuple(("%.3f" % x).rstrip("0").rstrip(".") for x in v)


def escribir_luau():
    with open(os.path.join(OUT, "manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    ruta_ids = os.path.join(OUT, "ids_subida.json")
    ids = json.load(open(ruta_ids, encoding="utf-8")) if os.path.exists(ruta_ids) else {}
    lineas = ["--!strict", "local PiezasRoturas = {}", "", f"PiezasRoturas.CORTE = {CORTE_Y}", f"PiezasRoturas.CORTE_ALA = {CORTE_X}", f"PiezasRoturas.CORTE_DERIVA = {CORTE_Z + 100}", f"PiezasRoturas.FILA_TECHO = {FILA_TECHO}",
              f"PiezasRoturas.HOMBRO = {round(hombro(), 3)}", "", "PiezasRoturas.IDS = {"]
    for e in man:
        if e["nombre"] in ids:
            lineas.append(f"\t{e['nombre']} = {ids[e['nombre']]},")
    lineas += ["} :: { [string]: number }", "", "PiezasRoturas.CAJAS = {"]
    for e in man:
        lineas.append(f"\t{e['nombre']} = {{ minimo = {v3(e['bbox_min'])}, maximo = {v3(e['bbox_max'])} }},")
    lineas += ["} :: { [string]: { minimo: Vector3, maximo: Vector3 } }", "", "return PiezasRoturas", ""]
    with open(os.path.join(RAIZ, "src", "shared", "PiezasRoturas.luau"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lineas))
    print("LUAU", len(ids), "ids")


def colocar_vista(objs):
    desp = {
        "RotPuntaIzq": (Matrix.Translation((7.0, 6.0, -5.0)), (CORTE_X, -24.0, -1.0), (0.4, 0.3, 0.6)),
        "RotDeriva": (Matrix.Translation((-2.0, 12.0, 7.0)), (0.0, 22.0, CORTE_Z), (0.0, 0.5, 0.35)),
        "RotCola": (Matrix.Translation((0.0, 9.0, -4.0)), (0.0, CORTE_Y, -3.75), (0.18, 0.0, 0.0)),
        "RotTapaTecho": (Matrix.Translation((-1.0, 3.0, 7.0)), (0.0, FILA_TECHO, 13.75), (0.6, 0.2, 0.3)),
    }
    for nombre, (tr, piv, rot) in desp.items():
        ob = objs[nombre]
        pv = Vector(piv)
        R = Matrix.Rotation(rot[0], 4, "X") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[2], 4, "Z")
        ob.matrix_world = tr @ Matrix.Translation(pv) @ R @ Matrix.Translation(-pv) @ ob.matrix_world
    objs["RotDeriva"].matrix_world = objs["RotCola"].matrix_world @ objs["RotDeriva"].matrix_world
    objs["RotBordeDeriva"].matrix_world = objs["RotCola"].matrix_world.copy()
    cola_borde = objs["RotBordeCola"].copy()
    cola_borde.data = objs["RotBordeCola"].data
    bpy.context.scene.collection.objects.link(cola_borde)
    cola_borde.matrix_world = objs["RotCola"].matrix_world.copy()
    for n in ("RotBordeAlaIzq", "RotBordeDeriva", "RotBordeCola", "RotTapaTecho", "RotTechoRoto"):
        objs[n].hide_render = False


def main():
    if "--solo-luau" in ARGS:
        escribir_luau()
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    img = A["make_palette_image"]()
    mat = A["palette_material"](img)
    objs = {}
    manifest = []
    for nombre, fn, espacio in PIEZAS:
        prims = [(A["fix_closed"](bm), col, ang) for bm, col, ang in fn()]
        ob = A["build_object"](nombre, prims, mat)
        tris = A["tri_count"](ob)
        mn, mx = A["bbox"](ob)
        A["export_fbx"](ob, os.path.join(OUT, nombre + ".fbx"))
        bmin, bmax = caja_roblox(mn, mx, espacio)
        manifest.append({"nombre": nombre, "archivo": nombre + ".fbx", "espacio": espacio, "bbox_min": bmin, "bbox_max": bmax, "triangulos": tris})
        print("PIEZA %-18s tris %5d  min %s  max %s" % (nombre, tris, bmin, bmax))
        objs[nombre] = ob
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    escribir_luau()
    if "--norender" in ARGS:
        return
    A["PREVIEW"] = "--preview" in ARGS
    A["render_setup"](scene, ground_z=-10.0, ground_size=5000, ground_hex="D9D4C7", sun_rot=(50, 10, -40))
    intactas = ("RotBase", "RotPuntaIzq", "RotPuntaDer", "RotCola", "RotDeriva")
    for n, ob in objs.items():
        ob.hide_render = n not in intactas
    A["shoot"](scene, "roturas_intacto", dict(loc=(-78.0, -112.0, 42.0), target=(0.0, -16.0, 1.0), lens=40))
    colocar_vista(objs)
    A["shoot"](scene, "roturas_partido", dict(loc=(-80.0, -95.0, 38.0), target=(0.0, -8.0, 3.0), lens=38))
    A["shoot"](scene, "roturas_partido_detras", dict(loc=(45.0, 70.0, 30.0), target=(0.0, -5.0, 3.0), lens=40))
    A["shoot"](scene, "roturas_techo", dict(loc=(-24.0, -38.0, 28.0), target=(0.0, FILA_TECHO, 12.0), lens=45))
    for ob in list(scene.objects):
        if ob.type == "MESH" and ob.name != "Ground":
            ob.hide_render = True
    objs["RotBordeTecho"].hide_render = False
    A["shoot"](scene, "roturas_techo_dentro", dict(loc=(0.0, -24.0, 4.0), target=(0.0, FILA_TECHO, 9.5), lens=28))
    objs["RotBordeTecho"].hide_render = True
    fila =[("RotCapo", (-9, 0, 0)), ("RotMotorExpuesto", (-4, 0, 0)), ("RotPolloGoma", (1, 0, 0)), ("RotAsientoSaludo", (6, 0, 1.6)), ("RotBrazosSaludo", (6, 0, 1.6))]
    for n, loc in fila:
        objs[n].hide_render = False
        objs[n].matrix_world = Matrix.Translation(loc) @ objs[n].matrix_world
    A["shoot"](scene, "roturas_piezas", dict(loc=(-2.0, -16.0, 6.0), target=(0.0, 0.0, 1.0), lens=35))


main()
