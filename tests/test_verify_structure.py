"""Tests for verify_structure.py, skill package, and install manifest."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts" / "verify_structure.py"
GEN = ROOT / "scripts" / "gen_minimal_tree.py"
SKILL_VERIFY = ROOT / "scripts" / "verify_skill_package.py"
MANIFEST = ROOT / "scripts" / "install-manifest.txt"


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def gen_tree(out: Path, name: str = "HabitVault") -> None:
    proc = run([str(GEN), "--out", str(out), "--name", name])
    assert proc.returncode == 0, proc.stdout + proc.stderr


class VerifyStructureTests(unittest.TestCase):
    def test_skill_package_ok(self) -> None:
        gen_tree(ROOT / "tests" / "fixtures" / "minimal_bootstrap")
        gen_tree(ROOT / "examples" / "offline-habit-tracker")
        proc = run([str(SKILL_VERIFY), "--root", str(ROOT)])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("privacy scan: clean", proc.stdout)

    def test_bootstrap_fixture_passes(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "minimal_bootstrap"
        gen_tree(fixture)
        proc = run([str(VERIFY), "--root", str(fixture), "--bootstrap", "--strict"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_bootstrap_fails_without_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "proj"
            gen_tree(out)
            shutil.rmtree(out / "docs" / "engineering")
            proc = run([str(VERIFY), "--root", str(out), "--bootstrap"])
            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertTrue("domain" in combined or "found 1" in combined, combined)

    def test_bootstrap_fails_on_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "proj"
            gen_tree(out)
            agents = out / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8")
                + "\nSee {Hard separations — example leftover}.\n",
                encoding="utf-8",
            )
            proc = run([str(VERIFY), "--root", str(out), "--bootstrap"])
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("placeholder", proc.stdout.lower())

    def test_bootstrap_fails_missing_registry_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "proj"
            gen_tree(out)
            tasks = out / "docs" / "tasks.md"
            text = tasks.read_text(encoding="utf-8")
            text = text.replace(
                "| 1.1.5 | not_started | Stage 1 gate | product/overview |",
                "| 1.1.5 | not_started | Stage 1 gate | product/overview |\n"
                "| 1.1.9 | not_started | Orphan task | product/overview |",
            )
            tasks.write_text(text, encoding="utf-8")
            proc = run([str(VERIFY), "--root", str(out), "--bootstrap"])
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("1.1.9", proc.stdout)

    def test_bootstrap_fails_domain_or_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "proj"
            gen_tree(out)
            eng = out / "docs" / "engineering" / "constraints.md"
            eng.write_text(
                "# Eng\n\n## Verification\n\nEmpty gate only.\n",
                encoding="utf-8",
            )
            proc = run([str(VERIFY), "--root", str(out), "--bootstrap"])
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("Verifiable claims", proc.stdout)

    def test_bootstrap_fails_adr_without_status_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "proj"
            gen_tree(out)
            adr = out / "docs" / "adr" / "0001-project-charter.md"
            adr.write_text(
                "# ADR-0001\n\nWe accepted this in conversation.\n",
                encoding="utf-8",
            )
            proc = run([str(VERIFY), "--root", str(out), "--bootstrap"])
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("Status", proc.stdout)

    def test_core_mode_fails_without_next_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# A\n", encoding="utf-8")
            docs = root / "docs"
            docs.mkdir()
            (docs / "registry.md").write_text("# r\n", encoding="utf-8")
            (docs / "tasks.md").write_text("# t\n\nNo next line here.\n", encoding="utf-8")
            (docs / "verification-gates.md").write_text("# v\n", encoding="utf-8")
            (docs / "documentation-strategy.md").write_text("# d\n", encoding="utf-8")
            adr = docs / "adr"
            adr.mkdir()
            (adr / "_template.md").write_text("# a\n", encoding="utf-8")
            proc = run([str(VERIFY), "--root", str(root)])
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("Next action", proc.stdout)

    def test_core_mode_passes_with_next_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# A\n", encoding="utf-8")
            docs = root / "docs"
            docs.mkdir()
            (docs / "registry.md").write_text("# r\n", encoding="utf-8")
            (docs / "tasks.md").write_text(
                "# t\n\n**Next action:** x\n", encoding="utf-8"
            )
            (docs / "verification-gates.md").write_text("# v\n", encoding="utf-8")
            (docs / "documentation-strategy.md").write_text("# d\n", encoding="utf-8")
            adr = docs / "adr"
            adr.mkdir()
            (adr / "_template.md").write_text("# a\n", encoding="utf-8")
            proc = run([str(VERIFY), "--root", str(root)])
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_install_manifest_excludes_dev_paths(self) -> None:
        text = MANIFEST.read_text(encoding="utf-8")
        entries = [
            ln.strip()
            for ln in text.splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        joined = "\n".join(entries)
        self.assertNotIn("gen_minimal_tree.py", joined)
        self.assertNotIn("tests/test_verify_structure.py", joined)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "skill"
            dest.mkdir()
            for line in entries:
                src = ROOT / line
                self.assertTrue(src.exists(), f"missing manifest source {line}")
                target = dest / line
                target.parent.mkdir(parents=True, exist_ok=True)
                if src.is_dir():
                    shutil.copytree(src, target)
                else:
                    shutil.copy2(src, target)
            self.assertTrue((dest / "SKILL.md").is_file())
            self.assertFalse((dest / "scripts" / "gen_minimal_tree.py").exists())
            self.assertFalse((dest / "tests").exists())
            self.assertTrue(
                (dest / "references" / "workflows" / "refresh.md").is_file()
            )


if __name__ == "__main__":
    unittest.main()
