"""
Module: tests/unit/test_document_parsers.py
Description: In-memory I/O unit tests for Document Parsers.
             Zero disk writes. Maximum speed and paranoia.
"""

import fitz
import pytest

from src.infrastructure.document_parsers import (
    extract_csv_summary,
    extract_pdf_text,
    parse_document,
)
from src.types.result import is_err, is_ok

# =============================================================================
# IN-MEMORY FIXTURES (DUMMY BOMBS & GOLD)
# =============================================================================


@pytest.fixture
def valid_csv_bytes() -> bytes:
    """Membangun file CSV berstruktur di dalam RAM."""
    csv_content = (
        "time,price,volume\n10:00,100.5,500\n10:01,100.6,600\n10:02,100.4,450\n"
    )
    return csv_content.encode("utf-8")


@pytest.fixture
def invalid_bytes() -> bytes:
    """Membangun byte sampah untuk memicu parsing error (Corrupted File)."""
    return b"\x00\xff\x00\xff\x99GarbageData!!!"


@pytest.fixture
def valid_pdf_bytes() -> bytes:
    """
    Mencetak dokumen PDF resmi langsung ke dalam byte stream (RAM).
    Tidak menyentuh hard disk sama sekali.
    """
    doc = fitz.open()  # Buat PDF kosong
    page = doc.new_page()  # Tambah halaman

    # Sisipkan teks dengan spasi ganda untuk menguji regex pembersihan kita
    page.insert_text((50, 50), "Alpha   Signal\n\nDetected    Here.")

    pdf_bytes = doc.tobytes()
    doc.close()

    return pdf_bytes


# =============================================================================
# CSV PARSER TESTS
# =============================================================================


def test_extract_csv_summary_success(valid_csv_bytes: bytes) -> None:
    """Uji 'Happy Path': CSV valid harus menghasilkan ringkasan EDA Pandas."""
    result = extract_csv_summary(valid_csv_bytes)

    assert is_ok(result), "Parser gagal membaca byte CSV valid."
    summary = result.unwrap()

    # Verifikasi struktur EDA (Harus memiliki kolom dan info agregat)
    assert "price" in summary
    assert "volume" in summary
    assert "Exploratory Data Analysis" in summary
    assert "**Total Rows:** 3" in summary


def test_extract_csv_summary_corrupted(invalid_bytes: bytes) -> None:
    """Uji 'Sad Path': CSV korup harus ditangkap dan dikembalikan sebagai Err()."""
    result = extract_csv_summary(invalid_bytes)
    assert is_err(result), "Sistem gagal menangkap I/O error pada byte sampah CSV."


# =============================================================================
# PDF PARSER TESTS
# =============================================================================


def test_extract_pdf_text_success(valid_pdf_bytes: bytes) -> None:
    """Uji 'Happy Path': PDF valid harus diekstrak dan dibersihkan spasinya."""
    result = extract_pdf_text(valid_pdf_bytes)

    assert is_ok(result), "Parser gagal membaca byte PDF valid."
    text = result.unwrap()

    # Memastikan regex kita bekerja (spasi ganda menjadi tunggal)
    assert text == "Alpha Signal Detected Here.", (
        f"Teks tidak dibersihkan dengan benar: '{text}'"
    )


def test_extract_pdf_text_corrupted(invalid_bytes: bytes) -> None:
    """Uji 'Sad Path': PDF korup harus ditangkap dengan aman tanpa crash."""
    result = extract_pdf_text(invalid_bytes)
    assert is_err(result), "Sistem gagal menjebak PyMuPDF error."


# =============================================================================
# ROUTER TESTS (POLISI LALU LINTAS)
# =============================================================================


def test_parse_document_routing_pdf(valid_pdf_bytes: bytes) -> None:
    """Router harus meneruskan ekstensi .pdf ke extract_pdf_text."""
    result = parse_document("research_paper.pdf", valid_pdf_bytes)
    assert is_ok(result)
    assert "Alpha Signal" in result.unwrap()


def test_parse_document_routing_csv(valid_csv_bytes: bytes) -> None:
    """Router harus meneruskan ekstensi .csv ke extract_csv_summary."""
    # Menguji ketahanan terhadap format huruf besar (case-insensitivity)
    result = parse_document("TICK_DATA.CSV", valid_csv_bytes)
    assert is_ok(result)
    assert "Exploratory Data Analysis" in result.unwrap()


def test_parse_document_unsupported_extension() -> None:
    """Uji Terminal: Router harus menolak ekstensi selain PDF dan CSV secara murni."""
    result = parse_document("virus.exe", b"malware bytes")

    assert is_err(result)
    err = result.unwrap_err()
    assert isinstance(err, ValueError)
    assert "Format file tidak didukung" in str(err)
