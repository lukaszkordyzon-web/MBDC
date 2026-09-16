import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from parsers import (
    build_master_dataframe,
    parse_detonator_pdf,
    parse_iredes_xml,
    parse_quarryx_csv,
    parse_txt_file,
)
import streamlit as st

st.set_page_config(
    page_title="BlastDataHub · PoC", page_icon="💥", layout="wide"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');

    html, body, [class*="css"] {
      font-family: 'Inter', sans-serif;
    }

    /* --- Ambient backdrop: a soft multi-hue mesh instead of a flat glow --- */
    [data-testid="stAppViewContainer"] {
      position: relative;
      background:
        radial-gradient(900px circle at 6% -12%, rgba(239, 68, 68, 0.14), transparent 55%),
        radial-gradient(700px circle at 100% 0%, rgba(249, 115, 22, 0.09), transparent 50%),
        radial-gradient(1000px circle at 40% 115%, rgba(168, 85, 247, 0.07), transparent 55%),
        #09090b;
    }
    [data-testid="stAppViewContainer"]::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      opacity: 0.05;
      mix-blend-mode: overlay;
      background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
    }
    section[data-testid="stSidebar"] {
      background: #0c0c0e;
      border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    h1, h2, h3, h4, .adc-hero h1 {
      font-family: 'Manrope', 'Inter', sans-serif;
      letter-spacing: -0.02em;
    }

    /* --- Hero: glass surface with a gradient border and a warm glow --- */
    .adc-hero {
      position: relative;
      overflow: hidden;
      z-index: 1;
      padding: 2.1rem 2.35rem;
      border-radius: 22px;
      margin-bottom: 1.5rem;
      border: 1px solid transparent;
      background:
        linear-gradient(#141316, #141316) padding-box,
        linear-gradient(120deg, rgba(239, 68, 68, 0.65), rgba(249, 115, 22, 0.4) 50%, rgba(168, 85, 247, 0.35)) border-box;
      backdrop-filter: blur(10px);
      box-shadow: 0 28px 56px -24px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }
    .adc-hero::before {
      content: "";
      position: absolute;
      top: -110px;
      right: -70px;
      width: 340px;
      height: 340px;
      background: radial-gradient(circle, rgba(249, 115, 22, 0.45), rgba(239, 68, 68, 0.25) 45%, transparent 72%);
      filter: blur(20px);
      pointer-events: none;
    }
    .adc-hero::after {
      content: "";
      position: absolute;
      bottom: -120px;
      left: -60px;
      width: 260px;
      height: 260px;
      background: radial-gradient(circle, rgba(168, 85, 247, 0.28), transparent 70%);
      filter: blur(24px);
      pointer-events: none;
    }
    .adc-hero h1 {
      position: relative;
      z-index: 1;
      color: #f5f5f7;
      margin: 0;
      font-weight: 800;
      font-size: 2.3rem;
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.6rem;
    }
    .adc-title-gradient {
      background: linear-gradient(120deg, #ffffff 8%, #fecaca 42%, #fdba74 75%, #fde68a 100%);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }
    .adc-hero p {
      position: relative;
      z-index: 1;
      color: #a5a3ab;
      margin: 0.55rem 0 0 0;
      font-size: 0.98rem;
      max-width: 60ch;
    }
    .adc-poc-badge {
      display: inline-block;
      background: linear-gradient(120deg, #fbbf24, #f97316);
      color: #1a1206;
      padding: 0.3rem 0.85rem;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      vertical-align: middle;
      box-shadow: 0 4px 16px -2px rgba(249, 115, 22, 0.55);
    }

    .adc-poc-banner {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      background: rgba(245, 158, 11, 0.1);
      border: 1px solid rgba(245, 158, 11, 0.35);
      color: #fcd34d;
      padding: 0.7rem 1.1rem;
      border-radius: 14px;
      font-size: 0.88rem;
      font-weight: 500;
      margin-bottom: 1.5rem;
    }

    .adc-sidebar-poc {
      display: inline-block;
      background: linear-gradient(135deg, #fbbf24, #f59e0b);
      color: #1a1206;
      padding: 0.18rem 0.55rem;
      border-radius: 999px;
      font-size: 0.68rem;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 0.5rem;
    }

    /* --- Consistent type scale: section (h3) > subsection (h4) --- */
    h3 {
      font-size: 1.2rem !important;
      font-weight: 700 !important;
      margin-top: 0.25rem !important;
      margin-bottom: 0.75rem !important;
    }
    h4 {
      font-size: 0.98rem !important;
      font-weight: 700 !important;
      margin-top: 0.25rem !important;
      margin-bottom: 0.5rem !important;
    }

    /* --- Metrics: modern soft cards with a gentle hover lift --- */
    div[data-testid="stMetric"] {
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 14px;
      padding: 0.75rem 1rem;
      margin-bottom: 0.5rem;
      transition: border-color 0.15s ease, transform 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
      border-color: rgba(255, 255, 255, 0.18);
      transform: translateY(-1px);
    }
    div[data-testid="stMetricValue"] {
      font-size: 1.3rem !important;
      white-space: normal !important;
      overflow-wrap: break-word;
      line-height: 1.25 !important;
      font-family: 'Manrope', 'Inter', sans-serif;
    }
    div[data-testid="stMetricLabel"] {
      font-size: 0.76rem !important;
      opacity: 0.65;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .adc-subsection {
      font-size: 0.92rem;
      font-weight: 700;
      margin: 0.25rem 0 0.5rem 0.75rem;
      padding-left: 0.75rem;
      border-left: 3px solid transparent;
      border-image: linear-gradient(180deg, #ef4444, #f97316) 1;
    }

    /* --- Cards: st.container(border=True) renders as a stVerticalBlock
           wrapped in a stLayoutWrapper in this Streamlit version.
           Glass surface with a gradient glow that appears on hover. --- */
    div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"] {
      border-radius: 18px !important;
      border: 1px solid rgba(255, 255, 255, 0.09) !important;
      background: rgba(255, 255, 255, 0.025) !important;
      backdrop-filter: blur(8px);
      padding: 1.15rem 1.35rem !important;
      margin-bottom: 1.1rem !important;
      transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }
    div[data-testid="stLayoutWrapper"] > div[data-testid="stVerticalBlock"]:hover {
      border-color: rgba(249, 115, 22, 0.4) !important;
      box-shadow: 0 0 0 1px rgba(249, 115, 22, 0.08), 0 16px 40px -24px rgba(239, 68, 68, 0.5);
    }

    /* --- Primary buttons: fire gradient, tactile, glowing on hover --- */
    section[data-testid="stSidebar"] .stButton button,
    div.stForm button {
      background: linear-gradient(120deg, #ef4444, #f97316);
      color: white;
      border: none;
      border-radius: 10px;
      font-weight: 600;
      padding: 0.5rem 1.1rem;
      box-shadow: 0 4px 14px -4px rgba(239, 68, 68, 0.55);
      transition: transform 0.12s ease, box-shadow 0.12s ease, filter 0.12s ease;
    }
    section[data-testid="stSidebar"] .stButton button:hover,
    div.stForm button:hover {
      filter: brightness(1.08);
      transform: translateY(-1px);
      box-shadow: 0 10px 26px -6px rgba(249, 115, 22, 0.6);
    }
    section[data-testid="stSidebar"] .stButton button:active,
    div.stForm button:active {
      transform: translateY(0);
    }

    /* --- Secondary / download buttons: quiet ghost style, not a solid block --- */
    .stDownloadButton button {
      background: transparent;
      color: #fdba74;
      border: 1px solid rgba(249, 115, 22, 0.45);
      border-radius: 10px;
      font-weight: 600;
      padding: 0.45rem 1rem;
      box-shadow: none;
      transition: background 0.12s ease, border-color 0.12s ease, color 0.12s ease;
    }
    .stDownloadButton button:hover {
      background: rgba(249, 115, 22, 0.12);
      border-color: #f97316;
      color: #ffffff;
    }

    /* --- Inputs: rounded with a warm gradient-toned focus ring --- */
    div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="base-input"] {
      border-radius: 10px !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
      box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.4) !important;
    }

    /* --- Tabs as a modern segmented control instead of an underline --- */
    div[data-testid="stTabs"] div[data-baseweb="tab-border"] {
      display: none;
    }
    div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {
      display: none;
    }
    div[data-testid="stTabs"] div[role="tablist"] {
      background: rgba(255, 255, 255, 0.035);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 14px;
      padding: 4px;
      gap: 2px;
      width: fit-content;
    }
    button[data-testid="stTab"] {
      font-size: 0.92rem;
      font-weight: 600;
      padding: 0.55rem 1.1rem;
      color: #96959c;
      border-radius: 10px !important;
      border: none !important;
      transition: background 0.15s ease, color 0.15s ease;
    }
    button[data-testid="stTab"]:hover {
      color: #f5f5f7;
      background: rgba(255, 255, 255, 0.04);
    }
    button[data-testid="stTab"][aria-selected="true"] {
      color: #ffffff;
      background: linear-gradient(120deg, #ef4444, #f97316);
      box-shadow: 0 4px 14px -4px rgba(239, 68, 68, 0.55);
    }

    /* --- Thin, dark scrollbar for a tidier feel --- */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 8px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
    </style>
    """,
    unsafe_allow_html=True,
)

if "projects" not in st.session_state:
  st.session_state.projects = {}

if "current_project" not in st.session_state:
  st.session_state.current_project = None

# --- SIDEBAR: PROJECT MANAGEMENT ---
st.sidebar.title("💥 BlastDataHub")
st.sidebar.markdown(
    '<span class="adc-sidebar-poc">⚠️ Proof of Concept</span>',
    unsafe_allow_html=True,
)
st.sidebar.caption("Blast & drilling data aggregation")

with st.sidebar.form("new_proj_form"):
  new_name = st.text_input("Project name")
  if st.form_submit_button("Create project") and new_name:
    if new_name not in st.session_state.projects:
      st.session_state.projects[new_name] = {
          "design": {},
          "actual": {},
          "files_parsed": {},
          "field_files_parsed": {},
          "hole_overrides": {},
      }
      st.session_state.current_project = new_name
      st.sidebar.success(f"Created: **{new_name}**")
    else:
      st.sidebar.warning("Project already exists.")

if st.session_state.projects:
  projs = list(st.session_state.projects.keys())
  st.session_state.current_project = st.sidebar.selectbox(
      "Select active project",
      projs,
      index=projs.index(st.session_state.current_project)
      if st.session_state.current_project in projs
      else 0,
  )

# --- MAIN PANEL ---
st.markdown(
    """
    <div class="adc-hero">
      <h1>💥 <span class="adc-title-gradient">BlastDataHub</span> <span class="adc-poc-badge">Proof of Concept</span></h1>
      <p>Aggregate drill plans, MWD reports and detonator logs into one blast database.</p>
    </div>
    <div class="adc-poc-banner">
      ⚠️ This is a Proof of Concept build — for internal testing and demonstration only, not production data.
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.current_project:
  st.info("👈 Select or create a project in the sidebar.")
else:
  curr_proj = st.session_state.current_project
  curr_data = st.session_state.projects[curr_proj]
  curr_data.setdefault("field_files_parsed", {})
  curr_data.setdefault("hole_overrides", {})

  CHARGE_TYPE_OPTIONS = ["Bulk emulsion", "Bulk ANFO", "Cartridge", "Other"]

  def render_hole_card(df, key_prefix):
    """Renders the hole selector, parameters, burden analytics, charge
    override form and 2D cross-section chart for the given hole dataframe."""
    if df is None or df.empty:
      st.info("ℹ️ Upload files to generate the hole database.")
      return

    st.subheader("🔍 Hole card")

    hole_list = df["Hole"].tolist()
    sel_hole = st.selectbox(
        "Select hole to analyze:", hole_list, key=f"{key_prefix}_hole_select"
    )

    hole_row = df[df["Hole"] == sel_hole].iloc[0]

    val_x = (
        hole_row.get("X")
        if pd.notna(hole_row.get("X"))
        else hole_row.get("XML_StartX")
    )
    val_y = (
        hole_row.get("Y")
        if pd.notna(hole_row.get("Y"))
        else hole_row.get("XML_StartY")
    )
    val_z = (
        hole_row.get("Z")
        if pd.notna(hole_row.get("Z"))
        else hole_row.get("XML_StartZ")
    )

    val_bx = (
        hole_row.get("BottomX")
        if pd.notna(hole_row.get("BottomX"))
        else hole_row.get("XML_EndX")
    )
    val_by = (
        hole_row.get("BottomY")
        if pd.notna(hole_row.get("BottomY"))
        else hole_row.get("XML_EndY")
    )
    val_bz = (
        hole_row.get("BottomZ")
        if pd.notna(hole_row.get("BottomZ"))
        else hole_row.get("XML_EndZ")
    )

    val_len = (
        hole_row.get("Length")
        if pd.notna(hole_row.get("Length"))
        else hole_row.get("TXT_Depth", 0.0)
    )
    val_ang = (
        hole_row.get("Angle")
        if pd.notna(hole_row.get("Angle"))
        else hole_row.get("TXT_Angle", 0.0)
    )
    val_az = (
        hole_row.get("Azimuth")
        if pd.notna(hole_row.get("Azimuth"))
        else hole_row.get("TXT_Azimuth", 0.0)
    )

    # Read hole diameter with a safe fallback
    raw_dia = hole_row.get("Hole diameter")
    if (
        pd.notna(raw_dia)
        and str(raw_dia).strip().lower() != "nan"
        and float(raw_dia) > 0
    ):
      val_dia = int(float(raw_dia))
    elif (
        pd.notna(hole_row.get("BitDia_XML_mm"))
        and float(hole_row.get("BitDia_XML_mm")) > 0
    ):
      val_dia = int(float(hole_row.get("BitDia_XML_mm")))
    else:
      val_dia = 100

    val_exp = (
        hole_row.get("Explosives Design")
        if pd.notna(hole_row.get("Explosives Design"))
        else 0.0
    )
    val_deck = (
        hole_row.get("Deck 1 timing")
        if pd.notna(hole_row.get("Deck 1 timing"))
        else "None"
    )

    card_left, card_right = st.columns([1, 1.2])

    with card_left, st.container(border=True):
      st.markdown("#### 📐 Hole Parameters")
      st.caption(
          f"Collar: `{val_x}, {val_y}, {val_z}`  •  Bottom:"
          f" `{val_bx}, {val_by}, {val_bz}`"
      )
      m1, m2 = st.columns(2)
      m1.metric("Length", f"{val_len} m")
      m2.metric("Diameter", f"{val_dia} mm")
      m3, m4 = st.columns(2)
      m3.metric("Angle", f"{val_ang}°")
      m4.metric("Azimuth", f"{val_az}°")
      m5, m6 = st.columns(2)
      m5.metric("Delay", f"{val_deck} ms")
      m6.metric("Explosive mass", f"{val_exp} kg")

      st.markdown("#### 📊 Burden Analytics")
      b1, b2 = st.columns(2)
      b1.metric("Crest burden", f"{hole_row.get('Crest_Burden_m', 'None')} m")
      b2.metric("Toe burden", f"{hole_row.get('Toe_Burden_m', 'None')} m")
      b3, b4 = st.columns(2)
      b3.metric(
          "Min. burden",
          f"{hole_row.get('Min_Burden_m', 'None')} m",
          help=(
              "Depth:"
              f" {hole_row.get('Min_Burden_Depth_m', '-')} m"
          ),
      )
      b4.metric(
          "Max. burden",
          f"{hole_row.get('Max_Burden_m', 'None')} m",
          help=(
              "Depth:"
              f" {hole_row.get('Max_Burden_Depth_m', '-')} m"
          ),
      )
      st.metric("Mean burden", f"{hole_row.get('Mean_Burden_m', 'None')} m")

      raw_json = hole_row.get("Burden_Profile_JSON")
      if pd.notna(raw_json) and raw_json:
        with st.expander("📦 Full JSON record"):
          st.json(json.loads(raw_json))

      st.markdown("#### 💣 Charge Parameters")
      st.caption("Manual Adjustment (in case data is missing)")
      hole_key = str(sel_hole)
      overrides_ns = curr_data["hole_overrides"].setdefault(key_prefix, {})
      existing_override = overrides_ns.get(hole_key, {})
      with st.form(f"hole_charge_form_{key_prefix}_{hole_key}"):
        hc_stemming = st.number_input(
            "Stemming length [m]",
            min_value=0.0,
            value=existing_override.get("stemming_length", 0.0),
            key=f"hc_stem_{key_prefix}_{hole_key}",
        )
        hc_inter_stemming = st.number_input(
            "Intermediate stemming length [m]",
            min_value=0.0,
            value=existing_override.get("intermediate_stemming_length", 0.0),
            key=f"hc_interstem_{key_prefix}_{hole_key}",
        )
        hc_charge = st.number_input(
            "Explosive charge [kg]",
            min_value=0.0,
            value=existing_override.get("explosive_charge", 0.0),
            key=f"hc_charge_{key_prefix}_{hole_key}",
        )
        hc_type = st.selectbox(
            "Explosive type",
            CHARGE_TYPE_OPTIONS,
            index=CHARGE_TYPE_OPTIONS.index(
                existing_override.get("explosive_type", CHARGE_TYPE_OPTIONS[0])
            ),
            key=f"hc_type_{key_prefix}_{hole_key}",
        )

        save_col1, save_col2 = st.columns(2)
        save_this = save_col1.form_submit_button("💾 Save for this hole")
        save_all = save_col2.form_submit_button("📋 Save for all holes")

        new_charge = {
            "stemming_length": hc_stemming,
            "intermediate_stemming_length": hc_inter_stemming,
            "explosive_charge": hc_charge,
            "explosive_type": hc_type,
        }
        if save_this:
          overrides_ns[hole_key] = new_charge
          st.success(f"Charge parameters saved for {hole_key}!")
        elif save_all:
          for h in hole_list:
            overrides_ns[str(h)] = dict(new_charge)
          st.success(f"Charge parameters saved for all {len(hole_list)} holes!")

    with card_right, st.container(border=True):
      st.markdown("#### 📉 2D Cross-Section with Perpendicular Dimensioning")
      raw_json = hole_row.get("Burden_Profile_JSON")
      if pd.notna(raw_json) and raw_json:
        pts = json.loads(raw_json)
        depths = [p["depth"] for p in pts]
        burdens = [p["burden"] for p in pts]

        ang_deg = float(val_ang) if pd.notna(val_ang) else 0.0
        ang_rad = np.radians(ang_deg)

        hole_x = np.array([d * np.sin(ang_rad) for d in depths])
        hole_z = np.array([-d * np.cos(ang_rad) for d in depths])

        face_x = hole_x + np.array(burdens) * np.cos(ang_rad)
        face_z = hole_z + np.array(burdens) * np.sin(ang_rad)

        fig, ax = plt.subplots(figsize=(5.5, 7.5))
        fig.patch.set_facecolor("#0f172a")
        ax.set_facecolor("#1e293b")
        ax.tick_params(colors="#e2e8f0")
        ax.xaxis.label.set_color("#e2e8f0")
        ax.yaxis.label.set_color("#e2e8f0")
        for spine in ax.spines.values():
          spine.set_color("#475569")
        ax.plot(
            hole_x,
            hole_z,
            color="red",
            linestyle="--",
            linewidth=2.5,
            label=f"Hole axis {sel_hole} ({ang_deg}°)",
        )
        ax.plot(
            face_x,
            face_z,
            color="black",
            linestyle="-",
            linewidth=2.0,
            label="Rock face (Profile)",
        )
        ax.fill_betweenx(
            hole_z,
            hole_x,
            face_x,
            color="#cbd5e1",
            alpha=0.35,
            label="Burden (Rock mass)",
        )

        for d, b, hx, hz, fx, fz in zip(
            depths, burdens, hole_x, hole_z, face_x, face_z
        ):
          if abs(d - round(d)) < 1e-4 and round(d) % 1 == 0:
            ax.plot(
                [hx, fx],
                [hz, fz],
                color="#fbbf24",
                linestyle=":",
                linewidth=1.3,
            )
            mid_x = (hx + fx) / 2
            mid_z = (hz + fz) / 2
            ax.text(
                mid_x,
                mid_z + 0.12,
                f"{b:.2f} m",
                color="#fbbf24",
                fontsize=7.5,
                ha="center",
                va="bottom",
                weight="bold",
                rotation=ang_deg,
            )

        ax.set_xlabel("Horizontal distance [m]", fontsize=9)
        ax.set_ylabel("Vertical elevation (downward) [m]", fontsize=9)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, linestyle=":", alpha=0.3, color="#475569")
        legend = ax.legend(loc="lower right", fontsize=8)
        legend.get_frame().set_facecolor("#1e293b")
        legend.get_frame().set_edgecolor("#475569")
        for text in legend.get_texts():
          text.set_color("#e2e8f0")
        st.pyplot(fig, width=950)
      else:
        st.info("No TXT burden profile available for this hole.")

  def render_pattern_plan(df):
    """Draws a dotted plan-view scatter of every hole's collar position."""
    if df is None or df.empty:
      return

    xs, ys, labels = [], [], []
    for _, row in df.iterrows():
      x_val = row.get("X") if pd.notna(row.get("X")) else row.get("XML_StartX")
      y_val = row.get("Y") if pd.notna(row.get("Y")) else row.get("XML_StartY")
      if pd.notna(x_val) and pd.notna(y_val):
        xs.append(float(x_val))
        ys.append(float(y_val))
        labels.append(str(row.get("Hole")))

    if not xs:
      return

    st.markdown("#### 🗺️ Blast Pattern Plan View")
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")
    ax.tick_params(colors="#e2e8f0")
    ax.xaxis.label.set_color("#e2e8f0")
    ax.yaxis.label.set_color("#e2e8f0")
    for spine in ax.spines.values():
      spine.set_color("#475569")

    ax.scatter(
        xs, ys, color="#fbbf24", s=70, edgecolors="#7c3aed", linewidths=1.4, zorder=3
    )
    for x_val, y_val, label in zip(xs, ys, labels):
      ax.annotate(
          label,
          (x_val, y_val),
          textcoords="offset points",
          xytext=(6, 6),
          fontsize=7.5,
          color="#e2e8f0",
      )

    ax.set_xlabel("X [m]", fontsize=9)
    ax.set_ylabel("Y [m]", fontsize=9)
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linestyle=":", alpha=0.3, color="#475569")
    st.pyplot(fig, width=700)

  def build_database_table(design_df, actual_df):
    """Combines the design/project dataframe's design-only fields
    (Explosives Design, Charge length design...) with the true-field
    dataframe's actual-only fields (Explosives Actual, Charge length
    actual...), matched per hole. Manually entered Charge Parameters
    (from each tab's Hole card) fill in Explosives Design/Actual when
    the uploaded files left them empty or zero, and always supply the
    Stemming length / Explosive type columns, which have no file-based
    source."""
    actual_cols = [
        "Explosives Actual",
        "Charge length actual",
        "Charge length actual without stemming",
    ]

    has_design = design_df is not None and not design_df.empty
    has_actual = actual_df is not None and not actual_df.empty

    if not has_design and not has_actual:
      return None

    if has_design:
      base = design_df.drop(
          columns=[c for c in actual_cols if c in design_df.columns]
      ).copy()
    else:
      base = actual_df[["Hole"]].drop_duplicates().copy()

    if has_actual:
      present = [c for c in actual_cols if c in actual_df.columns]
      actual_subset = (
          actual_df[["Hole"] + present] if present else actual_df[["Hole"]]
      )
      base = base.merge(actual_subset, on="Hole", how="outer")

    for col in ("Explosives Design", "Explosives Actual"):
      if col not in base.columns:
        base[col] = pd.NA

    proj_overrides = curr_data["hole_overrides"].get("proj", {})
    field_overrides = curr_data["hole_overrides"].get("field", {})

    def filled_explosive_mass(row, col, overrides):
      val = row.get(col)
      if pd.notna(val) and float(val) != 0:
        return val
      override = overrides.get(str(row.get("Hole")))
      if override and override.get("explosive_charge"):
        return override["explosive_charge"]
      return val

    def override_value(overrides, field):
      return lambda row: overrides.get(str(row.get("Hole")), {}).get(field)

    if proj_overrides:
      base["Explosives Design"] = base.apply(
          lambda r: filled_explosive_mass(r, "Explosives Design", proj_overrides),
          axis=1,
      )
      base["Stemming Length Design [m]"] = base.apply(
          override_value(proj_overrides, "stemming_length"), axis=1
      )
      base["Intermediate Stemming Design [m]"] = base.apply(
          override_value(proj_overrides, "intermediate_stemming_length"), axis=1
      )
      base["Explosive Type Design"] = base.apply(
          override_value(proj_overrides, "explosive_type"), axis=1
      )

    if field_overrides:
      base["Explosives Actual"] = base.apply(
          lambda r: filled_explosive_mass(r, "Explosives Actual", field_overrides),
          axis=1,
      )
      base["Stemming Length Actual [m]"] = base.apply(
          override_value(field_overrides, "stemming_length"), axis=1
      )
      base["Intermediate Stemming Actual [m]"] = base.apply(
          override_value(field_overrides, "intermediate_stemming_length"), axis=1
      )
      base["Explosive Type Actual"] = base.apply(
          override_value(field_overrides, "explosive_type"), axis=1
      )

    return base

  st.markdown(f"### 📍 Project: `{curr_proj}`")
  st.divider()

  tab_project, tab_field, tab_database = st.tabs(
      ["📁 Project Files", "📡 True Field Data", "📊 Hole Database"]
  )

  # --- TAB 1: PROJECT FILE UPLOAD ---
  with tab_project:
    st.subheader("📁 Project Files")

    with st.container(border=True):
      st.caption("Add your project files in xml, csv, txt, pdf formats.")
      uploaded_files = st.file_uploader(
          "Upload project package",
          type=["xml", "csv", "txt", "pdf"],
          accept_multiple_files=True,
          key=f"upl_des_{curr_proj}",
      )

      if uploaded_files:
        for f in uploaded_files:
          f_bytes = f.read()
          ext = f.name.split(".")[-1].lower()

          if ext == "xml":
            res = parse_iredes_xml(f_bytes)
            if res.get("status") == "success":
              curr_data["files_parsed"]["xml"] = res
              st.success(f"✅ XML: {f.name} ({res['holes_count']} holes)")
            else:
              st.error(f"❌ XML: {f.name} — {res.get('message')}")

          elif ext == "csv":
            res = parse_quarryx_csv(f_bytes)
            if res.get("status") == "success":
              curr_data["files_parsed"]["csv"] = res
              st.success(f"✅ CSV: {f.name} ({res['holes_count']} holes)")
            else:
              st.error(f"❌ CSV: {f.name} — {res.get('message')}")

          elif ext == "txt":
            res = parse_txt_file(f_bytes)
            if res.get("status") == "success":
              curr_data["files_parsed"]["txt"] = res
              st.success(f"✅ TXT: {f.name} ({res['holes_count']} profiles)")
            else:
              st.error(f"❌ TXT: {f.name} — {res.get('message')}")

          elif ext == "pdf":
            res = parse_detonator_pdf(f_bytes)
            if res.get("status") == "success":
              curr_data["files_parsed"]["pdf"] = res
              st.success(f"✅ PDF: {f.name}")
            else:
              st.error(f"❌ PDF: {f.name} — {res.get('message')}")

      project_master_df = build_master_dataframe(curr_data["files_parsed"])

      if "xml" in curr_data["files_parsed"]:
        x = curr_data["files_parsed"]["xml"]
        st.markdown("#### ℹ️ Project metadata (from XML file)")
        st.info(
            f"🛠️ **Software:** {x.get('generated_by')} | 📅 **Date:**"
            f" {x.get('creation_date')}\n\n👤 **Author:** {x.get('author')} | 🏢"
            f" **Client:** {x.get('project')}\n\n📍 **Work order:**"
            f" {x.get('work_order')}\n\n📐 **Grid:** First row burden ="
            f" **{x.get('first_row_burden')} m** | Spacing ="
            f" **{x.get('spacing')} m** | Rock volume ="
            f" **{x.get('cubic_mass_m3'):,.1f} m³**"
        )

      render_pattern_plan(project_master_df)

    st.divider()
    with st.container(border=True):
      render_hole_card(project_master_df, key_prefix="proj")
  # --- TAB 2: AS-BUILT / TRUE FIELD DATA ---
  with tab_field:
    st.subheader("📡 True Field Data")

    with st.container(border=True):
      st.caption("Here we add xml, csv, txt, pdf files captured in the field.")
      field_files = st.file_uploader(
          "Load reports / MWD",
          type=["xml", "csv", "txt", "pdf"],
          accept_multiple_files=True,
          key=f"upl_act_{curr_proj}",
      )

      if field_files:
        for f in field_files:
          f_bytes = f.read()
          ext = f.name.split(".")[-1].lower()

          if ext == "xml":
            res = parse_iredes_xml(f_bytes)
            if res.get("status") == "success":
              curr_data["field_files_parsed"]["xml"] = res
              st.success(f"✅ XML: {f.name} ({res['holes_count']} holes)")
            else:
              st.error(f"❌ XML: {f.name} — {res.get('message')}")

          elif ext == "csv":
            res = parse_quarryx_csv(f_bytes)
            if res.get("status") == "success":
              curr_data["field_files_parsed"]["csv"] = res
              st.success(f"✅ CSV: {f.name} ({res['holes_count']} holes)")
            else:
              st.error(f"❌ CSV: {f.name} — {res.get('message')}")

          elif ext == "txt":
            res = parse_txt_file(f_bytes)
            if res.get("status") == "success":
              curr_data["field_files_parsed"]["txt"] = res
              st.success(f"✅ TXT: {f.name} ({res['holes_count']} profiles)")
            else:
              st.error(f"❌ TXT: {f.name} — {res.get('message')}")

          elif ext == "pdf":
            res = parse_detonator_pdf(f_bytes)
            if res.get("status") == "success":
              curr_data["field_files_parsed"]["pdf"] = res
              st.success(f"✅ PDF: {f.name}")
            else:
              st.error(f"❌ PDF: {f.name} — {res.get('message')}")

    field_master_df = build_master_dataframe(curr_data["field_files_parsed"])

    with st.container(border=True):
      st.markdown("#### 📝 Real Hole Data")
      st.caption("Manual Adjustment (in case data is missing)")
      with st.form("actual_form"):
        act_holes = st.number_input(
            "Real hole number",
            min_value=1,
            value=curr_data.get("actual", {}).get("holes", 36),
        )
        act_exp = st.number_input(
            "Real explosives weight [kg]",
            min_value=0.0,
            value=curr_data.get("actual", {}).get("explosive_kg", 0.0),
        )
        act_notes = st.text_area(
            "Comments",
            value=curr_data.get("actual", {}).get("notes", ""),
        )

        if st.form_submit_button("💾 Save"):
          curr_data["actual"] = {
              "holes": act_holes,
              "explosive_kg": act_exp,
              "notes": act_notes,
          }
          st.success("Saved!")

      st.markdown(
          '<div class="adc-subsection">💣 Charge Parameters (bulk entry)</div>',
          unsafe_allow_html=True,
      )
      st.caption("Fill in once, then save it to a single hole or every hole.")
      with st.form("field_bulk_charge_form"):
        fd_stemming = st.number_input("Stemming length [m]", min_value=0.0, value=0.0)
        fd_inter_stemming = st.number_input(
            "Intermediate stemming length [m]", min_value=0.0, value=0.0
        )
        fd_charge = st.number_input(
            "Explosive charge [kg]", min_value=0.0, value=0.0
        )
        fd_type = st.selectbox("Explosive type", CHARGE_TYPE_OPTIONS)

        field_hole_options = (
            field_master_df["Hole"].tolist()
            if field_master_df is not None and not field_master_df.empty
            else []
        )
        if field_hole_options:
          fd_target_hole = st.selectbox(
              "Apply 'Save for this hole' to:", field_hole_options
          )

        fd_col1, fd_col2 = st.columns(2)
        save_this_hole = fd_col1.form_submit_button("💾 Save for this hole")
        save_all_holes = fd_col2.form_submit_button("📋 Save for all holes")

        new_field_charge = {
            "stemming_length": fd_stemming,
            "intermediate_stemming_length": fd_inter_stemming,
            "explosive_charge": fd_charge,
            "explosive_type": fd_type,
        }
        field_overrides_ns = curr_data["hole_overrides"].setdefault("field", {})

        if save_this_hole:
          if field_hole_options:
            field_overrides_ns[str(fd_target_hole)] = dict(new_field_charge)
            st.success(f"Charge parameters saved for {fd_target_hole}!")
          else:
            st.warning("Upload field files first to select a hole.")
        elif save_all_holes:
          if field_hole_options:
            for h in field_hole_options:
              field_overrides_ns[str(h)] = dict(new_field_charge)
            st.success(f"Charge parameters saved for all {len(field_hole_options)} holes!")
          else:
            st.warning("Upload field files first — no holes to save to yet.")

    st.divider()
    with st.container(border=True):
      render_hole_card(field_master_df, key_prefix="field")

  # --- TAB 3: HOLE DATABASE (FULL TABLE) ---
  with tab_database:
    master_df = build_database_table(project_master_df, field_master_df)

    with st.container(border=True):
      st.subheader("📊 Complex hole database")

      if master_df is not None and not master_df.empty:
        col_search, col_export = st.columns([3, 1])
        with col_search:
          query = st.text_input("🔎 Filter hole database")

        view_df = master_df
        if query:
          view_df = master_df[
              master_df.astype(str)
              .apply(lambda row: row.str.contains(query, case=False).any(), axis=1)
          ]

        st.dataframe(view_df, use_container_width=True, height=450)

        with col_export:
          csv_bytes = master_df.to_csv(index=False).encode("utf-8")
          st.download_button(
              label="📥 Export CSV",
              data=csv_bytes,
              file_name=f"{curr_proj}_Master_Blast_DB.csv",
              mime="text/csv",
          )
      else:
        st.info("ℹ️ Upload project files to generate the hole database.")