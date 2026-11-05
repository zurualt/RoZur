--!strict
export type Caja = { minimo: Vector3, maximo: Vector3 }

local Destinos = {}

Destinos.IDS = {
	AeropuertoCiudad = 109329544823580,
	AeropuertoDesierto = 107651799657572,
	AeropuertoJungla = 117032160058042,
	AeropuertoNieve = 85560836319027,
	AgujasDesierto = 93488380661156,
	BarrioCiudad = 119343695317352,
	BordeCiudad = 113414376672557,
	BordeDesierto = 81833331966363,
	BordeJungla = 111502010088348,
	BordeNieve = 70965611035683,
	CactusDesierto = 101355649195841,
	CerroJungla = 79912600715105,
	LucesCiudad = 121710444301942,
	LucesNieve = 95907426024221,
	MesaDesierto = 98581956620376,
	MontanaNieve1 = 80756056400281,
	MontanaNieve2 = 92831336406339,
	PalmeralJungla = 96636310020014,
	PinarNieve = 86793225323627,
	SelvaJungla = 135527940900477,
	SueloCiudad1 = 119453756241377,
	SueloCiudad2 = 124630457585398,
	SueloDesierto1 = 85411907222990,
	SueloDesierto2 = 132667569166833,
	SueloJungla1 = 106506704712487,
	SueloJungla2 = 117847244524993,
	SueloNieve1 = 90244059044489,
	SueloNieve2 = 112250710247202,
	TorresCiudad = 73694376883954,
} :: { [string]: number }

Destinos.CAJAS = {
	AeropuertoCiudad = { minimo = Vector3.new(-267, -1.6, -907), maximo = Vector3.new(267, 92.9, 907) },
	AeropuertoDesierto = { minimo = Vector3.new(-157, -1.6, -907), maximo = Vector3.new(157, 50.9, 907) },
	AeropuertoJungla = { minimo = Vector3.new(-157, -1.6, -907), maximo = Vector3.new(157, 27.5, 907) },
	AeropuertoNieve = { minimo = Vector3.new(-157, -3.477, -907), maximo = Vector3.new(157, 25.96, 907) },
	AgujasDesierto = { minimo = Vector3.new(-43.803, -4.484, -43.992), maximo = Vector3.new(43.803, 67.285, 43.992) },
	BarrioCiudad = { minimo = Vector3.new(-49.634, -1, -47.798), maximo = Vector3.new(49.634, 38.367, 47.798) },
	BordeCiudad = { minimo = Vector3.new(-431.879, -1, -1000), maximo = Vector3.new(431.331, 104.234, 1016.553) },
	BordeDesierto = { minimo = Vector3.new(-402, -1.5, -1000), maximo = Vector3.new(402, 89.988, 1000) },
	BordeJungla = { minimo = Vector3.new(-346, -1.6, -1001.665), maximo = Vector3.new(346, 45.942, 1000) },
	BordeNieve = { minimo = Vector3.new(-458, -1.5, -1002.397), maximo = Vector3.new(458, 144.741, 1000) },
	CactusDesierto = { minimo = Vector3.new(-16.077, -1.156, -13.738), maximo = Vector3.new(16.077, 13.253, 13.738) },
	CerroJungla = { minimo = Vector3.new(-71.638, -3, -62.901), maximo = Vector3.new(71.638, 123, 62.901) },
	LucesCiudad = { minimo = Vector3.new(-32.55, 1.4, -710.5), maximo = Vector3.new(32.55, 2.5, 710.5) },
	LucesNieve = { minimo = Vector3.new(-28.05, 1.4, -616.5), maximo = Vector3.new(28.05, 2.5, 616.5) },
	MesaDesierto = { minimo = Vector3.new(-201.689, -3, -112.564), maximo = Vector3.new(201.689, 95, 112.564) },
	MontanaNieve1 = { minimo = Vector3.new(-312.769, -5, -308.427), maximo = Vector3.new(312.769, 241.936, 308.427) },
	MontanaNieve2 = { minimo = Vector3.new(-381.952, -5, -388.062), maximo = Vector3.new(381.952, 204.802, 388.062) },
	PalmeralJungla = { minimo = Vector3.new(-19.78, -1.2, -18.815), maximo = Vector3.new(19.78, 22.599, 18.815) },
	PinarNieve = { minimo = Vector3.new(-27.878, -1.6, -23.86), maximo = Vector3.new(27.878, 24.427, 23.86) },
	SelvaJungla = { minimo = Vector3.new(-32.919, -0.668, -22.517), maximo = Vector3.new(32.919, 19.994, 22.517) },
	SueloCiudad1 = { minimo = Vector3.new(-1024, 0, -1024), maximo = Vector3.new(1024, 2, 1024) },
	SueloCiudad2 = { minimo = Vector3.new(-1024, 0, -1024), maximo = Vector3.new(1024, 2, 1024) },
	SueloDesierto1 = { minimo = Vector3.new(-1024, 0, -1024), maximo = Vector3.new(1024, 2, 1024) },
	SueloDesierto2 = { minimo = Vector3.new(-1024, 0, -1024), maximo = Vector3.new(1024, 2, 1024) },
	SueloJungla1 = { minimo = Vector3.new(-1024, 0, -1024), maximo = Vector3.new(1024, 2, 1024) },
	SueloJungla2 = { minimo = Vector3.new(-1024, 0, -1024), maximo = Vector3.new(1024, 2, 1024) },
	SueloNieve1 = { minimo = Vector3.new(-1024, 0, -1024), maximo = Vector3.new(1024, 2, 1024) },
	SueloNieve2 = { minimo = Vector3.new(-1024, 0, -1024), maximo = Vector3.new(1024, 2, 1024) },
	TorresCiudad = { minimo = Vector3.new(-42.5, -1, -38.5), maximo = Vector3.new(42.5, 110.9, 38.5) },
} :: { [string]: Caja }

Destinos.COLORES = {
	Jungla = Color3.fromRGB(79, 161, 76),
	Nieve = Color3.fromRGB(191, 211, 212),
	Desierto = Color3.fromRGB(229, 160, 92),
	Ciudad = Color3.fromRGB(157, 157, 143),
} :: { [string]: Color3 }

return Destinos
