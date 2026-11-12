#!/bin/sh
set -eu
python /solution/solve.py --images /app/images --output /work/reference_answer.json
python - <<'PY'
import json
from pathlib import Path
answer = json.loads(Path('/work/reference_answer.json').read_text())['answer']
Path('/work/answer.txt').write_text(str(answer) + '\n')
PY
