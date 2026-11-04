--!strict
local CollectionService = game:GetService("CollectionService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Agarre = require(script.Parent.Agarre)
local BocaVoz = require(script.Parent.BocaVoz)
local Piloto = require(script.Parent.Piloto)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local RemotoResultados = Remotos:WaitForChild("Resultados") :: RemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder

local Interfaz = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model

local CREMA = Color3.fromRGB(255, 244, 224)
local NARANJA = Color3.fromRGB(242, 123, 43)
local TURQUESA = Color3.fromRGB(31, 166, 160)
local OSCURO = Color3.fromRGB(27, 27, 33)
local ROJO = Color3.fromRGB(217, 68, 58)
local VERDE = Color3.fromRGB(85, 190, 95)
local FUENTE = Enum.Font.FredokaOne

local gui: ScreenGui
local textoFase: TextLabel
local textoRuta: TextLabel
local relleno: Frame
local textoCuenta: TextLabel
local panelPiloto: Frame
local datosPiloto: TextLabel
local avisoPiloto: TextLabel
local barraGas: Frame
local textoEstado: TextLabel
local pista: TextLabel
local listaAvisos: Frame
local panelResultados: Frame
local textoResultados: TextLabel
local tituloResultados: TextLabel
local tableroGui: SurfaceGui
local ayuda: Frame

local function esquina(padre: Instance, radio: number)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, radio)
	c.Parent = padre
end

local function borde(padre: Instance, color: Color3, grosor: number)
	local s = Instance.new("UIStroke")
	s.Color = color
	s.Thickness = grosor
	s.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	s.Parent = padre
end

local function marco(padre: Instance, tamano: UDim2, posicion: UDim2, ancla: Vector2, color: Color3, transparencia: number): Frame
	local f = Instance.new("Frame")
	f.Size = tamano
	f.Position = posicion
	f.AnchorPoint = ancla
	f.BackgroundColor3 = color
	f.BackgroundTransparency = transparencia
	f.BorderSizePixel = 0
	f.Parent = padre
	return f
end

local function texto(padre: Instance, contenido: string, tamano: UDim2, posicion: UDim2, color: Color3, altura: number?): TextLabel
	local t = Instance.new("TextLabel")
	t.Text = contenido
	t.Size = tamano
	t.Position = posicion
	t.BackgroundTransparency = 1
	t.TextColor3 = color
	t.Font = FUENTE
	t.TextScaled = altura == nil
	if altura then
		t.TextSize = altura
	end
	t.RichText = true
	t.TextWrapped = true
	t.Parent = padre
	return t
end

local function numero(nombre: string): number
	local v = avion:GetAttribute(nombre)
	return if typeof(v) == "number" then v else 0
end

local function construir()
	gui = Instance.new("ScreenGui")
	gui.Name = "Overbooked"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = jugador:WaitForChild("PlayerGui")

	local barra = marco(gui, UDim2.fromOffset(560, 74), UDim2.new(0.5, 0, 0, 14), Vector2.new(0.5, 0), CREMA, 0.08)
	esquina(barra, 16)
	borde(barra, NARANJA, 3)
	textoFase = texto(barra, "", UDim2.new(1, -24, 0, 26), UDim2.fromOffset(12, 6), OSCURO)
	textoRuta = texto(barra, "", UDim2.new(1, -24, 0, 18), UDim2.fromOffset(12, 32), Color3.fromRGB(80, 80, 90))
	local fondoBarra = marco(barra, UDim2.new(1, -24, 0, 10), UDim2.new(0, 12, 1, -16), Vector2.zero, Color3.fromRGB(220, 210, 190), 0)
	esquina(fondoBarra, 5)
	relleno = marco(fondoBarra, UDim2.fromScale(0, 1), UDim2.fromScale(0, 0), Vector2.zero, TURQUESA, 0)
	esquina(relleno, 5)
	textoCuenta = texto(gui, "", UDim2.fromOffset(160, 40), UDim2.new(0.5, 200, 0, 30), NARANJA)
	textoCuenta.AnchorPoint = Vector2.new(0, 0)

	local estado = marco(gui, UDim2.fromOffset(210, 92), UDim2.new(1, -14, 0, 14), Vector2.new(1, 0), OSCURO, 0.25)
	esquina(estado, 12)
	textoEstado = texto(estado, "", UDim2.new(1, -16, 1, -12), UDim2.fromOffset(8, 6), CREMA, 16)
	textoEstado.TextXAlignment = Enum.TextXAlignment.Left
	textoEstado.TextYAlignment = Enum.TextYAlignment.Top

	local mira = marco(gui, UDim2.fromOffset(6, 6), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5), Color3.new(1, 1, 1), 0.1)
	esquina(mira, 3)
	borde(mira, OSCURO, 1)
	pista = texto(gui, "", UDim2.fromOffset(420, 26), UDim2.new(0.5, 0, 0.5, 26), Color3.new(1, 1, 1), 18)
	pista.AnchorPoint = Vector2.new(0.5, 0)
	pista.TextStrokeTransparency = 0.4

	listaAvisos = marco(gui, UDim2.fromOffset(620, 200), UDim2.new(0.5, 0, 0, 100), Vector2.new(0.5, 0), Color3.new(), 1)
	local disposicion = Instance.new("UIListLayout")
	disposicion.Padding = UDim.new(0, 6)
	disposicion.HorizontalAlignment = Enum.HorizontalAlignment.Center
	disposicion.SortOrder = Enum.SortOrder.LayoutOrder
	disposicion.Parent = listaAvisos

	panelPiloto = marco(gui, UDim2.fromOffset(330, 230), UDim2.new(0, 14, 1, -14), Vector2.new(0, 1), OSCURO, 0.15)
	esquina(panelPiloto, 14)
	borde(panelPiloto, TURQUESA, 3)
	panelPiloto.Visible = false
	texto(panelPiloto, "✈ CABINA", UDim2.new(1, -20, 0, 24), UDim2.fromOffset(10, 6), TURQUESA)
	datosPiloto = texto(panelPiloto, "", UDim2.new(1, -20, 0, 110), UDim2.fromOffset(10, 32), CREMA, 18)
	datosPiloto.TextXAlignment = Enum.TextXAlignment.Left
	datosPiloto.TextYAlignment = Enum.TextYAlignment.Top
	local fondoGas = marco(panelPiloto, UDim2.new(1, -20, 0, 12), UDim2.fromOffset(10, 146), Vector2.zero, Color3.fromRGB(60, 60, 70), 0)
	esquina(fondoGas, 6)
	barraGas = marco(fondoGas, UDim2.fromScale(0, 1), UDim2.fromScale(0, 0), Vector2.zero, NARANJA, 0)
	esquina(barraGas, 6)
	avisoPiloto = texto(panelPiloto, "", UDim2.new(1, -20, 0, 40), UDim2.fromOffset(10, 162), Color3.fromRGB(255, 205, 80), 16)
	local controles = texto(panelPiloto, "W/S subir/bajar · A/D girar · Shift/Ctrl gases · Espacio salir", UDim2.new(1, -20, 0, 20), UDim2.new(0, 10, 1, -24), Color3.fromRGB(170, 170, 180), 13)
	controles.TextXAlignment = Enum.TextXAlignment.Left

	panelResultados = marco(gui, UDim2.fromOffset(460, 420), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5), CREMA, 0)
	esquina(panelResultados, 20)
	borde(panelResultados, NARANJA, 4)
	panelResultados.Visible = false
	tituloResultados = texto(panelResultados, "", UDim2.new(1, -30, 0, 46), UDim2.fromOffset(15, 14), NARANJA)
	textoResultados = texto(panelResultados, "", UDim2.new(1, -40, 1, -80), UDim2.fromOffset(20, 66), OSCURO, 19)
	textoResultados.TextXAlignment = Enum.TextXAlignment.Left
	textoResultados.TextYAlignment = Enum.TextYAlignment.Top

	ayuda = marco(gui, UDim2.fromOffset(360, 300), UDim2.new(1, -14, 1, -14), Vector2.new(1, 1), OSCURO, 0.15)
	esquina(ayuda, 14)
	ayuda.Visible = false
	local textoAyuda = texto(ayuda, table.concat({
		"<b>CONTROLES</b>  (H para cerrar)",
		"Clic: coger / soltar · Clic der.: lanzar",
		"F: usar extintor o llave",
		"E: interactuar (servir, coger comida, botones)",
		"R (mantener): calmar a un pasajero asustado",
		"",
		"<b>PILOTO</b>: siéntate en el asiento izquierdo",
		"Shift acelera · W sube · A/D gira",
		"Aterriza con < 340 km/h y bajando despacio",
		"",
		"<b>TRIPULACIÓN</b>: sirve 🍔 ☕ 💧, apaga 🔥,",
		"tapa agujeros 🔧 y vigila la carga 🐊",
	}, "\n"), UDim2.new(1, -24, 1, -20), UDim2.fromOffset(12, 10), CREMA, 16)
	textoAyuda.TextXAlignment = Enum.TextXAlignment.Left
	textoAyuda.TextYAlignment = Enum.TextYAlignment.Top
	local indicacion = texto(gui, "H: controles", UDim2.fromOffset(140, 22), UDim2.new(1, -14, 1, -14), Color3.new(1, 1, 1), 14)
	indicacion.AnchorPoint = Vector2.new(1, 1)
	indicacion.TextStrokeTransparency = 0.5
	ayuda:GetPropertyChangedSignal("Visible"):Connect(function()
		indicacion.Visible = not ayuda.Visible and not panelPiloto.Visible
	end)
	panelPiloto:GetPropertyChangedSignal("Visible"):Connect(function()
		indicacion.Visible = not ayuda.Visible and not panelPiloto.Visible
	end)
end

local function aviso(contenido: string, tipo: string)
	local color = if tipo == "peligro" then ROJO elseif tipo == "bien" then VERDE else TURQUESA
	local caja = marco(listaAvisos, UDim2.fromOffset(600, 38), UDim2.new(), Vector2.zero, OSCURO, 0.2)
	caja.LayoutOrder = math.floor(os.clock() * 100)
	esquina(caja, 10)
	borde(caja, color, 2)
	local t = texto(caja, contenido, UDim2.new(1, -20, 1, -8), UDim2.fromOffset(10, 4), CREMA)
	local hijos = 0
	for _, h in listaAvisos:GetChildren() do
		if h:IsA("Frame") then
			hijos += 1
		end
	end
	if hijos > 4 then
		local mas, menor = nil :: Frame?, math.huge
		for _, h in listaAvisos:GetChildren() do
			if h:IsA("Frame") and h.LayoutOrder < menor then
				mas, menor = h, h.LayoutOrder
			end
		end
		if mas then
			mas:Destroy()
		end
	end
	task.delay(4.5, function()
		if caja.Parent then
			TweenService:Create(caja, TweenInfo.new(0.5), { BackgroundTransparency = 1 }):Play()
			TweenService:Create(t, TweenInfo.new(0.5), { TextTransparency = 1 }):Play()
			task.wait(0.5)
			caja:Destroy()
		end
	end)
end

local NOMBRES_FASE = {
	Aeropuerto = "🏢 AEROPUERTO · Elige un contrato en el tablero",
	Embarque = "🧳 EMBARQUE · ¡Subid al avión!",
	Despegue = "🛫 DESPEGUE",
	Vuelo = "✈ EN VUELO",
	Aproximacion = "🛬 APROXIMACIÓN · ¡Hay que aterrizar!",
	Frenando = "🛬 FRENANDO",
	Aterrizado = "✅ EN TIERRA",
	Estrellado = "💥 ¡ESTRELLADOS!",
}

local function contratoActual(): { [string]: any }?
	local json = Estado:GetAttribute("Contrato")
	if typeof(json) ~= "string" then
		return nil
	end
	local ok, datos = pcall(HttpService.JSONDecode, HttpService, json)
	return if ok and typeof(datos) == "table" then datos else nil
end

local function actualizarBarra()
	local faseJuego = Estado:GetAttribute("Fase")
	local faseAvion = avion:GetAttribute("Fase")
	local clave = if faseJuego == "Aeropuerto" or faseJuego == "Embarque" then faseJuego else faseAvion
	textoFase.Text = NOMBRES_FASE[if typeof(clave) == "string" then clave else ""] or ""
	local contrato = contratoActual()
	if faseJuego == "Aeropuerto" then
		local ciudad = Estado:GetAttribute("Ciudad")
		textoRuta.Text = `Estás en {if typeof(ciudad) == "string" then ciudad else "?"} · Pulsa E en un pedestal del tablero`
		relleno.Size = UDim2.fromScale(0, 1)
	elseif contrato then
		local total, recorrido = numero("Total"), numero("Distancia")
		textoRuta.Text = `{contrato.origen} ✈ {contrato.destino} · {math.max(0, math.floor(total - recorrido))} km restantes`
		relleno.Size = UDim2.fromScale(math.clamp(recorrido / math.max(total, 1), 0, 1), 1)
		if avion:GetAttribute("ZonaEntrega") then
			textoRuta.Text ..= " · 📦 ¡ZONA DE ENTREGA!"
		end
	end
	local cuenta = Estado:GetAttribute("Cuenta")
	textoCuenta.Text = if typeof(cuenta) == "number" and cuenta > 0 and (faseJuego == "Embarque" or faseJuego == "Aeropuerto") then `⏱ {cuenta}` else ""
end

local function actualizarEstado()
	local fuegoI = if avion:GetAttribute("MotorIzqFuego") then " 🔥" else ""
	local fuegoD = if avion:GetAttribute("MotorDerFuego") then " 🔥" else ""
	textoEstado.Text = table.concat({
		`🛡 Casco: {numero("Casco")}%`,
		`⚙ Motores: I {numero("MotorIzq")}%{fuegoI} · D {numero("MotorDer")}%{fuegoD}`,
		`⛽ Combustible: {numero("Combustible")}%`,
		if avion:GetAttribute("Cinturones") then "🔔 Cinturones: ON" else "🔕 Cinturones: OFF",
	}, "\n")
end

local function actualizarPiloto()
	local visible = Piloto.activo()
	panelPiloto.Visible = visible
	if not visible then
		return
	end
	local desvio = numero("Desvio")
	local rumbo = if desvio > 4 then "◀◀ Gira a la IZQUIERDA (A)" elseif desvio < -4 then "Gira a la DERECHA (D) ▶▶" else "✔ Rumbo correcto"
	datosPiloto.Text = table.concat({
		`ALTITUD  <b>{numero("Altitud")}</b> m   ({numero("Vertical")} m/s)`,
		`VELOCIDAD  <b>{numero("Velocidad")}</b> km/h`,
		`RUMBO  {rumbo}`,
		`AUTOPILOTO  {if avion:GetAttribute("Autopiloto") then "<font color=\"#55D66B\">ON</font>" else "OFF"}   ·   GASES {numero("Gases")}%`,
	}, "\n")
	barraGas.Size = UDim2.fromScale(numero("Gases") / 100, 1)
	local fase = avion:GetAttribute("Fase")
	local mensaje = ""
	if avion:GetAttribute("Perdida") then
		mensaje = "⚠ ¡PÉRDIDA! Acelera (Shift) y baja el morro (S)"
	elseif fase == "Despegue" then
		mensaje = `Acelera con Shift. A {Config.VUELO.VELOCIDAD_DESPEGUE} km/h pulsa W para despegar`
	elseif fase == "Aproximacion" then
		local restante = numero("Total") - numero("Distancia")
		mensaje = `Pista a {math.floor(restante)} km · baja a 0 m con < {Config.VUELO.VELOCIDAD_ATERRIZAJE} km/h y suave`
	elseif numero("Altitud") < 800 and fase == "Vuelo" then
		mensaje = "⚠ ¡Muy bajo! Sube (W)"
	end
	avisoPiloto.Text = mensaje
end

local function actualizarPista()
	local objeto = Agarre.sostenido()
	if objeto then
		local tipo = Agarre.tipo(objeto)
		pista.Text = if tipo == "Extintor" or tipo == "Llave" then "F: usar · Clic: soltar · Clic der.: lanzar" else "Clic: soltar · Clic der.: lanzar"
		return
	end
	local apuntado = Agarre.apuntado()
	if apuntado then
		local tipo = Agarre.tipo(apuntado)
		local def = Config.OBJETOS[tipo]
		pista.Text = `Clic: coger {if def then def.nombre elseif tipo == "Pasajero" then "pasajero" else string.lower(tipo)}`
	else
		pista.Text = ""
	end
end

local function burbuja(modelo: Instance)
	if not modelo:IsA("Model") then
		return
	end
	local cuerpo = modelo:WaitForChild("Cuerpo", 5)
	if not cuerpo or not cuerpo:IsA("BasePart") then
		return
	end
	local b = Instance.new("BillboardGui")
	b.Name = "Burbuja"
	b.Size = UDim2.fromOffset(64, 70)
	b.StudsOffset = Vector3.new(0, 3.3, 0)
	b.MaxDistance = 60
	b.Adornee = cuerpo
	b.ResetOnSpawn = false
	local fondo = marco(b, UDim2.fromOffset(56, 56), UDim2.fromOffset(4, 0), Vector2.zero, Color3.new(1, 1, 1), 0)
	esquina(fondo, 28)
	borde(fondo, OSCURO, 2)
	local icono = texto(fondo, "", UDim2.fromScale(0.8, 0.8), UDim2.fromScale(0.1, 0.1), OSCURO)
	local fondoPaciencia = marco(b, UDim2.fromOffset(52, 7), UDim2.fromOffset(6, 61), Vector2.zero, Color3.fromRGB(60, 60, 60), 0)
	esquina(fondoPaciencia, 3)
	local paciencia = marco(fondoPaciencia, UDim2.fromScale(1, 1), UDim2.new(), Vector2.zero, VERDE, 0)
	esquina(paciencia, 3)
	b.Parent = gui
	local emocion = ""
	local emocionHasta = 0
	local function refrescar()
		local pedido = modelo:GetAttribute("Pedido")
		local miedo = modelo:GetAttribute("Miedo")
		local p = modelo:GetAttribute("Paciencia")
		if typeof(pedido) == "string" and pedido ~= "" then
			icono.Text = Config.ICONOS[pedido] or "?"
			local f = math.clamp((if typeof(p) == "number" then p else 0) / Config.PASAJEROS.PACIENCIA, 0, 1)
			paciencia.Size = UDim2.fromScale(f, 1)
			paciencia.BackgroundColor3 = if f > 0.5 then VERDE elseif f > 0.25 then Color3.fromRGB(245, 205, 61) else ROJO
			fondoPaciencia.Visible = true
			b.Enabled = true
		elseif os.clock() < emocionHasta then
			icono.Text = emocion
			fondoPaciencia.Visible = false
			b.Enabled = true
		elseif typeof(miedo) == "number" and miedo > 0.5 then
			icono.Text = Config.ICONOS.Miedo
			fondoPaciencia.Visible = false
			b.Enabled = true
		else
			b.Enabled = false
		end
	end
	local conexiones = {
		modelo:GetAttributeChangedSignal("Pedido"):Connect(refrescar),
		modelo:GetAttributeChangedSignal("Paciencia"):Connect(refrescar),
		modelo:GetAttributeChangedSignal("Miedo"):Connect(refrescar),
		modelo:GetAttributeChangedSignal("Feliz"):Connect(function()
			emocion, emocionHasta = Config.ICONOS.Feliz, os.clock() + 2
			refrescar()
			task.delay(2.1, refrescar)
		end),
		modelo:GetAttributeChangedSignal("Enfado"):Connect(function()
			emocion, emocionHasta = Config.ICONOS.Enfado, os.clock() + 2.5
			refrescar()
			task.delay(2.6, refrescar)
		end),
	}
	refrescar()
	modelo.Destroying:Connect(function()
		for _, c in conexiones do
			c:Disconnect()
		end
		b:Destroy()
	end)
end

local etiquetas: { [Player]: { gui: BillboardGui, voz: TextLabel } } = {}

local function etiqueta(otro: Player, personaje: Model)
	local anterior = etiquetas[otro]
	if anterior then
		anterior.gui:Destroy()
	end
	local cabeza = personaje:WaitForChild("Head", 10)
	if not cabeza or not cabeza:IsA("BasePart") then
		return
	end
	local b = Instance.new("BillboardGui")
	b.Name = "Etiqueta"
	b.Size = UDim2.fromOffset(200, 30)
	b.StudsOffset = Vector3.new(0, 2.6, 0)
	b.MaxDistance = 80
	b.Adornee = cabeza
	b.ResetOnSpawn = false
	local color = otro:GetAttribute("Color")
	local nombre = texto(b, otro.DisplayName, UDim2.new(1, -30, 1, 0), UDim2.fromOffset(30, 0), if typeof(color) == "Color3" then color else CREMA)
	nombre.TextStrokeTransparency = 0.3
	local voz = texto(b, "🔊", UDim2.fromOffset(28, 28), UDim2.fromOffset(0, 1), Color3.new(1, 1, 1))
	voz.Visible = false
	b.Parent = gui
	etiquetas[otro] = { gui = b, voz = voz }
end

local function seguirJugador(otro: Player)
	if otro == jugador then
		return
	end
	if otro.Character then
		task.spawn(etiqueta, otro, otro.Character)
	end
	otro.CharacterAdded:Connect(function(personaje)
		etiqueta(otro, personaje)
	end)
end

local function riesgo(n: number): string
	return string.rep("★", n) .. string.rep("☆", 3 - n)
end

local ICONOS_CARGA = { Maleta = "🧳", Caja = "📦", CajaFragil = "🍾", Jaula = "🐊" }

local function tablero()
	local json = Estado:GetAttribute("Contratos")
	local aeropuerto = Workspace:FindFirstChild("Aeropuerto")
	local parte = aeropuerto and aeropuerto:FindFirstChild("Tablero", true)
	if not parte or not parte:IsA("BasePart") or typeof(json) ~= "string" then
		return
	end
	local ok, ofertas = pcall(HttpService.JSONDecode, HttpService, json)
	if not ok or typeof(ofertas) ~= "table" then
		return
	end
	if tableroGui then
		tableroGui:Destroy()
	end
	tableroGui = Instance.new("SurfaceGui")
	tableroGui.Name = "Tablero"
	tableroGui.Face = Enum.NormalId.Back
	tableroGui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	tableroGui.PixelsPerStud = 50
	tableroGui.LightInfluence = 0
	tableroGui.Adornee = parte
	tableroGui.ResetOnSpawn = false
	local colores = { NARANJA, TURQUESA, Color3.fromRGB(245, 205, 61) }
	texto(tableroGui, "SALIDAS · ELIGE TU VUELO (E en el pedestal)", UDim2.new(1, -40, 0, 50), UDim2.fromOffset(20, 10), CREMA)
	for i, o in ofertas :: { any } do
		local columna = marco(tableroGui, UDim2.new(1 / 3, -20, 1, -90), UDim2.new((i - 1) / 3, 10, 0, 74), Vector2.zero, Color3.fromRGB(40, 40, 48), 0)
		esquina(columna, 16)
		borde(columna, colores[i] or CREMA, 4)
		local carga = {}
		for _, c in o.carga do
			table.insert(carga, `{ICONOS_CARGA[c.tipo] or "📦"}×{c.cantidad}{if c.entrega then "🪂" else ""}`)
		end
		local estimado = o.pasajeros * o.pagoPasajero
		for _, c in o.carga do
			estimado += c.valor * c.cantidad
		end
		local t = texto(columna, table.concat({
			`<font size="64" color="#{(colores[i] or CREMA):ToHex()}">{i}</font>`,
			`<b>{o.titulo}</b>`,
			`{o.origen} → {o.destino}`,
			`📏 {o.distancia} km   👥 {o.pasajeros}`,
			table.concat(carga, "  "),
			`Riesgo {riesgo(o.riesgo)}`,
			`💰 ~{estimado}`,
			if o.entregaAerea then "🪂 Incluye entrega aérea" else "",
		}, "\n"), UDim2.new(1, -20, 1, -20), UDim2.fromOffset(10, 10), CREMA, 30)
		t.TextYAlignment = Enum.TextYAlignment.Top
	end
	tableroGui.Parent = jugador:WaitForChild("PlayerGui")
end

local function resultados(datos: any)
	if typeof(datos) ~= "table" then
		return
	end
	tituloResultados.Text = if datos.tipo == "Estrellado" then "💥 ¡ESTRELLADOS!" elseif datos.aterrizaje == "Perfecto" then "🏆 ¡ATERRIZAJE PERFECTO!" else "✅ ¡VUELO COMPLETADO!"
	local lineas = {
		if datos.tipo == "Estrellado" then `<b>{datos.motivo}</b>` else `Destino: <b>{datos.destino}</b>`,
		`👥 Pasajeros entregados: {datos.pasajeros}   (perdidos: {datos.perdidos})`,
		`😊 Satisfacción media: {datos.satisfaccion}%   ·   Servidos: {datos.servidos}`,
		`🧳 Carga intacta: +{datos.carga}`,
		`🪂 Entregas aéreas: +{datos.entregas}`,
		`🐊 Cocodrilo: {if datos.cocodrilo == "" then "—" else datos.cocodrilo}`,
		`🛡 Casco: {datos.casco}%`,
	}
	if datos.billetes then
		table.insert(lineas, `🎫 Billetes: +{datos.billetes}`)
	end
	if datos.bonus and datos.bonus > 0 then
		table.insert(lineas, `🛬 Bonus aterrizaje: +{datos.bonus}`)
	end
	table.insert(lineas, "")
	table.insert(lineas, `<b>TOTAL: {datos.total} 💰   ·   Para cada uno: {datos.porJugador} 💰</b>`)
	textoResultados.Text = table.concat(lineas, "\n")
	panelResultados.Visible = true
	task.delay(Config.PARTIDA.RESULTADOS - 0.5, function()
		panelResultados.Visible = false
	end)
end

function Interfaz.iniciar()
	construir()
	RemotoAviso.OnClientEvent:Connect(function(contenido, tipo)
		if typeof(contenido) == "string" then
			aviso(contenido, if typeof(tipo) == "string" then tipo else "info")
		end
	end)
	RemotoResultados.OnClientEvent:Connect(resultados)
	for _, modelo in CollectionService:GetTagged("Pasajero") do
		task.spawn(burbuja, modelo)
	end
	CollectionService:GetInstanceAddedSignal("Pasajero"):Connect(burbuja)
	for _, otro in Players:GetPlayers() do
		seguirJugador(otro)
	end
	Players.PlayerAdded:Connect(seguirJugador)
	Players.PlayerRemoving:Connect(function(otro)
		local e = etiquetas[otro]
		if e then
			e.gui:Destroy()
			etiquetas[otro] = nil
		end
	end)
	Estado:GetAttributeChangedSignal("Contratos"):Connect(tablero)
	Workspace.ChildAdded:Connect(function(hijo)
		if hijo.Name == "Aeropuerto" then
			task.wait(1)
			tablero()
		end
	end)
	task.spawn(tablero)
	UserInputService.InputBegan:Connect(function(entrada, procesado)
		if not procesado and entrada.KeyCode == Enum.KeyCode.H then
			ayuda.Visible = not ayuda.Visible
		end
	end)
	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		actualizarPista()
		acumulado += dt
		if acumulado < 0.15 then
			return
		end
		acumulado = 0
		actualizarBarra()
		actualizarEstado()
		actualizarPiloto()
		for otro, e in etiquetas do
			e.voz.Visible = BocaVoz.nivel(otro) > 0.08
		end
	end)
end

return Interfaz
