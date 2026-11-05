--!strict
local DataStoreService = game:GetService("DataStoreService")
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(ReplicatedStorage.Shared.Config)
local Avion = require(script.Parent.Avion)
local Caos = require(script.Parent.Caos)
local Peligros = require(script.Parent.Peligros)
local Personajes = require(script.Parent.Personajes)
local Rafagas = require(script.Parent.Rafagas)
local Vidas = require(script.Parent.Vidas)

local R = Config.ROBUX
local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder

type Fichas = { [string]: number }

local Compras = {}

local almacen: DataStore? = nil
local fichas: { [Player]: Fichas } = {}
local objetivos: { [Player]: Player } = {}
local esperas: { [Player]: number } = {}
local ultimoCaos = -math.huge
local remoto: RemoteEvent

local function productoDe(nombre: string): number
	if nombre == "Revivir" then
		return R.REVIVIR
	end
	for _, e in R.CAOS do
		if e.nombre == nombre then
			return e.producto
		end
	end
	return 0
end

local function nombreDe(id: number): string?
	if id == 0 then
		return nil
	end
	if id == R.REVIVIR then
		return "Revivir"
	end
	for _, e in R.CAOS do
		if e.producto == id then
			return e.nombre
		end
	end
	return nil
end

local function tituloDe(nombre: string): string
	for _, e in R.CAOS do
		if e.nombre == nombre then
			return e.titulo
		end
	end
	return nombre
end

local function leer(v: any): Fichas
	local r: Fichas = {}
	if typeof(v) == "table" then
		for nombre, n in v do
			if typeof(nombre) == "string" and #nombre <= 20 and typeof(n) == "number" and n == n and n > 0 then
				r[nombre] = math.min(math.floor(n), 999)
			end
		end
	end
	return r
end

local function cambiar(userId: number, nombre: string, delta: number, recibo: string?): (boolean, Fichas?)
	local tienda = almacen
	if not tienda then
		return false, nil
	end
	local resultado: Fichas? = nil
	local ok = pcall(function()
		tienda:UpdateAsync("c_" .. userId, function(anterior: any)
			local t: { [string]: any } = if typeof(anterior) == "table" then anterior else {}
			local f = leer(t.Fichas)
			local recibos: { string } = if typeof(t.Recibos) == "table" then t.Recibos else {}
			resultado = f
			if recibo and table.find(recibos, recibo) then
				return nil
			end
			local n = (f[nombre] or 0) + delta
			if n < 0 then
				return nil
			end
			f[nombre] = n
			if recibo then
				table.insert(recibos, recibo)
				while #recibos > 60 do
					table.remove(recibos, 1)
				end
			end
			t.Fichas = f
			t.Recibos = recibos
			return t
		end)
	end)
	return ok, resultado
end

local function enviar(jugador: Player)
	remoto:FireClient(jugador, "fichas", fichas[jugador] or {})
end

local function avisar(jugador: Player, texto: string)
	RemotoAviso:FireClient(jugador, texto, "info")
end

local function motivoCaos(): string?
	if Estado:GetAttribute("Fase") ~= "Vuelo" or Avion.fase() ~= "Vuelo" then
		return "El caos de pago solo funciona en pleno vuelo"
	end
	if Peligros.calma() then
		return "Espera a que el avión termine de subir"
	end
	local quedan = ultimoCaos + R.ENFRIAMIENTO - os.clock()
	if quedan > 0 then
		return `Otro desastre podrá lanzarse en {math.ceil(quedan)} s`
	end
	return nil
end

local function lanzarCaos(jugador: Player, nombre: string): boolean
	if motivoCaos() then
		return false
	end
	if not (Caos.lanzar(nombre) or Peligros.lanzar(nombre)) then
		return false
	end
	ultimoCaos = os.clock()
	Caos.sumarBonus(R.BONUS_CAOS)
	remoto:FireAllClients("cartel", jugador.DisplayName, nombre)
	RemotoAviso:FireAllClients(`¡{jugador.DisplayName} ha pagado: {tituloDe(nombre)}!`, "peligro")
	local raiz = Personajes.raiz(jugador)
	if raiz then
		Rafagas.lanzar("Monedas", raiz.Position + Vector3.new(0, 3, 0), 1)
	end
	return true
end

local function usar(jugador: Player, nombre: string): boolean
	local f = fichas[jugador]
	if not f or (f[nombre] or 0) <= 0 then
		return false
	end
	local hecho = false
	if nombre == "Revivir" then
		local objetivo: Player? = objetivos[jugador]
		objetivos[jugador] = nil
		if not (objetivo and objetivo.Parent and Vidas.muerto(objetivo)) then
			objetivo = if Vidas.muerto(jugador) then jugador else nil
		end
		hecho = objetivo ~= nil and Vidas.revivir(objetivo, jugador)
	else
		hecho = lanzarCaos(jugador, nombre)
	end
	if hecho then
		f[nombre] -= 1
		task.spawn(cambiar, jugador.UserId, nombre, -1, nil)
	end
	enviar(jugador)
	return hecho
end

local function recibir(recibo: { [string]: any }): Enum.ProductPurchaseDecision
	local nombre = nombreDe(recibo.ProductId)
	if not nombre then
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	local jugador = Players:GetPlayerByUserId(recibo.PlayerId)
	local ok, nuevas = cambiar(recibo.PlayerId, nombre, 1, recibo.PurchaseId)
	if ok and nuevas then
		if jugador then
			fichas[jugador] = nuevas
		end
	elseif RunService:IsStudio() and jugador then
		local f = fichas[jugador] or {}
		f[nombre] = (f[nombre] or 0) + 1
		fichas[jugador] = f
	else
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	if jugador then
		task.spawn(function()
			if not usar(jugador, nombre) then
				avisar(jugador, if nombre == "Revivir" then "Revivir guardado: úsalo la próxima vez que te caigas" else "Desastre guardado: lánzalo en tu próximo vuelo")
			end
		end)
	end
	return Enum.ProductPurchaseDecision.PurchaseGranted
end

local function darPase(jugador: Player)
	if jugador:GetAttribute("VidasInfinitas") == true then
		return
	end
	jugador:SetAttribute("VidasInfinitas", true)
	if Vidas.muerto(jugador) then
		Vidas.revivir(jugador)
	end
end

local function pedir(jugador: Player, accion: any, dato: any)
	local ahora = os.clock()
	if (esperas[jugador] or 0) > ahora or typeof(accion) ~= "string" then
		return
	end
	esperas[jugador] = ahora + 0.4
	local nombre: string
	if accion == "comprar" and typeof(dato) == "string" and productoDe(dato) ~= 0 then
		pcall(MarketplaceService.PromptProductPurchase, MarketplaceService, jugador, productoDe(dato))
		return
	elseif accion == "revivir" then
		local objetivo = if typeof(dato) == "number" then Players:GetPlayerByUserId(dato) else jugador
		if not objetivo or not Vidas.muerto(objetivo) then
			return
		end
		objetivos[jugador] = objetivo
		nombre = "Revivir"
	elseif accion == "caos" and typeof(dato) == "string" and productoDe(dato) ~= 0 then
		local motivo = motivoCaos()
		if motivo then
			avisar(jugador, motivo)
			return
		end
		nombre = dato
	else
		return
	end
	if ((fichas[jugador] or {})[nombre] or 0) > 0 then
		usar(jugador, nombre)
		return
	end
	local id = productoDe(nombre)
	if id ~= 0 then
		pcall(MarketplaceService.PromptProductPurchase, MarketplaceService, jugador, id)
	end
end

local function cargar(jugador: Player)
	if R.PASE_VIDAS ~= 0 then
		local ok, tiene = pcall(MarketplaceService.UserOwnsGamePassAsync, MarketplaceService, jugador.UserId, R.PASE_VIDAS)
		if ok and tiene and jugador.Parent then
			darPase(jugador)
		end
	end
	local tienda = almacen
	if not tienda then
		return
	end
	for intento = 1, 3 do
		local ok, valor = pcall(tienda.GetAsync, tienda, "c_" .. jugador.UserId)
		if ok then
			if jugador.Parent and not fichas[jugador] then
				fichas[jugador] = leer(if typeof(valor) == "table" then valor.Fichas else nil)
				enviar(jugador)
			end
			return
		end
		task.wait(intento * 2)
	end
end

function Compras.iniciar()
	local ok, tienda = pcall(DataStoreService.GetDataStore, DataStoreService, "Overbooked_v1")
	if ok then
		almacen = tienda
	end
	remoto = Instance.new("RemoteEvent")
	remoto.Name = "Compras"
	remoto.Parent = Remotos
	remoto.OnServerEvent:Connect(pedir)
	MarketplaceService.ProcessReceipt = recibir
	MarketplaceService.PromptGamePassPurchaseFinished:Connect(function(jugador, pase, comprado)
		if comprado and pase == R.PASE_VIDAS and R.PASE_VIDAS ~= 0 then
			darPase(jugador)
			RemotoAviso:FireAllClients(`¡{jugador.DisplayName} tiene vidas infinitas!`, "bien")
		end
	end)
	for _, jugador in Players:GetPlayers() do
		task.spawn(cargar, jugador)
	end
	Players.PlayerAdded:Connect(cargar)
	Players.PlayerRemoving:Connect(function(jugador)
		fichas[jugador] = nil
		objetivos[jugador] = nil
		esperas[jugador] = nil
		for comprador, objetivo in objetivos do
			if objetivo == jugador then
				objetivos[comprador] = nil
			end
		end
	end)
end

return Compras
