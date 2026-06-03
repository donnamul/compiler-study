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

Block 1 step 3 — `mlirGen(BinaryExprAST&)` (`MLIRGen.cpp:181~208`) 를 읽으며 만난 패턴.

- `isa<T>` / `cast<T>` / `dyn_cast<T>` — LLVM식 RTTI. 이 함수 안엔 직접 안 나오지만 같은 파일의 dispatcher `mlirGen(ExprAST&)` (`:356`)가 `cast<BinaryExprAST>(expr)` 로 다운캐스트해 우리 함수로 보낸다. Python 대응: `isinstance(x, T)` + 캐스팅. `dyn_cast<T>(x)` 는 실패 시 `nullptr` 돌려주는 *안전판*, `cast<T>(x)` 는 실패 시 abort.
- `SmallVector<T, N>` — 이 함수엔 등장 X. op 정의 / verifier / 인자 수집 쪽에서 곧 나옴. Python의 `list`처럼 쓰지만 N개까지는 *스택*에 inline 할당해서 작은 컬렉션에서 heap alloc 회피.
- builder 패턴 (op 생성) — `AddOp::create(builder, location, lhs, rhs)` 로 새 op을 IR에 박는다. 같은 코드베이스에 옛 스타일 `builder.create<AddOp>(...)` 도 섞여 있는데 의미 동일. Python 비유: `op = AddOp(location, lhs, rhs); builder.append(op)` + 자동 type inference.
- `mlir::Value` — SSA result/operand 의 *handle*. 값 자체가 아니라 참조 비슷 (실제로는 PIMPL — 내부 pointer 한 개 들고 있는 thin wrapper). 비유: PyTorch FX의 `Node`.
- `auto` — 컴파일 타임 타입 추론. `auto location = loc(binop.loc());` 에서 `location`의 타입은 `mlir::Location`. Python 미타입 변수와 *결과는* 비슷하지만 컴파일 타임에 박힘.
- `nullptr` 기반 에러 전파 — `if (!lhs) return nullptr;` 가 MLIRGen 전체의 관용구. 예외 안 던지고 null 들고 위로 올림. Python 의 `Optional[Value]` + early `return None` 과 같은 패턴.
- AST 후위 순회 — `mlirGen(*binop.getLHS())` / `mlirGen(*binop.getRHS())` 재귀로 자식 먼저 emit해서 Value 받아오고, 그 위에 본인 op 생성. AST → IR 변환의 표준 모양. `*p` 의 `*` 는 포인터 역참조 — Python 엔 직접 대응 없음 (모든 변수가 이미 reference라).
- `switch (char)` — `binop.getOp()` 가 `char`라 `case '+':` / `case '*':` 로 분기. C/C++의 char 리터럴은 *정수*라 switch 가능. Python의 `match c: case '+':` 와 같은 자리.

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

## 2026-06-02
### Defining Toy Operations

CRTP로 공통 기계장치를 물려받고, trait로 행동을 조립하고, build로 생성 방법을 제공하고, addOperations로 등록한다

op 하나 정의하는 건 결국 네 가지를 챙기는 일:

1. **공통 machinery 상속** — `mlir::Op<...>`를 CRTP로 물려받아 `getOperation()`, operand/result accessor 같은 표준 인터페이스를 공짜로 얻는다.
2. **trait로 행동 조립** — `Pure`, `IsolatedFromAbove` 같은 trait를 template 인자로 끼워서 verification·optimization 동작을 선언적으로 붙인다.
3. **build로 생성 방법 제공** — `OperationState`를 채우는 `build` 메서드로 "이 op을 어떻게 만드는가"를 정의한다.
4. **addOperations로 등록** — `ToyDialect::initialize()`에서 `addOperations<...>()`로 등록해야 비로소 verify되는 op이 된다.

`Ops.td`에서 `def ConstantOp : Toy_Op<"constant", [Pure]>` 한 줄 쓰면 위 1~3에 해당하는 C++ boilerplate가 `.inc`로 생성된다. C++로 직접 짜면 같은 걸 손으로 적는 거고 — 둘은 1:1 대응 (`Defining a Toy Dialect` 메모랑 같은 구도).

`Ops.td`의 공통 base:
```tablegen
class Toy_Op<string mnemonic, list<Trait> traits = []> :
    Op<Toy_Dialect, mnemonic, traits>;
```
→ toy op은 전부 dialect(`Toy_Dialect`) + mnemonic("constant" 등) + trait 목록을 묶어서 정의된다.

### CRTP

Curiously Recurring Template Pattern — **부모 template이 자식 클래스 자신을 타입 인자로 받는** 패턴.

```cpp
// 손으로 쓰면 이런 모양 (TableGen이 생성해주는 것)
class ConstantOp : public mlir::Op<ConstantOp, /* traits... */> {
  // ...
};
```

`Op<ConstantOp, ...>` — 부모 `Op`가 자식 `ConstantOp`를 알고 있다. 그래서 부모 쪽 공통 메서드가 `static_cast<ConstantOp*>(this)`로 자식 타입을 그대로 복원할 수 있다.

- **왜 쓰나**: virtual 함수(런타임 vtable 비용) 없이 자식별로 다른 동작을 compile time static dispatch로 해결. op이 수백 개 생기는 MLIR에선 이 오버헤드 차이가 크다.
- **Python 시선**: Python엔 직접 대응이 없다. 굳이 비유하면 metaclass나 `__init_subclass__`로 부모가 자식 정보 받아서 메서드 주입하는 것과 비슷한데, CRTP는 전부 **compile time**에 끝난다는 게 핵심 차이.
- 그래서 `ConstantOp`은 그 자체로 가벼운 handle — 진짜 데이터는 `Operation*`에 있고 `Op<>`는 type-safe wrapper일 뿐 (→ Op vs Operation).

### Trait

op에 **행동/제약을 선언적으로 끼워 넣는 mixin**. `Op<Derived, Trait1, Trait2, ...>`의 variadic template 인자 자리에 들어간다.

`Ops.td`에서 본 예:
- `Pure` — side effect 없음 + 결과가 입력에만 의존. dead면 제거(DCE)해도 된다고 프레임워크에 알린다. `ConstantOp`에 붙음.
- `IsolatedFromAbove` — region 안에서 바깥 SSA value를 참조하지 않음. `FuncOp`에 붙어서 함수 경계를 보장.
- `FunctionOpInterface` 같은 interface도 같은 자리에 들어가는데, trait가 "정적 속성 표시"라면 interface는 "런타임에 호출 가능한 메서드 묶음"이라는 차이가 있다.

요점: verification·optimization 가능성·구조 제약을 op 본체에 직접 쓰지 않고 **조립**한다. 같은 trait를 여러 op이 공유 → 중복 제거.

### Op vs Operation

MLIR에서 자주 헷갈리는 한 글자 차이 — **둘은 다른 레이어다.**

| | `mlir::Operation` | `mlir::Op<Derived,...>` / `ConstantOp` 등 |
|---|---|---|
| 정체 | 모든 op의 **단일 범용 데이터 구조** | 특정 op에 대한 **type-safe wrapper (handle)** |
| 내용 | operand/result/attribute/region/location 등 실제 상태를 다 담음 | 실제 상태 없음. `Operation*` 하나만 들고 있음 |
| 다형성 | 종류와 무관하게 동일 타입 | op마다 별도 C++ 클래스 (CRTP로 생성) |
| 크기 | 무거움 (실제 IR node) | 가벼움 (포인터 한 개, 값으로 복사 OK) |

흐름: parser/builder는 항상 범용 `Operation`을 만든다 → `ConstantOp op = dyn_cast<ConstantOp>(operation)`으로 타입을 좁혀서 `op.getValue()` 같은 전용 accessor를 쓴다 → 내부적으론 다시 `op.getOperation()`으로 범용 형태로 돌아갈 수 있다.

즉 **`Operation`은 데이터, `Op`(=`ConstantOp`)는 그 데이터를 특정 op으로 해석하는 type-safe lens.** `isa/cast/dyn_cast`가 이 둘 사이를 오가는 도구 (→ LLVM C++ pattern cheat sheet).

## 2026-06-03

### AST → MLIR 로 가면서 추가된 정보 3가지

- **타입 정보** — AST 의 `VarDecl a` 에는 element type / shape 가 *암묵적* 이지만, MLIR 에선 `tensor<2x3xf64>` 처럼 *first-class* 로 박힌다. literal 에서 추출 가능한 shape 은 즉시 ranked, 아직 추론이 안 된 결과 (`toy.transpose` 의 출력) 는 `tensor<*xf64>` 로 unranked — Ch4 shape inference 가 이걸 좁힌다.
- **SSA value 흐름** — AST 는 *노드 트리* (Call → var: a) 지만, MLIR 은 `%0`, `%1` 처럼 *value 한 개당 def 하나, use 여러 개* 의 그래프. `toy.transpose(%0 : ...)` 한 줄에 "이 op 의 입력은 `%0` 의 결과" 가 명시되고 그 결과가 `toy.print %1` 의 입력으로 이어진다. AST 에 없던 *데이터 흐름 그래프* 가 IR 표면에 떠오른다.
- **dialect prefix (`toy.`)** — 모든 op 이름이 `dialect.opname` 으로 namespace 된다. `toy.func` / `toy.constant` / `toy.transpose` 가 모두 `toy` dialect 소속이라는 게 한눈에 보이고, 한 함수 안에 `arith.addi` + `memref.load` + `scf.for` 같이 *여러 dialect 혼용* 이 가능한 이유 — 이름 충돌을 prefix 가 해결한다. CRTP / trait / Op vs Operation 같은 C++ 기계장치는 결국 이 한 줄 텍스트를 type-safe 하게 만들기 위한 받침대.

### 왜 IR 이 또 필요한가

LLVM IR 의 고정된 타입 시스템은 C / C++ 같은 *시스템 언어 한 단계 위* 까지가 한계다. Python / DSL / tensor 언어처럼 *고수준 의미* 가 있는 코드를 AST 에서 LLVM IR 로 곧장 내리려 하면 — 정보가 손실되고, 한 번의 거대한 lowering 안에 typing / control flow / memory model / target-specific 결정이 *동시에* 들어가서 변환이 비현실적으로 복잡해진다 (Ch2 doc 의 "non-trivial lowering from their AST to LLVM IR").

MLIR 의 답: 중간에 *언어 의미를 보존하는 dialect* 한 층을 끼우고, 그 수준에서 analysis / optimization 을 끝낸 다음 점진적으로 lower. 차별점은 *그 중간층을 하나가 아니라 여러 개* 둘 수 있다는 것 — `toy → affine → memref → llvm` 처럼 한 단계마다 한 종류의 결정만 내리면 된다. opaque API 는 dialect 가 아직 등록되지 않아도 IR 텍스트를 round-trip 시켜주는 받침대라, 새 dialect 를 점진적으로 끼워 넣는 *확장* 도 자연스럽다 — ML / DSL / hardware-specific dialect 가 같은 인프라 위에 공존할 수 있는 이유.
