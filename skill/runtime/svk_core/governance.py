"""Role-aware governed-file registry for SVK 2.1."""

from __future__ import print_function

from pathlib import Path

from .constants import (
    EVIDENCE_INDEX_FILE,
    GOVERNANCE_FILE,
    INSTALL_FILE,
    INTERVIEW_FILE,
    PLAN_FILE,
    PROFILE_FILE,
    SCHEMA_VERSION,
    STATE_FILE,
    VERIFIERS_FILE,
    VERSION,
)
from .util import safe_relative_path, sha256_file, utc_now, write_json


ROLES = (
    "immutable_provenance",
    "generated_projection",
    "mutable_state",
    "append_only_index",
    "user_governed",
    "optional_governed",
)

GENERATED_PROJECTIONS = {
    "AGENTS.md": "agents-v2.1",
    "docs/tasks.md": "tasks-v2.1",
    "docs/adr/0001-project-charter.md": "charter-v2.1",
}


def build_governance(root, document_paths):
    root = Path(root).resolve()
    files = {
        PROFILE_FILE: {"role": "mutable_state"},
        STATE_FILE: {"role": "mutable_state"},
        PLAN_FILE: {"role": "mutable_state"},
        VERIFIERS_FILE: {"role": "mutable_state"},
        GOVERNANCE_FILE: {"role": "mutable_state"},
        INTERVIEW_FILE: {"role": "mutable_state"},
        EVIDENCE_INDEX_FILE: {"role": "append_only_index"},
        INSTALL_FILE: {"role": "immutable_provenance", "sha256": sha256_file(root / INSTALL_FILE)},
    }
    for relative in sorted(document_paths):
        path = safe_relative_path(root, relative, must_exist=True, expect_file=True)
        if relative in GENERATED_PROJECTIONS:
            files[relative] = {"role": "generated_projection", "renderer": GENERATED_PROJECTIONS[relative]}
        else:
            files[relative] = {"role": "user_governed", "baseline_sha256": sha256_file(path)}
    payload = {
        "schema_version": SCHEMA_VERSION,
        "kit_version": VERSION,
        "created_at": utc_now(),
        "files": files,
    }
    write_json(root / GOVERNANCE_FILE, payload)
    return payload


def validate_governance_shape(value):
    if not isinstance(value, dict):
        raise ValueError("Governance registry must be an object.")
    if set(value) != {"schema_version", "kit_version", "created_at", "files"}:
        raise ValueError("Governance registry has missing or unknown fields.")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("kit_version") != VERSION:
        raise ValueError("Governance registry must use SVK %s." % VERSION)
    files = value.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("Governance registry files must be a non-empty object.")
    for relative, policy in files.items():
        if not isinstance(relative, str) or not relative.strip():
            raise ValueError("Governance paths must be non-empty strings.")
        candidate = Path(relative)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("Unsafe governance path: %s" % relative)
        if not isinstance(policy, dict) or policy.get("role") not in ROLES:
            raise ValueError("Governance entry %s has an invalid role." % relative)
        role = policy["role"]
        allowed = {"role"}
        if role == "immutable_provenance":
            allowed.add("sha256")
            if not isinstance(policy.get("sha256"), str) or len(policy["sha256"]) != 64:
                raise ValueError("Immutable governance entry %s requires sha256." % relative)
        elif role == "generated_projection":
            allowed.add("renderer")
            if not isinstance(policy.get("renderer"), str) or not policy["renderer"].strip():
                raise ValueError("Generated entry %s requires a renderer." % relative)
        elif role in ("user_governed", "optional_governed"):
            allowed.add("baseline_sha256")
            digest = policy.get("baseline_sha256")
            if digest is not None and (not isinstance(digest, str) or len(digest) != 64):
                raise ValueError("Governed entry %s has invalid baseline_sha256." % relative)
        if set(policy) - allowed:
            raise ValueError("Governance entry %s has unknown fields." % relative)
    return True
