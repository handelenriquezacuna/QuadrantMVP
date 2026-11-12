# Criterios de aceptación (los verifica el Certificador)

1. Desde un clon limpio, `cp .env.example .env` y `docker compose up` dejan la app en `http://localhost:8501` sin pasos manuales adicionales.
2. Las pestañas 1, 2, 3, 4 y 6 funcionan sin Ollama instalado.
3. Una pregunta en español devuelve FAQs relevantes en inglés en la pestaña 1.
4. La pestaña 3 muestra resultados distintos entre denso, disperso e híbrido para una misma consulta.
5. Una petición a Qdrant sin API key es rechazada, y la pestaña 6 lo demuestra.
6. Con Ollama, preguntar dos veces lo mismo con distinta redacción da acierto de caché con 0 tokens la segunda vez.
7. Sin Ollama, la pestaña 5 muestra el benchmark grabado sin errores.
8. `docker compose run --rm app pytest` pasa.
9. El README tiene: requisitos, arranque en 3 comandos, diagrama Mermaid de la arquitectura, y un guion de demo de 4 minutos (qué mostrar en cada pestaña y qué número señalar).
10. `docs/LIBRO_TOKENS.md` y `docs/CERTIFICADO.md` existen y están completos.
11. Con `docker compose --profile llm up` y **sin Ollama instalado en el host**, el criterio 6 pasa. (Agregado por cambio de alcance, D-17.)
