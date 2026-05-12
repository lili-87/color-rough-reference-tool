from pathlib import Path
import json
import tempfile
import unittest

from color_rough_ref_tool.core.prediction_metadata import (
    PREDICTION_METADATA_FILENAME,
    build_prediction_metadata,
    save_prediction_metadata,
)
from color_rough_ref_tool.integrations.comfyui.prediction import PredictionOutputImage


TEST_TEMP_DIR = Path("tmp") / "tests"


class PredictionMetadataTest(unittest.TestCase):
    def test_build_prediction_metadata_uses_output_images(self) -> None:
        outputs = (
            PredictionOutputImage(
                path=Path("project_output/predictions/pred_001.png"),
                file_name="pred_001.png",
                file_size_bytes=10,
                modified_time=1.5,
            ),
        )

        metadata = build_prediction_metadata(outputs)

        self.assertEqual(len(metadata.predictions), 1)
        self.assertEqual(metadata.predictions[0].path, "project_output/predictions/pred_001.png")
        self.assertEqual(metadata.predictions[0].file_name, "pred_001.png")
        self.assertEqual(metadata.predictions[0].file_size_bytes, 10)
        self.assertEqual(metadata.predictions[0].modified_time, 1.5)

    def test_save_prediction_metadata_writes_predictions_json(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            metadata_dir = temp_path / "project_output" / "metadata"
            outputs = (
                PredictionOutputImage(
                    path=temp_path / "project_output" / "predictions" / "pred_001.png",
                    file_name="pred_001.png",
                    file_size_bytes=10,
                    modified_time=1.5,
                ),
                PredictionOutputImage(
                    path=temp_path / "project_output" / "predictions" / "pred_002.webp",
                    file_name="pred_002.webp",
                    file_size_bytes=20,
                    modified_time=2.5,
                ),
            )

            metadata_path = save_prediction_metadata(outputs, metadata_dir)
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        self.assertEqual(metadata_path, metadata_dir / PREDICTION_METADATA_FILENAME)
        self.assertEqual(len(metadata["predictions"]), 2)
        self.assertEqual(metadata["predictions"][0]["file_name"], "pred_001.png")
        self.assertEqual(metadata["predictions"][0]["file_size_bytes"], 10)
        self.assertEqual(metadata["predictions"][1]["file_name"], "pred_002.webp")
        self.assertEqual(metadata["predictions"][1]["modified_time"], 2.5)


if __name__ == "__main__":
    unittest.main()
