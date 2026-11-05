--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")
local Debris = game:GetService("Debris")

local Config = require(ReplicatedStorage.Shared.Config)
local Contratos = require(ReplicatedStorage.Shared.Contratos)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Agarre = require(script.Parent.Agarre)
local Avion = require(script.Parent.Avion)
local Carga = require(script.Parent.Carga)
local Objetos = require(script.Parent.Objetos)
local Pasajeros = require(script.Parent.Pasajeros)
local Personajes = require(script.Parent.Personajes)
local Piratas = require(script.Parent.Piratas)
local Rafagas = require(script.Parent.Rafagas)
local Sonidos = require(script.Parent.Sonidos)
local Estadisticas = require(script.Parent.Estadisticas)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local RemotoSacudida = Remotos:WaitForChild("Sacudida") :: UnreliableRemoteEvent
local RemotoUsar = Remotos:WaitForChild("Usar") :: RemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder

type Fuego = { parte: BasePart, vida: number }
type Panel = { parte: BasePart, reparacion: number }
type Brecha = { parte: BasePart, ventana: Model, reparacion: number, originales: { [BasePart]: number }, viento: ParticleEmitter, tapon: BasePart?, sinTapon: number }

local Peligros = {}

local avion = Workspace:WaitForChild("Avion") :: Model
local carpeta = avion:WaitForChild("Peligros") :: Folder
local fuegos: { [BasePart]: Fuego } = {}
local brechas: { [BasePart]: Brecha } = {}
local paneles: { [BasePart]: Panel } = {}
local activo = false
local rng = Random.new()
local turbulenciaEvento = 0
local finTormenta = 0
local ultimoUso: { [Player]: number } = {}
local quemados: { [Player]: number } = {}
local generacion = 0
local riesgoActual = 1
local finCalma = math.huge
local alSacudir: { (number) -> () } = {}
local TAPONES = { Maleta = true, Caja = true, CajaFragil = true, Carrito = true, Bolso = true }

local function efecto(posicion: Vector3, crear: (Instance) -> ParticleEmitter, cantidad: number)
	local marca = Instance.new("Part")
	marca.Anchored = true
	marca.CanCollide = false
	marca.CanQuery = false
	marca.CanTouch = false
	marca.Transparency = 1
	marca.Size = Vector3.one
	marca.Position = posicion
	marca.Parent = carpeta
	crear(marca):Emit(cantidad)
	Debris:AddItem(marca, 2)
end

local PUNTOS_FUEGO = {
	Vector3.new(-4.6, 100.2, -48),
	Vector3.new(4.6, 100.2, -47),
	Vector3.new(0, 100.2, -38),
	Vector3.new(0, 100.2, -29),
	Vector3.new(0, 100.2, -16),
	Vector3.new(-1.5, 100.2, -10),
	Vector3.new(3, 100.2, 6),
	Vector3.new(-3, 100.2, 14),
}

local function aviso(texto: string, tipo: string)
	RemotoAviso:FireAllClients(texto, tipo)
end

local function sueltos(): { BasePart }
	local lista = Objetos.sueltos()
	for _, p in Carga.sueltos() do
		table.insert(lista, p)
	end
	return lista
end

function Peligros.alSacudir(f: (number) -> ())
	table.insert(alSacudir, f)
end

local function destapar(b: Brecha, disparado: boolean)
	local tapon = b.tapon
	b.tapon = nil
	b.parte:SetAttribute("Fuerza", 1)
	b.viento.Rate = 80
	if not tapon or not tapon.Parent then
		return
	end
	tapon:SetAttribute("Tapon", nil)
	tapon.Anchored = false
	Objetos.servidor(tapon)
	if disparado then
		Sonidos.emitir("Succion", b.parte.Position)
		b.sinTapon = os.clock() + 2
		tapon.AssemblyLinearVelocity = b.parte.CFrame.LookVector * 30 + Vector3.new(0, 10, 0)
		aviso("¡El tapón ha salido disparado!", "peligro")
	end
end

local function taponar(b: Brecha, objeto: BasePart)
	Agarre.soltarObjeto(objeto)
	local centro = b.parte.Position
	local dentro = b.parte.CFrame.LookVector
	objeto.Anchored = true
	objeto.AssemblyLinearVelocity = Vector3.zero
	objeto.CFrame = CFrame.lookAt(centro + dentro * (objeto.Size.Z / 2 + 0.05), centro + dentro * 4)
	objeto:SetAttribute("Tapon", true)
	Sonidos.emitir("GolpeFuerte", centro)
	b.tapon = objeto
	b.parte:SetAttribute("Fuerza", 0)
	b.viento.Rate = 6
	aviso("¡Agujero tapado! Repáralo con la llave antes de que salga disparado", "bien")
end

function Peligros.sacudida(magnitud: number)
	for _, p in sueltos() do
		local dir = Vector3.new(rng:NextNumber(-1, 1), rng:NextNumber(0.4, 1.3), rng:NextNumber(-1, 1))
		Objetos.empujar(p, dir * Config.TURBULENCIA.IMPULSO_OBJETOS * magnitud)
	end
	Pasajeros.sacudir(magnitud, Avion.estado.cinturones)
	Carga.danarJaula(magnitud * 6)
	RemotoSacudida:FireAllClients(magnitud)
	if magnitud > 0.65 then
		for _, b in brechas do
			if b.tapon and rng:NextNumber() < 0.3 then
				destapar(b, true)
			end
		end
	end
	for _, f in alSacudir do
		task.spawn(f, magnitud)
	end
	if magnitud > Config.TURBULENCIA.UMBRAL_RAGDOLL then
		for _, jugador in Players:GetPlayers() do
			if rng:NextNumber() < 0.45 then
				local dir = Vector3.new(rng:NextNumber(-1, 1), 0, rng:NextNumber(-1, 1))
				Personajes.ragdoll(jugador, 1.4, dir * 26 + Vector3.new(0, 22, 0))
			end
		end
	end
end

function Peligros.fuego(posicion: Vector3)
	local count = 0
	for _ in fuegos do
		count += 1
	end
	if count >= 5 then
		return
	end
	local parte = Instance.new("Part")
	parte.Name = "Fuego"
	parte.Size = Vector3.new(3, 0.4, 3)
	parte.Anchored = true
	parte.CanCollide = false
	parte.CanQuery = false
	parte.Transparency = 1
	parte.Position = posicion
	local adjunto = Instance.new("Attachment")
	adjunto.Parent = parte
	VFX.fuego(adjunto, 1)
	local luz = Instance.new("PointLight")
	luz.Color = Color3.fromRGB(255, 150, 60)
	luz.Brightness = 2
	luz.Range = 14
	luz.Parent = parte
	parte:SetAttribute("Vida", 100)
	CollectionService:AddTag(parte, "Fuego")
	parte.Parent = carpeta
	fuegos[parte] = { parte = parte, vida = 100 }
	Rafagas.lanzar("Humo", posicion, 0.7)
	Pasajeros.asustar(0.3, posicion, 16)
end

local function apagar(f: Fuego)
	fuegos[f.parte] = nil
	efecto(f.parte.Position, VFX.vapor, 14)
	Sonidos.emitir("Succion", f.parte.Position, 0.3)
	f.parte:Destroy()
end

function Peligros.mojar(posicion: Vector3, radio: number, cantidad: number): boolean
	local alguno = false
	for parte, f in fuegos do
		if (parte.Position - posicion).Magnitude <= radio + 1.5 then
			alguno = true
			f.vida -= cantidad
			parte:SetAttribute("Vida", math.max(0, f.vida))
			if f.vida <= 0 then
				apagar(f)
			end
		end
	end
	return alguno
end

function Peligros.brecha()
	local candidatas: { Model } = {}
	for _, d in avion:GetDescendants() do
		if d:IsA("Model") and d.Name == "Ventana" and d:GetAttribute("Rota") ~= true then
			table.insert(candidatas, d)
		end
	end
	if #candidatas == 0 then
		return
	end
	local ventana = candidatas[rng:NextInteger(1, #candidatas)]
	local originales: { [BasePart]: number } = {}
	local centro = Vector3.zero
	local n = 0
	for _, p in ventana:GetChildren() do
		if p:IsA("BasePart") then
			originales[p] = p.Transparency
			centro += p.Position
			n += 1
			p.CanCollide = false
			p.Transparency = 1
		end
	end
	if n == 0 then
		return
	end
	centro /= n
	ventana:SetAttribute("Rota", true)
	local marca = Instance.new("Part")
	marca.Name = "Brecha"
	marca.Size = Vector3.new(1, 3, 4.5)
	marca.Anchored = true
	marca.CanCollide = false
	marca.CanQuery = false
	marca.Transparency = 1
	marca.CFrame = CFrame.lookAt(centro, Vector3.new(0, centro.Y, centro.Z))
	local adjunto = Instance.new("Attachment")
	adjunto.CFrame = CFrame.Angles(0, math.pi, 0)
	adjunto.Parent = marca
	local viento = VFX.viento(adjunto)
	viento.Rate = 80
	local chispas = VFX.chispas(marca)
	chispas:Emit(40)
	Sonidos.emitir("Explosion", centro)
	Rafagas.lanzar("Escombros", centro, 1.2)
	Rafagas.lanzar("Onda", centro, 0.8)
	task.delay(0.25, Sonidos.emitir, "Succion", centro)
	marca:SetAttribute("Reparacion", 0)
	marca:SetAttribute("Fuerza", 1)
	CollectionService:AddTag(marca, "Brecha")
	marca.Parent = carpeta
	brechas[marca] = { parte = marca, ventana = ventana, reparacion = 0, originales = originales, viento = viento, tapon = nil, sinTapon = 0 }
	Avion.danar(5)
	aviso("¡AGUJERO EN EL FUSELAJE! Repáralo con la llave", "peligro")
	Pasajeros.asustar(0.5)
end

local function cerrar(b: Brecha, silencioso: boolean?)
	destapar(b, false)
	brechas[b.parte] = nil
	for p, t in b.originales do
		p.CanCollide = true
		p.Transparency = t
	end
	b.ventana:SetAttribute("Rota", false)
	b.parte:Destroy()
	if not silencioso then
		Sonidos.emitir("Reparado", b.parte.Position)
		Rafagas.lanzar("Chispas", b.parte.Position, 1.2)
		aviso("¡Agujero reparado!", "bien")
	end
end

local function panelSuelto()
	local n = 0
	for _ in paneles do
		n += 1
	end
	if n >= 2 then
		return
	end
	local z = rng:NextNumber(-40, 10)
	local x = rng:NextNumber(-1.5, 1.5)
	local parte = Instance.new("Part")
	parte.Name = "PanelSuelto"
	parte.Size = Vector3.new(2.6, 0.25, 2.2)
	parte.Color = Color3.fromRGB(233, 228, 214)
	parte.Material = Enum.Material.Metal
	parte.Anchored = true
	parte.CanCollide = false
	parte.CanQuery = false
	local bisagra = CFrame.new(x, 113.7, z - 1.1)
	parte.CFrame = bisagra * CFrame.new(0, 0, 1.1)
	local chispas = VFX.chispas(parte)
	chispas.Rate = 6
	parte:SetAttribute("Reparacion", 0)
	parte:SetAttribute("Bisagra", bisagra)
	CollectionService:AddTag(parte, "PanelSuelto")
	parte.Parent = carpeta
	paneles[parte] = { parte = parte, reparacion = 0 }
	Avion.danar(3)
	Sonidos.emitir("GolpeMetal", parte.Position)
	aviso("¡Panel suelto en el techo! Sal al ala, trepa con el piolet y clávalo a martillazos (F)", "peligro")
end

local function cerrarPanel(p: Panel, silencioso: boolean?)
	paneles[p.parte] = nil
	if not silencioso then
		Sonidos.emitir("Reparado", p.parte.Position)
		Rafagas.lanzar("Chispas", p.parte.Position, 1.2)
		aviso("¡Panel del techo arreglado!", "bien")
	end
	p.parte:Destroy()
end

local function pajaros()
	aviso("¡Bandada de pájaros delante!", "peligro")
	avion:SetAttribute("Bandada", os.clock())
	local miGeneracion = generacion
	task.delay(3, function()
		if not activo or generacion ~= miGeneracion then
			return
		end
		local lado = if rng:NextNumber() < 0.5 then "Izq" else "Der"
		Avion.danarMotor(lado, 35, true)
		Avion.danar(6)
		Avion.plumas(lado)
		local motor = Avion.motorParte(lado)
		if motor then
			Rafagas.lanzar("Plumas", motor.Position, 1.6)
			Rafagas.lanzar("ExplosionPequena", motor.Position, 1.2)
		end
		Avion.desconectarAutopiloto()
		avion:SetAttribute("Pajaros", os.clock())
		aviso(`¡Motor {if lado == "Izq" then "izquierdo" else "derecho"} en llamas!`, "peligro")
		Peligros.sacudida(0.85)
	end)
end

local function caidaLibre()
	aviso("¡Caída libre! Agarraos a algo", "peligro")
	Sonidos.emitir("PasajeroGrito", Config.CENTRO_AVION)
	Workspace.Gravity = 26
	Pasajeros.flotar(Avion.estado.cinturones)
	for _, p in sueltos() do
		Objetos.empujar(p, Vector3.new(rng:NextNumber(-4, 4), rng:NextNumber(10, 20), rng:NextNumber(-4, 4)))
	end
	avion:SetAttribute("CaidaLibre", true)
	local miGeneracion = generacion
	task.delay(6, function()
		if generacion == miGeneracion then
			Workspace.Gravity = Config.GRAVEDAD
			avion:SetAttribute("CaidaLibre", false)
			Peligros.sacudida(0.6)
		end
	end)
end

local function tormenta()
	aviso("¡Entramos en una tormenta!", "peligro")
	finTormenta = os.clock() + 32
	avion:SetAttribute("Tormenta", true)
end

local function falloMotor()
	local lado = if rng:NextNumber() < 0.5 then "Izq" else "Der"
	Avion.danarMotor(lado, 100, false)
	local motor = Avion.motorParte(lado)
	if motor then
		Rafagas.lanzar("Humo", motor.Position, 1.6, Color3.fromRGB(90, 86, 84))
	end
	aviso(`¡Motor {if lado == "Izq" then "izquierdo" else "derecho"} apagado! Reinícialo en la cabina`, "peligro")
end

local function turbulencias()
	aviso("¡Zona de turbulencias! Cinturones, por favor", "peligro")
	turbulenciaEvento = os.clock() + 18
end

local function fuegoAleatorio()
	local punto = PUNTOS_FUEGO[rng:NextInteger(1, #PUNTOS_FUEGO)]
	Peligros.fuego(punto)
	aviso("¡Fuego a bordo! Coge un extintor", "peligro")
end

local EVENTOS: { { f: () -> (), peso: number, riesgo: number } } = {
	{ f = turbulencias, peso = 4, riesgo = 1 },
	{ f = fuegoAleatorio, peso = 3, riesgo = 1 },
	{ f = pajaros, peso = 2, riesgo = 1 },
	{ f = Peligros.brecha, peso = 2, riesgo = 2 },
	{ f = caidaLibre, peso = 2, riesgo = 1 },
	{ f = tormenta, peso = 1, riesgo = 2 },
	{ f = falloMotor, peso = 1, riesgo = 2 },
	{ f = Piratas.lanzar, peso = 2, riesgo = 2 },
	{ f = panelSuelto, peso = 2, riesgo = 1 },
	{ f = Pasajeros.alborotar, peso = 2, riesgo = 1 },
	{
		f = function()
			Avion.desconectarAutopiloto()
		end,
		peso = 2,
		riesgo = 1,
	},
}

local PAGADOS: { [string]: () -> () } = { Pajaros = pajaros, CaidaLibre = caidaLibre, Piratas = Piratas.lanzar }

function Peligros.lanzar(nombre: string): boolean
	local f = PAGADOS[nombre]
	if not f or not activo then
		return false
	end
	f()
	return true
end

local function elegirEvento(graves: boolean): () -> ()
	local total = 0
	for _, e in EVENTOS do
		if e.riesgo == 1 or graves then
			total += e.peso
		end
	end
	local tirada = rng:NextNumber() * total
	for _, e in EVENTOS do
		if e.riesgo == 1 or graves then
			tirada -= e.peso
			if tirada <= 0 then
				return e.f
			end
		end
	end
	return turbulencias
end

function Peligros.jornada(): number
	local j = Estado:GetAttribute("Jornada")
	return math.clamp(if typeof(j) == "number" then j else 1, 1, Config.RITMO.MAX_JORNADA)
end

function Peligros.progreso(): number
	local estado = Avion.estado
	return math.clamp(estado.distancia / math.max(estado.total, 1), 0, 1)
end

function Peligros.calma(): boolean
	return os.clock() < finCalma
end

function Peligros.intensidad(): number
	local R = Config.RITMO
	local curva = R.INICIO + (R.FINAL - R.INICIO) * Peligros.progreso()
	local nivel = (1 + R.POR_RIESGO * (riesgoActual - 1)) * (1 + R.POR_JORNADA * (Peligros.jornada() - 1))
	return math.min(curva * nivel * (1 + R.POR_JUGADOR * (math.max(#Players:GetPlayers(), 1) - 1)), R.MAXIMA)
end

function Peligros.activar(contrato: Contratos.Contrato)
	Peligros.detener()
	generacion += 1
	activo = true
	riesgoActual = contrato.riesgo
	finCalma = math.huge
	local miGeneracion = generacion
	local R = Config.RITMO
	task.spawn(function()
		while activo and generacion == miGeneracion and Avion.estado.enTierra do
			task.wait(0.5)
		end
		finCalma = os.clock() + R.CALMA
		task.wait(R.CALMA)
		while activo and generacion == miGeneracion do
			local fase = Avion.fase()
			if fase == "Vuelo" or fase == "Aproximacion" then
				elegirEvento(Peligros.progreso() >= R.GRAVES or contrato.riesgo + Peligros.jornada() - 1 >= 3)()
			end
			task.wait(rng:NextNumber(Config.PARTIDA.INTERVALO_PELIGRO_MIN, Config.PARTIDA.INTERVALO_PELIGRO_MAX) / Peligros.intensidad())
		end
	end)
	task.spawn(function()
		while activo and generacion == miGeneracion do
			local estado = Avion.estado
			local ritmo = if Peligros.calma() then R.TURBULENCIA_CALMA else math.clamp(Peligros.intensidad(), 0.5, 1.6)
			local base = if estado.enTierra then 0 else (Config.TURBULENCIA.BASE + (contrato.riesgo - 1) * 0.05) * ritmo
			local extra = (if os.clock() < turbulenciaEvento then 0.6 else 0) + (if os.clock() < finTormenta then 0.45 else 0)
			if estado.perdida then
				extra += 0.4
			end
			estado.turbulencia = math.clamp(base + extra, 0, 1)
			if os.clock() >= finTormenta and avion:GetAttribute("Tormenta") then
				avion:SetAttribute("Tormenta", false)
			end
			local t = estado.turbulencia
			if t > 0.05 and not estado.enTierra then
				Peligros.sacudida(math.clamp(t * rng:NextNumber(0.5, 1.3), 0, 1))
			end
			task.wait(rng:NextNumber(0.6, 1.8) / (0.4 + t))
		end
	end)
end

function Peligros.detener()
	activo = false
	generacion += 1
	for _, f in fuegos do
		f.parte:Destroy()
	end
	table.clear(fuegos)
	for _, b in brechas do
		cerrar(b, true)
	end
	for _, p in paneles do
		cerrarPanel(p, true)
	end
	Workspace.Gravity = Config.GRAVEDAD
	Piratas.detener()
	turbulenciaEvento = 0
	finTormenta = 0
	avion:SetAttribute("Tormenta", false)
	avion:SetAttribute("CaidaLibre", false)
	Avion.estado.turbulencia = 0
end

local function frente(jugador: Player): (Vector3?, Vector3?)
	local raiz = Personajes.raiz(jugador)
	if not raiz then
		return nil, nil
	end
	local personaje = jugador.Character
	local cabeza = personaje and personaje:FindFirstChild("Head")
	local origen = if cabeza and cabeza:IsA("BasePart") then cabeza.Position else raiz.Position
	return origen, raiz.CFrame.LookVector
end

local function usarExtintor(jugador: Player, mirada: Vector3?)
	local objeto = Agarre.sostenido(jugador)
	if objeto then
		local boquilla = objeto:FindFirstChild("Boquilla")
		local rocio = boquilla and boquilla:FindFirstChild("Rocio")
		if rocio and rocio:IsA("ParticleEmitter") then
			rocio.Enabled = true
			local marca = os.clock()
			objeto:SetAttribute("Rociando", marca)
			task.delay(0.35, function()
				if objeto:GetAttribute("Rociando") == marca then
					rocio.Enabled = false
				end
			end)
		end
	end
	local origen, frontal = frente(jugador)
	if not origen or not frontal then
		return
	end
	Sonidos.emitir("Extintor", origen, 0.32)
	local dir = mirada or frontal
	local H = Config.HERRAMIENTAS
	for _, p in sueltos() do
		local delta = p.Position - origen
		local d = delta.Magnitude
		if d < H.ALCANCE_EXTINTOR and d > 0.1 and delta.Unit:Dot(dir) > 0.6 then
			Objetos.empujar(p, dir * 22 * (1 - d / H.ALCANCE_EXTINTOR))
		end
	end
	Pasajeros.rociar(origen, dir, H.ALCANCE_EXTINTOR)
	for _, c in CollectionService:GetTagged("Cocodrilo") do
		local cuerpo = if c:IsA("Model") then c.PrimaryPart else nil
		if cuerpo then
			local delta = cuerpo.Position - origen
			if delta.Magnitude < H.ALCANCE_EXTINTOR * 0.7 and delta.Unit:Dot(dir) > 0.6 then
				Carga.aturdir(1.2)
			end
		end
	end
	for parte, f in fuegos do
		local delta = parte.Position - origen
		local d = delta.Magnitude
		if d <= H.ALCANCE_EXTINTOR and (d < 3 or delta.Unit:Dot(dir) > 0.35) then
			f.vida -= H.DANO_EXTINTOR
			parte:SetAttribute("Vida", math.max(0, f.vida))
			if f.vida <= 0 then
				apagar(f)
				Estadisticas.sumar(jugador, "fuego")
			end
		end
	end
	for _, lado in { "Izq", "Der" } do
		local motor = Avion.motorParte(lado)
		if motor and (motor.Position - origen).Magnitude <= H.ALCANCE_EXTINTOR + 3 then
			if Avion.extinguirMotor(lado, 7) then
				Estadisticas.sumar(jugador, "fuego", 2)
			end
		end
	end
end

local function usarAgua(jugador: Player, mirada: Vector3?)
	local origen, frontal = frente(jugador)
	if not origen or not frontal then
		return
	end
	local dir = mirada or frontal
	local objeto = Agarre.sostenido(jugador)
	local punto = origen + dir * 3.5 + Vector3.new(0, -2, 0)
	if objeto and objeto:IsA("BasePart") and Peligros.mojar(punto, 3.5, 100) then
		Sonidos.emitir("Salpicadura", objeto.Position)
		Estadisticas.sumar(jugador, "fuego")
		efecto(objeto.Position, function(padre)
			return VFX.salpicadura(padre, Color3.fromRGB(143, 211, 244))
		end, 30)
		Agarre.consumir(jugador)
		RemotoAviso:FireClient(jugador, "¡Fuego apagado con agua!", "bien")
	end
end

local function usarPiolet(jugador: Player)
	local origen = frente(jugador)
	local raiz = Personajes.raiz(jugador)
	if not origen or not raiz or raiz.Position.Y < 111 then
		return
	end
	local H = Config.HERRAMIENTAS
	for parte, p in paneles do
		if (parte.Position - origen).Magnitude <= H.ALCANCE_PIOLET then
			Sonidos.emitir("GolpeMetal", parte.Position, 0.15)
			Rafagas.lanzar("Martillazo", parte.Position, 0.5)
			p.reparacion += H.REPARACION_PIOLET
			Estadisticas.sumar(jugador, "reparar")
			parte:SetAttribute("Reparacion", math.min(100, p.reparacion))
			if p.reparacion >= 100 then
				cerrarPanel(p)
			end
			return
		end
	end
end

local function usarLlave(jugador: Player)
	local origen = frente(jugador)
	if not origen then
		return
	end
	Sonidos.emitir("Llave", origen, 0.3)
	local H = Config.HERRAMIENTAS
	for parte, b in brechas do
		if (parte.Position - origen).Magnitude <= H.ALCANCE_LLAVE then
			Rafagas.lanzar("Martillazo", parte.Position, 0.5)
			b.reparacion += H.REPARACION_LLAVE
			parte:SetAttribute("Reparacion", math.min(100, b.reparacion))
			Estadisticas.sumar(jugador, "reparar")
			if b.reparacion >= 100 then
				cerrar(b)
			end
			return
		end
	end
	for _, lado in { "Izq", "Der" } do
		local motor = Avion.motorParte(lado)
		if motor and (motor.Position - origen).Magnitude <= H.ALCANCE_LLAVE + 4 then
			if Avion.repararMotor(lado, 5) then
				Estadisticas.sumar(jugador, "reparar")
				return
			end
		end
	end
	Carga.repararJaula(origen, H.ALCANCE_LLAVE + 3, 6)
end

function Peligros.iniciar()
	RemotoUsar.OnServerEvent:Connect(function(jugador, mirada)
		local ahora = os.clock()
		if (ultimoUso[jugador] or 0) > ahora or not Personajes.vivo(jugador) or Personajes.enRagdoll(jugador) then
			return
		end
		ultimoUso[jugador] = ahora + Config.HERRAMIENTAS.CADENCIA
		local m: Vector3? = nil
		if typeof(mirada) == "Vector3" and mirada == mirada and mirada.Magnitude > 0.5 and mirada.Magnitude < 1.5 then
			m = mirada.Unit
		end
		local tipo = Agarre.tipo(jugador)
		if tipo == "Extintor" then
			usarExtintor(jugador, m)
		elseif tipo == "Llave" then
			usarLlave(jugador)
		elseif tipo == "Agua" then
			usarAgua(jugador, m)
		elseif tipo == "Piolet" then
			usarPiolet(jugador)
		elseif tipo == "Carrito" then
			ultimoUso[jugador] = ahora + 1.2
			local raiz = Personajes.raiz(jugador)
			if raiz then
				Sonidos.emitir("Bocina", raiz.Position, 0.5)
				Rafagas.lanzar("Bocina", raiz.Position + raiz.CFrame.LookVector * 3 + Vector3.new(0, 1.5, 0))
			end
		end
	end)
	Players.PlayerRemoving:Connect(function(jugador)
		ultimoUso[jugador] = nil
		quemados[jugador] = nil
	end)
	Agarre.antesDeAgarrar(function(objeto)
		if objeto:GetAttribute("Tapon") then
			for _, b in brechas do
				if b.tapon == objeto then
					destapar(b, false)
				end
			end
		end
	end)
	if RunService:IsStudio() then
		Workspace:GetAttributeChangedSignal("PruebaPajaros"):Connect(function()
			if not Workspace:GetAttribute("PruebaPajaros") then
				return
			end
			Workspace:SetAttribute("PruebaPajaros", nil)
			if activo then
				pajaros()
			else
				avion:SetAttribute("Bandada", os.clock())
				task.delay(3, function()
					avion:SetAttribute("Pajaros", os.clock())
				end)
			end
		end)
	end

	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		if acumulado < 0.1 then
			return
		end
		local paso = acumulado
		acumulado = 0
		local cinturones = Avion.estado.cinturones
		local lista: { BasePart } = {}
		if next(brechas) ~= nil then
			lista = sueltos()
		end
		for parte, b in brechas do
			local tapon = b.tapon
			if tapon and (not tapon.Parent or not tapon.Anchored) then
				destapar(b, false)
				tapon = nil
			end
			if tapon then
				Avion.danar(0.1 * paso)
				continue
			end
			Avion.danar(0.6 * paso)
			local centro = parte.Position
			for _, o in if os.clock() > b.sinTapon then CollectionService:GetTagged("Objeto") else {} do
				if o:IsA("BasePart") and o.Parent and not o.Anchored and not Agarre.portador(o) then
					local tipo = o:GetAttribute("Tipo")
					if typeof(tipo) == "string" and TAPONES[tipo] and (o.Position - centro).Magnitude < 2.6 then
						taponar(b, o)
						break
					end
				end
			end
			if b.tapon then
				continue
			end
			local salida = parte.CFrame.LookVector * -1
			for _, p in lista do
				local delta = centro - p.Position
				local d = delta.Magnitude
				if d < 24 and d > 0.1 then
					local fuerza = (1 - d / 24) * 70 * paso
					Objetos.empujar(p, delta.Unit * fuerza + (if d < 3 then salida * 40 * paso else Vector3.zero))
				end
			end
			Pasajeros.succionar(centro, 1.2, 22, cinturones, paso)
		end
		local ahora = os.clock()
		local nuevos: { Vector3 } = {}
		for _ in paneles do
			Avion.danar(0.25 * paso)
		end
		for parte, f in fuegos do
			Avion.danar(0.35 * paso)
			Carga.quemar(parte.Position, 2.5, 6 * paso)
			if f.vida > 55 and rng:NextNumber() < 0.012 * paso * 10 then
				local p = parte.Position + Vector3.new(rng:NextNumber(-4, 4), 0, rng:NextNumber(-4, 4))
				table.insert(nuevos, Vector3.new(math.clamp(p.X, -5.5, 5.5), p.Y, math.clamp(p.Z, -62, 20)))
			end
			for _, jugador in Players:GetPlayers() do
				local raiz = Personajes.raiz(jugador)
				if raiz and (raiz.Position - parte.Position).Magnitude < 3.2 and (quemados[jugador] or 0) < ahora then
					quemados[jugador] = ahora + 2
					Sonidos.emitir("GolpeFuerte", raiz.Position)
					local dir = (raiz.Position - parte.Position) * Vector3.new(1, 0, 1)
					Personajes.ragdoll(jugador, 1.2, (if dir.Magnitude > 0 then dir.Unit else Vector3.xAxis) * 30 + Vector3.new(0, 30, 0))
					RemotoAviso:FireClient(jugador, "¡Te has quemado!", "peligro")
				end
			end
		end
		for _, p in nuevos do
			Peligros.fuego(p)
		end
	end)
end

return Peligros
