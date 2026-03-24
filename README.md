# 🌍 REMHI Climate Simulations

**CMCC — REMHI Division** | Climate simulation tracking system

---

## Structure

```
remhi-simulations/
├── simulations/          ← one YAML file per simulation
├── docs/
│   └── index.html        ← GitHub Pages dashboard (HTML+JS, no server needed)
├── dashboard/
│   └── app.py            ← Streamlit dashboard (alternative)
├── scripts/
│   └── validate.py       ← YAML validation
├── schema/
│   └── simulation.schema.yaml
├── lists.yaml            ← single source of truth for all dropdown options
├── requirements.txt
└── README.md
```

---

## Dashboard — GitHub Pages (recommended)

No server needed. Runs entirely in the browser via GitHub API.

**URL**: `https://marioRaffa.github.io/remhi-simulations/`

### Setup (one time)
1. Go to **Settings → Pages**
2. Source: **Deploy from a branch** → Branch: `main` / folder: `/docs`
3. Save → wait ~1 minute

### Usage
- **View**: open the URL — no login needed for public repos
- **Private repo**: enter your GitHub token in the sidebar (saved automatically in browser)
- **Edit simulation**: click ✏️ Edit → opens GitHub editor directly
- **Add simulation**: tab ➕ Add → generates YAML → copy to GitHub

---

## Dropdown lists (`lists.yaml`)

Edit `lists.yaml` directly on GitHub to add/remove options. Changes apply immediately.

| Key | Used for |
|---|---|
| `experiment` | Experiment type |
| `status` | Simulation status |
| `supercomputer` | HPC system |
| `project` | Project name |
| `domain` | CORDEX domain |
| `rcm_model` | Regional Climate Model |
| `ic_lbc_reanalysis` | IC/LBC when experiment = Evaluation |
| `ic_lbc_gcm` | IC/LBC when experiment = Historical or SSP* |

---

## Simulation YAML template

```yaml
id: "009"
project: "FUTURA - CORDEX CORE"   # see lists.yaml → project
experiment: "Historical"           # Evaluation | Historical | SSP1-2.6 | SSP2-4.5 | SSP3-7.0 | SSP5-8.5
domain: "EUR-CORDEX"               # see lists.yaml → domain
spatial_resolution: "0.0275° - 3 km"
period:
  spin_up: 1995
  start: 1996
  end: 2005
rcm_model: "CCLM"                  # CCLM | ICLM
ic_lbc: "EC-Earth3"                # reanalysis if Evaluation, CMIP6 GCM otherwise
status: "Planned"                  # Completed | Ongoing | Planned | NOT Planned | Paused | Failed
compute:
  supercomputer: "Cassandra"       # Cassandra | Juno | Other Cluster
  cores: 1536
  timestep_s: 25
  relaxation_zone_pts: 23
  run_time_1yr_h: 54.75
  output_frequency: "1 hr - 3 hr - 6 hr"
  size_1yr_gb: 591
work_path: "/work/mr29116/..."
notes: ""
metadata:
  created_by: "your_username"
  created_at: "2026-03-24"
  updated_at: "2026-03-24"
```

---

## Validate YAML files

```bash
pip install pyyaml
python3 scripts/validate.py
```

GitHub Actions runs this automatically on every push.
