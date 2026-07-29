from __future__ import annotations
AGE_ORDER=['-1 year','0 to 4 years','5 to 9 years','10 to 14 years','15 to 19 years','20 to 24 years','25 to 29 years','30 to 34 years','35 to 39 years','40 to 44 years','45 to 49 years','50 to 54 years','55 to 59 years','60 to 64 years','65 to 69 years','70 to 74 years','75 to 79 years','80 to 84 years','85 to 89 years','90 to 94 years','95 to 99 years','100 years and older']
def fixed_alpha(a=.2): return {x:(0.0 if x=='-1 year' else float(a)) for x in AGE_ORDER}
