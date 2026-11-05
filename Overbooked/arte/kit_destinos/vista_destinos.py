import bpy
import math
import os
import random
from mathutils import Vector

OUT = os.path.dirname(os.path.abspath(__file__))
CIELO = os.path.join(os.path.dirname(OUT), "kit_cielo")
RENDERS = os.path.join(OUT, "renders")
LOSETA = 2048.0
FRENTE = 3000.0
HUNDIDO = 0.6

ADORNOS = {
    "Jungla": [("SelvaJungla", 34, 1.0, 1.5, False), ("PalmeralJungla", 14, 1.0, 1.4, False), ("CerroJungla", 12, 1.4, 2.3, True)],
    "Nieve": [("PinarNieve", 40, 1.0, 1.5, False), ("MontanaNieve1", 5, 1.1, 1.6, True), ("MontanaNieve2", 4, 1.1, 1.5, True)],
    "Desierto": [("CactusDesierto", 30, 1.0, 1.6, False), ("MesaDesierto", 8, 1.0, 1.6, True), ("AgujasDesierto", 6, 1.0, 1.6, True)],
    "Ciudad": [("BarrioCiudad", 34, 1.0, 1.3, False), ("TorresCiudad", 14, 1.0, 1.5, True)],
}
NIEBLA = {"Jungla": "CFE8D2", "Nieve": "DCE8FA", "Desierto": "F6D6AE", "Ciudad": "DDDAD3"}
LUCES = {"Nieve": "LucesNieve", "Ciudad": "LucesCiudad"}


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


class Escena:
    def __init__(self, objs):
        self.objs = objs
        self.hechos = []

    def poner(self, nombre, x, y, z=0.0, rz=0.0, s=1.0, mat=None):
        o = bpy.data.objects.new(nombre + "_i", self.objs[nombre].data)
        o.location = (x, y, z)
        o.rotation_euler = (0, 0, math.radians(rz))
        o.scale = (s, s, s)
        if mat is not None:
            o.material_slots[0].link = "OBJECT"
            o.material_slots[0].material = mat
        bpy.context.scene.collection.objects.link(o)
        self.hechos.append(o)
        return o

    def camara(self, loc, objetivo, fov=70.0):
        cd = bpy.data.cameras.new("Cam")
        cd.sensor_fit = "VERTICAL"
        cd.angle_y = math.radians(fov)
        cd.clip_start = 0.5
        cd.clip_end = 30000
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


def importar(nombre):
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(CIELO, nombre + ".fbx"), axis_forward="Z", axis_up="Y")
    nuevos = [o for o in bpy.data.objects if o not in antes and o.type == "MESH"]
    ob = nuevos[0]
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    vs = [v.co for v in ob.data.vertices]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    ob.data.transform(__import__("mathutils").Matrix.Translation(Vector((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z))))
    ob.location = (0, 0, 0)
    ob.hide_render = True
    ob.name = nombre
    return ob


def emisivo(hx, fuerza):
    m = bpy.data.materials.new("Luz")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*lin(hex_rgb(hx)), 1.0)
    e.inputs["Strength"].default_value = fuerza
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


def niebla(densidad, centro, color, radio=12000.0):
    import bmesh
    m = bpy.data.materials.new("Niebla")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*lin(hex_rgb(color)), 1.0)
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


def radio_de(ob, s):
    return max(ob.dimensions.x, ob.dimensions.y) / 2 * s


def montar(es, bioma, plano_y, todo_bioma, rnd):
    aero, borde = es.objs["Aeropuerto" + bioma], es.objs["Borde" + bioma]
    hx, hy = max(aero.dimensions.x, borde.dimensions.x) / 2, max(aero.dimensions.y, borde.dimensions.y) / 2
    celdas = {}
    for i in range(-3, 4):
        for j in range(-4, 5):
            cx, cy = i * LOSETA, j * LOSETA
            jit = ((i * 7919 + j * 104729) % 997) / 997 * 1000 - 500
            es_bioma = todo_bioma or cy < FRENTE + jit
            celdas[(i, j)] = es_bioma
            if es_bioma:
                v = (i * 7 + j * 13) % 2 + 1
                es.poner(f"Suelo{bioma}{v}", cx, cy, -HUNDIDO - 2.0)
            else:
                v = (i * 7 + j * 13) % 2 + 1
                es.poner(f"SueloCampos{v}", cx, cy, -2.0, rnd.choice([0, 90, 180, 270]))

    def bioma_en(x, y):
        return celdas.get((round(x / LOSETA), round(y / LOSETA)), True)

    for nombre, n, s0, s1, grande in ADORNOS[bioma]:
        radio = 4500.0 if grande else 2400.0
        puestos = 0
        intentos = 0
        while puestos < n and intentos < n * 30:
            intentos += 1
            s = rnd.uniform(s0, s1)
            r = radio_de(es.objs[nombre], s)
            x, y = rnd.uniform(-radio, radio), plano_y + rnd.uniform(-radio, radio)
            if grande and abs(x) < r + 150:
                continue
            if abs(x) < r + hx and abs(y) < r + hy:
                continue
            if not bioma_en(x, y):
                continue
            es.poner(nombre, x, y, -HUNDIDO, rnd.uniform(0, 360), s)
            puestos += 1
    if not todo_bioma:
        for k in range(47):
            nombre = rnd.choice(["Arboleda1", "Arboleda2", "Arboleda1", "Pueblo"])
            x, y = rnd.uniform(-2400, 2400), plano_y + rnd.uniform(-2400, 2400)
            if bioma_en(x, y):
                continue
            es.poner(nombre, x, y, 0.0, rnd.uniform(0, 360), rnd.uniform(1.5, 2.4))
    es.poner("Aeropuerto" + bioma, 0, 0, 0)
    es.poner("Borde" + bioma, 0, 0, 0)
    if bioma in LUCES:
        es.poner(LUCES[bioma], 0, 0, 0, mat=emisivo("FFE7A0", 6.0))


VISTAS = [
    ("aproximacion", 5200.0, 2600.0, False, -0.2),
    ("final", 760.0, 110.0, True, -0.05),
    ("aterrizado", -40.0, 0.0, True, 0.0),
]


def renderizar(objs, C, arg):
    os.makedirs(RENDERS, exist_ok=True)
    hilos = arg("--threads")
    C["preparar_render"](int(hilos) if isinstance(hilos, str) else 16)
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.cycles.samples = int(arg("--samples")) if isinstance(arg("--samples"), str) else 24
    for o in objs.values():
        o.hide_render = True
    for nombre in ("SueloCampos1", "SueloCampos2", "Arboleda1", "Arboleda2", "Pueblo"):
        objs[nombre] = importar(nombre)
    biomas = arg("--biomas")
    biomas = biomas.split(",") if isinstance(biomas, str) else list(ADORNOS)
    vistas = arg("--vistas")
    vistas = vistas.split(",") if isinstance(vistas, str) else [v[0] for v in VISTAS]
    for bioma in biomas:
        for clave, d, alt, todo, cab in VISTAS:
            if clave not in vistas:
                continue
            es = Escena(objs)
            montar(es, bioma, d, todo, random.Random(7))
            ojo = 18.0 + alt * 0.07
            if clave == "aterrizado":
                es.camara((-6.0, d, 14.0), (60.0, d - 160.0, 4.0), 70.0)
            else:
                mira = Vector((0.0, -1.0, cab)).normalized()
                loc = Vector((0.0, d, ojo))
                es.camara(loc, loc + mira * 100.0, 70.0)
            vol = niebla(0.00006, Vector((0.0, d, 0.0)), NIEBLA[bioma])
            scene.render.filepath = os.path.join(RENDERS, f"destinos_{bioma.lower()}_{clave}.png")
            bpy.ops.render.render(write_still=True)
            print("RENDER", scene.render.filepath, flush=True)
            es.limpiar()
            bpy.data.objects.remove(vol)
    if arg("--catalogo"):
        es = Escena(objs)
        x = 0.0
        pequenos = ["SelvaJungla", "PalmeralJungla", "PinarNieve", "CactusDesierto", "BarrioCiudad"]
        for nombre in pequenos:
            w = objs[nombre].dimensions.x
            es.poner(nombre, x + w / 2, 0, 0)
            x += w + 12
        es.camara((x / 2, -x * 0.75, x * 0.32), (x / 2, 0, 8), 40.0)
        scene.render.filepath = os.path.join(RENDERS, "destinos_catalogo.png")
        bpy.ops.render.render(write_still=True)
        es.limpiar()
        x = 0.0
        for nombre in ["CerroJungla", "MontanaNieve1", "MontanaNieve2", "MesaDesierto", "AgujasDesierto", "TorresCiudad"]:
            w = objs[nombre].dimensions.x
            es.poner(nombre, x + w / 2, 0, 0)
            x += w + 30
        es.camara((x / 2, -x * 0.8, x * 0.3), (x / 2, 0, 60), 40.0)
        scene.render.filepath = os.path.join(RENDERS, "destinos_grandes.png")
        bpy.ops.render.render(write_still=True)
        es.limpiar()
        for b in ADORNOS:
            es.poner("Aeropuerto" + b, 0, 0, 0)
            es.poner("Borde" + b, 0, 0, 0)
            if b in LUCES:
                es.poner(LUCES[b], 0, 0, 0, mat=emisivo("FFE7A0", 6.0))
            es.camara((-520, -760, 330), (60, 80, 0), 50.0)
            scene.render.filepath = os.path.join(RENDERS, f"destinos_aeropuerto_{b.lower()}.png")
            bpy.ops.render.render(write_still=True)
            es.limpiar()
