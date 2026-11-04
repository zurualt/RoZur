import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if len(sys.argv) > 1 and os.path.isdir(sys.argv[-1]):
    OUT = sys.argv[-1]

ZCB, ZCT, RB, RT, DEPTH = 2.05, 3.55, 0.88, 0.80, 0.86

PALETTE = {
    "body": (0, (1.0, 1.0, 1.0, 0.0)),
    "black": (1, "1B1B21"),
    "vest": (2, "F27B2B"),
    "teal": (3, "1FA6A0"),
    "dark": (4, "34383F"),
    "gold": (5, "F0B73A"),
    "cream": (6, "FFF4E0"),
    "shoe": (7, "4A3428"),
    "sole": (8, "EDE3CF"),
    "white": (9, "F7F7F2"),
    "mouth": (10, "2B1219"),
}

PLAYER_COLORS = {
    "Lima": "8BD24C",
    "Lavanda": "A07CF2",
    "Chicle": "F27BB5",
    "Sol": "F5CD3D",
}

PARTS = [
    "Head", "UpperTorso", "LowerTorso",
    "LeftUpperArm", "LeftLowerArm", "LeftHand",
    "RightUpperArm", "RightLowerArm", "RightHand",
    "LeftUpperLeg", "LeftLowerLeg", "LeftFoot",
    "RightUpperLeg", "RightLowerLeg", "RightFoot",
]


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def swatch_uv(role):
    i = PALETTE[role][0]
    return ((i % 4 + 0.5) / 4.0, (i // 4 + 0.5) / 4.0)


def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def r_at(z):
    if z < ZCB:
        return RB * math.sqrt(max(0.0, 1.0 - (ZCB - z) ** 2))
    if z > ZCT:
        return RT * math.sqrt(max(0.0, 1.0 - (z - ZCT) ** 2))
    return RB + (RT - RB) * (z - ZCB) / (ZCT - ZCB)


VEST_TOP, VEST_BOT = 3.30, 2.0


def vest_phi(z):
    return max(0.035, 0.5 * (z - 2.6) / (VEST_TOP - 2.6)) if z > 2.6 else 0.035


def under_vest(c):
    if not (VEST_BOT + 0.12 < c.z < VEST_TOP - 0.08):
        return False
    th = math.atan2(c.y / DEPTH, c.x)
    d = abs((th + math.pi / 2 + math.pi) % (2 * math.pi) - math.pi)
    return d > vest_phi(c.z) + 0.3


def frame_from_normal(n):
    n = n.normalized()
    x = Vector((0, 0, 1)).cross(n)
    if x.length < 1e-4:
        x = Vector((1, 0, 0))
    x.normalize()
    y = n.cross(x).normalized()
    m = Matrix((x, y, n)).transposed()
    return m.to_4x4()


def core_weights(z):
    t1 = ss(2.25, 2.65, z)
    t2 = ss(3.30, 3.70, z)
    w = {"LowerTorso": 1.0 - t1, "UpperTorso": t1 * (1.0 - t2), "Head": t2}
    return {k: v for k, v in w.items() if v > 1e-4}


def core_part(c):
    if c.z < 2.45:
        return "LowerTorso"
    if c.z < 3.5:
        return "UpperTorso"
    return "Head"


class Prim:
    def __init__(self, bm, role, part, weights, s_layer=False, angle=50.0):
        self.bm = bm
        self.role = role
        self.part = part
        self.weights = weights
        self.s_layer = s_layer
        self.angle = angle


PRIMS = []


def add(bm, role, part, weights, s_layer=False, angle=50.0):
    PRIMS.append(Prim(bm, role, part, weights, s_layer, angle))


def ellipsoid(radii, mat=Matrix(), u=20, v=14):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.transform(bm, matrix=mat @ Matrix.Diagonal((*radii, 1.0)), verts=bm.verts)
    return bm


def cylinder(radius, depth, mat=Matrix(), seg=20):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=radius, radius2=radius, depth=depth)
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
    sl = bm.verts.layers.float.new("s")
    rings = []
    for i in range(n):
        u = seglen[i] / total if total > 0 else 0.0
        r = radius_fn(u)
        b = tangents[i].cross(normals[i]).normalized()
        ring = []
        for j in range(k):
            a = 2 * math.pi * j / k
            v = bm.verts.new(path[i] + (normals[i] * math.cos(a) + b * math.sin(a)) * r)
            v[sl] = seglen[i]
            ring.append(v)
        rings.append(ring)
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
                    pole[sl] = seglen[end]
                    for j in range(k):
                        bm.faces.new((prev[j], prev[(j + 1) % k], pole))
                    break
                rr = r_end * math.cos(phi)
                ring = []
                for j in range(k):
                    a = 2 * math.pi * j / k
                    v = bm.verts.new(center + (normals[end] * math.cos(a) + b * math.sin(a)) * rr)
                    v[sl] = seglen[end]
                    ring.append(v)
                for j in range(k):
                    bm.faces.new((prev[j], prev[(j + 1) % k], ring[(j + 1) % k], ring[j]))
                prev = ring
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ctrl_s = []
    for p in ctrl:
        best = min(range(n), key=lambda i: (path[i] - p).length)
        ctrl_s.append(seglen[best])
    return bm, ctrl_s


def build_body():
    m = 28
    prof = []
    nb, nm, nt = 8, 7, 11
    for i in range(nb):
        a = math.radians(-90 + 90 * i / nb)
        prof.append((ZCB + math.sin(a), RB * math.cos(a)))
    for i in range(nm):
        prof.append((ZCB + (ZCT - ZCB) * i / nm, RB + (RT - RB) * i / nm))
    for i in range(nt + 1):
        a = math.radians(90 * i / nt)
        prof.append((ZCT + math.sin(a), RT * math.cos(a)))
    bm = bmesh.new()
    rings = []
    for z, r in prof:
        if r < 1e-5:
            rings.append([bm.verts.new((0, 0, z))])
            continue
        ring = []
        for j in range(m):
            th = -math.pi / 2 + 2 * math.pi * j / m
            ring.append(bm.verts.new((r * math.cos(th), DEPTH * r * math.sin(th), z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        if len(a) == 1:
            for j in range(m):
                bm.faces.new((a[0], b[(j + 1) % m], b[j]))
        elif len(b) == 1:
            for j in range(m):
                bm.faces.new((a[j], a[(j + 1) % m], b[0]))
        else:
            for j in range(m):
                bm.faces.new((a[j], a[(j + 1) % m], b[(j + 1) % m], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def cull_under_vest(bm):
    dead = [f for f in bm.faces if under_vest(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=dead, context="FACES_ONLY")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    return bm


def build_vest():
    rows, cols = 5, 20
    z_top = VEST_TOP
    off = 0.045
    phi = vest_phi

    def z_bot(th):
        f = max(0.0, math.cos(th + math.pi / 2))
        return VEST_BOT - 0.14 * f ** 6

    bm = bmesh.new()
    grid = []
    for ri in range(rows + 1):
        v = ri / rows
        zn = VEST_BOT + (z_top - VEST_BOT) * v
        p = phi(zn)
        row = []
        for ci in range(cols + 1):
            th = (-math.pi / 2 + p) + (2 * math.pi - 2 * p) * ci / cols
            z = z_bot(th) + (z_top - z_bot(th)) * v
            r = r_at(z) + off
            row.append(bm.verts.new((r * math.cos(th), DEPTH * r * math.sin(th), z)))
        grid.append(row)
    for ri in range(rows):
        for ci in range(cols):
            f = bm.faces.new((grid[ri][ci], grid[ri][ci + 1], grid[ri + 1][ci + 1], grid[ri + 1][ci]))
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, c.y, 0))) < 0:
            f.normal_flip()
    bm.normal_update()
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.03)
    bm.normal_update()
    return bm


def build_mouth(hit):
    cols, rows, w = 11, 4, 0.15
    bm = bmesh.new()
    ls = bm.verts.layers.float.new("ws")
    li = bm.verts.layers.float.new("wi")
    grid = []
    for ri in range(rows + 1):
        v = ri / rows
        row = []
        for ci in range(cols + 1):
            u = -1.0 + 2.0 * ci / cols
            zt = 3.70 + 0.035 * u * u
            t = 0.012 + 0.03 * math.sqrt(max(0.0, 1.0 - u * u))
            loc, n = hit(u * w, zt - v * t)
            vert = bm.verts.new(loc + n * 0.012)
            c = max(0.0, 1.0 - u * u) ** 0.6
            vert[ls] = (1.0 - v) * c
            vert[li] = v * c
            row.append(vert)
        grid.append(row)
    for ri in range(rows):
        for ci in range(cols):
            bm.faces.new((grid[ri][ci], grid[ri][ci + 1], grid[ri + 1][ci + 1], grid[ri + 1][ci]))
    bm.normal_update()
    if sum(f.normal.y for f in bm.faces) > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.normal_update()
    return bm


def chain_weights(bones, bounds, blend):
    def fn(s):
        w = {bones[0]: 1.0}
        for i, b in enumerate(bounds):
            t = ss(b - blend, b + blend, s)
            carry = w[bones[i]]
            w[bones[i]] = carry * (1.0 - t)
            w[bones[i + 1]] = carry * t
        return {k: v for k, v in w.items() if v > 1e-4}
    return fn


def build_character():
    PRIMS.clear()
    body = build_body()
    tree = BVHTree.FromBMesh(body)

    def hit(x, z):
        loc, nrm, _, _ = tree.ray_cast(Vector((x, -5.0, z)), Vector((0, 1, 0)))
        return loc, nrm

    add(cull_under_vest(body), "body", core_part, "core")
    add(build_vest(), "vest", core_part, "core", angle=60.0)

    zs = 3.36
    rs = r_at(zs) + 0.06
    ring_pts = [Vector((rs * math.cos(-math.pi / 2 + 2 * math.pi * j / 20), DEPTH * rs * math.sin(-math.pi / 2 + 2 * math.pi * j / 20), zs)) for j in range(20)]
    scarf, _ = tube(ring_pts, lambda u: 0.045, k=6, steps=1, closed=True, up=Vector((0, 0, 1)))
    add(scarf, "teal", "UpperTorso", "core")
    fy = -DEPTH * rs
    add(ellipsoid((0.12, 0.07, 0.1), Matrix.Translation((0, fy - 0.035, 3.33)), 10, 7), "teal", "UpperTorso", "core")
    for sx in (-1, 1):
        mat = Matrix.Translation((sx * 0.08, fy - 0.02, 3.15)) @ Matrix.Rotation(math.radians(-sx * 22), 4, "Y")
        add(ellipsoid((0.065, 0.022, 0.15), mat, 8, 5), "teal", "UpperTorso", "core")

    for sx in (-1, 1):
        loc, n = hit(sx * 0.24, 3.99)
        ctr = loc - n * 0.05
        add(ellipsoid((0.13, 0.13, 0.13), Matrix.Translation(ctr), 14, 10), "white", "Head", {"Head": 1.0})
        fr = Matrix.Translation(ctr + n * 0.112) @ frame_from_normal(n)
        add(ellipsoid((0.064, 0.07, 0.036), fr, 12, 8), "black", "Head", {"Head": 1.0})
        add(ellipsoid((0.019, 0.019, 0.012), fr @ Matrix.Translation((0.022, 0.028, 0.03)), 6, 4), "white", "Head", {"Head": 1.0})
        pts = []
        for x, z in ((0.12, 4.215), (0.24, 4.255), (0.36, 4.22)):
            l2, n2 = hit(sx * x, z)
            pts.append(l2 + n2 * 0.004)
        brow, _ = tube(pts, lambda u: 0.03 * (0.55 + 0.45 * math.sin(math.pi * u)), k=6, steps=3, cap_rings=2)
        add(brow, "black", "Head", {"Head": 1.0})

    add(build_mouth(hit), "mouth", "Head", "mouth", angle=80.0)

    band_pts = []
    a0 = math.asin(3.93 - ZCT)
    for i in range(13):
        a = a0 + (math.pi - 2 * a0) * i / 12
        ca, sa = math.cos(a), math.sin(a)
        nx, nz = ca / RT, sa
        nl = math.hypot(nx, nz)
        band_pts.append(Vector((RT * ca + 0.07 * nx / nl, 0.05, ZCT + sa + 0.07 * nz / nl)))
    band, _ = tube(band_pts, lambda u: 0.05, k=8, steps=2, up=Vector((0, 1, 0)))
    add(band, "dark", "Head", {"Head": 1.0})
    cr = r_at(3.93)
    for sx in (-1, 1):
        rot = Matrix.Rotation(math.radians(90), 4, "Y")
        add(cylinder(0.2, 0.15, Matrix.Translation((sx * (cr + 0.06), 0.05, 3.93)) @ rot, 16), "dark", "Head", {"Head": 1.0}, angle=40.0)
        add(cylinder(0.14, 0.05, Matrix.Translation((sx * (cr + 0.15), 0.05, 3.93)) @ rot, 16), "teal", "Head", {"Head": 1.0}, angle=40.0)

    mic_raw = [(-0.86, -0.06, 3.87), (-0.80, -0.38, 3.74), (-0.58, -0.62, 3.64), (-0.31, -0.72, 3.62)]
    mic_pts = []
    for x, y, z in mic_raw:
        th = math.atan2(y / DEPTH, x)
        r = r_at(z) + 0.075
        mic_pts.append(Vector((r * math.cos(th), DEPTH * r * math.sin(th), z)))
    mic, ms = tube(mic_pts, lambda u: 0.024, k=6, steps=4, cap_rings=2)
    add(mic, "dark", "Head", {"Head": 1.0})
    add(ellipsoid((0.065, 0.065, 0.065), Matrix.Translation(mic_pts[-1]), 10, 6), "black", "Head", {"Head": 1.0})

    loc, n = hit(0.40, 2.95)
    fr = Matrix.Translation(loc + n * 0.08) @ frame_from_normal(n)
    add(cylinder(0.062, 0.03, fr, 8), "gold", "UpperTorso", "core", angle=40.0)
    for sx in (-1, 1):
        wm = fr @ Matrix.Translation((sx * 0.105, 0.015, 0.0)) @ Matrix.Rotation(math.radians(sx * 14), 4, "Z")
        add(ellipsoid((0.1, 0.034, 0.016), wm, 6, 4), "gold", "UpperTorso", "core")
    for z in (2.42, 2.17):
        l2, n2 = hit(0.0, z)
        bm_ = ellipsoid((0.048, 0.048, 0.026), Matrix.Translation(l2 + n2 * 0.08) @ frame_from_normal(n2), 6, 4)
        add(bm_, "gold", core_part, "core")

    for side, sx in (("Left", 1), ("Right", -1)):
        ctrl = [Vector((sx * x, y, z)) for x, y, z in ((0.72, 0.0, 3.04), (0.84, 0.0, 3.0), (1.10, 0.0, 2.48), (1.24, 0.0, 1.98))]
        arm, cs = tube(ctrl, lambda u: 0.135 - 0.025 * u, k=10, steps=5, cap_rings=3)
        s_el, s_wr = cs[2], cs[3]
        wf = chain_weights([side + "UpperArm", side + "LowerArm", side + "Hand"], [s_el, s_wr - 0.04], 0.11)
        add(arm, "body", (lambda c, s, se=s_el, sd=side: sd + ("UpperArm" if s < se else "LowerArm")), wf, s_layer=True)
        hp = side + "Hand"
        add(ellipsoid((0.1, 0.17, 0.16), Matrix.Translation((sx * 1.275, 0.0, 1.83)), 12, 8), "body", hp, {hp: 1.0})
        for fy_ in (-0.095, 0.0, 0.095):
            fpts = [Vector((sx * 1.275, fy_, 1.77)), Vector((sx * 1.297, fy_, 1.67)), Vector((sx * 1.255, fy_, 1.585))]
            fbm, _ = tube(fpts, lambda u: 0.056 - 0.007 * u, k=6, steps=3, cap_rings=2)
            add(fbm, "body", hp, {hp: 1.0})
        tpts = [Vector((sx * 1.265, -0.10, 1.87)), Vector((sx * 1.243, -0.225, 1.78))]
        tbm, _ = tube(tpts, lambda u: 0.056, k=6, steps=2, cap_rings=2)
        add(tbm, "body", hp, {hp: 1.0})

        lctrl = [Vector((sx * x, y, z)) for x, y, z in ((0.39, 0.0, 1.45), (0.41, 0.0, 0.85), (0.42, 0.0, 0.24))]
        leg, lcs = tube(lctrl, lambda u: 0.215 - 0.035 * u, k=10, steps=6, cap_rings=3)
        s_kn, s_an = lcs[1], lcs[2]
        lw = chain_weights([side + "UpperLeg", side + "LowerLeg", side + "Foot"], [s_kn, s_an - 0.06], 0.15)
        add(leg, "body", (lambda c, s, sk=s_kn, sd=side: sd + ("UpperLeg" if s < sk else "LowerLeg")), lw, s_layer=True)
        fp = side + "Foot"
        shoe = ellipsoid((0.25, 0.37, 0.18), Matrix.Translation((sx * 0.42, -0.09, 0.155)), 14, 9)
        for v in shoe.verts:
            v.co.z = max(v.co.z, 0.03)
        add(shoe, "shoe", fp, {fp: 1.0})
        sole = ellipsoid((0.26, 0.38, 0.055), Matrix.Translation((sx * 0.42, -0.09, 0.045)), 14, 6)
        for v in sole.verts:
            v.co.z = max(v.co.z, 0.0)
        add(sole, "sole", fp, {fp: 1.0})


def assemble():
    acc = {p: {"v": [], "w": [], "f": [], "uv": [], "n": []} for p in PARTS}
    for pid, pr in enumerate(PRIMS):
        bm = pr.bm
        bm.verts.index_update()
        bm.normal_update()
        sl = bm.verts.layers.float.get("s") if pr.s_layer else None
        lws = bm.verts.layers.float.get("ws")
        lwi = bm.verts.layers.float.get("wi")
        cos_lim = math.cos(math.radians(pr.angle))
        uv = swatch_uv(pr.role)
        vmaps = {}
        for f in bm.faces:
            c = f.calc_center_median()
            if callable(pr.part):
                s = sum(v[sl] for v in f.verts) / len(f.verts) if sl else 0.0
                part = pr.part(c, s) if sl else pr.part(c)
            else:
                part = pr.part
            a = acc[part]
            vm = vmaps.setdefault(part, {})
            idx = []
            for lp in f.loops:
                v = lp.vert
                if v.index not in vm:
                    vm[v.index] = len(a["v"])
                    a["v"].append(v.co.copy())
                    if pr.weights == "core":
                        w = core_weights(v.co.z)
                    elif pr.weights == "mouth":
                        w = {"Head": max(0.0, 1.0 - v[lws] - v[lwi]), "BocaSup": v[lws], "BocaInf": v[lwi]}
                        w = {k: x for k, x in w.items() if x > 1e-4}
                    elif callable(pr.weights):
                        w = pr.weights(v[sl])
                    else:
                        w = dict(pr.weights)
                    tot = sum(w.values())
                    a["w"].append({k: x / tot for k, x in w.items()})
                idx.append(vm[v.index])
                nsum = Vector()
                for lf in v.link_faces:
                    if lf.normal.dot(f.normal) >= cos_lim:
                        nsum += lf.normal * lf.calc_area()
                a["n"].append(tuple(nsum.normalized() if nsum.length > 1e-9 else f.normal))
                a["uv"].append(uv)
            a["f"].append(tuple(idx))
    return acc


def make_palette_image():
    size = 64
    img = bpy.data.images.new("TripulantePalette", size, size, alpha=True)
    px = [0.0] * (size * size * 4)
    for role, (i, col) in PALETTE.items():
        rgba = col if isinstance(col, tuple) else (*hex_rgb(col), 1.0)
        gx, gy = i % 4, i // 4
        for y in range(gy * 16, gy * 16 + 16):
            for x in range(gx * 16, gx * 16 + 16):
                o = (y * size + x) * 4
                px[o:o + 4] = rgba
    img.pixels = px
    img.filepath_raw = os.path.join(OUT, "tripulante_palette.png")
    img.file_format = "PNG"
    img.save()
    return img


def palette_material(name, img, player_hex):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    rgb = nt.nodes.new("ShaderNodeRGB")
    rgb.name = "PlayerColor"
    rgb.label = "PlayerColor"
    rgb.outputs[0].default_value = (*lin(hex_rgb(player_hex)), 1.0)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    cin = [i for i in mix.inputs if i.type == "RGBA"]
    cout = [o for o in mix.outputs if o.type == "RGBA"][0]
    nt.links.new(tex.outputs["Alpha"], mix.inputs[0])
    nt.links.new(rgb.outputs[0], cin[0])
    nt.links.new(tex.outputs["Color"], cin[1])
    nt.links.new(cout, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.62
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return mat


def export_material(img):
    mat = bpy.data.materials.new("Tripulante_Export")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


BONES = [
    ("Root", None, (0, 0, 0), (0, 0, 0.4)),
    ("HumanoidRootNode", "Root", (0, 0, 2.05), (0, 0, 2.45)),
    ("LowerTorso", "HumanoidRootNode", (0, 0, 2.05), (0, 0, 2.45)),
    ("UpperTorso", "LowerTorso", (0, 0, 2.45), (0, 0, 3.5)),
    ("Head", "UpperTorso", (0, 0, 3.5), (0, 0, 4.55)),
    ("BocaSup", "Head", (0, -0.69, 3.71), (0, -0.69, 3.81)),
    ("BocaInf", "Head", (0, -0.69, 3.66), (0, -0.69, 3.56)),
    ("LeftUpperArm", "UpperTorso", (0.84, 0, 3.0), (1.10, 0, 2.48)),
    ("LeftLowerArm", "LeftUpperArm", (1.10, 0, 2.48), (1.24, 0, 1.98)),
    ("LeftHand", "LeftLowerArm", (1.24, 0, 1.98), (1.27, 0, 1.55)),
    ("RightUpperArm", "UpperTorso", (-0.84, 0, 3.0), (-1.10, 0, 2.48)),
    ("RightLowerArm", "RightUpperArm", (-1.10, 0, 2.48), (-1.24, 0, 1.98)),
    ("RightHand", "RightLowerArm", (-1.24, 0, 1.98), (-1.27, 0, 1.55)),
    ("LeftUpperLeg", "LowerTorso", (0.40, 0, 1.35), (0.41, 0, 0.85)),
    ("LeftLowerLeg", "LeftUpperLeg", (0.41, 0, 0.85), (0.42, 0, 0.24)),
    ("LeftFoot", "LeftLowerLeg", (0.42, 0, 0.24), (0.42, -0.36, 0.12)),
    ("RightUpperLeg", "LowerTorso", (-0.40, 0, 1.35), (-0.41, 0, 0.85)),
    ("RightLowerLeg", "RightUpperLeg", (-0.41, 0, 0.85), (-0.42, 0, 0.24)),
    ("RightFoot", "RightLowerLeg", (-0.42, 0, 0.24), (-0.42, -0.36, 0.12)),
]


def build_armature(coll):
    arm = bpy.data.armatures.new("Tripulante_Rig")
    obj = bpy.data.objects.new("Tripulante", arm)
    coll.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = {}
    for name, parent, h, t in BONES:
        eb = arm.edit_bones.new(name)
        eb.head = h
        eb.tail = t
        eb.roll = 0.0
        if parent:
            eb.parent = ebs[parent]
            eb.use_connect = False
        ebs[name] = eb
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.display_type = "STICK"
    return obj


def build_meshes(coll, rig, acc, mat):
    objs = []
    for part in PARTS:
        a = acc[part]
        me = bpy.data.meshes.new(part + "_Geo")
        me.from_pydata([tuple(v) for v in a["v"]], [], a["f"])
        me.update()
        uvl = me.uv_layers.new(name="UVMap")
        for i, uv in enumerate(a["uv"]):
            uvl.data[i].uv = uv
        try:
            me.shade_smooth()
        except AttributeError:
            for p in me.polygons:
                p.use_smooth = True
        me.normals_split_custom_set(a["n"])
        me.materials.append(mat)
        ob = bpy.data.objects.new(part + "_Geo", me)
        coll.objects.link(ob)
        ob.parent = rig
        for bone, _, _, _ in BONES:
            if bone in ("Root", "HumanoidRootNode"):
                continue
            ob.vertex_groups.new(name=bone)
        for vi, w in enumerate(a["w"]):
            for bone, val in w.items():
                ob.vertex_groups[bone].add([vi], val, "REPLACE")
        mod = ob.modifiers.new("Armature", "ARMATURE")
        mod.object = rig
        objs.append(ob)
    return objs


def pose(rig, rots):
    for bone, axis, deg in rots:
        bpy.context.view_layer.update()
        pb = rig.pose.bones[bone]
        m = pb.matrix.copy()
        if axis == "T":
            pb.matrix = Matrix.Translation(Vector(deg)) @ m
            continue
        h = m.translation.copy()
        r = Matrix.Rotation(math.radians(deg), 4, axis)
        pb.matrix = Matrix.Translation(h) @ r @ Matrix.Translation(-h) @ m
    bpy.context.view_layer.update()


def clone(rig, objs, coll, mat, loc, rot_z=0.0):
    r2 = rig.copy()
    r2.data = rig.data
    r2.animation_data_clear()
    coll.objects.link(r2)
    r2.location = loc
    r2.rotation_euler = (0, 0, math.radians(rot_z))
    r2.hide_render = False
    for ob in objs:
        o2 = ob.copy()
        coll.objects.link(o2)
        o2.parent = r2
        o2.modifiers["Armature"].object = r2
        o2.material_slots[0].link = "OBJECT"
        o2.material_slots[0].material = mat
        o2.hide_render = False
    return r2


def render_setup(scene, res):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 96
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    scene.cycles.max_bounces = 6
    scene.render.resolution_x, scene.render.resolution_y = res
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
    so.rotation_euler = (math.radians(48), math.radians(8), math.radians(-28))
    scene.collection.objects.link(so)
    gm = bpy.data.materials.new("Ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*lin(hex_rgb("EFE9DC")), 1.0)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60)
    gme = bpy.data.meshes.new("Ground")
    bm.to_mesh(gme)
    gme.materials.append(gm)
    go = bpy.data.objects.new("Ground", gme)
    scene.collection.objects.link(go)


def camera(scene, loc, target, lens=None, ortho=None):
    cd = bpy.data.cameras.new("Cam")
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


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    coll = scene.collection
    build_character()
    acc = assemble()
    img = make_palette_image()
    mat = palette_material("Tripulante_Palette", img, PLAYER_COLORS["Lavanda"])
    exp = export_material(img)
    rig = build_armature(coll)
    objs = build_meshes(coll, rig, acc, mat)
    tc = {o.name[:-4]: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}
    budget = {"Head": (["Head"], 4000), "Torso": (["UpperTorso", "LowerTorso"], 1750)}
    for sd in ("Left", "Right"):
        budget[sd + "Arm"] = ([sd + "UpperArm", sd + "LowerArm", sd + "Hand"], 1248)
        budget[sd + "Leg"] = ([sd + "UpperLeg", sd + "LowerLeg", sd + "Foot"], 1248)
    for k, (ps, lim) in budget.items():
        n = sum(tc[x] for x in ps)
        print("BUDGET", k, n, "/", lim, "OK" if n <= lim else "OVER")
    print("TRIS", sum(tc.values()), "/ 10742")
    for o in objs:
        o.data.materials[0] = exp
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUT, "tripulante.fbx"),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        use_mesh_modifiers=False,
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="Z",
        axis_up="Y",
        mesh_smooth_type="OFF",
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        armature_nodetype="NULL",
        bake_anim=False,
        path_mode="COPY",
        embed_textures=True,
    )
    for o in objs:
        o.data.materials[0] = mat
    img.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "tripulante.blend"))

    if "--render" not in sys.argv:
        return
    rdir = os.path.join(OUT, "renders")
    os.makedirs(rdir, exist_ok=True)
    rig.hide_render = True
    for o in objs:
        o.hide_render = True
    render_setup(scene, (1600, 900))
    mats = {nm: palette_material("Tripulante_" + nm, img, hx) for nm, hx in PLAYER_COLORS.items()}

    def boca(k):
        return [("BocaSup", "T", (0.0, -0.004 * k, 0.05 * k)), ("BocaInf", "T", (0.0, -0.02 * k, -0.24 * k))]

    def shot(name, cast, cam, res, samples):
        made = []
        for nm, loc, rz, p in cast:
            made.append((clone(rig, objs, coll, mats[nm], loc, rot_z=rz), p))
        bpy.context.view_layer.update()
        for r2, p in made:
            pose(r2, p)
        co = camera(scene, **cam)
        scene.render.resolution_x, scene.render.resolution_y = res
        scene.cycles.samples = samples
        scene.render.filepath = os.path.join(rdir, name + ".png")
        bpy.ops.render.render(write_still=True)
        for r2, _ in made:
            for ch in list(r2.children):
                bpy.data.objects.remove(ch)
            bpy.data.objects.remove(r2)
        bpy.data.objects.remove(co)

    wave = [("RightUpperArm", "Y", 150), ("RightLowerArm", "Y", 25), ("Head", "Y", 8)]
    carry = [("LeftUpperArm", "X", -55), ("RightUpperArm", "X", -55), ("LeftLowerArm", "X", -45), ("RightLowerArm", "X", -45)]
    run = [("UpperTorso", "X", 8), ("LeftUpperLeg", "X", -38), ("LeftLowerLeg", "X", 45), ("RightUpperLeg", "X", 28), ("RightLowerLeg", "X", 20), ("RightUpperArm", "X", -40), ("RightLowerArm", "X", -50), ("LeftUpperArm", "X", 35), ("LeftLowerArm", "X", -30)]
    shot("lineup", [
        ("Lima", (-4.2, 0, 0), 12, wave + boca(0.55)),
        ("Lavanda", (-1.4, 0, 0), 4, []),
        ("Chicle", (1.4, 0, 0), -4, carry + boca(1.0)),
        ("Sol", (4.2, 0, 0), -14, run + boca(0.3)),
    ], dict(loc=(0.6, -14.5, 5.0), target=(0, 0, 2.15), lens=42), (1600, 900), 96)
    shot("turnaround", [("Lavanda", (-4.5 + 3.0 * i, 0, 0), rz, []) for i, rz in enumerate((0, -40, -90, 180))],
         dict(loc=(0, -20, 2.4), target=(0, 0, 2.4), ortho=13.2), (1600, 640), 96)
    shot("boca_voz", [
        ("Lima", (-2.0, 0, 0), 0, []),
        ("Lavanda", (0.0, 0, 0), 0, boca(0.5)),
        ("Chicle", (2.0, 0, 0), 0, boca(1.0)),
    ], dict(loc=(0, -6.4, 3.9), target=(0, 0, 3.72), lens=38), (1600, 700), 64)
    shot("brazos_prueba", [
        ("Sol", (-4.2, 0, 0), 20, [("LeftUpperArm", "Y", -150), ("RightUpperArm", "Y", 150)] + boca(0.6)),
        ("Lima", (-1.4, 0, 0), 30, [("LeftUpperArm", "X", -75), ("RightUpperArm", "X", -75), ("LeftLowerArm", "X", -35), ("RightLowerArm", "X", -35)]),
        ("Lavanda", (1.4, 0, 0), 30, [("LeftUpperArm", "Y", -88), ("RightUpperArm", "Y", 88), ("LeftLowerArm", "X", -90), ("RightLowerArm", "X", -90)]),
        ("Chicle", (4.2, 0, 0), 25, [("UpperTorso", "X", 15), ("LeftUpperArm", "X", 60), ("RightUpperArm", "X", 60), ("LeftLowerArm", "X", -40), ("RightLowerArm", "X", -40), ("LeftUpperLeg", "X", -60), ("RightUpperLeg", "X", -60), ("LeftLowerLeg", "X", 80), ("RightLowerLeg", "X", 80)]),
    ], dict(loc=(0.6, -14.5, 5.0), target=(0, 0, 2.15), lens=42), (1600, 900), 64)

main()
