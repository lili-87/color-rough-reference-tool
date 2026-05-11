"""Placeholder handling for external ComfyUI workflow files."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


DEFAULT_WORKFLOW_DIR = Path("workflows")
PREDICTION_WORKFLOW_NAME = "prediction_workflow.json"
HAND_INPAINTING_WORKFLOW_NAME = "hand_inpainting_workflow.json"


@dataclass(frozen=True, slots=True)
class WorkflowPlaceholderPaths:
    """Paths where users can place their exported ComfyUI workflows."""

    root: Path
    prediction: Path
    hand_inpainting: Path


def prepare_workflow_placeholders(
    root: Path | str = DEFAULT_WORKFLOW_DIR,
) -> WorkflowPlaceholderPaths:
    """Create placeholder workflow files if they do not exist yet."""

    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)

    paths = WorkflowPlaceholderPaths(
        root=root_path,
        prediction=root_path / PREDICTION_WORKFLOW_NAME,
        hand_inpainting=root_path / HAND_INPAINTING_WORKFLOW_NAME,
    )

    _write_placeholder_if_missing(
        paths.prediction,
        "prediction",
        "Replace this file with a ComfyUI workflow for color rough prediction.",
    )
    _write_placeholder_if_missing(
        paths.hand_inpainting,
        "hand_inpainting",
        "Replace this file with a ComfyUI workflow for hand reference inpainting.",
    )

    return paths


def _write_placeholder_if_missing(
    path: Path,
    workflow_kind: str,
    note: str,
) -> None:
    if path.exists():
        return

    placeholder = {
        "placeholder": True,
        "workflow_kind": workflow_kind,
        "note": note,
        "expected_source": "Exported ComfyUI workflow JSON provided by the user.",
        "models_included": False,
        "nodes": {},
    }
    path.write_text(
        json.dumps(placeholder, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
