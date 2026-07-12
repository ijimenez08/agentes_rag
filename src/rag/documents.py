"""Lectura de archivos subidos sin rutas fijas del computador."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Protocol

from docx import Document as DocumentoWord
from langchain_core.documents import Document
from pypdf import PdfReader


class ArchivoSubido(Protocol):
    name: str

    def getvalue(self) -> bytes: ...


def _documento(texto: str, nombre: str, pagina: int | None = None) -> Document:
    metadata: dict[str, str | int] = {"source": nombre}
    if pagina is not None:
        metadata["page"] = pagina
    return Document(page_content=texto.strip(), metadata=metadata)


def leer_archivo(archivo: ArchivoSubido) -> list[Document]:
    """Convierte PDF, DOCX, TXT o MD en documentos de LangChain."""
    extension = Path(archivo.name).suffix.lower()
    contenido = archivo.getvalue()

    if extension == ".pdf":
        lector = PdfReader(BytesIO(contenido))
        documentos = []
        for numero, pagina in enumerate(lector.pages, start=1):
            texto = pagina.extract_text() or ""
            if texto.strip():
                documentos.append(_documento(texto, archivo.name, numero))
        return documentos

    if extension == ".docx":
        word = DocumentoWord(BytesIO(contenido))
        texto = "\n".join(p.text for p in word.paragraphs if p.text.strip())
        return [_documento(texto, archivo.name)] if texto else []

    if extension in {".txt", ".md"}:
        texto = contenido.decode("utf-8", errors="replace")
        return [_documento(texto, archivo.name)] if texto.strip() else []

    raise ValueError(f"Formato no permitido: {extension or 'sin extensión'}")


def leer_archivos(archivos: list[ArchivoSubido]) -> list[Document]:
    documentos: list[Document] = []
    for archivo in archivos:
        documentos.extend(leer_archivo(archivo))
    return documentos