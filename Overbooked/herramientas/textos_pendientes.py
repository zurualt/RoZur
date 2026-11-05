import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TEXTOS = RAIZ / "src" / "shared" / "Textos.luau"
SALTAR = {"Textos.luau", "Idioma.luau", "ImagenesGui.luau", "ImagenesVfx.luau", "ImagenesIntro.luau", "Visuales.luau"}

CONTEXTO_FUERA = re.compile(
    r"(GetAttribute|SetAttribute|GetAttributeChangedSignal|FindFirstChild\w*|WaitForChild|FindFirstAncestor\w*|IsA|"
    r"Instance\.new|GetService|reproducir|emitir\w*|bucle|GetTagged|HasTag|AddTag|RemoveTag|GetInstance\w+Signal|require|"
    r"Font\.new|ponerIcono|icono|panel|barra|FireServer|warn|print|error|assert|fallar|lanzar|tipo|GetPropertyChangedSignal|"
    r"BindAction|UnbindAction|BindToRenderStep|UnbindFromRenderStep|gsub|match|find|gmatch|sub|format|volumen|"
    r"Clone|efecto|sumar|atributo|fase|numero\w*|SetTitle)\(\s*(\w+\s*,\s*)*$"
    r"|(==|~=)\s*$|\[\s*$|\b(Name|Image|Texture|SoundId|AnimationId|Icono|icono|visual|Visual|clave|tipo|Tipo|codigo)\s*=\s*$"
)
CONTEXTO_DENTRO = re.compile(r"(\bText\s*=|ActionText|ObjectText|texto|titulo|descripcion|motivo|aviso|mensaje|fila|linea|tarea|boton|cartel|PEDIDOS|NOMBRES|SetTitle|textos|FRASES|DESPEDIDAS|sellar|palabra|deslizador|\"Accion\"|\"Objeto\")(?!.*[\"'`]\s*,\s*\w+\s*=)", re.I)
TEXTO_UI = re.compile(r"(\bText\s*=|ActionText|ObjectText|SetTitle)")
TAG = re.compile(r"<[^>]*>")

IGNORAR = {
    "%d:%02d",
    "Dark stone grey",
    "info",
    "peligro",
    "bien",
    "Gas+",
    "Gas-",
    "VIP",
    "English",
    "Español",
    "Português",
    "Français",
    "Accion",
    "Fov",
    "Musica",
    "Objeto",
    "ON",
    "OFF",
    "AUTO",
    "WC",
    '<font color="#6DBE45"><b>ON</b></font>',
}


def recursos() -> set:
    nombres = set()
    for nombre in ("ImagenesGui.luau", "ImagenesVfx.luau", "ImagenesIntro.luau"):
        archivo = RAIZ / "src" / "shared" / nombre
        if archivo.exists():
            nombres |= set(re.findall(r"^\s+(\w+) = ", archivo.read_text(encoding="utf-8"), re.M))
    return nombres


def literales(fuente: str):
    resultado = []
    interiores: list = []
    n = len(fuente)
    linea = 1

    def leer_cadena(i: int, cierre: str):
        partes = []
        j = i + 1
        while j < n:
            c = fuente[j]
            if c == "\\" and j + 1 < n:
                sig = fuente[j + 1]
                partes.append({"n": "\n", "t": "\t", '"': '"', "'": "'", "\\": "\\", "`": "`", "{": "{"}.get(sig, "\\" + sig))
                j += 2
                continue
            if c == cierre or c == "\n":
                return "".join(partes), j + 1
            if cierre == "`" and c == "{":
                k, profundidad = j + 1, 1
                while k < n and profundidad > 0:
                    if fuente[k] in "\"'`":
                        _, k = leer_cadena(k, fuente[k])
                        continue
                    profundidad += {"{": 1, "}": -1}.get(fuente[k], 0)
                    k += 1
                interiores.append(fuente[j + 1 : k - 1])
                partes.append("{}")
                j = k
                continue
            partes.append(c)
            j += 1
        return "".join(partes), j

    i = 0
    while i < n:
        c = fuente[i]
        if c == "\n":
            linea += 1
            i += 1
        elif fuente.startswith("--[[", i) or fuente.startswith("[[", i):
            fin = fuente.find("]]", i)
            linea += fuente.count("\n", i, fin)
            i = fin + 2
        elif fuente.startswith("--", i):
            fin = fuente.find("\n", i)
            i = n if fin < 0 else fin
        elif c in "\"'`":
            contexto = fuente[fuente.rfind("\n", 0, i) + 1 : i]
            interiores.clear()
            texto, i = leer_cadena(i, c)
            padre = (texto, contexto)
            resultado.append((texto, linea, contexto, None))
            for expresion in list(interiores):
                for t, _, ctx, _ in literales(expresion):
                    resultado.append((t, linea, ctx, padre))
        else:
            i += 1
    return resultado


def visible(texto: str, contexto: str, heredado: bool, nombres_recursos: set) -> bool:
    limpio = TAG.sub("", texto).replace("{}", "")
    if len(re.findall(r"[^\W\d_]", limpio)) < 2 or texto in IGNORAR or "://" in texto:
        return False
    if re.fullmatch(r"\w+", texto) and ("_" in texto or re.search(r"[a-z][A-Z]|\d", texto)):
        return False
    if CONTEXTO_FUERA.search(contexto.rstrip()):
        return False
    if texto in nombres_recursos and not TEXTO_UI.search(contexto):
        return False
    if heredado or " " in limpio.strip() or re.search(r"[^\x00-\x7f]", limpio) or re.fullmatch(r"[A-Z0-9 .]{2,}", limpio):
        return True
    return bool(CONTEXTO_DENTRO.search(contexto))


def normalizar(texto: str) -> str:
    return re.sub(r"\{\d*\}", "{}", texto).strip(" ·")


def claves() -> set:
    if not TEXTOS.exists():
        return set()
    encontradas = set()
    for m in re.finditer(r'^\s*\["((?:[^"\\]|\\.)*)"\]\s*=', TEXTOS.read_text(encoding="utf-8"), re.M):
        crudo = re.sub(r"\\(.)", lambda e: {"n": "\n", "t": "\t"}.get(e.group(1), e.group(1)), m.group(1))
        encontradas.add(normalizar(crudo))
    return encontradas


def textos_mapa():
    def recorrer(nodo, archivo):
        if isinstance(nodo, dict):
            texto = nodo.get("Text")
            if isinstance(texto, str):
                yield texto, archivo
            for v in nodo.values():
                yield from recorrer(v, archivo)
        elif isinstance(nodo, list):
            for v in nodo:
                yield from recorrer(v, archivo)

    for archivo in sorted((RAIZ / "mapa").glob("*.json")):
        yield from recorrer(json.loads(archivo.read_text(encoding="utf-8")), archivo.relative_to(RAIZ).as_posix())


def candidatos():
    nombres_recursos = recursos()
    for archivo in sorted((RAIZ / "src").rglob("*.luau")):
        if archivo.name in SALTAR:
            continue
        relativo = archivo.relative_to(RAIZ).as_posix()
        for texto, linea, contexto, padre in literales(archivo.read_text(encoding="utf-8")):
            heredado = padre is not None and visible(padre[0], padre[1], False, nombres_recursos)
            if visible(texto, contexto, heredado, nombres_recursos):
                yield normalizar(texto), f"{relativo}:{linea}"
    for texto, archivo in textos_mapa():
        if re.search(r"[^\W\d_]{2}", texto) and texto not in IGNORAR:
            yield texto, archivo


def luau(texto: str) -> str:
    contador = iter(range(1, 100))
    texto = re.sub(r"\{\}", lambda _: "{" + str(next(contador)) + "}", texto)
    return '"' + texto.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    conocidas = claves()
    faltan: dict = {}
    total = set()
    for texto, donde in candidatos():
        total.add(texto)
        if texto not in conocidas:
            faltan.setdefault(texto, []).append(donde)
    for texto, donde in faltan.items():
        if "--luau" in sys.argv:
            print(f"\t[{luau(texto)}] = {{ en = \"\", pt = \"\", fr = \"\" }},")
        else:
            print(f"{luau(texto)}  <- {', '.join(donde[:3])}")
    print(f"\n{len(faltan)} de {len(total)} textos sin traducir en {TEXTOS.relative_to(RAIZ).as_posix()}", file=sys.stderr)
    sys.exit(1 if faltan else 0)


if __name__ == "__main__":
    main()
