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

local AGARRE_MANO = Vector3.new(-0.117, 0.03, -0.03)
local DISTANCIA = 90
local SUAVIDAD = 16

local POSES: { [string]: { number } } = {
	relajada = { 18, 22, 22, 28, 8, 10, 0 },
	abierta = { -8, -6, -8, -6, -25, -5, 14 },
	agarre = { 60, 70, 60, 70, 35, 30, 0 },
	pulsar = { 0, 0, 85, 95, 40, 45, 0 },
	palma = { 5, 8, 5, 8, -15, 0, 6 },
	dos = { 45, 55, 45, 55, 20, 20, 6 },
}

local POSE_MODO: { [string]: { number } } = {
	puno = POSES.agarre,
	vaso = POSES.agarre,
	colgar = POSES.agarre,
	palma = POSES.palma,
	dos = POSES.dos,
}

local DEDOS: { DefDedo } = {
	{ nombre = "Indice", i = 1, abre = 1 },
	{ nombre = "Medio", i = 3, abre = 0 },
	{ nombre = "Menique", i = 3, abre = -1 },
	{ nombre = "Pulgar", i = 5, abre = 0 },
}

local ESTILOS: { [string]: Estilo } = {
	Extintor = { modo = "puno", altura = 0.6 },
	Llave = { modo = "puno", altura = -0.65 },
	Piolet = { modo = "puno", altura = -0.65 },
	Bengala = { modo = "puno", altura = -0.5 },
	RadioAntena = { modo = "puno", altura = -0.6 },
	Agua = { modo = "vaso", altura = 0 },
	Cafe = { modo = "vaso", altura = 0 },
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
		return CFrame.new(0, tamano.Y / 2 + 0.02, 0)
	elseif estilo.modo == "colgar" then
		return CFrame.new(0, -tamano.Y / 2 - 0.08, 0) * CFrame.Angles(0, math.pi / 2, 0)
	elseif estilo.modo == "dos" then
		return CFrame.identity
	end
	return CFrame.new(0, -estilo.altura * tamano.Y / 2, 0)
end

function Manos.marco(estilo: Estilo, mano: CFrame, punto: Vector3, cuerpo: CFrame): CFrame
	local giro = if estilo.modo == "puno" then mano.Rotation * CFrame.Angles(-math.pi / 2, 0, 0) else cuerpo.Rotation
	return CFrame.new(punto) * giro
end

function Manos.punto(personaje: Model): (BasePart?, Vector3?)
	local mano = personaje:FindFirstChild("RightHand")
	if not mano or not mano:IsA("BasePart") then
		return nil, nil
	end
	local medio = mano:FindFirstChild("DerMedio1")
	if medio and medio:IsA("Bone") then
		return mano, mano.CFrame * (medio.CFrame.Position + AGARRE_MANO)
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
			return nil
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
	return { dedos = dedos, valores = table.clone(POSES.relajada) }
end

local function mover(mano: Mano?, objetivo: { number }, k: number)
	if not mano then
		return
	end
	local v = mano.valores
	for i = 1, 7 do
		v[i] += (objetivo[i] - v[i]) * k
	end
	for _, d in mano.dedos do
		local curva = CFrame.fromAxisAngle(d.ejeA, math.rad(v[d.i]))
		d.a.Transform = if d.abre ~= 0 then CFrame.fromAxisAngle(d.abrir, math.rad(v[7] * d.abre)) * curva else curva
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
	local tipo = if typeof(s) == "string" then s else ""
	if tipo ~= estado.tipo then
		if ahora - estado.cambio > 0.4 then
			estado.cambio = ahora
		end
		estado.tipo = tipo
	end
	local estilo = if tipo ~= "" then Manos.estilo(tipo) else nil
	local dos = estilo ~= nil and estilo.modo == "dos"
	local der, izq = POSES.relajada, POSES.relajada
	if personaje:GetAttribute("Ragdoll") then
		return
	elseif ahora - estado.cambio < 0.14 then
		der = POSES.abierta
		izq = if dos then POSES.abierta else izq
	elseif estilo then
		der = POSE_MODO[estilo.modo]
		izq = if dos then der else izq
	elseif propio and ahora < pulsarHasta then
		der = POSES.pulsar
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
