--!strict
local InsertService = game:GetService("InsertService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)
local Visuales = require(ReplicatedStorage.Shared.Visuales)

local Activos = {}

local plantillas: { [string]: Model } = {}
local pendientes: { [string]: { (Model) -> () } } = {}
local fallidos: { [string]: boolean } = {}

local ROTACIONES = {
	CFrame.identity,
	CFrame.Angles(-math.pi / 2, 0, 0),
	CFrame.Angles(math.pi / 2, 0, 0),
	CFrame.Angles(0, math.pi / 2, 0),
	CFrame.Angles(0, 0, math.pi / 2),
	CFrame.Angles(-math.pi / 2, 0, math.pi / 2),
}

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

local function caja(modelo: Model): (Vector3, Vector3)
	local minimo = Vector3.one * math.huge
	local maximo = -Vector3.one * math.huge
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") then
			local cf, s = d.CFrame, d.Size / 2
			for _, signo in ESQUINAS do
				local p = cf:PointToWorldSpace(s * signo)
				minimo = minimo:Min(p)
				maximo = maximo:Max(p)
			end
		end
	end
	return minimo, maximo
end

local function forma(v: Vector3): Vector3
	return v / math.max(v.X, v.Y, v.Z, 1e-3)
end

local function orientar(modelo: Model, nombre: string): CFrame
	local esperada = Visuales.CAJAS[nombre]
	if not esperada then
		return Config.ROTACION_FBX
	end
	local objetivo = forma(esperada.maximo - esperada.minimo)
	local mejor, error = Config.ROTACION_FBX, math.huge
	for _, r in ROTACIONES do
		modelo:PivotTo(r)
		local minimo, maximo = caja(modelo)
		local d = forma(maximo - minimo) - objetivo
		local e = math.abs(d.X) + math.abs(d.Y) + math.abs(d.Z)
		if e < error - 0.02 then
			mejor, error = r, e
		end
	end
	modelo:PivotTo(CFrame.identity)
	return mejor
end

local function preparar(modelo: Model)
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = false
			d.CanCollide = false
			d.CanQuery = false
			d.CanTouch = false
			d.Massless = true
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
		task.wait(intento * 2)
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
	modelo:SetAttribute("Rotacion", orientar(modelo, nombre))
	plantillas[nombre] = modelo
	local cola = pendientes[nombre]
	if cola then
		pendientes[nombre] = nil
		for _, f in cola do
			task.spawn(f, modelo)
		end
	end
end

function Activos.iniciar()
	for nombre, id in Visuales.IDS do
		task.spawn(cargar, nombre, id)
	end
end

function Activos.cuando(nombre: string, f: (Model) -> ())
	local plantilla = plantillas[nombre]
	if plantilla then
		task.spawn(f, plantilla)
		return
	end
	if not Visuales.IDS[nombre] or fallidos[nombre] then
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

local function colocar(visual: Model, base: CFrame, nombre: string)
	local r = visual:GetAttribute("Rotacion")
	local giro = if typeof(r) == "CFrame" then r else Config.ROTACION_FBX
	visual:PivotTo(base * giro)
	local esperada = Visuales.CAJAS[nombre]
	if not esperada then
		return
	end
	local minimo, maximo = cajaEn(visual, base)
	local medida = maximo - minimo
	local tamano = esperada.maximo - esperada.minimo
	local mayorV = math.max(medida.X, medida.Y, medida.Z)
	if mayorV > 1e-3 then
		visual:ScaleTo(visual:GetScale() * math.max(tamano.X, tamano.Y, tamano.Z) / mayorV)
		minimo, maximo = cajaEn(visual, base)
	end
	local desplazamiento = (esperada.minimo + esperada.maximo) / 2 - (minimo + maximo) / 2
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

function Activos.vestirFijo(marcador: BasePart, nombre: string, baseY: number?)
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
		colocar(visual, CFrame.new(marcador.Position.X, y, marcador.Position.Z) * giro, nombre)
		anclar(visual)
		ocultar(marcador)
		visual.Parent = marcador
	end)
end

function Activos.vestirDinamico(parte: BasePart, nombre: string)
	Activos.cuando(nombre, function(plantilla)
		if not parte.Parent then
			return
		end
		local visual = plantilla:Clone()
		colocar(visual, parte.CFrame * CFrame.new(0, -parte.Size.Y / 2, 0), nombre)
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

function Activos.vestirAvion(avion: Model)
	Activos.cuando("AvionExterior", function(plantilla)
		local visual = plantilla:Clone()
		colocar(visual, CFrame.identity, "AvionExterior")
		anclar(visual)
		visual.Parent = avion
		local exterior = avion:FindFirstChild("Exterior")
		if exterior then
			for _, d in exterior:GetDescendants() do
				if d:IsA("BasePart") and d.Name ~= "Torreta" and not d:FindFirstAncestor("Torreta") and not (d.Parent and d.Parent.Name == "Tren") then
					d.Transparency = 1
				end
			end
		end
		avion:SetAttribute("CascoCargado", true)
	end)
end

function Activos.tiene(nombre: string): boolean
	return if plantillas[nombre] then true else false
end

return Activos
