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


def select_color_rough_image(path: Path | str) -> ColorRoughSelection:
    """Return a color rough selection for an existing file path."""

    image_path = Path(path)
    if not image_path.exists():
        raise FileNotFoundError(f"Color rough image does not exist: {image_path}")
    if not image_path.is_file():
        raise ValueError(f"Color rough path must be a file: {image_path}")

    return ColorRoughSelection(path=image_path)
