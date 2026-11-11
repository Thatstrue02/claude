import json,glob
exec(open('ta.py').read().split('res={}')[0])
D='/root/.claude/projects/-home-user-claude/20729b39-be27-5d29-a566-7f42e6fe8023/tool-results/'
fs=files[:8]+[D+'mcp-Binance_MCP-spot_klines-1794381161394.txt',D+'mcp-Binance_MCP-spot_klines-1794381162017.txt']
nms=names+['BNB','PEPE']
rows=[]
for nm,f in zip(nms,fs):
    k=json.loads(open(f).read())
    t=[int(x[0]) for x in k];h=[float(x[2]) for x in k];l=[float(x[3]) for x in k];c=[float(x[4]) for x in k];v=[float(x[7]) for x in k]
    b4={}
    for i in range(len(t)): b4.setdefault(t[i]//14400000,[]).append(i)
    c4=[c[ix[-1]] for kk,ix in sorted(b4.items())]
    bear4=ema(c4,50)[-1]<ema(c4,200)[-1]
    e50=ema(c,50);e200=ema(c,200);r=rsi(c);m=[a-b for a,b in zip(ema(c,12),ema(c,26))];sg=ema(m,9);A=atr(h,l,c)
    day=t[-1]//86400000;td=[i for i in range(len(t)) if t[i]//86400000==day];yd=[i for i in range(len(t)) if t[i]//86400000==day-1]
    vw=sum((h[i]+l[i]+c[i])/3*v[i] for i in td)/sum(v[i] for i in td)
    P=c[-1];dL=min(l[i] for i in td);dH=max(h[i] for i in td);yL=min(l[i] for i in yd);yH=max(h[i] for i in yd)
    H48=max(h[-48:]);L48=min(l[-48:]);f382=L48+(H48-L48)*.382;f618=L48+(H48-L48)*.618
    checks={'VWAP/Tages-Tief':P<vw,'Golden Cross 1h <4h':False,'4h EMA50<200':bear4,'RSI<50 & MACD<Sig':r[-1]<50 and m[-1]<sg[-1],'unter Fib/EMA-Struktur':P<f382 and P<e50[-1]}
    score=sum(checks.values())
    # short trigger: break below min(today low, yesterday low) - small buffer
    trig=min(dL,yL)*0.999; R=1.5*A[-1]; sl=trig+R; tp1=trig-1.8*R; tp2=trig-3*R
    risk_pct=R/trig*100; gain=1000*(0.5*1.8*R+0.5*3*R)/trig; loss=1000*R/trig
    vf=sum(v[-4:])/4/(sum(v[-100:-4])/96)
    rows.append(dict(sym=nm,price=P,score=score,checks=checks,rsi=round(r[-1],1),atr=A[-1],vwap=vw,dL=dL,dH=dH,yL=yL,yH=yH,trig=trig,sl=sl,tp1=tp1,tp2=tp2,risk_pct=risk_pct,gain=gain,loss=loss,crv=(0.5*1.8+0.5*3),volf=vf,f382=f382,f618=f618,e50=e50[-1],e200=e200[-1]))
rows.sort(key=lambda x:-x['gain'])
json.dump(rows,open('rank.json','w'),indent=1)
for x in rows: print(x['sym'],round(x['price'],6),'score',x['score'],'rsi',x['rsi'],'trig',round(x['trig'],6),'sl',round(x['sl'],6),'tp1',round(x['tp1'],6),'tp2',round(x['tp2'],6),'risk%',round(x['risk_pct'],2),'gain$',round(x['gain'],1),'loss$',round(x['loss'],1),'volf',round(x['volf'],2),'R1',round(x['f382'],6),'R2',round(x['f618'],6),'vwap',round(x['vwap'],6),'yH',x['yH'])
