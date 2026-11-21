"""Small Responses API adapter with local-only secret loading."""

from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path
from typing import Protocol, TypeVar

from openai import OpenAI
from openai.types.responses import (
    EasyInputMessageParam,
    ResponseInputImageParam,
    ResponseInputMessageContentListParam,
    ResponseInputParam,
    ResponseInputTextParam,
)
from pydantic import BaseModel, ValidationError

from .errors import InvalidReaderOutput, ReaderConfigurationError

T = TypeVar("T", bound=BaseModel)


class StructuredReader(Protocol):
    def generate(
        self,
        schema: type[T],
        *,
        developer: str,
        user_text: str,
        image_refs: list[str] | None = None,
    ) -> T: ...


def load_api_key(project_root: str | Path = ".") -> str:
    """Read OPENAI_API_KEY from exactly <project_root>/.env, never the process env."""
    env_path = Path(project_root).resolve() / ".env"
    if not env_path.is_file():
        raise ReaderConfigurationError(
            "./.env is missing; cannot call the reader model"
        )
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == "OPENAI_API_KEY":
            key = value.strip().strip('"').strip("'")
            if key:
                return key
    raise ReaderConfigurationError("OPENAI_API_KEY is missing from ./.env")


class OpenAIReaderClient:
    def __init__(
        self,
        *,
        project_root: str | Path = ".",
        image_root: str | Path = "data/listings",
        model: str = "gpt-6.2-sol",
        sdk_client: OpenAI | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        configured_image_root = Path(image_root)
        if not configured_image_root.is_absolute():
            configured_image_root = self.project_root / configured_image_root
        self.image_root = configured_image_root.resolve()
        self.model = model
        self._client = sdk_client or OpenAI(api_key=load_api_key(self.project_root))

    def generate(
        self,
        schema: type[T],
        *,
        developer: str,
        user_text: str,
        image_refs: list[str] | None = None,
    ) -> T:
        user_content: ResponseInputMessageContentListParam = [
            ResponseInputTextParam(type="input_text", text=user_text)
        ]
        for ref in image_refs or []:
            user_content.append(
                ResponseInputImageParam(
                    type="input_image",
                    image_url=self._image_data_url(ref),
                    detail="auto",
                )
            )
        schema_name = re.sub(r"[^A-Za-z0-9_-]", "_", schema.__name__)[:64]
        request_input: ResponseInputParam = [
            EasyInputMessageParam(
                role="developer",
                content=[ResponseInputTextParam(type="input_text", text=developer)],
            ),
            EasyInputMessageParam(role="user", content=user_content),
        ]
        response = self._client.responses.create(
            model=self.model,
            reasoning={"effort": "medium"},
            input=request_input,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema.model_json_schema(),
                }
            },
            store=False,
        )
        try:
            raw = json.loads(response.output_text)
            return schema.model_validate(raw)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise InvalidReaderOutput(
                "model output failed JSON schema validation"
            ) from exc

    def _image_data_url(self, ref: str) -> str:
        if ref.startswith("data:"):
            if not re.match(r"^data:image/(?:png|jpeg|webp|gif);base64,", ref):
                raise ReaderConfigurationError("image data URL has an unsupported type")
            if len(ref) > 27_000_000:
                raise ReaderConfigurationError("captured image exceeds the 20 MB limit")
            return ref
        path = Path(ref)
        if not path.is_absolute():
            path = self.project_root / path
        path = path.resolve()
        try:
            path.relative_to(self.image_root)
        except ValueError as exc:
            raise ReaderConfigurationError(
                "captured image must be inside data/listings"
            ) from exc
        if not path.is_file():
            raise ReaderConfigurationError(f"captured image is missing: {ref}")
        mime = mimetypes.guess_type(path.name)[0]
        if mime not in {"image/png", "image/jpeg", "image/webp", "image/gif"}:
            raise ReaderConfigurationError("captured image has an unsupported type")
        raw = path.read_bytes()
        if len(raw) > 20_000_000:
            raise ReaderConfigurationError("captured image exceeds the 20 MB limit")
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{encoded}"
