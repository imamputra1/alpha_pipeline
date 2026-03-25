"""
Defines Structural Subtyping (Protocols/Interfaces) for Dependency Injection.
Enforces strict contracts for LLM Gateways and Agent Functions to ensure
composability and predictability within the LangGraph ecosystem.
"""

from typing import Protocol, TypeVar

from pydantic import BaseModel

from src.types import (
    DomainError,
    PipelineState,
    Result,
)

T_Schema = TypeVar("T_Schema", bound=BaseModel)


class LLMGateway(Protocol):
    """
    Kontrak antarmuka wajib untuk semua konektor LLM eksternal (Gemini, Claude, dll).
    Menerapkan prinsip Dependency Inversion: Agen bergantung pada abstraksi ini,
    bukan pada implementasi spesifik vendor API.
    """

    def ganerate_structured(
        self,
        prompt: str,
        response_schema: type[T_Schema],
    ) -> Result[T_Schema, Exception]:
        """
        Menghasilkan output terstruktur dari LLM.

        Args:
            prompt (str): Instruksi sistem/konteks.
            response_schema (type[T_Schema]): Kelas Pydantic sebagai target parsing/DoD.

        Returns:
            Result[T_Schema, Exception]:
                - Ok(T_Schema) jika LLM merespons sesuai skema JSON.
                - Err(Exception) jika terjadi kegagalan jaringan, timeout, atau format kacau.
        """
        ...


class AgentFunction(Protocol):
    """
    Kontrak antarmuka homogen untuk semua node Agen (MAD, HE, SA) di dalam LangGraph.
    Memungkinkan Supervisor untuk memanggil agen apa pun secara seragam (duck-typing).
    """

    def __call__(
        self, state: PipelineState, llm: LLMGateway
    ) -> Result[PipelineState, DomainError]:
        """
        Eksekusi logika agen (Fungsi murni dengan dependensi injeksi).

        Args:
            state (PipelineState): Struct memori statis pada waktu t.
            llm (LLMGateway): Objek konektor LLM yang disuntikkan.

        Returns:
            Result[PipelineState, DomainError]:
                - Ok(PipelineState) dengan data mutasi (state baru) jika lolos filter.
                - Err(DomainError) jika agen melanggar aturan kuantitatif
                  (misal: LookAheadBiasError, NonFalsifiableError).
        """
        ...
