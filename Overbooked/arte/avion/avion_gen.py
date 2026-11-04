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


def tube(ctrl, radius_fn, k=12, steps=6, closed=False, up=None, caps=True, cap_rings=4):
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
    rings = []
    for i in range(n):
        u = seglen[i] / total if total > 0 else 0.0
        r = radius_fn(u)
        b = tangents[i].cross(normals[i]).normalized()
        rings.append([bm.verts.new(path[i] + (normals[i] * math.cos(2 * math.pi * j / k) + b * math.sin(2 * math.pi * j / k)) * r) for j in range(k)])
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
    for a_i, b_i in pairs:
        ra, rb = rings[a_i], rings[b_i]
        for j in range(k):
            bm.faces.new((ra[j], ra[(j + 1) % k], rb[(j + 1) % k], rb[j]))
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
                        bm.faces.new((prev[j], prev[(j + 1) % k], pole))
                    break
                rr = r_end * math.cos(phi)
                ring = [bm.verts.new(center + (normals[end] * math.cos(2 * math.pi * j / k) + b * math.sin(2 * math.pi * j / k)) * rr) for j in range(k)]
                for j in range(k):
                    bm.faces.new((prev[j], prev[(j + 1) % k], ring[(j + 1) % k], ring[j]))
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


def render_setup(scene, ground_z=0.0, ground_size=60, ground_hex="EFE9DC", sun_rot=(48, 8, -28)):
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
    scene.render.resolution_x, scene.render.resolution_y = (800, 450) if PREVIEW else (1600, 900)
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


R0, ZC0 = 8.75, 5.0
TH = [-90.0, -78.0, -66.0, -56.0,
      -math.degrees(math.acos(6.0 / R0)),
      math.degrees(math.asin((-0.4 - ZC0) / R0)),
      math.degrees(math.asin((0.0 - ZC0) / R0)),
      -24.0, -14.0, -6.0, 2.0,
      math.degrees(math.asin((6.5 - ZC0) / R0)),
      20.0, 30.0, 40.0, 44.0, 54.0, 64.0, 74.0, 84.0, 90.0]
KB = 4
NCOL = 2 * (len(TH) - 1)
WINDOW_ROWS = [-41.5 + 4.5 * i for i in range(8)]


def ring_pts(y, zc, W, Ht, Hb, nt, nb, th_kb):
    th0 = TH[KB]
    right = []
    for th in TH:
        if th <= th0:
            t2 = -90.0 + (th + 90.0) * (th_kb + 90.0) / (th0 + 90.0)
        else:
            t2 = th_kb + (th - th0) * (90.0 - th_kb) / (90.0 - th0)
        a = math.radians(t2)
        c, s = math.cos(a), math.sin(a)
        n = nt if s >= 0 else nb
        H = Ht if s >= 0 else Hb
        x = W * abs(c) ** (2.0 / n)
        z = zc + H * math.copysign(abs(s) ** (2.0 / n), s)
        right.append((x, z))
    pts = right + [(-x, z) for (x, z) in reversed(right[1:-1])]
    return [Vector((x, y, z)) for x, z in pts]


def herm(y):
    t = (y - 12.0) / 10.0
    p0, p1, m1 = -3.75, 0.0, 10.0
    return (2 * t ** 3 - 3 * t ** 2 + 1) * p0 + (-2 * t ** 3 + 3 * t ** 2) * p1 + (t ** 3 - t ** 2) * m1


def tail_params(y):
    zt = 13.75 - 1.15 * ss(14.0, 30.0, y)
    zb = -3.75 if y <= 12 else (herm(y) if y <= 22 else y - 22.0)
    W = R0 - 2.05 * ss(14.0, 30.0, y)
    zc = 0.5 * (zt + zb)
    nb = 2.0 + 2.5 * ss(12.0, 22.0, y)
    nt = 2.0 + 0.4 * ss(14.0, 30.0, y)
    cb = min(1.0, (6.0 / W) ** (nb / 2.0))
    th_kb = -math.degrees(math.acos(cb))
    return zc, W, zt - zc, zc - zb, nt, nb, th_kb


def nose_params(y):
    t = (y + 50.0) / -16.0
    R = R0 * max(0.0, 1.0 - t ** 3) ** (1.0 / 3.0)
    zc = ZC0 - 1.6 * t * t
    return zc, R


def build_fuselage():
    stations = []
    for y in (-65.6, -65.0, -64.0, -62.5, -61.0, -59.0, -56.5, -53.5):
        zc, R = nose_params(y)
        stations.append((y, ring_pts(y, zc, R, R, R, 2.0, 2.0, TH[KB])))
    for y in (-50.0, -25.0, -22.0, 12.0):
        stations.append((y, ring_pts(y, ZC0, R0, R0, R0, 2.0, 2.0, TH[KB])))
    last_kb = None
    for y in (14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30.0):
        zc, W, Ht, Hb, nt, nb, th_kb = tail_params(y)
        last_kb = th_kb
        stations.append((y, ring_pts(y, zc, W, Ht, Hb, nt, nb, th_kb)))
    for y, W, zt, zb in ((30.55, 5.9, 12.35, 8.75), (31.0, 4.2, 11.95, 9.55)):
        zc = 0.5 * (zt + zb)
        stations.append((y, ring_pts(y, zc, W, zt - zc, zc - zb, 2.4, 3.0, last_kb)))

    bm = bmesh.new()
    cl = bm.faces.layers.int.new("c")
    nose_zc, _ = nose_params(-66.0)
    rings = [(-66.0, [bm.verts.new((0.0, -66.0, nose_zc))])]
    for y, pts in stations:
        rings.append((y, [bm.verts.new(p) for p in pts]))
    rings.append((31.3, [bm.verts.new((0.0, 31.3, 10.75))]))

    def color(ya, yb, j):
        jr = j if j < NCOL // 2 else NCOL - 1 - j
        e = 1e-3
        if ya >= -25 - e and yb <= -22 + e and 6 <= jr <= 10:
            return None
        if ya >= 22 - e and yb <= 30 + e and jr <= 3:
            return None
        if ya >= -64 - e and yb <= -61 + e and jr >= 11:
            return CREAM if jr in (14, 19) else GLASS
        if jr <= 4:
            return ORANGE
        if jr == 5:
            return TEAL
        return CREAM

    for i in range(len(rings) - 1):
        ya, A = rings[i]
        yb, B = rings[i + 1]
        for j in range(NCOL):
            c = color(ya, yb, j)
            if c is None:
                continue
            j2 = (j + 1) % NCOL
            if len(A) == 1:
                f = bm.faces.new((A[0], B[j], B[j2]))
            elif len(B) == 1:
                f = bm.faces.new((A[j], B[0], A[j2]))
            else:
                f = bm.faces.new((A[j], B[j], B[j2], A[j2]))
            f[cl] = c
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    return bm


def surf(sx, y, s, off):
    r = R0 + off
    th = s / r
    return Vector((sx * r * math.cos(th), y, ZC0 + r * math.sin(th)))


def window(yc, sx):
    out = []
    for (a, b, off, col, rot, dy, ds, seg) in ((0.92, 1.32, 0.07, GLASS, 0.0, 0.0, 0.0, 16),
                                                (0.12, 0.46, 0.11, WHITE, 0.6, -0.34, 0.46, 8)):
        bm = bmesh.new()
        ctr = bm.verts.new(surf(sx, yc + dy, ds, off))
        ring = []
        for k in range(seg):
            t = 2 * math.pi * k / seg
            u, v = a * math.cos(t), b * math.sin(t)
            u, v = u * math.cos(rot) - v * math.sin(rot), u * math.sin(rot) + v * math.cos(rot)
            ring.append(bm.verts.new(surf(sx, yc + dy + u, ds + v, off)))
        for k in range(seg):
            bm.faces.new((ctr, ring[k], ring[(k + 1) % seg]))
        orient(bm, lambda c: Vector((c.x, 0.0, c.z - ZC0)))
        out.append((bm, col))
    return out


def rounded_rect(y0, y1, s0, s1, rc, per=4):
    pts = []
    corners = [((y1 - rc, s0 + rc), -90), ((y1 - rc, s1 - rc), 0), ((y0 + rc, s1 - rc), 90), ((y0 + rc, s0 + rc), 180)]
    for (cy, cs), a0 in corners:
        for k in range(per + 1):
            a = math.radians(a0 + 90.0 * k / per)
            pts.append((cy + rc * math.cos(a), cs + rc * math.sin(a)))
    return pts


def outline(sx, y0, y1, z0, z1, rc, radius, k, off):
    s0 = R0 * math.asin((z0 - ZC0) / R0)
    s1 = R0 * math.asin((z1 - ZC0) / R0)
    pts = [surf(sx, y, s, off) for y, s in rounded_rect(y0, y1, s0, s1, rc)]
    return tube(pts, lambda u: radius, k=k, steps=1, closed=True, up=Vector((sx, 0, 0)))


def wing_section(x):
    f = max(0.0, (x - 8.0) / 30.0)
    le = -30.0 + 4.5 * f
    te = -18.0 - 1.5 * f
    t = 1.0 - 0.45 * f
    C = te - le
    h = t * 0.5
    pts = [(te, 0.0), (le + 0.66 * C, 0.0), (le + 0.33 * C, 0.0), (le + h, 0.0)]
    for a in (135, 180, 225):
        r = math.radians(a)
        pts.append((le + h + h * math.cos(r), -h + h * math.sin(r)))
    pts += [(le + h, -t), (le + 0.4 * C, -t), (le + 0.7 * C, -0.85 * t), (te, -0.3 * t)]
    return [Vector((x, yy, -1.0 + zz)) for yy, zz in pts]


def sym_section(le, te, t, at):
    C = te - le
    us = [0.0, 0.03, 0.1, 0.25, 0.45, 0.65, 0.85, 1.0]
    fs = [0.0, 0.55, 0.85, 1.0, 1.0, 0.92, 0.6, 0.15]
    right = [(le + u * C, 0.5 * t * f) for u, f in zip(us, fs)]
    pts = [right[0]] + right[1:] + [(y, -h) for y, h in reversed(right[1:])]
    return [Vector((h + at[0], y, at[1])) for y, h in pts]


def build_plane():
    PRIMS.clear()
    add(build_fuselage(), None, 35.0)

    for sx in (-1, 1):
        for i, yc in enumerate(WINDOW_ROWS):
            if -25.0 - 0.9 < yc < -22.0 + 0.9:
                continue
            for bm, col in window(yc, sx):
                add(bm, col, 60.0)
        add(outline(sx, -25.0, -22.0, 0.0, 6.5, 0.32, 0.16, 6, 0.02), ORANGE, 70.0)
        for y0 in (-50.8, -6.3):
            add(outline(sx, y0, y0 + 3.6, 0.3, 7.2, 0.7, 0.075, 4, 0.03), DARK, 70.0)

    wing = loft([wing_section(x) for x in (5.5, 8.0, 13.0, 18.0, 23.0, 28.0, 33.0, 38.0)])
    winglet_secs = [sym_section(le, te, t, (37.85, z)) for z, le, te, t in
                    ((-1.7, -25.4, -19.6, 0.46), (-1.0, -25.2, -19.6, 0.46), (0.4, -23.6, -19.4, 0.36), (1.8, -21.9, -19.25, 0.26))]
    winglet = loft(winglet_secs)

    def nacelle(cx):
        y0 = -28.5
        prof = [
            (0.35, 0.0, CREAM), (0.75, 0.45, CREAM), (1.15, 0.7, BLACK), (1.2, 1.72, BLACK),
            (0.4, 1.8, BLACK), (0.08, 1.92, ORANGE), (0.0, 2.04, ORANGE), (0.28, 2.16, ORANGE),
            (1.15, 2.2, CREAM), (3.0, 2.2, CREAM), (6.0, 2.08, CREAM), (7.9, 1.8, CREAM),
            (8.55, 1.55, DARK), (8.6, 1.2, DARK), (9.0, 1.0, DARK), (9.75, 0.0, DARK),
        ]
        mat = Matrix.Translation((cx, y0, -4.0)) @ Matrix.Rotation(math.radians(-90), 4, "X")
        out = [(lathe(prof, 24, mat), None, 35.0)]
        for b in range(8):
            a = 2 * math.pi * b / 8
            m = (Matrix.Translation((cx, y0 + 1.1, -4.0)) @ Matrix.Rotation(a, 4, "Y") @
                 Matrix.Translation((1.2, 0, 0)) @ Matrix.Rotation(math.radians(35), 4, "X"))
            blade = bmesh.new()
            bmesh.ops.create_cube(blade, size=1.0)
            bmesh.ops.transform(blade, matrix=m @ Matrix.Diagonal((0.95, 0.08, 0.32, 1.0)), verts=blade.verts)
            out.append((blade, DARK, 30.0))
        out.append((ellipsoid((0.32, 3.4, 0.7), Matrix.Translation((cx, -24.6, -1.75)), 10, 6), CREAM, 50.0))
        return out

    for sx in (-1, 1):
        w = wing if sx == 1 else mirror_x(wing)
        add(w, CREAM, 50.0)
        wl = winglet if sx == 1 else mirror_x(winglet)
        add(wl, TEAL, 50.0)
        for bm, col, ang in nacelle(sx * 18.0):
            add(bm, col, ang)

    fin_secs = []
    for z in (11.0, 13.0, 16.0, 19.0, 21.6, 22.6):
        k = (z - 12.5) / 9.5
        le = 14.0 + (z - 12.5) * (10.5 / 9.5)
        te = 30.5 + (z - 12.5) * (1.0 / 9.5)
        t = 1.4 - 0.7 * k
        if z > 22.0:
            le, te, t = le + 1.2, te - 0.6, t * 0.55
        fin_secs.append(sym_section(le, te, t, (0.0, z)))
    add(loft(fin_secs), TEAL, 50.0)

    zl, yl = 17.4, 25.4
    tl = 1.4 - 0.7 * (zl - 12.5) / 9.5
    add(cylinder(2.25, tl + 0.12, Matrix.Translation((0, yl, zl)) @ Matrix.Rotation(math.radians(90), 4, "Y"), 28), ORANGE, 40.0)
    for sx in (-1, 1):
        for k, (ln, dz) in enumerate(((1.35, 0.62), (1.05, 0.0), (0.72, -0.62))):
            cy = yl + 0.15 + 0.35 * k
            m = (Matrix.Translation((sx * (tl / 2 + 0.11), cy, zl + dz)) @ Matrix.Rotation(math.radians(-24), 4, "X"))
            add(ellipsoid((0.06, ln, 0.2), m, 12, 4), CREAM, 60.0)

    stab_secs = []
    for x in (3.5, 6.0, 10.0, 13.6, 14.6):
        f = (x - 3.5) / 11.1
        le = 20.5 + 5.0 * f
        te = 29.4 - 0.4 * f
        t = 0.85 - 0.4 * f
        if x > 14.0:
            le, te, t = le + 0.6, te - 0.3, t * 0.6
        stab_secs.append([Vector((x, p.y, p.x + 10.4)) for p in sym_section(le, te, t, (0.0, 0.0))])
    stab = loft(stab_secs)
    add(stab, TEAL, 50.0)
    add(mirror_x(stab), TEAL, 50.0)

    def wheel(cx, cy, cz, R, w):
        prof = [(-0.5 * w - 0.02, 0.0, CREAM), (-0.5 * w, 0.42 * R, BLACK), (-0.5 * w, 0.82 * R, BLACK),
                (-0.32 * w, R, BLACK), (0.32 * w, R, BLACK), (0.5 * w, 0.82 * R, BLACK), (0.5 * w, 0.42 * R, CREAM),
                (0.5 * w + 0.02, 0.0, CREAM)]
        mat = Matrix.Translation((cx, cy, cz)) @ Matrix.Rotation(math.radians(90), 4, "Y")
        return lathe(prof, 14, mat)

    def strut(x, y, z0, z1, r):
        return cylinder(r, z0 - z1, Matrix.Translation((x, y, 0.5 * (z0 + z1))), 10)

    add(strut(0.0, -55.0, -2.5, -9.0, 0.32), DARK, 40.0)
    add(cylinder(0.18, 1.5, Matrix.Translation((0.0, -55.0, -9.0)) @ Matrix.Rotation(math.radians(90), 4, "Y"), 8), DARK, 40.0)
    for sx in (-1, 1):
        add(wheel(sx * 0.55, -55.0, -9.0, 1.0, 0.5), None, 40.0)
    for sx in (-1, 1):
        add(strut(sx * 4.5, -19.5, -1.8, -8.75, 0.4), DARK, 40.0)
        add(cylinder(0.2, 1.9, Matrix.Translation((sx * 4.5, -19.5, -8.75)) @ Matrix.Rotation(math.radians(90), 4, "Y"), 8), DARK, 40.0)
        for dx in (-0.62, 0.62):
            add(wheel(sx * 4.5 + dx, -19.5, -8.75, 1.25, 0.55), None, 40.0)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    img = make_palette_image()
    mat = palette_material(img)
    build_plane()
    ob = build_object("AvionExterior", PRIMS, mat)
    tris = tri_count(ob)
    print("TRIS AvionExterior", tris)
    export_fbx(ob, os.path.join(OUT, "AvionExterior.fbx"))
    mn, mx = bbox(ob)
    man = [{
        "nombre": "AvionExterior",
        "archivo": "AvionExterior.fbx",
        "bbox_min": [round(mn[0], 3), round(mn[2] + 100.0, 3), round(mn[1], 3)],
        "bbox_max": [round(mx[0], 3), round(mx[2] + 100.0, 3), round(mx[1], 3)],
        "triangulos": tris,
    }]
    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(man, fh, indent=2, ensure_ascii=False)
    print("BBOX", mn, mx)
    if not RENDER:
        return
    render_setup(scene, ground_z=-10.0, ground_size=400, ground_hex="D9D4C7", sun_rot=(50, 10, -40))
    shoot(scene, "avion_1", dict(loc=(-78.0, -112.0, 42.0), target=(0.0, -16.0, 1.0), lens=40))
    shoot(scene, "avion_2", dict(loc=(-160.0, -18.0, 14.0), target=(0.0, -18.0, 3.0), ortho=106))


main()
