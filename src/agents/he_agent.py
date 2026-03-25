"""
Module: src/agents/he_agent.py
Description: Pure function executor for Phase 2: Hypothesis Engineer.
             Maps the upgraded HEResponse (including market regime) to the pipeline state.
"""

import json

from src.protocol.agent_behavior import LLMGateway
from src.prompts.templates import HE_PROMPT_TEMPLATE
from src.types.agent_responses import HEResponse
from src.types.domain_errors import (
    DomainError,
    MissingDataError,
    NonFalsifiableError,
    StructuralFormattingError,
)
from src.types.pipeline_state import PipelineState
from src.types.result import Err, Ok, Result


def evaluate_he(
    state: PipelineState, llm: LLMGateway
) -> Result[PipelineState, DomainError]:
    # 1. GUARD CLAUSE
    economic_rationale = state.get("economic_rationale")
    if not economic_rationale:
        return Err(
            MissingDataError("HE Agent failed: 'economic_rationale' is missing.")
        )

    # 2. PROMPT ASSEMBLY
    error_logs = "\n".join(state.get("error_logs", [])) or "Tidak ada riwayat error."
    prompt = HE_PROMPT_TEMPLATE.format(
        economic_rationale=economic_rationale, error_logs=error_logs
    )

    # 3. LLM EXECUTION
    result = llm.generate_structured(prompt=prompt, response_schema=HEResponse)

    # 4. BUSINESS LOGIC
    if isinstance(result, Err):
        return Err(
            StructuralFormattingError(f"HE LLM parsing failed: {str(result.error)}")
        )

    response = result.unwrap()

    if response.status == "Fail":
        reason = response.revision_notes or "Ditolak: Ide tidak bisa dikuantifikasi."
        return Err(NonFalsifiableError(f"HE Rejection: {reason}"))

    # 5. STATE IMMUTABILITY & ADVANCED DATA MAPPING
    new_state = state.copy()
    new_state["falsifiable_hypothesis"] = json.dumps(
        {
            "independent_vars": response.independent_variables,
            "dependent_var": response.dependent_variable,
            "time_horizon": response.time_horizon,
            "market_regime": response.market_regime,
            "H0": response.null_hypothesis,
            "H1": response.alternative_hypothesis,
        }
    )

    return Ok(new_state)
