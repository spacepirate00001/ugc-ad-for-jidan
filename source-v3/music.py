# Uplifting modern-corporate score: marimba plucks, warm bass, snaps, shaker, string swells. 104 BPM, F major.
import numpy as np, json, wave, sys
d=sys.argv[1]; sc=json.load(open(d+'/scenes.json'))
SR=44100; T=sc['total']; N=int(SR*(T+0.2)); L=np.zeros(N); R=np.zeros(N)
rng=np.random.default_rng(11); st=sc['starts']
def put(sig,t,pan=0.0,g=1.0):
    i=int(t*SR)
    if i>=N or i<0: return
    s=sig[:N-i]*g; L[i:i+len(s)]+=s*np.sqrt(0.5*(1-pan)); R[i:i+len(s)]+=s*np.sqrt(0.5*(1+pan))
mid=lambda m:440*2**((m-69)/12)
def marimba(m,g=.16):
    n=int(.9*SR);t=np.arange(n)/SR;f=mid(m)
    w=np.sin(2*np.pi*f*t)*np.exp(-t/0.28)+0.35*np.sin(2*np.pi*f*4*t)*np.exp(-t/0.04)+0.15*np.sin(2*np.pi*f*10*t)*np.exp(-t/0.01)
    return w*np.minimum(t/0.002,1)*g
def bass(m,dur,g=.32):
    n=int(dur*SR);t=np.arange(n)/SR;f=mid(m)
    w=np.sin(2*np.pi*f*t)+0.3*np.sin(2*np.pi*2*f*t)+0.1*np.sin(2*np.pi*3*f*t)
    return w*np.minimum(t/0.01,1)*np.minimum((dur-t)/0.03,1).clip(0)*np.exp(-t/0.9)*g
def strings(m,dur,g=.03):
    n=int(dur*SR);t=np.arange(n)/SR;w=np.zeros(n)
    for det in (-0.08,0.0,0.07):
        f=mid(m)*2**(det/12)*(1+0.003*np.sin(2*np.pi*5*t)); w+=np.sin(2*np.pi*np.cumsum(f)/SR)
        w+=0.4*np.sin(2*np.pi*2*np.cumsum(f)/SR)
    env=np.minimum(t/0.9,1)*np.minimum((dur-t)/0.9,1).clip(0); return w*env*g
def kick(g=.55):
    n=int(.3*SR);t=np.arange(n)/SR;f=48+70*np.exp(-t/0.03)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.16)*g
def snap(g=.16):
    n=int(.15*SR);x=rng.standard_normal(n);x=x-np.convolve(x,np.ones(8)/8,'same')
    return x*np.exp(-np.arange(n)/SR/0.035)*g
def shaker(g=.035):
    n=int(.07*SR);x=rng.standard_normal(n);x=np.diff(x,prepend=0)
    t=np.arange(n)/SR; return x*np.minimum(t/0.01,1)*np.exp(-t/0.02)*g
def riser(dur,g=.1):
    n=int(dur*SR);x=rng.standard_normal(n);out=np.zeros(n);a=0.;c=np.linspace(0.01,0.4,n)
    for i in range(n): a+=c[i]*(x[i]-a); out[i]=a
    return out*np.linspace(0,1,n)**2*g
def boom(g=.6):
    n=int(2.5*SR);t=np.arange(n)/SR;f=38+40*np.exp(-t/0.08)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.8)*g
bpm=104; b=60/bpm; bar=4*b
# F  C/E  Dm  Bb
prog=[(41,[65,69,72]),(40,[64,67,72]),(38,[62,65,69]),(46,[62,65,70])]
motif=[0,2,1,2, 0,2,1,3]   # chord-tone indices per 8th
build=st[1]; calm=(st[7],st[8]); end=st[-1]
nb=int(T/bar)+1
for k in range(nb):
    t0=k*bar; root,ch=prog[k%4]
    full=t0>=build-0.01 and not (calm[0]<=t0<calm[1]-0.5)
    for m in ch: put(strings(m,bar+0.9),t0,0,1.3 if full else 1.0)
    put(strings(root+12,bar+0.9,.02),t0)
    for j,ix in enumerate(motif):
        m=ch[ix%3]+(12 if ix==3 else 0)+12
        put(marimba(m,.13 if j%2 else .17),t0+j*b/2,(-0.4 if j%2 else 0.4))
    if t0>=build-0.01:
        for q in range(4):
            put(bass(root,b*0.9,.3 if full else .18),t0+q*b)
            if full: put(kick(),t0+q*b)
            if full and q%2==1: put(snap(),t0+q*b,0.1)
            for s16 in range(4):
                if full or s16%2==0: put(shaker(.04 if s16%2 else .025),t0+q*b+s16*b/4,0.5)
# accents
put(boom(.7),0.45)
for s in st[1:]: put(riser(1.0,.07),s-1.0); put(kick(.35),s)
put(riser(2.0,.12),end-2.0); put(boom(.8),end+0.2)
for m in [53,65,69,72,77]: put(strings(m,5.5,.05),end+0.2)
for m in [65,69,72,77]: put(marimba(m+12,.2),end+0.2)
# room reverb
for buf in (L,R):
    for dl,g in [(0.029,.3),(0.043,.26),(0.067,.2),(0.097,.15),(0.151,.1)]:
        n=int(dl*SR)
        for _ in range(2): buf[n:]+=buf[:-n]*g*0.5
t=np.arange(N)/SR; fade=np.minimum(1,np.minimum(t/0.4,(T-t)/2.0)).clip(0)
L*=fade;R*=fade; m=max(abs(L).max(),abs(R).max()); out=np.stack([L,R],1)/m*0.92
out=np.tanh(out*1.15)/np.tanh(1.15)
w=wave.open(d+'/music.wav','wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
w.writeframes((out*30000).astype('<i2').tobytes());w.close()
