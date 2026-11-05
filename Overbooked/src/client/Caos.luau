--!strict
local CollectionService = game:GetService("CollectionService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")
local Workspace = game:GetService("Workspace")

local Audio = require(ReplicatedStorage.Shared.Audio)
local Camara = require(script.Parent.Camara)
local Rafagas = require(script.Parent.Rafagas)

type Estilo = { color: Color3, fondo: Color3, nube: boolean }
type Temblor = { objetivo: PVInstance, base: CFrame }

local Caos = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local rng = Random.new()

local ESTILOS: { [string]: Estilo } = {
	Grito = { color = Color3.fromRGB(255, 214, 70), fondo = Color3.fromRGB(232, 67, 58), nube = false },
	Animal = { color = Color3.new(1, 1, 1), fondo = Color3.fromRGB(31, 166, 160), nube = true },
	Asco = { color = Color3.fromRGB(235, 255, 170), fondo = Color3.fromRGB(110, 160, 50), nube = true },
	Bebe = { color = Color3.new(1, 1, 1), fondo = Color3.fromRGB(120, 180, 240), nube = true },
	Bien = { color = Color3.fromRGB(255, 244, 224), fondo = Color3.fromRGB(109, 190, 69), nube = false },
	Borracho = { color = Color3.fromRGB(255, 214, 110), fondo = Color3.fromRGB(160, 124, 242), nube = true },
}
local LUCES_DISCO = { -45, -32, -19, -6 }

local temblores: { [BasePart]: Temblor } = {}
local discoCosas: { Instance } = {}
local luces: { PointLight } = {}
local bola: BasePart? = nil
local tinteDisco: ColorCorrectionEffect? = nil
local latido = 0
local tintePeste: ColorCorrectionEffect? = nil
local desenfoque: BlurEffect? = nil
local nivelPeste = 0
local dentroPeste = false
local arcada = 0

local function temblar(parte: BasePart, activo: boolean)
	local t = temblores[parte]
	if activo and not t then
		local modelo = parte:FindFirstChildWhichIsA("Model")
		local primaria = modelo and modelo.PrimaryPart
		local objetivo: PVInstance = if modelo and primaria and primaria.Anchored then modelo else parte
		temblores[parte] = { objetivo = objetivo, base = objetivo:GetPivot() }
	elseif not activo and t then
		temblores[parte] = nil
		t.objetivo:PivotTo(t.base)
	end
end

local function vigilarTemblor(nombre: string, atributo: string)
	local parte = avion:FindFirstChild(nombre, true)
	if not parte or not parte:IsA("BasePart") then
		return
	end
	parte:GetAttributeChangedSignal(atributo):Connect(function()
		temblar(parte, parte:GetAttribute(atributo) == true)
	end)
	if parte:GetAttribute(atributo) == true then
		temblar(parte, true)
	end
end

local function empezarDisco()
	local b = Instance.new("Part")
	b.Name = "BolaDisco"
	b.Shape = Enum.PartType.Ball
	b.Size = Vector3.new(1.8, 1.8, 1.8)
	b.Material = Enum.Material.Foil
	b.Reflectance = 0.5
	b.Color = Color3.fromRGB(225, 225, 235)
	b.Anchored = true
	b.CanCollide = false
	b.CanQuery = false
	b.CanTouch = false
	b.CastShadow = false
	b.CFrame = CFrame.new(0, 108.8, -25)
	b.Parent = Workspace
	bola = b
	table.insert(discoCosas, b)
	for _, z in LUCES_DISCO do
		local soporte = Instance.new("Part")
		soporte.Anchored = true
		soporte.CanCollide = false
		soporte.CanQuery = false
		soporte.CanTouch = false
		soporte.Transparency = 1
		soporte.Size = Vector3.one * 0.2
		soporte.Position = Vector3.new(0, 108, z)
		local luz = Instance.new("PointLight")
		luz.Range = 22
		luz.Brightness = 3
		luz.Shadows = false
		luz.Parent = soporte
		soporte.Parent = Workspace
		table.insert(luces, luz)
		table.insert(discoCosas, soporte)
	end
	local cc = Instance.new("ColorCorrectionEffect")
	cc.Name = "CaosDisco"
	cc.Contrast = 0.1
	cc.Parent = Lighting
	tinteDisco = cc
	table.insert(discoCosas, cc)
	local id = Audio.IDS.Disco
	if id then
		local s = Instance.new("Sound")
		s.SoundId = `rbxassetid://{id}`
		s.Looped = true
		s.Volume = (Audio.DATOS.Disco or { volumen = 0.5 }).volumen
		local grupo = SoundService:FindFirstChild("Efectos")
		if grupo and grupo:IsA("SoundGroup") then
			s.SoundGroup = grupo
		end
		s.Parent = SoundService
		s:Play()
		table.insert(discoCosas, s)
	end
end

local function terminarDisco()
	for _, c in discoCosas do
		c:Destroy()
	end
	table.clear(discoCosas)
	table.clear(luces)
	bola = nil
	tinteDisco = nil
end

local function botar()
	local personaje = jugador.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
	if personaje and humanoide and raiz and raiz:IsA("BasePart") and not humanoide.SeatPart and humanoide.FloorMaterial ~= Enum.Material.Air and personaje:GetAttribute("Ragdoll") ~= true then
		raiz.AssemblyLinearVelocity += Vector3.new(0, 20, 0)
	end
end

local function disco(ahora: number)
	local fin = avion:GetAttribute("Disco")
	if typeof(fin) ~= "number" or Workspace:GetServerTimeNow() > fin then
		if bola then
			terminarDisco()
		end
		return
	end
	if not bola then
		empezarDisco()
	end
	local b = bola :: BasePart
	b.CFrame = CFrame.new(b.Position) * CFrame.Angles(0, ahora * 2, 0)
	for i, luz in luces do
		luz.Color = Color3.fromHSV((ahora * 0.5 + i * 0.25) % 1, 0.8, 1)
	end
	local cc = tinteDisco
	if cc then
		cc.TintColor = Color3.fromHSV((ahora * 0.5) % 1, 0.25, 1)
	end
	if ahora > latido then
		latido = ahora + 0.5
		Camara.sacudir(0.12)
		botar()
	end
end

local function enPeste(pos: Vector3): boolean
	for _, n in CollectionService:GetTagged("Peste") do
		if n:IsA("BasePart") then
			local r = n:GetAttribute("Radio")
			if (n.Position - pos).Magnitude < (if typeof(r) == "number" then r else 8) then
				return true
			end
		end
	end
	return false
end

local function peste(ahora: number, dt: number)
	local camara = Workspace.CurrentCamera
	if not camara then
		return
	end
	local dentro = enPeste(camara.CFrame.Position)
	if dentro and not dentroPeste then
		Rafagas.palabra(camara.CFrame.Position + camara.CFrame.LookVector * 6, "¡PUAJ!", ESTILOS.Asco.color, ESTILOS.Asco.fondo, 1, true)
	end
	dentroPeste = dentro
	nivelPeste = math.clamp(nivelPeste + (if dentro then dt * 1.5 else -dt), 0, 1)
	if nivelPeste <= 0 then
		local cc, blur = tintePeste, desenfoque
		if cc then
			cc:Destroy()
			tintePeste = nil
		end
		if blur then
			blur:Destroy()
			desenfoque = nil
		end
		return
	end
	local cc = tintePeste
	if not cc then
		local nuevo = Instance.new("ColorCorrectionEffect")
		nuevo.Name = "CaosPeste"
		nuevo.Parent = Lighting
		tintePeste = nuevo
		cc = nuevo
	end
	local blur = desenfoque
	if not blur then
		local nuevo = Instance.new("BlurEffect")
		nuevo.Name = "CaosPeste"
		nuevo.Parent = Lighting
		desenfoque = nuevo
		blur = nuevo
	end
	local c = cc :: ColorCorrectionEffect
	local b = blur :: BlurEffect
	c.TintColor = Color3.new(1, 1, 1):Lerp(Color3.fromRGB(190, 255, 140), nivelPeste)
	c.Saturation = -0.3 * nivelPeste
	b.Size = 5 * nivelPeste
	if dentro and ahora > arcada then
		arcada = ahora + rng:NextNumber(1.2, 2)
		Camara.sacudir(0.08)
	end
end

function Caos.iniciar()
	local remoto = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Caos") :: RemoteEvent
	remoto.OnClientEvent:Connect(function(tipo, posicion, texto, estilo, escala)
		if tipo ~= "Palabra" or typeof(posicion) ~= "Vector3" or typeof(texto) ~= "string" or typeof(estilo) ~= "string" then
			return
		end
		local e = ESTILOS[estilo] or ESTILOS.Grito
		Rafagas.palabra(posicion, texto, e.color, e.fondo, if typeof(escala) == "number" then escala else 1, e.nube)
	end)
	vigilarTemblor("PuertaBano", "Atascada")
	vigilarTemblor("DispensadorCafe", "Loca")
	RunService.RenderStepped:Connect(function(dt)
		local ahora = os.clock()
		for _, t in temblores do
			t.objetivo:PivotTo(t.base * CFrame.new(rng:NextNumber(-0.04, 0.04), rng:NextNumber(-0.03, 0.03), 0) * CFrame.Angles(0, rng:NextNumber(-0.03, 0.03), rng:NextNumber(-0.04, 0.04)))
		end
		disco(ahora)
		peste(ahora, dt)
	end)
end

return Caos
