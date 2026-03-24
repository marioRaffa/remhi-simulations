"""
REMHI Simulations Dashboard
Run: streamlit run dashboard/app.py
"""
import yaml, glob, hashlib, datetime
import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

SIMS_DIR = Path(__file__).parent.parent / "simulations"

USERS = {
    "mario":    hashlib.sha256(b"remhi2026").hexdigest(),
    "collega1": hashlib.sha256(b"remhi2026").hexdigest(),
    "admin":    hashlib.sha256(b"admin2026").hexdigest(),
}

# LISTS loaded from lists.yaml — see load_lists()
LISTS_FILE = Path(__file__).parent.parent / "lists.yaml"

def load_lists():
    with open(LISTS_FILE) as f:
        return yaml.safe_load(f)

LISTS_PLACEHOLDER = {
    "experiment":    ["Evalution", "Historical", "SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"],
    "status":        ["Completed", "Ongoing", "Planned", "NOT Planned", "Paused", "Failed"],
    "supercomputer": ["Cassandra", "Juno", "Other Cluster"],
    "project":       ["FUTURA - CORDEX CORE", "EURO-CORDEX"],
    "domain":        ["Africa CORDEX", "ALPAERA"],
    "rcm_model":     ["CCLM", "ICLM"],
    "ic_lbc":        ["ERA5", "GCM"],
}

STATUS_COLORS = {
    "Completed":   "#70AD47", "Ongoing":     "#4472C4",
    "Planned":     "#BF8F00", "NOT Planned": "#C00000",
    "Paused":      "#808080", "Failed":      "#C55A11",
}
STATUS_BG = {
    "Completed":   "#E2EFDA", "Ongoing":     "#D9E1F2",
    "Planned":     "#FFF2CC", "NOT Planned": "#FFDCE0",
    "Paused":      "#F2F2F2", "Failed":      "#FCE4D6",
}

st.set_page_config(page_title="REMHI Simulations", page_icon="🌍",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
[data-testid="stSidebar"]{background:#1F3864}
[data-testid="stSidebar"] *{color:#fff!important}
[data-testid="stSidebar"] select{background:rgba(255,255,255,.1)!important;color:#fff!important}
</style>""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────────────
def check_password(u, p):
    return USERS.get(u) == hashlib.sha256(p.encode()).hexdigest()

def login_form():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            ok = st.form_submit_button("Login", use_container_width=True)
        if ok:
            if check_password(u, p):
                st.session_state.update({"logged_in": True, "username": u})
                st.rerun()
            else:
                st.error("Invalid credentials.")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_simulations():
    sims = []
    for f in sorted(glob.glob(str(SIMS_DIR / "*.yaml"))):
        with open(f) as fh:
            d = yaml.safe_load(fh)
            d["_file"] = f
            sims.append(d)
    return sims

def save_simulation(sim):
    fpath = sim["_file"]
    data = {k: v for k, v in sim.items() if k != "_file"}
    with open(fpath, "w") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    st.cache_data.clear()

def sims_to_df(sims):
    rows = []
    for s in sims:
        c = s.get("compute", {})
        p = s.get("period", {})
        rows.append({
            "#":           s.get("id", ""),
            "Project":     s.get("project", ""),
            "Experiment":  s.get("experiment", ""),
            "Domain":      s.get("domain", ""),
            "Resolution":  s.get("spatial_resolution", ""),
            "Period":      f"{p.get('start','')}/{p.get('end','')}",
            "RCM Model":   s.get("rcm_model", ""),
            "IC/LBC":      s.get("ic_lbc", ""),
            "Status":      s.get("status", ""),
            "Supercomputer": c.get("supercomputer", ""),
            "Cores":       c.get("cores", ""),
            "Run time [h]":c.get("run_time_1yr_h", ""),
            "Size [GB]":   c.get("size_1yr_gb", ""),
            "Work Path":   s.get("work_path", ""),
            "Notes":       s.get("notes", ""),
        })
    return pd.DataFrame(rows)

# ── Sidebar ───────────────────────────────────────────────────────────────────
def sidebar(sims):
    st.sidebar.markdown("## 🌍 REMHI Simulations")
    st.sidebar.markdown("**CMCC — REMHI Division**")
    st.sidebar.markdown("---")

    if st.session_state["logged_in"]:
        st.sidebar.success(f"👤 {st.session_state['username']}")
        if st.sidebar.button("Logout"):
            st.session_state["logged_in"] = False
            st.rerun()
        st.sidebar.markdown("---")

    st.sidebar.markdown("### 🔍 Filters")

    def filt(label, key, values):
        opts = ["All"] + sorted({s.get(key, "") for s in sims} - {""})
        return st.sidebar.selectbox(label, opts)

    sel_proj  = filt("Project",       "project",    LISTS["project"])
    sel_exp   = filt("Experiment",    "experiment", LISTS["experiment"])
    sel_stat  = filt("Status",        "status",     LISTS["status"])
    sel_sc    = st.sidebar.selectbox("Supercomputer",
                    ["All"] + sorted({s.get("compute",{}).get("supercomputer","") for s in sims} - {""}))
    sel_dom   = filt("Domain",        "domain",     LISTS["domain"])
    sel_rcm   = filt("RCM Model",     "rcm_model",  LISTS["rcm_model"])
    sel_lbc   = filt("IC/LBC",        "ic_lbc",     LISTS["ic_lbc"])

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

    return sel_proj, sel_exp, sel_stat, sel_sc, sel_dom, sel_rcm, sel_lbc

def apply_filters(sims, proj, exp, stat, sc, dom, rcm, lbc):
    def match(s, key, val):
        return val == "All" or s.get(key) == val
    def match_sc(s, val):
        return val == "All" or s.get("compute", {}).get("supercomputer") == val
    return [s for s in sims
            if match(s,"project",proj) and match(s,"experiment",exp)
            and match(s,"status",stat) and match_sc(s,sc)
            and match(s,"domain",dom) and match(s,"rcm_model",rcm)
            and match(s,"ic_lbc",lbc)]

# ── KPI row ───────────────────────────────────────────────────────────────────
def kpi_row(sims):
    kpis = [
        ("Total",       len(sims),                                          "#1F3864","#D9E1F2"),
        ("Completed",   sum(1 for s in sims if s.get("status")=="Completed"),"#375623","#E2EFDA"),
        ("Ongoing",     sum(1 for s in sims if s.get("status")=="Ongoing"),  "#1F3864","#D9E1F2"),
        ("Planned",     sum(1 for s in sims if s.get("status")=="Planned"),  "#BF8F00","#FFF2CC"),
        ("NOT Planned", sum(1 for s in sims if s.get("status")=="NOT Planned"),"#C00000","#FFDCE0"),
    ]
    for col, (label, val, fg, bg) in zip(st.columns(5), kpis):
        col.markdown(f"""<div style="background:{bg};border-left:4px solid {fg};
            border-radius:8px;padding:12px 16px;margin-bottom:8px">
            <div style="font-size:10px;color:{fg};font-weight:600;text-transform:uppercase;
                letter-spacing:.05em">{label}</div>
            <div style="font-size:30px;font-weight:500;color:{fg}">{val}</div>
        </div>""", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
def charts(sims):
    df = sims_to_df(sims)
    if df.empty:
        st.info("No data to display.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Status distribution")
        cnt = df["Status"].value_counts().reset_index()
        cnt.columns = ["Status","Count"]
        fig = px.pie(cnt, names="Status", values="Count", hole=0.55,
                     color="Status", color_discrete_map=STATUS_COLORS)
        fig.update_traces(textposition="outside", textinfo="label+value")
        fig.update_layout(showlegend=False, margin=dict(t=10,b=10,l=10,r=10), height=260)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("#### By project & status")
        grp = df.groupby(["Project","Status"]).size().reset_index(name="Count")
        fig2 = px.bar(grp, x="Project", y="Count", color="Status",
                      color_discrete_map=STATUS_COLORS, barmode="stack", text_auto=True)
        fig2.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=260,
                           legend=dict(orientation="h", y=-0.35))
        fig2.update_xaxes(tickangle=-15)
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4, c5 = st.columns(3)
    with c3:
        st.markdown("#### By supercomputer")
        grp3 = df.groupby(["Supercomputer","Status"]).size().reset_index(name="Count")
        fig3 = px.bar(grp3, x="Supercomputer", y="Count", color="Status",
                      color_discrete_map=STATUS_COLORS, barmode="group")
        fig3.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=230,
                           legend=dict(orientation="h", y=-0.4))
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.markdown("#### By experiment")
        grp4 = df.groupby(["Experiment","Status"]).size().reset_index(name="Count")
        fig4 = px.bar(grp4, x="Experiment", y="Count", color="Status",
                      color_discrete_map=STATUS_COLORS, barmode="stack")
        fig4.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=230,
                           legend=dict(orientation="h", y=-0.4))
        fig4.update_xaxes(tickangle=-20)
        st.plotly_chart(fig4, use_container_width=True)

    with c5:
        st.markdown("#### By IC/LBC")
        grp5 = df.groupby(["IC/LBC","Status"]).size().reset_index(name="Count")
        fig5 = px.bar(grp5, x="IC/LBC", y="Count", color="Status",
                      color_discrete_map=STATUS_COLORS, barmode="stack")
        fig5.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=230,
                           legend=dict(orientation="h", y=-0.4))
        st.plotly_chart(fig5, use_container_width=True)

# ── Table ─────────────────────────────────────────────────────────────────────
def simulation_table(sims):
    df = sims_to_df(sims)
    if df.empty:
        st.info("No simulations match the current filters.")
        return
    styled = (df.style
              .map(lambda v: f"background-color:{STATUS_BG.get(v,'#fff')};"
                             f"color:{STATUS_COLORS.get(v,'#000')};font-weight:600",
                   subset=["Status"])
              .set_properties(**{"font-size":"12px"})
              .hide(axis="index"))
    st.dataframe(styled, use_container_width=True, height=320,
                 column_config={
                     "#":             st.column_config.TextColumn(width="small"),
                     "Cores":         st.column_config.NumberColumn(width="small"),
                     "Run time [h]":  st.column_config.NumberColumn(format="%.1f", width="small"),
                     "Size [GB]":     st.column_config.NumberColumn(format="%.0f", width="small"),
                     "IC/LBC":        st.column_config.TextColumn(width="small"),
                 })

# ── Edit panel ────────────────────────────────────────────────────────────────
def edit_panel(sims):
    st.markdown("### ✏️ Edit simulation")
    ids = [s.get("id") for s in sims]
    sel_id = st.selectbox("Select simulation #", ids,
        format_func=lambda x: f"#{x} — "
            f"{next((s.get('experiment','') for s in sims if s.get('id')==x), '')} | "
            f"{next((s.get('project','')    for s in sims if s.get('id')==x), '')}")

    sim = next((s for s in sims if s.get("id") == sel_id), None)
    if not sim: return

    with st.form("edit_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            new_proj = st.selectbox("Project",     LISTS["project"],
                index=LISTS["project"].index(sim.get("project","")) if sim.get("project") in LISTS["project"] else 0)
            new_exp  = st.selectbox("Experiment",  LISTS["experiment"],
                index=LISTS["experiment"].index(sim.get("experiment","")) if sim.get("experiment") in LISTS["experiment"] else 0)
            new_dom  = st.selectbox("Domain",      LISTS["domain"],
                index=LISTS["domain"].index(sim.get("domain","")) if sim.get("domain") in LISTS["domain"] else 0)
            new_res  = st.text_input("Spatial resolution", sim.get("spatial_resolution",""))

        with c2:
            p = sim.get("period", {})
            new_spin  = st.number_input("Spin-up", value=int(p.get("spin_up") or 0), step=1)
            new_start = st.number_input("Start",   value=int(p.get("start")   or 0), step=1)
            new_end   = st.number_input("End",     value=int(p.get("end")     or 0), step=1)
            new_rcm   = st.selectbox("RCM Model",  LISTS["rcm_model"],
                index=LISTS["rcm_model"].index(sim.get("rcm_model","")) if sim.get("rcm_model") in LISTS["rcm_model"] else 0)
            new_lbc   = st.selectbox("IC/LBC",     LISTS["ic_lbc"],
                index=LISTS["ic_lbc"].index(sim.get("ic_lbc","")) if sim.get("ic_lbc") in LISTS["ic_lbc"] else 0)

        with c3:
            cmp = sim.get("compute", {})
            new_stat  = st.selectbox("Status",     LISTS["status"],
                index=LISTS["status"].index(sim.get("status","")) if sim.get("status") in LISTS["status"] else 0)
            new_sc    = st.selectbox("Supercomputer", LISTS["supercomputer"],
                index=LISTS["supercomputer"].index(cmp.get("supercomputer","")) if cmp.get("supercomputer") in LISTS["supercomputer"] else 0)
            new_cores = st.number_input("Cores",   value=int(cmp.get("cores") or 0), step=1)
            new_rt    = st.number_input("Run time 1yr [h]", value=float(cmp.get("run_time_1yr_h") or 0.0), step=0.01)
            new_size  = st.number_input("Size 1yr [GB]",    value=float(cmp.get("size_1yr_gb") or 0.0), step=1.0)

        new_path  = st.text_input("Work Path", sim.get("work_path",""))
        new_notes = st.text_area("Notes",      sim.get("notes",""), height=60)
        submitted = st.form_submit_button("💾 Save changes", use_container_width=True, type="primary")

    if submitted:
        sim.update({
            "project": new_proj, "experiment": new_exp, "domain": new_dom,
            "spatial_resolution": new_res, "rcm_model": new_rcm, "ic_lbc": new_lbc,
            "status": new_stat,
            "period": dict(spin_up=new_spin, start=new_start, end=new_end),
            "compute": dict(supercomputer=new_sc, cores=new_cores,
                            timestep_s=cmp.get("timestep_s",25),
                            relaxation_zone_pts=cmp.get("relaxation_zone_pts",23),
                            run_time_1yr_h=new_rt,
                            output_frequency=cmp.get("output_frequency",""),
                            size_1yr_gb=new_size),
            "work_path": new_path, "notes": new_notes,
        })
        sim.setdefault("metadata",{}).update({
            "updated_at": str(datetime.date.today()),
            "updated_by": st.session_state.get("username",""),
        })
        save_simulation(sim)
        st.success(f"✅ Simulation #{sel_id} saved!")
        st.balloons()

# ── Add panel ─────────────────────────────────────────────────────────────────
def add_panel(sims):
    st.markdown("### ➕ Add new simulation")
    next_id = str(len(sims) + 1).zfill(3)

    with st.form("add_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            proj  = st.selectbox("Project",     LISTS["project"])
            exp   = st.selectbox("Experiment",  LISTS["experiment"])
            dom   = st.selectbox("Domain",      LISTS["domain"])
            res   = st.text_input("Spatial resolution", "0.0275° - 3 km")
        with c2:
            spin  = st.number_input("Spin-up", value=1999, step=1)
            start = st.number_input("Start",   value=2000, step=1)
            end   = st.number_input("End",     value=2009, step=1)
            rcm   = st.selectbox("RCM Model",  LISTS["rcm_model"])
            lbc   = st.selectbox("IC/LBC",     LISTS["ic_lbc"])
        with c3:
            stat  = st.selectbox("Status",      LISTS["status"])
            sc    = st.selectbox("Supercomputer", LISTS["supercomputer"])
            cores = st.number_input("Cores",    value=1536, step=1)
            rt    = st.number_input("Run time 1yr [h]", value=0.0, step=0.01)
            size  = st.number_input("Size 1yr [GB]",    value=0.0, step=1.0)

        path  = st.text_input("Work Path", "")
        notes = st.text_area("Notes", "", height=60)
        submitted = st.form_submit_button("➕ Add to Database", use_container_width=True, type="primary")

    if submitted:
        slug  = f"{next_id}_{proj.replace(' ','_')[:20]}_{exp.replace(' ','_')}"
        fpath = str(SIMS_DIR / f"{slug}.yaml")
        new_sim = dict(
            id=next_id, project=proj, experiment=exp, domain=dom,
            spatial_resolution=res,
            period=dict(spin_up=spin, start=start, end=end),
            rcm_model=rcm, ic_lbc=lbc, status=stat,
            compute=dict(supercomputer=sc, cores=cores, timestep_s=25,
                         relaxation_zone_pts=23, run_time_1yr_h=rt,
                         output_frequency="1 hr - 3 hr - 6 hr", size_1yr_gb=size),
            work_path=path, notes=notes,
            metadata=dict(created_by=st.session_state.get("username",""),
                          created_at=str(datetime.date.today()),
                          updated_at=str(datetime.date.today()))
        )
        with open(fpath, "w") as f:
            yaml.dump(new_sim, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        st.cache_data.clear()
        st.success(f"✅ Simulation #{next_id} added!")
        st.balloons()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global LISTS
    LISTS = load_lists()
    sims = load_simulations()
    filters = sidebar(sims)
    filtered = apply_filters(sims, *filters)

    st.markdown("# 🌍 REMHI Climate Simulations")
    st.markdown(f"**CMCC — REMHI Division** &nbsp;|&nbsp; "
                f"*{len(filtered)} simulation(s) of {len(sims)} total*")
    st.markdown("---")

    if st.session_state["logged_in"]:
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary","📋 Database","✏️ Edit","➕ Add"])
    else:
        tab1, tab2 = st.tabs(["📊 Summary","📋 Database"])

    with tab1:
        kpi_row(filtered)
        st.markdown("---")
        charts(filtered)

    with tab2:
        simulation_table(filtered)
        if not st.session_state["logged_in"]:
            st.info("🔒 Login to edit or add simulations.")
            login_form()

    if st.session_state["logged_in"]:
        with tab3:
            edit_panel(sims)
        with tab4:
            add_panel(sims)

if __name__ == "__main__":
    main()
