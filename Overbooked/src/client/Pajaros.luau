--!strict
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Criaturas = require(ReplicatedStorage.Shared.Criaturas)
local Rafagas = require(script.Parent.Rafagas)
local Sonido = require(script.Parent.Sonido)

type Ave = { pos: Vector3, vel: Vector3, fase: number, ritmo: number, susto: boolean, vuelta: number }

local Pajaros = {}

local CUANTOS = 40
local NARIZ = Vector3.new(0, 104, -66)
local PARABRISAS = CFrame.new(0.6, 105.3, -66) * CFrame.Angles(math.rad(6), 0, 0)
local ALA_IZQ = Criaturas.ALA
local ALA_DER = Vector3.new(-ALA_IZQ.X, ALA_IZQ.Y, ALA_IZQ.Z)
local NOMBRES = { "Pajaro", "AlaPajaroIzq", "AlaPajaroDer" }
local BLANCO = Color3.new(1, 1, 1)
local ROSA = Color3.fromRGB(242, 138, 160)

local avion = Workspace:WaitForChild("Avion") :: Model
local rng = Random.new()

local function animar(partes: { BasePart }, marcos: { CFrame }, duracion: number, f: (number) -> CFrame?, alFinal: () -> ())
	local destino = table.clone(marcos)
	local inicio = os.clock()
	local conexion: RBXScriptConnection
	conexion = RunService.PreRender:Connect(function()
		local t = os.clock() - inicio
		local cf = if t < duracion then f(t) else nil
		if not cf then
			conexion:Disconnect()
			alFinal()
			return
		end
		for i, m in marcos do
			destino[i] = cf * m
		end
		Workspace:BulkMoveTo(partes, destino, Enum.BulkMoveMode.FireCFrameChanged)
	end)
end

function Pajaros.bandada()
	local carpeta = Instance.new("Folder")
	carpeta.Name = "Bandada"
	carpeta.Parent = Workspace
	local aves: { Ave } = {}
	local partes: { BasePart } = {}
	local marcos: { CFrame } = {}
	local dueno: { number } = {}
	for i = 1, CUANTOS do
		table.insert(aves, {
			pos = Vector3.new(rng:NextNumber(-60, 60), 100 + rng:NextNumber(-10, 22), rng:NextNumber(-520, -160)),
			vel = Vector3.new(rng:NextNumber(-6, 6), rng:NextNumber(-2, 2), rng:NextNumber(150, 230)),
			fase = rng:NextNumber(0, 6),
			ritmo = rng:NextNumber(10, 14),
			susto = false,
			vuelta = 0,
		})
		for g, nombre in NOMBRES do
			local modelo, ps, ms = Criaturas.clonar(nombre)
			if modelo then
				modelo.Parent = carpeta
				for k, p in ps do
					table.insert(partes, p)
					table.insert(marcos, ms[k])
					table.insert(dueno, i * 3 - 3 + g)
				end
			elseif g == 1 then
				local p = Instance.new("WedgePart")
				p.Size = Vector3.new(1.6, 0.3, 1)
				p.Color = Color3.fromRGB(40, 40, 46)
				p.Anchored = true
				p.CanCollide = false
				p.CanQuery = false
				p.CanTouch = false
				p.CastShadow = false
				p.Parent = carpeta
				table.insert(partes, p)
				table.insert(marcos, CFrame.identity)
				table.insert(dueno, i * 3 - 2)
			end
		end
	end
	local cfs: { CFrame } = table.create(CUANTOS * 3, CFrame.identity)
	local destino = table.clone(marcos)
	local inicio = os.clock()
	local conexion: RBXScriptConnection
	conexion = RunService.PreRender:Connect(function(dt: number)
		local t = os.clock() - inicio
		local foco = Workspace.CurrentCamera.CFrame.Position
		for i, b in aves do
			if not b.susto and (b.pos - NARIZ).Magnitude < 75 then
				b.susto = true
				b.vel += Vector3.new((if b.pos.X < 0 then -1 else 1) * rng:NextNumber(25, 55), rng:NextNumber(-20, 35), 0)
				b.ritmo *= 2.2
				if rng:NextNumber() < 0.25 and (b.pos - foco).Magnitude < 70 then
					Rafagas.lanzar("Plumas", b.pos, 0.5)
				end
			end
			if b.susto and i % 3 == 0 then
				b.vuelta += dt * 10
			end
			b.pos += b.vel * dt
			local aleteo = math.sin(t * b.ritmo + b.fase)
			local a = aleteo * (if b.susto then 1.15 else 0.75)
			local base = CFrame.lookAt(b.pos, b.pos + b.vel)
				* CFrame.new(0, -aleteo * 0.25, 0)
				* CFrame.Angles(math.sin(t * 3 + b.fase) * 0.15, 0, math.sin(t * 2 + b.fase) * 0.25 + b.vuelta)
			cfs[i * 3 - 2] = base
			cfs[i * 3 - 1] = base * CFrame.new(ALA_IZQ) * CFrame.Angles(0, 0, -a)
			cfs[i * 3] = base * CFrame.new(ALA_DER) * CFrame.Angles(0, 0, a)
		end
		for k, m in marcos do
			destino[k] = cfs[dueno[k]] * m
		end
		Workspace:BulkMoveTo(partes, destino, Enum.BulkMoveMode.FireCFrameChanged)
		if t > 4.5 then
			conexion:Disconnect()
			carpeta:Destroy()
		end
	end)
end

local function mareado(origen: Vector3, sx: number)
	local modelo, partes, marcos = Criaturas.clonar("PajaroMareado")
	if not modelo then
		return
	end
	local p1 = origen + Vector3.new(-sx * 2, 10, -12)
	local p2 = Vector3.new(sx * 12.2, 105, -14)
	local p3 = Vector3.new(sx * 12, 103, 30)
	local proxima = 0
	animar(partes, marcos, 2.8, function(t)
		local u = t / 2.8
		local a, b, c = origen:Lerp(p1, u), p1:Lerp(p2, u), p2:Lerp(p3, u)
		local pos = a:Lerp(b, u):Lerp(b:Lerp(c, u), u)
		if os.clock() > proxima then
			proxima = os.clock() + 0.45
			Rafagas.lanzar("Estrellas", pos + Vector3.new(0, 2.2, 0), 0.6)
		end
		return CFrame.new(pos) * CFrame.Angles(u * 11, u * 7 * sx, u * 15)
	end, function()
		modelo:Destroy()
	end)
	modelo.Parent = Workspace
	Sonido.reproducir("Mareo", partes[1], 1)
	Rafagas.lanzar("Plumas", origen, 1.2)
end

local function plaf()
	local modelo, partes, marcos = Criaturas.clonar("PajaroPlaf", 0.85)
	if not modelo then
		return
	end
	local tamanos = table.create(#partes, Vector3.zero)
	for i, p in partes do
		tamanos[i] = p.Size
	end
	local pegado = false
	local function inflar(k: number)
		for i, p in partes do
			p.Size = tamanos[i] * k
		end
	end
	animar(partes, marcos, 2.6, function(t)
		if t < 0.14 then
			return PARABRISAS * CFrame.new(0, 0, -(1 - t / 0.14) * 30)
		elseif t < 1.9 then
			local k = t - 0.14
			if not pegado then
				pegado = true
				Rafagas.palabra(PARABRISAS * Vector3.new(0, 2.4, 1.5), "¡PLAF!", BLANCO, ROSA, 1.1, true)
				Rafagas.lanzar("Plumas", PARABRISAS.Position, 0.8)
				Sonido.reproducir("Bonk", PARABRISAS.Position, 1)
				Sonido.reproducir("Pajaros", PARABRISAS.Position, 0.8, 1.3)
			end
			if k < 0.7 then
				inflar(1 + 0.22 * math.exp(-k * 7) * math.cos(k * 30))
			end
			return PARABRISAS * CFrame.new(0, -k * 0.3, 0)
		end
		local k = (t - 1.9) / 0.7
		return PARABRISAS * CFrame.new(0, -0.53 + k * 6, -k * k * 14) * CFrame.Angles(-k * 2.5, 0, k * 1.5)
	end, function()
		modelo:Destroy()
	end)
	modelo.Parent = Workspace
end

function Pajaros.choque()
	local izq = avion:GetAttribute("MotorIzqFuego") == true
	local der = avion:GetAttribute("MotorDerFuego") == true
	local lado = if izq and not der then "Izq" elseif der and not izq then "Der" elseif rng:NextNumber() < 0.5 then "Izq" else "Der"
	local sx = if lado == "Izq" then -1 else 1
	local exterior = avion:FindFirstChild("Exterior")
	local parte = exterior and exterior:FindFirstChild("Motor" .. lado)
	local motor = if parte and parte:IsA("BasePart") then parte.Position else Vector3.new(sx * 18, 95.6, -24)
	mareado(motor + Vector3.new(0, 0, -4.8), sx)
	task.delay(0.35, plaf)
end

return Pajaros
