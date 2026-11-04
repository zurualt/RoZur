--!strict
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Config = require(ReplicatedStorage.Shared.Config)
local VFX = require(ReplicatedStorage.Shared.VFX)
local Activos = require(script.Parent.Activos)
local Agarre = require(script.Parent.Agarre)

type Soporte = {
	parte: BasePart,
	tipo: string,
	objeto: BasePart?,
	vacioDesde: number,
}

local Objetos = {}

local avion = Workspace:WaitForChild("Avion") :: Model
local carpeta = avion:WaitForChild("Objetos") :: Folder
local soportes: { Soporte } = {}
local orden: { BasePart } = {}
local esperas: { [Player]: number } = {}
local alPerder: { (BasePart) -> () } = {}

function Objetos.servidor(parte: BasePart)
	if parte.Anchored or not parte:IsDescendantOf(Workspace) then
		return
	end
	pcall(function()
		if parte:GetNetworkOwner() ~= nil then
			parte:SetNetworkOwner(nil)
		end
	end)
end

function Objetos.crear(tipo: string, cframe: CFrame, padre: Instance?, visual: string?): BasePart
	local def = Config.OBJETOS[tipo]
	local parte = Instance.new("Part")
	parte.Name = tipo
	parte.Size = def.tamano
	parte.Color = def.color
	parte.Material = def.material
	parte.TopSurface = Enum.SurfaceType.Smooth
	parte.BottomSurface = Enum.SurfaceType.Smooth
	parte.CustomPhysicalProperties = PhysicalProperties.new(def.densidad, 0.6, 0.15)
	parte.CFrame = cframe
	parte:SetAttribute("Tipo", tipo)
	parte:SetAttribute("Portador", 0)
	CollectionService:AddTag(parte, "Agarrable")
	CollectionService:AddTag(parte, "Objeto")
	if tipo == "Extintor" then
		local boquilla = Instance.new("Attachment")
		boquilla.Name = "Boquilla"
		boquilla.Position = Vector3.new(0, def.tamano.Y * 0.3, -def.tamano.Z / 2)
		boquilla.Parent = parte
		VFX.rocio(boquilla)
	end
	parte.Parent = padre or carpeta
	Objetos.servidor(parte)
	local v = visual or def.visual
	if v then
		Activos.vestirDinamico(parte, v)
	end
	if not padre then
		table.insert(orden, parte)
		while #orden > Config.PARTIDA.MAX_OBJETOS do
			local viejo = table.remove(orden, 1)
			if viejo and viejo.Parent and not Agarre.portador(viejo) then
				viejo:Destroy()
			end
		end
	end
	return parte
end

function Objetos.alPerder(f: (BasePart) -> ())
	table.insert(alPerder, f)
end

function Objetos.sueltos(): { BasePart }
	local lista: { BasePart } = {}
	for _, hijo in carpeta:GetChildren() do
		if hijo:IsA("BasePart") and not hijo.Anchored and not Agarre.portador(hijo) and Agarre.delServidor(hijo) then
			table.insert(lista, hijo)
		end
	end
	return lista
end

local function reponer(soporte: Soporte)
	local cf = soporte.parte.CFrame * CFrame.new(0, soporte.parte.Size.Y / 2 + Config.OBJETOS[soporte.tipo].tamano.Y / 2 + 0.05, 0)
	soporte.objeto = Objetos.crear(soporte.tipo, cf)
end

local function prepararDispensador(parte: BasePart, tipo: string)
	local def = Config.OBJETOS[tipo]
	local aviso = Instance.new("ProximityPrompt")
	aviso.ActionText = "Coger"
	aviso.ObjectText = def.nombre
	aviso.KeyboardKeyCode = Enum.KeyCode.E
	aviso.MaxActivationDistance = 8
	aviso.RequiresLineOfSight = false
	aviso.Parent = parte
	aviso.Triggered:Connect(function(jugador)
		local ahora = os.clock()
		if (esperas[jugador] or 0) > ahora or Agarre.sostenido(jugador) then
			return
		end
		esperas[jugador] = ahora + 0.6
		local cf = parte.CFrame * CFrame.new(0, parte.Size.Y / 2 + def.tamano.Y / 2 + 0.3, 0)
		Agarre.forzar(jugador, Objetos.crear(tipo, cf))
	end)
end

function Objetos.limpiar()
	for _, hijo in carpeta:GetChildren() do
		hijo:Destroy()
	end
	table.clear(orden)
	for _, soporte in soportes do
		reponer(soporte)
	end
end

function Objetos.iniciar()
	for _, d in avion:GetDescendants() do
		if d:IsA("BasePart") then
			local tipo = d:GetAttribute("Tipo")
			if typeof(tipo) == "string" and Config.OBJETOS[tipo] then
				if string.find(d.Name, "^Dispensador") then
					prepararDispensador(d, tipo)
				elseif string.find(d.Name, "^Soporte") then
					local soporte: Soporte = { parte = d, tipo = tipo, objeto = nil, vacioDesde = 0 }
					table.insert(soportes, soporte)
					reponer(soporte)
				end
			end
			local visual = d:GetAttribute("Visual")
			if typeof(visual) == "string" then
				local base = d:GetAttribute("Base")
				Activos.vestirFijo(d, visual, if typeof(base) == "number" then base else nil)
			end
		end
	end
	Activos.vestirAvion(avion)
	Players.PlayerRemoving:Connect(function(jugador)
		esperas[jugador] = nil
	end)

	task.spawn(function()
		while true do
			task.wait(1)
			local ahora = os.clock()
			for _, hijo in carpeta:GetChildren() do
				if hijo:IsA("BasePart") and hijo.Position.Y < Config.CAIDA_Y then
					for _, f in alPerder do
						task.spawn(f, hijo)
					end
					Agarre.soltarObjeto(hijo)
					hijo:Destroy()
				end
			end
			for _, soporte in soportes do
				local objeto = soporte.objeto
				if objeto and objeto.Parent then
					soporte.vacioDesde = 0
				else
					if soporte.vacioDesde == 0 then
						soporte.vacioDesde = ahora
					elseif ahora - soporte.vacioDesde > 12 then
						soporte.vacioDesde = 0
						reponer(soporte)
					end
				end
			end
		end
	end)
end

return Objetos
