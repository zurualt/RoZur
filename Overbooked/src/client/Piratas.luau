--!strict
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Criaturas = require(ReplicatedStorage.Shared.Criaturas)
local Gui = require(ReplicatedStorage.Shared.Gui)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Camara = require(script.Parent.Camara)
local Rafagas = require(script.Parent.Rafagas)
local Sonido = require(script.Parent.Sonido)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoDisparar = Remotos:WaitForChild("Disparar") :: RemoteEvent

type Visual = {
	carpeta: Instance?,
	modelo: Model,
	datos: Criaturas.Avion?,
	partes: { BasePart },
	marcos: { CFrame },
	grupos: { number },
	destino: { CFrame },
	cfs: { CFrame },
	emisores: { ParticleEmitter },
	cf: CFrame,
	pos: Vector3,
	vel: Vector3,
	alabeo: number,
	giro: number,
	vuelta: number,
	fase: number,
	vida: number,
	golpe: number,
	enfado: number,
	cayendo: number?,
	huyendo: number?,
	piloto: Vector3?,
	velPiloto: Vector3,
}

local Piratas = {}

local CENTRO = Vector3.new(0, 105, -18)
local ESCALA = 1.3
local TINTA = Color3.fromRGB(27, 27, 33)
local AMARILLO = Color3.fromRGB(255, 214, 70)
local ROJO = Color3.fromRGB(232, 67, 58)
local BALA = Color3.fromRGB(255, 120, 60)
local PUMS = { "¡PUM!", "¡CATAPLÁN!", "¡KABUM!" }
local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local visuales: { [Visual]: boolean } = {}
local rng = Random.new()
local enTorreta = false
local disparando = false
local ultimo = 0

local function posicion(f: Instance, t: number): Vector3
	local radio = f:GetAttribute("Radio")
	local velocidad = f:GetAttribute("Velocidad")
	local fase = f:GetAttribute("Fase")
	local altura = f:GetAttribute("Altura")
	local inicio = f:GetAttribute("Inicio")
	if typeof(radio) ~= "number" or typeof(velocidad) ~= "number" or typeof(fase) ~= "number" or typeof(altura) ~= "number" or typeof(inicio) ~= "number" then
		return CENTRO
	end
	local a = fase + velocidad * (t - inicio)
	return CENTRO + Vector3.new(math.cos(a) * radio, altura + math.sin(a * 2.3) * 8, math.sin(a) * radio * 0.7)
end

local function suelta(tamano: Vector3, color: Color3, forma: Enum.PartType?): Part
	local p = Instance.new("Part")
	p.Size = tamano
	p.Color = color
	p.Material = Enum.Material.SmoothPlastic
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	if forma then
		p.Shape = forma
	end
	return p
end

local function meter(v: Visual, parte: BasePart, marco: CFrame, grupo: number)
	parte.Parent = v.modelo
	table.insert(v.partes, parte)
	table.insert(v.marcos, marco)
	table.insert(v.grupos, grupo)
	table.insert(v.destino, marco)
	v.cfs[grupo] = CFrame.identity
end

local function anadir(v: Visual, nombre: string, grupo: number, escala: number)
	local modelo, partes, marcos = Criaturas.clonar(nombre, escala)
	if not modelo then
		return
	end
	for i, p in partes do
		meter(v, p, marcos[i], grupo)
	end
	modelo:Destroy()
end

local function trazador(origen: Vector3, destino: Vector3, color: Color3, grosor: number)
	local largo = (destino - origen).Magnitude
	local p = suelta(Vector3.new(grosor, grosor, largo), color)
	p.Material = Enum.Material.Neon
	p.CFrame = CFrame.lookAt(origen, destino) * CFrame.new(0, 0, -largo / 2)
	p.Parent = Workspace
	task.delay(0.07, function()
		p:Destroy()
	end)
end

local function rotulo(pos: Vector3)
	local ancla = Instance.new("Attachment")
	ancla.WorldPosition = pos
	ancla.Parent = Workspace.Terrain
	Rafagas.pop(ancla, Vector3.new(0, 4, 0), { texto = PUMS[rng:NextInteger(1, #PUMS)], color = AMARILLO, fondo = ROJO, tam = 14, vida = 1.5, subir = 8 })
	local gui = ancla:FindFirstChildWhichIsA("BillboardGui")
	if gui then
		gui.MaxDistance = 700
	end
	task.delay(1.7, ancla.Destroy, ancla)
end

local function caer(v: Visual)
	if v.cayendo then
		return
	end
	v.cayendo = os.clock()
	v.vel = v.vel * 0.6 + Vector3.new(0, 10, 0)
	local d = v.datos
	v.piloto = if d then v.cf * (d.asiento * ESCALA) else nil
	v.velPiloto = v.vel * 0.3 + Vector3.new(rng:NextNumber(-10, 10), 42, rng:NextNumber(-10, 10))
	for _, e in v.emisores do
		e.Enabled = true
	end
	Sonido.reproducir("PirataCae", v.pos, 1.2)
	Sonido.reproducir("SilbatoCaida", v.partes[1], 1)
end

local function herido(v: Visual, vida: number)
	local antes = v.vida
	v.vida = vida
	if vida < antes then
		v.golpe = os.clock()
		v.enfado = os.clock()
		Rafagas.lanzar("Chispas", v.pos, 1)
		if rng:NextNumber() < 0.12 then
			Rafagas.lanzar("Martillazo", v.pos + Vector3.new(0, 3, 0), 1.6)
		end
		Sonido.reproducir("GolpeMetal", v.pos, 0.6)
	end
	local humo, llama = v.emisores[2], v.emisores[1]
	if humo and llama then
		humo.Enabled = vida <= 60
		llama.Enabled = vida <= 30
	end
	if vida <= 0 then
		caer(v)
	end
end

local function disparar(v: Visual)
	local d = v.datos
	if v.cayendo or not d then
		return
	end
	v.enfado = os.clock()
	for _, c in d.canones do
		local boca = v.cf * (c * ESCALA)
		local destino = CENTRO + Vector3.new(rng:NextNumber(-6, 6), rng:NextNumber(-4, 4), rng:NextNumber(-30, 25))
		trazador(boca, destino, BALA, 0.35)
		Rafagas.lanzar("Chispas", boca, 0.7)
	end
	Sonido.reproducir("Disparo", v.pos, 0.8, 0.75)
end

local function actualizar(v: Visual, dt: number, ahora: number, t: number, camara: Vector3): boolean
	local f = v.carpeta
	local nueva = v.pos
	local cayendo, huyendo = v.cayendo, v.huyendo
	if cayendo then
		v.vel += Vector3.new(0, -60, 0) * dt
		nueva = v.pos + v.vel * dt
		v.vuelta += dt * (7 + (ahora - cayendo) * 5)
		if ahora - cayendo > 2.6 then
			Rafagas.lanzar("Explosion", nueva, 1.6)
			if (camara - nueva).Magnitude > 120 then
				rotulo(nueva)
			end
			Sonido.reproducir("BoomCartoon", nueva, 0.7)
			return false
		end
	elseif huyendo then
		v.vel = v.vel * (1 + dt * 0.9) + Vector3.new(0, 18 * dt, 0)
		nueva = v.pos + v.vel * dt
		if ahora - huyendo > 4 then
			return false
		end
	elseif f then
		nueva = posicion(f, t)
		local vel = (nueva - v.pos) / math.max(dt, 1e-3)
		if vel.Magnitude > 1 then
			local antes = v.vel * Vector3.new(1, 0, 1)
			local ahoraH = vel * Vector3.new(1, 0, 1)
			if antes.Magnitude > 1 and ahoraH.Magnitude > 1 then
				local giro = antes.Unit:Cross(ahoraH.Unit).Y / math.max(dt, 1e-3)
				v.alabeo += (math.clamp(giro * 1.8, -0.9, 0.9) - v.alabeo) * math.min(1, dt * 3)
			end
			v.vel = vel
		end
	end
	v.pos = nueva
	local fase = v.fase
	local golpe = math.max(0, 1 - (ahora - v.golpe) / 0.5)
	local frente = if v.vel.Magnitude > 0.5 then v.vel else v.cf.LookVector
	local cf = CFrame.lookAt(nueva, nueva + frente)
		* CFrame.new(0, math.sin(t * 1.7 + fase) * 0.8, 0)
		* CFrame.Angles(
			math.sin(t * 3.3 + fase) * 0.05 + math.sin(ahora * 45) * 0.12 * golpe,
			math.sin(t * 2.1 + fase) * 0.06 + math.sin(ahora * 38) * 0.1 * golpe,
			v.alabeo + v.vuelta + math.sin(t * 4.4 + fase) * 0.07 + math.sin(ahora * 52) * 0.2 * golpe
		)
	v.cf = cf
	v.cfs[1] = cf
	local d = v.datos
	if d then
		local h = #d.helices
		local velHelice = if cayendo then math.max(0, 26 - (ahora - cayendo) * 14) elseif v.vida <= 35 then 15 + math.sin(t * 7 + fase) * 9 else 26
		v.giro += velHelice * dt
		for k, helice in d.helices do
			v.cfs[1 + k] = cf * CFrame.new(helice.pos * ESCALA) * CFrame.Angles(0, 0, v.giro + k * 0.7)
		end
		local piloto: CFrame
		local agitar: number
		local expulsado = v.piloto
		if cayendo and expulsado then
			local c = ahora - cayendo
			v.velPiloto += Vector3.new(0, -50, 0) * dt
			expulsado += v.velPiloto * dt
			v.piloto = expulsado
			piloto = CFrame.new(expulsado) * CFrame.Angles(c * 6, c * 3, c * 8)
			agitar = 1
		else
			local objetivo = cf:PointToObjectSpace(CENTRO)
			local mirar = math.clamp(math.atan2(-objetivo.X, -objetivo.Z), -1.2, 1.2) * 0.6
			local enfado = math.clamp(1 - (ahora - v.enfado) / 1.6, 0, 1)
			agitar = math.max(enfado, math.max(0, math.sin(t * 0.8 + fase)) ^ 6)
			piloto = cf * CFrame.new(d.asiento * ESCALA + Vector3.new(0, math.abs(math.sin(ahora * 9)) * 0.25 * agitar, 0)) * CFrame.Angles(0, mirar, -v.alabeo * 0.3)
		end
		local hombro = Criaturas.HOMBRO * ESCALA
		local brazo = math.sin(ahora * 17 + fase) * 0.5 * agitar
		v.cfs[2 + h] = piloto
		v.cfs[3 + h] = piloto * CFrame.new(hombro) * CFrame.Angles(brazo * 0.5, 0, brazo - 0.2 * agitar) * CFrame.new(-hombro)
		local mareo = v.vida <= 35 or cayendo ~= nil
		for j, o in d.ojos do
			local centro = cf * (o.centro * ESCALA)
			local dir = (camara - centro).Unit + cf.LookVector * 0.7 + cf.UpVector * 0.5
			if mareo then
				dir += (cf.RightVector * math.cos(ahora * 10 + j) + cf.UpVector * math.sin(ahora * 10 + j)) * 1.2
			else
				dir += cf.RightVector * math.sin(ahora * 23 + fase) * 0.25 * golpe
			end
			v.cfs[3 + h + j] = CFrame.new(centro + dir.Unit * o.radio * ESCALA * 0.86)
		end
	end
	for i, p in v.marcos do
		v.destino[i] = v.cfs[v.grupos[i]] * p
	end
	Workspace:BulkMoveTo(v.partes, v.destino, Enum.BulkMoveMode.FireCFrameChanged)
	return true
end

local function crear(f: Instance)
	local n = tonumber(string.match(f.Name, "%d+")) or 1
	local nombre = Criaturas.VARIANTES[(n - 1) % #Criaturas.VARIANTES + 1]
	local datos = Criaturas.AVIONES[nombre]
	local modelo = Instance.new("Model")
	modelo.Name = "AvionPirata"
	local pos = posicion(f, Workspace:GetServerTimeNow())
	local vida = f:GetAttribute("Vida")
	local v: Visual = {
		carpeta = f,
		modelo = modelo,
		datos = nil,
		partes = {},
		marcos = {},
		grupos = {},
		destino = {},
		cfs = {},
		emisores = {},
		cf = CFrame.new(pos),
		pos = pos,
		vel = Vector3.zero,
		alabeo = 0,
		giro = 0,
		vuelta = 0,
		fase = rng:NextNumber(0, 6),
		vida = if typeof(vida) == "number" then vida else 100,
		golpe = 0,
		enfado = 0,
		cayendo = nil,
		huyendo = nil,
		piloto = nil,
		velPiloto = Vector3.zero,
	}
	anadir(v, nombre, 1, ESCALA)
	if #v.partes > 0 then
		v.datos = datos
		local h = #datos.helices
		for k, helice in datos.helices do
			anadir(v, "HelicePirata", 1 + k, ESCALA * helice.escala)
		end
		anadir(v, "PilotoPirata", 2 + h, ESCALA)
		anadir(v, "BrazoPirata", 3 + h, ESCALA)
		for j, o in datos.ojos do
			meter(v, suelta(Vector3.one * o.radio * ESCALA * 0.92, TINTA, Enum.PartType.Ball), CFrame.identity, 3 + h + j)
		end
		local adjunto = Instance.new("Attachment")
		adjunto.CFrame = v.marcos[1]:Inverse() * CFrame.new(datos.humo * ESCALA)
		adjunto.Parent = v.partes[1]
		v.emisores = VFX.fuego(adjunto, 1.6)
		for _, e in v.emisores do
			e.Enabled = false
		end
	else
		local gris = Color3.fromRGB(70, 74, 80)
		meter(v, suelta(Vector3.new(2.6, 2.6, 13), gris), CFrame.identity, 1)
		meter(v, suelta(Vector3.new(16, 0.5, 3.2), Color3.fromRGB(190, 40, 40)), CFrame.new(0, -0.3, -0.5), 1)
	end
	herido(v, v.vida)
	actualizar(v, 1 / 60, os.clock(), Workspace:GetServerTimeNow(), Workspace.CurrentCamera.CFrame.Position)
	modelo.Parent = Workspace
	visuales[v] = true
	f:GetAttributeChangedSignal("Vida"):Connect(function()
		local nueva = f:GetAttribute("Vida")
		if typeof(nueva) == "number" then
			herido(v, nueva)
		end
	end)
	f:GetAttributeChangedSignal("Disparo"):Connect(function()
		disparar(v)
	end)
	f.Destroying:Connect(function()
		v.carpeta = nil
		if not v.cayendo then
			v.huyendo = os.clock()
		end
	end)
end

local function cambiar(nuevo: boolean)
	if nuevo == enTorreta then
		return
	end
	enTorreta = nuevo
	if enTorreta then
		ContextActionService:BindAction("Disparar", function(_, estado)
			disparando = estado == Enum.UserInputState.Begin or estado == Enum.UserInputState.Change
			return Enum.ContextActionResult.Sink
		end, true, Enum.UserInputType.MouseButton1, Enum.KeyCode.ButtonR2)
		ContextActionService:SetTitle("Disparar", "Fuego")
		ContextActionService:SetPosition("Disparar", Gui.posTactil(1, 0))
	else
		ContextActionService:UnbindAction("Disparar")
		disparando = false
	end
end

function Piratas.iniciar()
	local carpeta = avion:WaitForChild("Piratas")
	for _, f in carpeta:GetChildren() do
		crear(f)
	end
	carpeta.ChildAdded:Connect(crear)
	local function alPersonaje(personaje: Model)
		cambiar(false)
		local humanoide = personaje:WaitForChild("Humanoid", 10)
		if humanoide and humanoide:IsA("Humanoid") then
			humanoide.Seated:Connect(function(sentado, asiento)
				if asiento then
					cambiar(sentado and asiento.Name == "Torreta")
				else
					cambiar(false)
				end
			end)
		end
	end
	if jugador.Character then
		task.spawn(alPersonaje, jugador.Character)
	end
	jugador.CharacterAdded:Connect(alPersonaje)
	RunService.PreRender:Connect(function(dt)
		local t = Workspace:GetServerTimeNow()
		local ahora = os.clock()
		local camara = Workspace.CurrentCamera
		local foco = camara.CFrame.Position
		for v in visuales do
			if not actualizar(v, dt, ahora, t, foco) then
				visuales[v] = nil
				v.modelo:Destroy()
			end
		end
		if enTorreta and disparando and ahora - ultimo > 0.12 then
			ultimo = ahora
			local dir = camara.CFrame.LookVector
			RemotoDisparar:FireServer(dir)
			Sonido.reproducir("Disparo", nil, 0.7)
			local origen = camara.CFrame.Position + dir * 3 - camara.CFrame.UpVector * 0.8
			trazador(origen, origen + dir * 260, Color3.fromRGB(255, 220, 120), 0.18)
			Camara.sacudir(0.12)
		end
	end)
end

return Piratas
