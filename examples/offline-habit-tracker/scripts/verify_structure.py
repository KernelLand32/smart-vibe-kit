#!/usr/bin/env python3
"""Structural hygiene check for Smart Vibe Kit projects.

Usage:
  python scripts/verify_structure.py --root .
  python scripts/verify_structure.py --root . --bootstrap
  python scripts/verify_structure.py --root . --strict --bootstrap

Exit 0 = pass. Exit 1 = failure.

Modes:
  (default)     Core process artifacts (ongoing projects).
  --bootstrap   Full tree from references/required-structure.md.
  --strict      Canonical paths only (no aliases such as subtasks.md).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CORE_GROUPS: list[tuple[str, list[str]]] = [
    ("agent entry", ["AGENTS.md", "agents.md"]),
    ("document registry", ["docs/registry.md"]),
    ("active tasks index", ["docs/tasks.md", "docs/subtasks.md"]),
    (
        "verification gates",
        ["docs/verification-gates.md", "docs/dev/verification-gates.md"],
    ),
    (
        "documentation strategy",
        ["docs/documentation-strategy.md", "docs/dev/documentation-strategy.md"],
    ),
    ("ADR template", ["docs/adr/_template.md"]),
]

BOOTSTRAP_FILES: list[tuple[str, list[str]]] = [
    ("roadmap", ["docs/roadmap.md", "docs/plan/roadmap.md"]),
    ("research profile", ["docs/research/profile.md"]),
    ("research landscape", ["docs/research/landscape.md"]),
    ("project charter ADR", ["docs/adr/0001-project-charter.md"]),
    ("authorize stage ADR", ["docs/adr/0002-authorize-phase1-stage1.md"]),
    ("deliverable-spec template", ["docs/_templates/deliverable-spec.md"]),
    ("phase-archive template", ["docs/_templates/phase-archive.md"]),
    ("toolchain pins", ["docs/toolchain-pins.md"]),
    ("project constitution", ["docs/constitution.md"]),
    (
        "structure verifier script",
        ["scripts/verify_structure.py", "scripts/Verify-Structure.py"],
    ),
    ("done checklist", ["docs/checklists/done.md"]),
    ("stage-gate checklist", ["docs/checklists/stage-gate.md"]),
    ("pr checklist", ["docs/checklists/pr.md"]),
    ("workflows index", ["docs/workflows/README.md"]),
    ("workflow constitute", ["docs/workflows/constitute.md"]),
    ("workflow specify", ["docs/workflows/specify.md"]),
    ("workflow authorize", ["docs/workflows/authorize.md"]),
    ("workflow plan-tasks", ["docs/workflows/plan-tasks.md"]),
    ("workflow implement", ["docs/workflows/implement.md"]),
    ("workflow verify", ["docs/workflows/verify.md"]),
    ("workflow close-stage", ["docs/workflows/close-stage.md"]),
    ("workflow recover", ["docs/workflows/recover.md"]),
    ("workflow refresh", ["docs/workflows/refresh.md"]),
    ("archives readme", ["docs/archives/README.md"]),
]

PROCESS_DOC_DIRS = {
    "adr",
    "research",
    "_templates",
    "checklists",
    "workflows",
    "archives",
    "dev",
    "plan",
}

# Any brace group up to 120 chars (catches multi-word template leftovers).
PLACEHOLDER_RE = re.compile(r"\{[^{}]{1,120}\}")
PLACEHOLDER_ALLOWLIST = {
    "{placeholders}",
    "{placeholder}",
    "{brace}",
    "{braces}",
    "{…}",
    "{...}",
    "{N}",  # archive naming prose
    "{slug}",
}

SKIP_PLACEHOLDER_SCAN = {
    "docs/_templates",
    "docs/workflows",
    "docs/checklists",
}

TASK_ID_RE = re.compile(r"^\|\s*(\d+\.\d+\.\d+)\s*\|", re.M)
STATUS_LINE_RE = re.compile(
    r"(?im)^\s*(?:\*\*)?Status(?:\*\*)?\s*:\s*(\*?\*?)\s*(accepted|proposed)\b"
)
# Alternate bullet form: - **Status:** accepted
STATUS_BULLET_RE = re.compile(
    r"(?im)^\s*[-*]\s*\*\*Status:\*\*\s*(accepted|proposed)\b"
)


def resolve_root(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    cwd = Path.cwd()
    if cwd.name == "smart-vibe-kit" and (cwd.parent / "AGENTS.md").exists():
        return cwd.parent.resolve()
    return cwd.resolve()


def first_existing(root: Path, candidates: list[str]) -> Path | None:
    for rel in candidates:
        path = root / rel
        if path.is_file():
            return path
    return None


def check_groups(
    root: Path,
    groups: list[tuple[str, list[str]]],
    strict: bool,
) -> tuple[list[tuple[str, str]], list[str]]:
    resolved: list[tuple[str, str]] = []
    missing: list[str] = []
    for label, candidates in groups:
        use = candidates[:1] if strict else candidates
        found = first_existing(root, use)
        if found is None:
            missing.append(f"{label} (tried: {', '.join(use)})")
        else:
            resolved.append(
                (label, str(found.relative_to(root)).replace("\\", "/"))
            )
    return resolved, missing


def domain_areas(root: Path) -> list[Path]:
    docs = root / "docs"
    if not docs.is_dir():
        return []
    areas: list[Path] = []
    for child in sorted(docs.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if child.name in PROCESS_DOC_DIRS:
            continue
        areas.append(child)
    return areas


def deliverable_files(area: Path) -> list[Path]:
    return [p for p in area.rglob("*.md") if p.is_file()]


def _has_gate_section(text: str) -> bool:
    return (
        "Gate checklist" in text
        or "## Verification" in text
        or "Verification (gate" in text
    )


def check_domain_deliverables(root: Path) -> list[str]:
    errors: list[str] = []
    areas = domain_areas(root)
    if len(areas) < 2:
        names = ", ".join(a.name for a in areas) or "(none)"
        errors.append(
            f"need >=2 domain folders under docs/ "
            f"(excluding process dirs); found {len(areas)}: {names}"
        )
        return errors

    for area in areas:
        files = deliverable_files(area)
        if not files:
            errors.append(f"domain folder docs/{area.name}/ has no .md deliverable")
            continue
        ok = False
        for f in files:
            text = f.read_text(encoding="utf-8", errors="replace")
            if (
                "Verifiable claims" in text
                and "OQ-" in text
                and _has_gate_section(text)
            ):
                ok = True
                break
        if not ok:
            errors.append(
                f"docs/{area.name}/: need one deliverable with Verifiable claims "
                f"AND OQ- AND Verification/gate checklist"
            )
    return errors


def scan_placeholders(root: Path) -> list[str]:
    hits: list[str] = []
    for path in root.rglob("*.md"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if any(rel == d or rel.startswith(d + "/") for d in SKIP_PLACEHOLDER_SCAN):
            continue
        if rel.startswith("examples/"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in PLACEHOLDER_RE.finditer(text):
            token = m.group(0)
            if token in PLACEHOLDER_ALLOWLIST:
                continue
            # Allow archive naming docs that discuss the pattern literally
            if token.startswith("{N}") or "phase-{N}" in token:
                continue
            hits.append(f"{rel}: {token[:60]}{'…' if len(token) > 60 else ''}")
            if len(hits) >= 20:
                hits.append("… (further placeholders truncated)")
                return hits
    return hits


def check_next_action(root: Path, strict: bool) -> list[str]:
    candidates = ["docs/tasks.md"] if strict else ["docs/tasks.md", "docs/subtasks.md"]
    tasks = first_existing(root, candidates)
    if tasks is None:
        return []
    text = tasks.read_text(encoding="utf-8", errors="replace")
    if "Next action" not in text:
        rel = str(tasks.relative_to(root)).replace("\\", "/")
        return [f"{rel} has no 'Next action' line"]
    return []


def check_adr_statuses(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in (
        "docs/adr/0001-project-charter.md",
        "docs/adr/0002-authorize-phase1-stage1.md",
    ):
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not (STATUS_LINE_RE.search(text) or STATUS_BULLET_RE.search(text)):
            errors.append(
                f"{rel}: need a Status line with accepted|proposed "
                f"(e.g. **Status:** accepted)"
            )
    return errors


def check_task_registry(root: Path, strict: bool) -> list[str]:
    candidates = ["docs/tasks.md"] if strict else ["docs/tasks.md", "docs/subtasks.md"]
    tasks_path = first_existing(root, candidates)
    registry_path = root / "docs" / "registry.md"
    if tasks_path is None or not registry_path.is_file():
        return []
    tasks_text = tasks_path.read_text(encoding="utf-8", errors="replace")
    registry_text = registry_path.read_text(encoding="utf-8", errors="replace")
    ids = TASK_ID_RE.findall(tasks_text)
    if not ids:
        return [
            f"{tasks_path.as_posix()}: no task IDs matching N.N.N in table rows"
        ]
    missing = [tid for tid in ids if tid not in registry_text]
    if missing:
        return [
            "task IDs missing from docs/registry.md: " + ", ".join(missing)
        ]
    return []


def check_constitution_customized(root: Path) -> list[str]:
    path = root / "docs" / "constitution.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    for article in ("Article IV", "Article V", "Article VI"):
        if article not in text:
            errors.append(f"docs/constitution.md: missing {article}")
    # Reject unedited kit-style customize placeholders
    lower = text.lower()
    if "(customize)" in lower and (
        "example placeholder" in lower or "{hard separations" in lower
    ):
        errors.append(
            "docs/constitution.md: Articles IV–VI still look like unedited kit placeholders"
        )
    # Article IV body should not be only the heading
    m = re.search(
        r"## Article IV[^\n]*\n+(.*?)(?=\n## |\Z)", text, re.S | re.I
    )
    if m and len(m.group(1).strip()) < 40:
        errors.append(
            "docs/constitution.md: Article IV body too short — customize domain walls"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Smart Vibe Kit project structure"
    )
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require canonical names only (no path aliases)",
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Enforce full required-structure.md tree (use after /smart-vibe-kit)",
    )
    args = parser.parse_args()
    root = resolve_root(args.root)

    mode = "bootstrap" if args.bootstrap else "core"
    print(f"Smart Vibe Kit structure check — root: {root} (mode={mode})")

    resolved, missing = check_groups(root, CORE_GROUPS, args.strict)

    # Next action required whenever tasks index exists (core + bootstrap).
    missing.extend(check_next_action(root, args.strict))

    if args.bootstrap:
        b_resolved, b_missing = check_groups(root, BOOTSTRAP_FILES, args.strict)
        resolved.extend(b_resolved)
        missing.extend(b_missing)
        missing.extend(check_domain_deliverables(root))
        missing.extend(check_adr_statuses(root))
        missing.extend(check_task_registry(root, args.strict))
        missing.extend(check_constitution_customized(root))
        placeholders = scan_placeholders(root)
        if placeholders:
            missing.append(
                "unresolved {placeholders} in project markdown:\n    - "
                + "\n    - ".join(placeholders)
            )

    if missing:
        print("FAIL — structure problems:")
        for item in missing:
            print(f"  - {item}")
        print(
            "\nSee installed skill references/required-structure.md "
            "(or re-run /smart-vibe-kit after fixing)."
        )
        return 1

    print("PASS — required process artifacts present:")
    for label, rel in resolved:
        print(f"  OK  {label}: {rel}")

    if not args.bootstrap:
        hint_paths = [
            "docs/roadmap.md",
            "docs/research/profile.md",
            "docs/toolchain-pins.md",
            "docs/checklists/done.md",
            "scripts/verify_structure.py",
        ]
        hints_missing = [rel for rel in hint_paths if not (root / rel).is_file()]
        if hints_missing:
            print("\nOptional / bootstrap artifacts not present (OK in core mode):")
            for rel in hints_missing:
                print(f"  --  {rel}")

    adr_dir = root / "docs/adr"
    if adr_dir.is_dir():
        adrs = [p for p in adr_dir.glob("*.md") if p.name != "_template.md"]
        print(f"\nADRs found: {len(adrs)}")
    else:
        print("\nWARN — docs/adr/ missing")

    return 0


if __name__ == "__main__":
    sys.exit(main())
