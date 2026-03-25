"""
Defines the absolute Definition of Done (DoD) schemas using Pydantic.
These schemas force the LLM to output predictable, structured JSON.
Philosophy: "Survival First, Profit Second." If the LLM cannot fit
its logic into these strict constraints, the logic is flawed and must be rejected.
"""

from typing import Literal
from pydantic import BaseModel, Field


class MADResponse(BaseModel):
    """
    DoD untuk agen MAD yang berburu mangsa (Counterparty) dan inefisiensi.
    """

    status: Literal["Pass", "Fail"] = Field(
        description="Harus 'Pass' jika ada Limits to Arbitrage yang logis. 'Fail' jika ide halusinasi atau alpha sudah mati."
    )
    counterparty: str = Field(
        description="Identifikasi pihak yang mensubsidi trade (Mangsa)."
    )
    inefficiency_classification: Literal[
        "Structural/Rules",
        "Behavioral/Psychological",
        "Information Asymmetry/Latency",
        "Unknown",
    ] = Field(description="Kategorisasi jenis inefisiensi pasar.")
    limits_to_arbitrage: str = Field(
        description="Alasan mengapa institusi besar (e.g., Jump/RenTec) membiarkan alpha ini. (Capacity constraint, slippage, dll)."
    )
    economic_rationale: str = Field(
        description="Penjelasan mikrostruktur (Order book, flow, funding). HARAM analisis teknikal."
    )
    revision_notes: str | None = Field(
        default=None,
        description="Jika status 'Fail', jelaskan alasan penolakan (misal: 'Tidak ada limits to arbitrage').",
    )


class HEResponse(BaseModel):
    """
    DoD untuk agen HE yang menerjemahkan ke hipotesis falsifiable.
    """

    status: Literal["Pass", "Fail"] = Field(
        description="'Pass' jika bisa diukur murni dengan data L2/Ticks/Funding. 'Fail' jika tidak."
    )
    independent_variables: list[str] = Field(description="Daftar prediktor/sinyal (X).")
    dependent_variable: str = Field(description="Target return/arah (Y).")
    time_horizon: str = Field(
        description="Batas waktu absolut (misal: '100ms', '5-ticks'). Dilarang menggunakan waktu relatif."
    )
    market_regime: str = Field(
        description="Kondisi pasar spesifik tempat hipotesis ini valid (misal: 'Volatilitas top 10%')."
    )
    null_hypothesis: str = Field(description="H0: Sinyal hanyalah noise acak.")
    alternative_hypothesis: str = Field(description="H1: Arah edge sesuai narasi MAD.")
    revision_notes: str | None = Field(
        default=None, description="Catatan koreksi jika status 'Fail'."
    )


class SAResponse(BaseModel):
    """
    DoD untuk agen SA. Lapisan pertahanan paling paranoid terhadap friksi pasar.
    """

    status: Literal["Pass", "Fail"] = Field(
        description="'Fail' jika ada Look-Ahead Bias, Non-Stationarity, atau mengabaikan biaya eksekusi."
    )
    raw_signal_formula_latex: str = Field(
        description="Formula Sinyal Mentah (S_t) dalam LaTeX murni."
    )
    expected_net_edge_formula_latex: str = Field(
        description="Formula Expected Net Edge (\\tilde{\\phi}_t) yang mendiskontokan S_t dengan probabilitas gagal dan biaya eksekusi."
    )
    execution_logic: str = Field(
        description="Logika trigger kondisional (Kapan Beli/Jual/Batal)."
    )
    variables_dict: dict[str, str] = Field(description="Kamus pemetaan variabel LaTeX.")
    is_stationary: bool = Field(
        description="Self-Audit: Apakah fungsi prediktor stasioner?"
    )
    considers_execution_costs: bool = Field(
        description="Self-Audit: Apakah model memasukkan penalti slippage dan fee secara eksplisit?"
    )
    has_look_ahead_bias: bool = Field(
        description="Self-Audit: Apakah ada kebocoran masa depan (t+1)? (Jika True, sistem akan langsung menolak)."
    )
    revision_notes: str | None = Field(
        default=None,
        description="Umpan balik jika terdapat kesalahan struktural atau matematis.",
    )
