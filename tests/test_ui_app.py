from pathlib import Path
import unittest

from color_rough_ref_tool.core.settings import AppSettings
from color_rough_ref_tool.integrations.comfyui.prediction import PredictionOutputImage
from color_rough_ref_tool.ui.app import (
    SettingsFormValues,
    build_settings_from_form,
    format_configuration_message,
    format_prediction_output_count,
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


if __name__ == "__main__":
    unittest.main()
