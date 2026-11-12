"""Common exact-answer verifier; no model judge or puzzle-specific executable."""
import json
from pathlib import Path
import re
import sys
import unicodedata


def normalize(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value))).upper()


# 542 and 5,4,2 are one answer, but a
# separator must sit between two symbols, and 5.42, 5:42 and 1/2 stay different.
SEPARATOR = "(?:->|=>|[,;|\\-_\u2192\u21d2\u3001])"  # \u2192 right arrow, \u21d2 double arrow, \u3001 ideographic comma
BRACKETS = re.compile(r"^[\[({]|[\])}]$")


def correct(answer, expected):
    answer, key = normalize(answer), normalize(expected)
    if not answer:
        return False
    if answer == key:
        return True
    # A key with its own punctuation (761/24) is matched exactly.
    if not (key.isascii() and key.isalnum()):
        return False
    text = BRACKETS.sub("", answer)
    if not re.fullmatch(r"[A-Z0-9]+(?:" + SEPARATOR + r"[A-Z0-9]+)*", text):
        return False
    return re.sub(SEPARATOR, "", text) == key


def grade(answer_path, expected_path, logs):
    expected = json.loads(Path(expected_path).read_text())["answer"]
    try:
        path = Path(answer_path)
        if path.is_symlink() or path.stat().st_size > 4096:
            raise ValueError("Invalid answer file")
        answer = path.read_text()
        reward = int(correct(answer, expected))
    except (OSError, UnicodeError, ValueError):
        reward = 0
    logs = Path(logs)
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "reward.txt").write_text(str(reward) + "\n")
    (logs / "result.json").write_text(json.dumps({"reward": reward}) + "\n")
    return reward


if __name__ == "__main__":
    grade(*sys.argv[1:])
