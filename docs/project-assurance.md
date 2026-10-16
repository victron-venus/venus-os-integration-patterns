# Architecture, assurance scope and roadmap

## Maintained source and trust boundaries

The runnable Python implementation is `patterns/mqtt-to-dbus/src`: it reads
YAML configuration, subscribes to selected MQTT topics, validates/converts values
and publishes configured D-Bus paths. `value_conversion.py` is shared by the
running bridge, unit tests and fuzz target. Configuration and error behavior are
in [the bridge guide](../patterns/mqtt-to-dbus/README.md). `dbus-to-mqtt` and
`http-api-wrapper` currently contain documentation examples, not complete
packaged services. Scheduled control and Home Assistant automation are future
ideas, not implemented directories.

Docker/Compose targets a companion Linux host with local D-Bus access; stock
Venus OS is not claimed to provide Docker. Native deployment needs dependencies
for the target Python ABI, retained firmware bindings and explicit device
acceptance. The bridge's current MQTT connection is plaintext; optional username
and password do not encrypt it. Run only on a trusted isolated network. Do not
expose the broker or D-Bus to an untrusted network or treat this example as a
production security boundary. Adding a reviewed, tested TLS configuration is a
roadmap item, not a current feature.

## Cryptography and supported configuration

Bridge MQTT traffic is local plaintext and does not offer encryption or
password storage. This project has no end-user password-verifier database or
custom cryptographic primitive. SHA-256 binds source/archive content and release
metadata. Git object identifiers are not newly designed security primitives.
Source-release helpers use GitHub CLI's maintained Go TLS implementation; use the
[verified strict release transport profile](release-tls-profile.md) for a
complete release-tool configuration. That profile preserves certificate and
hostname validation, TLS 1.2+, forward-secret key exchange and minimum
certificate key lengths. Custom release transport trust stores require separate verification. Library and operating-system CSPRNGs supply
cryptographic randomness; test-data pseudorandom generators are not key sources.

No hosted check establishes that a deployment used the documented profile.
Ordinary compatibility settings, arbitrary proxies, custom trust stores or
external applications need their own assessment.

## Verification and reporting

`bash scripts/ci.sh` parses source/configuration, validates workflow semantics,
runs the bridge tests with explicit D-Bus/GLib stubs and exercises the real pure
value converter. CI also builds/imports the native bridge container on amd64 and
arm64 with the hash-locked native dependencies. Stubs do not prove native binding
compatibility; the separate native builds supply that evidence. The RC-only
fuzz target mutates the value converter used by the running bridge.

CodeQL and dependency analysis provide independent static/security checks.
Inspect actual findings and run logs, including skipped work. The source archive
is versioned and its inventory verified, but a source archive alone does not
prove bit-identical external container rebuilds. Fixed seed replay is separate
from an actual instrumented mutation campaign; see [fuzzing](fuzzing.md).

## Roadmap: October 2026 through October 2027

Over the next twelve months, maintain the existing release/integration contracts,
add measured coverage of owned production code and improve tests at malformed
input and unavailable-dependency boundaries. Review transport configuration and
operator guidance with every supported toolchain update. Establish and exercise
an authorized second-person repository, CI and release recovery arrangement.
Add a reviewed TLS option for the bridge and expand native deployment guidance before considering further runnable patterns.

The project will not certify physical safety from mocks, promise unattended
production installation, or replace the security review of external services.
New features remain proposals until implemented and verified. Universal
accessibility/internationalization, exhaustive input validation, complete
coverage and a formal security assurance case are not currently claimed.
[GOVERNANCE](../GOVERNANCE.md) records the confirmed absence of backup
maintainership and recovery within one week; those Silver requirements remain
unmet. [The official assessment](https://www.bestpractices.dev/en/projects/15558)
is the source of truth for criterion status and the live README badge.
