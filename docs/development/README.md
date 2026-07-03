# Development Workflows

This directory contains reusable development-process templates for Sagittarius contributors and AI agents. These documents are operational workflow aids, not system architecture references or public capability claims.

Use these templates together with:

- [`../SOP.md`](../SOP.md) for scientific computing lifecycle principles;
- [`../status.md`](../status.md) for documentation maintenance triggers;
- [`../../AGENTS.md`](../../AGENTS.md) for repository-level AI agent instructions;
- [`../reference/development-sop.md`](../reference/development-sop.md) for logging, diagnostics, artifact, manifest, benchmark, and claim contracts.

## Templates

- [Agent workflow template](agent-workflow-template.md): reusable workflow for feature, development, release, benchmark, and documentation branches.
- [Prompt context standards](prompt-context.md): bilingual prompt templates for starting, resuming, implementing, reviewing, and closing AI-assisted branch work.

## Usage

Branch owners may copy the customization block from the template into a pull request, issue, or branch-local planning document. For long-running branches, use a branch-local file such as `docs/development/branches/<branch-name>.md` and decide before merge whether to delete it, retain it, or extract durable content into formal docs or the PR description. Tailor the required context, tests, artifacts, and handoff requirements for the specific branch without removing the baseline scientific correctness, reproducibility, documentation, and evidence gates.

Development workflow docs may include English and Chinese versions of templates when that improves reuse across contributors. Keep the technical requirements aligned between language versions.
