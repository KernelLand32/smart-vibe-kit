#!/usr/bin/env python3
"""Pocket List's first implemented increment: add and persist a task."""

from __future__ import print_function

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


DEFAULT_DATA = ".pocket-list.json"


class DataError(ValueError):
    """Raised when the stored task data is not safe to use."""


def load_tasks(path):
    path = Path(path)
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise DataError("Data file is not valid JSON: %s" % error)
    if not isinstance(value, list):
        raise DataError("Data file must contain a JSON array.")
    for task in value:
        if (
            not isinstance(task, dict)
            or isinstance(task.get("id"), bool)
            or not isinstance(task.get("id"), int)
            or task.get("id") < 1
            or not isinstance(task.get("text"), str)
            or not isinstance(task.get("done"), bool)
        ):
            raise DataError("Data file contains an invalid task record.")
    if len({task["id"] for task in value}) != len(value):
        raise DataError("Data file contains duplicate task IDs.")
    return value


def save_tasks(path, tasks):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".%s." % path.name, suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(tasks, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, str(path))
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def add_task(path, text):
    text = text.strip()
    if not text:
        raise ValueError("Task text is required.")
    tasks = load_tasks(path)
    task_id = max((task["id"] for task in tasks), default=0) + 1
    task = {"id": task_id, "text": text, "done": False}
    tasks.append(task)
    save_tasks(path, tasks)
    return task


def build_parser():
    parser = argparse.ArgumentParser(description="A small offline task list")
    parser.add_argument("--data", default=DEFAULT_DATA, help="Local JSON data file")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="Add one unfinished task")
    add.add_argument("text")
    return parser


def main(arguments=None):
    args = build_parser().parse_args(arguments)
    try:
        if args.command == "add":
            task = add_task(args.data, args.text)
            print("Added %d: %s" % (task["id"], task["text"]))
            return 0
        raise ValueError("Unsupported command: %s" % args.command)
    except (DataError, OSError, ValueError) as error:
        print("Pocket List error: %s" % error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
