import json
import os
import subprocess
import sys
import time

GRUPO = "783757619"
API = "https://apis.roblox.com/assets/v1"


def subir(ruta, nombre):
    peticion = json.dumps({
        "assetType": "Audio",
        "displayName": f"Overbooked {nombre}",
        "description": f"Sonido {nombre} de Overbooked!",
        "creationContext": {"creator": {"groupId": GRUPO}},
    })
    r = subprocess.run(["curl", "-sS", "-m", "180", "-X", "POST", "-F", f"request={peticion}",
                        "-F", f"fileContent=@{ruta};type=audio/ogg", f"{API}/assets"],
                       capture_output=True, text=True)
    try:
        datos = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None, {"crudo": r.stdout[:300]}
    operacion = datos.get("operationId")
    if not operacion:
        return None, datos
    for _ in range(40):
        time.sleep(3)
        r = subprocess.run(["curl", "-sS", "-m", "60", f"{API}/operations/{operacion}"], capture_output=True, text=True)
        try:
            estado = json.loads(r.stdout)
        except json.JSONDecodeError:
            continue
        if estado.get("done"):
            respuesta = estado.get("response", {})
            return respuesta.get("assetId"), respuesta
    return None, {"error": "timeout", "operationId": operacion}


def main():
    salida = sys.argv[1]
    archivos = sys.argv[2:]
    resultados = json.load(open(salida)) if os.path.exists(salida) else {}
    for ruta in archivos:
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        if nombre in resultados and "--forzar" not in sys.argv:
            print(nombre, resultados[nombre], "ya subido", flush=True)
            continue
        asset, info = subir(ruta, nombre)
        estado = (info or {}).get("moderationResult", {}).get("moderationState", "?")
        print(nombre, asset, estado, "" if asset else json.dumps(info)[:200], flush=True)
        if asset:
            resultados[nombre] = int(asset)
        json.dump(resultados, open(salida, "w"), indent=1, ensure_ascii=False)
        time.sleep(1.5)


main()
