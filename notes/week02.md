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

## 2026-05-31

### unranked tensor `tensor<*xf64>`

MLIR tensor 타입 3단계:

| 표기 | 무엇이 알려졌나 | 분류 |
|------|----------------|------|
| `tensor<2x3xf64>` | rank 2, 각 차원 크기까지 정적 | static shape |
| `tensor<?x3xf64>` | rank는 2, 첫 차원은 런타임 결정 | dynamic shape (ranked) |
| `tensor<*xf64>` | rank조차 모름. element type만 확정 | unranked |

Ch2 시점에 `toy.transpose` 결과가 `tensor<*xf64>`로 찍히는 이유 — Ch2엔 아직 shape inference가 없음. Ch4(Interfaces)에서 unranked → ranked로 좁혀진다.

### Defining a Toy Dialect

같은 dialect를 명령형 C++ class와 선언형 TableGen `.td` 두 형태로 선언. `getDialectNamespace() == "toy"` ↔ `let name = "toy"` 처럼 1:1 대응 — TableGen 쪽이 보일러플레이트가 적고, `.td`에서 C++ 코드가 생성된다.

**C++ class form:**
```cpp
/// This is the definition of the Toy dialect. A dialect inherits from
/// mlir::Dialect and registers custom attributes, operations, and types. It can
/// also override virtual methods to change some general behavior, which will be
/// demonstrated in later chapters of the tutorial.
class ToyDialect : public mlir::Dialect {
public:
  explicit ToyDialect(mlir::MLIRContext *ctx);

  /// Provide a utility accessor to the dialect namespace.
  static llvm::StringRef getDialectNamespace() { return "toy"; }

  /// An initializer called from the constructor of ToyDialect that is used to
  /// register attributes, operations, types, and more within the Toy dialect.
  void initialize();
};
```

**TableGen `.td` form (선언형):**

```tablegen
// Provide a definition of the 'toy' dialect in the ODS framework so that we
// can define our operations.
def Toy_Dialect : Dialect {
  // The namespace of our dialect, this corresponds 1-1 with the string we
  // provided in `ToyDialect::getDialectNamespace`.
  let name = "toy";

  // A short one-line summary of our dialect.
  let summary = "A high-level dialect for analyzing and optimizing the "
                "Toy language";

  // A much longer description of our dialect.
  let description = [{
    The Toy language is a tensor-based language that allows you to define
    functions, perform some math computation, and print results. This dialect
    provides a representation of the language that is amenable to analysis and
    optimization.
  }];

  // The C++ namespace that the dialect class definition resides in.
  let cppNamespace = "toy";
}
```