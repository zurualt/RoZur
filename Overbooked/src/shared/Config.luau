--!strict
export type DefObjeto = {
	tamano: Vector3,
	color: Color3,
	material: Enum.Material,
	densidad: number,
	visual: string?,
	nombre: string,
}

local Config = {}

Config.ASSET_TRIPULANTE = 93486408235562
Config.ALTURA_TRIPULANTE = 3.93
Config.ROTACION_FBX = CFrame.Angles(math.pi / 2, 0, 0)


Config.COLORES_JUGADOR = {
	Color3.fromRGB(139, 210, 76),
	Color3.fromRGB(160, 124, 242),
	Color3.fromRGB(242, 123, 181),
	Color3.fromRGB(245, 205, 61),
	Color3.fromRGB(90, 196, 232),
	Color3.fromRGB(240, 112, 88),
	Color3.fromRGB(120, 226, 186),
	Color3.fromRGB(250, 250, 250),
}

Config.PARTES_CUERPO = {
	"Head",
	"UpperTorso",
	"LowerTorso",
	"LeftUpperArm",
	"LeftLowerArm",
	"LeftHand",
	"RightUpperArm",
	"RightLowerArm",
	"RightHand",
	"LeftUpperLeg",
	"LeftLowerLeg",
	"LeftFoot",
	"RightUpperLeg",
	"RightLowerLeg",
	"RightFoot",
}

Config.BRAZOS = { "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand" }

Config.SUELO_Y = 100
Config.CAIDA_Y = 70
Config.GRAVEDAD = 196.2
Config.CENTRO_AVION = Vector3.new(0, 105, -18)

Config.VUELO = {
	TICK = 0.1,
	COMPRESION = 14,
	FACTOR_VERTICAL = 1.5,
	VELOCIDAD_MAX = 900,
	VELOCIDAD_DESPEGUE = 260,
	VELOCIDAD_PERDIDA = 220,
	VELOCIDAD_ATERRIZAJE = 340,
	VERTICAL_ATERRIZAJE = 9,
	ACELERACION = 70,
	CABECEO_MAX = 20,
	ALABEO_MAX = 35,
	VEL_CABECEO = 14,
	VEL_ALABEO = 30,
	GIRO = 0.09,
	CONSUMO = 0.11,
	ALTITUD_CRUCERO = 6000,
	ALTITUD_MAX = 11000,
	APROXIMACION = 140,
	PISTA = 18,
	ENTREGA_INICIO = 0.45,
	ENTREGA_FIN = 0.6,
}

Config.TURBULENCIA = {
	BASE = 0.12,
	UMBRAL_RAGDOLL = 0.72,
	IMPULSO_OBJETOS = 38,
	IMPULSO_PASAJEROS = 30,
}

Config.LOBBY = {
	CUENTA = 15,
	MAX = 4,
	ESPERA_GRUPO = 20,
}

Config.PARTIDA = {
	EMBARQUE = 45,
	RESULTADOS = 14,
	DESPEGUE_AUTO = 45,
	MAX_OBJETOS = 45,
	INTERVALO_PELIGRO_MIN = 32,
	INTERVALO_PELIGRO_MAX = 55,
}

Config.RITMO = {
	CALMA = 50,
	TURBULENCIA_CALMA = 0.35,
	INICIO = 0.5,
	FINAL = 1.6,
	MAXIMA = 2.6,
	GRAVES = 0.3,
	POR_RIESGO = 0.2,
	POR_JUGADOR = 0.12,
	POR_JORNADA = 0.15,
	MAX_JORNADA = 8,
	PASAJEROS_POR_JORNADA = 2,
	PAGO_POR_JORNADA = 0.1,
	CAOS_PRIMERO = 25,
	CAOS_MIN = 50,
	CAOS_MAX = 80,
}

Config.AGARRE = {
	DISTANCIA = 12,
	DISTANCIA_MAX = 26,
	VELOCIDAD_MAX = 90,
	LANZAMIENTO = 58,
	LANZAMIENTO_FUERTE = 92,
	DEVOLVER_PROPIEDAD = 1.5,
}

Config.HERRAMIENTAS = {
	ALCANCE_EXTINTOR = 15,
	DANO_EXTINTOR = 9,
	ALCANCE_LLAVE = 9,
	REPARACION_LLAVE = 8,
	REPARACION_PIOLET = 10,
	ALCANCE_PIOLET = 6,
	CADENCIA = 0.18,
}

Config.OBJETOS = {
	Hamburguesa = {
		tamano = Vector3.new(0.9, 0.6, 0.9),
		color = Color3.fromRGB(233, 166, 75),
		material = Enum.Material.SmoothPlastic,
		densidad = 0.5,
		visual = "Hamburguesa",
		nombre = "Hamburguesa",
	},
	Bandeja = {
		tamano = Vector3.new(1.6, 0.5, 1.1),
		color = Color3.fromRGB(169, 176, 184),
		material = Enum.Material.Metal,
		densidad = 0.6,
		visual = "Bandeja",
		nombre = "Bandeja de hamburguesas",
	},
	Cafe = {
		tamano = Vector3.new(0.5, 0.7, 0.5),
		color = Color3.fromRGB(217, 68, 58),
		material = Enum.Material.SmoothPlastic,
		densidad = 0.4,
		visual = "Cafe",
		nombre = "Café",
	},
	Agua = {
		tamano = Vector3.new(0.4, 0.9, 0.4),
		color = Color3.fromRGB(143, 211, 244),
		material = Enum.Material.Glass,
		densidad = 0.5,
		visual = "Agua",
		nombre = "Agua",
	},
	Extintor = {
		tamano = Vector3.new(0.7, 1.8, 0.7),
		color = Color3.fromRGB(217, 68, 58),
		material = Enum.Material.SmoothPlastic,
		densidad = 1.2,
		visual = "Extintor",
		nombre = "Extintor",
	},
	Llave = {
		tamano = Vector3.new(0.5, 1.8, 0.25),
		color = Color3.fromRGB(169, 176, 184),
		material = Enum.Material.Metal,
		densidad = 1.5,
		visual = "Llave",
		nombre = "Llave",
	},
	Maleta = {
		tamano = Vector3.new(1.6, 1.2, 0.7),
		color = Color3.fromRGB(242, 123, 43),
		material = Enum.Material.SmoothPlastic,
		densidad = 0.9,
		visual = "Maleta1",
		nombre = "Maleta",
	},
	Caja = {
		tamano = Vector3.new(3, 3, 3),
		color = Color3.fromRGB(201, 139, 78),
		material = Enum.Material.Wood,
		densidad = 0.35,
		visual = "Caja",
		nombre = "Caja",
	},
	CajaFragil = {
		tamano = Vector3.new(2, 2, 2),
		color = Color3.fromRGB(230, 200, 160),
		material = Enum.Material.Wood,
		densidad = 0.4,
		visual = "CajaFragil",
		nombre = "Caja frágil",
	},
	Carrito = {
		tamano = Vector3.new(1.6, 3.2, 2.6),
		color = Color3.fromRGB(242, 123, 43),
		material = Enum.Material.SmoothPlastic,
		densidad = 0.6,
		visual = "Carrito",
		nombre = "Carrito",
	},
	Piolet = {
		tamano = Vector3.new(0.25, 1.9, 0.5),
		color = Color3.fromRGB(242, 123, 43),
		material = Enum.Material.Metal,
		densidad = 1.2,
		visual = "Piolet",
		nombre = "Piolet",
	},
	Bolso = {
		tamano = Vector3.new(1.6, 1, 0.8),
		color = Color3.fromRGB(31, 166, 160),
		material = Enum.Material.Fabric,
		densidad = 0.45,
		visual = "Bolso",
		nombre = "Bolso de mano",
	},
	Jaula = {
		tamano = Vector3.new(3, 2.6, 7),
		color = Color3.fromRGB(52, 56, 63),
		material = Enum.Material.Metal,
		densidad = 0.5,
		visual = "Jaula",
		nombre = "Jaula",
	},
	Tronco = {
		tamano = Vector3.new(4, 1.2, 1.2),
		color = Color3.fromRGB(156, 107, 62),
		material = Enum.Material.Wood,
		densidad = 0.6,
		visual = "Tronco",
		nombre = "tronco",
	},
	Coco = {
		tamano = Vector3.new(1.2, 1.3, 1.2),
		color = Color3.fromRGB(122, 74, 42),
		material = Enum.Material.Wood,
		densidad = 0.7,
		visual = "Coco",
		nombre = "coco",
	},
	RadioAntena = {
		tamano = Vector3.new(1, 4, 1),
		color = Color3.fromRGB(169, 176, 184),
		material = Enum.Material.Metal,
		densidad = 0.5,
		visual = "RadioAntena",
		nombre = "antena de radio",
	},
	RadioBateria = {
		tamano = Vector3.new(1.6, 1.2, 1),
		color = Color3.fromRGB(246, 196, 69),
		material = Enum.Material.SmoothPlastic,
		densidad = 1,
		visual = "RadioBateria",
		nombre = "batería",
	},
	RadioCaja = {
		tamano = Vector3.new(2, 1.4, 1.4),
		color = Color3.fromRGB(31, 166, 160),
		material = Enum.Material.SmoothPlastic,
		densidad = 0.8,
		visual = "RadioCaja",
		nombre = "radio",
	},
	Bengala = {
		tamano = Vector3.new(0.4, 1.6, 0.4),
		color = Color3.fromRGB(217, 68, 58),
		material = Enum.Material.SmoothPlastic,
		densidad = 0.5,
		visual = "Bengala",
		nombre = "bengala",
	},
	Biberon = {
		tamano = Vector3.new(0.4, 1, 0.4),
		color = Color3.fromRGB(247, 247, 242),
		material = Enum.Material.SmoothPlastic,
		densidad = 0.4,
		visual = "Biberon",
		nombre = "biberón",
	},
	Piano = {
		tamano = Vector3.new(3.52, 2.97, 4.68),
		color = Color3.fromRGB(27, 27, 33),
		material = Enum.Material.SmoothPlastic,
		densidad = 1.4,
		visual = "Piano",
		nombre = "piano de cola",
	},
	Bombona = {
		tamano = Vector3.new(0.82, 1.98, 0.94),
		color = Color3.fromRGB(217, 68, 58),
		material = Enum.Material.SmoothPlastic,
		densidad = 0.8,
		visual = "Bombona",
		nombre = "bombona de gas",
	},
} :: { [string]: DefObjeto }

Config.ISLA = {
	CENTRO = Vector3.new(-25, 90.2, -105),
	DURACION = 300,
	RESCATE = 22,
	ENTREGA = 6,
	TRONCOS = 3,
	PIEZAS = { "RadioAntena", "RadioBateria", "RadioCaja" },
	CANGREJOS = 10,
	COCOS = 12,
	VELOCIDAD_CANGREJO = 5,
	PELLIZCO = 2.6,
	PAGO = 0.5,
	BONUS_RESCATE = 300,
}

Config.PREPARACION = {
	TIEMPO = 150,
	CONDUCIR = 75,
	INTERVALO_MALETA = 3.2,
	MALETAS_POR_JUGADOR = 1,
	COMBUSTIBLE_INICIAL = 25,
	BOMBEO = 7,
	LLEGADA = 20,
	REVENTON = 0.3,
}

Config.COMIDA = { "Hamburguesa", "Cafe", "Agua" }

Config.ICONOS = {
	Hamburguesa = "Hamburguesa",
	Cafe = "Cafe",
	Agua = "Agua",
	Miedo = "Miedo",
	Enfado = "Enfado",
	Feliz = "Feliz",
	Golpe = "Golpe",
	Quemado = "Fuego",
	Mojado = "Agua",
	Mordisco = "Cocodrilo",
	Bolso = "Maleta",
	Biberon = "Agua",
	Mareo = "Mareo",
}

Config.PEDIDOS = { Hamburguesa = "una hamburguesa", Cafe = "un café", Agua = "agua", Biberon = "el biberón" }

Config.PASAJEROS = {
	VISUALES = { "PasajeroAbuela", "PasajeroTurista", "PasajeroEjecutivo", "PasajeroNino", "PasajeroDeportista", "PasajeroRockero" },
	PIELES = {
		Color3.fromRGB(242, 201, 160),
		Color3.fromRGB(201, 142, 98),
		Color3.fromRGB(138, 90, 60),
		Color3.fromRGB(245, 169, 184),
	},
	ROPA = {
		Color3.fromRGB(31, 166, 160),
		Color3.fromRGB(74, 120, 201),
		Color3.fromRGB(245, 205, 61),
		Color3.fromRGB(107, 191, 89),
		Color3.fromRGB(217, 68, 58),
		Color3.fromRGB(52, 56, 63),
	},
	PEDIDO_PROB = 0.019,
	PACIENCIA = 70,
	PEDIDOS_BASE = 1,
	PEDIDOS_POR_JUGADOR = 2,
	SUBIDA_SERVIR = 0.35,
	BAJADA_ESPERA = 0.3,
	MIEDO_DECAE = 0.03,
	DISTANCIA_ASIENTO = 4.5,
	ESCALA_VISUAL = 0.85,
	CARACTERES = {
		{ nombre = "Normal", peso = 52, pedido = 1, paciencia = 1, miedo = 1, sueno = 1 },
		{ nombre = "Grunon", peso = 8, pedido = 1, paciencia = 0.65, miedo = 1, sueno = 0.5 },
		{ nombre = "Miedoso", peso = 7, pedido = 0.9, paciencia = 1, miedo = 2, sueno = 0.6 },
		{ nombre = "Dormilon", peso = 7, pedido = 0.3, paciencia = 1.2, miedo = 0.8, sueno = 12 },
		{ nombre = "Gloton", peso = 7, pedido = 2.2, paciencia = 0.9, miedo = 1, sueno = 0.8 },
		{ nombre = "Charlatan", peso = 7, pedido = 1, paciencia = 1, miedo = 1, sueno = 0 },
		{ nombre = "Fiestero", peso = 6, pedido = 1.1, paciencia = 1.1, miedo = 0.5, sueno = 0.3 },
		{ nombre = "Despistado", peso = 6, pedido = 0.8, paciencia = 1.2, miedo = 1, sueno = 1 },
	},
}

export type Accesorio = { nombre: string, titulo: string, ranura: string, precio: number, vuelos: number }
export type Mejora = { nombre: string, titulo: string, descripcion: string, precios: { number } }

Config.TIENDA = {
	RANURAS = { "Cabeza", "Cara", "Espalda" },
	ACCESORIOS = {
		{ nombre = "GorroCono", titulo = "Cono de tráfico", ranura = "Cabeza", precio = 300, vuelos = 0 },
		{ nombre = "GorraPiloto", titulo = "Gorra de piloto", ranura = "Cabeza", precio = 450, vuelos = 0 },
		{ nombre = "GorroChef", titulo = "Gorro de chef", ranura = "Cabeza", precio = 550, vuelos = 0 },
		{ nombre = "GorroHelice", titulo = "Gorro con hélice", ranura = "Cabeza", precio = 650, vuelos = 0 },
		{ nombre = "Chistera", titulo = "Chistera diminuta", ranura = "Cabeza", precio = 700, vuelos = 0 },
		{ nombre = "Auriculares2", titulo = "Auriculares retro", ranura = "Cabeza", precio = 750, vuelos = 0 },
		{ nombre = "GorroPlatano", titulo = "Plátano pelado", ranura = "Cabeza", precio = 800, vuelos = 0 },
		{ nombre = "SombreroVaquero", titulo = "Sombrero vaquero", ranura = "Cabeza", precio = 900, vuelos = 0 },
		{ nombre = "GorroPez", titulo = "Gorro de pez", ranura = "Cabeza", precio = 1100, vuelos = 0 },
		{ nombre = "GorroPato", titulo = "Gorro de pato", ranura = "Cabeza", precio = 1300, vuelos = 0 },
		{ nombre = "NidoPajaro", titulo = "Nido con okupa", ranura = "Cabeza", precio = 1500, vuelos = 0 },
		{ nombre = "CascoBombero", titulo = "Casco de bombero", ranura = "Cabeza", precio = 1800, vuelos = 0 },
		{ nombre = "CascoVikingo", titulo = "Casco vikingo", ranura = "Cabeza", precio = 2400, vuelos = 10 },
		{ nombre = "Corona", titulo = "Corona", ranura = "Cabeza", precio = 2500, vuelos = 15 },
		{ nombre = "GorroCocodrilo", titulo = "Cocodrilo comecabezas", ranura = "Cabeza", precio = 4500, vuelos = 30 },
		{ nombre = "Antifaz", titulo = "Antifaz de ladrón", ranura = "Cara", precio = 400, vuelos = 0 },
		{ nombre = "GafasEstrella", titulo = "Gafas de estrella", ranura = "Cara", precio = 800, vuelos = 0 },
		{ nombre = "Monoculo", titulo = "Monóculo elegante", ranura = "Cara", precio = 1400, vuelos = 0 },
		{ nombre = "GafasBuceo", titulo = "Gafas de buceo", ranura = "Cara", precio = 2000, vuelos = 5 },
		{ nombre = "LlaveGigante", titulo = "Llave gigante", ranura = "Espalda", precio = 700, vuelos = 0 },
		{ nombre = "MochilaParacaidas", titulo = "Mochila paracaídas", ranura = "Espalda", precio = 1200, vuelos = 0 },
		{ nombre = "FlotadorPato", titulo = "Flotador de patito", ranura = "Espalda", precio = 1600, vuelos = 0 },
		{ nombre = "AlasAvion", titulo = "Alas de avión", ranura = "Espalda", precio = 3200, vuelos = 15 },
		{ nombre = "Jetpack", titulo = "Mochila cohete", ranura = "Espalda", precio = 6000, vuelos = 40 },
	} :: { Accesorio },
	MEJORAS = {
		{ nombre = "Casco", titulo = "Casco reforzado", descripcion = "−12 % de daño al casco por nivel", precios = { 600, 1400, 3000 } },
		{ nombre = "Combustible", titulo = "Motores eficientes", descripcion = "−12 % de consumo por nivel", precios = { 500, 1200, 2600 } },
		{ nombre = "Cocina", titulo = "Cocina premium", descripcion = "+1 hamburguesa por bandeja y +6 s de paciencia por nivel", precios = { 400, 1000, 2200 } },
	} :: { Mejora },
}

export type ProductoCaos = { nombre: string, producto: number, precio: number, titulo: string, descripcion: string }

Config.ROBUX = {
	PASE_VIDAS = 2071564630,
	PRECIO_PASE = 59,
	REVIVIR = 3728527770,
	PRECIO_REVIVIR = 14,
	ESPERA = 30,
	ESPERA_EXTRA = 15,
	ESPERA_MAX = 90,
	ESPERA_PASE = 4,
	ENFRIAMIENTO = 45,
	BONUS_CAOS = 120,
	CAOS = {
		{ nombre = "Cabra", producto = 3728527782, precio = 15, titulo = "Cabra a bordo", descripcion = "Suelta una cabra loca por la cabina" },
		{ nombre = "Gallinas", producto = 3728527795, precio = 15, titulo = "Estampida de gallinas", descripcion = "Una jaula de gallinas se abre en pleno vuelo" },
		{ nombre = "Disco", producto = 3728527811, precio = 19, titulo = "Fiebre disco", descripcion = "Bola de discoteca y todos a bailar" },
		{ nombre = "Pajaros", producto = 3728527827, precio = 25, titulo = "Choque de pájaros", descripcion = "Pájaros directos al motor" },
		{ nombre = "CaidaLibre", producto = 3728527840, precio = 29, titulo = "Caída libre", descripcion = "Gravedad cero durante unos segundos" },
		{ nombre = "Piratas", producto = 3728527851, precio = 49, titulo = "Piratas del aire", descripcion = "Llegan los piratas a abordar el avión" },
	} :: { ProductoCaos },
}

Config.CARGA_ESPECIAL = {
	PIANO_UMBRAL = 45,
	PIANO_ROCE = 0.05,
	PIANO_SOLO = 0.3,
	PIANO_VELOCIDAD_SOLO = 5,
	PIANO_AYUDA = 10,
	PIANO_MULTA = 500,
	PIANO_PLONK = 9,
	PIANO_ATROPELLO = 11,
	INCLINACION = 45,
	BOMBONA_UMBRAL = 30,
	BOMBONA_LANZADA = 40,
	MECHA = 2.4,
	EMPUJE = 26,
	RADIO = 9,
	DANO_CASCO = 3,
	DANO_CARGA = 35,
}

Config.PANTALLAS = {
	DISTANCIA = 45,
	RADAR_ANTELACION = 24,
	RADAR_AVISO = 12,
	MONITOR_HZ = 10,
	MONITOR_FIGURAS = 30,
	MONITOR_CAMBIO = 9,
}

return Config
