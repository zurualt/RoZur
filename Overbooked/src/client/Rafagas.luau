--!strict
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local VFX = require(ReplicatedStorage.Shared.VFX)

type Chorro = {
	textura: string,
	cuenta: number,
	tam: { number },
	vida: { number },
	velocidad: { number },
	color: Color3?,
	tinte: boolean?,
	transparencia: { number }?,
	esparcir: number?,
	gravedad: Vector3?,
	arrastre: number?,
	giro: number?,
	luz: number?,
	orientacion: Enum.ParticleOrientation?,
	aplastar: { number }?,
	recto: boolean?,
}

type Trozos = { cantidad: number, color: Color3, material: Enum.Material, tam: Vector3, transparencia: number? }

type Palabra = { textos: { string }, color: Color3, fondo: Color3, nube: boolean?, prob: number?, tam: number? }

type Rafaga = { chorros: { Chorro }, luz: Color3?, trozos: Trozos?, palabra: Palabra? }

export type Pop = {
	imagen: string?,
	tinte: Color3?,
	texto: string?,
	color: Color3?,
	fondo: Color3?,
	nube: boolean?,
	tam: number,
	vida: number,
	subir: number,
	girar: number?,
}

local Rafagas = {}

local MAX_ACTIVAS = 16
local MAX_POPS = 10
local DISTANCIA = 250
local DISTANCIA_PALABRA = 130
local activas = 0
local pops = 0
local ultimaPalabra = 0
local rng = Random.new()
local carpeta = Instance.new("Folder")
carpeta.Name = "Rafagas"

local LETRA = Font.new("rbxasset://fonts/families/LuckiestGuy.json")
local TINTA = Color3.fromRGB(42, 36, 32)
local CAIDA = Vector3.new(0, -40, 0)
local HUMO_OSCURO = Color3.fromRGB(78, 74, 72)
local GRIS = Color3.fromRGB(196, 194, 190)
local ARENA = Color3.fromRGB(240, 214, 150)
local AGUA = Color3.fromRGB(143, 211, 244)
local ORO = Color3.fromRGB(255, 214, 110)
local AMARILLO = Color3.fromRGB(255, 214, 70)
local NARANJA = Color3.fromRGB(255, 140, 50)
local ROJO = Color3.fromRGB(232, 67, 58)
local BLANCO = Color3.new(1, 1, 1)
local TURQUESA = Color3.fromRGB(31, 166, 160)
local MARRON = Color3.fromRGB(138, 90, 51)
local METAL = Color3.fromRGB(150, 150, 156)
local HORIZONTAL = Enum.ParticleOrientation.VelocityPerpendicular
local POP = { 0.7, -0.35, 0 }
local TIEMPOS: { [number]: { number } } = { [2] = { 0, 1 }, [3] = { 0, 0.18, 1 }, [4] = { 0, 0.15, 0.4, 1 } }

local function confeti(textura: string, color: Color3): Chorro
	return { textura = textura, cuenta = 7, tam = { 0.9, 0.9 }, vida = { 2.4, 3.4 }, velocidad = { 20, 34 }, color = color, esparcir = 55, gravedad = Vector3.new(0, -16, 0), arrastre = 1.2, giro = 420 }
end

local CONFETI = {
	confeti("Confeti", Color3.fromRGB(242, 123, 43)),
	confeti("Confeti", Color3.fromRGB(31, 166, 160)),
	confeti("ConfetiPunto", Color3.fromRGB(246, 196, 69)),
	confeti("ConfetiPunto", Color3.fromRGB(242, 155, 178)),
	confeti("Confeti", Color3.fromRGB(109, 190, 69)),
	{ textura = "Brillito", cuenta = 6, tam = { 0.3, 1.6, 0 }, vida = { 0.5, 0.8 }, velocidad = { 8, 16 }, color = ORO, esparcir = 70, giro = 90 },
}

local ESTRELLAS: { Chorro } = {
	{ textura = "Estrella", cuenta = 6, tam = { 0.3, 1.9, 0.5 }, vida = { 0.6, 0.9 }, velocidad = { 8, 14 }, esparcir = 70, gravedad = Vector3.new(0, -25, 0), giro = 240, aplastar = POP },
	{ textura = "Brillito", cuenta = 4, tam = { 0.2, 1.2, 0 }, vida = { 0.25, 0.4 }, velocidad = { 4, 9 }, color = ORO, giro = 90 },
}

local TIPOS: { [string]: Rafaga } = {
	Explosion = {
		luz = Color3.fromRGB(255, 160, 60),
		trozos = { cantidad = 7, color = Color3.fromRGB(70, 70, 76), material = Enum.Material.SmoothPlastic, tam = Vector3.new(0.9, 0.5, 0.7) },
		palabra = { textos = { "¡BUUM!", "¡KABUM!", "¡PUM!" }, color = AMARILLO, fondo = ROJO, tam = 1.3 },
		chorros = {
			{ textura = "Destello", cuenta = 1, tam = { 6, 20, 14 }, vida = { 0.18, 0.22 }, velocidad = { 0, 0 }, luz = 1 },
			{ textura = "Explosion", cuenta = 3, tam = { 3, 13, 10 }, vida = { 0.35, 0.55 }, velocidad = { 1, 5 }, giro = 60, aplastar = { -0.6, 0.35, 0 } },
			{ textura = "Humo1", cuenta = 6, tam = { 1.5, 7, 9 }, vida = { 1.4, 2.4 }, velocidad = { 8, 16 }, color = HUMO_OSCURO, arrastre = 2.5, gravedad = Vector3.new(0, 4, 0), giro = 40, transparencia = { 0.05, 1 }, aplastar = POP },
			{ textura = "Humo2", cuenta = 5, tam = { 1.5, 6, 8 }, vida = { 1.2, 2 }, velocidad = { 8, 14 }, color = HUMO_OSCURO, arrastre = 2.5, gravedad = Vector3.new(0, 4, 0), giro = 40, transparencia = { 0.05, 1 }, aplastar = POP },
			{ textura = "Chispa", cuenta = 26, tam = { 0.9, 0 }, vida = { 0.5, 0.9 }, velocidad = { 25, 50 }, luz = 1, gravedad = CAIDA, color = ORO },
			{ textura = "Onda", cuenta = 1, tam = { 1, 26 }, vida = { 0.4, 0.4 }, velocidad = { 0.05, 0.05 }, esparcir = 0, orientacion = HORIZONTAL, transparencia = { 0.1, 1 } },
		},
	},
	Hongo = {
		luz = Color3.fromRGB(255, 150, 60),
		trozos = { cantidad = 9, color = Color3.fromRGB(70, 70, 76), material = Enum.Material.SmoothPlastic, tam = Vector3.new(1, 0.6, 0.8) },
		palabra = { textos = { "¡CATAPLÁN!", "¡KA-BUUUM!", "¡CATACROCK!" }, color = AMARILLO, fondo = ROJO, tam = 1.7 },
		chorros = {
			{ textura = "Destello", cuenta = 1, tam = { 8, 28, 20 }, vida = { 0.2, 0.25 }, velocidad = { 0, 0 }, luz = 1 },
			{ textura = "Explosion", cuenta = 4, tam = { 4, 15, 11 }, vida = { 0.45, 0.6 }, velocidad = { 2, 8 }, giro = 60, aplastar = { -0.6, 0.4, 0 } },
			{ textura = "Hongo", cuenta = 1, tam = { 3, 12, 15 }, vida = { 2.4, 2.4 }, velocidad = { 4, 4 }, esparcir = 0, gravedad = Vector3.new(0, 3, 0), transparencia = { 0, 0, 0, 1 }, aplastar = { -0.9, 0.5, -0.1, 0 }, recto = true },
			{ textura = "Humo1", cuenta = 10, tam = { 2, 7, 10 }, vida = { 1.6, 2.6 }, velocidad = { 18, 30 }, color = HUMO_OSCURO, arrastre = 3, esparcir = 100, gravedad = Vector3.new(0, 2, 0), giro = 40, transparencia = { 0.05, 1 }, aplastar = POP },
			{ textura = "Chispa", cuenta = 30, tam = { 1, 0 }, vida = { 0.6, 1 }, velocidad = { 30, 55 }, luz = 1, gravedad = CAIDA, color = ORO },
			{ textura = "Onda", cuenta = 1, tam = { 1, 34 }, vida = { 0.5, 0.5 }, velocidad = { 0.05, 0.05 }, esparcir = 0, orientacion = HORIZONTAL, transparencia = { 0.1, 1 } },
		},
	},
	ExplosionPequena = {
		luz = Color3.fromRGB(255, 170, 70),
		palabra = { textos = { "¡PUM!", "¡PAM!", "¡BUM!" }, color = AMARILLO, fondo = NARANJA, prob = 0.5 },
		chorros = {
			{ textura = "Destello", cuenta = 1, tam = { 3, 9, 6 }, vida = { 0.15, 0.18 }, velocidad = { 0, 0 }, luz = 1 },
			{ textura = "Explosion", cuenta = 2, tam = { 1.5, 6.5, 5 }, vida = { 0.3, 0.45 }, velocidad = { 1, 3 }, giro = 60, aplastar = { -0.6, 0.35, 0 } },
			{ textura = "Humo3", cuenta = 5, tam = { 1, 4, 5 }, vida = { 1, 1.8 }, velocidad = { 5, 10 }, color = HUMO_OSCURO, arrastre = 2.5, gravedad = Vector3.new(0, 3, 0), giro = 40, aplastar = POP },
			{ textura = "Chispa", cuenta = 12, tam = { 0.6, 0 }, vida = { 0.4, 0.7 }, velocidad = { 18, 32 }, luz = 1, gravedad = CAIDA, color = ORO },
		},
	},
	Humo = {
		chorros = {
			{ textura = "Humo1", cuenta = 3, tam = { 1, 5, 6 }, vida = { 1.4, 2.2 }, velocidad = { 3, 7 }, color = GRIS, tinte = true, arrastre = 1, gravedad = Vector3.new(0, 5, 0), giro = 40, esparcir = 40, aplastar = POP },
			{ textura = "Humo2", cuenta = 3, tam = { 1, 5, 6 }, vida = { 1.4, 2.2 }, velocidad = { 3, 7 }, color = GRIS, tinte = true, arrastre = 1, gravedad = Vector3.new(0, 5, 0), giro = 40, esparcir = 40, aplastar = POP },
			{ textura = "Humo3", cuenta = 2, tam = { 0.8, 4, 5 }, vida = { 1.2, 2 }, velocidad = { 3, 7 }, color = GRIS, tinte = true, arrastre = 1, gravedad = Vector3.new(0, 5, 0), giro = 40, esparcir = 40, aplastar = POP },
		},
	},
	Chispas = {
		luz = Color3.fromRGB(255, 220, 140),
		chorros = {
			{ textura = "Destello", cuenta = 1, tam = { 1.2, 3 }, vida = { 0.1, 0.12 }, velocidad = { 0, 0 }, luz = 1, color = ORO, tinte = true },
			{ textura = "Chispa", cuenta = 22, tam = { 0.6, 0 }, vida = { 0.3, 0.6 }, velocidad = { 14, 28 }, luz = 1, gravedad = CAIDA, color = ORO, tinte = true, esparcir = 70, giro = 180 },
		},
	},
	Martillazo = {
		luz = Color3.fromRGB(255, 220, 140),
		palabra = { textos = { "¡CLANC!", "¡TONC!", "¡CLONC!" }, color = BLANCO, fondo = METAL, prob = 0.35, tam = 0.8 },
		chorros = {
			{ textura = "Brillito", cuenta = 1, tam = { 0.5, 2.6, 0 }, vida = { 0.2, 0.22 }, velocidad = { 0, 0 }, color = ORO, recto = true },
			{ textura = "Chispa", cuenta = 16, tam = { 0.6, 0 }, vida = { 0.3, 0.5 }, velocidad = { 14, 26 }, luz = 1, gravedad = CAIDA, color = ORO, esparcir = 70, giro = 180 },
		},
	},
	Polvo = {
		chorros = {
			{ textura = "Polvo", cuenta = 10, tam = { 1, 5, 6 }, vida = { 0.8, 1.4 }, velocidad = { 6, 12 }, color = Color3.fromRGB(230, 215, 190), tinte = true, esparcir = 85, arrastre = 3, giro = 30, transparencia = { 0.1, 1 }, aplastar = { -0.6, 0.2, 0 } },
		},
	},
	Arena = {
		chorros = {
			{ textura = "Polvo", cuenta = 8, tam = { 1, 4, 5 }, vida = { 0.8, 1.3 }, velocidad = { 5, 10 }, color = ARENA, tinte = true, esparcir = 85, arrastre = 3, giro = 30, aplastar = { -0.6, 0.2, 0 } },
			{ textura = "ConfetiPunto", cuenta = 18, tam = { 0.22, 0.1 }, vida = { 0.5, 0.9 }, velocidad = { 10, 18 }, color = ARENA, tinte = true, esparcir = 60, gravedad = CAIDA },
		},
	},
	Estrellas = { chorros = ESTRELLAS },
	Bonk = {
		chorros = ESTRELLAS,
		palabra = { textos = { "¡BONK!", "¡TOC!", "¡PLONK!" }, color = AMARILLO, fondo = NARANJA },
	},
	Ay = {
		chorros = ESTRELLAS,
		palabra = { textos = { "¡AY!", "¡AUCH!", "¡ÑIC!" }, color = BLANCO, fondo = ROJO },
	},
	Confeti = { chorros = CONFETI },
	Salpicadura = {
		palabra = { textos = { "¡CHOF!", "¡PLAF!" }, color = BLANCO, fondo = AGUA, nube = true, prob = 0.45, tam = 0.85 },
		chorros = {
			{ textura = "Mancha", cuenta = 1, tam = { 0.8, 3.4, 2.6 }, vida = { 0.3, 0.35 }, velocidad = { 0, 0 }, color = AGUA, tinte = true, aplastar = { -0.8, 0.3, 0 } },
			{ textura = "Corona", cuenta = 1, tam = { 2, 3.6 }, vida = { 0.25, 0.3 }, velocidad = { 0, 0 }, color = AGUA, tinte = true, recto = true },
			{ textura = "Gota", cuenta = 16, tam = { 0.6, 0.2 }, vida = { 0.4, 0.8 }, velocidad = { 10, 20 }, color = AGUA, tinte = true, esparcir = 60, gravedad = Vector3.new(0, -55, 0), orientacion = Enum.ParticleOrientation.VelocityParallel },
		},
	},
	Escombros = {
		trozos = { cantidad = 6, color = METAL, material = Enum.Material.Metal, tam = Vector3.new(0.7, 0.3, 0.6) },
		palabra = { textos = { "¡CATACRAC!", "¡CRAAAC!" }, color = AMARILLO, fondo = METAL },
		chorros = {
			{ textura = "Escombro", cuenta = 10, tam = { 1, 0.6 }, vida = { 0.8, 1.3 }, velocidad = { 14, 26 }, color = GRIS, tinte = true, esparcir = 75, gravedad = CAIDA, giro = 300 },
			{ textura = "Humo3", cuenta = 4, tam = { 0.8, 3.5, 4 }, vida = { 0.8, 1.4 }, velocidad = { 4, 8 }, color = GRIS, arrastre = 2, giro = 40, aplastar = POP },
		},
	},
	Astillas = {
		trozos = { cantidad = 5, color = Color3.fromRGB(201, 154, 91), material = Enum.Material.Wood, tam = Vector3.new(1.1, 0.2, 0.3) },
		palabra = { textos = { "¡CRAC!", "¡CRAS!", "¡CROC!" }, color = Color3.fromRGB(255, 226, 170), fondo = MARRON, prob = 0.8 },
		chorros = {
			{ textura = "Astilla", cuenta = 14, tam = { 1.2, 0.8 }, vida = { 0.7, 1.2 }, velocidad = { 12, 24 }, esparcir = 75, gravedad = CAIDA, giro = 360 },
			{ textura = "Polvo", cuenta = 3, tam = { 1, 3.5, 4 }, vida = { 0.6, 1 }, velocidad = { 3, 6 }, color = Color3.fromRGB(220, 200, 170), arrastre = 2, aplastar = POP },
		},
	},
	Cristales = {
		trozos = { cantidad = 4, color = Color3.fromRGB(190, 230, 245), material = Enum.Material.Glass, tam = Vector3.new(0.5, 0.1, 0.4), transparencia = 0.3 },
		palabra = { textos = { "¡CRASH!", "¡CLINC!" }, color = BLANCO, fondo = AGUA, prob = 0.8 },
		chorros = {
			{ textura = "Cristal", cuenta = 14, tam = { 0.9, 0.5 }, vida = { 0.6, 1 }, velocidad = { 12, 22 }, esparcir = 75, gravedad = CAIDA, giro = 360 },
			{ textura = "Brillito", cuenta = 6, tam = { 0.2, 1.1, 0 }, vida = { 0.3, 0.5 }, velocidad = { 6, 12 }, color = BLANCO, giro = 90 },
		},
	},
	Monedas = {
		chorros = {
			{ textura = "Moneda", cuenta = 12, tam = { 1.1, 0.8 }, vida = { 0.9, 1.4 }, velocidad = { 14, 24 }, esparcir = 40, gravedad = Vector3.new(0, -35, 0), giro = 200 },
			{ textura = "Brillito", cuenta = 6, tam = { 0.2, 1.2, 0 }, vida = { 0.3, 0.6 }, velocidad = { 6, 14 }, color = ORO, giro = 90 },
		},
	},
	Hojas = {
		chorros = {
			{ textura = "Hoja", cuenta = 10, tam = { 1, 0.8 }, vida = { 2.5, 4 }, velocidad = { 4, 10 }, esparcir = 90, gravedad = Vector3.new(0, -3, 0), arrastre = 1.5, giro = 120 },
		},
	},
	Bengala = {
		luz = Color3.fromRGB(255, 70, 60),
		chorros = {
			{ textura = "Brillo", cuenta = 2, tam = { 6, 10 }, vida = { 1, 1.4 }, velocidad = { 0, 0 }, luz = 1, color = Color3.fromRGB(255, 80, 70), tinte = true },
			{ textura = "Chispa", cuenta = 30, tam = { 0.7, 0 }, vida = { 0.6, 1.1 }, velocidad = { 15, 30 }, luz = 1, color = Color3.fromRGB(255, 120, 90), tinte = true, esparcir = 35, gravedad = Vector3.new(0, -15, 0) },
			{ textura = "Humo1", cuenta = 6, tam = { 1, 6, 7 }, vida = { 2, 3 }, velocidad = { 4, 8 }, color = Color3.fromRGB(242, 170, 170), tinte = true, gravedad = Vector3.new(0, 6, 0), arrastre = 1, giro = 40, aplastar = POP },
		},
	},
	Vapor = {
		chorros = {
			{ textura = "Vapor", cuenta = 8, tam = { 1.5, 4 }, vida = { 1, 1.8 }, velocidad = { 3, 7 }, color = Color3.fromRGB(240, 242, 246), esparcir = 40, gravedad = Vector3.new(0, 4, 0), arrastre = 1, giro = 40 },
		},
	},
	Plumas = {
		palabra = { textos = { "¡PÍO!", "¡CUAC!", "¡PÍIIO!" }, color = AMARILLO, fondo = BLANCO, nube = true, prob = 0.9 },
		chorros = {
			{ textura = "Pluma", cuenta = 16, tam = { 1.2, 0.9 }, vida = { 2, 3.5 }, velocidad = { 6, 16 }, esparcir = 180, gravedad = Vector3.new(0, -4, 0), arrastre = 2, giro = 200 },
		},
	},
	Onda = {
		chorros = {
			{ textura = "Onda", cuenta = 1, tam = { 1, 16 }, vida = { 0.45, 0.45 }, velocidad = { 0.05, 0.05 }, esparcir = 0, color = BLANCO, tinte = true, orientacion = HORIZONTAL, transparencia = { 0, 1 } },
		},
	},
	Bocina = {
		palabra = { textos = { "¡MEC MEC!", "¡MOC MOC!" }, color = AMARILLO, fondo = TURQUESA, nube = true, tam = 0.9 },
		chorros = {
			{ textura = "Onda", cuenta = 2, tam = { 0.5, 6 }, vida = { 0.3, 0.45 }, velocidad = { 0.05, 0.05 }, esparcir = 0, color = AMARILLO, transparencia = { 0, 1 } },
			{ textura = "Brillito", cuenta = 4, tam = { 0.2, 1, 0 }, vida = { 0.3, 0.5 }, velocidad = { 6, 10 }, color = AMARILLO, giro = 90 },
		},
	},
	Pitido = {
		palabra = { textos = { "¡PIIIP!", "¡BIIIP!" }, color = BLANCO, fondo = ROJO, tam = 0.9 },
		chorros = {
			{ textura = "Onda", cuenta = 2, tam = { 0.5, 5 }, vida = { 0.3, 0.45 }, velocidad = { 0.05, 0.05 }, esparcir = 0, color = ROJO, transparencia = { 0, 1 } },
		},
	},
	Ding = {
		palabra = { textos = { "¡DING!", "¡DING DONG!" }, color = AMARILLO, fondo = TURQUESA, nube = true, tam = 0.8 },
		chorros = {
			{ textura = "Brillito", cuenta = 5, tam = { 0.2, 1, 0 }, vida = { 0.3, 0.5 }, velocidad = { 5, 9 }, color = ORO, giro = 90 },
		},
	},
	Corazones = {
		chorros = {
			{ textura = "Corazon", cuenta = 4, tam = { 0.2, 1, 0.6 }, vida = { 0.9, 1.3 }, velocidad = { 3, 6 }, esparcir = 40, gravedad = Vector3.new(0, 4, 0), arrastre = 1, giro = 30, aplastar = POP },
			{ textura = "Brillito", cuenta = 5, tam = { 0.2, 0.9, 0 }, vida = { 0.3, 0.6 }, velocidad = { 5, 9 }, color = ORO, giro = 90 },
		},
	},
	Enfado = {
		chorros = {
			{ textura = "Humo2", cuenta = 4, tam = { 0.3, 1.3, 1.8 }, vida = { 0.6, 0.9 }, velocidad = { 8, 12 }, color = BLANCO, esparcir = 30, arrastre = 3, giro = 60, transparencia = { 0, 1 }, aplastar = POP },
		},
	},
	Sudor = {
		chorros = {
			{ textura = "Gota", cuenta = 3, tam = { 0.5, 0.3 }, vida = { 0.5, 0.7 }, velocidad = { 6, 9 }, color = AGUA, esparcir = 50, gravedad = Vector3.new(0, -30, 0), orientacion = Enum.ParticleOrientation.VelocityParallel },
		},
	},
}

local function curva(v: { number }, k: number): NumberSequence
	local t = TIEMPOS[#v]
	local puntos = {}
	for i, x in v do
		table.insert(puntos, NumberSequenceKeypoint.new(t[i], x * k))
	end
	return NumberSequence.new(puntos)
end

local function animar(i: Instance, t: number, props: { [string]: any }, estilo: Enum.EasingStyle?, direccion: Enum.EasingDirection?)
	TweenService:Create(i, TweenInfo.new(t, estilo or Enum.EasingStyle.Quad, direccion or Enum.EasingDirection.Out), props):Play()
end

local function imagen(padre: Instance, textura: string, tamano: UDim2, color: Color3?, estirar: boolean?): ImageLabel
	local i = Instance.new("ImageLabel")
	i.BackgroundTransparency = 1
	i.AnchorPoint = Vector2.new(0.5, 0.5)
	i.Position = UDim2.fromScale(0.5, 0.5)
	i.Size = tamano
	i.Image = VFX.textura(textura)
	i.ImageColor3 = color or BLANCO
	i.ScaleType = if estirar then Enum.ScaleType.Stretch else Enum.ScaleType.Fit
	i.Parent = padre
	return i
end

function Rafagas.pop(padre: Instance, desplazamiento: Vector3, p: Pop)
	if pops >= MAX_POPS then
		return
	end
	pops += 1
	local giro = p.girar or rng:NextNumber(-12, 12)
	local gui = Instance.new("BillboardGui")
	gui.Size = UDim2.fromScale(if p.texto then p.tam * 2 else p.tam, p.tam)
	gui.StudsOffsetWorldSpace = desplazamiento
	gui.LightInfluence = 0
	gui.MaxDistance = DISTANCIA_PALABRA
	local marco = Instance.new("Frame")
	marco.BackgroundTransparency = 1
	marco.AnchorPoint = Vector2.new(0.5, 0.5)
	marco.Position = UDim2.fromScale(0.5, 0.5)
	marco.Size = UDim2.fromScale(1.4, 0.55)
	marco.Rotation = giro
	marco.Parent = gui
	local escala = Instance.new("UIScale")
	escala.Scale = 0.1
	escala.Parent = marco
	if p.imagen then
		imagen(marco, p.imagen, UDim2.fromScale(1, 1), p.tinte)
	end
	if p.texto then
		if p.fondo then
			imagen(marco, if p.nube then "Nube" else "Pinchos", UDim2.fromScale(1.05, 1.7), p.fondo, true)
		end
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1
		t.AnchorPoint = Vector2.new(0.5, 0.5)
		t.Position = UDim2.fromScale(0.5, 0.52)
		t.Size = UDim2.fromScale(0.86, 0.6)
		t.FontFace = LETRA
		t.Text = p.texto
		t.TextScaled = true
		t.TextColor3 = p.color or BLANCO
		local trazo = Instance.new("UIStroke")
		trazo.Color = TINTA
		trazo.Thickness = 3
		trazo.LineJoinMode = Enum.LineJoinMode.Round
		trazo.Parent = t
		t.Parent = marco
	end
	gui.Parent = padre
	animar(escala, 0.22, { Scale = 1 }, Enum.EasingStyle.Back)
	animar(marco, 0.6, { Size = UDim2.fromScale(1, 1), Rotation = -giro * 0.3 }, Enum.EasingStyle.Elastic)
	animar(gui, p.vida, { StudsOffsetWorldSpace = desplazamiento + Vector3.new(0, p.subir, 0) })
	task.delay(math.max(0.3, p.vida - 0.22), function()
		animar(escala, 0.22, { Scale = 0 }, Enum.EasingStyle.Back, Enum.EasingDirection.In)
	end)
	task.delay(p.vida, function()
		pops -= 1
		gui:Destroy()
	end)
end

function Rafagas.palabra(posicion: Vector3, texto: string, color: Color3, fondo: Color3, escala: number?, nube: boolean?)
	local camara = Workspace.CurrentCamera
	local ahora = os.clock()
	if not camara or (camara.CFrame.Position - posicion).Magnitude > DISTANCIA_PALABRA or ahora - ultimaPalabra < 0.2 then
		return
	end
	ultimaPalabra = ahora
	local e = math.clamp(escala or 1, 0.7, 2.6)
	local ancla = Instance.new("Attachment")
	ancla.WorldPosition = posicion
	ancla.Parent = Workspace.Terrain
	Rafagas.pop(ancla, Vector3.new(0, 0.8 * e, 0), { texto = texto, color = color, fondo = fondo, nube = nube, tam = 2.2 * e, vida = 1.1, subir = 1.4 * e })
	task.delay(1.2, ancla.Destroy, ancla)
end

local function emitir(adjunto: Attachment, c: Chorro, escala: number, color: Color3?)
	local e = Instance.new("ParticleEmitter")
	e.Texture = VFX.textura(c.textura)
	e.Enabled = false
	e.Size = curva(c.tam, escala)
	local t = c.transparencia
	e.Transparency = if t then curva(t, 1) else NumberSequence.new(0, 1)
	if c.aplastar then
		e.Squash = curva(c.aplastar, 1)
	end
	e.Lifetime = NumberRange.new(c.vida[1], c.vida[2])
	e.Speed = NumberRange.new(c.velocidad[1] * escala, c.velocidad[2] * escala)
	local abrir = c.esparcir or 180
	e.SpreadAngle = Vector2.new(abrir, abrir)
	e.Acceleration = (c.gravedad or Vector3.zero) * math.sqrt(escala)
	e.Drag = c.arrastre or 0
	e.Rotation = if c.recto then NumberRange.new(0) else NumberRange.new(0, 360)
	e.RotSpeed = NumberRange.new(-(c.giro or 0), c.giro or 0)
	e.LightEmission = c.luz or 0
	e.Color = ColorSequence.new(if c.tinte and color then color else c.color or BLANCO)
	e.Orientation = c.orientacion or Enum.ParticleOrientation.FacingCamera
	e.EmissionDirection = Enum.NormalId.Top
	e.Parent = adjunto
	e:Emit(math.max(1, math.floor(c.cuenta * math.clamp(escala, 0.5, 2))))
end

local function trozos(posicion: Vector3, t: Trozos, escala: number)
	for _ = 1, math.floor(t.cantidad * math.clamp(escala, 0.5, 1.5)) do
		local p = Instance.new("Part")
		p.Size = t.tam * escala * rng:NextNumber(0.7, 1.3)
		p.Color = t.color
		p.Material = t.material
		p.Transparency = t.transparencia or 0
		p.CanQuery = false
		p.CanTouch = false
		p.Massless = true
		p.CastShadow = false
		p.CollisionGroup = "Sostenido"
		p.CFrame = CFrame.new(posicion) * CFrame.Angles(rng:NextNumber(0, 6.28), rng:NextNumber(0, 6.28), 0)
		p.AssemblyLinearVelocity = Vector3.new(rng:NextNumber(-1, 1), rng:NextNumber(0.6, 1.4), rng:NextNumber(-1, 1)) * 22 * escala
		p.AssemblyAngularVelocity = Vector3.new(rng:NextNumber(-12, 12), rng:NextNumber(-12, 12), rng:NextNumber(-12, 12))
		p.Parent = carpeta
		task.delay(rng:NextNumber(1.8, 2.6), function()
			TweenService:Create(p, TweenInfo.new(0.5), { Transparency = 1 }):Play()
			task.wait(0.5)
			p:Destroy()
		end)
	end
end

function Rafagas.lanzar(tipo: string, posicion: Vector3, escala: number?, color: Color3?)
	local r = TIPOS[tipo]
	local camara = Workspace.CurrentCamera
	if not r or activas >= MAX_ACTIVAS or not camara or (camara.CFrame.Position - posicion).Magnitude > DISTANCIA then
		return
	end
	local e = math.clamp(escala or 1, 0.2, 4)
	local soporte = Instance.new("Part")
	soporte.Anchored = true
	soporte.CanCollide = false
	soporte.CanQuery = false
	soporte.CanTouch = false
	soporte.Transparency = 1
	soporte.Size = Vector3.one * 0.2
	soporte.CFrame = CFrame.new(posicion)
	local adjunto = Instance.new("Attachment")
	adjunto.Parent = soporte
	soporte.Parent = carpeta
	local vida = 0
	for _, c in r.chorros do
		emitir(adjunto, c, e, color)
		vida = math.max(vida, c.vida[2])
	end
	if r.luz then
		local luz = Instance.new("PointLight")
		luz.Color = r.luz
		luz.Brightness = 6
		luz.Range = math.min(60, 22 * e)
		luz.Shadows = false
		luz.Parent = soporte
		TweenService:Create(luz, TweenInfo.new(0.6, Enum.EasingStyle.Quad), { Brightness = 0 }):Play()
	end
	if r.trozos then
		trozos(posicion, r.trozos, e)
	end
	local w = r.palabra
	if w and rng:NextNumber() <= (w.prob or 1) then
		Rafagas.palabra(posicion, w.textos[rng:NextInteger(1, #w.textos)], w.color, w.fondo, math.clamp(e, 0.7, 1.6) * (w.tam or 1), w.nube)
	end
	activas += 1
	task.delay(vida + 0.3, function()
		activas -= 1
		soporte:Destroy()
	end)
end

function Rafagas.iniciar()
	carpeta.Parent = Workspace
	local remoto = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Efecto") :: UnreliableRemoteEvent
	remoto.OnClientEvent:Connect(function(tipo, posicion, escala, color)
		if typeof(tipo) == "string" and typeof(posicion) == "Vector3" then
			Rafagas.lanzar(tipo, posicion, if typeof(escala) == "number" then escala else 1, if typeof(color) == "Color3" then color else nil)
		end
	end)
end

return Rafagas
