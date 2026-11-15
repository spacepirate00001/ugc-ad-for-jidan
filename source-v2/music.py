# Cinematic corporate score: piano + strings pad + soft pulse, accents on scene cuts
import numpy as np, json, wave, sys
d=sys.argv[1]; sc=json.load(open(d+'/scenes.json'))
SR=44100; T=sc['total']; N=int(SR*(T+0.1)); L=np.zeros(N); R=np.zeros(N)
rng=np.random.default_rng(7)
def put(sig,t,pan=0.0,g=1.0):
    i=int(t*SR)
    if i>=N: return
    s=sig[:N-i]*g; L[i:i+len(s)]+=s*np.sqrt(0.5*(1-pan)); R[i:i+len(s)]+=s*np.sqrt(0.5*(1+pan))
mid=lambda m:440*2**((m-69)/12)
def piano(m,dur=2.5,g=.16):
    n=int(dur*SR);t=np.arange(n)/SR;f=mid(m);w=np.zeros(n)
    for h,a in [(1,1),(2,.45),(3,.22),(4,.12),(5,.06)]:
        w+=a*np.sin(2*np.pi*f*h*t*(1+0.0004*h))*np.exp(-t*(1.2+h*0.9))
    att=np.minimum(t/0.004,1); return w*att*g
def pad(m,dur,g=.035):
    n=int(dur*SR);t=np.arange(n)/SR;w=np.zeros(n)
    for det in (-0.12,0,0.12):
        ph=(mid(m)*2**(det/12)*t)%1; w+=2*ph-1
    k=np.ones(40)/40; w=np.convolve(w,k,'same'); w=np.convolve(w,k,'same')
    env=np.minimum(t/1.2,1)*np.minimum((dur-t)/1.2,1); return w*env*g
def sub(f0=55,dur=2.2,g=.5):
    n=int(dur*SR);t=np.arange(n)/SR;fr=f0*(1+1.5*np.exp(-t/0.05))
    return np.sin(2*np.pi*np.cumsum(fr)/SR)*np.exp(-t/0.7)*g
def whoosh(dur=0.9,g=.12):
    n=int(dur*SR);x=rng.standard_normal(n);out=np.zeros(n);a=0.0
    cut=np.linspace(0.02,0.25,n)
    for i in range(n): a+=cut[i]*(x[i]-a); out[i]=a
    e=np.sin(np.pi*np.linspace(0,1,n))**2; return out*e*g
def tick(g=.05):
    n=int(.05*SR);x=rng.standard_normal(n);x=np.diff(x,prepend=0);return x*np.exp(-np.arange(n)/SR/0.008)*g
bpm=90; b=60/bpm
# Dmaj9-ish progression: D  Bm  G  A  (voicings)
prog=[[50,57,62,64,66],[47,54,59,62,66],[43,55,59,62,64],[45,52,57,61,64]]
bars=int(T/(4*b))+1
for k in range(bars):
    t0=k*4*b; ch=prog[k%4]
    for m in ch[1:]: put(pad(m,4*b+1.2),t0,0,1.0)
    put(pad(ch[0]-12,4*b+1.2,0.05),t0)
    # piano arpeggio 8ths
    arp=[ch[1]+12,ch[2]+12,ch[3]+12,ch[4]+12,ch[3]+12,ch[2]+12,ch[4]+12,ch[3]+24]
    for j,m in enumerate(arp):
        put(piano(m,2.2,.11 if j%2 else .14),t0+j*b/2,(-0.35 if j%2 else 0.35))
    put(piano(ch[0],3.5,.22),t0); put(piano(ch[0]+12,3,.1),t0)
    # soft pulse after the opening
    if t0>=sc['starts'][1]-0.01 and t0<sc['starts'][-1]+2:
        for q in range(4): put(sub(44,0.6,.28),t0+q*b); put(tick(),t0+q*b+b/2,0.5)
# accents
put(sub(41,3,.7),sc['starts'][0]+0.45)            # logo reveal
for s in sc['starts'][1:]: put(whoosh(),s-0.55,0,1.0); put(sub(46,1.2,.25),s)
put(sub(41,3,.6),sc['starts'][-1]+0.2)
# simple reverb (feedback delays)
for buf in (L,R):
    for dl,g in [(0.031,.32),(0.047,.28),(0.073,.22),(0.113,.17),(0.167,.12)]:
        n=int(dl*SR); 
        for _ in range(3): buf[n:]+=buf[:-n]*g*0.5
t=np.arange(N)/SR; fade=np.minimum(1,np.minimum(t/0.6,(T-t)/2.5)).clip(0)
L*=fade;R*=fade; m=max(abs(L).max(),abs(R).max()); st=np.stack([L,R],1)/m*0.9
st=np.tanh(st*1.1)/np.tanh(1.1)
w=wave.open(d+'/music.wav','wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
w.writeframes((st*30000).astype('<i2').tobytes());w.close()
