"""
Mi Agente IA — Bot de Telegram
Powered by Claude Opus 4.6 (Anthropic)
"""

import os
import logging
import base64
from dotenv import load_dotenv

import anthropic
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from duckduckgo_search import DDGS

load_dotenv()

# ─── Configuración ─────────────────────────────────────────────────────────────

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY")
# Opcional: lista de IDs de Telegram autorizados (separados por coma)
# Si está vacío, cualquiera puede usar el bot
ALLOWED_USERS  = [u.strip() for u in os.getenv("ALLOWED_USERS", "").split(",") if u.strip()]

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)

# Historial de conversación por usuario (clave = user_id de Telegram)
conversations: dict[int, list] = {}

# ─── Personalidad ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un agente IA inteligente y versátil accesible por Telegram.
Tienes acceso a búsqueda web en tiempo real y puedes analizar imágenes.
Cuando la tarea lo requiere, piensas paso a paso antes de responder.
Respondes siempre en el idioma del usuario (español por defecto).
Tus respuestas son concisas pero completas — estás en Telegram, no en un documento.
Cuando necesites información reciente o que pueda haber cambiado, usa web_search."""

# ─── Herramientas ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Busca información actualizada en internet. Úsalo para: noticias recientes, "
            "precios actuales, eventos, datos que puedan haber cambiado, "
            "o cualquier cosa donde necesites información fresca."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Consulta de búsqueda",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Resultados a obtener (1-8, default 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
]


def run_web_search(query: str, max_results: int = 5) -> str:
    """Búsqueda web via DuckDuckGo (sin API key)."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "Sin resultados para esa búsqueda."
        items = []
        for r in results:
            items.append(f"📌 {r['title']}\n{r['body']}\n🔗 {r['href']}")
        return "\n\n---\n\n".join(items)
    except Exception as e:
        return f"Error en búsqueda: {e}"


def dispatch_tool(name: str, inputs: dict) -> str:
    if name == "web_search":
        return run_web_search(inputs["query"], inputs.get("max_results", 5))
    return f"Herramienta '{name}' no disponible."


# ─── Loop agéntico ─────────────────────────────────────────────────────────────

async def run_agent(user_id: int, text: str, image_bytes: bytes | None = None) -> str:
    """
    Envía el mensaje a Claude Opus 4.6 con thinking adaptativo.
    Claude puede llamar herramientas múltiples veces antes de responder.
    """
    if user_id not in conversations:
        conversations[user_id] = []

    # Construir contenido del mensaje
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

    # Loop agéntico (máx. 10 iteraciones por seguridad)
    for _ in range(10):
        response = await client.messages.create(
            model="claude-opus-4-6",
            max_tokens=16000,
            thinking={"type": "adaptive"},   # Claude decide cuánto razonar
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=conversations[user_id],
        )

        # Guardar respuesta del asistente en el historial
        conversations[user_id].append({
            "role": "assistant",
            "content": response.content,
        })

        if response.stop_reason == "end_turn":
            # Extraer el texto final
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "(Sin texto en la respuesta)"

        if response.stop_reason == "tool_use":
            # Ejecutar todas las herramientas solicitadas
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"🔧 Herramienta: {block.name} | {block.input}")
                    result = dispatch_tool(block.name, block.input)
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

    return "Se alcanzó el límite de pasos. Prueba simplificar la pregunta o usa /clear."


# ─── Handlers de Telegram ──────────────────────────────────────────────────────

def allowed(user_id: int) -> bool:
    return not ALLOWED_USERS or str(user_id) in ALLOWED_USERS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Hola {name}! Soy tu agente IA.\n\n"
        "Puedo hacer esto:\n"
        "🔍 Buscar información actualizada en la web\n"
        "🖼️ Analizar fotos que me mandes\n"
        "💬 Recordar el contexto de nuestra conversación\n"
        "🧠 Razonar en profundidad con problemas complejos\n\n"
        "Comandos:\n"
        "/clear — limpiar el historial\n"
        "/help  — ver este mensaje\n\n"
        "¡Escríbeme lo que necesitas!"
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conversations.pop(update.effective_user.id, None)
    await update.message.reply_text("🗑️ Historial borrado. ¡Empecemos de nuevo!")


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
        photo       = update.message.photo[-1]          # mayor resolución
        file        = await context.bot.get_file(photo.file_id)
        raw         = await file.download_as_bytearray()
        image_bytes = bytes(raw)

    logger.info(f"[{username}:{user_id}] {text[:100]}")

    try:
        reply = await run_agent(user_id, text, image_bytes)

        # Telegram limita mensajes a 4096 caracteres
        for i in range(0, max(len(reply), 1), 4096):
            await update.message.reply_text(reply[i : i + 4096])

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Ocurrió un error. Intenta de nuevo o usa /clear."
        )


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("❌ Falta TELEGRAM_TOKEN en el archivo .env")
    if not ANTHROPIC_KEY:
        raise ValueError("❌ Falta ANTHROPIC_API_KEY en el archivo .env")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("help",  cmd_start))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    logger.info("🤖 Agente iniciado. Ctrl+C para detener.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
