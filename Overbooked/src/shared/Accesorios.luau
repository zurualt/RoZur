--!strict
local Config = require(script.Parent.Config)
local MiniaturasAccesorios = require(script.Parent.MiniaturasAccesorios)
local ModelosAccesorios = require(script.Parent.ModelosAccesorios)

local Accesorios = {}

Accesorios.CARPETA = "Accesorios"

local porNombre: { [string]: Config.Accesorio } = {}
for _, a in Config.TIENDA.ACCESORIOS do
	porNombre[a.nombre] = a
end

function Accesorios.de(nombre: string): Config.Accesorio?
	return porNombre[nombre]
end

function Accesorios.disponible(nombre: string): boolean
	return porNombre[nombre] ~= nil and ModelosAccesorios.IDS[nombre] ~= nil
end

function Accesorios.modelo(nombre: string): string
	return "Acc" .. nombre
end

function Accesorios.parte(nombre: string): string
	return ModelosAccesorios.PARTES[nombre] or "Head"
end

function Accesorios.miniatura(nombre: string): string
	local id = MiniaturasAccesorios[nombre]
	return if id then `rbxassetid://{id}` else ""
end

return Accesorios
