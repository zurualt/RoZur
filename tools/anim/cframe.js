// Matemática mínima de CFrame (igual que en Roblox: posición + matriz 3x3 por filas).
// Sirve en Node (require) y en el navegador (window.CF).
(function (root) {
  function cf(x, y, z, r) {
    return { p: [x || 0, y || 0, z || 0], r: r || [1, 0, 0, 0, 1, 0, 0, 0, 1] };
  }

  // Igual que CFrame.new(x, y, z, R00, R01, R02, R10, R11, R12, R20, R21, R22)
  function cf12(x, y, z, a, b, c, d, e, f, g, h, i) {
    return cf(x, y, z, [a, b, c, d, e, f, g, h, i]);
  }

  function mulRot(A, B) {
    const o = new Array(9);
    for (let i = 0; i < 3; i++)
      for (let j = 0; j < 3; j++)
        o[i * 3 + j] = A[i * 3] * B[j] + A[i * 3 + 1] * B[3 + j] + A[i * 3 + 2] * B[6 + j];
    return o;
  }

  function rotVec(R, v) {
    return [
      R[0] * v[0] + R[1] * v[1] + R[2] * v[2],
      R[3] * v[0] + R[4] * v[1] + R[5] * v[2],
      R[6] * v[0] + R[7] * v[1] + R[8] * v[2],
    ];
  }

  function mul(A, B) {
    const pv = rotVec(A.r, B.p);
    return { p: [A.p[0] + pv[0], A.p[1] + pv[1], A.p[2] + pv[2]], r: mulRot(A.r, B.r) };
  }

  function inv(A) {
    const R = A.r;
    const T = [R[0], R[3], R[6], R[1], R[4], R[7], R[2], R[5], R[8]];
    const p = rotVec(T, A.p);
    return { p: [-p[0], -p[1], -p[2]], r: T };
  }

  function point(A, v) {
    const pv = rotVec(A.r, v);
    return [A.p[0] + pv[0], A.p[1] + pv[1], A.p[2] + pv[2]];
  }

  const rad = (d) => (d * Math.PI) / 180;

  function rx(deg) {
    const c = Math.cos(rad(deg)), s = Math.sin(rad(deg));
    return cf(0, 0, 0, [1, 0, 0, 0, c, -s, 0, s, c]);
  }
  function ry(deg) {
    const c = Math.cos(rad(deg)), s = Math.sin(rad(deg));
    return cf(0, 0, 0, [c, 0, s, 0, 1, 0, -s, 0, c]);
  }
  function rz(deg) {
    const c = Math.cos(rad(deg)), s = Math.sin(rad(deg));
    return cf(0, 0, 0, [c, -s, 0, s, c, 0, 0, 0, 1]);
  }
  function tr(x, y, z) {
    return cf(x, y, z);
  }

  function toQuat(R) {
    const [m00, m01, m02, m10, m11, m12, m20, m21, m22] = R;
    const t = m00 + m11 + m22;
    let w, x, y, z;
    if (t > 0) {
      const s = Math.sqrt(t + 1) * 2;
      w = 0.25 * s; x = (m21 - m12) / s; y = (m02 - m20) / s; z = (m10 - m01) / s;
    } else if (m00 > m11 && m00 > m22) {
      const s = Math.sqrt(1 + m00 - m11 - m22) * 2;
      w = (m21 - m12) / s; x = 0.25 * s; y = (m01 + m10) / s; z = (m02 + m20) / s;
    } else if (m11 > m22) {
      const s = Math.sqrt(1 + m11 - m00 - m22) * 2;
      w = (m02 - m20) / s; x = (m01 + m10) / s; y = 0.25 * s; z = (m12 + m21) / s;
    } else {
      const s = Math.sqrt(1 + m22 - m00 - m11) * 2;
      w = (m10 - m01) / s; x = (m02 + m20) / s; y = (m12 + m21) / s; z = 0.25 * s;
    }
    return [w, x, y, z];
  }

  function fromQuat(q) {
    let [w, x, y, z] = q;
    const n = Math.hypot(w, x, y, z);
    w /= n; x /= n; y /= n; z /= n;
    return [
      1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
      2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
      2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y),
    ];
  }

  // Igual que CFrame:Lerp: posición lineal y rotación esférica.
  function lerp(A, B, t) {
    const qa = toQuat(A.r);
    let qb = toQuat(B.r);
    let dot = qa[0] * qb[0] + qa[1] * qb[1] + qa[2] * qb[2] + qa[3] * qb[3];
    if (dot < 0) { qb = qb.map((v) => -v); dot = -dot; }
    let q;
    if (dot > 0.9995) {
      q = qa.map((v, i) => v + (qb[i] - v) * t);
    } else {
      const th = Math.acos(dot), s = Math.sin(th);
      const wa = Math.sin((1 - t) * th) / s, wb = Math.sin(t * th) / s;
      q = qa.map((v, i) => v * wa + qb[i] * wb);
    }
    return {
      p: A.p.map((v, i) => v + (B.p[i] - v) * t),
      r: fromQuat(q),
    };
  }

  const api = { cf, cf12, mul, inv, point, rotVec, rx, ry, rz, tr, lerp, toQuat, fromQuat };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.CF = api;
})(typeof window !== 'undefined' ? window : globalThis);
