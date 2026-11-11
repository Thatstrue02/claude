import json,glob,sys
D='/root/.claude/projects/-home-user-claude/20729b39-be27-5d29-a566-7f42e6fe8023/tool-results/'
files=sorted(glob.glob(D+'mcp-Binance_MCP-spot_klines-*.txt'))
names=['BTC','ETH','XRP','SOL','ZEC','UNI','NEAR','DOGE']
def ema(a,n):
    k=2/(n+1);o=[a[0]]
    for x in a[1:]: o.append(o[-1]+k*(x-o[-1]))
    return o
def rsi(c,n=14):
    g=l=0;out=[50]*len(c)
    for i in range(1,len(c)):
        d=c[i]-c[i-1];gg=max(d,0);ll=max(-d,0)
        if i<=n: g+=gg/n;l+=ll/n
        else: g=(g*(n-1)+gg)/n;l=(l*(n-1)+ll)/n
        out[i]=100-100/(1+g/l) if l>0 else 100
    return out
def atr(h,l,c,n=14):
    tr=[h[0]-l[0]]+[max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])) for i in range(1,len(c))]
    o=[tr[0]]
    for x in tr[1:]: o.append((o[-1]*(n-1)+x)/n)
    return o
res={}
FEE=0.001 # OKX taker 0.05% x2 round trip
bt_all={'short':[],'long':[]}
for nm,f,f0 in zip(names,files[:8],files[8:16]):
    k=json.loads(open(f0).read())+json.loads(open(f).read())
    t=[int(x[0]) for x in k];o=[float(x[1]) for x in k];h=[float(x[2]) for x in k];l=[float(x[3]) for x in k];c=[float(x[4]) for x in k];v=[float(x[7]) for x in k]
    # 4h aggregate (UTC aligned)
    b4={}
    for i in range(len(t)):
        key=t[i]//14400000; b4.setdefault(key,[]).append(i)
    c4=[c[ix[-1]] for kk,ix in sorted(b4.items())]
    e50_4=ema(c4,50);e200_4=ema(c4,200)
    e50=ema(c,50);e200=ema(c,200);r=rsi(c);m=[a-b for a,b in zip(ema(c,12),ema(c,26))];sig=ema(m,9);A=atr(h,l,c)
    day=t[-1]//86400000
    td=[i for i in range(len(t)) if t[i]//86400000==day]; yd=[i for i in range(len(t)) if t[i]//86400000==day-1]
    vw=sum((h[i]+l[i]+c[i])/3*v[i] for i in td)/max(sum(v[i] for i in td),1e-9)
    gc=[i for i in range(len(t)-4,len(t)) if (e50[i]>e200[i])!=(e50[i-1]>e200[i-1])]
    cross=('GOLDEN' if e50[-1]>e200[-1] else 'DEATH')+(' (neu <4h)' if gc else '')
    volf=sum(v[-4:])/4/(sum(v[-100:-4])/96)
    # fib from last 48h range
    H48=max(h[-48:]);L48=min(l[-48:])
    res[nm]=dict(price=c[-1],last_t=t[-1],e50_4=e50_4[-1],e200_4=e200_4[-1],trend4h='bear' if e50_4[-1]<e200_4[-1] else 'bull',
      rsi=r[-1],macd=m[-1],macdsig=sig[-1],atr=A[-1],vwap=vw,dH=max(h[i] for i in td),dL=min(l[i] for i in td),yH=max(h[i] for i in yd),yL=min(l[i] for i in yd),
      cross1h=cross,e50_1h=e50[-1],e200_1h=e200[-1],volf=volf,H48=H48,L48=L48,
      fib382=L48+(H48-L48)*0.382,fib5=L48+(H48-L48)*0.5,fib618=L48+(H48-L48)*0.618)
    # backtest: entry at 08:00 UTC bar open (09 CET), exit by 15:00 UTC close (16 CET)
    days=sorted(set(x//86400000 for x in t))
    for d in days[10:-1]:
        idx=[i for i in range(len(t)) if t[i]//86400000==d]
        try:
            ie=[i for i in idx if (t[i]//3600000)%24==8][0]; ix=[i for i in idx if (t[i]//3600000)%24==14][0]
        except IndexError: continue
        p=ie-1
        k4=[kk for kk in sorted(b4) if kk*14400000+14400000<=t[ie]]
        if len(k4)<200: continue
        cc=[c[b4[kk][-1]] for kk in k4]; tb='bear' if ema(cc,50)[-1]<ema(cc,200)[-1] else 'bull'
        dd=[i for i in idx if i<ie]; vwp=sum((h[i]+l[i]+c[i])/3*v[i] for i in dd)/max(sum(v[i] for i in dd),1e-9)
        for side in ('short','long'):
            s=-1 if side=='short' else 1
            conds=[(tb=='bear') if s<0 else (tb=='bull'), (c[p]<vwp) if s<0 else (c[p]>vwp), (r[p]<50) if s<0 else (r[p]>50), (m[p]<sig[p]) if s<0 else (m[p]>sig[p]), (e50[p]<e200[p]) if s<0 else (e50[p]>e200[p])]
            if sum(conds)<4 or not conds[0]: continue
            E=o[ie];R=1.5*A[p];SL=E-s*R;TP1=E+s*1.8*R;TP2=E+s*3*R
            pnl=0;half=False;sl=SL;mae=mfe=0
            for i in range(ie,ix+1):
                adv=(l[i]-E)*s if s>0 else (h[i]-E)*s; fav=(h[i]-E)*s if s>0 else (l[i]-E)*s
                mae=min(mae,adv);mfe=max(mfe,fav)
                hitsl=(l[i]<=sl) if s>0 else (h[i]>=sl)
                if hitsl: pnl+=(0.5 if half else 1)*(sl-E)*s; break
                if not half and ((h[i]>=TP1) if s>0 else (l[i]<=TP1)): pnl+=0.5*(TP1-E)*s;half=True;sl=E
                if half and ((h[i]>=TP2) if s>0 else (l[i]<=TP2)): pnl+=0.5*(TP2-E)*s;half=None;break
            else:
                pnl+=(0.5 if half else 1)*(c[ix]-E)*s
            ret=pnl/E-FEE
            bt_all[side].append((nm,d,ret,pnl/R))
json.dump(res,open('ta.json','w'),indent=1)
for nm,x in res.items():
    print(nm,{k:(round(v,5) if isinstance(v,float) else v) for k,v in x.items()})
import statistics
for side,L in bt_all.items():
    if not L: continue
    rets=[x[2] for x in L]; w=[x for x in rets if x>0]
    print(side,'n=',len(L),'win%',round(100*len(w)/len(L),1),'avg ret %',round(100*statistics.mean(rets),3),'avgR',round(statistics.mean(x[3] for x in L),3))
    # walk-forward: first half vs second half by day
    L2=sorted(L,key=lambda x:x[1]);hlf=len(L2)//2
    for part,PP in (('IS',L2[:hlf]),('OOS',L2[hlf:])):
        if PP: print('  ',part,len(PP),round(100*statistics.mean(x[2] for x in PP),3),round(100*sum(1 for x in PP if x[2]>0)/len(PP),1))
    per={}
    for x in L: per.setdefault(x[0],[]).append(x[2])
    print('  per sym',{k:(len(v),round(100*statistics.mean(v),2)) for k,v in per.items()})
