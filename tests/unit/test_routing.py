"""
Module: tests/unit/test_routing.py
Description: Unit tests for the Supervisor Routing Logic (Pattern Matching & Circuit Breakers).
             Ensures StateGraph edges flow correctly based on Result monads and DomainErrors.
"""

from src.types.domain_errors import (
    LookAheadBiasError,
    MissingDataError,
    NonFalsifiableError,
)
from src.types.pipeline_state import PipelineState
from src.types.result import Err, Ok
from src.workflow.routing_logic import (
    NODE_END,
    NODE_HE,
    NODE_SA,
    route_he,
    route_mad,
    route_sa,
)


def get_dummy_state(retry_count: int = 0) -> PipelineState:
    """Helper untuk menghasilkan state minimal untuk pengujian router."""
    return {
        "raw_input": "Dummy input",
        "economic_rationale": None,
        "falsifiable_hypothesis": None,
        "signal_architecture": None,
        "error_logs": [],
        "retry_count": retry_count,
    }


# =============================================================================
# SKENARIO 1: UJI RUTE "HAPPY PATH" (LANJUT KE NODE BERIKUTNYA)
# =============================================================================

def test_route_mad_ok() -> None:
    """Jika MAD mengembalikan Ok(), rute harus mengarah ke HE."""
    state = get_dummy_state()
    result = route_mad(Ok(state))
    assert result == NODE_HE


def test_route_sa_ok() -> None:
    """Jika SA (node terakhir) mengembalikan Ok(), rute harus mengarah ke END."""
    state = get_dummy_state()
    result = route_sa(Ok(state))
    assert result == NODE_END


# =============================================================================
# SKENARIO 2: UJI RUTE "SAD PATH" (PUTAR BALIK UNTUK REVISI)
# =============================================================================

def test_route_sa_look_ahead_bias() -> None:
    """Jika SA mendeteksi LookAheadBias (dan retry < max), putar balik ke SA."""
    state = get_dummy_state(retry_count=0)
    error = LookAheadBiasError("Look Ahead terdeteksi!", state=state)
    result = route_sa(Err(error))
    assert result == NODE_SA


def test_route_he_non_falsifiable() -> None:
    """Jika HE mendeteksi ide tidak falsifiable (dan retry < max), putar balik ke HE."""
    state = get_dummy_state(retry_count=1)
    error = NonFalsifiableError("Tidak bisa diukur.", state=state)
    result = route_he(Err(error))
    assert result == NODE_HE


# =============================================================================
# SKENARIO 3: UJI RUTE "FATAL ERROR" (BATAL TOTAL)
# =============================================================================

def test_route_missing_data() -> None:
    """Jika ada MissingDataError di node mana pun, graf harus langsung dihentikan (__end__)."""
    error = MissingDataError("Data prasyarat hilang.")
    
    assert route_mad(Err(error)) == NODE_END
    assert route_he(Err(error)) == NODE_END
    assert route_sa(Err(error)) == NODE_END


# =============================================================================
# SKENARIO 4: UJI CIRCUIT BREAKER (MENCEGAH INFINITE LOOP)
# =============================================================================

def test_route_max_retries() -> None:
    """
    Jika error terjadi tetapi retry_count sudah mencapai batas (misal: 3),
    router harus menyerah dan mengembalikan NODE_END.
    """
    state = get_dummy_state(retry_count=3)  # MAX_RETRIES tercapai
    error = LookAheadBiasError("Ngeyel pakai t+1", state=state)
    
    result = route_sa(Err(error))
    
    assert result == NODE_END, "Circuit Breaker gagal menghentikan infinite loop!"
