--!strict
local ReplicatedStorage = game:GetService("ReplicatedStorage")

export type Caja = { minimo: Vector3, maximo: Vector3 }
export type Avion = {
	helices: { { pos: Vector3, escala: number } },
	asiento: Vector3,
	ojos: { { centro: Vector3, radio: number } },
	humo: Vector3,
	canones: { Vector3 },
}

local Criaturas = {}

Criaturas.CARPETA = "ModelosCriaturas"

Criaturas.IDS = {
	PirataBarril = 137707221184730,
	PirataBanera = 107111592503824,
	PirataBarca = 79746753759268,
	HelicePirata = 117338072218053,
	PilotoPirata = 120664985159822,
	BrazoPirata = 140435021990962,
	Pajaro = 80841507845595,
	AlaPajaroIzq = 74877578935733,
	AlaPajaroDer = 72660726623917,
	PajaroMareado = 103374629783697,
	PajaroPlaf = 128779248727710,
} :: { [string]: number }

Criaturas.CAJAS = {
	PirataBarril = { minimo = Vector3.new(-10.672, -3.55, -6.05), maximo = Vector3.new(10.479, 6.84, 7.572) },
	PirataBanera = { minimo = Vector3.new(-10.054, -2.082, -6.4), maximo = Vector3.new(9.683, 6.34, 10) },
	PirataBarca = { minimo = Vector3.new(-10.2, -1.3, -5.65), maximo = Vector3.new(9.838, 6.94, 7.07) },
	HelicePirata = { minimo = Vector3.new(-3.8, -0.62, -1.15), maximo = Vector3.new(3.8, 0.62, 0.25) },
	PilotoPirata = { minimo = Vector3.new(-1.62, 0, -2.025), maximo = Vector3.new(1.62, 5.17, 2.693) },
	BrazoPirata = { minimo = Vector3.new(0.552, 1.682, -0.975), maximo = Vector3.new(2.097, 5.07, 0.379) },
	Pajaro = { minimo = Vector3.new(-0.95, -1.108, -2.489), maximo = Vector3.new(0.95, 1.658, 2.341) },
	AlaPajaroIzq = { minimo = Vector3.new(-3.35, -0.08, -0.62), maximo = Vector3.new(0, 0.08, 0.82) },
	AlaPajaroDer = { minimo = Vector3.new(0, -0.08, -0.62), maximo = Vector3.new(3.35, 0.08, 0.82) },
	PajaroMareado = { minimo = Vector3.new(-2.734, -2.387, -2.489), maximo = Vector3.new(2.734, 1.658, 2.341) },
	PajaroPlaf = { minimo = Vector3.new(-4.186, -2.617, -0.8), maximo = Vector3.new(4.186, 2.658, 0.159) },
} :: { [string]: Caja }

Criaturas.AVIONES = {
	PirataBarril = {
		helices = { { pos = Vector3.new(0, 0, -6.05), escala = 1.0 } },
		asiento = Vector3.new(0, 0.55, 0.75),
		ojos = { { centro = Vector3.new(-1.371, 2.111, -2.693), radio = 0.92 } },
		humo = Vector3.new(-2.85, 2.5, -2.6),
		canones = { Vector3.new(-2.6, -0.75, -4.1), Vector3.new(2.6, -0.75, -4.1) },
	},
	PirataBanera = {
		helices = { { pos = Vector3.new(0, 0.45, -6.45), escala = 1.0 } },
		asiento = Vector3.new(0, -0.45, 0.7),
		ojos = { { centro = Vector3.new(1.248, 1.718, -3.897), radio = 0.85 } },
		humo = Vector3.new(-0.65, 2.75, -5.2),
		canones = { Vector3.new(-2.25, 1, -2.9), Vector3.new(2.25, 1, -2.9) },
	},
	PirataBarca = {
		helices = { { pos = Vector3.new(0, 0.95, -5.7), escala = 0.9 } },
		asiento = Vector3.new(0, -0.65, 1),
		ojos = { { centro = Vector3.new(-0.661, 1.622, -3.271), radio = 0.8 } },
		humo = Vector3.new(-0.7, 2.9, -4.4),
		canones = { Vector3.new(-1.95, 0.35, -2.4), Vector3.new(1.95, 0.35, -2.4) },
	},
} :: { [string]: Avion }

Criaturas.VARIANTES = { "PirataBarril", "PirataBanera", "PirataBarca" }
Criaturas.HOMBRO = Vector3.new(0.93, 2.07, 0)
Criaturas.ALA = Vector3.new(-0.78, 0.38, 0)

function Criaturas.clonar(nombre: string, escala: number?): (Model?, { BasePart }, { CFrame })
	local partes: { BasePart } = {}
	local marcos: { CFrame } = {}
	local carpeta = ReplicatedStorage:FindFirstChild(Criaturas.CARPETA)
	local plantilla = carpeta and carpeta:FindFirstChild(nombre)
	if not plantilla or not plantilla:IsA("Model") then
		return nil, partes, marcos
	end
	local e = escala or 1
	local modelo = plantilla:Clone()
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true
			d.CastShadow = false
			d.Size *= e
			table.insert(partes, d)
			table.insert(marcos, CFrame.new(d.Position * e) * d.CFrame.Rotation)
		end
	end
	return modelo, partes, marcos
end

return Criaturas
