--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Gui = require(ReplicatedStorage.Shared.Gui)

type Etiqueta = { gui: BillboardGui, aro: ImageLabel, icono: ImageLabel, nota: ImageLabel, texto: TextLabel, flecha: ImageLabel, conexiones: { RBXScriptConnection } }

local Preparacion = {}

local jugador = Players.LocalPlayer
local etiquetas: { [Instance]: Etiqueta } = {}
local flechas: { [BasePart]: number } = {}

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
end

return Preparacion
