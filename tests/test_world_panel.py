import numpy as np
from acmf.world_panel import load_world_panel, world_panel_profile, make_acmf_proxy_panel, top_countries_by_coverage

def test_load_world_panel_bundled_dataset():
    df=load_world_panel(); assert len(df)>=900; assert df['country_name'].nunique()>=30; assert 'Population' in df.columns

def test_world_panel_profile_and_top_countries():
    df=load_world_panel(); profile=world_panel_profile(df); assert profile['countries_count']>=30; assert profile['indicator_count']>=15; assert len(top_countries_by_coverage(df,n=3))==3

def test_make_acmf_proxy_panel_canada():
    df=load_world_panel(); data=make_acmf_proxy_panel(df,'Canada',1995,2023)
    for key in ['t','P','Prod','A','Inst','F','Ch','M','G','V','R']:
        assert key in data and len(data[key])==len(data['t']) and np.all(np.isfinite(data[key]))
    for key in ['Prod','A','Inst','Ch','M','G','V','R']:
        assert data[key].min() >= 0.0 and data[key].max() <= 1.0
