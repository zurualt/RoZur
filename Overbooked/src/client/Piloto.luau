--!strict
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoPiloto = Remotos:WaitForChild("Piloto") :: UnreliableRemoteEvent

local Piloto = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local activo = false
local teclas = { arriba = 0, abajo = 0, izquierda = 0, derecha = 0, mas = 0, menos = 0 }
local stick = Vector2.zero
local gases = 0
local envio = 0

local ACCIONES = {
	{ nombre = "PilotoArriba", campo = "arriba", teclas = { Enum.KeyCode.W, Enum.KeyCode.Up }, titulo = "Subir" },
	{ nombre = "PilotoAbajo", campo = "abajo", teclas = { Enum.KeyCode.S, Enum.KeyCode.Down }, titulo = "Bajar" },
	{ nombre = "PilotoIzquierda", campo = "izquierda", teclas = { Enum.KeyCode.A, Enum.KeyCode.Left }, titulo = "Izq" },
	{ nombre = "PilotoDerecha", campo = "derecha", teclas = { Enum.KeyCode.D, Enum.KeyCode.Right }, titulo = "Der" },
	{ nombre = "PilotoMas", campo = "mas", teclas = { Enum.KeyCode.LeftShift, Enum.KeyCode.ButtonR2 }, titulo = "Gas+" },
	{ nombre = "PilotoMenos", campo = "menos", teclas = { Enum.KeyCode.LeftControl, Enum.KeyCode.Q, Enum.KeyCode.ButtonL2 }, titulo = "Gas-" },
}

function Piloto.activo(): boolean
	return activo
end

local function vincular()
	for _, a in ACCIONES do
		ContextActionService:BindAction(a.nombre, function(_, estado)
			local valor = if estado == Enum.UserInputState.Begin or estado == Enum.UserInputState.Change then 1 else 0
			teclas[a.campo] = valor
			return Enum.ContextActionResult.Sink
		end, true, table.unpack(a.teclas))
		ContextActionService:SetTitle(a.nombre, a.titulo)
	end
	ContextActionService:BindAction("PilotoStick", function(_, _, entrada)
		stick = Vector2.new(entrada.Position.X, entrada.Position.Y)
		return Enum.ContextActionResult.Sink
	end, false, Enum.KeyCode.Thumbstick1)
end

local function desvincular()
	for _, a in ACCIONES do
		ContextActionService:UnbindAction(a.nombre)
		teclas[a.campo] = 0
	end
	ContextActionService:UnbindAction("PilotoStick")
	stick = Vector2.zero
end

local function cambiar(nuevo: boolean)
	if nuevo == activo then
		return
	end
	activo = nuevo
	if activo then
		local g = avion:GetAttribute("Gases")
		gases = if typeof(g) == "number" then g / 100 else 0
		vincular()
	else
		desvincular()
	end
end

local function alPersonaje(personaje: Model)
	cambiar(false)
	local humanoide = personaje:WaitForChild("Humanoid", 10)
	if not humanoide or not humanoide:IsA("Humanoid") then
		return
	end
	humanoide.Seated:Connect(function(sentado, asiento)
		if asiento then
			cambiar(sentado and asiento.Name == "AsientoPiloto")
		else
			cambiar(false)
		end
	end)
	humanoide.Died:Connect(function()
		cambiar(false)
	end)
end

function Piloto.iniciar()
	if jugador.Character then
		task.spawn(alPersonaje, jugador.Character)
	end
	jugador.CharacterAdded:Connect(alPersonaje)
	RunService.Heartbeat:Connect(function(dt)
		if not activo then
			return
		end
		gases = math.clamp(gases + (teclas.mas - teclas.menos) * dt * 0.45, 0, 1)
		envio += dt
		if envio >= 0.1 then
			envio = 0
			local cab = math.clamp(teclas.arriba - teclas.abajo + stick.Y, -1, 1)
			local ala = math.clamp(teclas.derecha - teclas.izquierda + stick.X, -1, 1)
			RemotoPiloto:FireServer(cab, ala, gases)
		end
	end)
end

return Piloto
