import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTRO = os.path.join(RAIZ, "arte", "intro")
W, H = 1920, 1080
TINTA = (42, 36, 32, 255)
CREMA = (255, 244, 224, 255)
COLORES = {"naranja": (242, 123, 43), "turquesa": (31, 166, 160), "rojo": (217, 68, 58), "amarillo": (246, 196, 69)}


def fuente(nombre, tam):
    base = os.path.join(os.environ["LOCALAPPDATA"], "Roblox", "Versions")
    for v in os.listdir(base):
        ruta = os.path.join(base, v, "content", "fonts", nombre)
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    raise SystemExit("falta " + nombre)


def tintar(im, color):
    r, g, b, a = im.split()
    r = r.point(lambda v: v * color[0] // 255)
    g = g.point(lambda v: v * color[1] // 255)
    b = b.point(lambda v: v * color[2] // 255)
    return Image.merge("RGBA", (r, g, b, a))


def pegar(lienzo, im, cx, cy, ancho, giro=0.0):
    k = ancho / im.width
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    if giro:
        im = im.rotate(giro, resample=Image.BICUBIC, expand=True)
    sombra = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sombra.putalpha(im.getchannel("A").point(lambda a: int(a * 0.45)))
    sombra = sombra.filter(ImageFilter.GaussianBlur(12))
    lienzo.alpha_composite(sombra, (int(cx - im.width / 2 + 10), int(cy - im.height / 2 + 14)))
    lienzo.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def rotulo(lienzo, texto, x, y, tam, color, giro, ancla="izq", abajo=False):
    f = fuente("LuckiestGuy-Regular.ttf", tam)
    lineas = texto.split("\n")
    d = ImageDraw.Draw(lienzo)
    ancho = int(max(d.textlength(l, font=f) for l in lineas)) + 120
    alto = int(len(lineas) * tam * 1.08) + 70
    capa = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    dc.rounded_rectangle((18, 18, ancho - 6, alto - 6), 28, fill=(0, 0, 0, 90))
    dc.rounded_rectangle((6, 6, ancho - 18, alto - 18), 28, fill=COLORES[color] + (255,), outline=TINTA, width=8)
    for i, l in enumerate(lineas):
        w = dc.textlength(l, font=f)
        dc.text(((ancho - 12 - w) / 2, 26 + i * tam * 1.08), l, font=f, fill=CREMA, stroke_width=9, stroke_fill=TINTA)
    capa = capa.rotate(giro, resample=Image.BICUBIC, expand=True)
    px = x if ancla == "izq" else x - capa.width
    py = H - capa.height - 50 if abajo else y
    lienzo.alpha_composite(capa, (int(px), int(py)))


def miniatura(foto, salida, texto, color, giro, abajo=False, derecha=False, logo=True, viveza=1.12):
    im = Image.open(foto).convert("RGB")
    k = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
    im = ImageEnhance.Color(im).enhance(viveza)
    im = ImageEnhance.Contrast(im).enhance(1.04)
    lienzo = im.convert("RGBA")
    viñeta = Image.new("L", (W, H), 0)
    dv = ImageDraw.Draw(viñeta)
    dv.ellipse((-W * 0.25, -H * 0.3, W * 1.25, H * 1.3), fill=255)
    viñeta = viñeta.filter(ImageFilter.GaussianBlur(160))
    oscuro = Image.new("RGBA", (W, H), (20, 14, 30, 120))
    lienzo = Image.composite(lienzo, Image.alpha_composite(lienzo, oscuro), viñeta)
    y = H - 330 if abajo else 60
    x = W - 70 if derecha else 70
    rotulo(lienzo, texto, x, y, 104, color, giro, "der" if derecha else "izq", abajo)
    if logo:
        over = Image.open(os.path.join(INTRO, "LogoOver.png")).convert("RGBA")
        booked = Image.open(os.path.join(INTRO, "LogoBooked.png")).convert("RGBA")
        lx = 230 if derecha else W - 260
        ly = 100 if abajo else H - 170
        pegar(lienzo, over, lx, ly - 34, 380, -4)
        pegar(lienzo, booked, lx, ly + 52, 410, 3)
    lienzo.convert("RGB").save(salida, optimize=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    miniatura(a[0], a[1], a[2].replace("|", "\n"), a[3], float(a[4]), "abajo" in a[5:], "derecha" in a[5:], "sinlogo" not in a[5:])
