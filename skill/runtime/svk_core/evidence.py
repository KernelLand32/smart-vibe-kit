"""SVK-executed verifiers and immutable receipt storage."""

from __future__ import print_function

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from .constants import EVIDENCE_INDEX_FILE, EVIDENCE_RUNS_DIR, SCHEMA_VERSION, VERSION
from .util import (
    atomic_write,
    read_json,
    safe_relative_path,
    sha256_file,
    snapshot_fingerprint,
    utc_now,
    write_json,
)


OUTPUT_LIMIT = 1024 * 1024
SAFE_ENVIRONMENT = (
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
    "HOME", "USERPROFILE", "LANG", "LC_ALL", "TERM", "PYTHONIOENCODING",
)


def initial_index(profile, charter_accepted=False):
    records = [
        {
            "id": "attestation-interview",
            "kind": "attestation",
            "task_id": "1.1.1",
            "result": "recorded",
            "summary": "Project interview, adaptive profile, and approved structured plan were recorded.",
            "actor": "svk-interview",
            "recorded_at": utc_now(),
            "artifacts": [".svk/project.json", ".svk/plan.json"],
        }
    ]
    if charter_accepted:
        records.append(
            {
                "id": "attestation-charter",
                "kind": "attestation",
                "task_id": "1.1.2",
                "result": "recorded",
                "summary": "The caller recorded that a human accepted the charter during Interview.",
                "actor": "interview-human-attestation",
                "recorded_at": utc_now(),
                "artifacts": ["docs/adr/0001-project-charter.md"],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "kit_version": VERSION,
        "project": profile["slug"],
        "records": records,
    }


def add_attestation(root, task_id, actor, summary, artifacts):
    index_path = Path(root) / EVIDENCE_INDEX_FILE
    index = read_json(index_path)
    record = {
        "id": "attestation-%s" % uuid.uuid4().hex,
        "kind": "attestation",
        "task_id": task_id,
        "result": "recorded",
        "summary": summary,
        "actor": actor,
        "recorded_at": utc_now(),
        "artifacts": list(artifacts),
    }
    index["records"].append(record)
    write_json(index_path, index)
    return record


def _hash_stream(path):
    digest = hashlib.sha256()
    total = 0
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            total += len(block)
    return digest.hexdigest(), total


def _truncate_log(path, limit=OUTPUT_LIMIT):
    path = Path(path)
    digest, total = _hash_stream(path)
    with path.open("rb") as handle:
        kept = handle.read(limit)
    truncated = total > len(kept)
    if truncated:
        kept += b"\n[SVK output truncated; full-stream digest and byte count are in receipt.json]\n"
    with path.open("wb") as handle:
        handle.write(kept)
        handle.flush()
        os.fsync(handle.fileno())
    return {"sha256": digest, "bytes": total, "truncated": truncated}


def _safe_environment(definition):
    configured = definition.get("environment", {"inherit": "safe-defaults", "set": {}})
    result = {}
    if configured.get("inherit", "safe-defaults") == "safe-defaults":
        for name in SAFE_ENVIRONMENT:
            if name in os.environ:
                result[name] = os.environ[name]
    for name, value in configured.get("set", {}).items():
        if any(token in name.upper() for token in ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "PRIVATE_KEY")):
            raise ValueError("Verifier environment may not persist secret-like variables: %s" % name)
        result[name] = value
    return result


def _resolved_executable(argv, cwd, environment):
    command = argv[0]
    if any(separator in command for separator in ("/", "\\")):
        candidate = Path(command)
        if not candidate.is_absolute():
            candidate = Path(cwd) / candidate
        return str(candidate.resolve())
    return shutil.which(command, path=environment.get("PATH")) or command


def _terminate_process_tree(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _run_command(definition, cwd, stdout_path, stderr_path):
    environment = _safe_environment(definition)
    configured_argv = list(definition["argv"])
    argv = list(configured_argv)
    portable_python = argv[0] == "{python}"
    if portable_python:
        argv[0] = sys.executable
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    with Path(stdout_path).open("wb") as stdout_handle, Path(stderr_path).open("wb") as stderr_handle:
        started_at = utc_now()
        process = subprocess.Popen(
            argv,
            cwd=str(cwd),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            shell=False,
            start_new_session=(os.name != "nt"),
            creationflags=creationflags,
        )
        timed_out = False
        try:
            return_code = process.wait(timeout=definition["timeout_seconds"])
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_process_tree(process)
            return_code = process.returncode
        finished_at = utc_now()
    return {
        "started_at": started_at,
        "finished_at": finished_at,
        "exit_code": return_code,
        "timed_out": timed_out,
        "resolved_executable": (
            "python:%d.%d.%d:%s" % (sys.version_info[0], sys.version_info[1], sys.version_info[2], sys.implementation.name)
            if portable_python else _resolved_executable(argv, cwd, environment)
        ),
        "argv": configured_argv,
    }


def _artifact_descriptors(root, paths):
    descriptors = []
    missing = []
    for relative in sorted(set(paths)):
        path = safe_relative_path(root, relative, must_exist=False)
        if not path.exists():
            missing.append(relative)
            continue
        if path.is_file():
            descriptors.append({"path": relative, "kind": "file", "sha256": sha256_file(path)})
        elif path.is_dir():
            fingerprint = snapshot_fingerprint(root, [relative], excludes=(".svk/evidence", ".svk/locks", ".svk/transactions"))
            descriptors.append({"path": relative, "kind": "directory", "sha256": fingerprint["sha256"]})
        else:
            missing.append(relative)
    return descriptors, missing


def _input_paths(task):
    values = list(task.get("scope_hints", [])) + list(task.get("expected_artifacts", []))
    return list(dict.fromkeys(values))


def receipt_fresh(root, task, receipt):
    current = snapshot_fingerprint(
        root,
        _input_paths(task),
        excludes=(".svk/evidence", ".svk/locks", ".svk/transactions"),
    )
    recorded = receipt.get("inputs_after", {})
    if current.get("sha256") != recorded.get("sha256"):
        return False
    if receipt.get("missing_artifacts"):
        return False
    recorded_artifacts = receipt.get("artifacts")
    if not isinstance(recorded_artifacts, list):
        return False
    artifact_paths = [item.get("path") for item in recorded_artifacts if isinstance(item, dict)]
    if len(artifact_paths) != len(recorded_artifacts) or any(not isinstance(path, str) for path in artifact_paths):
        return False
    current_artifacts, missing = _artifact_descriptors(root, artifact_paths)
    return not missing and current_artifacts == recorded_artifacts


def run_verifier(root, task, verifier_id, definition, owner):
    root = Path(root).resolve()
    run_id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    evidence_root = root / ".svk" / "evidence"
    stage = evidence_root / (".stage-%s" % run_id)
    final = root / EVIDENCE_RUNS_DIR / run_id
    stage.mkdir(parents=True, exist_ok=False)
    stdout_path = stage / "stdout.log"
    stderr_path = stage / "stderr.log"
    inputs_before = snapshot_fingerprint(
        root,
        _input_paths(task),
        excludes=(".svk/evidence", ".svk/locks", ".svk/transactions"),
    )
    try:
        if definition["kind"] == "builtin":
            from .verify import check_project

            checked = check_project(root)
            failed = [item for item in checked["diagnostics"] if item["level"] == "ERROR"]
            atomic_write(stdout_path, json.dumps({"result": checked["result"], "diagnostics": checked["diagnostics"]}, indent=2, sort_keys=True) + "\n")
            atomic_write(stderr_path, "")
            process = {
                "started_at": utc_now(),
                "finished_at": utc_now(),
                "exit_code": 1 if failed else 0,
                "timed_out": False,
                "resolved_executable": "svk:builtin:governed",
            }
            argv = ["svk", "check", "--scope", "governed"]
            cwd_relative = "."
            expected_exit_codes = [0]
            configured_artifacts = []
        else:
            cwd_relative = definition.get("cwd", ".")
            cwd = safe_relative_path(root, cwd_relative, must_exist=True)
            if not cwd.is_dir():
                raise ValueError("Verifier cwd is not a directory: %s" % cwd_relative)
            process = _run_command(definition, cwd, stdout_path, stderr_path)
            argv = process["argv"]
            expected_exit_codes = definition["expected_exit_codes"]
            configured_artifacts = definition.get("artifacts", [])
        stdout_info = _truncate_log(stdout_path)
        stderr_info = _truncate_log(stderr_path)
        inputs_after = snapshot_fingerprint(
            root,
            _input_paths(task),
            excludes=(".svk/evidence", ".svk/locks", ".svk/transactions"),
        )
        artifact_paths = list(dict.fromkeys(configured_artifacts + task.get("expected_artifacts", [])))
        artifacts, missing = _artifact_descriptors(root, artifact_paths)
        input_changed = inputs_before["sha256"] != inputs_after["sha256"]
        passed = (
            not process["timed_out"]
            and process["exit_code"] in expected_exit_codes
            and not missing
            and not input_changed
        )
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "kit_version": VERSION,
            "run_id": run_id,
            "task_id": task["id"],
            "verifier_id": verifier_id,
            "owner": owner,
            "started_at": process["started_at"],
            "finished_at": process["finished_at"],
            "cwd": cwd_relative,
            "argv": argv,
            "resolved_executable": process["resolved_executable"],
            "exit_code": process["exit_code"],
            "timed_out": process["timed_out"],
            "expected_exit_codes": expected_exit_codes,
            "stdout": stdout_info,
            "stderr": stderr_info,
            "inputs_before": inputs_before,
            "inputs_after": inputs_after,
            "input_changed_during_run": input_changed,
            "artifacts": artifacts,
            "missing_artifacts": missing,
            "result": "pass" if passed else "fail",
        }
        write_json(stage / "receipt.json", receipt)
        receipt_digest = sha256_file(stage / "receipt.json")
        final.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(stage), str(final))
        index_path = root / EVIDENCE_INDEX_FILE
        index = read_json(index_path)
        index["records"].append(
            {
                "id": run_id,
                "kind": "verification",
                "task_id": task["id"],
                "verifier_id": verifier_id,
                "result": receipt["result"],
                "recorded_at": receipt["finished_at"],
                "path": "%s/%s/receipt.json" % (EVIDENCE_RUNS_DIR, run_id),
                "receipt_sha256": receipt_digest,
            }
        )
        write_json(index_path, index)
        return receipt
    finally:
        if stage.exists():
            shutil.rmtree(str(stage))


def load_receipt(root, run_id):
    if not isinstance(run_id, str) or not run_id or any(character not in "0123456789abcdef" for character in run_id):
        raise ValueError("Receipt IDs must be lowercase hexadecimal strings.")
    root = Path(root).resolve()
    expected_relative = "%s/%s/receipt.json" % (EVIDENCE_RUNS_DIR, run_id)
    index = read_json(root / EVIDENCE_INDEX_FILE)
    records = [
        item for item in index.get("records", [])
        if isinstance(item, dict) and item.get("kind") == "verification" and item.get("id") == run_id
    ]
    if len(records) != 1:
        raise ValueError("Receipt %s must have exactly one evidence-index record." % run_id)
    record = records[0]
    if record.get("path") != expected_relative:
        raise ValueError("Receipt %s has a non-canonical evidence path." % run_id)
    receipt_path = safe_relative_path(root, expected_relative, must_exist=True, expect_file=True)
    digest = record.get("receipt_sha256")
    if not isinstance(digest, str) or digest != sha256_file(receipt_path):
        raise ValueError("Receipt %s failed its immutable digest check." % run_id)
    receipt = read_json(receipt_path)
    if (
        receipt.get("run_id") != run_id
        or record.get("task_id") != receipt.get("task_id")
        or record.get("verifier_id") != receipt.get("verifier_id")
        or record.get("result") != receipt.get("result")
    ):
        raise ValueError("Receipt %s does not match its evidence-index subject or result." % run_id)
    return receipt
