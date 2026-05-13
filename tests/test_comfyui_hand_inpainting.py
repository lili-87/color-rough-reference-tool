from pathlib import Path
import json
import tempfile
import unittest

from color_rough_ref_tool.core.prompt_metadata import save_latest_hand_reference_prompt_metadata
from color_rough_ref_tool.core.settings import AppSettings
from color_rough_ref_tool.integrations.comfyui.hand_inpainting import (
    HAND_MASK_IMAGE_PATH_PLACEHOLDER,
    SELECTED_CANDIDATE_IMAGE_PATH_PLACEHOLDER,
    HandReferenceHistoryImage,
    HandReferenceHistoryInspection,
    copy_finished_hand_reference_images,
    download_finished_hand_reference_images,
    fetch_latest_hand_reference_history,
    inject_hand_inpainting_paths,
    inspect_hand_reference_history,
    load_hand_inpainting_workflow,
    read_hand_reference_outputs,
    read_hand_reference_outputs_safely,
    trigger_hand_inpainting_workflow,
)
from color_rough_ref_tool.integrations.comfyui.prediction import ComfyUIHistoryResult


TEST_TEMP_DIR = Path("tmp") / "tests_hand_inpainting"


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class FakeBytesResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeBytesResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


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

    def test_fetch_latest_hand_reference_history_uses_saved_prompt_id(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            metadata_dir = Path(temp_dir) / "project_output" / "metadata"
            save_latest_hand_reference_prompt_metadata("hand-003", metadata_dir)
            settings = AppSettings(comfyui_endpoint="http://localhost:8188")
            captured: dict[str, object] = {}

            def opener(request: object, timeout: float) -> FakeResponse:
                captured["url"] = request.full_url
                return FakeResponse({"hand-003": {"status": {"completed": True}}})

            result = fetch_latest_hand_reference_history(
                settings,
                metadata_dir,
                opener=opener,
            )

        self.assertEqual(result.prompt_id, "hand-003")
        self.assertEqual(captured["url"], "http://localhost:8188/history/hand-003")
        self.assertIn("hand-003", result.history)

    def test_inspect_hand_reference_history_detects_completed_images(self) -> None:
        history = ComfyUIHistoryResult(
            prompt_id="hand-004",
            history={
                "hand-004": {
                    "status": {"completed": True},
                    "outputs": {
                        "9": {
                            "images": [
                                {
                                    "filename": "ComfyUI_hand_00001_.png",
                                    "subfolder": "",
                                    "type": "output",
                                },
                                {
                                    "filename": "notes.txt",
                                    "subfolder": "",
                                    "type": "output",
                                },
                            ]
                        }
                    },
                }
            },
        )

        inspection = inspect_hand_reference_history(history)

        self.assertTrue(inspection.completed)
        self.assertEqual(inspection.prompt_id, "hand-004")
        self.assertEqual(len(inspection.images), 1)
        self.assertEqual(inspection.images[0].file_name, "ComfyUI_hand_00001_.png")
        self.assertEqual(inspection.images[0].image_type, "output")

    def test_inspect_hand_reference_history_reports_pending_without_completed_status(self) -> None:
        history = ComfyUIHistoryResult(
            prompt_id="hand-005",
            history={
                "hand-005": {
                    "status": {"completed": False},
                    "outputs": {},
                }
            },
        )

        inspection = inspect_hand_reference_history(history)

        self.assertFalse(inspection.completed)
        self.assertEqual(inspection.images, ())

    def test_inspect_hand_reference_history_reports_not_completed_without_history_entry(self) -> None:
        history = ComfyUIHistoryResult(prompt_id="missing-hand", history={})

        inspection = inspect_hand_reference_history(history)

        self.assertFalse(inspection.completed)
        self.assertEqual(inspection.images, ())

    def test_copy_finished_hand_reference_images_copies_history_images_to_hand_refs(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            comfyui_output_dir = temp_path / "comfyui_output"
            hand_refs_dir = temp_path / "project_output" / "hand_refs"
            comfyui_output_dir.mkdir()
            source_path = comfyui_output_dir / "ComfyUI_hand_00001_.png"
            source_path.write_bytes(b"generated hand reference bytes")
            inspection = HandReferenceHistoryInspection(
                prompt_id="hand-006",
                completed=True,
                images=(
                    HandReferenceHistoryImage(
                        file_name="ComfyUI_hand_00001_.png",
                        subfolder="",
                        image_type="output",
                    ),
                ),
            )

            copied = copy_finished_hand_reference_images(
                inspection,
                comfyui_output_dir=comfyui_output_dir,
                hand_refs_dir=hand_refs_dir,
            )

            self.assertEqual(len(copied), 1)
            self.assertEqual(copied[0].source_path, source_path)
            self.assertEqual(copied[0].saved_path, hand_refs_dir / "ComfyUI_hand_00001_.png")
            self.assertEqual(copied[0].saved_path.read_bytes(), b"generated hand reference bytes")

    def test_copy_finished_hand_reference_images_uses_comfyui_subfolder(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            comfyui_output_dir = temp_path / "comfyui_output"
            nested_dir = comfyui_output_dir / "roughref_hand"
            hand_refs_dir = temp_path / "project_output" / "hand_refs"
            nested_dir.mkdir(parents=True)
            (nested_dir / "ComfyUI_hand_00002_.webp").write_bytes(b"nested hand reference bytes")
            inspection = HandReferenceHistoryInspection(
                prompt_id="hand-007",
                completed=True,
                images=(
                    HandReferenceHistoryImage(
                        file_name="ComfyUI_hand_00002_.webp",
                        subfolder="roughref_hand",
                        image_type="output",
                    ),
                ),
            )

            copied = copy_finished_hand_reference_images(
                inspection,
                comfyui_output_dir=comfyui_output_dir,
                hand_refs_dir=hand_refs_dir,
            )

            self.assertEqual(copied[0].source_path, nested_dir / "ComfyUI_hand_00002_.webp")
            self.assertEqual(copied[0].saved_path.read_bytes(), b"nested hand reference bytes")

    def test_copy_finished_hand_reference_images_skips_pending_history(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            temp_path = Path(temp_dir)
            comfyui_output_dir = temp_path / "comfyui_output"
            hand_refs_dir = temp_path / "project_output" / "hand_refs"
            comfyui_output_dir.mkdir()
            inspection = HandReferenceHistoryInspection(
                prompt_id="hand-008",
                completed=False,
                images=(
                    HandReferenceHistoryImage(
                        file_name="ComfyUI_hand_00003_.png",
                        subfolder="",
                        image_type="output",
                    ),
                ),
            )

            copied = copy_finished_hand_reference_images(
                inspection,
                comfyui_output_dir=comfyui_output_dir,
                hand_refs_dir=hand_refs_dir,
            )

            self.assertEqual(copied, ())
            self.assertFalse(hand_refs_dir.exists())

    def test_copy_finished_hand_reference_images_rejects_unsafe_history_paths(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            comfyui_output_dir = Path(temp_dir) / "comfyui_output"
            hand_refs_dir = Path(temp_dir) / "project_output" / "hand_refs"
            comfyui_output_dir.mkdir()
            inspection = HandReferenceHistoryInspection(
                prompt_id="hand-009",
                completed=True,
                images=(
                    HandReferenceHistoryImage(
                        file_name="ComfyUI_hand_00004_.png",
                        subfolder="..",
                        image_type="output",
                    ),
                ),
            )

            with self.assertRaises(ValueError):
                copy_finished_hand_reference_images(
                    inspection,
                    comfyui_output_dir=comfyui_output_dir,
                    hand_refs_dir=hand_refs_dir,
                )

    def test_download_finished_hand_reference_images_fetches_view_images(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            hand_refs_dir = Path(temp_dir) / "project_output" / "hand_refs"
            captured: dict[str, object] = {}
            inspection = HandReferenceHistoryInspection(
                prompt_id="hand-010",
                completed=True,
                images=(
                    HandReferenceHistoryImage(
                        file_name="ComfyUI_hand_00005_.png",
                        subfolder="roughref hand",
                        image_type="output",
                    ),
                ),
            )

            def opener(request: object, timeout: float) -> FakeBytesResponse:
                captured["url"] = request.full_url
                captured["timeout"] = timeout
                captured["method"] = request.get_method()
                return FakeBytesResponse(b"downloaded hand reference bytes")

            downloaded = download_finished_hand_reference_images(
                inspection,
                endpoint="http://127.0.0.1:8188/",
                hand_refs_dir=hand_refs_dir,
                timeout_seconds=9,
                opener=opener,
            )

            self.assertEqual(len(downloaded), 1)
            self.assertEqual(downloaded[0].saved_path, hand_refs_dir / "ComfyUI_hand_00005_.png")
            self.assertEqual(downloaded[0].saved_path.read_bytes(), b"downloaded hand reference bytes")
        self.assertEqual(
            captured["url"],
            "http://127.0.0.1:8188/view?filename=ComfyUI_hand_00005_.png&subfolder=roughref+hand&type=output",
        )
        self.assertEqual(captured["timeout"], 9)
        self.assertEqual(captured["method"], "GET")

    def test_download_finished_hand_reference_images_skips_pending_history(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            hand_refs_dir = Path(temp_dir) / "project_output" / "hand_refs"
            inspection = HandReferenceHistoryInspection(
                prompt_id="hand-011",
                completed=False,
                images=(
                    HandReferenceHistoryImage(
                        file_name="ComfyUI_hand_00006_.png",
                        subfolder="",
                        image_type="output",
                    ),
                ),
            )

            downloaded = download_finished_hand_reference_images(
                inspection,
                endpoint="http://127.0.0.1:8188",
                hand_refs_dir=hand_refs_dir,
                opener=lambda request, timeout: FakeBytesResponse(b"unused"),
            )

        self.assertEqual(downloaded, ())
        self.assertFalse(hand_refs_dir.exists())

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

    def test_read_hand_reference_outputs_safely_reports_empty_folder(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            output_dir = Path(temp_dir) / "hand_refs"
            output_dir.mkdir()

            result = read_hand_reference_outputs_safely(output_dir)

        self.assertFalse(result.ok)
        self.assertEqual(result.images, ())
        self.assertIn("No hand reference images were found", result.messages[0])

    def test_read_hand_reference_outputs_safely_reports_missing_folder(self) -> None:
        result = read_hand_reference_outputs_safely("missing_hand_refs")

        self.assertFalse(result.ok)
        self.assertEqual(result.images, ())
        self.assertIn("Hand reference output folder does not exist", result.messages[0])

    def test_read_hand_reference_outputs_safely_reports_non_folder_path(self) -> None:
        TEST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR) as temp_dir:
            output_path = Path(temp_dir) / "hand_refs.txt"
            output_path.write_text("not a folder\n", encoding="utf-8")

            result = read_hand_reference_outputs_safely(output_path)

        self.assertFalse(result.ok)
        self.assertIn("must be a folder", result.messages[0])


if __name__ == "__main__":
    unittest.main()
