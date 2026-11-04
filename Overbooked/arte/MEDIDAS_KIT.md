# Kit de escenario de Overbooked!

Convenciones para todas las piezas:
- 1 unidad de Blender = 1 stud. Z arriba. El FRENTE (la cara que ve el jugador desde el pasillo o desde fuera) mira a -Y.
- Origen en el centro de la base de la caja. Transformaciones aplicadas.
- Una sola malla por pieza, un solo material con paleta de 64×64 (UV en el centro de cada casilla, interpolación Closest).
- Exportación FBX igual que `arte/props/props_gen.py`.
- Las medidas de cada pieza son su caja exacta: X × Y × Z.
- Los huecos (ventanas, puertas) se cortan de verdad: el cristal y las puertas son piezas aparte.

## Interior del avión (`arte/kit_interior`)

| Pieza | X × Y × Z | Notas |
|---|---|---|
| PanelVentana | 4,5 × 0,7 × 10 | Pared lateral de una fila. Hueco de ventana redondeado de 1,6 × 2,2 centrado en X = 0, Z = 5. Zócalo más oscuro hasta Z = 3,5; la parte alta (Z 6,5–10) se curva hacia el techo. Marco de ventana blanco con visera. |
| PanelSalida | 4,5 × 0,7 × 10 | Igual, con hueco de puerta de 3,4 × 6,5 desde Z = 0 y un cartel verde de salida (sin texto) encima. |
| Techo | 13,4 × 4,5 × 3,5 | Módulo de techo de una fila (X a lo ancho de la cabina, Y a lo largo). Altillos a ambos lados: 2,6 de ancho desde la pared, de Z = 0,3 a 3,1, con puerta hacia el pasillo, asa y filo naranja. Panel central con tira de luz, toberas de aire y señal de cinturones (sin texto). |
| CocinaModulo | 7,4 × 2,6 × 10 | Cocina contra una pared (frente = pasillo). Encimera de metal plana y libre a Z = 3,5; debajo, hornos, cajones y hueco de carrito; encima, salpicadero y armarios de Z 6 a 9,6. |
| MamparaCabina | 13,4 × 0,6 × 10 | Mampara con puerta centrada de 4 × 7,5. Marco, cortina recogida a un lado y placa con el logo de la aerolínea (sin texto) en ambas caras. |
| MamparaBodega | 13,4 × 0,6 × 10 | Igual con puerta de 5 × 7,5. Cara -Y crema (cabina), cara +Y chapa metálica (bodega). |
| Bano | 5 × 3,7 × 10 | Baño. Hueco de puerta de 2,4 × 7 centrado en el frente (-Y). Dentro: inodoro, lavabo con espejo. Fuera crema, dentro blanco. Señal de baño (figura, sin texto). |
| CabinaPiloto | 11,6 × 10,5 × 8 | Forro interior de la cabina del piloto: paredes laterales con ventanitas, techo con panel de interruptores. En el extremo -Y, marco del parabrisas: hueco de 11 × 4 entre Z = 3,5 y 7,5 con poste central. Por dentro vacío (cuadro y asientos van aparte). |
| PuertaAla | 3,4 × 0,3 × 6,5 | Puerta de salida sobre el ala: ventanita, asa roja, filo naranja. |
| PuertaSalida | 3,0 × 0,3 × 6,5 | Igual que PuertaAla, más estrecha. |
| PuertaBano | 2,4 × 0,15 × 7 | Hoja de puerta crema con asa e indicador de ocupado. |
| BodegaPared | 22 × 0,7 × 10 | Pared de la bodega: costillas metálicas cada 2,2, redes de carga en la mitad de arriba, raíles de anclaje. |
| Torreta | 3 × 4 × 3,2 | Torreta del ala: base redonda, aro giratorio, escudo y dos cañones apuntando a -Y, cajas de munición; el asiento queda en +Y. |
| Mascarilla | 0,4 × 0,4 × 1,4 | Mascarilla de oxígeno amarilla con tubo. |
| Astilla | 0,8 × 0,3 × 0,2 | Trozo de madera para cajas rotas. |
| Esquirla | 0,5 × 0,1 × 0,4 | Trozo de cristal (color cristal de la paleta) para cajas frágiles rotas. |

## Aeropuerto (`arte/kit_aeropuerto`)

| Pieza | X × Y × Z | Notas |
|---|---|---|
| Terminal | 54 × 54 × 15 | Edificio. Frente (-Y) = fachada de cristal: solo marcos y montantes (el cristal va aparte), con entrada centrada de 15 × 10 y marquesina. Las otras tres paredes macizas crema. Tejado con alero y franja naranja. Suelo interior de baldosas. Pared del fondo (+Y) con hueco para el tablero de salidas. |
| Mostrador | 6 × 3 × 3,5 | Mostrador de facturación turquesa con cinta de equipaje y pantalla. |
| BancoEspera | 10 × 2 × 2,2 | Fila de 5 asientos naranjas sobre una viga de metal. |
| Kiosko | 2,4 × 2,4 × 3 | Pedestal de contrato con pantalla inclinada arriba. Deja libre un círculo de 1,6 en la parte superior para el botón. |
| MarcoTablero | 18,6 × 0,8 × 9,6 | Marco hueco del tablero de salidas (borde de 0,3 y fondo). |
| TorreControl | 10 × 10 × 40 | Torre de control con cabina acristalada arriba. |
| CarroEquipaje | 7 × 5 × 1,9 | Carro de equipaje: plataforma arriba a Z = 1,3, barandillas, ruedas y lanza. |
| Tractor | 4 × 7 × 3 | Tractor de remolque de aviones. |
| Escalera | 3 × 9 × 9 | Escalerilla móvil de embarque (decorado). |
| Arbol | 6 × 6 × 9 | Árbol estilizado de copa redonda. |
| Arbusto | 3 × 3 × 2 | Arbusto. |
| Valla | 8 × 0,3 × 2,4 | Tramo de valla. |
| LuzPista | 0,4 × 0,4 × 0,6 | Luz de borde de pista. |
| Cono | 1 × 1 × 1,6 | Cono naranja con franja blanca. |
| Manga | 1,2 × 4 × 7 | Manga de viento en su mástil. |
| Hangar | 50 × 40 × 22 | Hangar con puerta grande (decorado). |
