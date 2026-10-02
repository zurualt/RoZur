# Catch It

Pilla-pilla parkour 1v1. Rondas de 30 s: quien tenga el tag rojo al acabar el tiempo pierde la ronda. Gana el primero que llegue a 3.

## Carpetas

| Carpeta | Qué hay | Dónde aparece en Studio |
|---|---|---|
| `src/shared` | Código que usan servidor y cliente (reglas, configuración) | `ReplicatedStorage.Shared` |
| `src/server` | Scripts del servidor (rondas, tag, anti-trampas) | `ServerScriptService.Server` |
| `src/client` | Scripts del jugador (movimiento, cámara, efectos) | `StarterPlayer.StarterPlayerScripts.Client` |

Rojo solo sincroniza el código. Los mapas, los modelos y las animaciones que hagas en Studio se quedan en tu archivo `.rbxl`, así que guárdalo como siempre.

## Conectar Rojo (una sola vez)

1. **Instala Rokit**, el instalador de herramientas de Roblox:
   - Windows: `winget install Rojo.Rokit`, o descárgalo de <https://github.com/rojo-rbx/rokit/releases>.
2. **Descarga el repo** en tu PC (con GitHub Desktop o con `git clone https://github.com/zurualt/RoZur`).
3. **Instala Rojo** abriendo una terminal en la carpeta `CatchIt` y ejecutando:
   ```
   rokit install
   ```
4. **Instala el plugin de Rojo en Studio:**
   ```
   rojo plugin install
   ```
   También puedes instalarlo desde la Creator Store buscando "Rojo".

## Trabajar cada día

1. Abre una terminal en la carpeta `CatchIt` y arranca Rojo:
   ```
   rojo serve
   ```
2. En Studio, abre el lugar del juego, ve a **Plugins > Rojo** y pulsa **Connect**.
3. Cuando Claude suba scripts nuevos, descárgalos con `git pull` (o "Fetch/Pull" en GitHub Desktop). Rojo los mete en Studio al momento.
