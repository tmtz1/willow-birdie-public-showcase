# Willow & Birdie Innovations — Public Technical Showcase

**Tmtz · Founder / Principal**

[Willow & Birdie Innovations](https://willowbirdie.com) is a technology research and development company focused on AI-assisted software development, digital forensics, data systems, and distributed computing infrastructure.

This repository is a public overview of selected research and product work. The production implementations remain private and proprietary.

## Selected work

### [APK Sentinel — deterministic APK triage](docs/apk-sentinel.md)

A private, in-development project for evidence-backed static analysis of Android APKs. The planned service produces bounded, versioned JSON triage reports without installing or executing submitted APKs.

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

---

## Update — human-assisted API access

APK Sentinel now has a human-assisted use path in addition to automated agent use. A person can submit an APK with a standard HTTP client such as `curl` or Postman, follow the x402 payment requirements, and poll the returned result. This is API access for a human operator—not a browser upload portal.

The existing endpoint, price, Base Sepolia network, asynchronous `202 queued` workflow, static-analysis boundaries, and retention limits remain unchanged. Human operators should treat the returned report as triage evidence and review it before making decisions about an APK.

### Hard lesson learned

The paid API contract is asynchronous: a successful submission returns `202 queued`, not the final report. A client must retain the job ID and result token and poll the result endpoint. Infrastructure readiness matters just as much: a worker can fail closed when its container runtime is unavailable, even when the API and payment path are healthy.
