from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from color_rough_ref_tool.core.hand_reference_sheet import (
    HAND_REFERENCE_SHEET_FILENAME,
    SHEET_GAP,
    SHEET_PADDING,
    export_hand_reference_sheet,
)
from color_rough_ref_tool.integrations.comfyui.hand_inpainting import HandReferenceOutputImage


TEST_TEMP_DIR = Path("tmp") / "tests"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class HandReferenceSheetTest(unittest.TestCase):
    def test_export_hand_reference_sheet_writes_simple_png_grid(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            hand_refs_dir = temp_path / "project_output" / "hand_refs"
            sheets_dir = temp_path / "project_output" / "sheets"
            hand_refs_dir.mkdir(parents=True)
            first_image = hand_refs_dir / "pred_002_hand_ref_001.png"
            second_image = hand_refs_dir / "pred_002_hand_ref_002.png"
            _write_rgb_png(first_image, width=2, height=2, rgb=(255, 0, 0))
            _write_rgb_png(second_image, width=2, height=2, rgb=(0, 0, 255))
            outputs = (
                _output_image(first_image),
                _output_image(second_image),
            )

            sheet_path = export_hand_reference_sheet(
                outputs,
                sheets_dir,
                columns=2,
                thumbnail_max_size=2,
            )
            data = sheet_path.read_bytes()

        self.assertEqual(sheet_path, sheets_dir / HAND_REFERENCE_SHEET_FILENAME)
        self.assertTrue(data.startswith(PNG_SIGNATURE))
        self.assertEqual(data[12:16], b"IHDR")
        self.assertEqual(
            struct.unpack(">II", data[16:24]),
            ((SHEET_PADDING * 2) + (2 * 2) + SHEET_GAP, (SHEET_PADDING * 2) + 2),
        )

    def test_export_hand_reference_sheet_rejects_empty_sources(self) -> None:
        with self.assertRaises(ValueError):
            export_hand_reference_sheet((), "project_output/sheets")

    def test_export_hand_reference_sheet_rejects_non_png_source(self) -> None:
        with self.assertRaises(ValueError):
            export_hand_reference_sheet(
                (
                    HandReferenceOutputImage(
                        path=Path("project_output/hand_refs/ref.jpg"),
                        file_name="ref.jpg",
                        file_size_bytes=10,
                        modified_time=1.0,
                    ),
                ),
                "project_output/sheets",
            )


def _output_image(path: Path) -> HandReferenceOutputImage:
    stat = path.stat()
    return HandReferenceOutputImage(
        path=path,
        file_name=path.name,
        file_size_bytes=stat.st_size,
        modified_time=stat.st_mtime,
    )


def _write_rgb_png(path: Path, *, width: int, height: int, rgb: tuple[int, int, int]) -> None:
    pixels = bytes(rgb) * (width * height)
    rows = [
        b"\x00" + pixels[y * width * 3 : (y + 1) * width * 3]
        for y in range(height)
    ]
    path.write_bytes(
        b"".join(
            (
                PNG_SIGNATURE,
                _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
                _png_chunk(b"IDAT", zlib.compress(b"".join(rows))),
                _png_chunk(b"IEND", b""),
            )
        )
    )


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", checksum)


if __name__ == "__main__":
    unittest.main()
