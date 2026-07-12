"""Interfaz Streamlit del asistente RAG."""

from __future__ import annotations

import os
import sys
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
from rag.documents import leer_archivos  # noqa: E402


load_dotenv()
st.set_page_config(page_title="Agente RAG", page_icon="📚", layout="centered")


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


st.title("📚 Agente RAG de Recursos Humanos")
st.caption("Consulta tus propios documentos con una configuración privada y segura.")

ajustes = ajustes_iniciales()
panel_administracion(ajustes)
config = construir_configuracion(ajustes)
archivos = st.file_uploader(
    "Sube uno o varios archivos",
    type=["pdf", "docx", "txt", "md"],
    accept_multiple_files=True,
)
k = 4

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

col1, col2 = st.columns(2)
with col1:
    procesar = st.button("Procesar archivos", type="primary", use_container_width=True)
with col2:
    if st.button("Limpiar conversación", use_container_width=True):
        st.session_state.mensajes = []
        st.rerun()

if procesar:
    if not archivos:
        st.warning("Sube al menos un archivo.")
    else:
        try:
            with st.spinner("Leyendo e indexando documentos..."):
                documentos = leer_archivos(archivos)
                servicio = ServicioRAG(config)
                cantidad = servicio.indexar(documentos)
                st.session_state.servicio_rag = servicio
                st.session_state.huella_rag = huella_configuracion(config)
                st.session_state.mensajes = []
            st.success(f"Listo: {len(archivos)} archivo(s) y {cantidad} fragmentos indexados.")
        except Exception as error:
            mostrar_error("No se pudieron procesar los archivos", error)

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])
        if mensaje.get("fuentes"):
            with st.expander("Fuentes recuperadas"):
                for fuente in mensaje["fuentes"]:
                    pagina = f", página {fuente['pagina']}" if fuente.get("pagina") else ""
                    st.write(f"- {fuente['archivo']}{pagina}")

pregunta = st.chat_input("Pregunta sobre los documentos")
if pregunta:
    if "servicio_rag" not in st.session_state:
        st.warning("Primero sube y procesa los archivos.")
    elif st.session_state.get("huella_rag") != huella_configuracion(config):
        st.warning("Cambió el proveedor o el modelo. Pulsa Procesar archivos otra vez.")
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