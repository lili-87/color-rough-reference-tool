"""Basic JSON settings storage for the application."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS_PATH = Path("settings") / "settings.json"


@dataclass(slots=True)
class AppSettings:
    """User-editable settings for local generation workflows."""

    comfyui_endpoint: str = "http://127.0.0.1:8188"
    prediction_workflow_path: str = ""
    hand_inpainting_workflow_path: str = ""
    default_output_dir: str = "project_output"


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
