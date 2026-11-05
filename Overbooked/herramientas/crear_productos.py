import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
import uuid

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ICONOS = RAIZ / "arte" / "robux"
CONFIG = RAIZ / "src" / "shared" / "Config.luau"
IDS = ICONOS / "productos.json"
UNIVERSO = "10774639088"
API = "https://apis.roblox.com"

PASE = {
    "clave": "VidasInfinitas",
    "name": "Infinite Lives",
    "description": "Fall out of the plane? You're back on board in 4 seconds instead of waiting. Forever.",
    "price": 59,
}
PRODUCTOS = [
    {"clave": "Revivir", "name": "Revive", "price": 14,
     "description": "Get back on the plane instantly after falling, or revive a fallen crewmate. Saved for later if you can't use it right away."},
    {"clave": "Cabra", "name": "Goat on Board", "price": 15,
     "description": "Release a crazy goat in the cabin mid-flight. If the crew lands, everyone gets +120 coins."},
    {"clave": "Gallinas", "name": "Chicken Stampede", "price": 15,
     "description": "A chicken crate bursts open mid-flight. If the crew lands, everyone gets +120 coins."},
    {"clave": "Disco", "name": "Disco Fever", "price": 19,
     "description": "Disco ball on, everybody dance, mid-flight. If the crew lands, everyone gets +120 coins."},
    {"clave": "Pajaros", "name": "Bird Strike", "price": 25,
     "description": "A flock of birds straight into the engine. If the crew lands, everyone gets +120 coins."},
    {"clave": "CaidaLibre", "name": "Free Fall", "price": 29,
     "description": "Zero gravity for a few seconds mid-flight. If the crew lands, everyone gets +120 coins."},
    {"clave": "Piratas", "name": "Sky Pirates", "price": 49,
     "description": "Sky pirates come to board the plane. If the crew lands, everyone gets +120 coins."},
]


def llamar(metodo, ruta, campos=None, archivo=None):
    cabeceras = {"x-api-key": os.environ["ROBLOX_API_KEY"]}
    datos = None
    if campos is not None:
        limite = uuid.uuid4().hex
        partes = []
        for k, v in campos.items():
            partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        if archivo and archivo.exists():
            partes.append(
                f'--{limite}\r\nContent-Disposition: form-data; name="imageFile"; filename="{archivo.name}"\r\nContent-Type: image/png\r\n\r\n'.encode()
                + archivo.read_bytes() + b"\r\n")
        partes.append(f"--{limite}--\r\n".encode())
        datos = b"".join(partes)
        cabeceras["Content-Type"] = f"multipart/form-data; boundary={limite}"
    peticion = urllib.request.Request(API + ruta, data=datos, headers=cabeceras, method=metodo)
    for intento in range(5):
        try:
            with urllib.request.urlopen(peticion) as r:
                cuerpo = r.read()
                return json.loads(cuerpo) if cuerpo else {}
        except urllib.error.HTTPError as e:
            if e.code == 429 and intento < 4:
                time.sleep(2 + intento * 2)
                continue
            raise SystemExit(f"{metodo} {ruta} -> {e.code} {e.read().decode(errors='replace')[:400]}")


def listar(ruta, clave):
    vistos, ficha = [], None
    while True:
        r = llamar("GET", ruta + (f"?pageSize=50&pageToken={ficha}" if ficha else "?pageSize=50"))
        vistos += r.get(clave) or []
        ficha = r.get("nextPageToken")
        if not ficha:
            return vistos


def main():
    ids = json.loads(IDS.read_text()) if IDS.exists() else {}
    pases = {p["name"]: p["gamePassId"] for p in listar(f"/game-passes/v1/universes/{UNIVERSO}/game-passes/creator", "gamePasses")}
    productos = {p["name"]: p["productId"] for p in listar(f"/developer-products/v2/universes/{UNIVERSO}/developer-products/creator", "developerProducts")}

    if PASE["name"] in pases:
        ids[PASE["clave"]] = pases[PASE["name"]]
    elif PASE["clave"] not in ids:
        r = llamar("POST", f"/game-passes/v1/universes/{UNIVERSO}/game-passes",
                   {"name": PASE["name"], "description": PASE["description"], "isForSale": "true", "price": str(PASE["price"])},
                   ICONOS / f"{PASE['clave']}.png")
        ids[PASE["clave"]] = r["gamePassId"]
        print("pase creado", PASE["name"], r["gamePassId"])
    for p in PRODUCTOS:
        if p["name"] in productos:
            ids[p["clave"]] = productos[p["name"]]
            continue
        if p["clave"] in ids:
            continue
        r = llamar("POST", f"/developer-products/v2/universes/{UNIVERSO}/developer-products",
                   {"name": p["name"], "description": p["description"], "isForSale": "true", "price": str(p["price"])},
                   ICONOS / f"{p['clave']}.png")
        ids[p["clave"]] = r["productId"]
        print("producto creado", p["name"], r["productId"])
        time.sleep(0.5)
    IDS.write_text(json.dumps(ids, indent=2))

    texto = CONFIG.read_text(encoding="utf-8")
    texto = re.sub(r"PASE_VIDAS = \d+,", f"PASE_VIDAS = {ids['VidasInfinitas']},", texto)
    texto = re.sub(r"\tREVIVIR = \d+,", f"\tREVIVIR = {ids['Revivir']},", texto)
    for p in PRODUCTOS[1:]:
        texto = re.sub(r'(\{ nombre = "' + p["clave"] + r'", producto = )\d+', r"\g<1>" + str(ids[p["clave"]]), texto)
    CONFIG.write_text(texto, encoding="utf-8")
    print(json.dumps(ids, indent=2))


if __name__ == "__main__":
    sys.exit(main())
