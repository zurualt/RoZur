# Trabajar en Overbooked! desde el PC

Todo el proyecto está en la rama `claude/beautiful-carson-qe8mn6` del repositorio `zurualt/RoZur`. Desde el PC se puede probar el juego en Roblox Studio y usar ElevenLabs, cosas que la nube no permite.

## 1. Instalar

| Programa | Para qué |
|---|---|
| Git | Bajar y subir el proyecto |
| Claude (app de escritorio) | Abrir una sesión de Claude Code en la carpeta del proyecto |
| Roblox Studio | Probar el juego |
| Rojo 7.x (programa + plugin de Studio) | Pasar el código y el mapa a Studio en vivo |
| Python 3.11 o más nuevo | Herramientas de `herramientas/` |
| Blender 4.x o 5.x | Regenerar modelos (`arte/*/..._gen.py`) |
| ffmpeg | Convertir sonidos a OGG |

## 2. Bajar el proyecto

```
git clone https://github.com/zurualt/RoZur.git
cd RoZur
git checkout claude/beautiful-carson-qe8mn6
```

## 3. Claves (nunca en el chat ni en el repositorio)

En Windows, crea estas variables de entorno de usuario (Configuración → Sistema → Información → Configuración avanzada → Variables de entorno):

| Variable | Qué es |
|---|---|
| `ROBLOX_API_KEY` | Clave de Open Cloud del grupo, con permisos de **Assets** (lectura y escritura), **Place publishing** (escritura) y **Luau Execution Sessions** (escritura) para la experiencia 10774639088 |
| `ELEVENLABS_API_KEY` | Clave de ElevenLabs, para sustituir los sonidos generados por código |

Los scripts `herramientas/subir_modelos.py`, `herramientas/subir_audio.py` y `herramientas/probar.py` leen `ROBLOX_API_KEY` si existe.

## 4. Probar en Studio

1. En la carpeta `Overbooked`, ejecuta `rojo serve default.project.json`.
2. Abre el lugar en Roblox Studio, pulsa **Connect** en el plugin de Rojo y luego **Play**.

## 5. Abrir Claude en el PC

En la app de escritorio de Claude, abre una sesión de Claude Code en la carpeta `RoZur` (o ejecuta `claude` en una terminal dentro de esa carpeta). Pídele que lea `Overbooked/README.md` y este archivo para seguir donde se quedó.
