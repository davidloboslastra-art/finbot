# Finbot

Asistente de educación financiera para Chile (FastAPI).

- Calcula cuota de crédito (sistema francés), ahorro para una meta e interés compuesto.
- Glosario: UF, CAE, APV, inflación, fondo mutuo.
- Preguntas abiertas: usa OpenAI solo si defines `OPENAI_API_KEY`.

## Uso

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # opcional: agrega tu OPENAI_API_KEY
uvicorn app.main:app --reload --env-file .env
```

Abre http://127.0.0.1:8000

## API

- `GET /health` → `{"status": "ok"}`
- `POST /chat` con `{"mensaje": "..."}` → `{"respuesta": "...", "fuente": "calculo|glosario|openai|reglas"}`

Ejemplos: «cuota de $10 millones al 12% a 36 meses», «quiero ahorrar $5.000.000 en 2 años al 4%»,
«interés compuesto de $1.000.000 al 6% por 10 años», «qué es el CAE».

## Despliegue

URL pública (Cloud Run, southamerica-west1): https://finbot-116705909722.southamerica-west1.run.app
