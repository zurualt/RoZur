--!strict
local ModelosCaos = {}

ModelosCaos.IDS = {
	Cabra = 140032600968177,
	Gallina = 89315558778350,
	Bebe = 116790237064421,
	Biberon = 114468559373136,
} :: { [string]: number }

ModelosCaos.CAJAS = {
	Cabra = { minimo = Vector3.new(-0.588, 0, -1.26), maximo = Vector3.new(0.588, 2.287, 1.26) },
	Gallina = { minimo = Vector3.new(-0.417, 0, -0.574), maximo = Vector3.new(0.417, 1.317, 0.574) },
	Bebe = { minimo = Vector3.new(-0.44, 0, -0.374), maximo = Vector3.new(0.44, 1.151, 0.374) },
	Biberon = { minimo = Vector3.new(-0.195, 0, -0.186), maximo = Vector3.new(0.195, 1.0, 0.186) },
} :: { [string]: { minimo: Vector3, maximo: Vector3 } }

return ModelosCaos
