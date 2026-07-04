# Week 03

> Stage 1 진행 중 학습 로그. Block 3부터.

## 2026-06-19

### Block 3 — `toy.neg` op 직접 추가

처음으로 *읽기*가 아니라 *쓰기*. Toy Ch2에 unary op 하나를 추가했다. 산출물 patch는 `experiments/toy-custom-ops/neg-op.patch`.

세 파일을 건드렸고, 각 조각이 무슨 의미고 왜 그렇게 썼는지 아래에 코드와 함께 정리한다.

---

#### 1. `Ops.td` — op *선언* (ODS)

```tablegen
def NegOp : Toy_Op<"neg"> {
  let summary = "element-wise negation";

  let arguments = (ins F64Tensor:$input);
  let results = (outs F64Tensor);

  let assemblyFormat = [{
    `(` $input `:` type($input) `)` attr-dict `to` type(results)
  }];

  // Allow building a NegOp from the input operand.
  let builders = [
    OpBuilder<(ins "Value":$input)>
  ];
}
```

- `def NegOp : Toy_Op<"neg">` — **무엇**: `toy` dialect에 `neg`라는 mnemonic의 op을 선언. **왜**: `Toy_Op` base를 상속하면 dialect 소속 + trait 자리 + TableGen 코드 생성이 한 줄로 붙는다 (`TransposeOp`와 같은 base).
- `arguments = (ins F64Tensor:$input)` — **무엇**: 입력 operand 1개, 이름 `input`, 타입은 f64 tensor. **왜**: neg는 단항(unary)이라 입력이 하나. `$input` 이름이 생성된 C++의 `getInput()` accessor가 된다.
- `results = (outs F64Tensor)` — **무엇**: 결과 1개, f64 tensor. **왜**: neg는 입력과 같은 모양의 tensor 하나를 돌려준다.
- `assemblyFormat` — **무엇**: 이 op의 텍스트 표기 규칙. **왜**: 직접 parser/printer를 C++로 안 짜도 ODS가 `toy.neg(%0 : tensor<...>) to tensor<...>` 형태를 자동 생성. `TransposeOp` 포맷을 그대로 가져옴 (둘 다 unary라 모양이 같다).
- `builders = [OpBuilder<(ins "Value":$input)>]` — **무엇**: "Value 하나로 NegOp을 만들 수 있다"는 builder *선언*. **왜**: 몸체는 `Dialect.cpp`에 따로 쓴다 (선언/구현 분리). MLIRGen에서 `NegOp::create(builder, loc, value)`로 부를 수 있게 하는 다리.
- **`hasVerifier`를 안 적었다** — **왜**: `TransposeOp`엔 `let hasVerifier = 1;`이 있지만 NegOp엔 뺐다. transpose는 결과 shape이 입력의 transpose라 verifier가 그 관계를 체크해야 하지만, neg는 shape을 안 바꾸는 element-wise라 따로 검증할 불변식이 없다.

---

#### 2. `Dialect.cpp` — builder *구현*

```cpp
void NegOp::build(mlir::OpBuilder &builder, mlir::OperationState &state,
                  mlir::Value value) {
  state.addTypes(UnrankedTensorType::get(builder.getF64Type()));
  state.addOperands(value);
}
```

- `NegOp::build(...)` — **무엇**: `Ops.td`에서 *선언*한 builder의 실제 몸체. **왜**: op을 만들 때 결과 타입과 operand를 `OperationState`에 채워 넣는 곳. op은 이 state로부터 생성된다.
- `state.addTypes(UnrankedTensorType::get(builder.getF64Type()))` — **무엇**: 결과 타입을 unranked f64 tensor(`tensor<*xf64>`)로 박는다. **왜**: Ch2엔 아직 shape inference가 없어서 "결과가 정확히 몇 x 몇인지" 모른다. 그래서 보수적으로 unranked. (`TransposeOp`도 동일 전략. 5/13에 본 `tensor<*xf64>` 개념이 여기 그대로.) Ch4 shape inference가 나중에 이걸 ranked로 좁힌다.
- `UnrankedTensorType::get(...)` / `builder.getF64Type()` — **무엇**: 타입을 *팩토리*로 가져온다. **왜**: MLIR의 Type은 context가 owner인 lightweight handle이라 직접 `new` 하지 않고 `get(...)`으로 받는다 (같은 타입은 context가 캐싱해 공유).
- `state.addOperands(value)` — **무엇**: 입력 operand로 `value` 하나 등록. **왜**: `Ops.td`의 `arguments`가 operand 1개라고 선언했으니 그것과 짝이 맞아야 한다.

---

#### 3. `MLIRGen.cpp` — AST → op *매핑*

```cpp
if (callee == "neg") {
  if (call.getArgs().size() != 1) {
    emitError(location, "MLIR codegen encountered an error: toy.neg "
                        "does not accept multiple arguments");
    return nullptr;
  }
  return NegOp::create(builder, location, operands[0]);
}
```

- 위치: `mlirGen(CallExprAST&)`의 `transpose` 분기 바로 옆. **왜**: Toy 언어에서 `neg`는 `neg(x)` 형태의 *built-in 함수 호출*로 파싱된다. 그래서 함수 호출을 처리하는 이 자리에서 callee 이름으로 분기. (단항 `-` 연산자로 했으면 lexer/parser부터 손봐야 해서 훨씬 무거움 — 일부러 함수형 선택.)
- `if (callee == "neg")` — **무엇**: 호출된 함수 이름이 `neg`인지 검사. **왜**: 같은 dispatcher가 transpose, 사용자 정의 함수 등을 다 처리하므로 이름으로 갈라야 한다.
- `if (call.getArgs().size() != 1)` — **무엇**: 인자가 정확히 1개인지 검사, 아니면 에러. **왜**: neg는 unary인데 `neg(a, b)`처럼 잘못 쓰면 *IR을 만들기 전에* frontend에서 막아야 의미 있는 에러가 난다.
- `emitError(location, ...)` + `return nullptr` — **무엇**: location을 끼운 에러를 내고 null 반환. **왜**: MLIR은 예외를 안 쓴다. null을 위로 올려 실패를 전파하는 게 관용구 (`LogicalResult`/`Optional`과 같은 자리). `location` 덕에 `test.toy:3:11` 같이 *소스 위치*가 찍힌다.
- `return NegOp::create(builder, location, operands[0])` — **무엇**: 실제로 `toy.neg` op을 IR에 만든다. **왜**: 위에서 정의/구현한 builder가 여기서 호출됨. `operands[0]`(이미 codegen된 입력 Value)을 받아 op을 만들고 그 결과 Value를 돌려준다. Block 1에서 *읽기*만 했던 `*Op::create` 패턴을 직접 *썼다*.

---

#### 출력 확인

```
%1 = toy.neg(%0 : tensor<2x2xf64>) to tensor<*xf64>
```

입력은 ranked(`2x2`), 결과는 unranked(`*`) — `Dialect.cpp`에서 내린 "결과를 unranked로 둔다"는 결정이 IR 표면에 그대로 드러난다.

에러 경로도 의도대로:

```
$ toyc-ch2 test_neg_err.toy -emit=mlir   # neg(a, a)
loc("test_neg_err.toy":3:11): error: MLIR codegen encountered an error:
toy.neg does not accept multiple arguments
```

---

#### 한 줄 요약

`Ops.td`(선언) → `Dialect.cpp`(build 구현) → `MLIRGen.cpp`(frontend 연결). 6/2 노트의 `Op vs Operation` / `Defining Toy Operations`가 한 op에서 전부 실전화됐다.

### 다음

- Block 3 마무리. 다음은 Block 4 — Toy Ch3 (Pattern Rewrite + Canonicalization).

## 2026-07-04

### Block 4 — Toy Ch3: Pattern Rewrite + Canonicalization

Block 3이 op *추가*(쓰기)였다면, Block 4는 op *변형/제거* 메커니즘. Block 7~8 Dialect Conversion의 전 단계 — `matchAndRewrite` 시그니처를 여기서 처음 만난다. 이번엔 코드를 짜지 않고 이미 있는 `TransposeTransposeOptPattern`이 IR을 실제로 바꾸는 걸 눈으로 확인.

---

#### `transpose(transpose(x)) → x` before / after

테스트 `.toy`:

```toy
def transpose_transpose(a) {
  return transpose(transpose(a));
}

def main() {
  var a = [[1, 2, 3], [4, 5, 6]];
  print(transpose_transpose(a));
}
```

같은 파일을 `toyc-ch3`로 두 번 emit — 최적화 OFF/ON:

| | `-emit=mlir` (opt 없음) | `-emit=mlir -opt` |
|---|---|---|
| `transpose_transpose` 본문 | `toy.transpose` **2개** (`%0`, `%1`가 체인) | **둘 다 소멸**, `toy.return %arg0` |
| `main` | 변화 없음 | 변화 없음 (매칭될 transpose가 없음) |

opt OFF:
```mlir
toy.func @transpose_transpose(%arg0: tensor<*xf64>) -> tensor<*xf64> {
  %0 = toy.transpose(%arg0 : tensor<*xf64>) to tensor<*xf64>
  %1 = toy.transpose(%0 : tensor<*xf64>) to tensor<*xf64>
  toy.return %1 : tensor<*xf64>
}
```

opt ON:
```mlir
toy.func @transpose_transpose(%arg0: tensor<*xf64>) -> tensor<*xf64> {
  toy.return %arg0 : tensor<*xf64>
}
```

**관찰**
- `transpose(transpose(a)) == a` 항등식을 `TransposeTransposeOptPattern::matchAndRewrite`가 op 2개를 지우고 `%arg0`로 갈아끼운 결과. **패턴 코드 한 조각 = IR에서 op 소멸**.
- 최적화는 opt-in — `-opt` 없으면 transpose 2개가 *남아있는 게* 정상. `-opt`가 내부에서 canonicalize pass를 돌려야 패턴이 적용된다.
- 패턴은 *매칭되는 자리에만* 작동 → `@main`은 transpose가 없어 그대로.

---

#### fold vs pattern rewrite (5줄)

1. **pattern rewrite** (`matchAndRewrite`): *여러 op에 걸친* 구조적 변형. 위 transpose-transpose처럼 op을 보고 새 op으로 교체하거나 통째로 제거. `RewritePatternSet`에 등록, `applyPatternsGreedily`로 구동.
2. **fold** (`OpFoldResult fold(...)`): *op 하나*를 상수나 이미 존재하는 SSA value로 접는 경량 경로. 예: `add(x, 0) → x`, 상수 폴딩. 새 op을 **만들면 안 됨**(기존 값/attribute 반환만).
3. 규모: fold는 single-op·no-new-op이 제약, pattern은 그 제약이 없어 multi-op 재작성까지 가능. "지금 op을 접기만 하면 되나 vs 주변 구조를 봐야 하나"가 갈림.
4. 둘 다 canonicalization이 굴린다 — `hasFolder = 1`(fold) / `hasCanonicalizer = 1`(pattern)로 ODS에서 켬. fold가 먼저·싸게 시도되고, 구조 변형이 필요하면 pattern.
5. DRR(TableGen 선언형)로도 pattern을 쓸 수 있지만(Quickstart), transpose-transpose는 C++ `OpRewritePattern`으로 작성 — 조건 로직이 있어 선언형보다 명령형이 편한 케이스.

**산출물**: before/after IR 비교(위) + fold vs pattern 5줄. 글로서리에 `matchAndRewrite` 시그니처 추가.

### 다음

- Block 4 마무리. 다음은 Block 5 — 직접 rewrite 1개 + 최소 테스트 작성.
