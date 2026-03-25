"""
Concrete implementation of LLMGateway using Google's Gemini via LangChain.
Enforces Pydantic structured outputs and wraps all network/parsing I/O
in the Result Monad. Includes a MockGateway for TDD.
"""

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from src.protocol.agent_behavior import LLMGateway, T_Schema
from src.types.domain_errors import StructuralFormattingError
from src.types.result import Err, Ok, Result


class GeminiGateway(LLMGateway):
    """
    Gateway nyata untuk berinteraksi dengan Google Gemini.
    Mengatur temperature=0.0 untuk penalaran deterministik dan memaksa output terstruktur.
    Sesuai filosofi "Survival First": Jika LLM berhalusinasi format, sistem gagal dengan aman.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0.0,
        api_key: str | None = None,
    ) -> None:
        """
        Inisialisasi klien Gemini.

        Args:
            model_name (str): Versi model Gemini yang digunakan.
            temperature (float): Tingkat kreativitas (wajib 0.0 untuk analitik kuantitatif murni).
            api_key (str | None): Kunci API. Jika None, LangChain otomatis mencari `GOOGLE_API_KEY` env var.
        """
        self.client = ChatGoogleGenerativeAI(
            model=model_name, temperature=temperature, api_key=api_key
        )

    def generate_structured(
        self, prompt: str, response_schema: type[T_Schema]
    ) -> Result[T_Schema, Exception]:
        """
        Menjalankan prompt dan memaksa output sesuai Pydantic schema (DoD).
        Semua error (jaringan, parsing gagal, limit API) ditangkap dan dibungkus monad Err.
        """
        try:
            structured_llm = self.client.with_structured_output(response_schema)
            raw_response: Any = structured_llm.invoke(prompt)
            if isinstance(raw_response, response_schema):
                return Ok(raw_response)
            if isinstance(raw_response, dict):
                parsed_response = response_schema.model_validate(raw_response)
                return Ok(parsed_response)
            error_msg = f"LangChain returned unexpected type: {type(raw_response)}. Exception {response_schema.__name__} or dict."
            return Err(StructuralFormattingError(error_msg))

        except Exception as e:
            return Err(e)


class MockGateway(LLMGateway):
    """
    Gateway tiruan untuk keperluan Test-Driven Development (TDD) dan CI/CD.
    """

    def __init__(
        self, default_responses: dict[type[BaseModel], dict[str, Any]] | None = None
    ) -> None:
        """
        Inisialisasi mock gateway dengan respons injeksi opsional.

        Args:
            default_responses: Pemetaan antara tipe skema (Pydantic model) dan dictionary dummy-nya.
        """
        self.default_responses = default_responses or {}

    def generate_structured(
        self, prompt: str, response_schema: type[T_Schema]
    ) -> Result[T_Schema, Exception]:
        """
        Mengembalikan data Pydantic tiruan (Mock) tanpa menembak API Google.
        """
        try:
            if response_schema in self.default_responses:
                dummy_dict = self.default_responses[response_schema]
                return Ok(response_schema.model_validate(dummy_dict))
            dummy_fallback = response_schema.model_construct(status="Pass")

            return Ok(dummy_fallback)

        except Exception as e:
            return Err(e)
