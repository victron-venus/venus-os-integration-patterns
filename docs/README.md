# Documentation

Runnable patterns for integrating services with Venus OS, with the release policy
and evidence records that keep each example checkable.

## Patterns

- [Architecture, assurance scope and roadmap](project-assurance.md) — the `patterns/mqtt-to-dbus` implementation and what it reads.

## Assurance

- [OpenSSF Best Practices evidence: venus-os-integration-patterns](openssf-evidence.md) — the index behind the assessment.

## Releases

- [Release helper TLS profile](release-tls-profile.md) — the qualified `gh` transport profile.
- [CI and release operations](release-workflow.md) — `.release-policy.json` and the required status.
- [CI orchestration](CI-ORCHESTRATION.md) — how the quality gate and release pipeline divide the events.
- [CI and release policy](CI_WORKFLOW.md) — the validation-only policy and its events.
- [Version plans and manifest synchronization](VERSIONING.md) — the versioning opt-in.
- [RC-only fuzz testing](fuzzing.md) — why fuzzing runs only on release candidates.
- [Fuzzing release candidates](rc-fuzzing.md) — the reusable bounded fuzz workflow.
- [Release read recovery and rerun validation](release-read-safety.md) — the two fixes carried from the shared toolkit.
- [Early final-build runner check](runner-preflight.md) — why the check runs before the final build.
