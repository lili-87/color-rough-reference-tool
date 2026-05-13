from pathlib import Path
import unittest

from color_rough_ref_tool.core.settings import AppSettings
from color_rough_ref_tool.core.selection_metadata import SelectedCandidateMetadata
from color_rough_ref_tool.integrations.comfyui.hand_inpainting import (
    HandReferenceOutputImage,
    HandReferenceOutputReadResult,
)
from color_rough_ref_tool.integrations.comfyui.prediction import (
    ComfyUIPromptResult,
    PredictionOutputImage,
    PredictionOutputReadResult,
    SavedPredictionCandidate,
)
from color_rough_ref_tool.ui.app import (
    SettingsFormValues,
    build_settings_from_form,
    format_configuration_message,
    format_error_message,
    format_exported_hand_reference_sheet_message,
    format_hand_reference_output_count,
    format_hand_reference_output_result,
    format_hand_reference_prompt_queued_message,
    format_thumbnail_file_label,
    format_thumbnail_file_size,
    format_prediction_output_count,
    format_prediction_output_result,
    format_prediction_prompt_queued_message,
    format_mask_candidate_message,
    format_saved_prediction_message,
    format_selected_prediction_message,
    format_project_reopen_message,
    format_project_summary,
    format_workflow_validation_message,
    hand_mask_path_for_candidate,
    hand_reference_output_folder,
    normalize_mask_brush_size,
    normalize_mask_tool,
    prediction_output_folder,
    thumbnail_grid_position,
)


class UiAppTest(unittest.TestCase):
    def test_build_settings_from_form_normalizes_values(self) -> None:
        settings = build_settings_from_form(
            SettingsFormValues(
                comfyui_endpoint=" http://localhost:8188/ ",
                prediction_workflow_path=" workflows/prediction.json ",
                hand_inpainting_workflow_path=" workflows/hand_inpaint.json ",
                default_output_dir=" project_output ",
            )
        )

        self.assertEqual(settings.comfyui_endpoint, "http://localhost:8188")
        self.assertEqual(settings.prediction_workflow_path, "workflows/prediction.json")
        self.assertEqual(settings.hand_inpainting_workflow_path, "workflows/hand_inpaint.json")
        self.assertEqual(settings.default_output_dir, "project_output")

    def test_format_configuration_message_reports_valid_settings(self) -> None:
        message = format_configuration_message(AppSettings())

        self.assertEqual(message, "Settings look OK.")

    def test_format_configuration_message_reports_invalid_settings(self) -> None:
        settings = AppSettings(
            comfyui_endpoint="file:///ComfyUI",
            prediction_workflow_path="workflows/prediction.txt",
            hand_inpainting_workflow_path="workflows/hand_inpaint.json",
            default_output_dir="project_output",
        )

        message = format_configuration_message(settings)

        self.assertIn("Please fix these settings:", message)
        self.assertIn("ComfyUI endpoint:", message)
        self.assertIn("Prediction workflow file:", message)

    def test_format_error_message_adds_comfyui_hint(self) -> None:
        message = format_error_message(
            "queue prediction generation",
            ConnectionError("Could not reach ComfyUI endpoint: http://127.0.0.1:8188"),
        )

        self.assertIn("Could not queue prediction generation.", message)
        self.assertIn("Start ComfyUI first", message)
        self.assertIn("Details:", message)

    def test_format_error_message_adds_selected_candidate_hint(self) -> None:
        message = format_error_message(
            "queue hand reference generation",
            FileNotFoundError("Selected candidate metadata does not exist: selected_candidate.json"),
        )

        self.assertIn("Save selected", message)

    def test_format_error_message_adds_mask_hint(self) -> None:
        message = format_error_message(
            "queue hand reference generation",
            FileNotFoundError("Hand mask image does not exist: project_output/masks/pred_002_hand_mask.png"),
        )

        self.assertIn("Save mask", message)

    def test_prediction_output_folder_uses_default_output_dir(self) -> None:
        settings = AppSettings(default_output_dir="custom_output")

        folder = prediction_output_folder(settings)

        self.assertEqual(folder.as_posix(), "custom_output/predictions")

    def test_hand_reference_output_folder_uses_default_output_dir(self) -> None:
        settings = AppSettings(default_output_dir="custom_output")

        folder = hand_reference_output_folder(settings)

        self.assertEqual(folder.as_posix(), "custom_output/hand_refs")

    def test_format_project_reopen_message_reports_loaded_outputs(self) -> None:
        self.assertEqual(
            format_project_reopen_message(
                Path("project_output"),
                prediction_count=2,
                hand_reference_count=3,
                selected_candidate_loaded=True,
            ),
            "Reopened project output: project_output | predictions: 2 | hand references: 3 | selected candidate loaded",
        )

    def test_format_project_summary_reports_current_project_state(self) -> None:
        self.assertEqual(
            format_project_summary(
                Path("project_output"),
                prediction_count=4,
                selected_candidate_exists=True,
                hand_mask_exists=False,
                hand_reference_count=3,
                sheet_count=1,
            ),
            "Project: project_output | predictions: 4 | selected: yes | mask: no | hand refs: 3 | sheets: 1",
        )

    def test_format_workflow_validation_message_reports_ok(self) -> None:
        self.assertEqual(
            format_workflow_validation_message((), ()),
            "Workflow placeholders and color rough input connection look OK.",
        )

    def test_format_workflow_validation_message_reports_missing_items(self) -> None:
        message = format_workflow_validation_message(
            ("color rough image",),
            ("hand mask image",),
        )

        self.assertIn("Please fix workflow placeholders:", message)
        self.assertIn("Prediction workflow missing: color rough image", message)
        self.assertIn("Hand inpainting workflow missing: hand mask image", message)

    def test_format_workflow_validation_message_reports_prediction_warning(self) -> None:
        message = format_workflow_validation_message(
            (),
            (),
            ("color rough image node may not be connected",),
        )

        self.assertIn("Workflow placeholders exist, but please check this:", message)
        self.assertIn("Prediction workflow warning:", message)

    def test_format_prediction_output_count_reports_count(self) -> None:
        output = PredictionOutputImage(
            path=Path("predictions/pred_001.png"),
            file_name="pred_001.png",
            file_size_bytes=10,
            modified_time=1.0,
        )

        self.assertEqual(format_prediction_output_count(()), "Loaded 0 prediction images.")
        self.assertEqual(format_prediction_output_count((output,)), "Loaded 1 prediction image.")

    def test_format_prediction_output_result_reports_messages(self) -> None:
        result = PredictionOutputReadResult(
            images=(),
            messages=("No prediction images were found in: project_output/predictions",),
        )

        self.assertEqual(
            format_prediction_output_result(result),
            "No prediction images were found in: project_output/predictions",
        )

    def test_format_prediction_prompt_queued_message_reports_prompt_id(self) -> None:
        result = ComfyUIPromptResult(
            prompt_id="prompt-001",
            response={"prompt_id": "prompt-001"},
        )

        self.assertEqual(
            format_prediction_prompt_queued_message(result),
            "Queued prediction workflow: prompt-001",
        )

    def test_format_selected_prediction_message_reports_file_name(self) -> None:
        output = PredictionOutputImage(
            path=Path("predictions/pred_002.png"),
            file_name="pred_002.png",
            file_size_bytes=20,
            modified_time=2.0,
        )

        self.assertEqual(
            format_selected_prediction_message(output),
            "Selected prediction: pred_002.png",
        )

    def test_format_saved_prediction_message_reports_saved_path(self) -> None:
        saved = SavedPredictionCandidate(
            source_path=Path("project_output/predictions/pred_002.png"),
            saved_path=Path("project_output/selected/pred_002.png"),
        )

        self.assertEqual(
            format_saved_prediction_message(saved),
            "Saved selected prediction: project_output/selected/pred_002.png",
        )

    def test_format_hand_reference_output_count_reports_count(self) -> None:
        output = HandReferenceOutputImage(
            path=Path("hand_refs/pred_002_hand_ref_001.png"),
            file_name="pred_002_hand_ref_001.png",
            file_size_bytes=10,
            modified_time=1.0,
        )

        self.assertEqual(format_hand_reference_output_count(()), "Loaded 0 hand reference images.")
        self.assertEqual(format_hand_reference_output_count((output,)), "Loaded 1 hand reference image.")

    def test_format_hand_reference_output_result_reports_messages(self) -> None:
        result = HandReferenceOutputReadResult(
            images=(),
            messages=("No hand reference images were found in: project_output/hand_refs",),
        )

        self.assertEqual(
            format_hand_reference_output_result(result),
            "No hand reference images were found in: project_output/hand_refs",
        )

    def test_format_hand_reference_prompt_queued_message_reports_prompt_id(self) -> None:
        result = ComfyUIPromptResult(
            prompt_id="hand-001",
            response={"prompt_id": "hand-001"},
        )

        self.assertEqual(
            format_hand_reference_prompt_queued_message(result),
            "Queued hand reference workflow: hand-001",
        )

    def test_format_exported_hand_reference_sheet_message_reports_saved_path(self) -> None:
        self.assertEqual(
            format_exported_hand_reference_sheet_message(
                Path("project_output/sheets/hand_sheet_001.png")
            ),
            "Exported hand reference sheet: project_output/sheets/hand_sheet_001.png",
        )

    def test_hand_mask_path_for_candidate_uses_saved_mask_name(self) -> None:
        self.assertEqual(
            hand_mask_path_for_candidate(Path("project_output/masks"), "pred_002.png"),
            Path("project_output/masks/pred_002_hand_mask.png"),
        )

    def test_thumbnail_grid_position_uses_three_column_layout_by_default(self) -> None:
        self.assertEqual(thumbnail_grid_position(0), (0, 0))
        self.assertEqual(thumbnail_grid_position(2), (0, 2))
        self.assertEqual(thumbnail_grid_position(3), (1, 0))

    def test_format_thumbnail_file_label_shortens_long_names(self) -> None:
        self.assertEqual(format_thumbnail_file_label("pred_001.png"), "pred_001.png")
        self.assertEqual(
            format_thumbnail_file_label("pred_002_hand_reference_result_long_name.png", 24),
            "pred_002_hand_ref....png",
        )

    def test_format_thumbnail_file_size_reports_small_readable_size(self) -> None:
        self.assertEqual(format_thumbnail_file_size(512), "512 B")
        self.assertEqual(format_thumbnail_file_size(1536), "1.5 KB")

    def test_format_mask_candidate_message_reports_file_name(self) -> None:
        metadata = SelectedCandidateMetadata(
            source_path="project_output/predictions/pred_002.png",
            saved_path="project_output/selected/pred_002.png",
            file_name="pred_002.png",
            file_size_bytes=123,
        )

        self.assertEqual(
            format_mask_candidate_message(metadata),
            "Loaded selected candidate for mask editing: pred_002.png",
        )

    def test_normalize_mask_brush_size_keeps_small_supported_range(self) -> None:
        self.assertEqual(normalize_mask_brush_size(0), 1)
        self.assertEqual(normalize_mask_brush_size(18), 18)
        self.assertEqual(normalize_mask_brush_size(999), 80)
        self.assertEqual(normalize_mask_brush_size("not a number"), 18)

    def test_normalize_mask_tool_accepts_supported_tools(self) -> None:
        self.assertEqual(normalize_mask_tool("brush"), "brush")
        self.assertEqual(normalize_mask_tool("rectangle"), "rectangle")
        self.assertEqual(normalize_mask_tool("unknown"), "brush")


if __name__ == "__main__":
    unittest.main()
