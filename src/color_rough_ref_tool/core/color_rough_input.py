"""Minimal color rough image selection handling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


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
