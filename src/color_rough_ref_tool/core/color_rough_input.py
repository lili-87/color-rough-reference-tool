"""Minimal color rough image selection handling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from color_rough_ref_tool.core.project_output import ProjectOutputFolders


@dataclass(frozen=True, slots=True)
class ColorRoughSelection:
    """A user-selected color rough image file."""

    path: Path

    @property
    def file_name(self) -> str:
        return self.path.name


@dataclass(frozen=True, slots=True)
class ColorRoughPreview:
    """Minimal file details needed to show a selected color rough."""

    path: Path
    file_name: str
    file_uri: str
    file_size_bytes: int


@dataclass(frozen=True, slots=True)
class SavedColorRoughInput:
    """Location of the color rough copied into the project output."""

    source_path: Path
    saved_path: Path


def select_color_rough_image(path: Path | str) -> ColorRoughSelection:
    """Return a color rough selection for an existing file path."""

    image_path = Path(path)
    if not image_path.exists():
        raise FileNotFoundError(f"Color rough image does not exist: {image_path}")
    if not image_path.is_file():
        raise ValueError(f"Color rough path must be a file: {image_path}")

    return ColorRoughSelection(path=image_path)


def build_color_rough_preview(
    selection: ColorRoughSelection,
) -> ColorRoughPreview:
    """Build preview metadata for the selected color rough image."""

    absolute_path = selection.path.resolve()
    return ColorRoughPreview(
        path=absolute_path,
        file_name=absolute_path.name,
        file_uri=absolute_path.as_uri(),
        file_size_bytes=absolute_path.stat().st_size,
    )


def save_color_rough_to_project_input(
    selection: ColorRoughSelection,
    output_folders: ProjectOutputFolders,
) -> SavedColorRoughInput:
    """Copy the selected color rough into the project input folder."""

    source_path = selection.path
    saved_path = output_folders.input / f"color_rough{source_path.suffix.lower()}"
    output_folders.input.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, saved_path)
    return SavedColorRoughInput(
        source_path=source_path,
        saved_path=saved_path,
    )
