--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
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
local antesDeAgarrar: { (Instance) -> () } = {}
local alSoltar: { (Player, Instance, BasePart) -> () } = {}

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
	if raiz.Anchored or not raiz:IsDescendantOf(workspace) then
		return
	end
	pcall(function()
		if jugador then
			raiz:SetNetworkOwner(jugador)
		else
			raiz:SetNetworkOwnershipAuto()
		end
	end)
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
	if velocidad and not raiz.Anchored then
		raiz.AssemblyLinearVelocity = velocidad
	end
	local marca = os.clock() + Config.AGARRE.DEVOLVER_PROPIEDAD
	devoluciones[objeto] = marca
	task.delay(Config.AGARRE.DEVOLVER_PROPIEDAD, function()
		if devoluciones[objeto] == marca and not portadores[objeto] and raiz.Parent then
			devoluciones[objeto] = nil
			propiedad(raiz, nil)
		end
	end)
	for _, f in alSoltar do
		task.spawn(f, jugador, objeto, raiz)
	end
end

local function tomar(jugador: Player, objeto: Instance): boolean
	if portadores[objeto] or not Personajes.vivo(jugador) or Personajes.enRagdoll(jugador) then
		return false
	end
	for _, f in antesDeAgarrar do
		f(objeto)
	end
	local raiz = Agarre.raiz(objeto)
	if not raiz or raiz.Anchored then
		return false
	end
	soltarInterno(jugador, nil)
	sostenidos[jugador] = objeto
	portadores[objeto] = jugador
	devoluciones[objeto] = nil
	objeto:SetAttribute("Portador", jugador.UserId)
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
		soltarInterno(jugador, nil)
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

function Agarre.alSoltar(f: (Player, Instance, BasePart) -> ())
	table.insert(alSoltar, f)
end

function Agarre.iniciar()
	RemotoAgarrar.OnServerEvent:Connect(function(jugador, objeto)
		if typeof(objeto) ~= "Instance" then
			return
		end
		local agarrable = Agarre.agarrable(objeto)
		if not agarrable then
			return
		end
		local raiz = Agarre.raiz(agarrable)
		local raizJugador = Personajes.raiz(jugador)
		if not raiz or not raizJugador then
			return
		end
		if (raiz.Position - raizJugador.Position).Magnitude > Config.AGARRE.DISTANCIA + 4 then
			RemotoSostener:FireClient(jugador, nil)
			return
		end
		if not tomar(jugador, agarrable) then
			RemotoSostener:FireClient(jugador, nil)
		end
	end)

	RemotoSoltar.OnServerEvent:Connect(function(jugador, velocidad)
		local v: Vector3? = nil
		if typeof(velocidad) == "Vector3" and velocidad == velocidad then
			v = if velocidad.Magnitude > Config.AGARRE.VELOCIDAD_MAX then velocidad.Unit * Config.AGARRE.VELOCIDAD_MAX else velocidad
		end
		soltarInterno(jugador, v)
	end)

	Players.PlayerRemoving:Connect(function(jugador)
		soltarInterno(jugador, nil)
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
