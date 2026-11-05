import bpy
import bmesh
import math
import os
import sys
import json
import random
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT = os.path.dirname(os.path.abspath(__file__))
ARTE = os.path.dirname(OUT)
RAIZ = os.path.dirname(ARTE)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MINI = os.path.join(OUT, "miniaturas")
RENDERS = os.path.join(OUT, "renders")


def cargar(rel):
    ruta = os.path.join(ARTE, rel)
    ns = {"__file__": ruta, "__name__": "generador"}
    with open(ruta, encoding="utf-8") as fh:
        exec(compile(fh.read(), ruta, "exec"), ns)
    ns["OUT"] = OUT
    return ns


K = cargar(os.path.join("kit_extra", "kit_extra_gen.py"))
for _n in ("M frame fr frame_from_normal rbox bb lathe elathe cyl rr_loft bar prism plate decal rect circ rrect "
           "ellipsoid ico tube sheet wrap Prop hat_role front_y logo").split():
    globals()[_n] = K[_n]

# Colores nuevos en las casillas libres de la paleta 8x8 del kit (32-55).
EXTRA = [("dgreen", "1E7A3C"), ("lgreen", "9BD36A"), ("peach", "F2A88A"), ("dred", "A8302A"),
         ("fish", "4FA3E0"), ("dfish", "2B6CB0"), ("flame", "FF9A1F"), ("brown", "6B4426"), ("banana", "FFDC3C")]
for _i, (_n, _h) in enumerate(EXTRA):
    K["PAL"][32 + _i] = (_n, _h)
    K["IDX"][_n] = 32 + _i

# Pivotes de las MeshParts del tripulante v5 (centro de su caja), medidos en Studio. Coordenadas de Blender:
# Z arriba, cara hacia -Y. En Roblox: X = -x, Y = z, Z = y.
PIVOTES = {"Head": Vector((0.0, -0.076, 4.173)), "UpperTorso": Vector((0.0, -0.025, 3.088)), "LowerTorso": Vector((0.0, -0.008, 2.345))}
# Ojos saltones de Ojos.luau: CENTRO y NORMAL respecto a HumanoidRootPart, que en reposo esta en z 3,18.
# El ojo de la derecha del personaje (x negativa en Blender) es un 12 % mas grande y el otro un 8 % mas pequeno.
OJO_Z = 3.18 + 1.143
GAFAS = 0.27
# Los disenos de los gorros se hicieron sobre la cabeza de la v3/v4 (borde en zb, radio ~0,74). Se encogen,
# se suben a la cupula de la cabeza de alubia y se echan 8 grados hacia atras: por delante el borde queda
# por encima de z 4,80 (Y 0,62 en la cabeza, las cejas estan en 0,50).
INCLINACION = math.radians(-8)
S_GORRO = 0.8
FRENTE_MIN = 4.80
# Las mochilas se disenaron sobre la espalda de la v4 (y 0,78 a z 2,83); en la v5 van a z 3,04 y algo mas pequenas.
YB4, ZC4, S_ESPALDA, Z_ESPALDA, Z_CORREA = 0.78, 2.83, 0.75, 3.02, 2.88


def ojo(sx):
    return Vector((sx * 0.232, -0.444, OJO_Z)), Vector((sx * 0.179, -0.98, 0.08)).normalized()


CUERPO = {}


def cargar_cuerpo():
    trip = K["load_tripulante"]()
    if not trip:
        raise SystemExit("Falta arte/tripulante/tripulante.blend")
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for o in trip["objs"]:
        if o.type != "MESH" or not o.name.split("_Geo")[0] in ("Head", "UpperTorso", "LowerTorso"):
            continue
        me = o.evaluated_get(dg).to_mesh()
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in me.vertices]
        polys += [tuple(base + i for i in p.vertices) for p in me.polygons]
        npol = len(me.polygons)
        lo = Vector([min((o.matrix_world @ v.co)[i] for v in me.vertices) for i in range(3)])
        hi = Vector([max((o.matrix_world @ v.co)[i] for v in me.vertices) for i in range(3)])
        print("PARTE %-12s centro %.3f %.3f %.3f" % (o.name.split("_Geo")[0], *((lo + hi) / 2)))
        o.evaluated_get(dg).to_mesh_clear()
        if o.name.startswith("Head_Geo"):
            CUERPO["cabeza"] = BVHTree.FromPolygons(verts[base:], [tuple(i - base for i in q) for q in polys[-npol:]])
    CUERPO["bvh"] = BVHTree.FromPolygons(verts, polys)


def superficie(x, z, lado=-1):
    """Punto de la piel (cabeza o torso) en (x, z) visto desde delante (lado -1) o desde detras (+1)."""
    loc, nrm, _, _ = CUERPO["bvh"].ray_cast(Vector((x, lado * 5.0, z)), Vector((0, -lado, 0)))
    if loc is None:
        raise ValueError("sin piel en %.2f %.2f" % (x, z))
    return loc, nrm


def hacia(bvh, centro, d):
    loc = bvh.ray_cast(centro + d * 4.0, -d)[0]
    return loc if loc is not None else centro


def cabeza_dir(th, al, off, centro=Vector((0.0, 0.0, 4.55))):
    """Punto de la cabeza (con la diadema) en la direccion (th desde arriba, al azimut desde +X; -90 = frente)."""
    d = Vector((math.sin(th) * math.cos(al), math.sin(th) * math.sin(al), math.cos(th)))
    return hacia(CUERPO["cabeza"], centro, d) + d * off


def medida_cabeza(z):
    b = CUERPO["cabeza"]
    ancho = max((hacia(b, Vector((0, y, z)), Vector((1, 0, 0))).x for y in (-0.25, -0.1, 0.05, 0.2)), default=0.0)
    fondo = max(max(-hacia(b, Vector((x, 0, z)), Vector((0, -1, 0))).y, hacia(b, Vector((x, 0, z)), Vector((0, 1, 0))).y) for x in (-0.2, 0.0, 0.2))
    return ancho, fondo


def gorro(zb, rx, ry, s=S_GORRO):
    """Lleva un gorro disenado con el borde en (0, 0, zb) y radios interiores rx, ry a la cupula de la v5."""
    a, b = rx * s - 0.02, ry * s - 0.02
    d = b * math.sin(-INCLINACION)
    zc = FRENTE_MIN - d
    while zc < 5.2:
        if medida_cabeza(zc)[0] <= a and medida_cabeza(zc)[1] <= b and medida_cabeza(zc - d)[1] <= b * math.cos(INCLINACION):
            break
        zc += 0.005
    return Matrix.Translation((0, 0, zc)) @ Matrix.Rotation(INCLINACION, 4, "X") @ Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation((0, 0, -zb))


def mover(desde, hasta, s):
    return Matrix.Translation(hasta) @ Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation(-Vector(desde))


def espalda():
    yb = superficie(0.0, Z_ESPALDA, 1)[0].y
    return mover((0, YB4, ZC4), (0, yb, Z_ESPALDA), S_ESPALDA)


def encajar(p, T):
    Ti = T.inverted()
    R3i = Ti.to_3x3()
    nuevas = []
    for bm, rol, ang in p.parts:
        bmesh.ops.transform(bm, matrix=T, verts=bm.verts)
        if T.to_3x3().determinant() < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
        if callable(rol):
            rol = (lambda f: lambda c, n: f(Ti @ c, (R3i @ n).normalized()))(rol)
        nuevas.append((bm, rol, ang))
    p.parts = nuevas


def anillo_cuerpo(z, off, n=28):
    pts = []
    for j in range(n):
        a = 2 * math.pi * j / n
        d = Vector((math.cos(a), math.sin(a), 0.0))
        loc, _, _, _ = CUERPO["bvh"].ray_cast(Vector((0, 0, z)) + d * 3.0, -d)
        pts.append(loc + d * off)
    return pts


def lamina(ext, inn):
    bm = bmesh.new()
    E = [[bm.verts.new(p) for p in fila] for fila in ext]
    I = [[bm.verts.new(p) for p in fila] for fila in inn]
    R, C = len(ext), len(ext[0])
    for i in range(R - 1):
        for j in range(C - 1):
            bm.faces.new((E[i][j], E[i + 1][j], E[i + 1][j + 1], E[i][j + 1]))
            bm.faces.new((I[i][j], I[i][j + 1], I[i + 1][j + 1], I[i + 1][j]))
    for i in (0, R - 1):
        for j in range(C - 1):
            bm.faces.new((E[i][j], E[i][j + 1], I[i][j + 1], I[i][j]))
    for j in (0, C - 1):
        for i in range(R - 1):
            bm.faces.new((E[i][j], I[i][j], I[i + 1][j], E[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def estrella(R, r, n=5, giro=90.0):
    return [((R if k % 2 == 0 else r) * math.cos(math.radians(giro + 180.0 * k / n)),
             (R if k % 2 == 0 else r) * math.sin(math.radians(giro + 180.0 * k / n))) for k in range(2 * n)]


def correa(p, z, color="navy"):
    pts = anillo_cuerpo(z, 0.03)
    p.add(tube(pts, lambda u: (0.065, 0.022), k=4, steps=1, closed=True, up=(0, 0, 1), phase=0.5), color, 60)


def item(nombre, parte, presupuesto=1600):
    return Prop(nombre, None, presupuesto, hat={"zb": None, "parte": parte})


# ---------------------------------------------------------------- Cabeza

def p_casco_vikingo():
    zb, k = 4.34, 0.74
    p = item("CascoVikingo", "Head")
    prof = [(0.745, zb, k), (0.752, zb + 0.05, k), (0.752, zb + 0.15, k), (0.738, zb + 0.18, k), (0.70, zb + 0.34, 0.75),
            (0.60, zb + 0.52, 0.77), (0.43, zb + 0.66, 0.78), (0.22, zb + 0.74, 0.78), (0.0, zb + 0.76)]

    def rol(c, n):
        if n.z < -0.95 and c.z < zb + 0.006:
            return "ddark"
        return "gold" if c.z < zb + 0.168 else "lmetal"
    p.add(elathe(prof, 24, a0=math.radians(-90)), rol, 40)
    cresta = []
    for r_, z_, *kk in prof[3:]:
        ky = kk[0] if kk else 0.78
        for s in (-1, 1):
            cresta.append((s, Vector((0.0, s * ky * r_, z_))))
    lado = sorted([q for s, q in cresta if s < 0], key=lambda q: q.y) + sorted([q for s, q in cresta if s > 0 and q.y > 1e-6], key=lambda q: q.y)
    lado = [q + Vector((0, q.y, q.z - zb - 0.17)).normalized() * 0.012 for q in lado]
    p.add(tube(lado, lambda u: (0.055, 0.03), k=6, steps=2, up=(1, 0, 0)), "gold", 50)
    for j in range(14):
        a = math.radians(-90 + 360 * j / 14)
        p.add(ico(0.026, (0.762 * math.cos(a), 0.762 * k * math.sin(a), zb + 0.085)), "lmetal", 70)
    for sx in (-1, 1):
        cuerno = [Vector((sx * 0.62, 0.0, zb + 0.30)), Vector((sx * 0.86, -0.02, zb + 0.36)), Vector((sx * 1.03, -0.05, zb + 0.52)),
                  Vector((sx * 1.10, -0.09, zb + 0.75)), Vector((sx * 1.04, -0.12, zb + 0.95))]
        p.add(tube(cuerno, lambda u: 0.135 * (1 - u) ** 0.85 + 0.008, k=10, steps=3, up=(0, 1, 0)), "cream2", 60)
        t = (cuerno[1] - cuerno[0]).normalized()
        p.add(cyl(0.155, 0.07, m=Matrix.Translation(cuerno[0] + t * 0.1) @ frame_from_normal(t), seg=12, center=True), "gold", 40)
    encajar(p, gorro(zb, 0.745, 0.745 * k))
    return p


def p_chistera():
    p = item("Chistera", "Head", 900)
    m = Matrix.Translation((0.12, 0.0, 4.59)) @ Matrix.Rotation(math.radians(13), 4, "Y") @ Matrix.Rotation(math.radians(5), 4, "X")
    p.add(lathe([(0.20, 0.0), (0.355, 0.004), (0.37, 0.03), (0.20, 0.036)], 20, m, sy=0.88, closed=True), "black", 40)
    p.add(lathe([(0.0, 0.03), (0.205, 0.03), (0.222, 0.47), (0.0, 0.47)], 16, m, sy=0.88), "black", 40)
    p.add(lathe([(0.212, 0.04), (0.222, 0.15)], 16, m, sy=0.88, cap0=False, cap1=False), "red", 40)
    p.add(decal(rrect(0, 0.095, 0.07, 0.07, 0.012, 1), m @ Matrix.Translation((0, -0.88 * 0.218, 0)) @ Matrix.Rotation(math.radians(90), 4, "X"), 0.012), "gold")
    encajar(p, mover((0.12, 0.0, 4.60), (0.09, 0.03, 5.04), 0.85))
    return p


def p_gorro_pez():
    p = item("GorroPez", "Head", 1500)
    zc = 4.88
    m = Matrix.Translation((0, -0.74, zc)) @ Matrix.Rotation(math.radians(-90), 4, "X")
    prof = [(0.0, -0.02), (0.15, 0.0), (0.28, 0.12), (0.38, 0.35), (0.42, 0.6), (0.40, 0.85), (0.30, 1.12), (0.16, 1.35), (0.09, 1.5)]

    def rol(c, n):
        if c.z < zc - 0.13 and n.z < 0.2:
            return "white"
        if 0.08 < c.y < 0.2 or 0.42 < c.y < 0.52:
            return "dfish"
        return "fish"
    p.add(lathe(prof, 16, m, sy=0.78), rol, 55)
    labio = [Vector((0.13 * math.cos(a), -0.745, zc + 0.10 * math.sin(a))) for a in (2 * math.pi * j / 12 for j in range(12))]
    p.add(tube(labio, lambda u: 0.045, k=6, steps=1, closed=True, up=(0, -1, 0)), "pink", 60)
    p.add(decal(circ(0, 0, 0.1, 10), fr((0, -0.768, zc), "-y"), 0.0), "ddark")
    for sx in (-1, 1):
        p.add(ellipsoid((0.12, 0.12, 0.12), Matrix.Translation((sx * 0.25, -0.46, zc + 0.11)), 10, 7), "white", 60)
        p.add(ellipsoid((0.055, 0.055, 0.055), Matrix.Translation((sx * 0.31, -0.54, zc + 0.12)), 8, 5), "black", 60)
        p.add(ellipsoid((0.04, 0.17, 0.11), Matrix.Translation((sx * 0.40, -0.05, zc - 0.17)) @ Matrix.Rotation(math.radians(sx * 25), 4, "Y"), 6, 4), "flame", 60)
    yz = frame((0, 0, 0), (0, 1, 0), (0, 0, 1))
    p.add(prism([(0.70, zc + 0.02), (1.14, zc + 0.36), (1.02, zc + 0.02), (1.14, zc - 0.30)], 0.06, yz, bev=0.012), "flame", 35)
    p.add(prism([(-0.25, zc + 0.28), (0.32, zc + 0.30), (0.05, zc + 0.55)], 0.05, yz, bev=0.01), "flame", 35)
    encajar(p, mover((0, 0, 4.56), (0, 0, 4.99), 0.78))
    return p


def p_gorro_platano():
    p = item("GorroPlatano", "Head", 2000)
    centro = Vector((0.0, 0.0, 4.55))

    def fin_para(al, z_fin):
        th = 0.05
        while th < 1.5 and cabeza_dir(th, al, 0.0, centro).z > z_fin:
            th += 0.01
        return th
    R, C = 8, 6
    for al_deg, z_fin in ((-135, 4.86), (-45, 4.86), (45, 4.48), (135, 4.48)):
        al0 = math.radians(al_deg)
        fin = fin_para(al0, z_fin)
        for t0, t1, color in ((0.0, 0.86, "banana"), (0.86, 1.0, "brown")):
            ext, inn = [], []
            for i in range(R):
                t = t0 + (t1 - t0) * i / (R - 1)
                th = 0.04 + (fin - 0.04) * t
                hw = 0.5 * (1.0 - 0.3 * t) * min(1.0, 0.35 + t * 2.0)
                off = 0.06 + 0.16 * t ** 3
                fe, fi = [], []
                for j in range(C):
                    al = al0 + hw * (2.0 * j / (C - 1) - 1.0)
                    curva = 0.04 * (1.0 - (2.0 * j / (C - 1) - 1.0) ** 2)
                    fe.append(cabeza_dir(th, al, off + curva + 0.03, centro))
                    fi.append(cabeza_dir(th, al, off + curva, centro))
                ext.append(fe)
                inn.append(fi)
            p.add(lamina(ext, inn), lambda c, n, col=color: col if n.dot(c - centro) > 0 else "cream2", 55)
    cima = cabeza_dir(0.0, 0.0, 0.0, centro).z
    fruta = [Vector((0, 0, cima - 0.04)), Vector((0.016, 0.0, cima + 0.22)), Vector((0.065, 0.016, cima + 0.42)), Vector((0.135, 0.03, cima + 0.55))]
    p.add(tube(fruta, lambda u: 0.12 - 0.055 * u ** 1.5, k=10, steps=3, up=(0, 1, 0)), "cream2", 55)
    p.add(ellipsoid((0.056, 0.056, 0.04), Matrix.Translation(fruta[-1] + Vector((0.005, 0, 0.005))) @ frame_from_normal(Vector((0.5, 0.1, 0.8))), 8, 5), "brown", 60)
    return p


def p_auriculares2():
    p = item("Auriculares2", "Head", 900)
    s = 0.9
    yc, zc = -0.06, 4.21
    tau = math.radians(10)
    for sx in (-1, 1):
        u = Vector((sx * math.cos(tau), 0, math.sin(tau)))
        org = Vector((sx * 0.58, yc, zc))
        m = frame(org, (0, 1, 0), u.cross(Vector((0, 1, 0)))) @ Matrix.Diagonal((s, s, s, 1.0))
        p.add(lathe([(0.0, 0.215), (0.245, 0.215), (0.245, 0.0), (0.355, 0.0), (0.38, 0.05), (0.38, 0.115)], 12, m, cap0=False, cap1=False, a0=0.0), "rubber", 50)
        p.add(lathe([(0.38, 0.115), (0.40, 0.135), (0.40, 0.27)], 12, m, cap0=False, cap1=False, a0=0.0), "orange", 50)
        p.add(lathe([(0.40, 0.27), (0.30, 0.30), (0.0, 0.312)], 12, m, cap0=False, cap1=False, a0=0.0), "cream", 30)
        p.add(decal(circ(0, 0, 0.17, 12), m, 0.312), "teal")
    centro = Vector((0.0, yc, zc))

    def arco(off, n=11):
        pts = []
        a0 = math.radians(22)
        for i in range(n):
            a = a0 + (math.pi - 2 * a0) * i / (n - 1)
            d = Vector((math.cos(a), 0.0, math.sin(a)))
            pts.append(hacia(CUERPO["cabeza"], centro, d) + d * off(a))
        return pts
    p.add(tube(arco(lambda a: 0.17), lambda u: (0.13, 0.045), k=6, steps=1, up=(0, 1, 0), caps=False), "teal", 60)
    p.add(tube(arco(lambda a: 0.19 + 0.16 * math.sin(a) ** 2), lambda u: 0.024, k=4, steps=1, up=(0, 1, 0), caps=False, phase=0.5), "metal", 60)
    return p


def p_casco_bombero():
    zb, k = 4.34, 0.75
    p = item("CascoBombero", "Head")
    prof = [(0.74, zb, k), (0.745, zb + 0.06, k), (0.735, zb + 0.25, 0.76), (0.68, zb + 0.45, 0.78), (0.55, zb + 0.62, 0.80),
            (0.33, zb + 0.73, 0.80), (0.0, zb + 0.77)]
    p.add(elathe(prof, 24, a0=math.radians(-90)), hat_role("red", "ddark", zb), 45)
    cresta = [Vector((0.0, s * kk * r_, z_)) for s in (-1, 1) for r_, z_, kk in prof[1:6]]
    cresta = sorted(cresta, key=lambda q: q.y)
    top = Vector((0, 0, zb + 0.77))
    cresta = [q for q in cresta if q.y < 0] + [top] + [q for q in cresta if q.y > 0]
    cresta = [q + Vector((0, q.y, q.z - zb - 0.2)).normalized() * 0.02 for q in cresta]
    p.add(tube(cresta, lambda u: (0.05, 0.075), k=6, steps=2, up=(1, 0, 0)), "dred", 50)
    filas = []
    for t in (0.0, 0.5, 1.0):
        fila = []
        for j in range(24):
            a = math.radians(-90 + 15 * j)
            atras = max(0.0, math.sin(a))
            xi, yi = 0.735 * math.cos(a), 0.735 * k * math.sin(a)
            d = (0.10 + 0.42 * atras ** 1.5) * t
            nrm = Vector((math.cos(a), math.sin(a) / k, 0)).normalized()
            z = zb + 0.035 - 0.17 * t * atras ** 2 + 0.03 * t * math.cos(a) ** 2
            fila.append((xi + nrm.x * d, yi + nrm.y * d, z))
        filas.append(fila)
    p.add(sheet(filas, 0.04, closed_u=True), lambda c, n: "red" if n.z > -0.3 else "dred", 55)
    z0, z1 = zb + 0.10, zb + 0.52
    y0, y1 = front_y(prof, 0.0, z0), front_y(prof, 0.0, z1)
    mb = frame((0, y0 - 0.022, z0), (1, 0, 0), Vector((0, y1 - y0, z1 - z0)))
    escudo = [(-0.2, 0.0), (0.2, 0.0), (0.23, 0.27), (0.13, 0.40), (0.0, 0.45), (-0.13, 0.40), (-0.23, 0.27)]
    p.add(prism(escudo, 0.04, mb, bev=0.01), "gold", 35)
    p.add(decal(circ(0, 0.22, 0.12, 14), mb, 0.022), "red")
    p.add(decal(rect(-0.02, 0.025, 0.14, 0.30), mb, 0.026), "white")
    p.add(decal([(-0.06, 0.25), (0.0, 0.30), (0.0, 0.26)], mb, 0.026), "white")
    encajar(p, gorro(zb, 0.74, 0.74 * k))
    return p


def p_gorro_cocodrilo():
    zb, k = 4.34, 0.76
    p = item("GorroCocodrilo", "Head", 2000)
    prof = [(0.735, zb, k), (0.75, zb + 0.08, k), (0.74, zb + 0.22, 0.78), (0.68, zb + 0.40, 0.80), (0.52, zb + 0.56, 0.82),
            (0.30, zb + 0.66, 0.84), (0.0, zb + 0.70)]
    p.add(elathe(prof, 20, a0=math.radians(-90)), hat_role("green", "pink", zb), 45)
    zc = 4.52
    m = Matrix.Translation((0, -0.40, zc)) @ Matrix.Rotation(math.radians(90), 4, "X")
    p.add(rr_loft(0.64, 0.25, 0.1, 2, [(0.0, 0.0), (0.0, 0.42), (0.03, 0.62), (0.08, 0.70)], m),
          lambda c, n: "lgreen" if n.z < -0.5 else "green", 40)
    for sx in (-1, 1):
        for i in range(6):
            y = -0.55 - 0.095 * i
            x = sx * (0.27 - 0.012 * i)
            p.add(lathe([(0.032, zc - 0.115), (0.0, zc - 0.19)], 4, M((x, y, 0))), "white", 70)
        p.add(ellipsoid((0.14, 0.13, 0.12), Matrix.Translation((sx * 0.22, -0.30, 4.90)), 10, 6), "green", 60)
        p.add(ellipsoid((0.095, 0.08, 0.085), Matrix.Translation((sx * 0.22, -0.38, 4.95)), 8, 6), "yellow", 60)
        p.add(ellipsoid((0.018, 0.02, 0.06), Matrix.Translation((sx * 0.22, -0.455, 4.955)), 6, 4), "black", 60)
        p.add(ellipsoid((0.04, 0.035, 0.025), Matrix.Translation((sx * 0.08, -1.0, zc + 0.12)), 6, 4), "dgreen", 60)
    for y, z in ((0.10, 4.99), (0.29, 4.93), (0.44, 4.83), (0.55, 4.68)):
        p.add(lathe([(0.075, 0.0), (0.0, 0.13)], 4, Matrix.Translation((0, y, z - 0.02)) @ frame_from_normal(Vector((0, y, z - 4.4)))), "dgreen", 60)
    encajar(p, gorro(zb, 0.735, 0.735 * k))
    return p


def p_nido():
    p = item("NidoPajaro", "Head", 2200)
    sec = [(0.60, 4.40), (0.72, 4.42), (0.79, 4.55), (0.75, 4.70), (0.62, 4.75), (0.54, 4.63)]
    p.add(lathe(sec, 20, sy=0.84, closed=True), "dtan", 50)
    rnd = random.Random(3)
    for j in range(30):
        a = 2 * math.pi * j / 30 + rnd.uniform(-0.1, 0.1)
        r0 = rnd.uniform(0.70, 0.82)
        z = rnd.uniform(4.45, 4.74)
        c = Vector((r0 * math.cos(a), 0.84 * r0 * math.sin(a), z))
        t = Vector((-math.sin(a) + rnd.uniform(-0.5, 0.5), 0.84 * math.cos(a), rnd.uniform(-0.4, 0.4))).normalized()
        L = rnd.uniform(0.3, 0.5)
        p.add(bar(c - t * L / 2, c + t * L / 2, 0.04, 0.04, caps=True), "brown" if j % 2 else "dtan", 70)
    p.add(cyl(0.6, 0.02, (0, 0, 4.68), seg=16, m=Matrix.Diagonal((1, 0.84, 1, 1))), "dtan")
    b = Vector((0.05, 0.08, 4.87))
    p.add(ellipsoid((0.2, 0.24, 0.18), Matrix.Translation(b), 12, 7), "sky", 60)
    p.add(ellipsoid((0.13, 0.12, 0.12), Matrix.Translation(b + Vector((0, -0.12, -0.02))), 8, 5), "white", 60)
    h = b + Vector((0, -0.2, 0.2))
    p.add(ellipsoid((0.14, 0.14, 0.14), Matrix.Translation(h), 10, 7), "sky", 60)
    p.add(lathe([(0.05, 0.0), (0.0, 0.12)], 6, Matrix.Translation(h + Vector((0, -0.12, -0.01))) @ frame_from_normal(Vector((0, -1, -0.15)))), "beak", 50)
    for sx in (-1, 1):
        p.add(ellipsoid((0.028, 0.02, 0.035), Matrix.Translation(h + Vector((sx * 0.065, -0.115, 0.04))), 6, 4), "black", 60)
        p.add(ellipsoid((0.05, 0.15, 0.09), Matrix.Translation(b + Vector((sx * 0.19, 0.03, 0.02))) @ Matrix.Rotation(math.radians(sx * 15), 4, "Y"), 6, 4), "dfish", 60)
    p.add(ellipsoid((0.03, 0.08, 0.03), Matrix.Translation(h + Vector((0, 0.02, 0.15))) @ Matrix.Rotation(math.radians(-40), 4, "X"), 6, 4), "dfish", 60)
    p.add(prism([(0.22, 4.88), (0.42, 5.05), (0.40, 4.92)], 0.12, frame((b.x, 0, 0), (0, 1, 0), (0, 0, 1)), bev=0.01), "dfish", 35)
    p.add(ellipsoid((0.075, 0.075, 0.095), Matrix.Translation((-0.28, 0.12, 4.76)), 8, 6), "white", 60)
    p.add(ellipsoid((0.07, 0.07, 0.09), Matrix.Translation((-0.14, 0.33, 4.75)) @ Matrix.Rotation(math.radians(20), 4, "X"), 8, 6), "lteal", 60)
    encajar(p, gorro(4.40, 0.60, 0.504))
    return p


# ---------------------------------------------------------------- Cara (los marcos rodean los ojos saltones)

def p_gafas_estrella():
    p = item("GafasEstrella", "Head", 1400)
    for sx in (-1, 1):
        e, n = ojo(sx)
        m = Matrix.Translation(e + n * 0.25) @ frame_from_normal(n)
        p.add(plate(estrella(0.39, 0.30), [circ(0, 0, GAFAS, 20)], 0.05, m), "pink", 35)
        p.add(plate(estrella(0.345, 0.283), [circ(0, 0, GAFAS + 0.016, 20)], 0.006, m, 0.05), "yellow", 35)
        xl = (m.to_3x3() @ Vector((1, 0, 0))).normalized()
        a = e + n * 0.27 + xl * (sx * 0.34) + Vector((0, 0, 0.03))
        patilla = [a, Vector((sx * 0.62, -0.52, OJO_Z + 0.02)), Vector((sx * 0.72, -0.30, OJO_Z - 0.04)), Vector((sx * 0.72, -0.12, OJO_Z - 0.08))]
        p.add(tube(patilla, lambda u: 0.024, k=6, steps=3, up=(0, 0, 1)), "pink", 60)
    return p


def p_monoculo():
    p = item("Monoculo", "Head", 1200)
    e, n = ojo(1)
    m = Matrix.Translation(e + n * 0.25) @ frame_from_normal(n)
    p.add(lathe([(GAFAS, 0.0), (GAFAS + 0.05, 0.0), (GAFAS + 0.05, 0.045), (GAFAS, 0.045)], 24, m, closed=True), "gold", 40)
    p.add(lathe([(GAFAS, 0.0), (GAFAS + 0.013, 0.0), (GAFAS + 0.013, 0.012), (GAFAS, 0.012)], 24, m @ Matrix.Translation((0, 0, 0.045)), closed=True), "white", 40)
    xl = (m.to_3x3() @ Vector((1, 0, 0))).normalized()
    yl = (m.to_3x3() @ Vector((0, 1, 0))).normalized()
    a = e + n * 0.27 + xl * 0.22 - yl * 0.21
    s, _ = superficie(0.30, 3.16)
    pts = [a, Vector((0.68, -0.56, 3.96)), Vector((0.64, -0.48, 3.62)), Vector((0.46, -0.44, 3.36)), s + Vector((0, -0.035, 0))]
    p.add(tube(pts, lambda u: 0.013, k=4, steps=4, up=(1, 0, 0)), "gold", 60)
    p.add(ellipsoid((0.045, 0.028, 0.065), Matrix.Translation(s + Vector((0, -0.035, 0))), 6, 4), "gold", 60)
    return p


def p_antifaz():
    p = item("Antifaz", "Head", 1400)
    zc = OJO_Z + 0.03
    centro = Vector((0.0, -0.076, 0.0))
    ext, inn = [], []
    C = 19
    for i in range(C):
        u = -1.0 + 2.0 * i / (C - 1)
        al = math.radians(-90 + 62 * u)
        hh = 0.16 * math.sqrt(max(0.0, 1.0 - u * u)) + 0.02
        top = zc + hh - 0.045 * math.exp(-(u / 0.2) ** 2)
        bot = zc - hh + 0.08 * math.exp(-(u / 0.22) ** 2)
        fe, fi = [], []
        for j in range(5):
            z = bot + (top - bot) * j / 4
            d = Vector((math.cos(al), math.sin(al), 0.0))
            q = hacia(CUERPO["cabeza"], centro + Vector((0, 0, z)), d)
            fe.append(q + d * 0.04)
            fi.append(q + d * 0.012)
        ext.append(fe)
        inn.append(fi)
    p.add(lamina(ext, inn), "black", 50)
    zb = 4.46
    cinta = []
    for g in range(-28, 209, 12):
        al = math.radians(g)
        d = Vector((math.cos(al), math.sin(al), 0.0))
        cinta.append(hacia(CUERPO["cabeza"], Vector((0, -0.04, zb)), d) + d * 0.03)
    p.add(tube(cinta, lambda u: (0.055, 0.016), k=4, steps=2, up=(0, 0, 1), phase=0.5), "black", 60)
    for sx in (-1, 1):
        lado = ext[0 if sx < 0 else -1][2]
        p.add(tube([lado, lado.lerp(cinta[0 if sx > 0 else -1], 0.5) + Vector((sx * 0.02, 0, 0)), cinta[0 if sx > 0 else -1]],
                   lambda u: (0.05, 0.016), k=4, steps=2, up=(0, 0, 1), phase=0.5), "black", 60)
    nudo = hacia(CUERPO["cabeza"], Vector((0, -0.04, zb)), Vector((0, 1, 0))) + Vector((0, 0.05, 0))
    p.add(ellipsoid((0.06, 0.045, 0.055), Matrix.Translation(nudo), 8, 5), "black", 60)
    for sx in (-1, 1):
        cola = [nudo, nudo + Vector((sx * 0.1, 0.08, -0.14)), nudo + Vector((sx * 0.17, 0.12, -0.32))]
        p.add(tube(cola, lambda u: (0.045 - 0.015 * u, 0.014), k=4, steps=3, up=(0, 1, 0), phase=0.5), "black", 60)
    return p


def p_gafas_buceo():
    p = item("GafasBuceo", "Head", 2400)
    for sx in (-1, 1):
        e, n = ojo(sx)
        m = Matrix.Translation(e + n * 0.16) @ frame_from_normal(n)
        p.add(lathe([(GAFAS, 0.0), (GAFAS + 0.07, 0.0), (GAFAS + 0.07, 0.07), (GAFAS + 0.04, 0.12), (GAFAS, 0.12)], 24, m, closed=True), "teal", 35)
        p.add(lathe([(GAFAS - 0.004, 0.115), (GAFAS + 0.045, 0.115), (GAFAS + 0.045, 0.13), (GAFAS - 0.004, 0.13)], 24, m, closed=True), "lteal", 35)
    zb = 4.47
    cinta = []
    for g in range(-30, 211, 12):
        al = math.radians(g)
        d = Vector((math.cos(al), math.sin(al), 0.0))
        cinta.append(hacia(CUERPO["cabeza"], Vector((0, -0.04, zb)), d) + d * 0.035)
    p.add(tube(cinta, lambda u: (0.065, 0.02), k=4, steps=2, up=(0, 0, 1), phase=0.5), "dark", 60)
    for sx in (-1, 1):
        e, n = ojo(sx)
        m = Matrix.Translation(e + n * 0.16) @ frame_from_normal(n)
        xl = (m.to_3x3() @ Vector((1, 0, 0))).normalized()
        a = e + n * 0.22 + xl * (sx * (GAFAS + 0.06))
        b = cinta[0 if sx > 0 else -1]
        p.add(tube([a, a.lerp(b, 0.5) + Vector((sx * 0.06, 0, 0.02)), b], lambda u: (0.06, 0.02), k=4, steps=3, up=(0, 0, 1), phase=0.5), "dark", 60)
    tubo = [Vector((0.80, -0.22, 4.06)), Vector((0.82, -0.08, 4.30)), Vector((0.78, 0.02, 4.62)), Vector((0.66, 0.10, 4.92)), Vector((0.52, 0.15, 5.06))]
    p.add(tube(tubo, lambda u: 0.05, k=8, steps=3, up=(1, 0, 0)), "banana", 50)
    t = (tubo[-1] - tubo[-2]).normalized()
    p.add(cyl(0.068, 0.09, m=Matrix.Translation(tubo[-1]) @ frame_from_normal(t), seg=10, center=True), "flame", 40)
    t0 = (tubo[0] - tubo[1]).normalized()
    p.add(ellipsoid((0.068, 0.068, 0.055), Matrix.Translation(tubo[0] + t0 * 0.02) @ frame_from_normal(t0), 8, 5), "flame", 60)
    return p


# ---------------------------------------------------------------- Espalda

def p_mochila_paracaidas():
    p = item("MochilaParacaidas", "UpperTorso", 1800)
    yb = YB4
    yc = yb + 0.10
    p.add(rr_loft(0.92, 0.40, 0.13, 2, [(0.07, 2.30), (0.0, 2.38), (0.0, 3.20), (0.04, 3.30), (0.12, 3.36)], M((0, yc, 0))), "teal", 40)
    p.add(rr_loft(0.96, 0.44, 0.15, 2, [(0.0, 3.02), (0.0, 3.26), (0.06, 3.34)], M((0, yc + 0.01, 0)), cap0=True), "dteal", 40)
    p.add(rbox((0.62, 0.07, 0.34), (0, yc + 0.22, 2.58), 0.03, 1), "dteal", 40)
    p.add(decal(rrect(0, 0, 0.12, 0.08, 0.02, 1), fr((0, yc + 0.256, 2.73), "+y"), 0.0), "gold")
    m = Matrix.Translation((0, yc + 0.05, 3.33)) @ Matrix.Rotation(math.radians(18), 4, "X")

    def gajos(c, n):
        a = math.atan2(c.y - (yc + 0.05), c.x)
        return "red" if int(math.floor((a + math.pi) / (math.pi / 4))) % 2 else "white"
    p.add(lathe([(0.0, 0.25), (0.13, 0.22), (0.22, 0.12), (0.25, 0.0), (0.0, 0.0)], 16, m), gajos, 45)
    encajar(p, espalda())
    correa(p, Z_CORREA)
    s, n = superficie(0.24, Z_CORREA)
    p.add(lathe([(0.065, 0.0), (0.095, 0.0), (0.095, 0.03), (0.065, 0.03)], 12, Matrix.Translation(s + n * 0.05) @ frame_from_normal(n), closed=True), "red", 40)
    return p


def p_jetpack():
    p = item("Jetpack", "UpperTorso", 2400)
    yb = YB4
    yc = yb + 0.20
    p.add(rbox((0.40, 0.12, 0.86), (0, yb + 0.02, 2.82), 0.03, 1), "dark", 40)
    for sx in (-1, 1):
        x = sx * 0.235
        z0 = 2.38

        def rol(c, n, z0=z0):
            dz = c.z - z0
            if 0.52 < dz < 0.62 or dz > 0.86:
                return "red"
            return "lmetal"
        p.add(lathe([(0.0, z0 - 0.0), (0.12, z0 + 0.03), (0.17, z0 + 0.12), (0.17, z0 + 0.78), (0.12, z0 + 0.88), (0.0, z0 + 0.93)], 14, M((x, yc, 0))), rol, 45)
        p.add(lathe([(0.075, z0 + 0.01), (0.115, z0 - 0.15), (0.10, z0 - 0.16)], 12, M((x, yc, 0)), cap0=False, cap1=False), "steel", 45)
        p.add(lathe([(0.105, z0 - 0.15), (0.09, z0 - 0.27), (0.0, z0 - 0.50)], 12, M((x, yc, 0)), cap0=False), "flame", 45)
        p.add(lathe([(0.065, z0 - 0.15), (0.05, z0 - 0.3), (0.0, z0 - 0.66)], 10, M((x, yc, 0)), cap0=False), "glow", 45)
        aleta = [(0.17, z0 + 0.02), (0.36, z0 - 0.08), (0.36, z0 + 0.06), (0.17, z0 + 0.38)]
        p.add(prism([(sx * u, v) for u, v in aleta], 0.035, frame((x, yc, 0), (1, 0, 0), (0, 0, 1)), bev=0.008), "red", 35)
    encajar(p, espalda())
    correa(p, Z_CORREA, "dark")
    return p


def p_alas_avion():
    p = item("AlasAvion", "UpperTorso", 2400)
    yb = YB4
    yc = yb + 0.13
    zc = 2.98
    p.add(rr_loft(0.50, 0.24, 0.09, 2, [(0.05, 2.62), (0.0, 2.68), (0.0, 3.22), (0.05, 3.28)], M((0, yc, 0))), "white", 40)
    logo(p, fr((0, yc + 0.121, 2.95), "+y"), 0.14, step=0.004, seg=14)
    plano = [(0.0, -0.28), (1.42, -0.12), (1.52, 0.0), (1.44, 0.12), (0.0, 0.26)]
    franja = [(0.25, -0.05), (1.36, 0.0), (1.36, 0.05), (0.25, 0.03)]
    dih = math.radians(8)
    for sx in (-1, 1):
        m = frame((sx * 0.2, yc, zc), (sx * math.cos(dih), 0, math.sin(dih)), (0, sx, 0))

        def rol(c, n):
            if abs(c.x) > 1.42:
                return "teal"
            return "lmetal" if n.z < -0.5 else "white"
        p.add(prism([(u, sx * v) for u, v in plano], 0.075, m, bev=0.02), rol, 35)
        p.add(decal([(u, sx * v) for u, v in franja], m, 0.04), "orange")
        cmot = m @ Vector((0.95, 0.0, -0.11))
        p.add(cyl(0.085, 0.42, (cmot.x, cmot.y + 0.02, cmot.z), (90, 0, 0), seg=10, center=True), "orange", 45)
        p.add(lathe([(0.085, 0.0), (0.05, 0.07), (0.0, 0.1)], 10, Matrix.Translation((cmot.x, cmot.y - 0.19, cmot.z)) @ frame_from_normal(Vector((0, -1, 0)))), "red", 45)
        for g in (0, 90):
            p.add(rbox((0.36, 0.018, 0.05), (cmot.x, cmot.y - 0.27, cmot.z), rot=(0, g + 20, 0)), "dark", 30)
    yz = frame((0, 0, 0), (0, 1, 0), (0, 0, 1))
    p.add(prism([(yc - 0.02, 3.2), (yc + 0.12, 3.2), (yc + 0.2, 3.58), (yc + 0.06, 3.58)], 0.05, yz, bev=0.01), lambda c, n: "teal" if c.z > 3.45 else "orange", 35)
    encajar(p, espalda())
    correa(p, Z_CORREA, "dark")
    return p


def p_flotador_pato():
    p = item("FlotadorPato", "LowerTorso", 2000)
    z, r = 2.18, 0.15
    aro = anillo_cuerpo(z, 0.03 + r, 28)
    centro = Vector((0, 0, z))

    def rol(c, n):
        a = math.degrees(math.atan2(c.y, c.x)) % 360
        return "white" if (a % 90) < 14 else "duck"
    p.add(tube(aro, lambda u: r, k=10, steps=1, closed=True, up=(0, 0, 1)), rol, 45)
    frente = min(aro, key=lambda q: q.y)
    cuello = [frente + Vector((0, 0.02, r * 0.6)), frente + Vector((0, -0.05, r + 0.16)), frente + Vector((0, -0.08, r + 0.28))]
    p.add(tube(cuello, lambda u: 0.09, k=8, steps=2, up=(1, 0, 0)), "duck", 50)
    h = cuello[-1] + Vector((0, -0.02, 0.07))
    p.add(ellipsoid((0.15, 0.14, 0.14), Matrix.Translation(h), 12, 8), "duck", 60)
    p.add(ellipsoid((0.09, 0.105, 0.035), Matrix.Translation(h + Vector((0, -0.14, -0.03))) @ Matrix.Rotation(math.radians(-8), 4, "X"), 8, 5), "beak", 60)
    for sx in (-1, 1):
        p.add(ellipsoid((0.026, 0.022, 0.034), Matrix.Translation(h + Vector((sx * 0.068, -0.11, 0.05))), 6, 4), "black", 60)
    atras = max(aro, key=lambda q: q.y)
    p.add(lathe([(0.08, 0.0), (0.0, 0.17)], 6, Matrix.Translation(atras + Vector((0, 0, r * 0.5))) @ frame_from_normal(Vector((0, 0.6, 0.8)))), "duck", 50)
    return p


def p_llave_gigante():
    p = item("LlaveGigante", "UpperTorso", 1400)
    yb = YB4
    a = Vector((0.58, yb + 0.16, 2.22))
    b = Vector((-0.60, yb + 0.16, 3.72))
    d = (b - a).normalized()
    L = (b - a).length
    m = frame(a, d, Vector((-d.z, 0, d.x)))
    t = 0.09
    p.add(plate(rrect(L * 0.45, 0, L * 0.7, 0.17, 0.06, 2), [], t, m, -t / 2), "lmetal")
    p.add(plate(circ(0.0, 0.0, 0.19, 16), [circ(0.0, 0.0, 0.085, 12)], t, m, -t / 2), "lmetal")
    c = L - 0.04
    arco = [(c + 0.27 * math.cos(math.radians(g)), 0.27 * math.sin(math.radians(g))) for g in range(35, 326, 18)]
    pinza = arco + [(c + 0.27 * math.cos(math.radians(325)), 0.27 * math.sin(math.radians(325))), (c + 0.03, -0.085), (c + 0.03, 0.085)]
    p.add(plate(pinza, [], t, m, -t / 2), "lmetal")
    p.add(rbox((0.55, 0.20, t + 0.03), bev=0.03, m=m @ Matrix.Translation((L * 0.33, 0, 0))), "red", 40)
    for u in (L * 0.18, L * 0.62):
        q = m @ Vector((u, 0, 0))
        p.add(rbox((0.08, 0.13, 0.25), (q.x, q.y, q.z), 0.02, 1, rot=(0, -math.degrees(math.atan2(d.z, d.x)), 0)), "brown", 40)
    encajar(p, espalda())
    correa(p, Z_CORREA, "brown")
    return p


NUEVOS = [p_casco_vikingo, p_chistera, p_gorro_pez, p_gorro_platano, p_casco_bombero, p_gorro_cocodrilo, p_nido,
          p_auriculares2, p_gafas_estrella, p_monoculo, p_antifaz, p_gafas_buceo,
          p_mochila_paracaidas, p_jetpack, p_alas_avion, p_flotador_pato, p_llave_gigante]
# Gorros del kit antiguo: (zb, radio interior x, radio interior y) del borde, para encajarlos en la v5.
VIEJOS = {"p_gorra_piloto": (4.30, 0.742, 0.534), "p_gorro_helice": (4.35, 0.725, 0.522), "p_gorro_chef": (4.33, 0.716, 0.53),
          "p_sombrero_vaquero": (4.28, 0.745, 0.544), "p_gorro_cono": (4.42, 0.60, 0.60), "p_corona": (4.40, 0.66, 0.53),
          "p_gorro_pato": (4.35, 0.705, 0.508)}
VISTA = {"Head": (14, 28), "UpperTorso": (14, 150), "LowerTorso": (22, 28)}
VISTA_CARA = (6, 24)
VISTA_PROPIA = {"AlasAvion": (40, 165), "NidoPajaro": (26, 28)}
CARA = {"GafasEstrella", "Monoculo", "Antifaz", "GafasBuceo"}


# ---------------------------------------------------------------- paleta, Luau, renders

def paleta():
    img = bpy.data.images.new("accesorios_palette", 64, 64, alpha=True)
    px = [0.5] * (64 * 64 * 4)
    for i in range(64):
        r, g, b = K["hex_rgb"](K["PAL"][i][1])
        gx, gy = i % 8, i // 8
        for y in range(gy * 8, gy * 8 + 8):
            for x in range(gx * 8, gx * 8 + 8):
                o = (y * 64 + x) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "accesorios_palette.png")
    img.file_format = "PNG"
    img.save()
    return K["palette_material"](img)


def caja_roblox(mn, mx, piv):
    a, b = mn - piv, mx - piv
    return [round(-b.x, 3), round(a.z, 3), round(a.y, 3)], [round(-a.x, 3), round(b.z, 3), round(b.y, 3)]


def v3(v):
    return "Vector3.new(%s, %s, %s)" % tuple(repr(float(x)) for x in v)


def escribir_luau():
    with open(os.path.join(OUT, "manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    ruta = os.path.join(OUT, "ids_subida.json")
    ids = json.load(open(ruta)) if os.path.exists(ruta) else {}
    L = ["--!strict", "local ModelosAccesorios = {}", "", "ModelosAccesorios.IDS = {"]
    L += ["\t%s = %d," % (e["nombre"], ids[e["nombre"]]) for e in man if e["nombre"] in ids]
    L += ["} :: { [string]: number }", "", "ModelosAccesorios.PARTES = {"]
    L += ['\t%s = "%s",' % (e["nombre"], e["parte"]) for e in man]
    L += ["} :: { [string]: string }", "", "ModelosAccesorios.CAJAS = {"]
    L += ["\t%s = { minimo = %s, maximo = %s }," % (e["nombre"], v3(e["minimo"]), v3(e["maximo"])) for e in man]
    L += ["} :: { [string]: { minimo: Vector3, maximo: Vector3 } }", "", "return ModelosAccesorios", ""]
    with open(os.path.join(RAIZ, "src", "shared", "ModelosAccesorios.luau"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))
    print("LUAU", len(ids), "ids de", len(man))


def trazo(scene, grosor):
    scene.render.use_freestyle = grosor > 0
    if grosor <= 0:
        return
    scene.render.line_thickness_mode = "ABSOLUTE"
    scene.render.line_thickness = grosor
    vl = scene.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("Tinta")
    ls.select_by_visibility = True
    ls.select_by_edge_types = True
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = False
    fs.crease_angle = math.radians(120)
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("Tinta")
    ls.linestyle.color = (0.03, 0.025, 0.02)
    ls.linestyle.thickness = grosor


def miniatura(scene, ob, nombre, parte, mw):
    K["render_setup"](scene, HILOS, 512, 512)
    scene.cycles.samples = 12 if "--rapido" in ARGS else 40
    scene.render.film_transparent = True
    K["world"](scene, "FFF6E8", 0.9)
    K["sun"](3.2, (48, 0, -30), 8)
    scene.view_settings.exposure = -0.1
    trazo(scene, 3.4)
    o = K["inst"]({nombre: ob}, nombre, mw=mw)
    el, az = VISTA_CARA if nombre in CARA else VISTA_PROPIA.get(nombre, VISTA[parte])
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    if nombre in CARA:
        tripulante("Fantasma", {"Head", "Ojos_normal"})
        pts += [Vector((sx * 0.6, -0.6, z)) for sx in (-1, 1) for z in (3.9, 4.9)]
    K["camera_fit"]([], el, az, 50, 0.86, 0.86, pts=pts)
    K["render_to"](os.path.join(MINI, nombre + ".png"))
    K["clear_temp"]()
    trazo(scene, 0)


def tripulante(color, partes=None):
    hechos = K["tripulante"](Matrix(), color)
    for c in hechos:
        n = c.name.split("_Geo")[0]
        c.hide_render = (n.startswith("Ojos_") and n != "Ojos_normal") or (partes is not None and n not in partes)
    return hechos


def hoja_prueba(scene, objs, datos, nombre_hoja, colores):
    rutas = K["tile_paths"](nombre_hoja, len(datos))
    for i, (nombre, parte, off, mw) in enumerate(datos):
        K["render_setup"](scene, HILOS, 400, 450)
        K["studio"](ground=None, sun_rot=(50, 0, -40))
        tripulante(colores[i % len(colores)])
        o = K["inst"](objs, nombre, mw=mw)
        el, az = (8, 150) if parte == "UpperTorso" else ((10, 30) if parte == "LowerTorso" else ((4, 12) if nombre in CARA else (8, 24)))
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if parte == "Head":
            pts += [Vector((sx * 0.75, sy * 0.6, z)) for sx in (-1, 1) for sy in (-1, 1) for z in (3.6, 5.1)]
        else:
            pts += [Vector((sx * 0.8, sy * 0.5, z)) for sx in (-1, 1) for sy in (-1, 1) for z in (1.6, 5.1)]
        cam = K["camera_fit"]([], el, az, 50, 0.86, 0.82, pts=pts)
        K["label"](cam, nombre, 400, 450, px=22)
        K["render_to"](rutas[i])
        K["clear_temp"]()
    cols = 4
    filas = (len(datos) + cols - 1) // cols
    K["composite"](rutas, cols, filas, 1600, 450 * filas, os.path.join(RENDERS, nombre_hoja + ".png"))


HILOS = 4


def main():
    global HILOS
    if "--solo-luau" in ARGS:
        escribir_luau()
        return
    if "--hilos" in ARGS:
        HILOS = int(ARGS[ARGS.index("--hilos") + 1])
    solo = set(ARGS[ARGS.index("--solo") + 1].split(",")) if "--solo" in ARGS else None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    mat = paleta()
    cargar_cuerpo()
    os.makedirs(MINI, exist_ok=True)
    os.makedirs(RENDERS, exist_ok=True)
    objs, datos, man = {}, [], []
    ruta_man = os.path.join(OUT, "manifest.json")
    previo = {e["nombre"]: e for e in json.load(open(ruta_man, encoding="utf-8"))} if os.path.exists(ruta_man) else {}
    for b in NUEVOS:
        p = b()
        if solo and p.name not in solo:
            if p.name in previo:
                man.append(previo[p.name])
            continue
        parte = p.hat["parte"]
        ob, tris, raw, sc, off = K["make_object"](p, mat)
        dim = ob.dimensions
        mn = Vector((off.x - dim.x / 2, off.y - dim.y / 2, off.z))
        mx = Vector((off.x + dim.x / 2, off.y + dim.y / 2, off.z + dim.z))
        minimo, maximo = caja_roblox(mn, mx, PIVOTES[parte])
        print("PIEZA %-18s %-10s tris %5d / %5d %s  caja %s .. %s" % (p.name, parte, tris, p.budget, "OK" if tris <= p.budget else "PASADO", minimo, maximo))
        if "--sin-fbx" not in ARGS:
            K["export_fbx"](ob)
        man.append({"nombre": p.name, "parte": parte, "archivo": p.name + ".fbx", "triangulos": tris, "minimo": minimo, "maximo": maximo})
        objs[p.name] = ob
        datos.append((p.name, parte, off, Matrix.Translation(off)))
    for nombre_fn, (zb, rx, ry) in VIEJOS.items():
        p = K[nombre_fn]()
        if solo and p.name not in solo:
            if p.name in previo:
                man.append(previo[p.name])
            continue
        p.hat = {"zb": None, "parte": "Head"}
        encajar(p, gorro(zb, rx, ry))
        ob, tris, raw, sc, off = K["make_object"](p, mat)
        dim = ob.dimensions
        mn = Vector((off.x - dim.x / 2, off.y - dim.y / 2, off.z))
        mx = Vector((off.x + dim.x / 2, off.y + dim.y / 2, off.z + dim.z))
        minimo, maximo = caja_roblox(mn, mx, PIVOTES["Head"])
        print("PIEZA %-18s %-10s tris %5d  caja %s .. %s" % (p.name, "Head", tris, minimo, maximo))
        if "--sin-fbx" not in ARGS:
            K["export_fbx"](ob)
        man.append({"nombre": p.name, "parte": "Head", "archivo": p.name + ".fbx", "triangulos": tris, "minimo": minimo, "maximo": maximo})
        objs[p.name] = ob
        datos.append((p.name, "Head", off, Matrix.Translation(off)))
    with open(ruta_man, "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=1)
    if "--sin-render" in ARGS:
        return
    for o in objs.values():
        o.hide_render = True
    K["preview_glow"](mat)
    if "--sin-miniaturas" not in ARGS:
        K["PLAYER"]["Fantasma"] = "D8D2C8"
        for nombre, parte, off, mw in datos:
            miniatura(scene, objs[nombre], nombre, parte, mw)
    colores = ["Lavanda", "Lima", "Chicle", "Sol"]
    for k in range(0, len(datos), 8):
        hoja_prueba(scene, objs, datos[k:k + 8], "prueba_%d" % (k // 8 + 1), colores)
    if K["TILE_DIR"]:
        import shutil
        shutil.rmtree(K["TILE_DIR"][0], ignore_errors=True)


main()
