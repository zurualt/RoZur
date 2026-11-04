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
    if not colision:
        props["CanQuery"] = False
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


def marca(nombre, tam, pos, visual, r=None, hijos=None, base=None, atributos=None):
    a = {"Visual": visual}
    if base is not None:
        a["Base"] = base
    if atributos:
        a.update(atributos)
    return part(nombre, tam, pos, "FFFFFF", r=r, transp=1, colision=False, sombra=False, atributos=a, hijos=hijos)


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
COLUMNAS = {"A": -5.55, "B": -3.35, "C": 3.35, "D": 5.55}
INTERIOR = 6.7
G = 0.3
MURO = INTERIOR + G / 2
FILA_SALIDA = 4


def estructura():
    p = []
    p.append(part("Suelo", (INTERIOR * 2, G, 84.5), (0, SUELO_Y - G / 2, -20.25), MOQUETA, "Fabric"))
    p.append(part("Pasillo", (2.2, 0.06, 37), (0, SUELO_Y + 0.03, -25.75), NARANJA, "Fabric", colision=False))
    p.append(part("Techo", (INTERIOR * 2, G, 74), (0, TECHO_Y + G / 2, -15), TECHO))
    for z in (-48, -4, 6, 16):
        p.append(part("Lampara", (1, 0.2, 1), (0, TECHO_Y - 0.1, z), "F2E6CC", "Neon", colision=False, sombra=False,
                      hijos=[luz(20, 0.8)]))
    for z in FILAS:
        p.append(part("LuzFila", (0.4, 0.1, 0.4), (0, TECHO_Y - 0.4, z), "FFFFFF", transp=1, colision=False, sombra=False,
                      hijos=[luz(16, 0.55)]))
    p.append(part("Lampara", (1, 0.2, 1), (0, 107.9, -57), "F2E6CC", "Neon", colision=False, sombra=False, hijos=[luz(14, 0.8)]))
    for lado, sx in (("Izq", -1), ("Der", 1)):
        x = sx * MURO
        giro = rot(0, 90 * sx, 0)
        p.append(part("ParedCocina" + lado, (G, 10, 8), (x, 105, -48), CREMA))
        for i, z in enumerate(FILAS):
            if i == FILA_SALIDA:
                p.append(marca("PanelSalida", (4.5, 10, 0.7), (sx * 7.05, 105, z), "PanelSalida", r=giro, hijos=[
                    part("Dintel" + lado, (G, 3.5, 4.5), (x, 108.25, z), CREMA),
                    part("Pared" + lado, (G, 6.5, 0.55), (x, 103.25, z - 1.975), CREMA),
                    part("Pared" + lado, (G, 6.5, 0.55), (x, 103.25, z + 1.975), CREMA),
                ]))
                continue
            p.append(marca("PanelVentana", (4.5, 10, 0.7), (sx * 7.05, 105, z), "PanelVentana", r=giro, hijos=[
                part("Zocalo" + lado, (G, 3.9, 4.5), (x, SUELO_Y + 1.95, z), CREMA_OSC),
                part("Altillo" + lado, (G, 3.9, 4.5), (x, TECHO_Y - 1.95, z), CREMA),
                part("Pilar", (G, 2.2, 1.45), (x, 105, z - 1.525), CREMA),
                part("Pilar", (G, 2.2, 1.45), (x, 105, z + 1.525), CREMA),
            ]))
            p.append(carpeta("Ventana", [part("Cristal", (0.15, 2.2, 1.6), (x, 105, z), CRISTAL, "Glass", transp=0.5)],
                             "Model", {"Fila": i + 1, "Lado": lado}))
        p.append(marca("BodegaPared", (22, 10, 0.7), (sx * 7.05, 105, 11), "BodegaPared", r=giro, hijos=[
            part("ParedBodega" + lado, (G, 10, 22), (x, 105, 11), "C9C2B5"),
        ]))
        p.append(part("Pilastra" + lado, (0.35, 10, 1), (sx * 6.35, 105, 22.5), "C9C2B5"))
        p.append(part("Relleno" + lado, (0.9, 10, 1), (sx * 6.25, 105, -52), CREMA))
    p.append(part("ParedTraseraIzq", (G, 10, 8), (-MURO, 105, -4), CREMA))
    p.append(part("ParedSalida", (G, 10, 3.25), (MURO, 105, -1.625), CREMA))
    p.append(part("ParedSalida", (G, 10, 0.25), (MURO, 105, -7.875), CREMA))
    p.append(marca("PanelSalida", (4.5, 10, 0.7), (7.05, 105, -5.5), "PanelSalida", r=rot(0, 90, 0), hijos=[
        part("DintelSalida", (G, 3.5, 4.5), (MURO, 108.25, -5.5), CREMA),
        part("ParedSalida", (G, 6.5, 0.55), (MURO, 103.25, -7.475), CREMA),
        part("ParedSalida", (G, 6.5, 0.55), (MURO, 103.25, -3.525), CREMA),
    ]))
    for nombre, z, hueco, visual in (("MamparaCabina", -52, 2.0, "MamparaCabina"), ("MamparaBodega", 0, 2.5, "MamparaBodega")):
        ancho = INTERIOR - hueco
        hijos = [part(nombre, (ancho, 10, 0.6), (sx * (hueco + ancho / 2), 105, z), CREMA_OSC) for sx in (-1, 1)]
        hijos.append(part(nombre, (hueco * 2, 2.5, 0.6), (0, 108.75, z), CREMA_OSC))
        p.append(marca(visual, (13.4, 10, 0.6), (0, 105, z), visual, hijos=hijos))
    return carpeta("Estructura", p)


def altillos():
    p = []
    for i, z in enumerate(FILAS):
        hijos = []
        for sx in (-1, 1):
            hijos.append(part("Caja", (2.6, 2.8, 4.5), (sx * 5.4, 108.4, z), CREMA))
        p.append(marca("Techo", (13.4, 3.5, 4.5), (0, TECHO_Y - 1.75, z), "Techo", hijos=hijos))
        for lado, sx in (("Izq", -1), ("Der", 1)):
            p.append(part("PuertaAltillo", (4.3, 2.4, 0.15), (sx * 4.025, 108.2, z), CREMA, r=rot(0, 90 * sx, 0),
                          atributos={"Visual": "PuertaAltillo", "Movil": True, "Fila": i + 1, "Lado": lado, "Altillo": True}))
    return carpeta("Altillos", p)


def asientos():
    p = []
    indice = 0
    for i, z in enumerate(FILAS):
        for col, x in COLUMNAS.items():
            if i == FILA_SALIDA and abs(x) > 5:
                continue
            indice += 1
            p.append(part("Asiento", (2.2, 1.2, 2.4), (x, 101.0, z), TURQUESA, "Fabric", clase="Seat",
                          atributos={"Fila": i + 1, "Columna": col, "Indice": indice, "Visual": "Asiento", "Base": SUELO_Y},
                          extra={"Disabled": True},
                          hijos=[
                              part("Respaldo", (2.2, 2.8, 0.5), (x, 102.8, z + 0.95), TURQUESA, "Fabric"),
                              part("Cabecero", (1.8, 0.6, 0.56), (x, 103.9, z + 0.95), NARANJA, "Fabric", colision=False),
                              part("Base", (1.8, 0.4, 1.8), (x, 100.2, z), GRIS),
                          ]))
    return carpeta("Asientos", p)


def cabina():
    p = []
    p.append(marca("CabinaPiloto", (11.6, 8, 10.5), (0, 104, -57.25), "CabinaPiloto", hijos=[
        part("ParedCabinaIzq", (G, 8, 10.5), (-5.65, 104, -57.25), CREMA),
        part("ParedCabinaDer", (G, 8, 10.5), (5.65, 104, -57.25), CREMA),
        part("TechoCabina", (11.6, G, 10.5), (0, 108 + G / 2, -57.25), TECHO),
        part("ParabrisasBajo", (11, 3.5, G), (0, SUELO_Y + 1.75, -62.35), CREMA),
        part("ParabrisasAlto", (11, 0.5, G), (0, 107.75, -62.35), CREMA),
        part("Parteluz", (0.4, 4, 0.4), (0, 105.5, -62.2), GRIS),
    ]))
    p.append(part("Parabrisas", (11, 4, 0.2), (0, 105.5, -62.35), CRISTAL, "Glass", transp=0.55))
    for nombre, x in (("AsientoPiloto", -2.6), ("AsientoCopiloto", 2.6)):
        p.append(part(nombre, (2.2, 1.2, 2.2), (x, 101.0, -57.5), GRIS, "Fabric", clase="Seat",
                      atributos={"Visual": "AsientoPiloto", "Base": SUELO_Y},
                      hijos=[part("Respaldo", (2.2, 3.2, 0.5), (x, 103.0, -56.4), GRIS, "Fabric"),
                             part("Raya", (0.5, 3.0, 0.52), (x, 103.0, -56.4), TURQUESA, "Fabric", colision=False)]))
    p.append(part("Cuadro", (10.5, 2.8, 2), (0, 102.8, -61.2), GRIS, r=rot(0, 180, 0), atributos={"Visual": "Cuadro"}))
    p.append(part("Columna", (0.35, 0.35, 1.8), (-2.6, 102.6, -59.6), "1B1B21", r=rot(0, 180, 0), atributos={"Visual": "Volante"},
                  hijos=[part("Volante", (1.5, 0.3, 0.3), (-2.6, 103.0, -58.8), "1B1B21")]))
    p.append(part("Gases", (1.2, 1.3, 2.0), (0, 100.65, -59.0), GRIS, atributos={"Visual": "Gases"}))
    for x in (-0.15, 0.15):
        p.append(part("Palanca", (0.13, 0.42, 0.17), (x, 101.141, -59.159), NARANJA, colision=False, r=rot(-24, 0, 0),
                      atributos={"Visual": "PalancaGases", "Movil": True}))
    botones = [("BotonExtintorMotor", -4.0, "D9443A"), ("BotonAutopiloto", -2.0, "4AB8F0"),
               ("BotonMotores", 0.0, "F5CD3D"), ("BotonCinturones", 2.0, "F27B2B"), ("BotonRampa", 4.0, "1FA6A0")]
    for nombre, x, c in botones:
        p.append(part(nombre, (0.4, 0.9, 0.9), (x, 104.85, -61.0), c, "SmoothPlastic", forma="Cylinder",
                      r=rot(0, 0, 90), atributos={"Visual": "Boton"}))
    etiquetas = {"BotonExtintorMotor": "EXTINTOR", "BotonAutopiloto": "AUTO", "BotonMotores": "MOTOR",
                 "BotonCinturones": "CINTUR.", "BotonRampa": "RAMPA"}
    for nombre, x, c in botones:
        p.append(part("Etiqueta", (1.5, 0.45, 0.05), (x, 105.75, -61.0), "1B1B21", colision=False,
                      hijos=[cartel(etiquetas[nombre], "Back", c)]))
    return carpeta("Cabina", p)


def cocina():
    p = []
    for sx in (-1, 1):
        p.append(marca("CocinaModulo", (7.4, 10, 2.6), (sx * 5.4, 105, -48), "CocinaModulo", r=rot(0, 90 * sx, 0), hijos=[
            part("Encimera", (2.6, 3.5, 7.4), (sx * 5.4, 101.75, -48), METAL, "Metal"),
            part("Armario", (2.6, 3.6, 7.4), (sx * 5.4, 107.8, -48), CREMA),
        ]))
    p.append(part("DispensadorHamburguesa", (1.6, 0.9, 1.6), (-5.4, 103.95, -50), "E9A64B", r=rot(0, -90, 0),
                  atributos={"Tipo": "Bandeja", "Visual": "Calentador"}, hijos=[cartel("COMIDA", "Front", fondo="FFF4E0")]))
    p.append(part("DispensadorCafe", (1.4, 1.6, 1.0), (5.6, 104.3, -50), "6B3A22", r=rot(0, 90, 0),
                  atributos={"Tipo": "Cafe", "Visual": "Cafetera"}, hijos=[cartel("CAFÉ", "Front", fondo="FFF4E0")]))
    p.append(part("DispensadorAgua", (1.8, 1.3, 1.2), (5.4, 104.15, -46), TURQUESA, r=rot(0, 90, 0),
                  atributos={"Tipo": "Agua", "Visual": "Nevera"}, hijos=[cartel("AGUA", "Front", fondo="FFF4E0")]))
    p.append(part("SoporteExtintor", (1.2, 0.3, 1.2), (-6.0, SUELO_Y + 0.15, -43.4), GRIS, atributos={"Tipo": "Extintor"}))
    p.append(part("SoporteLlave", (1.2, 0.3, 1.2), (6.0, SUELO_Y + 0.15, -43.4), GRIS, atributos={"Tipo": "Llave"}))
    p.append(part("SoporteCarrito", (1.8, 0.1, 2.8), (-2.6, SUELO_Y + 0.05, -45.2), GRIS, transp=1, colision=False,
                  atributos={"Tipo": "Carrito"}))
    p.append(part("CartelCocina", (4, 1.2, 0.2), (0, 108.6, -51.6), NARANJA, colision=False,
                  hijos=[cartel("COCINA", "Back", "FFFFFF")]))
    return carpeta("Cocina", p)


def bano_y_puertas():
    p = []
    p.append(marca("Bano", (5, 10, 3.7), (-4.85, 105, -5.5), "Bano", r=rot(0, -90, 0), hijos=[
        part("ParedBano", (0.4, 10, 1.3), (-3, 105, -7.35), CREMA_OSC),
        part("ParedBano", (0.4, 10, 1.3), (-3, 105, -3.65), CREMA_OSC),
        part("DintelBano", (0.4, 3, 2.4), (-3, 108.5, -5.5), CREMA_OSC),
        part("FrenteBano", (3.7, 10, 0.4), (-4.85, 105, -8.0), CREMA_OSC),
        part("FondoBano", (3.7, 10, 0.4), (-4.85, 105, -3.0), CREMA_OSC),
        part("Inodoro", (1.4, 1.6, 1.4), (-5.9, 100.8, -6.6), "FFFFFF"),
        part("Lavabo", (1.2, 0.4, 1.4), (-6.0, 103.2, -4.0), "FFFFFF"),
    ]))
    p.append(part("CartelBano", (1.6, 1.0, 0.1), (-2.75, 108.4, -5.5), "FFFFFF", colision=False, r=rot(0, 90, 0),
                  hijos=[cartel("WC", "Back", "1B1B21")]))
    p.append(part("PuertaBano", (2.4, 7, 0.15), (-3, 103.5, -5.5), CREMA, r=rot(0, -90, 0),
                  atributos={"Abierta": False, "Puerta": True, "Interior": True, "Visual": "PuertaBano", "Movil": True}))
    for nombre, sx, z in (("PuertaAlaIzq", -1, FILAS[FILA_SALIDA]), ("PuertaAlaDer", 1, FILAS[FILA_SALIDA]), ("PuertaSalida", 1, -5.5)):
        p.append(part(nombre, (3.4, 6.5, G), (sx * MURO, 103.25, z), NARANJA, r=rot(0, 90 * sx, 0),
                      atributos={"Abierta": False, "Puerta": True, "Visual": "PuertaAla", "Movil": True}))
    p.append(part("CartelSalida", (0.1, 0.8, 2.2), (6.6, 107.2, -5.5), "1FA650", "Neon", colision=False,
                  hijos=[cartel("SALIDA", "Left", "FFFFFF")]))
    return carpeta("Puertas", p)


def bodega():
    p = []
    p.append(part("SueloBodega", (INTERIOR * 2, 0.1, 22), (0, SUELO_Y + 0.05, 11), BODEGA, "DiamondPlate"))
    for sx in (-1, 1):
        for y in (103.35, 106.2):
            p.append(part("Estante", (2.2, 0.35, 18), (sx * 5.6, y, 11), MADERA, "Wood"))
    p.append(part("ZonaCarga", (8, 5, 15), (0, 103, 12), "FFFFFF", transp=1, colision=False, sombra=False))
    p.append(part("SoporteExtintor", (1.2, 0.3, 1.2), (6.0, SUELO_Y + 0.15, 1.0), GRIS, atributos={"Tipo": "Extintor"}))
    p.append(part("SoporteLlave", (1.2, 0.3, 1.2), (-6.0, SUELO_Y + 0.15, 1.0), GRIS, atributos={"Tipo": "Llave"}))
    for x in (-6.0, 6.0):
        p.append(part("SoportePiolet", (1.2, 0.3, 1.2), (x, SUELO_Y + 0.15, 20.0), GRIS, atributos={"Tipo": "Piolet"}))
    p.append(part("BotonRampaBodega", (0.4, 0.9, 0.9), (6.5, 103.5, 19.5), TURQUESA, forma="Cylinder"))
    angulo = -90.0
    largo = 9.6
    a = math.radians(angulo)
    centro = (0, SUELO_Y - 0.4 + (-math.sin(a)) * largo / 2, 22.4 + math.cos(a) * largo / 2)
    p.append(part("Rampa", (12, 0.8, largo), centro, "C9C2B5", "DiamondPlate", r=rot(angulo, 0, 0),
                  atributos={"Abierta": False, "Largo": largo}))
    p.append(part("TechoRampa", (INTERIOR * 2, G, 2), (0, TECHO_Y + G / 2, 23), "C9C2B5"))
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
    p.append(marca("BaseTorreta", (3, 1.2, 4), (-24, 99.6, -21.5), "Torreta", base=99.0, hijos=[
        part("PlacaTorreta", (3, 0.6, 3), (-24, 99.3, -21.5), "1B1B21", "Metal"),
    ]))
    p.append(part("Torreta", (1.2, 0.4, 1.0), (-24, 100.0, -20.0), GRIS, "Metal", clase="Seat", transp=1))
    p.append(part("Canones", (3, 2.2, 3.2), (-24, 101.1, -21.5), GRIS, "Metal", colision=False, transp=1,
                  atributos={"Visual": "TorretaCanones", "Movil": True},
                  hijos=[part("Escudo", (3.2, 2.2, 0.4), (-24, 101.4, -23.0), GRIS, "Metal", colision=False),
                         part("Canon", (0.35, 0.35, 3.2), (-24.5, 102.0, -24.4), "1B1B21", "Metal", colision=False),
                         part("Canon", (0.35, 0.35, 3.2), (-23.5, 102.0, -24.4), "1B1B21", "Metal", colision=False)]))
    p.append(part("Morro", (11, 3.5, 2), (0, 101.75, -63.5), "FFF4E0"))
    tren = []
    for x, z in ((0, -50), (-4.5, -2), (4.5, -2)):
        tren.append(part("Pata", (0.7, 8.4, 0.7), (x, 94.8, z), GRIS, "Metal"))
        tren.append(part("Rueda", (1.2, 2.4, 2.4), (x, 91.2, z), "1B1B21", forma="Cylinder", r=rot(0, 0, 0)))
    p.append(carpeta("Tren", tren))
    return carpeta("Exterior", p)


def casco():
    p = []
    radio, cy, z0, z1 = 8.45, 105.0, -48.0, 18.0
    huecos = {1: [(-25.4, -21.6)], -1: [(-25.4, -21.6)]}
    huecos_der = [(-7.4, -3.6)]
    n = 16
    ancho = 2 * radio * math.tan(math.pi / n) + 0.05
    for k in range(-1, 10):
        for lado in (1, -1):
            if lado == -1 and k in (4,):
                continue
            ang = math.radians(k * 22.5)
            if lado == -1:
                ang = math.pi - ang
            x = radio * math.cos(ang)
            y = cy + radio * math.sin(ang)
            giro = math.degrees(ang) - 90
            tramos = [(z0, z1)]
            if k in (-1, 0):
                cortes = list(huecos[lado]) + (huecos_der if lado == 1 else [])
                for a, b in sorted(cortes):
                    nuevos = []
                    for u, w in tramos:
                        if b <= u or a >= w:
                            nuevos.append((u, w))
                        else:
                            if a > u:
                                nuevos.append((u, a))
                            if b < w:
                                nuevos.append((b, w))
                    tramos = nuevos
            for u, w in tramos:
                p.append(part("Casco", (ancho, 0.4, w - u), (x, y, (u + w) / 2), "FFFFFF", r=rot(0, 0, giro), transp=1,
                              sombra=False, atributos={"Escalable": True}))
    return carpeta("Casco", p)


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
        "children": [estructura(), altillos(), asientos(), cabina(), cocina(), bano_y_puertas(), bodega(), exterior(), casco(),
                     marcadores(), carpeta("Peligros", []), carpeta("Objetos", []), carpeta("Pasajeros", [])],
    }


def deco(nombre, visual, tam, x, base, z, giro=0.0, color=GRIS, colision=True, hijos=None, atributos=None,
         material="SmoothPlastic", transp=0.0):
    a = {"Visual": visual, "Base": base}
    if atributos:
        a.update(atributos)
    return part(nombre, tam, (x, base + tam[1] / 2, z), color, material, r=rot(0, giro, 0), colision=colision,
                atributos=a, hijos=hijos, transp=transp)


def vehiculos():
    v = []
    base = 90.4
    cx, cz = 36.0, 34.0
    v.append(part("CarroEquipaje", (7, 1.3, 5), (cx, base + 0.65, cz), "34383F", "Metal",
                  atributos={"Visual": "CarroEquipaje", "Movil": True},
                  hijos=[part("BarandaCarro", (6.2, 0.55, 0.16), (cx, base + 1.58, cz + 2.38), TURQUESA, "Metal"),
                         part("BarandaCarro", (6.2, 0.55, 0.16), (cx, base + 1.58, cz - 2.38), TURQUESA, "Metal"),
                         part("BarandaCarro", (0.16, 0.55, 4.6), (cx + 2.56, base + 1.58, cz), TURQUESA, "Metal")]))
    tx, tz, e = 44.0, 38.0, 1.25
    v.append(part("Tractor", (4 * e, 1.8, 7 * e), (tx, base + 0.9, tz), NARANJA, "SmoothPlastic",
                  atributos={"Visual": "Tractor", "Movil": True, "Escala": e},
                  hijos=[part("AsientoTractor", (1.3 * e, 0.3, 1.0 * e), (tx, base + 1.95 * e - 0.15, tz + 1.675 * e), GRIS,
                              clase="VehicleSeat", transp=1,
                              extra={"MaxSpeed": 0, "Torque": 0, "TurnSpeed": 0, "HeadsUpDisplay": False})]))
    return carpeta("Vehiculos", v)


def aduana():
    a = []
    base = 90.4
    ex, ez = 22.0, 26.0
    hijos = []
    for dz in (-1.65, 1.65):
        hijos.append(part("ParedEscaner", (7, 4.2, 0.7), (ex, base + 2.1, ez + dz), "D9D2C5"))
    hijos.append(part("TechoEscaner", (7, 1.0, 4), (ex, base + 3.7, ez), "D9D2C5"))
    a.append(marca("Escaner", (4, 4.2, 7), (ex, base + 2.1, ez), "Escaner", r=rot(0, 90, 0), base=base, hijos=hijos))
    a.append(part("Cinta", (2.6, 0.2, 11), (ex, base + 0.9, ez), "1B1B21", "Rubber",
                  r=rot(0, 90, 0), atributos={"Velocidad": 7}))
    a.append(part("BaseCinta", (2.6, 0.8, 11), (ex, base + 0.4, ez), GRIS, r=rot(0, 90, 0)))
    a.append(part("Tunel", (7, 2.2, 2.6), (ex, base + 2.1, ez), "FFFFFF", transp=1, colision=False, sombra=False))
    cx, cz = 15.0, 21.5
    paredes = [part("FondoContenedor", (3, 0.2, 3), (cx, base + 0.1, cz), NARANJA)]
    for dx, dz, tx, tz in ((1.45, 0, 0.1, 3), (-1.45, 0, 0.1, 3), (0, 1.45, 3, 0.1), (0, -1.45, 3, 0.1)):
        paredes.append(part("ParedContenedor", (tx, 2, tz), (cx + dx, base + 1, cz + dz), NARANJA))
    a.append(marca("Contenedor", (3, 2, 3), (cx, base + 1, cz), "Contenedor", base=base, hijos=paredes))
    a.append(part("ZonaContenedor", (2.8, 2.4, 2.8), (cx, base + 1.3, cz), "FFFFFF", transp=1, colision=False, sombra=False))
    return carpeta("Aduana", a)


def terminal():
    t = []
    cx, cz, base = 74.0, -20.0, 90.0
    dx = cx - 58.0

    def mundo(lx, lz):
        return cx + lz, cz - lx

    hijos = [
        part("SueloTerminal", (53.6, 0.5, 53.2), (57.8 + dx, base + 0.25, cz), "E8E2D6", "Marble"),
        part("TechoTerminal", (54, 1.8, 54), (cx, base + 14.1, cz), "FFF4E0"),
        part("ParedFondo", (0.6, 15, 53.2), (cx + 26.3, base + 7.5, cz), "FFF4E0"),
        part("ParedNorte", (51.6, 15, 0.6), (58.8 + dx, base + 7.5, cz - 26.3), "FFF4E0"),
        part("ParedSur", (51.6, 15, 0.6), (58.8 + dx, base + 7.5, cz + 26.3), "FFF4E0"),
        part("DintelEntrada", (0.8, 2.7, 15), (cx - 25.0, base + 11.85, cz), TURQUESA),
    ]
    for signo in (-1, 1):
        hijos.append(part("Montante", (0.8, 13.2, 0.7), (cx - 25.0, base + 6.6, cz - signo * 7.85), TURQUESA))
        hijos.append(part("Esquina", (1.0, 13.2, 1.1), (cx - 25.0, base + 6.6, cz - signo * 26.4), "FFF4E0"))
    t.append(marca("Terminal", (54, 15, 54), (cx, base + 7.5, cz), "Terminal", r=rot(0, 90, 0), base=base, hijos=hijos))
    for signo in (-1, 1):
        for a, b in ((8.2, 11.488), (11.788, 15.076), (15.376, 18.664), (18.964, 22.252), (22.552, 25.84)):
            lx = signo * (a + b) / 2
            x, z = mundo(lx, -25.0)
            t.append(part("CristalTerminal", (0.2, 10.8, b - a), (x, base + 6.6, z), CRISTAL, "Glass", transp=0.6))
    x, z = mundo(0, 26.44)
    t.append(marca("MarcoTablero", (18.6, 9.6, 0.8), (x, base + 2.7 + 4.8, z), "MarcoTablero", r=rot(0, 90, 0), base=base + 2.7))
    t.append(part("Tablero", (17.6, 8.8, 0.2), (cx + 25.93, base + 7.5, cz), "1B1B21", r=rot(0, -90, 0), atributos={"Tablero": True}))
    for i, dz in enumerate((-12, 0, 12)):
        sx, sz = 72 + dx, cz + dz
        t.append(deco("PuertaSala", f"PuertaSala{i + 1}", (9.2, 3.47, 10.45), sx + 0.625, base + 0.5, sz, 90, GRIS, colision=False))
        t.append(part("SalaSalida", (0.12, 8.4, 8.4), (sx, base + 0.56, sz), "FFFFFF", forma="Cylinder", r=rot(0, 0, 90),
                      transp=1, colision=False, sombra=False, atributos={"Sala": i + 1}))
        t.append(part("PantallaSala", (1.95, 1.05, 0.04), (sx + 5.15, base + 0.5 + 2.65, sz), "1B1B21", r=rot(0, 90, 0),
                      transp=1, colision=False, sombra=False, atributos={"Sala": i + 1}))
    for x in (46, 54, 62):
        t.append(deco("Mostrador", "Mostrador", (6, 3.5, 3), x + dx, base + 0.5, cz - 23, 180, TURQUESA))
    for x in (52, 62):
        for z in (cz - 14, cz + 14):
            t.append(deco("Banco", "BancoEspera", (10, 2.2, 2), x + dx, base + 0.5, z, -90, NARANJA))
    t.append(deco("Tienda", "Tienda", (8, 5, 4), 66 + dx - 16, base + 0.5, cz + 23.5, 0, TURQUESA))
    for z in (cz - 21, cz - 15, cz + 15, cz + 21):
        t.append(deco("Planta", "Arbusto", (3, 2, 3), 81.5 + dx, base + 0.5, z, 0, "6BBF59", colision=False))
    for x, z in ((45, cz - 13), (45, cz + 13), (70, cz - 13), (70, cz + 13)):
        t.append(part("LuzTerminal", (0.4, 0.1, 0.4), (x + dx, base + 12.3, z), "FFFFFF", transp=1, colision=False, sombra=False,
                      hijos=[luz(34, 0.9)]))
    t.append(part("SpawnAeropuerto", (8, 0.4, 8), (62 + dx, base + 0.7, cz), "FFFFFF", clase="SpawnLocation", transp=1,
                  colision=False, extra={"Enabled": True, "Neutral": True, "Duration": 0}))
    return carpeta("Terminal", t)


def aeropuerto():
    p = []
    p.append(part("Cesped", (700, 2, 700), (0, 89, 0), "6BBF59", "Grass"))
    p.append(part("Pista", (34, 0.2, 520), (0, 90.1, -40), "3A3D42", "Asphalt"))
    for z in range(-280, 220, 24):
        p.append(part("Raya", (0.8, 0.05, 10), (0, 90.22, z), "FFFFFF", colision=False))
    for x in (-15.8, 15.8):
        p.append(part("Borde", (0.5, 0.05, 520), (x, 90.22, -40), "F5CD3D", colision=False))
    p.append(part("Plataforma", (30, 0.4, 110), (32, 90.2, -5), "8A8F96", "Concrete"))
    p.append(part("RampaSuelo", (12, 2.6, 5.2), (0, 91.3, 31.4), "8A8F96", "DiamondPlate", clase="WedgePart",
                  r=rot(0, 180, 0)))
    p.append(vehiculos())
    p.append(aduana())
    p.append(terminal())
    d = []
    d.append(deco("Torre", "TorreControl", (10, 40, 10), 44, 90, -95, 90, "FFF4E0"))
    d.append(deco("Hangar", "Hangar", (50, 22, 40), 72, 90, 64, 90, "1FA6A0"))
    d.append(deco("Escalera", "Escalera", (3, 9, 9), 25, 90.4, -48, 0, TURQUESA, colision=False))
    for i in range(6):
        d.append(deco("Cono", "Cono", (1, 1.6, 1), -14 + i * 5.6, 90.2, 36, 0, NARANJA))
    for x, z in ((26, 2), (28, 9), (20, -30)):
        d.append(deco("Cono", "Cono", (1, 1.6, 1), x, 90.4, z, 0, NARANJA))
    d.append(deco("Manga", "Manga", (1.2, 7, 4), -30, 90, 40, 0, "FFFFFF", colision=False))
    arboles = [(47, -58), (50, 16), (108, -56), (108, 14), (-40, -60), (-46, 8), (-38, 72), (36, 100), (96, 100),
               (-52, -130), (40, -140), (-60, 130), (116, -20), (118, 40), (-70, -20)]
    for x, z in arboles:
        d.append(deco("Arbol", "Arbol", (1.2, 9, 1.2), x, 90, z, (x * 37 + z) % 360, "8A5A33"))
    for x, z in ((45.5, -44), (45.5, -36), (45.5, -4), (45.5, 4), (104, -30), (104, -10)):
        d.append(deco("Arbusto", "Arbusto", (3, 2, 3), x, 90, z, (x + z * 13) % 360, "6BBF59", colision=False))
    for x in (-62, 132):
        for i in range(22):
            d.append(deco("Valla", "Valla", (8, 2.4, 0.3), x, 90, -88 + i * 8, 90, "A9B0B8"))
    for x in (-17.5, 17.5):
        for z in range(-280, 221, 25):
            d.append(deco("LuzPista", "LuzPista", (0.4, 0.6, 0.4), x, 90, z, 0, "F5CD3D", colision=False))
    p.append(carpeta("Decorado", d))
    return {"className": "Model", "children": p}


def punto(tipo, x, y, z):
    return part("Spot", (1, 1, 1), (x, y, z), "FFFFFF", transp=1, colision=False, sombra=False, atributos={"Spot": tipo})


def isla():
    cx, base, cz = -140.0, 90.2, -40.0
    p = []
    p.append(part("Agua", (2400, 0.4, 2400), (cx, 89.0, cz), "2FB3C4", "Glass", transp=0.3, colision=False, sombra=False))
    p.append(part("FondoMar", (2400, 1, 2400), (cx, 86.1, cz), "D9B877", "Sand"))
    p.append(part("ArenaPaso", (1.8, 500, 500), (cx, 87.7, cz), "D9B877", "Sand", forma="Cylinder", r=rot(0, 0, 90), transp=1))
    p.append(part("Arena", (2, 450, 450), (cx, 89.2, cz), "F2D9A0", "Sand", forma="Cylinder", r=rot(0, 0, 90), transp=1))
    p.append(part("RampaSuelo", (12, 2.6, 5.2), (0, 91.3, 31.4), "8A8F96", "DiamondPlate", clase="WedgePart", r=rot(0, 180, 0)))
    p.append(part("CubiertaMuelle", (30, 0.6, 8), (108, 89.9, -70), "6E4A2B", "WoodPlanks", transp=1))
    d = [deco("Terreno", "IslaTerreno", (520, 8.1, 520), cx, base - 8.1, cz, 0, "F2D9A0", colision=False, transp=1)]
    d.append(deco("Hoguera", "Hoguera", (6, 3, 6), -250, base, 0, 0, "6E4A2B", atributos={"Zona": "Hoguera"}))
    d.append(deco("EstacionRadio", "EstacionRadio", (6, 4, 4), 58, base, -10, 90, "9C6B3E", atributos={"Zona": "Radio"}))
    d.append(deco("Muelle", "Muelle", (8, 3, 30), 108, 87.2, -70, 90, "6E4A2B", colision=False))
    d.append(deco("Sos", "SenalSOS", (24, 0.6, 9), -80, base, -210, 8, "9AA0A6", colision=False))
    d.append(deco("RestosAla", "RestosAla", (26, 3, 10), -72, base, 72, 25, "FFF4E0"))
    d.append(deco("RestosMotor", "RestosMotor", (6, 6, 6), 54, base - 1, 60, 40, "9AA0A6"))
    cajones = ((70, 40), (-200, 120), (-300, -60), (20, -150))
    for i, (x, z) in enumerate(cajones):
        d.append(deco("Cajon", "Cajon", (3, 3, 3), x, base, z, i * 37, "9C6B3E"))
    palmas = ((-60, -120), (-120, -150), (-200, -170), (-280, -120), (-320, -20), (-300, 80), (-230, 140), (-150, 160),
              (-60, 150), (60, 120), (75, -90), (-180, 40), (-20, -200), (-250, -200), (-90, 20), (-330, 150))
    for i, (x, z) in enumerate(palmas):
        alto = 22 if i % 2 == 0 else 18
        ancho = 12 if i % 2 == 0 else 10
        d.append(deco("Palmera", f"Palmera{1 + i % 2}", (ancho, alto, ancho), x, base, z, (i * 53) % 360, "6DBE45", colision=False))
        d.append(part("TroncoPalmera", (alto * 0.62, 1.6, 1.6), (x, base + alto * 0.31, z), "9C6B3E", "Wood", forma="Cylinder",
                      r=rot(0, 0, 90), transp=1))
        d.append(punto("coco", x + 2.2, base + 0.8, z + 1.6))
        d.append(punto("coco", x - 1.8, base + 0.8, z - 2.0))
    for x, z, g in ((-330, -110, 20), (-60, -232, 70), (-262, 150, 140), (40, -40, 200)):
        d.append(deco("Roca", "RocaGrande", (14, 9, 12), x, base - 0.6, z, g, "9AA0A6"))
    for i, (x, z) in enumerate(((-100, -60), (-220, -40), (-170, -230), (10, 100), (-280, 30), (-40, 60), (30, -120), (-350, 50))):
        d.append(deco("Piedra", "RocaPequena", (5, 3, 4), x, base - 0.3, z, i * 61, "9AA0A6"))
    for i, (x, z) in enumerate(((-70, -100), (-210, -150), (-300, -100), (-310, 100), (-160, 140), (50, 100), (-10, -180),
                                (-200, 60), (-120, -10), (-260, 120), (70, -60), (-340, 0))):
        d.append(deco("Arbusto", "ArbustoTropical", (5, 4, 5), x, base, z, i * 47, "6DBE45", colision=False))
    for x, z in ((72, 44), (-200, 125), (-296, -56), (22, -146), (-325, -100), (-55, -222)):
        d.append(punto("radio", x, base + 1.4, z))
    for x, z in ((-118, -144), (-276, -114), (-148, 154), (58, 114), (-18, -194), (-226, 134), (-176, 46)):
        d.append(punto("tronco", x, base + 1, z))
    for x, z in ((80, -120), (-30, -250), (-330, 60), (-280, -200), (40, 150), (-120, 180)):
        d.append(punto("cangrejo", x, base + 0.6, z))
    d.append(punto("bengala", 64, base + 1, -24))
    d.append(part("PuntoRescate", (1, 1, 1), (150, 89.2, -46), "FFFFFF", transp=1, colision=False, sombra=False,
                  atributos={"Zona": "Rescate"}))
    p.append(carpeta("Decorado", d))
    return {"className": "Model", "children": p}


def main():
    os.makedirs(SALIDA, exist_ok=True)
    for nombre, datos in (("Avion", avion()), ("Aeropuerto", aeropuerto()), ("Isla", isla())):
        ruta = os.path.join(SALIDA, nombre + ".model.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)

    def contar(d):
        return 1 + sum(contar(h) for h in d.get("children", []))

    print("Avion", contar(avion()), "Aeropuerto", contar(aeropuerto()))


main()
