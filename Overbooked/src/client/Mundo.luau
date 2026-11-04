--!strict
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Mundo = {}

type Pieza = {
	parte: BasePart,
	rel: Vector3,
	giro: CFrame,
}

type Nube = {
	altura: number,
	pos: Vector3,
	piezas: { { parte: BasePart, offset: Vector3 } },
}

local avion = Workspace:WaitForChild("Avion") :: Model
local PIVOTE = Vector3.new(0, 100, -18)
local ESCALA_ALTURA = 0.07
local ESCALA_VELOCIDAD = 0.35
local RADIO = 1600
local rng = Random.new()

local carpeta = Instance.new("Folder")
carpeta.Name = "CieloLocal"
local suelo: Part
local pista: Part
local campos: { Pieza } = {}
local nubes: { Nube } = {}
local partes: { BasePart } = {}
local marcos: { CFrame } = {}
local rumbo = 0
local recorrido = 0
local faseAnterior = ""

local function nueva(tamano: Vector3, color: Color3, material: Enum.Material, forma: Enum.PartType?): Part
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Size = tamano
	p.Color = color
	p.Material = material
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	if forma then
		p.Shape = forma
	end
	p.Parent = carpeta
	return p
end

local function construir()
	suelo = nueva(Vector3.new(RADIO * 4, 2, RADIO * 4), Color3.fromRGB(107, 191, 89), Enum.Material.Grass)
	pista = nueva(Vector3.new(34, 0.4, 520), Color3.fromRGB(58, 61, 66), Enum.Material.Asphalt)
	local colores = {
		Color3.fromRGB(150, 200, 90),
		Color3.fromRGB(210, 190, 100),
		Color3.fromRGB(90, 160, 80),
		Color3.fromRGB(190, 150, 90),
		Color3.fromRGB(70, 130, 70),
		Color3.fromRGB(120, 180, 220),
	}
	for _ = 1, 90 do
		local c = colores[rng:NextInteger(1, #colores)]
		local tamano = Vector3.new(rng:NextNumber(60, 220), 1, rng:NextNumber(60, 220))
		local p = nueva(tamano, c, if c.B > 0.8 then Enum.Material.Glass else Enum.Material.Grass)
		table.insert(campos, {
			parte = p :: BasePart,
			rel = Vector3.new(rng:NextNumber(-RADIO, RADIO), 0.6, rng:NextNumber(-RADIO, RADIO)),
			giro = CFrame.Angles(0, rng:NextNumber(0, math.pi), 0),
		})
	end
	for _ = 1, 55 do
		local nube: Nube = {
			altura = rng:NextNumber(900, 7800),
			pos = Vector3.new(rng:NextNumber(-RADIO, RADIO), 0, rng:NextNumber(-RADIO, RADIO)),
			piezas = {},
		}
		local escala = rng:NextNumber(14, 34)
		for _ = 1, rng:NextInteger(3, 5) do
			local s = escala * rng:NextNumber(0.6, 1.2)
			local p = nueva(Vector3.one * s, Color3.fromRGB(250, 252, 255), Enum.Material.SmoothPlastic, Enum.PartType.Ball)
			table.insert(nube.piezas, {
				parte = p :: BasePart,
				offset = Vector3.new(rng:NextNumber(-1, 1) * escala, rng:NextNumber(-0.3, 0.3) * escala, rng:NextNumber(-1, 1) * escala * 0.7),
			})
		end
		table.insert(nubes, nube)
	end
	table.insert(partes, suelo)
	table.insert(partes, pista)
	for _, c in campos do
		table.insert(partes, c.parte)
	end
	for _, n in nubes do
		for _, pieza in n.piezas do
			table.insert(partes, pieza.parte)
		end
	end
	for _ = 1, #partes do
		table.insert(marcos, CFrame.identity)
	end
end

local function envolver(v: Vector3): Vector3
	local x, z = v.X, v.Z
	if z > RADIO then
		z -= RADIO * 2
		x = rng:NextNumber(-RADIO, RADIO)
	elseif z < -RADIO then
		z += RADIO * 2
	end
	if x > RADIO then
		x -= RADIO * 2
	elseif x < -RADIO then
		x += RADIO * 2
	end
	return Vector3.new(x, v.Y, z)
end

local function numero(nombre: string): number
	local v = avion:GetAttribute(nombre)
	return if typeof(v) == "number" then v else 0
end

local function actualizar(dt: number)
	local fase = avion:GetAttribute("Fase")
	local enAire = fase == "Despegue" or fase == "Vuelo" or fase == "Aproximacion" or fase == "Frenando" or fase == "Estrellado"
	if not enAire then
		if carpeta.Parent then
			carpeta.Parent = nil
		end
		return
	end
	if not carpeta.Parent then
		carpeta.Parent = Workspace
		rumbo = 0
	end
	if fase == "Despegue" and faseAnterior ~= "Despegue" then
		recorrido = 0
	end
	faseAnterior = if typeof(fase) == "string" then fase else ""
	local velocidad = numero("Velocidad") / 3.6 * ESCALA_VELOCIDAD
	local altitud = numero("Altitud")
	local alabeo = numero("Alabeo")
	local cab = numero("Cabeceo")
	local giro = math.rad(alabeo * 0.09) * dt
	rumbo += giro
	local actitud = CFrame.new(PIVOTE) * CFrame.Angles(0, 0, math.rad(alabeo)) * CFrame.Angles(math.rad(-cab), 0, 0)
	local avance = Vector3.new(0, 0, velocidad * dt)
	local yaw = CFrame.Angles(0, giro, 0)
	local alturaSuelo = -(10 + altitud * ESCALA_ALTURA)
	local i = 0
	local function poner(cf: CFrame)
		i += 1
		marcos[i] = cf
	end
	poner(actitud * CFrame.new(0, alturaSuelo - 1, 0))
	recorrido += velocidad * dt
	local zPista = if fase == "Aproximacion" or fase == "Frenando" then -(numero("Total") - numero("Distancia")) * 30 else -200 + recorrido
	poner(actitud * CFrame.new(0, alturaSuelo + 0.25, zPista))
	for _, c in campos do
		c.rel = envolver(yaw * (c.rel + avance))
		poner(actitud * CFrame.new(c.rel.X, alturaSuelo + 0.1, c.rel.Z) * c.giro)
	end
	for _, n in nubes do
		n.pos = envolver(yaw * (n.pos + avance))
		local y = (n.altura - altitud) * ESCALA_ALTURA
		for _, pieza in n.piezas do
			poner(actitud * CFrame.new(n.pos + pieza.offset + Vector3.new(0, y, 0)))
		end
	end
	Workspace:BulkMoveTo(partes, marcos, Enum.BulkMoveMode.FireCFrameChanged)
end

function Mundo.iniciar()
	construir()
	RunService.PreRender:Connect(actualizar)
end

return Mundo
