"""Minimal project metadata saved into project output."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


PROJECT_METADATA_FILENAME = "project.json"
PROJECT_METADATA_SCHEMA_VERSION = 1
APPLICATION_NAME = "Color Rough Reference Tool"


@dataclass(frozen=True, slots=True)
class ProjectMetadata:
    """Small metadata record for one project output folder."""

    schema_version: int
    application_name: str
    project_root: str
    created_at: str


def build_project_metadata(
    project_root: Path | str,
    *,
    created_at: datetime | None = None,
) -> ProjectMetadata:
    """Build minimal metadata for a project output folder."""

    root_path = Path(project_root)
    timestamp = created_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return ProjectMetadata(
        schema_version=PROJECT_METADATA_SCHEMA_VERSION,
        application_name=APPLICATION_NAME,
        project_root=root_path.as_posix(),
        created_at=timestamp.isoformat(),
    )


def save_project_metadata(
    project_root: Path | str,
    metadata_dir: Path | str,
    *,
    created_at: datetime | None = None,
) -> Path:
    """Save minimal project metadata and return the JSON path."""

    metadata = build_project_metadata(project_root, created_at=created_at)
    metadata_path = Path(metadata_dir) / PROJECT_METADATA_FILENAME
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(asdict(metadata), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return metadata_path
