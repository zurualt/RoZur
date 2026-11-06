--!strict
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

export type Estilo = {
	modo: string,
	altura: number,
}

type DefDedo = { nombre: string, i: number, abre: number }
type Dedo = { a: Bone, b: Bone, ejeA: Vector3, ejeB: Vector3, abrir: Vector3, abre: number, i: number }
type Mano = { dedos: { Dedo }, valores: { number } }
type Estado = { derecha: Mano?, izquierda: Mano?, tipo: string, cambio: number, reintento: number }

local Manos = {}

local jugador = Players.LocalPlayer
local estados: { [Model]: Estado } = setmetatable({}, { __mode = "k" }) :: any
local pulsarHasta = 0
local abrirHasta = 0
local bofetadaHasta = 0
local tipoPropio = ""
local primera = false

local AGARRE_MANO = Vector3.new(-0.199, -0.123, 0)
local PALMA = Vector3.new(-0.929, -0.371, 0)
local DESFASE_PALMA = -0.12
local INCLINAR_HERRAMIENTA = CFrame.Angles(-math.rad(20), 0, 0)
local DISTANCIA = 90
local SUAVIDAD = 16

local POSES: { [string]: { number } } = {
	relajada = { 26, 28, 24, 20, -6 },
	primera = { 10, 14, 14, 10, 4 },
	abierta = { -12, -8, -10, -4, 30 },
	agarre = { 40, 60, 30, 26, -6 },
	pulsar = { -4, -2, 40, 38, -12 },
	palma = { 4, 6, -8, 0, 12 },
	bofetada = { -16, -10, -14, -6, 32 },
	dos = { 34, 46, 22, 18, 0 },
	sosten = { 18, 24, 26, 22, -8 },
}

local POSE_MODO: { [string]: { number } } = {
	puno = POSES.agarre,
	vaso = POSES.agarre,
	colgar = POSES.agarre,
	palma = POSES.palma,
	dos = POSES.dos,
}

local DEDOS: { DefDedo } = {
	{ nombre = "Manopla", i = 1, abre = 0 },
	{ nombre = "Pulgar", i = 3, abre = 1 },
}

local ESTILOS: { [string]: Estilo } = {
	Extintor = { modo = "puno", altura = 0.6 },
	Llave = { modo = "puno", altura = -0.65 },
	Piolet = { modo = "puno", altura = -0.65 },
	Bengala = { modo = "puno", altura = -0.5 },
	RadioAntena = { modo = "puno", altura = -0.6 },
	Agua = { modo = "vaso", altura = 0 },
	Cafe = { modo = "vaso", altura = 0 },
	Biberon = { modo = "vaso", altura = 0 },
	Lata = { modo = "vaso", altura = 0 },
	Hamburguesa = { modo = "palma", altura = 0 },
	Bandeja = { modo = "palma", altura = 0 },
	Coco = { modo = "palma", altura = 0 },
	RadioBateria = { modo = "palma", altura = 0 },
	RadioCaja = { modo = "palma", altura = 0 },
	Maleta = { modo = "colgar", altura = 0 },
	Bolso = { modo = "colgar", altura = 0 },
}
local DOS_MANOS: Estilo = { modo = "dos", altura = 0 }

function Manos.estilo(tipo: string): Estilo
	return ESTILOS[tipo] or DOS_MANOS
end

function Manos.desfase(estilo: Estilo, tamano: Vector3): CFrame
	if estilo.modo == "palma" then
		return CFrame.new(0, tamano.Y / 2 + DESFASE_PALMA, 0)
	elseif estilo.modo == "colgar" then
		return CFrame.new(0, -tamano.Y / 2 - 0.08, 0) * CFrame.Angles(0, math.pi / 2, 0)
	elseif estilo.modo == "dos" then
		return CFrame.identity
	end
	return CFrame.new(0, -estilo.altura * tamano.Y / 2, 0)
end

function Manos.separacion(estilo: Estilo, tamano: Vector3): number
	if estilo.modo == "vaso" or estilo.modo == "puno" then
		return math.max(0, math.min(tamano.X, tamano.Z) / 2 - 0.1)
	end
	return 0
end

function Manos.marco(estilo: Estilo, mano: CFrame, punto: Vector3, cuerpo: CFrame, tamano: Vector3): CFrame
	local giro = if estilo.modo == "puno" then cuerpo.Rotation * INCLINAR_HERRAMIENTA else cuerpo.Rotation
	return CFrame.new(punto + mano:VectorToWorldSpace(PALMA) * Manos.separacion(estilo, tamano)) * giro
end

function Manos.punto(personaje: Model): (BasePart?, Vector3?)
	local mano = personaje:FindFirstChild("RightHand")
	if not mano or not mano:IsA("BasePart") then
		return nil, nil
	end
	local nudillo = mano:FindFirstChild("DerManopla1")
	if nudillo and nudillo:IsA("Bone") then
		return mano, mano.CFrame * (nudillo.CFrame.Position + AGARRE_MANO)
	end
	local agarre = mano:FindFirstChild("RightGripAttachment")
	if agarre and agarre:IsA("Attachment") then
		return mano, agarre.WorldPosition
	end
	return mano, nil
end

function Manos.agarrar()
	local personaje = jugador.Character
	local estado = personaje and estados[personaje]
	if estado then
		estado.cambio = os.clock()
	end
end

function Manos.pulsar()
	pulsarHasta = os.clock() + 0.6
end

function Manos.abrir()
	abrirHasta = os.clock() + 0.45
end

function Manos.bofetada()
	bofetadaHasta = os.clock() + 0.45
end

function Manos.sostener(tipo: string)
	tipoPropio = tipo
end

function Manos.vista(enPrimera: boolean)
	primera = enPrimera
end

function Manos.momentos(): (number, number)
	return pulsarHasta, bofetadaHasta
end

local function reposo(hueso: Bone): CFrame
	local cf = hueso.CFrame
	local padre = hueso.Parent
	while padre and padre:IsA("Bone") do
		cf = padre.CFrame * cf
		padre = padre.Parent
	end
	return cf
end

local function montarMano(parte: Instance?, prefijo: string, derecha: boolean): Mano?
	if not parte then
		return nil
	end
	local palma = Vector3.new(if derecha then -1 else 1, 0, 0)
	local cierre = (palma + Vector3.new(0, -0.2, 0.3)).Unit
	local frente = Vector3.new(0, 0, -1)
	local dedos: { Dedo } = {}
	for _, def in DEDOS do
		local a = parte:FindFirstChild(prefijo .. def.nombre .. "1", true)
		local b = parte:FindFirstChild(prefijo .. def.nombre .. "2", true)
		if not (a and a:IsA("Bone") and b and b:IsA("Bone")) then
			continue
		end
		local ra, rb = reposo(a), reposo(b)
		local dir = (rb.Position - ra.Position).Unit
		local eje = dir:Cross(if def.nombre == "Pulgar" then cierre else palma).Unit
		table.insert(dedos, {
			a = a,
			b = b,
			ejeA = ra:VectorToObjectSpace(eje),
			ejeB = rb:VectorToObjectSpace(eje),
			abrir = ra:VectorToObjectSpace(dir:Cross(frente).Unit),
			abre = def.abre,
			i = def.i,
		})
	end
	if #dedos == 0 then
		return nil
	end
	return { dedos = dedos, valores = table.clone(POSES.relajada) }
end

local function mover(mano: Mano?, objetivo: { number }, k: number)
	if not mano then
		return
	end
	local v = mano.valores
	for i = 1, 5 do
		v[i] += (objetivo[i] - v[i]) * k
	end
	for _, d in mano.dedos do
		local curva = CFrame.fromAxisAngle(d.ejeA, math.rad(v[d.i]))
		d.a.Transform = if d.abre ~= 0 then CFrame.fromAxisAngle(d.abrir, math.rad(v[5] * d.abre)) * curva else curva
		d.b.Transform = CFrame.fromAxisAngle(d.ejeB, math.rad(v[d.i + 1]))
	end
end

local function paso(personaje: Model, propio: boolean, ahora: number, k: number)
	local previo = estados[personaje]
	local estado: Estado
	if previo and (previo.derecha or ahora < previo.reintento) then
		estado = previo
	else
		estado = {
			derecha = montarMano(personaje:FindFirstChild("RightHand"), "Der", true),
			izquierda = montarMano(personaje:FindFirstChild("LeftHand"), "Izq", false),
			tipo = if previo then previo.tipo else "",
			cambio = if previo then previo.cambio else 0,
			reintento = ahora + 3,
		}
		estados[personaje] = estado
	end
	if not estado.derecha and not estado.izquierda then
		return
	end
	local s = personaje:GetAttribute("Sosteniendo")
	local tipo = if propio then tipoPropio elseif typeof(s) == "string" then s else ""
	if tipo ~= estado.tipo then
		if ahora - estado.cambio > 0.4 then
			estado.cambio = ahora
		end
		estado.tipo = tipo
	end
	local estilo = if tipo ~= "" then Manos.estilo(tipo) else nil
	local dos = estilo ~= nil and estilo.modo == "dos"
	local reposo = if propio and primera then POSES.primera else POSES.relajada
	local der, izq = reposo, reposo
	if personaje:GetAttribute("Ragdoll") then
		return
	elseif ahora - estado.cambio < 0.14 then
		der = POSES.abierta
		izq = if dos then POSES.abierta else izq
	elseif estilo then
		der = if propio and primera and (estilo.modo == "vaso" or estilo.modo == "puno") then POSES.sosten else POSE_MODO[estilo.modo]
		izq = if dos then der else izq
	elseif propio and ahora < pulsarHasta then
		der = POSES.pulsar
	elseif propio and ahora < bofetadaHasta then
		der = POSES.bofetada
	elseif propio and ahora < abrirHasta then
		der = POSES.abierta
	end
	mover(estado.derecha, der, k)
	mover(estado.izquierda, izq, k)
end

function Manos.iniciar()
	RunService.PreSimulation:Connect(function(dt)
		local ahora = os.clock()
		local k = 1 - math.exp(-dt * SUAVIDAD)
		local foco = Workspace.CurrentCamera.CFrame.Position
		for _, otro in Players:GetPlayers() do
			local personaje = otro.Character
			local raiz = personaje and personaje.PrimaryPart
			if personaje and raiz and (raiz.Position - foco).Magnitude < DISTANCIA then
				paso(personaje, otro == jugador, ahora, k)
			end
		end
	end)
end

return Manos
