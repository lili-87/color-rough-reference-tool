"""Metadata for queued ComfyUI prompt IDs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


LATEST_PREDICTION_PROMPT_FILENAME = "latest_prediction_prompt.json"


@dataclass(frozen=True, slots=True)
class LatestPredictionPromptMetadata:
    """Minimal metadata for the latest queued prediction prompt."""

    prompt_id: str


def build_latest_prediction_prompt_metadata(prompt_id: str) -> LatestPredictionPromptMetadata:
    """Build metadata for the latest queued prediction prompt ID."""

    normalized_prompt_id = prompt_id.strip()
    if not normalized_prompt_id:
        raise ValueError("Prediction prompt ID must not be empty.")
    return LatestPredictionPromptMetadata(prompt_id=normalized_prompt_id)


def save_latest_prediction_prompt_metadata(
    prompt_id: str,
    metadata_dir: Path | str,
) -> Path:
    """Save the latest prediction prompt ID and return the JSON path."""

    metadata = build_latest_prediction_prompt_metadata(prompt_id)
    metadata_path = Path(metadata_dir) / LATEST_PREDICTION_PROMPT_FILENAME
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(asdict(metadata), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return metadata_path


def load_latest_prediction_prompt_metadata(
    metadata_dir: Path | str,
) -> LatestPredictionPromptMetadata:
    """Load the latest prediction prompt ID from project metadata."""

    metadata_path = Path(metadata_dir) / LATEST_PREDICTION_PROMPT_FILENAME
    if not metadata_path.exists():
        raise FileNotFoundError(f"Latest prediction prompt metadata does not exist: {metadata_path}")
    if not metadata_path.is_file():
        raise ValueError(f"Latest prediction prompt metadata path must be a file: {metadata_path}")

    try:
        raw_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Latest prediction prompt metadata is not valid JSON: {metadata_path}") from error

    if not isinstance(raw_metadata, dict):
        raise ValueError(f"Latest prediction prompt metadata must contain a JSON object: {metadata_path}")
    prompt_id = raw_metadata.get("prompt_id")
    if not isinstance(prompt_id, str):
        raise ValueError("Latest prediction prompt metadata has an invalid field: prompt_id")

    return build_latest_prediction_prompt_metadata(prompt_id)
