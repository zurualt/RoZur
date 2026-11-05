--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Camara = require(script.Parent.Camara)
local Manos = require(script.Parent.Manos)
local Rafagas = require(script.Parent.Rafagas)
local Sonido = require(script.Parent.Sonido)

local Bofetada = {}

local jugador = Players.LocalPlayer
local rng = Random.new()
local remoto: RemoteEvent? = nil
local ultima = 0
local AMARILLO = Color3.fromRGB(255, 214, 70)
local ROJO = Color3.fromRGB(217, 68, 58)
local FRASES_BOFETADA = { "¡ZAS!", "¡PLAF!", "¡CHAS!" }

function Bofetada.dar()
	local ahora = os.clock()
	local personaje = jugador.Character
	local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
	if ahora - ultima < 0.6 or not personaje or not humanoide or humanoide.Health <= 0 or humanoide.SeatPart or personaje:GetAttribute("Ragdoll") then
		return
	end
	ultima = ahora
	Camara.alcanzar()
	Manos.bofetada()
	local r = remoto
	if r then
		r:FireServer(Workspace.CurrentCamera.CFrame.LookVector)
	end
end

function Bofetada.iniciar()
	task.spawn(function()
		local r = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Bofetada", 30)
		if not r or not r:IsA("RemoteEvent") then
			return
		end
		remoto = r
		r.OnClientEvent:Connect(function(posicion, _, clase, autor)
			if typeof(posicion) ~= "Vector3" then
				return
			end
			Sonido.reproducir("Bofetada", posicion, 1, rng:NextNumber(0.9, 1.15))
			local texto = if clase == "Revancha" then "¡TOMA!" else FRASES_BOFETADA[rng:NextInteger(1, #FRASES_BOFETADA)]
			Rafagas.palabra(posicion + Vector3.new(0, 0.6, 0), texto, AMARILLO, ROJO, 0.9)
			local raiz = jugador.Character and jugador.Character:FindFirstChild("HumanoidRootPart")
			if raiz and raiz:IsA("BasePart") and (raiz.Position - posicion).Magnitude < 3 then
				Camara.sacudir(0.7)
			elseif autor == jugador then
				Camara.sacudir(0.25)
			end
		end)
	end)
end

return Bofetada
