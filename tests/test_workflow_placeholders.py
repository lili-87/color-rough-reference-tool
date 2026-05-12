from pathlib import Path
import tempfile
import unittest

from color_rough_ref_tool.integrations.comfyui.workflow_placeholders import (
    HAND_INPAINTING_WORKFLOW_NAME,
    PREDICTION_WORKFLOW_NAME,
    prepare_workflow_placeholders,
    validate_hand_inpainting_workflow_placeholders,
    validate_prediction_workflow_placeholders,
)


TEST_TEMP_DIR = Path("tmp") / "tests"


class WorkflowPlaceholderTest(unittest.TestCase):
    def test_prepare_workflow_placeholders_creates_missing_files(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            paths = prepare_workflow_placeholders(Path(temp_dir) / "workflows")

            self.assertTrue(paths.prediction.is_file())
            self.assertTrue(paths.hand_inpainting.is_file())
            self.assertEqual(paths.prediction.name, PREDICTION_WORKFLOW_NAME)
            self.assertEqual(paths.hand_inpainting.name, HAND_INPAINTING_WORKFLOW_NAME)

    def test_prepare_workflow_placeholders_keeps_existing_files(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            workflow_dir = Path(temp_dir) / "workflows"
            workflow_dir.mkdir()
            prediction_path = workflow_dir / PREDICTION_WORKFLOW_NAME
            prediction_path.write_text('{"custom": true}\n', encoding="utf-8")

            paths = prepare_workflow_placeholders(workflow_dir)

            self.assertEqual(paths.prediction.read_text(encoding="utf-8"), '{"custom": true}\n')

    def test_validate_prediction_workflow_placeholders_accepts_color_rough_placeholder(self) -> None:
        result = validate_prediction_workflow_placeholders(
            {
                "10": {
                    "inputs": {
                        "image": "{{COLOR_ROUGH_IMAGE_PATH}}",
                    }
                }
            }
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.missing_requirements, ())

    def test_validate_prediction_workflow_placeholders_reports_missing_color_rough(self) -> None:
        result = validate_prediction_workflow_placeholders(
            {
                "10": {
                    "inputs": {
                        "image": "rough.png",
                    }
                }
            }
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.missing_requirements, ("color rough image",))

    def test_validate_hand_inpainting_workflow_placeholders_requires_selected_and_mask(self) -> None:
        result = validate_hand_inpainting_workflow_placeholders(
            {
                "20": {
                    "inputs": {
                        "image": "{{SELECTED_CANDIDATE_IMAGE_PATH}}",
                        "mask": "{{HAND_MASK_IMAGE_PATH}}",
                    }
                }
            }
        )

        self.assertTrue(result.ok)

    def test_validate_hand_inpainting_workflow_placeholders_reports_missing_mask(self) -> None:
        result = validate_hand_inpainting_workflow_placeholders(
            {
                "20": {
                    "inputs": {
                        "image": "{{SELECTED_CANDIDATE_IMAGE_PATH}}",
                    }
                }
            }
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.missing_requirements, ("hand mask image",))


if __name__ == "__main__":
    unittest.main()
