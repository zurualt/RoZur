--!strict
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local DB_MIN = -46
local DB_MAX = -12
local ATAQUE = 30
local CAIDA = 12
local MINIMO = 0.002
local A_DECIBELIOS = 20 / math.log(10)

type Estado = {
	entrada: AudioDeviceInput?,
	analizador: AudioAnalyzer?,
	apertura: number,
	conexiones: { RBXScriptConnection },
}

local BocaVoz = {}

local estados: { [Player]: Estado } = {}
local iniciado = false

local function soltarEntrada(estado: Estado)
	local analizador = estado.analizador
	if analizador then
		analizador:Destroy()
	end
	estado.entrada, estado.analizador = nil, nil
end

local function enlazarEntrada(estado: Estado, entrada: AudioDeviceInput)
	soltarEntrada(estado)
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
		apertura = 0,
		conexiones = {},
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
		jugador.ChildRemoved:Connect(function(hijo)
			if hijo == estado.entrada then
				soltarEntrada(estado)
			end
		end)
	)
end

local function soltar(jugador: Player)
	local estado = estados[jugador]
	if not estado then
		return
	end
	estados[jugador] = nil
	for _, conexion in estado.conexiones do
		conexion:Disconnect()
	end
	soltarEntrada(estado)
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
	local ataque = 1 - math.exp(-ATAQUE * dt)
	local caida = 1 - math.exp(-CAIDA * dt)
	for _, estado in estados do
		local objetivo = volumen(estado)
		local k = estado.apertura
		k += (objetivo - k) * (if objetivo > k then ataque else caida)
		estado.apertura = if k < MINIMO then 0 else k
	end
end

function BocaVoz.nivel(jugador: Player): number
	local estado = estados[jugador]
	return if estado then estado.apertura else 0
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
	RunService.PreSimulation:Connect(paso)
end

return BocaVoz
