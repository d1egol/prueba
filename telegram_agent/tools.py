"""
Herramientas disponibles para el agente.

Fix #3/#7: DDGS es síncrono — se envuelve en asyncio.to_thread
para no bloquear el event loop con múltiples usuarios simultáneos.
"""

import asyncio
import logging

from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

# ─── Definiciones para la API de Anthropic ────────────────────────────────────

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


# ─── Implementaciones ──────────────────────────────────────────────────────────

def _run_web_search_sync(query: str, max_results: int) -> str:
    """Búsqueda DuckDuckGo (síncrona, se ejecuta en thread pool)."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No se encontraron resultados para esa búsqueda."
        lines = [
            f"📌 {r['title']}\n{r['body']}\n🔗 {r['href']}"
            for r in results
        ]
        return "\n\n---\n\n".join(lines)
    except Exception as e:
        return f"Error en búsqueda: {e}"


async def run_web_search(query: str, max_results: int = 5) -> str:
    """Wrapper async — no bloquea el event loop."""
    return await asyncio.to_thread(_run_web_search_sync, query, max_results)


async def execute_tool(name: str, tool_input: dict) -> str:
    """Despacha la herramienta correcta de forma async."""
    if name == "web_search":
        return await run_web_search(
            tool_input["query"],
            tool_input.get("max_results", 5),
        )
    return f"Herramienta '{name}' no reconocida."
