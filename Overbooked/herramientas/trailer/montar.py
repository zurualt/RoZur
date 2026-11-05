import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
FUENTE = os.path.join(AQUI, "fuentes", "LuckiestGuy-Regular.ttf").replace("\\", "/").replace(":", "\\:")
W, H, FPS = 1080, 1920, 30


def esc(s):
    return s.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace(",", "\\,").replace("%", "\\%")


def main(ruta_plan):
    plan = json.load(open(ruta_plan, encoding="utf-8"))
    vx, vy, vw, vh = plan["vista"]
    entradas, filtros, etiquetas = [], [], []
    total = 0.0
    for i, t in enumerate(plan["tomas"]):
        entradas += ["-i", t["archivo"]]
        d = t["dura"]
        cw = vh * 9 / 16
        cx = max(0, min(vw - cw, t.get("centro", 0.5) * vw - cw / 2))
        z0, z1 = t.get("zoom", [1.0, 1.06])
        cadena = [
            f"[{i}:v]trim=start={t['desde']}:duration={d}",
            "setpts=PTS-STARTPTS",
            f"crop={vw}:{vh}:{vx}:{vy}",
            f"crop={int(cw)}:{vh}:{int(cx)}:0",
            f"scale={W}:{H}",
            f"scale=w='{W}*({z0}+({z1}-{z0})*t/{d})':h=-2:eval=frame",
            f"crop={W}:{H}:(iw-{W})/2:(ih-{H})/2",
            f"fps={FPS}",
            "setsar=1",
            "format=yuv420p",
        ]
        if t.get("flash"):
            cadena.append("fade=t=in:st=0:d=0.12:color=white")
        texto = t.get("texto")
        if texto:
            y = t.get("y", 0.16)
            tam = t.get("tam", 110)
            for k, linea in enumerate(texto.split("\n")):
                cadena.append(
                    f"drawtext=fontfile='{FUENTE}':text='{esc(linea)}':fontsize={tam}:fontcolor=0xFFF4E0:"
                    f"borderw=12:bordercolor=0x2A2420:x=(w-text_w)/2:y={H}*{y}+{k}*{int(tam * 1.1)}:"
                    f"alpha='min(1,t/0.12)'"
                )
        filtros.append(",".join(cadena) + f"[v{i}]")
        etiquetas.append(f"[v{i}]")
        total += d
    cartel = plan.get("cartel")
    if cartel:
        n = len(plan["tomas"])
        entradas += ["-loop", "1", "-t", str(cartel["dura"]), "-i", cartel["imagen"]]
        d = cartel["dura"]
        filtros.append(
            f"[{n}:v]scale={W}:{H},scale=w='{W}*(1+0.05*t/{d})':h=-2:eval=frame,crop={W}:{H}:(iw-{W})/2:(ih-{H})/2,"
            f"fps={FPS},setsar=1,format=yuv420p,fade=t=in:st=0:d=0.15:color=white[vc]"
        )
        etiquetas.append("[vc]")
        total += d
    filtros.append("".join(etiquetas) + f"concat=n={len(etiquetas)}:v=1:a=0[video]")
    base = len(entradas) // 2 if False else None
    sonidos = plan.get("musica", []) + plan.get("efectos", [])
    primera = sum(1 for a in entradas if a == "-i")
    mezcla = []
    for j, s in enumerate(sonidos):
        entradas += ["-i", s["archivo"]]
        idx = primera + j
        trozo = f"[{idx}:a]"
        cad = []
        if "desde" in s or "dura" in s:
            cad.append(f"atrim=start={s.get('desde', 0)}" + (f":duration={s['dura']}" if "dura" in s else ""))
            cad.append("asetpts=PTS-STARTPTS")
        cad.append("aresample=48000,aformat=channel_layouts=stereo")
        if s.get("entrada"):
            cad.append(f"afade=t=in:st=0:d={s['entrada']}")
        if s.get("salida") and "dura" in s:
            cad.append(f"afade=t=out:st={max(0, s['dura'] - s['salida'])}:d={s['salida']}")
        cad.append(f"volume={s.get('vol', 1.0)}")
        ms = int(s["en"] * 1000)
        cad.append(f"adelay={ms}|{ms}")
        filtros.append(trozo + ",".join(cad) + f"[a{j}]")
        mezcla.append(f"[a{j}]")
    if mezcla:
        filtros.append("".join(mezcla) + f"amix=inputs={len(mezcla)}:normalize=0:dropout_transition=0,"
                       f"atrim=duration={total},afade=t=out:st={max(0, total - 1.2)}:d=1.2,alimiter=limit=0.95[audio]")
    salida = plan["salida"]
    orden = ["ffmpeg", "-v", "error", "-y"] + entradas + ["-filter_complex", ";".join(filtros), "-map", "[video]"]
    if mezcla:
        orden += ["-map", "[audio]", "-c:a", "aac", "-b:a", "192k"]
    orden += ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p",
              "-movflags", "+faststart", "-t", f"{total:.3f}", salida]
    r = subprocess.run(orden)
    print("duracion", round(total, 2), "->", salida)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
