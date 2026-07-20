#!/usr/bin/env python3
"""Create and verify Phase 13 candidate distribution identity records."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 CI
    import tomli as tomllib


SCHEMA_VERSION = "phase13-candidate-artifact/v1"


def _run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def _read_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def read_versions(repo_root: Path) -> dict[str, str]:
    python_version = _read_toml(repo_root / "sagittarius_py" / "pyproject.toml")["project"]["version"]
    canonical_julia = _read_toml(repo_root / "Sagittarius.jl" / "Project.toml")["version"]
    embedded_julia = _read_toml(
        repo_root / "sagittarius_py" / "sagittarius" / "julia" / "Sagittarius.jl" / "Project.toml"
    )["version"]
    return {
        "python": str(python_version),
        "julia_canonical": str(canonical_julia),
        "julia_embedded": str(embedded_julia),
    }


def create_identity(
    *,
    repo_root: Path,
    expected_version: str,
    candidate_tag: str,
    expected_commit: str,
    source_ref: str,
    main_ref: str,
    run_url: str,
) -> dict[str, Any]:
    head = _run_git(repo_root, "rev-parse", "HEAD").stdout.strip()
    commit = _run_git(repo_root, "rev-parse", expected_commit).stdout.strip()
    if head != commit:
        raise ValueError(f"checked-out HEAD {head} does not equal expected commit {commit}")

    tag_commit = _run_git(repo_root, "rev-list", "-n", "1", candidate_tag).stdout.strip()
    if tag_commit != commit:
        raise ValueError(f"candidate tag {candidate_tag!r} resolves to {tag_commit}, expected {commit}")

    containment = _run_git(repo_root, "merge-base", "--is-ancestor", commit, main_ref, check=False)
    if containment.returncode != 0:
        raise ValueError(f"candidate commit {commit} is not contained in {main_ref}")

    status = _run_git(repo_root, "status", "--porcelain", "--untracked-files=all").stdout
    if status:
        raise ValueError(f"candidate worktree is not clean:\n{status}")

    version_tag = re.compile(rf"(?:^|[-/])v{re.escape(expected_version)}(?:$|[-/])")
    if version_tag.search(candidate_tag) is None:
        raise ValueError(
            f"candidate tag {candidate_tag!r} does not identify version {expected_version!r}"
        )

    versions = read_versions(repo_root)
    mismatches = {name: value for name, value in versions.items() if value != expected_version}
    if mismatches:
        raise ValueError(
            f"candidate version {expected_version!r} does not match package versions: {mismatches}"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "package": "sagittarius-py",
        "version": expected_version,
        "candidate_tag": candidate_tag,
        "commit": commit,
        "source_ref": source_ref,
        "main_ref": main_ref,
        "clean_worktree": True,
        "versions": versions,
        "run_url": run_url,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _wheel_version(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        metadata = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        lines = archive.read(metadata).decode("utf-8").splitlines()
    return next(line.removeprefix("Version: ") for line in lines if line.startswith("Version: "))


def _sdist_version(path: Path) -> str:
    with tarfile.open(path) as archive:
        pkg_info = next(member for member in archive.getmembers() if member.name.endswith("/PKG-INFO"))
        extracted = archive.extractfile(pkg_info)
        if extracted is None:
            raise ValueError(f"unable to read PKG-INFO from {path}")
        lines = extracted.read().decode("utf-8").splitlines()
    return next(line.removeprefix("Version: ") for line in lines if line.startswith("Version: "))


def _distribution_paths(dist_dir: Path) -> tuple[Path, Path]:
    wheels = sorted(dist_dir.glob("*.whl"))
    sdists = sorted(dist_dir.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError(
            f"expected exactly one wheel and one sdist in {dist_dir}, "
            f"found wheels={wheels}, sdists={sdists}"
        )
    return wheels[0], sdists[0]


def create_manifest(identity: dict[str, Any], dist_dir: Path) -> dict[str, Any]:
    if identity.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported identity schema: {identity.get('schema_version')!r}")
    wheel, sdist = _distribution_paths(dist_dir)
    versions = {wheel.name: _wheel_version(wheel), sdist.name: _sdist_version(sdist)}
    wrong_versions = {name: version for name, version in versions.items() if version != identity["version"]}
    if wrong_versions:
        raise ValueError(f"distribution versions do not match candidate: {wrong_versions}")
    distributions = {}
    for path, kind in ((wheel, "wheel"), (sdist, "sdist")):
        distributions[path.name] = {
            "kind": kind,
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
            "version": versions[path.name],
        }
    return {**identity, "distributions": distributions}


def verify_manifest(
    manifest: dict[str, Any],
    dist_dir: Path,
    *,
    expected_version: str | None = None,
    expected_commit: str | None = None,
    expected_tag: str | None = None,
) -> dict[str, Any]:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported candidate manifest schema: {manifest.get('schema_version')!r}")
    for field, expected in (
        ("version", expected_version),
        ("commit", expected_commit),
        ("candidate_tag", expected_tag),
    ):
        if expected is not None and manifest.get(field) != expected:
            raise ValueError(f"candidate {field} is {manifest.get(field)!r}, expected {expected!r}")

    wheel, sdist = _distribution_paths(dist_dir)
    actual_paths = {wheel.name: wheel, sdist.name: sdist}
    recorded = manifest.get("distributions")
    if not isinstance(recorded, dict) or set(recorded) != set(actual_paths):
        raise ValueError(
            f"candidate distribution filenames differ: recorded={sorted(recorded or {})}, "
            f"actual={sorted(actual_paths)}"
        )
    for name, path in actual_paths.items():
        entry = recorded[name]
        actual_digest = _sha256(path)
        if entry.get("sha256") != actual_digest:
            raise ValueError(
                f"SHA-256 mismatch for {name}: recorded={entry.get('sha256')}, actual={actual_digest}"
            )
        if entry.get("size_bytes") != path.stat().st_size:
            raise ValueError(f"size mismatch for {name}")
        actual_version = _wheel_version(path) if path.suffix == ".whl" else _sdist_version(path)
        if entry.get("version") != actual_version or actual_version != manifest["version"]:
            raise ValueError(f"version mismatch for {name}: {actual_version}")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "verified",
        "version": manifest["version"],
        "candidate_tag": manifest["candidate_tag"],
        "commit": manifest["commit"],
        "distributions": {
            name: {"sha256": entry["sha256"], "size_bytes": entry["size_bytes"]}
            for name, entry in sorted(recorded.items())
        },
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    identity = subparsers.add_parser("identity")
    identity.add_argument("--repo-root", type=Path, required=True)
    identity.add_argument("--expected-version", required=True)
    identity.add_argument("--candidate-tag", required=True)
    identity.add_argument("--expected-commit", required=True)
    identity.add_argument("--source-ref", required=True)
    identity.add_argument("--main-ref", default="origin/main")
    identity.add_argument("--run-url", default="")
    identity.add_argument("--output", type=Path, required=True)
    manifest = subparsers.add_parser("manifest")
    manifest.add_argument("--identity", type=Path, required=True)
    manifest.add_argument("--dist-dir", type=Path, required=True)
    manifest.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--dist-dir", type=Path, required=True)
    verify.add_argument("--expected-version")
    verify.add_argument("--expected-commit")
    verify.add_argument("--expected-tag")
    verify.add_argument("--output", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "identity":
        payload = create_identity(
            repo_root=args.repo_root.resolve(),
            expected_version=args.expected_version,
            candidate_tag=args.candidate_tag,
            expected_commit=args.expected_commit,
            source_ref=args.source_ref,
            main_ref=args.main_ref,
            run_url=args.run_url,
        )
        _write_json(args.output, payload)
    elif args.command == "manifest":
        payload = create_manifest(_load_json(args.identity), args.dist_dir)
        _write_json(args.output, payload)
    else:
        payload = verify_manifest(
            _load_json(args.manifest),
            args.dist_dir,
            expected_version=args.expected_version,
            expected_commit=args.expected_commit,
            expected_tag=args.expected_tag,
        )
        if args.output:
            _write_json(args.output, payload)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
