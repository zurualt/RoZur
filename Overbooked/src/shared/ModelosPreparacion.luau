--!strict
local ModelosPreparacion = {}

ModelosPreparacion.IDS = {
	CartelAnimales = 115870586719990,
	CartelCombustible = 131167330198652,
	CartelMaletas = 78317387015558,
	CartelSalida = 131846260542237,
	CorralAnimales = 79594012391033,
	CuboMerienda = 127536624245117,
	FlechaSuelo = 83635838906847,
	LamparaNave = 86140905231043,
	NaveCarga = 113420751024919,
	PersianaNave = 139901991008671,
	PilaCajas = 116217065560055,
	Surtidor = 118766647985502,
	Tobogan1 = 115615590069346,
	Tobogan2 = 73482721912226,
	Tobogan3 = 127289289280312,
	Tobogan4 = 123233887425863,
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
