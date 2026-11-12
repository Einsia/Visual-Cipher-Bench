# Contributing

Please open an issue with the task ID, observed behavior, and a minimal reproduction before changing a puzzle or its grading. Label discussions containing answers or mechanisms as spoilers.

Documentation corrections and setup clarifications are welcome. Changes to puzzle pixels, instructions, accepted answers, time limits, runner versions, or bundled reference resources affect benchmark comparability and need explicit maintainer review.

For a task change, provide:

- The affected task IDs and a before/after explanation.
- Evidence that the image, walkthrough, reference solver, and expected answer agree.
- The oracle result on the supported Linux runtime, including failures or timeouts.
- Updated task manifests/checksums and any third-party notices.
- A statement of whether existing evaluation results remain comparable.

Keep `solution/` and `tests/` outside the evaluated agent environment. Do not commit credentials, model-provider configuration files, downloaded agent binaries, Docker caches, raw rollout logs, or generated job directories.

Run the checksums documented in [SCHEMA.md](docs/SCHEMA.md), the base-image build, and an oracle check for each affected task. Changes to the verifier require positive and negative submission checks. A reference solver succeeding is not sufficient evidence of unrestricted mathematical uniqueness; document the mechanism and search assumptions.
