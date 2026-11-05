--!strict
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Audio = require(ReplicatedStorage.Shared.Audio)
local Piezas = require(ReplicatedStorage.Shared.PiezasRoturas)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Camara = require(script.Parent.Camara)
local Rafagas = require(script.Parent.Rafagas)
local Sonido = require(script.Parent.Sonido)

type Opciones = { vel: Vector3, giro: Vector3, vida: number?, humo: boolean?, silbato: boolean? }
type Extra = { modelo: Model, mov: ((number) -> CFrame)? }

local Roturas = {}

local DURACION_PARTIDO = 4.6
local CORTE = Piezas.CORTE
local PIVOTE = Vector3.new(0, 96.25, CORTE)
local VENTANAS = { -41.5, -37, -32.5, -28, -19, -14.5, -10 }
local MALETAS = { "Maleta1", "Maleta2", "Maleta3" }
local EXCLUIDAS = { Exterior = true, Casco = true, Objetos = true, Carga = true, Pasajeros = true, Peligros = true, Piratas = true, AvionExterior = true }

local avion = Workspace:WaitForChild("Avion") :: Model
local rng = Random.new()
local ritmo = 1
local generacion = 0
local efectos = Instance.new("Folder")
efectos.Name = "RoturasLocal"

local escondidas: { BasePart } = {}
local recortadas: { [BasePart]: { tam: Vector3, cf: CFrame } } = {}
local apagadas: { Instance } = {}
local calcas: { Decal } = {}

local function copia(nombre: string, marco: CFrame?, escala: number?): Model?
	local carpeta = ReplicatedStorage:FindFirstChild("Roturas")
	local p = carpeta and carpeta:FindFirstChild(nombre)
	if not p or not p:IsA("Model") then
		return nil
	end
	local m = p:Clone()
	if escala then
		m:ScaleTo(m:GetScale() * escala)
	end
	if marco then
		m:PivotTo(marco * m:GetPivot())
	end
	m.Parent = efectos
	return m
end

local function sonar(nombre: string, alterno: string, donde: (Vector3 | BasePart)?, volumen: number?, tono: number?)
	Sonido.reproducir(if Audio.IDS[nombre] then nombre else alterno, donde, volumen, tono)
end

local function velocidadMundo(): number
	local v = avion:GetAttribute("Velocidad")
	return math.max(if typeof(v) == "number" then v / 3.6 * 0.35 else 0, 45)
end

local function animar(duracion: number, paso: (number) -> ())
	local mia = generacion
	local t = 0
	while t < duracion and mia == generacion do
		local dt = RunService.PreRender:Wait()
		t = math.min(duracion, t + dt * ritmo)
		paso(t)
	end
end

local function estela(m: Model, centro: Vector3)
	local parte = m.PrimaryPart or m:FindFirstChildWhichIsA("BasePart", true)
	if not parte then
		return
	end
	local a = Instance.new("Attachment")
	a.Parent = parte
	a.WorldPosition = centro
	local e = Instance.new("ParticleEmitter")
	e.Texture = VFX.textura("Humo1")
	e.Color = ColorSequence.new(Color3.fromRGB(70, 66, 64))
	e.Size = NumberSequence.new(2.5, 8)
	e.Transparency = NumberSequence.new(0.25, 1)
	e.Lifetime = NumberRange.new(1.2, 1.8)
	e.Rate = 28
	e.Speed = NumberRange.new(0, 1)
	e.Rotation = NumberRange.new(0, 360)
	e.RotSpeed = NumberRange.new(-40, 40)
	e.Acceleration = Vector3.new(0, 3, 35)
	e.Parent = a
	local chispas = VFX.chispas(a)
	chispas.Rate = 18
end

local function volar(m: Model, o: Opciones, extras: { Extra }?)
	local inicio = m:GetPivot()
	local centro = m:GetBoundingBox().Position
	local otros = {}
	local lista: { Extra } = extras or {}
	for _, e in lista do
		table.insert(otros, { modelo = e.modelo, inicio = e.modelo:GetPivot(), mov = e.mov })
	end
	local vw = velocidadMundo()
	local w = o.giro.Magnitude
	local eje = if w > 0 then o.giro.Unit else Vector3.xAxis
	if o.humo then
		estela(m, centro)
	end
	if o.silbato then
		local parte = m.PrimaryPart or m:FindFirstChildWhichIsA("BasePart", true)
		if parte then
			Sonido.reproducir("SilbatoCaida", parte, 1, 1)
		end
	end
	animar(o.vida or 5, function(t)
		local atras = vw * (t - (1 - math.exp(-1.1 * t)) / 1.1)
		local d = o.vel * t + Vector3.new(0, -13 * t * t, atras)
		local mov = CFrame.new(centro + d) * CFrame.fromAxisAngle(eje, w * t) * CFrame.new(-centro)
		m:PivotTo(mov * inicio)
		for _, e in otros do
			e.modelo:PivotTo(mov * (if e.mov then e.mov(t) else CFrame.identity) * e.inicio)
		end
	end)
	m:Destroy()
	for _, e in otros do
		e.modelo:Destroy()
	end
end

local function temblar(m: Model, eje: Vector3, punto: Vector3, duracion: number, fuerza: number)
	local inicio = m:GetPivot()
	animar(duracion, function(t)
		local a = math.sin(t * 48) * fuerza * (1 - t / duracion)
		m:PivotTo(CFrame.new(punto) * CFrame.fromAxisAngle(eje, a) * CFrame.new(-punto) * inicio)
	end)
end

local function maletazo()
	local m = copia(MALETAS[rng:NextInteger(1, #MALETAS)])
	if not m then
		return
	end
	local s = if rng:NextNumber() < 0.5 then -1 else 1
	local ventana = Vector3.new(s * 9.3, 104.5, VENTANAS[rng:NextInteger(1, #VENTANAS)])
	local giro = CFrame.Angles(0, math.pi / 2, 0)
	local inicio = m:GetPivot()
	local desde = ventana + Vector3.new(s * 5, 3, -45)
	animar(0.55, function(t)
		local a = t / 0.55
		m:PivotTo(CFrame.new(desde:Lerp(ventana, a * a)) * giro * CFrame.Angles(0, 0, (1 - a) * 7) * inicio)
	end)
	Sonido.reproducir("Bonk", ventana, 1.3)
	Rafagas.lanzar("Bonk", ventana, 0.9)
	Camara.sacudir(0.12)
	animar(0.8, function(t)
		m:PivotTo(CFrame.new(ventana + Vector3.new(0, -t * 0.4, 0)) * giro * CFrame.Angles(0, 0, math.sin(t * 30) * 0.05) * inicio)
	end)
	volar(m, { vel = Vector3.new(s * 4, -3, 0), giro = Vector3.new(0, 0, s * 3), vida = 3 })
end

local function ala(lado: string)
	local m = copia("RotPunta" .. lado)
	if not m then
		return
	end
	local s = if lado == "Izq" then -1 else 1
	local corte = Vector3.new(s * Piezas.CORTE_ALA, 98.6, -23)
	sonar("ChapaRasgada", "GolpeMetal", corte, 1.3, 0.9)
	Rafagas.lanzar("Chispas", corte, 1.6)
	Rafagas.lanzar("Escombros", corte, 1)
	Camara.sacudir(0.45)
	temblar(m, Vector3.zAxis, corte, 0.45, 0.07 * s)
	Sonido.reproducir("BoomCartoon", corte, 0.9)
	Rafagas.lanzar("ExplosionPequena", corte, 1.2)
	Rafagas.lanzar("Humo", corte, 1.2)
	task.delay(0.9, maletazo)
	volar(m, { vel = Vector3.new(s * 9, 11, 0), giro = Vector3.new(4, 1, s * 7), humo = true, silbato = true })
end

local function deriva()
	local m = copia("RotDeriva")
	if not m then
		return
	end
	local corte = Vector3.new(0, Piezas.CORTE_DERIVA, 23)
	sonar("ChapaRasgada", "GolpeMetal", corte, 1.3, 0.8)
	Rafagas.lanzar("Chispas", corte, 1.8)
	Camara.sacudir(0.5)
	temblar(m, Vector3.zAxis, corte, 0.5, 0.12)
	Sonido.reproducir("BoomCartoon", corte, 1)
	Rafagas.lanzar("ExplosionPequena", corte, 1.4)
	Rafagas.lanzar("Escombros", corte, 1.3)
	task.delay(1.1, maletazo)
	volar(m, { vel = Vector3.new(rng:NextNumber(-6, 6), 15, 0), giro = Vector3.new(1.5, 3, rng:NextNumber(-6, 6)), humo = true, silbato = true })
end

local function capo(lado: string)
	local s = if lado == "Izq" then -1 else 1
	local base = CFrame.new(s * 18, 96, -24.5)
	local m = copia("RotCapo", base)
	if not m then
		return
	end
	local bisagra = base.Position + Vector3.new(-s * 1.95, 1.22, 0)
	local inicio = m:GetPivot()
	sonar("ChapaRasgada", "GolpeMetal", bisagra, 1.1, 1.15)
	animar(2.2, function(t)
		local a = math.rad(25 + 40 * t / 2.2) + math.rad(22) * math.sin(t * 17)
		m:PivotTo(CFrame.new(bisagra) * CFrame.Angles(0, 0, s * a) * CFrame.new(-bisagra) * inicio)
	end)
	Sonido.reproducir("Pop", bisagra, 1.2)
	Rafagas.lanzar("Chispas", bisagra, 1.2)
	Rafagas.lanzar("Plumas", base.Position + Vector3.new(0, 2, 0), 1.4)
	task.spawn(volar, m, { vel = Vector3.new(s * 7, 14, 0), giro = Vector3.new(2, 5, s * 6), vida = 4 })
	local pollo = copia("RotPolloGoma", CFrame.new(base.Position + Vector3.new(0, 2.5, -1)), 0.6)
	if pollo then
		local parte = pollo:FindFirstChildWhichIsA("BasePart", true)
		sonar("PolloGoma", "Bocina", parte or base.Position, 1)
		volar(pollo, { vel = Vector3.new(s * 2, 18, -3), giro = Vector3.new(9, 4, 6), vida = 4 })
	end
end

local function techo()
	local z = Piezas.FILA_TECHO
	local centro = Vector3.new(0, 112.5, z)
	Sonido.reproducir("Explosion", centro, 1)
	sonar("ChapaRasgada", "GolpeMetal", centro, 1.2, 0.85)
	task.delay(0.2, Sonido.reproducir, "Succion", centro, 1.2)
	Rafagas.lanzar("Escombros", centro, 1.6)
	Rafagas.lanzar("Onda", centro, 1.2)
	Rafagas.lanzar("Polvo", centro - Vector3.new(0, 5, 0), 1.6)
	Camara.sacudir(0.7)
	Camara.impulsoFov(8)
	local tapa = copia("RotTapaTecho")
	if tapa then
		task.spawn(function()
			temblar(tapa, Vector3.xAxis, centro, 0.3, 0.05)
			volar(tapa, { vel = Vector3.new(rng:NextNumber(-3, 3), 24, -2), giro = Vector3.new(5, 1, 2), vida = 5 })
		end)
	end
	for i, nombre in { "Maleta1", "Bolso", "Maleta2", "RotPolloGoma", "Maleta3", "Inodoro" } do
		task.delay(0.25 + i * 0.2, function()
			local marco = CFrame.new(rng:NextNumber(-3, 3), 107, z + rng:NextNumber(-1.2, 1.2)) * CFrame.Angles(rng:NextNumber(0, 6), rng:NextNumber(0, 6), 0)
			local m = copia(nombre, marco, if nombre == "RotPolloGoma" then 0.6 else nil)
			if not m then
				return
			end
			if nombre == "RotPolloGoma" then
				sonar("PolloGoma", "Bocina", marco.Position, 1)
			end
			volar(m, { vel = Vector3.new(rng:NextNumber(-7, 7), rng:NextNumber(20, 28), rng:NextNumber(-2, 2)), giro = Vector3.new(rng:NextNumber(-6, 6), rng:NextNumber(-6, 6), rng:NextNumber(-6, 6)), vida = 4 })
		end)
	end
end

local function esconder(p: BasePart)
	p.LocalTransparencyModifier = 1
	table.insert(escondidas, p)
	for _, d in p:GetChildren() do
		if d:IsA("Light") and d.Enabled then
			d.Enabled = false
			table.insert(apagadas, d)
		elseif d:IsA("LayerCollector") and d.Enabled then
			d.Enabled = false
			table.insert(apagadas, d)
		elseif d:IsA("Decal") then
			d.LocalTransparencyModifier = 1
			table.insert(calcas, d)
		end
	end
end

local function limpiarPartido()
	for _, p in escondidas do
		p.LocalTransparencyModifier = 0
	end
	table.clear(escondidas)
	for p, d in recortadas do
		p.Size = d.tam
		p.CFrame = d.cf
	end
	table.clear(recortadas)
	for _, d in apagadas do
		if d:IsA("Light") then
			d.Enabled = true
		elseif d:IsA("LayerCollector") then
			d.Enabled = true
		end
	end
	table.clear(apagadas)
	for _, d in calcas do
		d.LocalTransparencyModifier = 0
	end
	table.clear(calcas)
end

local function clonar(p: BasePart): BasePart
	local c = p:Clone()
	for _, d in c:GetDescendants() do
		if d:IsA("BasePart") or d:IsA("Model") or d:IsA("Folder") or d:IsA("ProximityPrompt") or d:IsA("ClickDetector") or d:IsA("BaseScript") or d:IsA("JointInstance") or d:IsA("Constraint") then
			d:Destroy()
		end
	end
	for _, etiqueta in c:GetTags() do
		c:RemoveTag(etiqueta)
	end
	c.Anchored = true
	c.CanCollide = false
	c.CanQuery = false
	c.CanTouch = false
	c.Parent = efectos
	return c
end

local function detras(d: BasePart, carpeta: Instance?): boolean
	if carpeta and d:IsDescendantOf(carpeta) then
		local raiz: Instance = d
		while raiz.Parent and raiz.Parent ~= carpeta do
			raiz = raiz.Parent
		end
		if raiz:IsA("Model") then
			return raiz:GetAttribute("Detras") == true
		end
	end
	return d.Position.Z > CORTE
end

local function trozoTrasero(): ({ BasePart }, { CFrame })
	local carpeta = avion:FindFirstChild("Roturas")
	if carpeta then
		carpeta:WaitForChild("Cola", 1)
	end
	local partes: { BasePart } = {}
	local marcos: { CFrame } = {}
	for _, hijo in avion:GetChildren() do
		if EXCLUIDAS[hijo.Name] then
			continue
		end
		for _, d in hijo:GetDescendants() do
			if not d:IsA("BasePart") or not d.Anchored or d.Transparency >= 1 or d.LocalTransparencyModifier >= 1 then
				continue
			end
			local cf, s = d.CFrame, d.Size / 2
			local recto = math.abs(cf.LookVector.Z) > 0.999 and math.abs(cf.UpVector.Y) > 0.999
			local z0, z1 = cf.Position.Z - s.Z, cf.Position.Z + s.Z
			if d.ClassName == "Part" and recto and z0 < CORTE and z1 > CORTE then
				recortadas[d] = { tam = d.Size, cf = cf }
				local c = clonar(d)
				c.Size = Vector3.new(d.Size.X, d.Size.Y, z1 - CORTE)
				c.CFrame = CFrame.new(cf.Position.X, cf.Position.Y, (z1 + CORTE) / 2)
				d.Size = Vector3.new(d.Size.X, d.Size.Y, CORTE - z0)
				d.CFrame = CFrame.new(cf.Position.X, cf.Position.Y, (z0 + CORTE) / 2)
				table.insert(partes, c)
				table.insert(marcos, c.CFrame)
			elseif detras(d, carpeta) then
				local c = clonar(d)
				esconder(d)
				table.insert(partes, c)
				table.insert(marcos, c.CFrame)
			end
		end
	end
	return partes, marcos
end

local function drama(): ColorCorrectionEffect
	local cc = Instance.new("ColorCorrectionEffect")
	cc.Name = "RoturaDrama"
	cc.Saturation = -0.55
	cc.Contrast = 0.25
	cc.TintColor = Color3.fromRGB(255, 236, 214)
	cc.Parent = Lighting
	return cc
end

local function escombrosPartido()
	local hombro = Vector3.new(1.5, 100 + Piezas.HOMBRO, CORTE + 0.5)
	local asiento = copia("RotAsientoSaludo", CFrame.new(1.5, 100, CORTE + 0.5))
	local brazos = copia("RotBrazosSaludo", CFrame.new(1.5, 100, CORTE + 0.5))
	if asiento and brazos then
		task.spawn(volar, asiento, { vel = Vector3.new(3, 8, 1.5), giro = Vector3.new(0.3, 0.6, 0.4), vida = 4.2 }, {
			{
				modelo = brazos,
				mov = function(t: number): CFrame
					return CFrame.new(hombro) * CFrame.Angles(0, 0, math.sin(t * 22) * 0.4) * CFrame.new(-hombro)
				end,
			},
		})
	end
	local lista = {
		{ n = "Inodoro", p = Vector3.new(-3, 101, CORTE + 1.5), v = Vector3.new(-7, 9, 1) },
		{ n = "RotPolloGoma", p = Vector3.new(0, 105, CORTE), v = Vector3.new(1, 15, -1) },
		{ n = "Maleta1", p = Vector3.new(3.5, 102, CORTE + 2), v = Vector3.new(8, 6, 1) },
		{ n = "Maleta2", p = Vector3.new(-1, 108, CORTE + 1), v = Vector3.new(-3, 12, 0) },
		{ n = "Bolso", p = Vector3.new(-4.5, 106, CORTE + 1), v = Vector3.new(-9, 7, 0) },
	}
	for _, e in lista do
		local m = copia(e.n, CFrame.new(e.p) * CFrame.Angles(rng:NextNumber(0, 6), rng:NextNumber(0, 6), 0), if e.n == "RotPolloGoma" then 0.6 else nil)
		if m then
			task.spawn(volar, m, { vel = e.v, giro = Vector3.new(rng:NextNumber(-4, 4), rng:NextNumber(-4, 4), rng:NextNumber(-4, 4)), vida = 4.2 })
		end
	end
	sonar("PolloGoma", "Bocina", Vector3.new(0, 105, CORTE), 1)
end

local function partido()
	local mia = generacion
	local partes, marcos = trozoTrasero()
	local grieta = Vector3.new(0, 105, CORTE)
	Sonido.reproducir("BoomCartoon", grieta, 1.2)
	sonar("ChapaRasgada", "GolpeMetal", grieta, 1.4, 0.75)
	for i = 0, 5 do
		local a = math.pi * 2 * i / 6
		Rafagas.lanzar("Chispas", grieta + Vector3.new(math.cos(a) * 8, math.sin(a) * 8, 0), 1.4)
	end
	Rafagas.lanzar("Escombros", grieta, 1.8)
	Camara.sacudir(1)
	Camara.impulsoFov(12)
	local cc: ColorCorrectionEffect? = nil
	task.delay(0.35, function()
		if mia ~= generacion then
			return
		end
		ritmo = 0.15
		cc = drama()
		Sonido.reproducir("RascarDisco", nil, 1, 1)
		Sonido.reproducir("Dramatico", nil, 1, 1)
		escombrosPartido()
	end)
	task.delay(2.25, function()
		if mia ~= generacion then
			return
		end
		Sonido.reproducir("SilbatoCaida", grieta + Vector3.new(0, 0, 20), 1.2, 1)
		Rafagas.lanzar("Explosion", grieta, 2)
		Rafagas.lanzar("Humo", grieta, 2.2)
		Camara.sacudir(0.8)
		local valor = Instance.new("NumberValue")
		valor.Value = ritmo
		valor.Changed:Connect(function(v)
			if mia == generacion then
				ritmo = v
			end
		end)
		TweenService:Create(valor, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Value = 1 }):Play()
		local efecto = cc
		if efecto then
			TweenService:Create(efecto, TweenInfo.new(1.5), { Saturation = 0, Contrast = 0 }):Play()
		end
	end)
	local vw = velocidadMundo()
	local lado = if rng:NextNumber() < 0.5 then -1 else 1
	local real, tau = 0, 0
	local cfs = table.create(#marcos)
	while real < DURACION_PARTIDO and mia == generacion do
		local dt = RunService.PreRender:Wait()
		real += dt
		local mov: CFrame
		if real < 0.35 then
			mov = CFrame.Angles(rng:NextNumber(-1, 1) * 0.004, 0, rng:NextNumber(-1, 1) * 0.004)
		else
			tau += dt * ritmo
			local atras = 0.8 * tau + vw * (tau - (1 - math.exp(-0.9 * tau)) / 0.9)
			local giro = CFrame.Angles(0.35 * tau + 0.15 * tau * tau, 0, lado * 0.08 * tau)
			mov = CFrame.new(0, -11 * tau * tau, atras) * CFrame.new(PIVOTE) * giro * CFrame.new(-PIVOTE)
		end
		for i, cf in marcos do
			cfs[i] = mov * cf
		end
		Workspace:BulkMoveTo(partes, cfs, Enum.BulkMoveMode.FireCFrameChanged)
	end
	for _, p in partes do
		p:Destroy()
	end
	if mia == generacion then
		limpiarPartido()
		ritmo = 1
	end
	local efecto = cc
	if efecto then
		efecto:Destroy()
	end
end

local function restaurar()
	generacion += 1
	ritmo = 1
	efectos:ClearAllChildren()
	limpiarPartido()
	local cc = Lighting:FindFirstChild("RoturaDrama")
	if cc then
		cc:Destroy()
	end
end

local ACCIONES: { [string]: (string) -> () } = {
	Ala = ala,
	Capo = capo,
	Deriva = function()
		deriva()
	end,
	Techo = function()
		techo()
	end,
	Partido = function()
		partido()
	end,
	Restaurar = function()
		restaurar()
	end,
}

function Roturas.iniciar()
	efectos.Parent = Workspace
	local remoto = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Rotura") :: RemoteEvent
	remoto.OnClientEvent:Connect(function(tipo, lado)
		local f = if typeof(tipo) == "string" then ACCIONES[tipo] else nil
		if f then
			task.spawn(f, if typeof(lado) == "string" then lado else "Izq")
		end
	end)
end

return Roturas
