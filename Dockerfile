FROM python:3.11.11-slim-bookworm

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FASTEMBED_CACHE_PATH=/models

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Hornea ambos modelos en /models durante el build
RUN python -c "from fastembed import TextEmbedding, SparseTextEmbedding; \
TextEmbedding('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', cache_dir='/models'); \
SparseTextEmbedding('Qdrant/bm25', cache_dir='/models')"

# Copia app/, ingest/, tests/, data/ y pricing.yaml (lo no listado se excluye en .dockerignore)
COPY . /app
