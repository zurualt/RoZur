import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

OUT = os.path.dirname(os.path.abspath(__file__))
ARTE = os.path.dirname(OUT)
RAIZ = os.path.dirname(ARTE)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

ruta = os.path.join(RAIZ, "herramientas", "vista_previa.py")
src = open(ruta, encoding="utf-8").read()
src = src[:src.rstrip().rfind("\nmain()")]
src = src.replace('"kit_aeropuerto", "kit_extra")', '"kit_aeropuerto", "kit_extra", "kit_lobby")')
V = {"__file__": ruta, "__name__": "vista"}
exec(compile(src, ruta, "exec"), V)

CAJAS = {e["nombre"]: e for e in json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8")) if "bbox_min" in e}
TECHO = {"LobbyTecho", "TechoTerminal", "Tragaluz"}
puestos = []


def colocar(nombre, cf):
    e = CAJAS.get(nombre)
    if e:
        mn, mx = e["bbox_min"], e["bbox_max"]
        cf = cf @ Matrix.Translation(Vector(((mn[0] + mx[0]) / 2, mn[1], (mn[2] + mx[2]) / 2)))
    ob = V["colocar"](nombre, cf)
    if ob:
        puestos.append((nombre, ob))
    return ob


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    escena = bpy.context.scene
    avion = json.load(open(os.path.join(RAIZ, "mapa", "Avion.model.json"), encoding="utf-8"))
    aero = json.load(open(os.path.join(RAIZ, "mapa", "Aeropuerto.model.json"), encoding="utf-8"))
    for h in avion["children"]:
        V["recorrer"](h, ["Avion"], [])
    for h in aero["children"]:
        V["recorrer"](h, ["Aeropuerto"], [])
    casco = V["plantilla"]("AvionExterior")
    if casco:
        c = casco.copy()
        escena.collection.objects.link(c)
        c.hide_render = False
        c.matrix_world = Matrix.Translation((0, 0, 100))
        puestos.append(("AvionExterior", c))
    for nombre, props, atributos in V["marcadores"]:
        visual = atributos.get("Visual")
        if visual and atributos.get("Movil"):
            colocar(visual, V["cframe"](props["CFrame"]["CFrame"]) @ Matrix.Translation(Vector((0, -props["Size"][1] / 2, 0))))
        elif visual:
            colocar(visual, V["base_marcador"](props, atributos))
    for nombre, x, z, giro in (("Maleta1", 96.5, -54.0, 20), ("Maleta2", 104.0, -48.6, 80), ("Maleta3", 92.0, -50.5, -30)):
        colocar(nombre, Matrix.Translation(Vector((x, 91.75, z))) @ Matrix.Rotation(math.radians(giro), 4, Vector((0, 1, 0))))
    colores = [(0.545, 0.824, 0.298), (0.627, 0.486, 0.949), (0.949, 0.482, 0.71), (0.961, 0.804, 0.239)]
    for i, (x, z, a) in enumerate(((78, -2, 200), (62, -8, 90), (90, 4, 160), (60.5, -27, 170))):
        V["tripulante"](colores[i], Matrix.Translation(Vector((x, 90.5, z))) @ Matrix.Rotation(math.radians(a), 4, Vector((0, 1, 0))), str(i))
    mundo = bpy.data.worlds.new("Cielo")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs[0].default_value = (*V["lin"]((0.68, 0.84, 0.95)), 1)
    mundo.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    escena.world = mundo
    sol = bpy.data.lights.new("Sol", "SUN")
    sol.energy = 3.2
    sol.angle = math.radians(8)
    so = bpy.data.objects.new("Sol", sol)
    so.rotation_euler = (math.radians(52), 0, math.radians(-120))
    escena.collection.objects.link(so)
    luces = []

    def buscar(n):
        if n.get("name") == "LamparaLobby":
            luces.append(n["properties"]["CFrame"]["CFrame"]["position"])
        for k in n.get("children", []):
            buscar(k)
    buscar(aero)
    for pos in luces:
        l = bpy.data.lights.new("Luz", "POINT")
        l.energy = float(os.environ.get("LAMPARA", "1400"))
        l.color = (1.0, 0.86, 0.66)
        l.shadow_soft_size = 1.0
        lo = bpy.data.objects.new("Luz", l)
        lo.location = V["rb"]((pos[0], pos[1] - 0.6, pos[2])).to_3d()
        escena.collection.objects.link(lo)
    escena.render.engine = "CYCLES"
    escena.cycles.device = "CPU"
    escena.cycles.samples = int(os.environ.get("MUESTRAS", "40"))
    escena.cycles.use_denoising = True
    escena.render.threads_mode = "FIXED"
    escena.render.threads = 15
    escena.render.resolution_x = int(os.environ.get("ANCHO", "1280"))
    escena.render.resolution_y = int(os.environ.get("ALTO", "720"))
    try:
        escena.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    salida = os.environ.get("SALIDA", OUT)
    vistas = [
        ("lobby_spawn", (84, 95.2, 13), (82, 94.5, -30), 15, False),
        ("lobby_puertas", (80, 95.5, 16), (56, 93.5, -20), 16, False),
        ("lobby_puerta2", (74, 95.2, -16), (52, 95.5, -30), 17, False),
        ("lobby_cinta", (84, 95.5, -24), (106, 92, -52), 16, False),
        ("lobby_cafe", (84, 95.2, -2), (106, 92.5, 20), 16, False),
        ("lobby_arriba", (82, 215, 30), (82, 90, -26), 22, True),
        ("lobby_fuera", (8, 128, 92), (84, 98, -20), 24, False),
        ("lobby_info", (93, 95.2, 0), (88, 93.5, -10), 20, False),
        ("lobby_facturacion", (98, 95.2, -2), (110, 92.5, -18), 18, False),
        ("lobby_tienda", (90, 95.2, -2), (70, 93.5, 20), 17, False),
    ]
    solo = os.environ.get("VISTAS")
    for nombre, desde, hacia, lente, sin_techo in vistas:
        if solo and nombre not in solo.split(","):
            continue
        for n, ob in puestos:
            if n in TECHO:
                ob.hide_render = sin_techo
        for n, obs in V["creados"].items():
            if n in TECHO:
                for ob in obs:
                    ob.hide_render = sin_techo
        escena.camera = V["camara"](nombre, desde, hacia, lente)
        escena.render.filepath = os.path.join(salida, nombre + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDER", nombre)


main()
