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


K = cargar(os.path.join("kit_aeropuerto", "kit_aeropuerto_gen.py"))

PAL = [
    ("cream", "F3E6CC"), ("orange", "F27B2B"), ("teal", "1FA6A0"), ("dark", "34383F"),
    ("black", "1B1B21"), ("white", "F2EFE6"), ("red", "D9443A"), ("yellow", "F6C445"),
    ("metal", "A9B0B8"), ("glass", "8FD3F4"), ("leaf", "6DBE45"), ("dleaf", "3D9447"),
    ("trunk", "8A5A33"), ("dteal", "157F7B"), ("concrete", "B9B4AA"), ("pink", "F29BB2"),
    ("tileA", "D6B088"), ("tileB", "C29469"), ("wall", "E0C9A6"), ("wainscot", "A86F45"),
    ("wood", "C08A57"), ("woodb", "9A6B40"), ("beam", "2E5E63"), ("carpet", "2F8F8A"),
    ("dcarpet", "1F6E6A"), ("rubber", "2A2C31"), ("steel", "7C858F"), ("lblue", "BFE3F2"),
    ("navy", "1E2A3A"), ("coffee", "6F4024"), ("cake", "F5D7A1"), ("mint", "9ED9C4"),
    ("purple", "9B6BD6"), ("hpink", "E8457A"), ("lime", "B8D94A"), ("sky", "6FB7E0"),
    ("plum", "6B3F7A"), ("peach", "F4B183"), ("brick", "B5523B"), ("olive", "7F8C3A"),
    ("pot", "C9693E"), ("soil", "4A3426"), ("lamp", "FFE2A8"), ("shade", "E8A54B"),
    ("gold", "D9A93A"), ("chrome", "D0D5DA"), ("mustard", "D9A23A"), ("wine", "8E2F3A"),
    ("roof", "BDB3A3"), ("sand", "E8CFA0"), ("green", "3FA34D"), ("blue", "3D7DD8"),
    ("grey", "8C8C8C"), ("dgrey", "55595F"), ("lgrey", "D4D1CB"), ("skin", "F2C29B"),
]
IDX = {n: i for i, (n, _) in enumerate(PAL)}


def suv(n):
    i = IDX[n]
    return ((i % 8 + 0.5) / 8.0, (i // 8 + 0.5) / 8.0)


K["PAL"], K["IDX"], K["suv"] = PAL, IDX, suv
for _n in ("bb", "rbox", "cyl", "lathe", "prism", "decal", "rect", "circ", "rrect", "pill", "arc_strip", "rr_loft", "bar",
           "tube", "ellipsoid", "blob", "gridplane", "wheel", "ring", "logo", "fr", "frame", "M", "yzx", "bevel_sharp", "Prop",
           "seg7", "hex_rgb", "lin"):
    globals()[_n] = K[_n]

XO, XE, ZN, ZS = -32.0, 32.0, -48.0, 48.0
FL = 0.5
HW, HE = 22.0, 15.0
PUERTAS = ((20.0, "orange"), (-4.0, "teal"), (-28.0, "yellow"))
SALA_X = -20.0
SALIDA = (35.0, 41.0)
MONTANTES = [-43.0 + 6.0 * k for k in range(16)]
TRAGALUCES = [(-30.0, -24.0), (-6.0, 0.0), (18.0, 24.0)]
TRAGALUZ_X = (-18.0, 14.0)
LAMPARAS = [(x, z) for x in (-22.0, -6.0, 10.0, 24.0) for z in (-38.0, -14.0, 4.0, 30.0)]
FACTURACION = (18.0, 8.0, -2.0)
TETA = math.atan((HW - HE) / (XE - XO))
G = 0.06
SL = 0.08
D = 0.05


def techo_y(x):
    return HW + (HE - HW) * (x - XO) / (XE - XO)


def bl(x0, x1, z0, z1, y0, y1, bev=0.0, seg=1):
    return bb(x0, x1, -z1, -z0, y0, y1, bev, seg)


def girar(pts, a):
    c, s = math.cos(a), math.sin(a)
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


def poner(p, polys, m, cx, cy, s, rol, w, a=0.0):
    for poly in polys:
        p.add(decal([(cx + x * s, cy + y * s) for x, y in girar(poly, a)], m, w), rol)


def arco(p, m, cx, cy, r0, r1, a0, a1, rol, w, n=8):
    p.add(arc_strip(cx, cy, r0, r1, a0, a1, n, m, w), rol)


AVION = [K["pill"](0, 0, 1.7, 0.16, 0.0, 3),
         [(0.18, 0.08), (-0.3, 0.95), (-0.55, 0.95), (-0.25, 0.08)], [(0.18, -0.08), (-0.25, -0.08), (-0.55, -0.95), (-0.3, -0.95)],
         [(-0.72, 0.06), (-0.98, 0.42), (-1.1, 0.42), (-0.98, 0.06)], [(-0.72, -0.06), (-0.98, -0.06), (-1.1, -0.42), (-0.98, -0.42)]]
HOMBRE = [K["circ"](0, 0.78, 0.2, 10), K["rrect"](0, 0.15, 0.56, 0.6, 0.12, 2), K["rect"](-0.25, -0.05, -0.65, -0.1),
          K["rect"](0.05, 0.25, -0.65, -0.1), K["rect"](-0.42, -0.32, -0.05, 0.4), K["rect"](0.32, 0.42, -0.05, 0.4)]
MUJER = [K["circ"](0, 0.78, 0.2, 10), [(-0.42, -0.3), (0.42, -0.3), (0.16, 0.48), (-0.16, 0.48)], K["rect"](-0.2, -0.06, -0.65, -0.28),
         K["rect"](0.06, 0.2, -0.65, -0.28), K["rect"](-0.42, -0.02, 0.38, 0.47), K["rect"](0.02, 0.42, 0.38, 0.47)]
TAZA = [[(-0.42, -0.3), (0.3, -0.3), (0.4, 0.3), (-0.52, 0.3)], K["pill"](-0.06, -0.42, 0.9, 0.07, 0.0, 3),
        K["pill"](-0.25, 0.62, 0.3, 0.05, math.pi / 2, 2), K["pill"](0.05, 0.66, 0.36, 0.05, math.pi / 2, 2)]
MALETA = [K["rrect"](0, -0.1, 1.2, 0.85, 0.12, 2), K["rect"](-0.3, -0.22, 0.32, 0.55), K["rect"](0.22, 0.3, 0.32, 0.55),
          K["rect"](-0.3, 0.3, 0.5, 0.58)]
BOLSA = [[(-0.45, -0.5), (0.45, -0.5), (0.38, 0.3), (-0.38, 0.3)], K["rect"](-0.24, -0.17, 0.3, 0.58), K["rect"](0.17, 0.24, 0.3, 0.58),
         K["rect"](-0.24, 0.24, 0.52, 0.6)]
CAMARA = [K["rrect"](0, -0.05, 1.1, 0.72, 0.12, 2), K["rect"](-0.25, 0.1, 0.3, 0.42)]
FLECHA = [[(-0.6, -0.14), (0.1, -0.14), (0.1, -0.38), (0.6, 0.0), (0.1, 0.38), (0.1, 0.14), (-0.6, 0.14)]]
CORRER = [K["circ"](0.28, 0.78, 0.17, 10), K["pill"](0.05, 0.2, 0.5, 0.11, math.radians(70), 2),
          K["pill"](-0.2, -0.38, 0.5, 0.09, math.radians(120), 2), K["pill"](0.25, -0.4, 0.5, 0.09, math.radians(60), 2),
          K["pill"](-0.25, 0.32, 0.38, 0.08, math.radians(-20), 2), K["pill"](0.38, 0.12, 0.38, 0.08, math.radians(-40), 2)]
INFO = [K["circ"](0, 0.42, 0.13, 10), K["rrect"](0, -0.14, 0.2, 0.6, 0.05, 1)]


def flecha(p, m, cx, cy, s, rol, w, grados):
    poner(p, FLECHA, m, cx, cy, s, rol, w, math.radians(grados))


def p_suelo():
    p = Prop("LobbySuelo", None, 7000)

    def zona(c, n):
        x, z = c.x, -c.y
        if x < -14.0 and -46.0 < z < 30.0:
            return "carpet"
        if x > 12.0 and z > 30.0:
            return "wood" if int((x - 12.0) // 2.0) % 2 == 0 else "woodb"
        return "tileA" if (int((x + 32.0) // 4.0) + int((z + 48.0) // 4.0)) % 2 == 0 else "tileB"
    xs = [XO + 2.0 * i for i in range(33)]
    ys = [ZN + 2.0 * i for i in range(49)]
    p.add(gridplane(xs, ys, FL), zona)
    m = M((0, 0, FL))
    for x0, x1, z0, z1 in ((-31.4, -14.0, -46.0, -45.6), (-31.4, -14.0, 29.6, 30.0), (-14.4, -14.0, -46.0, 30.0)):
        p.add(decal(rect(x0, x1, -z1, -z0), m, SL), "dcarpet")
    p.add(decal(rect(12.0, 31.4, -30.3, -30.0), m, SL), "wainscot")
    p.add(decal(rect(11.7, 12.0, -47.4, -30.0), m, SL), "wainscot")
    sx, sz = 2.0, 34.0
    p.add(decal(circ(sx, -sz, 4.4, 32), m, SL), "dteal")
    p.add(decal(circ(sx, -sz, 3.9, 32), m, 2 * SL), "cream")
    for k in range(16):
        a0 = 22.5 * k
        p.add(arc_strip(sx, -sz, 3.95, 4.25, a0, a0 + 11.0, 2, m, 2 * SL), "orange")
    logo(p, M((sx, -sz, FL + 2 * SL)), 2.8, base=False, step=SL)
    rutas = [
        ("yellow", [(-2.3, 32.6), (-6.0, 32.6), (-6.0, -28.0), (-14.3, -28.0)]),
        ("teal", [(-2.3, 34.0), (-8.0, 34.0), (-8.0, -4.0), (-14.3, -4.0)]),
        ("orange", [(-2.3, 35.4), (-10.0, 35.4), (-10.0, 20.0), (-14.3, 20.0)]),
    ]
    for rol, pts in rutas:
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            h = 0.32
            xa, xb = sorted((x0, x1))
            za, zb = sorted((z0, z1))
            p.add(decal(rect(xa - h, xb + h, -zb - h, -za + h), m, 3 * SL), rol)
        (x0, z0), (x1, z1) = pts[-2], pts[-1]
        d = math.atan2(-(z1 - z0), x1 - x0)
        poner(p, [[(0.0, -0.9), (1.0, 0.0), (0.0, 0.9)]], m, x1, -z1, 1.0, rol, 3 * SL, d)
        for k in range(1, 4):
            t = k / 4.0
            ax, az = pts[1][0] + (pts[2][0] - pts[1][0]) * t, pts[1][1] + (pts[2][1] - pts[1][1]) * t
            poner(p, [[(-0.5, -0.55), (0.3, 0.0), (-0.5, 0.55), (-0.25, 0.0)]], m, ax, -az, 1.0, "white", 4 * SL,
                  math.atan2(-(pts[2][1] - pts[1][1]), pts[2][0] - pts[1][0]))
    p.add(decal(rrect(-29.0, -38.0, 3.6, 7.0, 0.4, 2), m, SL), "rubber")
    for k in range(6):
        p.add(decal(rect(-30.4, -27.6, -35.4 - 0.9 * k - 0.2, -35.4 - 0.9 * k), m, 2 * SL), "dgrey")
    p.add(decal(rrect(-6.5, 39.0, 13.0, 9.0, 1.0, 3), m, SL), "plum")
    p.add(decal(rrect(-6.5, 39.0, 11.8, 7.8, 0.8, 3), m, 2 * SL), "peach")
    p.add(decal(rrect(-6.5, 39.0, 9.0, 5.0, 0.6, 3), m, 3 * SL), "mustard")
    p.add(decal(elipse(19.6, 28.0, 12.6, 6.6, 40), m, SL), "dgrey")
    p.add(decal(elipse(19.6, 28.0, 12.0, 6.0, 40), m, 2 * SL), "lgrey")
    for z in (-10.0, -18.0):
        for ax in (2.0, 8.0):
            p.add(decal(rect(ax - 1.5, ax + 1.5, -z - 0.15, -z + 0.15), m, SL), "yellow")
    return p


def elipse(cx, cy, a, b, n):
    return [(cx + a * math.cos(2 * math.pi * k / n), cy + b * math.sin(2 * math.pi * k / n)) for k in range(n)]


def pared_ns(p, zc, signo):
    pts = [(XO, 0.0), (XE, 0.0), (XE, HE), (XO, HW)]
    p.add(prism(pts, 0.6, frame((0, -zc, 0), (1, 0, 0), (0, 0, 1))), lambda c, n: "wall" if n.y * signo < -0.5 else "cream")
    yi = -zc - signo * 0.3
    tramos = ((XO + 0.75, 4.0), (11.6, XE - 0.75)) if signo > 0 else ((XO + 0.75, XE - 0.75),)
    for xa, xb in tramos:
        y0, y1 = sorted((yi + signo * 0.1, yi - signo * 0.08))
        p.add(bb(xa, xb, y0, y1, FL, 3.0), "wainscot")
        y0, y1 = sorted((yi + signo * 0.1, yi - signo * 0.14))
        p.add(bb(xa, xb, y0, y1, 3.0, 3.25, 0.03, 1), "orange")
    yo = -zc + signo * 0.3
    y0, y1 = sorted((yo, yo + signo * 0.08))
    p.add(bb(XO, XE, y0, y1, 0.0, 1.6), "teal")
    p.add(bb(XO, XE, y0, y1, 8.4, 8.9), "orange")


def p_paredes():
    p = Prop("LobbyParedes", None, 12000)
    p.add(bl(31.4, 32.0, ZN, ZS, 0.0, HE), lambda c, n: "wall" if n.x < -0.5 else "cream")
    p.add(bl(31.32, 31.5, ZN + 0.75, ZS - 0.75, FL, 3.0), "wainscot")
    p.add(bl(31.26, 31.5, ZN + 0.75, ZS - 0.75, 3.0, 3.25, 0.03, 1), "orange")
    p.add(bl(32.0, 32.08, ZN, ZS, 0.0, 1.6), "teal")
    p.add(bl(32.0, 32.08, ZN, ZS, 8.4, 8.9), "orange")
    pared_ns(p, ZN + 0.3, 1)
    pared_ns(p, ZS - 0.3, -1)
    for x, z in ((XO, ZN), (XO, ZS), (XE, ZN), (XE, ZS)):
        p.add(bl(x - 0.7, x + 0.7, z - 0.7, z + 0.7, 0.0, techo_y(x) + 0.1), "white")
    me = fr((31.4, 0, 0), "-x")
    p.add(decal(rect(-7.5, 23.5, 3.6, 11.4), me, G), "dteal")
    p.add(decal(rect(-7.1, 23.1, 4.0, 11.0), me, 2 * G), "teal")
    for i, z in enumerate(FACTURACION):
        p.add(decal(circ(z, 9.0, 1.3, 20), me, 3 * G), "cream")
        seg7(p, me, z, 9.0, 1.5, 0.3, i + 1, "dteal", 4 * G)
        poner(p, MALETA, me, z, 6.0, 1.3, "cream", 3 * G)
    p.add(decal(rect(-34.0, -22.0, 5.5, 9.5), me, G), "dteal")
    poner(p, MALETA, me, -30.0, 7.5, 1.8, "cream", 2 * G)
    for k in range(3):
        arco(p, me, -25.4, 7.5, 1.0, 1.35, 30 + 120 * k, 120 + 120 * k, "yellow", 2 * G)
    poner(p, [[(0.0, -0.35), (0.5, 0.0), (0.0, 0.35)]], me, -25.4 + 1.18, 7.5 + 0.2, 1.0, "yellow", 2 * G, math.radians(120))
    mn = fr((0, 47.4, 0), "-y")
    for i, x in enumerate((-12.0, -6.0, 0.0)):
        p.add(decal(rect(x - 2.4, x + 2.4, 4.6, 11.0), mn, G), "wainscot")
        p.add(decal(rect(x - 2.1, x + 2.1, 4.9, 10.7), mn, 2 * G), ("sky", "lblue", "peach")[i])
        if i == 0:
            p.add(decal(rect(x - 2.1, x + 2.1, 4.9, 6.6), mn, 3 * G), "teal")
            p.add(decal(rect(x - 2.1, x + 2.1, 4.9, 5.6), mn, 4 * G), "sand")
            p.add(decal(circ(x + 1.0, 9.3, 0.7, 14), mn, 3 * G), "yellow")
            p.add(decal([(x - 1.0, 5.3), (x - 0.7, 5.3), (x - 0.5, 8.4), (x - 0.75, 8.4)], mn, 5 * G), "trunk")
            for a in (20, 70, 120, 160, 200):
                poner(p, [K["pill"](0.55, 0, 1.1, 0.16, 0.0, 2)], mn, x - 0.62, 8.5, 1.0, "leaf", 6 * G, math.radians(a))
        elif i == 1:
            p.add(decal([(x - 2.1, 4.9), (x + 2.1, 4.9), (x + 2.1, 6.0), (x + 0.6, 8.6), (x - 0.4, 6.8), (x - 1.2, 8.0), (x - 2.1, 6.4)], mn, 3 * G), "dgrey")
            p.add(decal([(x + 0.25, 7.9), (x + 0.6, 8.6), (x + 0.95, 7.9)], mn, 4 * G), "white")
            p.add(decal([(x - 1.5, 7.3), (x - 1.2, 8.0), (x - 0.9, 7.3)], mn, 4 * G), "white")
            poner(p, AVION, mn, x - 0.6, 9.8, 0.55, "orange", 3 * G, math.radians(15))
        else:
            for k, (w, h) in enumerate(((0.8, 2.6), (0.9, 3.8), (0.7, 2.0), (1.0, 3.1))):
                bx = x - 2.0 + 1.0 * k
                p.add(decal(rect(bx, bx + w, 4.9, 4.9 + h), mn, 3 * G), "plum")
                for j in range(int(h / 0.7)):
                    p.add(decal(rect(bx + 0.2, bx + 0.4, 5.3 + 0.7 * j, 5.6 + 0.7 * j), mn, 4 * G), "lamp")
            p.add(decal(circ(x + 1.3, 9.6, 0.5, 14), mn, 3 * G), "cream")
            p.add(decal(circ(x + 1.5, 9.75, 0.42, 14), mn, 4 * G), "peach")
    for i, (x0, x1) in enumerate(((4.6, 7.0), (8.6, 11.0))):
        p.add(bb(x0 - 0.25, x1 + 0.25, 47.26, 47.55, FL, 7.8, 0.04, 1), "dteal")
        p.add(bb(x0, x1, 47.2, 47.48, FL + 0.08, 7.5, 0.03, 1), "mint")
        p.add(bb(x1 - 0.5, x1 - 0.3, 47.12, 47.2, 3.4, 3.6), "chrome")
        poner(p, (HOMBRE, MUJER)[i], fr((0, 47.2, 0), "-y"), (x0 + x1) / 2, 5.4, 1.0, "white", G)
        p.add(decal(circ(x0 + 0.5, 6.9, 0.14, 8), fr((0, 47.2, 0), "-y"), G), "green")
    p.add(bb(4.0, 11.6, 47.0, 47.5, 8.3, 10.3, 0.1, 2), "navy")
    mw = fr((0, 47.0, 0), "-y")
    poner(p, HOMBRE, mw, 6.4, 9.3, 0.95, "white", G)
    poner(p, MUJER, mw, 9.2, 9.3, 0.95, "white", G)
    p.add(decal(rect(7.75, 7.85, 8.6, 10.0), mw, G), "white")
    ms = fr((0, -47.4, 0), "+y")
    p.add(decal(rect(-6.0, 14.0, 7.0, 11.5), ms, G), "plum")
    p.add(decal(rect(-5.6, 13.6, 7.4, 11.1), ms, 2 * G), "purple")
    poner(p, BOLSA, ms, 4.0, 9.25, 1.6, "white", 3 * G)
    for k, (x, y) in enumerate(((-3.0, 9.8), (0.5, 8.3), (8.0, 10.1), (11.5, 8.6))):
        estrella = [(x + (0.55 if j % 2 == 0 else 0.2) * math.cos(math.pi / 2 + j * math.pi / 4), y + (0.55 if j % 2 == 0 else 0.2) * math.sin(math.pi / 2 + j * math.pi / 4)) for j in range(8)]
        p.add(decal(estrella, ms, 3 * G), ("yellow", "pink", "lamp", "yellow")[k])
    mo = fr((-31.75, 0, 0), "+x")
    for z in MONTANTES:
        if any(zg - 3.0 < z < zg + 3.0 for zg, _ in PUERTAS) or SALIDA[0] < z < SALIDA[1]:
            continue
        p.add(bl(-32.25, -31.75, z - 0.2, z + 0.2, 0.0, techo_y(XO)), "dteal")
    for y0, y1 in ((0.0, FL + 0.1), (9.3, 9.7), (16.0, 16.3)):
        p.add(bl(-32.3, -31.7, ZN + 0.7, ZS - 0.7, y0, y1), "dteal")
    for zg, col in PUERTAS:
        p.add(bl(-32.4, -31.5, zg - 3.0, zg - 2.6, 0.0, 9.3), "dteal")
        p.add(bl(-32.4, -31.5, zg + 2.6, zg + 3.0, 0.0, 9.3), "dteal")
        for s in (-1, 1):
            z0, z1 = sorted((zg, zg + s * 2.6))
            p.add(bl(-32.15, -31.85, z0 + 0.03, z1 - 0.03, FL, 9.0, 0.04, 1), "cream")
            mp = fr((-31.85, 0, 0), "+x")
            p.add(decal(circ(-(zg + s * 1.3), 6.2, 0.62, 16), mp, G), "dteal")
            p.add(decal(circ(-(zg + s * 1.3), 6.2, 0.5, 16), mp, 2 * G), "glass")
            p.add(bl(-31.85, -31.6, zg + s * 0.35 - 0.06, zg + s * 0.35 + 0.06, 3.0, 4.6), "chrome")
            u0, u1 = sorted((-(zg + s * 2.5), -(zg + s * 0.1)))
            p.add(decal(rect(u0, u1, 1.4, 1.65), mp, G), col)
        p.add(bl(-32.4, -31.4, zg - 2.4, zg + 2.4, 9.8, 13.6, 0.12, 2), "navy")
        mq = fr((-31.4, 0, 0), "+x")
        p.add(decal(rrect(-zg, 11.7, 4.4, 3.4, 0.3, 2), mq, G), col)
        p.add(decal(rrect(-zg, 11.7, 4.0, 3.0, 0.25, 2), mq, 2 * G), "navy")
        seg7(p, mq, -zg - 0.85, 11.7, 2.2, 0.42, PUERTAS.index((zg, col)) + 1, col, 3 * G)
        poner(p, AVION, mq, -zg + 0.95, 11.7, 0.62, "white", 3 * G, math.radians(35))
    z0, z1 = SALIDA
    p.add(bl(-32.45, -31.5, z0 - 0.4, z0, 0.0, 9.3), "dteal")
    p.add(bl(-32.45, -31.5, z1, z1 + 0.4, 0.0, 9.3), "dteal")
    for zz0, zz1 in ((z0 - 2.4, z0 - 0.1), (z1 + 0.1, z1 + 2.4)):
        p.add(bl(-31.6, -31.4, zz0, zz1, FL, 9.0, 0.04, 1), "dteal")
        for xg, lado in ((-31.4, "+x"), (-31.6, "-x")):
            mg = fr((xg, 0, 0), lado)
            u0, u1 = sorted((-(zz0 + 0.25), -(zz1 - 0.25)) if lado == "+x" else ((zz0 + 0.25), (zz1 - 0.25)))
            p.add(decal(rect(u0, u1, FL + 0.25, 8.75), mg, G), "glass")
    p.add(bl(-31.6, -31.2, z0 + 1.0, z1 - 1.0, 9.8, 11.6, 0.12, 2), "green")
    mx = fr((-31.2, 0, 0), "+x")
    poner(p, CORRER, mx, -(z0 + z1) / 2 - 1.3, 10.7, 1.2, "white", G)
    flecha(p, mx, -(z0 + z1) / 2 + 1.4, 10.7, 1.6, "white", G, 0)
    p.add(bl(-36.5, -32.3, z0 - 1.0, z1 + 1.0, 9.6, 10.2, 0.1, 2), lambda c, n: "orange" if n.z > 0.5 else "cream")
    for zz in (z0 - 0.8, z1 + 0.8):
        p.add(bar((-36.0, -zz, 9.7), (-32.3, -zz, 13.5), 0.12, 0.12, caps=False), "dark")
    p.add(cyl(4.2, 0.21, (31.95, 0, 8.0), (0, 90, 0), seg=28), "cream")
    logo(p, fr((32.16, 0, 8.0), "+x"), 4.2, base=False, step=G)
    p.add(cyl(3.0, 0.21, (10.0, 47.95, 6.5), (-90, 0, 0), seg=24), "cream")
    logo(p, fr((10.0, 48.16, 6.5), "+y"), 3.0, base=False, step=G)
    p.add(cyl(3.0, 0.21, (10.0, -47.95, 6.5), (90, 0, 0), seg=24), "cream")
    logo(p, fr((10.0, -48.16, 6.5), "-y"), 3.0, base=False, step=G)
    return p


def p_techo():
    p = Prop("LobbyTecho", None, 14000)
    c = math.cos(TETA)
    R = M((0, 0, techo_y(0.0)), (0, math.degrees(TETA), 0))
    xa, xb = -36.0 / c, 33.0 / c
    hx0, hx1 = TRAGALUZ_X[0] / c, TRAGALUZ_X[1] / c
    bandas = sorted((-z1, -z0) for z0, z1 in TRAGALUCES)

    def rol(cc, n):
        if n.z > 0.5:
            return "roof"
        if n.z < -0.5:
            return "wood"
        return "orange"
    cortes = [-49.5]
    for y0, y1 in bandas:
        cortes += [y0, y1]
    cortes.append(49.5)
    for i in range(0, len(cortes), 2):
        p.add(bb(xa, xb, cortes[i], cortes[i + 1], 0.0, 1.2, m=R), rol)
    for y0, y1 in bandas:
        p.add(bb(xa, hx0, y0, y1, 0.0, 1.2, m=R), rol)
        p.add(bb(hx1, xb, y0, y1, 0.0, 1.2, m=R), rol)
        p.add(bb(hx0 - 0.3, hx1 + 0.3, y0 - 0.3, y0, 1.2, 1.6, m=R), "beam")
        p.add(bb(hx0 - 0.3, hx1 + 0.3, y1, y1 + 0.3, 1.2, 1.6, m=R), "beam")
        p.add(bb(hx0 - 0.3, hx0, y0, y1, 1.2, 1.6, m=R), "beam")
        p.add(bb(hx1, hx1 + 0.3, y0, y1, 1.2, 1.6, m=R), "beam")
        for k in range(1, 8):
            x = hx0 + (hx1 - hx0) * k / 8
            p.add(bb(x - 0.1, x + 0.1, y0, y1, 1.3, 1.5, m=R), "beam")
    for y in range(-47, 48, 2):
        p.add(bb(-31.9 / c, 31.3 / c, y - 0.15, y + 0.15, -0.35, 0.0, m=R), "woodb")
    for y in (-36.0, -12.0, 12.0, 36.0):
        p.add(bb(-31.9 / c, 31.3 / c, y - 0.3, y + 0.3, -1.3, -0.35, m=R), "beam")
    for x, y in ((14.0, -40.0), (20.0, -40.0), (14.0, 40.0)):
        mm = R @ M((x / c, y, 1.2))
        p.add(bb(-2.0, 2.0, -1.4, 1.4, 0.0, 1.6, 0.1, 1, m=mm), "lgrey")
        p.add(cyl(0.9, 0.15, (0, 0, 1.6), seg=12, m=mm), "dgrey")
        for a in (0, 60, 120):
            p.add(rbox((1.6, 0.18, 0.06), (0, 0, 1.78), rot=(0, 0, a), m=mm), "metal")
    logo(p, R @ M((-6.0 / c, -9.0, 1.2)), 7.0, step=G)
    for x, z in LAMPARAS:
        y = techo_y(x) - 0.35
        p.add(cyl(0.05, 3.7, (x, -z, y - 3.7), seg=5, cap0=False, cap1=False), "dark")
        p.add(cyl(0.25, 0.2, (x, -z, y - 3.9), seg=8), "dark")
        ml = M((x, -z, 0))
        p.add(lathe([(1.15, y - 4.9), (1.15, y - 4.1), (0.6, y - 3.85), (0.25, y - 3.8)], 14, ml, cap0=False, cap1=False), "shade")
        p.add(lathe([(1.08, y - 4.9), (1.08, y - 4.15), (0.55, y - 3.92), (0.2, y - 3.88)], 14, ml, cap0=False, cap1=False),
              "lamp")
        p.add(cyl(1.0, 0.04, (x, -z, y - 4.75), seg=14, cap0=False), "lamp")
    for i, (zg, col) in enumerate(PUERTAS):
        x0, y0 = SALA_X, 11.6
        top = techo_y(x0) - 0.35
        for dz in (-1.2, 1.2):
            p.add(cyl(0.05, top - (y0 + 3.0), (x0, -zg + dz, y0 + 3.0), seg=5, cap0=False, cap1=False), "dark")
        p.add(bb(x0 - 1.8, x0 + 1.8, -zg - 1.8, -zg + 1.8, y0, y0 + 3.0, 0.15, 2), "navy")
        for ox, oy, side in ((x0 + 1.8, 0.0, "+x"), (x0 - 1.8, 0.0, "-x"), (0.0, -zg - 1.8, "-y"), (0.0, -zg + 1.8, "+y")):
            mf = fr((ox, oy, 0), side)
            u = {"+x": -zg, "-x": zg, "-y": x0, "+y": -x0}[side]
            p.add(decal(rrect(u, y0 + 1.5, 3.3, 2.7, 0.25, 2), mf, G), col)
            p.add(decal(rrect(u, y0 + 1.5, 3.0, 2.4, 0.2, 2), mf, 2 * G), "navy")
            seg7(p, mf, u - 0.55, y0 + 1.5, 1.7, 0.34, i + 1, col, 3 * G)
            poner(p, AVION, mf, u + 0.75, y0 + 1.5, 0.45, "white", 3 * G, math.radians(35))
    bx, by, bz = 2.0, -22.0, 9.2
    top = techo_y(bx) - 0.35
    for dx in (-2.8, 2.8):
        p.add(cyl(0.05, top - (bz + 3.6), (bx + dx, by, bz + 3.6), seg=5, cap0=False, cap1=False), "dark")
    p.add(bb(bx - 3.6, bx + 3.6, by - 0.15, by + 0.15, bz, bz + 3.6, 0.1, 2), "navy")
    for side, yy in (("-y", by - 0.15), ("+y", by + 0.15)):
        mf = fr((0, yy, 0), side)
        s = 1 if side == "-y" else -1
        filas = [(AVION, "orange", 135 if s > 0 else -45), (MALETA, "teal", 0 if s > 0 else 180), (TAZA, "cream", -45 if s > 0 else 135)]
        for k, (polys, col, ang) in enumerate(filas):
            yrow = bz + 2.95 - 1.15 * k
            ux = s * bx
            poner(p, polys, mf, ux - 1.6, yrow, 0.45, col, G, math.radians(35) if polys is AVION else 0.0)
            flecha(p, mf, ux + 1.4, yrow, 0.9, col, G, ang)
            p.add(decal(rect(ux - 3.3, ux + 3.3, yrow - 0.6, yrow - 0.56), mf, G), "dgrey")
    return p


def p_facturacion():
    p = Prop("Facturacion", None, 2200)
    p.add(bb(-3.5, 0.4, -0.85, 1.0, 0.0, 0.2), "dark")
    p.add(bb(-3.6, 0.5, -0.95, 1.1, 0.2, 2.25, 0.08, 1), lambda c, n: "cream" if n.y < -0.5 else "teal")
    p.add(bb(-3.4, 0.25, -1.0, -0.95, 0.5, 2.0), "teal")
    logo(p, fr((-1.55, -1.0, 1.25), "-y"), 0.5, step=D)
    p.add(bb(-3.7, 0.55, -1.15, 1.15, 2.25, 2.42, 0.04, 1), "wood")
    p.add(bb(-3.75, 0.6, -1.2, -1.15, 2.25, 2.42), "orange")
    p.add(bb(-2.6, -1.4, 0.3, 0.45, 2.42, 3.3, 0.04, 1), "dark")
    p.add(bb(-2.55, -1.45, 0.25, 0.3, 2.55, 3.25), "glass")
    p.add(bb(-2.15, -1.85, 0.4, 0.7, 2.42, 2.55), "dark")
    p.add(bb(-0.6, 0.2, -0.3, 0.3, 2.42, 2.6, 0.03, 1), "black")
    p.add(bb(0.6, 3.4, -1.8, -0.15, 0.0, 0.45, 0.06, 1), lambda c, n: "metal" if n.z > 0.5 else "steel")
    p.add(bb(0.8, 3.2, -1.62, -0.33, 0.45, 0.5), "rubber")
    for x0, x1 in ((0.55, 0.75), (3.25, 3.45)):
        p.add(bb(x0, x1, -1.85, 2.2, 0.2, 0.95, 0.03, 1), "metal")
    p.add(bb(0.78, 3.22, -0.15, 2.1, 0.25, 0.5), "rubber")
    for k in range(9):
        y = -0.05 + 0.24 * k
        p.add(decal(rect(0.8, 3.2, y - 0.025, y + 0.025), M((0, 0, 0.5)), D), "dark")
    p.add(bar((0.35, -1.0, 0.0), (0.35, -1.0, 2.7), 0.12, 0.12, caps=False), "dark")
    p.add(bb(-0.2, 0.9, -1.12, -0.88, 2.65, 3.3, 0.05, 1), "dark")
    p.add(bb(-0.12, 0.82, -1.17, -1.12, 2.72, 3.23), "black")
    p.add(bb(0.4, 0.8, 2.1, 2.5, 0.0, 2.0), "dteal")
    p.add(bb(3.2, 3.6, 2.1, 2.5, 0.0, 2.0), "dteal")
    p.add(bb(0.4, 3.6, 2.1, 2.5, 2.0, 3.1), "dteal")
    p.add(bb(0.35, 3.65, 2.05, 2.55, 3.1, 3.3, 0.04, 1), "orange")
    for k in range(8):
        x = 0.85 + 0.3 * k
        p.add(bb(x, x + 0.26, 2.25, 2.3, 0.5, 2.0), "rubber")
    mh = fr((0, 2.1, 0), "-y")
    for k in range(6):
        x = 0.4 + 0.55 * k
        p.add(decal([(x, 2.05), (x + 0.3, 2.05), (x + 0.55, 2.95), (x + 0.25, 2.95)], mh, D), "yellow")
    p.add(bar((-2.9, 0.85, 2.42), (-2.9, 0.85, 4.3), 0.1, 0.1, caps=False), "dark")
    p.add(cyl(0.75, 0.25, (-2.9, 0.85, 4.75), (90, 0, 0), seg=18, center=True), "cream")
    logo(p, fr((-2.9, 0.725, 4.75), "-y"), 0.75, base=False, step=D)
    p.add(cyl(0.3, 0.08, (-1.9, 1.7, 0.0), seg=8), "dark")
    p.add(cyl(0.06, 1.3, (-1.9, 1.7, 0.08), seg=6, cap0=False, cap1=False), "metal")
    p.add(cyl(0.5, 0.18, (-1.9, 1.7, 1.38), seg=12, bev=0.05), "orange")
    return p


def p_arco():
    p = Prop("ArcoSeguridad", None, 900)
    for s in (-1, 1):
        x0, x1 = sorted((s * 1.5, s * 2.05))
        p.add(bb(x0, x1, -0.5, 0.5, 0.0, 6.9, 0.1, 2), lambda c, n: "dteal" if abs(n.x) > 0.5 and c.x * n.x < 0 else "cream")
        x0, x1 = sorted((s * 1.4, s * 2.2))
        p.add(bb(x0, x1, -0.75, 0.75, 0.0, 0.18, 0.05, 1), "dark")
        mi = fr((s * 1.5, 0, 0), "-x" if s > 0 else "+x")
        for j in range(9):
            for i in range(2):
                p.add(decal(circ((i - 0.5) * 0.4 * s, 1.0 + 0.6 * j, 0.07, 6), mi, D), "steel")
        mo = fr((s * 2.05, 0, 0), "+x" if s > 0 else "-x")
        p.add(decal(rect(-0.4, 0.4, 2.0, 5.0), mo, D), "orange")
    p.add(bb(-2.05, 2.05, -0.5, 0.5, 6.9, 7.7, 0.12, 2), "cream")
    p.add(bb(-2.1, 2.1, -0.55, 0.55, 6.85, 7.0, 0.03, 1), "orange")
    p.add(cyl(0.38, 0.18, (0, 0, 7.7), seg=10), "dark")
    for side in ("-y", "+y"):
        y = -0.5 if side == "-y" else 0.5
        mf = fr((0, y, 0), side)
        p.add(decal(rrect(0, 7.3, 2.6, 0.5, 0.1, 1), mf, D), "navy")
        for k in range(5):
            p.add(decal(rect(-1.0 + 0.45 * k, -0.85 + 0.45 * k, 7.15, 7.15 + 0.1 + 0.06 * k), mf, 2 * D), "lime")
    return p


def p_rayosx():
    p = Prop("RayosX", None, 1800)
    p.add(bb(-1.6, 1.6, -1.9, 1.9, 0.0, 3.1, 0.15, 2), lambda c, n: "dark" if n.z < -0.5 else "lgrey")
    p.add(bb(-1.65, 1.65, -1.95, 1.95, 0.0, 0.6, 0.05, 1), "dteal")
    p.add(bb(-1.65, 1.65, -1.95, 1.95, 2.6, 2.75), "orange")
    for s in (-1, 1):
        mf = fr((0, s * 1.95, 0), "-y" if s < 0 else "+y")
        p.add(decal(rrect(0, 1.65, 2.3, 1.3, 0.12, 2), mf, D), "black")
        for k in range(7):
            x = -0.95 + 0.32 * k
            p.add(decal(rect(x - 0.13, x + 0.13, 1.05, 2.25), mf, 2 * D), "rubber")
        poner(p, [[(0.0, 0.0), (0.4, 0.0), (0.2, 0.36)]], mf, -0.55, 2.4, 1.0, "yellow", 2 * D)
    for s in (-1, 1):
        y0, y1 = sorted((s * 1.9, s * 5.2))
        p.add(bb(-1.25, 1.25, y0, y1, 0.75, 0.95, 0.04, 1), "rubber")
        p.add(bb(-1.35, -1.2, y0, y1, 0.6, 1.25, 0.03, 1), "metal")
        p.add(bb(1.2, 1.35, y0, y1, 0.6, 1.25, 0.03, 1), "metal")
        for yy in (s * 2.4, s * 4.8):
            for xx in (-1.0, 1.0):
                p.add(bar((xx, yy, 0.0), (xx, yy, 0.75), 0.12, 0.12, caps=False), "steel")
        for k in range(7):
            yy = (y0 + 0.25) + (y1 - y0 - 0.5) * k / 6
            p.add(decal(rect(-1.2, 1.2, yy - 0.03, yy + 0.03), M((0, 0, 0.95)), D), "dark")
    for yy, col in ((-4.0, "grey"), (-2.6, "dgrey")):
        p.add(bb(-0.9, 0.9, yy - 0.6, yy + 0.6, 0.95, 1.3, 0.05, 1), col)
        p.add(decal(rect(-0.75, 0.75, yy - 0.45, yy + 0.45), M((0, 0, 1.3)), D), "dark")
    p.add(bb(-0.4, 0.3, -4.2, -3.8, 1.35, 1.55, 0.04, 1), "orange")
    p.add(cyl(0.18, 0.5, (0.25, -2.5, 1.3), (90, 0, 0), seg=8), "chrome")
    p.add(bar((2.1, -0.6, 0.0), (2.1, -0.6, 3.0), 0.14, 0.14, caps=False), "dark")
    p.add(cyl(0.45, 0.08, (2.1, -0.6, 0.0), seg=10), "dark")
    m = M((2.1, -0.6, 3.5), (0, 0, -60))
    p.add(rbox((1.6, 0.18, 1.1), (0, 0, 0), 0.05, 1, m=m), "dark")
    mf = m @ frame((0, -0.09, 0), (1, 0, 0), (0, 0, 1))
    p.add(decal(rect(-0.7, 0.7, -0.48, 0.48), mf, D), "navy")
    pollo = [K["circ"](0.0, 0.0, 0.26, 10), K["circ"](0.28, 0.2, 0.13, 8), [(0.4, 0.22), (0.55, 0.18), (0.4, 0.14)],
             [(-0.05, -0.25), (0.0, -0.42), (0.05, -0.25)], [(-0.3, 0.05), (-0.48, 0.2), (-0.35, -0.05)]]
    poner(p, pollo, mf, -0.05, 0.0, 0.9, "lime", 2 * D)
    return p


def p_cinta():
    p = Prop("CintaEquipaje", None, 4200)
    L, R0, R1 = 6.0, 2.4, 4.6
    N = 12

    def punto(i, r):
        if i <= N:
            x = L - 2 * L * i / N
            return Vector((x, r, 0))
        k = i - N
        if k <= 12:
            a = math.radians(90 + 180 * k / 12)
            return Vector((-L + r * math.cos(a), r * math.sin(a), 0))
        k2 = k - 12
        if k2 <= N:
            x = -L + 2 * L * k2 / N
            return Vector((x, -r, 0))
        k3 = k2 - N
        a = math.radians(270 + 180 * k3 / 12)
        return Vector((L + r * math.cos(a), r * math.sin(a), 0))
    total = 2 * N + 24
    bm = bmesh.new()
    za, zb = 1.3, 1.0
    ins = [bm.verts.new(punto(i, R0) + Vector((0, 0, za))) for i in range(total)]
    outs = [bm.verts.new(punto(i, R1) + Vector((0, 0, zb))) for i in range(total)]
    bajos = [bm.verts.new(punto(i, R1 + 0.15) + Vector((0, 0, 0.0))) for i in range(total)]
    for i in range(total):
        j = (i + 1) % total
        bm.faces.new((ins[i], outs[i], outs[j], ins[j]))
        bm.faces.new((outs[i], bajos[i], bajos[j], outs[j]))
    def placa(c, n):
        if n.z < 0.6:
            return "steel"
        x, y = c.x, c.y
        if abs(x) <= L:
            t = int((x + L) / (2 * L / N))
        else:
            a = math.degrees(math.atan2(y, x - math.copysign(L, x)))
            t = int(a / 15.0)
        return "rubber" if t % 2 == 0 else "dark"
    p.add(bm, placa, 30)
    bm2 = bmesh.new()
    top = [bm2.verts.new(punto(i, R1 + 0.15) + Vector((0, 0, 1.0))) for i in range(total)]
    mid = [bm2.verts.new(punto(i, R1 + 0.3) + Vector((0, 0, 0.9))) for i in range(total)]
    bot = [bm2.verts.new(punto(i, R1 + 0.3) + Vector((0, 0, 0.6))) for i in range(total)]
    for i in range(total):
        j = (i + 1) % total
        bm2.faces.new((top[i], mid[i], mid[j], top[j]))
        bm2.faces.new((mid[i], bot[i], bot[j], mid[j]))
    p.add(bm2, "yellow", 40)
    p.add(rr_loft(2 * (L + R0), 2 * R0, R0, 6, [(0.0, 0.0), (0.0, 1.9)], cap0=False), lambda c, n: "dteal" if n.z > 0.5 else "steel")
    p.add(rr_loft(2 * L + 0.6, 0.6, 0.3, 3, [(0.0, 1.9), (0.0, 2.3)]), "orange")
    for x in (-3.0, 0.0, 3.0):
        p.add(bb(x - 0.12, x + 0.12, -0.2, 0.2, 2.3, 4.6), "dark")
        p.add(bb(x - 1.0, x + 1.0, -0.12, 0.12, 4.6, 6.0, 0.08, 1), "navy")
        for side in ("-y", "+y"):
            mf = fr((0, -0.12 if side == "-y" else 0.12, 0), side)
            ux = x if side == "-y" else -x
            poner(p, MALETA, mf, ux, 5.3, 0.75, "yellow", D)
    PX = L + R1 + 0.2
    p.add(bb(PX, PX + 1.8, -2.6, 2.6, 0.0, 5.2, 0.08, 1), "dteal")
    p.add(bb(PX - 0.06, PX, -1.6, 1.6, 2.4, 4.4), "black")
    for k in range(8):
        y = -1.5 + 0.38 * k
        p.add(bb(PX - 0.16, PX - 0.11, y, y + 0.34, 2.5, 4.4), "rubber")
    mf = fr((PX, 0, 0), "-x")
    for k in range(7):
        y = -2.5 + 0.75 * k
        p.add(decal([(y, 4.5), (y + 0.4, 4.5), (y + 0.75, 5.1), (y + 0.35, 5.1)], mf, D), "yellow")
    bmr = bmesh.new()
    rx0, rz0, rx1, rz1 = PX, 2.6, L + R0 + 0.6, 1.55
    v = [bmr.verts.new((rx0, -1.4, rz0)), bmr.verts.new((rx0, 1.4, rz0)), bmr.verts.new((rx1, 1.4, rz1)), bmr.verts.new((rx1, -1.4, rz1))]
    bmr.faces.new(v[::-1])
    p.add(bmr, "metal")
    for s in (-1, 1):
        p.add(bar((rx0, s * 1.5, rz0 + 0.25), (rx1, s * 1.5, rz1 + 0.25), 0.14, 0.5, up=(0, 1, 0)), "steel")
    return p


def p_isla():
    p = Prop("IslaInfo", None, 4500)
    W, T, H = 10.0, 0.6, 13.2
    pts = [(-W, 0.0), (W, 0.0), (W, H - 1.5)]
    for k in range(1, 6):
        a = math.radians(90 * k / 6)
        pts.append((W - 1.5 + 1.5 * math.cos(a), H - 1.5 + 1.5 * math.sin(a)))
    pts.append((W - 1.5, H))
    pts.append((-W + 1.5, H))
    for k in range(1, 6):
        a = math.radians(90 + 90 * k / 6)
        pts.append((-W + 1.5 + 1.5 * math.cos(a), H - 1.5 + 1.5 * math.sin(a)))
    pts.append((-W, H - 1.5))
    p.add(prism(pts, 2 * T, frame((0, 0, 0), (1, 0, 0), (0, 0, 1))), lambda c, n: "dteal" if abs(n.y) < 0.5 else "teal")
    p.add(bb(-W - 0.1, W + 0.1, -T - 0.1, T + 0.1, 0.0, 0.6, 0.05, 1), "dark")
    mf = fr((0, -T, 0), "-y")
    p.add(decal(rrect(0, 7.4, 18.6, 9.8, 0.4, 2), mf, D), "orange")
    p.add(decal(rrect(0, 7.4, 17.9, 9.1, 0.3, 2), mf, 2 * D), "black")
    p.add(decal(rrect(0, 12.55, 9.6, 0.95, 0.3, 2), mf, 2 * D), "navy")
    poner(p, AVION, mf, -3.3, 12.55, 0.4, "white", 3 * D, math.radians(30))
    for k, col in enumerate(("orange", "teal", "yellow")):
        p.add(decal(circ(2.5 + 0.85 * k, 12.55, 0.3, 12), mf, 3 * D), col)
    mb = fr((0, T, 0), "+y")
    p.add(decal(circ(0, 6.5, 4.4, 32), mb, D), "cream")
    logo(p, fr((0, T + D, 6.5), "+y"), 4.0, base=False, step=D)
    for k, col in enumerate(("orange", "teal", "yellow")):
        p.add(decal(rect(-W + 0.6, W - 0.6, 0.8 + 0.4 * k, 1.05 + 0.4 * k), mb, D), col)
    p.add(cyl(1.7, 1.7, (0, 0, H - 0.4), (90, 0, 0), seg=24, center=True), "cream")
    p.add(cyl(1.85, 1.2, (0, 0, H - 0.4), (90, 0, 0), seg=24, center=True, cap0=False, cap1=False), "orange")
    for side, sy in (("-y", -0.76), ("+y", 0.76)):
        mc = fr((0, math.copysign(0.85, sy), H - 0.4), side)
        p.add(decal(circ(0, 0, 1.45, 24), mc, D), "white")
        for k in range(12):
            a = math.radians(30 * k)
            p.add(decal(circ(1.2 * math.cos(a), 1.2 * math.sin(a), 0.07, 6), mc, 2 * D), "dark")
        poner(p, [K["rect"](-0.05, 0.05, -0.1, 1.0)], mc, 0, 0, 1.0, "dark", 2 * D, math.radians(-75))
        poner(p, [K["rect"](-0.07, 0.07, -0.1, 0.7)], mc, 0, 0, 1.0, "dark", 2 * D, math.radians(140))
        poner(p, [K["rect"](-0.025, 0.025, -0.2, 1.15)], mc, 0, 0, 1.0, "red", 3 * D, math.radians(200))
        p.add(decal(circ(0, 0, 0.1, 8), mc, 4 * D), "dark")
    cy_, r0, r1 = -4.2, 3.0, 4.0
    m = M((0, cy_, 0))
    prof_ext = []
    n = 16
    bmd = bmesh.new()
    capas = [(r0, 0.0), (r1, 0.0), (r1, 2.3), (r0, 2.3)]
    anillos = []
    for k in range(n + 1):
        a = math.radians(180 + 180 * k / n)
        anillos.append([bmd.verts.new((r * math.cos(a), cy_ + r * math.sin(a), z)) for r, z in capas])
    for k in range(n):
        a, b = anillos[k], anillos[k + 1]
        for j in range(4):
            j2 = (j + 1) % 4
            bmd.faces.new((a[j], b[j], b[j2], a[j2]))
    bmd.faces.new(anillos[0])
    bmd.faces.new(anillos[-1][::-1])
    bmesh.ops.recalc_face_normals(bmd, faces=bmd.faces)
    p.add(bmd, lambda c, n: "teal" if Vector((c.x, c.y - cy_, 0)).length > 3.9 and abs(n.z) < 0.5 else ("cream" if abs(n.z) < 0.5 else "dark"), 30)
    bmt = bmesh.new()
    capas = [(r0 - 0.1, 2.3), (r1 + 0.2, 2.3), (r1 + 0.2, 2.45), (r0 - 0.1, 2.45)]
    anillos = []
    for k in range(n + 1):
        a = math.radians(180 + 180 * k / n)
        anillos.append([bmt.verts.new((r * math.cos(a), cy_ + r * math.sin(a), z)) for r, z in capas])
    for k in range(n):
        a, b = anillos[k], anillos[k + 1]
        for j in range(4):
            j2 = (j + 1) % 4
            bmt.faces.new((a[j], b[j], b[j2], a[j2]))
    bmt.faces.new(anillos[0])
    bmt.faces.new(anillos[-1][::-1])
    bmesh.ops.recalc_face_normals(bmt, faces=bmt.faces)
    p.add(bmt, lambda c, n: "orange" if abs(n.z) < 0.5 else "wood", 30)
    ap = math.cos(math.radians(180 / n / 2))
    mfr = fr((0, cy_ - r1 * ap - 0.005, 0), "-y")
    p.add(decal(circ(0, 1.3, 0.75, 20), mfr, 0.07), "white")
    poner(p, INFO, mfr, 0, 1.3, 0.95, "teal", 0.07 + D)
    for s in (-1, 1):
        a = math.radians(270 + s * 40)
        mm = M((r1 * ap * math.cos(a) * 1.002, cy_ + r1 * ap * math.sin(a) * 1.002, 0), (0, 0, s * 40))
        p.add(decal(rect(-0.8, 0.8, 0.5, 0.6), mm @ frame((0, 0, 0), (1, 0, 0), (0, 0, 1)), 0.07), "orange")
    p.add(bb(-2.0, -1.0, cy_ - 3.1, cy_ - 2.9, 2.45, 3.2, 0.03, 1), "cream")
    mt = fr((0, cy_ - 3.1, 0), "-y")
    p.add(decal(circ(-1.5, 2.85, 0.24, 12), mt, D), "dark")
    p.add(decal(circ(-1.5, 2.85, 0.19, 12), mt, 2 * D), "white")
    p.add(decal(rect(-1.51, -1.49, 2.85, 3.0), mt, 3 * D), "dark")
    p.add(decal(rect(-1.5, -1.38, 2.84, 2.86), mt, 3 * D), "dark")
    p.add(cyl(0.45, 0.1, (0.0, cy_ - 1.0, 0.0), seg=10), "dark")
    p.add(cyl(0.06, 1.5, (0.0, cy_ - 1.0, 0.1), seg=6, cap0=False), "metal")
    p.add(cyl(0.55, 0.2, (0.0, cy_ - 1.0, 1.6), seg=14, bev=0.06), "orange")
    return p


def p_cafeteria():
    p = Prop("Cafeteria", None, 4500)
    p.add(bb(-7.0, 7.0, -0.9, 0.5, 0.0, 0.25), "dark")
    p.add(bb(-7.1, 7.1, -1.0, 0.6, 0.25, 2.3, 0.08, 1), lambda c, n: "wood" if n.y < -0.5 else "woodb")
    for k in range(14):
        x = -6.6 + 1.0 * k
        p.add(bb(x - 0.04, x + 0.04, -1.06, -1.0, 0.35, 2.2), "woodb")
    p.add(bb(-7.25, 7.25, -1.2, 0.7, 2.3, 2.5, 0.05, 1), "cream")
    p.add(bb(-6.5, -1.5, -0.9, 0.4, 3.5, 3.6, 0.03, 1), "metal")
    for x in (-6.45, -1.55):
        for y in (-0.85, 0.35):
            p.add(bar((x, y, 2.5), (x, y, 3.5), 0.06, 0.06, caps=False), "metal")
    for x, col in ((-5.8, "cake"), (-4.6, "pink"), (-3.4, "coffee"), (-2.3, "cake")):
        p.add(cyl(0.45, 0.4, (x, -0.25, 2.55), seg=10), col)
        p.add(cyl(0.48, 0.08, (x, -0.25, 2.95), seg=10), "white" if col != "coffee" else "pink")
        p.add(lathe([(0.12, 3.0), (0.1, 3.12), (0.0, 3.16)], 6, M((x, -0.25, 0))), "red")
    p.add(bb(2.5, 3.6, -0.6, 0.0, 2.5, 2.9, 0.06, 1), "dark")
    p.add(bb(2.6, 3.5, -0.65, -0.6, 2.65, 2.85), "lime")
    p.add(cyl(0.22, 0.4, (5.2, -0.4, 2.5), seg=10, cap1=False), "glass")
    for k in range(3):
        p.add(cyl(0.18, 0.3, (6.2, 0.1, 2.5 + 0.28 * k), seg=10, r2=0.22), "white")
    p.add(bb(-7.0, 7.0, 2.2, 3.2, 0.0, 2.2, 0.06, 1), "woodb")
    p.add(bb(-7.1, 7.1, 2.1, 3.25, 2.2, 2.35, 0.04, 1), "cream")
    p.add(bb(-1.5, 1.5, 2.3, 3.2, 2.35, 4.3, 0.15, 2), lambda c, n: "chrome" if n.y > -0.5 else "red")
    for k in range(3):
        x = -0.9 + 0.9 * k
        p.add(bb(x - 0.12, x + 0.12, 2.1, 2.3, 3.0, 3.4), "dark")
        p.add(cyl(0.2, 0.3, (x, 2.05, 2.36), seg=10, r2=0.24), "white")
    p.add(cyl(0.18, 0.5, (-1.2, 2.8, 4.3), seg=8), "chrome")
    for s in (-1, 1):
        for k in range(4):
            x = s * (3.0 + 0.9 * k)
            p.add(cyl(0.3, 0.7, (x, 2.75, 2.35), seg=10), ("coffee", "cake", "pink", "lime")[k])
            p.add(cyl(0.32, 0.1, (x, 2.75, 3.05), seg=10), "dark")
    p.add(bb(-7.2, 7.2, 3.05, 3.25, 2.35, 8.2), "beam")
    mm = fr((0, 3.05, 0), "-y")
    for k, x in enumerate((-4.6, 0.0, 4.6)):
        p.add(decal(rrect(x, 6.2, 4.2, 2.8, 0.2, 2), mm, D), "wood")
        p.add(decal(rrect(x, 6.2, 3.9, 2.5, 0.15, 2), mm, 2 * D), "navy")
        poner(p, TAZA if k != 1 else [K["circ"](0, 0, 0.5, 12)], mm, x - 1.1, 6.2, 0.9, ("cream", "pink", "cake")[k], 3 * D)
        for j in range(3):
            p.add(decal(rect(x - 0.2, x + 1.0 + 0.2 * j, 6.95 - 0.55 * j, 7.1 - 0.55 * j), mm, 3 * D), "white")
            p.add(decal(circ(x + 1.65, 7.02 - 0.55 * j, 0.12, 8), mm, 3 * D), "yellow")
    for x in (-7.0, 7.0):
        p.add(bar((x, -1.7, 2.5), (x, -1.7, 5.2), 0.16, 0.16, caps=False), "wainscot")
    bma = bmesh.new()
    nraya = 14
    for k in range(nraya):
        x0 = -7.4 + 14.8 * k / nraya
        x1 = -7.4 + 14.8 * (k + 1) / nraya
        v = [bma.verts.new(c) for c in ((x0, -2.2, 5.0), (x1, -2.2, 5.0), (x1, 3.05, 6.2), (x0, 3.05, 6.2))]
        bma.faces.new(v)
    p.add(bma, lambda c, n: "orange" if int((c.x + 7.4) / (14.8 / nraya)) % 2 == 0 else "cream")
    for k in range(nraya):
        x0 = -7.4 + 14.8 * k / nraya
        x1 = x0 + 14.8 / nraya
        p.add(prism([(x0, 5.0), (x1, 5.0), ((x0 + x1) / 2, 4.6)], 0.04, frame((0, -2.2, 0), (1, 0, 0), (0, 0, 1))),
              "orange" if k % 2 == 0 else "cream")
    return p


def p_mesa():
    p = Prop("MesaCafe", None, 900)
    p.add(cyl(0.6, 0.1, (0, 0, 0), seg=12, bev=0.03), "dark")
    p.add(cyl(0.1, 2.2, (0, 0, 0.1), seg=8, cap0=False, cap1=False), "dark")
    p.add(cyl(1.2, 0.14, (0, 0, 2.3), seg=20, bev=0.04), lambda c, n: "cream" if n.z > 0.5 else "wood")
    p.add(cyl(0.2, 0.25, (0.35, 0.2, 2.44), seg=8), "white")
    p.add(cyl(0.12, 0.25, (-0.4, -0.3, 2.44), seg=6), "pot")
    p.add(blob((0.22, 0.22, 0.2), (-0.4, -0.3, 2.8), sub=1, seed=3), "leaf")
    for s in (-1, 1):
        cx = s * 2.0
        p.add(bb(cx - 0.7, cx + 0.7, -0.7, 0.7, 1.3, 1.55, 0.12, 2), "mustard" if s < 0 else "teal")
        bx0, bx1 = sorted((cx + s * 0.55, cx + s * 0.75))
        p.add(bb(bx0, bx1, -0.7, 0.7, 1.55, 3.0, 0.08, 2), "mustard" if s < 0 else "teal")
        for dx in (-0.55, 0.55):
            for dy in (-0.55, 0.55):
                p.add(bar((cx + dx, dy, 0.0), (cx + dx * 1.1, dy * 1.1, 1.3), 0.08, 0.08, caps=False), "dark")
    return p


def p_expendedora(nombre, cuerpo, franja):
    p = Prop(nombre, None, 1500)
    p.add(bb(-1.6, 1.6, -1.1, 1.1, 0.0, 6.2, 0.12, 2), lambda c, n: "dark" if n.z < -0.5 else cuerpo)
    p.add(bb(-1.55, 1.55, -1.05, 1.05, 0.0, 0.3), "dark")
    mf = fr((0, -1.1, 0), "-y")
    p.add(decal(rect(-1.45, 0.65, 1.9, 5.7), mf, D), "white")
    p.add(decal(rect(-1.35, 0.55, 2.0, 5.6), mf, 2 * D), "black")
    cols = ("red", "yellow", "lime", "blue", "orange", "pink")
    for j in range(4):
        y = 2.2 + 0.88 * j
        p.add(decal(rect(-1.35, 0.55, y - 0.08, y), mf, 3 * D), "metal")
        for i in range(5):
            x = -1.15 + 0.37 * i
            p.add(decal(rrect(x, y + 0.32, 0.26, 0.58, 0.08, 1), mf, 3 * D), cols[(i + j * 2) % len(cols)])
            p.add(decal(rect(x - 0.13, x + 0.13, y + 0.3, y + 0.38), mf, 4 * D), "white")
    p.add(bb(0.75, 1.5, -1.16, -1.1, 2.0, 5.6, 0.02, 1), "dgrey")
    mp = fr((0, -1.16, 0), "-y")
    for j in range(4):
        for i in range(2):
            p.add(decal(circ(0.95 + 0.35 * i, 4.9 - 0.32 * j, 0.11, 8), mp, D), "lgrey")
    p.add(decal(rrect(1.12, 3.0, 0.5, 0.3, 0.06, 1), mp, D), "black")
    p.add(bb(1.08, 1.16, -1.21, -1.16, 3.5, 3.85), "black")
    p.add(bb(-1.3, 0.5, -1.16, -1.1, 0.6, 1.5, 0.04, 1), "dgrey")
    p.add(bb(-1.15, 0.35, -1.21, -1.16, 0.75, 1.35), "black")
    p.add(decal(rrect(0, 5.95, 3.0, 0.45, 0.1, 1), mf, D), franja)
    poner(p, [K["rrect"](0, 0, 0.3, 0.6, 0.08, 1)], mf, -0.9, 5.95, 0.6, "white", 2 * D)
    poner(p, [K["pill"](0, 0, 1.4, 0.06, 0.0, 2)], mf, 0.4, 5.95, 1.0, "white", 2 * D)
    for s in (-1, 1):
        ms = fr((s * 1.6, 0, 0), "+x" if s > 0 else "-x")
        p.add(decal([(-1.0, 0.8), (1.0, 2.2), (1.0, 2.8), (-1.0, 1.4)], ms, D), franja)
        poner(p, [K["rrect"](0, 0, 0.7, 1.4, 0.2, 2)], ms, 0, 4.2, 1.0, "white", D)
        poner(p, [K["rrect"](0, 0, 0.56, 0.4, 0.06, 1)], ms, 0, 4.2, 1.0, franja, 2 * D)
    return p


def p_fotomaton():
    p = Prop("Fotomaton", None, 1800)
    p.add(bb(-2.0, 2.0, -1.5, 1.5, 0.0, 6.8, 0.15, 2), lambda c, n: "dark" if n.z < -0.5 else ("yellow" if abs(n.x) > 0.5 else "orange"))
    p.add(bb(-2.05, 2.05, -1.55, 1.55, 0.0, 0.5, 0.05, 1), "navy")
    mf = fr((0, -1.5, 0), "-y")
    p.add(decal(rect(-1.2, 1.2, 0.5, 5.2), mf, D), "black")
    p.add(bb(-2.0, 2.0, -1.65, -1.5, 5.2, 5.5, 0.04, 1), "orange")
    p.add(bb(-1.25, 1.25, -1.62, -1.5, 5.05, 5.15), "metal")
    for k in range(6):
        x = -1.15 + 0.22 * k
        p.add(bb(x, x + 0.2, -1.68 + 0.05 * (k % 2), -1.58, 1.0, 5.05), "red")
    p.add(cyl(0.5, 0.5, (0.6, -0.6, 0.5), seg=10), "metal")
    p.add(cyl(0.6, 0.12, (0.6, -0.6, 1.0), seg=12, bev=0.03), "red")
    p.add(bb(-1.9, 1.9, -1.6, 1.6, 6.8, 8.0, 0.12, 2), "white")
    for side, y in (("-y", -1.6), ("+y", 1.6)):
        mt = fr((0, y, 0), side)
        poner(p, CAMARA, mt, -0.8, 7.4, 0.9, "navy", D)
        p.add(decal(circ(-0.8, 7.36, 0.24, 12), mt, 2 * D), "yellow")
        for k in range(3):
            p.add(decal(circ(0.5 + 0.45 * k, 7.4, 0.14, 8), mt, D), ("orange", "teal", "yellow")[k])
    ml = fr((2.0, 0, 0), "+x")
    p.add(decal(rect(-1.1, 1.1, 1.8, 5.8), ml, D), "white")
    for k in range(4):
        y = 5.4 - 0.95 * k
        p.add(decal(rect(-0.8, 0.8, y - 0.8, y), ml, 2 * D), "lblue")
        p.add(decal(circ(0.0, y - 0.45, 0.22, 10), ml, 3 * D), "skin")
        p.add(decal(rect(-0.35, 0.35, y - 0.8, y - 0.65), ml, 3 * D), ("orange", "teal", "pink", "yellow")[k])
        p.add(decal(rect(-0.12, -0.06, y - 0.45, y - 0.4), ml, 4 * D), "black")
        p.add(decal(rect(0.06, 0.12, y - 0.45, y - 0.4), ml, 4 * D), "black")
    p.add(bb(1.98, 2.08, -1.2, -0.2, 1.2, 1.32), "black")
    mo = fr((-2.0, 0, 0), "-x")
    poner(p, CAMARA, mo, 0, 3.6, 1.6, "navy", D)
    p.add(decal(circ(0, 3.55, 0.42, 14), mo, 2 * D), "yellow")
    p.add(decal(circ(0, 3.55, 0.25, 14), mo, 3 * D), "navy")
    p.add(bb(-1.0, 1.0, -1.75, -1.6, 7.75, 8.15, 0.05, 1), "lamp")
    return p


def p_carro_maletas():
    p = Prop("CarroMaletas", None, 1200)
    p.add(bb(-0.85, 0.85, -1.2, 1.1, 0.42, 0.55, 0.03, 1), "steel")
    for k in range(5):
        y = -1.0 + 0.45 * k
        p.add(decal(rect(-0.8, 0.8, y - 0.05, y + 0.05), M((0, 0, 0.55)), D), "dark")
    for x in (-0.75, 0.75):
        for y in (-0.95, 0.85):
            p.add(bar((x, y, 0.42), (x, y, 0.3), 0.08, 0.08, caps=False), "dark")
            wheel(p, (x, y, 0.2), 0.2, 0.12, axis="x", seg=8, detail=False)
    for x in (-0.75, 0.75):
        p.add(bar((x, 1.1, 0.5), (x, 1.35, 3.1), 0.1, 0.1, caps=False), "metal")
    p.add(bar((-0.85, 1.35, 3.1), (0.85, 1.35, 3.1), 0.14, 0.14, 0.04), "red")
    p.add(bar((-0.75, 1.2, 1.6), (0.75, 1.2, 1.6), 0.07, 0.07, caps=False), "metal")
    p.add(bb(-0.8, 0.8, -1.15, 1.0, 0.55, 1.45, 0.12, 2), "blue")
    p.add(bb(-0.85, 0.85, -0.2, 0.0, 0.6, 1.5), "yellow")
    p.add(bb(-0.25, 0.25, -1.25, -1.15, 1.0, 1.15), "dark")
    p.add(bb(-0.6, 0.55, -0.9, 0.4, 1.45, 2.35, 0.1, 2), "pink")
    p.add(bb(-0.25, 0.2, -0.3, -0.2, 2.35, 2.55), "dark")
    p.add(bb(-0.25, 0.2, -0.3, 0.1, 2.5, 2.58), "dark")
    p.add(decal(circ(0.0, 0.0, 0.18, 8), fr((0.55, -0.25, 1.9), "+x"), D), "yellow")
    return p


def maceta(p, r, h, col="pot"):
    p.add(lathe([(r * 0.78, 0.0), (r, h * 0.85), (r * 1.06, h * 0.88), (r * 1.06, h), (r * 0.95, h)], 14, cap0=True, cap1=False), col)
    p.add(cyl(r * 0.95, 0.02, (0, 0, h - 0.1), seg=14, cap0=False), "soil")


def p_planta_grande():
    p = Prop("PlantaGrande", None, 1100)
    maceta(p, 1.0, 1.6)
    p.add(tube([(0, 0, 1.4), (0.1, 0.05, 3.0), (-0.05, 0.1, 4.6)], lambda u: 0.14 - 0.05 * u, k=6, steps=2, caps=False), "trunk", 70)
    p.add(tube([(0, 0.05, 3.2), (0.6, 0.2, 4.0)], lambda u: 0.07, k=5, steps=2, caps=False), "trunk", 70)
    for i, (r, loc) in enumerate((((1.4, 1.4, 1.2), (0, 0.05, 5.4)), ((1.0, 1.0, 0.9), (0.8, 0.3, 4.4)), ((0.9, 0.9, 0.85), (-0.7, -0.4, 4.7)),
                                  ((0.9, 0.9, 0.8), (0.2, -0.2, 6.3)))):
        p.add(blob(r, loc, jit=0.08, seed=20 + i), "leaf" if i % 2 == 0 else "dleaf", 180)
    return p


def p_monstera():
    p = Prop("PlantaMonstera", None, 1100)
    maceta(p, 0.9, 1.3, "cream")
    p.add(cyl(0.95, 0.12, (0, 0, 0.5), seg=14, cap0=False, cap1=False), "teal")
    rnd = random.Random(5)
    for k in range(8):
        a = 2 * math.pi * k / 8 + rnd.uniform(-0.2, 0.2)
        L = rnd.uniform(1.6, 2.4)
        tip = Vector((math.cos(a) * L * 0.7, math.sin(a) * L * 0.7, 1.3 + L * 0.9))
        p.add(tube([(0, 0, 1.2), (tip.x * 0.4, tip.y * 0.4, 1.3 + L * 0.7), tuple(tip)], lambda u: 0.04, k=4, steps=2, caps=False), "dleaf", 60)
        m = M(tuple(tip), (rnd.uniform(-25, 25), 0, math.degrees(a)))
        hoja = ellipsoid((0.85, 0.55, 0.06), m @ M((0.6, 0, 0), (0, -25, 0)), u=10, v=4)
        p.add(hoja, "leaf" if k % 2 else "dleaf", 180)
    return p


def p_jardinera():
    p = Prop("Jardinera", None, 1400)
    p.add(bb(-4.0, 4.0, -0.8, 0.8, 0.0, 1.3, 0.06, 1), lambda c, n: "soil" if n.z > 0.5 else "wood")
    for k in range(16):
        x = -3.75 + 0.5 * k
        for s in (-1, 1):
            y0, y1 = sorted((s * 0.8, s * 0.86))
            p.add(bb(x - 0.02, x + 0.02, y0, y1, 0.1, 1.2), "woodb")
    for s in (-1, 1):
        y0, y1 = sorted((s * 0.7, s * 0.88))
        p.add(bb(-4.08, 4.08, y0, y1, 1.3, 1.42, 0.03, 1), "woodb")
        x0, x1 = sorted((s * 3.9, s * 4.08))
        p.add(bb(x0, x1, -0.7, 0.7, 1.3, 1.42, 0.03, 1), "woodb")
    rnd = random.Random(9)
    for k in range(7):
        x = -3.3 + 1.1 * k
        s = rnd.uniform(0.6, 0.85)
        p.add(blob((s, s * 0.8, s * 0.8), (x, rnd.uniform(-0.15, 0.15), 1.3 + s * 0.45), jit=0.07, seed=40 + k), "leaf" if k % 2 else "dleaf", 180)
    for k in range(5):
        x = -3.0 + 1.5 * k
        p.add(ellipsoid((0.16, 0.16, 0.12), M((x + 0.3, -0.45, 2.0 + rnd.uniform(-0.15, 0.1))), u=6, v=4), ("pink", "yellow", "red", "purple", "white")[k])
    return p


def p_lounge():
    p = Prop("RinconLounge", None, 2600)

    def sillon(cx, cy, giro, col):
        m = M((cx, cy, 0), (0, 0, giro))
        p.add(rbox((2.2, 2.0, 0.9), (0, 0, 0.75), 0.25, 2, m=m), col)
        p.add(rbox((2.2, 0.6, 1.6), (0, 0.75, 1.6), 0.25, 2, m=m), col)
        for s in (-1, 1):
            p.add(rbox((0.45, 2.0, 0.8), (s * 1.0, 0, 1.4), 0.18, 2, m=m), col)
        p.add(rbox((1.6, 1.4, 0.3), (0, -0.15, 1.3), 0.12, 2, m=m), "cream")
        for dx in (-0.9, 0.9):
            for dy in (-0.8, 0.8):
                p.add(rbox((0.15, 0.15, 0.3), (dx, dy, 0.15), m=m), "woodb")
    sillon(-3.0, 0.0, 90, "mustard")
    sillon(3.0, 0.0, -90, "teal")
    p.add(cyl(1.0, 0.12, (0, 0, 1.1), seg=18, bev=0.04), "wood")
    p.add(cyl(0.12, 1.1, (0, 0, 0), seg=8, cap0=False, cap1=False), "dark")
    p.add(cyl(0.6, 0.3, (0, 0, 0), seg=12), "dark")
    for k, col in enumerate(("red", "sky", "yellow")):
        p.add(rbox((0.7, 0.5, 0.03), (-0.2 + 0.25 * k, -0.15 + 0.2 * k, 1.27 + D * k), rot=(0, 0, 15 * k - 10)), col)
    p.add(cyl(0.35, 0.3, (2.8, 2.2, 0.0), seg=10), "dark")
    p.add(cyl(0.05, 3.78, (2.8, 2.2, 0.3), seg=6, cap0=False), "dark")
    p.add(lathe([(0.75, 3.6), (0.75, 4.1), (0.45, 4.5)], 12, M((2.8, 2.2, 0)), cap0=False, cap1=False), "shade")
    p.add(lathe([(0.7, 3.6), (0.7, 4.05), (0.4, 4.45)], 12, M((2.8, 2.2, 0)), cap0=False, cap1=False), "lamp")
    return p


def p_estanteria():
    p = Prop("EstanteriaTienda", None, 2200)
    p.add(bb(-3.0, 3.0, 0.2, 1.0, 0.0, 4.2, 0.06, 1), "plum")
    p.add(bb(-3.0, 3.0, -0.4, 0.2, 0.0, 0.4), "plum")
    rnd = random.Random(3)
    cols = ("pink", "gold", "purple", "hpink", "mint", "lime", "sky", "peach", "red", "white")
    for j, z in enumerate((0.4, 1.6, 2.8)):
        p.add(bb(-2.95, 2.95, -0.45, 0.2, z, z + 0.08), "white")
        x = -2.7
        while x < 2.5:
            w = rnd.uniform(0.3, 0.6)
            h = rnd.uniform(0.4, 0.9)
            col = rnd.choice(cols)
            if rnd.random() < 0.45:
                p.add(cyl(w * 0.4, h, (x + w / 2, -0.1, z + 0.08), seg=8), col)
                p.add(cyl(w * 0.18, 0.18, (x + w / 2, -0.1, z + 0.08 + h), seg=6), "gold")
            else:
                p.add(bb(x, x + w, -0.35, 0.1, z + 0.08, z + 0.08 + h, 0.03, 1), col)
            x += w + 0.08
    p.add(bb(-3.05, 3.05, -0.5, 1.05, 4.2, 4.5, 0.05, 1), "gold")
    mf = fr((0, 0.2, 0), "-y")
    p.add(decal(rect(-2.9, 2.9, 3.8, 4.15), mf, D), "hpink")
    return p


def p_chocolate():
    p = Prop("ChocolateGigante", None, 400)
    tri = [(-1.0, 0.0), (1.0, 0.0), (0.0, 1.7)]
    p.add(prism(tri, 6.0, frame((0, 0, 0), (0, 1, 0), (0, 0, 1)), bev=0.04), lambda c, n: "coffee" if abs(n.x) > 0.5 else "gold")
    tri2 = [(-1.05, 0.0), (1.05, 0.0), (0.0, 1.79)]
    p.add(prism(tri2, 2.0, frame((0, 0, 0), (0, 1, 0), (0, 0, 1))), lambda c, n: "red" if abs(n.x) < 0.5 else "coffee")
    return p


def p_timbre():
    p = Prop("Timbre", None, 200)
    p.add(cyl(0.32, 0.06, (0, 0, 0), seg=12), "dark")
    p.add(lathe([(0.27, 0.06), (0.26, 0.15), (0.18, 0.27), (0.06, 0.31), (0.0, 0.32)], 12), "gold")
    p.add(cyl(0.05, 0.1, (0, 0, 0.31), seg=6), "dark")
    return p


def p_microfono():
    p = Prop("Microfono", None, 400)
    p.add(cyl(0.3, 0.08, (0, 0, 0), seg=10), "dark")
    p.add(tube([(0, 0, 0.05), (0, 0, 0.4), (0, -0.15, 0.65), (0, -0.35, 0.75)], lambda u: 0.035, k=5, steps=3), "dark")
    p.add(ellipsoid((0.11, 0.17, 0.11), M((0, -0.42, 0.77), (-15, 0, 0))), "metal")
    p.add(bb(0.12, 0.26, -0.12, 0.12, 0.08, 0.13), "red")
    return p


def p_boton_rojo():
    p = Prop("BotonRojo", None, 120)
    p.add(cyl(0.3, 0.06, (0, 0, 0), (90, 0, 0), seg=12), "dark")
    p.add(lathe([(0.22, 0.0), (0.22, 0.08), (0.16, 0.14), (0.0, 0.15)], 12, M((0, -0.06, 0), (90, 0, 0))), "red")
    return p


def p_pelota():
    p = Prop("Pelota", None, 500)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.1)
    bmesh.ops.translate(bm, vec=Vector((0, 0, 1.1)), verts=bm.verts)
    cols = ("red", "white", "yellow", "white", "blue", "white")

    def gajo(c, n):
        if abs(n.z) > 0.93:
            return "white"
        a = math.degrees(math.atan2(c.y, c.x)) % 360
        return cols[int(a // 60)]
    p.add(bm, gajo, 60)
    return p


def p_lata():
    p = Prop("Lata", None, 120)
    p.add(lathe([(0.0, 0.0), (0.2, 0.0), (0.25, 0.06), (0.25, 0.68), (0.2, 0.75), (0.0, 0.75)], 10),
          lambda c, n: "metal" if c.z > 0.7 or c.z < 0.05 else ("white" if 0.3 < c.z < 0.42 else "red"), 50)
    return p


def p_papelera():
    p = Prop("Papelera", None, 300)
    p.add(lathe([(0.0, 0.0), (0.55, 0.0), (0.6, 1.4), (0.0, 1.4)], 12), lambda c, n: "dark" if c.z < 0.1 else "dteal", 40)
    p.add(lathe([(0.65, 1.4), (0.65, 1.55), (0.4, 1.75), (0.0, 1.8)], 12, cap0=False), "lgrey")
    p.add(decal(circ(0, 0.8, 0.22, 10), fr((0, -0.58, 0), "-y"), D), "lime")
    return p


def p_postes():
    p = Prop("PostesCola", None, 1800)
    filas = 4
    Lr = 7.0
    postes = []
    for f in range(filas + 1):
        y = -3.0 + 1.5 * f
        for x in (-Lr / 2, 0.0, Lr / 2):
            postes.append((x, y))
    for x, y in postes:
        p.add(cyl(0.3, 0.06, (x, y, 0.0), seg=8), "dark")
        p.add(cyl(0.06, 1.9, (x, y, 0.06), seg=6, cap0=False, cap1=False), "chrome")
        p.add(cyl(0.11, 0.18, (x, y, 1.9), seg=8), "dark")
    for f in range(filas + 1):
        y = -3.0 + 1.5 * f
        x0, x1 = (-Lr / 2, Lr / 2 - 1.6) if f % 2 == 0 else (-Lr / 2 + 1.6, Lr / 2)
        if f == 0 or f == filas:
            x0, x1 = -Lr / 2, Lr / 2
        p.add(bar((x0, y, 1.82), (x1, y, 1.82), 0.03, 0.18, up=(0, 1, 0)), "dteal")
    return p


BUILDERS = [p_suelo, p_paredes, p_techo, p_facturacion, p_arco, p_rayosx, p_cinta, p_isla, p_cafeteria, p_mesa,
            lambda: p_expendedora("ExpendedoraRoja", "red", "yellow"), lambda: p_expendedora("ExpendedoraAzul", "blue", "lime"),
            p_fotomaton, p_carro_maletas, p_planta_grande, p_monstera, p_jardinera, p_lounge, p_estanteria, p_chocolate,
            p_pelota, p_lata, p_papelera, p_postes, p_timbre, p_microfono, p_boton_rojo]


def limites(p):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for bm, _, _ in p.parts:
        for v in bm.verts:
            for i in range(3):
                mn[i] = min(mn[i], v.co[i])
                mx[i] = max(mx[i], v.co[i])
    return mn, mx


def palette_image():
    img = bpy.data.images.new("lobby_palette", 128, 128, alpha=True)
    px = [0.0] * (128 * 128 * 4)
    for i, (_, hx) in enumerate(PAL):
        r, g, b = hex_rgb(hx)
        gx, gy = i % 8, i // 8
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * 128 + x) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "lobby_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def arg(name, default=None):
    if name in ARGS:
        i = ARGS.index(name)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return default


def construir(only=None, exportar=True):
    img = palette_image()
    mat = K["palette_material"](img)
    objs, manifest = {}, []
    ok = True
    for b in BUILDERS:
        p = b()
        if only and p.name not in only:
            continue
        mn, mx = limites(p)
        p.size = tuple(mx - mn)
        ob, tris, raw, sc, _, _ = K["make_object"](p, mat)
        objs[p.name] = ob
        ok = ok and tris <= p.budget
        bmin = [round(-mx.x, 3), round(mn.z, 3), round(mn.y, 3)]
        bmax = [round(-mn.x, 3), round(mx.z, 3), round(mx.y, 3)]
        print("PIEZA %-18s tris %5d / %5d %s  min %s  max %s" % (p.name, tris, p.budget, "OK" if tris <= p.budget else "OVER", bmin, bmax))
        if exportar:
            K["export_fbx"](ob)
        manifest.append({"nombre": p.name, "archivo": p.name + ".fbx", "bbox_min": bmin, "bbox_max": bmax, "triangulos": tris})
    if exportar:
        ruta = os.path.join(OUT, "manifest.json")
        if only and os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as fh:
                manifest = [e for e in json.load(fh) if e["nombre"] not in only] + manifest
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("TODO OK" if ok else "ALGUNA PIEZA SE PASA")
    return objs


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    only = arg("--only")
    only = set(only.split(",")) if isinstance(only, str) else None
    objs = construir(only, not arg("--no-export"))
    hojas = arg("--hojas")
    if not hojas:
        return
    scene = bpy.context.scene
    K["render_setup"](scene, int(arg("--threads", "8")))
    for o in objs.values():
        o.hide_render = True
    filas = [
        [["Facturacion", "ArcoSeguridad", "RayosX", "ExpendedoraRoja", "ExpendedoraAzul", "Fotomaton"],
         ["CarroMaletas", "PlantaGrande", "PlantaMonstera", "Jardinera", "Papelera", "Pelota", "Lata", "ChocolateGigante"]],
        [["CintaEquipaje", "IslaInfo"], ["Cafeteria", "MesaCafe", "RinconLounge", "EstanteriaTienda", "PostesCola"]],
    ]
    for i, rows in enumerate(filas):
        if str(i + 1) not in hojas.split(","):
            continue
        st = K["Stage"](objs)
        K["sheet_catalog"](st, [[n for n in r if n in objs] for r in rows if any(n in objs for n in r)], 1.5)
        scene.render.filepath = os.path.join(arg("--dir", OUT), "lobby_kit_%d.png" % (i + 1))
        bpy.ops.render.render(write_still=True)
        print("RENDER", scene.render.filepath)
        st.clear()


main()
