from pathlib import Path
import json
import tempfile
import unittest

from color_rough_ref_tool.core.settings import AppSettings
from color_rough_ref_tool.integrations.comfyui.hand_inpainting import (
    load_hand_inpainting_workflow,
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


if __name__ == "__main__":
    unittest.main()
