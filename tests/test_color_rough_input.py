from pathlib import Path
import tempfile
import unittest

from color_rough_ref_tool.core.color_rough_input import (
    build_color_rough_preview,
    save_color_rough_to_project_input,
    select_color_rough_image,
)
from color_rough_ref_tool.core.project_output import prepare_project_output


TEST_TEMP_DIR = Path("tmp") / "tests"


class ColorRoughInputTest(unittest.TestCase):
    def test_select_color_rough_image_accepts_existing_file(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            image_path = Path(temp_dir) / "rough.png"
            image_path.write_bytes(b"placeholder image bytes")

            selection = select_color_rough_image(image_path)

            self.assertEqual(selection.path, image_path)
            self.assertEqual(selection.file_name, "rough.png")

    def test_select_color_rough_image_rejects_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            select_color_rough_image("missing.png")

    def test_select_color_rough_image_rejects_directory(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            with self.assertRaises(ValueError):
                select_color_rough_image(temp_dir)

    def test_build_color_rough_preview_returns_display_metadata(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            image_path = Path(temp_dir) / "rough.png"
            image_bytes = b"placeholder image bytes"
            image_path.write_bytes(image_bytes)
            selection = select_color_rough_image(image_path)

            preview = build_color_rough_preview(selection)

            self.assertEqual(preview.path, image_path.resolve())
            self.assertEqual(preview.file_name, "rough.png")
            self.assertTrue(preview.file_uri.startswith("file:///"))
            self.assertEqual(preview.file_size_bytes, len(image_bytes))

    def test_save_color_rough_to_project_input_copies_selected_file(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            workspace = Path(temp_dir)
            image_path = workspace / "rough.PNG"
            image_bytes = b"placeholder image bytes"
            image_path.write_bytes(image_bytes)
            selection = select_color_rough_image(image_path)
            output_folders = prepare_project_output(workspace / "project_output")

            saved = save_color_rough_to_project_input(selection, output_folders)

            self.assertEqual(saved.source_path, image_path)
            self.assertEqual(saved.saved_path, output_folders.input / "color_rough.png")
            self.assertEqual(saved.saved_path.read_bytes(), image_bytes)


if __name__ == "__main__":
    unittest.main()
