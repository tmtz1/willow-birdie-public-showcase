# Willow & Birdie Innovations — Public Technical Showcase

**Tmtz · Founder / Principal**

[Willow & Birdie Innovations](https://willowbirdie.com) is a technology research and development company focused on AI-assisted software development, digital forensics, data systems, and distributed computing infrastructure.

This repository is a public overview of selected research and product work. The production implementations remain private and proprietary.

## Selected work

### [APK Sentinel — AI-agent APK triage](docs/apk-sentinel.md)

A limited beta for bounded, static-only Android APK triage. The live x402 endpoint accepts one APK per paid job and returns a versioned JSON report without installing or executing the sample. Automated agents and human operators can use the API directly; a browser upload portal is not part of this release.

## Evidence and validation

- [APK Sentinel architecture](assets/apk-sentinel-architecture.svg)
- [Sanitized APK Sentinel report](examples/apk-sentinel-sanitized-report.json)
- [APK Sentinel validation notes](validation/apk-sentinel-validation.md)

## Local inference research

- [BirdieRog model benchmark](docs/local-inference-benchmark.md)
- [Local chatbot honesty and modality bake-off](docs/local-inference-chat-results.md)

## Technical themes

- Digital forensics and artifact analysis
- Deterministic data processing
- Evidence-backed reporting
- Secure handling of untrusted files
- Local-first and privacy-conscious tooling
- Bounded infrastructure and reproducible validation

## Public/private boundary

This repository intentionally contains documentation only. It does not contain production source code, private APK samples, proprietary detection logic, customer data, credentials, or deployment access.

## Links

- [Willow & Birdie Innovations](https://willowbirdie.com)
- [Project profile](https://github.com/tmtz1)

## Contact

[admin@willowbirdie.com](mailto:admin@willowbirdie.com)
