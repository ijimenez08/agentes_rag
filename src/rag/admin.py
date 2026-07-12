"""Autenticación administrativa y configuración privada persistente."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path


def verificar_clave(clave: str, hash_guardado: str) -> bool:
    """Verifica un hash PBKDF2-SHA256 sin guardar la contraseña en texto plano."""
    try:
        algoritmo, iteraciones, salt_b64, digest_b64 = hash_guardado.split("$", 3)
        if algoritmo != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        esperado = base64.urlsafe_b64decode(digest_b64.encode())
        calculado = hashlib.pbkdf2_hmac(
            "sha256", clave.encode(), salt, int(iteraciones)
        )
        return hmac.compare_digest(calculado, esperado)
    except (ValueError, TypeError):
        return False


def crear_hash(clave: str, iteraciones: int = 390_000) -> str:
    """Genera un hash para cambiar la contraseña administrativa."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", clave.encode(), salt, iteraciones)
    return "$".join(
        [
            "pbkdf2_sha256",
            str(iteraciones),
            base64.urlsafe_b64encode(salt).decode(),
            base64.urlsafe_b64encode(digest).decode(),
        ]
    )


def cargar_configuracion_privada(ruta: Path) -> dict:
    if not ruta.exists():
        return {}
    try:
        contenido = json.loads(ruta.read_text(encoding="utf-8"))
        return contenido if isinstance(contenido, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def guardar_configuracion_privada(ruta: Path, configuracion: dict) -> None:
    """Guarda la configuración fuera del repositorio y limita sus permisos."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(".tmp")
    temporal.write_text(
        json.dumps(configuracion, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    try:
        temporal.chmod(0o600)
    except OSError:
        pass
    temporal.replace(ruta)
