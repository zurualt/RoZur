--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Activos = require(script.Parent.Activos)
local Agarre = require(script.Parent.Agarre)
local Sonidos = require(script.Parent.Sonidos)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent

local Vehiculos = {}

local aeropuerto = Workspace:WaitForChild("Aeropuerto") :: Model
local carpeta = aeropuerto:WaitForChild("Vehiculos")
local tractor = carpeta:WaitForChild("Tractor") :: BasePart
local carro = carpeta:WaitForChild("CarroEquipaje") :: BasePart
local plantillaTractor: BasePart? = nil
local plantillaCarro: BasePart? = nil
local inicioTractor = tractor.CFrame
local inicioCarro = carro.CFrame
local enganche: RodConstraint? = nil
local aviso: ProximityPrompt? = nil
local cedidos: { [BasePart]: boolean } = {}
local conexiones: { RBXScriptConnection } = {}

local function propietario(parte: BasePart, jugador: Player?)
	if parte.Anchored or not parte:IsDescendantOf(Workspace) then
		return
	end
	pcall(function()
		parte:SetNetworkOwner(jugador)
	end)
end

local function asiento(): VehicleSeat?
	local a = tractor:FindFirstChild("AsientoTractor")
	return if a and a:IsA("VehicleSeat") then a else nil
end

local function conductor(): Player?
	local a = asiento()
	local ocupante = a and a.Occupant
	return if ocupante then Players:GetPlayerFromCharacter(ocupante.Parent) else nil
end

local function plantilla(parte: BasePart): BasePart
	local copia = parte:Clone()
	for _, h in copia:GetChildren() do
		if h:IsA("Model") then
			h:Destroy()
		end
	end
	return copia
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

local function devolverMaletas()
	for parte in cedidos do
		if parte.Parent and not Agarre.portador(parte) then
			propietario(parte, nil)
		end
	end
	table.clear(cedidos)
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
	devolverMaletas()
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
	barra.Length = math.max(d, 1.5)
	barra.Thickness = 0.2
	barra.Color = BrickColor.new("Dark stone grey")
	barra.Visible = true
	barra.Parent = tractor
	if d > 2.5 then
		TweenService:Create(barra, TweenInfo.new(1.2, Enum.EasingStyle.Sine), { Length = 2.5 }):Play()
	end
	enganche = barra
	propietario(carro, conductor())
	local p = aviso
	if p then
		p.ActionText = "Soltar del tractor"
	end
	Sonidos.emitir("GolpeMetal", lanza)
	return true
end

local function conectar()
	for _, c in conexiones do
		c:Disconnect()
	end
	table.clear(conexiones)
	local p = Instance.new("ProximityPrompt")
	p.ActionText = "Enganchar al tractor"
	p.ObjectText = "Carro de equipaje"
	p.KeyboardKeyCode = Enum.KeyCode.E
	p.MaxActivationDistance = 11
	p.RequiresLineOfSight = false
	p.Parent = carro
	aviso = p
	table.insert(conexiones, p.Triggered:Connect(function(jugador)
		if enganche then
			soltar()
		elseif not enganchar() then
			RemotoAviso:FireClient(jugador, "Acerca la parte de atrás del tractor a la lanza del carro", "info")
		end
	end))
	local a = asiento()
	if a then
		table.insert(conexiones, a:GetPropertyChangedSignal("Occupant"):Connect(function()
			local j = conductor()
			if not j then
				devolverMaletas()
			end
			propietario(tractor, j)
			if enganche then
				propietario(carro, j)
			end
			if not j then
				tractor.AssemblyLinearVelocity = Vector3.zero
				tractor.AssemblyAngularVelocity = Vector3.zero
			end
		end))
	end
end

local function rehacer()
	local t, c = plantillaTractor, plantillaCarro
	if not t or not c then
		return
	end
	soltar()
	if tractor.Parent then
		tractor:Destroy()
	end
	if carro.Parent then
		carro:Destroy()
	end
	tractor = t:Clone()
	carro = c:Clone()
	tractor.Parent = carpeta
	carro.Parent = carpeta
	preparar(tractor, 0.25)
	preparar(carro, 0.12)
	local escala = tractor:GetAttribute("Escala")
	Activos.vestirDinamico(tractor, "Tractor", if typeof(escala) == "number" then escala else nil)
	Activos.vestirDinamico(carro, "CarroEquipaje")
	conectar()
end

local function perdido(parte: BasePart, inicio: CFrame): boolean
	return not parte.Parent or not parte:IsDescendantOf(aeropuerto) or parte.Position.Y < 85 or (parte.Position - inicio.Position).Magnitude > 260
end

function Vehiculos.carro(): BasePart?
	if carro.Parent and carro:IsDescendantOf(Workspace) and not perdido(carro, inicioCarro) then
		return carro
	end
	return nil
end

function Vehiculos.tractor(): BasePart
	return tractor
end

local function aparcar(cfTractor: CFrame, cfCarro: CFrame)
	if perdido(tractor, inicioTractor) or perdido(carro, inicioCarro) then
		rehacer()
	end
	soltar()
	local a = asiento()
	local soldadura = a and a:FindFirstChild("SeatWeld")
	if soldadura then
		soldadura:Destroy()
	end
	propietario(tractor, nil)
	propietario(carro, nil)
	tractor:PivotTo(cfTractor)
	carro:PivotTo(cfCarro)
	for _, parte in { tractor, carro } do
		parte.AssemblyLinearVelocity = Vector3.zero
		parte.AssemblyAngularVelocity = Vector3.zero
	end
end

function Vehiculos.reiniciar()
	aparcar(inicioTractor, inicioCarro)
end

function Vehiculos.colocar(suelo: CFrame, sueloCarro: CFrame)
	aparcar(suelo * CFrame.new(0, tractor.Size.Y / 2, 0), sueloCarro * CFrame.new(0, carro.Size.Y / 2, 0))
	enganchar()
end

function Vehiculos.iniciar()
	plantillaTractor = plantilla(tractor)
	plantillaCarro = plantilla(carro)
	preparar(tractor, 0.25)
	preparar(carro, 0.12)
	conectar()
	aeropuerto.AncestryChanged:Connect(function()
		if aeropuerto:IsDescendantOf(Workspace) then
			task.defer(Vehiculos.reiniciar)
		end
	end)
	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		if acumulado < 0.5 then
			return
		end
		acumulado = 0
		local j = conductor()
		if not enganche or not j or not carro.Parent then
			if next(cedidos) then
				devolverMaletas()
			end
			return
		end
		local medio = carro.Size / 2 + Vector3.new(0.3, 2.5, 0.3)
		for _, parte in CollectionService:GetTagged("Carga") do
			if parte:IsA("BasePart") and parte.Parent and not parte.Anchored and not Agarre.portador(parte) then
				local l = carro.CFrame:PointToObjectSpace(parte.Position)
				local encima = math.abs(l.X) <= medio.X and l.Y >= 0 and l.Y <= medio.Y + carro.Size.Y and math.abs(l.Z) <= medio.Z
				if encima and not cedidos[parte] then
					cedidos[parte] = true
					propietario(parte, j)
				elseif not encima and cedidos[parte] then
					cedidos[parte] = nil
					propietario(parte, nil)
				end
			end
		end
	end)
end

return Vehiculos
