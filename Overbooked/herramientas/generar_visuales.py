import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTE = os.path.join(RAIZ, "arte")
IDS = os.path.join(ARTE, "ids_roblox.json")
SALIDA = os.path.join(RAIZ, "src", "shared", "Visuales.luau")


def v(x):
    return "Vector3.new(" + ", ".join(f"{round(c, 4)}" for c in x) + ")"


def main():
    ids = json.load(open(IDS)) if os.path.exists(IDS) else {}
    cajas = {}
    for carpeta in ("props", "avion", "pasajeros", "kit_interior", "kit_aeropuerto"):
        ruta = os.path.join(ARTE, carpeta, "manifest.json")
        if not os.path.exists(ruta):
            continue
        for e in json.load(open(ruta)):
            if "bbox_min" in e:
                cajas[e["nombre"]] = (e["bbox_min"], e["bbox_max"])
            elif "tamano" in e:
                x, y, z = e["tamano"]
                cajas[e["nombre"]] = ([-x / 2, 0, -z / 2], [x / 2, y, z / 2])
    lineas = ["--!strict", "export type Caja = { minimo: Vector3, maximo: Vector3 }", "", "local Visuales = {}", "",
              "Visuales.IDS = {"]
    for nombre in sorted(ids):
        if nombre in cajas:
            lineas.append(f"\t{nombre} = {ids[nombre]},")
    lineas.append("} :: { [string]: number }")
    lineas.append("")
    lineas.append("Visuales.CAJAS = {")
    for nombre in sorted(cajas):
        mn, mx = cajas[nombre]
        lineas.append(f"\t{nombre} = {{ minimo = {v(mn)}, maximo = {v(mx)} }},")
    lineas.append("} :: { [string]: Caja }")
    lineas.append("")
    lineas.append("return Visuales")
    with open(SALIDA, "w") as f:
        f.write("\n".join(lineas) + "\n")
    print(len(ids), "ids,", len(cajas), "cajas")


main()
