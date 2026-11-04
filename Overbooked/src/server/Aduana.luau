--!strict
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Carga = require(script.Parent.Carga)
local Sonidos = require(script.Parent.Sonidos)

local Remotos = ReplicatedStorage:WaitForChild("Remotos")
local RemotoAviso = Remotos:WaitForChild("Aviso") :: RemoteEvent

local Aduana = {}

Aduana.BONUS = 60
Aduana.MULTA = 150

local aeropuerto = Workspace:WaitForChild("Aeropuerto") :: Model

local function dentro(zona: BasePart, p: Vector3): boolean
	local local_ = zona.CFrame:PointToObjectSpace(p)
	local m = zona.Size / 2
	return math.abs(local_.X) <= m.X and math.abs(local_.Y) <= m.Y and math.abs(local_.Z) <= m.Z
end

function Aduana.iniciar()
	local carpeta = aeropuerto:WaitForChild("Aduana")
	local cinta = carpeta:WaitForChild("Cinta") :: BasePart
	local tunel = carpeta:WaitForChild("Tunel") :: BasePart
	local contenedor = carpeta:WaitForChild("ZonaContenedor") :: BasePart
	local velocidad = cinta:GetAttribute("Velocidad")
	local mover = cinta.CFrame.LookVector * (if typeof(velocidad) == "number" then velocidad else 7)
	local function activar()
		cinta.AssemblyLinearVelocity = mover
	end
	activar()
	aeropuerto.AncestryChanged:Connect(function()
		if aeropuerto:IsDescendantOf(Workspace) then
			task.defer(activar)
		end
	end)
	task.spawn(function()
		while true do
			task.wait(0.2)
			if not aeropuerto:IsDescendantOf(Workspace) then
				continue
			end
			for _, maleta in Carga.maletas() do
				local p = maleta.Position
				if dentro(tunel, p) then
					local resultado = Carga.escanear(maleta)
					if resultado == true then
						Sonidos.emitir("UiPeligro", p)
						RemotoAviso:FireAllClients("🚨 ¡Contrabando en una maleta! Déjala en el contenedor de aduanas", "peligro")
					elseif resultado == false then
						Sonidos.emitir("Ding", p, 0.2)
					end
				elseif dentro(contenedor, p) and Carga.confiscar(maleta) then
					Sonidos.emitir("Reparado", p)
					RemotoAviso:FireAllClients(`🛃 ¡Contrabando requisado! +{Aduana.BONUS}`, "bien")
				end
			end
		end
	end)
end

return Aduana
