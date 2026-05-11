"""Minimal hand inpainting workflow trigger for external ComfyUI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable
from urllib.request import urlopen

from color_rough_ref_tool.core.settings import AppSettings
from color_rough_ref_tool.integrations.comfyui.prediction import (
    ComfyUIPromptResult,
    queue_comfyui_prompt,
)


def trigger_hand_inpainting_workflow(
    settings: AppSettings,
    *,
    client_id: str | None = None,
    timeout_seconds: float = 30,
    opener: Callable[..., Any] = urlopen,
) -> ComfyUIPromptResult:
    """Load the configured hand inpainting workflow and queue it in external ComfyUI."""

    workflow = load_hand_inpainting_workflow(settings.hand_inpainting_workflow_path)
    return queue_comfyui_prompt(
        endpoint=settings.comfyui_endpoint,
        workflow=workflow,
        client_id=client_id,
        timeout_seconds=timeout_seconds,
        opener=opener,
    )


def load_hand_inpainting_workflow(workflow_path: Path | str) -> dict[str, Any]:
    """Load a user-provided ComfyUI hand inpainting workflow JSON file."""

    path = Path(workflow_path)
    if not path.exists():
        raise FileNotFoundError(f"Hand inpainting workflow file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Hand inpainting workflow path must be a file: {path}")

    try:
        workflow = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Hand inpainting workflow file is not valid JSON: {path}") from error

    if not isinstance(workflow, dict):
        raise ValueError(f"Hand inpainting workflow file must contain a JSON object: {path}")
    if workflow.get("placeholder") is True:
        raise ValueError(f"Hand inpainting workflow placeholder must be replaced: {path}")

    return workflow
