import json,glob,statistics
exec(open('ta.py').read().split('res={}')[0])
FEE=0.001
out={}
def sim(s,E,R,ie,ix,h,l,c,tp1m=1.8,tp2m=3.0):
    sl=E-s*R;TP1=E+s*tp1m*R;TP2=E+s*tp2m*R;pnl=0;half=False
    for i in range(ie,ix+1):
        if (l[i]<=sl) if s>0 else (h[i]>=sl): return (pnl+(0.5 if half else 1)*(sl-E)*s)/E-FEE
        if not half and ((h[i]>=TP1) if s>0 else (l[i]<=TP1)): pnl+=0.5*(TP1-E)*s;half=True;sl=E
        if half and ((h[i]>=TP2) if s>0 else (l[i]<=TP2)): return (pnl+0.5*(TP2-E)*s)/E-FEE
    return (pnl+(0.5 if half else 1)*(c[ix]-E)*s)/E-FEE
for nm,f,f0 in zip(names,files[:8],files[8:16]):
    k=json.loads(open(f0).read())+json.loads(open(f).read())
    t=[int(x[0]) for x in k];o=[float(x[1]) for x in k];h=[float(x[2]) for x in k];l=[float(x[3]) for x in k];c=[float(x[4]) for x in k];v=[float(x[7]) for x in k]
    e50=ema(c,50);e200=ema(c,200);r=rsi(c);A=atr(h,l,c)
    days=sorted(set(x//86400000 for x in t))
    byd={d:[i for i in range(len(t)) if t[i]//86400000==d] for d in days}
    for di,d in enumerate(days[12:-1],12):
        idx=byd[d];yd=byd[days[di-1]]
        if len(idx)<24: continue
        yL=min(l[i] for i in yd);yH=max(h[i] for i in yd)
        H=lambda hh:[i for i in idx if (t[i]//3600000)%24==hh][0]
        ix=H(14); bear=e50[H(7)]<e200[H(7)]
        # B breakdown short: any 1h close 08-09 UTC below yL with vol>1.5x
        for hh in (8,9):
            i=H(hh); vf=v[i]/(sum(v[i-24:i])/24)
            if bear and c[i]<yL and vf>1.5:
                out.setdefault('B_breakdown_short',[]).append((d,sim(-1,o[i+1],1.5*A[i],i+1,ix,h,l,c)));break
        for hh in (8,9):
            i=H(hh); vf=v[i]/(sum(v[i-24:i])/24)
            if (not bear) and c[i]>yH and vf>1.5:
                out.setdefault('B_breakout_long',[]).append((d,sim(1,o[i+1],1.5*A[i],i+1,ix,h,l,c)));break
        # C: pullback short to EMA50(1h) in bear: high touches ema50 at 08/09 and closes below
        for hh in (8,9):
            i=H(hh)
            if bear and h[i]>=e50[i]>c[i]:
                out.setdefault('C_ema_pullback_short',[]).append((d,sim(-1,o[i+1],1.0*A[i]+ (h[i]-c[i]),i+1,ix,h,l,c)));break
        # D: oversold mean reversion long at 08 UTC in bear trend (RSI<30), TP small
        i=H(8)
        if r[i-1]<30:
            out.setdefault('D_oversold_bounce_long',[]).append((d,sim(1,o[i],1.5*A[i-1],i,ix,h,l,c,1.0,2.0)))
        # E: no-trade baseline short at 08 UTC in bear trend only, hold to 15 UTC
        if bear: out.setdefault('E_plain_bear_short_hold',[]).append((d,(o[H(8)]-c[ix])/o[H(8)]-FEE))
for kk,L in out.items():
    L.sort();R=[x[1] for x in L];hf=len(R)//2
    m=lambda a: round(100*statistics.mean(a),3) if a else None
    print(kk,'n',len(R),'win%',round(100*sum(x>0 for x in R)/len(R),1),'exp%',m(R),'IS',m(R[:hf]),'OOS',m(R[hf:]))
