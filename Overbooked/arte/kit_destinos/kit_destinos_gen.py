import bpy
import bmesh
import math
import os
import sys
import json
import random
import numpy as np
from mathutils import Vector, Matrix

OUT = os.path.dirname(os.path.abspath(__file__))
ARTE = os.path.dirname(OUT)
RAIZ = os.path.dirname(ARTE)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    if name in ARGS:
        i = ARGS.index(name)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return default


def cargar(rel):
    ruta = os.path.join(ARTE, rel)
    with open(ruta, encoding="utf-8") as fh:
        src = fh.read()
    src = src[:src.rstrip().rfind("\nmain()")]
    ns = {"__file__": ruta, "__name__": "generador"}
    exec(compile(src, ruta, "exec"), ns)
    ns["OUT"] = OUT
    return ns


I = cargar(os.path.join("kit_isla", "kit_isla_gen.py"))
C = cargar(os.path.join("kit_cielo", "kit_cielo_gen.py"))
_SEP = {}
with open(os.path.join(RAIZ, "herramientas", "separar_capas.py"), encoding="utf-8") as _fh:
    exec(compile(_fh.read(), "separar_capas.py", "exec"), _SEP)

PAL = [
    ("white", "F7F7F2"), ("black", "1B1B21"), ("cream", "FFF4E0"), ("red", "D9443A"), ("orange", "F27B2B"), ("yellow", "F6C445"), ("teal", "1FA6A0"), ("glass", "8FD3F4"),
    ("metal", "A9B0B8"), ("dmetal", "5C6370"), ("asphalt", "4A4F57"), ("asphalt2", "5B6069"), ("mark", "F2F2EA"), ("concrete", "C9C3B6"), ("wood", "C08A57"), ("dwood", "7A4A26"),
    ("jleaf", "3FA34D"), ("jleaf2", "2E8540"), ("jleaf3", "6CC24A"), ("jlime", "A3D65C"), ("jdark", "1F6634"), ("thatch", "E6C068"), ("thatch2", "C99A46"), ("dirt", "C77A45"),
    ("dirt2", "A9643A"), ("grass", "7CC653"), ("grass2", "6AB547"), ("trunk", "8A5A33"), ("flower", "E8457A"), ("jrock", "B3AA92"), ("palm", "4FAE3E"), ("palm2", "3B8F35"),
    ("snow", "F4F8FC"), ("snow2", "DCE8F3"), ("snow3", "BCD2EA"), ("ice", "A8DDF0"), ("pine", "2F6B4F"), ("pine2", "23543F"), ("rock", "8C93A3"), ("rock2", "667086"),
    ("roofred", "C8453A"), ("cabin", "A0603A"), ("carrot", "F28C28"), ("sand", "E9A15A"), ("sand2", "D9844A"), ("redrock", "C2552F"), ("redrock2", "A3432A"), ("redrock3", "E07B45"),
    ("tan", "F2C98B"), ("cactus", "5FA347"), ("cactus2", "468C3A"), ("dust", "E8C79A"), ("dust2", "DDB886"), ("bone", "F3EBD8"), ("rwy", "BCAA8E"), ("rwy2", "A08E74"),
    ("bldg1", "ECE6DA"), ("bldg2", "9DB4C8"), ("bldg3", "F2B880"), ("bldg4", "E39A9A"), ("bldg5", "B6D7A8"), ("roofg", "7B828C"), ("dglass", "4E7FA3"), ("purple", "9B6BD6"),
]
IDX = {n: i for i, (n, _) in enumerate(PAL)}
FILAS = 8


def suv(n):
    i = IDX[n]
    return ((i % 8 + 0.5) / 8.0, (i // 8 + 0.5) / FILAS)


I["suv"], I["IDX"], I["PAL"] = suv, IDX, PAL
hex_rgb, lin = C["hex_rgb"], C["lin"]
lathe, cyl, tube, catmull, ellipsoid, blob, M, xf, palo, fronda = (I[k] for k in ("lathe", "cyl", "tube", "catmull", "ellipsoid", "blob", "M", "xf", "palo", "fronda"))
Prop = I["Prop"]

BIOMAS = ["Jungla", "Nieve", "Desierto", "Ciudad"]
TECHO_LOSA = 0.15


def imagen_paleta():
    rgb = np.zeros((FILAS * 16, 128, 3), dtype=np.float32)
    for i, (_, hx) in enumerate(PAL):
        gx, gy = i % 8, i // 8
        rgb[gy * 16:gy * 16 + 16, gx * 16:gx * 16 + 16] = hex_rgb(hx)
    return C["guardar_imagen"]("destinos_paleta", rgb)


S = 2048
YY, XX = np.mgrid[0:S, 0:S].astype(np.float32) + 0.5


def col(h):
    return np.array(hex_rgb(h), dtype=np.float32)


def ventanas(cx, cy, r):
    for ox in (-S, 0, S):
        x = cx + ox
        if x + r < 0 or x - r > S:
            continue
        for oy in (-S, 0, S):
            y = cy + oy
            if y + r < 0 or y - r > S:
                continue
            yield int(max(y - r, 0)), int(min(y + r + 2, S)), int(max(x - r, 0)), int(min(x + r + 2, S)), x, y


def disco(img, cx, cy, r, c):
    for y0, y1, x0, x1, x, y in ventanas(cx, cy, r):
        m = (XX[y0:y1, x0:x1] - x) ** 2 + (YY[y0:y1, x0:x1] - y) ** 2 < r * r
        img[y0:y1, x0:x1][m] = c


def mancha(img, cx, cy, ax, ay, ang, c, wob=0.12, fase=0.0, k=1.0):
    ax, ay = ax * k, ay * k
    r = max(ax, ay) * (1 + 1.7 * wob) + 2
    ca, sa = math.cos(ang), math.sin(ang)
    for y0, y1, x0, x1, x, y in ventanas(cx, cy, r):
        dx = XX[y0:y1, x0:x1] - x
        dy = YY[y0:y1, x0:x1] - y
        u = (dx * ca + dy * sa) / ax
        v = (-dx * sa + dy * ca) / ay
        th = np.arctan2(v, u)
        q = np.sqrt(u * u + v * v) - wob * np.sin(3 * th + fase) - 0.6 * wob * np.sin(5 * th + 1.7 * fase)
        img[y0:y1, x0:x1][q < 1.0] = c


def rect(img, x0, x1, y0, y1, c):
    img[int(max(y0, 0)):int(min(y1, S)), int(max(x0, 0)):int(min(x1, S))] = c


def ruta(ctrl, paso):
    pts = catmull([Vector((x, y, 0.0)) for x, y in ctrl], 24)
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        acc += (b - a).length
        if acc >= paso:
            out.append(b)
            acc = 0.0
    return [(p.x, p.y) for p in out]


def trazo(img, pts, r, c):
    for x, y in pts:
        disco(img, x, y, r, c)


def ctrl_serpiente(rnd, x0, y0, x1, y1, n, amp):
    d = Vector((x1 - x0, y1 - y0))
    perp = Vector((-d.y, d.x)).normalized()
    out = []
    for i in range(n):
        t = i / (n - 1)
        off = 0.0 if i in (0, n - 1) else amp * rnd.uniform(-1, 1)
        out.append((x0 + d.x * t + perp.x * off, y0 + d.y * t + perp.y * off))
    return out


def ruido(seed, octavas):
    n = C["ruido_periodico"](S, np.random.default_rng(seed), octavas)
    return (n - n.mean()) / n.std()


def bajar(img):
    img = img.reshape(S // 2, 2, S // 2, 2, 3).mean(axis=(1, 3))
    return img[::-1]


def mezcla(a, b, t):
    return a + (b - a) * t[..., None]


def copas(img, rnd, n, r0, r1, tonos, sombra, luz=None, mascara=None, paso=None):
    if paso:
        gx, gy = np.meshgrid(np.arange(0, S, paso), np.arange(0, S, paso))
        xs = (gx.ravel() + rnd.uniform(-paso * 0.45, paso * 0.45, gx.size)) % S
        ys = (gy.ravel() + rnd.uniform(-paso * 0.45, paso * 0.45, gy.size)) % S
    else:
        xs, ys = rnd.uniform(0, S, n), rnd.uniform(0, S, n)
    if mascara is not None:
        dentro = mascara[ys.astype(int) % S, xs.astype(int) % S]
        xs, ys = xs[dentro], ys[dentro]
    rs = rnd.uniform(r0, r1, len(xs))
    ts = rnd.integers(0, len(tonos), len(xs))
    for x, y, r in zip(xs, ys, rs):
        disco(img, x + r * 0.38, y + r * 0.38, r, sombra)
    for x, y, r, t in zip(xs, ys, rs, ts):
        disco(img, x, y, r, tonos[t])
        if luz is not None and r > r0 + (r1 - r0) * 0.45:
            disco(img, x - r * 0.3, y - r * 0.3, r * 0.42, luz)


def charca(img, cx, cy, ax, ay, ang, capas, wob=0.14, fase=0.0):
    for k, c in capas:
        mancha(img, cx, cy, ax, ay, ang, c, wob, fase, k)


def pintar_jungla(var):
    rnd = np.random.default_rng(510)
    n = ruido(511, [(2, 1.0), (4, 0.6), (8, 0.3)])
    img = np.empty((S, S, 3), dtype=np.float32)
    img[:] = col("21703A")
    img[n > -0.3] = col("2B8040")
    img[n > 0.7] = col("369046")
    tonos = [col(h) for h in ("2E8540", "3FA34D", "4DB24F", "5DBB4C", "6CC24A", "2A7A3A", "47A84A")]
    copas(img, rnd, 0, 11, 24, tonos, col("1D5A2E"), col("86D35E"), paso=27)
    flores = [col(h) for h in ("E8457A", "F6C445", "B57BE0", "F27B2B")]
    copas(img, rnd, 260, 7, 11, flores, col("1D5A2E"), col("FFF4E0"))
    rv = np.random.default_rng(520 + var)
    m = 360
    agua = [(1.0, col("D8C27E")), (0.84, col("3FA6B5")), (0.5, col("2F8FA3"))]
    if var == 1:
        ctrl = ctrl_serpiente(rv, m, rv.uniform(m, S - m), S - m, rv.uniform(m, S - m), 7, 260)
        pts = ruta(ctrl, 5)
        trazo(img, pts, 34, col("D8C27E"))
        trazo(img, pts, 26, col("3FA6B5"))
        trazo(img, pts, 12, col("2F8FA3"))
        for (x, y) in (ctrl[0], ctrl[-1]):
            charca(img, x, y, rv.uniform(70, 95), rv.uniform(50, 70), rv.uniform(0, 3), [(1.2, col("D8C27E")), (1.0, col("3FA6B5")), (0.55, col("2F8FA3"))], 0.16, rv.uniform(0, 6))
        for _ in range(2):
            charca(img, rv.uniform(m, S - m), rv.uniform(m, S - m), rv.uniform(35, 55), rv.uniform(25, 40), rv.uniform(0, 3), [(1.25, col("D8C27E")), (1.0, col("3FA6B5"))], 0.18, rv.uniform(0, 6))
    else:
        for _ in range(2):
            cx, cy = rv.uniform(m, S - m), rv.uniform(m, S - m)
            mancha(img, cx, cy, rv.uniform(110, 150), rv.uniform(80, 110), rv.uniform(0, 3), col("8CCB5A"), 0.16, rv.uniform(0, 6))
            mancha(img, cx, cy, 70, 50, rv.uniform(0, 3), col("9FD66A"), 0.2, rv.uniform(0, 6))
            for _ in range(7):
                hx, hy = cx + rv.uniform(-55, 55), cy + rv.uniform(-40, 40)
                disco(img, hx + 3, hy + 3, 6, col("5E7A35"))
                disco(img, hx, hy, 6, col("C99A46"))
                disco(img, hx - 1.5, hy - 1.5, 2.5, col("E6C068"))
        ctrl = ctrl_serpiente(rv, rv.uniform(m, S - m), m, rv.uniform(m, S - m), S - m, 6, 200)
        pts = ruta(ctrl, 4)
        trazo(img, pts, 13, col("D8C27E"))
        trazo(img, pts, 8, col("3FA6B5"))
        x, y = ctrl[-1]
        charca(img, x, y, 80, 60, 0.4, [(1.2, col("D8C27E")), (1.0, col("3FA6B5")), (0.55, col("2F8FA3"))], 0.15, 1.0)
    copas(img, rnd, 500, 13, 22, tonos, col("1D5A2E"), col("86D35E"))
    return bajar(img)


def pintar_nieve(var):
    rnd = np.random.default_rng(610)
    n = ruido(611, [(2, 1.0), (3, 0.6), (6, 0.35), (11, 0.15)])
    t = np.clip((n + 0.2) / 1.6, 0, 1)
    img = mezcla(np.broadcast_to(col("F6F9FC"), (S, S, 3)).copy(), np.broadcast_to(col("D3E2F1"), (S, S, 3)), t)
    img[n > 1.25] = col("C6D8EC")
    fase = ((5 * XX + 2 * YY) / S * 9.0 + 0.35 * n) % 1.0
    img[(fase < 0.05) & (n < 0.9)] = col("FFFFFF")
    bosque = ruido(612, [(2, 1.0), (4, 0.7), (7, 0.35)]) > 0.45
    pinos = [col("2F6B4F"), col("23543F"), col("356F52")]
    gx, gy = np.meshgrid(np.arange(0, S, 9), np.arange(0, S, 9))
    xs = (gx.ravel() + rnd.uniform(-4, 4, gx.size)) % S
    ys = (gy.ravel() + rnd.uniform(-4, 4, gy.size)) % S
    dentro = bosque[ys.astype(int), xs.astype(int)] | (rnd.random(xs.size) < 0.012)
    xs, ys = xs[dentro], ys[dentro]
    rs = rnd.uniform(4.0, 6.2, xs.size)
    for x, y, r in zip(xs, ys, rs):
        disco(img, x + 3.2, y + 2.4, r * 1.05, col("AFC3D8"))
    for x, y, r, k in zip(xs, ys, rs, rnd.integers(0, 3, xs.size)):
        disco(img, x, y, r, pinos[k])
        disco(img, x - r * 0.3, y - r * 0.32, r * 0.42, col("EAF2FA"))
    rv = np.random.default_rng(620 + var)
    m = 340

    def lago(cx, cy, ax, ay, ang, fase):
        charca(img, cx, cy, ax, ay, ang, [(1.1, col("FFFFFF")), (1.0, col("7CC7E6")), (0.93, col("A8DDF0"))], 0.13, fase)
        for _ in range(5):
            mancha(img, cx + rv.uniform(-0.5, 0.5) * ax, cy + rv.uniform(-0.45, 0.45) * ay, rv.uniform(0.12, 0.22) * ax, rv.uniform(0.08, 0.15) * ay, ang, col("C9EEF8"), 0.25, rv.uniform(0, 6))
        for _ in range(int(ax / 30)):
            a = rv.uniform(0, 6.28)
            px, py = cx + math.cos(a) * ax * rv.uniform(0, 0.5), cy + math.sin(a) * ay * rv.uniform(0, 0.5)
            pts = [(px, py)]
            for _ in range(rv.integers(3, 6)):
                a += rv.uniform(-0.9, 0.9)
                px, py = px + math.cos(a) * rv.uniform(14, 30), py + math.sin(a) * rv.uniform(14, 30)
                pts.append((px, py))
            trazo(img, ruta(pts, 1.5), 1.1, col("F4FBFF"))
        for _ in range(3):
            hx, hy = cx + rv.uniform(-0.4, 0.4) * ax, cy + rv.uniform(-0.35, 0.35) * ay
            disco(img, hx, hy, 3.5, col("2F6E9E"))
            rect(img, hx + 6, hx + 13, hy - 7, hy - 1, col("8A9AB0"))
            rect(img, hx + 5, hx + 12, hy - 8, hy - 2, col("C8453A"))

    def roca(cx, cy, r):
        mancha(img, cx + 5, cy + 4, r, r * 0.7, 0.3, col("A9B9CC"), 0.25, cx)
        mancha(img, cx, cy, r, r * 0.7, 0.3, col("8C93A3"), 0.25, cx)
        mancha(img, cx - r * 0.2, cy - r * 0.2, r * 0.7, r * 0.45, 0.3, col("F4F8FC"), 0.3, cy)
        for _ in range(3):
            a = rv.uniform(0, 6.28)
            trazo(img, ruta([(cx, cy), (cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.4)], 1.5), 1.4, col("667086"))

    if var == 1:
        lago(rv.uniform(m + 200, S - m - 200), rv.uniform(m + 150, S - m - 150), rv.uniform(240, 290), rv.uniform(150, 190), rv.uniform(0, 3), rv.uniform(0, 6))
        for _ in range(6):
            roca(rv.uniform(m, S - m), rv.uniform(m, S - m), rv.uniform(36, 70))
    else:
        for _ in range(2):
            lago(rv.uniform(m + 100, S - m - 100), rv.uniform(m + 100, S - m - 100), rv.uniform(120, 170), rv.uniform(80, 110), rv.uniform(0, 3), rv.uniform(0, 6))
        ctrl = ctrl_serpiente(rv, m, rv.uniform(m, S - m), S - m, rv.uniform(m, S - m), 6, 180)
        pts = ruta(ctrl, 4)
        trazo(img, pts, 10, col("FFFFFF"))
        trazo(img, pts, 7, col("A8DDF0"))
        for _ in range(4):
            roca(rv.uniform(m, S - m), rv.uniform(m, S - m), rv.uniform(36, 60))
    return bajar(img)


def pintar_desierto(var):
    rnd = np.random.default_rng(710)
    n = ruido(711, [(2, 1.0), (4, 0.5), (7, 0.25)])
    fase = ((7 * XX + 3 * YY) / S + 0.16 * n) % 1.0
    claro, base, sombra, cresta = col("F3B66E"), col("EAA35C"), col("D58747"), col("FAD08F")
    img = np.where((fase < 0.6)[..., None], mezcla(np.broadcast_to(claro, (S, S, 3)), np.broadcast_to(base, (S, S, 3)), np.clip(fase / 0.6, 0, 1)),
                   mezcla(np.broadcast_to(base, (S, S, 3)), np.broadcast_to(sombra, (S, S, 3)), np.clip((fase - 0.6) / 0.4, 0, 1))).astype(np.float32)
    img[(fase < 0.018) | (fase > 0.988)] = cresta
    rojizo = ruido(712, [(2, 1.0), (3, 0.6)]) > 0.6
    img[rojizo] = img[rojizo] * 0.82 + col("D0683A") * 0.18
    rv = np.random.default_rng(720 + var)
    m = 330
    if var == 1:
        ctrl = ctrl_serpiente(rv, m, rv.uniform(m, S - m), S - m, rv.uniform(m, S - m), 7, 240)
        pts = ruta(ctrl, 4)
        trazo(img, pts, 20, col("C98545"))
        trazo(img, pts, 15, col("E7BC82"))
        for x, y in pts[::3]:
            if rv.random() < 0.5:
                a = rv.uniform(0, 6.28)
                trazo(img, ruta([(x, y), (x + math.cos(a) * 9, y + math.sin(a) * 9)], 1.5), 0.9, col("C49660"))
        cx, cy = rv.uniform(m + 150, S - m - 150), rv.uniform(m + 150, S - m - 150)
        mancha(img, cx, cy, 170, 110, rv.uniform(0, 3), col("F3E2C2"), 0.12, 2.0)
        semillas = [(cx + rv.uniform(-170, 170), cy + rv.uniform(-110, 110)) for _ in range(40)]
        y0, y1, x0, x1 = int(cy - 200), int(cy + 200), int(cx - 200), int(cx + 200)
        sub = img[y0:y1, x0:x1]
        d1 = np.full(sub.shape[:2], np.inf, np.float32)
        d2 = np.full(sub.shape[:2], np.inf, np.float32)
        for sx, sy in semillas:
            d = np.sqrt((XX[y0:y1, x0:x1] - sx) ** 2 + (YY[y0:y1, x0:x1] - sy) ** 2)
            d2 = np.where(d < d1, d1, np.minimum(d2, d))
            d1 = np.minimum(d1, d)
        sal = np.all(np.abs(sub - col("F3E2C2")) < 1e-3, axis=2)
        sub[sal & (d2 - d1 < 2.2)] = col("D9C6A0")
        for _ in range(6):
            x, y, r = rv.uniform(m, S - m), rv.uniform(m, S - m), rv.uniform(40, 80)
            mancha(img, x + 7, y + 6, r, r * 0.65, rv.uniform(0, 3), col("8F3A22"), 0.22, x)
            mancha(img, x, y, r, r * 0.65, rv.uniform(0, 3), col("C2552F"), 0.22, x)
            mancha(img, x - 5, y - 5, r * 0.62, r * 0.38, rv.uniform(0, 3), col("E07B45"), 0.25, y)
    else:
        ctrl = ctrl_serpiente(rv, rv.uniform(m, S - m), m, rv.uniform(m, S - m), S - m, 8, 230)
        pts = ruta(ctrl, 4)
        trazo(img, pts, 34, col("E07B45"))
        trazo(img, pts, 26, col("A3432A"))
        trazo(img, pts, 13, col("6E2A1C"))
        trazo(img, pts, 3.5, col("3FA6B5"))
        cx, cy = rv.uniform(m + 120, S - m - 120), rv.uniform(m + 120, S - m - 120)
        mancha(img, cx, cy, 95, 75, 0.5, col("8DC85C"), 0.15, 1.0)
        mancha(img, cx, cy, 55, 42, 0.5, col("3FB8C9"), 0.15, 2.0)
        mancha(img, cx, cy, 30, 22, 0.5, col("2F9FB5"), 0.2, 3.0)
        for k in range(16):
            a = 2 * math.pi * k / 16 + rv.uniform(-0.15, 0.15)
            x, y = cx + math.cos(a) * 75, cy + math.sin(a) * 60
            disco(img, x + 4, y + 3, 9, col("6E8A3A"))
            disco(img, x, y, 9, col("4FAE3E"))
            disco(img, x - 2.5, y - 2.5, 3.5, col("8DD35E"))
        for _ in range(4):
            x, y, r = rv.uniform(m, S - m), rv.uniform(m, S - m), rv.uniform(40, 70)
            mancha(img, x + 7, y + 6, r, r * 0.65, rv.uniform(0, 3), col("8F3A22"), 0.22, x)
            mancha(img, x, y, r, r * 0.65, rv.uniform(0, 3), col("C2552F"), 0.22, x)
            mancha(img, x - 5, y - 5, r * 0.62, r * 0.38, rv.uniform(0, 3), col("E07B45"), 0.25, y)
    copas(img, rnd, 1100, 3.0, 4.8, [col("7E8F42"), col("6C7D38"), col("8E9C4C")], col("B8763E"))
    for x, y in zip(rnd.uniform(0, S, 1600), rnd.uniform(0, S, 1600)):
        disco(img, x, y, 1.6, col("B04A2A"))
    return bajar(img)


def pintar_ciudad(var):
    rnd = np.random.default_rng(810 + var)
    B, calle, acera = 128, 16, 3
    img = np.empty((S, S, 3), dtype=np.float32)
    img[:] = col("5E636B")
    n = S // B
    techos = [col(h) for h in ("ECE6DA", "9DB4C8", "F2B880", "E39A9A", "B6D7A8", "C9C3B6", "8E96A0", "F6D58A", "D7C2E8")]
    especial = set()
    if var == 1:
        especial = {(5, 9), (6, 9), (5, 10), (6, 10)}
    else:
        especial = {(9, 4), (10, 4), (9, 5), (10, 5)}

    def interior(bi, bj):
        x0, x1 = bi * B + calle / 2, (bi + 1) * B - calle / 2
        y0, y1 = bj * B + calle / 2, (bj + 1) * B - calle / 2
        if bi % 4 == 0:
            x0 += 6
        if (bi + 1) % 4 == 0:
            x1 -= 6
        if bj % 4 == 0:
            y0 += 6
        if (bj + 1) % 4 == 0:
            y1 -= 6
        return x0, x1, y0, y1

    for k in range(n):
        c = k * B
        largo = (YY[:, 0] % 20) < 10
        for off in (-1, 0):
            img[largo, (c + off) % S] = col("D9D9D0")
            img[(c + off) % S, largo] = col("D9D9D0")
    for k in range(0, S, B * 4):
        for off in range(-3, 3):
            cc = (k + off) % S
            img[:, cc] = col("79C25A")
            img[cc, :] = col("79C25A")
    for bi in range(n):
        for bj in range(n):
            if (bi, bj) in especial:
                continue
            x0, x1, y0, y1 = interior(bi, bj)
            rect(img, x0, x1, y0, y1, col("C9C3B6"))
            x0, x1, y0, y1 = x0 + acera, x1 - acera, y0 + acera, y1 - acera
            tipo = rnd.random()
            if tipo < 0.12:
                rect(img, x0, x1, y0, y1, col("79C25A"))
                rect(img, (x0 + x1) / 2 - 2, (x0 + x1) / 2 + 2, y0, y1, col("E2D3A8"))
                rect(img, x0, x1, (y0 + y1) / 2 - 2, (y0 + y1) / 2 + 2, col("E2D3A8"))
                for _ in range(26):
                    tx, ty = rnd.uniform(x0 + 5, x1 - 5), rnd.uniform(y0 + 5, y1 - 5)
                    disco(img, tx + 2, ty + 2, 5, col("3B7A31"))
                    disco(img, tx, ty, 5, col("4E9A3A") if rnd.random() < 0.6 else col("5DB443"))
            elif tipo < 0.19:
                rect(img, x0, x1, y0, y1, col("D9CBB0"))
                for g in range(int(x0), int(x1), 8):
                    rect(img, g, g + 1, y0, y1, col("CBBB9C"))
                disco(img, (x0 + x1) / 2, (y0 + y1) / 2, 14, col("F2F2EA"))
                disco(img, (x0 + x1) / 2, (y0 + y1) / 2, 11, col("8FD3F4"))
            elif tipo < 0.27:
                rect(img, x0, x1, y0, y1, col("8A9099"))
                for g in range(int(x0) + 4, int(x1) - 4, 9):
                    rect(img, g, g + 1, y0 + 4, y0 + 30, col("F2F2EA"))
                    rect(img, g, g + 1, y1 - 30, y1 - 4, col("F2F2EA"))
                    for yy in (y0 + 8, y1 - 26):
                        if rnd.random() < 0.7:
                            rect(img, g + 2, g + 7, yy, yy + 12, techos[rnd.integers(0, len(techos))] * 0.9)
            else:
                lotes = [(x0, x1, y0, y1)]
                for _ in range(rnd.integers(1, 4)):
                    lx0, lx1, ly0, ly1 = lotes.pop(rnd.integers(0, len(lotes)))
                    if lx1 - lx0 > ly1 - ly0:
                        cut = rnd.uniform(lx0 + 0.35 * (lx1 - lx0), lx0 + 0.65 * (lx1 - lx0))
                        lotes += [(lx0, cut, ly0, ly1), (cut, lx1, ly0, ly1)]
                    else:
                        cut = rnd.uniform(ly0 + 0.35 * (ly1 - ly0), ly0 + 0.65 * (ly1 - ly0))
                        lotes += [(lx0, lx1, ly0, cut), (lx0, lx1, cut, ly1)]
                rect(img, x0, x1, y0, y1, col("4A4F57"))
                for lx0, lx1, ly0, ly1 in lotes:
                    c = techos[rnd.integers(0, len(techos))]
                    rect(img, lx0 + 1, lx1 - 4, ly0 + 1, ly1 - 4, c)
                    rect(img, lx0 + 1, lx1 - 4, ly1 - 6, ly1 - 4, c * 0.82)
                    for _ in range(rnd.integers(1, 4)):
                        ax, ay = rnd.uniform(lx0 + 4, max(lx0 + 5, lx1 - 12)), rnd.uniform(ly0 + 4, max(ly0 + 5, ly1 - 12))
                        rect(img, ax + 1.5, ax + 6.5, ay + 1.5, ay + 6.5, c * 0.7)
                        rect(img, ax, ax + 5, ay, ay + 5, col("D5DAE0"))
                    if rnd.random() < 0.3:
                        tx, ty = rnd.uniform(lx0 + 6, max(lx0 + 7, lx1 - 10)), rnd.uniform(ly0 + 6, max(ly0 + 7, ly1 - 10))
                        disco(img, tx + 1.5, ty + 1.5, 3.5, c * 0.65)
                        disco(img, tx, ty, 3.5, col("8A5A33"))
    bis = sorted({b for b, _ in especial})
    bjs = sorted({b for _, b in especial})
    x0, _, y0, _ = interior(bis[0], bjs[0])
    _, x1, _, y1 = interior(bis[-1], bjs[-1])
    rect(img, x0, x1, y0, y1, col("C9C3B6"))
    x0, x1, y0, y1 = x0 + acera, x1 - acera, y0 + acera, y1 - acera
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if var == 1:
        rect(img, x0, x1, y0, y1, col("79C25A"))
        mancha(img, cx + 10, cy + 6, 70, 42, 0.4, col("C9C3B6"), 0.18, 1.0, 1.15)
        mancha(img, cx + 10, cy + 6, 70, 42, 0.4, col("5BB8D9"), 0.18, 1.0)
        for _ in range(140):
            tx, ty = rnd.uniform(x0 + 6, x1 - 6), rnd.uniform(y0 + 6, y1 - 6)
            if ((tx - cx - 10) / 85) ** 2 + ((ty - cy - 6) / 56) ** 2 < 1:
                continue
            disco(img, tx + 2, ty + 2, 6, col("3B7A31"))
            disco(img, tx, ty, 6, col("4E9A3A") if rnd.random() < 0.6 else col("5DB443"))
    else:
        rect(img, x0, x1, y0, y1, col("8A9099"))
        u = (XX[int(y0):int(y1), int(x0):int(x1)] - cx) / ((x1 - x0) / 2)
        v = (YY[int(y0):int(y1), int(x0):int(x1)] - cy) / ((y1 - y0) / 2)
        r = np.sqrt(u * u + v * v)
        ang = np.arctan2(v, u)
        sub = img[int(y0):int(y1), int(x0):int(x1)]
        sub[r < 0.98] = col("F2F2EA")
        sub[(r < 0.98) & ((ang * 12 / math.pi).astype(int) % 2 == 0)] = col("D94A3A")
        sub[r < 0.74] = col("C9693E")
        sub[r < 0.6] = col("6AB547")
        sub[(r < 0.6) & (np.abs(u) < 0.012)] = col("F2F2EA")
    return bajar(img)


PINTORES = {"Jungla": pintar_jungla, "Nieve": pintar_nieve, "Desierto": pintar_desierto, "Ciudad": pintar_ciudad}


def caja(x0, x1, y0, y1, z0, z1, fondo=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1.0)), verts=bm.verts)
    if not fondo:
        bm.normal_update()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.9], context="FACES_ONLY")
    return bm


def contorno(n, rnd, wob=(0.12, 0.07, 0.04)):
    f = [rnd.uniform(0, 6.28) for _ in range(3)]
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        r = 1 + wob[0] * math.sin(2 * a + f[0]) + wob[1] * math.sin(5 * a + f[1]) + wob[2] * math.sin(9 * a + f[2])
        out.append((r * math.cos(a), r * math.sin(a)))
    return out


def loft(pts, niveles, tapa=True, base=False):
    bm = bmesh.new()
    anillos = []
    for nv in niveles:
        sx, sy, z = nv[:3]
        dx, dy = nv[3:5] if len(nv) >= 5 else (0.0, 0.0)
        anillos.append([bm.verts.new((x * sx + dx, y * sy + dy, z)) for x, y in pts])
    n = len(pts)
    for a, b in zip(anillos, anillos[1:]):
        for j in range(n):
            j2 = (j + 1) % n
            bm.faces.new((a[j], a[j2], b[j2], b[j]))
    if tapa:
        bm.faces.new(anillos[-1])
    if base:
        bm.faces.new(list(reversed(anillos[0])))
    return bm


def rectp(w, d):
    return [(w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2), (-w / 2, -d / 2)]


def armar(p, mat, centrar=True):
    prims = []
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    contador = {}
    for bm, role, ang in p.parts:
        if any(len(f.verts) > 3 for f in bm.faces):
            bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method="BEAUTY", ngon_method="EAR_CLIP")
        bm.normal_update()
        clave = "losa" if role is None else (role if isinstance(role, str) else "fn")
        contador[clave] = contador.get(clave, 0) + len(bm.faces)
        uvl = bm.loops.layers.uv.active
        cols = []
        for f in bm.faces:
            if role is None:
                uv = f.loops[0][uvl].uv
                cols.append((uv.x, uv.y))
            else:
                cols.append(suv(role(f.calc_center_median(), f.normal.copy()) if callable(role) else role))
        for v in bm.verts:
            for i in range(3):
                mn[i] = min(mn[i], v.co[i])
                mx[i] = max(mx[i], v.co[i])
        prims.append((bm, cols, ang))
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, 0.0)) if centrar else Vector()
    verts, faces, uvs, nrms = [], [], [], []
    for bm, cols, ang in prims:
        bm.verts.index_update()
        base = len(verts)
        verts.extend(v.co - off for v in bm.verts)
        cl = math.cos(math.radians(ang))
        for f, uv in zip(bm.faces, cols):
            if f.calc_area() < 1e-7:
                continue
            faces.append([base + v.index for v in f.verts])
            for lp in f.loops:
                ns = Vector()
                for lf in lp.vert.link_faces:
                    if lf.normal.dot(f.normal) >= cl - 1e-6:
                        ns += lf.normal * lf.calc_area()
                nrms.append(ns.normalized() if ns.length > 1e-12 else f.normal.copy())
                uvs.append(uv)
        bm.free()
    me = bpy.data.meshes.new(p.name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", [c for uv in uvs for c in uv])
    me.shade_smooth()
    me.normals_split_custom_set([tuple(n) for n in nrms])
    me.materials.append(mat)
    ob = bpy.data.objects.new(p.name, me)
    bpy.context.scene.collection.objects.link(ob)
    if arg("--detalle"):
        print("  ", p.name, sorted(contador.items(), key=lambda kv: -kv[1])[:8])
    return ob, len(faces)


def losa(p, rects, fondo, x0, x1, y0, y1, falda=7.0, zb=-1.6, borde=None):
    z = TECHO_LOSA
    xs = sorted({x0, x1} | {min(max(r[i], x0), x1) for r in rects for i in (0, 1)})
    ys = sorted({y0, y1} | {min(max(r[i], y0), y1) for r in rects for i in (2, 3)})
    xs = [x0 - falda] + xs + [x1 + falda]
    ys = [y0 - falda] + ys + [y1 + falda]
    nx, ny = len(xs) - 1, len(ys) - 1
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    vs = [[bm.verts.new((x, y, zb if (i in (0, nx) or j in (0, ny)) else z)) for i, x in enumerate(xs)] for j, y in enumerate(ys)]
    clave = [[None] * nx for _ in range(ny)]
    caras = [[None] * nx for _ in range(ny)]
    for j in range(ny):
        for i in range(nx):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            bi, bj = i in (0, nx - 1), j in (0, ny - 1)
            if bi or bj:
                rol = borde or fondo
                zona = ("esquina", i, j) if bi and bj else ("lado", 0 if i == 0 else 1 if i == nx - 1 else 2 if j == 0 else 3)
            else:
                rol = fondo
                for r in rects:
                    if r[0] <= cx <= r[1] and r[2] <= cy <= r[3]:
                        rol = r[4]
                zona = ("dentro",)
            clave[j][i] = (rol, zona)
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            for lp in f.loops:
                lp[uvl].uv = suv(rol)
            caras[j][i] = f
    usado = [[False] * nx for _ in range(ny)]
    grupos = []
    for j in range(ny):
        for i in range(nx):
            if usado[j][i]:
                continue
            k = clave[j][i]
            w = 1
            while i + w < nx and not usado[j][i + w] and clave[j][i + w] == k:
                w += 1
            h = 1
            while j + h < ny and all(not usado[j + h][i + t] and clave[j + h][i + t] == k for t in range(w)):
                h += 1
            for jj in range(j, j + h):
                for ii in range(i, i + w):
                    usado[jj][ii] = True
            grupos.append([caras[jj][ii] for jj in range(j, j + h) for ii in range(i, i + w)])
    for g in grupos:
        if len(g) > 1:
            bmesh.ops.dissolve_faces(bm, faces=g, use_verts=True)
    rectos = []
    for v in bm.verts:
        if len(v.link_edges) == 2:
            e1 = v.link_edges[0].other_vert(v).co - v.co
            e2 = v.link_edges[1].other_vert(v).co - v.co
            if e1.length > 1e-6 and e2.length > 1e-6 and e1.normalized().dot(e2.normalized()) < -0.99999:
                rectos.append(v)
    if rectos:
        bmesh.ops.dissolve_verts(bm, verts=rectos)
    if arg("--detalle"):
        print("  losa", nx * ny, "celdas ->", len(grupos), "rectangulos,", len(bm.faces), "caras", sum(len(f.verts) for f in bm.faces), "vertices")
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="EAR_CLIP")
    p.add(bm, None, 0.0)


def franjas_pista(x0, x1, y0, y1, ancho_linea, rol_linea, rayas=True, piano=8, umbral=36.0):
    rs = []
    w = ancho_linea
    rs.append((x0 + 1.0, x0 + 1.0 + w, y0 + 2, y1 - 2, rol_linea))
    rs.append((x1 - 1.0 - w, x1 - 1.0, y0 + 2, y1 - 2, rol_linea))
    if rayas:
        y = y0 + umbral + 30
        while y + 18 < y1 - umbral - 30:
            rs.append((-w / 2, w / 2, y, y + 18, rol_linea))
            y += 40
    if piano:
        ancho = x1 - x0
        paso = (ancho - 8) / (piano * 2)
        for k in range(piano * 2):
            if k in (piano - 1, piano):
                continue
            bx = x0 + 4 + k * paso + paso * 0.2
            for ya, yb in ((y0 + 6, y0 + 6 + umbral), (y1 - 6 - umbral, y1 - 6)):
                rs.append((bx, bx + paso * 0.6, ya, yb, rol_linea))
    return rs


def copa(p, x, y, z, r, h, rol, seg=8, anillos=5, ang=70):
    p.add(ellipsoid((r, r, h), Matrix.Translation((x, y, z)), seg, anillos), rol, ang)


def arbol_selva(p, rnd, x, y, s=1.0):
    t = rnd.uniform(3.0, 5.0) * s
    p.add(palo((x, y, -0.6), (x + rnd.uniform(-0.6, 0.6) * s, y + rnd.uniform(-0.6, 0.6) * s, t + 1.5 * s), 0.55 * s, 5, 0.4 * s), "trunk", 40)
    r = rnd.uniform(4.2, 6.0) * s
    tonos = ["jleaf", "jleaf2", "jleaf3", "jleaf", "palm"]
    rol = rnd.choice(tonos)
    copa(p, x, y, t + r * 0.55, r, r * 0.72, rol, 8, 5)
    for k in range(rnd.randint(1, 2)):
        a = rnd.uniform(0, 6.28)
        rr = r * rnd.uniform(0.55, 0.7)
        copa(p, x + math.cos(a) * r * 0.6, y + math.sin(a) * r * 0.6, t + r * 0.5 + rnd.uniform(0.2, 1.2) * s, rr, rr * 0.75, rnd.choice(tonos), 7, 4)
    if rnd.random() < 0.25:
        copa(p, x + r * 0.2, y - r * 0.2, t + r * 1.05, r * 0.45, r * 0.35, "jlime", 6, 4)


def palmera(p, rnd, x, y, alto, s=1.0, nf=6):
    a = rnd.uniform(0, 6.28)
    inc = rnd.uniform(0.6, 1.8) * s
    ctrl = [(x, y, -0.6), (x + math.cos(a) * inc * 0.3, y + math.sin(a) * inc * 0.3, alto * 0.45), (x + math.cos(a) * inc, y + math.sin(a) * inc, alto)]
    p.add(tube(ctrl, lambda u: (0.42 - 0.16 * u) * s, 5, 2, caps=False), lambda c, n: "trunk" if int(c.z / (1.6 * s)) % 2 else "dwood", 60)
    cima = Vector(ctrl[-1])
    copa(p, cima.x, cima.y, cima.z, 0.55 * s, 0.45 * s, "dwood", 6, 4)
    for k in range(nf):
        b = 2 * math.pi * k / nf + rnd.uniform(-0.2, 0.2)
        p.add(fronda(cima, b, alto * rnd.uniform(0.42, 0.5), rnd.uniform(15, 30), rnd.uniform(-62, -42), 1.75 * s, 4, 0.6, 0.4),
              lambda c, n: "palm" if n.z > 0 else "palm2", 70)


def pino(p, rnd, x, y, alto, r, nieve=True, niveles=3):
    p.add(palo((x, y, -0.6), (x, y, alto * 0.22), r * 0.14, 4, None, False, False), "trunk", 40)
    for k in range(niveles):
        z0 = alto * (0.16 + 0.72 * k / niveles)
        h = alto * (0.5 - 0.18 * k / niveles)
        rk = r * (1.0 - 0.75 * k / niveles)
        corte = z0 + h * 0.42
        prof = [(rk, z0), (rk * 0.62, z0 + h * 0.4), (0.0, z0 + h)]
        rol = (lambda c, n, corte=corte: "snow" if c.z > corte else ("pine2" if n.z < 0.2 else "pine")) if nieve else (lambda c, n: "pine2" if n.z < 0.2 else "pine")
        p.add(lathe(prof, 7, Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(rnd.uniform(0, 1), 4, "Z"), cap0=(k == 0), cap1=False), rol, 30)


def saguaro(p, rnd, x, y, alto, s=1.0):
    def rol(c, n):
        a = math.atan2(n.y, n.x)
        return "cactus" if int((a + math.pi) / (2 * math.pi) * 16) % 2 else "cactus2"
    r = 0.55 * s
    p.add(tube([(x, y, -0.5), (x, y, alto * 0.5), (x, y, alto)], lambda u: r, 6, 1, caps=True, cap_rings=1), rol, 35)
    for k in range(rnd.randint(1, 3)):
        a = rnd.uniform(0, 6.28) if k == 0 else a + math.pi * rnd.uniform(0.7, 1.3)
        h0 = alto * rnd.uniform(0.35, 0.55)
        L = rnd.uniform(1.4, 2.0) * s
        up = alto * rnd.uniform(0.25, 0.4)
        ca, sa = math.cos(a), math.sin(a)
        ctrl = [(x + ca * r * 0.5, y + sa * r * 0.5, h0), (x + ca * L, y + sa * L, h0 + 0.2 * s), (x + ca * L * 1.05, y + sa * L * 1.05, h0 + up)]
        p.add(tube(ctrl, lambda u: r * 0.72, 6, 2, caps=True, cap_rings=1), rol, 35)


def roca_desierto(p, rnd, x, y, r, h):
    pts = contorno(9, rnd, (0.18, 0.1, 0.05))
    p.add(loft(pts, [(r * 1.15, r * 0.95, -0.6, x, y), (r, r * 0.82, h * 0.5, x, y), (r * 0.7, r * 0.55, h, x, y)]), lambda c, n: "redrock3" if n.z > 0.6 else ("redrock" if c.z > h * 0.3 else "redrock2"), 30)


def p_selva():
    p = Prop("SelvaJungla", None, 2600)
    rnd = random.Random(11)
    sitios = []
    while len(sitios) < 12:
        a, d = rnd.uniform(0, 6.28), 24 * math.sqrt(rnd.random())
        x, y = d * math.cos(a) * 1.2, d * math.sin(a)
        if all((x - sx) ** 2 + (y - sy) ** 2 > 55 for sx, sy in sitios):
            sitios.append((x, y))
    for i, (x, y) in enumerate(sitios):
        if i < 2:
            palmera(p, rnd, x, y, rnd.uniform(17, 21), 1.0, 6)
        else:
            arbol_selva(p, rnd, x, y, rnd.uniform(1.1, 1.45))
    return p


def p_palmeral():
    p = Prop("PalmeralJungla", None, 2400)
    rnd = random.Random(12)
    for k in range(7):
        a, d = 2 * math.pi * k / 7 + rnd.uniform(-0.3, 0.3), rnd.uniform(5, 17)
        palmera(p, rnd, d * math.cos(a), d * math.sin(a), rnd.uniform(14, 21), 1.0, 7)
    for k in range(4):
        a = rnd.uniform(0, 6.28)
        copa(p, 14 * math.cos(a), 14 * math.sin(a), 1.2, rnd.uniform(3, 4), 2.4, rnd.choice(["jleaf3", "jlime", "jleaf"]), 8, 5)
    return p


def p_cerro():
    p = Prop("CerroJungla", None, 3200)
    rnd = random.Random(13)
    pts = contorno(22, rnd, (0.1, 0.08, 0.04))
    H = 120.0
    niveles = [(62, 56, -3), (60, 54, 8), (55, 50, 30), (50, 46, 58), (45, 41, 82), (36, 33, 100), (22, 20, 113), (8, 7, H)]
    fr = [rnd.uniform(0, 6.28) for _ in range(3)]

    def rol_cerro(c, n):
        a = math.atan2(c.y, c.x)
        roca = math.sin(3 * a + fr[0]) + 0.6 * math.sin(7 * a + fr[1]) > 0.9 and n.z < 0.45 and 15 < c.z < H - 25
        if roca:
            return "jrock"
        return "jleaf3" if n.z > 0.6 else ("jleaf" if int(c.z / 18 + math.sin(4 * a + fr[2])) % 2 else "jleaf2")
    p.add(loft(pts, niveles, tapa=True), rol_cerro, 40)
    for k in range(32):
        a = rnd.uniform(0, 6.28)
        z = rnd.uniform(4, H - 6)
        rr = 1.0 if z < 58 else max(0.15, (H - z) / (H - 58))
        R = (58 if z < 58 else 22 + 28 * rr) * rnd.uniform(0.85, 1.0)
        size = rnd.uniform(9, 15) * (1.0 if z < 90 else 0.75)
        copa(p, math.cos(a) * R, math.sin(a) * R * 0.92, z, size, size * 0.7, rnd.choice(["jleaf", "jleaf3", "jleaf2", "palm"]), 8, 5)
    for k in range(6):
        a = rnd.uniform(0, 6.28)
        copa(p, math.cos(a) * 8, math.sin(a) * 8, H - 2, rnd.uniform(7, 10), 5, rnd.choice(["jleaf3", "jlime"]), 8, 5)
    return p


def p_pinar():
    p = Prop("PinarNieve", None, 2600)
    rnd = random.Random(21)
    sitios = []
    while len(sitios) < 13:
        a, d = rnd.uniform(0, 6.28), 24 * math.sqrt(rnd.random())
        x, y = d * math.cos(a) * 1.2, d * math.sin(a)
        if all((x - sx) ** 2 + (y - sy) ** 2 > 30 for sx, sy in sitios):
            sitios.append((x, y))
    for x, y in sitios:
        alto = rnd.uniform(14, 24)
        pino(p, rnd, x, y, alto, alto * 0.26)
    for k in range(5):
        a = rnd.uniform(0, 6.28)
        d = rnd.uniform(4, 22)
        copa(p, d * math.cos(a), d * math.sin(a), -0.2, rnd.uniform(3, 5), 1.4, "snow", 8, 4)
    return p


def montana(nombre, semilla, R, H, picos, nieve):
    p = Prop(nombre, None, 4000)
    rnd = random.Random(semilla)
    f = [rnd.uniform(0, 6.28) for _ in range(6)]

    def altura(x, y):
        h = 0.0
        for px, py, ph, pr in picos:
            d = math.sqrt((x - px) ** 2 + (y - py) ** 2) / pr
            if d < 1:
                h = max(h, ph * (1 - d) ** 1.25 * (1 - 0.35 * d * d))
        a = math.atan2(y, x)
        return h * (1 + 0.16 * math.sin(5 * a + f[0]) * min(1.0, math.hypot(x, y) / (R * 0.3)) + 0.08 * math.sin(9 * a + f[1]))

    nr, ns = 12, 34
    bm = bmesh.new()
    centro = bm.verts.new((picos[0][0], picos[0][1], altura(picos[0][0], picos[0][1])))
    anillos = []
    for i in range(1, nr + 1):
        t = i / nr
        anillo = []
        for j in range(ns):
            a = 2 * math.pi * (j + 0.5 * (i % 2)) / ns
            rr = R * t * (1 + 0.1 * math.sin(3 * a + f[2]) + 0.05 * math.sin(7 * a + f[3]))
            x, y = rr * math.cos(a), rr * math.sin(a)
            z = altura(x, y) * (1 + rnd.uniform(-0.04, 0.04)) if i < nr else -5.0
            if i == nr - 1:
                z = min(z, H * 0.04)
            anillo.append(bm.verts.new((x, y, z)))
        anillos.append(anillo)
    for j in range(ns):
        bm.faces.new((centro, anillos[0][j], anillos[0][(j + 1) % ns]))
    for a, b in zip(anillos, anillos[1:]):
        for j in range(ns):
            j2 = (j + 1) % ns
            bm.faces.new((a[j], a[j2], b[j2]))
            bm.faces.new((a[j], b[j2], b[j]))

    def rol(c, n):
        a = math.atan2(c.y, c.x)
        linea = H * (0.5 + 0.07 * math.sin(4 * a + f[4]) + 0.05 * math.sin(11 * a + f[5]))
        if nieve:
            if c.z > linea:
                return "snow" if n.z > 0.35 else "snow2"
            if n.z < 0.6:
                return "rock2" if c.z < H * 0.22 else "rock"
            return "snow2" if c.z < H * 0.12 else "snow3"
        if c.z > linea:
            return "redrock3"
        return "redrock" if n.z > 0.5 else "redrock2"
    p.add(bm, rol, 32)
    return p


def p_montana1():
    return montana("MontanaNieve1", 31, 300.0, 230.0, [(0, 0, 230.0, 300.0), (90, 60, 150.0, 170.0), (-110, -40, 120.0, 150.0)], True)


def p_montana2():
    return montana("MontanaNieve2", 32, 380.0, 190.0, [(0, 0, 190.0, 260.0), (170, 40, 165.0, 210.0), (-160, -50, 150.0, 200.0), (60, -150, 110.0, 160.0)], True)


def meseta(nombre, semilla, rx, ry, H):
    p = Prop(nombre, None, 3000)
    rnd = random.Random(semilla)
    pts = contorno(36, rnd, (0.14, 0.08, 0.05))
    k = [1.32, 1.1, 1.0, 0.99, 0.94, 0.93, 0.88, 0.87, 0.84]
    zs = [-3, H * 0.14, H * 0.22, H * 0.42, H * 0.46, H * 0.66, H * 0.7, H * 0.94, H]
    niveles = [(rx * a, ry * a, z) for a, z in zip(k, zs)]
    bandas = ["redrock", "redrock3", "redrock2", "redrock", "redrock3"]

    def rol(c, n):
        if n.z > 0.75:
            return "tan" if c.z > H * 0.97 else "redrock3"
        if c.z < H * 0.15:
            return "sand2"
        return bandas[min(len(bandas) - 1, int((c.z - H * 0.15) / (H * 0.85) * len(bandas)))]
    p.add(loft(pts, niveles, tapa=True), rol, 25)
    for _ in range(9):
        a = rnd.uniform(0, 6.28)
        roca_desierto(p, rnd, math.cos(a) * rx * 1.3, math.sin(a) * ry * 1.3, rnd.uniform(5, 11), rnd.uniform(4, 9))
    return p


def p_mesa():
    return meseta("MesaDesierto", 41, 130.0, 85.0, 95.0)


def p_agujas():
    p = Prop("AgujasDesierto", None, 3000)
    rnd = random.Random(42)
    for k in range(6):
        a = 2 * math.pi * k / 6 + rnd.uniform(-0.3, 0.3)
        d = rnd.uniform(15, 45)
        x, y = math.cos(a) * d, math.sin(a) * d
        H = rnd.uniform(35, 75)
        r = rnd.uniform(6, 11)
        pts = contorno(10, rnd, (0.15, 0.08, 0.04))
        niveles = [(r * 1.5, r * 1.4, -2, x, y), (r * 1.15, r * 1.1, H * 0.2, x, y), (r * 0.95, r * 0.9, H * 0.45, x, y), (r * 1.0, r * 0.95, H * 0.5, x, y),
                   (r * 0.8, r * 0.75, H * 0.8, x, y), (r * 1.05, r, H * 0.86, x, y), (r * 0.9, r * 0.85, H, x, y)]
        p.add(loft(pts, niveles, tapa=True), lambda c, n, H=H: "redrock3" if n.z > 0.6 else ["redrock", "redrock3", "redrock2"][int(c.z / (H / 6)) % 3], 25)
    ctrl = [(-40, -30, -2), (-46, -18, 30), (-30, 5, 48), (-8, 20, 32), (-2, 28, -2)]
    p.add(tube(ctrl, lambda u: 7.0 - 2.5 * math.sin(math.pi * u), 9, 4, caps=False), lambda c, n: "redrock3" if n.z > 0.6 else ("redrock" if int(c.z / 10) % 2 else "redrock2"), 30)
    return p


def p_cactus():
    p = Prop("CactusDesierto", None, 2400)
    rnd = random.Random(43)
    for k in range(6):
        a, d = 2 * math.pi * k / 6 + rnd.uniform(-0.4, 0.4), rnd.uniform(3, 15)
        saguaro(p, rnd, d * math.cos(a), d * math.sin(a), rnd.uniform(8, 14), rnd.uniform(1.0, 1.3))
    for k in range(5):
        a = rnd.uniform(0, 6.28)
        roca_desierto(p, rnd, 13 * math.cos(a), 13 * math.sin(a), rnd.uniform(1.5, 3.2), rnd.uniform(1.2, 2.6))
    for k in range(4):
        a = rnd.uniform(0, 6.28)
        copa(p, 10 * math.cos(a), 10 * math.sin(a), 0.4, rnd.uniform(1.4, 2.2), 1.1, "cactus2", 7, 4)
    return p


def edificio(p, cx, cy, w, d, h, pisos, muro, vidrio, techo, banda=0.5, z0=-1.0):
    hp = h / pisos
    zs = {z0, 0.0, h}
    for k in range(pisos):
        a = k * hp + hp * 0.25
        zs |= {a, a + hp * banda}
    zs = sorted(z for z in zs if z0 <= z <= h)

    def rol(c, n, hp=hp):
        if n.z > 0.5:
            return techo
        f = (c.z % hp) / hp
        return vidrio if 0 < c.z < h and 0.25 < f < 0.25 + banda else muro
    p.add(loft([(x + cx, y + cy) for x, y in rectp(w, d)], [(1, 1, z) for z in zs], tapa=True), rol, 0)


def azotea(p, rnd, cx, cy, w, d, h):
    for _ in range(rnd.randint(1, 3)):
        ax, ay = cx + rnd.uniform(-0.3, 0.3) * w, cy + rnd.uniform(-0.3, 0.3) * d
        s = rnd.uniform(1.6, 3.0)
        p.add(caja(ax - s, ax + s, ay - s * 0.7, ay + s * 0.7, h - 0.2, h + s * 0.8), "metal", 0)
    if rnd.random() < 0.5:
        ax, ay = cx + rnd.uniform(-0.25, 0.25) * w, cy + rnd.uniform(-0.25, 0.25) * d
        for lx, ly in ((-1.2, -1.2), (1.2, -1.2), (1.2, 1.2), (-1.2, 1.2)):
            p.add(palo((ax + lx, ay + ly, h - 0.2), (ax + lx, ay + ly, h + 2.4), 0.2, 4), "dwood", 0)
        p.add(cyl(2.0, 3.0, (ax, ay, h + 2.4), seg=10, cap0=True), "trunk", 30)
        p.add(lathe([(2.2, h + 5.4), (0.0, h + 6.6)], 10, cap0=True, cap1=False), "dwood", 30)


def p_torres():
    p = Prop("TorresCiudad", None, 4000)
    rnd = random.Random(51)
    torres = [(0, 0, 22, 20, 96, "bldg2", "dglass", "roofg"), (32, -14, 18, 18, 72, "bldg1", "dglass", "teal"), (-30, 10, 20, 16, 64, "bldg3", "glass", "roofg"),
              (12, 30, 16, 16, 84, "bldg5", "dglass", "roofg"), (-14, -32, 22, 14, 52, "bldg4", "glass", "roofg"), (38, 24, 14, 14, 44, "bldg1", "glass", "red")]
    for cx, cy, w, d, h, muro, vidrio, techo in torres:
        if h > 70:
            edificio(p, cx, cy, w, d, h * 0.6, int(h * 0.6 / 4), muro, vidrio, techo, 0.55)
            edificio(p, cx, cy, w * 0.72, d * 0.72, h, int(h / 4), muro, vidrio, techo, 0.55, h * 0.6 - 0.5)
            p.add(palo((cx, cy, h - 0.5), (cx, cy, h + 14), 0.5, 5, 0.15), "metal", 30)
            p.add(ellipsoid((0.9, 0.9, 0.9), Matrix.Translation((cx, cy, h + 14)), 8, 5), "red", 60)
        else:
            edificio(p, cx, cy, w, d, h, int(h / 4), muro, vidrio, techo, 0.55)
            azotea(p, rnd, cx, cy, w, d, h)
    return p


def p_barrio():
    p = Prop("BarrioCiudad", None, 4000)
    rnd = random.Random(52)
    muros = ["bldg1", "bldg3", "bldg4", "bldg5", "bldg2", "concrete"]
    for i in range(3):
        for j in range(3):
            if (i, j) == (1, 1):
                for k in range(6):
                    a = 2 * math.pi * k / 6
                    arbol = (math.cos(a) * 7, math.sin(a) * 7)
                    p.add(palo((arbol[0], arbol[1], -0.5), (arbol[0], arbol[1], 3.5), 0.4, 5), "trunk", 30)
                    copa(p, arbol[0], arbol[1], 5.5, 3.2, 2.6, rnd.choice(["jleaf", "jleaf3"]), 8, 5)
                p.add(cyl(3.0, 1.2, (0, 0, -0.5), seg=12), "concrete", 20)
                p.add(cyl(2.2, 1.0, (0, 0, -0.3), seg=12), "glass", 20)
                continue
            cx, cy = (i - 1) * 36, (j - 1) * 36
            w, d = rnd.uniform(18, 28), rnd.uniform(18, 28)
            h = rnd.uniform(12, 34)
            muro = rnd.choice(muros)
            edificio(p, cx, cy, w, d, h, max(2, int(h / 4)), muro, rnd.choice(["glass", "dglass"]), rnd.choice(["roofg", "roofred", "teal", "roofg"]), 0.45)
            azotea(p, rnd, cx, cy, w, d, h)
    return p


def choza(p, x, y, r, h, rol_muro="cream"):
    p.add(cyl(r, h, (x, y, -0.6), seg=10, cap0=False, cap1=False), rol_muro, 30)
    hr = r * 1.4
    prof = [(r * 1.45, h - 0.6), (r * 1.38, h - 0.2), (r * 0.7, h + hr * 0.55), (0.0, h + hr)]
    p.add(lathe(prof, 10, Matrix.Translation((x, y, 0)), cap0=True, cap1=False), lambda c, n: "thatch" if int((c.z - h) / 1.1) % 2 == 0 else "thatch2", 40)
    p.add(caja(x - r - 0.3, x - r + 0.5, y - 1.0, y + 1.0, -0.6, 2.6), "dwood", 0)


def torre_vigia(p, x, y, h):
    for lx, ly in ((-2.2, -2.2), (2.2, -2.2), (2.2, 2.2), (-2.2, 2.2)):
        p.add(palo((x + lx * 1.15, y + ly * 1.15, -0.6), (x + lx, y + ly, h), 0.35, 5), "trunk", 30)
    p.add(caja(x - 3.2, x + 3.2, y - 3.2, y + 3.2, h, h + 0.6, True), "wood", 0)
    for s in (-1, 1):
        p.add(caja(x - 3.2, x + 3.2, y + s * 3.1 - 0.15, y + s * 3.1 + 0.15, h + 0.6, h + 2.2), "wood", 0)
        p.add(caja(x + s * 3.1 - 0.15, x + s * 3.1 + 0.15, y - 3.0, y + 3.0, h + 0.6, h + 2.2), "wood", 0)
    for lx, ly in ((-2.9, -2.9), (2.9, -2.9), (2.9, 2.9), (-2.9, 2.9)):
        p.add(palo((x + lx, y + ly, h + 0.6), (x + lx, y + ly, h + 4.4), 0.2, 4), "dwood", 0)
    p.add(lathe([(5.3, h + 4.2), (5.0, h + 4.5), (0.0, h + 7.5)], 4, Matrix.Translation((x, y, 0)) @ Matrix.Rotation(math.pi / 4, 4, "Z"), cap0=True, cap1=False), "thatch", 0)
    p.add(palo((x, y, h + 7.3), (x, y, h + 10.5), 0.12, 4), "dwood", 0)
    p.add(caja(x + 0.1, x + 2.2, y - 0.04, y + 0.04, h + 9.2, h + 10.4, True), "red", 0)


def manga(p, x, y, h=9.0, rol_a="red", rol_b="white"):
    p.add(palo((x, y, -0.6), (x, y, h), 0.22, 6), "metal", 30)
    prof = [(1.0, 0.0), (0.85, 1.4), (0.7, 2.8), (0.55, 4.2), (0.4, 5.6)]
    m = Matrix.Translation((x + 0.3, y, h - 0.8)) @ Matrix.Rotation(math.radians(80), 4, "Y")
    p.add(lathe(prof, 8, m, cap0=False, cap1=True), lambda c, n: rol_a if int((c.x - x) / 1.4) % 2 == 0 else rol_b, 40)


def barril(p, x, y, rol, z=-0.4):
    p.add(cyl(0.7, 2.0, (x, y, z), seg=8), rol, 40)


def cajon(p, x, y, s=1.0, rol="wood", z=-0.4):
    p.add(caja(x - s, x + s, y - s, y + s, z, z + 2 * s), rol, 0)


def nave_arco(p, x0, x1, y0, y1, h, rol_a, rol_b, rol_frente, seg=10):
    bm = bmesh.new()
    rx, cx = (x1 - x0) / 2, (x0 + x1) / 2
    filas = []
    for y in (y0, y1):
        filas.append([bm.verts.new((cx - rx * math.cos(math.pi * k / seg), y, -0.6 + (h + 0.6) * math.sin(math.pi * k / seg))) for k in range(seg + 1)])
    for k in range(seg):
        bm.faces.new((filas[0][k], filas[0][k + 1], filas[1][k + 1], filas[1][k]))
    bm.faces.new(filas[0])
    bm.faces.new(list(reversed(filas[1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    def rol(c, n):
        if abs(n.y) > 0.9:
            return rol_frente
        a = math.atan2(c.z, c.x - cx)
        return rol_a if int(a / math.pi * seg) % 2 == 0 else rol_b
    p.add(bm, rol, 0)
    for y, s in ((y0, -1), (y1, 1)):
        p.add(caja(cx - rx * 0.45, cx + rx * 0.45, y + s * 0.3 - 0.25, y + s * 0.3 + 0.25, -0.6, h * 0.62), "dmetal", 0)


def jet(p, x, y, giro, rol_cola):
    m = Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(giro, 4, "Z")
    prof = [(0.0, -20.0), (1.6, -19.0), (2.6, -16.5), (3.0, -12.0), (3.0, 12.0), (2.4, 16.5), (1.2, 20.0), (0.3, 21.0)]
    p.add(lathe(prof, 10, m @ Matrix.Translation((0, 0, 4.6)) @ Matrix.Rotation(math.radians(-90), 4, "X"), cap0=False, cap1=True), lambda c, n: "white", 40)
    ala = [(-2.0, -3.0), (2.0, -3.0), (17.0, 3.0), (17.0, 5.5), (2.0, 4.0), (-2.0, 4.0), (-17.0, 5.5), (-17.0, 3.0)]
    p.add(I["prism"](ala, 0.5, m @ Matrix.Translation((0, 0, 3.4))), "white", 0)
    girar = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    p.add(I["prism"]([(13.5, 5.5), (20.5, 5.5), (22.0, 14.5), (19.0, 14.5)], 0.6, m @ girar), rol_cola, 0)
    p.add(I["prism"]([(-6.5, 17.0), (6.5, 17.0), (6.5, 19.5), (-6.5, 20.5)], 0.4, m @ Matrix.Translation((0, 0, 6.2))), "white", 0)
    for s in (-1, 1):
        p.add(lathe([(1.3, 0.0), (1.4, 2.0), (1.1, 5.0)], 8, m @ Matrix.Translation((s * 6.5, -3.0, 2.2)) @ Matrix.Rotation(math.radians(-90), 4, "X"), cap0=True, cap1=True), "metal", 40)
    for yy in (-12.0, 8.0):
        p.add(palo(tuple(m @ Vector((0, yy, -0.5))), tuple(m @ Vector((0, yy, 1.9))), 0.3, 5), "dmetal", 0)


def muneco(p, x, y):
    for r, z in ((2.2, 1.6), (1.6, 4.6), (1.15, 6.9)):
        copa(p, x, y, z, r, r * 0.95, "snow", 10, 7)
    p.add(lathe([(0.25, 0.0), (0.0, 1.6)], 6, Matrix.Translation((x - 1.0, y, 7.0)) @ Matrix.Rotation(math.radians(-90), 4, "Y"), cap0=True, cap1=False), "carrot", 30)
    p.add(cyl(1.1, 0.25, (x, y, 7.85), seg=10), "black", 20)
    p.add(cyl(0.75, 1.3, (x, y, 8.05), seg=10), "black", 20)
    for k in range(3):
        copa(p, x - 1.55, y + 0.1, 3.8 + k * 0.8 + 0.4, 0.22, 0.22, "black", 6, 4)
    for s in (-1, 1):
        p.add(palo((x, y + s * 1.4, 5.0), (x - 0.3, y + s * 3.6, 6.6), 0.13, 4), "dwood", 0)


def tejado_dos_aguas(x0, x1, y0, y1, z0, alto, vuelo=0.8, grosor=0.6):
    xa, xb, ya, yb = x0 - vuelo, x1 + vuelo, y0 - vuelo, y1 + vuelo
    ym = (y0 + y1) / 2
    pts = [(ya, z0 - grosor), (ym, z0 + alto - grosor), (yb, z0 - grosor), (yb, z0), (ym, z0 + alto), (ya, z0)]
    m = Matrix.Translation((xa, 0, 0)) @ Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    return I["prism"]([(u, v) for u, v in pts], xb - xa, m, z0=0.0)


def cabana_nieve(p, x0, x1, y0, y1, h, rol_muro="cabin"):
    p.add(caja(x0, x1, y0, y1, -0.6, h), rol_muro, 0)
    p.add(tejado_dos_aguas(x0, x1, y0, y1, h, (y1 - y0) * 0.38), lambda c, n: "snow" if n.z > 0.3 else "roofred", 0)
    for k in range(int((x1 - x0) / 7)):
        wx = x0 + 3.5 + k * 7
        for y, s in ((y0, -1), (y1, 1)):
            p.add(caja(wx - 1.2, wx + 1.2, y + s * 0.05 - 0.2, y + s * 0.05 + 0.2, h * 0.35, h * 0.75), "yellow", 0)


def palmeras_borde(p, rnd, xs, ys, paso, alto=(13, 19), prob=1.0):
    for x in xs:
        y = ys[0]
        while y <= ys[1]:
            if rnd.random() < prob:
                palmera(p, rnd, x + rnd.uniform(-4, 4), y + rnd.uniform(-6, 6), rnd.uniform(*alto), 1.0, 6)
            y += paso * rnd.uniform(0.8, 1.2)


def selva_borde(p, rnd, xs, ys, paso, s=(1.2, 1.7)):
    for x in xs:
        y = ys[0]
        while y <= ys[1]:
            arbol_selva(p, rnd, x + rnd.uniform(-5, 5), y + rnd.uniform(-6, 6), rnd.uniform(*s))
            y += paso * rnd.uniform(0.8, 1.2)


def franja(p, s, ys, columnas, rol, ang=45):
    bm = bmesh.new()
    filas = []
    for y in ys:
        filas.append([bm.verts.new((s * x, y, z)) for x, z in columnas(y)])
    for a, b in zip(filas, filas[1:]):
        for i in range(len(a) - 1):
            q = (a[i], a[i + 1], b[i + 1], b[i])
            bm.faces.new(q if s > 0 else q[::-1])
    p.add(bm, rol, ang)


def ondas(x, y, f):
    return math.sin(y / 19.0 + x / 23.0 + f[0]) * math.cos(x / 17.0 - y / 31.0 + f[1]) + 0.6 * math.sin(y / 7.3 + x * 0.21 + f[2])


def avioneta(p, x, y, giro, rol):
    m = Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(giro, 4, "Z")
    prof = [(0.0, -7.5), (1.3, -7.0), (1.6, -4.0), (1.5, 2.0), (0.8, 7.0), (0.2, 8.5)]
    p.add(lathe(prof, 8, m @ Matrix.Translation((0, 0, 3.4)) @ Matrix.Rotation(math.radians(-90), 4, "X"), cap0=False, cap1=True), rol, 40)
    p.add(I["prism"]([(-9.5, -3.0), (9.5, -3.0), (9.5, 0.2), (-9.5, 0.2)], 0.35, m @ Matrix.Translation((0, 0, 5.1))), "cream", 0)
    girar = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    p.add(I["prism"]([(6.0, 3.6), (8.6, 3.6), (8.9, 6.6), (7.6, 6.6)], 0.3, m @ girar), rol, 0)
    p.add(I["prism"]([(-3.0, 6.6), (3.0, 6.6), (3.0, 8.2), (-3.0, 8.2)], 0.3, m @ Matrix.Translation((0, 0, 3.8))), "cream", 0)
    p.add(I["prism"]([(-0.25, -3.2), (0.25, -3.2), (0.25, 3.2), (-0.25, 3.2)], 0.2, m @ Matrix.Translation((0, -7.75, 3.4)) @ Matrix.Rotation(math.radians(90), 4, "X")), "dmetal", 0)
    for sx in (-1, 1):
        p.add(palo(tuple(m @ Vector((sx * 1.2, -3.0, 2.2))), tuple(m @ Vector((sx * 2.0, -3.0, -0.4))), 0.15, 4), "dmetal", 0)
        p.add(cyl(0.7, 0.5, tuple(m @ Vector((sx * 2.2, -3.0, 0.2))), (0, 90, math.degrees(giro)), seg=8, center=True), "black", 30)


def calavera(p, x, y):
    p.add(palo((x, y, -0.6), (x, y, 4.0), 0.18, 4), "dwood", 0)
    copa(p, x, y - 0.2, 4.5, 0.9, 0.75, "bone", 8, 5)
    for s in (-1, 1):
        p.add(tube([(x + s * 0.6, y - 0.1, 4.8), (x + s * 1.8, y - 0.2, 5.2), (x + s * 2.4, y - 0.3, 6.1)], lambda u: 0.26 * (1 - 0.7 * u), 5, 2, caps=True, cap_rings=1), "bone", 40)
        copa(p, x + s * 0.35, y - 0.95, 4.65, 0.22, 0.22, "black", 6, 4)


def pino_simple(p, x, y, h, r, rot=0.0):
    p.add(lathe([(r, -0.6), (r * 0.5, h * 0.5), (0.0, h)], 6, Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(rot, 4, "Z"), cap0=False, cap1=False),
          lambda c, n, h=h: "snow" if c.z > h * 0.52 else ("pine2" if n.z < 0.25 else "pine"), 30)


def p_aeropuerto_jungla():
    p = Prop("AeropuertoJungla", None, 12000)
    rnd = random.Random(61)
    X, Y = 150.0, 900.0
    rs = []
    for k, y in enumerate(range(-900, 900, 60)):
        if k % 2:
            rs.append((-X, X, y, y + 60, "grass2"))
    rs += [(55, 145, -165, 95, "dirt"), (20, 55, -36, -12, "dirt"), (60, 100, -230, -165, "dirt"), (-20, 20, -600, 600, "dirt")]
    rs += [(-10, -6, -580, 580, "dirt2"), (6, 10, -580, 580, "dirt2")]
    for s in (-1, 1):
        y0 = s * 600 - (30 if s > 0 else 0)
        for k in range(5):
            bx = -16 + k * 7.5
            rs.append((bx, bx + 3.5, min(y0, y0 + 30), max(y0, y0 + 30), "mark"))
    losa(p, rs, "grass", -X, X, -Y, Y, borde="grass")
    for s in (-1, 1):
        for y in range(-580, 600, 40):
            p.add(caja(s * 22 - 0.9, s * 22 + 0.9, y - 0.9, y + 0.9, -0.3, 1.2), "white", 0)
    for x, y, r in ((86, -132, 8.0), (124, -100, 6.5), (94, -52, 9.0), (130, -8, 7.0), (88, 46, 6.5), (126, 70, 7.5)):
        choza(p, x, y, r, 6.0 + r * 0.3)
    torre_vigia(p, 62, 118, 17.0)
    avioneta(p, 80, -200, math.radians(160), "orange")
    manga(p, -40, 320, 11.0)
    manga(p, -40, -320, 11.0)
    for k in range(9):
        cajon(p, 60 + (k % 3) * 2.6, -10 + (k // 3) * 2.6, 1.2, "wood")
    for k in range(6):
        barril(p, 64 + k * 1.8, 22, ["red", "teal", "yellow"][k % 3])
    for x, y in ((50, -70), (58, 94), (140, -150), (44, 150), (110, 20), (142, 40), (70, -100)):
        palmera(p, rnd, x, y, rnd.uniform(17, 22), 1.1, 6)
    palmeras_borde(p, rnd, [-134], (-880, 880), 120, (18, 24), prob=0.8)
    palmeras_borde(p, rnd, [138], (180, 880), 120, (18, 24), prob=0.8)
    palmeras_borde(p, rnd, [138], (-880, -260), 120, (18, 24), prob=0.8)
    return p


def p_borde_jungla():
    p = Prop("BordeJungla", None, 12000)
    rnd = random.Random(71)
    ys = [-1000.0 + 25.0 * k for k in range(81)]
    for s in (-1, 1):
        f = [rnd.uniform(0, 6.28) for _ in range(6)]

        def borde(y, f=f):
            return 154.0 + 6.0 * math.sin(y / 37.0 + f[3]) + 4.0 * math.sin(y / 13.0 + f[4])

        def columnas(y, f=f):
            xe = borde(y)
            cols = [(146.0, -1.6), (xe, -1.0), (xe + 4, 9.0), (xe + 10, 21.0)]
            for dx in (25, 45, 70, 100, 135, 165):
                x = xe + dx
                cols.append((x, 27.0 + 5.0 * ondas(x, y, f) + 3.0 * math.sin(x / 41.0 + f[5])))
            cols += [(338.0, 12.0), (346.0, -1.6)]
            return cols

        def rol(c, n, f=f):
            if n.z < 0.45:
                return "jleaf2" if c.z > 10 else "jdark"
            h = c.z + 3.0 * math.sin(abs(c.x) / 9.0 + c.y / 11.0 + f[0])
            return "jlime" if h > 33 else ("jleaf3" if h > 29 else ("jleaf" if h > 24 else "jleaf2"))
        franja(p, s, ys, columnas, rol, 50)
        y = -990.0
        while y < 990:
            r = rnd.uniform(9, 13)
            copa(p, s * (borde(y) + rnd.uniform(5, 9)), y, 13 + r * 0.3, r, r * 0.95, rnd.choice(["jleaf", "jleaf2", "jleaf3", "palm"]), 7, 4)
            y += rnd.uniform(24, 34)
        for k in range(17):
            y = rnd.uniform(-980, 980)
            x = borde(y) + rnd.uniform(20, 160)
            r = rnd.uniform(10, 16)
            copa(p, s * x, y, 30 + r * 0.25, r, r * 0.7, rnd.choice(["jleaf3", "jleaf", "palm", "jlime"]), 8, 5)
        for k in range(5):
            y = rnd.uniform(-900, 900)
            palmera(p, rnd, s * (borde(y) + rnd.uniform(6, 14)), y, rnd.uniform(34, 42), 1.6, 6)
    return p


def p_aeropuerto_nieve():
    p = Prop("AeropuertoNieve", None, 12000)
    rnd = random.Random(62)
    X, Y = 150.0, 900.0
    rs = []
    rs.append((-30, 30, -620, 620, "snow2"))
    rs += [(-24, 24, -610, 610, "asphalt"), (24, 70, -14, 14, "asphalt"), (62, 148, -130, 90, "asphalt2")]
    rs += franjas_pista(-24, 24, -610, 610, 1.2, "mark", True, 6)
    rs += [(24, 70, -0.6, 0.6, "yellow"), (70, 140, -0.6, 0.6, "yellow")]
    losa(p, rs, "snow", -X, X, -Y, Y, borde="snow")
    for s in (-1, 1):
        y = -600.0
        while y < 600:
            L = rnd.uniform(40, 70)
            if s > 0 and y < 30 and y + L > -30:
                if y > -30:
                    y = 30.0
                    continue
                L = max(8.0, -30 - y)
            p.add(ellipsoid((rnd.uniform(3.0, 4.0), L / 2, rnd.uniform(2.0, 2.8)), Matrix.Translation((s * rnd.uniform(33, 36), y + L / 2, -0.4)), 8, 4), lambda c, n: "snow" if n.z > 0.45 else "snow3", 60)
            y += L + rnd.uniform(-2, 6)
        for y in range(-600, 601, 60):
            p.add(palo((s * 27.5, y, -0.4), (s * 27.5, y, 1.4), 0.22, 5), "dmetal", 0)
    cabana_nieve(p, 96, 146, -112, -70, 10.0)
    p.add(caja(132, 136, -96, -92, 13.0, 22.0), "rock2", 0)
    nave_arco(p, 90, 146, 12, 84, 21.0, "metal", "dmetal", "metal")
    p.add(cyl(7.0, 12, (128, 132, -0.6), seg=14), lambda c, n: "snow" if n.z > 0.5 else ("roofred" if int(c.z / 2.6) % 2 else "white"), 30)
    p.add(caja(70, 82, -168, -156, -0.6, 14), "cabin", 0)
    p.add(lathe([(8.0, 14.0), (8.8, 20.0)], 4, Matrix.Translation((76, -162, 0)) @ Matrix.Rotation(math.pi / 4, 4, "Z"), cap0=True, cap1=False), "glass", 0)
    p.add(caja(69, 83, -169, -155, 20, 21.4, True), lambda c, n: "snow" if n.z > 0.5 else "roofred", 0)
    muneco(p, 58, -60)
    muneco(p, 60, 110)
    manga(p, -40, 320, 11.0, "orange", "white")
    manga(p, -40, -320, 11.0, "orange", "white")
    for x, y in ((50, 160), (62, -220), (-60, -420), (-50, 480), (-90, 120), (100, 300)):
        p.add(I["blob"]((rnd.uniform(4, 7), rnd.uniform(3, 5), rnd.uniform(2.5, 4)), (x, y, 0.0), 1, 0.2, rnd.randint(0, 99)), lambda c, n: "snow" if n.z > 0.55 else "rock", 40)
    for k in range(18):
        x = rnd.choice([rnd.uniform(-140, -60), rnd.uniform(60, 145)])
        y = rnd.uniform(-880, 880)
        if x > 50 and -200 < y < 160:
            continue
        alto = rnd.uniform(18, 28)
        pino(p, rnd, x, y, alto, alto * 0.27, True, 2)
    return p


def p_borde_nieve():
    p = Prop("BordeNieve", None, 12000)
    rnd = random.Random(72)
    ys = [-1000.0 + 25.0 * k for k in range(81)]
    for s in (-1, 1):
        f = [rnd.uniform(0, 6.28) for _ in range(6)]

        def columnas(y, f=f):
            H = 95.0 + 35.0 * math.sin(y / 170.0 + f[0]) + 15.0 * math.sin(y / 61.0 + f[1])
            cols = [(208.0, -1.5), (213.0, 9.0)]
            for x in (235, 260, 285):
                cols.append((float(x), 11.0 + 2.5 * ondas(x, y, f)))
            cols += [(310.0, 14.0), (345.0, H * 0.45 + 6.0 * math.sin(y / 23.0 + f[2])), (380.0, H * 0.85), (402.0, H), (430.0, H * 0.7), (458.0, -1.5)]
            return cols

        def rol(c, n, f=f):
            if abs(c.x) < 312:
                return "snow" if (int(abs(c.x) / 9 + c.y / 13 + f[3]) % 3 == 0 and n.z > 0.7) else "pine2"
            if n.z < 0.5 and c.z > 40 and math.sin(c.y / 21.0 + f[4]) > 0.55:
                return "rock"
            return "snow" if n.z > 0.8 else ("snow2" if n.z > 0.6 else "snow3")
        franja(p, s, ys, columnas, rol, 35)
        for fila, x0 in ((0, 163.0), (2, 190.0)):
            y = -995.0 + fila * 7.0
            while y < 995:
                h = rnd.uniform(20, 32) * (1.12 if fila == 2 else 1.0)
                pino_simple(p, s * (x0 + rnd.uniform(-4, 4)), y + rnd.uniform(-4, 4), h, h * 0.3, rnd.uniform(0, 1))
                y += rnd.uniform(18, 26)
    return p


def p_aeropuerto_desierto():
    p = Prop("AeropuertoDesierto", None, 12000)
    rnd = random.Random(63)
    X, Y = 150.0, 900.0
    rs = []
    rs += [(-22, 22, -600, 600, "rwy"), (22, 64, -12, 12, "rwy"), (58, 148, -100, 120, "rwy")]
    rs += [(-12, -5, -600, -470, "rwy2"), (5, 12, -600, -470, "rwy2"), (-12, -5, 470, 600, "rwy2"), (5, 12, 470, 600, "rwy2")]
    rs += franjas_pista(-22, 22, -600, 600, 1.2, "bone", True, 5)
    for y, w, x1 in ((140, 16, 6), (-260, 22, 22), (380, 12, -4), (-470, 14, 10)):
        rs.append((-22, x1, y, y + w, "sand"))
    losa(p, rs, "dust", -X, X, -Y, Y, borde="dust")
    tx, ty = 106, -130
    p.add(loft(rectp(11, 11), [(1, 1, -0.6, tx, ty), (1, 1, 30, tx, ty), (0.92, 0.92, 30.5, tx, ty)], tapa=False), lambda c, n: "orange" if (19 < c.z < 22.5 or 8 < c.z < 11.5) else "bone", 0)
    p.add(loft(rectp(12, 12), [(0.843, 0.843, 30.5, tx, ty), (1.35, 1.35, 38.5, tx, ty)], tapa=False), "dglass", 0)
    p.add(loft(rectp(19, 19), [(1, 1, 38.5, tx, ty), (1, 1, 40.0, tx, ty), (0.6, 0.6, 41.4, tx, ty)], tapa=True, base=True), lambda c, n: "dmetal" if n.z < 0.5 else "red", 0)
    p.add(palo((tx, ty, 41.3), (tx, ty, 50.0), 0.22, 4), "metal", 0)
    p.add(ellipsoid((0.9, 0.9, 0.9), Matrix.Translation((tx, ty, 50.0)), 8, 5), "red", 60)
    p.add(caja(tx - 8, tx + 8, ty + 4.5, ty + 18, -0.6, 6.1), "tan", 0)
    p.add(caja(tx - 8.8, tx + 8.8, ty + 4.9, ty + 18.8, 6.0, 7.0, True), "redrock", 0)
    nave_arco(p, 82, 142, 8, 92, 22.0, "metal", "rwy2", "tan")
    wx, wy = 72, 190
    for lx, ly in ((-4, -4), (4, -4), (4, 4), (-4, 4)):
        p.add(palo((wx + lx * 1.25, wy + ly * 1.25, -0.6), (wx + lx, wy + ly, 20), 0.4, 5), "dmetal", 0)
    p.add(cyl(6.2, 8, (wx, wy, 20), seg=12), lambda c, n: "teal" if n.z < 0.5 else "metal", 30)
    p.add(lathe([(6.7, 28.0), (0.0, 31.5)], 12, Matrix.Translation((wx, wy, 0)), cap0=True, cap1=False), "dmetal", 30)
    manga(p, -40, -320, 11.0, "orange", "white")
    manga(p, -40, 320, 11.0, "orange", "white")
    calavera(p, 52, -60)
    calavera(p, -46, 140)
    for k in range(6):
        barril(p, 66 + (k % 3) * 1.8, -60 + (k // 3) * 1.8, ["red", "orange", "dmetal"][k % 3])
    for k in range(5):
        cajon(p, 70 + k * 2.6, 130, 1.2, "wood")
    for k in range(18):
        x = rnd.choice([rnd.uniform(-144, -40), rnd.uniform(40, 144)])
        y = rnd.uniform(-880, 880)
        if 45 < x < 150 and -180 < y < 220:
            continue
        saguaro(p, rnd, x, y, rnd.uniform(10, 16), rnd.uniform(1.1, 1.4))
    for k in range(22):
        x = rnd.choice([rnd.uniform(-144, -35), rnd.uniform(35, 144)])
        y = rnd.uniform(-880, 880)
        if 45 < x < 150 and -180 < y < 220:
            continue
        roca_desierto(p, rnd, x, y, rnd.uniform(2, 7), rnd.uniform(1.5, 6))
    return p


def p_borde_desierto():
    p = Prop("BordeDesierto", None, 12000)
    rnd = random.Random(73)
    ys = [-1000.0 + 20.0 * k for k in range(101)]
    for s in (-1, 1):
        f = [rnd.uniform(0, 6.28) for _ in range(6)]

        def pared(y, f=f):
            return 205.0 + 14.0 * math.sin(y / 61.0 + f[0]) + 7.0 * math.sin(y / 23.0 + f[1]) + 4.0 * math.sin(y / 9.0 + f[2])

        def alto(y, f=f):
            return 72.0 + 16.0 * math.sin(y / 140.0 + f[3])

        def columnas(y):
            w, H = pared(y), alto(y)
            return [(158.0, -1.5), (w - 26, -1.0), (w - 10, 2.5), (w - 4, 7.0), (w, 0.3 * H), (w + 3, 0.34 * H), (w + 8, 0.36 * H), (w + 11, 0.66 * H),
                    (w + 15, 0.7 * H), (w + 18, 0.97 * H), (w + 24, H), (w + 80, H + 2.0), (372.0, H), (392.0, 0.4 * H), (402.0, -1.5)]

        def rol(c, n, f=f):
            H = alto(c.y)
            t = c.z / H
            if c.z < 3.0:
                return "sand2"
            if n.z > 0.8:
                return "tan" if t > 0.9 else "redrock3"
            if t < 0.3:
                return "redrock2"
            if t < 0.38:
                return "redrock3"
            if t < 0.66:
                return "redrock"
            if t < 0.73:
                return "redrock3"
            return "redrock2" if int(c.z / 7.0) % 2 else "redrock"
        franja(p, s, ys, columnas, rol, 25)
        for k in range(7):
            y = rnd.uniform(-950, 950)
            x = pared(y) - rnd.uniform(14, 30)
            H = rnd.uniform(24, 48)
            r = rnd.uniform(5, 8)
            pts = contorno(9, rnd, (0.15, 0.08, 0.04))
            niveles = [(r * 1.5, r * 1.4, -1.5, s * x, y), (r * 1.1, r, H * 0.3, s * x, y), (r * 0.9, r * 0.85, H * 0.55, s * x, y), (r * 1.05, r, H * 0.62, s * x, y), (r * 0.8, r * 0.75, H, s * x, y)]
            p.add(loft(pts, niveles, tapa=True), lambda c, n, H=H: "redrock3" if n.z > 0.6 else ["redrock", "redrock3", "redrock2"][int(c.z / (H / 5)) % 3], 25)
        for k in range(10):
            y = rnd.uniform(-980, 980)
            roca_desierto(p, rnd, s * (pared(y) - rnd.uniform(8, 40)), y, rnd.uniform(3, 8), rnd.uniform(2, 7))
    return p


def p_aeropuerto_ciudad():
    p = Prop("AeropuertoCiudad", None, 14000)
    rnd = random.Random(64)
    X, Y = 260.0, 900.0
    rs = []
    for k, y in enumerate(range(-900, 900, 48)):
        if k % 2:
            rs.append((-X, X, y, y + 48, "grass2"))
    rs += [(-30, 30, -660, 660, "asphalt")]
    rs += [(95, 119, -640, 640, "asphalt2"), (30, 95, -632, -608, "asphalt2"), (30, 95, -12, 12, "asphalt2"), (30, 95, 608, 632, "asphalt2"), (119, 215, -330, 330, "concrete")]
    rs += [(106.4, 107.6, -630, 630, "yellow"), (30, 106.4, -620.6, -619.4, "yellow"), (30, 106.4, -0.6, 0.6, "yellow"), (30, 106.4, 619.4, 620.6, "yellow")]
    rs += franjas_pista(-30, 30, -660, 660, 1.6, "mark", True, 8, 40)
    for s in (-1, 1):
        for d in (150, 230, 300):
            for xs in (-17, 9):
                y = s * (660 - d)
                rs.append((xs, xs + 8, min(y, y + s * 22), max(y, y + s * 22), "mark"))
        y = s * (660 - 190)
        for xs in (-22, 14):
            rs.append((xs, xs + 8, min(y, y + s * 50), max(y, y + s * 50), "mark"))
    for k in range(-300, 301, 120):
        rs.append((130, 205, k - 0.4, k + 0.4, "yellow"))
    rs += [(150, 250, 380, 620, "asphalt2"), (140, 250, -620, -400, "concrete"), (250, 260, -900, 900, "asphalt2")]
    for k in range(380, 620, 12):
        rs.append((160, 196, k, k + 0.5, "mark"))
        rs.append((204, 240, k, k + 0.5, "mark"))
    losa(p, rs, "grass", -X, X, -Y, Y, borde="grass")
    tx0, tx1 = 222.0, 250.0

    def rol_term(c, n):
        if n.z > 0.5:
            return "roofg"
        if n.x < -0.5 and 3.0 < c.z < 19.0:
            return "glass" if int(c.z / 4.0) % 2 else "dglass"
        return "bldg1"
    p.add(loft(rectp(tx1 - tx0, 600), [(1, 1, -0.6, (tx0 + tx1) / 2, 0), (1, 1, 22, (tx0 + tx1) / 2, 0)], tapa=True), rol_term, 0)
    p.add(I["prism"]([(tx0 - 10 + (tx1 - tx0 + 10) * k / 8, 22.6 + 6.5 * math.sin(math.pi * k / 8)) for k in range(9)] + [(tx0 - 10 + (tx1 - tx0 + 10) * k / 8, 22.0 + 6.5 * math.sin(math.pi * k / 8)) for k in range(8, -1, -1)],
                     620, Matrix.Translation((0, -310, 0)) @ Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))), z0=0.0),
          lambda c, n: "teal" if n.z > 0.2 else "white", 0)
    for y in (-210.0, -70.0, 70.0, 210.0):
        p.add(caja(196, tx0 + 0.3, y - 2.5, y + 2.5, 6.0, 10.5), lambda c, n: "metal" if n.z < 0.5 else "concrete", 0)
        p.add(palo((198, y, -0.6), (198, y, 6.0), 0.5, 6), "dmetal", 0)
        jet(p, 172, y, math.radians(90), rnd.choice(["orange", "teal", "purple", "red"]))
    cx, cy = 238.0, 340.0
    p.add(cyl(4.5, 66, (cx, cy, -0.6), seg=12, cap1=False, cap0=False), lambda c, n: "bldg1" if int(c.z / 8) % 4 else "orange", 30)
    p.add(lathe([(4.5, 65.0), (9.5, 67.0), (10.5, 73.0)], 12, Matrix.Translation((cx, cy, 0)), cap0=True, cap1=False), "concrete", 20)
    p.add(lathe([(10.5, 73.0), (10.0, 79.0)], 12, Matrix.Translation((cx, cy, 0)), cap0=False, cap1=False), "dglass", 20)
    p.add(lathe([(11.6, 79.0), (11.6, 80.2), (5.0, 81.8), (0.0, 82.0)], 12, Matrix.Translation((cx, cy, 0)), cap0=True, cap1=False), "teal", 20)
    p.add(palo((cx, cy, 81.8), (cx, cy, 92.0), 0.25, 5), "metal", 0)
    p.add(ellipsoid((0.9, 0.9, 0.9), Matrix.Translation((cx, cy, 92.0)), 8, 5), "red", 60)
    nave_arco(p, 150, 238, -600, -520, 30.0, "metal", "dmetal", "concrete")
    nave_arco(p, 150, 238, -500, -420, 26.0, "bldg2", "dmetal", "concrete")
    for k in range(380, 620, 12):
        for x0 in (162, 206):
            if rnd.random() < 0.6:
                c = rnd.choice(["red", "teal", "yellow", "white", "bldg2", "orange", "purple"])
                xx = x0 + rnd.uniform(2, 20)
                p.add(caja(xx, xx + 6.5, k + 2.5, k + 9.5, -0.3, 1.9), c, 0)
                p.add(caja(xx + 1.2, xx + 5.0, k + 3.2, k + 8.8, 1.9, 3.1), "glass", 0)
    for y in range(-880, 881, 40):
        for x in (-245, -215):
            if rnd.random() < 0.7:
                p.add(palo((x, y, -0.5), (x, y, 3.0), 0.45, 5), "trunk", 30)
                copa(p, x + rnd.uniform(-1, 1), y, 5.0, rnd.uniform(3.4, 4.6), rnd.uniform(2.8, 3.6), rnd.choice(["jleaf", "jleaf3", "grass2"]), 7, 4)
    for s in (-1, 1):
        for d in range(670, 711, 10):
            p.add(caja(-13, 13, s * d - 0.4, s * d + 0.4, -0.4, 1.4), "dmetal", 0)
        for y in range(-660, 661, 50):
            p.add(palo((s * 32.0, y, -0.4), (s * 32.0, y, 1.4), 0.22, 5), "dmetal", 0)
    manga(p, -60, -400)
    manga(p, -60, 400)
    return p


def p_borde_ciudad():
    p = Prop("BordeCiudad", None, 12000)
    rnd = random.Random(74)
    muros = ["bldg1", "bldg3", "bldg4", "bldg5", "bldg2", "concrete", "cream"]
    for s in (-1, 1):
        p.add(caja(s * 263.5 - 0.3, s * 263.5 + 0.3, -1000, 1000, -0.4, 3.2), "metal", 0)
        y = -985.0
        while y < 985:
            d = rnd.uniform(34, 52)
            for x0, x1, hmin, hmax in ((276, 322, 10, 30), (334, 432, 20, 70)):
                w = rnd.uniform(0.6, 0.9) * (x1 - x0)
                cx = (x0 + x1) / 2 + rnd.uniform(-1, 1) * ((x1 - x0) - w) / 2
                h = rnd.uniform(hmin, hmax)
                if rnd.random() < 0.12 and x0 > 300:
                    h *= 1.6
                edificio(p, s * cx, y + d / 2, w, d * rnd.uniform(0.7, 0.9), h, max(2, int(h / 13)), rnd.choice(muros), rnd.choice(["glass", "dglass"]),
                         rnd.choice(["roofg", "roofg", "teal", "roofred"]), 0.5)
            y += d + rnd.uniform(4, 10)
        for y in range(-980, 981, 90):
            p.add(palo((s * 270, y, -0.5), (s * 270, y, 3.0), 0.45, 5), "trunk", 30)
            copa(p, s * 270, y, 5.2, 3.8, 3.0, rnd.choice(["jleaf", "jleaf3"]), 7, 4)
    return p


def luces(nombre, mitad_x, Y, paso, extra=()):
    p = Prop(nombre, None, 3000)
    for s in (-1, 1):
        y = -Y
        while y <= Y + 0.01:
            p.add(caja(s * mitad_x - 0.55, s * mitad_x + 0.55, y - 0.55, y + 0.55, 1.4, 2.5, True), "yellow", 0)
            y += paso
    for x, y in extra:
        p.add(caja(x - 0.5, x + 0.5, y - 0.5, y + 0.5, 1.4, 2.4, True), "yellow", 0)
    return p


def p_luces_nieve():
    return luces("LucesNieve", 27.5, 600, 60, [(x, s * 616) for s in (-1, 1) for x in range(-20, 21, 5)])


def p_luces_ciudad():
    extra = []
    for s in (-1, 1):
        for d in range(670, 711, 10):
            for x in range(-12, 13, 4):
                extra.append((x, s * d))
        for x in range(-28, 29, 4):
            extra.append((x, s * 664))
    return luces("LucesCiudad", 32.0, 660, 50, extra)


PROPS = [p_selva, p_palmeral, p_cerro, p_pinar, p_montana1, p_montana2, p_mesa, p_agujas, p_cactus, p_torres, p_barrio,
         p_aeropuerto_jungla, p_borde_jungla, p_aeropuerto_nieve, p_borde_nieve, p_luces_nieve, p_aeropuerto_desierto, p_borde_desierto,
         p_aeropuerto_ciudad, p_borde_ciudad, p_luces_ciudad]
SIN_CENTRAR = {"AeropuertoJungla", "AeropuertoNieve", "AeropuertoDesierto", "AeropuertoCiudad", "LucesNieve", "LucesCiudad",
               "BordeJungla", "BordeNieve", "BordeDesierto", "BordeCiudad"}


def exportar(ob, separar=True):
    if separar:
        _SEP["separar_capas"](ob)
    C["exportar"](ob)


def caja_roblox(ob):
    vs = [v.co for v in ob.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return [round(-mx.x, 3), round(mn.z, 3), round(mn.y, 3)], [round(-mn.x, 3), round(mx.z, 3), round(mx.y, 3)]


def v3(v):
    return "Vector3.new(%s)" % ", ".join(("%.3f" % x).rstrip("0").rstrip(".") if abs(x) >= 5e-4 else "0" for x in v)


def escribir_luau(manifest):
    ruta_ids = os.path.join(OUT, "ids_subida.json")
    ids = json.load(open(ruta_ids, encoding="utf-8")) if os.path.exists(ruta_ids) else {}
    L = ["--!strict", "export type Caja = { minimo: Vector3, maximo: Vector3 }", "", "local Destinos = {}", "", "Destinos.IDS = {"]
    for e in manifest["piezas"]:
        if e["nombre"] in ids:
            L.append(f"\t{e['nombre']} = {ids[e['nombre']]},")
    L += ["} :: { [string]: number }", "", "Destinos.CAJAS = {"]
    for e in manifest["piezas"]:
        L.append(f"\t{e['nombre']} = {{ minimo = {v3(e['bbox_min'])}, maximo = {v3(e['bbox_max'])} }},")
    L += ["} :: { [string]: Caja }", "", "Destinos.COLORES = {"]
    for b in BIOMAS:
        r, g, bl = manifest["colores"][b]
        L.append(f"\t{b} = Color3.fromRGB({r}, {g}, {bl}),")
    L += ["} :: { [string]: Color3 }", "", "return Destinos"]
    with open(os.path.join(RAIZ, "src", "shared", "Destinos.luau"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("LUAU", len(ids), "ids")


def construir(solo):
    paleta = imagen_paleta()
    mat = C["material_imagen"]("Destinos_Paleta", paleta, "Closest")
    objs, piezas, colores = {}, [], {}
    for b in BIOMAS:
        for v in (1, 2):
            nombre = f"Suelo{b}{v}"
            if solo and nombre not in solo and b not in solo:
                continue
            img = PINTORES[b](v)
            media = img.reshape(-1, 3).mean(axis=0)
            colores.setdefault(b, []).append(media)
            ob = C["suelo"](nombre, C["guardar_imagen"](nombre, img))
            objs[nombre] = ob
            piezas.append((nombre, ob, 12, False))
            print("SUELO", nombre, flush=True)
    for f in PROPS:
        p = f()
        if solo and p.name not in solo:
            continue
        ob, tris = armar(p, mat, p.name not in SIN_CENTRAR)
        objs[p.name] = ob
        piezas.append((p.name, ob, tris, True))
        print("PIEZA %-20s tris %6d / %6d %s" % (p.name, tris, p.budget, "OK" if tris <= p.budget else "PASADO"), flush=True)
    return objs, piezas, {b: [int(round(255 * x)) for x in np.mean(c, axis=0)] for b, c in colores.items()}


def leer_manifest():
    ruta = os.path.join(OUT, "manifest.json")
    ruta_c = os.path.join(OUT, "colores.json")
    piezas = json.load(open(ruta, encoding="utf-8")) if os.path.exists(ruta) else []
    colores = json.load(open(ruta_c, encoding="utf-8")) if os.path.exists(ruta_c) else {}
    return {"piezas": piezas if isinstance(piezas, list) else piezas.get("piezas", []), "colores": colores}


def main():
    if arg("--solo-luau"):
        escribir_luau(leer_manifest())
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    solo = arg("--only")
    solo = set(solo.split(",")) if isinstance(solo, str) else None
    objs, piezas, colores = construir(solo)
    ruta = os.path.join(OUT, "manifest.json")
    previo = leer_manifest()
    nuevas = []
    for nombre, ob, tris, separar in piezas:
        if not arg("--no-export"):
            exportar(ob, separar)
        mn, mx = caja_roblox(ob)
        nuevas.append({"nombre": nombre, "archivo": nombre + ".fbx", "triangulos": tris, "bbox_min": mn, "bbox_max": mx})
    if not arg("--no-export"):
        hechos = {e["nombre"] for e in nuevas}
        manifest = {"piezas": [e for e in previo["piezas"] if e["nombre"] not in hechos] + nuevas, "colores": {**previo.get("colores", {}), **colores}}
        manifest["piezas"].sort(key=lambda e: e["nombre"])
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(manifest["piezas"], fh, ensure_ascii=False, indent=1)
        with open(os.path.join(OUT, "colores.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest["colores"], fh, ensure_ascii=False, indent=1)
        if all(b in manifest["colores"] for b in BIOMAS):
            escribir_luau(manifest)
    if arg("--no-render"):
        return
    import importlib.util
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("vista_destinos", os.path.join(OUT, "vista_destinos.py"))
    vista = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vista)
    vista.renderizar(objs, C, arg)


main()
