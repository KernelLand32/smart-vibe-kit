import hashlib
import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from svk_core.operations import next_begin, next_block, next_finish, refresh, scaffold  # noqa: E402
from svk_core.profile import build_profile  # noqa: E402
from svk_core.util import read_json, write_json  # noqa: E402
from svk_core.verify import check_project, package_check  # noqa: E402


def answers(**overrides):
    value = {
        "title": "Portable Notes",
        "idea": "Build an offline-first notes utility with a small, inspectable core.",
        "goals": ["Create and search local notes"],
        "non_goals": ["No hosted collaboration in the first release"],
        "constraints": ["Run on Windows, macOS, and Linux"],
        "risk": "low",
        "team_size": 1,
    }
    value.update(overrides)
    return value


def tree_hashes(root):
    result = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


class ProfileTests(unittest.TestCase):
    def test_lean_profile_stays_small(self):
        profile = build_profile(answers())
        self.assertEqual(profile["profile"], "lean")
        self.assertEqual(profile["modules"], ["core"])
        self.assertLessEqual(profile["expected_document_count"], 12)

    def test_regulated_profile_cannot_exclude_safety_modules(self):
        profile = build_profile(
            answers(
                regulated=True,
                sensitive_data=True,
                exclude_modules=["research", "security", "regulated"],
            )
        )
        self.assertEqual(profile["profile"], "regulated")
        self.assertTrue({"research", "security", "regulated"}.issubset(set(profile["modules"])))

    def test_integrations_and_team_size_cannot_exclude_required_modules(self):
        profile = build_profile(
            answers(
                integrations=["Example API"],
                team_size=3,
                exclude_modules=["engineering", "collaboration"],
            )
        )
        self.assertTrue({"engineering", "collaboration"}.issubset(set(profile["modules"])))

    def test_invalid_answer_types_are_rejected(self):
        for override in (
            {"ui": "false"},
            {"team_size": 0},
            {"research_tier": 4},
            {"goals": "Build it"},
            {"risk": "extreme"},
        ):
            with self.subTest(override=override), self.assertRaises(ValueError):
                build_profile(answers(**override))


class ScaffoldTests(unittest.TestCase):
    def test_lean_and_regulated_scaffolds_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            lean = temporary / "lean"
            regulated = temporary / "regulated"
            lean_result = scaffold(lean, answers())
            regulated_result = scaffold(
                regulated,
                answers(
                    regulated=True,
                    sensitive_data=True,
                    deployable=True,
                    ui=True,
                    team_size=3,
                    research_tier=2,
                ),
            )
            self.assertEqual(lean_result["check"]["result"], "PASS")
            self.assertEqual(regulated_result["check"]["result"], "PASS")
            lean_files = [path for path in lean.rglob("*") if path.is_file()]
            regulated_files = [path for path in regulated.rglob("*") if path.is_file()]
            self.assertGreater(len(regulated_files), len(lean_files))
            self.assertTrue((regulated / "docs/compliance/traceability.md").is_file())

    def test_goals_create_implementation_tasks_before_release_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(goals=["Create notes", "Search notes"]))
            state = read_json(root / ".svk/state.json")
            titles = {task["id"]: task["title"] for task in state["tasks"]}
            self.assertEqual(titles["3.1.1"], "Implement and verify: Create notes")
            self.assertEqual(titles["3.2.1"], "Implement and verify: Search notes")
            self.assertEqual(titles["4.1.1"], "Run the release-readiness verification gate")

    def test_charter_accepted_shortcut_promotes_one_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            result = scaffold(root, answers(), charter_accepted=True)
            self.assertEqual(result["check"]["result"], "PASS")
            active = [task for task in result["state"]["tasks"] if task["status"] == "in_progress"]
            self.assertEqual(len(active), 1)
            self.assertNotEqual(active[0]["id"], "1.1.2")

    def test_manifest_excludes_temporary_stage_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers())
            manifest = read_json(root / ".svk/baselines/manifest.json")
            self.assertNotIn(".svk-stage-owner.json", manifest["files"])

    def test_existing_foreign_project_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            root.mkdir()
            source = root / "app.py"
            source.write_text("print('keep')\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                scaffold(root, answers())
            self.assertEqual(source.read_text(encoding="utf-8"), "print('keep')\n")

    def test_collision_is_refused_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            root.mkdir()
            agents = root / "AGENTS.md"
            agents.write_text("user-owned\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                scaffold(root, answers())
            self.assertEqual(agents.read_text(encoding="utf-8"), "user-owned\n")
            self.assertFalse((root / ".svk").exists())

    def test_refresh_is_byte_for_byte_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers())
            before = tree_hashes(root)
            summary = refresh(root)
            after = tree_hashes(root)
            self.assertEqual(summary["check"]["result"], "PASS")
            self.assertEqual(before, after)

    def test_refresh_returns_diagnostics_for_invalid_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers())
            (root / ".svk/state.json").write_text("{broken", encoding="utf-8")
            summary = refresh(root)
            self.assertEqual(summary["result"], "ERROR")
            self.assertTrue(any(item["code"] == "SVK-STATE.INVALID_JSON" for item in summary["check"]["diagnostics"]))

    def test_adversarial_semantic_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(ui=True, research_tier=1))
            (root / "docs/research/brief.md").write_text("", encoding="utf-8")
            state = read_json(root / ".svk/state.json")
            state["next_action"]["task_id"] = "9.9.9"
            state["charter"]["accepted"] = True
            write_json(root / ".svk/state.json", state)
            (root / "docs/product/requirements.md").write_text("# TODO\n", encoding="utf-8")
            result = check_project(root)
            codes = {item["code"] for item in result["diagnostics"]}
            self.assertEqual(result["result"], "ERROR")
            self.assertIn("SVK-FILE-EMPTY", codes)
            self.assertIn("SVK-NEXT-ACTION", codes)
            self.assertIn("SVK-CHARTER-STATE", codes)
            self.assertIn("SVK-PLACEHOLDER", codes)


class NextTests(unittest.TestCase):
    def test_finish_promotes_exactly_one_task_and_removes_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            root = temporary / "project"
            scaffold(root, answers(ui=True))
            begun = next_begin(root, "test-owner", allow_human_gate=True)
            self.assertEqual(begun["task"]["id"], "1.1.2")
            evidence = temporary / "evidence.json"
            write_json(
                evidence,
                {
                    "summary": "Reviewed and accepted the project charter.",
                    "commands": ["manual charter review"],
                    "artifacts": ["docs/adr/0001-project-charter.md"],
                    "result": "pass",
                },
            )
            result = next_finish(root, "test-owner", "1.1.2", evidence)
            self.assertEqual(result["check"]["result"], "PASS")
            self.assertFalse((root / ".svk/locks/next.json").exists())
            state = read_json(root / ".svk/state.json")
            active = [task for task in state["tasks"] if task["status"] == "in_progress"]
            self.assertEqual(len(active), 1)
            self.assertEqual(active[0]["id"], state["next_action"]["task_id"])
            agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("%s — %s" % (active[0]["id"], active[0]["title"]), agents_text)

    def test_block_records_consistent_state_and_releases_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers())
            begun = next_begin(root, "test-owner", allow_human_gate=True)
            result = next_block(root, "test-owner", begun["task"]["id"], "Waiting for scope approval")
            self.assertEqual(result["result"], "BLOCKED")
            self.assertFalse((root / ".svk/locks/next.json").exists())
            state = read_json(root / ".svk/state.json")
            active = [task for task in state["tasks"] if task["status"] == "blocked"]
            self.assertEqual(len(active), 1)
            self.assertEqual(active[0]["blocker"], "Waiting for scope approval")

    def test_invalid_lock_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers())
            for owner, ttl in (("", 120), ("owner", 0), ("owner", 10081)):
                with self.subTest(owner=owner, ttl=ttl), self.assertRaises(ValueError):
                    next_begin(root, owner, allow_human_gate=True, ttl_minutes=ttl)


class PackageTests(unittest.TestCase):
    def test_package_contract_and_cross_harness_matrix(self):
        bundle = Path(__file__).resolve().parents[1]
        result = package_check(bundle)
        self.assertEqual(result["result"], "PASS", result)
        compatibility = read_json(bundle / "compatibility.json")
        expected = {"codex", "cursor", "claude", "gemini", "antigravity", "grok", "qwen", "kimi"}
        self.assertTrue(expected.issubset(set(compatibility["hosts"])))
        allowed = {"contract-verified", "contract-compatible-untested", "partial-untested", "shared-standard"}
        for host in compatibility["hosts"].values():
            self.assertIn(host["status"], allowed)
            self.assertTrue(host["user_root"])
            self.assertTrue(host["project_root"])
            self.assertTrue(host["invocation"])

    def test_python_sources_parse_as_python_38(self):
        release_root = Path(__file__).resolve().parents[2]
        for path in release_root.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            try:
                ast.parse(source, filename=str(path), feature_version=(3, 8))
            except SyntaxError as error:
                self.fail("%s is not Python 3.8 syntax: %s" % (path, error))


if __name__ == "__main__":
    unittest.main()
