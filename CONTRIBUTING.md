# Contributing to venus-os-integration-patterns

Provides reference MQTT/D-Bus and HTTP integration implementations for Venus OS.

## Reports and discussion

Use [GitHub Issues](https://github.com/victron-venus/venus-os-integration-patterns/issues) for bugs, enhancements and design discussion. Search existing reports first. English reports and pull requests are welcome. Include the version or commit, platform, sanitized configuration, reproduction steps, expected behavior and actual behavior. Do not include credentials, personal data or private capture files. Use [SECURITY.md](SECURITY.md) for confidential vulnerability reports.

## Proposing a change

1. Fork or clone the repository over HTTPS and create a topic branch from the default branch.
2. Keep the change focused and explain the problem and observable behavior in a pull request.
3. Follow the existing language style and checked-in formatter/linter configuration. Resolve new warnings; explain any narrowly scoped exception with evidence.
4. Add automated tests for major new functionality and regression tests for corrected bugs. Cover rejected input, unavailable dependencies and relevant failure paths as well as successful input.
5. Update user-facing configuration/interface documentation and release notes for changed behavior. Record upgrade impact and any public vulnerability identifier when applicable.
6. Report the exact checks run, their results and any checks that were not run. Wait for required CI and reviewer approval before merging.

Contributions must be compatible with [LICENSE](LICENSE). Preserve third-party copyright and license notices; do not copy code without compatible redistribution rights.

## Local validation

Run `bash scripts/ci.sh` from the repository root. The script is the authoritative local entry point for the checks and tool versions; inspect it and the checked-in dependency manifests before installing prerequisites. Use an isolated development environment.

For the same Python 3.12 environment as CI:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes --only-binary=:all: -r .github/requirements-workflow-contracts.txt -r .github/requirements-bridge-tests.txt
bash scripts/ci.sh
```

The syntax checker also requires `node` and actionlint 1.7.12. Bridge unit tests
use explicit stubs for missing D-Bus/GLib host bindings. CI separately builds and
smoke-tests the real bridge container on Linux amd64 and arm64; no live bus or
MQTT broker is contacted by the unit suite.

Automated tests use mocks or controlled fixtures where available. A passing unit test does not establish hardware safety. Describe any physical-device test separately, including firmware, configuration and expected rollback. Never run installation, deployment, Terraform apply or actuator commands merely to validate a documentation change.

## Source and interfaces

- [patterns/mqtt-to-dbus](patterns/mqtt-to-dbus)
- [patterns/dbus-to-mqtt](patterns/dbus-to-mqtt)
- [patterns/http-api-wrapper](patterns/http-api-wrapper)

See [README.md](README.md) for acquisition, configuration and usage, and [the evidence index](docs/openssf-evidence.md) for the public development-process references.
