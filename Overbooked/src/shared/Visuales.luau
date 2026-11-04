--!strict
export type Caja = { minimo: Vector3, maximo: Vector3 }

local Visuales = {}

Visuales.IDS = {
	AvionExterior = 118431177149171,
	Cocodrilo = 127685716387558,
	PasajeroAbuela = 73450731808741,
	PasajeroDeportista = 110268157077635,
	PasajeroEjecutivo = 134465245438284,
	PasajeroNino = 136718313156951,
	PasajeroRockero = 94916049667450,
	PasajeroTurista = 79367930254328,
} :: { [string]: number }

Visuales.CAJAS = {
	AvionExterior = { minimo = Vector3.new(-38.08, 90.0, -66.0), maximo = Vector3.new(38.08, 122.6, 31.458) },
	Cocodrilo = { minimo = Vector3.new(-0.738, -0.034, -3.09), maximo = Vector3.new(0.738, 1.365, 3.0) },
	PasajeroAbuela = { minimo = Vector3.new(-1.055, -1.581, -1.58), maximo = Vector3.new(1.055, 3.591, 0.715) },
	PasajeroDeportista = { minimo = Vector3.new(-1.086, -1.581, -1.58), maximo = Vector3.new(1.086, 3.355, 0.765) },
	PasajeroEjecutivo = { minimo = Vector3.new(-1.055, -1.581, -1.58), maximo = Vector3.new(1.055, 3.409, 0.715) },
	PasajeroNino = { minimo = Vector3.new(-0.782, -1.197, -1.171), maximo = Vector3.new(0.782, 2.684, 0.53) },
	PasajeroRockero = { minimo = Vector3.new(-1.055, -1.581, -1.58), maximo = Vector3.new(1.055, 3.885, 0.911) },
	PasajeroTurista = { minimo = Vector3.new(-1.2, -1.581, -1.58), maximo = Vector3.new(1.2, 3.69, 1.052) },
} :: { [string]: Caja }

return Visuales
