# Aerolínea (nombre provisional)

Juego cooperativo de tripulación de avión caótica. El código va en Luau estricto, optimizado y sin comentarios. El arte (modelos, animaciones, efectos) se hace en Blender y los sonidos en ElevenLabs.

## Carpetas

| Carpeta | Qué hay | Dónde aparece en Studio |
|---|---|---|
| `src/client` | Scripts del jugador | `StarterPlayer.StarterPlayerScripts.Client` |
| `arte/tripulante` | Personaje jugable (Blender, FBX, renders) | Se importa a mano, ver su README |

Rojo se conecta igual que en Catch It: abre una terminal en la carpeta `Aerolinea`, ejecuta `rokit install` la primera vez y luego `rojo serve`. Los pasos completos están en el README de Catch It.

## Boca que se abre al hablar por voz

`src/client/BocaVoz.luau` abre la boca de cada tripulante según el volumen de su micrófono. Con la voz normal se abre un poco; si grita, se abre del todo. Cada jugador lo calcula en su propio PC, así que no gasta red.

**Cómo funciona:**
1. Roblox crea un `AudioDeviceInput` por cada jugador con voz.
2. Cada cliente lo conecta a un `AudioAnalyzer` y lee el volumen en cada fotograma.
3. El volumen se pasa a decibelios: de −46 dB (boca cerrada) a −12 dB (boca abierta del todo).
4. Se suaviza: abre rápido y cierra algo más despacio, para que no tiemble.
5. Mueve los huesos `BocaSup` y `BocaInf` del modelo.

Las bocas a más de 120 studs de la cámara no se calculan.

**Qué hay que activar en Studio:**
- **Voz:** actívala en Configuración del juego → Comunicación (micrófono). Solo funciona para jugadores con el chat de voz habilitado en su cuenta.
- **Servicio de voz:** `VoiceChatService.UseAudioApi = Enabled` y `EnableDefaultVoice = true`. Rojo ya los pone desde `default.project.json`; si no usas Rojo, cámbialos a mano en el Explorer.
- **Apariencia del avatar:** `StarterPlayer.LoadCharacterAppearance = false`, para que Roblox no meta sombreros ni ropa del avatar encima del tripulante. Rojo también lo pone.
- **Personaje:** el modelo importado tiene que estar en `StarterPlayer` con el nombre `StarterCharacter`.

**Números para ajustar jugando** (al principio de `BocaVoz.luau`):

| Valor | Qué hace | Ahora |
|---|---|---|
| `DB_MIN` | Volumen por debajo del cual la boca queda cerrada | −46 dB |
| `DB_MAX` | Volumen con el que la boca se abre del todo | −12 dB |
| `ATAQUE` / `CAIDA` | Rapidez al abrir / al cerrar | 30 / 12 |
| `ABRIR` | Cuánto baja el labio de abajo, en studs | 0,24 |
| `SUBIR` | Cuánto sube el labio de arriba, en studs | 0,05 |

**Pendiente de probar en Studio:** que Roblox conserve los huesos `BocaSup` y `BocaInf` al importar el FBX como R15, y los números de volumen con voces reales.
