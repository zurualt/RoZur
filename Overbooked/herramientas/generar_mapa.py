import json
import math
import os
import random

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
    giro = rot(0, 180, 0)
    p.append(marca("CabinaPiloto", (11.6, 8, 10.2), (0, 104, -57.4), "CabinaForro", r=giro, base=SUELO_Y, hijos=[
        part("ParedCabinaIzq", (G, 8, 10.2), (-5.65, 104, -57.4), CREMA),
        part("ParedCabinaDer", (G, 8, 10.2), (5.65, 104, -57.4), CREMA),
        part("TechoCabina", (11.6, G, 10.2), (0, 108 + G / 2, -57.4), TECHO),
        part("ParabrisasBajo", (11, 3.5, G), (0, SUELO_Y + 1.75, -62.35), CREMA),
        part("ParabrisasAlto", (11, 0.5, G), (0, 107.75, -62.35), CREMA),
        part("Parteluz", (0.36, 3.78, 0.31), (0, 105.61, -62.045), GRIS),
    ]))
    p.append(part("Parabrisas", (11, 4, 0.2), (0, 105.5, -62.35), CRISTAL, "Glass", transp=0.55))
    for sx in (-1, 1):
        for alto, ancho, y, z in ((1.6, 2.1, 105.2, -60.4), (1.4, 1.5, 105.25, -58.15)):
            p.append(part("CristalCabina", (0.04, alto, ancho), (sx * 5.48, y, z), CRISTAL, "Glass", transp=0.5, colision=False))
    for nombre, x in (("AsientoPiloto", -2.6), ("AsientoCopiloto", 2.6)):
        p.append(part(nombre, (2.2, 1.2, 2.2), (x, 101.0, -57.5), GRIS, "Fabric", clase="Seat",
                      atributos={"Visual": "AsientoPiloto", "Base": SUELO_Y},
                      hijos=[part("Respaldo", (2.2, 3.0, 0.5), (x, 103.1, -56.4), GRIS, "Fabric")]))
    p.append(marca("Cuadro", (10.9, 4.149, 1.873), (0, SUELO_Y + 2.0745, -61.2436), "CabinaCuadro", r=giro, base=SUELO_Y, hijos=[
        part("CuadroBajo", (10.9, 2.75, 1.17), (0, 101.375, -61.585), GRIS),
        part("CuadroAlto", (10.9, 0.8, 1.37), (0, 103.15, -61.485), GRIS),
    ]))
    p.append(part("Columna", (0.3, 0.3, 1.2), (-2.6, 102.2, -60.1668), "1B1B21", r=giro,
                  atributos={"Visual": "CabinaVolante", "Base": 101.9319},
                  hijos=[part("Volante", (1.36, 0.3, 0.26), (-2.6, 102.05, -59.41), "1B1B21")]))
    p.append(marca("Gases", (1.8, 1.688, 2.88), (0, SUELO_Y + 0.844, -59.4999), "CabinaGases", r=giro, base=SUELO_Y, hijos=[
        part("Pedestal", (1.6, 1.24, 2.2), (0, 100.62, -59.3), GRIS),
    ]))
    for x in (-0.17, 0.17):
        p.append(part("Palanca", (0.165, 0.502, 0.125), (x, 101.8523, -59.8812), NARANJA, colision=False, r=rot(-24, 0, 0),
                      atributos={"Visual": "CabinaPalanca", "Movil": True}))
    botones = [("BotonExtintorMotor", "BotonExtintor", -2.3, "D9443A"), ("BotonAutopiloto", "BotonAuto", -1.15, "4AB8F0"),
               ("BotonMotores", "BotonMotor", 0.0, "F5CD3D"), ("BotonCinturones", "BotonCinturon", 1.15, "F27B2B"),
               ("BotonRampa", "BotonRampa", 2.3, "1FA6A0")]
    for nombre, visual, x, c in botones:
        p.append(part(nombre, (0.4, 0.2, 0.4), (x, 103.4331, -60.3097), c, "SmoothPlastic", r=rot(math.degrees(math.atan(4)), 0, 0),
                      atributos={"Visual": visual, "Movil": True}))
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
    return carpeta("Puertas", p)


def bodega():
    p = []
    p.append(part("SueloBodega", (INTERIOR * 2, 0.1, 22), (0, SUELO_Y + 0.05, 11), BODEGA, "DiamondPlate"))
    for sx in (-1, 1):
        p.append(part("CornisaBodega", (0.9, 0.6, 22), (sx * 6.95, TECHO_Y - 0.15, 11), "C9C2B5", colision=False))
        p.append(part("ZocaloBodega", (0.5, 0.45, 22), (sx * 6.85, SUELO_Y + 0.22, 11), BODEGA, "Metal", colision=False))
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
    huecos = {1: [(-25.55, -21.45)], -1: [(-25.55, -21.45)]}
    huecos_der = [(-7.55, -3.45)]
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


ISLA_CELDA = 4
ISLA_X0, ISLA_Z0 = -296, -360
ISLA_NX, ISLA_NZ = 140, 132
ISLA_Y0 = 64
MAR = 89.0
FONDO = 71.0
SUELO_AVION = 90.2
OCEANO = 2048
ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
MATERIALES_ISLA = ["Sand", "Salt", "Grass", "LeafyGrass", "Ground", "Rock", "Slate"]
AVION_RECT = (-40.0, 40.0, -68.0, 36.0)
CIMA = (-78.0, -158.0)
ESTANQUE = (-28.0, -196.0)
LAGUNA = (-168.0, -50.0)
CAMPAMENTO = (146.0, -74.0)
SURCO = ((0.0, 128.0), (0.0, 40.0))
COSTA = [(95, 66), (55, 76), (15, 80), (-25, 78), (-65, 72), (-100, 70), (-130, 82), (-158, 86), (-178, 68), (-174, 42),
         (-196, 18), (-214, -18), (-222, -60), (-214, -100), (-204, -140), (-196, -185), (-172, -228), (-136, -262),
         (-88, -286), (-36, -296), (14, -290), (60, -270), (102, -240), (134, -200), (156, -156), (170, -112),
         (176, -70), (172, -28), (160, 12), (138, 44), (118, 60)]
ACANTILADOS = [(-92, -290, 80), (-20, -305, 70), (42, -285, 55), (-196, -196, 48), (122, -226, 40)]
SENDAS = [
    [(-8, -74), (-20, -98), (-36, -120), (-52, -138), (-66, -150)],
    [(-36, -120), (-30, -150), (-27, -178)],
    [(132, -92), (98, -122), (50, -146), (0, -160), (-60, -160)],
    [(44, -46), (78, -60), (116, -72)],
]
COLINAS = [(CIMA[0], CIMA[1], 29.0, 42.0, 12.0), (-150, -210, 13.0, 34.0, 0.0), (98, -176, 7.0, 28.0, 0.0), (-30, -252, 8.0, 40.0, 0.0)]
ROCAS_TERRENO = [(-166, 72, 11, 4.5), (-150, 90, 7, 2.5), (-184, 50, 8, 3.5), (150, -168, 9, 5.0), (-104, -122, 9, 6.0),
                 (-118, -200, 8, 5.0), (162, 30, 7, 3.0), (-206, -110, 8, 4.0), (60, -262, 9, 4.0)]
TAM_ISLA = {
    "RocaGrande": (14.408, 9.411, 11.625), "RocaPequena": (5.202, 3.005, 4.322), "ArbustoTropical": (5.03, 2.99, 5.055),
    "Hoguera": (5.88, 3.066, 5.845), "EstacionRadio": (6.059, 3.75, 2.381), "RestosAla": (27.074, 3.707, 9.6),
    "RestosMotor": (5.706, 5.699, 6.327), "Cajon": (3.477, 3.0, 3.477), "SenalSOS": (22.961, 0.55, 8.852), "Muelle": (7.79, 3.3, 30.64),
    "Palmera1": (11.53, 24.729, 12.093), "Palmera2": (11.576, 20.141, 11.924), "Palmera3": (13.386, 28.699, 12.798),
    "PalmeraInclinada": (10.785, 20.806, 16.331), "PalmeraJoven": (8.934, 9.473, 8.193), "Platanera": (9.432, 7.089, 9.408),
    "Helecho": (4.618, 1.588, 4.657), "HojasGrandes": (6.83, 2.974, 6.77), "Flores": (2.321, 2.12, 2.459), "Hierba": (1.818, 1.618, 1.993),
    "MaderaDeriva": (9.217, 1.595, 2.614), "Conchas": (2.645, 0.543, 2.191), "Charca": (10.027, 1.15, 7.84), "RocaMedia": (7.99, 4.418, 5.012),
    "Acantilado": (13.012, 15.5, 11.539), "RocasPlanas": (9.748, 1.07, 6.698), "AsientoRoto": (3.093, 2.966, 4.93),
    "MaletaAbierta": (3.2, 1.245, 5.473), "MaletaCerrada": (2.44, 1.072, 3.61), "TrozoFuselaje": (9.342, 6.647, 7.563),
    "CajaAbierta": (3.96, 2.766, 2.812), "CajaBengala": (2.4, 2.505, 2.657), "Bote": (10.9, 2.382, 7.518), "Cascada": (12.557, 15.533, 9.266),
    "Mirador": (12.65, 9.57, 15.712), "Cartel": (5.434, 6.28, 0.959), "Refugio": (9.771, 5.157, 7.147), "PilaLena": (4.318, 2.42, 2.754),
}
INCLINADA_BASE = 7.53


def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def mezcla(a, b, t):
    return a + (b - a) * t


def _hash(ix, iz, semilla):
    n = (ix * 374761393 + iz * 668265263 + semilla * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def ruido(x, z, escala, semilla):
    fx, fz = x / escala, z / escala
    ix, iz = math.floor(fx), math.floor(fz)
    tx, tz = fx - ix, fz - iz
    tx, tz = tx * tx * (3 - 2 * tx), tz * tz * (3 - 2 * tz)
    a, b = _hash(ix, iz, semilla), _hash(ix + 1, iz, semilla)
    c, d = _hash(ix, iz + 1, semilla), _hash(ix + 1, iz + 1, semilla)
    ab = a + (b - a) * tx
    return (ab + (c + (d - c) * tx - ab) * tz) * 2 - 1


def fbm(x, z, escala, semilla, octavas=3):
    s, amp, tot = 0.0, 1.0, 0.0
    for o in range(octavas):
        s += amp * ruido(x, z, escala, semilla + o * 17)
        tot += amp
        amp *= 0.5
        escala *= 0.5
    return s / tot


def catmull_2d(puntos, pasos):
    n = len(puntos)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = puntos[i - 1], puntos[i], puntos[(i + 1) % n], puntos[(i + 2) % n]
        for k in range(pasos):
            t = k / pasos
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    return out


def dist_seg(px, pz, ax, az, bx, bz):
    dx, dz = bx - ax, bz - az
    t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz)))
    return math.hypot(ax + dx * t - px, az + dz * t - pz), t


def dist_linea(px, pz, linea):
    return min(dist_seg(px, pz, *a, *b)[0] for a, b in zip(linea, linea[1:]))


def dist_costa(px, pz, segs):
    dmin = 1e18
    dentro = False
    for ax, az, bx, bz in segs:
        if (az > pz) != (bz > pz) and px < ax + (pz - az) * (bx - ax) / (bz - az):
            dentro = not dentro
        dx, dz = bx - ax, bz - az
        t = ((px - ax) * dx + (pz - az) * dz) / (dx * dx + dz * dz)
        t = 0.0 if t < 0 else 1.0 if t > 1 else t
        ex, ez = ax + dx * t - px, az + dz * t - pz
        d = ex * ex + ez * ez
        if d < dmin:
            dmin = d
    d = math.sqrt(dmin)
    return d if dentro else -d


def dist_rect(x, z, r):
    dx = max(r[0] - x, 0.0, x - r[1])
    dz = max(r[2] - z, 0.0, z - r[3])
    return math.hypot(dx, dz)


def acantilado(x, z):
    return max(ss(r, r * 0.45, math.hypot(x - cx, z - cz)) for cx, cz, r in ACANTILADOS)


def ancho_playa(x, z, c):
    return max(16.0, min(56.0, 36.0 + 16.0 * fbm(x, z, 110, 5))) * (1 - c)


class Terreno:
    def __init__(self):
        pts = catmull_2d(COSTA, 5)
        segs = [(a[0], a[1], b[0], b[1]) for a, b in zip(pts, pts[1:] + pts[:1])]
        n = ISLA_NX * ISLA_NZ
        self.s = [0.0] * n
        self.h = [0.0] * n
        self.m = [0] * n
        self.w = [0] * n
        self.niveles = [MAR]
        for iz in range(ISLA_NZ):
            for ix in range(ISLA_NX):
                x, z = self.centro(ix, iz)
                s = dist_costa(x, z, segs) + 7.0 * fbm(x, z, 70, 3)
                self.s[iz * ISLA_NX + ix] = s
        nivel_estanque = self.nivel(99.0)
        nivel_arroyo = self.nivel(111.2)
        for iz in range(ISLA_NZ):
            for ix in range(ISLA_NX):
                i = iz * ISLA_NX + ix
                x, z = self.centro(ix, iz)
                h, m, w = self.columna(x, z, self.s[i], nivel_estanque, nivel_arroyo)
                self.h[i], self.m[i], self.w[i] = h, m, w
        self.rocas_por_pendiente()

    def nivel(self, y):
        self.niveles.append(y)
        return len(self.niveles) - 1

    def centro(self, ix, iz):
        return ISLA_X0 + (ix + 0.5) * ISLA_CELDA, ISLA_Z0 + (iz + 0.5) * ISLA_CELDA

    def columna(self, x, z, s, nivel_estanque, nivel_arroyo):
        c = acantilado(x, z)
        W = ancho_playa(x, z, c)
        mat = "Sand"
        agua = 0
        if s < 0:
            d = -s
            h = MAR + 0.25 - (0.3 + 3.2 * ss(0, 40, d) + 14.6 * ss(30, 92, d))
        else:
            if s < W:
                hb = MAR + 0.25 + 0.9 * (s / max(W, 1)) + 1.85 * ss(0.55 * W, W, s)
                hb += 1.1 * ss(0.5 * W, 0.85 * W, s) * (1 - ss(0.85 * W, 1.15 * W, s)) * (0.6 + 0.5 * fbm(x, z, 24, 9))
            else:
                hb = 92.0 + 3.0 * ss(W, W + 30, s) + 1.8 * fbm(x, z, 46, 7) * ss(W, W + 22, s)
            hc = MAR + 12 * ss(0, 9, s) + 4 * ss(9, 40, s) + 1.5 * fbm(x, z, 30, 13)
            h = mezcla(hb, max(hb, hc), c)
            interior = ss(W - 2, W + 10, s)
            for cx, cz, A, sig, meseta in COLINAS:
                r = max(0.0, math.hypot(x - cx, z - cz) - meseta)
                h += A * math.exp(-r * r / (2 * sig * sig)) * max(interior, c)
            if s > W + 3 or (c > 0.5 and s > 6):
                mat = "LeafyGrass" if fbm(x, z, 38, 21) > 0.18 else "Grass"
        e = math.hypot((x - LAGUNA[0]) / 44.0, (z - LAGUNA[1]) / 31.0)
        canal, _ = dist_seg(x, z, LAGUNA[0], LAGUNA[1], -236.0, -60.0)
        hondo = max(1 - ss(0.5, 1.08, e), 1 - ss(5.0, 10.0, canal))
        if hondo > 0:
            fondo = 86.2 + 2.0 * ss(0, 0.6, e) + 0.6 * fbm(x, z, 12, 31)
            h = mezcla(h, min(h, fondo), hondo)
            if math.hypot(x + 160, z + 44) < 9:
                h = max(h, 89.9 - 0.12 * math.hypot(x + 160, z + 44) ** 1.4)
            if mat in ("Grass", "LeafyGrass") and hondo > 0.3:
                mat = "Sand"
        for cx, cz, r, alto in ROCAS_TERRENO:
            dd = math.hypot(x - cx, z - cz) / r
            if dd < 1.25:
                cima = MAR + 0.5 + alto * (1 - min(dd, 1.0) ** 2) ** 0.7 + 1.2 * fbm(x, z, 6, 41)
                if dd < 1.0 and cima > h:
                    h = max(h, cima)
                    mat = "Rock"
        ex, ez = ESTANQUE
        dx, dz = CIMA[0] - ex, CIMA[1] - ez
        L = math.hypot(dx, dz)
        ux, uz = dx / L, dz / L
        t = (x - ex) * ux + (z - ez) * uz
        q = abs(-(x - ex) * uz + (z - ez) * ux)
        r_est = math.hypot(x - ex, z - ez)
        if q < 16 and 11 < t < 36:
            muro = 99.0 + 13.2 * ss(12.5, 15.5, t) * (1 - ss(11, 16, q))
            if muro > h:
                h = muro
            if t < 17 and q < 13:
                mat = "Rock"
        if q < 3.2 and 15.5 < t < 34:
            h = min(h, 110.2 + 0.03 * (t - 16))
            mat = "Rock"
            agua = nivel_arroyo
        if r_est < 17:
            fondo = 96.0 + 3.6 * ss(8, 15, r_est)
            h = min(h, fondo) if r_est < 14 else mezcla(min(h, fondo), h, ss(14, 17, r_est))
            if r_est < 14:
                agua = nivel_estanque
            mat = "Rock" if 11 < r_est < 16 else ("Sand" if r_est <= 11 else mat)
        if s > -4:
            for linea in SENDAS:
                d = dist_linea(x, z, linea)
                if d < 6:
                    h -= 0.35 * (1 - ss(2, 6, d))
                    if d < 3.4 and mat in ("Grass", "LeafyGrass"):
                        mat = "Ground"
        cx, cz = CAMPAMENTO
        dc = math.hypot(x - cx, z - cz)
        if dc < 24:
            h = mezcla(h, 90.9, 1 - ss(12, 24, dc))
            if dc < 15:
                mat = "Sand"
        sx, sz = CIMA
        dcima = math.hypot(x - sx, z - sz)
        if dcima < 16:
            h = mezcla(h, 121.0, 1 - ss(10, 16, dcima))
        da = dist_rect(x, z, AVION_RECT) + 8 * fbm(x, z, 30, 63) * ss(0, 8, dist_rect(x, z, AVION_RECT))
        if da < 26:
            h = mezcla(h, SUELO_AVION, 1 - ss(0, 26, da))
        claro = math.hypot(x / 62.0, (z + 12) / (78.0 if z > -12 else 70.0)) + 0.2 * fbm(x, z, 34, 61) + 0.08 * fbm(x, z, 11, 67)
        if claro < 1.0 and mat not in ("Rock", "Ground"):
            mat = "Sand"
        (ax, az), (bx, bz) = SURCO
        ds, ts = dist_seg(x, z, ax, az, bx, bz)
        if ds < 13:
            fin = ss(0.0, 0.12, ts) * ss(0.0, 0.08, 1 - ts)
            surco = (-1.5 * (1 - ss(3.5, 6.5, ds)) + 1.0 * ss(4.5, 7.0, ds) * (1 - ss(9.0, 13.0, ds))) * (0.4 + 0.6 * fin)
            h += surco * (1.0 if z < 84 else 0.6)
            if ds < 9.5 and h > MAR - 0.2:
                mat = "Ground"
        if mat == "Sand" and -2.5 < s < 3.0 + 1.5 * fbm(x, z, 20, 51) and agua == 0 and hondo < 0.4:
            mat = "Salt"
        if hondo > 0.3 and abs(h - MAR) < 0.7:
            mat = "Salt"
        if mat == "Sand" and h < MAR - 7:
            mat = "Slate"
        return max(h, FONDO), MATERIALES_ISLA.index(mat), agua

    def rocas_por_pendiente(self):
        roca = MATERIALES_ISLA.index("Rock")
        nuevos = list(self.m)
        for iz in range(1, ISLA_NZ - 1):
            for ix in range(1, ISLA_NX - 1):
                i = iz * ISLA_NX + ix
                if self.h[i] < MAR + 1.5:
                    continue
                g = max(abs(self.h[i + 1] - self.h[i - 1]), abs(self.h[i + ISLA_NX] - self.h[i - ISLA_NX])) / (2 * ISLA_CELDA)
                if g > 0.85:
                    nuevos[i] = roca
        self.m = nuevos

    def indice(self, x, z):
        fx = (x - ISLA_X0) / ISLA_CELDA - 0.5
        fz = (z - ISLA_Z0) / ISLA_CELDA - 0.5
        ix = max(0, min(ISLA_NX - 2, int(math.floor(fx))))
        iz = max(0, min(ISLA_NZ - 2, int(math.floor(fz))))
        return ix, iz, min(1.0, max(0.0, fx - ix)), min(1.0, max(0.0, fz - iz))

    def interp(self, campo, x, z):
        ix, iz, tx, tz = self.indice(x, z)
        i = iz * ISLA_NX + ix
        a, b, c, d = campo[i], campo[i + 1], campo[i + ISLA_NX], campo[i + ISLA_NX + 1]
        return mezcla(mezcla(a, b, tx), mezcla(c, d, tx), tz)

    def altura(self, x, z):
        return self.interp(self.h, x, z)

    def costa(self, x, z):
        return self.interp(self.s, x, z)

    def suelo(self, x, z, r=0.0):
        if r <= 0:
            return self.altura(x, z)
        return min([self.altura(x, z)] + [self.altura(x + r * math.cos(a), z + r * math.sin(a)) for a in (0.0, 1.57, 3.14, 4.71)])

    def material(self, x, z):
        ix, iz, tx, tz = self.indice(x, z)
        return MATERIALES_ISLA[self.m[(iz + round(tz)) * ISLA_NX + ix + round(tx)]]

    def mojado(self, x, z):
        ix, iz, tx, tz = self.indice(x, z)
        return self.w[(iz + round(tz)) * ISLA_NX + ix + round(tx)] != 0 or self.altura(x, z) < MAR + 0.35

    def hacia_mar(self, x, z):
        gx = self.costa(x + 3, z) - self.costa(x - 3, z)
        gz = self.costa(x, z + 3) - self.costa(x, z - 3)
        n = math.hypot(gx, gz) or 1.0
        return -gx / n, -gz / n

    def codificar(self):
        out = []
        for i in range(ISLA_NX * ISLA_NZ):
            v = max(0, min(4095, int(round((self.h[i] - ISLA_Y0) * 32))))
            out.append(ALFABETO[v >> 6] + ALFABETO[v & 63] + ALFABETO[self.m[i]] + ALFABETO[self.w[i]])
        return "".join(out)


def giro_hacia(dx, dz):
    return math.degrees(math.atan2(-dx, -dz))


class Dispersor:
    def __init__(self, t, semilla=7):
        self.t = t
        self.rnd = random.Random(semilla)
        self.ocupado = []
        self.lista = []
        self.cuenta = {}
        self.palmeras = []

    def libre(self, x, z, r):
        if dist_rect(x, z, AVION_RECT) < 6 + r:
            return False
        for linea in SENDAS:
            if dist_linea(x, z, linea) < 3.6 + r * 0.6:
                return False
        if dist_seg(x, z, *SURCO[0], *SURCO[1])[0] < 8 + r * 0.5:
            return False
        if math.hypot(x - CAMPAMENTO[0], z - CAMPAMENTO[1]) < 16 + r:
            return False
        if math.hypot(x - CIMA[0], z - CIMA[1]) < 12 + r:
            return False
        if 150 < x < 230 and abs(z + 74) < 8 + r:
            return False
        for ox, oz, orr in self.ocupado:
            if (x - ox) ** 2 + (z - oz) ** 2 < (r + orr) ** 2:
                return False
        return True

    def poner(self, visual, x, z, giro, escala=1.0, nombre=None, hundir=0.15, radio=None, colision=False, atributos=None,
              hijos=None, base=None):
        tam = [v * escala for v in TAM_ISLA[visual]]
        if radio is not None:
            self.ocupado.append((x, z, radio))
        y = base if base is not None else self.t.suelo(x, z, min(tam[0], tam[2]) * 0.3) - hundir * escala
        self.lista.append(deco(nombre or visual, visual, tuple(tam), x, y, z, giro % 360, "FFFFFF", colision=colision,
                              hijos=hijos, atributos=atributos, transp=1))
        self.cuenta[visual] = self.cuenta.get(visual, 0) + 1
        return y, tam

    def palmera(self, visual, x, z, giro, escala, cocos=False):
        y = self.t.suelo(x, z, 1.0) - 0.4 * escala
        if visual == "PalmeraInclinada":
            fx, fz = -math.sin(math.radians(giro)), -math.cos(math.radians(giro))
            off = INCLINADA_BASE * escala
            self.poner(visual, x + fx * off, z + fz * off, giro, escala, "PalmeraInclinada", base=y)
            self.ocupado.append((x, z, 2.2 * escala))
            self.ocupado.append((x + fx * off * 1.6, z + fz * off * 1.6, 3.0 * escala))
        else:
            self.poner(visual, x, z, giro, escala, "Palmera", radio=2.2 * escala, base=y)
        alto = 6.0 * escala
        self.lista.append(part("TroncoPalmera", (alto, 1.5 * escala, 1.5 * escala), (x, y + alto / 2, z),
                               "9C6B3E", "Wood", forma="Cylinder", r=rot(0, 0, 90), transp=1, sombra=False))
        if cocos:
            for k in range(2):
                a = self.rnd.uniform(0, 6.28)
                cx, cz = x + 2.6 * math.cos(a), z + 2.6 * math.sin(a)
                if not self.t.mojado(cx, cz):
                    self.lista.append(punto("coco", cx, self.t.suelo(cx, cz) + 0.8, cz))

    def roca(self, visual, x, z, giro, escala, hundir=0.5):
        radio = max(TAM_ISLA[visual][0], TAM_ISLA[visual][2]) * 0.45 * escala
        y, tam = self.poner(visual, x, z, giro, escala, hundir=hundir, radio=radio)
        if tam[1] > 2.5:
            d = min(tam[0], tam[2]) * 0.8
            self.lista.append(part("ColisionRoca", (d, d, d), (x, y + tam[1] * 0.35, z), "FFFFFF", forma="Ball", transp=1,
                                   sombra=False))

    def poisson(self, n, minimo, filtro, rango=(ISLA_X0 + 8, ISLA_X0 + ISLA_NX * ISLA_CELDA - 8, ISLA_Z0 + 8, ISLA_Z0 + ISLA_NZ * ISLA_CELDA - 8)):
        celda = minimo / math.sqrt(2)
        rejilla = {}
        out = []
        for _ in range(n):
            x = self.rnd.uniform(rango[0], rango[1])
            z = self.rnd.uniform(rango[2], rango[3])
            gx, gz = int(x // celda), int(z // celda)
            cerca = False
            for ax in range(gx - 2, gx + 3):
                for az in range(gz - 2, gz + 3):
                    p = rejilla.get((ax, az))
                    if p and (p[0] - x) ** 2 + (p[1] - z) ** 2 < minimo * minimo:
                        cerca = True
            if cerca or not filtro(x, z):
                continue
            rejilla[(gx, gz)] = (x, z)
            out.append((x, z))
        return out


def isla():
    t = Terreno()
    D = Dispersor(t)
    rnd = D.rnd
    p = []
    datos = {"name": "Terreno", "className": "StringValue", "properties": {"Value": t.codificar()},
             "attributes": {"X0": float(ISLA_X0), "Z0": float(ISLA_Z0), "Y0": float(ISLA_Y0), "Celda": float(ISLA_CELDA),
                            "NX": float(ISLA_NX), "NZ": float(ISLA_NZ), "Mar": MAR, "Fondo": FONDO,
                            "Materiales": ",".join(MATERIALES_ISLA), "Niveles": ",".join(str(v) for v in t.niveles),
                            "Oceano": float(OCEANO)}}
    p.append(datos)
    ocx, ocz = ISLA_X0 + ISLA_NX * ISLA_CELDA / 2, ISLA_Z0 + ISLA_NZ * ISLA_CELDA / 2
    lejos = []
    for i in range(-2, 3):
        for k in range(-2, 3):
            if i or k:
                lejos.append(part("MarLejano", (OCEANO, 1, OCEANO), (ocx + i * OCEANO, MAR - 0.6, ocz + k * OCEANO), "17809A",
                                  colision=False, sombra=False))
    p.append(carpeta("MarLejano", lejos))
    p.append(part("RampaSuelo", (12, 2.6, 5.2), (0, 91.3, 31.4), "8A8F96", "DiamondPlate", clase="WedgePart", r=rot(0, 180, 0), transp=1))
    p.append(part("CubiertaMuelle", (62, 0.6, 8), (190, 89.9, -74), "6E4A2B", "WoodPlanks", transp=1))
    d = D.lista

    sx, sz = CIMA
    yc = t.suelo(sx, sz)
    D.ocupado.append((sx, sz, 10))
    gm = giro_hacia(12, 8)
    fx, fz = -math.sin(math.radians(gm)), -math.cos(math.radians(gm))
    D.poner("Mirador", sx, sz, gm, base=yc - 0.1)
    d.append(part("SueloMirador", (12.6, 1.4, 12.6), (sx, yc + 0.6, sz), "9C6B3E", "WoodPlanks", r=rot(0, gm, 0), transp=1))
    d.append(part("EscalonMirador", (3.4, 1.4, 2.4), (sx + fx * 7.2, yc + 0.6, sz + fz * 7.2), "9C6B3E", "WoodPlanks", clase="WedgePart",
                  r=rot(0, gm, 0), transp=1, sombra=False))
    d.append(deco("EstacionRadio", "EstacionRadio", (6, 4, 4), sx, yc + 1.3, sz, giro_hacia(12, 8), "9C6B3E", atributos={"Zona": "Radio"}))
    cx, cz = CAMPAMENTO
    d.append(deco("Hoguera", "Hoguera", (6, 3, 6), cx + 2, t.suelo(cx + 2, cz + 2) - 0.1, cz + 2, 0, "6E4A2B", atributos={"Zona": "Hoguera"}))
    D.ocupado.append((cx + 2, cz + 2, 5))
    D.poner("Refugio", cx - 10, cz - 12, giro_hacia(12, 14), radio=6)
    D.poner("Cartel", cx - 12, cz + 9, giro_hacia(-1, 0.3), radio=1.5)
    D.poner("SenalSOS", 108, 24, 15, hundir=0.05, radio=12)
    for i, x in enumerate((175, 205)):
        D.poner("Muelle", x, -74, 90, base=87.2)
    d.append(part("PuntoRescate", (1, 1, 1), (238, 89.2, -74), "FFFFFF", transp=1, colision=False, sombra=False, atributos={"Zona": "Rescate"}))

    D.poner("RestosAla", 30, 106, 20, hundir=0.5, radio=10)
    D.poner("RestosMotor", -24, 62, 40, hundir=0.6, radio=4, atributos={"Fuego": 1.6})
    D.poner("TrozoFuselaje", -62, 50, -32, hundir=0.5, radio=6, colision=True, atributos={"Fuego": 1.2})
    for x, z, g in ((12, 46, 30), (-14, 54, 200), (22, 84, 110), (-8, 98, 300), (42, 60, 75)):
        D.poner("AsientoRoto", x, z, g, hundir=0.2, radio=1.8)
    for x, z, g, v in ((26, 52, 10, "MaletaAbierta"), (-30, 80, 140, "MaletaAbierta"), (54, 44, 250, "MaletaAbierta"),
                       (8, 66, 60, "MaletaCerrada"), (-20, 40, 95, "MaletaCerrada"), (36, 72, 180, "MaletaCerrada"),
                       (-44, 64, 20, "MaletaCerrada"), (64, 30, 300, "MaletaCerrada")):
        D.poner(v, x, z, g, hundir=0.1, radio=2)
    D.ocupado.append((14, 34, 2))
    radios = [(16, 34), (-22, 72), (-56, 40), (-146, 50), (-12, -184), (128, 30)]
    for i, (x, z) in enumerate(radios):
        g = rnd.uniform(0, 360)
        y, tam = D.poner("CajaAbierta", x, z, g, hundir=0.1, radio=3)
        d.append(part("TapaCaja", (2.8, 1.6, 2.3), (x, y + 0.8, z), "C98B4E", "Wood", r=rot(0, g, 0), transp=1, sombra=False))
        d.append(punto("radio", x, y + 2.6, z))
    D.poner("Bote", -152, 60, 120, hundir=0.4, radio=7, colision=True)
    bx, bz = -52, 2
    gb = giro_hacia(1, -0.4)
    fx, fz = -math.sin(math.radians(gb)), -math.cos(math.radians(gb))
    y, _ = D.poner("CajaBengala", bx, bz, gb, hundir=0.05, radio=2)
    d.append(part("TapaCaja", (2.3, 0.9, 1.5), (bx + fx * 0.22, y + 0.45, bz + fz * 0.22), "F27B2B", r=rot(0, gb, 0), transp=1, sombra=False))
    d.append(punto("bengala", bx + fx * 0.22, y + 1.8, bz + fz * 0.22))

    ex, ez = ESTANQUE
    ux, uz = CIMA[0] - ex, CIMA[1] - ez
    L = math.hypot(ux, uz)
    ux, uz = ux / L, uz / L
    D.poner("Cascada", ex + ux * 10.8, ez + uz * 10.8, giro_hacia(-ux, -uz), 0.85, base=98.6, radio=5)
    D.ocupado.append((ex, ez, 15))

    for linea in SENDAS[:2]:
        a, b = linea[0], linea[1]
        D.poner("Cartel", a[0] + 4, a[1] - 2, giro_hacia(b[0] - a[0], b[1] - a[1]) + 90, radio=1.5)
    for x, z, g in ((-170, 62, 30), (-186, 46, 100), (-160, 82, 200), (-200, -118, 60)):
        D.poner("Charca", x, z, g, hundir=0.35, radio=5)

    for x, z in ((-58, -66), (52, -92), (-112, -84), (88, -138), (-24, -230), (-122, -152), (18, -120)):
        g = rnd.uniform(0, 360)
        D.poner("PilaLena", x + 3.5 * math.cos(math.radians(g)), z + 3.5 * math.sin(math.radians(g)), g, radio=3)
        d.append(punto("tronco", x, t.suelo(x, z) + 1, z))
        D.ocupado.append((x, z, 4.0))
    for x, z in ((60, 70), (-92, 74), (-190, 8), (152, -20), (130, -196), (-200, -126), (-120, 82), (166, -112)):
        d.append(punto("cangrejo", x, t.suelo(x, z) + 0.6, z))

    def zona(x, z):
        s = t.costa(x, z)
        c = acantilado(x, z)
        W = ancho_playa(x, z, c)
        return s, W, c

    for x, z in D.poisson(9000, 12, lambda x, z: (lambda s, W, c: c < 0.4 and W - 12 < s < W + 3 and not t.mojado(x, z))(*zona(x, z)) and D.libre(x, z, 2.5)):
        if rnd.random() < 0.8:
            mx, mz = t.hacia_mar(x, z)
            D.palmera("PalmeraInclinada", x, z, giro_hacia(mx, mz) + rnd.uniform(-30, 30), rnd.uniform(0.8, 1.15))

    grandes = (("Palmera1", 0.18), ("Palmera2", 0.17), ("Palmera3", 0.1), ("Platanera", 0.22), ("HojasGrandes", 0.15), ("PalmeraJoven", 0.18))

    def elegir(opciones):
        r = rnd.random() * sum(w for _, w in opciones)
        for nombre, w in opciones:
            r -= w
            if r <= 0:
                return nombre
        return opciones[-1][0]

    def selva(x, z):
        s, W, c = zona(x, z)
        return s > W + 5 and t.material(x, z) in ("Grass", "LeafyGrass") and not t.mojado(x, z) and fbm(x, z, 55, 77) > -0.2

    arboles = []
    for x, z in D.poisson(16000, 11, lambda x, z: selva(x, z) and D.libre(x, z, 2.5)):
        if rnd.random() > 0.3 + 0.7 * ss(-0.25, 0.3, fbm(x, z, 48, 79)):
            continue
        v = elegir(grandes)
        e = rnd.uniform(0.85, 1.15) * {"Platanera": 1.35, "HojasGrandes": 1.6}.get(v, 1.0)
        arboles.append((x, z))
        if v.startswith("Palmera"):
            D.palmera(v, x, z, rnd.uniform(0, 360), e, cocos=v != "PalmeraJoven" and rnd.random() < 0.5)
        else:
            D.poner(v, x, z, rnd.uniform(0, 360), e, radio=2.0 * e, hundir=0.2)
    rejilla = {}
    for x, z in arboles:
        rejilla.setdefault((int(x // 16), int(z // 16)), []).append((x, z))

    def junto_arbol(x, z, r):
        gx, gz = int(x // 16), int(z // 16)
        return any((x - ax) ** 2 + (z - az) ** 2 < r * r for i in (-1, 0, 1) for k in (-1, 0, 1) for ax, az in rejilla.get((gx + i, gz + k), ()))

    pequenas = (("Helecho", 0.34), ("ArbustoTropical", 0.26), ("Flores", 0.16), ("HojasGrandes", 0.16), ("Hierba", 0.08))
    escalas = {"Helecho": (1.5, 2.2), "ArbustoTropical": (1.0, 1.4), "Flores": (1.8, 2.6), "HojasGrandes": (0.9, 1.4), "Hierba": (1.2, 1.7)}

    def maleza(x, z):
        s, W, c = zona(x, z)
        if s < W - 4 or t.mojado(x, z) or t.material(x, z) == "Rock":
            return False
        borde = s < W + 9
        return (borde or junto_arbol(x, z, 9.5) or fbm(x, z, 30, 91) > 0.3) and D.libre(x, z, 2.6)
    for x, z in D.poisson(30000, 6.0, maleza):
        v = elegir(pequenas)
        a, b = escalas[v]
        e = rnd.uniform(a, b)
        D.poner(v, x, z, rnd.uniform(0, 360), e, radio=1.2 * e, hundir=0.12)
    for x, z in D.poisson(9000, 6, lambda x, z: (lambda s, W, c: W - 16 < s < W - 2 and c < 0.5 and not t.mojado(x, z))(*zona(x, z)) and D.libre(x, z, 0.8)):
        if rnd.random() < 0.55:
            D.poner("Hierba", x, z, rnd.uniform(0, 360), rnd.uniform(1.1, 1.7), radio=0.6, hundir=0.1)
    for x, z in D.poisson(4000, 16, lambda x, z: (lambda s, W, c: -3 < s < 14 and c < 0.5 and t.altura(x, z) > MAR - 0.6)(*zona(x, z)) and D.libre(x, z, 1.0)):
        D.poner("Conchas", x, z, rnd.uniform(0, 360), rnd.uniform(1.0, 1.5), radio=1.0, hundir=0.05)
    for x, z in D.poisson(3000, 42, lambda x, z: (lambda s, W, c: 5 < s < W - 6 and c < 0.4 and not t.mojado(x, z))(*zona(x, z)) and D.libre(x, z, 4)):
        D.poner("MaderaDeriva", x, z, rnd.uniform(0, 360), rnd.uniform(0.8, 1.2), radio=3.5, hundir=0.25)
    for x, z in D.poisson(4000, 20, lambda x, z: (lambda s, W, c: c > 0.45 and -16 < s < -3)(*zona(x, z)) and D.libre(x, z, 4)):
        D.roca("Acantilado", x, z, rnd.uniform(0, 360), rnd.uniform(0.7, 1.3), hundir=1.5)
    for x, z in D.poisson(6000, 14, lambda x, z: (lambda s, W, c: (c > 0.3 and -4 < s < 30) or t.material(x, z) == "Rock")(*zona(x, z)) and D.libre(x, z, 3)):
        v = elegir((("RocaGrande", 0.25), ("RocaMedia", 0.4), ("RocaPequena", 0.35)))
        D.roca(v, x, z, rnd.uniform(0, 360), rnd.uniform(0.6, 1.1) if v == "RocaGrande" else rnd.uniform(0.7, 1.3))
    for x, z in D.poisson(3000, 34, lambda x, z: (lambda s, W, c: -6 < s < 8 and c < 0.4)(*zona(x, z)) and D.libre(x, z, 4)):
        D.roca(elegir((("RocasPlanas", 0.6), ("RocaPequena", 0.4))), x, z, rnd.uniform(0, 360), rnd.uniform(0.8, 1.2), hundir=0.4)

    print("ISLA", sum(D.cuenta.values()), "props", sorted(D.cuenta.items()))
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
