--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Gui = require(ReplicatedStorage.Shared.Gui)

local AgarreVista = {}

local jugador = Players.LocalPlayer
local PUNTOS = 28
local actual: Instance? = nil
local resaltado: Highlight
local pista: ImageButton
local escalaPista: UIScale
local caja: ImageLabel
local textoTecla: TextLabel
local iconoTecla: ImageLabel
local textoNombre: TextLabel
local puntos: { BasePart } = {}
local marca: BasePart
local alTocar: () -> () = function() end

local function tecla(): string
	if Gui.tactil() then
		return ""
	end
	local ultimo = UserInputService:GetLastInputType()
	return if string.sub(ultimo.Name, 1, 7) == "Gamepad" then "R2" else "Clic"
end

local function parteArco(forma: Enum.PartType, tamano: Vector3, color: Color3, padre: Instance): BasePart
	local p = Instance.new("Part")
	p.Shape = forma
	p.Size = tamano
	p.Color = color
	p.Material = Enum.Material.Neon
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Transparency = 1
	p.Parent = padre
	return p
end

local function construir()
	local gui = Instance.new("ScreenGui")
	gui.Name = "AgarrePista"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 5
	gui.Parent = jugador:WaitForChild("PlayerGui")
	pista = Gui.panel(gui, "Boton", UDim2.fromOffset(230, 58), UDim2.new(0.5, -30, 0.5, 24), Vector2.new(1, 0), true) :: any
	pista.ImageColor3 = Gui.PAPEL
	pista.Visible = false
	pista.Active = Gui.tactil()
	escalaPista = Instance.new("UIScale")
	escalaPista.Parent = pista
	caja = Gui.panel(pista, "Boton", UDim2.fromOffset(54, 42), UDim2.fromOffset(7, 8))
	caja.ImageColor3 = Gui.AMARILLO
	textoTecla = Gui.texto(caja, "", UDim2.new(1, -10, 1, -12), UDim2.fromOffset(5, 4), Gui.TINTA, true)
	iconoTecla = Gui.icono(caja, "Mano", UDim2.new(1, -14, 1, -12), UDim2.fromOffset(7, 4))
	local accion = Gui.texto(pista, "Coger", UDim2.new(1, -76, 0, 24), UDim2.fromOffset(68, 7), Gui.TINTA, true)
	accion.TextXAlignment = Enum.TextXAlignment.Left
	textoNombre = Gui.texto(pista, "", UDim2.new(1, -76, 0, 19), UDim2.fromOffset(68, 31), Gui.LAPIZ, false)
	textoNombre.TextXAlignment = Enum.TextXAlignment.Left
	textoNombre.TextTruncate = Enum.TextTruncate.AtEnd
	pista.Activated:Connect(function()
		alTocar()
	end)
	resaltado = Instance.new("Highlight")
	resaltado.Name = "AgarreApuntado"
	resaltado.FillColor = Gui.AMARILLO
	resaltado.FillTransparency = 0.8
	resaltado.OutlineColor = Gui.AMARILLO
	resaltado.OutlineTransparency = 0
	resaltado.DepthMode = Enum.HighlightDepthMode.Occluded
	resaltado.Enabled = false
	resaltado.Parent = Workspace.CurrentCamera
	local carpeta = Instance.new("Folder")
	carpeta.Name = "ArcoLanzamiento"
	carpeta.Parent = Workspace.CurrentCamera
	for i = 1, PUNTOS do
		local t = 0.26 - 0.12 * i / PUNTOS
		table.insert(puntos, parteArco(Enum.PartType.Ball, Vector3.one * t, Gui.AMARILLO, carpeta))
	end
	marca = parteArco(Enum.PartType.Cylinder, Vector3.new(0.08, 1.5, 1.5), Gui.NARANJA, carpeta)
end

function AgarreVista.apuntar(objeto: Instance?, nombre: string)
	if objeto == actual then
		return
	end
	actual = objeto
	resaltado.Adornee = objeto
	resaltado.Enabled = objeto ~= nil
	pista.Visible = objeto ~= nil
	if not objeto then
		return
	end
	textoNombre.Text = nombre
	local t = tecla()
	textoTecla.Text = t
	textoTecla.Visible = t ~= ""
	iconoTecla.Visible = t == ""
	local base = Gui.escala(0.6, 1.1)
	escalaPista.Scale = base * 0.8
	TweenService:Create(escalaPista, TweenInfo.new(0.18, Enum.EasingStyle.Back), { Scale = base }):Play()
end

function AgarreVista.arco(lista: { Vector3 }?, normal: Vector3?)
	for i, p in puntos do
		local q = if lista then lista[i] else nil
		if q then
			p.CFrame = CFrame.new(q)
			p.Transparency = 0.1 + 0.5 * i / PUNTOS
		else
			p.Transparency = 1
		end
	end
	local fin = if lista then lista[#lista] else nil
	if fin and normal then
		local lado = if math.abs(normal.Y) < 0.9 then Vector3.yAxis else Vector3.xAxis
		marca.CFrame = CFrame.fromMatrix(fin + normal * 0.05, normal, normal:Cross(lado).Unit)
		marca.Transparency = 0.25
	else
		marca.Transparency = 1
	end
end

function AgarreVista.aplastar(objeto: Instance)
	local visual = if objeto:IsA("BasePart") then objeto:FindFirstChildOfClass("Model") else nil
	if not visual then
		return
	end
	local partes: { BasePart } = {}
	local tamanos: { Vector3 } = {}
	for _, d in visual:GetDescendants() do
		if d:IsA("BasePart") then
			table.insert(partes, d)
			table.insert(tamanos, d.Size)
		end
	end
	if #partes == 0 or #partes > 12 then
		return
	end
	local valor = Instance.new("NumberValue")
	valor.Changed:Connect(function(k: number)
		local f = 1 - k
		local escala = Vector3.new(1 + 0.25 * f, 1 - 0.3 * f, 1 + 0.25 * f)
		for i, p in partes do
			if p.Parent then
				p.Size = tamanos[i] * escala
			end
		end
	end)
	local tween = TweenService:Create(valor, TweenInfo.new(0.32, Enum.EasingStyle.Back), { Value = 1 })
	tween.Completed:Connect(function()
		for i, p in partes do
			if p.Parent then
				p.Size = tamanos[i]
			end
		end
		valor:Destroy()
	end)
	tween:Play()
end

function AgarreVista.iniciar(tocar: () -> ())
	alTocar = tocar
	construir()
	RunService.RenderStepped:Connect(function()
		if actual then
			resaltado.FillTransparency = 0.8 + math.sin(os.clock() * 7) * 0.08
		end
	end)
end

return AgarreVista
