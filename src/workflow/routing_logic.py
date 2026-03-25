from typing import Literal

from src.types.domain_errors import (
    DomainError,
    LookAheadBiasError,
    MissingDataError,
    NonFalsifiableError,
    NonStationaryError,
)
from src.types.pipeline_state import PipelineState
from src.types.result import Err, Ok, Result


NODE_MAD: Literal["mad_agent"] = "mad_agent"
NODE_HE: Literal["he_agent"] = "he_agent"
NODE_SA: Literal["sa_agent"] = "sa_agent"
NODE_END: Literal["__end__"] = "__end__"
MAX_RETRIES: int = 3


def route_mad(
    result: Result[PipelineState, DomainError],
) -> Literal["he_agent", "mad_agent", "__end__"]:
    """
    Router untuk Fase 1 (Market Asymmetry Detective).
    """
    match result:
        case Ok(_):
            return NODE_HE

        case Err(MissingDataError()):
            # Terminal fail, no retry for missing data
            return NODE_END

        case Err(e):
            # Fallback & Circuit Breaker untuk semua DomainError lainnya di MAD
            state = getattr(e, "state", None)
            if state and state.get("retry_count", 0) >= MAX_RETRIES:
                return NODE_END
            return NODE_MAD


def route_he(
    result: Result[PipelineState, DomainError],
) -> Literal["sa_agent", "he_agent", "__end__"]:
    """
    Router untuk Fase 2 (Hypothesis Engineer).
    """
    match result:
        case Ok(_):
            return NODE_SA

        case Err(MissingDataError()):
            return NODE_END

        case Err(NonFalsifiableError() as e):
            # Symmetric binding: tangkap instans secara langsung 'as e'
            if e.state and e.state.get("retry_count", 0) >= MAX_RETRIES:
                return NODE_END
            return NODE_HE

        case Err(e):
            state = getattr(e, "state", None)
            if state and state.get("retry_count", 0) >= MAX_RETRIES:
                return NODE_END
            return NODE_HE


def route_sa(
    result: Result[PipelineState, DomainError],
) -> Literal["sa_agent", "__end__"]:
    """
    Router untuk Fase 3 (Signal Architect). Paling ketat (Paranoia level).
    """
    match result:
        case Ok(_):
            # Matematika valid, sistem bertahan hidup. Selesai.
            return NODE_END

        case Err(MissingDataError()):
            return NODE_END

        # Kedua sub-pattern dalam 'OR' (|) menargetkan nama variabel yang sama ('e')
        case Err(LookAheadBiasError() as e) | Err(NonStationaryError() as e):
            # Haram rules violated. Putar balik ke SA jika masih ada "nyawa"
            if e.state and e.state.get("retry_count", 0) >= MAX_RETRIES:
                return NODE_END
            return NODE_SA

        case Err(e):
            state = getattr(e, "state", None)
            if state and state.get("retry_count", 0) >= MAX_RETRIES:
                return NODE_END
            return NODE_SA
