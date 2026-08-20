# APK Sentinel validation notes

## What was exercised

The private APK Sentinel implementation was tested with its local test suite:

```text
./.venv/bin/pytest -q
```

Observed result:

```text
393 passed in 4.89s
```

A signed synthetic APK fixture was built locally from committed test source. It was analyzed statically and serialized using the canonical report serializer. The published example was then parsed back through the `AnalysisReport` schema before writing.

The fixture is intentionally synthetic:

- Package: `com.example.apksentinelfixture`
- Version: `1.2.3` / code `123`
- Target SDK: 34
- Test-only signing certificate
- Inert references used to exercise static indicators
- Never installed, executed, or side-loaded

## Published example

[`examples/apk-sentinel-sanitized-report.json`](../examples/apk-sentinel-sanitized-report.json)

Observed report properties:

- Schema version: `1.0`
- Four static indicators
- Four evidence-backed findings
- Deterministic rule-based risk score: `70`
- Canonical JSON size: 2,850 bytes

## What this demonstrates

- APK metadata can be extracted into a strict report model.
- Findings carry evidence references.
- The canonical report is versioned and machine-readable.
- The same fixture is suitable for repeatability tests.
- Static analysis does not require execution or network access.

## Deliberate limits

This example is not a malware verdict and does not prove that static analysis can establish whether an APK is safe or malicious. It is a safe fixture demonstrating report structure and validation behavior. Production implementation, private fixtures, deployment evidence, and payment integration remain restricted.
