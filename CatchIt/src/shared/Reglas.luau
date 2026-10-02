--!strict
-- Reglas de la partida 1v1. El servidor y los clientes leen de aquí para usar los mismos números.

local Reglas = {
	-- Cada ronda dura esto. Al acabar, pierde la ronda quien tenga el tag.
	DURACION_RONDA = 30,
	-- Gana la partida el primero que llegue a estas rondas.
	RONDAS_PARA_GANAR = 3,
	-- Después de recibir el tag no puedes devolverlo durante este tiempo.
	PROTECCION_TRAS_TAG = 1.5,
	-- Distancia máxima entre los dos HumanoidRootPart para que cuente como toque.
	DISTANCIA_TAG_HORIZONTAL = 4.5,
	DISTANCIA_TAG_VERTICAL = 5.5,
}

return table.freeze(Reglas)
