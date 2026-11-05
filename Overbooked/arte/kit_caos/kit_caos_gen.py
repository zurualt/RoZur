import bpy
import bmesh
import math
import os
import json
from mathutils import Vector, Matrix, Euler

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

PAL = [
    ("cream", "FFF4E0"), ("white", "F7F7F2"), ("ink", "1B1B21"), ("pink", "F29BB2"),
    ("goat", "F4EFE4"), ("beard", "CFC4B0"), ("horn", "D9C49A"), ("hoof", "5E4B42"),
    ("red", "D9443A"), ("dred", "9E2A28"), ("yellow", "F6C445"), ("orange", "F27B2B"),
    ("beak", "F5A623"), ("skin", "F5C9A6"), ("blush", "F08F8F"), ("hair", "8A5A34"),
    ("lblue", "A9D8F2"), ("blue", "6FB4E3"), ("dblue", "3F86C6"), ("tear", "6CCBF5"),
    ("mouth", "5A1E2A"), ("milk", "FFFCF2"), ("glass", "D6ECF3"), ("teal", "1FA6A0"),
    ("dteal", "157F7B"), ("nipple", "E8C9A0"), ("lgrey", "D5DAE0"), ("hpink", "E8457A"),
]
IDX = {n: i for i, (n, _) in enumerate(PAL)}


def suv(n):
    i = IDX[n]
    return ((i % 8 + 0.5) / 8.0, (i // 8 + 0.5) / 4.0)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def M(loc=(0, 0, 0), rot=(0, 0, 0)):
    return Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot], "XYZ").to_matrix().to_4x4()


def xf(bm, m):
    if m is None:
        return bm
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    if m.to_3x3().determinant() < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return bm


def frame(origin, ex, ey):
    ex = Vector(ex).normalized()
    ey = Vector(ey).normalized()
    ez = ex.cross(ey).normalized()
    m = Matrix((ex, ey, ez)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


def frame_from_normal(n):
    n = Vector(n).normalized()
    x = Vector((0, 0, 1)).cross(n)
    if x.length < 1e-4:
        x = Vector((1, 0, 0))
    x.normalize()
    y = n.cross(x).normalized()
    return Matrix((x, y, n)).transposed().to_4x4()


def lathe(prof, seg=12, m=None, sx=1.0, sy=1.0, cap0=True, cap1=True, closed=False, a0=None):
    if a0 is None:
        a0 = math.pi / (2 * seg) if seg % 4 == 2 else 0.0
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r < 1e-6:
            rings.append([bm.verts.new((0.0, 0.0, z))])
        else:
            rings.append([bm.verts.new((sx * r * math.cos(a0 + 2 * math.pi * j / seg), sy * r * math.sin(a0 + 2 * math.pi * j / seg), z)) for j in range(seg)])
    n = len(rings)
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
    for i, k in pairs:
        a, b = rings[i], rings[k]
        if len(a) == 1 and len(b) == 1:
            continue
        for j in range(seg):
            j2 = (j + 1) % seg
            if len(a) == 1:
                bm.faces.new((a[0], b[j2], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[j], a[j2], b[0]))
            else:
                bm.faces.new((a[j], a[j2], b[j2], b[j]))
    if not closed:
        if cap0 and len(rings[0]) > 1:
            bm.faces.new(list(reversed(rings[0])))
        if cap1 and len(rings[-1]) > 1:
            bm.faces.new(rings[-1])
    return xf(bm, m)


def cyl(r, h, loc=(0, 0, 0), seg=12, r2=None, bev=0.0):
    rt = r if r2 is None else r2
    prof = [(r - bev, 0.0), (r, bev), (rt, h - bev), (rt - bev, h)] if bev > 0 else [(r, 0.0), (rt, h)]
    return lathe(prof, seg, M(loc))


def palo(p0, p1, r, seg=6, r2=None, cap0=True, cap1=True):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    m = Matrix.Translation(p0) @ q.to_matrix().to_4x4()
    return lathe([(r, 0.0), (r if r2 is None else r2, d.length)], seg, m, cap0=cap0, cap1=cap1)


def ring(p, c, R, rt, seg, role, n=4):
    prof = [(R + rt * math.cos(2 * math.pi * k / n + math.pi / n), rt * math.sin(2 * math.pi * k / n + math.pi / n)) for k in range(n)]
    p.add(lathe(prof, seg, M(c), closed=True), role)


def decal(pts, m=None, w=0.0):
    bm = bmesh.new()
    bm.faces.new([bm.verts.new((x, y, w)) for x, y in pts])
    return xf(bm, m)


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def ellipsoid(radii, mat=Matrix(), u=12, v=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.transform(bm, matrix=mat @ Matrix.Diagonal((*radii, 1.0)), verts=bm.verts)
    return bm


def catmull(points, steps, closed=False):
    n = len(points)
    out = []
    segs = n if closed else n - 1
    for i in range(segs):
        p0 = points[(i - 1) % n] if (closed or i > 0) else points[i]
        p1 = points[i % n]
        p2 = points[(i + 1) % n]
        p3 = points[(i + 2) % n] if (closed or i + 2 < n) else points[(i + 1) % n]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(points[-1].copy())
    return out


def tube(ctrl, rf, k=8, steps=4, up=None, caps=True, cap_rings=2):
    ctrl = [Vector(c) for c in ctrl]
    path = catmull(ctrl, steps)
    n = len(path)
    seglen = [0.0]
    for i in range(1, n):
        seglen.append(seglen[-1] + (path[i] - path[i - 1]).length)
    total = seglen[-1]
    tangents = []
    for i in range(n):
        t = path[1] - path[0] if i == 0 else path[-1] - path[-2] if i == n - 1 else path[i + 1] - path[i - 1]
        tangents.append(t.normalized())
    hint = Vector(up) if up is not None else Vector((0, 0, 1))
    nrm = hint - tangents[0] * hint.dot(tangents[0])
    if nrm.length < 1e-4:
        nrm = Vector((1, 0, 0)) - tangents[0] * tangents[0].x
    nrm.normalize()
    normals = [nrm]
    for i in range(1, n):
        q = tangents[i - 1].rotation_difference(tangents[i])
        normals.append((q @ normals[-1]).normalized())
    bm = bmesh.new()
    rings = []
    for i in range(n):
        r = rf(seglen[i] / total if total > 0 else 0.0)
        b = tangents[i].cross(normals[i]).normalized()
        rings.append([bm.verts.new(path[i] + (normals[i] * math.cos(2 * math.pi * j / k) + b * math.sin(2 * math.pi * j / k)) * r) for j in range(k)])
    for a_i in range(n - 1):
        ra, rb = rings[a_i], rings[a_i + 1]
        for j in range(k):
            bm.faces.new((ra[j], ra[(j + 1) % k], rb[(j + 1) % k], rb[j]))
    if caps:
        for end in (0, n - 1):
            d = -tangents[0] if end == 0 else tangents[-1]
            r_end = rf(0.0 if end == 0 else 1.0)
            b = tangents[end].cross(normals[end]).normalized()
            prev = rings[end]
            for c in range(1, cap_rings + 1):
                phi = (math.pi / 2) * c / cap_rings
                center = path[end] + d * r_end * math.sin(phi)
                if c == cap_rings:
                    pole = bm.verts.new(center)
                    for j in range(k):
                        bm.faces.new((prev[j], prev[(j + 1) % k], pole))
                    break
                rr = r_end * math.cos(phi)
                ring_ = [bm.verts.new(center + (normals[end] * math.cos(2 * math.pi * j / k) + b * math.sin(2 * math.pi * j / k)) * rr) for j in range(k)]
                for j in range(k):
                    bm.faces.new((prev[j], prev[(j + 1) % k], ring_[(j + 1) % k], ring_[j]))
                prev = ring_
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def surf(c, r, d):
    d = Vector(d).normalized()
    p = Vector(c) + Vector((r[0] * d.x, r[1] * d.y, r[2] * d.z))
    return p, Vector((d.x / r[0], d.y / r[1], d.z / r[2])).normalized()


def frente(c, r, x, z):
    u, w = (x - c[0]) / r[0], (z - c[2]) / r[2]
    return surf(c, r, (u, -math.sqrt(max(1.0 - u * u - w * w, 0.0)), w))


def bola(radii, p, n, u=8, v=6):
    return ellipsoid(radii, Matrix.Translation(p) @ frame_from_normal(n), u, v)


def ojo(p, c, r, d, re, rp, brillo=True, u=8, v=6):
    s, n = surf(c, r, d)
    t = Vector((0, -1, 0)) - n * (-n.y)
    t = t.normalized() * re * 0.22 if t.length > 1e-4 else Vector()
    p.add(bola((re, re * 1.1, re * 0.55), s - n * re * 0.15, n, u, v), "white", 60)
    pc = s + n * re * 0.33 + t
    p.add(bola((rp, rp * 1.15, rp * 0.5), pc, n, 6, 4), "ink", 60)
    if brillo:
        fx = frame_from_normal(n)
        p.add(bola((rp * 0.38,) * 3, pc + n * rp * 0.4 + fx.col[1].xyz * rp * 0.45 - fx.col[0].xyz * rp * 0.35, n, 5, 3), "white", 60)


class Prop:
    def __init__(self, name, size, budget):
        self.name = name
        self.size = size
        self.budget = budget
        self.parts = []

    def add(self, bm, role, ang=50.0):
        self.parts.append((bm, role, ang))
        return bm


def finalize(p):
    prims = []
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for bm, role, ang in p.parts:
        ng = [f for f in bm.faces if len(f.verts) > 4]
        if ng:
            bmesh.ops.triangulate(bm, faces=ng, quad_method="BEAUTY", ngon_method="BEAUTY")
        bm.normal_update()
        roles = [role(f.calc_center_median(), f.normal.copy()) if callable(role) else role for f in bm.faces]
        for v in bm.verts:
            for i in range(3):
                mn[i] = min(mn[i], v.co[i])
                mx[i] = max(mx[i], v.co[i])
        prims.append((bm, roles, ang))
    raw = mx - mn
    size = p.size or tuple(raw)
    sc = [size[i] / raw[i] for i in range(3)]
    T = Matrix.Diagonal((sc[0], sc[1], sc[2], 1.0)) @ Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)))
    verts, faces, uvs, nrms = [], [], [], []
    for bm, roles, ang in prims:
        bmesh.ops.transform(bm, matrix=T, verts=bm.verts)
        bm.normal_update()
        bm.verts.index_update()
        base = len(verts)
        verts.extend(v.co.copy() for v in bm.verts)
        cl = math.cos(math.radians(ang))
        for f, r in zip(bm.faces, roles):
            faces.append([base + v.index for v in f.verts])
            uv = suv(r)
            for lp in f.loops:
                ns = Vector()
                for lf in lp.vert.link_faces:
                    if lf.normal.dot(f.normal) >= cl:
                        ns += lf.normal * lf.calc_area()
                nrms.append(ns.normalized() if ns.length > 1e-12 else f.normal.copy())
                uvs.append(uv)
        bm.free()
    tris = sum(len(f) - 2 for f in faces)
    return verts, faces, uvs, nrms, tris, raw, sc


def palette_image():
    img = bpy.data.images.new("caos_palette", 128, 64, alpha=True)
    px = [0.0] * (128 * 64 * 4)
    for i, (_, hx) in enumerate(PAL):
        r, g, b = hex_rgb(hx)
        gx, gy = i % 8, i // 8
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * 128 + x) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "caos_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def palette_material(img):
    mat = bpy.data.materials.new("Caos_Palette")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.6
    return mat


def make_object(p, mat):
    verts, faces, uvs, nrms, tris, raw, sc = finalize(p)
    me = bpy.data.meshes.new(p.name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", [c for uv in uvs for c in uv])
    me.shade_smooth()
    me.normals_split_custom_set([tuple(n) for n in nrms])
    me.materials.append(mat)
    ob = bpy.data.objects.new(p.name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob, tris, raw, sc


def export_fbx(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, ob.name + ".fbx"),
        use_selection=True,
        object_types={"MESH"},
        use_mesh_modifiers=True,
        mesh_smooth_type="OFF",
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="Z",
        axis_up="Y",
        path_mode="COPY",
        embed_textures=True,
        bake_anim=False,
    )


def p_cabra():
    p = Prop("Cabra", None, 1500)
    p.add(ellipsoid((0.5, 0.85, 0.5), Matrix.Translation((0, 0.25, 1.0)), 14, 9), "goat", 60)
    for x in (-0.26, 0.26):
        for y in (-0.28, 0.8):
            p.add(palo((x, y, 0.12), (x, y, 0.85), 0.12, 8, r2=0.14, cap0=False, cap1=False), "goat", 60)
            p.add(lathe([(0.135, 0.0), (0.125, 0.16)], 8, M((x, y, 0)), cap1=False), "hoof")
    p.add(tube([(0, -0.4, 1.2), (0, -0.56, 1.42), (0, -0.68, 1.6)], lambda u: 0.27 - 0.06 * u, 10, 2, caps=False), "goat", 60)
    HC, HR = (0, -0.82, 1.75), (0.29, 0.34, 0.3)
    p.add(ellipsoid(HR, Matrix.Translation(HC), 12, 8), "goat", 60)
    SC, SR = (0, -1.08, 1.62), (0.2, 0.24, 0.19)
    p.add(ellipsoid(SR, Matrix.Translation(SC), 10, 6), "goat", 60)
    s, n = surf(SC, SR, (0, -0.72, 0.7))
    p.add(bola((0.1, 0.065, 0.05), s - n * 0.01, n, 6, 4), "pink", 60)
    p.add(tube([frente(SC, SR, x, z)[0] + Vector((0, -0.006, 0)) for x, z in ((-0.08, 1.57), (0, 1.54), (0.08, 1.57))], lambda u: 0.014, 4, 2, cap_rings=1), "ink")
    for sx in (-1, 1):
        ojo(p, HC, HR, (0.55 * sx, -0.68, 0.42), 0.115, 0.068)
        p.add(tube([(0.12 * sx, -0.82, 1.98), (0.15 * sx, -0.76, 2.16), (0.19 * sx, -0.62, 2.25), (0.22 * sx, -0.48, 2.22)], lambda u: 0.07 - 0.045 * u, 5, 2, cap_rings=1), "horn")
        o, _ = surf(HC, HR, (sx, 0.2, 0.15))
        ex = Vector((sx, 0, -0.75)).normalized()
        p.add(ellipsoid((0.24, 0.07, 0.11), frame(o + ex * 0.16, ex, (0, 1, 0)), 6, 5), "goat", 60)
        p.add(ellipsoid((0.17, 0.04, 0.065), frame(o + ex * 0.18 + Vector((0, -0.04, 0)), ex, (0, 1, 0)), 5, 4), "pink", 60)
    p.add(tube([(0, -1.12, 1.47), (0, -1.15, 1.35), (0, -1.11, 1.23)], lambda u: 0.07 * (1 - u) + 0.018, 5, 2, cap_rings=1), "beard", 60)
    p.add(tube([(0, 1.03, 1.2), (0, 1.15, 1.34), (0, 1.15, 1.46)], lambda u: 0.08 - 0.035 * u, 5, 2, cap_rings=1), "goat", 60)
    return p


def p_gallina():
    p = Prop("Gallina", None, 800)
    p.add(ellipsoid((0.36, 0.44, 0.36), Matrix.Translation((0, 0.08, 0.6)), 10, 7), "white", 60)
    HC, HR = (0, -0.2, 1.0), (0.2, 0.2, 0.22)
    p.add(ellipsoid(HR, Matrix.Translation(HC), 8, 6), "white", 60)
    for y, z, r in ((-0.28, 1.2, 0.065), (-0.19, 1.24, 0.075), (-0.1, 1.2, 0.065)):
        p.add(ellipsoid((0.035, r, r), Matrix.Translation((0, y, z)), 5, 4), "red", 60)
    s, n = surf(HC, HR, (0, -1, 0.05))
    p.add(palo(s - n * 0.02, s + n * 0.15, 0.065, 6, r2=0.0), "beak")
    p.add(ellipsoid((0.035, 0.04, 0.07), Matrix.Translation(s + Vector((0, 0.03, -0.12))), 5, 4), "red", 60)
    for sx in (-1, 1):
        ojo(p, HC, HR, (0.7 * sx, -0.6, 0.25), 0.072, 0.044, False, 6, 4)
        p.add(ellipsoid((0.07, 0.27, 0.17), M((0.35 * sx, 0.13, 0.6), (18, 0, 0)), 8, 5), "cream", 60)
        p.add(palo((0.12 * sx, 0.08, 0.3), (0.12 * sx, 0.06, 0.04), 0.03, 5, cap0=False), "orange")
        for dx in (-0.07, 0, 0.07):
            p.add(palo((0.12 * sx, 0.06, 0.03), (0.12 * sx + dx, -0.1, 0.02), 0.022, 4, cap0=False), "orange")
    for a in (-22, 0, 22):
        p.add(ellipsoid((0.05, 0.11, 0.2), M((0, 0.46, 0.86), (-30, a, 0)), 6, 4), "white", 60)
    return p


def p_bebe():
    p = Prop("Bebe", None, 900)
    prof = [(0, 0), (0.3, 0), (0.4, 0.07), (0.44, 0.23), (0.41, 0.39), (0.33, 0.5), (0.2, 0.56), (0, 0.58)]
    p.add(lathe(prof, 12, sy=0.85), "lblue", 60)
    ring(p, (0, 0, 0.53), 0.25, 0.065, 12, "white", n=3)
    HZ = 0.77
    HC, HR = (0, -0.02, HZ), (0.3, 0.28, 0.29)
    p.add(ellipsoid(HR, Matrix.Translation(HC), 12, 9), "skin", 60)
    for sx in (-1, 1):
        o, n = surf(HC, HR, (sx, 0.1, 0))
        p.add(bola((0.06, 0.07, 0.04), o, n, 5, 4), "skin", 60)
        x0, z0 = 0.11 * sx, HZ + 0.04
        p.add(tube([frente(HC, HR, x, z)[0] + frente(HC, HR, x, z)[1] * 0.006 for x, z in ((x0 + 0.045 * sx, z0 + 0.035), (x0 - 0.03 * sx, z0), (x0 + 0.045 * sx, z0 - 0.035))], lambda u: 0.016, 4, 1, cap_rings=1), "ink")
        s, n = frente(HC, HR, 0.16 * sx, HZ - 0.06)
        p.add(lathe([(0, -0.045), (0.03, -0.035), (0.04, -0.01), (0.03, 0.02), (0.012, 0.045), (0, 0.06)], 6, Matrix.Translation(s + n * 0.008) @ frame_from_normal(n) @ M(rot=(-90, 0, 0)), sy=0.5), "tear", 60)
        p.add(ellipsoid((0.075, 0.07, 0.07), Matrix.Translation((0.27 * sx, -0.2, 0.55)), 6, 4), "skin", 60)
    s, n = frente(HC, HR, 0, HZ - 0.12)
    p.add(bola((0.09, 0.075, 0.035), s - n * 0.008, n, 8, 5), "mouth", 60)
    s, n = frente(HC, HR, 0, HZ - 0.155)
    p.add(bola((0.05, 0.03, 0.02), s + n * 0.012, n, 6, 4), "pink", 60)
    p.add(tube([(0, -0.06, HZ + 0.26), (0, -0.08, HZ + 0.34), (0, -0.15, HZ + 0.36), (0, -0.17, HZ + 0.3), (0, -0.12, HZ + 0.27)], lambda u: 0.028 - 0.012 * u, 4, 2, up=(1, 0, 0), cap_rings=1), "hair", 60)
    return p


def p_biberon():
    p = Prop("Biberon", None, 300)
    seg = 10
    a0 = math.radians(270 - 180 / seg)
    p.add(lathe([(0, 0), (0.15, 0), (0.17, 0.03), (0.17, 0.42), (0.17, 0.6)], seg, cap1=False, a0=a0), lambda c, n: "milk" if c.z < 0.42 else "glass")
    inr = 0.17 * math.cos(math.pi / seg)
    m = frame((0, -inr, 0), (1, 0, 0), (0, 0, 1))
    for k, z in enumerate((0.12, 0.19, 0.26, 0.33, 0.4, 0.47)):
        w = 0.04 if k % 2 == 0 else 0.022
        p.add(decal(rect(-w, w, z - 0.006, z + 0.006), m, 0.003), "dteal")
    p.add(lathe([(0.17, 0.58), (0.19, 0.6), (0.195, 0.62), (0.195, 0.7), (0.19, 0.72), (0.15, 0.72)], seg, a0=a0, cap0=False, cap1=False), "teal")
    p.add(lathe([(0.15, 0.72), (0.15, 0.755), (0.075, 0.8), (0.05, 0.9), (0.055, 0.95), (0, 1.0)], seg, a0=a0, cap0=False), "nipple", 55)
    return p


BUILDERS = [p_cabra, p_gallina, p_bebe, p_biberon]


def render_sheet(objs, path):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    world = bpy.data.worlds.new("Fondo")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*lin(hex_rgb("D6EEF7")), 1.0)
    bg.inputs[1].default_value = 0.9
    scene.world = world
    sun = bpy.data.lights.new("Sol", "SUN")
    sun.energy = 3.2
    so = bpy.data.objects.new("Sol", sun)
    so.rotation_euler = (math.radians(50), 0.0, math.radians(-30))
    scene.collection.objects.link(so)
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    scene.render.resolution_x, scene.render.resolution_y = 1200, 900
    scene.render.image_settings.file_format = "PNG"
    for o in objs.values():
        o.hide_render = True
    cell = 2.6
    rows = (-30, 90, 150)
    for i, ob in enumerate(objs.values()):
        s = 2.0 / max(ob.dimensions)
        for j, rz in enumerate(rows):
            o = bpy.data.objects.new(ob.name + "_v", ob.data)
            o.location = (i * cell, 0, -j * cell)
            o.rotation_euler = (0, 0, math.radians(rz))
            o.scale = (s, s, s)
            scene.collection.objects.link(o)
    W, H = cell * len(objs), cell * len(rows)
    c = Vector(((len(objs) - 1) * cell / 2, 0, -(len(rows) - 1) * cell / 2 + 1.0))
    el, az = math.radians(14), math.radians(-10)
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cd = bpy.data.cameras.new("Cam")
    cd.type = "ORTHO"
    cd.ortho_scale = max(W, H * 1200 / 900) * 1.02
    co = bpy.data.objects.new("Cam", cd)
    co.location = c + d * 40
    co.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cd.clip_end = 200
    scene.collection.objects.link(co)
    scene.camera = co
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mat = palette_material(palette_image())
    objs = {}
    manifest = []
    for b in BUILDERS:
        p = b()
        ob, tris, raw, sc = make_object(p, mat)
        objs[p.name] = ob
        print("PIECE %-8s tris %5d / %5d %s  raw %.3f x %.3f x %.3f  fit %.3f %.3f %.3f" % (
            p.name, tris, p.budget, "OK" if tris <= p.budget else "OVER", raw.x, raw.y, raw.z, *sc))
        export_fbx(ob)
        dim = ob.dimensions
        manifest.append({"nombre": p.name, "archivo": p.name + ".fbx", "tamano": [round(dim.x, 3), round(dim.z, 3), round(dim.y, 3)], "triangulos": tris})
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    render_sheet(objs, os.path.join(OUT, "caos_kit.png"))


main()
