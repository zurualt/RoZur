--!strict
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local Vehiculo = {}

local jugador = Players.LocalPlayer
local VELOCIDAD = 26
local GIRO = 1.5

function Vehiculo.iniciar()
	RunService.Heartbeat:Connect(function(dt: number)
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		local asiento = humanoide and humanoide.SeatPart
		if not asiento or not asiento:IsA("VehicleSeat") or asiento.Name ~= "AsientoTractor" then
			return
		end
		local chasis = asiento.Parent
		if not chasis or not chasis:IsA("BasePart") or chasis.Anchored then
			return
		end
		local frente = chasis.CFrame.LookVector * Vector3.new(1, 0, 1)
		if frente.Magnitude < 0.1 then
			return
		end
		frente = frente.Unit
		local v = chasis.AssemblyLinearVelocity
		local plano = v * Vector3.new(1, 0, 1)
		local avance = plano:Dot(frente)
		local objetivo = frente * asiento.ThrottleFloat * VELOCIDAD
		local lateral = plano - frente * avance
		local nuevo = plano:Lerp(objetivo + lateral * 0.2, math.min(1, dt * 2.2))
		chasis.AssemblyLinearVelocity = Vector3.new(nuevo.X, v.Y, nuevo.Z)
		local giro = -asiento.SteerFloat * GIRO * math.clamp(avance / 6, -1, 1)
		local w = chasis.AssemblyAngularVelocity
		chasis.AssemblyAngularVelocity = Vector3.new(w.X, w.Y + (giro - w.Y) * math.min(1, dt * 6), w.Z)
	end)
end

return Vehiculo
