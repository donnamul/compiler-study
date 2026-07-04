# Week 04

> Stage 1 학습 로그 · Block 6~ (Interfaces → Dialect Conversion)

---

## Block 6 — Toy Ch4: Interfaces (Shape Inference) (2026-07-05)

> **한 줄 요약**: dialect(Toy)가 MLIR의 **범용 변환**(inlining, shape inference)에
> *hook*할 수 있도록 **interface**를 정의·구현하는 장. Block 3~5에서 계속 뭉개고 온
> `tensor<*xf64>`가 여기서 구체 shape(`tensor<3x2xf64>`)로 **확정**된다.

핵심은 두 pass이고 **순서가 중요**하다: **① inlining → ② shape inference**.

### 왜 이 순서인가 (제일 중요한 포인트)

shape inference는 **함수 하나 안에서** shape을 전파한다(intra-procedural). 그런데
`toy.generic_call @f(...)` 경계에서, 호출된 함수는 인자를 `tensor<*xf64>`(unranked)로
받으므로 shape이 그 벽을 못 넘는다. → **먼저 inline해서 벽을 없애야** 모든 op이 한
함수 안에 모이고, 그제서야 shape이 끝까지 흐른다.

### 1. Inlining — 직접 짜지 않고 generic inliner를 재사용

MLIR이 주는 범용 inliner를 그대로 쓰되, "Toy를 어떻게 다뤄야 하는지"만 interface로 알려준다.

- **`ToyInlinerInterface : DialectInlinerInterface`** — "이 op을 inline해도 되나?",
  "terminator(`toy.return`)는 어떻게 처리하나?" 같은 질문에 답하는 훅 모음. **dialect 단위** interface.
- **`GenericCallOp` → `CallOpInterface`**, **`FuncOp` → callable** 로 표시 →
  inliner가 "이게 call이고 저게 함수구나"를 인식.
- **shape 불일치 시 `toy.cast` 자동 삽입** — call 시점 인자는 `tensor<2x3xf64>`인데
  함수가 기대하는 건 `tensor<*xf64>`. inliner가 경계에서 `toy.cast`를 끼워 맞춘다.
  이를 위해 `CastOp`이 **`CastOpInterface`** 구현. (`toy.cast`는 Ch4에서 새로 도입된 op)

### 2. Shape Inference — op interface + worklist pass

inline 후 모든 게 한 함수에 모였으니 shape을 전파한다.

- **interface 정의** (`ShapeInferenceInterface.td`):
  ```tablegen
  def ShapeInferenceOpInterface : OpInterface<"ShapeInference"> {
    let methods = [
      InterfaceMethod<"...", "void", "inferShapes">   // 요구 메서드 딱 하나
    ];
  }
  ```
- **op이 계약을 받는다** (`Ops.td`): `MulOp`/`TransposeOp` 등이
  `DeclareOpInterfaceMethods<ShapeInferenceOpInterface>` trait을 달면 `inferShapes()`
  **구현 의무**가 생김. 구현은 `Dialect.cpp`에 `void MulOp::inferShapes() { ... }`
  ("내 input shape이 정해지면 output shape은 이렇게" 를 op이 스스로 안다).
- **pass가 구동** (`ShapeInferencePass.cpp`) — worklist 알고리즘:
  1. `returnsDynamicShape`(= 아직 unranked)인 op들을 worklist에 넣는다.
  2. worklist에서 **`allOperandsInferred`(입력이 다 확정)** 인 op을 찾아 `inferShapes()`
     호출 → worklist에서 제거.
  3. worklist가 빌 때까지 반복. 끝에 안 비면 실패.

### interface가 왜 필요한가 (산출물 한 단락)

inliner·shape inference 같은 변환은 **범용**이라 Toy op의 내부를 몰라야 한다. 그렇다고
Toy가 매번 변환을 새로 짜면 낭비. 그래서 **"op이 특정 계약을 따른다"고 선언**(interface)
하면, 범용 변환이 그 계약만 보고 작동한다. Toy는 "이 op의 output shape 계산법"
(`inferShapes`)이나 "inline 가능 여부"만 채워 넣으면, MLIR의 기성 pass가 그걸 호출해
준다. **변환 로직과 dialect 지식의 분리** — 이게 interface의 존재 이유.

### 두 층위의 interface (헷갈리지 말 것)

| | 예 | 단위 | 뜻 |
|---|---|---|---|
| **Dialect** interface | `DialectInlinerInterface` | dialect 하나 | "이 dialect를 inline할 때의 규칙" |
| **Op** interface | `ShapeInferenceOpInterface`, `CallOpInterface`, `CastOpInterface` | op 종류별 | "이 op이 따르는 계약" |

- MLIR `OpInterface`는 **C++ virtual 상속이 아니라 trait 기반 디스패치**. C++ 순수가상함수
  (`virtual void f()=0;`, Python `abstractmethod`)가 개념적 토대지만, 상속 대신
  `DeclareOpInterfaceMethods<...>` trait으로 붙인다 — *op 단위*라 ODS-generated 클래스에
  맞고 다이아몬드 상속도 회피.
- 메서드 **선언은 ODS가 자동 생성**, 구현만 `.cpp`에 작성 (Block 3의 builder, Block 5의
  canonicalizer와 같은 선언/구현 분리).

### 이전 블록과의 연결 (payoff)

- Block 3에서 `NegOp::build`가 결과를 `tensor<*xf64>`로 둔 이유 = "Ch2엔 shape inference
  없음". **그 shape inference가 바로 이 블록.** 미뤄둔 빚을 여기서 갚는다.
- `ShapeInferencePass`는 Block 5의 `CanonicalizerPass`와 **같은 자리** — op별 로직
  (`inferShapes` / `getCanonicalizationPatterns`)을 pass가 모아 돌린다.

**산출물**: interface가 왜 필요한지 한 단락(위) + 글로서리에 `OpInterface` /
`DeclareOpInterfaceMethods`.

---

## Glossary (Block 6)

| Term | 뜻 | 비고 |
|------|----|------|
| `OpInterface<"Name">` | op이 따르는 **계약** 정의 (`.td`) | trait 기반, C++ 상속 아님 |
| `DeclareOpInterfaceMethods<Iface>` | op에 그 interface **구현 의무**를 부여하는 trait | 메서드 선언은 ODS 자동 생성 |
| `DialectInlinerInterface` | dialect 단위 inline 규칙 훅 | `ToyInlinerInterface`가 상속 |
| `CallOpInterface` / callable | "이건 호출 op / 저건 함수" 를 inliner에 알림 | `GenericCallOp` / `FuncOp` |
| `CastOpInterface` | 타입 변환 op 계약 | `toy.cast` (shape 불일치 시 삽입) |
| `inferShapes()` | input shape → output shape 계산 (op이 스스로) | `void`, 인자 없음 |
| worklist: `returnsDynamicShape` / `allOperandsInferred` | unranked인 op 수집 / 입력 다 확정된 op부터 처리 | pass 구동 조건 |

---

## 다음

- Block 7 — Toy Ch5 (1): Dialect Conversion 개념 ★ (Stage 1의 load-bearing skill).
