--!strict
local ImagenesGui = require(script.Parent.ImagenesGui)

type Panel = { id: number, tam: { number }, corte: { number }, escala: number }

local Gui = {}

Gui.TITULO = Font.new("rbxasset://fonts/families/PermanentMarker.json")
Gui.CUERPO = Font.new("rbxasset://fonts/families/PatrickHand.json")
Gui.TINTA = Color3.fromRGB(42, 36, 32)
Gui.PAPEL = Color3.fromRGB(255, 244, 224)
Gui.TIZA = Color3.fromRGB(243, 231, 207)
Gui.LAPIZ = Color3.fromRGB(110, 98, 88)
Gui.NARANJA = Color3.fromRGB(242, 123, 43)
Gui.TURQUESA = Color3.fromRGB(31, 166, 160)
Gui.AMARILLO = Color3.fromRGB(246, 196, 69)
Gui.ROJO = Color3.fromRGB(217, 68, 58)
Gui.VERDE = Color3.fromRGB(109, 190, 69)

local paneles = ImagenesGui.Paneles :: { [string]: Panel }
local posiciones = ImagenesGui.Iconos.posiciones :: { [string]: { number } }

function Gui.panel(padre: Instance?, nombre: string, tamano: UDim2, posicion: UDim2, ancla: Vector2?, boton: boolean?): ImageLabel
	local p = paneles[nombre]
	local i = (if boton then Instance.new("ImageButton") else Instance.new("ImageLabel")) :: any
	i.Name = nombre
	i.BackgroundTransparency = 1
	i.Size = tamano
	i.Position = posicion
	i.AnchorPoint = ancla or Vector2.zero
	i.Image = `rbxassetid://{p.id}`
	local c, alto = p.corte, p.tam[2]
	if c[3] - c[1] > 4 then
		i.ScaleType = Enum.ScaleType.Slice
		i.SliceCenter = Rect.new(c[1], alto - c[4], c[3], alto - c[2])
		i.SliceScale = p.escala
	else
		i.ScaleType = Enum.ScaleType.Fit
	end
	i.Parent = padre
	return i
end

function Gui.ponerIcono(i: ImageLabel, nombre: string?)
	local pos = if nombre then posiciones[nombre] else nil
	i.Visible = pos ~= nil
	if pos then
		i.ImageRectOffset = Vector2.new(pos[1], pos[2])
	end
end

function Gui.icono(padre: Instance?, nombre: string?, tamano: UDim2, posicion: UDim2, ancla: Vector2?): ImageLabel
	local i = Instance.new("ImageLabel")
	i.Name = "Icono"
	i.BackgroundTransparency = 1
	i.Size = tamano
	i.Position = posicion
	i.AnchorPoint = ancla or Vector2.zero
	i.Image = `rbxassetid://{ImagenesGui.Iconos.id}`
	i.ImageRectSize = Vector2.new(ImagenesGui.Iconos.celda, ImagenesGui.Iconos.celda)
	i.ScaleType = Enum.ScaleType.Fit
	Gui.ponerIcono(i, nombre)
	i.Parent = padre
	return i
end

function Gui.texto(padre: Instance?, contenido: string, tamano: UDim2, posicion: UDim2, color: Color3, titulo: boolean?, altura: number?): TextLabel
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1
	t.Text = contenido
	t.Size = tamano
	t.Position = posicion
	t.TextColor3 = color
	t.FontFace = if titulo then Gui.TITULO else Gui.CUERPO
	t.TextScaled = altura == nil
	if altura then
		t.TextSize = altura
	end
	t.RichText = true
	t.TextWrapped = true
	t.Parent = padre
	return t
end

function Gui.trazado(t: TextLabel, color: Color3?)
	t.TextStrokeColor3 = color or Gui.TINTA
	t.TextStrokeTransparency = 0.15
end

function Gui.barra(padre: Instance?, tamano: UDim2, posicion: UDim2, color: Color3): (ImageLabel, ImageLabel)
	local fondo = Gui.panel(padre, "BarraFondo", tamano, posicion)
	local relleno = Gui.panel(fondo, "BarraRelleno", UDim2.fromScale(1, 1), UDim2.new())
	relleno.ImageColor3 = color
	return fondo, relleno
end

function Gui.llenar(relleno: ImageLabel, fraccion: number, color: Color3?)
	local f = math.clamp(fraccion, 0, 1)
	relleno.Visible = f > 0.02
	relleno.Size = UDim2.fromScale(f, 1)
	if color then
		relleno.ImageColor3 = color
	end
end

function Gui.fila(padre: Instance?, icono: string?, contenido: string, alto: number, color: Color3, orden: number?): Frame
	local f = Instance.new("Frame")
	f.BackgroundTransparency = 1
	f.Size = UDim2.new(1, 0, 0, alto)
	f.LayoutOrder = orden or 0
	local desplazado = if icono then alto + 6 else 0
	if icono then
		Gui.icono(f, icono, UDim2.fromOffset(alto, alto), UDim2.new())
	end
	local t = Gui.texto(f, contenido, UDim2.new(1, -desplazado, 1, 0), UDim2.fromOffset(desplazado, 0), color, false, math.floor(alto * 0.82))
	t.TextXAlignment = Enum.TextXAlignment.Left
	t.TextTruncate = Enum.TextTruncate.AtEnd
	t.TextWrapped = false
	f.Parent = padre
	return f
end

function Gui.precargar()
	local lista = { `rbxassetid://{ImagenesGui.Iconos.id}` }
	for _, p in paneles do
		table.insert(lista, `rbxassetid://{p.id}`)
	end
	task.spawn(function()
		pcall(function()
			game:GetService("ContentProvider"):PreloadAsync(lista)
		end)
	end)
end

function Gui.lista(padre: Instance, separacion: number)
	local l = Instance.new("UIListLayout")
	l.Padding = UDim.new(0, separacion)
	l.SortOrder = Enum.SortOrder.LayoutOrder
	l.Parent = padre
	return l
end

return Gui
