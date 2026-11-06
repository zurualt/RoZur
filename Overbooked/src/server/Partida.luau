--!strict
local HttpService = game:GetService("HttpService")
local MemoryStoreService = game:GetService("MemoryStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")
local TeleportService = game:GetService("TeleportService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Contratos = require(ReplicatedStorage.Shared.Contratos)
local Agarre = require(script.Parent.Agarre)
local Avion = require(script.Parent.Avion)
local Cabina = require(script.Parent.Cabina)
local Caos = require(script.Parent.Caos)
local Aduana = require(script.Parent.Aduana)
local Carga = require(script.Parent.Carga)
local Datos = require(script.Parent.Datos)
local Estadisticas = require(script.Parent.Estadisticas)
local Interacciones = require(script.Parent.Interacciones)
local Isla = require(script.Parent.Isla)
local Objetos = require(script.Parent.Objetos)
local Pasajeros = require(script.Parent.Pasajeros)
local Peligros = require(script.Parent.Peligros)
local Personajes = require(script.Parent.Personajes)
local Piratas = require(script.Parent.Piratas)
local Preparacion = require(script.Parent.Preparacion)
local Rafagas = require(script.Parent.Rafagas)
local Roturas = require(script.Parent.Roturas)
local Salas = require(script.Parent.Salas)
local Tienda = require(script.Parent.Tienda)
local Vehiculos = require(script.Parent.Vehiculos)

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
local resultado: { tipo: string, motivo: string }? = nil
local listos = false
local avisoListos: ProximityPrompt? = nil
local vuelos = MemoryStoreService:GetSortedMap("OverbookedVuelos")
local jornadas = MemoryStoreService:GetSortedMap("OverbookedJornadas")
local esPartida = game.PrivateServerId ~= "" and game.PrivateServerOwnerId == 0
local jornada = 1

type Sala = { centro: BasePart, destino: TextLabel, info: TextLabel, estado: TextLabel, plazas: { Frame }, fin: number? }
local COLORES_SALA = { Color3.fromRGB(242, 123, 43), Color3.fromRGB(31, 166, 160), Color3.fromRGB(246, 196, 69) }
local OSCURO = Color3.fromRGB(27, 27, 33)
local APAGADO = Color3.fromRGB(52, 56, 63)
local CREMA = Color3.fromRGB(255, 244, 224)
local salas: { [number]: Sala } = {}
local saliendo: { [Player]: boolean } = setmetatable({}, { __mode = "k" }) :: any

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

local function etiqueta(padre: Instance, pos: UDim2, tam: UDim2, color: Color3, alineacion: Enum.TextXAlignment): TextLabel
	local t = Instance.new("TextLabel")
	t.Position = pos
	t.Size = tam
	t.BackgroundTransparency = 1
	t.Font = Enum.Font.FredokaOne
	t.TextScaled = true
	t.TextColor3 = color
	t.TextXAlignment = alineacion
	t.Text = ""
	t.Parent = padre
	return t
end

local function prepararSalas()
	local pantallas: { [number]: BasePart } = {}
	local centros: { [number]: BasePart } = {}
	for _, d in aeropuerto:GetDescendants() do
		local n = d:GetAttribute("Sala")
		if d:IsA("BasePart") and typeof(n) == "number" then
			if d.Name == "PantallaSala" then
				pantallas[n] = d
			else
				centros[n] = d
			end
		end
	end
	for n, centro in centros do
		local pantalla = pantallas[n]
		if not pantalla then
			continue
		end
		local color = COLORES_SALA[n] or CREMA
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Front
		gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		gui.PixelsPerStud = 200
		gui.LightInfluence = 0
		gui.Brightness = 1.4
		gui.MaxDistance = 90
		local fondo = Instance.new("Frame")
		fondo.Size = UDim2.fromScale(1, 1)
		fondo.BackgroundColor3 = OSCURO
		fondo.BorderSizePixel = 0
		fondo.Parent = gui
		local cabecera = Instance.new("Frame")
		cabecera.Size = UDim2.fromScale(1, 0.24)
		cabecera.BackgroundColor3 = color
		cabecera.BorderSizePixel = 0
		cabecera.Parent = fondo
		etiqueta(cabecera, UDim2.fromScale(0.05, 0.12), UDim2.fromScale(0.5, 0.76), OSCURO, Enum.TextXAlignment.Left).Text = `PUERTA {n}`
		etiqueta(cabecera, UDim2.fromScale(0.5, 0.22), UDim2.fromScale(0.45, 0.56), OSCURO, Enum.TextXAlignment.Right).Text = "SALIDAS"
		local plazas = {}
		for i = 1, Config.LOBBY.MAX do
			local plaza = Instance.new("Frame")
			plaza.Position = UDim2.fromScale(0.05 + (i - 1) * 0.11, 0.77)
			plaza.Size = UDim2.fromScale(0.085, 0.16)
			plaza.BackgroundColor3 = APAGADO
			plaza.BorderSizePixel = 0
			Instance.new("UICorner").Parent = plaza
			plaza.Parent = fondo
			table.insert(plazas, plaza)
		end
		salas[n] = {
			centro = centro,
			destino = etiqueta(fondo, UDim2.fromScale(0.05, 0.29), UDim2.fromScale(0.9, 0.28), CREMA, Enum.TextXAlignment.Left),
			info = etiqueta(fondo, UDim2.fromScale(0.05, 0.58), UDim2.fromScale(0.9, 0.12), Color3.fromRGB(169, 176, 184), Enum.TextXAlignment.Left),
			estado = etiqueta(fondo, UDim2.fromScale(0.52, 0.76), UDim2.fromScale(0.43, 0.18), color, Enum.TextXAlignment.Right),
			plazas = plazas,
			fin = nil,
		}
		Salas.registrar(n, centro)
		gui.Parent = pantalla
	end
end

local function pintarSala(sala: Sala, oferta: Contratos.Contrato?, ocupadas: number, estado: string)
	sala.destino.Text = if oferta then oferta.destino else ""
	sala.info.Text = if oferta then `{math.floor(oferta.distancia)} km · {oferta.pasajeros} pasajeros` else ""
	sala.estado.Text = estado
	for i, plaza in sala.plazas do
		plaza.BackgroundColor3 = if i <= ocupadas then sala.estado.TextColor3 else APAGADO
	end
end

local function jornadaGrupo(grupo: { Player }): number
	local n = 1
	for _, jugador in grupo do
		local ok, valor = pcall(jornadas.GetAsync, jornadas, tostring(jugador.UserId))
		if ok and typeof(valor) == "number" then
			n = math.max(n, valor)
		end
	end
	return math.clamp(math.floor(n), 1, Config.RITMO.MAX_JORNADA)
end

local function guardarJornada()
	for _, jugador in Players:GetPlayers() do
		pcall(jornadas.SetAsync, jornadas, tostring(jugador.UserId), jornada, 3600)
	end
end

local function despegarGrupo(contrato: Contratos.Contrato, grupo: { Player }): boolean
	local ok, codigo, id = pcall(TeleportService.ReserveServer, TeleportService, game.PlaceId)
	if not ok then
		return false
	end
	local nivel = jornadaGrupo(grupo)
	local guardado = pcall(function()
		vuelos:SetAsync(id, HttpService:JSONEncode({ contrato = contrato, jugadores = #grupo, jornada = nivel }), 1800)
	end)
	if not guardado then
		return false
	end
	local opciones = Instance.new("TeleportOptions")
	opciones.ReservedServerAccessCode = codigo
	for _, jugador in grupo do
		saliendo[jugador] = true
	end
	local enviado = pcall(TeleportService.TeleportAsync, TeleportService, game.PlaceId, grupo, opciones)
	if not enviado then
		for _, jugador in grupo do
			saliendo[jugador] = nil
		end
	end
	return enviado
end

local function enLobby(): Contratos.Contrato
	fase("Aeropuerto")
	resultado = nil
	aeropuerto.Parent = Workspace
	spawnAeropuerto.Enabled = true
	spawnAvion.Enabled = false
	Avion.prepararTierra()
	publicarOfertas()
	Estado:SetAttribute("Cuenta", 0)
	while true do
		if RunService:IsStudio() and Workspace:GetAttribute("PruebaPreparacion") == true then
			Workspace:SetAttribute("PruebaPreparacion", nil)
			return Preparacion.conCocodrilo(Contratos.generar(rng, ciudad))
		end
		for n, sala in salas do
			local oferta = ofertas[n]
			local grupo = Salas.actualizar(n, saliendo)
			if not oferta or #grupo == 0 then
				sala.fin = nil
				pintarSala(sala, oferta, 0, "ESPERANDO")
				Salas.publicar(n, 0)
				continue
			end
			if Salas.pidioSalir(n) then
				sala.fin = math.min(sala.fin or math.huge, os.clock() + Config.LOBBY.CUENTA_CAPITAN)
			elseif not sala.fin and #grupo >= Config.LOBBY.MAX then
				sala.fin = os.clock() + Config.LOBBY.CUENTA
			end
			local fin = sala.fin
			if not fin then
				pintarSala(sala, oferta, #grupo, Salas.estado(n) or "ESPERANDO")
				Salas.publicar(n, 0)
				continue
			end
			local quedan = math.max(0, math.ceil(fin - os.clock()))
			pintarSala(sala, oferta, #grupo, `SALE EN {quedan}`)
			Salas.publicar(n, quedan)
			if quedan > 0 then
				continue
			end
			sala.fin = nil
			pintarSala(sala, oferta, #grupo, "EMBARCANDO")
			Salas.vaciar(n)
			Rafagas.lanzar("Onda", sala.centro.Position, 1.6, COLORES_SALA[n])
			Rafagas.lanzar("Confeti", sala.centro.Position + Vector3.new(0, 3, 0), 1.4)
			if RunService:IsStudio() then
				return oferta
			end
			if despegarGrupo(oferta, grupo) then
				ofertas[n] = Contratos.generar(rng, ciudad)
				Estado:SetAttribute("Contratos", HttpService:JSONEncode(ofertas))
			else
				for _, jugador in grupo do
					RemotoAviso:FireClient(jugador, "No se ha podido despegar. Volved a entrar en el círculo.", "peligro")
				end
			end
		end
		task.wait(0.25)
	end
end

local function leerVuelo(): (Contratos.Contrato?, number, number)
	for _ = 1, 10 do
		local ok, valor = pcall(vuelos.GetAsync, vuelos, game.PrivateServerId)
		if ok and typeof(valor) == "string" then
			local datos = HttpService:JSONDecode(valor)
			local nivel = if typeof(datos.jornada) == "number" then math.clamp(math.floor(datos.jornada), 1, Config.RITMO.MAX_JORNADA) else 1
			return datos.contrato, datos.jugadores, nivel
		end
		task.wait(1)
	end
	return nil, 1, 1
end

local function esperarGrupo(esperados: number)
	while #Players:GetPlayers() == 0 do
		task.wait(0.5)
	end
	local limite = os.clock() + Config.LOBBY.ESPERA_GRUPO
	while #Players:GetPlayers() < esperados and os.clock() < limite do
		task.wait(0.5)
	end
end

local function volverAlLobby()
	while #Players:GetPlayers() > 0 do
		pcall(TeleportService.TeleportAsync, TeleportService, game.PlaceId, Players:GetPlayers())
		task.wait(10)
	end
end

local function embarque(contrato: Contratos.Contrato, preparado: boolean)
	fase("Embarque")
	local R = Config.RITMO
	contrato.pasajeros += (jornada - 1) * R.PASAJEROS_POR_JORNADA
	contrato.pagoPasajero = math.floor(contrato.pagoPasajero * (1 + R.PAGO_POR_JORNADA * (jornada - 1)))
	Estado:SetAttribute("Jornada", jornada)
	Estado:SetAttribute("Contrato", HttpService:JSONEncode(contrato))
	Tienda.aplicar()
	local combustible = Avion.estado.combustible
	Avion.embarque(contrato.distancia)
	if preparado then
		Avion.estado.combustible = combustible
	end
	Cabina.reiniciar()
	Estado:SetAttribute("Condicion", contrato.condicion)
	Pasajeros.embarcar(contrato.pasajeros, contrato.riesgo, contrato.condicion)
	if preparado then
		aviso(`¡Embarque! Meted las maletas del carro en la bodega (y pasadlas por el escáner de aduanas). Destino: {contrato.destino}`, "info")
	else
		Vehiculos.reiniciar()
		Carga.cargar(contrato)
		aviso(`¡Embarque! Llevad el carro con el tractor, pasad las maletas por el escáner de aduanas y metedlas en la bodega. Destino: {contrato.destino}`, "info")
	end
	if jornada > 1 then
		task.delay(6, aviso, `Jornada {jornada}: más pasajeros, más caos y mejor paga`, "info")
	end
	listos = false
	local p = avisoListos
	if p then
		p.Enabled = true
	end
	for t = Config.PARTIDA.EMBARQUE, 1, -1 do
		Estado:SetAttribute("Cuenta", t)
		task.wait(1)
		if listos then
			break
		end
	end
	if p then
		p.Enabled = false
	end
	Estado:SetAttribute("Cuenta", 0)
end

local function vuelo(contrato: Contratos.Contrato)
	Carga.dejarEnTierra()
	Pasajeros.resentar()
	meterJugadores()
	Avion.despegar()
	task.wait(2.3)
	meterJugadores()
	aeropuerto.Parent = ServerStorage
	spawnAvion.Enabled = true
	spawnAeropuerto.Enabled = false
	fase("Vuelo")
	Estadisticas.reiniciar()
	Tienda.aplicar()
	Peligros.activar(contrato)
	aviso("¡A despegar! El piloto: siéntate en la cabina, acelera (Shift) y sube (W)", "info")
	local inicio = os.clock()
	local forzado = false
	while not resultado do
		if not forzado and Avion.fase() == "Despegue" and os.clock() - inicio > Config.PARTIDA.DESPEGUE_AUTO then
			forzado = true
			Avion.forzarDespegue()
			aviso(if Avion.piloto() then "El piloto automático ayuda con el despegue" else "Nadie pilota... el piloto automático despega por vosotros", "info")
		end
		task.wait(0.25)
	end
end

local function cobrar(contrato: Contratos.Contrato, tipo: string, motivo: string)
	local entregados, perdidos, satisfaccion, servidos = Pasajeros.resumen()
	local intacto, entregado, perdidoCarga, cocodrilo = Carga.resumen()
	local confiscados, contrabando = Carga.aduana()
	local casco = Avion.estado.casco
	local caos = if tipo == "Estrellado" then 0 else Caos.bonus()
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
		confiscados = confiscados,
		contrabando = contrabando,
		bonusAduana = Aduana.BONUS,
		multaAduana = Aduana.MULTA,
		premios = Estadisticas.premios(),
		caos = caos,
	}
	local total = caos
	if tipo == "Aterrizado" then
		local billetes = entregados * contrato.pagoPasajero * (0.4 + 0.6 * satisfaccion)
		local bonus = if datos.aterrizaje == "Perfecto" then 150 elseif datos.aterrizaje == "Bueno" then 60 else 0
		total += billetes + intacto + entregado * 1.5 + bonus + Piratas.bonus() + confiscados * Aduana.BONUS - contrabando * Aduana.MULTA - perdidos * contrato.multaPasajero - perdidoCarga * 0.5 - (100 - casco) * 3
		datos.billetes = math.floor(billetes)
		datos.bonus = bonus
	elseif tipo == "Rescatado" then
		local billetes = entregados * contrato.pagoPasajero * (0.4 + 0.6 * satisfaccion) * Config.ISLA.PAGO
		total += billetes + Config.ISLA.BONUS_RESCATE + Piratas.bonus() - perdidos * contrato.multaPasajero * 0.5
		datos.billetes = math.floor(billetes)
		datos.rescate = Config.ISLA.BONUS_RESCATE
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
	if tipo ~= "Estrellado" then
		jornada = math.min(jornada + 1, Config.RITMO.MAX_JORNADA)
	end
	if esPartida then
		task.spawn(guardarJornada)
	end
	if total > 0 then
		for _, jugador in jugadores do
			local raiz = Personajes.raiz(jugador)
			if raiz then
				Rafagas.lanzar("Monedas", raiz.Position + Vector3.new(0, 3, 0), 1.2)
			end
		end
	end
end

local function limpiar()
	Peligros.detener()
	Piratas.reiniciar()
	Agarre.soltarTodo()
	Pasajeros.limpiar()
	Carga.limpiar()
	Objetos.limpiar()
	Interacciones.limpiar()
	Cabina.reiniciar()
	Estado:SetAttribute("Condicion", "")
	Workspace.Gravity = Config.GRAVEDAD
end

local function naufragio(contrato: Contratos.Contrato, motivo: string)
	Roturas.esperar()
	Peligros.detener()
	Piratas.reiniciar()
	Workspace.Gravity = Config.GRAVEDAD
	fase("Isla")
	aviso(motivo, "peligro")
	task.wait(0.5)
	local rescatados = Isla.jugar()
	fase("Resultados")
	if rescatados then
		cobrar(contrato, "Rescatado", "Rescatados en la isla")
	else
		cobrar(contrato, "Estrellado", "Nadie vino a por vosotros")
	end
	task.wait(Config.PARTIDA.RESULTADOS)
	Isla.limpiar()
	limpiar()
	Avion.reparar()
end

local function jugar(contrato: Contratos.Contrato)
	embarque(contrato, Preparacion.jugar(contrato))
	vuelo(contrato)
	local r = resultado :: { tipo: string, motivo: string }
	if r.tipo == "Estrellado" then
		naufragio(contrato, r.motivo)
		return
	end
	fase("Resultados")
	ciudad = contrato.destino
	cobrar(contrato, r.tipo, r.motivo)
	task.wait(Config.PARTIDA.RESULTADOS)
	limpiar()
	Avion.reparar()
end

local function bucle()
	if esPartida then
		spawnAvion.Enabled = true
		spawnAeropuerto.Enabled = false
		Avion.prepararTierra()
		local leido, esperados, nivel = leerVuelo()
		jornada = nivel
		local contrato = leido or Contratos.generar(rng, ciudad)
		ciudad = contrato.origen
		Estado:SetAttribute("Contrato", HttpService:JSONEncode(contrato))
		fase("Embarque")
		esperarGrupo(esperados)
		meterJugadores()
		jugar(contrato)
		volverAlLobby()
		return
	end
	prepararSalas()
	while true do
		if RunService:IsStudio() and Workspace:GetAttribute("PruebaIsla") == true then
			Workspace:SetAttribute("PruebaIsla", nil)
			while #Players:GetPlayers() == 0 do
				task.wait(0.5)
			end
			task.wait(3)
			local contrato = Contratos.generar(rng, ciudad)
			Estado:SetAttribute("Contrato", HttpService:JSONEncode(contrato))
			Pasajeros.embarcar(contrato.pasajeros, contrato.riesgo, contrato.condicion)
			aeropuerto.Parent = ServerStorage
			spawnAvion.Enabled = true
			spawnAeropuerto.Enabled = false
			meterJugadores()
			naufragio(contrato, "Prueba de isla")
		else
			local contrato = enLobby()
			meterJugadores()
			jugar(contrato)
		end
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

local function prepararListos()
	local asiento = avion:FindFirstChild("AsientoPiloto", true)
	if not asiento or not asiento:IsA("BasePart") then
		return
	end
	local p = Instance.new("ProximityPrompt")
	p.ActionText = "Despegar ya"
	p.ObjectText = "Terminar el embarque"
	p.KeyboardKeyCode = Enum.KeyCode.E
	p.HoldDuration = 1.5
	p.MaxActivationDistance = 8
	p.RequiresLineOfSight = false
	p.Enabled = false
	p.Parent = asiento
	avisoListos = p
	p.Triggered:Connect(function(jugador)
		if Estado:GetAttribute("Fase") ~= "Embarque" or listos then
			return
		end
		listos = true
		aviso(`{jugador.DisplayName} da por terminado el embarque`, "info")
	end)
end

function Partida.iniciar()
	prepararListos()
	Avion.alTerminar(function(tipo, motivo)
		resultado = { tipo = tipo, motivo = motivo }
	end)
	Players.PlayerAdded:Connect(function(jugador)
		task.delay(6, function()
			if jugador.Parent and Estado:GetAttribute("Fase") ~= "Aeropuerto" then
				RemotoAviso:FireClient(jugador, "¡Bienvenido a bordo! Ayuda a la tripulación · H: controles", "info")
			end
		end)
	end)
	Personajes.alCaer(function(jugador)
		aviso(`¡{jugador.DisplayName} se ha caído del avión!`, "peligro")
	end)
	task.spawn(bucle)
end

return Partida
