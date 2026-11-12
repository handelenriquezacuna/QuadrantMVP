# Libro de tokens

Tokens según los reporta la herramienta de subagentes (`subagent_tokens` del último aviso de cada agente; incluye sus ciclos de corrección). "sin dato" si no hay cifra real.

| Tarea | Agente | Modelo | Ciclos de validación | Tokens dev | Tokens validador | Resultado |
|---|---|---|---|---|---|---|
| T-04 | dev-app / validador | sonnet / haiku | 2 (1 rechazo: variable `QDRANT_PUBLIC_URL` vs `QDRANT_URL_PUBLICA`; origen: brief del Dictador sin §1) | 37,893 | 42,062 | APROBADO |
| T-05 | dev-app / validador | sonnet / haiku | 1 | 40,143 | 48,155 | APROBADO |
| T-06 | dev-app / validador | sonnet / haiku | 1 | 39,573 | sin dato aún | APROBADO |
| T-01 | dev-infra / validador | sonnet / haiku | 1 (build terminado por el Dictador por red lenta; dev detenido tras reportes repetidos) | 46,577 | 35,542 | APROBADO |
| T-03 | dev-datos / validador | sonnet / haiku | 1 (más un ajuste de contrato del Dictador antes de validar) | 47,628 | 44,476 | APROBADO |
| T-02 | dev-datos / validador | sonnet / haiku | 2 (1 rechazo: faltaba `ingest/__init__.py`) | 30,081 | 33,055 | APROBADO |

## Totales por agente

| Agente | Tokens |
|---|---|
