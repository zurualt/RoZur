--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Contratos = require(ReplicatedStorage.Shared.Contratos)
local Estadisticas = require(script.Parent.Estadisticas)
local Mejoras = require(script.Parent.Mejoras)
local Sonidos = require(script.Parent.Sonidos)
local Rafagas = require(script.Parent.Rafagas)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoPiloto = Remotos:WaitForChild("Piloto") :: UnreliableRemoteEvent
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local RemotoPulsar = Remotos:WaitForChild("Pulsar") :: RemoteEvent

local V = Config.VUELO

type Motor = {
	vida: number,
	fuego: boolean,
	parte: BasePart?,
	efectos: { ParticleEmitter },
	extincion: number,
}

export type Estado = {
	fase: string,
	altitud: number,
	velocidad: number,
	vertical: number,
	cabeceo: number,
	alabeo: number,
	desvio: number,
	gases: number,
	combustible: number,
	distancia: number,
	total: number,
	casco: number,
	enTierra: boolean,
	autopiloto: boolean,
	cinturones: boolean,
	turbulencia: number,
	viento: number,
	perdida: boolean,
	motores: { [string]: Motor },
}

local Avion = {}

local avion = Workspace:WaitForChild("Avion") :: Model
local cabina = avion:WaitForChild("Cabina") :: Folder
local bodega = avion:WaitForChild("Bodega") :: Folder
local exterior = avion:WaitForChild("Exterior") :: Folder
local asientoPiloto = cabina:WaitForChild("AsientoPiloto") :: Seat
local rampa = bodega:WaitForChild("Rampa") :: BasePart

local estado: Estado = {
	fase = "Aeropuerto",
	altitud = 0,
	velocidad = 0,
	vertical = 0,
	cabeceo = 0,
	alabeo = 0,
	desvio = 0,
	gases = 0,
	combustible = 100,
	distancia = 0,
	total = 1000,
	casco = 100,
	enTierra = true,
	autopiloto = false,
	cinturones = true,
	turbulencia = 0,
	viento = 0,
	perdida = false,
	motores = {
		Izq = { vida = 100, fuego = false, parte = nil, efectos = {}, extincion = 0 },
		Der = { vida = 100, fuego = false, parte = nil, efectos = {}, extincion = 0 },
	},
}
Avion.estado = estado

local piloto: Player? = nil
local entrada = { cabeceo = 0, alabeo = 0, gases = 0, momento = 0 }
local alTerminar: { (string, string) -> () } = {}
local rng = Random.new()
local anguloRampa = Instance.new("NumberValue")
anguloRampa.Value = -90
local enfriamientos: { [string]: number } = {}
local ultimoAtributo: { [string]: any } = {}
local terminado = false
local forzado = false
local pausado = false
local pausaHasta = 0
local pruebaDestino = false

local function atributo(nombre: string, valor: any)
	if ultimoAtributo[nombre] ~= valor then
		ultimoAtributo[nombre] = valor
		avion:SetAttribute(nombre, valor)
	end
end

local function aviso(texto: string, tipo: string?)
	RemotoAviso:FireAllClients(texto, tipo or "info")
end

local function colocarRampa()
	local largo = rampa:GetAttribute("Largo")
	local l = if typeof(largo) == "number" then largo else 9.6
	rampa.CFrame = CFrame.new(0, Config.SUELO_Y - 0.4, 22.4) * CFrame.Angles(math.rad(anguloRampa.Value), 0, 0) * CFrame.new(0, 0, l / 2)
end

function Avion.rampa(abierta: boolean)
	local objetivo = if not abierta then -90 elseif estado.enTierra and estado.fase ~= "Despegue" then 48 else 12
	rampa:SetAttribute("Abierta", abierta)
	atributo("RampaAbierta", abierta)
	TweenService:Create(anguloRampa, TweenInfo.new(2.2, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut), { Value = objetivo }):Play()
end

local bisagras: { [BasePart]: { cerrada: CFrame, valor: NumberValue, signo: number } } = {}

local function bisagra(parte: BasePart)
	local b = bisagras[parte]
	if b then
		return b
	end
	local cerrada = parte.CFrame
	local medio = parte.Size.X / 2
	local eje = cerrada * CFrame.new(medio, 0, 0)
	local function en(a: number): CFrame
		return eje * CFrame.Angles(0, a, 0) * CFrame.new(-medio, 0, 0)
	end
	local angulo = math.rad(100)
	local signo = if math.abs(en(angulo).Position.X) > math.abs(en(-angulo).Position.X) then 1 else -1
	local valor = Instance.new("NumberValue")
	valor.Changed:Connect(function(v)
		parte.CFrame = en(v * signo * angulo)
	end)
	local nueva = { cerrada = cerrada, valor = valor, signo = signo }
	bisagras[parte] = nueva
	return nueva
end

local function puerta(parte: BasePart, abierta: boolean)
	if parte:GetAttribute("Abierta") == abierta and bisagras[parte] then
		return
	end
	parte:SetAttribute("Abierta", abierta)
	Sonidos.emitir(if abierta then "PuertaAbrir" else "PuertaCerrar", parte.Position, 0.1)
	local b = bisagra(parte)
	parte.CanCollide = false
	parte.CanQuery = not abierta
	local tween = TweenService:Create(b.valor, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Value = if abierta then 1 else 0 })
	tween.Completed:Connect(function(estadoTween)
		if estadoTween == Enum.PlaybackState.Completed then
			parte.CanCollide = not (parte:GetAttribute("Abierta") == true)
		end
	end)
	tween:Play()
	local aviso = parte:FindFirstChildOfClass("ProximityPrompt")
	if aviso then
		aviso.ActionText = if abierta then "Cerrar" else "Abrir"
	end
end
Avion.puerta = puerta

function Avion.puertas(abiertas: boolean)
	for _, d in avion:GetDescendants() do
		if d:IsA("BasePart") and d:GetAttribute("Puerta") and not d:GetAttribute("Interior") then
			puerta(d, abiertas)
		end
	end
end

local function tren(visible: boolean)
	local carpeta = exterior:FindFirstChild("Tren")
	if not carpeta then
		return
	end
	for _, d in carpeta:GetDescendants() do
		if d:IsA("BasePart") then
			d.Transparency = if visible then 0 else 1
			d.CanCollide = visible
		end
	end
end

local function efectosMotor(lado: string)
	local m = estado.motores[lado]
	for _, e in m.efectos do
		e.Enabled = m.fuego
	end
	atributo("Motor" .. lado .. "Fuego", m.fuego)
end

function Avion.danar(cantidad: number)
	estado.casco = math.clamp(estado.casco - cantidad * (1 - 0.12 * Mejoras.nivel("Casco")), 0, 100)
end

function Avion.danarMotor(lado: string, cantidad: number, fuego: boolean)
	local m = estado.motores[lado]
	m.vida = math.clamp(m.vida - cantidad, 0, 100)
	if fuego then
		m.fuego = true
		m.extincion = 0
	end
	efectosMotor(lado)
end

function Avion.extinguirMotor(lado: string, cantidad: number): boolean
	local m = estado.motores[lado]
	if not m.fuego then
		return false
	end
	m.extincion += cantidad
	if m.extincion >= 100 then
		m.fuego = false
		m.extincion = 0
		efectosMotor(lado)
		aviso(`¡Fuego del motor {if lado == "Izq" then "izquierdo" else "derecho"} apagado!`, "bien")
		return true
	end
	return false
end

function Avion.repararMotor(lado: string, cantidad: number): boolean
	local m = estado.motores[lado]
	if m.fuego or m.vida >= 100 then
		return false
	end
	m.vida = math.min(100, m.vida + cantidad)
	return true
end

function Avion.motorParte(lado: string): BasePart?
	return estado.motores[lado].parte
end

function Avion.desconectarAutopiloto(motivo: string?)
	if estado.autopiloto then
		estado.autopiloto = false
		aviso(motivo or "¡Piloto automático desconectado!", "peligro")
	end
end

function Avion.forzarDespegue()
	forzado = true
	estado.autopiloto = true
end

function Avion.piloto(): Player?
	return piloto
end

function Avion.alTerminar(f: (string, string) -> ())
	table.insert(alTerminar, f)
end

local function terminar(resultado: string, motivo: string)
	if terminado then
		return
	end
	terminado = true
	estado.fase = if resultado == "Estrellado" then "Estrellado" else "Aterrizado"
	for _, f in alTerminar do
		task.spawn(f, resultado, motivo)
	end
end

function Avion.prepararTierra()
	terminado = false
	estado.fase = "Aeropuerto"
	estado.altitud = 0
	estado.velocidad = 0
	estado.vertical = 0
	estado.cabeceo = 0
	estado.alabeo = 0
	estado.desvio = 0
	estado.gases = 0
	estado.enTierra = true
	estado.perdida = false
	estado.turbulencia = 0
	estado.autopiloto = false
	tren(true)
	Avion.rampa(true)
	Avion.puertas(true)
end

function Avion.reparar()
	estado.casco = 100
	estado.combustible = 100
	for lado, m in estado.motores do
		m.vida = 100
		m.fuego = false
		m.extincion = 0
		efectosMotor(lado)
	end
end

function Avion.embarque(total: number)
	estado.fase = "Embarque"
	estado.distancia = 0
	estado.total = total
	estado.cinturones = true
	Avion.reparar()
	if not pruebaDestino then
		avion:SetAttribute("PruebaBioma", nil)
	end
end

function Avion.despegar()
	terminado = false
	forzado = false
	pausado = false
	pausaHasta = 0
	avion:SetAttribute("Pausa", nil)
	avion:SetAttribute("Aterrizaje", "")
	estado.fase = "Despegue"
	estado.enTierra = true
	estado.velocidad = 0
	estado.gases = 0
	Avion.puertas(false)
	Avion.rampa(false)
end

function Avion.fase(): string
	return estado.fase
end

function Avion.restante(): number
	return estado.total - estado.distancia
end

function Avion.zonaEntrega(): boolean
	local f = estado.distancia / math.max(estado.total, 1)
	return not estado.enTierra and f >= V.ENTREGA_INICIO and f <= V.ENTREGA_FIN
end

local function autopiloto(): (number, number, number)
	if estado.enTierra then
		return if estado.velocidad > V.VELOCIDAD_DESPEGUE then 0.7 else 0, 0, 1
	end
	local errorAltitud = V.ALTITUD_CRUCERO - estado.altitud
	local cabeceo = math.clamp(errorAltitud / 1500, -0.45, 0.55)
	local alabeo = math.clamp(-estado.desvio / 18 - estado.alabeo / 60, -0.8, 0.8)
	return cabeceo, alabeo, 0.82
end

local function aproximar(actual: number, objetivo: number, velocidad: number, dt: number): number
	local paso = velocidad * dt
	if math.abs(objetivo - actual) <= paso then
		return objetivo
	end
	return actual + math.sign(objetivo - actual) * paso
end

local function polvoTren(escala: number)
	local carpeta = exterior:FindFirstChild("Tren")
	if carpeta then
		for _, d in carpeta:GetDescendants() do
			if d:IsA("BasePart") and d.Name == "Rueda" then
				Rafagas.lanzar("Polvo", d.Position - Vector3.new(0, d.Size.Y / 2, 0), escala)
			end
		end
	end
end

local function tocarSuelo()
	local restante = Avion.restante()
	local vertical = estado.vertical
	estado.altitud = 0
	estado.enTierra = true
	estado.vertical = 0
	if estado.fase == "Aproximacion" and math.abs(restante) <= V.PISTA then
		if vertical >= -V.VERTICAL_ATERRIZAJE and estado.velocidad <= V.VELOCIDAD_ATERRIZAJE and math.abs(estado.alabeo) < 15 then
			avion:SetAttribute("Aterrizaje", if vertical >= -V.VERTICAL_ATERRIZAJE * 0.5 then "Perfecto" else "Bueno")
			polvoTren(1)
			if avion:GetAttribute("Aterrizaje") == "Perfecto" then
				Rafagas.lanzar("Confeti", Config.CENTRO_AVION, 1.3)
			end
			aviso("¡Aterrizaje completado!", "bien")
		elseif vertical >= -V.VERTICAL_ATERRIZAJE * 2.2 and estado.velocidad <= V.VELOCIDAD_ATERRIZAJE * 1.35 then
			avion:SetAttribute("Aterrizaje", "Duro")
			polvoTren(2)
			Rafagas.lanzar("Onda", Vector3.new(0, 90.5, -20), 1.6)
			Avion.danar(25)
			aviso("¡Aterrizaje duro! Daños en el casco", "peligro")
			avion:SetAttribute("Golpe", os.clock())
		else
			terminar("Estrellado", "Aterrizaje demasiado brusco")
			return
		end
		estado.fase = "Frenando"
	else
		terminar("Estrellado", if estado.fase == "Aproximacion" then "Aterrizaje fuera de la pista" else "Nos hemos estrellado")
	end
end

local function saltarAproximacion()
	pruebaDestino = false
	estado.fase = "Vuelo"
	estado.enTierra = false
	tren(false)
	estado.altitud = 1800
	estado.vertical = 0
	estado.cabeceo = 0
	estado.alabeo = 0
	estado.velocidad = 480
	estado.gases = 0.55
	estado.autopiloto = false
	estado.distancia = math.max(0, estado.total - V.APROXIMACION - 60)
end

local function simular(dt: number)
	local fase = estado.fase
	if fase ~= "Despegue" and fase ~= "Vuelo" and fase ~= "Aproximacion" and fase ~= "Frenando" then
		return
	end
	if pruebaDestino and fase ~= "Frenando" then
		saltarAproximacion()
		fase = estado.fase
	end
	if pausaHasta > 0 then
		if os.clock() < pausaHasta then
			return
		end
		pausaHasta = 0
		avion:SetAttribute("Pausa", nil)
	end
	if not pausado and not estado.enTierra and (fase == "Vuelo" or fase == "Aproximacion") and estado.vertical < -20 and estado.altitud > 0 and estado.altitud / -estado.vertical < 2.4 then
		pausado = true
		pausaHasta = os.clock() + 1.5
		avion:SetAttribute("Pausa", true)
		return
	end
	if fase == "Frenando" then
		estado.velocidad = aproximar(estado.velocidad, 0, 90, dt)
		estado.cabeceo = aproximar(estado.cabeceo, 0, V.VEL_CABECEO, dt)
		estado.alabeo = aproximar(estado.alabeo, 0, V.VEL_ALABEO, dt)
		if estado.velocidad <= 0 then
			terminar("Aterrizado", "Aterrizaje completado")
		end
		return
	end
	local cab, ala, gas
	local ahora = os.clock()
	if piloto and not estado.enTierra then
		Estadisticas.sumar(piloto, "pilotar", dt)
	end
	if piloto and ahora - entrada.momento < 0.6 then
		cab, ala, gas = entrada.cabeceo, entrada.alabeo, entrada.gases
		if estado.autopiloto and not (forzado and estado.fase == "Despegue") and (math.abs(cab) > 0.2 or math.abs(ala) > 0.2) then
			Avion.desconectarAutopiloto("Piloto automático desconectado por el piloto")
		end
		if estado.autopiloto then
			cab, ala, gas = autopiloto()
		end
	elseif estado.autopiloto then
		cab, ala, gas = autopiloto()
	else
		cab, ala, gas = if estado.enTierra then 0 else -0.18, 0, estado.gases
	end
	estado.gases = math.clamp(gas, 0, 1)

	local factor = 0
	for _, m in estado.motores do
		if m.vida > 0 then
			factor += 0.5
		end
		if m.fuego then
			m.vida = math.max(0, m.vida - 2.2 * dt)
			Avion.danar(0.25 * dt)
		end
	end
	if estado.combustible <= 0 then
		factor = 0
	end
	estado.combustible = math.max(0, estado.combustible - estado.gases * V.CONSUMO * (1 - 0.12 * Mejoras.nivel("Combustible")) * dt)

	estado.perdida = not estado.enTierra and estado.velocidad < V.VELOCIDAD_PERDIDA
	local objetivoCabeceo = cab * V.CABECEO_MAX
	if estado.perdida then
		objetivoCabeceo = -14
	end
	if estado.enTierra then
		objetivoCabeceo = if estado.velocidad >= V.VELOCIDAD_DESPEGUE then math.max(objetivoCabeceo, 0) else 0
	end
	estado.cabeceo = aproximar(estado.cabeceo, objetivoCabeceo, V.VEL_CABECEO, dt)
	estado.alabeo = aproximar(estado.alabeo, if estado.enTierra then 0 else ala * V.ALABEO_MAX, V.VEL_ALABEO, dt)

	estado.viento = math.clamp(estado.viento + rng:NextNumber(-1, 1) * (0.5 + estado.turbulencia * 2) * dt, -1.6, 1.6)
	if not estado.enTierra then
		estado.desvio = math.clamp(estado.desvio + (estado.alabeo * V.GIRO + estado.viento) * dt, -90, 90)
	end

	local objetivoVelocidad = estado.gases * V.VELOCIDAD_MAX * factor - estado.cabeceo * 6
	if estado.enTierra and estado.gases < 0.05 then
		objetivoVelocidad = 0
	end
	estado.velocidad = math.max(0, aproximar(estado.velocidad, objetivoVelocidad, V.ACELERACION, dt))

	if estado.enTierra then
		if estado.velocidad >= V.VELOCIDAD_DESPEGUE and estado.cabeceo > 2 then
			estado.enTierra = false
			tren(false)
			if estado.fase == "Despegue" then
				estado.fase = "Vuelo"
				forzado = false
				aviso("¡Hemos despegado! Rumbo al destino", "bien")
			end
		end
	else
		estado.vertical = estado.velocidad / 3.6 * math.sin(math.rad(estado.cabeceo)) * V.FACTOR_VERTICAL
		estado.altitud = math.min(V.ALTITUD_MAX, estado.altitud + estado.vertical * dt)
		local avance = estado.velocidad / 3600 * V.COMPRESION * math.cos(math.rad(estado.desvio)) * dt
		estado.distancia += math.max(0, avance)
		if estado.fase == "Vuelo" and Avion.restante() <= V.APROXIMACION then
			estado.fase = "Aproximacion"
			Avion.desconectarAutopiloto("¡Aproximación! Aterrizaje manual: baja y reduce velocidad")
		end
		if estado.fase == "Aproximacion" and Avion.restante() < -V.PISTA then
			estado.distancia -= 70
			aviso("¡Nos hemos pasado la pista! Damos la vuelta", "peligro")
		end
		if estado.altitud <= 0 then
			tocarSuelo()
		end
	end
	if estado.casco <= 0 then
		terminar("Estrellado", "El avión se ha partido en el aire")
	end
end

local function publicar()
	atributo("Fase", estado.fase)
	atributo("Altitud", math.floor(estado.altitud))
	atributo("Velocidad", math.floor(estado.velocidad))
	atributo("Vertical", math.floor(estado.vertical * 10) / 10)
	atributo("Cabeceo", math.floor(estado.cabeceo * 10) / 10)
	atributo("Alabeo", math.floor(estado.alabeo * 10) / 10)
	atributo("Desvio", math.floor(estado.desvio))
	atributo("Gases", math.floor(estado.gases * 100))
	atributo("Combustible", math.floor(estado.combustible))
	atributo("Distancia", math.floor(estado.distancia))
	atributo("Total", estado.total)
	atributo("Casco", math.floor(estado.casco))
	atributo("MotorIzq", math.floor(estado.motores.Izq.vida))
	atributo("MotorDer", math.floor(estado.motores.Der.vida))
	atributo("Autopiloto", estado.autopiloto)
	atributo("Cinturones", estado.cinturones)
	atributo("Turbulencia", math.floor(estado.turbulencia * 100) / 100)
	atributo("Perdida", estado.perdida)
	atributo("EnTierra", estado.enTierra)
	atributo("ZonaEntrega", Avion.zonaEntrega())
	atributo("Piloto", if piloto then piloto.UserId else 0)
end

local botones: { [BasePart]: (Player, BasePart) -> () } = {}
local pulsaciones: { [Player]: number } = {}

local function boton(nombre: string, accion: string, objeto: string, duracion: number, f: (Player, BasePart) -> ())
	local parte = avion:FindFirstChild(nombre, true)
	if not parte or not parte:IsA("BasePart") then
		return
	end
	parte:SetAttribute("Accion", accion)
	parte:SetAttribute("Objeto", objeto)
	parte:SetAttribute("Duracion", duracion)
	CollectionService:AddTag(parte, "BotonMano")
	botones[parte] = f
end

local function pulsar(jugador: Player, parte: any)
	if typeof(parte) ~= "Instance" or not parte:IsA("BasePart") then
		return
	end
	local f = botones[parte]
	local personaje = jugador.Character
	local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	local ahora = os.clock()
	if not f or not raiz or not raiz:IsA("BasePart") or not humanoide or humanoide.Health <= 0 or (pulsaciones[jugador] or 0) > ahora then
		return
	end
	if (raiz.Position - parte.Position).Magnitude > 11 then
		return
	end
	pulsaciones[jugador] = ahora + 0.35
	Sonidos.emitir("Boton", parte.Position, 0.1)
	f(jugador, parte)
end

local function enfriado(clave: string, segundos: number): boolean
	local ahora = os.clock()
	if (enfriamientos[clave] or 0) > ahora then
		return false
	end
	enfriamientos[clave] = ahora + segundos
	return true
end

local function prepararControles()
	boton("BotonAutopiloto", "Activar", "Piloto automático", 0, function(_, parte)
		if estado.fase == "Aproximacion" then
			RemotoAviso:FireAllClients("En aproximación el aterrizaje es manual", "peligro")
			return
		end
		estado.autopiloto = not estado.autopiloto
		parte:SetAttribute("Accion", if estado.autopiloto then "Desactivar" else "Activar")
		RemotoAviso:FireAllClients(if estado.autopiloto then "Piloto automático activado" else "Piloto automático desactivado", "info")
	end)
	boton("BotonCinturones", "Cambiar", "Señal de cinturones", 0, function(_, parte)
		estado.cinturones = not estado.cinturones
		parte:SetAttribute("Accion", if estado.cinturones then "Apagar" else "Encender")
		RemotoAviso:FireAllClients(if estado.cinturones then "Abróchense los cinturones" else "Señal de cinturones apagada", "info")
	end)
	boton("BotonExtintorMotor", "Disparar", "Extintor de motores", 0, function()
		if not enfriado("ExtintorMotor", 40) then
			RemotoAviso:FireAllClients("El extintor de motores se está recargando", "info")
			return
		end
		local alguno = false
		for lado, m in estado.motores do
			if m.fuego then
				m.extincion = 100
				Avion.extinguirMotor(lado, 1)
				alguno = true
			end
		end
		if not alguno then
			RemotoAviso:FireAllClients("No hay fuego en los motores (extintor gastado)", "info")
		end
	end)
	boton("BotonMotores", "Reiniciar", "Motores", 2, function()
		if not enfriado("Motores", 20) then
			return
		end
		local alguno = false
		for _, m in estado.motores do
			if m.vida <= 0 and not m.fuego then
				m.vida = 35
				alguno = true
			end
		end
		RemotoAviso:FireAllClients(if alguno then "¡Motores reiniciados!" else "Los motores ya funcionan (o están ardiendo)", if alguno then "bien" else "info")
	end)
	local function alternarRampa()
		if enfriado("Rampa", 2.5) then
			Avion.rampa(not (rampa:GetAttribute("Abierta") == true))
		end
	end
	boton("BotonRampa", "Abrir/Cerrar", "Rampa de carga", 0, alternarRampa)
	boton("BotonRampaBodega", "Abrir/Cerrar", "Rampa de carga", 0, alternarRampa)
	for _, d in avion:GetDescendants() do
		if d:IsA("BasePart") and d:GetAttribute("Puerta") then
			local aviso = Instance.new("ProximityPrompt")
			aviso.ActionText = "Abrir"
			aviso.ObjectText = if d:GetAttribute("Interior") then "Baño" else "Puerta"
			aviso.MaxActivationDistance = 7
			aviso.RequiresLineOfSight = false
			aviso.Parent = d
			aviso.Triggered:Connect(function()
				if enfriado(d:GetFullName(), 0.8) then
					puerta(d, not (d:GetAttribute("Abierta") == true))
				end
			end)
		end
	end
end

local function prepararMotores()
	for lado, m in estado.motores do
		local parte = exterior:FindFirstChild("Motor" .. lado)
		if parte and parte:IsA("BasePart") then
			m.parte = parte
			local adjunto = Instance.new("Attachment")
			adjunto.Name = "Fuego"
			adjunto.Position = Vector3.new(0, 0, 0)
			adjunto.Parent = parte
			m.efectos = VFX.fuego(adjunto, 2.2)
			local plumas = VFX.plumas(adjunto)
			plumas.Name = "Plumas"
			for _, e in m.efectos do
				e.Enabled = false
			end
		end
	end
end

function Avion.plumas(lado: string)
	local parte = estado.motores[lado].parte
	local adjunto = parte and parte:FindFirstChild("Fuego")
	local emisor = adjunto and adjunto:FindFirstChild("Plumas")
	if emisor and emisor:IsA("ParticleEmitter") then
		emisor:Emit(90)
	end
end

function Avion.iniciar()
	anguloRampa.Changed:Connect(colocarRampa)
	colocarRampa()
	prepararMotores()
	prepararControles()
	RemotoPulsar.OnServerEvent:Connect(pulsar)
	Players.PlayerRemoving:Connect(function(jugador)
		pulsaciones[jugador] = nil
	end)

	asientoPiloto:GetPropertyChangedSignal("Occupant"):Connect(function()
		local ocupante = asientoPiloto.Occupant
		local nuevo = if ocupante then Players:GetPlayerFromCharacter(ocupante.Parent) else nil
		piloto = nuevo
		if nuevo then
			RemotoAviso:FireAllClients(`{nuevo.DisplayName} toma los mandos`, "info")
		end
	end)

	RemotoPiloto.OnServerEvent:Connect(function(jugador, cabeceo, alabeo, gases)
		if jugador ~= piloto or typeof(cabeceo) ~= "number" or typeof(alabeo) ~= "number" or typeof(gases) ~= "number" then
			return
		end
		if cabeceo ~= cabeceo or alabeo ~= alabeo or gases ~= gases then
			return
		end
		entrada.cabeceo = math.clamp(cabeceo, -1, 1)
		entrada.alabeo = math.clamp(alabeo, -1, 1)
		entrada.gases = math.clamp(gases, 0, 1)
		entrada.momento = os.clock()
	end)

	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		while acumulado >= V.TICK do
			acumulado -= V.TICK
			simular(V.TICK)
			publicar()
		end
	end)
	if RunService:IsStudio() then
		Workspace:GetAttributeChangedSignal("PruebaDestino"):Connect(function()
			local v = Workspace:GetAttribute("PruebaDestino")
			if typeof(v) ~= "string" or v == "" then
				return
			end
			Workspace:SetAttribute("PruebaDestino", nil)
			if not table.find(Contratos.BIOMAS, v) then
				warn(`[Overbooked] PruebaDestino desconocido: {v}`)
				return
			end
			avion:SetAttribute("PruebaBioma", v)
			pruebaDestino = true
		end)
	end
	Avion.prepararTierra()
end

return Avion
