--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Audio = require(ReplicatedStorage.Shared.Audio)
local Config = require(ReplicatedStorage.Shared.Config)
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
local cascadas: { BasePart } = {}
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
local MATERIAL_COLOR = {
	[Enum.Material.Sand] = Color3.fromRGB(232, 206, 150),
	[Enum.Material.Salt] = Color3.fromRGB(198, 170, 116),
	[Enum.Material.Grass] = Color3.fromRGB(104, 184, 64),
	[Enum.Material.LeafyGrass] = Color3.fromRGB(70, 146, 56),
	[Enum.Material.Ground] = Color3.fromRGB(168, 120, 74),
	[Enum.Material.Rock] = Color3.fromRGB(150, 146, 140),
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

local function emisor(padre: Instance, textura: string, color: ColorSequence, tamano: NumberSequence, ritmo: number, vida: NumberRange, velocidad: NumberRange, aceleracion: Vector3): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Texture = VFX.textura(textura)
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
	for _, c in cascadas do
		local a = punto(c.Position - Vector3.new(0, c.Size.Y * 0.45, 0) + c.CFrame.LookVector * 2, "Rocio")
		local e = emisor(a, "Humo2", ColorSequence.new(Color3.fromRGB(240, 250, 255)), NumberSequence.new({
			NumberSequenceKeypoint.new(0, 2),
			NumberSequenceKeypoint.new(1, 7),
		}), 8, NumberRange.new(1, 1.8), NumberRange.new(3, 6), Vector3.new(0, 2, 0))
		e.EmissionDirection = Enum.NormalId.Top
		e.SpreadAngle = Vector2.new(60, 60)
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
	p.CFrame = final + Vector3.new(1400, 260, 0)
	p.Parent = carpeta
	Activos.vestirDinamico(p, "Hidroavion")
	local motor = sonidoBucle("Hidroavion", p, 700)
	local duracion = math.max(4, C.RESCATE - 4)
	TweenService:Create(p, TweenInfo.new(duracion, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = final }):Play()
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
	ambienteTropical()
	generarTerreno()
	Avion.prepararTierra()
	Avion.danarMotor("Izq", 50, true)
	Avion.danarMotor("Der", 35, rng:NextNumber() < 0.5)
	isla.Parent = Workspace
	sonidoBucle("AmbienteIsla", isla)
	ambienteVivo()
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
	task.delay(2.5, aviso, "¡Náufragos! Llevad las 3 piezas a la radio y 3 troncos a la hoguera, y encendedla con la bengala", "peligro")
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
			Activos.vestirFijo(d, visual, if typeof(base) == "number" then base else nil)
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
		local grupo = if visual == "Flores" then flores elseif visual == "Acantilado" or visual == "RocasPlanas" then rocas elseif visual == "Cascada" then cascadas else nil
		if grupo then
			table.insert(grupo, d)
		end
	end
	Players.PlayerRemoving:Connect(function(jugador)
		pellizcos[jugador] = nil
	end)
end

return Isla
