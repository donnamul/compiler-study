# `torch.compile` to MLIR Mapping

| `torch.compile` concept | MLIR-style interpretation |
|---|---|
| Python program | source language |
| TorchDynamo graph capture | frontend IR extraction |
| FX graph | high-level IR / dialect boundary |
| AOTAutograd partitioning | graph transform / partition pass |
| Inductor loop IR | mid-level structured IR |
| Triton kernel IR | lower-level target-oriented dialect |
| backend codegen | final lowering + emission |

## Mental shortcut

If `torch.compile` feels like a chain of representations with invariants, you
already have the right intuition for MLIR.
