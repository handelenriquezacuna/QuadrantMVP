# Plan — Qdrant Lab

## Fases y orden

| Fase | Tareas | Agente | Paralelo con | Depende de |
|---|---|---|---|---|
| 1. Infraestructura y datos | T-01 Compose, Dockerfile, .env, CI | dev-infra | T-02, T-03 | — |
| | T-02 Muestra parquet del dataset | dev-datos | T-01, T-03 | — |
| | T-03 Capa `app/store/` + ingesta | dev-datos | T-01, T-02 | CONTRATOS |
| 2. Explorador | T-04 App Streamlit, pestañas 1, 2, 3, 4 y 6 | dev-app | T-05 | T-01, T-03 |
| 3. Caso de soporte | T-05 Grafo LangGraph, cliente Ollama, métricas | dev-app | T-04 | T-03 |
| | T-06 Pestaña 5 (UI + fallback benchmark) | dev-app | T-07 | T-05 |
| | T-10 Ollama como servicio opcional (profile `llm`) | dev-infra | T-06 | T-01 |
| | T-07 Benchmark grabado de 100 preguntas (con el contenedor de Ollama) | dev-datos | — | T-05, T-10 |
| 4. Documentación | T-08 README (requisitos, 3 comandos, Mermaid, guion 4 min) | dev-infra | — | T-04, T-06 |
| | T-11 Cifras reales en el guion | dev-infra | — | T-07 |
| 5. Certificación | T-09 Certificado desde clon limpio | certificador | — | todas |

T-02 y T-03 son del mismo agente pero independientes: se lanzan como dos invocaciones paralelas.

## Ciclo por tarea

1. Dictador lanza al dev con: `docs/tareas/T-XX.md` + sección de CONTRATOS citada + rutas permitidas.
2. Dev entrega (≤150 palabras).
3. Validador recibe: tarea, sección de contrato, `git diff` de la entrega. Responde `APROBADO` o `RECHAZADO` + defectos numerados.
4. Rechazo → mismo dev con la lista. Máx. 2 ciclos; al 3.º decide el Dictador.
5. Aprobado → commit `T-XX: <resumen>` (sin marcas de IA) y fila en `LIBRO_TOKENS.md`.

## Modelos por rol

| Rol | Modelo |
|---|---|
| Dictador | Opus (sesión principal) |
| dev-infra, dev-datos, dev-app | Sonnet |
| validador | Haiku |
| certificador | Opus |

## Riesgos

- ~~Ollama ausente~~ → resuelto con el profile `llm` (D-17). Latencias del benchmark en CPU (D-18).
- Tiempo de build: la imagen descarga ~0.3 GB de modelos; ingesta estimada < 30 s para 3,000 filas.
