"""
Module: src/workflow/graph_builder.py
Description: Assembles the LangGraph StateGraph. Acts as the factory that wires
             Pure Agents (Nodes) and Supervisor Logic (Edges) together using
             Dependency Injection for the LLM Gateway.
             Linter/Mypy strict compliant.
"""

from typing import Any, cast

from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.he_agent import evaluate_he
from src.agents.mad_agent import evaluate_mad
from src.agents.sa_agent import evaluate_sa
from src.protocol.agent_behavior import LLMGateway
from src.types.domain_errors import (
    DomainError,
    LookAheadBiasError,
    MissingDataError,
    NonFalsifiableError,
    NonStationaryError,
)
from src.types.pipeline_state import PipelineState
from src.types.result import Err, Ok
from src.workflow.routing_logic import (
    NODE_HE,
    NODE_MAD,
    NODE_SA,
    route_he,
    route_mad,
    route_sa,
)


def build_alpha_graph(llm: LLMGateway) -> CompiledStateGraph:  # type: ignore[type-arg]
    """
    Factory function untuk merakit graf LangGraph.
    Menggunakan # type: ignore[type-arg] pada CompiledStateGraph untuk
    mencegah konflik antar versi LangGraph yang terus berubah arity generiknya.
    """
    builder = StateGraph(PipelineState)

    # =========================================================================
    # 1. NODE WRAPPERS (CLOSURES)
    # =========================================================================

    def mad_node_wrapper(state: PipelineState) -> dict[str, Any]:
        result = evaluate_mad(state, llm)
        if isinstance(result, Ok):
            new_state = result.unwrap()
            return {
                "economic_rationale": new_state["economic_rationale"],
                "retry_count": 0,
            }
        else:
            err = result.unwrap_err()
            return {
                "error_logs": [f"{type(err).__name__}: {err.message}"],
                "retry_count": state.get("retry_count", 0) + 1,
            }

    def he_node_wrapper(state: PipelineState) -> dict[str, Any]:
        result = evaluate_he(state, llm)
        if isinstance(result, Ok):
            new_state = result.unwrap()
            return {
                "falsifiable_hypothesis": new_state["falsifiable_hypothesis"],
                "retry_count": 0,
            }
        else:
            err = result.unwrap_err()
            return {
                "error_logs": [f"{type(err).__name__}: {err.message}"],
                "retry_count": state.get("retry_count", 0) + 1,
            }

    def sa_node_wrapper(state: PipelineState) -> dict[str, Any]:
        result = evaluate_sa(state, llm)
        if isinstance(result, Ok):
            new_state = result.unwrap()
            return {
                "signal_architecture": new_state["signal_architecture"],
                "retry_count": 0,
            }
        else:
            err = result.unwrap_err()
            return {
                "error_logs": [f"{type(err).__name__}: {err.message}"],
                "retry_count": state.get("retry_count", 0) + 1,
            }

    # =========================================================================
    # 2. ROUTER ADAPTERS
    # =========================================================================

    def mad_edge_adapter(state: PipelineState) -> str:
        # Cast TypedDict ke dict standar untuk memuaskan strict type checker
        state_dict = cast(dict[str, Any], state)

        if state.get("retry_count", 0) > 0:
            last_log = state["error_logs"][-1] if state.get("error_logs") else ""
            if "MissingDataError" in last_log:
                return route_mad(Err(MissingDataError(last_log, state=state_dict)))
            return route_mad(Err(DomainError(last_log, state=state_dict)))
        return route_mad(Ok(state))

    def he_edge_adapter(state: PipelineState) -> str:
        state_dict = cast(dict[str, Any], state)

        if state.get("retry_count", 0) > 0:
            last_log = state["error_logs"][-1] if state.get("error_logs") else ""
            if "MissingDataError" in last_log:
                return route_he(Err(MissingDataError(last_log, state=state_dict)))
            elif "NonFalsifiableError" in last_log:
                return route_he(Err(NonFalsifiableError(last_log, state=state_dict)))
            return route_he(Err(DomainError(last_log, state=state_dict)))
        return route_he(Ok(state))

    def sa_edge_adapter(state: PipelineState) -> str:
        state_dict = cast(dict[str, Any], state)

        if state.get("retry_count", 0) > 0:
            last_log = state["error_logs"][-1] if state.get("error_logs") else ""
            if "MissingDataError" in last_log:
                return route_sa(Err(MissingDataError(last_log, state=state_dict)))
            elif "LookAheadBiasError" in last_log:
                return route_sa(Err(LookAheadBiasError(last_log, state=state_dict)))
            elif "NonStationaryError" in last_log:
                return route_sa(Err(NonStationaryError(last_log, state=state_dict)))
            return route_sa(Err(DomainError(last_log, state=state_dict)))
        return route_sa(Ok(state))

    # =========================================================================
    # 3. GRAPH REGISTRATION & WIRING
    # =========================================================================

    builder.add_node(NODE_MAD, mad_node_wrapper)
    builder.add_node(NODE_HE, he_node_wrapper)
    builder.add_node(NODE_SA, sa_node_wrapper)

    builder.set_entry_point(NODE_MAD)

    builder.add_conditional_edges(NODE_MAD, mad_edge_adapter)
    builder.add_conditional_edges(NODE_HE, he_edge_adapter)
    builder.add_conditional_edges(NODE_SA, sa_edge_adapter)

    return builder.compile()
