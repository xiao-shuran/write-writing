import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DOCTOR_RELATIVE = Path("scripts") / "skill_doctor.py"


class SkillDoctorTests(unittest.TestCase):
    def make_unsynced_package(self, temporary_root: Path) -> Path:
        destination = temporary_root / "writing-craft"
        manifest = json.loads((PACKAGE_ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

        for relative in manifest["core_files"]:
            source = PACKAGE_ROOT / relative
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        shutil.copy2(PACKAGE_ROOT / ".writing-craft-root", destination / ".writing-craft-root")
        return destination

    def run_doctor(self, package_root: Path, action: str):
        result = subprocess.run(
            [
                sys.executable,
                str(package_root / DOCTOR_RELATIVE),
                action,
                "--root",
                str(package_root),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertTrue(result.stdout, msg=result.stderr)
        return result, json.loads(result.stdout)

    def sync_package(self, package_root: Path) -> None:
        result, payload = self.run_doctor(package_root, "--sync")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue(payload["healthy"], msg=payload)

    def test_sync_creates_canonical_mirrors_and_platform_entries(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            package_root = self.make_unsynced_package(Path(temporary_directory))
            self.sync_package(package_root)

            manifest = json.loads((package_root / "MANIFEST.json").read_text(encoding="utf-8"))
            canonical = package_root / manifest["canonical_path"]
            claude_mirror = package_root / ".claude" / "skills" / "writing-craft"

            for relative in manifest["core_files"]:
                with self.subTest(relative=relative):
                    self.assertTrue((canonical / relative).is_file())
                    self.assertTrue((claude_mirror / relative).is_file())
                    self.assertEqual(
                        (canonical / relative).read_bytes(),
                        (package_root / relative).read_bytes(),
                    )

            for relative in manifest["platform_entries"]:
                with self.subTest(entry=relative):
                    self.assertTrue((package_root / relative).is_file())

            result, payload = self.run_doctor(package_root, "--check")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(payload["healthy"], msg=payload)

    def test_repair_restores_missing_file_but_preserves_drift(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            package_root = self.make_unsynced_package(Path(temporary_directory))
            self.sync_package(package_root)

            canonical = package_root / ".agents" / "skills" / "writing-craft"
            missing = package_root / "references" / "chinese-style.md"
            drifted = package_root / "SKILL.md"
            expected_missing_content = (canonical / "references" / "chinese-style.md").read_bytes()
            drifted.write_text("# local override\n", encoding="utf-8")
            missing.unlink()

            result, payload = self.run_doctor(package_root, "--repair")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(payload["healthy"])
            self.assertEqual(missing.read_bytes(), expected_missing_content)
            self.assertEqual(drifted.read_text(encoding="utf-8"), "# local override\n")

            result, payload = self.run_doctor(package_root, "--sync")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(payload["healthy"], msg=payload)
            self.assertEqual(drifted.read_bytes(), (canonical / "SKILL.md").read_bytes())

    def test_repair_recovers_missing_canonical_file_from_root_mirror(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            package_root = self.make_unsynced_package(Path(temporary_directory))
            self.sync_package(package_root)

            canonical_file = (
                package_root
                / ".agents"
                / "skills"
                / "writing-craft"
                / "references"
                / "material-ledger.md"
            )
            root_file = package_root / "references" / "material-ledger.md"
            expected = root_file.read_bytes()
            canonical_file.unlink()

            result, payload = self.run_doctor(package_root, "--repair")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(payload["healthy"], msg=payload)
            self.assertEqual(canonical_file.read_bytes(), expected)

    def test_repair_recovers_root_when_marker_manifest_and_entry_are_missing(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            package_root = self.make_unsynced_package(Path(temporary_directory))
            self.sync_package(package_root)

            canonical_root = package_root / ".agents" / "skills" / "writing-craft"
            expected_skill = (canonical_root / "SKILL.md").read_bytes()
            (package_root / ".writing-craft-root").unlink()
            (package_root / "MANIFEST.json").unlink()
            (package_root / "SKILL.md").unlink()

            result = subprocess.run(
                [sys.executable, str(canonical_root / DOCTOR_RELATIVE), "--repair"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["healthy"], msg=payload)
            self.assertTrue((package_root / ".writing-craft-root").is_file())
            self.assertTrue((package_root / "MANIFEST.json").is_file())
            self.assertEqual((package_root / "SKILL.md").read_bytes(), expected_skill)

    def test_standalone_skill_copy_is_healthy_without_distribution_layout(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            package_root = self.make_unsynced_package(Path(temporary_directory))
            (package_root / ".writing-craft-root").unlink()
            result, payload = self.run_doctor(package_root, "--check")

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(payload["healthy"], msg=payload)
            self.assertFalse(payload["full_distribution"])
            self.assertEqual(Path(payload["canonical"]), package_root)
            self.assertFalse((package_root / ".agents").exists())

    def test_standalone_agents_folder_does_not_rebuild_project_entries(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "project"
            standalone_root = project_root / ".agents" / "skills" / "writing-craft"
            manifest = json.loads((PACKAGE_ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

            for relative in manifest["core_files"]:
                source = PACKAGE_ROOT / relative
                destination = standalone_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

            result = subprocess.run(
                [sys.executable, str(standalone_root / DOCTOR_RELATIVE), "--check"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["healthy"], msg=payload)
            self.assertFalse(payload["full_distribution"])
            self.assertEqual(Path(payload["root"]), standalone_root)
            self.assertFalse((project_root / "AGENTS.md").exists())

    def test_explicit_rebuild_recovers_distribution_when_layout_signals_are_gone(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            package_root = self.make_unsynced_package(Path(temporary_directory))
            (package_root / ".writing-craft-root").unlink()

            result, payload = self.run_doctor(
                package_root, "--repair"
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(payload["healthy"], msg=payload)
            self.assertFalse(payload["full_distribution"])

            result = subprocess.run(
                [
                    sys.executable,
                    str(package_root / DOCTOR_RELATIVE),
                    "--repair",
                    "--root",
                    str(package_root),
                    "--rebuild-distribution",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["healthy"], msg=payload)
            self.assertTrue(payload["full_distribution"])
            self.assertTrue(payload["rebuild_distribution"])
            self.assertTrue((package_root / ".agents" / "skills" / "writing-craft").is_dir())
            self.assertTrue((package_root / "AGENTS.md").is_file())


if __name__ == "__main__":
    unittest.main()
