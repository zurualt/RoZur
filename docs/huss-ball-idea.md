# Huss Ball: idea de juego (Huss Valley + Blade Ball)

Fecha: 7 de octubre de 2026. Es una idea para decidir si la hacemos, todavía no hay código.

## Resumen en 30 segundos

- **La frase del juego:** "En vez de una bola, te persigue un bicho disfrazado que viene jadeando. Dale un chanclazo en el momento justo y sale disparado hacia otro jugador, más rápido y más grande. Si te pilla, te han hussado."
- **De Blade Ball** coge lo que funciona: algo que te persigue, un botón de parry con timing, cada parry lo acelera y gana el último que queda vivo.
- **De Huss Valley** coge la gracia del meme: huir corriendo de un personaje disfrazado absurdo, con el jadeo "huss, huss, huss" de fondo.
- **Lo que lo hace único:** la "bola" es un personaje que corre, crece y jadea cada vez más fuerte. Se entiende en un vídeo de 3 segundos sin explicar nada.
- **Todos los números son [Propuesta]** míos para empezar a probar.

---

## 1. De dónde sale cada parte

No he podido abrir la página de Roblox de ninguno de los dos juegos (las webs están bloqueadas desde aquí). Lo de abajo sale de resúmenes del buscador. [Probable]

**Huss Valley (el meme).** Empezó en TikTok e Instagram a principios de julio de 2026. Son vídeos de gente huyendo de personajes disfrazados en un sitio caótico, muchos con clips del creador Daniel LaBelle corriendo. "Huss" imita el sonido de alguien jadeando mientras corre. Luego salieron los "hussers" que "van hussin". (https://knowyourmeme.com/memes/huss-valley)

**Huss Valley / Escape Huss Valley (los juegos de Roblox).** Salieron en agosto de 2026. En "Escape Huss Valley" un pueblo tranquilo se convierte en una persecución: personajes como Spider-Man o el Grinch persiguen a todos y tienes que escapar o esconderte hasta que acabe la ronda. Con monedas compras mejoras de velocidad, objetos y emotes. (https://pcgamesn.com/escape-huss-valley-codes, https://www.thespike.gg/roblox/game-codes/huss-valley-codes)

**Blade Ball.** Es un "balón prisionero con espadas": una bola teledirigida va a por un jugador, la devuelves con un parry y cada vez va más rápido. Gana el último en pie. Tiene habilidades, skins de espada y efectos de remate. En 2026 sigue entre los 10 juegos más jugados de Roblox, con unos 15.000 jugadores a la vez. (https://profitable.app/roblox/games/blade-ball, https://boostmatch.gg/blog/other-games/articles/most-popular-roblox-games-2026)

**Ojo con el momento:** el meme ya tiene 3 meses. Si queremos aprovecharlo hay que sacar una versión jugable rápido. La parte de Blade Ball no caduca, así que el juego no depende solo del meme.

---

## 2. Cómo se juega una ronda

1. **Lobby:** de 6 a 12 jugadores en un pueblo pequeño (el "valle"). Empieza la cuenta atrás.
2. **Sale el Husser:** un personaje disfrazado aparece entre la niebla y empieza a correr hacia un jugador al azar. Se oye su jadeo.
3. **Si eres el objetivo:** tu personaje brilla en rojo, los bordes de la pantalla se ponen rojos y el jadeo se oye cada vez más fuerte.
4. **Parry (el chanclazo):** pulsas el botón cuando lo tienes cerca. Le das con la chancla y sale disparado hacia el jugador al que estás mirando con la cámara.
5. **Cada parry:** el Husser va más rápido, crece un poco y jadea más fuerte. En pantalla sale la velocidad en km/h.
6. **Si fallas:** te placa, sales volando como un muñeco de trapo y aparece "¡HUSSADO!". Quedas eliminado.
7. **Final:** cuando quedan 2, duelo 1v1 a velocidades ridículas. El último parry se ve a cámara lenta. El ganador se lleva las monedas.

### Qué lo diferencia

| | Blade Ball | Huss Valley | Huss Ball |
|---|---|---|---|
| Lo que te persigue | Una bola | Personajes disfrazados (a veces de marcas con copyright) | Un personaje disfrazado **inventado por nosotros** que corre como una bola de Blade Ball |
| Cómo te salvas | Parry con espada | Correr o esconderte | Parry con chancla, y también correr (con aguante) |
| Lo que escala | La velocidad | Nada fijo | Velocidad, tamaño y volumen del jadeo, todo a la vez |
| Para TikTok | Clips de velocidad | El meme | Las dos cosas, y se entiende sin texto |

---

## 3. Las reglas con números [Propuesta]

Todo irá en un ModuleScript `Reglas` como en Catch It, para cambiarlo sin tocar el código.

**El Husser**
- Velocidad inicial: 30 studs/s (tú corres a 16 andando y 24 con sprint).
- Cada parry: +8 % de velocidad. Con 20 parries va a unos 140 studs/s.
- En pantalla se enseña en km/h (1 stud = 28 cm, así que 30 studs/s ≈ 30 km/h). Las cifras de 3 dígitos son las que se comparten.
- Cada parry crece un 5 %, hasta 2,5 veces su tamaño.
- No usa el Humanoid normal para moverse: el servidor lo mueve en línea recta hacia el objetivo, girando un poco, como la bola de Blade Ball. Así es rápido y fiable. Usa la animación de correr que ya tenemos (`animations/correr`).

**El parry**
- Vale si el Husser va a llegar en menos de 0,45 s (se calcula con el tiempo y no con la distancia, porque así sigue siendo justo a cualquier velocidad).
- El servidor da un pequeño margen extra según tu ping, para que no te pille por lag.
- Si pulsas y no le das, no puedes volver a pulsar en 0,6 s (para que no se pueda spamear el botón).
- Nuevo objetivo: el jugador más cerca del centro de tu cámara, dentro de un cono de 60°. Si no hay nadie, uno al azar (pero nunca tú).

**El aguante (lo que trae de Huss Valley)**
- Barra de 100. Correr con sprint gasta 20 por segundo y se recupera 15 por segundo.
- Si llega a 0: 2 segundos a velocidad 10, tu personaje jadea en voz alta y todos lo oyen.
- Cada parry bueno te devuelve 25. Así se premia jugar bien y no solo huir.

---

## 4. Pensado para TikTok

- **Se entiende en 3 segundos:** un bicho disfrazado corre hacia ti, le das un chanclazo y sale volando hacia otro.
- **Números grandes en pantalla:** velocidad en km/h y combo (x12) bien visibles, para que salgan en los clips.
- **El sonido es la mitad del meme:** grabad vosotros el jadeo (es fácil y gracioso). No uséis audios de los vídeos del meme, porque en Roblox solo puedes subir audio que sea tuyo.
- **Cámara lenta en el último parry** de la partida, para que cada final sea un clip.
- **Muñeco de trapo exagerado** al ser hussado.
- **Vídeos para subir mientras lo hacemos (formato devlog):**
  1. "He juntado Huss Valley con Blade Ball" (el Husser corriendo y el primer chanclazo).
  2. "¿Hasta qué velocidad aguanta?" (1v1 hasta 500 km/h).
  3. "Mi amigo después de ser hussado" (el muñeco de trapo).
  4. Enseñar disfraces nuevos de Husser y que la gente vote el siguiente en comentarios.

---

## 5. Cosas que NO hay que hacer

- **No usar personajes con copyright** (Spider-Man, el Grinch, etc.). Roblox los puede borrar y te pueden denunciar. Nuestros Hussers son inventados: el Plátano, la Abuela Turbo, el Bebé Gigante, la Mascota del Súper...
- **No llamar al juego "Huss Valley"**, porque ya hay juegos con ese nombre. "Huss" es una palabra del meme y se puede usar.
- **No usar la cara ni el nombre de Daniel LaBelle** ni de ninguna persona real.
- **No vender cosas que den ventaja.** Todo lo de pago es estético, como en Blade Ball.

---

## 6. Qué hacemos primero

**Versión 1 (lo mínimo para publicar y grabar clips):**
1. Un mapa pequeño (lo haces tú en Blender o con bloques en Studio).
2. Un Husser (un disfraz) con la animación de correr.
3. Parry, cambio de objetivo, aceleración y crecimiento.
4. Eliminación con muñeco de trapo y "¡HUSSADO!".
5. Gana el último. Contador de km/h en pantalla.
6. Jadeo que sube de volumen.

**Versión 2 (cuando la 1 funcione):**
- Barra de aguante.
- Escondites de un solo uso (por ejemplo, retretes portátiles): si te metes cuando vas a por ti, el Husser pierde tu rastro y va a por otro.
- Un segundo Husser a los 40 s de ronda, para más caos.
- Los eliminados votan el disfraz del siguiente Husser.
- Monedas ("gotas de sudor" 💦) y tienda: chanclas nuevas (sartén, baguette, pez, escoba), efectos de parry y emotes de victoria.

**Cómo lo montamos:** igual que Catch It. Un proyecto Rojo nuevo en una carpeta `HussBall`, yo hago el código en Luau y tú los mapas, los modelos de los Hussers y las animaciones.

---

## 7. Preguntas para ti

1. ¿Te gusta el nombre **Huss Ball**, o prefieres otro?
2. ¿La chancla como arma de parry, o prefieres otra cosa (espada, sartén, capote)?
3. ¿Lo hacemos después de Catch It o a la vez?
4. ¿Monto ya el proyecto Rojo y empiezo con la versión 1?
