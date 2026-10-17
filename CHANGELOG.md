# Changelog

All notable changes to `@lam/ssh` are documented here.

## [3.0.1] - 2026-10-22

### Security

- `golang.org/x/crypto` v0.55.0 → v0.58.0: fixes GO-2026-6354 and
  GO-2026-6355 (denial of service through deadlocked established/undecided
  SSH channels). Requires Go 1.26 (the Go toolchain is fetched
  automatically with `GOTOOLCHAIN=auto`).

## [3.0.0] - 2026-10-15

### Fixed

- The test runner accepted only `lamc` 1.18.x, contradicting the package's `^1.18`
  compatibility; it now accepts any 1.x release from 1.18.0 on.

### Removed

- **Breaking:** removed the root `tag()` helper. The package name and version
  are declared in `lamlib.toml`, and the generic top-level function made this
  package impossible to link together with any other package (or application)
  that also declared `tag()`, because all Lam modules share one Go package.

## [2.0.0] - 2026-09-30

### Changed

- Replaced public `try*`/throwing operation pairs with one unsuffixed `Result` API: `connect`, `close`, `run`, `runContext`, `openSession`, `dial`, `dialTcp`, `send`, and `receive`.
- Migrated class constructors from `__init__` to `init` and updated flat, scoped, and historical nested compatibility coverage.
- Updated Lam standard-library composition to the unsuffixed `Os.readFile` and `Crypto.generateEd25519KeyPair` APIs and propagated fallible `Context.expirable` results.
- Raised compiler compatibility to `lamc ^1.18` and bumped the breaking package major to 2.
- Removed avoidable `go!` result-unwrapping bridges while retaining native blocks at the SSH, key-conversion, context, and `net.Conn` boundaries.

### Testing

- Added installed-package loopback composition coverage for encrypted keys,
  sessions, command failures, cancellation, TCP forwarding, and closed states.

## [1.0.0] - 2026-09-13

### Added

- Strict-by-default SSH configuration with password and private-key authentication.
- `known_hosts` and OpenSSH SHA256 fingerprint verification, including composed verification when both are configured.
- Explicitly acknowledged insecure host-key verification opt-out.
- Connect, handshake, and command timeout configuration.
- Typed `SshClient` lifecycle and command APIs with `Result`-returning `try*` variants.
- Separate stdout, stderr, exit code, and success state in `SshCommandResult`.
- Cancellation-aware command execution composed with the standard-library `lamcontext.Context`, including deterministic native-session cleanup through `Context.native()`.
- Re-exported `Context` plus a stateless `SshContext` facade using `simple`,
  `cancellable`, `expirable`, and `cancelled` constructors.
- Reusable `SshSession` templates for environment and stdin configuration.
- Ed25519 user/host key generation sourced from standard-library `lamcrypto.CryptoKeyPair`, with OpenSSH conversion/encryption, private-key parsing, authorized-key derivation, SHA256 fingerprints, and key-file readers.
- Typed SSH `direct-tcpip` connections with bounded reads and explicit errors.
- Uniquely named root implementation modules with package-relative imports, enabling scoped dependents to consume canonical `@lam/ssh` from one ordinary extlibs root.
- Thin parent-relative `ssh/*` compatibility re-exports and a flat `ssh.lam` shim without duplicated implementation.
- Collision-safe canonical exports without a generic root `tag()`; the scaffolded flat shim retains its tag.
- Offline key/config tests, scoped-package composition coverage, and a loopback SSH integration suite covering password/key authentication, host verification, sessions, cancellation, commands, and forwarding.
- `lamc` 1.16.x test runner, package scripts, documentation, and Apache-2.0 licensing.

[2.0.0]: https://github.com/thallium-solutions/lam-ssh/releases/tag/v2.0.0
[1.0.0]: https://github.com/thallium-solutions/lam-ssh/releases/tag/v1.0.0
