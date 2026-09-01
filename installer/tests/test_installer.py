import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


INSTALLER_PATH = Path(__file__).resolve().parents[1] / "install.py"
SPEC = importlib.util.spec_from_file_location("svk_installer", INSTALLER_PATH)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def test_installer_references_sibling_skill_bundle(self):
        self.assertEqual(installer.SKILL_BUNDLE, INSTALLER_PATH.parents[1] / "skill")
        self.assertTrue((installer.SKILL_BUNDLE / "VERSION").is_file())
        installer.validate_bundle()

    def test_install_clean_update_and_uninstall_owned_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            targets = [{"destination": destination, "hosts": ["test"]}]
            first = installer.run_transaction(targets)
            self.assertEqual(first[0]["action"], "installed")
            installation_ids = set()
            for name in installer.entries():
                marker = destination / name / installer.OWNER_FILE
                value = json.loads(marker.read_text(encoding="utf-8"))
                self.assertEqual(value["owner"], "smart-vibe-kit")
                self.assertEqual(value["version"], "2.1.0")
                self.assertEqual(value["name"], name)
                self.assertEqual(value["kind"], "shared-runtime" if name == installer.SHARED_ENTRY else "skill")
                self.assertEqual(value["destination_fingerprint"], installer.destination_fingerprint(destination))
                self.assertEqual(value["supported_upgrade_from"], ["2.0.0", "2.1.0"])
                self.assertEqual(len(value["bundle_digest"]), 64)
                installation_ids.add(value["installation_id"])
            self.assertEqual(installation_ids, {first[0]["installation_id"]})
            installer.run_transaction(targets)
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

    def test_incomplete_or_forged_ownership_markers_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            targets = [{"destination": destination, "hosts": ["agents"]}]
            installer.run_transaction(targets)
            marker = destination / "svk-next" / installer.OWNER_FILE
            original = json.loads(marker.read_text(encoding="utf-8"))
            mutations = (
                {"owner": "smart-vibe-kit"},
                dict(original, kind="shared-runtime"),
                dict(original, name="svk-check"),
                dict(original, version="9.9.9"),
                dict(original, installation_id="not-an-installation-id"),
                dict(original, destination_fingerprint="0" * 64),
                dict(original, supported_upgrade_from=[]),
            )
            for mutation in mutations:
                with self.subTest(fields=sorted(mutation)):
                    marker.write_text(json.dumps(mutation), encoding="utf-8")
                    with self.assertRaises(PermissionError):
                        installer.run_transaction(targets)
                    marker.write_text(json.dumps(original), encoding="utf-8")

    def test_failure_mid_replacement_restores_original_and_unrelated_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            targets = [{"destination": destination, "hosts": ["agents"]}]
            installer.run_transaction(targets)
            unrelated = destination / "personal-skill.txt"
            unrelated.write_text("keep\n", encoding="utf-8")
            before = {
                name: installer.entry_digest(destination / name)
                for name in installer.entries()
            }
            real_move = installer.shutil.move
            calls = {"count": 0}

            def fail_on_fourth_move(source, target):
                calls["count"] += 1
                if calls["count"] == 4:
                    raise OSError("injected replacement failure")
                return real_move(source, target)

            with mock.patch.object(installer.shutil, "move", side_effect=fail_on_fourth_move):
                with self.assertRaises(OSError):
                    installer.run_transaction(targets)
            self.assertEqual(
                before,
                {name: installer.entry_digest(destination / name) for name in installer.entries()},
            )
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep\n")
            self.assertEqual(list(destination.parent.glob(".svk-install-backup-*")), [])
            self.assertEqual(list(destination.parent.glob(".svk-install-stage-*")), [])

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
                [sys.executable, str(destination / "svk-interview/scripts/entry.py"), "questions"],
                text=True,
            )
            self.assertGreater(len(json.loads(output)["value"]["questions"]), 4)

    def test_local_drift_is_refused_unless_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            targets = [{"destination": destination, "hosts": ["agents"]}]
            installer.run_transaction(targets)
            sentinel = destination / "svk-check" / "sentinel.txt"
            sentinel.write_text("local change", encoding="utf-8")
            with self.assertRaises(PermissionError):
                installer.run_transaction(targets)
            result = installer.run_transaction(targets, preserve_local_changes=True)
            self.assertTrue(Path(result[0]["backup"]).is_dir())
            self.assertTrue((Path(result[0]["backup"]) / "svk-check/sentinel.txt").is_file())

    def test_legacy_20_upgrade_requires_explicit_human_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            target = destination / "svk-next"
            target.mkdir(parents=True)
            (target / installer.OWNER_FILE).write_text(
                json.dumps({"owner": "smart-vibe-kit", "kind": "skill", "version": "2.0.0"}),
                encoding="utf-8",
            )
            targets = [{"destination": destination, "hosts": ["agents"]}]
            with self.assertRaises(PermissionError):
                installer.run_transaction(targets)
            result = installer.run_transaction(targets, approve_upgrade=True)
            self.assertTrue(result[0]["retain_backup"])
            self.assertTrue((Path(result[0]["backup"]) / "svk-next" / installer.OWNER_FILE).is_file())

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
            canonical = Path(temporary).resolve()
            destinations = installer.resolve_destinations(
                "agents,cline,windsurf", scope="project", project_root=temporary
            )
            by_path = {item["destination"].relative_to(canonical).as_posix(): item["hosts"] for item in destinations}
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

    def test_lexical_path_alias_resolves_to_the_same_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            expected = (base / "skills").resolve()
            alias = base / "nested" / ".." / "skills"
            self.assertEqual(installer.safe_destination(alias), expected)
            self.assertEqual(installer.destination_fingerprint(alias), installer.destination_fingerprint(expected))


if __name__ == "__main__":
    unittest.main()
