--!strict
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Manos = require(script.Parent.Manos)

local Camara = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local trauma = 0
local tiempo = 0
local inclinacion = 0
local cabeceo = 0
local fovExtra = 0
local terceraPersona = false
local fovBase = 80
local aplicado = CFrame.identity
type Brazos = { motores: { [string]: Motor6D }, inclinacion: number, giro: number, codo: number }
local articulaciones: { [Model]: Brazos } = setmetatable({}, { __mode = "k" }) :: any
local MOTORES = { "RightShoulder", "LeftShoulder", "RightElbow", "LeftElbow", "RightWrist", "LeftWrist", "Root", "Waist" }
local POSE_BRAZO: { [string]: { number } } = {
	puno = { 58, 42, 0, 12 },
	vaso = { 58, 42, 0, 12 },
	palma = { 48, 58, -90, 12 },
	colgar = { 40, 20, 0, 6 },
	dos = { 62, 40, 0, 16 },
}
local tensionLanzar = 0
local alcanceHasta = 0
local lanzarHasta = 0
local ALTURA_OJOS = Vector3.new(0, -0.44, 0)
local OJOS = 1.5 + ALTURA_OJOS.Y

local VISTA: { [string]: { number } } = {
	reposo = { 0.54, -0.78, 0.86, 50, 0, -22, 30 },
	alcance = { 0.2, -0.46, 1.1, 68, 6, -12, 16 },
	pulsar = { 0.1, -0.42, 1.0, 74, 0, -6, 10 },
	bofetadaAtras = { 0.8, -0.5, 0.8, 64, 40, -10, -10 },
	bofetadaGolpe = { -0.02, -0.36, 0.92, 74, 28, 0, 22 },
	lanzar = { 0.24, -0.44, 1.2, 66, 8, -30, 12 },
	puno = { 0.32, -0.66, 0.92, 62, 0, -18, 12 },
	vaso = { 0.32, -0.64, 0.92, 64, 0, -18, 12 },
	palma = { 0.3, -0.66, 1.0, 32, 10, -180, 8 },
	colgar = { 0.46, -0.7, 0.95, 58, 4, -60, 8 },
	abrazo = { -0.06, 0.75, 0.1, 78, 35, 0, 0 },
}
local TAN_REF = math.tan(math.rad(40))

type Lado = { cf: CFrame?, signo: number, base: CFrame, hombro: string, codo: string, muneca: string, parte: string }

local function baseMano(signo: number): CFrame
	local dedos = Vector3.new(0.12 * signo, -0.3, 0).Unit
	local palma = Vector3.new(-signo, 0, 0)
	palma = (palma - dedos * dedos:Dot(palma)).Unit
	local mano = CFrame.fromMatrix(Vector3.zero, dedos, palma, dedos:Cross(palma))
	local vista = CFrame.fromMatrix(Vector3.zero, Vector3.new(0, 0, -1), Vector3.new(0, -1, 0), Vector3.new(-1, 0, 0))
	return vista * mano:Inverse()
end

local derecha: Lado = { cf = nil, signo = 1, base = baseMano(1), hombro = "RightShoulder", codo = "RightElbow", muneca = "RightWrist", parte = "RightHand" }
local izquierda: Lado = { cf = nil, signo = -1, base = baseMano(-1), hombro = "LeftShoulder", codo = "LeftElbow", muneca = "LeftWrist", parte = "LeftHand" }
local manosVisibles = false
local giroPrevio: CFrame? = nil
local retrasoX, retrasoY = 0, 0
local inercia = Vector3.zero
local fasePaso, mezclaPaso, airePaso, caidaPaso = 0, 0, 0, 0
local sostenidoPropio: Instance? = nil
local tipoPropio = ""
local agarreDesde = 0

function Camara.sacudir(cantidad: number)
	trauma = math.min(1, trauma + cantidad)
end

function Camara.impulsoFov(cantidad: number)
	fovExtra = math.max(fovExtra, cantidad)
end

function Camara.fov(valor: number)
	fovBase = math.clamp(valor, 60, 100)
end

function Camara.esTerceraPersona(): boolean
	return terceraPersona
end

function Camara.paso(fase: number, mezcla: number, aire: number, caida: number)
	fasePaso, mezclaPaso, airePaso, caidaPaso = fase, mezcla, aire, caida
end

function Camara.sosteniendo(objeto: Instance?, tipo: string)
	if objeto and objeto ~= sostenidoPropio then
		agarreDesde = os.clock()
	end
	sostenidoPropio = objeto
	tipoPropio = if objeto then tipo else ""
	Manos.sostener(tipoPropio)
end

local forzada = false
local preferida = false

local function aplicarModo()
	local activa = forzada or preferida
	terceraPersona = activa
	giroPrevio = nil
	if activa then
		jugador.CameraMode = Enum.CameraMode.Classic
		jugador.CameraMaxZoomDistance = 9.5
		jugador.CameraMinZoomDistance = 7
	else
		jugador.CameraMinZoomDistance = 0.5
		jugador.CameraMaxZoomDistance = 0.5
		jugador.CameraMode = Enum.CameraMode.LockFirstPerson
	end
end

function Camara.terceraPersona(activa: boolean)
	forzada = activa
	aplicarModo()
end

function Camara.preferirTercera(activa: boolean)
	preferida = activa
	aplicarModo()
end

local function ruido(t: number, semilla: number): number
	return math.noise(t * 9, semilla) * 2
end

local function girar(m: Motor6D?, giro: CFrame)
	if m then
		local rot = m.C0.Rotation
		m.Transform = rot:Inverse() * giro * rot
	end
end

local function angulos(v: Vector3): (number, number)
	return math.atan2(v.Y, -v.Z), math.atan2(-v.X, -v.Z)
end

local function apuntarAlObjeto(personaje: Model, datos: Brazos, estilo: Manos.Estilo)
	local valor = personaje:FindFirstChild("Sostenido")
	local objeto = if valor and valor:IsA("ObjectValue") then valor.Value else nil
	local raiz = if objeto and objeto:IsA("Model") then objeto.PrimaryPart elseif objeto and objeto:IsA("BasePart") then objeto else nil
	local torso = personaje:FindFirstChild("UpperTorso")
	local hombro = datos.motores.RightShoulder
	local mano, punto = Manos.punto(personaje)
	if not (raiz and torso and torso:IsA("BasePart") and hombro and mano) then
		return
	end
	local origen = torso.CFrame * hombro.C0.Position
	local actual = torso.CFrame:VectorToObjectSpace((punto or mano.Position) - origen)
	local agarre = (raiz.CFrame * Manos.desfase(estilo, raiz.Size):Inverse()).Position
	local plano = (agarre - origen) * Vector3.new(1, 0, 1)
	if plano.Magnitude > 0.01 then
		agarre -= plano.Unit * Manos.separacion(estilo, raiz.Size)
	end
	local objetivo = torso.CFrame:VectorToObjectSpace(agarre - origen)
	local altoA, ladoA = angulos(actual)
	local altoB, ladoB = angulos(objetivo)
	datos.inclinacion = math.clamp(datos.inclinacion + (altoB - altoA) * 0.5, -0.8, 1.5)
	if estilo.modo ~= "dos" then
		datos.giro = math.clamp(datos.giro + (ladoB - ladoA) * 0.4, -0.6, 0.9)
		datos.codo = math.clamp(datos.codo + (objetivo.Magnitude - actual.Magnitude) * 1.5, -1.3, 1.2)
	end
end

local function giroVista(p: { number }, signo: number, base: CFrame): CFrame
	return CFrame.Angles(0, 0, signo * math.rad(p[7])) * CFrame.fromEulerAnglesYXZ(math.rad(p[4]), signo * math.rad(p[5]), signo * math.rad(p[6])) * base
end

local function enVista(p: { number }, signo: number, tv: number, ancho: number, base: CFrame): CFrame
	local z = p[3] * math.sqrt(TAN_REF / tv)
	return CFrame.new(signo * p[1] * ancho * tv * z, p[2] * tv * z, -z) * giroVista(p, signo, base)
end

local function caja(objeto: Instance): (CFrame?, Vector3?)
	if objeto:IsA("Model") then
		return objeto:GetBoundingBox()
	elseif objeto:IsA("BasePart") then
		return objeto.CFrame, objeto.Size
	end
	return nil, nil
end

local function abrazo(lado: Lado, vista: CFrame, tv: number, ancho: number): CFrame?
	local objeto = sostenidoPropio
	if not objeto then
		return nil
	end
	local cf, tamano = caja(objeto)
	if not cf or not tamano then
		return nil
	end
	local frente = vista.LookVector * Vector3.new(1, 0, 1)
	if frente.Magnitude < 0.05 then
		frente = vista.UpVector * Vector3.new(1, 0, 1)
	end
	local marco = CFrame.lookAt(cf.Position, cf.Position + frente.Unit)
	local r = marco:ToObjectSpace(cf).Rotation
	local h = tamano / 2
	local function extension(eje: Vector3): number
		return math.abs(r.RightVector:Dot(eje)) * h.X + math.abs(r.UpVector:Dot(eje)) * h.Y + math.abs(r.LookVector:Dot(eje)) * h.Z
	end
	local p = VISTA.abrazo
	local sitio = CFrame.new(lado.signo * (extension(Vector3.xAxis) + p[1]), extension(Vector3.yAxis) * p[2], extension(Vector3.zAxis) + p[3])
	local l = vista:ToObjectSpace(marco * sitio * giroVista(p, lado.signo, lado.base))
	local fondo = math.max(0.6, -l.Z)
	local x = math.clamp(l.X, -0.85 * ancho * tv * fondo, 0.85 * ancho * tv * fondo)
	local y = math.clamp(l.Y, -0.85 * tv * fondo, 0.6 * tv * fondo)
	return CFrame.new(x, y, -fondo) * l.Rotation
end

local function hacia(desde: { number }, a: { number }, t: number): { number }
	local r = table.create(7, 0)
	for i = 1, 7 do
		r[i] = desde[i] + (a[i] - desde[i]) * t
	end
	return r
end

local function objetivoMano(lado: Lado, ahora: number, vista: CFrame, tv: number, ancho: number): (CFrame, number)
	local derechaActiva = lado.signo > 0
	local estilo = if tipoPropio ~= "" then Manos.estilo(tipoPropio) else nil
	local rapidez = 14
	if estilo and estilo.modo == "dos" then
		local cf = abrazo(lado, vista, tv, ancho)
		if cf then
			return cf, 18
		end
	end
	local p = VISTA.reposo
	if derechaActiva then
		local pulsarHasta, bofetadaHasta = Manos.momentos()
		local alcance = math.clamp((alcanceHasta - ahora) / 0.45, 0, 1)
		if estilo and estilo.modo ~= "dos" then
			p = VISTA[estilo.modo] or VISTA.vaso
			if tensionLanzar > 0 then
				p = hacia(p, { p[1] + 0.12, p[2] + 0.12, p[3] - 0.22, p[4] + 14, p[5] - 6, p[6], p[7] - 8 }, tensionLanzar)
			end
			local recien = 1 - math.clamp((ahora - agarreDesde) / 0.22, 0, 1)
			if recien > 0 then
				p = hacia(p, VISTA.alcance, math.sin(recien * math.pi * 0.5))
				rapidez = 22
			end
		elseif ahora < pulsarHasta then
			local t = 1 - (pulsarHasta - ahora) / 0.6
			p = hacia(p, VISTA.pulsar, math.sin(math.clamp(t / 0.7, 0, 1) * math.pi))
			rapidez = 26
		elseif ahora < bofetadaHasta then
			local t = 1 - (bofetadaHasta - ahora) / 0.45
			p = if t < 0.2 then VISTA.bofetadaAtras elseif t < 0.5 then VISTA.bofetadaGolpe else VISTA.reposo
			rapidez = if t < 0.5 then 34 else 12
		elseif ahora < lanzarHasta then
			p = hacia(p, VISTA.lanzar, math.sin((1 - (lanzarHasta - ahora) / 0.3) * math.pi))
			rapidez = 28
		elseif alcance > 0 then
			p = hacia(p, VISTA.alcance, math.sin(alcance * math.pi))
			rapidez = 20
		end
	end
	return enVista(p, lado.signo, tv, ancho, lado.base), rapidez
end

local function vida(lado: Lado, ahora: number): (Vector3, CFrame)
	local s = math.sin(fasePaso)
	local m = math.min(mezclaPaso, 1.2)
	local respira = math.sin(ahora * 1.7 + lado.signo * 0.5)
	local deriva = math.sin(ahora * 0.83 + lado.signo * 1.3)
	local quieto = math.max(0, 1 - m)
	local x = s * 0.022 * m + deriva * 0.006 * quieto
	local y = -(math.abs(s) - 0.64) * 0.05 * m + respira * 0.012 * quieto + airePaso * 0.05 - caidaPaso * 0.1
	local z = math.cos(fasePaso) * 0.015 * m * lado.signo
	return Vector3.new(x, y, z), CFrame.Angles(respira * 0.02 * quieto - caidaPaso * 0.12, 0, -s * 0.05 * m)
end

local function primeraPersona(personaje: Model, datos: Brazos, dt: number): boolean
	local m = datos.motores
	local raiz = personaje:FindFirstChild("HumanoidRootPart")
	local cam = Workspace.CurrentCamera
	if not (raiz and raiz:IsA("BasePart") and m.Root and m.Waist) or cam.CameraType == Enum.CameraType.Scriptable then
		return false
	end
	local vista = cam.CFrame * aplicado:Inverse()
	if (vista.Position - (raiz.Position + Vector3.new(0, OJOS, 0))).Magnitude > 2 then
		return false
	end
	local ahora = os.clock()
	local previo = giroPrevio
	giroPrevio = vista.Rotation
	if previo then
		local rx, ry = previo:ToObjectSpace(vista.Rotation):ToEulerAnglesYXZ()
		retrasoX = math.clamp(retrasoX - rx * 0.35, -0.1, 0.1)
		retrasoY = math.clamp(retrasoY - ry * 0.35, -0.14, 0.14)
	end
	local decae = math.exp(-dt * 9)
	retrasoX *= decae
	retrasoY *= decae
	local v = vista:VectorToObjectSpace(raiz.AssemblyLinearVelocity)
	inercia = inercia:Lerp(Vector3.new(math.clamp(v.X, -20, 20), math.clamp(v.Y, -40, 40), math.clamp(v.Z, -20, 20)), 1 - math.exp(-dt * 5))
	local empujon = CFrame.new(-inercia.X * 0.003, -inercia.Y * 0.0025, -inercia.Z * 0.002)
	local retraso = CFrame.fromEulerAnglesYXZ(retrasoX, retrasoY, 0)
	local tv = math.tan(math.rad(fovBase / 2))
	local tamano = cam.ViewportSize
	local ancho = math.clamp(tamano.X / math.max(tamano.Y, 1), 1.2, 1.78)
	local inicio = raiz.CFrame * m.Root.C0 * m.Root.Transform * m.Root.C1:Inverse() * m.Waist.C0 * m.Waist.Transform * m.Waist.C1:Inverse()
	for _, lado in { derecha, izquierda } do
		local hombro, codo, muneca = m[lado.hombro], m[lado.codo], m[lado.muneca]
		if not (hombro and codo and muneca) then
			return false
		end
		local objetivo, rapidez = objetivoMano(lado, ahora, vista, tv, ancho)
		local antes = lado.cf
		local actual = if antes then antes:Lerp(objetivo, 1 - math.exp(-dt * rapidez)) else objetivo
		lado.cf = actual
		hombro.Transform = CFrame.identity
		codo.Transform = CFrame.identity
		local antebrazo = inicio * hombro.C0 * hombro.C1:Inverse() * codo.C0 * codo.C1:Inverse()
		local desvio, balanceo = vida(lado, ahora)
		local mundo = vista * retraso * empujon * CFrame.new(actual.Position + desvio) * balanceo * actual.Rotation
		muneca.Transform = muneca.C0:Inverse() * antebrazo:Inverse() * mundo * muneca.C1
	end
	return true
end

local function poseSosteniendo(personaje: Model, dt: number)
	if personaje:GetAttribute("Ragdoll") then
		return
	end
	local esPropio = personaje == jugador.Character
	local atributo = personaje:GetAttribute("Sosteniendo")
	local tipo = if esPropio then tipoPropio elseif typeof(atributo) == "string" then atributo else ""
	local enPrimera = esPropio and not terceraPersona
	local datos = articulaciones[personaje]
	if tipo == "" and not enPrimera then
		if datos then
			girar(datos.motores.RightWrist, CFrame.identity)
			girar(datos.motores.LeftWrist, CFrame.identity)
		end
		return
	end
	if not datos then
		local lista: { [string]: Motor6D } = {}
		for _, nombre in MOTORES do
			local m = personaje:FindFirstChild(nombre, true)
			if m and m:IsA("Motor6D") then
				lista[nombre] = m
			end
		end
		if not lista.RightShoulder then
			return
		end
		datos = { motores = lista, inclinacion = 0, giro = 0, codo = 0 }
		articulaciones[personaje] = datos
	end
	local m = datos.motores
	if enPrimera then
		manosVisibles = primeraPersona(personaje, datos, dt)
		if manosVisibles then
			return
		end
		derecha.cf, izquierda.cf = nil, nil
		if tipo == "" then
			for _, nombre in { "RightShoulder", "LeftShoulder", "RightElbow", "LeftElbow", "RightWrist", "LeftWrist" } do
				girar(m[nombre], CFrame.identity)
			end
			return
		end
	end
	local estilo = Manos.estilo(tipo)
	if not esPropio then
		apuntarAlObjeto(personaje, datos, estilo)
	end
	local p = POSE_BRAZO[estilo.modo]
	local tension = if esPropio then tensionLanzar else 0
	local dentro = math.rad(p[4])
	local subir = CFrame.Angles(datos.inclinacion + math.rad(p[1]) + math.rad(40) * tension, 0, 0)
	local codo = CFrame.Angles(math.max(0, math.rad(p[2]) - datos.codo) + math.rad(40) * tension, 0, 0)
	girar(m.RightShoulder, CFrame.Angles(0, dentro + datos.giro, 0) * subir)
	girar(m.RightElbow, codo)
	girar(m.RightWrist, CFrame.Angles(0, math.rad(p[3]), 0))
	if estilo.modo == "dos" then
		girar(m.LeftShoulder, CFrame.Angles(0, -dentro, 0) * subir)
		girar(m.LeftElbow, codo)
	else
		girar(m.LeftShoulder, CFrame.Angles(math.rad(5), 0, -math.rad(12)))
		girar(m.LeftElbow, CFrame.Angles(math.rad(20), 0, 0))
	end
	girar(m.LeftWrist, CFrame.identity)
end

local function contorno(parte: BasePart, activo: boolean)
	local h = parte:FindFirstChild("ContornoManopla")
	if h and h:IsA("Highlight") then
		if h.Enabled ~= activo then
			h.Enabled = activo
		end
	elseif activo then
		local nuevo = Instance.new("Highlight")
		nuevo.Name = "ContornoManopla"
		nuevo.FillTransparency = 1
		nuevo.OutlineColor = Color3.fromRGB(44, 58, 94)
		nuevo.OutlineTransparency = 0.35
		nuevo.DepthMode = Enum.HighlightDepthMode.Occluded
		nuevo.Adornee = parte
		nuevo.Parent = parte
	end
end

function Camara.tension(fuerza: number)
	if fuerza == 0 and tensionLanzar > 0.1 then
		lanzarHasta = os.clock() + 0.3
	end
	tensionLanzar = fuerza
end

function Camara.alcanzar()
	Manos.abrir()
	alcanceHasta = os.clock() + 0.45
end

function Camara.iniciar()
	Camara.terceraPersona(false)
	local camara = Workspace.CurrentCamera
	camara.FieldOfView = fovBase

	RunService.PreSimulation:Connect(function(dt)
		local foco = camara.CFrame.Position
		manosVisibles = false
		for _, otro in Players:GetPlayers() do
			local personaje = otro.Character
			local raiz = personaje and personaje.PrimaryPart
			if personaje and raiz and (raiz.Position - foco).Magnitude < 90 then
				poseSosteniendo(personaje, math.min(dt, 0.1))
			end
		end
		Manos.vista(manosVisibles)
	end)

	RunService:BindToRenderStep("OverbookedDeshacer", Enum.RenderPriority.Camera.Value - 1, function()
		if aplicado ~= CFrame.identity then
			local cam = Workspace.CurrentCamera
			cam.CFrame = cam.CFrame * aplicado:Inverse()
			aplicado = CFrame.identity
		end
	end)
	RunService:BindToRenderStep("OverbookedCamara", Enum.RenderPriority.Camera.Value + 1, function(dt)
		tiempo += dt
		local cam = Workspace.CurrentCamera
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		local extra = CFrame.identity
		if humanoide and humanoide.CameraOffset ~= ALTURA_OJOS then
			humanoide.CameraOffset = ALTURA_OJOS
		end
		if humanoide and not terceraPersona and mezclaPaso > 0.01 then
			local s = math.sin(fasePaso)
			local m = math.min(mezclaPaso, 1.2)
			extra *= CFrame.new(s * 0.03 * m, (math.abs(s) - 0.64) * 0.045 * m, 0) * CFrame.Angles(0, 0, s * 0.006 * m)
		end
		local enTierra = avion:GetAttribute("EnTierra")
		local alabeo = avion:GetAttribute("Alabeo")
		local cab = avion:GetAttribute("Cabeceo")
		local objetivoInclinacion = if enTierra == false and typeof(alabeo) == "number" then math.rad(alabeo) * 0.22 else 0
		local objetivoCabeceo = if enTierra == false and typeof(cab) == "number" then math.rad(cab) * 0.12 else 0
		local suavizado = math.min(1, dt * 3)
		inclinacion += (objetivoInclinacion - inclinacion) * suavizado
		cabeceo += (objetivoCabeceo - cabeceo) * suavizado
		if trauma > 0 then
			local t = trauma * trauma
			extra *= CFrame.Angles(ruido(tiempo, 1) * 0.06 * t, ruido(tiempo, 2) * 0.06 * t, ruido(tiempo, 3) * 0.08 * t)
			trauma = math.max(0, trauma - dt * 1.4)
		end
		local total = extra * CFrame.Angles(cabeceo, 0, inclinacion)
		cam.CFrame = cam.CFrame * total
		aplicado = total
		fovExtra = math.max(0, fovExtra - dt * 18)
		cam.FieldOfView = fovBase + fovExtra
		if personaje then
			for _, lado in { derecha, izquierda } do
				local parte = personaje:FindFirstChild(lado.parte)
				if parte and parte:IsA("BasePart") then
					if manosVisibles then
						parte.LocalTransparencyModifier = 0
					end
					contorno(parte, manosVisibles)
				end
			end
		end
	end)
end

return Camara
