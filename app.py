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
    page_title="AutoDataCollector", page_icon="🛰️", layout="wide"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
      font-family: 'Inter', sans-serif;
    }

    .adc-hero {
      background: linear-gradient(135deg, #6d28d9 0%, #7c3aed 45%, #06b6d4 100%);
      padding: 1.75rem 2rem;
      border-radius: 16px;
      margin-bottom: 1.5rem;
      box-shadow: 0 10px 30px rgba(124, 58, 237, 0.35);
    }
    .adc-hero h1 {
      color: white;
      margin: 0;
      font-weight: 800;
      font-size: 2.1rem;
      letter-spacing: -0.02em;
    }
    .adc-hero p {
      color: rgba(255, 255, 255, 0.85);
      margin: 0.35rem 0 0 0;
      font-size: 0.95rem;
    }

    div[data-testid="stMetric"] {
      background: rgba(139, 92, 246, 0.08);
      border: 1px solid rgba(139, 92, 246, 0.25);
      border-radius: 12px;
      padding: 0.75rem 0.9rem;
    }

    section[data-testid="stSidebar"] .stButton button,
    div.stForm button {
      background: linear-gradient(135deg, #7c3aed, #06b6d4);
      color: white;
      border: none;
      border-radius: 8px;
      font-weight: 600;
    }

    button[data-testid="stTab"] {
      font-size: 1rem;
      font-weight: 700;
      padding: 0.75rem 1.25rem;
    }
    button[data-testid="stTab"][aria-selected="true"] {
      color: #c4b5fd;
      border-bottom-color: #8b5cf6 !important;
    }
    div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {
      background-color: #8b5cf6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "projects" not in st.session_state:
  st.session_state.projects = {}

if "current_project" not in st.session_state:
  st.session_state.current_project = None

# --- SIDEBAR: PROJECT MANAGEMENT ---
st.sidebar.title("🛰️ AutoDataCollector")
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
          "field_defaults": {},
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
      <h1>🛰️ AutoDataCollector</h1>
      <p>Aggregate drill plans, MWD reports and detonator logs into one blast database.</p>
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
  curr_data.setdefault("field_defaults", {})
  curr_data.setdefault("hole_overrides", {})

  CHARGE_TYPE_OPTIONS = ["Bulk emulsion", "Bulk ANFO", "Cartridge", "Other"]

  st.markdown(f"### 📍 Project: `{curr_proj}`")
  st.divider()

  tab_project, tab_field, tab_database = st.tabs(
      ["📁 Project Files", "📡 True Field Data", "📊 Hole Database"]
  )

  # --- TAB 1: PROJECT FILE UPLOAD ---
  with tab_project, st.container(border=True):
    st.subheader("📁 Project Files")
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

  # --- TAB 2: AS-BUILT / TRUE FIELD DATA ---
  with tab_field, st.container(border=True):
    st.subheader("📡 True Field Data")
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

    st.markdown("##### 💣 Default Charge Parameters (all holes)")
    st.caption("Applied to every hole unless overridden in its Hole card.")
    with st.form("field_defaults_form"):
      fd_stemming = st.number_input(
          "Stemming length [m]",
          min_value=0.0,
          value=curr_data["field_defaults"].get("stemming_length", 0.0),
      )
      fd_inter_stemming = st.number_input(
          "Intermediate stemming length [m]",
          min_value=0.0,
          value=curr_data["field_defaults"].get(
              "intermediate_stemming_length", 0.0
          ),
      )
      fd_charge = st.number_input(
          "Explosive charge [kg]",
          min_value=0.0,
          value=curr_data["field_defaults"].get("explosive_charge", 0.0),
      )
      fd_type = st.selectbox(
          "Explosive type",
          CHARGE_TYPE_OPTIONS,
          index=CHARGE_TYPE_OPTIONS.index(
              curr_data["field_defaults"].get("explosive_type", CHARGE_TYPE_OPTIONS[0])
          ),
      )

      if st.form_submit_button("💾 Save defaults"):
        curr_data["field_defaults"] = {
            "stemming_length": fd_stemming,
            "intermediate_stemming_length": fd_inter_stemming,
            "explosive_charge": fd_charge,
            "explosive_type": fd_type,
        }
        st.success("Default charge parameters saved!")

  # --- TAB 3: HOLE DATABASE (HOLE CARD + FULL TABLE) ---
  with tab_database:
    master_df = build_master_dataframe(curr_data["files_parsed"])

    if master_df is not None and not master_df.empty:
      st.subheader(
          "🔍 Hole card"
      )

      hole_list = master_df["Hole"].tolist()
      sel_hole = st.selectbox("Select hole to analyze:", hole_list)

      hole_row = master_df[master_df["Hole"] == sel_hole].iloc[0]

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
        m3.metric("Angle / Azimuth", f"{val_ang}° / {val_az}°")
        m4.metric("Delay / Explosive mass", f"{val_deck} ms / {val_exp} kg")

        st.markdown("#### 📊 Burden Analytics")
        b1, b2, b3 = st.columns(3)
        b1.metric("Crest burden", f"{hole_row.get('Crest_Burden_m', 'None')} m")
        b2.metric("Toe burden", f"{hole_row.get('Toe_Burden_m', 'None')} m")
        b3.metric("Mean burden", f"{hole_row.get('Mean_Burden_m', 'None')} m")
        b4, b5 = st.columns(2)
        b4.metric(
            "Min. burden",
            f"{hole_row.get('Min_Burden_m', 'None')} m",
            help=(
                "Depth:"
                f" {hole_row.get('Min_Burden_Depth_m', '-')} m"
            ),
        )
        b5.metric(
            "Max. burden",
            f"{hole_row.get('Max_Burden_m', 'None')} m",
            help=(
                "Depth:"
                f" {hole_row.get('Max_Burden_Depth_m', '-')} m"
            ),
        )

        raw_json = hole_row.get("Burden_Profile_JSON")
        if pd.notna(raw_json) and raw_json:
          with st.expander("📦 Full JSON record"):
            st.json(json.loads(raw_json))

        st.markdown("#### 💣 Charge Parameters")
        st.caption("Overrides the True Field Data defaults for this hole only.")
        hole_key = str(sel_hole)
        existing_override = curr_data["hole_overrides"].get(hole_key, {})
        field_defaults = curr_data["field_defaults"]
        with st.form(f"hole_charge_form_{hole_key}"):
          hc_stemming = st.number_input(
              "Stemming length [m]",
              min_value=0.0,
              value=existing_override.get(
                  "stemming_length", field_defaults.get("stemming_length", 0.0)
              ),
              key=f"hc_stem_{hole_key}",
          )
          hc_inter_stemming = st.number_input(
              "Intermediate stemming length [m]",
              min_value=0.0,
              value=existing_override.get(
                  "intermediate_stemming_length",
                  field_defaults.get("intermediate_stemming_length", 0.0),
              ),
              key=f"hc_interstem_{hole_key}",
          )
          hc_charge = st.number_input(
              "Explosive charge [kg]",
              min_value=0.0,
              value=existing_override.get(
                  "explosive_charge", field_defaults.get("explosive_charge", 0.0)
              ),
              key=f"hc_charge_{hole_key}",
          )
          hc_type = st.selectbox(
              "Explosive type",
              CHARGE_TYPE_OPTIONS,
              index=CHARGE_TYPE_OPTIONS.index(
                  existing_override.get(
                      "explosive_type",
                      field_defaults.get("explosive_type", CHARGE_TYPE_OPTIONS[0]),
                  )
              ),
              key=f"hc_type_{hole_key}",
          )

          if st.form_submit_button("💾 Save for this hole"):
            curr_data["hole_overrides"][hole_key] = {
                "stemming_length": hc_stemming,
                "intermediate_stemming_length": hc_inter_stemming,
                "explosive_charge": hc_charge,
                "explosive_type": hc_type,
            }
            st.success(f"Charge parameters saved for {hole_key}!")

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
                  color="#0284c7",
                  linestyle=":",
                  linewidth=1.3,
              )
              mid_x = (hx + fx) / 2
              mid_z = (hz + fz) / 2
              ax.text(
                  mid_x,
                  mid_z + 0.12,
                  f"{b:.2f} m",
                  color="#0369a1",
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
          st.pyplot(fig, width=700)
        else:
          st.info("No TXT burden profile available for this hole.")

    st.divider()
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
              label="📥 Export Full Database with JSON (.CSV)",
              data=csv_bytes,
              file_name=f"{curr_proj}_Master_Blast_DB.csv",
              mime="text/csv",
          )
      else:
        st.info("ℹ️ Upload project files to generate the hole database.")