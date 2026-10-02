// Rig R6 de Roblox y cómo convertir una pose "fácil de pensar" en los Transform de cada Motor6D.
//
// Convenciones (espacio del HumanoidRootPart, el personaje mira hacia -Z):
//   pitch > 0  -> el extremo del brazo/pierna va hacia delante
//   roll  > 0  -> el extremo va hacia +X (fuera para la derecha, hacia dentro para la izquierda)
//   lean  > 0  -> el torso se inclina hacia delante (pivotando en la cadera)
//   d = [x, y, z] -> desplazamiento SACANDO la pieza de su pivote (la clave de la animación)
//
// Las rotaciones de brazos, piernas y cabeza son absolutas (respecto al suelo), no respecto al
// torso: así "pitch 0" siempre es vertical y la cabeza se queda recta aunque el torso se incline.
(function (root) {
  const CF = typeof module !== 'undefined' && module.exports ? require('./cframe') : root.CF;
  const { cf12, mul, inv, point, rx, ry, rz, tr } = CF;

  const GROUND = -3; // el suelo está 3 studs por debajo del centro del HumanoidRootPart

  const JOINTS = {
    Torso: {
      parent: 'HumanoidRootPart', motor: 'RootJoint',
      C0: cf12(0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0),
      C1: cf12(0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0),
    },
    Head: {
      parent: 'Torso', motor: 'Neck',
      C0: cf12(0, 1, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0),
      C1: cf12(0, -0.5, 0, -1, 0, 0, 0, 0, 1, 0, 1, 0),
    },
    'Right Arm': {
      parent: 'Torso', motor: 'Right Shoulder',
      C0: cf12(1, 0.5, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0),
      C1: cf12(-0.5, 0.5, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0),
    },
    'Left Arm': {
      parent: 'Torso', motor: 'Left Shoulder',
      C0: cf12(-1, 0.5, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0),
      C1: cf12(0.5, 0.5, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0),
    },
    'Right Leg': {
      parent: 'Torso', motor: 'Right Hip',
      C0: cf12(1, -1, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0),
      C1: cf12(0.5, 1, 0, 0, 0, 1, 0, 1, 0, -1, 0, 0),
    },
    'Left Leg': {
      parent: 'Torso', motor: 'Left Hip',
      C0: cf12(-1, -1, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0),
      C1: cf12(-0.5, 1, 0, 0, 0, -1, 0, 1, 0, 1, 0, 0),
    },
  };

  const SIZES = {
    Torso: [2, 2, 1],
    Head: [1.25, 1.25, 1.25], // la cabeza R6 es 2x1x1 con malla; visualmente es un bloque redondeado
    'Right Arm': [1, 2, 1],
    'Left Arm': [1, 2, 1],
    'Right Leg': [1, 2, 1],
    'Left Leg': [1, 2, 1],
  };

  const LIMBS = ['Right Arm', 'Left Arm', 'Right Leg', 'Left Leg'];
  const PARTS = ['Torso', 'Head', ...LIMBS];

  function boxCorners(part, size) {
    const out = [];
    for (const sx of [-0.5, 0.5]) for (const sy of [-0.5, 0.5]) for (const sz of [-0.5, 0.5])
      out.push(point(part, [sx * size[0], sy * size[1], sz * size[2]]));
    return out;
  }

  // spec -> CFrame de cada pieza en el espacio del HumanoidRootPart
  function buildParts(spec) {
    const t = Object.assign({ x: 0, y: 0, z: 0, lean: 0, yaw: 0, roll: 0 }, spec.torso);
    const torso = [tr(t.x, t.y, t.z), tr(0, -1, 0), ry(t.yaw), rx(-t.lean), rz(t.roll), tr(0, 1, 0)].reduce(mul);
    const parts = { Torso: torso };

    for (const name of ['Head', ...LIMBS]) {
      const s = Object.assign({ pitch: 0, roll: 0, yaw: 0, d: [0, 0, 0] }, spec[name]);
      const j = JOINTS[name];
      const pivot = point(torso, j.C0.p);
      const q = j.C1.p;
      const R = name === 'Head'
        ? [ry(s.yaw), rx(s.pitch), rz(s.roll)].reduce(mul)
        : [ry(s.yaw), rz(s.roll), rx(s.pitch)].reduce(mul);
      const d = s.d.slice();
      let part = [tr(pivot[0] + d[0], pivot[1] + d[1], pivot[2] + d[2]), R, tr(-q[0], -q[1], -q[2])].reduce(mul);
      if (s.plant) {
        // Ajusta la altura para que el punto más bajo de la pierna toque el suelo justo
        const minY = Math.min(...boxCorners(part, SIZES[name]).map((c) => c[1]));
        part = mul(tr(0, GROUND - minY, 0), part);
      }
      parts[name] = part;
    }
    return parts;
  }

  // CFrame de pieza -> Transform del Motor6D (lo que guarda cada Pose del KeyframeSequence)
  function partsToTransforms(parts) {
    const hrp = CF.cf();
    const out = {};
    for (const name of PARTS) {
      const j = JOINTS[name];
      const parent = j.parent === 'HumanoidRootPart' ? hrp : parts[j.parent];
      const rel = mul(inv(parent), parts[name]);
      out[name] = mul(mul(inv(j.C0), rel), j.C1);
    }
    return out;
  }

  // Transforms -> CFrame de cada pieza (lo que hace Roblox al reproducir)
  function transformsToParts(T) {
    const parts = {};
    const hrp = CF.cf();
    for (const name of PARTS) {
      const j = JOINTS[name];
      const parent = j.parent === 'HumanoidRootPart' ? hrp : parts[j.parent];
      parts[name] = mul(mul(mul(parent, j.C0), T[name]), inv(j.C1));
    }
    return parts;
  }

  const SWAP = { 'Right Arm': 'Left Arm', 'Left Arm': 'Right Arm', 'Right Leg': 'Left Leg', 'Left Leg': 'Right Leg' };

  // Pose en espejo (izquierda <-> derecha): para la segunda mitad del ciclo
  function mirror(spec) {
    const out = {};
    for (const [k, v] of Object.entries(spec)) {
      const nk = SWAP[k] || k;
      const nv = Object.assign({}, v);
      if ('yaw' in nv) nv.yaw = -nv.yaw;
      if ('roll' in nv) nv.roll = -nv.roll;
      if ('x' in nv) nv.x = -nv.x;
      if (nv.d) nv.d = [-nv.d[0], nv.d[1], nv.d[2]];
      out[nk] = nv;
    }
    return out;
  }

  const api = { JOINTS, SIZES, PARTS, LIMBS, GROUND, buildParts, partsToTransforms, transformsToParts, mirror, boxCorners };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.R6 = api;
})(typeof window !== 'undefined' ? window : globalThis);
