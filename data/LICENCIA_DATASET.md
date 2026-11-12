# Dataset de la muestra

- **Fuente:** https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset
  (archivo `Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv`, 26,872 filas).
- **Licencia:** CDLA-Sharing-1.0 (Community Data License Agreement, Sharing). La muestra
  derivada se distribuye bajo la misma licencia y se atribuye a Bitext.
- **Cómo se generó:** `python -I ingest/preparar_muestra.py RUTA_CSV` toma 3,000 filas con
  muestreo estratificado por `intent` (cuota proporcional, mínimo 1 por intent, `random_state=42`),
  las mezcla y asigna `row_id` de 0 a 2999. Es reproducible: mismo CSV, mismo parquet.
