--!strict
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Camara = require(script.Parent.Camara)

type Motor = { m: Motor6D, rot: CFrame, inv: CFrame }
type Juntas = {
	humanoide: Humanoid,
	raiz: BasePart,
	motores: { [string]: Motor },
	fase: number,
	mezcla: number,
	aire: number,
	aterrizaje: number,
	sentado: number,
	nado: number,
	tiempo: number,
	estabaEnAire: boolean,
}

local Movimiento = {}

local jugador = Players.LocalPlayer
local NOMBRES = {
	"Root",
	"Waist",
	"Neck",
	"LeftHip",
	"LeftKnee",
	"LeftAnkle",
	"RightHip",
	"RightKnee",
	"RightAnkle",
	"LeftShoulder",
	"LeftElbow",
	"RightShoulder",
	"RightElbow",
}
local ZANCADA = 3.6
local ALCANCE = 160
local rad = math.rad
local datos: { [Model]: Juntas } = setmetatable({}, { __mode = "k" }) :: any

local function preparar(personaje: Model): Juntas?
	local humanoide = personaje:FindFirstChildOfClass("Humanoid")
	local raiz = personaje:FindFirstChild("HumanoidRootPart")
	if not humanoide or not raiz or not raiz:IsA("BasePart") then
		return nil
	end
	local motores: { [string]: Motor } = {}
	for _, nombre in NOMBRES do
		local m = personaje:FindFirstChild(nombre, true)
		if m and m:IsA("Motor6D") then
			local rot = m.C0.Rotation
			motores[nombre] = { m = m, rot = rot, inv = rot:Inverse() }
		end
	end
	if not motores.LeftHip or not motores.RightHip then
		return nil
	end
	local j: Juntas = {
		humanoide = humanoide,
		raiz = raiz,
		motores = motores,
		fase = 0,
		mezcla = 0,
		aire = 0,
		aterrizaje = 0,
		sentado = 0,
		nado = 0,
		tiempo = math.random() * 10,
		estabaEnAire = false,
	}
	datos[personaje] = j
	return j
end

local function poner(j: Juntas, nombre: string, cf: CFrame)
	local d = j.motores[nombre]
	if d and d.m.Parent then
		d.m.Transform = d.inv * cf * d.rot
	end
end

local function suave(actual: number, objetivo: number, velocidad: number, dt: number): number
	return actual + (objetivo - actual) * (1 - math.exp(-dt * velocidad))
end

local function animar(personaje: Model, j: Juntas, dt: number)
	if personaje:GetAttribute("Ragdoll") or j.humanoide.Health <= 0 then
		return
	end
	local h = j.humanoide
	local velocidad = j.raiz.AssemblyLinearVelocity
	local plano = Vector3.new(velocidad.X, 0, velocidad.Z).Magnitude
	local estado = h:GetState()
	local sentado = h.Sit or estado == Enum.HumanoidStateType.Seated
	local enAire = estado == Enum.HumanoidStateType.Freefall or estado == Enum.HumanoidStateType.Jumping
	local nadando = estado == Enum.HumanoidStateType.Swimming
	j.mezcla = suave(j.mezcla, if sentado or enAire then 0 else math.clamp(plano / 14, 0, 1.3), 10, dt)
	j.aire = suave(j.aire, if enAire and not sentado then 1 else 0, 12, dt)
	j.sentado = suave(j.sentado, if sentado then 1 else 0, 14, dt)
	j.nado = suave(j.nado, if nadando then 1 else 0, 6, dt)
	if j.estabaEnAire and not enAire and not sentado then
		j.aterrizaje = 1
	end
	j.estabaEnAire = enAire
	j.aterrizaje = math.max(0, j.aterrizaje - dt * 5)
	if not sentado and not enAire then
		j.fase = (j.fase + plano * dt * (2 * math.pi / ZANCADA)) % (2 * math.pi)
	end
	j.tiempo += dt
	local f, a, se, n = j.mezcla, j.aire, j.sentado, j.nado
	local s, c = math.sin(j.fase), math.cos(j.fase)
	local quieto = math.max(0, 1 - f) * (1 - se)
	local respira = math.sin(j.tiempo * 2.2)
	local caida = j.aterrizaje * j.aterrizaje
	local libre = 1 - se

	local bote = (math.abs(s) * 0.24 * f + respira * 0.02 * quieto - caida * 0.22) * libre
	poner(j, "Root", CFrame.new(0, bote, 0) * CFrame.Angles((rad(-6) * f - rad(65) * n) * libre, s * rad(7) * f * libre, s * rad(9) * f * libre))
	poner(j, "Waist", CFrame.Angles(rad(-5) * f + respira * rad(1.5) * quieto + rad(10) * caida, -s * rad(12) * f, -s * rad(5) * f))
	poner(j, "Neck", CFrame.Angles(rad(5) * f + math.sin(j.fase * 2) * rad(4) * f + rad(35) * n - rad(8) * caida, s * rad(4) * f, s * rad(3) * f))

	for _, lado in { "Left", "Right" } do
		local signo = if lado == "Left" then 1 else -1
		local paso = signo * s * rad(46) * f
		local doblez = -(math.max(0, signo * c) * rad(55) + rad(8)) * f
		local caderaAire = if signo > 0 then rad(45) else rad(-15)
		local rodillaAire = if signo > 0 then rad(-70) else rad(-30)
		local cadera = (paso * (1 - a) + caderaAire * a) * libre + rad(90) * se
		local rodilla = (doblez * (1 - a) + rodillaAire * a) * libre - rad(90) * se
		cadera += rad(25) * caida + math.sin(j.tiempo * 8 + (if signo > 0 then 0 else math.pi)) * rad(25) * n
		rodilla -= rad(45) * caida
		poner(j, lado .. "Hip", CFrame.Angles(cadera, 0, 0))
		poner(j, lado .. "Knee", CFrame.Angles(rodilla, 0, 0))
		poner(j, lado .. "Ankle", CFrame.Angles((-paso * 0.25 - doblez * 0.35) * libre, 0, 0))
	end

	local sosteniendo = personaje:GetAttribute("Sosteniendo")
	local lleva = typeof(sosteniendo) == "string" and sosteniendo ~= ""
	local propio = personaje == jugador.Character and not Camara.esTerceraPersona()
	if lleva or propio then
		return
	end
	for _, lado in { "Left", "Right" } do
		local signo = if lado == "Left" then 1 else -1
		local balanceo = -signo * s * rad(45) * f
		local hombro = (balanceo + rad(5)) * (1 - a) + (rad(150) + math.sin(j.tiempo * 18 + signo) * rad(25)) * a
		hombro += (rad(100) + math.sin(j.tiempo * 5) * rad(50)) * n
		hombro = hombro * libre + rad(30) * se
		local abre = rad(12) + rad(6) * quieto + rad(30) * a
		poner(j, lado .. "Shoulder", CFrame.Angles(hombro, 0, if signo > 0 then -abre else abre))
		poner(j, lado .. "Elbow", CFrame.Angles(rad(20) + math.max(0, balanceo) * 0.7 + rad(30) * se, 0, 0))
	end
end

function Movimiento.iniciar()
	RunService.PreSimulation:Connect(function(dt)
		local foco = Workspace.CurrentCamera.CFrame.Position
		for _, otro in Players:GetPlayers() do
			local personaje = otro.Character
			local raiz = personaje and personaje.PrimaryPart
			if personaje and raiz and (raiz.Position - foco).Magnitude < ALCANCE then
				local j: Juntas? = datos[personaje]
				if not j or not j.humanoide.Parent then
					j = preparar(personaje)
				end
				if j then
					animar(personaje, j, math.min(dt, 0.1))
				end
			end
		end
	end)
end

return Movimiento
