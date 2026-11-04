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
}

type Trozos = { cantidad: number, color: Color3, material: Enum.Material, tam: Vector3, transparencia: number? }

type Rafaga = { chorros: { Chorro }, luz: Color3?, trozos: Trozos? }

local Rafagas = {}

local MAX_ACTIVAS = 16
local DISTANCIA = 250
local activas = 0
local rng = Random.new()
local carpeta = Instance.new("Folder")
carpeta.Name = "Rafagas"

local CAIDA = Vector3.new(0, -40, 0)
local HUMO_OSCURO = Color3.fromRGB(78, 74, 72)
local GRIS = Color3.fromRGB(196, 194, 190)
local ARENA = Color3.fromRGB(240, 214, 150)
local AGUA = Color3.fromRGB(143, 211, 244)
local ORO = Color3.fromRGB(255, 214, 110)
local HORIZONTAL = Enum.ParticleOrientation.VelocityPerpendicular

local function confeti(textura: string, color: Color3): Chorro
	return { textura = textura, cuenta = 7, tam = { 0.9, 0.9 }, vida = { 2.4, 3.4 }, velocidad = { 20, 34 }, color = color, esparcir = 55, gravedad = Vector3.new(0, -16, 0), arrastre = 1.2, giro = 420 }
end

local CONFETI = {
	confeti("Confeti", Color3.fromRGB(242, 123, 43)),
	confeti("Confeti", Color3.fromRGB(31, 166, 160)),
	confeti("ConfetiPunto", Color3.fromRGB(246, 196, 69)),
	confeti("ConfetiPunto", Color3.fromRGB(242, 155, 178)),
	confeti("Confeti", Color3.fromRGB(109, 190, 69)),
}

local TIPOS: { [string]: Rafaga } = {
	Explosion = {
		luz = Color3.fromRGB(255, 160, 60),
		trozos = { cantidad = 7, color = Color3.fromRGB(70, 70, 76), material = Enum.Material.SmoothPlastic, tam = Vector3.new(0.9, 0.5, 0.7) },
		chorros = {
			{ textura = "Destello", cuenta = 1, tam = { 6, 18 }, vida = { 0.18, 0.22 }, velocidad = { 0, 0 }, luz = 1 },
			{ textura = "Explosion", cuenta = 3, tam = { 5, 12 }, vida = { 0.35, 0.55 }, velocidad = { 1, 5 }, giro = 60 },
			{ textura = "Humo1", cuenta = 6, tam = { 3, 9 }, vida = { 1.4, 2.4 }, velocidad = { 8, 16 }, color = HUMO_OSCURO, arrastre = 2.5, gravedad = Vector3.new(0, 4, 0), giro = 40, transparencia = { 0.05, 1 } },
			{ textura = "Humo2", cuenta = 5, tam = { 3, 8 }, vida = { 1.2, 2 }, velocidad = { 8, 14 }, color = HUMO_OSCURO, arrastre = 2.5, gravedad = Vector3.new(0, 4, 0), giro = 40, transparencia = { 0.05, 1 } },
			{ textura = "Chispa", cuenta = 26, tam = { 0.9, 0 }, vida = { 0.5, 0.9 }, velocidad = { 25, 50 }, luz = 1, gravedad = CAIDA, color = ORO },
			{ textura = "Onda", cuenta = 1, tam = { 1, 26 }, vida = { 0.4, 0.4 }, velocidad = { 0.05, 0.05 }, esparcir = 0, orientacion = HORIZONTAL, transparencia = { 0.1, 1 } },
		},
	},
	ExplosionPequena = {
		luz = Color3.fromRGB(255, 170, 70),
		chorros = {
			{ textura = "Destello", cuenta = 1, tam = { 3, 8 }, vida = { 0.15, 0.18 }, velocidad = { 0, 0 }, luz = 1 },
			{ textura = "Explosion", cuenta = 2, tam = { 2.5, 6 }, vida = { 0.3, 0.45 }, velocidad = { 1, 3 }, giro = 60 },
			{ textura = "Humo3", cuenta = 5, tam = { 1.5, 5 }, vida = { 1, 1.8 }, velocidad = { 5, 10 }, color = HUMO_OSCURO, arrastre = 2.5, gravedad = Vector3.new(0, 3, 0), giro = 40 },
			{ textura = "Chispa", cuenta = 12, tam = { 0.6, 0 }, vida = { 0.4, 0.7 }, velocidad = { 18, 32 }, luz = 1, gravedad = CAIDA, color = ORO },
		},
	},
	Humo = {
		chorros = {
			{ textura = "Humo1", cuenta = 3, tam = { 2, 6 }, vida = { 1.4, 2.2 }, velocidad = { 3, 7 }, color = GRIS, tinte = true, arrastre = 1, gravedad = Vector3.new(0, 5, 0), giro = 40, esparcir = 40 },
			{ textura = "Humo2", cuenta = 3, tam = { 2, 6 }, vida = { 1.4, 2.2 }, velocidad = { 3, 7 }, color = GRIS, tinte = true, arrastre = 1, gravedad = Vector3.new(0, 5, 0), giro = 40, esparcir = 40 },
			{ textura = "Humo3", cuenta = 2, tam = { 1.5, 5 }, vida = { 1.2, 2 }, velocidad = { 3, 7 }, color = GRIS, tinte = true, arrastre = 1, gravedad = Vector3.new(0, 5, 0), giro = 40, esparcir = 40 },
		},
	},
	Chispas = {
		luz = Color3.fromRGB(255, 220, 140),
		chorros = {
			{ textura = "Destello", cuenta = 1, tam = { 1.2, 3 }, vida = { 0.1, 0.12 }, velocidad = { 0, 0 }, luz = 1, color = ORO, tinte = true },
			{ textura = "Chispa", cuenta = 22, tam = { 0.6, 0 }, vida = { 0.3, 0.6 }, velocidad = { 14, 28 }, luz = 1, gravedad = CAIDA, color = ORO, tinte = true, esparcir = 70, giro = 180 },
		},
	},
	Polvo = {
		chorros = {
			{ textura = "Polvo", cuenta = 10, tam = { 2, 6 }, vida = { 0.8, 1.4 }, velocidad = { 6, 12 }, color = Color3.fromRGB(230, 215, 190), tinte = true, esparcir = 85, arrastre = 3, giro = 30, transparencia = { 0.1, 1 } },
		},
	},
	Arena = {
		chorros = {
			{ textura = "Polvo", cuenta = 8, tam = { 1.5, 5 }, vida = { 0.8, 1.3 }, velocidad = { 5, 10 }, color = ARENA, tinte = true, esparcir = 85, arrastre = 3, giro = 30 },
			{ textura = "ConfetiPunto", cuenta = 18, tam = { 0.22, 0.1 }, vida = { 0.5, 0.9 }, velocidad = { 10, 18 }, color = ARENA, tinte = true, esparcir = 60, gravedad = CAIDA },
		},
	},
	Estrellas = {
		chorros = {
			{ textura = "Estrella", cuenta = 6, tam = { 1.6, 0.5 }, vida = { 0.6, 0.9 }, velocidad = { 8, 14 }, esparcir = 70, gravedad = Vector3.new(0, -25, 0), giro = 240 },
			{ textura = "Chispa", cuenta = 6, tam = { 0.8, 0 }, vida = { 0.2, 0.35 }, velocidad = { 6, 12 }, luz = 1, color = ORO },
		},
	},
	Confeti = { chorros = CONFETI },
	Salpicadura = {
		chorros = {
			{ textura = "Corona", cuenta = 1, tam = { 2, 3.6 }, vida = { 0.25, 0.3 }, velocidad = { 0, 0 }, color = AGUA, tinte = true },
			{ textura = "Gota", cuenta = 16, tam = { 0.6, 0.2 }, vida = { 0.4, 0.8 }, velocidad = { 10, 20 }, color = AGUA, tinte = true, esparcir = 60, gravedad = Vector3.new(0, -55, 0), orientacion = Enum.ParticleOrientation.VelocityParallel },
		},
	},
	Escombros = {
		trozos = { cantidad = 6, color = Color3.fromRGB(150, 150, 156), material = Enum.Material.Metal, tam = Vector3.new(0.7, 0.3, 0.6) },
		chorros = {
			{ textura = "Escombro", cuenta = 10, tam = { 1, 0.6 }, vida = { 0.8, 1.3 }, velocidad = { 14, 26 }, color = GRIS, tinte = true, esparcir = 75, gravedad = CAIDA, giro = 300 },
			{ textura = "Humo3", cuenta = 4, tam = { 1.5, 4 }, vida = { 0.8, 1.4 }, velocidad = { 4, 8 }, color = GRIS, arrastre = 2, giro = 40 },
		},
	},
	Astillas = {
		trozos = { cantidad = 5, color = Color3.fromRGB(201, 154, 91), material = Enum.Material.Wood, tam = Vector3.new(1.1, 0.2, 0.3) },
		chorros = {
			{ textura = "Astilla", cuenta = 14, tam = { 1.2, 0.8 }, vida = { 0.7, 1.2 }, velocidad = { 12, 24 }, esparcir = 75, gravedad = CAIDA, giro = 360 },
			{ textura = "Polvo", cuenta = 3, tam = { 1.5, 4 }, vida = { 0.6, 1 }, velocidad = { 3, 6 }, color = Color3.fromRGB(220, 200, 170), arrastre = 2 },
		},
	},
	Cristales = {
		trozos = { cantidad = 4, color = Color3.fromRGB(190, 230, 245), material = Enum.Material.Glass, tam = Vector3.new(0.5, 0.1, 0.4), transparencia = 0.3 },
		chorros = {
			{ textura = "Cristal", cuenta = 14, tam = { 0.9, 0.5 }, vida = { 0.6, 1 }, velocidad = { 12, 22 }, esparcir = 75, gravedad = CAIDA, giro = 360 },
			{ textura = "Chispa", cuenta = 8, tam = { 0.7, 0 }, vida = { 0.3, 0.5 }, velocidad = { 6, 12 }, luz = 1 },
		},
	},
	Monedas = {
		chorros = {
			{ textura = "Moneda", cuenta = 12, tam = { 1.1, 0.8 }, vida = { 0.9, 1.4 }, velocidad = { 14, 24 }, esparcir = 40, gravedad = Vector3.new(0, -35, 0), giro = 200 },
			{ textura = "Chispa", cuenta = 10, tam = { 0.7, 0 }, vida = { 0.3, 0.6 }, velocidad = { 6, 14 }, luz = 1, color = ORO },
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
			{ textura = "Humo1", cuenta = 6, tam = { 2, 7 }, vida = { 2, 3 }, velocidad = { 4, 8 }, color = Color3.fromRGB(242, 170, 170), tinte = true, gravedad = Vector3.new(0, 6, 0), arrastre = 1, giro = 40 },
		},
	},
	Vapor = {
		chorros = {
			{ textura = "Vapor", cuenta = 8, tam = { 1.5, 4 }, vida = { 1, 1.8 }, velocidad = { 3, 7 }, color = Color3.fromRGB(240, 242, 246), esparcir = 40, gravedad = Vector3.new(0, 4, 0), arrastre = 1, giro = 40 },
		},
	},
	Plumas = {
		chorros = {
			{ textura = "Pluma", cuenta = 12, tam = { 1, 0.8 }, vida = { 2, 3.5 }, velocidad = { 6, 14 }, esparcir = 180, gravedad = Vector3.new(0, -4, 0), arrastre = 2, giro = 200 },
		},
	},
	Onda = {
		chorros = {
			{ textura = "Onda", cuenta = 1, tam = { 1, 16 }, vida = { 0.45, 0.45 }, velocidad = { 0.05, 0.05 }, esparcir = 0, color = Color3.fromRGB(255, 255, 255), tinte = true, orientacion = HORIZONTAL, transparencia = { 0, 1 } },
		},
	},
}

local function emitir(adjunto: Attachment, c: Chorro, escala: number, color: Color3?)
	local e = Instance.new("ParticleEmitter")
	e.Texture = VFX.textura(c.textura)
	e.Enabled = false
	e.Size = NumberSequence.new(c.tam[1] * escala, c.tam[2] * escala)
	local t = c.transparencia
	e.Transparency = NumberSequence.new(if t then t[1] else 0, if t then t[2] else 1)
	e.Lifetime = NumberRange.new(c.vida[1], c.vida[2])
	e.Speed = NumberRange.new(c.velocidad[1] * escala, c.velocidad[2] * escala)
	local abrir = c.esparcir or 180
	e.SpreadAngle = Vector2.new(abrir, abrir)
	e.Acceleration = (c.gravedad or Vector3.zero) * math.sqrt(escala)
	e.Drag = c.arrastre or 0
	e.Rotation = NumberRange.new(0, 360)
	e.RotSpeed = NumberRange.new(-(c.giro or 0), c.giro or 0)
	e.LightEmission = c.luz or 0
	e.Color = ColorSequence.new(if c.tinte and color then color else c.color or Color3.new(1, 1, 1))
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
