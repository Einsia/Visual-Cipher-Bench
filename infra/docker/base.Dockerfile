# Shared base image for every task: Python with NumPy and Pillow, plus the
# Claude Code and Codex agents preinstalled so that Harbor can skip its
# (networked) agent install step. Built by scripts/build_base_image.sh.
# Contains no font files.
FROM python:3.12.10-slim-bookworm
COPY wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels Pillow==12.3.0 numpy==2.5.3 \
    && rm -rf /wheels \
    && useradd --uid 1000 --create-home puzzle \
    && mkdir -p /app/images /work /logs/verifier \
    && chown puzzle:puzzle /work
COPY --chmod=755 agents/claude /usr/local/bin/claude
COPY --chmod=755 agents/codex /usr/local/bin/codex
COPY --chmod=755 agents/codex-code-mode-host /usr/local/bin/codex-code-mode-host
