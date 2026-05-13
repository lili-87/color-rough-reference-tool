"""Minimal Tkinter UI shell for settings and color rough selection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from color_rough_ref_tool.core.color_rough_input import (
    build_color_rough_preview,
    select_color_rough_image,
)
from color_rough_ref_tool.core.mask_image import (
    BrushMaskStroke,
    MaskOperation,
    RectangleMask,
    mask_file_name_for_candidate,
    save_mask_png,
)
from color_rough_ref_tool.core.hand_reference_sheet import export_hand_reference_sheet
from color_rough_ref_tool.core.project_output import prepare_project_output
from color_rough_ref_tool.core.prompt_metadata import (
    save_latest_hand_reference_prompt_metadata,
    save_latest_prediction_prompt_metadata,
)
from color_rough_ref_tool.core.selection_metadata import (
    SelectedCandidateMetadata,
    load_selected_candidate_metadata,
    save_selected_candidate_metadata,
)
from color_rough_ref_tool.core.settings import (
    AppSettings,
    check_comfyui_configuration,
    load_settings,
    save_settings,
    save_settings_snapshot,
    with_comfyui_endpoint,
    with_hand_inpainting_workflow_path,
    with_prediction_workflow_path,
)
from color_rough_ref_tool.integrations.comfyui.prediction import (
    ComfyUIPromptResult,
    PredictionOutputImage,
    PredictionOutputReadResult,
    SavedPredictionCandidate,
    download_finished_prediction_images,
    fetch_latest_prediction_history,
    inspect_prediction_history,
    load_prediction_workflow,
    read_prediction_outputs_safely,
    save_selected_prediction_candidate,
    trigger_prediction_workflow,
)
from color_rough_ref_tool.integrations.comfyui.hand_inpainting import (
    HandReferenceOutputImage,
    HandReferenceOutputReadResult,
    download_finished_hand_reference_images,
    fetch_latest_hand_reference_history,
    inspect_hand_reference_history,
    load_hand_inpainting_workflow,
    read_hand_reference_outputs_safely,
    trigger_hand_inpainting_workflow,
)
from color_rough_ref_tool.integrations.comfyui.workflow_placeholders import (
    validate_hand_inpainting_workflow_uses_inputs,
    validate_hand_inpainting_workflow_placeholders,
    validate_prediction_workflow_uses_color_rough_input,
    validate_prediction_workflow_placeholders,
)


WINDOW_TITLE = "Color Rough Reference Tool"
PREDICTION_THUMBNAIL_MAX_SIZE = 160
HAND_REFERENCE_THUMBNAIL_MAX_SIZE = 160
THUMBNAIL_GRID_COLUMNS = 3
THUMBNAIL_LABEL_MAX_LENGTH = 30
THUMBNAIL_LABEL_WRAP_LENGTH = 150
MASK_PREVIEW_MAX_SIZE = 320
DEFAULT_MASK_BRUSH_SIZE = 18
MIN_MASK_BRUSH_SIZE = 1
MAX_MASK_BRUSH_SIZE = 80
MASK_TOOL_BRUSH = "brush"
MASK_TOOL_RECTANGLE = "rectangle"
MASK_TOOLS = frozenset({MASK_TOOL_BRUSH, MASK_TOOL_RECTANGLE})
SUMMARY_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})


@dataclass(frozen=True, slots=True)
class SettingsFormValues:
    """Raw values entered in the settings form."""

    comfyui_endpoint: str
    prediction_workflow_path: str
    hand_inpainting_workflow_path: str
    default_output_dir: str


def build_settings_from_form(values: SettingsFormValues) -> AppSettings:
    """Build validated settings from the UI form values."""

    settings = AppSettings(default_output_dir=values.default_output_dir.strip() or "project_output")
    settings = with_comfyui_endpoint(settings, values.comfyui_endpoint)
    settings = with_prediction_workflow_path(settings, values.prediction_workflow_path)
    return with_hand_inpainting_workflow_path(settings, values.hand_inpainting_workflow_path)


def format_configuration_message(settings: AppSettings) -> str:
    """Return a short message for the configuration check result."""

    result = check_comfyui_configuration(settings)
    if result.ok:
        return "Settings look OK."
    return "Please fix these settings:\n" + "\n".join(f"- {error}" for error in result.errors)


def format_error_message(action: str, error: Exception) -> str:
    """Return a beginner-friendly error message for UI dialogs."""

    detail = str(error)
    detail_lower = detail.lower()
    hints: list[str] = []

    if "could not reach comfyui endpoint" in detail_lower:
        hints.extend(
            (
                "Start ComfyUI first. The ComfyUI command window should stay open while this app uses it.",
                "Open the endpoint in a browser, for example http://127.0.0.1:8188, and confirm the ComfyUI page appears.",
                "If the browser page does not open, check that ComfyUI finished starting and that the endpoint URL and port match this app.",
            )
        )
    if "workflow" in detail_lower:
        hints.append("Check the workflow file path. Placeholder files must be replaced with real ComfyUI workflow JSON files.")
    if "selected_candidate.json" in detail_lower or "selected candidate" in detail_lower:
        hints.append("Load prediction images, choose one candidate, then press Save selected.")
    if "hand mask" in detail_lower or "_hand_mask" in detail_lower:
        hints.append("Load the selected candidate for mask editing, draw a mask, then press Save mask.")
    if "no prediction images" in detail_lower:
        hints.append("Put generated prediction images in project_output/predictions, then press Load predictions.")
    if "no hand reference images" in detail_lower:
        hints.append("Put generated hand reference images in project_output/hand_refs, then reload or export again.")
    if "does not exist" in detail_lower and not hints:
        hints.append("The file or folder could not be found. Check the path and try again.")
    if not hints:
        hints.append("Check the current settings and required files, then try again.")

    hint_text = "\n".join(f"- {hint}" for hint in hints)
    return f"Could not {action}.\n\nWhat to check:\n{hint_text}\n\nDetails:\n{detail}"


def prediction_output_folder(settings: AppSettings) -> Path:
    """Return the folder where prediction outputs are expected."""

    return Path(settings.default_output_dir) / "predictions"


def hand_reference_output_folder(settings: AppSettings) -> Path:
    """Return the folder where hand reference outputs are expected."""

    return Path(settings.default_output_dir) / "hand_refs"


def format_project_reopen_message(
    project_output_dir: Path | str,
    prediction_count: int,
    hand_reference_count: int,
    selected_candidate_loaded: bool,
) -> str:
    """Return a short status message after reopening saved project output."""

    message = (
        f"Reopened project output: {Path(project_output_dir).as_posix()} | "
        f"predictions: {prediction_count} | hand references: {hand_reference_count}"
    )
    if selected_candidate_loaded:
        return f"{message} | selected candidate loaded"
    return message


def format_project_summary(
    project_output_dir: Path | str,
    prediction_count: int,
    selected_candidate_exists: bool,
    hand_mask_exists: bool,
    hand_reference_count: int,
    sheet_count: int,
) -> str:
    """Return a compact summary of the current project output."""

    selected_status = "yes" if selected_candidate_exists else "no"
    mask_status = "yes" if hand_mask_exists else "no"
    return (
        f"Project: {Path(project_output_dir).as_posix()} | "
        f"predictions: {prediction_count} | selected: {selected_status} | "
        f"mask: {mask_status} | hand refs: {hand_reference_count} | sheets: {sheet_count}"
    )


def format_workflow_validation_message(
    prediction_missing: tuple[str, ...],
    hand_inpainting_missing: tuple[str, ...],
    prediction_warnings: tuple[str, ...] = (),
    hand_inpainting_warnings: tuple[str, ...] = (),
) -> str:
    """Return a short UI message for local workflow placeholder validation."""

    messages: list[str] = []
    if prediction_missing:
        messages.append(f"- Prediction workflow missing: {', '.join(prediction_missing)}")
    if hand_inpainting_missing:
        messages.append(f"- Hand inpainting workflow missing: {', '.join(hand_inpainting_missing)}")
    if prediction_warnings:
        messages.extend(f"- Prediction workflow warning: {warning}" for warning in prediction_warnings)
    if hand_inpainting_warnings:
        messages.extend(
            f"- Hand inpainting workflow warning: {warning}"
            for warning in hand_inpainting_warnings
        )
    if not messages:
        return "Workflow placeholders and input connections look OK."
    if (
        (prediction_warnings or hand_inpainting_warnings)
        and not prediction_missing
        and not hand_inpainting_missing
    ):
        return (
            "Workflow placeholders exist, but the image inputs may be ignored.\n"
            "This usually means the placeholder is on a Load Image node that is sitting by itself, or the image/mask node is not wired into KSampler, img2img, ControlNet, or inpainting.\n"
            "Open the workflow in ComfyUI, connect the listed image nodes to the actual generation route, export the API workflow JSON again, then press Check workflows again:\n"
            + "\n".join(messages)
        )
    return "Please fix workflow placeholders:\n" + "\n".join(messages)


def format_prediction_output_count(outputs: tuple[PredictionOutputImage, ...]) -> str:
    """Return a short UI status message for loaded prediction outputs."""

    if len(outputs) == 1:
        return "Loaded 1 prediction image."
    return f"Loaded {len(outputs)} prediction images."


def format_prediction_output_result(result: PredictionOutputReadResult) -> str:
    """Return a short status message for prediction output loading."""

    if result.ok:
        return format_prediction_output_count(result.images)
    return " ".join(result.messages)


def format_prediction_thumbnail_refresh_result(result: PredictionOutputReadResult) -> str:
    """Return a short status message after refreshing prediction thumbnails."""

    if not result.ok:
        return format_prediction_output_result(result)
    if len(result.images) == 1:
        return "Prediction thumbnails refreshed: 1 image."
    return f"Prediction thumbnails refreshed: {len(result.images)} images."


def format_prediction_prompt_queued_message(result: ComfyUIPromptResult) -> str:
    """Return a short status message after queuing a prediction prompt."""

    return f"Queued prediction workflow: {result.prompt_id}"


def format_prediction_generation_waiting_status(
    result: ComfyUIPromptResult,
    prompt_metadata_path: Path,
) -> str:
    """Return the next manual step after queuing prediction generation."""

    return (
        f"{format_prediction_prompt_queued_message(result)} | "
        "ComfyUI is generating. Wait for ComfyUI to finish, then press Load predictions. "
        f"Prompt ID saved for history check: {prompt_metadata_path.as_posix()}"
    )


def format_prediction_generation_waiting_dialog(
    result: ComfyUIPromptResult,
    prompt_metadata_path: Path,
) -> str:
    """Return beginner-friendly queue guidance for prediction generation."""

    return (
        "Prediction workflow was queued.\n\n"
        f"Prompt ID:\n{result.prompt_id}\n\n"
        f"Saved for history check:\n{prompt_metadata_path}\n\n"
        "What to do next:\n"
        "1. Wait until ComfyUI finishes generating.\n"
        "2. Press Load predictions to manually load the finished images.\n"
        "3. If nothing appears yet, wait a little and press Load predictions again."
    )


def format_prediction_manual_load_status(result: PredictionOutputReadResult) -> str:
    """Return a manual-load status message for prediction thumbnails."""

    if result.ok:
        return format_prediction_thumbnail_refresh_result(result)
    return (
        f"{format_prediction_output_result(result)} "
        "If ComfyUI is still generating, wait a little and press Load predictions again."
    )


def format_prediction_history_import_status(
    *,
    history_checked: bool,
    history_completed: bool,
    imported_count: int,
    refresh_result: PredictionOutputReadResult,
) -> str:
    """Return a Load predictions status after checking ComfyUI history once."""

    refresh_status = format_prediction_manual_load_status(refresh_result)
    if not history_checked:
        return refresh_status
    if not history_completed:
        return (
            "ComfyUI history says the latest prediction is not finished yet. "
            "Wait until ComfyUI finishes, then press Load predictions again. "
            f"{refresh_status}"
        )
    if imported_count == 1:
        return f"Imported 1 prediction image from ComfyUI history. {refresh_status}"
    if imported_count > 1:
        return f"Imported {imported_count} prediction images from ComfyUI history. {refresh_status}"
    return (
        "ComfyUI history says the latest prediction is finished, but it did not report any prediction images to import. "
        f"{refresh_status}"
    )


def format_selected_prediction_message(output: PredictionOutputImage) -> str:
    """Return a short status message for the selected prediction candidate."""

    return f"Selected prediction: {output.file_name}"


def format_saved_prediction_message(saved: SavedPredictionCandidate) -> str:
    """Return a short status message after saving the selected prediction."""

    return f"Saved selected prediction: {saved.saved_path.as_posix()}"


def format_hand_reference_output_count(outputs: tuple[HandReferenceOutputImage, ...]) -> str:
    """Return a short UI status message for loaded hand reference outputs."""

    if len(outputs) == 1:
        return "Loaded 1 hand reference image."
    return f"Loaded {len(outputs)} hand reference images."


def format_hand_reference_output_result(result: HandReferenceOutputReadResult) -> str:
    """Return a short status message for hand reference output loading."""

    if result.ok:
        return format_hand_reference_output_count(result.images)
    return " ".join(result.messages)


def format_hand_reference_thumbnail_refresh_result(result: HandReferenceOutputReadResult) -> str:
    """Return a short status message after refreshing hand reference thumbnails."""

    if not result.ok:
        return format_hand_reference_output_result(result)
    if len(result.images) == 1:
        return "Hand reference thumbnails refreshed: 1 image."
    return f"Hand reference thumbnails refreshed: {len(result.images)} images."


def format_hand_reference_prompt_queued_message(result: ComfyUIPromptResult) -> str:
    """Return a short status message after queuing a hand reference prompt."""

    return f"Queued hand reference workflow: {result.prompt_id}"


def format_hand_reference_generation_guard_message(
    missing_selected_candidate: bool,
    missing_hand_mask: bool,
) -> str:
    """Return a simple message when hand reference generation is not ready."""

    steps: list[str] = []
    if missing_selected_candidate:
        steps.append("Load prediction images, choose one candidate, then press Save selected.")
    if missing_hand_mask:
        steps.append("Press Load selected for mask, draw the hand area, then press Save mask.")
    if not steps:
        return "Hand reference generation is ready."
    numbered_steps = "\n".join(f"{index}. {step}" for index, step in enumerate(steps, start=1))
    return (
        "Hand reference generation is not ready yet.\n\n"
        "Before pressing Regenerate hand ref:\n"
        + numbered_steps
    )


def format_hand_reference_generation_waiting_status(
    result: ComfyUIPromptResult,
    prompt_metadata_path: Path,
) -> str:
    """Return the next manual step after queuing hand reference generation."""

    return (
        f"{format_hand_reference_prompt_queued_message(result)} | "
        "ComfyUI is generating. Wait for ComfyUI to finish, then press Load hand refs. "
        f"Prompt ID saved for history check: {prompt_metadata_path.as_posix()}"
    )


def format_hand_reference_generation_waiting_dialog(
    result: ComfyUIPromptResult,
    prompt_metadata_path: Path,
) -> str:
    """Return beginner-friendly queue guidance for hand reference generation."""

    return (
        "Hand reference workflow was queued.\n\n"
        f"Prompt ID:\n{result.prompt_id}\n\n"
        f"Saved for history check:\n{prompt_metadata_path}\n\n"
        "What to do next:\n"
        "1. Wait until ComfyUI finishes generating.\n"
        "2. Press Load hand refs to manually load the finished images.\n"
        "3. If nothing appears yet, wait a little and press Load hand refs again."
    )


def format_hand_reference_manual_load_status(result: HandReferenceOutputReadResult) -> str:
    """Return a manual-load status message for hand reference thumbnails."""

    if result.ok:
        return format_hand_reference_thumbnail_refresh_result(result)
    return (
        f"{format_hand_reference_output_result(result)} "
        "If ComfyUI is still generating, wait a little and press Load hand refs again."
    )


def format_hand_reference_history_import_status(
    *,
    history_checked: bool,
    history_completed: bool,
    imported_count: int,
    refresh_result: HandReferenceOutputReadResult,
) -> str:
    """Return a Load hand refs status after checking ComfyUI history once."""

    refresh_status = format_hand_reference_manual_load_status(refresh_result)
    if not history_checked:
        return refresh_status
    if not history_completed:
        return (
            "ComfyUI history says the latest hand reference generation is not finished yet. "
            "Wait until ComfyUI finishes, then press Load hand refs again. "
            f"{refresh_status}"
        )
    if imported_count == 1:
        return f"Imported 1 hand reference image from ComfyUI history. {refresh_status}"
    if imported_count > 1:
        return f"Imported {imported_count} hand reference images from ComfyUI history. {refresh_status}"
    return (
        "ComfyUI history says the latest hand reference generation is finished, but it did not report any hand reference images to import. "
        f"{refresh_status}"
    )


def format_exported_hand_reference_sheet_message(sheet_path: Path) -> str:
    """Return a short status message after exporting the hand reference sheet."""

    return f"Exported hand reference sheet: {sheet_path.as_posix()}"


def thumbnail_grid_position(index: int, columns: int = THUMBNAIL_GRID_COLUMNS) -> tuple[int, int]:
    """Return a row and column for a thumbnail item."""

    if index < 0:
        raise ValueError("Thumbnail index must not be negative.")
    if columns <= 0:
        raise ValueError("Thumbnail column count must be positive.")
    return index // columns, index % columns


def format_thumbnail_file_label(file_name: str, max_length: int = THUMBNAIL_LABEL_MAX_LENGTH) -> str:
    """Return a compact file name label for thumbnail cards."""

    if max_length < 8:
        raise ValueError("Thumbnail label length must be at least 8.")
    if len(file_name) <= max_length:
        return file_name
    path = Path(file_name)
    suffix = path.suffix
    suffix_length = len(suffix)
    if suffix_length >= max_length - 4:
        return file_name[: max_length - 3] + "..."
    stem_limit = max_length - suffix_length - 3
    return f"{path.stem[:stem_limit]}...{suffix}"


def format_thumbnail_file_size(file_size_bytes: int) -> str:
    """Return a small readable file size label for thumbnails."""

    if file_size_bytes < 0:
        raise ValueError("File size must not be negative.")
    if file_size_bytes < 1024:
        return f"{file_size_bytes} B"
    return f"{file_size_bytes / 1024:.1f} KB"


def format_mask_candidate_message(metadata: SelectedCandidateMetadata) -> str:
    """Return a short status message for the mask editing preview candidate."""

    return f"Loaded selected candidate for mask editing: {metadata.file_name}"


def hand_mask_path_for_candidate(masks_dir: Path | str, candidate_file_name: str) -> Path:
    """Return the expected saved hand mask path for a selected candidate."""

    return Path(masks_dir) / mask_file_name_for_candidate(candidate_file_name)


def normalize_mask_brush_size(value: int | str) -> int:
    """Return a brush size within the small supported UI range."""

    try:
        brush_size = int(value)
    except (TypeError, ValueError):
        return DEFAULT_MASK_BRUSH_SIZE
    return max(MIN_MASK_BRUSH_SIZE, min(MAX_MASK_BRUSH_SIZE, brush_size))


def normalize_mask_tool(value: str) -> str:
    """Return a supported mask drawing tool name."""

    if value in MASK_TOOLS:
        return value
    return MASK_TOOL_BRUSH


class ColorRoughReferenceApp:
    """Small desktop shell for the first manual workflow steps."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.settings = load_settings()
        self.color_rough_path = tk.StringVar(value="No color rough selected")
        self.selected_color_rough_file_path = tk.StringVar(value="")
        self.status_message = tk.StringVar(value="Ready")
        self.project_summary_message = tk.StringVar(value="Project: not loaded yet")
        self.selected_prediction_path = tk.StringVar(value="")
        self.prediction_thumbnails: list[tk.PhotoImage] = []
        self.hand_reference_thumbnails: list[tk.PhotoImage] = []
        self.mask_preview_image: tk.PhotoImage | None = None
        self.mask_canvas: tk.Canvas | None = None
        self.last_mask_point: tuple[int, int] | None = None
        self.rectangle_start_point: tuple[int, int] | None = None
        self.active_rectangle_id: int | None = None
        self.mask_operations: list[MaskOperation] = []
        self.mask_candidate_metadata: SelectedCandidateMetadata | None = None

        self.endpoint_var = tk.StringVar(value=self.settings.comfyui_endpoint)
        self.prediction_workflow_var = tk.StringVar(value=self.settings.prediction_workflow_path)
        self.hand_workflow_var = tk.StringVar(value=self.settings.hand_inpainting_workflow_path)
        self.output_dir_var = tk.StringVar(value=self.settings.default_output_dir)
        self.mask_brush_size_var = tk.IntVar(value=DEFAULT_MASK_BRUSH_SIZE)
        self.mask_tool_var = tk.StringVar(value=MASK_TOOL_BRUSH)

        self.root.title(WINDOW_TITLE)
        self.root.minsize(760, 560)
        self._build_layout()
        self.reopen_project_outputs()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

        ttk.Label(container, text="Color rough").grid(row=0, column=0, sticky="w")
        ttk.Label(container, textvariable=self.color_rough_path).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(12, 8),
        )
        ttk.Button(container, text="Choose image", command=self.choose_color_rough).grid(
            row=0,
            column=2,
            sticky="e",
        )

        ttk.Separator(container).grid(row=1, column=0, columnspan=3, sticky="ew", pady=14)

        self._add_text_row(container, 2, "ComfyUI endpoint", self.endpoint_var)
        self._add_file_row(
            container,
            3,
            "Prediction workflow",
            self.prediction_workflow_var,
        )
        self._add_file_row(
            container,
            4,
            "Hand inpainting workflow",
            self.hand_workflow_var,
        )
        self._add_text_row(container, 5, "Project output", self.output_dir_var)

        button_bar = ttk.Frame(container)
        button_bar.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(16, 8))
        ttk.Button(button_bar, text="Check settings", command=self.check_settings).pack(
            side="left",
            padx=(0, 8),
        )
        ttk.Button(button_bar, text="Check workflows", command=self.check_workflows).pack(
            side="left",
            padx=(0, 8),
        )
        ttk.Button(button_bar, text="Save settings", command=self.save_current_settings).pack(
            side="left",
            padx=(0, 8),
        )
        ttk.Button(button_bar, text="Save snapshot", command=self.save_snapshot).pack(
            side="left",
            padx=(0, 8),
        )
        ttk.Button(
            button_bar,
            text="Regenerate prediction",
            command=self.regenerate_prediction,
        ).pack(
            side="left",
            padx=(0, 8),
        )
        ttk.Button(button_bar, text="Reopen project", command=self.reopen_project_outputs).pack(
            side="left",
            padx=(0, 8),
        )
        ttk.Button(button_bar, text="Load predictions", command=self.load_prediction_outputs).pack(
            side="left",
            padx=(0, 8),
        )
        ttk.Button(button_bar, text="Save selected", command=self.save_selected_prediction).pack(
            side="left",
        )

        summary_frame = ttk.LabelFrame(container, text="Project summary", padding=8)
        summary_frame.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        summary_frame.columnconfigure(0, weight=1)
        ttk.Label(summary_frame, textvariable=self.project_summary_message).grid(
            row=0,
            column=0,
            sticky="ew",
        )

        content_pane = ttk.PanedWindow(container, orient=tk.VERTICAL)
        content_pane.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        container.rowconfigure(8, weight=1)

        prediction_frame = ttk.LabelFrame(content_pane, text="Prediction outputs", padding=8)
        content_pane.add(prediction_frame, weight=1)
        prediction_frame.columnconfigure(0, weight=1)
        self.prediction_grid = ttk.Frame(prediction_frame)
        self.prediction_grid.grid(row=0, column=0, sticky="nw")
        ttk.Label(
            self.prediction_grid,
            text="No prediction images loaded",
        ).grid(row=0, column=0, sticky="w")

        mask_frame = ttk.LabelFrame(content_pane, text="Mask editing", padding=8)
        content_pane.add(mask_frame, weight=1)
        mask_frame.columnconfigure(0, weight=1)
        ttk.Button(
            mask_frame,
            text="Load selected for mask",
            command=self.load_selected_for_mask,
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Radiobutton(
            mask_frame,
            text="Brush",
            variable=self.mask_tool_var,
            value=MASK_TOOL_BRUSH,
        ).grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(
            mask_frame,
            text="Rectangle",
            variable=self.mask_tool_var,
            value=MASK_TOOL_RECTANGLE,
        ).grid(row=0, column=2, sticky="w", padx=(4, 8))
        ttk.Label(mask_frame, text="Size").grid(row=0, column=3, sticky="w")
        ttk.Spinbox(
            mask_frame,
            from_=MIN_MASK_BRUSH_SIZE,
            to=MAX_MASK_BRUSH_SIZE,
            textvariable=self.mask_brush_size_var,
            width=5,
        ).grid(row=0, column=4, sticky="w", padx=(4, 8))
        ttk.Button(
            mask_frame,
            text="Clear mask",
            command=self.clear_mask_drawing,
        ).grid(row=0, column=5, sticky="w")
        ttk.Button(
            mask_frame,
            text="Save mask",
            command=self.save_mask_image,
        ).grid(row=0, column=6, sticky="w", padx=(8, 0))
        self.mask_preview_frame = ttk.Frame(mask_frame, padding=(0, 8, 0, 0))
        self.mask_preview_frame.grid(row=1, column=0, columnspan=7, sticky="nw")
        ttk.Label(
            self.mask_preview_frame,
            text="No selected candidate loaded for mask editing",
        ).grid(row=0, column=0, sticky="w")

        hand_reference_frame = ttk.LabelFrame(content_pane, text="Hand references", padding=8)
        content_pane.add(hand_reference_frame, weight=1)
        hand_reference_frame.columnconfigure(0, weight=1)
        ttk.Button(
            hand_reference_frame,
            text="Export sheet",
            command=self.export_hand_reference_sheet,
        ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Button(
            hand_reference_frame,
            text="Regenerate hand ref",
            command=self.regenerate_hand_reference,
        ).grid(row=0, column=1, sticky="w", pady=(0, 8))
        ttk.Button(
            hand_reference_frame,
            text="Load hand refs",
            command=self.load_hand_reference_outputs,
        ).grid(row=0, column=2, sticky="w", padx=(8, 0), pady=(0, 8))
        self.hand_reference_grid = ttk.Frame(hand_reference_frame)
        self.hand_reference_grid.grid(row=1, column=0, columnspan=3, sticky="nw")
        ttk.Label(
            self.hand_reference_grid,
            text="No hand reference images loaded",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(container, textvariable=self.status_message).grid(
            row=9,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(8, 0),
        )

    def _add_text_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable).grid(
            row=row,
            column=1,
            columnspan=2,
            sticky="ew",
            padx=(12, 0),
            pady=4,
        )

    def _add_file_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable).grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(12, 8),
            pady=4,
        )
        ttk.Button(
            parent,
            text="Browse",
            command=lambda: self.choose_workflow_file(variable),
        ).grid(row=row, column=2, sticky="e", pady=4)

    def choose_color_rough(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose color rough image",
            filetypes=[
                ("Supported images", "*.png *.jpg *.jpeg *.webp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            selection = select_color_rough_image(path)
            preview = build_color_rough_preview(selection)
        except (FileNotFoundError, ValueError, OSError) as error:
            messagebox.showerror("Color rough", format_error_message("load the color rough image", error))
            return

        self.color_rough_path.set(f"{preview.file_name} ({preview.file_size_bytes} bytes)")
        self.selected_color_rough_file_path.set(selection.path.as_posix())
        self.status_message.set(f"Selected: {preview.path}")

    def choose_workflow_file(self, variable: tk.StringVar) -> None:
        path = filedialog.askopenfilename(
            title="Choose workflow JSON",
            filetypes=[
                ("ComfyUI workflow JSON", "*.json"),
                ("All files", "*.*"),
            ],
        )
        if path:
            variable.set(Path(path).as_posix())

    def check_settings(self) -> None:
        try:
            settings = self._settings_from_form()
        except ValueError as error:
            messagebox.showerror("Settings", format_error_message("read the settings", error))
            return

        message = format_configuration_message(settings)
        self.status_message.set(message.replace("\n", " "))
        if message == "Settings look OK.":
            messagebox.showinfo("Settings", message)
        else:
            messagebox.showerror("Settings", message)

    def check_workflows(self) -> None:
        try:
            settings = self._settings_from_form()
            prediction_workflow = load_prediction_workflow(settings.prediction_workflow_path)
            hand_workflow = load_hand_inpainting_workflow(settings.hand_inpainting_workflow_path)
            prediction_result = validate_prediction_workflow_placeholders(prediction_workflow)
            prediction_usage_result = validate_prediction_workflow_uses_color_rough_input(
                prediction_workflow
            )
            hand_result = validate_hand_inpainting_workflow_placeholders(hand_workflow)
            hand_usage_result = validate_hand_inpainting_workflow_uses_inputs(hand_workflow)
        except (FileNotFoundError, OSError, ValueError) as error:
            messagebox.showerror("Workflow check", format_error_message("check workflow placeholders", error))
            return

        message = format_workflow_validation_message(
            prediction_result.missing_requirements,
            hand_result.missing_requirements,
            prediction_usage_result.warnings,
            hand_usage_result.warnings,
        )
        self.status_message.set(message.replace("\n", " "))
        if (
            prediction_result.ok
            and hand_result.ok
            and prediction_usage_result.ok
            and hand_usage_result.ok
        ):
            messagebox.showinfo("Workflow check", message)
        elif prediction_result.ok and hand_result.ok:
            messagebox.showwarning("Workflow check", message)
        else:
            messagebox.showerror("Workflow check", message)

    def save_current_settings(self) -> None:
        try:
            settings = self._settings_from_form()
            saved_path = save_settings(settings)
        except ValueError as error:
            messagebox.showerror("Settings", format_error_message("save the settings", error))
            return

        self.settings = settings
        self.status_message.set(f"Saved settings: {saved_path}")
        messagebox.showinfo("Settings", f"Saved settings:\n{saved_path}")

    def save_snapshot(self) -> None:
        try:
            settings = self._settings_from_form()
            output_folders = prepare_project_output(settings.default_output_dir)
            saved_path = save_settings_snapshot(settings, output_folders.metadata)
        except ValueError as error:
            messagebox.showerror("Settings snapshot", format_error_message("save the settings snapshot", error))
            return

        self.status_message.set(f"Saved settings snapshot: {saved_path}")
        messagebox.showinfo("Settings snapshot", f"Saved settings snapshot:\n{saved_path}")

    def regenerate_prediction(self) -> None:
        color_rough_path = self.selected_color_rough_file_path.get()
        if not color_rough_path:
            message = "Choose a color rough image before regenerating predictions."
            self.status_message.set(message)
            messagebox.showinfo("Prediction generation", message)
            return

        try:
            settings = self._settings_from_form()
            output_folders = prepare_project_output(settings.default_output_dir)
            result = trigger_prediction_workflow(
                settings,
                color_rough_path=color_rough_path,
                client_id="color-rough-ref-tool-ui",
            )
            prompt_metadata_path = save_latest_prediction_prompt_metadata(
                result.prompt_id,
                output_folders.metadata,
            )
        except (ConnectionError, FileNotFoundError, OSError, ValueError) as error:
            messagebox.showerror("Prediction generation", format_error_message("queue prediction generation", error))
            return

        message = format_prediction_generation_waiting_status(result, prompt_metadata_path)
        self.status_message.set(message)
        messagebox.showinfo(
            "Prediction generation",
            format_prediction_generation_waiting_dialog(result, prompt_metadata_path),
        )

    def load_prediction_outputs(self) -> None:
        """Reload prediction images and refresh their thumbnails in the UI."""

        try:
            settings = self._settings_from_form()
            output_folders = prepare_project_output(settings.default_output_dir)
            history_checked, history_completed, imported_count = self._import_latest_prediction_history_outputs(
                settings,
                output_folders.metadata,
                output_folders.predictions,
            )
            result = self._refresh_prediction_thumbnails(settings)
        except (ConnectionError, FileNotFoundError, OSError, ValueError) as error:
            messagebox.showerror("Prediction outputs", format_error_message("load prediction outputs", error))
            return

        status = format_prediction_history_import_status(
            history_checked=history_checked,
            history_completed=history_completed,
            imported_count=imported_count,
            refresh_result=result,
        )
        self.status_message.set(status)
        if not result.ok:
            messagebox.showinfo("Prediction outputs", status)

    def _import_latest_prediction_history_outputs(
        self,
        settings: AppSettings,
        metadata_dir: Path,
        predictions_dir: Path,
    ) -> tuple[bool, bool, int]:
        try:
            history = fetch_latest_prediction_history(settings, metadata_dir)
        except FileNotFoundError:
            return False, False, 0

        inspection = inspect_prediction_history(history)
        if not inspection.completed:
            return True, False, 0

        imported = download_finished_prediction_images(
            inspection,
            endpoint=settings.comfyui_endpoint,
            predictions_dir=predictions_dir,
        )
        return True, True, len(imported)

    def _refresh_prediction_thumbnails(self, settings: AppSettings) -> PredictionOutputReadResult:
        output_folders = prepare_project_output(settings.default_output_dir)
        result = read_prediction_outputs_safely(output_folders.predictions)
        self._render_prediction_outputs(result.images)
        self.refresh_project_summary()
        return result

    def _render_prediction_outputs(self, outputs: tuple[PredictionOutputImage, ...]) -> None:
        for child in self.prediction_grid.winfo_children():
            child.destroy()
        self.prediction_thumbnails.clear()
        self.selected_prediction_path.set("")

        if not outputs:
            ttk.Label(
                self.prediction_grid,
                text="No prediction images found",
            ).grid(row=0, column=0, sticky="w")
            return

        for index, output in enumerate(outputs):
            row, column = thumbnail_grid_position(index)
            item_frame = ttk.Frame(self.prediction_grid, padding=8, relief="groove")
            item_frame.grid(row=row, column=column, sticky="n", padx=6, pady=6)

            image = self._load_thumbnail_image(output.path)
            if image is None:
                ttk.Label(
                    item_frame,
                    text="[preview unavailable]",
                    width=22,
                    anchor="center",
                ).grid(row=0, column=0)
            else:
                self.prediction_thumbnails.append(image)
                ttk.Label(item_frame, image=image).grid(row=0, column=0)

            ttk.Label(
                item_frame,
                text=format_thumbnail_file_label(output.file_name),
                wraplength=THUMBNAIL_LABEL_WRAP_LENGTH,
                justify="center",
            ).grid(row=1, column=0, pady=(6, 0))
            ttk.Label(
                item_frame,
                text=format_thumbnail_file_size(output.file_size_bytes),
                foreground="#555555",
            ).grid(row=2, column=0, pady=(2, 0))
            ttk.Radiobutton(
                item_frame,
                text="Select",
                variable=self.selected_prediction_path,
                value=output.path.as_posix(),
                command=lambda candidate=output: self.select_prediction(candidate),
            ).grid(row=3, column=0, pady=(6, 0))

    def load_hand_reference_outputs(self) -> None:
        """Reload hand reference images and refresh their thumbnails in the UI."""

        try:
            settings = self._settings_from_form()
            output_folders = prepare_project_output(settings.default_output_dir)
            history_checked, history_completed, imported_count = self._import_latest_hand_reference_history_outputs(
                settings,
                output_folders.metadata,
                output_folders.hand_refs,
            )
            result = self._refresh_hand_reference_thumbnails(settings)
        except (ConnectionError, FileNotFoundError, OSError, ValueError) as error:
            self.status_message.set(format_error_message("load hand reference outputs", error).replace("\n", " "))
            return

        status = format_hand_reference_history_import_status(
            history_checked=history_checked,
            history_completed=history_completed,
            imported_count=imported_count,
            refresh_result=result,
        )
        self.status_message.set(status)
        if not result.ok:
            messagebox.showinfo("Hand references", status)

    def _import_latest_hand_reference_history_outputs(
        self,
        settings: AppSettings,
        metadata_dir: Path,
        hand_refs_dir: Path,
    ) -> tuple[bool, bool, int]:
        try:
            history = fetch_latest_hand_reference_history(settings, metadata_dir)
        except FileNotFoundError:
            return False, False, 0

        inspection = inspect_hand_reference_history(history)
        if not inspection.completed:
            return True, False, 0

        imported = download_finished_hand_reference_images(
            inspection,
            endpoint=settings.comfyui_endpoint,
            hand_refs_dir=hand_refs_dir,
        )
        return True, True, len(imported)

    def _refresh_hand_reference_thumbnails(self, settings: AppSettings) -> HandReferenceOutputReadResult:
        output_folders = prepare_project_output(settings.default_output_dir)
        result = read_hand_reference_outputs_safely(output_folders.hand_refs)
        self._render_hand_reference_outputs(result.images)
        self.refresh_project_summary()
        return result

    def reopen_project_outputs(self) -> None:
        """Reload saved outputs from the current project output folder."""

        try:
            settings = self._settings_from_form()
            output_folders = prepare_project_output(settings.default_output_dir)
            prediction_result = read_prediction_outputs_safely(output_folders.predictions)
            hand_reference_result = read_hand_reference_outputs_safely(output_folders.hand_refs)
        except (OSError, ValueError) as error:
            self.status_message.set(format_error_message("reopen the project output", error).replace("\n", " "))
            return

        self._render_prediction_outputs(prediction_result.images)
        self._render_hand_reference_outputs(hand_reference_result.images)
        selected_candidate_loaded = self._restore_saved_selected_candidate_preview(output_folders.metadata)
        hand_mask_exists = self._saved_hand_mask_exists(output_folders.metadata, output_folders.masks)
        self.project_summary_message.set(
            format_project_summary(
                output_folders.root,
                len(prediction_result.images),
                selected_candidate_loaded,
                hand_mask_exists,
                len(hand_reference_result.images),
                self._count_summary_images(output_folders.sheets),
            )
        )
        self.status_message.set(
            format_project_reopen_message(
                output_folders.root,
                len(prediction_result.images),
                len(hand_reference_result.images),
                selected_candidate_loaded,
            )
        )

    def _restore_saved_selected_candidate_preview(self, metadata_dir: Path) -> bool:
        try:
            metadata = load_selected_candidate_metadata(metadata_dir)
            selected_path = Path(metadata.saved_path)
            if not selected_path.exists() or not selected_path.is_file():
                return False
        except (FileNotFoundError, OSError, ValueError):
            return False

        self._render_mask_preview(selected_path, metadata)
        return True

    def refresh_project_summary(self) -> None:
        try:
            settings = self._settings_from_form()
            output_folders = prepare_project_output(settings.default_output_dir)
            prediction_result = read_prediction_outputs_safely(output_folders.predictions)
            hand_reference_result = read_hand_reference_outputs_safely(output_folders.hand_refs)
        except (OSError, ValueError) as error:
            self.project_summary_message.set(format_error_message("refresh the project summary", error).replace("\n", " "))
            return

        selected_candidate_exists = self._saved_selected_candidate_exists(output_folders.metadata)
        self.project_summary_message.set(
            format_project_summary(
                output_folders.root,
                len(prediction_result.images),
                selected_candidate_exists,
                self._saved_hand_mask_exists(output_folders.metadata, output_folders.masks),
                len(hand_reference_result.images),
                self._count_summary_images(output_folders.sheets),
            )
        )

    def _saved_selected_candidate_exists(self, metadata_dir: Path) -> bool:
        try:
            metadata = load_selected_candidate_metadata(metadata_dir)
            selected_path = Path(metadata.saved_path)
        except (FileNotFoundError, OSError, ValueError):
            return False
        return selected_path.exists() and selected_path.is_file()

    def _saved_hand_mask_exists(self, metadata_dir: Path, masks_dir: Path) -> bool:
        try:
            metadata = load_selected_candidate_metadata(metadata_dir)
        except (FileNotFoundError, OSError, ValueError):
            return False

        mask_path = hand_mask_path_for_candidate(masks_dir, metadata.file_name)
        return mask_path.exists() and mask_path.is_file()

    def _count_summary_images(self, folder: Path) -> int:
        if not folder.exists() or not folder.is_dir():
            return 0
        return sum(
            1
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in SUMMARY_IMAGE_EXTENSIONS
        )

    def _render_hand_reference_outputs(
        self,
        outputs: tuple[HandReferenceOutputImage, ...],
    ) -> None:
        for child in self.hand_reference_grid.winfo_children():
            child.destroy()
        self.hand_reference_thumbnails.clear()

        if not outputs:
            ttk.Label(
                self.hand_reference_grid,
                text="No hand reference images found",
            ).grid(row=0, column=0, sticky="w")
            return

        for index, output in enumerate(outputs):
            row, column = thumbnail_grid_position(index)
            item_frame = ttk.Frame(self.hand_reference_grid, padding=8, relief="groove")
            item_frame.grid(row=row, column=column, sticky="n", padx=6, pady=6)

            image = self._load_hand_reference_thumbnail_image(output.path)
            if image is None:
                ttk.Label(
                    item_frame,
                    text="[preview unavailable]",
                    width=22,
                    anchor="center",
                ).grid(row=0, column=0)
            else:
                self.hand_reference_thumbnails.append(image)
                ttk.Label(item_frame, image=image).grid(row=0, column=0)

            ttk.Label(
                item_frame,
                text=format_thumbnail_file_label(output.file_name),
                wraplength=THUMBNAIL_LABEL_WRAP_LENGTH,
                justify="center",
            ).grid(row=1, column=0, pady=(6, 0))
            ttk.Label(
                item_frame,
                text=format_thumbnail_file_size(output.file_size_bytes),
                foreground="#555555",
            ).grid(row=2, column=0, pady=(2, 0))

    def export_hand_reference_sheet(self) -> None:
        try:
            settings = self._settings_from_form()
            output_folders = prepare_project_output(settings.default_output_dir)
            result = read_hand_reference_outputs_safely(output_folders.hand_refs)
            if not result.ok:
                message = format_hand_reference_output_result(result)
                self.status_message.set(message)
                messagebox.showinfo("Hand reference sheet", message)
                return
            sheet_path = export_hand_reference_sheet(result.images, output_folders.sheets)
        except (OSError, ValueError) as error:
            messagebox.showerror("Hand reference sheet", format_error_message("export the hand reference sheet", error))
            return

        message = format_exported_hand_reference_sheet_message(sheet_path)
        self.refresh_project_summary()
        self.status_message.set(message)
        messagebox.showinfo("Hand reference sheet", f"Export complete:\n{sheet_path}")

    def regenerate_hand_reference(self) -> None:
        try:
            settings = self._settings_from_form()
            output_folders = prepare_project_output(settings.default_output_dir)
        except (OSError, ValueError) as error:
            messagebox.showerror("Hand reference generation", format_error_message("queue hand reference generation", error))
            return

        try:
            metadata = load_selected_candidate_metadata(output_folders.metadata)
        except (FileNotFoundError, OSError, ValueError):
            message = format_hand_reference_generation_guard_message(
                missing_selected_candidate=True,
                missing_hand_mask=False,
            )
            self.status_message.set(message.replace("\n", " "))
            messagebox.showinfo("Hand reference generation", message)
            return

        selected_path = Path(metadata.saved_path)
        mask_path = hand_mask_path_for_candidate(output_folders.masks, metadata.file_name)
        missing_selected_candidate = not selected_path.exists() or not selected_path.is_file()
        missing_hand_mask = not mask_path.exists() or not mask_path.is_file()
        if missing_selected_candidate or missing_hand_mask:
            message = format_hand_reference_generation_guard_message(
                missing_selected_candidate=missing_selected_candidate,
                missing_hand_mask=missing_hand_mask,
            )
            self.status_message.set(message.replace("\n", " "))
            messagebox.showinfo("Hand reference generation", message)
            return

        try:
            result = trigger_hand_inpainting_workflow(
                settings,
                selected_candidate_path=selected_path,
                mask_path=mask_path,
                client_id="color-rough-ref-tool-ui",
            )
            prompt_metadata_path = save_latest_hand_reference_prompt_metadata(
                result.prompt_id,
                output_folders.metadata,
            )
        except (ConnectionError, OSError, ValueError) as error:
            messagebox.showerror("Hand reference generation", format_error_message("queue hand reference generation", error))
            return

        message = format_hand_reference_generation_waiting_status(result, prompt_metadata_path)
        self.status_message.set(message)
        messagebox.showinfo(
            "Hand reference generation",
            format_hand_reference_generation_waiting_dialog(result, prompt_metadata_path),
        )

    def select_prediction(self, output: PredictionOutputImage) -> None:
        self.selected_prediction_path.set(output.path.as_posix())
        self.status_message.set(format_selected_prediction_message(output))

    def save_selected_prediction(self) -> None:
        selected_path = self.selected_prediction_path.get()
        if not selected_path:
            message = "Choose a prediction candidate first."
            self.status_message.set(message)
            messagebox.showinfo("Selected prediction", message)
            return

        try:
            settings = self._settings_from_form()
            output_folders = prepare_project_output(settings.default_output_dir)
            saved = save_selected_prediction_candidate(selected_path, output_folders.selected)
            metadata_path = save_selected_candidate_metadata(
                saved.source_path,
                saved.saved_path,
                output_folders.metadata,
            )
        except (FileNotFoundError, OSError, ValueError) as error:
            messagebox.showerror("Selected prediction", format_error_message("save the selected prediction", error))
            return

        message = format_saved_prediction_message(saved)
        self.refresh_project_summary()
        self.status_message.set(message)
        messagebox.showinfo(
            "Selected prediction",
            f"Saved selected prediction:\n{saved.saved_path}\n\nMetadata:\n{metadata_path}",
        )

    def load_selected_for_mask(self) -> None:
        try:
            settings = self._settings_from_form()
            output_folders = prepare_project_output(settings.default_output_dir)
            metadata = load_selected_candidate_metadata(output_folders.metadata)
            selected_path = Path(metadata.saved_path)
            if not selected_path.exists():
                raise FileNotFoundError(f"Selected candidate image does not exist: {selected_path}")
            if not selected_path.is_file():
                raise ValueError(f"Selected candidate path must be a file: {selected_path}")
        except (FileNotFoundError, OSError, ValueError) as error:
            messagebox.showerror("Mask editing", format_error_message("load the selected candidate for mask editing", error))
            return

        self._render_mask_preview(selected_path, metadata)
        self.refresh_project_summary()
        message = format_mask_candidate_message(metadata)
        self.status_message.set(message)

    def _render_mask_preview(
        self,
        selected_path: Path,
        metadata: SelectedCandidateMetadata,
    ) -> None:
        for child in self.mask_preview_frame.winfo_children():
            child.destroy()
        self.mask_preview_image = self._load_image_preview(selected_path, MASK_PREVIEW_MAX_SIZE)
        self.mask_canvas = None
        self.last_mask_point = None
        self.rectangle_start_point = None
        self.active_rectangle_id = None
        self.mask_operations.clear()
        self.mask_candidate_metadata = metadata

        if self.mask_preview_image is None:
            ttk.Label(
                self.mask_preview_frame,
                text="[preview unavailable]",
            ).grid(row=0, column=0, sticky="w")
        else:
            self.mask_canvas = tk.Canvas(
                self.mask_preview_frame,
                width=self.mask_preview_image.width(),
                height=self.mask_preview_image.height(),
                highlightthickness=1,
                highlightbackground="#999999",
            )
            self.mask_canvas.grid(
                row=0,
                column=0,
                sticky="w",
            )
            self.mask_canvas.create_image(0, 0, anchor="nw", image=self.mask_preview_image)
            self.mask_canvas.bind("<ButtonPress-1>", self.start_mask_stroke)
            self.mask_canvas.bind("<B1-Motion>", self.draw_mask_stroke)
            self.mask_canvas.bind("<ButtonRelease-1>", self.end_mask_stroke)
        ttk.Label(self.mask_preview_frame, text=metadata.file_name).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(4, 0),
        )

    def start_mask_stroke(self, event: tk.Event) -> None:
        if normalize_mask_tool(self.mask_tool_var.get()) == MASK_TOOL_RECTANGLE:
            self.start_rectangle_mask(event)
            return

        self.last_mask_point = (int(event.x), int(event.y))
        self._draw_mask_dot(int(event.x), int(event.y))

    def draw_mask_stroke(self, event: tk.Event) -> None:
        if normalize_mask_tool(self.mask_tool_var.get()) == MASK_TOOL_RECTANGLE:
            self.update_rectangle_mask(event)
            return

        if self.mask_canvas is None:
            return

        current_point = (int(event.x), int(event.y))
        if self.last_mask_point is None:
            self.last_mask_point = current_point
            self._draw_mask_dot(*current_point)
            return

        brush_size = normalize_mask_brush_size(self.mask_brush_size_var.get())
        self.mask_canvas.create_line(
            self.last_mask_point[0],
            self.last_mask_point[1],
            current_point[0],
            current_point[1],
            fill="#ff3333",
            width=brush_size,
            tags=("mask_stroke",),
        )
        self.mask_operations.append(
            BrushMaskStroke(
                start=self.last_mask_point,
                end=current_point,
                size=brush_size,
            )
        )
        self.last_mask_point = current_point

    def end_mask_stroke(self, event: tk.Event) -> None:
        if normalize_mask_tool(self.mask_tool_var.get()) == MASK_TOOL_RECTANGLE:
            self.finish_rectangle_mask(event)
            return

        self.last_mask_point = None

    def start_rectangle_mask(self, event: tk.Event) -> None:
        if self.mask_canvas is None:
            return

        self.rectangle_start_point = (int(event.x), int(event.y))
        self.active_rectangle_id = self.mask_canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline="#ff3333",
            width=2,
            tags=("mask_stroke",),
        )

    def update_rectangle_mask(self, event: tk.Event) -> None:
        if (
            self.mask_canvas is None
            or self.rectangle_start_point is None
            or self.active_rectangle_id is None
        ):
            return

        self.mask_canvas.coords(
            self.active_rectangle_id,
            self.rectangle_start_point[0],
            self.rectangle_start_point[1],
            int(event.x),
            int(event.y),
        )

    def finish_rectangle_mask(self, event: tk.Event) -> None:
        if self.rectangle_start_point is not None:
            self.mask_operations.append(
                RectangleMask(
                    start=self.rectangle_start_point,
                    end=(int(event.x), int(event.y)),
                )
            )
        self.update_rectangle_mask(event)
        self.rectangle_start_point = None
        self.active_rectangle_id = None

    def clear_mask_drawing(self) -> None:
        if self.mask_canvas is None:
            self.status_message.set("No mask drawing to clear.")
            return

        self.mask_canvas.delete("mask_stroke")
        self.rectangle_start_point = None
        self.active_rectangle_id = None
        self.last_mask_point = None
        self.mask_operations.clear()
        self.status_message.set("Cleared mask drawing.")

    def _draw_mask_dot(self, x: int, y: int) -> None:
        if self.mask_canvas is None:
            return

        brush_size = normalize_mask_brush_size(self.mask_brush_size_var.get())
        radius = max(1, brush_size // 2)
        self.mask_canvas.create_oval(
            x - radius,
            y - radius,
            x + radius,
            y + radius,
            fill="#ff3333",
            outline="#ff3333",
            tags=("mask_stroke",),
        )
        self.mask_operations.append(
            BrushMaskStroke(
                start=(x, y),
                end=(x, y),
                size=brush_size,
            )
        )

    def save_mask_image(self) -> None:
        if self.mask_canvas is None or self.mask_preview_image is None:
            message = "Load a selected candidate before saving a mask."
            self.status_message.set(message)
            messagebox.showinfo("Mask editing", message)
            return
        if self.mask_candidate_metadata is None:
            message = "Selected candidate metadata is not loaded."
            self.status_message.set(message)
            messagebox.showinfo("Mask editing", message)
            return

        try:
            settings = self._settings_from_form()
            output_folders = prepare_project_output(settings.default_output_dir)
            saved_path = save_mask_png(
                width=self.mask_preview_image.width(),
                height=self.mask_preview_image.height(),
                operations=tuple(self.mask_operations),
                masks_dir=output_folders.masks,
                candidate_file_name=self.mask_candidate_metadata.file_name,
            )
        except (OSError, ValueError) as error:
            messagebox.showerror("Mask editing", format_error_message("save the mask image", error))
            return

        self.status_message.set(f"Saved mask: {saved_path}")
        self.refresh_project_summary()
        messagebox.showinfo("Mask editing", f"Saved mask:\n{saved_path}")

    def _load_thumbnail_image(self, path: Path) -> tk.PhotoImage | None:
        return self._load_image_preview(path, PREDICTION_THUMBNAIL_MAX_SIZE)

    def _load_hand_reference_thumbnail_image(self, path: Path) -> tk.PhotoImage | None:
        return self._load_image_preview(path, HAND_REFERENCE_THUMBNAIL_MAX_SIZE)

    def _load_image_preview(self, path: Path, max_size: int) -> tk.PhotoImage | None:
        try:
            image = tk.PhotoImage(file=path)
        except tk.TclError:
            return None

        scale = max(
            1,
            (image.width() + max_size - 1)
            // max_size,
            (image.height() + max_size - 1)
            // max_size,
        )
        if scale > 1:
            image = image.subsample(scale, scale)
        return image

    def _settings_from_form(self) -> AppSettings:
        return build_settings_from_form(
            SettingsFormValues(
                comfyui_endpoint=self.endpoint_var.get(),
                prediction_workflow_path=self.prediction_workflow_var.get(),
                hand_inpainting_workflow_path=self.hand_workflow_var.get(),
                default_output_dir=self.output_dir_var.get(),
            )
        )


def main() -> None:
    root = tk.Tk()
    ColorRoughReferenceApp(root)
    root.mainloop()
