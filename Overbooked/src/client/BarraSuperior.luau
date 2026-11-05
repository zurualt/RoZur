--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Gui = require(ReplicatedStorage.Shared.Gui)
local ImagenesBarra = require(ReplicatedStorage.Shared.ImagenesBarra)
local Sonido = require(script.Parent.Sonido)

type Icono = { boton: ImageButton, imagen: ImageLabel, etiqueta: TextLabel, insignia: TextLabel, quiere: boolean }

local BarraSuperior = {}

local jugador = Players.LocalPlayer
local FONDO = Color3.fromRGB(18, 18, 21)
local ALTO = 44
local LADO = 40
local iconos: { [string]: Icono } = {}
local gui: ScreenGui
local pildora: Frame
local oculta = false

local function imagen(nombre: string): string
	local id = (ImagenesBarra :: { [string]: number })[nombre]
	return if id then `rbxassetid://{id}` else ""
end

local function pintarVisibles()
	local alguno = false
	for _, i in iconos do
		i.boton.Visible = i.quiere and not oculta
		alguno = alguno or i.boton.Visible
	end
	pildora.Visible = alguno
end

function BarraSuperior.agregar(clave: string, icono: string, texto: string, orden: number, alPulsar: () -> ()): ImageButton
	local b = Instance.new("ImageButton")
	b.Name = clave
	b.LayoutOrder = orden
	b.AutoButtonColor = false
	b.BackgroundColor3 = Color3.new(1, 1, 1)
	b.BackgroundTransparency = 1
	b.Size = UDim2.fromOffset(LADO, LADO)
	b.Image = ""
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(1, 0)
	esquina.Parent = b
	local img = Instance.new("ImageLabel")
	img.Name = "Icono"
	img.BackgroundTransparency = 1
	img.Image = imagen(icono)
	img.ScaleType = Enum.ScaleType.Fit
	img.Size = UDim2.fromOffset(24, 24)
	img.Position = UDim2.fromScale(0.5, 0.5)
	img.AnchorPoint = Vector2.new(0.5, 0.5)
	img.Parent = b
	local etiqueta = Gui.texto(b, texto, UDim2.fromOffset(0, 28), UDim2.new(0.5, 0, 1, 12), Gui.PAPEL, false, 18)
	etiqueta.AnchorPoint = Vector2.new(0.5, 0)
	etiqueta.TextWrapped = false
	etiqueta.FontFace = Font.new("rbxasset://fonts/families/GothamSSm.json", Enum.FontWeight.Medium)
	etiqueta.TextColor3 = Color3.new(1, 1, 1)
	etiqueta.BackgroundColor3 = FONDO
	etiqueta.BackgroundTransparency = 0.2
	etiqueta.AutomaticSize = Enum.AutomaticSize.X
	etiqueta.Visible = false
	etiqueta.ZIndex = 5
	local relleno = Instance.new("UIPadding")
	relleno.PaddingLeft = UDim.new(0, 10)
	relleno.PaddingRight = UDim.new(0, 10)
	relleno.Parent = etiqueta
	local esquinaEtiqueta = Instance.new("UICorner")
	esquinaEtiqueta.CornerRadius = UDim.new(0, 8)
	esquinaEtiqueta.Parent = etiqueta
	local insignia = Instance.new("TextLabel")
	insignia.BackgroundColor3 = Gui.NARANJA
	insignia.Size = UDim2.fromOffset(16, 16)
	insignia.Position = UDim2.new(1, -3, 0, 3)
	insignia.AnchorPoint = Vector2.new(1, 0)
	insignia.FontFace = Font.new("rbxasset://fonts/families/GothamSSm.json", Enum.FontWeight.Bold)
	insignia.TextColor3 = Color3.new(1, 1, 1)
	insignia.TextSize = 11
	insignia.Text = ""
	insignia.Visible = false
	insignia.ZIndex = 3
	insignia.Parent = b
	local esquinaInsignia = Instance.new("UICorner")
	esquinaInsignia.CornerRadius = UDim.new(1, 0)
	esquinaInsignia.Parent = insignia
	b.MouseEnter:Connect(function()
		b.BackgroundTransparency = 0.88
		etiqueta.Visible = not Gui.tactil()
	end)
	b.MouseLeave:Connect(function()
		b.BackgroundTransparency = 1
		etiqueta.Visible = false
	end)
	b.Activated:Connect(function()
		img.Size = UDim2.fromOffset(19, 19)
		TweenService:Create(img, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Size = UDim2.fromOffset(24, 24) }):Play()
		Sonido.reproducir("UiClick", nil, 0.5, 1.1)
		alPulsar()
	end)
	b.Parent = pildora
	iconos[clave] = { boton = b, imagen = img, etiqueta = etiqueta, insignia = insignia, quiere = true }
	pintarVisibles()
	return b
end

function BarraSuperior.mostrar(clave: string, visible: boolean)
	local i = iconos[clave]
	if i and i.quiere ~= visible then
		i.quiere = visible
		pintarVisibles()
	end
end

function BarraSuperior.cambiarIcono(clave: string, icono: string)
	local i = iconos[clave]
	if i then
		i.imagen.Image = imagen(icono)
	end
end

function BarraSuperior.insignia(clave: string, texto: string?)
	local i = iconos[clave]
	if i then
		i.insignia.Text = texto or ""
		i.insignia.Visible = texto ~= nil and texto ~= ""
	end
end

function BarraSuperior.activo(clave: string, activo: boolean)
	local i = iconos[clave]
	if i then
		i.imagen.ImageColor3 = if activo then Gui.NARANJA else Color3.new(1, 1, 1)
	end
end

function BarraSuperior.iniciar()
	gui = Instance.new("ScreenGui")
	gui.Name = "BarraSuperior"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 40
	gui.ScreenInsets = Enum.ScreenInsets.TopbarSafeInsets
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = jugador:WaitForChild("PlayerGui")
	pildora = Instance.new("Frame")
	pildora.Name = "Pildora"
	pildora.BackgroundColor3 = FONDO
	pildora.BackgroundTransparency = 0.3
	pildora.AutomaticSize = Enum.AutomaticSize.X
	pildora.Size = UDim2.fromOffset(0, ALTO)
	pildora.AnchorPoint = Vector2.new(0, 0.5)
	pildora.Position = UDim2.fromScale(0, 0.5)
	pildora.Parent = gui
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(1, 0)
	esquina.Parent = pildora
	local relleno = Instance.new("UIPadding")
	relleno.PaddingLeft = UDim.new(0, 4)
	relleno.PaddingRight = UDim.new(0, 4)
	relleno.Parent = pildora
	local orden = Instance.new("UIListLayout")
	orden.FillDirection = Enum.FillDirection.Horizontal
	orden.VerticalAlignment = Enum.VerticalAlignment.Center
	orden.SortOrder = Enum.SortOrder.LayoutOrder
	orden.Padding = UDim.new(0, 2)
	orden.Parent = pildora
	local playerGui = jugador:WaitForChild("PlayerGui")
	task.spawn(function()
		while gui.Parent do
			local intro = playerGui:FindFirstChild("Intro")
			local ahora = intro ~= nil and intro:IsA("ScreenGui") and intro.Enabled
			if ahora ~= oculta then
				oculta = ahora
				pintarVisibles()
			end
			task.wait(0.4)
		end
	end)
	UserInputService.LastInputTypeChanged:Connect(function()
		for _, i in iconos do
			i.etiqueta.Visible = false
		end
	end)
end

return BarraSuperior
