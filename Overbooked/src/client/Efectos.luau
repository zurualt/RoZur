--!strict
local CollectionService = game:GetService("CollectionService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Gui = require(ReplicatedStorage.Shared.Gui)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Camara = require(script.Parent.Camara)
local Pajaros = require(script.Parent.Pajaros)
local Rafagas = require(script.Parent.Rafagas)
local Sonido = require(script.Parent.Sonido)

type Estela = { rastro: Trail, hasta: number }

local Efectos = {}

local jugador = Players.LocalPlayer
local avion = Workspace:WaitForChild("Avion") :: Model
local rng = Random.new()
local capa: ScreenGui
local destello: Frame
local atmosfera = Lighting:FindFirstChildOfClass("Atmosphere")
local base = {
	reloj = Lighting.ClockTime,
	brillo = Lighting.Brightness,
	densidad = if atmosfera then atmosfera.Density else 0.3,
}
local tormenta = false
local Estado = game:GetService("ReplicatedStorage"):WaitForChild("Estado")
local proximoRayo = 0
local zoom = 1
local zoomObjetivo = 1
local zoomHasta = 0
local ultimoDrama = -100
local congeladoEnVuelo = false
local fotoFija = 0
local pieFoto: Instance? = nil
local correccion = Instance.new("ColorCorrectionEffect")
local cayendo: { [BasePart]: boolean } = setmetatable({}, { __mode = "k" }) :: any
local estelas: { [BasePart]: Estela } = {}
local acumulado = 0
local selloHasta = 0

local AMARILLO = Color3.fromRGB(255, 214, 70)
local AGUA = Color3.fromRGB(143, 211, 244)
local BLANCO = Color3.new(1, 1, 1)
local FRASES_CHOQUE = { "ATERRIZAJE CREATIVO", "¿QUIÉN TE DIO EL CARNÉ?", "SUSPENSO EN PILOTAJE", "EL SUELO GANA", "ESO NO ERA LA PISTA", "CERO ESTRELLAS" }
local FRASES_PERFECTO = { "¡MANTEQUILLA!", "¡DE LIBRO!", "¡NI SE HA NOTADO!" }
local FRASES_DURO = { "¿ESO ERA ATERRIZAR?", "¡MIS RIÑONES!" }
local DESPEDIDAS = { "¡ADIÓOOS!", "¡HASTA LUEGO!", "¡AAAAH!" }
local EN_VUELO: { [string]: boolean } = { Despegue = true, Vuelo = true, Aproximacion = true }

local function elegir(lista: { string }): string
	return lista[rng:NextInteger(1, #lista)]
end

local function animar(i: Instance, t: number, props: { [string]: any }, estilo: Enum.EasingStyle?, direccion: Enum.EasingDirection?)
	TweenService:Create(i, TweenInfo.new(t, estilo or Enum.EasingStyle.Quad, direccion or Enum.EasingDirection.Out), props):Play()
end

local function numero(nombre: string): number
	local v = avion:GetAttribute(nombre)
	return if typeof(v) == "number" then v else 0
end

local function pantalla()
	capa = Instance.new("ScreenGui")
	capa.Name = "OverbookedEfectos"
	capa.IgnoreGuiInset = true
	capa.ResetOnSpawn = false
	capa.DisplayOrder = 50
	destello = Instance.new("Frame")
	destello.Size = UDim2.fromScale(1, 1)
	destello.BackgroundColor3 = Color3.new(1, 1, 1)
	destello.BackgroundTransparency = 1
	destello.BorderSizePixel = 0
	destello.Parent = capa
	capa.Parent = jugador:WaitForChild("PlayerGui")
	correccion.Name = "OverbookedCongelar"
	correccion.Parent = Lighting
end

local function destellar(color: Color3, fuerza: number, duracion: number)
	destello.BackgroundColor3 = color
	destello.BackgroundTransparency = 1 - fuerza
	TweenService:Create(destello, TweenInfo.new(duracion), { BackgroundTransparency = 1 }):Play()
end

local function acercar(factor: number, duracion: number)
	zoomObjetivo = factor
	zoomHasta = os.clock() + duracion
end

local function drama()
	if os.clock() - ultimoDrama < 30 then
		return
	end
	ultimoDrama = os.clock()
	Sonido.reproducir("Dramatico", nil, 1, 1)
	acercar(0.62, 1.3)
end

local function sellar(texto: string, subtitulo: string, color: Color3)
	selloHasta = os.clock() + 3.6
	local marco = Instance.new("Frame")
	marco.BackgroundTransparency = 1
	marco.AnchorPoint = Vector2.new(0.5, 0.5)
	marco.Position = UDim2.fromScale(0.5, 0.4)
	marco.Size = UDim2.fromScale(0.62, 0.31)
	marco.Rotation = rng:NextNumber(6, 11) * (if rng:NextNumber() < 0.5 then -1 else 1)
	local proporcion = Instance.new("UIAspectRatioConstraint")
	proporcion.AspectRatio = 2
	proporcion.Parent = marco
	local limite = Instance.new("UISizeConstraint")
	limite.MaxSize = Vector2.new(620, 310)
	limite.Parent = marco
	local escala = Instance.new("UIScale")
	escala.Scale = 3
	escala.Parent = marco
	local tampon = Instance.new("ImageLabel")
	tampon.BackgroundTransparency = 1
	tampon.Size = UDim2.fromScale(1, 1)
	tampon.Image = VFX.textura("Tampon")
	tampon.ImageColor3 = color
	tampon.ImageTransparency = 1
	tampon.Parent = marco
	local titulo = Gui.texto(marco, texto, UDim2.fromScale(0.8, 0.44), UDim2.fromScale(0.5, 0.44), color, true)
	titulo.AnchorPoint = Vector2.new(0.5, 0.5)
	titulo.TextTransparency = 1
	local sub = Gui.texto(marco, subtitulo, UDim2.fromScale(0.76, 0.17), UDim2.fromScale(0.5, 0.76), color, false)
	sub.AnchorPoint = Vector2.new(0.5, 0.5)
	sub.TextTransparency = 1
	marco.Parent = capa
	animar(escala, 0.16, { Scale = 0.94 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	animar(tampon, 0.12, { ImageTransparency = 0.05 })
	animar(titulo, 0.12, { TextTransparency = 0.05 })
	animar(sub, 0.12, { TextTransparency = 0.05 })
	task.delay(0.16, function()
		Sonido.reproducir("Sello", nil, 1, 1)
		Camara.sacudir(0.4)
		animar(escala, 0.35, { Scale = 1 }, Enum.EasingStyle.Back)
	end)
	task.delay(3, function()
		animar(tampon, 0.5, { ImageTransparency = 1 })
		animar(titulo, 0.5, { TextTransparency = 1 })
		animar(sub, 0.5, { TextTransparency = 1 })
		task.wait(0.55)
		marco:Destroy()
	end)
end

local function soltarFoto(marca: number?)
	if marca and marca ~= fotoFija then
		return
	end
	fotoFija = 0
	animar(correccion, 0.2, { Saturation = 0, Contrast = 0, Brightness = 0, TintColor = BLANCO })
	if pieFoto then
		pieFoto:Destroy()
		pieFoto = nil
	end
end

local function congelar()
	congeladoEnVuelo = true
	local marca = os.clock()
	Sonido.reproducir("RascarDisco", nil, 1, 1)
	animar(correccion, 0.06, { Saturation = -0.9, Contrast = 0.2, Brightness = 0.04, TintColor = Color3.fromRGB(255, 232, 196) })
	acercar(0.8, 1.5)
	Camara.sacudir(0.2)
	local pie = Gui.panel(capa, "Papel", UDim2.fromScale(0.56, 0.2), UDim2.fromScale(0.5, 0.9), Vector2.new(0.5, 1))
	local limite = Instance.new("UISizeConstraint")
	limite.MaxSize = Vector2.new(640, 170)
	limite.Parent = pie
	local cabecera = Gui.texto(pie, "PAUSA DRAMÁTICA", UDim2.fromScale(0.8, 0.26), UDim2.fromScale(0.5, 0.2), Gui.ROJO, true)
	cabecera.AnchorPoint = Vector2.new(0.5, 0.5)
	local cuerpo = Gui.texto(pie, "Sí, esos somos nosotros. ¿Que cómo hemos llegado hasta aquí? Larga historia…", UDim2.fromScale(0.84, 0.5), UDim2.fromScale(0.5, 0.62), Gui.TINTA, false)
	cuerpo.AnchorPoint = Vector2.new(0.5, 0.5)
	local escala = Instance.new("UIScale")
	escala.Scale = 0
	escala.Parent = pie
	animar(escala, 0.3, { Scale = 1 }, Enum.EasingStyle.Back)
	pieFoto = pie
	fotoFija = marca
	task.delay(4.2, soltarFoto, marca)
end

local function mareo(cabeza: BasePart, duracion: number, seguir: (() -> boolean)?)
	if cabeza:FindFirstChild("Mareo") then
		return
	end
	local gui = Instance.new("BillboardGui")
	gui.Name = "Mareo"
	gui.Size = UDim2.fromScale(3, 1.4)
	gui.StudsOffsetWorldSpace = Vector3.new(0, 1.4, 0)
	gui.LightInfluence = 0
	gui.MaxDistance = 90
	local estrellas: { ImageLabel } = {}
	for k = 1, 3 do
		local e = Instance.new("ImageLabel")
		e.BackgroundTransparency = 1
		e.AnchorPoint = Vector2.new(0.5, 0.5)
		e.Image = VFX.textura("Estrella")
		e.ScaleType = Enum.ScaleType.Fit
		e.Parent = gui
		table.insert(estrellas, e)
	end
	gui.Parent = cabeza
	local inicio = os.clock()
	local conexion: RBXScriptConnection
	conexion = RunService.RenderStepped:Connect(function()
		local t = os.clock() - inicio
		if t > duracion or not gui.Parent or (seguir and t > 0.5 and not seguir()) then
			conexion:Disconnect()
			gui:Destroy()
			return
		end
		for k, e in estrellas do
			local a = t * 5 + k * 2.094
			local fondo = (math.sin(a) + 1) / 2
			local tam = 0.18 + 0.12 * fondo
			e.Position = UDim2.fromScale(0.5 + math.cos(a) * 0.36, 0.5 + math.sin(a) * 0.2)
			e.Size = UDim2.fromScale(tam, tam * 2.1)
			e.ZIndex = if fondo > 0.5 then 2 else 1
			e.Rotation = t * 220
		end
	end)
end

local function pasajero(modelo: Instance)
	if not modelo:IsA("Model") then
		return
	end
	local cabeza = modelo:WaitForChild("Cabeza", 5)
	if not cabeza or not cabeza:IsA("BasePart") then
		return
	end
	local ultimo = 0
	local function emocion(imagen: string, tinte: Color3?, rafaga: string?, textos: { string }?, fondo: Color3?)
		local ahora = os.clock()
		if ahora - ultimo < 0.8 or (Workspace.CurrentCamera.CFrame.Position - cabeza.Position).Magnitude > 90 then
			return
		end
		ultimo = ahora
		Sonido.reproducir("Pop", cabeza, 0.8)
		Rafagas.pop(cabeza, Vector3.new(0, 1.9, 0), { imagen = imagen, tinte = tinte, tam = 1.6, vida = 1.3, subir = 0.8, girar = rng:NextNumber(-20, 20) })
		if rafaga then
			Rafagas.lanzar(rafaga, cabeza.Position + Vector3.new(0, 1, 0), 0.6)
		end
		if textos and fondo and rng:NextNumber() < 0.45 then
			Rafagas.palabra(cabeza.Position + Vector3.new(0, 1.6, 0), elegir(textos), AMARILLO, fondo, 0.75, true)
		end
	end
	local conexiones = {
		modelo:GetAttributeChangedSignal("Feliz"):Connect(function()
			emocion("Corazon", nil, "Corazones", { "¡ÑAM!", "¡RICO!", "¡GRACIAS!" }, Gui.VERDE)
		end),
		modelo:GetAttributeChangedSignal("Enfado"):Connect(function()
			emocion("Vena", nil, "Enfado", { "¡GRRR!", "¡HMPF!", "¡QUÉ SERVICIO!" }, Gui.ROJO)
		end),
		modelo:GetAttributeChangedSignal("ReaccionMarca"):Connect(function()
			local r = modelo:GetAttribute("Reaccion")
			if r == "Mojado" then
				emocion("Gota", AGUA, "Sudor")
			elseif r == "Golpe" then
				emocion("Espiral", AMARILLO)
				mareo(cabeza, 2.2)
			elseif r == "Quemado" or r == "Mordisco" then
				emocion("Exclamacion", Gui.ROJO, "Enfado")
			else
				emocion("Interrogacion", AMARILLO, "Sudor")
			end
		end),
		modelo:GetAttributeChangedSignal("Alborotador"):Connect(function()
			if modelo:GetAttribute("Alborotador") == true then
				Rafagas.palabra(cabeza.Position + Vector3.new(0, 1.6, 0), "¡ME QUIERO BAJAR!", AMARILLO, Gui.ROJO, 0.9)
			end
		end),
	}
	modelo.Destroying:Once(function()
		for _, c in conexiones do
			c:Disconnect()
		end
	end)
end

local function cocodrilo(modelo: Instance)
	local c = modelo:GetAttributeChangedSignal("Estado"):Connect(function()
		if modelo:GetAttribute("Estado") == "Suelto" then
			drama()
		end
	end)
	modelo.Destroying:Once(function()
		c:Disconnect()
	end)
end

local function personaje(p: Model)
	p:GetAttributeChangedSignal("Ragdoll"):Connect(function()
		local cabeza = p:FindFirstChild("Head")
		if p:GetAttribute("Ragdoll") == true and cabeza and cabeza:IsA("BasePart") then
			Sonido.reproducir("Mareo", cabeza, 0.8)
			mareo(cabeza, 6, function()
				return p:GetAttribute("Ragdoll") == true
			end)
		end
	end)
end

local function vaporCafe(o: Instance)
	if not o:IsA("BasePart") or o:GetAttribute("Tipo") ~= "Cafe" or o:FindFirstChild("VaporCafe") then
		return
	end
	local e = Instance.new("ParticleEmitter")
	e.Name = "VaporCafe"
	e.Texture = VFX.textura("Vapor")
	e.Color = ColorSequence.new(Color3.fromRGB(240, 242, 246))
	e.Size = NumberSequence.new(0.25, 0.9)
	e.Transparency = NumberSequence.new(0.2, 1)
	e.Lifetime = NumberRange.new(1.1, 1.6)
	e.Rate = 2.5
	e.Speed = NumberRange.new(1.2, 2.2)
	e.SpreadAngle = Vector2.new(12, 12)
	e.RotSpeed = NumberRange.new(-30, 30)
	e.Rotation = NumberRange.new(-20, 20)
	e.Acceleration = Vector3.new(0, 1, 0)
	e.EmissionDirection = Enum.NormalId.Top
	e.Parent = o
end

local function cuerpoDe(o: Instance): BasePart?
	if o:IsA("BasePart") then
		return o
	end
	if o:IsA("Model") then
		local c = o:FindFirstChild("Cuerpo")
		return if c and c:IsA("BasePart") then c else o.PrimaryPart
	end
	return nil
end

local function estela(p: BasePart): Estela
	local a0 = Instance.new("Attachment")
	a0.Name = "EstelaA"
	a0.Position = Vector3.new(0, 0.55, 0)
	a0.Parent = p
	local a1 = Instance.new("Attachment")
	a1.Name = "EstelaB"
	a1.Position = Vector3.new(0, -0.55, 0)
	a1.Parent = p
	local t = Instance.new("Trail")
	t.Attachment0 = a0
	t.Attachment1 = a1
	t.Texture = VFX.textura("Rayas")
	t.TextureMode = Enum.TextureMode.Stretch
	t.FaceCamera = true
	t.Lifetime = 0.22
	t.MinLength = 0.05
	t.LightEmission = 0
	t.Color = ColorSequence.new(BLANCO)
	t.Transparency = NumberSequence.new(0.1, 1)
	t.WidthScale = NumberSequence.new(1, 0.4)
	t.Parent = p
	return { rastro = t, hasta = 0 }
end

local function quitarEstela(p: BasePart, e: Estela)
	estelas[p] = nil
	e.rastro.Enabled = false
	task.delay(0.3, function()
		e.rastro:Destroy()
		for _, n in { "EstelaA", "EstelaB" } do
			local a = p:FindFirstChild(n)
			if a then
				a:Destroy()
			end
		end
	end)
end

local function revisarCaida(p: BasePart, propio: boolean)
	if p.Position.Y < 94 and p.AssemblyLinearVelocity.Y < -10 then
		if not cayendo[p] then
			cayendo[p] = true
			Sonido.reproducir("SilbatoCaida", if propio then nil else p, 1, 1)
			Rafagas.pop(p, Vector3.new(0, 3, 0), { texto = elegir(DESPEDIDAS), color = AMARILLO, fondo = BLANCO, nube = true, tam = 2, vida = 1.6, subir = 1.5 })
		end
	elseif p.Position.Y > 97 then
		cayendo[p] = nil
	end
end

local function vigilar()
	local ahora = os.clock()
	local fase = avion:GetAttribute("Fase")
	if fase == "Aeropuerto" or fase == "Despegue" then
		congeladoEnVuelo = false
	end
	local volando = EN_VUELO[fase :: string] == true and avion:GetAttribute("EnTierra") == false
	if volando and not congeladoEnVuelo and fase ~= "Despegue" then
		local alt, ver = numero("Altitud"), numero("Vertical")
		if ver < -20 and alt > 0 and alt / -ver < 2.4 then
			congelar()
		end
	end
	if volando then
		for _, otro in Players:GetPlayers() do
			local raiz = otro.Character and otro.Character:FindFirstChild("HumanoidRootPart")
			if raiz and raiz:IsA("BasePart") then
				revisarCaida(raiz, otro == jugador)
			end
		end
		for _, m in CollectionService:GetTagged("Pasajero") do
			local c = cuerpoDe(m)
			if c then
				revisarCaida(c, false)
			end
		end
	end
	local foco = Workspace.CurrentCamera.CFrame.Position
	local cuenta = 0
	for _ in estelas do
		cuenta += 1
	end
	for _, o in CollectionService:GetTagged("Agarrable") do
		local p = cuerpoDe(o)
		if p and p.AssemblyLinearVelocity.Magnitude > 34 and (p.Position - foco).Magnitude < 120 then
			local e = estelas[p]
			if not e and cuenta < 8 then
				e = estela(p)
				estelas[p] = e
				cuenta += 1
			end
			if e then
				e.hasta = ahora + 0.25
			end
		end
	end
	for p, e in estelas do
		if ahora > e.hasta or not p.Parent then
			quitarEstela(p, e)
		end
	end
end

local function ambiente()
	local fase = Estado:GetAttribute("Fase")
	local condicion = if fase == "Vuelo" then Estado:GetAttribute("Condicion") else ""
	local reloj, brillo, densidad = base.reloj, base.brillo, base.densidad
	if condicion == "Nocturno" then
		reloj, brillo = 22.5, 0.55
	elseif condicion == "Niebla" then
		densidad = 0.62
	end
	if tormenta then
		reloj = if condicion == "Nocturno" then reloj else 18.6
		brillo = math.min(brillo, 0.9)
		densidad = math.max(densidad, 0.55)
	end
	local info = TweenInfo.new(3)
	TweenService:Create(Lighting, info, { ClockTime = reloj, Brightness = brillo }):Play()
	if atmosfera then
		TweenService:Create(atmosfera, info, { Density = densidad }):Play()
	end
end

function Efectos.selloActivo(): boolean
	return os.clock() < selloHasta
end

local function graficos()
	local brillo = Lighting:FindFirstChildOfClass("BloomEffect")
	local terreno = Workspace.Terrain
	local function bajos(): boolean
		return jugador:GetAttribute("GraficosBajos") == true
	end
	local function aplicar()
		local b = bajos()
		Lighting.GlobalShadows = not b
		if brillo then
			brillo.Enabled = not b
		end
		if b then
			terreno.WaterReflectance = 0
			terreno.WaterWaveSize = 0
		end
		for _, d in Workspace:GetDescendants() do
			if d:IsA("ParticleEmitter") then
				local original = d:GetAttribute("RitmoOriginal")
				if b and d.Rate > 0 and original == nil then
					d:SetAttribute("RitmoOriginal", d.Rate)
					d.Rate *= 0.4
				elseif not b and typeof(original) == "number" then
					d.Rate = original
					d:SetAttribute("RitmoOriginal", nil)
				end
			end
		end
	end
	jugador:GetAttributeChangedSignal("GraficosBajos"):Connect(aplicar)
	for _, propiedad in { "WaterReflectance", "WaterWaveSize" } do
		terreno:GetPropertyChangedSignal(propiedad):Connect(function()
			if bajos() and (terreno :: any)[propiedad] > 0 then
				(terreno :: any)[propiedad] = 0
			end
		end)
	end
	local maleza = { Helecho = true, HojasGrandes = true, Flores = true, Hierba = true, HierbaPlaya = true, ArbustoTropical = true, Conchas = true, Espuma = true }
	local plantas = 0
	Workspace.DescendantAdded:Connect(function(d)
		if bajos() and d:IsA("Model") and maleza[d.Name] then
			plantas += 1
			if plantas % 3 ~= 0 then
				task.defer(function()
					for _, p in d:GetDescendants() do
						if p:IsA("BasePart") then
							p.LocalTransparencyModifier = 1
						end
					end
				end)
			end
		end
		if bajos() and d:IsA("ParticleEmitter") then
			task.defer(function()
				if d.Rate > 0 and not d:GetAttribute("RitmoOriginal") then
					d:SetAttribute("RitmoOriginal", d.Rate)
					d.Rate *= 0.4
				end
			end)
		end
	end)
	aplicar()
end

function Efectos.iniciar()
	pantalla()
	avion:GetAttributeChangedSignal("Tormenta"):Connect(function()
		tormenta = avion:GetAttribute("Tormenta") == true
		ambiente()
	end)
	Estado:GetAttributeChangedSignal("Fase"):Connect(ambiente)
	Estado:GetAttributeChangedSignal("Fase"):Connect(function()
		if Estado:GetAttribute("Fase") == "Isla" then
			task.delay(1.7, sellar, elegir(FRASES_CHOQUE), "Diagnóstico: falta de habilidad", Gui.ROJO)
		end
	end)
	graficos()
	Estado:GetAttributeChangedSignal("Condicion"):Connect(ambiente)
	avion:GetAttributeChangedSignal("CaidaLibre"):Connect(function()
		if avion:GetAttribute("CaidaLibre") then
			Camara.impulsoFov(16)
			Camara.sacudir(0.5)
		end
	end)
	avion:GetAttributeChangedSignal("Bandada"):Connect(Pajaros.bandada)
	avion:GetAttributeChangedSignal("Pajaros"):Connect(function()
		Pajaros.choque()
		Camara.sacudir(0.9)
		destellar(Color3.fromRGB(255, 170, 90), 0.35, 0.5)
		drama()
	end)
	avion:GetAttributeChangedSignal("Mascarillas"):Connect(function()
		if avion:GetAttribute("Mascarillas") == true then
			drama()
		end
	end)
	avion:GetAttributeChangedSignal("Golpe"):Connect(function()
		Camara.sacudir(1)
	end)
	avion:GetAttributeChangedSignal("Aterrizaje"):Connect(function()
		local a = avion:GetAttribute("Aterrizaje")
		if a == "Perfecto" then
			Sonido.reproducir("Aplausos", nil, 1, 1)
			task.delay(0.4, sellar, elegir(FRASES_PERFECTO), "Aterrizaje perfecto", Gui.VERDE)
		elseif a == "Bueno" then
			Sonido.reproducir("Aplausos", nil, 0.6, 1)
		elseif a == "Duro" then
			Sonido.reproducir("Bonk", nil, 1, 0.8)
			task.delay(0.4, sellar, elegir(FRASES_DURO), "Aterrizaje duro", Gui.NARANJA)
		end
	end)
	avion:GetAttributeChangedSignal("Fase"):Connect(function()
		local fase = avion:GetAttribute("Fase")
		if fase == "Estrellado" then
			soltarFoto()
			if numero("Altitud") > 30 then
				return
			end
			Camara.sacudir(1)
			destellar(Color3.fromRGB(255, 120, 60), 0.8, 1.6)
			acercar(0.55, 0.45)
			Sonido.reproducir("BoomCartoon", nil, 1, 1)
		end
	end)
	for _, m in CollectionService:GetTagged("Pasajero") do
		task.spawn(pasajero, m)
	end
	CollectionService:GetInstanceAddedSignal("Pasajero"):Connect(pasajero)
	for _, m in CollectionService:GetTagged("Cocodrilo") do
		cocodrilo(m)
	end
	CollectionService:GetInstanceAddedSignal("Cocodrilo"):Connect(cocodrilo)
	for _, o in CollectionService:GetTagged("Objeto") do
		vaporCafe(o)
	end
	CollectionService:GetInstanceAddedSignal("Objeto"):Connect(vaporCafe)
	local function alJugador(otro: Player)
		if otro.Character then
			personaje(otro.Character)
		end
		otro.CharacterAdded:Connect(personaje)
	end
	for _, otro in Players:GetPlayers() do
		alJugador(otro)
	end
	Players.PlayerAdded:Connect(alJugador)
	RunService:BindToRenderStep("OverbookedZoom", Enum.RenderPriority.Camera.Value + 2, function(dt: number)
		if os.clock() > zoomHasta then
			zoomObjetivo = 1
		end
		zoom += (zoomObjetivo - zoom) * math.min(1, dt * (if zoomObjetivo < zoom then 14 else 4))
		if math.abs(zoom - 1) > 0.002 then
			local cam = Workspace.CurrentCamera
			cam.FieldOfView = math.clamp(cam.FieldOfView * zoom, 20, 120)
		end
	end)
	RunService.Heartbeat:Connect(function(dt)
		if tormenta and os.clock() > proximoRayo then
			proximoRayo = os.clock() + rng:NextNumber(2.5, 7)
			destellar(Color3.new(1, 1, 1), 0.65, 0.35)
			Camara.sacudir(0.25)
			task.delay(rng:NextNumber(0.2, 0.9), Sonido.reproducir, "Trueno", nil, rng:NextNumber(0.6, 1))
		end
		acumulado += dt
		if acumulado >= 0.1 then
			acumulado = 0
			vigilar()
		end
	end)
end

return Efectos
