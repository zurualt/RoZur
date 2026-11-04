--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)

type Luz = { luz: Light, brillo: number, color: Color3 }
type Neon = { parte: BasePart, color: Color3 }
type Movil = { pivote: CFrame, partes: { BasePart }, relativos: { CFrame }, cframes: { CFrame }, clave: number }

local Cabina = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local luces: { Luz } = {}
local neones: { Neon } = {}
local rng = Random.new()
local ROJO = Color3.fromRGB(255, 72, 60)
local apagonHasta = 0
local ultimoFactor = -1
local ultimoRojo = -1

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
		if d:IsA("Light") then
			table.insert(luces, { luz = d, brillo = d.Brightness, color = d.Color })
		elseif d:IsA("BasePart") and d.Material == Enum.Material.Neon then
			table.insert(neones, { parte = d, color = d.Color })
		end
	end
end

local function luzCabina(t: number)
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
	local rojo = if avion:GetAttribute("Emergencia") == true then 0.55 + 0.45 * math.sin(t * 4) else 0
	if rojo > 0 then
		factor *= 0.75
	end
	factor = math.floor(factor * 20 + 0.5) / 20
	rojo = math.floor(rojo * 20 + 0.5) / 20
	if factor == ultimoFactor and rojo == ultimoRojo then
		return
	end
	ultimoFactor, ultimoRojo = factor, rojo
	for _, l in luces do
		l.luz.Brightness = l.brillo * factor
		l.luz.Color = l.color:Lerp(ROJO, rojo)
	end
	for _, n in neones do
		n.parte.Color = n.color:Lerp(Color3.new(0.1, 0.1, 0.1), 1 - factor):Lerp(ROJO, rojo * 0.8)
	end
end

function Cabina.iniciar()
	prepararLuces()
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
	local cab, ala, gas, mira = 0, 0, 0, 0
	local V = Config.VUELO
	RunService.RenderStepped:Connect(function(dt: number)
		local t = os.clock()
		luzCabina(t)
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
		end
	end)
end

return Cabina
