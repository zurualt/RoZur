--!strict
local ImagenesVfx = require(script.Parent.ImagenesVfx)

local VFX = {}

function VFX.textura(nombre: string): string
	return `rbxassetid://{ImagenesVfx[nombre] or 0}`
end

local function emisor(padre: Instance, nombre: string, textura: string, girar: boolean?): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Name = nombre
	e.Texture = VFX.textura(textura)
	e.LightEmission = 0
	if girar then
		e.Rotation = NumberRange.new(0, 360)
	end
	e.Parent = padre
	return e
end

function VFX.fuego(padre: Instance, escala: number): { ParticleEmitter }
	local llama = emisor(padre, "Llama", "Llama")
	llama.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 255, 255)),
		ColorSequenceKeypoint.new(0.6, Color3.fromRGB(255, 214, 170)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(230, 130, 90)),
	})
	llama.LightEmission = 0.35
	llama.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1.7 * escala),
		NumberSequenceKeypoint.new(1, 0.3 * escala),
	})
	llama.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(0.7, 0.1),
		NumberSequenceKeypoint.new(1, 1),
	})
	llama.Rotation = NumberRange.new(-12, 12)
	llama.RotSpeed = NumberRange.new(-30, 30)
	llama.Lifetime = NumberRange.new(0.45, 0.8)
	llama.Rate = 34
	llama.Speed = NumberRange.new(3 * escala, 6 * escala)
	llama.SpreadAngle = Vector2.new(16, 16)
	llama.Acceleration = Vector3.new(0, 6, 0)
	local humo = emisor(padre, "Humo", "Humo1", true)
	humo.Color = ColorSequence.new(Color3.fromRGB(120, 116, 112), Color3.fromRGB(60, 58, 56))
	humo.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1.2 * escala),
		NumberSequenceKeypoint.new(1, 4.2 * escala),
	})
	humo.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.15),
		NumberSequenceKeypoint.new(1, 1),
	})
	humo.Lifetime = NumberRange.new(1.4, 2.2)
	humo.Rate = 9
	humo.Speed = NumberRange.new(4, 7)
	humo.Acceleration = Vector3.new(0, 3, 0)
	humo.RotSpeed = NumberRange.new(-40, 40)
	return { llama, humo }
end

function VFX.rocio(padre: Instance): ParticleEmitter
	local e = emisor(padre, "Rocio", "Humo2", true)
	e.Color = ColorSequence.new(Color3.fromRGB(245, 248, 255))
	e.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.4),
		NumberSequenceKeypoint.new(1, 3.2),
	})
	e.Transparency = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.1),
		NumberSequenceKeypoint.new(1, 1),
	})
	e.Lifetime = NumberRange.new(0.5, 0.8)
	e.Rate = 70
	e.RotSpeed = NumberRange.new(-90, 90)
	e.Speed = NumberRange.new(22, 30)
	e.SpreadAngle = Vector2.new(8, 8)
	e.EmissionDirection = Enum.NormalId.Front
	e.Enabled = false
	return e
end

function VFX.chispas(padre: Instance): ParticleEmitter
	local e = emisor(padre, "Chispas", "Chispa", true)
	e.Color = ColorSequence.new(Color3.fromRGB(255, 220, 120))
	e.LightEmission = 1
	e.Size = NumberSequence.new(0.5, 0)
	e.Lifetime = NumberRange.new(0.25, 0.5)
	e.Rate = 0
	e.RotSpeed = NumberRange.new(-180, 180)
	e.Speed = NumberRange.new(12, 22)
	e.SpreadAngle = Vector2.new(60, 60)
	e.Acceleration = Vector3.new(0, -40, 0)
	return e
end

function VFX.plumas(padre: Instance): ParticleEmitter
	local e = emisor(padre, "Plumas", "Pluma", true)
	e.Color = ColorSequence.new(Color3.fromRGB(250, 250, 250))
	e.Size = NumberSequence.new(0.9, 0.6)
	e.Lifetime = NumberRange.new(1.5, 2.5)
	e.Rate = 0
	e.Speed = NumberRange.new(6, 14)
	e.SpreadAngle = Vector2.new(180, 180)
	e.RotSpeed = NumberRange.new(-200, 200)
	e.Drag = 1.5
	e.Acceleration = Vector3.new(0, -4, 25)
	return e
end

function VFX.viento(padre: Instance): ParticleEmitter
	local e = emisor(padre, "Viento", "Linea")
	e.Color = ColorSequence.new(Color3.fromRGB(230, 240, 255))
	e.Size = NumberSequence.new(1.1, 0.3)
	e.Transparency = NumberSequence.new(0.45, 1)
	e.Orientation = Enum.ParticleOrientation.VelocityParallel
	e.Lifetime = NumberRange.new(0.3, 0.55)
	e.Rate = 50
	e.Speed = NumberRange.new(30, 45)
	e.SpreadAngle = Vector2.new(25, 25)
	e.EmissionDirection = Enum.NormalId.Front
	return e
end

function VFX.salpicadura(padre: Instance, color: Color3): ParticleEmitter
	local e = emisor(padre, "Salpicadura", "Gota")
	e.Color = ColorSequence.new(color)
	e.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0.5),
		NumberSequenceKeypoint.new(1, 0.15),
	})
	e.Transparency = NumberSequence.new(0, 1)
	e.Orientation = Enum.ParticleOrientation.VelocityParallel
	e.Lifetime = NumberRange.new(0.35, 0.7)
	e.Rate = 0
	e.Speed = NumberRange.new(8, 16)
	e.SpreadAngle = Vector2.new(70, 70)
	e.Acceleration = Vector3.new(0, -50, 0)
	e.EmissionDirection = Enum.NormalId.Top
	return e
end

function VFX.vapor(padre: Instance): ParticleEmitter
	local e = emisor(padre, "Vapor", "Vapor", true)
	e.Color = ColorSequence.new(Color3.fromRGB(240, 242, 246))
	e.Size = NumberSequence.new(1.2, 4)
	e.Transparency = NumberSequence.new(0.15, 1)
	e.Lifetime = NumberRange.new(1, 1.8)
	e.Rate = 0
	e.RotSpeed = NumberRange.new(-40, 40)
	e.Speed = NumberRange.new(3, 7)
	e.SpreadAngle = Vector2.new(40, 40)
	e.Acceleration = Vector3.new(0, 4, 0)
	e.EmissionDirection = Enum.NormalId.Top
	return e
end

return VFX
