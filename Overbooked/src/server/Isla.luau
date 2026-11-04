--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Activos = require(script.Parent.Activos)
local Agarre = require(script.Parent.Agarre)
local Avion = require(script.Parent.Avion)
local Objetos = require(script.Parent.Objetos)
local Personajes = require(script.Parent.Personajes)
local Rafagas = require(script.Parent.Rafagas)
local Sonidos = require(script.Parent.Sonidos)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local RemotoSacudida = Remotos:WaitForChild("Sacudida") :: UnreliableRemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder

type Cangrejo = { parte: BasePart, casa: Vector3, objetivo: Vector3, espera: number }

local Isla = {}

local C = Config.ISLA
local ICONOS = { RadioAntena = "Radio", RadioBateria = "Radio", RadioCaja = "Radio", Tronco = "Tronco", Bengala = "Bengala" }
local rng = Random.new()
local isla: Model
local carpeta: Folder
local spots: { [string]: { BasePart } } = {}
local zonas: { [string]: BasePart } = {}
local cangrejos: { Cangrejo } = {}
local pellizcos: { [Player]: number } = {}
local efectos: { Instance } = {}
local palmeras: { BasePart } = {}
local HUMO_RESTOS = Color3.fromRGB(70, 66, 64)

local function motores(): { Vector3 }
	local exterior = Workspace:WaitForChild("Avion"):FindFirstChild("Exterior")
	local lista = {}
	for _, lado in { "Izq", "Der" } do
		local m = exterior and exterior:FindFirstChild("Motor" .. lado)
		if m and m:IsA("BasePart") then
			table.insert(lista, m.Position)
		end
	end
	return lista
end

local function caerCoco()
	local palmera = palmeras[rng:NextInteger(1, #palmeras)]
	if not palmera then
		return
	end
	local copa = palmera.Position + Vector3.new(rng:NextNumber(-3, 3), palmera.Size.Y * 0.45, rng:NextNumber(-3, 3))
	Rafagas.lanzar("Hojas", copa, 1.4)
	local coco = Objetos.crear("Coco", CFrame.new(copa), carpeta)
	coco.AssemblyLinearVelocity = Vector3.new(0, -10, 0)
	task.delay(1.1, function()
		if not coco.Parent then
			return
		end
		for _, jugador in Players:GetPlayers() do
			local raiz = Personajes.raiz(jugador)
			if raiz and (raiz.Position - coco.Position).Magnitude < 4 then
				Personajes.ragdoll(jugador, 1.2, Vector3.new(rng:NextNumber(-20, 20), 20, rng:NextNumber(-20, 20)))
				Rafagas.lanzar("Estrellas", raiz.Position + Vector3.new(0, 2.5, 0), 1.2)
				Sonidos.emitir("Golpe", raiz.Position)
				RemotoAviso:FireClient(jugador, "¡Un coco en toda la cabeza!", "peligro")
			end
		end
	end)
end

local function aviso(texto: string, tipo: string)
	RemotoAviso:FireAllClients(texto, tipo)
end

local function mezclar<T>(lista: { T }?): { T }
	local copia = table.clone(lista or {})
	for i = #copia, 2, -1 do
		local j = rng:NextInteger(1, i)
		copia[i], copia[j] = copia[j], copia[i]
	end
	return copia
end

local function crear(tipo: string, spot: BasePart): BasePart
	local o = Objetos.crear(tipo, CFrame.new(spot.Position) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0), carpeta)
	local icono = ICONOS[tipo]
	if icono then
		o:SetAttribute("Icono", icono)
		CollectionService:AddTag(o, "ObjetivoIsla")
	end
	return o
end

local function crearCangrejo(spot: BasePart)
	local p = Instance.new("Part")
	p.Name = "Cangrejo"
	p.Size = Vector3.new(2.4, 1.2, 1.8)
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.Transparency = 1
	p.CFrame = CFrame.new(spot.Position)
	p.Parent = carpeta
	Activos.vestirDinamico(p, "Cangrejo")
	table.insert(cangrejos, { parte = p, casa = spot.Position, objetivo = spot.Position, espera = 0 })
end

local function moverCangrejos(dt: number, ahora: number)
	for _, c in cangrejos do
		local pos = c.parte.Position
		local hacia = Vector3.new(c.objetivo.X - pos.X, 0, c.objetivo.Z - pos.Z)
		if hacia.Magnitude < 0.5 then
			if ahora >= c.espera then
				local a = rng:NextNumber(0, math.pi * 2)
				local r = rng:NextNumber(4, 22)
				c.objetivo = c.casa + Vector3.new(math.cos(a) * r, 0, math.sin(a) * r)
				c.espera = ahora + rng:NextNumber(0.6, 2.4)
			end
			continue
		end
		local direccion = hacia.Unit
		local nuevo = pos + direccion * math.min(hacia.Magnitude, C.VELOCIDAD_CANGREJO * dt)
		local frente = direccion:Cross(Vector3.yAxis)
		c.parte.CFrame = CFrame.lookAt(nuevo, nuevo + frente) * CFrame.Angles(0, 0, math.sin(ahora * 18) * 0.07)
	end
end

local function pellizcar(ahora: number)
	for _, jugador in Players:GetPlayers() do
		local raiz = Personajes.raiz(jugador)
		if not raiz or (pellizcos[jugador] or 0) > ahora then
			continue
		end
		for _, c in cangrejos do
			local d = raiz.Position - c.parte.Position
			if Vector3.new(d.X, 0, d.Z).Magnitude < C.PELLIZCO and math.abs(d.Y) < 4 then
				pellizcos[jugador] = ahora + 4
				c.objetivo = c.casa
				c.espera = ahora + 2
				local empuje = Vector3.new(d.X, 0, d.Z)
				Personajes.ragdoll(jugador, 1, (if empuje.Magnitude > 0.1 then empuje.Unit else Vector3.xAxis) * 28 + Vector3.new(0, 26, 0))
				Rafagas.lanzar("Estrellas", raiz.Position + Vector3.new(0, 2, 0), 1)
				Sonidos.emitir("Mordisco", raiz.Position)
				RemotoAviso:FireClient(jugador, "¡Un cangrejo te ha pellizcado!", "peligro")
				break
			end
		end
	end
end

local function cerca(o: BasePart, zona: BasePart?, radio: number): boolean
	return zona ~= nil and (o.Position - zona.Position).Magnitude < radio
end

local function consumir(o: BasePart)
	Agarre.soltarObjeto(o)
	o:Destroy()
end

local RANURAS = { RadioAntena = -1.93, RadioBateria = -0.03, RadioCaja = 1.87 }

local function encajar(tipo: string)
	local estacion = zonas.Radio
	if not estacion then
		return
	end
	local alto = Config.OBJETOS[tipo].tamano.Y
	local cima = 2.11 - estacion.Size.Y / 2
	local pieza = Objetos.crear(tipo, estacion.CFrame * CFrame.new(RANURAS[tipo] or 0, cima + alto / 2, -0.19), carpeta)
	pieza.Anchored = true
	pieza.CanCollide = false
	CollectionService:RemoveTag(pieza, "Agarrable")
	Rafagas.lanzar("Chispas", pieza.Position, 1)
	Sonidos.emitir("Reparado", pieza.Position)
end

local function encender()
	local hoguera = zonas.Hoguera
	if not hoguera then
		return
	end
	local a = Instance.new("Attachment")
	a.Name = "FuegoHoguera"
	a.Position = Vector3.new(0, 1, 0)
	a.Parent = hoguera
	VFX.fuego(a, 2.6)
	local luz = Instance.new("PointLight")
	luz.Color = Color3.fromRGB(255, 170, 80)
	luz.Range = 34
	luz.Brightness = 2.2
	luz.Parent = a
	table.insert(efectos, a)
	Rafagas.lanzar("Bengala", hoguera.Position + Vector3.new(0, 2, 0), 2)
	Rafagas.lanzar("Chispas", hoguera.Position + Vector3.new(0, 2, 0), 2)
	Rafagas.lanzar("Humo", hoguera.Position + Vector3.new(0, 6, 0), 3)
	Sonidos.emitir("Ding", hoguera.Position)
end

local function hidroavion()
	local destino = zonas.Rescate
	if not destino then
		return
	end
	local p = Instance.new("Part")
	p.Name = "Hidroavion"
	p.Size = Vector3.new(40, 12, 32)
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.Transparency = 1
	local final = CFrame.new(destino.Position + Vector3.new(0, 6, 0)) * CFrame.Angles(0, math.rad(90), 0)
	p.CFrame = final + Vector3.new(1400, 260, 0)
	p.Parent = carpeta
	Activos.vestirDinamico(p, "Hidroavion")
	local duracion = math.max(4, C.RESCATE - 4)
	TweenService:Create(p, TweenInfo.new(duracion, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = final }):Play()
	task.delay(duracion, function()
		if p.Parent then
			Rafagas.lanzar("Salpicadura", destino.Position, 4)
			Sonidos.emitir("Salpicadura", destino.Position)
		end
	end)
end

local function marcarDestinos(activos: boolean)
	for nombre, icono in { Radio = "Radio", Hoguera = "Fuego", Rescate = "Hidroavion" } do
		local z = zonas[nombre]
		if z then
			z:SetAttribute("Icono", icono)
			if activos then
				CollectionService:AddTag(z, "DestinoIsla")
			else
				CollectionService:RemoveTag(z, "DestinoIsla")
			end
		end
	end
end

local function estado(radio: number, lena: number, fuego: boolean, quedan: number, rescate: number)
	Estado:SetAttribute("IslaRadio", radio)
	Estado:SetAttribute("IslaLena", lena)
	Estado:SetAttribute("IslaFuego", fuego)
	Estado:SetAttribute("IslaQuedan", math.max(0, math.ceil(quedan)))
	Estado:SetAttribute("IslaRescate", math.ceil(rescate))
end

function Isla.jugar(): boolean
	local centro = Vector3.new(0, 104, -17)
	Rafagas.lanzar("Explosion", centro + Vector3.new(0, 0, -44), 2.5)
	for _, m in motores() do
		Rafagas.lanzar("Explosion", m, 2.5)
	end
	Rafagas.lanzar("Escombros", centro, 2)
	for z = -60, 30, 18 do
		Rafagas.lanzar("Arena", Vector3.new(0, 91, z), 2)
	end
	Sonidos.emitir("Explosion", centro)
	RemotoSacudida:FireAllClients(1)
	Avion.prepararTierra()
	Avion.danarMotor("Izq", 50, true)
	Avion.danarMotor("Der", 35, rng:NextNumber() < 0.5)
	isla.Parent = Workspace
	local piezas = mezclar(spots.radio)
	for i, tipo in C.PIEZAS do
		if piezas[i] then
			crear(tipo, piezas[i])
		end
	end
	for i, s in mezclar(spots.tronco) do
		if i <= C.TRONCOS + 2 then
			crear("Tronco", s)
		end
	end
	for i, s in mezclar(spots.coco) do
		if i <= C.COCOS then
			crear("Coco", s)
		end
	end
	for i, s in mezclar(spots.cangrejo) do
		if i <= C.CANGREJOS then
			crearCangrejo(s)
		end
	end
	local bengalas = spots.bengala
	if bengalas and bengalas[1] then
		crear("Bengala", bengalas[1])
	end
	marcarDestinos(true)
	task.delay(2.5, aviso, "¡Náufragos! Llevad las 3 piezas a la radio y 3 troncos a la hoguera, y encendedla con la bengala", "peligro")
	local radio, lena, fuego = 0, 0, false
	local rescate: number? = nil
	local fin = os.clock() + C.DURACION
	local ultimo = os.clock()
	local pista = 0
	local proximoHumo = 0
	local proximoCoco = os.clock() + rng:NextNumber(14, 22)
	local puntosHumo = motores()
	table.insert(puntosHumo, centro + Vector3.new(0, 4, -44))
	while true do
		task.wait(0.1)
		local ahora = os.clock()
		moverCangrejos(ahora - ultimo, ahora)
		ultimo = ahora
		pellizcar(ahora)
		if ahora >= proximoHumo then
			proximoHumo = ahora + 2.5
			Rafagas.lanzar("Humo", puntosHumo[rng:NextInteger(1, #puntosHumo)] + Vector3.new(0, 3, 0), 2.5, HUMO_RESTOS)
		end
		if ahora >= proximoCoco then
			proximoCoco = ahora + rng:NextNumber(16, 28)
			caerCoco()
		end
		for _, o in carpeta:GetChildren() do
			if not o:IsA("BasePart") or not o:HasTag("ObjetivoIsla") then
				continue
			end
			local tipo = o:GetAttribute("Tipo")
			if typeof(tipo) ~= "string" then
				continue
			end
			if table.find(C.PIEZAS, tipo) and cerca(o, zonas.Radio, C.ENTREGA) then
				consumir(o)
				radio += 1
				encajar(tipo)
				aviso(if radio < #C.PIEZAS then `Pieza de radio colocada ({radio}/{#C.PIEZAS})` else "¡Radio reparada! Ya podemos pedir ayuda", "bien")
			elseif tipo == "Tronco" and lena < C.TRONCOS and cerca(o, zonas.Hoguera, C.ENTREGA) then
				consumir(o)
				lena += 1
				Rafagas.lanzar("Astillas", (zonas.Hoguera :: BasePart).Position, 1)
				Sonidos.emitir("Madera", (zonas.Hoguera :: BasePart).Position)
				aviso(`Leña en la hoguera ({lena}/{C.TRONCOS})`, "bien")
			elseif tipo == "Bengala" and not fuego and cerca(o, zonas.Hoguera, C.ENTREGA) then
				if lena >= C.TRONCOS then
					consumir(o)
					fuego = true
					encender()
					aviso("¡Hoguera encendida! Seguro que la ven desde lejos", "bien")
				elseif ahora > pista then
					pista = ahora + 6
					aviso(`Faltan troncos: la hoguera necesita {C.TRONCOS}`, "info")
				end
			end
		end
		if not rescate and radio >= #C.PIEZAS and fuego then
			rescate = ahora + C.RESCATE
			hidroavion()
			aviso("¡Os han visto! Un hidroavión viene a por vosotros", "bien")
		end
		estado(radio, lena, fuego, fin - ahora, if rescate then rescate - ahora else -1)
		if rescate and ahora >= rescate then
			local destino = zonas.Rescate
			local punto = if destino then destino.Position + Vector3.new(0, 8, 0) else centro
			Rafagas.lanzar("Confeti", punto, 3)
			Rafagas.lanzar("Monedas", punto, 2)
			for _, jugador in Players:GetPlayers() do
				local raiz = Personajes.raiz(jugador)
				if raiz then
					Rafagas.lanzar("Confeti", raiz.Position + Vector3.new(0, 4, 0), 1.5)
				end
			end
			Sonidos.emitir("Victoria", nil)
			return true
		end
		if not rescate and ahora >= fin then
			return false
		end
	end
end

function Isla.limpiar()
	for _, h in carpeta:GetChildren() do
		Agarre.soltarObjeto(h)
		h:Destroy()
	end
	for _, e in efectos do
		e:Destroy()
	end
	table.clear(efectos)
	table.clear(cangrejos)
	table.clear(pellizcos)
	marcarDestinos(false)
	for _, n in { "IslaRadio", "IslaLena", "IslaFuego", "IslaQuedan", "IslaRescate" } do
		Estado:SetAttribute(n, nil)
	end
	isla.Parent = ServerStorage
end

function Isla.iniciar()
	isla = ServerStorage:WaitForChild("Isla") :: Model
	carpeta = Instance.new("Folder")
	carpeta.Name = "Naufragio"
	carpeta.Parent = isla
	for _, d in isla:GetDescendants() do
		if not d:IsA("BasePart") then
			continue
		end
		local visual = d:GetAttribute("Visual")
		if typeof(visual) == "string" then
			local base = d:GetAttribute("Base")
			Activos.vestirFijo(d, visual, if typeof(base) == "number" then base else nil)
		end
		local spot = d:GetAttribute("Spot")
		if typeof(spot) == "string" then
			local lista = spots[spot] or {}
			spots[spot] = lista
			table.insert(lista, d)
		end
		local zona = d:GetAttribute("Zona")
		if typeof(zona) == "string" then
			zonas[zona] = d
		end
		if d.Name == "Palmera" then
			table.insert(palmeras, d)
		end
	end
	Players.PlayerRemoving:Connect(function(jugador)
		pellizcos[jugador] = nil
	end)
end

return Isla
