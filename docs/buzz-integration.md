# Buzz: upstream relationship

Checked September 24, 2026. [tmtz1/buzz](https://github.com/tmtz1/buzz) is a fork of [block/buzz](https://github.com/block/buzz), not an original Willow & Birdie application.

The fork default branch at `3c7f288c60d67df78577b237e27c3dfc8831aaa1` compared as 0 commits ahead and 99 behind upstream at this check. That describes only those branch references, not other branches, our installed system, or a recommended supported release. There is no verified fork-specific distribution or supported deployed commit asserted here.

We are leaving the tracking branch unchanged rather than adding cosmetic divergence or synchronizing blindly. Before adopting upstream changes: identify the actual deployed commit, review the delta, test the integration in use, and retain a rollback reference. Inherited CI and release instructions are not evidence of a successful build in this fork; Block-private release infrastructure is not a release procedure for this account.

## Ownership and security

Upstream CODEOWNERS and security reporting apply to upstream work. Questions about Willow & Birdie's deployment or modifications belong at admin@willowbirdie.com; do not assume Block maintains those changes or offers response targets for our service. No compliance claim is adopted from inherited descriptions. A keyless audit chain does not stop a database writer from recomputing history.

## Source discrepancies to verify upstream

The reviewed workflow lists lowercase `justfile` in a Rust path filter while the tracked root file is `Justfile`. Case-sensitive path matching would not equate those literals. This is a source-level concern; the actual Actions filter action has not been executed against a Justfile-only PR here, so no runtime CI defect is claimed.

The reviewed security workflow invokes `cargo-deny check`, while SECURITY.md mentions `cargo audit`. No additional audit lane was established by this review. Upstream documentation or a demonstrated additional lane should reconcile the description. No upstream issue or PR has been filed as part of this documentation pass.
