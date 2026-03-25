"""
Module: src/agents/mad_agent.py
Description: Pure function executor for Phase 1: Market Asymmetry Detective.
             Maps the upgraded MADResponse (including limits to arbitrage) to the pipeline state.
"""

import json

from src.protocol.agent_behavior import LLMGateway
from src.prompts.templates import MAD_PROMPT_TEMPLATE
from src.types.agent_responses import MADResponse
from src.types.domain_errors import (
    DomainError,
    MissingDataError,
    NonFalsifiableError,
    StructuralFormattingError,
)
from src.types.pipeline_state import PipelineState
from src.types.result import Err, Ok, Result


def evaluate_mad(
    state: PipelineState, llm: LLMGateway
) -> Result[PipelineState, DomainError]:
    # 1. GUARD CLAUSE
    raw_input = state.get("raw_input")
    if not raw_input:
        return Err(MissingDataError("MAD Agent failed: 'raw_input' is missing."))

    # 2. PROMPT ASSEMBLY
    error_logs = "\n".join(state.get("error_logs", [])) or "Tidak ada riwayat error."
    prompt = MAD_PROMPT_TEMPLATE.format(raw_input=raw_input, error_logs=error_logs)

    # 3. LLM EXECUTION
    result = llm.generate_structured(prompt=prompt, response_schema=MADResponse)

    # 4. BUSINESS LOGIC
    if isinstance(result, Err):
        return Err(
            StructuralFormattingError(f"MAD LLM parsing failed: {str(result.error)}")
        )

    response = result.unwrap()

    if response.status == "Fail":
        reason = response.revision_notes or "Ditolak: Tidak ada inefisiensi yang logis."
        return Err(NonFalsifiableError(f"MAD Rejection: {reason}"))

    # 5. STATE IMMUTABILITY & ADVANCED DATA MAPPING
    new_state = state.copy()
    new_state["economic_rationale"] = json.dumps(
        {
            "counterparty": response.counterparty,
            "classification": response.inefficiency_classification,
            "limits_to_arbitrage": response.limits_to_arbitrage,
            "rationale": response.economic_rationale,
        }
    )

    return Ok(new_state)
