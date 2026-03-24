# 🌍 REMHI Climate Simulations

**CMCC — REMHI Division** | Simulation tracking system

---

## Structure

```
remhi-simulations/
├── simulations/          ← one YAML file per simulation
├── dashboard/
│   └── app.py            ← Streamlit web dashboard
├── scripts/
│   └── validate.py       ← YAML validation
├── schema/
│   └── simulation.schema.yaml
├── requirements.txt
└── README.md
```

---

## Quick start

### 1. Clone the repo
```bash
git clone https://github.com/CMCC-REMHI/remhi-simulations.git
cd remhi-simulations
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the dashboard
```bash
streamlit run dashboard/app.py
```
Opens at **http://localhost:8501**

---

## Dashboard

| Feature | Who |
|---|---|
| View all simulations, charts, filters | Everyone (no login) |
| Edit simulation fields and status | Logged-in users |
| Add new simulations | Logged-in users |

**Default credentials** (change before deploying!):
- `mario` / `remhi2026`
- `collega1` / `remhi2026`
- `admin` / `admin2026`

To change a password, generate a SHA-256 hash:
```bash
python3 -c "import hashlib; print(hashlib.sha256(b'newpassword').hexdigest())"
```
Then update the `USERS` dict in `dashboard/app.py`.

---

## Adding a simulation manually (YAML)

Create a new file in `simulations/` following this template:

```yaml
id: "009"
project: "FUTURA - CORDEX CORE"
experiment: "Historical"
domain: "Greater Alps - 522 x 490 x 50"
spatial_resolution: "0.0275° - 3 km"
period:
  spin_up: 1995
  start: 1996
  end: 2005
rcm_model: "cclm-sp_2.4_terra_urb_2.3.1_clean"
status: "Planned"          # Completed | Ongoing | Planned | NOT Planned | Paused | Failed
compute:
  supercomputer: "Athena"
  cores: 1536
  timestep_s: 25
  relaxation_zone_pts: 23
  run_time_1yr_h: 54.75
  output_frequency: "1 hr - 3 hr - 6 hr"
  size_1yr_gb: 591
nesting: "2nest - CCLM_EURO-CORDEX_0.11 (GCM EC-EARTH RCP4.5)"
work_path: "/work/mr29116/..."
notes: ""
metadata:
  created_by: "your_username"
  created_at: "2026-03-24"
  updated_at: "2026-03-24"
```

Then validate and push:
```bash
python3 scripts/validate.py
git add simulations/009_*.yaml
git commit -m "Add simulation 009: Historical / Greater Alps"
git push
```

---

## Deploy on Streamlit Cloud (free, public URL)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set **Main file path**: `dashboard/app.py`
5. Click **Deploy** → your colleagues get a URL, no install needed

---

## Validation

GitHub Actions automatically validates all YAML files on every push.
Run locally:
```bash
python3 scripts/validate.py
```

---

## Workflow for colleagues

```
Edit YAML or use dashboard
         ↓
  git add + commit + push
         ↓
  GitHub Actions validates
         ↓
  Dashboard auto-refreshes
```
