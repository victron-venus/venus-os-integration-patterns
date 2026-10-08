# Changelog

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
