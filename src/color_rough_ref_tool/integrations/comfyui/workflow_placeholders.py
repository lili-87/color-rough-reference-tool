"""Placeholder handling for external ComfyUI workflow files."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


DEFAULT_WORKFLOW_DIR = Path("workflows")
PREDICTION_WORKFLOW_NAME = "prediction_workflow.json"
HAND_INPAINTING_WORKFLOW_NAME = "hand_inpainting_workflow.json"
COLOR_ROUGH_PLACEHOLDERS = (
    "{{COLOR_ROUGH_IMAGE_PATH}}",
    "{{COLOR_ROUGH_IMAGE}}",
)
SELECTED_CANDIDATE_PLACEHOLDERS = (
    "{{SELECTED_CANDIDATE_IMAGE_PATH}}",
    "{{SELECTED_CANDIDATE_IMAGE}}",
)
HAND_MASK_PLACEHOLDERS = (
    "{{HAND_MASK_IMAGE_PATH}}",
    "{{HAND_MASK_IMAGE}}",
)


@dataclass(frozen=True, slots=True)
class WorkflowPlaceholderPaths:
    """Paths where users can place their exported ComfyUI workflows."""

    root: Path
    prediction: Path
    hand_inpainting: Path


@dataclass(frozen=True, slots=True)
class WorkflowPlaceholderValidationResult:
    """Result of checking whether a workflow still has required placeholders."""

    missing_requirements: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.missing_requirements


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


def validate_prediction_workflow_placeholders(
    workflow: dict[str, Any],
) -> WorkflowPlaceholderValidationResult:
    """Check that a prediction workflow can receive the color rough image path."""

    return _validate_placeholder_groups(
        workflow,
        (("color rough image", COLOR_ROUGH_PLACEHOLDERS),),
    )


def validate_hand_inpainting_workflow_placeholders(
    workflow: dict[str, Any],
) -> WorkflowPlaceholderValidationResult:
    """Check that a hand workflow can receive the selected image and mask paths."""

    return _validate_placeholder_groups(
        workflow,
        (
            ("selected candidate image", SELECTED_CANDIDATE_PLACEHOLDERS),
            ("hand mask image", HAND_MASK_PLACEHOLDERS),
        ),
    )


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


def _validate_placeholder_groups(
    workflow: dict[str, Any],
    groups: tuple[tuple[str, tuple[str, ...]], ...],
) -> WorkflowPlaceholderValidationResult:
    missing = tuple(
        label
        for label, placeholders in groups
        if not _contains_any_placeholder(workflow, placeholders)
    )
    return WorkflowPlaceholderValidationResult(missing_requirements=missing)


def _contains_any_placeholder(value: Any, placeholders: tuple[str, ...]) -> bool:
    if isinstance(value, str):
        return any(placeholder in value for placeholder in placeholders)
    if isinstance(value, list):
        return any(_contains_any_placeholder(item, placeholders) for item in value)
    if isinstance(value, dict):
        return any(_contains_any_placeholder(item, placeholders) for item in value.values())
    return False
