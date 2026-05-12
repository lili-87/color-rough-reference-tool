from pathlib import Path
import json
import tempfile
import unittest

from color_rough_ref_tool.core.hand_reference_metadata import (
    HAND_REFERENCE_METADATA_FILENAME,
    build_hand_reference_metadata,
    save_hand_reference_metadata,
)
from color_rough_ref_tool.integrations.comfyui.hand_inpainting import HandReferenceOutputImage


TEST_TEMP_DIR = Path("tmp") / "tests"


class HandReferenceMetadataTest(unittest.TestCase):
    def test_build_hand_reference_metadata_uses_output_images(self) -> None:
        outputs = (
            HandReferenceOutputImage(
                path=Path("project_output/hand_refs/pred_002_hand_ref_001.png"),
                file_name="pred_002_hand_ref_001.png",
                file_size_bytes=10,
                modified_time=1.5,
            ),
        )

        metadata = build_hand_reference_metadata(outputs)

        self.assertEqual(len(metadata.hand_refs), 1)
        self.assertEqual(
            metadata.hand_refs[0].path,
            "project_output/hand_refs/pred_002_hand_ref_001.png",
        )
        self.assertEqual(metadata.hand_refs[0].file_name, "pred_002_hand_ref_001.png")
        self.assertEqual(metadata.hand_refs[0].file_size_bytes, 10)
        self.assertEqual(metadata.hand_refs[0].modified_time, 1.5)

    def test_save_hand_reference_metadata_writes_hand_refs_json(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            metadata_dir = temp_path / "project_output" / "metadata"
            outputs = (
                HandReferenceOutputImage(
                    path=temp_path / "project_output" / "hand_refs" / "pred_002_hand_ref_001.png",
                    file_name="pred_002_hand_ref_001.png",
                    file_size_bytes=10,
                    modified_time=1.5,
                ),
                HandReferenceOutputImage(
                    path=temp_path / "project_output" / "hand_refs" / "pred_002_hand_ref_002.webp",
                    file_name="pred_002_hand_ref_002.webp",
                    file_size_bytes=20,
                    modified_time=2.5,
                ),
            )

            metadata_path = save_hand_reference_metadata(outputs, metadata_dir)
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        self.assertEqual(metadata_path, metadata_dir / HAND_REFERENCE_METADATA_FILENAME)
        self.assertEqual(len(metadata["hand_refs"]), 2)
        self.assertEqual(metadata["hand_refs"][0]["file_name"], "pred_002_hand_ref_001.png")
        self.assertEqual(metadata["hand_refs"][0]["file_size_bytes"], 10)
        self.assertEqual(metadata["hand_refs"][1]["file_name"], "pred_002_hand_ref_002.webp")
        self.assertEqual(metadata["hand_refs"][1]["modified_time"], 2.5)


if __name__ == "__main__":
    unittest.main()
