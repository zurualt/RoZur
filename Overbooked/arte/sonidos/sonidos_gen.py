#!/usr/bin/env python3
import os, sys, json, subprocess
import numpy as np

SR = 44100
TAU = 2*np.pi
DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG = "/usr/bin/ffmpeg"


def ns(d): return max(1, int(round(d*SR)))
def nl(d): return int(round(d*SR/1024))*1024
def tt(n, t0=0.0): return np.arange(n)/SR - t0
def R(s): return np.random.default_rng(s)
def m2f(m): return 440.0*2**((m-69)/12)
def dbg(x): return 10**(x/20)
def db(x): return 20*np.log10(max(float(x), 1e-12))
def p2(n): return 1 << int(np.ceil(np.log2(max(n, 2))))
def fq(f, n): return max(1, round(f*n/SR))*SR/n


def fase(f, n):
    if np.ndim(f) == 0:
        return TAU*float(f)*tt(n)
    f = np.asarray(f, float)
    return TAU*np.concatenate(([0.0], np.cumsum(f[:-1])))/SR


def seno(f, n, p0=0.0): return np.sin(fase(f, n)+p0)


def lin(pts, n):
    ts, vs = zip(*pts)
    return np.interp(tt(n), ts, vs)


def expi(pts, n):
    return np.exp(lin([(a, np.log(max(b, 1e-9))) for a, b in pts], n))


def ad(n, a, d, t0=0.0, hold=0.0):
    t = tt(n, t0)
    up = np.sin(0.5*np.pi*np.clip(t/max(a, 1e-5), 0, 1))**2
    tail = np.exp(-np.maximum(t-a-hold, 0)/d)
    return np.where(t < 0, 0.0, up*tail)


def suave(x): return x*x*(3-2*x)


def Mlp(f, fc, o=2): return 1.0/np.sqrt(1.0+(f/fc)**(2*o))
def Mhp(f, fc, o=2):
    r = (np.maximum(f, 1e-3)/fc)**(2*o)
    return np.sqrt(r/(1.0+r))
def Mbp(f, fc, q):
    x = np.maximum(f, 1e-3)/fc
    return 1.0/np.sqrt(1.0+(q*(x-1.0/x))**2)
def Mtilt(f, d, f0=1000.0): return (np.maximum(f, 20.0)/f0)**(d/6.0206)
def Mres(f, F, B): return F*F/np.sqrt((F*F-f*f)**2+(B*f)**2)


def lp(fc, o=2): return lambda f: Mlp(f, fc, o)
def hp(fc, o=2): return lambda f: Mhp(f, fc, o)
def bp(fc, q): return lambda f: Mbp(f, fc, q)
def tilt(d, f0=1000.0): return lambda f: Mtilt(f, d, f0)
def pk(fc, q, g): return lambda f: 1.0+(dbg(g)-1.0)*Mbp(f, fc, q)
def mul(*gs):
    def h(f):
        y = np.ones_like(f)
        for g in gs:
            y = y*g(f)
        return y
    return h
def add(*pares): return lambda f: sum(a*g(f) for a, g in pares)


def fasemin(mag):
    m = 2*(len(mag)-1)
    c = np.fft.irfft(np.log(np.maximum(mag, 1e-6)), m)
    w = np.zeros(m)
    w[0] = 1
    w[1:m//2] = 2
    w[m//2] = 1
    return np.exp(np.fft.rfft(c*w))


def filt(x, g, modo='min'):
    if x.ndim == 2:
        return np.stack([filt(x[:, i], g, modo) for i in range(x.shape[1])], 1)
    n = len(x)
    if modo == 'circ':
        f = np.fft.rfftfreq(n, 1/SR)
        return np.fft.irfft(np.fft.rfft(x)*g(f), n)
    m = p2(n+8192)
    if modo == 'min':
        mc = 4*m
        h = np.fft.irfft(fasemin(g(np.fft.rfftfreq(mc, 1/SR))), mc)[:m]
        Lh = m-n
        h[Lh:] = 0
        a = int(0.8*Lh)
        h[a:Lh] *= np.cos(0.5*np.pi*np.arange(Lh-a)/(Lh-a))**2
        H = np.fft.rfft(h)
    else:
        H = g(np.fft.rfftfreq(m, 1/SR))
    return np.fft.irfft(np.fft.rfft(x, m)*H, m)[:n]


def stft(x, gfn, N=1024, circ=False):
    H = N//4
    w = 0.5-0.5*np.cos(TAU*np.arange(N)/N)
    n = len(x)
    f = np.fft.rfftfreq(N, 1/SR)
    if circ:
        nf = n//H
        idx = (H*np.arange(nf)[:, None]+np.arange(N)[None, :]) % n
        tc = (H*np.arange(nf)+N/2)/SR
        S = np.fft.rfft(x[idx]*w, axis=1)
        y = (np.fft.irfft(S*gfn(tc[:, None], f[None, :]), N, axis=1)*w).reshape(nf, 4, H)
        ob = np.zeros((nf, H))
        for q in range(4):
            ob += np.roll(y[:, q], q, axis=0)
        return ob.ravel()/1.5
    xp = np.concatenate([np.zeros(N), x, np.zeros(N)])
    nf = -(-(len(xp)-N)//H)+1
    xp = np.concatenate([xp, np.zeros((nf-1)*H+N-len(xp))])
    idx = H*np.arange(nf)[:, None]+np.arange(N)[None, :]
    tc = (H*np.arange(nf)+N/2-N)/SR
    S = np.fft.rfft(xp[idx]*w, axis=1)
    y = (np.fft.irfft(S*gfn(tc[:, None], f[None, :]), N, axis=1)*w).reshape(nf, 4, H)
    ob = np.zeros((nf+3, H))
    for q in range(4):
        ob[q:q+nf] += y[:, q]
    return ob.ravel()[N:N+n]/1.5


def ruido(n, s): return R(s).standard_normal(n)


def buf(d, st=False): return np.zeros((ns(d), 2)) if st else np.zeros(ns(d))


def put(b, x, t0, g=1.0, wrap=False):
    i = int(round(t0*SR)) if isinstance(t0, float) else int(t0)
    if b.ndim == 2 and x.ndim == 1:
        x = np.stack([x, x], 1)
    L = len(b)
    if not wrap:
        if i >= L:
            return b
        if i < 0:
            x = x[-i:]
            i = 0
        k = min(L-i, len(x))
        b[i:i+k] += g*x[:k]
        return b
    i %= L
    pos = 0
    while pos < len(x):
        k = min(L-i, len(x)-pos)
        b[i:i+k] += g*x[pos:pos+k]
        pos += k
        i = 0
    return b


def pan(x, p):
    th = (p+1)*np.pi/4
    return np.stack([x*np.cos(th), x*np.sin(th)], 1)


def tono(dur, f1, f0, tf, ta, a=0.001, arm=()):
    n = ns(dur)
    t = tt(n)
    f = f0+(f1-f0)*np.exp(-t/tf)
    p = fase(f, n)
    y = np.sin(p)
    for k, g in arm:
        y += g*np.sin(k*p)
    return y*ad(n, a, ta)


def rafaga(dur, a, d, g, s, modo='min', hold=0.0):
    n = ns(dur)
    return filt(ruido(n, s)*ad(n, a, d, hold=hold), g, modo)


def modal(dur, fr, am, ta, att=0.0003):
    n = ns(dur)
    t = tt(n)
    y = np.zeros(n)
    for f, a, d in zip(fr, am, ta):
        if 20 < f < 0.45*SR:
            m = min(n, ns(d*10))
            y[:m] += a*np.sin(TAU*f*t[:m])*np.exp(-t[:m]/d)
    return y*np.clip(t/att, 0, 1)


def updown(x, k):
    n = len(x)
    X = np.fft.rfft(x)
    Y = np.zeros(n*k//2+1, complex)
    Y[:len(X)] = X
    return np.fft.irfft(Y, n*k)*k


def down(y, k):
    n = len(y)//k
    Y = np.fft.rfft(y)
    return np.fft.irfft(Y[:n//2+1], n)/k


def sat(x, drive=2.0, k=4):
    if x.ndim == 2:
        return np.stack([sat(x[:, i], drive, k) for i in range(2)], 1)
    n = len(x)
    m = n+(n % 2)+2048
    xp = np.zeros(m)
    xp[:n] = x
    s = np.abs(xp).max()+1e-12
    u = updown(xp/s, k)
    u = np.tanh(drive*u)/np.tanh(drive)
    return down(u, k)[:n]*s


def fold(h, n):
    if h.ndim == 2:
        return np.stack([fold(h[:, i], n) for i in range(2)], 1)
    out = np.zeros(n)
    for i in range(0, len(h), n):
        seg = h[i:i+n]
        out[:len(seg)] += seg
    return out


def conv(x, h, circ=False):
    if x.ndim == 1 and h.ndim == 2:
        x = np.stack([x, x], 1)
    if x.ndim == 2 and h.ndim == 1:
        h = np.stack([h, h], 1)
    if x.ndim == 2:
        return np.stack([conv(x[:, i], h[:, i], circ) for i in range(2)], 1)
    n = len(x)
    if circ:
        return np.fft.irfft(np.fft.rfft(x)*np.fft.rfft(fold(h, n)), n)
    m = p2(n+len(h))
    return np.fft.irfft(np.fft.rfft(x, m)*np.fft.rfft(h, m), m)[:n+len(h)-1]


def ir_sint(dur, rt, s, est=False, pre=0.008, nref=10):
    n = ns(dur)
    t = tt(n)
    out = []
    for c in range(2 if est else 1):
        r = R(s+17*c)
        y = np.zeros(n)
        bandas = [(lp(350, 2), rt[0]), (mul(hp(350, 2), lp(3000, 2)), rt[1]), (hp(3000, 2), rt[2])]
        for g, T in bandas:
            y += filt(r.standard_normal(n), g, 'zero')*np.exp(-6.9078*t/T)
        y *= np.clip(t/0.006, 0, 1)
        for i in range(nref):
            p = int(r.uniform(0.002, 0.05)*SR)
            y[p] += r.choice([-1, 1])*r.uniform(0.5, 1.5)*np.exp(-p/SR/0.05)*np.sqrt(np.mean(y[:ns(0.05)]**2))*20
        y = np.concatenate([np.zeros(ns(pre)), y])
        out.append(y/np.sqrt(np.sum(y**2)))
    return np.stack(out, 1) if est else out[0]


_IR = {}


def IR(nombre):
    if nombre not in _IR:
        cfg = {'cuarto': (0.5, (0.35, 0.3, 0.18), 901, False),
               'sala': (1.4, (1.0, 0.8, 0.45), 902, False),
               'grande': (3.5, (2.8, 2.2, 1.0), 903, False),
               'hall': (3.2, (2.6, 2.0, 0.9), 904, True),
               'lounge': (2.4, (1.9, 1.5, 0.7), 905, True),
               'estudio': (1.8, (1.3, 1.0, 0.5), 906, True),
               'cabina': (0.6, (0.35, 0.28, 0.15), 907, True)}[nombre]
        _IR[nombre] = ir_sint(cfg[0], cfg[1], cfg[2], cfg[3])
    return _IR[nombre]


def reverb(x, nombre, wet, circ=False, dry=1.0):
    y = conv(x, IR(nombre), circ)
    if circ:
        return dry*(x if y.ndim == x.ndim else np.stack([x, x], 1))+wet*y
    xd = x if y.ndim == x.ndim else np.stack([x, x], 1)
    out = wet*y
    out[:len(xd)] += dry*xd
    return out


def runmin(a, w):
    from numpy.lib.stride_tricks import sliding_window_view
    return sliding_window_view(a, w).min(axis=-1)


def limitador(x, techo, look=0.005, rel=0.12, circ=False):
    st = x.ndim == 2
    a = np.abs(x).max(axis=1) if st else np.abs(x)
    n = len(a)
    B = 32
    nb = -(-n//B)
    ap = np.zeros(nb*B)
    ap[:n] = a
    if circ and nb*B > n:
        ap[n:] = a[:nb*B-n]
    p = ap.reshape(nb, B).max(1)
    if circ:
        p = np.maximum(p, np.maximum(np.roll(p, 1), np.roll(p, -1)))
    else:
        p = np.maximum(p, np.maximum(np.concatenate([p[:1], p[:-1]]), np.concatenate([p[1:], p[-1:]])))
    g = np.minimum(1.0, techo/np.maximum(p, 1e-12))
    c = np.exp(-B/(rel*SR))
    env = np.empty(nb)
    e = 1.0
    gl = g.tolist()
    for _ in range(2 if circ else 1):
        for i in range(nb):
            e = min(gl[i], 1.0-(1.0-e)*c)
            env[i] = e
    A = max(1, int(look*SR/B))
    if circ:
        ep = np.concatenate([env[-A:], env, env[:A]])
    else:
        ep = np.concatenate([np.full(A, env[0]), env, np.full(A, env[-1])])
    e2 = runmin(ep, 2*A+1)
    k = np.concatenate([np.arange(1, A+2), np.arange(A, 0, -1)]).astype(float)
    k /= k.sum()
    if circ:
        e2p = np.concatenate([e2[-A:], e2, e2[:A]])
    else:
        e2p = np.concatenate([np.full(A, e2[0]), e2, np.full(A, e2[-1])])
    e3 = np.convolve(e2p, k, 'valid')
    cen = (np.arange(nb)+0.5)*B
    if circ:
        gs = np.interp(np.arange(n), np.concatenate([[cen[-1]-nb*B], cen, [cen[0]+nb*B]]), np.concatenate([[e3[-1]], e3, [e3[0]]]))
    else:
        gs = np.interp(np.arange(n), cen, e3)
    y = x*gs[:, None] if st else x*gs
    over = np.abs(y) > techo
    if over.any():
        y = np.where(over, np.sign(y)*techo*(1+np.tanh(np.abs(y)/techo-1)*0.02), y)
    return y


VOC = {'a': (820, 1250, 2650, 3500), 'e': (500, 1900, 2600, 3500), 'i': (320, 2350, 3000, 3700),
       'o': (540, 920, 2450, 3400), 'u': (360, 760, 2300, 3300), '@': (580, 1450, 2550, 3500),
       'm': (270, 1100, 2300, 3300), 'n': (280, 1650, 2500, 3400), 'b': (260, 900, 2250, 3300),
       'g': (300, 1900, 2400, 3300)}


def voz(f0, F, Bw, amp, tilt_=1.0, fmax=8000.0, s=0, jit=0.006, cr=64):
    n = len(f0)
    r = R(s)
    tj = np.linspace(0, n/SR, int(n/SR*22)+3)
    f0 = f0*(1+jit*np.interp(tt(n), tj, r.standard_normal(len(tj))))
    p = fase(f0, n)
    ic = np.unique(np.concatenate([np.arange(0, n, cr), [n-1]]))
    f0c = f0[ic]
    Fc = F[ic]
    ac = amp[ic]
    K = int(fmax/f0.min())
    y = np.zeros(n)
    xi = np.arange(n)
    for k in range(1, K+1):
        fk = k*f0c
        g = np.ones_like(fk)
        for i in range(F.shape[1]):
            g *= Mres(fk, Fc[:, i], Bw[i])
        g *= np.clip((fmax-fk)/(0.25*fmax), 0, 1)/k**tilt_*ac
        if g.max() < 1e-5:
            continue
        y += np.interp(xi, ic, g)*np.sin(k*p)
    return y


def suav_mm(x, w):
    w = max(1, int(w))
    k = np.ones(w)/w
    if x.ndim == 1:
        xp = np.concatenate([np.full(w, x[0]), x, np.full(w, x[-1])])
        return np.convolve(xp, k, 'same')[w:-w]
    return np.stack([suav_mm(x[:, i], w) for i in range(x.shape[1])], 1)


def jerga(sils, esc=1.0, t0=0.03, gap=0.015, cola=0.15):
    keys = []
    nz = []
    t = t0
    def Fv(v): return [x*esc for x in VOC[v]]
    keys.append((0.0, sils[0][3], *Fv(sils[0][1]), 0.0))
    for c, v, d, fa, fb, a in sils:
        F = Fv(v)
        fm = fa+(fb-fa)*0.25
        if c in ('m', 'n'):
            Fn = Fv(c)
            keys += [(t, fa, *Fn, 0.0), (t+0.02, fa, *Fn, 0.32*a), (t+0.07, fa, *Fn, 0.32*a), (t+0.11, fm, *F, a)]
        elif c in ('b', 'g'):
            Fb = Fv(c)
            keys += [(t, fa, *Fb, 0.0), (t+0.028, fa, *Fb, 0.0), (t+0.034, fa, *Fb, 0.5*a), (t+0.085, fm, *F, a)]
            nz.append((t+0.026, 0.012, 'b', 0.35*a))
        elif c == 'w':
            Fu = Fv('u')
            keys += [(t, fa, *Fu, 0.0), (t+0.025, fa, *Fu, 0.55*a), (t+0.1, fm, *F, a)]
        elif c == 'h':
            keys += [(t, fa, *F, 0.0), (t+0.05, fa, *F, 0.12*a), (t+0.09, fm, *F, a)]
            nz.append((t, 0.085, 'h', 0.32*a))
        else:
            keys += [(t, fa, *F, 0.0), (t+0.03, fa, *F, a)]
        keys += [(t+d-0.035, fb, *F, a), (t+d, fb, *F, 0.0)]
        if c == 'f':
            nz.append((t+d-0.03, 0.12, 'f', 0.4*a))
        t += d+gap
    keys.append((t+cola, keys[-1][1], *keys[-1][2:6], 0.0))
    keys.sort(key=lambda k: k[0])
    n = ns(t+cola)
    kt = np.array([k[0] for k in keys])
    kv = np.array([k[1:] for k in keys])
    tr = np.stack([np.interp(tt(n), kt, kv[:, i]) for i in range(kv.shape[1])], 1)
    tr[:, 1:5] = suav_mm(tr[:, 1:5], ns(0.018))
    tr[:, 5] = suav_mm(tr[:, 5], ns(0.008))
    tr[:, 0] = suav_mm(tr[:, 0], ns(0.03))
    return tr[:, 0], tr[:, 1:5], tr[:, 5], nz, n


def habla(sils, esc=1.0, s=0, bw=(90, 120, 170, 260), fmax=7500, tilt_=1.0, jit=0.008, asp=0.04):
    f0, F, A, nz, n = jerga(sils, esc)
    y = voz(f0, F, bw, A, tilt_, fmax, s, jit)
    y /= np.abs(y).max()+1e-9
    r = R(s+5)
    a_env = suav_mm(A, ns(0.01))
    y += asp*filt(r.standard_normal(n), mul(bp(1600, 0.6), lp(5000, 2)))*a_env
    for (t0, d, k, a) in nz:
        if k == 'b':
            x = rafaga(d+0.02, 0.0005, 0.004, lp(1800, 2), r.integers(1e9))
        elif k == 'h':
            x = rafaga(d+0.03, 0.02, 0.04, mul(bp(1400, 0.8), lp(4500, 2)), r.integers(1e9), hold=d*0.5)
        else:
            x = rafaga(d+0.05, 0.01, 0.05, mul(hp(1800, 2), lp(7000, 2)), r.integers(1e9), hold=d*0.4)
        x /= np.abs(x).max()+1e-9
        put(y, a*x, t0)
    return y


SONIDOS = []


def reg(nombre, tipo, vol, desc):
    def d(fn):
        SONIDOS.append((nombre, fn, tipo, vol, desc))
        return fn
    return d


@reg('Ding', 'sfx', -17, 'Campanita de cinturones, dos tonos suaves (agudo y grave).')
def s_ding():
    b = buf(2.6)
    def campana(f):
        return modal(2.2, [f, 2.0*f, 3.0*f, 4.16*f, 0.5*f], [1, 0.22, 0.07, 0.035, 0.05], [0.95, 0.35, 0.18, 0.1, 0.8], att=0.004)
    put(b, campana(880.0), 0.0)
    put(b, campana(659.26), 0.42)
    b = filt(b, lp(6500, 1))
    return reverb(b, 'cabina', 0.12)[:, 0]


@reg('AvisoMegafonia', 'sfx', -17, 'Gong de megafonía antes de un anuncio: tres notas ascendentes con color de altavoz.')
def s_megafonia():
    b = buf(2.8)
    for t0, m, a in [(0.0, 77, 0.9), (0.3, 81, 0.85), (0.6, 84, 1.0)]:
        f = m2f(m)
        put(b, modal(2.1, [f, 2.0*f, 3.0*f, 4.0*f], [1, 0.14, 0.05, 0.09], [1.15, 0.45, 0.25, 0.22], att=0.007), t0, a)
    b = filt(b, mul(hp(300, 1), lp(5200, 2), pk(1900, 1.0, 3)))
    return reverb(b, 'sala', 0.18)


@reg('Golpe', 'sfx', -16, 'Golpe sordo y suave de cuerpo u objeto.')
def s_golpe():
    b = buf(0.5)
    put(b, tono(0.45, 230, 88, 0.022, 0.07), 0, 0.8)
    put(b, rafaga(0.25, 0.001, 0.03, mul(lp(900, 2), hp(90, 1)), 11), 0, 1.0)
    put(b, rafaga(0.2, 0.001, 0.04, bp(260, 1.2), 13), 0, 0.6)
    put(b, rafaga(0.05, 0.0003, 0.003, bp(1700, 0.7), 12), 0, 0.15)
    return reverb(b, 'cuarto', 0.06)


@reg('GolpeFuerte', 'sfx', -13, 'Impacto pesado con cuerpo grave y algo de escombro.')
def s_golpe_fuerte():
    b = buf(1.8)
    put(b, tono(1.3, 160, 52, 0.045, 0.22, a=0.002, arm=((2, 0.3),)), 0, 0.75)
    put(b, rafaga(0.6, 0.0008, 0.08, mul(lp(2500, 2), hp(120, 1)), 21), 0, 1.3)
    put(b, rafaga(0.4, 0.001, 0.07, bp(240, 1.0), 22), 0, 1.0)
    put(b, rafaga(0.1, 0.0005, 0.018, bp(1300, 0.9), 24), 0, 0.6)
    r = R(23)
    for i in range(8):
        t0 = 0.06+r.uniform(0, 0.45)*(0.3+i/8)
        f = r.uniform(380, 1100)
        put(b, modal(0.15, [f, f*2.31, f*3.87], [1, 0.5, 0.25], [0.035, 0.02, 0.012]), t0, 0.11*r.uniform(0.4, 1)*(1-i/10))
    b = sat(b, 2.2)
    return reverb(b, 'cuarto', 0.12)


@reg('GolpeMetal', 'sfx', -15, 'Choque metálico (clanc) con rebote corto.')
def s_golpe_metal():
    b = buf(1.4)
    def clank(f, s, a):
        r = R(s)
        rat = np.array([1, 2.76, 5.40, 8.93, 13.34])*r.uniform(0.98, 1.02, 5)
        x = modal(1.3, f*rat, [1, 0.75, 0.45, 0.25, 0.1], [0.55, 0.38, 0.22, 0.12, 0.06])
        put(x, modal(0.3, [f*0.38], [1], [0.06]), 0, 0.5)
        put(x, rafaga(0.03, 0.0002, 0.003, bp(3200, 0.8), s+1), 0, 0.35)
        return a*x
    put(b, clank(430, 31, 1.0), 0)
    put(b, clank(455, 32, 0.35), 0.13)
    put(b, clank(440, 33, 0.12), 0.21)
    b = filt(b, lp(7000, 2))
    return reverb(b, 'cuarto', 0.15)


@reg('Cristal', 'sfx', -15, 'Cristal pequeño rompiéndose: crack y tintineo de esquirlas.')
def s_cristal():
    b = buf(1.3)
    r = R(41)
    put(b, rafaga(0.05, 0.0004, 0.012, mul(bp(3800, 0.8), lp(9000, 2)), 42), 0, 0.9)
    put(b, rafaga(0.15, 0.0005, 0.03, bp(1500, 0.9), 43), 0, 0.35)
    for i in range(46):
        t0 = 0.004+0.75*r.uniform()**2.2
        f = r.uniform(1900, 5200)
        a = r.uniform(0.25, 1)*np.exp(-t0/0.35)
        d = r.uniform(0.02, 0.11)
        put(b, modal(d*6, [f, f*2.32, f*1.41], [1, 0.3, 0.4], [d, d*0.5, d*0.7]), t0, 0.32*a)
    for i in range(5):
        t0 = 0.1+0.5*r.uniform()
        f = r.uniform(1300, 2000)
        put(b, modal(0.3, [f, f*2.7], [1, 0.4], [0.06, 0.03]), t0, 0.2)
    b += 0.05*filt(ruido(len(b), 44)*ad(len(b), 0.003, 0.18), mul(hp(3500, 2), lp(8000, 2)))
    b = filt(b, mul(lp(8000, 2), pk(900, 1.0, 3)))
    return reverb(b, 'cuarto', 0.14)


@reg('Madera', 'sfx', -15, 'Caja de madera rompiéndose: crujido, astillas y tablas cayendo.')
def s_madera():
    b = buf(1.5)
    r = R(51)
    put(b, modal(0.3, [175, 410, 720, 1150, 1700], [1, 0.8, 0.55, 0.35, 0.2], [0.07, 0.045, 0.03, 0.02, 0.012]), 0, 0.9)
    put(b, rafaga(0.08, 0.0004, 0.018, bp(1400, 0.8), 52), 0, 0.8)
    put(b, tono(0.3, 150, 70, 0.02, 0.06), 0, 0.6)
    for i in range(34):
        t0 = 0.01+0.55*r.uniform()**1.6
        fc = r.uniform(900, 4200)
        put(b, rafaga(0.03, 0.0003, r.uniform(0.002, 0.008), bp(fc, 2.0), 53+i), t0, r.uniform(0.2, 0.7)*np.exp(-t0/0.4))
    for i, t0 in enumerate([0.22, 0.37, 0.55, 0.71]):
        f = r.uniform(230, 480)
        put(b, modal(0.25, [f, f*2.4, f*4.1], [1, 0.6, 0.3], [0.05, 0.03, 0.015]), t0+r.uniform(-0.03, 0.03), 0.4*(1-i*0.18))
        put(b, rafaga(0.05, 0.0005, 0.01, bp(1100, 1.0), 90+i), t0, 0.2)
    return reverb(b, 'cuarto', 0.14)


@reg('Salpicadura', 'sfx', -16, 'Salpicadura de líquido con gotitas.')
def s_salpicadura():
    b = buf(1.2)
    r = R(61)
    n = ns(0.08)
    t = tt(n)
    put(b, np.sin(fase(190*(1+14*t), n))*ad(n, 0.002, 0.03), 0, 0.9)
    n = ns(0.9)
    sp = stft(ruido(n, 62), lambda t, f: Mlp(f, 900+4500*np.exp(-np.maximum(t, 0)/0.05), 2)*Mhp(f, 180, 2)*(1+Mbp(f, 500, 1.0)))
    put(b, sp*ad(n, 0.004, 0.13), 0.005, 0.8)
    put(b, stft(ruido(ns(0.5), 63), lambda t, f: Mbp(f, 600+1200*np.exp(-np.maximum(t, 0)/0.08), 0.8))*ad(ns(0.5), 0.015, 0.09), 0.1, 0.45)
    for i in range(18):
        t0 = 0.05+0.6*r.uniform()**1.4
        f = r.uniform(450, 1600)
        m = ns(0.06)
        tm = tt(m)
        put(b, np.sin(fase(f*(1+r.uniform(3, 7)*tm), m))*ad(m, 0.001, r.uniform(0.008, 0.02)), t0, 0.16*r.uniform(0.3, 1)*np.exp(-t0/0.35))
    b = filt(b, lp(7000, 2))
    return reverb(b, 'cuarto', 0.1)


@reg('Resbalon', 'sfx', -16, 'Resbalón de dibujo animado: chirrido de suela + silbato que sube (fiuuup).')
def s_resbalon():
    b = buf(0.7)
    n = ns(0.06)
    t = tt(n)
    sq = np.sin(fase(950+120*np.sin(TAU*45*t)+R(71).standard_normal(n)*20, n))*ad(n, 0.003, 0.02)
    put(b, filt(sq, lp(4000, 1)), 0, 0.35)
    n = ns(0.5)
    t = tt(n)
    f = expi([(0, 380), (0.3, 1500), (0.42, 1420)], n)*(1+0.015*np.sin(TAU*9*t))
    p = fase(f, n)
    w = np.sin(p)+0.12*np.sin(2*p)+0.04*np.sin(3*p)
    env = lin([(0, 0), (0.03, 0.8), (0.28, 1.0), (0.42, 0.7), (0.5, 0)], n)
    br = stft(ruido(n, 72), lambda tq, fr: Mbp(fr, np.interp(tq, tt(n), f), 3.0))*0.15
    put(b, (w+br)*env, 0.035)
    return reverb(b, 'cuarto', 0.1)


@reg('Extintor', 'sfx', -17, 'Ráfaga corta de extintor (~0,4 s), apta para repetir.')
def s_extintor():
    n = ns(0.44)
    t = tt(n)
    env = lin([(0, 0), (0.012, 1.25), (0.04, 1.0), (0.36, 0.95), (0.44, 0)], n)
    env *= 1+0.08*np.sin(TAU*31*t)*R(81).uniform()
    hiss = filt(ruido(n, 82), mul(hp(600, 2), lp(7000, 2), pk(2500, 0.8, 3), tilt(-2.0)))
    low = filt(ruido(n, 83), mul(lp(500, 2), hp(80, 2)))*ad(n, 0.004, 0.06)
    x = hiss*env+0.8*low
    return x


@reg('Llave', 'sfx', -17, 'Llave inglesa/carraca: serie de clics metálicos.')
def s_llave():
    b = buf(0.6)
    r = R(91)
    tiempos = [0.0, 0.058, 0.113, 0.165, 0.214, 0.262]
    for i, t0 in enumerate(tiempos):
        j = r.uniform(0.97, 1.03)
        x = modal(0.06, [1950*j, 3050*j, 4400*j, 900*j, 520*j], [0.8, 0.45, 0.2, 0.7, 0.4], [0.011, 0.007, 0.004, 0.01, 0.012])
        put(x, rafaga(0.01, 0.0002, 0.0012, bp(3500, 0.9), 92+i), 0, 0.4)
        put(b, x, t0+r.uniform(-0.004, 0.004), 0.8+0.2*(i % 2))
    put(b, modal(0.15, [1800, 3100], [1, 0.5], [0.03, 0.015]), 0.3, 0.4)
    b = filt(b, lp(8000, 2))
    return reverb(b, 'cuarto', 0.1)


@reg('Reparado', 'sfx', -16, 'Jingle brillante de reparación completada.')
def s_reparado():
    b = buf(1.8)
    r = R(101)
    for i, m in enumerate([72, 74, 77, 81, 84]):
        f = m2f(m+12)
        a = [0.8, 0.8, 0.85, 0.9, 0.7][i]
        put(b, modal(1.4, [f, 2.0*f, 3.0*f, 0.5*f], [1, 0.25, 0.06, 0.15], [0.55, 0.2, 0.08, 0.6], att=0.002), i*0.055, a)
    for m in [65, 69, 72, 76]:
        f = m2f(m+12)
        put(b, modal(1.5, [f, 2*f, 4*f], [1, 0.15, 0.05], [0.7, 0.3, 0.1], att=0.01), 0.3, 0.3)
    for i in range(26):
        t0 = 0.25+0.7*r.uniform()
        f = r.uniform(3000, 6000)
        put(b, modal(0.08, [f], [1], [0.012]), t0, 0.12*np.exp(-(t0-0.25)/0.4))
    n = ns(0.35)
    put(b, stft(ruido(n, 102), lambda t, f: Mbp(f, 1500+5000*np.clip(t/0.3, 0, 1), 1.5))*lin([(0, 0), (0.25, 1), (0.35, 0)], n), 0.0, 0.08)
    b = filt(b, lp(9000, 2))
    return reverb(b, 'sala', 0.2)


@reg('Explosion', 'sfx', -11, 'Explosión caricaturesca (boom redondo) para brecha en el casco o motor.')
def s_explosion():
    b = buf(3.4)
    put(b, tono(2.5, 110, 46, 0.08, 0.45, a=0.004, arm=((2, 0.35), (3, 0.1))), 0, 0.7)
    n = ns(2.6)
    body = stft(ruido(n, 111), lambda t, f: Mlp(f, 380+4200*np.exp(-np.maximum(t, 0)/0.15), 2)*Mhp(f, 60, 2)*(1+1.5*Mbp(f, 180, 1.0)))
    put(b, body*(ad(n, 0.003, 0.38)+0.3*ad(n, 0.15, 0.75)), 0, 3.0)
    put(b, rafaga(0.08, 0.0005, 0.015, mul(bp(900, 0.6)), 112), 0, 0.9)
    r = R(113)
    for i in range(30):
        t0 = 0.15+1.4*r.uniform()**1.5
        put(b, rafaga(0.02, 0.0003, r.uniform(0.002, 0.005), bp(r.uniform(700, 2600), 1.5), 114+i), t0, 0.25*r.uniform(0.3, 1)*np.exp(-t0/0.8))
    b = sat(b, 2.6)
    b = filt(b, lp(7000, 2))
    return reverb(b, 'sala', 0.22)


@reg('Succion', 'sfx', -14, 'Aire entrando a presión por un agujero: whoosh que crece y corta.')
def s_succion():
    b = buf(1.4)
    n = ns(1.0)
    fc = lambda t: 250*np.exp(np.log(9)*np.clip(t/0.92, 0, 1))
    x = stft(ruido(n, 121), lambda t, f: Mbp(f, fc(t), 1.1)+0.3*Mbp(f, fc(t)*2.1, 2.5))
    env = lin([(0, 0), (0.2, 0.25), (0.75, 0.85), (0.9, 1.0), (0.96, 0.15), (1.0, 0)], n)
    put(b, x*env, 0)
    m = ns(0.9)
    put(b, np.sin(fase(fc(tt(m))*0.95, m))*lin([(0, 0), (0.6, 0.06), (0.9, 0.12), (0.92, 0)], m), 0, 1.0)
    put(b, tono(0.4, 140, 70, 0.04, 0.08), 0.93, 0.5)
    b = filt(b, lp(8000, 2))
    return reverb(b, 'cuarto', 0.12)


@reg('Trueno', 'sfx', -13, 'Trueno: chasquido inicial y retumbo largo.')
def s_trueno():
    b = buf(5.5)
    r = R(131)
    for i in range(5):
        t0 = 0.015*i+r.uniform(0, 0.02)+0.08*(i > 2)
        put(b, rafaga(0.12, 0.002, 0.03, mul(lp(4500, 2), hp(150, 1)), 132+i), t0, 0.7*(1-i*0.12))
    n = ns(4.6)
    rum = filt(ruido(n, 140), mul(lp(220, 3), hp(25, 2)))
    mid = filt(ruido(n, 141), mul(lp(900, 2), hp(150, 2)))
    env = np.zeros(n)
    for i in range(9):
        t0 = 0.05+2.6*r.uniform()**1.3
        env += r.uniform(0.4, 1.0)*ad(n, r.uniform(0.05, 0.25), r.uniform(0.35, 1.1), t0)
    env += 0.6*ad(n, 0.1, 1.6, 0.05)
    env /= env.max()
    put(b, rum*env*2.2+mid*env**1.5*0.5, 0.03)
    b = sat(b, 1.6)
    return reverb(b, 'grande', 0.3)


@reg('Pajaros', 'sfx', -15, 'Bandada de pájaros caricaturescos: graznidos y aleteos.')
def s_pajaros():
    b = buf(2.2)
    r = R(151)
    for i in range(7):
        t0 = 0.05+i*0.22+r.uniform(-0.05, 0.05)
        d = r.uniform(0.09, 0.16)
        base = r.uniform(650, 1100)
        n = ns(d+0.05)
        f0 = expi([(0, base*0.85), (d*0.25, base*1.25), (d, base*0.7), (d+0.05, base*0.65)], n)
        f0 *= 1+0.03*np.sin(TAU*55*tt(n))
        esc = r.uniform(1.4, 1.9)
        F = np.tile(np.array([700, 1500, 2700, 3600])*esc/1.6, (n, 1))
        A = lin([(0, 0), (0.012, 1), (d*0.7, 0.8), (d, 0), (d+0.05, 0)], n)
        x = voz(f0, F, (180, 260, 380, 500), A, 0.8, 8000, 152+i, 0.02)
        x /= np.abs(x).max()+1e-9
        put(b, x, t0, 0.6*r.uniform(0.6, 1))
    for j in range(4):
        rate = r.uniform(9, 13)
        st = r.uniform(0.0, 0.5)
        for k in range(int(r.uniform(7, 12))):
            t0 = st+k/rate+r.uniform(-0.008, 0.008)
            x = rafaga(0.06, 0.006, 0.025, mul(bp(700, 0.7), lp(2600, 2)), 170+j*20+k)
            put(b, x, t0, 0.5*r.uniform(0.6, 1)*np.exp(-k*0.06))
    b = filt(b, lp(8500, 2))
    return reverb(b, 'sala', 0.18)


@reg('Cocodrilo', 'sfx', -14, 'Gruñido grave de cocodrilo seguido de un siseo.')
def s_cocodrilo():
    b = buf(2.1)
    n = ns(1.15)
    t = tt(n)
    f0 = 52+6*np.sin(TAU*1.3*t)-8*t
    F = np.tile([360, 820, 2000, 3000], (n, 1))*np.array([1+0.1*np.sin(TAU*0.9*t)]).T
    A = lin([(0, 0), (0.12, 1), (0.8, 0.9), (1.15, 0)], n)*(1+0.55*np.sin(TAU*24*t))
    g = voz(f0, F, (160, 220, 320, 400), A, 0.6, 4500, 181, 0.03)
    g /= np.abs(g).max()
    g = sat(g, 2.0)
    put(b, g, 0, 1.0)
    put(b, filt(ruido(ns(0.6), 182)*ad(ns(0.6), 0.02, 0.12, hold=0.05), mul(bp(2600, 0.7), hp(900, 2), lp(5000, 2))), 0.0, 0.18)
    n = ns(0.9)
    hs = filt(ruido(n, 183), mul(bp(3800, 0.6), hp(1500, 2), lp(7500, 2)))*lin([(0, 0), (0.06, 1), (0.5, 0.7), (0.9, 0)], n)
    put(b, hs, 0.95, 0.55)
    return reverb(b, 'cuarto', 0.12)


@reg('Mordisco', 'sfx', -15, 'Mordisco: chasquido de mandíbulas (chomp).')
def s_mordisco():
    b = buf(0.5)
    put(b, modal(0.15, [520, 1320, 2350, 3400], [1, 0.7, 0.4, 0.2], [0.03, 0.016, 0.01, 0.006]), 0, 0.8)
    put(b, rafaga(0.03, 0.0002, 0.003, bp(2600, 0.8), 191), 0, 0.6)
    put(b, rafaga(0.12, 0.002, 0.035, mul(bp(1500, 0.8), lp(4500, 2)), 192), 0.008, 0.55)
    r = R(193)
    for i in range(10):
        put(b, rafaga(0.01, 0.0002, 0.0015, bp(r.uniform(1200, 3500), 1.5), 194+i), 0.01+0.07*r.uniform(), 0.3*r.uniform(0.4, 1))
    put(b, tono(0.25, 170, 80, 0.02, 0.05), 0, 0.8)
    return reverb(b, 'cuarto', 0.1)


@reg('Comer', 'sfx', -17, 'Masticar caricaturesco: tres bocados (ñam ñam ñam).')
def s_comer():
    b = buf(1.0)
    r = R(201)
    for j, t0 in enumerate([0.0, 0.26, 0.5]):
        for i in range(16):
            put(b, rafaga(0.015, 0.0002, r.uniform(0.0015, 0.004), mul(bp(r.uniform(800, 2800), 1.3), lp(5000, 2)), 202+j*30+i), t0+0.1*r.uniform()**1.3, 0.6*r.uniform(0.3, 1))
        n = ns(0.16)
        t = tt(n)
        f0 = 150+25*np.exp(-t/0.05)+j*10
        F = np.tile(VOC['m'], (n, 1)).astype(float)*1.2
        x = voz(f0, F, (120, 200, 300, 400), ad(n, 0.01, 0.045), 0.9, 4000, 230+j)
        put(b, x/(np.abs(x).max()+1e-9), t0+0.02, 0.22)
        put(b, rafaga(0.08, 0.002, 0.02, bp(450, 1.0), 260+j), t0, 0.3)
    return reverb(b, 'cuarto', 0.08)


@reg('PasajeroQueja', 'sfx', -16, 'Pasajero quejándose en jerigonza (sin palabras reales), voz de dibujo.')
def s_queja():
    sil = [('b', 'a', 0.17, 215, 245, 1.0), ('n', 'e', 0.15, 240, 215, 0.85), ('m', 'e', 0.17, 210, 185, 0.85),
           ('h', 'o', 0.13, 200, 175, 0.75), ('m', 'u', 0.26, 170, 135, 0.7)]
    y = habla(sil, 1.1, 211)
    put(y, rafaga(0.12, 0.008, 0.035, mul(hp(1200, 2), lp(5000, 2)), 212), len(y)-ns(0.16), 0.12)
    return reverb(y, 'cuarto', 0.06)


@reg('PasajeroFeliz', 'sfx', -16, 'Pasajero contento: "¡mm-hm!" ascendente en jerigonza.')
def s_feliz():
    sil = [('m', 'm', 0.17, 240, 285, 0.8), ('h', 'm', 0.25, 300, 400, 1.0)]
    y = habla(sil, 1.25, 221, bw=(80, 110, 160, 250), asp=0.02, tilt_=0.8)
    return reverb(y, 'cuarto', 0.06)


@reg('PasajeroGrito', 'sfx', -14, 'Grito caricaturesco "¡aaah!" (síntesis de formantes).')
def s_grito():
    n = ns(1.25)
    t = tt(n)
    f0 = expi([(0, 360), (0.12, 640), (0.75, 600), (1.0, 520), (1.25, 400)], n)
    f0 *= 1+0.035*np.sin(TAU*6.8*t)*np.clip((t-0.12)/0.2, 0, 1)
    F = np.tile(np.array([950, 1450, 2950, 3900], float), (n, 1))
    F[:, 0] *= lin([(0, 0.8), (0.12, 1.0), (1.25, 0.9)], n)
    A = lin([(0, 0), (0.05, 0.6), (0.15, 1), (0.95, 0.85), (1.2, 0), (1.25, 0)], n)
    y = voz(f0, F, (110, 140, 220, 320), A, 1.15, 7000, 241, 0.012)
    y /= np.abs(y).max()
    y += 0.06*filt(ruido(n, 242), mul(bp(1800, 0.7), lp(6000, 2)))*A
    y = filt(y, lp(6500, 2))
    return reverb(y, 'cuarto', 0.1)


@reg('Servir', 'sfx', -17, 'Servir: plato apoyado con un "pop" agradable.')
def s_servir():
    b = buf(0.6)
    put(b, modal(0.4, [1240, 2960, 4780, 6350], [1, 0.45, 0.25, 0.08], [0.09, 0.05, 0.03, 0.015]), 0.01, 0.35)
    put(b, tono(0.12, 190, 120, 0.02, 0.025), 0.0, 0.5)
    n = ns(0.12)
    put(b, np.sin(fase(expi([(0, 620), (0.08, 330)], n), n))*ad(n, 0.002, 0.035), 0.012, 0.7)
    put(b, rafaga(0.03, 0.0004, 0.004, bp(2000, 0.8), 251), 0.0, 0.12)
    return reverb(b, 'cuarto', 0.1)


@reg('Coger', 'sfx', -18, 'Coger objeto: whoosh corto ascendente y clic.')
def s_coger():
    b = buf(0.4)
    n = ns(0.17)
    x = stft(ruido(n, 261), lambda t, f: Mbp(f, 450*np.exp(np.log(5)*np.clip(t/0.16, 0, 1)), 1.3))
    put(b, x*np.sin(np.pi*np.clip(tt(n)/0.17, 0, 1))**2, 0, 0.6)
    put(b, modal(0.05, [2200, 3700, 1100], [1, 0.4, 0.5], [0.009, 0.005, 0.01]), 0.15, 0.7)
    m = ns(0.06)
    put(b, np.sin(fase(expi([(0, 700), (0.05, 1300)], m), m))*ad(m, 0.002, 0.015), 0.15, 0.35)
    return b


@reg('Lanzar', 'sfx', -17, 'Lanzar objeto: whoosh que se aleja.')
def s_lanzar():
    n = ns(0.5)
    t = tt(n)
    fc = lambda t: 1900*np.exp(-np.log(4.5)*np.clip(t/0.4, 0, 1))
    x = stft(ruido(n, 271), lambda t, f: Mbp(f, fc(t), 1.2)+0.4*Mbp(f, fc(t)*1.8, 4))
    env = lin([(0, 0), (0.07, 1.0), (0.18, 0.6), (0.42, 0.05), (0.5, 0)], n)
    w = np.sin(fase(fc(t)*0.9, n))*0.05*env
    return reverb(x*env+w, 'cuarto', 0.08)


def creak(dur, r0, r1, body, s, jit=0.25, amp_pts=None):
    r = R(s)
    n = ns(dur)
    imp = np.zeros(n)
    t = 0.0
    while t < dur:
        u = t/dur
        rate = r0+(r1-r0)*u+0.3*(r1-r0)*np.sin(TAU*1.7*u)
        imp[min(n-1, int(t*SR))] += r.uniform(0.4, 1.0)
        t += (1.0/rate)*(1+jit*r.uniform(-1, 1))
    fr, ta = body
    k = modal(0.06, fr, [1, 0.8, 0.6, 0.4][:len(fr)], ta)
    y = conv(imp, k)[:n]
    if amp_pts:
        y *= lin(amp_pts, n)
    return y


@reg('PuertaAbrir', 'sfx', -15, 'Puerta pesada con bisagra abriéndose: cerrojo, crujido y tope.')
def s_puerta_abrir():
    b = buf(1.9)
    put(b, modal(0.3, [310, 860, 1620, 2700], [1, 0.7, 0.4, 0.25], [0.05, 0.03, 0.02, 0.01]), 0, 0.7)
    put(b, rafaga(0.02, 0.0002, 0.002, bp(3000, 0.8), 281), 0, 0.3)
    put(b, creak(1.0, 28, 55, ([340, 760, 1350, 2200], [0.02, 0.015, 0.01, 0.007]), 282,
                 amp_pts=[(0, 0), (0.1, 0.8), (0.5, 1), (0.85, 0.6), (1.0, 0)]), 0.12, 0.45)
    put(b, tono(0.4, 95, 52, 0.03, 0.1), 1.16, 0.8)
    put(b, rafaga(0.2, 0.001, 0.04, lp(800, 2), 283), 1.16, 0.5)
    put(b, modal(0.2, [520, 1310], [1, 0.5], [0.04, 0.02]), 1.17, 0.25)
    return reverb(b, 'cuarto', 0.14)


@reg('PuertaCerrar', 'sfx', -14, 'Puerta pesada cerrándose de golpe con pestillo.')
def s_puerta_cerrar():
    b = buf(1.2)
    n = ns(0.22)
    put(b, filt(ruido(n, 291), lp(700, 2))*lin([(0, 0), (0.18, 1), (0.22, 0)], n), 0, 0.25)
    put(b, tono(0.6, 120, 62, 0.03, 0.12, a=0.0015, arm=((2, 0.3),)), 0.2, 0.7)
    put(b, rafaga(0.2, 0.0008, 0.05, mul(lp(1500, 2), hp(100, 1)), 292), 0.2, 1.2)
    put(b, modal(0.3, [185, 410, 655, 980], [1, 0.8, 0.5, 0.3], [0.06, 0.04, 0.03, 0.02]), 0.2, 0.55)
    put(b, modal(0.2, [1100, 2600, 4150], [1, 0.6, 0.3], [0.035, 0.02, 0.01]), 0.205, 0.35)
    for i, t0 in enumerate([0.27, 0.31, 0.345]):
        put(b, modal(0.08, [1600+i*150, 3300], [1, 0.4], [0.012, 0.006]), t0, 0.15*(1-0.25*i))
    b = sat(b, 1.5)
    return reverb(b, 'cuarto', 0.16)


@reg('Altillo', 'sfx', -17, 'Compartimento superior: pop del pestillo y crujido de la tapa.')
def s_altillo():
    b = buf(1.0)
    put(b, modal(0.12, [900, 2150, 3400], [1, 0.6, 0.3], [0.02, 0.012, 0.007]), 0, 0.6)
    put(b, tono(0.08, 520, 260, 0.015, 0.025), 0.0, 0.5)
    put(b, rafaga(0.01, 0.0002, 0.0012, bp(3500, 0.9), 301), 0, 0.3)
    put(b, creak(0.42, 60, 110, ([780, 1650, 2850], [0.012, 0.008, 0.005]), 302,
                 amp_pts=[(0, 0), (0.08, 0.7), (0.3, 1), (0.42, 0)]), 0.07, 0.3)
    put(b, tono(0.2, 170, 110, 0.02, 0.05), 0.5, 0.6)
    put(b, modal(0.15, [640, 1500, 2600], [1, 0.5, 0.3], [0.03, 0.015, 0.01]), 0.502, 0.3)
    return reverb(b, 'cuarto', 0.12)


@reg('Mascarillas', 'sfx', -15, 'Caída de las mascarillas de oxígeno: paneles que saltan y repiqueteo de plástico.')
def s_mascarillas():
    b = buf(1.8)
    r = R(311)
    for i, t0 in enumerate([0.0, 0.035, 0.075, 0.1, 0.15, 0.2]):
        f = r.uniform(700, 1300)
        put(b, modal(0.08, [f, f*2.3, f*3.7], [1, 0.5, 0.25], [0.015, 0.008, 0.005]), t0, 0.5)
        put(b, rafaga(0.01, 0.0002, 0.0015, bp(2500, 0.9), 312+i), t0, 0.25)
    n = ns(0.4)
    put(b, filt(ruido(n, 320), mul(lp(1500, 2), hp(150, 1)))*lin([(0, 0), (0.15, 1), (0.4, 0)], n), 0.12, 0.2)
    for i in range(48):
        t0 = 0.15+1.1*r.uniform()**1.8
        f = r.uniform(1100, 3600)
        put(b, modal(0.05, [f, f*1.9], [1, 0.35], [r.uniform(0.004, 0.012), 0.004]), t0, 0.28*r.uniform(0.3, 1)*np.exp(-(t0-0.15)/0.6))
    for i in range(5):
        t0 = 0.25+0.6*r.uniform()
        put(b, tono(0.12, 220, 160, 0.03, 0.03), t0, 0.15)
    return reverb(b, 'cabina', 0.2)[:, 0]


@reg('Boton', 'sfx', -19, 'Botón de cabina de mando: clic de pulsar y soltar.')
def s_boton():
    b = buf(0.14)
    put(b, modal(0.04, [3100, 5200, 720, 1500], [1, 0.4, 0.7, 0.4], [0.004, 0.003, 0.009, 0.006]), 0, 1.0)
    put(b, rafaga(0.006, 0.0001, 0.0008, bp(4000, 0.8), 321), 0, 0.3)
    put(b, modal(0.04, [2700, 4600, 640], [1, 0.4, 0.6], [0.003, 0.002, 0.007]), 0.048, 0.45)
    return filt(b, lp(9000, 2))


@reg('Rampa', 'sfx', -16, 'Rampa hidráulica bajando (~2 s): motor, siseo y topes.')
def s_rampa():
    D = 2.4
    b = buf(D)
    put(b, modal(0.3, [240, 610, 1180, 2100], [1, 0.6, 0.35, 0.2], [0.06, 0.035, 0.02, 0.01]), 0, 0.6)
    put(b, tono(0.3, 110, 60, 0.02, 0.07), 0, 0.5)
    n = ns(2.05)
    t = tt(n)
    f0 = lin([(0, 70), (0.3, 112), (1.6, 118), (2.05, 80)], n)*(1+0.004*np.sin(TAU*3.1*t))
    p = fase(f0, n)
    mot = np.zeros(n)
    for k in range(1, 40):
        if k*120 > 9000:
            break
        a = 1/k*(1+2.5*Mbp(k*115, 1100, 2.5))*Mlp(k*115, 2500, 2)
        mot += a*np.sin(k*p+k*0.7)
    mot += 0.25*np.sin(13.5*p)
    env = lin([(0, 0), (0.12, 1), (1.85, 1), (2.05, 0)], n)
    put(b, 0.25*mot*env, 0.05)
    put(b, 0.5*filt(ruido(n, 331), mul(bp(2400, 0.7), lp(6000, 2)))*env*(1+0.2*np.sin(TAU*7*t)), 0.05, 0.35)
    put(b, filt(ruido(n, 332), lp(140, 3))*env, 0.05, 0.9)
    put(b, modal(0.3, [260, 650, 1250], [1, 0.6, 0.3], [0.07, 0.035, 0.02]), 2.08, 0.8)
    put(b, tono(0.3, 100, 50, 0.03, 0.09), 2.08, 0.8)
    return reverb(b, 'cuarto', 0.12)


@reg('Disparo', 'sfx', -15, 'Disparo de torreta caricaturesco (thump + pew), corto.')
def s_disparo():
    b = buf(0.5)
    put(b, tono(0.35, 300, 85, 0.016, 0.06, arm=((2, 0.25),)), 0, 0.85)
    put(b, tono(0.15, 1500, 320, 0.028, 0.05, arm=((2, 0.25), (3, 0.08))), 0.002, 0.7)
    put(b, rafaga(0.04, 0.0003, 0.012, mul(bp(1800, 0.7), lp(5000, 2)), 341), 0, 0.6)
    put(b, rafaga(0.35, 0.005, 0.09, lp(650, 2), 342), 0.01, 0.35)
    b = sat(b, 2.0)
    return reverb(b, 'cuarto', 0.1)


@reg('ImpactoPirata', 'sfx', -15, 'Impacto sobre el avión pirata: "ponk" con chapa y polvareda.')
def s_impacto_pirata():
    b = buf(0.8)
    put(b, tono(0.2, 950, 340, 0.03, 0.045), 0, 0.8)
    put(b, modal(0.5, [1650, 2930, 4310], [1, 0.6, 0.3], [0.12, 0.07, 0.035]), 0.002, 0.3)
    put(b, rafaga(0.25, 0.002, 0.07, mul(lp(2200, 2), hp(150, 1)), 351), 0, 0.5)
    put(b, rafaga(0.05, 0.0005, 0.02, bp(1200, 0.9), 352), 0, 0.4)
    put(b, tono(0.3, 140, 60, 0.02, 0.07), 0, 0.6)
    return reverb(b, 'sala', 0.15)


@reg('PirataCae', 'sfx', -15, 'Avión pirata cayendo: silbido descendente y golpe lejano.')
def s_pirata_cae():
    b = buf(4.2)
    n = ns(2.75)
    t = tt(n)
    f = expi([(0, 1500), (2.75, 400)], n)*(1+0.012*np.sin(TAU*5*t))
    p = fase(f, n)
    env = lin([(0, 0), (0.25, 0.5), (1.9, 1.0), (2.6, 0.8), (2.75, 0)], n)
    w = (np.sin(p)+0.08*np.sin(2*p))*env
    air = stft(ruido(n, 361), lambda tq, fr: Mbp(fr, np.interp(tq, t, f), 4.0))*env*0.12
    put(b, w+air, 0, 0.8)
    m = ns(1.4)
    th = tono(1.4, 70, 34, 0.06, 0.35, a=0.003)+0.8*filt(ruido(m, 362)*ad(m, 0.005, 0.25), lp(500, 2))
    th = filt(th, lp(700, 2))
    put(b, th, 2.78, 0.6)
    return reverb(b, 'grande', 0.25)


@reg('Caja', 'sfx', -16, 'Caja registradora y monedas para las ganancias (ka-ching).')
def s_caja():
    b = buf(1.6)
    r = R(371)
    put(b, modal(0.2, [300, 720, 1500], [1, 0.6, 0.3], [0.04, 0.025, 0.012]), 0, 0.6)
    put(b, filt(ruido(ns(0.1), 372), bp(1300, 0.9))*lin([(0, 0), (0.02, 1), (0.1, 0)], ns(0.1)), 0.005, 0.3)
    f = 1568.0
    put(b, modal(1.3, [f, 2.32*f, 3.88*f, 5.1*f, 1.5*f], [1, 0.45, 0.2, 0.07, 0.25], [0.6, 0.3, 0.15, 0.08, 0.4], att=0.001), 0.07, 0.5)
    put(b, modal(1.0, [f*1.26, f*1.26*2.32], [1, 0.4], [0.5, 0.25], att=0.001), 0.14, 0.4)
    for i in range(34):
        t0 = 0.12+0.6*r.uniform()**1.3
        fc = r.uniform(2800, 6200) if i % 3 else r.uniform(1700, 2500)
        put(b, modal(0.25, [fc, fc*1.47, fc*2.09], [1, 0.6, 0.3], [r.uniform(0.03, 0.09), 0.03, 0.015]), t0, 0.16*r.uniform(0.3, 1)*np.exp(-(t0-0.12)/0.5))
    b = filt(b, lp(9000, 2))
    return reverb(b, 'cuarto', 0.12)


def i_metal(f, d, v, brillo=1.0, voces=(-0.004, 0.004), rng=None):
    n = ns(d+0.25)
    t = tt(n)
    rise = 1-np.exp(-t/0.035)
    rel = np.where(t < d, 1.0, np.exp(-(t-d)/0.07))
    fc = f*(1.3+5.0*v*brillo*rise*(0.62+0.38*np.exp(-t/0.25))*(0.4+0.6*rel))
    vib = 1+0.004*np.sin(TAU*5.2*t)*np.clip((t-0.18)/0.25, 0, 1)
    y = np.zeros(n)
    ic = np.unique(np.concatenate([np.arange(0, n, 32), [n-1]]))
    for dt in voces:
        p = fase(f*(1+dt)*vib, n)
        for k in range(1, 60):
            if k*f > 9000:
                break
            a = Mlp(k*f, fc[ic], 2)/k*np.clip((9000-k*f)/2000, 0, 1)
            y += np.interp(np.arange(n), ic, a)*np.sin(k*p+0.3*k)
    env = lin([(0, 0), (0.025, 1.0), (0.12, 0.85), (max(d, 0.13), 0.8), (d+0.25, 0.8)], n)*rel
    return y*env*v/len(voces)


def i_clarinete(f, d, v, fag=False, rng=None):
    n = ns(d+0.12)
    t = tt(n)
    vib = 1+0.005*np.sin(TAU*5.3*t)*np.clip((t-0.12)/0.2, 0, 1)
    p = fase(f*vib, n)
    y = np.zeros(n)
    for k in range(1, 40):
        fk = k*f
        if fk > 9000:
            break
        if fag:
            a = 1/k*(1+1.5*Mbp(fk, 480, 1.0)+0.8*Mbp(fk, 1150, 1.5))*Mlp(fk, 2500, 2)
        else:
            a = (1/k if k % 2 else (0.18 if fk < 1600 else 0.6)/k)*(1+0.6*Mbp(fk, 1450, 1.2))*Mlp(fk, 3800, 1)
        y += a*np.sin(k*p)*np.clip((9000-fk)/2000, 0, 1)
    env = lin([(0, 0), (0.018, 1.05), (0.05, 0.9), (d, 0.85), (d+0.06, 0), (d+0.12, 0)], n)
    ch = filt(ruido(n, int(f*1000+d*77) % 99991)*ad(n, 0.002, 0.012), bp(2500, 1.0))*0.03
    return (y*env+ch)*v


def i_pluck(f, d, v, pos=0.2, tau0=2.0, brill=3500, B=6e-5, rel=0.07, cola=0.7, cuerpo=True, rng=None):
    n = ns(d+cola)
    t = tt(n)
    y = np.zeros(n)
    tau1 = tau0*(196/f)**0.35
    for k in range(1, 70):
        fk = k*f*np.sqrt(1+B*k*k)
        if fk > 12000:
            break
        a = abs(np.sin(np.pi*k*pos))/k*Mlp(fk, brill, 1)
        if cuerpo:
            a *= 1+0.8*Mbp(fk, 210, 2)+0.4*Mbp(fk, 480, 2)
        if a < 2e-4:
            continue
        tau = tau1/(1+(fk/900)**1.25)
        m = min(n, ns(tau*9)+1)
        y[:m] += a*np.sin(TAU*fk*t[:m])*np.exp(-t[:m]/tau)
    damp = np.where(t < d, 1.0, np.exp(-(t-d)/rel))
    return y*damp*np.clip(t/0.0012, 0, 1)*v


def i_contrabajo(f, d, v, rng=None):
    n = ns(d+0.35)
    t = tt(n)
    y = np.zeros(n)
    tau1 = 1.3*(55/f)**0.3
    for k in range(1, 16):
        fk = k*f
        if fk > 3500:
            break
        a = abs(np.sin(np.pi*k*0.14))/k**1.1*Mlp(fk, 650, 2)
        tau = tau1/(1+(fk/260)**1.3)
        y += a*np.sin(TAU*fk*t)*np.exp(-t/tau)
    th = filt(ruido(n, int(f*97+d*13) % 99991)*ad(n, 0.001, 0.008), lp(350, 2))*0.25
    damp = np.where(t < d, 1.0, np.exp(-(t-d)/0.06))
    return (y+th)*damp*np.clip(t/0.002, 0, 1)*v


def i_pizz(f, d, v, rng=None):
    return i_pluck(f, min(d, 0.5), v, pos=0.25, tau0=0.55, brill=2200, rel=0.05, cola=0.5, cuerpo=True)


def i_synthbajo(f, d, v, rng=None):
    n = ns(d+0.08)
    t = tt(n)
    fc = np.minimum(f*(1.6+9*v*np.exp(-t/0.05)), 5000)
    p = fase(f, n)
    y = np.zeros(n)
    ic = np.unique(np.concatenate([np.arange(0, n, 32), [n-1]]))
    for k in range(1, 50):
        if k*f > 7000:
            break
        a = Mlp(k*f, fc[ic], 2)/k
        y += np.interp(np.arange(n), ic, a)*np.sin(k*p)
    y += 0.5*np.sin(p)
    env = lin([(0, 0), (0.003, 1), (0.12, 0.75), (d, 0.7), (d+0.04, 0), (d+0.08, 0)], n)
    return y*env*v


def i_vibes(f, d, v, rng=None):
    tau = 2.2*(523/f)**0.3
    n = ns(min(d+1.2, 3.0))
    t = tt(n)
    x = modal(n/SR, [f, 4.0*f, 10.0*f], [1, 0.2, 0.035], [tau, tau*0.2, 0.07], att=0.0015)
    trem = 1-0.2*(0.5-0.5*np.cos(TAU*5.0*t))
    damp = np.where(t < d+0.08, 1.0, np.exp(-(t-d-0.08)/0.22))
    mal = filt(ruido(n, int(f*31) % 9999)*ad(n, 0.0005, 0.003), bp(min(3*f, 6000), 1.0))*0.04
    return (x*trem*damp+mal)*v


def i_celesta(f, d, v, rng=None):
    n = ns(min(d+0.8, 2.0))
    x = modal(n/SR, [f, 2.0*f, 3.0*f, 4.1*f], [1, 0.35, 0.08, 0.05], [0.7, 0.25, 0.12, 0.07], att=0.001)
    return x*v


def i_marimba(f, d, v, rng=None):
    tau = min(0.6, 0.45*(440/f)**0.6)
    n = ns(tau*5+0.02)
    x = modal(n/SR, [f, 3.93*f, 9.2*f], [1, 0.28, 0.05], [tau, tau/5, tau/12], att=0.001)
    mal = filt(ruido(n, int(f*7) % 9999)*ad(n, 0.0005, 0.002), bp(min(4*f, 6000), 1.0))*0.05
    return (x+mal)*v


def i_epiano(f, d, v, rng=None):
    n = ns(d+0.9)
    t = tt(n)
    sc = min(1.0, 330/f)**0.5
    I = (0.5+1.2*v)*sc*np.exp(-t/0.35)+0.18*sc
    car = np.sin(TAU*f*t+I*np.sin(TAU*f*t))
    tine = np.sin(TAU*f*7.0*t)*np.exp(-t/0.02)*0.1*v if 7*f < 15000 else 0
    env = np.exp(-t/(2.2*(261/f)**0.5))*np.clip(t/0.002, 0, 1)
    damp = np.where(t < d, 1.0, np.exp(-(t-d)/0.12))
    return (car+tine)*env*damp*v


def i_cuerdas(f, d, v, trem=0.0, rng=None):
    n = ns(d+0.4)
    t = tt(n)
    y = np.zeros(n)
    for j, dt in enumerate((-0.0055, 0.0, 0.0055)):
        vib = 1+0.003*np.sin(TAU*(5.0+0.4*j)*t+j)
        p = fase(f*(1+dt)*vib, n)
        for k in range(1, 50):
            fk = k*f
            if fk > 7000:
                break
            a = 1/k*Mlp(fk, 2600, 2)*(1+0.6*Mbp(fk, 1000, 1.0))
            y += a*np.sin(k*p+1.3*k*j)
    env = lin([(0, 0), (0.14, 1), (d, 1), (d+0.35, 0), (d+0.4, 0)], n)
    if trem > 0:
        env *= 0.5+0.5*(0.5-0.5*np.cos(TAU*trem*t))
    return y*env*v/3


def d_bombo(v, rng=None):
    n = ns(0.42)
    t = tt(n)
    f = 46+95*np.exp(-t/0.032)
    y = np.sin(fase(f, n))*ad(n, 0.001, 0.16)
    y += 0.12*filt(ruido(n, 1)*ad(n, 0.0002, 0.003), lp(3500, 1))
    return y*v


def d_caja(v, rng):
    n = ns(0.3)
    t = tt(n)
    tn = (np.sin(fase(185+40*np.exp(-t/0.01), n))+0.4*np.sin(fase(330, n)))*ad(n, 0.001, 0.05)
    nz = filt(rng.standard_normal(n)*ad(n, 0.0008, 0.1), mul(hp(1100, 2), lp(8000, 2), pk(4000, 1, 3)))
    return (0.6*tn+0.9*nz)*v


def d_aro(v, rng):
    x = modal(0.1, [1650, 2480, 3920, 820], [1, 0.6, 0.3, 0.4], [0.018, 0.011, 0.006, 0.012])
    put(x, rafaga(0.01, 0.0001, 0.001, bp(3000, 1), int(rng.integers(1e6))), 0, 0.3)
    return x*v


def d_shaker(v, rng):
    n = ns(0.09)
    return filt(rng.standard_normal(n)*ad(n, 0.007, 0.028), mul(hp(3500, 2), lp(8000, 2)))*v


def d_hat(v, rng, abierto=False):
    n = ns(0.5 if abierto else 0.09)
    t = tt(n)
    nz = filt(rng.standard_normal(n), mul(hp(6000, 2), lp(10500, 2)))
    met = sum(np.sin(TAU*fr*t) for fr in (3140, 4410, 5310, 6280, 7150, 8370))/6
    met = filt(met, hp(6000, 2))
    return (nz+0.6*met)*ad(n, 0.0005, 0.18 if abierto else 0.025)*v


def d_crash(v, rng):
    n = ns(2.0)
    t = tt(n)
    nz = filt(rng.standard_normal(n), mul(hp(3500, 2), lp(11000, 2)))
    met = sum(np.sin(TAU*fr*t+rng.uniform(0, 6)) for fr in rng.uniform(2500, 7500, 14))/14
    return (nz+0.5*met)*ad(n, 0.002, 0.75)*v


def d_tom(f, v, rng=None):
    n = ns(0.45)
    t = tt(n)
    y = np.sin(fase(f*(1+0.45*np.exp(-t/0.03)), n))*ad(n, 0.001, 0.2)
    y += 0.2*filt(ruido(n, int(f) % 999)*ad(n, 0.0005, 0.015), lp(1500, 1))
    return y*v


def d_palmas(v, rng):
    n = ns(0.3)
    y = np.zeros(n)
    for i, t0 in enumerate([0.0, 0.009, 0.018, 0.026]):
        y += ad(n, 0.0005, 0.006 if i < 3 else 0.09, t0)*(1.0 if i < 3 else 0.8)
    return filt(rng.standard_normal(n)*y, mul(bp(1300, 1.1), lp(6000, 2)))*v


def d_bloque(v, rng=None, f=880):
    return modal(0.12, [f, f*2.71, f*0.5], [1, 0.4, 0.15], [0.035, 0.015, 0.02])*v


def d_conga(v, rng=None, f=215):
    n = ns(0.35)
    t = tt(n)
    y = np.sin(fase(f*(1+0.18*np.exp(-t/0.02)), n))*ad(n, 0.001, 0.13)
    y += 0.25*np.sin(fase(f*1.52, n))*ad(n, 0.001, 0.05)
    return y*v


@reg('Victoria', 'sfx', -15, 'Fanfarria corta original de éxito (~2,5 s), Fa mayor.')
def s_victoria():
    b = buf(3.4, st=True)
    rng = R(381)
    mel = [(0.0, 0.1, 65), (0.12, 0.1, 69), (0.24, 0.1, 72), (0.36, 0.2, 76), (0.6, 0.13, 74), (0.76, 0.13, 79), (0.94, 1.35, 77)]
    for t0, d, m in mel:
        put(b, pan(i_metal(m2f(m), d, 0.9, 1.1), 0.0), t0, 0.55)
    for t0, d, notas, bajo in [(0.0, 0.34, [57, 60, 65], 41), (0.36, 0.38, [58, 62, 65], 43), (0.76, 0.16, [58, 64, 67], 36), (0.94, 1.35, [57, 60, 64, 69], 41)]:
        for j, m in enumerate(notas):
            put(b, pan(i_metal(m2f(m), d, 0.55, 0.8, voces=(-0.006, 0.0, 0.005)), -0.5+j*0.35), t0+0.004*j, 0.22)
        put(b, pan(i_pizz(m2f(bajo), d, 1.0), 0.0), t0, 0.5)
    for t0, v in [(0.0, 0.5), (0.36, 0.45), (0.76, 0.5), (0.94, 1.0)]:
        put(b, pan(d_bombo(v), 0), t0, 0.5)
    put(b, pan(d_crash(0.6, rng), 0.3), 0.94, 0.14)
    for i in range(6):
        put(b, pan(d_caja(0.25+0.08*i, rng), -0.1), 0.76+i*0.028, 0.25)
    put(b, pan(i_celesta(m2f(89), 0.5, 0.5), 0.4), 0.94, 0.12)
    put(b, pan(i_celesta(m2f(93), 0.5, 0.5), -0.4), 1.02, 0.1)
    return reverb(b, 'estudio', 0.22)


@reg('Derrota', 'sfx', -15, 'Jingle corto original de fracaso (~2,5 s), cómico y descendente.')
def s_derrota():
    b = buf(3.4, st=True)
    rng = R(391)
    for t0, d, m in [(0.0, 0.17, 69), (0.24, 0.17, 65), (0.48, 0.17, 62)]:
        put(b, pan(i_clarinete(m2f(m-12), d, 0.9, fag=True), 0.0), t0, 0.6)
    n = ns(1.9)
    t = tt(n)
    f = m2f(61-12)*expi([(0, 1.0), (0.7, 1.0), (1.5, 2**(-1.1/12)), (1.9, 2**(-1.2/12))], n)*(1+0.012*np.sin(TAU*5.0*t)*np.clip((t-0.3)/0.4, 0, 1))
    p = fase(f, n)
    y = np.zeros(n)
    for k in range(1, 40):
        if k*f.max() > 8000:
            break
        a = 1/k*(1+1.5*Mbp(k*f[0], 480, 1.0)+0.8*Mbp(k*f[0], 1150, 1.5))*Mlp(k*f[0], 2200, 2)
        y += a*np.sin(k*p)
    y *= lin([(0, 0), (0.03, 1), (1.2, 0.8), (1.9, 0)], n)
    put(b, pan(y, 0.0), 0.74, 0.6)
    for t0, d, m in [(0.0, 0.66, 38), (0.74, 1.6, 33)]:
        put(b, pan(i_clarinete(m2f(m), d, 0.8, fag=True), 0.0), t0, 0.35)
    for t0, notas in [(0.0, [57, 62, 65]), (0.74, [55, 61, 64, 70])]:
        for j, m in enumerate(notas):
            put(b, pan(i_pizz(m2f(m), 0.3, 0.6), -0.4+0.3*j), t0+0.01*j, 0.25)
    put(b, pan(d_tom(90, 0.8), 0), 2.25, 0.4)
    put(b, pan(d_bombo(0.6), 0), 2.25, 0.4)
    return reverb(b, 'estudio', 0.2)


@reg('Despegue', 'sfx', -14, 'Motor acelerando para el despegue (~5 s): silbido de turbina y rugido.')
def s_despegue():
    D = 5.2
    n = ns(D)
    t = tt(n)
    N = 0.3+0.7*suave(np.clip(t/3.9, 0, 1))
    roar = stft(ruido(n, 401), lambda tq, f: Mlp(f, 180+2600*np.interp(tq, t, N)**2.2, 2)*Mhp(f, 30, 2)*Mtilt(f, -2.0, 300))
    roar *= N**2.2
    rum = filt(ruido(n, 402), lp(110, 3))*N**1.5
    fb = 52*N
    p = fase(fb, n)
    core = np.zeros(n)
    for k in range(1, 25):
        core += (1/k)*Mlp(k*52, 700, 2)*np.sin(k*p+k*1.1)
    fw = 520+1150*N
    pw = fase(fw, n)
    whine = np.sin(pw)+0.3*np.sin(2*pw)+0.2*np.sin(fase(fw*1.013, n))
    whine *= 0.05*(0.3+0.7*N)
    x = 1.0*roar/np.abs(roar).max()+0.5*rum/np.abs(rum).max()+0.3*core*N**1.5/np.abs(core).max()+whine
    x *= lin([(0, 0), (0.15, 1), (D-0.7, 1), (D, 0)], n)
    return x


@reg('Aterrizaje', 'sfx', -14, 'Aterrizaje (~2 s): chirrido de neumáticos, golpe del tren y rodadura.')
def s_aterrizaje():
    b = buf(2.4)
    r = R(411)
    for t0, a in [(0.0, 1.0), (0.33, 0.6)]:
        put(b, tono(0.4, 85, 40, 0.03, 0.12), t0, a)
        put(b, rafaga(0.15, 0.001, 0.05, lp(650, 2), 412+int(t0*10)), t0, 0.7*a)
    for t0, d, a in [(0.02, 0.42, 1.0), (0.35, 0.28, 0.6)]:
        n = ns(d)
        t = tt(n)
        f = (1350+250*np.exp(-t/0.1))*(1+0.04*np.interp(t, np.linspace(0, d, int(d*180)), r.standard_normal(int(d*180))))
        sq = np.sin(fase(f, n))+0.3*np.sin(fase(2*f, n))
        sq += 0.6*filt(ruido(n, 415+int(t0*10)), bp(1500, 2.5))
        sq *= ad(n, 0.006, d*0.3)
        put(b, filt(sq, lp(3800, 2)), t0, 0.45*a)
    n = ns(2.3)
    roll = filt(ruido(n, 420), mul(lp(420, 2), hp(70, 2), pk(180, 1.0, 4)))*lin([(0, 0), (0.05, 1), (1.6, 0.6), (2.3, 0)], n)
    roll *= 1+0.25*np.sin(TAU*11*tt(n))
    put(b, roll, 0.03, 0.8)
    for t0 in [0.85, 1.35, 1.8]:
        put(b, tono(0.2, 90, 55, 0.02, 0.05), t0, 0.25)
    return reverb(b, 'cuarto', 0.08)


def pasos(s):
    r = R(s)
    b = buf(0.32)
    f = r.uniform(80, 105)
    put(b, tono(0.2, f*1.6, f, 0.015, 0.03), 0, 0.6)
    put(b, rafaga(0.15, 0.002, r.uniform(0.02, 0.03), mul(lp(r.uniform(500, 750), 2), hp(60, 1)), s+1), 0, 1.0)
    dt = r.uniform(0.055, 0.08)
    put(b, rafaga(0.12, 0.002, 0.022, mul(lp(r.uniform(800, 1100), 2), hp(80, 1)), s+2), dt, 0.55)
    put(b, rafaga(0.1, 0.006, 0.025, mul(bp(r.uniform(2000, 3000), 1.0), lp(5000, 2)), s+3), dt*0.8, 0.07)
    return b


for _i in (1, 2, 3):
    reg(f'Pasos{_i}', 'sfx', -21, f'Paso sobre moqueta, variante {_i}.')(lambda s=_i: pasos(420+s*10))


@reg('UiClick', 'sfx', -20, 'Clic suave de interfaz.')
def s_uiclick():
    b = buf(0.1)
    n = ns(0.08)
    put(b, np.sin(fase(expi([(0, 1500), (0.03, 1050)], n), n))*ad(n, 0.0008, 0.012), 0, 1.0)
    put(b, modal(0.05, [2900, 620], [0.15, 0.3], [0.004, 0.006]), 0, 1.0)
    return filt(b, lp(7000, 1))


@reg('UiAviso', 'sfx', -18, 'Notificación (toast): blip de dos notas ascendentes.')
def s_uiaviso():
    b = buf(0.55)
    for t0, m in [(0.0, 79), (0.09, 86)]:
        f = m2f(m)
        put(b, modal(0.45, [f, 4.0*f, 2.0*f], [1, 0.12, 0.1], [0.14, 0.02, 0.05], att=0.0015), t0, 0.8)
    return filt(b, lp(8000, 1))


@reg('UiPeligro', 'sfx', -17, 'Aviso de peligro (toast): dos golpes graves disonantes.')
def s_uipeligro():
    b = buf(0.75)
    for t0, notas, a in [(0.0, (62, 68), 1.0), (0.17, (61, 67), 0.9)]:
        for m in notas:
            f = m2f(m)
            n = ns(0.45)
            t = tt(n)
            p = fase(f, n)
            y = np.zeros(n)
            for k in range(1, 30, 2):
                if k*f > 5000:
                    break
                y += Mlp(k*f, 1700, 2)/k*np.sin(k*p)
            put(b, y*ad(n, 0.004, 0.11), t0, 0.45*a)
        put(b, tono(0.2, 120, 70, 0.02, 0.05), t0, 0.35*a)
    return reverb(b, 'cuarto', 0.1)


def periodico(n, fc, s, lo=1.0):
    x = filt(ruido(n, s), lambda f: Mlp(f, fc, 2)*Mhp(f, lo/(n/SR)*0.5, 1), 'circ')
    return x/np.std(x)


@reg('MotorAvion', 'loop', -24, 'Bucle de motores bimotor (turbohélice/turbofán), dron grave; admite cambiar PlaybackSpeed.')
def l_motor():
    n = nl(8.0)
    t = tt(n)
    r = R(501)
    y = np.zeros(n)
    for fb, s, g in [(fq(57.0, n), 502, 1.0), (fq(57.5, n), 503, 0.85)]:
        ph0 = r.uniform(0, TAU, 40)
        for k in range(1, 40):
            fk = k*fb
            if fk > 4000:
                break
            a = (1/k**1.05)*Mlp(fk, 650, 1)*(1.3 if k in (2, 4) else 1.0)*(1+1.2*Mbp(fk, 260, 0.8))
            y += g*a*np.sin(TAU*fk*t+ph0[k])
    thr = 1+0.12*np.sin(TAU*fq(14.25, n)*t)
    y *= thr
    wh = 0
    for fw, a in [(fq(1630, n), 1.0), (fq(1646, n), 0.8), (fq(3262, n), 0.25)]:
        wh = wh+a*np.sin(TAU*fw*t+r.uniform(0, TAU))
    roar = filt(ruido(n, 504), mul(Mtilt_f(-3.0, 200), lp(2600, 2), hp(60, 2)), 'circ')
    rum = filt(ruido(n, 505), mul(lp(85, 3), hp(22, 2)), 'circ')
    mod = 1+0.08*np.sin(TAU*fq(0.25, n)*t)+0.05*periodico(n, 1.5, 506)*0.3
    x = 0.55*y/np.std(y)+0.05*wh+0.75*roar/np.std(roar)*mod+0.22*rum/np.std(rum)
    return x


def Mtilt_f(d, f0): return lambda f: Mtilt(f, d, f0)


@reg('VientoCabina', 'loop', -21, 'Bucle de viento que entra a chorro (puerta abierta o brecha en el casco).')
def l_viento_cabina():
    n = nl(10.0)
    t = tt(n)
    base = filt(ruido(n, 511), mul(Mtilt_f(-3.0, 500), hp(140, 2), lp(4500, 2)), 'circ')
    g = periodico(n, 1.2, 512)
    gust = 0.75+0.25*np.tanh(g*0.8)+0.06*np.sin(TAU*fq(0.6, n)*t)
    cen = lambda tq: 700+180*np.sin(TAU*fq(0.2, n)*tq)+90*np.sin(TAU*fq(0.5, n)*tq+1)
    wh = stft(ruido(n, 513), lambda tq, f: Mbp(f, cen(tq), 14)+0.5*Mbp(f, cen(tq)*1.62, 18), circ=True)
    buff = filt(ruido(n, 514), lp(110, 3), 'circ')*(1+0.5*np.sin(TAU*fq(7.0, n)*t))
    x = base/np.std(base)*gust+0.45*wh/np.std(wh)*gust**2+0.5*buff/np.std(buff)
    return x


@reg('VientoExterior', 'loop', -22, 'Bucle estéreo de viento fuerte en el exterior (sobre el ala).')
def l_viento_exterior():
    n = nl(12.0)
    t = tt(n)
    g = periodico(n, 0.8, 521)
    chans = []
    for c in range(2):
        base = filt(ruido(n, 522+c), mul(Mtilt_f(-3.0, 300), hp(70, 2), lp(3200, 2)), 'circ')
        gl = periodico(n, 1.5, 524+c)
        gust = 0.7+0.2*np.tanh(g)+0.1*np.tanh(gl)
        buff = filt(ruido(n, 526+c), mul(lp(90, 3), hp(18, 2)), 'circ')*(1+0.6*periodico(n, 9.0, 528+c)*0.5)
        cen = lambda tq, c=c: 950+250*np.sin(TAU*fq(0.15, n)*tq+c)
        wh = stft(ruido(n, 530+c), lambda tq, f: Mbp(f, cen(tq), 10)+0.6*Mbp(f, cen(tq)*1.47, 14), circ=True)
        x = base/np.std(base)*gust+0.45*buff/np.std(buff)+0.3*wh/np.std(wh)*gust**2
        chans.append(x)
    common = filt(ruido(n, 535), lp(120, 3), 'circ')
    common /= np.std(common)
    return np.stack([chans[0]+0.25*common, chans[1]+0.25*common], 1)


@reg('Alarma', 'loop', -21, 'Bucle de aviso maestro de cabina: doble pitido "bi-bo", grave y no estridente.')
def l_alarma():
    n = ns(1.0)
    y = np.zeros(n)
    for t0, f in [(0.0, 698.46), (0.2, 587.33)]:
        m = ns(0.16)
        t = tt(m)
        p = TAU*f*t
        s = np.sin(p)+0.16*np.sin(3*p)+0.07*np.sin(2*p)+0.04*np.sin(5*p)
        env = np.clip(t/0.01, 0, 1)*np.clip((0.16-t)/0.015, 0, 1)
        env = np.sin(0.5*np.pi*env)**2
        put(y, s*env, ns(t0))
    return y


@reg('FuegoLoop', 'loop', -23, 'Bucle de fuego crepitante.')
def l_fuego():
    n = nl(8.0)
    r = R(541)
    fl = periodico(n, 3.0, 542)
    fl2 = periodico(n, 0.7, 543)
    roar = filt(ruido(n, 544), mul(lp(420, 2), hp(50, 2), pk(160, 0.8, 4)), 'circ')
    roar = roar/np.std(roar)*(0.75+0.18*np.tanh(fl)+0.12*np.tanh(fl2))
    hiss = filt(ruido(n, 545), mul(hp(3000, 2), lp(9000, 2)), 'circ')
    hiss = hiss/np.std(hiss)*(0.5+0.5*np.tanh(fl)**2)
    cr = np.zeros(n)
    T = n/SR
    for i in range(int(T*26)):
        t0 = r.uniform(0, T)
        d = r.uniform(0.0005, 0.003)
        x = filt(r.standard_normal(ns(0.02))*ad(ns(0.02), 0.0001, d), bp(r.uniform(1500, 6000), 1.2))
        put(cr, x, t0, r.lognormal(0, 0.6), wrap=True)
    for i in range(int(T*4)):
        t0 = r.uniform(0, T)
        x = filt(r.standard_normal(ns(0.04))*ad(ns(0.04), 0.0002, 0.004), bp(r.uniform(600, 1800), 1.0))
        put(cr, x, t0, 2.2*r.uniform(0.5, 1), wrap=True)
    for i in range(int(T*1.5)):
        t0 = r.uniform(0, T)
        for j in range(int(r.integers(5, 14))):
            x = filt(r.standard_normal(ns(0.01))*ad(ns(0.01), 0.0001, 0.0008), bp(r.uniform(2500, 7000), 1.5))
            put(cr, x, t0+r.uniform(0, 0.04), 0.7*r.uniform(0.3, 1), wrap=True)
    cr = filt(cr, lp(9000, 2), 'circ')
    return roar+0.08*hiss+0.9*cr/np.abs(cr).max()*np.abs(roar).max()*0.55


@reg('Lluvia', 'loop', -25, 'Bucle estéreo de lluvia de tormenta golpeando el fuselaje.')
def l_lluvia():
    n = nl(12.0)
    r = R(551)
    T = n/SR
    out = []
    km = ns(0.03)
    kern_s = [filt(r.standard_normal(km)*ad(km, 0.0001, 0.0012), mul(bp(fc, 0.9), lp(8000, 2))) for fc in (2200, 3300, 4600)]
    kern_b = modal(0.06, [1450, 2380, 3720, 430], [1, 0.6, 0.3, 0.6], [0.007, 0.005, 0.003, 0.012])
    for c in range(2):
        x = np.zeros(n)
        for k in kern_s:
            imp = np.zeros(n)
            m = int(T*650)
            np.add.at(imp, r.integers(0, n, m), r.exponential(1.0, m)**1.3)
            x += conv(imp, k, circ=True)
        imp = np.zeros(n)
        m = int(T*45)
        np.add.at(imp, r.integers(0, n, m), r.uniform(0.5, 1.0, m)*3)
        x += conv(imp, kern_b, circ=True)
        wash = filt(r.standard_normal(n), mul(hp(400, 2), lp(6500, 2), Mtilt_f(-2.0, 1000)), 'circ')
        hull = filt(r.standard_normal(n), mul(lp(170, 3), hp(30, 2)), 'circ')
        gust = 0.85+0.15*np.tanh(periodico(n, 0.5, 560+c))
        x = (x/np.std(x)*0.8+0.7*wash/np.std(wash))*gust+0.5*hull/np.std(hull)
        out.append(filt(x, mul(lp(8500, 2), pk(3800, 1.0, -3)), 'circ'))
    return np.stack(out, 1)


def jerga_stream(dur, s, f0b):
    r = R(s)
    sils_all = []
    t = r.uniform(0.3, 1.0)
    voc = 'aeiou@'
    cons = ['', 'b', 'm', 'n', 'h', 'w', 'g', '']
    while t < dur-1.5:
        nsil = int(r.integers(3, 11))
        sils = []
        f0 = f0b*r.uniform(1.05, 1.2)
        for i in range(nsil):
            d = r.uniform(0.11, 0.24)
            f1 = f0*r.uniform(0.92, 1.06)
            sils.append((r.choice(cons), r.choice(list(voc)), d, f0, f1, r.uniform(0.6, 1.0)))
            f0 = max(f0b*0.8, f1*0.985)
        sils_all.append((t, sils))
        t += sum(x[2] for x in sils)+0.015*nsil+r.uniform(0.4, 1.6)
    return sils_all


@reg('AmbienteTerminal', 'loop', -28, 'Bucle estéreo de tono de sala de terminal con murmullo lejano.')
def l_terminal():
    n = nl(20.0)
    T = n/SR
    r = R(571)
    room = np.stack([filt(ruido(n, 572+c), mul(Mtilt_f(-3, 200), lp(1200, 2), hp(40, 2)), 'circ') for c in range(2)], 1)
    room /= np.std(room)
    mur = np.zeros((n, 2))
    for v in range(9):
        f0b = r.choice([105, 120, 135, 190, 210, 230])*r.uniform(0.92, 1.08)
        esc = 1.0 if f0b < 160 else 1.15
        p = r.uniform(-0.8, 0.8)
        g = r.uniform(0.5, 1.0)
        for t0, sils in jerga_stream(T, 580+v, f0b):
            f0, F, A, nz, m = jerga(sils, esc, t0=0.02)
            y = voz(f0, F, (100, 130, 180, 260), A, 1.1, 3000, 600+v, 0.01)
            put(mur, pan(y, p), t0, g, wrap=True)
    mur = filt(mur, mul(lp(1800, 2), hp(150, 2)), 'circ')
    mur /= np.std(mur)
    ev = np.zeros((n, 2))
    for k in range(10):
        t0 = 2.0+k*0.55+r.uniform(-0.03, 0.03)
        x = modal(0.08, [2300, 3900, 1200], [1, 0.4, 0.6], [0.012, 0.006, 0.01])
        put(ev, pan(x, -0.6+0.12*k), t0, 0.5*np.sin(np.pi*(k+0.5)/10), wrap=True)
    m = ns(3.0)
    tm = tt(m)
    rodar = filt(ruido(m, 590), mul(lp(500, 2), hp(80, 2)))*(1+0.5*np.sin(TAU*7*tm))*np.sin(np.pi*tm/3.0)**2
    put(ev, pan(rodar, 0.5), 11.0, 0.6, wrap=True)
    put(ev, pan(modal(0.5, [2637, 3950, 5270], [1, 0.4, 0.2], [0.25, 0.12, 0.06]), -0.3), 15.2, 0.2, wrap=True)
    ev = filt(ev, lp(2500, 2), 'circ')
    ev /= np.std(ev)+1e-9
    wet = conv(mur*1.0+ev*0.25, IR('hall'), circ=True)
    x = 0.6*room+0.35*mur+0.9*wet/np.std(wet)*0.45+0.05*ev
    return x


@reg('AmbienteCabina', 'loop', -28, 'Bucle estéreo del interior de cabina: zumbido de motores y ventilación.')
def l_cabina():
    n = nl(15.0)
    t = tt(n)
    r = R(611)
    air = np.stack([filt(ruido(n, 612+c), mul(Mtilt_f(-3.5, 300), hp(70, 2), lp(5000, 2)), 'circ') for c in range(2)], 1)
    air = air[:, [0, 1]]*0.8+0.2*air[:, ::-1]
    air /= np.std(air)
    hum = np.zeros(n)
    for fb, g in [(fq(57.0, n), 1.0), (fq(57.5, n), 0.8)]:
        for k in range(1, 10):
            hum += g*(1/k)*Mlp(k*fb, 220, 2)*np.sin(TAU*k*fb*t+r.uniform(0, TAU))
    hum /= np.std(hum)
    el = np.sin(TAU*400*t)+0.3*np.sin(TAU*800*t+1)
    rum = filt(ruido(n, 615), mul(lp(70, 3), hp(20, 2)), 'circ')
    rum /= np.std(rum)
    mono = 0.5*hum+0.012*el+0.28*rum
    return 0.8*air+np.stack([mono, mono], 1)


def render_musica(bpm, compases, eventos, ir, enviar, s):
    spb = 60.0/bpm
    L = ns(compases*4*spb)
    rng = R(s)
    dry = np.zeros((L, 2))
    wet = np.zeros((L, 2))
    for (beat, durb, inst, nota, vel, p, snd) in eventos:
        fn = INST[inst]
        j = rng.normal(0, 0.003) if inst[0] != 'd' else rng.normal(0, 0.0015)
        v = vel*(1+rng.normal(0, 0.05))
        if nota is None:
            x = fn(v, rng)
        else:
            x = fn(m2f(nota), durb*spb, v)
        st = pan(x*MIXG.get(inst, 1.0), p)
        i0 = int(round((beat*spb+j)*SR)) % L
        put(dry, st, i0, wrap=True)
        if snd > 0:
            put(wet, st*snd, i0, wrap=True)
    wet = conv(wet, IR(ir), circ=True)
    return dry+enviar*wet


INST = {'vib': i_vibes, 'cel': i_celesta, 'nyl': lambda f, d, v: i_pluck(f, d, v), 'ctb': i_contrabajo,
        'epi': i_epiano, 'mar': i_marimba, 'cla': i_clarinete, 'fag': lambda f, d, v: i_clarinete(f, d, v, fag=True),
        'pzb': i_pizz, 'sbj': i_synthbajo, 'brs': lambda f, d, v: i_metal(f, d, v, 1.0),
        'brl': lambda f, d, v: i_metal(f, d, v, 1.2, voces=(-0.003, 0.003)),
        'str': lambda f, d, v: i_cuerdas(f, d, v), 'stt': lambda f, d, v: i_cuerdas(f, d, v, trem=10.0),
        'dbo': d_bombo, 'dca': d_caja, 'dar': d_aro, 'dsh': d_shaker, 'dhc': d_hat,
        'dho': lambda v, r: d_hat(v, r, True), 'dcr': d_crash, 'dpa': d_palmas, 'dbl': d_bloque,
        'dbh': lambda v, r: d_bloque(v, r, 1240), 'dcg': d_conga, 'dcl': lambda v, r: d_conga(v, r, 300),
        'dt1': lambda v, r: d_tom(165, v), 'dt2': lambda v, r: d_tom(125, v), 'dt3': lambda v, r: d_tom(92, v)}

MIXG = {}


def quinta(r, vc=None):
    iv = 7
    if vc is not None:
        pcs = {m % 12 for m in vc}
        for c in (7, 6, 8, 3, 4):
            if (r+c) % 12 in pcs:
                iv = c
                break
    return r+iv if r+iv <= 47 else r+iv-12


def acorde_en(prog, bar, beat):
    segs = prog[bar % len(prog)]
    cur = segs[0]
    for s in segs:
        if s[0] <= beat:
            cur = s
    return cur


AERO = [[(0, 41, [57, 60, 64, 67])], [(0, 39, [55, 61, 65, 70])], [(0, 38, [53, 57, 60, 64])], [(0, 37, [53, 56, 60, 63])],
        [(0, 43, [58, 62, 65, 69])], [(0, 36, [58, 62, 65, 67]), (2, 36, [58, 61, 64, 67])],
        [(0, 45, [55, 60, 64, 69]), (2, 38, [54, 60, 63, 69])], [(0, 43, [58, 62, 65, 69]), (2, 36, [58, 64, 67, 69])],
        [(0, 41, [57, 60, 64, 67])], [(0, 39, [55, 61, 65, 70])], [(0, 38, [53, 57, 60, 64])], [(0, 37, [53, 56, 60, 63])],
        [(0, 34, [57, 62, 65, 70])], [(0, 34, [55, 61, 65, 70])],
        [(0, 45, [55, 60, 64, 69]), (2, 44, [56, 59, 62, 65])], [(0, 43, [53, 58, 62, 67]), (2, 36, [58, 61, 64, 67])]]

AERO_MEL = [
    [(0.5, .5, 72), (1, .5, 76), (1.5, 1.5, 81), (3, .5, 79), (3.5, .5, 76)],
    [(0, 1.5, 77), (1.5, .5, 75), (2, .5, 73), (2.5, 1.5, 70)],
    [(0.5, .5, 69), (1, .5, 72), (1.5, 1, 76), (2.5, .5, 74), (3, 1, 77)],
    [(0, 1, 80), (1, .5, 79), (1.5, 2, 77)],
    [(0.5, .5, 74), (1, .5, 77), (1.5, 1.5, 81), (3, .5, 79), (3.5, .5, 77)],
    [(0, 1.5, 79), (1.5, .5, 77), (2, .5, 76), (2.5, 1.5, 73)],
    [(0, 1, 72), (1, .5, 76), (1.5, .5, 79), (2, 1, 78), (3, 1, 75)],
    [(0, 1.5, 74), (1.5, .5, 70), (2, 2, 76)],
    [(0.5, .5, 72), (1, .5, 76), (1.5, 1, 81), (2.5, .5, 84), (3, 1, 81)],
    [(0, .5, 82), (0.5, .5, 79), (1, 1, 77), (2, .5, 75), (2.5, 1.5, 77)],
    [(0.5, .5, 74), (1, .5, 77), (1.5, .5, 81), (2, 1.5, 84), (3.5, .5, 81)],
    [(0, 1, 80), (1, .5, 79), (1.5, .5, 77), (2, 2, 72)],
    [(0.5, .5, 74), (1, .5, 77), (1.5, 1.5, 81), (3, 1, 79)],
    [(0, 1.5, 77), (1.5, .5, 73), (2, 2, 79)],
    [(0, 1, 76), (1, .5, 72), (1.5, .5, 76), (2, 1, 77), (3, 1, 74)],
    [(0, 1, 70), (1, .5, 74), (1.5, 1, 79), (2.5, 1.5, 76)]]


@reg('MusicaAeropuerto', 'musica', -24, 'Música original del aeropuerto: lounge/bossa relajada y peculiar, Fa mayor, 100 BPM, 16 compases.')
def m_aeropuerto():
    MIXG.clear()
    MIXG.update({'nyl': 0.23, 'ctb': 0.75, 'vib': 0.5, 'epi': 0.22, 'cel': 0.16, 'dsh': 0.55, 'dar': 0.6, 'dbo': 0.6, 'dcg': 0.55, 'dcl': 0.45})
    ev = []
    r = R(701)
    for bar in range(16):
        b0 = bar*4
        for (st, root, vc) in AERO[bar]:
            ln = (2 if len(AERO[bar]) > 1 else 4)
            if ln == 4:
                ev += [(b0+st, 1.4, 'ctb', root, 0.9, 0.0, 0.08), (b0+st+1.5, 0.45, 'ctb', quinta(root, vc), 0.7, 0.0, 0.08),
                       (b0+st+2, 1.4, 'ctb', quinta(root, vc), 0.8, 0.0, 0.08), (b0+st+3.5, 0.45, 'ctb', root, 0.65, 0.0, 0.08)]
            else:
                ev += [(b0+st, 1.4, 'ctb', root, 0.9, 0.0, 0.08), (b0+st+1.5, 0.45, 'ctb', quinta(root, vc), 0.7, 0.0, 0.08)]
            for j, m in enumerate(vc):
                ev.append((b0+st, ln-0.1, 'epi', m, 0.35, -0.3+0.2*j, 0.35))
        pos = [0, 1.0, 2.5, 3.5] if bar % 2 == 0 else [0.5, 2.0, 3.0]
        for q in pos:
            _, root, vc = acorde_en(AERO, bar, q)
            for j, m in enumerate(vc):
                ev.append((b0+q+0.009*j, 0.45, 'nyl', m, 0.75 if q in (0, 2.0) else 0.6, -0.35+0.08*j, 0.3))
        for i in range(16):
            ev.append((b0+i*0.25, 0.1, 'dsh', None, [0.9, 0.45, 0.65, 0.45][i % 4], 0.45, 0.15))
        clave = [0, 1.5, 3] if bar % 2 == 0 else [1.0, 2.5]
        for q in clave:
            ev.append((b0+q, 0.1, 'dar', None, 0.8, -0.2, 0.2))
        for q, v in [(0, 0.8), (1.5, 0.4), (2, 0.7), (3.5, 0.4)]:
            ev.append((b0+q, 0.1, 'dbo', None, v, 0.0, 0.0))
        if bar % 2 == 1:
            ev += [(b0+1.75, 0.1, 'dcg', None, 0.6, 0.3, 0.2), (b0+3.0, 0.1, 'dcl', None, 0.7, 0.35, 0.2), (b0+3.25, 0.1, 'dcg', None, 0.5, 0.3, 0.2)]
        for (q, d, m) in AERO_MEL[bar]:
            ev.append((b0+q, d, 'vib', m, 0.85, 0.15, 0.45))
            if bar >= 8:
                ev.append((b0+q, d, 'cel', m+12, 0.6, -0.25, 0.5))
    x = render_musica(100, 16, ev, 'lounge', 0.32, 702)
    return x


VUELO = [[(0, 38, [57, 62, 65, 69])], [(0, 37, [57, 61, 65, 69])], [(0, 36, [57, 60, 65, 69])], [(0, 35, [57, 59, 65, 69])],
         [(0, 34, [57, 62, 65, 70])], [(0, 31, [58, 62, 65, 67])], [(0, 40, [55, 58, 62, 64]), (2, 33, [55, 61, 64, 69])],
         [(0, 33, [55, 62, 64, 69]), (2, 33, [55, 61, 64, 70])]]
VUELO_TAG = [[(0, 34, [57, 62, 65, 70])], [(0, 33, [55, 61, 64, 69])], [(0, 31, [58, 62, 65, 67])], [(0, 33, [55, 61, 64, 70])]]
CAOS_B = [[(0, 34, [57, 62, 65, 70])], [(0, 33, [55, 61, 64, 69])], [(0, 34, [57, 62, 65, 70])], [(0, 33, [55, 61, 64, 69])],
          [(0, 31, [58, 62, 65, 67])], [(0, 33, [55, 61, 64, 69])], [(0, 34, [57, 62, 65, 70])], [(0, 33, [55, 61, 64, 70])]]

MEL_A = [
    [(0, .4, 69), (0.5, .4, 74), (1, .4, 77), (1.5, .4, 76), (2, .9, 74)],
    [(0.5, .4, 73), (1, .4, 74), (1.5, .4, 76), (2, .4, 77), (2.5, .4, 76), (3, .9, 73)],
    [(0, .4, 72), (0.5, .4, 69), (1, .4, 72), (1.5, .4, 77), (2, .4, 76), (2.5, .4, 74), (3, .9, 72)],
    [(0, .9, 71), (1, .4, 74), (1.5, .4, 77), (2, .4, 81), (2.5, .4, 79), (3, .9, 77)],
    [(0, 1.4, 74), (1.5, .4, 77), (2, .4, 81), (2.5, .4, 79), (3, .9, 77)],
    [(0, .4, 74), (0.5, .4, 70), (1, .4, 67), (1.5, .4, 70), (2, .9, 74), (3, .4, 77), (3.5, .4, 79)],
    [(0, .9, 79), (1, .4, 76), (1.5, .4, 70), (2, .4, 73), (2.5, .4, 76), (3, .4, 79), (3.5, .4, 81)],
    [(0, 1.4, 74), (1.5, .4, 76), (2, .4, 73), (2.5, .4, 70), (3, .9, 69)]]
MEL_A2 = MEL_A[:4]+[
    [(0, .4, 77), (0.5, .4, 81), (1, .4, 84), (1.5, .4, 81), (2, .9, 77), (3, .4, 74), (3.5, .4, 77)],
    [(0, .9, 79), (1, .4, 77), (1.5, .4, 74), (2, .4, 70), (2.5, .4, 74), (3, .9, 77)],
    [(0, .4, 76), (0.5, .4, 79), (1, .4, 82), (1.5, .4, 79), (2, .4, 81), (2.5, .4, 79), (3, .4, 76), (3.5, .4, 73)],
    [(0, .9, 74), (1, .9, 76), (2, .4, 77), (2.5, .4, 76), (3, .4, 73), (3.5, .4, 69)]]
MEL_TAG = [
    [(0, .4, 65), (1, .4, 70), (2, .4, 69), (2.5, .4, 70), (3, .9, 74)],
    [(0, .4, 73), (1, .4, 69), (2, .4, 64), (2.5, .4, 67), (3, .9, 73)],
    [(0, .4, 70), (1, .4, 74), (2, .4, 77), (2.5, .4, 74), (3, .9, 70)],
    [(0, .4, 69), (0.5, .4, 70), (1, .4, 73), (1.5, .4, 76), (2, .4, 79), (2.5, .4, 82), (3, .9, 81)]]
MEL_B = [
    [(0, .4, 74), (0.5, .4, 74), (1, .4, 77), (1.5, .4, 74), (2, .4, 81), (2.5, .4, 79), (3, .4, 77), (3.5, .4, 74)],
    [(0, .4, 73), (0.5, .4, 73), (1, .4, 76), (1.5, .4, 73), (2, .4, 79), (2.5, .4, 77), (3, .4, 76), (3.5, .4, 73)],
    [(0, .4, 74), (0.5, .4, 74), (1, .4, 77), (1.5, .4, 74), (2, .4, 81), (2.5, .4, 79), (3, .4, 77), (3.5, .4, 74)],
    [(0, .4, 73), (0.5, .4, 73), (1, .4, 76), (1.5, .4, 79), (2, .9, 82), (3, .9, 81)],
    [(0, .4, 74), (0.5, .4, 70), (1, .4, 74), (1.5, .4, 77), (2, .4, 79), (2.5, .4, 77), (3, .4, 74), (3.5, .4, 70)],
    [(0, .4, 73), (0.5, .4, 69), (1, .4, 73), (1.5, .4, 76), (2, .4, 79), (2.5, .4, 76), (3, .4, 73), (3.5, .4, 69)],
    [(0, 1.4, 77), (1.5, .4, 74), (2, 1.4, 82), (3.5, .4, 81)],
    [(0, .4, 81), (0.5, .4, 82), (1, .4, 81), (1.5, .4, 79), (2, .4, 77), (2.5, .4, 76), (3, .4, 73), (3.5, .4, 69)]]


def bajo_caminante(prog, bar, nxt_root):
    segs = prog
    out = []
    if len(segs) == 1:
        root, vc = segs[0][1], segs[0][2]
        out = [(0, root), (1, quinta(root, vc)), (2, root+12 if root+12 <= 50 else root), (3, nxt_root+(1 if bar % 2 else -1))]
    else:
        for st, root, vc in segs:
            out += [(st, root), (st+1, quinta(root, vc))]
    return out


@reg('MusicaVuelo', 'musica', -24, 'Música original del vuelo: animada, cómica y algo tensa, Re menor, 125 BPM, 20 compases.')
def m_vuelo():
    MIXG.clear()
    MIXG.update({'pzb': 0.5, 'mar': 0.3, 'cla': 0.45, 'str': 0.2, 'dbo': 0.75, 'dca': 0.6, 'dhc': 0.45, 'dbl': 0.4, 'dbh': 0.4, 'dpa': 0.9, 'dcr': 0.25, 'fag': 0.22})
    prog = VUELO+VUELO+VUELO_TAG
    mel = MEL_A+MEL_A2+MEL_TAG
    ev = []
    for bar in range(20):
        b0 = bar*4
        segs = prog[bar]
        nxt = prog[(bar+1) % 20][0][1]
        for q, m in bajo_caminante(segs, bar, nxt):
            ev.append((b0+q, 0.45, 'pzb', m, 0.95 if q in (0, 2) else 0.75, 0.0, 0.08))
        for i in range(8):
            q = i*0.5
            _, root, vc = acorde_en(prog, bar, q)
            m = [vc[0], vc[2], vc[1], vc[3], vc[2], vc[1], vc[3], vc[2]][i]+12
            ev.append((b0+q, 0.3, 'mar', m, 0.85 if i % 2 == 0 else 0.6, 0.35, 0.2))
        for q, v in [(0, 0.9), (2, 0.8)]:
            ev.append((b0+q, 0.1, 'dbo', None, v, 0.0, 0.0))
        if bar % 4 == 3:
            ev.append((b0+2.5, 0.1, 'dbo', None, 0.55, 0.0, 0.0))
        for q in (1, 3):
            ev.append((b0+q, 0.1, 'dca', None, 0.7, 0.05, 0.15))
            if 8 <= bar < 16:
                ev.append((b0+q, 0.1, 'dpa', None, 0.7, -0.05, 0.2))
        for i in range(8):
            ev.append((b0+i*0.5, 0.1, 'dhc', None, 0.8 if i % 2 == 0 else 0.5, -0.35, 0.05))
        if bar % 2 == 1:
            ev += [(b0+3.5, 0.1, 'dbl', None, 0.8, 0.5, 0.15), (b0+3.75, 0.1, 'dbh', None, 0.6, 0.55, 0.15)]
        if bar >= 8:
            for st, root, vc in segs:
                ln = 4 if len(segs) == 1 else 2
                for j, m in enumerate(vc[1:]):
                    ev.append((b0+st, ln-0.15, 'str', m, 0.5, -0.4+0.3*j, 0.4))
        inst = 'cla' if bar < 16 else 'fag'
        for (q, d, m) in mel[bar]:
            ev.append((b0+q, d, inst, m if inst == 'cla' else m-12, 0.9, -0.1, 0.3))
    ev.append((0, 0.1, 'dcr', None, 0.7, 0.4, 0.2))
    ev.append((32, 0.1, 'dcr', None, 0.6, -0.4, 0.2))
    return render_musica(125, 20, ev, 'estudio', 0.28, 703)


@reg('MusicaCaos', 'musica', -23, 'Música original de emergencia: variante rápida e intensa del tema de vuelo, Re menor, 150 BPM, 24 compases.')
def m_caos():
    MIXG.clear()
    MIXG.update({'sbj': 0.26, 'mar': 0.18, 'cla': 0.34, 'brl': 0.5, 'brs': 0.3, 'stt': 0.14, 'dbo': 0.5, 'dca': 0.45, 'dhc': 0.3,
                 'dho': 0.2, 'dcr': 0.25, 'dt1': 0.5, 'dt2': 0.5, 'dt3': 0.5, 'dpa': 0.5})
    prog = VUELO+CAOS_B+VUELO
    mel = MEL_A+MEL_B+MEL_A2
    ev = []
    for bar in range(24):
        b0 = bar*4
        segs = prog[bar]
        for i in range(8):
            q = i*0.5
            _, root, vc = acorde_en(prog, bar, q)
            m = root+12 if i % 4 == 3 else root
            if m < 31:
                m += 12
            ev.append((b0+q, 0.38, 'sbj', m, 0.95 if i % 2 == 0 else 0.75, 0.0, 0.03))
        for q in range(4):
            ev.append((b0+q, 0.1, 'dbo', None, 0.95, 0.0, 0.0))
        if bar % 2 == 1:
            ev.append((b0+3.75, 0.1, 'dbo', None, 0.5, 0.0, 0.0))
        for q in (1, 3):
            ev.append((b0+q, 0.1, 'dca', None, 0.85, 0.05, 0.15))
            ev.append((b0+q, 0.1, 'dpa', None, 0.6, -0.05, 0.15))
        for i in range(16):
            q = i*0.25
            if i % 4 == 2:
                ev.append((b0+q, 0.1, 'dho', None, 0.7, -0.35, 0.05))
            else:
                ev.append((b0+q, 0.1, 'dhc', None, 0.8 if i % 2 == 0 else 0.45, -0.35, 0.05))
        if bar % 8 == 0:
            ev.append((b0, 0.1, 'dcr', None, 0.8, 0.4, 0.2))
        if bar % 8 == 7:
            for i, tm in enumerate(['dt1', 'dt1', 'dt2', 'dt2', 'dt3', 'dt3']):
                ev.append((b0+2.5+i*0.25, 0.1, tm, None, 0.8+0.03*i, -0.4+0.16*i, 0.15))
        for st, root, vc in segs:
            ln = 4 if len(segs) == 1 else 2
            for j, m in enumerate(vc[1:]):
                ev.append((b0+st, ln-0.1, 'stt', m+12, 0.5, -0.4+0.4*j, 0.3))
        if 8 <= bar < 16:
            for q in (1.5, 3.5):
                _, root, vc = acorde_en(prog, bar, q)
                for j, m in enumerate(vc):
                    ev.append((b0+q, 0.3, 'brs', m, 0.85, -0.3+0.2*j, 0.25))
        else:
            for i in range(16):
                q = i*0.25
                _, root, vc = acorde_en(prog, bar, q)
                m = vc[[0, 2, 1, 3][i % 4]]+24
                ev.append((b0+q, 0.15, 'mar', m, 0.7 if i % 4 == 0 else 0.45, 0.45, 0.15))
        inst = 'brl' if bar >= 16 else 'cla'
        for (q, d, m) in mel[bar]:
            ev.append((b0+q, d, inst, m, 0.9, 0.1, 0.25))
            if inst == 'brl':
                ev.append((b0+q, d, 'cla', m-12, 0.6, -0.15, 0.2))
    return render_musica(150, 24, ev, 'estudio', 0.25, 704)


def proc_sfx(x, pico=-1.0, cola=-50.0):
    x = np.asarray(x, float)
    if x.ndim == 2:
        x = x.mean(1)
    x = filt(np.concatenate([x, np.zeros(ns(0.05))]), hp(25, 2), 'min')
    a = np.abs(x)
    s = max(0, np.nonzero(a > a.max()*dbg(-60))[0][0]-ns(0.001))
    w = ns(0.01)
    env = np.sqrt(np.convolve(x*x, np.ones(w)/w, 'same'))
    e = min(len(x), np.nonzero(env > env.max()*dbg(cola))[0][-1]+w)
    x = np.concatenate([np.zeros(ns(0.003)), x[s:e]])
    fi = ns(0.003)+ns(0.001)
    x[:fi] *= np.sin(0.5*np.pi*np.arange(fi)/fi)**2
    fo = min(ns(0.08), len(x)//5)
    x[-fo:] *= np.cos(0.5*np.pi*np.arange(fo)/fo)**2
    x -= np.linspace(x[0], x[-1], len(x))
    return x*dbg(pico)/np.abs(x).max()


def proc_loop(x, pico=-6.0, pct=99.97, maxgr=2.5):
    x = np.asarray(x, float)
    x = filt(x, hp(22, 2), 'circ')
    x = x-x.mean(axis=0)
    ref = max(np.percentile(np.abs(x), pct), np.abs(x).max()*dbg(-maxgr))
    x = x*dbg(pico)/ref
    return limitador(x, dbg(pico), circ=True)


def codificar(y, path, q):
    ch = 1 if y.ndim == 1 else y.shape[1]
    pag = ['-page_duration', '50000'] if len(y) < 3*SR else []
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', str(ch), '-i', 'pipe:0',
                    '-c:a', 'libvorbis', '-q:a', str(q), '-map_metadata', '-1']+pag+['-f', 'ogg', path],
                   input=np.ascontiguousarray(y, dtype='<f4').tobytes(), check=True)


def decodificar(path, ch):
    out = subprocess.run([FFMPEG, '-loglevel', 'error', '-i', path, '-f', 'f32le', '-ac', str(ch), '-ar', str(SR), 'pipe:1'],
                         capture_output=True, check=True).stdout
    z = np.frombuffer(out, '<f4').astype(float)
    return z if ch == 1 else z.reshape(-1, ch)


LIM = {'sfx': 120*1024, 'loop': 600*1024, 'musica': 1536*1024}
QQ = {'sfx': 4, 'loop': 3, 'musica': 5}


def sonoridad(z, tipo):
    m = z if z.ndim == 1 else z
    k = filt(m, lambda f: Mhp(f, 60, 2)*(1+(dbg(4)-1)*Mhp(f, 1500, 1)))
    e = k**2 if k.ndim == 1 else (k**2).sum(1)
    if tipo != 'sfx':
        return 10*np.log10(e.mean()+1e-15)
    w = min(len(e), ns(0.4))
    c = np.convolve(e, np.ones(w)/w, 'valid')
    return 10*np.log10(c.max()+1e-15)


def analizar(z, tipo):
    m = z if z.ndim == 1 else z.mean(1)
    S = np.abs(np.fft.rfft(m*np.hanning(len(m))))**2
    f = np.fft.rfftfreq(len(m), 1/SR)
    cen = float((S*f).sum()/S.sum())
    hf = float(S[f > 10000].sum()/S.sum())
    harsh = float(S[(f > 2000) & (f < 5000)].sum()/S.sum())
    info = {'pico': db(np.abs(z).max()), 'rms': db(np.sqrt(np.mean(z**2))), 'dc': float(np.abs(z.mean(axis=0)).max()),
            'cen': cen, 'hf': hf, 'harsh': harsh}
    if tipo == 'sfx':
        info['bordes'] = float(max(abs(m[0]), abs(m[-1])))
        info['costura'] = None
    else:
        d = np.abs(np.diff(m))
        info['costura'] = float(abs(m[0]-m[-1])/(np.percentile(d, 99)+1e-12))
        e = np.convolve(np.concatenate([m[-200:], m, m[:200]]), [1, -1], 'valid')**2
        e = np.convolve(e, np.ones(64)/64, 'same')[200:-200]
        info['clic'] = float(e[[0, -1]].max()/(np.percentile(e, 99)+1e-15))
        info['bordes'] = None
    return info


def exportar(nombre, x, tipo):
    path = os.path.join(DIR, nombre+'.ogg')
    if tipo == 'sfx':
        y = proc_sfx(x)
        objetivo = -1.0
    else:
        y = proc_loop(x, -6.0, 99.97, 2.5 if tipo == 'loop' else 3.0)
        objetivo = -6.0
    ch = 1 if y.ndim == 1 else 2
    q = QQ[tipo]
    tmp = path+'.tmp'
    mejor = None
    for off in (0.0, -0.3, 0.3, -0.6, 0.6, -0.9, 0.9):
        yy = y*dbg(off)
        codificar(yy, tmp, q)
        while os.path.getsize(tmp) > LIM[tipo] and q > 0:
            q -= 1
            codificar(yy, tmp, q)
        z = decodificar(tmp, ch)
        pk_ = db(np.abs(z).max())
        err = abs(pk_-objetivo)+(3.0 if pk_ > objetivo+0.4 else 0.0)
        if mejor is None or err < mejor[0]:
            mejor = (err, off, z)
            os.replace(tmp, path)
        if err <= 0.12:
            break
    if os.path.exists(tmp):
        os.remove(tmp)
    z = mejor[2]
    y = y*dbg(mejor[1])
    assert len(z) == len(y), (nombre, len(z), len(y))
    info = analizar(z, tipo)
    info.update({'dur': len(y)/SR, 'kb': os.path.getsize(path)/1024, 'q': q, 'ch': ch, 'lk': sonoridad(z, tipo)})
    return info


def main():
    sel = set(sys.argv[1:])
    os.makedirs(DIR, exist_ok=True)
    mpath = os.path.join(DIR, 'manifest.json')
    previo = {}
    if sel and os.path.exists(mpath):
        previo = {e['nombre']: e for e in json.load(open(mpath, encoding='utf-8'))}
    filas = []
    man = []
    for nombre, fn, tipo, nivel, desc in SONIDOS:
        if sel and nombre not in sel:
            if nombre in previo:
                man.append(previo[nombre])
            continue
        x = fn()
        info = exportar(nombre, x, tipo)
        vol = float(np.clip(round(20*dbg(nivel-info['lk']))/20, 0.05, 1.0))
        info['vol'] = vol
        filas.append((nombre, tipo, info))
        man.append({'nombre': nombre, 'archivo': nombre+'.ogg', 'duracion': round(info['dur'], 3), 'bucle': tipo != 'sfx',
                    'volumen': vol, 'descripcion': desc})
        print(f"{nombre:18s} {info['dur']:6.2f}s pk {info['pico']:6.2f} rms {info['rms']:6.1f} {info['kb']:6.1f}KB vol {vol:.2f}", flush=True)
    orden = [s[0] for s in SONIDOS]
    man.sort(key=lambda e: orden.index(e['nombre']) if e['nombre'] in orden else 999)
    with open(mpath, 'w', encoding='utf-8') as fh:
        json.dump(man, fh, ensure_ascii=False, indent=1)
    print()
    print(f"{'nombre':18s} {'tipo':6s} {'ch':>2s} {'dur s':>6s} {'pico':>6s} {'rms':>6s} {'KB':>6s} {'q':>2s} {'sonor':>6s} {'vol':>4s} {'cent':>6s} {'>10k%':>6s} {'2-5k%':>6s} {'dc':>8s} {'borde/costura':>13s}")
    for nombre, tipo, i in filas:
        extra = f"{i['bordes']:.1e}" if tipo == 'sfx' else f"{i['costura']:.2f}/{i['clic']:.2f}"
        print(f"{nombre:18s} {tipo:6s} {i['ch']:2d} {i['dur']:6.2f} {i['pico']:6.2f} {i['rms']:6.1f} {i['kb']:6.1f} {i['q']:2d} {i['lk']:6.1f} {i['vol']:4.2f} {i['cen']:6.0f} {100*i['hf']:6.2f} {100*i['harsh']:6.1f} {i['dc']:8.1e} {extra:>13s}")


if __name__ == '__main__':
    main()
