--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local VFX = require(ReplicatedStorage.Shared.VFX)
local Avion = require(script.Parent.Avion)
local Pasajeros = require(script.Parent.Pasajeros)

local Estadisticas = require(script.Parent.Estadisticas)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local RemotoDisparar = Remotos:WaitForChild("Disparar") :: RemoteEvent
local RemotoSacudida = Remotos:WaitForChild("Sacudida") :: UnreliableRemoteEvent

type Pirata = {
	carpeta: Folder,
	radio: number,
	velocidad: number,
	fase: number,
	altura: number,
	inicio: number,
	vida: number,
	proximoDisparo: number,
}

local Piratas = {}

local CENTRO = Vector3.new(0, 105, -18)
local RADIO_IMPACTO = 7
local RECOMPENSA = 90

local avion = Workspace:WaitForChild("Avion") :: Model
local carpeta = Instance.new("Folder")
carpeta.Name = "Piratas"
carpeta.Parent = avion
local torreta = avion:FindFirstChild("Torreta", true) :: Seat?
local piratas: { Pirata } = {}
local ultimoDisparo: { [Player]: number } = {}
local derribados = 0
local fin = 0
local rng = Random.new()

function Piratas.posicion(radio: number, velocidad: number, fase: number, altura: number, inicio: number, t: number): Vector3
	local a = fase + velocidad * (t - inicio)
	return CENTRO + Vector3.new(math.cos(a) * radio, altura + math.sin(a * 2.3) * 8, math.sin(a) * radio * 0.7)
end

local function chispazo()
	local punto = Vector3.new(rng:NextNumber(-7, 7), rng:NextNumber(101, 109), rng:NextNumber(-55, 15))
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.Transparency = 1
	p.Size = Vector3.one
	p.Position = punto
	p.Parent = carpeta
	VFX.chispas(p):Emit(30)
	task.delay(1, function()
		p:Destroy()
	end)
end

function Piratas.lanzar()
	Piratas.detener()
	local ahora = Workspace:GetServerTimeNow()
	for i = 1, rng:NextInteger(2, 3) do
		local f = Instance.new("Folder")
		f.Name = "Pirata" .. i
		local p: Pirata = {
			carpeta = f,
			radio = rng:NextNumber(85, 150),
			velocidad = rng:NextNumber(0.18, 0.3) * (if rng:NextNumber() < 0.5 then -1 else 1),
			fase = rng:NextNumber(0, math.pi * 2),
			altura = rng:NextNumber(-14, 24),
			inicio = ahora,
			vida = 100,
			proximoDisparo = os.clock() + rng:NextNumber(4, 8),
		}
		f:SetAttribute("Radio", p.radio)
		f:SetAttribute("Velocidad", p.velocidad)
		f:SetAttribute("Fase", p.fase)
		f:SetAttribute("Altura", p.altura)
		f:SetAttribute("Inicio", p.inicio)
		f:SetAttribute("Vida", p.vida)
		f.Parent = carpeta
		table.insert(piratas, p)
	end
	fin = os.clock() + 70
	RemotoAviso:FireAllClients("¡AVIONES PIRATA! Corre a la torreta del ala izquierda", "peligro")
	Pasajeros.asustar(0.4)
end

function Piratas.detener()
	for _, p in piratas do
		p.carpeta:Destroy()
	end
	table.clear(piratas)
	fin = 0
end

function Piratas.bonus(): number
	return derribados * RECOMPENSA
end

function Piratas.reiniciar()
	Piratas.detener()
	derribados = 0
end

function Piratas.iniciar()
	RemotoDisparar.OnServerEvent:Connect(function(jugador, direccion)
		local asiento = torreta
		if not asiento or typeof(direccion) ~= "Vector3" or direccion ~= direccion or direccion.Magnitude < 0.5 or direccion.Magnitude > 1.5 then
			return
		end
		local ocupante = asiento.Occupant
		if not ocupante or ocupante.Parent ~= jugador.Character then
			return
		end
		local ahora = os.clock()
		if (ultimoDisparo[jugador] or 0) > ahora then
			return
		end
		ultimoDisparo[jugador] = ahora + 0.11
		local dir = direccion.Unit
		local plano = dir * Vector3.new(1, 0, 1)
		if plano.Magnitude > 0.05 then
			asiento:SetAttribute("Mira", math.floor(math.atan2(-plano.X, -plano.Z) * 100) / 100)
		end
		local origen = asiento.Position + Vector3.new(0, 2.5, 0)
		local t = Workspace:GetServerTimeNow()
		for i = #piratas, 1, -1 do
			local p = piratas[i]
			local pos = Piratas.posicion(p.radio, p.velocidad, p.fase, p.altura, p.inicio, t)
			local v = pos - origen
			local proyeccion = v:Dot(dir)
			if proyeccion > 0 and (v - dir * proyeccion).Magnitude < RADIO_IMPACTO then
				p.vida -= 12
				p.carpeta:SetAttribute("Vida", math.max(0, p.vida))
				if p.vida <= 0 then
					derribados += 1
					Estadisticas.sumar(jugador, "piratas")
					table.remove(piratas, i)
					RemotoAviso:FireAllClients(`¡{jugador.DisplayName} ha derribado un pirata! +{RECOMPENSA}`, "bien")
					local f = p.carpeta
					task.delay(2, function()
						f:Destroy()
					end)
				end
				break
			end
		end
	end)
	Players.PlayerRemoving:Connect(function(jugador)
		ultimoDisparo[jugador] = nil
	end)
	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		if acumulado < 0.25 or #piratas == 0 then
			return
		end
		acumulado = 0
		local ahora = os.clock()
		if Avion.estado.enTierra then
			Piratas.detener()
			return
		end
		if ahora > fin then
			RemotoAviso:FireAllClients("Los piratas se retiran", "info")
			Piratas.detener()
			return
		end
		for _, p in piratas do
			if ahora >= p.proximoDisparo then
				p.proximoDisparo = ahora + rng:NextNumber(3.5, 6.5)
				Avion.danar(1.6)
				chispazo()
				RemotoSacudida:FireAllClients(0.3)
				Pasajeros.asustar(0.1)
			end
		end
	end)
end

return Piratas
