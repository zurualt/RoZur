"""Iconos de los pases y productos de Robux: una chapa redonda de color con el motivo encima.

blender -b --factory-startup --python-exit-code 1 -P arte/robux/robux_gen.py -- [--solo Cabra,Disco] [--muestras 40]

El motivo se renderiza en 3D (Cycles + Freestyle, como las miniaturas de accesorios) con fondo transparente
y la chapa se pinta despues con numpy. Roblox recorta los iconos en circulo: todo cabe en el circulo central.
"""
import bpy
import math
import os
import random
import sys
import tempfile
import numpy as np
from mathutils import Vector, Matrix, Euler

OUT = os.path.dirname(os.path.abspath(__file__))
ARTE = os.path.dirname(OUT)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
N = 512
TMP = tempfile.gettempdir()


def cargar(rel):
    ruta = os.path.join(ARTE, rel)
    ns = {"__file__": ruta, "__name__": "generador"}
    with open(ruta, encoding="utf-8") as fh:
        exec(compile(fh.read(), ruta, "exec"), ns)
    return ns


K = cargar(os.path.join("kit_extra", "kit_extra_gen.py"))
hex_rgb, lin = K["hex_rgb"], K["lin"]

# ---------------------------------------------------------------- geometria


def M(loc=(0, 0, 0), rot=(0, 0, 0), s=1.0):
    s = (s, s, s) if isinstance(s, (int, float)) else s
    return Matrix.LocRotScale(Vector(loc), Euler([math.radians(a) for a in rot]), Vector(s))


def mat(hexc, rough=0.55, emit=0.0, metal=0.0):
    m = bpy.data.materials.new(hexc)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(hex_rgb(hexc)), 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*lin(hex_rgb(hexc)), 1.0)
        b.inputs["Emission Strength"].default_value = emit
    return m


def objeto(me, mats, mw=Matrix(), suave=True):
    for m in mats if isinstance(mats, (list, tuple)) else [mats]:
        me.materials.append(m)
    if suave:
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(50))
    o = bpy.data.objects.new(me.name, me)
    bpy.context.scene.collection.objects.link(o)
    o.matrix_world = mw
    return o


def curva(splines, extrude=0.0, bevel=0.0, res=4, tubo=False, cerrada=False):
    """Curva a malla. splines: listas de puntos 2D (cerradas, con relleno) o 3D (tubos abiertos si tubo)."""
    cu = bpy.data.curves.new("cu", "CURVE")
    cu.dimensions = "3D" if tubo else "2D"
    if not tubo:
        cu.fill_mode = "BOTH"
    cu.extrude, cu.bevel_depth, cu.bevel_resolution = extrude, bevel, res
    cu.use_fill_caps = tubo
    for pts in splines:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for p, c in zip(sp.points, pts):
            p.co = (c[0], c[1], c[2] if len(c) > 2 else 0.0, 1.0)
        sp.use_cyclic_u = cerrada or not tubo
    o = bpy.data.objects.new("cu", cu)
    bpy.context.scene.collection.objects.link(o)
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(o)
    bpy.data.curves.remove(cu)
    return me


def esfera(r=1.0, u=24, v=16):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)
    me = bpy.data.meshes.new("esfera")
    bm.to_mesh(me)
    bm.free()
    return me


def corazon_pts(n=120):
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        out.append((x / 15.0, (y + 2.5) / 15.0))
    return out


def corazon(hexc="E8343A"):
    """Corazon mullido: silueta extruida, remallada en voxeles y alisada (redondea la punta y el pico)."""
    me = curva([corazon_pts()], extrude=0.3)
    o = bpy.data.objects.new("corazon", me)
    bpy.context.scene.collection.objects.link(o)
    rm = o.modifiers.new("remesh", "REMESH")
    rm.mode, rm.voxel_size = "VOXEL", 0.035
    sm = o.modifiers.new("liso", "SMOOTH")
    sm.factor, sm.iterations = 1.0, 30
    me2 = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(o)
    return me2, mat(hexc, 0.45)


def destello_pts(n=64, p=0.55):
    """Estrella de 4 puntas de lados curvos (superelipse |x|^p + |y|^p = 1)."""
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s = math.cos(a), math.sin(a)
        r = (abs(c) ** p + abs(s) ** p) ** (-1 / p)
        out.append((r * c, r * s))
    return out


def pluma_pts(n=24):
    """Pluma curvada: ancha cerca de la base (x=-1), afilada en la punta (x=1), con una muesca."""
    arriba, abajo = [], []
    for i in range(n + 1):
        x = -1 + 2 * i / n
        w = 0.34 * math.sin(math.pi * (x + 1) / 2) ** 0.6 * (1.15 - 0.35 * (x + 1) / 2)
        c = 0.14 * x * x
        arriba.append((x, c + w * (0.55 if abs(x - 0.25) < 0.09 else 1.0)))
        abajo.append((x, c - w))
    return arriba + abajo[::-1][1:-1]


def rrect_pts(w, h, r, n=10):
    out = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def importar(rel, mw=Matrix()):
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(ARTE, rel))
    o = next(x for x in bpy.data.objects if x not in antes and x.type == "MESH")
    for m in o.data.materials:
        b = m.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Roughness"].default_value = 0.6
    o.matrix_world = mw
    return o


def copia(o, mw):
    c = bpy.data.objects.new(o.name + "_c", o.data)
    bpy.context.scene.collection.objects.link(c)
    c.matrix_world = mw
    return c


def vertices(objs, filtro=None):
    bpy.context.view_layer.update()
    out = []
    for o in objs:
        for v in o.data.vertices:
            if filtro is None or filtro(v.co):
                out.append(o.matrix_world @ v.co)
    return out


# ---------------------------------------------------------------- camara


class Cam:
    """Camara en perspectiva que mete los puntos dentro de un circulo de radio `radio` (1 = medio cuadro)."""

    def __init__(self, pts, el, az, lens=50, radio=0.86, giro=0.0, centro=(0.0, 0.0)):
        el, az, g = math.radians(el), math.radians(az), math.radians(giro)
        d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
        f = -d
        r0 = f.cross(Vector((0, 0, 1))).normalized()
        u0 = r0.cross(f).normalized()
        self.right = r0 * math.cos(g) + u0 * math.sin(g)
        self.up = u0 * math.cos(g) - r0 * math.sin(g)
        self.f, self.t = f, 18.0 / lens
        c = sum(pts, Vector()) / len(pts)
        D = max((p - c).length for p in pts) / (self.t * radio) + 1e-3
        for _ in range(40):
            self.pos = c + d * D
            uv = [self.proyecta(p) for p in pts]
            cu = (max(x for x, y in uv) + min(x for x, y in uv)) / 2 - centro[0]
            cv = (max(y for x, y in uv) + min(y for x, y in uv)) / 2 - centro[1]
            c += (self.right * cu + self.up * cv) * D * self.t
            rmax = max(math.hypot(x - cu - centro[0], y - cv - centro[1]) for x, y in uv)
            D *= (rmax / radio) ** 0.7
        self.pos = c + d * D
        self.D = D
        cd = bpy.data.cameras.new("Cam")
        cd.lens, cd.sensor_width, cd.sensor_fit = lens, 36, "HORIZONTAL"
        cd.clip_start, cd.clip_end = 0.01, 5000
        self.ob = bpy.data.objects.new("Cam", cd)
        bpy.context.scene.collection.objects.link(self.ob)
        self.rot = Matrix((self.right, self.up, d)).transposed()
        self.ob.matrix_world = Matrix.Translation(self.pos) @ self.rot.to_4x4()
        bpy.context.scene.camera = self.ob

    def proyecta(self, p):
        q = p - self.pos
        z = q.dot(self.f)
        return q.dot(self.right) / (z * self.t), q.dot(self.up) / (z * self.t)

    def punto(self, u, v, prof):
        return self.pos + self.f * prof + (self.right * u + self.up * v) * prof * self.t

    def mundo(self, u, v, prof=None, giro=0.0, escala=0.1, inclina=(0.0, 0.0)):
        """Matriz para algo plano mirando a camara en (u, v); `escala` en unidades de pantalla."""
        prof = prof or self.D
        r = self.rot.to_4x4() @ M(rot=(inclina[0], inclina[1], giro))
        return Matrix.Translation(self.punto(u, v, prof)) @ r @ Matrix.Scale(escala * prof * self.t, 4)


# ---------------------------------------------------------------- adornos en pantalla


def destellos(cam, lista, hexc="FFF6C8", prof=None):
    m = mat(hexc, 0.4, emit=0.6)
    me = curva([destello_pts()], extrude=0.04, bevel=0.04, res=2)
    for u, v, s in lista:
        objeto(me.copy(), m, cam.mundo(u, v, prof, giro=random.uniform(-12, 12), escala=s))


def plumas(cam, lista, hexc="F7F7F2", prof=None):
    m, m_canon = mat(hexc, 0.6), mat("BDB6A6", 0.6)
    me = curva([pluma_pts()], extrude=0.02, bevel=0.04, res=2)
    canon = curva([[(x, 0.14 * x * x, 0.07) for x in (-1.3, -0.9, -0.5, -0.1, 0.3, 0.7)]], bevel=0.035, res=2, tubo=True)
    for u, v, s, g in lista:
        mw = cam.mundo(u, v, prof, giro=g, escala=s, inclina=(random.uniform(-20, 20), random.uniform(-20, 20)))
        objeto(me.copy(), m, mw)
        objeto(canon.copy(), m_canon, mw)


def rayas(cam, lista, hexc="FFFFFF", prof=None, grosor=0.06):
    """Lineas de velocidad: (u0, v0, u1, v1) en pantalla."""
    m = mat(hexc, 0.6, emit=0.3)
    prof = prof or cam.D
    for u0, v0, u1, v1 in lista:
        a, b = cam.punto(u0, v0, prof), cam.punto(u1, v1, prof)
        k = 12
        objeto(curva([[a.lerp(b, i / k) for i in range(k + 1)]], bevel=grosor * prof * cam.t / 2, res=3, tubo=True), m)


# ---------------------------------------------------------------- iconos


def i_vidas():
    random.seed(1)
    me, m = corazon("E8343A")
    base = M(rot=(90, 0, -10))
    heart = objeto(me, m, base)
    mw = mat("F7F7F2", 0.5)
    ala = [(0, 0.15), (0.35, 0.5), (0.75, 0.72), (1.15, 0.84), (1.42, 0.8), (1.45, 0.62), (1.22, 0.55), (1.3, 0.38),
           (1.05, 0.33), (1.1, 0.14), (0.8, 0.12), (0.78, -0.06), (0.45, -0.02), (0.25, -0.14), (0.0, -0.1)]
    alas = []
    for sx in (1, -1):
        pts = [(sx * x, y) for x, y in ala]
        if sx < 0:
            pts.reverse()
        alas.append(objeto(curva([pts], extrude=0.05, bevel=0.07, res=3), mw, base @ M((sx * 0.7, 0.3, -0.25), (0, sx * 18, sx * 14), 0.78)))
    lem = []
    for i in range(160):
        t = 2 * math.pi * i / 160
        d = 1 + math.sin(t) ** 2
        lem.append((0.8 * math.cos(t) / d, 0.8 * math.sin(t) * math.cos(t) / d + 0.04 * math.sin(t), 0.0))
    objeto(curva([lem], bevel=0.12, res=4, tubo=True, cerrada=True), mat("FFD23F", 0.35, emit=0.15), base @ M((0, -0.12, 0.42)))
    cam = Cam(vertices([heart] + alas), 4, -6, 50, radio=0.9)
    destellos(cam, [(-0.6, 0.6, 0.15), (0.66, -0.52, 0.12), (0.6, 0.64, 0.1), (-0.68, -0.45, 0.1)])
    return {"color": "1FA6A0", "rayos": 16}


def i_revivir():
    random.seed(2)
    me, m = corazon("E8343A")
    heart = objeto(me, m, M((0, 0, -1.25), (90, 0, 8), 0.78))
    blanco, negro = mat("FFFFFF", 0.4), mat("1B1B21", 0.3)
    for sx, s in ((-1, 1.0), (1, 1.12)):
        c = Vector((sx * 0.3, -0.36, -1.12))
        objeto(esfera(0.2 * s), blanco, M(c, s=(1, 0.55, 1)))
        objeto(esfera(0.09 * s), negro, M(c + Vector((0.03, -0.1, -0.03)), s=(1, 0.6, 1)))
    tirita = mat("F2C9A0", 0.6)
    for g, dy in ((35, 0.0), (-35, -0.05)):
        objeto(curva([rrect_pts(0.62, 0.2, 0.09)], extrude=0.02, bevel=0.025, res=2), tirita, M((0.42, -0.36 + dy, -0.82), (90, 0, 0)) @ M(rot=(0, 0, g)))
    # paracaidas: casquete a gajos y cuerdas
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1.0)
    for v in [v for v in bm.verts if v.co.z < -0.05]:
        bm.verts.remove(v)
    for f in bm.faces:
        c = f.calc_center_median()
        f.material_index = int(((math.atan2(c.y, c.x) + math.pi) / (2 * math.pi)) * 10) % 2
    me = bpy.data.meshes.new("paracaidas")
    bm.to_mesh(me)
    bm.free()
    canopy = objeto(me, [mat("F7F7F2", 0.55), mat("F27B2B", 0.55)], M((0, 0, 0.55), (0, 0, 11), (1.25, 1.25, 0.72)))
    m_cuerda = mat("34383F", 0.7)
    for k in range(4):
        a = math.radians(45 + 90 * k + 11)
        p0 = Vector((1.18 * math.cos(a), 1.18 * math.sin(a), 0.6))
        p1 = Vector((0.18 * math.cos(a), 0.12 * math.sin(a), -0.62))
        objeto(curva([[p0.lerp(p1, i / 6) for i in range(7)]], bevel=0.018, res=2, tubo=True), m_cuerda)
    cam = Cam(vertices([heart, canopy]), 6, -10, 50, radio=0.88)
    cruz = mat("FFFFFF", 0.4, emit=0.2)
    for u, v, s in ((0.62, -0.42, 0.16), (-0.66, -0.3, 0.11)):
        objeto(curva([[(-1, -0.33), (-0.33, -0.33), (-0.33, -1), (0.33, -1), (0.33, -0.33), (1, -0.33), (1, 0.33), (0.33, 0.33), (0.33, 1), (-0.33, 1), (-0.33, 0.33), (-1, 0.33)]],
                     extrude=0.08, bevel=0.12, res=3), cruz, cam.mundo(u, v, cam.D * 0.9, giro=random.uniform(-15, 15), escala=s))
    return {"color": "F6C445", "rayos": 16}


def i_cabra():
    cabra = importar("kit_caos/Cabra.fbx", M(rot=(0, 0, -8)))
    pts = vertices([cabra], lambda c: c.z > 1.4 and c.y < -0.35)
    Cam(pts, 4, -42, 35, radio=0.8, giro=10, centro=(0.04, 0.08))
    return {"color": "8BD24C", "rayos": 16, "busto": True}


def i_gallinas():
    random.seed(4)
    g0 = importar("kit_caos/Gallina.fbx", M((0, 0, 0), (0, -6, 12)))
    g1 = copia(g0, M((-0.62, 1.1, 0.35), (0, 20, -28), 0.95))
    g2 = copia(g0, M((0.68, 1.0, 0.55), (6, -22, 36), 0.92))
    cam = Cam(vertices([g0, g1, g2]), 12, -6, 35, radio=0.84, centro=(0, -0.02))
    plumas(cam, [(-0.6, 0.44, 0.17, 30), (0.62, 0.36, 0.15, -40), (-0.6, -0.42, 0.14, 160), (0.56, -0.48, 0.15, 210)], prof=cam.D * 0.8)
    return {"color": "F27B2B", "rayos": 16}


def i_disco():
    random.seed(5)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=22, v_segments=14, radius=1.0)
    caras = list(bm.faces)
    bmesh.ops.inset_individual(bm, faces=caras, thickness=0.018, depth=0.012)
    tiles = set(caras)
    for f in bm.faces:
        k = random.random()
        f.material_index = 0 if f not in tiles else (1 + random.randrange(4) if k < 0.25 else (5 if k < 0.6 else 6))
    me = bpy.data.meshes.new("bola")
    bm.to_mesh(me)
    bm.free()
    mats = [mat("4A4F58", 0.6), mat("FFFFFF", 0.2, emit=1.2), mat("8FD3F4", 0.25, emit=0.9), mat("F27BB5", 0.25, emit=0.9),
            mat("FFDC3C", 0.25, emit=0.9), mat("D3D9DE", 0.25, emit=0.15), mat("A9B0B8", 0.3, emit=0.1)]
    bola = objeto(me, mats, M((0, 0, 0), (12, 0, 8)), suave=False)
    metal = mat("6E7782", 0.4, metal=0.6)
    objeto(curva([[(0, 0, 0.92), (0, 0, 1.18)]], bevel=0.16, res=3, tubo=True), metal)
    objeto(curva([[(0, 0, 1.18), (0, 0, 2.6)]], bevel=0.035, res=2, tubo=True), mat("34383F", 0.7))
    cam = Cam(vertices([bola]) + [Vector((0, 0, 1.25))], 6, -6, 50, radio=0.72, centro=(0, -0.08))
    destellos(cam, [(-0.62, 0.55, 0.13), (0.66, 0.42, 0.1), (0.6, -0.62, 0.12), (-0.7, -0.4, 0.08), (-0.25, -0.82, 0.07)], prof=cam.D * 0.8)
    return {"color": "7A4FD8", "rayos": 12, "colores_rayo": ["FF6FB5", "4FD8F4", "FFDC3C", "9BE34C"], "fuerza_rayo": 0.75}


def montar_pajaro(m, aleteo):
    cuerpo = importar("kit_criaturas/Pajaro.fbx", m)
    h = Vector((0.78, 0.0, 0.38))
    iz = importar("kit_criaturas/AlaPajaroIzq.fbx", m @ Matrix.Translation(h) @ Euler((0, math.radians(-aleteo), 0)).to_matrix().to_4x4())
    de = importar("kit_criaturas/AlaPajaroDer.fbx", m @ Matrix.Translation((-h.x, h.y, h.z)) @ Euler((0, math.radians(aleteo), 0)).to_matrix().to_4x4())
    return [cuerpo, iz, de]


def i_pajaros():
    random.seed(6)
    marco = objeto(curva([rrect_pts(8.8, 9.8, 3.8), rrect_pts(7.6, 8.6, 3.2)], extrude=0.35, bevel=0.25, res=4), mat("1FA6A0", 0.5), M((0, 1.2, 0.3), (90, 0, 0)))
    objeto(curva([rrect_pts(7.9, 8.9, 3.3)], extrude=0.02), mat("8FD3F4", 0.25, emit=0.25), M((0, 1.35, 0.3), (90, 0, 0)))
    m_grieta = mat("FFFFFF", 0.4, emit=0.5)
    random.seed(3)
    for k in range(7):
        a = math.radians(20 + k * 360 / 7 + random.uniform(-12, 12))
        p, pts = Vector((0, 0)), []
        for j in range(5):
            pts.append((p.x, 1.0, p.y + 0.3))
            a2 = a + random.uniform(-0.45, 0.45)
            p = p + Vector((math.cos(a2), math.sin(a2))) * random.uniform(0.7, 1.1)
        objeto(curva([[(x, y + 0.05, z) for x, y, z in pts]], bevel=0.07, res=1, tubo=True), m_grieta)
    # estrella del golpe, pegada al cristal detras del pajaro
    pts = [((1.0 if i % 2 == 0 else 0.55) * random.uniform(0.85, 1.1) * math.cos(math.pi * i / 9), (1.0 if i % 2 == 0 else 0.55) * random.uniform(0.85, 1.1) * math.sin(math.pi * i / 9)) for i in range(18)]
    objeto(curva([pts], extrude=0.005, bevel=0.01, res=1), mat("FFDC3C", 0.5, emit=0.3), M((0, 1.25, 0.6), (90, 0, 8), 4.2))
    plaf = importar("kit_criaturas/PajaroPlaf.fbx", M((0, -0.45, 0.2), (0, 0, 180), 1.3))
    cam = Cam(vertices([marco, plaf]), 4, -6, 50, radio=0.88)
    plumas(cam, [(-0.56, 0.56, 0.15, 30), (0.6, 0.54, 0.13, -40), (-0.6, -0.5, 0.13, 160), (0.56, -0.54, 0.14, 120)], prof=cam.D * 0.8)
    return {"color": "D9443A", "rayos": 16}


def i_caida():
    random.seed(7)
    # alabeo sobre su eje (Y), picado de morro (X) y un poco de guinada (Z)
    mw = M(rot=(0, 0, 12)) @ M(rot=(50, 0, 0)) @ M(rot=(0, 55, 0))
    avion = importar("avion/AvionExterior.fbx", mw)
    cam = Cam(vertices([avion]), 18, 58, 45, radio=0.86)
    nariz, cola = cam.proyecta(mw @ Vector((0, -66, 2))), cam.proyecta(mw @ Vector((0, 31, 8)))
    d = Vector((nariz[0] - cola[0], nariz[1] - cola[1])).normalized()
    n = Vector((-d.y, d.x))
    lineas = []
    for off, ini, lon in ((-0.62, -0.1, 0.4), (-0.4, 0.15, 0.45), (0.42, 0.1, 0.42), (0.62, -0.15, 0.35), (0.2, 0.45, 0.3)):
        p0 = n * off - d * ini
        p1 = p0 - d * lon
        while p1.length > 0.84 or p0.length > 0.84:
            p0, p1 = p0 * 0.97, p1 * 0.97
        lineas.append((p0.x, p0.y, p1.x, p1.y))
    rayas(cam, lineas, prof=cam.D * 1.2, grosor=0.075)
    return {"color": "4FA3E0", "rayos": 16}


def i_piratas():
    random.seed(8)
    base = M((0, 0, 0), (0, 0, 0))
    piloto = importar("kit_criaturas/PilotoPirata.fbx", base)
    h = Vector((-0.62, 0.0, 1.38)) * 1.5
    brazo = importar("kit_criaturas/BrazoPirata.fbx", base @ Matrix.Translation(h) @ Euler((0, math.radians(-15), 0)).to_matrix().to_4x4() @ Matrix.Translation(-h))
    pts = vertices([piloto], lambda c: c.z > 1.9) + vertices([brazo])
    Cam(pts, -8, -24, 40, radio=0.84, giro=-8, centro=(0.0, 0.05))
    return {"color": "2D3A4A", "rayos": 16, "busto": True}


ICONOS = {"VidasInfinitas": i_vidas, "Revivir": i_revivir, "Cabra": i_cabra, "Gallinas": i_gallinas,
          "Disco": i_disco, "Pajaros": i_pajaros, "CaidaLibre": i_caida, "Piratas": i_piratas}

# ---------------------------------------------------------------- render y chapa

R_FILL, R_CHAPA, R_MAX = 0.905, 0.96, 0.99


def trazo(scene, grosor):
    scene.render.use_freestyle = True
    scene.render.line_thickness_mode = "ABSOLUTE"
    scene.render.line_thickness = 1.0  # se multiplica por el grosor del estilo
    vl = scene.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("Tinta")
    ls.select_by_visibility = ls.select_by_edge_types = ls.select_silhouette = True
    ls.select_border = ls.select_crease = False
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("Tinta")
    ls.linestyle.color = (0.03, 0.025, 0.02)
    ls.linestyle.thickness = grosor


def leer(ruta):
    im = bpy.data.images.load(ruta)
    a = np.empty(N * N * 4, np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(N, N, 4)


def mezcla(a, b, t):
    a, b, t = (np.asarray(x, np.float32) for x in (a, b, t))
    return a + (b - a) * (t[..., None] if t.ndim else t)


def chapa(cfg):
    xs = (np.arange(N, dtype=np.float32) + 0.5) / N * 2 - 1
    X, Y = np.meshgrid(xs, xs)  # filas de abajo arriba, como los pixeles de Blender
    r, ang = np.hypot(X, Y), np.arctan2(Y, X)
    px = 2.0 / N
    dentro = lambda e: np.clip((e - r) / px + 0.5, 0, 1)
    base = np.array(hex_rgb(cfg["color"]), np.float32)
    claro, hondo = mezcla(base, (1, 1, 1), 0.38), mezcla(base, (0, 0, 0), 0.1)
    t = np.clip(r / R_FILL, 0, 1) ** 1.5
    col = claro[None, None] * (1 - t[..., None]) + hondo[None, None] * t[..., None]
    n = cfg.get("rayos", 16)
    k = np.floor((ang + math.pi + 0.13) / (2 * math.pi / n)).astype(int)
    par = (k % 2 == 0).astype(np.float32) * np.clip((r - 0.1) / 0.4, 0, 1)
    if cfg.get("colores_rayo"):
        cols = np.array([hex_rgb(c) for c in cfg["colores_rayo"]], np.float32)
        col = mezcla(col, cols[(k // 2) % len(cols)], cfg.get("fuerza_rayo", 0.55) * par)
    else:
        col = mezcla(col, (1, 1, 1), 0.12 * par)
    # borde interior mas oscuro y un brillo arriba a la izquierda
    banda = np.clip((r - (R_FILL - 0.075)) / 0.012, 0, 1)
    col = mezcla(col, mezcla(base, (0, 0, 0), 0.3), banda)
    brillo = np.clip(1 - np.abs(r - (R_FILL - 0.115)) / 0.014, 0, 1) * np.clip(np.cos(ang - math.radians(128)) * 2.2 - 1.0, 0, 1)
    col = mezcla(col, (1, 1, 1), 0.55 * brillo)
    tinta = np.array(hex_rgb("1E1A22"), np.float32)
    col = mezcla(col, tinta, 1 - dentro(R_FILL))
    return col, dentro(R_CHAPA), X, Y, r, ang


def componer(ruta_render, ruta_png, cfg):
    sub = leer(ruta_render)
    col, alfa, X, Y, r, ang = chapa(cfg)
    a = sub[..., 3]
    # el busto se corta en el borde interior por abajo y asoma por encima del borde arriba
    if cfg.get("busto"):
        lado = np.clip(np.sin(ang) / 0.35 + 0.5, 0, 1)
        limite = (R_FILL - 0.004) * (1 - lado) + R_MAX * lado
    else:
        limite = R_MAX
    a = a * np.clip((limite - r) / (2.0 / N) + 0.5, 0, 1)
    # sombra del motivo sobre la chapa
    s = np.roll(np.roll(a, -9, axis=0), 7, axis=1)
    for eje in (0, 1):
        s = sum(np.roll(s, d, axis=eje) for d in range(-3, 4)) / 7
    col = col * (1 - 0.32 * (s * np.clip((R_FILL - r) / 0.01, 0, 1)))[..., None]
    out_a = a + alfa * (1 - a)
    rgb = (sub[..., :3] * a[..., None] + col * (alfa * (1 - a))[..., None]) / np.maximum(out_a, 1e-6)[..., None]
    img = np.dstack([np.clip(rgb, 0, 1), out_a]).astype(np.float32)
    im = bpy.data.images.new(os.path.basename(ruta_png), N, N, alpha=True)
    im.pixels.foreach_set(img.ravel())
    im.filepath_raw = ruta_png
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)
    print("ICONO", ruta_png)


def main():
    solo = set(ARGS[ARGS.index("--solo") + 1].split(",")) if "--solo" in ARGS else None
    muestras = int(ARGS[ARGS.index("--muestras") + 1]) if "--muestras" in ARGS else 48
    for clave, fn in ICONOS.items():
        if solo and clave not in solo:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        K["render_setup"](scene, os.cpu_count() or 4, N, N)
        scene.cycles.samples = muestras
        scene.render.film_transparent = True
        scene.view_settings.exposure = -0.1
        K["world"](scene, "FFF6E8", 0.9)
        K["TEMP"].clear()
        K["sun"](3.2, (48, 0, -30), 8)
        trazo(scene, 9.0)
        cfg = fn()
        tmp = os.path.join(TMP, "robux_%s.png" % clave)
        K["render_to"](tmp)
        componer(tmp, os.path.join(OUT, clave + ".png"), cfg)
        os.remove(tmp)


main()
