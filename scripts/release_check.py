#!/usr/bin/env python3
"""Validate the complete Smart Vibe Kit source release."""

from __future__ import print_function

import ast
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "skill" / "runtime"
sys.path.insert(0, str(RUNTIME))

from svk_core.constants import VERSION  # noqa: E402
from svk_core.verify import check_project, package_check  # noqa: E402


LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FENCE_RE = re.compile(r"^\s*```", re.MULTILINE)
PRIVATE_PATTERNS = (
    re.compile(r"C:\\Users\\", re.IGNORECASE),
    re.compile(r"\.codex[\\/]visualizations", re.IGNORECASE),
    re.compile(r"pasted-text-\d+", re.IGNORECASE),
    re.compile(r"svk200-stage", re.IGNORECASE),
)
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", "node_modules", ".DS_Store"}


def issue(code, message, path=None):
    value = {"code": code, "message": message}
    if path is not None:
        value["path"] = str(path).replace("\\", "/")
    return value


def relative(path):
    return path.relative_to(ROOT)


def check_required_files(issues):
    required = (
        ".editorconfig",
        ".gitignore",
        ".github/workflows/ci.yml",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "NOTICE",
        "README.md",
        "RELEASING.md",
        "SECURITY.md",
        "installer/install.py",
        "installer/install.ps1",
        "installer/install.sh",
        "skill/VERSION",
        "scripts/build_release.py",
    )
    for name in required:
        path = ROOT / name
        if not path.is_file() or path.stat().st_size == 0:
            issues.append(issue("RELEASE-FILE", "Required release file is missing or empty.", name))


def check_versions(issues):
    consumers = {
        "skill/VERSION": ROOT / "skill/VERSION",
        "installer/install.py": ROOT / "installer/install.py",
        "skill/runtime/svk_core/constants.py": ROOT / "skill/runtime/svk_core/constants.py",
        "CHANGELOG.md": ROOT / "CHANGELOG.md",
    }
    tests = {
        "skill/VERSION": lambda text: text.strip() == VERSION,
        "installer/install.py": lambda text: ('VERSION = "%s"' % VERSION) in text,
        "skill/runtime/svk_core/constants.py": lambda text: ('VERSION = "%s"' % VERSION) in text,
        "CHANGELOG.md": lambda text: ("## %s" % VERSION) in text,
    }
    for name, path in consumers.items():
        if path.is_file() and not tests[name](path.read_text(encoding="utf-8")):
            issues.append(issue("RELEASE-VERSION", "Version does not match %s." % VERSION, name))


def check_machine_files(issues):
    for path in ROOT.rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            issues.append(issue("RELEASE-JSON", str(error), relative(path)))
    for path in ROOT.rglob("*.jsonl"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as error:
                issues.append(issue("RELEASE-JSONL", "Line %d: %s" % (number, error), relative(path)))
    for path in ROOT.rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as error:
            issues.append(issue("RELEASE-PYTHON", str(error), relative(path)))


def check_markdown(issues):
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if len(FENCE_RE.findall(text)) % 2:
            issues.append(issue("RELEASE-FENCE", "Markdown has an unclosed fenced code block.", relative(path)))
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip().split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            target = unquote(target)
            candidate = (path.parent / target).resolve()
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                issues.append(issue("RELEASE-LINK-ESCAPE", "Local link escapes the release: %s" % target, relative(path)))
                continue
            if not candidate.exists():
                issues.append(issue("RELEASE-LINK", "Local link does not resolve: %s" % target, relative(path)))


def check_cleanliness(issues):
    for path in ROOT.rglob("*"):
        if any(part in FORBIDDEN_PARTS for part in relative(path).parts):
            issues.append(issue("RELEASE-CACHE", "Generated cache or dependency directory is not publishable.", relative(path)))
            break
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".zip"):
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in PRIVATE_PATTERNS:
            if pattern.search(text):
                issues.append(issue("RELEASE-PRIVATE-PATH", "Release text contains a local development path or attachment reference.", relative(path)))
                break


def main():
    issues = []
    check_required_files(issues)
    check_versions(issues)
    check_machine_files(issues)
    check_markdown(issues)
    check_cleanliness(issues)

    package = package_check(ROOT / "skill")
    for diagnostic in package["diagnostics"]:
        issues.append(issue("PACKAGE-" + diagnostic["code"], diagnostic["message"], diagnostic.get("path")))

    examples = []
    examples_root = ROOT / "examples"
    if examples_root.is_dir():
        for project in sorted(path for path in examples_root.iterdir() if path.is_dir()):
            result = check_project(project)
            examples.append({"project": project.name, "result": result["result"]})
            if result["result"] != "PASS":
                issues.append(issue("RELEASE-EXAMPLE", "Example check returned %s." % result["result"], relative(project)))
    if not examples:
        issues.append(issue("RELEASE-EXAMPLE-MISSING", "At least one checked worked example is required.", "examples"))

    payload = {
        "version": VERSION,
        "result": "PASS" if not issues else "ERROR",
        "examples": examples,
        "issues": issues,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
