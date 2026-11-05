--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Gui = require(ReplicatedStorage.Shared.Gui)
local Sonido = require(script.Parent.Sonido)

local Estado = ReplicatedStorage:WaitForChild("Estado")

type Fila = { fila: Frame, marca: ImageLabel, texto: TextLabel, hecho: boolean }
type Etiqueta = { gui: BillboardGui, aro: ImageLabel, icono: ImageLabel, nota: ImageLabel, texto: TextLabel, flecha: ImageLabel, conexiones: { RBXScriptConnection } }

local Preparacion = {}

local jugador = Players.LocalPlayer
local panel: ImageLabel
local tarjeta: ImageLabel
local tarjetaIcono: ImageLabel
local tarjetaCifra: TextLabel
local tarjetaTexto: TextLabel
local tarjetaFondo: ImageLabel
local tarjetaBarra: ImageLabel
local filas: { [string]: Fila } = {}
local etiquetas: { [Instance]: Etiqueta } = {}
local flechas: { [BasePart]: number } = {}

local ORDEN = {
	{ clave = "maletas", icono = "Maleta" },
	{ clave = "animal", icono = "Cocodrilo" },
	{ clave = "combustible", icono = "Combustible" },
	{ clave = "conducir", icono = "Volante" },
	{ clave = "descargar", icono = "Avion" },
}

local function numero(nombre: string): number
	local v = Estado:GetAttribute(nombre)
	return if typeof(v) == "number" then v else 0
end

local function texto(nombre: string): string
	local v = Estado:GetAttribute(nombre)
	return if typeof(v) == "string" then v else ""
end

local function construir()
	local gui = Instance.new("ScreenGui")
	gui.Name = "Preparacion"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.Parent = jugador:WaitForChild("PlayerGui")
	panel = Gui.panel(gui, "Papel", UDim2.fromOffset(390, 70 + #ORDEN * 36), UDim2.fromOffset(14, 124))
	panel.Rotation = -1.2
	panel.Visible = false
	local titulo = Gui.texto(panel, "PREPARACIÓN", UDim2.new(1, -50, 0, 30), UDim2.fromOffset(26, 18), Gui.NARANJA, true)
	titulo.TextXAlignment = Enum.TextXAlignment.Left
	local cuerpo = Instance.new("Frame")
	cuerpo.BackgroundTransparency = 1
	cuerpo.Size = UDim2.new(1, -48, 1, -64)
	cuerpo.Position = UDim2.fromOffset(24, 54)
	cuerpo.Parent = panel
	Gui.lista(cuerpo, 6)
	for i, o in ORDEN do
		local f = Instance.new("Frame")
		f.BackgroundTransparency = 1
		f.Size = UDim2.new(1, 0, 0, 30)
		f.LayoutOrder = i
		f.Parent = cuerpo
		Gui.icono(f, "Casilla", UDim2.fromOffset(24, 24), UDim2.fromOffset(0, 3))
		local marca = Gui.icono(f, "Tick", UDim2.fromOffset(28, 28), UDim2.fromOffset(1, -3))
		Gui.icono(f, o.icono, UDim2.fromOffset(26, 26), UDim2.fromOffset(32, 2))
		local t = Gui.texto(f, "", UDim2.new(1, -66, 1, 0), UDim2.fromOffset(66, 0), Gui.TINTA, false, 21)
		t.TextXAlignment = Enum.TextXAlignment.Left
		t.TextTruncate = Enum.TextTruncate.AtEnd
		t.TextWrapped = false
		filas[o.clave] = { fila = f, marca = marca, texto = t, hecho = false }
	end

	tarjeta = Gui.panel(gui, "Papel", UDim2.fromOffset(560, 104), UDim2.fromScale(0.5, 0.76), Vector2.new(0.5, 0.5))
	tarjeta.Rotation = 0.8
	tarjeta.Visible = false
	tarjetaIcono = Gui.icono(tarjeta, "Maleta", UDim2.fromOffset(62, 62), UDim2.new(0, 22, 0.5, 0), Vector2.new(0, 0.5))
	tarjetaCifra = Gui.texto(tarjeta, "", UDim2.fromOffset(140, 50), UDim2.fromOffset(92, 14), Gui.NARANJA, true)
	tarjetaCifra.TextXAlignment = Enum.TextXAlignment.Left
	tarjetaTexto = Gui.texto(tarjeta, "", UDim2.new(1, -250, 0, 50), UDim2.fromOffset(232, 14), Gui.TINTA, false, 22)
	tarjetaTexto.TextXAlignment = Enum.TextXAlignment.Left
	tarjetaTexto.TextYAlignment = Enum.TextYAlignment.Center
	local fondo, barra = Gui.barra(tarjeta, UDim2.new(1, -120, 0, 16), UDim2.fromOffset(94, 72), Gui.VERDE)
	tarjetaFondo, tarjetaBarra = fondo, barra
	local escalas = { Instance.new("UIScale"), Instance.new("UIScale") }
	escalas[1].Parent = panel
	escalas[2].Parent = tarjeta
	local function ajustar()
		local v = Workspace.CurrentCamera.ViewportSize
		local s = math.clamp(math.min(v.X / 1366, v.Y / 768), 0.55, 1.2)
		for _, e in escalas do
			e.Scale = s
		end
	end
	ajustar()
	Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(ajustar)
end

local function renglon(clave: string, visible: boolean, hecho: boolean, contenido: string)
	local f = filas[clave]
	f.fila.Visible = visible
	f.marca.Visible = hecho
	f.texto.Text = if hecho then `<s>{contenido}</s>` else contenido
	f.texto.TextColor3 = if hecho then Gui.LAPIZ else Gui.TINTA
	if hecho and not f.hecho and visible then
		Sonido.reproducir("UiClick", nil, 0.8, 1.2)
	end
	f.hecho = hecho
end

local function tarjetaCon(icono: string, cifra: string, contenido: string, fraccion: number?)
	Gui.ponerIcono(tarjetaIcono, icono)
	tarjetaCifra.Text = cifra
	tarjetaTexto.Text = contenido
	tarjetaFondo.Visible = fraccion ~= nil
	if fraccion then
		Gui.llenar(tarjetaBarra, fraccion, if fraccion >= 1 then Gui.VERDE else Gui.AMARILLO)
	end
end

local function actualizarPaneles()
	local paso = texto("PrepPaso")
	local activo = paso ~= ""
	panel.Visible = activo
	tarjeta.Visible = activo
	if not activo then
		return
	end
	local n, t = numero("PrepMaletas"), numero("PrepTotal")
	local animal = texto("PrepAnimal")
	local combustible = numero("PrepCombustible")
	local fuera = numero("PrepFuera")
	local maletasHechas = t > 0 and n >= t
	local animalHecho = animal == "Bodega" or animal == "Perdido"
	local lleno = combustible >= 100
	local tareas = paso == "Tareas"
	renglon("maletas", true, maletasHechas or not tareas, `Carga las maletas en el carro {n}/{t}`)
	renglon("animal", animal ~= "", animalHecho, if animal == "Perdido" then "El cocodrilo se ha perdido" elseif animalHecho then "Cocodrilo enjaulado y en la bodega" else "Mete al cocodrilo en su jaula")
	renglon("combustible", true, lleno, `Llena el depósito del avión {combustible}%`)
	renglon("conducir", true, paso == "Descargar", "Lleva el carro hasta el avión")
	renglon("descargar", not tareas, false, if paso == "Descargar" then `Mete las maletas en la bodega ({fuera})` else "Mete las maletas en la bodega")
	if tareas and not maletasHechas then
		tarjetaCon("Maleta", `{n}/{t}`, "maletas en el carro · cargadlas todas para abrir la puerta", if t > 0 then n / t else 0)
	elseif tareas and animal == "Suelto" then
		tarjetaCon("Cocodrilo", "¡GRRR!", "el cocodrilo sigue suelto · enjauladlo para abrir la puerta", nil)
	elseif tareas and not lleno then
		tarjetaCon("Combustible", `{combustible}%`, "depósito del avión · llenadlo para abrir la puerta", combustible / 100)
	elseif tareas then
		tarjetaCon("Tick", "¡LISTO!", "abriendo la puerta del hangar...", 1)
	elseif paso == "Conducir" then
		tarjetaCon("Volante", "¡EN MARCHA!", "seguid las flechas y llevad el carro hasta el avión", nil)
	else
		tarjetaCon("Maleta", tostring(fuera), "maletas fuera del avión · metedlas en la bodega", nil)
	end
end

local function refrescar(parte: Instance, e: Etiqueta)
	local icono = parte:GetAttribute("PrepIcono")
	local contenido = parte:GetAttribute("PrepTexto")
	local destino = parte:GetAttribute("PrepDestino") == true
	local portador = parte:GetAttribute("Portador")
	Gui.ponerIcono(e.icono, if typeof(icono) == "string" then icono else "Info")
	local t = if typeof(contenido) == "string" then contenido else ""
	e.texto.Text = t
	e.nota.Visible = t ~= ""
	e.nota.Size = UDim2.fromOffset(math.clamp(utf8.len(t) or #t, 3, 40) * 10 + 46, 40)
	e.aro.Visible = destino
	e.flecha.Visible = not destino
	e.gui.Enabled = not (typeof(portador) == "number" and portador ~= 0)
end

local function marcar(parte: Instance)
	if not parte:IsA("BasePart") or etiquetas[parte] then
		return
	end
	local b = Instance.new("BillboardGui")
	b.Name = "MarcaPrep"
	b.Adornee = parte
	b.AlwaysOnTop = true
	b.Size = UDim2.fromOffset(420, 130)
	b.StudsOffsetWorldSpace = Vector3.new(0, math.min(parte.Size.Y / 2, 3) + 3.2, 0)
	b.MaxDistance = 420
	b.ResetOnSpawn = false
	local aro = Gui.panel(b, "Sello", UDim2.fromOffset(74, 74), UDim2.new(0.5, 0, 0, 30), Vector2.new(0.5, 0.5))
	aro.ImageColor3 = Gui.AMARILLO
	local icono = Gui.icono(b, "Info", UDim2.fromOffset(50, 50), UDim2.new(0.5, 0, 0, 30), Vector2.new(0.5, 0.5))
	icono.ZIndex = 2
	local nota = Gui.panel(b, "NotaInfo", UDim2.fromOffset(120, 40), UDim2.new(0.5, 0, 0, 60), Vector2.new(0.5, 0))
	local t = Gui.texto(nota, "", UDim2.new(1, -20, 1, -10), UDim2.fromOffset(10, 5), Gui.TINTA, true)
	local limite = Instance.new("UITextSizeConstraint")
	limite.MaxTextSize = 24
	limite.Parent = t
	local flecha = Gui.icono(b, "Flecha", UDim2.fromOffset(26, 26), UDim2.new(0.5, 0, 0, 114), Vector2.new(0.5, 0.5))
	flecha.Rotation = 180
	local e: Etiqueta = { gui = b, aro = aro, icono = icono, nota = nota, texto = t, flecha = flecha, conexiones = {} }
	table.insert(e.conexiones, parte.AttributeChanged:Connect(function()
		refrescar(parte, e)
	end))
	refrescar(parte, e)
	b.Parent = jugador:WaitForChild("PlayerGui")
	etiquetas[parte] = e
end

local function desmarcar(parte: Instance)
	local e = etiquetas[parte]
	if e then
		for _, c in e.conexiones do
			c:Disconnect()
		end
		e.gui:Destroy()
		etiquetas[parte] = nil
	end
end

local function nuevaFlecha(parte: Instance)
	if parte:IsA("BasePart") then
		local orden = parte:GetAttribute("Orden")
		flechas[parte] = if typeof(orden) == "number" then orden else 0
	end
end

function Preparacion.iniciar()
	construir()
	for _, p in CollectionService:GetTagged("MarcaPrep") do
		marcar(p)
	end
	CollectionService:GetInstanceAddedSignal("MarcaPrep"):Connect(marcar)
	CollectionService:GetInstanceRemovedSignal("MarcaPrep"):Connect(desmarcar)
	for _, p in CollectionService:GetTagged("FlechaPrep") do
		nuevaFlecha(p)
	end
	CollectionService:GetInstanceAddedSignal("FlechaPrep"):Connect(nuevaFlecha)
	CollectionService:GetInstanceRemovedSignal("FlechaPrep"):Connect(function(p)
		flechas[p :: BasePart] = nil
	end)
	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		local ahora = os.clock()
		local salto = UDim2.new(0.5, 0, 0, 114 + math.sin(ahora * 7) * 6)
		for _, e in etiquetas do
			e.flecha.Position = salto
		end
		acumulado += dt
		if acumulado < 1 / 30 then
			return
		end
		acumulado = 0
		for parte, orden in flechas do
			local brillo = 0.5 + 0.5 * math.sin(ahora * 4.2 - orden * 0.9)
			local modificador = 0.6 * (1 - brillo) ^ 2
			parte.LocalTransparencyModifier = modificador
			for _, d in parte:GetDescendants() do
				if d:IsA("BasePart") then
					d.LocalTransparencyModifier = modificador
				end
			end
		end
	end)
	local function cambio()
		actualizarPaneles()
	end
	for _, nombre in { "PrepPaso", "PrepMaletas", "PrepTotal", "PrepAnimal", "PrepCombustible", "PrepFuera" } do
		Estado:GetAttributeChangedSignal(nombre):Connect(cambio)
	end
	actualizarPaneles()
end

return Preparacion
