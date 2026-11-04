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
local Visuales = require(ReplicatedStorage.Shared.Visuales)
local Contratos = require(ReplicatedStorage.Shared.Contratos)
local Gui = require(ReplicatedStorage.Shared.Gui)
local Agarre = require(script.Parent.Agarre)
local BocaVoz = require(script.Parent.BocaVoz)
local Piloto = require(script.Parent.Piloto)
local Sonido = require(script.Parent.Sonido)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local RemotoResultados = Remotos:WaitForChild("Resultados") :: RemoteEvent
local RemotoTienda = Remotos:WaitForChild("Tienda") :: RemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder

local Interfaz = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model

local CREMA = Color3.fromRGB(255, 244, 224)
local NARANJA = Color3.fromRGB(242, 123, 43)
local TURQUESA = Color3.fromRGB(31, 166, 160)
local FUENTE_TABLERO = Enum.Font.FredokaOne

type Medidor = { relleno: ImageLabel, texto: TextLabel, icono: ImageLabel }

local gui: ScreenGui
local raiz: Frame
local escala: UIScale
local etiquetasGui: Instance
local contratoCache: { [string]: any }? = nil
local textoFase: TextLabel
local textoRuta: TextLabel
local relleno: ImageLabel
local avionRuta: ImageLabel
local relojCuenta: ImageLabel
local textoCuenta: TextLabel
local medidores: { [string]: Medidor } = {}
local iconoCinturones: ImageLabel
local textoCinturones: TextLabel
local panelPiloto: ImageLabel
local datosPiloto: TextLabel
local avisoPiloto: TextLabel
local barraGas: ImageLabel
local pista: TextLabel
local listaAvisos: Frame
local panelResultados: ImageLabel
local selloResultados: ImageLabel
local textoSello: TextLabel
local tituloResultados: TextLabel
local filasResultados: Frame
local tableroGui: SurfaceGui
local ayuda: ImageLabel
local resaltado: Highlight
local ultimoApuntado: Instance? = nil
local panelTienda: ImageLabel? = nil
local estadoTienda: { [string]: any }? = nil

local function numero(nombre: string): number
	local v = avion:GetAttribute(nombre)
	return if typeof(v) == "number" then v else 0
end

local function izquierda(t: TextLabel): TextLabel
	t.TextXAlignment = Enum.TextXAlignment.Left
	return t
end

local function colorNivel(f: number): Color3
	return if f > 0.5 then Gui.VERDE elseif f > 0.25 then Gui.AMARILLO else Gui.ROJO
end

local function ajustarEscala()
	local v = Workspace.CurrentCamera.ViewportSize
	local s = math.clamp(math.min(v.X / 1366, v.Y / 768), 0.55, 1.2)
	escala.Scale = s
	raiz.Size = UDim2.fromScale(1 / s, 1 / s)
end

local FILAS_ESTADO = {
	{ clave = "Casco", icono = "Casco", letra = "" },
	{ clave = "MotorIzq", icono = "Motor", letra = "I" },
	{ clave = "MotorDer", icono = "Motor", letra = "D" },
	{ clave = "Combustible", icono = "Combustible", letra = "" },
}

local LINEAS_AYUDA = {
	{ nil, "<b>Clic</b> coger / soltar · <b>Clic der.</b> lanzar" },
	{ nil, "<b>F</b> usar extintor, llave o agua" },
	{ nil, "<b>E</b> servir, coger comida y pulsar botones" },
	{ nil, "<b>G</b> sentarte · <b>T</b> abrir o cerrar altillos" },
	{ nil, "<b>R</b> (mantener) calmar a un pasajero" },
	{ "Hamburguesa", "Lanza la comida al pasajero que la pide" },
	{ "Maleta", "Tapa un agujero lanzándole una maleta" },
	{ "Cocodrilo", "El cocodrilo persigue la comida" },
	{ "Cinturon", "Sentado no te caes con las turbulencias" },
	{ "Llave", "Piolet de la bodega: trepa por fuera del avión" },
	{ "Aduana", "Escanea las maletas: el contrabando va al contenedor" },
	{ "Volante", "Piloto: asiento izquierdo · Shift acelera · W sube" },
	{ "Aterrizaje", "Aterriza a menos de 340 km/h y bajando despacio" },
}

local function construir()
	gui = Instance.new("ScreenGui")
	gui.Name = "Overbooked"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = jugador:WaitForChild("PlayerGui")
	etiquetasGui = jugador:WaitForChild("PlayerGui")
	raiz = Instance.new("Frame")
	raiz.Name = "Raiz"
	raiz.BackgroundTransparency = 1
	raiz.Parent = gui
	escala = Instance.new("UIScale")
	escala.Parent = raiz
	ajustarEscala()
	Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(ajustarEscala)

	local billete = Gui.panel(raiz, "Billete", UDim2.fromOffset(640, 104), UDim2.new(0.5, 0, 0, 8), Vector2.new(0.5, 0))
	textoFase = izquierda(Gui.texto(billete, "", UDim2.new(1, -130, 0, 30), UDim2.fromOffset(28, 18), Gui.TINTA, true))
	textoRuta = izquierda(Gui.texto(billete, "", UDim2.new(1, -130, 0, 22), UDim2.fromOffset(30, 48), Gui.LAPIZ))
	local fondoRuta, r = Gui.barra(billete, UDim2.new(1, -140, 0, 14), UDim2.fromOffset(30, 72), Gui.TURQUESA)
	relleno = r
	avionRuta = Gui.icono(fondoRuta, "Avion", UDim2.fromOffset(32, 32), UDim2.fromScale(0, 0.5), Vector2.new(0.5, 0.5))
	avionRuta.ZIndex = 3
	relojCuenta = Gui.icono(billete, "Reloj", UDim2.fromOffset(30, 30), UDim2.new(1, -41, 0, 16), Vector2.new(0.5, 0))
	textoCuenta = Gui.texto(billete, "", UDim2.fromOffset(62, 32), UDim2.new(1, -41, 0, 50), Gui.NARANJA, true)
	textoCuenta.AnchorPoint = Vector2.new(0.5, 0)

	local etiquetaEstado = Gui.panel(raiz, "Etiqueta", UDim2.fromOffset(256, 172), UDim2.new(1, -12, 0, 10), Vector2.new(1, 0))
	etiquetaEstado.Rotation = 2.5
	for k, f in FILAS_ESTADO do
		local y = 16 + (k - 1) * 27
		local icono = Gui.icono(etiquetaEstado, f.icono, UDim2.fromOffset(26, 26), UDim2.fromOffset(64, y))
		Gui.texto(etiquetaEstado, f.letra, UDim2.fromOffset(16, 24), UDim2.fromOffset(92, y + 1), Gui.TINTA, true)
		local _, barra = Gui.barra(etiquetaEstado, UDim2.fromOffset(92, 16), UDim2.fromOffset(110, y + 5), Gui.VERDE)
		local pct = Gui.texto(etiquetaEstado, "", UDim2.fromOffset(42, 24), UDim2.fromOffset(204, y + 1), Gui.TINTA, false, 21)
		medidores[f.clave] = { relleno = barra, texto = pct, icono = icono }
	end
	iconoCinturones = Gui.icono(etiquetaEstado, "Cinturon", UDim2.fromOffset(26, 26), UDim2.fromOffset(64, 124))
	textoCinturones = izquierda(Gui.texto(etiquetaEstado, "", UDim2.fromOffset(150, 24), UDim2.fromOffset(96, 125), Gui.TINTA, false, 21))

	Gui.panel(raiz, "Mira", UDim2.fromOffset(26, 26), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5))
	pista = Gui.texto(raiz, "", UDim2.fromOffset(560, 30), UDim2.new(0.5, 0, 0.5, 24), Gui.PAPEL, false, 24)
	pista.AnchorPoint = Vector2.new(0.5, 0)
	Gui.trazado(pista)

	listaAvisos = Instance.new("Frame")
	listaAvisos.BackgroundTransparency = 1
	listaAvisos.Size = UDim2.fromOffset(600, 300)
	listaAvisos.Position = UDim2.new(0.5, 0, 0, 118)
	listaAvisos.AnchorPoint = Vector2.new(0.5, 0)
	listaAvisos.Parent = raiz
	Gui.lista(listaAvisos, 2).HorizontalAlignment = Enum.HorizontalAlignment.Center

	panelPiloto = Gui.panel(raiz, "Pizarra", UDim2.fromOffset(370, 250), UDim2.new(0, 12, 1, -12), Vector2.new(0, 1))
	panelPiloto.Visible = false
	Gui.icono(panelPiloto, "Volante", UDim2.fromOffset(34, 34), UDim2.fromOffset(20, 14))
	izquierda(Gui.texto(panelPiloto, "CABINA", UDim2.fromOffset(200, 32), UDim2.fromOffset(62, 16), Gui.TIZA, true))
	datosPiloto = izquierda(Gui.texto(panelPiloto, "", UDim2.new(1, -44, 0, 104), UDim2.fromOffset(22, 52), Gui.TIZA, false, 21))
	datosPiloto.TextYAlignment = Enum.TextYAlignment.Top
	local _, gas = Gui.barra(panelPiloto, UDim2.new(1, -44, 0, 16), UDim2.fromOffset(22, 160), Gui.NARANJA)
	barraGas = gas
	avisoPiloto = izquierda(Gui.texto(panelPiloto, "", UDim2.new(1, -44, 0, 40), UDim2.fromOffset(22, 180), Gui.AMARILLO, false, 19))
	avisoPiloto.TextYAlignment = Enum.TextYAlignment.Top
	local controles = izquierda(Gui.texto(panelPiloto, "W/S subir y bajar · A/D girar · Shift/Ctrl gases · Espacio salir", UDim2.new(1, -44, 0, 20), UDim2.new(0, 22, 1, -30), Gui.TIZA, false, 16))
	controles.TextTransparency = 0.35

	panelResultados = Gui.panel(raiz, "Papel", UDim2.fromOffset(580, 520), UDim2.fromScale(0.5, 0.52), Vector2.new(0.5, 0.5))
	panelResultados.Rotation = -1.2
	panelResultados.Visible = false
	tituloResultados = izquierda(Gui.texto(panelResultados, "", UDim2.new(1, -210, 0, 46), UDim2.fromOffset(34, 26), Gui.TINTA, true))
	selloResultados = Gui.panel(panelResultados, "Sello", UDim2.fromOffset(150, 150), UDim2.new(1, -96, 0, 4), Vector2.new(0.5, 0))
	selloResultados.Rotation = 14
	selloResultados.ImageTransparency = 0.08
	textoSello = Gui.texto(selloResultados, "", UDim2.fromScale(0.7, 0.24), UDim2.fromScale(0.5, 0.5), Gui.VERDE, true)
	textoSello.AnchorPoint = Vector2.new(0.5, 0.5)
	filasResultados = Instance.new("Frame")
	filasResultados.BackgroundTransparency = 1
	filasResultados.Size = UDim2.new(1, -68, 1, -110)
	filasResultados.Position = UDim2.fromOffset(34, 84)
	filasResultados.Parent = panelResultados
	Gui.lista(filasResultados, 3)

	ayuda = Gui.panel(raiz, "Papel", UDim2.fromOffset(470, 476), UDim2.new(1, -12, 1, -12), Vector2.new(1, 1))
	ayuda.Rotation = 1.2
	ayuda.Visible = false
	izquierda(Gui.texto(ayuda, "CONTROLES", UDim2.fromOffset(220, 36), UDim2.fromOffset(30, 22), Gui.TINTA, true))
	izquierda(Gui.texto(ayuda, "H para cerrar", UDim2.fromOffset(150, 22), UDim2.new(1, -170, 0, 32), Gui.LAPIZ, false, 19))
	local lineasAyuda = Instance.new("Frame")
	lineasAyuda.BackgroundTransparency = 1
	lineasAyuda.Size = UDim2.new(1, -60, 1, -90)
	lineasAyuda.Position = UDim2.fromOffset(30, 66)
	lineasAyuda.Parent = ayuda
	Gui.lista(lineasAyuda, 4)
	for i, l in LINEAS_AYUDA do
		Gui.fila(lineasAyuda, l[1], l[2] :: string, 26, Gui.TINTA, i)
	end

	local indicacion = Gui.texto(raiz, "H controles · M música", UDim2.fromOffset(220, 24), UDim2.new(1, -14, 1, -10), Gui.PAPEL, false, 20)
	indicacion.AnchorPoint = Vector2.new(1, 1)
	indicacion.TextXAlignment = Enum.TextXAlignment.Right
	Gui.trazado(indicacion)
	local function indicar()
		indicacion.Visible = not ayuda.Visible and not panelPiloto.Visible
	end
	ayuda:GetPropertyChangedSignal("Visible"):Connect(indicar)
	panelPiloto:GetPropertyChangedSignal("Visible"):Connect(indicar)
end

local function aviso(contenido: string, tipo: string)
	Sonido.reproducir(if tipo == "peligro" then "UiPeligro" elseif tipo == "bien" then "Reparado" else "UiAviso", nil, if tipo == "bien" then 0.5 else 0.8, 1)
	local nota = Gui.panel(listaAvisos, if tipo == "peligro" then "NotaPeligro" elseif tipo == "bien" then "NotaBien" else "NotaInfo", UDim2.fromOffset(580, 68), UDim2.new())
	nota.LayoutOrder = math.floor(os.clock() * 100)
	nota.Rotation = math.random(-14, 14) / 10
	local icono = Gui.icono(nota, if tipo == "peligro" then "Peligro" elseif tipo == "bien" then "Tick" else "Info", UDim2.fromOffset(32, 32), UDim2.fromOffset(5, 17))
	local t = izquierda(Gui.texto(nota, contenido, UDim2.new(1, -62, 0, 42), UDim2.fromOffset(46, 12), Gui.TINTA))
	local limite = Instance.new("UITextSizeConstraint")
	limite.MaxTextSize = 29
	limite.Parent = t
	local notas = {}
	for _, h in listaAvisos:GetChildren() do
		if h:IsA("ImageLabel") then
			table.insert(notas, h)
		end
	end
	if #notas > 4 then
		table.sort(notas, function(a, b)
			return a.LayoutOrder < b.LayoutOrder
		end)
		notas[1]:Destroy()
	end
	task.delay(4.5, function()
		if nota.Parent then
			local info = TweenInfo.new(0.5)
			TweenService:Create(nota, info, { ImageTransparency = 1 }):Play()
			TweenService:Create(icono, info, { ImageTransparency = 1 }):Play()
			TweenService:Create(t, info, { TextTransparency = 1 }):Play()
			task.wait(0.5)
			nota:Destroy()
		end
	end)
end

local NOMBRES_FASE = {
	Aeropuerto = "AEROPUERTO · Elegid vuelo",
	Embarque = "EMBARQUE · ¡Subid al avión!",
	Despegue = "DESPEGUE",
	Vuelo = "EN VUELO",
	Aproximacion = "APROXIMACIÓN · ¡A aterrizar!",
	Frenando = "FRENANDO",
	Aterrizado = "EN TIERRA",
	Estrellado = "¡ESTRELLADOS!",
}

local function decodificarContrato()
	local json = Estado:GetAttribute("Contrato")
	if typeof(json) ~= "string" then
		contratoCache = nil
		return
	end
	local ok, datos = pcall(HttpService.JSONDecode, HttpService, json)
	contratoCache = if ok and typeof(datos) == "table" then datos else nil
end

local function actualizarBarra()
	local faseJuego = Estado:GetAttribute("Fase")
	local faseAvion = avion:GetAttribute("Fase")
	local clave = if faseJuego == "Aeropuerto" or faseJuego == "Embarque" then faseJuego else faseAvion
	textoFase.Text = NOMBRES_FASE[if typeof(clave) == "string" then clave else ""] or ""
	local contrato = contratoCache
	local progreso = 0
	if faseJuego == "Aeropuerto" then
		local ciudad = Estado:GetAttribute("Ciudad")
		textoRuta.Text = `Estás en {if typeof(ciudad) == "string" then ciudad else "?"} · entrad en la puerta de vuestro vuelo`
	elseif contrato then
		local total, recorrido = numero("Total"), numero("Distancia")
		textoRuta.Text = `{contrato.origen} → {contrato.destino} · quedan {math.max(0, math.floor(total - recorrido))} km`
		progreso = math.clamp(recorrido / math.max(total, 1), 0, 1)
		if avion:GetAttribute("ZonaEntrega") then
			textoRuta.Text ..= " · ¡ZONA DE ENTREGA!"
		end
	end
	Gui.llenar(relleno, progreso)
	avionRuta.Position = UDim2.fromScale(progreso, 0.5)
	local cuenta = Estado:GetAttribute("Cuenta")
	local hayCuenta = typeof(cuenta) == "number" and cuenta > 0 and (faseJuego == "Embarque" or faseJuego == "Aeropuerto")
	textoCuenta.Text = if hayCuenta then tostring(cuenta) else ""
	relojCuenta.Visible = hayCuenta
end

local function actualizarEstado()
	for _, f in FILAS_ESTADO do
		local m = medidores[f.clave]
		local valor = numero(f.clave)
		Gui.llenar(m.relleno, valor / 100, colorNivel(valor / 100))
		m.texto.Text = `{math.floor(valor)}%`
		if f.icono == "Motor" then
			Gui.ponerIcono(m.icono, if avion:GetAttribute(f.clave .. "Fuego") then "Fuego" else "Motor")
		end
	end
	local puestos = avion:GetAttribute("Cinturones") == true
	textoCinturones.Text = if puestos then "Cinturones <b>ON</b>" else "Cinturones <b>OFF</b>"
	textoCinturones.TextColor3 = if puestos then Gui.TINTA else Gui.ROJO
	iconoCinturones.ImageTransparency = if puestos then 0 else 0.45
end

local function actualizarPiloto()
	local visible = Piloto.activo()
	panelPiloto.Visible = visible
	if not visible then
		return
	end
	local desvio = numero("Desvio")
	local rumbo = if desvio > 4 then "← gira a la IZQUIERDA (A)" elseif desvio < -4 then "gira a la DERECHA (D) →" else "rumbo correcto"
	datosPiloto.Text = table.concat({
		`ALTITUD <b>{numero("Altitud")}</b> m  ({numero("Vertical")} m/s)`,
		`VELOCIDAD <b>{numero("Velocidad")}</b> km/h`,
		`RUMBO {rumbo}`,
		`AUTOPILOTO {if avion:GetAttribute("Autopiloto") then "<font color=\"#6DBE45\"><b>ON</b></font>" else "OFF"} · GASES {numero("Gases")}%`,
	}, "\n")
	Gui.llenar(barraGas, numero("Gases") / 100)
	local fase = avion:GetAttribute("Fase")
	local mensaje = ""
	if avion:GetAttribute("Perdida") then
		mensaje = "¡PÉRDIDA! Acelera (Shift) y baja el morro (S)"
	elseif fase == "Despegue" then
		mensaje = `Acelera con Shift. A {Config.VUELO.VELOCIDAD_DESPEGUE} km/h pulsa W para despegar`
	elseif fase == "Aproximacion" then
		local restante = numero("Total") - numero("Distancia")
		mensaje = `Pista a {math.floor(restante)} km · baja a 0 m con menos de {Config.VUELO.VELOCIDAD_ATERRIZAJE} km/h y suave`
	elseif numero("Altitud") < 800 and fase == "Vuelo" then
		mensaje = "¡Muy bajo! Sube (W)"
	end
	avisoPiloto.Text = mensaje
end

local function actualizarPista()
	local objetivo = if Agarre.sostenido() then nil else Agarre.apuntado()
	if objetivo ~= ultimoApuntado then
		ultimoApuntado = objetivo
		resaltado.Adornee = objetivo
		resaltado.Enabled = objetivo ~= nil
	end
	local objeto = Agarre.sostenido()
	if objeto then
		local tipo = Agarre.tipo(objeto)
		local raciones = objeto:GetAttribute("Raciones")
		pista.Text = if tipo == "Extintor" or tipo == "Llave" then "F usar · Clic soltar · Clic der. lanzar" elseif tipo == "Agua" then "E servir · F echar al fuego · Clic der. lanzar" elseif tipo == "Bolso" then "Suéltalo junto a un altillo abierto para guardarlo" elseif tipo == "Piolet" then "F clavarte al casco · Espacio soltarte · F junto al panel: martillear" elseif typeof(raciones) == "number" then `{raciones} raciones · E servir · Clic soltar` else "Clic soltar · Clic der. lanzar"
		return
	end
	local apuntado = Agarre.apuntado()
	if apuntado then
		local tipo = Agarre.tipo(apuntado)
		local def = Config.OBJETOS[tipo]
		pista.Text = `Clic coger {if def then def.nombre elseif tipo == "Pasajero" then "pasajero" else string.lower(tipo)}`
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
	b.Size = UDim2.fromOffset(66, 84)
	b.StudsOffset = Vector3.new(0, 3.4, 0)
	b.MaxDistance = 60
	b.Adornee = cuerpo
	b.ResetOnSpawn = false
	local fondo = Gui.panel(b, "Burbuja", UDim2.fromOffset(64, 70), UDim2.fromOffset(1, 0))
	local icono = Gui.icono(fondo, nil, UDim2.fromScale(0.62, 0.56), UDim2.fromScale(0.5, 0.42), Vector2.new(0.5, 0.5))
	local fondoPaciencia, paciencia = Gui.barra(b, UDim2.fromOffset(56, 13), UDim2.fromOffset(5, 70), Gui.VERDE)
	b.Parent = etiquetasGui
	local emocion = ""
	local emocionHasta = 0
	local function refrescar()
		local pedido = modelo:GetAttribute("Pedido")
		local miedo = modelo:GetAttribute("Miedo")
		local p = modelo:GetAttribute("Paciencia")
		fondoPaciencia.Visible = false
		b.Enabled = true
		if typeof(pedido) == "string" and pedido ~= "" then
			Gui.ponerIcono(icono, Config.ICONOS[pedido] or pedido)
			local maximo = modelo:GetAttribute("PacienciaMax")
			local f = math.clamp((if typeof(p) == "number" then p else 0) / (if typeof(maximo) == "number" and maximo > 0 then maximo else Config.PASAJEROS.PACIENCIA), 0, 1)
			Gui.llenar(paciencia, f, colorNivel(f))
			fondoPaciencia.Visible = true
		elseif modelo:GetAttribute("Alborotador") == true then
			Gui.ponerIcono(icono, "Alborotador")
		elseif os.clock() < emocionHasta then
			Gui.ponerIcono(icono, emocion)
		elseif typeof(miedo) == "number" and miedo > 0.5 then
			Gui.ponerIcono(icono, Config.ICONOS.Miedo)
		else
			b.Enabled = false
		end
	end
	local function emocionar(nombre: string, duracion: number)
		emocion, emocionHasta = nombre, os.clock() + duracion
		refrescar()
		task.delay(duracion + 0.1, refrescar)
	end
	local conexiones = {
		modelo:GetAttributeChangedSignal("Pedido"):Connect(refrescar),
		modelo:GetAttributeChangedSignal("Paciencia"):Connect(refrescar),
		modelo:GetAttributeChangedSignal("Miedo"):Connect(refrescar),
		modelo:GetAttributeChangedSignal("Alborotador"):Connect(refrescar),
		modelo:GetAttributeChangedSignal("Feliz"):Connect(function()
			emocionar(Config.ICONOS.Feliz, 2)
		end),
		modelo:GetAttributeChangedSignal("Enfado"):Connect(function()
			emocionar(Config.ICONOS.Enfado, 2.5)
		end),
		modelo:GetAttributeChangedSignal("ReaccionMarca"):Connect(function()
			local r = modelo:GetAttribute("Reaccion")
			emocionar(if typeof(r) == "string" then Config.ICONOS[r] or "Golpe" else "Golpe", 1.8)
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

local function estadoCocodrilo(modelo: Instance)
	if not modelo:IsA("Model") then
		return
	end
	local cuerpo = modelo:WaitForChild("Cuerpo", 5)
	if not cuerpo or not cuerpo:IsA("BasePart") then
		return
	end
	local b = Instance.new("BillboardGui")
	b.Name = "EstadoCocodrilo"
	b.Size = UDim2.fromOffset(54, 54)
	b.StudsOffset = Vector3.new(0, 2.4, 0)
	b.MaxDistance = 70
	b.Adornee = cuerpo
	b.ResetOnSpawn = false
	local icono = Gui.icono(b, "Enfado", UDim2.fromScale(1, 1), UDim2.new())
	b.Parent = etiquetasGui
	local function refrescar()
		local estado = modelo:GetAttribute("Estado")
		Gui.ponerIcono(icono, if estado == "Aturdido" then "Mareo" elseif estado == "Saciado" then "Saciado" else "Enfado")
	end
	local c = modelo:GetAttributeChangedSignal("Estado"):Connect(refrescar)
	refrescar()
	modelo.Destroying:Connect(function()
		c:Disconnect()
		b:Destroy()
	end)
end

local etiquetas: { [Player]: { gui: BillboardGui, voz: ImageLabel } } = {}

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
	b.Size = UDim2.fromOffset(220, 34)
	b.StudsOffset = Vector3.new(0, 2.6, 0)
	b.MaxDistance = 80
	b.Adornee = cabeza
	b.ResetOnSpawn = false
	local color = otro:GetAttribute("Color")
	local nombre = Gui.texto(b, otro.DisplayName, UDim2.new(1, -34, 1, 0), UDim2.fromOffset(34, 0), if typeof(color) == "Color3" then color else Gui.PAPEL, true)
	Gui.trazado(nombre)
	local voz = Gui.icono(b, "Altavoz", UDim2.fromOffset(30, 30), UDim2.fromOffset(0, 2))
	voz.Visible = false
	b.Parent = etiquetasGui
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

local NOMBRES_CARGA = { Maleta = "maletas", Caja = "cajas", CajaFragil = "frágiles", Jaula = "cocodrilo" }

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
	local cabecera = Instance.new("TextLabel")
	cabecera.BackgroundTransparency = 1
	cabecera.Size = UDim2.new(1, -40, 0, 50)
	cabecera.Position = UDim2.fromOffset(20, 10)
	cabecera.Font = FUENTE_TABLERO
	cabecera.TextScaled = true
	cabecera.TextColor3 = CREMA
	cabecera.Text = "SALIDAS · ENTRAD EN LA PUERTA DE VUESTRO VUELO"
	cabecera.Parent = tableroGui
	for i, o in ofertas :: { any } do
		local columna = Instance.new("Frame")
		columna.Size = UDim2.new(1 / 3, -20, 1, -90)
		columna.Position = UDim2.new((i - 1) / 3, 10, 0, 74)
		columna.BackgroundColor3 = Color3.fromRGB(40, 40, 48)
		columna.BorderSizePixel = 0
		columna.Parent = tableroGui
		local esquina = Instance.new("UICorner")
		esquina.CornerRadius = UDim.new(0, 16)
		esquina.Parent = columna
		local borde = Instance.new("UIStroke")
		borde.Color = colores[i] or CREMA
		borde.Thickness = 4
		borde.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
		borde.Parent = columna
		local carga = {}
		for _, c in o.carga do
			table.insert(carga, `{c.cantidad} {NOMBRES_CARGA[c.tipo] or "bultos"}`)
		end
		local estimado = o.pasajeros * o.pagoPasajero
		for _, c in o.carga do
			estimado += c.valor * c.cantidad
		end
		local lineas = {
			`<font size="60" color="#{(colores[i] or CREMA):ToHex()}">{i}</font>`,
			`<b>{o.titulo}</b>`,
			`{o.origen} → {o.destino}`,
			`{o.distancia} km · {o.pasajeros} pasajeros`,
			table.concat(carga, " · "),
			`Riesgo {riesgo(o.riesgo)} · Pago ~{estimado}`,
		}
		if o.entregaAerea then
			table.insert(lineas, "Incluye entrega aérea")
		end
		if typeof(o.condicion) == "string" and Contratos.CONDICIONES[o.condicion] and o.condicion ~= "Normal" then
			table.insert(lineas, Contratos.CONDICIONES[o.condicion].texto)
		end
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1
		t.Size = UDim2.new(1, -20, 1, -20)
		t.Position = UDim2.fromOffset(10, 10)
		t.Font = FUENTE_TABLERO
		t.TextSize = 22
		t.TextColor3 = CREMA
		t.RichText = true
		t.TextWrapped = true
		t.TextYAlignment = Enum.TextYAlignment.Top
		t.Text = table.concat(lineas, "\n")
		t.Parent = columna
	end
	tableroGui.Parent = jugador:WaitForChild("PlayerGui")
end

local function resultados(datos: any)
	if typeof(datos) ~= "table" then
		return
	end
	Sonido.reproducir(if datos.tipo == "Estrellado" then "Derrota" else "Victoria", nil, 1, 1)
	if typeof(datos.total) == "number" and datos.total > 0 then
		task.delay(1.2, Sonido.reproducir, "Caja", nil, 1, 1)
	end
	local estrellado = datos.tipo == "Estrellado"
	local perfecto = datos.aterrizaje == "Perfecto"
	tituloResultados.Text = if estrellado then "¡ESTRELLADOS!" elseif perfecto then "¡ATERRIZAJE PERFECTO!" else "¡VUELO COMPLETADO!"
	local colorSello = if estrellado then Gui.ROJO elseif perfecto then Gui.AMARILLO else Gui.VERDE
	selloResultados.ImageColor3 = colorSello
	textoSello.TextColor3 = colorSello
	textoSello.Text = if estrellado then "FALLIDO" elseif perfecto then "PERFECTO" else "PAGADO"
	for _, h in filasResultados:GetChildren() do
		if h:IsA("Frame") then
			h:Destroy()
		end
	end
	local orden = 0
	local function linea(icono: string?, contenido: string, alto: number?)
		orden += 1
		Gui.fila(filasResultados, icono, contenido, alto or 26, Gui.TINTA, orden)
	end
	linea(if estrellado then "Peligro" else "Aterrizaje", if estrellado then `<b>{datos.motivo}</b>` else `Destino: <b>{datos.destino}</b>`)
	linea("Pasajero", `Pasajeros entregados: {datos.pasajeros}  (perdidos: {datos.perdidos})`)
	linea("Feliz", `Satisfacción media: {datos.satisfaccion}% · Servidos: {datos.servidos}`)
	linea("Maleta", `Carga intacta: +{datos.carga}`)
	linea("Paracaidas", `Entregas aéreas: +{datos.entregas}`)
	linea("Cocodrilo", `Cocodrilo: {if datos.cocodrilo == "" then "—" else datos.cocodrilo}`)
	linea("Casco", `Casco: {datos.casco}%`)
	if datos.billetes then
		linea("Billete", `Billetes: +{datos.billetes}`)
	end
	if typeof(datos.confiscados) == "number" and datos.confiscados > 0 then
		linea("Aduana", `Contrabando requisado: {datos.confiscados} (+{datos.confiscados * (if typeof(datos.bonusAduana) == "number" then datos.bonusAduana else 60)})`)
	end
	if typeof(datos.contrabando) == "number" and datos.contrabando > 0 and not estrellado then
		linea("Alarma", `Multa de aduanas: {datos.contrabando} maletas (-{datos.contrabando * (if typeof(datos.multaAduana) == "number" then datos.multaAduana else 150)})`)
	end
	if datos.piratas and datos.piratas > 0 then
		linea("Pirata", `Piratas derribados: +{datos.piratas}`)
	end
	if datos.bonus and datos.bonus > 0 then
		linea("Estrella", `Bonus de aterrizaje: +{datos.bonus}`)
	end
	if typeof(datos.premios) == "table" then
		for _, p in datos.premios :: { any } do
			if typeof(p) == "table" and typeof(p.titulo) == "string" and typeof(p.nombre) == "string" then
				linea(if typeof(p.icono) == "string" then p.icono else "Medalla", `{p.titulo}: <b>{p.nombre}</b>`, 24)
			end
		end
	end
	linea("Moneda", `<b>TOTAL {datos.total}</b> · para cada uno {datos.porJugador}`, 34)
	local alto = 0
	for _, h in filasResultados:GetChildren() do
		if h:IsA("Frame") then
			alto += h.Size.Y.Offset + 3
		end
	end
	panelResultados.Size = UDim2.fromOffset(580, math.clamp(alto + 130, 360, 700))
	panelResultados.Visible = true
	task.delay(Config.PARTIDA.RESULTADOS - 0.5, function()
		panelResultados.Visible = false
	end)
end

local function boton(padre: Instance, contenido: string, tamano: UDim2, posicion: UDim2, color: Color3, accion: () -> ()): ImageButton
	local b = Gui.panel(padre, "Boton", tamano, posicion, nil, true) :: any
	b.ImageColor3 = color
	local t = Gui.texto(b, contenido, UDim2.new(1, -16, 1, -12), UDim2.fromOffset(8, 4), Gui.PAPEL, true)
	Gui.trazado(t)
	local limite = Instance.new("UITextSizeConstraint")
	limite.MaxTextSize = 22
	limite.Parent = t
	b.Activated:Connect(function()
		Sonido.reproducir("UiClick", nil, 0.7, 1)
		accion()
	end)
	return b
end

local function dibujarTienda()
	local panel = panelTienda
	local e = estadoTienda
	if not panel or not e then
		return
	end
	local contenido = panel:FindFirstChild("Contenido")
	if contenido then
		contenido:Destroy()
	end
	local c = Instance.new("Frame")
	c.Name = "Contenido"
	c.BackgroundTransparency = 1
	c.Size = UDim2.new(1, -60, 1, -110)
	c.Position = UDim2.fromOffset(30, 84)
	c.Parent = panel
	local dinero = if typeof(e.dinero) == "number" then e.dinero else 0
	local gorros = if typeof(e.gorros) == "table" then e.gorros else {}
	local mejoras = if typeof(e.mejoras) == "table" then e.mejoras else {}
	local puesto = if typeof(e.gorro) == "string" then e.gorro else ""
	local cabecera = panel:FindFirstChild("Dinero")
	if cabecera and cabecera:IsA("TextLabel") then
		cabecera.Text = tostring(dinero)
	end
	local columnaGorros = Instance.new("Frame")
	columnaGorros.BackgroundTransparency = 1
	columnaGorros.Size = UDim2.new(0.5, -10, 1, 0)
	columnaGorros.Parent = c
	local columnaMejoras = columnaGorros:Clone()
	columnaMejoras.Position = UDim2.new(0.5, 10, 0, 0)
	columnaMejoras.Parent = c
	Gui.fila(columnaGorros, "Gorro", "<b>GORROS</b>", 28, Gui.TURQUESA)
	Gui.fila(columnaMejoras, "Flecha", "<b>MEJORAS DEL AVIÓN</b>", 28, Gui.NARANJA)
	local disponibles: { Config.Gorro } = {}
	for _, g in Config.TIENDA.GORROS do
		if Visuales.IDS[g.nombre] then
			table.insert(disponibles, g)
		end
	end
	if #disponibles == 0 then
		izquierda(Gui.texto(columnaGorros, "Próximamente", UDim2.new(1, 0, 0, 30), UDim2.fromOffset(0, 38), Gui.LAPIZ, false, 20))
	end
	for i, g in disponibles do
		local y = 36 + (i - 1) * 50
		izquierda(Gui.texto(columnaGorros, g.titulo, UDim2.new(0.58, -6, 0, 40), UDim2.fromOffset(0, y), Gui.TINTA, false, 21))
		local tiene = gorros[g.nombre] == true
		local activo = puesto == g.nombre
		local color = if activo then Gui.ROJO elseif tiene then Gui.TURQUESA elseif dinero >= g.precio then Gui.VERDE else Color3.fromRGB(150, 140, 130)
		local b = boton(columnaGorros, if activo then "Quitar" elseif tiene then "Ponértelo" else tostring(g.precio), UDim2.new(0.42, 0, 0, 44), UDim2.new(0.58, 0, 0, y - 2), color, function()
			RemotoTienda:FireServer(if activo then "quitar" else "gorro", g.nombre)
		end)
		if not tiene and not activo then
			Gui.icono(b, "Moneda", UDim2.fromOffset(26, 26), UDim2.new(0, 10, 0.5, -2), Vector2.new(0, 0.5))
		end
	end
	for i, m in Config.TIENDA.MEJORAS do
		local nivel = if typeof(mejoras[m.nombre]) == "number" then mejoras[m.nombre] else 0
		local precio = m.precios[nivel + 1]
		local y = 36 + (i - 1) * 84
		izquierda(Gui.texto(columnaMejoras, `<b>{m.titulo}</b>  ({nivel}/{#m.precios})`, UDim2.new(0.6, -6, 0, 26), UDim2.fromOffset(0, y), Gui.TINTA, false, 21))
		local d = izquierda(Gui.texto(columnaMejoras, m.descripcion, UDim2.new(0.6, -6, 0, 44), UDim2.fromOffset(0, y + 26), Gui.LAPIZ, false, 17))
		d.TextYAlignment = Enum.TextYAlignment.Top
		if precio then
			local b = boton(columnaMejoras, tostring(precio), UDim2.new(0.4, 0, 0, 44), UDim2.new(0.6, 0, 0, y + 10), if dinero >= precio then Gui.VERDE else Color3.fromRGB(150, 140, 130), function()
				RemotoTienda:FireServer("mejora", m.nombre)
			end)
			Gui.icono(b, "Moneda", UDim2.fromOffset(26, 26), UDim2.new(0, 10, 0.5, -2), Vector2.new(0, 0.5))
		else
			local maximo = Gui.fila(columnaMejoras, "Tick", "Máximo", 30, Gui.VERDE)
			maximo.Position = UDim2.new(0.6, 0, 0, y + 14)
			maximo.Size = UDim2.new(0.4, 0, 0, 30)
		end
	end
	local nota = izquierda(Gui.texto(columnaMejoras, "Las mejoras se aplican si alguien de la tripulación las tiene.", UDim2.new(1, 0, 0, 40), UDim2.fromOffset(0, 36 + #Config.TIENDA.MEJORAS * 84), Gui.LAPIZ, false, 17))
	nota.TextYAlignment = Enum.TextYAlignment.Top
end

local function abrirTienda(abrir: any, datos: any)
	if typeof(datos) == "table" then
		estadoTienda = datos
	end
	if abrir == true and not panelTienda then
		local panel = Gui.panel(raiz, "Papel", UDim2.fromOffset(800, 500), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5))
		panel.Name = "Tienda"
		panel.Rotation = -0.8
		izquierda(Gui.texto(panel, "TIENDA DE LA TRIPULACIÓN", UDim2.new(1, -260, 0, 40), UDim2.fromOffset(32, 26), Gui.TINTA, true))
		Gui.icono(panel, "Moneda", UDim2.fromOffset(34, 34), UDim2.new(1, -196, 0, 28))
		local dinero = izquierda(Gui.texto(panel, "", UDim2.fromOffset(100, 36), UDim2.new(1, -156, 0, 28), Gui.NARANJA, true))
		dinero.Name = "Dinero"
		local cerrar = Gui.icono(panel, "Cerrar", UDim2.fromOffset(42, 42), UDim2.new(1, -58, 0, 22))
		local zona = Instance.new("TextButton")
		zona.BackgroundTransparency = 1
		zona.Text = ""
		zona.Size = UDim2.fromScale(1, 1)
		zona.Modal = true
		zona.Parent = cerrar
		zona.Activated:Connect(function()
			Sonido.reproducir("UiClick", nil, 0.7, 1)
			local p = panelTienda
			if p then
				p.Visible = false
			end
		end)
		panelTienda = panel
	end
	local p = panelTienda
	if abrir == true and p then
		p.Visible = true
	end
	dibujarTienda()
end

function Interfaz.iniciar()
	Gui.precargar()
	construir()
	resaltado = Instance.new("Highlight")
	resaltado.Name = "Apuntado"
	resaltado.FillTransparency = 1
	resaltado.OutlineColor = Color3.new(1, 1, 1)
	resaltado.OutlineTransparency = 0.15
	resaltado.DepthMode = Enum.HighlightDepthMode.Occluded
	resaltado.Enabled = false
	resaltado.Parent = Workspace.CurrentCamera
	RemotoAviso.OnClientEvent:Connect(function(contenido, tipo)
		if typeof(contenido) == "string" then
			aviso(contenido, if typeof(tipo) == "string" then tipo else "info")
		end
	end)
	RemotoResultados.OnClientEvent:Connect(resultados)
	RemotoTienda.OnClientEvent:Connect(abrirTienda)
	for _, modelo in CollectionService:GetTagged("Pasajero") do
		task.spawn(burbuja, modelo)
	end
	CollectionService:GetInstanceAddedSignal("Pasajero"):Connect(burbuja)
	for _, modelo in CollectionService:GetTagged("Cocodrilo") do
		task.spawn(estadoCocodrilo, modelo)
	end
	CollectionService:GetInstanceAddedSignal("Cocodrilo"):Connect(estadoCocodrilo)
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
	Estado:GetAttributeChangedSignal("Contrato"):Connect(decodificarContrato)
	decodificarContrato()
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
