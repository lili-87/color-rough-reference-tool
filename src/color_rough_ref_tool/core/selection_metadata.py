"""Metadata for the selected prediction candidate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


SELECTED_CANDIDATE_METADATA_FILENAME = "selected_candidate.json"


@dataclass(frozen=True, slots=True)
class SelectedCandidateMetadata:
    """Minimal metadata for the prediction candidate chosen by the user."""

    source_path: str
    saved_path: str
    file_name: str
    file_size_bytes: int


def build_selected_candidate_metadata(
    source_path: Path | str,
    saved_path: Path | str,
) -> SelectedCandidateMetadata:
    """Build metadata for a saved selected prediction candidate."""

    source = Path(source_path)
    saved = Path(saved_path)
    if not saved.exists():
        raise FileNotFoundError(f"Saved selected prediction does not exist: {saved}")
    if not saved.is_file():
        raise ValueError(f"Saved selected prediction path must be a file: {saved}")

    return SelectedCandidateMetadata(
        source_path=source.as_posix(),
        saved_path=saved.as_posix(),
        file_name=saved.name,
        file_size_bytes=saved.stat().st_size,
    )


def save_selected_candidate_metadata(
    source_path: Path | str,
    saved_path: Path | str,
    metadata_dir: Path | str,
) -> Path:
    """Save selected candidate metadata and return the JSON path."""

    metadata = build_selected_candidate_metadata(source_path, saved_path)
    metadata_path = Path(metadata_dir) / SELECTED_CANDIDATE_METADATA_FILENAME
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(asdict(metadata), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return metadata_path


def load_selected_candidate_metadata(metadata_dir: Path | str) -> SelectedCandidateMetadata:
    """Load selected candidate metadata from the project metadata folder."""

    metadata_path = Path(metadata_dir) / SELECTED_CANDIDATE_METADATA_FILENAME
    if not metadata_path.exists():
        raise FileNotFoundError(f"Selected candidate metadata does not exist: {metadata_path}")
    if not metadata_path.is_file():
        raise ValueError(f"Selected candidate metadata path must be a file: {metadata_path}")

    try:
        raw_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Selected candidate metadata is not valid JSON: {metadata_path}") from error

    if not isinstance(raw_metadata, dict):
        raise ValueError(f"Selected candidate metadata must contain a JSON object: {metadata_path}")

    required_fields = {
        "source_path": str,
        "saved_path": str,
        "file_name": str,
        "file_size_bytes": int,
    }
    for field_name, field_type in required_fields.items():
        if not isinstance(raw_metadata.get(field_name), field_type):
            raise ValueError(f"Selected candidate metadata has an invalid field: {field_name}")

    return SelectedCandidateMetadata(
        source_path=raw_metadata["source_path"],
        saved_path=raw_metadata["saved_path"],
        file_name=raw_metadata["file_name"],
        file_size_bytes=raw_metadata["file_size_bytes"],
    )
