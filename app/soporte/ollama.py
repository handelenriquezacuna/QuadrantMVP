"""Cliente mínimo de Ollama. Los tokens salen de la respuesta, nunca se estiman."""
import os
import time
from dataclasses import dataclass

import httpx


@dataclass
class RespuestaLLM:
    texto: str
    tokens_entrada: int   # prompt_eval_count
    tokens_salida: int    # eval_count
    latencia_ms: float


def _url() -> str:
    return os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434").rstrip("/")


def _modelo() -> str:
    return os.environ.get("OLLAMA_MODEL", "llama3.2:3b")


def _num_ctx() -> int:
    return int(os.environ.get("OLLAMA_NUM_CTX", "12288"))


def disponible() -> bool:
    """True si Ollama responde (timeout 2 s) y el modelo configurado está descargado."""
    try:
        r = httpx.get(f"{_url()}/api/tags", timeout=2.0)
        r.raise_for_status()
        nombres = {m.get("name", "") for m in r.json().get("models", [])}
    except Exception:  # noqa: BLE001 - cualquier fallo significa "no disponible"
        return False
    modelo = _modelo()
    candidatos = {modelo, modelo if ":" in modelo else f"{modelo}:latest"}
    return bool(candidatos & nombres)


def chat(sistema: str, usuario: str, modelo: str | None = None) -> RespuestaLLM:
    """Una llamada a /api/chat sin streaming y con temperatura 0."""
    cuerpo = {
        "model": modelo or _modelo(),
        "stream": False,
        "options": {"temperature": 0, "num_ctx": _num_ctx()},
        "messages": [{"role": "system", "content": sistema},
                     {"role": "user", "content": usuario}],
    }
    t0 = time.perf_counter()
    r = httpx.post(f"{_url()}/api/chat", json=cuerpo, timeout=900.0)
    r.raise_for_status()
    datos = r.json()
    ms = (time.perf_counter() - t0) * 1000
    return RespuestaLLM(
        texto=datos.get("message", {}).get("content", "").strip(),
        tokens_entrada=int(datos.get("prompt_eval_count", 0)),
        tokens_salida=int(datos.get("eval_count", 0)),
        latencia_ms=ms,
    )
