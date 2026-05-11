import unittest

from color_rough_ref_tool.core.settings import AppSettings
from color_rough_ref_tool.ui.app import (
    SettingsFormValues,
    build_settings_from_form,
    format_configuration_message,
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


if __name__ == "__main__":
    unittest.main()
