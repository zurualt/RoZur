--!strict
local ContextActionService = game:GetService("ContextActionService")
local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Accesorios = require(ReplicatedStorage.Shared.Accesorios)
local Config = require(ReplicatedStorage.Shared.Config)
local Gui = require(ReplicatedStorage.Shared.Gui)
local Robux = require(script.Parent.Robux)
local Sonido = require(script.Parent.Sonido)

local RemotoTienda = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Tienda") :: RemoteEvent

type Tarjeta = { boton: ImageButton, foto: ImageLabel, icono: ImageLabel, precio: TextLabel, marca: ImageLabel, tamano: UIScale }
type FilaMejora = { estrellas: { ImageLabel }, boton: ImageButton, texto: TextLabel, precio: TextLabel, moneda: ImageLabel }
type FilaRobux = { boton: ImageButton, texto: TextLabel, info: TextLabel }
type Estado = { dinero: number, vuelos: number, tiene: { [string]: boolean }, puestos: { [string]: string }, mejoras: { [string]: number } }
type Vista = { y: number, d: number, a: number }

local Tienda = {}

local jugador = Players.LocalPlayer
local GRIS = Color3.fromRGB(160, 150, 140)
local CREMA_CLARO = Color3.fromRGB(252, 250, 244)
local VERDE_CLARO = Color3.fromRGB(214, 240, 196)
local FONDO_VISTA = Color3.fromRGB(214, 236, 232)
local TINTA_OJO = Color3.fromRGB(27, 27, 33)
local BLANCO_OJO = Color3.fromRGB(247, 247, 242)
local PESTANAS = {
	{ clave = "Cabeza", icono = "Gorro" },
	{ clave = "Cara", icono = "Feliz" },
	{ clave = "Espalda", icono = "Maleta" },
	{ clave = "Mejoras", icono = "Llave" },
	{ clave = "Robux", icono = "Diamante" },
}
local ICONOS_MEJORA = { Casco = "Casco", Combustible = "Combustible", Cocina = "Hamburguesa" }
local VISTAS: { [string]: Vista } = {
	Cabeza = { y = 1.55, d = 7.6, a = 0.45 },
	Cara = { y = 1.02, d = 6, a = 0.3 },
	Espalda = { y = -0.15, d = 10.5, a = math.pi - 0.55 },
}
local OJO_CENTRO = Vector3.new(0.336, 1.059, -0.89)
local OJO_NORMAL = Vector3.new(0.166, -0.028, -0.986)
local OJO_ESCALA = { [1] = 1.12, [-1] = 0.92 }
local DISTANCIA_CIERRE = 24

local estado: Estado = { dinero = 0, vuelos = 0, tiene = {}, puestos = {}, mejoras = {} }
local pestana = "Cabeza"
local elegidos: { [string]: string } = {}
local tarjetas: { [string]: Tarjeta } = {}
local filasMejora: { [string]: FilaMejora } = {}
local filasRobux: { [string]: FilaRobux } = {}
local botonesPestana: { [string]: ImageButton } = {}
local abierto = false
local construida = false
local gui: ScreenGui
local raiz: Frame
local escala: UIScale
local panel: ImageLabel
local aparicion: UIScale
local rejilla: ScrollingFrame
local listaMejoras: ScrollingFrame
local listaRobux: ScrollingFrame
local notaRobux: Frame
local lado: ImageLabel
local vista: ViewportFrame
local saltoVista: UIScale
local camaraVista: Camera
local pista: TextLabel
local tituloSel: TextLabel
local infoSel: TextLabel
local accion: ImageButton
local textoAccion: TextLabel
local precioAccion: TextLabel
local monedaAccion: ImageLabel
local notaMejoras: Frame
local etiquetaDinero: ImageLabel
local textoDinero: TextLabel
local textoVuelos: TextLabel
local iconosMando: { ImageLabel } = {}
local muneco: Model? = nil
local contador: NumberValue
local camara: Vista = { y = 1.55, d = 7.6, a = 0.45 }
local giroUsuario = 0
local arrastre: Vector3? = nil
local reloj = 0
local origen: Vector3? = nil
local bucle: RBXScriptConnection? = nil

local function leerEstado(datos: any)
	if typeof(datos) ~= "table" then
		return
	end
	estado.dinero = if typeof(datos.dinero) == "number" then datos.dinero else 0
	estado.vuelos = if typeof(datos.vuelos) == "number" then datos.vuelos else 0
	estado.tiene = if typeof(datos.tiene) == "table" then datos.tiene else {}
	estado.puestos = if typeof(datos.puestos) == "table" then datos.puestos else {}
	estado.mejoras = if typeof(datos.mejoras) == "table" then datos.mejoras else {}
end

local function lista(ranura: string): { Config.Accesorio }
	local r = {}
	for _, a in Config.TIENDA.ACCESORIOS do
		if a.ranura == ranura and Accesorios.disponible(a.nombre) then
			table.insert(r, a)
		end
	end
	return r
end

local function elegido(): Config.Accesorio?
	if pestana == "Mejoras" then
		return nil
	end
	local nombre = elegidos[pestana] or estado.puestos[pestana]
	local a = if nombre then Accesorios.de(nombre) else nil
	if a and Accesorios.disponible(a.nombre) then
		return a
	end
	return lista(pestana)[1]
end

local function situacion(a: Config.Accesorio): (boolean, boolean, boolean, boolean)
	local tiene = estado.tiene[a.nombre] == true
	local puesto = estado.puestos[a.ranura] == a.nombre
	local bloqueado = not tiene and estado.vuelos < a.vuelos
	local caro = not tiene and not bloqueado and estado.dinero < a.precio
	return tiene, puesto, bloqueado, caro
end

local function sacudir(g: GuiObject)
	local base = g.Rotation
	task.spawn(function()
		for _, r in { -7, 6, -4, 3, 0 } do
			g.Rotation = base + r
			task.wait(0.04)
		end
		g.Rotation = base
	end)
end

local function rebote(s: UIScale, desde: number)
	s.Scale = desde
	TweenService:Create(s, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Scale = 1 }):Play()
end

local function sello(texto: string, color: Color3)
	local s = Gui.panel(lado, "Sello", UDim2.fromOffset(210, 210), UDim2.fromOffset(145, 120), Vector2.new(0.5, 0.5))
	s.ImageColor3 = color
	s.ZIndex = 20
	s.Rotation = -30
	s.ImageTransparency = 1
	local t = Gui.texto(s, texto, UDim2.fromScale(0.86, 0.3), UDim2.fromScale(0.5, 0.5), color, true)
	t.AnchorPoint = Vector2.new(0.5, 0.5)
	t.ZIndex = 21
	t.TextTransparency = 1
	local tam = Instance.new("UIScale")
	tam.Scale = 2.4
	tam.Parent = s
	local entrada = TweenInfo.new(0.28, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
	TweenService:Create(tam, entrada, { Scale = 1 }):Play()
	TweenService:Create(s, entrada, { Rotation = -12, ImageTransparency = 0.05 }):Play()
	TweenService:Create(t, entrada, { TextTransparency = 0 }):Play()
	task.delay(0.22, function()
		Sonido.reproducir("Sello", nil, 0.9, 1)
		sacudir(lado)
	end)
	task.delay(1.4, function()
		local salida = TweenInfo.new(0.4)
		TweenService:Create(s, salida, { ImageTransparency = 1 }):Play()
		TweenService:Create(t, salida, { TextTransparency = 1 }):Play()
		task.wait(0.45)
		s:Destroy()
	end)
end

local function monedas()
	local rng = Random.new()
	local centro = etiquetaDinero.AbsolutePosition + etiquetaDinero.AbsoluteSize / 2 - panel.AbsolutePosition
	local s = escala.Scale * aparicion.Scale
	for _ = 1, 12 do
		local m = Gui.icono(panel, "Moneda", UDim2.fromOffset(34, 34), UDim2.fromOffset(centro.X / s, centro.Y / s), Vector2.new(0.5, 0.5))
		m.ZIndex = 30
		local arriba = UDim2.fromOffset(centro.X / s + rng:NextNumber(-150, 150), centro.Y / s + rng:NextNumber(-60, 70))
		local caida = arriba + UDim2.fromOffset(rng:NextNumber(-60, 60), rng:NextNumber(160, 260))
		local t1 = TweenService:Create(m, TweenInfo.new(0.32, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Position = arriba, Rotation = rng:NextNumber(-90, 90) })
		t1.Completed:Connect(function()
			local t2 = TweenService:Create(m, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Position = caida, ImageTransparency = 1, Rotation = rng:NextNumber(-360, 360) })
			t2.Completed:Connect(function()
				m:Destroy()
			end)
			t2:Play()
		end)
		t1:Play()
	end
	Sonido.reproducir("Ding", nil, 0.7, 1.2)
end

local function pieza(padre: Instance, marco: CFrame, tamano: Vector3, color: Color3)
	local p = Instance.new("Part")
	p.Size = tamano
	p.Color = color
	p.Material = Enum.Material.SmoothPlastic
	p.Anchored = true
	p.CFrame = marco
	local m = Instance.new("SpecialMesh")
	m.MeshType = Enum.MeshType.Sphere
	m.Parent = p
	p.Parent = padre
end

local function ponerOjos(copia: Model)
	for _, signo in { -1, 1 } do
		local c = Vector3.new(OJO_CENTRO.X * signo, OJO_CENTRO.Y, OJO_CENTRO.Z)
		local marco = CFrame.lookAt(c, c + Vector3.new(OJO_NORMAL.X * signo, OJO_NORMAL.Y, OJO_NORMAL.Z))
		local e = OJO_ESCALA[signo]
		pieza(copia, marco * CFrame.new(0, 0, -0.07 * e), Vector3.new(0.42, 0.42, 0.08) * e, TINTA_OJO)
		pieza(copia, marco * CFrame.new(0, 0, -0.1 * e), Vector3.new(0.37, 0.37, 0.13) * e, BLANCO_OJO)
		pieza(copia, marco * CFrame.new(0, -0.075 * e, -0.165 * e), Vector3.new(0.16, 0.16, 0.05) * e, TINTA_OJO)
	end
end

local function reposo(copia: Model)
	local base = copia:FindFirstChild("HumanoidRootPart")
	if not base or not base:IsA("BasePart") then
		return
	end
	local hijos: { [BasePart]: { Motor6D } } = {}
	for _, d in copia:GetDescendants() do
		local p0 = if d:IsA("Motor6D") then d.Part0 else nil
		if d:IsA("Motor6D") and p0 and d.Part1 then
			hijos[p0] = hijos[p0] or {}
			table.insert(hijos[p0], d)
		end
	end
	base.CFrame = CFrame.identity
	local cola: { BasePart } = { base }
	local i = 1
	while cola[i] and i < 64 do
		local p = cola[i]
		local motores = hijos[p]
		if motores then
			for _, m in motores do
				local p1 = m.Part1
				if p1 then
					p1.CFrame = p.CFrame * m.C0 * m.C1:Inverse()
					table.insert(cola, p1)
				end
			end
		end
		i += 1
	end
end

local function montar(copia: Model, nombre: string)
	local carpeta = ReplicatedStorage:FindFirstChild(Accesorios.CARPETA)
	local plantilla = carpeta and carpeta:FindFirstChild(nombre)
	if not plantilla or not plantilla:IsA("Model") then
		return
	end
	local parte = copia:FindFirstChild(Accesorios.parte(nombre))
	if not parte or not parte:IsA("BasePart") then
		return
	end
	local v = plantilla:Clone()
	v:PivotTo(parte.CFrame * v:GetPivot())
	v.Parent = copia
end

local function actualizarMuneco()
	local viejo = muneco
	if viejo then
		viejo:Destroy()
		muneco = nil
	end
	local personaje = jugador.Character
	if pestana == "Mejoras" or not personaje then
		return
	end
	local antes = personaje.Archivable
	personaje.Archivable = true
	local copia = personaje:Clone()
	personaje.Archivable = antes
	if not copia then
		return
	end
	for _, h in copia:GetChildren() do
		if not h:IsA("BasePart") then
			h:Destroy()
		end
	end
	for _, d in copia:GetDescendants() do
		if d:IsA("BaseScript") or d:IsA("Sound") or d:IsA("ParticleEmitter") or d:IsA("BillboardGui") or d:IsA("ProximityPrompt") then
			d:Destroy()
		end
	end
	reposo(copia)
	for _, d in copia:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true
			d.LocalTransparencyModifier = 0
		end
	end
	ponerOjos(copia)
	local sel = elegido()
	for _, ranura in Config.TIENDA.RANURAS do
		local nombre = if sel and ranura == pestana then sel.nombre else estado.puestos[ranura]
		if nombre then
			montar(copia, nombre)
		end
	end
	copia.Parent = vista
	muneco = copia
end

local function refrescarTarjetas()
	local sel = elegido()
	for nombre, t in tarjetas do
		local a = Accesorios.de(nombre)
		if not a then
			continue
		end
		local tiene, puesto, bloqueado, caro = situacion(a)
		local escogida = sel ~= nil and sel.nombre == nombre
		t.boton.ImageColor3 = if escogida then Gui.AMARILLO elseif puesto then VERDE_CLARO elseif tiene then Gui.PAPEL else CREMA_CLARO
		t.foto.ImageColor3 = if bloqueado then Color3.fromRGB(52, 46, 42) else Color3.new(1, 1, 1)
		t.marca.Visible = puesto
		Gui.ponerIcono(t.icono, if bloqueado then "Avion" else "Moneda")
		t.icono.Visible = not tiene
		t.precio.Position = if tiene then UDim2.new(0, 8, 1, -10) else UDim2.new(0, 38, 1, -10)
		t.precio.Size = if tiene then UDim2.new(1, -16, 0, 26) else UDim2.new(1, -46, 0, 26)
		t.precio.TextXAlignment = if tiene then Enum.TextXAlignment.Center else Enum.TextXAlignment.Left
		t.precio.Text = if puesto then "Puesto" elseif tiene then "Tuyo" elseif bloqueado then `{a.vuelos} vuelos` else tostring(a.precio)
		t.precio.TextColor3 = if puesto then Gui.VERDE elseif tiene then Gui.TURQUESA elseif bloqueado or caro then Gui.ROJO else Gui.TINTA
	end
end

local function refrescarLado()
	local a = elegido()
	local mejoras = pestana == "Mejoras" or pestana == "Robux"
	vista.Visible = not mejoras
	pista.Visible = not mejoras
	tituloSel.Visible = not mejoras
	infoSel.Visible = not mejoras
	accion.Visible = not mejoras and a ~= nil
	notaMejoras.Visible = pestana == "Mejoras"
	notaRobux.Visible = pestana == "Robux"
	if mejoras or not a then
		if not mejoras then
			tituloSel.Text = "Próximamente"
			infoSel.Text = ""
		end
		return
	end
	local tiene, puesto, bloqueado, caro = situacion(a)
	tituloSel.Text = a.titulo
	infoSel.Text = if puesto then "Lo llevas puesto" elseif tiene then "Ya es tuyo" elseif bloqueado then `Necesitas {a.vuelos} vuelos (llevas {estado.vuelos})` elseif caro then `Te faltan {a.precio - estado.dinero}` else ""
	infoSel.TextColor3 = if bloqueado or caro then Gui.ROJO else Gui.LAPIZ
	textoAccion.Text = if puesto then "QUITAR" elseif tiene then "PONER" else "COMPRAR"
	accion.ImageColor3 = if puesto then Gui.ROJO elseif tiene then Gui.TURQUESA elseif bloqueado or caro then GRIS else Gui.VERDE
	precioAccion.Visible = not tiene
	monedaAccion.Visible = not tiene
	precioAccion.Text = tostring(a.precio)
	textoAccion.Size = if tiene then UDim2.new(1, -24, 1, -18) else UDim2.new(0.56, -12, 1, -18)
end

local function refrescarMejoras()
	for _, m in Config.TIENDA.MEJORAS do
		local f = filasMejora[m.nombre]
		if not f then
			continue
		end
		local nivel = if typeof(estado.mejoras[m.nombre]) == "number" then estado.mejoras[m.nombre] else 0
		local precio = m.precios[nivel + 1]
		for k, e in f.estrellas do
			Gui.ponerIcono(e, if k <= nivel then "Estrella" else "EstrellaVacia")
		end
		f.texto.Text = if precio then "MEJORAR" else "Máximo"
		f.texto.Size = if precio then UDim2.new(1, -16, 0, 30) else UDim2.new(1, -16, 1, -18)
		f.precio.Visible = precio ~= nil
		f.moneda.Visible = precio ~= nil
		f.precio.Text = if precio then tostring(precio) else ""
		f.precio.TextColor3 = if precio and estado.dinero < precio then Gui.ROJO else Gui.PAPEL
		f.boton.ImageColor3 = if not precio then GRIS elseif estado.dinero >= precio then Gui.VERDE else Gui.AMARILLO
	end
end

local function refrescarRobux()
	for nombre, f in filasRobux do
		local disponible = Robux.disponible(nombre)
		local n = Robux.fichas(nombre)
		local tiene = nombre == "VidasInfinitas" and Robux.tienePase()
		f.boton.Visible = disponible or tiene
		f.texto.Text = if tiene then "Tuyo" else Robux.precio(nombre)
		f.boton.ImageColor3 = if tiene then GRIS else Gui.VERDE
		f.info.Text = if not disponible and not tiene then "Muy pronto" elseif n > 0 then `Guardados: {n}` else ""
	end
end

local function refrescar()
	textoVuelos.Text = tostring(estado.vuelos)
	if contador.Value ~= estado.dinero then
		TweenService:Create(contador, TweenInfo.new(0.6, Enum.EasingStyle.Quad), { Value = estado.dinero }):Play()
	end
	for clave, b in botonesPestana do
		local activa = clave == pestana
		b.ImageColor3 = if activa then Gui.NARANJA else Gui.TIZA
		b.Position = UDim2.new(b.Position.X, UDim.new(0, if activa then 70 else 76))
		local t = b:FindFirstChild("Texto")
		if t and t:IsA("TextLabel") then
			t.TextColor3 = if activa then Gui.PAPEL else Gui.TINTA
			t.TextStrokeTransparency = if activa then 0.2 else 1
		end
	end
	rejilla.Visible = pestana ~= "Mejoras" and pestana ~= "Robux"
	listaMejoras.Visible = pestana == "Mejoras"
	listaRobux.Visible = pestana == "Robux"
	refrescarTarjetas()
	refrescarMejoras()
	refrescarRobux()
	refrescarLado()
end

local function elegir(nombre: string, sonar: boolean)
	local a = Accesorios.de(nombre)
	if not a or a.ranura ~= pestana then
		return
	end
	local antes = elegido()
	elegidos[pestana] = nombre
	if antes and antes.nombre == nombre then
		return
	end
	if sonar then
		Sonido.reproducir("UiClick", nil, 0.6, 1.15)
	end
	refrescarTarjetas()
	refrescarLado()
	actualizarMuneco()
	rebote(saltoVista, 0.94)
end

local function pulsarAccion()
	local a = elegido()
	if not a or not abierto then
		return
	end
	local tiene, puesto, bloqueado, caro = situacion(a)
	if puesto then
		RemotoTienda:FireServer("quitar", a.ranura)
	elseif tiene then
		RemotoTienda:FireServer("poner", a.nombre)
	elseif bloqueado or caro then
		sacudir(accion)
		sacudir(if caro then etiquetaDinero else infoSel)
		Sonido.reproducir("UiPeligro", nil, 0.6, 1)
		return
	else
		RemotoTienda:FireServer("comprar", a.nombre)
	end
	Sonido.reproducir("UiClick", nil, 0.6, 0.95)
end

local function boton(padre: Instance, contenido: string, tamano: UDim2, posicion: UDim2, color: Color3, alPulsar: () -> ()): (ImageButton, TextLabel)
	local b = Gui.panel(padre, "Boton", tamano, posicion, nil, true) :: any
	b.ImageColor3 = color
	local t = Gui.texto(b, contenido, UDim2.new(1, -24, 1, -18), UDim2.fromOffset(12, 7), Gui.PAPEL, true)
	t.Name = "Texto"
	Gui.trazado(t)
	local limite = Instance.new("UITextSizeConstraint")
	limite.MaxTextSize = 30
	limite.Parent = t
	b.Activated:Connect(function()
		b.Rotation = -3
		TweenService:Create(b, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Rotation = 0 }):Play()
		alPulsar()
	end)
	return b, t
end

local function iconoMando(padre: Instance, tecla: Enum.KeyCode, tamano: number, posicion: UDim2, ancla: Vector2?)
	local i = Instance.new("ImageLabel")
	i.BackgroundTransparency = 1
	i.Size = UDim2.fromOffset(tamano, tamano)
	i.Position = posicion
	i.AnchorPoint = ancla or Vector2.zero
	i.ZIndex = 8
	i.Image = UserInputService:GetImageForKeyCode(tecla)
	i.Parent = padre
	table.insert(iconosMando, i)
end

local function mostrarMando()
	local mando = UserInputService.GamepadEnabled
	for _, i in iconosMando do
		i.Visible = mando
	end
end

local function dibujarTarjetas()
	for _, t in tarjetas do
		t.boton:Destroy()
	end
	table.clear(tarjetas)
	if pestana == "Mejoras" or pestana == "Robux" then
		return
	end
	for orden, a in lista(pestana) do
		local b = Gui.panel(rejilla, "Boton", UDim2.fromOffset(130, 158), UDim2.new(), nil, true) :: any
		b.Name = a.nombre
		b.LayoutOrder = orden
		b.AutoButtonColor = false
		local tam = Instance.new("UIScale")
		tam.Parent = b
		local imagen = Accesorios.miniatura(a.nombre)
		local foto = if imagen ~= "" then Instance.new("ImageLabel") else Gui.icono(b, "Gorro", UDim2.fromOffset(96, 96), UDim2.new(0.5, 0, 0, 8), Vector2.new(0.5, 0))
		if imagen ~= "" then
			foto.BackgroundTransparency = 1
			foto.Image = imagen
			foto.ScaleType = Enum.ScaleType.Fit
			foto.Size = UDim2.fromOffset(100, 100)
			foto.Position = UDim2.new(0.5, 0, 0, 5)
			foto.AnchorPoint = Vector2.new(0.5, 0)
			foto.Parent = b
		end
		local titulo = Gui.texto(b, a.titulo, UDim2.new(1, -14, 0, 30), UDim2.fromOffset(7, 98), Gui.TINTA, false)
		local limite = Instance.new("UITextSizeConstraint")
		limite.MaxTextSize = 18
		limite.Parent = titulo
		local icono = Gui.icono(b, "Moneda", UDim2.fromOffset(24, 24), UDim2.new(0, 10, 1, -11), Vector2.new(0, 1))
		local precio = Gui.texto(b, "", UDim2.new(1, -46, 0, 26), UDim2.new(0, 38, 1, -10), Gui.TINTA, true)
		precio.AnchorPoint = Vector2.new(0, 1)
		precio.TextXAlignment = Enum.TextXAlignment.Left
		local limitePrecio = Instance.new("UITextSizeConstraint")
		limitePrecio.MaxTextSize = 21
		limitePrecio.Parent = precio
		local marca = Gui.icono(b, "Tick", UDim2.fromOffset(38, 38), UDim2.new(1, 4, 0, -6), Vector2.new(1, 0))
		marca.ZIndex = 3
		b.Activated:Connect(function()
			elegir(a.nombre, true)
		end)
		b.SelectionGained:Connect(function()
			elegir(a.nombre, false)
		end)
		b.MouseEnter:Connect(function()
			TweenService:Create(tam, TweenInfo.new(0.12), { Scale = 1.05 }):Play()
		end)
		b.MouseLeave:Connect(function()
			TweenService:Create(tam, TweenInfo.new(0.12), { Scale = 1 }):Play()
		end)
		tarjetas[a.nombre] = { boton = b, foto = foto, icono = icono, precio = precio, marca = marca, tamano = tam }
	end
	rejilla.CanvasPosition = Vector2.zero
end

local function seleccionarConMando()
	if not abierto or not UserInputService.GamepadEnabled then
		return
	end
	local a = elegido()
	local t = a and tarjetas[a.nombre]
	if t then
		GuiService.SelectedObject = t.boton
	elseif pestana == "Mejoras" then
		local primera = Config.TIENDA.MEJORAS[1]
		local f = primera and filasMejora[primera.nombre]
		GuiService.SelectedObject = if f then f.boton else accion
	elseif pestana == "Robux" then
		local f = filasRobux.VidasInfinitas or filasRobux.Revivir
		GuiService.SelectedObject = if f then f.boton else nil
	end
end

local function cambiarPestana(clave: string)
	if clave == pestana then
		return
	end
	pestana = clave
	Sonido.reproducir("RasgarPapel", nil, 0.35, 1.3)
	local v = VISTAS[clave]
	if v then
		giroUsuario = 0
		camara.a = v.a + (camara.a - v.a) * 0.3
	end
	dibujarTarjetas()
	refrescar()
	actualizarMuneco()
	seleccionarConMando()
end

local function pestanaVecina(paso: number)
	for i, p in PESTANAS do
		if p.clave == pestana then
			cambiarPestana(PESTANAS[(i - 1 + paso) % #PESTANAS + 1].clave)
			return
		end
	end
end

local function animarVista(dt: number)
	reloj += dt
	local personaje = jugador.Character
	local cuerpo = personaje and personaje:FindFirstChild("HumanoidRootPart")
	if origen and cuerpo and cuerpo:IsA("BasePart") and (cuerpo.Position - origen).Magnitude > DISTANCIA_CIERRE then
		Tienda.cerrar()
		return
	end
	local objetivo = VISTAS[pestana]
	if not objetivo then
		return
	end
	local k = 1 - math.exp(-dt * 5)
	local a = objetivo.a + giroUsuario + (if arrastre then 0 else math.sin(reloj * 0.8) * 0.3)
	camara.y += (objetivo.y - camara.y) * k
	camara.d += (objetivo.d - camara.d) * k
	camara.a += (a - camara.a) * (if arrastre then 1 else k)
	local foco = Vector3.new(0, camara.y, 0)
	local dir = Vector3.new(math.sin(camara.a), 0.2, -math.cos(camara.a)).Unit
	camaraVista.CFrame = CFrame.lookAt(foco + dir * camara.d, foco)
end

local function ajustarEscala()
	local v = gui.AbsoluteSize
	if v.X < 1 or v.Y < 1 then
		return
	end
	local s = math.clamp(math.min(v.X * 0.97 / 920, v.Y * 0.95 / 540), 0.4, 1.3)
	escala.Scale = s
	raiz.Size = UDim2.fromScale(1 / s, 1 / s)
end

local function construir()
	construida = true
	gui = Instance.new("ScreenGui")
	gui.Name = "Tienda"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 25
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Enabled = false
	gui.Parent = jugador:WaitForChild("PlayerGui")
	raiz = Instance.new("Frame")
	raiz.BackgroundTransparency = 1
	raiz.Parent = gui
	escala = Instance.new("UIScale")
	escala.Parent = raiz
	gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(ajustarEscala)
	ajustarEscala()

	panel = Gui.panel(raiz, "Papel", UDim2.fromOffset(920, 540), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5))
	aparicion = Instance.new("UIScale")
	aparicion.Parent = panel
	local modal = Instance.new("TextButton")
	modal.BackgroundTransparency = 1
	modal.Text = ""
	modal.Size = UDim2.fromScale(1, 1)
	modal.Modal = true
	modal.Selectable = false
	modal.Parent = panel

	local titulo = Gui.texto(panel, "TIENDA DE LA TRIPULACIÓN", UDim2.fromOffset(420, 46), UDim2.fromOffset(32, 20), Gui.NARANJA, true)
	titulo.TextXAlignment = Enum.TextXAlignment.Left
	local cerrar = boton(panel, "X", UDim2.fromOffset(54, 54), UDim2.new(1, -22, 0, 16), Gui.ROJO, function()
		Tienda.cerrar()
	end)
	cerrar.AnchorPoint = Vector2.new(1, 0)
	iconoMando(cerrar, Enum.KeyCode.ButtonB, 30, UDim2.new(0, -6, 1, 6), Vector2.new(0, 1))

	etiquetaDinero = Gui.panel(panel, "Boton", UDim2.fromOffset(184, 54), UDim2.new(1, -86, 0, 16), Vector2.new(1, 0))
	etiquetaDinero.ImageColor3 = Gui.PAPEL
	Gui.icono(etiquetaDinero, "Moneda", UDim2.fromOffset(38, 38), UDim2.new(0, 10, 0.5, -2), Vector2.new(0, 0.5))
	textoDinero = Gui.texto(etiquetaDinero, "0", UDim2.new(1, -66, 1, -16), UDim2.fromOffset(54, 6), Gui.NARANJA, true)
	textoDinero.TextXAlignment = Enum.TextXAlignment.Left
	contador = Instance.new("NumberValue")
	contador.Changed:Connect(function(v)
		textoDinero.Text = tostring(math.floor(v + 0.5))
	end)
	local etiquetaVuelos = Gui.panel(panel, "Boton", UDim2.fromOffset(118, 54), UDim2.new(1, -278, 0, 16), Vector2.new(1, 0))
	etiquetaVuelos.ImageColor3 = Gui.PAPEL
	Gui.icono(etiquetaVuelos, "Avion", UDim2.fromOffset(38, 38), UDim2.new(0, 8, 0.5, -2), Vector2.new(0, 0.5))
	textoVuelos = Gui.texto(etiquetaVuelos, "0", UDim2.new(1, -58, 1, -16), UDim2.fromOffset(50, 6), Gui.TURQUESA, true)
	textoVuelos.TextXAlignment = Enum.TextXAlignment.Left

	for i, p in PESTANAS do
		local b, t = boton(panel, p.clave, UDim2.fromOffset(150, 54), UDim2.fromOffset(32 + (i - 1) * 158, 76), Gui.TIZA, function()
			cambiarPestana(p.clave)
		end)
		Gui.icono(b, p.icono, UDim2.fromOffset(36, 36), UDim2.new(0, 10, 0.5, -2), Vector2.new(0, 0.5))
		t.Position = UDim2.fromOffset(46, 8)
		t.Size = UDim2.new(1, -54, 1, -18)
		t.FontFace = Gui.CUERPO
		t.TextColor3 = Gui.TINTA
		t.TextStrokeTransparency = 1
		botonesPestana[p.clave] = b
	end
	iconoMando(panel, Enum.KeyCode.ButtonL1, 30, UDim2.fromOffset(2, 88))
	iconoMando(panel, Enum.KeyCode.ButtonR1, 30, UDim2.fromOffset(32 + #PESTANAS * 158, 88))

	local function desplazable(): ScrollingFrame
		local s = Instance.new("ScrollingFrame")
		s.BackgroundTransparency = 1
		s.BorderSizePixel = 0
		s.Position = UDim2.fromOffset(26, 140)
		s.Size = UDim2.fromOffset(566, 382)
		s.CanvasSize = UDim2.new()
		s.AutomaticCanvasSize = Enum.AutomaticSize.Y
		s.ScrollingDirection = Enum.ScrollingDirection.Y
		s.ScrollBarThickness = 8
		s.ScrollBarImageColor3 = Gui.TINTA
		s.Selectable = false
		s.Parent = panel
		local relleno = Instance.new("UIPadding")
		relleno.PaddingTop = UDim.new(0, 8)
		relleno.PaddingLeft = UDim.new(0, 6)
		relleno.PaddingBottom = UDim.new(0, 8)
		relleno.Parent = s
		return s
	end
	rejilla = desplazable()
	local grid = Instance.new("UIGridLayout")
	grid.CellSize = UDim2.fromOffset(130, 158)
	grid.CellPadding = UDim2.fromOffset(8, 10)
	grid.SortOrder = Enum.SortOrder.LayoutOrder
	grid.Parent = rejilla

	listaMejoras = desplazable()
	Gui.lista(listaMejoras, 10)
	for i, m in Config.TIENDA.MEJORAS do
		local fila = Gui.panel(listaMejoras, "Boton", UDim2.fromOffset(540, 112), UDim2.new())
		fila.ImageColor3 = Gui.PAPEL
		fila.LayoutOrder = i
		Gui.icono(fila, ICONOS_MEJORA[m.nombre] or "Llave", UDim2.fromOffset(68, 68), UDim2.new(0, 16, 0.5, -3), Vector2.new(0, 0.5))
		local t = Gui.texto(fila, m.titulo, UDim2.fromOffset(250, 30), UDim2.fromOffset(98, 10), Gui.TINTA, true)
		t.TextXAlignment = Enum.TextXAlignment.Left
		local estrellas = {}
		for k = 1, #m.precios do
			table.insert(estrellas, Gui.icono(fila, "EstrellaVacia", UDim2.fromOffset(26, 26), UDim2.fromOffset(352 + (k - 1) * 28, 12)))
		end
		local d = Gui.texto(fila, m.descripcion, UDim2.fromOffset(300, 48), UDim2.fromOffset(98, 44), Gui.LAPIZ, false, 18)
		d.TextXAlignment = Enum.TextXAlignment.Left
		d.TextYAlignment = Enum.TextYAlignment.Top
		local b, bt = boton(fila, "MEJORAR", UDim2.fromOffset(122, 76), UDim2.new(1, -14, 0.5, -3), Gui.VERDE, function()
			RemotoTienda:FireServer("mejora", m.nombre)
			Sonido.reproducir("UiClick", nil, 0.6, 0.95)
		end)
		b.AnchorPoint = Vector2.new(1, 0.5)
		b.Name = m.nombre
		bt.Size = UDim2.new(1, -16, 0, 30)
		bt.Position = UDim2.fromOffset(8, 6)
		local moneda = Gui.icono(b, "Moneda", UDim2.fromOffset(24, 24), UDim2.new(0, 14, 1, -10), Vector2.new(0, 1))
		local precio = Gui.texto(b, "", UDim2.new(1, -50, 0, 26), UDim2.new(0, 42, 1, -9), Gui.PAPEL, true)
		precio.AnchorPoint = Vector2.new(0, 1)
		precio.TextXAlignment = Enum.TextXAlignment.Left
		Gui.trazado(precio)
		filasMejora[m.nombre] = { estrellas = estrellas, boton = b, texto = bt, precio = precio, moneda = moneda }
	end

	listaRobux = desplazable()
	Gui.lista(listaRobux, 10)
	local productos = { { nombre = "VidasInfinitas", titulo = "Vidas infinitas", descripcion = `¿Te caes del avión? Vuelves en {Config.ROBUX.ESPERA_PASE} segundos. Para siempre.` }, { nombre = "Revivir", titulo = "Revivir", descripcion = "Vuelve al avión al instante cuando te caigas. Si no lo usas, se guarda." } }
	for _, e in Config.ROBUX.CAOS do
		table.insert(productos, { nombre = e.nombre, titulo = e.titulo, descripcion = `{e.descripcion}. Se lanza en pleno vuelo.` })
	end
	for i, prod in productos do
		local fila = Gui.panel(listaRobux, "Boton", UDim2.fromOffset(540, 104), UDim2.new())
		fila.ImageColor3 = if i == 1 then Gui.AMARILLO else Gui.PAPEL
		fila.LayoutOrder = i
		Robux.imagen(fila, prod.nombre, UDim2.fromOffset(80, 80), UDim2.new(0, 12, 0.5, -3), Vector2.new(0, 0.5))
		local t = Gui.texto(fila, prod.titulo, UDim2.fromOffset(280, 30), UDim2.fromOffset(102, 8), Gui.TINTA, true)
		t.TextXAlignment = Enum.TextXAlignment.Left
		local d = Gui.texto(fila, prod.descripcion, UDim2.fromOffset(280, 44), UDim2.fromOffset(102, 40), Gui.LAPIZ, false, 17)
		d.TextXAlignment = Enum.TextXAlignment.Left
		d.TextYAlignment = Enum.TextYAlignment.Top
		local b, bt = boton(fila, "", UDim2.fromOffset(126, 64), UDim2.new(1, -12, 0.5, -10), Gui.VERDE, function()
			if prod.nombre == "VidasInfinitas" then
				Robux.comprarPase()
			else
				Robux.comprar(prod.nombre)
			end
		end)
		b.AnchorPoint = Vector2.new(1, 0.5)
		local info = Gui.texto(fila, "", UDim2.fromOffset(126, 20), UDim2.new(1, -12, 1, -6), Gui.TURQUESA, false, 16)
		info.AnchorPoint = Vector2.new(1, 1)
		filasRobux[prod.nombre] = { boton = b, texto = bt, info = info }
	end
	Robux.alCambiar(function()
		if construida and abierto then
			refrescarRobux()
		end
	end)

	lado = Gui.panel(panel, "Papel", UDim2.fromOffset(292, 388), UDim2.fromOffset(604, 136))
	lado.ImageColor3 = FONDO_VISTA
	vista = Instance.new("ViewportFrame")
	vista.BackgroundTransparency = 1
	vista.Size = UDim2.fromOffset(272, 194)
	vista.Position = UDim2.fromOffset(10, 10)
	vista.Ambient = Color3.fromRGB(170, 166, 160)
	vista.LightColor = Color3.fromRGB(255, 248, 236)
	vista.LightDirection = Vector3.new(-0.6, -1, -0.8)
	vista.Parent = lado
	saltoVista = Instance.new("UIScale")
	saltoVista.Parent = vista
	camaraVista = Instance.new("Camera")
	camaraVista.FieldOfView = 32
	camaraVista.Parent = vista
	vista.CurrentCamera = camaraVista
	vista.InputBegan:Connect(function(entrada: InputObject)
		if entrada.UserInputType == Enum.UserInputType.MouseButton1 or entrada.UserInputType == Enum.UserInputType.Touch then
			arrastre = entrada.Position
		end
	end)
	UserInputService.InputChanged:Connect(function(entrada: InputObject)
		local previa = arrastre
		if previa and (entrada.UserInputType == Enum.UserInputType.MouseMovement or entrada.UserInputType == Enum.UserInputType.Touch) then
			giroUsuario -= (entrada.Position.X - previa.X) * 0.012
			arrastre = entrada.Position
		elseif abierto and entrada.KeyCode == Enum.KeyCode.Thumbstick2 and math.abs(entrada.Position.X) > 0.2 then
			giroUsuario -= entrada.Position.X * 0.08
		end
	end)
	UserInputService.InputEnded:Connect(function(entrada: InputObject)
		if entrada.UserInputType == Enum.UserInputType.MouseButton1 or entrada.UserInputType == Enum.UserInputType.Touch then
			arrastre = nil
		end
	end)
	pista = Gui.texto(lado, "Arrastra para girar", UDim2.fromOffset(272, 20), UDim2.fromOffset(10, 208), Gui.LAPIZ, false, 15)
	tituloSel = Gui.texto(lado, "", UDim2.fromOffset(264, 34), UDim2.fromOffset(14, 230), Gui.TINTA, true)
	local limiteTitulo = Instance.new("UITextSizeConstraint")
	limiteTitulo.MaxTextSize = 28
	limiteTitulo.Parent = tituloSel
	infoSel = Gui.texto(lado, "", UDim2.fromOffset(264, 44), UDim2.fromOffset(14, 264), Gui.LAPIZ, false, 18)
	infoSel.TextYAlignment = Enum.TextYAlignment.Top
	local b, t = boton(lado, "COMPRAR", UDim2.fromOffset(264, 66), UDim2.fromOffset(14, 308), Gui.VERDE, pulsarAccion)
	accion = b
	textoAccion = t
	monedaAccion = Gui.icono(accion, "Moneda", UDim2.fromOffset(32, 32), UDim2.new(0.56, 0, 0.5, -3), Vector2.new(0, 0.5))
	precioAccion = Gui.texto(accion, "", UDim2.new(0.44, -48, 1, -22), UDim2.new(0.56, 36, 0, 8), Gui.PAPEL, true)
	precioAccion.TextXAlignment = Enum.TextXAlignment.Left
	Gui.trazado(precioAccion)
	iconoMando(accion, Enum.KeyCode.ButtonY, 30, UDim2.new(1, 6, 0, -8), Vector2.new(1, 0))

	notaMejoras = Instance.new("Frame")
	notaMejoras.BackgroundTransparency = 1
	notaMejoras.Size = UDim2.fromScale(1, 1)
	notaMejoras.Visible = false
	notaMejoras.Parent = lado
	Gui.icono(notaMejoras, "Avion", UDim2.fromOffset(150, 150), UDim2.new(0.5, 0, 0, 40), Vector2.new(0.5, 0))
	local nota = Gui.texto(notaMejoras, "Las mejoras se aplican si alguien de la tripulación las tiene.", UDim2.fromOffset(250, 120), UDim2.fromOffset(21, 210), Gui.TINTA, false, 22)
	nota.TextYAlignment = Enum.TextYAlignment.Top

	notaRobux = Instance.new("Frame")
	notaRobux.BackgroundTransparency = 1
	notaRobux.Size = UDim2.fromScale(1, 1)
	notaRobux.Visible = false
	notaRobux.Parent = lado
	Robux.imagen(notaRobux, "VidasInfinitas", UDim2.fromOffset(170, 170), UDim2.new(0.5, 0, 0, 30), Vector2.new(0.5, 0))
	local notaR = Gui.texto(notaRobux, "Gracias por apoyar a la peor aerolínea del mundo. Los desastres y los revivir que no uses se guardan para más tarde.", UDim2.fromOffset(250, 150), UDim2.fromOffset(21, 214), Gui.TINTA, false, 20)
	notaR.TextYAlignment = Enum.TextYAlignment.Top

	UserInputService.GamepadConnected:Connect(mostrarMando)
	UserInputService.GamepadDisconnected:Connect(mostrarMando)
	mostrarMando()
	ReplicatedStorage.ChildAdded:Connect(function(hijo)
		if hijo.Name == Accesorios.CARPETA then
			hijo.ChildAdded:Connect(function()
				if abierto then
					actualizarMuneco()
				end
			end)
		end
	end)
	local carpeta = ReplicatedStorage:FindFirstChild(Accesorios.CARPETA)
	if carpeta then
		carpeta.ChildAdded:Connect(function()
			if abierto then
				actualizarMuneco()
			end
		end)
	end
end

local function accionMando(_: string, fase: Enum.UserInputState, entrada: InputObject): Enum.ContextActionResult
	if fase ~= Enum.UserInputState.Begin then
		return Enum.ContextActionResult.Pass
	end
	if entrada.KeyCode == Enum.KeyCode.ButtonB then
		Tienda.cerrar()
	elseif entrada.KeyCode == Enum.KeyCode.ButtonL1 then
		pestanaVecina(-1)
	elseif entrada.KeyCode == Enum.KeyCode.ButtonR1 then
		pestanaVecina(1)
	elseif entrada.KeyCode == Enum.KeyCode.ButtonY then
		pulsarAccion()
	end
	return Enum.ContextActionResult.Sink
end

function Tienda.abrir()
	if not construida then
		construir()
	end
	if abierto then
		return
	end
	abierto = true
	local personaje = jugador.Character
	local cuerpo = personaje and personaje:FindFirstChild("HumanoidRootPart")
	origen = if cuerpo and cuerpo:IsA("BasePart") then cuerpo.Position else nil
	contador.Value = estado.dinero
	textoDinero.Text = tostring(estado.dinero)
	gui.Enabled = true
	ajustarEscala()
	dibujarTarjetas()
	refrescar()
	actualizarMuneco()
	local v = VISTAS[pestana]
	if v then
		camara.y, camara.d, camara.a = v.y, v.d, v.a + 1.2
	end
	aparicion.Scale = 0.6
	panel.Rotation = -6
	TweenService:Create(aparicion, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Scale = 1 }):Play()
	TweenService:Create(panel, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Rotation = 0 }):Play()
	Sonido.reproducir("RasgarPapel", nil, 0.5, 1)
	bucle = RunService.RenderStepped:Connect(animarVista)
	ContextActionService:BindActionAtPriority("TiendaMando", accionMando, false, 3000, Enum.KeyCode.ButtonB, Enum.KeyCode.ButtonL1, Enum.KeyCode.ButtonR1, Enum.KeyCode.ButtonY)
	mostrarMando()
	task.defer(seleccionarConMando)
end

function Tienda.cerrar()
	if not abierto then
		return
	end
	abierto = false
	origen = nil
	arrastre = nil
	local b = bucle
	if b then
		b:Disconnect()
		bucle = nil
	end
	ContextActionService:UnbindAction("TiendaMando")
	if GuiService.SelectedObject and GuiService.SelectedObject:IsDescendantOf(gui) then
		GuiService.SelectedObject = nil
	end
	Sonido.reproducir("UiClick", nil, 0.6, 0.85)
	local t = TweenService:Create(aparicion, TweenInfo.new(0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Scale = 0.2 })
	t.Completed:Connect(function()
		if not abierto then
			gui.Enabled = false
			local m = muneco
			if m then
				m:Destroy()
				muneco = nil
			end
		end
	end)
	t:Play()
end

local function reaccionar(evento: any)
	if typeof(evento) ~= "table" or typeof(evento.tipo) ~= "string" or not abierto then
		return
	end
	local tipo = evento.tipo
	if tipo == "comprado" then
		sello("¡COMPRADO!", Gui.VERDE)
		monedas()
		rebote(saltoVista, 1.18)
	elseif tipo == "mejora" then
		sello("¡MEJORADO!", Gui.NARANJA)
		monedas()
		Sonido.reproducir("Reparado", nil, 0.6, 1)
	elseif tipo == "puesto" then
		Sonido.reproducir("Pop", nil, 0.7, 1.1)
		rebote(saltoVista, 1.15)
	elseif tipo == "quitado" then
		Sonido.reproducir("Pop", nil, 0.6, 0.8)
		rebote(saltoVista, 0.88)
	elseif tipo == "pobre" or tipo == "bloqueado" then
		Sonido.reproducir("UiPeligro", nil, 0.6, 1)
		sacudir(if tipo == "pobre" then etiquetaDinero else infoSel)
		sacudir(accion)
	end
end

function Tienda.iniciar()
	RemotoTienda.OnClientEvent:Connect(function(abrir, datos, evento)
		leerEstado(datos)
		if abrir == true then
			Tienda.abrir()
		end
		if not abierto then
			return
		end
		refrescar()
		local tipo = if typeof(evento) == "table" then evento.tipo else nil
		if tipo == "comprado" or tipo == "puesto" or tipo == "quitado" then
			actualizarMuneco()
		end
		reaccionar(evento)
	end)
	UserInputService.InputBegan:Connect(function(entrada)
		if entrada.KeyCode == Enum.KeyCode.Escape and abierto then
			Tienda.cerrar()
		end
	end)
	jugador.CharacterAdded:Connect(function()
		Tienda.cerrar()
	end)
end

return Tienda
