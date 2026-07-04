# Week 03

> Stage 1 학습 로그 · Block 3~4

---

## Block 3 — `toy.neg` op 추가 (2026-06-19)

첫 *쓰기* 작업. Toy Ch2에 unary op 하나를 직접 추가했다.
patch: `experiments/toy-custom-ops/neg-op.patch`

> **한 줄 요약**: op 하나를 추가하려면 세 파일이 순서대로 꿰인다 —
> **선언(`Ops.td`) → build 구현(`Dialect.cpp`) → frontend 연결(`MLIRGen.cpp`)**.

### 1. 선언 — `Ops.td` (ODS)

```tablegen
def NegOp : Toy_Op<"neg"> {
  let summary = "element-wise negation";

  let arguments = (ins F64Tensor:$input);   // unary → operand 1개, accessor는 getInput()
  let results   = (outs F64Tensor);         // 입력과 같은 모양 tensor 1개

  let assemblyFormat = [{
    `(` $input `:` type($input) `)` attr-dict `to` type(results)
  }];                                        // parser/printer 자동 생성 (TransposeOp 포맷 그대로)

  let builders = [ OpBuilder<(ins "Value":$input)> ];  // 몸체는 Dialect.cpp에 (선언/구현 분리)
}
```

- `Toy_Op<"neg">` base 상속 = dialect 소속 + trait 자리 + 코드 생성이 한 줄로 붙음.
- **`hasVerifier` 생략** — `TransposeOp`엔 있지만 neg엔 뺐다. transpose는 결과 shape이 입력의 transpose라 검증할 불변식이 있지만, neg는 shape을 안 바꾸는 element-wise라 검증할 게 없다.

### 2. build 구현 — `Dialect.cpp`

```cpp
void NegOp::build(mlir::OpBuilder &builder, mlir::OperationState &state,
                  mlir::Value value) {
  state.addTypes(UnrankedTensorType::get(builder.getF64Type()));  // 결과 = tensor<*xf64>
  state.addOperands(value);                                       // operand 1개 연결
}
```

- **결과를 unranked(`tensor<*xf64>`)로 둔다** — Ch2엔 아직 shape inference가 없어 결과 shape을 모른다. 보수적으로 unranked. Ch4의 shape inference가 나중에 ranked로 좁힌다. (`TransposeOp`과 동일 전략)
- 타입은 `new`가 아니라 `...::get(...)` **팩토리**로 받는다 — Type은 context가 owner인 lightweight handle이라 같은 타입은 캐싱·공유된다.

### 3. frontend 연결 — `MLIRGen.cpp`

```cpp
if (callee == "neg") {                              // neg(x)는 built-in 함수 호출로 파싱됨
  if (call.getArgs().size() != 1) {                 // unary 가드 — IR 만들기 전에 막는다
    emitError(location, "MLIR codegen encountered an error: toy.neg "
                        "does not accept multiple arguments");
    return nullptr;                                 // 예외 대신 null 전파
  }
  return NegOp::create(builder, location, operands[0]);  // 위에서 정의한 build가 여기서 호출
}
```

- 위치: `mlirGen(CallExprAST&)`의 `transpose` 분기 옆. 단항 `-` 연산자로 했으면 lexer/parser부터 손대야 해서 무거움 → 일부러 **함수형** 선택.
- **MLIR은 예외를 안 쓴다** — 실패는 `emitError(location, ...)` + `return nullptr`로 위로 전파. `location` 덕에 `test.toy:3:11`처럼 소스 위치가 찍힌다.

### 결과

```mlir
%1 = toy.neg(%0 : tensor<2x2xf64>) to tensor<*xf64>   // 입력 ranked, 결과 unranked
```

```
$ toyc-ch2 test_neg_err.toy -emit=mlir   # neg(a, a)
loc("test_neg_err.toy":3:11): error: MLIR codegen encountered an error:
toy.neg does not accept multiple arguments
```

---

## Block 4 — Ch3 Pattern Rewrite + Canonicalization (2026-07-04)

op *변형/제거* 메커니즘. 코드는 안 짜고, 기존 `TransposeTransposeOptPattern`
(= `transpose(transpose(x)) → x`)이 IR을 실제로 바꾸는 걸 확인했다.
여기서 처음 만나는 `matchAndRewrite`가 Block 7~8 Dialect Conversion의 토대.

### `transpose(transpose(x)) → x` — before / after

같은 `.toy`를 `toyc-ch3`로 최적화 OFF/ON 두 번 emit:

```mlir
// -emit=mlir  (opt 없음) — transpose 2개가 체인
%0 = toy.transpose(%arg0 : tensor<*xf64>) to tensor<*xf64>
%1 = toy.transpose(%0    : tensor<*xf64>) to tensor<*xf64>
toy.return %1

// -emit=mlir -opt  (opt 있음) — 둘 다 소멸
toy.return %arg0
```

- `transpose(transpose(a)) == a` 항등식을 패턴의 `matchAndRewrite`가 op 2개를 지우고 `%arg0`로 갈아끼운 결과. **패턴 코드 한 조각 = IR에서 op 소멸.**
- 최적화는 **opt-in** — `-opt` 없으면 transpose가 남아있는 게 정상.
- 패턴은 **매칭되는 자리에만** 작동 → transpose 없는 `@main`은 그대로.

### fold vs pattern rewrite

| | **fold** | **pattern rewrite** |
|---|---|---|
| 대상 | op **하나** | **여러 op**에 걸친 구조 |
| 하는 일 | 상수/기존 SSA value로 접기 (`add(x,0)→x`, 상수 폴딩) | 새 op으로 교체·제거 (transpose-transpose) |
| 제약 | **새 op 못 만듦** — attribute/value 반환만 | 제약 없음 (multi-op 재작성 OK) |
| ODS 스위치 | `let hasFolder = 1;` | `let hasCanonicalizer = 1;` |
| 반환 | `OpFoldResult` | `LogicalResult` (`success`/`failure`) |

- 둘 다 canonicalization이 굴린다. fold가 먼저·싸게 시도되고, 구조 변형이 필요하면 pattern.
- 갈림 기준: **"지금 op을 접기만 하면 되나 vs 주변 구조를 봐야 하나."**

---

## Glossary (Block 3~4)

| Term | 뜻 | Python 대응 |
|------|----|-------------|
| `UnrankedTensorType` (`tensor<*xf64>`) | rank 미정 tensor. shape inference 전 보수적 결과 타입 | — |
| `Type::get(...)` factory | context가 캐싱·소유하는 lightweight handle | `intern()` 비슷 |
| `emitError(loc, msg)` + `return nullptr` | 예외 없는 실패 전파 관용구 | `raise` 대신 `return None` |
| `matchAndRewrite(T op, PatternRewriter&) const override` | 패턴 본체 — 매칭 op을 `rewriter`로 교체/삭제 (stateless) | `def rewrite(self, op)` |
| `value.getDefiningOp<T>()` | `Value` → 만든 op + `T` 캐스팅. block arg 등이면 `nullptr` | producer 접근 + `isinstance` |
| `DenseElementsAttr::isSplat()` / `getSplatValue<T>()` | 상수가 단일값 splat인지 / 그 값. **isSplat 먼저 안 보면 assert** | `arr.all_same()` / `arr[0]` |
| `hasVerifier` / `hasFolder` / `hasCanonicalizer` | ODS 스위치 — 각각 verify/fold/canonicalize 메서드를 선언 생성 | — |

---

## Block 5 — canonicalization 패턴 직접 작성 (2026-07-04)

Block 4에서 *읽은* 패턴을 이번엔 직접 *쓴다*. `mul(x, 1) → x` canonicalization 하나 +
FileCheck 테스트. 산출물: `experiments/toy-rewrites/`.

> **선언/구현 분리** (Block 3와 동일 구조): `.td`에 스위치 한 줄로 *선언* 생성 → `.cpp`에 *구현*.

### 1. 스위치 — `Ops.td`

```tablegen
def MulOp : Toy_Op<"mul", [Pure]> {
  // ...
  let hasCanonicalizer = 1;   // MulOp::getCanonicalizationPatterns 선언을 자동 생성
}
```

- `hasCanonicalizer`가 없으면 `.cpp`의 `getCanonicalizationPatterns` 정의가 "선언 없는 함수"라 컴파일 에러 → **`.td` 먼저**가 강제된다.

### 2. 패턴 — `ToyCombine.cpp`

```cpp
struct SimplifyMulByOne : public mlir::OpRewritePattern<MulOp> {
  SimplifyMulByOne(mlir::MLIRContext *context)
      : OpRewritePattern<MulOp>(context, /*benefit=*/1) {}

  llvm::LogicalResult
  matchAndRewrite(MulOp op, mlir::PatternRewriter &rewriter) const override {
    auto isSplatOne = [](ConstantOp c) {
      if (!c) return false;                                   // 상수 아님 → 매칭 실패
      auto v = c.getValue();                                  // DenseElementsAttr
      return v.isSplat() && v.getSplatValue<double>() == 1.0; // isSplat() 먼저!
    };
    auto lhs = op.getOperand(0), rhs = op.getOperand(1);
    if (isSplatOne(rhs.getDefiningOp<ConstantOp>())) {        // mul(x, 1) -> x
      rewriter.replaceOp(op, {lhs}); return success();
    }
    if (isSplatOne(lhs.getDefiningOp<ConstantOp>())) {        // mul(1, x) -> x
      rewriter.replaceOp(op, {rhs}); return success();
    }
    return failure();
  }
};

void MulOp::getCanonicalizationPatterns(RewritePatternSet &results,
                                        MLIRContext *context) {
  results.add<SimplifyMulByOne>(context);   // 여기 등록해야 프레임워크가 집어감
}
```

- `getDefiningOp<ConstantOp>()` — `Value`에서 *그 값을 만든 op*으로 거슬러 올라가 `ConstantOp`으로 캐스팅까지 한 번에. 아니면 `nullptr`. (`dyn_cast<ConstantOp>(v.getDefiningOp())`의 축약형)
- **양쪽 operand 다 검사** — `mul`은 commutative라 `mul(1, x)`도 잡아야 한다.
- **`isSplat()` 가드가 핵심** — `getSplatValue`를 non-splat 상수에 바로 부르면 assertion 크래시 (assert 빌드). splat 확인이 먼저.
- `replaceOp(op, {lhs})` — 한 줄에 `Operation*`(op)과 `Value`(lhs)가 섞인다. op의 결과 *uses*를 lhs로 갈아끼움.

### 3. 확인 — before / after

```mlir
// a * 1, before (-opt 없음)          // a * 1, after (-opt)
%0 = toy.constant dense<1.0> : ...     toy.return %arg0
%1 = toy.mul %arg0, %0 : ...
toy.return %1
```

| 입력 | `-opt` | 판정 |
|------|--------|------|
| `a * 1` | `toy.return %arg0` | mul 소멸 |
| `1 * a` | `toy.return %arg0` | commutative OK |
| `a * [[1,2],[3,4]]` | mul 유지, exit 0 | non-splat → 매칭 X, **크래시 없음** |

### 4. FileCheck

```
# RUN: toyc-ch3 %s -emit=mlir -opt 2>&1 | FileCheck %s
# CHECK-LABEL: toy.func @f(
# CHECK-SAME:              [[VAL_0:%.*]]: tensor<*xf64>) -> tensor<*xf64>
# CHECK-NEXT:    toy.return [[VAL_0]] : tensor<*xf64>
```

- `[[VAL_0:%.*]]` — SSA 이름을 하드코딩 대신 **캡처**해서 재사용.
- `CHECK-NEXT` — mul이 사이에 남아있으면 실패 → **mul이 사라졌음을 증명**.
- 실행: `toyc-ch3 t.toy -emit=mlir -opt | FileCheck t.toy` → PASS(exit 0). FileCheck는 빌드 유틸 (`cmake --build build -t FileCheck`).

### 함정 메모 — `mul(a,1)` vs `a * 1`

처음에 `mul(a, 1)` 함수 호출로 썼더니 `toy.generic_call @mul`이 나와 패턴이 안 먹었다. Toy에서:

- `neg` / `transpose` → **built-in 함수 호출** (`f(x)` 문법, MLIRGen이 이름으로 분기)
- `mul` / `add` → **연산자** (`*`, `+`에서만 `toy.mul` 생성)

같은 이름이라도 IR로 내려오는 경로가 다르다. 패턴은 `toy.mul`을 매칭하니 소스는 `*`를 써야 한다.

**산출물**: `mul-by-one.patch` + `mul_by_one.toy`(FileCheck) → `experiments/toy-rewrites/`. 글로서리에 `getDefiningOp()` 추가.

---

## 다음

- Block 5 마무리. 다음은 Block 6 — Toy Ch4: Interfaces (Shape Inference).
