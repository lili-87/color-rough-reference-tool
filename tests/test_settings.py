from pathlib import Path
import tempfile
import unittest

from color_rough_ref_tool.core.settings import (
    AppSettings,
    load_settings,
    normalize_comfyui_endpoint,
    normalize_workflow_file_path,
    save_settings,
    with_comfyui_endpoint,
    with_hand_inpainting_workflow_path,
    with_prediction_workflow_path,
)


TEST_TEMP_DIR = Path("tmp") / "tests"


class SettingsStorageTest(unittest.TestCase):
    def test_missing_file_returns_default_settings(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"

            settings = load_settings(settings_path)

        self.assertEqual(settings, AppSettings())

    def test_save_and_load_settings(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            original = AppSettings(
                comfyui_endpoint="http://127.0.0.1:8188",
                prediction_workflow_path="workflows/prediction.json",
                hand_inpainting_workflow_path="workflows/hand_inpaint.json",
                default_output_dir="project_output",
            )

            saved_path = save_settings(original, settings_path)
            loaded = load_settings(settings_path)

        self.assertEqual(saved_path, settings_path)
        self.assertEqual(loaded, original)

    def test_normalize_comfyui_endpoint_accepts_http_url(self) -> None:
        endpoint = normalize_comfyui_endpoint(" http://127.0.0.1:8188/ ")

        self.assertEqual(endpoint, "http://127.0.0.1:8188")

    def test_normalize_comfyui_endpoint_rejects_non_http_url(self) -> None:
        with self.assertRaises(ValueError):
            normalize_comfyui_endpoint("file:///ComfyUI")

    def test_with_comfyui_endpoint_updates_only_endpoint(self) -> None:
        settings = AppSettings(
            comfyui_endpoint="http://127.0.0.1:8188",
            prediction_workflow_path="workflows/prediction.json",
            hand_inpainting_workflow_path="workflows/hand_inpaint.json",
            default_output_dir="project_output",
        )

        updated = with_comfyui_endpoint(settings, "http://localhost:8188/")

        self.assertEqual(updated.comfyui_endpoint, "http://localhost:8188")
        self.assertEqual(updated.prediction_workflow_path, settings.prediction_workflow_path)
        self.assertEqual(
            updated.hand_inpainting_workflow_path,
            settings.hand_inpainting_workflow_path,
        )
        self.assertEqual(updated.default_output_dir, settings.default_output_dir)

    def test_normalize_workflow_file_path_accepts_json_path(self) -> None:
        workflow_path = normalize_workflow_file_path(" workflows/prediction_workflow.JSON ")

        self.assertEqual(workflow_path, "workflows/prediction_workflow.JSON")

    def test_normalize_workflow_file_path_rejects_non_json_path(self) -> None:
        with self.assertRaises(ValueError):
            normalize_workflow_file_path("workflows/prediction_workflow.txt")

    def test_normalize_workflow_file_path_rejects_existing_directory(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            with self.assertRaises(ValueError):
                normalize_workflow_file_path(temp_dir)

    def test_with_prediction_workflow_path_updates_only_prediction_workflow(self) -> None:
        settings = AppSettings(
            comfyui_endpoint="http://127.0.0.1:8188",
            prediction_workflow_path="workflows/prediction.json",
            hand_inpainting_workflow_path="workflows/hand_inpaint.json",
            default_output_dir="project_output",
        )

        updated = with_prediction_workflow_path(
            settings,
            "workflows/new_prediction.json",
        )

        self.assertEqual(updated.comfyui_endpoint, settings.comfyui_endpoint)
        self.assertEqual(updated.prediction_workflow_path, "workflows/new_prediction.json")
        self.assertEqual(
            updated.hand_inpainting_workflow_path,
            settings.hand_inpainting_workflow_path,
        )
        self.assertEqual(updated.default_output_dir, settings.default_output_dir)

    def test_with_hand_inpainting_workflow_path_updates_only_hand_workflow(self) -> None:
        settings = AppSettings(
            comfyui_endpoint="http://127.0.0.1:8188",
            prediction_workflow_path="workflows/prediction.json",
            hand_inpainting_workflow_path="workflows/hand_inpaint.json",
            default_output_dir="project_output",
        )

        updated = with_hand_inpainting_workflow_path(
            settings,
            "workflows/new_hand_inpaint.json",
        )

        self.assertEqual(updated.comfyui_endpoint, settings.comfyui_endpoint)
        self.assertEqual(updated.prediction_workflow_path, settings.prediction_workflow_path)
        self.assertEqual(
            updated.hand_inpainting_workflow_path,
            "workflows/new_hand_inpaint.json",
        )
        self.assertEqual(updated.default_output_dir, settings.default_output_dir)


if __name__ == "__main__":
    unittest.main()
