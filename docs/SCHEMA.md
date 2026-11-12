# Task schema

The release contains exactly 40 tasks, with ten in each category. [task-manifest.json](task-manifest.json) lists every task and its input image paths. [task-checksums.sha256](task-checksums.sha256) records the bytes of all task files, including reference resources.

```text
tasks/<category>/<task-id>/
├── instruction.md
├── task.toml
├── environment/
│   ├── .dockerignore
│   ├── Dockerfile
│   └── images/01.png [02.png, 03.png]
├── solution/
│   ├── solve.sh
│   ├── solve.py
│   ├── walkthrough.md
│   └── solver_lib/             # where needed
└── tests/
    ├── test.sh
    ├── grade.py
    └── expected.json
```

## Agent-visible inputs

The shared instruction is:

> Solve this visual reasoning puzzle: examine all images in /app/images/ and write the single final answer to /work/answer.txt. Write only the answer itself, with no quotes, punctuation, or explanation.

The task Dockerfile copies only `environment/images/` into `/app/images/` and removes write permission from the images. The agent runs as `puzzle` in `/work`. Host task IDs and category directories are for organization; do not supply category labels, walkthroughs, or answer keys as additional prompts.

## Configuration

| Field | Value |
| --- | --- |
| `artifacts` | `["/work/answer.txt"]` |
| `metadata.category` | Parent category directory |
| `agent.timeout_sec` | `3600` |
| `agent.user` | `puzzle` |
| `verifier.timeout_sec` | `120` |
| `verifier.user` | `root` |
| `verifier.environment_mode` | `separate` |
| Agent, verifier, environment network mode | `no-network` |
| Environment build timeout | `600` seconds |
| Environment resources | 2 CPUs, 4096 MB RAM, 4096 MB storage |

Task images inherit `visual-cipher-bench-base:1-codex163h`. Build this tag before invoking Harbor. The inherited runtime has Python, NumPy, Pillow, and the preinstalled agents; see [runtime documentation](../infra/README.md).

## Reference and verifier material

`solution/` is for maintainers and oracle runs. It includes a walkthrough, executable reference solution, and any task-specific libraries or reference resources. Some resources are Linux `x86_64` native libraries or binaries. They are kept outside the agent image.

`tests/expected.json` stores the reference answer. `tests/test.sh` runs the shared exact-answer grader in a separate verifier container. The verifier writes `reward.txt` and `result.json` under `/logs/verifier/`. Keep the full repository, reference resources, and answer keys out of evaluated-agent mounts.

An oracle success verifies that a bundled solver produces an accepted answer. It does not by itself prove uniqueness over every imaginable interpretation of a puzzle; walkthroughs and solver searches state the intended mechanism and search assumptions.

## Integrity check

From the repository root:

```bash
sha256sum -c docs/task-checksums.sha256
# macOS alternative:
shasum -a 256 -c docs/task-checksums.sha256
```
