from pathlib import Path
import struct
import tempfile
import unittest

from color_rough_ref_tool.core.mask_image import (
    BrushMaskStroke,
    RectangleMask,
    mask_file_name_for_candidate,
    save_mask_png,
)


TEST_TEMP_DIR = Path("tmp") / "tests"


class MaskImageTest(unittest.TestCase):
    def test_mask_file_name_for_candidate_uses_candidate_stem(self) -> None:
        self.assertEqual(
            mask_file_name_for_candidate("pred_002.png"),
            "pred_002_hand_mask.png",
        )

    def test_save_mask_png_writes_png_file(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            masks_dir = Path(temp_dir) / "project_output" / "masks"

            saved_path = save_mask_png(
                width=12,
                height=8,
                operations=(
                    BrushMaskStroke(start=(2, 2), end=(8, 2), size=3),
                    RectangleMask(start=(3, 3), end=(5, 5)),
                ),
                masks_dir=masks_dir,
                candidate_file_name="pred_002.png",
            )
            data = saved_path.read_bytes()

        self.assertEqual(saved_path, masks_dir / "pred_002_hand_mask.png")
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(data[12:16], b"IHDR")
        self.assertEqual(struct.unpack(">II", data[16:24]), (12, 8))

    def test_save_mask_png_rejects_empty_operations(self) -> None:
        with self.assertRaises(ValueError):
            save_mask_png(
                width=12,
                height=8,
                operations=(),
                masks_dir="project_output/masks",
                candidate_file_name="pred_002.png",
            )


if __name__ == "__main__":
    unittest.main()
