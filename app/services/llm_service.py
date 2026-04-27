from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.config import settings
from app.context.examples import ESTIMATION_EXAMPLES


class LLMConfigurationError(RuntimeError):
    """Raised when the selected LLM provider is not correctly configured."""


def build_system_prompt() -> str:
    examples = []
    for index, example in enumerate(ESTIMATION_EXAMPLES, start=1):
        examples.append(
            "\n".join(
                [
                    f"### Ejemplo historico {index}",
                    "Resumen de la reunion:",
                    example["meeting_summary"],
                    "",
                    "Estimacion generada:",
                    example["estimation"],
                ]
            )
        )

    examples_block = "\n\n---\n\n".join(examples)

    return f"""
Eres un estimador de software experto. Generas estimaciones claras, realistas y
accionables a partir de transcripciones de reuniones con clientes.

Usa los ejemplos historicos como referencia de formato, nivel de detalle,
criterios de desglose, riesgos y recomendaciones de equipo. No copies los
ejemplos literalmente: adaptalos al alcance de la nueva transcripcion.

Tu respuesta debe estar en espanol y seguir esta estructura:
- Titulo de la estimacion
- Supuestos principales
- Desglose de tareas con horas
- Total estimado
- Equipo recomendado
- Duracion estimada
- Riesgos y puntos abiertos

Contexto estatico de estimaciones previas:

{examples_block}
""".strip()


def build_user_prompt(transcription: str) -> str:
    return f"""
Genera una estimacion de software para la siguiente transcripcion de reunion.

Transcripcion:
{transcription}
""".strip()


async def generate_estimation(transcription: str) -> str:
    provider = settings.llm_provider

    if provider == "openai":
        return await _generate_with_openai(transcription)

    if provider == "anthropic":
        return await _generate_with_anthropic(transcription)

    raise LLMConfigurationError(f"Proveedor LLM no soportado: {provider}")


async def _generate_with_openai(transcription: str) -> str:
    if not settings.openai_api_key:
        raise LLMConfigurationError("OPENAI_API_KEY no esta configurada.")

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.responses.create(
        model=settings.llm_model,
        instructions=build_system_prompt(),
        input=build_user_prompt(transcription),
        temperature=0.2,
        store=False,
    )

    content = response.output_text
    if not content:
        raise RuntimeError("El modelo no devolvio contenido.")

    return content


async def _generate_with_anthropic(transcription: str) -> str:
    if not settings.anthropic_api_key:
        raise LLMConfigurationError("ANTHROPIC_API_KEY no esta configurada.")

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.llm_model,
        max_tokens=1600,
        temperature=0.2,
        system=build_system_prompt(),
        messages=[
            {"role": "user", "content": build_user_prompt(transcription)},
        ],
    )

    text_blocks = [
        block.text for block in response.content if getattr(block, "type", None) == "text"
    ]
    if not text_blocks:
        raise RuntimeError("El modelo no devolvio contenido.")

    return "\n".join(text_blocks)
