# Willow & Birdie Innovations

**Research and engineering index**

Willow & Birdie Innovations is a technology research and development company focused on difficult digital systems: digital forensics, applied AI, evidence processing, data systems, automation, and distributed infrastructure.

This repository is an index of public research and engineering records. APK Sentinel is maintained in its own repository as the primary public product and evidence package.

## Current projects

### [APK Sentinel](https://github.com/tmtz1/apk-sentinel)

A deterministic, automation-friendly API for static Android APK triage. The repository contains the primary public evidence package, architecture, sanitized reports, validation notes, real-world hard cases, API contracts, and security boundaries.

**Status:** Limited beta. The documented endpoint is callable for bounded testing through x402 on Base Sepolia. This is API access, not a browser upload portal; general customer intake and support are not enabled. See the [canonical status record](https://github.com/tmtz1/apk-sentinel/blob/main/product-status.json).

### Local inference reliability

Measured research on local model serving, structured output, latency, context retention, prompt-injection resistance, and operational boundaries.

- [Model benchmark](docs/local-inference-benchmark.md)
- [Chat and modality results](docs/local-inference-chat-results.md)

### RIVR

A personal ROVR and LightCone parser toolkit documented as research and engineering work.

- [RIVR project notes](docs/rivr.md)

## How the work is organized

Each public project is intended to make the following visible:

1. Problem and product thesis
2. Approach and architecture
3. Validation and failure cases
4. Current status and operational boundaries
5. Sanitized public artifacts

The company repository points to project-specific records without duplicating their full documentation.

## Engineering themes

- Evidence over assertion
- Determinism where repeatability matters
- Explicit uncertainty and partial-analysis states
- Fail-closed handling of unsupported or malformed input
- Stable contracts for humans and software agents
- Local and private processing where sensitive data requires it
- Real inputs, regression tests, and cleanup as part of correctness

## Public and private boundary

The public repositories contain documentation, research records, sanitized examples, and non-sensitive architecture material. Production source code, private samples, customer data, credentials, wallet keys, queue state, and deployment access remain outside the public repositories.

## Links

- [Willow & Birdie Innovations](https://willowbirdie.com)
- [GitHub profile](https://github.com/tmtz1)
- [Contact](mailto:admin@willowbirdie.com)
