"""Metadata for generated hand reference images."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from color_rough_ref_tool.integrations.comfyui.hand_inpainting import HandReferenceOutputImage


HAND_REFERENCE_METADATA_FILENAME = "hand_refs.json"


@dataclass(frozen=True, slots=True)
class HandReferenceImageMetadata:
    """Minimal metadata for one generated hand reference image."""

    path: str
    file_name: str
    file_size_bytes: int
    modified_time: float


@dataclass(frozen=True, slots=True)
class HandReferenceMetadata:
    """Minimal metadata for generated hand reference images."""

    hand_refs: tuple[HandReferenceImageMetadata, ...]


def build_hand_reference_metadata(
    outputs: tuple[HandReferenceOutputImage, ...],
) -> HandReferenceMetadata:
    """Build metadata for hand reference output images already found on disk."""

    return HandReferenceMetadata(
        hand_refs=tuple(
            HandReferenceImageMetadata(
                path=output.path.as_posix(),
                file_name=output.file_name,
                file_size_bytes=output.file_size_bytes,
                modified_time=output.modified_time,
            )
            for output in outputs
        )
    )


def save_hand_reference_metadata(
    outputs: tuple[HandReferenceOutputImage, ...],
    metadata_dir: Path | str,
) -> Path:
    """Save hand reference metadata and return the JSON path."""

    metadata = build_hand_reference_metadata(outputs)
    metadata_path = Path(metadata_dir) / HAND_REFERENCE_METADATA_FILENAME
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(asdict(metadata), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return metadata_path
