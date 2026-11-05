--!strict
local ContentProvider = game:GetService("ContentProvider")
local ContextActionService = game:GetService("ContextActionService")
local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local StarterGui = game:GetService("StarterGui")
local TeleportService = game:GetService("TeleportService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Audio = require(ReplicatedStorage.Shared.Audio)
local Gui = require(ReplicatedStorage.Shared.Gui)
local ImagenesIntro = require(ReplicatedStorage.Shared.ImagenesIntro)
local Visuales = require(ReplicatedStorage.Shared.Visuales)
local Camara = require(script.Parent.Camara)
local Rafagas = require(script.Parent.Rafagas)
local Sonido = require(script.Parent.Sonido)

type Toma = { duracion: number, desde: Vector3, control: Vector3, hasta: Vector3, mira0: Vector3, mira1: Vector3, fov0: number, fov1: number, giro0: number, giro1: number }
type Pila = { carpeta: Folder, cayendo: BasePart, base: CFrame }
type Logo = { marco: Frame, base: UDim2, over: ImageLabel, booked: ImageLabel, avioneta: ImageLabel, etiqueta: Frame, cinta: ImageLabel, gotas: ImageLabel, lema: TextLabel, inicio: number, fuera: boolean }

local Intro = {}

local jugador = Players.LocalPlayer
local Estado = ReplicatedStorage:WaitForChild("Estado")
local VISTA = "OverbookedIntroVista"
local BLOQUEO = "OverbookedIntroBloqueo"
local PASO = "OverbookedIntro"
local LEMA = "La peor aerolínea del mundo"
local BLOQUEADAS: { Enum.KeyCode | Enum.UserInputType } = { Enum.KeyCode.E, Enum.KeyCode.F, Enum.KeyCode.G, Enum.KeyCode.T, Enum.KeyCode.R, Enum.KeyCode.H, Enum.KeyCode.M, Enum.KeyCode.Q, Enum.KeyCode.Space, Enum.KeyCode.ButtonR2, Enum.KeyCode.ButtonL2, Enum.KeyCode.ButtonX, Enum.KeyCode.ButtonY, Enum.KeyCode.ButtonB, Enum.UserInputType.MouseButton1, Enum.UserInputType.MouseButton2 }
local NUCLEO = { Enum.CoreGuiType.PlayerList, Enum.CoreGuiType.Health, Enum.CoreGuiType.Backpack, Enum.CoreGuiType.Chat, Enum.CoreGuiType.EmotesMenu }
local CAIDA = 1.9
local ACOSTADA = CFrame.Angles(-math.pi / 2, 0, 0)

local gui: ScreenGui
local raiz: Frame
local conexiones: { RBXScriptConnection } = {}
local estado = "cargando"
local inicio = 0
local temblor = 0
local golpeFov = 0
local logo: Logo? = nil

local function sonar(nombre: string, alternativa: string, volumen: number?, tono: number?)
	Sonido.reproducir(if Audio.IDS[nombre] then nombre else alternativa, nil, volumen, tono or 1)
end

local function cargandoAun(): boolean
	return estado == "cargando"
end

local function suave(a: number): number
	return a * a * a * (a * (a * 6 - 15) + 10)
end

local function imagen(padre: Instance, nombre: string, tamano: UDim2, posicion: UDim2, ancla: Vector2?, z: number?): ImageLabel
	local i = Instance.new("ImageLabel")
	i.Name = nombre
	i.BackgroundTransparency = 1
	i.Image = `rbxassetid://{ImagenesIntro[nombre]}`
	i.Size = tamano
	i.Position = posicion
	i.AnchorPoint = ancla or Vector2.new(0.5, 0.5)
	i.ZIndex = z or 1
	i.Parent = padre
	return i
end

local function escalaDe(objeto: GuiObject): UIScale
	local e = objeto:FindFirstChildOfClass("UIScale")
	if e then
		return e
	end
	local nueva = Instance.new("UIScale")
	nueva.Parent = objeto
	return nueva
end

local function aparecer(objeto: GuiObject, retraso: number, sonido: string?)
	local e = escalaDe(objeto)
	e.Scale = 0
	objeto.Visible = false
	task.delay(retraso, function()
		objeto.Visible = true
		if sonido then
			sonar(sonido, "Pop", 0.8)
		end
		TweenService:Create(e, TweenInfo.new(0.4, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	end)
end

local function enLogo(x: number, y: number, w: number, h: number): (UDim2, UDim2)
	return UDim2.fromScale(w / 1024, h / 720), UDim2.fromScale(x / 1024, y / 720)
end

local function caer(i: ImageLabel, retraso: number, tono: number)
	local base, destino = i.Size, i.Position
	i.Visible = false
	task.delay(retraso, function()
		i.Visible = true
		i.Position = destino - UDim2.fromScale(0, 1.4)
		i.Size = UDim2.fromScale(base.X.Scale * 0.8, base.Y.Scale * 1.35)
		local t = TweenService:Create(i, TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Position = destino })
		t:Play()
		t.Completed:Wait()
		sonar("Bonk", "GolpeFuerte", 0.8, tono)
		temblor = math.min(1, temblor + 0.45)
		i.Size = UDim2.fromScale(base.X.Scale * 1.22, base.Y.Scale * 0.66)
		TweenService:Create(i, TweenInfo.new(0.6, Enum.EasingStyle.Elastic, Enum.EasingDirection.Out), { Size = base }):Play()
	end)
end

local function construirLogo(posicion: UDim2): Logo
	local marco = Instance.new("Frame")
	marco.Name = "Logo"
	marco.BackgroundTransparency = 1
	marco.AnchorPoint = Vector2.new(0.5, 0.5)
	marco.Size = UDim2.fromOffset(700, 492)
	marco.Position = posicion
	marco.ZIndex = 3
	marco.Parent = raiz
	local t, p = enLogo(512, 330, 1000, 1000)
	local gotas = imagen(marco, "Gotas", t, p, nil, 1)
	gotas.Visible = false
	t, p = enLogo(300, 430, 440, 440)
	local mancha2 = imagen(marco, "Mancha", t, p, nil, 2)
	mancha2.ImageColor3 = Gui.TURQUESA
	mancha2.Rotation = -25
	t, p = enLogo(540, 330, 640, 640)
	local mancha = imagen(marco, "Mancha", t, p, nil, 3)
	mancha.ImageColor3 = Gui.NARANJA
	mancha.Rotation = 10
	local etiqueta = Instance.new("Frame")
	etiqueta.BackgroundTransparency = 1
	t, p = enLogo(905, 512, 100, 400)
	etiqueta.Size = t
	etiqueta.Position = p
	etiqueta.AnchorPoint = Vector2.new(0.5, 0.5)
	etiqueta.ZIndex = 4
	etiqueta.Visible = false
	etiqueta.Parent = marco
	imagen(etiqueta, "Etiqueta", UDim2.fromScale(1, 0.5), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0), 4)
	t, p = enLogo(470, 340, 1024, 320)
	local over = imagen(marco, "LogoOver", t, p, Vector2.new(0.5, 1), 5)
	t, p = enLogo(512, 595, 1024, 320)
	local booked = imagen(marco, "LogoBooked", t, p, Vector2.new(0.5, 1), 6)
	t, p = enLogo(860, 92, 300, 150)
	local avioneta = imagen(marco, "Avioneta", t, p, nil, 7)
	avioneta.Visible = false
	t, p = enLogo(512, 650, 800, 150)
	local cinta = imagen(marco, "Cinta", t, p, nil, 8)
	cinta.ImageColor3 = Gui.ROJO
	local lema = Gui.texto(cinta, LEMA, UDim2.fromScale(0.72, 0.42), UDim2.fromScale(0.14, 0.2), Gui.PAPEL, true)
	lema.ZIndex = 9
	lema.MaxVisibleGraphemes = 0
	Gui.trazado(lema)
	for _, i in { mancha, mancha2, over, booked, cinta } do
		i.Visible = false
	end
	return { marco = marco, base = posicion, over = over, booked = booked, avioneta = avioneta, etiqueta = etiqueta, cinta = cinta, gotas = gotas, lema = lema, inicio = math.huge, fuera = false }
end

local function golpear(l: Logo)
	l.inicio = os.clock()
	sonar("BoomCartoon", "Explosion", 0.9)
	temblor = math.min(1, temblor + 0.6)
	golpeFov = -7
	for _, hijo in l.marco:GetChildren() do
		if hijo.Name == "Mancha" and hijo:IsA("GuiObject") then
			aparecer(hijo, if hijo.ZIndex == 2 then 0.08 else 0)
		end
	end
	caer(l.over, 0.05, 1.1)
	caer(l.booked, 0.3, 0.9)
	aparecer(l.cinta, 1.0, "Sello")
	task.delay(0.55, function()
		sonar("Lanzar", "Lanzar", 1.2, 0.8)
	end)
	task.delay(0.8, function()
		sonar("Pop", "UiClick", 0.8, 1.2)
	end)
end

local function animarLogo(l: Logo, ahora: number)
	local t = ahora - l.inicio
	if t < 0 or l.fuera then
		return
	end
	local sacudida = temblor * temblor * 14
	l.marco.Position = l.base + UDim2.fromOffset(math.noise(ahora * 30, 7) * sacudida, math.noise(ahora * 30, 9) * sacudida)
	l.gotas.Visible = t < 0.75
	local g = math.clamp(t / 0.45, 0, 1)
	local escala = 0.55 + 0.6 * (1 - (1 - g) * (1 - g))
	l.gotas.Size = UDim2.fromScale(escala * 1000 / 1024, escala * 1000 / 720)
	l.gotas.ImageTransparency = math.clamp((t - 0.15) / 0.55, 0, 1)
	local tv = t - 0.55
	l.avioneta.Visible = tv >= 0
	if tv >= 0 then
		local e = 1 - (1 - math.clamp(tv / 0.75, 0, 1)) ^ 3
		local _, destino = enLogo(860, 92, 300, 150)
		local desde = UDim2.fromScale(-0.45, 0.55)
		l.avioneta.Position = desde:Lerp(destino, e) + UDim2.fromScale(0, 0.012 * math.sin(ahora * 2.3))
		l.avioneta.Rotation = -28 * (1 - e) + 3 * math.sin(ahora * 1.7)
	end
	local te = t - 0.8
	l.etiqueta.Visible = te >= 0
	if te >= 0 then
		l.etiqueta.Rotation = 70 * math.cos(te * 5.5) * math.exp(-1.5 * te) + 4 * math.sin(ahora * 1.3)
	end
	if t > 1 then
		l.over.Rotation = 1.3 * math.sin(ahora * 1.4)
		l.booked.Rotation = -1.1 * math.sin(ahora * 1.4 + 1)
	end
	local largo = utf8.len(l.lema.Text) or #l.lema.Text
	l.lema.MaxVisibleGraphemes = math.floor(math.clamp((t - 1.15) / 0.7, 0, 1) * largo)
end

local function telon(): (Frame, Frame)
	local function mitad(arriba: boolean): Frame
		local f = Instance.new("Frame")
		f.Name = "Telon"
		f.BackgroundColor3 = Gui.PAPEL
		f.BorderSizePixel = 0
		f.Size = UDim2.fromScale(1, 0.5)
		f.Position = UDim2.fromScale(0, if arriba then 0 else 0.5)
		f.ZIndex = 10
		local textura = Instance.new("ImageLabel")
		textura.BackgroundTransparency = 1
		textura.Image = `rbxassetid://{ImagenesIntro.Papel}`
		textura.ScaleType = Enum.ScaleType.Tile
		textura.TileSize = UDim2.fromOffset(512, 512)
		textura.Size = UDim2.fromScale(1, 1)
		textura.Parent = f
		local borde = imagen(f, "Rasgado", UDim2.new(1, 40, 0, 110), UDim2.fromScale(0.5, if arriba then 1 else 0))
		borde.Rotation = if arriba then 0 else 180
		f.Parent = raiz
		return f
	end
	return mitad(true), mitad(false)
end

local function abrirTelon(arriba: Frame, abajo: Frame)
	sonar("RasgarPapel", "Lanzar", 1.1, 1)
	local info = TweenInfo.new(0.65, Enum.EasingStyle.Back, Enum.EasingDirection.In)
	TweenService:Create(arriba, info, { Position = UDim2.fromScale(0, -0.62), Rotation = -1.5 }):Play()
	TweenService:Create(abajo, info, { Position = UDim2.fromScale(0, 1.12), Rotation = 1.5 }):Play()
	task.delay(0.8, function()
		arriba:Destroy()
		abajo:Destroy()
	end)
end

local function barra(arriba: boolean): Frame
	local f = Instance.new("Frame")
	f.BackgroundColor3 = Gui.TINTA
	f.BorderSizePixel = 0
	f.Size = UDim2.fromScale(1, 0.08)
	f.AnchorPoint = Vector2.new(0, if arriba then 1 else 0)
	f.Position = UDim2.fromScale(0, if arriba then 0 else 1)
	f.ZIndex = 2
	local borde = imagen(f, "Rasgado", UDim2.new(1, 40, 0, 70), UDim2.fromScale(0.5, if arriba then 1 else 0))
	borde.Rotation = if arriba then 0 else 180
	borde.ImageColor3 = Gui.TINTA
	f.Parent = raiz
	return f
end

local function moverBarras(barras: { Frame }, dentro: boolean)
	local info = TweenInfo.new(0.45, Enum.EasingStyle.Quad, if dentro then Enum.EasingDirection.Out else Enum.EasingDirection.In)
	TweenService:Create(barras[1], info, { Position = UDim2.fromScale(0, if dentro then 0.08 else 0) }):Play()
	TweenService:Create(barras[2], info, { Position = UDim2.fromScale(0, if dentro then 0.92 else 1) }):Play()
end

local function boton(contenido: string, tamano: UDim2, posicion: UDim2, color: Color3, letra: Color3, accion: () -> ()): ImageButton
	local b = Gui.panel(raiz, "Boton", tamano, posicion, Vector2.new(0.5, 0.5), true) :: any
	b.ImageColor3 = color
	b.ZIndex = 4
	local t = Gui.texto(b, contenido, UDim2.new(1, -66, 1, -22), UDim2.fromOffset(16, 9), letra, true)
	if letra == Gui.PAPEL then
		Gui.trazado(t)
	end
	Gui.icono(b, "Flecha", UDim2.new(0, 40, 0.62, 0), UDim2.new(1, -14, 0.5, 0), Vector2.new(1, 0.5))
	local e = escalaDe(b)
	b.MouseEnter:Connect(function()
		TweenService:Create(e, TweenInfo.new(0.18, Enum.EasingStyle.Back), { Scale = 1.08 }):Play()
		b.Rotation = -2
	end)
	b.MouseLeave:Connect(function()
		TweenService:Create(e, TweenInfo.new(0.18, Enum.EasingStyle.Quad), { Scale = 1 }):Play()
		b.Rotation = 0
	end)
	b.Activated:Connect(function()
		Sonido.reproducir("UiClick", nil, 0.7, 1)
		accion()
	end)
	return b
end

local function crearGui()
	gui = Instance.new("ScreenGui")
	gui.Name = "Intro"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 25
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	raiz = Instance.new("Frame")
	raiz.BackgroundTransparency = 1
	raiz.Parent = gui
	local escala = Instance.new("UIScale")
	escala.Parent = raiz
	local function ajustar()
		local v = Workspace.CurrentCamera.ViewportSize
		local s = math.clamp(math.min(v.X / 1366, v.Y / 768), 0.45, 1.4)
		escala.Scale = s
		raiz.Size = UDim2.fromScale(1 / s, 1 / s)
	end
	ajustar()
	table.insert(conexiones, Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(ajustar))
	gui.Parent = jugador:WaitForChild("PlayerGui")
end

local function precargar(limite: number)
	local lista = {}
	for _, id in ImagenesIntro do
		table.insert(lista, `rbxassetid://{id}`)
	end
	local listo = false
	task.spawn(function()
		pcall(function()
			ContentProvider:PreloadAsync(lista)
		end)
		listo = true
	end)
	local fin = os.clock() + limite
	while not listo and os.clock() < fin do
		task.wait()
	end
end

local function limpiar()
	for _, c in conexiones do
		c:Disconnect()
	end
	table.clear(conexiones)
	RunService:UnbindFromRenderStep(PASO)
	gui:Destroy()
end

local function lugar(raizBusqueda: Instance?, nombre: string, defecto: Vector3): Vector3
	local p = raizBusqueda and raizBusqueda:FindFirstChild(nombre, true)
	return if p and p:IsA("BasePart") then p.Position else defecto
end

local function tomas(c: Vector3, k: Vector3): { Toma }
	local function toma(duracion: number, desde: Vector3, control: Vector3, hasta: Vector3, mira0: Vector3, mira1: Vector3, fov0: number, fov1: number, giro0: number, giro1: number): Toma
		return { duracion = duracion, desde = desde, control = control, hasta = hasta, mira0 = mira0, mira1 = mira1, fov0 = fov0, fov1 = fov1, giro0 = giro0, giro1 = giro1 }
	end
	return {
		toma(4.2, c + Vector3.new(-150, 75, -200), c + Vector3.new(-125, 25, -105), c + Vector3.new(-66, 6, -92), c + Vector3.new(10, -8, 10), c + Vector3.new(0, -2, -22), 48, 40, -7, 0),
		toma(3.6, c + Vector3.new(-58, -10, -62), c + Vector3.new(-64, -12, -8), c + Vector3.new(-50, -8, 42), c + Vector3.new(0, -4, -38), c + Vector3.new(2, 0, 22), 62, 56, 5, -3),
		toma(3.8, k + Vector3.new(-9.5, 3, -11.5), k + Vector3.new(-8.5, 2.6, -10), k + Vector3.new(-7.5, 2.3, -8.5), k + Vector3.new(0, 1.6, -1.5), k + Vector3.new(0, 1.2, -2.2), 50, 42, 0, 2),
		toma(4.5, c + Vector3.new(-62, -5, -84), c + Vector3.new(-58, 2, -94), c + Vector3.new(-48, 12, -100), c + Vector3.new(25, 8, -26), c + Vector3.new(31, 8, -22), 56, 50, 3, 0),
	}
end

local function encuadre(lista: { Toma }, t: number, centro: Vector3): (CFrame, number)
	local acumulado = 0
	for i, toma in lista do
		if t < acumulado + toma.duracion or i == #lista then
			local a = math.clamp((t - acumulado) / toma.duracion, 0, 1)
			local e = suave(a)
			local u = 1 - e
			local p = toma.desde * u * u + toma.control * 2 * u * e + toma.hasta * e * e
			local m = toma.mira0:Lerp(toma.mira1, e)
			local extra = t - acumulado - toma.duracion
			if i == #lista and extra > 0 then
				local orbita = CFrame.Angles(0, -0.05 * extra * extra / (extra + 3), 0)
				p = centro + orbita:VectorToWorldSpace(p - centro)
				m = centro + orbita:VectorToWorldSpace(m - centro)
			end
			local mano = CFrame.Angles(math.noise(t * 0.7, 3) * 0.008, math.noise(t * 0.7, 5) * 0.008, 0)
			return CFrame.lookAt(p, m) * mano * CFrame.Angles(0, 0, math.rad(toma.giro0 + (toma.giro1 - toma.giro0) * e)), toma.fov0 + (toma.fov1 - toma.fov0) * e
		end
		acumulado += toma.duracion
	end
	return CFrame.identity, 70
end

local function maleta(padre: Instance, nombre: string, color: Color3, cf: CFrame): BasePart
	local caja = Visuales.CAJAS[nombre]
	local cuerpo = Instance.new("Part")
	cuerpo.Size = if caja then caja.maximo - caja.minimo else Vector3.new(1.6, 1.2, 0.7)
	cuerpo.Color = color
	cuerpo.Material = Enum.Material.SmoothPlastic
	cuerpo.CFrame = cf
	cuerpo.Anchored = true
	cuerpo.CanQuery = false
	cuerpo.CanTouch = false
	cuerpo.CustomPhysicalProperties = PhysicalProperties.new(0.6, 0.5, 0.3)
	local modelos = ReplicatedStorage:FindFirstChild("ModelosIntro")
	local plantilla = modelos and modelos:FindFirstChild(nombre)
	local visual: Model
	if plantilla and plantilla:IsA("Model") then
		visual = plantilla:Clone()
		visual:PivotTo(cf * CFrame.new(0, -cuerpo.Size.Y / 2, 0) * visual:GetPivot())
		cuerpo.Transparency = 1
	else
		visual = Instance.new("Model")
		for _, d in { { Vector3.new(0.16, 1.24, 0.74), Vector3.new(-0.45, 0, 0) }, { Vector3.new(0.16, 1.24, 0.74), Vector3.new(0.45, 0, 0) }, { Vector3.new(0.6, 0.16, 0.14), Vector3.new(0, 0.68, 0) } } do
			local p = Instance.new("Part")
			p.Size = d[1]
			p.Color = Gui.TINTA
			p.Material = Enum.Material.SmoothPlastic
			p.CFrame = cf * CFrame.new(d[2])
			p.Parent = visual
		end
	end
	for _, d in visual:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = false
			d.CanCollide = false
			d.CanQuery = false
			d.CanTouch = false
			d.Massless = true
			local w = Instance.new("WeldConstraint")
			w.Part0 = cuerpo
			w.Part1 = d
			w.Parent = d
		end
	end
	visual.Parent = cuerpo
	cuerpo.Parent = padre
	return cuerpo
end

local function pila(k: Vector3): Pila
	local carpeta = Instance.new("Folder")
	carpeta.Name = "IntroMaletas"
	local suelo = k.Y + 0.65
	local z = k.Z - 1.6
	maleta(carpeta, "Maleta1", Gui.NARANJA, CFrame.new(k.X - 0.85, suelo + 0.35, z) * CFrame.Angles(0, 0.08, 0) * ACOSTADA)
	maleta(carpeta, "Maleta3", Gui.TURQUESA, CFrame.new(k.X + 0.85, suelo + 0.35, z + 0.1) * CFrame.Angles(0, -0.05, 0) * ACOSTADA)
	maleta(carpeta, "Maleta2", Gui.AMARILLO, CFrame.new(k.X, suelo + 1.05, z) * CFrame.Angles(0, 0.12, 0) * ACOSTADA)
	maleta(carpeta, "Bolso", Gui.ROJO, CFrame.new(k.X + 1.25, suelo + 1.2, z + 0.1) * CFrame.Angles(0, math.pi / 2 - 0.15, 0))
	local base = CFrame.new(k.X - 0.2, suelo + 1.75, z - 0.45) * CFrame.Angles(0, -0.1, 0)
	local cayendo = maleta(carpeta, "Maleta1", Gui.ROJO, base * ACOSTADA)
	carpeta.Parent = Workspace
	return { carpeta = carpeta, cayendo = cayendo, base = base }
end

local function controles(): any
	local m = jugador:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule", 5)
	if m and m:IsA("ModuleScript") then
		local ok, r = pcall(require, m)
		if ok and r then
			return (r :: any):GetControls()
		end
	end
	return nil
end

local function personajeListo(): (Model?, BasePart?)
	local personaje = jugador.Character
	local r = personaje and personaje:FindFirstChild("HumanoidRootPart")
	return personaje, if r and r:IsA("BasePart") then r else nil
end

local function destino(): CFrame?
	local _, r = personajeListo()
	if not r then
		return nil
	end
	local ojo = r.CFrame:PointToWorldSpace(Vector3.new(0, 1.5, 0))
	local frente = (r.CFrame.LookVector * Vector3.new(1, 0, 1)).Unit
	if Camara.esTerceraPersona() then
		local dir = (frente - Vector3.new(0, 0.3, 0)).Unit
		return CFrame.lookAt(ojo - dir * 10.5, ojo)
	end
	return CFrame.lookAt(ojo, ojo + frente)
end

local function tarjeta()
	crearGui()
	local arriba, abajo = telon()
	local catcher = Instance.new("TextButton")
	catcher.BackgroundTransparency = 1
	catcher.Text = ""
	catcher.Size = UDim2.fromScale(1, 1)
	catcher.ZIndex = 12
	catcher.Parent = raiz
	local l = construirLogo(UDim2.fromScale(0.5, 0.45))
	l.marco.ZIndex = 11
	logo = l
	local listo = false
	local function seguir()
		listo = listo or os.clock() - l.inicio > 0.4
	end
	catcher.Activated:Connect(seguir)
	table.insert(conexiones, UserInputService.InputBegan:Connect(function(entrada)
		if entrada.UserInputType == Enum.UserInputType.Keyboard or string.find(entrada.UserInputType.Name, "Gamepad") ~= nil then
			seguir()
		end
	end))
	table.insert(conexiones, RunService.RenderStepped:Connect(function(dt: number)
		temblor = math.max(0, temblor - dt * 1.6)
		animarLogo(l, os.clock())
	end))
	precargar(3)
	golpear(l)
	local fin = os.clock() + 2.6
	while not listo and os.clock() < fin do
		task.wait()
	end
	catcher:Destroy()
	l.fuera = true
	TweenService:Create(l.marco, TweenInfo.new(0.45, Enum.EasingStyle.Back, Enum.EasingDirection.In), { Position = l.base - UDim2.fromScale(0, 1) }):Play()
	abrirTelon(arriba, abajo)
	task.wait(0.9)
	limpiar()
end

local function completa()
	pcall(function()
		TeleportService:SetTeleportSetting(VISTA, true)
	end)
	crearGui()
	local barras = { barra(true), barra(false) }
	local arriba, abajo = telon()
	local cargando = Gui.icono(raiz, "Avion", UDim2.fromOffset(96, 96), UDim2.fromScale(0.5, 0.47), Vector2.new(0.5, 0.5))
	cargando.ZIndex = 11
	local textoCarga = Gui.texto(raiz, "Embarcando...", UDim2.fromOffset(320, 40), UDim2.new(0.5, 0, 0.47, 60), Gui.TINTA, false, 30)
	textoCarga.AnchorPoint = Vector2.new(0.5, 0)
	textoCarga.ZIndex = 11
	local playerGui = jugador:WaitForChild("PlayerGui")
	local ocultos: { [ScreenGui]: boolean } = {}
	local function ocultar(g: Instance)
		if g:IsA("ScreenGui") and g ~= gui and g.Name ~= "Ajustes" and g.Enabled then
			ocultos[g] = true
			g.Enabled = false
		end
	end
	for _, g in playerGui:GetChildren() do
		ocultar(g)
	end
	local vigilancia = playerGui.ChildAdded:Connect(ocultar)
	local nucleo: { [Enum.CoreGuiType]: boolean } = {}
	for _, tipo in NUCLEO do
		nucleo[tipo] = StarterGui:GetCoreGuiEnabled(tipo)
		StarterGui:SetCoreGuiEnabled(tipo, false)
	end
	local avisos = ProximityPromptService.Enabled
	ProximityPromptService.Enabled = false
	ContextActionService:BindActionAtPriority(BLOQUEO, function()
		return Enum.ContextActionResult.Sink
	end, false, Enum.ContextActionPriority.High.Value + 50, table.unpack(BLOQUEADAS))
	local mando = controles()
	if mando then
		mando:Disable()
	end

	local avion = Workspace:FindFirstChild("Avion")
	local aeropuerto = Workspace:FindFirstChild("Aeropuerto")
	local c = lugar(avion, "Centro", Vector3.new(0, 105, -18))
	local k = lugar(aeropuerto, "CarroEquipaje", Vector3.new(36, 91.04, 34))
	local lista = tomas(c, k)
	local inicioGag = lista[1].duracion + lista[2].duracion
	local finVuelo = inicioGag + lista[3].duracion
	local montada: Pila? = nil
	local silbato, soltada, golpeada = false, false, false
	local velocidadAntes = 0

	local catcher = Instance.new("TextButton")
	catcher.BackgroundTransparency = 1
	catcher.Text = ""
	catcher.Size = UDim2.fromScale(1, 1)
	catcher.Modal = true
	catcher.Parent = raiz
	local saltarBoton: ImageButton
	local jugarBoton: ImageButton? = nil
	local ajustesBoton: ImageButton? = nil
	local salida: { desde: CFrame, hasta: CFrame?, fov: number, t: number }? = nil

	local function entregar()
		estado = "fin"
		RunService:UnbindFromRenderStep(PASO)
		vigilancia:Disconnect()
		if montada then
			montada.carpeta:Destroy()
		end
		local cam = Workspace.CurrentCamera
		local s = salida
		if s and s.hasta then
			cam.CFrame = s.hasta
		end
		cam.CameraType = Enum.CameraType.Custom
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		if humanoide then
			cam.CameraSubject = humanoide
		end
		for g in ocultos do
			g.Enabled = true
		end
		for tipo, valor in nucleo do
			StarterGui:SetCoreGuiEnabled(tipo, valor)
		end
		ProximityPromptService.Enabled = avisos
		ContextActionService:UnbindAction(BLOQUEO)
		if mando then
			mando:Enable()
		end
		GuiService.SelectedObject = nil
	end

	local function jugar()
		if estado ~= "titulo" then
			return
		end
		estado = "saliendo"
		local cam = Workspace.CurrentCamera
		salida = { desde = cam.CFrame, hasta = destino(), fov = cam.FieldOfView, t = os.clock() }
		sonar("Bocina", "Lanzar", 0.7, 1)
		sonar("Lanzar", "Lanzar", 1.2, 0.7)
		GuiService.SelectedObject = nil
		local l = logo
		if l then
			l.fuera = true
			TweenService:Create(l.marco, TweenInfo.new(0.5, Enum.EasingStyle.Back, Enum.EasingDirection.In), { Position = l.base - UDim2.fromScale(0, 1) }):Play()
		end
		for _, b in { jugarBoton, ajustesBoton } do
			if b then
				TweenService:Create(escalaDe(b), TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.In), { Scale = 0 }):Play()
			end
		end
		moverBarras(barras, false)
		task.delay(0.3, function()
			local arriba, abajo = telon()
			arriba.Position = UDim2.fromScale(0, -0.62)
			abajo.Position = UDim2.fromScale(0, 1.12)
			local info = TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
			TweenService:Create(arriba, info, { Position = UDim2.fromScale(0, 0) }):Play()
			TweenService:Create(abajo, info, { Position = UDim2.fromScale(0, 0.5) }):Play()
			task.wait(0.4)
			sonar("Bonk", "Golpe", 0.5, 1.4)
			entregar()
			task.wait(0.25)
			abrirTelon(arriba, abajo)
			task.wait(0.8)
			limpiar()
		end)
	end

	local function titulo()
		estado = "titulo"
		TweenService:Create(escalaDe(saltarBoton), TweenInfo.new(0.2, Enum.EasingStyle.Back, Enum.EasingDirection.In), { Scale = 0 }):Play()
		local l = construirLogo(UDim2.fromScale(0.3, 0.4))
		logo = l
		golpear(l)
		local modulo = script.Parent:FindFirstChild("Ajustes")
		local x = if modulo then -125 else 0
		local j = boton("JUGAR", UDim2.fromOffset(280, 88), UDim2.new(0.3, x, 1, -150), Gui.NARANJA, Gui.PAPEL, jugar)
		jugarBoton = j
		aparecer(j, 1.5, "Pop")
		if modulo and modulo:IsA("ModuleScript") then
			local a = boton("AJUSTES", UDim2.fromOffset(220, 70), UDim2.new(0.3, 150, 1, -150), Gui.TURQUESA, Gui.PAPEL, function()
				pcall(function()
					(require(modulo) :: any).abrir()
				end)
			end)
			ajustesBoton = a
			aparecer(a, 1.62, "Pop")
		end
		task.delay(1.6, function()
			if estado == "titulo" and UserInputService.GamepadEnabled then
				GuiService.SelectedObject = j
			end
		end)
	end

	local function saltar()
		if estado ~= "vuelo" then
			return
		end
		inicio = os.clock() - finVuelo
		sonar("Lanzar", "Lanzar", 1.2, 0.6)
	end

	saltarBoton = boton("Saltar", UDim2.fromOffset(170, 60), UDim2.new(1, -110, 1, -50), Gui.PAPEL, Gui.TINTA, saltar)
	saltarBoton.Visible = false
	catcher.Activated:Connect(saltar)
	table.insert(conexiones, UserInputService.InputBegan:Connect(function(entrada)
		if UserInputService:GetFocusedTextBox() then
			return
		end
		local tipo = entrada.UserInputType
		local tecla = tipo == Enum.UserInputType.Keyboard or string.find(tipo.Name, "Gamepad") ~= nil
		if estado == "vuelo" and tecla and entrada.KeyCode ~= Enum.KeyCode.Escape then
			saltar()
		elseif estado == "titulo" and (entrada.KeyCode == Enum.KeyCode.Return or entrada.KeyCode == Enum.KeyCode.Space or entrada.KeyCode == Enum.KeyCode.ButtonStart) then
			jugar()
		end
	end))

	local function abortar()
		if estado == "saliendo" or estado == "fin" then
			return
		end
		entregar()
		limpiar()
		task.spawn(tarjeta)
	end
	table.insert(conexiones, Estado:GetAttributeChangedSignal("Fase"):Connect(function()
		if Estado:GetAttribute("Fase") ~= "Aeropuerto" then
			abortar()
		end
	end))
	if Estado:GetAttribute("Fase") ~= "Aeropuerto" then
		abortar()
		return
	end

	RunService:BindToRenderStep(PASO, Enum.RenderPriority.Camera.Value + 2, function(dt: number)
		local cam = Workspace.CurrentCamera
		if cam.CameraType ~= Enum.CameraType.Scriptable then
			cam.CameraType = Enum.CameraType.Scriptable
		end
		local ahora = os.clock()
		local cf: CFrame
		local fov: number
		local s = salida
		if estado == "saliendo" and s then
			local e = suave(math.clamp((ahora - s.t) / 1.6, 0, 1))
			local hasta = s.hasta or s.desde
			local medio = s.desde.Position:Lerp(hasta.Position, 0.5) + Vector3.new(0, (s.desde.Position - hasta.Position).Magnitude * 0.18, 0)
			local u = 1 - e
			local p = s.desde.Position * u * u + medio * 2 * u * e + hasta.Position * e * e
			cf = CFrame.new(p) * s.desde.Rotation:Lerp(hasta.Rotation, e)
			fov = s.fov + (cam.FieldOfView - s.fov) * e
		else
			local t = if estado == "cargando" then 0 else ahora - inicio
			cf, fov = encuadre(lista, t, c)
			local tg = t - inicioGag
			if estado == "vuelo" and tg >= 0 and tg < lista[3].duracion then
				local m = montada or pila(k)
				montada = m
				local cayendo, baseMaleta = m.cayendo, m.base
				if tg >= 0.3 and not silbato then
					silbato = true
					sonar("SilbatoCaida", "Lanzar", 0.9, 1)
				end
				if not soltada then
					local amplitud = math.clamp((tg - 0.3) / (CAIDA - 0.3), 0, 1)
					local angulo = math.rad(4 + 22 * amplitud) * (0.5 - 0.5 * math.cos(tg * 13)) * math.min(1, tg / 0.3)
					cayendo.CFrame = baseMaleta * CFrame.new(0, -0.35, -0.15) * CFrame.Angles(-angulo, 0, 0) * CFrame.new(0, 0.35, 0.15) * ACOSTADA
					if tg >= CAIDA then
						soltada = true
						cayendo.Anchored = false
						cayendo.AssemblyLinearVelocity = baseMaleta.LookVector * 5 + Vector3.new(0, 3, 0)
						cayendo.AssemblyAngularVelocity = baseMaleta.RightVector * -7
						local adjunto = Instance.new("Attachment")
						adjunto.Parent = cayendo
						local fuerza = Instance.new("VectorForce")
						fuerza.Attachment0 = adjunto
						fuerza.RelativeTo = Enum.ActuatorRelativeTo.World
						fuerza.Force = Vector3.new(0, cayendo.AssemblyMass * Workspace.Gravity * 0.5, 0)
						fuerza.Parent = cayendo
					end
				elseif not golpeada then
					local vy = cayendo.AssemblyLinearVelocity.Y
					if velocidadAntes < -5 and vy > velocidadAntes + 4 then
						golpeada = true
						sonar("Bonk", "Golpe", 1, 1)
						Rafagas.lanzar("Polvo", cayendo.Position, 0.8)
						Rafagas.lanzar("Estrellas", cayendo.Position + Vector3.new(0, 1.2, 0), 0.6)
						temblor = math.min(1, temblor + 0.55)
						golpeFov = -6
						task.delay(0.5, function()
							sonar("Mareo", "PasajeroQueja", 0.7, 1)
						end)
					end
					velocidadAntes = vy
				end
			end
			if estado == "vuelo" and t >= finVuelo + 0.35 then
				titulo()
			end
		end
		temblor = math.max(0, temblor - dt * 1.6)
		golpeFov *= math.exp(-dt * 6)
		local fuerzaTemblor = temblor * temblor
		local sacudida = CFrame.Angles(math.noise(ahora * 9, 1) * 0.05 * fuerzaTemblor, math.noise(ahora * 9, 2) * 0.05 * fuerzaTemblor, math.noise(ahora * 9, 3) * 0.06 * fuerzaTemblor)
		cam.CFrame = cf * sacudida
		cam.FieldOfView = fov + golpeFov
	end)
	table.insert(conexiones, RunService.RenderStepped:Connect(function()
		local l = logo
		if l then
			animarLogo(l, os.clock())
		end
		cargando.Rotation = 8 * math.sin(os.clock() * 5)
	end))

	precargar(5)
	if not cargandoAun() then
		return
	end
	sonar("Ding", "UiAviso", 2.5, 1)
	TweenService:Create(cargando, TweenInfo.new(0.2), { ImageTransparency = 1 }):Play()
	TweenService:Create(textoCarga, TweenInfo.new(0.2), { TextTransparency = 1 }):Play()
	task.wait(0.25)
	if not cargandoAun() then
		return
	end
	inicio = os.clock()
	estado = "vuelo"
	abrirTelon(arriba, abajo)
	moverBarras(barras, true)
	task.delay(0.6, function()
		if estado == "vuelo" then
			aparecer(saltarBoton, 0)
		end
	end)
end

function Intro.iniciar()
	task.spawn(function()
		if not game:IsLoaded() then
			game.Loaded:Wait()
		end
		local limite = os.clock() + 3
		while Estado:GetAttribute("Fase") == nil and os.clock() < limite do
			task.wait(0.1)
		end
		local ok, vista = pcall(function()
			return TeleportService:GetTeleportSetting(VISTA)
		end)
		local lobby = Estado:GetAttribute("Fase") == "Aeropuerto" and Workspace:FindFirstChild("Aeropuerto") ~= nil and Workspace:GetAttribute("PruebaIsla") ~= true
		if lobby and not (ok and vista == true) then
			completa()
		else
			tarjeta()
		end
	end)
end

return Intro
