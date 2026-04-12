import time
import logging

from app.core.config import get_settings
from app.llm.client import LLMClientError, create_structured_response
from app.llm.fallback import build_fallback_output
from app.llm.output_finalize import finalize_design_output
from app.llm.parser import LLMOutputParseError, parse_structured_output
from app.llm.prompt_builder import build_system_prompt, build_user_prompt
from app.schemas.design import DesignInputPayload, DesignOutputPayload, ScaleStance

logger = logging.getLogger("systemforge.generation")


async def generate_structured_design(
    input_payload: DesignInputPayload,
    *,
    scale_stance: ScaleStance = "balanced",
) -> tuple[DesignOutputPayload, int, str]:
    settings = get_settings()
    started = time.perf_counter()

    def _done(payload: DesignOutputPayload, elapsed_ms: int, model_name: str) -> tuple[DesignOutputPayload, int, str]:
        finalized = finalize_design_output(payload, input_payload, scale_stance=scale_stance)
        return finalized, elapsed_ms, model_name

    if not settings.openai_api_key:
        fallback = build_fallback_output(input_payload, scale_stance=scale_stance)
        elapsed = int((time.perf_counter() - started) * 1000)
        logger.info(
            "generation_fallback_no_api_key",
            extra={"project_title": input_payload.project_title, "elapsed_ms": elapsed},
        )
        return _done(fallback, elapsed, "fallback-no-api-key")

    system_prompt = build_system_prompt(scale_stance)
    user_prompt = build_user_prompt(input_payload, scale_stance)

    try:
        raw = await create_structured_response(system_prompt=system_prompt, user_prompt=user_prompt)
        parsed = parse_structured_output(raw)
    except (LLMClientError, LLMOutputParseError) as exc:
        logger.warning(
            "generation_fallback_recovered",
            extra={"project_title": input_payload.project_title, "error": str(exc)},
        )
        parsed = build_fallback_output(input_payload, scale_stance=scale_stance)
        elapsed = int((time.perf_counter() - started) * 1000)
        return _done(parsed, elapsed, "fallback-recovered")

    elapsed = int((time.perf_counter() - started) * 1000)
    logger.info(
        "generation_success",
        extra={"project_title": input_payload.project_title, "elapsed_ms": elapsed, "model": settings.openai_model},
    )
    return _done(parsed, elapsed, settings.openai_model)
