"""Command-line interface shared by installed skill wrappers."""

from __future__ import print_function

import argparse
import json
import sys
from pathlib import Path

from .operations import (
    interview_questions,
    next_begin,
    next_block,
    next_clear_lock,
    next_finish,
    next_show,
    refresh,
    scaffold,
)
from .verify import check_project, package_check


def _emit(value, as_json=True):
    if as_json:
        print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(value)


def _answers(path):
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_parser():
    parser = argparse.ArgumentParser(prog="svk", description="Smart Vibe Kit 2.0 deterministic runtime")
    parser.add_argument("--version", action="version", version="2.0.0")
    actions = parser.add_subparsers(dest="action", required=True)

    interview = actions.add_parser("interview", help="Create an adaptive project scaffold")
    interview.add_argument("--root", default=".")
    interview.add_argument("--answers")
    interview.add_argument("--questions", action="store_true")
    interview.add_argument("--charter-accepted", action="store_true")

    refresh_parser = actions.add_parser("refresh", help="Read and summarize project state without writing")
    refresh_parser.add_argument("--root", default=".")

    check = actions.add_parser("check", help="Run semantic project verification")
    check.add_argument("--root", default=".")
    check.add_argument("--package", action="store_true", dest="package_mode")

    next_parser = actions.add_parser("next", help="Show or advance exactly one task")
    next_parser.add_argument("--root", default=".")
    next_actions = next_parser.add_subparsers(dest="next_action", required=True)
    next_actions.add_parser("show")
    begin = next_actions.add_parser("begin")
    begin.add_argument("--owner", required=True)
    begin.add_argument("--allow-human-gate", action="store_true")
    begin.add_argument("--ttl-minutes", type=int, default=120)
    finish = next_actions.add_parser("finish")
    finish.add_argument("--owner", required=True)
    finish.add_argument("--task", required=True)
    finish.add_argument("--evidence", required=True)
    block = next_actions.add_parser("block")
    block.add_argument("--owner", required=True)
    block.add_argument("--task", required=True)
    block.add_argument("--reason", required=True)
    clear = next_actions.add_parser("clear-lock")
    clear.add_argument("--owner")
    clear.add_argument("--force", action="store_true")
    return parser


def run(arguments=None):
    parser = build_parser()
    args = parser.parse_args(arguments)
    try:
        if args.action == "interview":
            if args.questions:
                _emit({"questions": interview_questions()})
                return 0
            if not args.answers:
                parser.error("interview requires --answers <json> or --questions")
            value = scaffold(args.root, _answers(args.answers), charter_accepted=args.charter_accepted)
        elif args.action == "refresh":
            value = refresh(args.root)
        elif args.action == "check":
            value = package_check(args.root) if args.package_mode else check_project(args.root)
        elif args.action == "next" and args.next_action == "show":
            value = next_show(args.root)
        elif args.action == "next" and args.next_action == "begin":
            value = next_begin(args.root, args.owner, args.allow_human_gate, args.ttl_minutes)
        elif args.action == "next" and args.next_action == "finish":
            value = next_finish(args.root, args.owner, args.task, args.evidence)
        elif args.action == "next" and args.next_action == "block":
            value = next_block(args.root, args.owner, args.task, args.reason)
        elif args.action == "next" and args.next_action == "clear-lock":
            value = next_clear_lock(args.root, args.owner, args.force)
        else:
            parser.error("Unsupported action")
        _emit(value)
        if isinstance(value, dict) and value.get("result") in ("ERROR", "BLOCKED"):
            return 2
        return 0
    except (FileNotFoundError, FileExistsError, PermissionError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print("SVK error: %s" % error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
