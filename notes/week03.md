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
| `hasVerifier` / `hasFolder` / `hasCanonicalizer` | ODS 스위치 — 각각 verify/fold/canonicalize 메서드를 선언 생성 | — |

---

## 다음

- Block 5 — 직접 rewrite 1개 작성 (`mul(x,1)→x`) + FileCheck 테스트.
