--!strict
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remoto = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Efecto") :: UnreliableRemoteEvent

local Rafagas = {}

function Rafagas.lanzar(tipo: string, posicion: Vector3, escala: number?, color: Color3?)
	Remoto:FireAllClients(tipo, posicion, escala or 1, color)
end

return Rafagas
