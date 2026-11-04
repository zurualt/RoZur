--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local Contratos = require(ReplicatedStorage.Shared.Contratos)
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
}

local Carga = {}

local avion = Workspace:WaitForChild("Avion") :: Model
local zona = avion:FindFirstChild("ZonaCarga", true) :: BasePart
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
local COLORES_MALETA = { Color3.fromRGB(242, 123, 43), Color3.fromRGB(31, 166, 160), Color3.fromRGB(217, 68, 58) }

local function posicionLibre(): CFrame
	local s = zona.Size
	local p = zona.Position + Vector3.new(rng:NextNumber(-s.X / 2, s.X / 2), rng:NextNumber(0, s.Y / 2), rng:NextNumber(-s.Z / 2, s.Z / 2))
	return CFrame.new(p) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0)
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
	cocodrilo = crearCocodrilo(desde.CFrame * CFrame.new(0, 1.5, 0))
	cuenta.cocodrilo = "Suelto"
	RemotoAviso:FireAllClients("🐊 ¡SE HA ESCAPADO EL COCODRILO! Mételo en su jaula", "peligro")
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
	for _, c in contrato.carga do
		for _ = 1, c.cantidad do
			local parte = Objetos.crear(c.tipo, posicionLibre(), carpeta)
			if c.tipo == "Maleta" then
				parte.Color = COLORES_MALETA[rng:NextInteger(1, #COLORES_MALETA)]
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
		if parte.Parent and not parte.Anchored and not Agarre.portador(parte) then
			table.insert(lista, parte)
		end
	end
	local c = cocodrilo
	if c and c.PrimaryPart and not Agarre.portador(c) then
		table.insert(lista, c.PrimaryPart)
	end
	return lista
end

function Carga.resumen(): (number, number, number, string)
	local intacto = 0
	for _, b in bultos do
		if b.parte.Parent and not b.entrega then
			intacto += b.valor * b.vida / 100
		end
	end
	return math.floor(intacto), cuenta.entregado, cuenta.perdido, cuenta.cocodrilo
end

function Carga.danarJaula(cantidad: number)
	local j = jaula
	if not j or not j.Parent or cocodrilo then
		return
	end
	local b = bultos[j]
	if b then
		b.vida = math.max(0, b.vida - cantidad)
		j:SetAttribute("Vida", math.floor(b.vida))
		if b.vida <= 0 then
			soltarCocodrilo(j)
		end
	end
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
	local j = jaula
	if j and j.Parent and (j.Position - cuerpo.Position).Magnitude < 4.5 and not Agarre.portador(c) then
		local b = bultos[j]
		if b then
			b.vida = 60
			j:SetAttribute("Vida", 60)
		end
		Agarre.soltarObjeto(c)
		c:Destroy()
		cocodrilo = nil
		cuenta.cocodrilo = "Enjaulado"
		RemotoAviso:FireAllClients("🐊 ¡Cocodrilo enjaulado otra vez!", "bien")
		return
	end
	if Agarre.portador(c) then
		return
	end
	local objetivo: BasePart? = nil
	local mejor = 70
	for _, jugador in Players:GetPlayers() do
		local raiz = Personajes.raiz(jugador)
		if raiz then
			local d = (raiz.Position - cuerpo.Position).Magnitude
			if d < mejor then
				objetivo, mejor = raiz, d
			end
			if d < 3.8 and (golpes[jugador] or 0) < os.clock() then
				golpes[jugador] = os.clock() + 2.5
				local dir = (raiz.Position - cuerpo.Position) * Vector3.new(1, 0, 1)
				Personajes.ragdoll(jugador, 1.8, (if dir.Magnitude > 0 then dir.Unit else Vector3.zAxis) * 45 + Vector3.new(0, 25, 0))
				RemotoAviso:FireClient(jugador, "🐊 ¡Te ha mordido el cocodrilo!", "peligro")
			end
		end
	end
	if objetivo then
		local dir = (objetivo.Position - cuerpo.Position) * Vector3.new(1, 0, 1)
		if dir.Magnitude > 0.5 then
			local v = cuerpo.AssemblyLinearVelocity
			local plano = dir.Unit * 11
			cuerpo.AssemblyLinearVelocity = Vector3.new(plano.X, v.Y, plano.Z)
			local giro = CFrame.lookAt(cuerpo.Position, cuerpo.Position + dir)
			cuerpo.AssemblyAngularVelocity = Vector3.zero
			cuerpo.CFrame = cuerpo.CFrame:Lerp(giro, math.min(1, dt * 6))
		end
	end
end

function Carga.iniciar()
	local acumulado = 0
	RunService.Heartbeat:Connect(function(dt)
		acumulado += dt
		if acumulado < 0.1 then
			return
		end
		local paso = acumulado
		acumulado = 0
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
			if cambio > b.umbral and not Agarre.portador(parte) then
				local dano = (cambio - b.umbral) * (if b.umbral < 30 then 2.2 else 1.1)
				b.vida = math.max(0, b.vida - dano)
				parte:SetAttribute("Vida", math.floor(b.vida))
				if parte == jaula and b.vida <= 0 then
					soltarCocodrilo(parte)
				elseif b.vida <= 0 and parte:GetAttribute("Rota") ~= true then
					parte:SetAttribute("Rota", true)
					cuenta.rotas += 1
					parte.Color = parte.Color:Lerp(Color3.new(0.2, 0.2, 0.2), 0.5)
				end
			end
		end
		vigilarCocodrilo(paso)
	end)
end

return Carga
