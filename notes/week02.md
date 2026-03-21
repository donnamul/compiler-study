# Week 02

## Focus

- MLIR IR structure
- LLVM-style C++ reading comfort
- TableGen and ODS intuition
- Triton pipeline comparison

## Tasks

- [ ] Read MLIR LangRef sections for operations, blocks, regions, and types.
- [ ] Read Toy tutorial Chapter 1 and Chapter 2.
- [ ] Capture three LLVM C++ idioms with Python analogies.
- [ ] Compare Triton PTX and Tile IR backend pipelines.
- [ ] Observe upstream PR and review patterns.

## LLVM C++ pattern cheat sheet

- `isa/cast/dyn_cast`:
- `SmallVector`:
- builder pattern:

## TableGen intuition

- `.td` declares structure.
- generated `.inc` files materialize boilerplate.
- ODS is where semantic intent starts becoming compiler code.

## PR culture notes

- Triton-to-tile-IR review style:
- MLIR upstream review style:
- Commit message patterns:

## End-of-week check

- Can I explain operation/block/region/dialect in my own words?
- Can I point to the file that likely owns TTIR -> CUDA Tile IR conversion?
- Can I compare StableHLO, Triton IR, and Linalg at a high level?
