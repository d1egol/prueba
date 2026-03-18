"""
FireWatch Agent — Telegram Bot con IA
Powered by Claude (Anthropic) + python-telegram-bot
"""

import os
import logging
import base64
from typing import Optional
from dotenv import load_dotenv

import anthropic
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from duckduckgo_search import DDGS

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY")
ALLOWED_USERS   = [u.strip() for u in os.getenv("ALLOWED_USERS", "").split(",") if u.strip()]

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)

# Historial de conversación por usuario (en memoria)
conversations: dict[int, list] = {}

# ─── Personalidad del agente ───────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un agente IA inteligente accesible por Telegram.
Puedes buscar información actualizada en la web y analizar imágenes.
Razonas paso a paso cuando la tarea es compleja.
Respondes siempre en el idioma del usuario (español por defecto).
Eres conciso pero completo — esto es Telegram, no un documento.
Cuando necesites información reciente o específica, usa web_search."""

# ─── Herramientas disponibles ──────────────────────────────────────────────────

TOOLS = [
    {
        "name": "web_search",
        "description": (
            "Busca información actualizada en internet. "
            "Úsalo para noticias recientes, precios, datos que puedan haber cambiado, "
            "o cualquier información que no tengas segura."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Consulta de búsqueda en lenguaje natural",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Número de resultados (1-10, default 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
]


def run_web_search(query: str, max_results: int = 5) -> str:
    """Ejecuta búsqueda en DuckDuckGo (sin API key necesaria)."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No se encontraron resultados para esa búsqueda."
        lines = []
        for r in results:
            lines.append(f"📌 {r['title']}\n{r['body']}\n🔗 {r['href']}")
        return "\n\n---\n\n".join(lines)
    except Exception as e:
        return f"Error en búsqueda: {e}"


def execute_tool(name: str, tool_input: dict) -> str:
    """Despacha la herramienta correcta según el nombre."""
    if name == "web_search":
        return run_web_search(
            tool_input["query"],
            tool_input.get("max_results", 5),
        )
    return f"Herramienta '{name}' no reconocida."


# ─── Loop del agente ───────────────────────────────────────────────────────────

async def run_agent(
    user_id: int,
    text: str,
    image_data: Optional[bytes] = None,
) -> str:
    """
    Loop agentico: Claude puede llamar herramientas multiples veces
    antes de dar la respuesta final.
    """
    if user_id not in conversations:
        conversations[user_id] = []

    # Construir contenido del mensaje
    if image_data:
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(image_data).decode(),
                },
            },
            {"type": "text", "text": text or "¿Qué ves en esta imagen?"},
        ]
    else:
        content = text

    conversations[user_id].append({"role": "user", "content": content})

    # Loop hasta respuesta final
    for _ in range(10):  # máximo 10 iteraciones por seguridad
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=conversations[user_id],
        )

        # Guardar respuesta del asistente
        conversations[user_id].append({
            "role": "assistant",
            "content": response.content,
        })

        if response.stop_reason == "end_turn":
            # Extraer texto final
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "No generé texto en esta respuesta."

        if response.stop_reason == "tool_use":
            # Ejecutar todas las herramientas pedidas
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"Herramienta: {block.name} | Input: {block.input}")
                    result = execute_tool(block.name, block.input)
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

    return "Se alcanzó el límite de pasos. Intenta con una pregunta más específica."


# ─── Handlers de Telegram ──────────────────────────────────────────────────────

def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True  # Sin whitelist = abierto
    return str(user_id) in ALLOWED_USERS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Hola {name}! Soy tu agente IA.\n\n"
        "Puedo:\n"
        "🔍 Buscar info actualizada en la web\n"
        "🖼️ Analizar imágenes que me mandes\n"
        "💬 Recordar el contexto de nuestra conversación\n"
        "🤖 Razonar y ejecutar múltiples pasos\n\n"
        "Comandos:\n"
        "/clear — limpiar historial\n"
        "/help — ver esto de nuevo\n\n"
        "¡Escríbeme lo que necesitas!"
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conversations.pop(update.effective_user.id, None)
    await update.message.reply_text("🗑️ Historial limpiado. ¡Empecemos de nuevo!")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    username = update.effective_user.first_name

    if not is_allowed(user_id):
        await update.message.reply_text("⛔ No tienes acceso a este bot.")
        return

    await update.message.chat.send_action("typing")

    text       = update.message.text or update.message.caption or ""
    image_data = None

    # Si manda foto, descargarla
    if update.message.photo:
        photo      = update.message.photo[-1]  # mayor resolución
        file       = await context.bot.get_file(photo.file_id)
        raw        = await file.download_as_bytearray()
        image_data = bytes(raw)

    logger.info(f"[{username}:{user_id}] {text[:80]}")

    try:
        reply = await run_agent(user_id, text, image_data)

        # Telegram limita mensajes a 4096 caracteres
        if len(reply) > 4096:
            for i in range(0, len(reply), 4096):
                await update.message.reply_text(reply[i : i + 4096])
        else:
            await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Hubo un error. Intenta de nuevo o usa /clear si el problema persiste."
        )


# ─── Inicio ────────────────────────────────────────────────────────────────────

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Falta TELEGRAM_TOKEN en .env")
    if not ANTHROPIC_KEY:
        raise ValueError("Falta ANTHROPIC_API_KEY en .env")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    logger.info("🤖 Bot corriendo... Ctrl+C para detener.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
