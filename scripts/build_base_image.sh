#!/usr/bin/env bash
# Build the shared task base image `visual-cipher-bench-base:1-codex163h` once after
# cloning. It downloads pinned Python wheels and agent binaries, verifies their
# SHA-256 hashes, and builds infra/docker/base.Dockerfile. Every task image is built
# FROM it, so task builds and agent setup need no network.
#
#   bash scripts/build_base_image.sh
#
# The image is linux/amd64.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CTX="$ROOT/infra/docker"
IMAGE="visual-cipher-bench-base:1-codex163h"

# destination|sha256|url   (the codex entry is a .tar.gz; its binary is extracted below)
FILES=(
  "wheels/numpy-2.5.3-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl|b7e18c623bb5c95acb3b3328861272816ba199fb531921c5d6d0b675f1fde9e3|https://files.pythonhosted.org/packages/65/af/aa78d1a88805456e212b65461354cd943197fb9acecc4c90fd12295123a3/numpy-2.5.3-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
  "wheels/pillow-12.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl|78cb2c6865a35ab8ff8b75fd122f6033b92a62c82801110e48ddd6c936a45d91|https://files.pythonhosted.org/packages/84/21/a35af28dcc61f37ed850a2d64c65c701321dfbf25085e469d5559360cbbf/pillow-12.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
  "agents/claude|24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de|https://downloads.claude.ai/claude-code-releases/2.1.296/linux-x64/claude"
  "agents/codex.tar.gz|beb339e8ecd9ba057a6bb2dc81ad8ca474812edfbf0fc5056ca818797648dde4|https://github.com/openai/codex/releases/download/rust-v0.163.0/codex-x86_64-unknown-linux-musl.tar.gz"
  "agents/host.tar.gz|314263128ba6592e7e807c265deeaf928a692b72dcbfeb5e0b20c9423b703529|https://github.com/openai/codex/releases/download/rust-v0.163.0/codex-code-mode-host-x86_64-unknown-linux-musl.tar.gz"
)

sha256() {
  if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

mkdir -p "$CTX/wheels" "$CTX/agents"
for entry in "${FILES[@]}"; do
  IFS='|' read -r dest hash url <<<"$entry"
  file="$CTX/$dest"
  if [[ ! -f "$file" || "$(sha256 "$file")" != "$hash" ]]; then
    echo "downloading $dest"
    curl -fsSL --retry 3 -o "$file.part" "$url"
    mv "$file.part" "$file"
  fi
  got="$(sha256 "$file")"
  if [[ "$got" != "$hash" ]]; then
    echo "SHA-256 mismatch for $dest: expected $hash, got $got" >&2
    rm -f "$file"
    exit 1
  fi
done
tar -xzf "$CTX/agents/codex.tar.gz" -C "$CTX/agents"
mv -f "$CTX/agents/codex-x86_64-unknown-linux-musl" "$CTX/agents/codex"

tar -xzf "$CTX/agents/host.tar.gz" -C "$CTX/agents"
mv -f "$CTX/agents/codex-code-mode-host-x86_64-unknown-linux-musl" "$CTX/agents/codex-code-mode-host"

docker build --platform linux/amd64 -t "$IMAGE" -f "$CTX/base.Dockerfile" "$CTX"
echo "built $IMAGE (Claude Code 2.1.296, Codex 0.163.0)"
