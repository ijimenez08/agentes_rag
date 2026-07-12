"""Fábrica mínima de modelos compatibles con LangChain."""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings

from .config import ConfiguracionModelo


def crear_modelos(config: ConfiguracionModelo):
    """Devuelve (llm, embeddings) para LM Studio, OpenAI o NVIDIA."""
    config.validar()

    if config.proveedor == "nvidia":
        opciones = {
            "model": config.modelo_chat,
            "api_key": config.api_key,
            "temperature": 0,
        }
        opciones_embeddings = {
            "model": config.modelo_embeddings,
            "api_key": config.api_key,
            "truncate": "END",
        }
        if config.base_url:
            opciones["base_url"] = config.base_url.rstrip("/")
            opciones_embeddings["base_url"] = config.base_url.rstrip("/")

        return ChatNVIDIA(**opciones), NVIDIAEmbeddings(**opciones_embeddings)

    comunes = {"api_key": config.api_key or "lm-studio"}
    if config.base_url:
        comunes["base_url"] = config.base_url.rstrip("/")

    llm = ChatOpenAI(
        model=config.modelo_chat,
        temperature=0,
        timeout=120,
        max_retries=2,
        **comunes,
    )

    opciones_embeddings = dict(comunes)
    if config.proveedor == "local":
        # Evita que LangChain intente tokenizar modelos locales desconocidos.
        opciones_embeddings["check_embedding_ctx_length"] = False

    embeddings = OpenAIEmbeddings(
        model=config.modelo_embeddings,
        **opciones_embeddings,
    )
    return llm, embeddings