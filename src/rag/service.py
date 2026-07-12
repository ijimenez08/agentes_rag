"""Flujo RAG: fragmentar, indexar, recuperar y responder."""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import ConfiguracionModelo
from .providers import crear_modelos


PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Eres un asistente RAG. Responde en español usando únicamente el contexto.
Si el contexto no contiene la respuesta, dilo claramente y no inventes datos.
Sé preciso, práctico y cita las fuentes con [nombre del archivo, p. N] cuando haya página.

Historial reciente:
{historial}

Contexto recuperado:
{contexto}""",
        ),
        ("human", "{pregunta}"),
    ]
)


class ServicioRAG:
    def __init__(self, config: ConfiguracionModelo):
        self.llm, self.embeddings = crear_modelos(config)
        self.vectorstore: InMemoryVectorStore | None = None
        self.cadena = PROMPT | self.llm | StrOutputParser()

    def indexar(self, documentos: list[Document]) -> int:
        if not documentos:
            raise ValueError("No se encontró texto legible en los archivos.")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=120,
            add_start_index=True,
        )
        fragmentos = splitter.split_documents(documentos)
        self.vectorstore = InMemoryVectorStore.from_documents(
            documents=fragmentos,
            embedding=self.embeddings,
        )
        return len(fragmentos)

    def preguntar(
        self,
        pregunta: str,
        historial: list[dict[str, str]] | None = None,
        k: int = 4,
    ) -> tuple[str, list[dict[str, str | int]]]:
        if self.vectorstore is None:
            raise RuntimeError("Primero debes procesar los archivos.")

        encontrados = self.vectorstore.similarity_search(pregunta, k=k)
        contexto = "\n\n".join(self._formatear_fragmento(doc) for doc in encontrados)
        respuesta = self.cadena.invoke(
            {
                "pregunta": pregunta,
                "contexto": contexto,
                "historial": self._formatear_historial(historial or []),
            }
        )
        fuentes = self._fuentes_unicas(encontrados)
        return respuesta, fuentes

    @staticmethod
    def _formatear_fragmento(doc: Document) -> str:
        nombre = doc.metadata.get("source", "archivo")
        pagina = doc.metadata.get("page")
        etiqueta = f"{nombre}, p. {pagina}" if pagina else str(nombre)
        return f"FUENTE: {etiqueta}\n{doc.page_content}"

    @staticmethod
    def _formatear_historial(historial: list[dict[str, str]]) -> str:
        recientes = historial[-6:]
        if not recientes:
            return "Sin historial."
        return "\n".join(
            f"{('Usuario' if m['role'] == 'user' else 'Asistente')}: {m['content']}"
            for m in recientes
        )

    @staticmethod
    def _fuentes_unicas(documentos: list[Document]) -> list[dict[str, str | int]]:
        vistas: set[tuple[str, int | str]] = set()
        resultado: list[dict[str, str | int]] = []
        for doc in documentos:
            nombre = str(doc.metadata.get("source", "archivo"))
            pagina = doc.metadata.get("page", "")
            clave = (nombre, pagina)
            if clave not in vistas:
                vistas.add(clave)
                fuente: dict[str, str | int] = {"archivo": nombre}
                if pagina:
                    fuente["pagina"] = int(pagina)
                resultado.append(fuente)
        return resultado