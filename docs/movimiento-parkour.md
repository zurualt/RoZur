# Movimiento parkour para el 1v1 de pilla-pilla (inspirado en el juego de sdrame_ez, quizá "Pizza Hour")

## Resumen en 1 minuto

- **Lo que sabemos (poco y sin confirmar):** según resúmenes del buscador de páginas /discover de TikTok, SDRAME (@sdrame_ez) parece subir devlogs de un juego suyo de repartir pizzas. Por varias pistas, puede que se llame "Pizza Hour" (según un resumen de su perfil, enlaza a discord.gg/pizzahour). [Especulativo]
- **La única pista concreta** es la frase "swing from door to door", de la descripción de "Pizza Hour [BETA]" en una ficha de Medal.tv (copia de terceros, vista solo en un resumen del buscador). No está confirmado que ese juego sea suyo ni que "swing" sea una cuerda. [Especulativo]
- **Lo que no pudimos ver:** ningún vídeo, tampoco el que me mandaste. No sabemos sus movimientos exactos, sus controles ni sus efectos de cámara.
- **Movimientos que propongo:** correr siempre con barra de momentum, salto (con coyote time y buffer), deslizarse (slide, slide-jump y slide-hop), rodar al caer, saltar obstáculos (vault y Kong), subir bordes (mantle), correr por la pared, wall jump, escalar, gancho como movimiento estrella, dash y pillar por distancia.
- **Todos los números de diseño son míos [Propuesta]** (no los valores por defecto de Roblox ni los de las referencias), para probar y ajustar jugando. Ninguno viene de sdrame_ez.
- **Necesito 1:** capturas del vídeo que me mandaste, o que me cuentes qué se ve (tienes preguntas al final del apartado 1).
- **Necesito 2:** los IDs de las animaciones (`rbxassetid://...`) de la versión 1 (filas 1–23 del apartado 4.1).
- **Necesito 3:** un mapa de prueba en bloques grises con las medidas del apartado 2.6.

---

Fecha: 2 de octubre de 2026.

**El juego:** rondas de 30 s. El rojo pasa la marca al tocar al otro. Quien la tenga cuando se acaba el tiempo pierde la ronda. Gana el primero que llegue a 3.

**Quién hace qué:** tú haces las animaciones y los mapas en Blender. Yo escribo el código en Luau.

**Qué significa cada etiqueta**
- **[Confirmado]**: lo he leído en la documentación oficial o en el código fuente.
- **[Probable]**: solo lo he visto en resúmenes del buscador, porque la página original estaba bloqueada.
- **[Especulativo]**: es una deducción o un dato poco fiable.
- **[Propuesta]**: es un número o una idea de diseño mía para empezar a probar. **Ningún número de este documento viene de sdrame_ez.**
- **[hay que probarlo]**: no sabremos si funciona bien hasta probarlo en Studio.

---

## 1. Lo que sabemos del juego de sdrame_ez

**Aviso importante: no he podido ver ningún vídeo de sdrame_ez, tampoco el que me mandaste.** Desde aquí no se podía entrar en TikTok, Medal.tv, www.roblox.com, create.roblox.com ni la DevForum. Todo lo que pongo abajo viene de resúmenes del buscador sobre esas páginas.

**Sobre la documentación oficial de Roblox:** create.roblox.com estaba bloqueada, pero su contenido se puede leer en GitHub, en el repositorio Roblox/creator-docs, que es el código fuente de create.roblox.com/docs. Los datos marcados [Confirmado] con un enlace a create.roblox.com los he leído en esa copia de GitHub. Pongo el enlace de create.roblox.com porque es más cómodo de abrir.

### Lo que dicen las fuentes

1. **Quién es.** Según un resumen del buscador de la página discover "pizza-delivery-game-roblox", SDRAME (@sdrame_ez) es un desarrollador de Roblox que sube devlogs de un juego suyo de repartir pizzas. El mismo resumen describe uno de sus vídeos como "Dynamic Movement System Pizza Delivery": un juego de parkour y reparto centrado en moverse rápido, entregar pizzas y moverse con habilidad. Parece un resumen automático de TikTok, no el título del juego. Las páginas /discover las genera TikTok de forma automática y mezclan vídeos de muchos creadores, así que todo lo que sale solo de ellas lo marco como especulativo. [Especulativo] https://www.tiktok.com/discover/pizza-delivery-game-roblox
2. **Una página automática de TikTok.** Ese mismo vídeo aparece en la página /discover "Best Movement Games in Roblox". Las páginas /discover las genera TikTok de forma automática para los buscadores. No significa que nadie lo haya "clasificado" como juego de movimiento. [Especulativo] https://www.tiktok.com/discover/best-movement-games-in-roblox
3. **Puede que el juego se llame "Pizza Hour".** [Especulativo] Hay tres pistas:
   - Un resumen del buscador (de la página discover "roblox-headquarters-food", fuente débil) menciona un vídeo titulado "Delivery Throw in Pizza Hour" y dice que en él enseña cómo hizo el lanzamiento de pizza. [Especulativo] https://www.tiktok.com/discover/roblox-headquarters-food?lang=en
   - Un resumen de la página discover "pizza-time-game-on-roblox" menciona vídeos "Pizza Hour Q&A" atribuidos a él sobre su sistema de movimiento. Las respuestas no aparecían en ningún resumen. [Especulativo] https://www.tiktok.com/discover/pizza-time-game-on-roblox
   - Según un resumen de su perfil, enlaza a discord.gg/pizzahour. [Probable] https://www.tiktok.com/@sdrame_ez
4. **Una ficha de "Pizza Hour" en Medal.tv.** Medal.tv es una web de terceros que copia la información de los juegos de Roblox. No es la página oficial, y además solo la vi en un resumen del buscador.
   - La ficha es de una experiencia llamada "Pizza Hour [BETA]" (con emoji de pizza). Su descripción dice: *"the most chaotic pizza delivery you'll ever do! Swing from door to door delivering pizzas one by one for money. On your way you'll deal with multi-scale bosses, police chases, angry customers..."* La beta es de pago y la versión final será gratis. [Probable] https://medal.tv/games/roblox/experiences/1bdfrToozyZsui/pizza-hour-beta
   - Hay otra ficha llamada "Pizza Hour" sin [BETA]. Puede que sea la versión pública. [Probable] https://medal.tv/games/roblox/experiences/1bb6IDyiFpB1OK/pizza-hour
5. **Que ese juego sea suyo es una deducción.** Coincide el nombre, y un resumen del buscador menciona un vídeo suyo sobre si la policía es enemiga en Pizza Hour, que encajaría con las "police chases". Ese resumen parece salir de la página discover "pizza-time-game-on-roblox" (https://www.tiktok.com/discover/pizza-time-game-on-roblox), pero no lo puedo asegurar. Ninguna fuente dice directamente que el juego sea suyo. [Especulativo]
6. **El único movimiento que aparece escrito es "swing from door to door"**, en la ficha de Medal.tv (copia de terceros). Podría ser una cuerda o un gancho al estilo Spider-Man, pero hay tres dudas encadenadas:
   - La ficha es una copia de terceros que solo vi en un resumen del buscador.
   - No está confirmado que Pizza Hour sea de sdrame_ez.
   - "Swing from door to door" puede ser una forma de hablar ("ir de puerta en puerta"), no una cuerda.
   - El resto de lo que se dice de su movimiento es genérico: "parkour", "fast movement" y "skillful navigation".
   - [Especulativo] (la misma URL de Medal)
7. **Otros vídeos que los resúmenes del buscador le atribuyen:**
   - Un resumen menciona un vídeo sobre un menú principal "dinámico e inmersivo". [Especulativo] https://www.tiktok.com/discover/pizza-edition-games
   - Un resumen menciona vídeos sobre armas tipo karambit y bumerán. [Especulativo] https://www.tiktok.com/discover/pizza-delivery-game-roblox
   - Un resumen dice que el lanzamiento de pizza está inspirado en Mario Odyssey. [Especulativo] https://www.tiktok.com/@sdrame_ez
   - Un resumen dice que su estilo de interfaz inspira a otros desarrolladores. Sale de la página de un juego de terror que no tiene nada que ver. [Especulativo] https://www.tiktok.com/discover/devlog-horror-game-toy-factory
8. **Seguidores y likes:** las cifras no cuadran entre fuentes. Unas dicen 113.4K seguidores, otras 1.5M y otras 4.3M. El vídeo de movimiento aparece con 82.5K o con 216.4K likes. No te fíes de ninguna. [Especulativo]

### Juegos parecidos que NO son suyos (para no liarnos)
- "Pizza Delivery [2 Player Obby]" (place 70657911612614) es de DuoPlay Studios. El dato sale de una copia de la página de Roblox (roblox-jp). [Probable] https://game.roblox-jp.com/en/games/70657911612614
- "TAKEOUT", con un modo "Pizza Surfing" que tiene dash y voltereta, es otro juego distinto. [Especulativo] https://www.tiktok.com/discover/parkour-games-roblox

### Lo que NO se pudo comprobar
- **Los vídeos.** No pude ver ninguno. Tampoco el que me mandaste por el chat: https://www.tiktok.com/@sdrame_ez/video/7671501462718942486. Ni siquiera aparece en el buscador.
- **Los movimientos exactos:** si se desliza, si corre por paredes, si salta obstáculos, si tiene dash. Tampoco sus controles ni sus efectos de cámara (cambio de FOV, temblor, líneas de velocidad).
- Si el vídeo que me mandaste enseña un balanceo con cuerda o no.
- Si Pizza Hour es de verdad su juego.
- **Cómo lo hizo:** si usa Blender o Moon Animator, qué scripts tiene, cuál es el ID del juego en Roblox y qué grupo lo publica.
- Lo que contesta en sus Q&A sobre el movimiento.

### Qué significa esto para tu juego
- **No hay nada seguro sobre su movimiento.** Lo más parecido a una pista es el "swing" de la ficha de Medal.tv, y eso es [Especulativo].
- **El gancho es una [Propuesta] de diseño mía.** Lo pongo como movimiento estrella porque encaja con esa pista y porque da mucho juego en un pilla-pilla. No porque sepamos que su juego lo tiene.
- **El resto (deslizarse, correr por paredes, saltar obstáculos, rodar al caer, dash) es el kit de parkour típico de los juegos de este estilo en Roblox:** Parkour Reborn, untitled tag game (UTG) y RIVALS. Los números de referencia salen de esos juegos y de Titanfall 2, Mirror's Edge y Celeste.
- Está **inspirado** en lo poco que se sabe de su juego. No es una copia, ni intenta parecerse a algo que no hemos visto.

### Ayúdame a afinarlo
Dijiste "con fotos". Mándame capturas del vídeo que me pasaste (o de otros suyos) y dime qué ves. Por ejemplo:
- ¿Usa una cuerda de verdad? ¿Sale de la mano o de un objeto?
- ¿Se engancha a cualquier sitio o a puntos marcados?
- ¿Se desliza por el suelo?
- ¿Corre por las paredes?
- ¿Hace volteretas al soltarse?

Con eso ajusto lo que haga falta.

---

## 2. Cómo se mueve el personaje (spec de movimiento)

**Unidades:** studs y segundos. 1 stud = 28 cm [Confirmado] (https://github.com/Roblox/creator-docs/blob/main/content/en-us/physics/units.md).

**Valores por defecto de Roblox, para comparar** [Confirmado]:
- **Velocidad al andar** (`Humanoid.WalkSpeed`): 16 (https://github.com/Roblox/creator-docs/blob/main/content/en-us/reference/engine/classes/Humanoid.yaml).
- **Salto:** por defecto Roblox usa la potencia de salto (`StarterPlayer.CharacterUseJumpPower` = true) con JumpPower 50. Eso da unos 6.37 studs de altura. El valor JumpHeight = 7.2 solo se usa si `UseJumpPower` = false (misma URL de Humanoid.yaml).
  - **Ojo:** eso es el valor por defecto de la referencia, no lo que usa tu place. Se dice que las plantillas nuevas de Studio suelen traer `CharacterUseJumpPower` = false (JumpHeight 7.2), pero no lo he comprobado [Especulativo]. Mira StarterPlayer en tu place. [hay que probarlo]
- **Gravedad** (`Workspace.Gravity`): 196.2 studs/s² (https://github.com/Roblox/creator-docs/blob/main/content/en-us/reference/engine/classes/Workspace.yaml).
- **Campo de visión** (`Camera.FieldOfView`): 70. Es el ángulo **vertical**, y va de 1 a 120 (https://create.roblox.com/docs/reference/engine/classes/Camera).

**Todos los números de diseño de esta sección (no los valores por defecto de Roblox ni las referencias) son [Propuesta]:** son puntos de partida y los ajustaremos jugando. Los pondré todos juntos en un ModuleScript llamado `MovementConfig`, para que se puedan cambiar sin tocar el código.

### 2.0 Reglas que valen para todo

- **Siempre corres.** No hay botón de sprint, que es más cómodo en móvil y con mando.
  - Velocidad base: 20 studs/s.
  - **Stick analógico:** en mando y móvil, `MovingDirection` va de 0 a 1 según lo que inclines el stick. Si no se corrige, inclinarlo a medias te haría ir a menos de 20. Por eso, en cuanto pasas la zona muerta, la dirección se normaliza y vas a velocidad completa.
  - **Ventaja del que pilla (el rojo):** un 5% más sobre su velocidad total (base + momentum + sobrante). Es decir, 21 en vez de 20, y unos 35.7 en vez de 34. Una ventaja fija de +1 (21 contra 20) no se notaría al lado del momentum (0–14) ni del slide-hop (32–36). Otra opción es darle la ventaja en el momentum: que lo gane más rápido y lo pierda más despacio. [hay que probarlo]
- **Momentum (M): una barra de 0 a 14 que se suma a tu velocidad cuando corres por el suelo.** Con la barra llena corres a 34 studs/s.
  - **Se llena** encadenando movimientos. Esto es lo que da cada uno:
    - +4: soltarse del gancho con un buen lanzamiento (+2 si te sueltas en otro momento).
    - +3: Kong, rodada perfecta y wall jump.
    - +2: vault, y slide-jump en los primeros 0.35 s del deslizamiento.
    - 0: todo lo demás (salto normal, deslizarse sin saltar, rodada temprana, mantle, mantle jump, wallrun, wall kick, escalar, salto hacia atrás de la escalada y dash). [hay que probarlo]
  - **Se vacía poco a poco:** baja 1.5 por segundo mientras estás en el suelo. En el aire, en la pared o colgado del gancho no baja.
  - **Se vacía de golpe:**
    - Si vas a menos de 4 studs/s durante más de 0.25 s seguidos. Ese margen evita perderlo por soltar el stick un instante, pasar por la zona muerta o rozar una pared (con DecelerationTime 0.12 frenas casi al momento).
    - Si haces un aterrizaje duro.
  - **Se queda a la mitad** si giras bruscamente en el suelo: más de 110° en 0.2 s o menos. En el aire no cuenta.
  - Idea: mostrarla en pantalla como una porción de pizza que se va llenando.
  - Está basada en Parkour Reborn (el momentum sube encadenando y se pierde en giros bruscos) [Probable] https://parkour-reborn.fandom.com/wiki/Movement y en UTG (el momentum se suma a tu velocidad, baja 2 por segundo y vuelve a 0 si te paras) [Probable] https://utg.miraheze.org/wiki/Tech
- **Velocidad sobrante.** Si aterrizas más rápido que tu máximo (por ejemplo, después de soltarte del gancho), no la pierdes de golpe: baja 18 studs/s cada segundo. Deslizarte en llano no la conserva mejor: el slide entra como mucho a 48 y en llano pierde 22 studs/s cada segundo, más que corriendo. Solo ayuda cuesta abajo, donde el slide gana velocidad (ver "Deslizarse").
- **En el aire conservas el impulso.**
  - **Ojo con el AirController de Roblox:** `MaintainLinearMomentum = true` solo conserva el impulso cuando no tocas nada. Si empujas, el AirController lleva tu velocidad (también su dirección) hacia `MovingDirection × BaseMoveSpeed`, con toda la fuerza que le deje `MoveMaxForce`. O sea, al dirigir en el aire te quitaría velocidad [Confirmado] (https://create.roblox.com/docs/reference/engine/classes/AirController).
  - **Solución:** ponemos `MoveMaxForce = 0` y el control en el aire lo hace nuestro código, al estilo de Quake: solo te acelera hacia donde empujas si tu velocidad en esa dirección (`dot(v, dirección)`) es menor que tu máximo. Está explicado en el apartado 3.2.
  - El control en el aire es suave: puedes acelerar 30 studs/s cada segundo hacia donde empujas.
  - Así nunca te frena si vas más rápido que tu máximo.
  - El Humanoid normal de Roblox sí frena el impulso en el aire, y por eso no lo usamos [Probable] (https://devforum.roblox.com/t/questions-on-a-momentum-system/3896512).
- **Buffer en todos los botones:** salto, dash, deslizar, wall jump y gancho. Si pulsas un poco antes de que el movimiento se pueda hacer, la pulsación se guarda 0.12 s y sale en cuanto se puede. (Excepción: Deslizar pulsado en el aire se guarda 0.25 s. Al aterrizar te deslizas o, si caes rápido, ruedas. Ver "Deslizarse" y "Rodar al aterrizar".)
- **Límite absoluto:** 80 studs/s en horizontal, hagas lo que hagas.

### 2.1 Controles

| Acción | PC | Mando (Xbox / PlayStation) | Móvil |
|---|---|---|---|
| Moverse | WASD | Stick izquierdo | Joystick |
| Saltar, wall jump, Kong, cancelar | Espacio | A / Cruz | Botón Saltar |
| Deslizarse, o rodar al caer | C o Ctrl izquierdo | B / Círculo | Botón "Deslizar" |
| Dash | Q | X / Cuadrado | Botón "Dash" |
| Gancho | E o clic izquierdo (mantener) | RT / R2 (mantener) | Botón "Gancho" (mantener, o tocar: ver abajo) |
| Correr por la pared, saltar obstáculos, subir bordes, escalar, pillar | Automático | Automático | Automático |

- **Los botones se programan con el Input Action System** (ver 3.3). Permite poner controles distintos para cada dispositivo y botones táctiles propios.
- Los botones del mando son [Propuesta]. Hay que comprobar en Studio que no chocan con nada.
- Los movimientos automáticos ayudan mucho en móvil y con mando.

**PC**
- **El ratón va bloqueado en el centro por defecto:** con shift-lock, o con una cámara propia que use `MouseBehavior.LockCenter`. Con la cámara normal de Roblox solo giras manteniendo el clic derecho, y el gancho apunta al centro de la pantalla, así que sin bloquear el ratón no se podría apuntar bien.
- **El gancho va en el clic izquierdo, no en el derecho:** el clic derecho se deja libre para quien quite el shift-lock, porque en la cámara normal de Roblox se usa para girar la cámara.

**Móvil**
- **Botones táctiles propios** (ImageButtons), grandes, y colocados para poder pulsar Saltar + Deslizar con un solo pulgar (para el slide-hop). Los botones automáticos de ContextActionService se amontonan alrededor del de saltar, por eso no los usamos.
- **Gancho, opción "Tocar para engancharse":** mantener el botón ocupa el pulgar derecho, que es el que mueve la cámara, y no podrías dirigir durante el balanceo. Con esta opción tocas una vez para engancharte y otra vez (o Saltar) para soltarte.
- **Apuntado automático:** el gancho elige solo el punto de enganche más cercano al centro de la pantalla, dentro de un cono de 40° de medio ángulo (40° hacia cualquier lado del centro).
- **Ventanas de tiempo más amplias:** la rodada perfecta (0.12 s) y el coyote time (0.10 s) son más difíciles en táctil. Propuesta: ampliarlas en táctil (por ejemplo, a 0.2 s) o que la rodada salga sola. Hay que decidir si eso es justo en partidas entre móvil y PC. [hay que probarlo]
- **Pantalla siempre en horizontal:** `StarterGui.ScreenOrientation = LandscapeSensor`.
- **Rendimiento:** el desenfoque (BlurEffect), las partículas de velocidad y el resaltado (Highlight) pesan en móviles flojos. Van atados a la opción "Reducir efectos" y a la calidad gráfica (ver 2.5).

**Mando**
- **Gancho:** cono de 40° de medio ángulo con ayuda al apuntar, igual que en móvil (en vez de 30°).
- **Gatillo RT / R2:** cuenta como pulsado a partir de un umbral (`PressedThreshold` del Input Action System).
- **Iconos correctos:** se muestra el botón de Xbox o el de PlayStation según el mando conectado, con `InputActionLabel` o `UserInputService:GetImageForKeyCode`.
- **Vibración** (`HapticEffect`): en la rodada perfecta, al pillar y en el aterrizaje duro.

**Consola**
- Todos los menús se tienen que poder usar con el mando, y sin textos que solo valgan para teclado (nada de "pulsa E").

### 2.2 Los movimientos

#### Salto
- **Botón:** Espacio / A / botón Saltar.
- **Cuándo funciona:**
  - Estando en el suelo.
  - Hasta 0.10 s después de haberte caído de un borde. Se llama "coyote time" y perdona saltar un pelín tarde. (En táctil puede ser más largo: ver 2.1.)
  - Si pulsas hasta 0.12 s antes de tocar el suelo, el salto se guarda y sale justo al aterrizar ("buffer").
- **Qué hace:**
  - Te lanza hacia arriba a 54 studs/s, lo que da unos 7.4 studs de altura (el salto normal de Roblox da unos 6.37–7.2, según el ajuste de StarterPlayer: ver arriba).
  - Conservas toda tu velocidad hacia delante.
  - Si sueltas el botón mientras subes, la subida se corta a la mitad. Así puedes hacer saltitos cortos.
- **Por dentro:** en el mismo frame del impulso se cambia al AirController, y durante unos 0.1 s se ignora el sensor de suelo. Si no, el GroundController te vuelve a pegar al suelo y los saltos se notan "pegajosos" en cuestas y escalones.
- **Corrección de esquina:** si al subir la cabeza roza por poco el borde de un techo o una plataforma, el código te empuja 0.5–1 stud hacia un lado para que pases.
- **Salto encadenado:** si vuelves a saltar en los 0.10 s después de aterrizar, no pierdes nada de velocidad.
- **Cámara:** al aterrizar baja 0.3 studs y vuelve.
- **Referencias:**
  - Celeste usa 0.1 s de coyote time [Confirmado] https://github.com/NoelFB/Celeste/blob/master/Source/Player/Player.cs
  - En Roblox se suele usar entre 0.05 y 0.2 s de coyote time y entre 0.05 y 0.3 s de buffer [Probable] https://devforum.roblox.com/t/coyote-time-and-jump-buffer-for-platformer-games/2809273

#### Deslizarse (slide), slide-jump y slide-hop
- **Botón:** C / B / botón Deslizar.
  - Si lo pulsas en el aire hasta 0.25 s antes de aterrizar, te deslizas nada más tocar el suelo. Si caes desde muy alto, en vez de eso ruedas (ver el siguiente movimiento).
- **Cuándo funciona:** en el suelo, yendo a 14 studs/s o más, y si han pasado 0.5 s desde el último deslizamiento.
- **Con qué velocidad entras:**
  - Se toma tu velocidad más alta de los últimos 0.2 s y se multiplica por 1.15.
  - Ese extra no te puede subir de 36.
  - Mínimo 24, máximo 48.
  - Si ya ibas a 45 porque venías del gancho, entras a 45.
- **Cómo cambia la velocidad mientras te deslizas:**
  - En llano pierdes 22 studs/s cada segundo.
  - Cuesta abajo ganas 196.2 × sen(ángulo de la cuesta) × 0.6 cada segundo (196.2 es la gravedad del Workspace).
  - Cuesta arriba pierdes 196.2 × sen(ángulo de la cuesta) cada segundo.
- **Cuándo se acaba:** cuando bajas de 14 studs/s, o a los 1.2 s si estás en llano. En una bajada sigue mientras mantengas el botón. Al acabar te levantas corriendo.
- **Pasar por huecos bajos:** te agachas y cabes por huecos de 3.5 studs de alto como mínimo. Para los mapas, recomendado 3.5–4.5, siempre por debajo de la altura de pie para que haya que deslizarse (ver 2.6) [hay que probarlo].
- **Por dentro:** el slide usa el GroundController, no el AirController: `BaseMoveSpeed` = velocidad del slide, `GroundOffset` más bajo (vas agachado) y poca fricción. Ver 3.2.
- **Slide-jump:** si saltas mientras te deslizas, el deslizamiento se corta y conservas el 100% de tu velocidad hacia delante. Si saltas en los primeros 0.35 s, ganas +2 de momentum. A 36 studs/s saltas unos 20 studs de largo.
- **Slide-hop:** desliza → salta → desliza al aterrizar → salta, y así seguido.
  - El deslizamiento vuelve a estar listo justo cuando aterrizas: su espera es de 0.5 s y un salto dura unos 0.55 s en el aire.
  - Con esta técnica mantienes unos 32–36 studs/s: tan rápido como correr con el momentum lleno (34), pero sin necesitar momentum. Es la técnica "de pro", como en RIVALS.
  - El tope de 36 en el extra hace que no se pueda ganar velocidad infinita.
- **Cámara y efectos:**
  - La cámara baja 1.3 studs.
  - FOV +6 (sin pasar del tope de 95, ver 2.5).
  - La cámara se inclina 3° hacia donde giras.
  - Polvo o chispas en los pies y sonido de arrastre.
- **Referencias:**
  - Slide-jump en RIVALS [Probable] https://robloxrivals.fandom.com/wiki/Mechanics/Techs
  - Un sistema estilo Rivals que empieza a 42 studs/s y baja en 0.75 s [Confirmado] https://github.com/themvf/Roblox_Benji/pull/5
  - El ×1.15 y los límites vienen de un proyecto amateur [Confirmado] https://github.com/tfmvn/roblox-studio/blob/7ade1166a2ae6b083b634e66b8e4b93ceaf0ce5a/combat-system/src/ReplicatedStorage/Shared/MovementSettings.lua
  - Usar la velocidad más alta de los últimos 0.2 s [Probable] https://devforum.roblox.com/t/building-a-parkour-system-cuz-im-boreddevlog/4073003
  - Deslizarse más rápido en cuestas [Probable] https://devforum.roblox.com/t/how-could-i-make-a-slide-mechanic-that-picks-up-speed-on-slopes/2452696

#### Rodar al aterrizar, y aterrizajes medio y duro
- **Botón:** el de Deslizar, pulsado hasta 0.25 s antes de tocar el suelo.
- **Cuándo funciona:** cuando caes a 70 studs/s o más, que es más o menos una caída desde 12.5 studs de altura.
- **Si lo haces bien:**
  - **Rodada perfecta** (pulsas en los últimos 0.12 s antes de tocar el suelo): conservas el 100% de tu velocidad y ganas +3 de momentum. El mando vibra. (En táctil, la ventana puede ser más amplia o la rodada puede salir sola: ver 2.1.)
  - **Rodada temprana** (entre 0.12 y 0.25 s antes): conservas el 85% de tu velocidad.
  - La rodada dura 0.4 s. Si saltas durante la rodada, la cortas al instante sin perder velocidad ("roll cancel").
- **Si no ruedas:**
  - Cayendo a menos de 95 studs/s (una caída de menos de unos 23 studs): **aterrizaje normal**, sin castigo.
  - Cayendo entre 95 y 125 studs/s (una caída de unos 23 a 40 studs): **aterrizaje medio**. Te quedas parado 0.15 s y tu velocidad se multiplica por 0.8.
  - Cayendo a 125 studs/s o más (una caída de unos 40 studs o más): **aterrizaje duro**. Te quedas casi quieto 0.35 s, tu velocidad se multiplica por 0.4 y el momentum vuelve a 0.
- **Por qué estos umbrales:** si te sueltas a la altura de un punto de enganche (20–35 studs) sin velocidad hacia arriba, caes a unos 89–117 studs/s. Incluso un wall jump desde 8 studs (que sube hasta unos 14) cae a más de 70. Con umbrales más bajos, casi cada suelta del gancho acabaría en aterrizaje medio o duro si no ruedas.
  - **Ojo: soltándote del gancho se puede caer más rápido.** La velocidad al tocar el suelo es √(vy² + 2 × 196.2 × altura), donde vy es la velocidad hacia arriba al soltarte (ya con el bonus del buen lanzamiento) y la altura es desde donde te sueltas. Ejemplos con un punto a 35 studs y una cuerda de 10:
    - A 70 studs/s en el punto más bajo y buen lanzamiento a 60°: caes a unos 125 studs/s.
    - A 80 studs/s en el punto más bajo y buen lanzamiento a la altura del punto: subes hasta unos 46 studs y caes a unos 134 studs/s.
    - O sea, desde puntos altos y con cuerda corta **puedes tener un aterrizaje duro si no ruedas**. Si eso molesta al probarlo, se pueden bajar los puntos de enganche, reducir el bonus del lanzamiento o usar la opción de abajo. [hay que probarlo]
  - Otra opción [hay que probarlo]: medir la altura de caída sin contar lo que subiste con los lanzamientos hacia arriba (wall jump, soltarse del gancho).
- **Si la caída es pequeña** (menos de 70 studs/s) y tienes Deslizar pulsado, entras directamente en un deslizamiento.
- **Cámara y efectos:**
  - Rodada: la cámara baja 0.8 studs y vuelve suave. **La cámara NO da la vuelta con la voltereta**, porque marea.
  - Aterrizaje duro: temblor de 0.25 s, FOV −4, un golpe fuerte de sonido y vibración en el mando.
- **Referencias:**
  - En UTG, rodar justo antes de aterrizar da velocidad [Probable] https://utg.miraheze.org/wiki/Tech
  - La rodada de Mirror's Edge [Probable] https://strategywiki.org/wiki/Mirror's_Edge/Controls
  - El roll cancel de Parkour Reborn [Probable] https://parkour-reborn.fandom.com/wiki/Movement/Community_Techniques

#### Saltar obstáculos bajos (vault) y Kong
- **Botón:** ninguno, es automático. Para hacer un Kong, pulsa Espacio durante el vault (ver "Kong" abajo).
- **Cuándo funciona:**
  - Vas hacia delante a 12 studs/s o más.
  - La parte de arriba del obstáculo está a 1.5 studs o más por encima de tus pies, y a menos de 3.8. (A partir de 3.8 ya es un borde para subir: ver "Subir bordes".)
  - El obstáculo mide 5 studs de grosor como mucho, o sea, hay sitio detrás.
- **Cómo lo detecta el código:**
  1. Lanza 3 rayos hacia delante: a la altura de la rodilla, de la cintura y de la cabeza.
     - **Largo de los rayos:** max(3.5, velocidad × 0.12). Con un largo fijo de 3.5, a 80 studs/s solo verías 0.04 s por delante. A 80 studs/s miden 9.6.
     - **El rayo de la rodilla va por debajo de 1.5 studs sobre los pies.** Si no, no vería los obstáculos más bajos.
     - Los rayos no ven a ninguno de los dos personajes (ver 3.2).
  2. Si los de rodilla o cintura chocan y el de la cabeza no, hay un obstáculo bajo.
  3. Lanza otro rayo hacia abajo desde encima del obstáculo para medir su altura exacta.
- **Qué hace:**
  - Te da el impulso hacia arriba justo para pasar por encima: √(2 × 196.2 × (altura + 0.8)). Por ejemplo, para un obstáculo de 3 studs son 38.6 studs/s.
  - Conservas tu velocidad hacia delante, con un mínimo de 22.
  - Ganas +2 de momentum.
  - No teletransporta al personaje: todo es física normal, así el servidor no lo ve raro.
- **Kong:**
  - **Cómo se distingue de un salto:** si pulsas Espacio mientras haces el vault (hasta 0.2 s después de que empiece), el vault se convierte en Kong y el código añade el impulso extra en ese momento. Si pulsas Espacio antes de llegar al obstáculo, haces un salto normal, no un Kong. Así una pulsación nunca cuenta como salto y como Kong a la vez.
  - Te da 12 studs/s extra hacia arriba.
  - Tu velocidad hacia delante se multiplica por 1.15, ganando como mucho 8.
  - Ganas +3 de momentum en vez de +2.
- **Espera:** 0.3 s entre un salto de obstáculo y el siguiente.
- **Cámara y efectos:** un pequeño bote de la cámara, FOV +3 y sonido de las manos apoyándose.
- **Referencias:**
  - Detectar con rayos y calcular el impulso como altura × factor + impulso fijo [Probable] https://devforum.roblox.com/t/how-can-i-accomplish-a-vault-system/1785246
  - El Kong es como mantener salto al saltar un obstáculo en Parkour Reborn [Probable] https://parkour-reborn.fandom.com/wiki/Movement

#### Subir bordes (mantle) y mantle jump
- **Botón:** ninguno, es automático cuando miras al borde y vas hacia él. Funciona en el suelo y en el aire.
- **Cuándo funciona:**
  - La parte de arriba del borde está entre 3.8 studs (incluido) y 8 studs por encima de tus pies.
  - Miras hacia el borde con 45° de diferencia como mucho.
  - Encima del borde hay 5.5 studs libres o más, para que quepas.
  - Usa los mismos rayos hacia delante que el vault, con largo max(3.5, velocidad × 0.12).
- **Ayuda:** si saltas a un borde y te quedas corto por menos de 1 stud, subes automáticamente.
- **Qué hace:**
  - Dura 0.35 s: subes durante 0.2 s y luego avanzas 1.5 studs durante 0.15 s.
  - Sales con el 60% de la velocidad que traías, con un mínimo de 16.
- **Por dentro:** mientras subes se usa el AirController. En cuanto pisas arriba, el GroundController (ver 3.2).
- **Mantle jump:** si pulsas Espacio en los últimos 0.15 s, sales saltando y conservas el 100% de la velocidad que traías.
- **Opcional:** las manos se pueden pegar al borde de forma automática con IKControl.
- **Cámara y efectos:** la cámara baja 0.5 studs y mira un poco hacia arriba. Sonido de agarrarse.
- **Referencias:**
  - Detectar bordes con rayos a varias alturas [Probable] https://devforum.roblox.com/t/how-would-i-make-ledge-grabbing/658375
  - IKControl [Confirmado] https://create.roblox.com/docs/reference/engine/classes/IKControl

#### Correr por la pared (wallrun)
- **Botón:** ninguno, es automático.
- **Cuándo funciona:**
  - Estás en el aire.
  - Tienes una pared casi vertical a 2 studs o menos a tu izquierda o derecha.
  - Estás empujando hacia delante **a lo largo de la pared**. "Hacia delante" se mide respecto a la pared, no respecto a la cámara.
  - Vas a 16 studs/s o más.
  - El suelo está a 3 studs o más por debajo.
  - No estás cayendo muy rápido (más despacio que 50 studs/s hacia abajo).
- **Cómo lo detecta el código:**
  - Un Spherecast (una bola lanzada desde el centro del personaje) hacia cada lado.
  - **Problema:** un Spherecast no detecta las piezas que ya tocan la bola al empezar [Confirmado]. Con radio 1 y una fuerza que te pega a la pared, la pared queda dentro de la bola, no se detecta y el wallrun se corta.
  - **Solución:** lanzar la bola desde un punto apartado de la pared (desplazado hacia el lado contrario), o usar radio ~0.5 con un Raycast de respaldo.
  - Comprueba que la pared es casi vertical: la Y de su normal tiene que estar entre −0.25 y 0.25.
  - Las paredes con el tag "NoWallrun" no valen. El rival tampoco cuenta como pared (los rayos no ven a ninguno de los dos personajes).
- **Qué hace:**
  - Corres a lo largo de la pared a tu misma velocidad, con un mínimo de 24.
  - En los primeros 0.5 s aceleras +6, con un tope de 42.
  - Si ibas subiendo, conservas la mitad de esa subida, como mucho 12. Si ibas cayendo, la caída se pone a 0.
  - La gravedad es del 15% durante los primeros 0.6 s. Luego sube poco a poco hasta el 100%, y a los 1.4 s te despegas.
  - **Cómo se baja la gravedad:** el motor de Roblox sigue poniendo la gravedad normal. El código añade una VectorForce hacia arriba = `AssemblyMass × Workspace.Gravity × (1 − 0.15)`. Ver 3.2.
  - Una fuerza pequeña (4 studs/s) te mantiene pegado a la pared.
- **Límites:**
  - Puedes correr por 2 paredes por salto. La segunda tiene que estar en otra dirección: su ángulo tiene que diferir 30° o más de la primera.
  - **Cuándo te despegas antes de tiempo:** si empujas hacia fuera de la pared (`dot(input, normal) > 0.5`) o si pasas 0.2 s sin empujar nada. Soltar un instante el stick no te despega.
  - Después de despegarte tienes 0.15 s para hacer un wall jump.
- **Recarga el dash aéreo.**
- **Cámara y efectos:** la cámara se inclina 8° hacia el lado contrario a la pared. FOV +8. Polvo en la pared y pasos más rápidos.
- **Referencias:**
  - En Titanfall 2 el wallrun dura unos 1.75 s [Probable] https://titanfall2.fandom.com/wiki/Enhanced_Parkour_Kit
  - En Parkour Reborn hay 2 wallruns por salto y el segundo tiene que ser en otro ángulo [Probable] https://parkour-reborn.fandom.com/wiki/Movement
  - Gravedad del 18% y 0.15 s de margen para volver a pegarse (proyecto amateur) [Confirmado] (tfmvn, URL de arriba)
  - Inclinación de cámara de unos ±11° [Probable] https://devforum.roblox.com/t/wallrun-camera-tilt-snaps-and-not-smooth/2404000
  - Spherecast, y que no detecta lo que ya toca la bola al empezar [Confirmado] https://create.roblox.com/docs/reference/engine/classes/WorldRoot

#### Saltar desde la pared (wall jump y wall kick)
- **Botón:** Espacio (con buffer de 0.12 s).
- **Wall jump** (durante el wallrun, o hasta 0.15 s después de despegarte):
  - Sales con 32 studs/s hacia fuera de la pared y 50 hacia arriba, más el 90% de la velocidad que llevabas a lo largo de la pared.
  - Ganas +3 de momentum.
  - Durante 0.15 s no puedes controlarte en el aire, para que no te vuelvas a pegar a la misma pared.
- **Wall kick** (en el aire, sin estar corriendo por la pared ni escalando, con una pared delante o al lado a 2 studs o menos):
  - Sales con 30 studs/s hacia fuera y 46 hacia arriba, más la mitad de tu velocidad hacia delante.
  - Solo 1 por salto.
- **Si estás escalando**, Espacio no hace un wall kick: hace el salto hacia atrás de la escalada (ver 2.4).
- **Cámara y efectos:** FOV +5 durante 0.15 s y un temblor muy pequeño. La inclinación de la cámara vuelve a 0 en 0.2 s. Sonido de golpe en la pared.
- **Referencias:**
  - Saltar en la dirección de la normal de la pared más hacia arriba, y quitar la velocidad que va contra la pared [Probable] https://devforum.roblox.com/t/improvements-on-wallrunning-and-walljumping-system/3219917
  - Celeste bloquea el control durante 0.16 s después de un wall jump [Confirmado] (URL de Celeste de arriba)

#### Escalar la pared (wall climb)
- **Botón:** ninguno, es automático.
- **Cuándo funciona:**
  - Saltas de frente contra una pared, con menos de 35° de diferencia. (Con 35° o más y la pared a un lado, es un wallrun.)
  - Empujas hacia delante y vas hacia la pared a 8 studs/s o más.
  - La pared no tiene el tag "NoClimb".
- **Qué hace:**
  - Subes a 22 + (0.5 × momentum) studs/s durante 0.5 s como mucho. Eso son unos 11–14.5 studs.
  - Solo 1 vez por salto.
  - Si arriba hay un borde, lo subes automáticamente (mantle).
  - Si no hay borde, te separas un poco de la pared y caes.
  - Si pulsas Espacio mientras escalas, saltas hacia atrás (28 studs/s hacia fuera y 44 hacia arriba) y te das la vuelta 180°.
- **Hasta dónde se puede llegar:**
  - **En una pared suelta** (sin otra pared al lado o enfrente a la que llegues con un wall jump, y sin un punto de enganche cerca): salto (7.4) + escalada (hasta 14.5) + la inercia al acabar la escalada (unos 2, porque sales subiendo a 29 studs/s) + subir el borde (8) + la ayuda del mantle (1) ≈ 33 studs. Por eso, las paredes sueltas que no se deban poder subir tienen que medir 37 studs o más, o llevar el tag "NoClimb".
  - **En una esquina o un callejón** se llega bastante más alto (más de 40 studs) encadenando wallrun, wall jump, otro wallrun, otro wall jump, el wall kick, la escalada y el mantle. Cada wall jump sube unos 6.4 studs, el wall kick unos 5.4 y cada wallrun hasta unos 2.4 (si entras subiendo). Ahí no te fíes de la altura: pon "NoWallrun" en las paredes de alrededor y "NoClimb" en la que no se deba subir.
  - **Cerca de un punto de enganche** también se llega más alto: soltándote del gancho puedes subir a más de 45 studs (ver "Rodar al aterrizar").
- **Cámara y efectos:** la cámara mira 4° más arriba. Sonido de pasos rápidos.
- **Referencia:** en Parkour Reborn se escala 1 vez por salto y la altura depende del momentum [Probable] https://parkour-reborn.fandom.com/wiki/Movement

#### El gancho (swing): el movimiento estrella [Propuesta]
- **Botón:** mantener E / clic izquierdo / RT / botón Gancho. Al soltar el botón, te sueltas. En móvil también se puede usar "Tocar para engancharse" (ver 2.1).
- **A qué te enganchas:** a puntos de enganche marcados en el mapa. Son partes con el tag "SwingPoint": carteles de pizzería, farolas, marcos de puertas...
  - [Propuesta] Es mejor que engancharse a cualquier pared, por dos motivos: el rival puede ver por dónde vas a ir, y así se puede equilibrar el mapa.
- **Cuándo funciona:**
  - El punto está a 65 studs o menos.
  - Está al menos 4 studs por encima de ti.
  - Está dentro de un cono de 30° de **medio ángulo** desde el centro de la cámara (es decir, 30° hacia cualquier lado del centro). En móvil y con mando, 40° y con ayuda al apuntar.
  - No hay paredes en medio (el rayo no ve a ninguno de los dos personajes).
  - Si hay varios, se elige el más cercano al centro de la pantalla. Un icono marca el punto elegido antes de que pulses.
  - **Para que el icono no parpadee entre dos puntos:** el punto elegido solo cambia si otro está claramente mejor colocado, por ejemplo 5° más cerca del centro. [Propuesta]
- **Cómo se mueve el péndulo:**
  - Al engancharte, la cuerda mide tu distancia al punto × 0.95. Si estás en el suelo, × 0.9. Como mínimo 10 studs (como mucho sale 65 × 0.95 ≈ 62, así que no hace falta otro tope).
  - **Engancharse desde el suelo:** acortar la cuerda no basta para levantarte. Al engancharte en el suelo se cambia al AirController y se da un impulso hacia el punto y hacia arriba [hay que probarlo].
  - **La gravedad la pone el motor de Roblox.** El código no la suma, porque entonces habría el doble. El código solo añade:
    - Una fuerza de 30 studs/s² en la dirección en la que empujas.
    - La cuerda: si te alejas más que su largo, se quita la velocidad que te lleva hacia fuera y se corrige tu posición para dejarte justo sobre la esfera de la cuerda.
  - Con una cuerda de 30 studs bien aprovechada llegas a unos 55–75 studs/s en el punto más bajo.
- **Al soltarte:**
  - Conservas la velocidad que llevas.
  - **Buen lanzamiento** (te sueltas subiendo, después de haber pasado el punto más bajo): tu velocidad se multiplica por 1.12 (ganando como mucho 10), recibes 10 studs/s extra hacia arriba y ganas +4 de momentum.
  - Si te sueltas en otro momento, ganas +2 de momentum.
- **Límites:**
  - La cuerda se rompe a los 3 s. Así nadie se puede esconder colgado.
  - Tienes que esperar 0.35 s entre un gancho y el siguiente.
  - El mismo punto no se puede volver a usar hasta pasado 1 s.
  - Tope de velocidad: 80 studs/s.
- **Recarga el dash aéreo y los 2 wallruns.**
- **La cuerda es solo un efecto visual:** un Beam desde la mano hasta el punto. La física no usa RopeConstraint, porque en la DevForum hay hilos de gente a la que RopeConstraint le hace girar sin control o dar tirones al personaje. Solo los he visto en resúmenes del buscador, y que eso pase siempre con jugadores es una deducción mía [Especulativo] (https://devforum.roblox.com/t/rope-constraints-are-causing-player-to-spin-uncontrollably/3908273, https://devforum.roblox.com/t/ropeconstraint-in-tool-causes-character-to-glitch/1081925).
- **Cámara y efectos:**
  - El FOV sube con la velocidad, más hasta +10 extra, sin pasar del tope de 95 (ver 2.5).
  - La cámara se inclina hasta 5° hacia el lado del balanceo.
  - Líneas de velocidad a partir de 38 studs/s.
  - Sonido de viento que sube de tono cuanto más rápido vas.
  - Al soltarte: un "whoosh" y FOV +6 durante un momento.
- **Idea:** que la cuerda parezca queso fundido estirado. [Propuesta]
- **Referencias:**
  - La ficha de Medal.tv de "Pizza Hour [BETA]" (copia de terceros, vista solo en un resumen del buscador; no está confirmado que sea el juego de sdrame_ez) dice "swing from door to door". Que eso sea una cuerda es [Especulativo] (URL de Medal de arriba).
  - Calcular el péndulo en el código, la cuerda solo visual y un impulso extra al soltar [Probable] https://devforum.roblox.com/t/how-would-i-make-a-web-swinging-system-with-a-pendulum-motion/1094968
  - El sistema de código abierto Hooksystem usa gravedad al 0.5, fuerza de balanceo 35, tope de 120 studs/s y oculta los efectos por debajo de 40 [Confirmado] https://github.com/Ecliptorhizes/Hooksystem
  - Yo propongo gravedad completa (la del motor, sin VectorForce) y tope de 80, para que se lea mejor en un 1v1 en un mapa pequeño.

#### Dash
- **Botón:** Q / X (Cuadrado) / botón Dash.
- **Cuándo funciona:**
  - En el suelo: cada 1.5 s. El que pilla, cada 1.2 s.
  - En el aire: 1 vez por salto. Se recarga al tocar el suelo, al empezar un wallrun o al engancharte.
- **Qué hace:**
  - Durante 0.15 s vas a 42 studs/s, o a tu velocidad si ya vas más rápido.
  - **Dirección:** hacia donde empujas. Si no empujas, hacia donde mira la cámara pero **aplanado**: solo cuenta la parte horizontal, sin la inclinación arriba o abajo. Si no, mirando al suelo harías un dash contra el suelo.
  - Durante esos 0.15 s no hay gravedad: te quedas flotando un instante. El código pone una VectorForce hacia arriba = `AssemblyMass × Workspace.Gravity`, que anula la gravedad del motor (ver 3.2).
  - Después sigues a 26 studs/s, o a la velocidad que llevabas antes si era mayor.
  - No da momentum.
- **Dash-jump:** si saltas durante un dash en el suelo, conservas la velocidad del dash. Es el "abalanzarse" para pillar. Saltas unos 23 studs de largo, y con el dash aéreo después, unos 29.
- **Cámara y efectos:** FOV +12 (sube en 0.08 s y vuelve en 0.3 s, sin pasar del tope de 95), un desenfoque que va de 6 a 0 en 0.2 s (se apaga con "Reducir efectos") y un "whoosh".
- **Referencias:**
  - Ejemplo oficial de Roblox de un dash con ApplyImpulse [Confirmado] https://create.roblox.com/docs/characters/character-controller-library/custom-abilities
  - Usar LinearVelocity, porque BodyVelocity está obsoleto [Probable] https://devforum.roblox.com/t/making-a-dash-system/3657525
  - El proyecto amateur de antes usa 72–100 studs/s. Aquí es más bajo porque es un 1v1.

#### Pillar (tocar al otro)
- **Botón:** ninguno, es automático al tocar.
- **Qué cuenta como "tocar":** que los centros de los dos personajes (los HumanoidRootPart) estén a 4.5 studs o menos en horizontal y a 5.5 studs o menos en vertical.
  - Para que sea justo, todos los avatares miden lo mismo (ver 3.2, paso 1).
- **Los jugadores no chocan entre sí:** los personajes van en un grupo de colisión (CollisionGroup) que no choca consigo mismo. El pillado va por distancia, y dos cuerpos simulados en ordenadores distintos que chocan dan tirones y se bloquean.
- **Sin devoluciones inmediatas:** el que acaba de recibir la marca no puede devolverla durante 1.5 s. Sale un indicador en pantalla.
- **El rojo se distingue:** lleva un resaltado rojo (Highlight) y deja una estela. El Highlight pesa en móviles flojos, así que también va atado a "Reducir efectos" y a la calidad gráfica. La estela sigue marcando quién es el rojo.
- **Cámara y efectos:**
  - Al que pilla: temblor de 0.2 s, un sonido y vibración en el mando.
  - Al pillado: el borde de la pantalla se pone rojo y se reproduce una animación de reacción.
- **Cómo se comprueba en el servidor:** ver la sección 3.4.

### 2.3 Cómo se encadenan los movimientos

| Desde | Hacia | Qué pasa |
|---|---|---|
| Correr | Deslizarse | Entras con tu velocidad × 1.15 (el extra no pasa de 36) |
| Deslizarse | Saltar | Conservas el 100% de la velocidad (a 36, unos 20 studs de largo). +2 de momentum si saltas en los primeros 0.35 s |
| Salto, aterrizar | Deslizarse otra vez (slide-hop) | El deslizamiento está listo justo al aterrizar. Mantienes unos 32–36 studs/s |
| Caída de 70 studs/s o más | Rodar | Perfecta: 100% de la velocidad y +3 de momentum. Temprana: 85%. Si no ruedas, hay castigo solo desde 95 studs/s (medio) y 125 (duro) |
| Rodar | Saltar (roll cancel) | Sales al instante sin perder velocidad |
| Correr | Saltar obstáculo (o Kong pulsando Espacio durante el vault) | +2 de momentum (Kong: +3) |
| Salto | Correr por la pared | Conservas tu velocidad a lo largo de la pared (mínimo 24) |
| Correr por la pared | Wall jump | +3 de momentum y el 90% de la velocidad |
| Wall jump | Correr por otra pared | Es tu segundo wallrun del salto |
| Escalar pared | Subir borde | Automático si llegas arriba (hasta unos 33 studs en total en una pared suelta) |
| Escalar pared | Salto hacia atrás (Espacio) | 28 studs/s hacia fuera, 44 hacia arriba y giro de 180° |
| Subir borde | Mantle jump | Conservas el 100% de la velocidad que traías |
| Wallrun o wall jump | Gancho | Permitido. Recarga el dash y los wallruns |
| Gancho | Soltarse y luego wallrun, saltar obstáculo o rodar | Conservas la velocidad del lanzamiento |
| Gancho | Otro gancho ("de puerta en puerta") | Hay que esperar 0.35 s y usar otro punto distinto |
| Dash en el suelo | Saltar (dash-jump) | Conservas la velocidad del dash: unos 23 studs de largo |
| Dash-jump | Dash aéreo | Unos 6 studs más: hasta unos 29 en total |
| Dash en el aire | Wallrun o gancho | Permitido |

**Lo que te hace perder velocidad:** girar bruscamente en el suelo (más de 110° en 0.2 s), aterrizar duro (caer a 125 studs/s o más sin rodar) y estar casi parado más de 0.25 s.

### 2.4 Qué se recarga y qué tiene prioridad

**Recargas**
- **Al tocar el suelo:** se recarga todo (dash aéreo, los 2 wallruns, el wall kick y la escalada).
- **Al empezar un wallrun:** se recarga el dash aéreo.
- **Al engancharte al gancho:** se recargan el dash aéreo y los 2 wallruns.
- **El wall kick y la escalada** solo se recargan al tocar el suelo.

**Prioridades: qué gana si dos movimientos coinciden** [Propuesta]
- **Movimientos automáticos.** Si en el mismo frame valen varios, gana el primero de esta lista:
  1. Mantle
  2. Vault
  3. Escalar
  4. Wallrun
  - (El wall kick no está en esta lista porque no es automático: sale con Espacio. Su prioridad está en "Espacio en el aire cerca de una pared", abajo.)
- **Rangos que no se solapan** (el límite pertenece solo a uno):
  - Vault: altura desde 1.5 (incluido) hasta 3.8 (sin incluir).
  - Mantle: altura desde 3.8 (incluido) hasta 8.
  - Escalar: pared de frente con menos de 35° de diferencia. Con 35° o más y la pared a un lado, wallrun.
- **Espacio en el aire cerca de una pared:**
  1. Si estás corriendo por la pared, o hace menos de 0.15 s que te despegaste: wall jump.
  2. Si estás escalando: salto hacia atrás de la escalada (28 / 44).
  3. Si no: wall kick (30 / 46), si te queda.

### 2.5 Cámara y efectos generales
- **El FOV sube con la velocidad.**
  - `Camera.FieldOfView` es el ángulo **vertical**. Un FOV de 110 en vertical serían unos 140° en horizontal en una pantalla 16:9: un ojo de pez extremo.
  - FOV objetivo = 70 + 15 × clamp((velocidad − 20) / 45, 0, 1) + los extras de cada movimiento.
  - El extra por velocidad va de +12 a +15. Empezamos con +15.
  - **Tope: 95** (prueba también 90). Los extras de cada movimiento (slide +6, wallrun +8, dash +12, gancho hasta +10...) se suman, pero el total nunca pasa del tope.
  - Para que cambie suave: fov += (objetivo − fov) × (1 − e^(−8·dt)). Con este suavizado, en 0.125 s solo recorre un 63% del cambio (un 47% en 0.08 s y un 70% en 0.15 s).
  - **Por eso, los golpes rápidos de FOV de cada movimiento van aparte:** el dash (+12, sube en 0.08 s), el wall jump (+5 durante 0.15 s) y el de soltarse del gancho (+6) usan su propio tween, más rápido, y se suman encima del FOV suavizado. Si pasaran por el suavizado, no llegarían a su valor. El total sigue sin pasar del tope de 95.
  - No hay que redondear la velocidad, porque hace temblar el FOV. [Probable] https://devforum.roblox.com/t/fov-based-on-characters-speed/1931197
- **Líneas de velocidad:** partículas (ParticleEmitter) en un anillo delante de la cámara, o una animación de imagen en la pantalla (spritesheet en un ImageLabel).
  - Aparecen a partir de 38 studs/s y se vuelven más opacas cuanto más rápido vas.
  - Roblox no tiene desenfoque de movimiento de verdad. Se imita con un BlurEffect. [Probable] https://devforum.roblox.com/t/how-to-make-a-speed-blur/1559118
- **Inclinación del cuerpo:** el torso se inclina 6° hacia donde aceleras. Se calcula en el código, no hace falta animarlo (ver 3.3). [Probable] https://devforum.roblox.com/t/a-character-tilt-that-is-velocity-based/3887894
- **Inclinación de la cámara:**
  - Al ir de lado (strafe): 2° como mucho.
  - Cada movimiento tiene la suya: slide 3°, gancho hasta 5° y wallrun 8°. No se suman: manda la del movimiento que estés haciendo.
- **Balanceo de cabeza al correr:** casi nada (amplitud 0.15) o apagado. En juegos competitivos se recomienda poco. [Probable] https://devforum.roblox.com/t/configurable-head-bobbing-script/1505850
- **Opción "Reducir efectos" en ajustes:** cambios de FOV a la mitad, sin temblores, sin inclinaciones, sin desenfoque, con menos partículas de velocidad, y el resaltado (Highlight) se reduce o se quita (la estela sigue marcando quién es el rojo). Para la gente que se marea y para móviles flojos.
- **Calidad gráfica:** si la calidad gráfica del jugador es baja, el desenfoque (BlurEffect), las partículas de velocidad y el resaltado (Highlight) también se reducen o se apagan, aunque no haya activado "Reducir efectos".

### 2.6 Medidas para tus mapas en Blender
Salen de los números de arriba, así que son [Propuesta]. **Todas suponen que todos los avatares miden lo mismo** (ver 3.2, paso 1).

**Distancias de salto**
- Un salto sube 7.4 studs y dura unos 0.55 s en el aire. El largo es más o menos velocidad × 0.55:
  - Corriendo a 20 studs/s: unos 11 studs.
  - Corriendo a 34 studs/s (momentum lleno): unos 19.
  - Slide-jump a 36: unos 20.
  - Dash-jump a 42: unos 23.
  - Dash-jump + dash aéreo: unos 29.
- **Huecos:**
  - 8–10 studs: fáciles.
  - 14–18: necesitan momentum.
  - 20–29: se pueden saltar con slide-jump, dash-jump o dash aéreo.
  - **Los huecos que deban exigir el gancho (o una pared para correr) tienen que medir 32 studs o más.**
  - **Ojo: esta regla de 32 supone que llegas sin velocidad sobrante y sin bajar una cuesta deslizándote.** Con velocidad sobrante (por ejemplo, de un gancho anterior) se salta más lejos: un slide a 48 + dash aéreo ≈ 34 studs, un salto a 60 ≈ 33, y a 80 (el tope) unos 44, más con el dash aéreo. Una cuesta abajo justo antes también da velocidad al slide. Así que un hueco solo exige el gancho de verdad si antes no hay una cuesta abajo ni otro punto de enganche desde el que llegar lanzado. Si quieres margen contra un poco de velocidad sobrante (slide a 48, salto a 60), hazlos de 36–38. Contra un salto a 80 no sirve ningún tamaño razonable: ahí lo que manda es dónde pones los puntos de enganche. [hay que probarlo]

**Tamaños de los obstáculos**

| Elemento | Medidas |
|---|---|
| Obstáculos para saltar por encima (vault) | De 1.5 a menos de 3.8 studs de alto, y 5 de grosor como mucho |
| Bordes para subir (mantle) | De 3.8 a 8 studs por encima del suelo donde estás |
| Huecos para pasar deslizándose | Mínimo 3.5 studs de alto; recomendado 3.5–4.5, siempre por debajo de la altura de pie [hay que probarlo] |
| Paredes para correr por ellas | 12 studs de alto o más, 25–45 de largo, planas y con colisión Box. Las que no quieras que sirvan, con el tag "NoWallrun" |
| Paredes que se pueden escalar | Con salto + escalada + subir el borde se llega hasta unos 30 studs, y unos 33 contando la inercia al acabar la escalada y la ayuda del mantle (con el momentum lleno, en una pared suelta) |
| Paredes que NO se deben poder subir | En una pared suelta (sin otra pared cerca para wallrun o wall jump, y sin punto de enganche cerca): 37 studs o más, o con el tag "NoClimb". En esquinas y callejones se llega a más de 40: ahí usa los tags "NoWallrun" y "NoClimb" (ver "Escalar la pared") |
| Puntos de enganche | A 20–35 studs de altura, separados 25–45 studs, y que se vean bien (por ejemplo, un cartel de pizza). Si te sueltas a esa altura sin velocidad hacia arriba, caes a unos 89–117 studs/s (aterrizaje normal o medio si no ruedas). Pero con un buen lanzamiento desde un punto alto y cuerda corta puedes caer a 125 o más: aterrizaje duro si no ruedas (ver "Rodar al aterrizar") |
| Huecos que exigen el gancho | 32 studs o más, siempre que antes no haya cuesta abajo ni otro punto de enganche que te dé velocidad sobrante. 36–38 si quieres margen (ver "Huecos" arriba) |

**Tamaño de la arena:** para empezar, unos 150×150 studs con recorridos en bucle y sin callejones sin salida.

**Requisitos técnicos de Roblox** [Confirmado]
- Cada malla puede tener como mucho 20.000 triángulos (https://github.com/Roblox/creator-docs/blob/main/content/en-us/art/modeling/specifications.md).
- Al importar, la opción "Anchored" viene apagada. Tienes que encenderla para el mapa (https://github.com/Roblox/creator-docs/blob/main/content/en-us/studio/importer.md).
- Usa colisión Box o Hull. Para formas complicadas, pon partes invisibles que hagan de colisión (https://github.com/Roblox/creator-docs/blob/main/content/en-us/parts/meshes.md).
- Reutilizar las mismas piezas muchas veces es más barato para el juego que hacer muchas piezas distintas (https://github.com/Roblox/creator-docs/blob/main/content/en-us/performance-optimization/improve.md).

**Cómo marcar los puntos de enganche desde Blender:** modela un cubo pequeño y llámalo `SwingPoint_01`, `SwingPoint_02`... Al cargar el mapa, un script les pone el tag automáticamente (o se lo pones tú con el Tag Editor de Studio). Lo mismo para las paredes "NoWallrun" y "NoClimb". Los objetos "Empty" de Blender puede que no se importen como partes. [Especulativo]

### 2.7 Ideas opcionales [Propuesta]
- **Rebote en la pizza:** en el aire lanzas la caja de pizza, se queda flotando 0.4 s y puedes saltar encima una vez. Sería como la gorra de Mario Odyssey: un resumen dice que su lanzamiento de pizza se inspiró en ese juego [Especulativo]. Funcionaría como un doble salto con estilo propio.
- **Cuerda de queso fundido:** solo como efecto visual del gancho.

---

## 3. Cómo se programa en Roblox (arquitectura)

### 3.1 Qué opción usar

| Opción | Ventajas | Inconvenientes | Decisión |
|---|---|---|---|
| **A.** Humanoid normal + LinearVelocity | Es la que tiene más tutoriales | El Humanoid frena el impulso en el aire y no deja ajustar la fricción. Acabas peleándote con él | No |
| **B.** Humanoid con su sistema automático apagado + ControllerManager propio | Deja conservar el impulso en el aire y ajustar aceleración y fricción. Control total. Existe desde 2023. Las animaciones que pone el cliente se ven en los demás jugadores sin hacer nada | La física se calcula en el cliente, así que el servidor tiene que vigilar las trampas. El Humanoid deja de cambiar de estado: hay que hacer nuestro propio script de animaciones y los sonidos de pasos | **Sí, para la versión 1** [Propuesta] |
| **C.** Character Controller Library (CCL) + Server Authority | El servidor decide todo y bloquea los hacks de velocidad. Hay plantillas oficiales para empezar (ver 3.6) | Reglas muy estrictas (ver 3.6). CCL todavía es una beta de Studio. Un desarrollador contó que daba fallos al mover la cámara y el personaje a la vez [Especulativo] | Plan B para una versión 2 |

Fuentes:
- ControllerManager: https://create.roblox.com/docs/reference/engine/classes/ControllerManager
- Opciones de los controladores: https://create.roblox.com/docs/reference/engine/classes/AirController
- CCL: https://create.roblox.com/docs/characters/character-controller-library

### 3.2 Cómo funciona el controlador

1. **Ajustes en Studio (Avatar Settings):**
   - Deja Movement > Abilities en "Legacy Humanoid", que es la opción por defecto [Confirmado] (https://create.roblox.com/docs/studio/avatar-settings, Movement > Abilities: "Legacy Humanoid (default)"). Si creaste el juego desde la plantilla Classic Obby, compruébalo: en esa plantilla CCL viene activado [Probable].
   - **Iguala los avatares:** en General, "Consistent Gameplay", o en Collision, "Single Collider". Si no, los avatares pequeños caben por huecos por los que otros no, y un HipHeight distinto cambia la altura de todos los rayos.
2. **En el servidor, cuando aparece el personaje (`CharacterSetup`):**
   - Se crea un ControllerManager con un GroundController (para el suelo) y un AirController (para el aire).
   - `ControllerManager.RootPart` = el HumanoidRootPart.
   - Se añade un sensor de suelo (ControllerPartSensor en modo Floor) dentro del HumanoidRootPart y se asigna a `ControllerManager.GroundSensor`. Su `SearchDistance` ≈ GroundOffset + 1.5.
   - `GroundController.GroundOffset = Humanoid.HipHeight`. Si no, el personaje se arrastra o flota.
   - Se ajustan `BaseTurnSpeed` (lo rápido que gira), `FacingDirection` (hacia dónde mira) y `ActiveController` (empieza con el GroundController).
   - El sensor dice lo que ha encontrado con `SensedPart`, `HitFrame` y `HitNormal`. El cliente los lee para saber si hay suelo y cómo está inclinado.
   - Los personajes se meten en un grupo de colisión que no choca consigo mismo (ver "Pillar" en 2.2).
   - Se pone `Humanoid.EvaluateStateMachine = false` [Confirmado] (https://create.roblox.com/docs/reference/engine/classes/Humanoid). Esto tiene consecuencias:
     - El Humanoid deja de aplicar fuerzas y de buscar el suelo él solo.
     - Deja de cambiar de estado por sí mismo, y tampoco replica su estado a los demás.
     - **El script Animate de Roblox y los sonidos por defecto (pasos, salto, aterrizaje) dejan de funcionar.** Solución: poner un LocalScript vacío llamado "Animate" en StarterCharacterScripts (así Roblox no pone el suyo), y que nuestro `AnimationClient` elija las animaciones y haga los sonidos. Otra opción es llamar a `Humanoid:ChangeState` a mano: la documentación dice que, si pones los estados a mano, sus eventos siguen saltando y el script Animate sigue animando según ellos [Confirmado] (misma URL de Humanoid, en EvaluateStateMachine).
     - **Solo el torso y la cabeza tienen colisión.** Hay que decidir a propósito con qué partes choca el personaje [hay que probarlo].
     - **MoveDirection** (lo que lee hacia dónde empujas) sigue funcionando: la documentación dice que se sigue actualizando con `Humanoid:Move()` y los PlayerScripts [Confirmado] (Humanoid.yaml, apartado de EvaluateStateMachine: https://github.com/Roblox/creator-docs/blob/main/content/en-us/reference/engine/classes/Humanoid.yaml). Aun así, lo comprobamos en el paso 1 de 3.7.
   - Sigo el patrón del tutorial de la DevForum [Probable] (https://devforum.roblox.com/t/how-to-actually-use-robloxs-physics-character-controllers/3092097).
3. **Ajustes de los controladores:**
   - GroundController: AccelerationTime 0.2, DecelerationTime 0.12 y GroundOffset = HipHeight.
   - AirController: `MoveMaxForce = 0`. El control en el aire lo hace nuestro código (paso 4).
4. **En el cliente, en cada frame (en el momento PreSimulation):**
   - Lee lo que pulsas y lanza los rayos para detectar paredes, bordes y obstáculos.
     - **Todos los rayos (Raycast y Spherecast) usan unos `RaycastParams` que excluyen a los dos personajes.** Si no, el rival cuenta como pared, obstáculo o borde.
     - Los rayos hacia delante miden max(3.5, velocidad × 0.12).
   - Decide en qué estado estás (corriendo, deslizándote, en la pared...).
   - **En el suelo:** `BaseMoveSpeed = base + momentum + sobrante` (× 1.05 si eres el rojo). `MovingDirection` va normalizada pasada la zona muerta del stick.
   - **En el aire, control estilo Quake:**
     ```lua
     -- v: tu velocidad horizontal; dir: hacia donde empujas (normalizado)
     local actual = v:Dot(dir)            -- lo rápido que ya vas hacia ese lado
     local falta = maximo - actual        -- maximo = base + momentum (× 1.05 si eres el rojo)
     if falta > 0 then
         v += dir * math.min(falta, 30 * dt)  -- 30 studs/s cada segundo
     end
     ```
     Si ya vas más rápido que tu máximo hacia ese lado, ni te frena ni te acelera. Ojo: como en Quake, girando en el aire se puede ganar algo de velocidad. El tope de 80 lo limita [hay que probarlo].
   - Ajusta hacia dónde miras (`FacingDirection`).
   - Cambia entre el controlador de suelo y el de aire según el sensor de suelo.
   - **Al saltar:** cambia al AirController en el mismo frame del impulso e ignora el sensor de suelo unos 0.1 s.
5. **Movimientos especiales:**
   - **Los que van pegados al suelo usan el GroundController.** El slide: `BaseMoveSpeed` = velocidad del slide, `GroundOffset` más bajo y poca fricción. También la rodada (`BaseMoveSpeed` = la velocidad que conservas), los aterrizajes medio y duro (`BaseMoveSpeed` casi 0 mientras dura la parada) y el final del mantle, cuando ya pisas arriba. Si aquí usáramos el AirController con `MoveMaxForce = 0`, el personaje perdería la levitación y se hundiría hasta que chocara el torso.
   - **Los que van por el aire usan el AirController con `MoveMaxForce = 0`:** wallrun, escalar la pared, gancho, vault (y Kong), la subida del mantle y el dash. El código escribe directamente la velocidad (`AssemblyLinearVelocity`) en PreSimulation.
   - **Los impulsos que te lanzan al aire** (salto, slide-jump, mantle jump, wall jump, wall kick y el salto hacia atrás de la escalada) cambian al AirController en el mismo frame del impulso, igual que el salto (paso 4), y siguen en el estado Aire.
   - **La gravedad la pone siempre el motor**, en el paso de física que va justo después de PreSimulation. El código nunca la suma, o habría el doble. Para tener menos gravedad se añade una VectorForce hacia arriba = `AssemblyMass × Workspace.Gravity × (1 − factor)`:
     - Dash (sin gravedad, factor 0): la VectorForce anula toda la gravedad.
     - Wallrun (gravedad al 15%, factor 0.15): la VectorForce es masa × gravedad × 0.85.
     - Gancho (gravedad completa): sin VectorForce.
   - [hay que probarlo]
6. **Saltos e impulsos:** se hacen con `ApplyImpulse` o escribiendo la velocidad directamente (recuerda el cambio de controlador del paso 4).
7. **Por qué en PreSimulation:** es donde Roblox recomienda cambiar velocidades y fuerzas [Confirmado] (https://create.roblox.com/docs/performance-optimization/microprofiler/task-scheduler).
8. **Dónde se calcula la física:** tu personaje te pertenece (network ownership), así que su física se calcula en tu ordenador. Por eso se ve fluido y sin lag, pero el servidor tiene que vigilar las trampas [Confirmado] (https://create.roblox.com/docs/scripting/security/network-ownership).

### 3.3 Qué va en el cliente y qué en el servidor

```
ReplicatedStorage/
  Shared/MovementConfig      -- todos los números de la sección 2
  Shared/MovementMath        -- cálculos puros: velocidad del slide, wall jump, paso del péndulo...
  Shared/AnimationIds        -- los IDs que me pases
  Remotes/  TagClaim, SwingStart, SwingEnd, RoundState
StarterPlayerScripts/
  MovementClient   -- botones (Input Action System) + máquina de estados (Suelo, Aire, Slide, WallRun,
                   --   WallClimb, Vault, Mantle, Swing, Dash, Roll, MediumLand, HardLand) + física en PreSimulation
                   --   (Kong es una variante de Vault; mantle jump, wall jump, wall kick, slide-jump
                   --   y el salto hacia atrás de la escalada son impulsos que pasan a Aire)
  CameraFX         -- FOV, inclinación, temblor, líneas de velocidad, vibración del mando
  AnimationClient  -- sustituye al Animate de Roblox: qué animación suena según el estado
                   --   + sonidos de pasos, salto y aterrizaje
  TagClient        -- detecta el toque en tu pantalla y avisa al servidor
StarterCharacterScripts/
  Animate          -- LocalScript VACÍO, para que Roblox no ponga su script Animate
ServerScriptService/
  CharacterSetup   -- crea el ControllerManager, apaga el sistema automático del Humanoid
                   --   y pone el grupo de colisión
  RoundManager     -- rondas de 30 s, marcador hasta 3, quién es el rojo
  TagService       -- comprueba los toques con el historial de posiciones
  MovementSanity   -- detecta trampas de velocidad
```

- **Animaciones:** el cliente las reproduce en su propio Animator y los demás jugadores las ven solas, sin hacer nada más.
- **Lo que crea o cambia el cliente no llega a los demás** (atributos, partes, efectos).
  - Por eso los efectos del rival (estela, líneas de velocidad) los calcula cada jugador a partir de la velocidad del rival.
  - La cuerda del gancho del rival se manda así: el cliente avisa al servidor con `SwingStart` y el punto de enganche → el servidor comprueba que el punto existe y está a 75 studs o menos → avisa al otro jugador, que dibuja la cuerda. Los 75 son los 65 del cliente más 10 de margen por el lag: el servidor ve tu posición con algo de retraso, y a 80 studs/s en 0.125 s te mueves 10 studs. [Propuesta]
- **Quién es el rojo:** lo guarda el servidor como atributo del jugador. Como lo pone el servidor, sí llega a todos.
- **Inclinación del cuerpo en el código:**
  - Se hace en PreSimulation y **multiplicando, sin sobrescribir:** `joint.Transform = inclinacion * joint.Transform`. Si se sobrescribe, se pierde lo que pone la animación.
  - No se hace si `Animator.EvaluationThrottled` está activo.
  - **Qué es `joint`:** solo hay AnimationConstraint si `StarterPlayer.AvatarJointUpgrade` está activado ("por defecto en experiencias nuevas"). Con eso activado, los R15 ya no usan Motor6D. Por eso el código busca primero AnimationConstraint y, si no hay, usa Motor6D.
  - Si se escribe en RenderStepped, el Animator lo pisa y no se ve.
  - [Confirmado] https://create.roblox.com/docs/reference/engine/classes/AnimationConstraint y https://create.roblox.com/docs/reference/engine/classes/Motor6D
- **Inclinación de la cámara:** se añade con `BindToRenderStep` a prioridad `Enum.RenderPriority.Camera.Value + 1`, encima de la cámara normal. Esto lo deduzco de las prioridades que vienen en la documentación, no lo dice ningún ejemplo oficial [Especulativo] (https://create.roblox.com/docs/reference/engine/classes/Camera).
- **Botones: Input Action System desde la versión 1** (`PlayerScriptsUseInputActionSystem`). Es lo que recomienda ahora la documentación de Roblox, en vez de ContextActionService:
  - Permite controles distintos para cada dispositivo.
  - Permite botones táctiles propios (`InputBinding.UIButton`) y un umbral para los gatillos (`PressedThreshold`).
  - `InputActionLabel` muestra el icono correcto de cada mando.
  - Es obligatorio en Server Authority, así que el plan B (3.6) queda más fácil.

### 3.4 Cómo comprueba el servidor que un toque es válido

1. **Historial de posiciones.** El servidor apunta la posición del centro de cada personaje 30 veces por segundo y guarda el último segundo. Cada posición lleva su hora, tomada con `workspace:GetServerTimeNow()`.
2. **Camino A: solo el servidor.** En cada frame del servidor (Heartbeat):
   - Para cada jugador se toma el tramo que ha recorrido desde la muestra anterior hasta la actual.
   - Se calcula la **distancia mínima entre esos dos tramos**. Si en algún punto están a 4.5 studs o menos en horizontal y 5.5 o menos en vertical, cuenta como pillado.
   - Comparar solo los puntos sueltos dejaría pasar cruces rápidos: los dos jugadores se cruzan entre dos muestras y nunca parecen estar cerca.
3. **Camino B: el cliente avisa (compensación de lag).** Tu pantalla ve al rival con algo de retraso. Por eso tu cliente detecta el toque en lo que tú ves y manda `TagClaim(hora)` al servidor, con la hora de `workspace:GetServerTimeNow()` en ese momento. El servidor lo acepta solo si se cumple todo esto:
   - La ronda está en marcha.
   - Quien avisa es el rojo.
   - Ya han pasado los 1.5 s de protección.
   - No ha mandado más de 5 avisos por segundo.
   - **La hora se limita** a [ahora − *R*, ahora]. *R* = el menor entre (`Player:GetNetworkPing()` del rojo + 0.1) y 0.3 s.
   - Se mira dónde estaba el rival **en esa hora**, interpolando entre las dos muestras del historial que la rodean, y solo en una ventana estrecha alrededor de ella. Esa posición y la posición actual del rojo tienen que pasar la misma prueba de cilindro que el camino A (la misma función), con 2 studs de margen: 6.5 studs o menos en horizontal (4.5 + 2) y 7.5 o menos en vertical (5.5 + 2).
   - **Por qué no aceptar "cualquier momento de los últimos *R* segundos":** a 34 studs/s, 0.3 s son unos 10 studs de margen extra. Demasiado.
   - Cuanto mayor sea *R*, más justo es para quien tiene lag, pero más fácil de abusar. Por eso el límite es 0.3 s. [Propuesta]
4. **Los dos caminos usan la misma función, `TryTag`.** Solo acepta un pillado cada 0.2 s, aplica la protección de 1.5 s, cambia quién es el rojo, mueve el resaltado rojo y avisa a los dos jugadores.
5. **Final de la ronda:** manda el reloj del servidor. Opcional: aceptar avisos que lleguen hasta 0.25 s tarde si su hora es anterior al final, para que los pillados del último segundo sean justos.
6. **No usar el evento `.Touched` para pillar.** Como la física de cada personaje se calcula en su propio cliente, no es fiable. Con distancias funciona mejor. Y como los personajes no chocan entre sí (grupo de colisión, ver 3.2), no hay tirones cuando se tocan. [Propuesta]

### 3.5 Contra las trampas de velocidad
Roblox recomienda tener en cuenta el lag, mirar medias en el tiempo, usar un "cubo que gotea", medir solo el movimiento horizontal y dejar excepciones para los teletransportes [Confirmado] (https://create.roblox.com/docs/scripting/security/network-ownership).

**Cómo funciona el "cubo que gotea":**
- En cada frame del servidor se mide cuánto se ha movido el jugador en horizontal (d).
- Se actualiza el cubo así: `cubo = max(0, cubo + d − vmax × dt)`, con vmax ≈ 100 studs/s (por encima del tope de 80, para dejar margen).
- **Por qué así:** las posiciones del cliente llegan a ráfagas: unos frames sin movimiento y luego uno con el doble. Si se mirara cada frame por separado (por ejemplo, con un límite de 85 studs/s), un solo frame doble a 80 studs/s ya llenaría el cubo aunque el jugador fuera legal. Con esta fórmula, los frames sin movimiento compensan los dobles.
- **Otra opción:** medir la distancia recorrida en una ventana de 0.25–0.5 s y compararla con vmax × la duración de la ventana.
- Si el cubo pasa de 25: el jugador vuelve a su última posición válida y se apunta en un registro. En la versión 1 solo se apunta, no se echa a nadie.

**Otras reglas:**
- No se vigila durante los momentos en que el servidor teletransporta a los jugadores (al aparecer y al empezar una ronda).
- Estar más de 5 s en el aire sin haber usado el gancho se apunta como sospechoso.

### 3.6 Plan B: Server Authority + CCL
- **Cómo se activa:** poniendo `Workspace.AuthorityMode = Server`. Eso enciende automáticamente NextGenerationReplication, el Input Action System, SignalBehavior Deferred, UseFixedSimulation y StreamingEnabled [Confirmado] (https://create.roblox.com/docs/projects/server-authority).
- **Reglas que obliga a seguir:**
  - La lógica de movimiento tiene que ir en un ModuleScript compartido por cliente y servidor, dentro de `RunService:BindToSimulation`.
  - **Ojo:** `BindToSimulation` va a 30 Hz por defecto (`Hz30`). Para el movimiento hay que pasarle `Enum.StepFrequency.Hz60`.
  - El estado se guarda en atributos. Solo se sincronizan los 64 primeros de cada objeto, con nombres de 50 caracteres como mucho y textos de 50 como mucho [Confirmado] (https://create.roblox.com/docs/projects/server-authority#attribute-limits).
  - Los botones tienen que usar InputActions. Como ya usamos el Input Action System desde la versión 1, esta parte ya estará hecha.
  - El reloj es `time()`.
  - [Confirmado] https://create.roblox.com/docs/reference/engine/classes/RunService y la URL de Server Authority de arriba
- **Animaciones, cámara y efectos** van fuera de la simulación, en PreRender. Las animaciones se buscan con `GetTrackByAnimationId` [Confirmado] (https://create.roblox.com/docs/projects/server-authority/techniques).
- **Con CCL, cada movimiento sería una "habilidad",** como el ejemplo oficial de Dash. Su código no puede esperar (nada de task.wait) y tiene que dar siempre el mismo resultado con las mismas entradas [Confirmado] (https://create.roblox.com/docs/characters/character-controller-library/custom-abilities).
- **CCL sigue siendo una beta de Studio.** Hay que activarla en File > Beta Features > "AvatarAbilities Character Controller Library".
- **Plantillas oficiales:** la documentación de Server Authority enlaza plantillas para empezar: Racing, Soccer y Laser Tag. Laser Tag es la más parecida a un pilla-pilla (URL de Server Authority de arriba).
- **El pillado** lo decidiría directamente la simulación del servidor, sin avisos del cliente.
- **Riesgos:**
  - Es nuevo: según los resúmenes, salió para todos en julio de 2026 [Probable] (https://devforum.roblox.com/t/full-release-ship-fair-and-competitive-games-with-server-authority/4727993).
  - Un desarrollador contó que daba fallos al mover la cámara y el personaje a la vez [Especulativo] (https://x.com/Rawblocky/status/2076091937174810634).
- **Para que cambiar sea fácil más adelante,** escribiré los cálculos de cada movimiento como funciones puras, sin `task.wait`, `math.random` ni `os.clock`.

### 3.7 Orden en el que lo construiremos
1. Personaje con el ControllerManager: correr, saltar (con coyote time, buffer y cambio de controlador), momentum y FOV. Script Animate propio y sonidos de pasos. **Aquí comprobamos que MoveDirection sigue funcionando con `EvaluateStateMachine = false`** y con qué partes choca el personaje. Un mapa gris de pruebas.
2. Rondas y pillado: rondas de 30 s y se lleva la partida el primero en ganar 3 rondas, con la comprobación en el servidor. **A partir de aquí ya se puede jugar un 1v1.**
3. Deslizarse, slide-jump, rodar y aterrizajes.
4. Saltar obstáculos y subir bordes.
5. Correr por la pared, wall jump y escalar.
6. El gancho.
7. El dash.
8. Pulir la cámara y los efectos, las trampas, las opciones de accesibilidad, y probar en móvil y con mando.

**Cómo probar:**
- Siempre con 2 jugadores en Studio (pestaña Test > Clients and Servers).
- Siempre con lag simulado: usa el Network Simulator de Studio (beta: File > Beta Features > New Device Simulator). Añade latencia, jitter (lag que sube y baja) y pérdida de paquetes.

---

## 4. Animaciones que tienes que hacer en Blender

### 4.1 Lista
Los fotogramas son a 30 fps. Las duraciones son [Propuesta].

Como apagamos el script Animate de Roblox (ver 3.2), todas estas animaciones las pone mi código, también las básicas como quieto o correr.

| # | Animación | Prioridad | ¿En bucle? | Fotogramas | Notas | Cuándo |
|---|---|---|---|---|---|---|
| 1 | Quieto (idle) | Idle | Sí | 60–90 | Respiración suave | v1 |
| 2 | Correr | Movement | Sí | 20 (2 pasos) | Dime a qué velocidad la animaste, para sincronizar los pies | v1 |
| 3 | Correr rápido | Movement | Sí | 16 | Se mezcla con "Correr" según la velocidad | v1 |
| 4 | Despegue del salto | Action2 | No | 6 | También para el mantle jump, al final de "Subir borde" | v1 |
| 5 | Caída | Movement | Sí | 20 | Brazos sueltos | v1 |
| 6 | Aterrizaje suave | Action3 | No | 6 | | v1 |
| 7 | Deslizarse | Action | Sí | 20 | Pose agachada con algo de movimiento | v1 |
| 8 | Rodada | Action3 | No | 12 | Sin desplazar el personaje | v1 |
| 9 | Aterrizaje duro | Action3 | No | 10 | También para el aterrizaje medio, reproducida más rápido para que dure 0.15 s | v1 |
| 10 | Saltar obstáculo | Action2 | No | 10 | Marca de evento "HandPlant" hacia el fotograma 4 | v1 |
| 11 | Subir borde | Action2 | No | 11 | Marca de evento "Grab" hacia el fotograma 2 | v1 |
| 12 | Wallrun izquierda | Action | Sí | 18 | | v1 |
| 13 | Wallrun derecha | Action | Sí | 18 | La 12 en espejo, hecha en Blender | v1 |
| 14 | Wall jump izquierda | Action2 | No | 9 | También para el wall kick (la del lado de la pared; si la pared está delante, cualquiera de las dos) | v1 |
| 15 | Wall jump derecha | Action2 | No | 9 | La 14 en espejo. También para el wall kick | v1 |
| 16 | Colgado del gancho | Action | Sí | 24 | Brazo derecho arriba. El código lleva la mano al punto de enganche | v1 |
| 17 | Soltarse del gancho (voltereta) | Action2 | No | 15 | Puedes hacer 2 versiones para variar | v1 |
| 18 | Pillar (tocar) | Action4 | No | 7 | **Solo brazos y torso** | v1 |
| 19 | Ser pillado (reacción) | Action4 | No | 10 | **Solo torso, cabeza y brazos** | v1 |
| 20 | Dash | Action2 | No | 9 (5 de dash + 4 de recuperación) | | v1 |
| 21 | Kong | Action2 | No | 12 | Marca de evento "HandPlant" | v1 |
| 22 | Escalar pared | Action | Sí | 14 | | v1 |
| 23 | Salto hacia atrás desde la pared | Action2 | No | 12 | | v1 |
| 24 | Victoria y derrota | Action4 | No | 60–90 | **Cuerpo entero.** Al final de la ronda | v2 |
| 25 | Lanzar pizza | Action4 | No | 12 | Marca de evento "Release". Solo si hacemos la idea opcional | Opcional |

**Qué significa cada prioridad:**
- **Movement:** para moverse normal (correr, caer).
- **Action:** para estados que duran un rato (deslizarse, wallrun, gancho).
- **Action2:** para movimientos cortos que interrumpen a los anteriores (despegue del salto, saltar obstáculos, wall jump, soltarse, dash).
- **Action3:** para los aterrizajes (suave, medio, duro y la rodada).
- **Action4:** para lo que va encima de todo: las animaciones que solo mueven la parte de arriba del cuerpo (pillar, ser pillado) y las del final de la ronda (victoria y derrota, de cuerpo entero, cuando ya no te mueves).

**Cómo se mezclan** [Confirmado]: en cada parte del cuerpo gana la animación de prioridad más alta. Si dos tienen la misma prioridad, se mezclan según su peso. Por eso, si "Pillar" no tiene fotogramas clave en las piernas, las piernas siguen corriendo mientras el brazo toca (https://github.com/Roblox/creator-docs/blob/main/content/en-us/reference/engine/enums/AnimationPriority.yaml).

### 4.2 Reglas al animar
- **Pon Blender a 30 fps.** Blender usa 24 por defecto, y el Animation Editor de Roblox trabaja a 30 fps por defecto [Confirmado] (https://github.com/Roblox/creator-docs/blob/main/content/en-us/animation/editor.md).
- **Las animaciones no mueven al personaje: se quedan en el sitio.** Si el hueso raíz avanza, quítale ese movimiento antes de exportar. El desplazamiento real lo hace mi código [Confirmado] (https://github.com/Roblox/creator-docs/blob/main/content/en-us/art/characters/export-avatar-animations-from-maya.md).
- **Exporta una animación por archivo FBX.** La guía oficial pide desmarcar All Actions y NLA Strips al exportar, así que solo sale la acción activa. Que haya que hacer un archivo por animación lo deduzco de ahí; la guía no lo dice tal cual [Especulativo] (https://github.com/Roblox/creator-docs/blob/main/content/en-us/avatar/character-bodies/export.md).
- **Animaciones en bucle:** pon al final una copia de los primeros fotogramas clave, porque Roblox no mezcla el último con el primero [Confirmado] (https://github.com/Roblox/creator-docs/blob/main/content/en-us/animation/editor.md).
- **Marcas de evento** (HandPlant, Grab, Release): mi código las escucha con `GetMarkerReachedSignal` para lanzar sonidos y efectos justo en ese fotograma [Confirmado] (https://github.com/Roblox/creator-docs/blob/main/content/en-us/animation/events.md).
- **Consejos de animación** (son consejos generales, no una guía oficial):
  - Pon la anticipación (agacharse antes de saltar) y el retraso de brazos y cabeza en los propios fotogramas clave.
  - Las transiciones entre animaciones serán cortas, de 0.05 a 0.15 s. Si son más largas, se emborrona el timing.
  - Fuente de la parte técnica: https://github.com/Roblox/creator-docs/blob/main/content/en-us/reference/engine/classes/AnimationTrack.yaml
- **No llames a una malla igual que un hueso** (por ejemplo, una malla "Head" bajo el hueso "Head"). Puede romper la importación [Especulativo] (https://devforum.roblox.com/t/what-do-these-options-mean-fbx-vs-selected/3930429).

### 4.3 Cómo pasar una animación de Blender a Roblox
1. **Consigue el esqueleto.** Usa el archivo oficial `Rig_and_Attachments_Template.blend`, que es un R15 con los nombres correctos (https://github.com/Roblox/creator-docs/blob/main/content/en-us/avatar/character-bodies/project-files.md).
   - Los huesos tienen que llamarse y colgar exactamente así: Root > HumanoidRootPart (o HumanoidRootNode) > LowerTorso > UpperTorso > Head, los brazos y las piernas. Root y LowerTorso tienen que estar en 0,0,0.
   - La documentación no se aclara entre "HumanoidRootPart" y "HumanoidRootNode". Usa el nombre que traiga la plantilla (https://github.com/Roblox/creator-docs/blob/main/content/en-us/avatar/character-bodies/specifications.md).
2. **Prepara la escena:** Units > Unit System = None, rotación en grados y 30 fps (https://github.com/Roblox/creator-docs/blob/main/content/en-us/art/blender.md).
3. **Anima** y luego quita el desplazamiento del hueso raíz.
4. **Exporta en FBX con estos ajustes:**
   - Apply Scalings = "FBX Unit Scale" [Confirmado]
   - Forward = Z Forward, Up = Y Up, según la guía oficial de Blender para Roblox. Una guía no oficial dice -Y Forward: si la animación sale girada, prueba eso.
   - Armature > Add Leaf Bones: apagado [Confirmado]
   - Bake Animation: encendido. Dentro de esa sección, NLA Strips, All Actions y Force Start/End Keyframes: apagados [Confirmado]
   - Simplify = 0, para no perder fotogramas clave en movimientos rápidos. Esto lo deduzco yo y no lo he probado [Especulativo] (https://github.com/blender/blender/blob/main/scripts/addons_core/io_scene_fbx/__init__.py)
   - Fuentes: https://github.com/Roblox/creator-docs/blob/main/content/en-us/art/modeling/export-requirements.md y https://github.com/Roblox/creator-docs/blob/main/content/en-us/avatar/character-bodies/export.md
5. **Importa en Studio:**
   - Crea un muñeco R15 con el Rig Generator.
   - Abre la pestaña Avatar > Animation Editor ("Clip Editor") y haz clic en el muñeco.
   - Ponle nombre a la animación y pulsa Create.
   - En el menú "..." elige Import > From FBX Animation [Confirmado] (la URL de export-avatar-animations-from-maya del apartado 4.2).
   - Desde agosto de 2026 el importador tiene opciones nuevas: Rig Scale, Rest Pose Source, Rig Type y elegir qué pista importar [Probable] (https://devforum.roblox.com/t/animation-import-improvements/4775593). También acepta glTF [Probable] (https://devforum.roblox.com/t/full-release-animation-clip-editor-improved-importing-and-gltf-support/4260501).
6. **Configura la animación:** en "..." > Set Animation Priority pon la prioridad de la tabla. Activa el botón Looping si va en bucle. Añade las marcas de evento (activa antes "Show Animation Events" en los ajustes de la línea de tiempo).
7. **Publica:** "..." > Publish to Roblox. Si el juego es de un grupo, elige ese grupo como creador [Confirmado] (https://github.com/Roblox/creator-docs/blob/main/content/en-us/animation/editor.md). Si la animación es de otro dueño distinto al del juego, normalmente no carga. Esto es un comportamiento conocido de Roblox, pero no lo he comprobado en esta investigación [Especulativo].
8. **Copia el ID** (`rbxassetid://...`) y pásamelo.

**Haz primero una prueba con un clip corto, por ejemplo el despegue del salto.** Así compruebas que los ejes y la escala salen bien antes de animar todo.

### 4.4 Otra opción: el plugin RBXMonkey
- Es un plugin de la comunidad, no oficial: "Blender Animations Plugin" de Cautioned, con licencia GPL-3.0.
- Se compone de un add-on para Blender y un plugin para Studio (el asset 16708835782 de la Creator Store).
- Sincroniza en directo entre los dos programas y permite pasar animaciones en los dos sentidos.
- Necesita Blender 4.2 o más reciente. Su última versión, la v3.0.1, es del 27 de agosto de 2026 [Confirmado] (https://github.com/Cautioned/Blender-Animations-Plugin).
- Es útil porque la exportación a glTF de Studio no incluye animaciones [Confirmado] (https://github.com/Roblox/creator-docs/blob/main/content/en-us/art/modeling/gltf-export.md).
- El plugin oficial de Roblox para Blender sirve sobre todo para subir mallas, no sustituye al Animation Editor (https://github.com/Roblox/roblox-blender-plugin).

### 4.5 Lo que necesito de ti
1. **Capturas o una grabación del vídeo que me mandaste** (https://www.tiktok.com/@sdrame_ez/video/7671501462718942486), o que me cuentes qué movimientos ves en él (mira las preguntas del final del apartado 1).
2. **Los IDs de las animaciones** de la versión 1 (filas 1–23), o los que tengas, para empezar.
3. **Un mapa de prueba en bloques ("gris")** con las medidas del apartado 2.6, para ajustar los números jugando.
4. Si puedes, que me confirmes los controles del apartado 2.1, o lo que quieras cambiar. Por ejemplo, si en móvil prefieres "mantener" o "tocar" para el gancho.
