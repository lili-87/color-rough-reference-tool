from pathlib import Path
import tempfile
import unittest

from color_rough_ref_tool.core.color_rough_input import select_color_rough_image


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


if __name__ == "__main__":
    unittest.main()
