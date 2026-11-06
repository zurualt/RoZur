--!strict
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local Personajes = require(script.Parent.Personajes)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder

type Sala = {
	n: number,
	centro: BasePart,
	dueno: Player?,
	modo: string,
	miembros: { Player },
	vetados: { [Player]: number },
	salir: boolean,
	publicado: string,
}

local Salas = {}

local MODOS = { "Amigos", "Publica", "Privada" }
local VETO = 90
local salas: { [number]: Sala } = {}
local amigos: { [string]: boolean } = {}
local consultando: { [string]: boolean } = {}
local avisados: { [Player]: number } = {}
local esperas: { [Player]: number } = {}
local fuera: { [Player]: boolean } = {}

local function dentro(sala: Sala, jugador: Player): boolean
	local raiz = Personajes.raiz(jugador)
	if not raiz then
		return false
	end
	local d = raiz.Position - sala.centro.Position
	return Vector3.new(d.X, 0, d.Z).Magnitude <= sala.centro.Size.Y / 2 and math.abs(d.Y) < 6
end

local function esAmigo(dueno: Player, otro: Player): boolean
	local clave = `{dueno.UserId}:{otro.UserId}`
	local v = amigos[clave]
	if v ~= nil then
		return v
	end
	if not consultando[clave] then
		consultando[clave] = true
		task.spawn(function()
			local ok, r = pcall(dueno.IsFriendsWithAsync, dueno, otro.UserId)
			amigos[clave] = ok and r == true
			consultando[clave] = nil
		end)
	end
	return false
end

local function avisar(jugador: Player, texto: string)
	local ahora = os.clock()
	if (avisados[jugador] or 0) > ahora then
		return
	end
	avisados[jugador] = ahora + 3
	RemotoAviso:FireClient(jugador, texto, "peligro")
end

local function echar(sala: Sala, jugador: Player, texto: string)
	local personaje = jugador.Character
	local raiz = Personajes.raiz(jugador)
	if personaje and raiz then
		local c = sala.centro.Position
		local d = (raiz.Position - c) * Vector3.new(1, 0, 1)
		local dir = if d.Magnitude > 0.1 then d.Unit else Vector3.xAxis
		local destino = Vector3.new(c.X, raiz.Position.Y, c.Z) + dir * (sala.centro.Size.Y / 2 + 3.5)
		personaje:PivotTo(CFrame.lookAt(destino, destino + dir))
	end
	avisar(jugador, texto)
end

local function nombre(sala: Sala): string
	local d = sala.dueno
	return if d then d.DisplayName else ""
end

local function puede(sala: Sala, jugador: Player): string?
	if (sala.vetados[jugador] or 0) > os.clock() then
		return `{nombre(sala)} te ha echado de su sala`
	end
	if #sala.miembros >= Config.LOBBY.MAX then
		return "Esta sala está llena"
	end
	if sala.modo == "Privada" then
		return `La sala de {nombre(sala)} está cerrada`
	end
	local d = sala.dueno
	if sala.modo == "Amigos" and d and not esAmigo(d, jugador) then
		return `La sala de {nombre(sala)} es solo para sus amigos`
	end
	return nil
end

local function publicar(sala: Sala, quedan: number)
	local d = sala.dueno
	local texto = ""
	if d and #sala.miembros > 0 then
		local ids = {}
		for _, m in sala.miembros do
			table.insert(ids, m.UserId)
		end
		texto = HttpService:JSONEncode({ d = d.UserId, m = sala.modo, j = ids, c = quedan })
	end
	if texto ~= sala.publicado then
		sala.publicado = texto
		Estado:SetAttribute(`Sala{sala.n}`, texto)
	end
end

local function salaDe(jugador: Player): Sala?
	for _, s in salas do
		if table.find(s.miembros, jugador) then
			return s
		end
	end
	return nil
end

function Salas.registrar(n: number, centro: BasePart)
	salas[n] = { n = n, centro = centro, dueno = nil, modo = MODOS[1], miembros = {}, vetados = {}, salir = false, publicado = "" }
end

function Salas.actualizar(n: number, saliendo: { [Player]: boolean }): { Player }
	local sala = salas[n]
	if not sala then
		return {}
	end
	for i = #sala.miembros, 1, -1 do
		local m = sala.miembros[i]
		if not m.Parent or saliendo[m] or fuera[m] or not dentro(sala, m) then
			table.remove(sala.miembros, i)
			fuera[m] = nil
		end
	end
	local d = sala.dueno
	if not d or not table.find(sala.miembros, d) then
		sala.dueno = sala.miembros[1]
		if sala.dueno == nil then
			sala.modo = MODOS[1]
			sala.salir = false
		elseif d and d.Parent then
			RemotoAviso:FireClient(sala.dueno, "Ahora eres el capitán de la sala", "info")
		end
	end
	for _, jugador in Players:GetPlayers() do
		if saliendo[jugador] or table.find(sala.miembros, jugador) or not dentro(sala, jugador) then
			continue
		end
		local otra = salaDe(jugador)
		if otra and otra ~= sala then
			continue
		end
		if not sala.dueno then
			sala.dueno = jugador
			sala.miembros = { jugador }
			RemotoAviso:FireClient(jugador, "¡Eres el capitán! Elige quién puede entrar y pulsa DESPEGAR", "bien")
			continue
		end
		local motivo = puede(sala, jugador)
		if motivo then
			echar(sala, jugador, motivo)
		else
			table.insert(sala.miembros, jugador)
		end
	end
	return table.clone(sala.miembros)
end

function Salas.pidioSalir(n: number): boolean
	local sala = salas[n]
	if sala and sala.salir then
		sala.salir = false
		return true
	end
	return false
end

function Salas.publicar(n: number, quedan: number)
	local sala = salas[n]
	if sala then
		publicar(sala, quedan)
	end
end

function Salas.estado(n: number): string?
	local sala = salas[n]
	if not sala or not sala.dueno then
		return nil
	end
	return if sala.modo == "Publica" then "ABIERTA" elseif sala.modo == "Amigos" then "AMIGOS" else "CERRADA"
end

function Salas.vaciar(n: number)
	local sala = salas[n]
	if sala then
		table.clear(sala.miembros)
		sala.dueno = nil
		sala.modo = MODOS[1]
		sala.salir = false
		publicar(sala, 0)
	end
end

local function pedir(jugador: Player, accion: unknown, dato: unknown)
	local ahora = os.clock()
	if (esperas[jugador] or 0) > ahora or typeof(accion) ~= "string" then
		return
	end
	esperas[jugador] = ahora + 0.3
	local sala = salaDe(jugador)
	if not sala then
		return
	end
	if accion == "salir" then
		fuera[jugador] = true
		echar(sala, jugador, "Has salido de la sala")
		return
	end
	if sala.dueno ~= jugador then
		return
	end
	if accion == "modo" then
		local i = table.find(MODOS, sala.modo) or 1
		sala.modo = MODOS[i % #MODOS + 1]
	elseif accion == "despegar" then
		sala.salir = true
	elseif accion == "expulsar" and typeof(dato) == "number" then
		local otro = Players:GetPlayerByUserId(dato)
		if otro and otro ~= jugador and table.find(sala.miembros, otro) then
			sala.vetados[otro] = ahora + VETO
			fuera[otro] = true
			echar(sala, otro, `{jugador.DisplayName} te ha echado de su sala`)
		end
	end
end

function Salas.iniciar()
	local remoto = Instance.new("RemoteEvent")
	remoto.Name = "Sala"
	remoto.Parent = Remotos
	remoto.OnServerEvent:Connect(pedir)
	Players.PlayerRemoving:Connect(function(jugador)
		avisados[jugador] = nil
		esperas[jugador] = nil
		fuera[jugador] = nil
		for _, s in salas do
			s.vetados[jugador] = nil
		end
	end)
end

return Salas
