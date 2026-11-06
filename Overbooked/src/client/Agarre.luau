--!strict
local CollectionService = game:GetService("CollectionService")
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local StarterPlayer = game:GetService("StarterPlayer")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Gui = require(ReplicatedStorage.Shared.Gui)
local AgarreVista = require(script.Parent.AgarreVista)
local Bofetada = require(script.Parent.Bofetada)
local Camara = require(script.Parent.Camara)
local Manos = require(script.Parent.Manos)
local Piloto = require(script.Parent.Piloto)
local Sonido = require(script.Parent.Sonido)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAgarrar = Remotos:WaitForChild("Agarrar") :: RemoteEvent
local RemotoSoltar = Remotos:WaitForChild("Soltar") :: RemoteEvent
local RemotoSostener = Remotos:WaitForChild("Sostener") :: RemoteEvent
local RemotoUsar = Remotos:WaitForChild("Usar") :: RemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado")

local Agarre = {}

local A = Config.AGARRE
local jugador = Players.LocalPlayer
local sostenido: Instance? = nil
local raiz: BasePart? = nil
local adjunto: Attachment? = nil
local posicion: AlignPosition? = nil
local orientacion: AlignOrientation? = nil
local tipoActual = ""
local estiloActual: Manos.Estilo = Manos.estilo("")
local tamano = Vector3.one
local confirmarAntes = 0
local usando = false
local ultimoUso = 0
local apuntado: Instance? = nil
local proximaBusqueda = 0
local proximosUtiles = 0
local utiles: { [string]: boolean } = {}
local tactiles: { [string]: boolean } = {}
local estadoTactil = -1
local cargaDesde: number? = nil
local giro = 0
local giroObjetivo = 0
local extra = 0
local dejarEn: CFrame? = nil
local dejarHasta = 0
local lentitud = 1
local ayudando = false
local ruedaActiva = false
local teclasVisibles: { [ProximityPrompt]: Enum.KeyCode } = {}

local GRANDES = { Pasajero = true, Cocodrilo = true, Jaula = true, Caja = true, CajaFragil = true, Carrito = true, Piano = true }
local TAPONES = { "Maleta", "Bolso", "Caja", "CajaFragil", "Carrito" }
local ASISTENCIA = math.rad(7)
local CARGA_MIN = 0.18
local CARGA_TOTAL = 0.8
local LENTO = 0.8
local GIRO_PASO = math.pi / 4

local vista = RaycastParams.new()
vista.FilterType = Enum.RaycastFilterType.Exclude
vista.RespectCanCollide = true
local choque = RaycastParams.new()
choque.FilterType = Enum.RaycastFilterType.Exclude
choque.RespectCanCollide = true
choque.CollisionGroup = "Sostenido"

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

local function esBoton(instancia: Instance): boolean
	local actual: Instance? = instancia
	while actual and actual ~= Workspace do
		if CollectionService:HasTag(actual, "BotonMano") then
			return true
		end
		actual = actual.Parent
	end
	return false
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

local function nombreDe(objeto: Instance): string
	local tipo = tipoDe(objeto)
	local def = Config.OBJETOS[tipo]
	return if def then def.nombre elseif tipo == "Pasajero" then "pasajero" else string.lower(tipo)
end

local function cuerpo(): (Model?, BasePart?, BasePart?)
	local personaje = jugador.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	local hrp = personaje and personaje:FindFirstChild("HumanoidRootPart")
	local cabeza = personaje and personaje:FindFirstChild("Head")
	if not personaje or not humanoide or humanoide.Health <= 0 or not hrp or not hrp:IsA("BasePart") or not cabeza or not cabeza:IsA("BasePart") then
		return nil, nil, nil
	end
	return personaje, hrp, cabeza
end

local function ralentizar(factor: number)
	if factor == lentitud then
		return
	end
	lentitud = factor
	local personaje = jugador.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	if humanoide then
		humanoide.WalkSpeed = StarterPlayer.CharacterWalkSpeed * factor
	end
end

local function rueda(_: string, estado: Enum.UserInputState, entrada: InputObject): Enum.ContextActionResult
	if entrada.UserInputType == Enum.UserInputType.MouseWheel then
		extra = math.clamp(extra + entrada.Position.Z * 0.6, -1.2, 4)
	elseif estado == Enum.UserInputState.Begin then
		extra = math.clamp(extra + (if entrada.KeyCode == Enum.KeyCode.DPadUp then 0.8 else -0.8), -1.2, 4)
	end
	return Enum.ContextActionResult.Sink
end

local function activarRueda(activa: boolean)
	if activa == ruedaActiva then
		return
	end
	ruedaActiva = activa
	if activa then
		ContextActionService:BindAction("DistanciaAgarre", rueda, false, Enum.UserInputType.MouseWheel, Enum.KeyCode.DPadUp, Enum.KeyCode.DPadDown)
	else
		ContextActionService:UnbindAction("DistanciaAgarre")
	end
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
	ayudando = false
	cargaDesde = nil
	dejarEn = nil
	AgarreVista.arco(nil)
	Camara.tension(0)
	Camara.sosteniendo(nil, "")
	ralentizar(1)
	activarRueda(false)
end

local function empezar(objeto: Instance)
	limpiar()
	local r = raizDe(objeto)
	if not r then
		return
	end
	sostenido, raiz = objeto, r
	tipoActual = tipoDe(objeto)
	estiloActual = Manos.estilo(tipoActual)
	tamano = if objeto:IsA("Model") then objeto:GetExtentsSize() else r.Size
	Camara.sosteniendo(objeto, tipoActual)
	giro, giroObjetivo, extra = 0, 0, 0
	local enMano = estiloActual.modo ~= "dos"
	local pesado = GRANDES[tipoActual] == true
	local masa = r.AssemblyMass
	local portador = objeto:GetAttribute("Portador")
	if typeof(portador) == "number" and portador ~= 0 and portador ~= jugador.UserId then
		ayudando = true
		confirmarAntes = os.clock() + 1
		ralentizar(LENTO)
		apuntado = nil
		AgarreVista.apuntar(nil, "")
		Manos.agarrar()
		Camara.sacudir(0.22)
		return
	end
	local a = Instance.new("Attachment")
	a.Name = "AgarreLocal"
	a.Parent = r
	local p = Instance.new("AlignPosition")
	p.Mode = Enum.PositionAlignmentMode.OneAttachment
	p.Attachment0 = a
	p.MaxForce = math.max(2500, masa * 1200)
	p.MaxVelocity = if enMano then 60 elseif pesado then 26 else 45
	p.Responsiveness = if enMano then 200 else math.clamp(140 / math.max(masa, 1), 7, 30)
	p.Position = r.Position
	p.Parent = r
	local o = Instance.new("AlignOrientation")
	o.Mode = Enum.OrientationAlignmentMode.OneAttachment
	o.Attachment0 = a
	o.MaxTorque = math.max(2500, masa * 1200)
	o.MaxAngularVelocity = if enMano then math.huge else 9
	o.Responsiveness = if enMano then 200 elseif pesado then 10 else 18
	o.CFrame = r.CFrame
	o.Parent = r
	adjunto, posicion, orientacion = a, p, o
	confirmarAntes = os.clock() + 1
	ralentizar(if pesado then LENTO else 1)
	activarRueda(not enMano)
	apuntado = nil
	AgarreVista.apuntar(nil, "")
	AgarreVista.aplastar(objeto)
	Manos.agarrar()
	Camara.sacudir(if pesado then 0.22 else 0.1)
end

local function velocidadLanzamiento(fuerza: number, mirada: Vector3): Vector3
	return mirada * (A.LANZAMIENTO + (A.LANZAMIENTO_FUERTE - A.LANZAMIENTO) * fuerza) + Vector3.new(0, 7 + 6 * fuerza, 0)
end

local function soltar(lanzar: boolean, fuerza: number)
	local r = raiz
	if not sostenido or not r then
		return
	end
	if ayudando then
		limpiar()
		RemotoSoltar:FireServer(Vector3.zero)
		Manos.abrir()
		return
	end
	local mirada = Workspace.CurrentCamera.CFrame.LookVector
	local velocidad = if lanzar then velocidadLanzamiento(fuerza, mirada) else r.AssemblyLinearVelocity
	if not lanzar and velocidad.Magnitude > 20 then
		velocidad = velocidad.Unit * 20
	end
	limpiar()
	r.AssemblyLinearVelocity = velocidad
	r.AssemblyAngularVelocity *= if lanzar then 1 else 0.3
	RemotoSoltar:FireServer(velocidad)
	Manos.abrir()
	if lanzar then
		Sonido.reproducir("Lanzar", nil, 0.7 + 0.4 * fuerza, 1.05 - 0.2 * fuerza)
		Camara.sacudir(0.1 + 0.25 * fuerza)
		Camara.impulsoFov(2 + 6 * fuerza)
	else
		Sonido.reproducir("Pop", nil, 0.35, 0.8)
	end
end

local function extension(rot: CFrame, t: Vector3, eje: Vector3): number
	return (math.abs(rot.RightVector:Dot(eje)) * t.X + math.abs(rot.UpVector:Dot(eje)) * t.Y + math.abs(rot.LookVector:Dot(eje)) * t.Z) / 2
end

local function plano(mirada: Vector3, respaldo: Vector3): Vector3
	local p = Vector3.new(mirada.X, 0, mirada.Z)
	if p.Magnitude < 0.05 then
		p = Vector3.new(respaldo.X, 0, respaldo.Z)
	end
	return if p.Magnitude > 0.001 then p.Unit else Vector3.zAxis
end

local function puntoDejar(personaje: Model, hrp: BasePart, r: BasePart): CFrame?
	local frente = plano(Workspace.CurrentCamera.CFrame.LookVector, hrp.CFrame.LookVector)
	local rot = CFrame.lookAt(Vector3.zero, frente) * CFrame.Angles(0, giro, 0)
	local fondo = extension(rot, tamano, frente)
	local lejos = 1.3 + fondo
	choque.FilterDescendantsInstances = { personaje, sostenido :: Instance }
	local pared = Workspace:Raycast(hrp.Position, frente * (lejos + fondo), choque)
	if pared then
		lejos = math.max(0.6, pared.Distance - fondo - 0.1)
	end
	local sobre = hrp.Position + frente * lejos + Vector3.new(0, 1.5, 0)
	local suelo = Workspace:Raycast(sobre, Vector3.new(0, -12, 0), choque)
	if not suelo then
		return nil
	end
	local alto = if sostenido and sostenido:IsA("Model") then tamano.Y / 2 else r.Size.Y / 2
	return CFrame.new(suelo.Position + Vector3.new(0, alto + 0.05, 0)) * rot
end

local function dejar()
	local personaje, hrp = cuerpo()
	local r = raiz
	if not sostenido or not r or not personaje or not hrp or dejarEn then
		return
	end
	if ayudando then
		soltar(false, 0)
		return
	end
	local cf = puntoDejar(personaje, hrp, r)
	if not cf then
		soltar(false, 0)
		return
	end
	cargaDesde = nil
	AgarreVista.arco(nil)
	dejarEn = cf
	dejarHasta = os.clock() + (if GRANDES[tipoActual] then 0.4 else 0.22)
end

local function terminarDejar(r: BasePart, cf: CFrame)
	limpiar()
	if (r.Position - cf.Position).Magnitude < 1 then
		r.CFrame = cf
	end
	r.AssemblyLinearVelocity = Vector3.zero
	r.AssemblyAngularVelocity = Vector3.zero
	RemotoSoltar:FireServer(Vector3.zero)
	Manos.abrir()
	Sonido.reproducir("Pop", r.Position, 0.6, 1.1)
end

local function visible(cabeza: BasePart, personaje: Model, objeto: Instance, r: BasePart): boolean
	vista.FilterDescendantsInstances = { personaje, objeto }
	return Workspace:Raycast(cabeza.Position, r.Position - cabeza.Position, vista) == nil
end

local function valido(objeto: Instance, hrp: BasePart): BasePart?
	local portador = objeto:GetAttribute("Portador")
	if typeof(portador) == "number" and portador ~= 0 and portador ~= jugador.UserId and objeto:GetAttribute("Pesado") ~= true then
		return nil
	end
	local r = raizDe(objeto)
	if not r or not r:IsDescendantOf(Workspace) or (r.Position - hrp.Position).Magnitude > A.DISTANCIA + 3 then
		return nil
	end
	return r
end

local function refrescarUtiles()
	table.clear(utiles)
	if #CollectionService:GetTagged("Fuego") > 0 then
		utiles.Extintor, utiles.Agua = true, true
	end
	if #CollectionService:GetTagged("Brecha") > 0 then
		utiles.Llave = true
		for _, t in TAPONES do
			utiles[t] = true
		end
	end
	if #CollectionService:GetTagged("PanelSuelto") > 0 then
		utiles.Piolet = true
	end
	for _, m in CollectionService:GetTagged("Pasajero") do
		local pedido = m:GetAttribute("Pedido")
		if typeof(pedido) == "string" and pedido ~= "" then
			utiles[pedido], utiles.Bandeja = true, true
		end
	end
	local fase = Estado:GetAttribute("Fase")
	local animal = Estado:GetAttribute("PrepAnimal")
	if Estado:GetAttribute("PrepPaso") == "Tareas" then
		utiles.Maleta = true
	end
	if typeof(animal) == "string" and animal ~= "" and animal ~= "Bodega" and animal ~= "Perdido" then
		utiles.Cocodrilo, utiles.Hamburguesa = true, true
	end
	if fase == "Isla" then
		for _, t in Config.ISLA.PIEZAS do
			utiles[t] = true
		end
		utiles.Tronco, utiles.Bengala = true, true
	end
end

local function buscar(origen: Vector3, direccion: Vector3): Instance?
	local personaje, hrp, cabeza = cuerpo()
	if not personaje or not hrp or not cabeza then
		return nil
	end
	local largo = A.DISTANCIA + (origen - cabeza.Position).Magnitude
	vista.FilterDescendantsInstances = { personaje }
	local golpe = Workspace:Raycast(origen, direccion * largo, vista)
	if golpe then
		if esBoton(golpe.Instance) then
			return nil
		end
		local directo = agarrable(golpe.Instance)
		local r = directo and valido(directo, hrp)
		if directo and r and visible(cabeza, personaje, directo, r) then
			return directo
		end
	end
	local candidatos: { { objeto: Instance, raiz: BasePart, puntos: number } } = {}
	for _, o in CollectionService:GetTagged("Agarrable") do
		local r = valido(o, hrp)
		if not r then
			continue
		end
		local hacia = r.Position - origen
		local d = hacia.Magnitude
		if d < 0.1 or d > largo then
			continue
		end
		local angulo = math.acos(math.clamp(direccion:Dot(hacia / d), -1, 1))
		local radio = math.max(r.Size.X, r.Size.Y, r.Size.Z) / 2 + (if o:IsA("Model") then 1 else 0)
		local margen = math.atan2(radio, d) + ASISTENCIA
		if angulo > margen then
			continue
		end
		local puntos = angulo / margen + 0.35 * d / largo - (if utiles[tipoDe(o)] then 0.35 else 0)
		table.insert(candidatos, { objeto = o, raiz = r, puntos = puntos })
	end
	table.sort(candidatos, function(a, b)
		return a.puntos < b.puntos
	end)
	for i = 1, math.min(4, #candidatos) do
		local c = candidatos[i]
		if visible(cabeza, personaje, c.objeto, c.raiz) then
			return c.objeto
		end
	end
	return nil
end

local function puedeAgarrar(): boolean
	if sostenido or Piloto.activo() then
		return false
	end
	local personaje = jugador.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	return personaje ~= nil and humanoide ~= nil and not humanoide.SeatPart and not personaje:GetAttribute("Ragdoll")
end

local function agarrarObjeto(objeto: Instance)
	if not puedeAgarrar() then
		return
	end
	RemotoAgarrar:FireServer(objeto)
	empezar(objeto)
	Sonido.reproducir("Coger", nil, 0.6)
end

local function intentarAgarrar()
	if not puedeAgarrar() then
		return
	end
	local camara = Workspace.CurrentCamera
	local objeto = apuntado or buscar(camara.CFrame.Position, camara.CFrame.LookVector)
	if objeto then
		agarrarObjeto(objeto)
	end
end

local function teclaOcupada(entrada: InputObject?): boolean
	if not entrada or entrada.UserInputType ~= Enum.UserInputType.Keyboard then
		return false
	end
	for prompt, k in teclasVisibles do
		if k == entrada.KeyCode and prompt.Enabled then
			return true
		end
	end
	return false
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

function Agarre.usando(): boolean
	return usando
end

function Agarre.dosManos(): boolean
	return sostenido ~= nil and estiloActual.modo == "dos"
end

local function accionAgarrar(_: string, estado: Enum.UserInputState): Enum.ContextActionResult
	if estado == Enum.UserInputState.Begin then
		if sostenido then
			soltar(false, 0)
		else
			intentarAgarrar()
		end
	end
	return Enum.ContextActionResult.Pass
end

local function accionLanzar(_: string, estado: Enum.UserInputState): Enum.ContextActionResult
	if estado == Enum.UserInputState.Begin then
		if sostenido then
			if not dejarEn then
				cargaDesde = os.clock()
			end
		elseif not Piloto.activo() then
			Bofetada.dar()
		end
	elseif estado == Enum.UserInputState.End or estado == Enum.UserInputState.Cancel then
		local desde = cargaDesde
		cargaDesde = nil
		if desde and sostenido and estado == Enum.UserInputState.End then
			local t = os.clock() - desde
			soltar(true, if t < CARGA_MIN then 0 else math.clamp((t - CARGA_MIN) / CARGA_TOTAL, 0, 1))
		end
		AgarreVista.arco(nil)
		Camara.tension(0)
	end
	return Enum.ContextActionResult.Pass
end

local function accionUsar(_: string, estado: Enum.UserInputState): Enum.ContextActionResult
	usando = estado == Enum.UserInputState.Begin or estado == Enum.UserInputState.Change
	return Enum.ContextActionResult.Pass
end

local function accionDejar(_: string, estado: Enum.UserInputState, entrada: InputObject?): Enum.ContextActionResult
	if not sostenido or teclaOcupada(entrada) then
		return Enum.ContextActionResult.Pass
	end
	if estado == Enum.UserInputState.Begin then
		dejar()
	end
	return Enum.ContextActionResult.Sink
end

local function accionGirar(_: string, estado: Enum.UserInputState, entrada: InputObject?): Enum.ContextActionResult
	if not sostenido or teclaOcupada(entrada) then
		return Enum.ContextActionResult.Pass
	end
	if estado == Enum.UserInputState.Begin then
		giroObjetivo += GIRO_PASO
		Sonido.reproducir("UiClick", nil, 0.3, 1.4)
	end
	return Enum.ContextActionResult.Sink
end

local function botonTactil(nombre: string, quiere: boolean, titulo: string, columna: number, fila: number, f: (string, Enum.UserInputState, InputObject) -> Enum.ContextActionResult)
	if quiere ~= (tactiles[nombre] == true) then
		tactiles[nombre] = quiere
		if not quiere then
			ContextActionService:UnbindAction(nombre)
			return
		end
		ContextActionService:BindAction(nombre, f, true)
		ContextActionService:SetPosition(nombre, Gui.posTactil(columna, fila))
	end
	if quiere then
		ContextActionService:SetTitle(nombre, titulo)
	end
end

local function sincronizarTactil()
	if not UserInputService.TouchEnabled then
		return
	end
	local personaje = jugador.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	local asiento = humanoide and humanoide.SeatPart
	local sentado = asiento ~= nil
	local torreta = asiento ~= nil and asiento.Name == "Torreta"
	local clave = (if sentado then 1 else 0) + (if sostenido then 2 else 0) + (if torreta then 4 else 0)
	if clave == estadoTactil then
		return
	end
	estadoTactil = clave
	local manos = not torreta and (sostenido ~= nil or not sentado)
	botonTactil("AgarrarTactil", manos, if sostenido then "Soltar" else "Coger", 1, 0, accionAgarrar)
	botonTactil("LanzarTactil", manos, if sostenido then "Lanzar" else "Bofetada", 0, 1, accionLanzar)
	botonTactil("UsarTactil", sostenido ~= nil, "Usar", 1, 1, accionUsar)
	botonTactil("DejarTactil", sostenido ~= nil and not torreta, "Dejar", 2, 1, accionDejar)
	if sostenido == nil then
		usando = false
	end
end

local function apuntar(ahora: number)
	if ahora >= proximosUtiles then
		proximosUtiles = ahora + 0.5
		refrescarUtiles()
	end
	if ahora < proximaBusqueda then
		return
	end
	proximaBusqueda = ahora + 0.05
	local camara = Workspace.CurrentCamera
	apuntado = if puedeAgarrar() then buscar(camara.CFrame.Position, camara.CFrame.LookVector) else nil
	AgarreVista.apuntar(apuntado, if apuntado then nombreDe(apuntado) else "")
end

local function sinAtravesar(origen: Vector3, destino: CFrame, radio: number): CFrame
	local delta = destino.Position - origen
	if delta.Magnitude < 0.05 then
		return destino
	end
	local golpe = Workspace:Spherecast(origen, radio, delta, choque)
	if golpe then
		return CFrame.new(origen + delta.Unit * math.max(golpe.Distance, 0.2)) * destino.Rotation
	end
	return destino
end

local function delante(cf: CFrame, ojos: Vector3, hrp: BasePart, ahora: number): CFrame
	local frente = plano(cf.LookVector, hrp.CFrame.LookVector)
	local rot = CFrame.lookAt(Vector3.zero, frente) * CFrame.Angles(0, giro, 0)
	if tipoActual == "Pasajero" then
		rot *= CFrame.Angles(0, 0, math.pi / 2)
	end
	local fondo = extension(rot, tamano, frente)
	local medio = extension(rot, tamano, Vector3.yAxis)
	local d = math.clamp(fondo + 1.5 + extra, fondo + 0.9, fondo + 6)
	local abultado = GRANDES[tipoActual] or math.max(tamano.X, tamano.Y, tamano.Z) > 1.5
	local objetivo = ojos + cf.LookVector * d - Vector3.yAxis * (medio + (if abultado then 0.85 else 0.25))
	if GRANDES[tipoActual] then
		local paso = math.clamp(Vector3.new(hrp.AssemblyLinearVelocity.X, 0, hrp.AssemblyLinearVelocity.Z).Magnitude / 16, 0, 1.5)
		local vaiven = math.sin(ahora * 3.1)
		objetivo += cf.RightVector * vaiven * 0.14 * (0.3 + paso) + Vector3.yAxis * math.abs(math.sin(ahora * 6.2)) * 0.1 * paso
		rot = CFrame.Angles(0, 0, vaiven * 0.05 * (0.3 + paso)) * rot
	end
	return CFrame.new(objetivo) * rot
end

local function arco(r: BasePart, personaje: Model, fuerza: number)
	local p = r.Position
	local v = velocidadLanzamiento(fuerza, Workspace.CurrentCamera.CFrame.LookVector)
	local g = Vector3.new(0, -Workspace.Gravity, 0)
	choque.FilterDescendantsInstances = { personaje, r }
	local lista: { Vector3 } = {}
	local normal: Vector3? = nil
	for _ = 1, 28 do
		local paso = 0.045
		local siguiente = p + v * paso + g * (0.5 * paso * paso)
		local golpe = Workspace:Raycast(p, siguiente - p, choque)
		if golpe then
			table.insert(lista, golpe.Position)
			normal = golpe.Normal
			break
		end
		table.insert(lista, siguiente)
		p = siguiente
		v += g * paso
	end
	AgarreVista.arco(lista, normal)
end

local function sostener(dt: number, ahora: number)
	local objeto, r = sostenido, raiz
	if not objeto or not r then
		return
	end
	local personaje, hrp, cabeza = cuerpo()
	if not objeto.Parent or not personaje or not hrp or not cabeza or personaje:GetAttribute("Ragdoll") then
		limpiar()
		return
	end
	local portador = objeto:GetAttribute("Portador")
	if ayudando then
		local marca = personaje:GetAttribute("Sosteniendo")
		local confirmado = typeof(marca) == "string" and marca ~= ""
		if confirmado then
			confirmarAntes = 0
		end
		if portador == 0 or portador == jugador.UserId or (not confirmado and (confirmarAntes == 0 or ahora > confirmarAntes)) then
			soltar(false, 0)
		end
		return
	end
	if portador == jugador.UserId then
		confirmarAntes = 0
	elseif confirmarAntes ~= 0 and ahora > confirmarAntes then
		limpiar()
		return
	elseif typeof(portador) == "number" and portador ~= 0 and portador ~= jugador.UserId then
		limpiar()
		return
	end
	local camara = Workspace.CurrentCamera
	local cf = camara.CFrame
	local ojos = if Camara.esTerceraPersona() then cabeza.Position else cf.Position
	choque.FilterDescendantsInstances = { personaje, objeto }
	giro += (giroObjetivo - giro) * (1 - math.exp(-dt * 14))
	local destino: CFrame
	local fijo = dejarEn
	if fijo then
		if ahora >= dejarHasta then
			terminarDejar(r, fijo)
			return
		end
		destino = fijo
	else
		local mano, punto = Manos.punto(personaje)
		if estiloActual.modo ~= "dos" and mano and punto then
			destino = Manos.marco(estiloActual, mano.CFrame, punto, hrp.CFrame, tamano) * Manos.desfase(estiloActual, r.Size) * CFrame.Angles(0, giro, 0)
		else
			destino = delante(cf, ojos, hrp, ahora)
		end
		local radio = math.clamp(math.min(tamano.X, tamano.Y, tamano.Z) / 2, 0.15, 0.7)
		destino = sinAtravesar(ojos, destino, radio)
	end
	local p, o = posicion, orientacion
	if objeto:GetAttribute("Pesado") == true then
		local ayuda = objeto:GetAttribute("Ayudantes")
		local solo = not (typeof(ayuda) == "number" and ayuda > 0)
		ralentizar(if solo then Config.CARGA_ESPECIAL.PIANO_SOLO else LENTO)
		if p then
			p.MaxVelocity = if solo then Config.CARGA_ESPECIAL.PIANO_VELOCIDAD_SOLO else 26
		end
	end
	if p then
		p.Position = destino.Position + (if fijo then Vector3.zero else hrp.AssemblyLinearVelocity * dt)
	end
	if o then
		o.CFrame = destino.Rotation
	end
	local desde = cargaDesde
	if desde and ahora - desde >= CARGA_MIN then
		local fuerza = math.clamp((ahora - desde - CARGA_MIN) / CARGA_TOTAL, 0, 1)
		arco(r, personaje, fuerza)
		Camara.tension(fuerza)
	end
	if usando and ahora - ultimoUso >= Config.HERRAMIENTAS.CADENCIA then
		ultimoUso = ahora
		RemotoUsar:FireServer(cf.LookVector)
		if tipoActual == "Extintor" and Workspace.Gravity < 60 then
			hrp.AssemblyLinearVelocity -= cf.LookVector * 4
		end
	end
end

function Agarre.iniciar()
	AgarreVista.iniciar(function()
		local o = apuntado
		if o then
			agarrarObjeto(o)
		end
	end)
	ContextActionService:BindAction("Agarrar", accionAgarrar, false, Enum.UserInputType.MouseButton1, Enum.KeyCode.ButtonR2)
	ContextActionService:BindAction("Lanzar", accionLanzar, false, Enum.UserInputType.MouseButton2, Enum.KeyCode.ButtonL2)
	Bofetada.iniciar()
	ContextActionService:BindAction("Usar", accionUsar, false, Enum.KeyCode.F, Enum.KeyCode.ButtonX)
	ContextActionService:BindAction("DejarObjeto", accionDejar, false, Enum.KeyCode.G, Enum.KeyCode.ButtonL1)
	ContextActionService:BindAction("GirarObjeto", accionGirar, false, Enum.KeyCode.R, Enum.KeyCode.ButtonR1)

	ProximityPromptService.PromptShown:Connect(function(prompt)
		teclasVisibles[prompt] = prompt.KeyboardKeyCode
	end)
	ProximityPromptService.PromptHidden:Connect(function(prompt)
		teclasVisibles[prompt] = nil
	end)

	UserInputService.TouchTapInWorld:Connect(function(punto: Vector2, procesado: boolean)
		if procesado or not puedeAgarrar() then
			return
		end
		local rayo = Workspace.CurrentCamera:ScreenPointToRay(punto.X, punto.Y)
		local objeto = buscar(rayo.Origin, rayo.Direction)
		if objeto then
			agarrarObjeto(objeto)
		end
	end)

	RemotoSostener.OnClientEvent:Connect(function(objeto)
		if typeof(objeto) == "Instance" then
			empezar(objeto)
			confirmarAntes = 0
		else
			limpiar()
		end
	end)

	jugador.CharacterAdded:Connect(function()
		lentitud = 1
		limpiar()
	end)

	RunService.PreSimulation:Connect(function(dt)
		sincronizarTactil()
		local ahora = os.clock()
		if sostenido then
			sostener(dt, ahora)
		else
			apuntar(ahora)
		end
	end)
end

return Agarre
