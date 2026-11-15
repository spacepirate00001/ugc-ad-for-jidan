# Epic hybrid-trailer score: taiko/toms, punchy kick & snare, staccato string ostinato, distorted sub, brass braams.
# 120 BPM, D minor (i-VI-III-VII). Hits locked to the video's scene cuts.
import numpy as np, json, wave, sys
d=sys.argv[1]; sc=json.load(open(d+'/scenes.json'))
SR=44100; T=sc['total']; N=int(SR*(T+0.3)); L=np.zeros(N); R=np.zeros(N)
rng=np.random.default_rng(21); st=sc['starts']
def put(sig,t,pan=0.0,g=1.0):
    i=int(round(t*SR))
    if i>=N or i<0: return
    s=sig[:N-i]*g; L[i:i+len(s)]+=s*np.sqrt(0.5*(1-pan)); R[i:i+len(s)]+=s*np.sqrt(0.5*(1+pan))
mid=lambda m:440*2**((m-69)/12)
def lp(x,a):  # one-pole lowpass, vectorised-ish via scipy-free recursion in chunks
    y=np.empty_like(x);acc=0.0
    for i in range(len(x)): acc+=a*(x[i]-acc); y[i]=acc
    return y
def saw(f,n,t):
    ph=(f*t)%1; return 2*ph-1
def kick(g=.9):
    n=int(.45*SR);t=np.arange(n)/SR;f=42+130*np.exp(-t/0.025)
    w=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.22); w+=0.25*rng.standard_normal(n)*np.exp(-t/0.004)
    return np.tanh(w*1.6)*g
def snare(g=.45):
    n=int(.5*SR);t=np.arange(n)/SR;x=rng.standard_normal(n)
    body=np.sin(2*np.pi*190*t)*np.exp(-t/0.05)
    return (0.8*x*np.exp(-t/0.12)+0.6*body)*g
def taiko(f0=70,g=.8):
    n=int(1.0*SR);t=np.arange(n)/SR;f=f0*(1+0.8*np.exp(-t/0.03))
    w=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.28)+0.3*rng.standard_normal(n)*np.exp(-t/0.02)
    return np.tanh(w*1.3)*g
def hat(g=.06):
    n=int(.05*SR);x=np.diff(rng.standard_normal(n+1));return x*np.exp(-np.arange(n)/SR/0.012)*g
STAC={}
def stac(m,g=.09):   # staccato string
    if m not in STAC:
        n=int(.16*SR);t=np.arange(n)/SR;w=np.zeros(n)
        for det in (-0.06,0,0.05): w+=saw(mid(m)*2**(det/12),n,t)
        w=np.convolve(w,np.ones(10)/10,'same'); STAC[m]=w*np.minimum(t/0.006,1)*np.exp(-t/0.06)
    return STAC[m]*g
def subb(m,dur,g=.35):
    n=int(dur*SR);t=np.arange(n)/SR;f=mid(m)
    w=np.sin(2*np.pi*f*t)+0.5*np.sin(2*np.pi*2*f*t)
    return np.tanh(w*2.2)*np.minimum(t/0.005,1)*np.exp(-t/0.35)*g
def braam(root,dur=3.5,g=.22):
    n=int(dur*SR);t=np.arange(n)/SR;w=np.zeros(n)
    for m,a in [(root,1),(root+12,.8),(root+7,.6),(root+19,.35)]:
        for det in (-0.1,0,0.1): w+=a*saw(mid(m)*2**(det/12),n,t)
    w=lp(w,0.05)*2.5; w=np.tanh(w*1.4)
    env=np.minimum(t/0.12,1)*np.exp(-t/1.6); return w*env*g
def pad(m,dur,g=.03):
    n=int(dur*SR);t=np.arange(n)/SR;w=np.zeros(n)
    for det in (-0.08,0,0.08): w+=np.sin(2*np.pi*mid(m)*2**(det/12)*t)+0.3*saw(mid(m)*2**(det/12)*2,n,t)*0.3
    return w*np.minimum(t/0.8,1)*np.minimum((dur-t)/0.8,1).clip(0)*g
def riser(dur,g=.12):
    n=int(dur*SR);x=rng.standard_normal(n)
    y=lp(x,0.08); y2=x-lp(x,0.02); k=np.linspace(0,1,n)
    tone=np.sin(2*np.pi*np.cumsum(200+1400*k**2)/SR)*0.25
    return ((1-k)*y+k*y2+tone)*k**2.2*g
def crash(g=.25):
    n=int(2.2*SR);t=np.arange(n)/SR;x=np.diff(rng.standard_normal(n+1));return x*np.exp(-t/0.7)*g
def boom(g=.9):
    n=int(3*SR);t=np.arange(n)/SR;f=32+60*np.exp(-t/0.12)
    return np.tanh(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/1.0)*1.5)*g

b=0.5; bar=2.0
prog=[(38,[62,65,69]),(46,[62,65,70]),(41,[60,65,69]),(36,[60,64,67])]  # Dm Bb F C
pat=[0,1,2,1, 0,2,1,2, 0,1,2,1, 0,2,1,0]
def section(t):
    if t<st[1]: return 'intro'
    if t<st[2]: return 'build'
    if st[7]<=t<st[8]: return 'break'
    if t>=st[9]: return 'outro'
    return 'full'
nb=int(T/bar)+1
for k in range(nb):
    t0=k*bar; root,ch=prog[k%4]; sec=section(t0+0.01)
    for m in ch: put(pad(m,bar+0.8),t0,0,1.6 if sec in('break','intro') else 1.0)
    if sec in ('build','full','break'):
        for j in range(16):
            m=ch[pat[j]%3]+(12 if j in (4,12) else 0)
            put(stac(m,.10 if j%4==0 else .07),t0+j*b/4,(-0.5 if j%2 else 0.5))
            if sec=='full': put(stac(m-12,.05),t0+j*b/4)
    if sec=='full':
        for q in range(4):
            put(subb(root,b*0.95),t0+q*b); put(subb(root,b*0.45,.25),t0+q*b+b/2)
            if q in (0,2): put(kick(),t0+q*b)
            if q==2: put(kick(.6),t0+q*b-b/2*0.5)  # syncopation
            if q in (1,3): put(snare(),t0+q*b,0.05)
            put(hat(),t0+q*b+b/2,0.4); put(hat(.035),t0+q*b+b/4,-0.4); put(hat(.035),t0+q*b+3*b/4,-0.4)
        put(taiko(62,.5),t0,-0.3); put(taiko(80,.35),t0+1.25,0.3)
    elif sec=='build':
        put(kick(.8),t0); put(taiko(60,.7),t0+1.0); put(snare(.35),t0+1.0)
        for q in range(4): put(subb(root,b*0.9,.2),t0+q*b)
    elif sec=='break':
        put(kick(.5),t0); put(kick(.5),t0+1.0)
# tom fills into each cut (except into breakdown) + impacts on every cut
for i,s in enumerate(st[1:],1):
    put(riser(1.5 if i in (2,8,9) else 0.9,.13 if i in (2,8,9) else .07),s-(1.5 if i in (2,8,9) else 0.9))
    if section(s-0.1)!='intro':
        for j,f0 in enumerate([110,95,80,68]): put(taiko(f0,.35+0.08*j),s-0.5+j*0.125,(-0.4+0.27*j))
    put(boom(.7 if i in (2,8,9) else .45),s); put(crash(.22 if i in (2,8,9) else .12),s,0.2); put(kick(.9),s)
# image cuts inside chapters (beat hits)
for ci in range(5):
    s=st[2+ci]; n=[3,4,4,3,4][ci]; step=1.0 if n==4 else 1.5
    for k in range(1,n): put(taiko(75,.35),s+k*step,0.2); put(crash(.06),s+k*step)
# braams: logo slam, drop, final
put(braam(26,4.0,.26),0.95); put(boom(1.0),0.95); put(crash(.3),0.95)
put(braam(26,3.5,.2),st[2]); put(braam(22,3.0,.16),st[8])
put(braam(26,6.0,.28),st[9]+0.75); put(boom(1.0),st[9]+0.75)
for m in [50,57,62,65,69,74]: put(pad(m,5.0,.05),st[9]+0.75)
# reverb-ish
for buf in (L,R):
    for dl,g in [(0.033,.28),(0.051,.24),(0.079,.18),(0.117,.13),(0.173,.09)]:
        n=int(dl*SR)
        for _ in range(2): buf[n:]+=buf[:-n]*g*0.5
t=np.arange(N)/SR; fade=np.minimum(1,np.minimum(t/0.15,(T-t)/2.2)).clip(0)
L*=fade;R*=fade
out=np.stack([L,R],1); out/=np.percentile(np.abs(out),99.95); out=np.tanh(out*1.1)/np.tanh(1.1)*0.95
w=wave.open(d+'/music.wav','wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
w.writeframes((np.clip(out,-1,1)*31000).astype('<i2').tobytes());w.close()
