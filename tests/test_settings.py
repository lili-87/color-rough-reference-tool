from pathlib import Path
import tempfile
import unittest

from color_rough_ref_tool.core.settings import AppSettings, load_settings, save_settings


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


if __name__ == "__main__":
    unittest.main()
