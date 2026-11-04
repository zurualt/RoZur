--!strict
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Camara = require(script.Parent.Camara)
local Sonido = require(script.Parent.Sonido)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoDisparar = Remotos:WaitForChild("Disparar") :: RemoteEvent

type Visual = {
	modelo: Model,
	raiz: BasePart,
	partes: { BasePart },
	offsets: { CFrame },
	marcos: { CFrame },
	anterior: Vector3,
}

local Piratas = {}

local CENTRO = Vector3.new(0, 105, -18)
local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local visuales: { [Instance]: Visual } = {}
local enTorreta = false
local disparando = false
local ultimo = 0

local function posicion(f: Instance, t: number): Vector3
	local radio = f:GetAttribute("Radio")
	local velocidad = f:GetAttribute("Velocidad")
	local fase = f:GetAttribute("Fase")
	local altura = f:GetAttribute("Altura")
	local inicio = f:GetAttribute("Inicio")
	if typeof(radio) ~= "number" or typeof(velocidad) ~= "number" or typeof(fase) ~= "number" or typeof(altura) ~= "number" or typeof(inicio) ~= "number" then
		return CENTRO
	end
	local a = fase + velocidad * (t - inicio)
	return CENTRO + Vector3.new(math.cos(a) * radio, altura + math.sin(a * 2.3) * 8, math.sin(a) * radio * 0.7)
end

local function pieza(modelo: Model, tamano: Vector3, color: Color3, offset: CFrame, lista: { BasePart }, offsets: { CFrame }, forma: Enum.PartType?): Part
	local p = Instance.new("Part")
	p.Size = tamano
	p.Color = color
	p.Material = Enum.Material.SmoothPlastic
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	if forma then
		p.Shape = forma
	end
	p.Parent = modelo
	table.insert(lista, p)
	table.insert(offsets, offset)
	return p
end

local function crear(f: Instance)
	local modelo = Instance.new("Model")
	modelo.Name = "AvionPirata"
	local partes: { BasePart } = {}
	local offsets: { CFrame } = {}
	local gris = Color3.fromRGB(70, 74, 80)
	local rojo = Color3.fromRGB(190, 40, 40)
	local raiz = pieza(modelo, Vector3.new(2.6, 2.6, 13), gris, CFrame.identity, partes, offsets)
	pieza(modelo, Vector3.new(16, 0.5, 3.2), gris, CFrame.new(0, -0.3, -0.5), partes, offsets)
	pieza(modelo, Vector3.new(16.2, 0.55, 0.8), rojo, CFrame.new(0, -0.28, -1.8), partes, offsets)
	pieza(modelo, Vector3.new(6, 0.4, 2), gris, CFrame.new(0, 0.6, 5.4), partes, offsets)
	pieza(modelo, Vector3.new(0.4, 2.6, 2), rojo, CFrame.new(0, 1.8, 5.6), partes, offsets)
	pieza(modelo, Vector3.new(1.8, 1.2, 2.4), Color3.fromRGB(40, 60, 80), CFrame.new(0, 1.3, -1.8), partes, offsets)
	pieza(modelo, Vector3.new(3.4, 0.2, 0.3), Color3.fromRGB(30, 30, 30), CFrame.new(0, 0, -6.6), partes, offsets)
	pieza(modelo, Vector3.new(0.15, 1.6, 2.2), Color3.fromRGB(20, 20, 20), CFrame.new(0, 3.4, 5.6), partes, offsets)
	modelo.Parent = Workspace
	visuales[f] = { modelo = modelo, raiz = raiz, partes = partes, offsets = offsets, marcos = table.clone(offsets), anterior = posicion(f, Workspace:GetServerTimeNow()) }
	f:GetAttributeChangedSignal("Vida"):Connect(function()
		local vida = f:GetAttribute("Vida")
		if typeof(vida) == "number" and vida <= 0 then
			local explosion = Instance.new("Explosion")
			explosion.BlastPressure = 0
			explosion.BlastRadius = 0
			explosion.DestroyJointRadiusPercent = 0
			explosion.Position = raiz.Position
			explosion.Parent = Workspace
			Sonido.reproducir("PirataCae", raiz.Position, 1.2)
		end
	end)
	f.Destroying:Connect(function()
		modelo:Destroy()
		visuales[f] = nil
	end)
end

local function trazador(origen: Vector3, direccion: Vector3)
	local largo = 260
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.Material = Enum.Material.Neon
	p.Color = Color3.fromRGB(255, 220, 120)
	p.Size = Vector3.new(0.18, 0.18, largo)
	p.CFrame = CFrame.lookAt(origen, origen + direccion) * CFrame.new(0, 0, -largo / 2)
	p.Parent = Workspace
	task.delay(0.06, function()
		p:Destroy()
	end)
end

local function cambiar(nuevo: boolean)
	if nuevo == enTorreta then
		return
	end
	enTorreta = nuevo
	if enTorreta then
		ContextActionService:BindAction("Disparar", function(_, estado)
			disparando = estado == Enum.UserInputState.Begin or estado == Enum.UserInputState.Change
			return Enum.ContextActionResult.Sink
		end, true, Enum.UserInputType.MouseButton1, Enum.KeyCode.ButtonR2)
		ContextActionService:SetTitle("Disparar", "Fuego")
	else
		ContextActionService:UnbindAction("Disparar")
		disparando = false
	end
end

function Piratas.iniciar()
	local carpeta = avion:WaitForChild("Piratas")
	for _, f in carpeta:GetChildren() do
		crear(f)
	end
	carpeta.ChildAdded:Connect(crear)
	local function alPersonaje(personaje: Model)
		cambiar(false)
		local humanoide = personaje:WaitForChild("Humanoid", 10)
		if humanoide and humanoide:IsA("Humanoid") then
			humanoide.Seated:Connect(function(sentado, asiento)
				if asiento then
					cambiar(sentado and asiento.Name == "Torreta")
				else
					cambiar(false)
				end
			end)
		end
	end
	if jugador.Character then
		task.spawn(alPersonaje, jugador.Character)
	end
	jugador.CharacterAdded:Connect(alPersonaje)
	RunService.PreRender:Connect(function()
		local t = Workspace:GetServerTimeNow()
		for f, v in visuales do
			local pos = posicion(f, t)
			local avance = pos - v.anterior
			v.anterior = pos
			local base = if avance.Magnitude > 0.01 then CFrame.lookAt(pos, pos + avance) else CFrame.new(pos)
			local marcos = v.marcos
			for i, o in v.offsets do
				marcos[i] = base * o
			end
			Workspace:BulkMoveTo(v.partes, marcos, Enum.BulkMoveMode.FireCFrameChanged)
		end
		if enTorreta and disparando and os.clock() - ultimo > 0.12 then
			ultimo = os.clock()
			local camara = Workspace.CurrentCamera
			local dir = camara.CFrame.LookVector
			RemotoDisparar:FireServer(dir)
			Sonido.reproducir("Disparo", nil, 0.7)
			trazador(camara.CFrame.Position + dir * 3 - camara.CFrame.UpVector * 0.8, dir)
			Camara.sacudir(0.12)
		end
	end)
end

return Piratas
