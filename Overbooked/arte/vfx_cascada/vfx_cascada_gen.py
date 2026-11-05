import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.dirname(os.path.abspath(__file__))
TINTA = (27, 27, 33, 255)


def rgba(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def bandas_x(capa, y, grosor, color, w, rnd, huecos=3):
    d = ImageDraw.Draw(capa)
    x = rnd.uniform(0, w)
    for _ in range(huecos):
        largo = rnd.uniform(w * 0.25, w * 0.6)
        for desp in (-w, 0, w):
            d.rounded_rectangle((x + desp, y - grosor / 2, x + desp + largo, y + grosor / 2), radius=grosor / 2, fill=color)
        x += largo + rnd.uniform(w * 0.05, w * 0.2)


def agua():
    w, h = 512, 256
    rnd = random.Random(11)
    base = rgba(w, h)
    px = base.load()
    for y in range(h):
        v = abs(y / (h - 1) * 2 - 1)
        borde = max(0.0, min(1.0, (1 - v) / 0.14))
        for x in range(w):
            ola = 0.5 + 0.5 * math.sin(x / w * 2 * math.pi * 3 + y * 0.09)
            r, g, b = 70 + int(40 * ola), 190 + int(30 * ola), 225 + int(20 * ola)
            px[x, y] = (r, g, b, int(185 * borde))
    oscuras = rgba(w, h)
    for _ in range(14):
        bandas_x(oscuras, rnd.uniform(h * 0.1, h * 0.9), rnd.uniform(4, 10), (30, 130, 185, 150), w, rnd, 2)
    claras = rgba(w, h)
    for _ in range(26):
        bandas_x(claras, rnd.uniform(h * 0.08, h * 0.92), rnd.uniform(2, 7), (235, 252, 255, 235), w, rnd, 3)
    claras = claras.filter(ImageFilter.GaussianBlur(0.8))
    img = Image.alpha_composite(Image.alpha_composite(base, oscuras.filter(ImageFilter.GaussianBlur(1.2))), claras)
    a = img.split()[3].load()
    for y in range(h):
        v = abs(y / (h - 1) * 2 - 1)
        borde = max(0.0, min(1.0, (1 - v) / 0.14))
        for x in range(w):
            a[x, y] = int(a[x, y] * borde)
    return img


def espuma():
    w, h = 512, 128
    rnd = random.Random(23)
    img = rgba(w, h)
    sombra = rgba(w, h)
    ds, d = ImageDraw.Draw(sombra), ImageDraw.Draw(img)
    for _ in range(70):
        x, y = rnd.uniform(0, w), rnd.uniform(h * 0.2, h * 0.8)
        r = rnd.uniform(6, 22) * (1 - abs(y / h * 2 - 1) * 0.6)
        for desp in (-w, 0, w):
            ds.ellipse((x + desp - r - 1, y - r + 2, x + desp + r + 1, y + r + 4), fill=(120, 200, 230, 200))
            d.ellipse((x + desp - r, y - r, x + desp + r, y + r), fill=(250, 254, 255, 245))
    img = Image.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(2)), img.filter(ImageFilter.GaussianBlur(0.6)))
    return img


def arcoiris():
    w, h = 512, 128
    cols = [(255, 80, 80), (255, 160, 60), (255, 230, 90), (110, 220, 110), (80, 170, 255), (160, 110, 240)]
    img = rgba(w, h)
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        f = t * len(cols) - 0.5
        i = max(0, min(len(cols) - 2, int(math.floor(f))))
        k = min(1.0, max(0.0, f - i))
        c = tuple(int(cols[i][j] * (1 - k) + cols[i + 1][j] * k) for j in range(3))
        borde = max(0.0, min(1.0, min(t, 1 - t) / 0.12))
        for x in range(w):
            px[x, y] = (*c, int(215 * borde))
    return img


def rayo():
    w, h = 512, 128
    img = rgba(w, h)
    px = img.load()
    for y in range(h):
        g = math.exp(-((y / (h - 1) * 2 - 1) ** 2) / 0.18)
        for x in range(w):
            f = (1 - x / (w - 1)) ** 0.7 * min(1.0, x / (w * 0.08))
            px[x, y] = (255, 246, 214, int(255 * g * f))
    return img


def niebla():
    s = 256
    rnd = random.Random(31)
    img = rgba(s, s)
    d = ImageDraw.Draw(img)
    for _ in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(30, 52)
        cx, cy = s / 2 + math.cos(a) * rnd.uniform(10, 50), s / 2 + math.sin(a) * rnd.uniform(5, 35)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 255))
    d.ellipse((s / 2 - 62, s / 2 - 50, s / 2 + 62, s / 2 + 50), fill=(255, 255, 255, 255))
    img = img.filter(ImageFilter.GaussianBlur(9))
    px = img.load()
    for y in range(s):
        sombra = max(0.0, (y - s * 0.45) / (s * 0.5))
        for x in range(s):
            r, g, b, a = px[x, y]
            px[x, y] = (int(255 - 40 * sombra), int(255 - 18 * sombra), 255, int(a * 0.85))
    return img


def pez():
    s = 128
    big = 4
    img = rgba(s * big, s * big)
    d = ImageDraw.Draw(img)
    S = big

    def E(box, fill, out=TINTA, ancho=7):
        d.ellipse([v * S for v in box], fill=fill, outline=out, width=ancho * S // 2)

    def P(pts, fill, ancho=7):
        d.polygon([(x * S, y * S) for x, y in pts], fill=fill, outline=TINTA, width=ancho * S // 2)
    P([(30, 64), (6, 40), (12, 64), (6, 90)], (255, 140, 40, 255))
    P([(62, 40), (78, 22), (88, 44)], (255, 120, 30, 255))
    E((22, 36, 112, 92), (255, 160, 50, 255))
    d.chord([v * S for v in (30, 56, 106, 92)], 0, 180, fill=(255, 236, 190, 255))
    for x in (54, 70):
        d.arc([v * S for v in (x - 6, 40, x + 6, 88)], 290, 70, fill=(230, 110, 30, 255), width=3 * S)
    E((84, 48, 100, 64), (255, 255, 255, 255), ancho=4)
    E((90, 53, 97, 60), TINTA, ancho=1)
    d.arc([v * S for v in (96, 66, 108, 76)], 180, 300, fill=TINTA, width=3 * S)
    return img.resize((s, s), Image.LANCZOS)


def main():
    for nombre, f in (("AguaCascada", agua), ("EspumaCascada", espuma), ("Arcoiris", arcoiris), ("RayoLuz", rayo),
                      ("NieblaCascada", niebla), ("PezSalto", pez)):
        f().save(os.path.join(OUT, nombre + ".png"))
        print(nombre)


main()
