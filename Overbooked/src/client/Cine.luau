--!strict
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Gui = require(ReplicatedStorage.Shared.Gui)
local ImagenesIntro = require(ReplicatedStorage.Shared.ImagenesIntro)
local Camara = require(script.Parent.Camara)
local ModoClip = require(script.Parent.ModoClip)
local Rafagas = require(script.Parent.Rafagas)
local Sonido = require(script.Parent.Sonido)

export type Toma = { duracion: number, camara: (number) -> (CFrame, number), saltable: boolean?, aCabeza: boolean? }

local Cine = {}

local PASO = "OverbookedCine"
local AGUA = 89.4
local jugador = Players.LocalPlayer
local Estado = ReplicatedStorage:WaitForChild("Estado")
local gui: ScreenGui? = nil
local raiz: Frame
local barras: { Frame } = {}
local generacion = 0
local enCurso = false
local restaurar: (() -> ())? = nil
local mando: any = nil
local telonActual: { Frame }? = nil

local function suave(a: number): number
	return a * a * a * (a * (a * 6 - 15) + 10)
end

local function imagen(padre: Instance, nombre: string, tamano: UDim2, posicion: UDim2): ImageLabel
	local i = Instance.new("ImageLabel")
	i.Name = nombre
	i.BackgroundTransparency = 1
	i.Image = `rbxassetid://{ImagenesIntro[nombre]}`
	i.Size = tamano
	i.Position = posicion
	i.AnchorPoint = Vector2.new(0.5, 0.5)
	i.Parent = padre
	return i
end

function Cine.telon(padre: Instance): (Frame, Frame)
	local function mitad(arriba: boolean): Frame
		local f = Instance.new("Frame")
		f.Name = "Telon"
		f.BackgroundColor3 = Gui.PAPEL
		f.BorderSizePixel = 0
		f.Size = UDim2.fromScale(1, 0.5)
		f.Position = UDim2.fromScale(0, if arriba then 0 else 0.5)
		f.ZIndex = 10
		local textura = Instance.new("ImageLabel")
		textura.BackgroundTransparency = 1
		textura.Image = `rbxassetid://{ImagenesIntro.Papel}`
		textura.ScaleType = Enum.ScaleType.Tile
		textura.TileSize = UDim2.fromOffset(512, 512)
		textura.Size = UDim2.fromScale(1, 1)
		textura.ZIndex = 10
		textura.Parent = f
		local borde = imagen(f, "Rasgado", UDim2.new(1, 40, 0, 110), UDim2.fromScale(0.5, if arriba then 1 else 0))
		borde.Rotation = if arriba then 0 else 180
		borde.ZIndex = 10
		f.Parent = padre
		return f
	end
	return mitad(true), mitad(false)
end

function Cine.abrirTelon(arriba: Frame, abajo: Frame)
	Sonido.reproducir("RasgarPapel", nil, 1.1, 1)
	local info = TweenInfo.new(0.65, Enum.EasingStyle.Back, Enum.EasingDirection.In)
	TweenService:Create(arriba, info, { Position = UDim2.fromScale(0, -0.62), Rotation = -1.5 }):Play()
	TweenService:Create(abajo, info, { Position = UDim2.fromScale(0, 1.12), Rotation = 1.5 }):Play()
	task.delay(0.8, function()
		arriba:Destroy()
		abajo:Destroy()
	end)
end

function Cine.cerrarTelon(padre: Instance): (Frame, Frame)
	local arriba, abajo = Cine.telon(padre)
	arriba.Position = UDim2.fromScale(0, -0.62)
	abajo.Position = UDim2.fromScale(0, 1.12)
	local info = TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	TweenService:Create(arriba, info, { Position = UDim2.fromScale(0, 0) }):Play()
	TweenService:Create(abajo, info, { Position = UDim2.fromScale(0, 0.5) }):Play()
	task.delay(0.35, Sonido.reproducir, "Bonk", nil, 0.5, 1.4)
	return arriba, abajo
end

function Cine.barra(padre: Instance, arriba: boolean): Frame
	local f = Instance.new("Frame")
	f.BackgroundColor3 = Gui.TINTA
	f.BorderSizePixel = 0
	f.Size = UDim2.fromScale(1, 0.08)
	f.AnchorPoint = Vector2.new(0, if arriba then 1 else 0)
	f.Position = UDim2.fromScale(0, if arriba then 0 else 1)
	f.ZIndex = 2
	local borde = imagen(f, "Rasgado", UDim2.new(1, 40, 0, 70), UDim2.fromScale(0.5, if arriba then 1 else 0))
	borde.Rotation = if arriba then 0 else 180
	borde.ImageColor3 = Gui.TINTA
	borde.ZIndex = 2
	f.Parent = padre
	return f
end

function Cine.moverBarras(lista: { Frame }, dentro: boolean)
	local info = TweenInfo.new(0.45, Enum.EasingStyle.Quad, if dentro then Enum.EasingDirection.Out else Enum.EasingDirection.In)
	TweenService:Create(lista[1], info, { Position = UDim2.fromScale(0, if dentro then 0.08 else 0) }):Play()
	TweenService:Create(lista[2], info, { Position = UDim2.fromScale(0, if dentro then 0.92 else 1) }):Play()
end

function Cine.ocultarHud(conservar: { [string]: boolean }): () -> ()
	local playerGui = jugador:WaitForChild("PlayerGui")
	local ocultos: { [ScreenGui]: boolean } = {}
	local function ocultar(g: Instance)
		if g:IsA("ScreenGui") and not conservar[g.Name] and g.Enabled then
			ocultos[g] = true
			g.Enabled = false
		end
	end
	for _, g in playerGui:GetChildren() do
		ocultar(g)
	end
	local vigilancia = playerGui.ChildAdded:Connect(ocultar)
	local avisos = ProximityPromptService.Enabled
	ProximityPromptService.Enabled = false
	return function()
		vigilancia:Disconnect()
		for g in ocultos do
			g.Enabled = true
		end
		ProximityPromptService.Enabled = avisos
	end
end

function Cine.controles(): any
	if mando == nil then
		local m = jugador:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule", 5)
		if m and m:IsA("ModuleScript") then
			local ok, r = pcall(require, m)
			if ok and r then
				mando = (r :: any):GetControls()
			end
		end
	end
	return mando
end

function Cine.destino(): CFrame?
	local personaje = jugador.Character
	local r = personaje and personaje:FindFirstChild("HumanoidRootPart")
	if not r or not r:IsA("BasePart") then
		return nil
	end
	local ojo = r.CFrame:PointToWorldSpace(Vector3.new(0, 1.5, 0))
	local plano = r.CFrame.LookVector * Vector3.new(1, 0, 1)
	local frente = if plano.Magnitude > 0.01 then plano.Unit else Vector3.new(0, 0, -1)
	if Camara.esTerceraPersona() then
		local dir = (frente - Vector3.new(0, 0.3, 0)).Unit
		return CFrame.lookAt(ojo - dir * 10.5, ojo)
	end
	return CFrame.lookAt(ojo, ojo + frente)
end

local function asegurar(): Frame
	if gui then
		return raiz
	end
	local g = Instance.new("ScreenGui")
	g.Name = "Cine"
	g.IgnoreGuiInset = true
	g.ResetOnSpawn = false
	g.DisplayOrder = 45
	g.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	raiz = Instance.new("Frame")
	raiz.BackgroundTransparency = 1
	raiz.Parent = g
	local escala = Instance.new("UIScale")
	escala.Parent = raiz
	local function ajustar()
		local s = Gui.escala(0.45, 1.4)
		escala.Scale = s
		raiz.Size = UDim2.fromScale(1 / s, 1 / s)
	end
	ajustar()
	Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(ajustar)
	barras = { Cine.barra(raiz, true), Cine.barra(raiz, false) }
	g.Parent = jugador:WaitForChild("PlayerGui")
	gui = g
	return raiz
end

function Cine.activo(): boolean
	return enCurso or telonActual ~= nil
end

function Cine.cortina(cerrada: boolean)
	local r = asegurar()
	if cerrada then
		if telonActual then
			return
		end
		local a, b = Cine.cerrarTelon(r)
		local par = { a, b }
		telonActual = par
		task.delay(7, function()
			if telonActual == par then
				Cine.cortina(false)
			end
		end)
	else
		local t = telonActual
		telonActual = nil
		if t then
			Cine.abrirTelon(t[1], t[2])
		end
	end
end

function Cine.terminar()
	generacion += 1
	RunService:UnbindFromRenderStep(PASO)
	if not enCurso then
		return
	end
	enCurso = false
	jugador:SetAttribute("EnCine", nil)
	if not ModoClip.activo() then
		local cam = Workspace.CurrentCamera
		cam.CameraType = Enum.CameraType.Custom
		local personaje = jugador.Character
		local humanoide = personaje and personaje:FindFirstChildOfClass("Humanoid")
		if humanoide then
			cam.CameraSubject = humanoide
		end
	end
	Cine.moverBarras(barras, false)
	local r = restaurar
	restaurar = nil
	if r then
		r()
	end
	local c = Cine.controles()
	if c then
		c:Enable()
	end
end

local function volarACabeza(mia: number, desde: CFrame, fovDesde: number)
	local t0 = os.clock()
	RunService:UnbindFromRenderStep(PASO)
	RunService:BindToRenderStep(PASO, Enum.RenderPriority.Camera.Value + 3, function()
		local cam = Workspace.CurrentCamera
		local hasta = Cine.destino() or desde
		local e = suave(math.clamp((os.clock() - t0) / 0.9, 0, 1))
		local medio = desde.Position:Lerp(hasta.Position, 0.5) + Vector3.new(0, (desde.Position - hasta.Position).Magnitude * 0.15, 0)
		local u = 1 - e
		local p = desde.Position * u * u + medio * 2 * u * e + hasta.Position * e * e
		local fovBase = cam.FieldOfView
		cam.CFrame = CFrame.new(p) * desde.Rotation:Lerp(hasta.Rotation, e)
		cam.FieldOfView = fovDesde + (fovBase - fovDesde) * e
	end)
	while os.clock() - t0 < 0.9 and mia == generacion and not ModoClip.activo() do
		task.wait()
	end
end

function Cine.toma(t: Toma): boolean
	if ModoClip.activo() then
		return false
	end
	generacion += 1
	local mia = generacion
	asegurar()
	if not enCurso then
		enCurso = true
		jugador:SetAttribute("EnCine", true)
		restaurar = Cine.ocultarHud({ Cine = true, OverbookedEfectos = true })
		Cine.moverBarras(barras, true)
		local c = Cine.controles()
		if c then
			c:Disable()
		end
	end
	local inicio = os.clock()
	local saltado = false
	local entrada = UserInputService.InputBegan:Connect(function(e: InputObject, procesado: boolean)
		local tipo = e.UserInputType
		local valido = tipo == Enum.UserInputType.Touch or tipo == Enum.UserInputType.MouseButton1 or tipo == Enum.UserInputType.Keyboard or (string.find(tipo.Name, "Gamepad") ~= nil and e.KeyCode ~= Enum.KeyCode.Thumbstick1 and e.KeyCode ~= Enum.KeyCode.Thumbstick2)
		if t.saltable and not procesado and valido and e.KeyCode ~= Enum.KeyCode.Escape and os.clock() - inicio > 0.6 then
			saltado = true
		end
	end)
	local ultimo = Workspace.CurrentCamera.CFrame
	local ultimoFov = Workspace.CurrentCamera.FieldOfView
	RunService:UnbindFromRenderStep(PASO)
	RunService:BindToRenderStep(PASO, Enum.RenderPriority.Camera.Value + 3, function()
		local cam = Workspace.CurrentCamera
		if cam.CameraType ~= Enum.CameraType.Scriptable then
			cam.CameraType = Enum.CameraType.Scriptable
		end
		local cf, fov = t.camara(math.min(os.clock() - inicio, t.duracion))
		cam.CFrame = cf
		cam.FieldOfView = fov
		ultimo, ultimoFov = cf, fov
	end)
	while os.clock() - inicio < t.duracion and not saltado and mia == generacion and not ModoClip.activo() do
		task.wait()
	end
	entrada:Disconnect()
	if mia ~= generacion then
		return not saltado
	end
	if t.aCabeza and not saltado and not ModoClip.activo() then
		volarACabeza(mia, ultimo, ultimoFov)
		if mia ~= generacion then
			return true
		end
	end
	Cine.terminar()
	return not saltado
end

local function centroAvion(): Vector3
	local avion = Workspace:FindFirstChild("Avion")
	local p = avion and avion:FindFirstChild("Centro", true)
	return if p and p:IsA("BasePart") then p.Position else Vector3.new(0, 105, -18)
end

local function libre(desde: Vector3, hasta: Vector3): boolean
	local parametros = RaycastParams.new()
	parametros.FilterType = Enum.RaycastFilterType.Exclude
	local excluir: { Instance } = {}
	local avion = Workspace:FindFirstChild("Avion")
	if avion then
		table.insert(excluir, avion)
	end
	for _, p in Players:GetPlayers() do
		if p.Character then
			table.insert(excluir, p.Character)
		end
	end
	parametros.FilterDescendantsInstances = excluir
	if Workspace:Raycast(desde, hasta - desde, parametros) then
		return false
	end
	local suelo = Workspace:Raycast(hasta, Vector3.new(0, -6, 0), parametros)
	return suelo == nil
end

local function anguloLibre(centro: Vector3, radio: number, alto: number): number
	for k = 0, 7 do
		local a = math.pi * 0.25 * k + 0.4
		local pos = centro + Vector3.new(math.cos(a) * radio, alto, math.sin(a) * radio)
		if libre(centro + Vector3.new(0, 4, 0), pos) then
			return a
		end
	end
	return 0.4
end

local function naufragio()
	if ModoClip.activo() then
		return
	end
	Cine.cortina(true)
	local limite = os.clock() + 6
	local isla = Workspace:FindFirstChild("Isla")
	while not isla and os.clock() < limite do
		task.wait(0.1)
		isla = Workspace:FindFirstChild("Isla")
	end
	task.wait(0.45)
	Cine.cortina(false)
	if not isla then
		return
	end
	local centro = centroAvion() + Vector3.new(0, -3, 0)
	local a0 = anguloLibre(centro, 72, 20)
	local duracion = 3.6
	Cine.toma({
		duracion = duracion,
		saltable = true,
		aCabeza = true,
		camara = function(t: number): (CFrame, number)
			local e = suave(t / duracion)
			local a = a0 + 0.38 * t / duracion
			local radio = 72 - 12 * e
			local pos = centro + Vector3.new(math.cos(a) * radio, 20 - 7 * e, math.sin(a) * radio)
			local sacudida = Vector3.new(math.noise(t * 6, 1), math.noise(t * 6, 2), 0) * 0.6 * (1 - e)
			return CFrame.lookAt(pos + sacudida, centro), 52 - 8 * e
		end,
	})
end

local function hidroavion(p: BasePart)
	local inicio = p:GetAttribute("Inicio")
	local duracion = p:GetAttribute("Duracion")
	if typeof(inicio) ~= "number" or typeof(duracion) ~= "number" then
		return
	end
	local final = p.CFrame
	local salida = final.Position + Vector3.new(1400, 260, 0)
	local aproximacion = final.Position + Vector3.new(330, 2, 0)
	local CORTE = 0.72
	local function pose(u: number): CFrame
		if u < CORTE then
			local e = suave(u / CORTE)
			local pos = salida:Lerp(aproximacion, e) + Vector3.new(0, 60 * math.sin(e * math.pi) * (1 - e), 0)
			return CFrame.new(pos) * final.Rotation
		end
		local e = 1 - (1 - (u - CORTE) / (1 - CORTE)) ^ 2
		return CFrame.new(aproximacion:Lerp(final.Position, e)) * final.Rotation
	end
	local tomado = false
	local proximaOla = 0
	local conexion: RBXScriptConnection
	conexion = RunService.PreRender:Connect(function()
		local u = (Workspace:GetServerTimeNow() - inicio) / duracion
		if u >= 1 or not p.Parent then
			conexion:Disconnect()
			if p.Parent then
				p.CFrame = final
			end
			return
		end
		local cf = pose(math.max(u, 0))
		p.CFrame = cf
		local ahora = os.clock()
		if u >= CORTE and ahora > proximaOla then
			proximaOla = ahora + 0.22
			Rafagas.lanzar("Salpicadura", Vector3.new(cf.Position.X, AGUA, cf.Position.Z), 1.3)
		end
		if u >= CORTE - 0.03 and not tomado then
			tomado = true
			local muelle = final.Position
			local lado = if libre(muelle + Vector3.new(0, 6, 0), muelle + Vector3.new(-28, 10, 32)) then 1 else -1
			local camara = muelle + Vector3.new(-28, 10, 32 * lado)
			local resto = (1 - u) * duracion + 1.2
			task.spawn(Cine.toma, {
				duracion = resto,
				saltable = true,
				aCabeza = true,
				camara = function(t: number): (CFrame, number)
					local objetivo = if p.Parent then p.Position else muelle
					return CFrame.lookAt(camara + Vector3.new(0, 0, -3 * lado * t / resto), objetivo + Vector3.new(0, -2, 0)), 46
				end,
			})
		end
	end)
end

function Cine.iniciar()
	Estado:GetAttributeChangedSignal("Fase"):Connect(function()
		if Estado:GetAttribute("Fase") == "Isla" then
			task.spawn(naufragio)
		end
	end)
	Workspace.DescendantAdded:Connect(function(d: Instance)
		if d.Name == "Hidroavion" and d:IsA("BasePart") then
			local p: BasePart = d
			task.defer(function()
				hidroavion(p)
			end)
		end
	end)
end

return Cine
