import bpy
import bmesh
import math
import os
import sys
import json
import random
from mathutils import Vector, Matrix, Euler

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
RAIZ = os.path.dirname(os.path.dirname(OUT))
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]


def arg(name, default=None):
    if name in ARGS:
        i = ARGS.index(name)
        return ARGS[i + 1] if i + 1 < len(ARGS) and not ARGS[i + 1].startswith("--") else True
    return default


PAL = [
    ("cream", "FFF4E0"), ("ink", "1B1B21"), ("orange", "F27B2B"), ("teal", "1FA6A0"),
    ("yellow", "F5CD3D"), ("red", "D9443A"), ("grey", "34383F"), ("white", "F7F7F2"),
    ("wood", "C98A4B"), ("wood2", "A86B35"), ("dwood", "7A4A26"), ("iron", "5C6168"),
    ("metal", "A9B0B8"), ("rust", "B5562A"), ("gold", "E8B13A"), ("skin", "F2B48C"),
    ("skin2", "D9826A"), ("pink", "F28AA0"), ("beak", "F59A23"), ("lgrey", "D5DAE0"),
    ("mgrey", "98A2AE"), ("water", "8FD3F4"), ("dred", "9E2A28"), ("dteal", "157F7B"),
    ("straw", "E8CC7E"), ("navy", "2B3A55"), ("lblue", "BFE6F5"), ("green", "6DBE45"),
    ("dgreen", "3D9447"), ("purple", "9B6BD6"), ("brown", "5A3A22"), ("tan", "E6C9A0"),
]
IDX = {n: i for i, (n, _) in enumerate(PAL)}


def suv(n):
    i = IDX[n]
    return ((i % 8 + 0.5) / 8.0, (i // 8 + 0.5) / 4.0)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def V(*a):
    return Vector(a[0] if len(a) == 1 else a)


def M(loc=(0, 0, 0), rot=(0, 0, 0), scl=None):
    m = Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot], "XYZ").to_matrix().to_4x4()
    if scl is not None:
        m = m @ Matrix.Diagonal((scl[0], scl[1], scl[2], 1.0))
    return m


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


def bevel_edges(bm, edges, off, seg=1):
    if edges:
        bmesh.ops.bevel(bm, geom=list(edges) + list({v for e in edges for v in e.verts}), offset=off, offset_type="OFFSET",
                        segments=seg, profile=0.5, affect="EDGES", clamp_overlap=True)
    return bm


def bevel_sharp(bm, off, seg=1, ang=50):
    bm.normal_update()
    es = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(ang)]
    return bevel_edges(bm, es, off, seg)


def rbox(size, loc=(0, 0, 0), bev=0.0, seg=1, rot=(0, 0, 0), m=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bev > 0:
        bevel_edges(bm, list(bm.edges), bev, seg)
    mm = M(loc, rot)
    return xf(bm, m @ mm if m is not None else mm)


def bb(x0, x1, y0, y1, z0, z1, bev=0.0, seg=1, m=None):
    return rbox((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), bev, seg, m=m)


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


def cyl(r, h, loc=(0, 0, 0), rot=(0, 0, 0), seg=12, r2=None, bev=0.0, center=False, m=None, cap0=True, cap1=True):
    z0 = -h / 2 if center else 0.0
    rt = r if r2 is None else r2
    if bev > 0:
        prof = [(r - bev, z0), (r, z0 + bev), (rt, z0 + h - bev), (rt - bev, z0 + h)]
    else:
        prof = [(r, z0), (rt, z0 + h)]
    mm = M(loc, rot)
    return lathe(prof, seg, m @ mm if m is not None else mm, cap0=cap0, cap1=cap1)


def rr_pts(w, d, r, cs):
    hw, hd = w / 2, d / 2
    if cs <= 0 or r <= 1e-6:
        return [(hw, hd), (-hw, hd), (-hw, -hd), (hw, -hd)]
    r = min(r, hw - 1e-3, hd - 1e-3)
    pts = []
    for cx, cy, a0 in ((hw - r, hd - r, 0), (-(hw - r), hd - r, 90), (-(hw - r), -(hd - r), 180), (hw - r, -(hd - r), 270)):
        for k in range(cs + 1):
            a = math.radians(a0 + 90.0 * k / cs)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def rr_loft(w, d, r, cs, prof, m=None, cap0=True, cap1=True, closed=False):
    bm = bmesh.new()
    rings = []
    for ins, z in prof:
        rr = max(r - ins, 0.004) if cs > 0 else 0.0
        rings.append([bm.verts.new((x, y, z)) for x, y in rr_pts(w - 2 * ins, d - 2 * ins, rr, cs)])
    N = len(rings[0])
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for a, b in pairs:
        for j in range(N):
            j2 = (j + 1) % N
            bm.faces.new((a[j], a[j2], b[j2], b[j]))
    if not closed:
        if cap0:
            bm.faces.new(list(reversed(rings[0])))
        if cap1:
            bm.faces.new(rings[-1])
    return xf(bm, m)


def bar(p0, p1, w, t, ch=0.0, up=(0, 0, 1), caps=True):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    z = d / L
    x = Vector(up).cross(z)
    if x.length < 1e-6:
        x = Vector((1, 0, 0)).cross(z) if abs(z.x) < 0.9 else Vector((0, 1, 0)).cross(z)
    x.normalize()
    y = z.cross(x).normalized()
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = p0
    if ch > 0:
        return rr_loft(w, t, ch, 1, [(0.0, 0.0), (0.0, L)], m, caps, caps)
    return rr_loft(w, t, 0.0, 0, [(0.0, 0.0), (0.0, L)], m, caps, caps)


def area2(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))


def prism(pts, t, m=None, bev=0.0, bseg=1, z0=None):
    if area2(pts) < 0:
        pts = pts[::-1]
    z0 = -t / 2 if z0 is None else z0
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]
    hi = [bm.verts.new((x, y, z0 + t)) for x, y in pts]
    n = len(pts)
    for j in range(n):
        j2 = (j + 1) % n
        bm.faces.new((lo[j], lo[j2], hi[j2], hi[j]))
    f0 = bm.faces.new(list(reversed(lo)))
    f1 = bm.faces.new(hi)
    if bev > 0:
        bevel_edges(bm, [e for e in bm.edges if f0 in e.link_faces or f1 in e.link_faces], bev, bseg)
    return xf(bm, m)


def decal(pts, m=None, w=0.0):
    if area2(pts) < 0:
        pts = pts[::-1]
    bm = bmesh.new()
    bm.faces.new([bm.verts.new((x, y, w)) for x, y in pts])
    return xf(bm, m)


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def circ(cx, cy, r, n=10, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * k / n), cy + r * math.sin(a0 + 2 * math.pi * k / n)) for k in range(n)]


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


def tube(ctrl, rf, k=8, steps=4, closed=False, up=None, caps=True, cap_rings=2):
    ctrl = [Vector(c) for c in ctrl]
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
        r = rf(u)
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
                ring = [bm.verts.new(center + (normals[end] * math.cos(2 * math.pi * j / k) + b * math.sin(2 * math.pi * j / k)) * rr) for j in range(k)]
                for j in range(k):
                    bm.faces.new((prev[j], prev[(j + 1) % k], ring[(j + 1) % k], ring[j]))
                prev = ring
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


class Prop:
    def __init__(self, name, budget, escala=1.0):
        self.name = name
        self.budget = budget
        self.escala = escala
        self.parts = []

    def add(self, bm, role, ang=50.0):
        self.parts.append((bm, role, ang))
        return bm


def pill(cx, cy, L, h, a=0.0, n=3):
    pts = []
    for k in range(n + 1):
        t = -math.pi / 2 + math.pi * k / n
        pts.append((L / 2 + h * math.cos(t), h * math.sin(t)))
    for k in range(n + 1):
        t = math.pi / 2 + math.pi * k / n
        pts.append((-L / 2 + h * math.cos(t), h * math.sin(t)))
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def blob(r, loc, sub=2, jit=0.0, seed=0):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    rnd = random.Random(seed)
    for v in bm.verts:
        v.co *= 1.0 + rnd.uniform(-jit, jit)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(loc)) @ Matrix.Diagonal((r[0], r[1], r[2], 1.0)), verts=bm.verts)
    return bm


def wheel(p, c, r, w, axis="x", tire="black", hub="metal", seg=12, rh=None, detail=True):
    m = M(c, (0, 90, 0) if axis == "x" else (90, 0, 0))
    rh = rh if rh is not None else r * 0.62
    if detail:
        prof = [(rh, -w / 2), (r * 0.93, -w / 2), (r, -w / 2 + 0.08 * w), (r, w / 2 - 0.08 * w), (r * 0.93, w / 2), (rh, w / 2)]
    else:
        prof = [(rh, -w / 2), (r, -w / 2 + 0.12 * w), (r, w / 2 - 0.12 * w), (rh, w / 2)]
    a0 = 0.0 if axis == "x" else math.radians(270.0 % (360.0 / seg))
    p.add(lathe(prof, seg, m, cap0=False, cap1=False, a0=a0), tire)
    p.add(cyl(rh, w * 0.86, seg=seg if detail else max(6, seg - 2), center=True, m=m), hub)


def ring(p, c, R, rt, seg, role, rot=(0, 0, 0), n=4):
    prof = [(R + rt * math.cos(2 * math.pi * k / n + math.pi / n), rt * math.sin(2 * math.pi * k / n + math.pi / n)) for k in range(n)]
    p.add(lathe(prof, seg, M(c, rot), closed=True), role)



def palette_image():
    img = bpy.data.images.new("criaturas_paleta", 128, 64, alpha=True)
    px = [0.0] * (128 * 64 * 4)
    for i, (_, hx) in enumerate(PAL):
        r, g, b = hex_rgb(hx)
        gx, gy = i % 8, i // 8
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * 128 + x) * 4
                px[o:o + 4] = (r, g, b, 1.0)
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "criaturas_paleta.png")
    img.file_format = "PNG"
    img.save()
    return img


def palette_material(img):
    mat = bpy.data.materials.new("Criaturas_Paleta")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.6
    return mat


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


def render_setup(scene, threads):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    scene.cycles.max_bounces = 5
    scene.render.threads_mode = "FIXED"
    scene.render.threads = threads
    scene.render.resolution_x, scene.render.resolution_y = 1600, 900
    pct = arg("--pct")
    scene.render.resolution_percentage = int(pct) if isinstance(pct, str) else 100
    scene.render.image_settings.file_format = "PNG"
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    world = bpy.data.worlds.new("Sky")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*lin(hex_rgb("BFE3F2")), 1.0)
    bg.inputs[1].default_value = 0.8
    scene.world = world
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.6
    sun.angle = math.radians(10)
    so = bpy.data.objects.new("Sun", sun)
    so.rotation_euler = (math.radians(48), 0.0, math.radians(-34))
    scene.collection.objects.link(so)
    return so


MATS = {}


def mat_rgb(hx, rough=0.9, emit=0.0, alpha=1.0, spec=0.5):
    key = (hx, rough, emit, alpha)
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new("M_" + hx)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(hex_rgb(hx)), 1.0)
    b.inputs["Roughness"].default_value = rough
    if emit > 0:
        b.inputs["Emission Color"].default_value = (*lin(hex_rgb(hx)), 1.0)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
    MATS[key] = m
    return m


class Stage:
    def __init__(self, objs):
        self.objs = objs
        self.made = []

    def link(self, o):
        bpy.context.scene.collection.objects.link(o)
        self.made.append(o)
        return o

    def put(self, name, x, y, rz=0.0, z=0.0):
        o = bpy.data.objects.new(name + "_i", self.objs[name].data)
        o.location = (x, y, z)
        o.rotation_euler = (0, 0, math.radians(rz))
        return self.link(o)

    def box(self, x0, x1, y0, y1, z0, z1, mat, bev=0.0):
        bm = bb(x0, x1, y0, y1, z0, z1, bev, 2 if bev > 0 else 1)
        me = bpy.data.meshes.new("b")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        if bev > 0:
            me.shade_smooth()
        return self.link(bpy.data.objects.new("b", me))

    def quad(self, x0, x1, y0, y1, z, mat):
        me = bpy.data.meshes.new("q")
        me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
        me.materials.append(mat)
        return self.link(bpy.data.objects.new("q", me))

    def vquad(self, pts, mat):
        me = bpy.data.meshes.new("v")
        me.from_pydata(pts, [], [tuple(range(len(pts)))])
        me.materials.append(mat)
        return self.link(bpy.data.objects.new("v", me))

    def area(self, loc, size, power, sy=None, rot=(0, 0, 0), color=(1.0, 0.97, 0.9)):
        L = bpy.data.lights.new("A", "AREA")
        L.shape = "RECTANGLE"
        L.size = size
        L.size_y = sy if sy is not None else size
        L.energy = power
        L.color = color
        o = bpy.data.objects.new("A", L)
        o.location = loc
        o.rotation_euler = [math.radians(a) for a in rot]
        return self.link(o)

    def camera(self, loc, target, lens):
        cd = bpy.data.cameras.new("Cam")
        cd.lens = lens
        cd.clip_start = 0.1
        cd.clip_end = 2000
        co = bpy.data.objects.new("Cam", cd)
        co.location = loc
        co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.camera = co
        return self.link(co)

    def clear(self):
        for o in self.made:
            bpy.data.objects.remove(o)
        self.made = []



def fit_camera(st, pts, el, az, lens):
    scene = bpy.context.scene
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    f = -d
    right = f.cross(Vector((0, 0, 1))).normalized()
    upv = right.cross(f).normalized()
    tx = 18.0 / lens
    ty = tx * scene.render.resolution_y / scene.render.resolution_x
    c = sum(pts, Vector()) / len(pts)
    for _ in range(5):
        q = [(p - c).dot(right) for p in pts], [(p - c).dot(upv) for p in pts], [(p - c).dot(d) for p in pts]
        D = max(max(z + abs(x) / (tx * 0.92) for x, z in zip(q[0], q[2])), max(z + abs(y) / (ty * 0.9) for y, z in zip(q[1], q[2])))
        sxs = [x / (D - z) for x, z in zip(q[0], q[2])]
        sys_ = [y / (D - z) for y, z in zip(q[1], q[2])]
        c = c + right * ((max(sxs) + min(sxs)) / 2 * D) + upv * ((max(sys_) + min(sys_)) / 2 * D)
    q = [(p - c).dot(right) for p in pts], [(p - c).dot(upv) for p in pts], [(p - c).dot(d) for p in pts]
    D = max(max(z + abs(x) / (tx * 0.92) for x, z in zip(q[0], q[2])), max(z + abs(y) / (ty * 0.9) for y, z in zip(q[1], q[2])))
    return st.camera(c + d * D, c, lens)


def palo(p0, p1, r, seg=6, r2=None, cap0=True, cap1=True):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    m = Matrix.Translation(p0) @ q.to_matrix().to_4x4()
    return lathe([(r, 0.0), (r if r2 is None else r2, d.length)], seg, m, cap0=cap0, cap1=cap1)




def finalize(p):
    verts, faces, uvs, nrms = [], [], [], []
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    S = Matrix.Diagonal((p.escala, p.escala, p.escala, 1.0))
    for bm, role, ang in p.parts:
        ng = [f for f in bm.faces if len(f.verts) > 4]
        if ng:
            bmesh.ops.triangulate(bm, faces=ng, quad_method="BEAUTY", ngon_method="BEAUTY")
        bm.normal_update()
        roles = [role(f.calc_center_median(), f.normal.copy()) if callable(role) else role for f in bm.faces]
        bmesh.ops.transform(bm, matrix=S, verts=bm.verts)
        bm.normal_update()
        bm.verts.index_update()
        base = len(verts)
        for v in bm.verts:
            verts.append(v.co.copy())
            for i in range(3):
                mn[i] = min(mn[i], v.co[i])
                mx[i] = max(mx[i], v.co[i])
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
    return verts, faces, uvs, nrms, tris, mn, mx


def make_object(p, mat):
    verts, faces, uvs, nrms, tris, mn, mx = finalize(p)
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
    return ob, tris, mn, mx


def rb(v, s=1.0):
    return [round(-v[0] * s, 3), round(v[2] * s, 3), round(v[1] * s, 3)]


def envolver(pts, f, cuts=2, fuera=None):
    if area2(pts) < 0:
        pts = pts[::-1]
    bm = bmesh.new()
    cara = bm.faces.new([bm.verts.new((u, v, 0.0)) for u, v in pts])
    bmesh.ops.triangulate(bm, faces=[cara], quad_method="BEAUTY", ngon_method="EAR_CLIP")
    if cuts:
        bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        v.co = f(v.co.x, v.co.y)
    bm.normal_update()
    if fuera is not None:
        total = sum((fc.normal.dot(fuera(fc.calc_center_median())) for fc in bm.faces), 0.0)
        if total < 0:
            bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    return bm


def escalar_pts(pts, k):
    cu = sum(u for u, _ in pts) / len(pts)
    cv = sum(v for _, v in pts) / len(pts)
    return [(cu + (u - cu) * k, cv + (v - cv) * k) for u, v in pts]


def suave(pts, pasos=3):
    return [(v.x, v.y) for v in catmull([Vector((u, v, 0)) for u, v in pts], pasos, closed=True)]


def aro(p, m, R, rt, role, seg=16, n=4, sx=1.0, sy=1.0):
    prof = [(R + rt * math.cos(2 * math.pi * k / n + math.pi / n), rt * math.sin(2 * math.pi * k / n + math.pi / n)) for k in range(n)]
    p.add(lathe(prof, seg, m, closed=True, sx=sx, sy=sy), role)


def base_normal(n):
    n = Vector(n).normalized()
    m = frame_from_normal(n)
    return n, Vector((m[0][0], m[1][0], m[2][0])), Vector((m[0][1], m[1][1], m[2][1]))


def ojo(p, c, n, r, pupila=None, borde=True, seg=14):
    n, t, b = base_normal(n)
    centro = Vector(c) + n * (r * 0.3)
    p.add(ellipsoid((r, r, r), Matrix.Translation(centro), seg, seg - 4), "white", 75)
    if borde:
        aro(p, Matrix.Translation(Vector(c) + n * (r * 0.05)) @ frame_from_normal(n), r * 0.93, r * 0.11, "ink", seg)
    if pupila is not None:
        d = (n + t * pupila[0] + b * pupila[1]).normalized()
        p.add(ellipsoid((r * 0.46, r * 0.46, r * 0.22), Matrix.Translation(centro + d * r * 0.9) @ frame_from_normal(d), 10, 6), "ink", 75)
    return centro, r


def ceja(p, pts, grosor, role="ink"):
    p.add(tube([Vector(q) for q in pts], lambda u: grosor * (0.75 + 0.5 * math.sin(math.pi * u)), 6, 3), role, 60)


def parche(p, centro, n, r, correa):
    n, t, b = base_normal(n)
    p.add(ellipsoid((r * 1.08, r * 1.08, r * 0.62), Matrix.Translation(Vector(centro) + n * (r * 0.52)) @ frame_from_normal(n), 14, 8), "ink", 60)
    p.add(tube([Vector(q) for q in correa], lambda u: 0.11, 6, 4), "ink", 60)


def calavera(cu, cv, s, capa):
    capa("cream", 1, [(cu + x * s, cv + y * s) for x, y in circ(0, 0.18, 0.62, 18)])
    capa("cream", 1, [(cu + x * s, cv + y * s) for x, y in rect(-0.36, 0.36, -0.62, -0.12)])
    for sx in (-1, 1):
        capa("ink", 2, [(cu + x * s, cv + y * s) for x, y in circ(0.24 * sx, 0.1, 0.17, 10)])
    capa("ink", 2, [(cu + x * s, cv + y * s) for x, y in [(-0.07, -0.2), (0.07, -0.2), (0.0, -0.05)]])
    for x0 in (-0.14, 0.1):
        capa("ink", 2, [(cu + x * s, cv + y * s) for x, y in rect(x0, x0 + 0.05, -0.6, -0.36)])


def llaves(cu, cv, s, capa):
    for ang in (38, -38):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        capa("cream", 0, [(cu + x * s, cv + y * s) for x, y in pill(0, 0, 2.3, 0.13, a, 3)])
        for e in (-1, 1):
            ex, ey = e * 1.25 * ca, e * 1.25 * sa
            capa("cream", 0, [(cu + x * s, cv + y * s) for x, y in circ(ex, ey, 0.3, 12)])
            nx, ny = ex + e * 0.2 * ca, ey + e * 0.2 * sa
            capa("ink", 1, [(cu + (nx + x * ca - y * sa) * s, cv + (ny + x * sa + y * ca) * s) for x, y in rect(-0.16, 0.16, -0.09, 0.09)])


def bandera(p, mastil0, mastil1, largo, alto, onda=0.32, k=2.1):
    p.add(palo(mastil0, mastil1, 0.13, 6), "dwood")
    p.add(ellipsoid((0.22, 0.22, 0.22), Matrix.Translation(Vector(mastil1) + Vector((0, 0, 0.12))), 8, 6), "gold")
    y0 = mastil1[1] + 0.05
    z1 = mastil1[2] - 0.15
    z0 = z1 - alto

    def wave(u):
        return onda * math.sin((u - y0) * k) * min(1.0, max(0.0, u - y0) / 0.6)

    contorno = [(y0, z0), (y0 + largo * 0.82, z0 - 0.1), (y0 + largo * 0.9, z0 + alto * 0.18), (y0 + largo, z0 + alto * 0.3),
                (y0 + largo * 0.88, z0 + alto * 0.5), (y0 + largo * 1.02, z0 + alto * 0.72), (y0 + largo * 0.92, z0 + alto * 0.86), (y0 + largo, z1), (y0, z1)]
    cu, cv = y0 + largo * 0.47, z0 + alto * 0.5
    s = alto / 2.6
    for lado in (1, -1):
        def f(off, lado=lado):
            return lambda u, v: Vector((wave(u) + lado * (0.05 + off), u, v))

        def fuera(c, lado=lado):
            return Vector((lado, 0, 0))
        p.add(envolver(contorno, f(0.0), 3, fuera), "ink", 30)

        def capa(role, nivel, pts, f=f, fuera=fuera):
            p.add(envolver(pts, f(0.012 * (nivel + 1)), 2, fuera), role, 30)
        llaves(cu, cv, s, capa)
        calavera(cu, cv + 0.05 * s, s, lambda role, nivel, pts, capa=capa: capa(role, nivel + 2, pts))


def trabuco(p, boca, largo=2.0, r=0.2, role="gold"):
    bx, by, bz = boca
    m = Matrix.Translation((bx, by + largo, bz)) @ Euler((math.radians(90), 0, 0)).to_matrix().to_4x4()
    p.add(lathe([(r * 0.9, 0.0), (r, 0.15), (r * 0.8, largo * 0.55), (r * 1.15, largo * 0.85), (r * 2.0, largo), (r * 1.4, largo - 0.02)], 10, m, cap0=True, cap1=True), role, 40)
    p.add(lathe([(r * 1.25, -0.1), (r * 1.25, 0.25)], 10, m), "dwood", 40)


def boca_envuelta(p, f, fuera, poly, dientes, oro=None, lengua=None, cuts=3):
    p.add(envolver(escalar_pts(poly, 1.13), f(0.03), cuts, fuera), "ink", 25)
    p.add(envolver(poly, f(0.055), cuts, fuera), "dred", 25)
    for i, d in enumerate(dientes):
        p.add(envolver(d, f(0.08), 1, fuera), "gold" if i == oro else "cream", 25)
    if lengua:
        p.add(envolver(lengua, f(0.075), 2, fuera), "pink", 25)


def dientes_en(u0, u1, v_de, alto, n, hueco=None):
    out = []
    w = (u1 - u0) / n
    for i in range(n):
        if i == hueco:
            continue
        a, b = u0 + w * i + w * 0.08, u0 + w * (i + 1) - w * 0.08
        va, vb = v_de(a), v_de(b)
        out.append([(a, va), (b, vb), (b, vb + alto), (a, va + alto)])
    return out


def r_barril(y):
    return 1.95 + 0.45 * (1 - (y / 4.5) ** 2)


def p_barril():
    p = Prop("PirataBarril", 9000)
    pts = {}

    def bp(y, a, off=0.0):
        r = r_barril(y) + off
        ar = math.radians(a)
        return Vector((r * math.sin(ar), y, r * math.cos(ar)))

    def fuera_b(c):
        return Vector((c.x, 0, c.z))

    prof = [(r_barril(z), z) for z in [-4.5 + 9 * k / 12 for k in range(13)]]
    p.add(lathe(prof, 16, M((0, 0, 0), (90, 0, 0)), a0=math.pi / 16),
          lambda c, n: ("dwood" if abs(n.y) > 0.85 else ("wood" if int((math.atan2(c.x, c.z) + math.pi) / (2 * math.pi) * 16 + 0.5) % 2 == 0 else "wood2")), 30)
    for y in (-4.25, 1.9, 3.95):
        aro(p, M((0, y, 0), (90, 0, 0)), r_barril(y) + 0.03, 0.13, "iron", 16)
    p.add(envolver(suave([(0.55 + 1.15 * math.cos(2 * math.pi * k / 10), 40 * math.sin(2 * math.pi * k / 10)) for k in range(10)], 2), lambda u, v: bp(u, v, 0.025), 2, fuera_b), "ink", 30)
    p.add(tube([bp(0.55 + 1.15 * math.cos(2 * math.pi * k / 14), 40 * math.sin(2 * math.pi * k / 14), 0.06) for k in range(14)], lambda u: 0.16, 6, 3, closed=True), "tan", 40)
    pts["asiento"] = (0, 0.75, 0.55)
    p.add(cyl(1.35, 1.25, (0, -4.45, 0), (90, 0, 0), 14), "iron", 40)
    aro(p, M((0, -5.68, 0), (90, 0, 0)), 1.35, 0.14, "metal", 14)
    for sx in (-1, 1):
        aro(p, M((sx * 1.45, -5.05, 0), (0, 90, 0)), 0.3, 0.07, "iron", 8)
    p.add(cyl(0.45, 0.35, (0, -5.7, 0), (90, 0, 0), 10), "grey")
    pts["helices"] = [((0, -6.05, 0), 1.0)]
    for lado in (1, -1):
        e = bp(-2.65, 33 * lado)
        n = Vector((e.x, -0.35, e.z))
        c, r = ojo(p, e, n, 0.92, None)
        if lado == -1:
            parche(p, e, n, 0.92, [bp(-2.25, -12, 0.06), bp(-1.6, 10, 0.06), bp(-1.25, 45, 0.06), bp(-1.2, 80, 0.06), bp(-1.35, 110, 0.06)])
            ceja(p, [c + Vector((-0.75, -0.25, 0.95)), c + Vector((0.0, -0.45, 1.2)), c + Vector((0.75, -0.3, 1.02))], 0.17)
        else:
            pts.setdefault("ojos", []).append((tuple(c), r))
            ceja(p, [c + Vector((-0.8, -0.35, 0.82)), c + Vector((0.0, -0.45, 1.1)), c + Vector((0.8, -0.25, 1.32))], 0.17)
    for lado in (1, -1):
        def fb(off, lado=lado):
            return lambda u, v: bp(u, v * lado, off)
        poly = suave([(-4.2, 88), (-3.5, 91), (-2.7, 88), (-2.0, 80), (-1.7, 72), (-1.95, 86), (-2.5, 104), (-3.3, 116), (-4.2, 121)], 2)
        boca_envuelta(p, fb, fuera_b, poly, dientes_en(-4.1, -2.3, lambda u: 90 - 6 * max(0, u + 2.9) / 0.6, 9, 4, hueco=1), oro=2,
                      lengua=suave(circ(-3.6, 113, 0.42, 8), 1))
    for lado in (1, -1):
        a0 = 100 * lado
        p.add(envolver(rect(0.6, 1.8, a0 - 14, a0 + 14), lambda u, v: bp(u, v, 0.03), 2, fuera_b), "metal", 30)
        for y, a in ((0.75, a0 - 10), (1.65, a0 - 10), (0.75, a0 + 10), (1.65, a0 + 10)):
            p.add(ellipsoid((0.09, 0.09, 0.09), Matrix.Translation(bp(y, a, 0.06)), 6, 4), "ink")
    for ang in (35, -35):
        p.add(envolver([(u * 0.6 + 2.9, v * 22 - 150) for u, v in pill(0, 0, 1.6, 0.25, math.radians(ang), 3)], lambda u, v: bp(u, v, 0.03), 2, fuera_b), "cream", 30)
    p.add(tube([Vector((1.7, -3.7, 0.7)), Vector((2.45, -3.55, 0.95)), Vector((2.75, -3.0, 1.6)), Vector((2.85, -2.6, 2.35))], lambda u: 0.24, 8, 3), "iron", 40)
    aro(p, M((2.85, -2.6, 2.4), (0, 0, 0)), 0.26, 0.06, "rust", 8)
    pts["humo"] = (2.85, -2.6, 2.5)
    tabla = [(1.6, -0.95), (6.0, -1.05), (10.35, -1.15), (10.6, -0.6), (10.15, -0.2), (10.7, 0.35), (10.25, 0.85), (10.5, 1.4), (6.0, 1.5), (1.6, 1.45)]
    mt = M((0, 0, -1.05), (0, -5, 0))
    p.add(prism(tabla, 0.3, mt), lambda c, n: "dwood" if abs(n.z) < 0.5 else ("wood" if c.y < -0.2 or c.y > 0.65 else "wood2"), 40)
    for x, y in ((3.0, -0.6), (3.0, 1.0), (8.6, -0.6), (8.6, 1.0), (5.2, 0.25)):
        p.add(ellipsoid((0.07, 0.07, 0.04), mt @ Matrix.Translation((x, y, 0.16)), 5, 3), "ink")
    for ang in (40, -40):
        p.add(prism(pill(6.9, 0.25, 1.4, 0.2, math.radians(ang), 3), 0.04, mt @ Matrix.Translation((0, 0, 0.17))), "cream")
    tabla_s = suave([(-1.6, -0.95), (-5.5, -1.05), (-9.0, -0.75), (-10.6, 0.25), (-9.0, 1.25), (-5.5, 1.55), (-1.6, 1.5)], 3)
    ms = M((0, 0, -1.0), (0, 9, 0))
    p.add(prism(tabla_s, 0.32, ms, bev=0.1, bseg=2),
          lambda c, n: "orange" if abs(c.y - 0.3) < 0.2 else ("teal" if abs(c.y - 0.3) < 0.34 else "cream"), 40)
    p.add(prism([(-9.2, 0.0), (-8.4, 0.25), (-9.0, 0.6)], 0.08, ms @ Matrix.Translation((0, 0.05, -0.22)) @ Euler((math.radians(90), 0, 0)).to_matrix().to_4x4()), "teal")
    for sx in (1, -1):
        aro(p, M((sx * 2.55, 0.25, -1.05 - (0.12 if sx > 0 else 0.2)), (0, 90, 0)), 0.55, 0.07, "tan", 10, sx=0.55, sy=1.75)
    cola = [(-3.3, 0.0), (3.3, 0.0), (3.0, 1.25), (-3.0, 1.25)]
    p.add(prism(cola, 0.24, M((0, 4.15, 0.45), (0, 3, 0))), lambda c, n: "wood" if abs(n.z) > 0.5 else "dwood", 40)
    bandera(p, (0, 3.6, 1.8), (0, 3.85, 6.5), 3.6, 2.7)
    for sx in (1, -1):
        p.add(palo((sx * 0.9, -1.6, -1.9), (sx * 1.45, -1.7, -2.95), 0.12, 6), "iron")
        wheel(p, (sx * 1.6, -1.7, -3.0), 0.55, 0.35, "x", "ink", "red", 12)
    pts["canones"] = []
    for sx in (1, -1):
        b = (sx * 2.6, -4.1, -0.75)
        trabuco(p, b, 2.2, 0.2)
        pts["canones"].append(b)
    return p, pts


def r_banera(z):
    prof = [(-1.25, 1.35), (-1.1, 1.55), (-0.3, 1.75), (0.6, 1.9), (1.2, 1.98)]
    for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
        if z <= z1:
            t = max(0.0, (z - z0) / (z1 - z0))
            return r0 + (r1 - r0) * t
    return prof[-1][1]


def p_banera():
    p = Prop("PirataBanera", 9000)
    pts = {}
    SY = 2.3

    def tp(phi, z, off=0.0):
        r = r_banera(z) + off
        a = math.radians(phi)
        return Vector((r * math.sin(a), -SY * r * math.cos(a), z))

    def fuera_t(c):
        return Vector((c.x, c.y / (SY * SY), 0))

    def rol_tina(c, n):
        dentro = n.dot(Vector((c.x, c.y / (SY * SY), 0))) < 0 and c.z < 1.4
        if n.z > 0.6 and c.z < 0:
            return "lblue"
        if dentro:
            return "lblue"
        if math.sin(c.x * 3.1 + c.y * 1.7) * math.sin(c.y * 2.3 - c.z * 2.9) > 0.82 and c.z < 1.1:
            return "rust"
        return "white"

    perfil = [(1.35, -1.25), (1.55, -1.1), (1.75, -0.3), (1.9, 0.6), (1.98, 1.2), (2.08, 1.3), (2.08, 1.45), (1.9, 1.52), (1.78, 1.38), (1.68, 0.6), (1.5, -0.4), (1.25, -0.8), (0.0, -0.8)]
    p.add(lathe([(r, z) for r, z in perfil], 24, None, sx=1.0, sy=SY, a0=0.0), rol_tina, 35)
    p.add(decal(suave([(x * 1.62, y * 1.62 * SY) for x, y in circ(0, 0, 1.0, 12)], 2), Matrix.Translation((0, 0, 0.25))), "water", 30)
    rnd = random.Random(7)
    for k in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.9, 1.45)
        s = rnd.uniform(0.25, 0.42)
        p.add(ellipsoid((s, s, s * 0.7), Matrix.Translation((rr * math.cos(a), SY * rr * math.sin(a) * 0.95, 0.3)), 8, 5), "white", 70)
    pts["asiento"] = (0, 0.7, -0.45)
    for sx in (1, -1):
        for sy in (1, -1):
            c = Vector((sx * 1.15, sy * 2.6, -1.3))
            p.add(palo(c + Vector((0, 0, 0.3)), c - Vector((0, 0, 0.35)), 0.2, 8, 0.15), "gold")
            p.add(ellipsoid((0.32, 0.32, 0.26), Matrix.Translation(c - Vector((0, 0, 0.5))), 8, 6), "gold", 50)
            for k in (-1, 0, 1):
                d = Vector((sx * 0.25 + k * 0.18, -0.28 + abs(k) * 0.08, 0))
                p.add(tube([c - Vector((0, 0, 0.5)), c + d * 1.3 - Vector((0, 0, 0.72))], lambda u: 0.11 - 0.04 * u, 5, 2), "gold", 50)
    lata = (0, -4.75, 0.45)
    p.add(cyl(1.15, 1.45, lata, (90, 0, 0), 14), lambda c, n: "metal" if abs(n.y) > 0.8 else ("teal" if c.z > 0.75 or c.z < 0.15 else "orange"), 40)
    for y in (-4.85, -5.95):
        aro(p, M((0, y, 0.45), (90, 0, 0)), 1.15, 0.07, "metal", 14)
    p.add(cyl(0.4, 0.3, (0, -6.1, 0.45), (90, 0, 0), 10), "grey")
    pts["helices"] = [((0, -6.45, 0.45), 1.0)]
    p.add(palo((0.55, -5.4, 1.4), (0.65, -5.2, 2.6), 0.2, 8), "iron")
    aro(p, M((0.65, -5.2, 2.62)), 0.21, 0.06, "rust", 8)
    pts["humo"] = (0.65, -5.2, 2.75)
    for lado in (1, -1):
        e = tp(36 * lado, 1.45, 0.05) + Vector((0, 0, 0.05))
        n = Vector((0.25 * lado, -0.55, 1.0))
        c, r = ojo(p, e, n, 0.85, None)
        if lado == 1:
            parche(p, e, n, 0.85, [tp(52, 1.48, 0.12), tp(70, 1.1, 0.14), tp(80, 0.4, 0.12), tp(90, -0.3, 0.1)])
            ceja(p, [c + Vector((0.65, -0.25, 0.92)), c + Vector((0.0, -0.4, 1.12)), c + Vector((-0.7, -0.3, 0.98))], 0.16)
        else:
            pts.setdefault("ojos", []).append((tuple(c), r))
            ceja(p, [c + Vector((0.7, -0.3, 0.78)), c + Vector((0.0, -0.45, 1.08)), c + Vector((-0.7, -0.2, 1.3))], 0.16)
    for lado in (1, -1):
        def ft(off, lado=lado):
            return lambda u, v: tp(u * lado, v, off)
        poly = suave([(14, 0.35), (32, 0.42), (52, 0.38), (66, 0.55), (72, 0.75), (70, 0.2), (58, -0.35), (38, -0.62), (14, -0.65)], 2)
        boca_envuelta(p, ft, fuera_t, poly, dientes_en(16, 56, lambda u: 0.36 - 0.22 * max(0.0, (u - 40) / 16), -0.24, 4, hueco=2), oro=0,
                      lengua=suave(circ(30, -0.42, 0.18, 8), 1) if lado == 1 else None)
    plancha = suave([(1.7, -0.9), (5.0, -1.0), (8.2, -0.9), (9.6, -0.35), (10.1, 0.3), (9.6, 0.95), (8.2, 1.45), (5.0, 1.55), (1.7, 1.5)], 2)
    mp = M((0, 0.2, -0.15), (0, -6, 0))
    p.add(prism(plancha, 0.34, mp, bev=0.08), lambda c, n: "teal" if n.z > 0.5 else ("cream" if n.z > -0.5 else "lgrey"), 40)
    for x, y in ((3.0, 0.0), (4.4, 0.9), (5.6, -0.3), (6.9, 0.6), (8.3, 0.1), (3.2, 1.05)):
        p.add(decal(circ(x, y, 0.2, 8), mp, 0.18), "cream")
    for a, b in (((3.2, -0.6), (6.8, 1.1)), ((3.2, 1.1), (6.8, -0.6))):
        p.add(palo(mp @ Vector((a[0], a[1], -0.2)), mp @ Vector((b[0], b[1], -0.75)), 0.07, 5), "iron")
    puerta = rect(-9.7, -1.7, -1.0, 1.6)
    mpu = M((0, 0.2, -0.1), (0, 4, 0))
    p.add(prism(puerta, 0.3, mpu, bev=0.05), lambda c, n: "wood2" if abs(n.z) > 0.5 else "dwood", 40)
    for x0, x1 in ((-9.2, -6.1), (-5.6, -2.3)):
        for y0, y1 in ((-0.7, 0.15), (0.45, 1.3)):
            p.add(prism(rect(x0, x1, y0, y1), 0.06, mpu @ Matrix.Translation((0, 0, 0.17))), "wood")
    p.add(ellipsoid((0.26, 0.26, 0.22), mpu @ Matrix.Translation((-8.9, 0.3, 0.45)), 10, 6), "gold", 60)
    p.add(palo(mpu @ Vector((-8.9, 0.3, 0.12)), mpu @ Vector((-8.9, 0.3, 0.32)), 0.08, 6), "gold")
    p.add(palo((0, 3.9, 0.7), (0, 8.4, 1.15), 0.16, 8), "wood")
    escoba = [(-0.45, 0.0), (0.45, 0.0), (1.9, 1.9), (-1.9, 1.9)]
    p.add(prism(escoba, 0.4, M((0, 8.1, 1.12), (0, 0, 0))), lambda c, n: "straw" if c.y < 9.7 or abs(n.z) > 0.5 else "dwood", 40)
    aro(p, M((0, 8.35, 1.12), (90, 0, 0)), 0.42, 0.1, "red", 10, sx=1.4, sy=0.6)
    bandera(p, (0, 3.75, 1.1), (0, 4.05, 6.0), 3.5, 2.6)
    pato = Vector((-1.2, 3.35, 1.62))
    p.add(ellipsoid((0.38, 0.5, 0.32), Matrix.Translation(pato), 10, 6), "yellow", 60)
    p.add(ellipsoid((0.26, 0.26, 0.26), Matrix.Translation(pato + Vector((0, -0.32, 0.38))), 10, 6), "yellow", 60)
    p.add(ellipsoid((0.16, 0.14, 0.06), Matrix.Translation(pato + Vector((0, -0.6, 0.33))), 6, 4), "orange")
    for sx in (1, -1):
        p.add(ellipsoid((0.05, 0.05, 0.06), Matrix.Translation(pato + Vector((sx * 0.13, -0.53, 0.45))), 5, 3), "ink")
    pts["canones"] = []
    for sx in (1, -1):
        b = (sx * 2.25, -2.9, 1.0)
        trabuco(p, b, 1.8, 0.18)
        pts["canones"].append(b)
    return p, pts


def p_helice():
    p = Prop("HelicePirata", 1200)
    p.add(ellipsoid((0.62, 0.7, 0.62), Matrix.Translation((0, -0.45, 0)), 12, 8), "red", 70)
    p.add(ellipsoid((0.18, 0.1, 0.12), Matrix.Translation((0.25, -1.05, 0.25)), 6, 4), "white")
    p.add(cyl(0.38, 0.55, (0, 0.25, 0), (90, 0, 0), 10), "grey")
    pala = [(0.3, -0.22), (1.2, -0.42), (2.6, -0.42), (3.45, -0.3), (3.8, 0.0), (3.45, 0.3), (2.6, 0.4), (1.2, 0.36), (0.3, 0.22)]
    for giro in (0, 180):
        m = Euler((0, math.radians(giro), 0)).to_matrix().to_4x4() @ frame((0, 0, 0), (1, 0, 0), (0, 0, 1)) @ Euler((math.radians(12), 0, 0)).to_matrix().to_4x4()
        p.add(prism(pala, 0.2, m, bev=0.05), lambda c, n: "yellow" if abs(c.x) > 3.05 else ("red" if abs(c.x) > 2.75 else "wood"), 40)
    m = frame((0, 0, 0), (1, 0, 0), (0, 0, 1))
    for x0 in (1.5, 1.9):
        p.add(prism(rect(x0, x0 + 0.25, -0.5, 0.5), 0.26, m), "cream")
    return p, {}


def p_piloto():
    p = Prop("PilotoPirata", 4000, 1.5)
    p.add(ellipsoid((0.78, 0.62, 0.88), Matrix.Translation((0, 0, 0.88)), 16, 12), lambda c, n: "red" if int((c.z + 0.1) / 0.26) % 2 == 0 else "cream", 50)
    p.add(ellipsoid((0.95, 0.95, 0.93), Matrix.Translation((0, 0, 2.3)), 18, 12), "skin", 60)
    for sx in (1, -1):
        p.add(ellipsoid((0.16, 0.12, 0.24), Matrix.Translation((sx * 0.92, 0.08, 2.22)), 8, 6), "skin2", 60)
    domo = [(0.0, 1.02)] + [(1.03 * math.sin(math.radians(t)), 1.02 * math.cos(math.radians(t))) for t in range(12, 90, 11)] + [(1.03, -0.02)]
    md = M((0, 0.03, 2.38), (-16, 0, 0))
    p.add(lathe(domo, 18, md, cap1=False), "red", 60)
    for t, a in ((40, 20), (38, 120), (48, 200), (55, 290), (25, 250), (62, 60), (60, 160)):
        tr, ar = math.radians(t), math.radians(a)
        q = md @ Vector((1.04 * math.sin(tr) * math.cos(ar), 1.04 * math.sin(tr) * math.sin(ar), 1.03 * math.cos(tr)))
        n = (q - md @ Vector((0, 0, 0))).normalized()
        p.add(ellipsoid((0.15, 0.15, 0.05), Matrix.Translation(q) @ frame_from_normal(n), 8, 4), "cream")
    nudo = Vector((0, 0.98, 2.3))
    p.add(ellipsoid((0.2, 0.2, 0.2), Matrix.Translation(nudo), 8, 6), "red")
    for sx in (1, -1):
        p.add(tube([nudo, nudo + Vector((sx * 0.25, 0.45, -0.25)), nudo + Vector((sx * 0.42, 0.75, -0.6))], lambda u: 0.13 - 0.06 * u, 6, 3), "red")
    for sx, pup in ((1, (-0.35, -0.3)), (-1, (0.4, 0.45))):
        c = Vector((sx * 0.37, -0.8, 2.3))
        n = Vector((sx * 0.35, -0.95, 0.12))
        ojo(p, c, n, 0.35, pup, seg=12)
    ceja(p, [(0.72, -0.82, 2.72), (0.4, -0.95, 2.8), (0.1, -0.98, 2.62)], 0.09)
    ceja(p, [(-0.72, -0.82, 2.66), (-0.4, -0.95, 2.82), (-0.1, -0.98, 2.68)], 0.09)
    p.add(ellipsoid((0.3, 0.3, 0.27), Matrix.Translation((0, -1.05, 2.02)), 10, 8), "skin2", 60)
    p.add(ellipsoid((0.78, 0.58, 0.62), Matrix.Translation((0, -0.42, 1.55)), 14, 10), "ink", 50)
    p.add(ellipsoid((0.34, 0.14, 0.17), Matrix.Translation((0, -0.92, 1.6)), 10, 6), "dred", 60)
    p.add(bb(-0.17, -0.02, -1.02, -0.96, 1.6, 1.74), "cream")
    p.add(bb(0.05, 0.18, -1.02, -0.96, 1.6, 1.74), "cream")
    bigote = [Vector(q) for q in ((-0.82, -0.6, 2.05), (-0.6, -0.86, 1.78), (-0.22, -1.02, 1.82), (0.0, -1.06, 1.86), (0.22, -1.02, 1.82), (0.6, -0.86, 1.78), (0.82, -0.6, 2.05))]
    p.add(tube(bigote, lambda u: 0.05 + 0.11 * math.sin(math.pi * u), 7, 3), "ink", 60)
    aro(p, M((-0.95, 0.05, 1.98), (0, 90, 0)), 0.15, 0.04, "gold", 10)
    p.add(ellipsoid((0.25, 0.25, 0.25), Matrix.Translation((0.66, -0.12, 1.6)), 8, 6), "red")
    return p, {}


HOMBRO = (-0.62, 0.0, 1.38)


def p_brazo():
    p = Prop("BrazoPirata", 1500, 1.5)
    h = Vector(HOMBRO)
    codo = h + Vector((-0.5, -0.12, 0.62))
    muneca = h + Vector((-0.42, -0.28, 1.4))
    p.add(tube([h, codo], lambda u: 0.26, 8, 2), lambda c, n: "red" if int((c.z + 0.05) / 0.22) % 2 == 0 else "cream", 50)
    p.add(tube([codo, muneca], lambda u: 0.2 - 0.03 * u, 8, 2), "skin", 50)
    pu = muneca + Vector((0, -0.04, 0.28))
    p.add(ellipsoid((0.3, 0.27, 0.32), Matrix.Translation(pu), 10, 8), "skin", 60)
    for k in range(4):
        p.add(ellipsoid((0.09, 0.09, 0.09), Matrix.Translation(pu + Vector((-0.2 + 0.13 * k, -0.24, 0.12))), 6, 4), "skin", 60)
    p.add(ellipsoid((0.1, 0.16, 0.09), Matrix.Translation(pu + Vector((0.22, -0.14, -0.02))), 6, 4), "skin", 60)
    p.add(tube([codo + Vector((0.0, 0.0, -0.05)), codo + Vector((0.02, 0.0, 0.12))], lambda u: 0.28, 8, 1), "red")
    return p, {"hombro": HOMBRO}


def cuerpo_pajaro(p, cara):
    p.add(ellipsoid((0.95, 1.15, 0.9), Matrix.Translation((0, 0.1, 0)), 16, 12), lambda c, n: "white" if c.z < 0.15 or c.y < -0.6 else "mgrey", 60)
    p.add(ellipsoid((0.74, 0.72, 0.72), Matrix.Translation((0, -0.85, 0.55)), 14, 10), "white", 60)
    for sx in (1, -1):
        p.add(ellipsoid((0.22, 0.1, 0.14), Matrix.Translation((sx * 0.55, -1.15, 0.32)) @ frame_from_normal((sx * 0.7, -0.7, 0)), 8, 5), "pink")
    p.add(tube([Vector((0, -1.25, 0.55)), Vector((0, -1.85, 0.52)), Vector((0, -2.45, 0.38))], lambda u: 0.3 * (1 - u) + 0.04, 8, 3), "beak", 50)
    p.add(tube([Vector((0, -1.25, 0.33)), Vector((0, -1.8, 0.16)), Vector((0, -2.1, 0.08))], lambda u: 0.2 * (1 - u) + 0.04, 8, 3), "orange", 50)
    p.add(ellipsoid((0.16, 0.08, 0.08), Matrix.Translation((0, -1.7, 0.36)), 6, 4), "dred")
    for dx, dz in ((-0.12, 0.3), (0.05, 0.42), (0.2, 0.28)):
        b = Vector((dx * 0.5, -0.9, 1.22))
        p.add(tube([b, b + Vector((dx, 0.1, dz * 0.6)), b + Vector((dx * 1.6, 0.35, dz))], lambda u: 0.08 * (1 - u) + 0.02, 5, 2), "lgrey")
    for sx in (1, -1):
        p.add(prism(pill(0, 0, 0.9, 0.2, 0, 3), 0.1, M((sx * 0.3, 1.55, 0.1), (0, 0, 90 - sx * 18))), lambda c, n: "ink" if c.y > 1.85 else "mgrey")
    p.add(prism(pill(0, 0, 1.0, 0.22, 0, 3), 0.1, M((0, 1.65, 0.12), (0, 0, 90))), lambda c, n: "ink" if c.y > 2.0 else "mgrey")
    for sx in (1, -1):
        a = Vector((sx * 0.35, 0.35, -0.75))
        b = Vector((sx * 0.42, 0.8, -1.05))
        p.add(palo(a, b, 0.07, 5), "beak")
        p.add(prism([(-0.28, 0.0), (0.28, 0.0), (0.0, -0.55)], 0.06, Matrix.Translation(b) @ Euler((math.radians(-20), 0, math.radians(180))).to_matrix().to_4x4()), "beak")


ALA_PTS = [(0.0, -0.45), (0.9, -0.62), (1.9, -0.6), (2.8, -0.38), (3.35, 0.0), (3.05, 0.35), (2.65, 0.2), (2.4, 0.55), (1.95, 0.38), (1.65, 0.72), (1.15, 0.56), (0.65, 0.82), (0.0, 0.62)]
HOMBRO_ALA = (0.78, 0.0, 0.38)


def ala(p, m):
    p.add(prism(ALA_PTS, 0.16, m, bev=0.04), lambda c, n: "ink" if abs(c.x) > 2.35 else ("white" if c.y < -0.4 else "mgrey"), 45)


def p_pajaro():
    p = Prop("Pajaro", 2600)
    cuerpo_pajaro(p, "normal")
    for sx, pup in ((1, (0.0, -0.45)), (-1, (0.5, 0.45))):
        c = Vector((sx * 0.3, -1.28, 0.95))
        n = Vector((sx * 0.45, -0.75, 0.55))
        ojo(p, c, n, 0.32, pup, seg=12)
        ceja(p, [c + Vector((sx * 0.38, -0.05, 0.25)), c + Vector((sx * 0.08, -0.2, 0.42)), c + Vector((-sx * 0.12, -0.25, 0.5))], 0.06)
    return p, {"hombro": HOMBRO_ALA}


def p_ala(nombre, sx):
    p = Prop(nombre, 300)
    ala(p, Matrix.Diagonal((sx, 1, 1, 1)))
    return p, {}


def espiral(p, c, n, r):
    n, t, b = base_normal(n)
    q = []
    for k in range(22):
        a = k / 21 * 4 * math.pi
        rr = 0.08 + 0.72 * k / 21
        d = (n + (t * math.cos(a) + b * math.sin(a)) * rr * 1.1).normalized()
        q.append(c + d * (r * 1.02))
    p.add(tube(q, lambda u: 0.035, 5, 2, caps=False), "ink")


def p_mareado():
    p = Prop("PajaroMareado", 3400)
    cuerpo_pajaro(p, "mareado")
    for sx in (1, -1):
        c = Vector((sx * 0.3, -1.28, 0.95))
        n = Vector((sx * 0.45, -0.75, 0.55))
        centro, r = ojo(p, c, n, 0.32, None, seg=12)
        espiral(p, centro, n, r)
    p.add(tube([Vector((0.05, -1.75, 0.22)), Vector((0.35, -1.95, 0.05)), Vector((0.5, -2.0, -0.3)), Vector((0.42, -1.95, -0.55))], lambda u: 0.11, 6, 3), "pink", 60)
    p.add(ellipsoid((0.28, 0.28, 0.3), Matrix.Translation((0.15, -0.75, 1.25)), 10, 6), "pink", 60)
    for sx in (1, -1):
        m = Matrix.Translation((sx * HOMBRO_ALA[0], HOMBRO_ALA[1], HOMBRO_ALA[2])) @ Euler((0, math.radians(sx * 55), 0)).to_matrix().to_4x4() @ Matrix.Diagonal((sx, 1, 1, 1))
        ala(p, m)
    for k, q in enumerate(((0.5, 0.6, 0.8), (-0.6, 0.3, 0.75))):
        p.add(prism(pill(0, 0, 0.7, 0.13, 0, 3), 0.06, M(q, (0, 30 - 60 * k, 70))), "lgrey")
    return p, {}


def p_plaf():
    p = Prop("PajaroPlaf", 3400)
    plano = frame((0, 0, 0), (1, 0, 0), (0, 0, 1))
    p.add(ellipsoid((1.25, 0.4, 1.45), Matrix.Translation((0, -0.4, -0.25)), 16, 10), lambda c, n: "white" if n.y > 0.2 or c.z < 0.3 else "lgrey", 60)
    p.add(ellipsoid((0.95, 0.38, 0.8), Matrix.Translation((0, -0.35, 1.25)), 14, 10), "white", 60)
    for sx in (1, -1):
        m = Matrix.Translation((sx * 1.0, -0.42, 0.1)) @ frame((0, 0, 0), (sx, 0, 0), (0, 0, 1)) @ Euler((0, 0, math.radians(18))).to_matrix().to_4x4()
        p.add(prism(ALA_PTS, 0.14, m, bev=0.04), lambda c, n: "ink" if abs(c.x) > 3.2 else "lgrey", 45)
        p.add(palo((sx * 0.45, -0.3, -1.45), (sx * 0.7, -0.3, -2.0), 0.08, 5), "beak")
        p.add(prism([(-0.4, 0.0), (0.4, 0.0), (0.0, -0.6)], 0.07, Matrix.Translation((sx * 0.75, -0.25, -1.95)) @ plano @ Euler((0, 0, math.radians(sx * 20))).to_matrix().to_4x4()), "beak")
        c = Vector((sx * 0.36, -0.02, 1.4))
        p.add(ellipsoid((0.32, 0.08, 0.32), Matrix.Translation(c), 12, 6), "white", 70)
        aro(p, Matrix.Translation(c + Vector((0, 0.02, 0))) @ plano, 0.32, 0.05, "ink", 12)
        for ang in (45, -45):
            p.add(prism(pill(0, 0, 0.42, 0.055, math.radians(ang), 2), 0.05, Matrix.Translation(c + Vector((0, 0.08, 0))) @ plano), "ink")
    p.add(tube([Vector((0.2, -0.15, 1.05)), Vector((0.9, -0.1, 1.05)), Vector((1.45, -0.08, 0.8))], lambda u: 0.26 * (1 - u) + 0.05, 8, 3), "beak", 50)
    p.add(tube([Vector((0.25, -0.05, 0.85)), Vector((0.35, -0.03, 0.5)), Vector((0.3, -0.03, 0.15))], lambda u: 0.12, 6, 3), "pink", 60)
    p.add(prism(pill(0, 0, 1.0, 0.25, 0, 3), 0.1, Matrix.Translation((0, -0.4, -1.9)) @ plano @ Euler((0, 0, math.radians(90))).to_matrix().to_4x4()), lambda c, n: "ink" if c.z < -2.2 else "mgrey")
    for x, z, a in ((-1.3, 1.7, 30), (1.5, 1.9, -40), (0.2, 2.25, 80)):
        p.add(prism(pill(0, 0, 0.6, 0.12, 0, 3), 0.05, Matrix.Translation((x, -0.3, z)) @ plano @ Euler((0, 0, math.radians(a))).to_matrix().to_4x4()), "lgrey")
    return p, {}


def rejilla(f, us, vs, fuera=None):
    bm = bmesh.new()
    G = [[bm.verts.new(f(u, v)) for v in vs] for u in us]
    for i in range(len(us) - 1):
        for j in range(len(vs) - 1):
            bm.faces.new((G[i][j], G[i + 1][j], G[i + 1][j + 1], G[i][j + 1]))
    bm.normal_update()
    if fuera is not None:
        total = sum((fc.normal.dot(fuera(fc.calc_center_median())) for fc in bm.faces), 0.0)
        if total < 0:
            bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    return bm


def lin_esp(a, b, n):
    return [a + (b - a) * k / (n - 1) for k in range(n)]


def hw_barca(y):
    if y < 0.6:
        return 2.1 * math.sqrt(max(0.0, 1 - ((y - 0.6) / 5.2) ** 2))
    return 2.1 - 0.5 * ((y - 0.6) / 3.6) ** 2


def zt_barca(y):
    return 1.1 + 0.9 * max(0.0, (-y - 1) / 3.6) ** 2


def zb_barca(y):
    return -1.3 + 0.7 * max(0.0, (-y - 2) / 2.6) ** 2


def p_barca():
    p = Prop("PirataBarca", 9000)
    pts = {}
    Y0, Y1 = -4.45, 4.2

    def H(y, th, off=0.0):
        a = math.radians(th)
        zt, zb = zt_barca(y), zb_barca(y)
        return Vector(((hw_barca(y) + off) * math.sin(a), y, zb + (zt - zb) * (1 - math.cos(a)) - off * math.cos(a)))

    def fuera_h(c):
        return Vector((c.x, 0, c.z - 0.4))

    def rol_casco(c, n):
        if n.y > 0.9:
            return "dteal"
        zb = zb_barca(c.y)
        zt = zt_barca(c.y)
        if c.z < zb + 0.55:
            return "red"
        if c.z > zt - 0.42:
            return "cream"
        return "teal" if int((c.z - zb) / 0.38) % 2 == 0 else "dteal"

    p.add(rejilla(lambda y, th: H(y, th), lin_esp(Y0, Y1, 20), lin_esp(-90, 90, 15), fuera_h), rol_casco, 35)
    popa = bmesh.new()
    popa.faces.new([popa.verts.new(H(Y1, th)) for th in lin_esp(-90, 90, 15)])
    popa.normal_update()
    if list(popa.faces)[0].normal.y < 0:
        bmesh.ops.reverse_faces(popa, faces=list(popa.faces))
    p.add(popa, "dteal", 30)

    def piso(y, s, baja):
        zt, zb = zt_barca(y), zb_barca(y)
        zf = zt - baja
        c = min(1.0, max(-1.0, 1 - (zf - zb) / (zt - zb)))
        return Vector((s * hw_barca(y) * math.sin(math.acos(c)), y, zf))

    p.add(rejilla(lambda y, s: piso(y, s, 0.05), lin_esp(Y0, -2.4, 8), lin_esp(-1, 1, 5), lambda c: Vector((0, 0, 1))),
          lambda c, n: "wood" if int((c.x + 3) / 0.5) % 2 == 0 else "wood2", 30)
    p.add(rejilla(lambda y, s: piso(y, s, 0.5), lin_esp(-2.4, Y1, 12), lin_esp(-1, 1, 5), lambda c: Vector((0, 0, 1))), "dwood", 30)
    p.add(rejilla(lambda z, s: Vector((piso(-2.4, s, 0.05).x * (0.97 if z > 0.5 else 1.0), -2.4, zt_barca(-2.4) - 0.05 - 0.45 * z)), [0.0, 1.0], lin_esp(-1, 1, 5), lambda c: Vector((0, 1, 0))), "wood2", 30)
    borde = [H(y, -90, 0.05) + Vector((0, 0, 0.05)) for y in lin_esp(Y0 + 0.05, Y1, 12)] + [H(y, 90, 0.05) + Vector((0, 0, 0.05)) for y in lin_esp(Y1, Y0 + 0.05, 12)]
    p.add(tube(borde, lambda u: 0.16, 6, 2, closed=True), "dwood", 40)
    for y in (-0.6, 2.4):
        p.add(bb(-hw_barca(y) * 0.95, hw_barca(y) * 0.95, y - 0.35, y + 0.35, zt_barca(y) - 0.5, zt_barca(y) - 0.3), "wood")
    pts["asiento"] = (0, 1.0, -0.65)
    p.add(cyl(0.85, 1.1, (0, -4.25, 0.95), (90, 0, 0), 12), "iron", 40)
    aro(p, M((0, -5.33, 0.95), (90, 0, 0)), 0.85, 0.1, "metal", 12)
    p.add(cyl(0.38, 0.3, (0, -5.35, 0.95), (90, 0, 0), 10), "grey")
    pts["helices"] = [((0, -5.7, 0.95), 0.9)]
    p.add(tube([Vector((0.35, -4.8, 1.6)), Vector((0.45, -4.65, 2.2)), Vector((0.7, -4.4, 2.75))], lambda u: 0.18, 8, 2), "iron")
    aro(p, M((0.7, -4.4, 2.8)), 0.19, 0.05, "rust", 8)
    pts["humo"] = (0.7, -4.4, 2.9)
    for lado in (1, -1):
        e = piso(-3.15, 0.42 * lado, 0.05) + Vector((0, 0, 0.05))
        n = Vector((0.25 * lado, -0.6, 1.0))
        c, r = ojo(p, e, n, 0.8, None)
        if lado == -1:
            parche(p, e, n, 0.8, [e + Vector((-0.75, 0.15, 0.3)), e + Vector((-1.05, 0.35, -0.2)), H(-2.9, -80, 0.08), H(-2.6, -55, 0.08)])
            ceja(p, [c + Vector((-0.65, -0.25, 0.8)), c + Vector((0.0, -0.45, 1.05)), c + Vector((0.65, -0.3, 0.9))], 0.15)
        else:
            pts.setdefault("ojos", []).append((tuple(c), r))
            ceja(p, [c + Vector((-0.7, -0.3, 0.72)), c + Vector((0.0, -0.45, 0.98)), c + Vector((0.7, -0.25, 1.18))], 0.15)
    for lado in (1, -1):
        def fh(off, lado=lado):
            return lambda u, v: H(u, v * lado, off)
        poly = suave([(-4.25, 52), (-3.6, 58), (-2.9, 60), (-2.2, 54), (-1.9, 46), (-2.15, 56), (-2.8, 40), (-3.6, 30), (-4.25, 28)], 2)
        boca_envuelta(p, fh, fuera_h, poly, dientes_en(-4.15, -2.45, lambda u: 58 - 4 * max(0.0, u + 2.9) / 0.5, -9, 4, hueco=2), oro=1,
                      lengua=suave(circ(-3.5, 34, 0.32, 8), 1) if lado == 1 else None)
    for y0, y1 in ((-0.95, -0.25), (0.0, 0.7), (0.95, 1.65)):
        p.add(bb(1.7, 10.2, y0, y1, -0.05, 0.2, 0.04, 1), lambda c, n: "straw" if n.z > 0.5 else "tan", 40)
    for x in (3.0, 6.5, 9.8):
        p.add(bb(x - 0.3, x + 0.3, -0.95, 1.65, -0.42, -0.05), "wood2", 40)
    for x, y in ((4.0, -0.6), (8.0, 0.35), (5.2, 1.3)):
        p.add(ellipsoid((0.06, 0.06, 0.04), Matrix.Translation((x, y, 0.21)), 5, 3), "ink")
    p.add(prism(rect(-9.9, -1.7, -0.9, 1.5), 0.3, M((0, 0.1, 0.05), (0, 7, 0)), bev=0.05),
          lambda c, n: "cream" if abs(n.z) < 0.5 else ("red" if int((c.x + c.y + 20) / 1.1) % 2 == 0 else "cream"), 40)
    for x in (-3.8, -7.8):
        p.add(palo((x, 0.3, -0.15), (x - 0.6, 0.3, -1.2), 0.08, 5), "iron")
    p.add(prism([(-3.0, 0.0), (3.0, 0.0), (2.6, 1.15), (-2.6, 1.15)], 0.24, M((0, 3.95, 0.95), (0, -3, 0))), lambda c, n: "cream" if abs(n.z) > 0.5 else "wood2", 40)
    bandera(p, (0, 3.2, 0.7), (0, 3.45, 6.6), 3.5, 3.0)
    centro = H(1.9, 62, 0.22)
    nr = Vector((1.0, 0.0, 0.35)).normalized()
    m = Matrix.Translation(centro) @ frame_from_normal(nr)
    aro(p, m, 0.62, 0.2, lambda c, n: "orange" if int((math.atan2(c.y - centro.y, c.z - centro.z) + math.pi) / (math.pi / 2)) % 2 == 0 else "cream", 14, 6)
    pts["canones"] = []
    for sx in (1, -1):
        b = (sx * 1.95, -2.4, 0.35)
        trabuco(p, b, 1.9, 0.19)
        pts["canones"].append(b)
    return p, pts


BUILDERS = [p_barril, p_banera, p_barca, p_helice, p_piloto, p_brazo, p_pajaro, lambda: p_ala("AlaPajaroIzq", 1), lambda: p_ala("AlaPajaroDer", -1), p_mareado, p_plaf]
AVIONES = ["PirataBarril", "PirataBanera", "PirataBarca"]


LUAU_PIE = '''
function Criaturas.clonar(nombre: string, escala: number?): (Model?, { BasePart }, { CFrame })
	local partes: { BasePart } = {}
	local marcos: { CFrame } = {}
	local carpeta = ReplicatedStorage:FindFirstChild(Criaturas.CARPETA)
	local plantilla = carpeta and carpeta:FindFirstChild(nombre)
	if not plantilla or not plantilla:IsA("Model") then
		return nil, partes, marcos
	end
	local e = escala or 1
	local modelo = plantilla:Clone()
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true
			d.CastShadow = false
			d.Size *= e
			table.insert(partes, d)
			table.insert(marcos, CFrame.new(d.Position * e) * d.CFrame.Rotation)
		end
	end
	return modelo, partes, marcos
end

return Criaturas
'''


def v3(v):
    return "Vector3.new(%s)" % ", ".join(("%.3f" % x).rstrip("0").rstrip(".").replace("-0", "0") if abs(x) < 5e-4 else ("%.3f" % x).rstrip("0").rstrip(".") for x in v)


def puntos_roblox(puntos):
    out = {}
    for nombre in AVIONES:
        q = puntos[nombre]
        out[nombre] = {
            "helices": [[rb(pos), esc] for pos, esc in q["helices"]],
            "asiento": rb(q["asiento"]),
            "ojos": [[rb(c), round(r, 3)] for c, r in q["ojos"]],
            "humo": rb(q["humo"]),
            "canones": [rb(c) for c in q["canones"]],
        }
    out["hombro"] = rb(puntos["BrazoPirata"]["hombro"], 1.5)
    out["ala"] = rb(puntos["Pajaro"]["hombro"])
    return out


def escribir_luau(manifest):
    ruta_ids = os.path.join(OUT, "ids_subida.json")
    ids = json.load(open(ruta_ids, encoding="utf-8")) if os.path.exists(ruta_ids) else {}
    pz = manifest["piezas"]
    q = manifest["puntos"]
    L = ["--!strict", 'local ReplicatedStorage = game:GetService("ReplicatedStorage")', "",
         "export type Caja = { minimo: Vector3, maximo: Vector3 }",
         "export type Avion = {", "\thelices: { { pos: Vector3, escala: number } },", "\tasiento: Vector3,", "\tojos: { { centro: Vector3, radio: number } },", "\thumo: Vector3,", "\tcanones: { Vector3 },", "}", "",
         "local Criaturas = {}", "", 'Criaturas.CARPETA = "ModelosCriaturas"', "", "Criaturas.IDS = {"]
    for e in pz:
        if e["nombre"] in ids:
            L.append(f"\t{e['nombre']} = {ids[e['nombre']]},")
    L += ["} :: { [string]: number }", "", "Criaturas.CAJAS = {"]
    for e in pz:
        L.append(f"\t{e['nombre']} = {{ minimo = {v3(e['bbox_min'])}, maximo = {v3(e['bbox_max'])} }},")
    L += ["} :: { [string]: Caja }", "", "Criaturas.AVIONES = {"]
    for nombre in AVIONES:
        a = q[nombre]
        L.append(f"\t{nombre} = {{")
        L.append("\t\thelices = { " + ", ".join(f"{{ pos = {v3(pos)}, escala = {esc} }}" for pos, esc in a["helices"]) + " },")
        L.append(f"\t\tasiento = {v3(a['asiento'])},")
        L.append("\t\tojos = { " + ", ".join(f"{{ centro = {v3(c)}, radio = {r} }}" for c, r in a["ojos"]) + " },")
        L.append(f"\t\thumo = {v3(a['humo'])},")
        L.append("\t\tcanones = { " + ", ".join(v3(c) for c in a["canones"]) + " },")
        L.append("\t},")
    L += ["} :: { [string]: Avion }", "", "Criaturas.VARIANTES = { " + ", ".join(f'"{n}"' for n in AVIONES) + " }",
          f"Criaturas.HOMBRO = {v3(q['hombro'])}", f"Criaturas.ALA = {v3(q['ala'])}"]
    with open(os.path.join(RAIZ, "src", "shared", "Criaturas.luau"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n" + LUAU_PIE)
    print("LUAU", len(ids), "ids")


def instancia(st, nombre, m):
    o = bpy.data.objects.new(nombre + "_i", st.objs[nombre].data)
    o.matrix_world = m
    return st.link(o)


def bolita(st, c, r, hx="1B1B21"):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r)
    me = bpy.data.meshes.new("pup")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat_rgb(hx, 0.4))
    me.shade_smooth()
    o = bpy.data.objects.new("pup", me)
    o.location = c
    return st.link(o)


def montar_pirata(st, nombre, m, pts, giro=20.0, mira=None):
    instancia(st, nombre, m)
    for pos, esc in pts["helices"]:
        instancia(st, "HelicePirata", m @ Matrix.Translation(pos) @ Euler((0, math.radians(giro), 0)).to_matrix().to_4x4() @ Matrix.Diagonal((esc, esc, esc, 1)))
    a = m @ Matrix.Translation(pts["asiento"])
    instancia(st, "PilotoPirata", a)
    h = Vector(HOMBRO) * 1.5
    instancia(st, "BrazoPirata", a @ Matrix.Translation(h) @ Euler((0, math.radians(-15), 0)).to_matrix().to_4x4() @ Matrix.Translation(-h))
    for c, r in pts["ojos"]:
        cw = m @ Vector(c)
        d = (mira - cw).normalized() if mira is not None else (m.to_3x3() @ Vector((0.3, -1, 0.2))).normalized()
        bolita(st, cw + d * r * 0.86, r * 0.46)
    out = []
    for o in st.made:
        if o.type == "MESH":
            out += [o.matrix_world @ Vector(c) for c in o.bound_box]
    return out


def montar_pajaro(st, m, aleteo):
    instancia(st, "Pajaro", m)
    h = Vector(HOMBRO_ALA)
    instancia(st, "AlaPajaroIzq", m @ Matrix.Translation(h) @ Euler((0, math.radians(-aleteo), 0)).to_matrix().to_4x4())
    instancia(st, "AlaPajaroDer", m @ Matrix.Translation((-h.x, h.y, h.z)) @ Euler((0, math.radians(aleteo), 0)).to_matrix().to_4x4())


def esquinas(st):
    out = []
    bpy.context.view_layer.update()
    for o in st.made:
        if o.type == "MESH":
            out += [o.matrix_world @ Vector(c) for c in o.bound_box]
    return out


def hoja_cerca(st, puntos):
    for i, nombre in enumerate(AVIONES):
        montar_pirata(st, nombre, Matrix.Translation((i * 26.0 - 13.0 * (len(AVIONES) - 1), 0, 0)) @ Euler((0, 0, math.radians(-28))).to_matrix().to_4x4(), puntos[nombre])
    fit_camera(st, esquinas(st), math.radians(18), math.radians(-38), 50)


def hoja_lado(st, puntos):
    for i, nombre in enumerate(AVIONES):
        montar_pirata(st, nombre, Matrix.Translation((i * 28.0, 0, 0)) @ Euler((0, math.radians(-12), math.radians(-70))).to_matrix().to_4x4(), puntos[nombre], 70)
    fit_camera(st, esquinas(st), math.radians(22), math.radians(0), 60)


def hoja_cara(st, puntos):
    montar_pirata(st, AVIONES[0], Matrix.Translation((0, 0, 0)) @ Euler((0, 0, math.radians(-35))).to_matrix().to_4x4(), puntos[AVIONES[0]])
    a = Vector(puntos[AVIONES[0]]["asiento"])
    fit_camera(st, [Vector((0, -4, -1)), Vector((0, 2, 6.5)), Vector((3, -4, 2)), Vector((-3, -4, 2))], math.radians(10), math.radians(-30), 70)


def hoja_pajaros(st, puntos):
    montar_pajaro(st, Matrix.Translation((-9, 0, 0)) @ Euler((0, 0, math.radians(-30))).to_matrix().to_4x4(), 40)
    montar_pajaro(st, Matrix.Translation((-1, 0, 0)) @ Euler((0, 0, math.radians(20))).to_matrix().to_4x4(), -35)
    instancia(st, "PajaroMareado", Matrix.Translation((6, 0, 0)) @ Euler((math.radians(15), math.radians(-25), math.radians(-20))).to_matrix().to_4x4())
    instancia(st, "PajaroPlaf", Matrix.Translation((13, 2, 0)) @ Euler((0, 0, math.radians(180))).to_matrix().to_4x4())
    fit_camera(st, esquinas(st), math.radians(14), math.radians(-12), 50)


def hoja_lejos(st, puntos):
    scene = bpy.context.scene
    cam = st.camera((0, 0, 0), (0, -1, 0), 50)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle_y = math.radians(70)
    cam.data.clip_end = 5000
    vista = Vector((0, -1, 0))
    for nombre, d, x, z, giro in ((AVIONES[0], 95, -32, 6, 110), (AVIONES[-1], 140, 40, -10, -70)):
        montar_pirata(st, nombre, Matrix.Translation((x, -d, z)) @ Euler((math.radians(-25 if giro > 0 else 25), 0, math.radians(giro))).to_matrix().to_4x4(), puntos[nombre], 50, Vector((0, 0, 0)))
    for k, (x, y, z) in enumerate(((-6, -28, 3), (4, -36, -2), (9, -55, 6), (-14, -60, -5), (1, -80, 9))):
        montar_pajaro(st, Matrix.Translation((x, y, z)) @ Euler((math.radians(10), math.radians(15 * (-1) ** k), math.radians(180 + 10 * k))).to_matrix().to_4x4(), 35 if k % 2 else -30)


SHEETS = [("criaturas_cara.png", hoja_cara, (1200, 900)), ("criaturas_piratas.png", hoja_cerca, (1600, 900)), ("criaturas_piratas_lado.png", hoja_lado, (1600, 900)),
          ("criaturas_pajaros.png", hoja_pajaros, (1600, 900)), ("criaturas_lejos.png", hoja_lejos, (1280, 720))]


def render_sheets(objs, puntos, which, threads, outdir):
    scene = bpy.context.scene
    render_setup(scene, threads)
    for o in objs.values():
        o.hide_render = True
    for si, (fname, fn, res) in enumerate(SHEETS):
        if which and str(si + 1) not in which:
            continue
        scene.render.resolution_x, scene.render.resolution_y = res
        st = Stage(objs)
        fn(st, puntos)
        scene.render.filepath = os.path.join(outdir, fname)
        bpy.ops.render.render(write_still=True)
        print("RENDER", scene.render.filepath)
        st.clear()


def main():
    if arg("--solo-luau"):
        with open(os.path.join(OUT, "manifest.json"), encoding="utf-8") as fh:
            escribir_luau(json.load(fh))
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    mat = palette_material(palette_image())
    objs, puntos, piezas = {}, {}, []
    ok = True
    for b in BUILDERS:
        p, pts = b()
        ob, tris, mn, mx = make_object(p, mat)
        objs[p.name] = ob
        puntos[p.name] = pts
        ok = ok and tris <= p.budget
        print("PIECE %-14s tris %5d / %5d %s  min %.2f %.2f %.2f  max %.2f %.2f %.2f" % (p.name, tris, p.budget, "OK" if tris <= p.budget else "OVER", *mn, *mx))
        if not arg("--no-export"):
            export_fbx(ob)
        piezas.append({"nombre": p.name, "archivo": p.name + ".fbx", "triangulos": tris,
                       "bbox_min": [round(-mx.x, 3), round(mn.z, 3), round(mn.y, 3)], "bbox_max": [round(-mn.x, 3), round(mx.z, 3), round(mx.y, 3)]})
    manifest = {"piezas": piezas, "puntos": puntos_roblox(puntos)}
    if not arg("--no-export"):
        with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=1)
        escribir_luau(manifest)
    print("ALL BUDGETS OK" if ok else "SOME PIECES OVER BUDGET")
    if arg("--no-render"):
        return
    which = arg("--sheets")
    which = set(which.split(",")) if isinstance(which, str) else None
    outdir = arg("--render-dir")
    threads = arg("--threads")
    render_sheets(objs, puntos, which, int(threads) if isinstance(threads, str) else 8, outdir if isinstance(outdir, str) else OUT)


main()
