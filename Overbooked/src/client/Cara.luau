--!strict
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local BocaVoz = require(script.Parent.BocaVoz)

type Hueso = { b: Bone, r: CFrame, ri: CFrame, lado: number }
type Muelle = { x: number, v: number }
type Gesto = { [string]: number }
export type Mirada = { escala: number, alto: number, pupila: number, mareo: number, temblor: number }
type Rostro = {
	jugador: Player,
	personaje: Model,
	cabeza: BasePart,
	raiz: BasePart,
	huesos: { [string]: Hueso },
	completo: boolean,
	reintento: number,
	actual: Gesto,
	boca: Muelle,
	cejas: Muelle,
	ojos: Muelle,
	mejillas: Muelle,
	lengua: Muelle,
	flop: Muelle,
	gritoDesde: number?,
	nariz: Vector3,
	narizV: Vector3,
	posAntes: Vector3?,
	velAntes: Vector3,
	nivelAntes: number,
	parpadeo: number,
	parpadeoHasta: number,
	proximoParpadeo: number,
	ticHasta: number,
	ticLado: number,
	proximoTic: number,
	cejaHasta: number,
	cejaLado: number,
	proximaCeja: number,
	blepHasta: number,
	proximoBlep: number,
	proximoOlfateo: number,
	ragdollDesde: number?,
	cayendo: number,
	mirada: Mirada,
}

local Cara = {}

local ALCANCE = 120
local GRITO_NIVEL = 0.75
local GRITO_TIEMPO = 0.4
local LENGUA_FUERA = 0.4
local NOMBRES = { "BocaSup", "BocaInf", "Lengua", "CejaIzq", "CejaDer", "MejillaIzq", "MejillaDer", "Nariz" }
local CLAVES = { "boca", "cejas", "giro", "lengua", "lado", "mejillas", "ojos", "alto", "pupila", "temblor", "mareo" }
local NEUTRO: Gesto = { boca = 0, cejas = 0, giro = 0, lengua = 0, lado = 0, mejillas = 0, ojos = 1, alto = 1, pupila = 1, temblor = 0, mareo = 0 }
local GESTOS: { [string]: Gesto } = {
	Neutro = NEUTRO,
	Susto = { boca = 0.35, cejas = 0.9, giro = -1, lengua = 0, lado = 0, mejillas = 0.2, ojos = 1.2, alto = 1, pupila = 0.55, temblor = 1, mareo = 0 },
	Mareo = { boca = 0.4, cejas = 0.3, giro = 0.4, lengua = 1, lado = 1, mejillas = 0, ojos = 1, alto = 0.85, pupila = 1, temblor = 0, mareo = 1 },
	Feliz = { boca = 0.5, cejas = 0.6, giro = -0.3, lengua = 0, lado = 0, mejillas = 1, ojos = 1, alto = 0.3, pupila = 1, temblor = 0, mareo = 0 },
	Grito = { boca = 1.15, cejas = 1.2, giro = -0.5, lengua = 0.9, lado = 0, mejillas = 0.3, ojos = 1.32, alto = 1, pupila = 0.7, temblor = 0.6, mareo = 0 },
	Sorpresa = { boca = 0.6, cejas = 1.4, giro = 0, lengua = 0, lado = 0, mejillas = 0, ojos = 1.32, alto = 1, pupila = 0.7, temblor = 0, mareo = 0 },
	Enfado = { boca = 0.12, cejas = -0.8, giro = 1, lengua = 0, lado = 0, mejillas = 0, ojos = 1, alto = 0.62, pupila = 1, temblor = 0.4, mareo = 0 },
}

local rng = Random.new()
local rostros: { [Model]: Rostro } = {}
local avion: Instance? = nil
local general = "Neutro"
local generalHasta = 0

local function anunciar(nombre: string, duracion: number)
	general = nombre
	generalHasta = os.clock() + duracion
end

local function muelle(m: Muelle, objetivo: number, k: number, d: number, dt: number)
	m.v += ((objetivo - m.x) * k - m.v * d) * dt
	m.x += m.v * dt
end

local function enlazar(r: Rostro)
	local completo = true
	for _, nombre in NOMBRES do
		if r.huesos[nombre] then
			continue
		end
		local b = r.personaje:FindFirstChild(nombre, true)
		if not (b and b:IsA("Bone")) then
			completo = false
			continue
		end
		b.Transform = CFrame.identity
		local base = b:FindFirstAncestorWhichIsA("BasePart") or r.cabeza
		local rel = base.CFrame:ToObjectSpace(b.WorldCFrame)
		r.huesos[nombre] = { b = b, r = rel.Rotation, ri = rel.Rotation:Inverse(), lado = math.sign(rel.Position.X) }
	end
	r.completo = completo
	r.reintento = os.clock() + 3
end

local function crear(jugador: Player, personaje: Model): Rostro?
	local cabeza = personaje:FindFirstChild("Head")
	local raiz = personaje:FindFirstChild("HumanoidRootPart")
	if not (cabeza and cabeza:IsA("BasePart") and raiz and raiz:IsA("BasePart")) then
		return nil
	end
	local ahora = os.clock()
	local actual: Gesto = {}
	for _, clave in CLAVES do
		actual[clave] = NEUTRO[clave]
	end
	local r: Rostro = {
		jugador = jugador,
		personaje = personaje,
		cabeza = cabeza,
		raiz = raiz,
		huesos = {},
		completo = false,
		reintento = 0,
		actual = actual,
		boca = { x = 0, v = 0 },
		cejas = { x = 0, v = 0 },
		ojos = { x = 1, v = 0 },
		mejillas = { x = 0, v = 0 },
		lengua = { x = 0, v = 0 },
		flop = { x = 0, v = 0 },
		gritoDesde = nil,
		nariz = Vector3.zero,
		narizV = Vector3.zero,
		posAntes = nil,
		velAntes = Vector3.zero,
		nivelAntes = 0,
		parpadeo = 0,
		parpadeoHasta = 0,
		proximoParpadeo = ahora + rng:NextNumber(1, 4),
		ticHasta = 0,
		ticLado = 1,
		proximoTic = ahora + rng:NextNumber(2, 6),
		cejaHasta = 0,
		cejaLado = 1,
		proximaCeja = ahora + rng:NextNumber(4, 9),
		blepHasta = 0,
		proximoBlep = ahora + rng:NextNumber(10, 25),
		proximoOlfateo = ahora + rng:NextNumber(3, 7),
		ragdollDesde = nil,
		cayendo = 0,
		mirada = { escala = 1, alto = 1, pupila = 1, mareo = 0, temblor = 0 },
	}
	enlazar(r)
	rostros[personaje] = r
	return r
end

local function expresion(r: Rostro, ahora: number, susto: boolean): string
	if r.cayendo > 0.45 then
		return "Grito"
	end
	if r.personaje:GetAttribute("Ragdoll") == true then
		local desde = r.ragdollDesde or ahora
		r.ragdollDesde = desde
		return if ahora - desde < 0.9 then "Enfado" else "Mareo"
	end
	r.ragdollDesde = nil
	if ahora < generalHasta then
		return general
	end
	return if susto then "Susto" else "Neutro"
end

local function poner(h: Hueso?, d: CFrame)
	if h then
		h.b.Transform = h.ri * d * h.r
	end
end

local function idle(r: Rostro, ahora: number, quieto: boolean)
	if ahora > r.proximoParpadeo then
		r.parpadeoHasta = ahora + 0.11
		r.proximoParpadeo = ahora + (if rng:NextNumber() < 0.15 then 0.22 else rng:NextNumber(1.8, 5))
	end
	if not quieto then
		return
	end
	if ahora > r.proximoTic then
		r.ticHasta = ahora + 0.35
		r.ticLado = if rng:NextNumber() < 0.5 then -1 else 1
		r.proximoTic = ahora + rng:NextNumber(2.5, 6)
	end
	if ahora > r.proximaCeja then
		r.cejaHasta = ahora + 0.9
		r.cejaLado = if rng:NextNumber() < 0.5 then -1 else 1
		r.proximaCeja = ahora + rng:NextNumber(4, 9)
	end
	if ahora > r.proximoBlep then
		r.blepHasta = ahora + 0.7
		r.proximoBlep = ahora + rng:NextNumber(12, 25)
	end
	if ahora > r.proximoOlfateo then
		r.narizV += Vector3.new(0, 0.9, -0.3)
		r.proximoOlfateo = ahora + rng:NextNumber(3, 7)
	end
end

local function nariz(r: Rostro, dt: number)
	local pos = r.cabeza.Position
	local acel = Vector3.zero
	local antes = r.posAntes
	if antes then
		local vel = (pos - antes) / dt
		acel = r.cabeza.CFrame:VectorToObjectSpace((vel - r.velAntes) / dt)
		if acel.Magnitude > 300 then
			acel = acel.Unit * 300
		end
		r.velAntes = if vel.Magnitude < 200 then vel else Vector3.zero
	end
	r.posAntes = pos
	r.narizV += (-r.nariz * 260 - r.narizV * 7 - acel * 0.012) * dt
	r.nariz += r.narizV * dt
	if r.nariz.Magnitude > 0.06 then
		r.nariz = r.nariz.Unit * 0.06
	end
end

local function animar(r: Rostro, ahora: number, dt: number, susto: boolean)
	if not r.completo and ahora > r.reintento then
		enlazar(r)
	end
	local vel = r.raiz.AssemblyLinearVelocity.Y
	r.cayendo = if vel < -35 then r.cayendo + dt else 0
	local nombre = expresion(r, ahora, susto)
	local g = GESTOS[nombre]
	local a = r.actual
	for _, clave in CLAVES do
		local rapidez = if clave == "alto" then 18 else 10
		a[clave] += (g[clave] - a[clave]) * (1 - math.exp(-rapidez * dt))
	end
	local voz = BocaVoz.nivel(r.jugador)
	r.cejas.v += math.max(0, voz - r.nivelAntes) * 30
	r.nivelAntes = voz
	idle(r, ahora, nombre == "Neutro" and voz < 0.05)
	nariz(r, dt)
	local t = ahora
	local tic = if ahora < r.ticHasta then 1 else 0
	local blep = if ahora < r.blepHasta then 1 else 0
	local cejaIdle = if ahora < r.cejaHasta then 1 else 0
	r.parpadeo += ((if ahora < r.parpadeoHasta then 1 else 0) - r.parpadeo) * (1 - math.exp(-45 * dt))

	if voz > GRITO_NIVEL then
		r.gritoDesde = r.gritoDesde or ahora
	else
		r.gritoDesde = nil
	end
	local desde = r.gritoDesde
	local gritando = nombre == "Grito" or (desde ~= nil and ahora - desde > GRITO_TIEMPO)
	muelle(r.flop, if gritando then 1 else 0, 120, 10, dt)
	local flop = math.clamp(r.flop.x, 0, 1.2)
	local f1 = math.min(flop, 1)

	muelle(r.boca, math.max(a.boca, voz ^ 0.75 * 1.05, flop * 1.15) + tic * 0.08 + blep * 0.12, 380, 16, dt)
	muelle(r.cejas, a.cejas + voz * 0.7 + flop * 0.5, 300, 10, dt)
	muelle(r.ojos, a.ojos + voz * 0.12 + flop * 0.3, 260, 9, dt)
	muelle(r.mejillas, a.mejillas + voz * 0.6 + flop * 1.1, 200, 9, dt)
	local k = math.clamp(r.boca.x, -0.05, 1.35)
	muelle(r.lengua, (0.07 * math.max(0, k) + 0.14 * a.lengua + 0.12 * blep) * (1 - f1) + LENGUA_FUERA * flop, 260, 11, dt)

	local m = r.mirada
	m.escala = r.ojos.x
	m.alto = math.max(0.06, a.alto * (1 - r.parpadeo))
	m.pupila = a.pupila * (1 - 0.3 * f1)
	m.mareo = a.mareo
	m.temblor = math.max(a.temblor, 0.5 * f1)

	local cabeza = r.cabeza
	if cabeza.LocalTransparencyModifier > 0.5 or not r.huesos.BocaSup then
		return
	end
	local s = r.personaje:GetScale()
	local h = r.huesos
	local lateral = tic * 0.03 * r.ticLado + a.mareo * math.sin(t * 2.3) * 0.035
	poner(h.BocaSup, CFrame.new(lateral * s, 0.065 * k * s, 0))
	poner(h.BocaInf, CFrame.new((lateral * 1.3 - a.lado * 0.04) * s, -0.25 * k * s, -0.06 * k * s))
	local meneo = (math.sin(t * 14) * 0.3 * math.clamp(k, 0, 1) + math.sin(t * 9) * 0.3 * a.lengua) * (1 - f1)
	local aleteo = flop * (math.sin(t * 23) * 0.55 + math.sin(t * 11.3) * 0.25)
	local caida = (0.35 - math.sin(t * 11) * 0.25) * a.lengua * (1 - f1) + flop * (0.45 + math.sin(t * 17) * 0.18)
	poner(
		h.Lengua,
		CFrame.fromEulerAnglesYXZ(-caida, a.lado * 0.44 + meneo + aleteo, flop * math.sin(t * 19 + 1) * 0.35)
			* CFrame.new(-a.lado * 0.03 * s, -0.03 * a.lengua * s, -r.lengua.x * s)
	)
	local temblor = math.sin(t * 43) * 0.006 * a.temblor
	for _, ceja in { "CejaIzq", "CejaDer" } do
		local c = h[ceja]
		if c then
			local alto = r.cejas.x * 0.06 + (if c.lado == r.cejaLado then cejaIdle * 0.07 else 0) + temblor + a.mareo * c.lado * 0.04 * math.sin(t * 3)
			local frente = 0.05 * math.max(0, -r.cejas.x) + 0.03 * math.max(0, a.giro)
			poner(c, CFrame.new(0, alto * s, -frente * s) * CFrame.Angles(0, 0, c.lado * a.giro * math.rad(22) + temblor * 4))
		end
	end
	local p = 0.04 * r.mejillas.x + 0.025 * math.max(0, k)
	for _, mejilla in { "MejillaIzq", "MejillaDer" } do
		local c = h[mejilla]
		if c then
			poner(c, CFrame.new(c.lado * 0.4 * p * s, 0.035 * a.mejillas * s, -0.8 * p * s))
		end
	end
	local n = r.nariz + Vector3.new(0, voz * 0.012 * math.sin(t * 20), 0)
	poner(h.Nariz, CFrame.new(n * s))
end

local function paso(dt: number)
	dt = math.clamp(dt, 1 / 240, 1 / 30)
	local ahora = os.clock()
	local foco = Workspace.CurrentCamera.CFrame.Position
	local susto = false
	if avion then
		local turbulencia = avion:GetAttribute("Turbulencia")
		susto = (typeof(turbulencia) == "number" and turbulencia > 0.45) or avion:GetAttribute("CaidaLibre") == true
	end
	local vistos: { [Model]: boolean } = {}
	for _, jugador in Players:GetPlayers() do
		local personaje = jugador.Character
		local cabeza = personaje and personaje:FindFirstChild("Head")
		if not (personaje and cabeza and cabeza:IsA("BasePart")) or (cabeza.Position - foco).Magnitude > ALCANCE then
			continue
		end
		vistos[personaje] = true
		local r = rostros[personaje] or crear(jugador, personaje)
		if r then
			animar(r, ahora, dt, susto)
		end
	end
	for personaje in rostros do
		if not vistos[personaje] then
			rostros[personaje] = nil
		end
	end
end

function Cara.mirada(personaje: Model): Mirada?
	local r = rostros[personaje]
	return if r then r.mirada else nil
end

function Cara.iniciar()
	RunService.PreSimulation:Connect(paso)
	task.spawn(function()
		local a = Workspace:WaitForChild("Avion")
		avion = a
		a:GetAttributeChangedSignal("Aterrizaje"):Connect(function()
			local v = a:GetAttribute("Aterrizaje")
			if v == "Perfecto" or v == "Bueno" then
				anunciar("Feliz", 4)
			elseif v == "Duro" then
				anunciar("Sorpresa", 2)
			end
		end)
		a:GetAttributeChangedSignal("Pajaros"):Connect(function()
			anunciar("Sorpresa", 1.5)
		end)
		a:GetAttributeChangedSignal("Fase"):Connect(function()
			if a:GetAttribute("Fase") == "Estrellado" then
				anunciar("Susto", 2.5)
			end
		end)
	end)
end

return Cara
