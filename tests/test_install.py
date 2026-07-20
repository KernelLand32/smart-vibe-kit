"""Tests for cross-platform install path resolution and dry-run."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL_PY = ROOT / "scripts" / "install.py"


def load_install():
    spec = importlib.util.spec_from_file_location("svk_install", INSTALL_PY)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INSTALL_PY), *args],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


class InstallTests(unittest.TestCase):
    def test_hosts_cover_popular_apps(self) -> None:
        mod = load_install()
        self.assertEqual(
            set(mod.HOSTS),
            {"agents", "cursor", "claude", "codex", "gemini"},
        )

    def test_codex_project_equals_agents_project(self) -> None:
        mod = load_install()
        root = Path("/tmp/proj") if sys.platform != "win32" else Path("C:/proj")
        agents = mod.expand_dest(mod.HOSTS["agents"]["project"], root)
        codex = mod.expand_dest(mod.HOSTS["codex"]["project"], root)
        self.assertEqual(agents, codex)

    def test_what_if_all_dedupes_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc = run(
                [
                    "--what-if",
                    "--target",
                    "all",
                    "--scope",
                    "project",
                    "--project-root",
                    tmp,
                ]
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("skip duplicate path", proc.stdout)
            # Should mention agents/cursor/claude/gemini at least once
            for host in ("agents", "cursor", "claude", "gemini"):
                self.assertIn(host, proc.stdout)

    def test_list_runs(self) -> None:
        proc = run(["--list"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(".agents/skills", proc.stdout.replace("\\", "/"))

    def test_install_and_uninstall_agents_tmpdir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            # Patch HOME/USERPROFILE for this subprocess
            env = {
                **dict(**{k: v for k, v in __import__("os").environ.items()}),
                "HOME": str(home),
                "USERPROFILE": str(home),
            }
            proc = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_PY),
                    "--target",
                    "agents",
                    "--scope",
                    "user",
                    "--no-backup",
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            skill = home / ".agents" / "skills" / "smart-vibe-kit" / "SKILL.md"
            self.assertTrue(skill.is_file(), proc.stdout)

            proc2 = subprocess.run(
                [
                    sys.executable,
                    str(INSTALL_PY),
                    "--uninstall",
                    "--target",
                    "agents",
                    "--scope",
                    "user",
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
                env=env,
            )
            self.assertEqual(proc2.returncode, 0, proc2.stdout + proc2.stderr)
            self.assertFalse(skill.exists())


if __name__ == "__main__":
    unittest.main()
