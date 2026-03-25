"""
Module: src/types/pipeline_state.py
Description: Defines the strictly typed, logic-less data structures for the trading pipeline state.
             Follows the principle of 'Plain Data' (Struct/Record) to prevent hidden state mutations.
             Built specifically for LangGraph state management.
"""

import operator
from typing import Annotated, TypedDict


class PipelineState(TypedDict):
    """
    Wadah memori statis (Struct) yang dibawa keliling oleh LangGraph.

    SURVIVAL CHECKLIST:
    - Pastikan `retry_count` dievaluasi ketat oleh node Supervisor.
    - `error_logs` bersifat append-only untuk mencegah hilangnya konteks kegagalan (Look-Ahead Bias, dll).
    """

    raw_input: str
    economic_relationale: str | None
    falsifiable_hypothesis: str | None
    signal_architecture: dict[str, str] | None
    error_logs: Annotated[list[str], operator.add]
    retry_count: int
