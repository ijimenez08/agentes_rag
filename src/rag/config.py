"""Configuración de modelos locales y de pago."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfiguracionModelo:
    """Datos necesarios para construir el chat y los embeddings."""

    proveedor: str
    modelo_chat: str
    modelo_embeddings: str
    api_key: str
    base_url: str | None = None

    def validar(self) -> None:
        if self.proveedor not in {"local", "openai", "nvidia"}:
            raise ValueError("El proveedor debe ser 'local', 'openai' o 'nvidia'.")
        if not self.modelo_chat.strip():
            raise ValueError("Indica el modelo de chat.")
        if not self.modelo_embeddings.strip():
            raise ValueError("Indica el modelo de embeddings.")
        if self.proveedor == "local" and not self.base_url:
            raise ValueError("Indica la URL del servidor de LM Studio.")
        if self.proveedor == "openai" and not self.api_key:
            raise ValueError("Falta OPENAI_API_KEY para usar la API de pago.")
        if self.proveedor == "nvidia" and not self.api_key:
            raise ValueError("Falta NVIDIA_API_KEY para usar la API de NVIDIA.")