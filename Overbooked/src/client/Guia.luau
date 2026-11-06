--!strict
local CollectionService = game:GetService("CollectionService")
local GuiService = game:GetService("GuiService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Gui = require(ReplicatedStorage.Shared.Gui)
local Agarre = require(script.Parent.Agarre)
local Cine = require(script.Parent.Cine)
local Interfaz = require(script.Parent.Interfaz)
local Piloto = require(script.Parent.Piloto)
local Sonido = require(script.Parent.Sonido)

type Objetivo = BasePart | Vector3
type Tarea = { clave: string, icono: string, texto: string, hecho: boolean, objetivo: Objetivo?, info: boolean?, fallo: boolean?, actual: boolean? }
type Fila = { marco: Frame, resalte: ImageLabel, casilla: ImageLabel, marca: ImageLabel, icono: ImageLabel, texto: TextLabel, clave: string, fuente: string, hecho: boolean }
type Tarjeta = { clave: string, fase: string?, titulo: string, meta: string, puntos: { { string } } }

local Guia = {}

local jugador = Players.LocalPlayer
local Estado = ReplicatedStorage:WaitForChild("Estado")
local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local avion = Workspace:WaitForChild("Avion") :: Model
local TACTIL = Gui.tactil()
local MANDO = not TACTIL and UserInputService.GamepadEnabled and not UserInputService.KeyboardEnabled
local V = Config.VUELO
local MAX_FILAS = 5
local ANCHO = 370
local POSICION_PANEL = UDim2.new(0, 14, 0.27, 0)
local COMIDA: { [string]: boolean } = { Bandeja = true, Hamburguesa = true, Cafe = true, Agua = true }

local function tarjeta(clave: string, fase: string?, titulo: string, meta: string, puntos: { { string } }): Tarjeta
	return { clave = clave, fase = fase, titulo = titulo, meta = meta, puntos = puntos }
end

local FASES: { [string]: Tarjeta } = {
	Aeropuerto = tarjeta("Aeropuerto", "Aeropuerto", "LA TERMINAL", "Elegid un vuelo y entrad juntos en su puerta", {
		{ "Billete", "Los vuelos están en el tablero de SALIDAS" },
		{ "Diana", "El primero en pisar el círculo es el capitán de la sala" },
		{ "Moneda", "¿Dinero ganado? Gástalo en la tienda libre de impuestos" },
	}),
	Preparacion = tarjeta("Preparacion", "Preparacion", "¡A CARGAR EL AVIÓN!", "Con todo listo se abre la puerta del hangar", {
		{ "Maleta", "Maletas de los toboganes al carro" },
		{ "Combustible", "Bombea en el surtidor hasta el 100 %" },
		{ "Volante", "Después, el tractor lleva el carro al avión" },
	}),
	Embarque = tarjeta("Embarque", "Embarque", "¡EMBARQUE!", "Todos dentro antes de despegar", {
		{ "Maleta", "Maletas del carro a la bodega" },
		{ "Avion", "Se entra por la rampa de atrás" },
		{ "Volante", "Que alguien se siente a pilotar" },
	}),
	Despegue = tarjeta("Despegue", "Vuelo", "¡A DESPEGAR!", "Alguien tiene que pilotar este trasto", {
		{ "Volante", "Asiento izquierdo de la cabina (G)" },
		{ "Avion", `Acelera (Shift) hasta {V.VELOCIDAD_DESPEGUE} km/h` },
		{ "Flecha", "Y sube (W) para despegar" },
	}),
	Vuelo = tarjeta("Vuelo", "Vuelo", "¡EN EL AIRE!", "Pasajeros contentos y el avión de una pieza", {
		{ "Hamburguesa", "Comida de la cocina a quien la pida (E)" },
		{ "Extintor", "¿Fuego? Extintor y mantén F" },
		{ "Maleta", "¿Agujero? Tápalo con una maleta" },
	}),
	Aterrizaje = tarjeta("Aterrizaje", "Vuelo", "¡A ATERRIZAR!", "Bajad a la pista con suavidad", {
		{ "Aterrizaje", `Toca suelo a menos de {V.VELOCIDAD_ATERRIZAJE} km/h` },
		{ "Flecha", "Baja despacio (S) y con las alas rectas" },
		{ "Cinturon", "Los demás: ¡sentaos y agarraos!" },
	}),
	Isla = tarjeta("Isla", "Isla", "¡NÁUFRAGOS!", "Pedid rescate antes de que se acabe el tiempo", {
		{ "Radio", "3 piezas de radio a la estación" },
		{ "Tronco", "3 troncos a la hoguera" },
		{ "Bengala", "Y enciéndela con la bengala" },
	}),
	Resultados = tarjeta("Resultados", nil, "¡DÍA DE COBRO!", "El dinero se reparte entre toda la tripulación", {
		{ "Moneda", "Gástalo en la tienda libre de impuestos" },
		{ "Estrella", "Cada vuelo: más pasajeros, más caos, más paga" },
	}),
}

local SUCESOS: { [string]: Tarjeta } = {
	Fuego = tarjeta("Fuego", "Vuelo", "¡FUEGO A BORDO!", "Apágalo antes de que se extienda", {
		{ "Extintor", "Coge un extintor" },
		{ "Fuego", "Apunta a las llamas y mantén F" },
		{ "Agua", "El agua también vale" },
	}),
	Agujero = tarjeta("Agujero", "Vuelo", "¡AGUJERO EN EL CASCO!", "Se lo traga todo, ¡pasajeros incluidos!", {
		{ "Maleta", "Lánzale una maleta para taparlo" },
		{ "Llave", "Luego repáralo con la llave (F)" },
	}),
	Panel = tarjeta("Panel", "Vuelo", "¡PANEL SUELTO!", "Se arregla por fuera... en pleno vuelo", {
		{ "Llave", "Coge el piolet de la bodega" },
		{ "Avion", "Sal al ala y trepa por el casco" },
		{ "Golpe", "Clávalo a martillazos (F)" },
	}),
	Pajaros = tarjeta("Pajaros", "Vuelo", "¡PÁJAROS!", "Si se cuelan en un motor, arde", {
		{ "Motor", "Vigila los motores" },
		{ "Fuego", "Motor en llamas: extintor de motores de la cabina" },
	}),
	MotorFuego = tarjeta("MotorFuego", "Vuelo", "¡MOTOR EN LLAMAS!", "Se apaga desde la cabina", {
		{ "Fuego", "Pulsa el extintor de motores (E)" },
		{ "Motor", "Luego reinicia los motores (E)" },
	}),
	MotorApagado = tarjeta("MotorApagado", "Vuelo", "¡MOTOR APAGADO!", "Volamos con uno solo... de momento", {
		{ "Motor", "Botón de los motores en la cabina (E)" },
	}),
	CaidaLibre = tarjeta("CaidaLibre", "Vuelo", "¡CAÍDA LIBRE!", "Todo flota... y luego cae", {
		{ "Cinturon", "Siéntate (G) o agárrate a algo" },
	}),
	Tormenta = tarjeta("Tormenta", "Vuelo", "¡TORMENTA!", "Rayos, lluvia y botes sin parar", {
		{ "Cinturon", "Cinturones puestos" },
		{ "Volante", "Piloto: mantén el rumbo" },
	}),
	Piratas = tarjeta("Piratas", "Vuelo", "¡AVIONES PIRATA!", "Le disparan al casco", {
		{ "Pirata", "Corre a la torreta del ala izquierda" },
		{ "Diana", "Siéntate y dispara con clic" },
	}),
	Turbulencia = tarjeta("Turbulencia", "Vuelo", "¡TURBULENCIAS!", "Todo se mueve: agárrate", {
		{ "Cinturon", "Sentado (G) no te caes" },
		{ "Maleta", "Los altillos se abren: ciérralos (T)" },
		{ "Cafe", "Cuidado con la comida y el café" },
	}),
	Alborotador = tarjeta("Alborotador", "Vuelo", "¡PASAJERO ALBOROTADOR!", "Va dando tumbos por el pasillo", {
		{ "Mano", "Cógelo y siéntalo" },
		{ "Corazon", "Cálmalo (mantén R)" },
	}),
	Cabra = tarjeta("Cabra", "Vuelo", "¡CABRA SUELTA!", "Embiste y se come la comida", {
		{ "Mano", "Cógela" },
		{ "Maleta", "Lánzala a la bodega" },
	}),
	Gallinas = tarjeta("Gallinas", "Vuelo", "¡GALLINAS SUELTAS!", "Picotean a todo el que pasa", {
		{ "Mano", "Cógelas una a una" },
		{ "Maleta", "A la bodega con ellas" },
	}),
	Bebe = tarjeta("Bebe", "Vuelo", "¡BEBÉ LLORÓN!", "Toda la fila está a punto de estallar", {
		{ "Bandeja", "Coge el biberón de la cocina" },
		{ "Pasajero", "Dáselo a su familia (E)" },
	}),
	Bano = tarjeta("Bano", "Vuelo", "¡ATRAPADO EN EL BAÑO!", "Alguien no puede salir", {
		{ "Mano", "Tira de la puerta del baño (E)" },
	}),
	Cafetera = tarjeta("Cafetera", "Vuelo", "¡CAFETERA LOCA!", "Si explota, prende fuego", {
		{ "Llave", "Coge la llave inglesa" },
		{ "Golpe", "Dale con F hasta que se calme" },
	}),
	Salida = tarjeta("Salida", "Vuelo", "¡QUIERE ABRIR LA SALIDA!", "Un pasajero va directo a la salida de emergencia", {
		{ "Mano", "Cógelo o placadle" },
		{ "Alarma", "Si la abre, cierra la puerta (E)" },
	}),
	Peste = tarjeta("Peste", "Vuelo", "¡PESTE A PESCADO!", "Una nube verde que marea a todo el mundo", {
		{ "Extintor", "Dispérsala con el extintor (F)" },
	}),
	Disco = tarjeta("Disco", "Vuelo", "¡TURBULENCIA DISCO!", "Todo el avión bota al ritmo", {
		{ "Estrella", "Baila y aguanta: se pasa sola" },
	}),
	Borracho = tarjeta("Borracho", "Vuelo", "¡AUTOPILOTO BORRACHO!", "Se ha bebido el champán de primera", {
		{ "Volante", "Ve a la cabina" },
		{ "Info", "Desconéctalo 3 veces (E)" },
	}),
	Estornudo = tarjeta("Estornudo", "Vuelo", "¡ALERGIA!", "Un pasajero estornuda encima de todos", {
		{ "Agua", "Dale un vaso de agua (E)" },
	}),
	Carrito = tarjeta("Carrito", "Vuelo", "¡CARRITO DESBOCADO!", "El carrito de comida va solo por el pasillo", {
		{ "Mano", "Cógelo para pararlo" },
	}),
	Avalancha = tarjeta("Avalancha", "Vuelo", "¡AVALANCHA DE EQUIPAJE!", "Llueven maletas de los altillos", {
		{ "Casco", "¡Cuidado con la cabeza!" },
	}),
}

local CAOS: { [string]: { string } } = {
	Cabra = { "Mano", "Lleva la cabra a la bodega" },
	Gallinas = { "Mano", "Lleva las gallinas a la bodega" },
	Bebe = { "Bandeja", "Lleva el biberón de la cocina al bebé" },
	Bano = { "Mano", "Tira de la puerta del baño (E)" },
	Cafetera = { "Llave", "Arregla la cafetera con la llave (F)" },
	Salida = { "Alarma", "¡Para al pasajero de la salida de emergencia!" },
	Peste = { "Extintor", "Dispersa la peste con el extintor (F)" },
	Disco = { "Estrella", "Baila: se pasa sola", "info" },
	Borracho = { "Volante", "Desconecta el piloto automático 3 veces (E)" },
	Estornudo = { "Agua", "Dale agua al pasajero alérgico (E)" },
	Carrito = { "Mano", "Coge el carrito desbocado" },
	Avalancha = { "Casco", "¡Cuidado con las maletas!", "info" },
}

local PISTAS: { [string]: { string } } = {
	Pedido = { "Hamburguesa", "¿Ves la burbuja? Es su pedido: tráelo de la cocina y pulsa E" },
	Fuego = { "Extintor", "¡Fuego! Coge un extintor y mantén F apuntando a las llamas" },
	Agujero = { "Llave", "¡Agujero! Lánzale una maleta y luego repáralo con la llave (F)" },
	Cabina = { "Volante", "Cabina: siéntate a la izquierda (G) para pilotar" },
	Torreta = { "Pirata", "Torreta: siéntate (G) y dispara a los piratas con clic" },
	Tractor = { "Volante", "Tractor: súbete al asiento y conduce con WASD" },
	Surtidor = { "Combustible", "Surtidor: mantén E una y otra vez hasta el 100 %" },
	CocoPrep = { "Cocodrilo", "Cocodrilo: dale la merienda del cubo, cógelo y suéltalo junto a su jaula" },
	Coco = { "Cocodrilo", "Cocodrilo: persigue la comida. Lánzale una hamburguesa y se calma" },
}

local CONTROLES: { [string]: { { string } } } = {
	teclado = {
		{ "Mano", "Clic: coger y soltar · Clic der.: lanzar" },
		{ "Llave", "E: interactuar · F: usar · G: sentarte" },
		{ "Info", "H: controles · O: ajustes · M: música" },
	},
	tactil = {
		{ "Mano", "Botones Coger, Lanzar y Usar a la derecha" },
		{ "Info", "Toca las etiquetas para interactuar" },
		{ "Volante", "Pilota con el joystick y Gas+ / Gas-" },
	},
	mando = {
		{ "Mano", "R2: coger y soltar · L2: lanzar" },
		{ "Llave", "X: usar · Y: sentarte · B: altillos" },
		{ "Volante", "Sticks para moverte y pilotar" },
	},
}

local PAGINAS: { Tarjeta } = {
	tarjeta("ComoJugar", nil, "¡BIENVENIDO A OVERBOOKED!", "Sois la tripulación de la peor aerolínea del mundo. Llevad a los pasajeros a su destino... más o menos enteros.", {
		{ "Maleta", "Cargad el equipaje y el combustible" },
		{ "Hamburguesa", "Servid comida a los pasajeros" },
		{ "Fuego", "Apagad fuegos, tapad agujeros y sobrevivid" },
	}),
	tarjeta("ComoJugar", nil, "CÓMO EMPEZAR UN VUELO", "Mira el tablero de SALIDAS y entrad juntos en la puerta del vuelo que queráis.", {
		{ "Billete", "3 vuelos: ruta, pasajeros, riesgo y paga" },
		{ "Diana", "El primero en pisar el círculo es el capitán (hasta 4)" },
		{ "Estrella", "El capitán elige quién entra y pulsa DESPEGAR" },
	}),
	tarjeta("ComoJugar", nil, "CONTROLES", "Lo básico. Todo lo demás, en Ajustes → Controles.", CONTROLES[if TACTIL then "tactil" elseif MANDO then "mando" else "teclado"]),
}

local visto: { [string]: number } = {}
local enSesion: { [string]: boolean } = {}
local remotoVisto: RemoteEvent? = nil
local gui: ScreenGui
local panel: ImageLabel
local escalaPanel: UIScale
local flechaPanel: ImageLabel
local plegado = Gui.pequena()
local filas: { Fila } = {}
local escalas: { UIScale } = {}
local nota: ImageLabel
local notaIcono: ImageLabel
local notaTexto: TextLabel
local notaEscala: UIScale
local notaId = 0
local ancla: Part
local marca: BillboardGui
local marcaAro: ImageLabel
local marcaIcono: ImageLabel
local marcaDistancia: TextLabel
local marcaFlecha: ImageLabel
local borde: Frame
local bordeFlecha: ImageLabel
local objetivo: Objetivo? = nil
local objetivoIcono = "Info"
local cola: { Tarjeta } = {}
local tarjetaAbierta: Tarjeta? = nil
local saltarTarjeta = false
local comoAbierto = false
local cacheAvion: { [string]: BasePart } = {}
local salas: { BasePart } = {}
local escaneoSalas = 0
local dispensadorCache: BasePart? = nil

local function cadena(o: Instance, nombre: string): string
	local v = o:GetAttribute(nombre)
	return if typeof(v) == "string" then v else ""
end

local function numero(o: Instance, nombre: string): number
	local v = o:GetAttribute(nombre)
	return if typeof(v) == "number" then v else 0
end

local function fase(): string
	return cadena(Estado, "Fase")
end

local function reloj(segundos: number): string
	return string.format("%d:%02d", math.floor(segundos / 60), segundos % 60)
end

local function raiz(): BasePart?
	local p = jugador.Character
	local r = p and p:FindFirstChild("HumanoidRootPart")
	return if r and r:IsA("BasePart") then r else nil
end

local function sentadoEn(): string
	local p = jugador.Character
	local h = p and p:FindFirstChildOfClass("Humanoid")
	local s = h and h.SeatPart
	return if s then s.Name else ""
end

local function sostenido(): string
	local o = Agarre.sostenido()
	return if o then Agarre.tipo(o) else ""
end

local function parteDe(o: Instance?): BasePart?
	if not o then
		return nil
	elseif o:IsA("BasePart") then
		return o
	elseif o:IsA("Model") then
		local c = o:FindFirstChild("Cuerpo")
		return if c and c:IsA("BasePart") then c else o.PrimaryPart
	end
	return nil
end

local function portado(o: Instance): boolean
	local p = o:GetAttribute("Portador")
	return typeof(p) == "number" and p ~= 0
end

local function cercana(lista: { Instance }, filtro: ((Instance) -> boolean)?): BasePart?
	local r = raiz()
	local desde = if r then r.Position else Workspace.CurrentCamera.CFrame.Position
	local mejor: BasePart? = nil
	local distancia = math.huge
	for _, o in lista do
		if filtro == nil or filtro(o) then
			local p = parteDe(o)
			if p and p:IsDescendantOf(Workspace) then
				local d = (p.Position - desde).Magnitude
				if d < distancia then
					mejor, distancia = p, d
				end
			end
		end
	end
	return mejor
end

local function enAvion(nombre: string): BasePart?
	local p = cacheAvion[nombre]
	if p and p:IsDescendantOf(avion) then
		return p
	end
	local nuevo = avion:FindFirstChild(nombre, true)
	if nuevo and nuevo:IsA("BasePart") then
		cacheAvion[nombre] = nuevo
		return nuevo
	end
	return nil
end

local function dispensador(): BasePart?
	local p = dispensadorCache
	if p and p:IsDescendantOf(avion) then
		return p
	end
	for _, d in avion:GetDescendants() do
		if d:IsA("BasePart") and string.find(d.Name, "^Dispensador") then
			dispensadorCache = d
			return d
		end
	end
	return nil
end

local function salasLobby(): { BasePart }
	if #salas > 0 and salas[1]:IsDescendantOf(Workspace) then
		return salas
	end
	local ahora = os.clock()
	if ahora < escaneoSalas then
		return salas
	end
	escaneoSalas = ahora + 3
	table.clear(salas)
	local aeropuerto = Workspace:FindFirstChild("Aeropuerto")
	if aeropuerto then
		for _, d in aeropuerto:GetDescendants() do
			if d:IsA("BasePart") and d.Name ~= "PantallaSala" and typeof(d:GetAttribute("Sala")) == "number" then
				table.insert(salas, d)
			end
		end
	end
	return salas
end

local function marcaPrep(icono: string, destino: boolean?): BasePart?
	return cercana(CollectionService:GetTagged("MarcaPrep"), function(o)
		return o:GetAttribute("PrepIcono") == icono and (destino == nil or (o:GetAttribute("PrepDestino") == true) == destino)
	end)
end

local function marcaIsla(etiqueta: string, icono: string): BasePart?
	return cercana(CollectionService:GetTagged(etiqueta), function(o)
		return o:GetAttribute("Icono") == icono and not portado(o)
	end)
end

local function dentroAvion(p: Vector3): boolean
	return math.abs(p.X) < 7.4 and p.Y > 99 and p.Y < 112 and p.Z > -64 and p.Z < 22
end

local function anotar(l: { Tarea }, clave: string, icono: string, contenido: string, hecho: boolean, destino: Objetivo?): Tarea
	local t: Tarea = { clave = clave, icono = icono, texto = contenido, hecho = hecho, objetivo = destino }
	table.insert(l, t)
	return t
end

local function tareasAeropuerto(l: { Tarea })
	local r = raiz()
	local lista = salasLobby()
	local dentro = false
	if r then
		for _, s in lista do
			local d = r.Position - s.Position
			dentro = dentro or (Vector3.new(d.X, 0, d.Z).Magnitude <= s.Size.Y / 2 and math.abs(d.Y) < 6)
		end
	end
	anotar(l, "tablero", "Billete", "Mira los vuelos en el tablero de SALIDAS", dentro).info = true
	anotar(l, "puerta", "Diana", "Entra con tu grupo en el círculo de una puerta", dentro, cercana(lista :: { any }))
	if dentro then
		anotar(l, "espera", "Reloj", "El capitán pulsa DESPEGAR cuando estéis todos", false).info = true
	end
end

local function tareasPreparacion(l: { Tarea })
	local paso = cadena(Estado, "PrepPaso")
	if paso == "" then
		return
	end
	local enTareas = paso == "Tareas"
	local n, total = numero(Estado, "PrepMaletas"), numero(Estado, "PrepTotal")
	local animal = cadena(Estado, "PrepAnimal")
	local combustible = numero(Estado, "PrepCombustible")
	local fallos = cadena(Estado, "PrepFallos")
	local tipo = sostenido()
	local maletas = anotar(l, "maletas", "Maleta", `Lleva las maletas al carro {n}/{total}`, (total > 0 and n >= total) or not enTareas, if tipo == "Maleta" then marcaPrep("Maleta", true) else marcaPrep("Mano") or marcaPrep("Maleta", true))
	maletas.fallo = string.find(fallos, "maletas", 1, true) ~= nil
	maletas.actual = enTareas and tipo == "Maleta"
	if animal ~= "" then
		local hecho = animal == "Bodega" or animal == "Perdido"
		local coco = CollectionService:GetTagged("Cocodrilo")[1]
		local calmado = coco ~= nil and coco:GetAttribute("Estado") == "Saciado"
		local destino = if tipo == "Cocodrilo" then marcaPrep("Diana") elseif tipo ~= "" or calmado then marcaPrep("Cocodrilo") else marcaPrep("Hamburguesa") or marcaPrep("Cocodrilo")
		local t = anotar(l, "coco", "Cocodrilo", if animal == "Perdido" then "El cocodrilo se ha perdido" elseif hecho then "Cocodrilo enjaulado y en la bodega" else "Mete al cocodrilo en su jaula", hecho, destino)
		t.actual = tipo == "Cocodrilo" or tipo == "Hamburguesa"
	end
	anotar(l, "combustible", "Combustible", `Bombea en el surtidor (E) {combustible}%`, combustible >= 100, marcaPrep("Combustible"))
	local conducir = anotar(l, "conducir", "Volante", "Lleva el carro con el tractor hasta el avión", paso == "Descargar", if sentadoEn() == "AsientoTractor" then marcaPrep("Avion") else marcaPrep("Volante"))
	conducir.fallo = string.find(fallos, "conducir", 1, true) ~= nil
	if not enTareas then
		anotar(l, "bodega", "Avion", if paso == "Descargar" then `Mete las maletas en la bodega ({numero(Estado, "PrepFuera")})` else "Mete las maletas en la bodega", false, marcaPrep("Maleta", true))
	end
end

local function tareasEmbarque(l: { Tarea })
	if cadena(Estado, "PrepPaso") == "Descargar" then
		anotar(l, "bodega", "Maleta", `Mete las maletas en la bodega ({numero(Estado, "PrepFuera")})`, false, marcaPrep("Maleta", true))
	end
	local r = raiz()
	anotar(l, "subir", "Avion", "Sube al avión por la rampa de atrás", r ~= nil and dentroAvion(r.Position), enAvion("Rampa"))
	anotar(l, "piloto", "Volante", "Que alguien se siente a pilotar (asiento izquierdo)", numero(avion, "Piloto") ~= 0, enAvion("AsientoPiloto"))
end

local function tareasVuelo(l: { Tarea })
	local fa = cadena(avion, "Fase")
	local piloto = numero(avion, "Piloto")
	local yo = Piloto.activo()
	local asiento = enAvion("AsientoPiloto")
	if fa == "Despegue" then
		if yo then
			anotar(l, "acelera", "Avion", `Acelera (Shift) hasta {V.VELOCIDAD_DESPEGUE} km/h`, numero(avion, "Velocidad") >= V.VELOCIDAD_DESPEGUE)
			anotar(l, "sube", "Flecha", "Y sube (W) para despegar", false)
		elseif piloto == 0 then
			anotar(l, "piloto", "Volante", "¡Nadie pilota! Siéntate a la izquierda de la cabina (G)", false, asiento)
		else
			anotar(l, "agarrate", "Cinturon", "Agárrate: ¡despegamos!", false).info = true
		end
		return
	end
	if fa ~= "Vuelo" and fa ~= "Aproximacion" then
		return
	end
	local fuego = cercana(CollectionService:GetTagged("Fuego"))
	if fuego then
		anotar(l, "fuego", "Fuego", "Apaga el fuego con el extintor (F)", false, fuego)
	end
	local brecha = cercana(CollectionService:GetTagged("Brecha"), function(o)
		return o:GetAttribute("Reparacion") ~= nil
	end)
	if brecha then
		anotar(l, "agujero", "Casco", "Tapa el agujero con una maleta y repáralo (F)", false, brecha)
	end
	local suelto = cercana(CollectionService:GetTagged("PanelSuelto"))
	if suelto then
		anotar(l, "panel", "Llave", "Arregla el panel del techo: sal al ala con el piolet", false, suelto)
	end
	local piratas = avion:FindFirstChild("Piratas")
	if piratas and #piratas:GetChildren() > 0 then
		anotar(l, "piratas", "Pirata", "Dispara a los piratas desde la torreta del ala", false, enAvion("Torreta"))
	end
	if avion:GetAttribute("MotorIzqFuego") == true or avion:GetAttribute("MotorDerFuego") == true then
		anotar(l, "motorFuego", "Fuego", "Motor en llamas: extintor de motores en la cabina (E)", false, enAvion("BotonExtintorMotor"))
	elseif numero(avion, "MotorIzq") <= 0 or numero(avion, "MotorDer") <= 0 then
		anotar(l, "motor", "Motor", "Motor apagado: reinícialo en la cabina (E)", false, enAvion("BotonMotores"))
	end
	if piloto == 0 and avion:GetAttribute("Autopiloto") ~= true then
		anotar(l, "piloto", "Volante", "¡Nadie pilota! Siéntate a la izquierda de la cabina (G)", false, asiento)
	end
	for nombre, d in CAOS do
		local v = Estado:GetAttribute("Caos" .. nombre)
		if v ~= nil then
			anotar(l, "caos" .. nombre, d[1], d[2], false, if typeof(v) == "Vector3" then v else nil).info = d[3] == "info"
		end
	end
	if yo then
		if fa == "Aproximacion" then
			anotar(l, "aterriza", "Aterrizaje", `Aterriza: toca suelo a menos de {V.VELOCIDAD_ATERRIZAJE} km/h, suave`, false)
		else
			anotar(l, "rumbo", "Volante", "Sigue el rumbo del panel y no bajes de 800 m", false)
		end
		return
	end
	if fa == "Aproximacion" then
		anotar(l, "aterrizamos", "Cinturon", "¡Aterrizamos! Siéntate (G) o agárrate", false).info = true
	end
	local pasajeros = CollectionService:GetTagged("Pasajero")
	local pedidos = 0
	for _, m in pasajeros do
		if cadena(m, "Pedido") ~= "" then
			pedidos += 1
		end
	end
	if pedidos > 0 and COMIDA[sostenido()] then
		anotar(l, "servir", "Hamburguesa", `Sirve los pedidos (E) o lánzaselos: {pedidos}`, false, cercana(pasajeros, function(o)
			return cadena(o, "Pedido") ~= ""
		end))
	elseif pedidos > 0 then
		anotar(l, "cocina", "Bandeja", "Coge comida en la cocina (E)", false, dispensador())
		anotar(l, "pedidos", "Pasajero", `Pasajeros esperando su pedido: {pedidos}`, false).info = true
	elseif #l == 0 then
		anotar(l, "calma", "Feliz", "Todo tranquilo... de momento", false).info = true
	end
end

local function tareasIsla(l: { Tarea })
	local rescate = numero(Estado, "IslaRescate")
	if rescate > 0 then
		anotar(l, "muelle", "Hidroavion", "¡Corre al muelle, llega el hidroavión!", false, marcaIsla("DestinoIsla", "Hidroavion"))
		return
	end
	local objeto = Agarre.sostenido()
	local llevo = if objeto then cadena(objeto, "Icono") else ""
	local function pieza(clave: string, icono: string, zona: string, contenido: string, hecho: boolean)
		local t = anotar(l, clave, icono, contenido, hecho, if llevo == icono then marcaIsla("DestinoIsla", zona) else marcaIsla("ObjetivoIsla", icono))
		t.actual = llevo == icono
	end
	local piezas, troncos = #Config.ISLA.PIEZAS, Config.ISLA.TRONCOS
	local radio, lena = numero(Estado, "IslaRadio"), numero(Estado, "IslaLena")
	pieza("radio", "Radio", "Radio", `Lleva las piezas de radio a la estación {radio}/{piezas}`, radio >= piezas)
	pieza("lena", "Tronco", "Fuego", `Lleva troncos a la hoguera {lena}/{troncos}`, lena >= troncos)
	pieza("bengala", "Bengala", "Fuego", "Enciende la hoguera con la bengala", Estado:GetAttribute("IslaFuego") == true)
	anotar(l, "tiempo", "Reloj", `Quedan {reloj(numero(Estado, "IslaQuedan"))}`, false).info = true
end

local function calcular(): { Tarea }
	local l: { Tarea } = {}
	local f = fase()
	if f == "Aeropuerto" then
		tareasAeropuerto(l)
	elseif f == "Preparacion" then
		tareasPreparacion(l)
	elseif f == "Embarque" then
		tareasEmbarque(l)
	elseif f == "Vuelo" then
		tareasVuelo(l)
	elseif f == "Isla" then
		tareasIsla(l)
	end
	return l
end

local function escalar(o: GuiObject): UIScale
	local e = Instance.new("UIScale")
	e.Scale = Gui.escala()
	e.Parent = o
	table.insert(escalas, e)
	return e
end

local function izquierda(t: TextLabel, maximo: number): TextLabel
	t.TextXAlignment = Enum.TextXAlignment.Left
	t.TextWrapped = false
	t.TextScaled = true
	local l = Instance.new("UITextSizeConstraint")
	l.MaxTextSize = maximo
	l.Parent = t
	return t
end

local function construirPanel()
	panel = Gui.panel(gui, "Papel", UDim2.fromOffset(ANCHO, 100), POSICION_PANEL)
	panel.Rotation = -1.2
	panel.Visible = false
	escalaPanel = escalar(panel)
	izquierda(Gui.texto(panel, "TAREAS", UDim2.new(1, -60, 0, 30), UDim2.fromOffset(26, 16), Gui.NARANJA, true), 30)
	flechaPanel = Gui.icono(panel, "Flecha", UDim2.fromOffset(26, 26), UDim2.new(1, -44, 0, 18))
	local plegar = Instance.new("TextButton")
	plegar.BackgroundTransparency = 1
	plegar.Text = ""
	plegar.Size = UDim2.new(1, 0, 0, 50)
	plegar.Parent = panel
	plegar.Activated:Connect(function()
		Guia.alternarTareas()
	end)
	for i = 1, MAX_FILAS do
		local marco = Instance.new("Frame")
		marco.BackgroundTransparency = 1
		marco.Size = UDim2.new(1, -40, 0, 32)
		marco.Position = UDim2.fromOffset(20, 50 + (i - 1) * 34)
		marco.Parent = panel
		local resalte = Gui.panel(marco, "BarraRelleno", UDim2.new(1, 10, 1, 4), UDim2.fromOffset(-5, -2))
		resalte.ImageColor3 = Gui.AMARILLO
		resalte.ImageTransparency = 0.25
		local casilla = Gui.icono(marco, "Casilla", UDim2.fromOffset(24, 24), UDim2.fromOffset(4, 4))
		local tick = Gui.icono(marco, "Tick", UDim2.fromOffset(28, 28), UDim2.fromOffset(5, -2))
		local icono = Gui.icono(marco, "Info", UDim2.fromOffset(26, 26), UDim2.fromOffset(34, 3))
		local t = izquierda(Gui.texto(marco, "", UDim2.new(1, -68, 1, -4), UDim2.fromOffset(66, 2), Gui.TINTA), 21)
		filas[i] = { marco = marco, resalte = resalte, casilla = casilla, marca = tick, icono = icono, texto = t, clave = "", fuente = "", hecho = false }
	end
end

local function pintar(tareas: { Tarea }): Tarea?
	local actual: Tarea? = nil
	for _, t in tareas do
		if t.actual and not t.hecho then
			actual = t
			break
		end
	end
	if not actual then
		for _, t in tareas do
			if not t.hecho and not t.info and not t.fallo then
				actual = t
				break
			end
		end
	end
	local mostrar = if plegado and actual then { actual } else tareas
	local n = math.min(#mostrar, MAX_FILAS)
	panel.Visible = n > 0
	panel.Size = UDim2.fromOffset(ANCHO, 62 + n * 34)
	flechaPanel.Rotation = if plegado then 180 else 0
	flechaPanel.Visible = #tareas > 1
	for i, f in filas do
		local t = if i <= n then mostrar[i] else nil
		f.marco.Visible = t ~= nil
		if not t then
			f.clave = ""
			continue
		end
		local es = t == actual
		f.resalte.Visible = es
		Gui.ponerIcono(f.casilla, if es then "Flecha" else "Casilla")
		f.casilla.Visible = not t.info
		f.casilla.Rotation = if es then 90 else 0
		Gui.ponerIcono(f.marca, if t.fallo then "Cerrar" else "Tick")
		f.marca.Visible = not t.info and (t.hecho or t.fallo == true)
		f.marca.ImageColor3 = if t.fallo then Gui.ROJO else Color3.new(1, 1, 1)
		Gui.ponerIcono(f.icono, t.icono)
		local fuente = if t.fallo then `<s>{t.texto}</s> · <b>sin hacer</b>` elseif t.hecho then `<s>{t.texto}</s>` elseif es then `<b>{t.texto}</b>` else t.texto
		if fuente ~= f.fuente then
			f.fuente = fuente
			f.texto.Text = fuente
		end
		f.texto.TextColor3 = if t.fallo then Gui.ROJO elseif t.hecho or t.info then Gui.LAPIZ else Gui.TINTA
		if f.clave == t.clave and t.hecho and not f.hecho then
			Sonido.reproducir("UiClick", nil, 0.8, 1.2)
			f.marca.Rotation = -25
			TweenService:Create(f.marca, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Rotation = 0 }):Play()
		end
		f.clave = t.clave
		f.hecho = t.hecho
	end
	return actual
end

local function construirMarca()
	ancla = Instance.new("Part")
	ancla.Name = "AnclaGuia"
	ancla.Anchored = true
	ancla.CanCollide = false
	ancla.CanQuery = false
	ancla.CanTouch = false
	ancla.Transparency = 1
	ancla.Size = Vector3.one * 0.2
	ancla.Parent = Workspace.CurrentCamera
	marca = Instance.new("BillboardGui")
	marca.Name = "MarcaGuia"
	marca.AlwaysOnTop = true
	marca.LightInfluence = 0
	marca.Size = UDim2.fromOffset(120, 150)
	marca.MaxDistance = 2000
	marca.ResetOnSpawn = false
	marca.Enabled = false
	marca.Adornee = ancla
	marcaAro = Gui.panel(marca, "Sello", UDim2.fromOffset(78, 78), UDim2.new(0.5, 0, 0, 40), Vector2.new(0.5, 0.5))
	marcaAro.ImageColor3 = Gui.NARANJA
	marcaIcono = Gui.icono(marca, "Info", UDim2.fromOffset(50, 50), UDim2.new(0.5, 0, 0, 40), Vector2.new(0.5, 0.5))
	marcaIcono.ZIndex = 2
	marcaDistancia = Gui.texto(marca, "", UDim2.fromOffset(120, 28), UDim2.new(0.5, 0, 0, 80), Gui.PAPEL, true)
	marcaDistancia.AnchorPoint = Vector2.new(0.5, 0)
	Gui.trazado(marcaDistancia)
	marcaFlecha = Gui.icono(marca, "Flecha", UDim2.fromOffset(36, 36), UDim2.new(0.5, 0, 0, 128), Vector2.new(0.5, 0.5))
	marcaFlecha.Rotation = 180
	marca.Parent = jugador:WaitForChild("PlayerGui")
	borde = Instance.new("Frame")
	borde.BackgroundTransparency = 1
	borde.Size = UDim2.fromOffset(70, 70)
	borde.AnchorPoint = Vector2.new(0.5, 0.5)
	borde.Visible = false
	borde.Parent = gui
	escalar(borde)
	local aro = Gui.panel(borde, "Sello", UDim2.fromScale(1, 1), UDim2.new())
	aro.ImageColor3 = Gui.NARANJA
	bordeFlecha = Gui.icono(borde, "Flecha", UDim2.fromScale(0.62, 0.62), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5))
	bordeFlecha.ZIndex = 2
end

local function posicionObjetivo(o: Objetivo): Vector3?
	if typeof(o) == "Vector3" then
		return o
	end
	return if o:IsDescendantOf(Workspace) then o.Position else nil
end

local function apuntar(o: Objetivo?, icono: string)
	objetivo = o
	objetivoIcono = icono
	Gui.ponerIcono(marcaIcono, icono)
	local propia = false
	local alto, extra = 1.5, 0
	if typeof(o) ~= "Vector3" and o ~= nil then
		if CollectionService:HasTag(o, "MarcaPrep") then
			propia, alto, extra = true, math.min(o.Size.Y / 2, 3) + 3.2, 68
		elseif CollectionService:HasTag(o, "DestinoIsla") then
			propia, alto, extra = true, 8, 54
		elseif CollectionService:HasTag(o, "ObjetivoIsla") then
			propia, alto, extra = true, 3, 26
		elseif o.Parent and CollectionService:HasTag(o.Parent, "Pasajero") then
			propia, alto, extra = true, 3.4, 48
		end
	end
	marcaAro.Visible = not propia
	marcaIcono.Visible = not propia
	marca.StudsOffsetWorldSpace = Vector3.new(0, alto, 0)
	marca.SizeOffset = Vector2.new(0, 0.5 + extra / 150)
end

local ultimaDistancia = -1

local function seguirObjetivo()
	local o = objetivo
	local p = if o then posicionObjetivo(o) else nil
	local r = raiz()
	local visibleGui = gui.Enabled and not Cine.activo()
	if not p or not r or not visibleGui then
		marca.Enabled = false
		borde.Visible = false
		return
	end
	ancla.CFrame = CFrame.new(p)
	local d = (p - r.Position).Magnitude
	local lejos = d > 7
	marca.Enabled = lejos
	local metros = math.floor(d * 0.28 + 0.5)
	if metros ~= ultimaDistancia then
		ultimaDistancia = metros
		marcaDistancia.Text = `{metros} m`
	end
	marcaFlecha.Position = UDim2.new(0.5, 0, 0, 126 + math.sin(os.clock() * 7) * 6)
	local cam = Workspace.CurrentCamera
	local v = cam.ViewportSize
	local q, delante = cam:WorldToViewportPoint(p)
	local margen = 60 * Gui.escala()
	if not lejos or (delante and q.X > margen and q.X < v.X - margen and q.Y > margen and q.Y < v.Y - margen) then
		borde.Visible = false
		return
	end
	local centro = v / 2
	local dir = Vector2.new(q.X, q.Y) - centro
	if q.Z < 0 then
		dir = -dir
	end
	if dir.Magnitude < 1 then
		dir = Vector2.new(0, 1)
	end
	local limite = centro - Vector2.new(margen, margen)
	local k = math.min(if dir.X ~= 0 then limite.X / math.abs(dir.X) else math.huge, if dir.Y ~= 0 then limite.Y / math.abs(dir.Y) else math.huge)
	local punto = centro + dir * k - gui.AbsolutePosition
	borde.Position = UDim2.fromOffset(punto.X, punto.Y)
	bordeFlecha.Rotation = math.deg(math.atan2(dir.Y, dir.X)) + 90
	borde.Visible = true
end

local function leerVisto()
	local crudo = jugador:GetAttribute("Ajustes")
	if typeof(crudo) ~= "string" then
		return
	end
	local ok, t = pcall(HttpService.JSONDecode, HttpService, crudo)
	local v = if ok and typeof(t) == "table" then t.Visto else nil
	if typeof(v) ~= "table" then
		return
	end
	for clave, n in v do
		if typeof(clave) == "string" and typeof(n) == "number" then
			visto[clave] = math.max(visto[clave] or 0, n)
		end
	end
end

local function veces(clave: string): number
	return visto[clave] or 0
end

local function marcarVisto(clave: string)
	visto[clave] = veces(clave) + 1
	local r = remotoVisto
	if r then
		r:FireServer(clave)
	end
end

local function bloqueado(): boolean
	return comoAbierto or not gui.Enabled or Cine.activo()
end

local function encolar(t: Tarjeta)
	if FASES[t.clave] == t then
		for i = #cola, 1, -1 do
			if cola[i].fase and FASES[cola[i].clave] then
				table.remove(cola, i)
			end
		end
		local abierta = tarjetaAbierta
		if abierta and abierta.fase and FASES[abierta.clave] then
			saltarTarjeta = true
		end
	end
	table.insert(cola, t)
end

local function filaPunto(padre: Instance, icono: string, contenido: string, y: number, alto: number, maximo: number)
	Gui.icono(padre, icono, UDim2.fromOffset(alto, alto), UDim2.fromOffset(32, y))
	izquierda(Gui.texto(padre, contenido, UDim2.new(1, -(alto + 80), 0, alto - 4), UDim2.fromOffset(alto + 44, y + 2), Gui.TINTA), maximo)
end

local function mostrarTarjeta(t: Tarjeta)
	local completa = veces(t.clave) < 2
	local puntos: { { string } } = if completa then t.puntos else {}
	local alto = if completa then 104 + #puntos * 40 else 96
	local base = if TACTIL and Piloto.activo() then UDim2.new(0.5, 0, 1, -290) else UDim2.new(0.5, 0, 1, -22)
	local p = Gui.panel(gui, "Papel", UDim2.fromOffset(560, alto), base + UDim2.fromOffset(0, alto + 80), Vector2.new(0.5, 1))
	p.Rotation = 0.8
	p.ZIndex = 4
	local e = escalar(p)
	izquierda(Gui.texto(p, t.titulo, UDim2.new(1, -120, 0, 38), UDim2.fromOffset(30, 18), Gui.NARANJA, true), 36)
	izquierda(Gui.texto(p, t.meta, UDim2.new(1, -64, 0, 30), UDim2.fromOffset(30, 58), Gui.TINTA), 26)
	for i, punto in puntos do
		filaPunto(p, punto[1], punto[2], 96 + (i - 1) * 40, 36, 24)
	end
	local cerrar = Gui.panel(p, "Boton", UDim2.fromOffset(46, 46), UDim2.new(1, -62, 0, 14), nil, true) :: any
	cerrar.ImageColor3 = Gui.TIZA
	Gui.icono(cerrar, "Cerrar", UDim2.fromScale(0.6, 0.6), UDim2.fromScale(0.5, 0.48), Vector2.new(0.5, 0.5))
	cerrar.Activated:Connect(function()
		saltarTarjeta = true
	end)
	tarjetaAbierta = t
	saltarTarjeta = false
	if completa then
		marcarVisto(t.clave)
	end
	Sonido.reproducir("UiAviso", nil, 0.7, 1.15)
	TweenService:Create(p, TweenInfo.new(0.45, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Position = base }):Play()
	local fin = os.clock() + (if completa then 4.5 else 2.6)
	while os.clock() < fin and not saltarTarjeta and gui.Enabled do
		task.wait(0.1)
	end
	tarjetaAbierta = nil
	local destino = if panel.Visible
		then UDim2.fromOffset(panel.AbsolutePosition.X - gui.AbsolutePosition.X + panel.AbsoluteSize.X / 2, panel.AbsolutePosition.Y - gui.AbsolutePosition.Y + 24)
		else POSICION_PANEL + UDim2.fromOffset(ANCHO / 2, 24)
	local info = TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	TweenService:Create(p, info, { Position = destino, Rotation = -10 }):Play()
	TweenService:Create(e, info, { Scale = 0.06 }):Play()
	task.wait(0.4)
	p:Destroy()
	local i = table.find(escalas, e)
	if i then
		table.remove(escalas, i)
	end
	if panel.Visible then
		Sonido.reproducir("UiClick", nil, 0.5, 0.9)
		escalaPanel.Scale = Gui.escala() * 1.1
		TweenService:Create(escalaPanel, TweenInfo.new(0.3, Enum.EasingStyle.Back), { Scale = Gui.escala() }):Play()
	end
end

local function boton(padre: Instance, contenido: string, tamano: UDim2, posicion: UDim2, color: Color3, alPulsar: () -> ()): ImageButton
	local b = Gui.panel(padre, "Boton", tamano, posicion, nil, true) :: any
	b.ImageColor3 = color
	Gui.texto(b, contenido, UDim2.new(1, -18, 1, -14), UDim2.fromOffset(9, 6), Gui.TINTA, true)
	b.Activated:Connect(function()
		Sonido.reproducir("UiClick", nil, 0.5, 1.1)
		alPulsar()
	end)
	return b
end

function Guia.alternarTareas()
	plegado = not plegado
end

function Guia.comoJugar()
	if comoAbierto then
		return
	end
	comoAbierto = true
	saltarTarjeta = true
	local fondo = Instance.new("TextButton")
	fondo.Text = ""
	fondo.AutoButtonColor = false
	fondo.BackgroundColor3 = Gui.TINTA
	fondo.BackgroundTransparency = 0.5
	fondo.Size = UDim2.fromScale(1, 1)
	fondo.Modal = true
	fondo.ZIndex = 10
	fondo.Parent = gui
	local p = Gui.panel(fondo, "Papel", UDim2.fromOffset(640, 440), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5))
	p.ZIndex = 11
	local e = escalar(p)
	local base = e.Scale
	local contenido = Instance.new("Frame")
	contenido.BackgroundTransparency = 1
	contenido.Size = UDim2.new(1, 0, 1, -96)
	contenido.Parent = p
	local pagina = 1
	local terminado = false
	local siguiente: ImageButton
	local textoSiguiente: TextLabel
	local cuenta = Gui.texto(p, "", UDim2.fromOffset(80, 30), UDim2.new(0.5, 0, 1, -62), Gui.LAPIZ, false, 24)
	cuenta.AnchorPoint = Vector2.new(0.5, 0)
	local function dibujar()
		contenido:ClearAllChildren()
		local t = PAGINAS[pagina]
		izquierda(Gui.texto(contenido, t.titulo, UDim2.new(1, -72, 0, 46), UDim2.fromOffset(36, 26), Gui.NARANJA, true), 42)
		local meta = Gui.texto(contenido, t.meta, UDim2.new(1, -72, 0, 80), UDim2.fromOffset(36, 78), Gui.TINTA)
		meta.TextXAlignment = Enum.TextXAlignment.Left
		meta.TextYAlignment = Enum.TextYAlignment.Top
		local limite = Instance.new("UITextSizeConstraint")
		limite.MaxTextSize = 25
		limite.Parent = meta
		for i, punto in t.puntos do
			filaPunto(contenido, punto[1], punto[2], 166 + (i - 1) * 54, 46, 28)
		end
		cuenta.Text = `{pagina}/{#PAGINAS}`
		textoSiguiente.Text = if pagina == #PAGINAS then "¡A VOLAR!" else "SIGUIENTE"
		e.Scale = base * 0.92
		TweenService:Create(e, TweenInfo.new(0.3, Enum.EasingStyle.Back), { Scale = base }):Play()
	end
	local function avanzar()
		if pagina < #PAGINAS then
			pagina += 1
			dibujar()
		else
			terminado = true
		end
	end
	boton(p, "Saltar", UDim2.fromOffset(170, 64), UDim2.new(0, 34, 1, -86), Gui.TIZA, function()
		terminado = true
	end)
	siguiente = boton(p, "", UDim2.fromOffset(250, 72), UDim2.new(1, -284, 1, -92), Gui.NARANJA, avanzar)
	textoSiguiente = siguiente:FindFirstChildOfClass("TextLabel") :: TextLabel
	dibujar()
	Sonido.reproducir("UiAviso", nil, 0.8, 1)
	if UserInputService.GamepadEnabled then
		GuiService.SelectedObject = siguiente
	end
	local tecla = UserInputService.InputBegan:Connect(function(entrada)
		if entrada.KeyCode == Enum.KeyCode.Return and not UserInputService:GetFocusedTextBox() then
			Sonido.reproducir("UiClick", nil, 0.5, 1.1)
			avanzar()
		end
	end)
	while not terminado and fondo.Parent do
		task.wait(0.1)
	end
	tecla:Disconnect()
	if GuiService.SelectedObject and GuiService.SelectedObject:IsDescendantOf(fondo) then
		GuiService.SelectedObject = nil
	end
	TweenService:Create(e, TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Scale = 0.1 }):Play()
	task.wait(0.2)
	fondo:Destroy()
	local i = table.find(escalas, e)
	if i then
		table.remove(escalas, i)
	end
	if veces("ComoJugar") == 0 then
		marcarVisto("ComoJugar")
	end
	enSesion.ComoJugar = true
	comoAbierto = false
end

local function tarjetasEnBucle()
	local limite = os.clock() + 10
	while jugador:GetAttribute("Ajustes") == nil and os.clock() < limite do
		task.wait(0.25)
	end
	while true do
		local t = cola[1]
		if not t or bloqueado() then
			task.wait(0.25)
			continue
		end
		table.remove(cola, 1)
		if t.clave == "Resultados" then
			local hasta = os.clock() + 20
			while not Interfaz.resultadosVisibles() and os.clock() < hasta do
				task.wait(0.25)
			end
			while Interfaz.resultadosVisibles() or bloqueado() do
				task.wait(0.25)
			end
		end
		if t.fase == nil or t.fase == fase() then
			mostrarTarjeta(t)
		end
	end
end

local function alCambiarFaseAvion()
	if fase() ~= "Vuelo" then
		return
	end
	local fa = cadena(avion, "Fase")
	local t = if fa == "Despegue" then FASES.Despegue elseif fa == "Vuelo" then FASES.Vuelo elseif fa == "Aproximacion" then FASES.Aterrizaje else nil
	if t then
		encolar(t)
	end
end

local function alCambiarFase()
	local f = fase()
	if f == "Vuelo" then
		alCambiarFaseAvion()
		return
	end
	if f == "Aeropuerto" and veces("ComoJugar") == 0 and not enSesion.ComoJugar then
		enSesion.ComoJugar = true
		task.spawn(function()
			local limite = os.clock() + 10
			while jugador:GetAttribute("Ajustes") == nil and os.clock() < limite do
				task.wait(0.25)
			end
			while not gui.Enabled or Cine.activo() do
				task.wait(0.3)
			end
			task.wait(0.8)
			if fase() == "Aeropuerto" and veces("ComoJugar") == 0 then
				Guia.comoJugar()
			end
		end)
		return
	end
	local t = FASES[f]
	if t then
		encolar(t)
	end
end

local function suceso(clave: string)
	local t = SUCESOS[clave]
	if not t or fase() ~= "Vuelo" or enSesion[clave] or veces(clave) >= 2 then
		return
	end
	enSesion[clave] = true
	encolar(t)
end

local function mostrarPista(clave: string)
	local d = PISTAS[clave]
	enSesion["P" .. clave] = true
	marcarVisto("P" .. clave)
	notaId += 1
	local mio = notaId
	Gui.ponerIcono(notaIcono, d[1])
	notaTexto.Text = d[2]
	nota.Visible = true
	notaEscala.Scale = Gui.escala() * 0.6
	TweenService:Create(notaEscala, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Scale = Gui.escala() }):Play()
	Sonido.reproducir("UiClick", nil, 0.6, 1.4)
	task.delay(6, function()
		if mio == notaId then
			nota.Visible = false
		end
	end)
end

local function construirNota()
	nota = Gui.panel(gui, "NotaInfo", UDim2.fromOffset(0, 52), UDim2.new(0.5, 0, 0.5, 62), Vector2.new(0.5, 0))
	nota.AutomaticSize = Enum.AutomaticSize.X
	nota.Visible = false
	notaEscala = escalar(nota)
	local relleno = Instance.new("UIPadding")
	relleno.PaddingLeft = UDim.new(0, 14)
	relleno.PaddingRight = UDim.new(0, 24)
	relleno.Parent = nota
	local lista = Instance.new("UIListLayout")
	lista.FillDirection = Enum.FillDirection.Horizontal
	lista.VerticalAlignment = Enum.VerticalAlignment.Center
	lista.Padding = UDim.new(0, 8)
	lista.SortOrder = Enum.SortOrder.LayoutOrder
	lista.Parent = nota
	notaIcono = Gui.icono(nota, "Info", UDim2.fromOffset(34, 34), UDim2.new())
	notaIcono.LayoutOrder = 1
	notaTexto = Gui.texto(nota, "", UDim2.fromOffset(0, 34), UDim2.new(), Gui.TINTA, false, 23)
	notaTexto.AutomaticSize = Enum.AutomaticSize.X
	notaTexto.TextWrapped = false
	notaTexto.LayoutOrder = 2
end

local function revisarPistas()
	if nota.Visible or bloqueado() then
		return
	end
	local f = fase()
	local cam = Workspace.CurrentCamera.CFrame
	local function ver(clave: string, o: Instance?, radio: number): boolean
		if enSesion["P" .. clave] or veces("P" .. clave) > 0 then
			return false
		end
		local p = parteDe(o)
		if not p then
			return false
		end
		local d = p.Position - cam.Position
		local m = d.Magnitude
		if m < radio and m > 0.5 and d.Unit:Dot(cam.LookVector) > 0.94 then
			mostrarPista(clave)
			return true
		end
		return false
	end
	if f == "Preparacion" then
		local hangar = Workspace:FindFirstChild("Preparacion")
		local aeropuerto = Workspace:FindFirstChild("Aeropuerto")
		local vehiculos = aeropuerto and aeropuerto:FindFirstChild("Vehiculos")
		if ver("Surtidor", hangar and hangar:FindFirstChild("Surtidor"), 22) or ver("Tractor", vehiculos and vehiculos:FindFirstChild("Tractor"), 20) then
			return
		end
		for _, c in CollectionService:GetTagged("Cocodrilo") do
			if ver("CocoPrep", c, 20) then
				return
			end
		end
	elseif f == "Embarque" or f == "Vuelo" then
		if ver("Cabina", enAvion("AsientoPiloto"), 14) then
			return
		end
		if f ~= "Vuelo" then
			return
		end
		if ver("Torreta", enAvion("Torreta"), 18) then
			return
		end
		for _, o in CollectionService:GetTagged("Fuego") do
			if ver("Fuego", o, 24) then
				return
			end
		end
		for _, o in CollectionService:GetTagged("Brecha") do
			if o:GetAttribute("Reparacion") ~= nil and ver("Agujero", o, 24) then
				return
			end
		end
		for _, c in CollectionService:GetTagged("Cocodrilo") do
			if ver("Coco", c, 18) then
				return
			end
		end
		if not enSesion.PPedido and veces("PPedido") == 0 then
			for _, m in CollectionService:GetTagged("Pasajero") do
				if cadena(m, "Pedido") ~= "" and ver("Pedido", m, 14) then
					return
				end
			end
		end
	end
end

local function vigilarSucesos()
	CollectionService:GetInstanceAddedSignal("Fuego"):Connect(function()
		suceso("Fuego")
	end)
	CollectionService:GetInstanceAddedSignal("Brecha"):Connect(function(o)
		if o:GetAttribute("Reparacion") ~= nil then
			suceso("Agujero")
		end
	end)
	CollectionService:GetInstanceAddedSignal("PanelSuelto"):Connect(function()
		suceso("Panel")
	end)
	avion:GetAttributeChangedSignal("Bandada"):Connect(function()
		suceso("Pajaros")
	end)
	avion.AttributeChanged:Connect(function(nombre)
		local v = avion:GetAttribute(nombre)
		if nombre == "CaidaLibre" and v == true then
			suceso("CaidaLibre")
		elseif nombre == "Tormenta" and v == true then
			suceso("Tormenta")
		elseif (nombre == "MotorIzqFuego" or nombre == "MotorDerFuego") and v == true then
			suceso("MotorFuego")
		elseif (nombre == "MotorIzq" or nombre == "MotorDer") and v == 0 and avion:GetAttribute(nombre .. "Fuego") ~= true then
			suceso("MotorApagado")
		elseif nombre == "Turbulencia" and typeof(v) == "number" and v >= 0.5 then
			suceso("Turbulencia")
		elseif nombre == "Fase" then
			alCambiarFaseAvion()
		end
	end)
	task.spawn(function()
		local piratas = avion:WaitForChild("Piratas", 30)
		if piratas then
			piratas.ChildAdded:Connect(function()
				suceso("Piratas")
			end)
		end
	end)
	Estado.AttributeChanged:Connect(function(nombre)
		if nombre == "Fase" then
			alCambiarFase()
		elseif string.sub(nombre, 1, 4) == "Caos" and Estado:GetAttribute(nombre) ~= nil then
			suceso(string.sub(nombre, 5))
		end
	end)
end

function Guia.iniciar()
	gui = Instance.new("ScreenGui")
	gui.Name = "Guia"
	gui.ResetOnSpawn = false
	gui.IgnoreGuiInset = true
	gui.ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.DisplayOrder = 5
	gui.Parent = jugador:WaitForChild("PlayerGui")
	construirPanel()
	construirNota()
	construirMarca()
	Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(function()
		local s = Gui.escala()
		for _, e in escalas do
			e.Scale = s
		end
	end)
	leerVisto()
	jugador:GetAttributeChangedSignal("Ajustes"):Connect(leerVisto)
	task.spawn(function()
		local r = Remotos:WaitForChild("Visto", 30)
		if r and r:IsA("RemoteEvent") then
			remotoVisto = r
		end
	end)
	if RunService:IsStudio() then
		Workspace:GetAttributeChangedSignal("ReiniciarGuia"):Connect(function()
			if Workspace:GetAttribute("ReiniciarGuia") == true then
				table.clear(visto)
				table.clear(enSesion)
				alCambiarFase()
			end
		end)
	end
	UserInputService.InputBegan:Connect(function(entrada)
		if tarjetaAbierta and not comoAbierto and not UserInputService:GetFocusedTextBox() and (entrada.KeyCode == Enum.KeyCode.Return or entrada.KeyCode == Enum.KeyCode.ButtonSelect) then
			saltarTarjeta = true
		end
	end)
	vigilarSucesos()
	task.spawn(tarjetasEnBucle)
	alCambiarFase()
	local acumulado, pistas = 0, 0
	RunService.Heartbeat:Connect(function(dt)
		seguirObjetivo()
		acumulado += dt
		pistas += dt
		if pistas >= 0.2 then
			pistas = 0
			revisarPistas()
		end
		if acumulado < 0.25 then
			return
		end
		acumulado = 0
		local actual = pintar(calcular())
		local destino = if actual then actual.objetivo else nil
		local icono = if actual then actual.icono else "Info"
		if destino ~= objetivo or icono ~= objetivoIcono then
			apuntar(destino, icono)
		end
		if fase() == "Vuelo" then
			for _, m in CollectionService:GetTagged("Pasajero") do
				if m:GetAttribute("Alborotador") == true then
					suceso("Alborotador")
					break
				end
			end
		end
	end)
end

return Guia
