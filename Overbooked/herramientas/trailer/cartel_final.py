import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

INTRO = r"C:\Users\ZuruT\Documents\RoZur\Overbooked\arte\intro"
AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTES = os.path.join(AQUI, "fuentes")
W, H = 1080, 1920
TINTA = (42, 36, 32, 255)
CREMA = (255, 244, 224, 255)


def img(n, tinte=None):
    im = Image.open(os.path.join(INTRO, n)).convert("RGBA")
    if tinte:
        r, g, b, a = im.split()
        r = r.point(lambda v: v * tinte[0] // 255)
        g = g.point(lambda v: v * tinte[1] // 255)
        b = b.point(lambda v: v * tinte[2] // 255)
        im = Image.merge("RGBA", (r, g, b, a))
    return im


def texto(lienzo, s, y, tam, fuente="LuckiestGuy-Regular.ttf", relleno=CREMA, borde=TINTA, grosor=10):
    f = ImageFont.truetype(os.path.join(FUENTES, fuente), tam)
    d = ImageDraw.Draw(lienzo)
    w = d.textlength(s, font=f)
    d.text(((W - w) / 2, y), s, font=f, fill=relleno, stroke_width=grosor, stroke_fill=borde)


def pegar(lienzo, im, cx, cy, ancho, giro=0.0, sombra=True):
    k = ancho / im.width
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    if giro:
        im = im.rotate(giro, resample=Image.BICUBIC, expand=True)
    if sombra:
        s = Image.new("RGBA", im.size, (0, 0, 0, 0))
        s.putalpha(im.getchannel("A").point(lambda a: int(a * 0.35)))
        s = s.filter(ImageFilter.GaussianBlur(10))
        lienzo.alpha_composite(s, (int(cx - im.width / 2 + 10), int(cy - im.height / 2 + 16)))
    lienzo.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def main(salida, lema, llamada, extra):
    papel = img("Papel.png").resize((512, 512))
    lienzo = Image.new("RGBA", (W, H), CREMA)
    for x in range(0, W, 512):
        for y in range(0, H, 512):
            lienzo.alpha_composite(papel, (x, y))
    pegar(lienzo, img("Mancha.png", (31, 166, 160)), W / 2 + 40, 790, 940, -20, sombra=False)
    pegar(lienzo, img("Mancha.png", (242, 123, 43)), W / 2, 760, 900, 8, sombra=False)
    pegar(lienzo, img("LogoOver.png"), W / 2, 640, 900, -4)
    pegar(lienzo, img("LogoBooked.png"), W / 2, 880, 980, 3)
    pegar(lienzo, img("Avioneta.png"), 820, 420, 360, -12)
    pegar(lienzo, img("Cinta.png", (217, 68, 58)), W / 2, 1110, 1000, 0)
    texto(lienzo, lema, 1072, 54, "PermanentMarker-Regular.ttf", CREMA, (120, 24, 24, 255), 3)
    texto(lienzo, llamada, 1330, 92)
    texto(lienzo, extra, 1480, 60, "FredokaOne-Regular.ttf", CREMA, TINTA, 8)
    pegar(lienzo, img("Etiqueta.png"), 960, 960, 130, 18)
    lienzo.convert("RGB").save(salida)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if a else os.path.join(AQUI, "cartel_final.png"),
         a[1] if len(a) > 1 else "THE WORLD'S WORST AIRLINE",
         a[2] if len(a) > 2 else "PLAY FREE ON ROBLOX",
         a[3] if len(a) > 3 else "1-4 PLAYERS  ·  CO-OP CHAOS")
