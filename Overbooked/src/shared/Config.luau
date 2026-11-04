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

Config.ASSET_TRIPULANTE = 87418247604950
Config.ALTURA_TRIPULANTE = 4.67
Config.ROTACION_FBX = CFrame.identity


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
	COMPRESION = 20,
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

Config.PARTIDA = {
	EMBARQUE = 25,
	RESULTADOS = 14,
	DESPEGUE_AUTO = 45,
	MAX_OBJETOS = 45,
	PRIMER_PELIGRO = 25,
	INTERVALO_PELIGRO_MIN = 22,
	INTERVALO_PELIGRO_MAX = 40,
}

Config.AGARRE = {
	DISTANCIA = 12,
	DISTANCIA_MAX = 26,
	VELOCIDAD_MAX = 90,
	LANZAMIENTO = 58,
	DEVOLVER_PROPIEDAD = 1.5,
}

Config.HERRAMIENTAS = {
	ALCANCE_EXTINTOR = 15,
	DANO_EXTINTOR = 9,
	ALCANCE_LLAVE = 9,
	REPARACION_LLAVE = 8,
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
	Jaula = {
		tamano = Vector3.new(3, 2.6, 7),
		color = Color3.fromRGB(52, 56, 63),
		material = Enum.Material.Metal,
		densidad = 0.5,
		visual = "Jaula",
		nombre = "Jaula",
	},
} :: { [string]: DefObjeto }

Config.COMIDA = { "Hamburguesa", "Cafe", "Agua" }

Config.ICONOS = {
	Hamburguesa = "🍔",
	Cafe = "☕",
	Agua = "💧",
	Miedo = "😱",
	Enfado = "😡",
	Feliz = "😊",
}

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
	PEDIDO_PROB = 0.045,
	PACIENCIA = 45,
	SUBIDA_SERVIR = 0.35,
	BAJADA_ESPERA = 0.3,
	MIEDO_DECAE = 0.03,
	DISTANCIA_ASIENTO = 4.5,
}

return Config
