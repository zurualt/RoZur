--!strict
local ModelosPreparacion = {}

ModelosPreparacion.IDS = {
	CartelAnimales = 75468403907813,
	CartelCombustible = 136249828462670,
	CartelMaletas = 133933059246316,
	CartelSalida = 111918568192304,
	CorralAnimales = 98714186567066,
	CuboMerienda = 114927437716180,
	FlechaSuelo = 127848616945468,
	LamparaNave = 86140905231043,
	NaveCarga = 137875192053353,
	PersianaNave = 95952857309967,
	PilaCajas = 128042252486496,
	Surtidor = 111866396200947,
	Tobogan1 = 138243303430937,
	Tobogan2 = 77824776284376,
	Tobogan3 = 127585283344345,
	Tobogan4 = 84476062301094,
} :: { [string]: number }

ModelosPreparacion.CAJAS = {
	CartelAnimales = { minimo = Vector3.new(-2.5, 0.0, -0.21), maximo = Vector3.new(2.5, 2.6, 0.15) },
	CartelCombustible = { minimo = Vector3.new(-1.6, 0.0, -0.21), maximo = Vector3.new(1.6, 2.6, 0.15) },
	CartelMaletas = { minimo = Vector3.new(-3.5, 0.0, -0.21), maximo = Vector3.new(3.5, 2.6, 0.15) },
	CartelSalida = { minimo = Vector3.new(-4.0, 0.0, -0.21), maximo = Vector3.new(4.0, 3.0, 0.15) },
	CorralAnimales = { minimo = Vector3.new(-5.4, 0.0, -8.5), maximo = Vector3.new(5.4, 2.6, 8.52) },
	CuboMerienda = { minimo = Vector3.new(-0.675, 0.0, -0.675), maximo = Vector3.new(0.675, 1.705, 0.675) },
	FlechaSuelo = { minimo = Vector3.new(-1.6, 0.0, -2.2), maximo = Vector3.new(1.6, 0.081, 2.2) },
	LamparaNave = { minimo = Vector3.new(-0.916, 0.45, -0.916), maximo = Vector3.new(0.916, 5.0, 0.916) },
	NaveCarga = { minimo = Vector3.new(-16.6, 0.0, -20.6), maximo = Vector3.new(16.6, 19.5, 20.6) },
	PersianaNave = { minimo = Vector3.new(-7.1, 0.0, -0.36), maximo = Vector3.new(7.1, 9.2, 0.36) },
	PilaCajas = { minimo = Vector3.new(-2.321, 0.0, -2.12), maximo = Vector3.new(2.21, 4.82, 2.348) },
	Surtidor = { minimo = Vector3.new(-1.59, 0.0, -1.3), maximo = Vector3.new(1.52, 4.77, 1.45) },
	Tobogan1 = { minimo = Vector3.new(-1.75, 0.0, -6.55), maximo = Vector3.new(1.75, 9.53, 4.1) },
	Tobogan2 = { minimo = Vector3.new(-1.75, 0.0, -6.55), maximo = Vector3.new(1.75, 9.53, 4.1) },
	Tobogan3 = { minimo = Vector3.new(-1.75, 0.0, -6.55), maximo = Vector3.new(1.75, 9.53, 4.1) },
	Tobogan4 = { minimo = Vector3.new(-1.75, 0.0, -6.55), maximo = Vector3.new(1.75, 9.53, 4.1) },
} :: { [string]: { minimo: Vector3, maximo: Vector3 } }

return ModelosPreparacion
