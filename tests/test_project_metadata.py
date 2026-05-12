from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile
import unittest

from color_rough_ref_tool.core.project_metadata import (
    APPLICATION_NAME,
    PROJECT_METADATA_FILENAME,
    PROJECT_METADATA_SCHEMA_VERSION,
    build_project_metadata,
    save_project_metadata,
)


TEST_TEMP_DIR = Path("tmp") / "tests"


class ProjectMetadataTest(unittest.TestCase):
    def test_build_project_metadata_uses_project_root_and_timestamp(self) -> None:
        created_at = datetime(2026, 5, 12, 3, 4, 5, tzinfo=timezone.utc)

        metadata = build_project_metadata("project_output", created_at=created_at)

        self.assertEqual(metadata.schema_version, PROJECT_METADATA_SCHEMA_VERSION)
        self.assertEqual(metadata.application_name, APPLICATION_NAME)
        self.assertEqual(metadata.project_root, "project_output")
        self.assertEqual(metadata.created_at, "2026-05-12T03:04:05+00:00")

    def test_save_project_metadata_writes_project_json(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            project_root = temp_path / "project_output"
            metadata_dir = project_root / "metadata"
            created_at = datetime(2026, 5, 12, 3, 4, 5, tzinfo=timezone.utc)

            metadata_path = save_project_metadata(
                project_root,
                metadata_dir,
                created_at=created_at,
            )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        self.assertEqual(metadata_path, metadata_dir / PROJECT_METADATA_FILENAME)
        self.assertEqual(metadata["schema_version"], PROJECT_METADATA_SCHEMA_VERSION)
        self.assertEqual(metadata["application_name"], APPLICATION_NAME)
        self.assertEqual(metadata["project_root"], project_root.as_posix())
        self.assertEqual(metadata["created_at"], "2026-05-12T03:04:05+00:00")


if __name__ == "__main__":
    unittest.main()
