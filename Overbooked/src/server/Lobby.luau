--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Activos = require(script.Parent.Activos)
local Agarre = require(script.Parent.Agarre)
local Objetos = require(script.Parent.Objetos)
local Personajes = require(script.Parent.Personajes)
local Rafagas = require(script.Parent.Rafagas)
local Sonidos = require(script.Parent.Sonidos)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent
local RemotoPulsar = Remotos:WaitForChild("Pulsar") :: RemoteEvent

type Movil = { parte: BasePart, casa: CFrame, fuera: number, quieto: number }
type Bascula = { zona: BasePart, texto: TextLabel, fondo: Frame, peso: number }
type Arco = { zona: BasePart, luz: BasePart }

local Lobby = {}

local aeropuerto = Workspace:WaitForChild("Aeropuerto") :: Model
local terminal = aeropuerto:WaitForChild("Terminal")
local carpeta = Instance.new("Folder")
local rng = Random.new()
local botones: { [BasePart]: (Player, BasePart) -> () } = {}
local esperas: { [Player]: number } = {}
local pasos: { [Player]: number } = {}
local cintas: { [Player]: number } = {}
local maquinas: { [BasePart]: number } = {}
local moviles: { Movil } = {}
local tirados: { BasePart } = {}
local basculas: { Bascula } = {}
local arcos: { Arco } = {}
local salidaCinta: BasePart? = nil
local megafonia = 0
local foto = 0
local patada = 0

local VERDE = Color3.fromRGB(109, 190, 69)
local ROJO = Color3.fromRGB(232, 67, 58)
local OSCURO = Color3.fromRGB(27, 27, 33)
local KG = 14
local LIMITE_KG = 23

local FRASES_MEGAFONIA = {
	"Último aviso para el dueño del cocodrilo: su equipaje le está buscando.",
	"El vuelo a ninguna parte sale puntual. Es broma, nunca sale puntual.",
	"Se ruega a los pilotos que dejen de pulsar todos los botones a la vez.",
	"Recuerde: el chaleco salvavidas está debajo de su asiento. Probablemente.",
	"Objeto perdido en la cinta de equipajes: un pollo de goma. Pregunte en información.",
	"Su puerta de embarque es la del círculo de colores. No, esa no. La otra.",
	"Por su seguridad, no se suban a la cinta de equipajes. Bueno, solo un ratito.",
}

local FRASES_ARCO = {
	"¡PIIIP! ¿Eso es una llave inglesa en el bolsillo?",
	"¡PIIIP! Detectado: un pollo de goma sospechoso.",
	"¡PIIIP! Demasiadas monedas. O demasiado metal en los dientes.",
	"¡PIIIP! Falsa alarma. Creo.",
	"¡PIIIP! Pase, pase. Pero no vuelva a pitar.",
}

local FRASES_INFO = {
	"Información: vuelvo en cinco minutos.",
	"Información: ¿ha probado a apagarlo y encenderlo?",
	"Información: su vuelo sale por la puerta de su vuelo.",
}

local function lista(nombre: string): { BasePart }
	local r = {}
	for _, d in terminal:GetDescendants() do
		if d:IsA("BasePart") and d.Name == nombre then
			table.insert(r, d)
		end
	end
	return r
end

local function etiquetar(parte: BasePart, tipo: string)
	parte:SetAttribute("Tipo", tipo)
	parte:SetAttribute("Portador", 0)
	CollectionService:AddTag(parte, "Agarrable")
	CollectionService:AddTag(parte, "Objeto")
end

local function guardar(parte: BasePart)
	table.insert(tirados, parte)
	local i = 1
	while #tirados > 16 and i <= #tirados do
		local viejo = tirados[i]
		if not viejo.Parent then
			table.remove(tirados, i)
		elseif Agarre.portador(viejo) then
			i += 1
		else
			table.remove(tirados, i)
			viejo:Destroy()
		end
	end
end

local function seguir(parte: BasePart)
	table.insert(moviles, { parte = parte, casa = parte.CFrame, fuera = 0, quieto = 0 })
end

local function reponer(m: Movil)
	local p = m.parte
	p.AssemblyLinearVelocity = Vector3.zero
	p.AssemblyAngularVelocity = Vector3.zero
	p.CFrame = m.casa
	m.fuera, m.quieto = 0, 0
	Objetos.servidor(p)
end

local function dentro(p: Vector3): boolean
	return p.X > 44 and p.X < 120 and p.Z > -78 and p.Z < 30 and p.Y > 85 and p.Y < 130
end

local function mover()
	for _, c in lista("CintaLobby") do
		local v = c:GetAttribute("Velocidad")
		c.AssemblyLinearVelocity = c.CFrame.LookVector * (if typeof(v) == "number" then v else 4)
	end
end

local function boton(parte: BasePart, accion: string, objeto: string, f: (Player, BasePart) -> ())
	parte:SetAttribute("Accion", accion)
	parte:SetAttribute("Objeto", objeto)
	parte:SetAttribute("Duracion", 0)
	CollectionService:AddTag(parte, "BotonMano")
	botones[parte] = f
end

local function aviso(parte: BasePart, accion: string, objeto: string, f: (Player) -> ())
	local p = Instance.new("ProximityPrompt")
	p.ActionText = accion
	p.ObjectText = objeto
	p.KeyboardKeyCode = Enum.KeyCode.E
	p.MaxActivationDistance = 9
	p.RequiresLineOfSight = false
	p.Parent = parte
	p.Triggered:Connect(function(jugador)
		local ahora = os.clock()
		if (esperas[jugador] or 0) > ahora or not Personajes.vivo(jugador) then
			return
		end
		esperas[jugador] = ahora + 0.6
		f(jugador)
	end)
end

local function pulsar(jugador: Player, parte: any)
	if typeof(parte) ~= "Instance" or not parte:IsA("BasePart") then
		return
	end
	local f = botones[parte]
	local raiz = Personajes.raiz(jugador)
	local ahora = os.clock()
	if not f or not raiz or not Personajes.vivo(jugador) or (esperas[jugador] or 0) > ahora then
		return
	end
	if (raiz.Position - parte.Position).Magnitude > 11 then
		return
	end
	esperas[jugador] = ahora + 0.4
	Sonidos.emitir("Boton", parte.Position, 0.1)
	f(jugador, parte)
end

local function lata(cf: CFrame, empuje: Vector3)
	local p = Instance.new("Part")
	p.Name = "Lata"
	p.Size = Vector3.new(0.5, 0.75, 0.5)
	p.Color = ROJO
	p.CustomPhysicalProperties = PhysicalProperties.new(0.6, 0.4, 0.35)
	p.CFrame = cf
	etiquetar(p, "Lata")
	p.Parent = carpeta
	p.AssemblyLinearVelocity = empuje
	Objetos.servidor(p)
	Activos.vestirDinamico(p, "Lata")
	guardar(p)
end

local function expendedora(jugador: Player, parte: BasePart)
	if (maquinas[parte] or 0) > os.clock() then
		return
	end
	maquinas[parte] = os.clock() + 1.2
	local boca = parte:FindFirstChild("Boca")
	local origen = if boca and boca:IsA("BasePart") then boca.Position else parte.Position
	local frente = parte.CFrame.LookVector
	local suerte = rng:NextNumber()
	task.delay(0.5, function()
		if suerte < 0.12 then
			Sonidos.emitir("GolpeMetal", origen)
			Rafagas.lanzar("Bonk", parte.Position, 0.7)
			RemotoAviso:FireClient(jugador, "¡La máquina se ha tragado la moneda!", "peligro")
			return
		end
		local cuantas = if suerte > 0.92 then 3 else 1
		for i = 1, cuantas do
			lata(CFrame.new(origen + Vector3.new(0, 0.1 * i, 0)) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), math.pi / 2),
				frente * rng:NextNumber(5, 8) + Vector3.new(0, 3, 0))
		end
		Sonidos.emitir("GolpeMetal", origen)
		if cuantas > 1 then
			Rafagas.lanzar("Monedas", origen, 0.8)
			RemotoAviso:FireClient(jugador, "¡Premio! Tres latas por el precio de una", "bien")
		end
	end)
end

local function timbre(jugador: Player, parte: BasePart)
	Sonidos.emitir("Ding", parte.Position, 0.3)
	Rafagas.lanzar("Ding", parte.Position + Vector3.new(0, 1, 0), 0.8)
	if rng:NextNumber() < 0.35 then
		RemotoAviso:FireClient(jugador, FRASES_INFO[rng:NextInteger(1, #FRASES_INFO)], "info")
	end
end

local function microfono(_: Player, parte: BasePart)
	local ahora = os.clock()
	if ahora < megafonia then
		return
	end
	megafonia = ahora + 20
	Sonidos.emitir("AvisoMegafonia", nil, 1)
	Rafagas.lanzar("Bocina", parte.Position + Vector3.new(0, 1.5, 0), 0.8)
	local frase = FRASES_MEGAFONIA[rng:NextInteger(1, #FRASES_MEGAFONIA)]
	task.delay(1.6, function()
		RemotoAviso:FireAllClients(frase, "info")
	end)
end

local function pantalla(parte: BasePart): (TextLabel, Frame)
	local gui = Instance.new("SurfaceGui")
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 120
	gui.LightInfluence = 0
	gui.Brightness = 1.4
	gui.MaxDistance = 60
	local fondo = Instance.new("Frame")
	fondo.Size = UDim2.fromScale(1, 1)
	fondo.BackgroundColor3 = OSCURO
	fondo.BorderSizePixel = 0
	fondo.Parent = gui
	local t = Instance.new("TextLabel")
	t.Size = UDim2.fromScale(0.9, 0.8)
	t.Position = UDim2.fromScale(0.05, 0.1)
	t.BackgroundTransparency = 1
	t.Font = Enum.Font.FredokaOne
	t.TextScaled = true
	t.TextColor3 = VERDE
	t.Text = string.format("%.1f kg", 0)
	t.Parent = fondo
	gui.Parent = parte
	return t, fondo
end

local function pesar()
	for _, b in basculas do
		local zona = b.zona
		local cf = zona.CFrame * CFrame.new(0, zona.Size.Y / 2 + 2.6, 0)
		local vistos: { [BasePart]: boolean } = {}
		local masa = 0
		local jugador: Player? = nil
		for _, p in Workspace:GetPartBoundsInBox(cf, Vector3.new(zona.Size.X, 5, zona.Size.Z)) do
			local raiz = p.AssemblyRootPart
			if raiz and not raiz.Anchored and not vistos[raiz] then
				vistos[raiz] = true
				masa += raiz.AssemblyMass
				local modelo = raiz:FindFirstAncestorOfClass("Model")
				jugador = jugador or (modelo and Players:GetPlayerFromCharacter(modelo))
			end
		end
		local peso = if masa > 0 then masa * KG + rng:NextNumber(-0.3, 0.3) else 0
		b.texto.Text = string.format("%.1f kg", peso)
		local exceso = peso > LIMITE_KG
		b.texto.TextColor3 = if exceso then Color3.new(1, 1, 1) else VERDE
		b.fondo.BackgroundColor3 = if exceso then ROJO else OSCURO
		if b.peso == 0 and peso > 0 then
			Sonidos.emitir("Ding", zona.Position, 0.2)
			if exceso then
				Rafagas.lanzar("Bocina", zona.Position + Vector3.new(0, 3, 0), 0.7)
				if jugador then
					RemotoAviso:FireClient(jugador, "¡Exceso de equipaje! Pagará la diferencia en abrazos", "peligro")
				end
			end
		end
		b.peso = peso
	end
end

local function facturar()
	local salida = salidaCinta
	if not salida then
		return
	end
	for _, zona in lista("Trampilla") do
		for _, p in Workspace:GetPartBoundsInBox(zona.CFrame, zona.Size) do
			local modelo = p:FindFirstAncestorOfClass("Model")
			local jugador = modelo and Players:GetPlayerFromCharacter(modelo)
			local ahora = os.clock()
			if jugador and modelo and p.Name == "HumanoidRootPart" then
				if (cintas[jugador] or 0) < ahora then
					cintas[jugador] = ahora + 3
					Sonidos.emitir("Pop", zona.Position)
					modelo:PivotTo(CFrame.new(salida.Position + Vector3.new(0, 1.5, 0)) * CFrame.Angles(0, math.pi / 2, 0))
					Rafagas.lanzar("Estrellas", salida.Position, 1)
					Sonidos.emitir("Pop", salida.Position)
					RemotoAviso:FireClient(jugador, "¡Te has facturado a ti mismo! Recógete en la cinta de equipajes", "info")
				end
			elseif CollectionService:HasTag(p, "Objeto") and not p.Anchored and not Agarre.portador(p) then
				p.AssemblyLinearVelocity = Vector3.zero
				p.CFrame = CFrame.new(salida.Position + Vector3.new(0, 0, rng:NextNumber(-0.6, 0.6)))
				Objetos.servidor(p)
				Sonidos.emitir("Pop", salida.Position)
			end
		end
	end
end

local function arcosSeguridad()
	local ahora = os.clock()
	for _, a in arcos do
		for _, p in Workspace:GetPartBoundsInBox(a.zona.CFrame, a.zona.Size) do
			local modelo = p:FindFirstAncestorOfClass("Model")
			local jugador = modelo and Players:GetPlayerFromCharacter(modelo)
			if not jugador or p.Name ~= "HumanoidRootPart" then
				continue
			end
			if (pasos[jugador] or 0) > ahora then
				continue
			end
			pasos[jugador] = ahora + 2.5
			local pita = Agarre.sostenido(jugador) ~= nil or rng:NextNumber() < 0.4
			local luz = a.luz:FindFirstChildOfClass("PointLight")
			a.luz.Color = if pita then ROJO else VERDE
			if luz then
				luz.Color = a.luz.Color
				luz.Brightness = if pita then 4 else 2
			end
			if pita then
				Sonidos.emitir("UiPeligro", a.luz.Position, 0.3)
				Rafagas.lanzar("Pitido", a.luz.Position + Vector3.new(0, 1, 0), 1)
				RemotoAviso:FireClient(jugador, FRASES_ARCO[rng:NextInteger(1, #FRASES_ARCO)], "peligro")
			else
				Sonidos.emitir("Ding", a.luz.Position, 0.3)
			end
			task.delay(1.4, function()
				a.luz.Color = VERDE
				if luz then
					luz.Brightness = 0
				end
			end)
		end
	end
end

local function fotomaton(jugador: Player, cabina: BasePart)
	local ahora = os.clock()
	if ahora < foto then
		return
	end
	foto = ahora + 5
	local flash = terminal:FindFirstChild("FlashFoto", true)
	local salida = terminal:FindFirstChild("SalidaFoto", true)
	task.spawn(function()
		for _ = 1, 3 do
			task.wait(0.55)
			if flash and flash:IsA("BasePart") then
				local luz = flash:FindFirstChildOfClass("PointLight")
				flash.Transparency = 0
				if luz then
					luz.Brightness = 8
				end
				Sonidos.emitir("UiClick", flash.Position, 0.05)
				task.wait(0.12)
				flash.Transparency = 1
				if luz then
					luz.Brightness = 0
				end
			end
		end
		Rafagas.lanzar("Estrellas", cabina.Position + Vector3.new(0, 4, 0), 1)
		task.wait(0.8)
		if not salida or not salida:IsA("BasePart") then
			return
		end
		local p = Instance.new("Part")
		p.Name = "Foto"
		p.Size = Vector3.new(1.3, 1.7, 0.08)
		p.Color = Color3.fromRGB(242, 239, 230)
		p.CustomPhysicalProperties = PhysicalProperties.new(0.3, 0.6, 0.1)
		p.CFrame = CFrame.lookAt(salida.Position, salida.Position + Vector3.new(1, 0, 0))
		etiquetar(p, "Foto")
		for _, cara in { Enum.NormalId.Front, Enum.NormalId.Back } do
			local gui = Instance.new("SurfaceGui")
			gui.Face = cara
			gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
			gui.PixelsPerStud = 100
			local imagen = Instance.new("ImageLabel")
			imagen.Size = UDim2.fromScale(0.84, 0.66)
			imagen.Position = UDim2.fromScale(0.08, 0.06)
			imagen.BackgroundColor3 = Color3.fromRGB(143, 211, 244)
			imagen.BorderSizePixel = 0
			imagen.Image = `rbxthumb://type=AvatarHeadShot&id={jugador.UserId}&w=150&h=150`
			imagen.Parent = gui
			for k, color in { Color3.fromRGB(242, 123, 43), Color3.fromRGB(31, 166, 160), Color3.fromRGB(246, 196, 69) } do
				local punto = Instance.new("Frame")
				punto.Size = UDim2.fromScale(0.12, 0.09)
				punto.Position = UDim2.fromScale(0.08 + 0.16 * (k - 1), 0.8)
				punto.BackgroundColor3 = color
				punto.BorderSizePixel = 0
				Instance.new("UICorner").Parent = punto
				punto.Parent = gui
			end
			gui.Parent = p
		end
		p.Parent = carpeta
		p.AssemblyLinearVelocity = Vector3.new(5, 3, 0)
		Objetos.servidor(p)
		Sonidos.emitir("RasgarPapel", salida.Position)
		guardar(p)
	end)
end

local function cafe(jugador: Player, punto: BasePart)
	if Agarre.sostenido(jugador) then
		return
	end
	Sonidos.emitir("Servir", punto.Position)
	local c = Objetos.crear("Cafe", punto.CFrame + Vector3.new(0, 0.6, 0), carpeta)
	guardar(c)
	Agarre.forzar(jugador, c)
end

local function vigilar()
	for _, m in moviles do
		local p = m.parte
		if not p.Parent or Agarre.portador(p) then
			continue
		end
		if dentro(p.Position) then
			m.fuera = 0
		else
			m.fuera += 1
		end
		if p.AssemblyLinearVelocity.Magnitude < 0.5 and (p.Position - m.casa.Position).Magnitude > 4 then
			m.quieto += 1
		else
			m.quieto = 0
		end
		if m.fuera > 12 or m.quieto > 90 or p.Position.Y < 80 then
			reponer(m)
		end
	end
end

local function patear(pelota: BasePart)
	pelota.Touched:Connect(function(otra)
		local modelo = otra:FindFirstAncestorOfClass("Model")
		local jugador = modelo and Players:GetPlayerFromCharacter(modelo)
		local ahora = os.clock()
		if not jugador or ahora < patada or Agarre.portador(pelota) then
			return
		end
		local raiz = Personajes.raiz(jugador)
		if not raiz then
			return
		end
		local d = (pelota.Position - raiz.Position) * Vector3.new(1, 0, 1)
		if d.Magnitude < 0.1 then
			return
		end
		patada = ahora + 0.35
		Objetos.servidor(pelota)
		pelota.AssemblyLinearVelocity = d.Unit * 30 + Vector3.new(0, 18, 0) + raiz.AssemblyLinearVelocity * Vector3.new(0.5, 0, 0.5)
		Sonidos.emitir("Golpe", pelota.Position, 0.2)
	end)
end

local function preparar()
	carpeta.Name = "ObjetosLobby"
	carpeta.Parent = terminal
	for _, c in lista("CarroMaletas") do
		c.CustomPhysicalProperties = PhysicalProperties.new(0.3, 0.12, 0.1, 1, 1)
		etiquetar(c, "CarroMaletas")
		seguir(c)
	end
	for _, b in lista("Pelota") do
		b.CustomPhysicalProperties = PhysicalProperties.new(0.15, 0.4, 0.7, 1, 1)
		etiquetar(b, "Pelota")
		seguir(b)
		patear(b)
	end
	for _, punto in lista("PuntoMaleta") do
		local m = Objetos.crear("Maleta", CFrame.new(punto.Position) * CFrame.Angles(0, rng:NextNumber(0, math.pi * 2), 0), carpeta,
			`Maleta{rng:NextInteger(1, 3)}`)
		seguir(m)
	end
	for _, zona in lista("Bascula") do
		for _, p in lista("PantallaBascula") do
			if p:GetAttribute("Mostrador") == zona:GetAttribute("Mostrador") then
				local texto, fondo = pantalla(p)
				table.insert(basculas, { zona = zona, texto = texto, fondo = fondo, peso = 0 })
			end
		end
	end
	local luces = lista("LuzArco")
	for _, zona in lista("Detector") do
		local mejor: BasePart? = nil
		for _, l in luces do
			if not mejor or (l.Position - zona.Position).Magnitude < (mejor.Position - zona.Position).Magnitude then
				mejor = l
			end
		end
		if mejor then
			table.insert(arcos, { zona = zona, luz = mejor })
		end
	end
	local salida = terminal:FindFirstChild("SalidaCinta", true)
	salidaCinta = if salida and salida:IsA("BasePart") then salida else nil
	for _, p in lista("Timbre") do
		boton(p, "Tocar el timbre", "Información", timbre)
	end
	for _, p in lista("Microfono") do
		boton(p, "Hablar por megafonía", "Micrófono", microfono)
	end
	for _, p in lista("BotonExpendedora") do
		boton(p, "Pulsar", "Máquina de refrescos", expendedora)
	end
	for _, p in lista("PuntoCafe") do
		aviso(p, "Pedir un café", "Cafetería", function(jugador)
			cafe(jugador, p)
		end)
	end
	for _, p in lista("Fotomaton") do
		aviso(p, "Hacerse una foto", "Fotomatón", function(jugador)
			fotomaton(jugador, p)
		end)
	end
end

function Lobby.iniciar()
	preparar()
	mover()
	RemotoPulsar.OnServerEvent:Connect(pulsar)
	aeropuerto.AncestryChanged:Connect(function()
		if aeropuerto:IsDescendantOf(Workspace) then
			task.defer(function()
				mover()
				for _, m in moviles do
					reponer(m)
				end
			end)
		end
	end)
	Players.PlayerRemoving:Connect(function(jugador)
		esperas[jugador] = nil
		pasos[jugador] = nil
		cintas[jugador] = nil
	end)
	task.spawn(function()
		local tick = 0
		while true do
			task.wait(0.2)
			if not aeropuerto:IsDescendantOf(Workspace) then
				continue
			end
			tick += 1
			arcosSeguridad()
			facturar()
			if tick % 2 == 0 then
				pesar()
			end
			if tick % 5 == 0 then
				vigilar()
			end
		end
	end)
end

return Lobby
