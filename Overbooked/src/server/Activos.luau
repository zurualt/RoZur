--!strict
local InsertService = game:GetService("InsertService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Cielo = require(ReplicatedStorage.Shared.Cielo)
local Config = require(ReplicatedStorage.Shared.Config)
local Criaturas = require(ReplicatedStorage.Shared.Criaturas)
local PasajerosVivos = require(ReplicatedStorage.Shared.PasajerosVivos)
local Visuales = require(ReplicatedStorage.Shared.Visuales)

local Activos = {}

local plantillas: { [string]: Model } = {}
local pendientes: { [string]: { (Model) -> () } } = {}
local fallidos: { [string]: boolean } = {}
local extras: { [string]: Visuales.Caja } = {}

local ESQUINAS = {
	Vector3.new(1, 1, 1),
	Vector3.new(1, 1, -1),
	Vector3.new(1, -1, 1),
	Vector3.new(1, -1, -1),
	Vector3.new(-1, 1, 1),
	Vector3.new(-1, 1, -1),
	Vector3.new(-1, -1, 1),
	Vector3.new(-1, -1, -1),
}

local SIN_SOMBRA: { [string]: boolean } = {
	Helecho = true,
	HojasGrandes = true,
	Flores = true,
	Hierba = true,
	HierbaPlaya = true,
	ArbustoTropical = true,
	Conchas = true,
	Espuma = true,
	MaderaDeriva = true,
	Gaviota = true,
	RocaPequena = true,
	Charca = true,
	Pilote = true,
}

local function preparar(modelo: Model)
	local sombra = not SIN_SOMBRA[modelo.Name] and string.sub(modelo.Name, 1, 4) ~= "Vivo"
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = false
			d.CanCollide = false
			d.CanQuery = false
			d.CanTouch = false
			d.Massless = true
			if not sombra then
				d.CastShadow = false
			end
		elseif d:IsA("BaseScript") then
			d:Destroy()
		end
	end
end

local function fallar(nombre: string, motivo: string)
	warn(`[Overbooked] {motivo}`)
	fallidos[nombre] = true
	pendientes[nombre] = nil
end

local function cargar(nombre: string, id: number)
	local resultado: Model? = nil
	for intento = 1, 3 do
		local ok, r = pcall(function()
			return InsertService:LoadAsset(id)
		end)
		if ok and r then
			resultado = r
			break
		end
		if intento < 3 then
			task.wait(intento * 2)
		end
	end
	if not resultado then
		fallar(nombre, `No se pudo cargar el modelo {nombre} ({id})`)
		return
	end
	local modelo = Instance.new("Model")
	modelo.Name = nombre
	for _, hijo in resultado:GetChildren() do
		hijo.Parent = modelo
	end
	resultado:Destroy()
	local primera = modelo:FindFirstChildWhichIsA("BasePart", true)
	if not primera then
		fallar(nombre, `El modelo {nombre} no tiene piezas`)
		return
	end
	preparar(modelo)
	modelo.PrimaryPart = primera
	plantillas[nombre] = modelo
	local cola = pendientes[nombre]
	if cola then
		pendientes[nombre] = nil
		for _, f in cola do
			task.spawn(f, modelo)
		end
	end
end

local function cargarCielo(carpeta: Folder, nombre: string, id: number)
	cargar(nombre, id)
	local plantilla = plantillas[nombre]
	local parte = plantilla and plantilla:FindFirstChildWhichIsA("MeshPart", true)
	if not parte then
		return
	end
	local copia = parte:Clone()
	copia:PivotTo(Config.ROTACION_FBX)
	copia.Anchored = true
	copia.Name = nombre
	copia.Parent = carpeta
end

function Activos.iniciar()
	for nombre, id in Visuales.IDS do
		task.spawn(cargar, nombre, id)
	end
	local carpeta = Instance.new("Folder")
	carpeta.Name = Cielo.CARPETA
	carpeta.Parent = ReplicatedStorage
	for nombre, id in Cielo.IDS do
		task.spawn(cargarCielo, carpeta, nombre, id)
	end
	local intro = Instance.new("Folder")
	intro.Name = "ModelosIntro"
	intro.Parent = ReplicatedStorage
	for _, nombre in { "Maleta1", "Maleta2", "Maleta3", "Bolso" } do
		Activos.clonar(nombre, function(visual)
			visual.Parent = intro
		end)
	end
	local criaturas = Instance.new("Folder")
	criaturas.Name = Criaturas.CARPETA
	criaturas.Parent = ReplicatedStorage
	for nombre, id in Criaturas.IDS do
		Activos.registrar(nombre, id, Criaturas.CAJAS[nombre])
		Activos.clonar(nombre, function(visual)
			visual.Name = nombre
			visual.Parent = criaturas
		end)
	end
	local vivos = Instance.new("Folder")
	vivos.Name = "ModelosVivos"
	vivos.Parent = ReplicatedStorage
	for nombre, id in PasajerosVivos.IDS do
		Activos.registrar(nombre, id, PasajerosVivos.CAJAS[nombre])
		Activos.clonar(nombre, function(visual)
			visual.Name = nombre
			visual.Parent = vivos
		end)
	end
end

function Activos.cuando(nombre: string, f: (Model) -> ())
	local plantilla = plantillas[nombre]
	if plantilla then
		task.spawn(f, plantilla)
		return
	end
	if not (Visuales.IDS[nombre] or extras[nombre]) or fallidos[nombre] then
		return
	end
	local cola = pendientes[nombre] or {}
	pendientes[nombre] = cola
	table.insert(cola, f)
end

local function cajaEn(modelo: Model, base: CFrame): (Vector3, Vector3)
	local minimo = Vector3.one * math.huge
	local maximo = -Vector3.one * math.huge
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") then
			local cf, s = d.CFrame, d.Size / 2
			for _, signo in ESQUINAS do
				local p = base:PointToObjectSpace(cf:PointToWorldSpace(s * signo))
				minimo = minimo:Min(p)
				maximo = maximo:Max(p)
			end
		end
	end
	return minimo, maximo
end

local function colocar(visual: Model, base: CFrame, nombre: string, escala: number?)
	visual:PivotTo(base * Config.ROTACION_FBX)
	local esperada = Visuales.CAJAS[nombre] or extras[nombre]
	if not esperada then
		return
	end
	local e = escala or 1
	local minimo, maximo = cajaEn(visual, base)
	local medida = maximo - minimo
	local tamano = (esperada.maximo - esperada.minimo) * e
	local mayorV = math.max(medida.X, medida.Y, medida.Z)
	if mayorV > 1e-3 then
		visual:ScaleTo(visual:GetScale() * math.max(tamano.X, tamano.Y, tamano.Z) / mayorV)
		minimo, maximo = cajaEn(visual, base)
	end
	local desplazamiento = (esperada.minimo + esperada.maximo) / 2 * e - (minimo + maximo) / 2
	visual:PivotTo(visual:GetPivot() + base:VectorToWorldSpace(desplazamiento))
end

local function ocultar(parte: BasePart)
	parte.Transparency = 1
	for _, d in parte:GetDescendants() do
		if d:IsA("BasePart") then
			d.Transparency = 1
		elseif d:IsA("SurfaceGui") then
			d.Enabled = false
		end
	end
end

local function anclar(visual: Model)
	for _, d in visual:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true
		end
	end
end

function Activos.vestirFijo(marcador: BasePart, nombre: string, baseY: number?, escala: number?)
	Activos.cuando(nombre, function(plantilla)
		if not marcador.Parent then
			return
		end
		local visual = plantilla:Clone()
		local cf, s = marcador.CFrame, marcador.Size / 2
		local medioAlto = math.abs(cf.RightVector.Y) * s.X + math.abs(cf.UpVector.Y) * s.Y + math.abs(cf.LookVector.Y) * s.Z
		local y = baseY or (marcador.Position.Y - medioAlto)
		local frente = marcador.CFrame.LookVector * Vector3.new(1, 0, 1)
		local giro = if frente.Magnitude > 0.01 then CFrame.lookAt(Vector3.zero, frente) else CFrame.identity
		colocar(visual, CFrame.new(marcador.Position.X, y, marcador.Position.Z) * giro, nombre, escala)
		anclar(visual)
		ocultar(marcador)
		visual.Parent = marcador
	end)
end

function Activos.vestirDinamico(parte: BasePart, nombre: string, escala: number?)
	Activos.cuando(nombre, function(plantilla)
		if not parte.Parent then
			return
		end
		local visual = plantilla:Clone()
		colocar(visual, parte.CFrame * CFrame.new(0, -parte.Size.Y / 2, 0), nombre, escala)
		for _, hijo in parte:GetChildren() do
			if hijo:IsA("BasePart") then
				ocultar(hijo)
			end
		end
		for _, d in visual:GetDescendants() do
			if d:IsA("BasePart") then
				local soldadura = Instance.new("WeldConstraint")
				soldadura.Part0 = parte
				soldadura.Part1 = d
				soldadura.Parent = d
			end
		end
		visual.Parent = parte
		parte.Transparency = 1
	end)
end

function Activos.adjuntar(parte: BasePart, nombre: string, desplazamiento: CFrame, escala: number?, etiqueta: string?, valido: (() -> boolean)?)
	Activos.cuando(nombre, function(plantilla)
		local padre = parte.Parent
		if not padre or (valido and not valido()) then
			return
		end
		local nombreFinal = etiqueta or nombre
		for _, h in padre:GetChildren() do
			if h.Name == nombreFinal and h:IsA("Model") then
				h:Destroy()
			end
		end
		local visual = plantilla:Clone()
		visual.Name = nombreFinal
		colocar(visual, parte.CFrame * desplazamiento, nombre, escala)
		for _, d in visual:GetDescendants() do
			if d:IsA("BasePart") then
				d.Anchored = false
				d.Massless = true
				d.CanCollide = false
				d.CanQuery = false
				d.CanTouch = false
				local w = Instance.new("WeldConstraint")
				w.Part0 = parte
				w.Part1 = d
				w.Parent = d
			end
		end
		visual.Parent = padre
	end)
end

function Activos.vestirAvion(avion: Model)
	Activos.cuando("AvionExterior", function(plantilla)
		local visual = plantilla:Clone()
		colocar(visual, CFrame.identity, "AvionExterior")
		anclar(visual)
		visual.Parent = avion
		local exterior = avion:FindFirstChild("Exterior")
		if exterior then
			for _, d in exterior:GetDescendants() do
				if d:IsA("BasePart") and d.Parent == exterior and d:GetAttribute("Visual") == nil then
					d.Transparency = 1
				end
			end
		end
		avion:SetAttribute("CascoCargado", true)
	end)
end

function Activos.registrar(nombre: string, id: number, caja: Visuales.Caja)
	extras[nombre] = caja
	task.spawn(cargar, nombre, id)
end

function Activos.clonar(nombre: string, f: (Model) -> ())
	Activos.cuando(nombre, function(plantilla)
		local visual = plantilla:Clone()
		colocar(visual, CFrame.identity, nombre)
		anclar(visual)
		f(visual)
	end)
end

function Activos.tiene(nombre: string): boolean
	return if plantillas[nombre] then true else false
end

return Activos
