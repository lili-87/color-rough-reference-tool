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
