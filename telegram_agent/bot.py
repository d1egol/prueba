"""
FireWatch Agent — Telegram Bot (capa delgada)
Toda la lógica del agente vive en agent_core.py.

Fixes integrados:
  #4  Rate limiting (via rate_limiter.py)
  #6  AGENT_TIMEOUT en la sección de Config (arriba)
  #8  Comando /status con métricas básicas
  #10 Manejo de tipos de mensaje no soportados (stickers, audio, docs…)
  #11 Logs sin truncar
  #13 session_id = str(user_id) — el core no conoce Telegram
"""

import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from agent_core import run_agent
from memory import clear_history, get_stats
from rate_limiter import RateLimiter

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────────

TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_KEY     = os.getenv("ANTHROPIC_API_KEY")
ALLOWED_USERS     = [u.strip() for u in os.getenv("ALLOWED_USERS", "").split(",") if u.strip()]
AGENT_TIMEOUT     = int(os.getenv("AGENT_TIMEOUT", "120"))
RATE_LIMIT_MSGS   = int(os.getenv("RATE_LIMIT_MSGS", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

rate_limiter = RateLimiter(max_messages=RATE_LIMIT_MSGS, window_seconds=RATE_LIMIT_WINDOW)


# ─── Utilidades ────────────────────────────────────────────────────────────────

def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True  # Sin whitelist = abierto
    return str(user_id) in ALLOWED_USERS


async def keep_typing(chat, stop_event: asyncio.Event) -> None:
    """Mantiene el indicador 'escribiendo…' activo mientras el agente trabaja."""
    while not stop_event.is_set():
        try:
            await chat.send_action("typing")
        except Exception:
            pass
        await asyncio.sleep(4)


# ─── Handlers de comandos ──────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        "/status — estadísticas del agente\n"
        "/help — ver esto de nuevo\n\n"
        "¡Escríbeme lo que necesitas!"
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session_id = str(update.effective_user.id)
    await clear_history(session_id)
    await update.message.reply_text("🗑️ Historial limpiado. ¡Empecemos de nuevo!")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fix #8: estadísticas básicas del agente."""
    stats = await get_stats()
    await update.message.reply_text(
        f"📊 Estado del agente:\n"
        f"• Sesiones activas: {stats['active_sessions']}\n"
        f"• Mensajes totales: {stats['total_messages']}\n"
        f"• Rate limit: {RATE_LIMIT_MSGS} msgs / {RATE_LIMIT_WINDOW}s\n"
        f"• Timeout: {AGENT_TIMEOUT}s"
    )


# ─── Handler principal ─────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id  = update.effective_user.id
    username = update.effective_user.first_name
    msg      = update.message

    # Acceso
    if not is_allowed(user_id):
        await msg.reply_text("⛔ No tienes acceso a este bot.")
        return

    # Fix #10: tipos de mensaje no soportados
    if not msg.text and not msg.photo and not msg.caption:
        unsupported = (
            "sticker" if msg.sticker else
            "audio"   if msg.audio or msg.voice else
            "video"   if msg.video else
            "archivo" if msg.document else
            "mensaje"
        )
        await msg.reply_text(
            f"⚠️ No sé procesar este tipo de {unsupported}. "
            "Puedo responder texto e imágenes."
        )
        return

    # Fix #4: rate limiting
    session_id = str(user_id)
    if not rate_limiter.is_allowed(session_id):
        wait = rate_limiter.seconds_until_reset(session_id)
        await msg.reply_text(
            f"⏳ Demasiadas solicitudes. Espera {wait}s antes de enviar otro mensaje."
        )
        return

    text: str           = msg.text or msg.caption or ""
    image_data: Optional[bytes] = None

    # Descargar foto si viene
    if msg.photo:
        photo      = msg.photo[-1]  # mayor resolución disponible
        file       = await context.bot.get_file(photo.file_id)
        raw        = await file.download_as_bytearray()
        image_data = bytes(raw)

    # Fix #11: log sin truncar
    logger.info("[%s:%s] %s", username, user_id, repr(text))

    # Mantener "escribiendo…" activo durante todo el procesamiento
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(msg.chat, stop_typing))

    try:
        # Sin stream_callback → modo Telegram (respuesta completa de una vez)
        reply = await asyncio.wait_for(
            run_agent(session_id, text, image_data),
            timeout=AGENT_TIMEOUT,
        )

        # Telegram limita mensajes a 4096 caracteres
        for i in range(0, len(reply), 4096):
            await msg.reply_text(reply[i : i + 4096])

    except asyncio.TimeoutError:
        logger.warning("Timeout para usuario %s", user_id)
        await msg.reply_text(
            f"⏱️ La respuesta tardó más de {AGENT_TIMEOUT}s. "
            "Intenta con una instrucción más corta o usa /clear para limpiar el historial."
        )
    except Exception as e:
        logger.error("Error [%s]: %s", user_id, e, exc_info=True)
        await msg.reply_text(
            "❌ Hubo un error. Intenta de nuevo o usa /clear si el problema persiste."
        )
    finally:
        stop_typing.set()
        typing_task.cancel()


# ─── Inicio ────────────────────────────────────────────────────────────────────

def main() -> None:
    if not TELEGRAM_TOKEN:
        raise ValueError("Falta TELEGRAM_TOKEN en .env")
    if not ANTHROPIC_KEY:
        raise ValueError("Falta ANTHROPIC_API_KEY en .env")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("clear",  cmd_clear))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.Sticker.ALL |
        filters.AUDIO | filters.VOICE | filters.VIDEO | filters.Document.ALL,
        handle_message,
    ))

    logger.info("🤖 Bot Telegram corriendo… Ctrl+C para detener.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
