"""Stable JSON command-line contract shared by every installed SVK skill."""

from __future__ import print_function

import argparse
import json
import sys
from pathlib import Path

from .constants import SCHEMA_VERSION, VERSION
from .interview import session_abandon, session_checkpoint, session_show, session_start
from .operations import (
    interview_questions, next_begin, next_block, next_clear_lock, next_finish,
    next_show, refresh, scaffold, verify_task,
)
from .recovery import clear_expired_lease, index_orphan_receipts, inspect_recovery, rollback_incomplete_transactions
from .planning import apply_plan_edit
from .migration import apply_migration, inspect_migration, plan_migration, rollback_migration
from .verify import check_project, package_check


EXIT_SUCCESS = 0
EXIT_BLOCKED = 3
EXIT_CONTRACT = 4
EXIT_IO = 5
EXIT_INTERNAL = 10


class ContractArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def _emit(value):
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def _json_file(path):
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _csv(value):
    if value is None or not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _error(error, category, code, command):
    result = {
        "contract": "contract_error",
        "io-or-ownership": "io_error",
        "internal": "internal_error",
    }[category]
    _emit({
        "schema_version": SCHEMA_VERSION,
        "kit_version": VERSION,
        "ok": False,
        "command": command,
        "result": result,
        "diagnostics": [{
            "code": "SVK-CLI-%s" % category.upper().replace("-", "_"),
            "category": category,
            "severity": "error",
            "message": str(error),
        }],
        "error": {"category": category, "type": type(error).__name__, "message": str(error)},
    })
    return code


def build_parser():
    parser = ContractArgumentParser(prog="svk", description="Smart Vibe Kit 2.1 deterministic runtime")
    parser.add_argument("--version", action="version", version=VERSION)
    actions = parser.add_subparsers(dest="action", required=True)

    interview = actions.add_parser("interview", help="Checkpoint or scaffold a greenfield project")
    interview.add_argument("--root", default=".")
    interview_actions = interview.add_subparsers(dest="interview_action", required=True)
    interview_actions.add_parser("questions")
    start = interview_actions.add_parser("start")
    start.add_argument("--idea", required=True)
    interview_actions.add_parser("show")
    checkpoint = interview_actions.add_parser("checkpoint")
    checkpoint.add_argument("--section", required=True)
    checkpoint.add_argument("--answers", required=True)
    checkpoint.add_argument("--unresolved")
    checkpoint.add_argument("--proposal-sha256")
    abandon = interview_actions.add_parser("abandon")
    abandon.add_argument("--reason", required=True)
    create = interview_actions.add_parser("scaffold")
    create.add_argument("--answers", required=True)
    create.add_argument("--charter-accepted", action="store_true")

    refresh_parser = actions.add_parser("refresh", help="Read and summarize project state without writing")
    refresh_parser.add_argument("--root", default=".")
    refresh_parser.add_argument("--scope", choices=("governed", "all-docs"), default="governed")

    check = actions.add_parser("check", help="Run deterministic project verification")
    check.add_argument("--root", default=".")
    check.add_argument("--package", action="store_true", dest="package_mode")
    check.add_argument("--scope", choices=("governed", "all-docs"), default="governed")

    next_parser = actions.add_parser("next", help="Show, lease, verify, or advance exactly one task")
    next_parser.add_argument("--root", default=".")
    next_actions = next_parser.add_subparsers(dest="next_action", required=True)
    next_actions.add_parser("show")
    begin = next_actions.add_parser("begin")
    begin.add_argument("--owner", required=True)
    begin.add_argument("--allow-human-gate", action="store_true")
    begin.add_argument("--human-actor")
    begin.add_argument("--human-reason")
    begin.add_argument("--ttl-minutes", type=int, default=120)
    verify = next_actions.add_parser("verify")
    verify.add_argument("--owner", required=True)
    verify.add_argument("--task", required=True)
    verify.add_argument("--verifier", required=True)
    finish = next_actions.add_parser("finish")
    finish.add_argument("--owner", required=True)
    finish.add_argument("--task", required=True)
    finish.add_argument("--receipts", required=True, help="Comma-separated SVK receipt IDs")
    finish.add_argument("--note")
    block = next_actions.add_parser("block")
    block.add_argument("--owner", required=True)
    block.add_argument("--task", required=True)
    block.add_argument("--reason", required=True)
    clear = next_actions.add_parser("clear-lock")
    clear.add_argument("--owner")
    clear.add_argument("--force", action="store_true")

    recover = actions.add_parser("recover", help="Inspect or explicitly recover interrupted durable state")
    recover.add_argument("--root", default=".")
    recover_actions = recover.add_subparsers(dest="recover_action", required=True)
    recover_actions.add_parser("inspect")
    for name in ("index-orphans", "rollback-transactions", "clear-expired-lease"):
        item = recover_actions.add_parser(name)
        item.add_argument("--approve", action="store_true")

    plan = actions.add_parser("plan", help="Apply one approved, bounded pending-plan edit")
    plan.add_argument("--root", default=".")
    plan.add_argument("--owner", required=True)
    plan.add_argument("--edit", required=True, help="JSON file containing one narrow plan edit")
    plan.add_argument("--reviewer", required=True)
    plan.add_argument("--reason", required=True)
    plan.add_argument("--approve", action="store_true")

    migrate = actions.add_parser("migrate", help="Inspect, plan, apply, or roll back the deterministic 2.0 to 2.1 migration")
    migrate.add_argument("--root", default=".")
    migrate_actions = migrate.add_subparsers(dest="migrate_action", required=True)
    migrate_actions.add_parser("inspect")
    migrate_actions.add_parser("plan")
    apply = migrate_actions.add_parser("apply")
    apply.add_argument("--approve", action="store_true")
    rollback = migrate_actions.add_parser("rollback")
    rollback.add_argument("--backup", required=True)
    rollback.add_argument("--approve", action="store_true")
    return parser


def _raw_command(arguments):
    values = list(sys.argv[1:] if arguments is None else arguments)
    actions = {"interview", "refresh", "check", "next", "recover", "plan", "migrate"}
    action = next((item for item in values if item in actions), None)
    if action is None:
        return "unknown"
    index = values.index(action)
    if action in ("interview", "next", "recover", "migrate") and index + 1 < len(values) and not values[index + 1].startswith("-"):
        return "%s.%s" % (action, values[index + 1])
    return action


def _parsed_command(args):
    for attribute in ("interview_action", "next_action", "recover_action", "migrate_action"):
        value = getattr(args, attribute, None)
        if value:
            return "%s.%s" % (args.action, value)
    return args.action


def run(arguments=None):
    parser = build_parser()
    command = _raw_command(arguments)
    try:
        args = parser.parse_args(arguments)
        command = _parsed_command(args)
        if args.action == "interview":
            if args.interview_action == "questions":
                value = {"questions": interview_questions()}
            elif args.interview_action == "start":
                value = session_start(args.root, args.idea)
            elif args.interview_action == "show":
                value = session_show(args.root)
            elif args.interview_action == "checkpoint":
                value = session_checkpoint(args.root, args.section, _json_file(args.answers), _csv(args.unresolved), args.proposal_sha256)
            elif args.interview_action == "abandon":
                value = session_abandon(args.root, args.reason)
            else:
                value = scaffold(args.root, _json_file(args.answers), charter_accepted=args.charter_accepted)
        elif args.action == "refresh":
            value = refresh(args.root, scope=args.scope)
        elif args.action == "check":
            value = package_check(args.root) if args.package_mode else check_project(args.root, scope=args.scope)
        elif args.action == "migrate":
            if args.migrate_action == "inspect":
                value = inspect_migration(args.root)
            elif args.migrate_action == "plan":
                value = plan_migration(args.root)
            elif args.migrate_action == "apply":
                value = apply_migration(args.root, args.approve)
            else:
                value = rollback_migration(args.root, args.backup, args.approve)
        elif args.action == "plan":
            value = apply_plan_edit(args.root, args.owner, _json_file(args.edit), args.reviewer, args.reason, args.approve)
        elif args.action == "recover":
            if args.recover_action == "inspect":
                value = inspect_recovery(args.root)
            elif args.recover_action == "index-orphans":
                value = index_orphan_receipts(args.root, args.approve)
            elif args.recover_action == "rollback-transactions":
                value = rollback_incomplete_transactions(args.root, args.approve)
            else:
                value = clear_expired_lease(args.root, args.approve)
        elif args.next_action == "show":
            value = next_show(args.root)
        elif args.next_action == "begin":
            value = next_begin(args.root, args.owner, args.allow_human_gate, args.ttl_minutes, args.human_actor, args.human_reason)
        elif args.next_action == "verify":
            value = verify_task(args.root, args.owner, args.task, args.verifier)
        elif args.next_action == "finish":
            value = next_finish(args.root, args.owner, args.task, _csv(args.receipts), args.note)
        elif args.next_action == "block":
            value = next_block(args.root, args.owner, args.task, args.reason)
        else:
            value = next_clear_lock(args.root, args.owner, args.force)
        logical_result = "success"
        if isinstance(value, dict) and value.get("result") == "BLOCKED":
            logical_result = "blocked"
        elif isinstance(value, dict) and value.get("result") == "ERROR":
            logical_result = "contract_error"
        _emit({
            "schema_version": SCHEMA_VERSION,
            "kit_version": VERSION,
            "ok": True,
            "command": command,
            "result": logical_result,
            "diagnostics": value.get("diagnostics", []) if isinstance(value, dict) else [],
            "value": value,
        })
        if logical_result == "blocked":
            return EXIT_BLOCKED
        if logical_result == "contract_error":
            return EXIT_CONTRACT
        return EXIT_SUCCESS
    except (FileNotFoundError, FileExistsError, NotADirectoryError, PermissionError, OSError) as error:
        return _error(error, "io-or-ownership", EXIT_IO, command)
    except (ValueError, RuntimeError, json.JSONDecodeError) as error:
        return _error(error, "contract", EXIT_CONTRACT, command)
    except Exception as error:  # pragma: no cover
        return _error(error, "internal", EXIT_INTERNAL, command)


if __name__ == "__main__":
    raise SystemExit(run())
