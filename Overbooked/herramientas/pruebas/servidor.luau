local HttpService = game:GetService("HttpService")
local InsertService = game:GetService("InsertService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterPlayer = game:GetService("StarterPlayer")

task.wait(25)

local informe = {}

local function arbol(instancia: Instance, profundidad: number): { any }
	local lista = {}
	for _, hijo in instancia:GetChildren() do
		local nodo: { [string]: any } = { clase = hijo.ClassName, nombre = hijo.Name }
		if profundidad > 0 then
			nodo.hijos = arbol(hijo, profundidad - 1)
		end
		table.insert(lista, nodo)
	end
	return lista
end

local ok, tripulante = pcall(function()
	return InsertService:LoadAsset(87418247604950)
end)
if ok and tripulante then
	local humanoide = tripulante:FindFirstChildWhichIsA("Humanoid", true)
	informe.tripulante = {
		arbol = arbol(tripulante, 3),
		humanoide = humanoide ~= nil,
		raiz = tripulante:FindFirstChild("HumanoidRootPart", true) ~= nil,
		bocaSup = tripulante:FindFirstChild("BocaSup", true) ~= nil,
		bocaInf = tripulante:FindFirstChild("BocaInf", true) ~= nil,
		motores = #(function()
			local m = {}
			for _, d in tripulante:GetDescendants() do
				if d:IsA("Motor6D") then
					table.insert(m, d.Name)
				end
			end
			return m
		end)(),
		altura = if humanoide and humanoide.Parent and humanoide.Parent:IsA("Model") then humanoide.Parent:GetExtentsSize().Y else 0,
	}
else
	informe.tripulante = { error = tostring(tripulante) }
end

local plantilla = StarterPlayer:FindFirstChild("StarterCharacter")
informe.starterCharacter = plantilla ~= nil

local avion = workspace:FindFirstChild("Avion")
if avion then
	informe.cascoCargado = avion:GetAttribute("CascoCargado") == true
	local vestidos, marcadores = 0, 0
	for _, d in avion:GetDescendants() do
		if d:IsA("BasePart") and typeof(d:GetAttribute("Visual")) == "string" then
			marcadores += 1
			if d:FindFirstChildWhichIsA("Model") then
				vestidos += 1
			end
		end
	end
	informe.marcadores = marcadores
	informe.vestidos = vestidos
	informe.faseAvion = avion:GetAttribute("Fase")
end
local estado = ReplicatedStorage:FindFirstChild("Estado")
informe.fasePartida = if estado then estado:GetAttribute("Fase") else nil
informe.contratos = if estado then estado:GetAttribute("Contratos") ~= nil else false

print(HttpService:JSONEncode(informe))
return HttpService:JSONEncode(informe)
