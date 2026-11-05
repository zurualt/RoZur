# Overbooked!

Juego cooperativo de 1 a 4 jugadores: la tripulación de la peor aerolínea del mundo. Uno pilota y los demás atienden la cabina: sirven comida y bebida, calman pasajeros, apagan fuegos, tapan agujeros del fuselaje y cuidan de la carga… incluido un cocodrilo.

Todo el código es Luau estricto, sin comentarios. El arte se genera en Blender con scripts y se sube por la API de Open Cloud. El lugar también se construye con Rojo y se publica por la API.

## Vista previa

Montado en Blender con la misma lógica de colocación que usa el juego (`herramientas/vista_previa.py`). En Roblox las ventanas muestran el cielo y el mundo en movimiento; aquí se ve el interior del casco porque Blender dibuja las caras traseras.

![Cabina de pasajeros](renders/cabina_pasajeros.png)
![Cabina del piloto](renders/cabina_piloto.png)
![Bodega con la carga y la jaula](renders/bodega.png)
![Torreta en el ala](renders/ala_torreta.png)
![Exterior en el aeropuerto](renders/exterior.png)

## Cómo se juega

1. **Aeropuerto (lobby):** apareces en la terminal. En el tablero hay 3 vuelos (ruta, distancia, pasajeros, carga, riesgo y pago aproximado) y delante de cada uno un círculo de su color. Entrad en el círculo con vuestro grupo (hasta 4): a los 15 s os lleva juntos a un servidor reservado y la partida empieza dentro del avión. Al acabar volvéis al lobby. En Studio no hay teletransporte y la partida se juega en el mismo servidor.
2. **Preparación (hasta 2,5 min) en el hangar de equipaje:** las maletas salen por 4 toboganes numerados y hay que dejarlas en el carro; si el contrato lleva cocodrilo, anda suelto por su corral (dale la merienda del cubo, cógelo y suéltalo junto a su jaula); y hay que bombear combustible (mantener E en el surtidor) hasta el 100 %. Con todo hecho se abre la persiana (a los 150 s se abre igual), aparecen flechas en el suelo y uno conduce el tractor con el carro hasta la rampa del avión. En Studio, `PruebaPreparacion = true` en Workspace empieza una partida directamente aquí, con cocodrilo.
2. **Embarque (25 s):** suben los pasajeros y se carga la bodega. Entra al avión por la rampa trasera.
3. **Despegue:** alguien se sienta en el asiento izquierdo de la cabina, acelera con **Shift** y, al pasar de 260 km/h, sube con **W**. Si nadie pilota en 45 s, despega el piloto automático.
4. **Vuelo:** mantén el rumbo (el panel dice hacia dónde girar) y la altitud. El piloto automático ayuda, pero se desconecta con los sustos.
5. **Aproximación:** a 140 km del destino el aterrizaje es manual. Hay que llegar a 0 m con menos de 340 km/h, bajando despacio y con las alas rectas.
6. **Resultados:** se cobra por pasajeros entregados (según su satisfacción), carga intacta, entregas aéreas y la calidad del aterrizaje. Se resta por pasajeros perdidos, carga perdida y daños. El dinero se reparte y se guarda.
7. **Si os estrelláis: la isla.** El avión acaba en la playa de una isla desierta, con los motores ardiendo. Hay 5 minutos para pedir rescate: llevar las 3 piezas de radio (antena, batería y radio) a la estación de radio, 3 troncos a la hoguera de señales y encenderla con la bengala. Entonces llega un hidroavión al muelle y se cobra la mitad de los billetes más 300 de rescate. Por la isla hay cangrejos que pellizcan, cocos que caen de las palmeras (sirven de comida y bebida para los pasajeros) y los iconos dibujados marcan cada pieza y cada destino. Si se acaba el tiempo, nadie viene a por vosotros.

## Controles

| Acción | Teclado | Mando |
|---|---|---|
| Coger / soltar (con ayuda de puntería: vale apuntar cerca; en móvil también tocando el objeto) | Clic | R2 |
| Lanzar (toque rápido) / lanzar fuerte con arco de puntos (mantener y soltar) | Clic derecho | L2 |
| Dejar con cuidado, de pie y delante | G | L1 |
| Girar lo que llevas | R | R1 |
| Acercar / alejar lo grande | Rueda | Cruceta arriba / abajo |
| Bofetada (con las manos vacías) | Clic derecho | L2 |
| Usar extintor, llave o agua | F (mantener) | X |
| Tocar la bocina del carrito | F (con el carrito) | X |
| Interactuar (servir, coger comida, botones, puertas) | E | — |
| Sentarse en un asiento libre | G | Y |
| Abrir / cerrar altillos | T | B |
| Piolet: clavarte al casco / soltarte | F / Espacio | botón «Piolet» |
| Tractor: conducir | WASD (sentado) | stick |
| Silenciar la música | M | — |
| Calmar a un pasajero | R (mantener) | — |
| Pilotar: subir / bajar · girar | W / S · A / D | Stick izquierdo |
| Pilotar: más / menos gases | Shift / Ctrl o Q | R2 / L2 |
| Ayuda | H | — |

## Sistemas

| Sistema | Archivo | Qué hace |
|---|---|---|
| Partida | `src/server/Partida.luau` | Lobby con círculos de salida → servidor reservado (contrato por MemoryStore) → embarque → vuelo → resultados → vuelta al lobby, contratos y cobro |
| Preparación | `src/server/Preparacion.luau` + `src/client/Preparacion.luau` + `mapa/Preparacion.model.json` | Hangar de equipaje (en ServerStorage hasta que empieza la partida): toboganes, cocodrilo, surtidor, persiana, flechas hasta la rampa; lista de tareas, tarjeta de progreso y marcas dibujadas. Números en `Config.PREPARACION` |
| Vuelo | `src/server/Avion.luau` | Simulación a 10 Hz, piloto y automático, motores, combustible, casco, rampa, puertas y botones |
| Pasajeros | `src/server/Pasajeros.luau` | Pedidos 🍔 ☕ 💧 con paciencia, miedo y satisfacción (cada bandeja lleva 3 hamburguesas); salen volando si no llevan cinturón |
| Carga | `src/server/Carga.luau` | Daños por golpes, cajas frágiles, entregas aéreas desde la rampa y el cocodrilo |
| Peligros | `src/server/Peligros.luau` | Turbulencias, pájaros que incendian un motor, fuego que se extiende, agujeros que succionan, caída libre, tormenta y fallo de motor |
| Agarrar | `src/server/Agarre.luau` + `src/client/Agarre.luau` | Física con propiedad de red para quien sostiene; se puede coger a pasajeros y lanzarlos por la puerta. Lo pequeño va en la mano derecha (empuñado, en la palma o colgando, según `Manos.estilo`); lo grande, con las dos manos delante, más lento y con vaivén. `src/client/AgarreVista.luau` dibuja el contorno y la etiqueta «Coger» de lo que vas a coger, el arco del lanzamiento y el aplastado al cogerlo |
| Manos | `src/client/Manos.luau` | Dedos con huesos: relajados, se abren y cierran al coger, aprietan lo que llevas, se abren al alcanzar algo y el índice señala al pulsar botones. También los de los demás jugadores |
| Personajes | `src/server/Personajes.luau` + `src/client/Cuerpo.luau` | Tripulante como StarterCharacter, color por jugador, ragdoll, caídas del avión, viento en las alas |
| Cámara | `src/client/Camara.luau` | Primera persona con brazos visibles, balanceo al andar, inclinación con el avión y sacudidas |
| Mundo | `src/client/Mundo.luau` | El avión no se mueve: nubes, campos y pista se mueven a su alrededor en cada cliente |
| Interfaz | `src/client/Interfaz.luau` + `src/shared/Gui.luau` | Interfaz dibujada a mano (Blender): tarjeta de embarque con la ruta y la cuenta atrás, etiqueta de equipaje con el estado del avión, avisos en notas con cinta, pizarra del piloto, burbujas de pedidos, nombres con altavoz, ayuda y factura de resultados con sello. Sin emojis: todo son iconos dibujados |
| Cara | `src/client/BocaVoz.luau` + `src/client/Cara.luau` + `src/client/Ojos.luau` | Cara del tripulante: boca, lengua, cejas, mofletes y nariz con huesos que reaccionan a la voz y a lo que pasa (susto, mareo, grito, alegría, enfado); ojos saltones con parpadeo |
| Datos | `src/server/Datos.luau` | Dinero y vuelos en DataStore, con bloqueo de sesión para no pisar datos al cambiar de servidor |
| Piratas | `src/server/Piratas.luau` + `src/client/Piratas.luau` | Aviones pirata que dañan el casco; se derriban desde la torreta del ala izquierda |

| Interacciones | `src/server/Interacciones.luau` | Lo que vuela golpea: pasajeros que se enfadan o salen del asiento, jugadores que caen, cocodrilo aturdido. La comida lanzada al pasajero que la pide cuenta como servida. Café y agua dejan charcos resbaladizos; el agua apaga el fuego; las bandejas se derraman |
| Cabina | `src/server/Cabina.luau` + `src/client/Cabina.luau` | Altillos que se abren con las turbulencias y sueltan bolsos (se guardan soltándolos junto al altillo abierto), asientos para jugadores (sentado no te caes), mascarillas de oxígeno, luces que parpadean y de emergencia, volante, palancas y torreta animados |

Todos los números del juego están en `src/shared/Config.luau`.

| Tractor y carro | `src/server/Vehiculos.luau` + `src/client/Vehiculo.luau` | Tractor conducible que remolca el carro de maletas (E junto a la lanza para enganchar) |
| Piolet | `src/client/Escalada.luau` | Trepar por fuera del fuselaje sobre un casco invisible; en el techo hay viento fuerte en vuelo |
| Aduana | `src/server/Aduana.luau` | Escáner con cinta: revela el contrabando; el contenedor de aduanas da +60 por maleta y cada una que llegue a destino es una multa de 150 |
| Tienda | `src/server/Tienda.luau` + `src/client/Tienda.luau` + `src/shared/Accesorios.luau` + `src/server/Mejoras.luau` | Catálogo dibujado con pestañas (Cabeza, Cara, Espalda y Mejoras), miniaturas, vista 3D de tu tripulante que gira (arrastrar, stick derecho), sello de «¡COMPRADO!» y lluvia de monedas. 24 accesorios, uno por hueco; los más raros piden vuelos. El servidor valida precio, vuelos y propiedad, guarda lo comprado (`Accesorios`) y lo puesto (`Puestos`) en la clave `t_` (los `Gorros`/`Gorro` antiguos se migran solos) y los suelda a `Head`, `UpperTorso` o `LowerTorso` para que todos los vean. Mando: L1/R1 pestañas, Y comprar/poner, B cerrar |
| Sonido | `src/server/Sonidos.luau` + `src/client/Sonido.luau` | Efectos con posición, bucles (motores, viento, alarma, lluvia, fuego) y música por fase |
| Guía | `src/client/Guia.luau` + `src/server/Datos.luau` | Panel único de TAREAS (a la izquierda) con la tarea actual resaltada, contadores, flecha dibujada con distancia sobre su objetivo y flecha en el borde si queda fuera de pantalla; tarjetas que entran desde abajo al empezar cada fase, el primer peligro y el primer caos de cada tipo (completas las 2 primeras veces, luego compactas; se saltan con Enter, la X o Select en el mando) y se guardan en el panel; «Cómo se juega» en 3 tarjetas la primera vez en el lobby (también en Ajustes); consejos de una línea junto a la mira la primera vez que miras un pedido, fuego, agujero, cabina, torreta, tractor, surtidor o cocodrilo. Lo ya visto se guarda en `Ajustes.Visto` (validado en el servidor, remoto `Visto`). En Studio, `ReiniciarGuia = true` en Workspace lo borra todo |
| Isla | `src/server/Isla.luau` + `mapa/Isla.model.json` | Fase de náufragos tras estrellarse: piezas de radio, leña, hoguera, bengala, hidroavión, cangrejos y cocos. El relieve es Terrain de Roblox: `generar_mapa.py` calcula una rejilla de alturas de 4 studs (dunas, selva, colina con mirador, acantilados, laguna, estanque con cascada, surco del aterrizaje) y la guarda en el StringValue `Terreno`; el servidor la escribe con `WriteVoxelChannels` al estrellarse (unos 0,2 s) junto con el mar, y la borra en `Isla.limpiar()`. La isla vive en ServerStorage con unos 1000 adornos colocados por el mismo generador y se pone alrededor del avión al estrellarse. En Studio, el atributo `PruebaIsla = true` en Workspace salta directo a la isla |
| Roturas | `src/server/Roturas.luau` + `src/client/Roturas.luau` + `src/shared/PiezasRoturas.luau` | El avión se rompe en pedazos de verdad: con el casco a 65 se parte la punta de un ala, a 40 se va la deriva, a 20 se vuela el techo de la fila 7 (salen maletas, un váter y un pollo de goma) y con un motor en llamas el capó aletea y sale volando. Con el casco a 0 el avión se parte en dos a cámara lenta (la cola y la bodega se alejan, un pasajero saluda desde su asiento) y en la isla la cola queda caída. Al romperse algo, el casco se cambia por las piezas sueltas; todo vuelve a su sitio al volver al lobby o al embarcar. En Studio: atributo `PruebaRotura` en Workspace (`Ala`, `AlaIzq`, `AlaDer`, `Capo`, `CapoIzq`, `CapoDer`, `Deriva`, `Techo`, `Partido`, `Todo`, `Reparar`) |
| Lobby | `src/server/Lobby.luau` + `mapa/Aeropuerto.model.json` | Terminal abierta de 64×96 con techo de madera inclinado y fachada de cristal hacia el avión. Líneas de colores en el suelo llevan del punto de aparición a cada puerta; encima de cada puerta cuelga un farol con su número. Cosas que hacer mientras esperáis: subirse a la cinta de equipajes (gira de verdad, con maletas), facturarse a uno mismo en la cinta del mostrador (sales por la cinta de equipajes), pesarse en la báscula (pantalla en kg, en rojo si hay exceso), arcos de seguridad que pitan al azar (siempre si llevas algo), timbre y micrófono de información (avisos de megafonía de broma, uno cada 20 s), máquinas de refrescos que sueltan latas (a veces se tragan la moneda o dan premio), café de la cafetería, fotomatón que imprime una foto con tu cara, pelota para dar patadas, carros de maletas para empujar, bancos para sentarse en las puertas y tienda libre de impuestos. Lo que se sale de la terminal o se queda tirado vuelve solo a su sitio |
| Cinemáticas | `src/client/Cine.luau` | Herramientas comunes de cámara (prioridad Camera+3, letterbox, telón de papel, ocultar el HUD, saltar con cualquier toque o tecla, vuelta suave a la cabeza; nunca durante el modo clip) que también usa la intro. Tomas: rotura en el aire vista desde fuera a cámara lenta (el mundo también va lento), telón al cambiar a la isla y vuelta alrededor del avión estrellado (el sello sale aquí), hidroavión que planea y amerriza (se mueve en cada cliente) con toma desde el muelle. La «pausa dramática» congela de verdad el vuelo 1,5 s. Los resultados esperan a que acabe la toma y se revelan fila a fila con sello y botón de cerrar |
| Móvil y gráficos | `src/shared/Gui.luau` + `src/client/Ajustes.luau` | `Gui.escala()` para toda la interfaz, `Gui.posTactil()` coloca los botones táctiles alrededor del de saltar (solo salen cuando sirven: Coger/Bofetada/Lanzar/Usar, Gas+/Gas-, Fuego, Piolet). El piloto vuela con el joystick. En táctil los textos cambian las teclas por botones (`Idioma`). Ajustes → Gráficos Automático/Altos/Bajos: en bajos hay menos nubes, pájaros, partículas y maleza de la isla, sin sombras, bloom ni reflejos del agua, y caras de pasajeros con menos detalle |
| Indicaciones | `src/client/Indicaciones.luau` | Todos los ProximityPrompt usan estilo propio: etiqueta de papel dibujada con la tecla, la acción, el objeto y una barra si hay que mantener; en móvil se toca la etiqueta. Al usar algo, la mano derecha se estira hacia delante (`Camara.alcanzar`) |
| Efectos | `src/server/Rafagas.luau` + `src/client/Rafagas.luau` + `src/shared/VFX.luau` | Ráfagas dibujadas que el servidor lanza con `Rafagas.lanzar(tipo, posición, escala, color)` por `Remotos.Efecto`: Explosion, ExplosionPequena, Humo, Chispas, Polvo, Arena, Estrellas, Confeti, Salpicadura, Escombros, Astillas, Cristales, Monedas, Hojas, Bengala, Vapor, Plumas y Onda, más Hongo (explosión grande con seta), Bonk, Ay, Martillazo, Bocina, Corazones, Enfado y Sudor. Muchas sacan una onomatopeya dibujada (¡BONK!, ¡CATAPLÁN!, ¡CRAC!, ¡PÍO!…) con aplastar y estirar. `Efectos.luau` añade las bromas: emociones encima de los pasajeros, estrellas de mareo en el ragdoll, silbato y «¡ADIÓOOS!» al caerse del avión, «pausa dramática» en sepia justo antes de estrellarse, sello con frase al estrellarse o aterrizar, aplausos al aterrizar, zoom dramático (pájaros, mascarillas, cocodrilo suelto; cada 30 s como mucho), rayas de velocidad en lo que vuela y vapor en el café |
| Caos | `src/server/Caos.luau` + `src/client/Caos.luau` + `src/shared/ModelosCaos.luau` + `arte/kit_caos/` | Doce sucesos de caos con su aviso, onomatopeyas y premio o multa en la factura («Caos a bordo»): cabra suelta (embiste y se come la comida; hay que lanzarla a la bodega), gallinas sueltas, bebé llorón (biberón de la cocina a su familia), pasajero encerrado en el baño (tirar de la puerta), cafetera loca (llave inglesa o explota y prende fuego), pasajero que va a abrir la salida de emergencia (placarlo o cogerlo; si la abre, succiona hasta cerrarla), peste a pescado (nube verde que marea; se dispersa con el extintor), turbulencia disco (bola, luces y todos botando), piloto automático borracho (desconectarlo 3 veces), estornudos (darle agua), carrito desbocado (cogerlo) y avalancha de equipaje. En Studio: atributo `PruebaCaos` en Workspace con el nombre (`Cabra`, `Gallinas`, `Bebe`, `Bano`, `Cafetera`, `Salida`, `Peste`, `Disco`, `Borracho`, `Estornudo`, `Carrito`, `Avalancha`) |

### Ritmo y dificultad

Los números están en `Config.RITMO`. Cada vuelo empieza con calma (50 s tras despegar solo hay pedidos y turbulencia suave) y luego la intensidad sube con el progreso del vuelo (de 0,5 a 1,6), el riesgo del contrato, la jornada y el número de jugadores (tope 2,6). La intensidad divide los intervalos de peligros (32–55 s) y de caos (50–80 s); los peligros graves (agujeros, tormenta, fallo de motor, piratas) no salen antes del 30 % del vuelo salvo en riesgo o jornada altos. La **jornada** sube con cada vuelo terminado (aterrizado o rescatado, hasta 8): más pasajeros, más paga y más caos. Se guarda por jugador en MemoryStore (`OverbookedJornadas`, 1 h) y pasa al servidor del vuelo con el contrato. Un vuelo dura de media unos 10 minutos (`COMPRESION = 14`).

### Cómo se relaciona todo

- **Fuego:** se apaga con el extintor, con agua (F con la botella o lanzándola) y con los charcos de agua. Daña la carga que tenga cerca.
- **Agujeros:** succionan objetos, pasajeros y jugadores. Una maleta, caja, carrito o bolso lanzado al agujero lo tapa hasta que lo repares con la llave; una sacudida fuerte puede hacerlo saltar. Al abrirse, caen las mascarillas.
- **Cocodrilo:** persigue la comida suelta o a quien la lleva. Si se come una hamburguesa se calma unos segundos; un golpe o el extintor lo aturden. Muerde a los pasajeros por los que pasa.
- **Turbulencias:** abren altillos, tiran la comida de las bandejas y el café de las manos, mueven la carga y las mascarillas, y hacen parpadear las luces.
- **Carga:** las cajas se rompen en astillas y las frágiles en cristales.
- **Techo:** un panel suelto daña el casco; hay que salir al ala, trepar con el piolet y clavarlo a martillazos (F).
- **Aduana:** las maletas con contrabando solo se ven al pasarlas por el escáner.
- **Pasajero alborotador:** se levanta y va dando tumbos; hay que cogerlo, sentarlo y calmarlo (R).
- **Condiciones de vuelo:** nocturno, niebla, VIP, pasaje hambriento o carga frágil de lujo; salen en el tablero y cambian el pago.
- **Premios:** al aterrizar se reparten premios (mejor camarero, bombero, mecánico, puntería, artillero, piloto, domador, relaciones públicas, domador del caos y el más torpe).
- **Embarque:** desde el asiento del piloto se puede terminar antes (mantén E).

## Carpetas

| Carpeta | Qué hay |
|---|---|
| `src/` | Código (servidor, cliente y compartido) |
| `mapa/` | Avión y aeropuerto en piezas de Roblox, generados por `herramientas/generar_mapa.py` |
| `arte/` | Modelos de Blender (tripulante, avión, pasajeros, objetos) con sus generadores, FBX, renders y manifiestos |
| `arte/kit_interior/` | Kit del interior del avión: paneles con ventanas, techo con altillos y sus puertas, cocina, baño, mamparas, cabina del piloto, pared de bodega, puertas, torreta en dos piezas, bolso, mascarilla y trozos de cajas |
| `arte/kit_aeropuerto/` | Kit del aeropuerto: terminal, puertas de embarque del lobby (`PuertaSala1-3`), mostradores, bancos, quioscos, marco del tablero, torre de control, hangar, carro, tractor, escalerilla, árboles, arbustos, vallas, conos, luces de pista y manga de viento |
| `arte/kit_preparacion/` | Hangar de equipaje (`kit_preparacion_gen.py`): nave con tragaluces, persiana, toboganes 1-4, surtidor, corral con piscina hinchable, cubo de merienda, pilas de cajas, lámparas, flecha de suelo y carteles con pictogramas. Ids en `ids_subida.json`, se registran solos con `src/shared/ModelosPreparacion.luau` |
| `arte/interfaz/` | Interfaz dibujada en Blender (`interfaz_gen.py`): 13 paneles 9-slice (papel, pizarra, billete, etiqueta, notas, botón, barras, burbuja, mira, sello) y una hoja de 59 iconos de 128 px. `herramientas/subir_imagenes.py` sube solo lo que cambia y genera `src/shared/ImagenesGui.luau` |
| `arte/vfx/` | 35 sprites de efectos dibujados en Blender (`vfx_gen.py`, usa las primitivas de `arte/interfaz/interfaz_gen.py`): humo, llama (flipbook 2x2), chispa, estrella, polvo, gota, corona de salpicadura, confeti, moneda, hoja, pluma, escombro, astilla, cristal, destello, explosión, hongo, onda, vapor, línea, pinchos y nube de cómic, espiral, corazón, vena de enfado, exclamación, interrogación, mancha, brillito, rayas de velocidad y marco de sello. Se suben con `python herramientas/subir_imagenes.py arte/vfx arte/vfx/ids.json src/shared/ImagenesVfx.luau` |
| `arte/accesorios/` | Accesorios de la tienda (`accesorios_gen.py`, usa las primitivas de `arte/kit_extra/kit_extra_gen.py`): casco vikingo, chistera diminuta, gorro de pez, plátano pelado, casco de bombero, cocodrilo comecabezas, nido con okupa, antifaz, gafas de estrella, monóculo, gafas de buceo, mochila paracaídas, mochila cohete, alas de avión, flotador de patito y llave gigante, más los 8 gorros antiguos rehechos para el tripulante v5 (se suben aparte, ya no salen de `Visuales`), con sus miniaturas dibujadas (`miniaturas/`) y renders de prueba sobre el tripulante v5 (`renders/`). Los diseños se encajan en la cabeza de alubia: los gorros se encogen, se suben a la cúpula y se echan 8° hacia atrás para que el borde quede por encima de las cejas; las gafas rodean los ojos saltones de `Ojos.luau`; correas, cadena, antifaz, plátano, auriculares y flotador se hacen sobre la superficie del tripulante (`tripulante.blend`). Si cambia el tripulante, hay que actualizar `PIVOTES` y los ojos del generador, regenerar y volver a subir. Subir: `subir_modelos.py arte/accesorios/ids_subida.json arte/accesorios/*.fbx`, `subir_imagenes.py arte/accesorios/miniaturas arte/accesorios/ids_miniaturas.json src/shared/MiniaturasAccesorios.luau` y luego `accesorios_gen.py -- --solo-luau` (escribe `src/shared/ModelosAccesorios.luau`) |
| `arte/kit_lobby/` | Kit de la terminal en Blender (`kit_lobby_gen.py`, reutiliza las funciones de `kit_aeropuerto_gen.py`): suelo, paredes con la fachada de cristal y techo con lámparas, faroles de puerta y cartel de direcciones, mostradores de facturación con báscula y cinta, arcos de seguridad, rayos X, cinta de equipajes, isla de información con el tablero y reloj, cafetería, mesas, máquinas de refrescos, fotomatón, carro de maletas, plantas, jardinera, rincón con sillones, estanterías de la tienda, chocolate gigante, pelota, lata, papelera, postes de cola, timbre, micrófono y botón. El manifiesto guarda `bbox_min`/`bbox_max`, así que cada pieza se coloca por su origen real. `vista_lobby.py` monta el aeropuerto en Blender igual que el juego y renderiza `lobby_*.png` |
| `arte/kit_isla/` | Kit de la isla en Blender (`kit_isla_gen.py`): cinco palmeras (dos rectas, alta, inclinada y joven), platanera, helecho, hojas grandes, flores, hierba, arbusto, rocas (grande, media, pequeña, planas y farallón), charca, conchas, madera de deriva, hoguera, tronco, pila de leña, coco, cangrejo, piezas de radio, estación de radio en un mirador, bengala y su maletín, cajas abiertas, hidroavión, restos (ala, motor, trozo de fuselaje, asientos, maletas), bote, cascada, refugio, cartel, SOS y muelle con pilotes; de ambiente: palmera gigante con columpio, tiki, roca-cangrejo, santuario de botellas con mensaje, gaviotas, espuma de orilla y hierba de duna |
| `arte/roturas/` | Piezas que se rompen (`roturas_gen.py`): corta el casco de `avion_gen.py` en base, puntas de ala, cola y deriva con bordes rasgados, más capó, motor por dentro, agujero del techo, trozo de techo, pollo de goma y pasajero saludando. Si cambia `AvionExterior`, hay que regenerarlas y volver a subirlas (`subir_modelos.py arte/roturas/ids_subida.json …` y luego `roturas_gen.py -- --solo-luau`) |
| `arte/ids_roblox.json` | IDs de los modelos subidos a Roblox |
| `herramientas/` | Scripts: mapa, subida de modelos e imágenes y generación de `src/shared/Visuales.luau` |

## IDs en Roblox

| Qué | ID |
|---|---|
| Experiencia (universo) | `10774639088` |
| Lugar principal | `70554923634533` |
| Grupo dueño | `783757619` |
| Tripulante v5 (cuerpo alto, cara con huesos, guantes) | `79935936187714` |
| Resto de modelos (66: avión, pasajeros, cocodrilo, objetos, kit del interior y kit del aeropuerto) | `arte/ids_roblox.json` |

## Flujo de trabajo por API

1. Generar el mapa: `python3 herramientas/generar_mapa.py`
2. Subir modelos nuevos: `python3 herramientas/subir_modelos.py arte/ids_roblox.json ruta/Modelo.fbx …`
3. Regenerar los visuales: `python3 herramientas/generar_visuales.py`
4. Construir: `rojo build default.project.json -o overbooked.rbxlx`
5. Publicar: `POST https://apis.roblox.com/universes/v1/10774639088/places/70554923634533/versions?versionType=Published` con el archivo `.rbxlx`
6. Probar en un servidor de Roblox: `python3 herramientas/probar.py` ejecuta `herramientas/pruebas/servidor.luau` con la API de ejecución de Luau. Comprueba cómo se importó el tripulante (Humanoid, HumanoidRootPart, huesos de la boca, articulaciones), cuántos modelos de Blender se han colocado, si cargó el casco y la fase de la partida. Necesita el permiso *Luau Execution Sessions*.

## Cara que habla por voz

`BocaVoz.luau` conecta el `AudioDeviceInput` de cada jugador a un `AudioAnalyzer` y da su nivel de voz (0 a 1): del todo a −12 dB y nada por debajo de −46 dB. `Cara.luau` usa ese nivel para mover los huesos de la cara de todos los jugadores a menos de 120 studs: la boca se abre con un muelle que se pasa un poco y rebota, la lengua asoma y se menea, las cejas saltan con cada subida de volumen y los mofletes se inflan. Sin hablar parpadea, tuerce la boca, levanta una ceja, olisquea y a veces saca la lengua. Expresiones: susto (turbulencias fuertes, caída libre, al estrellarse), enfado y luego mareo (ragdoll), grito (cayendo rápido más de medio segundo), alegría (aterrizaje bueno o perfecto) y sorpresa (aterrizaje duro, pájaros). Los ojos saltones (`Ojos.luau`) son piezas del cliente: crecen, se aplastan para parpadear y en el mareo las pupilas dan vueltas. Detalles en `arte/tripulante/README.md`. Hace falta tener la voz activada en la configuración del juego (Comunicación). Rojo ya pone `VoiceChatService.UseAudioApi = Enabled`.

## Pendiente

- **Probar en el servidor por API:** la clave aún no tiene el permiso *Luau Execution Sessions* (escritura), así que no he podido arrancar el juego en un servidor de Roblox. Lo que sí está comprobado: todo el código pasa el analizador de tipos de Luau en modo estricto, dos revisiones de código de Roblox (sus hallazgos están corregidos) y la vista previa en Blender del mapa con todos los modelos colocados.
- **Orientación de los modelos:** comprobado en Studio con los 78 modelos: todos se importan igual y se colocan con `Config.ROTACION_FBX = CFrame.Angles(math.pi / 2, 0, 0)`. Mirar solo la forma de la caja no distingue un modelo de su versión boca abajo, por eso ya no se detecta por modelo.
- **Tripulante:** si el modelo importado no trae `Humanoid` o `HumanoidRootPart`, el juego usa personajes por defecto y lo avisa en la consola del servidor.
- **Sonidos:** ElevenLabs no es accesible desde esta sesión, así que los efectos y la música se generan por código (`arte/sonidos/sonidos_gen.py`) y se suben como audio por la API. Si se habilita ElevenLabs, se pueden sustituir archivo por archivo con el mismo nombre.
- **Del tráiler:** piolet, tractor de equipaje y aduana ya están hechos.
- **Botones de la cabina:** los cinco usan el mismo modelo rojo; se distinguen por la etiqueta de color que tienen encima.
