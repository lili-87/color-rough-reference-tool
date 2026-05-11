"""Basic JSON settings storage for the application."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_SETTINGS_PATH = Path("settings") / "settings.json"
WORKFLOW_FILE_EXTENSION = ".json"


@dataclass(slots=True)
class AppSettings:
    """User-editable settings for local generation workflows."""

    comfyui_endpoint: str = "http://127.0.0.1:8188"
    prediction_workflow_path: str = "workflows/prediction_workflow.json"
    hand_inpainting_workflow_path: str = "workflows/hand_inpainting_workflow.json"
    default_output_dir: str = "project_output"


@dataclass(frozen=True, slots=True)
class ComfyUIConfigurationCheck:
    """Result of checking the minimum ComfyUI-related settings."""

    ok: bool
    errors: tuple[str, ...]


def with_comfyui_endpoint(settings: AppSettings, endpoint: str) -> AppSettings:
    """Return settings with an updated ComfyUI endpoint."""

    normalized_endpoint = normalize_comfyui_endpoint(endpoint)
    return AppSettings(
        comfyui_endpoint=normalized_endpoint,
        prediction_workflow_path=settings.prediction_workflow_path,
        hand_inpainting_workflow_path=settings.hand_inpainting_workflow_path,
        default_output_dir=settings.default_output_dir,
    )


def with_prediction_workflow_path(
    settings: AppSettings,
    workflow_path: Path | str,
) -> AppSettings:
    """Return settings with an updated prediction workflow path."""

    normalized_path = normalize_workflow_file_path(workflow_path)
    return AppSettings(
        comfyui_endpoint=settings.comfyui_endpoint,
        prediction_workflow_path=normalized_path,
        hand_inpainting_workflow_path=settings.hand_inpainting_workflow_path,
        default_output_dir=settings.default_output_dir,
    )


def with_hand_inpainting_workflow_path(
    settings: AppSettings,
    workflow_path: Path | str,
) -> AppSettings:
    """Return settings with an updated hand inpainting workflow path."""

    normalized_path = normalize_workflow_file_path(workflow_path)
    return AppSettings(
        comfyui_endpoint=settings.comfyui_endpoint,
        prediction_workflow_path=settings.prediction_workflow_path,
        hand_inpainting_workflow_path=normalized_path,
        default_output_dir=settings.default_output_dir,
    )


def normalize_comfyui_endpoint(endpoint: str) -> str:
    """Validate and normalize a ComfyUI HTTP endpoint."""

    normalized_endpoint = endpoint.strip().rstrip("/")
    parsed = urlparse(normalized_endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(
            "ComfyUI endpoint must be an http or https URL, "
            "for example http://127.0.0.1:8188"
        )
    return normalized_endpoint


def normalize_workflow_file_path(workflow_path: Path | str) -> str:
    """Validate and normalize a ComfyUI workflow JSON file path."""

    normalized_path = Path(str(workflow_path).strip())
    if not str(normalized_path):
        raise ValueError("Workflow file path must not be empty.")
    if normalized_path.suffix.lower() != WORKFLOW_FILE_EXTENSION:
        raise ValueError("Workflow file path must point to a .json file.")
    if normalized_path.exists() and normalized_path.is_dir():
        raise ValueError(f"Workflow file path must not be a directory: {normalized_path}")
    return normalized_path.as_posix()


def check_comfyui_configuration(settings: AppSettings) -> ComfyUIConfigurationCheck:
    """Check the minimum local ComfyUI configuration without connecting to ComfyUI."""

    errors: list[str] = []

    try:
        normalize_comfyui_endpoint(settings.comfyui_endpoint)
    except ValueError as error:
        errors.append(f"ComfyUI endpoint: {error}")

    try:
        normalize_workflow_file_path(settings.prediction_workflow_path)
    except ValueError as error:
        errors.append(f"Prediction workflow file: {error}")

    try:
        normalize_workflow_file_path(settings.hand_inpainting_workflow_path)
    except ValueError as error:
        errors.append(f"Hand inpainting workflow file: {error}")

    return ComfyUIConfigurationCheck(ok=not errors, errors=tuple(errors))


def load_settings(path: Path | str = DEFAULT_SETTINGS_PATH) -> AppSettings:
    """Load settings from JSON, or return defaults when the file is missing."""

    settings_path = Path(path)
    if not settings_path.exists():
        return AppSettings()

    try:
        raw_settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Settings file is not valid JSON: {settings_path}") from error

    if not isinstance(raw_settings, dict):
        raise ValueError(f"Settings file must contain a JSON object: {settings_path}")

    return AppSettings(**_known_settings(raw_settings))


def save_settings(
    settings: AppSettings,
    path: Path | str = DEFAULT_SETTINGS_PATH,
) -> Path:
    """Save settings as pretty-printed JSON and return the saved path."""

    settings_path = Path(path)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(asdict(settings), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return settings_path


def _known_settings(raw_settings: dict[str, Any]) -> dict[str, Any]:
    setting_names = AppSettings.__dataclass_fields__.keys()
    return {name: raw_settings[name] for name in setting_names if name in raw_settings}
