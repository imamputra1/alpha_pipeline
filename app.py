import json
import logging
from typing import Any, Dict

import pandas as pd
import streamlit as st

# Mengimpor Functional Core
from src import (
    GeminiGateway,
    build_alpha_graph,
    parse_document,
)
from src.types.result import is_ok

# Konfigurasi Logging UI
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# =============================================================================
# 0. HELPER FUNCTIONS (DEFENSIVE PROGRAMMING)
# =============================================================================


def safe_parse_dict(data: Any) -> Dict[str, Any]:
    """Helper untuk memastikan data selalu berupa dictionary dengan aman."""
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            logging.error("Gagal mem-parsing string JSON.")
            return {}
    return {}


def render_mad_tab(data: Any) -> None:
    """Komponen UI khusus untuk merender hasil Market Asymmetry."""
    mad_data = safe_parse_dict(data)
    if not mad_data:
        st.info("Data Market Asymmetry tidak tersedia atau format tidak valid.")
        return

    col1, col2 = st.columns(2)
    col1.metric("Target Mangsa (Counterparty)", mad_data.get("counterparty", "N/A"))
    col2.metric("Klasifikasi Inefisiensi", mad_data.get("classification", "N/A"))

    st.subheader("Limits to Arbitrage")
    st.info(mad_data.get("limits_to_arbitrage", "Tidak ada catatan batas arbitrase."))

    st.subheader("Rasionalisasi Mikrostruktur")
    st.markdown(mad_data.get("rationale", "Tidak ada rasionalisasi."))


def render_he_tab(data: Any) -> None:
    """Komponen UI khusus untuk merender hasil Hypothesis Engineer."""
    he_data = safe_parse_dict(data)
    if not he_data:
        st.info("Data Hipotesis tidak tersedia.")
        return

    col_a, col_b = st.columns(2)
    col_a.metric("Variabel Target (Y)", he_data.get("dependent_var", "N/A"))
    col_b.metric("Horizon Absolut", he_data.get("time_horizon", "N/A"))

    st.markdown(f"**Market Regime:** `{he_data.get('market_regime', 'Agnostic')}`")
    ind_vars = he_data.get("independent_vars", [])
    if isinstance(ind_vars, list):
        st.markdown(f"**Variabel Sinyal (X):** `{', '.join(ind_vars)}`")

    st.subheader("Hipotesis Falsifiable")
    st.error(f"**H0 (Null):** {he_data.get('H0', 'N/A')}", icon="🛑")
    st.success(f"**H1 (Alternative):** {he_data.get('H1', 'N/A')}", icon="✅")


def render_sa_tab(data: Any) -> None:
    """Komponen UI khusus untuk merender Arsitektur Sinyal (LaTeX & Tabel)."""
    sa_data = safe_parse_dict(data)
    if not sa_data:
        st.info("Arsitektur Sinyal tidak tersedia.")
        return

    st.subheader("Formula Sinyal Mentah")
    raw_signal = sa_data.get("raw_signal_formula", "")
    if raw_signal:
        st.latex(raw_signal)
    else:
        st.warning("Formula tidak ditemukan.")

    st.subheader("Expected Net Edge")
    net_edge = sa_data.get("expected_net_edge_formula", "")
    if net_edge:
        st.latex(net_edge)

    st.subheader("Logika Eksekusi")
    exec_logic = sa_data.get("execution_logic", "")
    if exec_logic:
        st.code(exec_logic, language="python")

    st.subheader("Kamus Variabel")
    var_dict = sa_data.get("variables", {})
    if isinstance(var_dict, dict) and var_dict:
        df_vars = pd.DataFrame(
            list(var_dict.items()), columns=["Simbol LaTeX", "Definisi"]
        )
        st.dataframe(df_vars, use_container_width=True, hide_index=True)
    else:
        st.write(var_dict)


# =============================================================================
# 1. PAGE CONFIGURATION & SESSION STATE MANAGEMENT
# =============================================================================

st.set_page_config(
    page_title="Alpha Pipeline | Quant Lab",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inisialisasi State secara massal
DEFAULT_STATES = {"api_key": "", "raw_input_text": "", "pipeline_result": None}
for key, default_value in DEFAULT_STATES.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# =============================================================================
# 2. SIDEBAR CONFIGURATION (PANEL KENDALI)
# =============================================================================

with st.sidebar:
    st.header("⚙️ Konfigurasi Mesin")

    api_key_input = st.text_input(
        "Gemini API Key", type="password", value=st.session_state.api_key
    )
    if api_key_input:
        st.session_state.api_key = api_key_input

    model_name = st.selectbox(
        "Model Kognitif",
        options=["gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-pro"],
        index=0,
        help="Gunakan varian Pro untuk presisi matematis tertinggi.",
    )

    st.divider()
    st.subheader("📄 Ingesti Data Observasi")

    uploaded_file = st.file_uploader("Unggah Jurnal/EDA", type=["pdf", "csv"])
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_name = uploaded_file.name

        parse_result = parse_document(file_name, file_bytes)
        if is_ok(parse_result):
            st.session_state.raw_input_text = parse_result.unwrap()
            # Gunakan toast untuk notifikasi yang tidak mengganggu layout
            st.toast(f"Berhasil mengekstrak {file_name}", icon="✅")
        else:
            err = parse_result.unwrap_err()
            st.error(f"Gagal memproses file: {str(err)}")

    st.markdown("**— ATAU —**")
    manual_input = st.text_area("Observasi Manual (Teks)", height=150)
    if manual_input:
        st.session_state.raw_input_text = manual_input

# =============================================================================
# 3. MAIN PANEL UX (MESIN EKSEKUSI)
# =============================================================================

st.title("Alpha Pipeline Orchestrator")
st.markdown(
    "*Otomatisasi Reverse-Engineering Inefisiensi Pasar Berbasis Mikrostruktur.*"
)

is_ready = bool(st.session_state.api_key and st.session_state.raw_input_text)

if st.button(
    "🚀 Kompilasi & Jalankan Pipeline",
    type="primary",
    disabled=not is_ready,
    use_container_width=True,
):
    st.session_state.pipeline_result = None

    # Setup Gateway & Initial State
    gateway = GeminiGateway(api_key=st.session_state.api_key, model_name=model_name)
    graph = build_alpha_graph(gateway)

    current_state = {
        "raw_input": st.session_state.raw_input_text,
        "economic_rationale": None,
        "falsifiable_hypothesis": None,
        "signal_architecture": None,
        "error_logs": [],
        "retry_count": 0,
    }

    with st.status("⚙️ Menjalankan Automata LangGraph...", expanded=True) as status_box:
        try:
            # Akumulasi state secara progesif
            for output in graph.stream(current_state):
                for node_name, state_update in output.items():
                    # Update current_state dengan data terbaru dari node
                    current_state.update(state_update)

                    if node_name == "mad_agent":
                        st.write("✅ **MAD:** Asimetri pasar berhasil dipetakan.")
                    elif node_name == "he_agent":
                        st.write("✅ **HE:** Hipotesis falsifiable berhasil dikunci.")
                    elif node_name == "sa_agent":
                        st.write("✅ **SA:** Arsitektur sinyal matematis dirakit.")

            status_box.update(
                label="🎯 Pipeline Selesai!", state="complete", expanded=False
            )
            # Simpan state final yang sudah terakumulasi penuh
            st.session_state.pipeline_result = current_state

        except Exception as e:
            status_box.update(label="❌ Pipeline Crash", state="error", expanded=True)
            st.error(f"Terjadi kegagalan infrastruktur kritis: {str(e)}")
            logging.error(f"Graph execution failed: {e}")

# =============================================================================
# 4. DASBOR HASIL RISET (OUTPUT DISPLAY)
# =============================================================================

if st.session_state.pipeline_result:
    res = st.session_state.pipeline_result
    st.divider()

    # A. PENANGANAN KEGAGALAN (Circuit Breaker)
    if not res.get("signal_architecture") and res.get("error_logs"):
        st.error("🚨 **PIPELINE DIHENTIKAN: Batas Revisi Logika Tercapai**")
        with st.expander("Lihat Catatan Supervisor (Guard Clauses)", expanded=True):
            for log in res["error_logs"]:
                st.warning(log)
        st.stop()

    # B. RENDERING SUCCESS DASHBOARD
    st.header("📊 Laporan Arsitektur Kuantitatif")

    tab_mad, tab_he, tab_sa = st.tabs(
        [
            "🕵️ Fase 1: Market Asymmetry",
            "🧪 Fase 2: Hypothesis",
            "📐 Fase 3: Signal Architecture",
        ]
    )

    with tab_mad:
        render_mad_tab(res.get("economic_rationale"))

    with tab_he:
        render_he_tab(res.get("falsifiable_hypothesis"))

    with tab_sa:
        render_sa_tab(res.get("signal_architecture"))
