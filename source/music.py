import numpy as np, json, wave, sys
d=sys.argv[1]; sc=json.load(open(d+'/scenes.json'))
SR=44100; T=sc['total']; N=int(SR*T); L=np.zeros(N); R=np.zeros(N)
rng=np.random.default_rng(1); bpm=120; beat=60/bpm
def add(sig,t,pan=0.0,g=1.0):
    i=int(t*SR); s=sig[:max(0,N-i)]*g
    L[i:i+len(s)]+=s*(1-pan)/1.0 if pan>0 else s; R[i:i+len(s)]+=s*(1+pan) if pan<0 else s
def env(n,a,dcy):
    t=np.arange(n)/SR; return np.minimum(t/a,1)*np.exp(-t/dcy)
def kick():
    n=int(.35*SR);t=np.arange(n)/SR;f=45+90*np.exp(-t/0.04)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.12)*0.9
def hat():
    n=int(.06*SR);x=rng.standard_normal(n);x=np.diff(x,prepend=0);return x*env(n,.001,.015)*0.12
def clap():
    n=int(.2*SR);x=rng.standard_normal(n);x=np.diff(x,prepend=0);return x*env(n,.002,.05)*0.25
def tone(f,dur,kind='saw',dcy=.25,g=.2):
    n=int(dur*SR);t=np.arange(n)/SR;ph=(f*t)%1
    w=(2*ph-1) if kind=='saw' else np.sin(2*np.pi*f*t)
    if kind=='saw': w=np.convolve(w,np.ones(6)/6,'same')
    return w*env(n,.005,dcy)*g
mid=lambda m:440*2**((m-69)/12)
prog=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]]  # Am F C G
roots=[45,41,36,43]
nb=int(T/beat)
intro_end=sc['starts'][2]; outro=sc['starts'][-1]
for b in range(nb):
    t=b*beat; bar=b//4; ch=prog[bar%4]
    full = t>=intro_end
    if full or b%2==0: add(kick(),t)
    if full and b%2==1: add(clap(),t)
    add(hat(),t+beat/2,0.3)
    if full: add(hat(),t+beat*0.25,-0.3,0.6); add(hat(),t+beat*0.75,-0.3,0.6)
    # bass 8ths
    for k in range(2): add(tone(mid(roots[bar%4]),beat/2,'saw',.12,.28 if full else .18),t+k*beat/2)
    # pluck arp 16ths
    for k in range(4):
        m=ch[(b*4+k)%3]+12; add(tone(mid(m),.3,'saw',.09,.07),t+k*beat/4,0.4 if k%2 else -0.4)
# pad
for bar in range(int(T/(4*beat))+1):
    for m in prog[bar%4]: add(tone(mid(m),4*beat,'sin',3,.05),bar*4*beat)
# sidechain duck
t=np.arange(N)/SR; ph=(t%beat)/beat; duck=0.55+0.45*np.minimum(ph/0.35,1)
L*=duck;R*=duck
# whoosh + impact at scene cuts
for s in sc['starts'][1:]:
    n=int(.4*SR);x=rng.standard_normal(n);x=np.convolve(x,np.ones(30)/30,'same')
    e=np.linspace(0,1,n)**3*0.5; i0=s-.4
    add(x*e,i0,0.0,1.0); add(kick()*0.6,s)
L*=np.minimum(1,(T-t)/1.5).clip(0); R*=np.minimum(1,(T-t)/1.5).clip(0)
m=max(abs(L).max(),abs(R).max()); L,R=L/m*.85,R/m*.85
st=np.stack([L,R],1); st=np.tanh(st*1.2)/np.tanh(1.2)
w=wave.open(d+'/music.wav','wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
w.writeframes((st*32000).astype('<i2').tobytes());w.close()
