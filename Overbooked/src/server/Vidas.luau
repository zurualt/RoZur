--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Personajes = require(script.Parent.Personajes)
local Rafagas = require(script.Parent.Rafagas)

local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder
local RemotoAviso = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Aviso") :: RemoteEvent

local Vidas = {}

local REAPARECER = 3
local caidas: { [Player]: number } = {}

local function enVuelo(): boolean
	return Estado:GetAttribute("Fase") == "Vuelo"
end

local function cargar(jugador: Player)
	if jugador.Parent then
		pcall(function()
			jugador:LoadCharacterAsync()
		end)
	end
end

function Vidas.muerto(jugador: Player): boolean
	return jugador:GetAttribute("Muerto") == true
end

function Vidas.revivir(jugador: Player, quien: Player?, silencio: boolean?): boolean
	if not Vidas.muerto(jugador) or not jugador.Parent then
		return false
	end
	jugador:SetAttribute("Muerto", nil)
	jugador:SetAttribute("ReviveEn", nil)
	task.spawn(function()
		cargar(jugador)
		local raiz = Personajes.raiz(jugador)
		if raiz then
			Rafagas.lanzar("Confeti", raiz.Position + Vector3.new(0, 2, 0), 1.3)
		end
	end)
	if silencio then
		return true
	end
	if quien and quien ~= jugador then
		RemotoAviso:FireAllClients(`¡{quien.DisplayName} ha pagado para revivir a {jugador.DisplayName}!`, "bien")
	else
		RemotoAviso:FireAllClients(`¡{jugador.DisplayName} ha vuelto a bordo!`, "bien")
	end
	return true
end

local function caer(jugador: Player)
	local n = (caidas[jugador] or 0) + 1
	caidas[jugador] = n
	local R = Config.ROBUX
	local espera = if jugador:GetAttribute("VidasInfinitas") == true then R.ESPERA_PASE else math.min(R.ESPERA + R.ESPERA_EXTRA * (n - 1), R.ESPERA_MAX)
	jugador:SetAttribute("ReviveEn", Workspace:GetServerTimeNow() + espera)
	jugador:SetAttribute("Muerto", true)
end

local function alPersonaje(jugador: Player, personaje: Model)
	local humanoide = personaje:WaitForChild("Humanoid", 10)
	if not humanoide or not humanoide:IsA("Humanoid") then
		return
	end
	humanoide.Died:Connect(function()
		local raiz = personaje:FindFirstChild("HumanoidRootPart")
		if enVuelo() and raiz and raiz:IsA("BasePart") and raiz.Position.Y < Config.CAIDA_Y + 5 then
			caer(jugador)
			return
		end
		task.delay(REAPARECER, function()
			if jugador.Character == personaje and not Vidas.muerto(jugador) then
				cargar(jugador)
			end
		end)
	end)
end

function Vidas.iniciar()
	Players.CharacterAutoLoads = false
	local function alEntrar(jugador: Player)
		jugador.CharacterAdded:Connect(function(personaje)
			alPersonaje(jugador, personaje)
		end)
		local personaje = jugador.Character
		if personaje then
			task.spawn(alPersonaje, jugador, personaje)
		else
			task.spawn(cargar, jugador)
		end
	end
	for _, jugador in Players:GetPlayers() do
		alEntrar(jugador)
	end
	Players.PlayerAdded:Connect(alEntrar)
	Players.PlayerRemoving:Connect(function(jugador)
		caidas[jugador] = nil
	end)
	Estado:GetAttributeChangedSignal("Fase"):Connect(function()
		if enVuelo() then
			table.clear(caidas)
			return
		end
		for _, jugador in Players:GetPlayers() do
			Vidas.revivir(jugador, nil, true)
		end
	end)
	task.spawn(function()
		while true do
			task.wait(0.5)
			local ahora = Workspace:GetServerTimeNow()
			for _, jugador in Players:GetPlayers() do
				local t = jugador:GetAttribute("ReviveEn")
				if Vidas.muerto(jugador) and typeof(t) == "number" and ahora >= t then
					Vidas.revivir(jugador)
				end
			end
		end
	end)
end

return Vidas
