# 🌍 REMHI Climate Simulations

**CMCC — REMHI Division** | Climate simulation tracking system

**Dashboard**: [marioraffa.github.io/remhi-simulations](https://marioraffa.github.io/remhi-simulations/)

---

## Structure

```
remhi-simulations/
├── simulations/        ← one YAML file per simulation
├── docs/index.html     ← GitHub Pages dashboard (browser-only, no server)
├── lists.yaml          ← dropdown options (edit to add/remove values)
├── schema/simulation.schema.yaml
└── scripts/validate.py
```

---

## Dashboard features

| Feature | Description |
|---|---|
| 📊 Summary | KPI cards + 5 charts (status, project, supercomputer, experiment, IC/LBC) |
| 📋 Database | Filterable table with progress bars, core-hrs estimates, deadline badges |
| ➕ Add / ✏️ Edit | Full form — saves YAML directly to the repo via GitHub API |
| 🗑️ Delete | Removes the YAML file from the repo |
| 🔒 Permissions | Only the creator (`added_by`) can edit or delete their own simulations |
| 📊 Progress | Auto-calculated from `actual_start_date` + analysis period |
| ⚡ Core-hrs | Auto = Cores × Run time 1month. Total estimated over full period |
| 💾 Storage | Auto = Size 1month × total months. Total estimated over full period |
| 🔍 Click row | Popup with full details, domain map, progress bar, estimates |

---

## Access

- **Read-only** (no login): open the URL — anyone with the link can view
- **Edit/Add/Delete**: requires a GitHub token with `repo` scope
  - Enter it in the sidebar — saved automatically in the browser
  - Token auto-fills the **Added by** field with your GitHub username
  - Colleagues: invite as Collaborators via *Settings → Collaborators*

---

## Simulation YAML schema

```yaml
id: "001"
project: "FUTURA - CORDEX CORE"      # see lists.yaml
experiment: "Historical"              # Evaluation | Historical | SSP1-2.6 | SSP2-4.5 | SSP3-7.0 | SSP5-8.5
domain: "EUR-CORDEX"                  # see lists.yaml
spatial_resolution: "0.0275 deg - 3 km"
period:
  spin_up: 1995
  start: 1996
  end: 2005                           # analysis years = end - start + 1 = 10 yr
rcm_model: "CCLM"                     # CCLM | ICLM
ic_lbc: "EC-Earth3"                   # reanalysis if Evaluation, CMIP6 GCM otherwise
status: "Ongoing"                     # Completed | Ongoing | Planned | NOT Planned | Paused | Failed
compute:
  supercomputer: "Cassandra"
  cores: 1536
  run_time_1month_h: 4.5              # run time per simulated month [h]
  size_1month_gb: 591                 # output size per simulated month [GB]
  output_frequency: "1 hr - 3 hr - 6 hr"
  timestep_s: 25
  relaxation_zone_pts: 23
actual_start_date: "2025-01-15"       # ISO date — drives progress %
added_by: "Mario Raffa"               # auto-filled from GitHub username
contact_email: "m.raffa@cmcc.it"
delivery_deadline: "2026-12-31"       # expected end of simulation run
domain_map_url: "https://..."         # optional — shown in detail popup
work_path: "/work/..."
notes: ""
metadata:
  created_by: "marioRaffa"
  created_at: "2025-01-10"
  updated_at: "2025-09-01"
  updated_by: "marioRaffa"
```

### Auto-calculated fields (dashboard only, not stored in YAML)

| Field | Formula |
|---|---|
| Analysis period | `(end - start + 1) × 12` months |
| Core-hrs / month | `cores × run_time_1month_h` |
| Total core-hrs | `core-hrs/month × total months` |
| Total storage | `size_1month_gb × total months` |
| Progress % | `months elapsed since actual_start_date / total months` |

---

## Dropdown lists (`lists.yaml`)

Edit directly on GitHub to add/remove options — changes apply immediately.

`experiment` · `status` · `supercomputer` · `project` · `domain` · `rcm_model` · `ic_lbc_reanalysis` · `ic_lbc_gcm`

---

## Validate YAML

```bash
pip install pyyaml
python3 scripts/validate.py
```
