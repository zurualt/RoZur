--!strict
export type Carga = {
	tipo: string,
	cantidad: number,
	valor: number,
	entrega: boolean,
}

export type Contrato = {
	origen: string,
	destino: string,
	bioma: string,
	distancia: number,
	pasajeros: number,
	carga: { Carga },
	riesgo: number,
	pagoPasajero: number,
	multaPasajero: number,
	entregaAerea: boolean,
	titulo: string,
	condicion: string,
}

type Ciudad = { nombre: string, bioma: string }

local CIUDADES: { Ciudad } = {
	{ nombre = "Villaturbia", bioma = "Jungla" },
	{ nombre = "Puerto Maleta", bioma = "Ciudad" },
	{ nombre = "San Retraso", bioma = "Desierto" },
	{ nombre = "Nueva Escala", bioma = "Ciudad" },
	{ nombre = "Aerópolis", bioma = "Ciudad" },
	{ nombre = "Isla Equipaje", bioma = "Jungla" },
	{ nombre = "Monte Turbulento", bioma = "Nieve" },
	{ nombre = "Bahía Mareo", bioma = "Jungla" },
	{ nombre = "Cabo Cinturón", bioma = "Nieve" },
	{ nombre = "Valle Overbooking", bioma = "Nieve" },
	{ nombre = "Ciudad Embarque", bioma = "Ciudad" },
	{ nombre = "Llanos del Jet Lag", bioma = "Desierto" },
	{ nombre = "Dunas de la Demora", bioma = "Desierto" },
	{ nombre = "Cañón Facturado", bioma = "Desierto" },
	{ nombre = "Selva del Reembolso", bioma = "Jungla" },
	{ nombre = "Glaciar Objetos Perdidos", bioma = "Nieve" },
}

local TITULOS: { [string]: { string } } = {
	Jungla = { "Safari por la jungla", "Aterrizaje en plena jungla", "Jungla y mosquitos" },
	Nieve = { "Escapada a la nieve", "Pista helada en la nieve", "Nieve hasta las alas" },
	Desierto = { "Travesía del desierto", "Cañón rojo del desierto", "Polvo del desierto" },
	Ciudad = { "Puente aéreo a la ciudad", "Gran aeropuerto de la ciudad", "Ciudad de rascacielos" },
}

local NOMBRES_BIOMA: { [string]: string } = {
	Jungla = "Destino: jungla",
	Nieve = "Destino: nieve",
	Desierto = "Destino: desierto",
	Ciudad = "Destino: ciudad",
}

local Contratos = {}

Contratos.BIOMAS = { "Jungla", "Nieve", "Desierto", "Ciudad" }

Contratos.CONDICIONES = {
	Normal = { icono = "", texto = "", peso = 5 },
	Nocturno = { icono = "Luna", texto = "Vuelo nocturno (+15 %)", peso = 2 },
	Niebla = { icono = "Niebla", texto = "Niebla en destino (+20 %)", peso = 2 },
	VIP = { icono = "Diamante", texto = "Pasajeros VIP: pagan más y se impacientan antes", peso = 2 },
	Hambre = { icono = "Hamburguesa", texto = "Pasaje hambriento: piden el doble", peso = 2 },
	Fragil = { icono = "Fragil", texto = "Carga frágil de lujo", peso = 1 },
} :: { [string]: { icono: string, texto: string, peso: number } }

local ORDEN_CONDICIONES = { "Normal", "Nocturno", "Niebla", "VIP", "Hambre", "Fragil" }

local function condicion(rng: Random): string
	local total = 0
	for _, n in ORDEN_CONDICIONES do
		total += Contratos.CONDICIONES[n].peso
	end
	local tirada = rng:NextNumber() * total
	for _, n in ORDEN_CONDICIONES do
		tirada -= Contratos.CONDICIONES[n].peso
		if tirada <= 0 then
			return n
		end
	end
	return "Normal"
end

local function elegir<T>(lista: { T }, rng: Random): T
	return lista[rng:NextInteger(1, #lista)]
end

function Contratos.bioma(destino: any, bioma: any): string
	if typeof(bioma) == "string" and TITULOS[bioma] then
		return bioma
	end
	if typeof(destino) ~= "string" then
		return Contratos.BIOMAS[1]
	end
	for _, c in CIUDADES do
		if c.nombre == destino then
			return c.bioma
		end
	end
	local suma = 0
	for i = 1, #destino do
		suma = (suma * 31 + string.byte(destino, i)) % 1000003
	end
	return Contratos.BIOMAS[suma % #Contratos.BIOMAS + 1]
end

function Contratos.generar(rng: Random, origen: string): Contrato
	local riesgo = rng:NextInteger(1, 3)
	local ciudad = elegir(CIUDADES, rng)
	while ciudad.nombre == origen do
		ciudad = elegir(CIUDADES, rng)
	end
	local carga: { Carga } = {}
	table.insert(carga, { tipo = "Maleta", cantidad = rng:NextInteger(4, 8), valor = 15, entrega = false })
	table.insert(carga, { tipo = "Caja", cantidad = rng:NextInteger(1, 3), valor = 60, entrega = false })
	if rng:NextNumber() < 0.6 then
		table.insert(carga, { tipo = "CajaFragil", cantidad = rng:NextInteger(1, 3), valor = 110, entrega = false })
	end
	local entregaAerea = rng:NextNumber() < 0.45
	if entregaAerea then
		table.insert(carga, { tipo = "Caja", cantidad = rng:NextInteger(1, 2), valor = 180, entrega = true })
	end
	if riesgo >= 2 and rng:NextNumber() < 0.5 then
		table.insert(carga, { tipo = "Jaula", cantidad = 1, valor = 400, entrega = false })
	end
	local especial: string? = nil
	if riesgo >= 2 and rng:NextNumber() < 0.35 then
		table.insert(carga, { tipo = "Piano", cantidad = 1, valor = 700, entrega = false })
		especial = "Mudanza: incluye un piano de cola"
	end
	if rng:NextNumber() < 0.15 + riesgo * 0.1 then
		table.insert(carga, { tipo = "Bombona", cantidad = rng:NextInteger(3, 5), valor = 60, entrega = false })
		especial = if especial then "Piano y bombonas de gas: ¿qué puede salir mal?" else "Gas a presión: prohibido fumar"
	end
	local pasajeros = rng:NextInteger(10, 20) + riesgo * 4
	local c = condicion(rng)
	local pago = 18 + riesgo * 8
	local multa = 60
	if c == "Nocturno" then
		pago *= 1.15
	elseif c == "Niebla" then
		pago *= 1.2
	elseif c == "VIP" then
		pago *= 1.6
		multa *= 1.5
		pasajeros = math.floor(pasajeros * 0.7)
	elseif c == "Hambre" then
		pago *= 1.1
	elseif c == "Fragil" then
		table.insert(carga, { tipo = "CajaFragil", cantidad = rng:NextInteger(3, 5), valor = 140, entrega = false })
	end
	return {
		origen = origen,
		destino = ciudad.nombre,
		bioma = ciudad.bioma,
		distancia = rng:NextInteger(9, 16) * 100 + riesgo * 200,
		pasajeros = math.min(pasajeros, 32),
		carga = carga,
		riesgo = riesgo,
		pagoPasajero = math.floor(pago),
		multaPasajero = math.floor(multa),
		entregaAerea = entregaAerea,
		titulo = if especial then `{especial} · {NOMBRES_BIOMA[ciudad.bioma]}` else elegir(TITULOS[ciudad.bioma], rng),
		condicion = c,
	}
end

function Contratos.ciudadInicial(rng: Random): string
	return elegir(CIUDADES, rng).nombre
end

return Contratos
