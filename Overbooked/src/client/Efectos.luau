--!strict
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Camara = require(script.Parent.Camara)

local Efectos = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local rng = Random.new()
local destello: Frame
local atmosfera = Lighting:FindFirstChildOfClass("Atmosphere")
local base = {
	reloj = Lighting.ClockTime,
	brillo = Lighting.Brightness,
	densidad = if atmosfera then atmosfera.Density else 0.3,
}
local tormenta = false
local proximoRayo = 0

local function pantalla()
	local gui = Instance.new("ScreenGui")
	gui.Name = "OverbookedEfectos"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 50
	destello = Instance.new("Frame")
	destello.Size = UDim2.fromScale(1, 1)
	destello.BackgroundColor3 = Color3.new(1, 1, 1)
	destello.BackgroundTransparency = 1
	destello.BorderSizePixel = 0
	destello.Parent = gui
	gui.Parent = jugador:WaitForChild("PlayerGui")
end

local function destellar(color: Color3, fuerza: number, duracion: number)
	destello.BackgroundColor3 = color
	destello.BackgroundTransparency = 1 - fuerza
	TweenService:Create(destello, TweenInfo.new(duracion), { BackgroundTransparency = 1 }):Play()
end

local function ambiente(oscuro: boolean)
	local info = TweenInfo.new(3)
	TweenService:Create(Lighting, info, {
		ClockTime = if oscuro then 18.6 else base.reloj,
		Brightness = if oscuro then 0.9 else base.brillo,
	}):Play()
	if atmosfera then
		TweenService:Create(atmosfera, info, { Density = if oscuro then 0.55 else base.densidad }):Play()
	end
end

local function bandada()
	local carpeta = Instance.new("Folder")
	carpeta.Name = "Bandada"
	carpeta.Parent = Workspace
	local pajaros: { { parte: BasePart, pos: Vector3, vel: Vector3, fase: number } } = {}
	for _ = 1, 70 do
		local p = Instance.new("WedgePart")
		p.Size = Vector3.new(1.6, 0.3, 1)
		p.Color = Color3.fromRGB(40, 40, 46)
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.CanTouch = false
		p.CastShadow = false
		p.Parent = carpeta
		table.insert(pajaros, {
			parte = p :: BasePart,
			pos = Vector3.new(rng:NextNumber(-60, 60), 100 + rng:NextNumber(-10, 22), rng:NextNumber(-520, -160)),
			vel = Vector3.new(rng:NextNumber(-6, 6), rng:NextNumber(-2, 2), rng:NextNumber(150, 230)),
			fase = rng:NextNumber(0, 6),
		})
	end
	local inicio = os.clock()
	local conexion: RBXScriptConnection
	conexion = RunService.PreRender:Connect(function(dt)
		local t = os.clock() - inicio
		for _, b in pajaros do
			b.pos += b.vel * dt
			b.parte.CFrame = CFrame.new(b.pos) * CFrame.Angles(math.sin(t * 14 + b.fase) * 0.6, 0, 0)
		end
		if t > 4.5 then
			conexion:Disconnect()
			carpeta:Destroy()
		end
	end)
end

function Efectos.iniciar()
	pantalla()
	avion:GetAttributeChangedSignal("Tormenta"):Connect(function()
		tormenta = avion:GetAttribute("Tormenta") == true
		ambiente(tormenta)
	end)
	avion:GetAttributeChangedSignal("CaidaLibre"):Connect(function()
		if avion:GetAttribute("CaidaLibre") then
			Camara.impulsoFov(16)
			Camara.sacudir(0.5)
		end
	end)
	avion:GetAttributeChangedSignal("Bandada"):Connect(bandada)
	avion:GetAttributeChangedSignal("Pajaros"):Connect(function()
		Camara.sacudir(0.9)
		destellar(Color3.fromRGB(255, 170, 90), 0.35, 0.5)
	end)
	avion:GetAttributeChangedSignal("Golpe"):Connect(function()
		Camara.sacudir(1)
	end)
	avion:GetAttributeChangedSignal("Fase"):Connect(function()
		local fase = avion:GetAttribute("Fase")
		if fase == "Estrellado" then
			Camara.sacudir(1)
			destellar(Color3.fromRGB(255, 120, 60), 0.8, 1.6)
		end
	end)
	RunService.Heartbeat:Connect(function()
		if tormenta and os.clock() > proximoRayo then
			proximoRayo = os.clock() + rng:NextNumber(2.5, 7)
			destellar(Color3.new(1, 1, 1), 0.65, 0.35)
			Camara.sacudir(0.25)
		end
	end)
end

return Efectos
