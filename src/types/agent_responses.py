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
    DoD untuk agen Market Asymmetry Detective.
    Fokus utama: Siapa yang mensubsidi profit kita? (Counterparty analysis).
    Jika kita tidak tahu siapa yang kalah, berarti kita yang kalah.
    """

    status: Literal["Pass", "Fail"] = Field(
        description="Harus 'Pass' jika ada inefisiensi pasar yang logis. 'Fail' jika asumsi terlalu naif atau tidak masuk akal."
    )
    counterparty: str = Field(
        description="Identifikasi spesifik partisipan pasar yang menjadi sumber edge kita (misal: 'Retail stop-loss hunters', 'Slow liquidity providers')."
    )
    economic_rationale: str = Field(
        description="Penjelasan murni mekanisme mikrostruktur. DILARANG menggunakan alasan teknikal (seperti RSI overbought)."
    )
    revision_notes: str | None = Field(
        default=None,
        description="Jika status 'Fail', jelaskan alasan penolakannya di sini agar LLM bisa belajar di iterasi berikutnya.",
    )


class HEResponse(BaseModel):
    """
    DoD untuk agen Hypothesis Engineer.
    Fokus utama: Mengubah narasi ekonomi menjadi hipotesis yang BISA DIBANTAH (Falsifiable).
    Semua harus berakar pada probabilitas statistik, bukan opini.
    """

    status: Literal["Pass", "Fail"] = Field(
        description="Harus 'Pass' jika hipotesis bisa diuji secara statistik. 'Fail' jika mengandung ambiguitas waktu atau kata bersayap."
    )
    independent_variables: list[str] = Field(
        description="Daftar metrik observasi/katalis (State A) yang memicu sinyal."
    )
    dependent_variable: str = Field(
        description="Arah return, spread, atau pergerakan harga yang diekspektasikan (Y)."
    )
    time_horizon: str = Field(
        description="Batas waktu ekspektasi absolut. Harus presisi (misal: '100ms', '1-tick', '5-minutes', bukan 'soon' atau 'eventually')."
    )
    null_hypothesis: str = Field(
        description="H0: Kondisi di mana edge kita TIDAK ADA (misal: 'Spread tidak mean-reverting dalam 100ms')."
    )
    alternative_hypothesis: str = Field(
        description="H1: Kondisi di mana edge kita ADA dan tervalidasi."
    )
    revision_notes: str | None = Field(
        default=None, description="Catatan koreksi jika status 'Fail'."
    )


class SAResponse(BaseModel):
    """
    DoD untuk agen Signal Architect.
    Fokus utama: Transformasi hipotesis menjadi formula matematis murni.
    SANGAT KRITIKAL: Modul ini adalah garis pertahanan terakhir sebelum uang sungguhan terbakar.
    """

    status: Literal["Pass", "Fail"] = Field(
        description="Evaluasi final. 'Fail' jika model terindikasi memiliki look-ahead bias atau menggunakan harga absolut (non-stasioner)."
    )
    formula_latex: str = Field(
        description="Formula Sinyal (S_t) dalam format LaTeX murni. Contoh: S_t = \\alpha (P_t - P_{t-1})."
    )
    variables_dict: dict[str, str] = Field(
        description="Kamus pemetaan variabel LaTeX. Key: Simbol (misal: '\\pi_t'). Value: Definisi tegas."
    )
    is_stationary: bool = Field(
        description="LLM WAJIB mendeklarasikan apakah output fungsinya stasioner (misal: z-score, log-return). Jika False, strategi ini akan hancur."
    )
    has_look_ahead_bias: bool = Field(
        description="Self-Audit: Apakah fungsi menggunakan data masa depan (t+1)? Jika True, ini adalah DOSA BESAR dan harus di-routing ke kegagalan."
    )
    revision_notes: str | None = Field(
        default=None,
        description="Umpan balik jika terdapat kesalahan struktural atau matematis.",
    )
