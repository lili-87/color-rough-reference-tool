from pathlib import Path
import json
import tempfile
import unittest

from color_rough_ref_tool.core.settings import AppSettings
from color_rough_ref_tool.integrations.comfyui.hand_inpainting import (
    HAND_MASK_IMAGE_PATH_PLACEHOLDER,
    SELECTED_CANDIDATE_IMAGE_PATH_PLACEHOLDER,
    inject_hand_inpainting_paths,
    load_hand_inpainting_workflow,
    read_hand_reference_outputs,
    trigger_hand_inpainting_workflow,
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


class ComfyUIHandInpaintingTest(unittest.TestCase):
    def test_load_hand_inpainting_workflow_reads_json_object(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            workflow_path = Path(temp_dir) / "hand_inpaint.json"
            workflow_path.write_text('{"10": {"class_type": "VAEEncodeForInpaint"}}\n', encoding="utf-8")

            workflow = load_hand_inpainting_workflow(workflow_path)

        self.assertEqual(workflow["10"]["class_type"], "VAEEncodeForInpaint")

    def test_load_hand_inpainting_workflow_rejects_placeholder(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            workflow_path = Path(temp_dir) / "hand_inpaint.json"
            workflow_path.write_text('{"placeholder": true, "nodes": {}}\n', encoding="utf-8")

            with self.assertRaises(ValueError):
                load_hand_inpainting_workflow(workflow_path)

    def test_trigger_hand_inpainting_workflow_uses_settings_workflow_path(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            workflow_path = Path(temp_dir) / "hand_inpaint.json"
            workflow_path.write_text('{"20": {"class_type": "KSampler"}}\n', encoding="utf-8")
            settings = AppSettings(
                comfyui_endpoint="http://localhost:8188",
                prediction_workflow_path="workflows/prediction.json",
                hand_inpainting_workflow_path=workflow_path.as_posix(),
                default_output_dir="project_output",
            )
            captured: dict[str, object] = {}

            def opener(request: object, timeout: float) -> FakeResponse:
                captured["url"] = request.full_url
                captured["body"] = json.loads(request.data.decode("utf-8"))
                return FakeResponse({"prompt_id": "hand-001"})

            result = trigger_hand_inpainting_workflow(
                settings,
                client_id="roughref-hand-test",
                opener=opener,
            )

        self.assertEqual(result.prompt_id, "hand-001")
        self.assertEqual(captured["url"], "http://localhost:8188/prompt")
        self.assertEqual(captured["body"]["client_id"], "roughref-hand-test")
        self.assertEqual(captured["body"]["prompt"]["20"]["class_type"], "KSampler")

    def test_inject_hand_inpainting_paths_replaces_nested_placeholders(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            selected_path = temp_path / "selected" / "pred_002.png"
            mask_path = temp_path / "masks" / "pred_002_hand_mask.png"
            selected_path.parent.mkdir()
            mask_path.parent.mkdir()
            selected_path.write_bytes(b"selected image bytes")
            mask_path.write_bytes(b"mask bytes")
            workflow = {
                "30": {
                    "inputs": {
                        "image": SELECTED_CANDIDATE_IMAGE_PATH_PLACEHOLDER,
                        "mask": HAND_MASK_IMAGE_PATH_PLACEHOLDER,
                        "notes": [
                            f"selected={SELECTED_CANDIDATE_IMAGE_PATH_PLACEHOLDER}",
                            f"mask={HAND_MASK_IMAGE_PATH_PLACEHOLDER}",
                        ],
                    }
                }
            }

            injected = inject_hand_inpainting_paths(
                workflow,
                selected_candidate_path=selected_path,
                mask_path=mask_path,
            )

        expected_selected = selected_path.resolve().as_posix()
        expected_mask = mask_path.resolve().as_posix()
        self.assertEqual(injected["30"]["inputs"]["image"], expected_selected)
        self.assertEqual(injected["30"]["inputs"]["mask"], expected_mask)
        self.assertEqual(injected["30"]["inputs"]["notes"][0], f"selected={expected_selected}")
        self.assertEqual(injected["30"]["inputs"]["notes"][1], f"mask={expected_mask}")
        self.assertEqual(
            workflow["30"]["inputs"]["image"],
            SELECTED_CANDIDATE_IMAGE_PATH_PLACEHOLDER,
        )

    def test_inject_hand_inpainting_paths_rejects_missing_selected_file(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            mask_path = Path(temp_dir) / "mask.png"
            mask_path.write_bytes(b"mask bytes")

            with self.assertRaises(FileNotFoundError):
                inject_hand_inpainting_paths(
                    {"30": {"inputs": {"image": SELECTED_CANDIDATE_IMAGE_PATH_PLACEHOLDER}}},
                    selected_candidate_path=Path(temp_dir) / "missing.png",
                    mask_path=mask_path,
                )

    def test_trigger_hand_inpainting_workflow_can_pass_selected_and_mask_paths(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            workflow_path = temp_path / "hand_inpaint.json"
            selected_path = temp_path / "selected.png"
            mask_path = temp_path / "mask.png"
            selected_path.write_bytes(b"selected image bytes")
            mask_path.write_bytes(b"mask bytes")
            workflow_path.write_text(
                json.dumps(
                    {
                        "40": {
                            "inputs": {
                                "image": SELECTED_CANDIDATE_IMAGE_PATH_PLACEHOLDER,
                                "mask": HAND_MASK_IMAGE_PATH_PLACEHOLDER,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            settings = AppSettings(
                comfyui_endpoint="http://localhost:8188",
                prediction_workflow_path="workflows/prediction.json",
                hand_inpainting_workflow_path=workflow_path.as_posix(),
                default_output_dir="project_output",
            )
            captured: dict[str, object] = {}

            def opener(request: object, timeout: float) -> FakeResponse:
                captured["body"] = json.loads(request.data.decode("utf-8"))
                return FakeResponse({"prompt_id": "hand-002"})

            result = trigger_hand_inpainting_workflow(
                settings,
                selected_candidate_path=selected_path,
                mask_path=mask_path,
                opener=opener,
            )

        prompt = captured["body"]["prompt"]
        self.assertEqual(result.prompt_id, "hand-002")
        self.assertEqual(prompt["40"]["inputs"]["image"], selected_path.resolve().as_posix())
        self.assertEqual(prompt["40"]["inputs"]["mask"], mask_path.resolve().as_posix())

    def test_trigger_hand_inpainting_workflow_requires_selected_and_mask_together(self) -> None:
        settings = AppSettings(hand_inpainting_workflow_path="workflows/hand_inpaint.json")

        with self.assertRaises(ValueError):
            trigger_hand_inpainting_workflow(
                settings,
                selected_candidate_path="selected.png",
                mask_path=None,
            )

    def test_read_hand_reference_outputs_returns_supported_images_sorted_by_name(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            output_dir = Path(temp_dir) / "hand_refs"
            output_dir.mkdir()
            (output_dir / "pred_002_hand_ref_002.webp").write_bytes(b"webp bytes")
            (output_dir / "notes.txt").write_text("not an image\n", encoding="utf-8")
            (output_dir / "pred_002_hand_ref_001.PNG").write_bytes(b"png bytes")
            (output_dir / "nested").mkdir()

            outputs = read_hand_reference_outputs(output_dir)

        self.assertEqual(
            [output.file_name for output in outputs],
            ["pred_002_hand_ref_001.PNG", "pred_002_hand_ref_002.webp"],
        )
        self.assertEqual(outputs[0].file_size_bytes, len(b"png bytes"))
        self.assertGreater(outputs[0].modified_time, 0)

    def test_read_hand_reference_outputs_returns_empty_tuple_for_empty_folder(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            output_dir = Path(temp_dir) / "hand_refs"
            output_dir.mkdir()

            outputs = read_hand_reference_outputs(output_dir)

        self.assertEqual(outputs, ())

    def test_read_hand_reference_outputs_rejects_missing_folder(self) -> None:
        with self.assertRaises(FileNotFoundError):
            read_hand_reference_outputs("missing_hand_refs")


if __name__ == "__main__":
    unittest.main()
