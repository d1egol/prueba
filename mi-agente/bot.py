"""
Mi Agente IA — Bot de Telegram
Arquitectura de 4 Pilares:
  1. Modelos de Lenguaje  — multi-model (sonnet / opus / haiku)
  2. Herramientas autónomas — tool registry con dispatcher contextual
  3. Memoria persistente   — hechos / preferencias / notas por usuario
  4. Habilidades transferibles — skill registry compartido entre agentes
"""

import os, sys, json, logging, base64, asyncio, subprocess, threading, re
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

# Directorios de pilares 3 y 4
MEMORY_DIR = WORKSPACE / "memory"
SKILLS_DIR = WORKSPACE / "skills"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Pilar 1: Modelos de Lenguaje ──────────────────────────────────────────────
# Registro de modelos disponibles con sus alias

MODEL_REGISTRY: dict[str, str] = {
    "sonnet": "claude-sonnet-4-6",           # equilibrado — default
    "opus":   "claude-opus-4-6",             # máxima capacidad
    "haiku":  "claude-haiku-4-5-20251001",   # rápido y eficiente
}
DEFAULT_MODEL = "claude-sonnet-4-6"

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)

# modelo activo por usuario (se restaura desde memoria al iniciar sesión)
user_models: dict[int, str] = {}

def get_user_model(user_id: int) -> str:
    return user_models.get(user_id, DEFAULT_MODEL)


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
    """Contexto de memoria listo para inyectar en el system prompt."""
    mem = load_memory(user_id)
    parts = []
    if mem["facts"]:
        parts.append("Hechos del usuario:\n" + "\n".join(f"- {f}" for f in mem["facts"]))
    if mem["preferences"]:
        prefs = ", ".join(f"{k}={v}" for k, v in mem["preferences"].items())
        parts.append(f"Preferencias: {prefs}")
    if mem["notes"]:
        parts.append("Notas guardadas:\n" + "\n".join(f"- {n}" for n in mem["notes"][-10:]))
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
    """Resumen de habilidades disponibles para el system prompt."""
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


# ─── System Prompt dinámico (se construye por usuario en cada llamada) ──────────

BASE_SYSTEM = """Eres un agente IA autónomo con 4 pilares de capacidad:

1. MODELOS: Operas con diferentes modelos Claude según la complejidad de la tarea.
   - sonnet (default): tareas generales y equilibradas
   - opus: análisis complejos, razonamiento profundo, código avanzado
   - haiku: respuestas rápidas, tareas simples, bajo consumo

2. HERRAMIENTAS: Acceso autónomo a internet, código, archivos y mensajería.
   - web_search / fetch_url: información actualizada
   - run_python: código Python en el servidor
   - read_file / write_file / list_files: workspace ({workspace}) → :{port}
   - send_message: notificaciones proactivas a usuarios
   - read_own_code / update_own_code: auto-mejora

3. MEMORIA: Recuerdas información del usuario entre sesiones.
   - save_memory(type, content): guarda fact/preference/note
   - recall_memory(query): busca en la memoria
   - clear_memory: borra toda la memoria del usuario

4. HABILIDADES: Procedimientos reutilizables compartidos entre agentes.
   - save_skill(name, description, prompt, tags): guarda una habilidad
   - list_skills(tag?): lista habilidades disponibles
   - run_skill(name, args?): ejecuta una habilidad
   - delete_skill(name): elimina una habilidad

Reglas de uso:
- Al conocer datos relevantes del usuario (nombre, preferencias, proyectos), guárdalos con save_memory
- Antes de una tarea compleja, verifica si hay una habilidad ya creada con list_skills
- Usa opus para razonamiento profundo; haiku para tareas simples; sonnet por defecto
- switch_model cambia el modelo activo para el resto de la conversación
- Responde siempre en el idioma del usuario (español por defecto)
- Mensajes concisos — estás en Telegram, no en un documento"""

def build_system_prompt(user_id: int) -> str:
    base = BASE_SYSTEM.format(workspace=WORKSPACE, port=WEB_PORT)

    mem_ctx = memory_context(user_id)
    if mem_ctx:
        base += f"\n\n--- MEMORIA DEL USUARIO ---\n{mem_ctx}"

    sk_ctx = skills_context()
    if sk_ctx:
        base += f"\n\n--- HABILIDADES DISPONIBLES ---\n{sk_ctx}"

    model_alias = next((k for k, v in MODEL_REGISTRY.items() if v == get_user_model(user_id)), "sonnet")
    base += f"\n\nModelo activo: {model_alias}"

    return base


# ─── Definición de herramientas ────────────────────────────────────────────────

TOOLS = [
    # ── Pilar 2: Herramientas de conexión ──
    {
        "name": "web_search",
        "description": "Busca información actualizada en internet (noticias, precios, documentación, tendencias AI).",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Consulta de búsqueda"},
                "max_results": {"type": "integer", "description": "Resultados (1-8, default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_url",
        "description": "Descarga y lee el contenido completo de una URL.",
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
        "description": "Ejecuta código Python en el servidor. Útil para cálculos, análisis, generar archivos, instalar paquetes.",
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
        "description": "Crea o sobreescribe un archivo en el workspace (HTML, scripts, datos, etc.).",
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
        "description": "Reemplaza el código fuente completo del bot y lo reinicia. Lee el código primero.",
        "input_schema": {
            "type": "object",
            "properties": {
                "new_code": {"type": "string", "description": "Código Python completo"},
                "reason": {"type": "string", "description": "Descripción de las mejoras"},
            },
            "required": ["new_code", "reason"],
        },
    },
    # ── Pilar 1: Modelos ──
    {
        "name": "switch_model",
        "description": "Cambia el modelo Claude activo para este usuario. Usa opus para tareas complejas, haiku para respuestas rápidas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "enum": ["sonnet", "opus", "haiku"]},
                "reason": {"type": "string", "description": "Motivo del cambio (opcional)"},
            },
            "required": ["model"],
        },
    },
    # ── Pilar 3: Memoria ──
    {
        "name": "save_memory",
        "description": "Guarda información persistente del usuario que se recordará en futuras sesiones.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["fact", "preference", "note"],
                    "description": "fact=dato biográfico/contextual, preference=clave=valor, note=nota libre con fecha",
                },
                "content": {"type": "string", "description": "El hecho, 'clave=valor', o texto de la nota"},
            },
            "required": ["type", "content"],
        },
    },
    {
        "name": "recall_memory",
        "description": "Busca en la memoria persistente del usuario por palabra clave.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "clear_memory",
        "description": "Borra toda la memoria persistente del usuario. Solo usar si el usuario lo pide explícitamente.",
        "input_schema": {"type": "object", "properties": {}},
    },
    # ── Pilar 4: Habilidades ──
    {
        "name": "save_skill",
        "description": "Guarda una habilidad reutilizable. Las habilidades persisten entre sesiones y están disponibles para todos los agentes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nombre único en snake_case"},
                "description": {"type": "string", "description": "Qué hace esta habilidad (1 línea)"},
                "prompt": {"type": "string", "description": "Instrucción detallada de cómo ejecutar la habilidad paso a paso"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Etiquetas para categorizar (ej: ['análisis', 'web', 'código'])",
                },
            },
            "required": ["name", "description", "prompt"],
        },
    },
    {
        "name": "list_skills",
        "description": "Lista todas las habilidades guardadas, opcionalmente filtradas por etiqueta.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tag": {"type": "string", "description": "Filtrar por etiqueta (opcional)"},
            },
        },
    },
    {
        "name": "run_skill",
        "description": "Ejecuta una habilidad guardada. Proporciona contexto o argumentos específicos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nombre de la habilidad"},
                "args": {"type": "string", "description": "Contexto o argumentos para esta ejecución"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "delete_skill",
        "description": "Elimina una habilidad del registro.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
            "required": ["name"],
        },
    },
]


# ─── Implementaciones de herramientas ──────────────────────────────────────────

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
    # persistir en preferencias de memoria
    mem = load_memory(user_id)
    mem["preferences"]["model"] = model_alias
    _persist_memory(user_id, mem)
    note = f" — {reason}" if reason else ""
    return f"✅ Modelo cambiado a **{model_alias}** ({model_id}){note}."


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
        entry = f"[{datetime.now().strftime('%Y-%m-%d')}] {content}"
        mem["notes"].append(entry)
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
    return "✅ Memoria borrada."


# ── Pilar 4: Habilidades ─────────────────────────────────────────────────────

def run_save_skill(name: str, description: str, prompt: str,
                   tags: list[str] | None = None, author_id: int = 0) -> str:
    data = {
        "name": name,
        "description": description,
        "prompt": prompt,
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
    lines = [f"📚 {len(skills)} habilidad(es) disponible(s):"]
    for s in skills:
        tags_str = f" [{', '.join(s['tags'])}]" if s.get("tags") else ""
        lines.append(f"• **{s['name']}**{tags_str}: {s['description']}")
    return "\n".join(lines)


def run_delete_skill(name: str) -> str:
    path = _skill_path(name)
    if path.exists():
        path.unlink()
        return f"✅ Habilidad '{name}' eliminada."
    return f"❌ Habilidad '{name}' no encontrada."


def run_get_skill_prompt(name: str, args: str = "") -> str:
    """Devuelve el prompt de la habilidad para que el LLM lo ejecute."""
    skill = load_skill(name)
    if not skill:
        skills_list = ", ".join(s["name"] for s in all_skills()) or "ninguna"
        return f"❌ Habilidad '{name}' no encontrada. Disponibles: {skills_list}"
    prompt = skill["prompt"]
    if args:
        prompt = f"{prompt}\n\nContexto/argumentos para esta ejecución: {args}"
    return f"[Habilidad: {skill['name']}]\n{skill['description']}\n\n{prompt}"


# ─── Dispatcher ────────────────────────────────────────────────────────────────

async def dispatch_tool(name: str, inputs: dict, user_id: int) -> str:
    # Pilar 2: herramientas de conexión
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
    # Pilar 1: modelos
    elif name == "switch_model":
        return run_switch_model(user_id, inputs["model"], inputs.get("reason", ""))
    # Pilar 3: memoria
    elif name == "save_memory":
        return run_save_memory(user_id, inputs["type"], inputs["content"])
    elif name == "recall_memory":
        return run_recall_memory(user_id, inputs["query"])
    elif name == "clear_memory":
        return run_clear_memory(user_id)
    # Pilar 4: habilidades
    elif name == "save_skill":
        return run_save_skill(
            inputs["name"], inputs["description"], inputs["prompt"],
            inputs.get("tags"), user_id,
        )
    elif name == "list_skills":
        return run_list_skills(inputs.get("tag"))
    elif name == "run_skill":
        return run_get_skill_prompt(inputs["name"], inputs.get("args", ""))
    elif name == "delete_skill":
        return run_delete_skill(inputs["name"])
    return f"Herramienta '{name}' no disponible."


# ─── Estado de conversaciones ──────────────────────────────────────────────────

conversations: dict[int, list] = {}
_telegram_bot: Bot | None = None


# ─── Loop agéntico ─────────────────────────────────────────────────────────────

async def run_agent(user_id: int, text: str, image_bytes: bytes | None = None) -> str:
    # Nueva sesión: restaurar modelo desde memoria
    if user_id not in conversations:
        conversations[user_id] = []
        mem = load_memory(user_id)
        saved_model = mem.get("preferences", {}).get("model")
        if saved_model and saved_model in MODEL_REGISTRY:
            user_models[user_id] = MODEL_REGISTRY[saved_model]

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
            system=build_system_prompt(user_id),   # system prompt dinámico con memoria + skills
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
        logger.info("📬 Tendencias enviadas al owner.")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")


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
        "Comandos:\n"
        "/memory — ver tu memoria guardada\n"
        "/skills — ver habilidades disponibles\n"
        "/status — estado del agente\n"
        "/clear  — limpiar la conversación actual\n"
        "/help   — este mensaje\n\n"
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
        parts.append("*Notas:*\n" + "\n".join(f"• {n}" for n in mem["notes"][-5:]))
    if len(parts) == 1:
        parts.append("_(vacía — conversa y guardaré lo que importa)_")
    await update.message.reply_text("\n\n".join(parts), parse_mode="Markdown")


async def cmd_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not allowed(user_id):
        return
    text = run_list_skills()
    await update.message.reply_text(f"🎯 *Habilidades:*\n\n{text}", parse_mode="Markdown")


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
    await update.message.reply_text(
        f"⚙️ *Estado del agente*\n\n"
        f"🧠 Modelo activo: `{model_alias}`\n"
        f"💾 Ítems en memoria: {mem_items}\n"
        f"🎯 Habilidades guardadas: {len(all_skills())}\n"
        f"🔧 Herramientas disponibles: {len(TOOLS)}\n"
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

    await update.message.chat.send_action("typing")

    text        = update.message.text or update.message.caption or ""
    image_bytes = None

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

    async def post_init(application: Application) -> None:
        global _telegram_bot
        _telegram_bot = application.bot
        scheduler.start()
        logger.info("📅 Scheduler de tendencias iniciado.")

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
    app.add_handler(CommandHandler("status",  cmd_status))
    app.add_handler(CommandHandler("help",    cmd_start))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    logger.info("🤖 Agente 4-pilares iniciado. Ctrl+C para detener.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
