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
| See the master roadmap | `notes/full_plan_for compiler_study.md` | Source of truth for phase ordering |
| Execute current phase | `notes/phase0-detailed-plan.md`, `notes/phase1-detailed-plan.md` | Day-by-day plans with outputs |
| Review weekly learning state | `notes/week01.md`, `notes/week02.md` | Study-log style notes |
| Run MLIR basics | `experiments/mlir-basics/` | Primary Phase 0 verification area |
| Find visual summaries | `diagrams/` | Keep diagrams as markdown, not binaries |

## CONVENTIONS
- This repo is a study log, not a dump folder; every session should leave a note, diagram update, minimal experiment, or comparison memo.
- Keep source code checkouts outside this repo: `llvm-project` lives under `~/dev/compiler-sources/`, not here.
- Internal notes/plans are mainly Korean; blog drafts may be English.
- Plans use day-level granularity with time estimates and an explicit `산출물` section.
- Weekly notes use `weekNN.md`; blog drafts use numbered prefixes like `01-...md`.

## ANTI-PATTERNS (THIS PROJECT)
- Do not pull Triton or `torch.compile` backend deep-dives into early phases; Toy + LangRef + compiler theory come first.
- Do not treat optional later-phase backend work as required current-phase work.
- Do not commit raw clutter; convert readings into notes, experiments, diagrams, or memos.
- Do not assume `llvm-project/` or CUDA artifacts belong inside this repo.

## UNIQUE STYLES
- The roadmap is MLIR-first: Toy, StableHLO, and IREE appear before Triton backend deep dives.
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
