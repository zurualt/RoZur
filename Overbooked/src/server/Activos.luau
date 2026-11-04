--!strict
local InsertService = game:GetService("InsertService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)

local Activos = {}

local plantillas: { [string]: Model } = {}
local pendientes: { [string]: { (Model) -> () } } = {}

local ROTACIONES = {
	CFrame.identity,
	CFrame.Angles(-math.pi / 2, 0, 0),
	CFrame.Angles(math.pi / 2, 0, 0),
	CFrame.Angles(0, math.pi / 2, 0),
	CFrame.Angles(0, 0, math.pi / 2),
	CFrame.Angles(-math.pi / 2, 0, math.pi / 2),
}

local function caja(modelo: Model): (Vector3, Vector3)
	local minimo = Vector3.one * math.huge
	local maximo = -Vector3.one * math.huge
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") then
			local cf, s = d.CFrame, d.Size / 2
			for _, signo in { Vector3.new(1, 1, 1), Vector3.new(1, 1, -1), Vector3.new(1, -1, 1), Vector3.new(1, -1, -1), Vector3.new(-1, 1, 1), Vector3.new(-1, 1, -1), Vector3.new(-1, -1, 1), Vector3.new(-1, -1, -1) } do
				local p = cf:PointToWorldSpace(s * signo)
				minimo = minimo:Min(p)
				maximo = maximo:Max(p)
			end
		end
	end
	return minimo, maximo
end

local function forma(v: Vector3): Vector3
	local mayor = math.max(v.X, v.Y, v.Z, 1e-3)
	return v / mayor
end

local function orientar(modelo: Model, esperado: Vector3?): CFrame
	if not esperado then
		return Config.ROTACION_FBX
	end
	local objetivo = forma(esperado)
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

local function cargar(nombre: string, id: number)
	local ok, resultado = pcall(function()
		return InsertService:LoadAsset(id)
	end)
	if not ok or not resultado then
		warn(`[Overbooked] No se pudo cargar el modelo {nombre} ({id})`)
		return
	end
	local modelo = Instance.new("Model")
	modelo.Name = nombre
	for _, hijo in resultado:GetChildren() do
		hijo.Parent = modelo
	end
	resultado:Destroy()
	if not modelo:FindFirstChildWhichIsA("BasePart", true) then
		warn(`[Overbooked] El modelo {nombre} no tiene piezas`)
		return
	end
	preparar(modelo)
	if not modelo.PrimaryPart then
		modelo.PrimaryPart = modelo:FindFirstChildWhichIsA("BasePart", true)
	end
	modelo:SetAttribute("Rotacion", orientar(modelo, Config.TAMANOS[nombre]))
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
	for nombre, id in Config.VISUALES do
		task.spawn(cargar, nombre, id)
	end
end

function Activos.cuando(nombre: string, f: (Model) -> ())
	local plantilla = plantillas[nombre]
	if plantilla then
		task.spawn(f, plantilla)
		return
	end
	if not Config.VISUALES[nombre] then
		return
	end
	local cola = pendientes[nombre] or {}
	pendientes[nombre] = cola
	table.insert(cola, f)
end

local function colocar(visual: Model, base: CFrame, esperado: Vector3?)
	local r = visual:GetAttribute("Rotacion")
	local giro = if typeof(r) == "CFrame" then r else Config.ROTACION_FBX
	visual:PivotTo(base * giro)
	local minimo, maximo = caja(visual)
	local medida = maximo - minimo
	if esperado then
		local mayorV = math.max(medida.X, medida.Y, medida.Z)
		local mayorE = math.max(esperado.X, esperado.Y, esperado.Z)
		if mayorV > 1e-3 then
			visual:ScaleTo(visual:GetScale() * mayorE / mayorV)
		end
		minimo, maximo = caja(visual)
	end
	local fondo = Vector3.new((minimo.X + maximo.X) / 2, minimo.Y, (minimo.Z + maximo.Z) / 2)
	visual:PivotTo(visual:GetPivot() + (base.Position - fondo))
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

function Activos.vestirFijo(marcador: BasePart, nombre: string, baseY: number?)
	Activos.cuando(nombre, function(plantilla)
		if not marcador.Parent then
			return
		end
		local visual = plantilla:Clone()
		local y = baseY or (marcador.Position.Y - marcador.Size.Y / 2)
		local orientacion = marcador.CFrame - marcador.Position
		colocar(visual, CFrame.new(marcador.Position.X, y, marcador.Position.Z) * orientacion, Config.TAMANOS[nombre])
		for _, d in visual:GetDescendants() do
			if d:IsA("BasePart") then
				d.Anchored = true
			end
		end
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
		colocar(visual, parte.CFrame * CFrame.new(0, -parte.Size.Y / 2, 0), Config.TAMANOS[nombre])
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
		local minimoE, maximoE = Config.CAJA_AVION.minimo, Config.CAJA_AVION.maximo
		colocar(visual, CFrame.new((minimoE.X + maximoE.X) / 2, minimoE.Y, (minimoE.Z + maximoE.Z) / 2), maximoE - minimoE)
		for _, d in visual:GetDescendants() do
			if d:IsA("BasePart") then
				d.Anchored = true
			end
		end
		visual.Parent = avion
	end)
end

function Activos.tiene(nombre: string): boolean
	return if plantillas[nombre] then true else false
end

function Activos.clonar(nombre: string): Model?
	local plantilla = plantillas[nombre]
	return if plantilla then plantilla:Clone() else nil
end

function Activos.colocar(visual: Model, base: CFrame, nombre: string)
	colocar(visual, base, Config.TAMANOS[nombre])
end

return Activos
