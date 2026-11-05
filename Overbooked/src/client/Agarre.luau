--!strict
local CollectionService = game:GetService("CollectionService")
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Manos = require(script.Parent.Manos)
local Piloto = require(script.Parent.Piloto)
local Sonido = require(script.Parent.Sonido)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAgarrar = Remotos:WaitForChild("Agarrar") :: RemoteEvent
local RemotoSoltar = Remotos:WaitForChild("Soltar") :: RemoteEvent
local RemotoSostener = Remotos:WaitForChild("Sostener") :: RemoteEvent
local RemotoUsar = Remotos:WaitForChild("Usar") :: RemoteEvent

local Agarre = {}

local jugador = Players.LocalPlayer
local sostenido: Instance? = nil
local raiz: BasePart? = nil
local adjunto: Attachment? = nil
local posicion: AlignPosition? = nil
local orientacion: AlignOrientation? = nil
local distancia = 3.5
local confirmarAntes = 0
local usando = false
local ultimoUso = 0
local apuntado: Instance? = nil
local parametros = RaycastParams.new()
parametros.FilterType = Enum.RaycastFilterType.Exclude
parametros.RespectCanCollide = true

local GRANDES = { Pasajero = true, Cocodrilo = true, Jaula = true, Caja = true, CajaFragil = true, Carrito = true }

local function agarrable(instancia: Instance): Instance?
	local actual: Instance? = instancia
	while actual and actual ~= Workspace do
		if CollectionService:HasTag(actual, "Agarrable") then
			return actual
		end
		actual = actual.Parent
	end
	return nil
end

local function raizDe(objeto: Instance): BasePart?
	if objeto:IsA("BasePart") then
		return objeto
	elseif objeto:IsA("Model") then
		return objeto.PrimaryPart
	end
	return nil
end

local function tipoDe(objeto: Instance): string
	local t = objeto:GetAttribute("Tipo")
	if typeof(t) == "string" then
		return t
	end
	if CollectionService:HasTag(objeto, "Pasajero") then
		return "Pasajero"
	end
	return objeto.Name
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
	sostenido, raiz = nil, nil
	usando = false
end

local function empezar(objeto: Instance)
	limpiar()
	local r = raizDe(objeto)
	if not r then
		return
	end
	sostenido, raiz = objeto, r
	local tipo = tipoDe(objeto)
	local enMano = Manos.estilo(tipo).modo ~= "dos"
	distancia = if GRANDES[tipo] then 5.2 else 3.4
	local masa = r.AssemblyMass
	local a = Instance.new("Attachment")
	a.Name = "AgarreLocal"
	a.Parent = r
	local p = Instance.new("AlignPosition")
	p.Mode = Enum.PositionAlignmentMode.OneAttachment
	p.Attachment0 = a
	p.MaxForce = math.max(2000, masa * 900)
	p.MaxVelocity = if GRANDES[tipo] then 28 else 60
	p.Responsiveness = if enMano then 200 else math.clamp(160 / math.max(masa, 1), 8, 45)
	p.Position = r.Position
	p.Parent = r
	local o = Instance.new("AlignOrientation")
	o.Mode = Enum.OrientationAlignmentMode.OneAttachment
	o.Attachment0 = a
	o.MaxTorque = math.max(2000, masa * 900)
	o.Responsiveness = if enMano then 200 else 22
	o.CFrame = r.CFrame
	o.Parent = r
	adjunto, posicion, orientacion = a, p, o
	confirmarAntes = os.clock() + 1
	Manos.agarrar()
end

local function soltar(lanzar: boolean)
	local r = raiz
	if not sostenido or not r then
		return
	end
	local camara = Workspace.CurrentCamera
	local velocidad = if lanzar then camara.CFrame.LookVector * Config.AGARRE.LANZAMIENTO + Vector3.new(0, 7, 0) else r.AssemblyLinearVelocity
	limpiar()
	r.AssemblyLinearVelocity = velocidad
	RemotoSoltar:FireServer(velocidad)
	if lanzar then
		Sonido.reproducir("Lanzar", nil, 0.8)
	end
end

local function rayo(): RaycastResult?
	local camara = Workspace.CurrentCamera
	local personaje = jugador.Character
	parametros.FilterDescendantsInstances = if personaje then { personaje } else {}
	local centro = camara.ViewportSize / 2
	local r = camara:ViewportPointToRay(centro.X, centro.Y)
	return Workspace:Raycast(r.Origin, r.Direction * Config.AGARRE.DISTANCIA, parametros)
end

local function intentarAgarrar()
	if sostenido or Piloto.activo() then
		return
	end
	local personaje = jugador.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	if not personaje or not humanoide or humanoide.SeatPart or personaje:GetAttribute("Ragdoll") then
		return
	end
	local resultado = rayo()
	local objeto = resultado and agarrable(resultado.Instance)
	if not objeto then
		return
	end
	local portador = objeto:GetAttribute("Portador")
	if typeof(portador) == "number" and portador ~= 0 and portador ~= jugador.UserId then
		return
	end
	RemotoAgarrar:FireServer(objeto)
	empezar(objeto)
	Sonido.reproducir("Coger", nil, 0.6)
end

function Agarre.sostenido(): Instance?
	return sostenido
end

function Agarre.apuntado(): Instance?
	return apuntado
end

function Agarre.tipo(objeto: Instance): string
	return tipoDe(objeto)
end

function Agarre.iniciar()
	ContextActionService:BindAction("Agarrar", function(_, estado)
		if estado == Enum.UserInputState.Begin then
			if sostenido then
				soltar(false)
			else
				intentarAgarrar()
			end
		end
		return Enum.ContextActionResult.Pass
	end, true, Enum.UserInputType.MouseButton1, Enum.KeyCode.ButtonR2)
	ContextActionService:SetTitle("Agarrar", "Coger")
	ContextActionService:BindAction("Lanzar", function(_, estado)
		if estado == Enum.UserInputState.Begin and sostenido then
			soltar(true)
		end
		return Enum.ContextActionResult.Pass
	end, true, Enum.UserInputType.MouseButton2, Enum.KeyCode.ButtonL2)
	ContextActionService:SetTitle("Lanzar", "Lanzar")
	ContextActionService:BindAction("Usar", function(_, estado)
		usando = estado == Enum.UserInputState.Begin or estado == Enum.UserInputState.Change
		return Enum.ContextActionResult.Pass
	end, true, Enum.KeyCode.F, Enum.KeyCode.ButtonX)
	ContextActionService:SetTitle("Usar", "Usar")

	RemotoSostener.OnClientEvent:Connect(function(objeto)
		if typeof(objeto) == "Instance" then
			empezar(objeto)
			confirmarAntes = 0
		else
			limpiar()
		end
	end)

	jugador.CharacterAdded:Connect(function()
		limpiar()
	end)

	RunService.PreSimulation:Connect(function(dt)
		local camara = Workspace.CurrentCamera
		local resultado = if not sostenido then rayo() else nil
		apuntado = if resultado then agarrable(resultado.Instance) else nil
		local objeto, r = sostenido, raiz
		if not objeto or not r then
			return
		end
		local personaje = jugador.Character
		if not objeto.Parent or not personaje or personaje:GetAttribute("Ragdoll") then
			limpiar()
			return
		end
		local portador = objeto:GetAttribute("Portador")
		if portador == jugador.UserId then
			confirmarAntes = 0
		elseif confirmarAntes ~= 0 and os.clock() > confirmarAntes then
			limpiar()
			return
		elseif typeof(portador) == "number" and portador ~= 0 and portador ~= jugador.UserId then
			limpiar()
			return
		end
		local cf = camara.CFrame
		local p = posicion
		local o = orientacion
		local tipo = tipoDe(objeto)
		local estilo = Manos.estilo(tipo)
		local mano, punto = Manos.punto(personaje)
		local cuerpo = personaje.PrimaryPart
		local destino = if estilo.modo ~= "dos" and mano and punto and cuerpo then Manos.marco(estilo, mano.CFrame, punto, cuerpo.CFrame) * Manos.desfase(estilo, r.Size) else nil
		if p then
			p.Position = if destino and cuerpo then destino.Position + cuerpo.AssemblyLinearVelocity * dt else cf.Position + cf.LookVector * distancia - cf.UpVector * 0.7
		end
		if o and destino then
			o.CFrame = destino.Rotation
		elseif o then
			if tipo == "Extintor" or tipo == "Llave" or tipo == "Piolet" then
				o.CFrame = cf.Rotation
			else
				local plano = cf.LookVector * Vector3.new(1, 0, 1)
				o.CFrame = if plano.Magnitude > 0.01 then CFrame.lookAt(Vector3.zero, plano) else cf.Rotation
			end
		end
		if usando and os.clock() - ultimoUso >= Config.HERRAMIENTAS.CADENCIA then
			ultimoUso = os.clock()
			RemotoUsar:FireServer(cf.LookVector)
			local propia = personaje:FindFirstChild("HumanoidRootPart")
			if tipoDe(objeto) == "Extintor" and Workspace.Gravity < 60 and propia and propia:IsA("BasePart") then
				propia.AssemblyLinearVelocity -= cf.LookVector * 4
			end
		end
	end)
end

return Agarre
