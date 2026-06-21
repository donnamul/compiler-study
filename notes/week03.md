# Week 03

> Stage 1 진행 중 학습 로그. Block 3부터.

## 2026-06-19

### Block 3 — `toy.neg` op 직접 추가

처음으로 *읽기*가 아니라 *쓰기*. Toy Ch2에 unary op 하나를 추가했다. 산출물 patch는 `experiments/toy-custom-ops/neg-op.patch`.

#### 세 파일의 분담 (Block 1~2에서 본 구조가 그대로 손에)

| 파일 | 역할 | 무엇을 적었나 |
|------|------|---------------|
| `Ops.td` | op *선언* (ODS) | `def NegOp : Toy_Op<"neg">` + `arguments` / `results` / `assemblyFormat` / `builders` |
| `Dialect.cpp` | builder *구현* | `NegOp::build` 몸체 — 결과 타입 + operand 채우기 |
| `MLIRGen.cpp` | AST → op *매핑* | `neg` 호출을 만나면 `NegOp::create` |

→ "ODS는 선언, C++은 구현, MLIRGen은 frontend 연결"이 한 op에서 다 보인다. (6/2 노트의 `Op vs Operation`, `Defining Toy Operations`가 여기서 실전화)

#### 판단 포인트 2개

- **`hasVerifier` 뺐다** — `TransposeOp`엔 있지만 `NegOp`엔 없음. transpose는 결과 shape이 입력의 transpose라 verifier가 그걸 체크해야 하지만, neg는 shape을 안 바꾸는 element-wise라 검증할 게 없다.
- **결과 타입 = `UnrankedTensorType`(f64)** — Ch2엔 아직 shape inference가 없으니 `tensor<*xf64>`로 둔다 (transpose와 동일). 5/13에 물어본 unranked tensor 개념이 여기 그대로 적용. Ch4 shape inference가 나중에 이걸 좁힌다.

#### 출력 확인

```
%1 = toy.neg(%0 : tensor<2x2xf64>) to tensor<*xf64>
```

입력은 ranked(`2x2`), 결과는 unranked(`*`) — 위 결정이 IR 표면에 그대로 드러난다.

#### C++ 디테일 (글로서리에 추가)

- `NegOp::build(OpBuilder&, OperationState&, Value)` — `OperationState`에 `addTypes` / `addOperands`로 op의 *재료*를 채운다. op은 이 state로부터 만들어진다.
- `state.addTypes(UnrankedTensorType::get(builder.getF64Type()))` — 타입도 context가 owner인 lightweight handle. `get(...)` 팩토리로 가져온다 (직접 `new` 안 함).
- `NegOp::create(builder, location, operands[0])` — Block 1에서 *읽기*만 했던 op 생성 패턴을 직접 *썼다*.

### 다음

- Block 3 마무리. 다음은 Block 4 — Toy Ch3 (Pattern Rewrite + Canonicalization).
- (선택) NegOp의 `assemblyFormat` 줄에 공백 정리, `summary` 문구를 "negation"으로.
