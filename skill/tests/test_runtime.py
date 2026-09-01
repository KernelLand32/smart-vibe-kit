import ast
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import shutil
import io
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from svk_core.cli import EXIT_CONTRACT, run  # noqa: E402
from svk_core import evidence as evidence_module  # noqa: E402
from svk_core import migration as migration_module  # noqa: E402
from svk_core import operations as operations_module  # noqa: E402
from svk_core.interview import session_abandon, session_checkpoint, session_show, session_start  # noqa: E402
from svk_core.operations import (  # noqa: E402
    next_begin, next_block, next_finish, refresh, scaffold, verify_task,
)
from svk_core.evidence import OUTPUT_LIMIT  # noqa: E402
from svk_core.profile import build_profile  # noqa: E402
from svk_core.util import read_json, snapshot_fingerprint, write_json  # noqa: E402
from svk_core.verify import check_project, package_check  # noqa: E402
from svk_core.migration import apply_migration, inspect_migration, plan_migration, rollback_migration  # noqa: E402
from svk_core.planning import apply_plan_edit  # noqa: E402
from svk_core.recovery import (  # noqa: E402
    clear_expired_lease, index_orphan_receipts, inspect_recovery,
    rollback_incomplete_transactions,
)


def answers(**overrides):
    goal = "Create and search local notes"
    value = {
        "title": "Portable Notes",
        "idea": "Build an offline-first notes utility with a small, inspectable core.",
        "goals": [goal],
        "non_goals": ["No hosted collaboration in the first release"],
        "constraints": ["Run on Windows, macOS, and Linux"],
        "risk": "low",
        "team_size": 1,
        "verifiers": {},
        "plan_approved": True,
        "plan_reviewer": "project owner",
        "plan_review_reason": "The task boundaries and acceptance checks are understood.",
        "plan": {
            "goals": [{"id": "goal-1", "title": goal}],
            "deliverables": [{
                "id": "notes-core",
                "goal_id": "goal-1",
                "title": "Local notes core",
                "acceptance": ["A user can create and search notes locally."],
            }],
            "tasks": [{
                "id": "3.1.1",
                "kind": "implementation",
                "title": "Implement and verify the local notes core",
                "goal_id": "goal-1",
                "deliverable_id": "notes-core",
                "depends_on": [],
                "dependency_rationale": {},
                "human_gate": False,
                "acceptance": ["The local notes behavior is implemented and verified."],
                "expected_artifacts": ["app.py"],
                "scope_hints": ["app.py"],
                "required_verifiers": ["svk-governed"],
                "risk": "low",
                "size_signals": {"subsystems": 1, "acceptance_items": 1, "verifier_count": 1, "scope_hints": 1},
            }],
            "release_verifiers": ["svk-governed"],
        },
    }
    value.update(overrides)
    return value


def tree_hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(Path(root).rglob("*")) if path.is_file()
    }


def command_answers(argv, artifacts=None, scope_hints=None):
    value = answers()
    value["verifiers"] = {
        "command-check": {
            "kind": "command",
            "argv": argv,
            "cwd": ".",
            "timeout_seconds": 5,
            "expected_exit_codes": [0],
            "artifacts": list(artifacts or []),
            "environment": {"inherit": "safe-defaults", "set": {}},
        }
    }
    task = value["plan"]["tasks"][0]
    task["expected_artifacts"] = []
    task["no_artifact_reason"] = "The command verifier owns any generated test artifact."
    task["scope_hints"] = list(scope_hints or ["input.txt"])
    task["required_verifiers"] = ["command-check"]
    task["size_signals"]["scope_hints"] = len(task["scope_hints"])
    return value


def downgrade_to_20(root):
    profile = read_json(root / ".svk/project.json")
    profile["schema_version"] = 1
    profile["svk_version"] = "2.0.0"
    profile["expected_document_count"] = 12
    write_json(root / ".svk/project.json", profile)
    current = read_json(root / ".svk/state.json")
    tasks = []
    for task in current["tasks"]:
        tasks.append({
            "id": task["id"], "title": task["title"], "status": task["status"],
            "depends_on": task["depends_on"], "human_gate": task["human_gate"],
            "artifact": (task.get("expected_artifacts") or ["Narrative implementation output"])[0],
            "verification": task["acceptance"][0],
        })
    legacy = {
        "schema_version": "2.0", "kit_version": "2.0.0", "project": current["project"],
        "stage": current["stage"], "charter": current["charter"], "tasks": tasks,
        "next_action": current["next_action"], "authorizations": [], "updated_at": current["updated_at"],
    }
    write_json(root / ".svk/state.json", legacy)
    for relative in ("plan.json", "verifiers.json", "governance.json"):
        (root / ".svk" / relative).unlink()
    shutil.rmtree(root / ".svk/evidence")
    shutil.rmtree(root / ".svk/interview")
    write_json(root / ".svk/install.json", {"owner": "smart-vibe-kit", "version": "2.0.0", "created_at": current["updated_at"]})
    write_json(root / ".svk/baselines/manifest.json", {"version": "2.0.0", "files": {}})
    (root / ".svk/evidence.jsonl").write_text('{"result":"pass"}\n', encoding="utf-8")


class ProfileAndPlanTests(unittest.TestCase):
    def test_lean_profile_stays_small(self):
        profile = build_profile(answers())
        self.assertEqual(profile["profile"], "lean")
        self.assertEqual(profile["modules"], ["core"])

    def test_regulated_profile_keeps_required_modules(self):
        profile = build_profile(answers(regulated=True, sensitive_data=True, exclude_modules=["research", "security", "regulated"]))
        self.assertTrue({"research", "security", "regulated"}.issubset(set(profile["modules"])))

    def test_unapproved_or_oversized_plan_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                scaffold(Path(temporary) / "unapproved", answers(plan_approved=False))
            oversized = answers()
            oversized["plan"]["tasks"][0]["size_signals"]["subsystems"] = 2
            with self.assertRaises(ValueError):
                scaffold(Path(temporary) / "oversized", oversized)

    def test_missing_goal_and_dependency_cycle_are_rejected_without_partial_scaffold(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            missing = answers()
            missing["plan"]["goals"] = []
            with self.assertRaises(ValueError):
                scaffold(base / "missing", missing)
            self.assertFalse((base / "missing").exists())

            cyclic = answers()
            original = cyclic["plan"]["tasks"][0]
            second = copy.deepcopy(original)
            second["id"] = "3.1.2"
            second["title"] = "Verify the local notes core"
            second["depends_on"] = ["3.1.1"]
            second["dependency_rationale"] = {"3.1.1": "Verification follows implementation."}
            original["depends_on"] = ["3.1.2"]
            original["dependency_rationale"] = {"3.1.2": "Intentional cycle fixture."}
            cyclic["plan"]["tasks"].append(second)
            with self.assertRaises(ValueError):
                scaffold(base / "cyclic", cyclic)
            self.assertFalse((base / "cyclic").exists())


class ScaffoldTests(unittest.TestCase):
    def test_scaffold_has_strict_21_contract_and_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            result = scaffold(root, answers())
            self.assertEqual(result["check"]["result"], "PASS", result["check"])
            self.assertEqual(read_json(root / ".svk/project.json")["svk_version"], "2.1.0")
            for relative in (
                ".svk/plan.json", ".svk/verifiers.json", ".svk/governance.json",
                ".svk/evidence/index.json", ".svk/interview/session.json",
            ):
                self.assertTrue((root / relative).is_file(), relative)

    def test_existing_foreign_project_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            root.mkdir()
            source = root / "app.py"
            source.write_text("print('keep')\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                scaffold(root, answers())
            self.assertEqual(source.read_text(encoding="utf-8"), "print('keep')\n")

    def test_refresh_is_byte_for_byte_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers())
            before = tree_hashes(root)
            result = refresh(root)
            self.assertEqual(result["result"], "PASS")
            self.assertEqual(before, tree_hashes(root))

    def test_default_check_ignores_unregistered_markdown_but_all_docs_checks_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers())
            (root / "notes.md").write_text("# TODO\n", encoding="utf-8")
            self.assertEqual(check_project(root)["result"], "PASS")
            self.assertEqual(check_project(root, scope="all-docs")["result"], "ERROR")

    def test_resumable_interview_checkpoint_survives_before_scaffold(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            session_start(root, "A local notes tool")
            session_checkpoint(root, "project", {"title": "Portable Notes"}, ["Who owns release approval?"])
            result = session_show(root)
            self.assertEqual(result["session"]["sections"]["project"]["title"], "Portable Notes")
            self.assertEqual(len(result["session"]["unresolved_questions"]), 1)

    def test_abandoned_interview_is_durable_and_cannot_be_scaffolded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            session_start(root, "A local notes tool")
            session_checkpoint(root, "project", {"title": "Portable Notes"})
            result = session_abandon(root, "The owner cancelled this project.")
            self.assertEqual(result["session"]["status"], "abandoned")
            self.assertEqual(session_show(root)["session"]["abandon_reason"], "The owner cancelled this project.")
            with self.assertRaises(ValueError):
                scaffold(root, answers())
            self.assertFalse(root.exists())

    def test_required_top_level_contract_fields_and_unknown_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers())
            for relative in (".svk/project.json", ".svk/state.json"):
                path = root / relative
                original = read_json(path)
                for field in sorted(original):
                    mutated = copy.deepcopy(original)
                    mutated.pop(field)
                    write_json(path, mutated)
                    result = check_project(root)
                    self.assertEqual(result["result"], "ERROR", "%s accepted missing %s" % (relative, field))
                mutated = copy.deepcopy(original)
                mutated["unexpected_test_field"] = True
                write_json(path, mutated)
                self.assertEqual(check_project(root)["result"], "ERROR", "%s accepted an unknown field" % relative)
                write_json(path, original)
            self.assertEqual(check_project(root)["result"], "PASS")

    def test_project_symlink_escape_is_rejected_when_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "project"
            root.mkdir()
            outside = base / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            try:
                os.symlink(str(outside), str(root / "linked.txt"))
            except (OSError, NotImplementedError) as error:
                self.skipTest("Symbolic links are unavailable: %s" % error)
            with self.assertRaises(ValueError):
                snapshot_fingerprint(root, ["linked.txt"])


class NextTests(unittest.TestCase):
    def test_human_gate_needs_named_attestation_then_receipts_gate_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers())
            with self.assertRaises(PermissionError):
                next_begin(root, "agent")
            begun = next_begin(root, "agent", True, 120, "Alice", "I reviewed and accept the charter.")
            self.assertEqual(begun["task"]["id"], "1.1.2")
            finished = next_finish(root, "agent", "1.1.2", [])
            self.assertEqual(finished["check"]["result"], "PASS")
            (root / "app.py").write_text("def search_notes():\n    return []\n", encoding="utf-8")
            begun = next_begin(root, "agent")
            receipt = verify_task(root, "agent", begun["task"]["id"], "svk-governed")
            self.assertEqual(receipt["result"], "pass", receipt)
            finished = next_finish(root, "agent", begun["task"]["id"], [receipt["run_id"]])
            self.assertEqual(finished["check"]["result"], "PASS")

    def test_empty_self_report_cannot_finish_machine_verified_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            next_begin(root, "agent")
            with self.assertRaises(ValueError):
                next_finish(root, "agent", "3.1.1", [])

    def test_tampered_failed_receipt_cannot_be_promoted_to_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            data = command_answers(["{python}", "-c", "import sys; sys.exit(9)"])
            scaffold(root, data, charter_accepted=True)
            (root / "input.txt").write_text("input\n", encoding="utf-8")
            begun = next_begin(root, "agent")
            receipt = verify_task(root, "agent", begun["task"]["id"], "command-check")
            self.assertEqual(receipt["result"], "fail")
            receipt_path = root / ".svk/evidence/runs" / receipt["run_id"] / "receipt.json"
            tampered = read_json(receipt_path)
            tampered["result"] = "pass"
            tampered["exit_code"] = 0
            write_json(receipt_path, tampered)
            with self.assertRaises((ValueError, RuntimeError)):
                next_finish(root, "agent", begun["task"]["id"], [receipt["run_id"]])
            self.assertEqual(check_project(root)["result"], "ERROR")

    def test_block_is_consistent_and_releases_lease(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            begun = next_begin(root, "agent")
            result = next_block(root, "agent", begun["task"]["id"], "Waiting for an external decision")
            self.assertEqual(result["result"], "BLOCKED")
            self.assertFalse((root / ".svk/locks/next.json").exists())

    def test_stale_lease_revision_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            begun = next_begin(root, "agent")
            state = read_json(root / ".svk/state.json")
            state["state_revision"] += 1
            write_json(root / ".svk/state.json", state)
            with self.assertRaises(PermissionError):
                verify_task(root, "agent", begun["task"]["id"], "svk-governed")

    def test_second_begin_cannot_replace_an_existing_lease(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            first = next_begin(root, "first-agent")
            with self.assertRaises(RuntimeError):
                next_begin(root, "second-agent")
            self.assertEqual(read_json(root / ".svk/locks/next.json")["owner"], "first-agent")
            self.assertEqual(read_json(root / ".svk/locks/next.json")["task_id"], first["task"]["id"])

    def test_two_processes_racing_begin_create_exactly_one_lease(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            runtime = RUNTIME / "svk.py"
            processes = [
                subprocess.Popen(
                    [sys.executable, "-B", str(runtime), "next", "--root", str(root), "begin", "--owner", owner],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                )
                for owner in ("agent-a", "agent-b")
            ]
            results = [process.communicate(timeout=20) + (process.returncode,) for process in processes]
            self.assertEqual(sorted(item[2] for item in results), [0, EXIT_CONTRACT], results)
            lease = read_json(root / ".svk/locks/next.json")
            self.assertIn(lease["owner"], ("agent-a", "agent-b"))

    def test_finish_write_failure_restores_state_lease_and_records_rollback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            (root / "app.py").write_text("def search_notes():\n    return []\n", encoding="utf-8")
            begun = next_begin(root, "agent")
            receipt = verify_task(root, "agent", begun["task"]["id"], "svk-governed")
            state_before = read_json(root / ".svk/state.json")
            lease_before = read_json(root / ".svk/locks/next.json")
            with mock.patch.object(operations_module, "_render_generated", side_effect=OSError("injected render failure")):
                with self.assertRaises(OSError):
                    next_finish(root, "agent", begun["task"]["id"], [receipt["run_id"]])
            self.assertEqual(read_json(root / ".svk/state.json"), state_before)
            self.assertEqual(read_json(root / ".svk/locks/next.json"), lease_before)
            transactions = [read_json(path) for path in (root / ".svk/transactions").glob("next-*.json")]
            self.assertEqual([item["status"] for item in transactions], ["rolled_back"])
            self.assertFalse(any((root / ".svk/transactions").glob("*.state-snapshot")))

    def test_command_verifier_records_failure_timeout_and_bounded_output(self):
        fixtures = (
            (["{python}", "-c", "import sys; print('failed'); sys.exit(7)"], "failed", False),
            (["{python}", "-c", "import time; time.sleep(5)"], "timeout", True),
            (["{python}", "-c", "print('x' * %d)" % (OUTPUT_LIMIT + 1024)], "large", False),
        )
        for argv, label, expected_timeout in fixtures:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "project"
                data = command_answers(argv)
                if label == "timeout":
                    data["verifiers"]["command-check"]["timeout_seconds"] = 1
                scaffold(root, data, charter_accepted=True)
                (root / "input.txt").write_text("input\n", encoding="utf-8")
                begun = next_begin(root, "agent")
                receipt = verify_task(root, "agent", begun["task"]["id"], "command-check")
                self.assertEqual(receipt["timed_out"], expected_timeout)
                if label == "large":
                    self.assertEqual(receipt["result"], "pass")
                    self.assertTrue(receipt["stdout"]["truncated"])
                    self.assertGreater(receipt["stdout"]["bytes"], OUTPUT_LIMIT)
                else:
                    self.assertEqual(receipt["result"], "fail")
                    with self.assertRaises(ValueError):
                        next_finish(root, "agent", begun["task"]["id"], [receipt["run_id"]])

    def test_receipt_becomes_stale_after_input_or_verifier_artifact_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            command = "from pathlib import Path; Path('build.txt').write_text('built', encoding='utf-8')"
            scaffold(root, command_answers(["{python}", "-c", command], artifacts=["build.txt"]), charter_accepted=True)
            (root / "input.txt").write_text("v1\n", encoding="utf-8")
            begun = next_begin(root, "agent")
            receipt = verify_task(root, "agent", begun["task"]["id"], "command-check")
            self.assertEqual(receipt["result"], "pass")
            (root / "build.txt").write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                next_finish(root, "agent", begun["task"]["id"], [receipt["run_id"]])
            (root / "build.txt").write_text("built", encoding="utf-8")
            (root / "input.txt").write_text("v2\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                next_finish(root, "agent", begun["task"]["id"], [receipt["run_id"]])

    def test_secret_like_verifier_environment_is_refused(self):
        data = command_answers(["{python}", "-c", "print('ok')"])
        data["verifiers"]["command-check"]["environment"]["set"] = {"API_KEY": "do-not-store"}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, data, charter_accepted=True)
            (root / "input.txt").write_text("input\n", encoding="utf-8")
            begun = next_begin(root, "agent")
            with self.assertRaises(ValueError):
                verify_task(root, "agent", begun["task"]["id"], "command-check")


class PlanningRecoveryAndMigrationTests(unittest.TestCase):
    def test_approved_insert_edit_is_revisioned_and_unapproved_edit_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers())
            edit = {
                "operation": "insert",
                "task": {
                    "id": "3.2.1", "kind": "verification", "title": "Add a focused persistence regression test",
                    "goal_id": "goal-1", "deliverable_id": "notes-core", "depends_on": ["3.1.1"],
                    "dependency_rationale": {"3.1.1": "The implementation must exist before its persistence regression test."},
                    "human_gate": False, "acceptance": ["The regression test verifies persistence across restart."],
                    "expected_artifacts": ["tests/test_persistence.py"], "scope_hints": ["tests/test_persistence.py"],
                    "required_verifiers": ["svk-governed"], "risk": "low",
                    "size_signals": {"subsystems": 1, "acceptance_items": 1, "verifier_count": 1, "scope_hints": 1},
                },
            }
            with self.assertRaises(PermissionError):
                apply_plan_edit(root, "owner", edit, "Alice", "Adds missing coverage", False)
            before = read_json(root / ".svk/state.json")["state_revision"]
            result = apply_plan_edit(root, "owner", edit, "Alice", "Adds missing coverage", True)
            self.assertEqual(result["state_revision"], before + 1)
            self.assertIn("3.2.1", {task["id"] for task in read_json(root / ".svk/plan.json")["tasks"]})

    def test_orphan_receipt_is_inspected_and_explicitly_reindexed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            (root / "app.py").write_text("def search_notes():\n    return []\n", encoding="utf-8")
            begun = next_begin(root, "agent")
            receipt = verify_task(root, "agent", begun["task"]["id"], "svk-governed")
            index = read_json(root / ".svk/evidence/index.json")
            index["records"] = [item for item in index["records"] if item.get("id") != receipt["run_id"]]
            write_json(root / ".svk/evidence/index.json", index)
            self.assertEqual(inspect_recovery(root)["orphan_receipts"], [receipt["run_id"]])
            with self.assertRaises(PermissionError):
                index_orphan_receipts(root)
            result = index_orphan_receipts(root, approve=True)
            self.assertEqual(result["receipt_ids"], [receipt["run_id"]])

    def test_evidence_index_write_failure_leaves_recoverable_orphan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            (root / "app.py").write_text("def search_notes():\n    return []\n", encoding="utf-8")
            begun = next_begin(root, "agent")
            real_write = evidence_module.write_json

            def fail_index(path, value):
                if Path(path).resolve() == (root / ".svk/evidence/index.json").resolve():
                    raise OSError("injected evidence-index failure")
                return real_write(path, value)

            with mock.patch.object(evidence_module, "write_json", side_effect=fail_index):
                with self.assertRaises(OSError):
                    verify_task(root, "agent", begun["task"]["id"], "svk-governed")
            inspected = inspect_recovery(root)
            self.assertEqual(len(inspected["orphan_receipts"]), 1)
            recovered = index_orphan_receipts(root, approve=True)
            self.assertEqual(recovered["receipt_ids"], inspected["orphan_receipts"])

    def test_incomplete_transaction_is_inspected_and_explicitly_rolled_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            state_path = root / ".svk/state.json"
            original_text = state_path.read_text(encoding="utf-8")
            original = json.loads(original_text)
            transaction_path = root / ".svk/transactions/next-ffffffffffffffffffffffffffffffff.json"
            write_json(transaction_path, {
                "schema_version": "2.1", "kit_version": "2.1.0",
                "id": "f" * 32, "operation": "finish", "status": "in_progress",
                "recorded_at": original["updated_at"], "before_revision": original["state_revision"],
                "after_revision": original["state_revision"] + 1, "task_id": "3.1.1",
                "details": {"receipt_ids": [], "lease": None},
            })
            transaction_path.with_suffix(".state-snapshot").write_text(original_text, encoding="utf-8")
            mutated = copy.deepcopy(original)
            mutated["state_revision"] += 10
            write_json(state_path, mutated)
            self.assertEqual(inspect_recovery(root)["result"], "BLOCKED")
            with self.assertRaises(PermissionError):
                rollback_incomplete_transactions(root)
            recovered = rollback_incomplete_transactions(root, approve=True)
            self.assertEqual(recovered["check"]["result"], "PASS")
            self.assertEqual(read_json(state_path), original)
            self.assertFalse(transaction_path.with_suffix(".state-snapshot").exists())

    def test_expired_lease_requires_explicit_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            next_begin(root, "agent")
            lease_path = root / ".svk/locks/next.json"
            lease = read_json(lease_path)
            lease["expires_at"] = "2000-01-01T00:00:00Z"
            write_json(lease_path, lease)
            with self.assertRaises(PermissionError):
                clear_expired_lease(root)
            result = clear_expired_lease(root, approve=True)
            self.assertEqual(result["status"], "cleared-expired")
            self.assertFalse(lease_path.exists())

    def test_migration_preserves_user_docs_and_can_rollback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            constitution = root / "docs/constitution.md"
            constitution.write_text(constitution.read_text(encoding="utf-8") + "\nUser migration note.\n", encoding="utf-8")
            downgrade_to_20(root)
            self.assertEqual(inspect_migration(root)["status"], "ready")
            self.assertEqual(plan_migration(root)["status"], "approval-required")
            with self.assertRaises(PermissionError):
                apply_migration(root)
            result = apply_migration(root, approve=True)
            self.assertIn(result["result"], ("PASS", "WARN"))
            self.assertEqual(apply_migration(root, approve=True)["status"], "no-op")
            self.assertIn("User migration note.", constitution.read_text(encoding="utf-8"))
            self.assertTrue((root / ".svk/migrations/2.0/manifest.json").is_file())
            rollback_migration(root, result["backup"], approve=True)
            self.assertEqual(read_json(root / ".svk/project.json")["svk_version"], "2.0.0")

    def test_migration_blocks_unknown_custom_state_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            downgrade_to_20(root)
            state = read_json(root / ".svk/state.json")
            state["custom_extension"] = {"must": "survive"}
            write_json(root / ".svk/state.json", state)
            before = tree_hashes(root)
            inspected = inspect_migration(root)
            self.assertEqual(inspected["status"], "blocked")
            with self.assertRaises(ValueError):
                apply_migration(root, approve=True)
            self.assertEqual(before, tree_hashes(root))

    def test_migration_commit_failure_restores_the_complete_20_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            scaffold(root, answers(), charter_accepted=True)
            downgrade_to_20(root)
            before = tree_hashes(root)
            real_move = migration_module.shutil.move
            calls = {"count": 0}

            def fail_on_fourth_move(source, target):
                calls["count"] += 1
                if calls["count"] == 4:
                    raise OSError("injected migration failure")
                return real_move(source, target)

            with mock.patch.object(migration_module.shutil, "move", side_effect=fail_on_fourth_move):
                with self.assertRaises(OSError):
                    apply_migration(root, approve=True)
            self.assertEqual(before, tree_hashes(root))
            self.assertEqual(read_json(root / ".svk/project.json")["svk_version"], "2.0.0")
            leftovers = list(root.parent.glob(".%s.svk-migration-*" % root.name))
            self.assertEqual(leftovers, [])


class CliAndPackageTests(unittest.TestCase):
    def test_cli_errors_are_json_envelopes_with_stable_exit_category(self):
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(run(["refresh", "--root", "definitely-missing"]), EXIT_CONTRACT)
        envelope = json.loads(output.getvalue())
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["command"], "refresh")
        self.assertEqual(envelope["result"], "contract_error")
        self.assertEqual(envelope["value"]["result"], "ERROR")

        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(run(["next", "not-a-command"]), EXIT_CONTRACT)
        envelope = json.loads(output.getvalue())
        self.assertFalse(envelope["ok"])
        self.assertEqual(envelope["command"], "next.not-a-command")
        self.assertEqual(envelope["result"], "contract_error")
        self.assertEqual(envelope["error"]["category"], "contract")

    def test_package_contract(self):
        bundle = Path(__file__).resolve().parents[1]
        result = package_check(bundle)
        self.assertEqual(result["result"], "PASS", result)

    def test_python_sources_parse_as_python_311(self):
        release_root = Path(__file__).resolve().parents[2]
        for path in release_root.rglob("*.py"):
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 11))
            except SyntaxError as error:
                self.fail("%s is not Python 3.11 syntax: %s" % (path, error))


if __name__ == "__main__":
    unittest.main()
