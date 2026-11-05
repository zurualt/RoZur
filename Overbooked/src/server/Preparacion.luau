--!strict
local CollectionService = game:GetService("CollectionService")
local Debris = game:GetService("Debris")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Contratos = require(ReplicatedStorage.Shared.Contratos)
local ModelosPreparacion = require(ReplicatedStorage.Shared.ModelosPreparacion)
local Activos = require(script.Parent.Activos)
local Agarre = require(script.Parent.Agarre)
local Avion = require(script.Parent.Avion)
local Carga = require(script.Parent.Carga)
local Objetos = require(script.Parent.Objetos)
local Personajes = require(script.Parent.Personajes)
local Rafagas = require(script.Parent.Rafagas)
local Sonidos = require(script.Parent.Sonidos)
local Vehiculos = require(script.Parent.Vehiculos)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder

local P = Config.PREPARACION

type Tobogan = { numero: number, boca: BasePart, luz: BasePart }
type Marca = { icono: string, texto: string, destino: boolean }

local Preparacion = {}

local nave = ServerStorage:WaitForChild("Preparacion") :: Model
local aeropuerto = Workspace:WaitForChild("Aeropuerto") :: Model
local avion = Workspace:WaitForChild("Avion") :: Model
local marcasNave = nave:WaitForChild("Marcas") :: Folder
local sueltos = nave:WaitForChild("Sueltos") :: Folder
local persiana = nave:WaitForChild("Persiana") :: BasePart
local surtidor = nave:WaitForChild("Surtidor") :: BasePart
local cubo = nave:WaitForChild("CuboMerienda") :: BasePart
local zonaToboganes = nave:WaitForChild("ZonaToboganes") :: BasePart
local aparcamiento = marcasNave:WaitForChild("SpawnPreparacion") :: SpawnLocation
local rampa = avion:WaitForChild("Bodega"):WaitForChild("Rampa") :: BasePart
local cerrada = persiana.CFrame
local rng = Random.new()

local ROPA = {
	{ tam = Vector3.new(1.1, 0.12, 1.3), color = Color3.fromRGB(242, 155, 178) },
	{ tam = Vector3.new(0.9, 0.12, 0.7), color = Color3.fromRGB(250, 250, 250) },
	{ tam = Vector3.new(0.3, 0.12, 1.0), color = Color3.fromRGB(246, 196, 69) },
	{ tam = Vector3.new(0.3, 0.12, 1.0), color = Color3.fromRGB(111, 180, 227) },
	{ tam = Vector3.new(1.2, 0.12, 0.5), color = Color3.fromRGB(109, 190, 69) },
	{ tam = Vector3.new(0.8, 0.12, 0.8), color = Color3.fromRGB(217, 68, 58) },
}
local AMARILLO = Color3.fromRGB(246, 196, 69)
local APAGADA = Color3.fromRGB(90, 95, 102)

local toboganes: { Tobogan } = {}
local activa = false
local paso = ""
local maletas: { BasePart } = {}
local previas: { [BasePart]: Vector3 } = {}
local reventadas: { [BasePart]: boolean } = {}
local marcadas: { [BasePart]: boolean } = {}
local esperas: { [Player]: number } = {}
local nMaletas = 0
local creadas = 0
local cargadas = 0
local hechoMaletas = false
local conAnimal = false
local jaulaGuardada = false
local guardarEn = 0
local avisoReventon = false
local destino: BasePart? = nil
local pie = Vector3.zero
local tweenPuerta: Tween? = nil
local avisoBombear: ProximityPrompt? = nil
local avisoCubo: ProximityPrompt? = nil
local relleno: Frame? = nil
local cifra: TextLabel? = nil

local function poner(nombre: string, valor: any)
	if Estado:GetAttribute(nombre) ~= valor then
		Estado:SetAttribute(nombre, valor)
	end
end

local function aviso(texto: string, tipo: string)
	RemotoAviso:FireAllClients(texto, tipo)
end

local function marca(nombre: string): BasePart
	return marcasNave:WaitForChild(nombre) :: BasePart
end

local function aplicarMarcas(deseadas: { [BasePart]: Marca })
	for parte in marcadas do
		if not deseadas[parte] then
			marcadas[parte] = nil
			CollectionService:RemoveTag(parte, "MarcaPrep")
		end
	end
	for parte, m in deseadas do
		if parte:GetAttribute("PrepIcono") ~= m.icono then
			parte:SetAttribute("PrepIcono", m.icono)
		end
		if parte:GetAttribute("PrepTexto") ~= m.texto then
			parte:SetAttribute("PrepTexto", m.texto)
		end
		if parte:GetAttribute("PrepDestino") ~= m.destino then
			parte:SetAttribute("PrepDestino", m.destino)
		end
		if not marcadas[parte] then
			marcadas[parte] = true
			CollectionService:AddTag(parte, "MarcaPrep")
		end
	end
end

local function sobre(parte: BasePart, carro: BasePart): boolean
	local l = carro.CFrame:PointToObjectSpace(parte.Position)
	local m = carro.Size / 2
	return math.abs(l.X) <= m.X + 0.4 and l.Y >= 0 and l.Y <= m.Y + 5 and math.abs(l.Z) <= m.Z + 0.4
end

local function suelo(p: Vector3): number
	local filtro = RaycastParams.new()
	filtro.FilterType = Enum.RaycastFilterType.Exclude
	local fuera: { Instance } = { avion, sueltos }
	local vehiculos = aeropuerto:FindFirstChild("Vehiculos")
	if vehiculos then
		table.insert(fuera, vehiculos)
	end
	for _, jugador in Players:GetPlayers() do
		if jugador.Character then
			table.insert(fuera, jugador.Character)
		end
	end
	filtro.FilterDescendantsInstances = fuera
	local r = Workspace:Raycast(Vector3.new(p.X, p.Y + 20, p.Z), Vector3.new(0, -60, 0), filtro)
	return math.clamp(if r then r.Position.Y else 90.2, 89.5, 91.2)
end

local function pieRampa(): Vector3
	local a = rampa.CFrame:PointToWorldSpace(Vector3.new(0, 0, -rampa.Size.Z / 2))
	local b = rampa.CFrame:PointToWorldSpace(Vector3.new(0, 0, rampa.Size.Z / 2))
	local alto, bajo = if a.Y > b.Y then a else b, if a.Y > b.Y then b else a
	local plano = (bajo - alto) * Vector3.new(1, 0, 1)
	local dir = if plano.Magnitude > 0.5 then plano.Unit else Vector3.zAxis
	local p = bajo + dir * 5
	return Vector3.new(p.X, suelo(p), p.Z)
end

local function cerca(parte: BasePart?): boolean
	if not parte or not parte.Parent then
		return false
	end
	return ((parte.Position - pie) * Vector3.new(1, 0, 1)).Magnitude < P.LLEGADA
end

local function llegado(): boolean
	return cerca(Vehiculos.carro()) or cerca(Vehiculos.tractor())
end

local function encender(t: Tobogan, si: boolean)
	t.luz.Material = if si then Enum.Material.Neon else Enum.Material.SmoothPlastic
	t.luz.Color = if si then AMARILLO else APAGADA
	local l = t.luz:FindFirstChildOfClass("PointLight")
	if l then
		l.Brightness = if si then 1.4 else 0
	end
end

local function reventar(maleta: BasePart)
	reventadas[maleta] = true
	local centro = maleta.Position
	for _, r in ROPA do
		local t = Instance.new("Part")
		t.Name = "Ropa"
		t.Size = r.tam
		t.Color = r.color
		t.Material = Enum.Material.Fabric
		t.CanQuery = false
		t.CanTouch = false
		t.CollisionGroup = "Sostenido"
		t.CFrame = CFrame.new(centro + Vector3.new(0, 0.6, 0)) * CFrame.Angles(rng:NextNumber(0, 6.28), rng:NextNumber(0, 6.28), 0)
		t.AssemblyLinearVelocity = Vector3.new(rng:NextNumber(-14, 14), rng:NextNumber(18, 30), rng:NextNumber(-14, 14))
		t.AssemblyAngularVelocity = Vector3.new(rng:NextNumber(-8, 8), rng:NextNumber(-8, 8), rng:NextNumber(-8, 8))
		t.Parent = sueltos
		Debris:AddItem(t, rng:NextNumber(7, 10))
	end
	Sonidos.emitir("Pop", centro)
	Rafagas.lanzar("Polvo", centro, 0.8)
	Rafagas.lanzar("Confeti", centro + Vector3.new(0, 1, 0), 0.6)
	if not avisoReventon then
		avisoReventon = true
		aviso("¡Ha reventado una maleta! Calcetines y calzoncillos por todo el hangar", "info")
	end
end

local function soltarMaleta(t: Tobogan, turbo: boolean, valor: number, riesgo: number)
	encender(t, true)
	Sonidos.emitir("Ding", t.boca.Position, 0.2)
	local m = Carga.anadir("Maleta", t.boca.CFrame * CFrame.Angles(0, rng:NextNumber(-0.3, 0.3), 0), valor, riesgo)
	table.insert(maletas, m)
	local dir = t.boca.CFrame.LookVector
	m.AssemblyLinearVelocity = if turbo then dir * 75 + Vector3.new(0, 28, 0) else dir * 6
	if turbo then
		Rafagas.lanzar("Polvo", t.boca.Position, 1.2)
		Sonidos.emitir("Bocina", t.boca.Position)
		aviso(`¡El tobogán {t.numero} se ha vuelto loco! ¡Cuidado con la cabeza!`, "peligro")
	end
	task.delay(1.4, encender, t, false)
end

local function bombear(jugador: Player)
	local ahora = os.clock()
	local raiz = Personajes.raiz(jugador)
	if not activa or (esperas[jugador] or 0) > ahora or Avion.estado.combustible >= 100 or not raiz or (raiz.Position - surtidor.Position).Magnitude > 14 then
		return
	end
	esperas[jugador] = ahora + 0.6
	Avion.estado.combustible = math.min(100, Avion.estado.combustible + P.BOMBEO)
	local boca = surtidor.Position + Vector3.new(0, 1.5, 0)
	Sonidos.emitir("Salpicadura", boca, 0.3)
	if rng:NextNumber() < 0.1 then
		Rafagas.lanzar("Salpicadura", boca, 1.4, AMARILLO)
		local dir = (raiz.Position - surtidor.Position) * Vector3.new(1, 0, 1)
		Personajes.ragdoll(jugador, 1.3, (if dir.Magnitude > 0 then dir.Unit else Vector3.xAxis) * 30 + Vector3.new(0, 18, 0))
		RemotoAviso:FireClient(jugador, "¡Se ha soltado la manguera! Estás empapado de queroseno", "peligro")
	elseif Avion.estado.combustible >= 100 then
		Rafagas.lanzar("Confeti", boca, 0.8)
		Sonidos.emitir("Reparado", boca)
		aviso("¡Depósito lleno!", "bien")
	end
end

local function merienda(jugador: Player)
	local ahora = os.clock()
	if not activa or (esperas[jugador] or 0) > ahora or Agarre.sostenido(jugador) then
		return
	end
	esperas[jugador] = ahora + 0.8
	Sonidos.emitir("Coger", cubo.Position)
	Agarre.forzar(jugador, Objetos.crear("Hamburguesa", cubo.CFrame * CFrame.new(0, cubo.Size.Y / 2 + 0.5, 0), sueltos))
end

local function indicacion(parte: BasePart, accion: string, objeto: string, duracion: number, f: (Player) -> ()): ProximityPrompt
	local p = Instance.new("ProximityPrompt")
	p.ActionText = accion
	p.ObjectText = objeto
	p.KeyboardKeyCode = Enum.KeyCode.E
	p.HoldDuration = duracion
	p.MaxActivationDistance = 9
	p.RequiresLineOfSight = false
	p.Enabled = false
	p.Parent = parte
	p.Triggered:Connect(f)
	return p
end

local function bezier(a: Vector3, b: Vector3, c: Vector3, t: number): Vector3
	local u = 1 - t
	return a * (u * u) + b * (2 * u * t) + c * (t * t)
end

local function quitarFlechas()
	for _, f in CollectionService:GetTagged("FlechaPrep") do
		f:Destroy()
	end
end

local function flecha(pos: Vector3, dir: Vector3, orden: number)
	local y = suelo(pos)
	local f = Instance.new("Part")
	f.Name = "FlechaSuelo"
	f.Anchored = true
	f.CanCollide = false
	f.CanQuery = false
	f.CanTouch = false
	f.CastShadow = false
	f.Size = Vector3.new(3.2, 0.1, 4.4)
	f.Color = AMARILLO
	f.Material = Enum.Material.SmoothPlastic
	local centro = Vector3.new(pos.X, y + 0.06, pos.Z)
	f.CFrame = CFrame.lookAt(centro, centro + Vector3.new(dir.X, 0, dir.Z))
	f:SetAttribute("Orden", orden)
	f.Parent = sueltos
	CollectionService:AddTag(f, "FlechaPrep")
	Activos.vestirFijo(f, "FlechaSuelo", y + 0.02)
end

local function ponerFlechas()
	quitarFlechas()
	local a = marca("SalidaNave").Position
	local c = pie
	local b = Vector3.new(a.X, a.Y, c.Z - 3)
	local previo = a
	local recorrido = 4.5
	local orden = 0
	for i = 1, 240 do
		local p = bezier(a, b, c, i / 240)
		recorrido += (p - previo).Magnitude
		if recorrido >= 6 and (p - c).Magnitude > 5 then
			recorrido = 0
			orden += 1
			flecha(p, p - previo, orden)
		end
		previo = p
	end
end

local function cocodriloCuerpo(): BasePart?
	for _, c in CollectionService:GetTagged("Cocodrilo") do
		if c:IsA("Model") and c.PrimaryPart and c:IsDescendantOf(Workspace) then
			return c.PrimaryPart
		end
	end
	return nil
end

local function actualizar()
	local carro = Vehiculos.carro()
	local vivas: { BasePart } = {}
	cargadas = 0
	for _, m in maletas do
		if not m.Parent then
			previas[m] = nil
			continue
		end
		table.insert(vivas, m)
		local portada = Agarre.portador(m) ~= nil
		if carro and not portada and sobre(m, carro) then
			cargadas += 1
		end
		local v = m.AssemblyLinearVelocity
		local antes = previas[m] or v
		previas[m] = v
		if not portada and not reventadas[m] and (v - antes).Magnitude > 38 and rng:NextNumber() < P.REVENTON then
			reventar(m)
		end
	end
	maletas = vivas
	local total = #maletas + nMaletas - creadas
	if paso == "Tareas" and not hechoMaletas and creadas >= nMaletas and cargadas >= total then
		hechoMaletas = true
		aviso("¡Todas las maletas en el carro!", "bien")
	end
	local _, _, _, croc = Carga.resumen()
	if conAnimal and not jaulaGuardada and croc == "Enjaulado" then
		if guardarEn == 0 then
			guardarEn = os.clock() + 1.5
		elseif os.clock() >= guardarEn and Carga.guardarJaula() then
			jaulaGuardada = true
			aviso("¡Cocodrilo enjaulado! Los cuidadores llevan la jaula a la bodega", "bien")
		end
	elseif croc ~= "Enjaulado" then
		guardarEn = 0
	end
	local combustible = math.floor(Avion.estado.combustible)
	local suelto = conAnimal and croc == "Suelto"
	local b, c = avisoBombear, avisoCubo
	if b then
		b.Enabled = activa and combustible < 100
	end
	if c then
		c.Enabled = activa and suelto
	end
	local r, t = relleno, cifra
	if r and t then
		r.Size = UDim2.fromScale(combustible / 100, 1)
		r.BackgroundColor3 = if combustible >= 100 then Color3.fromRGB(109, 190, 69) else AMARILLO
		t.Text = `{combustible}%`
	end
	local fuera = 0
	if paso == "Descargar" then
		for _, m in Carga.maletas() do
			if not Carga.aBordo(m.Position) then
				fuera += 1
			end
		end
		if fuera == 0 then
			paso = ""
			quitarFlechas()
			aviso("¡Equipaje en la bodega! Buen trabajo", "bien")
		end
	end
	poner("PrepPaso", paso)
	poner("PrepMaletas", if hechoMaletas then total else math.min(cargadas, total))
	poner("PrepTotal", total)
	poner("PrepAnimal", if not conAnimal then "" elseif jaulaGuardada then "Bodega" else croc)
	poner("PrepCombustible", combustible)
	poner("PrepFuera", fuera)

	local d: { [BasePart]: Marca } = {}
	if paso == "Tareas" then
		if carro and not hechoMaletas then
			d[carro] = { icono = "Maleta", texto = `{cargadas}/{total}`, destino = true }
		end
		if not hechoMaletas and #maletas > cargadas then
			d[zonaToboganes] = { icono = "Mano", texto = "Recoge las maletas", destino = false }
		end
		if combustible < 100 then
			d[surtidor] = { icono = "Combustible", texto = `{combustible}%`, destino = false }
		end
	end
	if suelto and paso ~= "" then
		local cuerpo = cocodriloCuerpo()
		if cuerpo then
			d[cuerpo] = { icono = "Cocodrilo", texto = "¡A la jaula!", destino = false }
		end
		local carpeta = avion:FindFirstChild("Carga")
		local jaula = carpeta and carpeta:FindFirstChild("Jaula")
		if jaula and jaula:IsA("BasePart") then
			d[jaula] = { icono = "Diana", texto = "Jaula", destino = true }
		end
		d[cubo] = { icono = "Hamburguesa", texto = "Merienda", destino = false }
	end
	local meta = destino
	if paso == "Conducir" then
		d[Vehiculos.tractor()] = { icono = "Volante", texto = if hechoMaletas then "¡Carro cargado! Conduce hasta el avión" else "Conduce hasta el avión", destino = false }
		if meta then
			d[meta] = { icono = "Avion", texto = "Bodega", destino = true }
		end
	elseif paso == "Descargar" and meta then
		d[meta] = { icono = "Maleta", texto = `Metedlas en la bodega ({fuera})`, destino = true }
	end
	aplicarMarcas(d)
end

local function listo(): boolean
	local _, _, _, croc = Carga.resumen()
	return hechoMaletas and (not conAnimal or jaulaGuardada or croc == "Perdido") and Avion.estado.combustible >= 100
end

local function abrirPuerta()
	local subida = persiana:GetAttribute("Subida")
	local t = TweenService:Create(persiana, TweenInfo.new(2.6, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut), {
		CFrame = cerrada + Vector3.new(0, if typeof(subida) == "number" then subida else 8.8, 0),
	})
	tweenPuerta = t
	t:Play()
	persiana.CanCollide = false
	Sonidos.emitir("Rampa", persiana.Position)
	Rafagas.lanzar("Polvo", persiana.Position - Vector3.new(0, persiana.Size.Y / 2, 0), 2)
	Rafagas.lanzar("Confeti", persiana.Position, 1.4)
end

local function cerrarPuerta()
	local t = tweenPuerta
	if t then
		t:Cancel()
	end
	tweenPuerta = nil
	persiana.CFrame = cerrada
	persiana.CanCollide = true
end

local function llevar(jugador: Player, i: number)
	local personaje = jugador.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	if not personaje or not humanoide then
		return
	end
	local asiento = humanoide.SeatPart
	if asiento then
		local soldadura = asiento:FindFirstChild("SeatWeld")
		if soldadura then
			soldadura:Destroy()
		end
		humanoide.Sit = false
	end
	personaje:PivotTo(aparcamiento.CFrame * CFrame.new(((i - 1) % 2) * 3 - 1.5, 3.2, ((i - 1) // 2) * 3 - 1.5))
end

local function recoger()
	if not activa and nave.Parent == ServerStorage then
		return
	end
	activa = false
	paso = ""
	aplicarMarcas({})
	quitarFlechas()
	sueltos:ClearAllChildren()
	destino = nil
	table.clear(maletas)
	table.clear(previas)
	table.clear(reventadas)
	cerrarPuerta()
	for _, t in toboganes do
		encender(t, false)
	end
	aparcamiento.Enabled = false
	nave.Parent = ServerStorage
	for _, nombre in { "PrepPaso", "PrepMaletas", "PrepTotal", "PrepAnimal", "PrepCombustible", "PrepFuera" } do
		Estado:SetAttribute(nombre, nil)
	end
end

function Preparacion.conCocodrilo(contrato: Contratos.Contrato): Contratos.Contrato
	for _, c in contrato.carga do
		if c.tipo == "Jaula" then
			return contrato
		end
	end
	table.insert(contrato.carga, { tipo = "Jaula", cantidad = 1, valor = 400, entrega = false })
	return contrato
end

function Preparacion.jugar(contrato: Contratos.Contrato): boolean
	local limite = os.clock() + 20
	while #Players:GetPlayers() == 0 and os.clock() < limite do
		task.wait(0.5)
	end
	if #Players:GetPlayers() == 0 then
		return false
	end
	Estado:SetAttribute("Fase", "Preparacion")
	Estado:SetAttribute("Contrato", HttpService:JSONEncode(contrato))
	Avion.estado.total = contrato.distancia
	Avion.estado.distancia = 0
	Avion.estado.combustible = P.COMBUSTIBLE_INICIAL
	Agarre.soltarTodo()
	recoger()
	nave.Parent = Workspace
	local guardados: { [SpawnLocation]: boolean } = {}
	for _, d in Workspace:GetDescendants() do
		if d:IsA("SpawnLocation") and d ~= aparcamiento then
			guardados[d] = d.Enabled
			d.Enabled = false
		end
	end
	aparcamiento.Enabled = true
	Vehiculos.colocar(marca("PuestoTractor").CFrame, marca("PuestoCarro").CFrame)

	local valorMaleta, valorJaula = 15, 0
	local resto: { Contratos.Carga } = {}
	nMaletas = 0
	for _, c in contrato.carga do
		if c.tipo == "Maleta" and not c.entrega then
			nMaletas += c.cantidad
			valorMaleta = c.valor
		elseif c.tipo == "Jaula" then
			valorJaula += c.valor
		else
			table.insert(resto, c)
		end
	end
	nMaletas += (#Players:GetPlayers() - 1) * P.MALETAS_POR_JUGADOR
	local copia = table.clone(contrato)
	copia.carga = resto
	Carga.cargar(copia)
	creadas, cargadas, guardarEn = 0, 0, 0
	hechoMaletas, jaulaGuardada, avisoReventon = false, false, false
	conAnimal = valorJaula > 0
	if conAnimal then
		Carga.anadir("Jaula", marca("SitioJaula").CFrame * CFrame.new(0, Config.OBJETOS.Jaula.tamano.Y / 2 + 0.1, 0), valorJaula, contrato.riesgo)
		Carga.cocodriloEn(marca("SitioCocodrilo").CFrame * CFrame.new(0, 0.8, 0))
	end
	activa = true
	paso = "Tareas"
	for i, jugador in Players:GetPlayers() do
		llevar(jugador, i)
	end
	aviso("¡Preparad el vuelo! Cargad las maletas en el carro y llenad el depósito para abrir la puerta del hangar", "info")
	if conAnimal then
		task.delay(4, aviso, "¡El cocodrilo anda suelto! Dadle la merienda y metedlo en su jaula", "peligro")
	end

	local turbo = rng:NextInteger(3, math.max(3, nMaletas))
	local proxima = os.clock() + 1.5
	local fin = os.clock() + P.TIEMPO
	while activa do
		local ahora = os.clock()
		if creadas < nMaletas and ahora >= proxima and #toboganes > 0 then
			creadas += 1
			soltarMaleta(toboganes[(creadas - 1) % #toboganes + 1], creadas == turbo, valorMaleta, contrato.riesgo)
			proxima = ahora + (if creadas < 3 then 0.9 else P.INTERVALO_MALETA)
		end
		poner("Cuenta", math.max(0, math.ceil(fin - ahora)))
		if listo() then
			break
		elseif ahora >= fin then
			aviso("¡El avión no espera! Se abre la puerta: lo que falte, llevadlo a mano", "peligro")
			break
		end
		task.wait(0.2)
	end

	pie = pieRampa()
	local meta = Instance.new("Part")
	meta.Name = "DestinoPrep"
	meta.Anchored = true
	meta.CanCollide = false
	meta.CanQuery = false
	meta.CanTouch = false
	meta.Transparency = 1
	meta.Size = Vector3.one
	meta.Position = pie + Vector3.new(0, 1, 0)
	meta.Parent = sueltos
	destino = meta
	paso = "Conducir"
	abrirPuerta()
	ponerFlechas()
	aviso("¡Puerta abierta! Uno al volante del tractor y los demás, ¡al carro! Seguid las flechas hasta el avión", "bien")
	local finConducir = os.clock() + P.CONDUCIR
	while activa and not llegado() and os.clock() < finConducir do
		poner("Cuenta", math.max(0, math.ceil(finConducir - os.clock())))
		task.wait(0.2)
	end
	poner("Cuenta", 0)
	if activa then
		paso = "Descargar"
		if llegado() then
			aviso("¡Carro junto al avión! Meted las maletas en la bodega", "bien")
			Rafagas.lanzar("Confeti", pie + Vector3.new(0, 3, 0), 1.2)
		else
			aviso("¡Hora de embarcar! Llevad las maletas a la bodega como podáis", "peligro")
		end
	end
	for spawn, antes in guardados do
		spawn.Enabled = antes
	end
	aparcamiento.Enabled = false
	return true
end

function Preparacion.iniciar()
	for nombre, id in ModelosPreparacion.IDS do
		local caja = ModelosPreparacion.CAJAS[nombre]
		if caja then
			Activos.registrar(nombre, id, caja)
		end
	end
	for _, d in nave:GetDescendants() do
		if d:IsA("BasePart") then
			local visual = d:GetAttribute("Visual")
			if typeof(visual) == "string" then
				if d:GetAttribute("Movil") then
					Activos.vestirDinamico(d, visual)
				else
					local base = d:GetAttribute("Base")
					Activos.vestirFijo(d, visual, if typeof(base) == "number" then base else nil)
				end
			end
			if d.Name == "RampaTobogan" then
				d.CustomPhysicalProperties = PhysicalProperties.new(0.7, 0.42, 0.05, 1, 1)
			end
		end
	end
	for n = 1, 4 do
		local t = nave:FindFirstChild(`Tobogan{n}`)
		local luz = nave:FindFirstChild(`LuzTobogan{n}`)
		local boca = t and t:FindFirstChild("Boca")
		if boca and boca:IsA("BasePart") and luz and luz:IsA("BasePart") then
			table.insert(toboganes, { numero = n, boca = boca, luz = luz })
		end
	end
	avisoBombear = indicacion(surtidor, "Bombear", "Combustible del avión", 0.8, bombear)
	avisoCubo = indicacion(cubo, "Coger merienda", "Merienda del cocodrilo", 0, merienda)
	local pantalla = nave:FindFirstChild("PantallaSurtidor")
	if pantalla and pantalla:IsA("BasePart") then
		local gui = Instance.new("SurfaceGui")
		gui.Face = Enum.NormalId.Front
		gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		gui.PixelsPerStud = 120
		gui.LightInfluence = 0
		gui.Brightness = 1.3
		local fondo = Instance.new("Frame")
		fondo.Size = UDim2.fromScale(1, 1)
		fondo.BackgroundColor3 = Color3.fromRGB(27, 27, 33)
		fondo.BorderSizePixel = 0
		fondo.Parent = gui
		local barra = Instance.new("Frame")
		barra.Position = UDim2.fromScale(0.08, 0.6)
		barra.Size = UDim2.fromScale(0.84, 0.28)
		barra.BackgroundColor3 = Color3.fromRGB(52, 56, 63)
		barra.BorderSizePixel = 0
		barra.Parent = fondo
		local r = Instance.new("Frame")
		r.Size = UDim2.fromScale(0, 1)
		r.BackgroundColor3 = AMARILLO
		r.BorderSizePixel = 0
		r.Parent = barra
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1
		t.Position = UDim2.fromScale(0.05, 0.06)
		t.Size = UDim2.fromScale(0.9, 0.5)
		t.Font = Enum.Font.FredokaOne
		t.TextScaled = true
		t.TextColor3 = Color3.fromRGB(255, 244, 224)
		t.Text = ""
		t.Parent = fondo
		relleno, cifra = r, t
		gui.Parent = pantalla
	end
	aeropuerto.AncestryChanged:Connect(function()
		if not aeropuerto:IsDescendantOf(Workspace) then
			recoger()
		end
	end)
	Estado:GetAttributeChangedSignal("Fase"):Connect(function()
		local fase = Estado:GetAttribute("Fase")
		if fase == "Aeropuerto" or fase == "Vuelo" or fase == "Isla" then
			recoger()
		end
	end)
	Players.PlayerRemoving:Connect(function(jugador)
		esperas[jugador] = nil
	end)
	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		if acumulado < 0.1 or not activa then
			return
		end
		acumulado = 0
		actualizar()
	end)
end

return Preparacion
