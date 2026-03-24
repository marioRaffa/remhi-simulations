"""
REMHI Simulations Dashboard
Run: streamlit run dashboard/app.py
"""
import yaml, glob, hashlib, datetime
import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

SIMS_DIR   = Path(__file__).parent.parent / "simulations"
LISTS_FILE = Path(__file__).parent.parent / "lists.yaml"

USERS = {
    "mario":    hashlib.sha256(b"remhi2026").hexdigest(),
    "collega1": hashlib.sha256(b"remhi2026").hexdigest(),
    "admin":    hashlib.sha256(b"admin2026").hexdigest(),
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
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div{color:#fff!important}
[data-testid="stSidebar"] .stSelectbox > div > div{
    background:rgba(255,255,255,0.12)!important;
    color:#fff!important;
    border-color:rgba(255,255,255,0.3)!important}
[data-testid="stSidebar"] .stSelectbox svg{fill:#fff!important}
</style>""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def load_lists():
    with open(LISTS_FILE) as f:
        return yaml.safe_load(f)

def get_lbc_list(experiment):
    if experiment == "Evaluation":
        return LISTS.get("ic_lbc_reanalysis", ["ERA5"])
    return LISTS.get("ic_lbc_gcm", ["EC-Earth3"])

def lbc_label(experiment):
    return "IC/LBC — Reanalysis" if experiment == "Evaluation" else "IC/LBC — CMIP6 GCM"

def check_password(u, p):
    return USERS.get(u) == hashlib.sha256(p.encode()).hexdigest()

def safe_index(lst, val):
    return lst.index(val) if val in lst else 0

# ── Auth ──────────────────────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def login_form():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        u  = st.text_input("Username", key="login_u")
        p  = st.text_input("Password", type="password", key="login_p")
        if st.button("Login", use_container_width=True):
            if check_password(u, p):
                st.session_state.update({"logged_in": True, "username": u})
                st.rerun()
            else:
                st.error("Invalid credentials.")

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
            "#":             s.get("id", ""),
            "Project":       s.get("project", ""),
            "Experiment":    s.get("experiment", ""),
            "Domain":        s.get("domain", ""),
            "Resolution":    s.get("spatial_resolution", ""),
            "Period":        f"{p.get('start','')}/{p.get('end','')}",
            "RCM Model":     s.get("rcm_model", ""),
            "IC/LBC":        s.get("ic_lbc", ""),
            "Status":        s.get("status", ""),
            "Supercomputer": c.get("supercomputer", ""),
            "Cores":         c.get("cores", ""),
            "Run time [h]":  c.get("run_time_1yr_h", ""),
            "Size [GB]":     c.get("size_1yr_gb", ""),
            "Work Path":     s.get("work_path", ""),
            "Notes":         s.get("notes", ""),
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

    def filt(label, list_key, key):
        opts = ["All"] + LISTS.get(list_key, [])
        return st.sidebar.selectbox(label, opts, key=key)

    sel_proj = filt("Project",       "project",       "f_proj")
    sel_exp  = filt("Experiment",    "experiment",    "f_exp")
    sel_stat = filt("Status",        "status",        "f_stat")
    sel_sc   = filt("Supercomputer", "supercomputer", "f_sc")
    sel_dom  = filt("Domain",        "domain",        "f_dom")
    sel_rcm  = filt("RCM Model",     "rcm_model",     "f_rcm")
    all_lbc  = ["All"] + LISTS.get("ic_lbc_reanalysis",[]) + LISTS.get("ic_lbc_gcm",[])
    sel_lbc  = st.sidebar.selectbox("IC/LBC", all_lbc, key="f_lbc")

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
        ("Total",       len(sims),                                             "#1F3864","#D9E1F2"),
        ("Completed",   sum(1 for s in sims if s.get("status")=="Completed"),  "#375623","#E2EFDA"),
        ("Ongoing",     sum(1 for s in sims if s.get("status")=="Ongoing"),    "#1F3864","#D9E1F2"),
        ("Planned",     sum(1 for s in sims if s.get("status")=="Planned"),    "#BF8F00","#FFF2CC"),
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
                     "#":            st.column_config.TextColumn(width="small"),
                     "Cores":        st.column_config.NumberColumn(width="small"),
                     "Run time [h]": st.column_config.NumberColumn(format="%.1f", width="small"),
                     "Size [GB]":    st.column_config.NumberColumn(format="%.0f", width="small"),
                     "IC/LBC":       st.column_config.TextColumn(width="medium"),
                 })

# ── Edit panel — NO st.form so widgets react to each other ───────────────────
def edit_panel(sims):
    st.markdown("### ✏️ Edit simulation")

    ids = [s.get("id") for s in sims]
    sel_id = st.selectbox("Select simulation #", ids, key="edit_sel",
        format_func=lambda x: f"#{x}  {next((s.get('experiment','') for s in sims if s.get('id')==x),'')} | "
                              f"{next((s.get('project','') for s in sims if s.get('id')==x),'')}")

    sim = next((s for s in sims if s.get("id") == sel_id), None)
    if not sim:
        return

    cmp = sim.get("compute", {})
    p   = sim.get("period", {})

    st.markdown("---")
    c1, c2, c3 = st.columns(3)

    with c1:
        new_proj = st.selectbox("Project",    LISTS["project"],    key="e_proj",
                                index=safe_index(LISTS["project"], sim.get("project","")))
        new_exp  = st.selectbox("Experiment", LISTS["experiment"], key="e_exp",
                                index=safe_index(LISTS["experiment"], sim.get("experiment","")))
        new_dom  = st.selectbox("Domain",     LISTS["domain"],     key="e_dom",
                                index=safe_index(LISTS["domain"], sim.get("domain","")))
        new_res  = st.text_input("Spatial resolution", sim.get("spatial_resolution",""), key="e_res")

    with c2:
        new_spin  = st.number_input("Spin-up", value=int(p.get("spin_up") or 0), step=1, key="e_spin")
        new_start = st.number_input("Start",   value=int(p.get("start")   or 0), step=1, key="e_start")
        new_end   = st.number_input("End",     value=int(p.get("end")     or 0), step=1, key="e_end")
        new_rcm   = st.selectbox("RCM Model",  LISTS["rcm_model"], key="e_rcm",
                                 index=safe_index(LISTS["rcm_model"], sim.get("rcm_model","")))
        # IC/LBC reacts to new_exp in real time
        lbc_opts  = get_lbc_list(new_exp)
        new_lbc   = st.selectbox(lbc_label(new_exp), lbc_opts, key="e_lbc",
                                 index=safe_index(lbc_opts, sim.get("ic_lbc","")))

    with c3:
        new_stat  = st.selectbox("Status",        LISTS["status"],        key="e_stat",
                                 index=safe_index(LISTS["status"], sim.get("status","")))
        new_sc    = st.selectbox("Supercomputer",  LISTS["supercomputer"], key="e_sc",
                                 index=safe_index(LISTS["supercomputer"], cmp.get("supercomputer","")))
        new_cores = st.number_input("Cores",           value=int(cmp.get("cores") or 0),             step=1,    key="e_cores")
        new_rt    = st.number_input("Run time 1yr [h]",value=float(cmp.get("run_time_1yr_h") or 0.0),step=0.01, key="e_rt")
        new_size  = st.number_input("Size 1yr [GB]",   value=float(cmp.get("size_1yr_gb") or 0.0),   step=1.0,  key="e_size")

    new_path  = st.text_input("Work Path", sim.get("work_path",""), key="e_path")
    new_notes = st.text_area("Notes",      sim.get("notes",""),     key="e_notes", height=60)

    if st.button("💾 Save changes", type="primary", key="e_save", use_container_width=True):
        sim.update({
            "project": new_proj, "experiment": new_exp, "domain": new_dom,
            "spatial_resolution": new_res, "rcm_model": new_rcm, "ic_lbc": new_lbc,
            "status": new_stat,
            "period": dict(spin_up=new_spin, start=new_start, end=new_end),
            "compute": dict(
                supercomputer=new_sc, cores=new_cores,
                timestep_s=cmp.get("timestep_s", 25),
                relaxation_zone_pts=cmp.get("relaxation_zone_pts", 23),
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

# ── Add panel — NO st.form so IC/LBC reacts to experiment ────────────────────
def add_panel(sims):
    st.markdown("### ➕ Add new simulation")
    next_id = str(len(sims) + 1).zfill(3)

    c1, c2, c3 = st.columns(3)

    with c1:
        proj    = st.selectbox("Project",    LISTS["project"],    key="a_proj")
        new_exp = st.selectbox("Experiment", LISTS["experiment"], key="a_exp")
        dom     = st.selectbox("Domain",     LISTS["domain"],     key="a_dom")
        res     = st.text_input("Spatial resolution", "0.0275° - 3 km", key="a_res")

    with c2:
        spin  = st.number_input("Spin-up", value=1999, step=1,   key="a_spin")
        start = st.number_input("Start",   value=2000, step=1,   key="a_start")
        end   = st.number_input("End",     value=2009, step=1,   key="a_end")
        rcm   = st.selectbox("RCM Model",  LISTS["rcm_model"],   key="a_rcm")
        # IC/LBC reacts to experiment in real time
        lbc_opts = get_lbc_list(new_exp)
        lbc      = st.selectbox(lbc_label(new_exp), lbc_opts,    key="a_lbc")

    with c3:
        stat  = st.selectbox("Status",        LISTS["status"],        key="a_stat")
        sc    = st.selectbox("Supercomputer",  LISTS["supercomputer"], key="a_sc")
        cores = st.number_input("Cores",           value=1536, step=1,    key="a_cores")
        rt    = st.number_input("Run time 1yr [h]",value=0.0,  step=0.01, key="a_rt")
        size  = st.number_input("Size 1yr [GB]",   value=0.0,  step=1.0,  key="a_size")

    path  = st.text_input("Work Path", "", key="a_path")
    notes = st.text_area("Notes",      "", key="a_notes", height=60)

    if st.button("➕ Add to Database", type="primary", key="a_save", use_container_width=True):
        slug  = f"{next_id}_{proj.replace(' ','_')[:20]}_{new_exp.replace(' ','_')}"
        fpath = str(SIMS_DIR / f"{slug}.yaml")
        new_sim = dict(
            id=next_id, project=proj, experiment=new_exp, domain=dom,
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
    LISTS    = load_lists()
    sims     = load_simulations()
    filters  = sidebar(sims)
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
