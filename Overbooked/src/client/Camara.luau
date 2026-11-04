--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)

local Camara = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local trauma = 0
local tiempo = 0
local paso = 0
local inclinacion = 0
local cabeceo = 0
local fovExtra = 0
local terceraPersona = false
local aplicado = CFrame.identity
local articulaciones: { [Model]: { hombros: { Motor6D }, codos: { Motor6D } } } = setmetatable({}, { __mode = "k" }) :: any
local HOMBROS = { "RightUpperArm", "LeftUpperArm" }
local CODOS = { "RightLowerArm", "LeftLowerArm" }
local GIRO_HOMBRO = CFrame.Angles(math.rad(78), 0, 0)
local GIRO_CODO = CFrame.Angles(math.rad(18), 0, 0)

function Camara.sacudir(cantidad: number)
	trauma = math.min(1, trauma + cantidad)
end

function Camara.impulsoFov(cantidad: number)
	fovExtra = math.max(fovExtra, cantidad)
end

function Camara.terceraPersona(activa: boolean)
	terceraPersona = activa
	if activa then
		jugador.CameraMode = Enum.CameraMode.Classic
		jugador.CameraMaxZoomDistance = 12
		jugador.CameraMinZoomDistance = 9
	else
		jugador.CameraMinZoomDistance = 0.5
		jugador.CameraMaxZoomDistance = 0.5
		jugador.CameraMode = Enum.CameraMode.LockFirstPerson
	end
end

local function ruido(t: number, semilla: number): number
	return math.noise(t * 9, semilla) * 2
end

local function brazos(personaje: Model)
	for _, nombre in Config.BRAZOS do
		local parte = personaje:FindFirstChild(nombre)
		if parte and parte:IsA("BasePart") then
			parte.LocalTransparencyModifier = 0
		end
	end
end

local function motores(personaje: Model, nombres: { string }): { Motor6D }
	local lista: { Motor6D } = {}
	for _, nombre in nombres do
		local parte = personaje:FindFirstChild(nombre)
		if parte then
			for _, m in parte:GetChildren() do
				if m:IsA("Motor6D") then
					table.insert(lista, m)
				end
			end
		end
	end
	return lista
end

local function poseSosteniendo(personaje: Model)
	local sosteniendo = personaje:GetAttribute("Sosteniendo")
	if typeof(sosteniendo) ~= "string" or sosteniendo == "" or personaje:GetAttribute("Ragdoll") then
		return
	end
	local datos = articulaciones[personaje]
	if not datos then
		datos = { hombros = motores(personaje, HOMBROS), codos = motores(personaje, CODOS) }
		articulaciones[personaje] = datos
	end
	for _, m in datos.hombros do
		local rot = m.C0.Rotation
		m.Transform = rot:Inverse() * GIRO_HOMBRO * rot
	end
	for _, m in datos.codos do
		local rot = m.C0.Rotation
		m.Transform = rot:Inverse() * GIRO_CODO * rot
	end
end

function Camara.iniciar()
	Camara.terceraPersona(false)
	local camara = Workspace.CurrentCamera
	camara.FieldOfView = 80

	RunService.PreRender:Connect(function()
		local foco = camara.CFrame.Position
		for _, otro in Players:GetPlayers() do
			local personaje = otro.Character
			local raiz = personaje and personaje.PrimaryPart
			if personaje and raiz and (raiz.Position - foco).Magnitude < 90 then
				poseSosteniendo(personaje)
			end
		end
	end)

	RunService:BindToRenderStep("OverbookedDeshacer", Enum.RenderPriority.Camera.Value - 1, function()
		if aplicado ~= CFrame.identity then
			local cam = Workspace.CurrentCamera
			cam.CFrame = cam.CFrame * aplicado:Inverse()
			aplicado = CFrame.identity
		end
	end)
	RunService:BindToRenderStep("OverbookedCamara", Enum.RenderPriority.Camera.Value + 1, function(dt)
		tiempo += dt
		local cam = Workspace.CurrentCamera
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		local extra = CFrame.identity
		if humanoide and not terceraPersona then
			if humanoide.MoveDirection.Magnitude > 0.1 and humanoide.FloorMaterial ~= Enum.Material.Air then
				paso += dt * humanoide.WalkSpeed * 0.62
				extra *= CFrame.new(math.sin(paso) * 0.05, math.abs(math.cos(paso)) * 0.07 - 0.035, 0)
			end
		end
		local enTierra = avion:GetAttribute("EnTierra")
		local alabeo = avion:GetAttribute("Alabeo")
		local cab = avion:GetAttribute("Cabeceo")
		local objetivoInclinacion = if enTierra == false and typeof(alabeo) == "number" then math.rad(alabeo) * 0.22 else 0
		local objetivoCabeceo = if enTierra == false and typeof(cab) == "number" then math.rad(cab) * 0.12 else 0
		local suavizado = math.min(1, dt * 3)
		inclinacion += (objetivoInclinacion - inclinacion) * suavizado
		cabeceo += (objetivoCabeceo - cabeceo) * suavizado
		if trauma > 0 then
			local t = trauma * trauma
			extra *= CFrame.Angles(ruido(tiempo, 1) * 0.06 * t, ruido(tiempo, 2) * 0.06 * t, ruido(tiempo, 3) * 0.08 * t)
			trauma = math.max(0, trauma - dt * 1.4)
		end
		local total = extra * CFrame.Angles(cabeceo, 0, inclinacion)
		cam.CFrame = cam.CFrame * total
		aplicado = total
		fovExtra = math.max(0, fovExtra - dt * 18)
		cam.FieldOfView = 80 + fovExtra
		if personaje and not terceraPersona then
			brazos(personaje)
		end
	end)
end

return Camara
