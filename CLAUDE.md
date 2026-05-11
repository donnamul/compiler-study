# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal **study log**, not a source tree. It holds notes, `.mlir` experiments, diagrams, and blog drafts produced while working through a Stage 0~4 MLIR-focused roadmap (no time deadlines). There is no build system here and nothing to compile from this directory.

Upstream sources (`llvm-project`, `iree`, `cuda-tile`, ...) live in a sibling workspace at `~/dev/compiler-sources/` and must **not** be checked out, mirrored, or referenced as if they were inside this repo. The `.gitignore` explicitly excludes them.

## Companion guidance

The root `AGENTS.md` and the child `AGENTS.md` files in `notes/` and `experiments/` are authoritative for conventions, anti-patterns, and per-directory rules. Read the relevant one before editing files in that directory rather than re-deriving the conventions.

## Common commands

MLIR tools come from the sibling build at `~/dev/compiler-sources/llvm-project/build/bin/`. Stage 0 verification:

```bash
~/dev/compiler-sources/llvm-project/build/bin/mlir-opt experiments/mlir-basics/hello.mlir
~/dev/compiler-sources/llvm-project/build/bin/mlir-opt experiments/mlir-basics/tensor_ops.mlir
```

Stage 1 verification uses `toyc-chN` binaries from the same build directory with visible IR output. The full `check-mlir` suite is optional and slow; do not run it as part of routine work.

If the MLIR build does not yet exist, the baseline `cmake -G Ninja … -DLLVM_ENABLE_PROJECTS=mlir … --target mlir-opt mlir-translate toyc-ch7` recipe is in `README.md`.

## Roadmap entry points

Active plan is **Stage 0~4** (no time deadlines). Source of truth: `notes/full_plan_for compiler_study.md`. Stage details:

- `notes/stage1-toy-mlir.md` — Toy Tutorial Ch1~7 + parallel C++ track.
- `notes/stage2-iree-deep-read.md` — IREE single-project deep read (backend pipeline view).
- `notes/stage2_5-cuda-tile.md` — NVIDIA/cuda-tile dialect design analysis (dialect design view).
- `notes/stage3-custom-dialect.md` — out-of-tree mini dialect + Linalg lowering + bufferization.

Weekly logs are `notes/weekNN.md` (zero-padded). Deprecated Phase 0/1 plans live in `notes/archive/` — reference only, do not promote.

Lecture PDFs live outside the repo at `/Users/juntaek/Documents/Cmp./Cmp` — *on-demand reference*, not a parallel track.

## Writing conventions

- Active plans use `Stage → Block` headings with no time labels. End task units with a `**산출물:** …` (deliverable) line.
- Weekly notes are `week01.md`, `week02.md`, … (zero-padded).
- Blog drafts use numbered prefixes: `01-…md`, `02-…md`.
- Notes and plans are primarily in **Korean**; blog drafts may be English. Match the surrounding language of the file you are editing.
- Diagrams are tracked as Markdown (Mermaid/text), not exported images.

## Working principle

Every session should leave behind a note, a diagram update, a minimal experiment, or a comparison memo. Do not commit raw clutter, copied doc prose, or scratch files. Verification here is note-driven, not CI-driven — written reflection counts as part of "done."

## Anti-patterns specific to this project

- Do not re-introduce the dropped tracks (v4 → v5 re-alignment): 22-PDF mandatory lecture parallel, Kaleidoscope, Triton internals deep-dive, Torch-MLIR torch-dialect bridge, 16-week deadline, mandatory blog/PR outputs, multi-project (StableHLO + IREE + Triton + cuTile) simultaneous comparison.
- Production MLIR study is **IREE for backend pipeline (Stage 2) + cuda-tile for dialect design (Stage 2.5)**, deliberately split by *perspective*, not multi-project comparison.
- For tile-related questions, the default reference is `NVIDIA/cuda-tile`'s ODS, not Triton internals / cuTile-python / TileGym — those are already-covered ground (kernel-writer side).
- Do not re-promote `notes/archive/phase0-detailed-plan.md` or `phase1-detailed-plan.md` to active.
- Do not add `llvm-project/`, `iree/`, `cuda-tile/`, `triton/`, or CUDA artifacts inside this repo (gitignored for a reason).
- C++ is a known gap; the Stage 1 parallel C++ track is the primary remediation. Do not propose a separate "learn C++ first" track.
