--!strict
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Agarre = require(script.Parent.Agarre)
local Sonido = require(script.Parent.Sonido)

local Escalada = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local parametros = RaycastParams.new()
parametros.FilterType = Enum.RaycastFilterType.Include
local controles: any = nil
local activo = false
local punto = Vector3.zero
local normal = Vector3.xAxis
local adjunto: Attachment? = nil
local posicion: AlignPosition? = nil
local orientacion: AlignOrientation? = nil
local VELOCIDAD = 7
local tactil = false

local function cuerpo(): (Model?, Humanoid?, BasePart?)
	local personaje = jugador.Character
	local h = personaje and personaje:FindFirstChildOfClass("Humanoid")
	local r = personaje and personaje:FindFirstChild("HumanoidRootPart")
	if personaje and h and r and r:IsA("BasePart") then
		return personaje, h, r
	end
	return nil, nil, nil
end

local function conPiolet(): boolean
	local o = Agarre.sostenido()
	return o ~= nil and Agarre.tipo(o) == "Piolet"
end

local function arriba(n: Vector3, camara: CFrame): Vector3
	local u = Vector3.yAxis - n * n:Dot(Vector3.yAxis)
	if u.Magnitude < 0.35 then
		u = camara.LookVector - n * n:Dot(camara.LookVector)
	end
	return if u.Magnitude > 1e-3 then u.Unit else Vector3.zAxis
end

local function fuera(p: Vector3, n: Vector3): boolean
	return (p - Vector3.new(0, 105, p.Z)):Dot(n) > 0
end

local function enCabina(p: Vector3): boolean
	return math.abs(p.X) < 7.4 and p.Y > 99 and p.Y < 112 and p.Z > -63 and p.Z < 23
end

local function limpiar()
	if posicion then
		posicion:Destroy()
	end
	if orientacion then
		orientacion:Destroy()
	end
	if adjunto then
		adjunto:Destroy()
	end
	posicion, orientacion, adjunto = nil, nil, nil
end

local function soltar(saltar: boolean)
	if not activo then
		return
	end
	activo = false
	limpiar()
	local personaje, h, r = cuerpo()
	if personaje then
		personaje:SetAttribute("Escalando", false)
	end
	if h then
		h.PlatformStand = false
		if h.Health > 0 and not (personaje and personaje:GetAttribute("Ragdoll")) then
			h:ChangeState(Enum.HumanoidStateType.Freefall)
		end
	end
	if saltar and r then
		r.AssemblyLinearVelocity = normal * 16 + Vector3.yAxis * 12
	end
end

local function agarrar(): boolean
	local personaje, h, r = cuerpo()
	if not personaje or not h or not r or h.SeatPart or h.Health <= 0 or personaje:GetAttribute("Ragdoll") or not conPiolet() then
		return false
	end
	local casco = avion:FindFirstChild("Casco")
	if not casco or enCabina(r.Position) then
		return false
	end
	parametros.FilterDescendantsInstances = { casco }
	local camara = Workspace.CurrentCamera.CFrame
	local res = Workspace:Raycast(r.Position, camara.LookVector * 4.5, parametros)
	local plano = camara.LookVector * Vector3.new(1, 0, 1)
	if not res and plano.Magnitude > 0.05 then
		res = Workspace:Raycast(r.Position, plano.Unit * 4.5, parametros)
	end
	if not res then
		res = Workspace:Raycast(r.Position, Vector3.new(0, -4, 0), parametros)
	end
	if not res or not fuera(res.Position, res.Normal) then
		return false
	end
	punto, normal = res.Position, res.Normal
	local a = Instance.new("Attachment")
	a.Name = "Escalada"
	a.Parent = r
	local p = Instance.new("AlignPosition")
	p.Mode = Enum.PositionAlignmentMode.OneAttachment
	p.Attachment0 = a
	p.MaxForce = 2e5
	p.MaxVelocity = 30
	p.Responsiveness = 35
	p.Position = punto + normal * 1.3
	p.Parent = r
	local o = Instance.new("AlignOrientation")
	o.Mode = Enum.OrientationAlignmentMode.OneAttachment
	o.Attachment0 = a
	o.MaxTorque = 2e5
	o.Responsiveness = 30
	o.CFrame = CFrame.lookAt(Vector3.zero, -normal, arriba(normal, camara))
	o.Parent = r
	adjunto, posicion, orientacion = a, p, o
	h.PlatformStand = true
	activo = true
	personaje:SetAttribute("Escalando", true)
	Sonido.reproducir("GolpeMetal", punto, 0.6)
	return true
end

function Escalada.activo(): boolean
	return activo
end

function Escalada.iniciar()
	task.spawn(function()
		local scripts = jugador:WaitForChild("PlayerScripts")
		local modulo = scripts:WaitForChild("PlayerModule", 20)
		if modulo and modulo:IsA("ModuleScript") then
			local ok, m = pcall(require, modulo)
			if ok and m then
				controles = (m :: any):GetControls()
			end
		end
	end)
	ContextActionService:BindAction("Piolet", function(_, estado)
		if estado == Enum.UserInputState.Begin and not activo and conPiolet() then
			agarrar()
		end
		return Enum.ContextActionResult.Pass
	end, false, Enum.KeyCode.F, Enum.KeyCode.ButtonX)
	UserInputService.JumpRequest:Connect(function()
		soltar(true)
	end)
	jugador.CharacterAdded:Connect(function()
		activo = false
		limpiar()
	end)
	RunService.Heartbeat:Connect(function(dt: number)
		local quiere = UserInputService.TouchEnabled and conPiolet()
		if quiere ~= tactil then
			tactil = quiere
			if quiere then
				ContextActionService:BindAction("PioletTactil", function(_, estado)
					if estado == Enum.UserInputState.Begin then
						if activo then
							soltar(true)
						else
							agarrar()
						end
					end
					return Enum.ContextActionResult.Sink
				end, true)
				ContextActionService:SetTitle("PioletTactil", "Piolet")
			else
				ContextActionService:UnbindAction("PioletTactil")
			end
		end
		if not activo then
			return
		end
		local personaje, h, r = cuerpo()
		if not personaje or not h or not r or h.Health <= 0 or personaje:GetAttribute("Ragdoll") or not conPiolet() then
			soltar(false)
			return
		end
		local camara = Workspace.CurrentCamera.CFrame
		local mv: Vector3 = if controles then controles:GetMoveVector() else Vector3.zero
		local subir = arriba(normal, camara)
		local derecha = (-normal):Cross(subir)
		local mov = subir * -mv.Z + derecha * mv.X
		if mov.Magnitude > 0.01 then
			local nuevo = punto + mov.Unit * math.min(mov.Magnitude, 1) * VELOCIDAD * dt
			local res = Workspace:Raycast(nuevo + normal * 1.5, -normal * 3, parametros)
			if res and fuera(res.Position, res.Normal) then
				punto, normal = res.Position, res.Normal
				subir = arriba(normal, camara)
			end
		end
		local p, o = posicion, orientacion
		if p then
			p.Position = punto + normal * 1.3
		end
		if o then
			o.CFrame = CFrame.lookAt(Vector3.zero, -normal, subir)
		end
		if (r.Position - (punto + normal * 1.3)).Magnitude > 6 then
			soltar(false)
		end
	end)
end

return Escalada
