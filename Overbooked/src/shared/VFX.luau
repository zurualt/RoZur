--!strict
local VFX = {}

local TEX_FUEGO = "rbxasset://textures/particles/fire_main.dds"
local TEX_HUMO = "rbxasset://textures/particles/smoke_main.dds"
local TEX_CHISPA = "rbxasset://textures/particles/sparkles_main.dds"

local function emisor(padre: Instance, nombre: string, textura: string): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Name = nombre
	e.Texture = textura
	e.LightEmission = 0
	e.Parent = padre
	return e
end

function VFX.fuego(padre: Instance, escala: number): { ParticleEmitter }
	local llama = emisor(padre, "Llama", TEX_FUEGO)
	llama.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 236, 140)),
		ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 140, 40)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 50, 20)),
	})
	llama.LightEmission = 0.9
	llama.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1.6 * escala),
		NumberSequenceKeypoint.new(1, 0.2 * escala),
	})
	llama.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.1),
		NumberSequenceKeypoint.new(1, 1),
	})
	llama.Lifetime = NumberRange.new(0.5, 0.9)
	llama.Rate = 40
	llama.Speed = NumberRange.new(3 * escala, 6 * escala)
	llama.SpreadAngle = Vector2.new(18, 18)
	llama.Acceleration = Vector3.new(0, 6, 0)
	local humo = emisor(padre, "Humo", TEX_HUMO)
	humo.Color = ColorSequence.new(Color3.fromRGB(70, 70, 75), Color3.fromRGB(30, 30, 32))
	humo.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1.2 * escala),
		NumberSequenceKeypoint.new(1, 4 * escala),
	})
	humo.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.35),
		NumberSequenceKeypoint.new(1, 1),
	})
	humo.Lifetime = NumberRange.new(1.4, 2.2)
	humo.Rate = 10
	humo.Speed = NumberRange.new(4, 7)
	humo.Acceleration = Vector3.new(0, 3, 0)
	humo.RotSpeed = NumberRange.new(-40, 40)
	return { llama, humo }
end

function VFX.rocio(padre: Instance): ParticleEmitter
	local e = emisor(padre, "Rocio", TEX_HUMO)
	e.Color = ColorSequence.new(Color3.fromRGB(245, 248, 255))
	e.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.4),
		NumberSequenceKeypoint.new(1, 3.2),
	})
	e.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.2),
		NumberSequenceKeypoint.new(1, 1),
	})
	e.Lifetime = NumberRange.new(0.5, 0.8)
	e.Rate = 90
	e.Speed = NumberRange.new(22, 30)
	e.SpreadAngle = Vector2.new(8, 8)
	e.EmissionDirection = Enum.NormalId.Front
	e.Enabled = false
	return e
end

function VFX.chispas(padre: Instance): ParticleEmitter
	local e = emisor(padre, "Chispas", TEX_CHISPA)
	e.Color = ColorSequence.new(Color3.fromRGB(255, 220, 120))
	e.LightEmission = 1
	e.Size = NumberSequence.new(0.25, 0)
	e.Lifetime = NumberRange.new(0.25, 0.5)
	e.Rate = 0
	e.Speed = NumberRange.new(12, 22)
	e.SpreadAngle = Vector2.new(60, 60)
	e.Acceleration = Vector3.new(0, -40, 0)
	return e
end

function VFX.plumas(padre: Instance): ParticleEmitter
	local e = emisor(padre, "Plumas", TEX_HUMO)
	e.Color = ColorSequence.new(Color3.fromRGB(250, 250, 250))
	e.Size = NumberSequence.new(0.6, 0.3)
	e.Lifetime = NumberRange.new(1.5, 2.5)
	e.Rate = 0
	e.Speed = NumberRange.new(6, 14)
	e.SpreadAngle = Vector2.new(180, 180)
	e.RotSpeed = NumberRange.new(-200, 200)
	e.Acceleration = Vector3.new(0, -4, 25)
	return e
end

function VFX.viento(padre: Instance): ParticleEmitter
	local e = emisor(padre, "Viento", TEX_HUMO)
	e.Color = ColorSequence.new(Color3.fromRGB(230, 240, 255))
	e.Size = NumberSequence.new(0.5, 0.1)
	e.Transparency = NumberSequence.new(0.6, 1)
	e.Lifetime = NumberRange.new(0.4, 0.7)
	e.Rate = 50
	e.Speed = NumberRange.new(30, 45)
	e.SpreadAngle = Vector2.new(25, 25)
	e.EmissionDirection = Enum.NormalId.Front
	return e
end

return VFX
