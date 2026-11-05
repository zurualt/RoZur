--!strict
local CollectionService = game:GetService("CollectionService")
local Debris = game:GetService("Debris")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local ModelosCaos = require(ReplicatedStorage.Shared.ModelosCaos)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Activos = require(script.Parent.Activos)
local Agarre = require(script.Parent.Agarre)
local Avion = require(script.Parent.Avion)
local Cabina = require(script.Parent.Cabina)
local Carga = require(script.Parent.Carga)
local Estadisticas = require(script.Parent.Estadisticas)
local Interacciones = require(script.Parent.Interacciones)
local Objetos = require(script.Parent.Objetos)
local Pasajeros = require(script.Parent.Pasajeros)
local Peligros = require(script.Parent.Peligros)
local Personajes = require(script.Parent.Personajes)
local Rafagas = require(script.Parent.Rafagas)
local Sonidos = require(script.Parent.Sonidos)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local RemotoUsar = Remotos:WaitForChild("Usar") :: RemoteEvent
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder

type Uso = (Player, string, Vector3, Vector3) -> ()
type Evento = { nombre: string, vivo: boolean, limpiar: { () -> () }, usar: Uso? }
type Def = { nombre: string, f: () -> boolean, peso: number }
type Especie = {
	tamano: Vector3,
	color: Color3,
	densidad: number,
	velocidad: number,
	aguante: number,
	premio: number,
	ruido: string,
	gritos: { string },
	vuelta: string,
	perdida: string,
}
type Animal = {
	parte: BasePart,
	especie: Especie,
	nombre: string,
	soltado: number,
	quien: Player?,
	cogido: number,
	objetivo: Vector3,
	cambio: number,
	golpe: number,
	ruido: number,
	salto: number,
	bodega: number,
}

local Caos = {}

local avion = Workspace:WaitForChild("Avion") :: Model
local carpeta = Instance.new("Folder")
carpeta.Name = "Caos"
carpeta.Parent = avion
local remoto = Instance.new("RemoteEvent")
remoto.Name = "Caos"
remoto.Parent = Remotos

local rng = Random.new()
local activos: { [string]: Evento } = {}
local animales: { [BasePart]: Animal } = {}
local golpes: { [Player]: number } = {}
local alCoger: { [Instance]: (Player) -> () } = {}
local usos: { [Player]: number } = {}
local activo = false
local generacion = 0
local bonus = 0
local ultimo = ""
local ARRIBA = Vector3.new(0, 1, 0)
local PLANO = Vector3.new(1, 0, 1)
local CABINA = Vector3.new(0, 106.5, -57)
local COCINA = Vector3.new(0, 104, -47)
local VERDE = Color3.fromRGB(128, 196, 64)

local ESPECIES: { [string]: Especie } = {
	Cabra = {
		tamano = Vector3.new(1.2, 1.9, 2.5),
		color = Color3.fromRGB(240, 236, 226),
		densidad = 0.7,
		velocidad = 13,
		aguante = 4,
		premio = 60,
		ruido = "Cabra",
		gritos = { "¡BEEE!", "¡MEEEH!" },
		vuelta = "¡Cabra devuelta a la bodega! +60",
		perdida = "¡La cabra ha saltado del avión! -60",
	},
	Gallina = {
		tamano = Vector3.new(0.85, 1.1, 1.1),
		color = Color3.fromRGB(250, 250, 245),
		densidad = 0.35,
		velocidad = 11,
		aguante = 2.5,
		premio = 15,
		ruido = "Gallina",
		gritos = { "¡CLOC!", "¡COCOCÓ!" },
		vuelta = "¡Gallina a la bodega! +15",
		perdida = "¡Una gallina se ha ido volando! -15",
	},
}

local function aviso(texto: string, tipo: string)
	RemotoAviso:FireAllClients(texto, tipo)
end

local function rotular(posicion: Vector3, texto: string, estilo: string, escala: number?)
	remoto:FireAllClients("Palabra", posicion, texto, estilo, escala or 1)
end

local function premiar(cantidad: number, jugador: Player?)
	bonus += cantidad
	if jugador and cantidad > 0 then
		Estadisticas.sumar(jugador, "caos")
	end
end

local function empezar(nombre: string, donde: Vector3?): Evento
	local e: Evento = { nombre = nombre, vivo = true, limpiar = {}, usar = nil }
	activos[nombre] = e
	ultimo = nombre
	Estado:SetAttribute("Caos" .. nombre, donde or true)
	return e
end

local function terminar(e: Evento)
	if not e.vivo then
		return
	end
	e.vivo = false
	if activos[e.nombre] == e then
		activos[e.nombre] = nil
		Estado:SetAttribute("Caos" .. e.nombre, nil)
	end
	for _, f in e.limpiar do
		task.spawn(f)
	end
end

local function sumar(m: Instance, atributo: string, delta: number)
	local v = m:GetAttribute(atributo)
	m:SetAttribute(atributo, math.clamp((if typeof(v) == "number" then v else 0.5) + delta, 0, 1))
end

local function cuerpoDe(m: Model): BasePart?
	local c = m:FindFirstChild("Cuerpo")
	return if c and c:IsA("BasePart") then c else nil
end

local function pasajeros(): { Model }
	local lista: { Model } = {}
	for _, m in CollectionService:GetTagged("Pasajero") do
		if m:IsA("Model") and m.Parent then
			table.insert(lista, m)
		end
	end
	return lista
end

local function libres(): { Model }
	local lista: { Model } = {}
	for _, m in pasajeros() do
		if m:GetAttribute("Estado") == "Sentado" and m:GetAttribute("Pedido") == "" and m:GetAttribute("Alborotador") ~= true and cuerpoDe(m) then
			table.insert(lista, m)
		end
	end
	return lista
end

local function cerca(posicion: Vector3, radio: number, excepto: Model?): { Model }
	local lista: { Model } = {}
	for _, m in pasajeros() do
		local c = cuerpoDe(m)
		if m ~= excepto and c and (c.Position - posicion).Magnitude < radio then
			table.insert(lista, m)
		end
	end
	return lista
end

local function jugadorCercano(posicion: Vector3, radio: number): Player?
	local mejor: Player? = nil
	local distancia = radio
	for _, j in Players:GetPlayers() do
		local r = Personajes.raiz(j)
		if r and (r.Position - posicion).Magnitude < distancia then
			mejor, distancia = j, (r.Position - posicion).Magnitude
		end
	end
	return mejor
end

local function empujarJugador(j: Player, desde: Vector3, fuerza: number, alto: number, duracion: number)
	local r = Personajes.raiz(j)
	if not r then
		return
	end
	local dir = (r.Position - desde) * PLANO
	Personajes.ragdoll(j, duracion, (if dir.Magnitude > 0.01 then dir.Unit else Vector3.xAxis) * fuerza + Vector3.new(0, alto, 0))
end

local function pedir(m: Model, pedido: string, paciencia: number)
	m:SetAttribute("PacienciaMax", paciencia)
	m:SetAttribute("Paciencia", paciencia)
	m:SetAttribute("Pedido", pedido)
end

local function feliz(m: Model): boolean
	local f = m:GetAttribute("Feliz")
	return typeof(f) == "number" and os.clock() - f < 1.5
end

local function pegar(modelo: Model, parte: BasePart)
	for _, d in modelo:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = false
			d.Massless = true
			d.CanCollide = false
			local w = Instance.new("WeldConstraint")
			w.Part0 = parte
			w.Part1 = d
			w.Parent = d
		end
	end
end

local function sueltos(): { BasePart }
	local lista = Objetos.sueltos()
	for _, p in Carga.sueltos() do
		table.insert(lista, p)
	end
	return lista
end

local function enBodega(p: Vector3): boolean
	return math.abs(p.X) < 6.6 and p.Y > 99 and p.Y < 111 and p.Z > 1.5 and p.Z < 22
end

local function quitarAnimal(a: Animal)
	animales[a.parte] = nil
	Agarre.soltarObjeto(a.parte)
	a.parte:Destroy()
end

local function comidaCerca(pos: Vector3, radio: number): BasePart?
	local mejor: BasePart? = nil
	local distancia = radio
	for _, o in CollectionService:GetTagged("Objeto") do
		if o:IsA("BasePart") and o.Parent and not Agarre.portador(o) then
			local t = o:GetAttribute("Tipo")
			if (t == "Hamburguesa" or t == "Bandeja") and (o.Position - pos).Magnitude < distancia then
				mejor, distancia = o, (o.Position - pos).Magnitude
			end
		end
	end
	return mejor
end

local function crearAnimal(nombre: string, cf: CFrame): Animal
	local def = ESPECIES[nombre]
	local parte = Instance.new("Part")
	parte.Name = nombre
	parte.Size = def.tamano
	parte.Color = def.color
	parte.Material = Enum.Material.SmoothPlastic
	parte.CustomPhysicalProperties = PhysicalProperties.new(def.densidad, 0.5, 0.2)
	parte.CFrame = cf
	parte:SetAttribute("Tipo", nombre)
	parte:SetAttribute("Portador", 0)
	CollectionService:AddTag(parte, "Agarrable")
	parte.Parent = carpeta
	Objetos.servidor(parte)
	Activos.vestirDinamico(parte, nombre)
	local a: Animal = {
		parte = parte,
		especie = def,
		nombre = nombre,
		soltado = 0,
		quien = nil,
		cogido = 0,
		objetivo = cf.Position,
		cambio = 0,
		golpe = 0,
		ruido = os.clock() + rng:NextNumber(1, 3),
		salto = 0,
		bodega = 0,
	}
	animales[parte] = a
	return a
end

local function moverAnimal(a: Animal, dt: number, ahora: number)
	local p = a.parte
	local def = a.especie
	local pos = p.Position
	if pos.Y < Config.CAIDA_Y then
		premiar(-def.premio)
		aviso(def.perdida, "peligro")
		quitarAnimal(a)
		return
	end
	local portador = Agarre.portador(p)
	if portador then
		if a.cogido == 0 then
			a.cogido = ahora
		elseif ahora - a.cogido > def.aguante then
			a.cogido = 0
			Agarre.soltarObjeto(p)
			rotular(pos + ARRIBA * 2, def.gritos[rng:NextInteger(1, #def.gritos)], "Animal")
			Sonidos.emitir(def.ruido, pos)
			if a.nombre == "Cabra" then
				empujarJugador(portador, pos, 28, 16, 0.9)
				RemotoAviso:FireClient(portador, "¡La cabra se ha soltado de una coz!", "peligro")
			end
			p.AssemblyLinearVelocity = Vector3.new(rng:NextNumber(-14, 14), 16, rng:NextNumber(-14, 14))
		end
		return
	end
	a.cogido = 0
	if enBodega(pos) and ahora - a.soltado < 8 then
		a.bodega += dt
		if a.bodega > 0.5 then
			premiar(def.premio, a.quien)
			Rafagas.lanzar("Polvo", pos, 0.8)
			Rafagas.lanzar("Confeti", pos, 0.6)
			Sonidos.emitir(def.ruido, pos)
			aviso(def.vuelta, "bien")
			quitarAnimal(a)
			return
		end
	else
		a.bodega = 0
	end
	if ahora > a.ruido then
		a.ruido = ahora + rng:NextNumber(3, 6)
		Sonidos.emitir(def.ruido, pos, 0.3)
		if rng:NextNumber() < 0.5 then
			rotular(pos + ARRIBA * 2, def.gritos[rng:NextInteger(1, #def.gritos)], "Animal", 0.8)
		end
	end
	if not Agarre.delServidor(p) then
		return
	end
	local destino: Vector3? = nil
	if a.nombre == "Cabra" then
		local comida = comidaCerca(pos, 26)
		if comida then
			destino = comida.Position
			if (comida.Position - pos).Magnitude < 2.6 then
				Agarre.soltarObjeto(comida)
				comida:Destroy()
				Sonidos.emitir("Comer", pos)
				rotular(pos + ARRIBA * 2, "¡ÑAM!", "Animal")
			end
		else
			local distancia = if ahora % 8 < 5 then 34 else 0
			for _, j in Players:GetPlayers() do
				local r = Personajes.raiz(j)
				if r then
					local d = (r.Position - pos).Magnitude
					if d < distancia then
						destino, distancia = r.Position, d
					end
					if d < 3.4 and (golpes[j] or 0) < ahora and not Personajes.enRagdoll(j) then
						golpes[j] = ahora + 5
						empujarJugador(j, pos, 42, 26, 1.2)
						Sonidos.emitir("Cabra", pos)
						Rafagas.lanzar("Bonk", r.Position, 1.2)
						RemotoAviso:FireClient(j, "¡La cabra te ha embestido!", "peligro")
					end
				end
			end
		end
	else
		for _, j in Players:GetPlayers() do
			local r = Personajes.raiz(j)
			if r then
				local delta = (pos - r.Position) * PLANO
				if delta.Magnitude < 7 then
					local huida = pos + (if delta.Magnitude > 0.1 then delta.Unit else Vector3.zAxis) * 8
					destino = Vector3.new(math.clamp(huida.X, -5.5, 5.5), pos.Y, math.clamp(huida.Z, -50, -2))
					if delta.Magnitude < 2.2 and (golpes[j] or 0) < ahora and rng:NextNumber() < 0.3 then
						golpes[j] = ahora + 4
						empujarJugador(j, pos, 14, 10, 0.6)
						Rafagas.lanzar("Plumas", pos, 0.6)
						RemotoAviso:FireClient(j, "¡Te ha picoteado una gallina!", "peligro")
					end
				end
			end
		end
	end
	if not destino then
		if ahora > a.cambio or ((a.objetivo - pos) * PLANO).Magnitude < 2 then
			a.cambio = ahora + rng:NextNumber(2, 4)
			a.objetivo = Vector3.new(rng:NextNumber(-1.5, 1.5) * (if a.nombre == "Gallina" then 3 else 1), pos.Y, rng:NextNumber(-48, -4))
		end
		destino = a.objetivo
	end
	if ahora > a.golpe then
		local victima = Pasajeros.cercano(pos, if a.nombre == "Cabra" then 2.8 else 2)
		local c = victima and victima.PrimaryPart
		if victima and c then
			a.golpe = ahora + 2.5
			Pasajeros.golpear(victima, if a.nombre == "Cabra" then 55 else 25, (c.Position - pos) * PLANO, "Golpe", Avion.estado.cinturones)
		end
	end
	local meta = destino :: Vector3
	local dir = (meta - pos) * PLANO
	if dir.Magnitude < 0.6 then
		return
	end
	local v = p.AssemblyLinearVelocity
	local plano = dir.Unit * def.velocidad
	local vertical = v.Y
	local enSuelo = math.abs(v.Y) < 1.5
	if enSuelo and ahora > a.salto and ((v * PLANO).Magnitude < def.velocidad * 0.3 or (a.nombre == "Gallina" and rng:NextNumber() < 0.06)) then
		a.salto = ahora + 0.7
		vertical = if a.nombre == "Gallina" then rng:NextNumber(14, 22) else 24
		if a.nombre == "Gallina" then
			Rafagas.lanzar("Plumas", pos, 0.4)
		end
	end
	p.AssemblyLinearVelocity = Vector3.new(plano.X, vertical, plano.Z)
	p.AssemblyAngularVelocity = Vector3.zero
	p.CFrame = p.CFrame:Lerp(CFrame.lookAt(pos, pos + dir), 0.4)
end

local function soltarAnimales(nombre: string, cantidad: number, texto: string): boolean
	if activos.Cabra or activos.Gallinas then
		return false
	end
	local e = empezar(if nombre == "Cabra" then "Cabra" else "Gallinas")
	local mios: { Animal } = {}
	local def = ESPECIES[nombre]
	for _ = 1, cantidad do
		table.insert(mios, crearAnimal(nombre, CFrame.new(rng:NextNumber(-2, 2), Config.SUELO_Y + def.tamano.Y / 2 + 0.3, rng:NextNumber(3, 7))))
	end
	local salida = Vector3.new(0, 102, 4)
	Rafagas.lanzar(if nombre == "Gallina" then "Plumas" else "Polvo", salida, 1.4)
	Sonidos.emitir(def.ruido, salida)
	rotular(salida + ARRIBA * 2, def.gritos[1], "Animal", 1.3)
	aviso(texto, "peligro")
	table.insert(e.limpiar, function()
		for _, a in mios do
			if animales[a.parte] then
				quitarAnimal(a)
			end
		end
	end)
	task.spawn(function()
		while e.vivo do
			local dt = task.wait(0.1)
			local ahora = os.clock()
			local quedan = 0
			for _, a in mios do
				if animales[a.parte] then
					moverAnimal(a, dt, ahora)
					if animales[a.parte] then
						quedan += 1
					end
				end
			end
			if quedan == 0 then
				terminar(e)
			end
		end
	end)
	return true
end

local function cabra(): boolean
	return soltarAnimales("Cabra", 1, "¡Se ha escapado una cabra de la bodega! Cógela y lánzala de vuelta a la bodega")
end

local function gallinas(): boolean
	return soltarAnimales("Gallina", 3 + math.min(#Players:GetPlayers(), 3), "¡Gallinas sueltas por la cabina! Atrápalas y devuélvelas a la bodega")
end

local function biberones(): { BasePart }
	local lista: { BasePart } = {}
	for _, o in CollectionService:GetTagged("Objeto") do
		if o:IsA("BasePart") and o.Parent and o:GetAttribute("Tipo") == "Biberon" then
			table.insert(lista, o)
		end
	end
	return lista
end

local function nuevoBiberon()
	local cf = CFrame.new(-5.3, 104.1, -46.8)
	Objetos.crear("Biberon", cf)
	Rafagas.lanzar("Confeti", cf.Position, 0.4)
end

local function bebe(): boolean
	local lista = libres()
	if #lista == 0 then
		return false
	end
	local m = lista[rng:NextInteger(1, #lista)]
	local cuerpo = cuerpoDe(m) :: BasePart
	local e = empezar("Bebe")
	Activos.clonar("Bebe", function(v)
		if not e.vivo or not cuerpo.Parent then
			v:Destroy()
			return
		end
		v:PivotTo(cuerpo.CFrame * CFrame.new(0, -0.8, -0.9) * v:GetPivot())
		pegar(v, cuerpo)
		v.Name = "Bebe"
		v.Parent = carpeta
	end)
	pedir(m, "Biberon", 45)
	if #biberones() == 0 then
		nuevoBiberon()
	end
	aviso("¡Un bebé llora sin parar! Coge el biberón de la cocina y dáselo a su familia", "peligro")
	table.insert(e.limpiar, function()
		if m.Parent and m:GetAttribute("Pedido") == "Biberon" then
			m:SetAttribute("Pedido", "")
		end
		for _, b in biberones() do
			Agarre.soltarObjeto(b)
			b:Destroy()
		end
	end)
	task.spawn(function()
		local fin = os.clock() + 100
		local paso = 0
		while e.vivo do
			task.wait(1)
			paso += 1
			if not m.Parent then
				terminar(e)
				break
			end
			local c = cuerpoDe(m)
			local pos = if c then c.Position else COCINA
			local pedido = m:GetAttribute("Pedido")
			if pedido ~= "Biberon" then
				if feliz(m) then
					rotular(pos + ARRIBA * 2.5, "¡ZZZ!", "Bebe")
					premiar(50, jugadorCercano(pos, 14))
					for _, otro in cerca(pos, 14, nil) do
						sumar(otro, "Satisfaccion", 0.08)
						otro:SetAttribute("Feliz", os.clock())
					end
					aviso("¡Bebé dormido! Toda la fila os lo agradece +50", "bien")
					terminar(e)
					break
				elseif pedido == "" and m:GetAttribute("Estado") == "Sentado" then
					pedir(m, "Biberon", 35)
				end
			end
			if paso % 3 == 0 then
				Sonidos.emitir("Bebe", pos)
				rotular(pos + ARRIBA * 2.5, if rng:NextNumber() < 0.5 then "¡BUAAA!" else "¡UEEE!", "Bebe", 1.2)
			end
			for _, otro in cerca(pos, 14, m) do
				sumar(otro, "Satisfaccion", -0.004)
				local p = otro:GetAttribute("Paciencia")
				if otro:GetAttribute("Pedido") ~= "" and typeof(p) == "number" and p > 2 then
					otro:SetAttribute("Paciencia", p - 1)
				end
				if rng:NextNumber() < 0.04 then
					Pasajeros.reaccionar(otro, "Enfado")
				end
			end
			if #biberones() == 0 and paso % 5 == 0 then
				nuevoBiberon()
			end
			if os.clock() > fin then
				aviso("El bebé se ha dormido de tanto llorar", "info")
				terminar(e)
			end
		end
	end)
	return true
end

local function achis(m: Model, pos: Vector3)
	Rafagas.lanzar("Onda", pos, 1.3)
	Rafagas.lanzar("Salpicadura", pos + ARRIBA, 1.2, VERDE)
	rotular(pos + ARRIBA * 2.5, "¡ACHÍS!", "Grito", 1.6)
	for _, p in sueltos() do
		local delta = p.Position - pos
		local d = delta.Magnitude
		if d < 12 and d > 0.1 then
			Objetos.empujar(p, delta.Unit * 38 * (1 - d / 12) + Vector3.new(0, 10, 0))
		end
	end
	for _, j in Players:GetPlayers() do
		local r = Personajes.raiz(j)
		if r and (r.Position - pos).Magnitude < 9 then
			empujarJugador(j, pos, 40, 22, 1.1)
			RemotoAviso:FireClient(j, "¡Te ha estornudado encima!", "peligro")
		end
	end
	for _, otro in cerca(pos, 7, m) do
		local c = cuerpoDe(otro)
		if c then
			Pasajeros.golpear(otro, 30, (c.Position - pos) * PLANO, "Mojado", Avion.estado.cinturones)
		end
	end
	Pasajeros.asustar(0.15, pos, 12)
end

local function estornudo(): boolean
	local lista = libres()
	if #lista == 0 then
		return false
	end
	local m = lista[rng:NextInteger(1, #lista)]
	local e = empezar("Estornudo")
	pedir(m, "Agua", 50)
	aviso("¡Un pasajero tiene alergia! Dale agua antes de que vuelva a estornudar", "peligro")
	table.insert(e.limpiar, function()
		if m.Parent and m:GetAttribute("Pedido") == "Agua" then
			m:SetAttribute("Pedido", "")
		end
	end)
	task.spawn(function()
		local siguiente = os.clock() + 6
		local avisado = false
		local veces = 0
		while e.vivo do
			task.wait(0.25)
			local c = cuerpoDe(m)
			if not m.Parent or not c then
				terminar(e)
				break
			end
			local pos = c.Position
			local pedido = m:GetAttribute("Pedido")
			if pedido ~= "Agua" then
				if feliz(m) then
					rotular(pos + ARRIBA * 2.5, "¡SALUD!", "Bien")
					premiar(30, jugadorCercano(pos, 12))
					aviso("¡Alergia curada con un vaso de agua! +30", "bien")
					terminar(e)
					break
				elseif pedido == "" and m:GetAttribute("Estado") == "Sentado" then
					pedir(m, "Agua", 40)
				end
			end
			local ahora = os.clock()
			if not avisado and ahora > siguiente - 1.6 then
				avisado = true
				Sonidos.emitir("Estornudo", pos)
				rotular(pos + ARRIBA * 2.5, "¡A... AAA...!", "Grito", 0.9)
			end
			if ahora > siguiente then
				achis(m, pos)
				sumar(m, "Satisfaccion", -0.03)
				veces += 1
				avisado = false
				siguiente = ahora + rng:NextNumber(6, 9)
				if veces >= 7 then
					aviso("Al pasajero se le ha pasado la alergia (y a todos los demás, la paciencia)", "info")
					terminar(e)
				end
			end
		end
	end)
	return true
end

local function volarPasajero(desde: CFrame, hasta: Vector3)
	local nombres = Config.PASAJEROS.VISUALES
	Activos.clonar(nombres[rng:NextInteger(1, #nombres)], function(v)
		local base = v:GetPivot()
		local valor = Instance.new("NumberValue")
		valor.Changed:Connect(function(t)
			local p = desde.Position:Lerp(hasta, t) + Vector3.new(0, math.sin(t * math.pi) * 3, 0)
			v:PivotTo(CFrame.new(p) * desde.Rotation * CFrame.Angles(t * math.pi * 3, t * math.pi, 0) * base)
		end)
		v:PivotTo(desde * base)
		v.Parent = carpeta
		TweenService:Create(valor, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Value = 1 }):Play()
		task.delay(0.85, function()
			rotular(hasta + ARRIBA * 2.5, "¡GRACIAS!", "Bien")
			Rafagas.lanzar("Polvo", hasta, 0.8)
		end)
		task.delay(2.2, function()
			if v.Parent then
				Rafagas.lanzar("Humo", hasta + ARRIBA, 0.8)
				v:Destroy()
			end
			valor:Destroy()
		end)
	end)
end

local function bano(): boolean
	local puerta = avion:FindFirstChild("PuertaBano", true)
	if not puerta or not puerta:IsA("BasePart") then
		return false
	end
	local original = puerta:FindFirstChildOfClass("ProximityPrompt")
	if puerta:GetAttribute("Abierta") == true then
		Avion.puerta(puerta, false)
	end
	local e = empezar("Bano")
	local centro = puerta.Position
	if original then
		original.Enabled = false
	end
	puerta:SetAttribute("Atascada", true)
	local tirar = Instance.new("ProximityPrompt")
	tirar.Name = "Atasco"
	tirar.ActionText = "Tirar de la puerta"
	tirar.ObjectText = "Baño atascado"
	tirar.HoldDuration = 2
	tirar.MaxActivationDistance = 7
	tirar.RequiresLineOfSight = false
	tirar.Parent = puerta
	table.insert(e.limpiar, function()
		tirar:Destroy()
		puerta:SetAttribute("Atascada", nil)
		if original then
			original.Enabled = true
		end
	end)
	aviso("¡Un pasajero se ha quedado encerrado en el baño! Tirad de la puerta", "peligro")
	local function salir(jugador: Player?)
		terminar(e)
		Avion.puerta(puerta, true)
		Sonidos.emitir("Cisterna", centro)
		Rafagas.lanzar("Confeti", centro, 1.1)
		local dentro = CFrame.new(-4.6, Config.SUELO_Y + 1.6, centro.Z) * CFrame.Angles(0, math.pi / 2, 0)
		volarPasajero(dentro, Vector3.new(2, Config.SUELO_Y + 1.6, centro.Z - 1.5))
		if jugador then
			rotular(centro + ARRIBA * 3, "¡LIBRE!", "Bien", 1.3)
			empujarJugador(jugador, centro, 35, 20, 1.1)
			local r = Personajes.raiz(jugador)
			if r then
				Rafagas.lanzar("Bonk", r.Position + ARRIBA, 1)
			end
			premiar(40, jugador)
			for _, m in pasajeros() do
				sumar(m, "Satisfaccion", 0.05)
			end
			aviso(`¡{jugador.DisplayName} ha rescatado al pasajero del baño! +40`, "bien")
		else
			aviso("El pasajero del baño ha salido solo... y muy enfadado", "info")
		end
	end
	tirar.Triggered:Connect(function(jugador)
		if e.vivo then
			salir(jugador)
		end
	end)
	task.spawn(function()
		local fin = os.clock() + 70
		local chillidos = { "¡TOC TOC!", "¡SOCORRO!", "¡NO HAY PAPEL!", "¡QUE ALGUIEN ABRA!" }
		while e.vivo do
			task.wait(2.5)
			if not e.vivo then
				break
			end
			Sonidos.emitir("GolpesPuerta", centro)
			rotular(centro + Vector3.new(1, 2.5, 0), chillidos[rng:NextInteger(1, #chillidos)], "Grito", 0.9)
			for _, m in pasajeros() do
				sumar(m, "Satisfaccion", -0.006)
			end
			if os.clock() > fin then
				salir(nil)
			end
		end
	end)
	return true
end

local function cafeteraLoca(): boolean
	local maquina = avion:FindFirstChild("DispensadorCafe", true)
	if not maquina or not maquina:IsA("BasePart") then
		return false
	end
	local e = empezar("Cafetera")
	local pos = maquina.Position
	local arreglo = 0
	maquina:SetAttribute("Loca", true)
	table.insert(e.limpiar, function()
		maquina:SetAttribute("Loca", nil)
	end)
	aviso("¡La cafetera se ha vuelto loca! Dale con la llave inglesa (F) antes de que explote", "peligro")
	e.usar = function(jugador, tipo, origen)
		if tipo ~= "Llave" or (pos - origen).Magnitude > 8 then
			return
		end
		arreglo += 15
		Rafagas.lanzar("Martillazo", pos, 0.5)
		Sonidos.emitir("GolpeMetal", pos, 0.1)
		Estadisticas.sumar(jugador, "reparar")
		if arreglo >= 100 then
			terminar(e)
			Rafagas.lanzar("Chispas", pos, 1)
			Sonidos.emitir("Reparado", pos)
			rotular(pos + ARRIBA * 2, "¡ARREGLADA!", "Bien")
			premiar(40, jugador)
			aviso("¡Cafetera arreglada a llavazos! +40", "bien")
		end
	end
	task.spawn(function()
		local fin = os.clock() + 45
		local paso = 0
		local chillidos = { "¡BLUP!", "¡FSSSH!", "¡GLUGLÚ!" }
		while e.vivo do
			task.wait(1.3)
			if not e.vivo then
				break
			end
			paso += 1
			Rafagas.lanzar("Vapor", pos, 1)
			Sonidos.emitir("Cafetera", pos)
			local taza = Objetos.crear("Cafe", CFrame.new(pos + Vector3.new(-1, 0.4, 0)))
			taza.AssemblyLinearVelocity = Vector3.new(-rng:NextNumber(10, 18), rng:NextNumber(8, 14), rng:NextNumber(2, 16))
			taza.AssemblyAngularVelocity = Vector3.new(rng:NextNumber(-8, 8), rng:NextNumber(-8, 8), rng:NextNumber(-8, 8))
			Debris:AddItem(taza, 10)
			if paso % 2 == 0 then
				Interacciones.charco(Vector3.new(rng:NextNumber(0, 4.5), Config.SUELO_Y, rng:NextNumber(-50, -43)), "Cafe")
			end
			if paso % 3 == 0 then
				rotular(pos + ARRIBA * 2, chillidos[rng:NextInteger(1, #chillidos)], "Grito", 0.8)
			end
			if os.clock() > fin then
				terminar(e)
				Rafagas.lanzar("ExplosionPequena", pos, 1.2)
				Sonidos.emitir("Explosion", pos)
				Peligros.fuego(Vector3.new(4.6, Config.SUELO_Y + 0.2, -47))
				premiar(-40)
				aviso("¡La cafetera ha explotado! -40", "peligro")
			end
		end
	end)
	return true
end

local function succion(centro: Vector3, salida: Vector3, dt: number)
	for _, p in sueltos() do
		local delta = centro - p.Position
		local d = delta.Magnitude
		if d < 22 and d > 0.1 then
			Objetos.empujar(p, delta.Unit * (1 - d / 22) * 60 * dt + (if d < 3 then salida * 40 * dt else Vector3.zero))
		end
	end
	Pasajeros.succionar(centro, 1.2, 22, Avion.estado.cinturones, dt)
	Avion.danar(0.3 * dt)
end

local function salidaEmergencia(): boolean
	local candidatas: { BasePart } = {}
	for _, nombre in { "PuertaAlaIzq", "PuertaAlaDer" } do
		local d = avion:FindFirstChild(nombre, true)
		if d and d:IsA("BasePart") and d:GetAttribute("Abierta") ~= true then
			table.insert(candidatas, d)
		end
	end
	if #candidatas == 0 then
		return false
	end
	local puerta = candidatas[rng:NextInteger(1, #candidatas)]
	local lado = math.sign(puerta.Position.X)
	local zP = puerta.Position.Z
	local y = Config.SUELO_Y + 2.5
	local z0 = math.clamp(zP + (if rng:NextNumber() < 0.5 then 1 else -1) * rng:NextNumber(13, 18), -48, -4)
	local e = empezar("Salida")
	local modelo = Instance.new("Model")
	modelo.Name = "Espontaneo"
	local cuerpo = Instance.new("Part")
	cuerpo.Name = "Cuerpo"
	cuerpo.Size = Vector3.new(1.8, 2.3, 1.5)
	cuerpo.Color = Config.PASAJEROS.ROPA[rng:NextInteger(1, #Config.PASAJEROS.ROPA)]
	cuerpo.Material = Enum.Material.SmoothPlastic
	cuerpo.Anchored = true
	cuerpo.CanCollide = false
	cuerpo.CFrame = CFrame.new(0, y, z0)
	cuerpo.Parent = modelo
	modelo.PrimaryPart = cuerpo
	modelo:SetAttribute("Tipo", "Pasajero")
	modelo:SetAttribute("Portador", 0)
	CollectionService:AddTag(modelo, "Agarrable")
	modelo.Parent = carpeta
	local visuales = Config.PASAJEROS.VISUALES
	Activos.vestirDinamico(cuerpo, visuales[rng:NextInteger(1, #visuales)], Config.PASAJEROS.ESCALA_VISUAL)
	local placado = false
	local function placar(jugador: Player, cogido: boolean)
		if placado or not e.vivo then
			return
		end
		placado = true
		local pos = cuerpo.Position
		if not cogido then
			local r = Personajes.raiz(jugador)
			local dir = if r then (pos - r.Position) * PLANO else Vector3.xAxis
			cuerpo.Anchored = false
			cuerpo.CanCollide = true
			Objetos.servidor(cuerpo)
			cuerpo.AssemblyLinearVelocity = (if dir.Magnitude > 0.01 then dir.Unit else Vector3.xAxis) * 18 + Vector3.new(0, 12, 0)
			Personajes.ragdoll(jugador, 0.9, (if dir.Magnitude > 0.01 then dir.Unit else Vector3.xAxis) * 24 + Vector3.new(0, 10, 0))
		end
		Rafagas.lanzar("Polvo", pos, 1)
		Rafagas.lanzar("Estrellas", pos + ARRIBA * 2, 1)
		rotular(pos + ARRIBA * 3, "¡PLACAJE!", "Grito", 1.4)
		Sonidos.emitir("Placaje", pos)
		premiar(60, jugador)
		aviso(`¡Placaje de {jugador.DisplayName}! La salida de emergencia sigue cerrada +60`, "bien")
		task.delay(3, function()
			if modelo.Parent then
				Agarre.soltarObjeto(modelo)
				Rafagas.lanzar("Humo", cuerpo.Position, 0.8)
				modelo:Destroy()
			end
			terminar(e)
		end)
	end
	alCoger[modelo] = function(jugador)
		if not placado then
			cuerpo.Anchored = false
			cuerpo.CanCollide = true
			placar(jugador, true)
		end
	end
	table.insert(e.limpiar, function()
		alCoger[modelo] = nil
		if modelo.Parent then
			Agarre.soltarObjeto(modelo)
			modelo:Destroy()
		end
	end)
	aviso("¡Un pasajero quiere abrir la salida de emergencia! ¡Placadle antes de que llegue!", "peligro")
	rotular(cuerpo.Position + ARRIBA * 3, "¡ME QUIERO BAJAR!", "Grito", 1.2)
	task.spawn(function()
		local pos = cuerpo.Position
		local metas = { Vector3.new(0, y, zP), Vector3.new(lado * 4.9, y, zP) }
		local tramo = 1
		local forcejeo = 0
		local grito = 0
		while e.vivo and not placado do
			local dt = task.wait(0.1)
			if placado or not e.vivo then
				break
			end
			local ahora = os.clock()
			for _, j in Players:GetPlayers() do
				local r = Personajes.raiz(j)
				if r and not Personajes.enRagdoll(j) and (r.Position - cuerpo.Position).Magnitude < 3.2 then
					placar(j, false)
					break
				end
			end
			if placado then
				break
			end
			local meta = metas[tramo]
			if meta then
				local delta = meta - pos
				local paso = 3.6 * dt
				if delta.Magnitude <= paso then
					pos = meta
					tramo += 1
					if tramo > #metas then
						forcejeo = ahora + 5
					end
				else
					pos += delta.Unit * paso
				end
				local mira = if delta.Magnitude > 0.05 then pos + delta else pos - Vector3.zAxis
				cuerpo.CFrame = CFrame.lookAt(pos, mira) + Vector3.new(0, math.abs(math.sin(ahora * 9)) * 0.5, 0)
			else
				cuerpo.CFrame = CFrame.lookAt(pos, Vector3.new(lado * 8, pos.Y, pos.Z)) * CFrame.Angles(0, 0, math.sin(ahora * 20) * 0.15)
				if ahora > grito then
					grito = ahora + 1.2
					Sonidos.emitir("GolpeMetal", puerta.Position, 0.5)
					rotular(pos + ARRIBA * 3, if rng:NextNumber() < 0.5 then "¡AIRE FRESCO!" else "¡ESTA ES MI PARADA!", "Grito")
				end
				if ahora > forcejeo then
					break
				end
			end
		end
		if placado or not e.vivo then
			return
		end
		local centro = Vector3.new(lado * 6.4, 103.25, zP)
		local fuera = Vector3.new(lado, 0, 0)
		Avion.puerta(puerta, true)
		Sonidos.emitir("Succion", centro)
		Rafagas.lanzar("Onda", centro, 1.2)
		cuerpo.Anchored = false
		cuerpo.CanCollide = true
		Objetos.servidor(cuerpo)
		cuerpo.AssemblyLinearVelocity = fuera * 60 + Vector3.new(0, 10, 20)
		rotular(centro + ARRIBA * 2, "¡ADIÓOOS!", "Grito", 1.4)
		Debris:AddItem(modelo, 4)
		local marca = Instance.new("Part")
		marca.Name = "Brecha"
		marca.Size = Vector3.new(1, 3, 4.5)
		marca.Anchored = true
		marca.CanCollide = false
		marca.CanQuery = false
		marca.CanTouch = false
		marca.Transparency = 1
		marca.CFrame = CFrame.lookAt(centro, Vector3.new(0, centro.Y, centro.Z))
		local adjunto = Instance.new("Attachment")
		adjunto.CFrame = CFrame.Angles(0, math.pi, 0)
		adjunto.Parent = marca
		VFX.viento(adjunto).Rate = 80
		marca:SetAttribute("Fuerza", 0.8)
		CollectionService:AddTag(marca, "Brecha")
		marca.Parent = carpeta
		table.insert(e.limpiar, function()
			marca:Destroy()
		end)
		Pasajeros.asustar(0.5)
		premiar(-80)
		aviso("¡Ha abierto la salida de emergencia! Cerrad la puerta (E) antes de que salga todo volando -80", "peligro")
		while e.vivo and puerta:GetAttribute("Abierta") == true do
			succion(centro, fuera, task.wait(0.1))
		end
		if e.vivo then
			Sonidos.emitir("Reparado", centro)
			local quien = jugadorCercano(centro, 10)
			if quien then
				Estadisticas.sumar(quien, "caos")
			end
			aviso("¡Salida de emergencia cerrada!", "bien")
			terminar(e)
		end
	end)
	return true
end

local function peste(): boolean
	local e = empezar("Peste")
	local nube = Instance.new("Part")
	nube.Name = "Peste"
	nube.Anchored = true
	nube.CanCollide = false
	nube.CanQuery = false
	nube.CanTouch = false
	nube.Transparency = 1
	nube.Size = Vector3.one
	nube.Position = COCINA
	for _, textura in { "Humo1", "Humo2" } do
		local humo = Instance.new("ParticleEmitter")
		humo.Texture = VFX.textura(textura)
		humo.Color = ColorSequence.new(Color3.fromRGB(150, 210, 80), Color3.fromRGB(96, 150, 50))
		humo.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 3), NumberSequenceKeypoint.new(1, 8) })
		humo.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.2, 0.45), NumberSequenceKeypoint.new(1, 1) })
		humo.Lifetime = NumberRange.new(2.5, 3.5)
		humo.Rate = 8
		humo.Speed = NumberRange.new(1, 3)
		humo.SpreadAngle = Vector2.new(180, 180)
		humo.Rotation = NumberRange.new(0, 360)
		humo.RotSpeed = NumberRange.new(-30, 30)
		humo.Drag = 1
		humo.Parent = nube
	end
	nube:SetAttribute("Radio", 8)
	CollectionService:AddTag(nube, "Peste")
	nube.Parent = carpeta
	local vida = 100
	table.insert(e.limpiar, function()
		nube:Destroy()
	end)
	Sonidos.emitir("Ding", COCINA)
	Rafagas.lanzar("Humo", COCINA, 1.4, VERDE)
	rotular(COCINA + ARRIBA * 2, "¡PUAJ!", "Asco", 1.3)
	aviso("¡Alguien ha calentado pescado en el microondas! Dispersa la peste con el extintor", "peligro")
	e.usar = function(jugador, tipo, origen, dir)
		if tipo ~= "Extintor" then
			return
		end
		local delta = nube.Position - origen
		if delta.Magnitude > 16 or (delta.Magnitude > 2 and delta.Unit:Dot(dir) < 0.45) then
			return
		end
		vida -= 6
		nube.Position += Vector3.new(dir.X, 0, dir.Z) * 0.8
		if vida <= 0 then
			local pos = nube.Position
			terminar(e)
			Rafagas.lanzar("Humo", pos, 1.8, VERDE)
			rotular(pos + ARRIBA * 2, "¡FUSH!", "Bien", 1.3)
			premiar(35, jugador)
			aviso("¡Peste dispersada! +35", "bien")
		end
	end
	task.spawn(function()
		local fin = os.clock() + 75
		local objetivo = COCINA
		local cambio = 0
		local paso = 0
		while e.vivo do
			local dt = task.wait(0.25)
			if not e.vivo then
				break
			end
			local ahora = os.clock()
			paso += 1
			local pos = nube.Position
			if ahora > cambio or (objetivo - pos).Magnitude < 1.5 then
				cambio = ahora + 6
				local lista = pasajeros()
				local elegido = if #lista > 0 then cuerpoDe(lista[rng:NextInteger(1, #lista)]) else nil
				objetivo = if elegido then Vector3.new(elegido.Position.X * 0.5, 104, elegido.Position.Z) else Vector3.new(0, 104, rng:NextNumber(-45, -5))
			end
			local delta = objetivo - pos
			if delta.Magnitude > 0.1 then
				nube.Position = pos + delta.Unit * math.min(delta.Magnitude, 1.8 * dt)
			end
			if paso % 4 == 0 then
				local enferman = cerca(pos, 8, nil)
				for _, m in enferman do
					sumar(m, "Satisfaccion", -0.01)
				end
				if #enferman > 0 and paso % 12 == 0 then
					local m = enferman[rng:NextInteger(1, #enferman)]
					Pasajeros.reaccionar(m, "Mareo")
					if m:GetAttribute("Mareado") ~= true then
						m:SetAttribute("Mareado", true)
						task.delay(rng:NextNumber(3, 6), function()
							if m.Parent and m:GetAttribute("Mareado") == true then
								m:SetAttribute("Mareado", false)
								m:SetAttribute("Vomito", os.clock())
								sumar(m, "Satisfaccion", -0.06)
							end
						end)
					end
					local c = cuerpoDe(m)
					if c then
						rotular(c.Position + ARRIBA * 2.5, "¡PUAJ!", "Asco")
					end
				end
			end
			if ahora > fin then
				aviso("La peste se ha ido sola (por fin)", "info")
				terminar(e)
			end
		end
	end)
	return true
end

local function disco(): boolean
	local e = empezar("Disco")
	local fin = Workspace:GetServerTimeNow() + 14
	avion:SetAttribute("Disco", fin)
	table.insert(e.limpiar, function()
		avion:SetAttribute("Disco", nil)
	end)
	aviso("¡Turbulencia disco! Que nadie deje de bailar", "info")
	task.spawn(function()
		while e.vivo and Workspace:GetServerTimeNow() < fin do
			task.wait(1)
			for _, p in Objetos.sueltos() do
				Objetos.empujar(p, Vector3.new(rng:NextNumber(-3, 3), rng:NextNumber(8, 13), rng:NextNumber(-3, 3)))
			end
			local lista = pasajeros()
			for _ = 1, math.min(3, #lista) do
				local m = lista[rng:NextInteger(1, #lista)]
				Pasajeros.reaccionar(m, "Feliz")
				sumar(m, "Satisfaccion", 0.02)
			end
			Rafagas.lanzar("Confeti", Vector3.new(0, 108, rng:NextNumber(-45, -5)), 0.8)
		end
		terminar(e)
	end)
	return true
end

local function borracho(): boolean
	if Avion.fase() ~= "Vuelo" then
		return false
	end
	local estado = Avion.estado
	local e = empezar("Borracho")
	estado.autopiloto = true
	avion:SetAttribute("Borracho", true)
	table.insert(e.limpiar, function()
		avion:SetAttribute("Borracho", nil)
	end)
	aviso("¡El piloto automático se ha bebido el champán de primera! Desconéctalo 3 veces desde la cabina", "peligro")
	rotular(CABINA, "¡HIP!", "Borracho", 1.4)
	task.spawn(function()
		local fin = os.clock() + 60
		local cortes = 0
		local reconectar = 0
		local hipo = os.clock() + 2
		while e.vivo do
			local dt = task.wait(0.1)
			if Avion.fase() ~= "Vuelo" then
				terminar(e)
				break
			end
			local t = os.clock()
			if estado.autopiloto then
				reconectar = 0
				estado.viento = math.sin(t * 0.7) * 1.6
				estado.alabeo = math.clamp(estado.alabeo + math.sin(t * 1.6) * 40 * dt, -32, 32)
				estado.cabeceo = math.clamp(estado.cabeceo + math.sin(t * 1.1) * 10 * dt, -12, 14)
				if t > hipo then
					hipo = t + rng:NextNumber(2.5, 4)
					rotular(CABINA, "¡HIP!", "Borracho", 1.2)
					Sonidos.emitir("Hipo", CABINA)
					Peligros.sacudida(0.3)
				end
			elseif reconectar == 0 then
				cortes += 1
				if cortes >= 3 then
					premiar(45, Avion.piloto())
					rotular(CABINA, "¡ZZZ!", "Borracho")
					aviso("¡Piloto automático sobrio! Se ha ido a dormir la mona +45", "bien")
					terminar(e)
					break
				end
				reconectar = t + 3
				aviso(`¡Desconectado! ({cortes}/3)... pero sigue con hipo`, "info")
			elseif t > reconectar then
				reconectar = 0
				estado.autopiloto = true
				rotular(CABINA, "¡HIP! ¡MANDO YO!", "Borracho", 1.3)
				aviso("¡El piloto automático se ha vuelto a conectar solo!", "peligro")
			end
			if t > fin then
				aviso("El piloto automático se ha quedado dormido... y sobrio", "info")
				terminar(e)
			end
		end
	end)
	return true
end

local function carrito(): boolean
	local carro: BasePart? = nil
	for _, o in CollectionService:GetTagged("Objeto") do
		if o:IsA("BasePart") and o.Parent and o:GetAttribute("Tipo") == "Carrito" and not o.Anchored and not Agarre.portador(o) and Agarre.delServidor(o) then
			carro = o
			break
		end
	end
	local c = carro
	if not c then
		return false
	end
	local e = empezar("Carrito")
	aviso("¡El carrito de comida se ha desbocado! Cógelo para pararlo", "peligro")
	task.spawn(function()
		local dir = if c.Position.Z < -25 then 1 else -1
		local fin = os.clock() + 14
		local bocina = 0
		while e.vivo do
			task.wait(0.1)
			if not c.Parent then
				terminar(e)
				break
			end
			local quien = Agarre.portador(c)
			if quien then
				premiar(25, quien)
				aviso(`¡{quien.DisplayName} ha frenado el carrito desbocado! +25`, "bien")
				terminar(e)
				break
			end
			local p = c.Position
			if os.clock() > fin then
				Rafagas.lanzar("Bonk", p, 1.4)
				aviso("El carrito se ha estampado contra la mampara", "info")
				terminar(e)
				break
			end
			if not Agarre.delServidor(c) then
				continue
			end
			if dir > 0 and p.Z > -6 then
				dir = -1
			elseif dir < 0 and p.Z < -45 then
				dir = 1
			end
			c.AssemblyLinearVelocity = Vector3.new(-p.X * 4, c.AssemblyLinearVelocity.Y, dir * 24)
			c.AssemblyAngularVelocity = Vector3.zero
			c.CFrame = CFrame.lookAt(p, p + Vector3.new(0, 0, dir))
			if os.clock() > bocina then
				bocina = os.clock() + 1.1
				Sonidos.emitir("Bocina", p)
				Rafagas.lanzar("Bocina", p + ARRIBA * 2)
			end
		end
	end)
	return true
end

local function avalancha(): boolean
	local centro = Vector3.new(0, 108, rng:NextNumber(-40, -12))
	local abiertos = Cabina.reventar(centro, 9)
	if #abiertos == 0 then
		return false
	end
	local e = empezar("Avalancha", centro)
	aviso("¡Avalancha de equipaje! ¡Cuidado con la cabeza!", "peligro")
	Rafagas.lanzar("Polvo", centro, 1.2)
	rotular(centro, "¡CATAPLÁN!", "Grito", 1.4)
	task.delay(0.3, function()
		local bonk: { [Player]: boolean } = {}
		for _, pos in abiertos do
			local lado = math.sign(pos.X)
			local maleta = Objetos.crear("Maleta", CFrame.new(pos.X - lado * 1.2, pos.Y - 0.8, pos.Z), nil, `Maleta{rng:NextInteger(1, 3)}`)
			maleta.AssemblyLinearVelocity = Vector3.new(-lado * rng:NextNumber(4, 8), 2, rng:NextNumber(-3, 3))
			for _, j in Players:GetPlayers() do
				local r = Personajes.raiz(j)
				if r and not bonk[j] and ((r.Position - pos) * PLANO).Magnitude < 3.5 then
					bonk[j] = true
					Personajes.ragdoll(j, 1.2, Vector3.new(-lado * 8, 6, 0))
					Rafagas.lanzar("Bonk", r.Position + ARRIBA * 2, 1.2)
					RemotoAviso:FireClient(j, "¡Te ha caído una maleta en la cabeza!", "peligro")
				end
			end
			for _, m in cerca(Vector3.new(pos.X, 102, pos.Z), 3, nil) do
				Pasajeros.golpear(m, 35, -ARRIBA, "Golpe", Avion.estado.cinturones)
			end
		end
		terminar(e)
	end)
	return true
end

local EVENTOS: { Def } = {
	{ nombre = "Cabra", f = cabra, peso = 3 },
	{ nombre = "Gallinas", f = gallinas, peso = 3 },
	{ nombre = "Bebe", f = bebe, peso = 3 },
	{ nombre = "Bano", f = bano, peso = 3 },
	{ nombre = "Cafetera", f = cafeteraLoca, peso = 3 },
	{ nombre = "Salida", f = salidaEmergencia, peso = 2 },
	{ nombre = "Peste", f = peste, peso = 3 },
	{ nombre = "Disco", f = disco, peso = 2 },
	{ nombre = "Borracho", f = borracho, peso = 2 },
	{ nombre = "Estornudo", f = estornudo, peso = 3 },
	{ nombre = "Carrito", f = carrito, peso = 2 },
	{ nombre = "Avalancha", f = avalancha, peso = 2 },
}

function Caos.lanzar(nombre: string): boolean
	if activos[nombre] then
		return false
	end
	for _, ev in EVENTOS do
		if ev.nombre == nombre then
			return ev.f()
		end
	end
	return false
end

local function cuantos(): number
	local n = 0
	for _ in activos do
		n += 1
	end
	return n
end

local function alguno()
	local opciones: { Def } = {}
	local total = 0
	for _, ev in EVENTOS do
		if not activos[ev.nombre] and ev.nombre ~= ultimo then
			table.insert(opciones, ev)
			total += ev.peso
		end
	end
	for _ = 1, 4 do
		if #opciones == 0 then
			return
		end
		local tirada = rng:NextNumber() * total
		for i, ev in opciones do
			tirada -= ev.peso
			if tirada <= 0 then
				if ev.f() then
					return
				end
				total -= ev.peso
				table.remove(opciones, i)
				break
			end
		end
	end
end

function Caos.bonus(): number
	return bonus
end

function Caos.sumarBonus(cantidad: number)
	bonus += cantidad
end

function Caos.detener()
	activo = false
	generacion += 1
	local lista: { Evento } = {}
	for _, e in activos do
		table.insert(lista, e)
	end
	for _, e in lista do
		terminar(e)
	end
	table.clear(animales)
	table.clear(alCoger)
	ultimo = ""
	carpeta:ClearAllChildren()
end

function Caos.activar()
	Caos.detener()
	activo = true
	bonus = 0
	local mia = generacion
	local R = Config.RITMO
	task.spawn(function()
		while activo and generacion == mia and Avion.estado.enTierra do
			task.wait(1)
		end
		task.wait(R.CALMA + R.CAOS_PRIMERO)
		while activo and generacion == mia do
			local fase = Avion.fase()
			if (fase == "Vuelo" or fase == "Aproximacion") and cuantos() < 1 + math.floor(#Players:GetPlayers() / 2) then
				alguno()
			end
			task.wait(rng:NextNumber(R.CAOS_MIN, R.CAOS_MAX) / Peligros.intensidad())
		end
	end)
end

function Caos.iniciar()
	for nombre, id in ModelosCaos.IDS do
		local caja = ModelosCaos.CAJAS[nombre]
		if caja then
			Activos.registrar(nombre, id, caja)
		end
	end
	Agarre.permitir(function(jugador, objeto)
		local f = alCoger[objeto]
		if f then
			f(jugador)
		end
		return true
	end)
	Agarre.alSoltar(function(jugador, _, raiz)
		local a = animales[raiz]
		if a then
			a.soltado = os.clock()
			a.quien = jugador
		end
	end)
	RemotoUsar.OnServerEvent:Connect(function(jugador, mirada)
		local ahora = os.clock()
		if (usos[jugador] or 0) > ahora or next(activos) == nil then
			return
		end
		usos[jugador] = ahora + Config.HERRAMIENTAS.CADENCIA
		local tipo = Agarre.tipo(jugador)
		local raiz = Personajes.raiz(jugador)
		if not tipo or not raiz or Personajes.enRagdoll(jugador) then
			return
		end
		local dir = raiz.CFrame.LookVector
		if typeof(mirada) == "Vector3" and mirada == mirada and mirada.Magnitude > 0.5 and mirada.Magnitude < 1.5 then
			dir = mirada.Unit
		end
		local origen = raiz.Position + ARRIBA * 1.5
		for _, e in activos do
			local f = e.usar
			if f then
				f(jugador, tipo, origen, dir)
			end
		end
	end)
	Players.PlayerRemoving:Connect(function(jugador)
		golpes[jugador] = nil
		usos[jugador] = nil
	end)
	Estado:GetAttributeChangedSignal("Fase"):Connect(function()
		if Estado:GetAttribute("Fase") == "Vuelo" then
			Caos.activar()
		else
			Caos.detener()
		end
	end)
	if RunService:IsStudio() then
		Workspace:GetAttributeChangedSignal("PruebaCaos"):Connect(function()
			local v = Workspace:GetAttribute("PruebaCaos")
			if typeof(v) == "string" and v ~= "" then
				Workspace:SetAttribute("PruebaCaos", nil)
				task.spawn(Caos.lanzar, v)
			end
		end)
	end
end

return Caos
