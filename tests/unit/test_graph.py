"""
Module: tests/integration/test_graph.py
Description: End-to-End (E2E) integration tests for the LangGraph pipeline.
             Verifies that the StateMachine transitions correctly from raw input
             to the final mathematical model using the MockGateway.
"""

from src.infrastructure.gemini_gateway import MockGateway
from src.types.agent_responses import HEResponse, MADResponse, SAResponse
from src.types.pipeline_state import PipelineState
from src.workflow.graph_builder import build_alpha_graph


def get_happy_path_mock_gateway() -> MockGateway:
    """
    Menyiapkan MockGateway dengan payload valid (Happy Path) untuk
    memastikan Pydantic tidak melempar ValidationError selama E2E test.
    """
    mock_responses = {
        MADResponse: {
            "status": "Pass",
            "counterparty": "Retail Stop Loss",
            "inefficiency_classification": "Information Asymmetry/Latency",
            "limits_to_arbitrage": "High infrastructure cost (Microwave towers).",
            "economic_rationale": "Fast MMs exploit slow retail execution during news spikes.",
            "revision_notes": None,
        },
        HEResponse: {
            "status": "Pass",
            "independent_variables": ["Order_Book_Imbalance", "Spread_Velocity"],
            "dependent_variable": "Log_Return",
            "time_horizon": "100ms",
            "market_regime": "News Event / High Volatility",
            "null_hypothesis": "H0: Order book imbalance has no predictive power on 100ms return.",
            "alternative_hypothesis": "H1: High imbalance predicts directional move within 100ms.",
            "revision_notes": None,
        },
        SAResponse: {
            "status": "Pass",
            "raw_signal_formula_latex": "S_t = \\frac{V_{bid} - V_{ask}}{V_{bid} + V_{ask}}",
            "expected_net_edge_formula_latex": "\\tilde{\\phi}_t = S_t - C_{exec}(Q)",
            "execution_logic": "Execute Market Order if \\tilde{\\phi}_t > 0.1",
            "variables_dict": {
                "S_t": "Order Book Imbalance",
                "V_{bid}": "Bid Volume",
                "V_{ask}": "Ask Volume",
                "C_{exec}(Q)": "Slippage penalty",
            },
            "is_stationary": True,
            "considers_execution_costs": True,
            "has_look_ahead_bias": False,
            "revision_notes": None,
        },
    }
    return MockGateway(default_responses=mock_responses)


def test_graph_end_to_end_success() -> None:
    """
    Uji Integrasi E2E: Mengalirkan data dari observasi mentah (MAD)
    hingga menghasilkan arsitektur sinyal (SA) secara sukses tanpa putar balik.
    """
    # 1. SETUP INJEKSI
    mock_gateway = get_happy_path_mock_gateway()

    # 2. KOMPILASI GRAF
    graph = build_alpha_graph(mock_gateway)

    # 3. PERSIAPAN STATE AWAL (T=0)
    initial_state: PipelineState = {
        "raw_input": "Terjadi inefisiensi latensi pada pembukaan pasar London.",
        "economic_rationale": None,
        "falsifiable_hypothesis": None,
        "signal_architecture": None,
        "error_logs": [],
        "retry_count": 0,
    }

    # 4. EKSEKUSI MESIN OTOMATA
    # Graph akan memanggil node secara berurutan: MAD -> HE -> SA -> __end__
    final_state = graph.invoke(initial_state)

    # 5. ASSERTIONS (VERIFIKASI INTEGRITAS DATA)
    # Pastikan pipeline tidak berhenti di tengah jalan dan data terisi penuh
    assert final_state["economic_rationale"] is not None, (
        "MAD Agent failed to populate rationale."
    )
    assert "High infrastructure cost" in str(final_state["economic_rationale"])

    assert final_state["falsifiable_hypothesis"] is not None, (
        "HE Agent failed to populate hypothesis."
    )
    assert "100ms" in str(final_state["falsifiable_hypothesis"])

    assert final_state["signal_architecture"] is not None, (
        "SA Agent failed to populate architecture."
    )
    assert "S_t" in str(final_state["signal_architecture"])

    # Pastikan tidak ada kegagalan sirkuit (Happy Path murni)
    assert final_state["retry_count"] == 0, (
        f"Expected 0 retries, got {final_state['retry_count']}. Graph looped due to errors."
    )
    assert len(final_state["error_logs"]) == 0, (
        f"Expected clean logs, got errors: {final_state['error_logs']}"
    )
