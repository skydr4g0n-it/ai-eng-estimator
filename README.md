# Estimator

Aplicacion FastAPI dockerizada que recibe la transcripcion de una reunion y
genera una estimacion de software con un LLM. Usa arquitectura CAG: los ejemplos
historicos viven en `app/context/examples.py` y se inyectan directamente en el
prompt de cada llamada.

Los contratos HTTP (cuerpos de peticion, respuestas, validacion) estan en
`app/schemas/`; los routers solo orquestan y referencian esos modelos.

## Estructura

```text
estimator/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── estimations.py
│   ├── routers/
│   │   └── estimations.py
│   ├── services/
│   │   └── llm_service.py
│   └── context/
│       └── examples.py
├── tests/
├── transcripts/
│   └── meeting_transcription.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Configuracion

Copia `.env.example` a `.env` y completa la clave del proveedor que vayas a
usar:

```dotenv
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
APP_ENV=development
LOG_LEVEL=DEBUG
```

Para Anthropic, cambia `LLM_PROVIDER=anthropic` y usa un modelo compatible,
por ejemplo `claude-haiku-4-5`.

## Ejecutar con Docker

La forma principal de ejecutar el proyecto es Docker:

```bash
docker compose up --build api
```

Endpoints principales:

- `GET /health`
- `POST /api/v1/estimate`
- Swagger UI: `http://localhost:8000/docs`

Ejemplo con `curl`:

```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "transcription": "En la reunion con el equipo de marketing, el cliente explico que necesita una landing page con formulario de contacto, integracion con HubSpot, y una seccion de blog con editor WYSIWYG. El plazo ideal seria tenerlo listo en 4 semanas. El diseno ya existe en Figma."
  }'
```

Tambien hay una transcripcion de ejemplo en
`transcripts/meeting_transcription.txt`.

## Validacion automatica

La validacion local comprueba que la estructura base existe, que `.env` esta
ignorado, que Docker esta configurado y que los endpoints principales funcionan
con un mock del LLM:

```bash
docker compose run --rm tests
```

El pipeline de GitHub Actions en `.github/workflows/ci.yml` construye la imagen
Docker y ejecuta la misma validacion en cada push a `main` y en cada pull
request.

## Variables de entorno

| Variable | Descripcion | Valor por defecto |
| --- | --- | --- |
| `OPENAI_API_KEY` | API key de OpenAI | Sin default |
| `ANTHROPIC_API_KEY` | API key de Anthropic | Sin default |
| `LLM_PROVIDER` | Proveedor a utilizar: `openai` o `anthropic` | `openai` |
| `LLM_MODEL` | Modelo a utilizar | `gpt-4o-mini` |
| `APP_ENV` | Entorno de ejecucion | `development` |
| `LOG_LEVEL` | Nivel de logging | `DEBUG` |
