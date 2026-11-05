--!strict
local CollectionService = game:GetService("CollectionService")
local ContentProvider = game:GetService("ContentProvider")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local ImagenesCaras = require(ReplicatedStorage.Shared.ImagenesCaras)
local Vivos = require(ReplicatedStorage.Shared.PasajerosVivos)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Gui = require(ReplicatedStorage.Shared.Gui)
local Agarre = require(script.Parent.Agarre)
local Rafagas = require(script.Parent.Rafagas)
local Sonido = require(script.Parent.Sonido)

type Tipo = Vivos.Tipo
type Muelle = { x: Vector3, v: Vector3 }
type Ojo = { borde: Part, blanco: Part, pupila: Part, mb: SpecialMesh, mw: SpecialMesh, mp: SpecialMesh, p: Vector2, v: Vector2, ultimo: Vector3 }
type Objetivo = {
	ang: Vector3,
	bote: number,
	aplaste: number,
	brazoD: Vector3,
	brazoI: Vector3,
	piernaD: Vector3,
	piernaI: Vector3,
	rigidez: number,
	abre: number,
	guino: number,
	tam: number,
	pupila: number,
	sesgo: number,
	alto: number,
	angulo: number,
	mejilla: number,
	boca: string,
	paleta: string,
	mirar: Vector2?,
	mirarA: Vector3?,
	modoPupila: number,
	vapor: boolean,
	sudor: boolean,
	zetas: boolean,
	helice: number,
	temblor: number,
}
type Vivo = {
	modelo: Model,
	cuerpo: BasePart,
	tipo: Tipo,
	aspecto: string,
	partes: { [string]: MeshPart },
	reposo: { [string]: Vector3 },
	tamanos: { [string]: Vector3 },
	texturaBase: string,
	ojos: { Ojo },
	cejas: { Part },
	mejillas: { Part },
	mallasMejilla: { SpecialMesh },
	vapor: ParticleEmitter,
	sudor: ParticleEmitter,
	zetas: ParticleEmitter,
	flash: ParticleEmitter?,
	o: Objetivo,
	ang: Vector3,
	bote: number,
	aplaste: number,
	aplasteEscrito: number,
	limbs: { [string]: Muelle },
	abre: number,
	guino: number,
	tam: number,
	pupila: number,
	sesgo: number,
	alto: number,
	angulo: number,
	mejilla: number,
	boca: string,
	paleta: string,
	gelatina: Muelle,
	antes: Vector3?,
	velAntes: Vector3,
	acel: Vector3,
	evento: string,
	eventoDesde: number,
	eventoHasta: number,
	pedido: string,
	pedidoHasta: number,
	accion: string,
	accionDesde: number,
	accionHasta: number,
	proxima: number,
	parpadeo: number,
	proximoParpadeo: number,
	semilla: number,
	heliceAng: number,
	revisar: number,
	modo: string,
	ultimoGrito: number,
	proximaQueja: number,
	flashHecho: boolean,
	conexiones: { RBXScriptConnection },
	caracter: string,
	peligro: string,
	peligroPos: Vector3,
	vecino: Vector3?,
	proximaFrase: number,
	proximaDuda: number,
	huella: Part,
	calco: Decal,
	huellaHasta: number,
	huellaLado: number,
	ladoGolpe: number,
	lod: number,
}
type Foco = { tipo: string, pos: Vector3, radio: number, prioridad: number }

local CarasPasajeros = {}

local ALCANCE = 120
local ALCANCE_BAJO = 50
local LEJOS = 30
local LEJOS_BAJO = 16
local ESCALA = Config.PASAJEROS.ESCALA_VISUAL
local GRAVEDAD = 38
local TINTA = Color3.fromRGB(27, 27, 33)
local BLANCO = Color3.fromRGB(247, 247, 242)
local AMARILLO = Color3.fromRGB(255, 214, 70)
local ROJO = Color3.fromRGB(217, 68, 58)
local VERDE = Color3.fromRGB(107, 191, 89)
local VOMITO = Color3.fromRGB(150, 196, 70)
local AGUA = Color3.fromRGB(143, 211, 244)
local PIEZAS_PALETA = { "Cuerpo", "BrazoDer", "BrazoIzq", "PiernaDer", "PiernaIzq", "Helice" }
local EXTREMIDADES = { "BrazoDer", "BrazoIzq", "PiernaDer", "PiernaIzq" }
local PRIORIDAD: { [string]: number } = {
	Vomito = 9,
	Quemado = 8,
	Mordisco = 8,
	Choque = 7,
	Golpe = 7,
	Enfado = 6,
	Comer = 5,
	Beber = 5,
	Feliz = 4,
	Aplauso = 3,
	Susto = 3,
	Mojado = 2,
	Bofetada = 8,
	Revancha = 8,
	Cubrirse = 6,
	Grito = 6,
	Asco = 5,
	Eructo = 4,
	Ovacion = 4,
	Asombro = 3,
}
local ACCIONES_CARACTER: { [string]: { string } } = {
	Grunon = { "Cruzar", "Cruzar", "Mirar" },
	Dormilon = { "Bostezo", "Bostezo", "Estirar" },
	Gloton = { "Barriga", "Barriga", "Mirar" },
	Miedoso = { "Unas", "Unas", "Mirar" },
	Fiestero = { "Bailar", "Bailar", "Mirar" },
}
local CAOS_RISA: { [string]: boolean } = { Animal = true, Carrito = true, Bano = true, Cafetera = true, Peste = true }
local ICONOS: { [string]: string } = { Grunon = "Enfado", Miedoso = "Miedo", Dormilon = "Luna", Gloton = "Hamburguesa", Charlatan = "Altavoz", Fiestero = "Estrella", Despistado = "Info" }
local NOMBRES: { [string]: string } = { Grunon = "Gruñón", Miedoso = "Miedoso", Dormilon = "Dormilón", Gloton = "Glotón", Charlatan = "Charlatán", Fiestero = "Fiestero", Despistado = "Despistado" }
local HABLA = { "BocaAbierta", "BocaNeutra", "BocaOoh", "BocaContento" }
local AZUL = Color3.fromRGB(74, 120, 201)
local FRASES_GRUNON = { "¡HMPF!", "¡VAYA SERVICIO!", "¡EN MIS TIEMPOS ESTO NO PASABA!" }
local FRASES_CHARLA = { "BLA BLA BLA", "...Y ENTONCES...", "¿A QUE NO SABES QUÉ?" }
local FRASES_FIESTA = { "¡WUUU!", "¡FIESTA!" }
local FRASES_PERDIDO = { "¿DÓNDE ESTOY?", "¿ESTE ES MI ASIENTO?" }
local FRASES_HARTO = { "¡CALLA YA!", "¡SHHH!" }
local FRASES_PELIGRO: { [string]: string } = { Fuego = "¡FUEGO!", Brecha = "¡AGÁRRATE!", Bebe = "¡SHHH!", Peste = "¡PUAJ!", Bano = "¡JA, JA, JA!", Animal = "¡QUÉ BICHO!", Carrito = "¡CUIDADO!", Cafetera = "¡AL SUELO!" }
local ACCIONES: { [string]: { string } } = {
	PasajeroAbuela = { "Tejer", "Tejer", "Gafas", "Mirar", "Bostezo" },
	PasajeroTurista = { "Selfie", "Selfie", "Helado", "Mirar", "Bostezo" },
	PasajeroEjecutivo = { "Telefono", "Telefono", "Telefono", "Movil", "Rascar" },
	PasajeroNino = { "Piruleta", "Columpio", "Columpio", "Mirar", "Bostezo" },
	PasajeroDeportista = { "Pesas", "Estirar", "Correr", "Mirar" },
	PasajeroRockero = { "Cabeceo", "Cabeceo", "Guitarra", "Mirar", "Bostezo" },
}
local FRASES_GRITO = { "¡AAAAH!", "¡SOCORRO!", "¡WIIIII!", "¡MAMÁ!" }
local FRASES_VOMITO = { "¡BLEEEH!", "¡BUAAARGH!" }
local FRASES_PEDIDO: { [string]: string } = { Hamburguesa = "¡MI HAMBURGUESA!", Cafe = "¡MI CAFÉ!", Agua = "¡AGUA, POR FAVOR!" }

local avion = Workspace:WaitForChild("Avion") :: Model
local rng = Random.new()
local carpeta = Instance.new("Folder")
carpeta.Name = "PasajerosVivos"
local vivos: { [Model]: Vivo } = {}
local seguidos: { [Model]: boolean } = {}
local fallidos: { [Model]: number } = {}
local partes: { BasePart } = {}
local marcos: { CFrame } = {}
local cabezas: { Vector3 } = {}
local focos: { Foco } = {}
local fijos: { [string]: BasePart } = {}
local estado = ReplicatedStorage:WaitForChild("Estado")
local proximoSensor = 0
local buscarFijos = 0
local piratasVivos = 0
local disco = false
local borracho = false
local etiqueta = Instance.new("BillboardGui")
local etiquetaTexto: TextLabel? = nil
local etiquetaIcono: ImageLabel? = nil
local etiquetado = ""

local function imagen(nombre: string): string
	return `rbxassetid://{ImagenesCaras[nombre] or 0}`
end

local function num(i: Instance, nombre: string, defecto: number?): number
	local v = i:GetAttribute(nombre)
	return if typeof(v) == "number" then v else defecto or 0
end

local function suave(a: number, b: number, velocidad: number, dt: number): number
	return a + (b - a) * (1 - math.exp(-velocidad * dt))
end

local function elegir(lista: { string }): string
	return lista[rng:NextInteger(1, #lista)]
end

local function esfera(tamano: Vector3, color: Color3): (Part, SpecialMesh)
	local p = Instance.new("Part")
	p.Size = tamano
	p.Color = color
	p.Material = Enum.Material.SmoothPlastic
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	local m = Instance.new("SpecialMesh")
	m.MeshType = Enum.MeshType.Sphere
	m.Parent = p
	p.Parent = carpeta
	return p, m
end

local function emisor(padre: Attachment, textura: string, color: Color3, tam: NumberSequence, vida: NumberRange, rapidez: NumberRange, abrir: number, acel: Vector3, ritmo: number): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Texture = textura
	e.Color = ColorSequence.new(color)
	e.Size = tam
	e.Lifetime = vida
	e.Speed = rapidez
	e.SpreadAngle = Vector2.new(abrir, abrir)
	e.Acceleration = acel
	e.Rate = ritmo
	e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(0.7, 0.2), NumberSequenceKeypoint.new(1, 1) })
	e.Rotation = NumberRange.new(-25, 25)
	e.RotSpeed = NumberRange.new(-30, 30)
	e.EmissionDirection = Enum.NormalId.Top
	e.LightEmission = 0
	e.Enabled = false
	e.Parent = padre
	return e
end

local function aspectoDe(modelo: Model, cuerpo: BasePart): string?
	local a = modelo:GetAttribute("Aspecto")
	if typeof(a) == "string" and Vivos.TIPOS[a] then
		return a
	end
	for _, h in cuerpo:GetChildren() do
		if h:IsA("Model") and Vivos.TIPOS[h.Name] then
			return h.Name
		end
	end
	return nil
end

local function ocultar(modelo: Model, valor: number)
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") then
			d.LocalTransparencyModifier = valor
		end
	end
end

local function evento(v: Vivo, nombre: string, duracion: number, retraso: number?)
	local ahora = os.clock()
	if ahora < v.eventoHasta and (PRIORIDAD[v.evento] or 0) > (PRIORIDAD[nombre] or 0) then
		return
	end
	v.evento = nombre
	v.eventoDesde = ahora + (retraso or 0)
	v.eventoHasta = ahora + (retraso or 0) + duracion
	v.gelatina.v += Vector3.new(rng:NextNumber(-2.5, 2.5), 0, rng:NextNumber(-2.5, 2.5))
end

local function puntoBoca(v: Vivo): Vector3
	return v.partes.Boca.Position + v.cuerpo.CFrame.LookVector * 0.4
end

local function cerca(v: Vivo, distancia: number): boolean
	return (Workspace.CurrentCamera.CFrame.Position - v.cuerpo.Position).Magnitude < distancia
end

local function frase(v: Vivo, lista: { string }, color: Color3, fondo: Color3, prob: number)
	local ahora = os.clock()
	if ahora < v.proximaFrase then
		return
	end
	v.proximaFrase = ahora + rng:NextNumber(4, 8)
	if rng:NextNumber() < prob and cerca(v, 35) then
		Rafagas.palabra(v.cuerpo.Position + Vector3.new(0, 3, 0), elegir(lista), color, fondo, 0.7, true)
	end
end

local function duda(v: Vivo)
	local ahora = os.clock()
	if ahora < v.proximaDuda then
		return
	end
	v.proximaDuda = ahora + rng:NextNumber(5, 10)
	if cerca(v, 30) then
		local c = v.modelo:FindFirstChild("Cabeza")
		Rafagas.pop(if c then c else v.cuerpo, Vector3.new(0, 1.9, 0), { imagen = "Interrogacion", tinte = AMARILLO, tam = 1.3, vida = 1.2, subir = 0.6 })
	end
end

local function abofeteado(v: Vivo)
	local cabeza: Vector3? = nil
	local distancia = 12
	for _, c in cabezas do
		local d = (c - v.cuerpo.Position).Magnitude
		if d < distancia then
			cabeza, distancia = c, d
		end
	end
	local lado = if cabeza and v.cuerpo.CFrame:PointToObjectSpace(cabeza).X < 0 then -1 else 1
	v.ladoGolpe = lado
	v.huellaLado = lado
	v.huellaHasta = os.clock() + 4
	evento(v, if v.caracter == "Grunon" then "Revancha" else "Bofetada", 1.4)
end

local function vomitar(v: Vivo)
	evento(v, "Vomito", 1.7)
	task.delay(0.35, function()
		if not vivos[v.modelo] then
			return
		end
		local p = puntoBoca(v)
		Rafagas.lanzar("Salpicadura", p, 0.55, VOMITO)
		Sonido.reproducir("Salpicadura", v.cuerpo, 0.9, 0.7)
		if cerca(v, 45) then
			Rafagas.palabra(p + Vector3.new(0, 1.2, 0), elegir(FRASES_VOMITO), VERDE, BLANCO, 0.8, true)
		end
	end)
end

local function conectar(v: Vivo)
	local m = v.modelo
	local function reaccion()
		local r = m:GetAttribute("Reaccion")
		if r == "Golpe" then
			evento(v, "Golpe", 2.2)
		elseif r == "Mojado" then
			local asco = estado:GetAttribute("CaosEstornudo") ~= nil
			evento(v, if asco then "Asco" else "Mojado", if asco then 2.2 else 1.5)
		elseif r == "Mareo" then
			evento(v, "Asco", 2.2)
		elseif r == "Feliz" then
			evento(v, "Feliz", 2.5)
		elseif r == "Enfado" then
			evento(v, "Enfado", 3)
		elseif r == "Quemado" or r == "Mordisco" then
			evento(v, r :: string, 1.8)
		else
			evento(v, "Susto", 1.3)
		end
	end
	v.conexiones = {
		m:GetAttributeChangedSignal("Pedido"):Connect(function()
			local p = m:GetAttribute("Pedido")
			if typeof(p) == "string" and p ~= "" then
				v.pedido = p
			else
				v.pedidoHasta = os.clock() + 0.6
			end
		end),
		m:GetAttributeChangedSignal("Feliz"):Connect(function()
			if os.clock() < v.pedidoHasta and v.pedido ~= "" then
				evento(v, if v.pedido == "Cafe" or v.pedido == "Agua" then "Beber" else "Comer", 3.2)
				v.pedido = ""
			else
				evento(v, "Feliz", 2.5)
			end
		end),
		m:GetAttributeChangedSignal("Enfado"):Connect(function()
			evento(v, "Enfado", 3.5)
		end),
		m:GetAttributeChangedSignal("ReaccionMarca"):Connect(reaccion),
		m:GetAttributeChangedSignal("Vomito"):Connect(function()
			vomitar(v)
		end),
		m:GetAttributeChangedSignal("Bofetada"):Connect(function()
			abofeteado(v)
		end),
		m:GetAttributeChangedSignal("Eructo"):Connect(function()
			evento(v, "Eructo", 1.3)
			Sonido.reproducir("Eructo", v.cuerpo, 0.9, rng:NextNumber(0.85, 1.15))
			if cerca(v, 40) then
				Rafagas.palabra(v.cuerpo.Position + Vector3.new(0, 2.8, 0), "¡BUUURP!", VERDE, BLANCO, 0.75, true)
			end
		end),
		m:GetAttributeChangedSignal("Caracter"):Connect(function()
			local c = m:GetAttribute("Caracter")
			v.caracter = if typeof(c) == "string" then c else "Normal"
		end),
	}
end

local function quitar(modelo: Model)
	local v = vivos[modelo]
	if not v then
		return
	end
	vivos[modelo] = nil
	for _, c in v.conexiones do
		c:Disconnect()
	end
	for _, p in v.partes do
		p:Destroy()
	end
	for _, o in v.ojos do
		o.borde:Destroy()
		o.blanco:Destroy()
		o.pupila:Destroy()
	end
	for _, p in v.cejas do
		p:Destroy()
	end
	for _, p in v.mejillas do
		p:Destroy()
	end
	v.huella:Destroy()
	if modelo.Parent then
		ocultar(modelo, 0)
	end
end

local function crear(modelo: Model, cuerpo: BasePart): Vivo?
	local aspecto = aspectoDe(modelo, cuerpo)
	local tipo = if aspecto then Vivos.TIPOS[aspecto] else nil
	local modelos = ReplicatedStorage:FindFirstChild("ModelosVivos")
	local plantilla = if tipo and modelos then modelos:FindFirstChild(tipo.modelo) else nil
	if not aspecto or not tipo or not plantilla then
		return nil
	end
	local piezas: { [string]: MeshPart } = {}
	local reposo: { [string]: Vector3 } = {}
	local tamanos: { [string]: Vector3 } = {}
	local textura = ""
	for _, d in plantilla:GetDescendants() do
		if d:IsA("MeshPart") then
			local c = d:Clone()
			c.Anchored = true
			c.CanCollide = false
			c.CanQuery = false
			c.CanTouch = false
			c.Size = d.Size * ESCALA
			c.Parent = carpeta
			piezas[d.Name] = c
			reposo[d.Name] = d.Position * ESCALA
			tamanos[d.Name] = c.Size
			if d.Name == "Cuerpo" then
				textura = d.TextureID
			end
		end
	end
	if not piezas.Cuerpo or not piezas.Boca or not piezas.BrazoDer or not piezas.BrazoIzq or not piezas.PiernaDer or not piezas.PiernaIzq then
		for _, p in piezas do
			p:Destroy()
		end
		return nil
	end
	piezas.Boca.CastShadow = false
	piezas.Boca.Color = tipo.piel.Normal
	piezas.Boca.TextureID = imagen("BocaContento")
	local r = tipo.radio * ESCALA
	local k = r / 0.21
	local ojos: { Ojo } = {}
	local cejas: { Part } = {}
	local mejillas: { Part } = {}
	local mallas: { SpecialMesh } = {}
	for _ = 1, 2 do
		local borde, mb = esfera(Vector3.new(2 * r, 2 * r, 0.08 * k), TINTA)
		local blanco, mw = esfera(Vector3.new(1.76 * r, 1.76 * r, 0.13 * k), BLANCO)
		local pupila, mp = esfera(Vector3.new(0.76 * r, 0.76 * r, 0.05 * k), TINTA)
		table.insert(ojos, { borde = borde, blanco = blanco, pupila = pupila, mb = mb, mw = mw, mp = mp, p = Vector2.new(0, -0.02), v = Vector2.zero, ultimo = Vector3.zero })
		table.insert(cejas, (esfera(Vector3.new(1.6 * r, 0.34 * r, 0.28 * r), tipo.ceja)))
		local mejilla, mm = esfera(Vector3.one * 0.3 * tipo.escala * ESCALA, tipo.piel.Normal)
		mejilla.Transparency = 1
		mm.Scale = Vector3.zero
		table.insert(mejillas, mejilla)
		table.insert(mallas, mm)
	end
	local coronilla = Instance.new("Attachment")
	coronilla.Position = tipo.coronilla * ESCALA - reposo.Cuerpo
	coronilla.Parent = piezas.Cuerpo
	local vapor = emisor(coronilla, VFX.textura("Vapor"), Color3.fromRGB(240, 242, 246), NumberSequence.new(0.3, 1.2), NumberRange.new(0.5, 0.9), NumberRange.new(4, 7), 30, Vector3.new(0, 3, 0), 16)
	local sudor = emisor(coronilla, VFX.textura("Gota"), AGUA, NumberSequence.new(0.22, 0.12), NumberRange.new(0.5, 0.7), NumberRange.new(3, 5), 75, Vector3.new(0, -30, 0), 4)
	sudor.Orientation = Enum.ParticleOrientation.VelocityParallel
	local zetas = emisor(coronilla, imagen("Zeta"), BLANCO, NumberSequence.new(0.15, 0.6), NumberRange.new(2.2, 2.6), NumberRange.new(0.8, 1.2), 12, Vector3.new(0.5, 0.2, 0), 0.7)
	local flash: ParticleEmitter? = nil
	if tipo.objeto and aspecto == "PasajeroTurista" then
		local a = Instance.new("Attachment")
		a.Position = tipo.objeto * ESCALA - reposo.BrazoDer
		a.Parent = piezas.BrazoDer
		local f = emisor(a, VFX.textura("Destello"), BLANCO, NumberSequence.new(2.4, 0.6), NumberRange.new(0.15, 0.15), NumberRange.new(0, 0), 0, Vector3.zero, 0)
		f.LightEmission = 1
		flash = f
	end
	local limbs: { [string]: Muelle } = {}
	for _, n in EXTREMIDADES do
		limbs[n] = { x = Vector3.zero, v = Vector3.zero }
	end
	local huella = Instance.new("Part")
	huella.Size = Vector3.new(0.44, 0.44, 0.02) * tipo.escala
	huella.Transparency = 1
	huella.Anchored = true
	huella.CanCollide = false
	huella.CanQuery = false
	huella.CanTouch = false
	huella.CastShadow = false
	local calco = Instance.new("Decal")
	calco.Texture = imagen("Huella")
	calco.Face = Enum.NormalId.Front
	calco.Transparency = 1
	calco.Parent = huella
	huella.Parent = carpeta
	local car = modelo:GetAttribute("Caracter")
	local ahora = os.clock()
	local v: Vivo = {
		modelo = modelo,
		cuerpo = cuerpo,
		tipo = tipo,
		aspecto = aspecto,
		partes = piezas,
		reposo = reposo,
		tamanos = tamanos,
		texturaBase = textura,
		ojos = ojos,
		cejas = cejas,
		mejillas = mejillas,
		mallasMejilla = mallas,
		vapor = vapor,
		sudor = sudor,
		zetas = zetas,
		flash = flash,
		o = {} :: any,
		ang = Vector3.zero,
		bote = 0,
		aplaste = 1,
		aplasteEscrito = 1,
		limbs = limbs,
		abre = 1,
		guino = 1,
		tam = 1,
		pupila = 1,
		sesgo = 0,
		alto = 0,
		angulo = 0,
		mejilla = 0,
		boca = "BocaContento",
		paleta = "Normal",
		gelatina = { x = Vector3.zero, v = Vector3.zero },
		antes = nil,
		velAntes = Vector3.zero,
		acel = Vector3.zero,
		evento = "",
		eventoDesde = 0,
		eventoHasta = 0,
		pedido = "",
		pedidoHasta = 0,
		accion = "",
		accionDesde = 0,
		accionHasta = 0,
		proxima = ahora + rng:NextNumber(1, 6),
		parpadeo = 0,
		proximoParpadeo = ahora + rng:NextNumber(1, 4),
		semilla = (tonumber(string.match(modelo.Name, "%d+")) or rng:NextInteger(1, 99)) * 7.31 + 0.5,
		heliceAng = 0,
		revisar = 0,
		modo = "",
		ultimoGrito = 0,
		proximaQueja = ahora + rng:NextNumber(4, 9),
		flashHecho = false,
		conexiones = {},
		caracter = if typeof(car) == "string" then car else "Normal",
		peligro = "",
		peligroPos = Vector3.zero,
		vecino = nil,
		proximaFrase = ahora + rng:NextNumber(2, 8),
		proximaDuda = ahora + rng:NextNumber(3, 8),
		huella = huella,
		calco = calco,
		huellaHasta = 0,
		huellaLado = 1,
		ladoGolpe = 1,
		lod = 0,
	}
	local p = modelo:GetAttribute("Pedido")
	v.pedido = if typeof(p) == "string" then p else ""
	conectar(v)
	ocultar(modelo, 1)
	vivos[modelo] = v
	return v
end

local function reiniciar(o: Objetivo)
	o.ang = Vector3.zero
	o.bote = 0
	o.aplaste = 1
	o.brazoD = Vector3.zero
	o.brazoI = Vector3.zero
	o.piernaD = Vector3.zero
	o.piernaI = Vector3.zero
	o.rigidez = 1
	o.abre = 1
	o.guino = 1
	o.tam = 1
	o.pupila = 1
	o.sesgo = 0
	o.alto = 0
	o.angulo = 0
	o.mejilla = 0
	o.boca = "BocaContento"
	o.paleta = "Normal"
	o.mirar = nil
	o.mirarA = nil
	o.modoPupila = 0
	o.vapor = false
	o.sudor = false
	o.zetas = false
	o.helice = 0.15
	o.temblor = 0
end

local function asustado(o: Objetivo)
	o.boca = "BocaGrito"
	o.tam = 1.3
	o.pupila = 0.45
	o.alto = 0.1
	o.angulo = -0.4
	o.modoPupila = 1
	o.temblor = 0.05
	o.sudor = true
	o.helice = 1
end

local function furioso(o: Objetivo)
	o.boca = "BocaEnfado"
	o.abre = 0.55
	o.sesgo = 0.3
	o.pupila = 0.75
	o.alto = -0.05
	o.angulo = 0.5
	o.paleta = "Rojo"
	o.vapor = true
end

local function aleteo(o: Objetivo, t: number, fuerza: number)
	o.brazoD = Vector3.new(2.5 + math.sin(t * 13) * 0.5 * fuerza, 0, 0.5 + math.sin(t * 11) * 0.4 * fuerza)
	o.brazoI = Vector3.new(2.5 + math.sin(t * 13 + 2) * 0.5 * fuerza, 0, 0.5 + math.sin(t * 11 + 1) * 0.4 * fuerza)
end

local function patalear(o: Objetivo, t: number, fuerza: number)
	o.piernaD = Vector3.new(math.sin(t * 14) * fuerza, 0, 0)
	o.piernaI = Vector3.new(-math.sin(t * 14) * fuerza, 0, 0)
end

local function colgar(v: Vivo, o: Objetivo)
	local g = v.cuerpo.CFrame:VectorToObjectSpace(Vector3.new(0, -1, 0))
	local delante = math.atan2(-g.Z, -g.Y)
	local h, m = v.tipo.hombro, v.tipo.mano
	local d = (m - h).Unit
	local base = math.atan2(-d.Z, -d.Y)
	local fuera = math.atan2(d.X, -d.Y)
	o.brazoD = Vector3.new(math.clamp(delante - base, -2.6, 2.8), 0, math.clamp(math.atan2(g.X, -g.Y) - fuera, -1.2, 2.4))
	o.brazoI = Vector3.new(math.clamp(delante - base, -2.6, 2.8), 0, math.clamp(math.atan2(-g.X, -g.Y) - fuera, -1.2, 2.4))
	local pierna = math.clamp(delante - 0.59, -1.4, 1.2)
	o.piernaD = Vector3.new(pierna, 0, math.clamp(math.atan2(g.X, -g.Y) * 0.5, -0.5, 0.5))
	o.piernaI = Vector3.new(pierna, 0, math.clamp(math.atan2(-g.X, -g.Y) * 0.5, -0.5, 0.5))
	o.rigidez = 0.3
end

local function accion(v: Vivo, o: Objetivo, t: number, ta: number)
	local a = v.accion
	if a == "Tejer" then
		o.brazoD = Vector3.new(0.5 + math.sin(t * 9) * 0.16, 0, -0.25 + math.cos(t * 9) * 0.08)
		o.brazoI = Vector3.new(0.5 + math.sin(t * 9 + math.pi) * 0.16, 0, -0.25)
		o.mirar = Vector2.new(0, -1)
		o.ang = Vector3.new(0.12, 0, 0)
		o.boca = "BocaContento"
	elseif a == "Gafas" then
		o.brazoD = Vector3.new(1.55, 0, -0.45)
		o.tam = 1.2
		o.boca = "BocaOoh"
	elseif a == "Selfie" then
		o.brazoD = Vector3.new(1.5, 0, 0.35)
		o.boca = if ta % 2 < 1 then "BocaSonrisa" else "BocaLengua"
		o.guino = if ta % 2 < 1 then 1 else 0.1
		o.mirar = Vector2.new(0.6, 0.8)
		o.ang = Vector3.new(-0.05, -0.25, -0.12)
		if ta > 1.3 and not v.flashHecho then
			v.flashHecho = true
			local f = v.flash
			if f then
				f:Emit(1)
				Sonido.reproducir("Boton", v.cuerpo, 0.5, 1.4)
			end
		end
	elseif a == "Helado" then
		o.brazoI = Vector3.new(1.25 + math.max(0, math.sin(t * 6)) * 0.15, 0, -0.4)
		o.boca = "BocaLengua"
		o.mirar = Vector2.new(-0.3, -0.5)
	elseif a == "Telefono" then
		local grito = ta % 4 > 3
		o.boca = if grito then "BocaEnfado" elseif (t * 7) % 2 < 1 then "BocaAbierta" else "BocaNeutra"
		o.brazoD = Vector3.new(0.8 + math.sin(t * 5) * 0.45, 0, 0.3 + math.cos(t * 4) * 0.3 + (if grito then 0.5 else 0))
		o.ang = Vector3.new(0, math.sin(t * 1.5) * 0.15, 0.12)
		o.sesgo = 0.12
		o.angulo = if grito then 0.5 else 0.2
		o.paleta = if grito then "Rojo" else "Normal"
	elseif a == "Movil" then
		o.brazoD = Vector3.new(0.9, 0, -0.25)
		o.mirar = Vector2.new(0.3, -1)
		o.boca = "BocaNeutra"
		o.ang = Vector3.new(0.15, 0, 0)
	elseif a == "Piruleta" then
		o.brazoD = Vector3.new(0.85 + math.max(0, math.sin(t * 7)) * 0.25, 0, -0.35)
		o.boca = "BocaLengua"
		o.mirar = Vector2.new(0.2, -0.3)
		o.helice = 0.6
	elseif a == "Columpio" then
		o.piernaD = Vector3.new(math.sin(t * 6) * 0.55, 0, 0)
		o.piernaI = Vector3.new(-math.sin(t * 6) * 0.55, 0, 0)
		o.bote = math.abs(math.sin(t * 6)) * 0.05
		o.boca = "BocaSonrisa"
		o.helice = 1
	elseif a == "Pesas" then
		local c = (math.sin(t * 5) + 1) / 2
		o.brazoI = Vector3.new(0.3 + c * 1.4, 0, 0.35)
		o.boca = if c > 0.7 then "BocaEnfado" else "BocaSonrisa"
		o.sesgo = c * 0.2
	elseif a == "Estirar" then
		o.brazoD = Vector3.new(2.9, 0, 0.25)
		o.brazoI = Vector3.new(2.9, 0, 0.25)
		o.aplaste = 1.1
		o.boca = "BocaOoh"
		o.abre = 0.2
	elseif a == "Correr" then
		o.piernaD = Vector3.new(math.max(0, math.sin(t * 11)) * 0.6, 0, 0)
		o.piernaI = Vector3.new(math.max(0, math.sin(t * 11 + math.pi)) * 0.6, 0, 0)
		o.brazoD = Vector3.new(0.5 + math.sin(t * 11) * 0.5, 0, 0.2)
		o.brazoI = Vector3.new(0.5 + math.sin(t * 11 + math.pi) * 0.5, 0, 0.2)
		o.boca = "BocaAbierta"
		o.bote = math.abs(math.sin(t * 11)) * 0.04
	elseif a == "Cabeceo" then
		o.ang = Vector3.new(0.12 + math.sin(t * 12) * 0.22, 0, 0)
		o.boca = if (t * 3) % 2 < 1 then "BocaLengua" else "BocaGrito"
		o.brazoD = Vector3.new(0.6 + math.sin(t * 12) * 0.3, 0, -0.15)
		o.brazoI = Vector3.new(1, 0, 0.6)
		o.abre = 0.6
		o.sesgo = 0.15
	elseif a == "Guitarra" then
		o.brazoD = Vector3.new(0.5 + math.sin(t * 16) * 0.2, 0, -0.3)
		o.brazoI = Vector3.new(1.1, 0.3, 0.75 + math.sin(t * 4) * 0.1)
		o.boca = "BocaLengua"
		o.ang = Vector3.new(-0.15, 0, math.sin(t * 3) * 0.12)
		o.abre = 0.45
	elseif a == "Cruzar" then
		o.brazoD = Vector3.new(0.95, 0, -0.75)
		o.brazoI = Vector3.new(0.95, 0, -0.75)
		o.boca = "BocaPuchero"
		o.angulo = 0.4
		o.sesgo = 0.15
	elseif a == "Barriga" then
		o.brazoD = Vector3.new(0.15 + math.sin(t * 5) * 0.12, 0, -0.5)
		o.brazoI = Vector3.new(0.15 + math.cos(t * 5) * 0.12, 0, -0.5)
		o.boca = "BocaLengua"
		o.abre = 0.3
	elseif a == "Unas" then
		o.brazoD = Vector3.new(1.25, 0, -0.35 + math.sin(t * 30) * 0.03)
		o.boca = "BocaPuchero"
		o.tam = 1.15
		o.pupila = 0.7
		o.angulo = -0.3
	elseif a == "Bailar" then
		o.brazoD = Vector3.new(1.8 + math.sin(t * 7) * 0.5, 0, 0.4)
		o.brazoI = Vector3.new(1.8 + math.sin(t * 7 + math.pi) * 0.5, 0, 0.4)
		o.ang = Vector3.new(0, math.sin(t * 3.5) * 0.2, math.sin(t * 7) * 0.12)
		o.bote = math.abs(math.sin(t * 7)) * 0.08
		o.boca = "BocaSonrisa"
	elseif a == "Mirar" then
		o.ang = Vector3.new(0, math.sin(t * 1.6) * 0.45, 0)
		o.mirar = Vector2.new(math.sin(t * 1.6) * 1.2, 0.2)
	elseif a == "Bostezo" then
		o.boca = "BocaOoh"
		o.abre = 0.15
		o.brazoD = Vector3.new(2.7, 0, 0.5)
		o.brazoI = Vector3.new(2.7, 0, 0.5)
		o.aplaste = 1.12
		o.ang = Vector3.new(-0.15, 0, 0)
	elseif a == "Rascar" then
		o.brazoD = Vector3.new(2.6, 0, 0.1 + math.sin(t * 20) * 0.06)
		o.boca = "BocaPuchero"
		o.mirar = Vector2.new(0.5, 0.8)
	end
end

local function vitorear(o: Objetivo, t: number)
	o.brazoD = Vector3.new(2.5, 0, 0.5 + math.sin(t * 12) * 0.2)
	o.brazoI = Vector3.new(2.5, 0, 0.5 + math.sin(t * 12 + 1) * 0.2)
	o.boca = "BocaSonrisa"
	o.tam = 1.1
	o.pupila = 1.2
	o.alto = 0.05
	o.bote = math.abs(math.sin(t * 8)) * 0.2
	o.helice = 1
end

local function apuntar(v: Vivo, objetivo: Vector3, lado: number): Vector3
	local tipo = v.tipo
	local h = Vector3.new(tipo.hombro.X * lado, tipo.hombro.Y, tipo.hombro.Z)
	local base = v.cuerpo.CFrame * CFrame.new(0, -v.cuerpo.Size.Y / 2, 0)
	local d = base:VectorToObjectSpace(objetivo - base:PointToWorldSpace(h * ESCALA))
	local m = Vector3.new(tipo.mano.X * lado, tipo.mano.Y, tipo.mano.Z) - h
	if d.Magnitude < 0.1 or m.Magnitude < 0.01 then
		return Vector3.zero
	end
	d, m = d.Unit, m.Unit
	local adelante = math.atan2(-d.Z, -d.Y) - math.atan2(-m.Z, -m.Y)
	local fuera = (math.atan2(d.X, -d.Y) - math.atan2(m.X, -m.Y)) * lado
	return Vector3.new(math.clamp(adelante, -1, 2.9), 0, math.clamp(fuera, -0.8, 2))
end

local function peligro(v: Vivo, o: Objetivo, t: number)
	local tipo = v.peligro
	local destino = v.peligroPos
	o.mirarA = destino
	if v.caracter == "Fiestero" and CAOS_RISA[tipo] then
		vitorear(o, t)
		frase(v, FRASES_FIESTA, AMARILLO, VERDE, 0.5)
		return
	end
	local d = v.cuerpo.CFrame:VectorToObjectSpace(destino - v.cuerpo.Position)
	local dl = if d.Magnitude > 0.1 then d.Unit else Vector3.new(0, 0, -1)
	local risa = (v.semilla * 3.7) % 1 < 0.35
	if tipo == "Fuego" then
		asustado(o)
		local lado = if dl.X >= 0 then 1 else -1
		local brazo = apuntar(v, destino, lado)
		local abanico = Vector3.new(1.2 + math.sin(t * 12) * 0.4, 0, 0.3)
		o.brazoD = if lado > 0 then brazo else abanico
		o.brazoI = if lado > 0 then abanico else brazo
		o.paleta = "Palido"
	elseif tipo == "Brecha" then
		asustado(o)
		o.brazoD = Vector3.new(-0.35, 0, 0.55)
		o.brazoI = Vector3.new(-0.35, 0, 0.55)
		o.ang = Vector3.new(-dl.Z * 0.35, 0, -dl.X * 0.35)
		o.temblor = 0.09
		o.paleta = "Palido"
	elseif tipo == "Carrito" or tipo == "Animal" then
		o.piernaD = Vector3.new(1.1, 0, 0.1)
		o.piernaI = Vector3.new(1.1, 0, 0.1)
		o.bote = 0.15 + math.abs(math.sin(t * 9)) * 0.08
		if risa then
			o.boca = "BocaSonrisa"
			o.brazoD = Vector3.new(0.2 + math.sin(t * 10) * 0.1, 0, -0.5)
			o.brazoI = Vector3.new(0.2 + math.sin(t * 10) * 0.1, 0, -0.5)
			o.abre = 0.2
		else
			asustado(o)
			o.brazoD = Vector3.new(1.8, 0, 0.5)
			o.brazoI = Vector3.new(1.8, 0, 0.5)
		end
	elseif tipo == "Cafetera" then
		asustado(o)
		o.ang = Vector3.new(0.2, 0, math.sin(t * 5) * 0.3)
		o.bote = -0.1
		o.brazoD = Vector3.new(2.5, 0, -0.3)
		o.brazoI = Vector3.new(2.5, 0, -0.3)
	elseif tipo == "Peste" then
		o.paleta = "Verde"
		o.mejilla = 0.5 + 0.4 * math.max(0, math.sin(t * 2.5))
		o.boca = if t % 2 < 1 then "BocaMareo" else "BocaPuchero"
		o.brazoD = Vector3.new(1.3 + math.sin(t * 14) * 0.25, 0, -0.35)
		o.abre = 0.45
		o.angulo = 0.3
	elseif tipo == "Bebe" then
		o.brazoD = Vector3.new(2.3, 0, 0.6)
		o.brazoI = Vector3.new(2.3, 0, 0.6)
		o.boca = "BocaPuchero"
		o.angulo = 0.45
		o.sesgo = 0.25
		o.abre = 0.6
	elseif tipo == "Bano" then
		if risa then
			o.boca = "BocaSonrisa"
			o.bote = math.abs(math.sin(t * 10)) * 0.08
			o.brazoD = Vector3.new(0.2, 0, -0.5)
			o.abre = 0.2
		else
			o.brazoD = Vector3.new(1.35, 0, -0.45)
			o.boca = "BocaPuchero"
			o.angulo = 0.3
		end
	end
	if v.caracter == "Miedoso" then
		o.temblor += 0.04
	end
	local texto = FRASES_PELIGRO[tipo]
	if texto then
		frase(v, { texto }, AMARILLO, ROJO, if v.caracter == "Miedoso" then 0.6 else 0.3)
	end
end

local function posar(v: Vivo, o: Objetivo, ahora: number, turbulencia: number)
	reiniciar(o)
	local m = v.modelo
	local t = ahora + v.semilla
	local sentado = m:GetAttribute("Estado") == "Sentado"
	local llevado = num(m, "Portador") ~= 0
	local miedo = num(m, "Miedo")
	local pedido = m:GetAttribute("Pedido")
	local evento = if ahora < v.eventoHasta and ahora >= v.eventoDesde then v.evento else ""
	local te = ahora - v.eventoDesde
	local umbral = if v.caracter == "Miedoso" then 0.3 elseif v.caracter == "Fiestero" then 0.75 else 0.55
	local modo = "Reposo"
	if llevado then
		modo = "Llevado"
	elseif not sentado and v.velAntes.Magnitude > 16 then
		modo = "Volando"
	elseif m:GetAttribute("Alborotador") == true then
		modo = "Alboroto"
	elseif evento ~= "" then
		modo = evento
	elseif m:GetAttribute("Perdido") == true and not sentado then
		modo = "Perdido"
	elseif v.peligro ~= "" and v.peligro ~= "Charla" then
		modo = "Peligro"
	elseif piratasVivos > 0 then
		modo = "Piratas"
	elseif m:GetAttribute("Mareado") == true then
		modo = "Mareo"
	elseif miedo > umbral or (turbulencia > 0.5 and miedo > umbral * 0.45) then
		modo = "Miedo"
	elseif miedo > umbral * 0.4 or not sentado then
		modo = "Nervioso"
	elseif disco then
		modo = "Disco"
	elseif typeof(pedido) == "string" and pedido ~= "" then
		modo = "Esperando"
	elseif m:GetAttribute("Dormido") == true then
		modo = "Dormido"
	end
	if modo ~= v.modo then
		if modo == "Volando" and ahora - v.ultimoGrito > 2.5 and cerca(v, 50) then
			v.ultimoGrito = ahora
			Sonido.reproducir("PasajeroGrito", v.cuerpo, 0.8, rng:NextNumber(0.9, 1.25))
			if rng:NextNumber() < 0.6 then
				Rafagas.palabra(v.cuerpo.Position + Vector3.new(0, 2.5, 0), elegir(FRASES_GRITO), AMARILLO, ROJO, 0.8, true)
			end
		end
		if modo == "Reposo" then
			v.proxima = math.max(v.proxima, ahora + rng:NextNumber(1, 3))
		end
		v.modo = modo
	end

	if modo == "Llevado" then
		colgar(v, o)
		o.boca = if v.velAntes.Magnitude > 7 then "BocaGrito" elseif t % 1.6 < 0.8 then "BocaOoh" else "BocaPuchero"
		o.tam = 1.2
		o.angulo = -0.3
		o.modoPupila = if v.velAntes.Magnitude > 7 then 2 else 0
		o.paleta = if miedo > 0.7 then "Palido" else "Normal"
		o.helice = 1
	elseif modo == "Volando" then
		asustado(o)
		aleteo(o, t, 1.4)
		patalear(o, t, 0.8)
		o.paleta = "Palido"
		o.rigidez = 0.6
	elseif modo == "Alboroto" then
		furioso(o)
		o.boca = if t % 0.7 < 0.35 then "BocaEnfado" else "BocaGrito"
		o.brazoD = Vector3.new(1.4 + math.sin(t * 10) * 1.5, 0, 0.4)
		o.brazoI = Vector3.new(1.4 + math.sin(t * 10 + math.pi) * 1.5, 0, 0.4)
		patalear(o, t, 0.6)
		o.bote = math.abs(math.sin(t * 9)) * 0.15
		o.ang = Vector3.new(0.1, 0, math.sin(t * 9) * 0.2)
		o.rigidez = 2
	elseif modo == "Vomito" then
		o.paleta = "Verde"
		o.mejilla = if te < 0.35 then 1.3 else 0
		o.boca = if te < 0.35 then "BocaMareo" else "BocaBleh"
		o.ang = Vector3.new(if te < 0.35 then -0.1 else 0.4, 0, 0)
		o.brazoD = Vector3.new(0.4, 0, -0.2)
		o.brazoI = Vector3.new(0.4, 0, -0.2)
		o.abre = 0.3
		o.angulo = -0.3
		o.aplaste = if te < 0.35 then 0.9 else 1.08
	elseif modo == "Quemado" or modo == "Mordisco" then
		asustado(o)
		aleteo(o, t, 1.2)
		patalear(o, t, 0.7)
		o.bote = math.max(0, 0.6 * math.sin(te * 9)) * math.exp(-te * 2.5)
		o.paleta = if modo == "Quemado" then "Rojo" else "Palido"
		o.vapor = modo == "Quemado"
	elseif modo == "Golpe" or modo == "Choque" then
		if modo == "Choque" then
			asustado(o)
			aleteo(o, t, 1)
			patalear(o, t, 0.6)
			o.paleta = "Palido"
		else
			o.boca = "BocaOoh"
			o.modoPupila = 2
			o.abre = 0.8
			o.angulo = -0.2
		end
		o.ang = Vector3.new(math.sin(t * 6) * 0.15, 0, math.cos(t * 6) * 0.15)
	elseif modo == "Enfado" then
		furioso(o)
		o.brazoD = Vector3.new(1.7 + math.sin(t * 16) * 0.25, 0, 0.25)
		o.ang = Vector3.new(0.1, 0, math.sin(t * 20) * 0.04)
		o.aplaste = 1 + math.sin(t * 16) * 0.03
	elseif modo == "Comer" then
		local c = (t * 6) % 2 < 1
		o.brazoD = Vector3.new(1.15 + math.max(0, math.sin(t * 5)) * 0.3, 0, -0.35)
		o.boca = if c then "BocaMasticar" else "BocaOoh"
		o.abre = 0.12
		o.alto = 0.06
		o.angulo = -0.2
		o.aplaste = 1 + math.sin(t * 12) * 0.025
	elseif modo == "Beber" then
		o.brazoD = Vector3.new(1.35, 0, -0.4)
		o.ang = Vector3.new(-0.25, 0, 0)
		o.boca = "BocaOoh"
		o.abre = 0.12
		o.alto = 0.06
		o.aplaste = 1 + math.sin(t * 9) * 0.03
	elseif modo == "Feliz" or modo == "Ovacion" then
		vitorear(o, t)
	elseif modo == "Bofetada" or modo == "Revancha" then
		local l = v.ladoGolpe
		local caida = math.exp(-te * 3.5)
		o.ang = Vector3.new(0, l * 0.5 * caida, l * 0.45 * caida * math.cos(te * 12))
		o.boca = if te < 0.5 then "BocaOoh" else "BocaEnfado"
		o.modoPupila = if te < 0.7 then 2 else 0
		o.paleta = "Rojo"
		o.tam = if te < 0.4 then 1.3 else 1
		o.angulo = if te < 0.5 then -0.3 else 0.5
		o.sesgo = if te < 0.5 then 0 else 0.3
		o.abre = if te < 0.5 then 1 else 0.6
		if modo == "Revancha" and te > 0.3 then
			o.brazoD = Vector3.new(1.4, 0, 1.3 - math.min(1, (te - 0.3) * 6) * 1.8)
		end
	elseif modo == "Eructo" then
		o.boca = if te < 0.7 then "BocaOoh" else "BocaSonrisa"
		o.aplaste = if te < 0.7 then 1.15 else 1
		o.mejilla = if te < 0.25 then 1 else 0
		o.abre = 0.25
		o.brazoD = Vector3.new(0.2, 0, -0.45)
		o.ang = Vector3.new(-0.15, 0, 0)
	elseif modo == "Asombro" then
		local fuera = Vector3.new(if v.cuerpo.Position.X >= 0 then 1 else -1, 0, 0)
		local lado = if v.cuerpo.CFrame:VectorToObjectSpace(fuera).X >= 0 then 1 else -1
		if lado > 0 then
			o.brazoD = Vector3.new(1.3, 0, 1)
		else
			o.brazoI = Vector3.new(1.3, 0, 1)
		end
		o.boca = "BocaOoh"
		o.tam = 1.3
		o.pupila = 0.6
		o.alto = 0.1
		o.angulo = -0.3
		o.mirar = Vector2.new(lado, 0.2)
		o.ang = Vector3.new(0, -lado * 0.35, 0)
	elseif modo == "Grito" then
		asustado(o)
		aleteo(o, t, 1.2)
		patalear(o, t, 0.6)
		o.paleta = "Palido"
	elseif modo == "Cubrirse" then
		asustado(o)
		o.brazoD = Vector3.new(2.6, 0, -0.35)
		o.brazoI = Vector3.new(2.6, 0, -0.35)
		o.ang = Vector3.new(0.35, 0, 0)
		o.bote = -0.12
		o.abre = 0.2
	elseif modo == "Asco" then
		o.paleta = "Verde"
		o.boca = if t % 1 < 0.5 then "BocaPuchero" else "BocaBleh"
		o.brazoD = Vector3.new(1.35, 0, -0.5 + math.sin(t * 10) * 0.3)
		o.abre = 0.4
		o.angulo = 0.35
		o.ang = Vector3.new(-0.1, 0, 0)
	elseif modo == "Perdido" then
		o.piernaD = Vector3.new(math.sin(t * 9) * 0.5, 0, 0)
		o.piernaI = Vector3.new(-math.sin(t * 9) * 0.5, 0, 0)
		o.brazoD = Vector3.new(0.3 + math.sin(t * 9) * 0.4, 0, 0.2)
		o.brazoI = Vector3.new(0.3 - math.sin(t * 9) * 0.4, 0, 0.2)
		o.boca = "BocaOoh"
		o.tam = 1.15
		o.mirar = Vector2.new(math.sin(t * 1.3) * 1.2, 0.3)
		o.ang = Vector3.new(0, math.sin(t * 1.3) * 0.4, 0)
		frase(v, FRASES_PERDIDO, AMARILLO, AZUL, 0.5)
	elseif modo == "Peligro" then
		peligro(v, o, t)
	elseif modo == "Piratas" then
		asustado(o)
		if t % 3 < 0.8 then
			o.ang = Vector3.new(0.1, 0, 0)
			o.brazoD = Vector3.new(1.4, 0, -0.3)
			o.brazoI = Vector3.new(1.4, 0, -0.3)
			o.boca = "BocaOoh"
		else
			o.ang = Vector3.new(0.45, 0, 0)
			o.bote = -0.15
			o.brazoD = Vector3.new(2.5, 0, -0.3)
			o.brazoI = Vector3.new(2.5, 0, -0.3)
			o.abre = 0.25
		end
	elseif modo == "Disco" then
		local f = if v.caracter == "Fiestero" then 1.6 else 1
		o.brazoD = Vector3.new(2.2 + math.sin(t * 7) * 0.6, 0, 0.4 + math.sin(t * 3.5) * 0.3 * f)
		o.brazoI = Vector3.new(2.2 + math.sin(t * 7 + math.pi) * 0.6, 0, 0.4 - math.sin(t * 3.5) * 0.3 * f)
		o.ang = Vector3.new(0, math.sin(t * 3.5) * 0.25 * f, math.sin(t * 7) * 0.15 * f)
		o.bote = math.abs(math.sin(t * 7)) * 0.12 * f
		o.boca = if t % 2 < 1 then "BocaSonrisa" else "BocaLengua"
		o.abre = if t % 1 < 0.5 then 1 else 0.2
		o.helice = 1
	elseif modo == "Aplauso" then
		o.brazoD = Vector3.new(1.1, 0, -0.45 + math.max(0, math.sin(t * 14)) * 0.3)
		o.brazoI = Vector3.new(1.1, 0, -0.45 + math.max(0, math.sin(t * 14)) * 0.3)
		o.boca = "BocaSonrisa"
		o.abre = if t % 1.2 < 0.6 then 1 else 0.15
		o.alto = 0.05
		o.bote = math.abs(math.sin(t * 7)) * 0.12
		o.helice = 1
	elseif modo == "Susto" then
		asustado(o)
		o.brazoD = Vector3.new(2.2, 0, 0.6)
		o.brazoI = Vector3.new(2.2, 0, 0.6)
		o.bote = math.max(0, 0.35 * math.sin(te * 8)) * math.exp(-te * 3)
	elseif modo == "Mojado" then
		o.boca = "BocaOoh"
		o.abre = 0.35
		o.angulo = -0.3
		o.ang = Vector3.new(0, math.sin(t * 25) * 0.12, 0)
		o.brazoD = Vector3.new(0.6, 0, 0.3 + math.sin(t * 20) * 0.2)
		o.brazoI = Vector3.new(0.6, 0, 0.3 + math.sin(t * 20 + 1) * 0.2)
		o.sudor = true
	elseif modo == "Mareo" then
		o.paleta = "Verde"
		o.boca = "BocaMareo"
		o.mejilla = 0.55 + 0.45 * math.max(0, math.sin(t * 2.2))
		o.abre = 0.5
		o.angulo = -0.25
		o.modoPupila = 2
		o.ang = Vector3.new(0.12, 0, math.sin(t * 1.8) * 0.12)
		o.brazoD = Vector3.new(0.75 + math.sin(t * 2.2) * 0.15, 0, -0.3)
		o.brazoI = Vector3.new(0.3, 0, -0.2)
		o.sudor = true
	elseif modo == "Miedo" then
		asustado(o)
		aleteo(o, t, 1)
		patalear(o, t, 0.5)
		o.paleta = if miedo > 0.75 then "Palido" else "Normal"
	elseif modo == "Nervioso" then
		o.boca = "BocaPuchero"
		o.tam = 1.1
		o.pupila = 0.7
		o.angulo = -0.25
		o.alto = 0.04
		o.brazoD = Vector3.new(1.25, 0, -0.35 + math.sin(t * 30) * 0.03)
		o.temblor = 0.02
		o.sudor = true
	elseif modo == "Esperando" then
		local i = math.min(1, 1 - math.clamp(num(m, "Paciencia") / math.max(1, num(m, "PacienciaMax", 1)), 0, 1) + (if v.caracter == "Grunon" then 0.3 else 0))
		if i < 0.4 then
			o.boca = "BocaContento"
			if t % 5 < 1.3 then
				o.brazoD = Vector3.new(2.4, 0, 0.1)
				o.boca = "BocaAbierta"
			end
		elseif i < 0.7 then
			o.boca = if t % 3 < 1.5 then "BocaNeutra" else "BocaPuchero"
			o.angulo = 0.2
			o.sesgo = 0.1
			o.brazoD = Vector3.new(0.1 + math.max(0, math.sin(t * 14)) * 0.12, 0, 0)
			o.piernaD = Vector3.new(math.max(0, math.sin(t * 12)) * 0.12, 0, 0)
		else
			furioso(o)
			o.paleta = if i > 0.85 then "Rojo" else "Normal"
			o.vapor = i > 0.85
			o.boca = if t % 0.8 < 0.4 then "BocaEnfado" else "BocaAbierta"
			o.brazoD = Vector3.new(2.7, 0, 0.3 + math.sin(t * 10) * 0.5)
			o.bote = math.abs(math.sin(t * 6)) * 0.06
			if ahora > v.proximaQueja then
				v.proximaQueja = ahora + rng:NextNumber(5, 9)
				if rng:NextNumber() < 0.4 and cerca(v, 45) then
					Sonido.reproducir("PasajeroQueja", v.cuerpo, 0.8, rng:NextNumber(0.9, 1.15))
					Rafagas.palabra(v.cuerpo.Position + Vector3.new(0, 3, 0), FRASES_PEDIDO[pedido :: string] or "¡OIGA!", AMARILLO, ROJO, 0.75, true)
				end
			end
		end
	elseif modo == "Dormido" then
		local cabezada = math.max(0, math.sin(t * 0.9)) ^ 8
		o.abre = 0.06
		o.boca = "BocaDormido"
		o.ang = Vector3.new(0.25 + cabezada * 0.25, 0, 0.15)
		o.aplaste = 1 + math.sin(t * 1.6) * 0.03
		o.brazoD = Vector3.new(-0.15, 0, 0.1)
		o.brazoI = Vector3.new(-0.15, 0, 0.1)
		o.zetas = true
		o.helice = 0
	else
		local s = num(m, "Satisfaccion", 0.7)
		o.boca = if s >= 0.6 then "BocaContento" elseif s >= 0.35 then "BocaNeutra" else "BocaPuchero"
		o.angulo = if s < 0.35 then 0.25 else 0
		o.aplaste = 1 + math.sin(t * 2) * 0.015
		o.ang = Vector3.new(0, math.noise(v.semilla, t * 0.3) * 0.4, math.noise(v.semilla + 3, t * 0.3) * 0.1)
		local car = v.caracter
		if car == "Grunon" then
			o.boca = if s >= 0.6 then "BocaNeutra" else "BocaPuchero"
			o.angulo = 0.35
			o.sesgo = 0.12
			for _, c in cabezas do
				if (c - v.cuerpo.Position).Magnitude < 10 then
					frase(v, FRASES_GRUNON, AMARILLO, ROJO, 0.45)
					break
				end
			end
		elseif car == "Miedoso" then
			o.tam = 1.12
			o.pupila = 0.75
			o.temblor = 0.012
			o.angulo = -0.2
		elseif car == "Dormilon" then
			o.abre = 0.5
			o.alto = -0.03
		elseif car == "Gloton" then
			if t % 6 < 1.5 then
				o.boca = "BocaLengua"
			end
		elseif car == "Charlatan" then
			o.boca = HABLA[math.floor(t * 8) % #HABLA + 1]
			local vecino = v.vecino
			o.mirarA = vecino
			if vecino then
				local d = v.cuerpo.CFrame:VectorToObjectSpace(vecino - v.cuerpo.Position)
				o.ang = Vector3.new(0, math.clamp(-d.X * 0.6, -0.5, 0.5), 0)
			end
			o.brazoD = Vector3.new(0.7 + math.sin(t * 5) * 0.4, 0, 0.3 + math.cos(t * 4) * 0.3)
			frase(v, FRASES_CHARLA, BLANCO, AZUL, 0.7)
		elseif car == "Fiestero" then
			o.ang = Vector3.new(math.sin(t * 7) * 0.07, 0, math.sin(t * 3.5) * 0.06)
			o.boca = "BocaSonrisa"
			o.bote = math.abs(math.sin(t * 7)) * 0.03
		elseif car == "Despistado" then
			o.boca = if t % 5 < 2.5 then "BocaOoh" else "BocaNeutra"
			o.mirar = Vector2.new(math.noise(v.semilla, t * 0.9) * 2.4, math.noise(v.semilla + 9, t * 0.9) * 2)
			duda(v)
		end
		if v.peligro == "Charla" and car ~= "Charlatan" then
			o.boca = "BocaPuchero"
			o.angulo = 0.4
			o.sesgo = 0.2
			o.mirarA = v.peligroPos
			frase(v, FRASES_HARTO, AMARILLO, ROJO, 0.25)
		end
		if car ~= "Charlatan" and ahora > v.accionHasta and ahora > v.proxima then
			local especial = ACCIONES_CARACTER[car]
			local lista = if especial and rng:NextNumber() < 0.6 then especial else ACCIONES[v.aspecto] or { "Mirar" }
			v.accion = elegir(lista)
			v.accionDesde = ahora
			v.accionHasta = ahora + rng:NextNumber(2.5, 5) * (if v.accion == "Telefono" then 2 else 1)
			v.proxima = v.accionHasta + rng:NextNumber(2, 7)
			v.flashHecho = false
		end
		if ahora < v.accionHasta then
			accion(v, o, t, ahora - v.accionDesde)
		end
	end
	if borracho and (modo == "Reposo" or modo == "Esperando" or modo == "Dormido") then
		o.ang += Vector3.new(0, 0, math.sin(t * 1.6) * 0.15)
		if modo == "Reposo" then
			o.angulo = -0.25
			o.boca = "BocaPuchero"
		end
	end
	o.temblor += turbulencia * 0.12
end

local function muelle(m: Muelle, objetivo: Vector3, k: number, dt: number)
	local c = 2 * math.sqrt(k) * 0.55
	m.v += ((objetivo - m.x) * k - m.v * c) * dt
	m.x += m.v * dt
end

local function mirada(v: Vivo, o: Objetivo, marco: CFrame, t: number): Vector2
	if o.mirar then
		return o.mirar
	end
	local a = o.mirarA
	if a and (a - marco.Position).Magnitude > 0.5 then
		local d = (a - marco.Position).Unit
		return Vector2.new(d:Dot(marco.RightVector), d:Dot(marco.UpVector)) * 1.6
	end
	local mejor, distancia = nil :: Vector3?, 30
	for _, c in cabezas do
		local d = (c - marco.Position).Magnitude
		if d < distancia and d > 1.5 then
			mejor, distancia = c, d
		end
	end
	if mejor then
		local d = (mejor - marco.Position).Unit
		return Vector2.new(d:Dot(marco.RightVector), d:Dot(marco.UpVector)) * 1.6
	end
	return Vector2.new(math.noise(v.semilla, t * 0.4), math.noise(v.semilla + 5, t * 0.4)) * 2
end

local function pupila(ojo: Ojo, marco: CFrame, destino: Vector2, acel: Vector3, rango: number, modo: number, t: number, dt: number)
	if destino.Magnitude > 1 then
		destino = destino.Unit
	end
	local fin = destino * rango
	if modo == 2 then
		fin = Vector2.new(math.cos(t * 7), math.sin(t * 7)) * rango
	elseif modo == 1 then
		fin += Vector2.new(rng:NextNumber(-1, 1), rng:NextNumber(-1, 1)) * rango * 0.6
	end
	local relativa = Vector3.new(0, -GRAVEDAD, 0) - acel
	local empuje = Vector2.new(relativa:Dot(marco.RightVector), relativa:Dot(marco.UpVector)) * 0.08
	ojo.v = (ojo.v + (empuje + (fin - ojo.p) * 140) * dt) * math.exp(-10 * dt)
	ojo.p += ojo.v * dt
	local largo = ojo.p.Magnitude
	if largo > rango then
		local dir = ojo.p / largo
		ojo.p = dir * rango
		local hacia = ojo.v:Dot(dir)
		if hacia > 0 then
			ojo.v -= dir * hacia * 1.5
		end
	end
end

local function pintar(v: Vivo, paleta: string)
	v.paleta = paleta
	local textura = if paleta == "Normal" then v.texturaBase else imagen("Paleta" .. paleta)
	for _, n in PIEZAS_PALETA do
		local p = v.partes[n]
		if p then
			p.TextureID = textura
		end
	end
	local piel = v.tipo.piel[paleta] or v.tipo.piel.Normal
	v.partes.Boca.Color = piel
	for _, mj in v.mejillas do
		mj.Color = piel
	end
end

local function animar(v: Vivo, dt: number, ahora: number, turbulencia: number)
	local cuerpo = v.cuerpo
	local pos = cuerpo.Position
	local antes = v.antes
	if antes then
		local vel = (pos - antes) / dt
		local acel = (vel - v.velAntes) / dt
		v.acel = if acel.Magnitude > 300 then acel.Unit * 300 else acel
		v.velAntes = if vel.Magnitude < 200 then vel else Vector3.zero
	end
	v.antes = pos
	if ahora > v.revisar then
		v.revisar = ahora + 0.5
		ocultar(v.modelo, 1)
	end
	local o = v.o
	posar(v, o, ahora, turbulencia)
	local t = ahora + v.semilla
	local rapido = 14
	v.ang = Vector3.new(suave(v.ang.X, o.ang.X, rapido, dt), suave(v.ang.Y, o.ang.Y, rapido, dt), suave(v.ang.Z, o.ang.Z, rapido, dt))
	v.bote = suave(v.bote, o.bote, 16, dt)
	v.aplaste = suave(v.aplaste, o.aplaste, 12, dt)
	v.abre = suave(v.abre, o.abre, 18, dt)
	v.guino = suave(v.guino, o.guino, 18, dt)
	v.tam = suave(v.tam, o.tam, 14, dt)
	v.pupila = suave(v.pupila, o.pupila, 14, dt)
	v.sesgo = suave(v.sesgo, o.sesgo, 14, dt)
	v.alto = suave(v.alto, o.alto, 14, dt)
	v.angulo = suave(v.angulo, o.angulo, 14, dt)
	v.mejilla = suave(v.mejilla, o.mejilla, 10, dt)
	local k = 220 * o.rigidez
	muelle(v.limbs.BrazoDer, o.brazoD, k, dt)
	muelle(v.limbs.BrazoIzq, o.brazoI, k, dt)
	muelle(v.limbs.PiernaDer, o.piernaD, k, dt)
	muelle(v.limbs.PiernaIzq, o.piernaI, k, dt)
	local relativa = cuerpo.CFrame:VectorToObjectSpace(v.acel)
	local g = v.gelatina
	g.v += (Vector3.new(relativa.Z, 0, relativa.X) * 0.012 - g.x * 140 - g.v * 6) * dt
	g.x += g.v * dt
	if g.x.Magnitude > 0.6 then
		g.x = g.x.Unit * 0.6
	end
	v.heliceAng = (v.heliceAng + dt * (3 + 30 * o.helice)) % (2 * math.pi)
	if ahora > v.proximoParpadeo then
		v.parpadeo = ahora + 0.12
		v.proximoParpadeo = ahora + rng:NextNumber(2, 5.5)
	end
	if o.boca ~= v.boca then
		v.boca = o.boca
		v.partes.Boca.TextureID = imagen(o.boca)
	end
	if o.paleta ~= v.paleta then
		pintar(v, o.paleta)
	end
	if v.vapor.Enabled ~= o.vapor then
		v.vapor.Enabled = o.vapor
	end
	if v.sudor.Enabled ~= o.sudor then
		v.sudor.Enabled = o.sudor
	end
	if v.zetas.Enabled ~= o.zetas then
		v.zetas.Enabled = o.zetas
	end

	local tipo = v.tipo
	local a = v.aplaste
	local kx = 1 / math.sqrt(a)
	local escala = Vector3.new(kx, a, kx)
	local temblor = Vector3.new(math.noise(t * 9, v.semilla), 0, math.noise(t * 9, v.semilla + 3)) * o.temblor * 2
	local giro = v.ang + Vector3.new(g.x.X, 0, g.x.Z) + temblor
	local base = cuerpo.CFrame * CFrame.new(0, -cuerpo.Size.Y / 2, 0)
	local cadera = base * CFrame.new(0, v.bote + temblor.X * 0.3, 0)
	local anim = cadera * CFrame.Angles(-giro.X, giro.Y, giro.Z)
	local p = v.partes
	if math.abs(a - v.aplasteEscrito) > 0.004 then
		v.aplasteEscrito = a
		p.Cuerpo.Size = v.tamanos.Cuerpo * escala
		p.Boca.Size = v.tamanos.Boca * escala
	end
	table.insert(partes, p.Cuerpo)
	table.insert(marcos, anim * CFrame.new(v.reposo.Cuerpo * escala))
	table.insert(partes, p.Boca)
	table.insert(marcos, anim * CFrame.new(v.reposo.Boca * escala))
	local helice = p.Helice
	if helice then
		table.insert(partes, helice)
		table.insert(marcos, anim * CFrame.new(v.reposo.Helice * escala) * CFrame.Angles(0, v.heliceAng, 0))
	end
	for _, lado in { 1, -1 } do
		local brazo = if lado > 0 then "BrazoDer" else "BrazoIzq"
		local pierna = if lado > 0 then "PiernaDer" else "PiernaIzq"
		local h = Vector3.new(tipo.hombro.X * lado, tipo.hombro.Y, tipo.hombro.Z) * ESCALA
		local mb = v.limbs[brazo].x
		table.insert(partes, p[brazo])
		table.insert(marcos, anim * CFrame.new(h * escala) * CFrame.Angles(mb.X, mb.Y * lado, mb.Z * lado) * CFrame.new(v.reposo[brazo] - h))
		local c = Vector3.new(tipo.cadera.X * lado, tipo.cadera.Y, tipo.cadera.Z) * ESCALA
		local mp = v.limbs[pierna].x
		table.insert(partes, p[pierna])
		table.insert(marcos, cadera * CFrame.new(c) * CFrame.Angles(mp.X, mp.Y * lado, mp.Z * lado) * CFrame.new(v.reposo[pierna] - c))
	end

	local r = tipo.radio * ESCALA
	local kk = r / 0.21
	local parpado = if ahora < v.parpadeo then 0.08 else 1
	for i, ojo in v.ojos do
		local lado = if i == 1 then 1 else -1
		local c = Vector3.new(tipo.ojo.X * lado, tipo.ojo.Y, tipo.ojo.Z) * ESCALA * escala
		local n = Vector3.new(tipo.normal.X * lado, tipo.normal.Y, tipo.normal.Z)
		local marco0 = anim * CFrame.lookAt(c, c + n)
		local marco = marco0 * CFrame.Angles(0, 0, v.sesgo * lado)
		local abre = v.abre * parpado * (if lado < 0 then v.guino else 1)
		local tam, pu = v.tam, v.pupila
		local clave = Vector3.new(tam, abre, pu)
		if (clave - ojo.ultimo).Magnitude > 0.004 then
			ojo.ultimo = clave
			ojo.mb.Scale = Vector3.new(tam, tam * math.max(0.07, abre), 1)
			ojo.mw.Scale = Vector3.new(tam, tam * math.max(0.02, abre - 0.1), 1)
			ojo.mp.Scale = Vector3.new(tam * pu, tam * pu * math.min(1, abre * 1.4), 1)
			ojo.pupila.Transparency = if abre > 0.3 then 0 else 1
		end
		local rango = math.max(0, 0.88 * r * tam - 0.38 * r * tam * pu)
		pupila(ojo, marco, mirada(v, o, marco, t), v.acel, rango, o.modoPupila, t + i, dt)
		table.insert(partes, ojo.borde)
		table.insert(marcos, marco * CFrame.new(0, 0, -0.07 * kk))
		table.insert(partes, ojo.blanco)
		table.insert(marcos, marco * CFrame.new(0, 0, -0.1 * kk))
		table.insert(partes, ojo.pupila)
		table.insert(marcos, marco * CFrame.new(ojo.p.X, ojo.p.Y * math.clamp(abre, 0.3, 1), -0.168 * kk))
		table.insert(partes, v.cejas[i])
		table.insert(marcos, marco0 * CFrame.new(0, r * 1.28 * math.max(1, tam) + v.alto * kk, -0.1 * kk) * CFrame.Angles(0, 0, v.angulo * lado))
		local mj = v.mejillas[i]
		local visible = v.mejilla > 0.03
		if (mj.Transparency == 0) ~= visible then
			mj.Transparency = if visible then 0 else 1
		end
		if visible then
			v.mallasMejilla[i].Scale = Vector3.one * v.mejilla
			table.insert(partes, mj)
			table.insert(marcos, anim * CFrame.new(Vector3.new(tipo.mejilla.X * lado, tipo.mejilla.Y, tipo.mejilla.Z) * ESCALA * escala))
		end
	end
	local restante = v.huellaHasta - ahora
	if restante > 0 then
		local c = Vector3.new(tipo.mejilla.X * v.huellaLado, tipo.mejilla.Y, tipo.mejilla.Z) * ESCALA * escala
		local n = Vector3.new(c.X, 0, c.Z).Unit
		v.calco.Transparency = math.clamp(1 - restante, 0.1, 1)
		table.insert(partes, v.huella)
		table.insert(marcos, anim * CFrame.lookAt(c + n * 0.04, c + n))
	elseif v.calco.Transparency < 1 then
		v.calco.Transparency = 1
	end
end

local function todos(nombre: string, duracion: number, desfase: number, centro: Vector3?, radio: number?)
	for _, v in vivos do
		if not centro or (v.cuerpo.Position - centro).Magnitude < (radio or 12) then
			evento(v, nombre, duracion, if v.caracter == "Miedoso" then 0 else rng:NextNumber(0.05, desfase))
		end
	end
end

local function foco(tipo: string, pos: Vector3, radio: number, prioridad: number)
	table.insert(focos, { tipo = tipo, pos = pos, radio = radio, prioridad = prioridad })
end

local function sensar(ahora: number)
	table.clear(focos)
	if ahora > buscarFijos then
		buscarFijos = ahora + 10
		for _, n in { "PuertaBano", "DispensadorCafe" } do
			local d = avion:FindFirstChild(n, true)
			if d and d:IsA("BasePart") then
				fijos[n] = d
			end
		end
	end
	for _, f in CollectionService:GetTagged("Fuego") do
		if f:IsA("BasePart") and num(f, "Vida", 100) > 0 then
			foco("Fuego", f.Position, 12, 8)
		end
	end
	for _, b in CollectionService:GetTagged("Brecha") do
		if b:IsA("BasePart") and num(b, "Fuerza") > 0 then
			foco("Brecha", b.Position, 16, 9)
		end
	end
	for _, c in CollectionService:GetTagged("Objeto") do
		if c:IsA("BasePart") and c:GetAttribute("Tipo") == "Carrito" and c.AssemblyLinearVelocity.Magnitude > 9 then
			foco("Carrito", c.Position, 5, 7)
		end
	end
	for _, n in CollectionService:GetTagged("Peste") do
		if n:IsA("BasePart") then
			foco("Peste", n.Position, num(n, "Radio", 8) + 2, 5)
		end
	end
	local caos = avion:FindFirstChild("Caos")
	if caos then
		for _, h in caos:GetChildren() do
			local tipo = h:GetAttribute("Tipo")
			if h:IsA("BasePart") and (tipo == "Cabra" or tipo == "Gallina") then
				foco("Animal", h.Position, 5, 6)
			elseif h:IsA("Model") and h.Name == "Bebe" then
				foco("Bebe", h:GetPivot().Position, 10, 3)
			end
		end
	end
	local bano, cafetera = fijos.PuertaBano, fijos.DispensadorCafe
	if bano and bano:GetAttribute("Atascada") == true then
		foco("Bano", bano.Position, 9, 2)
	end
	if cafetera and cafetera:GetAttribute("Loca") == true then
		foco("Cafetera", cafetera.Position, 10, 6)
	end
	for _, v in vivos do
		if v.caracter == "Charlatan" and v.modelo:GetAttribute("Estado") == "Sentado" then
			foco("Charla", v.cuerpo.Position, 4.5, 1)
		end
	end
	piratasVivos = 0
	local piratas = avion:FindFirstChild("Piratas")
	if piratas then
		for _, f in piratas:GetChildren() do
			if num(f, "Vida", 100) > 0 then
				piratasVivos += 1
			end
		end
	end
	for _, v in vivos do
		local pos = v.cuerpo.Position
		local mejor, prioridad = "", 0
		for _, f in focos do
			local d = (f.pos - pos).Magnitude
			if f.prioridad > prioridad and d < f.radio and d > 0.5 then
				mejor, prioridad = f.tipo, f.prioridad
				v.peligroPos = f.pos
			end
		end
		v.peligro = mejor
		if v.caracter == "Charlatan" then
			local cercano: Vector3? = nil
			local distancia = 5
			for _, otro in vivos do
				local d = (otro.cuerpo.Position - pos).Magnitude
				if otro ~= v and d < distancia then
					cercano, distancia = otro.cuerpo.Position + Vector3.new(0, 1.5, 0), d
				end
			end
			v.vecino = cercano
		end
	end
end

local function etiquetar()
	local a = Agarre.apuntado()
	local v = if a and a:IsA("Model") then vivos[a] else nil
	local texto, icono = etiquetaTexto, etiquetaIcono
	if not texto or not icono then
		return
	end
	if v and NOMBRES[v.caracter] then
		etiqueta.Adornee = v.partes.Cuerpo
		etiqueta.StudsOffsetWorldSpace = Vector3.new(0, v.tipo.coronilla.Y * ESCALA - v.reposo.Cuerpo.Y + 0.9, 0)
		if etiquetado ~= v.caracter then
			etiquetado = v.caracter
			texto.Text = NOMBRES[v.caracter]
			Gui.ponerIcono(icono, ICONOS[v.caracter])
		end
		etiqueta.Enabled = true
	elseif etiqueta.Enabled then
		etiqueta.Enabled = false
	end
end

local function actualizar(dt: number)
	dt = math.clamp(dt, 1 / 240, 1 / 30)
	local camara = Workspace.CurrentCamera
	if not camara then
		return
	end
	local foco = camara.CFrame.Position
	local mira = camara.CFrame.LookVector
	local bajos = Players.LocalPlayer:GetAttribute("GraficosBajos") == true
	local alcance = if bajos then ALCANCE_BAJO else ALCANCE
	local lejos = if bajos then LEJOS_BAJO else LEJOS
	local ahora = os.clock()
	local turbulencia = num(avion, "Turbulencia")
	disco = avion:GetAttribute("Disco") ~= nil
	borracho = avion:GetAttribute("Borracho") == true
	if ahora > proximoSensor then
		proximoSensor = ahora + 0.25
		sensar(ahora)
		etiquetar()
	end
	table.clear(cabezas)
	for _, j in Players:GetPlayers() do
		local c = j.Character and j.Character:FindFirstChild("Head")
		if c and c:IsA("BasePart") then
			table.insert(cabezas, c.Position)
		end
	end
	table.clear(partes)
	table.clear(marcos)
	for modelo in seguidos do
		local cuerpo = modelo.PrimaryPart
		if not modelo.Parent or not cuerpo then
			if not modelo.Parent then
				seguidos[modelo] = nil
				fallidos[modelo] = nil
			end
			quitar(modelo)
			continue
		end
		local rel = cuerpo.Position - foco
		local d = rel.Magnitude
		local enRango = d < alcance
		local v: Vivo? = vivos[modelo]
		if not enRango then
			if v then
				quitar(modelo)
			end
			continue
		end
		if not v and ahora > (fallidos[modelo] or 0) then
			v = crear(modelo, cuerpo)
			if not v then
				fallidos[modelo] = ahora + 1
			end
		end
		if v and (d < 10 or rel:Dot(mira) > -0.3 * d) then
			v.lod += dt
			if d < lejos or v.lod >= 1 / 15 then
				animar(v, math.min(v.lod, 1 / 15), ahora, turbulencia)
				v.lod = 0
			end
		end
	end
	if #partes > 0 then
		Workspace:BulkMoveTo(partes, marcos, Enum.BulkMoveMode.FireCFrameChanged)
	end
end

local function seguir(modelo: Instance)
	if modelo:IsA("Model") then
		seguidos[modelo] = true
	end
end

function CarasPasajeros.iniciar()
	carpeta.Parent = Workspace
	local lista: { string } = {}
	for nombre in ImagenesCaras do
		table.insert(lista, imagen(nombre))
	end
	task.spawn(function()
		pcall(function()
			ContentProvider:PreloadAsync(lista)
		end)
	end)
	for _, m in CollectionService:GetTagged("Pasajero") do
		seguir(m)
	end
	CollectionService:GetInstanceAddedSignal("Pasajero"):Connect(seguir)
	CollectionService:GetInstanceRemovedSignal("Pasajero"):Connect(function(m)
		if m:IsA("Model") then
			seguidos[m] = nil
			fallidos[m] = nil
			quitar(m)
		end
	end)
	avion:GetAttributeChangedSignal("Aterrizaje"):Connect(function()
		local a = avion:GetAttribute("Aterrizaje")
		if a == "Perfecto" or a == "Bueno" then
			todos("Aplauso", 4.5, 0.6)
		elseif a == "Duro" then
			todos("Susto", 1.6, 0.2)
		end
	end)
	avion:GetAttributeChangedSignal("Fase"):Connect(function()
		if avion:GetAttribute("Fase") == "Estrellado" then
			todos("Choque", 4, 0.3)
		end
	end)
	avion:GetAttributeChangedSignal("Golpe"):Connect(function()
		todos("Susto", 1.2, 0.25)
	end)
	avion:GetAttributeChangedSignal("Pajaros"):Connect(function()
		todos("Asombro", 2.4, 0.5)
	end)
	avion:GetAttributeChangedSignal("Bandada"):Connect(function()
		todos("Asombro", 2, 0.8)
	end)
	avion:GetAttributeChangedSignal("CaidaLibre"):Connect(function()
		if avion:GetAttribute("CaidaLibre") == true then
			todos("Grito", 3, 0.3)
		end
	end)
	local motores: { [string]: number } = { MotorIzq = num(avion, "MotorIzq", 100), MotorDer = num(avion, "MotorDer", 100) }
	for _, nombre in { "MotorIzq", "MotorDer" } do
		avion:GetAttributeChangedSignal(nombre):Connect(function()
			local nuevo = num(avion, nombre, 100)
			if motores[nombre] > 0 and nuevo <= 0 then
				todos("Grito", 2.5, 0.4)
			end
			motores[nombre] = nuevo
		end)
	end
	estado.AttributeChanged:Connect(function(nombre)
		if string.sub(nombre, 1, 4) ~= "Caos" then
			return
		end
		local valor = estado:GetAttribute(nombre)
		if nombre == "CaosAvalancha" and typeof(valor) == "Vector3" then
			todos("Cubrirse", 2, 0.25, valor, 12)
		end
		if valor ~= nil then
			for _, v in vivos do
				if v.caracter == "Fiestero" then
					evento(v, "Ovacion", 2.5, rng:NextNumber(0, 0.6))
				end
			end
		end
	end)
	task.spawn(function()
		local carpetaPiratas = avion:WaitForChild("Piratas", 30)
		if not carpetaPiratas then
			return
		end
		local function vigilarPirata(f: Instance)
			f:GetAttributeChangedSignal("Vida"):Connect(function()
				if num(f, "Vida", 100) <= 0 then
					todos("Ovacion", 3, 0.6)
				end
			end)
			f:GetAttributeChangedSignal("Disparo"):Connect(function()
				todos("Susto", 1, 0.25)
			end)
		end
		for _, f in carpetaPiratas:GetChildren() do
			vigilarPirata(f)
		end
		carpetaPiratas.ChildAdded:Connect(vigilarPirata)
	end)
	etiqueta.Name = "CaracterPasajero"
	etiqueta.Size = UDim2.fromOffset(176, 46)
	etiqueta.AlwaysOnTop = true
	etiqueta.LightInfluence = 0
	etiqueta.MaxDistance = 20
	etiqueta.ResetOnSpawn = false
	etiqueta.Enabled = false
	local fondo = Gui.panel(etiqueta, "Etiqueta", UDim2.fromScale(1, 1), UDim2.fromScale(0, 0))
	etiquetaIcono = Gui.icono(fondo, "Info", UDim2.fromOffset(30, 30), UDim2.new(0, 10, 0.5, 0), Vector2.new(0, 0.5))
	etiquetaTexto = Gui.texto(fondo, "", UDim2.new(1, -52, 1, -10), UDim2.fromOffset(46, 5), Gui.TINTA, true)
	etiqueta.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	RunService.PreRender:Connect(actualizar)
end

return CarasPasajeros
