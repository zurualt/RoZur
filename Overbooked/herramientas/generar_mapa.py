import json
import math
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "mapa")


def rgb(h):
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def rot(rx=0.0, ry=0.0, rz=0.0):
    ax, ay, az = math.radians(rx), math.radians(ry), math.radians(rz)
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)
    mx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    my = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    mz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]

    def mul(a, b):
        return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

    return mul(mul(mx, my), mz)


def part(nombre, tam, pos, color, material="SmoothPlastic", clase="Part", r=None, forma=None,
         transp=0.0, colision=True, atributos=None, hijos=None, extra=None, sombra=True, anclado=True):
    props = {
        "Size": [round(v, 4) for v in tam],
        "CFrame": {"CFrame": {"position": [round(v, 4) for v in pos], "orientation": r or rot()}},
        "Anchored": anclado,
        "Color": rgb(color),
        "Material": material,
        "TopSurface": "Smooth",
        "BottomSurface": "Smooth",
        "CanCollide": colision,
        "CastShadow": sombra,
    }
    if transp:
        props["Transparency"] = transp
    if forma:
        props["Shape"] = forma
    if extra:
        props.update(extra)
    d = {"name": nombre, "className": clase, "properties": props}
    if atributos:
        d["attributes"] = atributos
    if hijos:
        d["children"] = hijos
    return d


def carpeta(nombre, hijos, clase="Folder", atributos=None):
    d = {"name": nombre, "className": clase, "children": hijos}
    if atributos:
        d["attributes"] = atributos
    return d


def luz(rango=18, brillo=1.1, color="FFE9C7"):
    return {"name": "Luz", "className": "PointLight",
            "properties": {"Range": rango, "Brightness": brillo, "Color": rgb(color), "Shadows": False}}


def cartel(texto, cara="Front", color="1B1B21", fondo=None):
    props = {"Face": cara, "SizingMode": "PixelsPerStud", "PixelsPerStud": 40, "LightInfluence": 1}
    etiqueta = {"Text": texto, "TextScaled": True, "BackgroundTransparency": 1 if fondo is None else 0,
                "Size": {"UDim2": [[1, 0], [1, 0]]}, "Font": "FredokaOne", "TextColor3": rgb(color)}
    if fondo:
        etiqueta["BackgroundColor3"] = rgb(fondo)
    return {"name": "Cartel", "className": "SurfaceGui", "properties": props,
            "children": [{"name": "Texto", "className": "TextLabel", "properties": etiqueta}]}


CREMA = "F3EBDD"
CREMA_OSC = "D9D2C5"
TECHO = "FAF6EE"
MOQUETA = "2B5459"
NARANJA = "F27B2B"
TURQUESA = "1FA6A0"
GRIS = "34383F"
METAL = "A9B0B8"
CRISTAL = "8FD3F4"
MADERA = "C98B4E"
BODEGA = "7D858F"
SUELO_Y = 100.0
TECHO_Y = 110.0
FILAS = [-41.5 + 4.5 * i for i in range(8)]
COLUMNAS = {"A": -5.7, "B": -3.5, "C": 3.5, "D": 5.7}
FILA_SALIDA = 4


def estructura():
    p = []
    p.append(part("Suelo", (14, 1, 86), (0, SUELO_Y - 0.5, -21), MOQUETA, "Fabric"))
    p.append(part("Pasillo", (2.2, 0.06, 52), (0, SUELO_Y + 0.03, -26), NARANJA, "Fabric", colision=False))
    p.append(part("Techo", (14, 1, 86), (0, TECHO_Y + 0.5, -21), TECHO))
    for x in (-2.6, 2.6):
        p.append(part("Tira", (0.5, 0.15, 62), (x, TECHO_Y - 0.08, -24), "FFF6DD", "Neon", colision=False, sombra=False))
    for i, z in enumerate((-58, -48, -36, -24, -12, 6, 16)):
        p.append(part("Lampara", (1, 0.2, 1), (0, TECHO_Y - 0.1, z), "FFF6DD", "Neon", colision=False, sombra=False,
                      hijos=[luz(22 if z > -52 else 14, 1.0)]))
    for lado, sx in (("Izq", -1), ("Der", 1)):
        x = sx * 7.5
        p.append(part("ParedCabina" + lado, (1, 10, 12), (sx * 6.0, 105, -58), CREMA))
        p.append(part("ParedCocina" + lado, (1, 10, 8), (x, 105, -48), CREMA))
        for i, z in enumerate(FILAS):
            if i == FILA_SALIDA:
                p.append(part("Dintel" + lado, (1, 3.5, 3.4), (x, 108.25, z), CREMA))
                p.append(part("Pared" + lado, (1, 10, 0.55), (x, 105, z - 1.975), CREMA))
                p.append(part("Pared" + lado, (1, 10, 0.55), (x, 105, z + 1.975), CREMA))
                continue
            p.append(part("Zocalo" + lado, (1, 3.5, 4.5), (x, SUELO_Y + 1.75, z), CREMA_OSC))
            p.append(part("Altillo" + lado, (1, 3.5, 4.5), (x, TECHO_Y - 1.75, z), CREMA))
            hijos = [
                part("Pilar", (1, 3, 1.45), (x, 105, z - 1.525), CREMA),
                part("Pilar", (1, 3, 1.45), (x, 105, z + 1.525), CREMA),
                part("Cristal", (0.3, 2.2, 1.6), (x, 105, z), CRISTAL, "Glass", transp=0.5),
            ]
            p.append(carpeta("Ventana", hijos, "Model", {"Fila": i + 1, "Lado": lado}))
        if lado == "Izq":
            p.append(part("ParedTrasera" + lado, (1, 10, 8), (x, 105, -4), CREMA))
        p.append(part("ParedBodega" + lado, (1, 10, 22), (x, 105, 11), "C9C2B5"))
        p.append(part("Pilastra" + lado, (1, 10, 1), (sx * 6.5, 105, 22.5), "C9C2B5"))
        p.append(part("Relleno" + lado, (1.5, 10, 1), (sx * 6.25, 105, -52), CREMA))
    p.append(part("ParabrisasBajo", (11, 3.5, 1), (0, SUELO_Y + 1.75, -64.5), CREMA))
    p.append(part("Parabrisas", (11, 4, 0.4), (0, 105.5, -64.3), CRISTAL, "Glass", transp=0.55))
    p.append(part("ParabrisasAlto", (11, 2.5, 1), (0, 108.75, -64.5), CREMA))
    p.append(part("Parteluz", (0.4, 4, 0.5), (0, 105.5, -64.2), GRIS))
    for nombre, z, hueco in (("MamparaCabina", -52, 2.0), ("MamparaBodega", 0, 2.5)):
        ancho = 7 - hueco
        for sx in (-1, 1):
            p.append(part(nombre, (ancho, 10, 0.6), (sx * (hueco + ancho / 2), 105, z), CREMA_OSC))
        p.append(part(nombre, (hueco * 2, 2.5, 0.6), (0, 108.75, z), CREMA_OSC))
    p.append(part("Altillos", (3, 2.8, 36), (-5.5, 108.4, -26), CREMA, hijos=None))
    p.append(part("Altillos", (3, 2.8, 36), (5.5, 108.4, -26), CREMA))
    p.append(part("BordeAltillos", (0.2, 0.3, 36), (-3.95, 107.1, -26), NARANJA, colision=False))
    p.append(part("BordeAltillos", (0.2, 0.3, 36), (3.95, 107.1, -26), NARANJA, colision=False))
    return carpeta("Estructura", p)


def asientos():
    p = []
    indice = 0
    for i, z in enumerate(FILAS):
        for col, x in COLUMNAS.items():
            if i == FILA_SALIDA and abs(x) > 5:
                continue
            indice += 1
            p.append(part("Asiento", (2.2, 1.2, 2.4), (x, 101.0, z), TURQUESA, "Fabric",
                          atributos={"Fila": i + 1, "Columna": col, "Indice": indice, "Visual": "Asiento", "Base": SUELO_Y},
                          hijos=[
                              part("Respaldo", (2.2, 2.8, 0.5), (x, 102.8, z + 0.95), TURQUESA, "Fabric"),
                              part("Cabecero", (1.8, 0.6, 0.56), (x, 103.9, z + 0.95), NARANJA, "Fabric", colision=False),
                              part("Base", (1.8, 0.4, 1.8), (x, 100.2, z), GRIS),
                          ]))
    return carpeta("Asientos", p)


def cabina():
    p = []
    for nombre, x in (("AsientoPiloto", -2.6), ("AsientoCopiloto", 2.6)):
        p.append(part(nombre, (2.2, 1.2, 2.2), (x, 101.0, -57.5), GRIS, "Fabric", clase="Seat",
                      atributos={"Visual": "AsientoPiloto", "Base": SUELO_Y},
                      hijos=[part("Respaldo", (2.2, 3.2, 0.5), (x, 103.0, -56.4), GRIS, "Fabric"),
                             part("Raya", (0.5, 3.0, 0.52), (x, 103.0, -56.4), TURQUESA, "Fabric", colision=False)]))
    p.append(part("Cuadro", (10.5, 2.8, 2), (0, 102.8, -62.2), GRIS, atributos={"Visual": "Cuadro"}))
    p.append(part("Visera", (10.5, 0.5, 1.4), (0, 104.4, -62.5), "1B1B21"))
    for i, x in enumerate((-4.2, -3.0, -1.5, 1.5, 3.0, 4.2)):
        colores = ["55D66B", "F5CD3D", "55D66B", "4AB8F0", "F27B2B", "55D66B"]
        p.append(part("Indicador", (0.15, 0.7, 0.7), (x, 103.3, -61.15), colores[i], "Neon", forma="Cylinder",
                      r=rot(0, 90, 0), colision=False, sombra=False))
    p.append(part("Columna", (0.35, 0.35, 1.8), (-2.6, 102.6, -60.4), "1B1B21", atributos={"Visual": "Volante"},
                  hijos=[part("Volante", (1.5, 0.3, 0.3), (-2.6, 103.0, -59.5), "1B1B21")]))
    p.append(part("Gases", (1.2, 1.3, 2.0), (0, 100.65, -59.0), GRIS, atributos={"Visual": "Gases"},
                  hijos=[part("Palanca", (0.2, 0.9, 0.2), (-0.25, 101.7, -59.3), NARANJA),
                         part("Palanca", (0.2, 0.9, 0.2), (0.25, 101.7, -59.3), NARANJA)]))
    botones = [("BotonExtintorMotor", -4.0, "D9443A"), ("BotonAutopiloto", -2.0, "4AB8F0"),
               ("BotonMotores", 0.0, "F5CD3D"), ("BotonCinturones", 2.0, "F27B2B"), ("BotonRampa", 4.0, "1FA6A0")]
    for nombre, x, c in botones:
        p.append(part(nombre, (0.4, 0.9, 0.9), (x, 104.85, -62.0), c, "SmoothPlastic", forma="Cylinder",
                      r=rot(0, 0, 90), atributos={"Visual": "Boton"}))
    return carpeta("Cabina", p)


def cocina():
    p = []
    for sx in (-1, 1):
        p.append(part("Encimera", (3, 3.5, 7.4), (sx * 5.5, 101.75, -48), METAL, "Metal"))
        p.append(part("Armario", (3, 2.6, 7.4), (sx * 5.5, 108.7, -48), CREMA))
    p.append(part("DispensadorHamburguesa", (1.6, 0.9, 1.6), (-5.4, 103.95, -50), "E9A64B",
                  atributos={"Tipo": "Hamburguesa"}, hijos=[cartel("🍔", "Top", fondo="FFF4E0")]))
    p.append(part("DispensadorCafe", (1.4, 1.6, 1.0), (5.6, 104.3, -50), "6B3A22",
                  atributos={"Tipo": "Cafe", "Visual": "Cafetera"}, hijos=[cartel("☕", "Left", fondo="FFF4E0")]))
    p.append(part("DispensadorAgua", (1.8, 1.3, 1.2), (5.4, 104.15, -46), TURQUESA,
                  atributos={"Tipo": "Agua", "Visual": "Nevera"}, hijos=[cartel("💧", "Left", fondo="FFF4E0")]))
    p.append(part("SoporteExtintor", (1.2, 0.3, 1.2), (-6.3, 101.5, -44.6), GRIS, atributos={"Tipo": "Extintor"}))
    p.append(part("SoporteLlave", (1.2, 0.3, 1.2), (6.3, 101.5, -44.6), GRIS, atributos={"Tipo": "Llave"}))
    p.append(part("CartelCocina", (4, 1.2, 0.2), (0, 108.6, -51.6), NARANJA, colision=False,
                  hijos=[cartel("COCINA", "Back", "FFFFFF")]))
    return carpeta("Cocina", p)


def bano_y_puertas():
    p = []
    p.append(part("ParedBano", (0.4, 10, 2.6), (-3, 105, -6.7), CREMA_OSC))
    p.append(part("ParedBano", (0.4, 10, 1.0), (-3, 105, -3.5), CREMA_OSC))
    p.append(part("DintelBano", (0.4, 2.5, 2.4), (-3, 108.75, -4.8), CREMA_OSC))
    p.append(part("FrenteBano", (4, 10, 0.4), (-5, 105, -8.0), CREMA_OSC))
    p.append(part("FondoBano", (4, 10, 0.4), (-5, 105, -3.0), CREMA_OSC))
    p.append(part("Inodoro", (1.4, 1.6, 2.0), (-5.6, 100.8, -6.0), "FFFFFF", atributos={"Visual": "Inodoro"}))
    p.append(part("CartelBano", (1.6, 1.0, 0.1), (-2.75, 107.0, -4.8), "FFFFFF", colision=False, r=rot(0, 90, 0),
                  hijos=[cartel("WC", "Back", "1B1B21")]))
    p.append(part("PuertaAlaIzq", (0.6, 6.5, 3.4), (-7.5, 103.25, FILAS[FILA_SALIDA]), NARANJA,
                  atributos={"Abierta": False, "Puerta": True}))
    p.append(part("PuertaAlaDer", (0.6, 6.5, 3.4), (7.5, 103.25, FILAS[FILA_SALIDA]), NARANJA,
                  atributos={"Abierta": False, "Puerta": True}))
    p.append(part("PuertaSalida", (0.6, 6.5, 3.0), (7.5, 103.25, -5.5), NARANJA,
                  atributos={"Abierta": False, "Puerta": True}))
    p.append(part("ParedSalida", (1, 10, 4.0), (7.5, 105, -2.0), CREMA))
    p.append(part("ParedSalida", (1, 10, 1.0), (7.5, 105, -7.5), CREMA))
    p.append(part("DintelSalida", (1, 3.5, 3.0), (7.5, 108.25, -5.5), CREMA))
    for nombre, z in (("CartelSalida", -5.5),):
        p.append(part(nombre, (0.1, 0.8, 2.2), (6.9, 107.2, z), "1FA650", "Neon", colision=False,
                      hijos=[cartel("SALIDA", "Left", "FFFFFF")]))
    return carpeta("Puertas", p)


def bodega():
    p = []
    p.append(part("SueloBodega", (13.8, 0.1, 22), (0, SUELO_Y + 0.05, 11), BODEGA, "DiamondPlate"))
    for sx in (-1, 1):
        for y in (103.2, 106.2):
            p.append(part("Estante", (2.2, 0.35, 18), (sx * 5.85, y, 11), MADERA, "Wood"))
    p.append(part("ZonaCarga", (8, 5, 15), (0, 103, 12), "FFFFFF", transp=1, colision=False, sombra=False))
    p.append(part("ZonaPasajerosCaidos", (2, 2, 2), (0, 101.5, -26), "FFFFFF", transp=1, colision=False, sombra=False))
    p.append(part("SoporteExtintor", (1.2, 0.3, 1.2), (6.3, 101.5, 2.5), GRIS, atributos={"Tipo": "Extintor"}))
    p.append(part("SoporteLlave", (1.2, 0.3, 1.2), (-6.3, 101.5, 2.5), GRIS, atributos={"Tipo": "Llave"}))
    p.append(part("BotonRampaBodega", (0.4, 0.9, 0.9), (6.8, 103.5, 19.5), TURQUESA, forma="Cylinder",
                  atributos={"Visual": "Boton"}))
    angulo = -90.0
    largo = 9.6
    a = math.radians(angulo)
    centro = (0, SUELO_Y - 0.4 + (-math.sin(a)) * largo / 2, 22.4 + math.cos(a) * largo / 2)
    p.append(part("Rampa", (12, 0.8, largo), centro, "C9C2B5", "DiamondPlate", r=rot(angulo, 0, 0),
                  atributos={"Abierta": False, "Largo": largo}))
    p.append(part("TechoRampa", (14, 0.6, 2), (0, TECHO_Y - 0.3, 23), "C9C2B5"))
    return carpeta("Bodega", p)


def exterior():
    p = []
    for lado, sx in (("Izq", -1), ("Der", 1)):
        p.append(part("Ala" + lado, (31, 1, 12), (sx * 22.5, 98.5, -24), "FFF4E0",
                      atributos={"Ala": True}))
        p.append(part("Borde" + lado, (31, 0.3, 0.6), (sx * 22.5, 99.0, -30.2), NARANJA, colision=False))
        p.append(part("Punta" + lado, (1.2, 2.2, 3), (sx * 38.4, 99.6, -21), NARANJA))
        p.append(part("Soporte" + lado, (0.8, 1.6, 4), (sx * 18, 97.4, -24), GRIS))
        p.append(part("Motor" + lado, (9, 4.4, 4.4), (sx * 18, 95.6, -24), GRIS, "Metal", forma="Cylinder",
                      r=rot(0, 90, 0), atributos={"Motor": lado}))
        p.append(part("Aro" + lado, (0.6, 4.6, 4.6), (sx * 18, 95.6, -28.6), NARANJA, forma="Cylinder",
                      r=rot(0, 90, 0), colision=False))
        p.append(part("Estabilizador" + lado, (11, 0.6, 5), (sx * 7.5, 108.5, 28), "FFF4E0"))
    p.append(part("Deriva", (0.8, 10, 7), (0, 116, 27), TURQUESA))
    p.append(part("Morro", (11, 3.5, 2), (0, 101.75, -65.6), "FFF4E0"))
    tren = []
    for x, z in ((0, -50), (-4.5, -2), (4.5, -2)):
        tren.append(part("Pata", (0.7, 8.4, 0.7), (x, 94.8, z), GRIS, "Metal"))
        tren.append(part("Rueda", (1.2, 2.4, 2.4), (x, 91.2, z), "1B1B21", forma="Cylinder", r=rot(0, 0, 0)))
    p.append(carpeta("Tren", tren))
    return carpeta("Exterior", p)


def marcadores():
    return carpeta("Marcadores", [
        part("SpawnAvion", (4, 0.4, 4), (0, SUELO_Y + 0.2, -47), "FFFFFF", clase="SpawnLocation", transp=1,
             colision=False, extra={"Enabled": False, "Neutral": True, "Duration": 0}),
        part("Centro", (1, 1, 1), (0, 105, -18), "FFFFFF", transp=1, colision=False, sombra=False),
    ])


def avion():
    return {
        "className": "Model",
        "attributes": {"Fase": "Aeropuerto"},
        "children": [estructura(), asientos(), cabina(), cocina(), bano_y_puertas(), bodega(), exterior(),
                     marcadores(), carpeta("Peligros", []), carpeta("Objetos", []), carpeta("Pasajeros", [])],
    }


def aeropuerto():
    p = []
    p.append(part("Cesped", (700, 2, 700), (0, 89, 0), "6BBF59", "Grass"))
    p.append(part("Pista", (34, 0.2, 520), (0, 90.1, -40), "3A3D42", "Asphalt"))
    for z in range(-280, 220, 24):
        p.append(part("Raya", (0.8, 0.05, 10), (0, 90.22, z), "FFFFFF", colision=False))
    p.append(part("Plataforma", (60, 0.4, 70), (52, 90.2, 10), "8A8F96", "Concrete"))
    p.append(part("RampaSuelo", (12, 2.6, 5.2), (0, 91.3, 31.4), "8A8F96", "DiamondPlate", clase="WedgePart",
                  r=rot(0, 180, 0)))
    t = []
    t.append(part("SueloTerminal", (52, 1, 52), (58, 90.5, -20), "E8E2D6", "Marble"))
    t.append(part("TechoTerminal", (54, 1, 54), (58, 104.5, -20), "FFF4E0"))
    t.append(part("FranjaTerminal", (54.2, 1.2, 54.2), (58, 103.6, -20), NARANJA, colision=False))
    t.append(part("ParedFondo", (52, 13, 1), (58, 97.5, -46.5), "FFF4E0"))
    t.append(part("ParedEste", (1, 13, 52), (84.5, 97.5, -20), "FFF4E0"))
    t.append(part("ParedSur", (52, 13, 1), (58, 97.5, 6.5), "FFF4E0"))
    t.append(part("CristalOeste", (0.4, 12, 18), (31.5, 97, -35), CRISTAL, "Glass", transp=0.5))
    t.append(part("CristalOeste", (0.4, 12, 18), (31.5, 97, -2), CRISTAL, "Glass", transp=0.5))
    t.append(part("DintelOeste", (1, 4, 15), (31.5, 102, -18.5), "FFF4E0"))
    for i, z in enumerate((-30, -22, -14)):
        t.append(part("Mostrador", (3, 3.5, 6), (74, 92.75, z), TURQUESA))
    for i, z in enumerate((-36, -10)):
        t.append(part("Banco", (10, 1.2, 2), (48, 91.6, z), NARANJA))
    t.append(part("Tablero", (18, 9, 0.6), (58, 98, -45.8), "1B1B21", atributos={"Tablero": True}))
    t.append(part("Rotulo", (20, 2.4, 0.4), (58, 103.6, -46.0), NARANJA, colision=False,
                  hijos=[cartel("OVERBOOKED!  ·  SALIDAS", "Back", "FFFFFF")]))
    for i, x in enumerate((52, 58, 64)):
        t.append(part("PedestalContrato", (2.4, 3, 2.4), (x, 92.5, -38), GRIS,
                      hijos=[part("BotonContrato", (0.5, 1.6, 1.6), (x, 94.2, -38), [NARANJA, TURQUESA, "F5CD3D"][i],
                                  forma="Cylinder", r=rot(0, 0, 90), atributos={"Contrato": i + 1})]))
    t.append(part("SpawnAeropuerto", (8, 0.4, 8), (62, 91.2, -20), "FFFFFF", clase="SpawnLocation", transp=1,
                  colision=False, extra={"Enabled": True, "Neutral": True, "Duration": 0}))
    p.append(carpeta("Terminal", t))
    for i in range(6):
        p.append(part("Cono", (1, 1.6, 1), (-14 + i * 5.6, 90.9, 36), NARANJA))
    p.append(part("Manga", (1, 6, 1), (-30, 93, 40), "FFFFFF", hijos=[part("Tela", (0.6, 1.4, 3), (-30, 95.6, 41.4), NARANJA, colision=False)]))
    return {"className": "Model", "children": p}


def main():
    os.makedirs(SALIDA, exist_ok=True)
    for nombre, datos in (("Avion", avion()), ("Aeropuerto", aeropuerto())):
        ruta = os.path.join(SALIDA, nombre + ".model.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)

    def contar(d):
        return 1 + sum(contar(h) for h in d.get("children", []))

    print("Avion", contar(avion()), "Aeropuerto", contar(aeropuerto()))


main()
