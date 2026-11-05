--!strict
local DataStoreService = game:GetService("DataStoreService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Config = require(ReplicatedStorage.Shared.Config)

type Perfil = {
	Dinero: number,
	Vuelos: number,
	Mejor: number,
	Gorros: { [string]: boolean },
	Gorro: string,
	Mejoras: { [string]: number },
	Ajustes: { [string]: any },
}

local Datos = {}

local VERSION = 2
local CADUCIDAD_SESION = 300

local almacen: DataStore? = nil
local perfiles: { [Player]: Perfil } = {}
local cargados: { [Player]: boolean } = {}
local tiendaCargada: { [Player]: boolean } = {}
local liberados: { [Player]: boolean } = {}
local sesion = if game.JobId ~= "" then game.JobId else "estudio"

local function numero(t: { [string]: any }, clave: string): number
	local v = t[clave]
	return if typeof(v) == "number" and v == v then v else 0
end

local function gorroValido(nombre: string): boolean
	for _, g in Config.TIENDA.GORROS do
		if g.nombre == nombre then
			return true
		end
	end
	return false
end

local function mejoraMaxima(nombre: string): number
	for _, m in Config.TIENDA.MEJORAS do
		if m.nombre == nombre then
			return #m.precios
		end
	end
	return 0
end

local function leerGorros(v: any): { [string]: boolean }
	local r: { [string]: boolean } = {}
	local n = 0
	if typeof(v) == "table" then
		for nombre, tiene in v do
			if typeof(nombre) == "string" and #nombre <= 40 and tiene == true and n < 64 then
				r[nombre] = true
				n += 1
			end
		end
	end
	return r
end

local function leerMejoras(v: any): { [string]: number }
	local r: { [string]: number } = {}
	if typeof(v) == "table" then
		for nombre, n in v do
			if typeof(nombre) == "string" and #nombre <= 40 and typeof(n) == "number" and n == n then
				r[nombre] = math.clamp(math.floor(n), 0, 10)
			end
		end
	end
	return r
end

local function leerAjustes(v: any): { [string]: any }
	local r: { [string]: any } = {}
	if typeof(v) ~= "table" then
		return r
	end
	local function numeroEn(clave: string, minimo: number, maximo: number)
		local n = v[clave]
		if typeof(n) == "number" and n == n then
			r[clave] = math.clamp(n, minimo, maximo)
		end
	end
	numeroEn("Fov", 60, 100)
	numeroEn("Musica", 0, 1)
	numeroEn("Efectos", 0, 1)
	if typeof(v.Tercera) == "boolean" then
		r.Tercera = v.Tercera
	end
	if typeof(v.Idioma) == "string" and string.match(v.Idioma, "^%a%a$") then
		r.Idioma = v.Idioma
	end
	return r
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
		valor(carpeta, "Cash", perfil.Dinero)
		valor(carpeta, "Flights", perfil.Vuelos)
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

local function nuestra(guardado: any): boolean
	if typeof(guardado) ~= "table" then
		return false
	end
	local s = guardado.Sesion
	return typeof(s) == "table" and s.Job == sesion
end

local function liberarSinPerfil(tienda: DataStore, clave: string)
	pcall(function()
		tienda:UpdateAsync(clave, function(anterior: any)
			if not nuestra(anterior) then
				return nil
			end
			anterior.Sesion = nil
			return anterior
		end)
	end)
end

local function futura(t: any): boolean
	return typeof(t) == "table" and typeof(t.Version) == "number" and t.Version > VERSION
end

local function leerTienda(perfil: Perfil, t: { [string]: any })
	perfil.Gorros = leerGorros(t.Gorros)
	perfil.Mejoras = leerMejoras(t.Mejoras)
	local g = t.Gorro
	perfil.Gorro = if typeof(g) == "string" and perfil.Gorros[g] then g else ""
end

local function cargar(jugador: Player)
	local perfil: Perfil = { Dinero = 0, Vuelos = 0, Mejor = 0, Gorros = {}, Gorro = "", Mejoras = {}, Ajustes = {} }
	local tienda = almacen
	if tienda then
		local clave = "j_" .. jugador.UserId
		local claveTienda = "t_" .. jugador.UserId
		for intento = 1, 13 do
			if not jugador.Parent then
				return
			end
			local forzar = intento == 13
			local ocupada = false
			local nueva = false
			local ok, guardado = pcall(function()
				return tienda:UpdateAsync(clave, function(anterior: any)
					if futura(anterior) then
						nueva = true
						return nil
					end
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
			if ok and nueva then
				warn("[Overbooked] Perfil guardado con una versión más nueva; esta sesión no guardará")
				break
			end
			if ok and not ocupada then
				if not jugador.Parent then
					liberarSinPerfil(tienda, clave)
					return
				end
				cargados[jugador] = true
				local t: { [string]: any } = if typeof(guardado) == "table" then guardado else {}
				perfil.Dinero = numero(t, "Dinero")
				perfil.Vuelos = numero(t, "Vuelos")
				perfil.Mejor = numero(t, "Mejor")
				perfil.Ajustes = leerAjustes(t.Ajustes)
				leerTienda(perfil, t)
				for intentoTienda = 1, 4 do
					local okT, datosTienda = pcall(function()
						return tienda:GetAsync(claveTienda)
					end)
					if okT then
						if typeof(datosTienda) == "table" then
							leerTienda(perfil, datosTienda)
						end
						tiendaCargada[jugador] = not futura(datosTienda)
						break
					end
					task.wait(intentoTienda)
				end
				break
			end
			task.wait(if ok then 5 else intento)
		end
	end
	if jugador.Parent then
		perfiles[jugador] = perfil
		marcador(jugador, perfil)
		jugador:SetAttribute("Ajustes", HttpService:JSONEncode(perfil.Ajustes))
	end
end

local function guardar(jugador: Player, liberar: boolean)
	local perfil = perfiles[jugador]
	local tienda = almacen
	if not perfil or not tienda or not cargados[jugador] then
		return
	end
	if liberados[jugador] and not liberar then
		return
	end
	local copia = table.clone(perfil)
	copia.Gorros = table.clone(perfil.Gorros)
	copia.Mejoras = table.clone(perfil.Mejoras)
	copia.Ajustes = table.clone(perfil.Ajustes)
	local escrito = false
	for intento = 1, 4 do
		local ok = pcall(function()
			tienda:UpdateAsync("j_" .. jugador.UserId, function(anterior: any)
				escrito = false
				if not nuestra(anterior) or futura(anterior) then
					return nil
				end
				local t = anterior :: { [string]: any }
				t.Version = VERSION
				t.Dinero = copia.Dinero
				t.Vuelos = copia.Vuelos
				t.Mejor = copia.Mejor
				t.Ajustes = copia.Ajustes
				t.Gorros = nil
				t.Gorro = nil
				t.Mejoras = nil
				t.Sesion = if liberar then nil else { Job = sesion, Hora = os.time() }
				escrito = true
				return t
			end)
		end)
		if ok then
			break
		end
		task.wait(intento)
	end
	if not escrito or not tiendaCargada[jugador] then
		return
	end
	for intento = 1, 4 do
		local ok = pcall(function()
			tienda:UpdateAsync("t_" .. jugador.UserId, function(anterior: any)
				if futura(anterior) then
					return nil
				end
				local t: { [string]: any } = if typeof(anterior) == "table" then anterior else {}
				t.Version = VERSION
				t.Gorros = copia.Gorros
				t.Gorro = copia.Gorro
				t.Mejoras = copia.Mejoras
				return t
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

function Datos.listo(jugador: Player): boolean
	return perfiles[jugador] ~= nil
end

function Datos.guardable(jugador: Player): boolean
	return cargados[jugador] == true and tiendaCargada[jugador] == true
end

function Datos.gastar(jugador: Player, cantidad: number): boolean
	local perfil = perfiles[jugador]
	if not perfil or cantidad < 0 or perfil.Dinero < cantidad then
		return false
	end
	perfil.Dinero -= cantidad
	marcador(jugador, perfil)
	return true
end

function Datos.gorros(jugador: Player): ({ [string]: boolean }, string)
	local perfil = perfiles[jugador]
	if not perfil then
		return {}, ""
	end
	return table.clone(perfil.Gorros), perfil.Gorro
end

function Datos.darGorro(jugador: Player, nombre: string)
	local perfil = perfiles[jugador]
	if perfil and gorroValido(nombre) then
		perfil.Gorros[nombre] = true
	end
end

function Datos.equipar(jugador: Player, nombre: string): boolean
	local perfil = perfiles[jugador]
	if not perfil or (nombre ~= "" and not perfil.Gorros[nombre]) then
		return false
	end
	perfil.Gorro = nombre
	return true
end

function Datos.mejoras(jugador: Player): { [string]: number }
	local perfil = perfiles[jugador]
	return if perfil then table.clone(perfil.Mejoras) else {}
end

function Datos.subirMejora(jugador: Player, nombre: string)
	local perfil = perfiles[jugador]
	if perfil then
		perfil.Mejoras[nombre] = math.min(mejoraMaxima(nombre), (perfil.Mejoras[nombre] or 0) + 1)
	end
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
	local esperaAjustes: { [Player]: number } = {}
	local RemotoAjustes = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Ajustes") :: RemoteEvent
	RemotoAjustes.OnServerEvent:Connect(function(jugador, datos)
		local perfil = perfiles[jugador]
		local ahora = os.clock()
		if not perfil or (esperaAjustes[jugador] or 0) > ahora then
			return
		end
		esperaAjustes[jugador] = ahora + 0.5
		perfil.Ajustes = leerAjustes(datos)
		jugador:SetAttribute("Ajustes", HttpService:JSONEncode(perfil.Ajustes))
	end)
	for _, jugador in Players:GetPlayers() do
		task.spawn(cargar, jugador)
	end
	Players.PlayerAdded:Connect(cargar)
	Players.PlayerRemoving:Connect(function(jugador)
		liberados[jugador] = true
		guardar(jugador, true)
		perfiles[jugador] = nil
		esperaAjustes[jugador] = nil
		cargados[jugador] = nil
		tiendaCargada[jugador] = nil
		liberados[jugador] = nil
	end)
	game:BindToClose(function()
		local hilos = 0
		for _, jugador in Players:GetPlayers() do
			hilos += 1
			liberados[jugador] = true
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
