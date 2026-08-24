"""Semantic verification for generated projects and the distributable package."""

from __future__ import print_function

import ast
import json
import re
from datetime import date
from datetime import datetime, timezone
from pathlib import Path

from .constants import (
    CORE_DOCUMENTS,
    EVIDENCE_FILE,
    INSTALL_FILE,
    LOCK_FILE,
    MANIFEST_FILE,
    MODULES,
    MODULE_DOCUMENTS,
    PROFILE_FILE,
    STATE_FILE,
    STATUS_VALUES,
    TASK_ID_PATTERN,
    VERSION,
)
from .profile import expected_document_count, profile_name, select_modules
from .util import read_json, sha256_file


LEVEL_RANK = {"PASS": 0, "WARN": 1, "BLOCKED": 2, "ERROR": 3}
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME)\b|\[PLACEHOLDER\]|<fill(?:-|\s)", re.IGNORECASE)
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def diagnostic(code, level, message, path=None):
    value = {"code": code, "level": level, "message": message}
    if path:
        value["path"] = str(path).replace("\\", "/")
    return value


def overall(diagnostics):
    if not diagnostics:
        return "PASS"
    return max((item["level"] for item in diagnostics), key=lambda level: LEVEL_RANK[level])


def _load(path, code, diagnostics):
    try:
        return read_json(path)
    except FileNotFoundError:
        diagnostics.append(diagnostic(code + ".MISSING", "ERROR", "Required JSON file is missing.", path))
    except (ValueError, json.JSONDecodeError) as error:
        diagnostics.append(diagnostic(code + ".INVALID_JSON", "ERROR", str(error), path))
    return None


def _required_paths(profile):
    required = list(CORE_DOCUMENTS) + [PROFILE_FILE, STATE_FILE, EVIDENCE_FILE, INSTALL_FILE, MANIFEST_FILE]
    for module in profile.get("modules", []):
        required.extend(MODULE_DOCUMENTS.get(module, ()))
    return required


def _validate_profile(profile, diagnostics):
    if not isinstance(profile, dict):
        diagnostics.append(diagnostic("SVK-PROFILE-TYPE", "ERROR", "Project profile must be an object."))
        return
    if profile.get("svk_version") != VERSION:
        diagnostics.append(diagnostic("SVK-PROFILE-VERSION", "ERROR", "Profile version must be %s." % VERSION))
    if not isinstance(profile.get("title"), str) or not profile.get("title", "").strip():
        diagnostics.append(diagnostic("SVK-PROFILE-TITLE", "ERROR", "Profile title must be non-empty."))
    modules = profile.get("modules")
    if not isinstance(modules, list) or "core" not in modules or len(modules) != len(set(modules)):
        diagnostics.append(diagnostic("SVK-PROFILE-MODULES", "ERROR", "Modules must be unique and include core."))
        return
    unknown = set(modules) - set(MODULES)
    if unknown:
        diagnostics.append(diagnostic("SVK-PROFILE-MODULE-UNKNOWN", "ERROR", "Unknown modules: %s" % ", ".join(sorted(unknown))))
    try:
        answer_view = dict(profile.get("signals", {}))
        answer_view.update(
            {
                "research_tier": profile.get("research_tier", 0),
                "integrations": profile.get("integrations", []),
                "team_size": profile.get("team_size", 1),
            }
        )
        required = set(select_modules(answer_view))
        missing = required - set(modules)
        if missing:
            diagnostics.append(diagnostic("SVK-PROFILE-UNSAFE-DOWNGRADE", "ERROR", "Required modules were removed: %s" % ", ".join(sorted(missing))))
        expected = expected_document_count(modules)
        if profile.get("expected_document_count") != expected:
            diagnostics.append(diagnostic("SVK-PROFILE-DOCUMENT-COUNT", "ERROR", "expected_document_count must be %d for the selected modules." % expected))
        expected_name = profile_name(modules, {"risk": profile.get("risk", "normal")})
        if profile.get("profile") != expected_name:
            diagnostics.append(diagnostic("SVK-PROFILE-LABEL", "ERROR", "Profile label must be %s for the selected modules and risk." % expected_name))
    except (TypeError, ValueError) as error:
        diagnostics.append(diagnostic("SVK-PROFILE-SIGNALS", "ERROR", str(error)))


def _validate_state(state, profile, diagnostics):
    if not isinstance(state, dict):
        diagnostics.append(diagnostic("SVK-STATE-TYPE", "ERROR", "Project state must be an object."))
        return
    if state.get("schema_version") != "2.0" or state.get("kit_version") != VERSION:
        diagnostics.append(diagnostic("SVK-STATE-VERSION", "ERROR", "State schema/version is not SVK 2.0.0."))
    tasks = state.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        diagnostics.append(diagnostic("SVK-TASKS-EMPTY", "ERROR", "State must contain tasks."))
        return
    ids = []
    by_id = {}
    for task in tasks:
        if not isinstance(task, dict):
            diagnostics.append(diagnostic("SVK-TASK-TYPE", "ERROR", "Every task must be an object."))
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str) or not re.match(TASK_ID_PATTERN, task_id):
            diagnostics.append(diagnostic("SVK-TASK-ID", "ERROR", "Invalid task ID: %r" % task_id))
            continue
        ids.append(task_id)
        by_id[task_id] = task
        if task.get("status") not in STATUS_VALUES:
            diagnostics.append(diagnostic("SVK-TASK-STATUS", "ERROR", "Invalid status for task %s." % task_id))
        dependencies = task.get("depends_on", [])
        if not isinstance(dependencies, list):
            diagnostics.append(diagnostic("SVK-TASK-DEPS", "ERROR", "Dependencies must be an array for task %s." % task_id))
        if not isinstance(task.get("title"), str) or not task.get("title", "").strip():
            diagnostics.append(diagnostic("SVK-TASK-TITLE", "ERROR", "Task %s requires a non-empty title." % task_id))
        if not isinstance(task.get("human_gate"), bool):
            diagnostics.append(diagnostic("SVK-TASK-HUMAN-GATE", "ERROR", "Task %s requires a boolean human_gate." % task_id))
    duplicates = sorted({task_id for task_id in ids if ids.count(task_id) > 1})
    if duplicates:
        diagnostics.append(diagnostic("SVK-TASK-DUPLICATE", "ERROR", "Duplicate task IDs: %s" % ", ".join(duplicates)))
    for task in tasks:
        if not isinstance(task, dict):
            continue
        for dependency in task.get("depends_on", []) if isinstance(task.get("depends_on", []), list) else []:
            if dependency not in by_id:
                diagnostics.append(diagnostic("SVK-TASK-DEPENDENCY-MISSING", "ERROR", "Task %s depends on unknown task %s." % (task.get("id"), dependency)))
            elif dependency == task.get("id"):
                diagnostics.append(diagnostic("SVK-TASK-DEPENDENCY-SELF", "ERROR", "Task %s cannot depend on itself." % task.get("id")))

    def visit(task_id, visiting, visited):
        if task_id in visiting:
            diagnostics.append(diagnostic("SVK-TASK-DEPENDENCY-CYCLE", "ERROR", "Task dependency cycle includes %s." % task_id))
            return
        if task_id in visited or task_id not in by_id:
            return
        visiting.add(task_id)
        for dependency in by_id[task_id].get("depends_on", []):
            visit(dependency, visiting, visited)
        visiting.remove(task_id)
        visited.add(task_id)

    visited = set()
    for task_id in by_id:
        visit(task_id, set(), visited)

    for task in tasks:
        if not isinstance(task, dict) or task.get("status") not in ("in_progress", "blocked", "done"):
            continue
        incomplete = [dependency for dependency in task.get("depends_on", []) if by_id.get(dependency, {}).get("status") != "done"]
        if incomplete:
            diagnostics.append(diagnostic("SVK-TASK-DEPENDENCY-INCOMPLETE", "ERROR", "Task %s is active or done before dependencies are done: %s" % (task.get("id"), ", ".join(incomplete))))

    active = [task for task in tasks if task.get("status") in ("in_progress", "blocked")]
    blocked = [task for task in active if task.get("status") == "blocked"]
    if blocked:
        diagnostics.append(diagnostic("SVK-TASK-BLOCKED", "BLOCKED", "Task %s is blocked: %s" % (blocked[0].get("id"), blocked[0].get("blocker", "reason not recorded"))))
    all_done = all(task.get("status") == "done" for task in tasks if isinstance(task, dict))
    if len(active) != 1 and not (all_done and len(active) == 0):
        diagnostics.append(diagnostic("SVK-ACTIVE-COUNT", "ERROR", "Exactly one task must be active until all tasks are done; found %d." % len(active)))
    action = state.get("next_action")
    if all_done and action is None:
        pass
    elif not isinstance(action, dict) or action.get("task_id") not in by_id:
        diagnostics.append(diagnostic("SVK-NEXT-ACTION", "ERROR", "next_action must name a real task."))
    elif len(active) == 1 and action.get("task_id") != active[0].get("id"):
        diagnostics.append(diagnostic("SVK-NEXT-MISMATCH", "ERROR", "next_action does not match the active task."))
    elif len(active) == 1 and action.get("instruction") != active[0].get("title"):
        diagnostics.append(diagnostic("SVK-NEXT-INSTRUCTION", "ERROR", "next_action instruction does not match the active task title."))

    accepted = bool(state.get("charter", {}).get("accepted", False))
    charter_task = by_id.get("1.1.2", {})
    if accepted != (charter_task.get("status") == "done"):
        diagnostics.append(diagnostic("SVK-CHARTER-STATE", "ERROR", "Charter acceptance and task 1.1.2 disagree."))
    if profile and state.get("project") != profile.get("slug"):
        diagnostics.append(diagnostic("SVK-PROJECT-MISMATCH", "ERROR", "State and profile identify different projects."))


def _validate_evidence(root, state, diagnostics):
    path = root / EVIDENCE_FILE
    records = []
    if path.exists():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                diagnostics.append(diagnostic("SVK-EVIDENCE-JSON", "ERROR", "Line %d: %s" % (number, error), EVIDENCE_FILE))
    known_ids = {task.get("id") for task in (state or {}).get("tasks", []) if isinstance(task, dict)}
    evidence_ids = {
        record.get("task_id")
        for record in records
        if isinstance(record, dict) and record.get("result") == "pass"
    }
    for record in records:
        if not isinstance(record, dict) or any(key not in record for key in ("task_id", "summary", "commands", "artifacts", "result")):
            diagnostics.append(diagnostic("SVK-EVIDENCE-SHAPE", "ERROR", "Every evidence record requires task_id, summary, commands, artifacts, and result.", EVIDENCE_FILE))
        elif not isinstance(record.get("commands"), list) or not isinstance(record.get("artifacts"), list) or record.get("result") not in ("pass", "fail", "partial"):
            diagnostics.append(diagnostic("SVK-EVIDENCE-VALUES", "ERROR", "Evidence commands/artifacts must be arrays and result must be pass, fail, or partial.", EVIDENCE_FILE))
        else:
            if record.get("task_id") not in known_ids:
                diagnostics.append(diagnostic("SVK-EVIDENCE-TASK", "ERROR", "Evidence refers to an unknown task: %s" % record.get("task_id"), EVIDENCE_FILE))
            if not isinstance(record.get("summary"), str) or not record.get("summary", "").strip():
                diagnostics.append(diagnostic("SVK-EVIDENCE-SUMMARY", "ERROR", "Evidence summary must be non-empty.", EVIDENCE_FILE))
            if any(not isinstance(item, str) or not item.strip() for item in record.get("commands", [])):
                diagnostics.append(diagnostic("SVK-EVIDENCE-COMMAND", "ERROR", "Evidence commands must contain non-empty strings.", EVIDENCE_FILE))
            for artifact in record.get("artifacts", []):
                if not isinstance(artifact, str) or not artifact.strip():
                    diagnostics.append(diagnostic("SVK-EVIDENCE-ARTIFACT", "ERROR", "Evidence artifacts must contain non-empty relative paths.", EVIDENCE_FILE))
                    continue
                if artifact.startswith(("https://", "http://")):
                    continue
                candidate = Path(artifact)
                if candidate.is_absolute() or ".." in candidate.parts:
                    diagnostics.append(diagnostic("SVK-EVIDENCE-ARTIFACT-PATH", "ERROR", "Evidence artifact must stay inside the project: %s" % artifact, EVIDENCE_FILE))
                    continue
                if not (root / candidate).exists():
                    diagnostics.append(diagnostic("SVK-EVIDENCE-ARTIFACT-MISSING", "ERROR", "Evidence artifact does not exist: %s" % artifact, EVIDENCE_FILE))
    if state:
        for task in state.get("tasks", []):
            if task.get("status") == "done" and task.get("id") not in evidence_ids:
                diagnostics.append(diagnostic("SVK-EVIDENCE-MISSING", "ERROR", "Completed task %s lacks evidence." % task.get("id"), EVIDENCE_FILE))


def _validate_markdown(root, state, diagnostics):
    state_ids = {task.get("id") for task in (state or {}).get("tasks", [])}
    task_doc = root / "docs/tasks.md"
    if task_doc.exists():
        text = task_doc.read_text(encoding="utf-8")
        doc_ids = set(re.findall(r"(?<![0-9])([1-9][0-9]*\.[1-9][0-9]*\.[1-9][0-9]*)(?![0-9])", text))
        if doc_ids != state_ids:
            diagnostics.append(diagnostic("SVK-TASK-DOC-DRIFT", "ERROR", "docs/tasks.md task IDs differ from state.", "docs/tasks.md"))
        documented_status = dict(re.findall(r"\|\s*([1-9][0-9]*\.[1-9][0-9]*\.[1-9][0-9]*)\s*\|\s*(pending|in_progress|blocked|done)\s*\|", text))
        state_status = {task.get("id"): task.get("status") for task in (state or {}).get("tasks", [])}
        if documented_status != state_status:
            diagnostics.append(diagnostic("SVK-TASK-STATUS-DRIFT", "ERROR", "docs/tasks.md statuses differ from state.", "docs/tasks.md"))
    charter_doc = root / "docs/adr/0001-project-charter.md"
    if charter_doc.exists() and state:
        charter_text = charter_doc.read_text(encoding="utf-8")
        documented_accepted = "Status: **accepted**" in charter_text
        if documented_accepted != bool(state.get("charter", {}).get("accepted", False)):
            diagnostics.append(diagnostic("SVK-CHARTER-DOC-DRIFT", "ERROR", "Charter document status differs from state.", "docs/adr/0001-project-charter.md"))
    agents_doc = root / "AGENTS.md"
    if agents_doc.exists() and state:
        action = state.get("next_action")
        expected = "Complete" if action is None else "%s — %s" % (action.get("task_id"), action.get("instruction"))
        if expected not in agents_doc.read_text(encoding="utf-8"):
            diagnostics.append(diagnostic("SVK-AGENTS-OBJECTIVE-DRIFT", "ERROR", "AGENTS.md current objective differs from state.", "AGENTS.md"))
    for path in sorted(root.rglob("*.md")):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        text = path.read_text(encoding="utf-8")
        if PLACEHOLDER_RE.search(text):
            diagnostics.append(diagnostic("SVK-PLACEHOLDER", "ERROR", "Unresolved placeholder text found.", relative))
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.strip("<>")
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                diagnostics.append(diagnostic("SVK-LINK-ESCAPE", "ERROR", "Relative link escapes the project: %s" % target, relative))
                continue
            if not resolved.exists():
                diagnostics.append(diagnostic("SVK-LINK-MISSING", "ERROR", "Relative link does not resolve: %s" % target, relative))


def _validate_transactions(root, diagnostics):
    transaction_dir = root / ".svk/transactions"
    if transaction_dir.exists():
        for path in sorted(transaction_dir.glob("*.json")):
            transaction = _load(path, "SVK-TRANSACTION", diagnostics)
            if transaction and transaction.get("status") not in ("committed", "rolled_back"):
                diagnostics.append(diagnostic("SVK-TRANSACTION-INCOMPLETE", "BLOCKED", "Incomplete transaction requires review.", path.relative_to(root)))
    lock = root / LOCK_FILE
    if lock.exists():
        value = _load(lock, "SVK-LOCK", diagnostics)
        if value:
            if not isinstance(value.get("owner"), str) or not value.get("owner", "").strip() or not isinstance(value.get("task_id"), str):
                diagnostics.append(diagnostic("SVK-LOCK-SHAPE", "ERROR", "Lock requires a non-empty owner and task_id.", LOCK_FILE))
            expires_at = value.get("expires_at")
            try:
                expires = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                expired = expires <= datetime.now(timezone.utc)
            except (TypeError, ValueError):
                diagnostics.append(diagnostic("SVK-LOCK-EXPIRY", "ERROR", "Lock expires_at must be an ISO-8601 timestamp.", LOCK_FILE))
                expired = False
            code = "SVK-LOCK-EXPIRED" if expired else "SVK-LOCK-PRESENT"
            message = "SVK Next lock has expired; confirm its owner is inactive before clearing it." if expired else "SVK Next lock is present; clear it only after confirming no owner is active."
            diagnostics.append(diagnostic(code, "BLOCKED", message, LOCK_FILE))


def _validate_install_and_manifest(root, diagnostics):
    install = _load(root / INSTALL_FILE, "SVK-INSTALL", diagnostics)
    if install and (install.get("owner") != "smart-vibe-kit" or install.get("version") != VERSION):
        diagnostics.append(diagnostic("SVK-INSTALL-OWNER", "ERROR", "Install record must identify Smart Vibe Kit %s." % VERSION, INSTALL_FILE))
    manifest = _load(root / MANIFEST_FILE, "SVK-MANIFEST", diagnostics)
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, dict) or not files:
        diagnostics.append(diagnostic("SVK-MANIFEST-FILES", "ERROR", "Baseline manifest requires a non-empty files object.", MANIFEST_FILE))
        return
    for relative, digest in files.items():
        candidate = Path(relative) if isinstance(relative, str) else Path(".")
        if not isinstance(relative, str) or not relative or candidate.is_absolute() or ".." in candidate.parts:
            diagnostics.append(diagnostic("SVK-MANIFEST-PATH", "ERROR", "Baseline manifest contains an unsafe path: %r" % relative, MANIFEST_FILE))
        if not isinstance(digest, str) or not re.match(r"^[0-9a-f]{64}$", digest):
            diagnostics.append(diagnostic("SVK-MANIFEST-HASH", "ERROR", "Baseline manifest contains an invalid SHA-256 value for %r." % relative, MANIFEST_FILE))
    if ".svk-stage-owner.json" in files:
        diagnostics.append(diagnostic("SVK-MANIFEST-STAGE-MARKER", "ERROR", "Baseline manifest must not include the temporary staging marker.", MANIFEST_FILE))


def check_project(root):
    root = Path(root).resolve()
    diagnostics = []
    profile = _load(root / PROFILE_FILE, "SVK-PROFILE", diagnostics)
    state = _load(root / STATE_FILE, "SVK-STATE", diagnostics)
    if profile is not None:
        _validate_profile(profile, diagnostics)
        for relative in _required_paths(profile):
            path = root / relative
            if not path.is_file():
                diagnostics.append(diagnostic("SVK-FILE-MISSING", "ERROR", "Required file is missing.", relative))
            elif path.stat().st_size == 0:
                diagnostics.append(diagnostic("SVK-FILE-EMPTY", "ERROR", "Required file is empty.", relative))
    if state is not None:
        _validate_state(state, profile, diagnostics)
    _validate_evidence(root, state, diagnostics)
    _validate_markdown(root, state, diagnostics)
    _validate_transactions(root, diagnostics)
    _validate_install_and_manifest(root, diagnostics)
    return {"result": overall(diagnostics), "diagnostics": diagnostics}


def package_check(bundle_root):
    bundle_root = Path(bundle_root).resolve()
    diagnostics = []
    expected = ("svk-interview", "svk-refresh", "svk-next", "svk-check")
    expected_hosts = {
        "agents", "codex", "cursor", "claude", "gemini", "antigravity", "grok",
        "copilot", "qwen", "kimi", "opencode", "goose", "roo", "junie", "cline",
        "kiro", "windsurf",
    }
    version_path = bundle_root / "VERSION"
    if not version_path.exists() or version_path.read_text(encoding="utf-8").strip() != VERSION:
        diagnostics.append(diagnostic("SVK-PACKAGE-VERSION", "ERROR", "VERSION must be %s." % VERSION, "VERSION"))
    for name in expected:
        root = bundle_root / "skills" / name
        skill_path = root / "SKILL.md"
        yaml_path = root / "agents/openai.yaml"
        entry_path = root / "scripts/entry.py"
        for path in (skill_path, yaml_path, entry_path):
            if not path.is_file() or path.stat().st_size == 0:
                diagnostics.append(diagnostic("SVK-PACKAGE-FILE", "ERROR", "Required skill file is missing or empty.", path.relative_to(bundle_root)))
        if skill_path.exists():
            text = skill_path.read_text(encoding="utf-8")
            if not text.startswith("---\n") and not text.startswith("---\r\n"):
                diagnostics.append(diagnostic("SVK-PACKAGE-FRONTMATTER", "ERROR", "SKILL.md requires YAML frontmatter.", skill_path.relative_to(bundle_root)))
            for required in ("name: %s" % name, 'version: "2.0.0"'):
                if required not in text:
                    diagnostics.append(diagnostic("SVK-PACKAGE-METADATA", "ERROR", "Missing metadata: %s" % required, skill_path.relative_to(bundle_root)))
            for host_only in ("disable-model-invocation:", "disableModelInvocation:"):
                if host_only in text:
                    diagnostics.append(diagnostic("SVK-PACKAGE-HOST-KEY", "ERROR", "Canonical source contains host-only metadata: %s" % host_only, skill_path.relative_to(bundle_root)))
            if PLACEHOLDER_RE.search(text):
                diagnostics.append(diagnostic("SVK-PACKAGE-PLACEHOLDER", "ERROR", "Skill contains unresolved placeholder text.", skill_path.relative_to(bundle_root)))
            if text.count("\n---") < 1:
                diagnostics.append(diagnostic("SVK-PACKAGE-FRONTMATTER-CLOSE", "ERROR", "SKILL.md frontmatter is not closed.", skill_path.relative_to(bundle_root)))
        if yaml_path.exists() and "allow_implicit_invocation: false" not in yaml_path.read_text(encoding="utf-8"):
            diagnostics.append(diagnostic("SVK-PACKAGE-IMPLICIT", "ERROR", "OpenAI metadata must disable implicit invocation.", yaml_path.relative_to(bundle_root)))
    if any(bundle_root.rglob("install.py")) or any(bundle_root.rglob("install.ps1")) or any(bundle_root.rglob("install.sh")):
        diagnostics.append(diagnostic("SVK-PACKAGE-SEPARATION", "ERROR", "Installer files must not be stored inside skill/."))
    compatibility = _load(bundle_root / "compatibility.json", "SVK-COMPATIBILITY", diagnostics)
    if compatibility:
        hosts = compatibility.get("hosts", {})
        if compatibility.get("kit_version") != VERSION:
            diagnostics.append(diagnostic("SVK-COMPATIBILITY-VERSION", "ERROR", "Compatibility metadata version must be %s." % VERSION, "compatibility.json"))
        try:
            date.fromisoformat(compatibility.get("evaluated_on", ""))
        except (TypeError, ValueError):
            diagnostics.append(diagnostic("SVK-COMPATIBILITY-DATE", "ERROR", "evaluated_on must be an ISO date.", "compatibility.json"))
        for required_host in sorted(expected_hosts):
            if required_host not in hosts:
                diagnostics.append(diagnostic("SVK-COMPATIBILITY-HOST", "ERROR", "Compatibility metadata omits %s." % required_host))
        allowed_statuses = {"contract-verified", "contract-compatible-untested", "partial-untested", "shared-standard"}
        allowed_policy_keys = {None, "disable-model-invocation", "disableModelInvocation"}
        for host, details in hosts.items():
            if not isinstance(details, dict):
                diagnostics.append(diagnostic("SVK-COMPATIBILITY-HOST-SHAPE", "ERROR", "Host %s metadata must be an object." % host, "compatibility.json"))
                continue
            for field in ("user_root", "project_root", "invocation"):
                if not isinstance(details.get(field), str) or not details.get(field, "").strip():
                    diagnostics.append(diagnostic("SVK-COMPATIBILITY-FIELD", "ERROR", "Host %s requires %s." % (host, field), "compatibility.json"))
            if details.get("status") not in allowed_statuses:
                diagnostics.append(diagnostic("SVK-COMPATIBILITY-STATUS", "ERROR", "Host %s has an unknown support status." % host, "compatibility.json"))
            if not isinstance(details.get("runtime_tested"), bool):
                diagnostics.append(diagnostic("SVK-COMPATIBILITY-RUNTIME", "ERROR", "Host %s runtime_tested must be boolean." % host, "compatibility.json"))
            if details.get("frontmatter_policy_key") not in allowed_policy_keys:
                diagnostics.append(diagnostic("SVK-COMPATIBILITY-POLICY", "ERROR", "Host %s has an unsupported policy adapter key." % host, "compatibility.json"))
            if host != "agents" and not str(details.get("evidence_url", "")).startswith("https://"):
                diagnostics.append(diagnostic("SVK-COMPATIBILITY-EVIDENCE", "ERROR", "Host %s requires an HTTPS evidence URL." % host, "compatibility.json"))
    for schema_name in ("project-profile.schema.json", "project-state.schema.json"):
        schema = _load(bundle_root / "schemas" / schema_name, "SVK-SCHEMA", diagnostics)
        if schema and (schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or schema.get("additionalProperties") is not False):
            diagnostics.append(diagnostic("SVK-SCHEMA-CONTRACT", "ERROR", "%s must use JSON Schema 2020-12 and reject undeclared top-level properties." % schema_name, "schemas/%s" % schema_name))
    for path in bundle_root.rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as error:
            diagnostics.append(diagnostic("SVK-PACKAGE-PYTHON", "ERROR", str(error), path.relative_to(bundle_root)))
    forbidden_names = {"__pycache__", ".pytest_cache", "node_modules", ".DS_Store"}
    for path in bundle_root.rglob("*"):
        if any(part in forbidden_names for part in path.relative_to(bundle_root).parts):
            diagnostics.append(diagnostic("SVK-PACKAGE-CACHE", "ERROR", "Generated cache or platform metadata is not allowed in the skill bundle.", path.relative_to(bundle_root)))
            break
    return {"result": overall(diagnostics), "diagnostics": diagnostics}


def manifest_matches(root):
    root = Path(root).resolve()
    manifest_path = root / MANIFEST_FILE
    if not manifest_path.exists():
        return False
    manifest = read_json(manifest_path)
    for relative, digest in manifest.get("files", {}).items():
        path = root / relative
        if not path.is_file() or sha256_file(path) != digest:
            return False
    return True
