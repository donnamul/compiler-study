# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal **study log**, not a source tree. It holds notes, `.mlir` experiments, diagrams, and blog drafts produced while working through a 16-week MLIR-first compiler roadmap. There is no build system here and nothing to compile from this directory.

Upstream sources (`llvm-project`, optionally `triton`, `Triton-to-tile-IR`) live in a sibling workspace at `~/dev/compiler-sources/` and must **not** be checked out, mirrored, or referenced as if they were inside this repo. The `.gitignore` explicitly excludes them.

## Companion guidance

The root `AGENTS.md` and the child `AGENTS.md` files in `notes/` and `experiments/` are authoritative for conventions, anti-patterns, and per-directory rules. Read the relevant one before editing files in that directory rather than re-deriving the conventions.

## Common commands

MLIR tools come from the sibling build at `~/dev/compiler-sources/llvm-project/build/bin/`. Typical Phase 0 verification:

```bash
~/dev/compiler-sources/llvm-project/build/bin/mlir-opt experiments/mlir-basics/hello.mlir
~/dev/compiler-sources/llvm-project/build/bin/mlir-opt experiments/mlir-basics/tensor_ops.mlir
```

Phase 1 verification uses `toyc-chN` binaries from the same build directory with visible IR output. The full `check-mlir` suite is optional and slow; do not run it as part of routine work.

If the MLIR build does not yet exist, the baseline `cmake -G Ninja … -DLLVM_ENABLE_PROJECTS=mlir … --target mlir-opt mlir-translate toyc-ch7` recipe is in `README.md`.

## Roadmap entry points

- `notes/full_plan_for compiler_study.md` — master roadmap, source of truth for phase ordering.
- `notes/phase0-detailed-plan.md` — current phase: MLIR basics + LangRef.
- `notes/phase1-detailed-plan.md` — next phase: Toy Tutorial + compiler theory.
- `notes/weekNN.md` — weekly study log (zero-padded).

Lecture PDFs live outside the repo at `/Users/juntaek/Documents/Cmp./Cmp` — reference them, do not mirror them in.

## Writing conventions

- Plans follow a `Phase -> Week -> Day` structure with explicit time estimates and end task units with a `**산출물:** …` (deliverable) line.
- Weekly notes are `week01.md`, `week02.md`, … (zero-padded).
- Blog drafts use numbered prefixes: `01-…md`, `02-…md`.
- Notes and plans are primarily in **Korean**; blog drafts may be English. Match the surrounding language of the file you are editing.
- Diagrams are tracked as Markdown (Mermaid/text), not exported images.

## Working principle

Every session should leave behind a note, a diagram update, a minimal experiment, or a comparison memo. Do not commit raw clutter, copied doc prose, or scratch files. Verification here is note-driven, not CI-driven — written reflection counts as part of "done."

## Anti-patterns specific to this project

- Do not pull Triton, CUDA, or `torch.compile` backend work into Phase 0/1. The roadmap is MLIR-first: Toy → StableHLO → IREE come before Triton backend study.
- Do not treat optional later-phase backend work as required current-phase work.
- Do not add `llvm-project/`, `triton/`, or CUDA artifacts inside this repo (gitignored for a reason).
- Do not skip the distinction between master plan, phase plan, and weekly note — they serve different purposes.
