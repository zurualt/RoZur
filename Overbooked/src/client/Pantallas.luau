--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Gui = require(ReplicatedStorage.Shared.Gui)
local VFX = require(ReplicatedStorage.Shared.VFX)

type Marca = { punto: Frame, borde: UIStroke, icono: ImageLabel, angulo: number, conIcono: boolean }
type Objetivo = { x: number, y: number, color: Color3, tamano: number, icono: string? }
type Figura = { cuerpo: Part, cabeza: Part }
type Contador = { icono: ImageLabel, numero: TextLabel, valor: number }

local Pantallas = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local Estado = ReplicatedStorage:WaitForChild("Estado")
local P = Config.PANTALLAS
local VERDE = Color3.fromRGB(120, 255, 150)
local FONDO_RADAR = Color3.fromRGB(8, 40, 22)
local BLANCO = Color3.new(1, 1, 1)
local AZUL = Color3.fromRGB(120, 170, 255)
local CIELO = Color3.fromRGB(143, 211, 244)
local CENTRO_PIRATAS = Vector3.new(0, 105, -18)
local OCULTO = CFrame.new(0, -500, 0)
local CAMARAS = {
	{ zona = "PASILLO", cf = CFrame.lookAt(Vector3.new(0, 109, -50.8), Vector3.new(0, 101, -24)) },
	{ zona = "COLA", cf = CFrame.lookAt(Vector3.new(-3.5, 108.8, -30), Vector3.new(1.5, 101.5, -8)) },
}
local NO_COPIAR: { [string]: boolean } = { LuzFila = true, BalizaLuz = true }
local BANDADA = { { 0, 0 }, { -0.05, 0.04 }, { 0.05, 0.04 }, { -0.1, 0.08 }, { 0.1, 0.08 } }
local rng = Random.new()

local marcas: { Marca } = {}
local objetivos: { Objetivo } = {}
local estela: { Frame } = {}
local barrido = 0
local bandadaHasta = 0
local aviso: TextLabel
local avisoActual = ""
local avisoUrgente = false

local vista: ViewportFrame
local camaraMonitor: Camera
local figuras: { Figura } = {}
local extras: { Part } = {}
local contadores: { [string]: Contador } = {}
local ruido: { Frame } = {}
local etiquetaCam: TextLabel
local etiquetaZona: TextLabel
local rec: Frame
local alerta: Frame
local rodillo: Frame
local construida = false
local camaraIndice = 0
local proximoCambio = 0
local estaticaHasta = 0

local function atributo(i: Instance, nombre: string, defecto: number): number
	local v = i:GetAttribute(nombre)
	return if typeof(v) == "number" then v else defecto
end

local function prueba(): string?
	if not RunService:IsStudio() then
		return nil
	end
	local v = Workspace:GetAttribute("PruebaRadar")
	return if typeof(v) == "string" and v ~= "" then v else nil
end

local function superficie(nombre: string, parte: BasePart, lienzo: Vector2, brillo: number): SurfaceGui
	local s = Instance.new("SurfaceGui")
	s.Name = nombre
	s.Adornee = parte
	s.Face = Enum.NormalId.Front
	s.SizingMode = Enum.SurfaceGuiSizingMode.FixedSize
	s.CanvasSize = lienzo
	s.LightInfluence = 0
	s.Brightness = brillo
	s.MaxDistance = P.DISTANCIA
	s.ResetOnSpawn = false
	s.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	s.Parent = jugador:WaitForChild("PlayerGui")
	return s
end

local function redondo(f: GuiObject)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(1, 0)
	c.Parent = f
end

local function marco(padre: Instance, tamano: UDim2, posicion: UDim2, color: Color3, transparencia: number): Frame
	local f = Instance.new("Frame")
	f.AnchorPoint = Vector2.new(0.5, 0.5)
	f.Size = tamano
	f.Position = posicion
	f.BackgroundColor3 = color
	f.BackgroundTransparency = transparencia
	f.BorderSizePixel = 0
	f.Parent = padre
	return f
end

local function crearRadar(parte: BasePart): SurfaceGui
	local s = superficie("Radar", parte, Vector2.new(360, 360), 1.6)
	local fondo = marco(s, UDim2.fromScale(1, 1), UDim2.fromScale(0.5, 0.5), FONDO_RADAR, 0)
	redondo(fondo)
	local brillo = Instance.new("ImageLabel")
	brillo.BackgroundTransparency = 1
	brillo.AnchorPoint = Vector2.new(0.5, 0.5)
	brillo.Position = UDim2.fromScale(0.5, 0.5)
	brillo.Size = UDim2.fromScale(1, 1)
	brillo.Image = VFX.textura("Brillo")
	brillo.ImageColor3 = VERDE
	brillo.ImageTransparency = 0.82
	brillo.Parent = fondo
	for _, r in { 0.33, 0.66, 0.96 } do
		local anillo = marco(fondo, UDim2.fromScale(r, r), UDim2.fromScale(0.5, 0.5), VERDE, 1)
		redondo(anillo)
		local trazo = Instance.new("UIStroke")
		trazo.Color = VERDE
		trazo.Thickness = 2
		trazo.Transparency = 0.55
		trazo.Parent = anillo
	end
	marco(fondo, UDim2.new(0.96, 0, 0, 2), UDim2.fromScale(0.5, 0.5), VERDE, 0.72)
	marco(fondo, UDim2.new(0, 2, 0.96, 0), UDim2.fromScale(0.5, 0.5), VERDE, 0.72)
	for k = 0, 9 do
		local giro = marco(fondo, UDim2.fromScale(1, 1), UDim2.fromScale(0.5, 0.5), VERDE, 1)
		giro.ZIndex = 2
		local linea = Instance.new("Frame")
		linea.AnchorPoint = Vector2.new(0, 0.5)
		linea.Position = UDim2.fromScale(0.5, 0.5)
		linea.Size = UDim2.new(0.47, 0, 0, if k == 0 then 4 else 9)
		linea.BackgroundColor3 = VERDE
		linea.BackgroundTransparency = if k == 0 then 0 else 0.62 + k * 0.035
		linea.BorderSizePixel = 0
		linea.ZIndex = 2
		linea.Parent = giro
		table.insert(estela, giro)
	end
	for _ = 1, 24 do
		local punto = marco(fondo, UDim2.fromOffset(14, 14), UDim2.fromScale(0.5, 0.5), VERDE, 0)
		punto.Visible = false
		redondo(punto)
		local borde = Instance.new("UIStroke")
		borde.Color = Gui.TINTA
		borde.Thickness = 2
		borde.Parent = punto
		local icono = Gui.icono(punto, nil, UDim2.fromOffset(42, 42), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5))
		table.insert(marcas, { punto = punto, borde = borde, icono = icono, angulo = 0, conIcono = false })
	end
	local propio = Gui.icono(fondo, "Avion", UDim2.fromOffset(46, 46), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5))
	propio.ZIndex = 4
	propio.Rotation = -90
	local titulo = Gui.texto(fondo, "RADAR", UDim2.fromScale(0.4, 0.085), UDim2.fromScale(0.5, 0.15), VERDE, false)
	titulo.AnchorPoint = Vector2.new(0.5, 0.5)
	titulo.ZIndex = 5
	aviso = Gui.texto(fondo, "DESPEJADO", UDim2.fromScale(0.74, 0.12), UDim2.fromScale(0.5, 0.79), VERDE, true)
	aviso.AnchorPoint = Vector2.new(0.5, 0.5)
	aviso.ZIndex = 5
	Gui.trazado(aviso)
	avisoActual = "DESPEJADO"
	return s
end

local function anadir(x: number, y: number, color: Color3, tamano: number, icono: string?)
	table.insert(objetivos, { x = x, y = y, color = color, tamano = tamano, icono = icono })
end

local function polar(r: number, a: number): (number, number)
	return math.sin(a) * r, -math.cos(a) * r
end

local function bandada(r: number, a: number)
	local cx, cy = polar(r, a)
	for _, d in BANDADA do
		anadir(cx + d[1], cy + d[2], BLANCO, 10)
	end
end

local function nube(cx: number, cy: number, escala: number)
	for k = 0, 3 do
		local a = k * 1.7 + os.clock() * 0.2
		anadir(cx + math.cos(a) * 0.08 * escala, cy + math.sin(a) * 0.06 * escala, Gui.AMARILLO, math.floor(50 * escala))
	end
end

local function rumbo(semilla: number, ancho: number): number
	return math.clamp(math.noise(semilla % 997 * 0.731, 0.5) * 2.5, -1, 1) * ancho
end

local function calcularRadar(): (string, Color3)
	table.clear(objetivos)
	local mejor, texto, color = 0, "DESPEJADO", VERDE
	local function avisar(prioridad: number, t: string, c: Color3)
		if prioridad > mejor then
			mejor, texto, color = prioridad, t, c
		end
	end
	local p = prueba()
	local tipo = avion:GetAttribute("Radar")
	local hora = atributo(avion, "RadarHora", 0)
	local restante = hora - Workspace:GetServerTimeNow()
	local pendientes: { string } = {}
	if p and p ~= "Pista" then
		restante = P.RADAR_ANTELACION * (1 - (os.clock() % 9) / 9)
		hora = 7
		pendientes = if p == "Todo" then { "Pajaros", "Tormenta", "Piratas" } else { p }
	elseif typeof(tipo) == "string" and restante > 0 and restante < P.RADAR_ANTELACION then
		pendientes = { tipo }
	end
	local r = 0.12 + 0.83 * math.clamp(restante / P.RADAR_ANTELACION, 0, 1)
	local cerca = restante < P.RADAR_AVISO
	for i, t in pendientes do
		local a = rumbo(hora + i * 3.1, if t == "Piratas" then math.pi else 0.7)
		if t == "Pajaros" then
			bandada(r, a)
			if cerca then
				avisar(3, "¡PÁJAROS DELANTE!", Gui.AMARILLO)
			end
		elseif t == "Tormenta" then
			local x, y = polar(r, a)
			nube(x, y, 1.3)
			if cerca then
				avisar(2, "¡TORMENTA DELANTE!", Gui.AMARILLO)
			end
		elseif t == "Piratas" then
			for k = -1, 1 do
				local x, y = polar(r + math.abs(k) * 0.06, a + k * 0.25)
				anadir(x, y, Gui.ROJO, 14, "Pirata")
			end
			if cerca then
				avisar(4, "¡PIRATAS A LA VISTA!", Gui.ROJO)
			end
		end
	end
	if os.clock() < bandadaHasta then
		bandada((bandadaHasta - os.clock()) / 3 * 0.12, 0)
		avisar(5, "¡PÁJAROS DELANTE!", Gui.ROJO)
	end
	if avion:GetAttribute("Tormenta") == true then
		nube(-0.3, -0.25, 1.2)
		nube(0.32, 0.05, 1)
		nube(-0.08, 0.38, 0.9)
		avisar(3, "¡DENTRO DE LA TORMENTA!", Gui.AMARILLO)
	end
	local piratas = avion:FindFirstChild("Piratas")
	if piratas then
		local t = Workspace:GetServerTimeNow()
		for _, f in piratas:GetChildren() do
			if atributo(f, "Vida", 0) <= 0 then
				continue
			end
			local a = atributo(f, "Fase", 0) + atributo(f, "Velocidad", 0) * (t - atributo(f, "Inicio", t))
			local radio = atributo(f, "Radio", 100)
			local pos = CENTRO_PIRATAS + Vector3.new(math.cos(a) * radio, 0, math.sin(a) * radio * 0.7)
			anadir((pos.X - CENTRO_PIRATAS.X) / 165, (pos.Z - CENTRO_PIRATAS.Z) / 165, Gui.ROJO, 14, "Pirata")
			avisar(6, "¡PIRATAS ALREDEDOR!", Gui.ROJO)
		end
	end
	local quedan: number? = nil
	local desvio = atributo(avion, "Desvio", 0)
	if p == "Pista" or p == "Todo" then
		quedan = 75 - (os.clock() % 30) * 2.2
		desvio = 18 * math.sin(os.clock() * 0.4)
	elseif avion:GetAttribute("Fase") == "Aproximacion" then
		quedan = atributo(avion, "Total", 0) - atributo(avion, "Distancia", 0)
	end
	if quedan then
		local x, y = polar(math.clamp(quedan / Config.VUELO.APROXIMACION, 0.04, 1) * 0.88, -math.rad(desvio))
		anadir(x, y, VERDE, 14, "Aterrizaje")
		avisar(1, `PISTA A {math.max(0, math.floor(quedan))} KM`, VERDE)
	end
	return texto, color
end

local function pintarRadar(texto: string, color: Color3)
	for i, m in marcas do
		local o = objetivos[i]
		if not o then
			m.punto.Visible = false
			continue
		end
		local x, y = o.x, o.y
		local r = math.sqrt(x * x + y * y)
		if r > 0.9 then
			x, y = x / r * 0.9, y / r * 0.9
		end
		m.punto.Position = UDim2.fromScale(0.5 + x * 0.5, 0.5 + y * 0.5)
		m.punto.Size = UDim2.fromOffset(o.tamano, o.tamano)
		m.punto.BackgroundColor3 = o.color
		m.punto.ZIndex = if o.tamano > 30 then 1 else 3
		m.angulo = math.atan2(y, x) % (2 * math.pi)
		m.conIcono = o.icono ~= nil
		m.borde.Enabled = o.icono == nil and o.tamano <= 30
		Gui.ponerIcono(m.icono, o.icono)
		m.punto.Visible = true
	end
	if texto ~= avisoActual then
		avisoActual = texto
		aviso.Text = texto
	end
	aviso.TextColor3 = color
	avisoUrgente = color ~= VERDE
end

local function animarRadar(dt: number)
	barrido = (barrido + dt * 2.4) % (2 * math.pi)
	local grados = math.deg(barrido)
	for k, giro in estela do
		giro.Rotation = grados - (k - 1) * 3.2
	end
	for _, m in marcas do
		if m.punto.Visible then
			local luz = 1 - ((barrido - m.angulo) % (2 * math.pi)) / (2 * math.pi)
			m.punto.BackgroundTransparency = if m.conIcono then 1 elseif m.punto.ZIndex == 1 then 0.95 - 0.55 * luz else 0.8 - 0.8 * luz
			m.icono.ImageTransparency = 0.55 * (1 - luz)
		end
	end
	aviso.TextTransparency = if avisoUrgente and os.clock() % 0.7 > 0.45 then 0.75 else 0
end

local function bloque(padre: Instance, origen: BasePart)
	local b = Instance.new("Part")
	b.Anchored = true
	b.CanCollide = false
	b.CanQuery = false
	b.CanTouch = false
	b.CastShadow = false
	b.Size = origen.Size
	b.CFrame = origen.CFrame
	b.Material = Enum.Material.SmoothPlastic
	b.Color = if origen.Name == "Cristal" then CIELO else origen.Color
	if origen:IsA("Part") then
		b.Shape = origen.Shape
	end
	b.Parent = padre
end

local function copiarCabina()
	local modelo = Instance.new("Model")
	modelo.Name = "Cabina"
	for _, nombre in { "Estructura", "Asientos", "Altillos", "Cocina", "Puertas" } do
		local raiz = avion:FindFirstChild(nombre)
		if not raiz then
			continue
		end
		for _, d in raiz:GetDescendants() do
			if not d:IsA("BasePart") or d:IsA("MeshPart") or NO_COPIAR[d.Name] then
				continue
			end
			local p = d.Position
			if p.Z < -53 or p.Z > 1 or math.abs(p.X) > 7.6 then
				continue
			end
			local dueno = d:FindFirstAncestorOfClass("Model")
			if (dueno and dueno ~= avion and dueno.Name ~= "Ventana") or (d:GetAttribute("Visual") ~= nil and d.Color == BLANCO) then
				continue
			end
			bloque(modelo, d)
		end
	end
	modelo.Parent = vista
end

local function pieza(forma: Enum.PartType, huevo: boolean): Part
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Material = Enum.Material.SmoothPlastic
	p.Shape = forma
	if huevo then
		local m = Instance.new("SpecialMesh")
		m.MeshType = Enum.MeshType.Sphere
		m.Parent = p
	end
	p.CFrame = OCULTO
	p.Parent = vista
	return p
end

local function persona(i: number, cuerpo: CFrame, cabeza: CFrame, colorCuerpo: Color3, colorCabeza: Color3)
	local f = figuras[i]
	if not f then
		local nueva: Figura = { cuerpo = pieza(Enum.PartType.Block, true), cabeza = pieza(Enum.PartType.Ball, false) }
		nueva.cuerpo.Size = Vector3.new(1.7, 2.3, 1.5)
		nueva.cabeza.Size = Vector3.new(1.5, 1.5, 1.5)
		figuras[i] = nueva
		f = nueva
	end
	f.cuerpo.CFrame = cuerpo
	f.cuerpo.Color = colorCuerpo
	f.cabeza.CFrame = cabeza
	f.cabeza.Color = colorCabeza
end

local function extra(i: number, cf: CFrame, tamano: Vector3, color: Color3, forma: Enum.PartType, neon: boolean)
	local p = extras[i]
	if not p then
		p = pieza(forma, false)
		extras[i] = p
	end
	p.Shape = forma
	p.Size = tamano
	p.CFrame = cf
	p.Color = color
	p.Material = if neon then Enum.Material.Neon else Enum.Material.SmoothPlastic
end

local function dentro(p: Vector3): boolean
	return math.abs(p.X) < 7.6 and p.Y > 98 and p.Y < 112 and p.Z > -53 and p.Z < 1
end

local function cuenta(nombre: string, valor: number)
	local c = contadores[nombre]
	if not c or c.valor == valor then
		return
	end
	c.valor = valor
	c.numero.Text = tostring(valor)
	c.numero.TextColor3 = if valor > 0 then Gui.ROJO else BLANCO
	c.numero.TextTransparency = if valor > 0 then 0 else 0.55
	c.icono.ImageTransparency = if valor > 0 then 0 else 0.6
end

local function actualizarMonitor()
	local n = 0
	for _, otro in Players:GetPlayers() do
		local personaje = otro.Character
		local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
		if n < P.MONITOR_FIGURAS and raiz and raiz:IsA("BasePart") and dentro(raiz.Position) then
			local color = otro:GetAttribute("Color")
			n += 1
			persona(n, raiz.CFrame, raiz.CFrame * CFrame.new(0, 2, 0), if typeof(color) == "Color3" then color else Gui.NARANJA, Color3.fromRGB(255, 214, 170))
		end
	end
	local enfadados = 0
	for _, m in CollectionService:GetTagged("Pasajero") do
		local cuerpo = m:FindFirstChild("Cuerpo")
		if not cuerpo or not cuerpo:IsA("BasePart") or not dentro(cuerpo.Position) then
			continue
		end
		local enfado = atributo(m, "Satisfaccion", 1) < 0.35 or m:GetAttribute("Alborotador") == true
		if enfado then
			enfadados += 1
		end
		if n < P.MONITOR_FIGURAS then
			local cabeza = m:FindFirstChild("Cabeza")
			local piel = if cabeza and cabeza:IsA("BasePart") then cabeza.Color else Color3.fromRGB(255, 214, 170)
			n += 1
			persona(n, cuerpo.CFrame, if cabeza and cabeza:IsA("BasePart") then cabeza.CFrame else cuerpo.CFrame * CFrame.new(0, 1.85, 0), cuerpo.Color,
				if enfado then Gui.ROJO elseif atributo(m, "Miedo", 0) > 0.5 then AZUL else piel)
		end
	end
	for i = n + 1, #figuras do
		local f = figuras[i]
		if f.cuerpo.CFrame ~= OCULTO then
			f.cuerpo.CFrame = OCULTO
			f.cabeza.CFrame = OCULTO
		end
	end
	local e, fuegos, agujeros, animales = 0, 0, 0, 0
	local t = os.clock()
	for _, f in CollectionService:GetTagged("Fuego") do
		if f:IsA("BasePart") and dentro(f.Position) then
			fuegos += 1
			e += 1
			extra(e, CFrame.new(f.Position + Vector3.new(0, 1, 0)), Vector3.new(1.6, 2 + math.sin(t * 17 + e) * 0.5, 1.6), Color3.fromRGB(255, 140, 40), Enum.PartType.Ball, true)
		end
	end
	for _, b in CollectionService:GetTagged("Brecha") do
		if b:IsA("BasePart") and dentro(b.Position) then
			agujeros += 1
			e += 1
			extra(e, CFrame.new(b.Position), Vector3.new(2, 2, 2), Gui.TINTA, Enum.PartType.Ball, false)
		end
	end
	for _, c in CollectionService:GetTagged("Cocodrilo") do
		local cf = if c:IsA("Model") then c:GetPivot() elseif c:IsA("BasePart") then c.CFrame else nil
		if cf and dentro(cf.Position) then
			animales += 1
			e += 1
			extra(e, cf, Vector3.new(1.1, 0.8, 3.2), Gui.VERDE, Enum.PartType.Block, false)
		end
	end
	for _, a in CollectionService:GetTagged("Agarrable") do
		local tipo = a:GetAttribute("Tipo")
		if a:IsA("BasePart") and (tipo == "Cabra" or tipo == "Gallina") and dentro(a.Position) then
			animales += 1
			e += 1
			extra(e, a.CFrame, if tipo == "Cabra" then Vector3.new(1, 1.3, 1.9) else Vector3.new(0.9, 0.9, 0.9), BLANCO, Enum.PartType.Block, false)
		end
	end
	for i = e + 1, #extras do
		if extras[i].CFrame ~= OCULTO then
			extras[i].CFrame = OCULTO
		end
	end
	cuenta("Fuego", fuegos)
	cuenta("Peligro", agujeros)
	cuenta("Enfado", enfadados)
	cuenta("Cocodrilo", animales)
end

local function crearMonitor(parte: BasePart): SurfaceGui
	local s = superficie("Monitor", parte, Vector2.new(512, 288), 1.25)
	vista = Instance.new("ViewportFrame")
	vista.Size = UDim2.fromScale(1, 1)
	vista.BackgroundColor3 = Color3.fromRGB(18, 20, 26)
	vista.BorderSizePixel = 0
	vista.Ambient = Color3.fromRGB(190, 184, 172)
	vista.LightColor = Color3.fromRGB(255, 246, 232)
	vista.LightDirection = Vector3.new(-0.3, -1, -0.45)
	vista.Parent = s
	camaraMonitor = Instance.new("Camera")
	camaraMonitor.FieldOfView = 72
	camaraMonitor.CFrame = CAMARAS[1].cf
	camaraMonitor.Parent = vista
	vista.CurrentCamera = camaraMonitor
	for k = 0, 17 do
		local linea = Instance.new("Frame")
		linea.BackgroundColor3 = Color3.new(0, 0, 0)
		linea.BackgroundTransparency = 0.82
		linea.BorderSizePixel = 0
		linea.Size = UDim2.new(1, 0, 0, 3)
		linea.Position = UDim2.fromOffset(0, k * 16 + 6)
		linea.ZIndex = 2
		linea.Parent = s
	end
	rodillo = Instance.new("Frame")
	rodillo.BackgroundColor3 = BLANCO
	rodillo.BackgroundTransparency = 0.93
	rodillo.BorderSizePixel = 0
	rodillo.Size = UDim2.new(1, 0, 0, 40)
	rodillo.ZIndex = 2
	rodillo.Parent = s
	alerta = Instance.new("Frame")
	alerta.BackgroundColor3 = Gui.ROJO
	alerta.BackgroundTransparency = 1
	alerta.BorderSizePixel = 0
	alerta.Size = UDim2.fromScale(1, 1)
	alerta.ZIndex = 3
	alerta.Parent = s
	for _ = 1, 26 do
		local f = Instance.new("Frame")
		f.BorderSizePixel = 0
		f.Visible = false
		f.ZIndex = 4
		f.Parent = s
		table.insert(ruido, f)
	end
	etiquetaCam = Gui.texto(s, "", UDim2.fromOffset(150, 34), UDim2.fromOffset(14, 8), BLANCO, true)
	etiquetaCam.TextXAlignment = Enum.TextXAlignment.Left
	etiquetaCam.ZIndex = 5
	Gui.trazado(etiquetaCam)
	etiquetaZona = Gui.texto(s, CAMARAS[1].zona, UDim2.fromOffset(150, 24), UDim2.fromOffset(14, 40), BLANCO, false)
	etiquetaZona.TextXAlignment = Enum.TextXAlignment.Left
	etiquetaZona.ZIndex = 5
	Gui.trazado(etiquetaZona)
	rec = marco(s, UDim2.fromOffset(16, 16), UDim2.new(1, -78, 0, 25), Gui.ROJO, 0)
	rec.ZIndex = 5
	redondo(rec)
	local textoRec = Gui.texto(s, "REC", UDim2.fromOffset(56, 26), UDim2.new(1, -66, 0, 12), BLANCO, true)
	textoRec.TextXAlignment = Enum.TextXAlignment.Left
	textoRec.ZIndex = 5
	Gui.trazado(textoRec)
	for i, nombre in { "Fuego", "Peligro", "Enfado", "Cocodrilo" } do
		local x = 14 + (i - 1) * 92
		local icono = Gui.icono(s, nombre, UDim2.fromOffset(38, 38), UDim2.new(0, x, 1, -46))
		icono.ZIndex = 5
		local numero = Gui.texto(s, "0", UDim2.fromOffset(44, 34), UDim2.new(0, x + 42, 1, -44), BLANCO, true)
		numero.TextXAlignment = Enum.TextXAlignment.Left
		numero.ZIndex = 5
		Gui.trazado(numero)
		contadores[nombre] = { icono = icono, numero = numero, valor = -1 }
		cuenta(nombre, 0)
	end
	return s
end

local function animarMonitor()
	local t = os.clock()
	if t >= proximoCambio then
		proximoCambio = t + P.MONITOR_CAMBIO
		camaraIndice = camaraIndice % #CAMARAS + 1
		camaraMonitor.CFrame = CAMARAS[camaraIndice].cf
		etiquetaCam.Text = `CAM {camaraIndice}`
		etiquetaZona.Text = CAMARAS[camaraIndice].zona
		estaticaHasta = t + 0.35
	end
	local estatica = t < estaticaHasta
	for _, f in ruido do
		f.Visible = estatica
		if estatica then
			local g = rng:NextNumber(0.2, 0.9)
			f.BackgroundColor3 = Color3.new(g, g, g)
			f.BackgroundTransparency = rng:NextNumber(0, 0.4)
			f.Size = UDim2.fromOffset(rng:NextInteger(30, 220), rng:NextInteger(3, 14))
			f.Position = UDim2.fromOffset(rng:NextInteger(-40, 500), rng:NextInteger(0, 288))
		end
	end
	rec.Visible = t % 1.2 < 0.75
	rodillo.Position = UDim2.new(0, 0, (t * 0.18) % 1.2 - 0.15, 0)
	alerta.BackgroundTransparency = if avion:GetAttribute("Emergencia") == true then 0.78 + 0.12 * math.sin(t * 6) else 1
	local noche = Estado:GetAttribute("Fase") == "Vuelo" and Estado:GetAttribute("Condicion") == "Nocturno"
	vista.ImageColor3 = if noche then Color3.fromRGB(205, 190, 170) else BLANCO
end

function Pantallas.iniciar()
	local cabina = avion:WaitForChild("Cabina")
	local parteRadar = cabina:WaitForChild("PantallaRadar", 30)
	local parteMonitor = cabina:WaitForChild("PantallaMonitor", 30)
	if not parteRadar or not parteRadar:IsA("BasePart") or not parteMonitor or not parteMonitor:IsA("BasePart") then
		return
	end
	local radar = crearRadar(parteRadar)
	local monitor = crearMonitor(parteMonitor)
	avion:GetAttributeChangedSignal("Bandada"):Connect(function()
		bandadaHasta = os.clock() + 3
	end)
	local acumulado = 1
	RunService.RenderStepped:Connect(function(dt: number)
		local camara = Workspace.CurrentCamera.CFrame.Position
		local cercaRadar = (camara - parteRadar.Position).Magnitude < P.DISTANCIA
		local cercaMonitor = (camara - parteMonitor.Position).Magnitude < P.DISTANCIA
		if radar.Enabled ~= cercaRadar then
			radar.Enabled = cercaRadar
		end
		if monitor.Enabled ~= cercaMonitor then
			monitor.Enabled = cercaMonitor
		end
		if cercaMonitor and not construida then
			construida = true
			copiarCabina()
		end
		acumulado += dt
		if acumulado >= 1 / P.MONITOR_HZ then
			acumulado = 0
			if cercaRadar then
				pintarRadar(calcularRadar())
			end
			if cercaMonitor then
				actualizarMonitor()
			end
		end
		if cercaRadar then
			animarRadar(dt)
		end
		if cercaMonitor then
			animarMonitor()
		end
	end)
end

return Pantallas
