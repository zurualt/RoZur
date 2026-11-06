"""Icono y portada de la pagina del juego (Roblox).

Blender:  blender -b --factory-startup --python-exit-code 1 -P pagina_gen.py -- [icono] [alt] [portada] [--rapido] [--cpu]
          Renderiza las capas en capas/ (en la GPU con OptiX; --cpu si no hay) y luego compone con PIL llamando a este
          mismo script con python -I (--sin-componer lo salta). --rapido: media resolucion y pocas muestras, para probar.
          --solo-fondo: solo el fondo de la portada. Imprime CHOQUE con las piezas que se cruzan (las juntas que ya se
          tocan en reposo y la gorra, que se mete un poco en la cabeza por su borde, no cuentan).
Python:   python -I pagina_gen.py      solo compone las imagenes finales a partir de capas/.
"""
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARTE = os.path.dirname(AQUI)
CAPAS = os.path.join(AQUI, "capas")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]

try:
    import bpy
except ImportError:
    bpy = None

TINTA = (42, 36, 32)
PAPEL = (255, 244, 224)
NARANJA = (242, 123, 43)
TURQUESA = (31, 166, 160)
ROJO = (217, 68, 58)


# ------------------------------------------------------------------------------------------------ Blender
if bpy is not None:
    import bmesh
    import random
    from mathutils import Vector, Matrix, Euler

    RUTA_T = os.path.join(ARTE, "tripulante", "tripulante_gen.py")
    T = {"__file__": RUTA_T, "__name__": "tripulante"}
    with open(RUTA_T, encoding="utf-8") as _fh:
        exec(compile(_fh.read().rsplit("\nmain()", 1)[0], RUTA_T, "exec"), T)
    lin, hex_rgb, cara, pose, pose_mano, POSES_MANO = T["lin"], T["hex_rgb"], T["cara"], T["pose"], T["pose_mano"], T["POSES_MANO"]
    COLORES = {"Sol": "F5CD3D", "Lima": "8BD24C", "Chicle": "F27BB5", "Lavanda": "A07CF2"}
    RAPIDO = "--rapido" in ARGS
    # Gorra de piloto: su caja en el espacio de Head (manifest de accesorios) llevada a Blender (x = -X, y = Z, z = Y).
    PIV_HEAD = Vector((0.0, -0.048, 2.845))
    GORRA_MIN = Vector((-0.9, -1.62, 0.612))
    S = {}

    def agarre_reposo(sx):
        # Igual que build_mano de tripulante_gen: punto donde la manopla cierra, en reposo.
        c, w = Vector((sx * 0.58, 0, 1.56)), Vector((sx * 0.70, 0, 1.26))
        a = (w - c).normalized()
        pn = Vector((-sx, 0, 0))
        pn = (pn - a * a.dot(pn)).normalized()
        return w + a * 0.17 + pn * 0.23, pn

    def preparar():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        with bpy.data.libraries.load(os.path.join(ARTE, "tripulante", "tripulante.blend"), link=False) as (src, dst):
            dst.objects = list(src.objects)
        S["coll_base"] = bpy.data.collections.new("Base")
        scene.collection.children.link(S["coll_base"])
        objs = []
        for o in dst.objects:
            S["coll_base"].objects.link(o)
            o.hide_render = True
            if o.type == "ARMATURE":
                S["rig"] = o
            elif o.name.startswith("Ojos_"):
                T["OJOS_OBJ"][o.name[5:-4]] = o
            else:
                objs.append(o)
        S["objs"] = objs
        S["coll_base"].hide_render = True
        img = bpy.data.images["TripulantePalette"]
        S["mats"] = {nm: T["palette_material"]("Trip_" + nm, img, hx) for nm, hx in COLORES.items()}
        gorra = importar("accesorios/GorraPiloto.fbx")
        mn = Vector([min((v.co)[i] for v in gorra.data.vertices) for i in range(3)])
        gorra.data.transform(Matrix.Translation(PIV_HEAD + GORRA_MIN - mn))
        S["gorra"] = gorra

        sc = scene
        sc.render.engine = "CYCLES"
        if "--cpu" in ARGS:
            sc.cycles.device = "CPU"
        else:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = "OPTIX"
            prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type == "OPTIX"
            sc.cycles.device = "GPU"
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 6
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_mode = "RGBA"
        sc.render.film_transparent = True
        sc.render.resolution_percentage = 100
        try:
            sc.view_settings.view_transform = "Standard"
        except TypeError:
            pass
        os.makedirs(CAPAS, exist_ok=True)

    def importar(rel):
        antes = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=os.path.join(ARTE, rel), axis_forward="Z", axis_up="Y")
        nuevos = [o for o in bpy.data.objects if o not in antes]
        malla = next(o for o in nuevos if o.type == "MESH")
        malla.data.transform(malla.matrix_world)
        malla.matrix_world = Matrix()
        malla.parent = None
        for o in nuevos:
            if o is not malla:
                bpy.data.objects.remove(o)
        for c in list(malla.users_collection):
            c.objects.unlink(malla)
        S["coll_base"].objects.link(malla)
        return malla

    PLANTILLAS = {}

    def plantilla(rel):
        if rel not in PLANTILLAS:
            PLANTILLAS[rel] = importar(rel)
        return PLANTILLAS[rel]

    def capa(nombre):
        c = bpy.data.collections.get(nombre)
        if c is None:
            c = bpy.data.collections.new(nombre)
            bpy.context.scene.collection.children.link(c)
        return c

    def poner(ob, coll):
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll.objects.link(ob)
        ob.hide_render = False
        return ob

    def copia(rel, mw, coll):
        t = plantilla(rel)
        o = bpy.data.objects.new(os.path.basename(rel)[:-4], t.data)
        o.matrix_world = mw
        return poner(o, coll)

    def malla(nombre, bm, mat, coll, mw=Matrix()):
        me = bpy.data.meshes.new(nombre)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(mat)
        o = bpy.data.objects.new(nombre, me)
        o.matrix_world = mw
        return poner(o, coll)

    MATS = {}

    def mat_color(hexa, rug=0.5, emision=0.0, nombre=None):
        clave = nombre or "M_%s_%.2f_%.2f" % (hexa, rug, emision)
        if clave in MATS:
            return MATS[clave]
        m = bpy.data.materials.new(clave)
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        c = (*lin(hex_rgb(hexa)), 1.0)
        b.inputs["Base Color"].default_value = c
        b.inputs["Roughness"].default_value = rug
        if emision > 0:
            b.inputs["Emission Color"].default_value = c
            b.inputs["Emission Strength"].default_value = emision
        MATS[clave] = m
        return m

    # ---------------------------------------------------------------- tripulantes
    def girar(r2, hueso, eje, grados):
        bpy.context.view_layer.update()
        pb = r2.pose.bones[hueso]
        m = pb.matrix.copy()
        h = m.translation.copy()
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(grados), 4, Vector(eje).normalized()) @ Matrix.Translation(-h) @ m
        bpy.context.view_layer.update()

    def apuntar(r2, hueso, d, giro=0.0):
        """Gira el hueso (en el espacio del esqueleto) para que apunte hacia d y luego lo rueda sobre si mismo."""
        bpy.context.view_layer.update()
        pb = r2.pose.bones[hueso]
        actual = (pb.tail - pb.head).normalized()
        q = actual.rotation_difference(Vector(d).normalized())
        m = pb.matrix.copy()
        h = m.translation.copy()
        pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ m
        if isinstance(giro, tuple):
            # giro = hacia donde tiene que mirar la palma: rueda el antebrazo lo que haga falta.
            lado = "Left" if hueso.startswith("Left") else "Right"
            _, n = mano(r2, lado)
            n = r2.matrix_world.to_3x3().inverted() @ n
            d = Vector(d).normalized()
            p = Vector(giro)
            n = (n - d * n.dot(d)).normalized()
            p = (p - d * p.dot(d)).normalized()
            girar(r2, hueso, d, math.degrees(math.atan2(d.dot(n.cross(p)), n.dot(p))))
        elif giro:
            girar(r2, hueso, d, giro)
        bpy.context.view_layer.update()

    def tripulante(color, coll, mw, ojos="normal", cuerpo=(), brazos=(), caras=(), manos=None, gorra=True):
        r2 = T["clone"](S["rig"], S["objs"], coll, S["mats"][color], (0, 0, 0), ojos=ojos)
        r2.matrix_world = mw
        for ch in r2.children:
            poner(ch, coll)
        poner(r2, coll)
        bpy.context.view_layer.update()
        pose(r2, list(cuerpo))
        for hueso, d, g in brazos:
            apuntar(r2, hueso, d, g)
        pose(r2, list(caras))
        for lado, nombre in (manos or {}).items():
            pose_mano(r2, lado, POSES_MANO[nombre] if isinstance(nombre, str) else nombre)
        bpy.context.view_layer.update()
        if gorra:
            g = bpy.data.objects.new("Gorra", S["gorra"].data)
            m = hueso_mw(r2, "Head")
            g.parent = r2
            g.matrix_parent_inverse = r2.matrix_world.inverted()
            g.matrix_world = m
            poner(g, coll)
        return r2

    def hueso_mw(r2, hueso):
        """Matriz que lleva un punto del tripulante en reposo a donde esta ahora con ese hueso."""
        bpy.context.view_layer.update()
        return r2.matrix_world @ r2.pose.bones[hueso].matrix @ r2.data.bones[hueso].matrix_local.inverted()

    def mano(r2, lado):
        """Punto de agarre de la manopla y normal de la palma, en el mundo."""
        sx = 1 if lado == "Left" else -1
        p, n = agarre_reposo(sx)
        m = hueso_mw(r2, lado + "Hand")
        return m @ p, (m.to_3x3() @ n).normalized()

    # ---------------------------------------------------------------- piezas sueltas
    def gota_bm(r=1.0, punta=1.9, plano=1.0):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1.0)
        for v in bm.verts:
            z = v.co.z
            if z > 0:
                f = (1.0 - z) ** 0.85
                v.co.x *= f
                v.co.y *= f
                v.co.z = z * punta
            v.co.y *= plano
        bmesh.ops.scale(bm, vec=(r, r, r), verts=bm.verts)
        return bm

    def bola_bm(r, u=20, v=12):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)
        return bm

    def gota(coll, pos, dirc, r):
        """Gota de sudor: punta hacia la cabeza (de donde sale), cola redonda hacia fuera, con brillo."""
        d = Vector(dirc).normalized()
        m = Matrix.Translation(pos) @ (-d).to_track_quat("Z", "Y").to_matrix().to_4x4()
        malla("Gota", gota_bm(r), mat_color("6FD0FF", 0.12, 0.25), coll, m)
        b = bmesh.new()
        bmesh.ops.create_uvsphere(b, u_segments=12, v_segments=8, radius=1.0)
        bmesh.ops.scale(b, vec=(0.22 * r, 0.12 * r, 0.32 * r), verts=b.verts)
        malla("Brillo", b, mat_color("FFFFFF", 0.3, 1.2), coll, m @ Matrix.Translation((-0.38 * r, -0.62 * r, 0.25 * r)) @ Matrix.Rotation(0.4, 4, "Y"))

    def humo(coll, puntos, r0, r1, semilla=1, colores=("4E4E5A", "76768A", "9C9CAE", "C2C2D0"), pasos=None):
        """Estela de humo: racimos de bolas que crecen y se aclaran a lo largo de la curva."""
        rnd = random.Random(semilla)
        pts = T["catmull"]([Vector(p) for p in puntos], 8)
        acum = [0.0]
        for i in range(len(pts) - 1):
            acum.append(acum[-1] + (pts[i + 1] - pts[i]).length)
        largo = acum[-1]
        n = pasos or max(6, int(largo / ((r0 + r1) * 0.5)))
        for k in range(n):
            u = k / (n - 1)
            s = u * largo
            i = next((j for j in range(len(acum) - 1) if acum[j + 1] >= s), len(pts) - 2)
            t = (s - acum[i]) / max(1e-6, acum[i + 1] - acum[i])
            c = pts[i].lerp(pts[i + 1], t)
            r = r0 + (r1 - r0) * u ** 0.8
            col = mat_color(colores[min(len(colores) - 1, int(u * len(colores)))], 1.0)
            for j in range(3 if k else 1):
                off = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * r * (0.55 if j else 0.15)
                malla("Humo", bola_bm(r * (rnd.uniform(0.85, 1.05) if j == 0 else rnd.uniform(0.5, 0.75))), col, coll, Matrix.Translation(c + off))

    def fuego(coll, base, arriba, esc=1.0, semilla=3):
        """Llama de dibujo: lenguas en forma de gota, aplanadas hacia la camara, en tres capas (rojo, naranja, amarillo)
        cada una un poco por delante de la anterior para que se vean las tres."""
        rnd = random.Random(semilla)
        cam = bpy.context.scene.camera.matrix_world.translation
        up = Vector(arriba).normalized()
        hacia = (cam - base)
        hacia = (hacia - up * hacia.dot(up)).normalized()
        x = up.cross(hacia).normalized()
        marco = Matrix((x, -hacia, up)).transposed().to_4x4()
        lenguas = [(0.0, 0.0, 1.0)] + [(s * rnd.uniform(0.45, 0.6), s * rnd.uniform(18, 30), rnd.uniform(0.55, 0.75)) for s in (-1, 1)]
        for i, (col, k, em) in enumerate((("FF3B1A", 1.0, 2.0), ("FF9A1F", 0.72, 2.4), ("FFE45A", 0.44, 3.0))):
            for dx, ang, alto in lenguas:
                m = (Matrix.Translation(base + hacia * (0.12 * i * esc) + x * (dx * 0.35 * k * esc)) @ marco @
                     Matrix.Rotation(math.radians(ang), 4, "Y") @ Matrix.Translation((0, 0, -0.1 * esc * i)))
                malla("Fuego", gota_bm(0.42 * esc * k * (0.75 + 0.25 * alto), 3.2 * alto, 0.4), mat_color(col, 0.5, em), coll, m)

    def luces(sol=(52, 0, -35), energia=3.6, contra=True, cielo="8FD3FF", fuerza=0.9):
        coll = bpy.context.scene.collection
        w = bpy.data.worlds.new("Cielo")
        w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = (*lin(hex_rgb(cielo)), 1.0)
        w.node_tree.nodes["Background"].inputs[1].default_value = fuerza
        bpy.context.scene.world = w
        d = bpy.data.lights.new("Sol", "SUN")
        d.energy = energia
        d.angle = math.radians(10)
        d.color = (1.0, 0.96, 0.9)
        o = bpy.data.objects.new("Sol", d)
        o.rotation_euler = [math.radians(a) for a in sol]
        coll.objects.link(o)
        if contra:
            d2 = bpy.data.lights.new("Contra", "SUN")
            d2.energy = 2.0
            d2.angle = math.radians(6)
            d2.color = (1.0, 0.97, 0.92)
            o2 = bpy.data.objects.new("Contra", d2)
            o2.rotation_euler = (math.radians(-60), 0, math.radians(200))
            coll.objects.link(o2)

    def camara(loc, target, lens, shift=(0.0, 0.0)):
        coll = bpy.context.scene.collection
        cd = bpy.data.cameras.new("Cam")
        cd.lens = lens
        cd.sensor_fit = "HORIZONTAL"
        cd.clip_start = 0.1
        cd.clip_end = 5000
        cd.shift_x, cd.shift_y = shift
        co = bpy.data.objects.new("Cam", cd)
        coll.objects.link(co)
        co.location = loc
        co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.camera = co
        return co

    def en_pantalla(u, v, dist):
        """Punto del mundo que la camara ve en (u, v) (fraccion del ancho, 0 = centro, v hacia arriba) a esa distancia."""
        sc = bpy.context.scene
        co = sc.camera
        bpy.context.view_layer.update()
        r = co.matrix_world.to_3x3()
        media = dist * 18.0 / co.data.lens
        return co.matrix_world.translation + r @ Vector((2 * u * media + co.data.shift_x * 2 * media, 2 * v * media + co.data.shift_y * 2 * media, -dist))

    def orientar_cam(morro, arriba, alabeo=0.0):
        """Orientacion del avion con el morro y el techo dados en el espacio de la camara (x derecha, y arriba, z hacia la camara),
        alabeado esos grados sobre el morro."""
        r = bpy.context.scene.camera.matrix_world.to_3x3()
        d = (r @ Vector(morro)).normalized()
        up = r @ Vector(arriba)
        up = (up - d * up.dot(d)).normalized()
        up = Matrix.Rotation(math.radians(alabeo), 3, d) @ up
        y = -d
        x = y.cross(up).normalized()
        return Matrix((x, y, up)).transposed().to_4x4()

    def bvh_de(ob):
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        b = T["BVHTree"].FromPolygons([ob.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
        ev.to_mesh_clear()
        return b

    def choques(coll, nombre):
        """Cuenta triangulos que se cruzan entre piezas distintas de la capa (tripulantes por pieza, objetos sueltos)
        y lo imprime; las piezas de un mismo tripulante que ya se tocan en reposo (cuello, munecas) no cuentan."""
        if "base" not in S:
            bb = {o.name: bvh_de(o) for o in S["objs"]}
            S["base"] = {(a, b): len(bb[a].overlap(bb[b])) for a in bb for b in bb if a < b}
            # La gorra se mete un poco en la cabeza por su borde (asi esta hecha para el juego): eso no cuenta.
            S["base"][("Gorra", "Head_Geo")] = len(bvh_de(S["gorra"]).overlap(bb[next(n for n in bb if n.startswith("Head_Geo"))]))
        obs = [o for o in coll.objects if o.type == "MESH" and not o.name.startswith(("Humo", "Fuego", "Ojo", "Brillo"))]
        bv = {o.name: bvh_de(o) for o in obs}
        for i, a in enumerate(obs):
            for b in obs[i + 1:]:
                n = len(bv[a.name].overlap(bv[b.name]))
                k = tuple(sorted((a.name.split(".")[0], b.name.split(".")[0])))
                if a.parent is not None and a.parent == b.parent:
                    n = n - S["base"].get(k, 0) if k in S["base"] else 0
                if n > 0:
                    print("CHOQUE", nombre, a.name, b.name, n)

    def render(nombre, res, muestras, visibles):
        sc = bpy.context.scene
        for c in sc.collection.children:
            c.hide_render = c.name not in visibles
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.resolution_percentage = 50 if RAPIDO else 100
        sc.cycles.samples = max(16, muestras // 4) if RAPIDO else muestras
        sc.render.filepath = os.path.join(CAPAS, nombre + ".png")
        bpy.ops.render.render(write_still=True)
        print("CAPA", sc.render.filepath)

    def limpiar():
        for c in list(bpy.context.scene.collection.children):
            if c.name == "Base":
                continue
            for o in list(c.objects):
                bpy.data.objects.remove(o)
            bpy.data.collections.remove(c)
        for o in list(bpy.context.scene.collection.objects):
            bpy.data.objects.remove(o)

    # ---------------------------------------------------------------- icono
    def avion_cayendo(coll, mw, humo_pts, r0, r1, semilla=5, motor=18.0, llama=1.0):
        """El avion (morro en -Y, motores en x = +-18, y -28.5 a -18.75, z -4) con un motor ardiendo y su estela."""
        copia("avion/AvionExterior.fbx", mw, coll)
        esc = mw.to_scale().x
        atras = (mw.to_3x3() @ Vector((0, 1, 0.25))).normalized()
        fuego(coll, mw @ Vector((motor, -21.0, -2.2)), atras, 9.0 * esc * llama, semilla)
        humo(coll, humo_pts, r0, r1, semilla)

    def motor_visible(amw):
        """El motor (x = +-18) del lado del avion que mira a la camara."""
        hacia = bpy.context.scene.camera.matrix_world.translation - amw.translation
        return 18.0 if (amw.to_3x3() @ Vector((1, 0, 0))).dot(hacia) > 0 else -18.0

    def dir_cam(mw, v):
        """Una direccion dada en el espacio de la camara (x derecha, y arriba, z hacia la camara), en el del tripulante."""
        return tuple(mw.to_3x3().inverted() @ (bpy.context.scene.camera.matrix_world.to_3x3() @ Vector(v)).normalized())

    def sujetar(mw, lado, antebrazo, eje):
        """Antebrazo y manopla para agarrar con el puno algo cuyo eje va hacia eje (todo en el espacio de la camara):
        los dedos siguen al antebrazo y rodean el eje (dedos x palma = eje, como en_puno)."""
        d = Vector(dir_cam(mw, antebrazo))
        a = Vector(dir_cam(mw, eje))
        a = (a - d * a.dot(d)).normalized()
        n = a.cross(d).normalized()
        return [(lado + "LowerArm", tuple(d), 0), (lado + "Hand", tuple(d), tuple(n))], a

    def estela(amw, motor, puntos, lado=1):
        """Curva del humo: sale del motor hacia la cola (s, en largos de avion) y se tuerce en pantalla (c a un lado, h arriba)."""
        r = bpy.context.scene.camera.matrix_world.to_3x3()
        R, U = r @ Vector((lado, 0, 0)), r @ Vector((0, 1, 0))
        atras = (amw.to_3x3() @ Vector((0, 1, 0))).normalized()
        L = 97.0 * amw.to_scale().x
        m0 = amw @ Vector((motor, -18.0, -4.0))
        return [m0 + atras * L * s + R * L * c + U * L * h for s, c, h in puntos]

    def sobre_palma(r2, lado, esc, giro=0.0, alto=-0.1, adelante=0.0):
        """Matriz de un objeto apoyado en la palma abierta (su origen en la base): igual que Manos.desfase.
        adelante lo corre hacia la punta de la manopla."""
        p, n = mano(r2, lado)
        pb = r2.pose.bones[lado + "Hand"]
        punta = (r2.matrix_world.to_3x3() @ (pb.tail - pb.head)).normalized()
        punta = (punta - n * punta.dot(n)).normalized()
        return (Matrix.Translation(p + n * alto + punta * adelante) @ n.to_track_quat("Z", "Y").to_matrix().to_4x4() @
                Matrix.Rotation(math.radians(giro), 4, "Z") @ Matrix.Diagonal((esc, esc, esc, 1)))

    def icono(nombre, color, ojos, cara_rots, brazos, manos, extra=None, avion=(-0.37, 0.27), gotas=True, cabeza_rots=(("Head", "Y", 6), ("Head", "X", -5)), cam=((0.9, -5.45, 2.85), (0.0, 0, 3.4))):
        limpiar()
        cp, cf = capa("Personaje"), capa("Fondo")
        luces(sol=(50, 0, -38), energia=3.4, cielo="CFE6F2", fuerza=0.8)
        camara(cam[0], cam[1], 60)
        mw = Matrix.Rotation(math.radians(-10), 4, "Z")
        r2 = tripulante(color, cp, mw, ojos=ojos, cuerpo=list(cabeza_rots), brazos=brazos, caras=cara_rots, manos=manos)
        if extra:
            extra(r2, cp)
        cabeza = hueso_mw(r2, "Head")
        for p, d, r in (((-1.22, -0.3, 3.55), (-1, 0, 0.5), 0.2), ((-1.42, -0.1, 3.08), (-1, 0, -0.1), 0.14),
                        ((1.2, -0.35, 3.55), (1, 0, 0.55), 0.18)) if gotas else ():
            gota(cp, cabeza @ Vector(p), cabeza.to_3x3() @ Vector(d), r)
        # Avion pequeno cayendo en picado por detras, con un motor ardiendo y su estela hacia arriba.
        dist = 40.0
        ancho = 2 * dist * 18.0 / 60.0
        e = ancho * 0.3 / 97.0
        u, v = avion
        lado = 1 if u > 0 else -1
        amw = Matrix.Translation(en_pantalla(u, v, dist)) @ orientar_cam((lado * 0.3, -0.9, 0.3), (-lado * 0.35, 0.1, 0.9)) @ Matrix.Diagonal((e, e, e, 1))
        motor = 18.0 * lado
        pts = estela(amw, motor, ((0, 0, 0), (0.3, 0, 0), (0.6, 0.04, 0.04), (0.85, 0.2, 0.12), (1.0, 0.45, 0.16), (1.1, 0.8, 0.18)), -lado)
        avion_cayendo(cf, amw, pts, ancho * 0.018, ancho * 0.08, 7, motor, 2.4)
        choques(cp, nombre)
        render(nombre + "_personaje", (1024, 1024), 128, {"Personaje"})
        render(nombre + "_fondo", (1024, 1024), 96, {"Fondo"})

    def icono_grito():
        brazos = [("RightUpperArm", (-0.75, -0.35, 0.55), 0), ("RightLowerArm", (-0.35, -0.45, 0.85), -30),
                  ("LeftUpperArm", (0.8, -0.3, 0.5), 0), ("LeftLowerArm", (0.6, -0.4, 0.7), 30)]
        icono("icono", "Sol", "susto", cara(boca=1.32, cejas=1.3, giro=-0.6, mejillas=1.5, flop=1.0, fase=0.068),
              brazos, {"Left": "abierta", "Right": "abierta"})

    def ojos_risa(r2, coll):
        """Ojos cerrados de risa (arcos ^ ^) pegados a la cara, en el sitio de los ojos saltones (OJO_CENTRO/OJO_NORMAL)."""
        cabeza = next(o for o in r2.children if o.name.startswith("Head_Geo"))
        dg = bpy.context.evaluated_depsgraph_get()
        me = cabeza.evaluated_get(dg).to_mesh()
        mwh = cabeza.matrix_world
        bvh = T["BVHTree"].FromPolygons([mwh @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
        cabeza.evaluated_get(dg).to_mesh_clear()
        h = hueso_mw(r2, "Head")
        for sx in (-1, 1):
            c = h @ Vector((sx * 0.336, -0.890, 3.009))
            n = (h.to_3x3() @ Vector((sx * 0.166, -0.986, -0.028))).normalized()
            up = (h.to_3x3() @ Vector((0, 0, 1)))
            x = up.cross(n).normalized()
            y = n.cross(x).normalized()
            pts = []
            for k in range(9):
                a = math.radians(-75 + 150 * k / 8)
                p = c + x * math.sin(a) * 0.19 + y * (math.cos(a) * 0.17 - 0.06)
                hit = bvh.ray_cast(p + n * 0.6, -n, 2.0)
                pts.append(hit[0] + hit[1] * 0.012 if hit[0] is not None else p)
            bm, _ = T["tube"](pts, lambda u: 0.042 * (0.8 + 0.2 * math.sin(math.pi * u)), k=16, steps=4, up=n)
            malla("OjoRisa", bm, mat_color("1B1B21", 0.4), coll)

    def icono_alt():
        brazos = [("RightUpperArm", (-0.95, -0.3, 0.12), 0), ("RightLowerArm", (-0.85, -0.5, 0.25), 0),
                  ("RightHand", (-0.9, -0.45, 0.1), (0.0, -0.3, 1.0)),
                  ("LeftUpperArm", (0.75, -0.25, 0.55), 0), ("LeftLowerArm", (0.3, -0.35, 0.9), 30)]

        def extra(r2, cp):
            copia("props/Hamburguesa.fbx", sobre_palma(r2, "Right", 1.3, 20, 0.0, 0.2), cp)
            ojos_risa(r2, cp)
        icono("icono_alt", "Chicle", None, cara(boca=0.75, cejas=0.9, giro=-0.35, mejillas=1.6, lengua=0.4),
              brazos, {"Left": "abierta", "Right": "palma"}, extra, gotas=False, cabeza_rots=(("Head", "Y", -8), ("Head", "X", -9)), cam=((0.9, -6.3, 2.7), (-0.2, 0, 3.0)))

    # ---------------------------------------------------------------- portada
    CABEZA_REPOSO = Vector((0, 0, 3.03))

    def colocar(u, v, dist, rx=0.0, ry=0.0, rz=0.0):
        """Matriz del tripulante para que el centro de su cabeza caiga en (u, v) de la pantalla a esa distancia.
        rz gira hacia los lados, rx lo echa hacia delante o atras y ry lo ladea en la pantalla."""
        co = bpy.context.scene.camera
        hacia = (co.matrix_world.translation - en_pantalla(u, v, dist))
        hacia.z = 0
        base = Matrix.Rotation(math.atan2(-hacia.x, hacia.y) + math.pi, 4, "Z") if hacia.length > 1e-6 else Matrix()
        r = base @ Matrix.Rotation(math.radians(rz), 4, "Z") @ Matrix.Rotation(math.radians(ry), 4, "Y") @ Matrix.Rotation(math.radians(rx), 4, "X")
        return Matrix.Translation(en_pantalla(u, v, dist) - r.to_3x3() @ CABEZA_REPOSO) @ r

    def piernas(izq, der):
        """Direcciones de muslo y espinilla (en el espacio del tripulante) para cada pierna."""
        return [("LeftUpperLeg", izq[0], 0), ("LeftLowerLeg", izq[1], 0), ("RightUpperLeg", der[0], 0), ("RightLowerLeg", der[1], 0)]

    def en_puno(r2, lado, radio, eje_signo=1):
        """Centro y eje de un objeto cilindrico agarrado con el puno (como Manos.separacion)."""
        p, n = mano(r2, lado)
        pb = r2.pose.bones[lado + "Hand"]
        dedos = (r2.matrix_world.to_3x3() @ (pb.tail - pb.head)).normalized()
        eje = dedos.cross(n).normalized() * eje_signo
        return p + n * max(0.0, radio - 0.1), eje

    def separar(ob, r2, lado, n, paso=0.015, tope=0.3):
        """Aparta el objeto de la palma (hacia n) hasta que la manopla deja de meterse dentro. Devuelve lo que se ha movido."""
        manopla = next(o for o in r2.children if o.name.startswith(lado + "Hand_Geo"))
        bm = bvh_de(manopla)
        movido = Vector()
        while len(bm.overlap(bvh_de(ob))) and movido.length < tope:
            ob.matrix_world = Matrix.Translation(n * paso) @ ob.matrix_world
            movido += n * paso
            bpy.context.view_layer.update()
        print("SEPARAR", ob.name, round(movido.length, 3))
        return movido

    def alinear(eje_z, pos, esc, giro=0.0):
        return (Matrix.Translation(pos) @ Vector(eje_z).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4() @
                Matrix.Rotation(math.radians(giro), 4, "Z") @ Matrix.Diagonal((esc, esc, esc, 1)))

    def portada():
        limpiar()
        sc = bpy.context.scene
        luces(sol=(48, 0, -40), energia=3.4, cielo="CFE6F2", fuerza=0.85)
        camara((0.0, -12.0, 2.6), (0.0, 0.0, 2.9), 30)
        cf = capa("Fondo")
        rnd = random.Random(11)

        # Avion grande detras de la tripulacion, de lado y en picado (cola arriba a la izquierda, morro abajo a la derecha),
        # con la puerta abierta de este lado y su motor ardiendo; la estela sube hacia la esquina de arriba a la izquierda.
        amw = Matrix.Translation(en_pantalla(-0.09, -0.025, 120.0)) @ orientar_cam((0.85, -0.45, 0.1), (0.45, 0.85, 0.05), -20)
        motor = motor_visible(amw)
        pts = estela(amw, motor, ((0, 0, 0), (0.3, 0, 0), (0.6, 0.0, 0.03), (0.9, 0.02, 0.08), (1.2, 0.08, 0.12), (1.5, 0.16, 0.14)), -1)
        avion_cayendo(cf, amw, pts, 2.2, 8.5, 21, motor, 1.9)
        # Carga cayendo entre el avion y la tripulacion: (archivo, u, v, distancia, tamano en pixeles).
        caidas = [("props/Maleta1.fbx", 0.06, -0.01, 70, 70), ("props/Maleta2.fbx", 0.44, 0.13, 50, 95), ("props/Maleta3.fbx", 0.28, -0.21, 28, 120),
                  ("props/Caja.fbx", -0.21, 0.01, 60, 80), ("kit_caos/Cabra.fbx", 0.3, 0.2, 70, 170), ("props/Maleta1.fbx", 0.47, -0.07, 26, 120),
                  ("props/Maleta3.fbx", -0.47, -0.17, 30, 110), ("props/Maleta2.fbx", -0.28, 0.17, 90, 70)]
        for rel, u, v, d, px in caidas:
            t = plantilla(rel)
            e = px / 1920 * (2 * d * 18.0 / sc.camera.data.lens) / max(t.dimensions)
            rot = Euler([rnd.uniform(0, 6.28) for _ in range(3)]).to_matrix().to_4x4()
            if "Cabra" in rel:
                rot = sc.camera.matrix_world.to_3x3().to_4x4() @ Matrix.Rotation(math.radians(-35), 4, "Z") @ Matrix.Rotation(math.radians(-90), 4, "X") @ Matrix.Rotation(math.radians(70), 4, "Z")
            copia(rel, Matrix.Translation(en_pantalla(u, v, d)) @ rot @ Matrix.Diagonal((e, e, e, 1)) @ Matrix.Translation((0, 0, -t.dimensions.z / 2)), cf)
        # Nubes: un mar abajo y algunas sueltas.
        for rel, u, v, d, e, rz in (("kit_cielo/NubeCumulo1.fbx", -0.42, -0.36, 700, 1.0, 10), ("kit_cielo/NubeCumulo2.fbx", 0.05, -0.38, 800, 1.0, -20),
                                    ("kit_cielo/NubeCumulo3.fbx", 0.45, -0.34, 650, 1.0, 40), ("kit_cielo/NubeTorre.fbx", -0.5, -0.05, 900, 1.0, 0),
                                    ("kit_cielo/NubePequena1.fbx", -0.3, 0.2, 500, 1.2, 0), ("kit_cielo/NubePequena2.fbx", 0.42, 0.24, 450, 1.2, 30),
                                    ("kit_cielo/NubeCumulo2.fbx", 0.62, -0.1, 900, 1.0, 60)):
            copia(rel, Matrix.Translation(en_pantalla(u, v, d)) @ Matrix.Rotation(math.radians(rz), 4, "Z") @ Matrix.Diagonal((e, e, e, 1)), cf)
        render("portada_fondo", (1920, 1080), 128, {"Fondo"})

        for i, (nombre, hacer) in enumerate(portada_reparto() if "--solo-fondo" not in ARGS else []):
            c = capa("P%d" % i)
            hacer(c)
            choques(c, nombre)
            render("portada_" + nombre, (1920, 1080), 128, {"P%d" % i})

    REPARTO = ("lavanda", "chicle", "lima", "sol")

    def gotas_de(r2, coll, *gotas):
        """Gotas de sudor saliendo de la cabeza: (punto, direccion, radio) en el espacio de la cabeza en reposo."""
        cabeza = hueso_mw(r2, "Head")
        for p, d, r in gotas:
            gota(coll, cabeza @ Vector(p), cabeza.to_3x3() @ Vector(d), r)

    def portada_reparto():
        caer_corriendo = piernas(((0.15, -0.75, -0.6), (0.1, 0.05, -1.0)), ((-0.15, 0.35, -0.93), (-0.1, 0.75, -0.65)))

        def sol(c):
            # Delante, a la izquierda del centro: gritando con la lengua al viento y los brazos arriba.
            r2 = tripulante("Sol", c, colocar(-0.17, -0.085, 10.5, rx=-6, ry=12, rz=10), ojos="susto",
                       brazos=[("RightUpperArm", (-0.8, -0.2, 0.6), 0), ("RightLowerArm", (-0.45, -0.3, 0.85), -20),
                               ("LeftUpperArm", (0.85, -0.2, 0.5), 0), ("LeftLowerArm", (0.65, -0.3, 0.7), 20)] + caer_corriendo,
                       caras=cara(boca=1.3, cejas=1.3, giro=-0.6, mejillas=1.5, flop=1.0, fase=0.068), manos={"Left": "abierta", "Right": "abierta"})
            gotas_de(r2, c, ((-1.22, -0.3, 3.5), (-1, 0, 0.5), 0.2), ((1.25, -0.35, 3.45), (1, 0, 0.45), 0.17))

        def chicle(c):
            # A la derecha, con una gallina revoloteando junto a la cabeza.
            r2 = tripulante("Chicle", c, colocar(0.37, -0.005, 13.0, rx=-4, ry=-14, rz=-25), ojos="grande",
                            brazos=[("RightUpperArm", (-0.9, -0.35, -0.1), 0), ("RightLowerArm", (-0.7, -0.6, 0.3), -20),
                                    ("LeftUpperArm", (0.75, -0.3, 0.6), 0), ("LeftLowerArm", (0.55, -0.35, 0.75), 20)]
                            + piernas(((0.2, -0.3, -0.95), (0.2, 0.45, -0.88)), ((-0.15, -0.7, -0.7), (-0.1, 0.0, -1.0))),
                            caras=cara(boca=1.15, cejas=1.2, giro=-0.5, mejillas=1.0, lengua=0.5), manos={"Left": "abierta", "Right": "abierta"})
            h = hueso_mw(r2, "Head")
            copia("kit_caos/Gallina.fbx", h @ Matrix.Translation((-1.6, -0.3, 3.75)) @ Matrix.Rotation(math.radians(-30), 4, "Y") @
                  Matrix.Rotation(math.radians(70), 4, "Z") @ Matrix.Diagonal((0.75, 0.75, 0.75, 1)) @ Matrix.Translation((0, 0, -0.6)), c)

        def lima(c):
            # A la derecha del centro, mareado, echando espuma con el extintor al motor en llamas (sin ninguna utilidad).
            mw = colocar(0.175, -0.085, 12.0, rx=-4, ry=-10, rz=-20)
            agarre, eje_cam = sujetar(mw, "Right", (-0.5, -0.05, 0.86), (-0.88, 0.45, 0.0))
            r2 = tripulante("Lima", c, mw, ojos="mareo",
                            brazos=[("LeftUpperArm", (0.75, -0.3, 0.6), 0), ("LeftLowerArm", (0.55, -0.35, 0.75), 20),
                                    ("RightUpperArm", dir_cam(mw, (-0.65, -0.15, 0.75)), 0)] + agarre
                            + piernas(((0.15, -0.5, -0.85), (0.1, 0.25, -0.96)), ((-0.15, -0.2, -0.97), (-0.1, 0.5, -0.86))),
                            caras=cara(boca=0.6, cejas=0.4, giro=0.4, lengua=1.0, lado=1.0) + [("CejaIzq", "T", (0, 0, 0.07))],
                            manos={"Right": "sosten", "Left": "abierta"})
            e = 0.7
            centro, eje = en_puno(r2, "Right", 0.3 * e)
            if eje.dot(mw.to_3x3() @ Vector(eje_cam)) < 0:
                eje = -eje
            ext = copia("props/Extintor.fbx", alinear(eje, centro - eje * (1.7 * e * 0.45), e, 90), c)
            _, n = mano(r2, "Right")
            centro += separar(ext, r2, "Right", n)
            boca_ext = centro + eje * (1.7 * e * 0.6)
            r = bpy.context.scene.camera.matrix_world.to_3x3()
            humo(c, [boca_ext + eje * 0.08, boca_ext + eje * 0.5 + r @ Vector((0.0, -0.04, 0)), boca_ext + eje * 1.0 + r @ Vector((0.0, -0.12, 0))], 0.05, 0.24, 4,
                 colores=("FFFFFF", "F4FAFF", "E6F2FA"), pasos=9)

        def lavanda(c):
            # A la izquierda: con la bandeja de hamburguesas en la palma y las hamburguesas saliendo volando.
            r2 = tripulante("Lavanda", c, colocar(-0.36, 0.035, 13.5, rx=-6, ry=16, rz=28), ojos="grande",
                            brazos=[("LeftUpperArm", (0.8, -0.35, 0.5), 0), ("LeftLowerArm", (0.4, -0.4, 0.85), 20),
                                    ("RightUpperArm", (-0.9, -0.2, 0.3), 0), ("RightLowerArm", (-0.75, -0.45, 0.45), 0), ("RightHand", (-0.85, -0.5, 0.1), (0.0, -0.2, 1.0))]
                            + piernas(((0.2, -0.6, -0.75), (0.1, 0.2, -0.97)), ((-0.1, -0.3, -0.95), (-0.1, 0.35, -0.93))),
                            caras=cara(boca=1.0, cejas=1.4, giro=-0.8, mejillas=0.8), manos={"Right": "palma", "Left": "abierta"})
            m = sobre_palma(r2, "Right", 0.7, 20, 0.0, 0.1)
            copia("props/Bandeja.fbx", m, c)
            # Dos hamburguesas saltando de la bandeja hacia arriba a la izquierda (en el espacio de la camara).
            r = bpy.context.scene.camera.matrix_world.to_3x3()
            for p, g in (((-0.25, 0.75, 0.2), (30, 20, -10)), ((-0.42, 1.45, 0.1), (-25, -40, -70))):
                copia("props/Hamburguesa.fbx", Matrix.Translation(m.translation + r @ Vector(p)) @ Euler([math.radians(a) for a in g]).to_matrix().to_4x4() @
                      Matrix.Diagonal((0.75, 0.75, 0.75, 1)) @ Matrix.Translation((0, 0, -0.27)), c)
            gotas_de(r2, c, ((1.25, -0.3, 3.5), (1, 0, 0.5), 0.17))

        return [(n, {"sol": sol, "chicle": chicle, "lima": lima, "lavanda": lavanda}[n]) for n in REPARTO]

    def main():
        preparar()
        hacer = [a for a in ARGS if not a.startswith("--")] or ["icono", "alt", "portada"]
        if "icono" in hacer:
            icono_grito()
        if "alt" in hacer:
            icono_alt()
        if "portada" in hacer and "portada" in globals():
            globals()["portada"]()
        if "--sin-componer" not in ARGS:
            import subprocess
            subprocess.run(["python", "-I", os.path.abspath(__file__)], check=True)


# ------------------------------------------------------------------------------------------------ PIL
def componer():
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

    def cargar(n):
        return Image.open(os.path.join(CAPAS, n + ".png")).convert("RGBA")

    def contorno(im, grosor, color=TINTA):
        a = im.split()[3]
        g = a.filter(ImageFilter.GaussianBlur(grosor * 0.5)).point(lambda v: 255 if v > 6 else int(v * 42))
        g = g.filter(ImageFilter.MaxFilter(3 if grosor < 8 else 5))
        g = g.filter(ImageFilter.GaussianBlur(grosor * 0.5)).point(lambda v: 255 if v > 100 else int(v * 2.55))
        fondo = Image.new("RGBA", im.size, (*color, 255))
        fondo.putalpha(g)
        fondo.alpha_composite(im)
        return fondo

    def saturar(im, k):
        a = im.split()[3]
        rgb = ImageEnhance.Color(im.convert("RGB")).enhance(k)
        rgb.putalpha(a)
        return rgb

    def rayos(tam, centro, c1, c2, n=18, giro=0.0):
        im = Image.new("RGBA", tam, (*c1, 255))
        d = ImageDraw.Draw(im)
        R = max(tam) * 2
        for i in range(n):
            a0 = giro + 2 * math.pi * i / n
            a1 = a0 + math.pi / n
            d.polygon([centro, (centro[0] + R * math.cos(a0), centro[1] + R * math.sin(a0)), (centro[0] + R * math.cos(a1), centro[1] + R * math.sin(a1))], fill=(*c2, 255))
        return im

    def radial(tam, centro, r, c_in, c_out, fuerza=1.0):
        w, h = tam
        m = Image.new("L", tam)
        px = m.load()
        for y in range(h):
            for x in range(w):
                t = min(1.0, math.hypot(x - centro[0], y - centro[1]) / r)
                px[x, y] = int(255 * fuerza * (1 - t * t * (3 - 2 * t)))
        a = Image.new("RGBA", tam, (*c_out, 0))
        b = Image.new("RGBA", tam, (*c_in, 255))
        b.putalpha(m)
        a.alpha_composite(b)
        return a

    def tenir(im, color):
        """Como ImageColor3 de Roblox: multiplica el color de la imagen por el tinte."""
        r, g, b, a = im.split()
        r, g, b = (c.point(lambda v, t=t: v * t // 255) for c, t in zip((r, g, b), color))
        return Image.merge("RGBA", (r, g, b, a))

    def pegar(lienzo, im, centro, ancho, giro=0.0):
        im = im.resize((round(ancho), round(im.height * ancho / im.width)), Image.LANCZOS)
        if giro:
            im = im.rotate(giro, Image.BICUBIC, expand=True)
        lienzo.alpha_composite(im, (round(centro[0] - im.width / 2), round(centro[1] - im.height / 2)))

    def icono_final(base, salida, fuera, mancha, borde):
        per = cargar(base + "_personaje")
        fon = cargar(base + "_fondo")
        W = per.width
        k = W / 1024
        centro = (W * 0.55, W * 0.5)
        cielo = rayos(per.size, centro, *fuera, 20, 0.05)
        vi = radial(per.size, (W * 0.5, W * 0.5), W * 0.98, (0, 0, 0), (0, 0, 0), 1.0)
        osc = Image.new("RGBA", per.size, (*borde, 255))
        osc.putalpha(vi.split()[3].point(lambda v: int((255 - v) * 0.6)))
        cielo.alpha_composite(osc)
        pegar(cielo, tenir(Image.open(os.path.join(ARTE, "intro", "Mancha.png")).convert("RGBA"), mancha), (W * 0.56, W * 0.47), W * 1.2, 12)
        cielo.alpha_composite(contorno(saturar(fon, 1.15), 5 * k))
        cielo.alpha_composite(contorno(saturar(per, 1.12), 16 * k))
        cielo = cielo.convert("RGB").resize((512, 512), Image.LANCZOS)
        cielo.save(os.path.join(AQUI, salida + ".png"))
        cielo.resize((64, 64), Image.LANCZOS).save(os.path.join(CAPAS, salida + "_64.png"))
        print("FINAL", salida)

    def degradado(tam, arriba, abajo):
        w, h = tam
        col = Image.new("RGB", (1, h))
        for y in range(h):
            t = y / (h - 1)
            col.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(arriba, abajo)))
        return col.resize(tam).convert("RGBA")

    def portada_final():
        W, H = 1920, 1080
        fon = cargar("portada_fondo")
        k = fon.width / W
        cielo = degradado(fon.size, (38, 132, 230), (150, 220, 255))
        rz = rayos(fon.size, (fon.width * 0.5, fon.height * 0.2), (0, 0, 0), (255, 255, 255), 28, 0.03)
        rz.putalpha(rz.convert("L").point(lambda v: 26 if v > 128 else 0))
        cielo.alpha_composite(rz)
        cielo.alpha_composite(contorno(saturar(fon, 1.1), 3 * k))
        for nombre in ("lavanda", "chicle", "lima", "sol"):
            cielo.alpha_composite(contorno(saturar(cargar("portada_" + nombre), 1.1), 7 * k))
        sin = cielo.convert("RGB").resize((W, H), Image.LANCZOS)
        sin.save(os.path.join(AQUI, "Portada_sin_logo.png"))
        print("FINAL Portada_sin_logo")
        con = sin.convert("RGBA")
        con.alpha_composite(logo(W * 0.5, 12, 0.62))
        con.convert("RGB").save(os.path.join(AQUI, "Portada.png"))
        print("FINAL Portada")

    def fuente(nombre):
        import glob
        from PIL import ImageFont
        patron = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Roblox", "Versions", "*", "content", "fonts", nombre)
        return sorted(glob.glob(patron))[-1]

    def logo(cx, arriba, esc, lema="THE WORLD'S WORST AIRLINE"):
        """El logo de la intro (Intro.luau, construirLogo, en su estado final) en un lienzo de 1920x1080: marco de 1024x720
        escalado por esc, con su borde de arriba (y 10 del marco, la punta de la mancha) en la altura arriba."""
        from PIL import ImageFont
        lienzo = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
        x0, y0 = cx - 512 * esc, arriba - 10 * esc

        def img(n):
            return Image.open(os.path.join(ARTE, "intro", n + ".png")).convert("RGBA")

        def poner(im, x, y, w, h, ancla=(0.5, 0.5), giro=0.0):
            im = im.resize((round(w * esc), round(h * esc)), Image.LANCZOS)
            px, py = x0 + (x - ancla[0] * w) * esc, y0 + (y - ancla[1] * h) * esc
            if giro:
                c = (px + im.width / 2, py + im.height / 2)
                im = im.rotate(giro, Image.BICUBIC, expand=True)
                px, py = c[0] - im.width / 2, c[1] - im.height / 2
            lienzo.alpha_composite(im, (round(px), round(py)))

        poner(tenir(img("Mancha"), TURQUESA), 300, 430, 440, 440, giro=25)
        poner(tenir(img("Mancha"), NARANJA), 540, 330, 640, 640, giro=-10)
        eti = img("Etiqueta")
        poner(eti, 905, 512, 100, 200, ancla=(0.5, 0.0), giro=-4)
        poner(img("LogoOver"), 470, 340, 1024, 320, ancla=(0.5, 1.0))
        poner(img("LogoBooked"), 512, 595, 1024, 320, ancla=(0.5, 1.0))
        poner(img("Avioneta"), 860, 92, 300, 150)
        poner(tenir(img("Cinta"), ROJO), 512, 640, 800, 150)
        # Lema dentro de la cinta (como Gui.texto con Gui.trazado: papel con borde de tinta).
        f = ImageFont.truetype(fuente("LuckiestGuy-Regular.ttf"), 10)
        caja_w, caja_h = 0.72 * 800 * esc, 0.42 * 150 * esc
        tam = 10
        while True:
            f2 = ImageFont.truetype(fuente("LuckiestGuy-Regular.ttf"), tam + 1)
            bb = f2.getbbox(lema)
            if bb[2] - bb[0] > caja_w or bb[3] - bb[1] > caja_h:
                break
            tam, f = tam + 1, f2
        bb = f.getbbox(lema)
        cx_t, cy_t = x0 + 512 * esc, y0 + (640 - 75 + 0.2 * 150 + 0.21 * 150) * esc
        borde = max(2, round(tam * 0.09))
        d = ImageDraw.Draw(lienzo)
        d.text((cx_t - (bb[0] + bb[2]) / 2, cy_t - (bb[1] + bb[3]) / 2), lema, font=f, fill=(*PAPEL, 255), stroke_width=borde, stroke_fill=(*TINTA, 255))
        return lienzo

    if os.path.exists(os.path.join(CAPAS, "portada_sol.png")):
        portada_final()
    if os.path.exists(os.path.join(CAPAS, "icono_personaje.png")):
        icono_final("icono", "Icono", ((40, 150, 240), (72, 182, 255)), NARANJA, (16, 58, 150))
    if os.path.exists(os.path.join(CAPAS, "icono_alt_personaje.png")):
        icono_final("icono_alt", "Icono_alt", ((40, 150, 240), (72, 182, 255)), (255, 200, 60), (16, 58, 150))


if bpy is not None:
    main()
else:
    componer()
