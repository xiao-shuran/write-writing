import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
AUDIT = PACKAGE_ROOT / "scripts" / "prose_audit.py"


FLAT_TEXT = """在当今社会，沟通非常重要。我们应该提升效率，促进发展，实现更好的协作。

首先，沟通很重要。其次，效率很重要。最后，团队应该共同努力。

总的来说，只要积极努力，未来一定会更加美好。复杂的环境需要必要的调整，积极的团队才能实现更深刻、更温暖、更有效的改变。提升沟通、促进发展、推动协作，都是重要而必要的工作，也值得我们持续思考和积极实践。"""


class ProseAuditTests(unittest.TestCase):
    def run_audit(self, text):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "draft.md"
            path.write_text(text, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(AUDIT), str(path), "--json"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            return json.loads(result.stdout)

    def test_flags_common_flat_prose_signals(self):
        payload = self.run_audit(FLAT_TEXT)
        codes = {finding["code"] for finding in payload["findings"]}
        self.assertIn("generic-opening", codes)
        self.assertIn("generic-closing", codes)
        self.assertIn("abstract-density", codes)
        self.assertGreater(payload["finding_count"], 0)

    def test_short_specific_text_is_not_overdiagnosed(self):
        payload = self.run_audit("雨停了。门口的水还没有退。")
        self.assertEqual(payload["finding_count"], 0)
        self.assertIsNotNone(payload["note"])

    def test_cli_reports_unreadable_file_without_traceback(self):
        result = subprocess.run(
            [sys.executable, str(AUDIT), "missing-draft.md", "--json"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(PACKAGE_ROOT),
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("无法读取输入文件", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
