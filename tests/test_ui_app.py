from pathlib import Path
import unittest

from color_rough_ref_tool.core.settings import AppSettings
from color_rough_ref_tool.integrations.comfyui.prediction import (
    PredictionOutputImage,
    PredictionOutputReadResult,
    SavedPredictionCandidate,
)
from color_rough_ref_tool.ui.app import (
    SettingsFormValues,
    build_settings_from_form,
    format_configuration_message,
    format_prediction_output_count,
    format_prediction_output_result,
    format_saved_prediction_message,
    format_selected_prediction_message,
    prediction_output_folder,
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

    def test_prediction_output_folder_uses_default_output_dir(self) -> None:
        settings = AppSettings(default_output_dir="custom_output")

        folder = prediction_output_folder(settings)

        self.assertEqual(folder.as_posix(), "custom_output/predictions")

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


if __name__ == "__main__":
    unittest.main()
