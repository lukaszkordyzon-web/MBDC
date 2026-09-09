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
    page_title="Multiple Blast Data", page_icon="⛏️", layout="wide"
)

if "projects" not in st.session_state:
  st.session_state.projects = {}

if "current_project" not in st.session_state:
  st.session_state.current_project = None

# --- SIDEBAR: ZARZĄDZANIE PROJEKTAMI ---
st.sidebar.title("🗂️ Multiple Blast Projects")

with st.sidebar.form("new_proj_form"):
  new_name = st.text_input("Project name")
  if st.form_submit_button("Create project") and new_name:
    if new_name not in st.session_state.projects:
      st.session_state.projects[new_name] = {
          "design": {},
          "actual": {},
          "files_parsed": {},
      }
      st.session_state.current_project = new_name
      st.sidebar.success(f"Utworzono: **{new_name}**")
    else:
      st.sidebar.warning("Projekt już istnieje.")

if st.session_state.projects:
  projs = list(st.session_state.projects.keys())
  st.session_state.current_project = st.sidebar.selectbox(
      "Wybierz aktywny projekt",
      projs,
      index=projs.index(st.session_state.current_project)
      if st.session_state.current_project in projs
      else 0,
  )

# --- PANEL GŁÓWNY ---
st.title("⛏️ Multiple Blast Data")

if not st.session_state.current_project:
  st.info("👈 Wybierz lub załóż projekt w panelu bocznym.")
else:
  curr_proj = st.session_state.current_project
  curr_data = st.session_state.projects[curr_proj]

  st.markdown(f"### 📍 Projekt: `{curr_proj}`")
  st.divider()

  col1, col2 = st.columns(2)

  # --- SEKCJA 1: WGRYWANIE PLIKÓW PROJEKTOWYCH ---
  with col1:
    st.subheader("1️⃣ Project files (XML, CSV, TXT, PDF)")
    uploaded_files = st.file_uploader(
        "Wgraj paczkę projektową",
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
            st.success(f"✅ XML: {f.name} ({res['holes_count']} otworów)")
          else:
            st.error(f"❌ XML: {f.name} — {res.get('message')}")

        elif ext == "csv":
          res = parse_quarryx_csv(f_bytes)
          if res.get("status") == "success":
            curr_data["files_parsed"]["csv"] = res
            st.success(f"✅ CSV: {f.name} ({res['holes_count']} otworów)")
          else:
            st.error(f"❌ CSV: {f.name} — {res.get('message')}")

        elif ext == "txt":
          res = parse_txt_file(f_bytes)
          if res.get("status") == "success":
            curr_data["files_parsed"]["txt"] = res
            st.success(f"✅ TXT: {f.name} ({res['holes_count']} profili)")
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
      st.markdown("#### ℹ️ Metadane projektu (z pliku XML)")
      st.info(
          f"🛠️ **Program:** {x.get('generated_by')} | 📅 **Data:**"
          f" {x.get('creation_date')}\n\n👤 **Autor:** {x.get('author')} | 🏢"
          f" **Zleceniodawca:** {x.get('project')}\n\n📍 **Zadanie:**"
          f" {x.get('work_order')}\n\n📐 **Siatka:** Zabiór rz. I ="
          f" **{x.get('first_row_burden')} m** | Rozstaw ="
          f" **{x.get('spacing')} m** | Objętość calizny ="
          f" **{x.get('cubic_mass_m3'):,.1f} m³**"
      )

  # --- SEKCJA 2: DANE POWYKONAWCZE ---
  with col2:
    st.subheader("2️⃣ Dane Rzeczywiste (MWD / Powykonawcze)")
    st.file_uploader(
        "Load reports / MWD",
        type=["txt", "csv", "pdf"],
        accept_multiple_files=True,
        key=f"upl_act_{curr_proj}",
    )

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
        st.success("Zapisano!")

  # --- SEKCJA 3: KARTA SZCZEGÓŁOWA OTWORU + PRZEKRÓJ 2D (90 STOPNI DO OSI) ---
  st.divider()
  master_df = build_master_dataframe(curr_data["files_parsed"])

  if master_df is not None and not master_df.empty:
    st.subheader(
        "🔍 Hole card"
    )

    hole_list = master_df["Hole"].tolist()
    sel_hole = st.selectbox("Wybierz otwór do analizy:", hole_list)

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

    # Odczyt i bezpieczny fallback średnicy otworu
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
        else "Brak"
    )

    card_left, card_right = st.columns([1, 1.2])

    with card_left:
      st.markdown("#### 📐 Parametry Otworu")
      st.write(
          f"- **Współrzędne wlotu (X, Y, Z):** `{val_x}`, `{val_y}`, `{val_z}`"
      )
      st.write(
          "- **Współrzędne dna (BottomX, Y, Z):**"
          f" `{val_bx}`, `{val_by}`, `{val_bz}`"
      )
      st.write(
          f"- **Długość:** `{val_len} m` | **Średnica:** `{val_dia} mm` |"
          f" **Kąt / Azymut:** `{val_ang}° / {val_az}°`"
      )
      st.write(
          f"- **Opóźnienie:** `{val_deck} ms` | **Masa MW:** `{val_exp} kg`"
      )

      st.markdown("#### 📊 Analityka Zabioru")
      st.write(
          "- **Zabiór pod koroną (Crest):**"
          f" `{hole_row.get('Crest_Burden_m', 'Brak')} m`"
      )
      st.write(
          "- **Zabiór na stopie (Toe):**"
          f" `{hole_row.get('Toe_Burden_m', 'Brak')} m`"
      )
      st.write(
          "- **Min. Zabiór:**"
          f" `{hole_row.get('Min_Burden_m', 'Brak')} m` (głębokość:"
          f" `{hole_row.get('Min_Burden_Depth_m', '-')} m`)"
      )
      st.write(
          "- **Max. Zabiór:**"
          f" `{hole_row.get('Max_Burden_m', 'Brak')} m` (głębokość:"
          f" `{hole_row.get('Max_Burden_Depth_m', '-')} m`)"
      )
      st.write(
          "- **Średni zabiór otworu:**"
          f" `{hole_row.get('Mean_Burden_m', 'Brak')} m`"
      )

      raw_json = hole_row.get("Burden_Profile_JSON")
      if pd.notna(raw_json) and raw_json:
        with st.expander("📦 Pełny rekord JSON"):
          st.json(json.loads(raw_json))

    with card_right:
      st.markdown("#### 📉 Przekrój 2D z Wymiarowaniem Prostopadłym")
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
        ax.plot(
            hole_x,
            hole_z,
            color="red",
            linestyle="--",
            linewidth=2.5,
            label=f"Oś otworu {sel_hole} ({ang_deg}°)",
        )
        ax.plot(
            face_x,
            face_z,
            color="black",
            linestyle="-",
            linewidth=2.0,
            label="Lico ściany (Profil)",
        )
        ax.fill_betweenx(
            hole_z,
            hole_x,
            face_x,
            color="#cbd5e1",
            alpha=0.35,
            label="Zabiór (Calizna)",
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

        ax.set_xlabel("Odległość pozioma [m]", fontsize=9)
        ax.set_ylabel("Rzędna pionowa (w dół) [m]", fontsize=9)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="lower right", fontsize=8)
        st.pyplot(fig)
      else:
        st.info("Brak profilu zabioru TXT dla tego otworu.")

  # --- SEKCJA 4: GŁÓWNA TABELA BAZY DANYCH ---
  st.divider()
  st.subheader(
      "📊 Complex hole database"
  )

  if master_df is not None and not master_df.empty:
    col_search, col_export = st.columns([3, 1])
    with col_search:
      query = st.text_input("🔎 Filtruj bazę otworów")

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
          label="📥 Eksportuj Pełną Bazę z JSON (.CSV)",
          data=csv_bytes,
          file_name=f"{curr_proj}_Master_Blast_DB.csv",
          mime="text/csv",
      )
  else:
    st.info("ℹ️ Wgraj pliki projektu, aby wygenerować bazę danych otworów.")