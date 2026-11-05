--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Activos = require(script.Parent.Activos)
local Agarre = require(script.Parent.Agarre)
local Avion = require(script.Parent.Avion)
local Objetos = require(script.Parent.Objetos)
local Pasajeros = require(script.Parent.Pasajeros)
local Peligros = require(script.Parent.Peligros)
local Personajes = require(script.Parent.Personajes)
local Sonidos = require(script.Parent.Sonidos)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent

type Altillo = {
	puerta: BasePart,
	valor: NumberValue,
	abierto: boolean,
	contenido: number,
	aviso: ProximityPrompt,
	lado: number,
	espera: number,
}

local Cabina = {}

local avion = Workspace:WaitForChild("Avion") :: Model
local altillos: { Altillo } = {}
local asientos: { [Seat]: ProximityPrompt } = {}
local INTERIOR = 6.5
local mascarillas: Folder? = nil
local piezas: { BasePart } = {}
local rng = Random.new()

local function tiempo(): number
	return Workspace:GetServerTimeNow()
end

function Cabina.parpadeo(segundos: number)
	local fin = tiempo() + segundos
	local actual = avion:GetAttribute("Parpadeo")
	if typeof(actual) ~= "number" or actual < fin then
		avion:SetAttribute("Parpadeo", fin)
	end
end

local function moverAltillo(a: Altillo, abierto: boolean)
	if abierto ~= a.abierto then
		Sonidos.emitir("Altillo", a.puerta.Position, 0.1)
	end
	a.abierto = abierto
	a.puerta:SetAttribute("Abierta", abierto)
	a.puerta.CanCollide = not abierto
	a.aviso.ActionText = if abierto then "Cerrar" else "Abrir"
	TweenService:Create(a.valor, TweenInfo.new(if abierto then 0.35 else 0.5, if abierto then Enum.EasingStyle.Back else Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Value = if abierto then 1 else 0 }):Play()
end

local function soltarBolso(a: Altillo)
	if a.contenido <= 0 then
		return
	end
	a.contenido -= 1
	local p = a.puerta.Position
	local bolso = Objetos.crear("Bolso", CFrame.new(p.X - a.lado * 0.9, p.Y - 0.2, p.Z + rng:NextNumber(-1.2, 1.2)) * CFrame.Angles(0, rng:NextNumber(-0.5, 0.5), 0))
	bolso.AssemblyLinearVelocity = Vector3.new(-a.lado * rng:NextNumber(5, 9), rng:NextNumber(1, 4), rng:NextNumber(-3, 3))
	bolso.AssemblyAngularVelocity = Vector3.new(rng:NextNumber(-4, 4), rng:NextNumber(-4, 4), rng:NextNumber(-4, 4))
	Pasajeros.asustar(0.15, p, 6)
end

local function prepararAltillo(puerta: BasePart)
	local cerrada = puerta.CFrame
	local medio = puerta.Size.Y / 2
	local eje = cerrada * CFrame.new(0, medio, 0)
	local function en(angulo: number): CFrame
		return eje * CFrame.Angles(angulo, 0, 0) * CFrame.new(0, -medio, 0)
	end
	local angulo = math.rad(92)
	local signo = if math.abs(en(angulo).Position.X) < math.abs(en(-angulo).Position.X) then 1 else -1
	local valor = Instance.new("NumberValue")
	valor.Changed:Connect(function(v)
		puerta.CFrame = en(v * signo * angulo)
	end)
	local aviso = Instance.new("ProximityPrompt")
	aviso.ActionText = "Abrir"
	aviso.ObjectText = "Altillo"
	aviso.KeyboardKeyCode = Enum.KeyCode.T
	aviso.GamepadKeyCode = Enum.KeyCode.ButtonB
	aviso.MaxActivationDistance = 8
	aviso.RequiresLineOfSight = false
	aviso.Parent = puerta
	local a: Altillo = { puerta = puerta, valor = valor, abierto = false, contenido = 0, aviso = aviso, lado = math.sign(puerta.Position.X), espera = 0 }
	aviso.Triggered:Connect(function()
		local ahora = os.clock()
		if ahora < a.espera then
			return
		end
		a.espera = ahora + 0.6
		moverAltillo(a, not a.abierto)
	end)
	table.insert(altillos, a)
end

local function prepararAsiento(asiento: Seat)
	local aviso = Instance.new("ProximityPrompt")
	aviso.ActionText = "Sentarse"
	aviso.ObjectText = "Asiento"
	aviso.KeyboardKeyCode = Enum.KeyCode.G
	aviso.GamepadKeyCode = Enum.KeyCode.ButtonY
	aviso.MaxActivationDistance = 6
	aviso.RequiresLineOfSight = false
	aviso.Enabled = false
	aviso.Parent = asiento
	asientos[asiento] = aviso
	aviso.Triggered:Connect(function(jugador)
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		local raiz = personaje and personaje:FindFirstChild("HumanoidRootPart")
		if not humanoide or not raiz or not raiz:IsA("BasePart") or humanoide.SeatPart or humanoide.Health <= 0 or Personajes.enRagdoll(jugador) or Pasajeros.ocupado(asiento) then
			return
		end
		if math.abs(avion:GetPivot():PointToObjectSpace(raiz.Position).X) > INTERIOR then
			return
		end
		Agarre.soltar(jugador)
		asiento.Disabled = false
		asiento:Sit(humanoide)
		aviso.Enabled = false
		task.delay(0.5, function()
			if not asiento.Occupant then
				asiento.Disabled = true
			end
		end)
	end)
	asiento:GetPropertyChangedSignal("Occupant"):Connect(function()
		if not asiento.Occupant then
			asiento.Disabled = true
		end
	end)
end

local function desplegarMascarillas()
	if mascarillas then
		return
	end
	local carpeta = Instance.new("Folder")
	carpeta.Name = "Mascarillas"
	carpeta.Parent = avion
	mascarillas = carpeta
	table.clear(piezas)
	local filas: { [number]: boolean } = {}
	for asiento in asientos do
		filas[math.floor(asiento.Position.Z * 10 + 0.5) / 10] = true
	end
	for z in filas do
		for _, sx in { -1, 1 } do
			for _, x in { 3.95, 4.95 } do
				local arriba = Vector3.new(sx * x, 106.75, z - 0.3)
				local ancla = Instance.new("Part")
				ancla.Name = "Ancla"
				ancla.Size = Vector3.new(0.2, 0.2, 0.2)
				ancla.Anchored = true
				ancla.CanCollide = false
				ancla.CanQuery = false
				ancla.CanTouch = false
				ancla.Transparency = 1
				ancla.Position = arriba
				local a0 = Instance.new("Attachment")
				a0.Parent = ancla
				ancla.Parent = carpeta
				local m = Instance.new("Part")
				m.Name = "Mascarilla"
				m.Size = Vector3.new(0.4, 1.4, 0.4)
				m.Color = Color3.fromRGB(245, 205, 61)
				m.Material = Enum.Material.SmoothPlastic
				m.CanCollide = false
				m.CanQuery = false
				m.CanTouch = false
				m.CustomPhysicalProperties = PhysicalProperties.new(0.2, 0.3, 0.1)
				m.CFrame = CFrame.new(arriba - Vector3.new(0, 0.6, 0)) * CFrame.Angles(0, rng:NextNumber(0, 6.28), 0)
				local a1 = Instance.new("Attachment")
				a1.Position = Vector3.new(0, 0.7, 0)
				a1.Parent = m
				local cuerda = Instance.new("RopeConstraint")
				cuerda.Attachment0 = a0
				cuerda.Attachment1 = a1
				cuerda.Length = 0.8
				cuerda.Visible = false
				cuerda.Parent = m
				m.Parent = carpeta
				m.AssemblyLinearVelocity = Vector3.new(rng:NextNumber(-2, 2), -14, rng:NextNumber(-2, 2))
				Objetos.servidor(m)
				if Activos.tiene("Mascarilla") then
					Activos.vestirDinamico(m, "Mascarilla")
				end
				table.insert(piezas, m)
			end
		end
	end
	avion:SetAttribute("Mascarillas", true)
	Cabina.parpadeo(1.2)
	RemotoAviso:FireAllClients("¡Mascarillas de oxígeno desplegadas!", "peligro")
end

function Cabina.reiniciar()
	local m = mascarillas
	if m then
		m:Destroy()
	end
	mascarillas = nil
	table.clear(piezas)
	avion:SetAttribute("Mascarillas", false)
	avion:SetAttribute("Emergencia", false)
	avion:SetAttribute("Parpadeo", 0)
	for _, a in altillos do
		if a.abierto then
			moverAltillo(a, false)
		end
		a.contenido = rng:NextInteger(1, 2)
	end
end

local function sacudida(magnitud: number)
	if magnitud > 0.45 then
		for _, a in altillos do
			if not a.abierto and rng:NextNumber() < magnitud * 0.045 then
				moverAltillo(a, true)
				task.delay(0.15, soltarBolso, a)
			elseif a.abierto and rng:NextNumber() < magnitud * 0.06 then
				soltarBolso(a)
			end
		end
	end
	if magnitud > 0.6 then
		Cabina.parpadeo(0.4 + magnitud)
	end
	for _, m in piezas do
		if m.Parent then
			m.AssemblyLinearVelocity += Vector3.new(rng:NextNumber(-1, 1), rng:NextNumber(0, 0.6), rng:NextNumber(-1, 1)) * magnitud * 9
		end
	end
end

local function guardar(jugador: Player, objeto: Instance, raiz: BasePart)
	if objeto:GetAttribute("Tipo") ~= "Bolso" then
		return
	end
	for _, a in altillos do
		if a.abierto and a.contenido < 3 and (a.puerta.Position - raiz.Position).Magnitude < 4.5 then
			a.contenido += 1
			Sonidos.emitir("Servir", raiz.Position)
			raiz:Destroy()
			RemotoAviso:FireClient(jugador, "Bolso guardado en el altillo", "bien")
			return
		end
	end
end

local function vigilar()
	while true do
		task.wait(0.5)
		local estado = Avion.estado
		local enAire = not estado.enTierra
		local brecha = next(CollectionService:GetTagged("Brecha")) ~= nil
		local motorCaido = estado.motores.Izq.vida <= 0 or estado.motores.Der.vida <= 0
		local emergencia = estado.casco < 30 or brecha or (enAire and motorCaido)
		if avion:GetAttribute("Emergencia") ~= emergencia then
			avion:SetAttribute("Emergencia", emergencia)
		end
		if enAire and not mascarillas and (brecha or avion:GetAttribute("CaidaLibre") == true or estado.casco < 25) then
			desplegarMascarillas()
		end
		for asiento, aviso in asientos do
			local libre = not Pasajeros.ocupado(asiento)
			if aviso.Enabled ~= libre then
				aviso.Enabled = libre
			end
		end
	end
end

function Cabina.iniciar()
	for _, d in avion:GetDescendants() do
		if d:IsA("BasePart") and d.Name == "PuertaAltillo" and d:GetAttribute("Altillo") then
			prepararAltillo(d)
		elseif d:IsA("Seat") and d.Name == "Asiento" then
			prepararAsiento(d)
		end
	end
	Peligros.alSacudir(sacudida)
	Agarre.alSoltar(guardar)
	CollectionService:GetInstanceAddedSignal("Brecha"):Connect(function()
		Cabina.parpadeo(2.5)
	end)
	for _, nombre in { "Pajaros", "Golpe" } do
		avion:GetAttributeChangedSignal(nombre):Connect(function()
			Cabina.parpadeo(1.6)
		end)
	end
	Players.PlayerRemoving:Connect(function(jugador)
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		local asiento = humanoide and humanoide.SeatPart
		if asiento and asiento:IsA("Seat") and asientos[asiento] then
			asiento.Disabled = true
		end
	end)
	Cabina.reiniciar()
	task.spawn(vigilar)
end

return Cabina
