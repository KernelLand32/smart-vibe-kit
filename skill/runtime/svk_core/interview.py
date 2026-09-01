"""Durable, resumable Interview checkpoints stored outside greenfield targets."""

from __future__ import print_function

import re
import uuid
from pathlib import Path

from .constants import SCHEMA_VERSION, VERSION
from .util import parse_utc, read_json, safe_project_root, utc_now, write_json


SECTIONS = ("project", "users", "scope", "constraints", "risk", "plan", "review")
SESSION_REQUIRED_FIELDS = {
    "schema_version", "kit_version", "session_id", "target", "idea", "status",
    "sections", "unresolved_questions", "proposal_sha256", "created_at", "updated_at",
}


def validate_session(value):
    if not isinstance(value, dict):
        raise ValueError("Interview session must be a JSON object.")
    unknown = set(value) - SESSION_REQUIRED_FIELDS - {"abandon_reason"}
    missing = SESSION_REQUIRED_FIELDS - set(value)
    if missing or unknown:
        raise ValueError("Interview session fields are invalid; missing=%s unknown=%s" % (sorted(missing), sorted(unknown)))
    if value.get("schema_version") != SCHEMA_VERSION or value.get("kit_version") != VERSION:
        raise ValueError("Interview session is not an SVK %s session." % VERSION)
    if not re.match(r"^[0-9a-f]{32}$", str(value.get("session_id", ""))):
        raise ValueError("Interview session_id must be 32 lowercase hexadecimal characters.")
    if not isinstance(value.get("target"), str) or not value["target"].strip() or not isinstance(value.get("idea"), str) or not value["idea"].strip():
        raise ValueError("Interview target and idea must be non-empty strings.")
    if value.get("status") not in ("collecting", "proposal-ready", "scaffolded", "abandoned"):
        raise ValueError("Interview session has an invalid status.")
    sections = value.get("sections")
    if not isinstance(sections, dict) or set(sections) - set(SECTIONS) or any(not isinstance(item, dict) for item in sections.values()):
        raise ValueError("Interview sections have an invalid shape.")
    unresolved = value.get("unresolved_questions")
    if not isinstance(unresolved, list) or any(not isinstance(item, str) or not item.strip() for item in unresolved):
        raise ValueError("Interview unresolved_questions must contain non-empty strings.")
    proposal = value.get("proposal_sha256")
    if proposal is not None and not re.match(r"^[0-9a-f]{64}$", str(proposal)):
        raise ValueError("Interview proposal_sha256 must be null or a lowercase SHA-256 digest.")
    parse_utc(value.get("created_at")); parse_utc(value.get("updated_at"))
    reason = value.get("abandon_reason")
    if value["status"] == "abandoned":
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("An abandoned Interview session requires abandon_reason.")
    elif reason is not None:
        raise ValueError("abandon_reason is valid only for an abandoned Interview session.")
    return True


def session_path(project_root):
    root = safe_project_root(project_root)
    return root.parent / (".%s.svk-interview.json" % root.name)


def session_start(project_root, idea):
    root = safe_project_root(project_root)
    if not isinstance(idea, str) or not idea.strip():
        raise ValueError("Interview session requires a non-empty project idea.")
    path = session_path(root)
    if path.exists():
        raise FileExistsError("Interview session already exists: %s" % path)
    value = {
        "schema_version": SCHEMA_VERSION,
        "kit_version": VERSION,
        "session_id": uuid.uuid4().hex,
        "target": root.name,
        "idea": idea.strip(),
        "status": "collecting",
        "sections": {},
        "unresolved_questions": [],
        "proposal_sha256": None,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    write_json(path, value)
    return {"status": "started", "session_path": str(path), "session": value}


def _load_owned_session(project_root):
    root = safe_project_root(project_root)
    path = session_path(root)
    value = read_json(path)
    validate_session(value)
    if value.get("target") != root.name:
        raise ValueError("Interview session target does not match the requested project.")
    if value.get("status") not in ("collecting", "proposal-ready", "abandoned"):
        raise ValueError("Interview session has an invalid status.")
    return path, value


def session_show(project_root):
    path, value = _load_owned_session(project_root)
    return {"status": value["status"], "session_path": str(path), "session": value}


def session_checkpoint(project_root, section, answers, unresolved_questions=None, proposal_sha256=None):
    if section not in SECTIONS:
        raise ValueError("Unknown Interview section: %s" % section)
    if not isinstance(answers, dict):
        raise ValueError("Interview checkpoint answers must be a JSON object.")
    unresolved = unresolved_questions if unresolved_questions is not None else []
    if not isinstance(unresolved, list) or any(not isinstance(item, str) or not item.strip() for item in unresolved):
        raise ValueError("unresolved_questions must be an array of non-empty strings.")
    path, value = _load_owned_session(project_root)
    if value["status"] == "abandoned":
        raise ValueError("An abandoned Interview session cannot be checkpointed.")
    value["sections"][section] = answers
    value["unresolved_questions"] = [item.strip() for item in unresolved]
    if proposal_sha256 is not None:
        if not isinstance(proposal_sha256, str) or len(proposal_sha256) != 64:
            raise ValueError("proposal_sha256 must be a 64-character digest.")
        value["proposal_sha256"] = proposal_sha256
    value["status"] = "proposal-ready" if section == "review" and not unresolved else "collecting"
    value["updated_at"] = utc_now()
    write_json(path, value)
    return {"status": "checkpointed", "section": section, "session_path": str(path), "session": value}


def session_abandon(project_root, reason):
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Abandoning an Interview requires a reason.")
    path, value = _load_owned_session(project_root)
    value["status"] = "abandoned"
    value["abandon_reason"] = reason.strip()
    value["updated_at"] = utc_now()
    write_json(path, value)
    return {"status": "abandoned", "session_path": str(path), "session": value}


def final_session(project_root, answers):
    root = safe_project_root(project_root)
    path = session_path(root)
    if path.exists():
        _, value = _load_owned_session(root)
        if value["status"] == "abandoned":
            raise ValueError("Cannot scaffold from an abandoned Interview session.")
    else:
        value = {
            "schema_version": SCHEMA_VERSION,
            "kit_version": VERSION,
            "session_id": uuid.uuid4().hex,
            "target": root.name,
            "idea": str(answers.get("idea", "")).strip(),
            "status": "proposal-ready",
            "sections": {"review": {"final_answers_recorded": True}},
            "unresolved_questions": [],
            "proposal_sha256": None,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
    value["status"] = "scaffolded"
    value["updated_at"] = utc_now()
    return value
