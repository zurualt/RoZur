--!strict
local CollectionService = game:GetService("CollectionService")
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")
local Debris = game:GetService("Debris")
local Workspace = game:GetService("Workspace")

local Audio = require(ReplicatedStorage.Shared.Audio)

type Bucle = { sonido: Sound, objetivo: number, tono: number, base: number }

local Sonido = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local Estado = ReplicatedStorage:WaitForChild("Estado")
local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoSonido = Remotos:WaitForChild("Sonido") :: UnreliableRemoteEvent
local rng = Random.new()
local grupos: { [string]: SoundGroup } = {}
local bucles: { [string]: Bucle } = {}
local fuegos: { [Instance]: Sound } = {}
local recientes: { [string]: number } = {}
local musicaActiva = true

local bases: { [string]: number } = {}
local factores: { [string]: number } = {}

local function grupo(nombre: string, volumen: number): SoundGroup
	local g = Instance.new("SoundGroup")
	g.Name = nombre
	g.Volume = volumen * (factores[nombre] or 1)
	g.Parent = SoundService
	grupos[nombre] = g
	bases[nombre] = volumen
	return g
end

function Sonido.volumen(nombre: string, factor: number)
	factores[nombre] = math.clamp(factor, 0, 1)
	local g = grupos[nombre]
	if g then
		g.Volume = (bases[nombre] or 1) * factores[nombre]
	end
end

local function asset(nombre: string): string?
	local id = Audio.IDS[nombre]
	return if id then `rbxassetid://{id}` else nil
end

local function volumenBase(nombre: string): number
	local d = Audio.DATOS[nombre]
	return if d then d.volumen else 0.6
end

function Sonido.reproducir(nombre: string, donde: (Vector3 | BasePart)?, volumen: number?, tono: number?)
	local id = asset(nombre)
	if not id then
		return
	end
	local ahora = os.clock()
	local clave = if typeof(donde) == "Vector3" then nombre .. math.floor(donde.X / 4) .. math.floor(donde.Z / 4) else nombre
	if ahora - (recientes[clave] or 0) < 0.05 then
		return
	end
	recientes[clave] = ahora
	local s = Instance.new("Sound")
	s.SoundId = id
	s.Volume = volumenBase(nombre) * (volumen or 1)
	s.PlaybackSpeed = tono or rng:NextNumber(0.93, 1.07)
	s.SoundGroup = grupos.Efectos
	s.RollOffMode = Enum.RollOffMode.InverseTapered
	s.RollOffMinDistance = 10
	s.RollOffMaxDistance = 140
	if typeof(donde) == "Vector3" then
		local a = Instance.new("Attachment")
		a.WorldPosition = donde
		a.Parent = Workspace.Terrain
		s.Parent = a
		s.Ended:Once(function()
			a:Destroy()
		end)
		task.delay(12, function()
			if a.Parent then
				a:Destroy()
			end
		end)
	elseif typeof(donde) == "Instance" then
		s.Parent = donde
		s.Ended:Once(function()
			s:Destroy()
		end)
	else
		s.Parent = SoundService
		s.Ended:Once(function()
			s:Destroy()
		end)
	end
	local datos = Audio.DATOS[nombre]
	Debris:AddItem(s, (if datos then datos.duracion else 8) / math.max(s.PlaybackSpeed, 0.5) + 2)
	s:Play()
end

local function bucle(nombre: string, padre: Instance, g: SoundGroup, minimo: number?, maximo: number?): Bucle?
	local id = asset(nombre)
	if not id then
		return nil
	end
	local s = Instance.new("Sound")
	s.Name = nombre
	s.SoundId = id
	s.Looped = true
	s.Volume = 0
	s.SoundGroup = g
	s.RollOffMode = Enum.RollOffMode.InverseTapered
	s.RollOffMinDistance = minimo or 12
	s.RollOffMaxDistance = maximo or 200
	s.Parent = padre
	s:Play()
	local b: Bucle = { sonido = s, objetivo = 0, tono = 1, base = volumenBase(nombre) }
	bucles[nombre .. padre:GetFullName()] = b
	return b
end

local function dentro(p: Vector3): boolean
	return math.abs(p.X) < 7 and p.Y > 99 and p.Y < 111 and p.Z > -63 and p.Z < 23
end

local function numero(nombre: string): number
	local v = avion:GetAttribute(nombre)
	return if typeof(v) == "number" then v else 0
end

local function prepararFuego(f: Instance)
	if not f:IsA("BasePart") or fuegos[f] then
		return
	end
	local id = asset("FuegoLoop")
	if not id then
		return
	end
	local s = Instance.new("Sound")
	s.SoundId = id
	s.Looped = true
	s.Volume = volumenBase("FuegoLoop")
	s.SoundGroup = grupos.Efectos
	s.RollOffMinDistance = 6
	s.RollOffMaxDistance = 60
	s.Parent = f
	s:Play()
	fuegos[f] = s
end

local function pasajero(modelo: Instance)
	if not modelo:IsA("Model") then
		return
	end
	local cuerpo = modelo:WaitForChild("Cuerpo", 5)
	if not cuerpo or not cuerpo:IsA("BasePart") then
		return
	end
	local c1 = modelo:GetAttributeChangedSignal("ReaccionMarca"):Connect(function()
		local r = modelo:GetAttribute("Reaccion")
		Sonido.reproducir(if r == "Quemado" or r == "Mordisco" then "PasajeroGrito" else "PasajeroQueja", cuerpo, 0.9)
	end)
	local c2 = modelo:GetAttributeChangedSignal("Feliz"):Connect(function()
		Sonido.reproducir("PasajeroFeliz", cuerpo, 0.8)
	end)
	local c3 = modelo:GetAttributeChangedSignal("Enfado"):Connect(function()
		Sonido.reproducir("PasajeroQueja", cuerpo, 1, 0.85)
	end)
	modelo.Destroying:Once(function()
		c1:Disconnect()
		c2:Disconnect()
		c3:Disconnect()
	end)
end

local function cocodrilo(modelo: Instance)
	if not modelo:IsA("Model") then
		return
	end
	local cuerpo = modelo:WaitForChild("Cuerpo", 5)
	if not cuerpo or not cuerpo:IsA("BasePart") then
		return
	end
	Sonido.reproducir("Cocodrilo", cuerpo, 1.2)
	local c = modelo:GetAttributeChangedSignal("Estado"):Connect(function()
		if modelo:GetAttribute("Estado") == "Suelto" then
			Sonido.reproducir("Cocodrilo", cuerpo)
		end
	end)
	modelo.Destroying:Once(function()
		c:Disconnect()
	end)
end

local function pieza(nombre: string): BasePart?
	local p = avion:FindFirstChild(nombre, true)
	return if p and p:IsA("BasePart") then p else nil
end

function Sonido.alternarMusica()
	musicaActiva = not musicaActiva
end

function Sonido.iniciar()
	grupo("Efectos", 0.9)
	grupo("Ambiente", 0.7)
	grupo("Musica", 0.45)
	local function agrupar(d: Instance)
		if d:IsA("Sound") and d.SoundGroup == nil then
			d.SoundGroup = if d.Looped then grupos.Ambiente else grupos.Efectos
		end
	end
	for _, d in Workspace:GetDescendants() do
		agrupar(d)
	end
	Workspace.DescendantAdded:Connect(function(d)
		if d:IsA("Sound") then
			task.defer(agrupar, d)
		end
	end)
	local motores: { Bucle } = {}
	for _, lado in { "Izq", "Der" } do
		local m = pieza("Motor" .. lado)
		if m then
			local b = bucle("MotorAvion", m, grupos.Ambiente, 30, 600)
			if b then
				table.insert(motores, b)
			end
		end
	end
	local cuadro = pieza("Cuadro")
	local alarma = if cuadro then bucle("Alarma", cuadro, grupos.Efectos, 6, 40) else nil
	local cabina = bucle("AmbienteCabina", SoundService, grupos.Ambiente)
	local viento = bucle("VientoCabina", SoundService, grupos.Ambiente)
	local vientoFuera = bucle("VientoExterior", SoundService, grupos.Ambiente)
	local lluvia = bucle("Lluvia", SoundService, grupos.Ambiente)
	local terminal = bucle("AmbienteTerminal", SoundService, grupos.Ambiente)
	local musicas: { [string]: Bucle } = {}
	local pistas: { [string]: string } = { Aeropuerto = "MusicaAeropuerto", Vuelo = "MusicaVuelo", Caos = "MusicaCaos" }
	for clave, nombre in pistas do
		local b = bucle(nombre, SoundService, grupos.Musica)
		if b then
			musicas[clave] = b
		end
	end

	RemotoSonido.OnClientEvent:Connect(function(nombre, posicion)
		if typeof(nombre) == "string" then
			Sonido.reproducir(nombre, if typeof(posicion) == "Vector3" then posicion else nil)
		end
	end)
	for _, f in CollectionService:GetTagged("Fuego") do
		prepararFuego(f)
	end
	CollectionService:GetInstanceAddedSignal("Fuego"):Connect(prepararFuego)
	CollectionService:GetInstanceRemovedSignal("Fuego"):Connect(function(f)
		local s = fuegos[f]
		if s then
			s:Destroy()
			fuegos[f] = nil
		end
	end)
	for _, m in CollectionService:GetTagged("Pasajero") do
		task.spawn(pasajero, m)
	end
	CollectionService:GetInstanceAddedSignal("Pasajero"):Connect(pasajero)
	CollectionService:GetInstanceAddedSignal("Cocodrilo"):Connect(cocodrilo)

	local function enCabina(): boolean
		local raiz = jugador.Character and jugador.Character:FindFirstChild("HumanoidRootPart")
		return raiz ~= nil and raiz:IsA("BasePart") and dentro(raiz.Position)
	end
	avion:GetAttributeChangedSignal("Cinturones"):Connect(function()
		if enCabina() then
			Sonido.reproducir("Ding", nil, 1, 1)
		end
	end)
	avion:GetAttributeChangedSignal("Pajaros"):Connect(function()
		Sonido.reproducir("Pajaros", nil, 1.2)
		Sonido.reproducir("Explosion", nil, 0.8)
	end)
	avion:GetAttributeChangedSignal("Bandada"):Connect(function()
		Sonido.reproducir("Pajaros", nil, 0.6)
	end)
	avion:GetAttributeChangedSignal("Golpe"):Connect(function()
		Sonido.reproducir("GolpeFuerte", nil, 1.3)
	end)
	avion:GetAttributeChangedSignal("Aterrizaje"):Connect(function()
		local a = avion:GetAttribute("Aterrizaje")
		if a == "Perfecto" or a == "Bueno" or a == "Duro" then
			Sonido.reproducir("Aterrizaje", nil, 1.1)
		end
	end)
	avion:GetAttributeChangedSignal("Mascarillas"):Connect(function()
		if avion:GetAttribute("Mascarillas") == true then
			Sonido.reproducir("Mascarillas", nil, 1)
		end
	end)
	avion:GetAttributeChangedSignal("RampaAbierta"):Connect(function()
		local rampa = pieza("Rampa")
		Sonido.reproducir("Rampa", if rampa then rampa.Position else nil)
	end)
	avion:GetAttributeChangedSignal("Fase"):Connect(function()
		local fase = avion:GetAttribute("Fase")
		if fase == "Despegue" then
			Sonido.reproducir("Despegue", nil, 1, 1)
		elseif fase == "Estrellado" then
			Sonido.reproducir("Explosion", nil, 1.4, 0.8)
		end
	end)
	Estado:GetAttributeChangedSignal("Fase"):Connect(function()
		local f = Estado:GetAttribute("Fase")
		if f == "Embarque" or f == "Vuelo" then
			Sonido.reproducir("AvisoMegafonia", nil, 1, 1)
		end
	end)
	avion:GetAttributeChangedSignal("Tormenta"):Connect(function()
		if avion:GetAttribute("Tormenta") == true then
			Sonido.reproducir("Trueno", nil, 1)
		end
	end)

	ContextActionService:BindAction("Musica", function(_, estado)
		if estado == Enum.UserInputState.Begin then
			Sonido.alternarMusica()
		end
		return Enum.ContextActionResult.Pass
	end, false, Enum.KeyCode.M)

	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		if acumulado >= 0.1 then
			acumulado = 0
			local fase = avion:GetAttribute("Fase")
			local enVuelo = fase == "Despegue" or fase == "Vuelo" or fase == "Aproximacion" or fase == "Frenando"
			local gases = numero("Gases") / 100
			local raiz = jugador.Character and jugador.Character:FindFirstChild("HumanoidRootPart")
			local pos = if raiz and raiz:IsA("BasePart") then raiz.Position else Workspace.CurrentCamera.CFrame.Position
			local adentro = dentro(pos)
			for _, b in motores do
				b.objetivo = if enVuelo then 0.35 + gases * 0.65 else 0
				b.tono = 0.75 + gases * 0.5
			end
			if alarma then
				alarma.objetivo = if avion:GetAttribute("Emergencia") == true or avion:GetAttribute("Perdida") == true then 1 else 0
			end
			if cabina then
				cabina.objetivo = if adentro then (if enVuelo then 1 else 0.4) else 0
			end
			local soplo = 0
			if enVuelo and adentro then
				for _, b in CollectionService:GetTagged("Brecha") do
					if b:IsA("BasePart") then
						local f = b:GetAttribute("Fuerza")
						local d = (b.Position - pos).Magnitude
						soplo = math.max(soplo, (1 - math.clamp(d / 40, 0, 1)) * (if typeof(f) == "number" then f else 1))
					end
				end
				local puertas = avion:FindFirstChild("Puertas")
				if puertas then
					for _, d in puertas:GetChildren() do
						if d:IsA("BasePart") and d:GetAttribute("Abierta") == true and not d:GetAttribute("Interior") then
							soplo = math.max(soplo, 1 - math.clamp((d.Position - pos).Magnitude / 35, 0, 1))
						end
					end
				end
				if avion:GetAttribute("RampaAbierta") == true then
					soplo = math.max(soplo, math.clamp((pos.Z + 10) / 32, 0, 1))
				end
			end
			if viento then
				viento.objetivo = soplo
			end
			if vientoFuera then
				vientoFuera.objetivo = if enVuelo and not adentro then 1 else 0
			end
			if lluvia then
				lluvia.objetivo = if avion:GetAttribute("Tormenta") == true then (if adentro then 0.6 else 1) else 0
			end
			if terminal then
				local d = (pos - Vector3.new(74, 95, -20)).Magnitude
				terminal.objetivo = if not enVuelo then 1 - math.clamp((d - 20) / 50, 0, 1) else 0
			end
			local faseJuego = Estado:GetAttribute("Fase")
			local caos = avion:GetAttribute("Emergencia") == true or numero("Turbulencia") > 0.5 or next(CollectionService:GetTagged("Brecha")) ~= nil or next(CollectionService:GetTagged("Cocodrilo")) ~= nil
			local elegida = if not musicaActiva or faseJuego == "Resultados" then "" elseif faseJuego == "Vuelo" then (if caos then "Caos" else "Vuelo") else "Aeropuerto"
			for nombre, b in musicas do
				b.objetivo = if nombre == elegida then 1 else 0
			end
		end
		local k = math.min(1, dt * 2.5)
		for _, b in bucles do
			local s = b.sonido
			local meta = b.objetivo * b.base
			s.Volume += (meta - s.Volume) * k
			s.PlaybackSpeed += (b.tono - s.PlaybackSpeed) * k
		end
	end)
end

return Sonido
