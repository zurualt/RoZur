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
2. **Embarque (25 s):** suben los pasajeros y se carga la bodega. Entra al avión por la rampa trasera.
3. **Despegue:** alguien se sienta en el asiento izquierdo de la cabina, acelera con **Shift** y, al pasar de 260 km/h, sube con **W**. Si nadie pilota en 45 s, despega el piloto automático.
4. **Vuelo:** mantén el rumbo (el panel dice hacia dónde girar) y la altitud. El piloto automático ayuda, pero se desconecta con los sustos.
5. **Aproximación:** a 140 km del destino el aterrizaje es manual. Hay que llegar a 0 m con menos de 340 km/h, bajando despacio y con las alas rectas.
6. **Resultados:** se cobra por pasajeros entregados (según su satisfacción), carga intacta, entregas aéreas y la calidad del aterrizaje. Se resta por pasajeros perdidos, carga perdida y daños. El dinero se reparte y se guarda.

## Controles

| Acción | Teclado | Mando |
|---|---|---|
| Coger / soltar | Clic | R2 |
| Lanzar | Clic derecho | L2 |
| Usar extintor, llave o agua | F (mantener) | X |
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
| Vuelo | `src/server/Avion.luau` | Simulación a 10 Hz, piloto y automático, motores, combustible, casco, rampa, puertas y botones |
| Pasajeros | `src/server/Pasajeros.luau` | Pedidos 🍔 ☕ 💧 con paciencia, miedo y satisfacción (cada bandeja lleva 3 hamburguesas); salen volando si no llevan cinturón |
| Carga | `src/server/Carga.luau` | Daños por golpes, cajas frágiles, entregas aéreas desde la rampa y el cocodrilo |
| Peligros | `src/server/Peligros.luau` | Turbulencias, pájaros que incendian un motor, fuego que se extiende, agujeros que succionan, caída libre, tormenta y fallo de motor |
| Agarrar | `src/server/Agarre.luau` + `src/client/Agarre.luau` | Física con propiedad de red para quien sostiene; se puede coger a pasajeros y lanzarlos por la puerta |
| Personajes | `src/server/Personajes.luau` + `src/client/Cuerpo.luau` | Tripulante como StarterCharacter, color por jugador, ragdoll, caídas del avión, viento en las alas |
| Cámara | `src/client/Camara.luau` | Primera persona con brazos visibles, balanceo al andar, inclinación con el avión y sacudidas |
| Mundo | `src/client/Mundo.luau` | El avión no se mueve: nubes, campos y pista se mueven a su alrededor en cada cliente |
| Interfaz | `src/client/Interfaz.luau` + `src/shared/Gui.luau` | Interfaz dibujada a mano (Blender): tarjeta de embarque con la ruta y la cuenta atrás, etiqueta de equipaje con el estado del avión, avisos en notas con cinta, pizarra del piloto, burbujas de pedidos, nombres con altavoz, ayuda, tienda y factura de resultados con sello. Sin emojis: todo son iconos dibujados |
| Boca con voz | `src/client/BocaVoz.luau` | La boca del tripulante se abre según el volumen del chat de voz |
| Datos | `src/server/Datos.luau` | Dinero y vuelos en DataStore, con bloqueo de sesión para no pisar datos al cambiar de servidor |
| Piratas | `src/server/Piratas.luau` + `src/client/Piratas.luau` | Aviones pirata que dañan el casco; se derriban desde la torreta del ala izquierda |

| Interacciones | `src/server/Interacciones.luau` | Lo que vuela golpea: pasajeros que se enfadan o salen del asiento, jugadores que caen, cocodrilo aturdido. La comida lanzada al pasajero que la pide cuenta como servida. Café y agua dejan charcos resbaladizos; el agua apaga el fuego; las bandejas se derraman |
| Cabina | `src/server/Cabina.luau` + `src/client/Cabina.luau` | Altillos que se abren con las turbulencias y sueltan bolsos (se guardan soltándolos junto al altillo abierto), asientos para jugadores (sentado no te caes), mascarillas de oxígeno, luces que parpadean y de emergencia, volante, palancas y torreta animados |

Todos los números del juego están en `src/shared/Config.luau`.

| Tractor y carro | `src/server/Vehiculos.luau` + `src/client/Vehiculo.luau` | Tractor conducible que remolca el carro de maletas (E junto a la lanza para enganchar) |
| Piolet | `src/client/Escalada.luau` | Trepar por fuera del fuselaje sobre un casco invisible; en el techo hay viento fuerte en vuelo |
| Aduana | `src/server/Aduana.luau` | Escáner con cinta: revela el contrabando; el contenedor de aduanas da +60 por maleta y cada una que llegue a destino es una multa de 150 |
| Tienda | `src/server/Tienda.luau` + `src/server/Mejoras.luau` | Gorros cosméticos y mejoras del avión con el dinero guardado (DataStore versión 2) |
| Sonido | `src/server/Sonidos.luau` + `src/client/Sonido.luau` | Efectos con posición, bucles (motores, viento, alarma, lluvia, fuego) y música por fase |
| Tutorial | `src/client/Tutorial.luau` | Lista de pasos para los dos primeros vuelos |

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
- **Premios:** al aterrizar se reparten premios (mejor camarero, bombero, mecánico, puntería, artillero, piloto, domador, relaciones públicas y el más torpe).
- **Embarque:** desde el asiento del piloto se puede terminar antes (mantén E).

## Carpetas

| Carpeta | Qué hay |
|---|---|
| `src/` | Código (servidor, cliente y compartido) |
| `mapa/` | Avión y aeropuerto en piezas de Roblox, generados por `herramientas/generar_mapa.py` |
| `arte/` | Modelos de Blender (tripulante, avión, pasajeros, objetos) con sus generadores, FBX, renders y manifiestos |
| `arte/kit_interior/` | Kit del interior del avión: paneles con ventanas, techo con altillos y sus puertas, cocina, baño, mamparas, cabina del piloto, pared de bodega, puertas, torreta en dos piezas, bolso, mascarilla y trozos de cajas |
| `arte/kit_aeropuerto/` | Kit del aeropuerto: terminal, puertas de embarque del lobby (`PuertaSala1-3`), mostradores, bancos, quioscos, marco del tablero, torre de control, hangar, carro, tractor, escalerilla, árboles, arbustos, vallas, conos, luces de pista y manga de viento |
| `arte/interfaz/` | Interfaz dibujada en Blender (`interfaz_gen.py`): 13 paneles 9-slice (papel, pizarra, billete, etiqueta, notas, botón, barras, burbuja, mira, sello) y una hoja de 51 iconos de 128 px. `herramientas/subir_imagenes.py` sube solo lo que cambia y genera `src/shared/ImagenesGui.luau` |
| `arte/ids_roblox.json` | IDs de los modelos subidos a Roblox |
| `herramientas/` | Scripts: mapa, subida de modelos e imágenes y generación de `src/shared/Visuales.luau` |

## IDs en Roblox

| Qué | ID |
|---|---|
| Experiencia (universo) | `10774639088` |
| Lugar principal | `70554923634533` |
| Grupo dueño | `783757619` |
| Tripulante v2 | `87418247604950` |
| Resto de modelos (66: avión, pasajeros, cocodrilo, objetos, kit del interior y kit del aeropuerto) | `arte/ids_roblox.json` |

## Flujo de trabajo por API

1. Generar el mapa: `python3 herramientas/generar_mapa.py`
2. Subir modelos nuevos: `python3 herramientas/subir_modelos.py arte/ids_roblox.json ruta/Modelo.fbx …`
3. Regenerar los visuales: `python3 herramientas/generar_visuales.py`
4. Construir: `rojo build default.project.json -o overbooked.rbxlx`
5. Publicar: `POST https://apis.roblox.com/universes/v1/10774639088/places/70554923634533/versions?versionType=Published` con el archivo `.rbxlx`
6. Probar en un servidor de Roblox: `python3 herramientas/probar.py` ejecuta `herramientas/pruebas/servidor.luau` con la API de ejecución de Luau. Comprueba cómo se importó el tripulante (Humanoid, HumanoidRootPart, huesos de la boca, articulaciones), cuántos modelos de Blender se han colocado, si cargó el casco y la fase de la partida. Necesita el permiso *Luau Execution Sessions*.

## Boca que se abre al hablar por voz

Cada cliente conecta el `AudioDeviceInput` de cada jugador a un `AudioAnalyzer` y mueve los huesos `BocaSup` y `BocaInf`. La boca se abre del todo a −12 dB y queda cerrada por debajo de −46 dB. Hace falta tener la voz activada en la configuración del juego (Comunicación). Rojo ya pone `VoiceChatService.UseAudioApi = Enabled`.

## Pendiente

- **Probar en el servidor por API:** la clave aún no tiene el permiso *Luau Execution Sessions* (escritura), así que no he podido arrancar el juego en un servidor de Roblox. Lo que sí está comprobado: todo el código pasa el analizador de tipos de Luau en modo estricto, dos revisiones de código de Roblox (sus hallazgos están corregidos) y la vista previa en Blender del mapa con todos los modelos colocados.
- **Orientación de los modelos:** comprobado en Studio con los 78 modelos: todos se importan igual y se colocan con `Config.ROTACION_FBX = CFrame.Angles(math.pi / 2, 0, 0)`. Mirar solo la forma de la caja no distingue un modelo de su versión boca abajo, por eso ya no se detecta por modelo.
- **Tripulante:** si el modelo importado no trae `Humanoid` o `HumanoidRootPart`, el juego usa personajes por defecto y lo avisa en la consola del servidor.
- **Sonidos:** ElevenLabs no es accesible desde esta sesión, así que los efectos y la música se generan por código (`arte/sonidos/sonidos_gen.py`) y se suben como audio por la API. Si se habilita ElevenLabs, se pueden sustituir archivo por archivo con el mismo nombre.
- **Del tráiler:** piolet, tractor de equipaje y aduana ya están hechos.
- **Botones de la cabina:** los cinco usan el mismo modelo rojo; se distinguen por la etiqueta de color que tienen encima.
