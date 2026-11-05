# Tripulante v6

Personaje jugable de la tripulación. Estilo blando, redondo y liso: cabeza grande casi esférica (algo aplastada y más llena abajo, como un bollo) sobre un cuerpo bajito y rechoncho, bracitos y piernas cortas. Va de piloto de la peor aerolínea del mundo: camisa blanca de manga corta, hombreras azul marino con dos galones dorados, corbata turquesa, alas doradas en el pecho y un boli naranja en el bolsillo, cinturón marrón con hebilla dorada, pantalón corto azul marino (uniforme de verano de aerolínea low cost), calcetines altos blancos con rayas turquesa y naranja, botas negras gordotas y manoplas blancas con puño turquesa. La cabeza, los brazos y las rodillas son del color del jugador. Diseño propio.

![Vistas frontal, 3/4, lateral y trasera](renders/turnaround.png)
![Primera persona sin nada en las manos](renders/primera_reposo.png)
![Primera persona con un vaso en la mano derecha](renders/primera_agarre.png)
![Cuatro tripulantes](renders/lineup.png)
![Callado, hablando y gritando](renders/caras_voz.png)
![Gritando mucho: lengua de perro al viento](renders/caras_grito.png)
![Sorpresa, susto, mareo y alegría](renders/caras_eventos.png)
![Enfado y hablando de lado](renders/caras_enfado.png)
![Prueba de brazos y piernas en posturas extremas](renders/brazos_prueba.png)
![Manoplas: abierta, relajada, agarrando una barra, puño, pulsando y palma](renders/manos_prueba.png)
![Las mismas posturas desde el lado de la palma](renders/manos_prueba_palma.png)

## Cambios de la v6

- Cuerpo nuevo, bajito y redondo: 3,93 studs (antes 5,08). Cabeza de 1,96 de ancho, 1,72 de alto y 1,82 de fondo, centrada en 3,03; cuerpo de 0,70 a 2,13 con barriga; piernas de 0,75 (cadera a 0,95) y brazos que llegan a la cadera. Se nota un poquito de cuello entre el cuello de la camisa y la cabeza.
- Todo liso: más segmentos (cabeza de 44 lados, manoplas de 28) y normales suaves, sin facetas en primera persona. Sin solapes: `auditar_solapes.py` no encuentra caras paralelas a menos de 0,04 studs (0 ALTA, 0 MEDIA, 0 BAJA).
- Manoplas con pulgar en vez de guantes de cinco dedos: 4 huesos por mano (`DerManopla1`, `DerManopla2`, `DerPulgar1`, `DerPulgar2` y lo mismo con `Izq`). Se fueron los 20 huesos de los dedos.
- Cara más pequeña y mona con las mismas piezas que se mueven: boquita con un diente, lengua, cejas, coloretes (casilla nueva `blush`) y nariz de botón.
- Lengua nueva: plana, más ancha en la punta y larga (0,5 studs, casi toda escondida dentro de la cabeza), pesada entera a `Lengua` sin estirarse. Su hueso nace en el labio de abajo, así que gira alrededor de la boca y puede salir 0,4 studs sin despegarse de dentro. Los ojos siguen siendo las piezas saltonas de `Ojos.luau`.
- Sin auriculares (la gorra de piloto es un accesorio de la tienda, `GorraPiloto`).
- Hombreras con galones sobre los hombros, pesadas a medias entre `UpperTorso` y el brazo para que sigan un poco al hombro.
- El uniforme no se monta en capas: el cuerpo es una sola pieza que cambia de color en el cinturón, y la pierna una sola que cambia de color en el calcetín (rayas incluidas). Lo que va encima (corbata, hombreras, alas, cinturón) sobresale 0,03 studs o más.

## Cara en el juego

`src/client/Cara.luau` mueve los huesos con `Bone.Transform` en cada `PreSimulation`, para todos los jugadores a menos de 120 studs (no lo hace con tu propia cabeza en primera persona). Los desplazamientos están en el espacio de la pieza `Head` y se pasan al del hueso con su rotación de reposo, así que no dependen de cómo orienta Roblox cada hueso. Son los mismos números que `cara()` de `tripulante_gen.py` (no han cambiado con la v6):

| Hueso | Movimiento (studs, en la cabeza: X derecha, Y arriba, −Z delante) |
|---|---|
| `BocaSup` | sube 0,065 × apertura (lleva el diente) |
| `BocaInf` | baja 0,25 y sale 0,06 × apertura |
| `Lengua` | gira alrededor del labio y luego sale hacia donde apunta (`CFrame.fromEulerAnglesYXZ(...) * CFrame.new(...)`): al hablar asoma (0,07 × apertura) y se menea poco; al gritar mucho sale 0,4, cae 0,45 rad y aletea de lado como un perro con la cabeza por la ventanilla |
| `CejaIzq`/`CejaDer` | suben 0,06 × cejas; giran ±22° (enfado: extremo interior abajo) y se adelantan al bajar |
| `MejillaIzq`/`MejillaDer` | los coloretes se inflan hacia fuera y delante |
| `Nariz` | se bambolea con la aceleración de la cabeza y olisquea |

**Grito con lengua al viento:** si el nivel de voz pasa de 0,75 durante más de 0,4 s, o con la expresión «Grito» (cayendo deprisa), un muelle (`flop`) lleva la lengua fuera: cae, aletea a ±0,8 rad, se retuerce, la boca se abre del todo, los mofletes se inflan, las cejas suben, los ojos crecen un 30 % con las pupilas pequeñas y tiemblan. Al acabar el grito la lengua vuelve con un muelle poco amortiguado, así que entra con un rebote. Solo son transformaciones de huesos, igual para todos a menos de 120 studs. En `cara()` del generador es el parámetro `flop` (con `fase` para el aleteo).

Los ojos se colocan con `CENTRO = (0.336, 1.059, -0.89)` y `NORMAL = (0.166, -0.028, -0.986)` en el marco de reposo del `HumanoidRootPart` (en `Ojos.luau` y, para la vista previa de la tienda, `OJO_CENTRO`/`OJO_NORMAL` en `Tienda.luau`). El generador los imprime al ejecutarse (`OJO CENTRO …`).

## Primera persona

El importador pone el centro del `HumanoidRootPart` 1 stud por encima de las caderas (1,95 sobre el suelo, `HipHeight` = 0,963) y la cámara de Roblox va a raíz + 1,5 y 0,5 por detrás (el zoom mínimo). `src/client/Camara.luau` pone `Humanoid.CameraOffset = (0, -0.44, 0)` para que vaya a la altura de los ojos (3,01). Sentado, el `SeatWeld` de Roblox pone la raíz 1,214 sobre el asiento (las caderas a 0,21, justo el radio del muslo), así que no hace falta bajar nada.

Con los brazos tan cortos las manos no llegan a verse desde los ojos, así que en tu propia vista (el torso no se ve) los hombros suben 0,35 studs (`ELEVAR`) y los brazos van a 58° en el hombro, 80° en el codo, 15° hacia fuera y la muñeca doblada 32° hacia arriba: las manoplas quedan en las esquinas de abajo con el pulgar encima (`primera_reposo.png`). Con algo en la mano, la derecha va a 58° + 22° (`LEVANTE_PROPIO`), codo 42°, 12° hacia dentro y muñeca 18° (`POSE_BRAZO`). Los demás jugadores te ven con los brazos normales. `PRIMERA` y `ELEVAR` del generador usan los mismos números que `Camara.luau`, con la cámara a la altura de los ojos, 0,5 por detrás y 80° de campo vertical, como en el juego.

## Manoplas en el juego

`src/client/Manos.luau` gira los huesos de las manoplas con `Bone.Transform` en cada `PreSimulation`. La manopla se dobla en dos sitios (nudillo y punta) hacia la palma y el pulgar se cierra hacia ella y se abre hacia delante. Las posturas son 5 ángulos en grados (manopla 1 y 2, pulgar 1 y 2, apertura del pulgar), los mismos que `POSES_MANO` de `tripulante_gen.py`. Si a un personaje le faltan huesos, esa parte de la mano no se mueve.

Roblox borra al importar los huesos que no tienen ningún vértice, así que el punto de agarre no es un hueso: está a `(-0.199, -0.123, 0)` de `DerManopla1` en el espacio de `RightHand` (el `AGARRE` del generador; lo imprime como `AGARRE_MANO`).

## Dónde van los accesorios

Medidas en el espacio de la pieza `Head` (centro de su caja; `Head.Size` = 1,96 × 2,17 × 1,919; en Blender el centro está en (0, −0,048, 2,845)):

- **Gorros:** la cabeza acaba arriba en Y 1,085. Por delante no deben bajar de Y ≈ 0,675: las cejas están en Y 0,50 y al gritar suben hasta Y ≈ 0,62. A la altura del borde de los gorros (Y 0,7) la cabeza mide unos 0,76 de radio a lo ancho y 0,74 a lo hondo.
- **Gafas:** los ojos están en X ±0,336, Y 0,164, Z −0,842, con el frente de la pupila en Z ≈ −1,03 y un radio de 0,24 (el ojo grande; 0,31 en sorpresa). Unas gafas van por delante, a 0,25 del centro del ojo (Z ≈ −1,09), con cristales de radio 0,27 o más.
- **Libre:** la boca (Y −0,17, se abre hasta −0,46, ancho ±0,14), la nariz (Y 0,015, sobresale hasta Z ≈ −0,98) y los coloretes (X ±0,56, Y −0,08). Los lados de la cabeza (X ±0,98) están libres para auriculares.
- **Espalda:** en el espacio de `UpperTorso` (`Size` = 1,258 × 0,896 × 0,961, centro en (0, −0,027, 1,757)), la espalda de la camisa está en Z ≈ +0,47; una mochila va en `(0, -0.06, 0.47 + fondo / 2)` y no debe pasar de Y +0,35 (ahí empieza la cabeza). Las hombreras están encima de los hombros, de X ±0,29 a ±0,59, Y ≈ +0,35.

## Archivos

| Archivo | Para qué |
|---|---|
| `tripulante.blend` | Escena de Blender con el esqueleto, las 15 mallas y los ojos de los renders (ocultos, no se exportan). Ábrela para retocar. |
| `tripulante.fbx` | El que se importa en Roblox Studio. Lleva la textura dentro. |
| `tripulante_palette.png` | Textura de paleta de 64×64 (una casilla por color). |
| `tripulante_gen.py` | Script que genera todo desde cero (modelo, esqueleto, pesos, FBX y renders). |
| `ids_subida.json` | Id del modelo subido. |
| `renders/` | Imágenes de referencia. |

## Especificaciones

- **Altura:** 3,93 studs (`Config.ALTURA_TRIPULANTE`). Bajito a propósito: la distancia de la cadera a los ojos (2,06) es casi la de la v5 (2,14), así que sentado en la cabina los ojos quedan por encima del cuadro de mandos y se ve por el parabrisas; de pie ves por encima de los mostradores bajos y los dispensadores de la cocina te quedan a la altura de la cara.
- **Esqueleto:** R15 con huesos, jerarquía oficial de Roblox: `Root → HumanoidRootNode → LowerTorso → …`. Root en el origen y LowerTorso en el mismo punto que HumanoidRootNode (1,05). Cintura a 1,32, cuello a 2,12, hombros en (±0,47, 1,92), codos en (±0,58, 1,56), muñecas en (±0,70, 1,26), caderas en (±0,25, 0,95), rodillas en (±0,26, 0,55) y tobillos en (±0,27, 0,20). Además, 8 huesos de cara y 8 de manoplas (33 en total; en Roblox quedan 16 porque los del cuerpo se convierten en piezas).
- **Mallas:** 15 objetos con los nombres oficiales (`Head_Geo`, `UpperTorso_Geo`, …), todos con pesos. Como mucho 3 huesos por vértice (el límite es 4).
- **Pose:** brazos un poco abiertos (17°) para no rozar la barriga.
- **Triángulos:** 24.304 en total (es un StarterCharacter propio, no un avatar UGC):

| Pieza | Triángulos |
|---|---|
| Cabeza | 5.136 |
| Torso de arriba / de abajo | 4.144 / 1.800 |
| Cada brazo (arriba, abajo, manopla) | 868 + 340 + 2.588 |
| Cada pierna (muslo, pierna, bota) | 844 + 460 + 1.512 |

## Color del jugador

La casilla "piel" de la paleta es transparente. En Roblox, lo transparente de la textura deja ver el `Color` de la MeshPart, así que el color de cada jugador se cambia poniendo el mismo `Color` a las 15 partes del cuerpo. Son de piel la cabeza, el cuello, la nariz, los brazos y las rodillas; el resto (uniforme, manoplas, calcetines, botas y cara) sale siempre igual.

En Blender, el color se cambia en el nodo `PlayerColor` del material.

| Casilla | Color |
|---|---|
| 0 | Transparente (color del jugador) |
| 1 | Negro cara `#1B1B21` |
| 2 | Naranja boli y raya del calcetín `#F27B2B` |
| 3 | Turquesa corbata, puños y rayas `#1FA6A0` |
| 4 | Suela `#4A3F3A` |
| 5 | Dorado galones, alas y hebilla `#F0B73A` |
| 6 | Camisa `#FFF4E0` |
| 7 | Cinturón `#5A3B2A` |
| 8 | Botas `#2E2A2C` |
| 9 | Blanco manoplas, diente y calcetines `#F7F7F2` |
| 10 | Interior boca `#2B1219` |
| 11 | Lengua `#E85A78` |
| 12 | Azul marino pantalón y hombreras `#2C3A5E` |
| 13 | Coloretes `#FF8F7E` |

## En Roblox

Subido con la API de assets al grupo del juego: modelo `93486408235562` (la v5 era `79935936187714`, la v4 `126872888876091`, la v3 `124975432706541` y la v2 `87418247604950`). Si alguna vez hay que importarlo a mano en Studio:

1. Abre el importador 3D y elige `tripulante.fbx`.
2. En **Rig Type** deja **R15 / Default**.
3. Si sale mirando hacia atrás, cambia **World Forward** en el importador. Si sale con un tamaño raro, revisa la unidad de escala: 1 unidad de Blender = 1 stud.
4. Para jugar con él, llama al modelo `StarterCharacter` y ponlo en `StarterPlayer`.


## Regenerar

```
blender -b -P tripulante_gen.py -- --render <carpeta absoluta>
```

Sin `--render` solo genera el `.blend`, el `.fbx` y la paleta, en unos segundos. Con `--render` también hace las imágenes (≈ 1,5 min en CPU), con `--manos` solo las dos de las manoplas y con `--primera` solo las de primera persona. La carpeta de salida tiene que ir como ruta absoluta: con `.` Blender no encuentra dónde guardar la paleta.

Si cambia el cuerpo, hay que actualizar a mano: `Config.ASSET_TRIPULANTE` y `Config.ALTURA_TRIPULANTE`, `CENTRO`/`NORMAL` en `Ojos.luau` y `OJO_CENTRO`/`OJO_NORMAL` en `Tienda.luau`, `ALTURA_OJOS` y la pose de primera persona en `Camara.luau`, `AGARRE_MANO` en `Manos.luau`, y `PIVOTES`, ojos y medidas de `arte/accesorios/accesorios_gen.py` (y volver a subir los accesorios).

## Probado en Studio

Cargado con `InsertService:LoadAsset`: llegan los 16 huesos (8 de cara y 8 de manoplas), 15 juntas y `HipHeight` = 0,963. Jugando: la cámara a la altura de los ojos y las manoplas en las esquinas en primera persona, la vista en tercera persona, los ojos saltones en su sitio, andar a saltitos, el ragdoll, sentarse en un banco, accesorios de cabeza, cara y espalda y la vista previa de la tienda. Falta verlo con 2 jugadores (cómo ven los demás lo que llevas en la mano) y la cara con voz de verdad.
