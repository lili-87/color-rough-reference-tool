from pathlib import Path
import json
import tempfile
import unittest

from color_rough_ref_tool.core.prompt_metadata import (
    LATEST_PREDICTION_PROMPT_FILENAME,
    build_latest_prediction_prompt_metadata,
    save_latest_prediction_prompt_metadata,
)


TEST_TEMP_DIR = Path("tmp") / "tests"


class PromptMetadataTest(unittest.TestCase):
    def test_build_latest_prediction_prompt_metadata_strips_prompt_id(self) -> None:
        metadata = build_latest_prediction_prompt_metadata(" prompt-001 ")

        self.assertEqual(metadata.prompt_id, "prompt-001")

    def test_build_latest_prediction_prompt_metadata_rejects_empty_prompt_id(self) -> None:
        with self.assertRaises(ValueError):
            build_latest_prediction_prompt_metadata("  ")

    def test_save_latest_prediction_prompt_metadata_writes_json(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            metadata_dir = Path(temp_dir) / "project_output" / "metadata"

            metadata_path = save_latest_prediction_prompt_metadata(
                "prediction-001",
                metadata_dir,
            )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        self.assertEqual(metadata_path, metadata_dir / LATEST_PREDICTION_PROMPT_FILENAME)
        self.assertEqual(metadata["prompt_id"], "prediction-001")


if __name__ == "__main__":
    unittest.main()
