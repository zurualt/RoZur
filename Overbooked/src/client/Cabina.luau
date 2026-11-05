--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")
local Workspace = game:GetService("Workspace")

local Audio = require(ReplicatedStorage.Shared.Audio)
local Config = require(ReplicatedStorage.Shared.Config)
local VFX = require(ReplicatedStorage.Shared.VFX)

type Luz = { luz: Light, brillo: number, color: Color3 }
type Neon = { parte: BasePart, color: Color3 }
type Movil = { pivote: CFrame, partes: { BasePart }, relativos: { CFrame }, cframes: { CFrame }, clave: number }
type Baliza = { luz: BasePart, color: Color3, haces: { SpotLight }, cartel: BillboardGui, destello: ImageLabel }

local Cabina = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local luces: { Luz } = {}
local neones: { Neon } = {}
local rng = Random.new()
local ROJO = Color3.fromRGB(255, 72, 60)
local CALIDO = Color3.fromRGB(255, 178, 104)
local VOLUMEN_ALARMA = if Audio.DATOS.AlarmaCabina then Audio.DATOS.AlarmaCabina.volumen else 0.3
local Estado = ReplicatedStorage:WaitForChild("Estado")
local balizas: { Baliza } = {}
local alarma: Sound? = nil
local mezclaRojo = 0
local encendidas = false
local mezclaNoche = 0
local apagonHasta = 0
local ultimoFactor = -1
local ultimoRojo = -1
local ultimoCalido = -1

local function movil(raiz: BasePart, ancla: CFrame?): Movil
	local m: Movil = { pivote = raiz.CFrame * (ancla or CFrame.identity), partes = {}, relativos = {}, cframes = {}, clave = math.huge }
	local function recoger()
		table.clear(m.partes)
		table.clear(m.relativos)
		for _, d in raiz:GetDescendants() do
			if d:IsA("BasePart") and d.Anchored then
				table.insert(m.partes, d)
				table.insert(m.relativos, m.pivote:ToObjectSpace(d.CFrame))
			end
		end
		table.insert(m.partes, raiz)
		table.insert(m.relativos, m.pivote:ToObjectSpace(raiz.CFrame))
	end
	recoger()
	raiz.DescendantAdded:Connect(function()
		task.defer(function()
			for i, p in m.partes do
				p.CFrame = m.pivote * m.relativos[i]
			end
			recoger()
			m.clave = math.huge
		end)
	end)
	return m
end

local function mover(m: Movil, clave: number, desplazamiento: CFrame)
	if math.abs(clave - m.clave) < 1e-3 then
		return
	end
	m.clave = clave
	local cframes = m.cframes
	table.clear(cframes)
	local base = m.pivote * desplazamiento
	for i, r in m.relativos do
		cframes[i] = base * r
	end
	Workspace:BulkMoveTo(m.partes, cframes, Enum.BulkMoveMode.FireCFrameChanged)
end

local function numero(nombre: string): number
	local v = avion:GetAttribute(nombre)
	return if typeof(v) == "number" then v else 0
end

local function prepararLuces()
	local estructura = avion:WaitForChild("Estructura")
	for _, d in estructura:GetDescendants() do
		if d.Name == "BalizaLuz" then
			continue
		elseif d:IsA("Light") then
			table.insert(luces, { luz = d, brillo = d.Brightness, color = d.Color })
		elseif d:IsA("BasePart") and d.Material == Enum.Material.Neon then
			table.insert(neones, { parte = d, color = d.Color })
		end
	end
end

local function prepararBalizas()
	local efectos = SoundService:FindFirstChild("Efectos")
	local central: BasePart? = nil
	for _, d in avion:WaitForChild("Estructura"):GetChildren() do
		if not d:IsA("BasePart") or d.Name ~= "BalizaLuz" then
			continue
		end
		local b: Baliza = { luz = d, color = d.Color, haces = {}, cartel = Instance.new("BillboardGui"), destello = Instance.new("ImageLabel") }
		for _, giro in { 0, math.pi } do
			local a = Instance.new("Attachment")
			a.CFrame = CFrame.Angles(0, giro, 0) * CFrame.Angles(math.rad(-22), 0, 0)
			a.Parent = d
			local haz = Instance.new("SpotLight")
			haz.Face = Enum.NormalId.Front
			haz.Angle = 55
			haz.Range = 22
			haz.Brightness = 0
			haz.Color = ROJO
			haz.Shadows = false
			haz.Enabled = false
			haz.Parent = a
			table.insert(b.haces, haz)
		end
		local cartel = b.cartel
		cartel.Name = "Destello"
		cartel.Size = UDim2.fromScale(2.6, 2.6)
		cartel.LightInfluence = 0
		cartel.Enabled = false
		cartel.Adornee = d
		cartel.Parent = d
		b.destello.BackgroundTransparency = 1
		b.destello.Size = UDim2.fromScale(1, 1)
		b.destello.Image = VFX.textura("Destello")
		b.destello.ImageColor3 = ROJO
		b.destello.Parent = cartel
		table.insert(balizas, b)
		if not central or math.abs(d.Position.Z + 26) < math.abs(central.Position.Z + 26) then
			central = d
		end
	end
	local id = Audio.IDS.AlarmaCabina
	if central and id then
		local s = Instance.new("Sound")
		s.Name = "AlarmaCabina"
		s.SoundId = `rbxassetid://{id}`
		s.Looped = true
		s.Volume = 0
		s.RollOffMode = Enum.RollOffMode.InverseTapered
		s.RollOffMinDistance = 30
		s.RollOffMaxDistance = 90
		if efectos and efectos:IsA("SoundGroup") then
			s.SoundGroup = efectos
		end
		s.Parent = central
		alarma = s
	end
end

local function prueba(nombre: string): boolean
	return RunService:IsStudio() and Workspace:GetAttribute(nombre) == true
end

local function balizasEn(t: number, mezcla: number)
	local encendida = mezcla > 0.01
	if not encendida and not encendidas then
		return
	end
	encendidas = encendida
	local camara = Workspace.CurrentCamera.CFrame.Position
	for _, b in balizas do
		for _, haz in b.haces do
			haz.Enabled = encendida
			haz.Brightness = 7 * mezcla
		end
		b.cartel.Enabled = encendida
		b.luz.Material = if encendida then Enum.Material.Neon else Enum.Material.Glass
		b.luz.Color = b.color:Lerp(ROJO, mezcla)
		if encendida then
			b.luz.CFrame = CFrame.new(b.luz.Position) * CFrame.Angles(0, t * 5.5, 0)
			local hacia = (camara - b.luz.Position) * Vector3.new(1, 0, 1)
			local frente = b.luz.CFrame.LookVector * Vector3.new(1, 0, 1)
			local cara = if hacia.Magnitude > 0.1 then math.abs(hacia.Unit:Dot(frente.Unit)) else 0
			b.destello.ImageTransparency = 1 - mezcla * (0.25 + 0.75 * cara ^ 6)
		end
	end
	local s = alarma
	if s then
		s.Volume = mezcla * VOLUMEN_ALARMA
		if encendida and not s.Playing then
			s:Play()
		elseif not encendida then
			s:Stop()
		end
	end
end

local function luzCabina(t: number, dt: number)
	local ahora = Workspace:GetServerTimeNow()
	local factor = 1
	if numero("Parpadeo") > ahora then
		factor = if math.noise(t * 11, 0.3) > 0.05 then 0.08 else 1
	elseif avion:GetAttribute("Tormenta") == true then
		if os.clock() < apagonHasta then
			factor = 0.1
		elseif rng:NextNumber() < 0.004 then
			apagonHasta = os.clock() + rng:NextNumber(0.08, 0.3)
		end
	end
	local enVuelo = Estado:GetAttribute("Fase") == "Vuelo"
	local emergencia = avion:GetAttribute("Emergencia") == true and (enVuelo or prueba("PruebaEmergencia"))
	local nocturno = (enVuelo and Estado:GetAttribute("Condicion") == "Nocturno") or prueba("PruebaNoche")
	local k = math.min(1, dt * 2)
	mezclaRojo += ((if emergencia then 1 else 0) - mezclaRojo) * k
	mezclaNoche += ((if nocturno then 1 else 0) - mezclaNoche) * math.min(1, dt * 0.8)
	balizasEn(t, if mezclaRojo > 0.01 then mezclaRojo else 0)
	local rojo = if avion:GetAttribute("Emergencia") == true then math.max(mezclaRojo, 0.45 + 0.3 * math.sin(t * 4)) else mezclaRojo
	if rojo > 0.01 then
		factor *= 1 - 0.4 * rojo + 0.12 * rojo * math.sin(t * 11)
	end
	factor *= 1 - 0.42 * mezclaNoche
	local calido = mezclaNoche * 0.65
	factor = math.floor(factor * 20 + 0.5) / 20
	rojo = math.floor(rojo * 20 + 0.5) / 20
	calido = math.floor(calido * 20 + 0.5) / 20
	if factor == ultimoFactor and rojo == ultimoRojo and calido == ultimoCalido then
		return
	end
	ultimoFactor, ultimoRojo, ultimoCalido = factor, rojo, calido
	for _, l in luces do
		l.luz.Brightness = l.brillo * factor
		l.luz.Color = l.color:Lerp(CALIDO, calido):Lerp(ROJO, rojo)
	end
	for _, n in neones do
		n.parte.Color = n.color:Lerp(CALIDO, calido):Lerp(Color3.new(0.1, 0.1, 0.1), 1 - factor):Lerp(ROJO, rojo * 0.8)
	end
end

function Cabina.iniciar()
	prepararLuces()
	prepararBalizas()
	local cabina = avion:WaitForChild("Cabina")
	local exterior = avion:WaitForChild("Exterior")
	local columna = cabina:WaitForChild("Columna") :: BasePart
	local palancas: { Movil } = {}
	for _, d in cabina:GetChildren() do
		if d:IsA("BasePart") and d.Name == "Palanca" then
			table.insert(palancas, movil(d, CFrame.new(0, -d.Size.Y / 2, 0)))
		end
	end
	local yugo = movil(columna)
	local canones = exterior:WaitForChild("Canones", 10)
	local torreta = exterior:WaitForChild("Torreta", 10)
	local giro = if canones and canones:IsA("BasePart") then movil(canones) else nil
	local giroAsiento = if canones and canones:IsA("BasePart") and torreta and torreta:IsA("BasePart") then movil(torreta, torreta.CFrame:Inverse() * CFrame.new(canones.Position)) else nil
	local cab, ala, gas, mira = 0, 0, 0, 0
	local V = Config.VUELO
	local paneles: { Instance } = CollectionService:GetTagged("PanelSuelto")
	CollectionService:GetInstanceAddedSignal("PanelSuelto"):Connect(function()
		paneles = CollectionService:GetTagged("PanelSuelto")
	end)
	CollectionService:GetInstanceRemovedSignal("PanelSuelto"):Connect(function()
		paneles = CollectionService:GetTagged("PanelSuelto")
	end)
	RunService.RenderStepped:Connect(function(dt: number)
		local t = os.clock()
		luzCabina(t, dt)
		for _, panel in paneles do
			local b = panel:GetAttribute("Bisagra")
			if panel:IsA("BasePart") and typeof(b) == "CFrame" then
				panel.CFrame = b * CFrame.Angles(math.rad(19 + 19 * math.sin(t * 26)), 0, 0) * CFrame.new(0, 0, 1.1)
			end
		end
		local camara = Workspace.CurrentCamera
		local cerca = (camara.CFrame.Position - columna.Position).Magnitude < 70
		local k = math.min(1, dt * 8)
		if cerca then
			cab += (numero("Cabeceo") / V.CABECEO_MAX - cab) * k
			ala += (numero("Alabeo") / V.ALABEO_MAX - ala) * k
			gas += (numero("Gases") / 100 - gas) * k
			mover(yugo, cab * 7 + ala * 13, CFrame.new(0, 0, -cab * 0.35) * CFrame.Angles(0, 0, -ala * 1.1))
			for _, p in palancas do
				mover(p, gas, CFrame.Angles(-(gas - 0.5) * 1.1, 0, 0))
			end
		end
		if giro and torreta and torreta:IsA("Seat") and (camara.CFrame.Position - torreta.Position).Magnitude < 160 then
			local ocupante = torreta.Occupant
			local objetivo = mira
			local remota = torreta:GetAttribute("Mira")
			if typeof(remota) == "number" then
				objetivo = remota
			end
			if ocupante and ocupante.Parent == jugador.Character then
				local plano = camara.CFrame.LookVector * Vector3.new(1, 0, 1)
				if plano.Magnitude > 0.05 then
					objetivo = math.atan2(-plano.X, -plano.Z)
				end
			end
			local delta = (objetivo - mira + math.pi) % (2 * math.pi) - math.pi
			mira += delta * math.min(1, dt * 10)
			mover(giro, mira, CFrame.Angles(0, mira, 0))
			if giroAsiento then
				mover(giroAsiento, mira, CFrame.Angles(0, mira, 0))
			end
		end
	end)
end

return Cabina
