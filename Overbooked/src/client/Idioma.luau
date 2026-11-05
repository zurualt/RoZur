--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Textos = require(ReplicatedStorage.Shared.Textos)

type Plantilla = { patron: string, posicion: { [number]: number }, entrada: Textos.Entrada, peso: number }
type ConTexto = TextLabel | TextButton

local Idioma = {}

Idioma.IDIOMAS = {
	{ codigo = "en", nombre = "English" },
	{ codigo = "es", nombre = "Español" },
	{ codigo = "pt", nombre = "Português" },
	{ codigo = "fr", nombre = "Français" },
}

local ATRIBUTO = "TextoOriginal"
local MAX_CACHE = 3000
local TACTIL: { [string]: string } = {
	["<b>Clic</b> coger / soltar · <b>Clic der.</b> lanzar"] = "<b>Coger</b> coger y soltar · <b>Lanzar</b> lanzar",
	["<b>F</b> usar extintor, llave o agua"] = "<b>Usar</b> (mantén) extintor, llave o agua",
	["<b>E</b> servir, coger comida y pulsar botones"] = "Toca las etiquetas para servir, coger comida y pulsar botones",
	["<b>G</b> sentarte · <b>T</b> abrir o cerrar altillos"] = "Toca la etiqueta para sentarte o abrir altillos",
	["<b>R</b> (mantener) calmar a un pasajero"] = "Mantén la etiqueta para calmar a un pasajero",
	["<b>Clic der.</b> con las manos vacías: ¡bofetada!"] = "<b>Bofetada</b> con las manos vacías",
	["Piloto: asiento izquierdo · Shift acelera · W sube"] = "Piloto: asiento izquierdo, Gas+ acelera y el joystick sube",
	["H para cerrar"] = "Toca para cerrar",
	["W/S subir y bajar · A/D girar · Shift/Ctrl gases · Espacio salir"] = "Joystick: subir, bajar y girar · Gas+ y Gas- · salta para salir",
	["Sirve a un pasajero (E o lánzasela)"] = "Sirve a un pasajero (etiqueta o lánzasela)",
}
local tactil = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled

local evento = Instance.new("BindableEvent")
Idioma.cambiado = evento.Event

local actual = "en"
local iniciado = false
local plantillas: { Plantilla } = {}
local cache: { [string]: string } = {}
local enCache = 0
local escritos: { [Instance]: string } = setmetatable({}, { __mode = "k" }) :: any
local vigilados: { [ConTexto]: boolean } = setmetatable({}, { __mode = "k" }) :: any

for clave, entrada in Textos do
	if not string.find(clave, "{%d+}") then
		continue
	end
	local posicion = {}
	local capturas = 0
	local escapada = string.gsub(clave, "[%^%$%(%)%%%.%[%]%*%+%-%?]", "%%%0")
	local patron = string.gsub(escapada, "{(%d+)}", function(n: string): string
		capturas += 1
		posicion[tonumber(n) :: number] = capturas
		return "(.-)"
	end)
	local literal = string.gsub(clave, "{%d+}", "")
	table.insert(plantillas, { patron = `^{patron}$`, posicion = posicion, entrada = entrada, peso = #literal })
end
table.sort(plantillas, function(a, b)
	return a.peso > b.peso
end)

local function elegir(e: Textos.Entrada): string
	return if actual == "pt" then e.pt elseif actual == "fr" then e.fr else e.en
end

local traducir: (string) -> string

local function unir(s: string, separador: string): string
	local partes = string.split(s, separador)
	for i, parte in partes do
		partes[i] = traducir(parte)
	end
	return table.concat(partes, separador)
end

traducir = function(s: string): string
	local e = Textos[s]
	if e then
		return elegir(e)
	end
	if string.find(s, "\n", 1, true) then
		return unir(s, "\n")
	end
	for _, p in plantillas do
		local capturas: { string } = { string.match(s, p.patron) } :: any
		if #capturas > 0 then
			return (string.gsub(elegir(p.entrada), "{(%d+)}", function(n: string): string
				local i = p.posicion[tonumber(n) :: number]
				return if i then traducir(capturas[i]) else ""
			end))
		end
	end
	if string.find(s, " · ", 1, true) then
		return unir(s, " · ")
	end
	local abre, dentro, cierra = string.match(s, "^(<[^>]+>)(.-)(</[^>]+>)$")
	if abre and dentro and cierra then
		return abre .. traducir(dentro) .. cierra
	end
	local cifra, resto = string.match(s, "^([%-+]?[%d.,]+) (.+)$")
	if cifra and resto then
		return `{cifra} {traducir(resto)}`
	end
	return s
end

local function quitarTeclas(s: string): string
	return (string.gsub(s, " %(([%w/]+)%)", function(k: string): string
		if string.match(k, "^%u$") or k == "Shift" or k == "Ctrl" or k == "Shift/Ctrl" then
			return ""
		end
		return ` ({k})`
	end))
end

function Idioma.tactil(): boolean
	return tactil
end

function Idioma.t(s: string): string
	if s == "" or (actual == "es" and not tactil) then
		return s
	end
	local hecho = cache[s]
	if hecho then
		return hecho
	end
	local base = if tactil then TACTIL[s] or s else s
	local convertido = if actual == "es" then base else traducir(base)
	if tactil then
		convertido = quitarTeclas(convertido)
	end
	if enCache >= MAX_CACHE then
		table.clear(cache)
		enCache = 0
	end
	cache[s] = convertido
	enCache += 1
	return convertido
end

function Idioma.actual(): string
	return actual
end

local function aplicar(t: ConTexto)
	local texto = t.Text
	if escritos[t] == texto then
		return
	end
	t:SetAttribute(ATRIBUTO, texto)
	local nuevo = Idioma.t(texto)
	escritos[t] = nuevo
	if nuevo ~= texto then
		local destino: any = t
		destino.Text = nuevo
	end
end

local function vigilar(d: Instance)
	if d:IsA("TextLabel") or d:IsA("TextButton") then
		if vigilados[d] then
			return
		end
		vigilados[d] = true
		d:GetPropertyChangedSignal("Text"):Connect(function()
			aplicar(d)
		end)
		aplicar(d)
	end
end

function Idioma.cambiar(codigo: string)
	if codigo == actual then
		return
	end
	local valido = false
	for _, i in Idioma.IDIOMAS do
		valido = valido or i.codigo == codigo
	end
	if not valido then
		return
	end
	actual = codigo
	table.clear(cache)
	enCache = 0
	for t in vigilados do
		local texto = t.Text
		local original = if texto ~= escritos[t] then texto else t:GetAttribute(ATRIBUTO)
		if typeof(original) == "string" then
			t:SetAttribute(ATRIBUTO, original)
			local nuevo = Idioma.t(original)
			escritos[t] = nuevo
			local destino: any = t
			destino.Text = nuevo
		end
	end
	evento:Fire(codigo)
end

function Idioma.iniciar()
	if iniciado then
		return
	end
	iniciado = true
	for _, raiz in { Players.LocalPlayer:WaitForChild("PlayerGui"), Workspace } :: { Instance } do
		for _, d in raiz:GetDescendants() do
			vigilar(d)
		end
		raiz.DescendantAdded:Connect(vigilar)
	end
end

return Idioma
