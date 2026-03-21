# AI Compiler Ecosystem Through a `torch.compile` Engineer's Lens

## Why this map matters

I already understand the `torch.compile` world well enough to reason about
graph extraction, partitioning, and backend code generation. What I want now is
to place MLIR, Triton, StableHLO, IREE, and CUDA Tile IR on the same map so I
can study with a contributor's eye instead of a tourist's eye.

## `torch.compile` in one line

`torch.compile` is a frontend-to-backend handoff system:

- Dynamo captures and guards Python programs.
- AOTAutograd rewrites training graphs.
- A backend lowers the result into something executable.

That backend boundary is where the compiler ecosystem starts to fork.

## Backend paths worth comparing

- TorchInductor -> Triton -> TTIR -> TTGIR -> LLVM IR -> PTX
- Triton-to-tile-IR -> TTIR -> CUDA Tile IR -> `tileiras` -> GPU binary
- PyTorch/XLA -> StableHLO/HLO -> XLA pipeline -> target codegen
- Legato-style custom backend -> custom IR/MLIR -> accelerator binary

## The common pattern: repeated lowering

These systems look different on the surface, but they repeat the same pattern:

1. capture a high-level program,
2. rewrite it into a compiler-friendly IR,
3. lower that IR through increasingly constrained representations,
4. emit target-specific code.

That is exactly why MLIR matters. It turns that repeated lowering story into a
framework rather than a one-off compiler implementation.

## Why `Triton-to-tile-IR` is a useful study target

`Triton-to-tile-IR` is not just another repo. It is a clean example of backend
replacement in a modern AI compiler stack. Instead of treating PTX as the only
destination after Triton IR, it swaps in a CUDA Tile IR path and lets you study
what changes when the backend contract changes.

## Next expansion points

- add a diagram comparing TTIR, StableHLO, and Linalg abstraction levels,
- show where `DialectConversion` appears in each stack,
- connect this map back to my day job work on compiler backend design.
