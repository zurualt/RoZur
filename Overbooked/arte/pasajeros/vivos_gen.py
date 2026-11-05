import bpy
import bmesh
import colorsys
import json
import math
import os
import sys
from mathutils import Vector, Matrix

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, "vivos")
CARAS = os.path.join(AQUI, "caras")
RAIZ = os.path.dirname(os.path.dirname(AQUI))
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def cargar(ruta):
    with open(ruta, encoding="utf-8") as fh:
        src = fh.read()
    src = src[:src.rstrip().rfind("\nmain()")]
    ns = {"__file__": ruta, "__name__": "generador"}
    exec(compile(src, ruta, "exec"), ns)
    ns["OUT"] = OUT
    return ns


P = cargar(os.path.join(AQUI, "pasajeros_gen.py"))
tube, ellipsoid, cylinder, lathe = P["tube"], P["ellipsoid"], P["cylinder"], P["lathe"]
Face, build_body, cap_shell, hairline = P["Face"], P["build_body"], P["cap_shell"], P["hairline"]
surf_ring, body_pt, body_normal, frame_from_normal, align_z, v_patch = P["surf_ring"], P["body_pt"], P["body_normal"], P["frame_from_normal"], P["align_z"], P["v_patch"]
fix_closed, hex_rgb, lin = P["fix_closed"], P["hex_rgb"], P["lin"]
ARM_CTRL, LEG_CTRL = P["ARM_CTRL"], P["LEG_CTRL"]
ZCT, NECK, WAIST, BOTTOM, r_at = P["ZCT"], P["NECK"], P["WAIST"], P["BOTTOM"], P["r_at"]

PAL = ["FFF4E0", "F27B2B", "1FA6A0", "34383F", "1B1B21", "F7F7F2", "D9443A", "2E4E66",
       "F2C9A0", "C98E62", "8A5A3C", "F2907E", "6BBF59", "3E7D3A", "4A78C9", "F5CD3D",
       "F5A9B8", "D9CCF0", "9AA0A8", "7A4A2A", "E8B83A", "E8508A", "8FD3F4", "C9C6BA",
       "E3A982", "B07650", "70452C", "E06A5C", "7A4FB5", "D5DAE0", "26324A", "D8B98A"]
(CREAM, ORANGE, TEAL, DARK, BLACK, WHITE, RED, GLASS, SK1, SK2, SK3, SKQ, GREEN, DGREEN, BLUE, YELLOW,
 PINK, LILAC, GREY, BROWN, GOLD, HOTPINK, SKY, TAPE, SK1D, SK2D, SK3D, SKQD, PURPLE, SILVER, NAVY, TAN) = range(32)
PIELES = [SK1, SK2, SK3, SKQ, SK1D, SK2D, SK3D, SKQD]
VARIANTES = {
    "Verde": lambda h, s, v: (0.27, 0.5, min(1.0, v * 0.92 + 0.04)),
    "Rojo": lambda h, s, v: (0.01, 0.62, min(1.0, v * 1.02 + 0.06)),
    "Palido": lambda h, s, v: (0.58, 0.1, min(1.0, v * 1.12 + 0.12)),
}
CARD_PHI, CARD_Z0, CARD_Z1, EZ = 0.56, 3.335, 3.775, 3.99

PIEZAS = []


def color_variante(hx, variante):
    r, g, b = hex_rgb(hx)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if variante == "Normal":
        return (r, g, b)
    return colorsys.hsv_to_rgb(*VARIANTES[variante](h, s, v))


def paleta(variante, ruta):
    w, h = 128, 64
    img = bpy.data.images.new("Paleta" + variante, w, h, alpha=True)
    px = [0.0] * (w * h * 4)
    for i, hx in enumerate(PAL):
        rgb = color_variante(hx, variante) if i in PIELES else hex_rgb(hx)
        gx, gy = i % 8, i // 8
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * w + x) * 4
                px[o:o + 4] = (*rgb, 1.0)
    img.pixels = px
    img.filepath_raw = ruta
    img.file_format = "PNG"
    img.save()
    return img


def mat_imagen(nombre, img):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.6
    return mat


def mat_color(nombre, rgb, rough=0.5):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*lin(rgb), 1.0)
    b.inputs["Roughness"].default_value = rough
    return mat


def assemble(prims):
    V, F, UV, N = [], [], [], []
    for bm, col, ang in prims:
        bm.verts.index_update()
        bm.normal_update()
        cl = bm.faces.layers.int.get("c")
        cos_lim = math.cos(math.radians(ang))
        base = len(V)
        V.extend(v.co.copy() for v in bm.verts)
        for f in bm.faces:
            c = f[cl] if col is None else col
            uv = ((c % 8 + 0.5) / 8.0, (c // 8 + 0.5) / 4.0)
            F.append(tuple(base + v.index for v in f.verts))
            fn = f.normal
            for lp in f.loops:
                ns = Vector()
                for lf in lp.vert.link_faces:
                    if lf.normal.dot(fn) >= cos_lim:
                        ns += lf.normal * lf.calc_area()
                N.append(tuple(ns.normalized() if ns.length > 1e-12 else fn))
                UV.append(uv)
    return V, F, UV, N


def objeto(nombre, V, F, UV, N, mat):
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([tuple(v) for v in V], [], F)
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for i, uv in enumerate(UV):
        uvl.data[i].uv = uv
    for p in me.polygons:
        p.use_smooth = True
    if N:
        me.normals_split_custom_set(N)
    me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def ring_pts(face, cx, cz, rx, rz, off, n=14):
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        loc, nn = face.hit(cx + rx * math.cos(a), cz + rz * math.sin(a))
        out.append(loc + nn * off)
    return out


def slab(sx, sy, sz, m, bev=0.02):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    if bev > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bev, segments=1, affect="EDGES")
    bmesh.ops.transform(bm, matrix=m @ Matrix.Diagonal((sx, sy, sz, 1.0)), verts=bm.verts)
    return bm


def en_cara(face, x, z, off):
    loc, n = face.hit(x, z)
    return Matrix.Translation(loc + n * off) @ frame_from_normal(n), loc, n


def nariz_bola(face, add, z, radios, col, off=0.06):
    m, _, _ = en_cara(face, 0.0, z, off)
    add("Cuerpo", ellipsoid(radios, m, 12, 8), col)
    return m


def ab_cuerpo(face, add, sp):
    add("Cuerpo", cap_shell(hairline(0.9, 0.3, -0.22), 0.06, lambda th, r: LILAC, rows=5), None)
    rulos = [(0.82, -145), (0.82, -112), (0.82, -68), (0.82, -35), (1.1, -125), (1.1, -90), (1.1, -55), (1.35, -90),
             (1.35, 90), (1.05, 70), (1.05, 110), (0.75, 55), (0.75, 125)]
    for i, (e, th) in enumerate(rulos):
        t = math.radians(th)
        p = body_pt(t, e, 0.12)
        tang = (body_pt(t + 0.05, e, 0.12) - body_pt(t - 0.05, e, 0.12)).normalized()
        add("Cuerpo", cylinder(0.085, 0.3, Matrix.Translation(p) @ align_z(tang), 10), PINK if i % 2 == 0 else SKY)
    for k in range(8):
        t = 2 * math.pi * k / 8
        pts = [body_pt(t, e, 0.18) for e in (0.62, 0.9, 1.15, 1.4, 1.57)]
        add("Cuerpo", tube(pts, lambda u: 0.016, k=4, steps=3, cap_rings=1), GREY)
    for e in (0.75, 1.15):
        add("Cuerpo", tube(surf_ring(lambda th, e=e: e, 0.18, 24), lambda u: 0.016, k=4, steps=1, closed=True), GREY)
    ex, r = sp["ex"], sp["radio"]
    R = r + 0.07
    lados = []
    for sx in (-1, 1):
        pts = ring_pts(face, sx * ex, EZ, R, R * 0.92, 0.14, 16)
        add("Cuerpo", tube(pts, lambda u: 0.045, k=6, steps=1, closed=True), HOTPINK)
        m, _, _ = en_cara(face, sx * (ex + R * 0.82), EZ + R * 0.75, 0.15)
        add("Cuerpo", ellipsoid((0.12, 0.05, 0.04), m @ Matrix.Rotation(math.radians(sx * 35), 4, "Z"), 8, 4), HOTPINK)
        l0, n0 = face.hit(sx * (ex + R), EZ)
        side = body_pt(math.radians(-90 + sx * 64), 0.4, 0.02)
        add("Cuerpo", tube([l0 + n0 * 0.14, side], lambda u: 0.025, k=4, steps=1, cap_rings=1), HOTPINK)
        lados.append(side)
    a, na = face.hit(-ex + R * 0.9, EZ + 0.02)
    b, nb = face.hit(0.0, EZ + 0.06)
    c, nc = face.hit(ex - R * 0.9, EZ + 0.02)
    add("Cuerpo", tube([a + na * 0.14, b + nb * 0.17, c + nc * 0.14], lambda u: 0.035, k=5, steps=2, cap_rings=1), HOTPINK)
    cadena = [lados[0], body_pt(math.radians(-90 - 60), -0.25, 0.08), body_pt(math.radians(-90 - 25), -0.62, 0.06),
              body_pt(math.radians(-90), -0.72, 0.06), body_pt(math.radians(-90 + 25), -0.62, 0.06),
              body_pt(math.radians(-90 + 60), -0.25, 0.08), lados[1]]
    add("Cuerpo", tube(cadena, lambda u: 0.02, k=4, steps=4, cap_rings=1), GOLD)
    nariz_bola(face, add, 3.79, (0.13, 0.11, 0.1), SK1D, 0.07)
    add("Cuerpo", v_patch(face, 3.3, 2.62, 0.3, 0.03), CREAM)
    for z in (2.45, 2.2, 1.95):
        add("Cuerpo", face.dot(0.0, z, (0.055, 0.055, 0.03), 0.02, 6, 4), YELLOW)
    for k in range(16):
        t = -math.pi / 2 + 2 * math.pi * k / 16
        add("Cuerpo", ellipsoid((0.055, 0.055, 0.055), Matrix.Translation(body_pt(t, -0.26, 0.05)), 6, 4), WHITE)


def ab_brazo(sx, add):
    nombre = "BrazoIzq" if sx > 0 else "BrazoDer"
    h = Vector((sx * 0.5, -1.02, 1.6))
    if sx < 0:
        for ang in (25, -15):
            d = (Matrix.Rotation(math.radians(ang), 3, "Y") @ Vector((0.1, -0.35, 1.0))).normalized()
            add(nombre, cylinder(0.022, 0.85, Matrix.Translation(h + d * 0.3) @ align_z(d), 6, r2=0.008), GREY)
        add(nombre, slab(0.34, 0.05, 0.3, Matrix.Translation(h + Vector((0.0, -0.16, 0.42))) @ Matrix.Rotation(math.radians(-12), 4, "X"), 0.02), RED)
        for z in (0.32, 0.42, 0.52):
            add(nombre, slab(0.34, 0.06, 0.025, Matrix.Translation(h + Vector((0.0, -0.165, z))) @ Matrix.Rotation(math.radians(-12), 4, "X"), 0.0), HOTPINK)
    else:
        c = h + Vector((0.02, -0.12, 0.13))
        add(nombre, ellipsoid((0.17, 0.17, 0.17), Matrix.Translation(c), 12, 8), HOTPINK)
        for k in range(3):
            pts = [c + Vector((0.18 * math.cos(a), 0.18 * math.sin(a) * 0.9, 0.16 * math.sin(a * 2 + k) * 0.6)) for a in [i * 0.6 + k for i in range(7)]]
            add(nombre, tube(pts, lambda u: 0.014, k=4, steps=2, cap_rings=1), RED)


def tu_cuerpo(face, add, sp):
    prof = [(-0.03, 0.55, YELLOW), (-0.07, 0.95, YELLOW), (-0.17, 1.22, YELLOW), (-0.13, 1.27, YELLOW),
            (0.0, 0.99, YELLOW), (0.07, 0.92, TEAL), (0.2, 0.9, YELLOW), (0.45, 0.85, YELLOW), (0.64, 0.7, YELLOW),
            (0.72, 0.4, YELLOW), (0.74, 0.0, YELLOW)]
    m = Matrix.Translation((0, 0.1, 4.3)) @ Matrix.Rotation(math.radians(-22), 4, "X") @ Matrix.Diagonal((1.0, 0.92, 1.0, 1.0))
    add("Cuerpo", lathe(prof, 16, m), None)
    for sx in (-1, 1):
        lm = m @ Matrix.Translation((sx * 0.22, -0.88, 0.32)) @ Matrix.Rotation(math.radians(-8), 4, "X")
        add("Cuerpo", ellipsoid((0.17, 0.05, 0.12), lm, 10, 5), BLACK)
    add("Cuerpo", cylinder(0.03, 0.12, m @ Matrix.Translation((0, -0.92, 0.36)) @ Matrix.Rotation(math.radians(90), 4, "Y"), 6), BLACK)
    nm = nariz_bola(face, add, 3.8, (0.16, 0.14, 0.13), SKQD, 0.09)
    add("Cuerpo", ellipsoid((0.13, 0.04, 0.05), nm @ Matrix.Translation((0, 0.06, 0.1)), 10, 5), WHITE)
    loc, n = face.hit(0.0, 2.78)
    fr = Matrix.Translation(loc + n * 0.11) @ frame_from_normal(n)
    add("Cuerpo", slab(0.4, 0.25, 0.17, fr, 0.035), BLACK)
    add("Cuerpo", cylinder(0.085, 0.12, fr @ Matrix.Translation((0.04, -0.01, 0.12)), 12), DARK)
    add("Cuerpo", cylinder(0.05, 0.02, fr @ Matrix.Translation((0.04, -0.01, 0.185)), 10), GLASS)
    for k in range(14):
        t = -math.pi / 2 + 2 * math.pi * k / 14
        p = body_pt(t, -0.4, 0.08)
        add("Cuerpo", ellipsoid((0.1, 0.1, 0.06), Matrix.Translation(p) @ frame_from_normal(body_normal(t, -0.4)), 8, 4), (HOTPINK, YELLOW, WHITE)[k % 3])


def tu_brazo(sx, add):
    nombre = "BrazoIzq" if sx > 0 else "BrazoDer"
    h = Vector((sx * 0.5, -1.02, 1.6))
    if sx < 0:
        tip = Vector((-0.95, -1.95, 3.55))
        d = (tip - h).normalized()
        add(nombre, cylinder(0.03, (tip - h).length, Matrix.Translation((h + tip) / 2) @ align_z(d), 6), DARK)
        cara = Vector((0.0, -0.55, 4.0))
        nf = (cara - tip).normalized()
        fr = Matrix.Translation(tip) @ frame_from_normal(nf) @ Matrix.Rotation(math.radians(90), 4, "Z")
        add(nombre, slab(0.24, 0.42, 0.045, fr, 0.02), BLACK)
        add(nombre, slab(0.2, 0.36, 0.01, fr @ Matrix.Translation((0, 0, 0.026)), 0.0), SKY)
        add(nombre, cylinder(0.04, 0.03, fr @ Matrix.Translation((0.06, 0.13, -0.03)), 8), WHITE)
    else:
        c = h + Vector((0.0, -0.05, 0.12))
        add(nombre, cylinder(0.1, 0.36, Matrix.Translation(c + Vector((0, 0, 0.14))), 10, r2=0.015), TAN)
        add(nombre, ellipsoid((0.13, 0.13, 0.12), Matrix.Translation(c + Vector((0, 0, 0.36))), 10, 7), PINK)
        add(nombre, ellipsoid((0.04, 0.04, 0.04), Matrix.Translation(c + Vector((0, -0.02, 0.5))), 6, 4), RED)


def ej_cuerpo(face, add, sp):
    add("Cuerpo", cap_shell(hairline(0.95, 0.32, -0.15), 0.05, lambda th, r: BLACK, rows=5), None)
    m = Matrix.Translation(body_pt(math.radians(-95), 1.05, 0.08)) @ Matrix.Rotation(math.radians(-35), 4, "X") @ Matrix.Rotation(math.radians(-10), 4, "Y")
    add("Cuerpo", ellipsoid((0.45, 0.3, 0.17), m, 12, 6), BLACK)
    add("Cuerpo", ellipsoid((0.18, 0.05, 0.03), m @ Matrix.Translation((0.08, -0.22, 0.12)), 8, 4), GREY)
    t = math.radians(0.0)
    p = body_pt(t, 0.36, 0.06)
    n = body_normal(t, 0.36)
    fr = Matrix.Translation(p) @ frame_from_normal(n)
    add("Cuerpo", slab(0.24, 0.48, 0.06, fr, 0.025), BLACK)
    for ang in (38, -38):
        add("Cuerpo", slab(0.12, 0.62, 0.025, fr @ Matrix.Translation((0, 0, 0.045)) @ Matrix.Rotation(math.radians(ang), 4, "Z"), 0.0), TAPE)
    mn, loc, nn = en_cara(face, 0.0, 3.8, 0.02)
    d = (nn + Vector((0, 0, -0.25))).normalized()
    add("Cuerpo", cylinder(0.1, 0.46, Matrix.Translation(loc + d * 0.21) @ align_z(d), 10, r2=0.02), SK2D)
    pts = []
    for x, z in ((-0.24, 3.8), (-0.16, 3.755), (-0.07, 3.75), (0.07, 3.75), (0.16, 3.755), (0.24, 3.8)):
        l, nl = face.hit(x, z)
        pts.append(l + nl * 0.035)
    add("Cuerpo", tube(pts, lambda u: 0.032, k=5, steps=3, cap_rings=1), BLACK)
    add("Cuerpo", v_patch(face, 3.3, 2.62, 0.28, 0.03), WHITE)
    l, n2 = face.hit(0.0, 3.2)
    add("Cuerpo", ellipsoid((0.075, 0.05, 0.06), Matrix.Translation(l + n2 * 0.06) @ frame_from_normal(n2), 8, 5), RED)
    l, n2 = face.hit(0.0, 2.82)
    add("Cuerpo", ellipsoid((0.1, 0.38, 0.03), Matrix.Translation(l + n2 * 0.055) @ frame_from_normal(n2), 8, 5), RED)
    for sx in (-1, 1):
        def lap(u, v, sx=sx):
            return sx * (0.31 * (1 - v) + 0.03 + 0.09 * u), 3.3 - 0.62 * v
        add("Cuerpo", face.patch(lap, 1, 4, 0.035), DARK)
    gm, _, _ = en_cara(face, -0.5, 4.25, 0.02)
    add("Cuerpo", ellipsoid((0.05, 0.07, 0.03), gm, 8, 5), SKY)


def ej_brazo(sx, add):
    nombre = "BrazoIzq" if sx > 0 else "BrazoDer"
    h = Vector((sx * 0.5, -1.02, 1.6))
    if sx < 0:
        fr = Matrix.Translation(h + Vector((0.02, -0.1, 0.2))) @ Matrix.Rotation(math.radians(-30), 4, "X")
        add(nombre, slab(0.2, 0.06, 0.38, fr, 0.02), BLACK)
        add(nombre, slab(0.16, 0.01, 0.3, fr @ Matrix.Translation((0, -0.035, 0)), 0.0), SKY)
    else:
        w = Vector((sx * 0.6, -0.88, 1.72))
        add(nombre, tube(surf_local(w, 0.15), lambda u: 0.03, k=4, steps=1, closed=True), GOLD)


def surf_local(c, r, n=10):
    d = Vector((-0.24, -0.32, -0.12)).normalized()
    fr = Matrix.Translation(c) @ frame_from_normal(d)
    return [fr @ Vector((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), 0)) for k in range(n)]


def ni_cuerpo(face, add, sp):
    gores = [BLUE, YELLOW, RED]
    add("Cuerpo", cap_shell(hairline(0.98, 0.5, 0.18), 0.07, lambda th, r: gores[int(((th + math.pi / 2) % (2 * math.pi)) / (math.pi / 3)) % 3], rows=5), None)
    p = body_pt(math.radians(-90), 0.98, 0.07)
    add("Cuerpo", ellipsoid((0.52, 0.42, 0.045), Matrix.Translation(p + Vector((0, -0.2, -0.02))) @ Matrix.Rotation(math.radians(18), 4, "X"), 14, 5), BLUE)
    top = Vector((0, 0, ZCT + 1.07))
    add("Cuerpo", cylinder(0.04, 0.22, Matrix.Translation(top + Vector((0, 0, 0.08))), 8), DARK)
    nariz_bola(face, add, 3.8, (0.065, 0.055, 0.05), SK1D, 0.04)
    for x, z in ((0.47, 3.8), (0.53, 3.85), (0.52, 3.74), (0.58, 3.79)):
        for sx in (-1, 1):
            add("Cuerpo", face.dot(sx * x, z, (0.025, 0.025, 0.01), 0.004, 6, 3), BROWN)


def ni_helice(add):
    top = Vector((0, 0, ZCT + 1.07 + 0.2))
    add("Helice", ellipsoid((0.07, 0.07, 0.07), Matrix.Translation(top), 8, 6), RED)
    for sgn in (-1, 1):
        m = Matrix.Translation(top + Vector((sgn * 0.26, 0, 0))) @ Matrix.Rotation(math.radians(sgn * 18), 4, "X")
        add("Helice", ellipsoid((0.26, 0.08, 0.022), m, 10, 4), YELLOW)


def ni_brazo(sx, add):
    nombre = "BrazoIzq" if sx > 0 else "BrazoDer"
    h = Vector((sx * 0.5, -1.02, 1.6))
    if sx < 0:
        add(nombre, cylinder(0.035, 0.75, Matrix.Translation(h + Vector((0, -0.05, 0.38))), 8), WHITE)
        c = h + Vector((0, -0.05, 0.98))
        fr = Matrix.Translation(c) @ Matrix.Rotation(math.radians(90), 4, "X")
        for r, col, d in ((0.32, HOTPINK, 0.07), (0.24, WHITE, 0.08), (0.16, YELLOW, 0.09), (0.08, HOTPINK, 0.1)):
            add(nombre, cylinder(r, d, fr, 20), col)


def ni_pierna(sx, add):
    nombre = "PiernaIzq" if sx > 0 else "PiernaDer"
    if sx < 0:
        add(nombre, slab(0.2, 0.06, 0.12, Matrix.Translation((-0.41, -1.45, 0.75)), 0.02), TAPE)


def de_cuerpo(face, add, sp):
    add("Cuerpo", cap_shell(hairline(1.0, 0.4, -0.12), 0.05, lambda th, r: BLACK, rows=4), None)
    band = surf_ring(lambda th: 1.04 - 0.14 * math.sin(th), 0.07, 22)
    add("Cuerpo", tube(band, lambda u: 0.09, k=6, steps=1, closed=True), RED)
    for th, e in ((-35, 0.55), (-150, 0.45), (-28, 0.25)):
        t = math.radians(th)
        n = body_normal(t, e)
        m = Matrix.Translation(body_pt(t, e, 0.03)) @ frame_from_normal(n)
        add("Cuerpo", ellipsoid((0.05, 0.08, 0.03), m, 8, 5), SKY)
    l0, n0 = face.hit(0.0, 3.3)
    pts = [l0 + n0 * 0.015]
    for z in (2.9, 2.5, 2.1, 1.85):
        l, n = face.hit(0.0, z)
        pts.append(l + n * 0.015)
    add("Cuerpo", tube(pts, lambda u: 0.03, k=4, steps=1, cap_rings=1), WHITE)
    add("Cuerpo", tube(surf_ring(lambda th: -0.27, 0.05, 18), lambda u: 0.07, k=5, steps=1, closed=True), BLUE)
    cordon = [body_pt(math.radians(-90 + a), e, 0.08) for a, e in ((-70, -0.3), (-35, -0.55), (0, -0.75), (35, -0.55), (70, -0.3))]
    add("Cuerpo", tube(cordon, lambda u: 0.018, k=4, steps=3, cap_rings=1), GOLD)
    wm, _, _ = en_cara(face, 0.0, 2.55, 0.1)
    add("Cuerpo", cylinder(0.06, 0.2, wm @ Matrix.Rotation(math.radians(90), 4, "Y"), 10), SILVER)
    nm = nariz_bola(face, add, 3.79, (0.15, 0.09, 0.09), SK3D, 0.05)
    for ang in (35, -35):
        add("Cuerpo", slab(0.26, 0.07, 0.02, nm @ Matrix.Translation((0, 0.02, 0.085)) @ Matrix.Rotation(math.radians(ang), 4, "Z"), 0.0), TAPE)


def de_brazo(sx, add):
    nombre = "BrazoIzq" if sx > 0 else "BrazoDer"
    pts = [Vector((sx * (x + 0.14), y, z + 0.03)) for x, y, z in ARM_CTRL[:4]]
    pts[0] = Vector((sx * 0.72, 0.0, 3.17))
    add(nombre, tube(pts, lambda u: 0.03, k=4, steps=3, cap_rings=1), WHITE)
    add(nombre, ellipsoid((0.19, 0.2, 0.24), Matrix.Translation((sx * 0.98, -0.12, 2.6)), 10, 6), BLUE)
    w = Vector((sx * 0.63, -0.86, 1.73))
    add(nombre, tube(surf_local(w, 0.15), lambda u: 0.055, k=5, steps=1, closed=True), RED)
    if sx > 0:
        c = Vector((sx * 0.5, -1.12, 1.78))
        add(nombre, cylinder(0.11, 0.42, Matrix.Translation(c), 12), SKY)
        add(nombre, cylinder(0.07, 0.08, Matrix.Translation(c + Vector((0, 0, 0.25))), 10), WHITE)
        add(nombre, cylinder(0.025, 0.08, Matrix.Translation(c + Vector((0, 0, 0.33))), 6), WHITE)


def ro_cuerpo(face, add, sp):
    spikes = [(-90, 0.9, 0.5, 0.15), (-90, 1.15, 0.7, 0.18), (-90, 1.4, 0.85, 0.2),
              (90, 1.35, 0.85, 0.2), (90, 1.05, 0.72, 0.19), (90, 0.75, 0.6, 0.17), (90, 0.42, 0.45, 0.14), (90, 0.1, 0.32, 0.12)]
    ridge = []
    for i, (th, e, ln, r) in enumerate(spikes):
        p = body_pt(math.radians(th), e, 0.0)
        n = body_normal(math.radians(th), e)
        d = (n + Vector((0, 0.3, 0.25))).normalized()
        add("Cuerpo", cylinder(r, ln, Matrix.Translation(p + d * (ln * 0.5)) @ align_z(d), 7, r2=0.015), GREEN if i % 2 == 0 else DGREEN)
        ridge.append(p + n * 0.02)
    add("Cuerpo", tube(ridge, lambda u: 0.14, k=6, steps=2, cap_rings=2), GREEN)
    add("Cuerpo", v_patch(face, 3.32, 1.75, 0.27, 0.2, 3, 5, 0.02), RED)
    for sx in (-1, 1):
        for z in (3.15, 2.85, 2.55):
            add("Cuerpo", face.dot(sx * (0.27 - 0.05 * (3.3 - z)), z, (0.04, 0.04, 0.03), 0.03, 6, 4), WHITE)
        for k in range(4):
            t = math.radians(-90 + sx * (55 + k * 14))
            n = body_normal(t, -0.45)
            add("Cuerpo", cylinder(0.045, 0.1, Matrix.Translation(body_pt(t, -0.45, 0.05)) @ align_z(n), 6, r2=0.0), SILVER)
        t = math.radians(-90 + sx * 88)
        add("Cuerpo", tube(surf_local(body_pt(t, 0.15, 0.06), 0.06, 10), lambda u: 0.018, k=4, steps=1, closed=True), GOLD)
    nm, loc, nn = en_cara(face, 0.0, 3.82, 0.05)
    add("Cuerpo", ellipsoid((0.11, 0.1, 0.14), nm, 10, 7), SK2D)
    add("Cuerpo", ellipsoid((0.07, 0.07, 0.07), nm @ Matrix.Translation((0, -0.08, 0.09)), 8, 5), SK2D)
    ring = [loc + nn * 0.13 + Vector((0.06 * math.cos(a), 0.0, -0.1 + 0.06 * math.sin(a))) for a in [2 * math.pi * k / 10 for k in range(10)]]
    add("Cuerpo", tube(ring, lambda u: 0.016, k=4, steps=1, closed=True), GOLD)


def ro_brazo(sx, add):
    nombre = "BrazoIzq" if sx > 0 else "BrazoDer"
    w = Vector((sx * 0.63, -0.86, 1.73))
    add(nombre, tube(surf_local(w, 0.15), lambda u: 0.06, k=5, steps=1, closed=True), BLACK)
    d = Vector((-0.24, -0.32, -0.12)).normalized()
    fr = Matrix.Translation(w) @ frame_from_normal(d)
    for k in range(6):
        a = 2 * math.pi * k / 6
        q = fr @ Vector((0.2 * math.cos(a), 0.2 * math.sin(a), 0))
        dd = (q - w).normalized()
        add(nombre, cylinder(0.035, 0.1, Matrix.Translation(q) @ align_z(dd), 5, r2=0.0), SILVER)


def top_stripes(c):
    k = int((NECK - c.z) / 0.25)
    return WHITE if k % 2 == 0 else BLUE


TIPOS = [
    ("PasajeroAbuela", "VivoAbuela", dict(scale=0.945, skin=SK1, top=TEAL, bottom=PURPLE, shoe=PINK, radio=0.22, ceja=WHITE,
                                          cuerpo=ab_cuerpo, brazo=ab_brazo, coronilla=4.85)),
    ("PasajeroTurista", "VivoTurista", dict(scale=0.945, skin=SKQ, top=WHITE, top_fn=top_stripes, bottom=CREAM, shoe=BROWN, sock=WHITE,
                                            extra_z=[NECK - 0.25 * i for i in range(1, 6)], sleeve=0.33, arm_color=WHITE, shorts=0.45,
                                            radio=0.19, ceja=BROWN, cuerpo=tu_cuerpo, brazo=tu_brazo, coronilla=5.15)),
    ("PasajeroEjecutivo", "VivoEjecutivo", dict(scale=0.945, skin=SK2, top=DARK, bottom=DARK, shoe=BLACK, radio=0.17, ceja=BLACK,
                                                cuerpo=ej_cuerpo, brazo=ej_brazo, coronilla=4.8)),
    ("PasajeroNino", "VivoNino", dict(scale=0.70, skin=SK1, top=GREEN, bottom=BLUE, shoe=RED, sleeve=0.33, arm_color=GREEN, shorts=0.5,
                                      radio=0.22, ceja=BROWN, cuerpo=ni_cuerpo, brazo=ni_brazo, pierna=ni_pierna, helice=ni_helice, coronilla=5.0)),
    ("PasajeroDeportista", "VivoDeportista", dict(scale=0.945, skin=SK3, top=BLUE, bottom=DARK, shoe=WHITE, radio=0.19, ceja=BLACK,
                                                  arm_r=0.15, cuerpo=de_cuerpo, brazo=de_brazo, coronilla=4.75)),
    ("PasajeroRockero", "VivoRockero", dict(scale=0.945, skin=SK2, top=BLACK, bottom=BLUE, shoe=BLACK, radio=0.18, ceja=GREEN,
                                            cuerpo=ro_cuerpo, brazo=ro_brazo, coronilla=5.45)),
]
SOMBRA = {SK1: SK1D, SK2: SK2D, SK3: SK3D, SKQ: SKQD}


def construir(sp):
    piezas = {n: [] for n in ("Cuerpo", "BrazoIzq", "BrazoDer", "PiernaIzq", "PiernaDer", "Helice")}

    def add(pieza, bm, col, ang=55.0):
        piezas[pieza].append((fix_closed(bm), col, ang))

    s = sp["scale"]
    floor = BOTTOM - 1.6 / s
    top, bottom, skin = sp["top"], sp["bottom"], sp["skin"]
    sp["ex"] = sp["radio"] + 0.025

    def body_color(c):
        if c.z > NECK:
            return skin
        if c.z > WAIST:
            fn = sp.get("top_fn")
            return fn(c) if fn else top
        return bottom

    body = build_body([NECK, WAIST] + sp.get("extra_z", []), body_color)
    face = Face(body)
    piezas["Cuerpo"].append((body, None, 50.0))
    for sx in (-1, 1):
        brazo = "BrazoIzq" if sx > 0 else "BrazoDer"
        ctrl = [Vector((sx * x, y, z)) for x, y, z in ARM_CTRL]
        sleeve, arm_col, ar = sp.get("sleeve", 1.0), sp.get("arm_color", top), sp.get("arm_r", 0.13)
        add(brazo, tube(ctrl, lambda u: ar - 0.025 * u, k=8, steps=3, cap_rings=2,
                        color_fn=lambda u, sl=sleeve, ac=arm_col: ac if u < sl else skin), None, 50.0)
        hand = Matrix.Translation((sx * 0.50, -1.02, 1.6)) @ Matrix.Rotation(math.radians(-sx * 18), 4, "Z")
        add(brazo, ellipsoid((0.135, 0.175, 0.095), hand, 10, 6), skin, 60.0)
        add(brazo, ellipsoid((0.055, 0.08, 0.055), hand @ Matrix.Translation((-sx * 0.12, -0.04, 0.03)) @ Matrix.Rotation(math.radians(sx * 30), 4, "Z"), 6, 4), skin, 60.0)
        pierna = "PiernaIzq" if sx > 0 else "PiernaDer"
        lctrl = [Vector((sx * x, y, z)) for x, y, z in LEG_CTRL]
        short, sock = sp.get("shorts", 1.0), sp.get("sock")

        def leg_col(u, sh=short, so=sock):
            if u < sh:
                return bottom
            if so is not None and u > 0.8:
                return so
            return skin
        add(pierna, tube(lctrl, lambda u: 0.235 - 0.05 * u, k=8, steps=3, cap_rings=1, color_fn=leg_col), None, 50.0)
        sz = max(floor + 0.155, LEG_CTRL[-1][2] - 0.1)
        shoe = ellipsoid((0.25, 0.38, 0.17), Matrix.Translation((sx * 0.42, -1.35, sz)), 10, 6)
        if s > 0.8:
            for v in shoe.verts:
                v.co.z = max(v.co.z, floor + 0.02)
        add(pierna, shoe, sp["shoe"], 60.0)
        sp["brazo"](sx, add)
        if "pierna" in sp:
            sp["pierna"](sx, add)
    sp["cuerpo"](face, add, sp)
    if "helice" in sp:
        sp["helice"](add)

    T = Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation((0, 0, -BOTTOM))
    for lista in piezas.values():
        for bm, _, _ in lista:
            bmesh.ops.transform(bm, matrix=T, verts=bm.verts)
    carta = tarjeta(face, T)
    datos = anclas(face, sp, T)
    return {k: v for k, v in piezas.items() if v}, carta, datos


def tarjeta(face, T, nu=18, nv=7, off=0.012):
    V, UV, F = [], [], []
    for a in range(nv + 1):
        v = a / nv
        z = CARD_Z0 + (CARD_Z1 - CARD_Z0) * v
        for b in range(nu + 1):
            u = b / nu
            phi = -CARD_PHI + 2 * CARD_PHI * u
            loc, n = face.hit(r_at(z) * math.sin(phi), z)
            V.append(T @ (loc + n * off))
            UV.append((u, v))
    for a in range(nv):
        for b in range(nu):
            i = a * (nu + 1) + b
            F.append((i, i + nu + 1, i + nu + 2, i + 1))
    return V, F, UV


def roblox(v, T=None):
    if T is not None:
        v = T @ v
    return [round(-v.x, 4), round(v.z, 4), round(v.y, 4)]


def anclas(face, sp, T):
    s = sp["scale"]
    r = sp["radio"]
    ojo, n = face.hit(-sp["ex"], EZ)
    boca, nb = face.hit(0.0, 3.56)
    mej, nm = face.hit(-0.38, 3.56)
    d = {
        "escala": s,
        "radio": round(r * s, 4),
        "ojo": roblox(ojo, T),
        "normal": roblox(n),
        "boca": roblox(boca, T),
        "normalBoca": roblox(nb),
        "mejilla": roblox(mej + nm * 0.02, T),
        "coronilla": roblox(Vector((0, 0, sp["coronilla"])), T),
        "hombro": roblox(Vector((-0.74, 0.0, 3.0)), T),
        "cadera": roblox(Vector((-0.36, -0.2, 1.31)), T),
        "mano": roblox(Vector((-0.5, -1.02, 1.6)), T),
    }
    if sp["brazo"] is tu_brazo:
        d["objeto"] = roblox(Vector((-0.95, -1.95, 3.55)), T)
    elif sp["brazo"] is ni_brazo:
        d["objeto"] = roblox(Vector((-0.5, -1.07, 2.58)), T)
    elif sp["brazo"] is ab_brazo:
        d["objeto"] = roblox(Vector((-0.5, -1.2, 2.0)), T)
    d["ceja"] = PAL[sp["ceja"]]
    d["piel"] = {v: [round(c * 255) for c in color_variante(PAL[sp["skin"]], v)] for v in ("Normal", "Verde", "Rojo", "Palido")}
    return d


def caja_roblox(mn, mx):
    return [round(-mx[0], 3), round(mn[2], 3), round(mn[1], 3)], [round(-mn[0], 3), round(mx[2], 3), round(mx[1], 3)]


def v3(v):
    return "Vector3.new(%s)" % ", ".join(("%.4f" % (x + 0.0)).rstrip("0").rstrip(".").replace("-0", "0") if abs(x) < 5e-5 else ("%.4f" % x).rstrip("0").rstrip(".") for x in v)


def escribir_luau(manifest, datos):
    ruta_ids = os.path.join(OUT, "ids_subida.json")
    ids = json.load(open(ruta_ids, encoding="utf-8")) if os.path.exists(ruta_ids) else {}
    L = ["--!strict", "export type Tipo = {", "\tmodelo: string,", "\tescala: number,", "\tradio: number,", "\tojo: Vector3,", "\tnormal: Vector3,",
         "\tboca: Vector3,", "\tnormalBoca: Vector3,", "\tmejilla: Vector3,", "\tcoronilla: Vector3,", "\thombro: Vector3,", "\tcadera: Vector3,",
         "\tmano: Vector3,", "\tobjeto: Vector3?,", "\tceja: Color3,", "\tpiel: { [string]: Color3 },", "}", "",
         "local PasajerosVivos = {}", "", "PasajerosVivos.IDS = {"]
    for e in manifest:
        if e["nombre"] in ids:
            L.append(f"\t{e['nombre']} = {ids[e['nombre']]},")
    L += ["} :: { [string]: number }", "", "PasajerosVivos.CAJAS = {"]
    for e in manifest:
        L.append(f"\t{e['nombre']} = {{ minimo = {v3(e['bbox_min'])}, maximo = {v3(e['bbox_max'])} }},")
    L += ["} :: { [string]: { minimo: Vector3, maximo: Vector3 } }", "", "PasajerosVivos.TIPOS = {"]
    for aspecto, d in datos.items():
        L.append(f"\t{aspecto} = {{")
        L.append(f"\t\tmodelo = \"{d['modelo']}\",")
        for k in ("escala", "radio"):
            L.append(f"\t\t{k} = {d[k]},")
        for k in ("ojo", "normal", "boca", "normalBoca", "mejilla", "coronilla", "hombro", "cadera", "mano", "objeto"):
            if k in d:
                L.append(f"\t\t{k} = {v3(d[k])},")
        L.append(f"\t\tceja = Color3.fromHex(\"{d['ceja']}\"),")
        L.append("\t\tpiel = {")
        for v, c in d["piel"].items():
            L.append(f"\t\t\t{v} = Color3.fromRGB({c[0]}, {c[1]}, {c[2]}),")
        L.append("\t\t},")
        L.append("\t},")
    L += ["} :: { [string]: Tipo }", "", "return PasajerosVivos", ""]
    with open(os.path.join(RAIZ, "src", "shared", "PasajerosVivos.luau"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))
    print("LUAU", len(ids), "ids")


def exportar(objs, ruta):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=ruta, use_selection=True, object_types={"MESH"}, use_mesh_modifiers=True, mesh_smooth_type="OFF",
                             apply_scale_options="FBX_SCALE_UNITS", axis_forward="Z", axis_up="Y", path_mode="COPY", embed_textures=True, bake_anim=False)


EXPRESIONES = {
    "Contento": dict(boca="BocaContento"),
    "Sonrisa": dict(boca="BocaSonrisa", tam=1.08, pupila=1.15, alto=0.04, angulo=-0.15, brazos=(0.0, 2.6)),
    "Enfado": dict(boca="BocaEnfado", abre=0.55, sesgo=0.3, pupila=0.75, alto=-0.05, angulo=0.5, paleta="Rojo"),
    "Grito": dict(boca="BocaGrito", tam=1.3, pupila=0.45, alto=0.1, angulo=-0.4, paleta="Palido", brazos=(-2.4, -2.4)),
    "Mareo": dict(boca="BocaMareo", abre=0.5, angulo=-0.25, paleta="Verde", mejilla=1.0, mirar=((0.6, -0.4), (-0.6, 0.4))),
    "Dormido": dict(boca="BocaDormido", abre=0.07, angulo=-0.1, alto=-0.03),
    "Lengua": dict(boca="BocaLengua", guino=True),
}


def bl(v):
    return Vector((-v[0], v[2], v[1]))


def elip(nombre, radios, base, centro, m):
    ob = bpy.data.objects.new(nombre, bpy.data.meshes.new(nombre))
    bm = ellipsoid(radios, Matrix.Translation(centro) @ base.to_4x4(), 16, 10)
    bm.to_mesh(ob.data)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(m)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def caras(d, M, e, piel, mats):
    E, N, r = bl(d["ojo"]), bl(d["normal"]).normalized(), d["radio"]
    k = r / 0.21
    for lado in (1, -1):
        Ei = M @ Vector((E.x * lado, E.y, E.z))
        Ni = Vector((N.x * lado, N.y, N.z))
        ax = Vector((0, 0, 1)).cross(Ni).normalized()
        ay = Ni.cross(ax).normalized()
        abre = 0.08 if e.get("guino") and lado < 0 else e.get("abre", 1.0)
        tam = e.get("tam", 1.0)
        t = -e.get("sesgo", 0.0) * lado
        base = Matrix((ax * math.cos(t) + ay * math.sin(t), -ax * math.sin(t) + ay * math.cos(t), Ni)).transposed()
        elip("Borde", (r * tam, r * tam * abre, 0.04 * k), base, Ei + Ni * 0.07 * k, mats["negro"])
        elip("Blanco", (0.88 * r * tam, 0.88 * r * tam * max(0.02, abre - 0.1), 0.065 * k), base, Ei + Ni * 0.1 * k, mats["blanco"])
        if abre > 0.3:
            mx, my = e.get("mirar", ((0.0, -0.3), (0.0, -0.3)))[0 if lado > 0 else 1]
            pr = 0.38 * r * tam * e.get("pupila", 1.0)
            c = Ei + Ni * 0.168 * k + (ax * mx + ay * my) * (0.88 * r * tam - pr)
            elip("Pupila", (pr, pr * min(1.0, abre * 1.4), 0.025 * k), base, c, mats["negro"])
        tb = -e.get("angulo", 0.0) * lado
        bb = Matrix((ax * math.cos(tb) + ay * math.sin(tb), -ax * math.sin(tb) + ay * math.cos(tb), Ni)).transposed()
        elip("Ceja", (0.8 * r, 0.17 * r, 0.14 * r), bb, Ei + ay * (r * 1.28 * max(1.0, tam) + e.get("alto", 0.0) * k) + Ni * 0.1 * k, mats["ceja"])
        if e.get("mejilla"):
            mj = bl(d["mejilla"])
            elip("Mejilla", (0.15 * d["escala"],) * 3, Matrix.Identity(3), M @ Vector((mj.x * lado, mj.y, mj.z)), mats["piel"])


def vista(escena, mat):
    import numpy as np
    scene = bpy.context.scene
    P["render_setup"](scene, ground_z=-1.6, ground_size=160, ground_hex="EFE9DC", sun_rot=(52, 6, -30))
    pal = {"Normal": mat}
    for v in VARIANTES:
        pal[v] = mat_imagen("Paleta" + v, bpy.data.images.load(os.path.join(CARAS, "Paleta" + v + ".png")))
    cache = {}

    def mat_boca(nombre, piel):
        if (nombre, piel) not in cache:
            img = bpy.data.images.load(os.path.join(CARAS, nombre + ".png"))
            px = np.array(img.pixels[:]).reshape(-1, 4)
            a = px[:, 3:4]
            px[:, :3] = px[:, :3] * a + np.array(piel) * (1 - a)
            px[:, 3] = 1.0
            nuevo = bpy.data.images.new("I%d" % len(cache), img.size[0], img.size[1])
            nuevo.pixels = px.ravel().tolist()
            m = mat_imagen("M%d" % len(cache), nuevo)
            m.node_tree.nodes["Image Texture"].interpolation = "Linear"
            cache[(nombre, piel)] = m
        return cache[(nombre, piel)]

    for objs, _, _ in escena.values():
        for ob in objs:
            ob.hide_render = True
    filas = [(0.0, ["Contento"] * 6), (16.0, ["Enfado", "Grito", "Mareo", "Dormido", "Sonrisa", "Lengua"])]
    for desp, exprs in filas:
        for i, (aspecto, expr) in enumerate(zip(escena, exprs)):
            objs, d, sp = escena[aspecto]
            e = EXPRESIONES[expr]
            x = desp - 6.25 + 2.5 * i
            M = Matrix.Translation((x, 0, 0))
            pn = e.get("paleta", "Normal")
            piel = tuple(c / 255 for c in d["piel"][pn])
            for ob in objs:
                c = ob.copy()
                c.data = ob.data.copy()
                c.hide_render = False
                corto = ob.name.split("_")[-1]
                c.data.materials[0] = mat_boca(e["boca"], piel) if corto == "Boca" else pal[pn]
                R = Matrix.Identity(4)
                if corto in ("BrazoIzq", "BrazoDer") and "brazos" in e:
                    lado = 1 if corto == "BrazoDer" else -1
                    S = bl(d["hombro"])
                    S = Vector((S.x * lado, S.y, S.z))
                    ang = e["brazos"][0 if lado > 0 else 1]
                    R = Matrix.Translation(S) @ Matrix.Rotation(ang * 0.5, 4, "X") @ Matrix.Rotation(ang * 0.6 * lado, 4, "Y") @ Matrix.Translation(-S)
                c.matrix_world = M @ R
                scene.collection.objects.link(c)
            mats = {"negro": mat_color("n", (0.1, 0.1, 0.12)), "blanco": mat_color("b", (0.97, 0.97, 0.95), 0.3),
                    "ceja": mat_color("c", hex_rgb(d["ceja"])), "piel": mat_color("p", piel)}
            caras(d, M, e, piel, mats)
            objeto("Seat", *assemble(P["seat"](x)), mat)
    P["shoot"](bpy.context.scene, "vivos_1", dict(loc=(0.0, -15.5, 3.4), target=(0.0, 0.0, 1.5), lens=40))
    P["shoot"](bpy.context.scene, "vivos_2", dict(loc=(16.0, -15.5, 3.4), target=(16.0, 0.0, 1.5), lens=40))
    P["shoot"](bpy.context.scene, "vivos_3", dict(loc=(12.5, -7.0, 3.6), target=(12.5, 0.0, 2.6), lens=50))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(OUT, exist_ok=True)
    img = paleta("Normal", os.path.join(OUT, "paleta.png"))
    for v in VARIANTES:
        paleta(v, os.path.join(CARAS, "Paleta" + v + ".png"))
    mat = mat_imagen("PaletaVivos", img)
    mat_boca = mat_color("Boca", (0.95, 0.8, 0.65))
    manifest, datos, escena = [], {}, {}
    for aspecto, modelo, sp in TIPOS:
        piezas, carta, d = construir(dict(sp))
        objs = []
        for nombre, prims in piezas.items():
            objs.append(objeto(nombre, *assemble(prims), mat))
        V, F, UV = carta
        objs.append(objeto("Boca", V, F, [UV[i] for f in F for i in f], None, mat_boca))
        exportar(objs, os.path.join(OUT, modelo + ".fbx"))
        vs = [ob.matrix_world @ v.co for ob in objs for v in ob.data.vertices]
        mn = [min(v[i] for v in vs) for i in range(3)]
        mx = [max(v[i] for v in vs) for i in range(3)]
        bmin, bmax = caja_roblox(mn, mx)
        tris = sum(len(p.vertices) - 2 for ob in objs for p in ob.data.polygons)
        manifest.append({"nombre": modelo, "archivo": modelo + ".fbx", "bbox_min": bmin, "bbox_max": bmax, "triangulos": tris})
        d["modelo"] = modelo
        datos[aspecto] = d
        escena[aspecto] = (objs, d, sp)
        for ob in objs:
            ob.name = modelo + "_" + ob.name
        print("VIVO %-16s tris %5d min %s max %s" % (modelo, tris, bmin, bmax))
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    escribir_luau(manifest, datos)
    if "--norender" in ARGS:
        return
    vista(escena, mat)


main()
