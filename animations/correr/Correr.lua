--[[
  Correr (R6) - generado por tools/anim/build.js desde correr.pose.js.
  No lo edites a mano: cambia el .pose.js y vuelve a generarlo.

  Cómo usarlo:
   1. Selecciona tu rig R6 en el Explorer (el Model con Humanoid, HumanoidRootPart y Torso).
   2. Pega TODO este código en la Command Bar (pestaña View > Command Bar) y pulsa Enter.
   3. Abre el Animation Editor con ese rig y carga "Correr" desde el menú "...".
]]

local Selection = game:GetService("Selection")
local ServerStorage = game:GetService("ServerStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local NAME = "Correr"
local FPS = 30

local rig = Selection:Get()[1]
if not (rig and rig:IsA("Model")) then
	error("Selecciona el Model de tu rig R6 en el Explorer y vuelve a ejecutar")
end
local hrp = rig:FindFirstChild("HumanoidRootPart")
local torso = rig:FindFirstChild("Torso")
if not (hrp and torso) then
	error("Este rig no es R6: necesita HumanoidRootPart y Torso")
end

-- Se leen los Motor6D reales del rig, así la animación respeta sus pivotes
local motors = {
	["Torso"] = hrp:FindFirstChild("RootJoint"),
	["Head"] = torso:FindFirstChild("Neck"),
	["Right Arm"] = torso:FindFirstChild("Right Shoulder"),
	["Left Arm"] = torso:FindFirstChild("Left Shoulder"),
	["Right Leg"] = torso:FindFirstChild("Right Hip"),
	["Left Leg"] = torso:FindFirstChild("Left Hip"),
}
for name, motor in motors do
	if not (motor and motor:IsA("Motor6D")) then
		error("Falta el Motor6D de " .. name .. " (¿es un rig R6 estándar?)")
	end
end

-- Posición de cada pieza respecto a su padre en cada key (calculada en build.js)
local KEYS = {
	{ -- Contacto (pie derecho delante)
		frame = 0,
		easing = "Cubic",
		rel = {
			["Torso"] = CFrame.new(0.03359, -0.18874, -0.27358, 0.99255, 0.03359, -0.11715, 0, 0.96126, 0.27564, 0.12187, -0.27358, 0.9541),
			["Head"] = CFrame.new(-0.00822, 1.49879, 0.07338, 0.99255, -0.00425, 0.1218, 0.03359, 0.97022, -0.23987, -0.11715, 0.24217, 0.96313),
			["Right Arm"] = CFrame.new(1.80434, 0.34522, 0.80621, 0.97086, -0.21819, -0.09914, 0.23272, 0.75941, 0.60757, -0.05728, -0.61294, 0.78805),
			["Left Arm"] = CFrame.new(-1.32231, 0.68969, -0.94361, 0.94397, -0.03639, 0.32803, 0.32899, 0.18276, -0.92648, -0.02624, 0.98248, 0.1845),
			["Right Leg"] = CFrame.new(0.38604, -1.47755, -1.07063, 0.99255, 0.07503, 0.09603, 0.03359, 0.58905, -0.8074, -0.11715, 0.80461, 0.58214),
			["Left Leg"] = CFrame.new(-0.37953, -1.83219, 0.75028, 0.99255, -0.08155, 0.09057, 0.03359, 0.89742, 0.4399, -0.11715, -0.43358, 0.89347),
		},
	},
	{ -- Bajada (amortigua)
		frame = 2,
		easing = "Linear",
		rel = {
			["Torso"] = CFrame.new(0.02981, -0.46031, -0.34072, 0.99619, 0.02981, -0.0819, 0, 0.93969, 0.34202, 0.08716, -0.34072, 0.93612),
			["Head"] = CFrame.new(-0.0074, 1.45064, 0.07404, 0.99619, -0.00608, 0.08694, 0.02981, 0.96117, -0.27434, -0.0819, 0.27589, 0.95769),
			["Right Arm"] = CFrame.new(1.73694, 0.2102, 0.6715, 0.98106, -0.18052, -0.07024, 0.19253, 0.86896, 0.45589, -0.02126, -0.46077, 0.88726),
			["Left Arm"] = CFrame.new(-1.33752, 0.60838, -0.84195, 0.9666, -0.07115, 0.2462, 0.25626, 0.25604, -0.93208, 0.00328, 0.96404, 0.26573),
			["Right Leg"] = CFrame.new(0.47507, -1.39666, -0.42442, 0.99619, 0.01812, 0.08525, 0.02981, 0.84832, -0.52865, -0.0819, 0.52918, 0.84455),
			["Left Leg"] = CFrame.new(-0.43218, -1.74258, 0.53145, 0.99619, -0.04358, 0.07548, 0.02981, 0.98416, 0.17478, -0.0819, -0.17186, 0.98171),
		},
	},
	{ -- Paso (todo vuelve al pivote)
		frame = 4,
		easing = "Linear",
		rel = {
			["Torso"] = CFrame.new(0, -0.0937, -0.29237, 1, 0, 0, 0, 0.9563, 0.29237, 0, -0.29237, 0.9563),
			["Head"] = CFrame.new(0, 1.47815, 0.14619, 1, 0, 0, 0, 0.9563, -0.29237, 0, 0.29237, 0.9563),
			["Right Arm"] = CFrame.new(1.53358, 0.09515, -0.0873, 0.99756, -0.06959, -0.00487, 0.06671, 0.97205, -0.22511, 0.02039, 0.22424, 0.97432),
			["Left Arm"] = CFrame.new(-1.46399, 0.04883, -0.17441, 0.99756, -0.06959, 0.00487, 0.06671, 0.93126, -0.35821, 0.02039, 0.35766, 0.93363),
			["Right Leg"] = CFrame.new(0.5, -1.89076, -0.05492, 1, 0, 0, 0, 0.99619, -0.08716, 0, 0.08716, 0.99619),
			["Left Leg"] = CFrame.new(-0.5, -1.09231, -0.57472, 1, 0, 0, 0, 0.74314, -0.66913, 0, 0.66913, 0.74314),
		},
	},
	{ -- Impulso (en el aire)
		frame = 6,
		easing = "Cubic",
		rel = {
			["Torso"] = CFrame.new(-0.02256, 0.16593, -0.25783, 0.99619, -0.02256, 0.08419, 0, 0.96593, 0.25882, -0.08716, -0.25783, 0.96225),
			["Head"] = CFrame.new(-0.00152, 1.47817, 0.14612, 0.99619, -0.00304, -0.0871, -0.02256, 0.95634, -0.29139, 0.08419, 0.29224, 0.95263),
			["Right Arm"] = CFrame.new(1.28863, 0.67595, -0.95708, 0.94744, 0.06757, -0.31272, -0.31994, 0.20035, -0.92601, 0.00009, 0.97739, 0.21144),
			["Left Arm"] = CFrame.new(-1.77532, 0.35217, 0.83543, 0.97443, 0.19019, 0.11967, -0.22289, 0.75044, 0.62222, 0.02853, -0.63298, 0.77364),
			["Right Leg"] = CFrame.new(0.41538, -1.93634, 0.72789, 0.99619, 0.05602, -0.06677, -0.02256, 0.90567, 0.42337, 0.08419, -0.42026, 0.90349),
			["Left Leg"] = CFrame.new(-0.40872, -1.21196, -1.11431, 0.99619, -0.05832, -0.06477, -0.02256, 0.5453, -0.83794, 0.08419, 0.83621, 0.54191),
		},
	},
	{ -- Contacto (pie izquierdo delante)
		frame = 10,
		easing = "Cubic",
		rel = {
			["Torso"] = CFrame.new(-0.03359, -0.18874, -0.27358, 0.99255, -0.03359, 0.11715, 0, 0.96126, 0.27564, -0.12187, -0.27358, 0.9541),
			["Head"] = CFrame.new(0.00822, 1.49879, 0.07338, 0.99255, 0.00425, -0.1218, -0.03359, 0.97022, -0.23987, 0.11715, 0.24217, 0.96313),
			["Right Arm"] = CFrame.new(1.32231, 0.68969, -0.94361, 0.94397, 0.03639, -0.32803, -0.32899, 0.18276, -0.92648, 0.02624, 0.98248, 0.1845),
			["Left Arm"] = CFrame.new(-1.80434, 0.34522, 0.80621, 0.97086, 0.21819, 0.09914, -0.23272, 0.75941, 0.60757, 0.05728, -0.61294, 0.78805),
			["Right Leg"] = CFrame.new(0.37953, -1.83219, 0.75028, 0.99255, 0.08155, -0.09057, -0.03359, 0.89742, 0.4399, 0.11715, -0.43358, 0.89347),
			["Left Leg"] = CFrame.new(-0.38604, -1.47755, -1.07063, 0.99255, -0.07503, -0.09603, -0.03359, 0.58905, -0.8074, 0.11715, 0.80461, 0.58214),
		},
	},
	{ -- Bajada (amortigua)
		frame = 12,
		easing = "Linear",
		rel = {
			["Torso"] = CFrame.new(-0.02981, -0.46031, -0.34072, 0.99619, -0.02981, 0.0819, 0, 0.93969, 0.34202, -0.08716, -0.34072, 0.93612),
			["Head"] = CFrame.new(0.0074, 1.45064, 0.07404, 0.99619, 0.00608, -0.08694, -0.02981, 0.96117, -0.27434, 0.0819, 0.27589, 0.95769),
			["Right Arm"] = CFrame.new(1.33752, 0.60838, -0.84195, 0.9666, 0.07115, -0.2462, -0.25626, 0.25604, -0.93208, -0.00328, 0.96404, 0.26573),
			["Left Arm"] = CFrame.new(-1.73694, 0.2102, 0.6715, 0.98106, 0.18052, 0.07024, -0.19253, 0.86896, 0.45589, 0.02126, -0.46077, 0.88726),
			["Right Leg"] = CFrame.new(0.43218, -1.74258, 0.53145, 0.99619, 0.04358, -0.07548, -0.02981, 0.98416, 0.17478, 0.0819, -0.17186, 0.98171),
			["Left Leg"] = CFrame.new(-0.47507, -1.39666, -0.42442, 0.99619, -0.01812, -0.08525, -0.02981, 0.84832, -0.52865, 0.0819, 0.52918, 0.84455),
		},
	},
	{ -- Paso (todo vuelve al pivote)
		frame = 14,
		easing = "Linear",
		rel = {
			["Torso"] = CFrame.new(0, -0.0937, -0.29237, 1, 0, 0, 0, 0.9563, 0.29237, 0, -0.29237, 0.9563),
			["Head"] = CFrame.new(0, 1.47815, 0.14619, 1, 0, 0, 0, 0.9563, -0.29237, 0, 0.29237, 0.9563),
			["Right Arm"] = CFrame.new(1.46399, 0.04883, -0.17441, 0.99756, 0.06959, -0.00487, -0.06671, 0.93126, -0.35821, -0.02039, 0.35766, 0.93363),
			["Left Arm"] = CFrame.new(-1.53358, 0.09515, -0.0873, 0.99756, 0.06959, 0.00487, -0.06671, 0.97205, -0.22511, -0.02039, 0.22424, 0.97432),
			["Right Leg"] = CFrame.new(0.5, -1.09231, -0.57472, 1, 0, 0, 0, 0.74314, -0.66913, 0, 0.66913, 0.74314),
			["Left Leg"] = CFrame.new(-0.5, -1.89076, -0.05492, 1, 0, 0, 0, 0.99619, -0.08716, 0, 0.08716, 0.99619),
		},
	},
	{ -- Impulso (en el aire)
		frame = 16,
		easing = "Cubic",
		rel = {
			["Torso"] = CFrame.new(0.02256, 0.16593, -0.25783, 0.99619, 0.02256, -0.08419, 0, 0.96593, 0.25882, 0.08716, -0.25783, 0.96225),
			["Head"] = CFrame.new(0.00152, 1.47817, 0.14612, 0.99619, 0.00304, 0.0871, 0.02256, 0.95634, -0.29139, -0.08419, 0.29224, 0.95263),
			["Right Arm"] = CFrame.new(1.77532, 0.35217, 0.83543, 0.97443, -0.19019, -0.11967, 0.22289, 0.75044, 0.62222, -0.02853, -0.63298, 0.77364),
			["Left Arm"] = CFrame.new(-1.28863, 0.67595, -0.95708, 0.94744, -0.06757, 0.31272, 0.31994, 0.20035, -0.92601, -0.00009, 0.97739, 0.21144),
			["Right Leg"] = CFrame.new(0.40872, -1.21196, -1.11431, 0.99619, 0.05832, 0.06477, 0.02256, 0.5453, -0.83794, -0.08419, 0.83621, 0.54191),
			["Left Leg"] = CFrame.new(-0.41538, -1.93634, 0.72789, 0.99619, -0.05602, 0.06677, 0.02256, 0.90567, 0.42337, -0.08419, -0.42026, 0.90349),
		},
	},
	{ -- Igual que el frame 0 (cierra el bucle)
		frame = 20,
		easing = "Cubic",
		rel = {
			["Torso"] = CFrame.new(0.03359, -0.18874, -0.27358, 0.99255, 0.03359, -0.11715, 0, 0.96126, 0.27564, 0.12187, -0.27358, 0.9541),
			["Head"] = CFrame.new(-0.00822, 1.49879, 0.07338, 0.99255, -0.00425, 0.1218, 0.03359, 0.97022, -0.23987, -0.11715, 0.24217, 0.96313),
			["Right Arm"] = CFrame.new(1.80434, 0.34522, 0.80621, 0.97086, -0.21819, -0.09914, 0.23272, 0.75941, 0.60757, -0.05728, -0.61294, 0.78805),
			["Left Arm"] = CFrame.new(-1.32231, 0.68969, -0.94361, 0.94397, -0.03639, 0.32803, 0.32899, 0.18276, -0.92648, -0.02624, 0.98248, 0.1845),
			["Right Leg"] = CFrame.new(0.38604, -1.47755, -1.07063, 0.99255, 0.07503, 0.09603, 0.03359, 0.58905, -0.8074, -0.11715, 0.80461, 0.58214),
			["Left Leg"] = CFrame.new(-0.37953, -1.83219, 0.75028, 0.99255, -0.08155, 0.09057, 0.03359, 0.89742, 0.4399, -0.11715, -0.43358, 0.89347),
		},
	},
}

local LIMBS = { "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg" }

local ks = Instance.new("KeyframeSequence")
ks.Name = NAME
ks.Loop = true
ks.Priority = Enum.AnimationPriority.Movement

for _, key in KEYS do
	local style = if key.easing == "Linear" then Enum.PoseEasingStyle.Linear else Enum.PoseEasingStyle.Cubic
	local function newPose(name, cf)
		local pose = Instance.new("Pose")
		pose.Name = name
		pose.CFrame = cf
		pose.Weight = 1
		pose.EasingStyle = style
		-- InOut es simétrico, así no nos afecta que Roblox tenga In y Out al revés en las animaciones
		pose.EasingDirection = Enum.PoseEasingDirection.InOut
		return pose
	end
	local function transform(name)
		local motor = motors[name]
		return motor.C0:Inverse() * key.rel[name] * motor.C1
	end

	local keyframe = Instance.new("Keyframe")
	keyframe.Time = key.frame / FPS
	local rootPose = newPose("HumanoidRootPart", CFrame.identity)
	rootPose.Parent = keyframe
	local torsoPose = newPose("Torso", transform("Torso"))
	torsoPose.Parent = rootPose
	for _, name in LIMBS do
		newPose(name, transform(name)).Parent = torsoPose
	end
	keyframe.Parent = ks
end

-- Guardarlo donde lo busca el Animation Editor (rig.AnimSaves apunta a ServerStorage.RBX_ANIMSAVES)
local saves = rig:FindFirstChild("AnimSaves")
local folder = nil
if saves and saves:IsA("ObjectValue") then
	folder = saves.Value
elseif saves then
	folder = saves -- formato antiguo: la carpeta está dentro del rig
end

if folder then
	local old = folder:FindFirstChild(NAME)
	if old then
		old:Destroy()
	end
	ks.Parent = folder
	print(("✅ '%s' creada en %s. Ábrela con el Animation Editor (... > Load)."):format(NAME, folder:GetFullName()))
else
	local old = ServerStorage:FindFirstChild(NAME)
	if old then
		old:Destroy()
	end
	ks.Parent = ServerStorage
	print(("✅ '%s' creada en ServerStorage."):format(NAME))
	print("   Este rig aún no tiene animaciones guardadas, así que el Animation Editor no la verá todavía.")
	print("   Opción A: abre el Animation Editor con el rig, guarda una animación vacía y vuelve a ejecutar este script.")
	print("   Opción B: clic derecho en ServerStorage > Correr > 'Save to Roblox' para publicarla directamente.")
end
Selection:Set({ ks })
ChangeHistoryService:SetWaypoint("Crear animación " .. NAME)
