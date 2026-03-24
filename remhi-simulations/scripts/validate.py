#!/usr/bin/env python3
import yaml, glob, sys
from pathlib import Path

ROOT   = Path(__file__).parent.parent
SIMS   = ROOT / "simulations"
SCHEMA = ROOT / "schema" / "simulation.schema.yaml"
LISTS  = ROOT / "lists.yaml"

with open(SCHEMA) as f: schema = yaml.safe_load(f)
with open(LISTS)  as f: lists  = yaml.safe_load(f)

all_lbc = lists.get("ic_lbc_reanalysis",[]) + lists.get("ic_lbc_gcm",[])

errors = []; warnings = []

for fpath in sorted(glob.glob(str(SIMS / "*.yaml"))):
    fname = Path(fpath).name
    with open(fpath) as f: sim = yaml.safe_load(f)

    for field in schema["required"]:
        if field not in sim or sim[field] is None or sim[field] == "":
            errors.append(f"[{fname}] Missing required field: '{field}'")

    for sim_key, list_key in [
        ("status","status"), ("experiment","experiment"),
        ("domain","domain"), ("rcm_model","rcm_model"),
        ("project","project"),
    ]:
        val = sim.get(sim_key)
        allowed = lists.get(list_key,[])
        if val and val not in allowed:
            warnings.append(f"[{fname}] '{sim_key}' value '{val}' not in lists.yaml")

    lbc = sim.get("ic_lbc")
    if lbc and lbc not in all_lbc:
        warnings.append(f"[{fname}] 'ic_lbc' value '{lbc}' not in lists.yaml")

    sc = sim.get("compute",{}).get("supercomputer")
    if sc and sc not in lists.get("supercomputer",[]):
        warnings.append(f"[{fname}] 'supercomputer' value '{sc}' not in lists.yaml")

if errors:
    print(f"\n❌ {len(errors)} ERROR(S):\n")
    for e in errors: print(f"  • {e}")
if warnings:
    print(f"\n⚠️  {len(warnings)} WARNING(S):\n")
    for w in warnings: print(f"  • {w}")
if not errors and not warnings:
    n = len(list(glob.glob(str(SIMS / "*.yaml"))))
    print(f"✅ All {n} simulations are valid.")

sys.exit(1 if errors else 0)
