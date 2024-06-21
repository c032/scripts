#!/usr/bin/env python

from typing import (
    Generator,
    Optional,
)

import json
import os
import subprocess
import sys
import time


HERE = os.path.dirname(os.path.abspath(__file__))

# File where update timestamps will be stored.
STATUS_FILE = os.path.join(HERE, "status.json")

# Skip updating repositories that were updated less than
# `UPDATE_INTERVAL_IN_SECONDS` seconds ago.
UPDATE_INTERVAL_IN_SECONDS = 8 * 60 * 60

# How many seconds to wait between one `git remote update` and the next.
DELAY_BETWEEN_REPOSITORY_UPDATES_IN_SECONDS = 2


def sh(
    cmd: str, args: Optional[list[str]] = None, working_directory: Optional[str] = None
) -> None:
    if not isinstance(cmd, str):
        raise TypeError("`cmd` must be str")
    if args is not None:
        if not isinstance(args, list):
            raise TypeError("`args` must be list")
        for arg in args:
            if not isinstance(arg, str):
                raise TypeError("`args` must contain only values of type str")

    if working_directory is None:
        raise ValueError("`working_directory` is required")
    if not isinstance(working_directory, str):
        raise TypeError("`working_directory` must be str")
    if not os.path.isabs(working_directory):
        raise ValueError("`working_directory` must be an absolute path")

    if args is None:
        args = []

    subprocess.run(
        [cmd, *args],
        check=True,
        cwd=working_directory,
    )

    return None


def get_repositories() -> Generator[str, None, None]:
    search_directories = [HERE]
    for search_directory in search_directories:
        for root, dirs, files in os.walk(search_directory):
            dirs.sort()

            if not root.endswith(".git"):
                continue

            while len(dirs) > 0:
                dirs.pop()

            yield root


def get_human_duration(total_seconds: int) -> str:
    t = total_seconds

    output = ""

    if t > 3600:
        hours, t = divmod(t, 3600)
        output += "{}h".format(hours)

    if t > 60:
        minutes, t = divmod(t, 60)
        output += "{}m".format(minutes)
    elif output != "":
        output += "0m"

    seconds = t
    output += "{}s".format(seconds)

    return output


def main() -> int:
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status = json.loads(f.read())
    except FileNotFoundError:
        status = {}

    now = time.gmtime()

    print("===> Started {}".format(time.strftime("%Y-%m-%d %H:%M:%S %z", now)))

    started = int(time.mktime(now))

    try:
        is_first_iteration = True
        for repository_path in get_repositories():
            if repository_path in status:
                last_updated = status[repository_path]
                if started - last_updated < UPDATE_INTERVAL_IN_SECONDS:
                    continue

            if is_first_iteration:
                is_first_iteration = False
            else:
                time.sleep(DELAY_BETWEEN_REPOSITORY_UPDATES_IN_SECONDS)

            relpath = os.path.relpath(repository_path, start=HERE)
            print("===> {}".format(relpath))
            try:
                sh("git", ["remote", "update"], working_directory=repository_path)
                status[repository_path] = int(time.time())
            except subprocess.CalledProcessError:
                print("===> Error updating {}".format(repository_path))
    finally:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            new_status = json.dumps(status, indent=4)
            f.write(new_status)

    finished = int(time.time())

    diff = finished - started
    human_diff = get_human_duration(diff)

    print("===> Finished in {}".format(human_diff))

    return 0


if __name__ == "__main__":
    sys.exit(main())
