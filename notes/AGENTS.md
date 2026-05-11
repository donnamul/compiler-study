# NOTES KNOWLEDGE BASE

## OVERVIEW
`notes/` holds the active roadmap (Stage 0~4), stage execution docs, and weekly study logs.

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Master plan | `full_plan_for compiler_study.md` | Stage 0~4 — single source of truth for sequencing |
| Stage 1 execution | `stage1-toy-mlir.md` | Toy Ch1~7 + parallel C++ track |
| Stage 2 execution | `stage2-iree-deep-read.md` | IREE single-project deep read |
| Stage 3 execution | `stage3-custom-dialect.md` | Out-of-tree mini dialect + Linalg lowering + bufferization |
| Weekly log | `week01.md`, `week02.md`, ... | Session outputs and self-checks |
| Old plans | `archive/` | Deprecated Phase 0/1 plans, kept for reference only |

## CONVENTIONS
- Active plan is **Stage 0~4**. Do not reintroduce the Phase/Block-numbered ordering from the archived plans.
- Stage docs use loose "Block N" headings inside a stage. Time labels and date deadlines are not used.
- End meaningful task units with `**산출물:** ...`.
- Weekly note files stay zero-padded: `week01.md`, `week02.md`, ...
- Prefer self-explanations, comparisons, and review questions over copied doc prose.
- Korean is primary for notes/plans. Blog drafts may be English.

## ANTI-PATTERNS
- Do not re-insert the dropped tracks: 22-PDF mandatory lecture parallel, Kaleidoscope, Triton internals deep-dive, multi-project (StableHLO + IREE + Triton + cuTile) simultaneous comparison, 16-week deadline, mandatory blog/PR outputs, Torch-MLIR's torch-dialect bridge (Legato sits in Inductor's slot and bypasses it).
- Do not re-promote the archived `phase0-detailed-plan.md` / `phase1-detailed-plan.md` to active. They were dropped on purpose.
- Do not skip from a Stage's prerequisites into a later Stage without the listed termination conditions met.
- Lecture PDFs at `/Users/juntaek/Documents/Cmp./Cmp` are an *on-demand reference*, not a parallel track. Cite them by section when actually consulted, not as scheduled reading.

## NOTES
- External lecture PDFs live at `/Users/juntaek/Documents/Cmp./Cmp`; reference them, but do not mirror them here.
- External source repos (`llvm-project`, `iree`, ...) live at `~/dev/compiler-sources/`; this directory remains output-focused.
- C++ proficiency is a known gap; the Stage 1 parallel C++ track is the primary remediation. Do not propose a separate "learn C++ first" track.
