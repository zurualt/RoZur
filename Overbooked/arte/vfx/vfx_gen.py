import os
import math
import random

_AQUI = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(os.path.dirname(_AQUI), "interfaz", "interfaz_gen.py"), encoding="utf-8") as _fh:
    exec(_fh.read().split("\nPANELES = {}")[0], globals())
SALIDA = _AQUI

GRIS = "5F5A55"
GRIS_CLARO = "8A847E"
SOMBRA = "DCDCDC"

SPRITES = []


def sprite(nombre, tam=128):
    def deco(f):
        SPRITES.append((nombre, tam, f))
        return f
    return deco


def bulto(cx, cy, r, n, semilla, aplanar=1.0, hondo=0.2):
    fase = random.Random(semilla).uniform(0, math.pi)
    pts = []
    for k in range(144):
        a = 2 * math.pi * k / 144
        s = abs(math.sin(n * a / 2 + fase))
        rr = r * (1 - hondo + hondo * s ** 0.5) * (1 + 0.05 * math.sin(3 * a + semilla))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * aplanar))
    return pts


def girar(pts, ang, c=(64, 64)):
    a = math.radians(ang)
    return [(c[0] + (x - c[0]) * math.cos(a) - (y - c[1]) * math.sin(a), c[1] + (x - c[0]) * math.sin(a) + (y - c[1]) * math.cos(a)) for x, y in pts]


def ribete(pts, ancho, fondo, frente, semilla, cerrado=False):
    trazo(pts, ancho + 8, fondo, cerrado=cerrado, semilla=semilla, var=0.2, afilar=False)
    trazo(pts, ancho, frente, cerrado=cerrado, semilla=semilla + 1, var=0.15, amp=0.5, afilar=False)


def humo(cx, cy, r, n, semilla, aplanar, tinta=GRIS):
    forma = bulto(cx, cy, r, n, semilla, aplanar)
    pieza(forma, BLANCO, r * 0.09, tinta=tinta, semilla=semilla, desfase=(0, 0),
          rayas={"sep": r * 0.1, "ancho": r * 0.025, "color": SOMBRA, "zona": lambda q: (q[0] - cx) - (q[1] - cy) > r * 0.55})
    trazo(elipse(cx - r * 0.25, cy + r * 0.18, r * 0.32, r * 0.24, 16, 0, 100, 210), r * 0.05, SOMBRA, semilla=semilla + 7)


@sprite("Humo1", 256)
def s_humo1():
    humo(128, 128, 100, 7, 11, 0.92)


@sprite("Humo2", 256)
def s_humo2():
    humo(128, 124, 98, 6, 23, 0.84)


@sprite("Humo3", 256)
def s_humo3():
    humo(128, 130, 94, 5, 37, 0.96)


@sprite("Polvo", 256)
def s_polvo():
    humo(128, 138, 96, 8, 41, 0.66, GRIS_CLARO)
    for k, y in enumerate((52, 38)):
        trazo([(70 + k * 20, y), (186 - k * 20, y)], 6.0, GRIS_CLARO, semilla=44 + k)


@sprite("Llama")
def s_llama():
    fuera = suave([(64, 124), (84, 92), (100, 66), (100, 40), (86, 16), (64, 8), (42, 16), (28, 40), (30, 66), (44, 84), (52, 70), (58, 96)], True, 6)
    pieza(fuera, "FFAE3A", 6.0, semilla=51, desfase=(0, 0))
    dentro = suave([(64, 80), (78, 60), (82, 38), (72, 22), (56, 22), (46, 36), (48, 54), (58, 62)], True, 6)
    pieza(dentro, "FFF1A8", 4.0, tinta="F08A2E", semilla=52, desfase=(0, 0))


@sprite("Chispa")
def s_chispa():
    relleno([estrella(64, 64, 60, 8, 4, 90)], BLANCO)
    relleno([estrella(64, 64, 34, 6, 4, 45)], BLANCO, 0.75)
    puntos(64, 64, 10, BLANCO)


@sprite("Estrella")
def s_estrella():
    pieza(estrella(64, 62, 56, 24), AMARILLO, 6.5, semilla=61, brillo=[(52, 84), (58, 98)])


@sprite("Gota")
def s_gota():
    gota = suave([(64, 120), (88, 80), (96, 56), (86, 26), (64, 16), (42, 26), (32, 56), (40, 80)], True, 6)
    pieza(gota, BLANCO, 6.0, semilla=71, desfase=(0, 0), rayas={"sep": 7, "ancho": 1.8, "color": "D5E1E7", "zona": lambda q: q[0] > 70 and q[1] < 60})
    trazo([(50, 46), (46, 60), (50, 74)], 5.0, "D5E1E7", semilla=72)


@sprite("Corona")
def s_corona():
    base = [(14, 34), (24, 22), (64, 16), (104, 22), (114, 34), (104, 44), (100, 82), (90, 50), (78, 96), (68, 54), (60, 104), (50, 54), (38, 90), (30, 48), (24, 76), (22, 44)]
    pieza(base, BLANCO, 5.0, semilla=81, desfase=(0, 0))
    for cx, cy, r in ((24, 92, 6), (40, 106, 5), (62, 118, 6), (82, 110, 5), (102, 96, 6)):
        pieza(elipse(cx, cy, r, r * 1.2, 16), BLANCO, 3.4, semilla=cx, desfase=(0, 0))


@sprite("Confeti")
def s_confeti():
    ribete(suave([(20, 40), (44, 66), (64, 52), (84, 80), (108, 70)], False, 8), 18.0, TINTA, BLANCO, 91)


@sprite("ConfetiPunto")
def s_confeti_punto():
    pieza(girar(rrect(30, 30, 98, 98, 14), 18), BLANCO, 6.0, semilla=95, desfase=(0, 0))


@sprite("Moneda")
def s_moneda():
    pieza(elipse(64, 64, 52, 52, 48), AMARILLO, 6.0, semilla=101, rayas={"sep": 8, "ancho": 1.8, "color": "D9A72E", "zona": lambda q: q[0] > 74 and q[1] < 54})
    trazo(elipse(64, 64, 36, 36, 40), 4.0, "C9952A", cerrado=True, semilla=102)
    trazo([(64, 44), (64, 84)], 7.0, "C9952A", semilla=103, var=0.2)
    trazo(elipse(64, 64, 44, 44, 16, 0, 110, 160), 4.6, BLANCO, semilla=104)


@sprite("Hoja")
def s_hoja():
    hoja = suave([(16, 20), (40, 60), (70, 100), (110, 116), (104, 82), (78, 44), (44, 20)], True, 6)
    pieza(hoja, VERDE, 5.4, semilla=111)
    trazo(suave([(18, 22), (60, 64), (108, 114)], False, 6), 3.6, "3D9447", semilla=112)


@sprite("Pluma")
def s_pluma():
    pluma = suave([(64, 122), (82, 96), (86, 60), (76, 28), (64, 12), (52, 28), (42, 60), (46, 96)], True, 6)
    pieza(pluma, BLANCO, 5.0, semilla=121, desfase=(0, 0))
    trazo([(64, 124), (64, 8)], 3.4, TINTA, semilla=122)
    for k in range(5):
        y = 34 + k * 16
        trazo([(64, y), (80 - k, y + 10)], 2.4, SOMBRA, semilla=123 + k)
        trazo([(64, y), (48 + k, y + 10)], 2.4, SOMBRA, semilla=130 + k)


@sprite("Escombro")
def s_escombro():
    forma = [(26, 44), (66, 20), (106, 46), (98, 94), (56, 108), (22, 84)]
    pieza(forma, BLANCO, 6.0, semilla=141, desfase=(0, 0), rayas={"sep": 8, "ancho": 2.0, "color": SOMBRA, "zona": lambda q: q[0] > 70})
    trazo([(44, 70), (70, 56)], 3.6, GRIS, semilla=142)


@sprite("Astilla")
def s_astilla():
    forma = [(14, 50), (98, 70), (118, 64), (102, 54), (20, 38)]
    pieza(forma, "C99A5B", 5.0, semilla=151, desfase=(0, 0))
    trazo([(30, 46), (96, 62)], 2.6, "9A6B35", semilla=152)


@sprite("Cristal")
def s_cristal():
    forma = [(40, 18), (104, 54), (62, 112), (26, 70)]
    pieza(forma, "BFE6F5", 5.0, semilla=161, desfase=(0, 0))
    trazo([(44, 34), (36, 64)], 5.0, BLANCO, semilla=162)
    trazo([(54, 32), (86, 52)], 2.6, "8FC6DC", semilla=163)


def pinchos(cx, cy, r, n, semilla, hondo):
    rnd = random.Random(semilla)
    pts = []
    for k in range(n * 2):
        a = 2 * math.pi * k / (n * 2) + rnd.uniform(-0.08, 0.08)
        rr = r * (rnd.uniform(0.92, 1.0) if k % 2 == 0 else hondo * rnd.uniform(0.9, 1.08))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


@sprite("Explosion", 256)
def s_explosion():
    pieza(pinchos(128, 128, 118, 11, 171, 0.66), NARANJA, 10.0, semilla=171, desfase=(0, 0))
    pieza(pinchos(128, 130, 84, 9, 172, 0.68), AMARILLO, 7.0, tinta="E0702A", semilla=172, desfase=(0, 0))
    relleno([temblar(bulto(130, 132, 46, 6, 173, 1.0, 0.15), 1.2, 174)], "FFF4C2")


@sprite("Destello", 256)
def s_destello():
    relleno([pinchos(128, 128, 124, 8, 181, 0.22)], BLANCO, 0.9)
    relleno([elipse(128, 128, 46, 46, 40)], BLANCO)


@sprite("Brillo")
def s_brillo():
    for k in range(10):
        relleno([elipse(64, 64, 62 - k * 6, 62 - k * 6, 48)], BLANCO, 0.1 + k * 0.012)


@sprite("Onda", 256)
def s_onda():
    trazo(elipse(128, 128, 104, 104, 64), 16.0, BLANCO, cerrado=True, semilla=191, var=0.3)
    trazo(elipse(128, 128, 84, 84, 64), 5.0, BLANCO, cerrado=True, semilla=192, var=0.4, a=0.6)


@sprite("Vapor")
def s_vapor():
    ribete(suave([(64, 10), (44, 34), (76, 62), (48, 92), (66, 120)], False, 8), 14.0, "C6C6C6", BLANCO, 201)


@sprite("Linea")
def s_linea():
    trazo([(64, 8), (64, 120)], 12.0, BLANCO, semilla=211, var=0.15)


def main():
    solo = set(ARGS[ARGS.index("--solo") + 1].split(",")) if "--solo" in ARGS else None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for nombre, tam, f in SPRITES:
        if solo and nombre not in solo:
            continue
        escena(tam, tam)
        f()
        guardar(nombre)
    print("SPRITES", len(SPRITES))


main()
