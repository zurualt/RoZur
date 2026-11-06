import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
import uuid

RAIZ = pathlib.Path(__file__).resolve().parent.parent
UNIVERSO = "10774639088"
LUGAR = "70554923634533"
GRUPO = "783757619"
API = "https://apis.roblox.com"
DATOS = RAIZ / "marketing" / "pagina.json"
IDS = RAIZ / "marketing" / "ids_pagina.json"


def llamar(metodo, ruta, cuerpo=None, tipo="application/json"):
    cabeceras = {"x-api-key": os.environ["ROBLOX_API_KEY"]}
    datos = None
    if cuerpo is not None:
        datos = cuerpo if isinstance(cuerpo, bytes) else json.dumps(cuerpo).encode()
        cabeceras["Content-Type"] = tipo
    peticion = urllib.request.Request(API + ruta, data=datos, headers=cabeceras, method=metodo)
    try:
        with urllib.request.urlopen(peticion) as r:
            texto = r.read()
            return json.loads(texto) if texto else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{metodo} {ruta} -> {e.code} {e.read().decode(errors='replace')[:500]}")


def multipart(campos, archivo=None):
    limite = uuid.uuid4().hex
    partes = []
    for k, v in campos.items():
        partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    if archivo:
        partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="fileContent"; filename="{archivo.name}"\r\nContent-Type: image/png\r\n\r\n'.encode()
                      + archivo.read_bytes() + b"\r\n")
    partes.append(f"--{limite}--\r\n".encode())
    return b"".join(partes), f"multipart/form-data; boundary={limite}"


def subir_imagen(ruta, nombre):
    meta = json.dumps({"assetType": "Image", "displayName": f"Overbooked {nombre}"[:50], "description": "Overbooked! store page art",
                       "creationContext": {"creator": {"groupId": GRUPO}}})
    cuerpo, tipo = multipart({"request": meta}, ruta)
    op = llamar("POST", "/assets/v1/assets", cuerpo, tipo)
    for _ in range(60):
        r = llamar("GET", f"/assets/v1/{op['path']}")
        if r.get("done"):
            return r["response"]["assetId"]
        time.sleep(2)
    raise SystemExit(f"sin terminar {nombre}")


def descripcion():
    d = json.loads(DATOS.read_text(encoding="utf-8"))
    r = llamar("PATCH", f"/cloud/v2/universes/{UNIVERSO}/places/{LUGAR}?updateMask=description", {"description": d["descripcion"]["en"]})
    print("descripcion:", len(r.get("description", "")), "caracteres")


def imagenes(icono, previas):
    ids = json.loads(IDS.read_text()) if IDS.exists() else {}
    ruta_icono = pathlib.Path(icono)
    ids["icono"] = subir_imagen(ruta_icono, "Icono")
    print("icono", ids["icono"])
    lista = []
    for p in previas:
        ruta, alt = p.split("=", 1)
        ruta = pathlib.Path(ruta)
        ids[ruta.stem] = subir_imagen(ruta, ruta.stem)
        print(ruta.stem, ids[ruta.stem])
        lista.append({"asset": f"assets/{ids[ruta.stem]}", "altText": alt})
    IDS.write_text(json.dumps(ids, indent=2))
    cuerpo, tipo = multipart({"request": json.dumps({"assetId": LUGAR, "icon": f"assets/{ids['icono']}"})})
    llamar("PATCH", f"/assets/v1/assets/{LUGAR}?updateMask=icon", cuerpo, tipo)
    print("icono puesto")
    cuerpo, tipo = multipart({"request": json.dumps({"assetId": LUGAR, "previews": lista})})
    llamar("PATCH", f"/assets/v1/assets/{LUGAR}?updateMask=previews", cuerpo, tipo)
    print("miniaturas puestas:", len(lista))


if __name__ == "__main__":
    accion = sys.argv[1]
    if accion == "descripcion":
        descripcion()
    elif accion == "imagenes":
        imagenes(sys.argv[2], sys.argv[3:])
