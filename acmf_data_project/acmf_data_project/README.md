# ACMF Data Project
## Agent-Capital-Model-Framework Panel Dataset Builder

### Architecture

```
acmf_data_project/
├── build_panel_dataset.py          # Main orchestrator
├── config/
│   └── (future: API keys, paths)
├── data/
│   ├── metadata/
│   │   └── indicators.yaml         # Full indicator metadata with Fisher scores
│   ├── raw/
│   │   ├── world_bank/             # WB Open Data
│   │   ├── wgi/                    # Worldwide Governance Indicators
│   │   ├── innovation/             # WIPO GII, UNESCO R&D
│   │   ├── world_values_survey/    # WVS, ESS, GSS
│   │   ├── resilience/             # V-Dem, INFORM, IMF fiscal
│   │   └── ...
│   └── processed/
│       ├── panel_dataset.csv         # Final balanced panel
│       └── quality_report.csv      # Coverage & Fisher info per indicator
└── fetchers/
    ├── fetch_world_bank.py
    ├── fetch_wgi.py
    ├── fetch_innovation.py
    ├── fetch_world_values.py
    ├── fetch_resilience.py
    └── __init__.py
```

### Installation

```bash
pip install -r requirements.txt
```

### Quick Start

```bash
# 1. See all available indicators
python build_panel_dataset.py --list-indicators

# 2. Rank by Fisher Information per unit cost
python build_panel_dataset.py --fisher-rank

# 3. Build minimal dataset (Level 1 only, free APIs)
python build_panel_dataset.py --budget minimal --years 1995:2024

# 4. Build standard dataset (Level 1 + 2 + major Level 3)
python build_panel_dataset.py --budget standard --years 1995:2024

# 5. Build comprehensive dataset (all available sources)
python build_panel_dataset.py --budget comprehensive --years 1995:2024

# 6. Focus on specific constructs
python build_panel_dataset.py --budget standard --constructs Ch,M,Y
```

### Indicator Levels

| Level | Name | Constructs | Data Source |
|-------|------|------------|-------------|
| **1** | Core ACMF | Y (Observable State) | World Bank (free API) |
| **2** | Institutions | I (Governance) | WGI (free, manual) |
| **3** | Observation Design | Ch, M, G, V, R | Multiple (see below) |

### Level 3 — Observation Design Proxies

#### Ch — Creativity / Human Potential
| Proxy | Source | API/Format | Cost |
|-------|--------|------------|------|
| Global Innovation Index (GII) | WIPO | CSV download | Free |
| Patent Applications | World Bank | `wbdata` | Free |
| R&D Expenditure | UNESCO / WB | `wbdata` | Free |
| Researchers in R&D | UNESCO / OECD | API key | Free (registration) |
| High-Tech Exports | World Bank | `wbdata` | Free |
| Scientific Papers | World Bank / SCImago | `wbdata` | Free |
| Citation Index | SCImago / Web of Science | Manual / API | Paid (WoS) |
| Knowledge Creation (GII) | WIPO | CSV download | Free |
| Creative Outputs (GII) | WIPO | CSV download | Free |

#### M — Motivation / Engagement
| Proxy | Source | API/Format | Cost |
|-------|--------|------------|------|
| Labor Force Participation | World Bank | `wbdata` | Free |
| Youth Unemployment | World Bank / ILO | `wbdata` | Free |
| HDI | UNDP | API / CSV | Free |
| Working-Age Employment | World Bank / ILO | `wbdata` | Free |
| Job Satisfaction | Gallup / Eurofound | Paid survey | Paid |

#### G — Agency / Entrepreneurship
| Proxy | Source | API/Format | Cost |
|-------|--------|------------|------|
| New Business Density | World Bank | `wbdata` | Free |
| Business Formations | World Bank / UNCTAD | `wbdata` | Free |
| Ease of Doing Business | World Bank | `wbdata` (legacy) | Free |
| Self-Employment Rate | World Bank / ILO | `wbdata` | Free |
| VC Investment | OECD / PitchBook / EMPEA | Manual / Paid | Paid |

#### V — Values / Social Cohesion
| Proxy | Source | API/Format | Cost |
|-------|--------|------------|------|
| Generalized Trust | WVS / ESS / GSS | Microdata download | Free |
| Religiosity | WVS / Pew | Microdata download | Free |
| Tolerance Index | WVS / ESS | Microdata download | Free |
| Civic Participation | OECD / WVS | Microdata download | Free |
| Gini Coefficient | World Bank | `wbdata` | Free |

#### R — Resilience / Buffers
| Proxy | Source | API/Format | Cost |
|-------|--------|------------|------|
| Fiscal Buffer | IMF WEO / World Bank | `wbdata` | Free |
| Forex Reserves | IMF | `wbdata` | Free |
| Institutional Continuity | V-Dem | CSV download | Free |
| Disaster Preparedness | INFORM / UNDRR | CSV download | Free |
| Government Resilience | OECD / Bertelsmann | Manual | Free |
| Recovery Speed | Calculated from WB GDP | Derived | Free |

### Optimal Experimental Design

The builder uses a greedy algorithm to maximize Fisher Information under budget constraint:

```
Fisher Score = (OVI × Coverage × Quality/5) / Cost
```

Where:
- **OVI** = Observed Variable Importance (expert-assigned, 0–1)
- **Coverage** = Expected data availability (0–1)
- **Quality** = Data reliability score (1–5)
- **Cost** = Acquisition cost (1=free API, 5=manual/paid)

Budget scenarios:
- **Minimal** (20): Core ACMF only
- **Standard** (50): Core + Institutions + major Level-3
- **Comprehensive** (100): Full panel
- **Unlimited** (999): Everything available

### Manual Data Integration

Some sources require manual download:

1. **WGI** (Governance): http://info.worldbank.org/governance/wgi/
   → Place `wgidataset.xlsx` in `data/raw/wgi/`

2. **GII** (Innovation): https://www.wipo.int/global_innovation_index/
   → Place `gii_2024.csv` in `data/raw/innovation/`

3. **WVS** (Values): https://www.worldvaluessurvey.org/WVSDocumentation.jsp
   → Place WVS aggregated CSV in `data/raw/world_values_survey/`

4. **V-Dem** (Resilience): https://v-dem.net/data/the-v-dem-dataset/
   → Place `V-Dem-CY-Full+Others-v13.csv` in `data/raw/resilience/`

5. **INFORM** (Disaster Risk): https://drmkc.jrc.ec.europa.eu/inform-index/
   → Place `INFORM_Risk_2024.xlsx` in `data/raw/resilience/`

After placing files, re-run:
```bash
python build_panel_dataset.py --budget comprehensive
```

### Output

```
data/processed/
├── panel_dataset.csv          # Wide-format panel: country × year × indicators
└── quality_report.csv         # Per-indicator coverage & Fisher scores
```

### Citation

If using this dataset, cite:
- World Bank Open Data: https://data.worldbank.org/
- WGI: Kaufmann, D., Kraay, A., & Mastruzzi, M. (2011)
- WIPO GII: https://www.wipo.int/global_innovation_index/
- V-Dem: Coppedge et al. (2023) V-Dem v13
- WVS: Inglehart et al. World Values Survey
