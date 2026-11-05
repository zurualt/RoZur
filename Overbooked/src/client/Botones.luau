--!strict
local CollectionService = game:GetService("CollectionService")
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Gui = require(ReplicatedStorage.Shared.Gui)
local Camara = require(script.Parent.Camara)

local RemotoPulsar = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Pulsar") :: RemoteEvent

local Botones = {}

local jugador = Players.LocalPlayer
local ALCANCE = 8
local apuntado: BasePart? = nil
local carga: { parte: BasePart, inicio: number, duracion: number, alcance: number }? = nil
local resaltado: Highlight
local pista: ImageButton
local textoAccion: TextLabel
local textoObjeto: TextLabel
local barra: ImageLabel
local relleno: ImageLabel
local hundidos: { [BasePart]: boolean } = {}
local manos: any = nil
local parametros = RaycastParams.new()
parametros.FilterType = Enum.RaycastFilterType.Exclude

local function moduloManos(): any
	if manos == nil then
		local m = script.Parent:FindFirstChild("Manos")
		if m and m:IsA("ModuleScript") then
			local ok, r = pcall(require, m)
			manos = if ok then r else false
		else
			manos = false
		end
	end
	return if manos then manos else nil
end

local function botonDe(instancia: Instance?): BasePart?
	local actual = instancia
	while actual and actual ~= Workspace do
		if actual:IsA("BasePart") and CollectionService:HasTag(actual, "BotonMano") then
			return actual
		end
		actual = actual.Parent
	end
	return nil
end

local function buscar(): BasePart?
	local camara = Workspace.CurrentCamera
	local personaje = jugador.Character
	local cabeza = personaje and personaje:FindFirstChild("Head")
	if not personaje or not cabeza or not cabeza:IsA("BasePart") then
		return nil
	end
	parametros.FilterDescendantsInstances = { personaje }
	local origen = camara.CFrame.Position
	local largo = ALCANCE + (origen - cabeza.Position).Magnitude
	local direccion = camara.CFrame.LookVector * largo
	local r = Workspace:Raycast(origen, direccion, parametros)
	local b = botonDe(r and r.Instance)
	if b then
		return b
	end
	local s = Workspace:Spherecast(origen, 0.35, direccion, parametros)
	return botonDe(s and s.Instance)
end

local function hundir(parte: BasePart)
	if hundidos[parte] or not parte.Anchored then
		return
	end
	hundidos[parte] = true
	local eje = if parte:IsA("Part") and parte.Shape == Enum.PartType.Cylinder then parte.CFrame.RightVector else parte.CFrame.UpVector
	local haciaCamara = Workspace.CurrentCamera.CFrame.Position - parte.Position
	local hacia = if eje:Dot(haciaCamara) > 0 then -eje else eje
	local original = parte.CFrame
	local valor = Instance.new("CFrameValue")
	valor.Value = original
	valor.Changed:Connect(function(cf)
		parte.CFrame = cf
	end)
	local bajar = TweenService:Create(valor, TweenInfo.new(0.08, Enum.EasingStyle.Quad), { Value = original + hacia * 0.14 })
	local subir = TweenService:Create(valor, TweenInfo.new(0.22, Enum.EasingStyle.Back), { Value = original })
	bajar.Completed:Connect(function()
		subir:Play()
	end)
	subir.Completed:Connect(function()
		parte.CFrame = original
		valor:Destroy()
		hundidos[parte] = nil
	end)
	bajar:Play()
end

local function senalar()
	local m = moduloManos()
	if m and typeof(m.pulsar) == "function" then
		pcall(m.pulsar)
	end
end

local function apretar(parte: BasePart)
	Camara.alcanzar()
	senalar()
	hundir(parte)
	pista.Rotation = -5
	TweenService:Create(pista, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Rotation = 0 }):Play()
	RemotoPulsar:FireServer(parte)
end

local function empezar(parte: BasePart)
	local d = parte:GetAttribute("Duracion")
	local duracion = if typeof(d) == "number" then d else 0
	if duracion <= 0 then
		apretar(parte)
		return
	end
	carga = { parte = parte, inicio = os.clock(), duracion = duracion, alcance = 0 }
	Camara.alcanzar()
	senalar()
end

local function soltar()
	carga = nil
	Gui.llenar(relleno, 0)
end

local function texto(parte: BasePart, nombre: string): string
	local v = parte:GetAttribute(nombre)
	return if typeof(v) == "string" then v else ""
end

local function construir()
	local gui = Instance.new("ScreenGui")
	gui.Name = "BotonMano"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 5
	gui.Parent = jugador:WaitForChild("PlayerGui")
	pista = Gui.panel(gui, "Boton", UDim2.fromOffset(250, 66), UDim2.new(0.5, 34, 0.5, 26), nil, true) :: any
	pista.ImageColor3 = Gui.PAPEL
	pista.Visible = false
	local escala = Instance.new("UIScale")
	escala.Parent = pista
	local function ajustar()
		local v = Workspace.CurrentCamera.ViewportSize
		escala.Scale = math.clamp(math.min(v.X / 1366, v.Y / 768), 0.6, 1.1)
	end
	ajustar()
	Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(ajustar)
	local caja = Gui.panel(pista, "Boton", UDim2.fromOffset(46, 46), UDim2.fromOffset(8, 9))
	caja.ImageColor3 = Gui.AMARILLO
	Gui.icono(caja, "Mano", UDim2.new(1, -12, 1, -12), UDim2.fromOffset(6, 4))
	textoAccion = Gui.texto(pista, "", UDim2.new(1, -74, 0, 26), UDim2.fromOffset(62, 9), Gui.TINTA, true)
	textoAccion.TextXAlignment = Enum.TextXAlignment.Left
	textoObjeto = Gui.texto(pista, "", UDim2.new(1, -74, 0, 19), UDim2.fromOffset(62, 35), Gui.LAPIZ, false)
	textoObjeto.TextXAlignment = Enum.TextXAlignment.Left
	textoObjeto.TextTruncate = Enum.TextTruncate.AtEnd
	local fondo, r = Gui.barra(pista, UDim2.new(1, -74, 0, 8), UDim2.new(0, 62, 1, -14), Gui.NARANJA)
	barra = fondo
	relleno = r
	Gui.llenar(relleno, 0)
	pista.InputBegan:Connect(function(entrada)
		if entrada.UserInputType == Enum.UserInputType.Touch then
			local b = apuntado
			if b then
				empezar(b)
			end
		end
	end)
	pista.InputEnded:Connect(function(entrada)
		if entrada.UserInputType == Enum.UserInputType.Touch then
			soltar()
		end
	end)
	resaltado = Instance.new("Highlight")
	resaltado.FillColor = Gui.AMARILLO
	resaltado.FillTransparency = 0.65
	resaltado.OutlineColor = Gui.AMARILLO
	resaltado.OutlineTransparency = 0
	resaltado.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop
	resaltado.Enabled = false
	resaltado.Parent = Workspace.CurrentCamera
end

local function actualizar()
	local nuevo = buscar()
	if nuevo ~= apuntado then
		apuntado = nuevo
		if nuevo then
			local visual = nuevo:FindFirstChildOfClass("Model")
			resaltado.Adornee = visual or nuevo
			resaltado.Enabled = true
			pista.Visible = true
			pista.Active = UserInputService.TouchEnabled
			local d = nuevo:GetAttribute("Duracion")
			barra.Visible = typeof(d) == "number" and d > 0
		else
			resaltado.Enabled = false
			resaltado.Adornee = nil
			pista.Visible = false
		end
	end
	local b = apuntado
	if b then
		textoAccion.Text = texto(b, "Accion")
		textoObjeto.Text = texto(b, "Objeto")
	end
	local c = carga
	if c then
		if c.parte ~= apuntado then
			soltar()
			return
		end
		local f = (os.clock() - c.inicio) / c.duracion
		Gui.llenar(relleno, f)
		if os.clock() > c.alcance then
			c.alcance = os.clock() + 0.3
			Camara.alcanzar()
			senalar()
		end
		if f >= 1 then
			soltar()
			apretar(c.parte)
		end
	end
end

function Botones.iniciar()
	construir()
	RunService.RenderStepped:Connect(actualizar)
	ContextActionService:BindActionAtPriority("PulsarBoton", function(_, estado)
		local b = apuntado
		if not b then
			return Enum.ContextActionResult.Pass
		end
		if estado == Enum.UserInputState.Begin then
			empezar(b)
		elseif estado == Enum.UserInputState.End then
			soltar()
		end
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.UserInputType.MouseButton1, Enum.KeyCode.ButtonR2)
end

return Botones
