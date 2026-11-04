--!strict
local CollectionService = game:GetService("CollectionService")
local Debris = game:GetService("Debris")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Agarre = require(script.Parent.Agarre)
local Avion = require(script.Parent.Avion)
local Carga = require(script.Parent.Carga)
local Objetos = require(script.Parent.Objetos)
local Pasajeros = require(script.Parent.Pasajeros)
local Peligros = require(script.Parent.Peligros)
local Personajes = require(script.Parent.Personajes)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent

type Charco = { parte: BasePart, fin: number, tipo: string }
type Lanzamiento = { jugador: Player, hora: number }

local Interacciones = {}

local avion = Workspace:WaitForChild("Avion") :: Model
local carpetaPasajeros = avion:WaitForChild("Pasajeros")
local carpetaPeligros = avion:WaitForChild("Peligros")
local previas: { [BasePart]: Vector3 } = setmetatable({}, { __mode = "k" }) :: any
local posiciones: { [BasePart]: Vector3 } = setmetatable({}, { __mode = "k" }) :: any
local enfriados: { [BasePart]: number } = setmetatable({}, { __mode = "k" }) :: any
local lanzamientos: { [BasePart]: Lanzamiento } = setmetatable({}, { __mode = "k" }) :: any
local charcos: { Charco } = {}
local resbalones: { [Player]: number } = {}
local rng = Random.new()
local parametros = RaycastParams.new()
parametros.FilterType = Enum.RaycastFilterType.Include

local LIQUIDOS = { Cafe = Color3.fromRGB(111, 64, 36), Agua = Color3.fromRGB(143, 211, 244) }

local function dentro(p: Vector3): boolean
	return math.abs(p.X) < 6.7 and p.Y > 99 and p.Y < 111 and p.Z > -62 and p.Z < 22
end

local function salpicar(posicion: Vector3, tipo: string)
	local marca = Instance.new("Part")
	marca.Anchored = true
	marca.CanCollide = false
	marca.CanQuery = false
	marca.CanTouch = false
	marca.Transparency = 1
	marca.Size = Vector3.one
	marca.Position = posicion
	marca.Parent = carpetaPeligros
	VFX.salpicadura(marca, LIQUIDOS[tipo] or Color3.new(1, 1, 1)):Emit(28)
	Debris:AddItem(marca, 1.5)
end

local function charco(posicion: Vector3, tipo: string)
	if not dentro(posicion) then
		return
	end
	local p = Instance.new("Part")
	p.Name = "Charco"
	p.Shape = Enum.PartType.Cylinder
	local diametro = rng:NextNumber(2.6, 3.6)
	p.Size = Vector3.new(0.05, diametro, diametro)
	p.CFrame = CFrame.new(posicion.X, Config.SUELO_Y + 0.07, posicion.Z) * CFrame.Angles(0, rng:NextNumber(0, 6.28), math.pi / 2)
	p.Color = LIQUIDOS[tipo] or Color3.new(1, 1, 1)
	p.Material = Enum.Material.Glass
	p.Transparency = if tipo == "Agua" then 0.45 else 0.25
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p:SetAttribute("Tipo", tipo)
	CollectionService:AddTag(p, "Charco")
	p.Parent = carpetaPeligros
	table.insert(charcos, { parte = p :: BasePart, fin = os.clock() + 30, tipo = tipo })
	while #charcos > 8 do
		local viejo = table.remove(charcos, 1)
		if viejo then
			viejo.parte:Destroy()
		end
	end
end

local function romperLiquido(o: BasePart, tipo: string)
	local pos = o.Position
	Agarre.soltarObjeto(o)
	o:Destroy()
	salpicar(pos, tipo)
	charco(pos, tipo)
end

local function derramar(o: BasePart)
	local raciones = o:GetAttribute("Raciones")
	local n = if typeof(raciones) == "number" then math.clamp(raciones, 0, 3) else 1
	local pos = o.Position
	local v = o.AssemblyLinearVelocity
	Agarre.soltarObjeto(o)
	o:Destroy()
	for i = 1, n do
		local h = Objetos.crear("Hamburguesa", CFrame.new(pos + Vector3.new(rng:NextNumber(-0.6, 0.6), 0.3 + i * 0.3, rng:NextNumber(-0.6, 0.6))))
		h.AssemblyLinearVelocity = v * 0.3 + Vector3.new(rng:NextNumber(-8, 8), rng:NextNumber(6, 12), rng:NextNumber(-8, 8))
	end
	Pasajeros.asustar(0.05, pos, 8)
end

local function jugadorDe(instancia: Instance): Player?
	for _, jugador in Players:GetPlayers() do
		local personaje = jugador.Character
		if personaje and instancia:IsDescendantOf(personaje) then
			return jugador
		end
	end
	return nil
end

local function impacto(o: BasePart, tipo: string, golpeado: Instance, velocidad: Vector3, ahora: number): boolean
	enfriados[o] = ahora + 0.5
	local rapidez = velocidad.Magnitude
	local fuerza = rapidez * math.sqrt(math.max(o.AssemblyMass, 0.05))
	local dir = if rapidez > 0.01 then velocidad.Unit else Vector3.yAxis
	local l = lanzamientos[o]
	local lanzador = if l and ahora - l.hora < 4 then l.jugador else nil
	local modelo = Pasajeros.desde(golpeado)
	if modelo then
		if Pasajeros.servirCon(modelo, o) then
			if lanzador then
				RemotoAviso:FireClient(lanzador, "🎯 ¡Pedido servido al vuelo!", "bien")
			end
			return o.Parent == nil
		end
		Pasajeros.golpear(modelo, fuerza, dir, if tipo == "Cafe" then "Quemado" elseif tipo == "Agua" then "Mojado" else "Golpe", Avion.estado.cinturones)
		if LIQUIDOS[tipo] then
			local pos = o.Position
			Agarre.soltarObjeto(o)
			o:Destroy()
			salpicar(pos, tipo)
			return true
		end
		return false
	end
	local cocodrilo = golpeado:FindFirstAncestorWhichIsA("Model")
	if cocodrilo and CollectionService:HasTag(cocodrilo, "Cocodrilo") then
		if fuerza > 18 and Carga.aturdir(3.5) and lanzador then
			RemotoAviso:FireClient(lanzador, "🐊💫 ¡Cocodrilo aturdido!", "bien")
		end
		return false
	end
	local jugador = jugadorDe(golpeado)
	if jugador and not (jugador == lanzador and l and ahora - l.hora < 0.8) and fuerza > 40 then
		Personajes.ragdoll(jugador, 1.1, dir * math.min(fuerza, 80) * 0.5 + Vector3.new(0, 18, 0))
		RemotoAviso:FireClient(jugador, if lanzador and lanzador ~= jugador then `💢 ¡{lanzador.DisplayName} te ha dado!` else "💢 ¡Cuidado con lo que vuela!", "peligro")
	end
	return false
end

local function incluir()
	local lista: { Instance } = { carpetaPasajeros }
	for _, c in CollectionService:GetTagged("Cocodrilo") do
		table.insert(lista, c)
	end
	for _, jugador in Players:GetPlayers() do
		local personaje = jugador.Character
		if personaje then
			table.insert(lista, personaje)
		end
	end
	parametros.FilterDescendantsInstances = lista
end

local function objetos(ahora: number)
	for _, o in CollectionService:GetTagged("Objeto") do
		if not o:IsA("BasePart") or not o.Parent or o.Anchored then
			continue
		end
		local tipo = o:GetAttribute("Tipo")
		if typeof(tipo) ~= "string" then
			continue
		end
		if Agarre.portador(o) then
			previas[o] = nil
			posiciones[o] = nil
			continue
		end
		local v = o.AssemblyLinearVelocity
		local pos = o.Position
		local previa = previas[o] or v
		local antes = posiciones[o] or pos
		previas[o] = v
		posiciones[o] = pos
		if tipo == "Agua" and Peligros.mojar(pos, 2, 100) then
			romperLiquido(o, tipo)
			continue
		end
		local rapida = if v.Magnitude > previa.Magnitude then v else previa
		if rapida.Magnitude > 16 and (enfriados[o] or 0) < ahora then
			local delta = pos - antes
			if delta.Magnitude > 0.05 then
				local radio = math.clamp(math.min(o.Size.X, o.Size.Y, o.Size.Z) / 2, 0.3, 1.2)
				local r = Workspace:Spherecast(antes, radio, delta + delta.Unit * 0.6, parametros)
				if r and impacto(o, tipo, r.Instance, rapida, ahora) then
					continue
				end
			end
		end
		local cambio = (v - previa).Magnitude
		if tipo == "Bandeja" and cambio > 26 then
			derramar(o)
		elseif LIQUIDOS[tipo] and cambio > 34 then
			romperLiquido(o, tipo)
		end
	end
end

local function resbalar(ahora: number)
	for i = #charcos, 1, -1 do
		local c = charcos[i]
		if ahora > c.fin or not c.parte.Parent then
			c.parte:Destroy()
			table.remove(charcos, i)
		elseif c.tipo == "Agua" then
			Peligros.mojar(c.parte.Position, c.parte.Size.Y / 2, 4)
		end
	end
	if #charcos == 0 then
		return
	end
	for _, jugador in Players:GetPlayers() do
		local raiz = Personajes.raiz(jugador)
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		if not raiz or not humanoide or humanoide.SeatPart or (resbalones[jugador] or 0) > ahora or Personajes.enRagdoll(jugador) then
			continue
		end
		local plano = raiz.AssemblyLinearVelocity * Vector3.new(1, 0, 1)
		if plano.Magnitude < 9 then
			continue
		end
		for _, c in charcos do
			local delta = (raiz.Position - c.parte.Position) * Vector3.new(1, 0, 1)
			if delta.Magnitude < c.parte.Size.Y / 2 and raiz.Position.Y - c.parte.Position.Y < 4.5 then
				resbalones[jugador] = ahora + 2.5
				Personajes.ragdoll(jugador, 1.1, plano.Unit * 30 + Vector3.new(0, 16, 0))
				RemotoAviso:FireClient(jugador, if c.tipo == "Cafe" then "☕ ¡Resbalón en el café!" else "💦 ¡Resbalón!", "peligro")
				break
			end
		end
	end
end

local function sacudida(magnitud: number)
	if magnitud < 0.4 then
		return
	end
	for _, jugador in Players:GetPlayers() do
		local objeto = Agarre.sostenido(jugador)
		local tipo = Agarre.tipo(jugador)
		if not objeto or not objeto:IsA("BasePart") then
			continue
		end
		if tipo == "Bandeja" and rng:NextNumber() < magnitud * 0.5 then
			local raciones = objeto:GetAttribute("Raciones")
			local n = if typeof(raciones) == "number" then raciones else 1
			local h = Objetos.crear("Hamburguesa", objeto.CFrame * CFrame.new(0, 0.7, 0))
			h.AssemblyLinearVelocity = Vector3.new(rng:NextNumber(-10, 10), rng:NextNumber(8, 14), rng:NextNumber(-10, 10))
			if n <= 1 then
				Agarre.consumir(jugador)
			else
				objeto:SetAttribute("Raciones", n - 1)
			end
			RemotoAviso:FireClient(jugador, "🍔 ¡Se te ha caído una hamburguesa!", "peligro")
		elseif tipo == "Cafe" and rng:NextNumber() < magnitud * 0.3 then
			local pos = objeto.Position
			Agarre.consumir(jugador)
			salpicar(pos, "Cafe")
			charco(pos, "Cafe")
			Personajes.ragdoll(jugador, 0.8, Vector3.new(0, 16, 0))
			RemotoAviso:FireClient(jugador, "☕ ¡Te has tirado el café encima!", "peligro")
		end
	end
end

function Interacciones.limpiar()
	for _, c in charcos do
		c.parte:Destroy()
	end
	table.clear(charcos)
end

function Interacciones.iniciar()
	Agarre.alSoltar(function(jugador, _, raiz)
		lanzamientos[raiz] = { jugador = jugador, hora = os.clock() }
		previas[raiz] = nil
		posiciones[raiz] = nil
	end)
	Peligros.alSacudir(sacudida)
	Players.PlayerRemoving:Connect(function(jugador)
		resbalones[jugador] = nil
	end)
	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		if acumulado < 0.1 then
			return
		end
		acumulado = 0
		local ahora = os.clock()
		incluir()
		objetos(ahora)
		resbalar(ahora)
	end)
end

return Interacciones
