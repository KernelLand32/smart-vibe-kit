import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


INSTALLER_PATH = Path(__file__).resolve().parents[1] / "install.py"
SPEC = importlib.util.spec_from_file_location("svk_installer", INSTALLER_PATH)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def test_installer_references_sibling_skill_bundle(self):
        self.assertEqual(installer.SKILL_BUNDLE, INSTALLER_PATH.parents[1] / "skill")
        self.assertTrue((installer.SKILL_BUNDLE / "VERSION").is_file())
        installer.validate_bundle()

    def test_install_update_and_uninstall_owned_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            targets = [{"destination": destination, "hosts": ["test"]}]
            first = installer.run_transaction(targets)
            self.assertEqual(first[0]["action"], "installed")
            for name in installer.entries():
                marker = destination / name / installer.OWNER_FILE
                self.assertEqual(json.loads(marker.read_text(encoding="utf-8"))["owner"], "smart-vibe-kit")
            sentinel = destination / "svk-check" / "sentinel.txt"
            sentinel.write_text("old", encoding="utf-8")
            installer.run_transaction(targets)
            self.assertFalse(sentinel.exists())
            removed = installer.run_transaction(targets, uninstall=True)
            self.assertEqual(removed[0]["action"], "uninstalled")
            self.assertTrue(all(not (destination / name).exists() for name in installer.entries()))

    def test_unowned_collision_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            collision = destination / "svk-next"
            collision.mkdir(parents=True)
            (collision / "personal.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(PermissionError):
                installer.run_transaction([{"destination": destination, "hosts": ["test"]}])
            self.assertEqual((collision / "personal.txt").read_text(encoding="utf-8"), "keep")

    def test_targeted_installs_add_only_the_host_policy_key(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            qwen = base / "qwen"
            kimi = base / "kimi"
            installer.run_transaction([{"destination": qwen, "hosts": ["qwen"]}])
            installer.run_transaction([{"destination": kimi, "hosts": ["kimi"]}])
            qwen_text = (qwen / "svk-interview/SKILL.md").read_text(encoding="utf-8")
            kimi_text = (kimi / "svk-interview/SKILL.md").read_text(encoding="utf-8")
            self.assertIn("disable-model-invocation: true", qwen_text)
            self.assertNotIn("disableModelInvocation: true", qwen_text)
            self.assertIn("disableModelInvocation: true", kimi_text)
            self.assertNotIn("disable-model-invocation: true", kimi_text)

    def test_installed_wrapper_finds_shared_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            installer.run_transaction([{"destination": destination, "hosts": ["agents"]}])
            output = subprocess.check_output(
                [sys.executable, str(destination / "svk-interview/scripts/entry.py"), "--questions"],
                text=True,
            )
            self.assertGreater(len(json.loads(output)["questions"]), 4)

    def test_dry_run_makes_no_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            result = installer.run_transaction(
                [{"destination": destination, "hosts": ["test"]}], dry_run=True
            )
            self.assertEqual(result[0]["action"], "would-install")
            self.assertFalse(destination.exists())

    def test_project_destinations_deduplicate_shared_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            destinations = installer.resolve_destinations(
                "agents,codex", scope="project", project_root=temporary
            )
            self.assertEqual(len(destinations), 1)
            self.assertEqual(set(destinations[0]["hosts"]), {"agents", "codex"})
            self.assertEqual(destinations[0]["destination"], (Path(temporary) / ".agents/skills").resolve())

    def test_native_cline_and_windsurf_project_paths_do_not_collapse_into_agents(self):
        with tempfile.TemporaryDirectory() as temporary:
            destinations = installer.resolve_destinations(
                "agents,cline,windsurf", scope="project", project_root=temporary
            )
            by_path = {item["destination"].relative_to(Path(temporary)).as_posix(): item["hosts"] for item in destinations}
            self.assertEqual(set(by_path), {".agents/skills", ".cline/skills", ".windsurf/skills"})

    def test_copilot_does_not_receive_an_unsupported_frontmatter_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            installer.run_transaction([{"destination": destination, "hosts": ["copilot"]}])
            text = (destination / "svk-interview/SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("disable-model-invocation:", text)
            self.assertNotIn("disableModelInvocation:", text)

    def test_filesystem_root_is_rejected(self):
        anchor = Path(Path.cwd().anchor)
        with self.assertRaises(ValueError):
            installer.safe_destination(anchor)


if __name__ == "__main__":
    unittest.main()
