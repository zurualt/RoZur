--!strict
local ContextActionService = game:GetService("ContextActionService")
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Gui = require(ReplicatedStorage.Shared.Gui)
local ImagenesRobux = require(ReplicatedStorage.Shared.ImagenesRobux)
local BarraSuperior = require(script.Parent.BarraSuperior)
local Camara = require(script.Parent.Camara)
local Sonido = require(script.Parent.Sonido)

local R = Config.ROBUX
local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoCompras = Remotos:WaitForChild("Compras") :: RemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder
local avion = Workspace:WaitForChild("Avion") :: Model

local Robux = {}

local jugador = Players.LocalPlayer
local SIMBOLO = utf8.char(0xE002)
local ICONOS_RESERVA: { [string]: string } = {
	VidasInfinitas = "Corazon",
	Revivir = "Paracaidas",
	Cabra = "Alborotador",
	Gallinas = "Alborotador",
	Disco = "Estrella",
	Pajaros = "Motor",
	CaidaLibre = "Avion",
	Piratas = "Pirata",
}
local fichas: { [string]: number } = {}
local precios: { [string]: number } = {}
local cambio = Instance.new("BindableEvent")
local gui: ScreenGui
local escala: UIScale
local capaMuerte: Frame
local cuenta: TextLabel
local botonRevivir: ImageButton
local textoRevivir: TextLabel
local botonPase: ImageButton
local textoPase: TextLabel
local mirando: TextLabel
local listaCaidos: Frame
local caosDisponible = false
local panelCaos: ImageLabel
local filasCaos: { [string]: { boton: ImageButton, precio: TextLabel } } = {}
local cartel: Frame
local muertoDesde = 0
local objetivo: Player? = nil
local giroOrbita = 0

local function hayCaos(): boolean
	for _, e in R.CAOS do
		if e.producto ~= 0 then
			return true
		end
	end
	return false
end

function Robux.simbolo(): string
	return SIMBOLO
end

function Robux.fichas(nombre: string): number
	return fichas[nombre] or 0
end

function Robux.precio(nombre: string): string
	local base = if nombre == "VidasInfinitas" then R.PRECIO_PASE elseif nombre == "Revivir" then R.PRECIO_REVIVIR else 0
	for _, e in R.CAOS do
		if e.nombre == nombre then
			base = e.precio
		end
	end
	return SIMBOLO .. tostring(precios[nombre] or base)
end

function Robux.disponible(nombre: string): boolean
	if nombre == "VidasInfinitas" then
		return R.PASE_VIDAS ~= 0
	elseif nombre == "Revivir" then
		return R.REVIVIR ~= 0
	end
	for _, e in R.CAOS do
		if e.nombre == nombre then
			return e.producto ~= 0
		end
	end
	return false
end

function Robux.tienePase(): boolean
	return jugador:GetAttribute("VidasInfinitas") == true
end

function Robux.alCambiar(f: () -> ())
	cambio.Event:Connect(f)
end

function Robux.comprarPase()
	if R.PASE_VIDAS ~= 0 and not Robux.tienePase() then
		pcall(MarketplaceService.PromptGamePassPurchase, MarketplaceService, jugador, R.PASE_VIDAS)
	end
end

function Robux.comprar(nombre: string)
	RemotoCompras:FireServer("comprar", nombre)
end

function Robux.imagen(padre: Instance, nombre: string, tamano: UDim2, posicion: UDim2, ancla: Vector2?): ImageLabel
	local id = (ImagenesRobux :: { [string]: number })[nombre]
	if not id then
		return Gui.icono(padre, ICONOS_RESERVA[nombre] or "Diamante", tamano, posicion, ancla)
	end
	local i = Instance.new("ImageLabel")
	i.Name = "Icono"
	i.BackgroundTransparency = 1
	i.Image = `rbxassetid://{id}`
	i.ScaleType = Enum.ScaleType.Fit
	i.Size = tamano
	i.Position = posicion
	i.AnchorPoint = ancla or Vector2.zero
	i.Parent = padre
	return i
end

local function leerPrecios()
	local lista: { { nombre: string, id: number, tipo: Enum.InfoType } } = {
		{ nombre = "VidasInfinitas", id = R.PASE_VIDAS, tipo = Enum.InfoType.GamePass },
		{ nombre = "Revivir", id = R.REVIVIR, tipo = Enum.InfoType.Product },
	}
	for _, e in R.CAOS do
		table.insert(lista, { nombre = e.nombre, id = e.producto, tipo = Enum.InfoType.Product })
	end
	for _, p in lista do
		if p.id ~= 0 then
			local ok, info = pcall(MarketplaceService.GetProductInfo, MarketplaceService, p.id, p.tipo)
			if ok and typeof(info) == "table" and typeof(info.PriceInRobux) == "number" then
				precios[p.nombre] = info.PriceInRobux
			end
		end
	end
	cambio:Fire()
end

local function boton(padre: Instance, contenido: string, tamano: UDim2, posicion: UDim2, color: Color3, alPulsar: () -> ()): (ImageButton, TextLabel)
	local b = Gui.panel(padre, "Boton", tamano, posicion, nil, true) :: any
	b.ImageColor3 = color
	local t = Gui.texto(b, contenido, UDim2.new(1, -24, 1, -18), UDim2.fromOffset(12, 7), Gui.PAPEL, true)
	t.Name = "Texto"
	Gui.trazado(t)
	b.Activated:Connect(function()
		b.Rotation = -3
		TweenService:Create(b, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Rotation = 0 }):Play()
		Sonido.reproducir("UiClick", nil, 0.6, 1)
		alPulsar()
	end)
	return b, t
end

local function vivo(p: Player): boolean
	local personaje = p.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	return humanoide ~= nil and humanoide.Health > 0 and p:GetAttribute("Muerto") ~= true
end

local function vivos(): { Player }
	local lista = {}
	for _, p in Players:GetPlayers() do
		if p ~= jugador and vivo(p) then
			table.insert(lista, p)
		end
	end
	return lista
end

local function cambiarObjetivo(paso: number)
	local lista = vivos()
	if #lista == 0 then
		objetivo = nil
		return
	end
	local i = table.find(lista, objetivo :: Player) or 0
	objetivo = lista[(i - 1 + paso) % #lista + 1]
end

local function muerto(): boolean
	return jugador:GetAttribute("Muerto") == true
end

local function pintarMuerte()
	local activo = muerto()
	capaMuerte.Visible = activo
	if not activo then
		return
	end
	local n = Robux.fichas("Revivir")
	botonRevivir.Visible = R.REVIVIR ~= 0 or n > 0
	textoRevivir.Text = if n > 0 then `REVIVIR YA (x{n})` else `REVIVIR YA  {Robux.precio("Revivir")}`
	botonPase.Visible = R.PASE_VIDAS ~= 0 and not Robux.tienePase()
	textoPase.Text = `VIDAS INFINITAS  {Robux.precio("VidasInfinitas")}`
end

local function pintarCaidos()
	for _, h in listaCaidos:GetChildren() do
		if h:IsA("GuiObject") then
			h:Destroy()
		end
	end
	if muerto() or Estado:GetAttribute("Fase") ~= "Vuelo" or R.REVIVIR == 0 then
		return
	end
	local cabecera = false
	for i, p in Players:GetPlayers() do
		if p ~= jugador and p:GetAttribute("Muerto") == true then
			if not cabecera then
				cabecera = true
				local c = Gui.texto(listaCaidos, "COMPAÑEROS CAÍDOS (J)", UDim2.fromOffset(300, 30), UDim2.new(), Gui.PAPEL, true)
				c.TextXAlignment = Enum.TextXAlignment.Left
				Gui.trazado(c)
			end
			local b, t = boton(listaCaidos, `REVIVIR A {p.DisplayName}`, UDim2.fromOffset(300, 58), UDim2.new(), Gui.VERDE, function()
				RemotoCompras:FireServer("revivir", p.UserId)
			end)
			b.LayoutOrder = i
			t.Size = UDim2.new(1, -110, 1, -18)
			local precio = Gui.texto(b, if Robux.fichas("Revivir") > 0 then `x{Robux.fichas("Revivir")}` else Robux.precio("Revivir"), UDim2.new(0, 84, 1, -18), UDim2.new(1, -96, 0, 7), Gui.AMARILLO, true)
			Gui.trazado(precio)
		end
	end
end

local function pintarCaos()
	local enVuelo = Estado:GetAttribute("Fase") == "Vuelo"
	local guardadas = 0
	for _, e in R.CAOS do
		local f = filasCaos[e.nombre]
		local n = Robux.fichas(e.nombre)
		guardadas += n
		if f then
			f.boton.Visible = e.producto ~= 0 or n > 0
			f.precio.Text = if n > 0 then `LANZAR (x{n})` else Robux.precio(e.nombre)
			f.boton.ImageColor3 = if n > 0 then Gui.NARANJA else Gui.VERDE
		end
	end
	caosDisponible = enVuelo and (hayCaos() or guardadas > 0)
	if not caosDisponible then
		panelCaos.Visible = false
	end
	BarraSuperior.mostrar("Desastres", caosDisponible)
	BarraSuperior.insignia("Desastres", if guardadas > 0 then tostring(guardadas) else nil)
	BarraSuperior.activo("Desastres", panelCaos.Visible)
end

local function pintar()
	pintarMuerte()
	pintarCaidos()
	pintarCaos()
end

local function mostrarCartel(quien: string, nombre: string)
	local titulo = nombre
	for _, e in R.CAOS do
		if e.nombre == nombre then
			titulo = e.titulo
		end
	end
	cartel:ClearAllChildren()
	local tam = Instance.new("UIScale")
	tam.Scale = 0.2
	tam.Parent = cartel
	local fondo = Gui.panel(cartel, "NotaPeligro", UDim2.fromScale(1, 1), UDim2.new())
	Robux.imagen(fondo, nombre, UDim2.fromOffset(170, 170), UDim2.new(0, 18, 0.5, 0), Vector2.new(0, 0.5))
	Gui.texto(fondo, `¡{quien} HA PAGADO!`, UDim2.new(1, -220, 0, 52), UDim2.fromOffset(200, 34), Gui.TINTA, true)
	local abajo = Gui.texto(fondo, titulo, UDim2.new(1, -220, 0, 90), UDim2.fromOffset(200, 92), Gui.ROJO, true)
	Gui.trazado(abajo, Gui.PAPEL)
	cartel.Visible = true
	cartel.Rotation = -8
	TweenService:Create(tam, TweenInfo.new(0.45, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	TweenService:Create(cartel, TweenInfo.new(0.45, Enum.EasingStyle.Back), { Rotation = -2 }):Play()
	Sonido.reproducir("UiPeligro", nil, 0.9, 0.8)
	Camara.sacudir(0.35)
	task.delay(3, function()
		if tam.Parent then
			TweenService:Create(tam, TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Scale = 0 }):Play()
		end
	end)
end

local function construir()
	gui = Instance.new("ScreenGui")
	gui.Name = "Robux"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 22
	gui.IgnoreGuiInset = true
	gui.Parent = jugador:WaitForChild("PlayerGui")
	local raiz = Instance.new("Frame")
	raiz.BackgroundTransparency = 1
	raiz.Size = UDim2.fromScale(1, 1)
	raiz.Parent = gui
	escala = Instance.new("UIScale")
	escala.Parent = raiz
	local function ajustar()
		local s = Gui.escala(0.55, 1.1)
		escala.Scale = s
		raiz.Size = UDim2.fromScale(1 / s, 1 / s)
	end
	ajustar()
	Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(ajustar)

	capaMuerte = Instance.new("Frame")
	capaMuerte.BackgroundTransparency = 1
	capaMuerte.Size = UDim2.fromScale(1, 1)
	capaMuerte.Visible = false
	capaMuerte.Parent = raiz
	local titulo = Gui.texto(capaMuerte, "¡TE HAS CAÍDO DEL AVIÓN!", UDim2.fromOffset(760, 74), UDim2.new(0.5, 0, 1, -424), Gui.ROJO, true)
	titulo.AnchorPoint = Vector2.new(0.5, 0)
	Gui.trazado(titulo, Gui.PAPEL)
	cuenta = Gui.texto(capaMuerte, "", UDim2.fromOffset(600, 40), UDim2.new(0.5, 0, 1, -344), Gui.PAPEL, true)
	cuenta.AnchorPoint = Vector2.new(0.5, 0)
	Gui.trazado(cuenta)
	botonRevivir, textoRevivir = boton(capaMuerte, "", UDim2.fromOffset(400, 84), UDim2.new(0.5, 0, 1, -150), Gui.VERDE, function()
		RemotoCompras:FireServer("revivir", jugador.UserId)
	end)
	botonRevivir.AnchorPoint = Vector2.new(0.5, 1)
	botonPase, textoPase = boton(capaMuerte, "", UDim2.fromOffset(370, 58), UDim2.new(0.5, 0, 1, -84), Gui.AMARILLO, Robux.comprarPase)
	botonPase.AnchorPoint = Vector2.new(0.5, 1)
	textoPase.Position = UDim2.fromOffset(46, 7)
	textoPase.Size = UDim2.new(1, -58, 1, -18)
	Robux.imagen(botonPase, "VidasInfinitas", UDim2.fromOffset(62, 62), UDim2.new(0, -18, 0.5, 0), Vector2.new(0, 0.5))
	local fila = Instance.new("Frame")
	fila.BackgroundTransparency = 1
	fila.Size = UDim2.fromOffset(460, 50)
	fila.Position = UDim2.new(0.5, 0, 1, -246)
	fila.AnchorPoint = Vector2.new(0.5, 1)
	fila.Parent = capaMuerte
	boton(fila, "<", UDim2.fromOffset(56, 50), UDim2.new(), Gui.TURQUESA, function()
		cambiarObjetivo(-1)
	end)
	boton(fila, ">", UDim2.fromOffset(56, 50), UDim2.new(1, -56, 0, 0), Gui.TURQUESA, function()
		cambiarObjetivo(1)
	end)
	mirando = Gui.texto(fila, "", UDim2.new(1, -130, 1, -8), UDim2.fromOffset(65, 4), Gui.PAPEL, true)
	Gui.trazado(mirando)

	listaCaidos = Instance.new("Frame")
	listaCaidos.BackgroundTransparency = 1
	listaCaidos.Size = UDim2.fromOffset(300, 260)
	listaCaidos.Position = UDim2.new(0, 14, 0.5, 40)
	listaCaidos.Parent = raiz
	Gui.lista(listaCaidos, 8)

	BarraSuperior.agregar("Desastres", "Desastres", "Desastres (J)", 5, function()
		panelCaos.Visible = not panelCaos.Visible
		pintarCaos()
	end)
	BarraSuperior.mostrar("Desastres", false)

	panelCaos = Gui.panel(raiz, "Papel", UDim2.fromOffset(560, 540), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5))
	panelCaos.Visible = false
	local modal = Instance.new("TextButton")
	modal.BackgroundTransparency = 1
	modal.Text = ""
	modal.Size = UDim2.fromScale(1, 1)
	modal.Modal = true
	modal.Selectable = false
	modal.Parent = panelCaos
	local cabecera = Gui.texto(panelCaos, "DESASTRES DE PAGO", UDim2.fromOffset(420, 44), UDim2.fromOffset(28, 18), Gui.NARANJA, true)
	cabecera.TextXAlignment = Enum.TextXAlignment.Left
	local nota = Gui.texto(panelCaos, `Lánzale un desastre al avión. Si aterrizáis, +{R.BONUS_CAOS} monedas para la tripulación`, UDim2.fromOffset(500, 40), UDim2.fromOffset(28, 62), Gui.LAPIZ, false, 18)
	nota.TextXAlignment = Enum.TextXAlignment.Left
	local cerrar = boton(panelCaos, "X", UDim2.fromOffset(50, 50), UDim2.new(1, -18, 0, 14), Gui.ROJO, function()
		panelCaos.Visible = false
		pintarCaos()
	end)
	cerrar.AnchorPoint = Vector2.new(1, 0)
	local filas = Instance.new("Frame")
	filas.BackgroundTransparency = 1
	filas.Size = UDim2.fromOffset(510, 420)
	filas.Position = UDim2.fromOffset(24, 108)
	filas.Parent = panelCaos
	Gui.lista(filas, 6)
	for i, e in R.CAOS do
		local f = Gui.panel(filas, "Boton", UDim2.fromOffset(510, 64), UDim2.new())
		f.ImageColor3 = Gui.PAPEL
		f.LayoutOrder = i
		Robux.imagen(f, e.nombre, UDim2.fromOffset(56, 56), UDim2.new(0, 8, 0.5, -2), Vector2.new(0, 0.5))
		local t = Gui.texto(f, e.titulo, UDim2.fromOffset(270, 28), UDim2.fromOffset(72, 6), Gui.TINTA, true)
		t.TextXAlignment = Enum.TextXAlignment.Left
		local d = Gui.texto(f, e.descripcion, UDim2.fromOffset(280, 24), UDim2.fromOffset(72, 34), Gui.LAPIZ, false, 19)
		d.TextXAlignment = Enum.TextXAlignment.Left
		local b, bt = boton(f, "", UDim2.fromOffset(140, 52), UDim2.new(1, -8, 0.5, -2), Gui.VERDE, function()
			RemotoCompras:FireServer("caos", e.nombre)
		end)
		b.AnchorPoint = Vector2.new(1, 0.5)
		filasCaos[e.nombre] = { boton = b, precio = bt }
	end

	cartel = Instance.new("Frame")
	cartel.BackgroundTransparency = 1
	cartel.Size = UDim2.fromOffset(720, 220)
	cartel.Position = UDim2.new(0.5, 0, 0, 110)
	cartel.AnchorPoint = Vector2.new(0.5, 0)
	cartel.Visible = false
	cartel.Parent = raiz
end

local function seguir(dt: number)
	local camara = Workspace.CurrentCamera
	if not muerto() then
		return
	end
	if not Camara.esTerceraPersona() then
		Camara.terceraPersona(true)
	end
	local fin = jugador:GetAttribute("ReviveEn")
	local quedan = if typeof(fin) == "number" then math.max(0, math.ceil(fin - Workspace:GetServerTimeNow())) else 0
	cuenta.Text = `Vuelves a bordo en {quedan} s`
	if os.clock() - muertoDesde < 1.6 then
		return
	end
	local o = objetivo
	if not (o and o.Parent and vivo(o)) then
		cambiarObjetivo(1)
		o = objetivo
	end
	local personaje = o and o.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	if o and humanoide then
		mirando.Text = `Mirando a {o.DisplayName}`
		if camara.CameraType ~= Enum.CameraType.Custom then
			camara.CameraType = Enum.CameraType.Custom
		end
		if camara.CameraSubject ~= humanoide then
			camara.CameraSubject = humanoide
		end
		return
	end
	mirando.Text = "Mirando el avión"
	camara.CameraType = Enum.CameraType.Scriptable
	giroOrbita += dt * 0.25
	local centro = avion:GetPivot().Position
	local pos = centro + Vector3.new(math.sin(giroOrbita) * 120, 35, math.cos(giroOrbita) * 120)
	camara.CFrame = CFrame.lookAt(pos, centro)
end

local function alMorir()
	if muerto() then
		muertoDesde = os.clock()
		objetivo = nil
		Sonido.reproducir("UiPeligro", nil, 0.8, 0.7)
	else
		local camara = Workspace.CurrentCamera
		camara.CameraType = Enum.CameraType.Custom
		Camara.terceraPersona(false)
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		if humanoide then
			camara.CameraSubject = humanoide
		end
	end
	pintar()
end

function Robux.iniciar()
	construir()
	RemotoCompras.OnClientEvent:Connect(function(tipo, a, b)
		if tipo == "fichas" and typeof(a) == "table" then
			table.clear(fichas)
			for nombre, n in a do
				if typeof(nombre) == "string" and typeof(n) == "number" then
					fichas[nombre] = n
				end
			end
			pintar()
			cambio:Fire()
		elseif tipo == "cartel" and typeof(a) == "string" and typeof(b) == "string" then
			mostrarCartel(a, b)
		end
	end)
	jugador:GetAttributeChangedSignal("Muerto"):Connect(alMorir)
	jugador:GetAttributeChangedSignal("VidasInfinitas"):Connect(function()
		pintar()
		cambio:Fire()
	end)
	jugador.CharacterAdded:Connect(function()
		if not muerto() then
			alMorir()
		end
	end)
	Estado:GetAttributeChangedSignal("Fase"):Connect(pintar)
	local function vigilar(p: Player)
		p:GetAttributeChangedSignal("Muerto"):Connect(pintarCaidos)
	end
	for _, p in Players:GetPlayers() do
		vigilar(p)
	end
	Players.PlayerAdded:Connect(vigilar)
	Players.PlayerRemoving:Connect(function()
		task.defer(pintarCaidos)
	end)
	RunService:BindToRenderStep("OverbookedEspectador", Enum.RenderPriority.Camera.Value, seguir)
	ContextActionService:BindActionAtPriority("Desastres", function(_, estado)
		if estado ~= Enum.UserInputState.Begin or not caosDisponible then
			return Enum.ContextActionResult.Pass
		end
		panelCaos.Visible = not panelCaos.Visible
		pintarCaos()
		Sonido.reproducir("UiClick", nil, 0.6, 1)
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.J)
	pintar()
	task.spawn(leerPrecios)
end

return Robux
