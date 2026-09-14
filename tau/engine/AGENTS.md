# Agents and Toolchain Structure

## Toolchain Structure

### vendor/
The `vendor/` directory contains external dependencies managed as submodules to maintain a sovereign codebase and prevent build drift:
- `kimi-code-sovereign`: Custom healer components.
- `modelbeats`: Model interaction utilities.
- `oh-my-pi`: Upstream oh-my-pi core.
- `pi-subagents`: Sub-agent orchestration.
- `pi-upstream`: Canonical pi upstream source.
- `tinker-cookbook`: Experimental tools and recipes.

### tools/
Custom utility scripts for local build, test, and diagnostics.

### provider hotfixes
When editing provider-specific login or request-shaping code, patch only the exact provider and the narrowest governing guidance file. Prefer fail-fast validation for provider-specific credentials; do not broaden the change into unrelated providers or broad catalog rewrites.

### NVIDIA / provider hotfix workflow
For NVIDIA/NIM work, keep the change in the exact provider or request-shaping file, not AST tooling. Use a single repo-root `grep`/`glob` pass before chasing subtrees, fail fast on obviously invalid NVIDIA selectors or credentials, validate NVIDIA via the full provider catalog (`MODEL_PATTERN='nvidia'`, `MAX_MODELS=0`), and verify by reading back the touched regions after each edit.

Run `git submodule update --init --recursive` to ensure all submodules are synchronized.

<!-- ralph-workflow-policy:begin v1 -->
This project participates in Ralph Workflow's project-policy-readiness
preflight. Before ordinary planning or development begins, the canonical
quality-policy files under docs/ralph-workflow-policy/ must exist, be customized for
this project's languages, frameworks, and commands, and pass the
deterministic validator (see marker contract below).

The remediation agent MUST, in order:

1. Inspect the project's actual languages, frameworks, package managers,
   test frameworks, and existing CONTRIBUTING/TESTING/DEVELOPMENT docs.
2. Create and maintain the canonical policy files under docs/ralph-workflow-policy/ for
   every core policy type listed in the Ralph markers.
3. Customize each policy file with verified project facts (commands,
   owners, supported platforms, exceptions). Replace every starter
   placeholder with verified project evidence.
4. Migrate any existing project policy-like content into the matching
   canonical file, leaving a `ralph-workflow-policy:migrated ->` marker at
   the old location so the validator can clear the RWP-MIGRATE-UNRECONCILED
   finding.
5. Configure executable gates for testing, type checking, linting,
   dependency checks, and verification. Document each gate as a
   RALPH-COMMAND line (or RALPH-INAPPLICABLE with reason) so the validator
   can confirm the gate is real and non-placeholder.
6. Update CLAUDE.md (if present) to point Claude-compatible agents at this
   AGENTS.md.
7. Run every declared verification gate and report the outcome.

Dead code is prohibited; remove it — rewriting later is better than retaining it.

The remediation agent MUST NOT mark any policy complete while any RALPH-FACT
placeholder token, RALPH-COMMAND without a real value, or unresolved
RALPH-LANG coverage remains.

The readiness preflight is byte-exact deterministic; near-miss prose, extra
whitespace, or case changes do not satisfy any requirement.
<!-- ralph-workflow-policy:end -->
