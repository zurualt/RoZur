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

local CIUDADES = {
	"Villaturbia",
	"Puerto Maleta",
	"San Retraso",
	"Nueva Escala",
	"Aerópolis",
	"Isla Equipaje",
	"Monte Turbulento",
	"Bahía Mareo",
	"Cabo Cinturón",
	"Valle Overbooking",
	"Ciudad Embarque",
	"Llanos del Jet Lag",
}

local TITULOS = {
	"Vuelo tranquilo (en teoría)",
	"Puente aéreo low cost",
	"Ruta panorámica",
	"Mercancía especial",
	"Charter turístico",
	"Vuelo exprés",
}

local Contratos = {}

Contratos.CONDICIONES = {
	Normal = { icono = "", texto = "", peso = 5 },
	Nocturno = { icono = "🌙", texto = "Vuelo nocturno (+15 %)", peso = 2 },
	Niebla = { icono = "🌫", texto = "Niebla en destino (+20 %)", peso = 2 },
	VIP = { icono = "💎", texto = "Pasajeros VIP: pagan más y se impacientan antes", peso = 2 },
	Hambre = { icono = "🍔", texto = "Pasaje hambriento: piden el doble", peso = 2 },
	Fragil = { icono = "🍷", texto = "Carga frágil de lujo", peso = 1 },
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

function Contratos.generar(rng: Random, origen: string): Contrato
	local riesgo = rng:NextInteger(1, 3)
	local destino = elegir(CIUDADES, rng)
	while destino == origen do
		destino = elegir(CIUDADES, rng)
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
		destino = destino,
		distancia = rng:NextInteger(9, 16) * 100 + riesgo * 200,
		pasajeros = math.min(pasajeros, 32),
		carga = carga,
		riesgo = riesgo,
		pagoPasajero = math.floor(pago),
		multaPasajero = math.floor(multa),
		entregaAerea = entregaAerea,
		titulo = elegir(TITULOS, rng),
		condicion = c,
	}
end

function Contratos.ciudadInicial(rng: Random): string
	return elegir(CIUDADES, rng)
end

return Contratos
