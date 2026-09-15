#!/usr/bin/env python3
"""Compile and run every consumer-style Lam test with lamc 1.16.x."""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parent.parent
TESTS = pathlib.Path(__file__).resolve().parent
REQUIRED_MAJOR_MINOR = (1, 16)
VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


def require_lamc() -> str:
    lamc = shutil.which("lamc")
    if lamc is None:
        raise SystemExit("error: lamc is required but was not found on PATH")

    try:
        completed = subprocess.run(
            [lamc, "version"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"error: could not execute 'lamc version': {exc}") from exc

    version = completed.stdout.strip()
    match = VERSION_RE.fullmatch(version)
    if match is None:
        raise SystemExit(f"error: unrecognized lamc version output: {version!r}")
    major_minor = (int(match.group(1)), int(match.group(2)))
    if major_minor != REQUIRED_MAJOR_MINOR:
        raise SystemExit(
            f"error: @lam/ssh tests require lamc 1.16.x; found {version}"
        )
    return lamc


def write_composition_fixture(extlibs: pathlib.Path) -> None:
    """Create a second scoped package that consumes canonical @lam/ssh."""
    package = extlibs / "@lam" / "ssh_composition"
    package.mkdir(parents=True)
    (package / "config.lam").write_text(
        """class CompositionConfig {
    func __init__(self, name: str = "sftp-shape") {
        self.name: str = name
    }
}
""",
        encoding="utf-8",
    )
    (package / "__init__.lam").write_text(
        """from lamerrors import Result
from .config import CompositionConfig
from @lam/ssh import SshKeyPair

func generatedKeyType() -> Result[str] {
    pair: SshKeyPair = SshKeyPair.generateEd25519("scoped-composition", "")?
    return Result.Ok(pair.publicKey.keyType)
}

func tag() -> str {
    return "@lam/ssh_composition"
}
""",
        encoding="utf-8",
    )


def main() -> int:
    lamc = require_lamc()
    cases = sorted(TESTS.glob("test_*.lam"))
    if not cases:
        print("error: no Lam test cases found", file=sys.stderr)
        return 2

    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="lam-ssh-tests-") as temporary:
        temp_root = pathlib.Path(temporary)
        extlibs = temp_root / "extlibs"
        package_root = extlibs / "@lam" / "ssh"
        package_root.parent.mkdir(parents=True)
        shutil.copytree(
            ROOT,
            package_root,
            ignore=shutil.ignore_patterns(
                ".git", "__pycache__", "*.pyc", "build", "extlibs"
            ),
        )
        write_composition_fixture(extlibs)

        for case in cases:
            output = temp_root / case.stem
            flat_mode = case.name in {
                "test_flat_export.lam",
                "test_nested_compatibility.lam",
            }
            extlib_root = package_root if flat_mode else extlibs
            command = [
                lamc,
                "build",
                str(case),
                "--run",
                "--no-cache",
                "--extlibs",
                str(extlib_root),
                "-o",
                str(output),
            ]
            print(f"==> {case.name}", flush=True)
            try:
                completed = subprocess.run(command, cwd=ROOT, timeout=180)
            except subprocess.TimeoutExpired:
                print(f"FAIL {case.name}: timed out after 180 seconds", file=sys.stderr)
                failures.append(case.name)
                continue
            except OSError as exc:
                print(f"FAIL {case.name}: {exc}", file=sys.stderr)
                failures.append(case.name)
                continue
            if completed.returncode != 0:
                failures.append(case.name)

    if failures:
        print(
            f"\n{len(failures)} test file(s) failed: {', '.join(failures)}",
            file=sys.stderr,
        )
        return 1
    print(f"\n{len(cases)} test file(s) passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
