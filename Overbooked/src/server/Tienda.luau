--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Visuales = require(ReplicatedStorage.Shared.Visuales)
local Activos = require(script.Parent.Activos)
local Datos = require(script.Parent.Datos)
local Mejoras = require(script.Parent.Mejoras)
local Sonidos = require(script.Parent.Sonidos)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoTienda = Remotos:WaitForChild("Tienda") :: RemoteEvent
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent

local Tienda = {}

local esperas: { [Player]: number } = {}

local function estado(jugador: Player): { [string]: any }
	local gorros, gorro = Datos.gorros(jugador)
	return { dinero = Datos.dinero(jugador), gorros = gorros, gorro = gorro, mejoras = Datos.mejoras(jugador) }
end

local function enviar(jugador: Player, abrir: boolean)
	RemotoTienda:FireClient(jugador, abrir, estado(jugador))
end

local function ponerGorro(jugador: Player)
	local personaje = jugador.Character
	if not personaje then
		return
	end
	for _, h in personaje:GetChildren() do
		if h.Name == "Gorro" and h:IsA("Model") then
			h:Destroy()
		end
	end
	local _, gorro = Datos.gorros(jugador)
	if gorro == "" or not Visuales.IDS[gorro] then
		return
	end
	local cabeza = personaje:FindFirstChild("Head")
	if not cabeza or not cabeza:IsA("BasePart") then
		return
	end
	local escala = personaje:GetScale()
	local ancla = Visuales.ANCLAS[gorro] or Vector3.new(0, cabeza.Size.Y / 2 / escala, 0)
	Activos.adjuntar(cabeza, gorro, CFrame.new(ancla * escala), escala, "Gorro", function()
		local _, actual = Datos.gorros(jugador)
		return actual == gorro and jugador.Character == personaje
	end)
end

local function gorroDe(nombre: string): Config.Gorro?
	for _, g in Config.TIENDA.GORROS do
		if g.nombre == nombre and Visuales.IDS[g.nombre] then
			return g
		end
	end
	return nil
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

local function pedir(jugador: Player, accion: any, nombre: any)
	local ahora = os.clock()
	if (esperas[jugador] or 0) > ahora or typeof(accion) ~= "string" or not Datos.listo(jugador) then
		return
	end
	esperas[jugador] = ahora + 0.3
	if (accion == "gorro" or accion == "mejora") and not Datos.guardable(jugador) then
		RemotoAviso:FireClient(jugador, "No se ha podido cargar tu perfil: la tienda no está disponible en este servidor", "peligro")
		return
	end
	if accion == "quitar" then
		Datos.equipar(jugador, "")
		ponerGorro(jugador)
	elseif accion == "gorro" and typeof(nombre) == "string" then
		local g = gorroDe(nombre)
		if not g then
			return
		end
		local tiene = Datos.gorros(jugador)
		if tiene[g.nombre] then
			Datos.equipar(jugador, g.nombre)
			ponerGorro(jugador)
		elseif Datos.gastar(jugador, g.precio) then
			Datos.darGorro(jugador, g.nombre)
			Datos.equipar(jugador, g.nombre)
			ponerGorro(jugador)
			Sonidos.emitirA(jugador, "Caja")
			RemotoAviso:FireClient(jugador, `¡Has comprado: {g.titulo}!`, "bien")
		else
			RemotoAviso:FireClient(jugador, "No tienes dinero suficiente", "info")
		end
	elseif accion == "mejora" and typeof(nombre) == "string" then
		local m = mejoraDe(nombre)
		if not m then
			return
		end
		local nivel = Datos.mejoras(jugador)[m.nombre] or 0
		local precio = m.precios[nivel + 1]
		if not precio then
			return
		end
		if Datos.gastar(jugador, precio) then
			Datos.subirMejora(jugador, m.nombre)
			Sonidos.emitirA(jugador, "Caja")
			RemotoAviso:FireClient(jugador, `{m.titulo}: nivel {nivel + 1}`, "bien")
		else
			RemotoAviso:FireClient(jugador, "No tienes dinero suficiente", "info")
		end
	end
	enviar(jugador, false)
end

function Tienda.iniciar()
	local puesto = Workspace:WaitForChild("Aeropuerto"):FindFirstChild("Tienda", true)
	if puesto and puesto:IsA("BasePart") then
		local aviso = Instance.new("ProximityPrompt")
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
	RemotoTienda.OnServerEvent:Connect(pedir)
	local function alEntrar(jugador: Player)
		jugador.CharacterAdded:Connect(function(personaje)
			personaje:WaitForChild("Head", 10)
			task.wait(0.5)
			ponerGorro(jugador)
		end)
		task.spawn(function()
			local limite = os.clock() + 90
			while jugador.Parent and not Datos.listo(jugador) and os.clock() < limite do
				task.wait(0.5)
			end
			if jugador.Parent then
				ponerGorro(jugador)
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
