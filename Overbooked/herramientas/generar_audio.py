import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS = os.path.join(RAIZ, "arte", "ids_audio.json")
MANIFIESTO = os.path.join(RAIZ, "arte", "sonidos", "manifest.json")
SALIDA = os.path.join(RAIZ, "src", "shared", "Audio.luau")


def main():
    ids = json.load(open(IDS)) if os.path.exists(IDS) else {}
    datos = {e["nombre"]: e for e in json.load(open(MANIFIESTO))} if os.path.exists(MANIFIESTO) else {}
    lineas = ["--!strict", "export type Datos = { volumen: number, bucle: boolean, duracion: number }", "",
              "local Audio = {}", "", "Audio.IDS = {"]
    for nombre in sorted(ids):
        lineas.append(f"\t{nombre} = {ids[nombre]},")
    lineas.append("} :: { [string]: number }")
    lineas.append("")
    lineas.append("Audio.DATOS = {")
    for nombre in sorted(datos):
        e = datos[nombre]
        bucle = "true" if e.get("bucle") else "false"
        lineas.append(f"\t{nombre} = {{ volumen = {round(float(e.get('volumen', 0.6)), 3)}, bucle = {bucle}, duracion = {round(float(e.get('duracion', 1)), 3)} }},")
    lineas.append("} :: { [string]: Datos }")
    lineas.append("")
    lineas.append("return Audio")
    with open(SALIDA, "w") as f:
        f.write("\n".join(lineas) + "\n")
    print(len(ids), "ids,", len(datos), "datos")


main()
