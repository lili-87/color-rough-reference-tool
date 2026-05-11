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
    save_mask_png,
)
from color_rough_ref_tool.core.project_output import prepare_project_output
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
    PredictionOutputImage,
    PredictionOutputReadResult,
    SavedPredictionCandidate,
    read_prediction_outputs_safely,
    save_selected_prediction_candidate,
)


WINDOW_TITLE = "Color Rough Reference Tool"
PREDICTION_THUMBNAIL_MAX_SIZE = 160
MASK_PREVIEW_MAX_SIZE = 320
DEFAULT_MASK_BRUSH_SIZE = 18
MIN_MASK_BRUSH_SIZE = 1
MAX_MASK_BRUSH_SIZE = 80
MASK_TOOL_BRUSH = "brush"
MASK_TOOL_RECTANGLE = "rectangle"
MASK_TOOLS = frozenset({MASK_TOOL_BRUSH, MASK_TOOL_RECTANGLE})


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


def prediction_output_folder(settings: AppSettings) -> Path:
    """Return the folder where prediction outputs are expected."""

    return Path(settings.default_output_dir) / "predictions"


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


def format_selected_prediction_message(output: PredictionOutputImage) -> str:
    """Return a short status message for the selected prediction candidate."""

    return f"Selected prediction: {output.file_name}"


def format_saved_prediction_message(saved: SavedPredictionCandidate) -> str:
    """Return a short status message after saving the selected prediction."""

    return f"Saved selected prediction: {saved.saved_path.as_posix()}"


def format_mask_candidate_message(metadata: SelectedCandidateMetadata) -> str:
    """Return a short status message for the mask editing preview candidate."""

    return f"Loaded selected candidate for mask editing: {metadata.file_name}"


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
        self.status_message = tk.StringVar(value="Ready")
        self.selected_prediction_path = tk.StringVar(value="")
        self.prediction_thumbnails: list[tk.PhotoImage] = []
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
        ttk.Button(button_bar, text="Save settings", command=self.save_current_settings).pack(
            side="left",
            padx=(0, 8),
        )
        ttk.Button(button_bar, text="Save snapshot", command=self.save_snapshot).pack(
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

        content_pane = ttk.PanedWindow(container, orient=tk.VERTICAL)
        content_pane.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        container.rowconfigure(7, weight=1)

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

        ttk.Label(container, textvariable=self.status_message).grid(
            row=8,
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
            messagebox.showerror("Color rough", str(error))
            return

        self.color_rough_path.set(f"{preview.file_name} ({preview.file_size_bytes} bytes)")
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
            messagebox.showerror("Settings", str(error))
            return

        message = format_configuration_message(settings)
        self.status_message.set(message.replace("\n", " "))
        if message == "Settings look OK.":
            messagebox.showinfo("Settings", message)
        else:
            messagebox.showerror("Settings", message)

    def save_current_settings(self) -> None:
        try:
            settings = self._settings_from_form()
            saved_path = save_settings(settings)
        except ValueError as error:
            messagebox.showerror("Settings", str(error))
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
            messagebox.showerror("Settings snapshot", str(error))
            return

        self.status_message.set(f"Saved settings snapshot: {saved_path}")
        messagebox.showinfo("Settings snapshot", f"Saved settings snapshot:\n{saved_path}")

    def load_prediction_outputs(self) -> None:
        try:
            settings = self._settings_from_form()
            prepare_project_output(settings.default_output_dir)
            result = read_prediction_outputs_safely(prediction_output_folder(settings))
        except ValueError as error:
            messagebox.showerror("Prediction outputs", str(error))
            return

        self._render_prediction_outputs(result.images)
        status = format_prediction_output_result(result)
        self.status_message.set(status)
        if not result.ok:
            messagebox.showinfo("Prediction outputs", status)

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
            row = index // 4
            column = index % 4
            item_frame = ttk.Frame(self.prediction_grid, padding=6)
            item_frame.grid(row=row, column=column, sticky="n", padx=4, pady=4)

            image = self._load_thumbnail_image(output.path)
            if image is None:
                ttk.Label(item_frame, text="[preview unavailable]").grid(row=0, column=0)
            else:
                self.prediction_thumbnails.append(image)
                ttk.Label(item_frame, image=image).grid(row=0, column=0)

            ttk.Label(item_frame, text=output.file_name).grid(row=1, column=0, pady=(4, 0))
            ttk.Radiobutton(
                item_frame,
                text="Select",
                variable=self.selected_prediction_path,
                value=output.path.as_posix(),
                command=lambda candidate=output: self.select_prediction(candidate),
            ).grid(row=2, column=0, pady=(4, 0))

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
            messagebox.showerror("Selected prediction", str(error))
            return

        message = format_saved_prediction_message(saved)
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
            messagebox.showerror("Mask editing", str(error))
            return

        self._render_mask_preview(selected_path, metadata)
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
            messagebox.showerror("Mask editing", str(error))
            return

        self.status_message.set(f"Saved mask: {saved_path}")
        messagebox.showinfo("Mask editing", f"Saved mask:\n{saved_path}")

    def _load_thumbnail_image(self, path: Path) -> tk.PhotoImage | None:
        return self._load_image_preview(path, PREDICTION_THUMBNAIL_MAX_SIZE)

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
