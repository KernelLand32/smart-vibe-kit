"""Stable constants shared by every SVK action."""

VERSION = "2.0.0"
STATE_DIR = ".svk"
PROFILE_FILE = ".svk/project.json"
STATE_FILE = ".svk/state.json"
EVIDENCE_FILE = ".svk/evidence.jsonl"
INSTALL_FILE = ".svk/install.json"
LOCK_FILE = ".svk/locks/next.json"
MANIFEST_FILE = ".svk/baselines/manifest.json"

MODULES = (
    "core",
    "research",
    "product",
    "design",
    "engineering",
    "operations",
    "security",
    "regulated",
    "collaboration",
)

STATUS_VALUES = ("pending", "in_progress", "blocked", "done")
TASK_ID_PATTERN = r"^[1-9][0-9]*\.[1-9][0-9]*\.[1-9][0-9]*$"

CORE_DOCUMENTS = (
    "AGENTS.md",
    "docs/constitution.md",
    "docs/tasks.md",
    "docs/registry.md",
    "docs/adr/0001-project-charter.md",
    "docs/verification.md",
)

MODULE_DOCUMENTS = {
    "research": ("docs/research/brief.md", "docs/research/sources.md"),
    "product": ("docs/product/requirements.md", "docs/product/acceptance.md"),
    "design": ("docs/design/system.md", "docs/design/accessibility.md"),
    "engineering": ("docs/engineering/architecture.md", "docs/engineering/interfaces.md"),
    "operations": ("docs/operations/runbook.md", "docs/operations/release.md"),
    "security": ("docs/security/threat-model.md", "docs/security/data-handling.md"),
    "regulated": (
        "docs/compliance/controls.md",
        "docs/compliance/traceability.md",
        "docs/compliance/risk-register.md",
    ),
    "collaboration": ("docs/collaboration/ownership.md", "docs/collaboration/decisions.md"),
}

DIAGNOSTIC_LEVELS = ("PASS", "WARN", "BLOCKED", "ERROR")
