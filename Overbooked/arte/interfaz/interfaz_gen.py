import bpy
import json
import math
import os
import random
import sys

SALIDA = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

TINTA = "2A2420"
PAPEL = "FFF4E0"
PAPEL2 = "EFDDBD"
MANILA = "F2DCA8"
PIZARRA = "2E3342"
TIZA = "F3E7CF"
NARANJA = "F27B2B"
TURQUESA = "1FA6A0"
AMARILLO = "F6C445"
ROJO = "D9443A"
VERDE = "6DBE45"
CIELO = "8FD3F4"
BLANCO = "FFFFFF"
GRIS = "A9B0B8"
MARRON = "8A5A33"
ROSA = "F29BB2"
CREMA_OSC = "D9C29A"

MATS = {}
LIENZO = {"z": 0.0, "ox": 0.0, "oy": 0.0}


def rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def material(h, a=1.0):
    clave = (h, round(a, 3))
    if clave in MATS:
        return MATS[clave]
    m = bpy.data.materials.new("M%d" % len(MATS))
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    salida = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*lin(rgb(h)), 1.0)
    em.inputs[1].default_value = 1.0
    if a < 1.0:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mez = nt.nodes.new("ShaderNodeMixShader")
        mez.inputs[0].default_value = a
        nt.links.new(tr.outputs[0], mez.inputs[1])
        nt.links.new(em.outputs[0], mez.inputs[2])
        nt.links.new(mez.outputs[0], salida.inputs[0])
    else:
        nt.links.new(em.outputs[0], salida.inputs[0])
    MATS[clave] = m
    return m


def _poner(ob, h, a):
    ob.data.materials.append(material(h, a))
    ob.location = (LIENZO["ox"], LIENZO["oy"], LIENZO["z"])
    LIENZO["z"] += 0.01
    bpy.context.scene.collection.objects.link(ob)
    return ob


def relleno(lazos, h, a=1.0):
    cu = bpy.data.curves.new("r", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    for pts in lazos:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for p, (x, y) in zip(sp.points, pts):
            p.co = (x, y, 0.0, 1.0)
        sp.use_cyclic_u = True
    return _poner(bpy.data.objects.new("r", cu), h, a)


def tira(izq, der, h, a=1.0):
    me = bpy.data.meshes.new("t")
    n = len(izq)
    vs = [(x, y, 0.0) for x, y in izq] + [(x, y, 0.0) for x, y in der]
    me.from_pydata(vs, [], [(i, i + 1, n + i + 1, n + i) for i in range(n - 1)])
    return _poner(bpy.data.objects.new("t", me), h, a)


class Ruido:
    def __init__(self, semilla, armonicos=6):
        r = random.Random(semilla)
        self.c = [(k, r.uniform(0, 2 * math.pi), r.uniform(0.5, 1.0) / k) for k in range(1, armonicos + 1)]

    def __call__(self, t):
        return 0.55 * sum(a * math.sin(2 * math.pi * k * t + f) for k, f, a in self.c)


def largo(pts, cerrado):
    P = pts + [pts[0]] if cerrado else pts
    return sum(math.dist(P[i], P[i + 1]) for i in range(len(P) - 1))


def remuestrear(pts, paso, cerrado):
    P = pts + [pts[0]] if cerrado else list(pts)
    total = largo(pts, cerrado)
    n = max(4, int(total / paso))
    salida = []
    acum = [0.0]
    for i in range(len(P) - 1):
        acum.append(acum[-1] + math.dist(P[i], P[i + 1]))
    j = 0
    rango = n if cerrado else n + 1
    for k in range(rango):
        d = total * k / n
        while j < len(P) - 2 and acum[j + 1] < d:
            j += 1
        seg = acum[j + 1] - acum[j]
        t = 0.0 if seg < 1e-9 else (d - acum[j]) / seg
        salida.append((P[j][0] + (P[j + 1][0] - P[j][0]) * t, P[j][1] + (P[j + 1][1] - P[j][1]) * t))
    return salida


def normales(pts, cerrado):
    n = len(pts)
    out = []
    for i in range(n):
        a = pts[(i - 1) % n] if cerrado or i > 0 else pts[i]
        b = pts[(i + 1) % n] if cerrado or i < n - 1 else pts[i]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        out.append((-dy / L, dx / L))
    return out


def temblar(pts, amp, semilla, cerrado=True, paso=3.0):
    q = remuestrear(pts, paso, cerrado)
    nn = normales(q, cerrado)
    r = Ruido(semilla)
    n = len(q)
    return [(x + nx * amp * r(i / n), y + ny * amp * r(i / n)) for i, ((x, y), (nx, ny)) in enumerate(zip(q, nn))]


def trazo(pts, ancho, h=TINTA, cerrado=False, semilla=1, var=0.35, amp=None, a=1.0, afilar=True):
    amp = ancho * 0.22 if amp is None else amp
    q = temblar(pts, amp, semilla, cerrado)
    if cerrado:
        q = q + [q[0]]
    nn = normales(q, False) if not cerrado else normales(q[:-1], True) + [normales(q[:-1], True)[0]]
    r = Ruido(semilla + 101, 4)
    n = len(q)
    izq, der = [], []
    for i, ((x, y), (nx, ny)) in enumerate(zip(q, nn)):
        t = i / max(1, n - 1)
        w = ancho * (1.0 + var * r(t))
        if not cerrado and afilar:
            w *= min(1.0, (t / 0.14) ** 0.6 if t < 0.14 else 1.0, ((1 - t) / 0.14) ** 0.6 if t > 0.86 else 1.0)
            w = max(w, ancho * 0.25)
        izq.append((x + nx * w / 2, y + ny * w / 2))
        der.append((x - nx * w / 2, y - ny * w / 2))
    return tira(izq, der, h, a)


def mover(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def rrect(x0, y0, x1, y1, r, n=6):
    r = min(r, (x1 - x0) / 2 - 0.01, (y1 - y0) / 2 - 0.01)
    pts = []
    for cx, cy, a0 in ((x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def elipse(cx, cy, rx, ry=None, n=48, giro=0.0, a0=0.0, a1=360.0):
    ry = rx if ry is None else ry
    g = math.radians(giro)
    out = []
    completo = abs(a1 - a0) >= 360.0
    pasos = n if completo else max(3, int(n * abs(a1 - a0) / 360.0))
    for k in range(pasos if completo else pasos + 1):
        a = math.radians(a0 + (a1 - a0) * k / pasos)
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * math.cos(g) - y * math.sin(g), cy + x * math.sin(g) + y * math.cos(g)))
    return out


def estrella(cx, cy, r0, r1, puntas=5, giro=90.0):
    out = []
    for k in range(puntas * 2):
        a = math.radians(giro + 180.0 * k / puntas)
        r = r0 if k % 2 == 0 else r1
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def suave(pts, cerrado=False, pasos=8):
    n = len(pts)
    out = []
    rango = n if cerrado else n - 1
    for i in range(rango):
        p0 = pts[(i - 1) % n] if cerrado or i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if cerrado or i + 2 < n else pts[min(i + 2, n - 1)]
        for k in range(pasos):
            t = k / pasos
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    if not cerrado:
        out.append(pts[-1])
    return out


def cortes(pts, p, d):
    res = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-9:
            continue
        t = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den
        u = ((a[0] - p[0]) * d[1] - (a[1] - p[1]) * d[0]) / den
        if 0 <= u < 1:
            res.append(t)
    return sorted(res)


def rayado(pts, separacion, ancho, h, angulo=45.0, zona=None, semilla=3, margen=3.0):
    d = (math.cos(math.radians(angulo)), math.sin(math.radians(angulo)))
    nrm = (-d[1], d[0])
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    R = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    k = -R
    i = 0
    while k <= R:
        p = (cx + nrm[0] * k - d[0] * R, cy + nrm[1] * k - d[1] * R)
        ts = cortes(pts, p, d)
        for j in range(0, len(ts) - 1, 2):
            t0, t1 = ts[j] + margen, ts[j + 1] - margen
            if t1 - t0 < 4:
                continue
            a = (p[0] + d[0] * t0, p[1] + d[1] * t0)
            b = (p[0] + d[0] * t1, p[1] + d[1] * t1)
            if zona and not (zona(a) or zona(b)):
                continue
            if zona:
                seg = [a, b]
                dentro = [q for q in (a, b) if zona(q)]
                if len(dentro) == 1:
                    lo, hi = (0.0, 1.0)
                    for _ in range(14):
                        m = (lo + hi) / 2
                        q = (a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m)
                        if zona(q) == zona(a):
                            lo = m
                        else:
                            hi = m
                    q = (a[0] + (b[0] - a[0]) * lo, a[1] + (b[1] - a[1]) * lo)
                    seg = [a, q] if zona(a) else [q, b]
                a, b = seg
            if math.dist(a, b) > 4:
                trazo([a, b], ancho, h, semilla=semilla + i, var=0.25, amp=0.4)
            i += 1
        k += separacion


def pieza(pts, fill, ancho=5.0, tinta=TINTA, semilla=1, desfase=(1.8, -1.8), sombra=None, amp=None, rayas=None, brillo=None):
    if sombra:
        relleno([mover(temblar(pts, 0.6, semilla + 50), sombra[0], sombra[1])], TINTA, sombra[2] if len(sombra) > 2 else 1.0)
    if fill:
        relleno([mover(temblar(pts, ancho * 0.18, semilla + 9), desfase[0], desfase[1])], fill)
    if rayas:
        rayado(pts, rayas.get("sep", 7.0), rayas.get("ancho", 1.6), rayas.get("color", TINTA), rayas.get("angulo", 45.0), rayas.get("zona"), semilla + 20)
    if brillo:
        trazo(brillo, ancho * 0.7, BLANCO, semilla=semilla + 30, var=0.2)
    trazo(pts, ancho, tinta, cerrado=True, semilla=semilla, amp=amp)


def puntos(cx, cy, r, h=TINTA):
    relleno([elipse(cx, cy, r, r, 16)], h)


def escena(ancho, alto):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for col in (bpy.data.curves, bpy.data.meshes):
        for d in list(col):
            col.remove(d)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.samples = 24
    s.cycles.use_denoising = False
    try:
        s.cycles.filter_width = 1.2
    except Exception:
        pass
    s.render.film_transparent = True
    s.render.resolution_x, s.render.resolution_y = ancho, alto
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGBA"
    s.render.dither_intensity = 0.0
    s.view_settings.view_transform = "Standard"
    s.view_settings.look = "None"
    cam = bpy.data.cameras.new("Cam")
    cam.type = "ORTHO"
    cam.ortho_scale = max(ancho, alto)
    co = bpy.data.objects.new("Cam", cam)
    co.location = (ancho / 2, alto / 2, 50)
    s.collection.objects.link(co)
    s.camera = co
    LIENZO.update(z=0.0, ox=0.0, oy=0.0)


def guardar(nombre):
    s = bpy.context.scene
    s.render.filepath = os.path.join(SALIDA, nombre + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDER", nombre)


PANELES = {}


def panel(nombre, ancho, alto, corte, escala=0.5):
    def deco(f):
        PANELES[nombre] = {"f": f, "tam": [ancho, alto], "corte": corte, "escala": escala}
        return f
    return deco


@panel("Papel", 256, 256, [70, 70, 186, 186])
def p_papel():
    forma = rrect(22, 30, 226, 226, 30)
    pieza(forma, PAPEL, 7.0, semilla=11, sombra=(8, -9, 0.32), amp=2.4, rayas={"sep": 8, "ancho": 1.7, "color": CREMA_OSC, "zona": lambda q: q[0] < 70 and q[1] < 92})


@panel("Pizarra", 256, 256, [70, 70, 186, 186])
def p_pizarra():
    forma = rrect(22, 30, 226, 226, 30)
    pieza(forma, PIZARRA, 6.5, tinta=TIZA, semilla=21, sombra=(8, -9, 0.4), amp=2.4)
    rayado(rrect(30, 38, 218, 218, 24), 9, 1.4, "3C4254", 135.0, lambda q: q[0] > 180 and q[1] > 160, 5)


@panel("Billete", 640, 176, [80, 60, 470, 116])
def p_billete():
    x0, y0, x1, y1 = 18, 26, 616, 158
    xs, rn = 500, 13
    base = rrect(x0, y0, x1, y1, 22)
    n = 7
    forma = base[:n] + elipse(xs, y1, rn, rn, 20, 0, 0, -180) + base[n:2 * n] + base[2 * n:3 * n] + elipse(xs, y0, rn, rn, 20, 0, 180, 0) + base[3 * n:]
    pieza(forma, PAPEL, 6.5, semilla=31, sombra=(7, -8, 0.3), amp=2.0, rayas={"sep": 8, "ancho": 1.6, "color": CREMA_OSC, "zona": lambda q: q[0] < 90 and q[1] < 70})
    for k in range(8):
        y = y0 + rn + 10 + k * 12.0
        trazo([(xs, y), (xs, y + 6)], 3.2, TINTA, semilla=40 + k, var=0.2)
    relleno([temblar(rrect(x0 + 12, y1 - 16, xs - 26, y1 - 8, 3), 0.8, 63)], NARANJA)


@panel("Etiqueta", 320, 256, [120, 64, 270, 192])
def p_etiqueta():
    forma = suave_esquinas([(82, 30), (296, 30), (296, 226), (82, 226), (26, 170), (26, 86)], 14)
    agujero = elipse(66, 128, 10, 10, 24)
    relleno([mover(temblar(forma, 0.6, 91), 8, -9), mover(agujero, 8, -9)], TINTA, 0.32)
    relleno([mover(temblar(forma, 1.3, 50), 1.8, -1.8), agujero], MANILA)
    rayado(forma, 8, 1.7, "D8BE86", 45.0, lambda q: q[1] < 70 and q[0] > 220, 61)
    relleno([elipse(66, 128, 17, 17, 28), agujero], "D8BE86")
    trazo(forma, 7.0, TINTA, cerrado=True, semilla=41, amp=2.2)
    trazo(elipse(66, 128, 17, 17, 28), 5.0, TINTA, cerrado=True, semilla=43)
    trazo(agujero, 3.5, TINTA, cerrado=True, semilla=44)


def suave_esquinas(pts, r):
    out = []
    n = len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        da = math.dist(a, b)
        dc = math.dist(b, c)
        k1 = min(r, da / 2) / da
        k2 = min(r, dc / 2) / dc
        p1 = (b[0] + (a[0] - b[0]) * k1, b[1] + (a[1] - b[1]) * k1)
        p2 = (b[0] + (c[0] - b[0]) * k2, b[1] + (c[1] - b[1]) * k2)
        for k in range(6):
            t = k / 5
            q0 = (p1[0] + (b[0] - p1[0]) * t, p1[1] + (b[1] - p1[1]) * t)
            q1 = (b[0] + (p2[0] - b[0]) * t, b[1] + (p2[1] - b[1]) * t)
            out.append((q0[0] + (q1[0] - q0[0]) * t, q0[1] + (q1[1] - q0[1]) * t))
    return out


def roto(x0, y0, x1, y1, semilla, dientes=18, alto=5.0):
    r = random.Random(semilla)
    arriba = [(x0 + (x1 - x0) * k / dientes, y1 + (alto if k % 2 else 0) * r.uniform(0.4, 1.0)) for k in range(dientes + 1)]
    abajo = [(x1 - (x1 - x0) * k / dientes, y0 - (alto if k % 2 else 0) * r.uniform(0.4, 1.0)) for k in range(dientes + 1)]
    return arriba[::-1][::-1] + [(x1, (y0 + y1) / 2)] + abajo + [(x0, (y0 + y1) / 2)]


def nota(color, semilla):
    def f():
        forma = roto(20, 30, 362, 104, semilla)
        pieza(forma, PAPEL, 5.5, semilla=semilla, sombra=(6, -7, 0.3), amp=0.8)
        cinta = [(10, 78), (62, 88), (66, 54), (14, 44)]
        relleno([temblar(cinta, 1.0, semilla + 3)], color, 0.88)
        trazo([(14, 44), (10, 78)], 2.4, TINTA, semilla=semilla + 4, var=0.3)
        trazo([(62, 88), (66, 54)], 2.4, TINTA, semilla=semilla + 5, var=0.3)
    return f


for _n, _c, _s in (("NotaInfo", TURQUESA, 51), ("NotaPeligro", ROJO, 52), ("NotaBien", VERDE, 53)):
    PANELES[_n] = {"f": nota(_c, _s), "tam": [384, 128], "corte": [80, 40, 340, 92], "escala": 0.5}


@panel("Boton", 256, 112, [44, 36, 212, 76])
def p_boton():
    forma = rrect(14, 22, 238, 98, 26)
    pieza(forma, BLANCO, 6.0, semilla=61, sombra=(5, -7, 0.45))
    trazo([(34, 80), (120, 84)], 4.0, "E6E6E6", semilla=62, var=0.3)


@panel("BarraFondo", 256, 64, [32, 20, 224, 44])
def p_barra_fondo():
    forma = rrect(10, 14, 246, 52, 19)
    pieza(forma, PAPEL2, 5.0, semilla=71, desfase=(0, 0))


@panel("BarraRelleno", 256, 64, [32, 20, 224, 44])
def p_barra_relleno():
    forma = rrect(14, 18, 242, 48, 15)
    relleno([temblar(forma, 0.8, 72)], BLANCO)
    rayado(forma, 9, 2.0, "E2E2E2", 60.0, None, 73, 1.0)


@panel("Burbuja", 176, 192, [88, 120, 89, 121], 1.0)
def p_burbuja():
    cuerpo = suave([(88, 184), (150, 166), (168, 112), (150, 62), (106, 46), (84, 18), (82, 46), (34, 60), (10, 112), (28, 166)], True, 6)
    pieza(cuerpo, BLANCO, 6.0, semilla=81, sombra=(6, -7, 0.3))


@panel("Mira", 64, 64, [31, 31, 33, 33], 1.0)
def p_mira():
    trazo(elipse(32, 32, 9, 9, 24), 4.2, TINTA, cerrado=True, semilla=91)
    trazo(elipse(32, 32, 9, 9, 24), 2.0, BLANCO, cerrado=True, semilla=92, var=0.1)
    puntos(32, 32, 2.6, BLANCO)


@panel("Sello", 256, 256, [127, 127, 129, 129], 1.0)
def p_sello():
    trazo(elipse(128, 128, 110, 110, 64), 9.0, BLANCO, cerrado=True, semilla=93)
    trazo(elipse(128, 128, 92, 92, 64), 4.0, BLANCO, cerrado=True, semilla=94)
    for k in range(12):
        a = 2 * math.pi * k / 12
        trazo([(128 + 98 * math.cos(a), 128 + 98 * math.sin(a)), (128 + 104 * math.cos(a), 128 + 104 * math.sin(a))], 3.0, BLANCO, semilla=95 + k)


ICONOS = []


def icono(nombre):
    def deco(f):
        ICONOS.append((nombre, f))
        return f
    return deco


def cara(fill, semilla):
    pieza(elipse(64, 62, 46, 44, 48), fill, 5.0, semilla=semilla, brillo=elipse(64, 62, 34, 32, 12, 0, 110, 160))


@icono("Hamburguesa")
def i_hamburguesa():
    pieza(rrect(22, 26, 106, 46, 9), "E8A65A", 4.6, semilla=1)
    pieza(rrect(18, 46, 110, 60, 7), "7A4A2A", 4.6, semilla=2)
    pieza([(20, 62), (108, 62), (96, 52), (80, 60), (64, 50), (48, 60), (32, 52)], AMARILLO, 3.6, semilla=3)
    pieza(suave([(18, 64), (30, 70), (42, 64), (54, 70), (66, 64), (78, 70), (90, 64), (102, 70), (112, 64)], False, 4) + [(108, 60), (20, 60)], VERDE, 3.6, semilla=4)
    pieza(elipse(64, 70, 46, 34, 40, 0, 0, 180) + [(18, 70)], "F0B566", 4.8, semilla=5, brillo=elipse(64, 70, 34, 24, 10, 0, 110, 150))
    for x, y in ((44, 90), (60, 96), (76, 92), (88, 82), (52, 80)):
        relleno([elipse(x, y, 3.4, 2.2, 10, 30)], PAPEL)


@icono("Cafe")
def i_cafe():
    trazo(elipse(92, 62, 14, 16, 24, 0, -90, 90), 6.0, TINTA, semilla=11)
    pieza([(28, 92), (100, 92), (90, 30), (38, 30)], BLANCO, 5.0, semilla=12)
    relleno([[(34, 60), (94, 60), (91, 44), (37, 44)]], NARANJA)
    relleno([elipse(64, 90, 34, 6, 24)], MARRON)
    pieza(rrect(22, 18, 106, 30, 6), PAPEL2, 4.2, semilla=13)
    for x in (52, 70):
        trazo(suave([(x, 98), (x + 6, 106), (x - 2, 114), (x + 4, 122)], False, 6), 3.6, GRIS, semilla=x)


@icono("Agua")
def i_agua():
    gota = suave([(64, 116), (86, 78), (92, 56), (82, 30), (64, 22), (46, 30), (36, 56), (42, 78)], True, 6)
    pieza(gota, CIELO, 5.0, semilla=21, brillo=[(52, 44), (48, 58), (52, 72)])


@icono("Feliz")
def i_feliz():
    cara(AMARILLO, 31)
    trazo(elipse(46, 70, 8, 7, 12, 0, 20, 160), 4.4, TINTA, semilla=32)
    trazo(elipse(82, 70, 8, 7, 12, 0, 20, 160), 4.4, TINTA, semilla=33)
    trazo(elipse(64, 54, 22, 16, 20, 0, 200, 340), 4.6, TINTA, semilla=34)
    relleno([elipse(36, 52, 7, 4, 12)], ROSA, 0.85)
    relleno([elipse(92, 52, 7, 4, 12)], ROSA, 0.85)


@icono("Enfado")
def i_enfado():
    cara("E8653C", 41)
    trazo([(34, 84), (56, 74)], 5.0, TINTA, semilla=42)
    trazo([(94, 84), (72, 74)], 5.0, TINTA, semilla=43)
    puntos(48, 66, 4.6)
    puntos(80, 66, 4.6)
    trazo(elipse(64, 34, 18, 12, 16, 0, 30, 150), 4.6, TINTA, semilla=44)


@icono("Miedo")
def i_miedo():
    cara("BFE3EE", 51)
    for x in (48, 80):
        pieza(elipse(x, 70, 10, 12, 20), BLANCO, 3.6, semilla=x)
        puntos(x, 70, 3.6)
    pieza(elipse(64, 38, 10, 8, 18), "6B3A3A", 3.6, semilla=52)
    pieza(suave([(102, 96), (108, 84), (104, 76), (98, 82)], True, 5), CIELO, 3.0, semilla=53)


@icono("Alborotador")
def i_alborotador():
    cara("B5D86A", 61)
    for x, s in ((46, 1), (82, -1)):
        pts = [(x + s * 0.9 * t * math.cos(t), 70 + 0.9 * t * math.sin(t)) for t in [k * 0.35 for k in range(26)]]
        trazo(pts, 3.2, TINTA, semilla=62 + x)
    trazo(elipse(64, 40, 20, 10, 16, 0, 200, 340), 4.4, TINTA, semilla=63)
    pieza(suave([(62, 34), (76, 34), (78, 20), (70, 14), (62, 20)], True, 5), ROSA, 3.4, semilla=64)


@icono("Mareo")
def i_mareo():
    pts = [(64 + 1.5 * t * math.cos(t), 64 + 1.5 * t * math.sin(t)) for t in [k * 0.3 for k in range(48)]]
    trazo(pts, 4.4, TINTA, semilla=71)
    for cx, cy, r in ((26, 98, 13), (100, 104, 11), (104, 30, 12)):
        pieza(estrella(cx, cy, r, r * 0.45), AMARILLO, 3.4, semilla=cx)


@icono("Saciado")
def i_saciado():
    cara(AMARILLO, 81)
    trazo(elipse(46, 72, 8, 6, 12, 0, 200, 340), 4.4, TINTA, semilla=82)
    trazo(elipse(82, 72, 8, 6, 12, 0, 200, 340), 4.4, TINTA, semilla=83)
    trazo(elipse(64, 50, 20, 12, 18, 0, 200, 340), 4.6, TINTA, semilla=84)
    pieza(suave([(70, 42), (84, 44), (86, 32), (76, 28)], True, 5), ROSA, 3.4, semilla=85)


@icono("Golpe")
def i_golpe():
    for k, (sx, sy) in enumerate(((-1, 1), (1, 1), (1, -1), (-1, -1))):
        cx, cy = 64 + sx * 40, 64 + sy * 40
        a = math.degrees(math.atan2(-sy, -sx))
        arco = elipse(cx, cy, 30, 30, 16, 0, a - 38, a + 38)
        trazo(arco, 17.0, TINTA, semilla=91 + k, var=0.15)
        trazo(arco, 10.0, ROJO, semilla=95 + k, var=0.15, amp=0.6)


@icono("Casco")
def i_casco():
    escudo = suave([(64, 116), (104, 102), (102, 60), (84, 30), (64, 16), (44, 30), (26, 60), (24, 102)], True, 6)
    pieza(escudo, TURQUESA, 5.0, semilla=101, rayas={"sep": 7, "ancho": 1.6, "color": "178580", "zona": lambda q: q[0] > 64})
    trazo([(64, 98), (64, 34)], 6.0, PAPEL, semilla=102, var=0.2)
    trazo([(40, 74), (88, 74)], 6.0, PAPEL, semilla=103, var=0.2)


@icono("Motor")
def i_motor():
    pieza(elipse(64, 64, 48, 48, 48), GRIS, 5.0, semilla=111)
    pieza(elipse(64, 64, 36, 36, 40), "5A6270", 3.6, semilla=112)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        b = a + math.radians(60)
        aspa = [(64, 64), (64 + 34 * math.cos(a), 64 + 34 * math.sin(a)), (64 + 30 * math.cos(b), 64 + 30 * math.sin(b))]
        pieza(aspa, PAPEL, 3.4, semilla=113 + k)
    pieza(elipse(64, 64, 9, 9, 16), NARANJA, 3.4, semilla=117)


@icono("Fuego")
def i_fuego():
    llama = suave([(62, 120), (82, 92), (96, 70), (98, 46), (84, 22), (64, 14), (42, 20), (30, 42), (32, 66), (44, 80), (50, 66), (56, 92)], True, 6)
    pieza(llama, NARANJA, 5.0, semilla=121)
    dentro = suave([(64, 78), (76, 60), (80, 42), (70, 26), (58, 26), (48, 38), (50, 54), (58, 60)], True, 6)
    pieza(dentro, AMARILLO, 3.4, semilla=122, desfase=(0, 0))


@icono("Combustible")
def i_combustible():
    pieza(rrect(28, 16, 100, 100, 12), ROJO, 5.0, semilla=131, rayas={"sep": 7, "ancho": 1.6, "color": "B43328", "zona": lambda q: q[0] > 74})
    pieza(rrect(40, 100, 70, 116, 5), GRIS, 4.0, semilla=132)
    pieza(rrect(78, 96, 96, 112, 4), TINTA, 3.0, semilla=133)
    trazo([(40, 30), (88, 84)], 5.0, "F28A7E", semilla=134, var=0.2)
    trazo([(40, 84), (88, 30)], 5.0, "F28A7E", semilla=135, var=0.2)


@icono("Cinturon")
def i_cinturon():
    pieza(rrect(10, 50, 118, 78, 6), TURQUESA, 4.4, semilla=141)
    pieza(rrect(40, 36, 88, 92, 12), GRIS, 5.0, semilla=142)
    pieza(rrect(52, 48, 76, 80, 6), "5A6270", 3.4, semilla=143)


@icono("Reloj")
def i_reloj():
    pieza(rrect(54, 102, 74, 118, 4), GRIS, 4.0, semilla=151)
    pieza(elipse(64, 58, 44, 44, 48), PAPEL, 5.2, semilla=152, rayas={"sep": 7, "ancho": 1.5, "color": CREMA_OSC, "zona": lambda q: q[0] > 74 and q[1] < 50})
    trazo([(64, 58), (64, 88)], 5.0, TINTA, semilla=153)
    trazo([(64, 58), (84, 48)], 5.0, NARANJA, semilla=154)
    puntos(64, 58, 4.4)


def girar(pts, ang, c=(64, 64), esc=1.0, d=(0, 0)):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + d[0] + esc * ((x - c[0]) * ca - (y - c[1]) * sa), c[1] + d[1] + esc * ((x - c[0]) * sa + (y - c[1]) * ca)) for x, y in pts]


def dibujar_avion(T, semilla, grosor=1.0):
    cuerpo = suave([(14, 66), (30, 74), (100, 74), (116, 68), (116, 60), (100, 56), (30, 56), (14, 60)], True, 4)
    pieza(T([(54, 66), (78, 66), (60, 108), (48, 108)]), TURQUESA, 4.0 * grosor, semilla=semilla)
    pieza(T([(54, 62), (78, 62), (60, 22), (48, 22)]), TURQUESA, 4.0 * grosor, semilla=semilla + 1)
    pieza(T([(18, 66), (30, 66), (22, 92), (14, 92)]), NARANJA, 3.6 * grosor, semilla=semilla + 2)
    pieza(T(cuerpo), PAPEL, 4.6 * grosor, semilla=semilla + 3)
    trazo(T([(96, 68), (108, 66)]), 3.4 * grosor, CIELO, semilla=semilla + 4)


@icono("Avion")
def i_avion():
    dibujar_avion(lambda p: p, 161)


@icono("Moneda")
def i_moneda():
    pieza(elipse(64, 64, 46, 46, 48), AMARILLO, 5.2, semilla=171, rayas={"sep": 7, "ancho": 1.6, "color": "D9A72E", "zona": lambda q: q[0] > 72 and q[1] < 56})
    trazo(elipse(64, 64, 32, 32, 40), 3.4, "C9952A", cerrado=True, semilla=172)
    trazo([(64, 46), (64, 82)], 6.0, "C9952A", semilla=173, var=0.2)
    trazo(elipse(64, 64, 38, 38, 16, 0, 110, 160), 4.0, BLANCO, semilla=174)


@icono("Estrella")
def i_estrella():
    pieza(estrella(64, 62, 52, 22), AMARILLO, 5.0, semilla=181, brillo=[(52, 82), (60, 96)])


@icono("EstrellaVacia")
def i_estrella_vacia():
    pieza(estrella(64, 62, 52, 22), "D7CDBB", 5.0, semilla=182)


@icono("Maleta")
def i_maleta():
    trazo(suave([(48, 92), (50, 108), (64, 112), (78, 108), (80, 92)], False, 5), 6.0, TINTA, semilla=191)
    pieza(rrect(18, 22, 110, 94, 14), NARANJA, 5.2, semilla=192, rayas={"sep": 7, "ancho": 1.6, "color": "C65E1A", "zona": lambda q: q[0] > 86})
    for x in (44, 84):
        trazo([(x, 26), (x, 90)], 5.0, "A84E15", semilla=193 + x, var=0.2)
    for x in (32, 96):
        pieza(elipse(x, 16, 7, 7, 14), TINTA, 2.0, semilla=194 + x, desfase=(0, 0))


@icono("Caja")
def i_caja():
    pieza([(20, 24), (88, 24), (88, 84), (20, 84)], "D9A866", 5.0, semilla=201)
    pieza([(20, 84), (88, 84), (108, 100), (40, 100)], "E9C083", 4.6, semilla=202)
    pieza([(88, 24), (108, 40), (108, 100), (88, 84)], "B98848", 4.6, semilla=203)
    relleno([[(48, 84), (60, 84), (80, 100), (68, 100)]], "F2DCA8")
    trazo([(30, 58), (50, 58)], 3.4, TINTA, semilla=204)
    trazo([(30, 48), (60, 48)], 3.4, TINTA, semilla=205)


@icono("Fragil")
def i_fragil():
    copa = suave([(30, 112), (98, 112), (94, 78), (78, 62), (50, 62), (34, 78)], True, 5)
    trazo([(64, 62), (64, 24)], 6.0, TINTA, semilla=211)
    pieza(rrect(38, 14, 90, 26, 6), BLANCO, 4.4, semilla=212)
    pieza(copa, BLANCO, 5.0, semilla=213)
    relleno([suave([(34, 92), (94, 92), (92, 80), (78, 66), (50, 66), (36, 80)], True, 5)], "B3243A")


@icono("Cocodrilo")
def i_cocodrilo():
    arriba = suave([(10, 70), (30, 90), (60, 100), (96, 92), (120, 74), (116, 64), (10, 64)], True, 4)
    abajo = suave([(14, 58), (116, 58), (112, 46), (80, 34), (40, 36), (16, 48)], True, 4)
    pieza(abajo, "4E9A3D", 4.6, semilla=221)
    for x in range(30, 112, 14):
        relleno([[(x, 64), (x + 7, 64), (x + 3.5, 54)]], BLANCO)
        relleno([[(x + 7, 58), (x + 14, 58), (x + 10.5, 66)]], BLANCO)
    pieza(arriba, VERDE, 5.0, semilla=222)
    pieza(elipse(42, 98, 12, 12, 20), "4E9A3D", 4.0, semilla=223)
    pieza(elipse(42, 100, 6, 7, 14), AMARILLO, 2.6, semilla=224)
    puntos(43, 100, 2.6)
    for x, y in ((90, 80), (104, 76)):
        puntos(x, y, 2.4)


@icono("Paracaidas")
def i_paracaidas():
    cupula = elipse(64, 76, 52, 40, 40, 0, 0, 180) + [(12, 76)]
    pieza(cupula, ROJO, 5.0, semilla=231)
    for x0, x1 in ((30, 46), (82, 98)):
        relleno([[(x0, 77), (x1, 77), (x1 - 2, 110), (x0 + 4, 106)]], BLANCO)
    for x in (16, 40, 64, 88, 112):
        trazo([(x, 76), (64, 30)], 2.6, TINTA, semilla=232 + x, var=0.2)
    pieza(rrect(52, 12, 76, 32, 4), MARRON, 4.0, semilla=239)


@icono("Altavoz")
def i_altavoz():
    pieza([(16, 50), (38, 50), (64, 26), (64, 102), (38, 78), (16, 78)], GRIS, 5.0, semilla=241)
    for r, s in ((20, 242), (34, 243)):
        trazo(elipse(66, 64, r, r, 16, 0, -50, 50), 5.0, TINTA, semilla=s)


@icono("Pasajero")
def i_pasajero():
    pieza(elipse(64, 34, 40, 28, 32, 0, 0, 180) + [(24, 34)], TURQUESA, 5.0, semilla=251)
    pieza(elipse(64, 80, 22, 24, 32), "F2C9A0", 5.0, semilla=252)


@icono("Llave")
def i_llave():
    pieza(suave([(40, 46), (90, 96), (100, 90), (50, 38)], True, 3), GRIS, 4.6, semilla=261)
    pieza(suave([(16, 28), (24, 12), (48, 10), (58, 32), (46, 52), (30, 44), (36, 32), (28, 24)], True, 4), GRIS, 4.6, semilla=262)
    aro = elipse(98, 96, 7, 7, 14)
    relleno([mover(elipse(98, 96, 16, 16, 24), 1.5, -1.5), aro], GRIS)
    trazo(elipse(98, 96, 16, 16, 24), 4.6, TINTA, cerrado=True, semilla=263)
    trazo(aro, 3.4, TINTA, cerrado=True, semilla=264)


@icono("Extintor")
def i_extintor():
    pieza(rrect(40, 12, 84, 92, 18), ROJO, 5.2, semilla=271, rayas={"sep": 7, "ancho": 1.6, "color": "B43328", "zona": lambda q: q[0] > 68})
    pieza(rrect(50, 92, 74, 104, 4), GRIS, 4.0, semilla=272)
    pieza([(50, 104), (92, 112), (92, 104), (70, 104)], TINTA, 3.4, semilla=273)
    trazo(suave([(74, 100), (100, 98), (106, 76), (100, 56)], False, 6), 5.0, TINTA, semilla=274)
    pieza(rrect(46, 44, 78, 64, 4), PAPEL, 3.4, semilla=275)


@icono("Aduana")
def i_aduana():
    pieza(elipse(64, 102, 16, 14, 24), MARRON, 4.6, semilla=281)
    pieza(rrect(56, 56, 72, 92, 4), MARRON, 4.4, semilla=282)
    pieza(rrect(24, 30, 104, 58, 8), TURQUESA, 5.0, semilla=283)
    pieza(rrect(20, 14, 108, 30, 4), TINTA, 3.4, semilla=284)


@icono("Alarma")
def i_alarma():
    pieza(rrect(22, 14, 106, 32, 6), GRIS, 4.4, semilla=291)
    pieza(elipse(64, 32, 34, 50, 32, 0, 0, 180) + [(30, 32)], ROJO, 5.0, semilla=292, brillo=[(50, 50), (52, 66)])
    for a in (150, 115, 65, 30):
        r = math.radians(a)
        trazo([(64 + 56 * math.cos(r), 40 + 56 * math.sin(r)), (64 + 70 * math.cos(r), 40 + 70 * math.sin(r))], 5.0, AMARILLO, semilla=293 + a)


@icono("Pirata")
def i_pirata():
    for a, b in (((18, 18), (110, 52)), ((18, 52), (110, 18))):
        trazo([a, b], 15.0, TINTA, semilla=301 + int(a[1]), var=0.15, afilar=False)
        trazo([a, b], 8.0, PAPEL, semilla=305 + int(a[1]), var=0.15, amp=0.5, afilar=False)
        for p in (a, b):
            pieza(elipse(p[0], p[1], 7, 7, 14), PAPEL, 3.6, semilla=307 + int(p[0]), desfase=(0, 0))
    pieza(suave([(64, 116), (98, 106), (106, 78), (90, 54), (84, 40), (44, 40), (38, 54), (22, 78), (30, 106)], True, 5), PAPEL, 5.0, semilla=303)
    for x in (48, 80):
        pieza(elipse(x, 78, 11, 12, 20), TINTA, 2.0, semilla=x, desfase=(0, 0))
    relleno([[(60, 60), (68, 60), (64, 68)]], TINTA)


@icono("Trofeo")
def i_trofeo():
    for s in (-1, 1):
        trazo(elipse(64 + s * 38, 92, 14, 14, 16, 0, -90 if s > 0 else 90, 90 if s > 0 else 270), 5.0, TINTA, semilla=311 + s)
    pieza(suave([(30, 114), (98, 114), (92, 70), (76, 54), (52, 54), (36, 70)], True, 5), AMARILLO, 5.0, semilla=313, brillo=[(44, 100), (46, 80)])
    pieza(rrect(56, 30, 72, 56, 4), "D9A72E", 4.0, semilla=314)
    pieza(rrect(36, 12, 92, 30, 5), MARRON, 4.4, semilla=315)


@icono("Medalla")
def i_medalla():
    pieza([(30, 120), (52, 120), (72, 70), (54, 64)], ROJO, 4.4, semilla=321)
    pieza([(98, 120), (76, 120), (56, 70), (74, 64)], TURQUESA, 4.4, semilla=322)
    pieza(elipse(64, 46, 32, 32, 36), AMARILLO, 5.0, semilla=323, brillo=elipse(64, 46, 22, 22, 10, 0, 110, 160))
    pieza(estrella(64, 46, 16, 7), "D9A72E", 2.6, semilla=324, desfase=(0, 0))


@icono("Billete")
def i_billete():
    forma = rrect(10, 34, 118, 94, 8)
    pieza(forma, PAPEL, 5.0, semilla=331)
    relleno([rrect(16, 76, 84, 88, 3)], NARANJA)
    for k in range(5):
        trazo([(92, 40 + k * 11), (92, 46 + k * 11)], 2.6, TINTA, semilla=332 + k)
    for y in (64, 52):
        trazo([(20, y), (70, y)], 3.0, GRIS, semilla=340 + y)


@icono("Aterrizaje")
def i_aterrizaje():
    pieza(rrect(6, 12, 122, 30, 5), "5A6270", 4.4, semilla=341)
    for x in (22, 50, 78, 106):
        trazo([(x - 8, 21), (x + 4, 21)], 3.4, BLANCO, semilla=342 + x, var=0.2)
    dibujar_avion(lambda p: girar(p, -22, (64, 64), 0.74, (4, 22)), 343, 0.85)
    for k in range(3):
        trazo([(18 + k * 6, 104 - k * 12), (34 + k * 6, 96 - k * 12)], 3.0, GRIS, semilla=349 + k)


@icono("Cerrar")
def i_cerrar():
    trazo([(30, 30), (98, 98)], 13.0, ROJO, semilla=351, var=0.25)
    trazo([(30, 98), (98, 30)], 13.0, ROJO, semilla=352, var=0.25)


@icono("Tick")
def i_tick():
    trazo(suave([(18, 64), (46, 32), (110, 104)], False, 6), 13.0, VERDE, semilla=361, var=0.3)


@icono("Casilla")
def i_casilla():
    pieza(rrect(18, 18, 110, 110, 14), PAPEL, 6.0, semilla=371)


@icono("Luna")
def i_luna():
    fuera = elipse(64, 64, 48, 48, 48, 0, 60, 300)
    dentro = elipse(86, 64, 42, 42, 32, 0, -87, -273)
    pieza(fuera + dentro, "F6E3A0", 5.0, semilla=381)


@icono("Niebla")
def i_niebla():
    nube = suave([(22, 56), (20, 76), (40, 88), (56, 104), (82, 102), (96, 86), (110, 80), (110, 58)], True, 5)
    pieza(nube, "E4ECF0", 5.0, semilla=391)
    for y, x0, x1 in ((40, 14, 92), (26, 34, 114)):
        trazo([(x0, y), (x1, y)], 6.0, GRIS, semilla=392 + y)


@icono("Diamante")
def i_diamante():
    pieza([(64, 14), (116, 74), (96, 98), (32, 98), (12, 74)], CIELO, 5.0, semilla=401)
    trazo([(12, 74), (116, 74)], 3.4, TINTA, semilla=402)
    trazo([(44, 98), (64, 74), (84, 98)], 3.0, TINTA, semilla=403)
    trazo([(40, 74), (64, 16), (88, 74)], 3.0, TINTA, semilla=404)
    trazo([(34, 88), (44, 96)], 4.0, BLANCO, semilla=405)


@icono("Diana")
def i_diana():
    for r, c, s in ((50, ROJO, 411), (36, BLANCO, 412), (22, ROJO, 413), (9, BLANCO, 414)):
        pieza(elipse(64, 60, r, r, 40), c, 4.4, semilla=s, desfase=(0, 0))
    trazo([(64, 60), (114, 110)], 5.0, MARRON, semilla=415)
    pieza([(104, 112), (118, 118), (112, 104)], NARANJA, 3.0, semilla=416)


@icono("Bandeja")
def i_bandeja():
    pieza(rrect(10, 26, 118, 38, 6), GRIS, 4.6, semilla=421)
    pieza(elipse(64, 38, 44, 48, 40, 0, 0, 180) + [(20, 38)], "D8DDE2", 5.0, semilla=422, brillo=elipse(64, 38, 32, 36, 10, 0, 110, 150))
    pieza(elipse(64, 90, 8, 6, 16), GRIS, 3.6, semilla=423)


@icono("Corazon")
def i_corazon():
    corazon = [(64 + 40 * (16 * math.sin(t) ** 3) / 16, 62 + 40 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16) for t in [2 * math.pi * k / 48 for k in range(48)]]
    pieza(corazon, ROJO, 5.0, semilla=431, brillo=[(40, 80), (44, 92)])


@icono("Platano")
def i_platano():
    fuera = elipse(64, 92, 54, 62, 28, 0, 196, 344)
    dentro = elipse(66, 104, 46, 50, 28, 0, 338, 202)
    pieza(fuera + dentro, AMARILLO, 5.0, semilla=441, rayas={"sep": 6, "ancho": 1.5, "color": "D9A72E", "zona": lambda q: q[1] < 52})
    pieza(rrect(6, 70, 20, 86, 4), MARRON, 3.4, semilla=442)
    trazo(elipse(64, 92, 46, 54, 14, 0, 230, 300), 3.0, "D9A72E", semilla=443)


@icono("Gorro")
def i_gorro():
    pieza(suave([(16, 50), (60, 44), (118, 40), (112, 30), (60, 28), (14, 40)], True, 4), "178580", 4.4, semilla=451)
    pieza(elipse(56, 48, 42, 46, 40, 0, 0, 180) + [(14, 48)], TURQUESA, 5.0, semilla=452, brillo=elipse(56, 48, 30, 34, 10, 0, 110, 150))
    pieza(elipse(56, 94, 6, 5, 12), NARANJA, 3.0, semilla=453)


@icono("Flecha")
def i_flecha():
    pieza([(64, 118), (110, 66), (82, 66), (82, 14), (46, 14), (46, 66), (18, 66)], VERDE, 5.4, semilla=461)


@icono("Info")
def i_info():
    pieza(elipse(64, 64, 48, 48, 48), TURQUESA, 5.0, semilla=471)
    trazo([(64, 34), (64, 70)], 11.0, BLANCO, semilla=472, var=0.15)
    puntos(64, 90, 7.0, BLANCO)


@icono("Peligro")
def i_peligro():
    pieza(suave_esquinas([(64, 116), (118, 18), (10, 18)], 12), AMARILLO, 5.4, semilla=481)
    trazo([(64, 90), (64, 50)], 11.0, TINTA, semilla=482, var=0.15)
    puntos(64, 34, 6.6)


@icono("Volante")
def i_volante():
    pieza(rrect(54, 10, 74, 50, 5), GRIS, 4.4, semilla=491)
    pieza(suave([(14, 98), (24, 60), (44, 48), (84, 48), (104, 60), (114, 98), (96, 100), (88, 72), (40, 72), (32, 100)], True, 4), "5A6270", 5.0, semilla=492)
    pieza(rrect(46, 52, 82, 70, 5), NARANJA, 3.6, semilla=493)


@icono("Radio")
def i_radio():
    trazo([(84, 92), (100, 122)], 5.0, TINTA, semilla=501)
    puntos(100, 122, 4.0, ROJO)
    pieza(rrect(14, 24, 114, 92, 12), TURQUESA, 5.2, semilla=502, rayas={"sep": 7, "ancho": 1.5, "color": "178580", "zona": lambda q: q[0] > 90})
    pieza(rrect(22, 34, 66, 82, 8), PAPEL2, 3.6, semilla=503)
    for y in (44, 56, 68):
        for x in (30, 42, 54):
            puntos(x, y, 2.6)
    pieza(elipse(88, 64, 14, 14, 24), PAPEL, 3.8, semilla=504)
    trazo([(88, 64), (96, 72)], 3.6, NARANJA, semilla=505)
    pieza(rrect(76, 32, 104, 42, 3), AMARILLO, 3.0, semilla=506)


@icono("Tronco")
def i_tronco():
    pieza(rrect(12, 40, 104, 88, 22), "9C6B3E", 5.0, semilla=511, rayas={"sep": 6, "ancho": 1.6, "color": "6E4A2B", "angulo": 0.0, "zona": lambda q: q[1] < 56})
    pieza(elipse(100, 64, 18, 24, 28), "E9C083", 5.0, semilla=512)
    trazo(elipse(100, 64, 10, 14, 20), 3.0, "9C6B3E", cerrado=True, semilla=513)
    puntos(100, 64, 2.6, "9C6B3E")
    trazo([(30, 76), (70, 78)], 3.0, "6E4A2B", semilla=514)


@icono("Bengala")
def i_bengala():
    pieza(rrect(52, 10, 76, 80, 8), ROJO, 5.0, semilla=521, rayas={"sep": 6, "ancho": 1.5, "color": "B43328", "zona": lambda q: q[0] > 66})
    pieza(rrect(48, 74, 80, 86, 4), BLANCO, 3.6, semilla=522)
    llama = suave([(64, 124), (80, 104), (78, 90), (64, 84), (50, 90), (48, 104)], True, 6)
    pieza(llama, NARANJA, 4.4, semilla=523)
    pieza(suave([(64, 112), (72, 100), (64, 90), (56, 100)], True, 5), AMARILLO, 3.0, semilla=524, desfase=(0, 0))
    for a in (40, 90, 140):
        r = math.radians(a)
        trazo([(64 + 30 * math.cos(r), 100 + 24 * math.sin(r)), (64 + 40 * math.cos(r), 100 + 32 * math.sin(r))], 3.4, AMARILLO, semilla=525 + a)


@icono("Coco")
def i_coco():
    pieza(elipse(64, 60, 46, 44, 40), "7A4A2A", 5.2, semilla=531, rayas={"sep": 6, "ancho": 1.6, "color": "5A3520", "zona": lambda q: q[0] > 70})
    for x, y in ((50, 78), (72, 80), (60, 64)):
        pieza(elipse(x, y, 6, 7, 14), "3E2414", 2.6, semilla=532 + x, desfase=(0, 0))
    trazo(elipse(64, 60, 36, 34, 14, 0, 110, 150), 4.0, "A87A55", semilla=536)


@icono("Cangrejo")
def i_cangrejo():
    for s in (-1, 1):
        for k in range(3):
            trazo([(64 + s * 26, 46 - k * 6), (64 + s * 50, 30 - k * 9)], 4.0, TINTA, semilla=541 + k + s * 10)
        trazo([(64 + s * 24, 66), (64 + s * 40, 90)], 4.4, TINTA, semilla=545 + s)
        pieza(suave([(64 + s * 40, 112), (64 + s * 54, 100), (64 + s * 50, 84), (64 + s * 36, 82), (64 + s * 30, 96), (64 + s * 42, 98)], True, 4), ROJO, 4.0, semilla=547 + s)
        trazo([(64 + s * 12, 70), (64 + s * 16, 92)], 3.4, TINTA, semilla=549 + s)
        pieza(elipse(64 + s * 16, 96, 6, 6, 12), BLANCO, 2.8, semilla=551 + s, desfase=(0, 0))
        puntos(64 + s * 16, 96, 2.4)
    pieza(elipse(64, 56, 36, 24, 36), ROJO, 5.2, semilla=553, brillo=elipse(64, 56, 26, 16, 10, 0, 110, 160))
    trazo(elipse(64, 56, 10, 6, 12, 0, 200, 340), 3.2, TINTA, semilla=554)


@icono("Hidroavion")
def i_hidroavion():
    for x in (42, 86):
        trazo([(x, 48), (x - 4, 30)], 3.4, TINTA, semilla=561 + x)
    pieza(suave([(14, 28), (24, 32), (112, 32), (118, 26), (104, 18), (20, 18)], True, 3), "F2DCA8", 4.0, semilla=563)
    dibujar_avion(lambda p: girar(p, 0, (64, 64), 0.9, (0, 4)), 564, 0.9)
    for k in range(3):
        trazo([(10 + k * 34, 12), (30 + k * 34, 12)], 3.0, CIELO, semilla=570 + k)


@icono("Palmera")
def i_palmera():
    tronco = suave([(56, 12), (60, 40), (66, 70), (74, 92)], False, 6)
    trazo(tronco, 11.0, TINTA, semilla=581, var=0.15, afilar=False)
    trazo(tronco, 6.0, "9C6B3E", semilla=582, var=0.15, amp=0.5, afilar=False)
    for a, l in ((160, 44), (120, 40), (70, 42), (30, 46), (200, 34), (-10, 34)):
        r = math.radians(a)
        punta = (74 + l * math.cos(r), 92 + l * math.sin(r) * 0.7)
        medio = (74 + l * 0.5 * math.cos(r), 92 + l * 0.5 * math.sin(r) * 0.7 + 10)
        pieza(suave([(74, 92), medio, punta, (medio[0], medio[1] - 9)], True, 4), VERDE, 3.6, semilla=583 + a)
    for x, y in ((70, 84), (80, 86)):
        pieza(elipse(x, y, 5, 5, 12), "7A4A2A", 2.6, semilla=590 + x, desfase=(0, 0))


@icono("Mano")
def i_mano():
    piel = "F2C9A0"
    for x, alto, s in ((36, 96, 601), (52, 108, 602), (68, 110, 603), (84, 100, 604)):
        pieza(rrect(x - 7, 52, x + 7, alto, 7), piel, 4.0, semilla=s)
    pieza(suave([(30, 64), (16, 78), (12, 70), (22, 54), (32, 46)], True, 4), piel, 4.0, semilla=605)
    pieza(rrect(28, 14, 94, 66, 18), piel, 5.0, semilla=606, rayas={"sep": 6, "ancho": 1.5, "color": "D9A57A", "zona": lambda q: q[0] > 74})
    for x in (40, 56, 72):
        trazo([(x, 60), (x + 4, 52)], 2.4, "C98F62", semilla=607 + x)
    pieza(rrect(26, 6, 96, 20, 6), TURQUESA, 3.6, semilla=611)


def atlas():
    escena(1024, 1024)
    manifiesto = {}
    for i, (nombre, f) in enumerate(ICONOS):
        cx, cy = i % 8, i // 8
        LIENZO["ox"], LIENZO["oy"] = cx * 128.0, (7 - cy) * 128.0
        f()
        manifiesto[nombre] = [cx * 128, cy * 128]
    LIENZO["ox"] = LIENZO["oy"] = 0.0
    guardar("Iconos")
    return manifiesto


def main():
    solo = None
    if "--solo" in ARGS:
        solo = set(ARGS[ARGS.index("--solo") + 1].split(","))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    datos = {"paneles": {}, "iconos": {}, "celda": 128}
    ruta = os.path.join(SALIDA, "manifest.json")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as fh:
            datos.update(json.load(fh))
    for nombre, p in PANELES.items():
        if solo and nombre not in solo:
            continue
        escena(*p["tam"])
        p["f"]()
        guardar(nombre)
        datos["paneles"][nombre] = {"tam": p["tam"], "corte": p["corte"], "escala": p["escala"]}
    if not solo or "Iconos" in solo:
        datos["iconos"] = atlas()
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=1)
    print("PANELES", len(PANELES), "ICONOS", len(ICONOS))


main()
