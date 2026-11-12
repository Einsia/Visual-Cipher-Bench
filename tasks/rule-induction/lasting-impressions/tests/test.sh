#!/bin/sh
set -eu
# Never run from the agent-writable /work; -I keeps Python from importing
# modules out of the current directory or the environment.
cd /
# Harbor environment_mode=separate runs verification in a fresh container, so
# leftover agent processes cannot interfere with grading. If shared mode is
# used, the killall below stops all agent-owned processes first.
python -I - <<'PY'
import os, pwd, signal
uid = pwd.getpwnam("puzzle").pw_uid
for pid in filter(str.isdigit, os.listdir("/proc")):
    try:
        if os.stat(f"/proc/{pid}").st_uid == uid:
            os.kill(int(pid), signal.SIGKILL)
    except OSError:
        pass
PY
chmod -R go-rwx /tests
mkdir -p /logs/verifier
python -I /tests/grade.py /work/answer.txt /tests/expected.json /logs/verifier
