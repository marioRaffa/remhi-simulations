#!/usr/bin/env python3
"""
Validate all simulation YAML files against schema + lists.yaml.
Run: python3 scripts/validate.py
"""
import yaml, glob, sys
from pathlib import Path

ROOT   = Path(__file__).parent.parent
SIMS   = ROOT / "simulations"
SCHEMA = ROOT / "schema" / "simulation.schema.yaml"
LISTS  = ROOT / "lists.yaml"

with open(SCHEMA) as f:
    schema = yaml.safe_load(f)
with open(LISTS) as f:
    lists = yaml.safe_load(f)

errors   = []
warnings = []

for fpath in sorted(glob.glob(str(SIMS / "*.yaml"))):
    fname = Path(fpath).name
    with open(fpath) as f:
        sim = yaml.safe_load(f)

    for field in schema["required"]:
        if field not in sim or sim[field] is None or sim[field] == "":
            errors.append(f"[{fname}] Missing required field: '{field}'")

    checks = [
        ("status",        "status"),
        ("experiment",    "experiment"),
        ("domain",        "domain"),
        ("rcm_model",     "rcm_model"),
        ("ic_lbc",        "ic_lbc"),
        ("project",       "project"),
    ]
    for sim_key, list_key in checks:
        val     = sim.get(sim_key)
        allowed = lists.get(list_key, [])
        if val and val not in allowed:
            warnings.append(
                f"[{fname}] '{sim_key}' value '{val}' not in lists.yaml "
                f"→ allowed: {allowed}"
            )

    sc = sim.get("compute", {}).get("supercomputer")
    if sc and sc not in lists.get("supercomputer", []):
        warnings.append(
            f"[{fname}] 'supercomputer' value '{sc}' not in lists.yaml"
        )

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
