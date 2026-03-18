"""
Mi Agente IA — Bot de Telegram
Powered by Claude Sonnet 4.6 (Anthropic)
"""

import os
import sys
import logging
import base64
import asyncio
import subprocess
import threading
from pathlib import Path
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

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)

# Historial de conversación por usuario
conversations: dict[int, list] = {}

# Referencia global al bot de Telegram para el scheduler
_telegram_bot: Bot | None = None

# ─── Servidor web para workspace ───────────────────────────────────────────────

class WorkspaceHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WORKSPACE), **kwargs)

    def log_message(self, format, *args):
        pass  # Silenciar logs del HTTP server


def start_web_server():
    server = HTTPServer(("0.0.0.0", WEB_PORT), WorkspaceHandler)
    logger.info(f"🌐 Servidor web iniciado en :{WEB_PORT} → sirve {WORKSPACE}")
    server.serve_forever()


# ─── Personalidad ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""Eres un agente IA autónomo, proactivo y capaz de mejorar sus propias capacidades, accesible por Telegram.

Herramientas disponibles:
- web_search: busca información actualizada en internet (noticias, tendencias, novedades de Claude/Anthropic)
- fetch_url: descarga y lee el contenido completo de una URL
- run_python: ejecuta código Python en el servidor (cálculos, análisis, generación de archivos)
- read_file / write_file / list_files: trabaja con archivos en el workspace ({WORKSPACE})
- send_message: envía mensajes proactivos a usuarios de Telegram
- read_own_code: lee tu código fuente actual para entenderte a ti mismo
- update_own_code: modifica tu propio código fuente y te reinicias con las mejoras

Capacidades especiales:
- Puedes crear páginas web completas escribiendo HTML en el workspace — son accesibles en el puerto {WEB_PORT}
- Puedes modificar tu propio código para agregar nuevas herramientas, mejorar tu personalidad o instalar plugins
- Siempre que detectes una limitación, puedes proponer y aplicar una mejora a tu propio código
- Para mantenerte actualizado, busca periódicamente novedades de Claude y Anthropic

Reglas:
- Usa múltiples herramientas en secuencia cuando sea necesario
- Antes de modificar tu código, léelo primero con read_own_code
- Responde siempre en el idioma del usuario (español por defecto)
- Mensajes concisos — estás en Telegram, no en un documento"""

# ─── Definición de herramientas ────────────────────────────────────────────────

TOOLS = [
    {
        "name": "web_search",
        "description": "Busca información actualizada en internet. Úsalo para noticias, tendencias de Claude/AI, precios, eventos, o cualquier dato que pueda haber cambiado.",
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
        "description": "Descarga y lee el contenido de una URL específica. Útil para leer artículos completos, documentación, o scraping.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL a descargar"},
                "max_chars": {"type": "integer", "description": "Máximo de caracteres (default 6000)", "default": 6000},
            },
            "required": ["url"],
        },
    },
    {
        "name": "run_python",
        "description": "Ejecuta código Python en el servidor. Útil para cálculos, análisis de datos, generar archivos, instalar paquetes con pip, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Código Python a ejecutar"},
                "timeout": {"type": "integer", "description": "Timeout en segundos (default 30)", "default": 30},
            },
            "required": ["code"],
        },
    },
    {
        "name": "read_file",
        "description": "Lee el contenido de un archivo en el workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Nombre del archivo (relativo al workspace)"},
            },
            "required": ["filename"],
        },
    },
    {
        "name": "write_file",
        "description": "Crea o sobreescribe un archivo en el workspace. Ideal para páginas HTML, scripts, notas, datos JSON, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Nombre del archivo (relativo al workspace)"},
                "content": {"type": "string", "description": "Contenido del archivo"},
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "list_files",
        "description": "Lista todos los archivos disponibles en el workspace.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "send_message",
        "description": "Envía un mensaje proactivo de Telegram a un usuario. Útil para notificaciones, alertas de tendencias, o resultados de tareas en segundo plano.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "ID del usuario de Telegram"},
                "text": {"type": "string", "description": "Mensaje a enviar"},
            },
            "required": ["user_id", "text"],
        },
    },
    {
        "name": "read_own_code",
        "description": "Lee el código fuente actual de este bot (bot.py). Úsalo antes de modificarte a ti mismo.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "update_own_code",
        "description": "Reemplaza el código fuente completo de este bot y lo reinicia automáticamente. IMPORTANTE: lee el código actual primero con read_own_code, luego proporciona el código completo mejorado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "new_code": {"type": "string", "description": "Código Python completo que reemplaza bot.py"},
                "reason": {"type": "string", "description": "Descripción de las mejoras realizadas"},
            },
            "required": ["new_code", "reason"],
        },
    },
]

# ─── Implementaciones de herramientas ──────────────────────────────────────────

def run_web_search(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "Sin resultados para esa búsqueda."
        items = [f"📌 {r['title']}\n{r['body']}\n🔗 {r['href']}" for r in results]
        return "\n\n---\n\n".join(items)
    except Exception as e:
        return f"Error en búsqueda: {e}"


def run_fetch_url(url: str, max_chars: int = 6000) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AgentBot/1.0)"}
        with httpx.Client(timeout=15, follow_redirects=True) as client_http:
            r = client_http.get(url, headers=headers)
            r.raise_for_status()
            text = r.text
            # Eliminar etiquetas HTML básicamente
            import re
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s{3,}", "\n\n", text).strip()
            return text[:max_chars] + (f"\n\n[...truncado en {max_chars} chars]" if len(text) > max_chars else "")
    except Exception as e:
        return f"Error al descargar URL: {e}"


def run_python_code(code: str, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(WORKSPACE),
        )
        output = ""
        if result.stdout:
            output += f"stdout:\n{result.stdout}"
        if result.stderr:
            output += f"\nstderr:\n{result.stderr}"
        if not output:
            output = "(Sin salida)"
        return output[:4000]
    except subprocess.TimeoutExpired:
        return f"❌ Timeout ({timeout}s) alcanzado."
    except Exception as e:
        return f"❌ Error: {e}"


def run_read_file(filename: str) -> str:
    try:
        path = (WORKSPACE / filename).resolve()
        if not str(path).startswith(str(WORKSPACE)):
            return "❌ Acceso denegado fuera del workspace."
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"❌ Archivo '{filename}' no encontrado."
    except Exception as e:
        return f"❌ Error: {e}"


def run_write_file(filename: str, content: str) -> str:
    try:
        path = (WORKSPACE / filename).resolve()
        if not str(path).startswith(str(WORKSPACE)):
            return "❌ Acceso denegado fuera del workspace."
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"✅ Archivo '{filename}' guardado ({len(content)} chars). Accesible en el servidor web."
    except Exception as e:
        return f"❌ Error: {e}"


def run_list_files() -> str:
    try:
        files = list(WORKSPACE.rglob("*"))
        if not files:
            return "El workspace está vacío."
        lines = []
        for f in sorted(files):
            if f.is_file():
                size = f.stat().st_size
                lines.append(f"📄 {f.relative_to(WORKSPACE)} ({size} bytes)")
        return "\n".join(lines) if lines else "Sin archivos."
    except Exception as e:
        return f"❌ Error: {e}"


async def run_send_message(user_id: int, text: str) -> str:
    if not _telegram_bot:
        return "❌ Bot no inicializado aún."
    try:
        await _telegram_bot.send_message(chat_id=user_id, text=text)
        return f"✅ Mensaje enviado a {user_id}."
    except Exception as e:
        return f"❌ Error al enviar: {e}"


def run_read_own_code() -> str:
    try:
        return BOT_FILE.read_text(encoding="utf-8")
    except Exception as e:
        return f"❌ Error leyendo código: {e}"


def run_update_own_code(new_code: str, reason: str) -> str:
    try:
        # Backup del código actual
        backup = BOT_FILE.with_suffix(".backup.py")
        backup.write_text(BOT_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        # Escribir nuevo código
        BOT_FILE.write_text(new_code, encoding="utf-8")
        logger.info(f"🔄 Código actualizado: {reason}")
        # Reiniciar el proceso en 3 segundos (para dar tiempo a responder)
        def restart():
            import time
            time.sleep(3)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        threading.Thread(target=restart, daemon=True).start()
        return f"✅ Código actualizado: {reason}\n♻️ El bot se reiniciará en 3 segundos con las mejoras aplicadas."
    except Exception as e:
        return f"❌ Error actualizando código: {e}"


async def dispatch_tool(name: str, inputs: dict) -> str:
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
    return f"Herramienta '{name}' no disponible."


# ─── Loop agéntico ─────────────────────────────────────────────────────────────

async def run_agent(user_id: int, text: str, image_bytes: bytes | None = None) -> str:
    if user_id not in conversations:
        conversations[user_id] = []

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
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=SYSTEM_PROMPT,
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
            return "(Sin texto en la respuesta)"

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"🔧 {block.name} | {str(block.input)[:120]}")
                    result = await dispatch_tool(block.name, block.input)
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

    return "Se alcanzó el límite de pasos. Prueba simplificar la tarea o usa /clear."


# ─── Scheduler: tendencias de Claude/AI ────────────────────────────────────────

async def send_trend_update():
    """Busca las últimas novedades de Claude/Anthropic y las envía al owner."""
    if not OWNER_ID or not _telegram_bot:
        return
    try:
        results = run_web_search("Claude Anthropic AI novedades actualizaciones", max_results=4)
        msg = "🤖 *Tendencias AI del día:*\n\n" + results[:3000]
        await _telegram_bot.send_message(
            chat_id=OWNER_ID,
            text=msg[:4096],
            parse_mode="Markdown",
        )
        logger.info("📬 Tendencias enviadas al owner.")
    except Exception as e:
        logger.error(f"Error en scheduler de tendencias: {e}")


# ─── Handlers de Telegram ──────────────────────────────────────────────────────

def allowed(user_id: int) -> bool:
    return not ALLOWED_USERS or str(user_id) in ALLOWED_USERS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Hola {name}! Soy tu agente IA autónomo.\n\n"
        "Puedo hacer esto:\n"
        "🔍 Buscar información actualizada en la web\n"
        "🌐 Leer el contenido de cualquier URL\n"
        "🐍 Ejecutar código Python en el servidor\n"
        "📁 Leer y escribir archivos en el workspace\n"
        "🖼️ Crear páginas web y publicarlas\n"
        "📬 Enviarte notificaciones proactivas\n"
        "🔧 Modificar mi propio código para mejorarme\n"
        "🧠 Analizar imágenes que me mandes\n\n"
        "Comandos:\n"
        "/clear — limpiar el historial\n"
        "/status — ver estado del agente\n"
        "/help  — ver este mensaje\n\n"
        "¡Escríbeme lo que necesitas!"
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conversations.pop(update.effective_user.id, None)
    await update.message.reply_text("🗑️ Historial borrado. ¡Empecemos de nuevo!")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = list(WORKSPACE.rglob("*"))
    file_count = sum(1 for f in files if f.is_file())
    await update.message.reply_text(
        f"⚙️ *Estado del agente*\n\n"
        f"🤖 Modelo: claude-sonnet-4-6\n"
        f"🌐 Servidor web: :{WEB_PORT}\n"
        f"📁 Workspace: {WORKSPACE} ({file_count} archivos)\n"
        f"👥 Conversaciones activas: {len(conversations)}\n"
        f"🔧 Herramientas: {len(TOOLS)}",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    username = update.effective_user.first_name

    if not allowed(user_id):
        await update.message.reply_text("⛔ No tienes acceso a este bot.")
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
        logger.error(f"Error procesando mensaje: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Ocurrió un error. Intenta de nuevo o usa /clear."
        )


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    global _telegram_bot

    if not TELEGRAM_TOKEN:
        raise ValueError("❌ Falta TELEGRAM_TOKEN en el archivo .env")
    if not ANTHROPIC_KEY:
        raise ValueError("❌ Falta ANTHROPIC_API_KEY en el archivo .env")

    # Servidor web para workspace (hilo separado)
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    _telegram_bot = app.bot

    # Scheduler de tendencias (cada 6 horas)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_trend_update, "interval", hours=6)
    scheduler.start()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("clear",  cmd_clear))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("help",   cmd_start))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    logger.info("🤖 Agente iniciado. Ctrl+C para detener.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
