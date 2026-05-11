"""Create the standard project output folder structure."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


OUTPUT_SUBDIRS = (
    "input",
    "predictions",
    "selected",
    "masks",
    "hand_refs",
    "sheets",
    "metadata",
)


@dataclass(frozen=True, slots=True)
class ProjectOutputFolders:
    """Paths used to save one project of generated reference materials."""

    root: Path
    input: Path
    predictions: Path
    selected: Path
    masks: Path
    hand_refs: Path
    sheets: Path
    metadata: Path


def prepare_project_output(root: Path | str = "project_output") -> ProjectOutputFolders:
    """Create the project output folders and return their paths."""

    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)

    folders = {
        subdir: root_path / subdir
        for subdir in OUTPUT_SUBDIRS
    }
    for folder_path in folders.values():
        folder_path.mkdir(parents=True, exist_ok=True)

    return ProjectOutputFolders(root=root_path, **folders)
