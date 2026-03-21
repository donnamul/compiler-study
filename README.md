# Compiler Study

Phase 0 setup for a 16-week compiler study plan focused on MLIR, Triton,
and `triton-lang/Triton-to-tile-IR`.

## Goal

- Build solid MLIR fundamentals.
- Read real compiler code instead of tutorial-only examples.
- Contribute a small PR to `triton-lang/Triton-to-tile-IR`.
- Publish at least one technical write-up during the journey.

## Current Focus

- Phase 0: environment setup, ecosystem mapping, and compiler pipeline literacy.
- Local machine mode: macOS study-first setup.
- Constraint: CUDA Tile IR execution is not available on this machine.

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
```

- `compiler-study/` holds notes, experiments, diagrams, and drafts.
- `compiler-sources/` holds upstream repositories such as `llvm-project`,
  `triton`, and `Triton-to-tile-IR`.

## Phase 0 Outputs

- `notes/week01.md`
- `notes/week02.md`
- `blog-drafts/01-ai-compiler-landscape.md`
- `diagrams/ai-compiler-ecosystem.md`
- `diagrams/torch-compile-to-mlir-mapping.md`
- `diagrams/triton-ptx-vs-tileir.md`
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

## Triton Study Mode on macOS

- Treat Triton as code-reading and interpreter-mode tooling on this machine.
- Use `TRITON_INTERPRET=1` for study-oriented experiments.
- Read `Triton-to-tile-IR` locally, but expect CUDA/Blackwell execution to require
  a separate Linux + NVIDIA environment.

## Phase 0 Checklist

- [ ] Build `llvm-project` MLIR tools.
- [ ] Clone `triton-lang/triton`.
- [ ] Clone `triton-lang/Triton-to-tile-IR`.
- [ ] Run `mlir-opt` on the starter `.mlir` examples.
- [ ] Finish `week01.md` and `week02.md` notes.
- [ ] Complete the ecosystem and pipeline diagrams.
- [ ] Publish the first draft of the landscape article.

## Working Principle

Use this repo as a study log, not as a dump folder. Every reading session should
leave one of these behind:

- a note,
- a diagram update,
- a minimal experiment,
- or a comparison memo.
