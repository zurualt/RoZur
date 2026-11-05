--!strict
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
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

function Idioma.t(s: string): string
	if actual == "es" or s == "" then
		return s
	end
	local hecho = cache[s]
	if hecho then
		return hecho
	end
	hecho = traducir(s)
	if enCache >= MAX_CACHE then
		table.clear(cache)
		enCache = 0
	end
	cache[s] = hecho
	enCache += 1
	return hecho
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
		t.Text = nuevo
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
			t.Text = nuevo
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
