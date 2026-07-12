# Agente RAG con LangChain

Aplicación web para consultar documentos mediante **Retrieval-Augmented Generation (RAG)**. Permite utilizar modelos locales con **LM Studio** o servicios externos mediante las API de **OpenAI** y **NVIDIA NIM**.

El usuario puede subir varios documentos, procesarlos y realizar preguntas sobre su contenido. La configuración técnica está protegida mediante un panel administrativo y no aparece en la interfaz pública.

## Características

- Carga múltiple de archivos PDF, DOCX, TXT y Markdown.
- Respuestas generadas únicamente con el contexto recuperado.
- Referencias al archivo y página utilizados.
- Compatibilidad con LM Studio, OpenAI y NVIDIA NIM.
- Cambio de proveedor desde un panel administrativo protegido.
- Claves, modelos y endpoints ocultos para los usuarios públicos.
- Contraseña administrativa almacenada mediante hash PBKDF2-SHA256.
- Configuración privada excluida automáticamente de Git.
- Interfaz web desarrollada con Streamlit.
- Contenedor Docker incluido.
- Código modular preparado para migrar a FastAPI y una base vectorial persistente.

## Tecnologías

| Tecnología | Función |
| --- | --- |
| Python 3.12 | Lenguaje principal recomendado |
| Streamlit | Interfaz web, carga de archivos y chat |
| LangChain | Orquestación del flujo RAG |
| LangChain OpenAI | Conexión con OpenAI y LM Studio |
| LangChain NVIDIA AI Endpoints | Conexión con NVIDIA NIM |
| InMemoryVectorStore | Almacenamiento vectorial de la versión inicial |
| PyPDF | Extracción de texto de archivos PDF |
| python-docx | Lectura de documentos Word |
| python-dotenv | Carga de variables privadas desde `.env` |
| PBKDF2-SHA256 | Protección de la contraseña administrativa |
| Docker | Empaquetado y despliegue de la aplicación |
| Pytest | Pruebas automatizadas |

## Diagrama de flujo

```mermaid
flowchart TD
    U["Usuario"] --> A["Interfaz Streamlit"]
    A --> B["Carga de documentos"]
    B --> C["Extracción de texto"]
    C --> D["División en fragmentos"]
    D --> E["Generación de embeddings"]
    E --> F["Índice vectorial en memoria"]

    U --> G["Pregunta"]
    G --> H["Búsqueda semántica"]
    F --> H
    H --> I["Contexto recuperado"]
    I --> J{"Proveedor configurado"}
    J --> K["LM Studio"]
    J --> L["OpenAI"]
    J --> M["NVIDIA NIM"]
    K --> N["Respuesta con fuentes"]
    L --> N
    M --> N
    N --> A
```

## Arquitectura del proyecto

```text
agente-rag/
├── app.py                         # Interfaz Streamlit y panel administrativo
├── generar_clave_admin.py         # Generador de hash para el administrador
├── src/
│   └── rag/
│       ├── __init__.py
│       ├── admin.py               # Autenticación y configuración privada
│       ├── config.py              # Validación de proveedores
│       ├── documents.py           # Lectura de PDF, DOCX, TXT y MD
│       ├── providers.py           # LM Studio, OpenAI y NVIDIA
│       └── service.py             # Indexación, recuperación y respuesta
├── tests/
│   └── test_documents.py
├── docs/
│   └── DECISIONES.md
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── .env.example
├── requirements.txt
├── pytest.ini
├── Dockerfile
└── README.md
```

## Requisitos

- Python 3.11 o 3.12.
- `pip` actualizado.
- LM Studio si se utilizarán modelos locales.
- Una clave de OpenAI o NVIDIA si se utilizarán sus respectivas API.

Se recomienda evitar Python 3.13 cuando alguna dependencia todavía no disponga de una versión compatible.

## Instalación

Clona el repositorio y entra en la carpeta:

```bash
git clone https://github.com/ijimenez08/agentes_rag.git
cd agentes_rag
```

Crea y activa un entorno virtual:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

En Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

Instala las dependencias:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Variables de entorno

Copia el archivo de ejemplo:

```bash
cp .env.example .env
```

En Windows:

```powershell
Copy-Item .env.example .env
```

Configura únicamente los proveedores que utilizarás:

```env
# Administración
ADMIN_USERNAME=tu_usuario
ADMIN_PASSWORD_HASH=tu_hash_pbkdf2

# Proveedor inicial: local, openai o nvidia
RAG_PROVIDER=local
RAG_CONFIG_PATH=.runtime/private_config.json

# LM Studio
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_CHAT_MODEL=identificador-del-modelo-chat
LM_STUDIO_EMBEDDING_MODEL=identificador-del-modelo-embeddings

# OpenAI
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# NVIDIA
NVIDIA_API_KEY=
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_CHAT_MODEL=nvidia/nemotron-3-ultra-550b-a55b
NVIDIA_EMBEDDING_MODEL=nvidia/nv-embedqa-e5-v5
```
## Crear o cambiar la contraseña administrativa

La contraseña no se guarda directamente. Genera su hash con:

```bash
python generar_clave_admin.py
```

El programa solicitará una contraseña con al menos 12 caracteres y devolverá:

```env
ADMIN_PASSWORD_HASH=pbkdf2_sha256$...
```

Copia la línea completa al archivo `.env` y reinicia la aplicación.

## Ejecución

```bash
python -m streamlit run app.py
```

La aplicación estará disponible normalmente en:

```text
http://localhost:8501
```

## Uso

### Usuario público

1. Sube uno o varios documentos.
2. Pulsa **Procesar archivos**.
3. Escribe una pregunta en el chat.
4. Revisa la respuesta y las fuentes recuperadas.

El usuario público no puede visualizar el proveedor, la clave API, los modelos ni las URLs internas.

### Administrador

1. Abre **🔒 Administración** en la barra lateral.
2. Inicia sesión.
3. Selecciona el proveedor activo.
4. Configura el modelo de chat, embeddings y URL base.
5. Escribe una nueva clave únicamente cuando quieras reemplazar la actual.
6. Pulsa **Guardar configuración**.
7. Procesa nuevamente los documentos.

Los cambios se guardan localmente en `.runtime/private_config.json` con permisos restringidos.

## Configuración de LM Studio

1. Descarga un modelo de chat.
2. Descarga un modelo de embeddings.
3. Entra en **Developer** y activa **Start Server**.
4. Carga ambos modelos.
5. Verifica la URL `http://localhost:1234/v1`.
6. Copia los identificadores exactos de los modelos al panel administrativo.

Puedes comprobar los modelos cargados con:

```bash
curl http://localhost:1234/v1/models
```

LM Studio expone endpoints compatibles con OpenAI, por lo que se utiliza `ChatOpenAI` y `OpenAIEmbeddings` cambiando la URL base.

## Configuración de OpenAI

1. Genera una clave en la plataforma de OpenAI.
2. Guárdala como `OPENAI_API_KEY` o introdúcela desde el panel administrativo.
3. Selecciona **API de pago · OpenAI**.
4. Guarda la configuración y procesa nuevamente los documentos.

El uso de esta opción puede generar cargos según el modelo y el volumen procesado.

## Configuración de NVIDIA NIM

1. Entra en [NVIDIA API Catalog](https://build.nvidia.com/).
2. Inicia sesión y abre **API Keys**.
3. Genera una clave; normalmente comienza con `nvapi-`.
4. Guárdala como `NVIDIA_API_KEY` o introdúcela desde el panel administrativo.
5. Copia el identificador exacto del modelo desde su página en el catálogo.

El proyecto utiliza las integraciones oficiales de LangChain [`ChatNVIDIA`](https://docs.langchain.com/oss/python/integrations/chat/nvidia_ai_endpoints) y [`NVIDIAEmbeddings`](https://docs.langchain.com/oss/python/integrations/embeddings/nvidia_ai_endpoints).

## Docker

Construye la imagen:

```bash
docker build -t agente-rag .
```

Ejecuta el contenedor:

```bash
docker run --rm -p 8501:8501 --env-file .env \
  -v "$(pwd)/.runtime:/app/.runtime" agente-rag
```

Para acceder desde Docker a LM Studio ejecutado en el equipo anfitrión:

```env
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
```

En Linux puede ser necesario agregar:

```bash
--add-host=host.docker.internal:host-gateway
```

## Pruebas

```bash
python -m pip install pytest
python -m pytest -q
```

## Seguridad

- Las claves no se incluyen en el código fuente.
- La contraseña administrativa se verifica mediante PBKDF2-SHA256.
- La interfaz pública no muestra datos técnicos de las API.
- Los errores detallados solo se presentan en sesiones administrativas.
- La configuración privada está excluida de Git.
- Los archivos deben validarse nuevamente antes de utilizar la aplicación en un entorno empresarial.
- Debe añadirse limitación de intentos, HTTPS y autenticación centralizada para una publicación de producción.

El archivo `.runtime/private_config.json` puede contener claves guardadas desde el panel. No debe copiarse al repositorio, compartirse ni incluirse en imágenes Docker.

## Limitaciones actuales

- El índice vectorial permanece en memoria.
- Los documentos deben procesarse nuevamente después de reiniciar la aplicación.
- Los PDF escaneados requieren OCR y no se procesan todavía.
- El almacenamiento local de configuración no se comparte entre varias réplicas.
- Streamlit Community Cloud no garantiza persistencia permanente del archivo `.runtime/private_config.json`.

## Escalamiento futuro

- Sustituir `InMemoryVectorStore` por PostgreSQL con pgvector o Qdrant.
- Guardar archivos en S3 o almacenamiento compatible.
- Separar el backend mediante FastAPI.
- Ejecutar la indexación mediante Celery, RQ o una cola administrada.
- Incorporar autenticación por usuario y separación por `tenant_id`.
- Guardar secretos en Vault, AWS Secrets Manager, Google Secret Manager o equivalente.
- Añadir métricas de latencia, costo y calidad de recuperación.
- Incorporar OCR para documentos escaneados.
- Agregar evaluación automática de respuestas y recuperación.

## Solución de problemas

### No se encuentra un módulo

Instala nuevamente las dependencias dentro del entorno virtual:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### NVIDIA no está instalado

```bash
python -m pip install langchain-nvidia-ai-endpoints
```

### LM Studio indica que no hay modelos cargados

Abre **Developer**, inicia el servidor y carga tanto el modelo de chat como el modelo de embeddings.

### El PDF no devuelve contenido

El archivo probablemente contiene imágenes escaneadas. Esta versión utiliza extracción de texto y todavía no incorpora OCR.

## Licencia

Antes de publicar el repositorio, agrega el archivo `LICENSE` con la licencia elegida. Para un proyecto abierto sencillo puede utilizarse MIT, siempre que las licencias y condiciones de uso de los modelos seleccionados sean compatibles.

## Autor

Proyecto desarrollado como base escalable para asistentes documentales con LangChain.


## Capturas y ejecucion

### Modo local 

<img width="1920" height="1080" alt="Captura desde 2026-07-12 15-03-52" src="https://github.com/user-attachments/assets/c3684352-16bd-4ea9-b4be-458e0021a523" />

<img width="1920" height="1080" alt="Captura desde 2026-07-12 15-03-58" src="https://github.com/user-attachments/assets/8b50583c-c8cd-49d8-ab06-48570570e803" />

<img width="1920" height="1080" alt="Captura desde 2026-07-12 15-04-27" src="https://github.com/user-attachments/assets/ac4abb61-4712-445b-a107-bc7f3ed35f73" />

<img width="1920" height="1080" alt="Captura desde 2026-07-12 15-06-07" src="https://github.com/user-attachments/assets/6e3de7f5-4d2c-4017-94a9-57d44d8cc52a" />

<img width="1920" height="1080" alt="Captura desde 2026-07-12 15-06-14" src="https://github.com/user-attachments/assets/37b0b783-1dc0-4286-9a8a-67009d01dfcc" />

### Modo Web con streamlit

https://agentesrag-prxhhkx3gwyzzhy6hzmp4h.streamlit.app

## comentarios

por seguridad la api de nvidia no esta disponible, te recomiendo que accedas al panel de configuracion para que puedas colocar la api directamente.

para acceder en la web te dejo el usuario que es "admin_rag" y pass "abc123456789", sin tu llave api no funciona el modelo, puedes ejecutarlo en local.



