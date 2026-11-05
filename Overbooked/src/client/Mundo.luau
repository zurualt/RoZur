--!strict
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Cielo = require(ReplicatedStorage.Shared.Cielo)
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
}

type Adorno = {
	i: number,
	rel: Vector3,
	giro: CFrame,
	alto: number,
	radio: number,
}

type Loseta = {
	i: number,
	giro: CFrame,
	medio: number,
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

local avion = Workspace:WaitForChild("Avion") :: Model
local PIVOTE = Vector3.new(0, 100, -18)
local ESCALA_ALTURA = 0.07
local ESCALA_VELOCIDAD = 0.35
local RADIO_NUBES = 2800
local RADIO_SUELO = 2400
local LOSETA = 2048
local CARRIL = 130
local OCULTO = CFrame.new(0, -20000, 0)
local VIENTO = Vector3.new(3, 0, 5)
local AZUL_ALTO = Color3.fromRGB(150, 190, 240)
local DECAY_ALTO = Color3.fromRGB(90, 140, 215)
local BLANCO_NUBE = Color3.fromRGB(236, 240, 247)
local rng = Random.new()

local carpeta = Instance.new("Folder")
carpeta.Name = "CieloLocal"
local partes: { BasePart } = {}
local marcos: { CFrame } = {}
local suelos: { number } = {}
local iPista = 0
local nubes: { Nube } = {}
local adornos: { Adorno } = {}
local losetas: { { Loseta } } = { {}, {} }
local listos: { [string]: boolean } = {}
local posicion = Vector3.zero
local rumbo = 0
local recorrido = 0
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

local function llegar(plantilla: Instance)
	if not plantilla:IsA("BasePart") or listos[plantilla.Name] then
		return
	end
	local nombre = plantilla.Name
	listos[nombre] = true
	local rot = plantilla.CFrame.Rotation
	for _, capa in CAPAS do
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
				})
			end
		end
	end
	local adorno = ADORNOS[nombre]
	if adorno then
		for _ = 1, adorno[1] do
			local p = clonar(plantilla, Vector3.one * rng:NextNumber(adorno[2], adorno[3]))
			table.insert(adornos, {
				i = registrar(p),
				rel = Vector3.new(rng:NextNumber(-RADIO_SUELO, RADIO_SUELO), 0, rng:NextNumber(-RADIO_SUELO, RADIO_SUELO)),
				giro = CFrame.Angles(0, rng:NextNumber(0, 2 * math.pi), 0) * rot,
				alto = p.Size.Y / 2,
				radio = math.max(p.Size.X, p.Size.Z) / 2,
			})
		end
	end
	local v = table.find(VARIANTES, nombre)
	if v then
		for _ = 1, 9 do
			local p = clonar(plantilla, Vector3.one)
			table.insert(losetas[v], { i = registrar(p), giro = rot, medio = p.Size.Y / 2 })
		end
	end
end

local function construir()
	for _ = 1, 25 do
		table.insert(suelos, nueva(Vector3.new(2048, 2, 2048), Color3.fromRGB(112, 176, 84), Enum.Material.SmoothPlastic))
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

local function restaurar()
	niebla = 0
	dentro = false
	velo.BackgroundTransparency = 1
	nubesAltas.Enabled = altasAntes
	Workspace.GlobalWind = vientoAntes
	if atmosfera and ambienteBase then
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

local function ambiente(dt: number, altitud: number, velocidad: number, objetivo: number)
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
	if atmosfera and ambienteBase then
		local a = math.clamp(altitud / 9000, 0, 1)
		atmosfera.Color = ambienteBase.color:Lerp(AZUL_ALTO, 0.45 * a):Lerp(BLANCO_NUBE, niebla)
		atmosfera.Decay = ambienteBase.decay:Lerp(DECAY_ALTO, 0.5 * a):Lerp(BLANCO_NUBE, niebla)
		atmosfera.Haze = ambienteBase.haze * (1 - 0.5 * a) * (1 - niebla) + 3.5 * niebla
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
	if not carpeta.Parent then
		carpeta.Parent = Workspace
		rumbo = 0
		nubesAltas.Enabled = true
	end
	if fase == "Despegue" and faseAnterior ~= "Despegue" then
		recorrido = 0
	end
	faseAnterior = if typeof(fase) == "string" then fase else ""
	local velocidad = numero("Velocidad") / 3.6 * ESCALA_VELOCIDAD
	local altitud = numero("Altitud")
	local alabeo = numero("Alabeo")
	local cab = numero("Cabeceo")
	local giro = math.rad(alabeo * 0.09) * dt
	posicion += CFrame.Angles(0, -rumbo, 0) * Vector3.new(0, 0, -velocidad * dt)
	rumbo += giro
	local giroMundo = CFrame.Angles(0, rumbo, 0)
	local actitud = CFrame.new(PIVOTE) * CFrame.Angles(0, 0, math.rad(alabeo)) * CFrame.Angles(math.rad(-cab), 0, 0)
	local avance = Vector3.new(0, 0, velocidad * dt)
	local yaw = CFrame.Angles(0, giro, 0)
	local alturaSuelo = -(10 + altitud * ESCALA_ALTURA)
	local k = 0
	for gx = -2, 2 do
		for gz = -2, 2 do
			k += 1
			marcos[suelos[k]] = actitud * CFrame.new(gx * 2048, alturaSuelo - 1.6, gz * 2048)
		end
	end
	recorrido += velocidad * dt
	local zPista = if fase == "Aproximacion" or fase == "Frenando" or fase == "Aterrizado" then -(numero("Total") - numero("Distancia")) * 30 else -200 + recorrido
	marcos[iPista] = actitud * CFrame.new(0, alturaSuelo + 0.25, zPista)
	local ci, cj = math.floor(posicion.X / LOSETA), math.floor(posicion.Z / LOSETA)
	local usados = { 0, 0 }
	for di = -1, 1 do
		for dj = -1, 1 do
			local ti, tj = ci + di, cj + dj
			local h = (ti * 7 + tj * 13 + ti * tj * 3) % 8
			local v = h % 2 + 1
			if #losetas[v] == 0 then
				v = 3 - v
			end
			local lista = losetas[v]
			if #lista > 0 then
				usados[v] += 1
				local l = lista[usados[v]]
				local rel = giroMundo * Vector3.new((ti + 0.5) * LOSETA - posicion.X, 0, (tj + 0.5) * LOSETA - posicion.Z)
				marcos[l.i] = actitud * CFrame.new(rel.X, alturaSuelo - l.medio, rel.Z) * giroMundo * CFrame.Angles(0, math.floor(h / 2) % 4 * math.pi / 2, 0) * l.giro
			end
		end
	end
	for v = 1, 2 do
		for n = usados[v] + 1, #losetas[v] do
			marcos[losetas[v][n].i] = OCULTO
		end
	end
	for _, a in adornos do
		a.rel = envolver(yaw * (a.rel + avance), RADIO_SUELO, 0)
		local enPista = math.abs(a.rel.X) < a.radio + 30 and math.abs(a.rel.Z - zPista) < a.radio + 280
		marcos[a.i] = if enPista then OCULTO else actitud * CFrame.new(a.rel.X, alturaSuelo + a.alto, a.rel.Z) * giroMundo * a.giro
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
		marcos[n.i] = actitud * CFrame.new(rel.X, y, rel.Z) * giroTotal
		local borde = math.max(math.abs(rel.X), math.abs(rel.Z))
		local alfa = math.round(math.clamp((borde - RADIO_NUBES + 700) / 600, 0, 1) * 8) / 8
		if alfa ~= n.alfa then
			n.alfa = alfa
			n.parte.Transparency = alfa
		end
		local alcance = m.X + m.Z
		if math.abs(y) < m.Y and math.abs(rel.X) < alcance and math.abs(rel.Z) < alcance then
			local l = giroTotal:VectorToObjectSpace(Vector3.new(-rel.X, -y, -rel.Z))
			local dentroNube = if n.capa.manto
				then (1 - (l.X / (m.X * 0.8)) ^ 2 - (l.Z / (m.Z * 0.8)) ^ 2) * (1 - (l.Y / m.Y) ^ 2)
				else 1 - (l.X / (m.X * 0.85)) ^ 2 - (l.Y / (m.Y * 0.9)) ^ 2 - (l.Z / (m.Z * 0.85)) ^ 2
			objetivo = math.max(objetivo, math.min(1, dentroNube * 2.5))
		end
	end
	Workspace:BulkMoveTo(partes, marcos, Enum.BulkMoveMode.FireCFrameChanged)
	ambiente(dt, altitud, velocidad, objetivo)
end

function Mundo.iniciar()
	construir()
	RunService.PreRender:Connect(actualizar)
end

return Mundo
