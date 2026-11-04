--!strict
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

type Perfil = {
	Dinero: number,
	Vuelos: number,
	Mejor: number,
}

local Datos = {}

local almacen: DataStore? = nil
local perfiles: { [Player]: Perfil } = {}
local cargados: { [Player]: boolean } = {}

local function reintentar<T>(f: () -> T): (boolean, T?)
	for intento = 1, 4 do
		local ok, resultado = pcall(f)
		if ok then
			return true, resultado
		end
		task.wait(intento)
	end
	return false, nil
end

local function valor(carpeta: Instance, nombre: string, v: number)
	local existente = carpeta:FindFirstChild(nombre)
	if existente and existente:IsA("IntValue") then
		existente.Value = v
		return
	end
	local nuevo = Instance.new("IntValue")
	nuevo.Name = nombre
	nuevo.Value = v
	nuevo.Parent = carpeta
end

local function marcador(jugador: Player, perfil: Perfil)
	local carpeta = jugador:FindFirstChild("leaderstats")
	if not carpeta then
		local nueva = Instance.new("Folder")
		nueva.Name = "leaderstats"
		nueva.Parent = jugador
		carpeta = nueva
	end
	if carpeta then
		valor(carpeta, "Dinero", perfil.Dinero)
		valor(carpeta, "Vuelos", perfil.Vuelos)
	end
end

local function cargar(jugador: Player)
	local perfil: Perfil = { Dinero = 0, Vuelos = 0, Mejor = 0 }
	local tienda = almacen
	if tienda then
		local ok, guardado = reintentar(function()
			return tienda:GetAsync("j_" .. jugador.UserId)
		end)
		if ok and jugador.Parent then
			cargados[jugador] = true
			if typeof(guardado) == "table" then
				local t = guardado :: { [string]: any }
				perfil.Dinero = if typeof(t.Dinero) == "number" then t.Dinero else 0
				perfil.Vuelos = if typeof(t.Vuelos) == "number" then t.Vuelos else 0
				perfil.Mejor = if typeof(t.Mejor) == "number" then t.Mejor else 0
			end
		end
	end
	if jugador.Parent then
		perfiles[jugador] = perfil
		marcador(jugador, perfil)
	end
end

local function guardar(jugador: Player)
	local perfil = perfiles[jugador]
	local tienda = almacen
	if not perfil or not tienda or not cargados[jugador] then
		return
	end
	local copia = table.clone(perfil)
	reintentar(function()
		return tienda:UpdateAsync("j_" .. jugador.UserId, function()
			return copia
		end)
	end)
end

function Datos.sumar(jugador: Player, dinero: number, vuelo: boolean)
	local perfil = perfiles[jugador]
	if not perfil then
		return
	end
	perfil.Dinero = math.max(0, perfil.Dinero + math.floor(dinero))
	if vuelo then
		perfil.Vuelos += 1
	end
	perfil.Mejor = math.max(perfil.Mejor, math.floor(dinero))
	marcador(jugador, perfil)
end

function Datos.dinero(jugador: Player): number
	local perfil = perfiles[jugador]
	return if perfil then perfil.Dinero else 0
end

function Datos.iniciar()
	local ok, tienda = pcall(function()
		return DataStoreService:GetDataStore("Overbooked_v1")
	end)
	if ok then
		almacen = tienda
	else
		warn("[Overbooked] DataStore no disponible; el dinero no se guardará")
	end
	for _, jugador in Players:GetPlayers() do
		task.spawn(cargar, jugador)
	end
	Players.PlayerAdded:Connect(cargar)
	Players.PlayerRemoving:Connect(function(jugador)
		guardar(jugador)
		perfiles[jugador] = nil
		cargados[jugador] = nil
	end)
	game:BindToClose(function()
		local hilos = 0
		for _, jugador in Players:GetPlayers() do
			hilos += 1
			task.spawn(function()
				guardar(jugador)
				hilos -= 1
			end)
		end
		local limite = os.clock() + 25
		while hilos > 0 and os.clock() < limite do
			task.wait(0.2)
		end
	end)
	task.spawn(function()
		while true do
			task.wait(120)
			for _, jugador in Players:GetPlayers() do
				task.spawn(guardar, jugador)
			end
		end
	end)
end

return Datos
