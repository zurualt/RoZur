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
    ("cream", "F3EBDD"), ("wall", "E9DCC4"), ("wallb", "C9A27A"), ("floor", "B9B4AA"), ("floord", "9C978E"), ("yellow", "F6C445"),
    ("ink", "1B1B21"), ("orange", "F27B2B"), ("teal", "1FA6A0"), ("dteal", "157F7B"), ("red", "D9443A"), ("dred", "9E2A28"),
    ("metal", "A9B0B8"), ("dmetal", "6B737C"), ("rubber", "2A2C31"), ("wood", "C98B4E"), ("dwood", "8A5A33"), ("straw", "E8C872"),
    ("dstraw", "C9A24E"), ("white", "F7F7F2"), ("blue", "6FB4E3"), ("lblue", "A9D8F2"), ("green", "6DBE45"), ("dgreen", "3F8F3A"),
    ("croc", "6BBF59"), ("pink", "F29BB2"), ("roof", "8A8F96"), ("droof", "6E737A"), ("brick", "C46A4A"), ("fish", "8FB7C9"),
    ("steel", "7C858F"), ("chrome", "D0D5DA"), ("lamp", "FFE2A8"), ("hpink", "E8457A"), ("navy", "1E2A3A"), ("mint", "9ED9C4"),
    ("bun", "D98A3A"), ("patty", "6F4024"), ("cheese", "F5B83D"), ("sky", "BFE3F2"),
]
IDX = {n: i for i, (n, _) in enumerate(PAL)}


def suv(n):
    i = IDX[n]
    return ((i % 8 + 0.5) / 8.0, (i // 8 + 0.5) / 8.0)


K["PAL"], K["IDX"], K["suv"] = PAL, IDX, suv
for _n in ("bb", "rbox", "cyl", "lathe", "prism", "decal", "rect", "circ", "rrect", "pill", "arc_strip", "bar", "tube", "ellipsoid",
           "ring", "frame", "fr", "M", "Prop", "hex_rgb", "lin"):
    globals()[_n] = K[_n]

E = 0.012


def caja(p, x0, x1, y0, y1, z0, z1, rol, bev=0.0):
    return p.add(bb(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1), bev, 2 if bev > 0 else 1), rol)


def poner(p, polys, m, rol, w, cx=0.0, cy=0.0, s=1.0, a=0.0):
    ca, sa = math.cos(a), math.sin(a)
    for poly in polys:
        p.add(decal([(cx + (x * ca - y * sa) * s, cy + (x * sa + y * ca) * s) for x, y in poly], m, w), rol)


DIGITOS = {
    1: [(1, 2, 0, 5), (0, 1, 3, 4), (0, 3, 0, 1)],
    2: [(0, 3, 4, 5), (2, 3, 3, 4), (0, 3, 2, 3), (0, 1, 1, 2), (0, 3, 0, 1)],
    3: [(0, 3, 4, 5), (2, 3, 0, 5), (1, 2, 2, 3), (0, 2, 0, 1)],
    4: [(0, 1, 2, 5), (0, 3, 2, 3), (2, 3, 0, 5)],
}


def digito(p, m, n, cx, cy, alto, rol, w):
    c = alto / 5.0
    for u0, u1, v0, v1 in DIGITOS[n]:
        p.add(decal(rect(cx + (u0 - 1.5) * c, cx + (u1 - 1.5) * c, cy + (v0 - 2.5) * c, cy + (v1 - 2.5) * c), m, w), rol)


MALETA = [rrect(0, -0.1, 1.2, 0.85, 0.14, 2), rect(-0.3, -0.2, 0.32, 0.56), rect(0.2, 0.3, 0.32, 0.56), rect(-0.3, 0.3, 0.48, 0.58)]
MALETA_RAYAS = [rect(-0.3, -0.2, -0.5, 0.3), rect(0.2, 0.3, -0.5, 0.3)]
FLECHA = [[(-0.6, -0.14), (0.1, -0.14), (0.1, -0.38), (0.6, 0.0), (0.1, 0.38), (0.1, 0.14), (-0.6, 0.14)]]
CARRO = [rect(-0.7, 0.6, -0.2, 0.0), rect(0.6, 0.9, -0.14, -0.06), rect(-0.7, -0.62, 0.0, 0.42), rect(0.52, 0.6, 0.0, 0.42),
         circ(-0.42, -0.34, 0.15, 10), circ(0.32, -0.34, 0.15, 10)]
AVION = [pill(0, 0, 1.7, 0.16, 0.0, 3),
         [(0.18, 0.08), (-0.3, 0.95), (-0.55, 0.95), (-0.25, 0.08)], [(0.18, -0.08), (-0.25, -0.08), (-0.55, -0.95), (-0.3, -0.95)],
         [(-0.72, 0.06), (-0.98, 0.42), (-1.1, 0.42), (-0.98, 0.06)], [(-0.72, -0.06), (-0.98, -0.06), (-1.1, -0.42), (-0.98, -0.42)]]
GOTA = [circ(0, -0.18, 0.42, 14), [(-0.36, -0.02), (0.0, 0.62), (0.36, -0.02)]]
AVISO = [[(-0.62, -0.5), (0.62, -0.5), (0.0, 0.58)]]
EXCLAMA = [rect(-0.07, 0.07, -0.12, 0.3), circ(0, -0.28, 0.08, 8)]
CROC_ARRIBA = [[(-0.9, 0.0), (-0.55, 0.32), (0.05, 0.36), (0.75, 0.2), (0.95, 0.08), (0.9, 0.0)]]
CROC_ABAJO = [[(-0.9, -0.05), (0.85, -0.12), (0.9, -0.22), (0.2, -0.36), (-0.6, -0.3)]]
CROC_DIENTES = [[(x, 0.0), (x + 0.07, -0.11), (x + 0.14, 0.0)] for x in (-0.35, -0.15, 0.05, 0.25, 0.45, 0.65)]
OJO = [circ(-0.42, 0.42, 0.16, 10)]
PUPILA = [circ(-0.39, 0.43, 0.07, 8)]


def cartel(nombre, ancho, alto, borde, fondo, dibujo):
    p = Prop(nombre, None, 1600)
    caja(p, -ancho / 2, ancho / 2, -0.15, 0.15, 0, alto, borde, 0.06)
    m = fr((0, -0.15, alto / 2), "-y")
    p.add(decal(rrect(0, 0, ancho - 0.36, alto - 0.36, 0.14, 2), m, E), fondo)
    for k in (-1, 1):
        p.add(cyl(0.07, 0.04, (k * (ancho / 2 - 0.16), -0.17, alto - 0.16), (90, 0, 0), 8), "metal")
    dibujo(p, m)
    return p


def d_maletas(p, m):
    poner(p, MALETA, m, "orange", 2 * E, -2.1, 0, 1.25)
    poner(p, MALETA_RAYAS, m, "dred", 3 * E, -2.1, 0, 1.25)
    poner(p, FLECHA, m, "ink", 2 * E, -0.3, 0, 1.4)
    poner(p, CARRO, m, "dteal", 2 * E, 1.8, 0.1, 1.35)
    poner(p, [rrect(0, 0.3, 0.9, 0.55, 0.08, 1)], m, "orange", 3 * E, 1.75, 0.1, 1.0)


def d_animales(p, m):
    poner(p, AVISO, m, "ink", 2 * E, -1.45, 0, 1.25)
    poner(p, AVISO, m, "yellow", 3 * E, -1.45, -0.02, 1.0)
    poner(p, EXCLAMA, m, "ink", 4 * E, -1.45, 0, 1.25)
    poner(p, CROC_ARRIBA + CROC_ABAJO, m, "croc", 2 * E, 0.75, 0.05, 1.35)
    poner(p, CROC_DIENTES, m, "white", 3 * E, 0.75, 0.05, 1.35)
    poner(p, OJO, m, "white", 3 * E, 0.75, 0.05, 1.35)
    poner(p, PUPILA, m, "ink", 4 * E, 0.75, 0.05, 1.35)


def d_combustible(p, m):
    poner(p, GOTA, m, "ink", 2 * E, -0.55, 0, 1.45)
    poner(p, GOTA, m, "yellow", 3 * E, -0.55, -0.04, 1.2)
    poner(p, AVION, m, "dteal", 2 * E, 0.75, -0.05, 0.55, math.pi / 2)


def d_salida(p, m):
    poner(p, MALETA, m, "orange", 2 * E, -2.4, 0, 1.5)
    poner(p, MALETA_RAYAS, m, "dred", 3 * E, -2.4, 0, 1.5)
    poner(p, FLECHA, m, "ink", 2 * E, -0.3, 0, 1.6)
    poner(p, AVION, m, "teal", 2 * E, 2.1, 0, 1.1)


def p_cartel_maletas():
    return cartel("CartelMaletas", 7.0, 2.6, "orange", "cream", d_maletas)


def p_cartel_animales():
    return cartel("CartelAnimales", 5.0, 2.6, "teal", "cream", d_animales)


def p_cartel_combustible():
    return cartel("CartelCombustible", 3.2, 2.6, "red", "cream", d_combustible)


def p_cartel_salida():
    return cartel("CartelSalida", 8.0, 3.0, "teal", "white", d_salida)


NX, NZ, NB = 34.0, 72.0, 90.0


def hx(X):
    return -(X - NX)


def hy(Z):
    return Z - NZ


def hz(Y):
    return Y - NB


def hcaja(p, X0, X1, Y0, Y1, Z0, Z1, rol, bev=0.0):
    return caja(p, hx(X0), hx(X1), hy(Z0), hy(Z1), hz(Y0), hz(Y1), rol, bev)


def p_nave():
    p = Prop("NaveCarga", None, 14000)
    S, T = 90.5, 108.5
    hcaja(p, 17.7, 50.3, 90.0, S, 51.7, 92.3, "floor")
    hcaja(p, 17.7, 18.3, S, T, 51.7, 92.3, "wall")
    hcaja(p, 49.7, 50.3, S, T, 51.7, 92.3, "wall")
    hcaja(p, 18.3, 49.7, S, T, 91.7, 92.3, "wall")
    hcaja(p, 17.7, 26.8, S, T, 51.7, 52.3, "wall")
    hcaja(p, 41.2, 50.3, S, T, 51.7, 52.3, "wall")
    hcaja(p, 26.8, 41.2, 99.9, T, 51.7, 52.3, "wall")
    interiores = [("-x", hx(18.3) - E, 52.3, 91.7), ("+x", hx(49.7) + E, 52.3, 91.7), ("-y", hy(91.7) - E, 18.3, 49.7)]
    for lado, c, a, b in interiores:
        if lado == "-y":
            o, u0, u1 = (0, c, 0), hx(b), hx(a)
        else:
            o = (c, 0, 0)
            u0, u1 = (-hy(b), -hy(a)) if lado == "-x" else (hy(a), hy(b))
        m = fr(o, lado)
        p.add(decal(rect(u0, u1, hz(S), hz(93.2)), m, 0), "wallb")
        p.add(decal(rect(u0, u1, hz(93.2), hz(93.55)), m, 0), "orange")
        p.add(decal(rect(u0, u1, hz(106.4), hz(106.7)), m, 0), "teal")
    m = fr((0, hy(52.3) + E, 0), "+y")
    for u0, u1 in ((-hx(18.3), -hx(26.8)), (-hx(41.2), -hx(49.7))):
        a, b = min(u0, u1), max(u0, u1)
        p.add(decal(rect(a, b, hz(S), hz(93.2)), m, 0), "wallb")
        p.add(decal(rect(a, b, hz(93.2), hz(93.55)), m, 0), "orange")
        p.add(decal(rect(a, b, hz(106.4), hz(106.7)), m, 0), "teal")
    exteriores = [("+x", hx(17.7) + E, 51.7, 92.3), ("-x", hx(50.3) - E, 51.7, 92.3), ("+y", hy(92.3) + E, 17.7, 50.3)]
    for lado, c, a, b in exteriores:
        if lado == "+y":
            o, u0, u1 = (0, c, 0), -hx(a), -hx(b)
            u0, u1 = min(u0, u1), max(u0, u1)
        else:
            o = (c, 0, 0)
            u0, u1 = (hy(a), hy(b)) if lado == "+x" else (-hy(b), -hy(a))
        m = fr(o, lado)
        p.add(decal(rect(u0, u1, 0, hz(94.5)), m, 0), "teal")
        p.add(decal(rect(u0, u1, hz(94.5), hz(94.9)), m, 0), "yellow")
    m = fr((0, hy(51.7) - E, 0), "-y")
    for X0, X1 in ((17.7, 26.8), (41.2, 50.3)):
        p.add(decal(rect(hx(X1), hx(X0), 0, hz(94.5)), m, 0), "teal")
        p.add(decal(rect(hx(X1), hx(X0), hz(94.5), hz(94.9)), m, 0), "yellow")
    for X in [18.6 + 2.0 * k for k in range(16)]:
        if not (25.6 < X < 42.4):
            hcaja(p, X, X + 0.3, 94.9, 107.2, 51.55, 51.7, "metal")
        hcaja(p, X, X + 0.3, 94.9, 107.2, 92.3, 92.45, "metal")
    for Z in [53.0 + 2.0 * k for k in range(20)]:
        hcaja(p, 17.55, 17.7, 94.9, 107.2, Z, Z + 0.3, "metal")
        hcaja(p, 50.3, 50.45, 94.9, 107.2, Z, Z + 0.3, "metal")
    hcaja(p, 17.4, 50.6, 107.2, T + 0.7, 51.4, 51.7, "orange")
    hcaja(p, 17.4, 50.6, 107.2, T + 0.7, 92.3, 92.6, "orange")
    hcaja(p, 17.4, 17.7, 107.2, T + 0.7, 51.7, 92.3, "orange")
    hcaja(p, 50.3, 50.6, 107.2, T + 0.7, 51.7, 92.3, "orange")
    for X0, X1 in ((17.7, 24.0), (44.0, 50.3)):
        hcaja(p, X0, X1, T, T + 0.6, 51.7, 92.3, "droof")
    for Z0, Z1 in ((51.7, 58.0), (62.0, 70.0), (74.0, 82.0), (86.0, 92.3)):
        hcaja(p, 24.0, 44.0, T, T + 0.6, Z0, Z1, "droof")
    for Z0, Z1 in ((58.0, 62.0), (70.0, 74.0), (82.0, 86.0)):
        for X0, X1, A, B in ((23.7, 24.0, Z0, Z1), (44.0, 44.3, Z0, Z1)):
            hcaja(p, X0, X1, T + 0.6, T + 1.0, A, B, "metal")
        hcaja(p, 23.7, 44.3, T + 0.6, T + 1.0, Z0 - 0.3, Z0, "metal")
        hcaja(p, 23.7, 44.3, T + 0.6, T + 1.0, Z1, Z1 + 0.3, "metal")
    for Z in (54.0, 61.5, 68.5, 75.5, 82.5, 89.5):
        hcaja(p, 18.3, 49.7, T - 1.1, T, Z - 0.25, Z + 0.25, "dteal")
        hcaja(p, 18.3, 18.9, S, T - 1.1, Z - 0.3, Z + 0.3, "dteal")
        hcaja(p, 49.1, 49.7, S, T - 1.1, Z - 0.3, Z + 0.3, "dteal")
    hcaja(p, 33.7, 34.3, T - 0.9, T, 52.3, 91.7, "dteal")
    for X in (26.2, 41.2):
        for k in range(12):
            hcaja(p, X, X + 0.6, S + k * 0.8, S + (k + 1) * 0.8, 52.3, 52.35, "yellow" if k % 2 == 0 else "ink")
            hcaja(p, X, X + 0.6, S + k * 0.8, S + (k + 1) * 0.8, 51.65, 51.7, "yellow" if k % 2 == 0 else "ink")
    hcaja(p, 26.2, 41.8, 99.9, 100.5, 52.3, 52.35, "yellow")
    hcaja(p, 26.2, 41.8, 99.9, 100.5, 51.65, 51.7, "yellow")
    for X in (26.5, 41.15):
        hcaja(p, X, X + 0.35, S, T - 1.1, 52.3, 53.0, "dmetal")
    hcaja(p, 26.5, 41.5, 106.9, T - 1.1, 52.95, 54.1, "dmetal")
    suelo = fr((0, 0, hz(S) + E), "+z")
    for X0, X1, Z0, Z1 in ((30.8, 37.2, 54.8, 55.1), (30.8, 37.2, 74.9, 75.2), (30.8, 31.1, 54.8, 75.2), (36.9, 37.2, 54.8, 75.2)):
        p.add(decal(rect(hx(X1), hx(X0), hy(Z0), hy(Z1)), suelo, 0), "yellow")
    p.add(decal(rect(hx(41.2), hx(26.8), hy(52.3), hy(53.9)), suelo, 0), "yellow")
    for k in range(9):
        X = 27.4 + k * 1.5
        p.add(decal([(hx(X), hy(52.3)), (hx(X + 0.6), hy(52.3)), (hx(X + 1.1), hy(53.9)), (hx(X + 0.5), hy(53.9))], suelo, E), "ink")
    for k in range(10):
        Z = 55.5 + k * 2.5
        p.add(decal(rect(hx(28.75), hx(28.45), hy(Z), hy(Z + 1.5)), suelo, 0), "yellow")
    for X0, X1, Z0, Z1 in ((45.6, 49.7, 54.4, 54.7), (45.6, 49.7, 59.3, 59.6), (45.6, 45.9, 54.4, 59.6)):
        p.add(decal(rect(hx(X1), hx(X0), hy(Z0), hy(Z1)), suelo, 0), "red")
    p.add(decal(circ(hx(31.0), hy(85.5), 3.0, 24), suelo, 0), "teal")
    p.add(decal(circ(hx(31.0), hy(85.5), 2.6, 24), suelo, E), "dteal")
    poner(p, AVION, suelo, "cream", 2 * E, hx(31.0), hy(85.5), 2.0, math.pi / 2)
    oeste = fr((hx(18.3) - E, 0, 0), "-x")
    este = fr((hx(49.7) + E, 0, 0), "+x")
    for Z in (56.0, 64.0, 76.0, 84.0):
        for m, u in ((oeste, -hy(Z + 2.0)), (este, hy(Z - 2.0))):
            p.add(decal(rect(u, u + 4.0, hz(103.6), hz(106.1)), m, E), "white")
            p.add(decal(rect(u + 0.2, u + 3.8, hz(103.8), hz(105.9)), m, 2 * E), "sky")
            p.add(decal(rect(u + 1.9, u + 2.1, hz(103.8), hz(105.9)), m, 3 * E), "white")
    for Z in (56.0, 64.0, 76.0, 84.0):
        for m, u in ((fr((hx(17.7) + E, 0, 0), "+x"), hy(Z - 2.0)), (fr((hx(50.3) - E, 0, 0), "-x"), -hy(Z + 2.0))):
            p.add(decal(rect(u, u + 4.0, hz(103.6), hz(106.1)), m, 0), "white")
            p.add(decal(rect(u + 0.2, u + 3.8, hz(103.8), hz(105.9)), m, E), "sky")
    m = este
    p.add(decal(rect(hy(61.5), hy(66.5), hz(95.0), hz(99.6)), m, E), "white")
    p.add(decal(rect(hy(61.7), hy(66.3), hz(95.2), hz(99.4)), m, 2 * E), "sky")
    p.add(decal(circ(hy(65.2), hz(98.5), 0.55, 12), m, 3 * E), "yellow")
    poner(p, AVION, m, "teal", 3 * E, hy(63.6), hz(97.0), 1.6, 0.3)
    sur = fr((0, hy(91.7) - E, 0), "-y")
    p.add(decal(circ(hx(30.0), hz(100.0), 1.0, 20), sur, E), "ink")
    p.add(decal(circ(hx(30.0), hz(100.0), 0.86, 20), sur, 2 * E), "white")
    p.add(decal(pill(hx(30.0), hz(100.0) + 0.3, 0.6, 0.06, math.pi / 2, 2), sur, 3 * E), "ink")
    p.add(decal(pill(hx(30.0) + 0.2, hz(100.0), 0.45, 0.05, 0.0, 2), sur, 3 * E), "red")
    return p


def p_persiana():
    p = Prop("PersianaNave", None, 2400)
    caja(p, -7.05, 7.05, -0.14, 0.14, 0.5, 9.2, "ink")
    for k in range(11):
        z0 = 0.5 + k * 0.79
        caja(p, -7.1, 7.1, -0.2, 0.2, z0 + 0.03, z0 + 0.76, "orange" if k % 2 == 0 else "yellow", 0.03)
    caja(p, -7.1, 7.1, -0.22, 0.22, 0, 0.5, "ink")
    for lado, y in (("-y", -0.22 - E), ("+y", 0.22 + E)):
        m = fr((0, y, 0), lado)
        for k in range(14):
            x = -6.9 + k * 1.0
            p.add(decal([(x, 0.04), (x + 0.45, 0.04), (x + 0.75, 0.46), (x + 0.3, 0.46)], m, 0), "yellow")
        for x in (-3.6, 0.0, 3.6):
            p.add(decal(rrect(x, 6.4, 1.6, 0.7, 0.12, 2), m, 0.02), "ink")
            p.add(decal(rrect(x, 6.4, 1.4, 0.5, 0.1, 2), m, 0.03), "sky")
        poner(p, MALETA, m, "cream", 0.02, 0, 3.4, 1.6)
        poner(p, MALETA_RAYAS, m, "orange", 0.03, 0, 3.4, 1.6)
    for y in (-0.3, 0.3):
        caja(p, -0.7, 0.7, y - 0.06, y + 0.06, 0.9, 1.05, "metal")
    return p


def p_tobogan(n):
    p = Prop("Tobogan%d" % n, None, 3400)
    caja(p, -1.55, 1.55, 3.75, 4.1, 3.6, 7.5, "orange", 0.05)
    m = fr((0, 3.75 - E, 0), "-y")
    p.add(decal(rect(-1.2, 1.2, 4.4, 7.0), m, 0), "ink")
    for k in range(4):
        x0 = -1.2 + k * 0.6
        caja(p, x0 + 0.03, x0 + 0.57, 3.62, 3.68, 4.7, 7.0, "rubber")
    caja(p, -1.75, 1.75, 3.3, 4.1, 7.5, 7.85, "dteal", 0.05)
    p.add(cyl(0.78, 0.1, (0, 4.1, 8.75), (90, 0, 0), 20), "orange")
    p.add(cyl(0.64, 0.12, (0, 4.1, 8.75), (90, 0, 0), 20), "white")
    placa = fr((0, 4.1 - 0.12 - E, 0), "-y")
    digito(p, placa, n, 0, 8.75, 0.85, "ink", 0)
    arriba, abajo = Vector((0, 3.6, 4.5)), Vector((0, -1.4, 1.9))
    p.add(bar(arriba, abajo, 2.4, 0.3), "metal")
    eje = (abajo - arriba).normalized()
    normal = Vector((0, -eje.z, eje.y)) if eje.z < 0 else Vector((0, eje.z, -eje.y))
    if normal.z < 0:
        normal = -normal
    for x in (-1.3, 1.3):
        p.add(bar(arriba + Vector((x, 0, 0.35)), abajo + Vector((x, 0, 0.35)), 0.2, 0.7), "orange")
    for k in range(7):
        c = arriba + (abajo - arriba) * ((k + 0.5) / 7) + normal * 0.16
        p.add(bar(c - Vector((1.15, 0, 0)), c + Vector((1.15, 0, 0)), 0.12, 0.04, up=tuple(normal)), "dmetal")
    for yb, alto in ((1.6, 3.2), (-0.6, 2.2)):
        for x in (-0.95, 0.95):
            caja(p, x - 0.1, x + 0.1, yb - 0.1, yb + 0.1, 0, alto, "dmetal")
    caja(p, -1.4, 1.4, -4.0, -1.4, 1.0, 1.4, "metal", 0.03)
    for x in (-1.3, 1.3):
        caja(p, x - 0.1, x + 0.1, -4.0, -1.4, 1.35, 2.05, "orange")
    caja(p, -1.4, 1.4, -4.3, -4.0, 1.2, 2.3, "orange", 0.03)
    for x in (-1.2, 1.2):
        for yb in (-1.6, -3.8):
            caja(p, x - 0.09, x + 0.09, yb - 0.09, yb + 0.09, 0, 1.0, "dmetal")
    suelo = fr((0, 0, E), "+z")
    p.add(decal(rrect(0, -5.6, 1.9, 1.9, 0.3, 2), suelo, 0), "ink")
    digito(p, suelo, n, 0, -5.6, 1.3, "yellow", E)
    return p


def p_surtidor():
    p = Prop("Surtidor", None, 3600)
    caja(p, -1.1, 1.1, -1.3, 1.3, 0, 0.25, "dmetal", 0.04)
    caja(p, -1.0, 1.0, -1.2, 1.2, 0.25, 4.0, "red", 0.08)
    caja(p, -1.08, 1.08, -1.28, 1.28, 4.0, 4.35, "cream", 0.06)
    p.add(ellipsoid((0.22, 0.22, 0.22), Matrix.Translation((0, 0, 4.55)), 10, 6), "yellow")
    caja(p, -0.85, 0.85, -1.26, -1.2, 2.72, 3.98, "ink")
    m = fr((0, -1.2 - E, 0), "-y")
    p.add(decal(circ(0, 1.75, 0.62, 18), m, 0), "dred")
    poner(p, GOTA, m, "yellow", E, 0, 1.75, 0.85)
    p.add(decal(circ(0.0, 0.85, 0.3, 14), m, 0), "white")
    p.add(decal(pill(0.08, 0.92, 0.3, 0.04, math.radians(55), 2), m, E), "ink")
    p.add(decal(rect(-0.9, 0.9, 2.45, 2.6), m, 0), "yellow")
    caja(p, 1.0, 1.25, -0.75, -0.25, 2.2, 2.9, "ink")
    p.add(bar((1.13, -0.5, 2.3), (1.13, -0.95, 1.95), 0.16, 0.16), "dmetal")
    p.add(tube([(1.13, -0.5, 2.25), (1.35, -0.3, 1.2), (1.5, 0.1, 0.3), (1.35, 0.8, 0.18), (1.1, 1.35, 0.45)], lambda u: 0.09, 8, 4), "rubber")
    ring(p, (-1.12, 0, 2.2), 0.55, 0.06, 16, "metal", (0, 90, 0))
    p.add(bar((-1.12, -0.55, 2.2), (-1.12, 0.55, 2.2), 0.08, 0.08), "metal")
    p.add(bar((-1.12, 0, 1.65), (-1.12, 0, 2.75), 0.08, 0.08), "metal")
    p.add(cyl(0.07, 0.4, (-1.12, 0.5, 2.2), (0, -90, 0), 8), "red")
    p.add(cyl(0.2, 0.25, (0, 1.2, 0.6), (-90, 0, 0), 10), "dmetal")
    return p


def p_corral():
    p = Prop("CorralAnimales", None, 7000)
    rng = random.Random(5)
    for k in range(7):
        x = 5.25 - k * 1.75
        caja(p, x - 0.15, x + 0.15, -8.5, -8.2, 0, 2.6, "dwood", 0.03)
    for z in (0.55, 1.35, 2.15):
        caja(p, -5.25, 5.25, -8.42, -8.28, z - 0.17, z + 0.17, "wood", 0.02)
        caja(p, 5.18, 5.32, -8.35, 8.35, z - 0.17, z + 0.17, "wood", 0.02)
    for k in range(9):
        y = -8.35 + k * 2.09
        caja(p, 5.1, 5.4, y - 0.15, y + 0.15, 0, 2.6, "dwood", 0.03)
    suelo = fr((0, 0, E), "+z")
    for cx, cy, r in ((1.0, -4.5, 2.6), (-1.5, 1.0, 3.0), (2.2, 5.6, 2.4), (-3.2, -6.2, 1.8), (-2.8, 6.4, 2.2)):
        pts = [(cx + r * (0.8 + 0.3 * rng.random()) * math.cos(a), cy + r * (0.8 + 0.3 * rng.random()) * math.sin(a))
               for a in [2 * math.pi * k / 12 for k in range(12)]]
        p.add(decal(pts, suelo, 0), "straw")
        for _ in range(9):
            a = rng.uniform(0, math.pi)
            px, py = cx + rng.uniform(-r, r) * 0.6, cy + rng.uniform(-r, r) * 0.6
            p.add(decal(pill(px, py, 0.5, 0.025, a, 1), suelo, E), "dstraw")
    for bx, by, pila in ((-3.65, 6.75, True), (4.15, 6.95, False)):
        caja(p, bx - 0.8, bx + 0.8, by - 0.5, by + 0.5, 0, 0.9, "straw", 0.08)
        for dx in (-0.4, 0.4):
            caja(p, bx + dx - 0.05, bx + dx + 0.05, by - 0.52, by + 0.52, 0, 0.92, "dstraw")
        if pila:
            caja(p, bx - 0.75, bx + 0.85, by - 0.45, by + 0.55, 0.9, 1.8, "straw", 0.08)
    caja(p, -4.75, -3.55, -6.45, -3.45, 0, 0.9, "steel", 0.05)
    caja(p, -4.6, -3.7, -6.3, -3.6, 0.78, 0.82, "blue")
    ring(p, (2.75, 4.95, 0.3), 1.75, 0.3, 24, "hpink")
    ring(p, (2.75, 4.95, 0.62), 1.7, 0.22, 24, "pink")
    p.add(cyl(1.6, 0.05, (2.75, 4.95, 0.28), seg=24), "lblue")
    p.add(ellipsoid((0.22, 0.28, 0.17), Matrix.Translation((2.3, 4.6, 0.45)), 10, 6), "yellow")
    p.add(ellipsoid((0.14, 0.14, 0.14), Matrix.Translation((2.3, 4.38, 0.66)), 8, 6), "yellow")
    p.add(ellipsoid((0.07, 0.06, 0.03), Matrix.Translation((2.3, 4.24, 0.64)), 6, 4), "orange")
    p.add(lathe([(0.0, 0.0), (0.42, 0.0), (0.5, 0.22), (0.44, 0.24), (0.36, 0.08), (0.0, 0.08)], 14, M((-2.6, -6.9, 0))), "red")
    p.add(ellipsoid((0.3, 0.12, 0.08), Matrix.Translation((-2.6, -6.9, 0.18)), 8, 4), "fish")
    p.add(prism([(-2.25, -6.9), (-2.05, -6.75), (-2.05, -7.05)], 0.04, M((0, 0, 0.18))), "fish")
    return p


def p_cubo():
    p = Prop("CuboMerienda", None, 1600)
    p.add(lathe([(0.0, 0.0), (0.52, 0.0), (0.66, 1.1), (0.6, 1.1), (0.47, 0.08), (0.0, 0.08)], 16), "teal")
    ring(p, (0, 0, 1.1), 0.64, 0.05, 16, "dteal")
    p.add(tube([(-0.62, 0, 1.05), (-0.45, 0, 1.5), (0, 0, 1.68), (0.45, 0, 1.5), (0.62, 0, 1.05)], lambda u: 0.025, 6, 3), "metal")
    p.add(cyl(0.6, 0.02, (0, 0, 0.95), seg=16), "blue")
    for x, y, a in ((-0.25, 0.15, 25), (0.2, -0.2, -20), (0.3, 0.25, 60)):
        mm = Matrix.Translation((x, y, 1.05)) @ Matrix.Rotation(math.radians(a), 4, "Z") @ Matrix.Rotation(math.radians(70), 4, "Y")
        p.add(ellipsoid((0.32, 0.11, 0.08), mm, 8, 5), "fish")
        p.add(prism([(0.3, 0.0), (0.5, 0.14), (0.5, -0.14)], 0.03, mm), "fish")
    for z, r, h, rol in ((1.02, 0.3, 0.12, "bun"), (1.14, 0.3, 0.07, "patty"), (1.21, 0.32, 0.03, "green"), (1.24, 0.31, 0.03, "cheese")):
        p.add(cyl(r, h, (-0.05, -0.05, z), seg=14), rol)
    p.add(ellipsoid((0.3, 0.3, 0.14), Matrix.Translation((-0.05, -0.05, 1.28)), 12, 6), "bun")
    return p


def p_pila_cajas():
    p = Prop("PilaCajas", None, 3000)

    def caja_madera(cx, cy, z0, l, a=0.0):
        mm = Matrix.Translation((cx, cy, z0)) @ Matrix.Rotation(math.radians(a), 4, "Z")
        h = l / 2
        p.add(bb(-h, h, -h, h, 0, l, 0.03, 2, mm), "wood")
        for sx in (-1, 1):
            for sy in (-1, 1):
                p.add(bb(sx * h - 0.12 - 0.01 * sx, sx * h + 0.12 - 0.01 * sx, sy * h - 0.12, sy * h + 0.12, 0, l, 0, 1, mm), "dwood")
        for z in (0.0, l - 0.22):
            p.add(bb(-h - 0.02, h + 0.02, -h - 0.02, h + 0.02, z, z + 0.22, 0, 1, mm), "dwood")
        frente = mm @ fr((0, -h - E, 0), "-y")
        p.add(decal([(-h + 0.2, 0.3), (-h + 0.45, 0.22), (h - 0.2, l - 0.3), (h - 0.45, l - 0.22)], frente, 0), "dwood")

    caja_madera(-1.05, -0.95, 0, 2.1)
    caja_madera(1.1, -0.85, 0, 2.0, 6)
    caja_madera(0.1, 1.1, 0, 2.1, -4)
    caja_madera(-0.1, -0.1, 2.1, 2.0, 18)
    mm = Matrix.Translation((-0.05, -0.15, 4.1)) @ Matrix.Rotation(math.radians(-25), 4, "Z")
    p.add(bb(-0.75, 0.75, -0.32, 0.32, 0, 0.58, 0.06, 2, mm), "orange")
    p.add(bb(-0.25, 0.25, -0.05, 0.05, 0.58, 0.72, 0, 1, mm), "ink")
    etiqueta = fr((-1.05, -0.95 - 1.05 - 2 * E, 0), "-y")
    p.add(decal(rect(-0.45, 0.45, 0.9, 1.6), etiqueta, 0), "white")
    p.add(decal([(-0.2, 1.45), (0.2, 1.45), (0.05, 1.18), (0.05, 1.0), (0.15, 0.98), (-0.15, 0.98), (-0.05, 1.0), (-0.05, 1.18)], etiqueta, E), "red")
    return p


def p_lampara():
    p = Prop("LamparaNave", None, 900)
    p.add(cyl(0.04, 3.4, (0, 0, 1.55), seg=6), "ink")
    p.add(cyl(0.16, 0.15, (0, 0, 4.85), seg=10), "dmetal")
    p.add(lathe([(0.22, 1.6), (0.3, 1.42), (0.9, 0.6), (0.92, 0.5), (0.86, 0.5), (0.84, 0.58), (0.26, 1.38), (0.17, 1.52)], 18, closed=True), "dteal")
    p.add(cyl(0.18, 0.22, (0, 0, 1.38), seg=10), "dmetal")
    p.add(ellipsoid((0.26, 0.26, 0.3), Matrix.Translation((0, 0, 0.75)), 12, 8), "lamp")
    return p


def p_flecha():
    p = Prop("FlechaSuelo", None, 300)
    borde = [(0.0, -2.2), (1.6, -0.25), (0.78, -0.25), (0.78, 2.2), (-0.78, 2.2), (-0.78, -0.25), (-1.6, -0.25)]
    relleno = [(0.0, -1.85), (1.28, -0.42), (0.5, -0.42), (0.5, 1.95), (-0.5, 1.95), (-0.5, -0.42), (-1.28, -0.42)]
    p.add(prism(borde, 0.04, None, z0=0.0), "ink")
    p.add(prism(relleno, 0.04, None, z0=0.04), "yellow")
    p.add(decal([(-0.25, -1.45), (-0.05, -1.62), (-0.85, -0.62), (-1.0, -0.62)], fr((0, 0, 0.081), "+z"), 0), "white")
    return p


BUILDERS = [p_nave, p_persiana, lambda: p_tobogan(1), lambda: p_tobogan(2), lambda: p_tobogan(3), lambda: p_tobogan(4), p_surtidor,
            p_corral, p_cubo, p_pila_cajas, p_lampara, p_flecha, p_cartel_maletas, p_cartel_animales, p_cartel_combustible,
            p_cartel_salida]


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
    img = bpy.data.images.new("prep_palette", 128, 128, alpha=True)
    px = [0.0] * (128 * 128 * 4)
    for i, (_, hx_) in enumerate(PAL):
        r, g, b = hex_rgb(hx_)
        gx, gy = i % 8, i // 8
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * 128 + x) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "prep_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def arg(name, default=None):
    if name in ARGS:
        i = ARGS.index(name)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return default


S0 = 90.5
COLOCACION = [
    ("NaveCarga", 34.0, 90.0, 72.0, 0), ("PersianaNave", 34.0, S0, 52.65, 0), ("Surtidor", 48.3, S0, 57.0, 90),
    ("CorralAnimales", 44.75, S0, 83.65, 0), ("CuboMerienda", 38.2, S0, 73.4, 30), ("PilaCajas", 21.2, S0, 88.4, 12),
    ("PilaCajas", 21.0, S0, 54.6, -8), ("CartelMaletas", 18.45, S0 + 9.8, 68.5, -90), ("CartelAnimales", 44.6, S0 + 7.6, 91.55, 0),
    ("CartelCombustible", 49.55, S0 + 6.6, 57.0, 90), ("CartelSalida", 34.0, S0 + 11.0, 51.55, 0),
] + [("Tobogan%d" % (i + 1), 22.4, S0, z, -90) for i, z in enumerate((58.0, 65.0, 72.0, 79.0))] + \
    [("LamparaNave", x, 108.5 - 5.0, z, 0) for x, z in ((26.0, 62.0), (42.0, 62.0), (26.0, 82.0), (42.0, 82.0))] + \
    [("FlechaSuelo", 34.0 - 3 * k, 90.45, 46.0 - 4.5 * k, -30) for k in range(4)]


def construir(only=None, exportar=True):
    img = palette_image()
    mat = K["palette_material"](img)
    objs, manifest, centros = {}, [], {}
    ok = True
    for b in BUILDERS:
        p = b()
        if only and p.name not in only:
            continue
        mn, mx = limites(p)
        p.size = tuple(mx - mn)
        centros[p.name] = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
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
    return objs, centros


def montar(st, objs, centros):
    for nombre, X, Y, Z, g in COLOCACION:
        if nombre not in objs:
            continue
        base = Vector((-(X - NX), Z - NZ, Y - NB))
        rz = Matrix.Rotation(math.radians(g), 3, "Z")
        o = st.put(nombre, 0, 0, g)
        o.location = base + rz @ centros[nombre]
    st.box(hx(36.5), hx(31.5), hy(55.6), hy(64.4), 0.5, 3.0, K["mat_rgb"]("F27B2B"), 0.1)
    st.box(hx(36.5), hx(31.5), hy(67.4), hy(74.4), 0.5, 1.8, K["mat_rgb"]("34383F"), 0.05)
    st.box(hx(47.9), hx(44.9), hy(80.5), hy(87.5), 0.5, 3.1, K["mat_rgb"]("34383F"), 0.05)
    for z in (58.0, 65.0, 72.0, 79.0):
        st.box(hx(25.4), hx(24.2), hy(z - 0.4), hy(z + 0.4), 1.9, 3.1, K["mat_rgb"]("F27B2B"), 0.05)
    st.quad(-300, 300, -300, 300, -0.02, K["mat_rgb"]("8DC85C", 0.95))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    only = arg("--only")
    only = set(only.split(",")) if isinstance(only, str) else None
    objs, centros = construir(only, not arg("--no-export"))
    vistas = arg("--vistas")
    if not vistas:
        return
    scene = bpy.context.scene
    K["render_setup"](scene, int(arg("--threads", "8")))
    for o in objs.values():
        o.hide_render = True
    outdir = arg("--dir", os.path.join(OUT, "renders"))
    os.makedirs(outdir, exist_ok=True)
    if "1" in vistas.split(","):
        st = K["Stage"](objs)
        K["sheet_catalog"](st, [[n for n in r if n in objs] for r in
                                [["Tobogan1", "Tobogan2", "Tobogan3", "Tobogan4", "Surtidor", "CuboMerienda"],
                                 ["PersianaNave", "PilaCajas", "LamparaNave", "FlechaSuelo"],
                                 ["CartelMaletas", "CartelAnimales", "CartelCombustible", "CartelSalida"]]], 1.4)
        scene.render.filepath = os.path.join(outdir, "kit_preparacion.png")
        bpy.ops.render.render(write_still=True)
        st.clear()
    if "2" in vistas.split(",") or "3" in vistas.split(","):
        st = K["Stage"](objs)
        montar(st, objs, centros)
        if "2" in vistas.split(","):
            st.camera((hx(-6.0), hy(20.0), 26.0), (0, -2.0, 4.0), 30)
            scene.render.filepath = os.path.join(outdir, "nave_exterior.png")
            bpy.ops.render.render(write_still=True)
        if "3" in vistas.split(","):
            st.area((0, 0, 16.5), 24, 2500, 30)
            st.camera((hx(46.0), hy(88.0), 9.0), (hx(26.0), hy(62.0), 2.5), 18)
            scene.render.filepath = os.path.join(outdir, "nave_interior.png")
            bpy.ops.render.render(write_still=True)
        st.clear()


main()
