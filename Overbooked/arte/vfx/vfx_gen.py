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
    tam = tam if isinstance(tam, tuple) else (tam, tam)
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


def encoger(pts, c, k, dx=0.0, dy=0.0):
    return [(c[0] + (x - c[0]) * k + dx, c[1] + (y - c[1]) * k + dy) for x, y in pts]


def humo(cx, cy, r, n, semilla, aplanar, tinta=TINTA):
    forma = bulto(cx, cy, r, n, semilla, aplanar, 0.3)
    relleno([temblar(forma, r * 0.015, semilla + 3)], SOMBRA)
    relleno([temblar(encoger(forma, (cx, cy), 0.8, -r * 0.1, r * 0.1), r * 0.015, semilla + 4)], BLANCO)
    trazo(elipse(cx - r * 0.42, cy + r * 0.3, r * 0.16, r * 0.11, 16, -30), r * 0.07, BLANCO, cerrado=True, semilla=semilla + 7)
    trazo(forma, r * 0.12, tinta, cerrado=True, semilla=semilla, var=0.25)


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
    humo(128, 138, 96, 8, 41, 0.66, GRIS)
    for k, y in enumerate((52, 34)):
        trazo([(70 + k * 20, y), (186 - k * 20, y)], 9.0, GRIS, semilla=44 + k)


def llama(fase, semilla):
    o = [math.sin(fase + k * 1.9) for k in range(6)]
    fuera = suave([(128, 14), (178, 24), (208, 60), (214, 104), (202, 142), (190 + 10 * o[0], 188 + 8 * o[1]), (166, 146), (128 + 14 * o[2], 240 - 6 * o[3]), (92, 152),
                   (62 + 10 * o[4], 182 + 8 * o[5]), (50, 132), (46, 88), (60, 46), (88, 22)], True, 6)
    pieza(fuera, "FF8A2B", 10.0, semilla=semilla, desfase=(0, 0))
    dentro = suave([(128, 30), (160, 40), (176, 74), (170, 112), (150, 134 + 8 * o[1]), (128 + 10 * o[3], 176 + 6 * o[0]), (104, 136), (86, 106), (82, 70), (98, 40)], True, 6)
    pieza(dentro, "FFE36E", 6.0, tinta="E0602A", semilla=semilla + 1, desfase=(0, 0))
    relleno([temblar(elipse(128, 64, 22, 26, 24), 1.2, semilla + 2)], "FFF8D6")
    trazo([(176, 92), (184, 120)], 7.0, BLANCO, semilla=semilla + 3, var=0.2)


@sprite("Llama", 512)
def s_llama():
    for k in range(4):
        LIENZO["ox"], LIENZO["oy"] = (k % 2) * 256, (1 - k // 2) * 256
        llama(k * math.pi / 2, 51 + k * 7)
    LIENZO["ox"], LIENZO["oy"] = 0.0, 0.0


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
    pieza(pinchos(128, 128, 116, 11, 171, 0.64), "F2552B", 11.0, semilla=171, desfase=(0, 0))
    pieza(pinchos(128, 130, 84, 9, 172, 0.66), "FFB02E", 8.0, semilla=172, desfase=(0, 0))
    pieza(bulto(130, 132, 50, 6, 173, 1.0, 0.2), "FFF1A8", 6.0, semilla=174, desfase=(0, 0))
    trazo(elipse(112, 150, 16, 10, 16, -30), 6.0, BLANCO, cerrado=True, semilla=175)


@sprite("Hongo", 256)
def s_hongo():
    base = bulto(128, 40, 96, 7, 301, 0.26, 0.3)
    pieza(base, "C9BFB2", 8.0, semilla=301, desfase=(0, 0))
    tallo = suave([(104, 36), (112, 80), (106, 128), (150, 128), (144, 80), (152, 36)], True, 6)
    pieza(tallo, "F7CF7A", 8.0, semilla=302, desfase=(0, 0), rayas={"sep": 8, "ancho": 2.2, "color": "E0A848", "zona": lambda q: q[0] > 136})
    pieza(bulto(128, 112, 52, 6, 303, 0.3, 0.3), "FFB347", 7.0, semilla=303, desfase=(0, 0))
    copa = bulto(128, 178, 98, 9, 304, 0.6, 0.28)
    relleno([temblar(copa, 1.4, 305)], "E8762E")
    relleno([temblar(encoger(copa, (128, 178), 0.82, -8, 9), 1.4, 306)], "FFB347")
    relleno([temblar(bulto(104, 196, 26, 5, 307, 0.6, 0.25), 1.0, 308)], "FFE08A")
    trazo(copa, 9.0, TINTA, cerrado=True, semilla=304, var=0.25)


@sprite("Pinchos", 256)
def s_pinchos():
    pieza(pinchos(128, 128, 120, 13, 311, 0.7), BLANCO, 10.0, semilla=311, desfase=(0, 0), sombra=(7, -8, 0.45))
    trazo(pinchos(128, 128, 92, 13, 311, 0.7), 3.0, SOMBRA, cerrado=True, semilla=312, var=0.2)


@sprite("Nube", 256)
def s_nube():
    pieza(bulto(128, 132, 112, 8, 321, 0.72, 0.26), BLANCO, 10.0, semilla=321, desfase=(0, 0), sombra=(7, -8, 0.45))


@sprite("Espiral")
def s_espiral():
    pts = [(64 + (4 + 52 * t) * math.cos(t * 6 * math.pi), 64 + (4 + 52 * t) * math.sin(t * 6 * math.pi)) for t in [k / 120 for k in range(121)]]
    ribete(pts, 9.0, TINTA, BLANCO, 331)


@sprite("Corazon")
def s_corazon():
    pts = [(64 + 3.4 * 16 * math.sin(t) ** 3, 58 + 3.4 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))) for t in [2 * math.pi * k / 96 for k in range(96)]]
    pieza(pts, "F2556B", 7.0, semilla=341, desfase=(0, 0), rayas={"sep": 8, "ancho": 2.0, "color": "C93A50", "zona": lambda q: q[0] > 74 and q[1] < 56})
    trazo(elipse(42, 82, 13, 9, 16, 40, 100, 230), 6.0, BLANCO, semilla=342)


@sprite("Vena")
def s_vena():
    for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        a = math.degrees(math.atan2(-sy, -sx))
        ribete(elipse(64 + sx * 42, 64 + sy * 42, 36, 36, 24, 0, a - 50, a + 50), 15.0, TINTA, "E8433A", 351 + k)


@sprite("Exclamacion")
def s_exclamacion():
    pieza(suave([(44, 120), (84, 120), (74, 46), (54, 46)], True, 4), BLANCO, 7.0, semilla=361, desfase=(0, 0))
    pieza(elipse(64, 20, 15, 15, 24), BLANCO, 7.0, semilla=362, desfase=(0, 0))


@sprite("Interrogacion")
def s_interrogacion():
    ribete(suave([(32, 90), (48, 114), (78, 116), (96, 96), (86, 72), (64, 60), (64, 44)], False, 8), 24.0, TINTA, BLANCO, 371)
    pieza(elipse(64, 18, 12, 12, 24), BLANCO, 6.0, semilla=372, desfase=(0, 0))


@sprite("Mancha", 256)
def s_mancha():
    pieza(bulto(128, 124, 80, 9, 381, 0.9, 0.36), BLANCO, 8.0, semilla=381, desfase=(0, 0), rayas={"sep": 9, "ancho": 2.2, "color": SOMBRA, "zona": lambda q: q[0] > 150 and q[1] < 110})
    rnd = random.Random(382)
    for k in range(7):
        a = 2 * math.pi * k / 7 + rnd.uniform(-0.3, 0.3)
        d = rnd.uniform(100, 116)
        r = rnd.uniform(7, 14)
        pieza(elipse(128 + d * math.cos(a), 124 + d * math.sin(a) * 0.9, r, r, 16), BLANCO, 5.0, semilla=383 + k, desfase=(0, 0))
    trazo(elipse(104, 146, 18, 11, 16, 20, 110, 220), 6.0, BLANCO, semilla=390)


@sprite("Brillito")
def s_brillito():
    pieza(estrella(64, 64, 60, 13, 4, 90), BLANCO, 6.0, semilla=391, desfase=(0, 0))
    puntos(64, 64, 6, BLANCO)


@sprite("Rayas")
def s_rayas():
    for k, (y, x0, x1) in enumerate(((30, 30, 120), (64, 8, 120), (98, 40, 120))):
        ribete([(x0, y), (x1, y)], 8.0, TINTA, BLANCO, 401 + k)


@sprite("Tampon", (512, 256))
def s_tampon():
    rnd = random.Random(411)
    for k, (caja, ancho) in enumerate(((rrect(18, 18, 494, 238, 26), 15.0), (rrect(40, 40, 472, 216, 14), 6.0))):
        q = remuestrear(caja, 3.0, True)
        i = 0
        while i < len(q) - 2:
            tramo_largo = rnd.randint(14, 40)
            tramo = q[i:i + tramo_largo + 1]
            if len(tramo) > 2:
                trazo(tramo, ancho * rnd.uniform(0.85, 1.1), BLANCO, semilla=412 + i + k * 1000, var=0.3, afilar=False)
            i += tramo_largo + rnd.choice((0, 0, 1, 2))


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
        escena(*tam)
        f()
        guardar(nombre)
    print("SPRITES", len(SPRITES))


main()
