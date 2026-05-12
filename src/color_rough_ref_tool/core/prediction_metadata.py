"""Metadata for generated prediction images."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from color_rough_ref_tool.integrations.comfyui.prediction import PredictionOutputImage


PREDICTION_METADATA_FILENAME = "predictions.json"


@dataclass(frozen=True, slots=True)
class PredictionImageMetadata:
    """Minimal metadata for one generated prediction image."""

    path: str
    file_name: str
    file_size_bytes: int
    modified_time: float


@dataclass(frozen=True, slots=True)
class PredictionMetadata:
    """Minimal metadata for generated prediction candidates."""

    predictions: tuple[PredictionImageMetadata, ...]


def build_prediction_metadata(
    outputs: tuple[PredictionOutputImage, ...],
) -> PredictionMetadata:
    """Build metadata for prediction output images already found on disk."""

    return PredictionMetadata(
        predictions=tuple(
            PredictionImageMetadata(
                path=output.path.as_posix(),
                file_name=output.file_name,
                file_size_bytes=output.file_size_bytes,
                modified_time=output.modified_time,
            )
            for output in outputs
        )
    )


def save_prediction_metadata(
    outputs: tuple[PredictionOutputImage, ...],
    metadata_dir: Path | str,
) -> Path:
    """Save prediction metadata and return the JSON path."""

    metadata = build_prediction_metadata(outputs)
    metadata_path = Path(metadata_dir) / PREDICTION_METADATA_FILENAME
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(asdict(metadata), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return metadata_path
