# Changelog

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
