"""Minimal hand inpainting workflow trigger for external ComfyUI."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable
from urllib.request import urlopen

from color_rough_ref_tool.core.settings import AppSettings
from color_rough_ref_tool.integrations.comfyui.prediction import (
    ComfyUIPromptResult,
    queue_comfyui_prompt,
)


HAND_REFERENCE_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})
SELECTED_CANDIDATE_IMAGE_PATH_PLACEHOLDER = "{{SELECTED_CANDIDATE_IMAGE_PATH}}"
SELECTED_CANDIDATE_IMAGE_PLACEHOLDER = "{{SELECTED_CANDIDATE_IMAGE}}"
HAND_MASK_IMAGE_PATH_PLACEHOLDER = "{{HAND_MASK_IMAGE_PATH}}"
HAND_MASK_IMAGE_PLACEHOLDER = "{{HAND_MASK_IMAGE}}"
SELECTED_CANDIDATE_PLACEHOLDERS = (
    SELECTED_CANDIDATE_IMAGE_PATH_PLACEHOLDER,
    SELECTED_CANDIDATE_IMAGE_PLACEHOLDER,
)
HAND_MASK_PLACEHOLDERS = (
    HAND_MASK_IMAGE_PATH_PLACEHOLDER,
    HAND_MASK_IMAGE_PLACEHOLDER,
)


@dataclass(frozen=True, slots=True)
class HandReferenceOutputImage:
    """A generated hand reference image found in an output folder."""

    path: Path
    file_name: str
    file_size_bytes: int
    modified_time: float


def trigger_hand_inpainting_workflow(
    settings: AppSettings,
    *,
    selected_candidate_path: Path | str | None = None,
    mask_path: Path | str | None = None,
    client_id: str | None = None,
    timeout_seconds: float = 30,
    opener: Callable[..., Any] = urlopen,
) -> ComfyUIPromptResult:
    """Load the configured hand inpainting workflow and queue it in external ComfyUI."""

    if (selected_candidate_path is None) != (mask_path is None):
        raise ValueError("Both selected candidate path and mask path are required.")

    workflow = load_hand_inpainting_workflow(settings.hand_inpainting_workflow_path)
    if selected_candidate_path is not None and mask_path is not None:
        workflow = inject_hand_inpainting_paths(
            workflow,
            selected_candidate_path=selected_candidate_path,
            mask_path=mask_path,
        )
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


def read_hand_reference_outputs(output_dir: Path | str) -> tuple[HandReferenceOutputImage, ...]:
    """Read generated hand reference image files from an output folder."""

    folder = Path(output_dir)
    if not folder.exists():
        raise FileNotFoundError(f"Hand reference output folder does not exist: {folder}")
    if not folder.is_dir():
        raise ValueError(f"Hand reference output path must be a folder: {folder}")

    images: list[HandReferenceOutputImage] = []
    for path in sorted(folder.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in HAND_REFERENCE_IMAGE_EXTENSIONS:
            continue
        stat = path.stat()
        images.append(
            HandReferenceOutputImage(
                path=path,
                file_name=path.name,
                file_size_bytes=stat.st_size,
                modified_time=stat.st_mtime,
            )
        )

    return tuple(images)


def inject_hand_inpainting_paths(
    workflow: dict[str, Any],
    *,
    selected_candidate_path: Path | str,
    mask_path: Path | str,
) -> dict[str, Any]:
    """Return a workflow with selected candidate and mask placeholders replaced."""

    selected_path = _existing_file_path(
        selected_candidate_path,
        "Selected candidate image",
    )
    hand_mask_path = _existing_file_path(mask_path, "Hand mask image")

    replacements = {
        placeholder: selected_path
        for placeholder in SELECTED_CANDIDATE_PLACEHOLDERS
    }
    replacements.update(
        {
            placeholder: hand_mask_path
            for placeholder in HAND_MASK_PLACEHOLDERS
        }
    )
    return _replace_placeholders(workflow, replacements)


def _existing_file_path(path: Path | str, label: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"{label} does not exist: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"{label} path must be a file: {file_path}")
    return file_path.resolve().as_posix()


def _replace_placeholders(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        replaced = value
        for placeholder, replacement in replacements.items():
            replaced = replaced.replace(placeholder, replacement)
        return replaced
    if isinstance(value, list):
        return [
            _replace_placeholders(item, replacements)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _replace_placeholders(item, replacements)
            for key, item in value.items()
        }
    return value
