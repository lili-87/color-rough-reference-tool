"""Minimal prediction workflow trigger for external ComfyUI."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
from typing import Any, Callable
from urllib.parse import quote
from urllib.error import URLError
from urllib.request import Request, urlopen

from color_rough_ref_tool.core.prompt_metadata import load_latest_prediction_prompt_metadata
from color_rough_ref_tool.core.settings import AppSettings, normalize_comfyui_endpoint


PROMPT_ENDPOINT_PATH = "/prompt"
HISTORY_ENDPOINT_PATH = "/history"
PREDICTION_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})
COLOR_ROUGH_IMAGE_PATH_PLACEHOLDER = "{{COLOR_ROUGH_IMAGE_PATH}}"
COLOR_ROUGH_IMAGE_PLACEHOLDER = "{{COLOR_ROUGH_IMAGE}}"
COLOR_ROUGH_PLACEHOLDERS = (
    COLOR_ROUGH_IMAGE_PATH_PLACEHOLDER,
    COLOR_ROUGH_IMAGE_PLACEHOLDER,
)


@dataclass(frozen=True, slots=True)
class ComfyUIPromptResult:
    """Result returned after ComfyUI accepts a queued prompt."""

    prompt_id: str
    response: dict[str, Any]


@dataclass(frozen=True, slots=True)
class PredictionOutputImage:
    """A generated prediction image found in an output folder."""

    path: Path
    file_name: str
    file_size_bytes: int
    modified_time: float


@dataclass(frozen=True, slots=True)
class PredictionOutputReadResult:
    """Safe result for reading prediction output images."""

    images: tuple[PredictionOutputImage, ...]
    messages: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.messages


@dataclass(frozen=True, slots=True)
class SavedPredictionCandidate:
    """A selected prediction candidate copied into the project output."""

    source_path: Path
    saved_path: Path


@dataclass(frozen=True, slots=True)
class ComfyUIHistoryResult:
    """Raw ComfyUI history response for one prompt ID."""

    prompt_id: str
    history: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ComfyUIHistoryImage:
    """One image output reported by ComfyUI history."""

    file_name: str
    subfolder: str
    image_type: str


@dataclass(frozen=True, slots=True)
class PredictionHistoryInspection:
    """Small parsed status for one prediction history response."""

    prompt_id: str
    completed: bool
    images: tuple[ComfyUIHistoryImage, ...]


def trigger_prediction_workflow(
    settings: AppSettings,
    *,
    color_rough_path: Path | str | None = None,
    client_id: str | None = None,
    timeout_seconds: float = 30,
    opener: Callable[..., Any] = urlopen,
) -> ComfyUIPromptResult:
    """Load the configured prediction workflow and queue it in external ComfyUI."""

    workflow = load_prediction_workflow(settings.prediction_workflow_path)
    if color_rough_path is not None:
        workflow = inject_color_rough_path(workflow, color_rough_path)
    return queue_comfyui_prompt(
        endpoint=settings.comfyui_endpoint,
        workflow=workflow,
        client_id=client_id,
        timeout_seconds=timeout_seconds,
        opener=opener,
    )


def load_prediction_workflow(workflow_path: Path | str) -> dict[str, Any]:
    """Load a user-provided ComfyUI prediction workflow JSON file."""

    path = Path(workflow_path)
    if not path.exists():
        raise FileNotFoundError(f"Prediction workflow file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Prediction workflow path must be a file: {path}")

    try:
        workflow = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Prediction workflow file is not valid JSON: {path}") from error

    if not isinstance(workflow, dict):
        raise ValueError(f"Prediction workflow file must contain a JSON object: {path}")
    if workflow.get("placeholder") is True:
        raise ValueError(f"Prediction workflow placeholder must be replaced: {path}")

    return workflow


def inject_color_rough_path(
    workflow: dict[str, Any],
    color_rough_path: Path | str,
) -> dict[str, Any]:
    """Return a workflow with color rough placeholders replaced by the image path."""

    image_path = Path(color_rough_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Color rough image does not exist: {image_path}")
    if not image_path.is_file():
        raise ValueError(f"Color rough path must be a file: {image_path}")

    normalized_image_path = image_path.resolve().as_posix()
    return _replace_color_rough_placeholders(workflow, normalized_image_path)


def read_prediction_outputs(output_dir: Path | str) -> tuple[PredictionOutputImage, ...]:
    """Read generated prediction image files from an output folder."""

    folder = Path(output_dir)
    if not folder.exists():
        raise FileNotFoundError(f"Prediction output folder does not exist: {folder}")
    if not folder.is_dir():
        raise ValueError(f"Prediction output path must be a folder: {folder}")

    images: list[PredictionOutputImage] = []
    for path in sorted(folder.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in PREDICTION_IMAGE_EXTENSIONS:
            continue
        stat = path.stat()
        images.append(
            PredictionOutputImage(
                path=path,
                file_name=path.name,
                file_size_bytes=stat.st_size,
                modified_time=stat.st_mtime,
            )
        )

    return tuple(images)


def read_prediction_outputs_safely(output_dir: Path | str) -> PredictionOutputReadResult:
    """Read prediction outputs and return messages instead of raising for UI use."""

    try:
        images = read_prediction_outputs(output_dir)
    except (FileNotFoundError, OSError, ValueError) as error:
        return PredictionOutputReadResult(images=(), messages=(str(error),))

    if not images:
        return PredictionOutputReadResult(
            images=(),
            messages=(f"No prediction images were found in: {Path(output_dir)}",),
        )

    return PredictionOutputReadResult(images=images, messages=())


def fetch_comfyui_history(
    *,
    endpoint: str,
    prompt_id: str,
    timeout_seconds: float = 30,
    opener: Callable[..., Any] = urlopen,
) -> ComfyUIHistoryResult:
    """Fetch ComfyUI history once for a prompt ID."""

    normalized_prompt_id = prompt_id.strip()
    if not normalized_prompt_id:
        raise ValueError("ComfyUI history prompt ID must not be empty.")

    request = Request(
        _history_url(endpoint, normalized_prompt_id),
        method="GET",
    )

    try:
        with opener(request, timeout=timeout_seconds) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except URLError as error:
        raise ConnectionError(f"Could not reach ComfyUI endpoint: {endpoint}") from error
    except json.JSONDecodeError as error:
        raise ValueError("ComfyUI history response was not valid JSON.") from error

    if not isinstance(response_data, dict):
        raise ValueError("ComfyUI history response must be a JSON object.")

    return ComfyUIHistoryResult(
        prompt_id=normalized_prompt_id,
        history=response_data,
    )


def fetch_latest_prediction_history(
    settings: AppSettings,
    metadata_dir: Path | str,
    *,
    timeout_seconds: float = 30,
    opener: Callable[..., Any] = urlopen,
) -> ComfyUIHistoryResult:
    """Fetch ComfyUI history once using the saved latest prediction prompt ID."""

    metadata = load_latest_prediction_prompt_metadata(metadata_dir)
    return fetch_comfyui_history(
        endpoint=settings.comfyui_endpoint,
        prompt_id=metadata.prompt_id,
        timeout_seconds=timeout_seconds,
        opener=opener,
    )


def inspect_prediction_history(
    history_result: ComfyUIHistoryResult,
) -> PredictionHistoryInspection:
    """Detect completion and image outputs from a ComfyUI history response."""

    prompt_history = history_result.history.get(history_result.prompt_id)
    if not isinstance(prompt_history, dict):
        return PredictionHistoryInspection(
            prompt_id=history_result.prompt_id,
            completed=False,
            images=(),
        )

    return PredictionHistoryInspection(
        prompt_id=history_result.prompt_id,
        completed=_history_entry_is_completed(prompt_history),
        images=_history_entry_images(prompt_history),
    )


def save_selected_prediction_candidate(
    candidate_path: Path | str,
    selected_dir: Path | str,
) -> SavedPredictionCandidate:
    """Copy a selected prediction image into the project selected folder."""

    source_path = Path(candidate_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Selected prediction does not exist: {source_path}")
    if not source_path.is_file():
        raise ValueError(f"Selected prediction path must be a file: {source_path}")
    if source_path.suffix.lower() not in PREDICTION_IMAGE_EXTENSIONS:
        raise ValueError(f"Selected prediction must be a supported image file: {source_path}")

    destination_dir = Path(selected_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    saved_path = destination_dir / source_path.name
    shutil.copy2(source_path, saved_path)

    return SavedPredictionCandidate(source_path=source_path, saved_path=saved_path)


def queue_comfyui_prompt(
    *,
    endpoint: str,
    workflow: dict[str, Any],
    client_id: str | None = None,
    timeout_seconds: float = 30,
    opener: Callable[..., Any] = urlopen,
) -> ComfyUIPromptResult:
    """Send a workflow prompt to ComfyUI's /prompt endpoint."""

    payload: dict[str, Any] = {"prompt": workflow}
    if client_id is not None:
        payload["client_id"] = client_id

    request = Request(
        _prompt_url(endpoint),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with opener(request, timeout=timeout_seconds) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except URLError as error:
        raise ConnectionError(f"Could not reach ComfyUI endpoint: {endpoint}") from error
    except json.JSONDecodeError as error:
        raise ValueError("ComfyUI returned a response that was not valid JSON.") from error

    if not isinstance(response_data, dict):
        raise ValueError("ComfyUI response must be a JSON object.")

    prompt_id = response_data.get("prompt_id")
    if not isinstance(prompt_id, str) or not prompt_id:
        raise ValueError("ComfyUI response did not include a prompt_id.")

    return ComfyUIPromptResult(prompt_id=prompt_id, response=response_data)


def _prompt_url(endpoint: str) -> str:
    return f"{normalize_comfyui_endpoint(endpoint)}{PROMPT_ENDPOINT_PATH}"


def _history_url(endpoint: str, prompt_id: str) -> str:
    escaped_prompt_id = quote(prompt_id, safe="")
    return f"{normalize_comfyui_endpoint(endpoint)}{HISTORY_ENDPOINT_PATH}/{escaped_prompt_id}"


def _history_entry_is_completed(prompt_history: dict[str, Any]) -> bool:
    status = prompt_history.get("status")
    if isinstance(status, dict) and status.get("completed") is True:
        return True
    return False


def _history_entry_images(prompt_history: dict[str, Any]) -> tuple[ComfyUIHistoryImage, ...]:
    outputs = prompt_history.get("outputs")
    if not isinstance(outputs, dict):
        return ()

    images: list[ComfyUIHistoryImage] = []
    for output in outputs.values():
        if not isinstance(output, dict):
            continue
        raw_images = output.get("images")
        if not isinstance(raw_images, list):
            continue
        for raw_image in raw_images:
            image = _history_image_from_raw(raw_image)
            if image is not None:
                images.append(image)
    return tuple(images)


def _history_image_from_raw(raw_image: Any) -> ComfyUIHistoryImage | None:
    if not isinstance(raw_image, dict):
        return None

    file_name = raw_image.get("filename")
    if not isinstance(file_name, str) or not file_name:
        return None
    if Path(file_name).suffix.lower() not in PREDICTION_IMAGE_EXTENSIONS:
        return None

    subfolder = raw_image.get("subfolder", "")
    image_type = raw_image.get("type", "")
    return ComfyUIHistoryImage(
        file_name=file_name,
        subfolder=subfolder if isinstance(subfolder, str) else "",
        image_type=image_type if isinstance(image_type, str) else "",
    )


def _replace_color_rough_placeholders(value: Any, image_path: str) -> Any:
    if isinstance(value, str):
        replaced = value
        for placeholder in COLOR_ROUGH_PLACEHOLDERS:
            replaced = replaced.replace(placeholder, image_path)
        return replaced
    if isinstance(value, list):
        return [
            _replace_color_rough_placeholders(item, image_path)
            for item in value
        ]
    if isinstance(value, dict):
        return {
            key: _replace_color_rough_placeholders(item, image_path)
            for key, item in value.items()
        }
    return value
