--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Agarre = require(script.Parent.Agarre)
local Sonido = require(script.Parent.Sonido)

type Paso = { texto: string, hecho: boolean, etiqueta: TextLabel? }

local Tutorial = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local Estado = ReplicatedStorage:WaitForChild("Estado")
local CREMA = Color3.fromRGB(255, 244, 224)
local VERDE = Color3.fromRGB(120, 220, 130)
local FUENTE = Enum.Font.FredokaOne
local comidaHasta = 0

local pasos: { Paso } = {
	{ texto = "Elige un vuelo: E en un quiosco de la terminal", hecho = false },
	{ texto = "Lleva maletas al avión (tractor 🚜, escáner 🛃)", hecho = false },
	{ texto = "Coge comida en la cocina del avión", hecho = false },
	{ texto = "Sirve a un pasajero (E o lánzasela 🎯)", hecho = false },
	{ texto = "Usa el extintor 🔥 o la llave 🔧 (F)", hecho = false },
	{ texto = "Que alguien pilote: asiento izquierdo de la cabina", hecho = false },
	{ texto = "Aterrizad en el destino 🛬", hecho = false },
}

local function vuelos(): number
	local stats = jugador:FindFirstChild("leaderstats")
	local v = stats and stats:FindFirstChild("Vuelos")
	return if v and v:IsA("IntValue") then v.Value else -1
end

local function construir(): Frame
	local gui = Instance.new("ScreenGui")
	gui.Name = "Tutorial"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.Parent = jugador:WaitForChild("PlayerGui")
	local panel = Instance.new("Frame")
	panel.Size = UDim2.fromOffset(330, 34 + #pasos * 26)
	panel.Position = UDim2.new(0, 14, 0.5, -60)
	panel.BackgroundColor3 = Color3.fromRGB(27, 27, 33)
	panel.BackgroundTransparency = 0.25
	panel.BorderSizePixel = 0
	panel.Parent = gui
	local esquina = Instance.new("UICorner")
	esquina.CornerRadius = UDim.new(0, 12)
	esquina.Parent = panel
	local titulo = Instance.new("TextLabel")
	titulo.Text = "✈ PRIMEROS VUELOS"
	titulo.Size = UDim2.new(1, -20, 0, 26)
	titulo.Position = UDim2.fromOffset(10, 4)
	titulo.BackgroundTransparency = 1
	titulo.Font = FUENTE
	titulo.TextSize = 18
	titulo.TextColor3 = Color3.fromRGB(242, 123, 43)
	titulo.TextXAlignment = Enum.TextXAlignment.Left
	titulo.Parent = panel
	for i, p in pasos do
		local t = Instance.new("TextLabel")
		t.Size = UDim2.new(1, -20, 0, 24)
		t.Position = UDim2.fromOffset(10, 6 + i * 26)
		t.BackgroundTransparency = 1
		t.Font = FUENTE
		t.TextSize = 15
		t.TextColor3 = CREMA
		t.TextXAlignment = Enum.TextXAlignment.Left
		t.TextTruncate = Enum.TextTruncate.AtEnd
		t.Parent = panel
		p.etiqueta = t
	end
	return panel
end

local function marcar(i: number)
	local p = pasos[i]
	if p.hecho then
		return
	end
	p.hecho = true
	Sonido.reproducir("UiClick", nil, 0.8, 1.2)
end

local function refrescar()
	for _, p in pasos do
		local t = p.etiqueta
		if t then
			t.Text = (if p.hecho then "✅ " else "⬜ ") .. p.texto
			t.TextColor3 = if p.hecho then VERDE else CREMA
			t.TextTransparency = if p.hecho then 0.35 else 0
		end
	end
end

local function cerca(modelo: Instance, radio: number): boolean
	local raiz = jugador.Character and jugador.Character:FindFirstChild("HumanoidRootPart")
	local cuerpo = modelo:FindFirstChild("Cuerpo")
	return raiz ~= nil and cuerpo ~= nil and raiz:IsA("BasePart") and cuerpo:IsA("BasePart") and (raiz.Position - cuerpo.Position).Magnitude < radio
end

function Tutorial.iniciar()
	task.spawn(function()
		local limite = os.clock() + 60
		while vuelos() < 0 and os.clock() < limite do
			task.wait(0.5)
		end
		if vuelos() >= 2 then
			return
		end
		local panel = construir()
		local function servido(modelo: Instance)
			if modelo:IsA("Model") then
				modelo:GetAttributeChangedSignal("Feliz"):Connect(function()
					if cerca(modelo, 16) and os.clock() < comidaHasta then
						marcar(4)
					end
				end)
			end
		end
		for _, m in CollectionService:GetTagged("Pasajero") do
			servido(m)
		end
		local conexion = CollectionService:GetInstanceAddedSignal("Pasajero"):Connect(servido)
		local uso = UserInputService.InputBegan:Connect(function(entrada, procesado)
			if procesado or (entrada.KeyCode ~= Enum.KeyCode.F and entrada.KeyCode ~= Enum.KeyCode.ButtonX) then
				return
			end
			local o = Agarre.sostenido()
			local t = if o then Agarre.tipo(o) else ""
			if t == "Extintor" or t == "Llave" then
				marcar(5)
			end
		end)
		refrescar()
		while panel.Parent do
			task.wait(0.5)
			local fase = Estado:GetAttribute("Fase")
			if fase == "Embarque" or fase == "Vuelo" then
				marcar(1)
			end
			if fase == "Vuelo" then
				marcar(2)
			end
			local o = Agarre.sostenido()
			local tipo = if o then Agarre.tipo(o) else ""
			if tipo == "Maleta" then
				marcar(2)
			elseif tipo == "Bandeja" or tipo == "Cafe" or tipo == "Agua" or tipo == "Hamburguesa" then
				marcar(3)
				comidaHasta = os.clock() + 4
			end
			local piloto = avion:GetAttribute("Piloto")
			if typeof(piloto) == "number" and piloto ~= 0 then
				marcar(6)
			end
			if fase == "Resultados" and avion:GetAttribute("Fase") == "Aterrizado" then
				marcar(7)
			end
			refrescar()
			local todos = true
			for _, p in pasos do
				todos = todos and p.hecho
			end
			if todos or vuelos() >= 2 then
				task.wait(4)
				conexion:Disconnect()
				uso:Disconnect()
				local gui = panel.Parent
				if gui then
					gui:Destroy()
				end
				return
			end
		end
	end)
end

return Tutorial
