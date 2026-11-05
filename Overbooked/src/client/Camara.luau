--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Manos = require(script.Parent.Manos)

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
local fovBase = 80
local aplicado = CFrame.identity
type Brazos = { motores: { [string]: Motor6D }, inclinacion: number }
local articulaciones: { [Model]: Brazos } = setmetatable({}, { __mode = "k" }) :: any
local MOTORES = { "RightShoulder", "LeftShoulder", "RightElbow", "LeftElbow", "RightWrist", "LeftWrist" }
local POSE_BRAZO: { [string]: { number } } = {
	puno = { 58, 42, 0, 12, 18 },
	vaso = { 58, 42, 0, 12, 18 },
	palma = { 48, 58, -90, 12, 0 },
	colgar = { 40, 20, 0, 6, 0 },
	dos = { 62, 40, 0, 16, 20 },
}
local tensionLanzar = 0
local LEVANTE_PROPIO = math.rad(22)
local GIRO_HOMBRO_REPOSO = CFrame.Angles(math.rad(58), 0, 0)
local alcanceHasta = 0
local GIRO_CODO_REPOSO = CFrame.Angles(math.rad(80), 0, 0)
local GIRO_MUNECA_REPOSO = CFrame.Angles(-math.rad(32), 0, 0)
local ABRIR_REPOSO = math.rad(15)
local ELEVAR = CFrame.new(0, 0.35, 0)
local ALTURA_OJOS = Vector3.new(0, -0.44, 0)

function Camara.sacudir(cantidad: number)
	trauma = math.min(1, trauma + cantidad)
end

function Camara.impulsoFov(cantidad: number)
	fovExtra = math.max(fovExtra, cantidad)
end

function Camara.fov(valor: number)
	fovBase = math.clamp(valor, 60, 100)
end

function Camara.esTerceraPersona(): boolean
	return terceraPersona
end

local forzada = false
local preferida = false

local function aplicarModo()
	local activa = forzada or preferida
	terceraPersona = activa
	if activa then
		jugador.CameraMode = Enum.CameraMode.Classic
		jugador.CameraMaxZoomDistance = 9.5
		jugador.CameraMinZoomDistance = 7
	else
		jugador.CameraMinZoomDistance = 0.5
		jugador.CameraMaxZoomDistance = 0.5
		jugador.CameraMode = Enum.CameraMode.LockFirstPerson
	end
end

function Camara.terceraPersona(activa: boolean)
	forzada = activa
	aplicarModo()
end

function Camara.preferirTercera(activa: boolean)
	preferida = activa
	aplicarModo()
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

local function girar(m: Motor6D?, giro: CFrame)
	if m then
		local rot = m.C0.Rotation
		m.Transform = rot:Inverse() * giro * rot
	end
end

local function elevacion(marco: CFrame, v: Vector3): number
	local l = marco:VectorToObjectSpace(v)
	return math.atan2(l.Y, -l.Z)
end

local function apuntarAlObjeto(personaje: Model, datos: Brazos, estilo: Manos.Estilo)
	local valor = personaje:FindFirstChild("Sostenido")
	local objeto = if valor and valor:IsA("ObjectValue") then valor.Value else nil
	local raiz = if objeto and objeto:IsA("Model") then objeto.PrimaryPart elseif objeto and objeto:IsA("BasePart") then objeto else nil
	local torso = personaje:FindFirstChild("UpperTorso")
	local hombro = datos.motores.RightShoulder
	local mano, punto = Manos.punto(personaje)
	if not (raiz and torso and torso:IsA("BasePart") and hombro and mano) then
		return
	end
	local actual = punto or mano.Position
	local objetivo = (raiz.CFrame * Manos.desfase(estilo, raiz.Size):Inverse()).Position
	local origen = (torso.CFrame * hombro.C0).Position
	local desvio = elevacion(torso.CFrame, objetivo - origen) - elevacion(torso.CFrame, actual - origen)
	datos.inclinacion = math.clamp(datos.inclinacion + desvio * 0.5, -0.8, 1.2)
end

local function poseSosteniendo(personaje: Model)
	if personaje:GetAttribute("Ragdoll") then
		return
	end
	local sosteniendo = personaje:GetAttribute("Sosteniendo")
	local tipo = if typeof(sosteniendo) == "string" then sosteniendo else ""
	local propio = personaje == jugador.Character and not terceraPersona
	local datos = articulaciones[personaje]
	if tipo == "" and not propio then
		if datos then
			girar(datos.motores.RightWrist, CFrame.identity)
			girar(datos.motores.LeftWrist, CFrame.identity)
		end
		return
	end
	if not datos then
		local lista: { [string]: Motor6D } = {}
		for _, nombre in MOTORES do
			local m = personaje:FindFirstChild(nombre, true)
			if m and m:IsA("Motor6D") then
				lista[nombre] = m
			end
		end
		if not lista.RightShoulder then
			return
		end
		datos = { motores = lista, inclinacion = 0 }
		articulaciones[personaje] = datos
	end
	local m = datos.motores
	local inclinacionVista = if propio then math.clamp(math.asin(math.clamp(Workspace.CurrentCamera.CFrame.LookVector.Y, -1, 1)), -0.8, 1.2) else 0
	local reposo = CFrame.Angles(inclinacionVista, 0, 0) * GIRO_HOMBRO_REPOSO
	local reposoDer = CFrame.Angles(0, -ABRIR_REPOSO, 0) * reposo
	local reposoIzq = CFrame.Angles(0, ABRIR_REPOSO, 0) * reposo
	if tipo ~= "" then
		local estilo = Manos.estilo(tipo)
		if personaje ~= jugador.Character then
			apuntarAlObjeto(personaje, datos, estilo)
			inclinacionVista = datos.inclinacion
		elseif propio and estilo.modo ~= "dos" then
			inclinacionVista += LEVANTE_PROPIO
		end
		local p = POSE_BRAZO[estilo.modo]
		local tension = if personaje == jugador.Character then tensionLanzar else 0
		local dentro = math.rad(p[4])
		local alzar = if propio then ELEVAR else CFrame.identity
		local doblar = if propio then CFrame.Angles(-math.rad(p[5]), 0, 0) else CFrame.identity
		local subir = CFrame.Angles(inclinacionVista + math.rad(p[1]) + math.rad(40) * tension, 0, 0)
		local codo = CFrame.Angles(math.rad(p[2]) + math.rad(40) * tension, 0, 0)
		girar(m.RightShoulder, alzar * CFrame.Angles(0, dentro, 0) * subir)
		girar(m.RightElbow, codo)
		girar(m.RightWrist, CFrame.Angles(0, math.rad(p[3]), 0) * doblar)
		if estilo.modo == "dos" then
			girar(m.LeftShoulder, alzar * CFrame.Angles(0, -dentro, 0) * subir)
			girar(m.LeftElbow, codo)
			girar(m.LeftWrist, doblar)
		elseif propio then
			girar(m.LeftShoulder, ELEVAR * reposoIzq)
			girar(m.LeftElbow, GIRO_CODO_REPOSO)
			girar(m.LeftWrist, GIRO_MUNECA_REPOSO)
		else
			girar(m.LeftShoulder, CFrame.Angles(math.rad(5), 0, -math.rad(12)))
			girar(m.LeftElbow, CFrame.Angles(math.rad(20), 0, 0))
			girar(m.LeftWrist, CFrame.identity)
		end
		return
	end
	local alcance = math.clamp((alcanceHasta - os.clock()) / 0.45, 0, 1)
	local estirar = math.sin(alcance * math.pi)
	girar(m.RightShoulder, (ELEVAR * reposoDer):Lerp(ELEVAR * CFrame.Angles(inclinacionVista + math.rad(90), 0, 0), estirar))
	girar(m.RightElbow, GIRO_CODO_REPOSO:Lerp(CFrame.identity, estirar))
	girar(m.RightWrist, GIRO_MUNECA_REPOSO:Lerp(CFrame.identity, estirar))
	girar(m.LeftShoulder, ELEVAR * reposoIzq)
	girar(m.LeftElbow, GIRO_CODO_REPOSO)
	girar(m.LeftWrist, GIRO_MUNECA_REPOSO)
end

function Camara.tension(fuerza: number)
	tensionLanzar = fuerza
end

function Camara.alcanzar()
	Manos.abrir()
	alcanceHasta = os.clock() + 0.45
end

function Camara.iniciar()
	Camara.terceraPersona(false)
	local camara = Workspace.CurrentCamera
	camara.FieldOfView = fovBase

	RunService.PreSimulation:Connect(function()
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
		if humanoide and humanoide.CameraOffset ~= ALTURA_OJOS then
			humanoide.CameraOffset = ALTURA_OJOS
		end
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
		cam.FieldOfView = fovBase + fovExtra
		if personaje and not terceraPersona then
			brazos(personaje)
		end
	end)
end

return Camara
