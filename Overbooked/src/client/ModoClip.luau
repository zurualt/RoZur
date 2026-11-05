--!strict
local ContextActionService = game:GetService("ContextActionService")
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ProximityPromptService = game:GetService("ProximityPromptService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local StarterGui = game:GetService("StarterGui")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Gui = require(ReplicatedStorage.Shared.Gui)
local Agarre = require(script.Parent.Agarre)
local Camara = require(script.Parent.Camara)
local Sonido = require(script.Parent.Sonido)

local ModoClip = {}

local jugador = Players.LocalPlayer
local PASO = "OverbookedModoClip"
local BLOQUEO = "OverbookedModoClipBloqueo"
local RADIO = 32
local NUCLEO = { Enum.CoreGuiType.PlayerList, Enum.CoreGuiType.Health, Enum.CoreGuiType.Backpack, Enum.CoreGuiType.Chat, Enum.CoreGuiType.EmotesMenu }
local BLOQUEADAS: { Enum.KeyCode | Enum.UserInputType } = {
	Enum.KeyCode.W, Enum.KeyCode.A, Enum.KeyCode.S, Enum.KeyCode.D, Enum.KeyCode.Q, Enum.KeyCode.E, Enum.KeyCode.F, Enum.KeyCode.G,
	Enum.KeyCode.T, Enum.KeyCode.R, Enum.KeyCode.H, Enum.KeyCode.M, Enum.KeyCode.O, Enum.KeyCode.Z, Enum.KeyCode.X, Enum.KeyCode.B,
	Enum.KeyCode.Space, Enum.KeyCode.LeftShift, Enum.KeyCode.RightShift, Enum.KeyCode.LeftControl, Enum.KeyCode.RightControl,
	Enum.KeyCode.Up, Enum.KeyCode.Down, Enum.KeyCode.Left, Enum.KeyCode.Right,
	Enum.KeyCode.ButtonA, Enum.KeyCode.ButtonB, Enum.KeyCode.ButtonX, Enum.KeyCode.ButtonY, Enum.KeyCode.ButtonR1, Enum.KeyCode.ButtonL1,
	Enum.KeyCode.ButtonR2, Enum.KeyCode.ButtonL2, Enum.KeyCode.DPadUp, Enum.KeyCode.DPadDown, Enum.KeyCode.DPadLeft, Enum.KeyCode.DPadRight,
	Enum.KeyCode.Thumbstick1, Enum.KeyCode.Thumbstick2,
	Enum.UserInputType.MouseButton1, Enum.UserInputType.MouseButton2,
}
local PISTA_TECLADO = "P salir · F seguir · B desenfoque · Z/X zoom · rueda: velocidad"
local PISTA_MANDO = "B salir · Y seguir · X desenfoque · R1/L1 zoom · cruceta: velocidad"
local PISTA_TACTIL = "Arrastra para mirar · pellizca para moverte · toca aquí para salir"

local activo = false
local deshacer: { () -> () } = {}
local siguiendo = false
local desenfoque: DepthOfFieldEffect? = nil
local posicion = Vector3.zero
local velocidadActual = Vector3.zero
local velocidad = 10
local yaw, pitch, yawObjetivo, pitchObjetivo = 0, 0, 0, 0
local fov, fovObjetivo = 70, 70
local distancia, distanciaObjetivo = 8, 8
local foco = 20
local palancaMover = Vector2.zero
local palancaMirar = Vector2.zero
local gatillos = Vector2.zero
local toque = Vector2.zero
local pellizco = 0
local escalaPellizco = 1
local gui: ScreenGui? = nil
local etiqueta: ImageButton
local pista: TextLabel
local titulo: TextLabel
local turno = 0

local function raizDe(): BasePart?
	local personaje = jugador.Character
	local r = personaje and personaje:FindFirstChild("HumanoidRootPart")
	return if r and r:IsA("BasePart") then r else nil
end

local function construirIndicador()
	local g = Instance.new("ScreenGui")
	g.Name = "ModoClip"
	g.IgnoreGuiInset = true
	g.ResetOnSpawn = false
	g.DisplayOrder = 40
	local raiz = Instance.new("Frame")
	raiz.BackgroundTransparency = 1
	raiz.Parent = g
	local escala = Instance.new("UIScale")
	local v = Workspace.CurrentCamera.ViewportSize
	local s = math.clamp(math.min(v.X / 1366, v.Y / 768), 0.55, 1.2)
	escala.Scale = s
	raiz.Size = UDim2.fromScale(1 / s, 1 / s)
	escala.Parent = raiz
	etiqueta = Gui.panel(raiz, "Etiqueta", UDim2.fromOffset(440, 124), UDim2.fromOffset(18, 18), nil, true) :: any
	etiqueta.AutoButtonColor = false
	etiqueta.Rotation = -2
	titulo = Gui.texto(etiqueta, "MODO CLIP", UDim2.new(1, -96, 0, 40), UDim2.fromOffset(72, 14), Gui.NARANJA, true)
	titulo.TextXAlignment = Enum.TextXAlignment.Left
	Gui.trazado(titulo)
	pista = Gui.texto(etiqueta, "", UDim2.new(1, -96, 0, 54), UDim2.fromOffset(72, 56), Gui.TINTA, false)
	pista.TextXAlignment = Enum.TextXAlignment.Left
	etiqueta.Activated:Connect(function()
		ModoClip.salir()
	end)
	g.Parent = jugador:WaitForChild("PlayerGui")
	gui = g
end

local function mostrar(texto: string?)
	if not gui then
		construirIndicador()
	end
	local ultimo = UserInputService:GetLastInputType()
	pista.Text = texto or (if ultimo == Enum.UserInputType.Touch then PISTA_TACTIL elseif string.find(ultimo.Name, "Gamepad") then PISTA_MANDO else PISTA_TECLADO)
	etiqueta.ImageTransparency = 0
	for _, t in { titulo, pista } do
		t.TextTransparency = 0
		t.TextStrokeTransparency = if t == titulo then 0.15 else 1
	end
	turno += 1
	local mio = turno
	task.delay(2, function()
		if mio ~= turno or not gui then
			return
		end
		local info = TweenInfo.new(0.6)
		TweenService:Create(etiqueta, info, { ImageTransparency = 1 }):Play()
		for _, t in { titulo, pista } do
			TweenService:Create(t, info, { TextTransparency = 1, TextStrokeTransparency = 1 }):Play()
		end
	end)
end

local function avisar(texto: string)
	local g = gui
	mostrar(texto)
	if not activo and not g then
		task.delay(2.8, function()
			if not activo and gui then
				(gui :: ScreenGui):Destroy()
				gui = nil
			end
		end)
	end
end

local function orientacionDe(mirada: Vector3)
	yaw = math.atan2(-mirada.X, -mirada.Z)
	pitch = math.asin(math.clamp(mirada.Y, -1, 1))
	yawObjetivo, pitchObjetivo = yaw, pitch
end

local function cabeza(r: BasePart): Vector3
	return r.CFrame:PointToWorldSpace(Vector3.new(0, 1.5, 0))
end

local function alternarSeguir()
	local r = raizDe()
	if not r then
		return
	end
	local cam = Workspace.CurrentCamera
	siguiendo = not siguiendo
	if siguiendo then
		local centro = cabeza(r)
		local desde = cam.CFrame.Position
		distanciaObjetivo = math.clamp((desde - centro).Magnitude, 2.5, 24)
		distancia = distanciaObjetivo
		local dir = centro - desde
		orientacionDe(if dir.Magnitude > 0.01 then dir.Unit else cam.CFrame.LookVector)
	else
		posicion = cam.CFrame.Position
		velocidadActual = Vector3.zero
		orientacionDe(cam.CFrame.LookVector)
	end
	mostrar(if siguiendo then "Siguiendo a tu personaje" else "Cámara libre")
end

local function alternarDesenfoque()
	local d = desenfoque
	if d then
		d:Destroy()
		desenfoque = nil
	else
		local nuevo = Instance.new("DepthOfFieldEffect")
		nuevo.Name = "ModoClipDesenfoque"
		nuevo.FarIntensity = 0.8
		nuevo.NearIntensity = 0.7
		nuevo.FocusDistance = foco
		nuevo.InFocusRadius = 6
		nuevo.Parent = Lighting
		desenfoque = nuevo
	end
	mostrar(if desenfoque then "Desenfoque activado" else "Desenfoque desactivado")
end

local function cambiarVelocidad(factor: number)
	velocidad = math.clamp(velocidad * factor, 2, 60)
	mostrar(`Velocidad {math.floor(velocidad + 0.5)}`)
end

local function controles(): any
	local m = jugador:WaitForChild("PlayerScripts"):FindFirstChild("PlayerModule")
	if m and m:IsA("ModuleScript") then
		local ok, r = pcall(require, m)
		if ok and r then
			return (r :: any):GetControls()
		end
	end
	return nil
end

local function tecla(k: Enum.KeyCode): number
	return if UserInputService:IsKeyDown(k) then 1 else 0
end

local function boton(k: Enum.KeyCode): number
	return if UserInputService:IsGamepadButtonDown(Enum.UserInputType.Gamepad1, k) then 1 else 0
end

local function zona(v: Vector2): Vector2
	return if v.Magnitude < 0.15 then Vector2.zero else v
end

local function paso(dt: number)
	local cam = Workspace.CurrentCamera
	local r = raizDe()
	if not r then
		ModoClip.salir()
		return
	end
	if cam.CameraType ~= Enum.CameraType.Scriptable then
		cam.CameraType = Enum.CameraType.Scriptable
	end
	if not Camara.esTerceraPersona() then
		Camara.terceraPersona(true)
	end
	if UserInputService.MouseEnabled then
		UserInputService.MouseBehavior = Enum.MouseBehavior.LockCenter
	end
	local escritura = UserInputService:GetFocusedTextBox() ~= nil
	local raton = UserInputService:GetMouseDelta()
	local sensibilidad = 0.0035 * fov / 70
	local mirar = zona(palancaMirar)
	yawObjetivo -= raton.X * sensibilidad + mirar.X * dt * 2.2 + toque.X * 0.006
	pitchObjetivo = math.clamp(pitchObjetivo - raton.Y * sensibilidad + mirar.Y * dt * 1.8 - toque.Y * 0.006, -1.45, 1.45)
	toque = Vector2.zero
	local k = 1 - math.exp(-dt * 10)
	yaw += (yawObjetivo - yaw) * k
	pitch += (pitchObjetivo - pitch) * k
	local giro = CFrame.fromEulerAnglesYXZ(pitch, yaw, 0)
	local mover = zona(palancaMover)
	local entrada = if escritura then Vector3.zero else Vector3.new(
		tecla(Enum.KeyCode.D) - tecla(Enum.KeyCode.A) + mover.X,
		tecla(Enum.KeyCode.E) - tecla(Enum.KeyCode.Q) + gatillos.X - gatillos.Y,
		tecla(Enum.KeyCode.S) - tecla(Enum.KeyCode.W) - mover.Y
	)
	local cf: CFrame
	if siguiendo then
		distanciaObjetivo = math.clamp(distanciaObjetivo + entrada.Z * dt * velocidad * 0.6 - pellizco * 6, 2.5, 24)
		yawObjetivo -= entrada.X * dt * 1.4
		pitchObjetivo = math.clamp(pitchObjetivo - entrada.Y * dt * 1.0, -1.45, 1.45)
		distancia += (distanciaObjetivo - distancia) * k
		cf = CFrame.new(cabeza(r)) * giro * CFrame.new(0, 0, distancia)
		foco = distancia
	else
		local factor = if not escritura and tecla(Enum.KeyCode.LeftShift) > 0 then 3 elseif not escritura and tecla(Enum.KeyCode.LeftControl) > 0 then 0.3 else 1
		local deseada = giro:VectorToWorldSpace(entrada) * velocidad * factor
		velocidadActual = velocidadActual:Lerp(deseada, 1 - math.exp(-dt * 6))
		posicion += velocidadActual * dt + giro.LookVector * pellizco * 6
		local desvio = posicion - r.Position
		if desvio.Magnitude > RADIO then
			posicion = r.Position + desvio.Unit * RADIO
		end
		cf = CFrame.new(posicion) * giro
	end
	pellizco = 0
	local zoom = if escritura then 0 else tecla(Enum.KeyCode.X) - tecla(Enum.KeyCode.Z) + boton(Enum.KeyCode.ButtonL1) - boton(Enum.KeyCode.ButtonR1)
	fovObjetivo = math.clamp(fovObjetivo + zoom * dt * 35, 15, 100)
	fov += (fovObjetivo - fov) * k
	cam.CFrame = cf
	cam.FieldOfView = fov
	local d = desenfoque
	if d then
		if not siguiendo then
			local rayo = Workspace:Raycast(cf.Position, cf.LookVector * 300)
			foco += ((if rayo then rayo.Distance else 300) - foco) * math.min(1, dt * 5)
		end
		d.FocusDistance = foco
		d.InFocusRadius = math.clamp(foco * 0.25, 1.5, 20)
	end
	for _, h in cam:GetChildren() do
		if h:IsA("Highlight") then
			h.Enabled = false
		end
	end
	local personaje = jugador.Character
	if personaje then
		for _, p in personaje:GetDescendants() do
			if p:IsA("BasePart") then
				p.LocalTransparencyModifier = 0
			end
		end
	end
end

function ModoClip.activo(): boolean
	return activo
end

function ModoClip.entrar()
	local r = raizDe()
	local playerGui = jugador:WaitForChild("PlayerGui")
	local intro = playerGui:FindFirstChild("Intro")
	if activo or not r or (intro and intro:IsA("ScreenGui") and intro.Enabled) then
		return
	end
	if Agarre.sostenido() then
		avisar("Suelta lo que llevas para grabar")
		return
	end
	activo = true
	local cam = Workspace.CurrentCamera
	siguiendo = false
	posicion = cam.CFrame.Position
	velocidadActual = Vector3.zero
	orientacionDe(cam.CFrame.LookVector)
	fov = cam.FieldOfView
	fovObjetivo = fov

	local ocultos: { [ScreenGui]: boolean } = {}
	local lejanias: { [BillboardGui]: number } = {}
	local function ocultar(g: Instance)
		if g:IsA("ScreenGui") and g.Name ~= "ModoClip" and g.Enabled then
			ocultos[g] = true
			g.Enabled = false
		elseif g:IsA("BillboardGui") and lejanias[g] == nil then
			lejanias[g] = g.MaxDistance
			g.MaxDistance = 0.05
		end
	end
	for _, g in playerGui:GetChildren() do
		ocultar(g)
	end
	local vigilancia = playerGui.ChildAdded:Connect(ocultar)
	table.insert(deshacer, function()
		vigilancia:Disconnect()
		for g in ocultos do
			g.Enabled = true
		end
		for g, valor in lejanias do
			g.MaxDistance = valor
		end
	end)

	local nucleo: { [Enum.CoreGuiType]: boolean } = {}
	for _, tipo in NUCLEO do
		nucleo[tipo] = StarterGui:GetCoreGuiEnabled(tipo)
		StarterGui:SetCoreGuiEnabled(tipo, false)
	end
	table.insert(deshacer, function()
		for tipo, valor in nucleo do
			StarterGui:SetCoreGuiEnabled(tipo, valor)
		end
	end)

	local avisos = ProximityPromptService.Enabled
	ProximityPromptService.Enabled = false
	table.insert(deshacer, function()
		ProximityPromptService.Enabled = avisos
	end)

	ContextActionService:BindActionAtPriority(BLOQUEO, function()
		return Enum.ContextActionResult.Sink
	end, false, Enum.ContextActionPriority.High.Value + 60, table.unpack(BLOQUEADAS))
	table.insert(deshacer, function()
		ContextActionService:UnbindAction(BLOQUEO)
	end)

	local mando = controles()
	if mando then
		mando:Disable()
		table.insert(deshacer, function()
			mando:Enable()
		end)
	end

	local transparencias: { [BasePart]: number } = {}
	local personaje = jugador.Character
	if personaje then
		for _, p in personaje:GetDescendants() do
			if p:IsA("BasePart") then
				transparencias[p] = p.LocalTransparencyModifier
			end
		end
	end
	table.insert(deshacer, function()
		Camara.terceraPersona(personaje ~= nil and personaje:GetAttribute("Ragdoll") == true)
		for p, valor in transparencias do
			p.LocalTransparencyModifier = valor
		end
	end)

	local resaltados: { [Highlight]: boolean } = {}
	for _, h in cam:GetChildren() do
		if h:IsA("Highlight") then
			resaltados[h] = h.Enabled
		end
	end
	table.insert(deshacer, function()
		for h, valor in resaltados do
			h.Enabled = valor
		end
	end)

	local icono = UserInputService.MouseIconEnabled
	UserInputService.MouseIconEnabled = false
	table.insert(deshacer, function()
		UserInputService.MouseIconEnabled = icono
		UserInputService.MouseBehavior = Enum.MouseBehavior.Default
	end)

	table.insert(deshacer, function()
		local d = desenfoque
		if d then
			d:Destroy()
			desenfoque = nil
		end
		local g = gui
		if g then
			g:Destroy()
			gui = nil
		end
	end)

	RunService:BindToRenderStep(PASO, Enum.RenderPriority.Camera.Value + 5, paso)
	Sonido.reproducir("UiClick", nil, 0.8, 0.8)
	mostrar(nil)
end

function ModoClip.salir()
	if not activo then
		return
	end
	activo = false
	RunService:UnbindFromRenderStep(PASO)
	for i = #deshacer, 1, -1 do
		deshacer[i]()
	end
	table.clear(deshacer)
	local cam = Workspace.CurrentCamera
	local r = raizDe()
	if r then
		local ojo = cabeza(r)
		local frente = r.CFrame.LookVector * Vector3.new(1, 0, 1)
		frente = if frente.Magnitude > 0.01 then frente.Unit else Vector3.new(0, 0, -1)
		cam.CFrame = if Camara.esTerceraPersona() then CFrame.lookAt(ojo - (frente - Vector3.new(0, 0.3, 0)).Unit * 10.5, ojo) else CFrame.lookAt(ojo, ojo + frente)
	end
	cam.CameraType = Enum.CameraType.Custom
	local humanoide = jugador.Character and jugador.Character:FindFirstChildOfClass("Humanoid")
	if humanoide then
		cam.CameraSubject = humanoide
	end
	Sonido.reproducir("UiClick", nil, 0.8, 1.2)
end

function ModoClip.alternar()
	if activo then
		ModoClip.salir()
	else
		ModoClip.entrar()
	end
end

function ModoClip.iniciar()
	UserInputService.InputBegan:Connect(function(entrada, procesado)
		if UserInputService:GetFocusedTextBox() then
			return
		end
		local k = entrada.KeyCode
		if k == Enum.KeyCode.P and not procesado then
			ModoClip.alternar()
		elseif (k == Enum.KeyCode.ButtonR3 and UserInputService:IsGamepadButtonDown(entrada.UserInputType, Enum.KeyCode.ButtonL3)) or (k == Enum.KeyCode.ButtonL3 and UserInputService:IsGamepadButtonDown(entrada.UserInputType, Enum.KeyCode.ButtonR3)) then
			ModoClip.alternar()
		elseif not activo then
			return
		elseif k == Enum.KeyCode.ButtonB then
			ModoClip.salir()
		elseif k == Enum.KeyCode.F or k == Enum.KeyCode.ButtonY then
			alternarSeguir()
		elseif k == Enum.KeyCode.B or k == Enum.KeyCode.ButtonX then
			alternarDesenfoque()
		elseif k == Enum.KeyCode.DPadUp then
			cambiarVelocidad(1.25)
		elseif k == Enum.KeyCode.DPadDown then
			cambiarVelocidad(0.8)
		end
	end)
	UserInputService.InputChanged:Connect(function(entrada, procesado)
		if not activo then
			return
		end
		local tipo = entrada.UserInputType
		if tipo == Enum.UserInputType.MouseWheel then
			cambiarVelocidad(if entrada.Position.Z > 0 then 1.25 else 0.8)
		elseif tipo == Enum.UserInputType.Touch and not procesado then
			toque += Vector2.new(entrada.Delta.X, entrada.Delta.Y)
		elseif entrada.KeyCode == Enum.KeyCode.Thumbstick1 then
			palancaMover = Vector2.new(entrada.Position.X, entrada.Position.Y)
		elseif entrada.KeyCode == Enum.KeyCode.Thumbstick2 then
			palancaMirar = Vector2.new(entrada.Position.X, entrada.Position.Y)
		elseif entrada.KeyCode == Enum.KeyCode.ButtonR2 then
			gatillos = Vector2.new(entrada.Position.Z, gatillos.Y)
		elseif entrada.KeyCode == Enum.KeyCode.ButtonL2 then
			gatillos = Vector2.new(gatillos.X, entrada.Position.Z)
		end
	end)
	UserInputService.InputEnded:Connect(function(entrada)
		local k = entrada.KeyCode
		if k == Enum.KeyCode.Thumbstick1 then
			palancaMover = Vector2.zero
		elseif k == Enum.KeyCode.Thumbstick2 then
			palancaMirar = Vector2.zero
		elseif k == Enum.KeyCode.ButtonR2 then
			gatillos = Vector2.new(0, gatillos.Y)
		elseif k == Enum.KeyCode.ButtonL2 then
			gatillos = Vector2.new(gatillos.X, 0)
		end
	end)
	UserInputService.TouchPinch:Connect(function(_, escala, _, estado, procesado)
		if not activo or procesado then
			return
		end
		if estado == Enum.UserInputState.Begin then
			escalaPellizco = escala
		else
			pellizco += escala - escalaPellizco
			escalaPellizco = escala
		end
	end)
end

return ModoClip
