# Week 01

## Focus

- Phase 0 bootstrap
- MLIR build readiness
- first-pass ecosystem map

## Environment

- OS: macOS 15.7 arm64
- Compiler: Apple clang 17
- Python: 3.9.6
- Installed for Phase 0: `cmake`, `ninja`, `ccache`

## Tasks

- [ ] Create study repo structure.
- [ ] Clone `llvm-project`.
- [ ] Configure MLIR build with Ninja.
- [ ] Create first `.mlir` examples.
- [ ] Clone `Triton-to-tile-IR` and inspect layout.

## Notes

### Build issues

- Record any configure or link issues here.
- If memory becomes a problem, reduce targets or build fewer tools first.

### MLIR first impressions

- Operation:
- Block:
- Region:
- Dialect: arith, memref, tensor, scf

### Triton-to-tile-IR structure memo

- `lib/`
- `include/`
- `python/`
- `third_party/tileir/`
- `test/`

## Questions to resolve

- Why is `DialectConversion` a better mental model than a hand-written lowering chain?
- Where exactly does `Triton-to-tile-IR` replace the default Triton PTX path?



### MLIR first impressions

- Operation:
- Block:
- Region:
- Dialect: arith, memref, tensor, scf#Day1(3/21)