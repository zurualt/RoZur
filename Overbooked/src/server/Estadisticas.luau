--!strict
local Players = game:GetService("Players")

export type Premio = { icono: string, titulo: string, nombre: string, valor: number }

local Estadisticas = {}

local PREMIOS = {
	{ clave = "servir", icono = "🍔", titulo = "Mejor camarero" },
	{ clave = "fuego", icono = "🧯", titulo = "Bombero del vuelo" },
	{ clave = "reparar", icono = "🔧", titulo = "Mecánico" },
	{ clave = "punteria", icono = "🎯", titulo = "Puntería" },
	{ clave = "piratas", icono = "🏴‍☠️", titulo = "Artillero" },
	{ clave = "pilotar", icono = "✈", titulo = "Piloto del día" },
	{ clave = "cocodrilo", icono = "🐊", titulo = "Domador" },
	{ clave = "caidas", icono = "🤕", titulo = "Más torpe" },
}

local datos: { [Player]: { [string]: number } } = {}

function Estadisticas.sumar(jugador: Player?, clave: string, cantidad: number?)
	if not jugador or not jugador.Parent then
		return
	end
	local t = datos[jugador]
	if not t then
		t = {}
		datos[jugador] = t
	end
	t[clave] = (t[clave] or 0) + (cantidad or 1)
end

function Estadisticas.reiniciar()
	table.clear(datos)
end

function Estadisticas.premios(): { Premio }
	local lista: { Premio } = {}
	for _, p in PREMIOS do
		local mejor: Player? = nil
		local valor = 0
		for jugador, t in datos do
			local v = t[p.clave] or 0
			if v > valor and jugador.Parent then
				mejor, valor = jugador, v
			end
		end
		if mejor then
			table.insert(lista, { icono = p.icono, titulo = p.titulo, nombre = mejor.DisplayName, valor = math.floor(valor) })
		end
	end
	return lista
end

function Estadisticas.iniciar()
	Players.PlayerRemoving:Connect(function(jugador)
		datos[jugador] = nil
	end)
end

return Estadisticas
