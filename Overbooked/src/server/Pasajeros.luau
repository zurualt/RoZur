--!strict
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Activos = require(script.Parent.Activos)
local Agarre = require(script.Parent.Agarre)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent

local P = Config.PASAJEROS

type Pasajero = {
	modelo: Model,
	cuerpo: BasePart,
	asiento: BasePart?,
	servir: ProximityPrompt,
	calmar: ProximityPrompt,
}

local Pasajeros = {}

local avion = Workspace:WaitForChild("Avion") :: Model
local carpeta = avion:WaitForChild("Pasajeros") :: Folder
local asientos: { BasePart } = {}
local ocupacion: { [BasePart]: Pasajero } = {}
local lista: { [Model]: Pasajero } = {}
local rng = Random.new()
local cuenta = { embarcados = 0, perdidos = 0, servidos = 0 }
local riesgo = 1

local function soldar(a: BasePart, b: BasePart)
	local w = Instance.new("WeldConstraint")
	w.Part0 = a
	w.Part1 = b
	w.Parent = a
end

local function parte(nombre: string, tamano: Vector3, color: Color3, forma: Enum.PartType?): Part
	local p = Instance.new("Part")
	p.Name = nombre
	p.Size = tamano
	p.Color = color
	p.Material = Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	if forma then
		p.Shape = forma
	end
	return p
end

local function sentar(p: Pasajero, asiento: BasePart)
	local agarrador = Agarre.portador(p.modelo)
	if agarrador then
		Agarre.soltar(agarrador)
	end
	p.asiento = asiento
	ocupacion[asiento] = p
	p.cuerpo.Anchored = true
	p.modelo:PivotTo(asiento.CFrame * CFrame.new(0, asiento.Size.Y / 2 + p.cuerpo.Size.Y / 2, 0.25))
	p.modelo:SetAttribute("Estado", "Sentado")
end

local function levantar(p: Pasajero)
	local asiento = p.asiento
	if asiento then
		ocupacion[asiento] = nil
	end
	p.asiento = nil
	p.cuerpo.Anchored = false
	pcall(function()
		p.cuerpo:SetNetworkOwner(nil)
	end)
	p.modelo:SetAttribute("Estado", "Suelto")
	p.modelo:SetAttribute("Pedido", "")
end

local function coincide(pedido: string, tipo: string?): boolean
	return tipo ~= nil and (tipo == pedido or (tipo == "Bandeja" and pedido == "Hamburguesa"))
end

local function quitarRacion(objeto: Instance): boolean
	local raciones = objeto:GetAttribute("Raciones")
	if typeof(raciones) == "number" and raciones > 1 then
		objeto:SetAttribute("Raciones", raciones - 1)
		return true
	end
	return false
end

local function atender(modelo: Model)
	local s = modelo:GetAttribute("Satisfaccion")
	modelo:SetAttribute("Satisfaccion", math.min(1, (if typeof(s) == "number" then s else 0.5) + P.SUBIDA_SERVIR))
	modelo:SetAttribute("Pedido", "")
	modelo:SetAttribute("Feliz", os.clock())
	cuenta.servidos += 1
end

local function reaccion(modelo: Model, nombre: string)
	modelo:SetAttribute("Reaccion", nombre)
	modelo:SetAttribute("ReaccionMarca", os.clock())
end

local function crear(indice: number): Pasajero
	local modelo = Instance.new("Model")
	modelo.Name = "Pasajero" .. indice
	local piel = P.PIELES[rng:NextInteger(1, #P.PIELES)]
	local ropa = P.ROPA[rng:NextInteger(1, #P.ROPA)]
	local cuerpo = parte("Cuerpo", Vector3.new(1.8, 2.3, 1.5), ropa)
	cuerpo.CustomPhysicalProperties = PhysicalProperties.new(0.6, 0.5, 0.2)
	cuerpo.Parent = modelo
	local cabeza = parte("Cabeza", Vector3.new(1.6, 1.6, 1.6), piel, Enum.PartType.Ball)
	cabeza.CFrame = cuerpo.CFrame * CFrame.new(0, 1.85, 0)
	cabeza.Parent = modelo
	soldar(cuerpo, cabeza)
	for _, x in { -0.32, 0.32 } do
		local ojo = parte("Ojo", Vector3.new(0.2, 0.28, 0.1), Color3.fromRGB(27, 27, 33))
		ojo.CanCollide = false
		ojo.Massless = true
		ojo.CFrame = cabeza.CFrame * CFrame.new(x, 0.15, -0.76)
		ojo.Parent = modelo
		soldar(cabeza, ojo)
	end
	local piernas = parte("Piernas", Vector3.new(1.6, 0.6, 1.8), Color3.fromRGB(52, 56, 63))
	piernas.CFrame = cuerpo.CFrame * CFrame.new(0, -0.85, -0.9)
	piernas.Massless = true
	piernas.Parent = modelo
	soldar(cuerpo, piernas)
	modelo.PrimaryPart = cuerpo
	modelo:SetAttribute("Pedido", "")
	modelo:SetAttribute("Paciencia", 0)
	modelo:SetAttribute("Miedo", 0)
	modelo:SetAttribute("Satisfaccion", 0.7)
	modelo:SetAttribute("Estado", "Sentado")
	modelo:SetAttribute("Portador", 0)
	CollectionService:AddTag(modelo, "Agarrable")
	CollectionService:AddTag(modelo, "Pasajero")

	local servir = Instance.new("ProximityPrompt")
	servir.Name = "Servir"
	servir.ActionText = "Servir"
	servir.ObjectText = "Pasajero"
	servir.KeyboardKeyCode = Enum.KeyCode.E
	servir.MaxActivationDistance = 7
	servir.RequiresLineOfSight = false
	servir.Enabled = false
	servir.Parent = cuerpo
	local calmar = Instance.new("ProximityPrompt")
	calmar.Name = "Calmar"
	calmar.ActionText = "Calmar"
	calmar.ObjectText = "Pasajero asustado"
	calmar.KeyboardKeyCode = Enum.KeyCode.R
	calmar.HoldDuration = 1.2
	calmar.MaxActivationDistance = 7
	calmar.RequiresLineOfSight = false
	calmar.Enabled = false
	calmar.Parent = cuerpo

	local p: Pasajero = { modelo = modelo, cuerpo = cuerpo, asiento = nil, servir = servir, calmar = calmar }
	lista[modelo] = p

	servir.Triggered:Connect(function(jugador)
		local pedido = modelo:GetAttribute("Pedido")
		if typeof(pedido) ~= "string" or pedido == "" then
			return
		end
		local objeto = Agarre.sostenido(jugador)
		if not objeto or not coincide(pedido, Agarre.tipo(jugador)) then
			RemotoAviso:FireClient(jugador, `Quiere {Config.ICONOS[pedido] or pedido}`, "info")
			return
		end
		if not quitarRacion(objeto) then
			Agarre.consumir(jugador)
		end
		atender(modelo)
	end)
	calmar.Triggered:Connect(function()
		modelo:SetAttribute("Miedo", 0)
		local s = modelo:GetAttribute("Satisfaccion")
		modelo:SetAttribute("Satisfaccion", math.min(1, (if typeof(s) == "number" then s else 0.5) + 0.05))
	end)
	modelo:GetAttributeChangedSignal("Pedido"):Connect(function()
		servir.Enabled = modelo:GetAttribute("Pedido") ~= ""
		local pedido = modelo:GetAttribute("Pedido")
		servir.ObjectText = if typeof(pedido) == "string" and pedido ~= "" then `Quiere {Config.ICONOS[pedido] or pedido}` else "Pasajero"
	end)
	modelo:GetAttributeChangedSignal("Miedo"):Connect(function()
		local m = modelo:GetAttribute("Miedo")
		calmar.Enabled = typeof(m) == "number" and m > 0.5
	end)
	modelo.Parent = carpeta
	local visual = P.VISUALES[rng:NextInteger(1, #P.VISUALES)]
	if Activos.tiene(visual) then
		cabeza.Transparency = 1
		piernas.Transparency = 1
		for _, d in modelo:GetChildren() do
			if d.Name == "Ojo" and d:IsA("BasePart") then
				d.Transparency = 1
			end
		end
		Activos.vestirDinamico(cuerpo, visual, P.ESCALA_VISUAL)
	end
	return p
end

function Pasajeros.ocupado(asiento: BasePart): boolean
	if ocupacion[asiento] then
		return true
	end
	return asiento:IsA("Seat") and asiento.Occupant ~= nil
end

local function libre(cerca: Vector3?, radio: number?): BasePart?
	local mejor, distancia = nil, radio or math.huge
	for _, asiento in asientos do
		if not Pasajeros.ocupado(asiento) then
			local d = if cerca then (asiento.Position - cerca).Magnitude else 0
			if d < distancia then
				mejor, distancia = asiento, d
				if not cerca then
					break
				end
			end
		end
	end
	return mejor
end

function Pasajeros.embarcar(cantidad: number, nivelRiesgo: number)
	Pasajeros.limpiar()
	riesgo = nivelRiesgo
	local orden: { BasePart } = {}
	for _, asiento in asientos do
		if not Pasajeros.ocupado(asiento) then
			table.insert(orden, asiento)
		end
	end
	for i = #orden, 2, -1 do
		local j = rng:NextInteger(1, i)
		orden[i], orden[j] = orden[j], orden[i]
	end
	for i = 1, math.min(cantidad, #orden) do
		local p = crear(i)
		sentar(p, orden[i])
	end
	cuenta.embarcados = math.min(cantidad, #orden)
end

function Pasajeros.limpiar()
	for modelo in lista do
		Agarre.soltarObjeto(modelo)
		modelo:Destroy()
	end
	table.clear(lista)
	table.clear(ocupacion)
	cuenta.embarcados = 0
	cuenta.perdidos = 0
	cuenta.servidos = 0
end

local function sumar(modelo: Model, atributo: string, cantidad: number)
	local v = modelo:GetAttribute(atributo)
	modelo:SetAttribute(atributo, math.clamp((if typeof(v) == "number" then v else 0) + cantidad, 0, 1))
end

function Pasajeros.asustar(cantidad: number, centro: Vector3?, radio: number?)
	for modelo, p in lista do
		if not centro or (p.cuerpo.Position - centro).Magnitude <= (radio or 15) then
			sumar(modelo, "Miedo", cantidad)
		end
	end
end

local function empujar(p: Pasajero, velocidad: Vector3)
	if Agarre.portador(p.modelo) then
		return
	end
	if p.asiento then
		levantar(p)
	elseif not Agarre.delServidor(p.cuerpo) then
		return
	end
	p.cuerpo.AssemblyLinearVelocity += velocidad
	p.cuerpo.AssemblyAngularVelocity += Vector3.new(rng:NextNumber(-6, 6), rng:NextNumber(-6, 6), rng:NextNumber(-6, 6))
end

function Pasajeros.sacudir(magnitud: number, cinturones: boolean)
	for _, p in lista do
		local suelto = p.asiento == nil
		if suelto or (not cinturones and rng:NextNumber() < magnitud * 0.35) then
			local dir = Vector3.new(rng:NextNumber(-1, 1), rng:NextNumber(0.5, 1.2), rng:NextNumber(-1, 1))
			empujar(p, dir * Config.TURBULENCIA.IMPULSO_PASAJEROS * magnitud)
		end
	end
	Pasajeros.asustar(magnitud * 0.25)
end

function Pasajeros.flotar(cinturones: boolean)
	for _, p in lista do
		if p.asiento == nil or not cinturones then
			empujar(p, Vector3.new(rng:NextNumber(-4, 4), rng:NextNumber(12, 22), rng:NextNumber(-4, 4)))
		end
	end
	Pasajeros.asustar(0.5)
end

function Pasajeros.succionar(centro: Vector3, fuerza: number, radio: number, cinturones: boolean, dt: number)
	for _, p in lista do
		local delta = centro - p.cuerpo.Position
		local d = delta.Magnitude
		if d < radio and d > 0.1 and not Agarre.portador(p.modelo) and (p.asiento or Agarre.delServidor(p.cuerpo)) then
			if p.asiento then
				if not cinturones and rng:NextNumber() < (1 - d / radio) * 0.25 * dt * 10 then
					levantar(p)
				end
			else
				p.cuerpo.AssemblyLinearVelocity += delta.Unit * fuerza * (1 - d / radio) * dt * 60
			end
			sumar(p.modelo, "Miedo", 0.05 * dt * 10)
		end
	end
end

function Pasajeros.desde(instancia: Instance): Model?
	local actual: Instance? = instancia
	while actual and actual ~= carpeta do
		if actual:IsA("Model") and lista[actual] then
			return actual
		end
		actual = actual.Parent
	end
	return nil
end

function Pasajeros.cercano(posicion: Vector3, radio: number): Model?
	local mejor: Model? = nil
	local distancia = radio
	for modelo, p in lista do
		local d = (p.cuerpo.Position - posicion).Magnitude
		if d < distancia and not Agarre.portador(modelo) then
			mejor, distancia = modelo, d
		end
	end
	return mejor
end

function Pasajeros.servirCon(modelo: Model, objeto: BasePart): boolean
	local pedido = modelo:GetAttribute("Pedido")
	local tipo = objeto:GetAttribute("Tipo")
	if typeof(pedido) ~= "string" or pedido == "" or typeof(tipo) ~= "string" or not coincide(pedido, tipo) then
		return false
	end
	if not quitarRacion(objeto) then
		Agarre.soltarObjeto(objeto)
		objeto:Destroy()
	end
	atender(modelo)
	return true
end

function Pasajeros.golpear(modelo: Model, impacto: number, direccion: Vector3, motivo: string, cinturones: boolean)
	local p = lista[modelo]
	if not p or Agarre.portador(modelo) then
		return
	end
	sumar(modelo, "Miedo", math.clamp(impacto / 120, 0.1, 0.6))
	sumar(modelo, "Satisfaccion", -(math.clamp(impacto / 400, 0.03, 0.2) + (if motivo == "Quemado" then 0.12 else 0)))
	reaccion(modelo, motivo)
	if impacto > (if cinturones then 85 else 45) then
		local d = if direccion.Magnitude > 0.01 then direccion.Unit else Vector3.yAxis
		empujar(p, d * math.min(impacto, 90) * 0.35 + Vector3.new(0, 8, 0))
	end
end

function Pasajeros.rociar(origen: Vector3, direccion: Vector3, alcance: number)
	local ahora = os.clock()
	for modelo, p in lista do
		local delta = p.cuerpo.Position - origen
		local d = delta.Magnitude
		if d < alcance and d > 0.1 and delta.Unit:Dot(direccion) > 0.6 and not Agarre.portador(modelo) then
			if p.asiento then
				local marca = modelo:GetAttribute("ReaccionMarca")
				if typeof(marca) ~= "number" or ahora - marca > 2 then
					reaccion(modelo, "Mojado")
					sumar(modelo, "Satisfaccion", -0.02)
				end
			elseif Agarre.delServidor(p.cuerpo) then
				p.cuerpo.AssemblyLinearVelocity += direccion * 18 * (1 - d / alcance)
			end
		end
	end
end

function Pasajeros.reaccionar(modelo: Model, nombre: string)
	if lista[modelo] then
		reaccion(modelo, nombre)
	end
end

function Pasajeros.resentar()
	for _, p in lista do
		if not p.asiento and not Agarre.portador(p.modelo) then
			local asiento = libre(nil, nil)
			if asiento then
				sentar(p, asiento)
			end
		end
	end
end

function Pasajeros.resumen(): (number, number, number, number)
	local total, satisfaccion = 0, 0
	for modelo in lista do
		total += 1
		local s = modelo:GetAttribute("Satisfaccion")
		satisfaccion += if typeof(s) == "number" then s else 0.5
	end
	return total, cuenta.perdidos, if total > 0 then satisfaccion / total else 0, cuenta.servidos
end

function Pasajeros.iniciar()
	local carpetaAsientos = avion:WaitForChild("Asientos")
	for _, d in carpetaAsientos:GetChildren() do
		if d:IsA("BasePart") and d.Name == "Asiento" then
			table.insert(asientos, d)
		end
	end
	table.sort(asientos, function(a, b)
		local ia, ib = a:GetAttribute("Indice"), b:GetAttribute("Indice")
		return (if typeof(ia) == "number" then ia else 0) < (if typeof(ib) == "number" then ib else 0)
	end)

	Agarre.antesDeAgarrar(function(objeto)
		if objeto:IsA("Model") then
			local p = lista[objeto]
			if p and p.asiento then
				levantar(p)
				sumar(objeto, "Miedo", 0.3)
			end
		end
	end)

	Agarre.alSoltar(function(_, objeto, raiz)
		if not objeto:IsA("Model") then
			return
		end
		local p = lista[objeto]
		if not p then
			return
		end
		task.delay(0.3, function()
			if not objeto.Parent or p.asiento or Agarre.portador(objeto) then
				return
			end
			local asiento = libre(raiz.Position, P.DISTANCIA_ASIENTO)
			if asiento and raiz.AssemblyLinearVelocity.Magnitude < 20 then
				sentar(p, asiento)
			end
		end)
	end)

	task.spawn(function()
		while true do
			task.wait(1)
			for modelo, p in lista do
				if not modelo.Parent then
					lista[modelo] = nil
					continue
				end
				if p.cuerpo.Position.Y < Config.CAIDA_Y then
					cuenta.perdidos += 1
					lista[modelo] = nil
					if p.asiento then
						ocupacion[p.asiento] = nil
					end
					Agarre.soltarObjeto(modelo)
					modelo:Destroy()
					RemotoAviso:FireAllClients("😱 ¡Un pasajero ha salido volando del avión!", "peligro")
					continue
				end
				local miedo = modelo:GetAttribute("Miedo")
				local m = if typeof(miedo) == "number" then miedo else 0
				if p.asiento then
					local pedido = modelo:GetAttribute("Pedido")
					if pedido == "" then
						if rng:NextNumber() < P.PEDIDO_PROB * (0.8 + riesgo * 0.2) then
							modelo:SetAttribute("Pedido", Config.COMIDA[rng:NextInteger(1, #Config.COMIDA)])
							modelo:SetAttribute("Paciencia", P.PACIENCIA)
						end
					else
						local paciencia = modelo:GetAttribute("Paciencia")
						local restante = (if typeof(paciencia) == "number" then paciencia else 0) - 1
						modelo:SetAttribute("Paciencia", restante)
						if restante <= 0 then
							modelo:SetAttribute("Pedido", "")
							modelo:SetAttribute("Enfado", os.clock())
							sumar(modelo, "Satisfaccion", -P.BAJADA_ESPERA)
						end
					end
				else
					sumar(modelo, "Satisfaccion", -0.015)
					m = math.min(1, m + 0.04)
				end
				modelo:SetAttribute("Miedo", math.max(0, m - P.MIEDO_DECAE * (if avion:GetAttribute("Mascarillas") == true then 2.5 else 1)))
				if m > 0.6 then
					sumar(modelo, "Satisfaccion", -0.012)
				end
			end
		end
	end)
end

return Pasajeros
