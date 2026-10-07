# Huss Ball: idea de juego (Huss Valley + Blade Ball)

Fecha: 7 de octubre de 2026. Es una idea para decidir si la hacemos, todavía no hay código.

## Resumen en 30 segundos

- **La frase del juego:** "Cruza el campo sin que te pillen. Si un infectado se tira a por ti, dale un parry en el momento justo y sale volando como una bola de Blade Ball, tirando a los demás como bolos."
- **De Huss Valley** coge la base: todos en una línea, los que pillan en el medio, hay que cruzar al otro lado y, si te pillan, te infectas y pillas con ellos. Gana el último que queda.
- **De Blade Ball** coge el parry con timing, apuntar hacia dónde sale lo que devuelves y que todo va cada vez más rápido.
- **Lo que lo hace único:** el infectado al que le haces parry se convierte en la "bola". Si apuntas bien, tiras a varios infectados de golpe (un "strike" humano). En Huss Valley solo puedes huir. Aquí también te puedes defender, pero tienes que acertar el momento.
- **Todos los números son [Propuesta]** míos para empezar a probar.

---

## 1. De dónde sale cada parte

**Huss Valley (el juego).** Según me has contado: un campo con los jugadores en una línea y uno que pilla en el medio. Hay que cruzar al otro lado sin que te pillen. Si te pillan te infectas y pillas con los demás, hasta que no queda nadie en el campo. Es como el juego del patio "bulldog" (o "tiburones y pececitos").

Hay otro juego que se llama "Escape Huss Valley" y es distinto: ahí te persiguen personajes disfrazados por un pueblo. No es al que nos referimos. [Probable] (https://pcgamesn.com/escape-huss-valley-codes)

**El meme.** Empezó en TikTok e Instagram a principios de julio de 2026: vídeos de gente huyendo de personajes disfrazados. "Huss" imita el sonido de alguien jadeando mientras corre. [Probable] (https://knowyourmeme.com/memes/huss-valley)

**Blade Ball.** Es un "balón prisionero con espadas": una bola teledirigida va a por un jugador, la devuelves con un parry y cada vez va más rápido. Gana el último en pie. En 2026 sigue entre los 10 juegos más jugados de Roblox, con unos 15.000 jugadores a la vez. [Probable] (https://profitable.app/roblox/games/blade-ball, https://boostmatch.gg/blog/other-games/articles/most-popular-roblox-games-2026)

**Ojo con el momento:** el meme ya tiene 3 meses y Huss Valley es nuevo. Si queremos aprovechar la ola hay que sacar una versión jugable rápido.

---

## 2. Cómo se juega una partida

1. **Salida:** de 8 a 16 jugadores en la línea de un extremo del campo. Uno al azar empieza infectado en el medio (dos si sois más de 12).
2. **Cruce:** suena el silbato y todos tienen 12 s para llegar a la zona segura del otro lado. Los infectados no pueden entrar en las zonas seguras.
3. **Pillar:** si un infectado te toca, te infectas y en el siguiente cruce estás en el medio con ellos.
4. **Placaje:** los infectados tienen un botón para tirarse en plancha hacia delante. Llegan más lejos, pero si fallan se quedan un momento en el suelo.
5. **Parry:** si eres corredor y pulsas el botón justo cuando un infectado te toca o se tira a por ti, no te pilla. Sale disparado hacia donde miras con la cámara.
6. **Bolos humanos:** el infectado que sale disparado tira al suelo a los infectados con los que choca. Si tira a 3 o más, sale "¡STRIKE!".
7. **Si no llegas:** quien no esté en una zona segura cuando se acaba el tiempo se infecta (así nadie se queda quieto esperando).
8. **Cada cruce** los infectados van un poco más rápido, como la bola de Blade Ball.
9. **Final:** cuando queda un solo corredor, tiene que hacer un último cruce él solo contra todos. Si llega, sale "CRUCE IMPOSIBLE" a cámara lenta y gana el doble de premio. Si lo pillan, gana igual, pero sin el extra.

### Qué lo diferencia

| | Huss Valley | Blade Ball | Huss Ball |
|---|---|---|---|
| Cómo te salvas | Correr y esquivar | Parry a la bola | Correr, esquivar y hacer parry a los infectados |
| Lo que devuelves | Nada | La bola, hacia quien apuntas | Al infectado, como si fuera una bola |
| Lo que escala | Cada vez hay más infectados | La bola va más rápido | Las dos cosas |
| Momento estrella | Cruzar en el último segundo | Duelo final a toda velocidad | El último corredor contra todos, tirándolos como bolos |

---

## 3. Las reglas con números [Propuesta]

Todo irá en un ModuleScript `Reglas` como en Catch It, para cambiarlo sin tocar el código.

**El campo**
- 140 studs de largo y 70 de ancho, con una zona segura de 12 studs en cada extremo.
- Casi sin obstáculos en la versión 1, para que el parry se vea bien.

**Velocidades**
- Corredores: 20 studs/s.
- Infectados: 18 studs/s en el primer cruce y +1 en cada cruce, hasta 24. Al principio el número de infectados es el peligro; al final, la velocidad.

**Placaje de los infectados**
- Se lanzan 16 studs hacia delante en 0,35 s.
- Recarga de 3 s. Si fallan, se quedan 0,8 s en el suelo.

**Parry de los corredores**
- Al pulsar, tienes 0,3 s en los que cualquier infectado que te toque o se tire a por ti sale despedido.
- Recarga: 1,5 s si le das a alguien y 2,5 s si fallas (para que no se pueda spamear el botón).
- Con la recarga no puedes parar a todos. Cuando hay muchos infectados también hay que esquivar.
- El servidor da un pequeño margen extra según tu ping, para que no te pillen por lag.

**El infectado que sale volando**
- Sale a 80 studs/s durante 0,5 s, hacia donde apunta tu cámara.
- Él se queda 2 s en el suelo. Los infectados con los que choca, 1,5 s.

**El tiempo**
- 12 s por cruce y 4 s de descanso en la zona segura antes del siguiente.

---

## 4. Pensado para TikTok

- **Se entiende en 3 segundos:** un campo, todos cruzando y una horda en el medio. No hace falta explicar nada.
- **El clip estrella:** el último corredor contra 15 infectados, haciéndoles parry uno tras otro y tirándolos como bolos.
- **Textos grandes en pantalla:** "¡PARRY!", "¡STRIKE x4!", "CRUCE IMPOSIBLE" y el número de infectados contra corredores.
- **Cámara lenta** en el parry que salva al último corredor.
- **Muñeco de trapo exagerado** cuando un infectado sale volando.
- **El jadeo "huss":** grabadlo vosotros para cuando alguien corre al límite. En Roblox solo puedes subir audio que sea tuyo.
- **Vídeos para subir mientras lo hacemos (formato devlog):**
  1. "He juntado Huss Valley con Blade Ball" (el primer parry que manda a un infectado volando).
  2. "1 contra 15" (el cruce final).
  3. "STRIKE humano" (un parry que tira a 4 o 5).
  4. Enseñar las armas de parry nuevas y que la gente vote la siguiente en comentarios.

---

## 5. Cosas que NO hay que hacer

- **No llamar al juego "Huss Valley"** ni copiar su mapa o su interfaz. Cruzar el campo es un juego de patio y no es de nadie, pero el nombre y el aspecto sí son suyos. "Huss" es una palabra del meme y se puede usar.
- **No usar personajes con copyright** (Spider-Man, el Grinch, etc.) para los disfraces de los infectados.
- **No usar la cara ni el nombre de personas reales** (por ejemplo, Daniel LaBelle, que sale en muchos vídeos del meme).
- **No vender cosas que den ventaja.** Todo lo de pago es estético, como en Blade Ball.

---

## 6. Qué hacemos primero

**Versión 1 (lo mínimo para publicar y grabar clips):**
1. Un campo con dos zonas seguras (bloques en Studio sirven para empezar).
2. Salida, cruces con tiempo, infección al tocar y fin de partida.
3. Placaje de los infectados.
4. Parry con recarga y el infectado saliendo volando hacia donde apuntas.
5. Bolos humanos y "¡STRIKE!".
6. Textos grandes, contador de infectados contra corredores y cámara lenta en el cruce final.

**Versión 2 (cuando la 1 funcione):**
- Monedas y tienda: armas de parry (chancla, sartén, baguette, pez, escoba), efectos de parry, disfraces de infectado y emotes de victoria.
- Más campos (con obstáculos, de noche, en la nieve).
- Algún objeto en el campo, por ejemplo uno que te dé un parry extra.
- Clasificación de "cruces imposibles".

**Cómo lo montamos:** igual que Catch It. Un proyecto Rojo nuevo en una carpeta `HussBall`, yo hago el código en Luau y tú los mapas, los modelos y las animaciones. Catch It también es de pillar, así que la forma de detectar los toques y la de las rondas nos sirven para los dos juegos.

---

## 7. Preguntas para ti

1. ¿Lo he entendido bien? ¿En Huss Valley hay algo más (habilidades, objetos, un tiempo para cruzar)?
2. ¿Te gusta lo de que el infectado salga volando como la bola, o prefieres que haya una bola de verdad en el campo?
3. ¿Te gusta el nombre **Huss Ball**, o prefieres otro?
4. ¿Lo hacemos después de Catch It o a la vez? ¿Monto ya el proyecto Rojo y empiezo con la versión 1?
