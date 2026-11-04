local HttpService = game:GetService("HttpService")
local InsertService = game:GetService("InsertService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterPlayer = game:GetService("StarterPlayer")
local LogService = game:GetService("LogService")
local RunService = game:GetService("RunService")

local informe: { [string]: any } = { arranque = {}, registros = {} }

if not RunService:IsRunning() then
	local carpeta = game:GetService("ServerScriptService"):FindFirstChild("Server")
	local orden = { "Activos", "Estadisticas", "Datos", "Personajes", "Agarre", "Objetos", "Avion", "Pasajeros", "Carga", "Piratas", "Peligros", "Interacciones", "Cabina", "Vehiculos", "Aduana", "Tienda", "Partida" }
	local modulos = {}
	for _, nombre in orden do
		local ok, m = pcall(require, (carpeta :: Instance):FindFirstChild(nombre) :: ModuleScript)
		if ok then
			modulos[nombre] = m
		else
			informe.arranque[nombre] = "require: " .. tostring(m)
		end
	end
	for _, nombre in orden do
		local m = modulos[nombre]
		if m then
			local ok, e = pcall(m.iniciar)
			if not ok then
				informe.arranque[nombre] = tostring(e)
			end
		end
	end
end

task.wait(25)

for _, m in LogService:GetLogHistory() do
	if m.messageType == Enum.MessageType.MessageWarning or m.messageType == Enum.MessageType.MessageError then
		table.insert(informe.registros, string.sub(m.message, 1, 300))
	end
end

local function arbol(instancia: Instance, profundidad: number): { any }
	local lista = {}
	for _, hijo in instancia:GetChildren() do
		local nodo: { [string]: any } = { clase = hijo.ClassName, nombre = hijo.Name }
		if profundidad > 0 then
			nodo.hijos = arbol(hijo, profundidad - 1)
		end
		table.insert(lista, nodo)
	end
	return lista
end

local ok, tripulante = pcall(function()
	return InsertService:LoadAsset(87418247604950)
end)
if ok and tripulante then
	local humanoide = tripulante:FindFirstChildWhichIsA("Humanoid", true)
	informe.tripulante = {
		arbol = arbol(tripulante, 3),
		humanoide = humanoide ~= nil,
		raiz = tripulante:FindFirstChild("HumanoidRootPart", true) ~= nil,
		bocaSup = tripulante:FindFirstChild("BocaSup", true) ~= nil,
		bocaInf = tripulante:FindFirstChild("BocaInf", true) ~= nil,
		motores = #(function()
			local m = {}
			for _, d in tripulante:GetDescendants() do
				if d:IsA("Motor6D") then
					table.insert(m, d.Name)
				end
			end
			return m
		end)(),
		altura = if humanoide and humanoide.Parent and humanoide.Parent:IsA("Model") then humanoide.Parent:GetExtentsSize().Y else 0,
	}
else
	informe.tripulante = { error = tostring(tripulante) }
end

local plantilla = StarterPlayer:FindFirstChild("StarterCharacter")
informe.starterCharacter = plantilla ~= nil

local avion = workspace:FindFirstChild("Avion")
if avion then
	informe.cascoCargado = avion:GetAttribute("CascoCargado") == true
	local vestidos, marcadores = 0, 0
	for _, d in avion:GetDescendants() do
		if d:IsA("BasePart") and typeof(d:GetAttribute("Visual")) == "string" then
			marcadores += 1
			if d:FindFirstChildWhichIsA("Model") then
				vestidos += 1
			end
		end
	end
	informe.marcadores = marcadores
	informe.vestidos = vestidos
	informe.faseAvion = avion:GetAttribute("Fase")
end
local estado = ReplicatedStorage:FindFirstChild("Estado")
informe.fasePartida = if estado then estado:GetAttribute("Fase") else nil
informe.contratos = if estado then estado:GetAttribute("Contratos") ~= nil else false

local aeropuerto = workspace:FindFirstChild("Aeropuerto")
if aeropuerto then
	local vestidos, marcadores = 0, 0
	for _, d in aeropuerto:GetDescendants() do
		if d:IsA("BasePart") and typeof(d:GetAttribute("Visual")) == "string" then
			marcadores += 1
			if d:FindFirstChildWhichIsA("Model") then
				vestidos += 1
			end
		end
	end
	informe.aeropuerto = { marcadores = marcadores, vestidos = vestidos }
	local tractor = aeropuerto:FindFirstChild("Tractor", true)
	local carro = aeropuerto:FindFirstChild("CarroEquipaje", true)
	informe.vehiculos = {
		tractor = tractor ~= nil and tractor:IsA("BasePart") and not tractor.Anchored,
		asiento = tractor ~= nil and tractor:FindFirstChildOfClass("VehicleSeat") ~= nil,
		carro = carro ~= nil and carro:IsA("BasePart") and not carro.Anchored,
		aviso = carro ~= nil and carro:FindFirstChildOfClass("ProximityPrompt") ~= nil,
	}
	local cinta = aeropuerto:FindFirstChild("Cinta", true)
	informe.aduana = {
		cinta = if cinta and cinta:IsA("BasePart") then tostring(cinta.AssemblyLinearVelocity) else "falta",
		tunel = aeropuerto:FindFirstChild("Tunel", true) ~= nil,
		contenedor = aeropuerto:FindFirstChild("ZonaContenedor", true) ~= nil,
	}
	local tienda = aeropuerto:FindFirstChild("Tienda", true)
	informe.tienda = tienda ~= nil and tienda:FindFirstChildOfClass("ProximityPrompt") ~= nil
end
if avion then
	local casco = avion:FindFirstChild("Casco")
	informe.casco = if casco then #casco:GetChildren() else 0
	local altillos = 0
	for _, d in avion:GetDescendants() do
		if d.Name == "PuertaAltillo" and d:FindFirstChildOfClass("ProximityPrompt") then
			altillos += 1
		end
	end
	informe.altillos = altillos
end
local remotos = ReplicatedStorage:FindFirstChild("Remotos")
informe.remotos = {}
if remotos then
	for _, r in remotos:GetChildren() do
		table.insert(informe.remotos, r.Name)
	end
end
local okAudio, Audio = pcall(require, ReplicatedStorage.Shared.Audio)
informe.sonidos = 0
if okAudio then
	for _ in Audio.IDS do
		informe.sonidos += 1
	end
end
local servidor = game:GetService("ServerScriptService"):FindFirstChild("Server")
if servidor then
	local okP, Peligros = pcall(require, servidor:FindFirstChild("Peligros"))
	local CollectionService = game:GetService("CollectionService")
	if okP then
		local antes = #CollectionService:GetTagged("Fuego")
		Peligros.fuego(Vector3.new(0, 100.2, -30))
		local con = #CollectionService:GetTagged("Fuego")
		local mojado = Peligros.mojar(Vector3.new(0, 100.2, -30), 2, 200)
		task.wait(0.2)
		informe.fuego = { antes = antes, creado = con, mojado = mojado, despues = #CollectionService:GetTagged("Fuego") }
	else
		informe.fuego = { error = tostring(Peligros) }
	end
end

print(HttpService:JSONEncode(informe))
return HttpService:JSONEncode(informe)
