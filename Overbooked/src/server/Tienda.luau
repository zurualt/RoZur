--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Accesorios = require(ReplicatedStorage.Shared.Accesorios)
local Config = require(ReplicatedStorage.Shared.Config)
local ModelosAccesorios = require(ReplicatedStorage.Shared.ModelosAccesorios)
local Activos = require(script.Parent.Activos)
local Datos = require(script.Parent.Datos)
local Mejoras = require(script.Parent.Mejoras)
local Rafagas = require(script.Parent.Rafagas)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoTienda = Remotos:WaitForChild("Tienda") :: RemoteEvent
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent

local Tienda = {}

local esperas: { [Player]: number } = {}

local function estado(jugador: Player): { [string]: any }
	local tiene, puestos = Datos.accesorios(jugador)
	return { dinero = Datos.dinero(jugador), vuelos = Datos.vuelos(jugador), tiene = tiene, puestos = puestos, mejoras = Datos.mejoras(jugador) }
end

local function enviar(jugador: Player, abrir: boolean, evento: { [string]: string }?)
	RemotoTienda:FireClient(jugador, abrir, estado(jugador), evento)
end

local function vestir(jugador: Player)
	local personaje = jugador.Character
	if not personaje then
		return
	end
	local _, puestos = Datos.accesorios(jugador)
	local escala = personaje:GetScale()
	for _, ranura in Config.TIENDA.RANURAS do
		local etiqueta = "Accesorio" .. ranura
		for _, h in personaje:GetChildren() do
			if h.Name == etiqueta and h:IsA("Model") then
				h:Destroy()
			end
		end
		local nombre = puestos[ranura]
		if not nombre or not Accesorios.disponible(nombre) then
			continue
		end
		local parte = personaje:FindFirstChild(Accesorios.parte(nombre))
		if parte and parte:IsA("BasePart") then
			Activos.adjuntar(parte, Accesorios.modelo(nombre), CFrame.identity, escala, etiqueta, function()
				local _, actuales = Datos.accesorios(jugador)
				return actuales[ranura] == nombre and jugador.Character == personaje
			end)
		end
	end
end

local function mejoraDe(nombre: string): Config.Mejora?
	for _, m in Config.TIENDA.MEJORAS do
		if m.nombre == nombre then
			return m
		end
	end
	return nil
end

function Tienda.aplicar()
	local maximos: { [string]: number } = {}
	for _, jugador in Players:GetPlayers() do
		for nombre, n in Datos.mejoras(jugador) do
			local m = mejoraDe(nombre)
			if m then
				maximos[nombre] = math.max(maximos[nombre] or 0, math.min(n, #m.precios))
			end
		end
	end
	Mejoras.fijar(maximos)
end

local function sinPerfil(jugador: Player): boolean
	if Datos.guardable(jugador) then
		return false
	end
	RemotoAviso:FireClient(jugador, "No se ha podido cargar tu perfil: la tienda no está disponible en este servidor", "peligro")
	return true
end

local function comprar(jugador: Player, nombre: string): { [string]: string }?
	local a = Accesorios.de(nombre)
	local tiene = Datos.accesorios(jugador)
	if not a or tiene[nombre] or not Accesorios.disponible(nombre) or sinPerfil(jugador) then
		return nil
	end
	if Datos.vuelos(jugador) < a.vuelos then
		return { tipo = "bloqueado", nombre = nombre }
	end
	if not Datos.gastar(jugador, a.precio) then
		return { tipo = "pobre", nombre = nombre }
	end
	Datos.darAccesorio(jugador, nombre)
	Datos.poner(jugador, nombre)
	vestir(jugador)
	local personaje = jugador.Character
	local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
	if raiz and raiz:IsA("BasePart") then
		Rafagas.lanzar("Monedas", raiz.Position + Vector3.new(0, 3, 0), 0.8)
	end
	return { tipo = "comprado", nombre = nombre }
end

local function mejorar(jugador: Player, nombre: string): { [string]: string }?
	local m = mejoraDe(nombre)
	if not m or sinPerfil(jugador) then
		return nil
	end
	local precio = m.precios[(Datos.mejoras(jugador)[m.nombre] or 0) + 1]
	if not precio then
		return nil
	end
	if not Datos.gastar(jugador, precio) then
		return { tipo = "pobre", nombre = nombre }
	end
	Datos.subirMejora(jugador, m.nombre)
	return { tipo = "mejora", nombre = nombre }
end

local function pedir(jugador: Player, accion: any, nombre: any)
	local ahora = os.clock()
	if (esperas[jugador] or 0) > ahora or typeof(accion) ~= "string" or typeof(nombre) ~= "string" or #nombre > 40 or not Datos.listo(jugador) then
		return
	end
	esperas[jugador] = ahora + 0.25
	local evento: { [string]: string }? = nil
	if accion == "comprar" then
		evento = comprar(jugador, nombre)
	elseif accion == "mejora" then
		evento = mejorar(jugador, nombre)
	elseif accion == "poner" and Datos.poner(jugador, nombre) then
		vestir(jugador)
		evento = { tipo = "puesto", nombre = nombre }
	elseif accion == "quitar" and table.find(Config.TIENDA.RANURAS, nombre) then
		Datos.quitar(jugador, nombre)
		vestir(jugador)
		evento = { tipo = "quitado", nombre = nombre }
	end
	enviar(jugador, false, evento)
end

local function ponerAviso(aeropuerto: Instance)
	local puesto = aeropuerto:FindFirstChild("Tienda", true)
	if not puesto or not puesto:IsA("BasePart") or puesto:FindFirstChild("AvisoTienda") then
		return
	end
	local aviso = Instance.new("ProximityPrompt")
	aviso.Name = "AvisoTienda"
	aviso.ActionText = "Abrir tienda"
	aviso.ObjectText = "Tienda de la tripulación"
	aviso.KeyboardKeyCode = Enum.KeyCode.E
	aviso.MaxActivationDistance = 10
	aviso.RequiresLineOfSight = false
	aviso.Parent = puesto
	aviso.Triggered:Connect(function(jugador)
		if Datos.listo(jugador) then
			enviar(jugador, true)
		end
	end)
end

local function prepararModelos()
	for nombre, id in ModelosAccesorios.IDS do
		local caja = ModelosAccesorios.CAJAS[nombre]
		if caja then
			Activos.registrar(Accesorios.modelo(nombre), id, caja)
		end
	end
	local carpeta = Instance.new("Folder")
	carpeta.Name = Accesorios.CARPETA
	carpeta.Parent = ReplicatedStorage
	for _, a in Config.TIENDA.ACCESORIOS do
		if Accesorios.disponible(a.nombre) then
			Activos.clonar(Accesorios.modelo(a.nombre), function(visual)
				visual.Name = a.nombre
				visual.Parent = carpeta
			end)
		end
	end
end

function Tienda.iniciar()
	prepararModelos()
	RemotoTienda.OnServerEvent:Connect(pedir)
	local aeropuerto = Workspace:FindFirstChild("Aeropuerto")
	if aeropuerto then
		ponerAviso(aeropuerto)
	end
	Workspace.ChildAdded:Connect(function(hijo)
		if hijo.Name == "Aeropuerto" then
			task.wait(1)
			ponerAviso(hijo)
		end
	end)
	local function alEntrar(jugador: Player)
		jugador.CharacterAdded:Connect(function(personaje)
			personaje:WaitForChild("Head", 10)
			personaje:WaitForChild("UpperTorso", 10)
			task.wait(0.5)
			vestir(jugador)
		end)
		task.spawn(function()
			local limite = os.clock() + 90
			while jugador.Parent and not Datos.listo(jugador) and os.clock() < limite do
				task.wait(0.5)
			end
			if jugador.Parent then
				vestir(jugador)
			end
		end)
	end
	for _, jugador in Players:GetPlayers() do
		alEntrar(jugador)
	end
	Players.PlayerAdded:Connect(alEntrar)
	Players.PlayerRemoving:Connect(function(jugador)
		esperas[jugador] = nil
	end)
end

return Tienda
