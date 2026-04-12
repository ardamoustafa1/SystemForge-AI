import json

from pydantic import ValidationError

from app.schemas.design import DesignOutputPayload


class LLMOutputParseError(Exception):
    pass


def parse_structured_output(raw_output: str) -> DesignOutputPayload:
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise LLMOutputParseError("Model output is not valid JSON") from exc

    try:
        return DesignOutputPayload.model_validate(data)
    except ValidationError as exc:
        raise LLMOutputParseError("Model JSON failed schema validation") from exc
