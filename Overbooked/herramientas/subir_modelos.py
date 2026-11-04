import json
import os
import subprocess
import sys
import time

GRUPO = "783757619"
API = "https://apis.roblox.com/assets/v1"


def subir(ruta, nombre):
    peticion = json.dumps({
        "assetType": "Model",
        "displayName": f"Overbooked {nombre}",
        "description": f"Modelo {nombre} de Overbooked!",
        "creationContext": {"creator": {"groupId": GRUPO}},
    })
    r = subprocess.run(["curl", "-sS", "-m", "180", "-X", "POST", "-F", f"request={peticion}",
                        "-F", f"fileContent=@{ruta};type=model/fbx", f"{API}/assets"],
                       capture_output=True, text=True)
    datos = json.loads(r.stdout)
    operacion = datos.get("operationId")
    if not operacion:
        return None, datos
    for _ in range(40):
        time.sleep(3)
        r = subprocess.run(["curl", "-sS", "-m", "60", f"{API}/operations/{operacion}"], capture_output=True, text=True)
        estado = json.loads(r.stdout)
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
        asset, info = subir(ruta, nombre)
        estado = (info or {}).get("moderationResult", {}).get("moderationState", "?")
        print(nombre, asset, estado, flush=True)
        if asset:
            resultados[nombre] = int(asset)
        json.dump(resultados, open(salida, "w"), indent=1, ensure_ascii=False)


main()
