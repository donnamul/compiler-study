# PROJECT KNOWLEDGE BASE

## OVERVIEW
Study repo for MLIR fundamentals, compiler-theory notes, Toy Tutorial work, and later-phase production compiler comparisons.

## STRUCTURE
```text
compiler-study/
├── notes/         # master roadmap, phase plans, weekly notes
├── experiments/   # .mlir files and small study scripts
├── diagrams/      # markdown diagrams, mostly Mermaid/text
├── blog-drafts/   # public-facing writeups
└── README.md      # repo purpose, build baseline, working principle
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Understand repo purpose | `README.md` | Start here; contains workspace split and build baseline |
| See the master roadmap | `notes/full_plan_for compiler_study.md` | Source of truth for Stage 0~4 ordering |
| Execute current stage | `notes/stage1-toy-mlir.md`, `stage2-iree-deep-read.md`, `stage3-custom-dialect.md` | Block-level plans with 산출물 |
| Review weekly learning state | `notes/week01.md`, `notes/week02.md`, ... | Study-log style notes |
| Look up an old plan | `notes/archive/` | Deprecated Phase 0/1 plans; reference only |
| Run MLIR basics | `experiments/mlir-basics/` | Primary Phase 0 verification area |
| Find visual summaries | `diagrams/` | Keep diagrams as markdown, not binaries |

## CONVENTIONS
- This repo is a study log, not a dump folder; every session should leave a note, diagram update, minimal experiment, or comparison memo.
- Keep source code checkouts outside this repo: `llvm-project` lives under `~/dev/compiler-sources/`, not here.
- Internal notes/plans are mainly Korean; blog drafts may be English.
- Plans use day-level granularity with time estimates and an explicit `산출물` section.
- Weekly notes use `weekNN.md`; blog drafts use numbered prefixes like `01-...md`.

## ANTI-PATTERNS (THIS PROJECT)
- Do not re-insert the dropped tracks: 22-PDF mandatory lecture parallel, Kaleidoscope, Triton internals deep-dive, Torch-MLIR torch-dialect bridge (Legato sits in Inductor's slot), 16-week deadline, mandatory blog/PR outputs, multi-project (StableHLO + IREE + Triton + cuTile) simultaneous comparison. These were dropped on purpose during the v5 re-alignment.
- Do not re-promote `notes/archive/phase0-detailed-plan.md` or `phase1-detailed-plan.md` to active.
- Do not commit raw clutter; convert readings into notes, experiments, diagrams, or memos.
- Do not assume `llvm-project/`, `iree/`, or CUDA artifacts belong inside this repo.

## UNIQUE STYLES
- The roadmap is **Stage 0~4 with no time labels**: Toy → IREE single-project deep read → out-of-tree custom dialect + bufferization → retrospective.
- Production MLIR study is single-project (IREE), not multi-project comparison.
- Diagrams are tracked as `.md` files, typically Mermaid/text, not exported images.
- Verification is lightweight and note-driven rather than CI-driven.

## COMMANDS
```bash
# MLIR tools live in the sibling source workspace
/Users/juntaek/dev/compiler-sources/llvm-project/build/bin/mlir-opt experiments/mlir-basics/hello.mlir
/Users/juntaek/dev/compiler-sources/llvm-project/build/bin/mlir-opt experiments/mlir-basics/control_flow.mlir
/Users/juntaek/dev/compiler-sources/llvm-project/build/bin/mlir-opt experiments/mlir-basics/tensor_ops.mlir

# Full MLIR suite is optional and slow
cmake --build /Users/juntaek/dev/compiler-sources/llvm-project/build --target check-mlir
```

## NOTES
- On this machine, Triton is later-phase study/reference work; CUDA execution is not the normal path.
- If you add repo guidance, prefer `notes/` or `experiments/` child AGENTS.md files over bloating this root file.
