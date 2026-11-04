--!strict
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Gui = require(ReplicatedStorage.Shared.Gui)
local Camara = require(script.Parent.Camara)
local Sonido = require(script.Parent.Sonido)

type Abierta = { gui: BillboardGui, relleno: ImageLabel?, carga: Tween? }

local Indicaciones = {}

local jugador = Players.LocalPlayer
local abiertas: { [ProximityPrompt]: Abierta } = {}

local function personalizar(d: Instance)
	if d:IsA("ProximityPrompt") then
		d.Style = Enum.ProximityPromptStyle.Custom
	end
end

local function tecla(prompt: ProximityPrompt, tipo: Enum.ProximityPromptInputType): string
	if tipo == Enum.ProximityPromptInputType.Touch then
		return ""
	elseif tipo == Enum.ProximityPromptInputType.Gamepad then
		return (string.gsub(prompt.GamepadKeyCode.Name, "^Button", ""))
	end
	local texto = UserInputService:GetStringForKeyCode(prompt.KeyboardKeyCode)
	return if texto ~= "" then texto else prompt.KeyboardKeyCode.Name
end

local function cerrar(prompt: ProximityPrompt)
	local a = abiertas[prompt]
	if a then
		a.gui:Destroy()
		abiertas[prompt] = nil
	end
end

local function mostrar(prompt: ProximityPrompt, tipo: Enum.ProximityPromptInputType)
	cerrar(prompt)
	local adorno = prompt.Parent
	if not adorno or not (adorno:IsA("BasePart") or adorno:IsA("Attachment") or adorno:IsA("Model")) then
		return
	end
	local tactil = tipo == Enum.ProximityPromptInputType.Touch
	local b = Instance.new("BillboardGui")
	b.Name = "Indicacion"
	b.AlwaysOnTop = true
	b.Active = tactil
	b.Size = UDim2.fromOffset(270, 70)
	b.StudsOffsetWorldSpace = Vector3.new(0, 1.6, 0)
	b.LightInfluence = 0
	b.MaxDistance = prompt.MaxActivationDistance + 6
	b.ResetOnSpawn = false
	b.Adornee = adorno :: Instance
	local fondo = Gui.panel(b, "Boton", UDim2.new(1, 0, 1, 0), UDim2.new(), nil, tactil)
	fondo.ImageColor3 = Gui.PAPEL
	local caja = Gui.panel(fondo, "Boton", UDim2.fromOffset(50, 46), UDim2.fromOffset(8, 9))
	caja.ImageColor3 = Gui.AMARILLO
	local letra = tecla(prompt, tipo)
	if letra == "" then
		Gui.icono(caja, "Mano", UDim2.new(1, -12, 1, -12), UDim2.fromOffset(6, 4))
	else
		Gui.texto(caja, letra, UDim2.new(1, -12, 1, -14), UDim2.fromOffset(6, 4), Gui.TINTA, true)
	end
	Gui.icono(fondo, "Mano", UDim2.fromOffset(26, 26), UDim2.new(1, -36, 0, 6))
	local accion = Gui.texto(fondo, prompt.ActionText, UDim2.new(1, -110, 0, 28), UDim2.fromOffset(66, 9), Gui.TINTA, true)
	accion.TextXAlignment = Enum.TextXAlignment.Left
	local objeto = Gui.texto(fondo, prompt.ObjectText, UDim2.new(1, -110, 0, 20), UDim2.fromOffset(66, 37), Gui.LAPIZ, false)
	objeto.TextXAlignment = Enum.TextXAlignment.Left
	objeto.TextTruncate = Enum.TextTruncate.AtEnd
	local a: Abierta = { gui = b, relleno = nil, carga = nil }
	if prompt.HoldDuration > 0 then
		local _, relleno = Gui.barra(fondo, UDim2.new(1, -78, 0, 10), UDim2.new(0, 66, 1, -16), Gui.NARANJA)
		Gui.llenar(relleno, 0)
		a.relleno = relleno
	end
	if tactil then
		local boton = fondo :: any
		boton.InputBegan:Connect(function(entrada: InputObject)
			if entrada.UserInputType == Enum.UserInputType.Touch or entrada.UserInputType == Enum.UserInputType.MouseButton1 then
				prompt:InputHoldBegin()
			end
		end)
		boton.InputEnded:Connect(function(entrada: InputObject)
			if entrada.UserInputType == Enum.UserInputType.Touch or entrada.UserInputType == Enum.UserInputType.MouseButton1 then
				prompt:InputHoldEnd()
			end
		end)
	end
	b.Parent = jugador:WaitForChild("PlayerGui")
	abiertas[prompt] = a
end

function Indicaciones.iniciar()
	for _, d in Workspace:GetDescendants() do
		personalizar(d)
	end
	Workspace.DescendantAdded:Connect(personalizar)
	ProximityPromptService.PromptShown:Connect(mostrar)
	ProximityPromptService.PromptHidden:Connect(cerrar)
	ProximityPromptService.PromptButtonHoldBegan:Connect(function(prompt)
		Camara.alcanzar()
		local a = abiertas[prompt]
		local relleno = a and a.relleno
		if a and relleno then
			relleno.Visible = true
			relleno.Size = UDim2.fromScale(0.02, 1)
			a.carga = TweenService:Create(relleno, TweenInfo.new(prompt.HoldDuration, Enum.EasingStyle.Linear), { Size = UDim2.fromScale(1, 1) })
			;(a.carga :: Tween):Play()
		end
	end)
	ProximityPromptService.PromptButtonHoldEnded:Connect(function(prompt)
		local a = abiertas[prompt]
		local relleno = a and a.relleno
		if a and relleno then
			local carga = a.carga
			if carga then
				carga:Cancel()
			end
			Gui.llenar(relleno, 0)
		end
	end)
	ProximityPromptService.PromptTriggered:Connect(function(prompt)
		Camara.alcanzar()
		Sonido.reproducir("UiClick", nil, 0.5, 1.1)
		local a = abiertas[prompt]
		if a then
			local fondo = a.gui:FindFirstChildWhichIsA("GuiObject")
			if fondo then
				fondo.Rotation = -4
				TweenService:Create(fondo, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Rotation = 0 }):Play()
			end
		end
	end)
end

return Indicaciones
