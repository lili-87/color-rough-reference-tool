from pathlib import Path
import json
import tempfile
import unittest

from color_rough_ref_tool.core.selection_metadata import (
    SELECTED_CANDIDATE_METADATA_FILENAME,
    build_selected_candidate_metadata,
    load_selected_candidate_metadata,
    save_selected_candidate_metadata,
)


TEST_TEMP_DIR = Path("tmp") / "tests"


class SelectionMetadataTest(unittest.TestCase):
    def test_build_selected_candidate_metadata_reads_saved_file(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "predictions" / "pred_002.png"
            saved_path = temp_path / "selected" / "pred_002.png"
            saved_path.parent.mkdir()
            saved_path.write_bytes(b"selected bytes")

            metadata = build_selected_candidate_metadata(source_path, saved_path)

        self.assertEqual(metadata.source_path, source_path.as_posix())
        self.assertEqual(metadata.saved_path, saved_path.as_posix())
        self.assertEqual(metadata.file_name, "pred_002.png")
        self.assertEqual(metadata.file_size_bytes, len(b"selected bytes"))

    def test_save_selected_candidate_metadata_writes_json_file(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "predictions" / "pred_003.webp"
            saved_path = temp_path / "selected" / "pred_003.webp"
            metadata_dir = temp_path / "metadata"
            saved_path.parent.mkdir()
            saved_path.write_bytes(b"webp bytes")

            metadata_path = save_selected_candidate_metadata(
                source_path,
                saved_path,
                metadata_dir,
            )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

            self.assertEqual(
                metadata_path,
                metadata_dir / SELECTED_CANDIDATE_METADATA_FILENAME,
            )
            self.assertEqual(metadata["source_path"], source_path.as_posix())
            self.assertEqual(metadata["saved_path"], saved_path.as_posix())
            self.assertEqual(metadata["file_name"], "pred_003.webp")
            self.assertEqual(metadata["file_size_bytes"], len(b"webp bytes"))

    def test_load_selected_candidate_metadata_reads_json_file(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            metadata_dir = Path(temp_dir) / "metadata"
            metadata_dir.mkdir()
            metadata_path = metadata_dir / SELECTED_CANDIDATE_METADATA_FILENAME
            metadata_path.write_text(
                json.dumps(
                    {
                        "source_path": "project_output/predictions/pred_002.png",
                        "saved_path": "project_output/selected/pred_002.png",
                        "file_name": "pred_002.png",
                        "file_size_bytes": 123,
                    }
                ),
                encoding="utf-8",
            )

            metadata = load_selected_candidate_metadata(metadata_dir)

        self.assertEqual(metadata.source_path, "project_output/predictions/pred_002.png")
        self.assertEqual(metadata.saved_path, "project_output/selected/pred_002.png")
        self.assertEqual(metadata.file_name, "pred_002.png")
        self.assertEqual(metadata.file_size_bytes, 123)

    def test_build_selected_candidate_metadata_rejects_missing_saved_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            build_selected_candidate_metadata(
                "project_output/predictions/pred_004.png",
                "project_output/selected/pred_004.png",
            )

    def test_load_selected_candidate_metadata_rejects_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_selected_candidate_metadata("project_output/metadata")

    def test_load_selected_candidate_metadata_rejects_invalid_shape(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            metadata_dir = Path(temp_dir) / "metadata"
            metadata_dir.mkdir()
            metadata_path = metadata_dir / SELECTED_CANDIDATE_METADATA_FILENAME
            metadata_path.write_text('{"saved_path": 42}\n', encoding="utf-8")

            with self.assertRaises(ValueError):
                load_selected_candidate_metadata(metadata_dir)


if __name__ == "__main__":
    unittest.main()
