# Evaluation protocol

## One attempt

Each fresh task environment exposes one to three fixed images and the shared submission instruction. The agent may inspect images, crop or transform them, and write and run programs. There is no correctness feedback during solving. The puzzle evidence remains fixed throughout the attempt.

The agent has 3,600 seconds, 2 CPUs, and 4 GB RAM, with no GPU. Puzzle-side network access is disabled. The harness may allow the configured model API hostname for agent inference; this is not permission to browse the web or retrieve additional puzzle material. Reference solutions, answer keys, and verifier files are not agent inputs.

The paper setup uses Harbor `0.24.0`, Codex `0.163.0` for GPT-family configurations, and Claude Code `2.1.296` for the other model configurations. The latter were served through an Anthropic-compatible gateway. A different model endpoint or runner can change results and should be reported explicitly.

## Exact-answer scoring

The independent verifier reads `/work/answer.txt` and compares it with `tests/expected.json`. The reward is binary, with no partial credit or LLM judge.

1. Apply Unicode NFKC normalization, remove whitespace, and uppercase both strings.
2. Accept an exact match.
3. For an ASCII alphanumeric reference answer, also accept separators between alphanumeric groups: comma, semicolon, vertical bar, hyphen, underscore, `->`, `=>`, `→`, `⇒`, or `、`. The implemented grader also strips a leading opening bracket and a trailing closing bracket from `[]`, `()`, or `{}` before checking this form.
4. If the reference answer contains punctuation, require its normalized punctuation to match exactly. Dots, colons, and slashes are not interchangeable separators.

For example, `5,4,2` and `542` match the same alphanumeric key, while `5.42` does not. A key such as `761/24` retains its slash. Empty, missing, unreadable, oversized (more than 4,096 bytes), or symbolic-link answer files score zero. Timeouts and failed attempts count as zero in reported accuracy.

## Repeats and aggregation

Each model–effort configuration is evaluated on all 40 tasks with three independent attempts per task. These repetitions are independent runs, not conversational rounds. `reasoning_effort` is a runner/model setting and is separate from whether an agent uses multiple tool turns.

```text
mean accuracy = total correct answers / 120
mean solved tasks = total correct answers / 3
category accuracy = correct answers in that category / 30
```

Report every scheduled slot, including zeros. Do not average only completed answers, select the best attempt, or treat pass@3 as mean accuracy.
