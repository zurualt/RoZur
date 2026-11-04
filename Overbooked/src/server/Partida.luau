--!strict
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Contratos = require(ReplicatedStorage.Shared.Contratos)
local Agarre = require(script.Parent.Agarre)
local Avion = require(script.Parent.Avion)
local Carga = require(script.Parent.Carga)
local Datos = require(script.Parent.Datos)
local Objetos = require(script.Parent.Objetos)
local Pasajeros = require(script.Parent.Pasajeros)
local Peligros = require(script.Parent.Peligros)
local Personajes = require(script.Parent.Personajes)
local Piratas = require(script.Parent.Piratas)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local RemotoResultados = Remotos:WaitForChild("Resultados") :: RemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder

local Partida = {}

local avion = Workspace:WaitForChild("Avion") :: Model
local aeropuerto = Workspace:WaitForChild("Aeropuerto") :: Model
local spawnAvion = avion:FindFirstChild("SpawnAvion", true) :: SpawnLocation
local spawnAeropuerto = aeropuerto:FindFirstChild("SpawnAeropuerto", true) :: SpawnLocation
local rng = Random.new()
local ciudad = Contratos.ciudadInicial(rng)
local ofertas: { Contratos.Contrato } = {}
local elegido: Contratos.Contrato? = nil
local resultado: { tipo: string, motivo: string }? = nil

local function fase(nombre: string)
	Estado:SetAttribute("Fase", nombre)
end

local function aviso(texto: string, tipo: string)
	RemotoAviso:FireAllClients(texto, tipo)
end

local function dentroDelAvion(posicion: Vector3): boolean
	return math.abs(posicion.X) < 7.4 and posicion.Y > 99 and posicion.Y < 112 and posicion.Z > -64 and posicion.Z < 22
end

local function meterJugadores()
	local i = 0
	for _, jugador in Players:GetPlayers() do
		local raiz = Personajes.raiz(jugador)
		local personaje = jugador.Character
		if raiz and personaje and not dentroDelAvion(raiz.Position) then
			local humanoide = personaje:FindFirstChildOfClass("Humanoid")
			local asiento = humanoide and humanoide.SeatPart
			if humanoide and asiento then
				local soldadura = asiento:FindFirstChild("SeatWeld")
				if soldadura then
					soldadura:Destroy()
				end
				humanoide.Sit = false
			end
			i += 1
			personaje:PivotTo(CFrame.new(rng:NextNumber(-1, 1), Config.SUELO_Y + 3.2, -46 + (i % 6) * 1.5))
		end
	end
end

local function publicarOfertas()
	table.clear(ofertas)
	for _ = 1, 3 do
		table.insert(ofertas, Contratos.generar(rng, ciudad))
	end
	Estado:SetAttribute("Contratos", HttpService:JSONEncode(ofertas))
	Estado:SetAttribute("Ciudad", ciudad)
end

local function prepararBotones()
	for _, d in aeropuerto:GetDescendants() do
		local n = d:GetAttribute("Contrato")
		if d:IsA("BasePart") and typeof(n) == "number" then
			local boton = Instance.new("ProximityPrompt")
			boton.ActionText = "Elegir"
			boton.ObjectText = `Contrato {n}`
			boton.MaxActivationDistance = 9
			boton.RequiresLineOfSight = false
			boton.Parent = d
			boton.Triggered:Connect(function(jugador)
				if Estado:GetAttribute("Fase") ~= "Aeropuerto" or elegido then
					return
				end
				local oferta = ofertas[n]
				if oferta then
					elegido = oferta
					RemotoAviso:FireAllClients(`{jugador.DisplayName} ha elegido: {oferta.origen} → {oferta.destino}`, "bien")
				end
			end)
		end
	end
end

local function esperarJugadores()
	while #Players:GetPlayers() == 0 do
		task.wait(1)
	end
end

local function enAeropuerto()
	fase("Aeropuerto")
	elegido = nil
	resultado = nil
	aeropuerto.Parent = Workspace
	spawnAeropuerto.Enabled = true
	spawnAvion.Enabled = false
	Avion.prepararTierra()
	publicarOfertas()
	esperarJugadores()
	local limite = os.clock() + 120
	while not elegido do
		Estado:SetAttribute("Cuenta", math.max(0, math.ceil(limite - os.clock())))
		if os.clock() >= limite and #Players:GetPlayers() > 0 then
			elegido = ofertas[1]
			aviso("Se ha elegido el primer contrato automáticamente", "info")
		end
		task.wait(0.5)
	end
end

local function embarque(contrato: Contratos.Contrato)
	fase("Embarque")
	Estado:SetAttribute("Contrato", HttpService:JSONEncode(contrato))
	Avion.embarque(contrato.distancia)
	Pasajeros.embarcar(contrato.pasajeros, contrato.riesgo)
	Carga.cargar(contrato)
	aviso(`🧳 ¡Embarque! Subid al avión por la rampa y meted las maletas del carro en la bodega. Destino: {contrato.destino}`, "info")
	for t = Config.PARTIDA.EMBARQUE, 1, -1 do
		Estado:SetAttribute("Cuenta", t)
		task.wait(1)
	end
	Estado:SetAttribute("Cuenta", 0)
end

local function vuelo(contrato: Contratos.Contrato)
	Carga.dejarEnTierra()
	meterJugadores()
	Avion.despegar()
	task.wait(2.3)
	meterJugadores()
	aeropuerto.Parent = ServerStorage
	spawnAvion.Enabled = true
	spawnAeropuerto.Enabled = false
	fase("Vuelo")
	Peligros.activar(contrato)
	aviso("🛫 ¡A despegar! El piloto: siéntate en la cabina, acelera (Shift) y sube (W)", "info")
	local inicio = os.clock()
	while not resultado do
		if Avion.fase() == "Despegue" and not Avion.estado.autopiloto and os.clock() - inicio > Config.PARTIDA.DESPEGUE_AUTO then
			Avion.estado.autopiloto = true
			aviso("Nadie pilota... el piloto automático despega por vosotros", "info")
		end
		task.wait(0.25)
	end
end

local function cobrar(contrato: Contratos.Contrato, tipo: string, motivo: string)
	local entregados, perdidos, satisfaccion, servidos = Pasajeros.resumen()
	local intacto, entregado, perdidoCarga, cocodrilo = Carga.resumen()
	local casco = Avion.estado.casco
	local datos: { [string]: any } = {
		tipo = tipo,
		motivo = motivo,
		destino = contrato.destino,
		pasajeros = entregados,
		perdidos = perdidos,
		satisfaccion = math.floor(satisfaccion * 100),
		servidos = servidos,
		carga = intacto,
		entregas = entregado,
		cargaPerdida = perdidoCarga,
		cocodrilo = cocodrilo,
		casco = math.floor(casco),
		aterrizaje = avion:GetAttribute("Aterrizaje") or "",
		piratas = Piratas.bonus(),
	}
	local total = 0
	if tipo == "Aterrizado" then
		local billetes = entregados * contrato.pagoPasajero * (0.4 + 0.6 * satisfaccion)
		local bonus = if datos.aterrizaje == "Perfecto" then 150 elseif datos.aterrizaje == "Bueno" then 60 else 0
		total = billetes + intacto + entregado * 1.5 + bonus + Piratas.bonus() - perdidos * contrato.multaPasajero - perdidoCarga * 0.5 - (100 - casco) * 3
		datos.billetes = math.floor(billetes)
		datos.bonus = bonus
	end
	total = math.max(0, math.floor(total))
	datos.total = total
	local jugadores = Players:GetPlayers()
	local parte = if #jugadores > 0 then math.floor(total / #jugadores) else 0
	datos.porJugador = parte
	for _, jugador in jugadores do
		Datos.sumar(jugador, parte, tipo == "Aterrizado")
	end
	RemotoResultados:FireAllClients(datos)
end

local function limpiar()
	Peligros.detener()
	Piratas.reiniciar()
	Agarre.soltarTodo()
	Pasajeros.limpiar()
	Carga.limpiar()
	Objetos.limpiar()
	Workspace.Gravity = Config.GRAVEDAD
end

local function bucle()
	prepararBotones()
	while true do
		enAeropuerto()
		local contrato = elegido :: Contratos.Contrato
		embarque(contrato)
		vuelo(contrato)
		local r = resultado :: { tipo: string, motivo: string }
		fase("Resultados")
		if r.tipo == "Estrellado" then
			aviso(`💥 {r.motivo}`, "peligro")
			Personajes.ragdollTodos(3, 70)
			task.wait(3)
		else
			ciudad = contrato.destino
		end
		cobrar(contrato, r.tipo, r.motivo)
		task.wait(Config.PARTIDA.RESULTADOS)
		limpiar()
		Avion.reparar()
		aeropuerto.Parent = Workspace
		spawnAeropuerto.Enabled = true
		spawnAvion.Enabled = false
		for _, jugador in Players:GetPlayers() do
			task.spawn(function()
				jugador:LoadCharacter()
			end)
		end
		task.wait(1)
	end
end

function Partida.iniciar()
	Avion.alTerminar(function(tipo, motivo)
		resultado = { tipo = tipo, motivo = motivo }
	end)
	Players.PlayerAdded:Connect(function(jugador)
		task.delay(6, function()
			if jugador.Parent then
				RemotoAviso:FireClient(jugador, "✈ ¡Bienvenido a Overbooked! Elige un vuelo en el tablero de la terminal · H: controles", "info")
			end
		end)
	end)
	Personajes.alCaer(function(jugador)
		aviso(`🪂 ¡{jugador.DisplayName} se ha caído del avión!`, "peligro")
	end)
	task.spawn(bucle)
end

return Partida
