# Changelog

## [0.1.6] - 2026-10-27

### Changed

- Update the MQTT-to-D-Bus example to the reviewed, hash-pinned dbus-python 1.5.1 source distribution. Both native architecture validation jobs continue to exercise the GLib and D-Bus build dependencies.
- Update the native build lock to setuptools 84.2.1 and verify that every declared build dependency retains its version, marker, extras and SHA-256 hash in the lockfile.

## [0.1.5] - 2026-10-18

### Changed

- Route Dependabot metadata approval through the trusted default branch while preserving the existing author and review policy.
- Update Pycairo to 1.29.2, PyGObject to 3.58.1 and pinned shared CI workflows.

### Upgrade

Use the documented upgrade procedure and preserve local configuration and data. No configuration migration is required. Keep the previous immutable release available for rollback.

### Security

This maintenance release preserves the existing security and release-validation requirements. Publication does not deploy the service or establish physical-device acceptance.

## [0.1.4] - 2026-10-17

- Remove the unused runtime pip-compile input manifest so Dependabot treats the canonical
  hash-locked dependency files as ordinary pip requirements. Native container
  builds and Cairo preinstallation consistency checks remain required.

- Document governance, private conduct reporting, the maintained architecture and
  assurance scope; link the official OpenSSF assessment from the README.
- Clarify the 60-day fix policy for publicly known medium-or-higher vulnerabilities.

### Upgrade

Extract the source suite into a separate directory and use its committed dependency locks. Preserve local configuration; production deployment and device acceptance remain separate.

### Security

The source and dependency-maintenance changes preserve the existing validation gates. No new application vulnerability fix or target-device acceptance is claimed.

## [0.1.3] - 2026-10-14

### Changed

- Require positive fuzz engine execution counts, instrumented production code and validated seed corpora before accepting RC evidence.
- Add regression tests for malformed reports, unsafe corpora and incomplete seed replay; retain the existing coverage requirements.
- Keep mutation campaigns restricted to public RCs and use deterministic seed checks in ordinary CI.

### Upgrade

Use the documented update procedure and preserve local configuration. No application configuration or data migration is introduced. Keep the previous accepted package available for rollback; the exact candidate still requires applicable device and integration acceptance.

### Security

RC publication rejects absent or invalid source-bound fuzz reports. The fuzz runner bounds corpus paths, file types and size. No application vulnerability or new target-device acceptance is claimed by these tooling changes.

## [0.1.2]

### Added

- RC-only fuzzing of real pure input handlers, with documented synthetic seeds and bounded execution.
- Reviewed source archives with isolated acceptance, frozen versions, receipts and checksums.

### Upgrade

Extract the new source suite into a separate directory. Preserve local configuration
and device state. This package does not deploy or install itself on any device.

### Security

The source suite and test corpus contain no private captures or credentials.
Fuzz campaigns cannot contact devices; actual hardware acceptance is separate.

## Unreleased

- Preserve MQTT processing and template error tracebacks while retaining the
  existing fallback values and recovery on the next valid message.
- Run offline bridge unit tests in the shared local/CI entry point using
  hash-locked Python dependencies, alongside the native container smoke checks.
- Analyze GitHub Actions workflows with CodeQL alongside Python source.
- Explain the D-Bus signal hook and simplify the example container build steps
  without changing its pinned dependencies or non-root runtime user.

## 0.1.1 - 2026-09-12

- Distinguish native Venus OS service integration from companion-host examples.
- Document persistent `/data` paths, native supervision, bounded logs and offline
  dependency requirements for GX deployments.
- Mark example integrations as patterns requiring validation rather than ready
  installers. This documentation release installs no service on a GX device.
