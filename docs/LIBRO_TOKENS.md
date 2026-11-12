# Libro de tokens

Tokens según los reporta la herramienta de subagentes (`subagent_tokens` del último aviso de cada agente; incluye sus ciclos de corrección). "sin dato" si no hay cifra real.

| Tarea | Agente | Modelo | Ciclos de validación | Tokens dev | Tokens validador | Resultado |
|---|---|---|---|---|---|---|
| T-02 | dev-datos / validador | sonnet / haiku | 2 (1 rechazo: faltaba `ingest/__init__.py`) | 30,081 | 33,055 | APROBADO |

## Totales por agente

| Agente | Tokens |
|---|---|
