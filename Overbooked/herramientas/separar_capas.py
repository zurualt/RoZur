import math

import bmesh
from mathutils import Vector

CELDA_CAPAS = 8.0
GROSOR_CAPA = 0.1
HUECO_CAPAS = 0.05


class Cara:
    __slots__ = ("vs", "n", "c", "area", "color", "inst", "orden")

    def __init__(self, vs, n, c, area, color, inst, orden=0):
        self.vs, self.n, self.c, self.area, self.color, self.inst, self.orden = vs, n, c, area, color, inst, orden


def base_plano(n):
    t = Vector((0, 1, 0)) if abs(n.y) < 0.9 else Vector((1, 0, 0))
    u = n.cross(t).normalized()
    return u, n.cross(u).normalized()


def area2d(pol):
    return sum(pol[i][0] * pol[(i + 1) % len(pol)][1] - pol[(i + 1) % len(pol)][0] * pol[i][1] for i in range(len(pol))) / 2


def recortar(sujeto, recorte):
    salida = sujeto
    sentido = area2d(recorte)
    for i in range(len(recorte)):
        a, b = recorte[i], recorte[(i + 1) % len(recorte)]
        entrada, salida = salida, []
        if not entrada:
            break

        def dentro(p):
            return ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) * sentido >= -1e-12

        for k in range(len(entrada)):
            p, q = entrada[k], entrada[(k + 1) % len(entrada)]
            dp, dq = dentro(p), dentro(q)
            if dp:
                salida.append(p)
            if dp != dq:
                ex, ey = q[0] - p[0], q[1] - p[1]
                fx, fy = b[0] - a[0], b[1] - a[1]
                den = ex * fy - ey * fx
                if abs(den) > 1e-15:
                    t = ((a[0] - p[0]) * fy - (a[1] - p[1]) * fx) / den
                    salida.append((p[0] + ex * t, p[1] + ey * t))
    return salida


def candidatos(caras, mismo):
    cubos = {}
    for idx, f in enumerate(caras):
        for g in (0.0, 0.5):
            clave_n = tuple(math.floor(x * 20 + g) for x in f.n)
            nb = Vector(tuple((k + 0.5 - g) / 20 for k in clave_n)).normalized()
            u, v = base_plano(nb)
            us = [p.dot(u) for p in f.vs]
            ws = [p.dot(v) for p in f.vs]
            for cu in range(math.floor(min(us) / CELDA_CAPAS), math.floor(max(us) / CELDA_CAPAS) + 1):
                for cv in range(math.floor(min(ws) / CELDA_CAPAS), math.floor(max(ws) / CELDA_CAPAS) + 1):
                    ancla = u * ((cu + 0.5) * CELDA_CAPAS) + v * ((cv + 0.5) * CELDA_CAPAS)
                    d = f.n.dot(f.c - ancla)
                    for h in (0.0, 0.5):
                        cubos.setdefault((g, clave_n, cu, cv, h, math.floor(d / GROSOR_CAPA + h)), []).append(idx)
    pares = set()
    for grupo in cubos.values():
        for a in range(len(grupo)):
            ia = grupo[a]
            for b in range(a + 1, len(grupo)):
                ib = grupo[b]
                if mismo != (caras[ia].inst == caras[ib].inst):
                    continue
                pares.add((ia, ib) if ia < ib else (ib, ia))
    return pares


def solape(fa, fb, hueco, area_min, cos_max):
    if fa.n.dot(fb.n) < cos_max:
        return None
    separacion = max(abs(fa.n.dot(p - fa.vs[0])) for p in fb.vs)
    if separacion > hueco:
        return None
    u, v = base_plano(fa.n)
    a2 = [(p.dot(u), p.dot(v)) for p in fa.vs]
    b2 = [(p.dot(u), p.dot(v)) for p in fb.vs]
    if max(x for x, _ in a2) <= min(x for x, _ in b2) or max(x for x, _ in b2) <= min(x for x, _ in a2):
        return None
    if max(y for _, y in a2) <= min(y for _, y in b2) or max(y for _, y in b2) <= min(y for _, y in a2):
        return None
    pol = recortar(b2, a2)
    if len(pol) < 3:
        return None
    area = abs(area2d(pol))
    if area < area_min:
        return None
    return fa.n.dot(fb.c - fa.vs[0]), separacion, area


def separar_capas(ob, hueco=HUECO_CAPAS, area_min=0.0025, angulo=2.0, pasadas=16):
    me = ob.data
    cos_max = math.cos(math.radians(angulo))
    total = 0
    for pasada in range(pasadas):
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.normal_update()
        uv = bm.loops.layers.uv.active
        zmin = min((v.co.z for v in bm.verts), default=0.0)
        caras, fuentes = [], []
        for f in bm.faces:
            area = f.calc_area()
            if area < 1e-5:
                continue
            pts = [v.co.copy() for v in f.verts]
            if f.normal.z < -0.95 and max(p.z for p in pts) < zmin + 0.02:
                continue
            col = None
            if uv:
                l = f.loops[0][uv].uv
                col = (round(l.x * 128), round(l.y * 128))
            caras.append(Cara(pts, f.normal.copy(), f.calc_center_median(), area, col, 0, f.index))
            fuentes.append(frozenset(v.index for v in f.verts))
        coords = [v.co.copy() for v in bm.verts]
        bm.free()
        medidas = [max((c[i] for c in coords), default=0.0) - min((c[i] for c in coords), default=0.0) for i in range(3)]
        fino = medidas.index(min(medidas))
        extremos = {}

        def extremo(n):
            clave = (round(n.x, 4), round(n.y, 4), round(n.z, 4))
            if clave not in extremos:
                extremos[clave] = max((n.dot(c) for c in coords), default=0.0)
            return extremos[clave]
        empuje = {}
        for ia, ib in candidatos(caras, True):
            fa, fb = caras[ia], caras[ib]
            if fa.color == fb.color or not fuentes[ia].isdisjoint(fuentes[ib]):
                continue
            r = solape(fa, fb, hueco - 1e-4, area_min, cos_max)
            if not r:
                continue
            s = r[0]
            frente = ia if fa.orden > fb.orden else ib
            detras = ib if frente == ia else ia
            falta = hueco - (s if frente == ib else -s) + 2e-4
            if falta <= 0:
                continue
            n = caras[frente].n
            eje = max(range(3), key=lambda i: abs(n[i]))
            seccion = medidas[(eje + 1) % 3] * medidas[(eje + 2) % 3]
            libre = abs(n[fino]) > 0.9 or (pasada >= pasadas // 2 and caras[frente].area < 0.25 * seccion)
            if not libre and n.dot(caras[frente].c) + falta > extremo(n) + 1e-3:
                clave = (detras, -1)
            else:
                clave = (frente, 1)
            empuje[clave] = max(empuje.get(clave, 0.0), falta)
        if not empuje:
            break
        mover = {}
        for (k, signo), d in empuje.items():
            n = caras[k].n * signo
            clave = (round(n.x, 3), round(n.y, 3), round(n.z, 3))
            for vi in fuentes[k]:
                por_normal = mover.setdefault(vi, {})
                if clave not in por_normal or por_normal[clave][1] < d:
                    por_normal[clave] = (n, d)
        for vi, por_normal in mover.items():
            co = me.vertices[vi].co
            for n, d in por_normal.values():
                co += n * d
            me.vertices[vi].co = co
        me.update()
        total += len(empuje)
    return total
