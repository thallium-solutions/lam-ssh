# Changelog

All notable changes to `@lam/ssh` are documented here.

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

[1.0.0]: https://github.com/thallium-solutions/lam-ssh/releases/tag/v1.0.0
