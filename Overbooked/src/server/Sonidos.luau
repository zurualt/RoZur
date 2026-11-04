--!strict
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Audio = require(ReplicatedStorage.Shared.Audio)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoSonido = Remotos:WaitForChild("Sonido") :: UnreliableRemoteEvent

local Sonidos = {}

local ultimos: { [string]: number } = {}
local ventana = 0
local enVentana = 0

function Sonidos.emitir(nombre: string, posicion: Vector3?, intervalo: number?)
	if not Audio.IDS[nombre] then
		return
	end
	local ahora = os.clock()
	if ahora - (ultimos[nombre] or 0) < (intervalo or 0.06) then
		return
	end
	if ahora - ventana > 0.25 then
		ventana = ahora
		enVentana = 0
	end
	if enVentana >= 8 then
		return
	end
	enVentana += 1
	ultimos[nombre] = ahora
	RemotoSonido:FireAllClients(nombre, posicion)
end

return Sonidos
