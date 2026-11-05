import bpy
import glob
import math
import os
import random

_AQUI = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(os.path.dirname(_AQUI), "interfaz", "interfaz_gen.py"), encoding="utf-8") as _fh:
    exec(_fh.read().rsplit("\nmain()", 1)[0], globals())
SALIDA = _AQUI

GRIS_CINTA = "C9C9C9"
GRIS_PLIEGUE = "8E8E8E"
GRIS_RAYA = "D2D2D2"
FUENTE = {}
IMAGENES = []


def imagen(nombre, ancho, alto):
    def deco(f):
        IMAGENES.append((nombre, ancho, alto, f))
        return f
    return deco


def fuente():
    if "f" not in FUENTE:
        if "--fuente" in ARGS:
            ruta = ARGS[ARGS.index("--fuente") + 1]
        else:
            patron = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Roblox", "Versions", "*", "content", "fonts", "LuckiestGuy-Regular.ttf")
            ruta = sorted(glob.glob(patron))[-1]
        FUENTE["f"] = bpy.data.fonts.load(ruta)
    return FUENTE["f"]


def bezier(sp, pasos=7):
    bp = sp.bezier_points
    n = len(bp)
    pts = []
    for i in range(n):
        a, b = bp[i], bp[(i + 1) % n]
        p0, p1, p2, p3 = a.co, a.handle_right, b.handle_left, b.co
        for k in range(pasos):
            t = k / pasos
            u = 1 - t
            pts.append(tuple(u * u * u * p0[j] + 3 * u * u * t * p1[j] + 3 * u * t * t * p2[j] + t * t * t * p3[j] for j in (0, 1)))
    return pts


def glifo(ch):
    cu = bpy.data.curves.new("g", "FONT")
    cu.body = ch
    cu.font = fuente()
    cu.size = 100
    ob = bpy.data.objects.new("g", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    curva = ob.evaluated_get(dg).to_curve(dg)
    lazos = [bezier(s) for s in curva.splines]
    bpy.data.objects.remove(ob, do_unlink=True)
    return lazos


def caja(lazos):
    xs = [p[0] for l in lazos for p in l]
    ys = [p[1] for l in lazos for p in l]
    return min(xs), min(ys), max(xs), max(ys)


def area(l):
    return sum(l[i][0] * l[(i + 1) % len(l)][1] - l[(i + 1) % len(l)][0] * l[i][1] for i in range(len(l))) / 2


def transformar(lazos, ang, esc, centro, destino):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [[(destino[0] + esc * ((x - centro[0]) * ca - (y - centro[1]) * sa), destino[1] + esc * ((x - centro[0]) * sa + (y - centro[1]) * ca)) for x, y in l] for l in lazos]


def componer(texto, alto, semilla, inclinacion=0.0, sep=-0.02, giro=6.0):
    rnd = random.Random(semilla)
    ref = caja(glifo("E"))
    k = alto / (ref[3] - ref[1])
    letras = []
    x = 0.0
    for ch in texto:
        lazos = [[(px * k, py * k) for px, py in l] for l in glifo(ch)]
        x0, _, x1, _ = caja(lazos)
        ancho = x1 - x0
        esc = rnd.uniform(0.96, 1.05)
        dy = rnd.uniform(-0.05, 0.05) * alto + (x + ancho / 2) * math.tan(math.radians(inclinacion))
        destino = (x + ancho * esc / 2, alto / 2 + dy)
        letras.append(transformar(lazos, rnd.uniform(-giro, giro), esc, ((x0 + x1) / 2, alto / 2), destino))
        x += ancho * esc + sep * alto
    return letras


def encajar(letras, ancho, alto, dx=0.0, dy=0.0):
    x0, y0, x1, y1 = caja([l for lazos in letras for l in lazos])
    mx, my = ancho / 2 - (x0 + x1) / 2 + dx, alto / 2 - (y0 + y1) / 2 + dy
    return [[mover(l, mx, my) for l in lazos] for lazos in letras]


def rayas(lazos, sep, ancho, color, angulo, zona, semilla):
    d = (math.cos(math.radians(angulo)), math.sin(math.radians(angulo)))
    nrm = (-d[1], d[0])
    x0, y0, x1, y1 = caja(lazos)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = math.hypot(x1 - x0, y1 - y0)
    k = -R
    i = 0
    while k <= R:
        p = (cx + nrm[0] * k - d[0] * R, cy + nrm[1] * k - d[1] * R)
        ts = sorted(t for l in lazos for t in cortes(l, p, d))
        for j in range(0, len(ts) - 1, 2):
            t0, t1 = ts[j] + 3.0, ts[j + 1] - 3.0
            tramo = []
            t = t0
            while t <= t1:
                q = (p[0] + d[0] * t, p[1] + d[1] * t)
                if zona(q):
                    tramo.append(q)
                elif tramo:
                    break
                t += 2.0
            if len(tramo) > 2 and math.dist(tramo[0], tramo[-1]) > 5:
                trazo([tramo[0], tramo[-1]], ancho, color, semilla=semilla + i, var=0.25, amp=0.4)
                i += 1
        k += sep


def brillo_letra(lazos, linea, semilla):
    fuera = max(lazos, key=lambda l: abs(area(l)))
    q = remuestrear(fuera, 4.0, True)
    signo = 1.0 if area(fuera) > 0 else -1.0
    nn = normales(q, True)
    o = linea * 1.9
    q = [(x + nx * o * signo, y + ny * o * signo) for (x, y), (nx, ny) in zip(q, nn)]
    x0, y0, x1, y1 = caja([q])
    dentro = [y > y1 - (y1 - y0) * 0.2 and x < x0 + (x1 - x0) * 0.5 for x, y in q]
    n = len(q)
    mejor, actual = [], []
    for i in range(2 * n):
        if dentro[i % n] and len(actual) < n:
            actual.append(q[i % n])
            if len(actual) > len(mejor):
                mejor = list(actual)
        else:
            actual = []
    if len(mejor) >= 4:
        trazo(mejor, linea * 1.2, BLANCO, semilla=semilla, var=0.2)


def rotulo(letras, estilos, alto, semilla):
    banda = alto * 0.15
    linea = max(5.0, alto * 0.034)
    prof = alto * 0.06
    sombra = (alto * 0.045, -alto * 0.06)
    pasos = 7
    for i, lazos in enumerate(letras):
        for d in ((sombra[0] + prof, sombra[1] - prof), (0, 0), (prof, -prof)):
            m = [mover(l, d[0], d[1]) for l in lazos]
            relleno(m, TINTA)
            for j, l in enumerate(m):
                trazo(l, banda + 2 * linea, TINTA, cerrado=True, semilla=semilla + i * 13 + j, var=0.1, amp=1.6)
    for i, lazos in enumerate(letras):
        for d in ((0, 0), (prof, -prof)):
            m = [mover(l, d[0], d[1]) for l in lazos]
            relleno(m, PAPEL)
            for j, l in enumerate(m):
                trazo(l, banda, PAPEL, cerrado=True, semilla=semilla + i * 17 + j, var=0.08, amp=1.0)
    for i, lazos in enumerate(letras):
        cara_, profundo, raya = estilos[i]
        s = semilla + 100 + i * 31
        for k in range(1, pasos + 1):
            for j, l in enumerate(lazos):
                trazo(mover(l, prof * k / pasos, -prof * k / pasos), 2 * linea, TINTA, cerrado=True, semilla=s + j, var=0.1, amp=0.8)
        for k in range(1, pasos + 1):
            relleno([mover(l, prof * k / pasos, -prof * k / pasos) for l in lazos], profundo)
        relleno(lazos, cara_)
        x0, y0, x1, y1 = caja(lazos)
        rayas(lazos, linea * 1.5, linea * 0.42, raya, 50.0, lambda q, y0=y0, y1=y1: q[1] < y0 + (y1 - y0) * 0.3, s + 7)
        brillo_letra(lazos, linea, s + 9)
        for j, l in enumerate(lazos):
            trazo(l, linea, TINTA, cerrado=True, semilla=s + 20 + j, amp=1.2)


TURQ = (TURQUESA, "137670", "168C86")
AMAR = (AMARILLO, "D9792B", "E3A532")
NARA = (NARANJA, "B4501A", "D96A24")
ROJA = (ROJO, "9E2A22", "BC372D")


@imagen("LogoOver", 1024, 320)
def i_logo_over():
    alto = 176
    letras = encajar(componer("OVER", alto, 3, inclinacion=4.0, sep=0.06, giro=6.0), 1024, 320, dx=-8, dy=6)
    rotulo(letras, [TURQ, NARA, TURQ, NARA], alto, 300)


@imagen("LogoBooked", 1024, 320)
def i_logo_booked():
    alto = 164
    letras = encajar(componer("BOOKED!", alto, 11, inclinacion=-1.5, sep=-0.035, giro=6.0), 1024, 320, dx=-8, dy=6)
    rotulo(letras, [AMAR, AMAR, AMAR, AMAR, AMAR, AMAR, ROJA], alto, 500)


@imagen("Avioneta", 512, 256)
def i_avioneta():
    for k, (y, x0, x1) in enumerate(((158, 40, 190), (124, 14, 176), (90, 52, 186))):
        linea_ = suave([(x0, y), ((x0 + x1) / 2, y + 7), (x1, y - 3)], False, 6)
        trazo(linea_, 17.0, TINTA, semilla=700 + k, var=0.15)
        trazo(linea_, 8.0, BLANCO, semilla=710 + k, var=0.15, amp=0.6)
    for k, (cx, cy, r) in enumerate(((196, 104, 22), (170, 86, 14), (214, 82, 12))):
        pieza(elipse(cx, cy, r, r * 0.85, 24), BLANCO, 5.0, semilla=720 + k, desfase=(0, 0))
    T = lambda p: girar(p, 9.0, (64, 64), 2.3, (330 - 64, 128 - 64))
    dibujar_avion(T, 741, 2.4)
    for k, x in enumerate((36, 46, 84, 92)):
        pieza(T(elipse(x, 66, 2.4, 2.4, 12)), CIELO, 3.2, semilla=760 + k, desfase=(0, 0))


@imagen("Etiqueta", 256, 512)
def i_etiqueta():
    cordel = suave([(128, 506), (104, 478), (124, 440), (128, 396)], False, 8)
    trazo(cordel, 13.0, TINTA, semilla=801, var=0.1, afilar=False)
    trazo(cordel, 6.0, ROJO, semilla=802, var=0.1, amp=0.6, afilar=False)
    forma = suave_esquinas([(46, 24), (210, 24), (210, 330), (166, 396), (90, 396), (46, 330)], 16)
    agujero = elipse(128, 360, 11, 11, 24)
    relleno([mover(temblar(forma, 0.6, 811), 9, -10), mover(agujero, 9, -10)], TINTA, 0.32)
    relleno([mover(temblar(forma, 1.3, 812), 1.8, -1.8), agujero], MANILA)
    relleno([temblar(rrect(50, 196, 206, 236, 2), 1.0, 813)], ROJO)
    trazo([(52, 236), (204, 236)], 4.0, TINTA, semilla=814)
    trazo([(52, 196), (204, 196)], 4.0, TINTA, semilla=815)
    rayado(forma, 8, 1.7, "D8BE86", 45.0, lambda q: q[1] < 70 and q[0] > 150, 816)
    rnd = random.Random(817)
    x = 66
    while x < 190:
        w = rnd.choice((3.0, 3.0, 5.0, 8.0))
        trazo([(x, 50), (x, 168)], w, TINTA, semilla=820 + int(x), var=0.1, amp=0.4, afilar=False)
        x += w + rnd.choice((3.0, 4.0, 6.0))
    letras = encajar(componer("OVB", 50, 5, sep=0.04, giro=2.0), 256, 512, dy=10)
    for i, lazos in enumerate(letras):
        relleno(lazos, TINTA)
        for j, l in enumerate(lazos):
            trazo(l, 2.6, TINTA, cerrado=True, semilla=830 + i * 3 + j)
    relleno([elipse(128, 360, 19, 19, 28), agujero], "D8BE86")
    trazo(forma, 7.0, TINTA, cerrado=True, semilla=840, amp=2.2)
    trazo(elipse(128, 360, 19, 19, 28), 5.0, TINTA, cerrado=True, semilla=841)
    trazo(agujero, 3.5, TINTA, cerrado=True, semilla=842)
    trazo(suave([(128, 396), (122, 376), (130, 364)], False, 6), 6.0, ROJO, semilla=843, afilar=False)


def mancha(cx, cy, R, brazos, semilla):
    rnd = random.Random(semilla)
    puntas = [(2 * math.pi * (k + rnd.uniform(-0.3, 0.3)) / brazos, rnd.uniform(0.2, 0.62), rnd.uniform(0.07, 0.15)) for k in range(brazos)]
    ruido = Ruido(semilla + 1, 5)
    pts = []
    for k in range(240):
        a = 2 * math.pi * k / 240
        r = 1.0 + 0.07 * ruido(k / 240)
        for a0, alto_, ancho in puntas:
            da = (a - a0 + math.pi) % (2 * math.pi) - math.pi
            r += alto_ * math.exp(-(da / ancho) ** 2 * 2.2)
        pts.append((cx + R * r * math.cos(a), cy + R * r * math.sin(a)))
    return pts, puntas


@imagen("Mancha", 512, 512)
def i_mancha():
    rnd = random.Random(901)
    forma, puntas = mancha(256, 256, 132, 12, 902)
    relleno([mover(temblar(forma, 0.8, 903), 10, -12)], TINTA, 0.3)
    pieza(forma, BLANCO, 8.0, semilla=904, desfase=(0, 0), rayas={"sep": 11, "ancho": 2.4, "color": GRIS_RAYA, "zona": lambda q: (q[0] - 256) - (q[1] - 256) > 120})
    trazo(elipse(220, 300, 70, 50, 24, -20, 110, 200), 9.0, BLANCO, semilla=905)
    for k, (a0, alto_, _) in enumerate(puntas):
        d = 132 * (1 + alto_) + rnd.uniform(16, 30)
        r = rnd.uniform(9, 17)
        if d + r < 246:
            pieza(elipse(256 + d * math.cos(a0), 256 + d * math.sin(a0), r, r * 0.9, 18, math.degrees(a0)), BLANCO, 4.5, semilla=910 + k, desfase=(0, 0))
    for k in range(10):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(200, 236)
        r = rnd.uniform(4, 8)
        pieza(elipse(256 + d * math.cos(a), 256 + d * math.sin(a), r, r, 12), BLANCO, 3.4, semilla=930 + k, desfase=(0, 0))


@imagen("Gotas", 512, 512)
def i_gotas():
    rnd = random.Random(951)
    for k in range(26):
        a = 2 * math.pi * k / 26 + rnd.uniform(-0.1, 0.1)
        d = rnd.uniform(150, 214)
        r = rnd.uniform(7, 15)
        largo_ = r * rnd.uniform(1.6, 2.6)
        ca, sa = math.cos(a), math.sin(a)
        cx, cy = 256 + d * ca, 256 + d * sa
        gota = suave([(cx + ca * r, cy + sa * r), (cx - sa * r, cy + ca * r), (cx - ca * largo_, cy - sa * largo_), (cx + sa * r, cy - ca * r)], True, 6)
        relleno([temblar(gota, 0.8, 960 + k)], TINTA)
        if rnd.random() < 0.6:
            e = d + r + rnd.uniform(10, 26)
            if e < 246:
                puntos(256 + e * ca, 256 + e * sa, rnd.uniform(2.5, 5.0))


@imagen("Cinta", 1024, 192)
def i_cinta():
    def arco(x):
        return 9.0 * math.sin(math.pi * (x - 110) / 804)
    for s in (-1, 1):
        def X(x):
            return x if s < 0 else 1024 - x
        cola = [(X(18), 28), (X(150), 28), (X(150), 116), (X(18), 116), (X(58), 72)]
        pieza(cola, GRIS_CINTA, 6.0, semilla=1001 + s, desfase=(0, 0), sombra=(7, -8, 0.3), rayas={"sep": 9, "ancho": 1.8, "color": "B0B0B0", "zona": lambda q: q[1] < 60})
        pliegue = [(X(112), 64 + arco(X(112))), (X(150), 28), (X(150), 64)]
        pieza(pliegue, GRIS_PLIEGUE, 5.0, semilla=1005 + s, desfase=(0, 0))
    abajo = [(x, 64 + arco(x)) for x in range(112, 913, 16)]
    arriba = [(x, 162 + arco(x)) for x in range(912, 111, -16)]
    banda = abajo + arriba
    relleno([mover(temblar(banda, 0.6, 1010), 8, -9)], TINTA, 0.3)
    pieza(banda, BLANCO, 6.5, semilla=1011, desfase=(0, 0), amp=1.4, rayas={"sep": 9, "ancho": 1.8, "color": GRIS_RAYA, "zona": lambda q: q[1] < 64 + arco(q[0]) + 18})
    trazo([(150, 146 + arco(150)), (330, 150 + arco(330))], 5.0, BLANCO, semilla=1012)


@imagen("Rasgado", 1024, 128)
def i_rasgado():
    rnd = random.Random(1101)
    borde = []
    x = 0.0
    while x <= 1030:
        borde.append((x, 64 + rnd.uniform(-9, 9) + 6 * math.sin(x / 61)))
        x += rnd.uniform(9, 22)
    forma = [(-8, 140)] + [(-8, borde[0][1])] + borde + [(1040, borde[-1][1]), (1040, 140)]
    relleno([forma], PAPEL)
    trazo(borde, 5.0, TINTA, semilla=1102, var=0.3, amp=1.5, afilar=False)
    for k in range(70):
        i = rnd.randrange(len(borde) - 1)
        x0, y0 = borde[i]
        trazo([(x0, y0 + 2), (x0 + rnd.uniform(-6, 6), y0 - rnd.uniform(4, 9))], 1.4, PAPEL2, semilla=1110 + k, var=0.2, amp=0.3)
    for k in range(40):
        y = rnd.uniform(78, 124)
        x0 = rnd.uniform(0, 1000)
        trazo([(x0, y), (x0 + rnd.uniform(10, 26), y + rnd.uniform(-3, 3))], 1.2, "E3CFA9", semilla=1200 + k, var=0.3, amp=0.5, a=0.5)


@imagen("Papel", 512, 512)
def i_papel():
    rnd = random.Random(1301)
    relleno([[(-4, -4), (516, -4), (516, 516), (-4, 516)]], PAPEL)

    def envolver(pts, f):
        x0, y0, x1, y1 = caja([pts])
        for dx in (-512, 0, 512):
            for dy in (-512, 0, 512):
                if x1 + dx > -4 and x0 + dx < 516 and y1 + dy > -4 and y0 + dy < 516:
                    f(mover(pts, dx, dy))
    for k in range(46):
        r = rnd.uniform(50, 140)
        forma = temblar(elipse(rnd.uniform(0, 512), rnd.uniform(0, 512), r, r * rnd.uniform(0.5, 0.9), 24, rnd.uniform(0, 180)), r * 0.12, 1310 + k)
        color = rnd.choice(("EEDDBE", "F7E8CC", "E8D4B0"))
        envolver(forma, lambda p, c=color: relleno([p], c, 0.07))
    for k in range(240):
        x, y = rnd.uniform(0, 512), rnd.uniform(0, 512)
        a = rnd.uniform(0, math.pi)
        l = rnd.uniform(8, 26)
        fibra = suave([(x, y), (x + math.cos(a) * l / 2 + rnd.uniform(-3, 3), y + math.sin(a) * l / 2 + rnd.uniform(-3, 3)), (x + math.cos(a) * l, y + math.sin(a) * l)], False, 4)
        ancho = rnd.uniform(0.8, 1.5)
        color = rnd.choice(("D8C49C", "CDB892", "E2D0AA"))
        alfa = rnd.uniform(0.25, 0.55)
        envolver(fibra, lambda p, w=ancho, c=color, al=alfa, s=1400 + k: trazo(p, w, c, semilla=s, var=0.3, amp=0.3, a=al))
    for k in range(180):
        r = rnd.uniform(0.6, 1.5)
        x, y = rnd.uniform(0, 512), rnd.uniform(0, 512)
        envolver(elipse(x, y, r, r, 8), lambda p, al=rnd.uniform(0.25, 0.5): relleno([p], "B9A47E", al))


def main():
    solo = set(ARGS[ARGS.index("--solo") + 1].split(",")) if "--solo" in ARGS else None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for nombre, ancho, alto, f in IMAGENES:
        if solo and nombre not in solo:
            continue
        escena(ancho, alto)
        bpy.context.scene.cycles.transparent_max_bounces = 256
        f()
        guardar(nombre)
    print("IMAGENES", len(IMAGENES))


main()
