# EXPERIMENTS KNOWLEDGE BASE

## OVERVIEW
`experiments/` stores small, focused study artifacts: starter `.mlir` files and narrow scripts for observing compiler behavior.

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| MLIR syntax basics | `mlir-basics/` | Main Phase 0 verification area |
| Triton IR observation | `triton-ir-dumps/` | Later-phase/reference study on this machine |
| torch.compile bridge scripts | `torch-compile-to-triton/` | Keep secondary to MLIR-first work |

## CONVENTIONS
- Prefer one topic directory per experiment theme.
- File names should describe the concept directly: `hello.mlir`, `tensor_ops.mlir`, `control_flow.mlir`.
- Keep experiments minimal and readable; they are study aids, not benchmark suites.
- When Phase 1+ adds new experiment areas, use descriptive directories like `toy-custom-ops/`, `toy-rewrites/`, or `toy-lowering/`.

## VERIFICATION
- Primary check: run `mlir-opt` on `.mlir` files and confirm parse/print success.
- Toy Tutorial work should validate via `toyc-chN` binaries and visible IR output, not hidden automation.
- FileCheck-style tests belong here only when the plan explicitly reaches custom op/rewrite work.

## ANTI-PATTERNS
- Do not turn this directory into a source checkout mirror.
- Do not add heavyweight or CUDA-dependent workflows as if they are baseline local checks.
- Do not keep experiments without a matching note or plan context.

## COMMANDS
```bash
/Users/juntaek/dev/compiler-sources/llvm-project/build/bin/mlir-opt mlir-basics/hello.mlir
/Users/juntaek/dev/compiler-sources/llvm-project/build/bin/mlir-opt mlir-basics/regions.mlir
TRITON_INTERPRET=1 python triton-ir-dumps/vector_add.py
```
