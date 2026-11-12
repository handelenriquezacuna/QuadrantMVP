# Libro de tokens

Tokens según los reporta la herramienta de subagentes (`subagent_tokens` del último aviso de cada agente; incluye sus ciclos de corrección). "sin dato" si no hay cifra real.

| Tarea | Agente | Modelo | Ciclos de validación | Tokens dev | Tokens validador | Resultado |
|---|---|---|---|---|---|---|
| T-01 | dev-infra / validador | sonnet / haiku | 1 (build terminado por el Dictador por red lenta; dev detenido tras reportes repetidos) | 46,577 | 35,542 | APROBADO |
| T-02 | dev-datos / validador | sonnet / haiku | 2 (1 rechazo: faltaba `ingest/__init__.py`) | 30,081 | 33,055 | APROBADO |
| T-03 | dev-datos / validador | sonnet / haiku | 1 (más un ajuste de contrato del Dictador antes de validar) | 47,628 | 44,476 | APROBADO |
| T-04 | dev-app / validador | sonnet / haiku | 2 (1 rechazo: variable `QDRANT_PUBLIC_URL` vs `QDRANT_URL_PUBLICA`; origen: brief del Dictador sin §1) | 37,893 | 42,062 | APROBADO |
| T-05 | dev-app / validador | sonnet / haiku | 1 | 40,143 | 48,155 | APROBADO |
| T-06 | dev-app / validador | sonnet / haiku | 1 | 39,573 | 36,080 | APROBADO |
| T-07 | dev-datos (2 instancias) / validador | sonnet / haiku | 2 (1 rechazo: etiqueta fija "CPU"; corregido por una instancia nueva para no arrastrar contexto). Benchmark pausado por num_ctx (T-12) y regenerado en GPU nativa (D-23) | 65,733 + 28,377 | 44,126 (acumulado) | APROBADO |
| T-08 | dev-infra / validador | sonnet / haiku | 3 → decide Dictador: aprobado con alcance reducido; cifras de las filas 3 y 5 pasan a T-11 | 35,482 | 43,278 | APROBADO (Dictador) |
| T-10 | dev-infra / validador | sonnet / haiku | 1 (rechazo anulado por el Dictador: el archivo señalado era una edición del Dictador al libro de tokens) | 41,355 | 40,042 | APROBADO |
| T-11 | dev-infra / validador | sonnet / haiku | 1 (rechazo resuelto por el Dictador: faltaba registrar en D-25 la composición de la híbrida, ya medida) | 28,859 | 32,092 | APROBADO |
| T-12 | dev-app / validador | sonnet / haiku | 1 (rechazo anulado por el Dictador: docs eran del Dictador; timeout pedido en el brief, D-22) | 29,002 | 33,481 | APROBADO |
| T-14 | dev-infra / validador | sonnet / haiku | 1 | 27,575 | 28,419 | APROBADO |
| T-09 | certificador | opus | — (11/11 PASA; C11 con desviación D-26) | 64,570 | — | CERTIFICADO |
| T-13 | dev-infra / validador | sonnet / haiku | 1 | 28,708 | 28,879 | APROBADO |

## Totales por agente

| Agente | Modelo | Tokens |
|---|---|---|
| dev-infra | sonnet | 208,556 |
| dev-datos | sonnet | 171,819 |
| dev-app | sonnet | 146,611 |
| validador | haiku | 489,687 |
| certificador | opus | 64,570 |
| Dictador (sesión principal) | opus | sin dato: la herramienta no reporta el consumo de la sesión principal |
| **Total subagentes** | | **1,081,243** |

Notas: cifras = `subagent_tokens` del último aviso de cada agente (acumulado del agente, incluye sus ciclos). Trabajo del Dictador fuera de subagentes (builds, pruebas de humo, corridas del benchmark) no tiene cifra reportada.
