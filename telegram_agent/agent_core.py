"""
Núcleo del agente IA — agnóstico al canal (Telegram, webchat, etc.)

Fixes integrados:
  #1  Memoria persistente (via memory.py)
  #2  Contexto limitado a CONTEXT_WINDOW mensajes (ventana deslizante)
  #3  Búsqueda web async, no bloquea el event loop (via tools.py)
  #5  Detección real del formato de imagen (JPEG/PNG/GIF/WebP)
  #9  SYSTEM_PROMPT sin referencias a Telegram
  #10 Manejo de mensajes vacíos
  #11 Logs sin truncar
  #13 session_id: str — no acoplado a user_id de Telegram
  #14 Streaming de tokens via stream_callback (para webchat)
"""

import base64
import logging
import os
from typing import Any, Awaitable, Callable, Optional

import anthropic
from dotenv import load_dotenv

from memory import add_message, get_history
from tools import TOOLS, execute_tool

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────────

ANTHROPIC_KEY    = os.getenv("ANTHROPIC_API_KEY")
CONTEXT_WINDOW   = int(os.getenv("CONTEXT_WINDOW", "40"))   # máx mensajes en contexto
MAX_AGENT_STEPS  = int(os.getenv("MAX_AGENT_STEPS", "10"))  # máx iteraciones del loop

logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)

# ─── Personalidad ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un agente IA inteligente, conciso y útil.
Puedes buscar información actualizada en la web y analizar imágenes.
Razonas paso a paso cuando la tarea es compleja.
Respondes siempre en el idioma del usuario (español por defecto).
Cuando necesites información reciente o específica, usa web_search."""

# Tipo del callback de streaming: recibe un dict de evento
StreamCallback = Callable[[dict], Awaitable[None]]


# ─── Utilidades ────────────────────────────────────────────────────────────────

def detect_media_type(data: bytes) -> str:
    """Detecta el formato de imagen desde los primeros bytes (fix #5)."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"  # fallback seguro


def serialize_content(content: list) -> list[dict]:
    """Convierte bloques de respuesta de Anthropic a dicts serializables."""
    result = []
    for block in content:
        if block.type == "text":
            result.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            result.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })
        else:
            # thinking u otros — serializar con model_dump si está disponible
            if hasattr(block, "model_dump"):
                result.append(block.model_dump())
    return result


def build_user_content(text: str, image_data: Optional[bytes]) -> Any:
    """Construye el contenido del mensaje del usuario."""
    if not image_data:
        return text if text.strip() else "Hola"

    media_type = detect_media_type(image_data)
    return [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.standard_b64encode(image_data).decode(),
            },
        },
        {"type": "text", "text": text.strip() or "¿Qué ves en esta imagen?"},
    ]


# ─── Loop agéntico ─────────────────────────────────────────────────────────────

async def run_agent(
    session_id: str,
    text: str,
    image_data: Optional[bytes] = None,
    stream_callback: Optional[StreamCallback] = None,
) -> str:
    """
    Loop agéntico principal.

    Args:
        session_id:      Identificador único de sesión (str, agnóstico al canal).
        text:            Texto del mensaje del usuario.
        image_data:      Bytes de la imagen adjunta (opcional).
        stream_callback: Si se provee, se llama en tiempo real con cada evento
                         de streaming (para webchat). Sin callback → sin streaming
                         (para Telegram).

    Returns:
        Texto completo de la última respuesta del asistente.
    """
    # Fix #10: mensaje vacío
    if not text.strip() and not image_data:
        return "No recibí ningún mensaje. ¿En qué te puedo ayudar?"

    content = build_user_content(text, image_data)
    await add_message(session_id, "user", content)

    logger.info("[%s] → %s", session_id, repr(text[:200]))  # fix #11: sin truncar a 80

    current_text = ""

    for step in range(MAX_AGENT_STEPS):
        # Fix #2: solo los últimos CONTEXT_WINDOW mensajes
        messages = await get_history(session_id, limit=CONTEXT_WINDOW)
        current_text = ""

        # ── Modo streaming (webchat) ──────────────────────────────────────────
        if stream_callback:
            stream = client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            async with stream as s:
                async for event in s:
                    if (
                        event.type == "content_block_delta"
                        and event.delta.type == "text_delta"
                    ):
                        await stream_callback({"type": "token", "text": event.delta.text})
                        current_text += event.delta.text

            response = await stream.get_final_message()

        # ── Modo normal (Telegram) ────────────────────────────────────────────
        else:
            response = await client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            for block in response.content:
                if hasattr(block, "text"):
                    current_text += block.text

        # Persistir respuesta del asistente
        await add_message(session_id, "assistant", serialize_content(response.content))

        # ── Respuesta final ───────────────────────────────────────────────────
        if response.stop_reason == "end_turn":
            break

        # ── Llamadas a herramientas ───────────────────────────────────────────
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info("[%s] Tool: %s | %s", session_id, block.name, block.input)

                    if stream_callback:
                        await stream_callback({
                            "type": "tool_start",
                            "name": block.name,
                            "input": block.input,
                        })

                    result = await execute_tool(block.name, block.input)

                    if stream_callback:
                        await stream_callback({"type": "tool_done", "name": block.name})

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            await add_message(session_id, "user", tool_results)
        else:
            # stop_reason inesperado
            break

    return current_text or "No generé texto en esta respuesta."
