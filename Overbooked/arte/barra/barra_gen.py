import math
import os

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTE = os.path.join(os.environ["LOCALAPPDATA"], "Roblox", "Versions")
G = 512
B = (255, 255, 255, 255)
N = (0, 0, 0, 0)


def fuente(tam):
    for v in os.listdir(FUENTE):
        ruta = os.path.join(FUENTE, v, "content", "fonts", "FredokaOne-Regular.ttf")
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    raise SystemExit("falta FredokaOne")


def lienzo():
    im = Image.new("RGBA", (G, G), N)
    return im, ImageDraw.Draw(im)


def engranaje():
    im, d = lienzo()
    c, r1, r2, n = G / 2, 140, 222, 8
    pts = []
    for i in range(n * 4):
        a = 2 * math.pi * i / (n * 4) - math.pi / (n * 4) * 1.5
        r = r2 if i % 4 in (1, 2) else r1
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
    d.polygon(pts, fill=B)
    d.ellipse((c - 158, c - 158, c + 158, c + 158), fill=B)
    d.ellipse((c - 66, c - 66, c + 66, c + 66), fill=N)
    return im


def interrogacion():
    im, d = lienzo()
    d.ellipse((46, 46, G - 46, G - 46), outline=B, width=40)
    f = fuente(300)
    w = d.textlength("?", font=f)
    d.text(((G - w) / 2, 70), "?", font=f, fill=B)
    return im


def lista():
    im, d = lienzo()
    for k, y in enumerate((130, 256, 382)):
        d.rounded_rectangle((70, y - 42, 154, y + 42), 18, outline=B, width=22)
        if k < 2:
            d.line([(86, y - 2), (108, y + 22), (150, y - 34)], fill=B, width=24, joint="curve")
        d.rounded_rectangle((200, y - 20, 450, y + 20), 20, fill=B)
    return im


def nota(tachada):
    im, d = lienzo()
    d.ellipse((92, 330, 222, 432), fill=B)
    d.ellipse((290, 290, 420, 392), fill=B)
    d.rectangle((192, 120, 222, 382), fill=B)
    d.rectangle((390, 82, 420, 342), fill=B)
    d.polygon([(192, 120), (420, 82), (420, 152), (192, 190)], fill=B)
    if tachada:
        d.line([(70, 70), (442, 442)], fill=N, width=70)
        d.line([(80, 80), (432, 432)], fill=B, width=34)
    return im


def camara():
    im, d = lienzo()
    d.rounded_rectangle((56, 150, 352, 362), 46, fill=B)
    d.polygon([(372, 256), (456, 180), (456, 332)], fill=B)
    d.ellipse((104, 206, 164, 266), fill=N)
    return im


def aviso():
    im, d = lienzo()
    d.polygon([(256, 54), (470, 440), (42, 440)], fill=B)
    d.rounded_rectangle((232, 170, 280, 330), 24, fill=N)
    d.ellipse((230, 352, 282, 404), fill=N)
    return im


ICONOS = {
    "Ajustes": engranaje,
    "Ayuda": interrogacion,
    "Tareas": lista,
    "Musica": lambda: nota(False),
    "MusicaNo": lambda: nota(True),
    "Clip": camara,
    "Desastres": aviso,
}

if __name__ == "__main__":
    for nombre, f in ICONOS.items():
        f().resize((128, 128), Image.LANCZOS).save(os.path.join(AQUI, nombre + ".png"))
