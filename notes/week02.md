# Week 02

## 복귀 메모 (2026-05-11)

마지막 활동은 2026-03-23 (PR #7, Phase 0→1 전환 단순화) — 약 7주 공백.

**Phase 0에서 닫힌 것**
- MLIR 빌드 + `mlir-opt` 동작 확인
- `experiments/mlir-basics/` 예제 6개 (`hello`, `tensor_ops`, `control_flow`, `memref_ops`, `regions`, `blocks`)
- `week01.md`에 LangRef / `01_Intro.pdf` / Toy Ch1 진입 메모 정리

**아직 비어 있는 것**
- 이 파일의 LLVM C++ 패턴 (`isa/cast`, `SmallVector`, Builder), TableGen/ODS, PR 문화 섹션
- 강의안과 MLIR 예제 연결 메모, 커뮤니티 가입 / PR 관찰

**다음 진입점 — Phase 1 Block 18 (Toy Ch2)**
`llvm-project/mlir/examples/toy/Ch2/`에서 `Ops.td`, `mlir/MLIRGen.cpp`, `mlir/Dialect.cpp`를 "Python 시선"으로 훑고, 이 파일의 빈 C++ 패턴 / TableGen 섹션을 우선 채운다. 그 다음 Block 19~23로 `09_IR.pdf` / `17_SSA.pdf` 발췌 + Toy Ch2 마무리.

---

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

---

## 2026-05-12

### Generic function

- a function defined with type parameters, allowing it to operate on various data types while maintaining type safety, rather than being restricted to a single specific type

### toy tutorial Ch2 Emitting Basic MLIR

- llvm의 한계 고정된 타입 시스템으로 인해 C/c++보다 높은 수준의 언어를 해석하는데 정말 힘들었다 non trivial loweing from their ast to llvm ir
- 그래서 확장가능한 구조의 mlir 등장

### general form of an operation

- A name for the operation.
- A list of SSA operand values.
- A list of attributes.
- A list of types for result values.
- A source location for debugging purposes.
- A list of successors blocks (for branches, mostly).
- A list of regions (for structural operations like functions).

### Opaque API

- MLIR은 등록 안 된 op도 텍스트 그대로 받아들여서 round-trip은 되지만, 의미 검증은 안 해주니까 말도 안 되는 IR도 통과한다.