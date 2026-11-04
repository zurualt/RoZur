import gzip
import hashlib
import json
import os
import pathlib
import re
import time
import urllib.request
import uuid

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "arte" / "interfaz"
IDS = CARPETA / "ids.json"
SALIDA = RAIZ / "src" / "shared" / "ImagenesGui.luau"
GRUPO = "783757619"
API = "https://apis.roblox.com/"


def llamar(url, datos=None, tipo=None):
    cabeceras = {"x-api-key": os.environ["ROBLOX_API_KEY"]}
    if tipo:
        cabeceras["Content-Type"] = tipo
    return json.load(urllib.request.urlopen(urllib.request.Request(url, data=datos, headers=cabeceras)))


def subir(ruta, nombre):
    limite = uuid.uuid4().hex
    meta = json.dumps({
        "assetType": "Decal",
        "displayName": f"Overbooked {nombre}"[:50],
        "description": "Interfaz de Overbooked! dibujada en Blender",
        "creationContext": {"creator": {"groupId": GRUPO}},
    })
    cuerpo = (
        f'--{limite}\r\nContent-Disposition: form-data; name="request"\r\nContent-Type: application/json\r\n\r\n{meta}\r\n'
        f'--{limite}\r\nContent-Disposition: form-data; name="fileContent"; filename="{ruta.name}"\r\nContent-Type: image/png\r\n\r\n'
    ).encode() + ruta.read_bytes() + f"\r\n--{limite}--\r\n".encode()
    op = llamar(API + "assets/v1/assets", cuerpo, f"multipart/form-data; boundary={limite}")
    for _ in range(120):
        if op.get("done"):
            break
        time.sleep(2)
        op = llamar(API + "assets/v1/operations/" + op["operationId"])
    respuesta = op.get("response")
    if not respuesta:
        raise RuntimeError(f"{nombre}: {op}")
    if "REJECTED" in respuesta.get("moderationResult", {}).get("moderationState", "").upper():
        raise RuntimeError(f"{nombre}: rechazado por moderación")
    return int(respuesta["assetId"])


def imagen_de(decal):
    for _ in range(40):
        try:
            datos = urllib.request.urlopen(llamar(API + f"asset-delivery-api/v1/assetId/{decal}")["location"]).read()
            if datos[:2] == b"\x1f\x8b":
                datos = gzip.decompress(datos)
            m = re.search(rb"(?:asset/\?id=|rbxassetid://)(\d+)", datos)
            if m:
                return int(m.group(1))
        except Exception:
            pass
        time.sleep(3)
    raise RuntimeError(f"Sin imagen para el decal {decal}")


def lua(v, sangria=1):
    if isinstance(v, dict):
        pad = "\t" * sangria
        cuerpo = "".join(f"{pad}{k if str(k).isidentifier() else '[' + json.dumps(k) + ']'} = {lua(x, sangria + 1)},\n" for k, x in v.items())
        return "{\n" + cuerpo + "\t" * (sangria - 1) + "}"
    if isinstance(v, (list, tuple)):
        return "{ " + ", ".join(lua(x, sangria) for x in v) + " }"
    if isinstance(v, bool):
        return "true" if v else "false"
    return json.dumps(v, ensure_ascii=False) if isinstance(v, str) else repr(v)


def main():
    ids = json.loads(IDS.read_text()) if IDS.exists() else {}
    manifiesto = json.loads((CARPETA / "manifest.json").read_text(encoding="utf-8"))
    for png in sorted(CARPETA.glob("*.png")):
        huella = hashlib.sha1(png.read_bytes()).hexdigest()
        if ids.get(png.stem, {}).get("sha1") == huella:
            continue
        decal = subir(png, png.stem)
        ids[png.stem] = {"id": imagen_de(decal), "decal": decal, "sha1": huella}
        IDS.write_text(json.dumps(ids, indent=1))
        print(png.stem, ids[png.stem]["id"], flush=True)
    datos = {
        "Paneles": {n: {"id": ids[n]["id"], "tam": p["tam"], "corte": p["corte"], "escala": p["escala"]} for n, p in manifiesto["paneles"].items() if n in ids},
        "Iconos": {"id": ids["Iconos"]["id"], "celda": manifiesto["celda"], "posiciones": manifiesto["iconos"]},
    }
    SALIDA.write_text("--!strict\nreturn " + lua(datos) + "\n", encoding="utf-8", newline="\n")
    print("ImagenesGui.luau con", len(datos["Paneles"]), "paneles y", len(datos["Iconos"]["posiciones"]), "iconos")


main()
