import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTE = os.path.join(RAIZ, "arte")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ORDEN = ["props", "avion", "pasajeros", "kit_interior", "kit_aeropuerto", "kit_extra", "kit_isla", "kit_cabina", "kit_lobby"]
P = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
COS = math.cos(math.radians(2.0))
with open(os.path.join(RAIZ, "herramientas", "separar_capas.py"), encoding="utf-8") as _fh:
    exec(compile(_fh.read(), "separar_capas.py", "exec"))


def lista(nombre):
    r = []
    for i, a in enumerate(ARGS):
        if a == nombre and i + 1 < len(ARGS):
            r += ARGS[i + 1].split(",")
    return r


def valor(nombre, defecto):
    v = lista(nombre)
    return float(v[0]) if v else defecto


HUECO = valor("--hueco", 0.04)
AREA = valor("--area", 0.0025)
MAXIMO = int(valor("--max", 25))


def catalogo():
    carpetas = [c for c in ORDEN if os.path.isdir(os.path.join(ARTE, c))]
    carpetas += sorted(c for c in os.listdir(ARTE) if c not in carpetas and os.path.isfile(os.path.join(ARTE, c, "manifest.json")))
    piezas = {}
    for c in carpetas:
        with open(os.path.join(ARTE, c, "manifest.json"), encoding="utf-8") as fh:
            man = json.load(fh)
        for e in man if isinstance(man, list) else []:
            nombre = e.get("nombre")
            ruta = os.path.join(ARTE, c, e.get("archivo", (nombre or "") + ".fbx"))
            if not nombre or not ruta.lower().endswith(".fbx") or not os.path.exists(ruta):
                continue
            if "bbox_min" in e:
                caja = (Vector(e["bbox_min"]), Vector(e["bbox_max"]))
            elif "tamano" in e:
                x, y, z = e["tamano"]
                caja = (Vector((-x / 2, 0, -z / 2)), Vector((x / 2, y, z / 2)))
            else:
                caja = None
            piezas[nombre] = (c, ruta, caja)
    return carpetas, piezas


def imagen_de(ob):
    for slot in ob.material_slots:
        m = slot.material
        if m and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image:
                    img = n.image
                    w, h = img.size
                    if w and h:
                        return (w, h, list(img.pixels[:]))
    return None


CACHE = {}


def cargar(ruta):
    if ruta in CACHE:
        return CACHE[ruta]
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=ruta, axis_forward="Z", axis_up="Y")
    nuevos = [o for o in bpy.data.objects if o not in antes]
    caras = []
    for ob in nuevos:
        if ob.type != "MESH":
            continue
        mat = ob.matrix_world.copy()
        me = ob.data
        me.calc_loop_triangles()
        uv = me.uv_layers.active
        img = imagen_de(ob)
        for lt in me.loop_triangles:
            vs = [P @ (mat @ me.vertices[i].co) for i in lt.vertices]
            color = None
            if uv and img:
                u = sum(uv.data[l].uv[0] for l in lt.loops) / 3
                v = sum(uv.data[l].uv[1] for l in lt.loops) / 3
                w, h, px = img
                x = min(w - 1, max(0, int(u % 1.0 * w)))
                y = min(h - 1, max(0, int(v % 1.0 * h)))
                o = (y * w + x) * 4
                color = (round(px[o], 2), round(px[o + 1], 2), round(px[o + 2], 2))
            elif uv:
                u = sum(uv.data[l].uv[0] for l in lt.loops) / 3
                v = sum(uv.data[l].uv[1] for l in lt.loops) / 3
                color = (round(u, 2), round(v, 2), -1)
            caras.append((vs, color))
    for o in nuevos:
        d = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o)
        if d is not None and d.users == 0:
            bpy.data.meshes.remove(d)
    CACHE[ruta] = caras
    return caras


def preparar(vs):
    a, b, c = vs
    n = (b - a).cross(c - a)
    doble = n.length
    if doble < 2e-5:
        return None
    n /= doble
    return n, (a + b + c) / 3, doble / 2


def misma_tinta(a, b):
    if a is None or b is None:
        return False
    return max(abs(x - y) for x, y in zip(a, b)) < 0.03


def auditar(caras, nombres, mismo, titulo):
    pares = candidatos(caras, mismo)
    grupos = {}
    for ia, ib in pares:
        r = solape(caras[ia], caras[ib], HUECO, AREA, COS)
        if not r:
            continue
        _, hueco, area = r
        fa, fb = caras[ia], caras[ib]
        igual = misma_tinta(fa.color, fb.color)
        clave = (nombres[fa.inst], nombres[fb.inst]) if not mismo else (nombres[fa.inst],)
        tintas = tuple(sorted((hexa(fa.color), hexa(fb.color))))
        g = grupos.setdefault((clave, igual, tintas), {"n": 0, "area": 0.0, "hueco": 9.0, "donde": None, "mayor": 0.0})
        g["n"] += 1
        g["area"] += area
        g["hueco"] = min(g["hueco"], hueco)
        if area > g["mayor"]:
            g["mayor"] = area
            g["donde"] = (fa.c + fb.c) / 2
    filas = []
    for (clave, igual, tintas), g in grupos.items():
        if igual:
            sev = "BAJA"
        elif g["area"] >= 0.05:
            sev = "ALTA"
        else:
            sev = "MEDIA"
        filas.append((sev, clave + (tintas[0] + "/" + tintas[1],), g))
    orden = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
    filas.sort(key=lambda f: (orden[f[0]], -f[2]["area"]))
    cuenta = {k: sum(1 for f in filas if f[0] == k) for k in orden}
    print(f"\n== {titulo}: {len(caras)} triangulos, {cuenta['ALTA']} ALTA, {cuenta['MEDIA']} MEDIA, {cuenta['BAJA']} BAJA (misma tinta)")
    for sev, clave, g in filas[:MAXIMO]:
        d = g["donde"]
        print(f"  {sev:5s} {' | '.join(clave):58s} en ({d.x:7.2f},{d.y:7.2f},{d.z:7.2f})  hueco {g['hueco']:.3f}  area {g['area']:7.3f}  x{g['n']}")
    if len(filas) > MAXIMO:
        print(f"  ... {len(filas) - MAXIMO} grupos mas")
    return cuenta


def hexa(color):
    if color is None:
        return "?"
    if color[2] == -1:
        return "uv%.2f,%.2f" % (color[0], color[1])
    return "%02X%02X%02X" % tuple(int(max(0.0, min(1.0, c)) * 255 + 0.5) for c in color)


def caras_de(tris, mat, inst, salida):
    nuevas = []
    for vs, color in tris:
        w = [mat @ p for p in vs]
        r = preparar(w)
        if r:
            n, c, area = r
            nuevas.append(Cara(w, n, c, area, color, inst))
    if nuevas:
        suelo = min(p.y for f in nuevas for p in f.vs)
        nuevas = [f for f in nuevas if not (f.n.y < -0.95 and max(p.y for p in f.vs) < suelo + 0.02)]
    salida.extend(nuevas)


def kit(carpeta, piezas):
    caras, nombres = [], []
    for nombre, (c, ruta, _) in sorted(piezas.items()):
        if c != carpeta:
            continue
        nombres.append(nombre)
        caras_de(cargar(ruta), Matrix.Identity(4), len(nombres) - 1, caras)
    return auditar(caras, nombres, True, f"kit {carpeta} (dentro de cada malla, coordenadas locales de Roblox)")


def cframe(cf):
    pos, o = cf["position"], cf["orientation"]
    return Matrix(((o[0][0], o[0][1], o[0][2], pos[0]), (o[1][0], o[1][1], o[1][2], pos[1]),
                   (o[2][0], o[2][1], o[2][2], pos[2]), (0, 0, 0, 1)))


def caja_de(tris):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for vs, _ in tris:
        for p in vs:
            for i in range(3):
                mn[i] = min(mn[i], p[i])
                mx[i] = max(mx[i], p[i])
    return mn, mx


def colocacion(nombre, piezas, escala):
    _, ruta, esperada = piezas[nombre]
    tris = cargar(ruta)
    mn, mx = caja_de(tris)
    if esperada is None:
        return tris, Matrix.Identity(4)
    emn, emx = esperada[0] * escala, esperada[1] * escala
    medida = mx - mn
    s = max(emx - emn) / max(medida) if max(medida) > 1e-6 else 1.0
    mc = (mn + mx) / 2
    ec = (emn + emx) / 2
    return tris, Matrix.Translation(ec) @ Matrix.Scale(s, 4) @ Matrix.Translation(-mc)


def giro_plano(o):
    look = Vector((-o[0][2], -o[1][2], -o[2][2]))
    look.y = 0
    if look.length < 1e-3:
        return Matrix.Identity(4)
    look.normalize()
    a = math.atan2(-look.x, -look.z)
    return Matrix.Rotation(a, 4, Vector((0, 1, 0)))


CARAS_CAJA = [((0, 1, 3, 2), (-1, 0, 0)), ((4, 6, 7, 5), (1, 0, 0)), ((0, 4, 5, 1), (0, -1, 0)), ((2, 3, 7, 6), (0, 1, 0)),
              ((0, 2, 6, 4), (0, 0, -1)), ((1, 5, 7, 3), (0, 0, 1))]


def caras_parte(props, clase, inst, salida):
    s = Vector(props.get("Size", [1, 1, 1])) / 2
    cf = cframe(props["CFrame"]["CFrame"])
    color = tuple(round(c, 2) for c in props.get("Color", [0.6, 0.6, 0.6]))
    forma = props.get("Shape", "Block")
    if forma in ("Ball", "Cylinder"):
        return
    esq = [Vector((x, y, z)) for x in (-s.x, s.x) for y in (-s.y, s.y) for z in (-s.z, s.z)]
    if clase == "WedgePart":
        pts = [Vector(p) for p in ((-s.x, -s.y, -s.z), (s.x, -s.y, -s.z), (s.x, -s.y, s.z), (-s.x, -s.y, s.z), (-s.x, s.y, s.z), (s.x, s.y, s.z))]
        poli = [(0, 1, 2, 3), (3, 2, 5, 4), (0, 4, 5, 1), (0, 3, 4), (1, 5, 2)]
    else:
        pts = esq
        poli = [q for q, _ in CARAS_CAJA]
    w = [cf @ p for p in pts]
    for q in poli:
        for k in range(1, len(q) - 1):
            tri = [w[q[0]], w[q[k]], w[q[k + 1]]]
            r = preparar(tri)
            if not r:
                continue
            n, c, area = r
            centro = sum(w, Vector()) / len(w)
            if n.dot(c - centro) < 0:
                tri = [tri[0], tri[2], tri[1]]
                n = -n
            salida.append(Cara(tri, n, c, area, color, inst))


def mapa(nombre, piezas):
    with open(os.path.join(RAIZ, "mapa", nombre + ".model.json"), encoding="utf-8") as fh:
        datos = json.load(fh)
    caras, nombres = [], []
    faltan = set()

    def instancia(etiqueta):
        nombres.append(etiqueta)
        return len(nombres) - 1

    def recorrer(nodo, oculto):
        props = nodo.get("properties", {})
        atr = nodo.get("attributes", {})
        clase = nodo.get("className", "Folder")
        visual = atr.get("Visual")
        esconde = oculto
        if "CFrame" in props and clase not in ("Model", "Folder"):
            if isinstance(visual, str):
                esconde = True
                if visual in piezas:
                    cf = cframe(props["CFrame"]["CFrame"])
                    if atr.get("Movil"):
                        base = cf @ Matrix.Translation(Vector((0, -props["Size"][1] / 2, 0)))
                        e = atr.get("Escala", 1.0)
                    else:
                        o = props["CFrame"]["CFrame"]["orientation"]
                        tam = props.get("Size", [1, 1, 1])
                        medio = abs(o[1][0]) * tam[0] / 2 + abs(o[1][1]) * tam[1] / 2 + abs(o[1][2]) * tam[2] / 2
                        y = atr.get("Base", cf.translation.y - medio)
                        base = Matrix.Translation(Vector((cf.translation.x, y, cf.translation.z))) @ giro_plano(o)
                        e = 1.0
                    tris, local = colocacion(visual, piezas, e)
                    caras_de(tris, base @ local, instancia(visual), caras)
                else:
                    faltan.add(visual)
            elif not oculto and props.get("Transparency", 0) < 0.99:
                caras_parte(props, clase, instancia(nodo.get("name", "?") + " (parte)"), caras)
        for h in nodo.get("children", []):
            recorrer(h, esconde)

    recorrer(datos, False)
    if nombre == "Avion" and "AvionExterior" in piezas:
        tris, local = colocacion("AvionExterior", piezas, 1.0)
        caras_de(tris, local, instancia("AvionExterior"), caras)
    if faltan:
        print(f"\n(mapa {nombre}: sin modelo para {', '.join(sorted(faltan))})")
    return auditar(caras, nombres, False, f"mapa {nombre} (entre piezas colocadas como en el juego, coordenadas de Roblox)")


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    carpetas, piezas = catalogo()
    kits = lista("--kit")
    if "todos" in kits:
        kits = carpetas
    mapas = lista("--mapa")
    if "todos" in mapas:
        mapas = [f[:-len(".model.json")] for f in sorted(os.listdir(os.path.join(RAIZ, "mapa"))) if f.endswith(".model.json")]
    if not kits and not mapas:
        print("uso: blender -b --factory-startup -P herramientas/auditar_solapes.py -- --kit kit_lobby[,otro|todos] --mapa Aeropuerto[,..|todos] [--hueco 0.04] [--area 0.0025] [--max 25]")
        return
    print(f"caras paralelas (<2 grados, mismo sentido) a menos de {HUECO} studs que se solapan mas de {AREA} studs^2")
    for k in kits:
        kit(k, piezas)
    for m in mapas:
        mapa(m, piezas)


main()
