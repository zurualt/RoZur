// Animación de CORRER para R6 (versión 1).
//
// Ideas que sigue:
//  - Las extremidades salen de su pivote (d = desplazamiento) en las poses extremas.
//  - Los extremos se mantienen un par de frames y luego pasan por el pivote muy rápido
//    (el "passing" dura 1-2 frames), así no se nota que se separan del cuerpo.
//  - Torso inclinado hacia delante y cabeza recta (la cabeza compensa la inclinación).
//
// 30 fps. Ciclo de 20 frames (0.67 s): dos pasos de 10 frames.
// Solo se escribe la mitad del ciclo; la otra mitad es la misma en espejo.

const HALF = 10;

// easing: easing que va DESDE esta key hasta la siguiente ("Cubic" = Cubic InOut, o "Linear")
const half = [
  {
    frame: 0, nombre: 'Contacto (pie derecho delante)', easing: 'Cubic',
    pose: {
      torso: { y: -0.15, lean: 16, yaw: -7 },
      Head: { pitch: -2, d: [0, 0, -0.05] },
      'Right Leg': { pitch: 38, d: [0, 0, -0.35], plant: true },
      'Left Leg': { pitch: -42, d: [0, 0.15, 0.35] },
      'Left Arm': { pitch: 62, roll: 18, d: [0.2, 0.3, -0.55] },
      'Right Arm': { pitch: -55, roll: 12, d: [0.15, 0.25, 0.5] },
    },
  },
  {
    frame: 2, nombre: 'Bajada (amortigua)', easing: 'Linear',
    pose: {
      torso: { y: -0.4, lean: 20, yaw: -5 },
      Head: { pitch: -4, d: [0, -0.05, -0.05] },
      'Right Leg': { pitch: 12, d: [0, 0, -0.1], plant: true },
      'Left Leg': { pitch: -30, d: [0, 0.35, 0.3] },
      'Left Arm': { pitch: 54, roll: 14, d: [0.15, 0.22, -0.45] },
      'Right Arm': { pitch: -48, roll: 10, d: [0.12, 0.2, 0.42] },
    },
  },
  {
    frame: 4, nombre: 'Paso (todo vuelve al pivote)', easing: 'Linear',
    pose: {
      torso: { y: -0.05, lean: 17, yaw: 0 },
      Head: { pitch: 0 },
      'Right Leg': { pitch: -12, plant: true },
      'Left Leg': { pitch: 25, d: [0, 0.65, -0.1] },
      'Left Arm': { pitch: 4, roll: 4, d: [0, 0.05, 0] },
      'Right Arm': { pitch: -4, roll: 4, d: [0, 0.05, 0] },
    },
  },
  {
    frame: 6, nombre: 'Impulso (en el aire)', easing: 'Cubic',
    pose: {
      torso: { y: 0.2, lean: 15, yaw: 5 },
      Head: { pitch: 2 },
      'Right Leg': { pitch: -40, d: [0, 0.05, 0.35] },
      'Left Leg': { pitch: 42, d: [0, 0.25, -0.4] },
      'Left Arm': { pitch: -55, roll: -12, d: [-0.15, 0.25, 0.5] },
      'Right Arm': { pitch: 62, roll: -18, d: [-0.2, 0.3, -0.55] },
    },
  },
];

module.exports = {
  nombre: 'Correr',
  fps: 30,
  duracionFrames: HALF * 2,
  loop: true,
  prioridad: 'Movement',
  half,
  HALF,
};
