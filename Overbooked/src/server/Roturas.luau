--!strict
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Audio = require(ReplicatedStorage.Shared.Audio)
local Piezas = require(ReplicatedStorage.Shared.PiezasRoturas)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Activos = require(script.Parent.Activos)
local Avion = require(script.Parent.Avion)
local Pasajeros = require(script.Parent.Pasajeros)
local Peligros = require(script.Parent.Peligros)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder

local Roturas = {}

local DURACION_PARTIDO = 4.6
local PAUSA = 6
local LADOS = { "Izq", "Der" }
local GONDOLAS = { Izq = CFrame.new(-18, 96, -24.5), Der = CFrame.new(18, 96, -24.5) }
local PRESTADOS = { "Inodoro", "Maleta1", "Maleta2", "Maleta3", "Bolso" }
local PIVOTE_COLA = Vector3.new(0, 96.25, Piezas.CORTE)
local HUNDIDA = CFrame.new(PIVOTE_COLA + Vector3.new(0, -0.3, 0.8)) * CFrame.Angles(math.rad(5), 0, 0) * CFrame.new(-PIVOTE_COLA)

local avion = Workspace:WaitForChild("Avion") :: Model
local exterior = avion:WaitForChild("Exterior") :: Folder
local rng = Random.new()

local remoto = Instance.new("RemoteEvent")
remoto.Name = "Rotura"
remoto.Parent = Remotos
local plantillas = Instance.new("Folder")
plantillas.Name = "Roturas"
plantillas.Parent = ReplicatedStorage
local carpeta = Instance.new("Folder")
carpeta.Name = "Roturas"
carpeta.Parent = avion

local hechos: { [string]: boolean } = {}
local ocultos: { [BasePart]: { transparencia: number, colision: boolean } } = {}
local apagados: { [Light]: boolean } = {}
local movidos: { [BasePart]: { cf: CFrame, tam: Vector3 } } = {}
local libre = 0
local finPartido = 0

local function aviso(texto: string)
	RemotoAviso:FireAllClients(texto, "peligro")
end

local function ocultar(raiz: Instance)
	local lista = raiz:GetDescendants()
	table.insert(lista, raiz)
	for _, d in lista do
		if d:IsA("BasePart") and not ocultos[d] then
			ocultos[d] = { transparencia = d.Transparency, colision = d.CanCollide }
			d.Transparency = 1
			d.CanCollide = false
		elseif d:IsA("Light") and d.Enabled then
			apagados[d] = true
			d.Enabled = false
		end
	end
end

local function mover(parte: BasePart, tam: Vector3, cf: CFrame)
	movidos[parte] = movidos[parte] or { cf = parte.CFrame, tam = parte.Size }
	parte.Size = tam
	parte.CFrame = cf
end

local function poner(nombre: string, como: string, marco: CFrame?): Model?
	local plantilla = plantillas:FindFirstChild(nombre)
	if not plantilla or not plantilla:IsA("Model") then
		return nil
	end
	local m = plantilla:Clone()
	m.Name = como
	if marco then
		m:PivotTo(marco * m:GetPivot())
	end
	m.Parent = carpeta
	return m
end

local function quitar(nombre: string)
	local m = carpeta:FindFirstChild(nombre)
	if m then
		m:Destroy()
	end
end

local function sacudir(magnitud: number)
	Peligros.sacudida(magnitud)
	Pasajeros.asustar(magnitud * 0.8)
	libre = os.clock() + PAUSA
end

local function desglosar(): boolean
	if carpeta:FindFirstChild("Base") then
		return true
	end
	for _, n in { "RotBase", "RotPuntaIzq", "RotPuntaDer", "RotCola", "RotDeriva" } do
		if not plantillas:FindFirstChild(n) then
			return false
		end
	end
	local casco = avion:FindFirstChild("AvionExterior")
	if casco then
		ocultar(casco)
	end
	poner("RotBase", "Base")
	poner("RotPuntaIzq", "PuntaIzq")
	poner("RotPuntaDer", "PuntaDer")
	for _, n in { "Cola", "Deriva" } do
		local m = poner("Rot" .. n, n)
		if m then
			m:SetAttribute("Detras", true)
		end
	end
	return true
end

local function enVuelo(): boolean
	local fase = Avion.fase()
	return fase == "Vuelo" or fase == "Aproximacion"
end

local function ala(lado: string)
	if not desglosar() then
		return
	end
	hechos.Ala = true
	hechos["Ala" .. lado] = true
	local s = if lado == "Izq" then -1 else 1
	quitar("Punta" .. lado)
	poner("RotBordeAla" .. lado, "BordeAla" .. lado)
	local parte = exterior:FindFirstChild("Ala" .. lado)
	if parte and parte:IsA("BasePart") then
		mover(parte, Vector3.new(20, parte.Size.Y, parte.Size.Z), CFrame.new(s * 17, parte.Position.Y, parte.Position.Z))
	end
	local punta = exterior:FindFirstChild("Punta" .. lado)
	if punta then
		ocultar(punta)
	end
	remoto:FireAllClients("Ala", lado)
	aviso("¡Se nos ha caído un trozo de ala! Tranquilos, era la parte decorativa")
	sacudir(0.75)
	if enVuelo() then
		Avion.estado.alabeo = math.clamp(Avion.estado.alabeo + s * 12, -45, 45)
	end
end

local function deriva()
	if not desglosar() then
		return
	end
	hechos.Deriva = true
	quitar("Deriva")
	local borde = poner("RotBordeDeriva", "BordeDeriva")
	if borde then
		borde:SetAttribute("Detras", true)
	end
	local parte = exterior:FindFirstChild("Deriva")
	if parte then
		ocultar(parte)
	end
	remoto:FireAllClients("Deriva")
	aviso("¡Hemos perdido la cola! El timón ahora es opcional")
	sacudir(0.8)
end

local function capo(lado: string)
	hechos.Capo = true
	hechos["Capo" .. lado] = true
	poner("RotMotorExpuesto", "Expuesto" .. lado, GONDOLAS[lado])
	remoto:FireAllClients("Capo", lado)
	aviso("¡El capó del motor se ha ido volando! Mejor no mirar dentro")
	sacudir(0.5)
end

local function techo()
	local z = Piezas.FILA_TECHO
	local plano: BasePart? = nil
	for _, d in avion:GetDescendants() do
		if not d:IsA("BasePart") or d:IsDescendantOf(carpeta) then
			continue
		end
		local cerca = math.abs(d.Position.Z - z)
		if d.Name == "Techo" and d.Size.Z > 40 then
			plano = d
		elseif (d.Name == "Techo" or d.Name == "LuzFila") and cerca < 1 then
			ocultar(d)
		elseif d.Name == "PuertaAltillo" and cerca < 2.3 then
			ocultar(d)
		end
	end
	if plano then
		ocultar(plano)
		local z0, z1 = plano.Position.Z - plano.Size.Z / 2, plano.Position.Z + plano.Size.Z / 2
		for _, tramo in { { z0, z - 2.25 }, { z + 2.25, z1 } } do
			local p = plano:Clone()
			p:ClearAllChildren()
			p.Name = "TechoParte"
			p.Size = Vector3.new(plano.Size.X, plano.Size.Y, tramo[2] - tramo[1])
			p.CFrame = CFrame.new(plano.Position.X, plano.Position.Y, (tramo[1] + tramo[2]) / 2)
			p.Transparency = 0
			p.CanCollide = true
			p.Parent = carpeta
		end
	end
	hechos.Techo = true
	poner("RotTechoRoto", "TechoRoto")
	poner("RotBordeTecho", "BordeTecho")
	local soporte = Instance.new("Part")
	soporte.Name = "VientoTecho"
	soporte.Anchored = true
	soporte.CanCollide = false
	soporte.CanQuery = false
	soporte.CanTouch = false
	soporte.Transparency = 1
	soporte.Size = Vector3.new(8, 0.2, 3.5)
	soporte.CFrame = CFrame.lookAt(Vector3.new(0, 109.5, z), Vector3.new(0, 120, z + 4))
	VFX.viento(soporte).Rate = 70
	local id = Audio.IDS.VientoExterior
	if id then
		local s = Instance.new("Sound")
		s.SoundId = `rbxassetid://{id}`
		s.Looped = true
		s.Volume = 0.9
		s.RollOffMode = Enum.RollOffMode.InverseTapered
		s.RollOffMinDistance = 8
		s.RollOffMaxDistance = 70
		s.Parent = soporte
		s:Play()
	end
	soporte.Parent = carpeta
	remoto:FireAllClients("Techo")
	aviso("¡Se ha volado el techo! Ahora somos un descapotable")
	sacudir(0.85)
end

local function hundirCola()
	if finPartido == 0 then
		return
	end
	for _, m in carpeta:GetChildren() do
		if m:IsA("Model") and m:GetAttribute("Detras") then
			m:PivotTo(HUNDIDA * m:GetPivot())
		end
	end
end

local function partir()
	if hechos.Partido or not desglosar() then
		return
	end
	hechos.Partido = true
	poner("RotBordeCola", "BordeColaDelante")
	local detras = poner("RotBordeCola", "BordeColaDetras")
	if detras then
		detras:SetAttribute("Detras", true)
	end
	finPartido = os.clock() + DURACION_PARTIDO
	remoto:FireAllClients("Partido")
	aviso("¡EL AVIÓN SE HA PARTIDO EN EL AIRE! La parte de atrás va por libre")
	sacudir(1)
	task.delay(DURACION_PARTIDO, hundirCola)
end

local function restaurar()
	finPartido = 0
	table.clear(hechos)
	carpeta:ClearAllChildren()
	for p, d in ocultos do
		p.Transparency = d.transparencia
		p.CanCollide = d.colision
	end
	table.clear(ocultos)
	for l in apagados do
		l.Enabled = true
	end
	table.clear(apagados)
	for p, d in movidos do
		p.Size = d.tam
		p.CFrame = d.cf
	end
	table.clear(movidos)
	remoto:FireAllClients("Restaurar")
end

local function revisar()
	if not enVuelo() or os.clock() < libre then
		return
	end
	for _, lado in LADOS do
		if not hechos["Capo" .. lado] and avion:GetAttribute("Motor" .. lado .. "Fuego") == true then
			capo(lado)
			return
		end
	end
	local casco = Avion.estado.casco
	if casco <= 65 and not hechos.Ala then
		ala(LADOS[rng:NextInteger(1, 2)])
	elseif casco <= 40 and not hechos.Deriva then
		deriva()
	elseif casco <= 20 and not hechos.Techo then
		techo()
	end
end

local PRUEBAS: { [string]: () -> () } = {
	Ala = function()
		ala(LADOS[rng:NextInteger(1, 2)])
	end,
	AlaIzq = function()
		ala("Izq")
	end,
	AlaDer = function()
		ala("Der")
	end,
	Capo = function()
		capo(LADOS[rng:NextInteger(1, 2)])
	end,
	CapoIzq = function()
		capo("Izq")
	end,
	CapoDer = function()
		capo("Der")
	end,
	Deriva = deriva,
	Techo = techo,
	Partido = partir,
	Reparar = restaurar,
}

local SECUENCIA = { { n = "CapoIzq", t = 0 }, { n = "AlaDer", t = 4 }, { n = "Deriva", t = 5 }, { n = "Techo", t = 5 }, { n = "Partido", t = 6 } }

local function probar(nombre: string)
	if nombre == "Todo" then
		restaurar()
		for _, paso in SECUENCIA do
			task.wait(paso.t)
			PRUEBAS[paso.n]()
		end
		return
	end
	local f = PRUEBAS[nombre]
	if not f then
		warn(`[Overbooked] PruebaRotura desconocida: {nombre}`)
		return
	end
	if hechos[nombre] then
		restaurar()
	end
	f()
end

function Roturas.esperar()
	while os.clock() < finPartido do
		task.wait(0.1)
	end
end

function Roturas.iniciar()
	for nombre, id in Piezas.IDS do
		local caja = Piezas.CAJAS[nombre]
		if caja then
			Activos.registrar(nombre, id, caja)
		end
	end
	local nombres = table.clone(PRESTADOS)
	for nombre in Piezas.IDS do
		table.insert(nombres, nombre)
	end
	for _, nombre in nombres do
		Activos.clonar(nombre, function(m)
			m.Name = nombre
			m.Parent = plantillas
		end)
	end
	Avion.alTerminar(function(tipo)
		if tipo == "Estrellado" and Avion.estado.casco <= 0 then
			partir()
		end
	end)
	Estado:GetAttributeChangedSignal("Fase"):Connect(function()
		local fase = Estado:GetAttribute("Fase")
		if fase == "Aeropuerto" or fase == "Embarque" then
			restaurar()
		end
	end)
	if RunService:IsStudio() then
		Workspace:GetAttributeChangedSignal("PruebaRotura"):Connect(function()
			local v = Workspace:GetAttribute("PruebaRotura")
			if typeof(v) == "string" and v ~= "" then
				Workspace:SetAttribute("PruebaRotura", nil)
				task.spawn(probar, v)
			end
		end)
	end
	task.spawn(function()
		while true do
			task.wait(0.25)
			revisar()
		end
	end)
end

return Roturas
