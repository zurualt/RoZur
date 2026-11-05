import bpy
import bmesh
import math
import os
import sys
import json
import random
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]


def arg(name, default=None):
    if name in ARGS:
        i = ARGS.index(name)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return default


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


GRADIENTE = [(0.0, "A2AADB"), (0.28, "BDC4EC"), (0.55, "DDE2F7"), (0.8, "F6F8FF"), (1.0, "FFFFFF")]

PAL = [
    ("leaf", "6DBE45"), ("dleaf", "3D9447"), ("lleaf", "8FD05A"), ("trunk", "8A5A33"),
    ("roof", "D9443A"), ("roof2", "E8743B"), ("wall", "FFF4E0"), ("wall2", "F2D9A0"),
    ("teal", "1FA6A0"), ("grey", "9AA0A6"), ("dgrey", "6B7178"), ("plaza", "E2D3A8"),
    ("white", "F7F7F2"), ("yellow", "F6C445"), ("glass", "8FD3F4"), ("black", "1B1B21"),
    ("bleaf", "2F7A3E"), ("roof3", "B8462F"),
]
IDX = {n: i for i, (n, _) in enumerate(PAL)}


def suv(n):
    i = IDX[n]
    return ((i % 8 + 0.5) / 8.0, (i // 8 + 0.5) / 4.0)


def guardar_imagen(nombre, rgb):
    h, w = rgb.shape[:2]
    img = bpy.data.images.new(nombre, w, h, alpha=False)
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(rgb, 0.0, 1.0)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = os.path.join(OUT, nombre + ".png")
    img.file_format = "PNG"
    img.save()
    return img


def material_imagen(nombre, img, interp="Linear"):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = interp
    tex.extension = "EXTEND" if interp == "Linear" else "REPEAT"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    try:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    except KeyError:
        pass
    return mat


def imagen_degradado():
    w = 256
    fila = np.zeros((w, 3), dtype=np.float32)
    for x in range(w):
        t = x / (w - 1)
        for (t0, c0), (t1, c1) in zip(GRADIENTE, GRADIENTE[1:]):
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0)
                k = k * k * (3 - 2 * k)
                a, b = np.array(hex_rgb(c0)), np.array(hex_rgb(c1))
                fila[x] = a + (b - a) * k
                break
    return guardar_imagen("cielo_degradado", np.repeat(fila[None, :, :], 8, axis=0))


def imagen_paleta():
    rgb = np.zeros((64, 128, 3), dtype=np.float32)
    for i, (_, hx) in enumerate(PAL):
        gx, gy = i % 8, i // 8
        rgb[gy * 16:gy * 16 + 16, gx * 16:gx * 16 + 16] = hex_rgb(hx)
    return guardar_imagen("cielo_paleta", rgb)


class Bolas:
    def __init__(self, seed):
        self.rnd = random.Random(seed)
        self.lista = []

    def bola(self, x, y, z, r):
        self.lista.append((Vector((x, y, z)), r))

    def bultos(self, desde, n, k0, k1, zmin=0.05):
        r = self.rnd
        nuevas = []
        for c, rad in self.lista[desde:]:
            for _ in range(n):
                d = Vector((r.gauss(0, 1), r.gauss(0, 1), abs(r.gauss(0, 1)) + zmin))
                d.normalize()
                rr = rad * r.uniform(k0, k1)
                nuevas.append((c + d * rad * r.uniform(0.6, 0.72), rr))
        self.lista.extend(nuevas)


def metabolas(nombre, bolas, res):
    mb = bpy.data.metaballs.new("MB" + nombre)
    mb.resolution = res
    mb.render_resolution = res
    mb.threshold = 0.6
    for c, r in bolas:
        el = mb.elements.new(type="BALL")
        el.co = c
        el.radius = r
        el.stiffness = 2.0
    ob = bpy.data.objects.new("MB" + nombre, mb)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.metaballs.remove(mb)
    return me


def quitar_islas(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    visto = set()
    grupos = []
    for v in bm.verts:
        if v.index in visto:
            continue
        pila, grupo = [v], []
        visto.add(v.index)
        while pila:
            c = pila.pop()
            grupo.append(c)
            for e in c.link_edges:
                o = e.other_vert(c)
                if o.index not in visto:
                    visto.add(o.index)
                    pila.append(o)
        grupos.append(grupo)
    mayor = max(len(g) for g in grupos)
    fuera = [v for g in grupos if len(g) < mayor * 0.2 for v in g]
    if fuera:
        bmesh.ops.delete(bm, geom=fuera, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    return len(grupos), len(fuera)


def aplanar_base(me, z0, k):
    for v in me.vertices:
        if v.co.z < z0:
            v.co.z = z0 - (z0 - v.co.z) * k


def con_modificadores(me, mods):
    ob = bpy.data.objects.new("tmp", me)
    bpy.context.scene.collection.objects.link(ob)
    for tipo, props in mods:
        m = ob.modifiers.new(tipo, tipo)
        for k, v in props.items():
            setattr(m, k, v)
    dg = bpy.context.evaluated_depsgraph_get()
    nuevo = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    return nuevo


def triangulos(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def sombreado(me, rayos=24, seed=5):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.normal_update()
    arbol = BVHTree.FromBMesh(bm)
    zs = [v.co.z for v in bm.verts]
    z0, z1 = min(zs), max(zs)
    dims = [max(v.co[i] for v in bm.verts) - min(v.co[i] for v in bm.verts) for i in range(3)]
    alcance = 0.45 * max(dims)
    rnd = random.Random(seed)
    dirs = []
    for _ in range(rayos):
        u, w = rnd.random(), rnd.random()
        r, a = math.sqrt(u), 2 * math.pi * w
        dirs.append(Vector((r * math.cos(a), r * math.sin(a), math.sqrt(max(0.0, 1 - u)))))
    valores = {}
    for v in bm.verts:
        n = v.normal
        t = n.orthogonal().normalized()
        b = n.cross(t)
        tapado = 0
        for d in dirs:
            dw = t * d.x + b * d.y + n * d.z
            if arbol.ray_cast(v.co + n * 0.02, dw, alcance)[0] is not None:
                tapado += 1
        ao = 1.0 - tapado / rayos
        h = (v.co.z - z0) / max(z1 - z0, 1e-6)
        s = 0.55 * h ** 0.85 + 0.24 * (n.z * 0.5 + 0.5) + 0.3 * ao - 0.08
        valores[v.index] = min(1.0, max(0.0, s))
    bm.free()
    return valores


def nube(nombre, bolas, res, base_z, aplastado, suavizado, objetivo, largo, mat, escala_z=1.0):
    me = metabolas(nombre, bolas, res)
    print("ISLAS", nombre, quitar_islas(me))
    aplanar_base(me, base_z, aplastado)
    if escala_z != 1.0:
        me.transform(Matrix.Diagonal((1.0, 1.0, escala_z, 1.0)))
    me = con_modificadores(me, [("SMOOTH", {"factor": 0.5, "iterations": suavizado})])
    t = triangulos(me)
    if t > objetivo:
        me = con_modificadores(me, [("DECIMATE", {"ratio": objetivo / t * 0.985, "use_collapse_triangulate": True})])
    me = con_modificadores(me, [("TRIANGULATE", {})])
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    k = largo / (max(xs) - min(xs))
    T = Matrix.Diagonal((k, k, k, 1.0)) @ Matrix.Translation(Vector((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs))))
    me.transform(T)
    me.update()
    valores = sombreado(me)
    uvl = me.uv_layers.new(name="UVMap")
    for lp in me.loops:
        uvl.data[lp.index].uv = (0.03 + 0.94 * valores[lp.vertex_index], 0.5)
    me.shade_smooth()
    me.materials.append(mat)
    me.name = nombre
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def g_cumulo(seed, largo=20.0, fondo=12.0, domos=3, alto=1.0):
    b = Bolas(seed)
    r = b.rnd
    n = 6
    for i in range(n):
        x = (-0.5 + (i + 0.5) / n) * largo * 0.8 + r.uniform(-0.6, 0.6)
        b.bola(x, r.uniform(-0.6, 0.6), 1.2, r.uniform(3.8, 4.4))
        for s in (-1, 1):
            if 0 < i < n - 1:
                b.bola(x + r.uniform(-1, 1), s * fondo * 0.26, 1.0, r.uniform(3.2, 3.8))
    for i in range(domos):
        x = (-0.5 + (i + 0.5) / domos) * largo * 0.52 + r.uniform(-0.8, 0.8)
        b.bola(x, r.uniform(-1.0, 1.0), (3.6 + r.uniform(0, 0.9)) * alto, r.uniform(4.6, 5.4))
    x = r.uniform(-largo * 0.12, largo * 0.12)
    b.bola(x, r.uniform(-0.6, 0.6), 6.6 * alto, r.uniform(4.2, 4.8))
    if alto > 1.05:
        b.bola(x + r.uniform(-1.5, 1.5), 0.0, 9.0 * alto, r.uniform(3.6, 4.2))
    for s in (-1, 1):
        b.bola(s * largo * 0.42, r.uniform(-1, 1), 2.4, r.uniform(3.0, 3.5))
    b.bultos(n, 3, 0.48, 0.62, 0.25)
    return b.lista


def g_torre(seed):
    b = Bolas(seed)
    r = b.rnd
    for i in range(5):
        x = (-0.5 + (i + 0.5) / 5) * 16.0 + r.uniform(-0.6, 0.6)
        b.bola(x, r.uniform(-0.6, 0.6), 1.2, r.uniform(3.8, 4.4))
        if 0 < i < 4:
            for s in (-1, 1):
                b.bola(x, s * 3.2, 1.0, r.uniform(3.2, 3.8))
    z = 3.8
    dx = 0.0
    for p in range(6):
        ancho = 10.0 * (1.0 - 0.07 * p)
        n = 3 if p < 4 else 2
        dx += r.uniform(-0.4, 0.9)
        for i in range(n):
            x = dx + (-0.5 + (i + 0.5) / n) * ancho + r.uniform(-0.8, 0.8)
            b.bola(x, r.uniform(-2.0, 2.0), z + r.uniform(-0.5, 0.5), r.uniform(4.0, 4.8) * (1 - 0.03 * p))
        z += 2.5
    b.bola(dx + 0.5, 0.0, z + 0.6, 4.4)
    b.bultos(14, 3, 0.45, 0.6, 0.2)
    return b.lista


def g_pequena(seed, n=4):
    b = Bolas(seed)
    r = b.rnd
    for i in range(n):
        x = (-0.5 + (i + 0.5) / n) * 7.0 + r.uniform(-0.4, 0.4)
        b.bola(x, r.uniform(-0.5, 0.5), 1.0 + (0.8 if 0 < i < n - 1 else 0.0), r.uniform(2.8, 3.3))
    b.bola(r.uniform(-0.8, 0.8), 0.0, 2.3, 3.4)
    b.bultos(n, 3, 0.48, 0.62, 0.3)
    return b.lista


def g_manto(seed, largo=40.0, fondo=26.0):
    b = Bolas(seed)
    r = b.rnd
    fases = [r.uniform(0, 6.28) for _ in range(6)]
    paso = 2.7
    nx, ny = int(largo / paso), int(fondo / paso)
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = (i / nx - 0.5) * largo + r.uniform(-0.9, 0.9)
            y = (j / ny - 0.5) * fondo + r.uniform(-0.9, 0.9)
            a = math.atan2(y / fondo, x / largo)
            borde = 0.82 + 0.1 * math.sin(3 * a + fases[0]) + 0.07 * math.sin(5 * a + fases[1]) + 0.05 * math.sin(9 * a + fases[2])
            q = (2 * x / largo) ** 2 + (2 * y / fondo) ** 2
            if q > borde * borde:
                continue
            ondula = 0.5 + 0.5 * math.sin(x * 0.31 + fases[3]) * math.cos(y * 0.37 + fases[4])
            b.bola(x, y, 0.4 + 0.6 * ondula, r.uniform(3.4, 4.1))
    n = len(b.lista)
    for _ in range(int(n * 0.3)):
        c, rad = b.lista[r.randrange(n)]
        b.bola(c.x + r.uniform(-1, 1), c.y + r.uniform(-1, 1), c.z + r.uniform(1.2, 2.0), rad * r.uniform(0.55, 0.8))
    return b.lista


NUBES = [
    ("NubeCumulo1", lambda: g_cumulo(11), 0.22, 0.7, 0.25, 4, 3000, 260.0, 1.0),
    ("NubeCumulo2", lambda: g_cumulo(23, 24.0, 13.0, 4), 0.22, 0.7, 0.25, 4, 3000, 300.0, 1.0),
    ("NubeCumulo3", lambda: g_cumulo(37, 16.0, 12.0, 2, 1.15), 0.22, 0.7, 0.25, 4, 3000, 220.0, 1.0),
    ("NubeTorre", lambda: g_torre(41), 0.24, 0.7, 0.25, 4, 3800, 230.0, 1.0),
    ("NubePequena1", lambda: g_pequena(53, 4), 0.2, 0.8, 0.2, 3, 800, 70.0, 1.0),
    ("NubePequena2", lambda: g_pequena(67, 3), 0.2, 0.8, 0.2, 3, 800, 55.0, 1.0),
    ("NubeManto1", lambda: g_manto(71), 0.32, 0.45, 0.06, 6, 2600, 900.0, 0.5),
    ("NubeManto2", lambda: g_manto(83, 34.0, 28.0), 0.32, 0.45, 0.06, 6, 2600, 760.0, 0.5),
]


def ruido_periodico(S, rnd, octavas):
    v = np.linspace(0, 2 * np.pi, S, endpoint=False, dtype=np.float32)
    X, Y = np.meshgrid(v, v)
    total = np.zeros((S, S), dtype=np.float32)
    for f, amp in octavas:
        for _ in range(3):
            a, b = rnd.integers(-f, f + 1, 2)
            if a == 0 and b == 0:
                a = f
            total += amp * np.sin(a * X + b * Y + rnd.uniform(0, 6.28)).astype(np.float32)
    return total


def pintar_campos(seed, bosque, lagos):
    S = 2048
    rnd = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) + 0.5
    G = 9
    celda = S / G
    semillas = []
    for j in range(G):
        for i in range(G):
            semillas.append((((i + 0.5 + rnd.uniform(-0.36, 0.36)) * celda) % S, ((j + 0.5 + rnd.uniform(-0.36, 0.36)) * celda) % S))
    d1 = np.full((S, S), np.inf, dtype=np.float32)
    d2 = np.full((S, S), np.inf, dtype=np.float32)
    idx = np.zeros((S, S), dtype=np.int32)
    for k, (px, py) in enumerate(semillas):
        dx = (xx - px + S / 2) % S - S / 2
        dy = (yy - py + S / 2) % S - S / 2
        d = dx * dx + dy * dy
        cerca = d < d1
        d2 = np.where(cerca, d1, np.minimum(d2, d))
        d1 = np.where(cerca, d, d1)
        idx = np.where(cerca, k, idx)
    tipos = [("E9C85A", "D6B04A", 1.0), ("A6D46C", "93C35C", 1.2), ("74C24C", "62AE3F", 1.1),
             ("BE8F5A", "A57A48", 0.8), ("8FC95E", "8FC95E", 1.0), ("C9A5DE", "B48FCB", 0.18),
             ("F0A64A", "DB9038", 0.25), ("5FAE45", "4F9A3A", 0.7)]
    pesos = np.array([t[2] for t in tipos])
    pesos /= pesos.sum()
    n = len(semillas)
    eleccion = rnd.choice(len(tipos), n, p=pesos)
    base = np.array([hex_rgb(tipos[e][0]) for e in eleccion], dtype=np.float32)
    surco = np.array([hex_rgb(tipos[e][1]) for e in eleccion], dtype=np.float32)
    ang = rnd.choice([0.0, np.pi / 2, np.pi / 4, -np.pi / 4, 0.3, -0.3], n).astype(np.float32)
    paso = rnd.uniform(9.0, 16.0, n).astype(np.float32)
    ca, sa, pp = np.cos(ang)[idx], np.sin(ang)[idx], paso[idx]
    raya = ((xx * ca + yy * sa) / pp) % 1.0 < 0.42
    img = np.where(raya[..., None], surco[idx], base[idx])
    seto = (np.sqrt(d2) - np.sqrt(d1)) < 5.0
    img[seto] = hex_rgb("4C8E3A")
    if bosque > 0:
        r = ruido_periodico(S, rnd, [(2, 1.0), (4, 0.55), (7, 0.3)])
        r = (r - r.mean()) / r.std()
        masc = r > (1.6 - bosque * 1.6)
        img[masc] = hex_rgb("3F8A3C")
        ys, xs = np.nonzero(masc[::9, ::9])
        orden = rnd.permutation(len(xs))
        oscuro, claro = np.array(hex_rgb("2F7434")), np.array(hex_rgb("57A245"))
        for t in orden[: 2600]:
            cx, cy = xs[t] * 9 + rnd.uniform(-4, 4), ys[t] * 9 + rnd.uniform(-4, 4)
            rad = rnd.uniform(5.5, 9.0)
            x0, x1 = int(max(cx - rad, 0)), int(min(cx + rad + 1, S))
            y0, y1 = int(max(cy - rad, 0)), int(min(cy + rad + 1, S))
            sub = (xx[y0:y1, x0:x1] - cx) ** 2 + (yy[y0:y1, x0:x1] - cy) ** 2 < rad * rad
            som = (xx[y0:y1, x0:x1] - cx - 2.2) ** 2 + (yy[y0:y1, x0:x1] - cy + 2.2) ** 2 < rad * rad
            parche = img[y0:y1, x0:x1]
            parche[som & ~sub & masc[y0:y1, x0:x1]] = oscuro
            parche[sub] = claro if rnd.random() < 0.45 else hex_rgb("4A9A40")
    for _ in range(lagos):
        cx, cy = rnd.uniform(380, S - 380, 2)
        ax, ay = rnd.uniform(90, 170), rnd.uniform(60, 120)
        a = rnd.uniform(0, np.pi)
        dx, dy = xx - cx, yy - cy
        u = (dx * np.cos(a) + dy * np.sin(a)) / ax
        v = (-dx * np.sin(a) + dy * np.cos(a)) / ay
        th = np.arctan2(v, u)
        q = np.sqrt(u * u + v * v) - 0.12 * np.sin(3 * th + 1.0) - 0.07 * np.sin(5 * th)
        img[q < 1.12] = hex_rgb("D9C98F")
        img[q < 1.0] = hex_rgb("3FA9D6")
        img[q < 0.62] = hex_rgb("2F8FC4")
    def carretera(dist, ancho):
        img[dist < ancho + 2.5] = hex_rgb("C2B286")
        img[dist < ancho] = hex_rgb("ECE0BC")
    borde = np.minimum(np.minimum(xx, S - xx), np.minimum(yy, S - yy))
    y0, y1 = rnd.uniform(500, 1500, 2)
    ruta = y0 + (y1 - y0) * xx / S + 90 * np.sin(2 * np.pi * xx / S * 1.5 + rnd.uniform(0, 6))
    x0, x1 = rnd.uniform(500, 1500, 2)
    ruta2 = x0 + (x1 - x0) * yy / S + 70 * np.sin(2 * np.pi * yy / S + rnd.uniform(0, 6))
    carretera(np.abs(yy - ruta) / np.sqrt(1 + ((y1 - y0) / S) ** 2), 5.0)
    carretera(np.abs(xx - ruta2), 5.0)
    carretera(borde, 7.0)
    casas = 0
    while casas < 26:
        x = rnd.uniform(60, S - 60)
        cerca_ruta = rnd.random() < 0.5
        if cerca_ruta:
            yv = float(ruta[0, int(x)]) + rnd.choice([-1, 1]) * rnd.uniform(18, 30)
            xv = x
        else:
            yv = rnd.uniform(60, S - 60)
            xv = float(ruta2[int(yv), 0]) + rnd.choice([-1, 1]) * rnd.uniform(18, 30)
        if not (40 < xv < S - 40 and 40 < yv < S - 40):
            continue
        w, h = rnd.uniform(7, 10), rnd.uniform(10, 15)
        if rnd.random() < 0.5:
            w, h = h, w
        xa, ya = int(xv - w / 2), int(yv - h / 2)
        img[ya + 3:ya + int(h) + 3, xa + 3:xa + int(w) + 3] = hex_rgb("3E6B33")
        img[ya:ya + int(h), xa:xa + int(w)] = hex_rgb(["D9443A", "E8743B", "B8462F", "F2EBDD"][rnd.integers(0, 4)])
        casas += 1
    img = img.reshape(S // 2, 2, S // 2, 2, 3).mean(axis=(1, 3))
    return img[::-1]


def suelo(nombre, img, tam=2048.0, grosor=2.0):
    mat = material_imagen("M_" + nombre, img, "Linear")
    mat.node_tree.nodes["Image Texture"].extension = "REPEAT"
    h = tam / 2
    vs = [(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0), (-h, -h, -grosor), (h, -h, -grosor), (h, h, -grosor), (-h, h, -grosor)]
    caras = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me = bpy.data.meshes.new(nombre)
    me.from_pydata(vs, [], caras)
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = ((v.x + h) / tam, (v.y + h) / tam) if p.index == 0 else (0.002, 0.002)
    me.materials.append(mat)
    me.transform(Matrix.Translation((0, 0, grosor)))
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def xf(bm, m):
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    return bm


def elipsoide(r, c, u=8, v=6):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    return xf(bm, Matrix.Translation(Vector(c)) @ Matrix.Diagonal((r[0], r[1], r[2], 1.0)))


def caja(x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    return xf(bm, Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1.0)))


def cilindro(r, h, c, seg=6, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    return xf(bm, Matrix.Translation(Vector(c) + Vector((0, 0, h / 2))))


def tejado(x0, x1, y0, y1, z0, alto, vuelo=0.4):
    bm = bmesh.new()
    xa, xb, ya, yb = x0 - vuelo, x1 + vuelo, y0 - vuelo, y1 + vuelo
    ym = (y0 + y1) / 2
    v = [bm.verts.new(p) for p in ((xa, ya, z0), (xb, ya, z0), (xb, ym, z0 + alto), (xa, ym, z0 + alto), (xa, yb, z0), (xb, yb, z0))]
    bm.faces.new((v[0], v[1], v[2], v[3]))
    bm.faces.new((v[3], v[2], v[5], v[4]))
    bm.faces.new((v[0], v[3], v[4]))
    bm.faces.new((v[1], v[5], v[2]))
    bm.faces.new((v[0], v[4], v[5], v[1]))
    return bm


class Prop:
    def __init__(self, nombre):
        self.nombre = nombre
        self.partes = []

    def add(self, bm, rol):
        self.partes.append((bm, rol))


def construir_prop(p, mat):
    verts, caras, uvs = [], [], []
    for parte, rol in p.partes:
        bmesh.ops.recalc_face_normals(parte, faces=parte.faces)
        ng = [f for f in parte.faces if len(f.verts) > 3]
        if ng:
            bmesh.ops.triangulate(parte, faces=ng)
        parte.verts.index_update()
        base = len(verts)
        verts.extend(v.co.copy() for v in parte.verts)
        for f in parte.faces:
            caras.append([base + v.index for v in f.verts])
            uvs.extend([suv(rol)] * 3)
        parte.free()
    mn = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
    mx = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
    off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    me = bpy.data.meshes.new(p.nombre)
    me.from_pydata([tuple(v - off) for v in verts], [], caras)
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", [c for uv in uvs for c in uv])
    me.shade_flat()
    me.materials.append(mat)
    ob = bpy.data.objects.new(p.nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def p_arboleda(nombre, seed, n):
    p = Prop(nombre)
    rnd = random.Random(seed)
    sitios = []
    while len(sitios) < n:
        a, d = rnd.uniform(0, 2 * math.pi), 14.0 * math.sqrt(rnd.random())
        x, y = d * math.cos(a) * 1.3, d * math.sin(a)
        if all((x - sx) ** 2 + (y - sy) ** 2 > 30 for sx, sy in sitios):
            sitios.append((x, y))
    for x, y in sitios:
        r = rnd.uniform(3.6, 5.4)
        alto = r * rnd.uniform(1.15, 1.5)
        tronco = rnd.uniform(2.0, 3.2)
        p.add(cilindro(0.7, tronco + 1.0, (x, y, 0.0), 5), "trunk")
        rol = rnd.choice(["leaf", "dleaf", "bleaf", "leaf"])
        p.add(elipsoide((r, r, alto), (x, y, tronco + alto * 0.85), 8, 6), rol)
        if rnd.random() < 0.5:
            p.add(elipsoide((r * 0.62, r * 0.62, alto * 0.6), (x + r * 0.35, y - r * 0.3, tronco + alto * 1.45), 7, 5), "lleaf" if rol == "leaf" else "leaf")
    return p


def p_pueblo(seed):
    p = Prop("Pueblo")
    rnd = random.Random(seed)
    p.add(caja(-9.0, 9.0, -7.0, 7.0, 0.0, 0.5), "plaza")
    p.add(caja(-3.2, 3.2, 8.5, 20.0, 0.0, 7.0), "wall")
    m = Matrix.Translation((0, 14.25, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z") @ Matrix.Translation((0, -14.25, 0))
    p.add(xf(tejado(-5.75, 5.75, 11.05, 17.45, 7.0, 3.6, 0.5), m), "roof3")
    p.add(caja(-2.0, 2.0, 4.5, 8.5, 0.0, 15.0), "wall")
    p.add(cilindro(2.9, 6.0, (0.0, 6.5, 15.0), 4, 0.0), "teal")
    p.add(caja(-0.6, 0.6, 4.45, 4.5, 9.0, 11.5), "black")
    casas = [(-16, -2, 0), (-16, 9, 1), (-15, -13, 0), (-4, -16, 1), (8, -16, 0), (17, -10, 1), (17, 2, 0), (16, 13, 1),
             (-27, 3, 0), (-26, -9, 1), (28, -2, 1), (6, 25, 0), (-9, 22, 1), (-5, 31, 0), (20, 24, 1)]
    for cx, cy, gira in casas:
        cx += rnd.uniform(-1.2, 1.2)
        cy += rnd.uniform(-1.2, 1.2)
        w, d = rnd.uniform(6.0, 8.0), rnd.uniform(4.5, 6.0)
        if gira:
            w, d = d, w
        h = rnd.uniform(3.5, 6.0)
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2
        p.add(caja(x0, x1, y0, y1, 0.0, h), rnd.choice(["wall", "wall", "wall2", "white"]))
        rol = rnd.choice(["roof", "roof2", "roof3", "roof", "teal"])
        if w >= d:
            p.add(tejado(x0, x1, y0, y1, h, d * 0.45, 0.45), rol)
        else:
            m = Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z") @ Matrix.Translation((-cx, -cy, 0))
            p.add(xf(tejado(cx - d / 2, cx + d / 2, cy - w / 2, cy + w / 2, h, w * 0.45, 0.45), m), rol)
    for _ in range(9):
        a, d = rnd.uniform(0, 2 * math.pi), rnd.uniform(24, 34)
        x, y = d * math.cos(a), d * math.sin(a) * 0.9
        r = rnd.uniform(2.6, 3.6)
        p.add(cilindro(0.5, 2.5, (x, y, 0.0), 5), "trunk")
        p.add(elipsoide((r, r, r * 1.25), (x, y, 2.0 + r), 7, 5), rnd.choice(["leaf", "dleaf"]))
    return p


def exportar(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.hide_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    assert [o.name for o in bpy.context.view_layer.objects if o.select_get()] == [ob.name]
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, ob.name + ".fbx"),
        use_selection=True,
        object_types={"MESH"},
        use_mesh_modifiers=True,
        mesh_smooth_type="OFF",
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="Z",
        axis_up="Y",
        path_mode="COPY",
        embed_textures=True,
        bake_anim=False,
    )


def preparar_render(threads):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 40
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.render.threads_mode = "FIXED"
    scene.render.threads = threads
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    pct = arg("--pct")
    scene.render.resolution_percentage = int(pct) if isinstance(pct, str) else 100
    scene.render.image_settings.file_format = "PNG"
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    world = bpy.data.worlds.new("Cielo")
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*lin(hex_rgb("CFE6F5")), 1.0)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (*lin(hex_rgb("4F9EDB")), 1.0)
    e = ramp.color_ramp.elements.new(0.5)
    e.color = (*lin(hex_rgb("B7DAF2")), 1.0)
    bg.inputs[1].default_value = 1.0
    scene.world = world
    sun = bpy.data.lights.new("Sol", "SUN")
    sun.energy = 4.0
    sun.angle = math.radians(4)
    sun.color = (1.0, 0.97, 0.9)
    so = bpy.data.objects.new("Sol", sun)
    so.rotation_euler = (math.radians(42), 0.0, math.radians(-38))
    scene.collection.objects.link(so)


def niebla(densidad, centro, radio=7000.0):
    m = bpy.data.materials.new("Niebla")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*lin(hex_rgb("D8EAF7")), 1.0)
    vol.inputs["Density"].default_value = densidad
    nt.links.new(vol.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=radio)
    me = bpy.data.meshes.new("Niebla")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    ob = bpy.data.objects.new("Niebla", me)
    ob.location = centro
    bpy.context.scene.collection.objects.link(ob)
    return ob


class Escena:
    def __init__(self, objs):
        self.objs = objs
        self.hechos = []

    def poner(self, nombre, x, y, z=0.0, rz=0.0, s=1.0):
        o = bpy.data.objects.new(nombre + "_i", self.objs[nombre].data)
        o.location = (x, y, z)
        o.rotation_euler = (0, 0, math.radians(rz))
        o.scale = (s, s, s)
        bpy.context.scene.collection.objects.link(o)
        self.hechos.append(o)
        return o

    def camara(self, loc, objetivo, lente):
        cd = bpy.data.cameras.new("Cam")
        cd.lens = lente
        cd.clip_start = 1.0
        cd.clip_end = 20000
        co = bpy.data.objects.new("Cam", cd)
        co.location = loc
        co.rotation_euler = (Vector(objetivo) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.collection.objects.link(co)
        bpy.context.scene.camera = co
        self.hechos.append(co)

    def limpiar(self):
        for o in self.hechos:
            bpy.data.objects.remove(o)
        self.hechos = []


def hoja_nubes(es):
    x = 0.0
    for nm in ["NubeCumulo3", "NubeCumulo1", "NubeCumulo2", "NubeTorre"]:
        if nm in es.objs:
            w = es.objs[nm].dimensions.x
            es.poner(nm, x + w / 2, 0, 0, 0)
            x += w + 40
    c = Vector((x / 2, 0, 110))
    es.camara(c + Vector((0, -x * 1.2, 160)), c, 35)


def hoja_nubes2(es):
    es.poner("NubeManto1", 0, 0, 0, 0)
    es.poner("NubeManto2", 820, 120, -10, 25)
    es.poner("NubePequena1", 150, -520, 60, 0, 2.2)
    es.poner("NubePequena2", 450, -560, 50, 0, 2.2)
    es.camara((400, -1500, 650), (400, 0, 0), 40)


def hoja_suelo(es):
    nombres = ["SueloCampos1", "SueloCampos2"]
    rnd = random.Random(5)
    for i in range(-1, 2):
        for j in range(-1, 2):
            es.poner(nombres[(i * 7 + j * 3) % 2], i * 2048, j * 2048, -2, rnd.choice([0, 90, 180, 270]))
    for k in range(40):
        es.poner(rnd.choice(["Arboleda1", "Arboleda2"]), rnd.uniform(-2400, 2400), rnd.uniform(-2400, 2400), 0, rnd.uniform(0, 360), rnd.uniform(1.0, 1.6))
    for k in range(5):
        es.poner("Pueblo", rnd.uniform(-1800, 1800), rnd.uniform(-1800, 1800), 0, rnd.uniform(0, 360), 1.3)
    es.poner("Pueblo", 120, -300, 0, 20, 1.3)
    es.poner("Arboleda1", 260, -320, 0, 0, 1.4)
    es.camara((0, -1500, 700), (0, -200, 0), 30)


CAPAS_JUEGO = [
    (["NubeManto1", "NubeManto2"], 30, 3450, 3650, 1.1, 1.6, 1.0),
    (["NubeCumulo1", "NubeCumulo2", "NubeCumulo3"], 15, 1200, 2000, 0.8, 1.3, 1.0),
    (["NubePequena1", "NubePequena2"], 10, 1000, 2600, 0.9, 1.6, 1.0),
    (["NubeTorre"], 7, 3300, 3500, 0.9, 1.35, 1.0),
    (["NubeCumulo1", "NubeCumulo2", "NubeCumulo3"], 12, 5000, 6300, 0.8, 1.25, 1.0),
    (["NubePequena1", "NubePequena2"], 14, 5000, 7200, 0.9, 1.8, 1.0),
    (["NubePequena1", "NubePequena2"], 8, 8800, 10200, 1.6, 2.4, 0.65),
]


def hoja_vuelo(es):
    rnd = random.Random(9)
    altitud = 6000.0
    suelo_z = -(10 + altitud * 0.07)
    for i in range(-2, 2):
        for j in range(-1, 2):
            es.poner(["SueloCampos1", "SueloCampos2"][(i * 7 + j * 13) % 2], (i + 0.5) * 2048, (j + 0.5) * 2048, suelo_z - 2, rnd.choice([0, 90, 180, 270]))
    for k in range(47):
        es.poner(rnd.choice(["Arboleda1", "Arboleda2", "Arboleda1", "Pueblo"]), rnd.uniform(-2400, 2400), rnd.uniform(-2400, 2400), suelo_z, rnd.uniform(0, 360), 2.0)
    for modelos, n, b0, b1, e0, e1, plano in CAPAS_JUEGO:
        for k in range(n):
            nm = rnd.choice(modelos)
            e = rnd.uniform(e0, e1)
            x, y = rnd.uniform(-2800, 2800), rnd.uniform(-2800, 2800)
            o = es.poner(nm, x, y, (rnd.uniform(b0, b1) - altitud) * 0.07, rnd.uniform(0, 360), e)
            o.scale = (e, e, e * plano)
    es.camara((0, 0, 0), (-500, 1400, -260), 18)


HOJAS = [("cielo_nubes.png", hoja_nubes, 0.0), ("cielo_nubes2.png", hoja_nubes2, 0.0), ("cielo_suelo.png", hoja_suelo, 0.00005), ("cielo_vuelo.png", hoja_vuelo, 0.00009)]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    solo = arg("--only")
    solo = set(solo.split(",")) if isinstance(solo, str) else None
    degradado = imagen_degradado()
    mat_nube = material_imagen("Nube_Degradado", degradado, "Linear")
    paleta = imagen_paleta()
    mat_pal = material_imagen("Cielo_Paleta", paleta, "Closest")
    objs = {}
    for nombre, gen, res, base_z, aplastado, suav, objetivo, largo, ez in NUBES:
        if solo and nombre not in solo:
            continue
        objs[nombre] = nube(nombre, gen(), res, base_z, aplastado, suav, objetivo, largo, mat_nube, ez)
    if not solo or "SueloCampos1" in solo:
        objs["SueloCampos1"] = suelo("SueloCampos1", guardar_imagen("SueloCampos1", pintar_campos(101, 0.35, 1)))
    if not solo or "SueloCampos2" in solo:
        objs["SueloCampos2"] = suelo("SueloCampos2", guardar_imagen("SueloCampos2", pintar_campos(202, 0.6, 2)))
    for p in (p_arboleda("Arboleda1", 7, 8), p_arboleda("Arboleda2", 8, 5), p_pueblo(9)):
        if solo and p.nombre not in solo:
            continue
        objs[p.nombre] = construir_prop(p, mat_pal)
    manifest = []
    for nombre, ob in objs.items():
        tris = triangulos(ob.data)
        d = ob.dimensions
        print("PIEZA %-14s tris %5d  tam %.1f x %.1f x %.1f" % (nombre, tris, d.x, d.z, d.y))
        if not arg("--no-export"):
            exportar(ob)
        manifest.append({"nombre": nombre, "archivo": nombre + ".fbx", "tamano": [round(d.x, 3), round(d.z, 3), round(d.y, 3)], "triangulos": tris})
    if not arg("--no-export"):
        ruta = os.path.join(OUT, "manifest.json")
        if solo and os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as fh:
                manifest = [e for e in json.load(fh) if e["nombre"] not in solo] + manifest
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
    if arg("--no-render") or (solo and not arg("--sheets")):
        return
    hilos = arg("--threads")
    preparar_render(int(hilos) if isinstance(hilos, str) else 8)
    cuales = arg("--sheets")
    cuales = set(cuales.split(",")) if isinstance(cuales, str) else None
    for o in objs.values():
        o.hide_render = True
    for i, (archivo, f, dens) in enumerate(HOJAS):
        if cuales and str(i + 1) not in cuales:
            continue
        es = Escena(objs)
        f(es)
        vol = niebla(dens, bpy.context.scene.camera.location) if dens > 0 else None
        bpy.context.scene.render.filepath = os.path.join(OUT, archivo)
        bpy.ops.render.render(write_still=True)
        print("RENDER", archivo)
        es.limpiar()
        if vol:
            bpy.data.objects.remove(vol)


main()
