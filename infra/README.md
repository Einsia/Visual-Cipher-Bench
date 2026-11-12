# Runtime infrastructure

The task packages use one shared `linux/amd64` image, built with:

```bash
bash scripts/build_base_image.sh
```

Run this from the repository root. The script builds `visual-cipher-bench-base:1-codex163h` from [docker/base.Dockerfile](docker/base.Dockerfile). The tag is retained because all 40 evaluated task Dockerfiles reference it.

| Component | Pin |
| --- | --- |
| Base OS / Python | `python:3.12.10-slim-bookworm` |
| NumPy | `2.5.3` |
| Pillow | `12.3.0` |
| Codex | `0.163.0`, Linux musl `x86_64` |
| Codex code-mode host | Matching `0.163.0` binary |
| Claude Code | `2.1.296`, Linux `x64` |
| Harbor on the host | `0.24.0` |

The build script verifies the SHA-256 of every downloaded wheel and agent archive. It installs Python dependencies from those local wheels. The base Python image is version-tagged, not digest-pinned; record the resolved image digest for exact environment archival.

The `codex-code-mode-host` executable must sit beside `codex`. Omitting it can make the command tool fail even when `codex --version` succeeds.

`docker/.dockerignore` allows only the Dockerfile, wheels, and agent binaries into the shared build context. These downloads are ignored by Git. Each task builds from its own `environment/`, which contains only its image recipe and input images. Reference fonts, dictionaries, solver libraries, answers, and walkthroughs stay outside agent images. Do not install extra fonts in the runtime: several tasks require recovering glyphs from the supplied pixels.

Build-time downloads require network access. Task execution uses the offline settings in `task.toml`, with only the model API host allowed by the harness. A Docker build is not a complete evaluation; use the commands and checks in [SETUP.md](../docs/SETUP.md).
