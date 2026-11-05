--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Agarre = require(script.Parent.Agarre)
local Pasajeros = require(script.Parent.Pasajeros)
local Personajes = require(script.Parent.Personajes)
local Rafagas = require(script.Parent.Rafagas)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoUsar = Remotos:WaitForChild("Usar") :: RemoteEvent

local Bofetadas = {}

local ESPERA = 0.6
local ALCANCE = 5
local ARRIBA = Vector3.new(0, 1, 0)
local PLANO = Vector3.new(1, 0, 1)

local remoto = Instance.new("RemoteEvent")
remoto.Name = "Bofetada"
remoto.Parent = Remotos
local ultimas: { [Player]: number } = {}
local herramientas: { [Player]: number } = {}
local golpeados: { [Model]: number } = setmetatable({}, { __mode = "k" }) :: any

local function mirada(raiz: BasePart, valor: unknown): Vector3
	if typeof(valor) == "Vector3" and valor == valor and valor.Magnitude > 0.5 and valor.Magnitude < 1.5 then
		return valor.Unit
	end
	return raiz.CFrame.LookVector
end

local function companero(jugador: Player, origen: Vector3, dir: Vector3): (Player?, number)
	local mejor: Player? = nil
	local distancia = ALCANCE
	for _, otro in Players:GetPlayers() do
		local r = if otro ~= jugador then Personajes.raiz(otro) else nil
		if r then
			local delta = r.Position + ARRIBA - origen
			local d = delta.Magnitude
			if d < distancia and d > 0.1 and delta.Unit:Dot(dir) > 0.45 then
				mejor, distancia = otro, d
			end
		end
	end
	return mejor, distancia
end

local function devolver(jugador: Player, pasajero: Model)
	local r = Personajes.raiz(jugador)
	local c = pasajero.PrimaryPart
	if not r or not c or not pasajero.Parent or not Personajes.vivo(jugador) then
		return
	end
	local d = (r.Position - c.Position) * PLANO
	local dir = if d.Magnitude > 0.1 then d.Unit else Vector3.xAxis
	remoto:FireAllClients(r.Position + ARRIBA * 1.8, dir, "Revancha", jugador)
	Personajes.ragdoll(jugador, 1, dir * 18 + ARRIBA * 8)
end

local function golpearPasajero(jugador: Player, pasajero: Model, dir: Vector3, herramienta: boolean)
	if Pasajeros.abofetear(pasajero, dir, herramienta) then
		task.delay(0.45, devolver, jugador, pasajero)
	end
end

local function abofetear(jugador: Player, valor: unknown)
	local ahora = os.clock()
	if (ultimas[jugador] or 0) > ahora then
		return
	end
	ultimas[jugador] = ahora + ESPERA
	local raiz = Personajes.raiz(jugador)
	if not raiz or not Personajes.vivo(jugador) or Personajes.enRagdoll(jugador) or Agarre.sostenido(jugador) then
		return
	end
	local dir = mirada(raiz, valor)
	local origen = raiz.Position + ARRIBA * 1.5
	local pasajero = Pasajeros.cercano(origen + dir * 2.4, 2.6)
	local cuerpo = if pasajero then pasajero.PrimaryPart else nil
	local otro, distancia = companero(jugador, origen, dir)
	if pasajero and cuerpo and (not otro or (cuerpo.Position - origen).Magnitude < distancia) then
		remoto:FireAllClients(cuerpo.Position + ARRIBA * 1.6, dir, "Pasajero", jugador)
		golpearPasajero(jugador, pasajero, dir, false)
	elseif otro then
		local r = Personajes.raiz(otro)
		if r then
			remoto:FireAllClients(r.Position + ARRIBA * 1.8, dir, "Tripulante", jugador)
			Personajes.ragdoll(otro, 0.9, dir * 16 + ARRIBA * 7)
		end
	end
end

local function herramienta(jugador: Player, valor: unknown)
	local tipo = Agarre.tipo(jugador)
	if tipo ~= "Llave" and tipo ~= "Piolet" then
		return
	end
	local ahora = os.clock()
	local raiz = Personajes.raiz(jugador)
	if (herramientas[jugador] or 0) > ahora or not raiz or Personajes.enRagdoll(jugador) then
		return
	end
	local dir = mirada(raiz, valor)
	local pasajero = Pasajeros.cercano(raiz.Position + ARRIBA * 1.5 + dir * 2, 1.8)
	if not pasajero or (golpeados[pasajero] or 0) > ahora then
		return
	end
	herramientas[jugador] = ahora + 0.5
	golpeados[pasajero] = ahora + 4
	local c = pasajero.PrimaryPart
	if c then
		Rafagas.lanzar("Bonk", c.Position + ARRIBA * 2, 0.9)
	end
	golpearPasajero(jugador, pasajero, dir, true)
end

function Bofetadas.iniciar()
	remoto.OnServerEvent:Connect(abofetear)
	RemotoUsar.OnServerEvent:Connect(herramienta)
	Players.PlayerRemoving:Connect(function(jugador)
		ultimas[jugador] = nil
		herramientas[jugador] = nil
	end)
end

return Bofetadas
