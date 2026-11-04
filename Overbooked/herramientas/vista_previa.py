import json
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTE = os.path.join(RAIZ, "arte")
SALIDA = os.path.join(RAIZ, "renders")
P = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
P_INV = P.inverted()
rng = random.Random(7)


def rb(v):
    return P @ Vector((v[0], v[1], v[2], 1))


def cframe(cf):
    pos = cf["position"]
    o = cf["orientation"]
    return Matrix(((o[0][0], o[0][1], o[0][2], pos[0]), (o[1][0], o[1][1], o[1][2], pos[1]),
                   (o[2][0], o[2][1], o[2][2], pos[2]), (0, 0, 0, 1)))


def lin(c):
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


materiales = {}


def material(color, transp=0.0, neon=False, metal=False):
    clave = (tuple(round(c, 3) for c in color), round(transp, 2), neon, metal)
    if clave in materiales:
        return materiales[clave]
    m = bpy.data.materials.new("M")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(color), 1)
    b.inputs["Roughness"].default_value = 0.35 if metal else 0.7
    b.inputs["Metallic"].default_value = 0.6 if metal else 0
    if transp > 0:
        b.inputs["Alpha"].default_value = 1 - transp
    if neon:
        b.inputs["Emission Color"].default_value = (*lin(color), 1)
        b.inputs["Emission Strength"].default_value = 4
    materiales[clave] = m
    return m


def malla(nombre, verts, caras, mat):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(v[:3]) for v in verts], [], caras)
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def pieza(props, nombre, clase):
    tam = props.get("Size", [1, 1, 1])
    cf = cframe(props["CFrame"]["CFrame"])
    transp = props.get("Transparency", 0)
    if transp >= 0.99:
        return None
    color = props.get("Color", [0.6, 0.6, 0.6])
    material_rb = props.get("Material", "SmoothPlastic")
    mat = material(color, transp, material_rb == "Neon", material_rb in ("Metal", "DiamondPlate"))
    sx, sy, sz = tam[0] / 2, tam[1] / 2, tam[2] / 2
    forma = props.get("Shape", "Block")
    verts, caras = [], []
    if clase == "WedgePart":
        loc = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, -sy, sz), (-sx, -sy, sz), (-sx, sy, sz), (sx, sy, sz)]
        caras = [(0, 1, 2, 3), (3, 2, 5, 4), (0, 4, 5, 1), (0, 3, 4), (1, 5, 2)]
    elif forma == "Cylinder":
        n = 16
        loc = []
        for x in (-sx, sx):
            for i in range(n):
                a = 2 * math.pi * i / n
                loc.append((x, math.cos(a) * sy, math.sin(a) * sz))
        caras = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
        for i in range(n):
            caras.append((i, (i + 1) % n, n + (i + 1) % n, n + i))
    elif forma == "Ball":
        n, m = 16, 10
        loc = [(0, -sy, 0)]
        for j in range(1, m):
            t = math.pi * j / m
            for i in range(n):
                a = 2 * math.pi * i / n
                loc.append((math.sin(t) * math.cos(a) * sx, -math.cos(t) * sy, math.sin(t) * math.sin(a) * sz))
        loc.append((0, sy, 0))
        for i in range(n):
            caras.append((0, 1 + (i + 1) % n, 1 + i))
        for j in range(m - 2):
            for i in range(n):
                a0 = 1 + j * n + i
                a1 = 1 + j * n + (i + 1) % n
                caras.append((a0, a1, a1 + n, a0 + n))
        ult = len(loc) - 1
        for i in range(n):
            caras.append((ult, 1 + (m - 2) * n + i, 1 + (m - 2) * n + (i + 1) % n))
    else:
        loc = [(x, y, z) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]
        caras = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    verts = [P @ (cf @ Vector((*v, 1))) for v in loc]
    return malla(nombre, verts, caras, mat)


luces = []
marcadores = []
creados = {}


def recorrer(nodo, ruta, ocultos, padre_oculto=False):
    nombre = nodo.get("name", "?")
    clase = nodo.get("className", "Folder")
    props = nodo.get("properties", {})
    atributos = nodo.get("attributes", {})
    ob = None
    oculto = padre_oculto or any(o in ruta + [nombre] for o in ocultos)
    if "CFrame" in props and clase in ("Part", "Seat", "SpawnLocation", "WedgePart"):
        if "Visual" in atributos:
            marcadores.append((nombre, props, atributos))
            oculto = True
        elif nombre == "ZonaCarga" or nombre.startswith("Soporte"):
            marcadores.append((nombre, props, atributos))
        if not oculto:
            ob = pieza(props, nombre, clase)
            if ob:
                creados.setdefault(nombre, []).append(ob)
        if clase == "Part" and any(h.get("className") == "PointLight" for h in nodo.get("children", [])):
            luces.append(props["CFrame"]["CFrame"]["position"])
    for h in nodo.get("children", []):
        recorrer(h, ruta + [nombre], ocultos, oculto)


def importar(ruta):
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=ruta, axis_forward="Z", axis_up="Y")
    nuevos = [o for o in bpy.data.objects if o not in antes]
    malla_ob = [o for o in nuevos if o.type == "MESH"]
    for o in nuevos:
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    ob = malla_ob[0]
    ob.parent = None
    return ob


plantillas = {}


def plantilla(nombre):
    if nombre in plantillas:
        return plantillas[nombre]
    for carpeta in ("props", "pasajeros", "avion", "kit_interior", "kit_aeropuerto"):
        ruta = os.path.join(ARTE, carpeta, nombre + ".fbx")
        if os.path.exists(ruta):
            ob = importar(ruta)
            ob.matrix_world = Matrix.Identity(4)
            ob.hide_render = True
            plantillas[nombre] = ob
            return ob
    return None


def colocar(nombre, cf_roblox):
    base = plantilla(nombre)
    if not base:
        return None
    ob = base.copy()
    bpy.context.scene.collection.objects.link(ob)
    ob.hide_render = False
    ob.matrix_world = P @ cf_roblox @ P_INV
    return ob


def yaw(o):
    look = Vector((-o[0][2], -o[1][2], -o[2][2]))
    look.y = 0
    if look.length < 1e-3:
        return Matrix.Identity(4)
    look.normalize()
    ang = math.atan2(-look.x, -look.z)
    return Matrix.Rotation(ang, 4, Vector((0, 1, 0)))


def base_marcador(props, atributos):
    cf = props["CFrame"]["CFrame"]
    o = cf["orientation"]
    s = props["Size"]
    medio = abs(o[1][0]) * s[0] / 2 + abs(o[1][1]) * s[1] / 2 + abs(o[1][2]) * s[2] / 2
    y = atributos.get("Base", cf["position"][1] - medio)
    return Matrix.Translation(Vector((cf["position"][0], y, cf["position"][2]))) @ yaw(o)


def tripulante(color, cf_roblox, nombre):
    ruta = os.path.join(ARTE, "tripulante", "tripulante.blend")
    with bpy.data.libraries.load(ruta, link=False) as (desde, hacia):
        hacia.objects = [n for n in desde.objects]
    rig = None
    for o in hacia.objects:
        if o is None:
            continue
        bpy.context.scene.collection.objects.link(o)
        if o.type == "ARMATURE":
            rig = o
    mat = None
    for o in hacia.objects:
        if o and o.type == "MESH":
            if mat is None:
                mat = o.data.materials[0].copy()
                nodo = mat.node_tree.nodes.get("PlayerColor")
                if nodo:
                    nodo.outputs[0].default_value = (*lin(color), 1)
            o.material_slots[0].link = "OBJECT"
            o.material_slots[0].material = mat
    if rig:
        rig.matrix_world = P @ cf_roblox @ P_INV
    return rig


def camara(nombre, desde, hacia, lente=18):
    cd = bpy.data.cameras.new(nombre)
    cd.lens = lente
    cd.clip_end = 5000
    co = bpy.data.objects.new(nombre, cd)
    bpy.context.scene.collection.objects.link(co)
    a = rb(desde).to_3d()
    b = rb(hacia).to_3d()
    co.location = a
    co.rotation_euler = (b - a).to_track_quat("-Z", "Y").to_euler()
    return co


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    escena = bpy.context.scene
    avion = json.load(open(os.path.join(RAIZ, "mapa", "Avion.model.json")))
    aeropuerto = json.load(open(os.path.join(RAIZ, "mapa", "Aeropuerto.model.json")))
    ocultos_exterior = ["Ala" + l for l in ("Izq", "Der")] + ["Borde" + l for l in ("Izq", "Der")] + \
        ["Punta" + l for l in ("Izq", "Der")] + ["Soporte" + l for l in ("Izq", "Der")] + \
        ["Motor" + l for l in ("Izq", "Der")] + ["Aro" + l for l in ("Izq", "Der")] + \
        ["Estabilizador" + l for l in ("Izq", "Der")] + ["Deriva", "Morro"]
    for h in avion["children"]:
        recorrer(h, ["Avion"], ocultos_exterior)
    for h in aeropuerto["children"]:
        recorrer(h, ["Aeropuerto"], [])
    casco = plantilla("AvionExterior")
    if casco:
        c = casco.copy()
        escena.collection.objects.link(c)
        c.hide_render = False
        c.matrix_world = Matrix.Translation((0, 0, 100))
    asientos = []
    soportes = []
    zona = None
    for nombre, props, atributos in marcadores:
        if nombre == "Asiento":
            asientos.append(props)
        if nombre.startswith("Soporte"):
            soportes.append((props, atributos))
        if nombre == "ZonaCarga":
            zona = props
        visual = atributos.get("Visual")
        if visual and atributos.get("Movil"):
            colocar(visual, cframe(props["CFrame"]["CFrame"]) @ Matrix.Translation(Vector((0, -props["Size"][1] / 2, 0))))
        elif visual:
            colocar(visual, base_marcador(props, atributos))
    pasajeros = ["PasajeroAbuela", "PasajeroTurista", "PasajeroEjecutivo", "PasajeroNino", "PasajeroDeportista", "PasajeroRockero"]
    elegidos = rng.sample(asientos, 22)
    for props in elegidos:
        cf = props["CFrame"]["CFrame"]["position"]
        colocar(rng.choice(pasajeros), Matrix.Translation(Vector((cf[0], 101.6, cf[2] + 0.25))) @ Matrix.Scale(0.85, 4))
    tamanos = {"Extintor": 1.8, "Llave": 1.8, "Carrito": 3.2}
    for props, atributos in soportes:
        tipo = atributos.get("Tipo")
        if not tipo:
            continue
        cf = props["CFrame"]["CFrame"]["position"]
        visual = tipo
        colocar(visual, Matrix.Translation(Vector((cf[0], cf[1] + props["Size"][1] / 2 + 0.05, cf[2]))))
    if zona:
        zp = zona["CFrame"]["CFrame"]["position"]
        zs = zona["Size"]
        huecos = []
        for piso in range(3):
            for fila in range(5):
                z = zp[2] - zs[2] / 2 + 1.8 + fila * 3.3
                for col in (-3.2, 0, 3.2):
                    if not (col < 0 and z > 10.5):
                        huecos.append((zp[0] + col, piso * 3.2, z))
        carga = ["Caja", "Caja", "CajaFragil", "CajaFragil", "Maleta1", "Maleta2", "Maleta3", "Maleta1", "Maleta2", "Maleta3", "Maleta1"]
        for i, nombre in enumerate(carga):
            h = huecos[i]
            giro = Matrix.Rotation(rng.uniform(-0.4, 0.4), 4, Vector((0, 1, 0))) if nombre.startswith("Maleta") else Matrix.Identity(4)
            colocar(nombre, Matrix.Translation(Vector((h[0], 100.1 + h[1], h[2]))) @ giro)
        colocar("Jaula", Matrix.Translation(Vector((-5.5, 100.1, zp[2] + zs[2] / 2 - 3.6))))
        colocar("Cocodrilo", Matrix.Translation(Vector((-5.5, 100.4, zp[2] + zs[2] / 2 - 3.6))))
    colocar("Bandeja", Matrix.Translation(Vector((5.4, 103.5, -48.3))))
    colocar("Cafe", Matrix.Translation(Vector((4.6, 103.5, -51.2))))
    colocar("Agua", Matrix.Translation(Vector((4.5, 103.5, -45))))
    colores = [(0.545, 0.824, 0.298), (0.627, 0.486, 0.949), (0.949, 0.482, 0.71), (0.961, 0.804, 0.239)]
    tripulante(colores[0], Matrix.Translation(Vector((0.2, 100, -33))) @ Matrix.Rotation(math.pi, 4, Vector((0, 1, 0))), "A")
    tripulante(colores[1], Matrix.Translation(Vector((-0.6, 100, -20))) @ Matrix.Rotation(math.pi * 0.85, 4, Vector((0, 1, 0))), "B")
    tripulante(colores[2], Matrix.Translation(Vector((2.6, 100, -57.2))), "C")
    tripulante(colores[3], Matrix.Translation(Vector((-24, 99, -26))) @ Matrix.Rotation(math.pi, 4, Vector((0, 1, 0))), "D")

    mundo = bpy.data.worlds.new("Cielo")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs[0].default_value = (*lin((0.68, 0.84, 0.95)), 1)
    mundo.node_tree.nodes["Background"].inputs[1].default_value = 1.1
    escena.world = mundo
    sol = bpy.data.lights.new("Sol", "SUN")
    sol.energy = 3.5
    sol.angle = math.radians(10)
    so = bpy.data.objects.new("Sol", sol)
    so.rotation_euler = (math.radians(50), 0, math.radians(35))
    escena.collection.objects.link(so)
    for pos in luces:
        l = bpy.data.lights.new("Luz", "POINT")
        l.energy = 900
        l.color = (1.0, 0.93, 0.82)
        lo = bpy.data.objects.new("Luz", l)
        lo.location = rb((pos[0], pos[1] - 1.0, pos[2])).to_3d()
        escena.collection.objects.link(lo)

    escena.render.engine = "CYCLES"
    escena.cycles.device = "CPU"
    escena.cycles.samples = int(os.environ.get("MUESTRAS", "48"))
    escena.cycles.use_denoising = True
    escena.render.resolution_x = int(os.environ.get("ANCHO", "1280"))
    escena.render.resolution_y = int(os.environ.get("ALTO", "720"))
    try:
        escena.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    os.makedirs(SALIDA, exist_ok=True)
    vistas = [
        ("cabina_pasajeros", (0, 104.3, -46.5), (0, 103.2, -12), 15),
        ("cabina_piloto", (-2.6, 104.4, -56.8), (-1.2, 103.6, -70), 14),
        ("bodega", (0.5, 104.8, 0.8), (-0.5, 101.5, 18), 15),
        ("ala_torreta", (-17, 104.5, -31), (-26, 100.5, -15), 16),
        ("exterior", (-70, 128, -105), (0, 100, -18), 30),
        ("cocina", (0, 104.6, -42.5), (0, 102.5, -52), 16),
        ("asientos_lado", (0.4, 104.2, -30), (-6, 101.5, -30.5), 18),
        ("bano", (-1.5, 104.5, -2.5), (-5.5, 101.5, -6.5), 16),
        ("puerta_ala", (2.5, 104.4, -23.5), (-8, 102.5, -23.5), 17),
        ("terminal", (52, 96.5, -20), (100, 96, -20), 16),
        ("terminal_fuera", (24, 99, 14), (56, 95, -22), 18),
        ("aeropuerto", (-40, 135, 95), (40, 92, -10), 22),
        ("plataforma", (44, 101, 62), (20, 91.5, 26), 18),
        ("techo_avion", (14, 122, -4), (0, 112, -24), 20),
        ("rampa_exterior", (6, 97, 52), (0, 97, 20), 20),
    ]
    solo = os.environ.get("VISTAS")
    for nombre, desde, hacia, lente in vistas:
        if solo and nombre not in solo.split(","):
            continue
        escena.camera = camara(nombre, desde, hacia, lente)
        escena.render.filepath = os.path.join(SALIDA, nombre + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDER", nombre)


main()
