# @lam/ssh

A typed, production-minded SSH client package for [Lammergeier](https://github.com/thallium-solutions/lammergeier-lang), backed by `golang.org/x/crypto/ssh` v0.55.0.

`@lam/ssh` provides password and Ed25519 private-key authentication, strict host-key verification, separate stdout/stderr command results, cancellation-aware execution, reusable session templates, Ed25519 key utilities, and typed `direct-tcpip` connections. It composes with the `lamcrypto` and `lamcontext` standard-library modules and targets `lamc` 1.16.x.

## Installation

### Local path

```bash
lamc install /path/to/lam-ssh
```

For development without installation, the retained flat shim can be loaded directly; use `from ssh import ...` in that local-only case:

```bash
lamc build app.lam --extlibs /path/to/lam-ssh --run
```

Use `lamc install` when testing the canonical scoped `from @lam/ssh import ...` form.

### Git

```bash
lamc install https://github.com/thallium-solutions/lam-ssh.git@v1.0.0
```

Pin a tag or commit in reproducible projects rather than tracking a branch.

### Registry

```bash
lamc install @lam/ssh@^1.0.0
```

The scoped package root exports the public API. The generated `ssh.lam` shim remains available for local flat-module development and retains its scaffolded `tag()` smoke test. Import the canonical package with:

```lammergeier
from @lam/ssh import SshConfig, SshClient, SshCommandResult
```

The canonical root intentionally does not export generic `tag()`, allowing a dependent scoped package to define its own `tag` without a generated Go-symbol collision.

## Package layout and composition

```text
lam-ssh/
├── __init__.lam          # canonical @lam/ssh exports; no tag()
├── ssh.lam               # generated flat-mode compatibility shim + tag()
├── ssh_config.lam        # uniquely named root implementation
├── ssh_context.lam
├── ssh_key.lam
├── ssh_client.lam
└── ssh/                  # historical nested-import compatibility only
    ├── __init__.lam
    ├── config.lam
    ├── context.lam
    ├── key.lam
    └── client.lam
```

Root implementation modules use package-relative imports such as `from .ssh_config import SshConfig`. The canonical package therefore composes from a normal `extlibs/@lam/ssh` installation with only the ordinary `extlibs` search root. Thin nested modules use parent-relative imports and contain no duplicate implementation.

## Password authentication and pinned host key

Host verification is strict by default. A config is invalid until it has a `known_hosts` file, a SHA256 host-key fingerprint, or an explicit insecure opt-out.

```lammergeier
from @lam/ssh import SshConfig, SshClient, SshCommandResult

func main() {
    config: SshConfig = SshConfig("ssh.example.com", "deploy", 22)
    config.withPassword("read-this-from-a-secret-store")
    config.withHostKeyFingerprint("SHA256:REPLACE_WITH_THE_VERIFIED_FINGERPRINT")
    config.withTimeouts(5000, 5000, 30000)
    config.withEnv("LANG", "C")

    client: SshClient = SshClient.connect(config)
    result: SshCommandResult = client.run("uname -a")
    print(result.stdout)
    if not result.success {
        print(f"remote command exited {result.exitCode}")
    }
    client.close()
}
```

A nonzero remote exit status is still a successful SSH operation: `tryRun` returns `Result.Ok(SshCommandResult)` with `success == False`. Connection, protocol, cancellation, and missing-exit-status failures return `Result.Err`.

## Private-key authentication

Key APIs return `Result`, allowing `?` propagation without exposing key material in errors.

```lammergeier
from lamerrors import Result
from @lam/ssh import SshConfig, SshClient, SshKeyPair, SshCommandResult

func deploy() -> Result {
    pair: SshKeyPair = SshKeyPair.fromPrivateKeyFile(
        "/home/deploy/.ssh/id_ed25519",
        "optional-key-passphrase",
    )?

    config: SshConfig = SshConfig("ssh.example.com", "deploy")
    config.withPrivateKey(pair.privateKeyPem, "optional-key-passphrase")
    config.withKnownHosts("/home/deploy/.ssh/known_hosts")

    client: SshClient = SshClient.tryConnect(config)?
    result: SshCommandResult = client.tryRun("id")?
    client.close()
    return Result.Ok(result)
}
```

Generate user or host Ed25519 keys in OpenSSH format:

```lammergeier
pair: SshKeyPair = SshKeyPair.generateEd25519("deploy@example")?
hostPair: SshKeyPair = SshKeyPair.generateHostEd25519("host.example.com")?
print(pair.authorizedPublicKey())
print(pair.sha256Fingerprint())
```

Secure Ed25519 generation comes from `Crypto.tryGenerateEd25519KeyPair()` and its portable `CryptoKeyPair`. `@lam/ssh` only converts that key into OpenSSH private-key, authorized-key, and fingerprint forms through `x/crypto/ssh`; passphrases still produce encrypted OpenSSH private keys.

`privateKeyPem` is sensitive. Write private keys only to a securely permissioned destination (normally mode `0600`), and never print a key pair or populated config.

## Host-key verification

Use one or both strict mechanisms:

```lammergeier
config.withKnownHosts("/home/app/.ssh/known_hosts")
config.withHostKeyFingerprint("SHA256:verified-base64-fingerprint")
```

When both are configured, both checks must pass. `known_hosts` parsing, hashed host entries, non-default port matching, and key-change errors use the behavior of `x/crypto/ssh/knownhosts`.

The only opt-out is intentionally explicit:

```lammergeier
config.insecureSkipHostKeyVerification(True)
```

Do not use that setting in production. It permits machine-in-the-middle attacks. Validation also rejects mixing the insecure switch with strict verification inputs.

## Context cancellation and expiration

Normal `run`/`tryRun` derives a standard-library expirable `Context` from `config.commandTimeoutMs` (`0` disables that timeout). For caller-controlled cancellation, pass `lamcontext.Context` directly; it is re-exported by `@lam/ssh`:

```lammergeier
from lamerrors import Result
from @lam/ssh import Context, SshClient, SshCommandResult

func bounded(client: SshClient) -> Result {
    root: Context = Context.simple()
    requestContext: Context = root.expirable(2, "seconds")
    result: Result[SshCommandResult] = client.tryRunContext(
        requestContext,
        "long-running-command",
    )
    requestContext.cancel("request complete")
    return result
}
```

The SSH boundary calls `Context.native()` to obtain the underlying Go `context.Context`. Cancellation closes the native SSH session and waits for its command waiter to finish, preventing abandoned session goroutines while preserving stdlib expiration, cancellation reasons, and parent/child propagation.

`SshContext.simple()`, `SshContext.cancellable()`, `SshContext.expirable(expiration, unit)`, and `SshContext.cancelled(reason)` are stateless convenience constructors. They return `Context` values and own no separate context state; new code may use `Context` directly.

## Reusable sessions

`SshSession` is a reusable command template. Every run opens a fresh native Go SSH session while preserving the template's environment and stdin settings.

```lammergeier
session = client.openSession()
session.env("APP_ENV", "production").stdin("input\n")
first = session.run("read value; printf '%s:%s' \"$APP_ENV\" \"$value\"")

session.clearStdin()
second = session.run("printf '%s' \"$APP_ENV\"")
session.close()
```

Closing a session template does not close its parent client. Reuse is intended for sequential calls; create separate templates for concurrent mutable environment/stdin configuration.

## Direct TCP dialing through SSH

For database clients and other protocols that can consume a stream, `direct-tcpip` is exposed as a typed connection:

```lammergeier
connection = client.dialTcp("127.0.0.1", 5432)
connection.send("protocol bytes")
reply = connection.recv(4096)
connection.close()
```

Only `tcp`, `tcp4`, and `tcp6` are accepted by `tryDial`. Reads are bounded (maximum 16 MiB per call), close is idempotent, and failures use `Result`. SSH channel connections may report that deadlines are unsupported; `setDeadline` returns that as `Result.Err` rather than hiding it.

## API overview

- `SshConfig`: fluent password/private-key, port, timeout, environment, `known_hosts`, fingerprint, and explicit insecure settings; `validate()` returns `Result[SshConfig]`.
- `SshClient`: `connect`/`tryConnect`, `connected`, `close`/`tryClose`, `run`/`tryRun`, context variants, reusable sessions, and typed TCP dialing.
- `SshCommandResult`: `stdout`, `stderr`, `exitCode`, and `success`.
- `SshSession`: `env`, `stdin`, timeout, run/context variants, clear, state, and close APIs.
- `SshKey` / `SshKeyPair`: `lamcrypto`-backed Ed25519 generation, OpenSSH parsing/conversion, authorized-key derivation, SHA256 fingerprints, and public/private key-file readers.
- `Context`: re-exported `lamcontext.Context` accepted by all context-aware client/session methods; `native()` is used only at the Go SSH boundary.
- `SshContext`: deprecated stateless compatibility facade whose static constructors return `Context` values.
- `SshTcpConn`: bounded send/receive, address, deadline, and close APIs over SSH direct TCP channels.

## Security guidance

- Verify fingerprints out of band or maintain `known_hosts`; never learn a production key by accepting the first connection blindly.
- Load passwords and key passphrases from a secret manager or protected environment, not source control.
- Do not log or serialize `SshConfig.privateKeyPem`, `SshConfig.password`, `SshKeyPair.privateKeyPem`, or passphrases.
- Do not concatenate untrusted text into remote shell commands. Prefer fixed commands with tightly validated arguments.
- Set finite connect, handshake, and command timeouts, and close clients, sessions, and forwarded connections promptly.
- Restrict the SSH account and server-side forwarding policy to the minimum privileges required.
- Treat an unexpected host-key mismatch as a security incident until rotation is independently confirmed.

## Development

Tests are entirely offline or bind only to loopback. The runner requires `lamc` 1.16.x and separately exercises the canonical package with one ordinary extlibs root, the flat shim, nested compatibility modules, and a generated scoped dependent with its own `config.lam` and `tag()`:

```bash
python3 tests/run_tests.py
# or
lamc lib run test
```

Format checks are available through `lamc lib run check`.

The package composes directly with Lammergeier 1.16's `lamcrypto.Crypto` / `CryptoKeyPair` for secure Ed25519 generation and `lamcontext.Context` for cancellation trees, unit-aware expiration, reasons, and native Go interop. `go!` remains confined to the unavoidable `x/crypto/ssh`, `net.Conn`, stream, OpenSSH conversion, and `Context.native()` boundaries; fallible APIs use `lamerrors`, and file reads use `lamos`.
