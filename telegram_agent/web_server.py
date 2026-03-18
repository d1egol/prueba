"""
Servidor web para el webchat del agente.
FastAPI + WebSocket con streaming de tokens en tiempo real.

Ejecutar:
    cd telegram_agent
    python web_server.py
    # o con uvicorn directamente:
    uvicorn web_server:app --host 0.0.0.0 --port 8080 --reload
"""

import asyncio
import base64
import json
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from agent_core import run_agent
from memory import clear_history, get_stats
from rate_limiter import RateLimiter

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────────

WEB_PORT          = int(os.getenv("WEB_PORT", "8080"))
WEB_HOST          = os.getenv("WEB_HOST", "0.0.0.0")
RATE_LIMIT_MSGS   = int(os.getenv("RATE_LIMIT_MSGS", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
AGENT_TIMEOUT     = int(os.getenv("AGENT_TIMEOUT", "120"))

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="FireWatch Agent Webchat")
rate_limiter = RateLimiter(max_messages=RATE_LIMIT_MSGS, window_seconds=RATE_LIMIT_WINDOW)

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


# ─── HTTP endpoints ────────────────────────────────────────────────────────────

@app.get("/")
async def get_index() -> HTMLResponse:
    index = STATIC_DIR / "index.html"
    return HTMLResponse(index.read_text(encoding="utf-8"))


@app.post("/api/clear/{session_id}")
async def api_clear(session_id: str) -> dict:
    """Borra el historial de una sesión."""
    await clear_history(session_id)
    return {"ok": True}


@app.get("/api/stats")
async def api_stats() -> dict:
    """Estadísticas globales (sesiones activas, mensajes totales)."""
    return await get_stats()


# ─── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info("WS conectado: %s", session_id)

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send(websocket, {"type": "error", "text": "JSON inválido."})
                continue

            text: str = msg.get("text", "").strip()
            image_b64: Optional[str] = msg.get("image")

            # Fix #10: mensajes vacíos
            if not text and not image_b64:
                await _send(websocket, {"type": "error", "text": "Mensaje vacío."})
                continue

            # Fix #4: rate limiting
            if not rate_limiter.is_allowed(session_id):
                wait = rate_limiter.seconds_until_reset(session_id)
                await _send(websocket, {
                    "type": "error",
                    "text": f"Demasiadas solicitudes. Espera {wait}s.",
                })
                continue

            # Decodificar imagen si viene
            image_data: Optional[bytes] = None
            if image_b64:
                try:
                    # Quitar prefijo data URL si viene del browser
                    if "," in image_b64:
                        image_b64 = image_b64.split(",", 1)[1]
                    image_data = base64.b64decode(image_b64)
                except Exception as exc:
                    logger.warning("Error decodificando imagen: %s", exc)

            # Callback de streaming → envía eventos al browser vía WebSocket
            async def stream_callback(event: dict) -> None:
                await _send(websocket, event)

            try:
                await asyncio.wait_for(
                    run_agent(session_id, text, image_data, stream_callback),
                    timeout=AGENT_TIMEOUT,
                )
                await _send(websocket, {"type": "done"})

            except asyncio.TimeoutError:
                logger.warning("Timeout para sesión %s", session_id)
                await _send(websocket, {
                    "type": "error",
                    "text": f"Tiempo de espera excedido ({AGENT_TIMEOUT}s). "
                            "Intenta con una pregunta más corta.",
                })

            except Exception as exc:
                logger.error("Error en agente [%s]: %s", session_id, exc, exc_info=True)
                await _send(websocket, {
                    "type": "error",
                    "text": "Error interno. Intenta de nuevo.",
                })

    except WebSocketDisconnect:
        logger.info("WS desconectado: %s", session_id)


async def _send(ws: WebSocket, data: dict) -> None:
    """Envía un dict como JSON por WebSocket, ignorando errores de conexión cerrada."""
    try:
        await ws.send_text(json.dumps(data, ensure_ascii=False))
    except Exception:
        pass


# ─── Entrada ───────────────────────────────────────────────────────────────────

def main():
    import uvicorn
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT, log_level="info")


if __name__ == "__main__":
    main()
