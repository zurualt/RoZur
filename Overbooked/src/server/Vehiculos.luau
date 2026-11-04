--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Sonidos = require(script.Parent.Sonidos)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent

local Vehiculos = {}

local aeropuerto = Workspace:WaitForChild("Aeropuerto") :: Model
local carpeta = aeropuerto:WaitForChild("Vehiculos")
local tractor = carpeta:WaitForChild("Tractor") :: BasePart
local asiento = tractor:WaitForChild("AsientoTractor") :: VehicleSeat
local carro = carpeta:WaitForChild("CarroEquipaje") :: BasePart
local inicioTractor = tractor.CFrame
local inicioCarro = carro.CFrame
local enganche: RodConstraint? = nil
local aviso: ProximityPrompt? = nil

local function propietario(parte: BasePart, jugador: Player?)
	if parte.Anchored or not parte:IsDescendantOf(Workspace) then
		return
	end
	pcall(function()
		parte:SetNetworkOwner(jugador)
	end)
end

local function conductor(): Player?
	local ocupante = asiento.Occupant
	return if ocupante then Players:GetPlayerFromCharacter(ocupante.Parent) else nil
end

local function preparar(raiz: BasePart, friccion: number)
	for _, h in raiz:GetChildren() do
		if h:IsA("BasePart") then
			local w = Instance.new("WeldConstraint")
			w.Part0 = raiz
			w.Part1 = h
			w.Parent = h
			h.Anchored = false
			h.Massless = true
		end
	end
	raiz.CustomPhysicalProperties = PhysicalProperties.new(0.7, friccion, 0, 1, 1)
	local a = Instance.new("Attachment")
	a.Name = "Vertical"
	a.Axis = Vector3.yAxis
	a.SecondaryAxis = Vector3.xAxis
	a.Parent = raiz
	local al = Instance.new("AlignOrientation")
	al.Mode = Enum.OrientationAlignmentMode.OneAttachment
	al.AlignType = Enum.AlignType.PrimaryAxisParallel
	al.PrimaryAxis = Vector3.yAxis
	al.Attachment0 = a
	al.MaxTorque = 2e5
	al.Responsiveness = 25
	al.Parent = raiz
	raiz.Anchored = false
end

local function puntos(): (Vector3, Vector3)
	local trasera = tractor.CFrame * Vector3.new(0, -0.35, tractor.Size.Z / 2 + 0.15)
	local lanza = carro.CFrame * Vector3.new(carro.Size.X / 2 + 0.35, -0.2, 0)
	return trasera, lanza
end

local function soltar()
	local e = enganche
	if e then
		local a0, a1 = e.Attachment0, e.Attachment1
		e:Destroy()
		if a0 then
			a0:Destroy()
		end
		if a1 then
			a1:Destroy()
		end
	end
	enganche = nil
	propietario(carro, nil)
	local p = aviso
	if p then
		p.ActionText = "Enganchar al tractor"
	end
end

local function enganchar(): boolean
	local trasera, lanza = puntos()
	local d = (trasera - lanza).Magnitude
	if d > 7 then
		return false
	end
	local a0 = Instance.new("Attachment")
	a0.Name = "Enganche"
	a0.Position = tractor.CFrame:PointToObjectSpace(trasera)
	a0.Parent = tractor
	local a1 = Instance.new("Attachment")
	a1.Name = "Lanza"
	a1.Position = carro.CFrame:PointToObjectSpace(lanza)
	a1.Parent = carro
	local barra = Instance.new("RodConstraint")
	barra.Attachment0 = a0
	barra.Attachment1 = a1
	barra.Length = math.clamp(d, 1.5, 4)
	barra.Thickness = 0.2
	barra.Color = BrickColor.new("Dark stone grey")
	barra.Visible = true
	barra.Parent = tractor
	enganche = barra
	propietario(carro, conductor())
	local p = aviso
	if p then
		p.ActionText = "Soltar del tractor"
	end
	Sonidos.emitir("GolpeMetal", lanza)
	return true
end

function Vehiculos.reiniciar()
	soltar()
	local soldadura = asiento:FindFirstChild("SeatWeld")
	if soldadura then
		soldadura:Destroy()
	end
	for _, parte in { tractor, carro } do
		parte.AssemblyLinearVelocity = Vector3.zero
		parte.AssemblyAngularVelocity = Vector3.zero
	end
	tractor:PivotTo(inicioTractor)
	carro:PivotTo(inicioCarro)
	propietario(tractor, nil)
	propietario(carro, nil)
end

function Vehiculos.iniciar()
	preparar(tractor, 0.25)
	preparar(carro, 0.12)
	local p = Instance.new("ProximityPrompt")
	p.ActionText = "Enganchar al tractor"
	p.ObjectText = "Carro de equipaje"
	p.KeyboardKeyCode = Enum.KeyCode.E
	p.MaxActivationDistance = 11
	p.RequiresLineOfSight = false
	p.Parent = carro
	aviso = p
	p.Triggered:Connect(function(jugador)
		if enganche then
			soltar()
		elseif not enganchar() then
			RemotoAviso:FireClient(jugador, "🚜 Acerca la parte de atrás del tractor a la lanza del carro", "info")
		end
	end)
	asiento:GetPropertyChangedSignal("Occupant"):Connect(function()
		local j = conductor()
		propietario(tractor, j)
		if enganche then
			propietario(carro, j)
		end
		if not j then
			tractor.AssemblyLinearVelocity = Vector3.zero
			tractor.AssemblyAngularVelocity = Vector3.zero
		end
	end)
	aeropuerto.AncestryChanged:Connect(function()
		if aeropuerto:IsDescendantOf(Workspace) then
			task.defer(Vehiculos.reiniciar)
		end
	end)
end

return Vehiculos
