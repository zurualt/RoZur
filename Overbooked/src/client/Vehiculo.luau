--!strict
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local Audio = require(ReplicatedStorage.Shared.Audio)
local Gui = require(ReplicatedStorage.Shared.Gui)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Camara = require(script.Parent.Camara)

local Vehiculo = {}

local jugador = Players.LocalPlayer
local VELOCIDAD = 30
local MARCHA_ATRAS = 14
local ACELERACION = 1.8
local FRENADO = 4.5
local GIRO = 1.7
local claxon: RemoteEvent? = nil
local conduciendo: BasePart? = nil
local motor: Sound? = nil
local humo: ParticleEmitter? = nil
local cartel: ScreenGui? = nil
local ultimoClaxon = 0
local rapidez = 0
local giroActual = 0

local modControles: any = nil

local function controles(): any
	return modControles
end

local function entrada(): (number, number)
	local acel, giro = 0, 0
	if UserInputService:IsKeyDown(Enum.KeyCode.W) or UserInputService:IsKeyDown(Enum.KeyCode.Up) then
		acel += 1
	end
	if UserInputService:IsKeyDown(Enum.KeyCode.S) or UserInputService:IsKeyDown(Enum.KeyCode.Down) then
		acel -= 1
	end
	if UserInputService:IsKeyDown(Enum.KeyCode.D) or UserInputService:IsKeyDown(Enum.KeyCode.Right) then
		giro += 1
	end
	if UserInputService:IsKeyDown(Enum.KeyCode.A) or UserInputService:IsKeyDown(Enum.KeyCode.Left) then
		giro -= 1
	end
	for _, estado in UserInputService:GetGamepadState(Enum.UserInputType.Gamepad1) do
		if estado.KeyCode == Enum.KeyCode.ButtonR2 then
			acel += estado.Position.Z
		elseif estado.KeyCode == Enum.KeyCode.ButtonL2 then
			acel -= estado.Position.Z
		end
	end
	local c = controles()
	if c then
		local ok, mv = pcall(function()
			return c:GetMoveVector()
		end)
		if ok and typeof(mv) == "Vector3" and mv.Magnitude > 0.1 then
			acel += -mv.Z
			giro += mv.X
		end
	end
	return math.clamp(acel, -1, 1), math.clamp(giro, -1, 1)
end

local function tocarClaxon(_: string, estado: Enum.UserInputState): Enum.ContextActionResult
	if estado ~= Enum.UserInputState.Begin then
		return Enum.ContextActionResult.Pass
	end
	local ahora = os.clock()
	local c = claxon
	if c and conduciendo and ahora - ultimoClaxon > 0.8 then
		ultimoClaxon = ahora
		c:FireServer()
	end
	return Enum.ContextActionResult.Sink
end

local function crearCartel()
	local g = Instance.new("ScreenGui")
	g.Name = "Conducir"
	g.ResetOnSpawn = false
	g.IgnoreGuiInset = true
	g.DisplayOrder = 6
	local escala = Instance.new("UIScale")
	escala.Scale = Gui.escala(0.7, 1)
	escala.Parent = g
	local panel = Gui.panel(g, "Etiqueta", UDim2.fromOffset(520, 64), UDim2.new(0.5, 0, 1, -24), Vector2.new(0.5, 1))
	local texto = if Gui.tactil() then "Joystick: conducir · Bocina: botón · Salta para bajar" else "W/S acelerar · A/D girar · F bocina · Espacio bajar"
	Gui.icono(panel, "Volante", UDim2.fromOffset(40, 40), UDim2.fromOffset(18, 12))
	local t = Gui.texto(panel, texto, UDim2.new(1, -86, 0, 30), UDim2.fromOffset(68, 17), Gui.TINTA, false)
	t.TextXAlignment = Enum.TextXAlignment.Left
	g.Parent = jugador:WaitForChild("PlayerGui")
	cartel = g
end

local function subir(chasis: BasePart)
	conduciendo = chasis
	Camara.terceraPersona(true)
	local s = Instance.new("Sound")
	s.Name = "MotorTractor"
	s.SoundId = `rbxassetid://{Audio.IDS.MotorAvion or 0}`
	s.Looped = true
	s.Volume = 0.35
	s.PlaybackSpeed = 1.5
	s.RollOffMaxDistance = 80
	s.Parent = chasis
	s:Play()
	motor = s
	local a = chasis:FindFirstChild("Escape")
	if not a then
		local nuevo = Instance.new("Attachment")
		nuevo.Name = "Escape"
		nuevo.Position = Vector3.new(chasis.Size.X * 0.35, chasis.Size.Y * 0.5 + 0.6, chasis.Size.Z * 0.42)
		nuevo.Parent = chasis
		a = nuevo
	end
	local e = Instance.new("ParticleEmitter")
	e.Texture = VFX.textura("Humo1")
	e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.4), NumberSequenceKeypoint.new(1, 1.6) })
	e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) })
	e.Color = ColorSequence.new(Color3.fromRGB(120, 120, 128))
	e.Lifetime = NumberRange.new(0.6, 1.1)
	e.Speed = NumberRange.new(1.5, 3)
	e.SpreadAngle = Vector2.new(18, 18)
	e.Acceleration = Vector3.new(0, 3, 0)
	e.Rate = 6
	e.Parent = a
	humo = e
	ContextActionService:BindActionAtPriority("ClaxonTractor", tocarClaxon, true, 3100, Enum.KeyCode.F, Enum.KeyCode.ButtonX)
	ContextActionService:SetTitle("ClaxonTractor", "Bocina")
	ContextActionService:SetPosition("ClaxonTractor", Gui.posTactil(1, 1))
	crearCartel()
end

local function bajar()
	conduciendo = nil
	rapidez = 0
	giroActual = 0
	Camara.terceraPersona(false)
	local m = motor
	if m then
		m:Destroy()
	end
	motor = nil
	local h = humo
	if h then
		h:Destroy()
	end
	humo = nil
	ContextActionService:UnbindAction("ClaxonTractor")
	local c = cartel
	if c then
		c:Destroy()
	end
	cartel = nil
end

function Vehiculo.iniciar()
	task.spawn(function()
		local modulo = jugador:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule", 20)
		if modulo and modulo:IsA("ModuleScript") then
			local ok, m = pcall(require, modulo)
			if ok and m then
				modControles = (m :: any):GetControls()
			end
		end
	end)
	task.spawn(function()
		local r = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Claxon", 30)
		if r and r:IsA("RemoteEvent") then
			claxon = r
		end
	end)
	RunService.Heartbeat:Connect(function(dt: number)
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		local asiento = humanoide and humanoide.SeatPart
		local chasis = if asiento and asiento:IsA("VehicleSeat") and asiento.Name == "AsientoTractor" then asiento.Parent else nil
		if not chasis or not chasis:IsA("BasePart") or chasis.Anchored then
			if conduciendo then
				bajar()
			end
			return
		end
		if conduciendo ~= chasis then
			if conduciendo then
				bajar()
			end
			subir(chasis)
		end
		local frente = chasis.CFrame.LookVector * Vector3.new(1, 0, 1)
		if frente.Magnitude < 0.1 then
			return
		end
		frente = frente.Unit
		local acel, giroEntrada = entrada()
		local v = chasis.AssemblyLinearVelocity
		local plano = v * Vector3.new(1, 0, 1)
		local avance = plano:Dot(frente)
		local lateral = plano - frente * avance
		if math.abs(rapidez - avance) > 10 then
			rapidez = avance + math.sign(rapidez - avance) * 10
		end
		local objetivo = if acel >= 0 then acel * VELOCIDAD else acel * MARCHA_ATRAS
		local frenando = (acel > 0 and rapidez < -1) or (acel < 0 and rapidez > 1) or acel == 0
		local paso = (if frenando then FRENADO * 9 else ACELERACION * 9) * dt
		rapidez += math.clamp(objetivo - rapidez, -paso, paso)
		local nuevo = frente * rapidez + lateral * math.max(0, 1 - dt * 8)
		chasis.AssemblyLinearVelocity = Vector3.new(nuevo.X, v.Y, nuevo.Z)
		local sentido = if rapidez < -0.5 then -1 else 1
		local objetivoGiro = -giroEntrada * GIRO * math.clamp(math.abs(rapidez) / 5, 0, 1) * sentido
		giroActual += (objetivoGiro - giroActual) * math.min(1, dt * 8)
		local w = chasis.AssemblyAngularVelocity
		chasis.AssemblyAngularVelocity = Vector3.new(w.X, giroActual, w.Z)
		local m = motor
		if m then
			local r = math.abs(rapidez) / VELOCIDAD
			m.PlaybackSpeed = 1.3 + r * 0.9
			m.Volume = 0.25 + r * 0.25
		end
		local h = humo
		if h then
			h.Rate = 5 + math.abs(acel) * 20
		end
	end)
end

return Vehiculo
