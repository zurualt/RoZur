import math
import os

from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "caras")
SS = 4
W, H = 512, 256
CX, CY = 256, 118
K = 1.2
GROSOR = 1.45
TINTA = (46, 28, 30, 255)
BOCA = (110, 24, 36, 255)
LENGUA = (236, 96, 108, 255)
LENGUA_RAYA = (190, 60, 76, 255)
DIENTE = (252, 250, 242, 255)
CAMPANILLA = (214, 70, 84, 255)
BABA = (168, 220, 246, 255)
RUBOR = (246, 118, 128, 120)
MIGA = (176, 120, 60, 255)


def lienzo(w=W, h=H):
    return Image.new("RGBA", (w * SS, h * SS), TINTA[:3] + (0,))


def p(x, y):
    return ((CX + x * K) * SS, (CY + y * K) * SS)


def muestras(f, a, b, n=48):
    return [f(a + (b - a) * i / n) for i in range(n + 1)]


def trazo(img, pts, ancho, color=TINTA):
    d = ImageDraw.Draw(img)
    q = [p(x, y) for x, y in pts]
    d.line(q, fill=color, width=int(ancho * GROSOR * SS), joint="curve")
    r = ancho * GROSOR * SS / 2
    for x, y in (q[0], q[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=color)


def poligono(img, pts, relleno, ancho=0.0, borde=TINTA):
    d = ImageDraw.Draw(img)
    q = [p(x, y) for x, y in pts]
    d.polygon(q, fill=relleno)
    if ancho > 0:
        d.line(q + [q[0]], fill=borde, width=int(ancho * GROSOR * SS), joint="curve")
        r = ancho * GROSOR * SS / 2
        for x, y in q:
            d.ellipse((x - r, y - r, x + r, y + r), fill=borde)


def elipse(cx, cy, rx, ry, n=64):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def recortado(img, contorno, dibujar):
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dibujar(capa)
    mascara = Image.new("L", img.size, 0)
    ImageDraw.Draw(mascara).polygon([p(x, y) for x, y in contorno], fill=255)
    img.paste(capa, (0, 0), Image.composite(capa, Image.new("RGBA", img.size, (0, 0, 0, 0)), mascara).split()[3])


def rubor(img, dy=-34):
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for sx in (-1, 1):
        poligono(capa, elipse(sx * 178, dy, 34, 20), RUBOR)
    img.alpha_composite(capa)


def sonrisa_d(w, alto, arriba=-30, curva=14):
    top = muestras(lambda x: (x, arriba + curva * (1 - (x / w) ** 2)), -w, w)
    bot = muestras(lambda x: (x, arriba + alto * math.sqrt(max(0.0, 1 - (x / w) ** 2))), w, -w)
    return top + bot


def boca_abierta(img, contorno, techo, dientes, lengua):
    poligono(img, contorno, BOCA)

    def interior(c):
        if dientes:
            poligono(c, [(x, y) for x, y in techo] + [(x, y + dientes) for x, y in reversed(techo)], DIENTE)
        if lengua:
            poligono(c, elipse(*lengua), LENGUA)
    recortado(img, contorno, interior)
    poligono(img, contorno, None, 12)


def contento(img):
    trazo(img, muestras(lambda x: (x, 22 - 30 * (x / 80) ** 2), -80, 80), 13)
    for sx in (-1, 1):
        trazo(img, [(sx * 80, -8), (sx * 90, -14), (sx * 94, -24)], 9)


def sonrisa(img):
    w = 112
    c = sonrisa_d(w, 112, -32, 14)
    techo = muestras(lambda x: (x, -32 + 14 * (1 - (x / w) ** 2)), -w, w)
    boca_abierta(img, c, techo, 26, (0, 62, 56, 32))
    trazo(img, [(0, -18), (0, 0)], 5)
    rubor(img)


def abierta(img):
    w = 74
    c = sonrisa_d(w, 70, -16, 8)
    techo = muestras(lambda x: (x, -16 + 8 * (1 - (x / w) ** 2)), -w, w)
    boca_abierta(img, c, techo, 16, (0, 44, 36, 20))


def neutra(img):
    trazo(img, muestras(lambda x: (x, 6 + 5 * math.sin(x / 58 * math.pi * 1.4)), -58, 58), 12)


def puchero(img):
    trazo(img, muestras(lambda x: (x, -2 + 28 * (x / 72) ** 2 - 4 * math.cos(x / 72 * math.pi)), -72, 72), 13)


def enfado(img):
    w = 118

    def t(x):
        return -30 + 16 * (x / w) ** 2

    def b(x):
        return 36 + 8 * (x / w) ** 2
    c = muestras(lambda x: (x, t(x)), -w, w) + muestras(lambda x: (x, b(x)), w, -w)
    poligono(img, c, DIENTE)
    trazo(img, muestras(lambda x: (x, (t(x) + b(x)) / 2 + 3 * math.sin(x / 9)), -w + 4, w - 4), 7)
    for x in (-78, -39, 0, 39, 78):
        trazo(img, [(x, t(x) + 2), (x, b(x) - 2)], 6)
    poligono(img, c, None, 13)


def grito(img):
    contorno = [(x, y + 8) for x, y in elipse(0, 0, 70, 90)]
    poligono(img, contorno, BOCA)

    def interior(c):
        poligono(c, [(-80, -100), (80, -100), (80, -60), (-80, -60)], DIENTE)
        trazo(c, [(0, -60), (0, -44)], 12, CAMPANILLA)
        poligono(c, elipse(0, -38, 11, 13), CAMPANILLA)
        poligono(c, elipse(0, 84, 50, 30), LENGUA)
    recortado(img, contorno, interior)
    poligono(img, contorno, None, 13)


def bleh(img):
    contorno = [(x, y - 14) for x, y in elipse(0, 0, 100, 62)]
    boca_abierta(img, contorno, [(-110, -80), (110, -80)], 0, None)
    lengua = [(-32, 20), (-32, 66)] + muestras(lambda a: (-32 * math.cos(a), 66 + 32 * math.sin(a)), 0, math.pi, 24) + [(32, 66), (32, 20)]
    poligono(img, lengua, LENGUA, 9)
    trazo(img, [(0, 30), (0, 70)], 5, LENGUA_RAYA)


def mareo(img):
    trazo(img, muestras(lambda x: (x, 8 + 11 * math.sin(x / 92 * math.pi * 3)), -92, 92, 96), 12)
    for sx in (-1, 1):
        trazo(img, [(sx * 120, -20), (sx * 132, -6), (sx * 120, 8)], 7)


def lengua(img):
    poligono(img, [(-24, 14), (-24, 50)] + muestras(lambda a: (-24 * math.cos(a), 50 + 24 * math.sin(a)), 0, math.pi, 20) + [(24, 50), (24, 14)], LENGUA, 9)
    trazo(img, [(0, 22), (0, 52)], 5, LENGUA_RAYA)
    trazo(img, muestras(lambda x: (x, 20 - 26 * (x / 78) ** 2), -78, 78), 13)


def dormido(img):
    poligono(img, elipse(6, 10, 22, 18), BOCA, 10)
    gota = [(40, 20)] + muestras(lambda a: (40 + 12 * math.cos(a), 56 + 12 * math.sin(a)), math.pi + 0.4, -0.4, 24)
    poligono(img, gota, BABA, 6)


def ooh(img):
    contorno = elipse(0, 8, 34, 44)
    poligono(img, contorno, BOCA)
    recortado(img, contorno, lambda c: poligono(c, elipse(0, 50, 26, 16), LENGUA))
    poligono(img, contorno, None, 12)


def masticar(img):
    trazo(img, muestras(lambda x: (x, 10 - 12 * abs(math.sin(x / 44 * math.pi))), -66, 66, 64), 12)
    for x, y, r in ((92, 22, 7), (104, 38, 5), (84, 46, 4)):
        poligono(img, elipse(x, y, r, r, 16), MIGA)


def zeta(img):
    pts = [(16, 14), (112, 14), (112, 40), (56, 90), (112, 90), (112, 116), (16, 116), (16, 90), (72, 40), (16, 40)]
    d = ImageDraw.Draw(img)
    q = [(x * SS, y * SS) for x, y in pts]
    d.polygon(q, fill=(255, 255, 255, 255))
    d.line(q + [q[0]], fill=TINTA, width=9 * SS, joint="curve")


def huella(img):
    d = ImageDraw.Draw(img)
    rojo = (214, 40, 46, 200)
    d.ellipse((70 * SS, 112 * SS, 186 * SS, 236 * SS), fill=rojo)
    for cx, cy, ang, largo in ((80, 120, -0.55, 70), (106, 100, -0.18, 92), (134, 96, 0.08, 98), (160, 104, 0.32, 86), (190, 168, 1.05, 64)):
        x2, y2 = cx + math.sin(ang) * largo * 0.2, cy - math.cos(ang) * largo
        d.line((cx * SS, cy * SS, x2 * SS, y2 * SS), fill=rojo, width=26 * SS)
        r = 13 * SS
        d.ellipse((x2 * SS - r, y2 * SS - r, x2 * SS + r, y2 * SS + r), fill=rojo)


BOCAS = {
    "BocaContento": contento,
    "BocaSonrisa": sonrisa,
    "BocaAbierta": abierta,
    "BocaNeutra": neutra,
    "BocaPuchero": puchero,
    "BocaEnfado": enfado,
    "BocaGrito": grito,
    "BocaBleh": bleh,
    "BocaMareo": mareo,
    "BocaLengua": lengua,
    "BocaDormido": dormido,
    "BocaOoh": ooh,
    "BocaMasticar": masticar,
}


def guardar(img, nombre, w, h):
    img = img.resize((w, h), Image.LANCZOS)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                px[x, y] = TINTA[:3] + (0,)
    img.save(os.path.join(OUT, nombre + ".png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    for nombre, f in BOCAS.items():
        img = lienzo()
        f(img)
        guardar(img, nombre, W, H)
    img = Image.new("RGBA", (128 * SS, 128 * SS), TINTA[:3] + (0,))
    zeta(img)
    guardar(img, "Zeta", 128, 128)
    img = Image.new("RGBA", (256 * SS, 256 * SS), (214, 40, 46, 0))
    huella(img)
    img = img.resize((256, 256), Image.LANCZOS)
    img.save(os.path.join(OUT, "Huella.png"))
    hoja = Image.new("RGBA", (W * 4, H * 4), (240, 200, 160, 255))
    for i, nombre in enumerate(BOCAS):
        b = Image.open(os.path.join(OUT, nombre + ".png"))
        hoja.alpha_composite(b, ((i % 4) * W, (i // 4) * H))
    hoja.save(os.path.join(os.path.dirname(OUT), "bocas_hoja.png"))
    print("BOCAS", len(BOCAS))


main()
