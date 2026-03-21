# Triton PTX vs Tile IR

## Default Triton backend

```text
Python DSL
  -> TTIR
  -> TTGIR
  -> LLVM IR
  -> PTX
  -> CUBIN
```

## Triton-to-tile-IR backend

```text
Python DSL
  -> TTIR
  -> CUDA Tile IR
  -> tileiras
  -> GPU binary
```

## What changes

- the backend target after TTIR,
- the lowering passes and legality rules,
- performance knobs and hardware assumptions.

## What stays conceptually the same

- high-level kernel semantics,
- need for canonicalization and conversion patterns,
- test strategy based on IR expectations and lowering behavior.
