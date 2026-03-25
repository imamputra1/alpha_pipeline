"""
Defines static, immutable domain errors (Guard Clauses) for the trading pipeline.
These act as the "Circuit Breakers" in our Result Monad.
Philosophy: "Survival First, Profit Second." If a rule is violated,
the system fails predictably and explicitly.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DomainError(Exception):
    """
    Akar dari semua domain error kuantitatif.
    Wajib immutable (frozen=True) agar state pesan kegagalan tidak termutasi
    saat dibawa berkeliling oleh monad Err().
    """

    message: str
    state: dict[str, Any] | None = None


@dataclass(frozen=True)
class NonFalsifiableError(DomainError):
    """
    Dipicu ketika Hypothesis Engine (HE) menghasilkan hipotesis yang tidak bisa diuji.
    Ciri-ciri: Mengandung ambiguitas waktu, kata bersayap, atau tidak ada Null Hypothesis (H0) yang jelas.
    Sistem kuantitatif tidak bisa beroperasi pada opini, hanya pada probabilitas yang bisa dibantah.
    """

    pass


@dataclass(frozen=True)
class LookAheadBiasError(DomainError):
    """
    PELANGGARAN FATAL (CARDINAL SIN).
    Dipicu jika agen Signal Architect menyusupkan variabel t+1 (masa depan)
    atau agregasi masa depan ke dalam pembentukan sinyal di waktu t.
    Look-ahead bias akan membuat backtest terlihat seperti mesin pencetak uang (Sharpe > 5),
    tapi akan langsung menghancurkan akun saat live trading.
    """

    pass


@dataclass(frozen=True)
class NonStationaryError(DomainError):
    """
    Dipicu jika model mencoba menggunakan harga absolut (seperti Pt)
    alih-alih deret waktu stasioner (seperti log-return, Z-Score dari spread, atau fractional differencing).
    Memasukkan data non-stasioner ke model statistik sama dengan membangun rumah di atas pasir hisap.
    """

    pass


@dataclass(frozen=True)
class StructuralFormattingError(DomainError):
    """
    Dipicu ketika agen LLM berhalusinasi dan gagal mematuhi skema output (Pydantic/JSON).
    Contoh: Kehilangan kunci `formula_latex` atau menghasilkan format list padahal diminta dict.
    Kita tidak mentolerir anomali parsing data.
    """

    pass


@dataclass(frozen=True)
class MissingDataError(DomainError):
    """
    Dipicu dalam LangGraph jika sebuah node dieksekusi tetapi prasyarat state-nya kosong.
    Contoh: Node SA dipanggil, tetapi `falsifiable_hypothesis` di PipelineState masih None.
    Menjamin linearitas dan integritas aliran data antar-fase.
    """

    pass


@dataclass(frozen=True)
class MaxRetriesExceededError(DomainError):
    """
    TERMINAL CIRCUIT BREAKER.
    Dipicu oleh Supervisor ketika LLM terus-menerus gagal memperbaiki kesalahannya
    (misal: ngeyel menggunakan Look-Ahead Bias) meskipun sudah diberi feedback loop.
    Lebih baik menghentikan eksekusi daripada memaksakan model yang cacat logika.
    """

    pass
