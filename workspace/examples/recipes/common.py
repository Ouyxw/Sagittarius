"""Shared helpers for the Phase 15 executable experiment recipes.

Recipes persist ordinary Sagittarius ``result-artifact/v1`` outputs. They do
not introduce a recipe-specific result schema; the adjacent manifest is only a
convenient inspection copy of the manifest embedded in each result artifact.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class RecipeRun:
    artifact_path: Path
    manifest_path: Path
    result: Any


def output_directory(recipe_name: str) -> Path:
    parser = argparse.ArgumentParser(description=f"Run the Sagittarius {recipe_name} recipe.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts") / recipe_name,
        help="Directory for the result artifact and manifest copy.",
    )
    return parser.parse_args().output_dir


def save_recipe_result(result: Any, output_dir: Path, recipe_name: str) -> RecipeRun:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / f"{recipe_name}.result.json"
    manifest_path = output_dir / f"{recipe_name}.run-manifest.json"
    result.save(str(artifact_path))
    manifest_path.write_text(json.dumps(result.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return RecipeRun(artifact_path=artifact_path, manifest_path=manifest_path, result=result)


def print_recipe_summary(recipe_name: str, run: RecipeRun, metrics: Mapping[str, Any]) -> None:
    print(f"recipe: {recipe_name}")
    print(f"result artifact: {run.artifact_path}")
    print(f"manifest copy: {run.manifest_path}")
    for name, value in metrics.items():
        print(f"{name}: {value}")
