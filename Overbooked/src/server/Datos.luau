--!strict
local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")

type Perfil = {
	Dinero: number,
	Vuelos: number,
	Mejor: number,
}

local Datos = {}

local VERSION = 1
local CADUCIDAD_SESION = 300

local almacen: DataStore? = nil
local perfiles: { [Player]: Perfil } = {}
local cargados: { [Player]: boolean } = {}
local sesion = if game.JobId ~= "" then game.JobId else "estudio"

local function numero(t: { [string]: any }, clave: string): number
	local v = t[clave]
	return if typeof(v) == "number" and v == v then v else 0
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

local function bloqueada(guardado: any): boolean
	if typeof(guardado) ~= "table" then
		return false
	end
	local s = guardado.Sesion
	if typeof(s) ~= "table" or typeof(s.Job) ~= "string" or typeof(s.Hora) ~= "number" then
		return false
	end
	return s.Job ~= sesion and os.time() - s.Hora < CADUCIDAD_SESION
end

local function cargar(jugador: Player)
	local perfil: Perfil = { Dinero = 0, Vuelos = 0, Mejor = 0 }
	local tienda = almacen
	if tienda then
		local clave = "j_" .. jugador.UserId
		for intento = 1, 6 do
			if not jugador.Parent then
				return
			end
			local forzar = intento == 6
			local ocupada = false
			local ok, guardado = pcall(function()
				return tienda:UpdateAsync(clave, function(anterior: any)
					if bloqueada(anterior) and not forzar then
						ocupada = true
						return nil
					end
					local t: { [string]: any } = if typeof(anterior) == "table" then anterior else {}
					t.Version = VERSION
					t.Sesion = { Job = sesion, Hora = os.time() }
					return t
				end)
			end)
			if ok and not ocupada then
				if not jugador.Parent then
					return
				end
				cargados[jugador] = true
				if typeof(guardado) == "table" then
					local t = guardado :: { [string]: any }
					perfil.Dinero = numero(t, "Dinero")
					perfil.Vuelos = numero(t, "Vuelos")
					perfil.Mejor = numero(t, "Mejor")
				end
				break
			end
			task.wait(if ok then 3 else intento)
		end
	end
	if jugador.Parent then
		perfiles[jugador] = perfil
		marcador(jugador, perfil)
	end
end

local function guardar(jugador: Player, liberar: boolean)
	local perfil = perfiles[jugador]
	local tienda = almacen
	if not perfil or not tienda or not cargados[jugador] then
		return
	end
	local copia = table.clone(perfil)
	for intento = 1, 4 do
		local ok = pcall(function()
			tienda:UpdateAsync("j_" .. jugador.UserId, function(anterior: any)
				if bloqueada(anterior) then
					return nil
				end
				return {
					Version = VERSION,
					Dinero = copia.Dinero,
					Vuelos = copia.Vuelos,
					Mejor = copia.Mejor,
					Sesion = if liberar then nil else { Job = sesion, Hora = os.time() },
				}
			end)
		end)
		if ok then
			return
		end
		task.wait(intento)
	end
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
		guardar(jugador, true)
		perfiles[jugador] = nil
		cargados[jugador] = nil
	end)
	game:BindToClose(function()
		local hilos = 0
		for _, jugador in Players:GetPlayers() do
			hilos += 1
			task.spawn(function()
				guardar(jugador, true)
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
				task.spawn(guardar, jugador, false)
			end
		end
	end)
end

return Datos
