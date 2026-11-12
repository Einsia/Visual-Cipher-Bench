# Setup and running

## Requirements

Use Linux `amd64`, Python 3.12, Docker, Bash, `curl`, `tar`, and either `sha256sum` or `shasum`. No GPU is required. Each concurrent task requests 2 CPUs, 4 GB RAM, and 4 GB storage, in addition to host and image-build overhead. Start with concurrency 1.

On Apple Silicon or another ARM host, enable Docker's `amd64` emulation and set `DOCKER_DEFAULT_PLATFORM=linux/amd64`. Native reference-solver binaries are not macOS executables. The supported reproduction target is Linux `amd64`; emulated timing is not comparable to the reported experiment.

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install harbor==0.24.0
docker info
bash scripts/build_base_image.sh
```

Run commands from the repository root. The base build is a one-time prerequisite for all task images. It downloads wheels and the pinned agent binaries, checks hashes, and creates `visual-cipher-bench-base:1-codex163h`. See [infrastructure details](../infra/README.md).

Check the runtime before spending model tokens:

```bash
docker run --rm --platform linux/amd64 visual-cipher-bench-base:1-codex163h codex --version
docker run --rm --platform linux/amd64 visual-cipher-bench-base:1-codex163h claude --version
harbor run -p tasks/spatial-reasoning/prism-camera -a oracle -n 1
```

An oracle run executes the bundled reference solution and then the verifier. It does not call a model API. Some reference solvers perform substantial searches; a failed or timed-out oracle run should be investigated rather than counted as a model result.

## Run one model task

Set credentials in the shell environment, then use an available model ID and supported effort. These examples use the standard provider hosts; a compatible gateway may require a different model ID and base URL.

```bash
export MODEL='your-available-model-id'
export EFFORT='high'
# Set OPENAI_API_KEY securely in your environment first.
harbor run -p tasks/spatial-reasoning/prism-camera \
  -a codex -m "$MODEL" \
  --ak version=0.163.0 --ak reasoning_effort="$EFFORT" \
  --ae OPENAI_API_KEY="$OPENAI_API_KEY" \
  --allow-agent-host api.openai.com \
  -n 1 -o jobs --job-name codex-one-task
```

For Claude Code:

```bash
# Set ANTHROPIC_API_KEY securely in your environment first.
harbor run -p tasks/spatial-reasoning/prism-camera \
  -a claude-code -m "$MODEL" \
  --ak version=2.1.296 --ak reasoning_effort="$EFFORT" \
  --ae ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --allow-agent-host api.anthropic.com \
  -n 1 -o jobs --job-name claude-one-task
```

`MODEL` must match the selected runner and endpoint. For a gateway, additionally pass `--ae OPENAI_BASE_URL="$OPENAI_BASE_URL"` or `--ae ANTHROPIC_BASE_URL="$ANTHROPIC_BASE_URL"`, and replace the allowed hostname with that gateway's hostname. Do not allow arbitrary network access. The paper used an Anthropic-compatible gateway for non-GPT models; the public Anthropic endpoint does not provide those other vendors' models.

## Evaluate all 40 tasks

Run all four category directories. This makes coverage explicit and avoids depending on recursive dataset discovery. Use a new job name for each category and repeat.

```bash
for RUN in 1 2 3; do
  for CATEGORY in spatial-reasoning logic-puzzles rule-induction knowledge-decoding; do
    harbor run -p "tasks/$CATEGORY" \
      -a codex -m "$MODEL" \
      --ak version=0.163.0 --ak reasoning_effort="$EFFORT" \
      --ae OPENAI_API_KEY="$OPENAI_API_KEY" \
      --allow-agent-host api.openai.com \
      --agent-setup-timeout-multiplier 8 \
      --max-retries 2 --retry-include UnknownApiError \
      -n 1 -o jobs --job-name "codex-$EFFORT-$CATEGORY-r$RUN"
  done
done
```

For Claude Code, substitute its runner, version, credentials, and endpoint as in the one-task example. Keep the agent's 60-minute execution limit unchanged. An increased setup timeout is separate from the solving budget.

Confirm 40 distinct tasks and 120 scored slots per model–effort configuration. Keep the model ID, runner/version, effort, environment digest, run index, task ID, final reward, and failure/retry evidence with your results. Avoid reusing job names across models. [EVALUATION.md](EVALUATION.md) defines aggregation.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Docker daemon unavailable | Start Docker and confirm `docker info` succeeds. |
| Base image not found | Build `visual-cipher-bench-base:1-codex163h` on the same Docker daemon Harbor uses. |
| `exec format error` | Build and run with `linux/amd64`; Linux solver binaries require a Linux container. |
| Codex command tool fails | Confirm the matching `codex-code-mode-host` binary is installed beside `codex`. |
| Agent setup tries to download | Check runner version pins and the preinstalled CLI; setup also runs under offline restrictions. |
| API connection fails | Check credentials, base URL, and the narrowly allowed API hostname. |
| SHA-256 mismatch | Stop the build and investigate the download; do not bypass the hash check. |
| Answer is spoken but reward is zero | The agent must write `/work/answer.txt`; conversational text alone is not a submission. |

Keep credentials and raw job output outside commits. The repository's `.gitignore` excludes downloaded runtime assets, environments, and job directories.
