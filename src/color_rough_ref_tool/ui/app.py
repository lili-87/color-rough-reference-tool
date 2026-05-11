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
from color_rough_ref_tool.core.project_output import prepare_project_output
from color_rough_ref_tool.core.selection_metadata import save_selected_candidate_metadata
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


class ColorRoughReferenceApp:
    """Small desktop shell for the first manual workflow steps."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.settings = load_settings()
        self.color_rough_path = tk.StringVar(value="No color rough selected")
        self.status_message = tk.StringVar(value="Ready")
        self.selected_prediction_path = tk.StringVar(value="")
        self.prediction_thumbnails: list[tk.PhotoImage] = []

        self.endpoint_var = tk.StringVar(value=self.settings.comfyui_endpoint)
        self.prediction_workflow_var = tk.StringVar(value=self.settings.prediction_workflow_path)
        self.hand_workflow_var = tk.StringVar(value=self.settings.hand_inpainting_workflow_path)
        self.output_dir_var = tk.StringVar(value=self.settings.default_output_dir)

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

        prediction_frame = ttk.LabelFrame(container, text="Prediction outputs", padding=8)
        prediction_frame.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        prediction_frame.columnconfigure(0, weight=1)
        container.rowconfigure(7, weight=1)
        self.prediction_grid = ttk.Frame(prediction_frame)
        self.prediction_grid.grid(row=0, column=0, sticky="nw")
        ttk.Label(
            self.prediction_grid,
            text="No prediction images loaded",
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

    def _load_thumbnail_image(self, path: Path) -> tk.PhotoImage | None:
        try:
            image = tk.PhotoImage(file=path)
        except tk.TclError:
            return None

        scale = max(
            1,
            (image.width() + PREDICTION_THUMBNAIL_MAX_SIZE - 1)
            // PREDICTION_THUMBNAIL_MAX_SIZE,
            (image.height() + PREDICTION_THUMBNAIL_MAX_SIZE - 1)
            // PREDICTION_THUMBNAIL_MAX_SIZE,
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
