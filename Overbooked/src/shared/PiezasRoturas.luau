--!strict
local PiezasRoturas = {}

PiezasRoturas.CORTE = -8.4
PiezasRoturas.CORTE_ALA = 27.0
PiezasRoturas.CORTE_DERIVA = 114.3
PiezasRoturas.FILA_TECHO = -14.5
PiezasRoturas.HOMBRO = 1.843

PiezasRoturas.IDS = {
	RotBase = 102636619941103,
	RotPuntaIzq = 115617670188893,
	RotPuntaDer = 98636148488027,
	RotCola = 110752349064059,
	RotDeriva = 114810061022791,
	RotBordeAlaIzq = 79132986071516,
	RotBordeAlaDer = 112671126200725,
	RotBordeDeriva = 79574449776983,
	RotBordeCola = 91587312815042,
	RotTechoRoto = 81636288414137,
	RotBordeTecho = 102959693057655,
	RotTapaTecho = 132368712427406,
	RotCapo = 110940544001132,
	RotMotorExpuesto = 128267686217224,
	RotPolloGoma = 104255792322887,
	RotAsientoSaludo = 138325796633266,
	RotBrazosSaludo = 135371912518611,
} :: { [string]: number }

PiezasRoturas.CAJAS = {
	RotBase = { minimo = Vector3.new(-27.495, 90, -66), maximo = Vector3.new(27.495, 113.75, -7.9) },
	RotPuntaIzq = { minimo = Vector3.new(-38.08, 98.285, -27.15), maximo = Vector3.new(-26.548, 101.8, -18.95) },
	RotPuntaDer = { minimo = Vector3.new(26.548, 98.285, -27.15), maximo = Vector3.new(38.08, 101.8, -18.95) },
	RotCola = { minimo = Vector3.new(-14.6, 96.25, -8.9), maximo = Vector3.new(14.6, 114.738, 31.3) },
	RotDeriva = { minimo = Vector3.new(-0.689, 113.934, 15.989), maximo = Vector3.new(0.689, 122.6, 31.458) },
	RotBordeAlaIzq = { minimo = Vector3.new(-28.569, 97.365, -27.15), maximo = Vector3.new(-26.528, 99.25, -18.95) },
	RotBordeAlaDer = { minimo = Vector3.new(26.528, 97.365, -27.15), maximo = Vector3.new(28.569, 99.25, -18.95) },
	RotBordeDeriva = { minimo = Vector3.new(-0.933, 113.914, 15.989), maximo = Vector3.new(0.933, 115.766, 30.689) },
	RotBordeCola = { minimo = Vector3.new(-9.085, 96.19, -10.155), maximo = Vector3.new(9.172, 114.096, -6.6) },
	RotTechoRoto = { minimo = Vector3.new(-5.496, 111.999, -17.21), maximo = Vector3.new(5.381, 115.131, -11.818) },
	RotBordeTecho = { minimo = Vector3.new(-6.7, 106.6, -16.788), maximo = Vector3.new(6.7, 110.147, -12.015) },
	RotTapaTecho = { minimo = Vector3.new(-5.29, 109.76, -16.801), maximo = Vector3.new(5.29, 113.75, -12.271) },
	RotCapo = { minimo = Vector3.new(-2.151, 1.095, -2.5), maximo = Vector3.new(2.151, 2.31, 2.3) },
	RotMotorExpuesto = { minimo = Vector3.new(-1.896, 1.287, -2.3), maximo = Vector3.new(1.814, 2.889, 2.1) },
	RotPolloGoma = { minimo = Vector3.new(-0.728, -1.888, -3.936), maximo = Vector3.new(0.728, 1.344, 2.552) },
	RotAsientoSaludo = { minimo = Vector3.new(-1.2, -1.6, -1.58), maximo = Vector3.new(1.2, 3.69, 1.205) },
	RotBrazosSaludo = { minimo = Vector3.new(-1.392, 1.748, -0.171), maximo = Vector3.new(1.392, 3.924, 0.127) },
} :: { [string]: { minimo: Vector3, maximo: Vector3 } }

return PiezasRoturas
