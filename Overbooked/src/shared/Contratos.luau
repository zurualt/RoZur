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
	return {
		origen = origen,
		destino = destino,
		distancia = rng:NextInteger(9, 16) * 100 + riesgo * 200,
		pasajeros = math.min(pasajeros, 32),
		carga = carga,
		riesgo = riesgo,
		pagoPasajero = 18 + riesgo * 8,
		multaPasajero = 60,
		entregaAerea = entregaAerea,
		titulo = elegir(TITULOS, rng),
	}
end

function Contratos.ciudadInicial(rng: Random): string
	return elegir(CIUDADES, rng)
end

return Contratos
