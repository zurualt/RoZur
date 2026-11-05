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
    p.append(part("Suelo", (INTERIOR * 2, G, 74.3), (0, SUELO_Y - G / 2, -15.15), MOQUETA, "Fabric"))
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
    p.append(part("SueloCabina", (11, G, 9.9), (0, SUELO_Y - G / 2, -57.25), MOQUETA, "Fabric"))
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
    for k in range(-1, 5):
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


TC = (82.0, -24.0)
SUELO_T = 90.5
LOBBY_HW, LOBBY_HE = 22.0, 15.0
LOBBY_PUERTAS = (20.0, -4.0, -28.0)
LOBBY_SALIDA = (35.0, 41.0)
LOBBY_MONTANTES = [-48.0] + [-43.0 + 6.0 * k for k in range(16)] + [48.0]
LOBBY_TRAGALUCES = [(-30.0, -24.0), (-6.0, 0.0), (18.0, 24.0)]
LOBBY_LAMPARAS = [(x, z) for x in (-22.0, -6.0, 10.0, 24.0) for z in (-38.0, -14.0, 4.0, 30.0)]
CRUDO = "FFFFFF"


def techo_lobby(x):
    return LOBBY_HW + (LOBBY_HE - LOBBY_HW) * (x + 32.0) / 64.0


def tl(x, z):
    return TC[0] + x, TC[1] + z


def desde(ox, oz, base, giro, xb, yb, zb):
    lx, ly, lz = -xb, zb, yb
    g = math.radians(giro)
    c, s = math.cos(g), math.sin(g)
    return ox + lx * c + lz * s, base + ly, oz - lx * s + lz * c


def caja(nombre, o, giro, x0, x1, y0, y1, z0, z1, color, base=SUELO_T, girar=0.0, **kw):
    pos = desde(o[0], o[1], base, giro, (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    return part(nombre, (x1 - x0, z1 - z0, y1 - y0), pos, color, r=rot(0, giro + girar, 0), **kw)


def zona(nombre, o, giro, x0, x1, y0, y1, z0, z1, atributos=None, base=SUELO_T):
    return caja(nombre, o, giro, x0, x1, y0, y1, z0, z1, CRUDO, base, transp=1, colision=False, sombra=False, atributos=atributos)


def pieza(nombre, visual, x, z, giro, tam=(1, 1, 1), color=GRIS, colision=False, hijos=None, atributos=None, base=SUELO_T,
          forma=None, transp=0.0):
    a = {"Visual": visual, "Base": base}
    if atributos:
        a.update(atributos)
    wx, wz = tl(x, z)
    return part(nombre, tam, (wx, base + tam[1] / 2, wz), color, r=rot(0, giro, 0), colision=colision, atributos=a, hijos=hijos,
                forma=forma, transp=transp)


def luz_neon(nombre, tam, pos, color, rango, brillo, forma=None, r=None, transp=0.0):
    return part(nombre, tam, pos, color, "Neon", forma=forma, r=r, colision=False, sombra=False, transp=transp,
                hijos=[{"name": "Luz", "className": "PointLight",
                        "properties": {"Range": rango, "Brightness": brillo, "Color": rgb(color), "Shadows": False}}])


def lobby_casco():
    t = []
    cx, cz = TC
    teta = math.degrees(math.atan((LOBBY_HW - LOBBY_HE) / 64.0))
    t.append(pieza("LobbySuelo", "LobbySuelo", 0, 0, 180, (64, 0.5, 96), base=90.0,
                   hijos=[part("SueloTerminal", (64, 0.5, 96), (cx, 90.25, cz), "D6B088", "SmoothPlastic")]))
    paredes = [
        part("ParedEste", (0.6, LOBBY_HE, 96), (cx + 31.7, 90 + LOBBY_HE / 2, cz), "E0C9A6"),
    ]
    for nombre, z in (("ParedNorte", cz - 47.7), ("ParedSur", cz + 47.7)):
        paredes.append(part(nombre, (64, LOBBY_HE, 0.6), (cx, 90 + LOBBY_HE / 2, z), "E0C9A6"))
        paredes.append(part(nombre, (0.6, LOBBY_HW - LOBBY_HE, 64), (cx, 90 + LOBBY_HE + (LOBBY_HW - LOBBY_HE) / 2, z), "E0C9A6",
                            clase="WedgePart", r=rot(0, -90, 0)))
    for zg in LOBBY_PUERTAS:
        paredes.append(part("PuertaEmbarque", (0.4, 8.6, 5.2), (cx - 32, SUELO_T + 4.3, cz + zg), "F3E6CC"))
    t.append(pieza("LobbyParedes", "LobbyParedes", 0, 0, 180, (64, 1, 96), base=90.0, hijos=paredes))
    alto = LOBBY_HW
    for za, zb in zip(LOBBY_MONTANTES, LOBBY_MONTANTES[1:]):
        puerta = any(abs((za + zb) / 2 - zg) < 0.5 for zg in LOBBY_PUERTAS) or (za, zb) == LOBBY_SALIDA
        y0 = 9.7 if puerta else SUELO_T - 90
        t.append(part("CristalTerminal", (0.2, alto - y0, zb - za - 0.4), (cx - 32, 90 + (alto + y0) / 2, cz + (za + zb) / 2),
                      CRISTAL, "Glass", transp=0.6, sombra=False))
    xm = (-36.0 + 33.0) / 2
    ancho = (33.0 + 36.0) / math.cos(math.radians(teta))
    t.append(pieza("LobbyTecho", "LobbyTecho", 0, 0, 180, (64, 1, 96), base=90.0, hijos=[
        part("TechoTerminal", (ancho, 1.2, 99), (cx + xm, 90 + techo_lobby(xm) + 0.6, cz), "BDB3A3", r=rot(0, 0, -teta))]))
    xs = (-18.0 + 14.0) / 2
    largo = (14.0 + 18.0) / math.cos(math.radians(teta))
    for z0, z1 in LOBBY_TRAGALUCES:
        t.append(part("Tragaluz", (largo, 0.2, z1 - z0), (cx + xs, 90 + techo_lobby(xs) + 1.2, cz + (z0 + z1) / 2), CRISTAL, "Glass",
                      r=rot(0, 0, -teta), transp=0.55, sombra=False, colision=False))
    for x, z in LOBBY_LAMPARAS:
        wx, wz = tl(x, z)
        t.append(luz_neon("LamparaLobby", (0.1, 2.0, 2.0), (wx, 90 + techo_lobby(x) - 5.15, wz), "FFE2A8", 30, 0.55,
                          forma="Cylinder", r=rot(0, 0, 90)))
    return t


def lobby_puertas():
    t = []
    cx, cz = TC
    for i, zg in enumerate(LOBBY_PUERTAS):
        sx, sz = cx - 20.0, cz + zg
        t.append(deco("PuertaSala", f"PuertaSala{i + 1}", (9.2, 3.47, 10.45), sx - 0.625, SUELO_T, sz, -90, GRIS, colision=False))
        t.append(part("SalaSalida", (0.12, 8.4, 8.4), (sx, SUELO_T + 0.06, sz), CRUDO, forma="Cylinder", r=rot(0, 0, 90),
                      transp=1, colision=False, sombra=False, atributos={"Sala": i + 1}))
        t.append(part("PantallaSala", (1.95, 1.05, 0.04), (sx - 5.15, SUELO_T + 2.65, sz), "1B1B21", r=rot(0, -90, 0),
                      transp=1, colision=False, sombra=False, atributos={"Sala": i + 1}))
    for x in (-27.0, -23.0):
        for z in (8.0, -16.0, -39.0):
            o = tl(x, z)
            asientos = [caja("BancoColision", o, 90, -5.0, 5.0, -1.0, 1.0, 0.0, 1.0, NARANJA)]
            for k in range(5):
                asientos.append(caja("AsientoLobby", o, 90, -4.8 + 2.0 * k, -3.2 + 2.0 * k, -0.8, 0.9, 1.0, 1.3, NARANJA,
                                     clase="Seat", transp=1, sombra=False))
            t.append(pieza("Banco", "BancoEspera", x, z, 90, (10, 1.0, 2), NARANJA, hijos=asientos))
    for x, z in ((-17.0, 8.0), (-17.0, -16.0), (-1.5, -21.0), (11.0, 31.0)):
        t.append(pieza("Papelera", "Papelera", x, z, 0, (1.2, 1.8, 1.2), "157F7B", colision=True))
    return t


def lobby_isla():
    t = []
    o = tl(6.0, 10.0)
    hijos = [caja("MuroTablero", o, 180, -10.0, 10.0, -0.6, 0.6, 0.0, 13.2, "1FA6A0"),
             part("MostradorInfo", (2.45, 8.4, 8.4), desde(o[0], o[1], SUELO_T, 180, 0.0, -4.2, 1.225), "1FA6A0", forma="Cylinder",
                  r=rot(0, 0, 90))]
    t.append(pieza("IslaInfo", "IslaInfo", 6.0, 10.0, 180, (2, 2, 2), hijos=hijos))
    tx, ty, tz = desde(o[0], o[1], SUELO_T, 180, 0.0, -0.72, 7.4)
    t.append(part("Tablero", (17.6, 8.8, 0.2), (tx, ty, tz), "1B1B21", atributos={"Tablero": True}))
    for nombre, xb, yb in (("Timbre", 1.6, -7.65), ("Microfono", -1.6, -7.6)):
        px, _, pz = desde(o[0], o[1], SUELO_T, 180, xb, yb, 0.0)
        t.append(part(nombre, (0.8, 0.5, 0.8) if nombre == "Timbre" else (0.7, 0.9, 0.9), (px, SUELO_T + 2.45 + 0.4, pz), CRUDO,
                      r=rot(0, 180, 0), colision=False, transp=1, atributos={"Visual": nombre, "Base": SUELO_T + 2.45},
                      extra={"CanQuery": True}))
    for x, z in ((-2.5, 6.5), (14.5, 6.5)):
        t.append(pieza("Planta", "PlantaMonstera", x, z, 0, (1.6, 1.3, 1.6), "C9693E", colision=True))
    sx, sz = tl(2.0, 34.0)
    t.append(part("SpawnAeropuerto", (8, 0.4, 8), (sx, SUELO_T + 0.2, sz), CRUDO, clase="SpawnLocation", transp=1,
                  colision=False, extra={"Enabled": True, "Neutral": True, "Duration": 0}))
    return t


def lobby_facturacion():
    t = []
    for i, z in enumerate((18.0, 8.0, -2.0)):
        o = tl(28.85, z)
        hijos = [
            caja("MostradorFacturacion", o, 90, -3.7, 0.55, -1.17, 1.15, 0.0, 2.42, "1FA6A0"),
            caja("Bascula", o, 90, 0.6, 3.4, -1.8, -0.15, 0.0, 0.45, "A9B0B8", atributos={"Mostrador": i + 1}),
            caja("CintaLobby", o, 90, 0.78, 3.22, -0.15, 2.1, 0.25, 0.5, "2A2C31", girar=180, atributos={"Velocidad": 4}),
            caja("PortalFacturacion", o, 90, 0.4, 3.6, 2.1, 2.5, 0.0, 3.1, "157F7B"),
            caja("PantallaBascula", o, 90, -0.12, 0.82, -1.19, -1.15, 2.72, 3.23, "1B1B21", transp=1, colision=False, sombra=False,
                 atributos={"Mostrador": i + 1}),
            zona("Trampilla", o, 90, 0.8, 3.2, 1.5, 2.1, 0.5, 2.6, {"Mostrador": i + 1}),
        ]
        t.append(pieza("Facturacion", "Facturacion", 28.85, z, 90, (1, 1, 1), hijos=hijos))
    t.append(pieza("ColaFacturacion", "PostesCola", 21.5, 8.0, 90, (1, 1, 1)))
    return t


def lobby_seguridad():
    t = []
    for i, x in enumerate((2.0, 8.0)):
        o = tl(x, -14.0)
        hijos = [caja("ArcoColision", o, 0, -2.05, -1.5, -0.5, 0.5, 0.0, 6.9, "F3E6CC"),
                 caja("ArcoColision", o, 0, 1.5, 2.05, -0.5, 0.5, 0.0, 6.9, "F3E6CC"),
                 caja("ArcoColision", o, 0, -2.05, 2.05, -0.5, 0.5, 6.9, 7.7, "F3E6CC"),
                 zona("Detector", o, 0, -1.45, 1.45, -0.45, 0.45, 0.0, 5.0, {"Arco": i + 1})]
        t.append(pieza("ArcoSeguridad", "ArcoSeguridad", x, -14.0, 0, (1, 1, 1), hijos=hijos))
        lx, ly, lz = desde(o[0], o[1], SUELO_T, 0, 0.0, 0.0, 8.15)
        t.append(luz_neon("LuzArco", (0.6, 0.6, 0.6), (lx, ly, lz), "6DBE45", 10, 0, forma="Ball", r=None))
    o = tl(14.0, -14.0)
    hijos = [caja("RayosColision", o, 0, -1.6, 1.6, -1.9, 1.9, 0.0, 3.1, "D4D1CB"),
             caja("RayosColision", o, 0, -1.35, 1.35, -5.2, -1.9, 0.0, 1.25, "2A2C31"),
             caja("RayosColision", o, 0, -1.35, 1.35, 1.9, 5.2, 0.0, 1.25, "2A2C31")]
    t.append(pieza("RayosX", "RayosX", 14.0, -14.0, 0, (1, 1, 1), hijos=hijos))
    return t


def lobby_cinta():
    t = []
    L, RC, ALTO = 6.0, 3.5, 1.2
    o = tl(18.8, -28.0)
    g = 180
    hijos = [caja("IslaCinta", o, g, -L, L, -2.4, 2.4, 0.0, 1.9, "7C858F")]
    for s in (-1, 1):
        cx_, _, cz_ = desde(o[0], o[1], SUELO_T, g, s * L, 0.0, 0.0)
        hijos.append(part("IslaCinta", (1.9, 4.8, 4.8), (cx_, SUELO_T + 0.95, cz_), "7C858F", forma="Cylinder", r=rot(0, 0, 90)))
    tramos = []
    for s in (-1, 1):
        tramos.append((0.0, s * RC, 2 * L, 1.0 if s < 0 else -1.0, 0.0))
    for s in (-1, 1):
        for k in range(8):
            a = math.radians(-90 + 22.5 * (k + 0.5)) if s > 0 else math.radians(90 + 22.5 * (k + 0.5))
            tx, ty = -math.sin(a), math.cos(a)
            tramos.append((s * L + RC * math.cos(a), RC * math.sin(a), 1.95, tx, ty))
    for xb, yb, largo, tx, ty in tramos:
        px, _, pz = desde(o[0], o[1], SUELO_T, g, xb, yb, 0.0)
        dx, dz = tx, -ty
        yaw = math.degrees(math.atan2(-dx, -dz))
        hijos.append(part("CintaLobby", (2.2, 0.6, largo), (px, SUELO_T + ALTO - 0.3, pz), "2A2C31", r=rot(0, yaw, 0),
                          atributos={"Velocidad": 6}))
        nx, ny = (0.0, yb / abs(yb)) if abs(xb) < 0.01 else ((xb - math.copysign(L, xb)) / RC, yb / RC)
        rx, _, rz = desde(o[0], o[1], SUELO_T, g, xb + nx * 1.25, yb + ny * 1.25, 0.0)
        hijos.append(part("BordeCinta", (0.25, 0.9, largo + 0.15), (rx, SUELO_T + 1.15, rz), "F6C445", r=rot(0, yaw, 0)))
    PX = L + 4.6 + 0.2
    hijos.append(caja("PortalCinta", o, g, PX, PX + 1.8, -2.6, 2.6, 0.0, 5.2, "157F7B"))
    rx0, rz0, rx1, rz1 = PX, 2.6, L + 2.4 + 0.6, 1.55
    pend = math.degrees(math.atan((rz0 - rz1) / (rx0 - rx1)))
    largo = math.hypot(rx0 - rx1, rz0 - rz1)
    mx, my, mz = desde(o[0], o[1], SUELO_T, g, (rx0 + rx1) / 2, 0.0, (rz0 + rz1) / 2 - 0.1)
    hijos.append(part("RampaCinta", (largo, 0.2, 2.8), (mx, my, mz), "A9B0B8", r=rot(0, 0, pend)))
    t.append(pieza("CintaEquipaje", "CintaEquipaje", 18.8, -28.0, g, (1, 1, 1), hijos=hijos))
    sx, sy, sz = desde(o[0], o[1], SUELO_T, g, PX - 0.6, 0.0, 3.4)
    t.append(part("SalidaCinta", (1, 1, 1), (sx, sy, sz), CRUDO, transp=1, colision=False, sombra=False))
    for xb, yb in ((-4.0, -RC), (0.0, -RC), (4.0, -RC), (-4.0, RC), (2.0, RC), (-L - RC, 0.0)):
        px, py, pz = desde(o[0], o[1], SUELO_T, g, xb, yb, ALTO + 0.7)
        t.append(part("PuntoMaleta", (1, 1, 1), (px, py, pz), CRUDO, transp=1, colision=False, sombra=False))
    return t


def lobby_rincones():
    t = []
    o = tl(-7.0, -39.0)
    t.append(pieza("RinconLounge", "RinconLounge", -7.0, -39.0, 0, (1, 1, 1), hijos=[
        caja("SillonColision", o, 0, -4.0, -2.0, -1.1, 1.1, 0.0, 1.4, "D9A23A"),
        caja("SillonColision", o, 0, 2.0, 4.0, -1.1, 1.1, 0.0, 1.4, "1FA6A0"),
        caja("MesaColision", o, 0, -0.9, 0.9, -0.9, 0.9, 0.0, 1.2, "C08A57")]))
    o = tl(20.0, -45.77)
    t.append(pieza("Fotomaton", "Fotomaton", 20.0, -45.77, 180, (4.0, 8.0, 3.0), "F27B2B", colision=True))
    fx, fy, fz = desde(o[0], o[1], SUELO_T, 180, 0.0, -1.85, 7.95)
    t.append(luz_neon("FlashFoto", (2.0, 0.4, 0.15), (fx, fy, fz), "FFF6E0", 26, 0, transp=1))
    fx, fy, fz = desde(o[0], o[1], SUELO_T, 180, 2.3, -0.7, 1.3)
    t.append(part("SalidaFoto", (0.3, 0.3, 0.3), (fx, fy, fz), CRUDO, transp=1, colision=False, sombra=False))
    for nombre, z in (("ExpendedoraRoja", -38.5), ("ExpendedoraAzul", -43.0)):
        o = tl(30.3, z)
        bx, by, bz = desde(o[0], o[1], SUELO_T, 90, 1.12, -1.2, 2.45)
        boca = part("Boca", (0.4, 0.4, 0.4), desde(o[0], o[1], SUELO_T, 90, -0.4, -1.5, 1.0), CRUDO, transp=1, colision=False,
                    sombra=False)
        t.append(pieza("Expendedora", nombre, 30.3, z, 90, (3.24, 6.2, 2.2), "D9443A", colision=True))
        t.append(part("BotonExpendedora", (0.6, 0.6, 0.4), (bx, by, bz), CRUDO, r=rot(0, 90, 0), colision=False, transp=1,
                      atributos={"Visual": "BotonRojo", "Base": by}, hijos=[boca], extra={"CanQuery": True}))
    for x, z in ((-29.5, 31.0), (-29.5, -45.5), (29.5, -14.0), (13.5, -45.5), (29.5, 26.0)):
        t.append(pieza("Planta", "PlantaGrande", x, z, (x * 7 + z * 3) % 360, (1.8, 1.6, 1.8), "C9693E", colision=True))
    for x, z in ((1.5, -45.0), (-15.5, -45.0)):
        t.append(pieza("Planta", "PlantaMonstera", x, z, 30, (1.6, 1.3, 1.6), "F3E6CC", colision=True))
    for x, z, g in ((16.0, 29.6, 0), (-12.0, -36.0, 90)):
        t.append(pieza("Jardinera", "Jardinera", x, z, g, (8.1, 1.4, 1.7), "C08A57", colision=True))
    return t


def lobby_cafe_tienda():
    t = []
    o = tl(22.0, 44.15)
    hijos = [caja("BarraCafe", o, 0, -7.25, 7.25, -1.2, 0.7, 0.0, 2.5, "C08A57"),
             caja("BarraCafe", o, 0, -7.2, 7.2, 2.1, 3.25, 0.0, 8.2, "2E5E63")]
    t.append(pieza("Cafeteria", "Cafeteria", 22.0, 44.15, 0, (1, 1, 1), hijos=hijos))
    px, py, pz = desde(o[0], o[1], SUELO_T, 0, 0.5, -0.9, 2.9)
    t.append(part("PuntoCafe", (1.2, 0.8, 1.0), (px, py, pz), CRUDO, transp=1, colision=False, sombra=False))
    for x, z, g in ((15.5, 34.5, 0), (22.0, 36.0, 15), (28.0, 34.5, -10), (18.5, 39.8, 5), (25.5, 39.8, -5)):
        o = tl(x, z)
        t.append(pieza("MesaCafe", "MesaCafe", x, z, g, (1, 1, 1), hijos=[
            caja("SillasColision", o, g, -2.75, 2.75, -0.75, 0.75, 0.0, 1.5, "1FA6A0"),
            part("MesaColision", (2.44, 2.4, 2.4), desde(o[0], o[1], SUELO_T, g, 0, 0, 1.22), "F3E6CC", forma="Cylinder",
                 r=rot(0, 0, 90))]))
    t.append(deco("Tienda", "Tienda", (8, 5, 4), tl(-4.0, 45.4)[0], SUELO_T, tl(-4.0, 45.4)[1], 0, TURQUESA))
    for x in (-12.5, 4.5):
        o = tl(x, 46.35)
        t.append(pieza("Estanteria", "EstanteriaTienda", x, 46.35, 0, (1, 1, 1), hijos=[
            caja("EstanteriaColision", o, 0, -3.05, 3.05, -0.5, 1.05, 0.0, 4.5, "6B3F7A")]))
    o = tl(-19.0, 43.5)
    t.append(pieza("Chocolate", "ChocolateGigante", -19.0, 43.5, 20, (1, 1, 1), hijos=[
        caja("ChocolateColision", o, 20, -3.0, 3.0, -1.0, 1.0, 0.0, 1.7, "D9A93A")]))
    return t


def lobby_movibles():
    t = []
    for x, z, g in ((13.5, 25.5, 0), (16.0, 25.5, 4), (18.5, 25.5, -3), (7.0, -21.0, 70)):
        wx, wz = tl(x, z)
        t.append(part("CarroMaletas", (1.7, 2.4, 2.7), (wx, SUELO_T + 1.2, wz), "3D7DD8", anclado=False, r=rot(0, g, 0),
                      atributos={"Visual": "CarroMaletas", "Movil": True}))
    wx, wz = tl(8.0, 26.0)
    t.append(part("Pelota", (2.2, 2.2, 2.2), (wx, SUELO_T + 1.1, wz), "D9443A", forma="Ball", anclado=False,
                  atributos={"Visual": "Pelota", "Movil": True}))
    return t


def terminal():
    t = lobby_casco() + lobby_puertas() + lobby_isla() + lobby_facturacion() + lobby_seguridad() + lobby_cinta() + \
        lobby_rincones() + lobby_cafe_tienda() + lobby_movibles()
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
    arboles = [(40, -82), (124, 28), (124, -62), (124, 6), (-40, -60), (-46, 8), (-38, 72), (36, 100), (96, 100),
               (-52, -130), (40, -140), (-60, 130), (124, -26), (118, 40), (-70, -20)]
    for x, z in arboles:
        d.append(deco("Arbol", "Arbol", (1.2, 9, 1.2), x, 90, z, (x * 37 + z) % 360, "8A5A33"))
    for x, z in ((47.5, -66), (47.5, -40), (47.5, -16), (47.5, 4), (118, -40), (118, -10)):
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
AVION_PIEZAS = [((-8.5, 8.5, -66.0, 31.5), 90.0), ((-38.1, 38.1, -30.5, -17.5), 97.4), ((-22.6, -13.4, -28.8, -19.2), 93.2),
                ((13.4, 22.6, -28.8, -19.2), 93.2), ((-6.2, 6.2, 22.0, 36.0), 89.0)]
CIMA = (-78.0, -158.0)
ESTANQUE = (0.0, -200.0)
LAGUNA = (-168.0, -50.0)
CAMPAMENTO = (146.0, -74.0)
SURCO = ((0.0, 128.0), (0.0, 27.0))
COSTA = [(95, 66), (55, 76), (15, 80), (-25, 78), (-65, 72), (-100, 70), (-130, 82), (-158, 86), (-178, 68), (-174, 42),
         (-196, 18), (-214, -18), (-222, -60), (-214, -100), (-204, -140), (-196, -185), (-172, -228), (-136, -262),
         (-88, -286), (-36, -296), (14, -290), (60, -270), (102, -240), (134, -200), (156, -156), (170, -112),
         (176, -70), (172, -28), (160, 12), (138, 44), (118, 60)]
ACANTILADOS = [(-92, -290, 80), (-20, -305, 70), (42, -285, 55), (-196, -196, 48), (122, -226, 40)]
SENDAS = [
    [(-8, -74), (-20, -98), (-36, -120), (-52, -138), (-66, -150), (-71, -154)],
    [(-36, -120), (-8, -148), (14, -172), (15, -189)],
    [(132, -92), (98, -122), (50, -146), (0, -160), (-50, -162), (-68, -156)],
    [(40, -44), (78, -60), (116, -72), (130, -76)],
]
COLINAS = [(CIMA[0], CIMA[1], 29.0, 42.0, 12.0), (-150, -210, 13.0, 34.0, 0.0), (98, -176, 7.0, 28.0, 0.0), (-30, -252, 8.0, 40.0, 0.0)]
ROCAS_TERRENO = [(-166, 72, 11, 4.5), (-150, 90, 7, 2.5), (-184, 50, 8, 3.5), (150, -168, 9, 5.0), (-104, -122, 9, 6.0),
                 (-118, -200, 8, 5.0), (162, 30, 7, 3.0), (-206, -110, 8, 4.0), (60, -262, 9, 4.0)]
RADIOS = [(16.0, 38.0), (-22.0, 72.0), (-56.0, 40.0), (-146.0, 48.0), (24.0, -186.0), (128.0, 30.0)]
LENAS = [(-58, -66, 30), (52, -92, 120), (-112, -84, 200), (88, -138, 300), (-24, -230, 60), (-122, -152, 250), (18, -120, 160)]
BENGALA = (-52.0, 2.0)
SOS = (108.0, 24.0)
TIKI = (56.0, -6.0)
GIGANTE = (-70.0, -44.0)
SANTUARIO = (74.0, 46.0)
ROCA_CANGREJO = (-116.0, 64.0)
PECES = [(-172, -52), (-160, -36), (-182, -62), (-150, -58), (-196, -48), (206, -40), (212, -112)]


def pila_lena(x, z, g):
    return x + 3.5 * math.cos(math.radians(g)), z + 3.5 * math.sin(math.radians(g))


CHARCAS = [(-170, 62, 30), (-186, 46, 100), (-160, 82, 200), (-200, -118, 60)]
PLATAFORMAS = ([(x, z, 3.2) for x, z in RADIOS] + [(x, z, 4.5) for x, z, _ in CHARCAS] + [(BENGALA[0], BENGALA[1], 2.6), (SOS[0], SOS[1], 12.5), (TIKI[0], TIKI[1], 3.0),
                                                   (SANTUARIO[0], SANTUARIO[1], 4.0)] + [(*pila_lena(x, z, g), 3.6) for x, z, g in LENAS])
TAM_ISLA = {e["nombre"]: tuple(e["tamano"]) for e in json.load(open(os.path.join(RAIZ, "arte", "kit_isla", "manifest.json"), encoding="utf-8"))}
INCLINADA_BASE = 7.53
ARBOLES_ISLA = {"Palmera1", "Palmera2", "Palmera3", "PalmeraInclinada", "PalmeraJoven", "Platanera", "PalmeraGigante"}
PLANTAS_ISLA = {"Helecho", "HojasGrandes", "Flores", "Hierba", "HierbaPlaya", "ArbustoTropical"}
INCLINAR = {"RocaGrande", "RocaMedia", "RocaPequena", "RocasPlanas", "Charca", "Conchas", "MaderaDeriva", "AsientoRoto", "MaletaAbierta",
            "MaletaCerrada", "TrozoFuselaje", "RestosAla", "RestosMotor", "Bote", "RocaCangrejo"}
HUNDIR = {"Acantilado": 0.1, "RocasPlanas": 0.25, "Charca": 0.3, "Conchas": 0.1, "RestosAla": 0.25, "Bote": 0.15, "RestosMotor": 0.18,
          "TrozoFuselaje": 0.06, "RocaGrande": 0.16, "RocaMedia": 0.16, "RocaPequena": 0.18, "RocaCangrejo": 0.06, "MaderaDeriva": 0.15}


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
        for px, pz, pr in PLATAFORMAS:
            objetivo = self.altura(px, pz)
            for iz in range(ISLA_NZ):
                for ix in range(ISLA_NX):
                    x, z = self.centro(ix, iz)
                    dd = math.hypot(x - px, z - pz)
                    if dd < pr + 5:
                        i = iz * ISLA_NX + ix
                        self.h[i] = mezcla(self.h[i], objetivo, 1 - ss(pr, pr + 5, dd))
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
        if q < 16 and 11 < t < 38:
            muro = 99.0 + 13.2 * min(1.0, max(0.0, (t - 12.5) / 8.0)) * (1 - ss(11, 16, q))
            if muro > h:
                h = muro
            if t < 22 and q < 13:
                mat = "Rock"
        if q < 4.8 and 12.0 < t < 20.5:
            cara = 98.6 + 1.76 * (t - 12.85) - 1.3 * (1 - ss(3.0, 4.8, q))
            if h > cara:
                h = cara
        if q < 3.2 and 20.0 < t < 36:
            h = min(h, 110.2 + 0.03 * (t - 16))
            mat = "Rock"
            agua = nivel_arroyo
        abierto = (1 - ss(14, 42, r_est)) * ss(-2, -16, t)
        if abierto > 0:
            h = mezcla(h, min(h, 100.4 + 0.08 * max(0.0, r_est - 14)), abierto)
        if r_est < 17:
            fondo = 96.0 + 3.6 * ss(8, 15, r_est)
            h = min(h, fondo) if r_est < 14 else mezcla(min(h, fondo), h, ss(14, 17, r_est))
            if r_est < 14:
                agua = nivel_estanque
            mat = "Rock" if 11 < r_est < 16 and t > -5 else ("Sand" if r_est <= 13 else mat)
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
        if dcima < 20:
            h = mezcla(h, 121.0, 1 - ss(13, 20, dcima))
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
            antes = h
            h += surco * (1.0 if z < 84 else 0.6)
            if antes > MAR + 0.5:
                h = max(h, MAR + 0.45)
            if ds < 4.6 + 1.2 * fbm(x, z, 9, 71) and h > MAR - 0.2:
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

    def h_grad(self, x, z):
        return ((self.altura(x + 2, z) - self.altura(x - 2, z)) / 4, (self.altura(x, z + 2) - self.altura(x, z - 2)) / 4)

    def pendiente(self, x, z):
        return math.hypot(*self.h_grad(x, z))

    def normal(self, x, z, r, tope=22):
        gx = (self.altura(x + r, z) - self.altura(x - r, z)) / (2 * r)
        gz = (self.altura(x, z + r) - self.altura(x, z - r)) / (2 * r)
        n = math.sqrt(gx * gx + 1 + gz * gz)
        nx, ny, nz = -gx / n, 1 / n, -gz / n
        lim = math.cos(math.radians(tope))
        if ny < lim:
            k = math.sqrt((1 - lim * lim) / (nx * nx + nz * nz))
            nx, ny, nz = nx * k, lim, nz * k
        return nx, ny, nz

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


def frente(giro):
    return -math.sin(math.radians(giro)), -math.cos(math.radians(giro))


def bajo_avion(x, z, r, alto):
    for (x0, x1, z0, z1), y0 in AVION_PIEZAS:
        if alto > y0 and x0 - r < x < x1 + r and z0 - r < z < z1 + r:
            return True
    return False


class Dispersor:
    def __init__(self, t, semilla=7):
        self.t = t
        self.rnd = random.Random(semilla)
        self.ocupado = []
        self.lista = []
        self.cuenta = {}
        self.rocas = []

    def libre(self, x, z, r, alto=False):
        if dist_rect(x, z, AVION_RECT) < 6 + r:
            return False
        for i, linea in enumerate(SENDAS):
            if dist_linea(x, z, linea) < 3.6 + r * 0.6 + (7 if alto and i in (0, 3) else 0):
                return False
        if dist_seg(x, z, *SURCO[0], *SURCO[1])[0] < 8 + r * 0.5:
            return False
        if math.hypot(x - CAMPAMENTO[0], z - CAMPAMENTO[1]) < 16 + r:
            return False
        if math.hypot(x - CIMA[0], z - CIMA[1]) < (24 if alto else 12) + r:
            return False
        if 150 < x < 240 and abs(z + 74) < 8 + r:
            return False
        if alto and self.t.pendiente(x, z) > 0.55:
            return False
        for ox, oz, orr in self.ocupado:
            if (x - ox) ** 2 + (z - oz) ** 2 < (r + orr) ** 2:
                return False
        return True

    def poner(self, visual, x, z, giro, escala=1.0, nombre=None, hundir=None, radio=None, colision=False, atributos=None,
              hijos=None, base=None):
        tam = [v * escala for v in TAM_ISLA[visual]]
        if radio is not None:
            self.ocupado.append((x, z, radio))
        atributos = dict(atributos or {})
        if base is None:
            h0 = self.t.altura(x, z)
            if hundir is None:
                hundir = HUNDIR.get(visual, 0.02 if visual in ARBOLES_ISLA else (0.07 if visual in PLANTAS_ISLA else 0.03))
            if visual in PLANTAS_ISLA or visual in ARBOLES_ISLA:
                r = 0.22 * max(tam[0], tam[2]) if visual not in ARBOLES_ISLA else 0.9 * escala
                h0 = min([h0] + [self.t.altura(x + r * math.cos(k * 0.785), z + r * math.sin(k * 0.785)) for k in range(8)])
            base = h0 - hundir * tam[1]
            if visual in INCLINAR:
                nx, ny, nz = self.t.normal(x, z, max(1.5, 0.4 * max(tam[0], tam[2])), 34 if visual in ("RocaGrande", "RocaMedia", "RocaPequena") else 22)
                if ny < 0.9995:
                    atributos["Normal"] = {"Vector3": [round(nx, 4), round(ny, 4), round(nz, 4)]}
                r = 0.38 * max(tam[0], tam[2])
                hueco = min(self.t.altura(x + dx * r, z + dz * r) - (h0 - (nx * dx * r + nz * dz * r) / ny)
                            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)))
                base += min(0.0, hueco)
        self.lista.append(deco(nombre or visual, visual, tuple(tam), x, base, z, giro % 360, "FFFFFF", colision=colision,
                               hijos=hijos, atributos=atributos or None, transp=1))
        self.cuenta[visual] = self.cuenta.get(visual, 0) + 1
        return base, tam

    def palmera(self, visual, x, z, giro, escala, cocos=False):
        y = self.t.suelo(x, z, 0.8) - 0.35 * escala
        if visual == "PalmeraInclinada":
            fx, fz = frente(giro)
            off = INCLINADA_BASE * escala
            self.poner(visual, x + fx * off, z + fz * off, giro, escala, "PalmeraInclinada", base=y)
            self.ocupado.append((x, z, 2.4 * escala))
            self.ocupado.append((x + fx * off * 1.6, z + fz * off * 1.6, 3.4 * escala))
        else:
            self.poner(visual, x, z, giro, escala, "Palmera" if visual != "PalmeraGigante" else visual, radio=2.4 * escala, base=y)
        alto = 6.0 * escala
        grueso = 1.5 * escala * (2.0 if visual == "PalmeraGigante" else 1.0)
        self.lista.append(part("TroncoPalmera", (alto, grueso, grueso), (x, y + alto / 2, z), "9C6B3E", "Wood", forma="Cylinder", r=rot(0, 0, 90),
                               transp=1, sombra=False))
        if cocos:
            for k in range(2):
                a = self.rnd.uniform(0, 6.28)
                cx, cz = x + 2.6 * math.cos(a), z + 2.6 * math.sin(a)
                if not self.t.mojado(cx, cz):
                    self.lista.append(punto("coco", cx, self.t.altura(cx, cz) + 0.8, cz))

    def roca(self, visual, x, z, giro, escala, hundir=None):
        radio = max(TAM_ISLA[visual][0], TAM_ISLA[visual][2]) * 0.45 * escala
        y, tam = self.poner(visual, x, z, giro, escala, hundir=hundir, radio=radio)
        self.rocas.append((visual, x, z, y, tam, escala))
        if tam[1] > 2.5:
            dd = min(tam[0], tam[2]) * 0.8
            self.lista.append(part("ColisionRoca", (dd, dd, dd), (x, y + tam[1] * 0.35, z), "FFFFFF", forma="Ball", transp=1, sombra=False))

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


def orilla(t):
    puntos = []
    for iz in range(ISLA_NZ):
        for ix in range(ISLA_NX):
            i = iz * ISLA_NX + ix
            for j, (dx, dz) in ((i + 1, (1, 0)), (i + ISLA_NX, (0, 1))):
                if (dx and ix == ISLA_NX - 1) or (dz and iz == ISLA_NZ - 1):
                    continue
                a, b = t.h[i] - MAR, t.h[j] - MAR
                if a * b < 0 and t.w[i] == 0 and t.w[j] == 0:
                    f = a / (a - b)
                    x, z = t.centro(ix, iz)
                    puntos.append((x + dx * ISLA_CELDA * f, z + dz * ISLA_CELDA * f))
    return puntos


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
    p.append(part("RampaSuelo", (12, 2.6, 5.2), (0, 91.3, 31.4), "8A8F96", "DiamondPlate", clase="WedgePart", r=rot(0, 180, 0), transp=1))
    d = D.lista

    sx, sz = CIMA
    yc = t.altura(sx, sz)
    D.ocupado.append((sx, sz, 11))
    gm = giro_hacia(12, 8)
    fx, fz = frente(gm)
    D.poner("Mirador", sx, sz, gm, base=yc - 0.05)
    d.append(part("SueloMirador", (12.6, 1.4, 15.6), (sx, yc + 0.6, sz), "9C6B3E", "WoodPlanks", r=rot(0, gm, 0), transp=1))
    d.append(part("EscalonMirador", (3.4, 1.35, 2.2), (sx + fx * 7.85, yc + 0.6, sz + fz * 7.85), "9C6B3E", "WoodPlanks", clase="WedgePart",
                  r=rot(0, gm, 0), transp=1, sombra=False))
    d.append(deco("EstacionRadio", "EstacionRadio", (6, 4, 4), sx, yc + 1.25, sz, gm, "9C6B3E", atributos={"Zona": "Radio", "Apoyo": "Mirador"}, transp=1))

    cx, cz = CAMPAMENTO
    d.append(deco("Hoguera", "Hoguera", (6, 3, 6), cx + 2, t.altura(cx + 2, cz + 2) - 0.08, cz + 2, 0, "6E4A2B", atributos={"Zona": "Hoguera"}, transp=1))
    D.ocupado.append((cx + 2, cz + 2, 5))
    D.poner("Refugio", cx - 9, cz - 11, giro_hacia(11, 13), radio=6)
    D.poner("Cartel", cx - 12, cz + 9, giro_hacia(-1, 0.3), radio=1.5)
    D.poner("SenalSOS", SOS[0], SOS[1], 15, radio=12)
    muelle_y = max(t.altura(160.5, -74), t.altura(163, -74)) + 0.12 - 2.8
    for x in (175, 205):
        D.poner("Muelle", x, -74, 90, base=muelle_y)
        for k in (-14, -7, 0, 7, 14):
            for lado in (-3.55, 3.55):
                px = x + k
                if t.altura(px, -74 + lado) < muelle_y + 0.5:
                    D.poner("Pilote", px, -74 + lado, 0, base=muelle_y + 0.6 - TAM_ISLA["Pilote"][1], atributos={"Apoyo": "Muelle"})
    p.append(part("CubiertaMuelle", (62, 0.6, 8), (190, muelle_y + 2.5, -74), "6E4A2B", "WoodPlanks", transp=1))
    d.append(part("PuntoRescate", (1, 1, 1), (238, MAR + 0.2, -74), "FFFFFF", transp=1, colision=False, sombra=False, atributos={"Zona": "Rescate"}))

    D.poner("RestosAla", 30, 106, 20, radio=10)
    D.poner("RestosMotor", -24, 62, 40, radio=4, atributos={"Fuego": 1.6})
    D.poner("TrozoFuselaje", -62, 52, -32, radio=6, colision=True, atributos={"Fuego": 1.2})
    for x, z, g in ((14, 48, 30), (-14, 54, 200), (22, 84, 110), (-8, 98, 300), (42, 60, 75), (34, -7, 250), (-26, 6, 120)):
        D.poner("AsientoRoto", x, z, g, radio=1.8)
    for x, z, g, v in ((24, 3, 70, "MaletaCerrada"), (31, 12, 200, "MaletaAbierta"), (18, 14, 140, "MaletaCerrada"), (27, 54, 10, "MaletaAbierta"), (-30, 80, 140, "MaletaAbierta"), (54, 44, 250, "MaletaAbierta"),
                       (8, 66, 60, "MaletaCerrada"), (-20, 42, 95, "MaletaCerrada"), (36, 72, 180, "MaletaCerrada"),
                       (-44, 64, 20, "MaletaCerrada"), (64, 30, 300, "MaletaCerrada")):
        D.poner(v, x, z, g, radio=2)
    for i, (x, z) in enumerate(RADIOS):
        g = rnd.uniform(0, 360)
        y, tam = D.poner("CajaAbierta", x, z, g, radio=3.2)
        d.append(part("TapaCaja", (2.8, 1.6, 2.3), (x, y + 0.8, z), "C98B4E", "Wood", r=rot(0, g, 0), transp=1, sombra=False))
        d.append(punto("radio", x, y + 2.6, z))
    D.poner("Bote", -152, 60, 120, radio=7, colision=True)
    bx, bz = BENGALA
    gb = giro_hacia(1, -0.4)
    fx, fz = frente(gb)
    y, _ = D.poner("CajaBengala", bx, bz, gb, radio=2.4)
    d.append(part("TapaCaja", (2.3, 0.9, 1.5), (bx + fx * 0.22, y + 0.45, bz + fz * 0.22), "F27B2B", r=rot(0, gb, 0), transp=1, sombra=False))
    d.append(punto("bengala", bx + fx * 0.22, y + 1.8, bz + fz * 0.22))

    D.poner("Tiki", TIKI[0], TIKI[1], giro_hacia(-1, 0.15), 1.05, radio=3, colision=True)
    D.palmera("PalmeraGigante", GIGANTE[0], GIGANTE[1], giro_hacia(1, 0.2), 1.0)
    D.poner("SantuarioBotellas", SANTUARIO[0], SANTUARIO[1], giro_hacia(-0.3, -1), radio=4)
    D.roca("RocaCangrejo", ROCA_CANGREJO[0], ROCA_CANGREJO[1], giro_hacia(0.3, -1), 1.0)

    ex, ez = ESTANQUE
    ux, uz = CIMA[0] - ex, CIMA[1] - ez
    L = math.hypot(ux, uz)
    ux, uz = ux / L, uz / L
    D.poner("Cascada", ex + ux * 14.5, ez + uz * 14.5, giro_hacia(-ux, -uz), 0.85, base=98.75, radio=5)
    D.ocupado.append((ex, ez, 15))

    for linea in (SENDAS[0], SENDAS[1], SENDAS[3]):
        a, b = linea[0], linea[1]
        lx, lz = b[0] - a[0], b[1] - a[1]
        n = math.hypot(lx, lz)
        D.poner("Cartel", a[0] - lz / n * 4.5, a[1] + lx / n * 4.5, giro_hacia(lx, lz) + 90, radio=1.5)
    for x, z, g in CHARCAS:
        D.poner("Charca", x, z, g, radio=5)

    for x, z, g in LENAS:
        px, pz = pila_lena(x, z, g)
        D.poner("PilaLena", px, pz, g, radio=3)
        d.append(punto("tronco", x, t.altura(x, z) + 1, z))
        D.ocupado.append((x, z, 4.0))

    def zona(x, z):
        s = t.costa(x, z)
        c = acantilado(x, z)
        W = ancho_playa(x, z, c)
        return s, W, c

    cangrejos = D.poisson(6000, 40, lambda x, z: (lambda s, W, c: 4 < s < W - 4 and c < 0.4 and not t.mojado(x, z))(*zona(x, z)) and D.libre(x, z, 1.5))
    for x, z in cangrejos[:16]:
        d.append(punto("cangrejo", x, t.altura(x, z) + 0.6, z))
    for x, z in PECES:
        d.append(punto("pez", x, MAR, z))

    for x, z in D.poisson(9000, 12, lambda x, z: (lambda s, W, c: c < 0.4 and W - 12 < s < W + 3 and not t.mojado(x, z))(*zona(x, z)) and t.pendiente(x, z) < 0.6 and D.libre(x, z, 2.5)):
        if rnd.random() < 0.8:
            mx, mz = t.hacia_mar(x, z)
            g = giro_hacia(mx, mz) + rnd.uniform(-30, 30)
            e = rnd.uniform(0.8, 1.15)
            fx, fz = frente(g)
            cx, cz = x + fx * 10 * e, z + fz * 10 * e
            if bajo_avion(cx, cz, 6 * e, 120) or any(math.hypot(cx - ox, cz - oz) < 4 + orr * 0.5 for ox, oz, orr in D.ocupado):
                continue
            D.palmera("PalmeraInclinada", x, z, g, e)

    grandes = (("Palmera1", 0.18), ("Palmera2", 0.17), ("Palmera3", 0.1), ("Platanera", 0.22), ("HojasGrandes", 0.15), ("PalmeraJoven", 0.18))

    def elegir(opciones):
        r = rnd.random() * sum(w for _, w in opciones)
        for nombre, w in opciones:
            r -= w
            if r <= 0:
                return nombre
        return opciones[-1][0]

    for x, z in D.poisson(4000, 20, lambda x, z: (lambda s, W, c: c > 0.45 and -16 < s < -3)(*zona(x, z)) and D.libre(x, z, 4)):
        D.roca("Acantilado", x, z, rnd.uniform(0, 360), rnd.uniform(0.7, 1.3))
    for x, z in D.poisson(6000, 14, lambda x, z: (lambda s, W, c: (c > 0.3 and -4 < s < 30) or t.material(x, z) == "Rock")(*zona(x, z)) and t.pendiente(x, z) < 1.1 and D.libre(x, z, 3)):
        v = elegir((("RocaGrande", 0.25), ("RocaMedia", 0.4), ("RocaPequena", 0.35)))
        D.roca(v, x, z, rnd.uniform(0, 360), rnd.uniform(0.6, 1.1) if v == "RocaGrande" else rnd.uniform(0.7, 1.3))
    for x, z in D.poisson(3000, 34, lambda x, z: (lambda s, W, c: -6 < s < 8 and c < 0.4)(*zona(x, z)) and D.libre(x, z, 5)):
        D.roca(elegir((("RocasPlanas", 0.6), ("RocaPequena", 0.4))), x, z, rnd.uniform(0, 360), rnd.uniform(0.8, 1.2))

    def selva(x, z):
        s, W, c = zona(x, z)
        return s > W + 5 and t.material(x, z) in ("Grass", "LeafyGrass") and not t.mojado(x, z) and fbm(x, z, 55, 77) > -0.2

    arboles = []
    for x, z in D.poisson(16000, 11, lambda x, z: selva(x, z) and D.libre(x, z, 2.5, alto=True)):
        if rnd.random() > 0.3 + 0.7 * ss(-0.25, 0.3, fbm(x, z, 48, 79)):
            continue
        v = elegir(grandes)
        e = rnd.uniform(0.85, 1.15) * {"Platanera": 1.35, "HojasGrandes": 1.6}.get(v, 1.0)
        if v == "HojasGrandes":
            e *= min(1.0, max(0.6, 1.0 - 1.6 * (t.pendiente(x, z) - 0.15)))
        arboles.append((x, z))
        if v.startswith("Palmera"):
            D.palmera(v, x, z, rnd.uniform(0, 360), e, cocos=v != "PalmeraJoven" and rnd.random() < 0.5)
        else:
            D.poner(v, x, z, rnd.uniform(0, 360), e, radio=2.0 * e)
    rejilla = {}
    for x, z in arboles:
        rejilla.setdefault((int(x // 16), int(z // 16)), []).append((x, z))

    def junto_arbol(x, z, r):
        gx, gz = int(x // 16), int(z // 16)
        return any((x - ax) ** 2 + (z - az) ** 2 < r * r for i in (-1, 0, 1) for k in (-1, 0, 1) for ax, az in rejilla.get((gx + i, gz + k), ()))

    pequenas = (("Helecho", 0.34), ("ArbustoTropical", 0.26), ("Flores", 0.16), ("HojasGrandes", 0.16), ("Hierba", 0.08))
    escalas = {"Helecho": (1.5, 2.2), "ArbustoTropical": (1.1, 1.5), "Flores": (1.8, 2.6), "HojasGrandes": (0.9, 1.4), "Hierba": (1.2, 1.7)}

    def maleza(x, z):
        s, W, c = zona(x, z)
        if s < W - 4 or t.mojado(x, z) or t.material(x, z) == "Rock" or t.pendiente(x, z) > 0.34:
            return False
        borde = s < W + 9
        return (borde or junto_arbol(x, z, 9.5) or fbm(x, z, 30, 91) > 0.3) and D.libre(x, z, 2.6)
    for x, z in D.poisson(30000, 11.0, maleza):
        v = elegir(pequenas)
        a, b = escalas[v]
        e = rnd.uniform(a, b) * min(1.0, max(0.55, 1.0 - 1.6 * (t.pendiente(x, z) - 0.15)))
        D.poner(v, x, z, rnd.uniform(0, 360), e, radio=1.2 * e)

    borde = []
    for iz in range(1, ISLA_NZ - 1):
        for ix in range(1, ISLA_NX - 1):
            i = iz * ISLA_NX + ix
            if MATERIALES_ISLA[t.m[i]] not in ("Grass", "LeafyGrass") or t.h[i] < MAR + 0.8:
                continue
            for j in (i + 1, i - 1, i + ISLA_NX, i - ISLA_NX):
                if MATERIALES_ISLA[t.m[j]] == "Sand":
                    x1, z1 = t.centro(ix, iz)
                    x2, z2 = t.centro(j % ISLA_NX, j // ISLA_NX)
                    borde.append(((x1 + x2) / 2 + rnd.uniform(-1.5, 1.5), (z1 + z2) / 2 + rnd.uniform(-1.5, 1.5), x2 - x1, z2 - z1))
                    break
    rnd.shuffle(borde)
    puestos = []
    for x, z, dx, dz in borde:
        if any((x - a) ** 2 + (z - b) ** 2 < 81 for a, b in puestos) or not D.libre(x, z, 1.0) or t.mojado(x, z):
            continue
        puestos.append((x, z))
        r = rnd.random()
        if r < 0.55:
            D.poner("HierbaPlaya", x + dx * 0.4, z + dz * 0.4, rnd.uniform(0, 360), rnd.uniform(0.8, 1.2), radio=0.8)
        elif r < 0.85:
            D.poner("Hierba", x - dx * 0.3, z - dz * 0.3, rnd.uniform(0, 360), rnd.uniform(1.2, 1.7), radio=0.6)
        else:
            D.poner("Helecho", x - dx * 0.5, z - dz * 0.5, rnd.uniform(0, 360), rnd.uniform(0.9, 1.3), radio=1.2)
    def pradera(x, z):
        s, W, c = zona(x, z)
        return s > W + 6 and t.material(x, z) in ("Grass", "LeafyGrass") and not t.mojado(x, z) and t.pendiente(x, z) < 0.34 and D.libre(x, z, 4.0)
    for x, z in D.poisson(12000, 17.0, pradera):
        r = rnd.random()
        v = "Hierba" if r < 0.45 else ("Flores" if r < 0.7 else ("Helecho" if r < 0.9 else "ArbustoTropical"))
        e = {"Hierba": rnd.uniform(1.3, 1.9), "Flores": rnd.uniform(1.4, 2.0), "Helecho": rnd.uniform(1.1, 1.5), "ArbustoTropical": rnd.uniform(0.9, 1.2)}[v]
        D.poner(v, x, z, rnd.uniform(0, 360), e, radio=1.0 * e)
    for x, z in D.poisson(9000, 12.0, lambda x, z: (lambda s, W, c: W - 16 < s < W - 2 and c < 0.5 and not t.mojado(x, z))(*zona(x, z)) and D.libre(x, z, 0.8)):
        if rnd.random() < 0.5:
            D.poner("HierbaPlaya" if rnd.random() < 0.7 else "Hierba", x, z, rnd.uniform(0, 360), rnd.uniform(0.8, 1.25), radio=0.7)
    for x, z in D.poisson(4000, 16, lambda x, z: (lambda s, W, c: -3 < s < 14 and c < 0.5 and t.altura(x, z) > MAR - 0.6)(*zona(x, z)) and D.libre(x, z, 1.0)):
        D.poner("Conchas", x, z, rnd.uniform(0, 360), rnd.uniform(1.0, 1.5), radio=1.0)
    for x, z in D.poisson(3000, 42, lambda x, z: (lambda s, W, c: 5 < s < W - 6 and c < 0.4 and not t.mojado(x, z))(*zona(x, z)) and D.libre(x, z, 4)):
        e = rnd.uniform(0.8, 1.2)
        D.poner("MaderaDeriva", x, z, rnd.uniform(0, 360), e, radio=4.8 * e)
    cimas = {"Acantilado": (0.2, -0.1, 0.985), "RocaGrande": (0.06, 0.0, 0.97), "RocaCangrejo": (0.0, -0.05, 0.93)}
    candidatas = [r for r in D.rocas if r[0] in cimas]
    rnd.shuffle(candidatas)
    for v, x, z, y, tam, e in candidatas[:14]:
        ox, oz, fy = cimas[v]
        D.poner("Gaviota", x + ox * tam[0], z + oz * tam[2], rnd.uniform(0, 360), rnd.uniform(1.1, 1.4), base=y + tam[1] * fy - 0.08,
                atributos={"Apoyo": v})
    for x, z in ((182, -70.45), (198, -77.55), (212, -70.45)):
        D.poner("Gaviota", x, z, rnd.uniform(0, 360), 1.25, base=muelle_y + 3.0, atributos={"Apoyo": "Muelle"})

    puntos = orilla(t)
    rnd.shuffle(puntos)
    espumas = []
    for x, z in puntos:
        if any((x - a) ** 2 + (z - b) ** 2 < 81 for a, b in espumas):
            continue
        if 150 < x < 240 and abs(z + 74) < 10:
            continue
        if math.hypot((x - LAGUNA[0]) / 44.0, (z - LAGUNA[1]) / 31.0) < 1.15:
            continue
        espumas.append((x, z))
        g = t.h_grad(x, z)
        mx, mz = -g[0], -g[1]
        n = math.hypot(mx, mz) or 1
        mx, mz = mx / n, mz / n
        D.poner("Espuma", x + mx * 0.6, z + mz * 0.6, giro_hacia(mx, mz) + rnd.uniform(-8, 8), rnd.uniform(0.9, 1.15), base=MAR + 0.03)

    print("ISLA", sum(D.cuenta.values()), "props", sorted(D.cuenta.items()))
    p.append(carpeta("Decorado", d))
    return {"className": "Model", "children": p}


NAVE_X, NAVE_Z, NAVE_SUELO = 34.0, 72.0, 90.5
NAVE_X0, NAVE_X1, NAVE_Z0, NAVE_Z1, NAVE_ALTO = 18.0, 50.0, 52.0, 92.0, 18.0
NAVE_PUERTA = (26.8, 41.2, 9.4)
TOBOGANES = (58.0, 65.0, 72.0, 79.0)


def entre(nombre, a, b, ancho, grueso, color, material="SmoothPlastic", **kw):
    dx, dy = b[0] - a[0], b[1] - a[1]
    largo = math.hypot(dx, dy)
    centro = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, a[2])
    return part(nombre, (largo, grueso, ancho), centro, color, material, r=rot(0, 0, math.degrees(math.atan2(dy, dx))), **kw)


def tobogan(n, z):
    s = NAVE_SUELO
    arriba, abajo = (18.8, s + 4.5, z), (23.8, s + 1.9, z)
    hijos = [entre("RampaTobogan", arriba, abajo, 2.4, 0.3, METAL, "Metal")]
    for dz in (-1.3, 1.3):
        hijos.append(entre("BordeTobogan", (arriba[0], arriba[1] + 0.35, z + dz), (abajo[0], abajo[1] + 0.35, z + dz), 0.2, 0.7, NARANJA))
        hijos.append(part("BordeBandeja", (2.6, 0.7, 0.2), (25.1, s + 1.7, z + dz), NARANJA))
    hijos.append(part("Bandeja", (2.6, 0.4, 2.8), (25.1, s + 1.2, z), METAL, "Metal"))
    hijos.append(part("TopeBandeja", (0.3, 1.1, 2.8), (26.55, s + 1.75, z), NARANJA))
    hijos.append(part("Boca", (1, 1, 1), (19.6, s + 5.7, z), "FFFFFF", r=rot(0, -90, 0), transp=1, colision=False, sombra=False))
    luz_ = part(f"LuzTobogan{n}", (0.5, 0.5, 1.4), (18.55, s + 9.9, z), "5A5F66", colision=False,
                hijos=[{"name": "Luz", "className": "PointLight",
                        "properties": {"Range": 10, "Brightness": 0, "Color": rgb("F6C445"), "Shadows": False}}])
    return [deco(f"Tobogan{n}", f"Tobogan{n}", (3.0, 8.4, 8.4), 22.4, s, z, -90, GRIS, colision=False, transp=1,
                 hijos=hijos, atributos={"Tobogan": n}), luz_]


def preparacion():
    s = NAVE_SUELO
    x0, x1, z0, z1, alto = NAVE_X0, NAVE_X1, NAVE_Z0, NAVE_Z1, NAVE_ALTO
    pa, pb, ph = NAVE_PUERTA
    techo = s + alto
    pared = "D6CAB3"
    p = []
    casco = [
        part("ParedOeste", (0.6, alto, z1 - z0), (x0, s + alto / 2, NAVE_Z), pared),
        part("ParedEste", (0.6, alto, z1 - z0), (x1, s + alto / 2, NAVE_Z), pared),
        part("ParedSur", (x1 - x0, alto, 0.6), (NAVE_X, s + alto / 2, z1), pared),
        part("ParedNorte", (pa - x0, alto, 0.6), ((x0 + pa) / 2, s + alto / 2, z0), pared),
        part("ParedNorte", (x1 - pb, alto, 0.6), ((pb + x1) / 2, s + alto / 2, z0), pared),
        part("DintelPuerta", (pb - pa, alto - ph, 0.6), (NAVE_X, s + ph + (alto - ph) / 2, z0), pared),
    ]
    for xa, xb in ((x0, 24.0), (44.0, x1)):
        casco.append(part("Techo", (xb - xa, 0.6, z1 - z0), ((xa + xb) / 2, techo + 0.3, NAVE_Z), "8A8F96", colision=False))
    for za, zb in ((z0, 58.0), (62.0, 70.0), (74.0, 82.0), (86.0, z1)):
        casco.append(part("Techo", (20.0, 0.6, zb - za), (NAVE_X, techo + 0.3, (za + zb) / 2), "8A8F96", colision=False))
    p.append(deco("Nave", "NaveCarga", (x1 - x0, 0.5, z1 - z0), NAVE_X, 90.0, NAVE_Z, 0, "C9C2B5", hijos=casco,
                  material="Concrete"))
    p.append(part("Persiana", (pb - pa - 0.2, ph - 0.2, 0.4), (NAVE_X, s + (ph - 0.2) / 2, z0 + 0.65), "F6C445", "Metal",
                  atributos={"Visual": "PersianaNave", "Movil": True, "Subida": ph - 0.6}))
    for n, z in enumerate(TOBOGANES, 1):
        p.extend(tobogan(n, z))
    p.append(part("ZonaToboganes", (6, 4, 26), (24.0, s + 2, 68.5), "FFFFFF", transp=1, colision=False, sombra=False))
    p.append(deco("Surtidor", "Surtidor", (2.0, 4.6, 2.6), 48.3, s, 57.0, 90, "D9443A"))
    p.append(part("PantallaSurtidor", (1.5, 1.1, 0.05), (47.05, s + 3.35, 57.0), "1B1B21", r=rot(0, 90, 0), transp=1,
                  colision=False, sombra=False))
    vallas = [part("VallaCorral", (x1 - 39.5, 2.6, 0.3), ((39.5 + x1) / 2, s + 1.3, 75.3), MADERA, "Wood"),
              part("VallaCorral", (0.3, 2.6, z1 - 75.3), (39.5, s + 1.3, (75.3 + z1) / 2), MADERA, "Wood")]
    p.append(marca("Corral", (x1 - 39.5, 2.6, z1 - 75.3), ((39.5 + x1) / 2, s + 1.3, (75.3 + z1) / 2), "CorralAnimales",
                   base=s, hijos=vallas))
    p.append(deco("CuboMerienda", "CuboMerienda", (1.4, 1.6, 1.4), 38.2, s, 73.4, 30, TURQUESA))
    p.append(deco("CarroDecorado", "CarroEquipaje", (7, 1.9, 5), 45.0, s, 66.0, 90, GRIS))
    for x, z, g in ((21.2, 88.4, 12), (21.0, 54.6, -8)):
        p.append(deco("PilaCajas", "PilaCajas", (4.4, 4.8, 4.4), x, s, z, g, MADERA))
    for x, z in ((26.0, 62.0), (42.0, 62.0), (26.0, 82.0), (42.0, 82.0)):
        p.append(deco("Lampara", "LamparaNave", (1.8, 5.0, 1.8), x, techo - 5.0, z, 0, GRIS, colision=False, hijos=[
            part("Bombilla", (0.4, 0.4, 0.4), (x, techo - 4.6, z), "FFE2A8", "Neon", colision=False, sombra=False,
                 hijos=[luz(26, 0.32, "FFEBD2")])]))
    p.append(deco("CartelMaletas", "CartelMaletas", (7.0, 2.6, 0.3), x0 + 0.45, s + 9.8, 68.5, -90, NARANJA, colision=False))
    p.append(deco("CartelAnimales", "CartelAnimales", (5.0, 2.6, 0.3), 44.6, s + 7.6, z1 - 0.45, 0, TURQUESA, colision=False))
    p.append(deco("CartelCombustible", "CartelCombustible", (3.2, 2.6, 0.3), x1 - 0.45, s + 6.6, 57.0, 90, "D9443A",
                  colision=False))
    p.append(deco("CartelSalida", "CartelSalida", (8.0, 3.0, 0.3), NAVE_X, s + ph + 1.6, z0 - 0.45, 0, TURQUESA, colision=False))
    marcas = [
        part("PuestoTractor", (1, 1, 1), (NAVE_X, s, 60.0), "FFFFFF", transp=1, colision=False, sombra=False),
        part("PuestoCarro", (1, 1, 1), (NAVE_X, s, 70.875), "FFFFFF", r=rot(0, 90, 0), transp=1, colision=False, sombra=False),
        part("SitioJaula", (1, 1, 1), (46.4, s, 84.0), "FFFFFF", transp=1, colision=False, sombra=False),
        part("SitioCocodrilo", (1, 1, 1), (42.0, s, 79.0), "FFFFFF", r=rot(0, 40, 0), transp=1, colision=False, sombra=False),
        part("SalidaNave", (1, 1, 1), (NAVE_X, s, z0 - 4.0), "FFFFFF", transp=1, colision=False, sombra=False),
        part("SpawnPreparacion", (8, 0.4, 8), (28.5, s + 0.2, 81.0), "FFFFFF", clase="SpawnLocation", transp=1, colision=False,
             sombra=False, extra={"Enabled": False, "Neutral": True, "Duration": 0}),
    ]
    p.append(carpeta("Marcas", marcas))
    p.append(carpeta("Sueltos", []))
    return {"className": "Model", "children": p}


def main():
    os.makedirs(SALIDA, exist_ok=True)
    for nombre, datos in (("Avion", avion()), ("Aeropuerto", aeropuerto()), ("Isla", isla()), ("Preparacion", preparacion())):
        ruta = os.path.join(SALIDA, nombre + ".model.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)

    def contar(d):
        return 1 + sum(contar(h) for h in d.get("children", []))

    print("Avion", contar(avion()), "Aeropuerto", contar(aeropuerto()))


main()
