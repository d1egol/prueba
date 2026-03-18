"""
Mi Agente IA — Bot de Telegram
Arquitectura de 4 Pilares:
  1. Modelos de Lenguaje  — multi-model (sonnet / opus / haiku)
  2. Herramientas autónomas — tool registry con dispatcher contextual
  3. Memoria persistente   — hechos / preferencias / notas por usuario
  4. Habilidades transferibles — skill registry compartido entre agentes

Mejoras adicionales (awesome-claude-code / claude-skills patterns):
  - Personas especializadas (investigador / programador / analista / escritor)
  - Auto-activación de habilidades por palabras clave
  - Rate limiting por usuario
  - Detección de prompt injection
  - Skills con system_prompt propio
"""

import os, sys, json, logging, base64, asyncio, subprocess, threading, re, time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from dotenv import load_dotenv

import httpx
import anthropic
from telegram import Bot, Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from duckduckgo_search import DDGS
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()

# ─── Configuración ─────────────────────────────────────────────────────────────

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY")
ALLOWED_USERS  = [u.strip() for u in os.getenv("ALLOWED_USERS", "").split(",") if u.strip()]
OWNER_ID       = int(ALLOWED_USERS[0]) if ALLOWED_USERS else None
WORKSPACE      = Path(os.getenv("WORKSPACE", "/app/workspace"))
WORKSPACE.mkdir(parents=True, exist_ok=True)
BOT_FILE       = Path(__file__).resolve()
WEB_PORT       = int(os.getenv("WEB_PORT", "8080"))

MEMORY_DIR = WORKSPACE / "memory"
SKILLS_DIR = WORKSPACE / "skills"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

# ── Configuración de email ──────────────────────────────────────────────────
# Configura estas variables en .env para habilitar el reporte por email.
# SMTP_HOST     — servidor SMTP (ej: smtp.gmail.com)
# SMTP_PORT     — puerto (587 para TLS)
# SMTP_USER     — tu cuenta de correo emisor
# SMTP_PASS     — contraseña o app password
# REPORT_EMAIL  — email destino del reporte diario

SMTP_HOST    = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT    = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER    = os.getenv("SMTP_USER", "")
SMTP_PASS    = os.getenv("SMTP_PASS", "")
REPORT_EMAIL = os.getenv("REPORT_EMAIL", "dilopezd91@gmail.com")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Pilar 1: Modelos de Lenguaje ──────────────────────────────────────────────

MODEL_REGISTRY: dict[str, str] = {
    "sonnet": "claude-sonnet-4-6",
    "opus":   "claude-opus-4-6",
    "haiku":  "claude-haiku-4-5-20251001",
}
DEFAULT_MODEL = "claude-sonnet-4-6"

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)
user_models: dict[int, str] = {}

def get_user_model(user_id: int) -> str:
    return user_models.get(user_id, DEFAULT_MODEL)


# ─── Personas especializadas ───────────────────────────────────────────────────
# Cada persona tiene su propio system prompt base y estilo de comunicación.

PERSONAS: dict[str, dict] = {
    "asistente": {
        "description": "Asistente general equilibrado (default)",
        "prompt": (
            "Eres un asistente IA general, equilibrado y útil. "
            "Adaptas tu nivel de detalle a la complejidad de la pregunta. "
            "Eres conciso en Telegram pero exhaustivo cuando es necesario."
        ),
    },
    "programador": {
        "description": "Experto en desarrollo de software",
        "prompt": (
            "Eres un programador experto con 15 años de experiencia. "
            "Al revisar código: identifica bugs, problemas de rendimiento y seguridad. "
            "Formatea el código con bloques de código. "
            "Explica el PORQUÉ de cada problema, no solo el CÓMO solucionarlo. "
            "Sugiere refactorizaciones y patrones cuando sea apropiado."
        ),
    },
    "investigador": {
        "description": "Investigador profundo, cita fuentes, análisis exhaustivo",
        "prompt": (
            "Eres un investigador experto. Cuando abordes una pregunta: "
            "1) Busca información actualizada antes de responder. "
            "2) Cita fuentes específicas con URLs. "
            "3) Distingue entre hechos verificados y especulaciones. "
            "4) Presenta múltiples perspectivas cuando existan. "
            "5) Sintetiza la información de forma clara y estructurada."
        ),
    },
    "analista": {
        "description": "Analista de datos y sistemas, orientado a métricas",
        "prompt": (
            "Eres un analista de datos y sistemas experto. "
            "Piensas en términos de métricas, tendencias y causas raíz. "
            "Cuando analices un problema: identifica patrones, cuantifica impactos, "
            "sugiere experimentos para validar hipótesis. "
            "Usa Python para análisis cuando sea útil."
        ),
    },
    "escritor": {
        "description": "Escritor y comunicador experto",
        "prompt": (
            "Eres un escritor y comunicador experto. "
            "Ayudas a redactar, mejorar y estructurar textos. "
            "Adaptas el tono al contexto (formal/informal, técnico/divulgativo). "
            "Corriges gramática, estilo y claridad. "
            "Propones alternativas creativas cuando hay bloqueo."
        ),
    },
    "arquitecto": {
        "description": "Arquitecto de sistemas y software",
        "prompt": (
            "Eres un arquitecto de sistemas con amplia experiencia. "
            "Al evaluar diseños: analiza escalabilidad, fiabilidad, seguridad y coste. "
            "Identifica puntos únicos de fallo, cuellos de botella y deuda técnica. "
            "Proporciona trade-offs claros para cada decisión arquitectónica. "
            "Usa diagramas ASCII cuando ayuden a ilustrar conceptos."
        ),
    },
}
DEFAULT_PERSONA = "asistente"

user_personas: dict[int, str] = {}

def get_user_persona(user_id: int) -> str:
    return user_personas.get(user_id, DEFAULT_PERSONA)


# ─── Auto-activación de habilidades ────────────────────────────────────────────
# Si el mensaje del usuario contiene estas palabras clave, se sugieren skills.

SKILL_TRIGGERS: dict[str, list[str]] = {
    "código|bug|debug|error|refactor|programar|función|clase|script": "programador",
    "invest|buscar|investigar|documentar|fuente|artículo|paper": "investigador",
    "analiz|datos|métrica|estadística|csv|gráfico|tendencia": "analista",
    "redact|escribir|texto|artículo|correo|mensaje|mejorar": "escritor",
    "arquitectura|diseño|sistema|escalar|microservic|base de datos": "arquitecto",
}

def detect_suggested_persona(text: str) -> str | None:
    """Sugiere una persona basada en palabras clave del mensaje."""
    text_lower = text.lower()
    for pattern, persona in SKILL_TRIGGERS.items():
        if re.search(pattern, text_lower):
            return persona
    return None


# ─── Seguridad: Rate limiting & Prompt injection ───────────────────────────────

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT", "30"))   # por hora
RATE_LIMIT_WINDOW   = 3600  # segundos

user_request_log: dict[int, list[float]] = {}

def check_rate_limit(user_id: int) -> tuple[bool, str]:
    now = time.time()
    log = user_request_log.setdefault(user_id, [])
    # Limpiar timestamps fuera de la ventana
    user_request_log[user_id] = [t for t in log if now - t < RATE_LIMIT_WINDOW]
    if len(user_request_log[user_id]) >= RATE_LIMIT_REQUESTS:
        wait = int(RATE_LIMIT_WINDOW - (now - user_request_log[user_id][0]))
        return False, f"⏳ Límite de {RATE_LIMIT_REQUESTS} mensajes/hora alcanzado. Espera {wait//60}m {wait%60}s."
    user_request_log[user_id].append(now)
    return True, ""

INJECTION_PATTERNS = [
    r"ignore (previous|all|your) instructions",
    r"disregard (previous|all|your)",
    r"system prompt (is|contains|says)",
    r"forget (about|everything|your instructions)",
    r"new (role|persona|instructions):\s*(you are|act as)",
    r"pretend (you are|to be) (a|an) (?!helpful)",
    r"jailbreak",
    r"DAN mode",
]

def detect_prompt_injection(text: str) -> bool:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# ─── Pilar 3: Memoria Persistente ──────────────────────────────────────────────

def _memory_path(user_id: int) -> Path:
    return MEMORY_DIR / f"{user_id}.json"

def load_memory(user_id: int) -> dict:
    path = _memory_path(user_id)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"facts": [], "preferences": {}, "notes": [], "updated": ""}

def _persist_memory(user_id: int, data: dict) -> None:
    data["updated"] = datetime.now().isoformat()
    _memory_path(user_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

def memory_context(user_id: int) -> str:
    mem = load_memory(user_id)
    parts = []
    if mem["facts"]:
        parts.append("Hechos del usuario:\n" + "\n".join(f"- {f}" for f in mem["facts"]))
    if mem["preferences"]:
        prefs = ", ".join(f"{k}={v}" for k, v in mem["preferences"].items())
        parts.append(f"Preferencias: {prefs}")
    if mem["notes"]:
        parts.append("Notas:\n" + "\n".join(f"- {n}" for n in mem["notes"][-10:]))
    return "\n".join(parts)


# ─── Pilar 4: Habilidades Transferibles ────────────────────────────────────────

def _skill_path(name: str) -> Path:
    safe = re.sub(r"[^a-z0-9_\-]", "_", name.lower())
    return SKILLS_DIR / f"{safe}.json"

def load_skill(name: str) -> dict | None:
    path = _skill_path(name)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None

def all_skills() -> list[dict]:
    skills = []
    for p in sorted(SKILLS_DIR.glob("*.json")):
        try:
            skills.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return skills

def skills_context() -> str:
    skills = all_skills()
    if not skills:
        return ""
    lines = ["Habilidades guardadas (usa run_skill para ejecutarlas):"]
    for s in skills:
        tags = f" [{', '.join(s['tags'])}]" if s.get("tags") else ""
        lines.append(f"- {s['name']}{tags}: {s['description']}")
    return "\n".join(lines)


# ─── Servidor web ───────────────────────────────────────────────────────────────

class WorkspaceHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WORKSPACE), **kwargs)
    def log_message(self, format, *args):
        pass

def start_web_server():
    server = HTTPServer(("0.0.0.0", WEB_PORT), WorkspaceHandler)
    logger.info(f"🌐 Servidor web iniciado en :{WEB_PORT} → sirve {WORKSPACE}")
    server.serve_forever()


# ─── System Prompt dinámico ─────────────────────────────────────────────────────

BASE_CAPABILITIES = """
Pilares de capacidad:
1. MODELOS: sonnet (default) · opus (complejo) · haiku (rápido) — usa switch_model según tarea
2. HERRAMIENTAS: web_search, fetch_url, run_python, archivos, send_message, auto-mejora
3. MEMORIA: save_memory / recall_memory / clear_memory — persiste entre sesiones
4. HABILIDADES: save_skill / list_skills / run_skill / delete_skill — compartidas entre agentes

Reglas operativas:
- Al conocer datos relevantes del usuario, guárdalos con save_memory
- Antes de tarea compleja, verifica habilidades disponibles con list_skills
- Usa opus para razonamiento profundo; haiku para tareas simples
- Responde en el idioma del usuario (español por defecto)
- Mensajes concisos — estás en Telegram (límite 4096 chars por mensaje)
- Workspace: {workspace} → accesible en :{port}"""

def build_system_prompt(user_id: int, suggested_persona: str | None = None) -> str:
    # Persona activa (la guardada, la sugerida, o la default)
    persona_key = get_user_persona(user_id)
    if suggested_persona and suggested_persona in PERSONAS:
        # Solo sugerir, no cambiar permanentemente
        persona_key = suggested_persona

    persona = PERSONAS.get(persona_key, PERSONAS[DEFAULT_PERSONA])
    parts = [persona["prompt"]]
    parts.append(BASE_CAPABILITIES.format(workspace=WORKSPACE, port=WEB_PORT))

    mem_ctx = memory_context(user_id)
    if mem_ctx:
        parts.append(f"--- MEMORIA DEL USUARIO ---\n{mem_ctx}")

    sk_ctx = skills_context()
    if sk_ctx:
        parts.append(f"--- HABILIDADES DISPONIBLES ---\n{sk_ctx}")

    model_alias = next(
        (k for k, v in MODEL_REGISTRY.items() if v == get_user_model(user_id)), "sonnet"
    )
    parts.append(f"Modelo activo: {model_alias} | Persona: {persona_key}")

    return "\n\n".join(parts)


# ─── Definición de herramientas ────────────────────────────────────────────────

TOOLS = [
    # ── Pilar 2: Herramientas de conexión ──
    {
        "name": "web_search",
        "description": "Busca información actualizada en internet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_url",
        "description": "Descarga y lee el contenido de una URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "max_chars": {"type": "integer", "default": 6000},
            },
            "required": ["url"],
        },
    },
    {
        "name": "run_python",
        "description": "Ejecuta código Python en el servidor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["code"],
        },
    },
    {
        "name": "read_file",
        "description": "Lee un archivo del workspace.",
        "input_schema": {
            "type": "object",
            "properties": {"filename": {"type": "string"}},
            "required": ["filename"],
        },
    },
    {
        "name": "write_file",
        "description": "Crea o sobreescribe un archivo en el workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "list_files",
        "description": "Lista todos los archivos del workspace.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "send_message",
        "description": "Envía un mensaje proactivo de Telegram a un usuario.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "text": {"type": "string"},
            },
            "required": ["user_id", "text"],
        },
    },
    {
        "name": "read_own_code",
        "description": "Lee el código fuente del bot. Siempre hazlo antes de update_own_code.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "update_own_code",
        "description": "Reemplaza el código fuente completo y reinicia el bot.",
        "input_schema": {
            "type": "object",
            "properties": {
                "new_code": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["new_code", "reason"],
        },
    },
    # ── Pilar 1: Modelos ──
    {
        "name": "switch_model",
        "description": "Cambia el modelo Claude activo: sonnet (default), opus (potente), haiku (rápido).",
        "input_schema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "enum": ["sonnet", "opus", "haiku"]},
                "reason": {"type": "string"},
            },
            "required": ["model"],
        },
    },
    # ── Personas ──
    {
        "name": "switch_persona",
        "description": (
            "Cambia la persona activa del agente. "
            "Personas: asistente, programador, investigador, analista, escritor, arquitecto."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "persona": {
                    "type": "string",
                    "enum": list(PERSONAS.keys()),
                },
                "reason": {"type": "string"},
            },
            "required": ["persona"],
        },
    },
    # ── Pilar 3: Memoria ──
    {
        "name": "save_memory",
        "description": "Guarda información persistente del usuario (fact/preference/note).",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["fact", "preference", "note"],
                    "description": "fact=dato biográfico, preference=clave=valor, note=nota libre",
                },
                "content": {"type": "string"},
            },
            "required": ["type", "content"],
        },
    },
    {
        "name": "recall_memory",
        "description": "Busca en la memoria persistente del usuario.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "clear_memory",
        "description": "Borra toda la memoria del usuario. Solo si lo pide explícitamente.",
        "input_schema": {"type": "object", "properties": {}},
    },
    # ── Pilar 4: Habilidades ──
    {
        "name": "save_skill",
        "description": (
            "Guarda una habilidad reutilizable compartida entre agentes y sesiones. "
            "Puede incluir un system_prompt propio para especialización."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nombre único en snake_case"},
                "description": {"type": "string", "description": "Qué hace (1 línea)"},
                "prompt": {"type": "string", "description": "Instrucción detallada paso a paso"},
                "system_prompt": {
                    "type": "string",
                    "description": "System prompt especializado para esta habilidad (opcional)",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Etiquetas para categorizar",
                },
            },
            "required": ["name", "description", "prompt"],
        },
    },
    {
        "name": "list_skills",
        "description": "Lista todas las habilidades guardadas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tag": {"type": "string", "description": "Filtrar por etiqueta (opcional)"},
            },
        },
    },
    {
        "name": "run_skill",
        "description": "Ejecuta una habilidad guardada con contexto opcional.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "args": {"type": "string", "description": "Contexto o argumentos"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "delete_skill",
        "description": "Elimina una habilidad del registro.",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
]


# ─── Implementaciones ──────────────────────────────────────────────────────────

def run_web_search(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "Sin resultados."
        return "\n\n---\n\n".join(
            f"📌 {r['title']}\n{r['body']}\n🔗 {r['href']}" for r in results
        )
    except Exception as e:
        return f"Error en búsqueda: {e}"


def run_fetch_url(url: str, max_chars: int = 6000) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AgentBot/1.0)"}
        with httpx.Client(timeout=15, follow_redirects=True) as c:
            r = c.get(url, headers=headers)
            r.raise_for_status()
            text = r.text
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s{3,}", "\n\n", text).strip()
            return text[:max_chars] + ("\n[...truncado]" if len(text) > max_chars else "")
    except Exception as e:
        return f"Error: {e}"


def run_python_code(code: str, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout, cwd=str(WORKSPACE),
        )
        out = ""
        if result.stdout: out += f"stdout:\n{result.stdout}"
        if result.stderr: out += f"\nstderr:\n{result.stderr}"
        return out[:4000] or "(Sin salida)"
    except subprocess.TimeoutExpired:
        return f"❌ Timeout ({timeout}s)."
    except Exception as e:
        return f"❌ {e}"


def run_read_file(filename: str) -> str:
    try:
        path = (WORKSPACE / filename).resolve()
        if not str(path).startswith(str(WORKSPACE)):
            return "❌ Acceso denegado."
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"❌ '{filename}' no encontrado."
    except Exception as e:
        return f"❌ {e}"


def run_write_file(filename: str, content: str) -> str:
    try:
        path = (WORKSPACE / filename).resolve()
        if not str(path).startswith(str(WORKSPACE)):
            return "❌ Acceso denegado."
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"✅ '{filename}' guardado ({len(content)} chars)."
    except Exception as e:
        return f"❌ {e}"


def run_list_files() -> str:
    try:
        files = [
            f for f in sorted(WORKSPACE.rglob("*"))
            if f.is_file()
            and not str(f).startswith(str(MEMORY_DIR))
            and not str(f).startswith(str(SKILLS_DIR))
        ]
        if not files:
            return "Workspace vacío."
        return "\n".join(f"📄 {f.relative_to(WORKSPACE)} ({f.stat().st_size}b)" for f in files)
    except Exception as e:
        return f"❌ {e}"


async def run_send_message(user_id: int, text: str) -> str:
    if not _telegram_bot:
        return "❌ Bot no listo."
    try:
        await _telegram_bot.send_message(chat_id=user_id, text=text)
        return f"✅ Enviado a {user_id}."
    except Exception as e:
        return f"❌ {e}"


def run_read_own_code() -> str:
    try:
        return BOT_FILE.read_text(encoding="utf-8")
    except Exception as e:
        return f"❌ {e}"


def run_update_own_code(new_code: str, reason: str) -> str:
    try:
        backup = BOT_FILE.with_suffix(".backup.py")
        backup.write_text(BOT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        BOT_FILE.write_text(new_code, encoding="utf-8")
        logger.info(f"🔄 Código actualizado: {reason}")
        def restart():
            import time; time.sleep(3)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        threading.Thread(target=restart, daemon=True).start()
        return f"✅ Actualizado: {reason}\n♻️ Reiniciando en 3s..."
    except Exception as e:
        return f"❌ {e}"


# ── Pilar 1: Modelos ──────────────────────────────────────────────────────────

def run_switch_model(user_id: int, model_alias: str, reason: str = "") -> str:
    model_id = MODEL_REGISTRY.get(model_alias)
    if not model_id:
        return f"❌ Modelo '{model_alias}' no existe. Opciones: {', '.join(MODEL_REGISTRY)}"
    user_models[user_id] = model_id
    mem = load_memory(user_id)
    mem["preferences"]["model"] = model_alias
    _persist_memory(user_id, mem)
    return f"✅ Modelo → **{model_alias}** ({model_id})" + (f" — {reason}" if reason else "")


# ── Personas ──────────────────────────────────────────────────────────────────

def run_switch_persona(user_id: int, persona_key: str, reason: str = "") -> str:
    if persona_key not in PERSONAS:
        opts = ", ".join(PERSONAS.keys())
        return f"❌ Persona '{persona_key}' no existe. Opciones: {opts}"
    user_personas[user_id] = persona_key
    mem = load_memory(user_id)
    mem["preferences"]["persona"] = persona_key
    _persist_memory(user_id, mem)
    desc = PERSONAS[persona_key]["description"]
    return f"✅ Persona → **{persona_key}** ({desc})" + (f" — {reason}" if reason else "")


# ── Pilar 3: Memoria ──────────────────────────────────────────────────────────

def run_save_memory(user_id: int, mem_type: str, content: str) -> str:
    mem = load_memory(user_id)
    if mem_type == "fact":
        if content not in mem["facts"]:
            mem["facts"].append(content)
    elif mem_type == "preference":
        if "=" not in content:
            return "❌ Las preferencias deben ser 'clave=valor'."
        k, v = content.split("=", 1)
        mem["preferences"][k.strip()] = v.strip()
    elif mem_type == "note":
        mem["notes"].append(f"[{datetime.now().strftime('%Y-%m-%d')}] {content}")
    _persist_memory(user_id, mem)
    return f"✅ Memoria guardada ({mem_type}): {content[:80]}"


def run_recall_memory(user_id: int, query: str) -> str:
    mem = load_memory(user_id)
    q = query.lower()
    results = []
    for f in mem["facts"]:
        if q in f.lower(): results.append(f"fact: {f}")
    for k, v in mem["preferences"].items():
        if q in k.lower() or q in v.lower(): results.append(f"pref: {k}={v}")
    for n in mem["notes"]:
        if q in n.lower(): results.append(f"note: {n}")
    return "\n".join(results) if results else f"Sin resultados para '{query}'."


def run_clear_memory(user_id: int) -> str:
    _memory_path(user_id).unlink(missing_ok=True)
    user_models.pop(user_id, None)
    user_personas.pop(user_id, None)
    return "✅ Memoria borrada."


# ── Pilar 4: Habilidades ─────────────────────────────────────────────────────

def run_save_skill(name: str, description: str, prompt: str,
                   system_prompt: str | None = None,
                   tags: list[str] | None = None,
                   author_id: int = 0) -> str:
    data = {
        "name": name,
        "description": description,
        "prompt": prompt,
        "system_prompt": system_prompt or "",   # system prompt propio opcional
        "tags": tags or [],
        "author": author_id,
        "created": datetime.now().isoformat(),
    }
    _skill_path(name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return f"✅ Habilidad '{name}' guardada."


def run_list_skills(tag: str | None = None) -> str:
    skills = all_skills()
    if tag:
        skills = [s for s in skills if tag in s.get("tags", [])]
    if not skills:
        return "No hay habilidades guardadas aún."
    lines = [f"📚 {len(skills)} habilidad(es):"]
    for s in skills:
        tags_str = f" [{', '.join(s['tags'])}]" if s.get("tags") else ""
        has_sp = " 🎭" if s.get("system_prompt") else ""
        lines.append(f"• **{s['name']}**{tags_str}{has_sp}: {s['description']}")
    return "\n".join(lines)


def run_delete_skill(name: str) -> str:
    path = _skill_path(name)
    if path.exists():
        path.unlink()
        return f"✅ Habilidad '{name}' eliminada."
    return f"❌ Habilidad '{name}' no encontrada."


def run_get_skill_prompt(name: str, args: str = "") -> str:
    """Devuelve el prompt de la habilidad (+ system_prompt si tiene) para que el LLM lo ejecute."""
    skill = load_skill(name)
    if not skill:
        available = ", ".join(s["name"] for s in all_skills()) or "ninguna"
        return f"❌ Habilidad '{name}' no encontrada. Disponibles: {available}"
    parts = [f"[Habilidad: {skill['name']}] {skill['description']}"]
    if skill.get("system_prompt"):
        parts.append(f"Contexto especializado:\n{skill['system_prompt']}")
    parts.append(f"Instrucciones:\n{skill['prompt']}")
    if args:
        parts.append(f"Contexto de esta ejecución: {args}")
    return "\n\n".join(parts)


# ─── Dispatcher ────────────────────────────────────────────────────────────────

async def dispatch_tool(name: str, inputs: dict, user_id: int) -> str:
    if name == "web_search":
        return run_web_search(inputs["query"], inputs.get("max_results", 5))
    elif name == "fetch_url":
        return run_fetch_url(inputs["url"], inputs.get("max_chars", 6000))
    elif name == "run_python":
        return run_python_code(inputs["code"], inputs.get("timeout", 30))
    elif name == "read_file":
        return run_read_file(inputs["filename"])
    elif name == "write_file":
        return run_write_file(inputs["filename"], inputs["content"])
    elif name == "list_files":
        return run_list_files()
    elif name == "send_message":
        return await run_send_message(inputs["user_id"], inputs["text"])
    elif name == "read_own_code":
        return run_read_own_code()
    elif name == "update_own_code":
        return run_update_own_code(inputs["new_code"], inputs["reason"])
    elif name == "switch_model":
        return run_switch_model(user_id, inputs["model"], inputs.get("reason", ""))
    elif name == "switch_persona":
        return run_switch_persona(user_id, inputs["persona"], inputs.get("reason", ""))
    elif name == "save_memory":
        return run_save_memory(user_id, inputs["type"], inputs["content"])
    elif name == "recall_memory":
        return run_recall_memory(user_id, inputs["query"])
    elif name == "clear_memory":
        return run_clear_memory(user_id)
    elif name == "save_skill":
        return run_save_skill(
            inputs["name"], inputs["description"], inputs["prompt"],
            inputs.get("system_prompt"), inputs.get("tags"), user_id,
        )
    elif name == "list_skills":
        return run_list_skills(inputs.get("tag"))
    elif name == "run_skill":
        return run_get_skill_prompt(inputs["name"], inputs.get("args", ""))
    elif name == "delete_skill":
        return run_delete_skill(inputs["name"])
    return f"Herramienta '{name}' no disponible."


# ─── Estado de sesiones ────────────────────────────────────────────────────────

conversations: dict[int, list] = {}
_telegram_bot: Bot | None = None


# ─── Loop agéntico ─────────────────────────────────────────────────────────────

async def run_agent(user_id: int, text: str, image_bytes: bytes | None = None) -> str:
    # Nueva sesión: restaurar modelo y persona desde memoria
    if user_id not in conversations:
        conversations[user_id] = []
        mem = load_memory(user_id)
        prefs = mem.get("preferences", {})
        if prefs.get("model") in MODEL_REGISTRY:
            user_models[user_id] = MODEL_REGISTRY[prefs["model"]]
        if prefs.get("persona") in PERSONAS:
            user_personas[user_id] = prefs["persona"]

    # Auto-detección de persona sugerida por el mensaje
    suggested_persona = detect_suggested_persona(text) if text else None

    if image_bytes:
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(image_bytes).decode(),
                },
            },
            {"type": "text", "text": text or "¿Qué ves en esta imagen?"},
        ]
    else:
        content = text

    conversations[user_id].append({"role": "user", "content": content})

    for _ in range(15):
        response = await client.messages.create(
            model=get_user_model(user_id),
            max_tokens=8096,
            system=build_system_prompt(user_id, suggested_persona),
            tools=TOOLS,
            messages=conversations[user_id],
        )

        conversations[user_id].append({
            "role": "assistant",
            "content": response.content,
        })

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "(Sin respuesta)"

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"🔧 [{user_id}] {block.name} | {str(block.input)[:120]}")
                    result = await dispatch_tool(block.name, block.input, user_id)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            conversations[user_id].append({
                "role": "user",
                "content": tool_results,
            })
        else:
            break

    return "Límite de pasos alcanzado. Usa /clear para reiniciar."


# ─── Scheduler: tendencias cada 6h ────────────────────────────────────────────

async def send_trend_update():
    if not OWNER_ID or not _telegram_bot:
        return
    try:
        results = run_web_search("Claude Anthropic AI novedades actualizaciones", max_results=4)
        msg = "🤖 *Tendencias AI:*\n\n" + results[:3000]
        await _telegram_bot.send_message(
            chat_id=OWNER_ID, text=msg[:4096], parse_mode="Markdown",
        )
        logger.info("📬 Tendencias enviadas.")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")


# ─── Subagente diario: análisis y revisión del sistema ─────────────────────────
# Corre una vez al día. Usa Claude con herramientas para auditar el estado
# del agente: habilidades, memorias, workspace, código y uso reciente.
# Genera un reporte y lo envía al owner por Telegram.

def _generate_pdf_report(text: str, output_path: Path, date_str: str) -> bool:
    """Genera un PDF con el reporte usando reportlab. Retorna True si tuvo éxito."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_LEFT

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "Title", parent=styles["Heading1"], fontSize=16, spaceAfter=12,
        )
        body_style = ParagraphStyle(
            "Body", parent=styles["Normal"], fontSize=10, leading=14,
            alignment=TA_LEFT,
        )

        story = []
        story.append(Paragraph(f"Reporte Diario del Agente IA — {date_str}", title_style))
        story.append(Spacer(1, 0.5 * cm))

        # Procesar líneas del reporte
        for line in text.split("\n"):
            clean = re.sub(r"[*_`]", "", line).strip()
            if not clean:
                story.append(Spacer(1, 0.2 * cm))
            else:
                story.append(Paragraph(clean, body_style))

        doc.build(story)
        return True
    except ImportError:
        logger.warning("reportlab no instalado. Ejecuta: pip install reportlab")
        return False
    except Exception as e:
        logger.error(f"Error generando PDF: {e}")
        return False


def _send_email_report(pdf_path: Path, date_str: str) -> tuple[bool, str]:
    """Envía el reporte PDF por email. Retorna (éxito, mensaje)."""
    try:
        msg = MIMEMultipart()
        msg["From"]    = SMTP_USER
        msg["To"]      = REPORT_EMAIL
        msg["Subject"] = f"Reporte Diario Agente IA — {date_str}"

        body = (
            f"Hola,\n\n"
            f"Adjunto encontrarás el reporte diario del agente IA correspondiente al {date_str}.\n\n"
            f"El reporte incluye:\n"
            f"- Estado de habilidades y memoria\n"
            f"- Archivos en workspace\n"
            f"- Análisis del código\n"
            f"- Recomendaciones de mejora\n"
            f"- Puntuación de salud del sistema\n\n"
            f"Saludos,\nAgente IA"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Adjuntar PDF
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="reporte_{date_str}.pdf"',
            )
            msg.attach(part)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, REPORT_EMAIL, msg.as_string())

        return True, f"✅ Reporte enviado a {REPORT_EMAIL}"
    except Exception as e:
        logger.error(f"Error enviando email: {e}")
        return False, f"❌ Error enviando email: {e}"


DAILY_ANALYSIS_SYSTEM = """Eres un subagente de análisis y auditoría interna.
Tu tarea es revisar el estado del agente IA y generar un reporte diario conciso.

Analiza y reporta:
1. HABILIDADES: cuántas hay, cuáles se usaron recientemente, cuáles pueden mejorarse
2. MEMORIAS: cuántos usuarios tienen memoria, resumen de hechos y preferencias guardadas
3. WORKSPACE: archivos presentes, tamaño total, archivos obsoletos
4. CÓDIGO: lee bot.py y detecta posibles mejoras, bugs o técnicas desactualizadas
5. ACTIVIDAD: usuarios activos, modelos más usados, horas de mayor demanda

Formato del reporte:
- Sé conciso (cabe en un mensaje de Telegram)
- Usa emojis para secciones
- Incluye 2-3 recomendaciones de mejora concretas
- Termina con una puntuación de salud del sistema (0-10)"""

async def run_daily_analysis():
    """Subagente autónomo que analiza el sistema una vez al día."""
    if not OWNER_ID or not _telegram_bot:
        return

    logger.info("🔍 Iniciando análisis diario del sistema...")
    try:
        await _telegram_bot.send_message(
            chat_id=OWNER_ID,
            text="🔍 *Análisis diario iniciado...*",
            parse_mode="Markdown",
        )
    except Exception:
        pass

    # Recopilar contexto del sistema para el subagente
    skills = all_skills()
    memory_files = list(MEMORY_DIR.glob("*.json"))
    workspace_files = [f for f in WORKSPACE.rglob("*") if f.is_file()
                       and not str(f).startswith(str(MEMORY_DIR))
                       and not str(f).startswith(str(SKILLS_DIR))]
    workspace_size = sum(f.stat().st_size for f in workspace_files)

    # Construir snapshot del estado actual
    system_snapshot = (
        f"Estado del sistema — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Habilidades guardadas: {len(skills)}\n"
        + ("".join(f"  - {s['name']}: {s['description']}\n" for s in skills) or "  (ninguna)\n")
        + f"\nUsuarios con memoria: {len(memory_files)}\n"
        f"Archivos en workspace: {len(workspace_files)} ({workspace_size // 1024} KB)\n"
        f"Conversaciones activas en sesión: {len(conversations)}\n"
        f"Modelos en uso: {dict((v, k) for k, v in user_models.items())}\n"
    )

    # Leer el código del bot para análisis
    try:
        bot_code_summary = BOT_FILE.read_text(encoding="utf-8")[:6000]
    except Exception:
        bot_code_summary = "(no disponible)"

    # Llamada a Claude como subagente de análisis (modelo opus para análisis profundo)
    analysis_messages = [
        {
            "role": "user",
            "content": (
                f"Realiza el análisis diario del sistema.\n\n"
                f"SNAPSHOT DEL SISTEMA:\n{system_snapshot}\n\n"
                f"CÓDIGO DEL BOT (primeras 6000 chars):\n```python\n{bot_code_summary}\n```\n\n"
                f"Genera el reporte diario según tus instrucciones."
            ),
        }
    ]

    try:
        response = await client.messages.create(
            model="claude-opus-4-6",   # Opus para análisis profundo
            max_tokens=2048,
            system=DAILY_ANALYSIS_SYSTEM,
            messages=analysis_messages,
        )
        report = ""
        for block in response.content:
            if hasattr(block, "text"):
                report = block.text
                break

        header = f"📊 *Reporte diario — {datetime.now().strftime('%d/%m/%Y')}*\n\n"
        full_report = header + report

        # Enviar en chunks si es largo
        for i in range(0, max(len(full_report), 1), 4096):
            await _telegram_bot.send_message(
                chat_id=OWNER_ID,
                text=full_report[i : i + 4096],
                parse_mode="Markdown",
            )

        # Guardar reporte en workspace
        date_str = datetime.now().strftime('%Y-%m-%d')
        report_dir = WORKSPACE / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        txt_path = report_dir / f"daily_{date_str}.txt"
        txt_path.write_text(full_report, encoding="utf-8")

        # Generar PDF y enviar por email
        pdf_path = report_dir / f"daily_{date_str}.pdf"
        pdf_ok = _generate_pdf_report(full_report, pdf_path, date_str)
        if pdf_ok and SMTP_USER and SMTP_PASS:
            email_ok, email_msg = _send_email_report(pdf_path, date_str)
            status = f"📧 Email: {email_msg}"
        elif not SMTP_USER:
            status = "📧 Email no configurado (falta SMTP_USER en .env)"
        else:
            status = "⚠️ PDF no generado (instala reportlab: pip install reportlab)"

        try:
            await _telegram_bot.send_message(
                chat_id=OWNER_ID, text=status, parse_mode="Markdown",
            )
        except Exception:
            pass

        logger.info("📊 Análisis diario completado y enviado.")
    except Exception as e:
        logger.error(f"Error en análisis diario: {e}")
        try:
            await _telegram_bot.send_message(
                chat_id=OWNER_ID,
                text=f"⚠️ Error en análisis diario: {e}",
            )
        except Exception:
            pass


# ─── Handlers de Telegram ──────────────────────────────────────────────────────

def allowed(user_id: int) -> bool:
    return not ALLOWED_USERS or str(user_id) in ALLOWED_USERS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Hola {name}! Soy tu agente IA con 4 pilares:\n\n"
        "🧠 *Modelos* — sonnet / opus / haiku según la tarea\n"
        "🔧 *Herramientas* — web, código Python, archivos, URLs\n"
        "💾 *Memoria* — recuerdo tus datos entre sesiones\n"
        "🎯 *Habilidades* — procedimientos reutilizables entre agentes\n\n"
        "🎭 *Personas disponibles:*\n"
        "• asistente · programador · investigador\n"
        "• analista · escritor · arquitecto\n\n"
        "Comandos:\n"
        "/persona — cambiar persona activa\n"
        "/memory  — ver tu memoria guardada\n"
        "/skills  — ver habilidades disponibles\n"
        "/status  — estado del agente\n"
        "/clear   — limpiar la conversación\n"
        "/help    — este mensaje\n\n"
        "¡Escríbeme lo que necesitas!",
        parse_mode="Markdown",
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conversations.pop(update.effective_user.id, None)
    await update.message.reply_text(
        "🗑️ Conversación limpiada. Tu memoria y habilidades se mantienen."
    )


async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not allowed(user_id):
        return
    mem = load_memory(user_id)
    parts = ["💾 *Tu memoria persistente:*\n"]
    if mem["facts"]:
        parts.append("*Hechos:*\n" + "\n".join(f"• {f}" for f in mem["facts"]))
    if mem["preferences"]:
        parts.append("*Preferencias:*\n" + "\n".join(f"• {k} = {v}" for k, v in mem["preferences"].items()))
    if mem["notes"]:
        parts.append("*Notas recientes:*\n" + "\n".join(f"• {n}" for n in mem["notes"][-5:]))
    if len(parts) == 1:
        parts.append("_(vacía — conversa y guardaré lo que importa)_")
    await update.message.reply_text("\n\n".join(parts), parse_mode="Markdown")


async def cmd_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not allowed(user_id):
        return
    text = run_list_skills()
    await update.message.reply_text(f"🎯 *Habilidades:*\n\n{text}", parse_mode="Markdown")


async def cmd_persona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not allowed(user_id):
        return
    args = context.args
    if args:
        persona_key = args[0].lower()
        result = run_switch_persona(user_id, persona_key)
        await update.message.reply_text(result, parse_mode="Markdown")
    else:
        current = get_user_persona(user_id)
        lines = [f"🎭 *Personas disponibles* (actual: `{current}`):\n"]
        for key, info in PERSONAS.items():
            marker = "✅" if key == current else "•"
            lines.append(f"{marker} *{key}*: {info['description']}")
        lines.append("\nUsa: `/persona nombre`")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    files = [
        f for f in WORKSPACE.rglob("*")
        if f.is_file()
        and not str(f).startswith(str(MEMORY_DIR))
        and not str(f).startswith(str(SKILLS_DIR))
    ]
    model_alias = next(
        (k for k, v in MODEL_REGISTRY.items() if v == get_user_model(uid)), "sonnet"
    )
    mem = load_memory(uid)
    mem_items = len(mem["facts"]) + len(mem["preferences"]) + len(mem["notes"])
    persona = get_user_persona(uid)
    # Rate limit restante
    now = time.time()
    used = len([t for t in user_request_log.get(uid, []) if now - t < RATE_LIMIT_WINDOW])
    await update.message.reply_text(
        f"⚙️ *Estado del agente*\n\n"
        f"🧠 Modelo: `{model_alias}`\n"
        f"🎭 Persona: `{persona}`\n"
        f"💾 Ítems en memoria: {mem_items}\n"
        f"🎯 Habilidades: {len(all_skills())}\n"
        f"🔧 Herramientas: {len(TOOLS)}\n"
        f"⏱️ Requests esta hora: {used}/{RATE_LIMIT_REQUESTS}\n"
        f"🌐 Servidor web: :{WEB_PORT}\n"
        f"📁 Archivos workspace: {len(files)}\n"
        f"👥 Conversaciones activas: {len(conversations)}",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    username = update.effective_user.first_name

    if not allowed(user_id):
        await update.message.reply_text("⛔ Sin acceso.")
        return

    text        = update.message.text or update.message.caption or ""
    image_bytes = None

    # Seguridad: detección de prompt injection
    if text and detect_prompt_injection(text):
        logger.warning(f"⚠️ Posible prompt injection de [{username}:{user_id}]: {text[:80]}")
        await update.message.reply_text(
            "⚠️ Se detectó un patrón sospechoso en tu mensaje. "
            "Por favor reformula tu solicitud de forma diferente."
        )
        return

    # Rate limiting
    ok, rate_msg = check_rate_limit(user_id)
    if not ok:
        await update.message.reply_text(rate_msg)
        return

    await update.message.chat.send_action("typing")

    if update.message.photo:
        photo       = update.message.photo[-1]
        file        = await context.bot.get_file(photo.file_id)
        raw         = await file.download_as_bytearray()
        image_bytes = bytes(raw)

    logger.info(f"[{username}:{user_id}] {text[:100]}")

    try:
        reply = await run_agent(user_id, text, image_bytes)
        for i in range(0, max(len(reply), 1), 4096):
            await update.message.reply_text(reply[i : i + 4096])
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text("❌ Error. Intenta de nuevo o /clear.")


# ─── Main ───────────────────────────────────────────────────────────────────────

def main():
    global _telegram_bot

    if not TELEGRAM_TOKEN:
        raise ValueError("❌ Falta TELEGRAM_TOKEN en .env")
    if not ANTHROPIC_KEY:
        raise ValueError("❌ Falta ANTHROPIC_API_KEY en .env")

    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_trend_update, "interval", hours=6)
    # Subagente diario: análisis a las 08:00 cada día
    scheduler.add_job(run_daily_analysis, "cron", hour=8, minute=0)

    async def post_init(application: Application) -> None:
        global _telegram_bot
        _telegram_bot = application.bot
        scheduler.start()
        logger.info("📅 Scheduler iniciado (tendencias 6h + análisis diario 08:00).")

    async def post_shutdown(application: Application) -> None:
        scheduler.shutdown(wait=False)

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("clear",   cmd_clear))
    app.add_handler(CommandHandler("memory",  cmd_memory))
    app.add_handler(CommandHandler("skills",  cmd_skills))
    app.add_handler(CommandHandler("persona", cmd_persona))
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(CommandHandler("help",    cmd_start))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    logger.info("🤖 Agente iniciado (4 pilares + personas + seguridad). Ctrl+C para detener.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
