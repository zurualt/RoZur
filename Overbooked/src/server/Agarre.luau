--!strict
local CollectionService = game:GetService("CollectionService")
local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)
local Personajes = require(script.Parent.Personajes)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAgarrar = Remotos:WaitForChild("Agarrar") :: RemoteEvent
local RemotoSoltar = Remotos:WaitForChild("Soltar") :: RemoteEvent
local RemotoSostener = Remotos:WaitForChild("Sostener") :: RemoteEvent

local Agarre = {}

local sostenidos: { [Player]: Instance } = {}
local portadores: { [Instance]: Player } = {}
local devoluciones: { [Instance]: number } = {}
local esperas: { [Player]: number } = {}
local antesDeAgarrar: { (Instance) -> () } = {}
local alSoltar: { (Player, Instance, BasePart, Vector3?) -> () } = {}
local permisos: { (Player, Instance) -> boolean } = {}

function Agarre.raiz(objeto: Instance): BasePart?
	if objeto:IsA("BasePart") then
		return objeto
	elseif objeto:IsA("Model") then
		return objeto.PrimaryPart
	end
	return nil
end

function Agarre.agarrable(instancia: Instance): Instance?
	local actual: Instance? = instancia
	while actual and actual ~= workspace do
		if CollectionService:HasTag(actual, "Agarrable") then
			return actual
		end
		actual = actual.Parent
	end
	return nil
end

local function marcarPersonaje(jugador: Player, tipo: string)
	local personaje = jugador.Character
	if personaje then
		personaje:SetAttribute("Sosteniendo", tipo)
	end
end

local function propiedad(raiz: BasePart, jugador: Player?)
	if raiz.Anchored or not raiz:IsDescendantOf(Workspace) then
		return
	end
	pcall(function()
		raiz:SetNetworkOwner(jugador)
	end)
end

local function grupo(objeto: Instance, nombre: string)
	if objeto:IsA("BasePart") then
		objeto.CollisionGroup = nombre
	end
	for _, d in objeto:GetDescendants() do
		if d:IsA("BasePart") and d.CanCollide then
			d.CollisionGroup = nombre
		end
	end
end

function Agarre.delServidor(parte: BasePart): boolean
	local ok, dueno = pcall(function()
		return parte:GetNetworkOwner()
	end)
	return ok and dueno == nil and not devoluciones[parte]
end

local function soltarInterno(jugador: Player, velocidad: Vector3?)
	local objeto = sostenidos[jugador]
	if not objeto then
		return
	end
	sostenidos[jugador] = nil
	portadores[objeto] = nil
	marcarPersonaje(jugador, "")
	if not objeto.Parent then
		return
	end
	objeto:SetAttribute("Portador", 0)
	local raiz = Agarre.raiz(objeto)
	if not raiz then
		return
	end
	local marca = os.clock() + Config.AGARRE.DEVOLVER_PROPIEDAD
	devoluciones[objeto] = marca
	task.delay(Config.AGARRE.DEVOLVER_PROPIEDAD, function()
		if devoluciones[objeto] == marca then
			devoluciones[objeto] = nil
			if not portadores[objeto] and raiz.Parent then
				grupo(objeto, "Default")
				propiedad(raiz, nil)
			end
		end
	end)
	for _, f in alSoltar do
		task.spawn(f, jugador, objeto, raiz, velocidad)
	end
end

local function tomar(jugador: Player, objeto: Instance): boolean
	if portadores[objeto] or not Personajes.vivo(jugador) or Personajes.enRagdoll(jugador) then
		return false
	end
	for _, f in permisos do
		if not f(jugador, objeto) then
			return false
		end
	end
	for _, f in antesDeAgarrar do
		f(objeto)
	end
	local raiz = Agarre.raiz(objeto)
	if not raiz or raiz.Anchored then
		return false
	end
	soltarInterno(jugador)
	sostenidos[jugador] = objeto
	portadores[objeto] = jugador
	devoluciones[objeto] = nil
	objeto:SetAttribute("Portador", jugador.UserId)
	grupo(objeto, "Sostenido")
	local tipo = objeto:GetAttribute("Tipo")
	marcarPersonaje(jugador, if typeof(tipo) == "string" then tipo else objeto.Name)
	propiedad(raiz, jugador)
	return true
end

function Agarre.forzar(jugador: Player, objeto: Instance)
	if tomar(jugador, objeto) then
		RemotoSostener:FireClient(jugador, objeto)
	end
end

function Agarre.soltar(jugador: Player)
	if sostenidos[jugador] then
		soltarInterno(jugador)
		RemotoSostener:FireClient(jugador, nil)
	end
end

function Agarre.soltarObjeto(objeto: Instance)
	local jugador = portadores[objeto]
	if jugador then
		Agarre.soltar(jugador)
	end
end

function Agarre.soltarTodo()
	for jugador in sostenidos do
		Agarre.soltar(jugador)
	end
end

function Agarre.sostenido(jugador: Player): Instance?
	local objeto = sostenidos[jugador]
	if objeto and objeto.Parent then
		return objeto
	end
	return nil
end

function Agarre.tipo(jugador: Player): string?
	local objeto = Agarre.sostenido(jugador)
	if not objeto then
		return nil
	end
	local tipo = objeto:GetAttribute("Tipo")
	return if typeof(tipo) == "string" then tipo else nil
end

function Agarre.portador(objeto: Instance): Player?
	return portadores[objeto]
end

function Agarre.consumir(jugador: Player)
	local objeto = sostenidos[jugador]
	if not objeto then
		return
	end
	sostenidos[jugador] = nil
	portadores[objeto] = nil
	marcarPersonaje(jugador, "")
	RemotoSostener:FireClient(jugador, nil)
	objeto:Destroy()
end

function Agarre.antesDeAgarrar(f: (Instance) -> ())
	table.insert(antesDeAgarrar, f)
end

function Agarre.permitir(f: (Player, Instance) -> boolean)
	table.insert(permisos, f)
end

function Agarre.alSoltar(f: (Player, Instance, BasePart, Vector3?) -> ())
	table.insert(alSoltar, f)
end

local function visible(jugador: Player, raiz: BasePart, agarrable: Instance): boolean
	local personaje = jugador.Character
	local cabeza = personaje and personaje:FindFirstChild("Head")
	if not personaje or not cabeza or not cabeza:IsA("BasePart") then
		return false
	end
	local parametros = RaycastParams.new()
	parametros.FilterType = Enum.RaycastFilterType.Exclude
	parametros.RespectCanCollide = true
	parametros.FilterDescendantsInstances = { personaje, agarrable }
	local delta = raiz.Position - cabeza.Position
	return Workspace:Raycast(cabeza.Position, delta, parametros) == nil
end

function Agarre.iniciar()
	pcall(function()
		PhysicsService:RegisterCollisionGroup("Sostenido")
		PhysicsService:RegisterCollisionGroup("Jugadores")
		PhysicsService:CollisionGroupSetCollidable("Sostenido", "Jugadores", false)
	end)
	RemotoAgarrar.OnServerEvent:Connect(function(jugador, objeto)
		local ahora = os.clock()
		if typeof(objeto) ~= "Instance" then
			return
		end
		if (esperas[jugador] or 0) > ahora then
			RemotoSostener:FireClient(jugador, nil)
			return
		end
		esperas[jugador] = ahora + 0.25
		local agarrable = Agarre.agarrable(objeto)
		if not agarrable then
			return
		end
		local raiz = Agarre.raiz(agarrable)
		local raizJugador = Personajes.raiz(jugador)
		if not raiz or not raizJugador then
			return
		end
		if (raiz.Position - raizJugador.Position).Magnitude > Config.AGARRE.DISTANCIA + 4 or not visible(jugador, raiz, agarrable) then
			RemotoSostener:FireClient(jugador, nil)
			return
		end
		if not tomar(jugador, agarrable) then
			RemotoSostener:FireClient(jugador, nil)
		end
	end)

	RemotoSoltar.OnServerEvent:Connect(function(jugador, velocidad)
		local v: Vector3? = nil
		if typeof(velocidad) == "Vector3" and velocidad == velocidad and velocidad.Magnitude <= Config.AGARRE.LANZAMIENTO + 12 then
			v = velocidad
		end
		soltarInterno(jugador, v)
	end)

	Players.PlayerRemoving:Connect(function(jugador)
		soltarInterno(jugador)
		esperas[jugador] = nil
	end)

	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		if acumulado < 0.5 then
			return
		end
		acumulado = 0
		for jugador, objeto in sostenidos do
			local raiz = Agarre.raiz(objeto)
			local raizJugador = Personajes.raiz(jugador)
			if not objeto.Parent or not raiz or not raizJugador or not Personajes.vivo(jugador) or Personajes.enRagdoll(jugador) or (raiz.Position - raizJugador.Position).Magnitude > Config.AGARRE.DISTANCIA_MAX then
				Agarre.soltar(jugador)
			end
		end
	end)
end

return Agarre
