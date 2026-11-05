--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Gui = require(ReplicatedStorage.Shared.Gui)
local Agarre = require(script.Parent.Agarre)
local Sonido = require(script.Parent.Sonido)

type Paso = { texto: string, hecho: boolean, etiqueta: TextLabel?, marca: ImageLabel? }

local Tutorial = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local Estado = ReplicatedStorage:WaitForChild("Estado")
local comidaHasta = 0

local pasos: { Paso } = {
	{ texto = "Elige un vuelo: entrad en su puerta de la terminal", hecho = false },
	{ texto = "Lleva maletas al avión (tractor y escáner)", hecho = false },
	{ texto = "Coge comida en la cocina del avión", hecho = false },
	{ texto = "Sirve a un pasajero (E o lánzasela)", hecho = false },
	{ texto = "Usa el extintor o la llave (F)", hecho = false },
	{ texto = "Que alguien pilote: asiento izquierdo de la cabina", hecho = false },
	{ texto = "Aterrizad en el destino", hecho = false },
}

local function vuelos(): number
	local stats = jugador:FindFirstChild("leaderstats")
	local v = stats and stats:FindFirstChild("Flights")
	return if v and v:IsA("IntValue") then v.Value else -1
end

local function construir(): ImageLabel
	local gui = Instance.new("ScreenGui")
	gui.Name = "Tutorial"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.Parent = jugador:WaitForChild("PlayerGui")
	local panel = Gui.panel(gui, "Papel", UDim2.fromOffset(360, 74 + #pasos * 30), UDim2.new(0, 14, 0.5, -70), Vector2.new(0, 0.5))
	panel.Rotation = -1.5
	local escala = Instance.new("UIScale")
	escala.Parent = panel
	local function ajustar()
		local v = Workspace.CurrentCamera.ViewportSize
		escala.Scale = math.clamp(math.min(v.X / 1366, v.Y / 768), 0.55, 1.2)
	end
	ajustar()
	Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(ajustar)
	local titulo = Gui.texto(panel, "PRIMEROS VUELOS", UDim2.new(1, -50, 0, 30), UDim2.fromOffset(26, 18), Gui.NARANJA, true)
	titulo.TextXAlignment = Enum.TextXAlignment.Left
	for i, p in pasos do
		local y = 22 + i * 30
		Gui.icono(panel, "Casilla", UDim2.fromOffset(24, 24), UDim2.fromOffset(24, y))
		p.marca = Gui.icono(panel, "Tick", UDim2.fromOffset(28, 28), UDim2.fromOffset(25, y - 6))
		local t = Gui.texto(panel, "", UDim2.new(1, -86, 0, 26), UDim2.fromOffset(56, y - 1), Gui.TINTA, false, 20)
		t.TextXAlignment = Enum.TextXAlignment.Left
		t.TextTruncate = Enum.TextTruncate.AtEnd
		t.TextWrapped = false
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
			t.Text = if p.hecho then `<s>{p.texto}</s>` else p.texto
			t.TextColor3 = if p.hecho then Gui.LAPIZ else Gui.TINTA
		end
		local m = p.marca
		if m then
			m.Visible = p.hecho
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
			panel.Visible = fase ~= "Preparacion"
			if fase == "Preparacion" or fase == "Embarque" or fase == "Vuelo" then
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
