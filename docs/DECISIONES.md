# Decisiones

Registro corto: fecha, decisión, motivo. Los agentes leen de aquí; no repetir en conversación.

| # | Fecha | Decisión | Motivo |
|---|---|---|---|
| D-01 | 2026-11-11 | Modelo denso: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dims, 0.22 GB) vía fastembed 0.9.1 | Multilingüe, liviano para 8 GB. Prueba local: "quiero que me devuelvan el dinero de mi compra" → "I want a refund for my purchase" con coseno 0.76; 1,000 textos/s en CPU (M-series). |
| D-02 | 2026-11-11 | Disperso: `Qdrant/bm25` con `modifier=IDF` en la colección | Requerido por el prompt; el IDF lo calcula Qdrant. |
| D-03 | 2026-11-11 | Versiones fijadas: Qdrant `v1.20.0` (imagen amd64+arm64 verificada en Docker Hub), qdrant-client 1.20.0, fastembed 0.9.1, streamlit 1.67.0, langgraph 1.2.20 | Últimas estables al 2026-11-11. |
| D-04 | 2026-11-11 | Fusión híbrida con `models.FusionQuery(fusion=models.Fusion.RRF)` en `query_points` con dos `Prefetch` | Documentado en qdrant.tech/documentation/concepts/hybrid-queries; clases verificadas en qdrant-client 1.20.0 (`RrfQuery` también existe). |
| D-05 | 2026-11-11 | Recomendaciones con `models.RecommendQuery(recommend=models.RecommendInput(positive, negative, strategy))` + `using="dense"` | Documentado en qdrant.tech/documentation/concepts/explore. Estrategias: average_vector, best_score, sum_scores. |
| D-06 | 2026-11-11 | Dataset: columnas reales `flags, instruction, category, intent, response`; 26,872 filas; licencia CDLA-Sharing-1.0 | Verificado en la API de Hugging Face. La licencia permite redistribuir con la misma licencia → se incluye muestra de 3,000 filas en `data/` con aviso de licencia. |
| D-07 | 2026-11-11 | Una sola imagen Docker para `app` e `ingest` (distinto `command`) | Los modelos se descargan una vez en el build. |
| D-08 | 2026-11-11 | `.env.example` trae una API key de desarrollo local no secreta | El criterio 1 exige arrancar con `cp .env.example .env` sin pasos extra. Se documenta que debe cambiarse fuera del aula. |
| D-09 | 2026-11-11 | Commits sin ninguna marca de IA (sin Co-Authored-By ni pie "Generated with") | Instrucción del dueño del repo. |
| D-10 | 2026-11-11 | Ollama no está instalado en la máquina de construcción | El benchmark grabado (T-07) debe ser real: requiere instalar Ollama en el host antes de la fase 4. Pendiente de OK del usuario. |
