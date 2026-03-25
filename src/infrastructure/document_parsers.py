"""
Module: src/infrastructure/document_parsers.py
Description: Pure functions to parse raw bytes from Streamlit (PDF/CSV)
             into structured text for LLM ingestion.
             Wraps all volatile I/O operations safely in the Result Monad.
"""

import io
import re

import fitz  # PyMuPDF
import pandas as pd

from src.types.result import Err, Ok, Result


def extract_pdf_text(file_bytes: bytes) -> Result[str, Exception]:
    """
    Mengekstrak teks dari file PDF mentah menggunakan PyMuPDF.
    Membersihkan whitespace berlebih agar menghemat token LLM.
    """
    try:
        # Membaca dokumen langsung dari memori (RAM) tanpa menyentuh disk
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())

        raw_text = "\n".join(text_parts)

        # Pembersihan Data: Mengganti spasi, tab, atau newline ganda menjadi spasi tunggal
        # Ini krusial untuk mencegah Context Window Exhaustion.
        cleaned_text = re.sub(r"\s+", " ", raw_text).strip()

        return Ok(cleaned_text)

    except Exception as e:
        # Menangkap error jika file PDF korup atau dipassword
        return Err(e)


def extract_csv_summary(file_bytes: bytes) -> Result[str, Exception]:
    """
    Mengekstrak ringkasan analitik (EDA) dari CSV menggunakan Pandas.
    Haram memasukkan data mentah jutaan baris ke LLM. Kita hanya mengirim
    statistik deskriptif dan sampel kepala data.
    """
    try:
        # Memuat byte ke dalam buffer dan dibaca oleh Pandas
        df = pd.read_csv(io.BytesIO(file_bytes))

        # Merakit struktur Markdown untuk pemahaman spasial LLM
        summary_parts = [
            "### Exploratory Data Analysis (EDA) Summary ###\n",
            f"**Total Rows:** {len(df)}",
            f"**Total Columns:** {len(df.columns)}",
            f"**Variables:** {', '.join(df.columns)}\n",
            "**Data Sample (First 5 Rows):**",
            df.head().to_markdown(index=False),
            "\n**Descriptive Statistics:**",
            df.describe().to_markdown(),
        ]

        summary_string = "\n".join(summary_parts)

        return Ok(summary_string)

    except Exception as e:
        # Menangkap error jika CSV memiliki delimiter yang aneh atau format rusak
        return Err(e)


def parse_document(file_name: str, file_bytes: bytes) -> Result[str, Exception]:
    """
    Fungsi Router Utama (Polisi Lalu Lintas File).
    Dipanggil secara murni oleh Imperative Shell (Streamlit).
    """
    lower_name = file_name.lower()

    if lower_name.endswith(".pdf"):
        return extract_pdf_text(file_bytes)

    elif lower_name.endswith(".csv"):
        return extract_csv_summary(file_bytes)

    else:
        # Reject format selain PDF dan CSV dengan aman
        error_msg = f"Format file tidak didukung: '{file_name}'. Harap unggah dokumen .pdf atau .csv."
        return Err(ValueError(error_msg))
