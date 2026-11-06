import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPAS = os.path.join(RAIZ, "arte", "pagina", "capas")
INTRO = os.path.join(RAIZ, "arte", "intro")
FOTOS = sys.argv[1] if len(sys.argv) > 1 else ""
SALIDA = os.path.join(RAIZ, "marketing", "miniaturas_clic")
W, H = 1920, 1080
NEGRO = (20, 16, 14, 255)
AMARILLO = (255, 217, 59, 255)
BLANCO = (255, 255, 255, 255)
ROJO = (235, 38, 38, 255)


def fuente(tam):
    base = os.path.join(os.environ["LOCALAPPDATA"], "Roblox", "Versions")
    for v in os.listdir(base):
        ruta = os.path.join(base, v, "content", "fonts", "LuckiestGuy-Regular.ttf")
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    raise SystemExit("falta la fuente")


def fondo(nombre, zoom=1.0, cx=0.5, cy=0.5, desenfoque=1.6):
    im = Image.open(os.path.join(FOTOS, nombre)).convert("RGB")
    k = max(W / im.width, H / im.height) * zoom
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x = int((im.width - W) * cx)
    y = int((im.height - H) * cy)
    im = im.crop((x, y, x + W, y + H))
    im = ImageEnhance.Color(im).enhance(1.4)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = ImageEnhance.Brightness(im).enhance(1.05)
    im = im.filter(ImageFilter.GaussianBlur(desenfoque))
    lienzo = im.convert("RGBA")
    vineta = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vineta).ellipse((-W * 0.2, -H * 0.25, W * 1.2, H * 1.25), fill=255)
    vineta = vineta.filter(ImageFilter.GaussianBlur(180))
    oscuro = Image.alpha_composite(lienzo, Image.new("RGBA", (W, H), (10, 6, 20, 150)))
    return Image.composite(lienzo, oscuro, vineta)


def rayos(lienzo, cx, cy, color=(255, 236, 120), alfa=70, n=18):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    r = 2600
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n
        d.polygon([(cx, cy), (cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1))], fill=color + (alfa,))
    mascara = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mascara).ellipse((cx - 900, cy - 900, cx + 900, cy + 900), fill=255)
    mascara = mascara.filter(ImageFilter.GaussianBlur(220))
    capa.putalpha(ImageChops.multiply(capa.getchannel("A"), mascara))
    lienzo.alpha_composite(capa)


def pegatina(nombre, alto, giro=0.0, espejo=False):
    im = Image.open(os.path.join(CAPAS, nombre)).convert("RGBA")
    caja = im.getchannel("A").getbbox()
    im = im.crop(caja)
    if espejo:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    k = alto / im.height
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    m = 40
    base = Image.new("RGBA", (im.width + 2 * m, im.height + 2 * m), (0, 0, 0, 0))
    base.alpha_composite(im, (m, m))
    a = base.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    blanco = a.filter(ImageFilter.MaxFilter(17))
    negro = blanco.filter(ImageFilter.MaxFilter(9))
    capa = Image.new("RGBA", base.size, (0, 0, 0, 0))
    capa.alpha_composite(Image.new("RGBA", base.size, NEGRO), (0, 0)) if False else None
    out = Image.new("RGBA", base.size, (0, 0, 0, 0))
    out.paste(Image.new("RGBA", base.size, NEGRO), (0, 0), negro)
    out.paste(Image.new("RGBA", base.size, BLANCO), (0, 0), blanco)
    out.alpha_composite(base)
    if giro:
        out = out.rotate(giro, resample=Image.BICUBIC, expand=True)
    return out


def poner(lienzo, im, x, y, sombra=True):
    if sombra:
        s = Image.new("RGBA", im.size, (0, 0, 0, 0))
        s.putalpha(im.getchannel("A").point(lambda v: int(v * 0.55)))
        s = s.filter(ImageFilter.GaussianBlur(18))
        lienzo.alpha_composite(s, (int(x + 16), int(y + 22)))
    lienzo.alpha_composite(im, (int(x), int(y)))


def texto(lienzo, lineas, x, y, tam, colores, giro=-4.0, ancla="izq"):
    f = fuente(tam)
    d0 = ImageDraw.Draw(lienzo)
    anchos = [d0.textlength(l, font=f) for l in lineas]
    ancho = int(max(anchos)) + 80
    alto = int(len(lineas) * tam * 1.02) + 80
    capa = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    for i, l in enumerate(lineas):
        px = (ancho - anchos[i]) / 2 if ancla == "centro" else (40 if ancla == "izq" else ancho - 40 - anchos[i])
        py = 30 + i * tam * 1.02
        d.text((px + 10, py + 14), l, font=f, fill=(0, 0, 0, 160), stroke_width=22, stroke_fill=(0, 0, 0, 160))
        d.text((px, py), l, font=f, fill=colores[i % len(colores)], stroke_width=22, stroke_fill=NEGRO)
    capa = capa.rotate(giro, resample=Image.BICUBIC, expand=True)
    px = x if ancla == "izq" else (x - capa.width if ancla == "der" else x - capa.width / 2)
    lienzo.alpha_composite(capa, (int(px), int(y)))


def circulo(lienzo, cx, cy, rx, ry, grosor=22):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    d.ellipse((cx - rx - 6, cy - ry - 6, cx + rx + 6, cy + ry + 6), outline=BLANCO, width=grosor + 12)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=ROJO, width=grosor)
    lienzo.alpha_composite(capa)


def flecha(lienzo, x0, y0, x1, y1, ancho=60):
    ang = math.atan2(y1 - y0, x1 - x0)
    largo = math.hypot(x1 - x0, y1 - y0)
    cabeza = ancho * 2.2

    def punto(t, n):
        return (x0 + math.cos(ang) * t - math.sin(ang) * n, y0 + math.sin(ang) * t + math.cos(ang) * n)

    pts = [punto(0, -ancho / 2), punto(largo - cabeza, -ancho / 2), punto(largo - cabeza, -ancho * 1.3), punto(largo, 0),
           punto(largo - cabeza, ancho * 1.3), punto(largo - cabeza, ancho / 2), punto(0, ancho / 2)]
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    d.polygon([(px + 12, py + 16) for px, py in pts], fill=(0, 0, 0, 120))
    d.line(pts + [pts[0]], fill=BLANCO, width=26, joint="curve")
    d.polygon(pts, fill=ROJO)
    d.line(pts + [pts[0]], fill=NEGRO, width=6, joint="curve")
    lienzo.alpha_composite(capa)


def logo(lienzo, cx, cy, ancho=360):
    over = Image.open(os.path.join(INTRO, "LogoOver.png")).convert("RGBA")
    booked = Image.open(os.path.join(INTRO, "LogoBooked.png")).convert("RGBA")
    for im, dy, w, g in ((over, -ancho * 0.09, ancho, -4), (booked, ancho * 0.13, ancho * 1.08, 3)):
        k = w / im.width
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS).rotate(g, resample=Image.BICUBIC, expand=True)
        poner(lienzo, im, cx - im.width / 2, cy + dy - im.height / 2)


def guardar(lienzo, nombre):
    os.makedirs(SALIDA, exist_ok=True)
    lienzo.convert("RGB").save(os.path.join(SALIDA, nombre), optimize=True)


def a_estrellado():
    l = fondo("isla_rec.png", 1.18, 0.62, 0.45)
    rayos(l, 560, 600)
    circulo(l, 1125, 585, 140, 120)
    flecha(l, 1720, 640, 1290, 600)
    p = pegatina("icono_personaje.png", 980, 6)
    poner(l, p, -40, H - p.height + 70)
    texto(l, ["DON'T", "CRASH!"], W - 60, 40, 190, [AMARILLO, BLANCO], -5, "der")
    logo(l, W - 260, H - 150, 330)
    guardar(l, "1_NoTeEstrelles.png")


def b_piano():
    l = fondo("bodega_limpia.png", 1.15, 0.35, 0.5)
    circulo(l, 920, 440, 290, 175)
    flecha(l, 1330, 150, 1150, 300)
    p = pegatina("portada_chicle.png", 860, -6, True)
    poner(l, p, W - p.width + 40, H - p.height + 60)
    texto(l, ["WHY IS THERE", "A PIANO?!"], 50, 40, 150, [BLANCO, AMARILLO], -4)
    logo(l, 230, H - 150, 330)
    guardar(l, "2_Piano.png")


def c_tripulacion():
    l = fondo("cabina_rec.png", 1.05, 0.5, 0.5, 2.4)
    rayos(l, W / 2, H, (255, 200, 90), 60)
    for nombre, x, alto, g, espejo in (("portada_lavanda.png", -30, 700, 8, False), ("portada_lima.png", 1340, 720, -6, True),
                                       ("portada_chicle.png", 940, 760, 4, False), ("portada_sol.png", 420, 820, -4, False)):
        p = pegatina(nombre, alto, g, espejo)
        poner(l, p, x, H - p.height + 80)
    texto(l, ["1 PLANE", "4 IDIOTS"], W / 2, 10, 170, [AMARILLO, BLANCO], -3, "centro")
    guardar(l, "3_Tripulacion.png")


def d_aterrizar():
    l = fondo("cabina_piloto_rec.png", 1.12, 0.5, 0.35)
    circulo(l, 930, 600, 150, 160)
    flecha(l, 1380, 760, 1110, 640)
    p = pegatina("portada_lavanda.png", 900, -5)
    poner(l, p, -60, H - p.height + 80)
    texto(l, ["LAND IT...", "IF YOU CAN"], W - 50, 30, 165, [BLANCO, AMARILLO], -4, "der")
    logo(l, W - 260, H - 150, 330)
    guardar(l, "4_Aterriza.png")


def e_hambre():
    l = fondo("cabina_rec.png", 1.25, 0.6, 0.55, 2.8)
    rayos(l, 1350, 560, (255, 230, 110), 80)
    p = pegatina("icono_alt_personaje.png", 1000, 4)
    poner(l, p, W - p.width + 60, H - p.height + 90)
    texto(l, ["FEED THE", "PASSENGERS", "...OR ELSE"], 50, 40, 150, [BLANCO, AMARILLO, ROJO], -4)
    logo(l, 230, H - 140, 300)
    guardar(l, "5_Comida.png")


if __name__ == "__main__":
    for f in (a_estrellado, b_piano, c_tripulacion, d_aterrizar, e_hambre):
        f()
        print("hecha", f.__name__)
