// Genera, a partir de un archivo *.pose.js:
//   - <Nombre>.lua      -> script para la Command Bar de Studio que crea el KeyframeSequence
//   - preview.html      -> vista previa interactiva (sin Studio)
//
// Uso: node tools/anim/build.js animations/correr/correr.pose.js
const fs = require('fs');
const path = require('path');
const CF = require('./cframe');
const R6 = require('./r6');

const posePath = path.resolve(process.argv[2] || 'animations/correr/correr.pose.js');
const anim = require(posePath);
const outDir = path.dirname(posePath);

function mirrorName(n) {
  return n.replace(/derech|izquierd/g, (m) => (m === 'derech' ? 'izquierd' : 'derech'));
}

function expandKeys() {
  const keys = anim.half.map((k) => ({ frame: k.frame, nombre: k.nombre, easing: k.easing, pose: k.pose }));
  for (const k of anim.half)
    keys.push({ frame: k.frame + anim.HALF, nombre: mirrorName(k.nombre), easing: k.easing, pose: R6.mirror(k.pose) });
  const first = anim.half[0];
  keys.push({ frame: anim.duracionFrames, nombre: 'Igual que el frame 0 (cierra el bucle)', easing: first.easing, pose: first.pose });
  return keys.sort((a, b) => a.frame - b.frame);
}

const keys = expandKeys().map((k) => {
  const parts = R6.buildParts(k.pose);
  const T = R6.partsToTransforms(parts);
  const rel = {};
  for (const name of R6.PARTS) {
    const j = R6.JOINTS[name];
    const parent = j.parent === 'HumanoidRootPart' ? CF.cf() : parts[j.parent];
    rel[name] = CF.mul(CF.inv(parent), parts[name]);
  }
  return { ...k, T, rel };
});

// Comprobación: reconstruir las piezas desde los Transform tiene que dar lo mismo
for (const k of keys) {
  const back = R6.transformsToParts(k.T);
  const parts = R6.buildParts(k.pose);
  for (const name of R6.PARTS) {
    const err = Math.max(...back[name].p.map((v, i) => Math.abs(v - parts[name].p[i])), ...back[name].r.map((v, i) => Math.abs(v - parts[name].r[i])));
    if (err > 1e-6) throw new Error(`Error de reconstrucción en frame ${k.frame}, ${name}: ${err}`);
  }
}

const fmt = (v) => {
  const s = (Math.abs(v) < 5e-6 ? 0 : v).toFixed(5).replace(/\.?0+$/, '');
  return s === '-0' ? '0' : s;
};
const luaCF = (c) => `CFrame.new(${[...c.p, ...c.r].map(fmt).join(', ')})`;

function buildLua() {
  const L = [];
  L.push(`--[[`);
  L.push(`  ${anim.nombre} (R6) - generado por tools/anim/build.js desde ${path.basename(posePath)}.`);
  L.push(`  No lo edites a mano: cambia el .pose.js y vuelve a generarlo.`);
  L.push(``);
  L.push(`  Cómo usarlo:`);
  L.push(`   1. Selecciona tu rig R6 en el Explorer (el Model con Humanoid, HumanoidRootPart y Torso).`);
  L.push(`   2. Pega TODO este código en la Command Bar (pestaña View > Command Bar) y pulsa Enter.`);
  L.push(`   3. Abre el Animation Editor con ese rig y carga "${anim.nombre}" desde el menú "...".`);
  L.push(`]]`);
  L.push(``);
  L.push(`local Selection = game:GetService("Selection")`);
  L.push(`local ServerStorage = game:GetService("ServerStorage")`);
  L.push(`local ChangeHistoryService = game:GetService("ChangeHistoryService")`);
  L.push(``);
  L.push(`local NAME = "${anim.nombre}"`);
  L.push(`local FPS = ${anim.fps}`);
  L.push(``);
  L.push(`local rig = Selection:Get()[1]`);
  L.push(`if not (rig and rig:IsA("Model")) then`);
  L.push(`\terror("Selecciona el Model de tu rig R6 en el Explorer y vuelve a ejecutar")`);
  L.push(`end`);
  L.push(`local hrp = rig:FindFirstChild("HumanoidRootPart")`);
  L.push(`local torso = rig:FindFirstChild("Torso")`);
  L.push(`if not (hrp and torso) then`);
  L.push(`\terror("Este rig no es R6: necesita HumanoidRootPart y Torso")`);
  L.push(`end`);
  L.push(``);
  L.push(`-- Se leen los Motor6D reales del rig, así la animación respeta sus pivotes`);
  L.push(`local motors = {`);
  L.push(`\t["Torso"] = hrp:FindFirstChild("RootJoint"),`);
  for (const name of R6.PARTS.slice(1)) L.push(`\t["${name}"] = torso:FindFirstChild("${R6.JOINTS[name].motor}"),`);
  L.push(`}`);
  L.push(`for name, motor in motors do`);
  L.push(`\tif not (motor and motor:IsA("Motor6D")) then`);
  L.push(`\t\terror("Falta el Motor6D de " .. name .. " (¿es un rig R6 estándar?)")`);
  L.push(`\tend`);
  L.push(`end`);
  L.push(``);
  L.push(`-- Posición de cada pieza respecto a su padre en cada key (calculada en build.js)`);
  L.push(`local KEYS = {`);
  for (const k of keys) {
    L.push(`\t{ -- ${k.nombre}`);
    L.push(`\t\tframe = ${k.frame},`);
    L.push(`\t\teasing = "${k.easing}",`);
    L.push(`\t\trel = {`);
    for (const name of R6.PARTS) L.push(`\t\t\t["${name}"] = ${luaCF(k.rel[name])},`);
    L.push(`\t\t},`);
    L.push(`\t},`);
  }
  L.push(`}`);
  L.push(``);
  L.push(`local LIMBS = { "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg" }`);
  L.push(``);
  L.push(`local ks = Instance.new("KeyframeSequence")`);
  L.push(`ks.Name = NAME`);
  L.push(`ks.Loop = ${anim.loop ? 'true' : 'false'}`);
  L.push(`ks.Priority = Enum.AnimationPriority.${anim.prioridad}`);
  L.push(``);
  L.push(`for _, key in KEYS do`);
  L.push(`\tlocal style = if key.easing == "Linear" then Enum.PoseEasingStyle.Linear else Enum.PoseEasingStyle.Cubic`);
  L.push(`\tlocal function newPose(name, cf)`);
  L.push(`\t\tlocal pose = Instance.new("Pose")`);
  L.push(`\t\tpose.Name = name`);
  L.push(`\t\tpose.CFrame = cf`);
  L.push(`\t\tpose.Weight = 1`);
  L.push(`\t\tpose.EasingStyle = style`);
  L.push(`\t\t-- InOut es simétrico, así no nos afecta que Roblox tenga In y Out al revés en las animaciones`);
  L.push(`\t\tpose.EasingDirection = Enum.PoseEasingDirection.InOut`);
  L.push(`\t\treturn pose`);
  L.push(`\tend`);
  L.push(`\tlocal function transform(name)`);
  L.push(`\t\tlocal motor = motors[name]`);
  L.push(`\t\treturn motor.C0:Inverse() * key.rel[name] * motor.C1`);
  L.push(`\tend`);
  L.push(``);
  L.push(`\tlocal keyframe = Instance.new("Keyframe")`);
  L.push(`\tkeyframe.Time = key.frame / FPS`);
  L.push(`\tlocal rootPose = newPose("HumanoidRootPart", CFrame.identity)`);
  L.push(`\trootPose.Parent = keyframe`);
  L.push(`\tlocal torsoPose = newPose("Torso", transform("Torso"))`);
  L.push(`\ttorsoPose.Parent = rootPose`);
  L.push(`\tfor _, name in LIMBS do`);
  L.push(`\t\tnewPose(name, transform(name)).Parent = torsoPose`);
  L.push(`\tend`);
  L.push(`\tkeyframe.Parent = ks`);
  L.push(`end`);
  L.push(``);
  L.push(`-- Guardarlo donde lo busca el Animation Editor (rig.AnimSaves apunta a ServerStorage.RBX_ANIMSAVES)`);
  L.push(`local saves = rig:FindFirstChild("AnimSaves")`);
  L.push(`local folder = nil`);
  L.push(`if saves and saves:IsA("ObjectValue") then`);
  L.push(`\tfolder = saves.Value`);
  L.push(`elseif saves then`);
  L.push(`\tfolder = saves -- formato antiguo: la carpeta está dentro del rig`);
  L.push(`end`);
  L.push(``);
  L.push(`if folder then`);
  L.push(`\tlocal old = folder:FindFirstChild(NAME)`);
  L.push(`\tif old then`);
  L.push(`\t\told:Destroy()`);
  L.push(`\tend`);
  L.push(`\tks.Parent = folder`);
  L.push(`\tprint(("✅ '%s' creada en %s. Ábrela con el Animation Editor (... > Load)."):format(NAME, folder:GetFullName()))`);
  L.push(`else`);
  L.push(`\tlocal old = ServerStorage:FindFirstChild(NAME)`);
  L.push(`\tif old then`);
  L.push(`\t\told:Destroy()`);
  L.push(`\tend`);
  L.push(`\tks.Parent = ServerStorage`);
  L.push(`\tprint(("✅ '%s' creada en ServerStorage."):format(NAME))`);
  L.push(`\tprint("   Este rig aún no tiene animaciones guardadas, así que el Animation Editor no la verá todavía.")`);
  L.push(`\tprint("   Opción A: abre el Animation Editor con el rig, guarda una animación vacía y vuelve a ejecutar este script.")`);
  L.push(`\tprint("   Opción B: clic derecho en ServerStorage > ${anim.nombre} > 'Save to Roblox' para publicarla directamente.")`);
  L.push(`end`);
  L.push(`Selection:Set({ ks })`);
  L.push(`ChangeHistoryService:SetWaypoint("Crear animación " .. NAME)`);
  return L.join('\n') + '\n';
}

function buildPreview() {
  const tpl = fs.readFileSync(path.join(__dirname, 'preview.template.html'), 'utf8');
  const data = {
    nombre: anim.nombre,
    fps: anim.fps,
    duracionFrames: anim.duracionFrames,
    keys: keys.map((k) => ({ frame: k.frame, nombre: k.nombre, easing: k.easing, T: k.T })),
  };
  return tpl
    .replace('/*__CFRAME__*/', () => fs.readFileSync(path.join(__dirname, 'cframe.js'), 'utf8'))
    .replace('/*__R6__*/', () => fs.readFileSync(path.join(__dirname, 'r6.js'), 'utf8'))
    .replace('/*__DATA__*/', () => `window.ANIM = ${JSON.stringify(data)};`);
}

const luaPath = path.join(outDir, `${anim.nombre}.lua`);
fs.writeFileSync(luaPath, buildLua());
const htmlPath = path.join(outDir, 'preview.html');
fs.writeFileSync(htmlPath, buildPreview());
console.log(`OK: ${keys.length} keys -> ${path.relative(process.cwd(), luaPath)}, ${path.relative(process.cwd(), htmlPath)}`);
