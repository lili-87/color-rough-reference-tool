from pathlib import Path
import json
import tempfile
import unittest

from color_rough_ref_tool.core.settings import AppSettings
from color_rough_ref_tool.integrations.comfyui.prediction import (
    COLOR_ROUGH_IMAGE_PATH_PLACEHOLDER,
    inject_color_rough_path,
    load_prediction_workflow,
    queue_comfyui_prompt,
    read_prediction_outputs,
    read_prediction_outputs_safely,
    save_selected_prediction_candidate,
    trigger_prediction_workflow,
)


TEST_TEMP_DIR = Path("tmp") / "tests"


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class ComfyUIPredictionTest(unittest.TestCase):
    def test_load_prediction_workflow_reads_json_object(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            workflow_path = Path(temp_dir) / "prediction.json"
            workflow_path.write_text('{"3": {"class_type": "CheckpointLoaderSimple"}}\n', encoding="utf-8")

            workflow = load_prediction_workflow(workflow_path)

        self.assertEqual(workflow["3"]["class_type"], "CheckpointLoaderSimple")

    def test_load_prediction_workflow_rejects_placeholder(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            workflow_path = Path(temp_dir) / "prediction.json"
            workflow_path.write_text('{"placeholder": true, "nodes": {}}\n', encoding="utf-8")

            with self.assertRaises(ValueError):
                load_prediction_workflow(workflow_path)

    def test_queue_comfyui_prompt_posts_to_prompt_endpoint(self) -> None:
        captured: dict[str, object] = {}

        def opener(request: object, timeout: float) -> FakeResponse:
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["method"] = request.get_method()
            return FakeResponse({"prompt_id": "abc123", "number": 1})

        result = queue_comfyui_prompt(
            endpoint="http://127.0.0.1:8188/",
            workflow={"3": {"class_type": "CheckpointLoaderSimple"}},
            client_id="roughref-test",
            timeout_seconds=12,
            opener=opener,
        )

        self.assertEqual(result.prompt_id, "abc123")
        self.assertEqual(captured["url"], "http://127.0.0.1:8188/prompt")
        self.assertEqual(captured["timeout"], 12)
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["body"]["client_id"], "roughref-test")
        self.assertIn("prompt", captured["body"])

    def test_inject_color_rough_path_replaces_nested_placeholders(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            image_path = Path(temp_dir) / "rough.png"
            image_path.write_bytes(b"placeholder image bytes")
            workflow = {
                "10": {
                    "inputs": {
                        "image": COLOR_ROUGH_IMAGE_PATH_PLACEHOLDER,
                        "notes": ["input", f"path={COLOR_ROUGH_IMAGE_PATH_PLACEHOLDER}"],
                    }
                }
            }

            injected = inject_color_rough_path(workflow, image_path)

        expected_path = image_path.resolve().as_posix()
        self.assertEqual(injected["10"]["inputs"]["image"], expected_path)
        self.assertEqual(injected["10"]["inputs"]["notes"][1], f"path={expected_path}")
        self.assertEqual(workflow["10"]["inputs"]["image"], COLOR_ROUGH_IMAGE_PATH_PLACEHOLDER)

    def test_inject_color_rough_path_rejects_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            inject_color_rough_path(
                {"10": {"inputs": {"image": COLOR_ROUGH_IMAGE_PATH_PLACEHOLDER}}},
                "missing.png",
            )

    def test_trigger_prediction_workflow_uses_settings_workflow_path(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            workflow_path = Path(temp_dir) / "prediction.json"
            workflow_path.write_text('{"3": {"class_type": "KSampler"}}\n', encoding="utf-8")
            settings = AppSettings(
                comfyui_endpoint="http://localhost:8188",
                prediction_workflow_path=workflow_path.as_posix(),
                hand_inpainting_workflow_path="workflows/hand_inpaint.json",
                default_output_dir="project_output",
            )

            def opener(request: object, timeout: float) -> FakeResponse:
                return FakeResponse({"prompt_id": "prediction-001"})

            result = trigger_prediction_workflow(settings, opener=opener)

        self.assertEqual(result.prompt_id, "prediction-001")

    def test_trigger_prediction_workflow_can_pass_color_rough_path(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            workflow_path = Path(temp_dir) / "prediction.json"
            image_path = Path(temp_dir) / "rough.png"
            image_path.write_bytes(b"placeholder image bytes")
            workflow_path.write_text(
                json.dumps(
                    {
                        "10": {
                            "class_type": "LoadImage",
                            "inputs": {"image": COLOR_ROUGH_IMAGE_PATH_PLACEHOLDER},
                        }
                    }
                ),
                encoding="utf-8",
            )
            settings = AppSettings(
                comfyui_endpoint="http://localhost:8188",
                prediction_workflow_path=workflow_path.as_posix(),
                hand_inpainting_workflow_path="workflows/hand_inpaint.json",
                default_output_dir="project_output",
            )
            captured: dict[str, object] = {}

            def opener(request: object, timeout: float) -> FakeResponse:
                captured["body"] = json.loads(request.data.decode("utf-8"))
                return FakeResponse({"prompt_id": "prediction-002"})

            result = trigger_prediction_workflow(
                settings,
                color_rough_path=image_path,
                opener=opener,
            )

        prompt = captured["body"]["prompt"]
        self.assertEqual(result.prompt_id, "prediction-002")
        self.assertEqual(prompt["10"]["inputs"]["image"], image_path.resolve().as_posix())

    def test_read_prediction_outputs_returns_supported_images_sorted_by_name(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            output_dir = Path(temp_dir) / "predictions"
            output_dir.mkdir()
            (output_dir / "pred_002.webp").write_bytes(b"webp bytes")
            (output_dir / "notes.txt").write_text("not an image\n", encoding="utf-8")
            (output_dir / "pred_001.PNG").write_bytes(b"png bytes")
            (output_dir / "nested").mkdir()

            outputs = read_prediction_outputs(output_dir)

        self.assertEqual([output.file_name for output in outputs], ["pred_001.PNG", "pred_002.webp"])
        self.assertEqual(outputs[0].file_size_bytes, len(b"png bytes"))
        self.assertGreater(outputs[0].modified_time, 0)

    def test_read_prediction_outputs_returns_empty_tuple_for_empty_folder(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            output_dir = Path(temp_dir) / "predictions"
            output_dir.mkdir()

            outputs = read_prediction_outputs(output_dir)

        self.assertEqual(outputs, ())

    def test_read_prediction_outputs_rejects_missing_folder(self) -> None:
        with self.assertRaises(FileNotFoundError):
            read_prediction_outputs("missing_predictions")

    def test_read_prediction_outputs_safely_reports_empty_folder(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            output_dir = Path(temp_dir) / "predictions"
            output_dir.mkdir()

            result = read_prediction_outputs_safely(output_dir)

        self.assertFalse(result.ok)
        self.assertEqual(result.images, ())
        self.assertIn("No prediction images were found", result.messages[0])

    def test_read_prediction_outputs_safely_reports_missing_folder(self) -> None:
        result = read_prediction_outputs_safely("missing_predictions")

        self.assertFalse(result.ok)
        self.assertEqual(result.images, ())
        self.assertIn("Prediction output folder does not exist", result.messages[0])

    def test_read_prediction_outputs_safely_reports_non_folder_path(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            output_path = Path(temp_dir) / "predictions.txt"
            output_path.write_text("not a folder\n", encoding="utf-8")

            result = read_prediction_outputs_safely(output_path)

        self.assertFalse(result.ok)
        self.assertIn("must be a folder", result.messages[0])

    def test_save_selected_prediction_candidate_copies_image_to_selected_folder(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "pred_002.PNG"
            selected_dir = temp_path / "project_output" / "selected"
            source_path.write_bytes(b"selected prediction bytes")

            saved = save_selected_prediction_candidate(source_path, selected_dir)

            self.assertEqual(saved.source_path, source_path)
            self.assertEqual(saved.saved_path, selected_dir / "pred_002.PNG")
            self.assertEqual(saved.saved_path.read_bytes(), b"selected prediction bytes")

    def test_save_selected_prediction_candidate_rejects_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            save_selected_prediction_candidate("missing_prediction.png", "project_output/selected")

    def test_save_selected_prediction_candidate_rejects_unsupported_file(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            source_path = Path(temp_dir) / "pred_002.txt"
            source_path.write_text("not an image\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                save_selected_prediction_candidate(source_path, Path(temp_dir) / "selected")


if __name__ == "__main__":
    unittest.main()
