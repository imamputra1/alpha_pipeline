"""
Module: src/agents/sa_agent.py
Description: Pure function executor for Phase 3: Signal Architect.
             Enforces Look-Ahead Bias, Stationarity, AND Execution Cost validations.
"""

from src.protocol.agent_behavior import LLMGateway
from src.prompts.templates import SA_PROMPT_TEMPLATE
from src.types.agent_responses import SAResponse
from src.types.domain_errors import (
    DomainError,
    LookAheadBiasError,
    MissingDataError,
    NonStationaryError,
    StructuralFormattingError,
)
from src.types.pipeline_state import PipelineState
from src.types.result import Err, Ok, Result


def evaluate_sa(
    state: PipelineState, llm: LLMGateway
) -> Result[PipelineState, DomainError]:
    # 1. GUARD CLAUSE
    hypothesis = state.get("falsifiable_hypothesis")
    if not hypothesis:
        return Err(
            MissingDataError("SA Agent failed: 'falsifiable_hypothesis' is missing.")
        )

    # 2. PROMPT ASSEMBLY
    error_logs = "\n".join(state.get("error_logs", [])) or "Tidak ada riwayat error."
    prompt = SA_PROMPT_TEMPLATE.format(
        falsifiable_hypothesis=hypothesis, error_logs=error_logs
    )

    # 3. LLM EXECUTION
    result = llm.generate_structured(prompt=prompt, response_schema=SAResponse)

    # 4. BUSINESS LOGIC & SURVIVAL FILTERS
    if isinstance(result, Err):
        return Err(
            StructuralFormattingError(f"SA LLM parsing failed: {str(result.error)}")
        )

    response = result.unwrap()

    # STRICT FAIL-SAFES (The "Paranoia" Filters)
    if response.has_look_ahead_bias:
        msg = response.revision_notes or "Terdeteksi kebocoran masa depan (t+1)."
        return Err(LookAheadBiasError(f"CARDINAL SIN (Look-Ahead): {msg}"))

    if not response.is_stationary:
        msg = response.revision_notes or "Deret waktu tidak stasioner."
        return Err(NonStationaryError(f"STATISTICAL FAILURE (Non-Stationary): {msg}"))

    # NEW SURVIVAL FILTER: ILLUSION OF EXECUTION
    if not response.considers_execution_costs:
        msg = (
            response.revision_notes
            or "Model mengabaikan biaya eksekusi dan slippage non-linear."
        )
        return Err(DomainError(f"ILLUSION OF EXECUTION: {msg}"))

    if response.status == "Fail":
        msg = response.revision_notes or "Sinyal ditolak secara matematis."
        return Err(DomainError(f"SA Rejection: {msg}"))

    # 5. STATE UPDATE & ADVANCED MAPPING
    new_state = state.copy()
    new_state["signal_architecture"] = {
        "raw_signal_formula": response.raw_signal_formula_latex,
        "expected_net_edge_formula": response.expected_net_edge_formula_latex,
        "execution_logic": response.execution_logic,
        "variables": str(response.variables_dict),
    }

    return Ok(new_state)
