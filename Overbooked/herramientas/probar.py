import json
import os
import subprocess
import sys
import time

CLAVE = os.environ.get("ROBLOX_API_KEY", "")
CABECERA = ["-H", f"x-api-key: {CLAVE}"] if CLAVE else []

UNIVERSO = "10774639088"
LUGAR = "70554923634533"
API = "https://apis.roblox.com/cloud/v2"


def curl(args):
    r = subprocess.run(["curl", "-sS", "-m", "60"] + CABECERA + args, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"crudo": r.stdout, "error": r.stderr}


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "pruebas", "servidor.luau")
    cuerpo = json.dumps({"script": open(ruta).read(), "timeout": "300s"})
    tarea = curl(["-X", "POST", "-H", "Content-Type: application/json", "--data", cuerpo,
                  f"{API}/universes/{UNIVERSO}/places/{LUGAR}/luau-execution-session-tasks"])
    camino = tarea.get("path")
    if not camino:
        print(json.dumps(tarea, indent=1, ensure_ascii=False))
        return
    for _ in range(120):
        time.sleep(5)
        estado = curl([f"{API}/{camino}"])
        if estado.get("state") in ("COMPLETE", "FAILED", "CANCELLED"):
            print(json.dumps(estado, indent=1, ensure_ascii=False))
            registros = curl([f"{API}/{camino}/logs"])
            print(json.dumps(registros, indent=1, ensure_ascii=False)[:6000])
            return
    print("Tiempo agotado", camino)


main()
