--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Camara = require(script.Parent.Camara)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoRagdoll = Remotos:WaitForChild("Ragdoll") :: RemoteEvent
local RemotoSacudida = Remotos:WaitForChild("Sacudida") :: UnreliableRemoteEvent

local Cuerpo = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local enRagdoll = false
local puertas: { BasePart } = {}
local brechas: { [BasePart]: boolean } = {}
local rng = Random.new()

local function partes(personaje: Model, colision: boolean)
	for _, nombre in Config.PARTES_CUERPO do
		local p = personaje:FindFirstChild(nombre)
		if p and p:IsA("BasePart") and nombre ~= "Head" then
			p.CanCollide = colision
		end
	end
end

local function ragdoll(duracion: number, impulso: Vector3)
	local personaje = jugador.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
	if not personaje or not humanoide or not raiz or not raiz:IsA("BasePart") then
		return
	end
	if duracion > 0 then
		if not enRagdoll then
			enRagdoll = true
			humanoide:ChangeState(Enum.HumanoidStateType.Physics)
			partes(personaje, true)
			Camara.terceraPersona(true)
		end
		raiz.AssemblyLinearVelocity += impulso
		raiz.AssemblyAngularVelocity += Vector3.new(rng:NextNumber(-8, 8), rng:NextNumber(-8, 8), rng:NextNumber(-8, 8))
		Camara.sacudir(0.6)
	elseif enRagdoll then
		enRagdoll = false
		partes(personaje, false)
		humanoide:ChangeState(Enum.HumanoidStateType.GettingUp)
		Camara.terceraPersona(false)
	end
end

local function enAire(): boolean
	local fase = avion:GetAttribute("Fase")
	return fase == "Vuelo" or fase == "Aproximacion" or fase == "Despegue"
end

function Cuerpo.iniciar()
	for _, d in avion:WaitForChild("Puertas"):GetChildren() do
		if d:IsA("BasePart") and d:GetAttribute("Puerta") and not d:GetAttribute("Interior") then
			table.insert(puertas, d)
		end
	end
	for _, b in CollectionService:GetTagged("Brecha") do
		if b:IsA("BasePart") then
			brechas[b] = true
		end
	end
	CollectionService:GetInstanceAddedSignal("Brecha"):Connect(function(b)
		if b:IsA("BasePart") then
			brechas[b] = true
		end
	end)
	CollectionService:GetInstanceRemovedSignal("Brecha"):Connect(function(b)
		if b:IsA("BasePart") then
			brechas[b] = nil
		end
	end)
	RemotoRagdoll.OnClientEvent:Connect(function(duracion, impulso)
		if typeof(duracion) == "number" and typeof(impulso) == "Vector3" then
			ragdoll(duracion, impulso)
		end
	end)
	RemotoSacudida.OnClientEvent:Connect(function(magnitud)
		if typeof(magnitud) ~= "number" then
			return
		end
		Camara.sacudir(magnitud * 0.55)
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
		if humanoide and raiz and raiz:IsA("BasePart") and not humanoide.SeatPart and humanoide.FloorMaterial ~= Enum.Material.Air then
			raiz.AssemblyLinearVelocity += Vector3.new(rng:NextNumber(-1, 1) * 9, 4 + 10 * magnitud, rng:NextNumber(-1, 1) * 9) * magnitud
		end
	end)
	jugador.CharacterAdded:Connect(function()
		if enRagdoll then
			enRagdoll = false
			Camara.terceraPersona(false)
		end
	end)
	RunService.Heartbeat:Connect(function(dt)
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
		if not humanoide or not raiz or not raiz:IsA("BasePart") or humanoide.SeatPart or humanoide.Health <= 0 then
			return
		end
		if not enAire() or (personaje and personaje:GetAttribute("Escalando") == true) then
			return
		end
		local pos = raiz.Position
		local empuje = Vector3.zero
		for brecha in brechas do
			local delta = brecha.Position - pos
			local d = delta.Magnitude
			local fuerza = brecha:GetAttribute("Fuerza")
			if d < 20 and d > 0.1 then
				empuje += delta.Unit * 55 * (1 - d / 20) * (if typeof(fuerza) == "number" then fuerza else 1)
			end
		end
		if math.abs(pos.X) > 8.2 and pos.Y < 104 then
			empuje += Vector3.new(math.sign(pos.X) * 6, 0, 28)
		end
		if pos.Y > 111.2 and math.abs(pos.X) < 10 then
			empuje += Vector3.new(math.sign(pos.X) * 5, 0, 36)
		end
		for _, d in puertas do
			if d:GetAttribute("Abierta") then
				local delta = pos - d.Position
				if delta.Magnitude < 7 then
					empuje += Vector3.new(math.sign(d.Position.X) * 22, 0, 4) * (1 - delta.Magnitude / 7)
				end
			end
		end
		if avion:GetAttribute("RampaAbierta") and pos.Z > 12 then
			empuje += Vector3.new(0, 0, 14)
		end
		if empuje.Magnitude > 0 then
			raiz.AssemblyLinearVelocity += empuje * dt
		end
	end)
end

return Cuerpo
