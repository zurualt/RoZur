import bpy
import bmesh
import math
import os
import sys
import json
from mathutils import Vector, Matrix

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
RENDER = "--norender" not in sys.argv
PREVIEW = "--preview" in sys.argv

PAL = ["FFF4E0", "F27B2B", "1FA6A0", "34383F", "1B1B21", "F7F7F2", "D9443A", "2E4E66",
       "F2C9A0", "C98E62", "8A5A3C", "F5A9B8", "6BBF59", "3E7D3A", "4A78C9", "F5CD3D"]
CREAM, ORANGE, TEAL, DARK, BLACK, WHITE, RED, GLASS, SK1, SK2, SK3, SK4, GREEN, DGREEN, BLUE, YELLOW = range(16)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


PRIMS = []


def fix_closed(bm):
    if bm.edges and all(e.is_manifold for e in bm.edges):
        bm.normal_update()
        vol = sum(f.calc_center_median().dot(f.normal) * f.calc_area() for f in bm.faces)
        if vol < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
            print("FLIPPED closed prim", len(bm.faces))
    return bm


def add(bm, color, angle=40.0):
    PRIMS.append((fix_closed(bm), color, angle))
    return bm


def ellipsoid(radii, mat=Matrix(), u=16, v=10):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.transform(bm, matrix=mat @ Matrix.Diagonal((*radii, 1.0)), verts=bm.verts)
    return bm


def cylinder(radius, depth, mat=Matrix(), seg=16, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=radius,
                          radius2=radius if r2 is None else r2, depth=depth)
    bmesh.ops.transform(bm, matrix=mat, verts=bm.verts)
    return bm


def catmull(points, steps, closed=False):
    n = len(points)
    if n < 3 and not closed:
        out = []
        for i in range(n - 1):
            for k in range(steps):
                out.append(points[i].lerp(points[i + 1], k / steps))
        out.append(points[-1])
        return out
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


def tube(ctrl, radius_fn, k=12, steps=6, closed=False, up=None, caps=True, cap_rings=4, color_fn=None):
    path = catmull(ctrl, steps, closed)
    n = len(path)
    seglen = [0.0]
    for i in range(1, n):
        seglen.append(seglen[-1] + (path[i] - path[i - 1]).length)
    total = seglen[-1] + ((path[0] - path[-1]).length if closed else 0.0)
    tangents = []
    for i in range(n):
        if closed:
            t = path[(i + 1) % n] - path[(i - 1) % n]
        elif i == 0:
            t = path[1] - path[0]
        elif i == n - 1:
            t = path[-1] - path[-2]
        else:
            t = path[i + 1] - path[i - 1]
        tangents.append(t.normalized())
    hint = up if up is not None else Vector((0, 0, 1))
    nrm = hint - tangents[0] * hint.dot(tangents[0])
    if nrm.length < 1e-4:
        nrm = Vector((1, 0, 0)) - tangents[0] * tangents[0].x
    nrm.normalize()
    normals = [nrm]
    for i in range(1, n):
        q = tangents[i - 1].rotation_difference(tangents[i])
        normals.append((q @ normals[-1]).normalized())
    bm = bmesh.new()
    cl = bm.faces.layers.int.new("c")
    us = [seglen[i] / total if total > 0 else 0.0 for i in range(n)]
    rings = []
    for i in range(n):
        u = us[i]
        r = radius_fn(u)
        b = tangents[i].cross(normals[i]).normalized()
        rings.append([bm.verts.new(path[i] + (normals[i] * math.cos(2 * math.pi * j / k) + b * math.sin(2 * math.pi * j / k)) * r) for j in range(k)])
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
    for a_i, b_i in pairs:
        ra, rb = rings[a_i], rings[b_i]
        for j in range(k):
            f = bm.faces.new((ra[j], ra[(j + 1) % k], rb[(j + 1) % k], rb[j]))
            if color_fn:
                f[cl] = color_fn(0.5 * (us[a_i] + us[b_i]))
    if caps and not closed:
        for end in (0, n - 1):
            d = -tangents[0] if end == 0 else tangents[-1]
            r_end = radius_fn(0.0 if end == 0 else 1.0)
            b = tangents[end].cross(normals[end]).normalized()
            prev = rings[end]
            for c in range(1, cap_rings + 1):
                phi = (math.pi / 2) * c / cap_rings
                center = path[end] + d * r_end * math.sin(phi)
                if c == cap_rings:
                    pole = bm.verts.new(center)
                    for j in range(k):
                        f = bm.faces.new((prev[j], prev[(j + 1) % k], pole))
                        if color_fn:
                            f[cl] = color_fn(us[end])
                    break
                rr = r_end * math.cos(phi)
                ring = [bm.verts.new(center + (normals[end] * math.cos(2 * math.pi * j / k) + b * math.sin(2 * math.pi * j / k)) * rr) for j in range(k)]
                for j in range(k):
                    f = bm.faces.new((prev[j], prev[(j + 1) % k], ring[(j + 1) % k], ring[j]))
                    if color_fn:
                        f[cl] = color_fn(us[end])
                prev = ring
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def lathe(profile, seg, mat):
    bm = bmesh.new()
    cl = bm.faces.layers.int.new("c")
    rings = []
    for h, r, _ in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((0.0, 0.0, h))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * j / seg), r * math.sin(2 * math.pi * j / seg), h)) for j in range(seg)])
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        col = profile[i][2]
        for j in range(seg):
            if len(a) == 1:
                f = bm.faces.new((a[0], b[(j + 1) % seg], b[j]))
            elif len(b) == 1:
                f = bm.faces.new((a[j], a[(j + 1) % seg], b[0]))
            else:
                f = bm.faces.new((a[j], a[(j + 1) % seg], b[(j + 1) % seg], b[j]))
            f[cl] = col
    bmesh.ops.transform(bm, matrix=mat, verts=bm.verts)
    return bm


def loft(sections, cap_start=True, cap_end=True):
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in s] for s in sections]
    m = len(sections[0])
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(m):
            bm.faces.new((a[j], a[(j + 1) % m], b[(j + 1) % m], b[j]))
    if cap_start:
        bm.faces.new(rings[0])
    if cap_end:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def mirror_x(bm):
    out = bm.copy()
    for v in out.verts:
        v.co.x = -v.co.x
    bmesh.ops.reverse_faces(out, faces=out.faces)
    return out


def orient(bm, ref):
    bm.normal_update()
    flip = [f for f in bm.faces if f.normal.dot(ref(f.calc_center_median())) < 0]
    if flip:
        bmesh.ops.reverse_faces(bm, faces=flip)
    bm.normal_update()
    return bm


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
            uv = ((c % 4 + 0.5) / 4.0, (c // 4 + 0.5) / 4.0)
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


def make_palette_image():
    size = 64
    img = bpy.data.images.new("ModelsPalette", size, size, alpha=True)
    px = [0.0] * (size * size * 4)
    for i, hx in enumerate(PAL):
        rgba = (*hex_rgb(hx), 1.0)
        gx, gy = i % 4, i // 4
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * size + x) * 4
                px[o:o + 4] = rgba
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "models_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def palette_material(img):
    mat = bpy.data.materials.new("ModelsPalette")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.6
    return mat


def build_object(name, prims, mat):
    V, F, UV, N = assemble(prims)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], F)
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for i, uv in enumerate(UV):
        uvl.data[i].uv = uv
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set(N)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def bbox(ob):
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    return [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]


def export_fbx(ob, path):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.export_scene.fbx(
        filepath=path,
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


def render_setup(scene, ground_z=0.0, ground_size=60, ground_hex="EFE9DC", sun_rot=(48, 8, -28), res=(1600, 900)):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16 if PREVIEW else 32
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    scene.cycles.max_bounces = 4
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.render.resolution_x, scene.render.resolution_y = (res[0] // 2, res[1] // 2) if PREVIEW else res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    world = bpy.data.worlds.new("Sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (*lin(hex_rgb("BFE3F2")), 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.85
    scene.world = world
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.2
    sun.angle = math.radians(14)
    so = bpy.data.objects.new("Sun", sun)
    so.rotation_euler = tuple(math.radians(a) for a in sun_rot)
    scene.collection.objects.link(so)
    gm = bpy.data.materials.new("Ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin(hex_rgb(ground_hex)), 1.0)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=ground_size)
    bmesh.ops.translate(bm, vec=(0, 0, ground_z), verts=bm.verts)
    gme = bpy.data.meshes.new("Ground")
    bm.to_mesh(gme)
    gme.materials.append(gm)
    go = bpy.data.objects.new("Ground", gme)
    scene.collection.objects.link(go)
    return go


def camera(scene, loc, target, lens=None, ortho=None):
    cd = bpy.data.cameras.new("Cam")
    cd.clip_end = 2000
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    co = bpy.data.objects.new("Cam", cd)
    scene.collection.objects.link(co)
    co.location = loc
    d = Vector(target) - Vector(loc)
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    scene.camera = co
    return co


def shoot(scene, name, cam):
    co = camera(scene, **cam)
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(co)



from mathutils.bvhtree import BVHTree

ZCB, ZCT, RB, RT, DEPTH = 2.05, 3.55, 0.88, 0.80, 0.86
NECK, WAIST = 3.30, 1.80
BOTTOM = ZCB - 1.0


def r_at(z):
    if z < ZCB:
        return RB * math.sqrt(max(0.0, 1.0 - (ZCB - z) ** 2))
    if z > ZCT:
        return RT * math.sqrt(max(0.0, 1.0 - (z - ZCT) ** 2))
    return RB + (RT - RB) * (z - ZCB) / (ZCT - ZCB)


def frame_from_normal(n):
    n = n.normalized()
    x = Vector((0, 0, 1)).cross(n)
    if x.length < 1e-4:
        x = Vector((1, 0, 0))
    x.normalize()
    y = n.cross(x).normalized()
    return Matrix((x, y, n)).transposed().to_4x4()


def align_z(n):
    return Vector((0, 0, 1)).rotation_difference(n.normalized()).to_matrix().to_4x4()


def build_body(extra_z, color_fn, m=20):
    prof = []
    for i in range(3):
        a = math.radians(-90 + 90 * i / 3)
        prof.append([ZCB + math.sin(a), RB * math.cos(a), i == 0])
    for i in range(4):
        z = ZCB + (ZCT - ZCB) * i / 4
        prof.append([z, r_at(z), False])
    for i in range(8):
        a = math.radians(90 * i / 7)
        prof.append([ZCT + math.sin(a), RT * math.cos(a), i == 7])
    for ez in extra_z:
        near = [p for p in prof if not p[2] and abs(p[0] - ez) < 0.07]
        if near:
            p = min(near, key=lambda p: abs(p[0] - ez))
            p[0], p[1] = ez, r_at(ez)
        else:
            prof.append([ez, r_at(ez), False])
    prof.sort(key=lambda p: p[0])
    bm = bmesh.new()
    cl = bm.faces.layers.int.new("c")
    rings = []
    for z, r, pole in prof:
        if pole or r < 1e-5:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(-math.pi / 2 + 2 * math.pi * j / m), DEPTH * r * math.sin(-math.pi / 2 + 2 * math.pi * j / m), z)) for j in range(m)])
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(m):
            j2 = (j + 1) % m
            if len(a) == 1:
                f = bm.faces.new((a[0], b[j2], b[j]))
            elif len(b) == 1:
                f = bm.faces.new((a[j], a[j2], b[0]))
            else:
                f = bm.faces.new((a[j], a[j2], b[j2], b[j]))
            f[cl] = color_fn(f.calc_center_median())
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def body_pt(th, e, off):
    if e >= 0:
        r = (RT + off) * math.cos(e)
        z = ZCT + (1.0 + off) * math.sin(e)
    else:
        z = ZCT + e
        r = r_at(z) + off
    return Vector((r * math.cos(th), DEPTH * r * math.sin(th), z))


def body_normal(th, e):
    p = body_pt(th, e, 0.0)
    q = body_pt(th, e, 0.05)
    return (q - p).normalized()


def cap_shell(edge_fn, off, color_fn, cols=18, rows=4, lip=0.09):
    bm = bmesh.new()
    cl = bm.faces.layers.int.new("c")
    grid = []
    for i in range(cols):
        th = -math.pi / 2 + 2 * math.pi * i / cols
        e0 = edge_fn(th)
        col = [bm.verts.new(body_pt(th, e0, off - lip))]
        for r in range(rows):
            e = e0 + (math.pi / 2 - e0) * (r / rows) ** 0.9
            col.append(bm.verts.new(body_pt(th, e, off)))
        grid.append((th, col))
    pole = bm.verts.new(body_pt(0.0, math.pi / 2, off))
    for i in range(cols):
        th, a = grid[i]
        _, b = grid[(i + 1) % cols]
        thm = th + math.pi / cols
        for r in range(rows):
            f = bm.faces.new((a[r], b[r], b[r + 1], a[r + 1]))
            f[cl] = color_fn(thm, r)
        f = bm.faces.new((a[rows], b[rows], pole))
        f[cl] = color_fn(thm, rows)
    bm.normal_update()
    score = sum(f.normal.dot(f.calc_center_median() - Vector((0, 0, ZCT - 0.3))) for f in bm.faces)
    if score < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return bm


def hairline(front, side, back, p=1.5):
    def fn(th):
        w = (1.0 - math.sin(th)) / 2.0
        if w >= 0.5:
            return side + (front - side) * ((w - 0.5) * 2.0) ** p
        return back + (side - back) * (w * 2.0) ** (1.0 / p)
    return fn


class Face:
    def __init__(self, body):
        self.tree = BVHTree.FromBMesh(body)

    def hit(self, x, z):
        loc, nrm, _, _ = self.tree.ray_cast(Vector((x, -5.0, z)), Vector((0, 1, 0)))
        return loc, nrm

    def patch(self, fn, nu, nv, off):
        bm = bmesh.new()
        grid = []
        for a in range(nv + 1):
            row = []
            for b in range(nu + 1):
                x, z = fn(b / nu, a / nv)
                loc, n = self.hit(x, z)
                row.append(bm.verts.new(loc + n * off))
            grid.append(row)
        for a in range(nv):
            for b in range(nu):
                bm.faces.new((grid[a][b], grid[a][b + 1], grid[a + 1][b + 1], grid[a + 1][b]))
        return orient(bm, lambda c: Vector((0, -1, 0)))

    def curve(self, pts, radius, off=0.0, k=4, steps=3, taper=0.45):
        ctrl = []
        for x, z in pts:
            loc, n = self.hit(x, z)
            ctrl.append(loc + n * off)
        return tube(ctrl, lambda u: radius * (1.0 - taper + taper * math.sin(math.pi * u)), k=k, steps=steps, cap_rings=2)

    def lens(self, x, z, a, b, off=0.004, dome=0.03, seg=12):
        bm = bmesh.new()
        lc, nc = self.hit(x, z)
        ctr = bm.verts.new(lc + nc * (off + dome))
        ring = []
        for k in range(seg):
            t = 2 * math.pi * k / seg
            l, n = self.hit(x + a * math.cos(t), z + b * math.sin(t))
            ring.append(bm.verts.new(l + n * off))
        for k in range(seg):
            bm.faces.new((ctr, ring[k], ring[(k + 1) % seg]))
        return orient(bm, lambda c: Vector((0, -1, 0)))

    def dot(self, x, z, radii, off=0.0, u=8, v=6):
        loc, n = self.hit(x, z)
        return ellipsoid(radii, Matrix.Translation(loc + n * off) @ frame_from_normal(n), u, v)


ARM_CTRL = [(0.70, 0.02, 3.0), (0.88, 0.0, 2.88), (1.0, -0.14, 2.40), (0.86, -0.56, 1.95), (0.62, -0.88, 1.72)]
LEG_CTRL = [(0.34, -0.15, 1.33), (0.37, -0.72, 1.33), (0.40, -1.12, 1.25), (0.41, -1.22, 0.85), (0.42, -1.22, 0.0), (0.42, -1.2, -0.40)]


def passenger(spec):
    prims = []
    s = spec["scale"]
    floor = BOTTOM - 1.6 / s
    top, bottom, skin = spec["top"], spec["bottom"], spec["skin"]

    def body_color(c):
        if c.z > NECK:
            return skin
        if c.z > WAIST:
            fn = spec.get("top_fn")
            return fn(c) if fn else top
        return bottom

    body = build_body([NECK, WAIST] + spec.get("extra_z", []), body_color)
    face = Face(body)
    prims.append((body, None, 50.0))

    for sx in (-1, 1):
        ctrl = [Vector((sx * x, y, z)) for x, y, z in ARM_CTRL]
        sleeve = spec.get("sleeve", 1.0)
        arm_col = spec.get("arm_color", top)
        prims.append((tube(ctrl, lambda u: 0.13 - 0.025 * u, k=6, steps=2, cap_rings=1,
                           color_fn=lambda u, sl=sleeve, ac=arm_col: ac if u < sl else skin), None, 50.0))
        hand = Matrix.Translation((sx * 0.50, -1.02, 1.6)) @ Matrix.Rotation(math.radians(-sx * 18), 4, "Z")
        prims.append((ellipsoid((0.125, 0.165, 0.085), hand, 8, 5), skin, 60.0))
        prims.append((ellipsoid((0.05, 0.075, 0.05), hand @ Matrix.Translation((-sx * 0.11, -0.04, 0.03)) @ Matrix.Rotation(math.radians(sx * 30), 4, "Z"), 5, 3), skin, 60.0))
        lctrl = [Vector((sx * x, y, z)) for x, y, z in LEG_CTRL]
        short = spec.get("shorts", 1.0)
        prims.append((tube(lctrl, lambda u: 0.235 - 0.05 * u, k=6, steps=2, cap_rings=1,
                           color_fn=lambda u, sh=short: bottom if u < sh else spec.get("leg_skin", skin)), None, 50.0))
        sz = max(floor + 0.155, LEG_CTRL[-1][2] - 0.1)
        shoe = ellipsoid((0.23, 0.36, 0.16), Matrix.Translation((sx * 0.42, -1.33, sz)), 8, 5)
        if s > 0.8:
            for v in shoe.verts:
                v.co.z = max(v.co.z, floor + 0.02)
        prims.append((shoe, spec["shoe"], 60.0))

    ex, ez = spec.get("eye_x", 0.215), spec.get("eye_z", 3.98)
    er = spec.get("eye_r", (0.055, 0.08, 0.04))
    for sx in (-1, 1):
        prims.append((face.lens(sx * ex, ez, er[0], er[1], 0.004, er[2] * 0.8), BLACK, 80.0))
        bi, bo = spec.get("brow", (4.16, 4.16))
        if isinstance(bi, tuple):
            (bi, bo) = bi if sx > 0 else bo
        prims.append((face.curve([(sx * 0.11, bi), (sx * 0.2, 0.5 * (bi + bo) + 0.03), (sx * 0.29, bo)], 0.03, 0.0, k=4, steps=2), spec.get("brow_color", BLACK), 70.0))

    for item in spec["extras"](face):
        prims.append(item)

    T = Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation((0, 0, -BOTTOM))
    out = []
    for bm, col, ang in prims:
        bmesh.ops.transform(bm, matrix=T, verts=bm.verts)
        out.append((fix_closed(bm), col, ang))
    return out


def mouth_line(face, pts, r=0.03):
    return (face.curve(pts, r, 0.0, k=4, steps=3), BLACK, 70.0)


def open_mouth(face, z0, w, h, teeth=True, tongue=True, lift=0.05):
    out = []

    def fn(u, v):
        x = (u - 0.5) * 2.0 * w * math.sqrt(max(0.05, 1.0 - v * v))
        return x, z0 + lift * (2 * u - 1) ** 2 - v * h
    out.append((face.patch(fn, 8, 4, 0.012), BLACK, 70.0))
    if teeth:
        def ft(u, v):
            x = (u - 0.5) * 2.0 * w * 0.82
            return x, z0 + lift * (2 * u - 1) ** 2 * 0.8 - 0.005 - v * h * 0.22
        out.append((face.patch(ft, 6, 1, 0.022), WHITE, 70.0))
    if tongue:
        out.append((face.dot(0.0, z0 - h * 0.72, (w * 0.42, h * 0.22, 0.02), 0.02, 8, 4), RED, 70.0))
    return out


def v_patch(face, z0, z1, w0, w1=0.03, nu=4, nv=4, off=0.02):
    def fn(u, v):
        hw = w0 + (w1 - w0) * v
        return (u - 0.5) * 2.0 * hw, z0 + (z1 - z0) * v
    return face.patch(fn, nu, nv, off)


def surf_ring(e_fn, off, n=20):
    return [body_pt(-math.pi / 2 + 2 * math.pi * i / n, e_fn(-math.pi / 2 + 2 * math.pi * i / n), off) for i in range(n)]


def extras_abuela(face):
    out = []
    hair = cap_shell(hairline(0.86, 0.25, -0.22), 0.06, lambda th, r: WHITE, rows=5)
    out.append((hair, None, 55.0))
    out.append((ellipsoid((0.3, 0.28, 0.27), Matrix.Translation((0, 0.32, 4.58)), 10, 7), WHITE, 60.0))
    for sx in (-1, 1):
        ring = []
        for k in range(10):
            a = 2 * math.pi * k / 10
            loc, n = face.hit(sx * 0.215 + 0.135 * math.cos(a), 3.98 + 0.135 * math.sin(a))
            ring.append(loc + n * 0.05)
        out.append((tube(ring, lambda u: 0.024, k=4, steps=1, closed=True), DARK, 60.0))
        l0, n0 = face.hit(sx * 0.35, 3.99)
        side = body_pt(math.radians(-90 + sx * 62), 0.42, 0.02)
        out.append((tube([l0 + n0 * 0.05, side], lambda u: 0.02, k=4, steps=1, cap_rings=1), DARK, 60.0))
        out.append((face.dot(sx * 0.36, 3.80, (0.085, 0.055, 0.015), 0.005, 8, 4), SK4, 70.0))
    l1, n1 = face.hit(-0.08, 3.995)
    l2, n2 = face.hit(0.0, 4.02)
    l3, n3 = face.hit(0.08, 3.995)
    out.append((tube([l1 + n1 * 0.05, l2 + n2 * 0.06, l3 + n3 * 0.05], lambda u: 0.02, k=4, steps=2, cap_rings=1), DARK, 60.0))
    out.append(mouth_line(face, [(-0.1, 3.75), (0.0, 3.715), (0.1, 3.75)]))
    out.append((v_patch(face, 3.32, 2.62, 0.3, 0.03), CREAM, 60.0))
    for z in (2.45, 2.2, 1.95):
        out.append((face.dot(0.0, z, (0.05, 0.05, 0.03), 0.02, 6, 4), YELLOW, 60.0))
    return out


def extras_turista(face):
    out = []
    prof = [(-0.03, 0.55, YELLOW), (-0.07, 0.95, YELLOW), (-0.17, 1.22, YELLOW), (-0.13, 1.27, YELLOW),
            (0.0, 0.99, YELLOW), (0.07, 0.92, TEAL), (0.2, 0.9, YELLOW), (0.45, 0.85, YELLOW), (0.64, 0.7, YELLOW),
            (0.72, 0.4, YELLOW), (0.74, 0.0, YELLOW)]
    m = (Matrix.Translation((0, 0.02, 4.18)) @ Matrix.Rotation(math.radians(-11), 4, "X") @ Matrix.Diagonal((1.0, 0.92, 1.0, 1.0)))
    out.append((lathe(prof, 14, m), None, 55.0))
    loc, n = face.hit(0.0, 2.78)
    fr = Matrix.Translation(loc + n * 0.11) @ frame_from_normal(n)
    cam = bmesh.new()
    bmesh.ops.create_cube(cam, size=1.0)
    bmesh.ops.bevel(cam, geom=cam.edges[:], offset=0.035, segments=1, affect="EDGES")
    bmesh.ops.transform(cam, matrix=fr @ Matrix.Diagonal((0.4, 0.25, 0.17, 1.0)), verts=cam.verts)
    out.append((cam, BLACK, 40.0))
    out.append((cylinder(0.085, 0.12, fr @ Matrix.Translation((0.04, -0.01, 0.12)), 12), DARK, 40.0))
    out.append((cylinder(0.05, 0.02, fr @ Matrix.Translation((0.04, -0.01, 0.185)), 10), GLASS, 40.0))
    flash = bmesh.new()
    bmesh.ops.create_cube(flash, size=1.0)
    bmesh.ops.transform(flash, matrix=fr @ Matrix.Translation((-0.12, 0.07, 0.09)) @ Matrix.Diagonal((0.09, 0.06, 0.02, 1.0)), verts=flash.verts)
    out.append((flash, WHITE, 30.0))
    for sx in (-1, 1):
        a, na = face.hit(sx * 0.18, 2.86)
        b, nb = face.hit(sx * 0.36, 3.12)
        pts = [a + na * 0.08, b + nb * 0.035]
        for th in (-90 + sx * 52, -90 + sx * 80, -90 + sx * 115):
            pts.append(body_pt(math.radians(th), -0.22, 0.035))
        pts.append(body_pt(math.radians(90), -0.22, 0.035))
        out.append((tube(pts, lambda u: 0.025, k=4, steps=2, cap_rings=1), DARK, 60.0))
    out.extend(open_mouth(face, 3.77, 0.11, 0.09, teeth=False, tongue=True, lift=0.03))
    return out


def extras_ejecutivo(face):
    out = []
    hair = cap_shell(hairline(0.92, 0.32, -0.15), 0.05, lambda th, r: BLACK, rows=5)
    out.append((hair, None, 55.0))
    m = Matrix.Translation(body_pt(math.radians(-100), 1.0, 0.1)) @ Matrix.Rotation(math.radians(-25), 4, "X") @ Matrix.Rotation(math.radians(-12), 4, "Y")
    out.append((ellipsoid((0.4, 0.26, 0.15), m, 12, 6), BLACK, 60.0))
    out.append((v_patch(face, 3.32, 2.62, 0.28, 0.03), WHITE, 60.0))
    loc, n = face.hit(0.0, 3.2)
    out.append((ellipsoid((0.065, 0.05, 0.05), Matrix.Translation(loc + n * 0.06) @ frame_from_normal(n), 8, 5), ORANGE, 60.0))
    loc, n = face.hit(0.0, 2.82)
    out.append((ellipsoid((0.085, 0.36, 0.03), Matrix.Translation(loc + n * 0.055) @ frame_from_normal(n), 8, 5), ORANGE, 60.0))
    for sx in (-1, 1):
        def lap(u, v, sx=sx):
            z = 3.3 - 0.62 * v
            x = sx * (0.31 * (1 - v) + 0.03 + 0.09 * u)
            return x, z
        out.append((face.patch(lap, 1, 4, 0.035), DARK, 60.0))
    out.append(mouth_line(face, [(-0.09, 3.725), (0.0, 3.735), (0.09, 3.715)], 0.026))
    return out


def extras_nino(face):
    out = []
    gores = [BLUE, YELLOW, RED]
    cap = cap_shell(hairline(0.80, 0.42, 0.18), 0.07, lambda th, r: gores[int(((th + math.pi / 2) % (2 * math.pi)) / (math.pi / 3)) % 3], rows=5)
    out.append((cap, None, 55.0))
    p = body_pt(math.radians(-90), 0.78, 0.07)
    out.append((ellipsoid((0.52, 0.42, 0.045), Matrix.Translation(p + Vector((0, -0.2, -0.04))) @ Matrix.Rotation(math.radians(14), 4, "X"), 14, 5), BLUE, 60.0))
    top = Vector((0, 0, ZCT + 1.07))
    out.append((cylinder(0.04, 0.22, Matrix.Translation(top + Vector((0, 0, 0.08))), 8), DARK, 40.0))
    out.append((ellipsoid((0.065, 0.065, 0.065), Matrix.Translation(top + Vector((0, 0, 0.2))), 8, 6), RED, 60.0))
    for sgn in (-1, 1):
        m = Matrix.Translation(top + Vector((sgn * 0.24, 0, 0.2))) @ Matrix.Rotation(math.radians(sgn * 18), 4, "X")
        out.append((ellipsoid((0.24, 0.075, 0.022), m, 10, 4), YELLOW, 60.0))
    out.extend(open_mouth(face, 3.79, 0.19, 0.15, teeth=True, tongue=True, lift=0.06))
    for sx in (-1, 1):
        out.append((face.dot(sx * 0.37, 3.78, (0.08, 0.05, 0.015), 0.005, 8, 4), SK4, 70.0))
    return out


def extras_deportista(face):
    out = []
    hair = cap_shell(hairline(0.86, 0.32, -0.12), 0.05, lambda th, r: BLACK, rows=4)
    out.append((hair, None, 55.0))
    band = surf_ring(lambda th: 0.64 - 0.12 * math.sin(th), 0.07, 18)
    out.append((tube(band, lambda u: 0.085, k=5, steps=1, closed=True), RED, 55.0))
    l0, n0 = face.hit(0.0, 3.3)
    pts = [l0 + n0 * 0.015]
    for z in (2.9, 2.5, 2.1, 1.85):
        l, n = face.hit(0.0, z)
        pts.append(l + n * 0.015)
    out.append((tube(pts, lambda u: 0.03, k=4, steps=1, cap_rings=1), WHITE, 50.0))
    l, n = face.hit(0.03, 3.05)
    out.append((ellipsoid((0.045, 0.08, 0.025), Matrix.Translation(l + n * 0.05) @ frame_from_normal(n), 6, 4), DARK, 60.0))
    collar = surf_ring(lambda th: -0.27, 0.05, 18)
    out.append((tube(collar, lambda u: 0.07, k=5, steps=1, closed=True), BLUE, 55.0))
    for sx in (-1, 1):
        pts = [Vector((sx * (x + 0.12), y, z + 0.03)) for x, y, z in ARM_CTRL[:4]]
        pts[0] = Vector((sx * 0.70, 0.0, 3.17))
        out.append((tube(pts, lambda u: 0.03, k=4, steps=3, cap_rings=1), WHITE, 50.0))
    out.append(mouth_line(face, [(-0.1, 3.735), (0.0, 3.72), (0.11, 3.77)]))
    return out


def extras_rockero(face):
    out = []
    spikes = [(-90, 0.98, 0.36, 0.13), (-90, 1.22, 0.52, 0.16), (-90, 1.47, 0.64, 0.18),
              (90, 1.3, 0.62, 0.18), (90, 1.0, 0.55, 0.17), (90, 0.66, 0.44, 0.15), (90, 0.3, 0.3, 0.12)]
    ridge = []
    for i, (th, e, ln, r) in enumerate(spikes):
        p = body_pt(math.radians(th), e, 0.0)
        n = body_normal(math.radians(th), e)
        d = (n + Vector((0, 0.45, 0.0))).normalized()
        out.append((cylinder(r, ln, Matrix.Translation(p + d * (ln * 0.5)) @ align_z(d), 6, r2=0.015), GREEN if i % 2 == 0 else DGREEN, 45.0))
        ridge.append(p + n * 0.02)
    out.append((tube(ridge, lambda u: 0.13, k=6, steps=2, cap_rings=2), GREEN, 55.0))
    out.append((v_patch(face, 3.32, 1.75, 0.27, 0.2, 3, 5, 0.02), RED, 60.0))
    for sx in (-1, 1):
        for z in (3.15, 2.85, 2.55):
            out.append((face.dot(sx * (0.27 - 0.05 * (3.3 - z)), z, (0.04, 0.04, 0.03), 0.03, 6, 4), WHITE, 60.0))
    out.append(mouth_line(face, [(-0.1, 3.73), (0.0, 3.73), (0.1, 3.775)]))
    return out


def top_stripes(c):
    k = int((NECK - c.z) / 0.25)
    return WHITE if k % 2 == 0 else BLUE


PASSENGERS = [
    ("PasajeroAbuela", dict(scale=0.945, skin=SK1, top=TEAL, bottom=BLUE, shoe=RED, extras=extras_abuela,
                            brow=((4.15, 4.17), (4.15, 4.17)), brow_color=DARK, eye_r=(0.05, 0.072, 0.035))),
    ("PasajeroTurista", dict(scale=0.945, skin=SK4, top=WHITE, top_fn=top_stripes, bottom=CREAM, shoe=DARK, extras=extras_turista,
                             extra_z=[NECK - 0.25 * i for i in range(1, 6)], sleeve=0.33, arm_color=WHITE, shorts=0.45,
                             brow=((4.18, 4.2), (4.18, 4.2)))),
    ("PasajeroEjecutivo", dict(scale=0.945, skin=SK2, top=DARK, bottom=DARK, shoe=BLACK, extras=extras_ejecutivo,
                               brow=((4.19, 4.13), (4.19, 4.13)))),
    ("PasajeroNino", dict(scale=0.70, skin=SK1, top=GREEN, bottom=BLUE, shoe=RED, extras=extras_nino, sleeve=0.33, arm_color=GREEN,
                          shorts=0.5, eye_r=(0.065, 0.095, 0.04), eye_z=4.0, brow=((4.22, 4.24), (4.22, 4.24)))),
    ("PasajeroDeportista", dict(scale=0.945, skin=SK3, top=BLUE, bottom=DARK, shoe=WHITE, extras=extras_deportista,
                                brow=((4.12, 4.18), (4.12, 4.18)))),
    ("PasajeroRockero", dict(scale=0.945, skin=SK2, top=BLACK, bottom=BLUE, shoe=BLACK, extras=extras_rockero,
                             brow=((4.15, 4.17), (4.2, 4.24)))),
]


def croc_section(y):
    keys = [
        (-3.0, 0.22, 0.33, 0.60),
        (-2.92, 0.29, 0.30, 0.64),
        (-2.6, 0.32, 0.28, 0.66),
        (-2.2, 0.36, 0.27, 0.69),
        (-1.85, 0.45, 0.26, 0.78),
        (-1.5, 0.56, 0.25, 0.92),
        (-1.2, 0.60, 0.25, 0.98),
        (-0.95, 0.55, 0.26, 0.93),
        (-0.6, 0.62, 0.24, 1.0),
        (-0.1, 0.67, 0.22, 1.06),
        (0.4, 0.65, 0.23, 1.03),
        (0.9, 0.56, 0.26, 0.93),
        (1.4, 0.43, 0.28, 0.78),
        (1.9, 0.30, 0.27, 0.62),
        (2.4, 0.19, 0.23, 0.47),
        (2.8, 0.09, 0.19, 0.32),
        (2.97, 0.03, 0.18, 0.26),
    ]
    for i in range(len(keys) - 1):
        if keys[i][0] <= y <= keys[i + 1][0]:
            a, b = keys[i], keys[i + 1]
            t = (y - a[0]) / (b[0] - a[0])
            t = t * t * (3 - 2 * t)
            return tuple(a[k] + (b[k] - a[k]) * t for k in (1, 2, 3))
    return keys[-1][1:]


def croc_xo(y):
    return 0.16 * ss(0.8, 3.0, y) * math.sin((y - 0.8) * 1.2)


CROC_N = 2.6
MOUTH_END = -1.08


def croc_mz(y):
    return 0.455 + 0.3 * ss(-1.75, -1.1, y) ** 1.4


def croc_theta_m(y):
    if y >= MOUTH_END:
        return 0.0
    w, zb, zt = croc_section(y)
    zc, h = 0.5 * (zb + zt), 0.5 * (zt - zb)
    q = max(-0.95, min(0.95, (croc_mz(y) - zc) / h))
    return math.asin(math.copysign(abs(q) ** (CROC_N / 2), q))


def croc_ring(y, m):
    tm = croc_theta_m(y)
    half = []
    for j in range(m // 2 + 1):
        th = -math.pi / 2 + 2 * math.pi * j / m
        if th <= 0:
            t2 = -math.pi / 2 + (th + math.pi / 2) * (tm + math.pi / 2) / (math.pi / 2)
        else:
            t2 = tm + th * (math.pi / 2 - tm) / (math.pi / 2)
        half.append(croc_pt(y, t2) - Vector((croc_xo(y), 0, 0)))
    pts = half + [Vector((-p.x, p.y, p.z)) for p in reversed(half[1:-1])]
    return [p + Vector((croc_xo(y), 0, 0)) for p in pts]


def croc_pt(y, th, off=0.0):
    w, zb, zt = croc_section(y)
    zc, h = 0.5 * (zb + zt), 0.5 * (zt - zb)
    c, s = math.cos(th), math.sin(th)
    x = (w + off) * math.copysign(abs(c) ** (2 / CROC_N), c)
    z = zc + (h + off) * math.copysign(abs(s) ** (2 / CROC_N), s)
    return Vector((x + croc_xo(y), y, z))


def croc_side_x(y, z):
    w, zb, zt = croc_section(y)
    zc, h = 0.5 * (zb + zt), 0.5 * (zt - zb)
    t = min(1.0, abs(z - zc) / h)
    return w * (1 - t ** CROC_N) ** (1 / CROC_N)


def build_croc():
    prims = []
    m = 16
    ys = [-2.97, -2.86, -2.65, -2.4, -2.15, -1.9, -1.65, -1.42, -1.2, -1.0, -0.78, -0.45, -0.05, 0.4, 0.8,
          1.2, 1.6, 2.0, 2.4, 2.7, 2.9]
    bm = bmesh.new()
    cl = bm.faces.layers.int.new("c")
    ths = [-math.pi / 2 + 2 * math.pi * j / m for j in range(m)]
    rings = [[bm.verts.new((croc_xo(-3.0), -3.0, 0.465))]]
    for y in ys:
        rings.append([bm.verts.new(p) for p in croc_ring(y, m)])
    rings.append([bm.verts.new((croc_xo(3.0), 3.0, 0.22))])
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        yb = ys[i] if i < len(ys) else 3.0
        for j in range(m):
            j2 = (j + 1) % m
            if len(a) == 1:
                f = bm.faces.new((a[0], b[j], b[j2]))
            elif len(b) == 1:
                f = bm.faces.new((a[j], b[0], a[j2]))
            else:
                f = bm.faces.new((a[j], b[j], b[j2], a[j2]))
            c = f.calc_center_median()
            thm = ths[j] + math.pi / m
            sn = math.sin(thm)
            jaw = yb <= MOUTH_END and (j < m // 4 or j >= 3 * m // 4)
            if sn < -0.62 or jaw:
                f[cl] = CREAM
            elif sn > 0.9 and -0.95 < yb < 2.9:
                f[cl] = DGREEN
            else:
                f[cl] = GREEN
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    prims.append((bm, None, 45.0))

    for sx in (-1, 1):
        pts = [Vector((sx * (croc_side_x(-1.02, 0.80) - 0.02), -1.02, 0.84))]
        for y in (-1.1, -1.2, -1.34, -1.55, -1.8, -2.08, -2.36, -2.62, -2.84):
            z = croc_mz(y)
            x = croc_side_x(y, z) + 0.012
            pts.append(Vector((sx * x + croc_xo(y), y, z)))
        pts.append(Vector((sx * 0.14, -2.975, 0.462)))
        pts.append(Vector((0.0, -3.0, 0.462)))
        prims.append((tube(pts, lambda u: 0.036, k=4, steps=1, cap_rings=1), BLACK, 60.0))
        for i, y in enumerate((-1.3, -1.52, -1.76, -2.0, -2.24, -2.48, -2.72)):
            up = i % 2 == 0
            z = croc_mz(y)
            x = croc_side_x(y, z)
            base = Vector((sx * (x + 0.015), y, z + (0.012 if up else -0.012)))
            d = Vector((sx * 0.3, -0.1, -1.0 if up else 1.0)).normalized()
            ln = 0.19 if i < 3 else 0.15
            prims.append((cylinder(0.07, ln, Matrix.Translation(base + d * (ln * 0.5)) @ align_z(d), 4, r2=0.0), WHITE, 40.0))
    for sx in (-0.13, 0.13):
        d = Vector((sx * 0.5, -0.8, -1.0)).normalized()
        base = Vector((sx, -2.95, 0.475))
        prims.append((cylinder(0.06, 0.16, Matrix.Translation(base + d * 0.08) @ align_z(d), 4, r2=0.0), WHITE, 40.0))

    for sx in (-1, 1):
        ec = Vector((sx * 0.27, -1.4, 1.14))
        prims.append((ellipsoid((0.24, 0.27, 0.2), Matrix.Translation((sx * 0.27, -1.36, 0.95)), 10, 6), GREEN, 60.0))
        prims.append((ellipsoid((0.21, 0.21, 0.21), Matrix.Translation(ec), 12, 8), WHITE, 60.0))
        dpup = Vector((-sx * 0.12, -1.0, 0.05)).normalized()
        prims.append((ellipsoid((0.08, 0.1, 0.045), Matrix.Translation(ec + dpup * 0.19) @ frame_from_normal(dpup), 8, 4), BLACK, 70.0))
        ln = Vector((-sx * 0.42, 0.42, 1.0)).normalized()
        a0 = math.radians(96)
        prof = [(0.18 * math.cos(a0), 0.18 * math.sin(a0), DGREEN)]
        for k in range(5):
            a = a0 * (1 - k / 4)
            prof.append((0.228 * math.cos(a), 0.228 * math.sin(a), GREEN if k else DGREEN))
        prims.append((lathe(prof, 12, Matrix.Translation(ec) @ align_z(ln)), None, 60.0))
        prims.append((ellipsoid((0.065, 0.055, 0.04), Matrix.Translation((sx * 0.11 + croc_xo(-2.85), -2.86, 0.645)), 6, 4), DGREEN, 60.0))

    scutes = [(-0.72, 0.0), (-0.42, -0.18), (-0.42, 0.18), (-0.12, -0.2), (-0.12, 0.2), (0.18, -0.2), (0.18, 0.2),
              (0.48, -0.18), (0.48, 0.18), (0.78, 0.0), (1.08, 0.0), (1.38, 0.0), (1.68, 0.0), (1.98, 0.0), (2.28, 0.0), (2.58, 0.0)]
    for y, dx in scutes:
        w, zb, zt = croc_section(y)
        f = 1.0 if y < 0.9 else max(0.45, 1.0 - (y - 0.9) / 2.2)
        zc, h = 0.5 * (zb + zt), 0.5 * (zt - zb)
        t = min(0.98, abs(dx) / w)
        zz = zc + h * (1 - t ** CROC_N) ** (1 / CROC_N)
        n = Vector((dx * 1.5, 0, 1.0)).normalized()
        base = Vector((dx + croc_xo(y), y, zz - 0.02))
        ln = 0.14 * f
        prims.append((cylinder(0.105 * f, ln, Matrix.Translation(base + n * ln * 0.5) @ align_z(n), 5, r2=0.03 * f), DGREEN, 45.0))

    for ly in (-0.6, 0.72):
        for sx in (-1, 1):
            w, zb, zt = croc_section(ly)
            ctrl = [Vector((sx * (w - 0.27), ly + 0.04, 0.5)), Vector((sx * (w - 0.1), ly, 0.3)), Vector((sx * 0.54, ly - 0.05, 0.1))]
            prims.append((tube(ctrl, lambda u: 0.17 - 0.03 * u, k=9, steps=3, cap_rings=1), GREEN, 60.0))
            foot = ellipsoid((0.14, 0.22, 0.09), Matrix.Translation((sx * 0.54, ly - 0.12, 0.07)), 10, 6)
            for v in foot.verts:
                v.co.z = max(v.co.z, 0.0)
            prims.append((foot, GREEN, 60.0))
            for k in (-1, 0, 1):
                d = Vector((k * 0.35, -1.0, -0.15)).normalized()
                base = Vector((sx * 0.54 + k * 0.07, ly - 0.3, 0.05))
                prims.append((cylinder(0.035, 0.09, Matrix.Translation(base + d * 0.04) @ align_z(d), 4, r2=0.0), CREAM, 40.0))
    lo = min(v.co.y for bm, _, _ in prims for v in bm.verts)
    hi = max(v.co.y for bm, _, _ in prims for v in bm.verts)
    k = 6.0 / (hi - lo)
    T = Matrix.Diagonal((k, k, k, 1.0)) @ Matrix.Translation((0, -0.5 * (lo + hi), 0))
    out = []
    for bm, col, ang in prims:
        bmesh.ops.transform(bm, matrix=T, verts=bm.verts)
        for v in bm.verts:
            v.co.z = max(v.co.z, 0.0)
        out.append((fix_closed(bm), col, ang))
    return out


def seat(x):
    out = []
    for (cx, cy, cz, sx_, sy_, sz_, col) in ((x, -0.22, -0.25, 2.2, 1.95, 0.5, TEAL),
                                              (x, 0.98, 1.05, 2.2, 0.45, 3.1, TEAL),
                                              (x, 0.1, -1.0, 1.6, 1.4, 1.2, DARK)):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.transform(bm, matrix=Matrix.Translation((cx, cy, cz)) @ Matrix.Diagonal((sx_, sy_, sz_, 1.0)), verts=bm.verts)
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.14, segments=3, affect="EDGES", profile=0.5)
        out.append((bm, col, 40.0))
    return out


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    img = make_palette_image()
    mat = palette_material(img)
    manifest = []
    objs = []
    for name, spec in PASSENGERS:
        ob = build_object(name, passenger(spec), mat)
        objs.append(ob)
    objs.append(build_object("Cocodrilo", build_croc(), mat))
    for ob in objs:
        tris = tri_count(ob)
        mn, mx = bbox(ob)
        print("TRIS", ob.name, tris, "BBOX", [round(v, 2) for v in mn], [round(v, 2) for v in mx])
        export_fbx(ob, os.path.join(OUT, ob.name + ".fbx"))
        manifest.append({
            "nombre": ob.name,
            "archivo": ob.name + ".fbx",
            "bbox_min": [round(mn[0], 3), round(mn[2], 3), round(mn[1], 3)],
            "bbox_max": [round(mx[0], 3), round(mx[2], 3), round(mx[1], 3)],
            "triangulos": tris,
        })
    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    if not RENDER:
        return
    croc = objs[-1]
    pas = objs[:-1]
    render_setup(scene, ground_z=-1.6, ground_size=80, ground_hex="EFE9DC", sun_rot=(52, 6, -30))
    seat_objs = []
    for i, ob in enumerate(pas):
        x = -6.25 + 2.5 * i
        ob.location = (x, 0, 0)
        seat_objs.append(build_object("Seat%d" % i, seat(x), mat))
    croc.hide_render = True
    shoot(scene, "pasajeros_1", dict(loc=(-2.6, -17.0, 4.3), target=(0.35, 0.0, 0.8), lens=35))
    for ob in pas + seat_objs:
        ob.hide_render = True
    croc.hide_render = False
    croc.location = (0, 0, -1.6)
    shoot(scene, "cocodrilo", dict(loc=(-4.5, -5.0, 0.6), target=(0.25, -0.25, -1.0), lens=40))


main()
