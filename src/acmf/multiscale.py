from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from .world_panel import make_acmf_proxy_panel, load_world_panel

@dataclass
class ScaleNode:
    node_id: str
    name: str
    level: str
    parent_id: str|None=None

class MultiScaleFrame:
    def __init__(self,nodes,edges,observations):
        self.nodes=pd.DataFrame(nodes); self.edges=pd.DataFrame(edges); self.observations=pd.DataFrame(observations)
    def validate(self):
        ids=set(self.nodes.node_id); obs=set(self.observations.node_id) if len(self.observations) else set()
        return {'ok': obs.issubset(ids), 'n_nodes':len(self.nodes), 'n_edges':len(self.edges), 'n_observations':len(self.observations)}

def build_country_multiscale_frame(countries, start_year=1995, end_year=2024):
    df=load_world_panel(); nodes=[{'node_id':'world:world','name':'World','level':'world','parent_id':None}]; edges=[]; obs=[]
    for c in countries:
        cid='country:'+c.lower().replace(' ','_').replace(',','')
        nodes.append({'node_id':cid,'name':c,'level':'country','parent_id':'world:world'}); edges.append({'source_id':'world:world','target_id':cid,'relation':'contains'})
        d=make_acmf_proxy_panel(df,c,start_year,end_year)
        for i,y in enumerate(d['t']):
            row={'node_id':cid,'Year':int(y)}; row.update({k:float(d[k][i]) for k in ['P','Prod','A','Inst','F','Ch','M','G','V','R']}); obs.append(row)
    return MultiScaleFrame(nodes,edges,obs)
