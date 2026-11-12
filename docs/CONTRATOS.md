# Contratos

Fuente única de verdad entre módulos. Solo el Dictador la modifica. Cada tarea cita las secciones (§) que le aplican.

## §1 Variables de entorno (`.env.example`)

| Variable | Default | Usada por |
|---|---|---|
| `QDRANT_API_KEY` | `qdrant-lab-clave-local-cambiar` | qdrant (como `QDRANT__SERVICE__API_KEY`), app, ingest |
| `QDRANT_URL` | `http://qdrant:6333` | app, ingest |
| `QDRANT_URL_PUBLICA` | `http://localhost:6333` | app (solo para mostrar el enlace al dashboard) |
| `DENSE_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | app, ingest |
| `SPARSE_MODEL` | `Qdrant/bm25` | app, ingest |
| `FASTEMBED_CACHE_PATH` | `/models` | app, ingest (modelos horneados en la imagen) |
| `MUESTRA_PATH` | `/app/data/muestra_bitext.parquet` | ingest, soporte (modo sin Qdrant) |
| `BENCHMARK_PATH` | `/app/data/benchmark_grabado.csv` | pestaña 5 |
| `PRICING_PATH` | `/app/pricing.yaml` | soporte |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | soporte |
| `OLLAMA_MODEL` | `llama3.2:3b` (en la Mac M4 Max: `qwen2.5:14b`) | soporte |
| `CACHE_THRESHOLD` | `0.92` | soporte |

## §2 Docker Compose

- Servicios: `qdrant`, `ingest`, `app`. Una sola imagen (`Dockerfile`) para `ingest` y `app`.
- `qdrant`: imagen `qdrant/qdrant:v1.20.0`, puertos `6333:6333` y `6334:6334`, volumen nombrado `qdrant_data:/qdrant/storage`, `QDRANT__SERVICE__API_KEY=${QDRANT_API_KEY}`, healthcheck sobre `/healthz` (la imagen no trae curl: usar `bash -c ':> /dev/tcp/127.0.0.1/6333'` o equivalente que exista en la imagen).
- `ingest`: `command: python -m ingest.ingestar`, `depends_on: qdrant: service_healthy`, `restart: "no"`.
- `app`: `command: streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0`, puerto `8501:8501`, `depends_on: ingest: service_completed_successfully`, `extra_hosts: ["host.docker.internal:host-gateway"]`.
- `docker compose run --rm app pytest` debe funcionar (el `command` se sobrescribe).
- Imagen base fijada (p. ej. `python:3.11.X-slim-bookworm`), multi-arquitectura. Nada de `latest`.
- `Dockerfile` instala `requirements.txt` con versiones exactas y descarga ambos modelos de fastembed en `/models` durante el build. Copia `app/`, `ingest/`, `tests/`, `data/`, `pricing.yaml` a `/app`. `WORKDIR /app`, `PYTHONPATH=/app`.

## §3 Datos

- `data/muestra_bitext.parquet`: 3,000 filas de `bitext/Bitext-customer-support-llm-chatbot-training-dataset`, muestreo estratificado por `intent` con `random_state=42`. Columnas: `row_id:int` (0..2999), `flags:str`, `instruction:str`, `category:str`, `intent:str`, `response:str`.
- `data/LICENCIA_DATASET.md`: fuente, licencia CDLA-Sharing-1.0, cómo se generó la muestra.
- `data/benchmark_grabado.csv`: ver §7.

## §4 Colecciones Qdrant

### `faq_kb`
- Vectores con nombre: `dense` (384, `Distance.COSINE`). Disperso con nombre: `bm25` (`SparseVectorParams(modifier=Modifier.IDF)`).
- `hnsw_config`: `m=16`, `ef_construct=100`.
- `quantization_config`: `ScalarQuantization(scalar=ScalarQuantizationConfig(type=ScalarType.INT8, quantile=0.99, always_ram=True))`.
- ID de punto: `row_id` (entero) → upsert idempotente.
- Payload: `row_id, instruction, response, category, intent, flags`.
- Índices de payload: `category` keyword, `intent` keyword, `instruction` text (tokenizer word, lowercase).
- Texto embebido (denso y disperso): `instruction`.

### `answer_cache`
- Vector con nombre `dense` (384, coseno). Sin disperso.
- ID: `uuid5(NAMESPACE_URL, pregunta_normalizada)`.
- Payload: `pregunta, respuesta, category, intent, modelo, creado_en` (ISO 8601).
- Índice de payload: `category` keyword.

## §5 API de `app/store/` (dueño: dev-datos)

```python
# app/store/cliente.py
def get_client() -> QdrantClient                 # singleton, usa QDRANT_URL y QDRANT_API_KEY
def probar_api_key() -> dict                     # {"sin_clave": int, "clave_incorrecta": int, "con_clave": int} códigos HTTP de GET {QDRANT_URL}/collections

# app/store/embeddings.py
def embed_denso(textos: list[str]) -> list[list[float]]
def embed_disperso(textos: list[str], consulta: bool = False) -> list[models.SparseVector]   # consulta=True usa query_embed (BM25 de consulta)

# app/store/colecciones.py
FAQ_KB = "faq_kb"; ANSWER_CACHE = "answer_cache"
def crear_colecciones(recrear: bool = False) -> None      # crea ambas según §4 si no existen
def info_coleccion(nombre: str) -> dict                   # {"puntos", "segmentos", "estado", "hnsw": {...}, "cuantizacion": {...}|None,
                                                          #  "vectores": {...}, "indices_payload": {...},
                                                          #  "memoria_estimada_mb": {"float32": float, "int8": float}}
def listar_colecciones() -> list[str]

# app/store/busquedas.py
@dataclass
class Resultado:
    id: int | str; score: float; instruction: str; response: str; category: str; intent: str

def buscar_denso(consulta: str | list[float], top_k: int = 5, category: str | None = None, intent: str | None = None) -> list[Resultado]
def buscar_disperso(consulta: str, top_k: int = 5, category: str | None = None, intent: str | None = None) -> list[Resultado]
def buscar_hibrido(consulta: str, top_k: int = 5, category: str | None = None, intent: str | None = None) -> list[Resultado]   # Prefetch dense+bm25 (limit 20 c/u) + FusionQuery RRF
def buscar_palabra_exacta(consulta: str, top_k: int = 5) -> list[Resultado]   # scroll con MatchText sobre "instruction"; score = 0.0
def recomendar(positivos: list[int], negativos: list[int], top_k: int = 5, estrategia: str = "average_vector") -> list[Resultado]
def listar_valores(campo: str, category: str | None = None) -> list[str]     # facet sobre "category" o "intent"
def obtener_punto(id: int) -> Resultado | None
def cache_buscar(vector: list[float], umbral: float) -> Resultado | None     # top-1 en answer_cache; None si score < umbral. instruction=pregunta, response=respuesta
def cache_guardar(pregunta: str, vector: list[float], respuesta: str, category: str, intent: str, modelo: str) -> None
```

## §6 Ingesta (`ingest/`, dueño: dev-datos)

- `python -m ingest.ingestar`: lee `MUESTRA_PATH`, llama `crear_colecciones()`, embebe denso y disperso en lotes de 64, hace upsert en `faq_kb`. Idempotente: si `faq_kb` ya tiene 3,000 puntos, imprime "ya ingerido" y sale con código 0. Imprime tiempo total. Sale con código ≠ 0 si falla.
- `ingest/preparar_muestra.py`: se corre una vez con internet para generar el parquet (no forma parte del arranque).
- `ingest/benchmark.py`: ver §7.

## §7 Soporte (`app/soporte/`, dueño: dev-app) y benchmark

```python
# app/soporte/ollama.py
@dataclass
class RespuestaLLM:
    texto: str; tokens_entrada: int; tokens_salida: int; latencia_ms: float   # de prompt_eval_count / eval_count
def disponible() -> bool                                   # GET {OLLAMA_URL}/api/tags, timeout 2 s, y el modelo está descargado
def chat(sistema: str, usuario: str, modelo: str | None = None) -> RespuestaLLM   # POST /api/chat, stream=false, temperature=0

# app/soporte/metricas.py
@dataclass
class MetricaNodo:
    nodo: str; tokens_entrada: int; tokens_salida: int; latencia_ms: float; cache_hit: bool = False
def cargar_precios() -> dict                               # lee PRICING_PATH
def costo_usd(tokens_entrada: int, tokens_salida: int, referencia: str) -> float

# app/soporte/grafo.py
@dataclass
class ResultadoConsulta:
    pregunta: str; respuesta: str; category: str; intent: str; cache_hit: bool; aprobado_qa: bool
    metricas: list[MetricaNodo]
    def tokens_totales(self) -> int
    def latencia_total_ms(self) -> float
def responder_con_qdrant(pregunta: str, umbral: float | None = None, llm=chat) -> ResultadoConsulta   # grafo LangGraph: triage → retriever → responder → qa
def responder_sin_qdrant(pregunta: str, llm=chat, categorias: list[str] | None = None) -> ResultadoConsulta    # LLM clasifica category; prompt con 30 FAQs de esa category leídas del parquet
```

- Nodos y nombres en `MetricaNodo.nodo`: `triage`, `retriever`, `responder`, `qa` (con Qdrant); `clasificador`, `responder` (sin Qdrant).
- Triage: `embed_denso` → `cache_buscar(umbral)`; acierto → fin con 0 tokens. Si no, voto mayoritario de `category`/`intent` entre los 5 vecinos de `buscar_denso`.
- Retriever: `buscar_denso(vector, top_k=3, category=...)`.
- Responder: responde en español solo con el contexto.
- QA: prompt corto, responde `SI` o `NO`; si `SI` → `cache_guardar`.
- `llm` es inyectable para tests (fake sin red).

`pricing.yaml`:
```yaml
moneda: USD
unidad: por_millon_tokens
modelos:
  <nombre>: {entrada: float, salida: float, nota: str}
```

`data/benchmark_grabado.csv` (generado por `python -m ingest.benchmark` con Ollama en el host):
columnas `pregunta_id, pregunta, grupo (original|parafrasis), modo (con_qdrant|sin_qdrant), cache_hit, tokens_entrada, tokens_salida, latencia_ms, category_predicha, category_real, modelo`. 100 preguntas en español (50 originales + 50 paráfrasis de esas mismas), cada una en ambos modos. Las preguntas viven en `ingest/preguntas_benchmark.yaml`.

## §8 UI (`app/main.py`, `app/ui/`, dueño: dev-app)

- `app/main.py`: `st.set_page_config(layout="wide")`, `st.tabs` con seis pestañas; cada una llama `render()` de su módulo.
- Módulos: `tab1_semantica.py`, `tab2_filtros.py`, `tab3_hibrida.py`, `tab4_recomendaciones.py`, `tab5_soporte.py`, `tab6_inspector.py`.
- Cada pestaña muestra una línea "Qué demuestra" y la latencia de la consulta en ms.
- Pestaña 1: consulta → columnas lado a lado `buscar_denso` vs `buscar_palabra_exacta`, con score.
- Pestaña 2: selectores de `category`/`intent` desde `listar_valores` → `buscar_denso` filtrado vs sin filtro.
- Pestaña 3: tres columnas denso / disperso / híbrido; resalta IDs que aparecen en una sola columna.
- Pestaña 4: elegir ejemplos positivos y negativos (de resultados de búsqueda) y estrategia → `recomendar`.
- Pestaña 5: si `disponible()` es falso → aviso + gráficos de `BENCHMARK_PATH`. Si es verdadero → consulta en ambos modos, tabla por nodo, KPIs (tokens totales, % ahorro, tasa de aciertos de caché, latencia, costo USD con selector de referencia de `pricing.yaml`), y también los gráficos del benchmark grabado.
- Pestaña 6: `listar_colecciones`, `info_coleccion` de ambas (HNSW, cuantización, memoria estimada float32 vs int8), enlace al dashboard, botón que ejecuta `probar_api_key` y muestra 401/403 sin clave vs 200 con clave.

## §9 Tests (`tests/`)

- Prefijos por dueño: `test_infra_*.py` (dev-infra), `test_store_*.py` y `test_ingest_*.py` (dev-datos), `test_soporte_*.py` y `test_ui_*.py` (dev-app).
- Tests de integración usan el Qdrant de compose; se marcan con `pytest.mark.integracion` y se saltan con mensaje claro si Qdrant no responde. Ningún test requiere Ollama (se usa LLM falso).
- Los tests **no destruyen datos**: nunca `crear_colecciones(recrear=True)` sobre `faq_kb`/`answer_cache`. Si `faq_kb` está vacía, la llenan con la ingesta idempotente. Los tests que necesitan colección propia usan nombres con prefijo `test_` y la borran al final. Los puntos que un test guarda en `answer_cache` se eliminan al terminar.
- `pytest.ini` (dueño: dev-infra) registra el marcador y `testpaths = tests`.

## §10 Convenciones

- Python 3.11, comentarios y docstrings en español (lo explica un estudiante en clase).
- Sin secretos en el repo. `.env` en `.gitignore`.
- Sin marcas de IA en código, comentarios ni commits.
