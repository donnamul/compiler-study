# Stage 1 — Toy Tutorial로 MLIR 핵심 메커니즘 익히기 + C++ 보강

> **상위 plan**: `notes/full_plan_for compiler_study.md` (v5.2)
> **상태**: Toy Ch1 진입 노트는 `week01.md` 끝에 있음. Toy Ch2부터가 실질적 진입점.

---

## 목표

- `.td` (ODS/TableGen)로 op을 정의하고 TableGen이 생성한 C++ 코드를 *읽을 수 있다*.
- fold / canonicalization / pattern rewrite가 같은 메커니즘의 다른 등장임을 설명한다.
- Dialect Conversion의 세 구성요소(ConversionTarget / RewritePattern / TypeConverter)를 자기 말로 설명한다.
- LLVM 스타일 C++ 패턴 (`isa/cast/dyn_cast`, `SmallVector`, `OpRewritePattern`, Builder, CRTP) 을 만났을 때 *당황하지 않는다*.

---

## Stage 1 시작 직전 — C++ 5분 오리엔테이션

Toy 코드를 본격적으로 열기 전에 알아둘 *최소* C++. 따로 책 읽지 말고 이 섹션만 보고 시작. 막히면 그때 발췌.

### 파일 구조
- `.h` (헤더) 는 *선언*, `.cpp` 는 *정의*. Python의 한 파일에 다 적는 것과 다름. 같은 함수가 헤더에 `void f();` 로, cpp에 `void f() { ... }` 로 두 번 등장.
- `#include "X.h"` 는 컴파일 전에 그 파일 내용을 *그대로 붙여넣음*. Python `import` 와 다름. 이름 충돌은 `namespace` 로 막음.
- `#pragma once` 또는 include guard 는 같은 헤더가 여러 번 붙어 정의가 중복되지 않게 한다.

### `auto`, `const`, reference
- `auto x = builder.create<...>()` — 타입 추론. Python의 동적 타입과 비슷한 *작성 편의*지만 컴파일 타임에 타입은 고정.
- `const T&` (const reference) — "복사 안 하고 받지만 수정 안 함". 함수 인자에서 매우 자주 등장. Python의 immutable view와 비슷.
- `T*` (raw pointer) vs `T&` (reference) — pointer는 null 가능, reference는 항상 유효. MLIR은 `Operation*` 처럼 raw pointer 자주 씀 (소유권은 다른 곳).
- 메서드 뒤의 `const` — `T getType() const;` 는 "이 메서드는 객체를 수정 안 한다"는 약속.

### Template (Toy를 읽는 만큼만)
- `OpRewritePattern<TransposeOp>` 는 *클래스 템플릿 인스턴스*. Python의 `List[int]` 와 비슷한 자리.
- 함수/메서드 호출에 `<...>` 가 붙은 것 (`builder.create<arith::AddFOp>(...)`) 은 *어떤 op을 만들지* 타입으로 알려주는 것.
- 템플릿 *내부 정의* 까지 깊게 읽지 않는다. 사용만.

### LLVM RTTI — `isa<T>`, `cast<T>`, `dyn_cast<T>`
LLVM/MLIR에서 *제일 자주* 만나는 세 함수. 셋의 차이만 알면 90% 풀림.

| 함수 | 무슨 일 | Python 대응 | 실패 시 |
|------|---------|-------------|---------|
| `isa<T>(v)` | v가 T인지 *검사만* | `isinstance(v, T)` | `false` 반환 |
| `cast<T>(v)` | v를 T로 변환, **확신할 때만** | `assert isinstance + 캐스트` | **assertion 실패 — 크래시** |
| `dyn_cast<T>(v)` | v가 T면 T*, 아니면 null | try/except 없이 `isinstance` 후 분기 | `nullptr` 반환 |

전형 패턴:
```cpp
if (auto op = dyn_cast<arith::AddIOp>(value.getDefiningOp())) {
  // op은 여기서 arith::AddIOp* 로 보장됨
}
```
→ Python의 `if isinstance(x, AddIOp): ...` 와 똑같은 자리.

`std::dynamic_cast` (C++ 표준 RTTI) 와는 *다른* 메커니즘 — LLVM은 자기만의 RTTI를 만들어서 더 빠르고 가볍게 쓴다. 동작은 비슷.

### MLIR 고유: 소유권을 거의 신경 안 써도 되는 이유
- `Operation*`, `Value`, `Block*` 같은 핵심 타입들은 **MLIR Context가 메모리 owner**. 직접 `new` / `delete` 안 함.
- `Value`, `Type`, `Attribute` 는 *포인터처럼 동작하는 작은 wrapper* (immutable, value-passed). 복사가 싸다 — 그래서 함수 인자로 그냥 `Value v` 받아도 됨.
- `Operation*` 은 raw pointer지만 owner가 아님. 그냥 "이 op을 가리킨다"는 의미.
- → Python에서 reference만 쓰는 느낌. delete 신경 안 써도 됨.

### LogicalResult — 실패를 표현하는 방법
- `LogicalResult` 는 `success()` / `failure()` 두 값을 가지는 enum-비슷한 타입.
- MLIR이 *예외를 안 쓰기 때문에* return 값으로 성공/실패를 알린다.
- 패턴: `if (failed(verify(...))) return failure();`
- Python 대응: `Optional` 또는 status enum. `None` 리턴해서 실패 표현하는 것과 비슷한 자리.

이 정도면 Block 1 시작 가능. 나머지는 만나는 대로.

---

## C++ 보강 평행 트랙 (글로서리)

별도 학습 시간이 아니라, Toy 코드를 읽다 마주치는 패턴을 매 블록 끝에 *글로서리*로 누적. 만나는 대로 채워간다.

| LLVM/MLIR 패턴 | Python 대응 | 어디서 만나나 |
|----------------|--------------|---------------|
| `llvm::isa<T>`, `cast<T>`, `dyn_cast<T>` | `isinstance` + cast | `MLIRGen.cpp`의 AST 분기 |
| `llvm::SmallVector<T, N>` | `list` (스택에 N개 inline) | op 결과 모으기 |
| `llvm::ArrayRef<T>` | `list`의 read-only view | argument 받기 |
| `llvm::StringRef` | `str` slice view | 이름/symbol 처리 |
| `mlir::Value` | symbol에 대한 immutable handle | SSA value 다룰 때 |
| `mlir::Type`, `mlir::Attribute` | type/attribute의 lightweight handle | ODS argument에서 |
| `mlir::Operation*` | op에 대한 raw pointer (non-owning) | op 변환 / 검사 |
| `OpBuilder` / `ConversionPatternRewriter` | builder 패턴 / context manager | op 생성 |
| `OpRewritePattern<T>` | template + 가상 메서드 | rewrite 정의 |
| `matchAndRewrite(T op, PatternRewriter&) const override` | `def rewrite(self, op)` (stateless) | 패턴 본체 — 매칭 op을 `rewriter`로 교체/삭제 |
| `OpConversionPattern<T>` | OpRewritePattern + adaptor | dialect conversion |
| `LogicalResult`, `success()` / `failure()` | `Optional` / status enum | 예외 대신 성공 표현 |
| CRTP (`X : public Base<X>`) | — | trait, interface 구현 |
| `override` 키워드 | `@override` 데코레이터 (style) | virtual 메서드 재정의 |
| `static` 멤버 함수 | `@classmethod` 비슷 | matcher factory |
| `const T&` 인자 | immutable view | API 인자 |

---

## 진행 단위 (Block)

날짜 없음. 한 block이 안 끝나면 다음 session에 그 자리에서 이어 한다. **매 블록 끝의 "C++ 디테일"은 그 블록에서 *반드시 손에 박을* 패턴**. 글로서리에 한 줄 추가.

---

### Block 1 — Toy Ch2 (1): MLIR IR 생성과 op 해부

**할 일**
1. Toy Tutorial Ch2 문서 전반부 (operation 해부, dialect 등록 이유) 정독.
2. `toyc-ch2` 빌드 후 `-emit=mlir`로 출력 확인:
   ```bash
   cmake --build ~/dev/compiler-sources/llvm-project/build -t toyc-ch2
   ~/dev/compiler-sources/llvm-project/build/bin/toyc-ch2 /tmp/test.toy -emit=mlir
   ```
3. 출력의 한 줄에서 **result / op name / operand / attribute / type / location** 을 짚는다.
4. AST dump와 MLIR dump를 *나란히* 놓고 어떤 정보가 추가됐는지 본다.

**C++ 디테일 (이번 블록에서 손에 박을 것)**
- `examples/toy/Ch2/mlir/MLIRGen.cpp` 의 `mlirGen(BinaryExprAST&)` 한 함수만 정독.
- `llvm::dyn_cast<...>(...)` 위치 두세 군데 표시. AST 노드 타입 분기에서 무조건 등장.
- `mlir::Value` 가 변수에 담기는 패턴 — `mlir::Value lhs = mlirGen(*binop.getLHS());` 이 줄에서 lhs는 *복사된 핸들*. SSA value를 *Python 변수처럼* 들고 다닐 수 있다는 감각.
- `builder.create<toy::AddOp>(location, lhs, rhs)` — 템플릿 인자로 *어떤 op을 만들지* 알려주는 패턴. Python의 `factory("add", lhs, rhs)` 와 비슷한 자리.
- `mlir::Location` 이 함수 인자 첫 자리에 자주 옴 — *모든 op 생성*은 source location을 받음. 에러 메시지 품질이 여기서 나옴.

**산출물**: `week03.md` 시작. "AST → MLIR로 가면서 추가된 정보 3가지" + "왜 IR이 또 필요한가" 한 단락. 글로서리에 새로 만난 패턴 추가.

---

### Block 2 — Toy Ch2 (2): ODS/TableGen으로 op 정의

**할 일**
1. Ch2 후반부 (ODS 프레임워크) 정독.
2. `examples/toy/Ch2/include/toy/Ops.td`에서 `TransposeOp`의 `summary` / `arguments` / `results` / `assemblyFormat`만 확인.
3. 빌드 산출물 디렉토리에서 ODS가 생성한 `.inc` 파일을 찾아 `TransposeOp` 관련 부분이 어떻게 나왔는지 살펴봄 (전부 읽지 않는다, 어떤 함수가 생기는지 *형태*만).
4. SSA가 헷갈리면 그때 `17_SSA.pdf`에서 def-use chain 부분만 발췌.

**C++ 디테일 (이번 블록)**
- TableGen은 *C++이 아닌 별도 DSL*. `.td` → tablegen 도구 → `.inc` (C++ 코드) → 헤더에 `#include`. Python의 protobuf codegen / dataclass 자동 생성과 같은 자리.
- 생성된 `.inc` 가 헤더 안에서 `#define GET_OP_CLASSES` 같은 매크로로 *어디에* 붙는지 한 번 본다. 매크로 더럽다 — 그냥 "include 시점에 클래스 선언이 박힌다" 정도로 통과.
- 생성된 클래스의 메서드 *이름*만 본다: `getLhs()`, `getRhs()`, `build(...)`, `verify()`, `parse()`, `print()`. Python에서 받는 자동 생성 모델 클래스와 비슷한 구조.
- 클래스 상속 chain은 `class AddOp : public Op<AddOp, traits...>` 형태 — CRTP. *지금은 안 깊게 봄*, Block 6 (interface) 에서 다시.
- `mlir::OpAsmPrinter` / `mlir::OpAsmParser` 가 assembly format에서 나오는데, 이건 ODS의 `assemblyFormat` 가 충분하면 직접 손댈 일 거의 없음.

**산출물**: `.td 정의 → 생성된 C++` 대응 메모 (10줄 안쪽). 글로서리에 ODS-generated 메서드 이름 패턴 추가.

---

### Block 3 — 직접 해보기: `toy.neg` op 추가  (처음으로 C++ 직접 쓰는 자리)

**할 일**
1. `Ops.td`에 `NegOp` 추가 (unary, `Toy_Type` 입력/출력).
2. `MLIRGen.cpp`에서 단항 `-` 또는 `neg` 호출을 `NegOp`로 매핑.
3. 빌드 후 `-emit=mlir` 출력에 `toy.neg`가 나타나는지 확인.
4. 변경분을 `experiments/toy-custom-ops/` 에 별도 커밋 (llvm-project 안에서 작업하지 않음 — diff만 이 repo로 옮긴다).

**C++ 디테일 (이번 블록 — 처음 *쓰는* 자리라 두툼하게)**
- `auto value = builder.create<NegOp>(loc, operandValue);` — Block 1에서 본 패턴을 직접 *쓴다*. `loc` 가 어디서 오는지 (보통 호출자가 넘김), `operandValue` 가 `mlir::Value` 임을 확인.
- 새 op이 받는 인자의 *타입* 은 ODS의 `arguments` 가 결정. `Toy_Type:$input` 이면 builder의 `create<NegOp>` 가 자동으로 `Value` 하나 받는 시그니처를 생성.
- 빌드 에러를 *반드시 한 번은* 일부러 낸다. 예: ODS에서 `results` 누락. 에러 메시지 어떻게 생겼는지 익숙해지는 게 중요 — LLVM C++ 에러는 처음엔 무섭게 길다. **첫 줄만 보면 대부분 풀린다**.
- 헤더와 cpp 사이의 *링크 에러* (undefined reference to ...) 와 *컴파일 에러* (unknown identifier) 의 차이를 한 번은 직접 본다. Python의 ImportError / NameError 와 비슷한 자리지만 발생 시점이 다름.
- include 누락 → "unknown identifier" 에러 → 헤더 추가. Python의 ModuleNotFoundError 자리. C++ 에선 *어떤 헤더가 필요한지* 가 자동으로 안 알려줘서 IDE 도움이 큼.

**산출물**: `toy.neg` 동작 확인 + `experiments/toy-custom-ops/neg-op.patch` 또는 변경된 파일 사본. 이번 블록에서 만난 *에러 메시지 한 개* 와 그 해석을 메모.

---

### Block 4 — Toy Ch3: Pattern Rewrite + Canonicalization

**할 일**
1. Ch3 문서 정독 (Pattern Rewrite 시스템, `TransposeTransposeOptPattern`).
2. `toyc-ch3 -emit=mlir` vs `-emit=mlir -opt` 비교로 `transpose(transpose(x))`가 제거되는지 확인.
3. Quickstart Rewrites 문서 + Canonicalization 문서 읽기.
4. fold vs pattern rewrite 차이를 5줄로 메모.

**C++ 디테일 (이번 블록)**
- `class TransposeTransposeOptPattern : public mlir::OpRewritePattern<TransposeOp>` — 템플릿 base class 상속. `<TransposeOp>` 가 "이 패턴은 TransposeOp을 매칭한다"는 정보. Python으로 치면 `class P(OpRewritePattern[TransposeOp]):` 같은 자리.
- `using OpRewritePattern<TransposeOp>::OpRewritePattern;` — base 생성자를 그대로 가져오는 문법. *이 한 줄 있어야* `MLIRContext*` 받아 생성됨. 안 적으면 컴파일 에러.
- `LogicalResult matchAndRewrite(TransposeOp op, mlir::PatternRewriter &rewriter) const override` — 메서드 서명 *통째로* 외워두는 게 좋음.
  - `op` 는 매칭된 op (typed). `op.getOperand()` 같은 ODS-generated 메서드 그대로 호출 가능.
  - `rewriter` 는 reference. `replaceOp` / `replaceOpWithNewOp` / `eraseOp` 같은 호출이 여기로 감.
  - `const` 끝에 — "이 메서드는 패턴 객체를 수정 안 한다". 패턴은 stateless.
  - `override` — 부모의 virtual 메서드를 재정의한다는 명시. 빠뜨려도 동작은 하지만 컴파일러가 검사를 못 해서 위험.
- `return mlir::success();` / `return mlir::failure();` — Python에서 `return True/False` 자리. 단 *match 실패* 와 *match 후 rewrite 실패* 둘 다 같은 메커니즘.
- `rewriter.replaceOp(op, newValues)` vs `rewriter.replaceOpWithNewOp<NewOp>(op, args...)` — 후자가 *생성 + 교체*를 한 번에. 거의 항상 후자.

**산출물**: 최적화 전/후 IR 비교 + "fold vs pattern" 5줄. 글로서리에 `OpRewritePattern` / `matchAndRewrite` 시그니처 한 줄 추가.

---

### Block 5 — 직접 해보기: rewrite 1개 + 최소 테스트

**할 일**
1. 아래 중 하나만 구현 (욕심 X):
   - `add(x, 0) → x`
   - `mul(x, 1) → x`
2. 작은 FileCheck 테스트 1개.

3개 의무 안 둔다. 하나 제대로가 셋 대충보다 낫다.

**C++ 디테일 (이번 블록 — 두 번째로 *쓰는* 자리)**
- 패턴 안에서 "0인지 확인" 하는 자리: operand의 defining op을 `dyn_cast<arith::ConstantOp>(...)` 로 변환 → 성공하면 attribute 추출 → 값 비교. Block 1의 `dyn_cast` 패턴이 그대로 재등장.
- `op.getOperand(0).getDefiningOp()` — `Value` 에서 *그 value를 만든 op* 으로 거슬러 올라가는 핵심 호출. 없으면 (block argument 등) `nullptr` 반환 — 그래서 `dyn_cast` 와 같이 씀.
- `rewriter.replaceOp(op, op.getOperand(0));` — 한 줄 안에 `Operation*` (op) 과 `Value` (operand) 가 *섞여* 등장. 두 타입이 어떻게 다른지 헷갈리지 않는 자리.
- FileCheck 테스트의 `// CHECK: ...` 주석은 *C++이 아니라* LLVM 테스트 DSL. 그냥 문자열 매칭. Python의 doctest와 비슷한 자리.
- 패턴을 *등록* 하는 자리 — `void TransposeOp::getCanonicalizationPatterns(RewritePatternSet &results, MLIRContext *context)` 같은 static 메서드 안. ODS의 `let hasCanonicalizer = 1;` 이 이 메서드를 *선언만* 자동 생성. *정의* 는 직접 작성.

**산출물**: rewrite 1개 + FileCheck 테스트 1개 → `experiments/toy-rewrites/`. 글로서리에 `getDefiningOp()` 추가.

---

### Block 6 — Toy Ch4: Interfaces (Shape Inference)

**할 일**
1. Ch4 문서 정독 (shape inference op interface).
2. `toyc-ch4 -emit=mlir -opt` 출력에서 generic tensor가 구체 shape로 바뀌는지 확인.
3. "op interface = op이 특정 계약을 따른다고 선언" 한 줄 메모.

**C++ 디테일 (이번 블록)**
- C++의 *순수 가상 함수* (`virtual void f() = 0;`) 가 인터페이스의 토대. Python의 `abstractmethod` 와 같은 자리.
- MLIR `OpInterface` 는 **C++ interface와는 다른 메커니즘**: ODS의 `OpInterface<"ShapeInference">` 로 *interface 정의* 를 만들고, op이 `DeclareOpInterfaceMethods<ShapeInferenceOpInterface>` trait을 받으면 그 메서드 구현 의무가 생긴다. C++ 상속이 아니라 *trait 기반* 디스패치.
- 왜 굳이 두 메커니즘 — C++ virtual은 *클래스 단위*, MLIR interface는 *op 단위* 라 ODS-generated 클래스에 잘 맞음. 다이아몬드 상속 문제도 회피.
- CRTP (`class TransposeOp : public Op<TransposeOp, traits...>`) 가 여기 다시 등장. CRTP 자체는 깊게 안 봐도 됨 — "base class가 derived class를 *알기 위한* 트릭" 정도로 통과. C++ 책의 CRTP 챕터로 빠지지 않는다.
- ShapeInferenceInterface 구현 메서드는 ODS의 trait 선언만으로 *서명이 자동 생성*되고, 구현은 cpp 파일에 `void TransposeOp::inferShapes() { ... }` 로 작성. 헤더에 따로 선언 안 적어도 됨 — ODS가 이미 적어줬으니까.

**산출물**: interface가 왜 필요한지 한 단락. 글로서리에 `DeclareOpInterfaceMethods` / `OpInterface` 추가.

---

### Block 7 — Toy Ch5 (1): Dialect Conversion 개념  ★

**할 일**
1. Ch5 전반부 정독. 세 구성요소를 *자기 말로*:
   - **ConversionTarget**: 어떤 op이 legal/illegal인지
   - **RewritePattern**: 어떻게 변환할지
   - **TypeConverter**: 타입을 어떻게 변환할지
2. `--mlir-print-ir-after-all`로 중간 IR 관찰.
3. dialect conversion의 종류 (Full / Partial / Analysis) 한 줄씩 메모.

**C++ 디테일 (이번 블록 — Stage 2.7 production 코드 골격의 *예고편*)**
- `ConversionTarget target(getContext());` — 객체를 *지역 변수로* 만든다. Python의 `target = ConversionTarget(...)` 와 같은 자리. `new` 없음.
- `target.addLegalDialect<arith::ArithDialect, ...>();` — 템플릿 인자에 *여러 타입* 가능 (parameter pack). 일단 "쉼표로 dialect 여러 개 적으면 다 legal" 정도.
- `target.addIllegalDialect<toy::ToyDialect>();` — 변환 후 *남아 있으면 에러*인 dialect 명시.
- `RewritePatternSet patterns(&getContext());` — 패턴 컨테이너. `patterns.add<MyPattern1, MyPattern2>(&getContext());` 로 여러 개 한 번에 등록.
- `if (failed(applyPartialConversion(getOperation(), target, std::move(patterns)))) signalPassFailure();` — *통째로* 외워두는 게 좋은 자리. `std::move` 는 "patterns를 *건네준다*, 이후로 안 쓴다" 의미. Python에 없는 개념 — *moved-from* 상태는 사용 금지. Block 8에서 실제로 쓰면 손에 박힘.
- `applyPartialConversion` vs `applyFullConversion` vs `applyAnalysisConversion` 세 함수 *시그니처* 만 비교해서 차이 적어두기 — 본격 사용은 Block 8 + Stage 2.7.

**산출물**: "ConversionTarget / Pattern / TypeConverter" 자기 말 정리 + 종류 3개 차이. 글로서리에 `applyPartialConversion` + `std::move` 추가.

---

### Block 8 — Toy Ch5 (2): NegOp lowering 작성

**할 일**
1. Block 3에서 만든 `NegOp`에 대해 `toy.neg → arith.negf` lowering 패턴 작성.
2. 빌드 후 `-emit=mlir-affine` 또는 해당 단계 출력에서 변환 확인.
3. before/after IR 캡처해서 메모.

**C++ 디테일 (이번 블록 — 두 번째로 *쓰는* conversion 자리)**
- `class NegOpLowering : public OpConversionPattern<toy::NegOp>` — `OpRewritePattern` 의 *conversion 버전*. 차이는 인자 하나 — `adaptor`.
- `LogicalResult matchAndRewrite(NegOp op, OpAdaptor adaptor, ConversionPatternRewriter &rewriter) const override` — 시그니처에서 `adaptor` 가 새 인자. Block 4의 `OpRewritePattern` 시그니처와 *나란히* 적어두면 차이 한눈에 보임.
- `adaptor.getInput()` 은 *변환된 후의* operand. `op.getInput()` 은 *변환 전*. TypeConverter가 동작한 뒤에는 operand 타입이 바뀌어 있을 수 있어서, 항상 `adaptor` 쪽을 써야 안전. Stage 2.7의 production 패턴에서 이 구분이 자주 등장.
- `rewriter.replaceOpWithNewOp<arith::NegFOp>(op, adaptor.getInput());` — Block 4의 패턴과 동일 형태. 여기선 새 op이 *다른 dialect* (arith) 라는 점만 다름.
- 패턴 등록 자리 — pass의 `runOnOperation()` 안에서 `patterns.add<NegOpLowering>(typeConverter, &getContext());` 로 등록. Block 7의 `applyPartialConversion` 호출에 들어감.

**산출물**: NegOp lowering pattern 코드 + before/after IR. 글로서리에 `OpConversionPattern` / `OpAdaptor` 추가.

---

### Block 9 — Toy Ch6: LLVM dialect lowering chain

**할 일**
1. Ch6 문서 정독.
2. `toyc-ch6`로 4단계 IR 덤프 확인:
   ```bash
   toyc-ch6 /tmp/test.toy -emit=mlir         # Toy dialect
   toyc-ch6 /tmp/test.toy -emit=mlir-affine  # Affine dialect
   toyc-ch6 /tmp/test.toy -emit=mlir-llvm    # LLVM dialect
   toyc-ch6 /tmp/test.toy -emit=llvm         # LLVM IR
   ```
3. 4단계를 *나란히* 놓고 같은 add 한 줄이 어떻게 바뀌는지 본다.

**C++ 디테일 (이번 블록 — 가볍게)**
- `mlir::PassManager pm(&context);` + `pm.addPass(...)` — pass pipeline 구성. Python의 sklearn pipeline 자리와 비슷.
- `mlir::createConvertToLLVMPass()` 같은 *factory 함수* 패턴 — 각 pass는 직접 `new` 하지 않고 factory가 unique_ptr로 반환. unique_ptr은 *자동 소유권* — pass manager가 받으면 ownership 이전.
- 여기서 처음 `std::unique_ptr<Pass>` 가 나옴. 깊게 안 봐도 됨 — "pm에 넘기면 알아서 관리" 정도로 통과.

**산출물**: 4단계 IR을 같은 op 기준으로 나란히 놓은 비교 메모.

---

### Block 10 — Toy Ch7: Composite type (선택)

**할 일**
- Ch7 (struct 타입)은 시간/체력 남을 때만. Stage 1 본질 아님.
- 읽었다면 한 단락 메모: "타입이 파이프라인을 관통하면 무엇이 어려워지는가."

**C++ 디테일**: 새로운 패턴 거의 없음. ODS의 `Type` 정의가 등장하지만 Stage 3에서 더 깊게 다룸.

---

### Block 11 — Stage 1 종합 회고

**할 일**
1. C++ 보강 글로서리가 채워졌는지 확인. 빈 줄이 많으면 Stage 2 들어가기 전 30분 발췌 보강.
2. 아래 셋을 자기 말로 5분 안에 설명할 수 있는지 자가 점검:
   - `.td`로 op을 정의하면 C++이 어떻게 생기나
   - fold / canonicalize / dialect conversion이 어떻게 다른가
   - Toy의 전체 lowering chain
3. 막히는 항목이 있으면 그 chapter만 재독.

**C++ 자가 점검 (별도)**: 아래 5개를 *코드 없이* 자기 말로 답할 수 있나.
- `isa<T>`, `cast<T>`, `dyn_cast<T>` 의 셋 다른 점
- `OpRewritePattern<T>` 와 `OpConversionPattern<T>` 의 차이 (한 줄)
- `LogicalResult` 가 왜 존재하는가
- `mlir::Value` 와 `mlir::Operation*` 이 어떻게 다른가
- `std::move` 가 무엇을 의미하나 (한 줄)

5개 중 3개 이상 막히면 그 항목의 Block을 다시.

**산출물**: `week05.md` 마무리 + Stage 2 진입 직전 메모. 글로서리 최종본.

---

## Stage 1 종료 조건

- Toy Ch2~6은 끝났다 (Ch7은 선택, Ch1은 이미 끝).
- `toy.neg` 추가 + lowering이 동작한다.
- rewrite 1개 + 테스트가 있다.
- C++ 보강 글로서리가 절반 이상 채워져 있다.
- ConversionTarget / Pattern / TypeConverter를 자기 말로 설명할 수 있다.
- C++ 자가 점검 5개 중 3개 이상 답할 수 있다.

이 여섯 개가 안 되면 Stage 2로 안 넘어간다. Stage 2의 TTIR 코드 + Stage 2.7의 production conversion pass는 Stage 1의 기초 위에서만 의미 있다.
