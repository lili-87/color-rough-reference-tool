from pathlib import Path
import tempfile
import unittest

from color_rough_ref_tool.core.project_output import (
    OUTPUT_SUBDIRS,
    prepare_project_output,
)


TEST_TEMP_DIR = Path("tmp") / "tests"


class ProjectOutputTest(unittest.TestCase):
    def test_prepare_project_output_creates_standard_folders(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            root = Path(temp_dir) / "project_output"

            folders = prepare_project_output(root)

            self.assertEqual(folders.root, root)
            for subdir in OUTPUT_SUBDIRS:
                self.assertTrue((root / subdir).is_dir())


if __name__ == "__main__":
    unittest.main()
