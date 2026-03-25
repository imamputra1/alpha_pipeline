import json

from src.agents.he_agent import evaluate_he  # <-- PASTIKAN INI ADA
from src.agents.mad_agent import evaluate_mad
from src.agents.sa_agent import evaluate_sa
from src.infrastructure.gemini_gateway import MockGateway
from src.types.agent_responses import (
    HEResponse,
    MADResponse,
    SAResponse,
)  # <-- PASTIKAN HEResponse ADA DI SINI
from src.types.domain_errors import (
    DomainError,
    LookAheadBiasError,
    MissingDataError,
    NonFalsifiableError,
    NonStationaryError,
)
from src.types.pipeline_state import PipelineState
from src.types.result import is_err, is_ok

# =============================================================================
# FIXTURES & HELPERS
# =============================================================================


def get_base_state() -> PipelineState:
    """Helper untuk menghasilkan state awal yang kosong/bersih."""
    return {
        "raw_input": "Market shows inefficiency during London open.",
        "economic_rationale": None,
        "falsifiable_hypothesis": None,
        "signal_architecture": None,
        "error_logs": [],
        "retry_count": 0,
    }


def get_sa_ready_state() -> PipelineState:
    """Helper untuk menghasilkan state yang siap untuk diuji oleh SA Agent."""
    state = get_base_state()
    # Updated JSON payloads to match the new MAD and HE schemas
    state["economic_rationale"] = json.dumps(
        {
            "counterparty": "Retail",
            "classification": "Behavioral/Psychological",
            "limits_to_arbitrage": "Capacity constraint max $100k.",
            "rationale": "Stop loss hunting",
        }
    )
    state["falsifiable_hypothesis"] = json.dumps(
        {
            "independent_vars": ["Spread_ZScore"],
            "dependent_var": "Log_Return",
            "time_horizon": "100ms",
            "market_regime": "Top 10% Volatility",
            "H0": "No edge",
            "H1": "Edge exists",
        }
    )
    return state


# =============================================================================
# SA AGENT TESTS (Fase 3: Sinyal Kuantitatif)
# =============================================================================


def test_sa_agent_success() -> None:
    """Uji 'Happy Path': LLM menghasilkan model yang valid (Stationary, No Look-Ahead, with Exec Costs)."""
    state = get_sa_ready_state()

    mock_responses = {
        SAResponse: {
            "status": "Pass",
            "raw_signal_formula_latex": "S_t = \\log(P_t) - \\log(P_{t-1})",
            "expected_net_edge_formula_latex": "\\tilde{\\phi}_t = S_t - C_{exec}",
            "execution_logic": "Buy when \\tilde{\\phi}_t > 0.5",
            "variables_dict": {
                "S_t": "Raw Signal",
                "\\tilde{\\phi}_t": "Net Edge",
                "C_{exec}": "Cost",
            },
            "is_stationary": True,
            "considers_execution_costs": True,  # LOLOS FILTER
            "has_look_ahead_bias": False,
            "revision_notes": None,
        }
    }
    mock_llm = MockGateway(default_responses=mock_responses)
    result = evaluate_sa(state, mock_llm)

    assert is_ok(result), "Expected Ok result for valid SA generation."
    new_state = result.unwrap()
    assert new_state["signal_architecture"] is not None
    assert "raw_signal_formula" in str(new_state["signal_architecture"])


def test_sa_agent_illusion_of_execution() -> None:
    """Uji 'Sad Path': LLM mengabaikan biaya eksekusi (Illusion of Execution)."""
    state = get_sa_ready_state()

    mock_responses = {
        SAResponse: {
            "status": "Pass",
            "raw_signal_formula_latex": "S_t = \\log(P_t) - \\log(P_{t-1})",
            "expected_net_edge_formula_latex": "\\tilde{\\phi}_t = S_t",  # Mengabaikan biaya
            "execution_logic": "Buy",
            "variables_dict": {"S_t": "Signal"},
            "is_stationary": True,
            "considers_execution_costs": False,  # RACUN DISEBARKAN DI SINI
            "has_look_ahead_bias": False,
            "revision_notes": "Execution costs are negligible.",
        }
    }
    mock_llm = MockGateway(default_responses=mock_responses)
    result = evaluate_sa(state, mock_llm)

    assert is_err(result)
    assert isinstance(result.unwrap_err(), DomainError)
    assert "ILLUSION OF EXECUTION" in str(result.unwrap_err())


def test_sa_agent_look_ahead_bias() -> None:
    state = get_sa_ready_state()
    mock_responses = {
        SAResponse: {
            "status": "Pass",
            "raw_signal_formula_latex": "S_t = P_{t+1} - P_t",
            "expected_net_edge_formula_latex": "\\tilde{\\phi}_t = S_t - C_{exec}",
            "execution_logic": "Buy",
            "variables_dict": {"P_{t+1}": "Future Price"},
            "is_stationary": True,
            "considers_execution_costs": True,
            "has_look_ahead_bias": True,  # RACUN
            "revision_notes": "Using t+1.",
        }
    }
    mock_llm = MockGateway(default_responses=mock_responses)
    result = evaluate_sa(state, mock_llm)

    assert is_err(result)
    assert isinstance(result.unwrap_err(), LookAheadBiasError)


def test_sa_agent_non_stationary() -> None:
    state = get_sa_ready_state()
    mock_responses = {
        SAResponse: {
            "status": "Pass",
            "raw_signal_formula_latex": "S_t = P_t",
            "expected_net_edge_formula_latex": "\\tilde{\\phi}_t = S_t - C_{exec}",
            "execution_logic": "Buy",
            "variables_dict": {"P_t": "Absolute Price"},
            "is_stationary": False,  # RACUN
            "considers_execution_costs": True,
            "has_look_ahead_bias": False,
            "revision_notes": "Using raw prices.",
        }
    }
    mock_llm = MockGateway(default_responses=mock_responses)
    result = evaluate_sa(state, mock_llm)

    assert is_err(result)
    assert isinstance(result.unwrap_err(), NonStationaryError)


def test_sa_agent_missing_hypothesis() -> None:
    state = get_base_state()  # falsifiable_hypothesis is None here
    mock_llm = MockGateway()
    result = evaluate_sa(state, mock_llm)

    assert is_err(result)
    assert isinstance(result.unwrap_err(), MissingDataError)


# =============================================================================
# MAD AGENT TESTS (Fase 1: Market Asymmetry)
# =============================================================================


def test_mad_agent_success() -> None:
    state = get_base_state()
    mock_responses = {
        MADResponse: {
            "status": "Pass",
            "counterparty": "Retail Stop Loss",
            "inefficiency_classification": "Information Asymmetry/Latency",
            "limits_to_arbitrage": "Latency barrier of 5ms.",
            "economic_rationale": "Liquidity providers widen spread during news.",
            "revision_notes": None,
        }
    }
    mock_llm = MockGateway(default_responses=mock_responses)
    result = evaluate_mad(state, mock_llm)

    assert is_ok(result)
    new_state = result.unwrap()
    assert new_state["economic_rationale"] is not None
    assert "limits_to_arbitrage" in new_state["economic_rationale"]


def test_mad_agent_fail_status() -> None:
    state = get_base_state()
    mock_responses = {
        MADResponse: {
            "status": "Fail",
            "counterparty": "Unknown",
            "inefficiency_classification": "Unknown",
            "limits_to_arbitrage": "None",
            "economic_rationale": "Idea relies on technical indicator.",
            "revision_notes": "Not falsifiable without counterparty identification.",
        }
    }
    mock_llm = MockGateway(default_responses=mock_responses)
    result = evaluate_mad(state, mock_llm)

    assert is_err(result)
    assert isinstance(result.unwrap_err(), NonFalsifiableError)


# =============================================================================
# HE AGENT TESTS (Fase 2: Hypothesis Engineer)
# =============================================================================


def test_he_agent_success() -> None:
    """
    Uji 'Happy Path': Agen HE berhasil mengubah economic_rationale (dari MAD)
    menjadi hipotesis berstruktur (falsifiable).
    """
    state = get_base_state()
    # Menyimulasikan bahwa MAD Agent telah berhasil berjalan sebelumnya
    state["economic_rationale"] = json.dumps(
        {
            "counterparty": "Retail",
            "classification": "Behavioral/Psychological",
            "limits_to_arbitrage": "Capacity constraint",
            "rationale": "Stop loss hunting by liquidity providers.",
        }
    )

    mock_responses = {
        HEResponse: {
            "status": "Pass",
            "independent_variables": ["Spread_ZScore", "Order_Imbalance"],
            "dependent_variable": "Log_Return",
            "time_horizon": "100ms",
            "market_regime": "Top 10% Volatility",
            "null_hypothesis": "Spread Z-Score has no correlation with next 100ms return (Edge=0).",
            "alternative_hypothesis": "High Spread Z-Score predicts mean-reverting return within 100ms.",
            "revision_notes": None,
        }
    }
    mock_llm = MockGateway(default_responses=mock_responses)

    result = evaluate_he(state, mock_llm)

    assert is_ok(result), "Expected Ok result for valid HE generation."
    new_state = result.unwrap()
    assert new_state["falsifiable_hypothesis"] is not None
    assert "H0" in str(new_state["falsifiable_hypothesis"])
    assert "H1" in str(new_state["falsifiable_hypothesis"])


def test_he_agent_missing_rationale() -> None:
    """
    Uji 'Edge Case': Guard Clause awal. Jika state.get("economic_rationale") kosong,
    agen HE harus langsung mengembalikan Err(MissingDataError).
    """
    state = get_base_state()  # economic_rationale is explicitly None here
    mock_llm = MockGateway()

    result = evaluate_he(state, mock_llm)

    assert is_err(result), (
        "Expected Err because prerequisite economic_rationale is missing."
    )
    assert isinstance(result.unwrap_err(), MissingDataError), (
        "Error type must be MissingDataError."
    )


def test_he_agent_fail_status() -> None:
    """
    Uji 'Sad Path': Memastikan jika output LLM untuk HE merespons dengan status = "Fail"
    (karena rasionalnya dianggap tidak falsifiable), agen mengembalikan Err(NonFalsifiableError).
    """
    state = get_base_state()
    state["economic_rationale"] = json.dumps(
        {
            "counterparty": "Unknown",
            "classification": "Unknown",
            "limits_to_arbitrage": "None",
            "rationale": "Harga sepertinya akan naik karena feeling trader.",
        }
    )

    mock_responses = {
        HEResponse: {
            "status": "Fail",  # LLM Menolak
            "independent_variables": ["Feeling"],
            "dependent_variable": "Price",
            "time_horizon": "Soon",
            "market_regime": "Always",
            "null_hypothesis": "None",
            "alternative_hypothesis": "None",
            "revision_notes": "Ide tidak dapat diukur secara kuantitatif menggunakan Order Book atau Ticks.",
        }
    }
    mock_llm = MockGateway(default_responses=mock_responses)

    result = evaluate_he(state, mock_llm)

    assert is_err(result), (
        "Expected Err because HE rejected the hypothesis as non-falsifiable."
    )
    assert isinstance(result.unwrap_err(), NonFalsifiableError), (
        "Error type must be NonFalsifiableError."
    )
