--!strict
local ContextActionService = game:GetService("ContextActionService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Gui = require(ReplicatedStorage.Shared.Gui)
local Camara = require(script.Parent.Camara)
local Sonido = require(script.Parent.Sonido)

local RemotoAjustes = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Ajustes") :: RemoteEvent

type Valores = { Fov: number, Musica: number, Efectos: number, Tercera: boolean, Idioma: string }
type Deslizador = { relleno: ImageLabel, pomo: ImageLabel, valor: TextLabel, fijar: (number) -> () }

local Ajustes = {}

local jugador = Players.LocalPlayer
local valores: Valores = { Fov = 80, Musica = 1, Efectos = 1, Tercera = false, Idioma = "en" }
local cargados = false
local envioPendiente = 0
local gui: ScreenGui
local raiz: Frame
local escala: UIScale
local panel: ImageLabel
local aparicion: UIScale
local deslizadores: { [string]: Deslizador } = {}
local textoCamara: TextLabel
local textoIdioma: TextLabel
local abierto = false
local idioma: any = nil

local IDIOMAS_BASE = { { codigo = "en", nombre = "English" }, { codigo = "es", nombre = "Español" } }

local function modulo(): any
	if idioma == nil then
		local m = script.Parent:FindFirstChild("Idioma")
		if m and m:IsA("ModuleScript") then
			local ok, r = pcall(require, m)
			idioma = if ok then r else false
		else
			idioma = false
		end
	end
	return if idioma then idioma else nil
end

local function idiomas(): { { codigo: string, nombre: string } }
	local m = modulo()
	if m and typeof(m.IDIOMAS) == "table" then
		return m.IDIOMAS
	end
	return IDIOMAS_BASE
end

local function nombreIdioma(codigo: string): string
	for _, i in idiomas() do
		if i.codigo == codigo then
			return i.nombre
		end
	end
	return codigo
end

local function aplicar()
	Camara.fov(valores.Fov)
	Sonido.volumen("Musica", valores.Musica)
	Sonido.volumen("Efectos", valores.Efectos)
	Sonido.volumen("Ambiente", valores.Efectos)
	Camara.preferirTercera(valores.Tercera)
	local m = modulo()
	if m and typeof(m.cambiar) == "function" then
		pcall(m.cambiar, valores.Idioma)
	end
	if textoCamara then
		textoCamara.Text = if valores.Tercera then "Tercera persona" else "Primera persona"
		textoIdioma.Text = nombreIdioma(valores.Idioma)
		deslizadores.Fov.fijar((valores.Fov - 60) / 40)
		deslizadores.Musica.fijar(valores.Musica)
		deslizadores.Efectos.fijar(valores.Efectos)
	end
end

local function guardar()
	envioPendiente += 1
	local mio = envioPendiente
	task.delay(0.8, function()
		if mio == envioPendiente then
			RemotoAjustes:FireServer(valores)
		end
	end)
end

local function leerGuardados()
	if cargados then
		return
	end
	local crudo = jugador:GetAttribute("Ajustes")
	if typeof(crudo) ~= "string" then
		return
	end
	cargados = true
	local ok, t = pcall(HttpService.JSONDecode, HttpService, crudo)
	if not ok or typeof(t) ~= "table" then
		aplicar()
		return
	end
	if typeof(t.Fov) == "number" then
		valores.Fov = math.clamp(t.Fov, 60, 100)
	end
	if typeof(t.Musica) == "number" then
		valores.Musica = math.clamp(t.Musica, 0, 1)
	end
	if typeof(t.Efectos) == "number" then
		valores.Efectos = math.clamp(t.Efectos, 0, 1)
	end
	if typeof(t.Tercera) == "boolean" then
		valores.Tercera = t.Tercera
	end
	if typeof(t.Idioma) == "string" then
		valores.Idioma = t.Idioma
	end
	aplicar()
end

local function boton(padre: Instance, contenido: string, tamano: UDim2, posicion: UDim2, color: Color3, alPulsar: () -> ()): (ImageButton, TextLabel)
	local b = Gui.panel(padre, "Boton", tamano, posicion, nil, true) :: any
	b.ImageColor3 = color
	local t = Gui.texto(b, contenido, UDim2.new(1, -16, 1, -12), UDim2.fromOffset(8, 5), Gui.TINTA, true)
	b.Activated:Connect(function()
		Sonido.reproducir("UiClick", nil, 0.5, 1.1)
		b.Rotation = -3
		TweenService:Create(b, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Rotation = 0 }):Play()
		alPulsar()
	end)
	return b, t
end

local function fila(orden: number, titulo: string): Frame
	local f = Instance.new("Frame")
	f.BackgroundTransparency = 1
	f.Size = UDim2.new(1, 0, 0, 58)
	f.LayoutOrder = orden
	local t = Gui.texto(f, titulo, UDim2.new(0.36, 0, 0, 34), UDim2.fromOffset(0, 12), Gui.TINTA, false, 27)
	t.TextXAlignment = Enum.TextXAlignment.Left
	f.Parent = panel:FindFirstChild("Filas")
	return f
end

local function deslizador(clave: string, orden: number, titulo: string, texto: (number) -> string, alCambiar: (number) -> ())
	local f = fila(orden, titulo)
	local fondo, relleno = Gui.barra(f, UDim2.new(0.42, 0, 0, 18), UDim2.new(0.36, 0, 0, 20), Gui.TURQUESA)
	local pomo = Gui.panel(fondo, "Boton", UDim2.fromOffset(30, 34), UDim2.fromScale(0, 0.5), Vector2.new(0.5, 0.5))
	pomo.ImageColor3 = Gui.AMARILLO
	pomo.ZIndex = 3
	local valor = Gui.texto(f, "", UDim2.new(0.1, 0, 0, 30), UDim2.new(0.79, 6, 0, 14), Gui.LAPIZ, false, 24)
	local fraccion = 0
	local function fijar(x: number)
		fraccion = math.clamp(x, 0, 1)
		Gui.llenar(relleno, fraccion)
		pomo.Position = UDim2.fromScale(fraccion, 0.5)
		valor.Text = texto(fraccion)
	end
	local function cambiar(x: number)
		fijar(x)
		alCambiar(fraccion)
		guardar()
	end
	local arrastrando = false
	local function desde(entrada: InputObject)
		local x = (entrada.Position.X - fondo.AbsolutePosition.X) / math.max(1, fondo.AbsoluteSize.X)
		cambiar(x)
	end
	local zona = Instance.new("TextButton")
	zona.BackgroundTransparency = 1
	zona.Text = ""
	zona.Size = UDim2.new(1, 24, 0, 44)
	zona.Position = UDim2.new(0, -12, 0.5, 0)
	zona.AnchorPoint = Vector2.new(0, 0.5)
	zona.ZIndex = 4
	zona.Parent = fondo
	zona.InputBegan:Connect(function(entrada)
		if entrada.UserInputType == Enum.UserInputType.MouseButton1 or entrada.UserInputType == Enum.UserInputType.Touch then
			arrastrando = true
			desde(entrada)
		end
	end)
	UserInputService.InputChanged:Connect(function(entrada)
		if arrastrando and (entrada.UserInputType == Enum.UserInputType.MouseMovement or entrada.UserInputType == Enum.UserInputType.Touch) then
			desde(entrada)
		end
	end)
	UserInputService.InputEnded:Connect(function(entrada)
		if entrada.UserInputType == Enum.UserInputType.MouseButton1 or entrada.UserInputType == Enum.UserInputType.Touch then
			arrastrando = false
		end
	end)
	boton(f, "-", UDim2.fromOffset(40, 40), UDim2.new(0.89, 4, 0, 9), Gui.TIZA, function()
		cambiar(fraccion - 0.1)
	end)
	boton(f, "+", UDim2.fromOffset(40, 40), UDim2.new(0.89, 48, 0, 9), Gui.TIZA, function()
		cambiar(fraccion + 0.1)
	end)
	deslizadores[clave] = { relleno = relleno, pomo = pomo, valor = valor, fijar = fijar }
end

local function ajustarEscala()
	local v = Workspace.CurrentCamera.ViewportSize
	local s = math.clamp(math.min(v.X / 1366, v.Y / 768), 0.5, 1.2)
	escala.Scale = s
	raiz.Size = UDim2.fromScale(1 / s, 1 / s)
end

function Ajustes.abrir()
	if abierto then
		return
	end
	abierto = true
	panel.Visible = true
	aparicion.Scale = 0.6
	panel.Rotation = -6
	TweenService:Create(aparicion, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	TweenService:Create(panel, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Rotation = 0 }):Play()
	Sonido.reproducir("UiClick", nil, 0.6, 0.9)
end

function Ajustes.cerrar()
	if not abierto then
		return
	end
	abierto = false
	local t = TweenService:Create(aparicion, TweenInfo.new(0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Scale = 0.2 })
	t.Completed:Connect(function()
		if not abierto then
			panel.Visible = false
		end
	end)
	t:Play()
end

function Ajustes.alternar()
	if abierto then
		Ajustes.cerrar()
	else
		Ajustes.abrir()
	end
end

local function construir()
	gui = Instance.new("ScreenGui")
	gui.Name = "Ajustes"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 30
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = jugador:WaitForChild("PlayerGui")
	raiz = Instance.new("Frame")
	raiz.BackgroundTransparency = 1
	raiz.Parent = gui
	escala = Instance.new("UIScale")
	escala.Parent = raiz
	ajustarEscala()
	Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(ajustarEscala)

	local abrir = boton(raiz, "AJUSTES (O)", UDim2.fromOffset(170, 50), UDim2.new(0, 14, 1, -14), Gui.PAPEL, Ajustes.alternar)
	abrir.AnchorPoint = Vector2.new(0, 1)
	local playerGui = jugador:WaitForChild("PlayerGui")
	task.spawn(function()
		while gui.Parent do
			local intro = playerGui:FindFirstChild("Intro")
			abrir.Visible = not (intro and intro:IsA("ScreenGui") and intro.Enabled)
			task.wait(0.4)
		end
	end)

	panel = Gui.panel(raiz, "Papel", UDim2.fromOffset(640, 470), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5))
	panel.Visible = false
	panel.ZIndex = 2
	aparicion = Instance.new("UIScale")
	aparicion.Parent = panel
	local modal = Instance.new("TextButton")
	modal.BackgroundTransparency = 1
	modal.Text = ""
	modal.Size = UDim2.fromScale(1, 1)
	modal.Modal = true
	modal.Parent = panel
	local titulo = Gui.texto(panel, "AJUSTES", UDim2.new(1, -120, 0, 52), UDim2.fromOffset(40, 26), Gui.NARANJA, true)
	titulo.TextXAlignment = Enum.TextXAlignment.Left
	boton(panel, "X", UDim2.fromOffset(52, 52), UDim2.new(1, -78, 0, 22), Gui.ROJO, Ajustes.cerrar)
	local filas = Instance.new("Frame")
	filas.Name = "Filas"
	filas.BackgroundTransparency = 1
	filas.Size = UDim2.new(1, -80, 1, -110)
	filas.Position = UDim2.fromOffset(40, 92)
	filas.Parent = panel
	Gui.lista(filas, 10)

	deslizador("Fov", 1, "Campo de visión", function(x)
		return tostring(math.floor(60 + x * 40 + 0.5))
	end, function(x)
		valores.Fov = math.floor(60 + x * 40 + 0.5)
		Camara.fov(valores.Fov)
	end)
	deslizador("Musica", 2, "Música", function(x)
		return `{math.floor(x * 100 + 0.5)}%`
	end, function(x)
		valores.Musica = x
		Sonido.volumen("Musica", x)
	end)
	deslizador("Efectos", 3, "Efectos", function(x)
		return `{math.floor(x * 100 + 0.5)}%`
	end, function(x)
		valores.Efectos = x
		Sonido.volumen("Efectos", x)
		Sonido.volumen("Ambiente", x)
	end)
	local filaCamara = fila(4, "Cámara")
	local _, tc = boton(filaCamara, "", UDim2.new(0.62, 0, 0, 48), UDim2.new(0.36, 0, 0, 5), Gui.AMARILLO, function()
		valores.Tercera = not valores.Tercera
		aplicar()
		guardar()
	end)
	textoCamara = tc
	local filaIdioma = fila(5, "Idioma")
	local _, ti = boton(filaIdioma, "", UDim2.new(0.62, 0, 0, 48), UDim2.new(0.36, 0, 0, 5), Gui.TURQUESA, function()
		local lista = idiomas()
		local i = 1
		for n, d in lista do
			if d.codigo == valores.Idioma then
				i = n
			end
		end
		valores.Idioma = lista[i % #lista + 1].codigo
		aplicar()
		guardar()
	end)
	textoIdioma = ti
end

function Ajustes.iniciar()
	construir()
	aplicar()
	leerGuardados()
	jugador:GetAttributeChangedSignal("Ajustes"):Connect(leerGuardados)
	ContextActionService:BindActionAtPriority("Ajustes", function(_, estado)
		if estado == Enum.UserInputState.Begin then
			Ajustes.alternar()
		end
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.O)
	UserInputService.InputBegan:Connect(function(entrada)
		if entrada.KeyCode == Enum.KeyCode.Escape and abierto then
			Ajustes.cerrar()
		end
	end)
end

return Ajustes
