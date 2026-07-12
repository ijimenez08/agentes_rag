"""Interfaz Streamlit del asistente RAG."""

from __future__ import annotations

import os
import sys
import hashlib
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))

from rag import ConfiguracionModelo, ServicioRAG  # noqa: E402
from rag.admin import (  # noqa: E402
    cargar_configuracion_privada,
    guardar_configuracion_privada,
    verificar_clave,
)
from rag.documents import (  # noqa: E402
    leer_archivos,
    leer_carpeta,
    listar_archivos_carpeta,
)


load_dotenv()
st.set_page_config(
    page_title="Normativa Laboral de Panamá",
    page_icon="⚖️",
    layout="centered",
)


def secreto(nombre: str, defecto: str = "") -> str:
    """Lee primero variables del sistema y luego secretos de Streamlit."""
    valor = os.getenv(nombre)
    if valor:
        return valor
    try:
        return str(st.secrets.get(nombre, defecto))
    except FileNotFoundError:
        return defecto


def ruta_configuracion() -> Path:
    ruta = secreto("RAG_CONFIG_PATH", ".runtime/private_config.json")
    return Path(ruta).expanduser()


def ajustes_iniciales() -> dict:
    """Carga las API desde variables privadas, nunca desde controles públicos."""
    base = {
        "proveedor": secreto("RAG_PROVIDER", "local"),
        "local": {
            "base_url": secreto(
                "LM_STUDIO_BASE_URL",
                secreto("OPENAI_API_BASE", "http://localhost:1234/v1"),
            ),
            "modelo_chat": secreto(
                "LM_STUDIO_CHAT_MODEL", secreto("LM_STUDIO_MODEL", "")
            ),
            "modelo_embeddings": secreto(
                "LM_STUDIO_EMBEDDING_MODEL",
                "text-embedding-embeddinggemma-300m",
            ),
            "api_key": secreto("LM_STUDIO_API_KEY", "lm-studio"),
        },
        "openai": {
            "base_url": "",
            "modelo_chat": secreto("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
            "modelo_embeddings": secreto(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
            ),
            "api_key": secreto("OPENAI_API_KEY"),
        },
        "nvidia": {
            "base_url": secreto(
                "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
            ),
            "modelo_chat": secreto(
                "NVIDIA_CHAT_MODEL", "meta/llama-3.1-8b-instruct"
            ),
            "modelo_embeddings": secreto(
                "NVIDIA_EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5"
            ),
            "api_key": secreto("NVIDIA_API_KEY"),
        },
    }
    guardados = cargar_configuracion_privada(ruta_configuracion())
    if guardados.get("proveedor") in {"local", "openai", "nvidia"}:
        base["proveedor"] = guardados["proveedor"]
    for proveedor in ("local", "openai", "nvidia"):
        if isinstance(guardados.get(proveedor), dict):
            base[proveedor].update(guardados[proveedor])
    return base


def construir_configuracion(ajustes: dict) -> ConfiguracionModelo:
    proveedor = ajustes["proveedor"]
    valores = ajustes[proveedor]
    return ConfiguracionModelo(
        proveedor=proveedor,
        modelo_chat=str(valores.get("modelo_chat", "")),
        modelo_embeddings=str(valores.get("modelo_embeddings", "")),
        api_key=str(valores.get("api_key", "")),
        base_url=str(valores.get("base_url", "")) or None,
    )


def panel_administracion(ajustes: dict) -> None:
    """Mantiene todos los datos de las API detrás del inicio administrativo."""
    with st.sidebar.expander("🔒 Administración"):
        if not st.session_state.get("admin_autenticado", False):
            usuario = st.text_input("Usuario", key="admin_usuario")
            clave = st.text_input("Contraseña", type="password", key="admin_clave")
            if st.button("Ingresar", key="admin_ingresar", use_container_width=True):
                usuario_correcto = secreto("ADMIN_USERNAME")
                hash_correcto = secreto("ADMIN_PASSWORD_HASH")
                if (
                    usuario_correcto
                    and hash_correcto
                    and usuario == usuario_correcto
                    and verificar_clave(clave, hash_correcto)
                ):
                    st.session_state.admin_autenticado = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
            return

        st.success("Sesión administrativa activa")
        nombres = {
            "local": "Local · LM Studio",
            "openai": "API de pago · OpenAI",
            "nvidia": "API · NVIDIA NIM",
        }
        inverso = {nombre: clave for clave, nombre in nombres.items()}
        proveedor_visible = st.selectbox(
            "Proveedor activo",
            list(inverso),
            index=list(inverso).index(nombres[ajustes["proveedor"]]),
        )
        proveedor = inverso[proveedor_visible]
        valores = ajustes[proveedor]

        with st.form("configuracion_api"):
            modelo_chat = st.text_input(
                "Modelo de chat", value=str(valores.get("modelo_chat", ""))
            )
            modelo_embeddings = st.text_input(
                "Modelo de embeddings",
                value=str(valores.get("modelo_embeddings", "")),
            )
            base_url = st.text_input(
                "URL base", value=str(valores.get("base_url", ""))
            )
            nueva_clave = st.text_input(
                "Nueva clave API",
                type="password",
                help="Déjala vacía para conservar la clave actual.",
            )
            guardar = st.form_submit_button(
                "Guardar configuración", type="primary", use_container_width=True
            )

        if guardar:
            ajustes["proveedor"] = proveedor
            ajustes[proveedor].update(
                {
                    "modelo_chat": modelo_chat.strip(),
                    "modelo_embeddings": modelo_embeddings.strip(),
                    "base_url": base_url.strip(),
                }
            )
            if nueva_clave:
                ajustes[proveedor]["api_key"] = nueva_clave.strip()
            guardar_configuracion_privada(ruta_configuracion(), ajustes)
            st.session_state.pop("servicio_rag", None)
            st.session_state.pop("huella_rag", None)
            st.session_state.mensajes = []
            st.success("Configuración guardada.")
            st.rerun()

        if st.button("Cerrar sesión", key="admin_salir", use_container_width=True):
            st.session_state.admin_autenticado = False
            st.rerun()


def huella_configuracion(configuracion: ConfiguracionModelo) -> tuple[str, str, str, str]:
    """Identifica cambios que obligan a regenerar los embeddings."""
    return (
        configuracion.proveedor,
        configuracion.modelo_chat,
        configuracion.modelo_embeddings,
        configuracion.base_url or "",
    )


def mostrar_error(mensaje: str, error: Exception) -> None:
    """Evita revelar proveedor, modelo o endpoint a usuarios públicos."""
    if st.session_state.get("admin_autenticado", False):
        st.error(f"{mensaje}: {error}")
    else:
        st.error(f"{mensaje}. Contacta al administrador.")


def firma_documentos_base(archivos: list[Path], carpeta: Path) -> tuple:
    """Detecta cambios sin volver a generar embeddings en cada rerun."""
    return tuple(
        (
            str(archivo.relative_to(carpeta)),
            archivo.stat().st_size,
            archivo.stat().st_mtime_ns,
        )
        for archivo in archivos
    )


def firma_archivos_subidos(archivos) -> tuple:
    return tuple(
        (archivo.name, hashlib.sha256(archivo.getvalue()).hexdigest())
        for archivo in (archivos or [])
    )


def cargar_indice_automaticamente(
    config: ConfiguracionModelo,
    carpeta: Path,
    archivos_base: list[Path],
    archivos_subidos,
    firma_indice: tuple,
) -> None:
    """Combina ambas fuentes y crea el índice una vez por cada cambio."""
    documentos_base = leer_carpeta(carpeta)
    documentos_usuario = leer_archivos(archivos_subidos or [])
    documentos = documentos_base + documentos_usuario
    if not documentos:
        raise ValueError("No se encontró texto legible en los documentos.")

    servicio = ServicioRAG(config)
    cantidad = servicio.indexar(documentos)
    st.session_state.servicio_rag = servicio
    st.session_state.huella_rag = huella_configuracion(config)
    st.session_state.firma_indice = firma_indice
    st.session_state.pop("firma_indice_fallida", None)
    st.session_state.mensajes = []
    st.session_state.resumen_indice = {
        "base": len(archivos_base),
        "subidos": len(archivos_subidos or []),
        "fragmentos": cantidad,
    }


st.title("⚖️ Normativa Laboral de Panamá")
st.subheader("Legislación y políticas laborales fundamentales")
st.caption(
    "Consulta la base documental normativa mediante preguntas en lenguaje natural."
)
st.info(
    "Las respuestas son informativas y se basan exclusivamente en los documentos "
    "disponibles. Verifica siempre la vigencia de la norma y consulta a un profesional "
    "del derecho cuando necesites una interpretación aplicable a un caso concreto."
)
with st.expander("Ejemplos de consultas"):
    st.markdown(
        """
- ¿Qué establece la normativa disponible sobre este derecho laboral?
- ¿En qué artículo o página se fundamenta la respuesta?
- ¿Qué requisitos aparecen en los documentos para este procedimiento?
- ¿Los instrumentos cargados señalan excepciones o condiciones especiales?
- ¿Qué información no puede confirmarse con la base actual?
"""
    )

ajustes = ajustes_iniciales()
panel_administracion(ajustes)
config = construir_configuracion(ajustes)
carpeta_documentos = Path(
    secreto("RAG_DOCUMENTS_PATH", "data/documentos_base")
).expanduser()
archivos = st.file_uploader(
    "Agregar legislación, reglamentos o políticas laborales",
    type=["pdf", "docx", "txt", "md"],
    accept_multiple_files=True,
)
k = 4

archivos_almacenados = listar_archivos_carpeta(carpeta_documentos)
if archivos_almacenados:
    st.info(
        f"📁 Base normativa disponible: {len(archivos_almacenados)} "
        "documento(s). Se cargan automáticamente."
    )
    with st.expander("Ver normativa disponible"):
        for archivo in archivos_almacenados:
            st.write(f"- {archivo.relative_to(carpeta_documentos)}")
else:
    st.warning(
        "La base normativa todavía no contiene documentos. Agrega legislación o "
        "políticas laborales para comenzar."
    )

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

col1, col2 = st.columns(2)
with col1:
    actualizar = st.button("Actualizar base normativa", use_container_width=True)
with col2:
    if st.button("Limpiar conversación", use_container_width=True):
        st.session_state.mensajes = []
        st.rerun()

firma_actual = (
    huella_configuracion(config),
    firma_documentos_base(archivos_almacenados, carpeta_documentos),
    firma_archivos_subidos(archivos),
)
hay_documentos = bool(archivos_almacenados or archivos)
requiere_carga = st.session_state.get("firma_indice") != firma_actual
fallo_esta_firma = st.session_state.get("firma_indice_fallida") == firma_actual

if actualizar:
    requiere_carga = True
    fallo_esta_firma = False

if hay_documentos and requiere_carga and not fallo_esta_firma:
    try:
        with st.spinner("Preparando la base normativa automáticamente..."):
            cargar_indice_automaticamente(
                config,
                carpeta_documentos,
                archivos_almacenados,
                archivos,
                firma_actual,
            )
    except Exception as error:
        st.session_state.firma_indice_fallida = firma_actual
        mostrar_error("No se pudo preparar la base normativa", error)

resumen = st.session_state.get("resumen_indice")
if resumen and st.session_state.get("firma_indice") == firma_actual:
    st.success(
        "✅ Base normativa lista: "
        f"{resumen['base']} almacenado(s), "
        f"{resumen['subidos']} subido(s) y "
        f"{resumen['fragmentos']} fragmentos indexados."
    )

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])
        if mensaje.get("fuentes"):
            with st.expander("Fuentes recuperadas"):
                for fuente in mensaje["fuentes"]:
                    pagina = f", página {fuente['pagina']}" if fuente.get("pagina") else ""
                    st.write(f"- {fuente['archivo']}{pagina}")

pregunta = st.chat_input(
    "Consulta sobre legislación o políticas laborales de Panamá"
)
if pregunta:
    if "servicio_rag" not in st.session_state:
        st.warning("Espera la carga automática o agrega documentos para comenzar.")
    elif st.session_state.get("firma_indice") != firma_actual:
        st.warning(
            "La base normativa todavía no está lista. Pulsa Actualizar base normativa."
        )
    elif st.session_state.get("huella_rag") != huella_configuracion(config):
        st.warning("Cambió el proveedor o el modelo. Actualiza la base normativa.")
    else:
        historial = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.mensajes
        ]
        st.session_state.mensajes.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)
        try:
            with st.chat_message("assistant"):
                with st.spinner("Consultando..."):
                    respuesta, fuentes = st.session_state.servicio_rag.preguntar(
                        pregunta,
                        historial=historial,
                        k=k,
                    )
                st.markdown(respuesta)
                with st.expander("Fuentes recuperadas"):
                    for fuente in fuentes:
                        pagina = f", página {fuente['pagina']}" if fuente.get("pagina") else ""
                        st.write(f"- {fuente['archivo']}{pagina}")
            st.session_state.mensajes.append(
                {"role": "assistant", "content": respuesta, "fuentes": fuentes}
            )
        except Exception as error:
            mostrar_error("No se pudo generar la respuesta", error)