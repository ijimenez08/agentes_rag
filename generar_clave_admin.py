"""Genera el hash de una nueva contraseña administrativa."""

from getpass import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from rag.admin import crear_hash  # noqa: E402


clave = getpass("Nueva contraseña administrativa: ")
confirmacion = getpass("Repite la contraseña: ")

if len(clave) < 12:
    raise SystemExit("La contraseña debe tener al menos 12 caracteres.")
if clave != confirmacion:
    raise SystemExit("Las contraseñas no coinciden.")

print("\nCopia esta línea en tu archivo .env:\n")
print(f"ADMIN_PASSWORD_HASH={crear_hash(clave)}")