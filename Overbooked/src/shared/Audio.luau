--!strict
export type Datos = { volumen: number, bucle: boolean, duracion: number }

local Audio = {}

Audio.IDS = {
} :: { [string]: number }

Audio.DATOS = {
} :: { [string]: Datos }

return Audio
