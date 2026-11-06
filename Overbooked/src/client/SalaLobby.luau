--!strict
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SocialService = game:GetService("SocialService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")

local Gui = require(ReplicatedStorage.Shared.Gui)
local Sonido = require(script.Parent.Sonido)

type Datos = { d: number, m: string, j: { number }, c: number }

local SalaLobby = {}

local jugador = Players.LocalPlayer
local Estado = ReplicatedStorage:WaitForChild("Estado") :: Folder
local MODOS: { [string]: { texto: string, color: Color3 } } = {
	Amigos = { texto = "Solo amigos", color = Gui.TURQUESA },
	Publica = { texto = "Abierta a todos", color = Gui.VERDE },
	Privada = { texto = "Cerrada", color = Gui.ROJO },
}
local ANCHO = 380

local remoto: RemoteEvent? = nil
local gui: ScreenGui
local escala: UIScale
local panel: ImageLabel
local aparicion: UIScale
local titulo: TextLabel
local botonModo: ImageButton
local textoModo: TextLabel
local etiquetaModo: TextLabel
local lista: Frame
local botonDespegar: ImageButton
local espera: TextLabel
local visible = false
local ultimo = ""

local function enviar(accion: string, dato: any?)
	local r = remoto
	if r then
		r:FireServer(accion, dato)
	end
end

local function boton(padre: Instance, contenido: string, tamano: UDim2, posicion: UDim2, color: Color3, alPulsar: () -> ()): (ImageButton, TextLabel)
	local b = Gui.panel(padre, "Boton", tamano, posicion, nil, true) :: any
	b.ImageColor3 = color
	local t = Gui.texto(b, contenido, UDim2.new(1, -20, 1, -16), UDim2.fromOffset(10, 6), Gui.PAPEL, true)
	t.Name = "Texto"
	Gui.trazado(t)
	local limite = Instance.new("UITextSizeConstraint")
	limite.MaxTextSize = 30
	limite.Parent = t
	b.Activated:Connect(function()
		b.Rotation = -3
		TweenService:Create(b, TweenInfo.new(0.25, Enum.EasingStyle.Back), { Rotation = 0 }):Play()
		Sonido.reproducir("UiClick", nil, 0.6, 1)
		alPulsar()
	end)
	return b, t
end

local function leer(): Datos?
	for n = 1, 3 do
		local crudo = Estado:GetAttribute(`Sala{n}`)
		if typeof(crudo) == "string" and crudo ~= "" then
			local ok, t = pcall(HttpService.JSONDecode, HttpService, crudo)
			if ok and typeof(t) == "table" and typeof(t.j) == "table" and table.find(t.j, jugador.UserId) then
				return t :: any
			end
		end
	end
	return nil
end

local function nombreDe(id: number): string
	local p = Players:GetPlayerByUserId(id)
	return if p then p.DisplayName else "?"
end

local function pintar()
	local datos = leer()
	local crudo = if datos then HttpService:JSONEncode(datos) else ""
	if crudo == ultimo then
		return
	end
	ultimo = crudo
	if not datos then
		if visible then
			visible = false
			local t = TweenService:Create(aparicion, TweenInfo.new(0.18, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Scale = 0 })
			t.Completed:Connect(function()
				if not visible then
					panel.Visible = false
				end
			end)
			t:Play()
		end
		return
	end
	local capitan = datos.d == jugador.UserId
	local modo = MODOS[datos.m] or MODOS.Amigos
	titulo.Text = if capitan then "TU SALA" else `SALA DE {nombreDe(datos.d)}`
	botonModo.Visible = capitan
	etiquetaModo.Visible = not capitan
	textoModo.Text = modo.texto
	botonModo.ImageColor3 = modo.color
	etiquetaModo.Text = modo.texto
	etiquetaModo.TextColor3 = modo.color
	for _, h in lista:GetChildren() do
		if h:IsA("GuiObject") then
			h:Destroy()
		end
	end
	for i, id in datos.j do
		local fila = Instance.new("Frame")
		fila.BackgroundTransparency = 1
		fila.Size = UDim2.new(1, 0, 0, 44)
		fila.LayoutOrder = i
		fila.Parent = lista
		Gui.icono(fila, if id == datos.d then "Estrella" else "Pasajero", UDim2.fromOffset(34, 34), UDim2.new(0, 0, 0.5, 0), Vector2.new(0, 0.5))
		local t = Gui.texto(fila, nombreDe(id), UDim2.new(1, -110, 0, 32), UDim2.new(0, 44, 0.5, 0), Gui.TINTA, false, 24)
		t.AnchorPoint = Vector2.new(0, 0.5)
		t.TextXAlignment = Enum.TextXAlignment.Left
		t.TextTruncate = Enum.TextTruncate.AtEnd
		t.TextWrapped = false
		if capitan and id ~= jugador.UserId then
			local x = boton(fila, "X", UDim2.fromOffset(44, 40), UDim2.new(1, 0, 0.5, 0), Gui.ROJO, function()
				enviar("expulsar", id)
			end)
			x.AnchorPoint = Vector2.new(1, 0.5)
		end
	end
	local filas = #datos.j
	panel.Size = UDim2.fromOffset(ANCHO, 204 + filas * 48)
	local contando = datos.c > 0
	botonDespegar.Visible = capitan and not contando
	espera.Visible = not botonDespegar.Visible
	espera.Text = if contando then `SALE EN {datos.c}` else "Esperando al capitán..."
	espera.TextColor3 = if contando then Gui.NARANJA else Gui.LAPIZ
	if not visible then
		visible = true
		panel.Visible = true
		aparicion.Scale = 0.6
		TweenService:Create(aparicion, TweenInfo.new(0.35, Enum.EasingStyle.Back), { Scale = 1 }):Play()
		Sonido.reproducir("RasgarPapel", nil, 0.4, 1.2)
	end
end

local function construir()
	gui = Instance.new("ScreenGui")
	gui.Name = "SalaLobby"
	gui.ResetOnSpawn = false
	gui.DisplayOrder = 20
	gui.ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = jugador:WaitForChild("PlayerGui")
	local raiz = Instance.new("Frame")
	raiz.BackgroundTransparency = 1
	raiz.Size = UDim2.fromScale(1, 1)
	raiz.Parent = gui
	escala = Instance.new("UIScale")
	escala.Parent = raiz
	local function ajustar()
		local s = Gui.escala(0.55, 1.05)
		escala.Scale = s
		raiz.Size = UDim2.fromScale(1 / s, 1 / s)
	end
	ajustar()
	Workspace.CurrentCamera:GetPropertyChangedSignal("ViewportSize"):Connect(ajustar)

	panel = Gui.panel(raiz, "Papel", UDim2.fromOffset(ANCHO, 300), UDim2.new(1, -14, 0.5, 20), Vector2.new(1, 0.5))
	panel.Visible = false
	aparicion = Instance.new("UIScale")
	aparicion.Parent = panel
	local modal = Instance.new("TextButton")
	modal.BackgroundTransparency = 1
	modal.Text = ""
	modal.Size = UDim2.fromScale(1, 1)
	modal.Modal = true
	modal.Selectable = false
	modal.Parent = panel
	titulo = Gui.texto(panel, "", UDim2.new(1, -226, 0, 40), UDim2.fromOffset(26, 18), Gui.NARANJA, true)
	titulo.TextXAlignment = Enum.TextXAlignment.Left
	local salir = boton(panel, "X", UDim2.fromOffset(48, 48), UDim2.new(1, -18, 0, 14), Gui.ROJO, function()
		enviar("salir")
	end)
	salir.AnchorPoint = Vector2.new(1, 0)
	local invitar = boton(panel, "INVITAR", UDim2.fromOffset(122, 48), UDim2.new(1, -74, 0, 14), Gui.AMARILLO, function()
		task.spawn(function()
			local ok, puede = pcall(SocialService.CanSendGameInviteAsync, SocialService, jugador)
			if ok and puede then
				pcall(SocialService.PromptGameInvite, SocialService, jugador)
			end
		end)
	end)
	invitar.AnchorPoint = Vector2.new(1, 0)
	local m, tm = boton(panel, "", UDim2.new(1, -44, 0, 46), UDim2.fromOffset(22, 66), Gui.TURQUESA, function()
		enviar("modo")
	end)
	botonModo, textoModo = m, tm
	etiquetaModo = Gui.texto(panel, "", UDim2.new(1, -44, 0, 32), UDim2.fromOffset(26, 72), Gui.TURQUESA, true)
	etiquetaModo.TextXAlignment = Enum.TextXAlignment.Left
	lista = Instance.new("Frame")
	lista.BackgroundTransparency = 1
	lista.Size = UDim2.new(1, -44, 1, -210)
	lista.Position = UDim2.fromOffset(22, 122)
	lista.Parent = panel
	Gui.lista(lista, 4)
	local d = boton(panel, "¡DESPEGAR!", UDim2.new(1, -44, 0, 64), UDim2.new(0, 22, 1, -18), Gui.VERDE, function()
		enviar("despegar")
	end)
	d.AnchorPoint = Vector2.new(0, 1)
	botonDespegar = d
	espera = Gui.texto(panel, "", UDim2.new(1, -44, 0, 40), UDim2.new(0, 22, 1, -30), Gui.LAPIZ, true)
	espera.AnchorPoint = Vector2.new(0, 1)
end

function SalaLobby.iniciar()
	construir()
	task.spawn(function()
		local r = ReplicatedStorage:WaitForChild("Remotos"):WaitForChild("Sala", 60)
		if r and r:IsA("RemoteEvent") then
			remoto = r
		end
	end)
	for n = 1, 3 do
		Estado:GetAttributeChangedSignal(`Sala{n}`):Connect(pintar)
	end
	Players.PlayerAdded:Connect(function()
		ultimo = ""
		pintar()
	end)
	pintar()
end

return SalaLobby
