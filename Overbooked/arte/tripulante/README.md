# Tripulante v5

Personaje jugable de la tripulación. Estilo blando y redondo (tipo PEAK): alto y delgado, cabeza de alubia sobre un cuello corto, uniforme de la aerolínea, guantes de dibujos animados y una cara muy tonta que se mueve al hablar por voz. Diseño propio.

![Cuatro tripulantes](renders/lineup.png)
![Vistas frontal, 3/4, lateral y trasera](renders/turnaround.png)
![Primera persona sin nada en las manos](renders/primera_reposo.png)
![Primera persona con algo en la mano derecha](renders/primera_agarre.png)
![Callado, hablando y gritando](renders/caras_voz.png)
![Sorpresa, susto, mareo y alegría](renders/caras_eventos.png)
![Enfado y hablando de lado](renders/caras_enfado.png)
![Prueba de brazos en posturas extremas](renders/brazos_prueba.png)
![Dedos de frente: abierta, relajada, agarrando una barra, puño y señalando](renders/manos_prueba.png)
![Las mismas posturas desde el lado de la palma](renders/manos_prueba_palma.png)

## Cambios de la v5

- Cuerpo nuevo con proporciones de persona larguirucha: 5,08 studs con los auriculares (antes 4,67), piernas largas (cadera a 2,18), brazos largos que llegan a medio muslo y hombros marcados.
- Cabeza de alubia separada del cuerpo, más ancha abajo (mofletes) que arriba, sobre un cuello corto. La cara de la v4 (boca, paletas, lengua, cejas, mofletes, nariz, auriculares con micro) está igual, recolocada en la cabeza nueva.
- Uniforme: camisa crema de manga corta con ribete turquesa, corbata turquesa, charreteras naranjas, alas doradas en el pecho, pantalón azul marino (`#2C3A5E`, casilla 12), cinturón marrón con hebilla dorada y zapatones marrones.
- Guantes blancos gordos de dibujos animados con puño acampanado: palma grande, cuatro dedos gruesos bien separados y pulgar. Hueso nuevo por mano: `DerAnular1/2` e `IzqAnular1/2`.
- El color del jugador se ve en la cabeza, el cuello y los brazos.

## Cambios de la v4

- Cara mucho más tonta: boca el doble de ancha que al abrirse baja y sale como una mandíbula, dos paletas de conejo (una torcida) y una lengua rosa que vive dentro de la cabeza y asoma al abrir.
- Huesos de cara con vértices para que Roblox no los borre: `Lengua` (hijo de `BocaInf`), `CejaIzq`, `CejaDer`, `MejillaIzq`, `MejillaDer` y `Nariz`. Las paletas van con `BocaSup`.
- Los ojos no están en la malla: son las piezas de `src/client/Ojos.luau` (borde, blanco y pupila con física) para que puedan parpadear, crecer y aplastarse. El de la derecha del personaje es un 12 % más grande y el otro un 8 % más pequeño. En los renders se ven con mallas que no se exportan (`Ojos_normal`, `Ojos_grande`, `Ojos_susto`, `Ojos_mareo`, `Ojos_feliz`, `Ojos_enfado`) con las mismas medidas y posición que las piezas del juego.

## Cara en el juego

`src/client/Cara.luau` mueve los huesos con `Bone.Transform` en cada `PreSimulation`, para todos los jugadores a menos de 120 studs (no lo hace con tu propia cabeza en primera persona). Los desplazamientos están en el espacio de la pieza `Head` y se pasan al del hueso con su rotación de reposo, así que no dependen de cómo orienta Roblox cada hueso. Son los mismos números que `cara()` de `tripulante_gen.py`:

| Hueso | Movimiento (studs, en la cabeza: X derecha, Y arriba, −Z delante) |
|---|---|
| `BocaSup` | sube 0,065 × apertura |
| `BocaInf` | baja 0,25 y sale 0,06 × apertura |
| `Lengua` | sale 0,07 × apertura + 0,14 × lengua fuera; gira de lado y se menea |
| `CejaIzq`/`CejaDer` | suben 0,06 × cejas; giran ±22° (enfado: extremo interior abajo) y se adelantan al bajar para no meterse detrás del ojo |
| `MejillaIzq`/`MejillaDer` | se inflan hacia fuera y delante |
| `Nariz` | se bambolea con la aceleración de la cabeza y olisquea |

Entradas: el nivel de voz de `BocaVoz.nivel(jugador)`, el atributo `Ragdoll` del personaje, la velocidad vertical del `HumanoidRootPart` y los atributos del avión `Turbulencia`, `CaidaLibre`, `Aterrizaje`, `Pajaros` y `Fase`. `Cara.mirada(personaje)` le da a `Ojos.luau` el tamaño, el aplastado (parpadeo), el tamaño de pupila, el temblor y el mareo de los ojos.

Los ojos se colocan con `CENTRO = (0.232, 1.143, -0.444)` y `NORMAL = (0.179, 0.08, -0.98)` en el marco de reposo del `HumanoidRootPart`. El generador los imprime al ejecutarse (`OJO CENTRO …`).

## Primera persona

El importador de Roblox pone el fondo del `HumanoidRootPart` a la altura de las caderas (`HipHeight` = 2,18), así que su centro en reposo queda a 3,18 sobre el suelo y la cámara de Roblox (raíz + 1,5) quedaría por encima de los ojos. `src/client/Camara.luau` pone `Humanoid.CameraOffset = (0, -0.36, 0)` para que la cámara vaya a la altura de los ojos (4,32). Sin nada en las manos, los brazos van a 64° en el hombro, 96° en el codo y 14° hacia fuera, y los guantes quedan en las esquinas de abajo (`primera_reposo.png`). Con algo en la mano, la derecha sube 22° más (`LEVANTE_PROPIO`). `PRIMERA` en el generador usa los mismos ángulos que `Camara.luau` y la cámara a la altura de los ojos con 80° de campo vertical, como en el juego.

## Dónde van los accesorios

Medidas en el espacio de la pieza `Head` (centro de su caja; `Head.Size` = 1,376 × 1,807 × 1,182):

- **Gorros:** encima, en `(0, Head.Size.Y / 2, 0)` = Y 0,90, la diadema de los auriculares (la calva acaba en Y 0,79). Por delante no deben bajar de Y ≈ 0,62: las cejas están en Y 0,50 y Z −0,29 y al gritar suben hasta Y ≈ 0,66.
- **Gafas:** los ojos están en X ±0,232, Y 0,15, Z −0,37, con el frente de la pupila en Z ≈ −0,55 y un radio de 0,24 (el ojo grande; 0,31 en sorpresa). Unas gafas tienen que ir por delante, en Z ≈ −0,64, con cristales de radio 0,26 o más.
- **Libre:** la boca (Y −0,18 a −0,59 abierta, Z −0,44 y la mandíbula sale hasta −0,50), la nariz (Y −0,10, sobresale hasta Z −0,60), los mofletes (X ±0,40, Y −0,19) y los cascos de los auriculares (X ±0,60, Y 0,04). Nada debería tapar de Y 0,45 hacia abajo por delante.
- **Espalda:** en el espacio de `UpperTorso` (`Size` = 1,2 × 0,807 × 0,75), la espalda de la camisa está en Z +0,375; una mochila va en `(0, -0.05, 0.375 + fondo / 2)`. Las charreteras están encima de los hombros, en X ±0,40, Y 0,31.

## Archivos

| Archivo | Para qué |
|---|---|
| `tripulante.blend` | Escena de Blender con el esqueleto, las 15 mallas y los ojos de los renders (ocultos, no se exportan). Ábrela para retocar. |
| `tripulante.fbx` | El que se importa en Roblox Studio. Lleva la textura dentro. |
| `tripulante_palette.png` | Textura de paleta de 64×64 (una casilla por color). |
| `tripulante_gen.py` | Script que genera todo desde cero (modelo, esqueleto, pesos, FBX y renders). |
| `renders/` | Imágenes de referencia. |

## Especificaciones

- **Altura:** 5,08 studs con los auriculares (`Config.ALTURA_TRIPULANTE`).
- **Esqueleto:** R15 con huesos, jerarquía oficial de Roblox: `Root → HumanoidRootNode → LowerTorso → …`. Root en el origen y LowerTorso en el mismo punto que HumanoidRootNode (2,30), como pide la especificación. Cintura a 2,70, cuello a 3,42, hombros en (±0,62, 3,17), codos en (±0,76, 2,62), muñecas en (±0,84, 2,00), caderas en (±0,27, 2,18), rodillas a 1,24 y tobillos a 0,34. Además, 8 huesos de cara y 20 en los dedos (45 huesos en total; en Roblox quedan 28 porque los del cuerpo se convierten en piezas).
- **Mallas:** 15 objetos con los nombres oficiales (`Head_Geo`, `UpperTorso_Geo`, …), todos con pesos. Como mucho 3 huesos por vértice (el límite es 4).
- **Pose:** brazos abajo (pose I).
- **Triángulos:** 9.162 en total, dentro de los límites oficiales de Roblox para cuerpos de avatar:

| Pieza | Triángulos | Límite |
|---|---|---|
| Cabeza | 3.782 | 4.000 |
| Torso | 1.436 | 1.750 |
| Cada brazo | 1.200 | 1.248 |
| Cada pierna | 772 | 1.248 |

## Dedos en el juego

`src/client/Manos.luau` gira los huesos de los dedos con `Bone.Transform` en cada `PreSimulation`, como la boca. Cada dedo se dobla sobre el eje perpendicular a su dirección y a la normal de la palma (calculado de los huesos, así que no depende del tamaño de la mano), y los dedos se abren en abanico: índice 1, medio 0,3, anular −0,3, meñique −1. Las posturas son 7 ángulos en grados (índice 1 y 2, medio, anular y meñique 1 y 2, pulgar 1 y 2, separación) y son los mismos números que `POSES_MANO` de `tripulante_gen.py`.

Roblox borra al importar los huesos que no tienen ningún vértice, así que el punto de agarre no es un hueso: está a `(-0.156, 0.061, 0.035)` de `DerMedio1` en el espacio de `RightHand` (el `AGARRE` del generador, donde está la barra dorada de los renders; el generador lo imprime como `AGARRE_MANO`).

## Color del jugador

La casilla "piel" de la paleta es transparente. En Roblox, lo transparente de la textura deja ver el `Color` de la MeshPart, así que el color de cada jugador se cambia poniendo el mismo `Color` a las 15 partes del cuerpo. Solo la cabeza, el cuello y los brazos son de piel; el resto (uniforme, guantes, auriculares, zapatos y cara) sale siempre igual.

En Blender, el color se cambia en el nodo `PlayerColor` del material.

| Casilla | Color |
|---|---|
| 0 | Transparente (color del jugador) |
| 1 | Negro cara `#1B1B21` |
| 2 | Naranja charreteras `#F27B2B` |
| 3 | Turquesa `#1FA6A0` |
| 4 | Gris auriculares `#34383F` |
| 5 | Dorado `#F0B73A` |
| 6 | Crema camisa `#FFF4E0` |
| 7 | Zapato y cinturón `#4A3428` |
| 8 | Suela `#EDE3CF` |
| 9 | Blanco guantes y dientes `#F7F7F2` |
| 10 | Interior boca `#2B1219` |
| 11 | Lengua `#E85A78` |
| 12 | Pantalón azul marino `#2C3A5E` |

## En Roblox

Subido con la API de assets al grupo del juego: modelo `79935936187714` (la v4 era `126872888876091`, la v3 `124975432706541` y la v2 `87418247604950`). Si alguna vez hay que importarlo a mano en Studio:

1. Abre el importador 3D y elige `tripulante.fbx`.
2. En **Rig Type** deja **R15 / Default**.
3. Si sale mirando hacia atrás, cambia **World Forward** en el importador. Si sale con un tamaño raro, revisa la unidad de escala: 1 unidad de Blender = 1 stud.
4. Para jugar con él, llama al modelo `StarterCharacter` y ponlo en `StarterPlayer`.

## Regenerar

```
blender -b -P tripulante_gen.py -- --render <carpeta absoluta>
```

Sin `--render` solo genera el `.blend`, el `.fbx` y la paleta, en unos segundos. Con `--render` también hace las imágenes (≈ 2 min en CPU), con `--manos` solo las dos de los dedos y con `--primera` solo las de primera persona. La carpeta de salida tiene que ir como ruta absoluta: con `.` Blender no encuentra dónde guardar la paleta.

## Pendiente de probar

Comprobado en Studio (solo lectura, con `InsertService:LoadAsset`): llegan los 28 huesos (8 de cara y 20 de dedos), `HipHeight` = 2,18 y los desplazamientos de `Cara.luau` mueven cada hueso en la dirección de los renders. Falta verlo en partida: la cámara a la altura de los ojos y los guantes en primera persona, la zancada de `Movimiento.luau` con las piernas largas, cómo se sienta en los asientos (muslos de 0,94) y la fuerza de los muelles de la cara con voz de verdad.
