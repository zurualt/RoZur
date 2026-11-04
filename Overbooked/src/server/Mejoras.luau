--!strict
local Mejoras = {}

local niveles: { [string]: number } = {}

function Mejoras.nivel(nombre: string): number
	return niveles[nombre] or 0
end

function Mejoras.fijar(nuevos: { [string]: number })
	table.clear(niveles)
	for nombre, n in nuevos do
		niveles[nombre] = n
	end
end

return Mejoras
