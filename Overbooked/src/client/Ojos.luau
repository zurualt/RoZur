--!strict
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

type Ojo = {
	relativo: CFrame,
	borde: Part,
	blanco: Part,
	pupila: Part,
	p: Vector2,
	v: Vector2,
	antes: Vector3?,
	velAntes: Vector3,
}
type Cara = { cabeza: BasePart, ojos: { Ojo } }

local Ojos = {}

local ALCANCE = 120
local GRAVEDAD = 38
local RADIO = 0.095
local REBOTE = 0.5
local FRENO = 2.6
local CENTRO = Vector3.new(0.226, 1.69, -0.6)
local NORMAL = Vector3.new(0.248, 0.14, -0.958)
local TINTA = Color3.fromRGB(27, 27, 33)
local BLANCO = Color3.fromRGB(247, 247, 242)

local carpeta = Instance.new("Folder")
carpeta.Name = "OjosSaltones"
local caras: { [Model]: Cara } = {}
local partes: { BasePart } = {}
local marcos: { CFrame } = {}

local function pieza(tamano: Vector3, color: Color3): Part
	local p = Instance.new("Part")
	p.Size = tamano
	p.Color = color
	p.Material = Enum.Material.SmoothPlastic
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	local malla = Instance.new("SpecialMesh")
	malla.MeshType = Enum.MeshType.Sphere
	malla.Parent = p
	p.Parent = carpeta
	return p
end

local function motor(personaje: Model, nombre: string): Motor6D?
	local m = personaje:FindFirstChild(nombre, true)
	return if m and m:IsA("Motor6D") then m else nil
end

local function cabezaEnReposo(personaje: Model, cabeza: BasePart, raiz: BasePart): CFrame
	local root, cintura, cuello = motor(personaje, "Root"), motor(personaje, "Waist"), motor(personaje, "Neck")
	if root and cintura and cuello then
		return root.C0 * root.C1:Inverse() * cintura.C0 * cintura.C1:Inverse() * cuello.C0 * cuello.C1:Inverse()
	end
	return raiz.CFrame:ToObjectSpace(cabeza.CFrame)
end

local function crear(personaje: Model): Cara?
	local cabeza = personaje:FindFirstChild("Head")
	local raiz = personaje:FindFirstChild("HumanoidRootPart")
	if not cabeza or not cabeza:IsA("BasePart") or not raiz or not raiz:IsA("BasePart") then
		return nil
	end
	local reposo = cabezaEnReposo(personaje, cabeza, raiz)
	local ojos: { Ojo } = {}
	for _, signo in { -1, 1 } do
		local centro = Vector3.new(CENTRO.X * signo, CENTRO.Y, CENTRO.Z)
		local normal = Vector3.new(NORMAL.X * signo, NORMAL.Y, NORMAL.Z).Unit
		local enRaiz = CFrame.lookAt(centro, centro + normal)
		table.insert(ojos, {
			relativo = reposo:Inverse() * enRaiz,
			borde = pieza(Vector3.new(0.42, 0.42, 0.08), TINTA),
			blanco = pieza(Vector3.new(0.37, 0.37, 0.13), BLANCO),
			pupila = pieza(Vector3.new(0.16, 0.16, 0.05), TINTA),
			p = Vector2.new(0, -RADIO),
			v = Vector2.zero,
			antes = nil,
			velAntes = Vector3.zero,
		})
	end
	local cara = { cabeza = cabeza, ojos = ojos }
	caras[personaje] = cara
	return cara
end

local function quitar(personaje: Model)
	local cara = caras[personaje]
	if cara then
		for _, o in cara.ojos do
			o.borde:Destroy()
			o.blanco:Destroy()
			o.pupila:Destroy()
		end
		caras[personaje] = nil
	end
end

local function fisica(o: Ojo, marco: CFrame, dt: number)
	local pos = marco.Position
	local antes = o.antes
	local acel = Vector3.zero
	if antes then
		local vel = (pos - antes) / dt
		acel = (vel - o.velAntes) / dt
		if acel.Magnitude > 400 then
			acel = acel.Unit * 400
		end
		o.velAntes = if vel.Magnitude < 200 then vel else Vector3.zero
	end
	o.antes = pos
	local relativa = Vector3.new(0, -GRAVEDAD, 0) - acel
	local empuje = Vector2.new(relativa:Dot(marco.RightVector), relativa:Dot(marco.UpVector))
	o.v = (o.v + empuje * dt) * math.exp(-FRENO * dt)
	o.p += o.v * dt
	local largo = o.p.Magnitude
	if largo > RADIO then
		local dir = o.p / largo
		o.p = dir * RADIO
		local hacia = o.v:Dot(dir)
		if hacia > 0 then
			o.v -= dir * hacia * (1 + REBOTE)
		end
	end
end

local function actualizar(dt: number)
	dt = math.clamp(dt, 1 / 240, 0.1)
	local foco = Workspace.CurrentCamera.CFrame.Position
	local vistos: { [Model]: boolean } = {}
	for _, otro in Players:GetPlayers() do
		local personaje = otro.Character
		local cabeza = personaje and personaje:FindFirstChild("Head")
		if personaje and cabeza and cabeza:IsA("BasePart") and (cabeza.Position - foco).Magnitude < ALCANCE then
			vistos[personaje] = true
		end
	end
	for personaje in caras do
		if not vistos[personaje] or not caras[personaje].cabeza.Parent then
			quitar(personaje)
		end
	end
	table.clear(partes)
	table.clear(marcos)
	for personaje in vistos do
		local cara = caras[personaje] or crear(personaje)
		if not cara then
			continue
		end
		local oculto = cara.cabeza.LocalTransparencyModifier > 0.5 or cara.cabeza.Transparency > 0.5
		for _, o in cara.ojos do
			local marco = cara.cabeza.CFrame * o.relativo
			fisica(o, marco, dt)
			local t = if oculto then 1 else 0
			if o.blanco.Transparency ~= t then
				o.borde.Transparency = t
				o.blanco.Transparency = t
				o.pupila.Transparency = t
			end
			table.insert(partes, o.borde)
			table.insert(marcos, marco * CFrame.new(0, 0, -0.07))
			table.insert(partes, o.blanco)
			table.insert(marcos, marco * CFrame.new(0, 0, -0.1))
			table.insert(partes, o.pupila)
			table.insert(marcos, marco * CFrame.new(o.p.X, o.p.Y, -0.165))
		end
	end
	if #partes > 0 then
		Workspace:BulkMoveTo(partes, marcos, Enum.BulkMoveMode.FireCFrameChanged)
	end
end

function Ojos.iniciar()
	carpeta.Parent = Workspace
	RunService.PreRender:Connect(actualizar)
end

return Ojos
