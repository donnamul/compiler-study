# AI Compiler Ecosystem

```mermaid
flowchart TD
    A[PyTorch / JAX / TensorFlow] --> B[Frontend capture]
    B --> C1[torch.compile]
    B --> C2[jit / graph export]

    C1 --> D1[TorchInductor]
    D1 --> E1[Triton TTIR]
    E1 --> F1[Triton TTGIR]
    F1 --> G1[LLVM IR]
    G1 --> H1[PTX / CUBIN]

    E1 --> F2[CUDA Tile IR]
    F2 --> G2[tileiras]
    G2 --> H2[GPU binary]

    C2 --> D2[StableHLO / HLO]
    D2 --> E2[XLA or IREE lowering]
    E2 --> F3[Linalg / LLVM / target backend]

    C1 --> D3[Custom backend]
    D3 --> E3[Custom IR / MLIR]
    E3 --> F4[Accelerator codegen]
```

## Reading frame

- Triton: kernel-centric GPU compiler path.
- StableHLO/XLA: graph-level portability and optimization path.
- IREE: end-to-end compiler/runtime system with explicit lowering stages.
- CUDA Tile IR: alternative GPU backend abstraction below Triton IR.
