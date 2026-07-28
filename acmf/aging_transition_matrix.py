from __future__ import annotations
import pandas as pd
AGE_ORDER=['-1 year','0 to 4 years','5 to 9 years','10 to 14 years','15 to 19 years','20 to 24 years','25 to 29 years','30 to 34 years','35 to 39 years','40 to 44 years','45 to 49 years','50 to 54 years','55 to 59 years','60 to 64 years','65 to 69 years','70 to 74 years','75 to 79 years','80 to 84 years','85 to 89 years','90 to 94 years','95 to 99 years','100 years and older']
def fixed_alpha(a=.2): return {x:(0.0 if x=='-1 year' else float(a)) for x in AGE_ORDER}
def transition_matrix(alpha):
    rows=[]
    for i,a in enumerate(AGE_ORDER):
        if a=='-1 year': continue
        if a=='100 years and older': rows.append({'age_from':a,'age_to':a,'probability':1.0})
        else:
            q=alpha.get(a,.2); rows.append({'age_from':a,'age_to':a,'probability':1-q}); rows.append({'age_from':a,'age_to':AGE_ORDER[i+1],'probability':q})
    return pd.DataFrame(rows)
def apply_aging(pop_t,alpha):
    out=[]
    for (geo,gender),g in pop_t.groupby(['geo','gender']):
        mp=dict(zip(g.age_group,g.population))
        for i,age in enumerate(AGE_ORDER):
            if age=='-1 year': val=0.0
            elif age=='0 to 4 years': val=(1-alpha.get(age,.2))*mp.get(age,0.0)
            elif age=='100 years and older': val=mp.get(age,0.0)+alpha.get(AGE_ORDER[i-1],.2)*mp.get(AGE_ORDER[i-1],0.0)
            else: val=(1-alpha.get(age,.2))*mp.get(age,0.0)+alpha.get(AGE_ORDER[i-1],.2)*mp.get(AGE_ORDER[i-1],0.0)
            out.append({'geo':geo,'gender':gender,'age_group':age,'population_pred':val})
    return pd.DataFrame(out)
