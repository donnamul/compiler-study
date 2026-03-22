# Compiler Study

Personal compiler-study repo centered on MLIR fundamentals, hands-on IR
practice, and compiler theory from lecture notes.

## Goal

- Build solid MLIR fundamentals.
- Study core compiler theory alongside MLIR practice.
- Read real compiler code after the fundamentals are stable.
- Contribute a small PR to an MLIR-related project later in the roadmap.
- Publish at least one technical write-up during the journey.

## Study Direction

- Learn compiler theory and MLIR together instead of treating MLIR as a detached tool.
- Use Toy Tutorial as the first serious implementation track.
- Bring in StableHLO/IREE before deep Triton backend work.
- Keep backend-specific GPU work as a later-phase extension.

## What This Repo Is

- A study log for notes, experiments, diagrams, and comparison memos.
- A lightweight workspace for MLIR/Toy learning outputs.
- A place to track progress across a 16-week roadmap.

## What This Repo Is Not

- Not a source checkout for `llvm-project`, Triton, or other upstream repos.
- Not a dump folder for copied docs or random scratch files.
- Not a CUDA execution environment.

## Repo Layout

```text
.
|-- README.md
|-- blog-drafts/
|-- diagrams/
|-- experiments/
|-- notes/
```

## Local Workspace Layout

```text
~/dev/
|-- compiler-study/
|-- compiler-sources/

~/Documents/Cmp./Cmp/
|-- lecture PDFs
```

- `compiler-study/` holds notes, experiments, diagrams, and drafts.
- `compiler-sources/` holds upstream repositories such as `llvm-project` and,
  in later phases, optional reference projects like `triton` or `Triton-to-tile-IR`.
- `/Users/juntaek/Documents/Cmp./Cmp` holds the compiler lecture PDFs used as the
  theory track.

## Study Flow

1. Read the relevant compiler lecture PDFs for theory.
2. Read MLIR LangRef or Toy Tutorial sections for implementation structure.
3. Run or inspect a minimal experiment under `experiments/`.
4. Write the result back into `notes/`, `diagrams/`, or `blog-drafts/`.
5. Only move to production compiler code after the current phase goals are clear.

## Start Here

- `notes/full_plan_for compiler_study.md` - master roadmap for all phases
- `notes/phase0-detailed-plan.md` - MLIR basics and LangRef entry path
- `notes/phase1-detailed-plan.md` - Toy Tutorial and compiler-theory integration
- `notes/week01.md` - current detailed Phase 0 note example
- `experiments/mlir-basics/` - first files to run with `mlir-opt`

## Current Key Outputs

- `notes/week01.md`
- `notes/week02.md`
- `blog-drafts/01-ai-compiler-landscape.md`
- `diagrams/ai-compiler-ecosystem.md`
- starter files under `experiments/`

## Local Setup Notes

Verified on this machine:

- `python3`
- `pip3`
- `git`
- `clang`
- `cmake`
- `ninja`
- `ccache`
- `rg`
- `sg`

## MLIR Build Baseline

```bash
mkdir -p ~/dev/compiler-sources
cd ~/dev/compiler-sources
git clone --depth 1 https://github.com/llvm/llvm-project.git
mkdir -p llvm-project/build
cd llvm-project/build

cmake -G Ninja ../llvm \
  -DLLVM_ENABLE_PROJECTS=mlir \
  -DLLVM_BUILD_EXAMPLES=ON \
  -DLLVM_TARGETS_TO_BUILD="Native" \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_ENABLE_ASSERTIONS=ON \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++

cmake --build . --target mlir-opt mlir-translate toyc-ch7
```

If the full test suite is needed later:

```bash
cmake --build . --target check-mlir
```

## Later-Phase GPU Backend Notes on macOS

- Treat Triton as a later-phase reference project on this machine.
- Use `TRITON_INTERPRET=1` only when the roadmap reaches backend study.
- Read `Triton-to-tile-IR` locally later, but expect CUDA/Blackwell execution to
  require a separate Linux + NVIDIA environment.

## Verification Pattern

- Phase 0: validate `.mlir` files with `mlir-opt`.
- Phase 1: validate Toy Tutorial work with `toyc-chN` binaries and visible IR output.
- Full upstream validation with `check-mlir` is optional and slow.
- In this repo, notes and comparison memos are part of verification, not just test output.

## Phase 0 Checklist

- [ ] Build `llvm-project` MLIR tools.
- [ ] Run `mlir-opt` on the starter `.mlir` examples.
- [ ] Finish `week01.md` and `week02.md` notes.
- [ ] Complete the MLIR/compiler-theory notes and core diagrams.
- [ ] Publish the first draft of the landscape article.

## Working Principle

Use this repo as a study log, not as a dump folder. Every reading session should
leave one of these behind:

- a note,
- a diagram update,
- a minimal experiment,
- or a comparison memo.
