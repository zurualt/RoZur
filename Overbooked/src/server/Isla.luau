--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")

local Audio = require(ReplicatedStorage.Shared.Audio)
local Config = require(ReplicatedStorage.Shared.Config)
local ImagenesCascada = require(ReplicatedStorage.Shared.ImagenesCascada)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Activos = require(script.Parent.Activos)
local Agarre = require(script.Parent.Agarre)
local Avion = require(script.Parent.Avion)
local Objetos = require(script.Parent.Objetos)
local Personajes = require(script.Parent.Personajes)
local Rafagas = require(script.Parent.Rafagas)
local Sonidos = require(script.Parent.Sonidos)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local RemotoSacudida = Remotos:WaitForChild("Sacudida") :: UnreliableRemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder

type Cangrejo = { parte: BasePart, casa: Vector3, objetivo: Vector3, espera: number }

local Isla = {}

local C = Config.ISLA
local ICONOS = { RadioAntena = "Radio", RadioBateria = "Radio", RadioCaja = "Radio", Tronco = "Tronco", Bengala = "Bengala" }
local rng = Random.new()
local isla: Model
local carpeta: Folder
local spots: { [string]: { BasePart } } = {}
local zonas: { [string]: BasePart } = {}
local cangrejos: { Cangrejo } = {}
local pellizcos: { [Player]: number } = {}
local efectos: { Instance } = {}
local palmeras: { BasePart } = {}
local fuegos: { BasePart } = {}
local flores: { BasePart } = {}
local rocas: { BasePart } = {}
local cascada: BasePart? = nil
local decorados: { BasePart } = {}
local asentados: { [BasePart]: boolean } = {}
local datosTerreno: StringValue? = nil
local zonasTerreno: { { minimo: Vector3, maximo: Vector3 } } = {}
local guardado: { [Instance]: { [string]: any } } = {}
local HUMO_RESTOS = Color3.fromRGB(70, 66, 64)
local ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
local VALOR: { [number]: number } = {}
for i = 1, #ALFABETO do
	VALOR[string.byte(ALFABETO, i)] = i - 1
end
local BLOQUE = 16
local VIENTO = Vector3.new(2.2, 0, 1.4)
local FLUJO = 1
local SIN_ASENTAR = {
	Muelle = true,
	Pilote = true,
	Cascada = true,
	LabioCascada = true,
	Espuma = true,
	Gaviota = true,
	Mirador = true,
	EstacionRadio = true,
	Nenufares = true,
}
local MATERIAL_COLOR = {
	[Enum.Material.Sand] = Color3.fromRGB(232, 206, 150),
	[Enum.Material.Salt] = Color3.fromRGB(198, 170, 116),
	[Enum.Material.Grass] = Color3.fromRGB(104, 184, 64),
	[Enum.Material.LeafyGrass] = Color3.fromRGB(70, 146, 56),
	[Enum.Material.Ground] = Color3.fromRGB(168, 120, 74),
	[Enum.Material.Rock] = Color3.fromRGB(146, 152, 156),
	[Enum.Material.Slate] = Color3.fromRGB(36, 92, 112),
}
local PROPIEDADES: { [string]: { [string]: any } } = {
	Terrain = {
		WaterColor = Color3.fromRGB(18, 150, 176),
		WaterTransparency = 0.62,
		WaterWaveSize = 0.12,
		WaterWaveSpeed = 7,
		WaterReflectance = 0.45,
	},
	Lighting = {
		OutdoorAmbient = Color3.fromRGB(122, 122, 128),
		ColorShift_Top = Color3.fromRGB(255, 248, 236),
		EnvironmentDiffuseScale = 0.5,
	},
	Atmosphere = {
		Color = Color3.fromRGB(222, 228, 232),
		Decay = Color3.fromRGB(150, 200, 226),
		Haze = 0.9,
		Glare = 0.18,
	},
	ColorCorrectionEffect = {
		Saturation = 0.06,
		Contrast = 0.1,
		TintColor = Color3.fromRGB(255, 253, 248),
	},
}

local function numero(i: Instance, nombre: string): number
	local v = i:GetAttribute(nombre)
	return if typeof(v) == "number" then v else 0
end

local function lista(i: Instance, nombre: string): { string }
	local v = i:GetAttribute(nombre)
	local out = {}
	if typeof(v) == "string" then
		for parte in string.gmatch(v, "[^,]+") do
			table.insert(out, parte)
		end
	end
	return out
end

local function ambienteTropical()
	local Lighting = game:GetService("Lighting")
	local objetivos: { [string]: Instance? } = {
		Terrain = Workspace.Terrain,
		Lighting = Lighting,
		Atmosphere = Lighting:FindFirstChildOfClass("Atmosphere"),
		ColorCorrectionEffect = Lighting:FindFirstChildOfClass("ColorCorrectionEffect"),
	}
	for clase, valores in PROPIEDADES do
		local objetivo = objetivos[clase]
		if not objetivo then
			continue
		end
		local copia = guardado[objetivo] or {}
		guardado[objetivo] = copia
		for propiedad, valor in valores do
			copia[propiedad] = (objetivo :: any)[propiedad];
			(objetivo :: any)[propiedad] = valor
		end
	end
	local terreno = Workspace.Terrain
	local colores = {}
	for material, color in MATERIAL_COLOR do
		colores[material.Name] = terreno:GetMaterialColor(material)
		terreno:SetMaterialColor(material, color)
	end
	guardado[script] = colores
end

local function restaurarAmbiente()
	local terreno = Workspace.Terrain
	for objetivo, valores in guardado do
		if objetivo == script then
			for nombre, color in valores do
				terreno:SetMaterialColor((Enum.Material :: any)[nombre], color)
			end
			continue
		end
		for propiedad, valor in valores do
			(objetivo :: any)[propiedad] = valor
		end
	end
	table.clear(guardado)
end

local function generarTerreno()
	local datos = datosTerreno
	if not datos then
		return
	end
	local terreno = Workspace.Terrain
	local x0, z0, y0 = numero(datos, "X0"), numero(datos, "Z0"), numero(datos, "Y0")
	local nx, nz, celda = numero(datos, "NX"), numero(datos, "NZ"), numero(datos, "Celda")
	local mar, fondo, oceano = numero(datos, "Mar"), numero(datos, "Fondo"), numero(datos, "Oceano")
	local materiales: { Enum.Material } = {}
	for _, nombre in lista(datos, "Materiales") do
		table.insert(materiales, (Enum.Material :: any)[nombre])
	end
	local niveles: { number } = {}
	for _, v in lista(datos, "Niveles") do
		table.insert(niveles, tonumber(v) or mar)
	end
	local texto = datos.Value
	local alturas: { number } = table.create(nx * nz)
	local mats: { Enum.Material } = table.create(nx * nz)
	local aguas: { number } = table.create(nx * nz)
	local techo = mar
	for i = 1, nx * nz do
		local a, b, c, d = string.byte(texto, i * 4 - 3, i * 4)
		local h = y0 + (VALOR[a] * 64 + VALOR[b]) / 32
		alturas[i] = h
		mats[i] = materiales[VALOR[c] + 1]
		aguas[i] = niveles[VALOR[d] + 1]
		techo = math.max(techo, h, aguas[i])
	end
	techo = math.ceil(techo / celda + 1) * celda
	local ny = (techo - y0) // celda
	local cx, cz = x0 + nx * celda / 2, z0 + nz * celda / 2
	table.insert(zonasTerreno, { minimo = Vector3.new(cx - oceano / 2, y0, cz - oceano / 2), maximo = Vector3.new(cx + oceano / 2, techo, cz + oceano / 2) })
	local trozo = 1024
	for ox = -oceano / 2, oceano / 2 - 1, trozo do
		for oz = -oceano / 2, oceano / 2 - 1, trozo do
			local x, z = cx + ox + trozo / 2, cz + oz + trozo / 2
			terreno:FillBlock(CFrame.new(x, (y0 + fondo - 2) / 2, z), Vector3.new(trozo, fondo - 2 - y0, trozo), Enum.Material.Slate)
			terreno:FillBlock(CFrame.new(x, (fondo - 2 + mar) / 2, z), Vector3.new(trozo, mar - fondo + 2, trozo), Enum.Material.Water)
		end
		task.wait()
	end
	for bx = 0, nx - 1, BLOQUE do
		local ancho = math.min(BLOQUE, nx - bx)
		local solido, ocupado, liquido = table.create(ancho), table.create(ancho), table.create(ancho)
		for ix = 1, ancho do
			local cs, co, cl = table.create(ny), table.create(ny), table.create(ny)
			for iy = 1, ny do
				cs[iy], co[iy], cl[iy] = table.create(nz), table.create(nz), table.create(nz)
			end
			for iz = 1, nz do
				local i = (iz - 1) * nx + bx + ix
				local h, m, w = alturas[i], mats[i], aguas[i]
				local tierra = h > mar + 3 and m ~= Enum.Material.Sand and m ~= Enum.Material.Salt
				for iy = 1, ny do
					local yb = y0 + (iy - 1) * celda
					local o = math.clamp((h - yb) / celda - 0.5, 0, 1)
					cs[iy][iz] = if o <= 0 then Enum.Material.Air elseif h - yb > celda * 2.5 then (if tierra then Enum.Material.Rock else Enum.Material.Sand) else m
					co[iy][iz] = o
					cl[iy][iz] = math.min(math.clamp((w - yb) / celda, 0, 1), 1 - o)
				end
			end
			solido[ix], ocupado[ix], liquido[ix] = cs, co, cl
		end
		local region = Region3.new(Vector3.new(x0 + bx * celda, y0, z0), Vector3.new(x0 + (bx + ancho) * celda, techo, z0 + nz * celda))
		terreno:WriteVoxelChannels(region, celda, { SolidMaterial = solido, SolidOccupancy = ocupado, LiquidOccupancy = liquido })
		task.wait()
	end
end

local function borrarTerreno()
	for _, z in zonasTerreno do
		local minimo, maximo = z.minimo - Vector3.new(4, 4, 4), z.maximo + Vector3.new(4, 4, 4)
		for x = minimo.X, maximo.X - 1, 512 do
			for zz = minimo.Z, maximo.Z - 1, 512 do
				local a = Vector3.new(x, minimo.Y, zz)
				local b = Vector3.new(math.min(x + 512, maximo.X), maximo.Y, math.min(zz + 512, maximo.Z))
				Workspace.Terrain:FillBlock(CFrame.new((a + b) / 2), b - a, Enum.Material.Air)
			end
			task.wait()
		end
	end
	table.clear(zonasTerreno)
end

local function textura(nombre: string): string
	local id = ImagenesCascada[nombre]
	return if id then `rbxassetid://{id}` else VFX.textura(nombre)
end

local function emisor(padre: Instance, imagen: string, color: ColorSequence, tamano: NumberSequence, ritmo: number, vida: NumberRange, velocidad: NumberRange, aceleracion: Vector3): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Texture = textura(imagen)
	e.Color = color
	e.Size = tamano
	e.Rate = ritmo
	e.Lifetime = vida
	e.Speed = velocidad
	e.Acceleration = aceleracion
	e.SpreadAngle = Vector2.new(180, 180)
	e.Rotation = NumberRange.new(0, 360)
	e.RotSpeed = NumberRange.new(-160, 160)
	e.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1),
		NumberSequenceKeypoint.new(0.15, 0),
		NumberSequenceKeypoint.new(0.85, 0),
		NumberSequenceKeypoint.new(1, 1),
	})
	e.Parent = padre
	return e
end

local function punto(posicion: Vector3, nombre: string): Attachment
	local a = Instance.new("Attachment")
	a.Name = nombre
	a.Position = posicion
	a.Parent = Workspace.Terrain
	table.insert(efectos, a)
	return a
end

local function elegir<T>(opciones: { T }, n: number): { T }
	local out = {}
	for _ = 1, math.min(n, #opciones) do
		table.insert(out, opciones[rng:NextInteger(1, #opciones)])
	end
	return out
end

local function ambienteVivo()
	for _, f in fuegos do
		local a = punto(f.Position + Vector3.new(0, f.Size.Y * 0.2, 0), "FuegoRestos")
		VFX.fuego(a, numero(f, "Fuego"))
	end
	for _, f in elegir(flores, 10) do
		local a = punto(f.Position + Vector3.new(0, 2, 0), "Mariposas")
		emisor(a, "Hoja", ColorSequence.new(Color3.fromRGB(255, 120, 190), Color3.fromRGB(255, 220, 90)), NumberSequence.new(0.7), 0.6,
			NumberRange.new(4, 7), NumberRange.new(1.5, 3), Vector3.new(0, 0.6, 0))
	end
	for _, p in elegir(palmeras, 8) do
		local a = punto(p.Position + Vector3.new(0, p.Size.Y * 0.42, 0), "HojasCaen")
		local e = emisor(a, "Hoja", ColorSequence.new(Color3.fromRGB(120, 200, 80)), NumberSequence.new(0.9), 0.25,
			NumberRange.new(5, 8), NumberRange.new(1, 3), Vector3.new(1.5, -2.5, 0.6))
		e.Drag = 1
	end
	for _, r in elegir(rocas, 8) do
		local a = punto(r.Position, "Espuma")
		local e = emisor(a, "Humo2", ColorSequence.new(Color3.fromRGB(245, 252, 255)), NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1.5),
			NumberSequenceKeypoint.new(1, 5),
		}), 1.2, NumberRange.new(0.8, 1.4), NumberRange.new(4, 8), Vector3.new(0, -6, 0))
		e.SpreadAngle = Vector2.new(35, 35)
		e.EmissionDirection = Enum.NormalId.Top
	end
end

local function sonidoBucle(nombre: string, padre: Instance, alcance: number?): Sound?
	local id = Audio.IDS[nombre]
	if not id then
		return nil
	end
	local s = Instance.new("Sound")
	s.Name = nombre
	s.SoundId = `rbxassetid://{id}`
	s.Looped = true
	local datos = Audio.DATOS[nombre]
	s.Volume = if datos then datos.volumen else 0.6
	s.RollOffMode = Enum.RollOffMode.InverseTapered
	s.RollOffMinDistance = 10
	s.RollOffMaxDistance = alcance or 120
	s.Parent = padre
	s:Play()
	table.insert(efectos, s)
	return s
end

local function curva(puntos: { { number } }): NumberSequence
	local k = {}
	for _, p in puntos do
		table.insert(k, NumberSequenceKeypoint.new(p[1], p[2]))
	end
	return NumberSequence.new(k)
end

local function eje(posicion: Vector3, direccion: Vector3): CFrame
	local d = direccion.Unit
	return CFrame.lookAt(posicion, posicion + d, if math.abs(d.Y) > 0.95 then Vector3.zAxis else Vector3.yAxis) * CFrame.Angles(0, math.pi / 2, 0)
end

local function soloTerreno(agua: boolean): RaycastParams
	local p = RaycastParams.new()
	p.FilterType = Enum.RaycastFilterType.Include
	p.FilterDescendantsInstances = { Workspace.Terrain }
	p.IgnoreWater = not agua
	return p
end

local function viga(padre: BasePart, a0: Attachment, a1: Attachment, imagen: string, ancho0: number, ancho1: number): Beam
	local b = Instance.new("Beam")
	b.Name = imagen
	b.Attachment0 = a0
	b.Attachment1 = a1
	b.Texture = textura(imagen)
	b.Width0 = ancho0
	b.Width1 = ancho1
	b.FaceCamera = true
	b.Segments = 16
	b.Parent = padre
	table.insert(efectos, b)
	return b
end

local function zonaVfx(nombre: string, cf: CFrame, tam: Vector3): BasePart
	local p = Instance.new("Part")
	p.Name = nombre
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Transparency = 1
	p.Size = tam
	p.CFrame = cf
	p.Parent = isla
	table.insert(efectos, p)
	return p
end

local function enCaja(e: ParticleEmitter)
	e.Shape = Enum.ParticleEmitterShape.Box
	e.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
end

local function cascadaViva(mirador: Vector3): Vector3?
	local c = cascada
	if not c then
		return nil
	end
	local function ancla(nombre: string): Attachment?
		local a = c:FindFirstChild(nombre)
		return if a and a:IsA("Attachment") then a else nil
	end
	local impacto, lago = ancla("Impacto"), ancla("Lago")
	if not impacto or not lago then
		return nil
	end
	local centro = impacto.WorldPosition
	local hit = Workspace:Raycast(centro + Vector3.new(0, 4, 0), Vector3.new(0, -14, 0), soloTerreno(true))
	local agua = if hit then hit.Position.Y else centro.Y - 0.6
	local giro = c.CFrame.Rotation
	local blanco = ColorSequence.new(Color3.fromRGB(245, 252, 255))
	local gotas = ColorSequence.new(Color3.fromRGB(220, 244, 255))
	for i = 1, 5 do
		local a0, a1 = ancla(`Labio{i}`), ancla(`Base{i}`)
		if not a0 or not a1 then
			continue
		end
		a0.CFrame = eje(a0.Position, Vector3.new(0, -0.45, -1))
		a1.CFrame = eje(a1.Position, Vector3.new(0, -1, 0))
		local b = viga(c, a0, a1, "AguaCascada", 2.3, 3.3)
		b.CurveSize0 = 1.2
		b.CurveSize1 = 1.6
		b.TextureMode = Enum.TextureMode.Wrap
		b.TextureLength = 4.5 + (i % 3) * 0.8
		b.TextureSpeed = FLUJO * (1.5 + (i % 2) * 0.35)
		b.Transparency = curva({ { 0, 0.35 }, { 0.12, 0.12 }, { 0.85, 0.15 }, { 1, 0.7 } })
		b.Color = ColorSequence.new(Color3.fromRGB(190, 236, 250), Color3.fromRGB(235, 250, 255))
		b.LightEmission = 0.25
		b.LightInfluence = 0.55
		b.ZOffset = 0.05 * i
		if i >= 2 and i <= 4 then
			local f = viga(c, a0, a1, "EspumaCascada", 1.4, 2.8)
			f.CurveSize0 = 1.2
			f.CurveSize1 = 1.6
			f.TextureMode = Enum.TextureMode.Wrap
			f.TextureLength = 2.6
			f.TextureSpeed = FLUJO * 2.3
			f.Transparency = curva({ { 0, 0.6 }, { 0.2, 0.3 }, { 0.8, 0.25 }, { 1, 0.5 } })
			f.LightEmission = 0.35
			f.LightInfluence = 0.6
			f.ZOffset = 0.4
		end
		if i == 1 or i == 5 then
			local e = emisor(a0, "Gota", gotas, curva({ { 0, 0.35 }, { 1, 0.2 } }), 9, NumberRange.new(0.8, 1.1), NumberRange.new(2, 4), Vector3.new(0, -40, 0))
			e.EmissionDirection = Enum.NormalId.Right
			e.SpreadAngle = Vector2.new(25, 25)
			e.RotSpeed = NumberRange.new(0)
			e.Orientation = Enum.ParticleOrientation.VelocityParallel
		elseif i ~= 3 then
			local e = emisor(a0, "Humo2", blanco, curva({ { 0, 0.8 }, { 1, 2.2 } }), 5, NumberRange.new(0.5, 0.9), NumberRange.new(1.5, 3), Vector3.new(0, -22, 0))
			e.EmissionDirection = Enum.NormalId.Right
			e.SpreadAngle = Vector2.new(30, 30)
		end
	end
	local suelo = CFrame.new(centro.X, agua, centro.Z) * giro
	local base = zonaVfx("NieblaCascada", suelo * CFrame.new(0, 1, -1.5), Vector3.new(9, 1.5, 5))
	local niebla = emisor(base, "NieblaCascada", ColorSequence.new(Color3.fromRGB(255, 255, 255), Color3.fromRGB(214, 236, 248)),
		curva({ { 0, 4 }, { 0.4, 10 }, { 1, 15 } }), 5, NumberRange.new(4, 6), NumberRange.new(1, 2.5), VIENTO * 0.3 + Vector3.new(0, 0.6, 0))
	niebla.EmissionDirection = Enum.NormalId.Top
	niebla.SpreadAngle = Vector2.new(55, 55)
	niebla.Drag = 0.5
	niebla.RotSpeed = NumberRange.new(-12, 12)
	niebla.Transparency = curva({ { 0, 1 }, { 0.18, 0.45 }, { 0.6, 0.6 }, { 1, 1 } })
	niebla.LightInfluence = 0.7
	niebla.LightEmission = 0.08
	enCaja(niebla)
	local rocio = emisor(base, "Humo2", blanco, curva({ { 0, 1.5 }, { 1, 5.5 } }), 14, NumberRange.new(1.4, 2.4), NumberRange.new(5, 9), VIENTO * 1.4 + Vector3.new(0, -1.5, 0))
	rocio.EmissionDirection = Enum.NormalId.Top
	rocio.SpreadAngle = Vector2.new(35, 35)
	rocio.Drag = 1.3
	rocio.Transparency = curva({ { 0, 1 }, { 0.12, 0.5 }, { 0.7, 0.7 }, { 1, 1 } })
	enCaja(rocio)
	local salto = emisor(base, "Gota", gotas, curva({ { 0, 0.35 }, { 1, 0.25 } }), 28, NumberRange.new(0.7, 1.1), NumberRange.new(9, 15), Vector3.new(0, -45, 0) + VIENTO * 0.6)
	salto.EmissionDirection = Enum.NormalId.Top
	salto.SpreadAngle = Vector2.new(40, 40)
	salto.Orientation = Enum.ParticleOrientation.VelocityParallel
	salto.RotSpeed = NumberRange.new(0)
	salto.Rotation = NumberRange.new(0)
	enCaja(salto)
	local brillos = emisor(base, "Brillito", ColorSequence.new(Color3.fromRGB(255, 255, 236)), curva({ { 0, 0 }, { 0.5, 0.5 }, { 1, 0 } }), 10,
		NumberRange.new(0.6, 1.1), NumberRange.new(3, 7), Vector3.new(0, -5, 0) + VIENTO)
	brillos.EmissionDirection = Enum.NormalId.Top
	brillos.SpreadAngle = Vector2.new(60, 60)
	brillos.LightEmission = 1
	brillos.LightInfluence = 0
	enCaja(brillos)
	local velo = zonaVfx("VeloCascada", suelo * CFrame.new(0, 6.5, -0.6), Vector3.new(7, 9, 1.5))
	local deriva = emisor(velo, "Humo2", blanco, curva({ { 0, 2 }, { 1, 6.5 } }), 6, NumberRange.new(2.5, 3.5), NumberRange.new(0.5, 1.5), VIENTO)
	deriva.Drag = 0.3
	deriva.Transparency = curva({ { 0, 1 }, { 0.2, 0.72 }, { 0.7, 0.8 }, { 1, 1 } })
	enCaja(deriva)
	local poza = zonaVfx("EspumaPoza", suelo * CFrame.new(0, 0.12, -2.5), Vector3.new(10, 0.1, 7))
	local espuma = emisor(poza, "EspumaCascada", blanco, curva({ { 0, 2.5 }, { 1, 4.5 } }), 4, NumberRange.new(3, 4.5), NumberRange.new(0.05, 0.1), Vector3.zero)
	espuma.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
	espuma.EmissionDirection = Enum.NormalId.Top
	espuma.SpreadAngle = Vector2.zero
	espuma.RotSpeed = NumberRange.new(-25, 25)
	espuma.Transparency = curva({ { 0, 1 }, { 0.2, 0.2 }, { 0.75, 0.35 }, { 1, 1 } })
	espuma.LightInfluence = 0.8
	enCaja(espuma)
	local onda = emisor(punto(Vector3.new(centro.X, agua + 0.1, centro.Z), "OndaCascada"), "Onda", blanco, curva({ { 0, 2 }, { 1, 11 } }), 1.6,
		NumberRange.new(1.8, 2.2), NumberRange.new(0.05), Vector3.zero)
	onda.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
	onda.EmissionDirection = Enum.NormalId.Top
	onda.SpreadAngle = Vector2.zero
	onda.RotSpeed = NumberRange.new(0)
	onda.Transparency = curva({ { 0, 0.2 }, { 1, 1 } })
	local pLago = lago.WorldPosition
	local peces = zonaVfx("PecesCascada", CFrame.new(pLago.X, agua + 0.05, pLago.Z) * giro, Vector3.new(10, 0.1, 7))
	local pez = emisor(peces, "PezSalto", ColorSequence.new(Color3.new(1, 1, 1)), NumberSequence.new(1.5), 0.45, NumberRange.new(0.85, 0.9),
		NumberRange.new(10, 12), Vector3.new(0, -26, 0))
	pez.Orientation = Enum.ParticleOrientation.VelocityParallel
	pez.EmissionDirection = Enum.NormalId.Top
	pez.SpreadAngle = Vector2.new(25, 25)
	pez.Rotation = NumberRange.new(-90)
	pez.RotSpeed = NumberRange.new(0)
	pez.Transparency = curva({ { 0, 0 }, { 0.92, 0 }, { 1, 1 } })
	pez.LightInfluence = 1
	enCaja(pez)
	local hacia = (mirador - pLago) * Vector3.new(1, 0, 1)
	local normal = if hacia.Magnitude > 1 then hacia.Unit else c.CFrame.LookVector
	local lado = normal:Cross(Vector3.yAxis).Unit
	local medio = Vector3.new(pLago.X, agua + 0.6, pLago.Z)
	for k, e in { 1, 1.32 } do
		local a0 = punto(medio - lado * 15 * e, "Arcoiris")
		local a1 = punto(medio + lado * 15 * e, "Arcoiris")
		a0.CFrame = eje(a0.Position, Vector3.yAxis)
		a1.CFrame = eje(a1.Position, Vector3.yAxis)
		local b = viga(c, a0, a1, "Arcoiris", 2.6 * e, 2.6 * e)
		b.CurveSize0 = 17 * e
		b.CurveSize1 = -17 * e
		b.TextureMode = Enum.TextureMode.Stretch
		b.TextureLength = 1
		b.Segments = 32
		b.LightEmission = 0.7
		b.LightInfluence = 0
		local opaco = if k == 1 then 0.45 else 0.78
		b.Transparency = curva({ { 0, 1 }, { 0.12, opaco }, { 0.88, opaco }, { 1, 1 } })
	end
	for i = 1, 3 do
		local a0, a1 = ancla(`Rayo{i}`), ancla(`RayoFin{i}`)
		if a0 and a1 then
			local b = viga(c, a0, a1, "RayoLuz", 1.6, 6.5)
			b.TextureMode = Enum.TextureMode.Stretch
			b.TextureLength = 1
			b.Segments = 2
			b.LightEmission = 0.9
			b.LightInfluence = 0
			b.Color = ColorSequence.new(Color3.fromRGB(255, 244, 210))
			b.Transparency = NumberSequence.new(0.5 + i * 0.08)
		end
	end
	sonidoBucle("Cascada", impacto, 160)
	for i, s in spots.rapido or {} do
		local a = punto(s.Position, "Rapido")
		local e = emisor(a, "Humo2", blanco, curva({ { 0, 0.8 }, { 1, 2.4 } }), 3, NumberRange.new(0.7, 1.2), NumberRange.new(1, 2.5), Vector3.new(0, -3, 0))
		e.EmissionDirection = Enum.NormalId.Top
		e.SpreadAngle = Vector2.new(50, 50)
		local g = emisor(a, "Gota", gotas, curva({ { 0, 0.25 }, { 1, 0.18 } }), 5, NumberRange.new(0.5, 0.8), NumberRange.new(5, 8), Vector3.new(0, -35, 0))
		g.EmissionDirection = Enum.NormalId.Top
		g.SpreadAngle = Vector2.new(35, 35)
		g.Orientation = Enum.ParticleOrientation.VelocityParallel
		g.RotSpeed = NumberRange.new(0)
		local o = emisor(a, "Onda", blanco, curva({ { 0, 1 }, { 1, 4.5 } }), 0.9, NumberRange.new(1.2, 1.6), NumberRange.new(0.05), Vector3.zero)
		o.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
		o.EmissionDirection = Enum.NormalId.Top
		o.SpreadAngle = Vector2.zero
		o.RotSpeed = NumberRange.new(0)
		o.Transparency = curva({ { 0, 0.3 }, { 1, 1 } })
		if i % 2 == 1 then
			local son = sonidoBucle("Cascada", a, 45)
			if son then
				son.Volume *= 0.3
				son.PlaybackSpeed = 1.15
			end
		end
	end
	return Vector3.new(centro.X, agua, centro.Z)
end

local function asentar()
	local parametros = soloTerreno(false)
	local muestras = { Vector3.zero, Vector3.new(0.35, 0, 0.35), Vector3.new(-0.35, 0, 0.35), Vector3.new(0.35, 0, -0.35), Vector3.new(-0.35, 0, -0.35) }
	for _ = 1, 20 do
		local quedan = 0
		for i, d in decorados do
			if asentados[d] then
				continue
			end
			local modelo = d:FindFirstChildOfClass("Model")
			if not modelo then
				quedan += 1
				continue
			end
			asentados[d] = true
			local base = numero(d, "Base")
			local techo = -math.huge
			for _, m in muestras do
				local p = d.CFrame:PointToWorldSpace(d.Size * m)
				local r = Workspace:Raycast(Vector3.new(p.X, base + 30, p.Z), Vector3.new(0, -60, 0), parametros)
				if r then
					techo = math.max(techo, r.Position.Y)
				end
			end
			if techo > -math.huge and base - techo > 0.25 then
				local bajar = Vector3.new(0, base - techo - 0.1, 0)
				modelo:PivotTo(modelo:GetPivot() - bajar)
				d.CFrame -= bajar
				d:SetAttribute("Base", base - bajar.Y)
			end
			if i % 50 == 0 then
				task.wait()
			end
		end
		if quedan == 0 then
			return
		end
		task.wait(2)
	end
end

local function brillar(o: BasePart)
	local e = Instance.new("ParticleEmitter")
	e.Name = "Brillo"
	e.Texture = VFX.textura("Brillito")
	e.LightEmission = 1
	e.Color = ColorSequence.new(Color3.fromRGB(255, 236, 150))
	e.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(0.5, 0.9),
		NumberSequenceKeypoint.new(1, 0),
	})
	e.Rate = 3
	e.Lifetime = NumberRange.new(0.6, 1)
	e.Speed = NumberRange.new(0.5, 1.5)
	e.SpreadAngle = Vector2.new(180, 180)
	e.Parent = o
	local luz = Instance.new("PointLight")
	luz.Name = "Brillo"
	luz.Color = Color3.fromRGB(255, 220, 150)
	luz.Range = 9
	luz.Brightness = 0.8
	luz.Shadows = false
	luz.Parent = o
end

local function motores(): { Vector3 }
	local exterior = Workspace:WaitForChild("Avion"):FindFirstChild("Exterior")
	local lista = {}
	for _, lado in { "Izq", "Der" } do
		local m = exterior and exterior:FindFirstChild("Motor" .. lado)
		if m and m:IsA("BasePart") then
			table.insert(lista, m.Position)
		end
	end
	return lista
end

local function caerCoco()
	local palmera = palmeras[rng:NextInteger(1, #palmeras)]
	if not palmera then
		return
	end
	local copa = palmera.Position + Vector3.new(rng:NextNumber(-3, 3), palmera.Size.Y * 0.45, rng:NextNumber(-3, 3))
	Rafagas.lanzar("Hojas", copa, 1.4)
	local coco = Objetos.crear("Coco", CFrame.new(copa), carpeta)
	coco.AssemblyLinearVelocity = Vector3.new(0, -10, 0)
	task.delay(1.1, function()
		if not coco.Parent then
			return
		end
		for _, jugador in Players:GetPlayers() do
			local raiz = Personajes.raiz(jugador)
			if raiz and (raiz.Position - coco.Position).Magnitude < 4 then
				Personajes.ragdoll(jugador, 1.2, Vector3.new(rng:NextNumber(-20, 20), 20, rng:NextNumber(-20, 20)))
				Rafagas.lanzar("Bonk", raiz.Position + Vector3.new(0, 2.5, 0), 1.2)
				Sonidos.emitir("Coco", raiz.Position)
				RemotoAviso:FireClient(jugador, "¡Un coco en toda la cabeza!", "peligro")
			end
		end
	end)
end

local function aviso(texto: string, tipo: string)
	RemotoAviso:FireAllClients(texto, tipo)
end

local function mezclar<T>(lista: { T }?): { T }
	local copia = table.clone(lista or {})
	for i = #copia, 2, -1 do
		local j = rng:NextInteger(1, i)
		copia[i], copia[j] = copia[j], copia[i]
	end
	return copia
end

local function crear(tipo: string, spot: BasePart): BasePart
	local o = Objetos.crear(tipo, CFrame.new(spot.Position) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0), carpeta)
	local icono = ICONOS[tipo]
	if icono then
		o:SetAttribute("Icono", icono)
		CollectionService:AddTag(o, "ObjetivoIsla")
		brillar(o)
	end
	return o
end

local function crearCangrejo(spot: BasePart)
	local p: BasePart = Instance.new("Part")
	p.Name = "Cangrejo"
	p.Size = Vector3.new(2.4, 1.2, 1.8)
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.Transparency = 1
	p.CFrame = CFrame.new(spot.Position)
	p.Parent = carpeta
	Activos.vestirDinamico(p, "Cangrejo")
	table.insert(cangrejos, { parte = p, casa = spot.Position, objetivo = spot.Position, espera = 0 })
end

local function moverCangrejos(dt: number, ahora: number)
	for _, c in cangrejos do
		local pos = c.parte.Position
		local hacia = Vector3.new(c.objetivo.X - pos.X, 0, c.objetivo.Z - pos.Z)
		if hacia.Magnitude < 0.5 then
			if ahora >= c.espera then
				local a = rng:NextNumber(0, math.pi * 2)
				local r = rng:NextNumber(4, 22)
				c.objetivo = c.casa + Vector3.new(math.cos(a) * r, 0, math.sin(a) * r)
				c.espera = ahora + rng:NextNumber(0.6, 2.4)
			end
			continue
		end
		local direccion = hacia.Unit
		local nuevo = pos + direccion * math.min(hacia.Magnitude, C.VELOCIDAD_CANGREJO * dt)
		local frente = direccion:Cross(Vector3.yAxis)
		c.parte.CFrame = CFrame.lookAt(nuevo, nuevo + frente) * CFrame.Angles(0, 0, math.sin(ahora * 18) * 0.07)
	end
end

local function pellizcar(ahora: number)
	for _, jugador in Players:GetPlayers() do
		local raiz = Personajes.raiz(jugador)
		if not raiz or (pellizcos[jugador] or 0) > ahora then
			continue
		end
		for _, c in cangrejos do
			local d = raiz.Position - c.parte.Position
			if Vector3.new(d.X, 0, d.Z).Magnitude < C.PELLIZCO and math.abs(d.Y) < 4 then
				pellizcos[jugador] = ahora + 4
				c.objetivo = c.casa
				c.espera = ahora + 2
				local empuje = Vector3.new(d.X, 0, d.Z)
				Personajes.ragdoll(jugador, 1, (if empuje.Magnitude > 0.1 then empuje.Unit else Vector3.xAxis) * 28 + Vector3.new(0, 26, 0))
				Rafagas.lanzar("Ay", raiz.Position + Vector3.new(0, 2, 0), 1)
				Sonidos.emitir("Cangrejo", raiz.Position)
				RemotoAviso:FireClient(jugador, "¡Un cangrejo te ha pellizcado!", "peligro")
				break
			end
		end
	end
end

local function cerca(o: BasePart, zona: BasePart?, radio: number): boolean
	return zona ~= nil and (o.Position - zona.Position).Magnitude < radio
end

local function consumir(o: BasePart)
	Agarre.soltarObjeto(o)
	o:Destroy()
end

local RANURAS = { RadioAntena = -1.93, RadioBateria = -0.03, RadioCaja = 1.87 }

local function encajar(tipo: string)
	local estacion = zonas.Radio
	if not estacion then
		return
	end
	local alto = Config.OBJETOS[tipo].tamano.Y
	local cima = 2.11 - estacion.Size.Y / 2
	local pieza = Objetos.crear(tipo, estacion.CFrame * CFrame.new(RANURAS[tipo] or 0, cima + alto / 2, -0.19), carpeta)
	pieza.Anchored = true
	pieza.CanCollide = false
	CollectionService:RemoveTag(pieza, "Agarrable")
	Rafagas.lanzar("Chispas", pieza.Position, 1)
	Sonidos.emitir("Radio", pieza.Position)
end

local function encender()
	local hoguera = zonas.Hoguera
	if not hoguera then
		return
	end
	local a = Instance.new("Attachment")
	a.Name = "FuegoHoguera"
	a.Position = Vector3.new(0, 1, 0)
	a.Parent = hoguera
	VFX.fuego(a, 2.6)
	local luz = Instance.new("PointLight")
	luz.Color = Color3.fromRGB(255, 170, 80)
	luz.Range = 34
	luz.Brightness = 2.2
	luz.Parent = a
	table.insert(efectos, a)
	sonidoBucle("Hoguera", a, 90)
	Rafagas.lanzar("Bengala", hoguera.Position + Vector3.new(0, 2, 0), 2)
	Rafagas.lanzar("Chispas", hoguera.Position + Vector3.new(0, 2, 0), 2)
	Rafagas.lanzar("Humo", hoguera.Position + Vector3.new(0, 6, 0), 3)
	Sonidos.emitir("Ding", hoguera.Position)
end

local function hidroavion()
	local destino = zonas.Rescate
	if not destino then
		return
	end
	local p = Instance.new("Part")
	p.Name = "Hidroavion"
	p.Size = Vector3.new(40, 12, 32)
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.Transparency = 1
	local final = CFrame.new(destino.Position + Vector3.new(0, 6, 0)) * CFrame.Angles(0, math.rad(90), 0)
	local duracion = math.max(4, C.RESCATE - 4)
	p.CFrame = final
	p:SetAttribute("Inicio", Workspace:GetServerTimeNow())
	p:SetAttribute("Duracion", duracion)
	p.Parent = carpeta
	Activos.vestirDinamico(p, "Hidroavion")
	local motor = sonidoBucle("Hidroavion", p, 700)
	task.delay(duracion, function()
		if motor then
			motor:Stop()
		end
		if p.Parent then
			Rafagas.lanzar("Salpicadura", destino.Position, 4)
			Sonidos.emitir("Salpicadura", destino.Position)
		end
	end)
end

local function marcarDestinos(activos: boolean)
	for nombre, icono in ({ Radio = "Radio", Hoguera = "Fuego", Rescate = "Hidroavion" } :: { [string]: string }) do
		local z = zonas[nombre]
		if z then
			z:SetAttribute("Icono", icono)
			if activos then
				CollectionService:AddTag(z, "DestinoIsla")
			else
				CollectionService:RemoveTag(z, "DestinoIsla")
			end
		end
	end
end

local function estado(radio: number, lena: number, fuego: boolean, quedan: number, rescate: number)
	Estado:SetAttribute("IslaRadio", radio)
	Estado:SetAttribute("IslaLena", lena)
	Estado:SetAttribute("IslaFuego", fuego)
	Estado:SetAttribute("IslaQuedan", math.max(0, math.ceil(quedan)))
	Estado:SetAttribute("IslaRescate", math.ceil(rescate))
end

function Isla.jugar(): boolean
	local centro = Vector3.new(0, 104, -17)
	ambienteTropical()
	generarTerreno()
	Avion.prepararTierra()
	Avion.danarMotor("Izq", 50, true)
	Avion.danarMotor("Der", 35, rng:NextNumber() < 0.5)
	isla.Parent = Workspace
	task.delay(1.1, function()
		Rafagas.lanzar("Hongo", centro + Vector3.new(0, 0, -44), 2.5)
		for _, m in motores() do
			Rafagas.lanzar("Explosion", m, 2.5)
		end
		Rafagas.lanzar("Escombros", centro, 2)
		for z = -60, 30, 18 do
			Rafagas.lanzar("Arena", Vector3.new(0, 91, z), 2)
		end
		Sonidos.emitir("Explosion", centro)
		RemotoSacudida:FireAllClients(1)
		Personajes.ragdollTodos(3, 70)
	end)
	sonidoBucle("AmbienteIsla", isla)
	ambienteVivo()
	task.spawn(asentar)
	local chorro = cascadaViva(centro)
	local proximaSalpicadura = 0
	local piezas = mezclar(spots.radio)
	for i, tipo in C.PIEZAS do
		if piezas[i] then
			crear(tipo, piezas[i])
		end
	end
	for i, s in mezclar(spots.tronco) do
		if i <= C.TRONCOS + 2 then
			crear("Tronco", s)
		end
	end
	for i, s in mezclar(spots.coco) do
		if i <= C.COCOS then
			crear("Coco", s)
		end
	end
	for i, s in mezclar(spots.cangrejo) do
		if i <= C.CANGREJOS then
			crearCangrejo(s)
		end
	end
	local bengalas = spots.bengala
	if bengalas and bengalas[1] then
		crear("Bengala", bengalas[1])
	end
	marcarDestinos(true)
	task.delay(6.5, aviso, "¡Náufragos! Llevad las 3 piezas a la radio y 3 troncos a la hoguera, y encendedla con la bengala", "peligro")
	local radio, lena, fuego = 0, 0, false
	local rescate: number? = nil
	local fin = os.clock() + C.DURACION
	local ultimo = os.clock()
	local pista = 0
	local proximoHumo = 0
	local proximoCoco = os.clock() + rng:NextNumber(14, 22)
	local proximoPez = os.clock() + 3
	local puntosHumo = motores()
	table.insert(puntosHumo, centro + Vector3.new(0, 4, -44))
	for _, f in fuegos do
		table.insert(puntosHumo, f.Position)
	end
	while true do
		task.wait(0.1)
		local ahora = os.clock()
		moverCangrejos(ahora - ultimo, ahora)
		ultimo = ahora
		pellizcar(ahora)
		if ahora >= proximoHumo then
			proximoHumo = ahora + 2.5
			Rafagas.lanzar("Humo", puntosHumo[rng:NextInteger(1, #puntosHumo)] + Vector3.new(0, 3, 0), 2.5, HUMO_RESTOS)
		end
		if ahora >= proximoCoco then
			proximoCoco = ahora + rng:NextNumber(16, 28)
			caerCoco()
		end
		local peces = spots.pez
		if peces and #peces > 0 and ahora >= proximoPez then
			proximoPez = ahora + rng:NextNumber(3.5, 7)
			local pez = peces[rng:NextInteger(1, #peces)].Position + Vector3.new(rng:NextNumber(-6, 6), 0, rng:NextNumber(-6, 6))
			Rafagas.lanzar("Salpicadura", pez, rng:NextNumber(0.5, 0.8))
			Sonidos.emitir("Salpicadura", pez)
		end
		if chorro and ahora >= proximaSalpicadura then
			proximaSalpicadura = ahora + rng:NextNumber(0.9, 1.8)
			Rafagas.lanzar("Salpicadura", chorro + Vector3.new(rng:NextNumber(-3, 3), 0, rng:NextNumber(-3, 3)), rng:NextNumber(0.9, 1.4))
		end
		for _, o in carpeta:GetChildren() do
			if not o:IsA("BasePart") or not o:HasTag("ObjetivoIsla") then
				continue
			end
			local tipo = o:GetAttribute("Tipo")
			if typeof(tipo) ~= "string" then
				continue
			end
			if table.find(C.PIEZAS, tipo) and cerca(o, zonas.Radio, C.ENTREGA) then
				consumir(o)
				radio += 1
				encajar(tipo)
				aviso(if radio < #C.PIEZAS then `Pieza de radio colocada ({radio}/{#C.PIEZAS})` else "¡Radio reparada! Ya podemos pedir ayuda", "bien")
			elseif tipo == "Tronco" and lena < C.TRONCOS and cerca(o, zonas.Hoguera, C.ENTREGA) then
				consumir(o)
				lena += 1
				Rafagas.lanzar("Astillas", (zonas.Hoguera :: BasePart).Position, 1)
				Sonidos.emitir("Madera", (zonas.Hoguera :: BasePart).Position)
				aviso(`Leña en la hoguera ({lena}/{C.TRONCOS})`, "bien")
			elseif tipo == "Bengala" and not fuego and cerca(o, zonas.Hoguera, C.ENTREGA) then
				if lena >= C.TRONCOS then
					consumir(o)
					fuego = true
					encender()
					aviso("¡Hoguera encendida! Seguro que la ven desde lejos", "bien")
				elseif ahora > pista then
					pista = ahora + 6
					aviso(`Faltan troncos: la hoguera necesita {C.TRONCOS}`, "info")
				end
			end
		end
		if not rescate and radio >= #C.PIEZAS and fuego then
			rescate = ahora + C.RESCATE
			hidroavion()
			aviso("¡Os han visto! Un hidroavión viene a por vosotros", "bien")
		end
		estado(radio, lena, fuego, fin - ahora, if rescate then rescate - ahora else -1)
		if rescate and ahora >= rescate then
			local destino = zonas.Rescate
			local punto = if destino then destino.Position + Vector3.new(0, 8, 0) else centro
			Rafagas.lanzar("Confeti", punto, 3)
			Rafagas.lanzar("Monedas", punto, 2)
			for _, jugador in Players:GetPlayers() do
				local raiz = Personajes.raiz(jugador)
				if raiz then
					Rafagas.lanzar("Confeti", raiz.Position + Vector3.new(0, 4, 0), 1.5)
				end
			end
			Sonidos.emitir("Victoria", nil)
			return true
		end
		if not rescate and ahora >= fin then
			return false
		end
	end
end

function Isla.limpiar()
	for _, h in carpeta:GetChildren() do
		Agarre.soltarObjeto(h)
		h:Destroy()
	end
	for _, e in efectos do
		e:Destroy()
	end
	table.clear(efectos)
	table.clear(cangrejos)
	table.clear(pellizcos)
	marcarDestinos(false)
	for _, n in { "IslaRadio", "IslaLena", "IslaFuego", "IslaQuedan", "IslaRescate" } do
		Estado:SetAttribute(n, nil)
	end
	isla.Parent = ServerStorage
	borrarTerreno()
	restaurarAmbiente()
end

function Isla.iniciar()
	isla = ServerStorage:WaitForChild("Isla") :: Model
	carpeta = Instance.new("Folder")
	carpeta.Name = "Naufragio"
	carpeta.Parent = isla
	local datos = isla:FindFirstChild("Terreno")
	if datos and datos:IsA("StringValue") then
		datosTerreno = datos
		datos.Parent = nil
	end
	for _, d in isla:GetDescendants() do
		if not d:IsA("BasePart") then
			continue
		end
		local visual = d:GetAttribute("Visual")
		if typeof(visual) == "string" then
			local base = d:GetAttribute("Base")
			local normal = d:GetAttribute("Normal")
			if typeof(normal) == "Vector3" and typeof(base) == "number" then
				local pivote = Vector3.new(d.Position.X, base, d.Position.Z)
				local inclinar = CFrame.new(pivote) * CFrame.fromRotationBetweenVectors(Vector3.yAxis, normal.Unit) * CFrame.new(-pivote)
				local conexion: RBXScriptConnection
				conexion = d.ChildAdded:Connect(function(hijo)
					if hijo:IsA("Model") then
						conexion:Disconnect()
						hijo:PivotTo(inclinar * hijo:GetPivot())
					end
				end)
			end
			local escala = d:GetAttribute("Escala")
			Activos.vestirFijo(d, visual, if typeof(base) == "number" then base else nil, if typeof(escala) == "number" then escala else nil)
			if not SIN_ASENTAR[visual] and d:GetAttribute("Apoyo") == nil and typeof(base) == "number" then
				table.insert(decorados, d)
			end
		end
		if d.Name == "CascadaVFX" then
			cascada = d
		end
		local spot = d:GetAttribute("Spot")
		if typeof(spot) == "string" then
			local lista = spots[spot] or {}
			spots[spot] = lista
			table.insert(lista, d)
		end
		local zona = d:GetAttribute("Zona")
		if typeof(zona) == "string" then
			zonas[zona] = d
		end
		if d.Name == "Palmera" then
			table.insert(palmeras, d)
		end
		if d:GetAttribute("Fuego") then
			table.insert(fuegos, d)
		end
		local grupo = if visual == "Flores" then flores elseif visual == "Acantilado" or visual == "RocasPlanas" then rocas else nil
		if grupo then
			table.insert(grupo, d)
		end
	end
	Players.PlayerRemoving:Connect(function(jugador)
		pellizcos[jugador] = nil
	end)
end

return Isla
