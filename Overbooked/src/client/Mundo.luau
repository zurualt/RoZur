--!strict
local HttpService = game:GetService("HttpService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Cielo = require(ReplicatedStorage.Shared.Cielo)
local Contratos = require(ReplicatedStorage.Shared.Contratos)
local Destinos = require(ReplicatedStorage.Shared.Destinos)
local Camara = require(script.Parent.Camara)

local Mundo = {}

type Capa = {
	modelos: { string },
	cantidad: number,
	base: { number },
	escala: { number },
	plano: number,
	carril: number,
	manto: boolean,
}

type Nube = {
	parte: BasePart,
	i: number,
	capa: Capa,
	rel: Vector3,
	base: number,
	giro: CFrame,
	medio: Vector3,
	alfa: number,
	extra: boolean,
}

type Adorno = {
	i: number,
	rel: Vector3,
	giro: CFrame,
	alto: number,
	radio: number,
	extra: boolean,
	grande: boolean,
	envoltura: number,
}

type Loseta = {
	i: number,
	giro: CFrame,
	medio: number,
}

type Fijo = { i: number, centro: Vector3, giro: CFrame }

type AdornoBioma = { modelo: string, cantidad: number, escala: { number }, grande: boolean }

type Bioma = {
	suelos: { string },
	adornos: { AdornoBioma },
	fijos: { string },
	luces: string?,
	color: Color3,
	decay: Color3,
	haze: number,
}

type Reserva = {
	bioma: Bioma,
	losetas: { { Loseta } },
	adornos: { Adorno },
	fijos: { Fijo },
	mitad: Vector3,
	hechos: { [string]: boolean },
}

type Ambiente = { color: Color3, decay: Color3, haze: number, glare: number }

local CUMULOS = { "NubeCumulo1", "NubeCumulo2", "NubeCumulo3" }
local PEQUENAS = { "NubePequena1", "NubePequena2" }

local CAPAS: { Capa } = {
	{ modelos = { "NubeManto1", "NubeManto2" }, cantidad = 30, base = { 3450, 3650 }, escala = { 1.1, 1.6 }, plano = 1, carril = 0, manto = true },
	{ modelos = CUMULOS, cantidad = 15, base = { 1200, 2000 }, escala = { 0.8, 1.3 }, plano = 1, carril = 0.2, manto = false },
	{ modelos = PEQUENAS, cantidad = 10, base = { 1000, 2600 }, escala = { 0.9, 1.6 }, plano = 1, carril = 0.15, manto = false },
	{ modelos = { "NubeTorre" }, cantidad = 7, base = { 3300, 3500 }, escala = { 0.9, 1.35 }, plano = 1, carril = 0.1, manto = false },
	{ modelos = CUMULOS, cantidad = 12, base = { 5000, 6300 }, escala = { 0.8, 1.25 }, plano = 1, carril = 0.2, manto = false },
	{ modelos = PEQUENAS, cantidad = 14, base = { 5000, 7200 }, escala = { 0.9, 1.8 }, plano = 1, carril = 0.15, manto = false },
	{ modelos = PEQUENAS, cantidad = 8, base = { 8800, 10200 }, escala = { 1.6, 2.4 }, plano = 0.65, carril = 0, manto = false },
}

local ADORNOS: { [string]: { number } } = {
	Arboleda1 = { 22, 1.5, 2.4 },
	Arboleda2 = { 18, 1.5, 2.4 },
	Pueblo = { 7, 1.7, 2.2 },
}

local VARIANTES = { "SueloCampos1", "SueloCampos2" }

local BIOMAS: { [string]: Bioma } = {
	Jungla = {
		suelos = { "SueloJungla1", "SueloJungla2" },
		adornos = {
			{ modelo = "SelvaJungla", cantidad = 34, escala = { 1, 1.5 }, grande = false },
			{ modelo = "PalmeralJungla", cantidad = 14, escala = { 1, 1.4 }, grande = false },
			{ modelo = "CerroJungla", cantidad = 12, escala = { 1.4, 2.3 }, grande = true },
		},
		fijos = { "AeropuertoJungla", "BordeJungla" },
		luces = nil,
		color = Color3.fromRGB(200, 232, 206),
		decay = Color3.fromRGB(112, 168, 120),
		haze = 1.3,
	},
	Nieve = {
		suelos = { "SueloNieve1", "SueloNieve2" },
		adornos = {
			{ modelo = "PinarNieve", cantidad = 40, escala = { 1, 1.5 }, grande = false },
			{ modelo = "MontanaNieve1", cantidad = 5, escala = { 1.1, 1.6 }, grande = true },
			{ modelo = "MontanaNieve2", cantidad = 4, escala = { 1.1, 1.5 }, grande = true },
		},
		fijos = { "AeropuertoNieve", "BordeNieve" },
		luces = "LucesNieve",
		color = Color3.fromRGB(214, 230, 252),
		decay = Color3.fromRGB(150, 186, 236),
		haze = 0.8,
	},
	Desierto = {
		suelos = { "SueloDesierto1", "SueloDesierto2" },
		adornos = {
			{ modelo = "CactusDesierto", cantidad = 30, escala = { 1, 1.6 }, grande = false },
			{ modelo = "MesaDesierto", cantidad = 8, escala = { 1, 1.6 }, grande = true },
			{ modelo = "AgujasDesierto", cantidad = 6, escala = { 1, 1.6 }, grande = true },
		},
		fijos = { "AeropuertoDesierto", "BordeDesierto" },
		luces = nil,
		color = Color3.fromRGB(250, 206, 156),
		decay = Color3.fromRGB(222, 140, 92),
		haze = 2,
	},
	Ciudad = {
		suelos = { "SueloCiudad1", "SueloCiudad2" },
		adornos = {
			{ modelo = "BarrioCiudad", cantidad = 34, escala = { 1, 1.3 }, grande = false },
			{ modelo = "TorresCiudad", cantidad = 14, escala = { 1, 1.5 }, grande = true },
		},
		fijos = { "AeropuertoCiudad", "BordeCiudad" },
		luces = "LucesCiudad",
		color = Color3.fromRGB(218, 214, 204),
		decay = Color3.fromRGB(172, 162, 150),
		haze = 1.4,
	},
}

local DUENO: { [string]: string } = {}
for nombre, b in BIOMAS do
	for _, s in b.suelos do
		DUENO[s] = nombre
	end
	for _, a in b.adornos do
		DUENO[a.modelo] = nombre
	end
	for _, f in b.fijos do
		DUENO[f] = nombre
	end
	local luces = b.luces
	if luces then
		DUENO[luces] = nombre
	end
end

local avion = Workspace:WaitForChild("Avion") :: Model
local Estado = ReplicatedStorage:WaitForChild("Estado")
local jugador = Players.LocalPlayer
local PIVOTE = Vector3.new(0, 100, -18)
local ESCALA_ALTURA = 0.07
local ESCALA_VELOCIDAD = 0.35
local KM = 30
local RADIO_NUBES = 2800
local RADIO_SUELO = 2400
local RADIO_GRANDE = 4500
local LOSETA = 2048
local CARRIL = 130
local PASILLO = 150
local FRENTE = 3000
local HUNDIDO = 0.6
local VISTA_DESTINO = 12000
local OCULTO = CFrame.new(0, -20000, 0)
local VIENTO = Vector3.new(3, 0, 5)
local AZUL_ALTO = Color3.fromRGB(150, 190, 240)
local DECAY_ALTO = Color3.fromRGB(90, 140, 215)
local BLANCO_NUBE = Color3.fromRGB(236, 240, 247)
local VERDE = Color3.fromRGB(112, 176, 84)
local LUZ_PISTA = Color3.fromRGB(255, 226, 150)
local rng = Random.new()

local carpeta = Instance.new("Folder")
carpeta.Name = "CieloLocal"
local partes: { BasePart } = {}
local marcos: { CFrame } = {}
local suelos: { number } = {}
local tonoSuelos: { number } = {}
local iPista = 0
local nubes: { Nube } = {}
local adornos: { Adorno } = {}
local losetas: { { Loseta } } = { {}, {} }
local listos: { [string]: boolean } = {}
local plantillasDestino: { [string]: BasePart } = {}
local reservas: { [string]: Reserva } = {}
local celdas: { [number]: boolean } = {}
local centroVentana = math.huge
local biomaContrato: string? = nil
local biomaActivo: string? = nil
local posicion = Vector3.zero
local rumbo = 0
local recorrido = 0
local rodado = 0
local faseAnterior = ""
local niebla = 0
local dentro = false
local proximoBache = 0
local velo: Frame
local nubesAltas: Clouds
local altasAntes = false
local vientoAntes = Workspace.GlobalWind
local atmosfera = Lighting:FindFirstChildOfClass("Atmosphere")
local ambienteBase: Ambiente? = if atmosfera then { color = atmosfera.Color, decay = atmosfera.Decay, haze = atmosfera.Haze, glare = atmosfera.Glare } else nil
local densidadAjena = if atmosfera then atmosfera.Density else 0
local densidadEscrita: number? = nil
local ultimoAmbiente = -1
local ritmo = 1
local frenado = 1

local function registrar(p: BasePart): number
	p.Parent = carpeta
	table.insert(partes, p)
	table.insert(marcos, OCULTO)
	return #partes
end

local function nueva(tamano: Vector3, color: Color3, material: Enum.Material): number
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Size = tamano
	p.Color = color
	p.Material = material
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	return registrar(p)
end

local function clonar(plantilla: BasePart, escala: Vector3): BasePart
	local p = plantilla:Clone()
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Material = Enum.Material.SmoothPlastic
	p.Size = plantilla.Size * escala
	return p
end

local function extension(p: BasePart, rot: CFrame): Vector3
	local s = rot:VectorToWorldSpace(p.Size)
	return Vector3.new(math.abs(s.X), math.abs(s.Y), math.abs(s.Z))
end

local function posicionX(radio: number, carril: number): number
	return if rng:NextNumber() < carril then rng:NextNumber(-CARRIL, CARRIL) else rng:NextNumber(-radio, radio)
end

local function envolver(v: Vector3, radio: number, carril: number): (Vector3, boolean)
	local x, z = v.X, v.Z
	local renacida = false
	if z > radio then
		z -= radio * 2
		x = posicionX(radio, carril)
		renacida = true
	elseif z < -radio then
		z += radio * 2
	end
	if x > radio then
		x -= radio * 2
	elseif x < -radio then
		x += radio * 2
	end
	return Vector3.new(x, 0, z), renacida
end

local function fueraDelPasillo(x: number, radio: number): number
	local minimo = radio + PASILLO
	if math.abs(x) >= minimo then
		return x
	end
	return (if x < 0 then -1 else 1) * (minimo + rng:NextNumber(0, 500))
end

local function caja(nombre: string, escala: number): (Vector3, Vector3)
	local c = Destinos.CAJAS[nombre]
	if c then
		return (c.minimo + c.maximo) / 2 * escala, (c.maximo - c.minimo) / 2 * escala
	end
	return Vector3.zero, Vector3.zero
end

local function poblar(r: Reserva, plantilla: BasePart)
	local nombre = plantilla.Name
	if r.hechos[nombre] then
		return
	end
	r.hechos[nombre] = true
	local b = r.bioma
	local rot = plantilla.CFrame.Rotation
	local v = table.find(b.suelos, nombre)
	if v then
		for _ = 1, 9 do
			local p = clonar(plantilla, Vector3.one)
			table.insert(r.losetas[v], { i = registrar(p), giro = rot, medio = extension(p, rot).Y / 2 })
		end
		return
	end
	for _, a in b.adornos do
		if a.modelo ~= nombre then
			continue
		end
		local envoltura = if a.grande then RADIO_GRANDE else RADIO_SUELO
		for _ = 1, a.cantidad do
			local e = rng:NextNumber(a.escala[1], a.escala[2])
			local p = clonar(plantilla, Vector3.one * e)
			local ext = extension(p, rot)
			local centro = caja(nombre, e)
			local radio = math.max(ext.X, ext.Z) / 2
			local x = rng:NextNumber(-envoltura, envoltura)
			table.insert(r.adornos, {
				i = registrar(p),
				rel = Vector3.new(if a.grande then fueraDelPasillo(x, radio) else x, 0, rng:NextNumber(-envoltura, envoltura)),
				giro = CFrame.Angles(0, rng:NextNumber(0, 2 * math.pi), 0) * rot,
				alto = if Destinos.CAJAS[nombre] then centro.Y else ext.Y / 2,
				radio = radio,
				extra = not a.grande and #r.adornos % 3 ~= 0,
				grande = a.grande,
				envoltura = envoltura,
			})
		end
		return
	end
	if table.find(b.fijos, nombre) or b.luces == nombre then
		local p = clonar(plantilla, Vector3.one)
		if b.luces == nombre then
			p.Material = Enum.Material.Neon
			p.Color = LUZ_PISTA
		elseif string.sub(nombre, 1, 10) == "Aeropuerto" then
			p.CastShadow = true
		end
		local centro, mitad = caja(nombre, 1)
		table.insert(r.fijos, { i = registrar(p), centro = centro, giro = rot })
		r.mitad = r.mitad:Max(mitad)
	end
end

local function reservaDe(nombre: string): Reserva?
	local b = BIOMAS[nombre]
	if not b then
		return nil
	end
	local r = reservas[nombre]
	if r then
		return r
	end
	local nueva: Reserva = { bioma = b, losetas = { {}, {} }, adornos = {}, fijos = {}, mitad = Vector3.zero, hechos = {} }
	reservas[nombre] = nueva
	for modelo, plantilla in plantillasDestino do
		if DUENO[modelo] == nombre then
			poblar(nueva, plantilla)
		end
	end
	return nueva
end

local function ocultarReserva(r: Reserva)
	for _, lista in r.losetas do
		for _, l in lista do
			marcos[l.i] = OCULTO
		end
	end
	for _, a in r.adornos do
		marcos[a.i] = OCULTO
	end
	for _, f in r.fijos do
		marcos[f.i] = OCULTO
	end
end

local function llegar(plantilla: Instance)
	if not plantilla:IsA("BasePart") or listos[plantilla.Name] then
		return
	end
	local nombre = plantilla.Name
	listos[nombre] = true
	local dueno = DUENO[nombre]
	if dueno then
		plantillasDestino[nombre] = plantilla
		local r = reservas[dueno]
		if r then
			poblar(r, plantilla)
		end
		return
	end
	local rot = plantilla.CFrame.Rotation
	for k, capa in CAPAS do
		if table.find(capa.modelos, nombre) then
			for _ = 1, math.round(capa.cantidad / #capa.modelos) do
				local e = rng:NextNumber(capa.escala[1], capa.escala[2])
				local p = clonar(plantilla, Vector3.new(e * rng:NextNumber(0.9, 1.15), e * capa.plano * rng:NextNumber(0.85, 1.1), e))
				table.insert(nubes, {
					parte = p,
					i = registrar(p),
					capa = capa,
					rel = Vector3.new(posicionX(RADIO_NUBES, capa.carril), 0, rng:NextNumber(-RADIO_NUBES, RADIO_NUBES)),
					base = rng:NextNumber(capa.base[1], capa.base[2]),
					giro = CFrame.Angles(0, rng:NextNumber(0, 2 * math.pi), 0) * rot,
					medio = p.Size / 2,
					alfa = -1,
					extra = k == #CAPAS or #nubes % 3 ~= 0,
				})
			end
		end
	end
	local adorno = ADORNOS[nombre]
	if adorno then
		for _ = 1, adorno[1] do
			local p = clonar(plantilla, Vector3.one * rng:NextNumber(adorno[2], adorno[3]))
			local ext = extension(p, rot)
			table.insert(adornos, {
				i = registrar(p),
				rel = Vector3.new(rng:NextNumber(-RADIO_SUELO, RADIO_SUELO), 0, rng:NextNumber(-RADIO_SUELO, RADIO_SUELO)),
				giro = CFrame.Angles(0, rng:NextNumber(0, 2 * math.pi), 0) * rot,
				alto = ext.Y / 2,
				radio = math.max(ext.X, ext.Z) / 2,
				extra = #adornos % 3 ~= 0,
				grande = false,
				envoltura = RADIO_SUELO,
			})
		end
	end
	local v = table.find(VARIANTES, nombre)
	if v then
		for _ = 1, 9 do
			local p = clonar(plantilla, Vector3.one)
			table.insert(losetas[v], { i = registrar(p), giro = rot, medio = extension(p, rot).Y / 2 })
		end
	end
end

local function leerContrato()
	local json = Estado:GetAttribute("Contrato")
	biomaContrato = nil
	if typeof(json) ~= "string" or json == "" then
		return
	end
	local ok, datos = pcall(HttpService.JSONDecode, HttpService, json)
	if ok and typeof(datos) == "table" then
		biomaContrato = Contratos.bioma(datos.destino, datos.bioma)
	end
end

local function construir()
	for _ = 1, 25 do
		local i = nueva(Vector3.new(2048, 2, 2048), VERDE, Enum.Material.SmoothPlastic)
		table.insert(suelos, i)
		table.insert(tonoSuelos, 0)
	end
	iPista = nueva(Vector3.new(34, 0.4, 520), Color3.fromRGB(58, 61, 66), Enum.Material.Asphalt)
	local gui = Instance.new("ScreenGui")
	gui.Name = "CieloNiebla"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.DisplayOrder = -5
	velo = Instance.new("Frame")
	velo.Size = UDim2.fromScale(1, 1)
	velo.BackgroundColor3 = BLANCO_NUBE
	velo.BackgroundTransparency = 1
	velo.BorderSizePixel = 0
	velo.Parent = gui
	gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
	local existentes = Workspace.Terrain:FindFirstChildOfClass("Clouds")
	if existentes then
		nubesAltas = existentes
	else
		nubesAltas = Instance.new("Clouds")
		nubesAltas.Enabled = false
		nubesAltas.Cover = 0.42
		nubesAltas.Density = 0.32
		nubesAltas.Color = Color3.new(1, 1, 1)
		nubesAltas.Parent = Workspace.Terrain
	end
	altasAntes = nubesAltas.Enabled
	Estado:GetAttributeChangedSignal("Contrato"):Connect(leerContrato)
	leerContrato()
	task.spawn(function()
		local modelos = ReplicatedStorage:WaitForChild(Cielo.CARPETA)
		modelos.ChildAdded:Connect(llegar)
		for _, hijo in modelos:GetChildren() do
			llegar(hijo)
		end
	end)
end

local function numero(nombre: string): number
	local v = avion:GetAttribute(nombre)
	return if typeof(v) == "number" then v else 0
end

local function biomaDeseado(): string?
	local prueba = avion:GetAttribute("PruebaBioma")
	if typeof(prueba) == "string" and BIOMAS[prueba] then
		return prueba
	end
	return biomaContrato
end

local function restaurar()
	niebla = 0
	dentro = false
	velo.BackgroundTransparency = 1
	nubesAltas.Enabled = altasAntes
	Workspace.GlobalWind = vientoAntes
	ultimoAmbiente = -1
	table.clear(celdas)
	centroVentana = math.huge
	if atmosfera and ambienteBase and Estado:GetAttribute("Fase") ~= "Isla" then
		atmosfera.Color = ambienteBase.color
		atmosfera.Decay = ambienteBase.decay
		atmosfera.Haze = ambienteBase.haze
		atmosfera.Glare = ambienteBase.glare
		if densidadEscrita and math.abs(atmosfera.Density - densidadEscrita) <= 1e-3 then
			atmosfera.Density = densidadAjena
		end
		densidadEscrita = nil
	end
end

local function ambiente(dt: number, altitud: number, velocidad: number, objetivo: number, bioma: Bioma?, tinte: number)
	niebla += (objetivo - niebla) * math.min(1, (if objetivo > niebla then 3.5 else 1.4) * dt)
	if niebla > 0.3 and not dentro then
		dentro = true
		Camara.sacudir(0.4)
	elseif niebla < 0.08 then
		dentro = false
	end
	local ahora = os.clock()
	if dentro and ahora > proximoBache then
		proximoBache = ahora + rng:NextNumber(0.2, 0.45)
		Camara.sacudir(0.07 * niebla)
	end
	velo.BackgroundTransparency = 1 - 0.28 * niebla
	local a = math.clamp(altitud / 9000, 0, 1)
	local t = if bioma then tinte else 0
	local clave = math.floor(t * 40) * 1000000 + math.floor(a * 200) * 1000 + math.floor(niebla * 200)
	if atmosfera and ambienteBase and (clave ~= ultimoAmbiente or (densidadEscrita ~= nil and math.abs(atmosfera.Density - (densidadEscrita :: number)) > 1e-3)) then
		ultimoAmbiente = clave
		local color = ambienteBase.color:Lerp(AZUL_ALTO, 0.45 * a)
		local decay = ambienteBase.decay:Lerp(DECAY_ALTO, 0.5 * a)
		local haze = ambienteBase.haze * (1 - 0.5 * a)
		if bioma then
			color = color:Lerp(bioma.color, 0.65 * t)
			decay = decay:Lerp(bioma.decay, 0.65 * t)
			haze += bioma.haze * t
		end
		atmosfera.Color = color:Lerp(BLANCO_NUBE, niebla)
		atmosfera.Decay = decay:Lerp(BLANCO_NUBE, niebla)
		atmosfera.Haze = haze * (1 - niebla) + 3.5 * niebla
		atmosfera.Glare = (ambienteBase.glare + 0.45 * a) * (1 - niebla)
		if densidadEscrita == nil or math.abs(atmosfera.Density - (densidadEscrita :: number)) > 1e-3 then
			densidadAjena = atmosfera.Density
		end
		atmosfera.Density = densidadAjena + math.max(0, 0.82 - densidadAjena) * niebla
		densidadEscrita = atmosfera.Density
	end
	local viento = Vector3.new(0, 0, 4 + math.min(velocidad * 0.5, 40))
	if (Workspace.GlobalWind - viento).Magnitude > 1 then
		Workspace.GlobalWind = viento
	end
end

local function desfase(ti: number, tj: number): number
	return ((ti * 7919 + tj * 104729) % 997) / 997 * 1000 - 500
end

local function actualizar(dt: number)
	local fase = avion:GetAttribute("Fase")
	local enAire = fase == "Despegue" or fase == "Vuelo" or fase == "Aproximacion" or fase == "Frenando" or fase == "Estrellado" or fase == "Aterrizado"
	if not enAire then
		if carpeta.Parent then
			carpeta.Parent = nil
			restaurar()
		end
		return
	end
	local bajos = jugador:GetAttribute("GraficosBajos") == true
	if not carpeta.Parent then
		carpeta.Parent = Workspace
		rumbo = 0
		nubesAltas.Enabled = not bajos
	end
	dt *= if avion:GetAttribute("Pausa") == true then 0 else ritmo
	if fase == "Estrellado" and numero("Altitud") <= 1 then
		frenado *= math.exp(-dt * 2.5)
	else
		frenado = 1
	end
	if fase == "Despegue" and faseAnterior ~= "Despegue" then
		recorrido = 0
		table.clear(celdas)
		centroVentana = math.huge
	end
	faseAnterior = if typeof(fase) == "string" then fase else ""
	local deseado = biomaDeseado()
	if deseado ~= biomaActivo then
		local anterior = if biomaActivo then reservas[biomaActivo] else nil
		if anterior then
			ocultarReserva(anterior)
		end
		biomaActivo = deseado
		table.clear(celdas)
		centroVentana = math.huge
		for i in tonoSuelos do
			tonoSuelos[i] = -1
		end
	end
	local reserva = if biomaActivo then reservaDe(biomaActivo) else nil
	local velocidad = numero("Velocidad") / 3.6 * ESCALA_VELOCIDAD * frenado
	local altitud = numero("Altitud")
	local alabeo = numero("Alabeo")
	local cab = numero("Cabeceo")
	local giro = math.rad(alabeo * 0.09) * dt
	posicion += CFrame.Angles(0, -rumbo, 0) * Vector3.new(0, 0, -velocidad * dt)
	rumbo += giro
	local giroMundo = CFrame.Angles(0, rumbo, 0)
	local inverso = CFrame.Angles(0, -rumbo, 0)
	local actitud = CFrame.new(PIVOTE) * CFrame.Angles(0, 0, math.rad(alabeo)) * CFrame.Angles(math.rad(-cab), 0, 0)
	local avance = Vector3.new(0, 0, velocidad * dt)
	local yaw = CFrame.Angles(0, giro, 0)
	local alturaSuelo = -(10 + altitud * ESCALA_ALTURA)
	if fase == "Frenando" or fase == "Aterrizado" then
		rodado += velocidad * dt
	else
		rodado = 0
	end
	local zDestino = -(numero("Total") - numero("Distancia")) * KM + rodado
	local hayDestino = reserva ~= nil and fase ~= "Despegue" and zDestino > -VISTA_DESTINO * 2
	local frente = zDestino + FRENTE
	local tinte = if hayDestino then math.clamp((6000 + zDestino) / 4000, 0, 1) else 0
	local colorBioma = if biomaActivo then Destinos.COLORES[biomaActivo] or VERDE else VERDE
	local k = 0
	for gx = -2, 2 do
		for gz = -2, 2 do
			k += 1
			marcos[suelos[k]] = actitud * CFrame.new(gx * 2048, alturaSuelo - 2.7, gz * 2048)
			local tono = if hayDestino then math.round(math.clamp((frente + 1500 - gz * 2048) / 3000, 0, 1) * 10) else 0
			if tono ~= tonoSuelos[k] then
				tonoSuelos[k] = tono
				partes[suelos[k]].Color = VERDE:Lerp(colorBioma, tono / 10)
			end
		end
	end
	recorrido += velocidad * dt
	local hayFijos = hayDestino and reserva ~= nil and #reserva.fijos > 0 and zDestino > -VISTA_DESTINO
	local enDestino = fase == "Aproximacion" or fase == "Frenando" or fase == "Aterrizado"
	local zPista = if enDestino then zDestino else -200 + recorrido
	marcos[iPista] = if enDestino and hayFijos then OCULTO else actitud * CFrame.new(0, alturaSuelo + 0.25, zPista)
	local mitad = if hayFijos and reserva then reserva.mitad else Vector3.zero
	if reserva then
		local base = actitud * CFrame.new(0, alturaSuelo, zDestino)
		for _, f in reserva.fijos do
			marcos[f.i] = if hayFijos then base * CFrame.new(f.centro) * f.giro else OCULTO
		end
	end
	local ci, cj = math.floor(posicion.X / LOSETA), math.floor(posicion.Z / LOSETA)
	local centro = ci * 4096 + cj
	if centro ~= centroVentana then
		centroVentana = centro
		local quedan: { [number]: boolean } = {}
		for di = -1, 1 do
			for dj = -1, 1 do
				local clave = (ci + di) * 4096 + cj + dj
				if celdas[clave] ~= nil then
					quedan[clave] = celdas[clave]
				end
			end
		end
		celdas = quedan
	end
	local function esBioma(ti: number, tj: number, fijar: boolean): boolean
		local clave = ti * 4096 + tj
		local c = celdas[clave]
		if c ~= nil then
			return c
		end
		local rel = giroMundo * Vector3.new((ti + 0.5) * LOSETA - posicion.X, 0, (tj + 0.5) * LOSETA - posicion.Z)
		local si = hayDestino and rel.Z < frente + desfase(ti, tj)
		if fijar then
			celdas[clave] = si
		end
		return si
	end
	local usados = { 0, 0 }
	local usadosBioma = { 0, 0 }
	for di = -1, 1 do
		for dj = -1, 1 do
			local ti, tj = ci + di, cj + dj
			local h = (ti * 7 + tj * 13 + ti * tj * 3) % 8
			local rel = giroMundo * Vector3.new((ti + 0.5) * LOSETA - posicion.X, 0, (tj + 0.5) * LOSETA - posicion.Z)
			local v = h % 2 + 1
			if reserva and esBioma(ti, tj, true) and #reserva.losetas[v] + #reserva.losetas[3 - v] > 0 then
				if #reserva.losetas[v] == 0 then
					v = 3 - v
				end
				usadosBioma[v] += 1
				local l = reserva.losetas[v][usadosBioma[v]]
				marcos[l.i] = actitud * CFrame.new(rel.X, alturaSuelo - HUNDIDO - l.medio, rel.Z) * giroMundo * l.giro
				continue
			end
			if #losetas[v] == 0 then
				v = 3 - v
			end
			local lista = losetas[v]
			if #lista > 0 then
				usados[v] += 1
				local l = lista[usados[v]]
				marcos[l.i] = actitud * CFrame.new(rel.X, alturaSuelo - l.medio, rel.Z) * giroMundo * CFrame.Angles(0, math.floor(h / 2) % 4 * math.pi / 2, 0) * l.giro
			end
		end
	end
	for v = 1, 2 do
		for n = usados[v] + 1, #losetas[v] do
			marcos[losetas[v][n].i] = OCULTO
		end
		if reserva then
			for n = usadosBioma[v] + 1, #reserva.losetas[v] do
				marcos[reserva.losetas[v][n].i] = OCULTO
			end
		end
	end
	local function tapado(a: Adorno): boolean
		return hayFijos and math.abs(a.rel.X) < a.radio + mitad.X and math.abs(a.rel.Z - zDestino) < a.radio + mitad.Z
	end
	local function celdaBioma(rel: Vector3): boolean
		if not reserva then
			return false
		end
		local w = posicion + inverso * rel
		return esBioma(math.floor(w.X / LOSETA), math.floor(w.Z / LOSETA), false)
	end
	for _, a in adornos do
		a.rel = envolver(yaw * (a.rel + avance), RADIO_SUELO, 0)
		local enPista = math.abs(a.rel.X) < a.radio + 30 and math.abs(a.rel.Z - zPista) < a.radio + 280
		marcos[a.i] = if enPista or (bajos and a.extra) or tapado(a) or celdaBioma(a.rel) then OCULTO else actitud * CFrame.new(a.rel.X, alturaSuelo + a.alto, a.rel.Z) * giroMundo * a.giro
	end
	if reserva then
		for _, a in reserva.adornos do
			local rel, renacida = envolver(yaw * (a.rel + avance), a.envoltura, 0)
			if renacida and a.grande then
				rel = Vector3.new(fueraDelPasillo(rel.X, a.radio), 0, rel.Z)
			end
			a.rel = rel
			local visible = hayDestino and not (bajos and a.extra) and not tapado(a) and celdaBioma(rel)
			marcos[a.i] = if visible then actitud * CFrame.new(rel.X, alturaSuelo - HUNDIDO + a.alto, rel.Z) * giroMundo * a.giro else OCULTO
		end
	end
	local deriva = VIENTO * dt
	local objetivo = 0
	for _, n in nubes do
		local rel, renacida = envolver(yaw * (n.rel + avance) + deriva, RADIO_NUBES, n.capa.carril)
		if renacida then
			n.base = rng:NextNumber(n.capa.base[1], n.capa.base[2])
		end
		n.rel = rel
		local m = n.medio
		local y = (n.base - altitud) * ESCALA_ALTURA + m.Y
		local giroTotal = giroMundo * n.giro
		marcos[n.i] = if bajos and n.extra then OCULTO else actitud * CFrame.new(rel.X, y, rel.Z) * giroTotal
		local borde = math.max(math.abs(rel.X), math.abs(rel.Z))
		local alfa = math.round(math.clamp((borde - RADIO_NUBES + 700) / 600, 0, 1) * 8) / 8
		if alfa ~= n.alfa then
			n.alfa = alfa
			n.parte.Transparency = alfa
		end
		local alcance = m.X + m.Z
		if not (bajos and n.extra) and math.abs(y) < m.Y and math.abs(rel.X) < alcance and math.abs(rel.Z) < alcance then
			local l = giroTotal:VectorToObjectSpace(Vector3.new(-rel.X, -y, -rel.Z))
			local dentroNube = if n.capa.manto
				then (1 - (l.X / (m.X * 0.8)) ^ 2 - (l.Z / (m.Z * 0.8)) ^ 2) * (1 - (l.Y / m.Y) ^ 2)
				else 1 - (l.X / (m.X * 0.85)) ^ 2 - (l.Y / (m.Y * 0.9)) ^ 2 - (l.Z / (m.Z * 0.85)) ^ 2
			objetivo = math.max(objetivo, math.min(1, dentroNube * 2.5))
		end
	end
	Workspace:BulkMoveTo(partes, marcos, Enum.BulkMoveMode.FireCFrameChanged)
	ambiente(dt, altitud, velocidad, objetivo, if hayDestino and reserva then reserva.bioma else nil, if enDestino then 1 else tinte)
end

function Mundo.fijarRitmo(r: number)
	ritmo = r
end

function Mundo.iniciar()
	construir()
	RunService.PreRender:Connect(actualizar)
end

return Mundo
