--!strict
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local DB_MIN = -46
local DB_MAX = -12
local ATAQUE = 30
local CAIDA = 12
local ABRIR = 0.24
local SUBIR = 0.05
local ADELANTE = 0.02
local SEPARACION_REPOSO = 0.05
local DISTANCIA_MAX = 120
local MINIMO = 0.002
local A_DECIBELIOS = 20 / math.log(10)

type Estado = {
	entrada: AudioDeviceInput?,
	analizador: AudioAnalyzer?,
	sup: Bone?,
	inf: Bone?,
	cabeza: BasePart?,
	vSup: Vector3,
	vInf: Vector3,
	apertura: number,
	aplicada: number,
	conexiones: { RBXScriptConnection },
	conexionesPersonaje: { RBXScriptConnection },
}

local BocaVoz = {}

local estados: { [Player]: Estado } = {}
local iniciado = false

local function desconectar(lista: { RBXScriptConnection })
	for _, conexion in lista do
		conexion:Disconnect()
	end
	table.clear(lista)
end

local function ponerBoca(estado: Estado, k: number)
	local sup, inf = estado.sup, estado.inf
	if sup and inf then
		sup.Transform = CFrame.new(estado.vSup * k)
		inf.Transform = CFrame.new(estado.vInf * k)
	end
	estado.aplicada = k
end

local function enHueso(hueso: Bone, cabeza: BasePart, v: Vector3): Vector3
	return hueso.WorldCFrame:VectorToObjectSpace(cabeza.CFrame:VectorToWorldSpace(v))
end

local function enlazarHuesos(estado: Estado, personaje: Model): boolean
	local sup = personaje:FindFirstChild("BocaSup", true)
	local inf = personaje:FindFirstChild("BocaInf", true)
	local cabeza = personaje:FindFirstChild("Head")
	if not (sup and sup:IsA("Bone") and inf and inf:IsA("Bone") and cabeza and cabeza:IsA("BasePart")) then
		return false
	end
	sup.Transform = CFrame.identity
	inf.Transform = CFrame.identity
	local escala = (sup.WorldPosition - inf.WorldPosition).Magnitude / SEPARACION_REPOSO
	estado.sup = sup
	estado.inf = inf
	estado.cabeza = cabeza
	estado.vSup = enHueso(sup, cabeza, Vector3.new(0, SUBIR * escala, 0))
	estado.vInf = enHueso(inf, cabeza, Vector3.new(0, -ABRIR * escala, -ADELANTE * escala))
	estado.apertura = 0
	estado.aplicada = 0
	return true
end

local function alPersonaje(estado: Estado, personaje: Model)
	desconectar(estado.conexionesPersonaje)
	estado.sup, estado.inf, estado.cabeza = nil, nil, nil
	if enlazarHuesos(estado, personaje) then
		return
	end
	table.insert(
		estado.conexionesPersonaje,
		personaje.DescendantAdded:Connect(function(nuevo)
			local nombre = nuevo.Name
			if (nombre == "BocaSup" or nombre == "BocaInf" or nombre == "Head") and enlazarHuesos(estado, personaje) then
				desconectar(estado.conexionesPersonaje)
			end
		end)
	)
end

local function enlazarEntrada(estado: Estado, entrada: AudioDeviceInput)
	local anterior = estado.analizador
	if anterior then
		anterior:Destroy()
	end
	local analizador = Instance.new("AudioAnalyzer")
	analizador.SpectrumEnabled = false
	local cable = Instance.new("Wire")
	cable.SourceInstance = entrada
	cable.TargetInstance = analizador
	cable.Parent = analizador
	analizador.Parent = entrada
	estado.entrada = entrada
	estado.analizador = analizador
end

local function seguir(jugador: Player)
	if estados[jugador] then
		return
	end
	local estado: Estado = {
		entrada = nil,
		analizador = nil,
		sup = nil,
		inf = nil,
		cabeza = nil,
		vSup = Vector3.zero,
		vInf = Vector3.zero,
		apertura = 0,
		aplicada = 0,
		conexiones = {},
		conexionesPersonaje = {},
	}
	estados[jugador] = estado
	local entrada = jugador:FindFirstChildOfClass("AudioDeviceInput")
	if entrada then
		enlazarEntrada(estado, entrada)
	end
	table.insert(
		estado.conexiones,
		jugador.ChildAdded:Connect(function(hijo)
			if hijo:IsA("AudioDeviceInput") then
				enlazarEntrada(estado, hijo)
			end
		end)
	)
	table.insert(
		estado.conexiones,
		jugador.CharacterAdded:Connect(function(personaje)
			alPersonaje(estado, personaje)
		end)
	)
	local personaje = jugador.Character
	if personaje then
		alPersonaje(estado, personaje)
	end
end

local function soltar(jugador: Player)
	local estado = estados[jugador]
	if not estado then
		return
	end
	estados[jugador] = nil
	desconectar(estado.conexiones)
	desconectar(estado.conexionesPersonaje)
	local analizador = estado.analizador
	if analizador then
		analizador:Destroy()
	end
end

local function volumen(estado: Estado): number
	local analizador, entrada = estado.analizador, estado.entrada
	if not (analizador and entrada) or entrada.Muted or not entrada.Active then
		return 0
	end
	local nivel = math.max(analizador.RmsLevel, analizador.PeakLevel * 0.5)
	if nivel <= 0 then
		return 0
	end
	return math.clamp((math.log(nivel) * A_DECIBELIOS - DB_MIN) / (DB_MAX - DB_MIN), 0, 1)
end

local function paso(dt: number)
	local camara = Workspace.CurrentCamera
	local foco = if camara then camara.CFrame.Position else Vector3.zero
	local ataque = 1 - math.exp(-ATAQUE * dt)
	local caida = 1 - math.exp(-CAIDA * dt)
	local limite = DISTANCIA_MAX * DISTANCIA_MAX
	for _, estado in estados do
		local cabeza = estado.cabeza
		if not (cabeza and cabeza.Parent) then
			continue
		end
		local delta = cabeza.Position - foco
		local objetivo = if delta:Dot(delta) < limite then volumen(estado) else 0
		local k = estado.apertura
		k += (objetivo - k) * (if objetivo > k then ataque else caida)
		if k < MINIMO then
			k = 0
		end
		estado.apertura = k
		if math.abs(k - estado.aplicada) > MINIMO or (k == 0 and estado.aplicada ~= 0) then
			ponerBoca(estado, k)
		end
	end
end

function BocaVoz.iniciar()
	if iniciado then
		return
	end
	iniciado = true
	for _, jugador in Players:GetPlayers() do
		seguir(jugador)
	end
	Players.PlayerAdded:Connect(seguir)
	Players.PlayerRemoving:Connect(soltar)
	RunService.PreRender:Connect(paso)
end

return BocaVoz
