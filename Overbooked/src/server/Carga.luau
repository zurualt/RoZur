--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")
local Debris = game:GetService("Debris")

local Config = require(ReplicatedStorage.Shared.Config)
local Contratos = require(ReplicatedStorage.Shared.Contratos)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Activos = require(script.Parent.Activos)
local Agarre = require(script.Parent.Agarre)
local Avion = require(script.Parent.Avion)
local Objetos = require(script.Parent.Objetos)
local Pasajeros = require(script.Parent.Pasajeros)
local Personajes = require(script.Parent.Personajes)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent

type Bulto = {
	parte: BasePart,
	valor: number,
	entrega: boolean,
	vida: number,
	umbral: number,
	previa: Vector3,
	gracia: number,
}

local Carga = {}

local avion = Workspace:WaitForChild("Avion") :: Model
local zona = avion:FindFirstChild("ZonaCarga", true) :: BasePart
local carro = Workspace:WaitForChild("Aeropuerto"):FindFirstChild("CarroEquipaje", true) :: BasePart?
local carpeta = Instance.new("Folder")
carpeta.Name = "Carga"
carpeta.Parent = avion
local bultos: { [BasePart]: Bulto } = {}
local cuenta = { entregado = 0, perdido = 0, rotas = 0, cocodrilo = "" }
local cocodrilo: Model? = nil
local jaula: BasePart? = nil
local golpes: { [Player]: number } = {}
local rng = Random.new()

local UMBRALES = { Maleta = 55, Caja = 42, CajaFragil = 24, Jaula = 38 }
local MALETAS = { "Maleta1", "Maleta2", "Maleta3" }
local COLORES_MALETA = { Color3.fromRGB(242, 123, 43), Color3.fromRGB(31, 166, 160), Color3.fromRGB(217, 68, 58) }
local COLUMNAS = { -3.2, 0, 3.2 }
local ORDEN = { Caja = 1, CajaFragil = 2, Maleta = 3 }
local huecos: { Vector3 } = {}
local enEspera = 0
local saciadoHasta = 0
local aturdidoHasta = 0
local ultimoMordisco = 0
local TROZOS = {
	Caja = { nombre = "Astilla", tamano = Vector3.new(0.8, 0.2, 0.3), color = Color3.fromRGB(201, 139, 78), material = Enum.Material.Wood, cantidad = 7 },
	CajaFragil = { nombre = "Esquirla", tamano = Vector3.new(0.5, 0.4, 0.1), color = Color3.fromRGB(143, 211, 244), material = Enum.Material.Glass, cantidad = 8 },
}

local function servidor(parte: BasePart)
	if parte.Anchored or not parte:IsDescendantOf(Workspace) then
		return
	end
	pcall(function()
		if parte:GetNetworkOwnershipAuto() or parte:GetNetworkOwner() ~= nil then
			parte:SetNetworkOwner(nil)
		end
	end)
end

local function prepararHuecos()
	for piso = 0, 2 do
		for fila = 0, 4 do
			local z = zona.Position.Z - zona.Size.Z / 2 + 1.8 + fila * 3.3
			for _, columna in COLUMNAS do
				if not (columna < 0 and z > 10.5) then
					table.insert(huecos, Vector3.new(zona.Position.X + columna, piso * 3.2, z))
				end
			end
		end
	end
end

local function hueco(indice: number, alto: number): CFrame
	local h = huecos[math.clamp(indice, 1, #huecos)]
	return CFrame.new(h.X, Config.SUELO_Y + alto / 2 + 0.1 + h.Y, h.Z)
end

local function crearCocodrilo(cf: CFrame): Model
	local modelo = Instance.new("Model")
	modelo.Name = "Cocodrilo"
	local cuerpo = Instance.new("Part")
	cuerpo.Name = "Cuerpo"
	cuerpo.Size = Vector3.new(1.4, 1.2, 6)
	cuerpo.Color = Color3.fromRGB(107, 191, 89)
	cuerpo.Material = Enum.Material.SmoothPlastic
	cuerpo.CustomPhysicalProperties = PhysicalProperties.new(0.8, 0.3, 0.1)
	cuerpo.CFrame = cf
	cuerpo.Parent = modelo
	local boca = Instance.new("Part")
	boca.Name = "Boca"
	boca.Size = Vector3.new(1.2, 0.6, 1.6)
	boca.Color = Color3.fromRGB(62, 125, 58)
	boca.Material = Enum.Material.SmoothPlastic
	boca.CFrame = cf * CFrame.new(0, -0.1, -3.4)
	boca.Massless = true
	boca.Parent = modelo
	local w = Instance.new("WeldConstraint")
	w.Part0 = cuerpo
	w.Part1 = boca
	w.Parent = cuerpo
	modelo.PrimaryPart = cuerpo
	modelo:SetAttribute("Tipo", "Cocodrilo")
	modelo:SetAttribute("Portador", 0)
	CollectionService:AddTag(modelo, "Agarrable")
	CollectionService:AddTag(modelo, "Cocodrilo")
	modelo.Parent = carpeta
	servidor(cuerpo)
	if Activos.tiene("Cocodrilo") then
		boca.Transparency = 1
		Activos.vestirDinamico(cuerpo, "Cocodrilo")
	end
	return modelo
end

local function soltarCocodrilo(desde: BasePart)
	if cocodrilo then
		return
	end
	local x = math.clamp(desde.Position.X, -5.5, 5.5)
	if math.abs(x) > 4.5 then
		x = math.sign(x) * 5.5
	end
	local z = math.clamp(desde.Position.Z - (desde.Size.Z / 2 + 3.6), -58, 16)
	cocodrilo = crearCocodrilo(CFrame.new(x, Config.SUELO_Y + 0.7, z))
	cuenta.cocodrilo = "Suelto"
	saciadoHasta = 0
	aturdidoHasta = 0
	RemotoAviso:FireAllClients("🐊 ¡SE HA ESCAPADO EL COCODRILO! Atráelo con comida y suéltalo junto a su jaula", "peligro")
	Pasajeros.asustar(0.6)
end

local function registrar(parte: BasePart, tipo: string, valor: number, entrega: boolean)
	parte:SetAttribute("Valor", valor)
	parte:SetAttribute("Entrega", entrega)
	parte:SetAttribute("Vida", 100)
	CollectionService:AddTag(parte, "Carga")
	bultos[parte] = {
		parte = parte,
		valor = valor,
		entrega = entrega,
		vida = 100,
		umbral = UMBRALES[tipo] or 45,
		previa = Vector3.zero,
		gracia = os.clock() + 2,
	}
	if entrega then
		local marca = Instance.new("Highlight")
		marca.FillTransparency = 1
		marca.OutlineColor = Color3.fromRGB(245, 205, 61)
		marca.DepthMode = Enum.HighlightDepthMode.Occluded
		marca.Parent = parte
	end
end

function Carga.cargar(contrato: Contratos.Contrato)
	Carga.limpiar()
	enEspera = 0
	local indice = 0
	local lista = table.clone(contrato.carga)
	table.sort(lista, function(a, b)
		return (ORDEN[a.tipo] or 0) < (ORDEN[b.tipo] or 0)
	end)
	for _, c in lista do
		for _ = 1, c.cantidad do
			local alto = Config.OBJETOS[c.tipo].tamano.Y
			local cf
			local enCarro = carro
			if c.tipo == "Jaula" then
				cf = CFrame.new(-5.15, Config.SUELO_Y + alto / 2 + 0.1, zona.Position.Z + zona.Size.Z / 2 - 3.6)
			elseif c.tipo == "Maleta" and enCarro then
				local k = enEspera
				enEspera += 1
				cf = enCarro.CFrame * CFrame.new(-2.4 + (k % 4) * 1.6, enCarro.Size.Y / 2 + alto / 2 + 0.05 + (k // 8) * 1.3, -1.2 + ((k // 4) % 2) * 2.4)
			else
				indice += 1
				cf = hueco(indice, alto) * CFrame.Angles(0, if c.tipo == "Maleta" then rng:NextNumber(-0.4, 0.4) else 0, 0)
			end
			local variante = if c.tipo == "Maleta" then rng:NextInteger(1, #MALETAS) else 0
			local parte = Objetos.crear(c.tipo, cf, carpeta, if variante > 0 then MALETAS[variante] else nil)
			if variante > 0 then
				parte.Color = COLORES_MALETA[variante]
			end
			if c.tipo == "Jaula" then
				jaula = parte
				cuenta.cocodrilo = "Enjaulado"
				parte.CustomPhysicalProperties = PhysicalProperties.new(2, 0.6, 0.1)
			end
			registrar(parte, c.tipo, c.valor, c.entrega)
		end
	end
end

function Carga.limpiar()
	for parte in bultos do
		Agarre.soltarObjeto(parte)
	end
	local c = cocodrilo
	if c then
		Agarre.soltarObjeto(c)
	end
	carpeta:ClearAllChildren()
	table.clear(bultos)
	cocodrilo = nil
	jaula = nil
	cuenta.entregado = 0
	cuenta.perdido = 0
	cuenta.rotas = 0
	cuenta.cocodrilo = ""
end

function Carga.sueltos(): { BasePart }
	local lista: { BasePart } = {}
	for parte in bultos do
		if parte.Parent and not parte.Anchored and not Agarre.portador(parte) and Agarre.delServidor(parte) then
			table.insert(lista, parte)
		end
	end
	local c = cocodrilo
	if c and c.PrimaryPart and not Agarre.portador(c) and Agarre.delServidor(c.PrimaryPart) then
		table.insert(lista, c.PrimaryPart)
	end
	return lista
end

function Carga.resumen(): (number, number, number, string)
	local intacto = 0
	for _, b in bultos do
		if b.parte.Parent and not b.entrega then
			intacto += b.valor * math.clamp(b.vida, 0, 100) / 100
		end
	end
	return math.floor(intacto), cuenta.entregado, cuenta.perdido, cuenta.cocodrilo
end

local function romper(parte: BasePart, b: Bulto, tipo: string)
	local trozo = TROZOS[tipo]
	bultos[parte] = nil
	cuenta.rotas += 1
	local centro = parte.Position
	local medio = parte.Size / 2
	for _ = 1, trozo.cantidad do
		local t = Instance.new("Part")
		t.Name = trozo.nombre
		t.Size = trozo.tamano
		t.Color = trozo.color
		t.Material = trozo.material
		t.Transparency = if tipo == "CajaFragil" then 0.3 else 0
		t.CanQuery = false
		t.CanTouch = false
		t.CollisionGroup = "Sostenido"
		t.CFrame = CFrame.new(centro + Vector3.new(rng:NextNumber(-medio.X, medio.X), rng:NextNumber(-medio.Y, medio.Y), rng:NextNumber(-medio.Z, medio.Z))) * CFrame.Angles(rng:NextNumber(0, 6.28), rng:NextNumber(0, 6.28), 0)
		t.AssemblyLinearVelocity = parte.AssemblyLinearVelocity * 0.4 + Vector3.new(rng:NextNumber(-12, 12), rng:NextNumber(6, 16), rng:NextNumber(-12, 12))
		t.Parent = carpeta
		servidor(t)
		if Activos.tiene(trozo.nombre) then
			Activos.vestirDinamico(t, trozo.nombre)
		end
		Debris:AddItem(t, rng:NextNumber(6, 9))
	end
	local marca = Instance.new("Part")
	marca.Anchored = true
	marca.CanCollide = false
	marca.CanQuery = false
	marca.CanTouch = false
	marca.Transparency = 1
	marca.Size = Vector3.one
	marca.Position = centro
	marca.Parent = carpeta
	VFX.chispas(marca):Emit(30)
	Debris:AddItem(marca, 1.5)
	Agarre.soltarObjeto(parte)
	parte:Destroy()
	Pasajeros.asustar(0.2, centro, 12)
	RemotoAviso:FireAllClients(if tipo == "CajaFragil" then `💥 ¡Se ha roto una caja frágil! -{b.valor}` else `💥 ¡Se ha roto una caja! -{b.valor}`, "peligro")
end

local function aplicarDano(parte: BasePart, b: Bulto, dano: number)
	b.vida = math.max(0, b.vida - dano)
	parte:SetAttribute("Vida", math.floor(b.vida))
	if b.vida > 0 then
		return
	end
	local tipo = parte:GetAttribute("Tipo")
	if parte == jaula then
		soltarCocodrilo(parte)
	elseif typeof(tipo) == "string" and TROZOS[tipo] then
		romper(parte, b, tipo)
	elseif parte:GetAttribute("Rota") ~= true then
		parte:SetAttribute("Rota", true)
		cuenta.rotas += 1
		parte.Color = parte.Color:Lerp(Color3.new(0.2, 0.2, 0.2), 0.5)
	end
end

function Carga.quemar(posicion: Vector3, radio: number, cantidad: number)
	for parte, b in bultos do
		if parte.Parent and (parte.Position - posicion).Magnitude < radio + parte.Size.Magnitude / 2 then
			aplicarDano(parte, b, cantidad)
		end
	end
end

function Carga.aturdir(segundos: number): boolean
	local c = cocodrilo
	if not c then
		return false
	end
	aturdidoHasta = math.max(aturdidoHasta, os.clock() + segundos)
	return true
end

function Carga.danarJaula(cantidad: number)
	local j = jaula
	if not j or not j.Parent or cocodrilo then
		return
	end
	local b = bultos[j]
	if b then
		b.vida = math.clamp(b.vida - cantidad, 0, 100)
		j:SetAttribute("Vida", math.floor(b.vida))
		if b.vida <= 0 then
			soltarCocodrilo(j)
		end
	end
end

function Carga.dejarEnTierra(): number
	local perdidas = 0
	for parte, b in bultos do
		local p = parte.Position
		local dentro = math.abs(p.X) < 7 and p.Y > 99 and p.Y < 112 and p.Z > -63 and p.Z < 22
		if not dentro then
			bultos[parte] = nil
			perdidas += 1
			cuenta.perdido += b.valor
			if parte == jaula then
				jaula = nil
				cuenta.cocodrilo = "Perdido"
			end
			Agarre.soltarObjeto(parte)
			parte:Destroy()
		end
	end
	local c = cocodrilo
	local cuerpo = c and c.PrimaryPart
	if c and cuerpo then
		local p = cuerpo.Position
		if not (math.abs(p.X) < 7 and p.Y > 99 and p.Y < 112 and p.Z > -63 and p.Z < 22) then
			cuenta.cocodrilo = "Perdido"
			cuenta.perdido += 400
			Agarre.soltarObjeto(c)
			c:Destroy()
			cocodrilo = nil
			perdidas += 1
		end
	end
	if perdidas > 0 then
		RemotoAviso:FireAllClients(`🧳 Se han quedado {perdidas} bultos en tierra`, "peligro")
	end
	return perdidas
end

function Carga.repararJaula(origen: Vector3, alcance: number, cantidad: number): boolean
	local j = jaula
	if not j or not j.Parent or cocodrilo or (j.Position - origen).Magnitude > alcance then
		return false
	end
	local b = bultos[j]
	if not b or b.vida >= 100 then
		return false
	end
	b.vida = math.min(100, b.vida + cantidad)
	j:SetAttribute("Vida", math.floor(b.vida))
	return true
end

local function caida(parte: BasePart, b: Bulto?)
	if b then
		bultos[parte] = nil
		if b.entrega and Avion.zonaEntrega() then
			cuenta.entregado += b.valor
			RemotoAviso:FireAllClients(`📦 ¡Entrega aérea completada! +{b.valor}`, "bien")
		else
			cuenta.perdido += b.valor
			RemotoAviso:FireAllClients(if b.entrega then "📦 Esa entrega no estaba sobre la zona... perdida" else "Se ha caído carga del avión", "peligro")
		end
		if parte == jaula then
			jaula = nil
			cuenta.cocodrilo = "Perdido"
		end
	end
	Agarre.soltarObjeto(parte)
	parte:Destroy()
end

local function enjaular(c: Model)
	local j = jaula
	if j then
		local b = bultos[j]
		if b then
			b.vida = 60
			j:SetAttribute("Vida", 60)
		end
	end
	Agarre.soltarObjeto(c)
	c:Destroy()
	cocodrilo = nil
	cuenta.cocodrilo = "Enjaulado"
	RemotoAviso:FireAllClients("🐊 ¡Cocodrilo enjaulado otra vez!", "bien")
end

local function vigilarCocodrilo(dt: number)
	local c = cocodrilo
	if not c then
		return
	end
	local cuerpo = c.PrimaryPart
	if not c.Parent or not cuerpo then
		cocodrilo = nil
		return
	end
	if cuerpo.Position.Y < Config.CAIDA_Y then
		cuenta.cocodrilo = "Perdido"
		cuenta.perdido += 400
		RemotoAviso:FireAllClients("🐊 El cocodrilo ha salido volando... adiós a la carga", "peligro")
		Agarre.soltarObjeto(c)
		c:Destroy()
		cocodrilo = nil
		return
	end
	local ahora = os.clock()
	local estado = if ahora < aturdidoHasta then "Aturdido" elseif ahora < saciadoHasta then "Saciado" else "Suelto"
	if c:GetAttribute("Estado") ~= estado then
		c:SetAttribute("Estado", estado)
	end
	if Agarre.portador(c) or not Agarre.delServidor(cuerpo) then
		return
	end
	if estado == "Aturdido" then
		local v = cuerpo.AssemblyLinearVelocity
		cuerpo.AssemblyLinearVelocity = Vector3.new(v.X * 0.5, v.Y, v.Z * 0.5)
		return
	end
	local boca = cuerpo.Position + cuerpo.CFrame.LookVector * (cuerpo.Size.Z / 2)
	local objetivo: BasePart? = nil
	local comida: BasePart? = nil
	local velocidad = if estado == "Saciado" then 3.5 else 11
	if estado == "Suelto" then
		local mejor = 34
		for _, o in CollectionService:GetTagged("Objeto") do
			if o:IsA("BasePart") and o.Parent and not Agarre.portador(o) then
				local t = o:GetAttribute("Tipo")
				if (t == "Hamburguesa" or t == "Bandeja") and o.Position.Y - cuerpo.Position.Y < 1.5 then
					local d = (o.Position - boca).Magnitude
					if d < mejor then
						comida, mejor = o, d
					end
				end
			end
		end
		objetivo = comida
		local cebo = math.huge
		local cercano = 70
		for _, jugador in Players:GetPlayers() do
			local raiz = Personajes.raiz(jugador)
			if raiz then
				local d = (raiz.Position - cuerpo.Position).Magnitude
				local tipo = Agarre.tipo(jugador)
				if (tipo == "Hamburguesa" or tipo == "Bandeja") and d < 40 and d < cebo then
					cebo = d
					objetivo, comida = raiz, nil
				elseif cebo == math.huge and not comida and d < cercano then
					objetivo, cercano = raiz, d
				end
				if d < 3.8 and (golpes[jugador] or 0) < ahora then
					golpes[jugador] = ahora + 2.5
					local dir = (raiz.Position - cuerpo.Position) * Vector3.new(1, 0, 1)
					Personajes.ragdoll(jugador, 1.8, (if dir.Magnitude > 0 then dir.Unit else Vector3.zAxis) * 45 + Vector3.new(0, 25, 0))
					RemotoAviso:FireClient(jugador, "🐊 ¡Te ha mordido el cocodrilo!", "peligro")
				end
			end
		end
		local presa = comida
		if presa and (presa.Position - boca).Magnitude < 2.8 then
			Agarre.soltarObjeto(presa)
			presa:Destroy()
			saciadoHasta = ahora + 14
			RemotoAviso:FireAllClients("🐊 ¡El cocodrilo se ha comido la hamburguesa! Ahora está tranquilo: llévalo a la jaula", "bien")
			return
		end
		if ahora > ultimoMordisco then
			local victima = Pasajeros.cercano(boca, 2.6)
			if victima then
				ultimoMordisco = ahora + 3
				local p = victima.PrimaryPart
				Pasajeros.golpear(victima, 75, if p then (p.Position - cuerpo.Position) * Vector3.new(1, 0, 1) else Vector3.yAxis, "Mordisco", false)
			end
		end
	end
	if objetivo then
		local dir = (objetivo.Position - cuerpo.Position) * Vector3.new(1, 0, 1)
		if dir.Magnitude > 0.5 then
			local v = cuerpo.AssemblyLinearVelocity
			local plano = dir.Unit * velocidad
			cuerpo.AssemblyLinearVelocity = Vector3.new(plano.X, v.Y, plano.Z)
			local giro = CFrame.lookAt(cuerpo.Position, cuerpo.Position + dir)
			cuerpo.AssemblyAngularVelocity = Vector3.zero
			cuerpo.CFrame = cuerpo.CFrame:Lerp(giro, math.min(1, dt * 6))
		end
	end
end

function Carga.iniciar()
	prepararHuecos()
	Agarre.permitir(function(jugador, objeto)
		local c = cocodrilo
		if objeto ~= c or not c then
			return true
		end
		local ahora = os.clock()
		if ahora < aturdidoHasta or ahora < saciadoHasta then
			return true
		end
		local raiz = Personajes.raiz(jugador)
		local cuerpo = c.PrimaryPart
		if raiz and cuerpo and (golpes[jugador] or 0) < ahora then
			golpes[jugador] = ahora + 2.5
			local dir = (raiz.Position - cuerpo.Position) * Vector3.new(1, 0, 1)
			Personajes.ragdoll(jugador, 1.6, (if dir.Magnitude > 0 then dir.Unit else Vector3.zAxis) * 40 + Vector3.new(0, 22, 0))
		end
		RemotoAviso:FireClient(jugador, "🐊 ¡Está furioso! Dale de comer o atúrdelo antes de cogerlo", "peligro")
		return false
	end)
	Agarre.alSoltar(function(_, objeto, raiz)
		local b = bultos[raiz]
		if b then
			b.previa = raiz.AssemblyLinearVelocity
			b.gracia = os.clock() + 0.5
		end
		local c = cocodrilo
		local j = jaula
		if c and objeto == c and j and j.Parent and (j.Position - raiz.Position).Magnitude < 6 then
			enjaular(c)
		end
	end)
	Players.PlayerRemoving:Connect(function(jugador)
		golpes[jugador] = nil
	end)
	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		if acumulado < 0.1 then
			return
		end
		local paso = acumulado
		acumulado = 0
		local ahora = os.clock()
		for parte, b in bultos do
			if not parte.Parent then
				bultos[parte] = nil
				continue
			end
			if parte.Position.Y < Config.CAIDA_Y + 15 then
				caida(parte, b)
				continue
			end
			local v = parte.AssemblyLinearVelocity
			local cambio = (v - b.previa).Magnitude
			b.previa = v
			if ahora > b.gracia and cambio > b.umbral and not Agarre.portador(parte) then
				aplicarDano(parte, b, (cambio - b.umbral) * (if b.umbral < 30 then 2.2 else 1.1))
			end
		end
		vigilarCocodrilo(paso)
	end)
end

return Carga
