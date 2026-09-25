# Willow & Birdie Innovations

We build tools that help people inspect digital evidence, automate repetitive work, and understand what their data actually supports.

This index links to usable evidence, measured limitations and project status. It does not publish private implementations or customer data.

## Products

### [APK Sentinel](https://github.com/tmtz1/apk-sentinel)

- **Problem:** inspect an Android package without installing or executing it.
- **Output:** [synthetic JSON report](https://github.com/tmtz1/apk-sentinel/blob/main/examples/apk-sentinel-sanitized-report.json), [real-world hard cases](https://github.com/tmtz1/apk-sentinel/blob/main/docs/real-world-hard-cases.md).
- **Status:** public evidence package; consult the [canonical product status](https://github.com/tmtz1/apk-sentinel/blob/main/product-status.json) for current availability. This index intentionally does not repeat price or payment network.
- **Next useful milestone:** reconcile the deployed paid contract and current operating terms before renewed intake.

## Research

### Cloud Model Coding Benchmarks

[Four assistants, one receipt-validation repair: SOL 5.6, SOL 6, Astra and Opus](docs/benchmarks/gpt-sol-receipt-validation/README.md).

- **Problem:** distinguish a successful subprocess exit from a valid send receipt.
- **Output:** frozen baseline/candidates, offline tests, hashes, [reproduction harness](docs/benchmarks/gpt-sol-receipt-validation/verify.py) and a separate hardening follow-up.
- **Status:** one controlled code-repair experiment, not a general model ranking or deployed integration.
- **Execution boundary:** inference ran on provider infrastructure; the harness and generated-code tests ran locally. Provider timings/tokens are reported historical measurements; correctness tests are independently reproducible.
- **Next useful milestone:** versioned additional tasks and repeated trials, without rewriting this experiment.

### Local LLM / On-Device Inference

[Local serving benchmark](docs/local-inference-benchmark.md) · [Chat-route results](docs/local-inference-chat-results.md).

- **Problem:** evaluate locally served models under limited GPU/memory budgets.
- **Output:** historical task scores, latency observations and failure descriptions.
- **Status:** historical research; incomplete run metadata prevents exact reproduction or universal model rankings.
- **Next useful milestone:** a separately dated rerun with artifact hashes, scoring rules and full configuration. No rerun is claimed here.

### RIVR

[Public RIVR case study](docs/rivr.md).

- **Problem:** inspect proprietary sensor recordings without modifying the source capture.
- **Output:** described inventory, timeline and viewer capabilities; implementation and recordings are private.
- **Status:** research; encrypted recovery is parked where a required device key is unavailable.
- **Next useful milestone:** a sanitized synthetic viewer/export demonstration and annotation overlays.

## Upstream integrations

### Buzz

[Upstream relationship and verification limits](docs/buzz-integration.md) · [fork](https://github.com/tmtz1/buzz).

Buzz is upstream software from Block. Hosting a fork does not make its application code our original work. The fork's default branch is an upstream copy, not evidence of our deployed version or a tested fork distribution.

## Reuse and corrections

See [usage terms](USAGE.md). Documentation corrections and reproducibility reports are welcome; include the file, commit, command, Python version and observed result. Do not submit secrets, customer samples or private provider receipts. Production code and infrastructure stay private.

[Company website](https://willowbirdie.com) · [GitHub profile](https://github.com/tmtz1) · [Integration and pilot inquiries](mailto:admin@willowbirdie.com)
