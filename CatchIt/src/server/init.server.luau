--!strict
-- Punto de entrada del servidor de Catch It.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Reglas = require(ReplicatedStorage.Shared.Reglas)

print(`[Catch It] Servidor listo: rondas de {Reglas.DURACION_RONDA} s, gana quien llegue a {Reglas.RONDAS_PARA_GANAR}`)
