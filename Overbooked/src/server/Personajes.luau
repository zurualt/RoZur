--!strict
local InsertService = game:GetService("InsertService")
local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local StarterPlayer = game:GetService("StarterPlayer")

local Config = require(ReplicatedStorage.Shared.Config)
local Estadisticas = require(script.Parent.Estadisticas)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoRagdoll = Remotos:WaitForChild("Ragdoll") :: RemoteEvent

type Ragdoll = {
	motores: { Motor6D },
	juntas: { BallSocketConstraint },
	activo: boolean,
	fin: number,
	jugador: Player,
}

local Personajes = {}

local colores: { [Player]: Color3 } = {}
local ocupados: { [number]: Player } = {}
local ragdolls: { [Model]: Ragdoll } = {}
local alCaer: { (Player) -> () } = {}

local function asignarColor(jugador: Player)
	for i, color in Config.COLORES_JUGADOR do
		if not ocupados[i] then
			ocupados[i] = jugador
			colores[jugador] = color
			jugador:SetAttribute("Color", color)
			return
		end
	end
	colores[jugador] = Config.COLORES_JUGADOR[1]
	jugador:SetAttribute("Color", Config.COLORES_JUGADOR[1])
end

local function liberarColor(jugador: Player)
	for i, dueno in ocupados do
		if dueno == jugador then
			ocupados[i] = nil
		end
	end
	colores[jugador] = nil
end

local function pintar(personaje: Model, color: Color3)
	for _, d in personaje:GetDescendants() do
		if d:IsA("BasePart") and table.find(Config.PARTES_CUERPO, d.Name) then
			d.Color = color
		end
	end
end

local function prepararRagdoll(jugador: Player, personaje: Model)
	local motores: { Motor6D } = {}
	local juntas: { BallSocketConstraint } = {}
	for _, d in personaje:GetDescendants() do
		if d:IsA("Motor6D") and d.Name ~= "Root" then
			local p0, p1 = d.Part0, d.Part1
			if p0 and p1 and p0.Name ~= "HumanoidRootPart" then
				local a0 = Instance.new("Attachment")
				a0.Name = "RagdollA"
				a0.CFrame = d.C0
				a0.Parent = p0
				local a1 = Instance.new("Attachment")
				a1.Name = "RagdollB"
				a1.CFrame = d.C1
				a1.Parent = p1
				local junta = Instance.new("BallSocketConstraint")
				junta.Name = "RagdollJunta"
				junta.Attachment0 = a0
				junta.Attachment1 = a1
				junta.LimitsEnabled = true
				junta.UpperAngle = 55
				junta.TwistLimitsEnabled = true
				junta.TwistLowerAngle = -45
				junta.TwistUpperAngle = 45
				junta.Enabled = false
				junta.Parent = p1
				table.insert(motores, d)
				table.insert(juntas, junta)
			end
		end
	end
	ragdolls[personaje] = { motores = motores, juntas = juntas, activo = false, fin = 0, jugador = jugador }
end

local function terminarRagdoll(personaje: Model, datos: Ragdoll)
	datos.activo = false
	for _, m in datos.motores do
		m.Enabled = true
	end
	for _, j in datos.juntas do
		j.Enabled = false
	end
	personaje:SetAttribute("Ragdoll", false)
	if datos.jugador.Parent then
		RemotoRagdoll:FireClient(datos.jugador, 0, Vector3.zero)
	end
end

function Personajes.ragdoll(jugador: Player, duracion: number, impulso: Vector3)
	local personaje = jugador.Character
	if not personaje then
		return
	end
	local datos = ragdolls[personaje]
	local humanoide = personaje:FindFirstChildOfClass("Humanoid")
	if not datos or not humanoide or humanoide.Health <= 0 or humanoide.SeatPart then
		return
	end
	datos.fin = math.max(datos.fin, os.clock() + duracion)
	if not datos.activo then
		Estadisticas.sumar(jugador, "caidas")
		datos.activo = true
		for _, m in datos.motores do
			m.Enabled = false
		end
		for _, j in datos.juntas do
			j.Enabled = true
		end
		personaje:SetAttribute("Ragdoll", true)
	end
	RemotoRagdoll:FireClient(jugador, duracion, impulso)
end

function Personajes.ragdollTodos(duracion: number, fuerza: number)
	local rng = Random.new()
	for _, jugador in Players:GetPlayers() do
		local dir = Vector3.new(rng:NextNumber(-1, 1), 0.6, rng:NextNumber(-1, 1)).Unit
		Personajes.ragdoll(jugador, duracion, dir * fuerza)
	end
end

function Personajes.enRagdoll(jugador: Player): boolean
	local personaje = jugador.Character
	local datos = personaje and ragdolls[personaje]
	return datos ~= nil and datos.activo
end

function Personajes.raiz(jugador: Player): BasePart?
	local personaje = jugador.Character
	local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
	if raiz and raiz:IsA("BasePart") then
		return raiz
	end
	return nil
end

function Personajes.vivo(jugador: Player): boolean
	local personaje = jugador.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	return humanoide ~= nil and humanoide.Health > 0
end

function Personajes.alCaer(f: (Player) -> ())
	table.insert(alCaer, f)
end

function Personajes.color(jugador: Player): Color3
	return colores[jugador] or Config.COLORES_JUGADOR[1]
end

local function alPersonaje(jugador: Player, personaje: Model)
	local humanoide = personaje:WaitForChild("Humanoid", 10)
	if not humanoide or not humanoide:IsA("Humanoid") then
		return
	end
	humanoide.BreakJointsOnDeath = false
	humanoide.RequiresNeck = false
	humanoide.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	pintar(personaje, Personajes.color(jugador))
	prepararRagdoll(jugador, personaje)
	personaje:SetAttribute("Sosteniendo", "")
	for _, d in personaje:GetDescendants() do
		if d:IsA("BasePart") then
			d.CollisionGroup = "Jugadores"
		end
	end
	personaje.DescendantAdded:Connect(function(d)
		if d:IsA("BasePart") then
			d.CollisionGroup = "Jugadores"
		end
	end)
	personaje.Destroying:Connect(function()
		ragdolls[personaje] = nil
	end)
end

local function cargarPlantilla()
	local resultado: Model? = nil
	for intento = 1, 3 do
		local ok, r = pcall(function()
			return InsertService:LoadAsset(Config.ASSET_TRIPULANTE)
		end)
		if ok and r then
			resultado = r
			break
		end
		if intento < 3 then
			task.wait(intento * 2)
		end
	end
	if not resultado then
		warn("[Overbooked] No se pudo cargar el tripulante; se usan personajes por defecto")
		return
	end
	local humanoide = resultado:FindFirstChildWhichIsA("Humanoid", true)
	local modelo = humanoide and humanoide.Parent
	if not humanoide or not modelo or not modelo:IsA("Model") then
		warn("[Overbooked] El tripulante importado no tiene Humanoid; se usan personajes por defecto")
		return
	end
	local raiz = modelo:FindFirstChild("HumanoidRootPart")
	if not raiz or not raiz:IsA("BasePart") then
		warn("[Overbooked] El tripulante importado no tiene HumanoidRootPart; se usan personajes por defecto")
		return
	end
	for _, d in modelo:GetDescendants() do
		if d:IsA("BaseScript") or d:IsA("BallSocketConstraint") then
			d:Destroy()
		elseif d:IsA("BasePart") then
			d.Anchored = false
		elseif d:IsA("AnimationConstraint") then
			local a0, a1 = d.Attachment0, d.Attachment1
			local p0 = a0 and a0.Parent
			local p1 = a1 and a1.Parent
			if a0 and a1 and p0 and p1 and p0:IsA("BasePart") and p1:IsA("BasePart") then
				local motor = Instance.new("Motor6D")
				motor.Name = d.Name
				motor.Part0 = p0
				motor.Part1 = p1
				motor.C0 = a0.CFrame
				motor.C1 = a1.CFrame
				motor.Parent = p1
			end
			d:Destroy()
		end
	end
	modelo.PrimaryPart = raiz
	raiz.Transparency = 1
	local altura = modelo:GetExtentsSize().Y
	if altura > 0 and (altura < Config.ALTURA_TRIPULANTE * 0.75 or altura > Config.ALTURA_TRIPULANTE * 1.35) then
		modelo:ScaleTo(modelo:GetScale() * Config.ALTURA_TRIPULANTE / altura)
	end
	humanoide.BreakJointsOnDeath = false
	humanoide.RequiresNeck = false
	if not humanoide:FindFirstChildOfClass("Animator") then
		Instance.new("Animator").Parent = humanoide
	end
	local fondo = math.huge
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") and d ~= raiz then
			local cf, medio = d.CFrame, d.Size / 2
			local alto = math.abs(cf.RightVector.Y) * medio.X + math.abs(cf.UpVector.Y) * medio.Y + math.abs(cf.LookVector.Y) * medio.Z
			fondo = math.min(fondo, d.Position.Y - alto)
		end
	end
	local cadera = (raiz.Position.Y - raiz.Size.Y / 2) - fondo
	if cadera > 0 and cadera < 10 then
		humanoide.HipHeight = cadera
	end
	modelo.Name = "StarterCharacter"
	modelo.Parent = nil
	resultado:Destroy()
	modelo.Parent = StarterPlayer
	local estado = ReplicatedStorage:FindFirstChild("Estado")
	local fase = if estado then estado:GetAttribute("Fase") else nil
	if fase == "Vuelo" or fase == "Resultados" then
		return
	end
	for _, jugador in Players:GetPlayers() do
		task.spawn(function()
			jugador:LoadCharacter()
		end)
	end
end

function Personajes.iniciar()
	pcall(function()
		PhysicsService:RegisterCollisionGroup("Jugadores")
		PhysicsService:RegisterCollisionGroup("Sostenido")
		PhysicsService:CollisionGroupSetCollidable("Sostenido", "Jugadores", false)
	end)
	local function alEntrar(jugador: Player)
		asignarColor(jugador)
		jugador.CharacterAdded:Connect(function(personaje)
			alPersonaje(jugador, personaje)
		end)
		jugador.CharacterRemoving:Connect(function(personaje)
			ragdolls[personaje] = nil
		end)
		local personaje = jugador.Character
		if personaje then
			task.spawn(alPersonaje, jugador, personaje)
		end
	end
	for _, jugador in Players:GetPlayers() do
		alEntrar(jugador)
	end
	Players.PlayerAdded:Connect(alEntrar)
	Players.PlayerRemoving:Connect(liberarColor)
	task.spawn(cargarPlantilla)

	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		if acumulado < 0.2 then
			return
		end
		acumulado = 0
		local ahora = os.clock()
		for personaje, datos in ragdolls do
			if datos.activo and ahora >= datos.fin then
				terminarRagdoll(personaje, datos)
			end
		end
		for _, jugador in Players:GetPlayers() do
			local raiz = Personajes.raiz(jugador)
			if raiz and raiz.Position.Y < Config.CAIDA_Y and Personajes.vivo(jugador) then
				local humanoide = (jugador.Character :: Model):FindFirstChildOfClass("Humanoid")
				if humanoide then
					humanoide.Health = 0
				end
				for _, f in alCaer do
					task.spawn(f, jugador)
				end
			end
		end
	end)
end

return Personajes
