#!/usr/bin/env python3
"""Validate Sagittarius Markdown links and stable SPEC documentation metadata."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

METADATA_FIELDS = ("Spec ID", "Status", "Roadmap", "Version", "Last reviewed")
SPEC_ID_RE = re.compile(r"^SPEC-[A-Z]+-\d{3}$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
STATUS_ENTRY_RE = re.compile(
    r"^\|\s+\x60(?P<spec>SPEC-[A-Z]+-\d{3})\x60\s+\|\s+\[[^\]]+\]\((?P<target>[^)]+)\)",
    re.MULTILINE,
)


def markdown_files(docs_root: Path) -> Iterable[Path]:
    return sorted(path for path in docs_root.rglob("*.md") if path.is_file())


def metadata_for(path: Path) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[:80]:
        if line.startswith("## "):
            break
        for field in METADATA_FIELDS:
            prefix = f"{field}:"
            if line.startswith(prefix):
                metadata[field] = line[len(prefix):].strip()
    return metadata


def local_link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    else:
        target = target.split(maxsplit=1)[0] if target else target
    if not target or target.startswith(("#", "mailto:", "http://", "https://")):
        return None
    return target.split("#", maxsplit=1)[0]


def validate_docs(docs_root: Path) -> list[str]:
    docs_root = docs_root.resolve()
    errors: list[str] = []
    specs: dict[str, Path] = {}

    for path in markdown_files(docs_root):
        metadata = metadata_for(path)
        spec_id = metadata.get("Spec ID")
        if spec_id:
            missing = [field for field in METADATA_FIELDS if not metadata.get(field)]
            if missing:
                errors.append(f"{path}: SPEC metadata is missing {', '.join(missing)}.")
            elif not SPEC_ID_RE.fullmatch(spec_id.strip(chr(96))):
                errors.append(f"{path}: invalid Spec ID {spec_id!r}.")
            else:
                normalized_id = spec_id.strip(chr(96))
                previous = specs.setdefault(normalized_id, path)
                if previous != path:
                    errors.append(f"{path}: duplicate Spec ID {normalized_id}; first declared in {previous}.")

        in_fence = False
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.strip().startswith(chr(96) * 3):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for match in LINK_RE.finditer(line):
                target = local_link_target(match.group(1))
                if target is None:
                    continue
                destination = (path.parent / target).resolve()
                if not destination.exists():
                    errors.append(f"{path}:{line_number}: local Markdown link target does not exist: {target}")

    status_path = docs_root / "development" / "status.md"
    if not status_path.is_file():
        errors.append(f"{status_path}: required documentation status index is missing.")
        return errors

    entries = [(match.group("spec"), match.group("target")) for match in STATUS_ENTRY_RE.finditer(
        status_path.read_text(encoding="utf-8")
    )]
    for spec_id, spec_path in specs.items():
        matching_targets = [target for entry_id, target in entries if entry_id == spec_id]
        if not matching_targets:
            errors.append(f"{status_path}: missing status entry for {spec_id}.")
            continue
        if not any((status_path.parent / target.split('#', maxsplit=1)[0]).resolve() == spec_path.resolve()
                   for target in matching_targets):
            errors.append(f"{status_path}: {spec_id} does not link to {spec_path.relative_to(docs_root)}.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs",
        help="Documentation root to validate (default: repository docs directory).",
    )
    args = parser.parse_args()
    errors = validate_docs(args.docs_root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Documentation governance checks passed for {args.docs_root.resolve()}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

