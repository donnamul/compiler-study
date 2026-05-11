# Stage 1 — Toy Tutorial로 MLIR 핵심 메커니즘 익히기 + C++ 보강

> **상위 plan**: `notes/full_plan_for compiler_study.md`
> **상태**: Toy Ch1 진입 노트는 `week01.md` 끝에 있음. Toy Ch2부터가 실질적 진입점.

---

## 목표

- `.td` (ODS/TableGen)로 op을 정의하고 TableGen이 생성한 C++ 코드를 *읽을 수 있다*.
- fold / canonicalization / pattern rewrite가 같은 메커니즘의 다른 등장임을 설명한다.
- Dialect Conversion의 세 구성요소(ConversionTarget / RewritePattern / TypeConverter)를 자기 말로 설명한다.
- LLVM 스타일 C++ 패턴 (`isa/cast/dyn_cast`, `SmallVector`, `OpRewritePattern`, Builder, CRTP) 을 만났을 때 *당황하지 않는다*.

## C++ 보강 평행 트랙

별도 학습 시간이 아니라, Toy 코드를 읽다 마주치는 패턴을 매 블록 끝에 5~10줄 정리. Python 대응으로 적는 것이 핵심.

| LLVM/MLIR 패턴 | Python 대응 | 어디서 만나나 |
|----------------|--------------|---------------|
| `llvm::isa<T>`, `cast<T>`, `dyn_cast<T>` | `isinstance` + cast | `MLIRGen.cpp`의 AST 분기 |
| `llvm::SmallVector<T, N>` | `list` (스택에 N개 inline) | op 결과 모으기 |
| `llvm::ArrayRef<T>` | `list`의 read-only view | argument 받기 |
| `llvm::StringRef` | `str` slice view | 이름/symbol 처리 |
| `OpBuilder` | builder 패턴 / context manager | op 생성 |
| `OpRewritePattern<T>` | template + 가상 메서드 | rewrite 정의 |
| CRTP (`X : public Base<X>`) | — | trait, interface 구현 |
| `mlir::failure()` / `success()` | `Optional` / 예외 대신 status | pattern 적용 결과 |

이 표는 처음에 비어 있어도 됨. 만나는 대로 채워간다.

---

## 진행 단위 (Block)

날짜 없음. 한 block이 안 끝나면 다음 session에 그 자리에서 이어 한다.

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

**C++ 보강**: `examples/toy/Ch2/mlir/MLIRGen.cpp`의 `mlirGen(BinaryExprAST&)` 한 함수만 읽고, `isa/cast/dyn_cast` 등장 위치 메모.

**산출물**: `week03.md` 시작. "AST → MLIR로 가면서 추가된 정보 3가지" + "왜 IR이 또 필요한가" 한 단락.

---

### Block 2 — Toy Ch2 (2): ODS/TableGen으로 op 정의

**할 일**
1. Ch2 후반부 (ODS 프레임워크) 정독.
2. `examples/toy/Ch2/include/toy/Ops.td`에서 `TransposeOp`의 `summary` / `arguments` / `results` / `assemblyFormat`만 확인.
3. 빌드 산출물 디렉토리에서 ODS가 생성한 `.inc` 파일을 찾아 `TransposeOp` 관련 부분이 어떻게 나왔는지 살펴봄 (전부 읽지 않는다, 어떤 함수가 생기는지 *형태*만).
4. SSA가 헷갈리면 그때 `17_SSA.pdf`에서 def-use chain 부분만 발췌.

**C++ 보강**: TableGen의 declaration → C++ generation 관계는 Python의 dataclass 또는 protobuf-codegen과 비슷한 느낌. 그 비유로 한 줄 메모.

**산출물**: `.td 정의 → 생성된 C++` 대응 메모 (10줄 안쪽).

---

### Block 3 — 직접 해보기: `toy.neg` op 추가

**할 일**
1. `Ops.td`에 `NegOp` 추가 (unary, `Toy_Type` 입력/출력).
2. `MLIRGen.cpp`에서 단항 `-` 또는 `neg` 호출을 `NegOp`로 매핑.
3. 빌드 후 `-emit=mlir` 출력에 `toy.neg`가 나타나는지 확인.
4. 변경분을 `experiments/toy-custom-ops/` 에 별도 커밋 (llvm-project 안에서 작업하지 않음 — diff만 이 repo로 옮긴다).

**산출물**: `toy.neg` 동작 확인 + `experiments/toy-custom-ops/neg-op.patch` 또는 변경된 파일 사본.

---

### Block 4 — Toy Ch3: Pattern Rewrite + Canonicalization

**할 일**
1. Ch3 문서 정독 (Pattern Rewrite 시스템, `TransposeTransposeOptPattern`).
2. `toyc-ch3 -emit=mlir` vs `-emit=mlir -opt` 비교로 `transpose(transpose(x))`가 제거되는지 확인.
3. Quickstart Rewrites 문서 + Canonicalization 문서 읽기.
4. fold vs pattern rewrite 차이를 5줄로 메모.

**산출물**: 최적화 전/후 IR 비교 + "fold vs pattern" 5줄.

---

### Block 5 — 직접 해보기: rewrite 1개 + 최소 테스트

**할 일**
1. 아래 중 하나만 구현 (욕심 X):
   - `add(x, 0) → x`
   - `mul(x, 1) → x`
2. 작은 FileCheck 테스트 1개.

3개 의무 안 둔다. 하나 제대로가 셋 대충보다 낫다.

**산출물**: rewrite 1개 + FileCheck 테스트 1개 → `experiments/toy-rewrites/`.

---

### Block 6 — Toy Ch4: Interfaces (Shape Inference)

**할 일**
1. Ch4 문서 정독 (shape inference op interface).
2. `toyc-ch4 -emit=mlir -opt` 출력에서 generic tensor가 구체 shape로 바뀌는지 확인.
3. "op interface = op이 특정 계약을 따른다고 선언" 한 줄 메모.

**산출물**: interface가 왜 필요한지 한 단락.

---

### Block 7 — Toy Ch5 (1): Dialect Conversion 개념  ★

**할 일**
1. Ch5 전반부 정독. 세 구성요소를 *자기 말로*:
   - **ConversionTarget**: 어떤 op이 legal/illegal인지
   - **RewritePattern**: 어떻게 변환할지
   - **TypeConverter**: 타입을 어떻게 변환할지
2. `--mlir-print-ir-after-all`로 중간 IR 관찰.
3. dialect conversion의 종류 (Full / Partial / Analysis) 한 줄씩 메모.

**산출물**: "ConversionTarget / Pattern / TypeConverter" 자기 말 정리 + 종류 3개 차이.

---

### Block 8 — Toy Ch5 (2): NegOp lowering 작성

**할 일**
1. Block 3에서 만든 `NegOp`에 대해 `toy.neg → arith.negf` lowering 패턴 작성.
2. 빌드 후 `-emit=mlir-affine` 또는 해당 단계 출력에서 변환 확인.
3. before/after IR 캡처해서 메모.

**산출물**: NegOp lowering pattern 코드 + before/after IR.

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

**산출물**: 4단계 IR을 같은 op 기준으로 나란히 놓은 비교 메모.

---

### Block 10 — Toy Ch7: Composite type (선택)

**할 일**
- Ch7 (struct 타입)은 시간/체력 남을 때만. Stage 1 본질 아님.
- 읽었다면 한 단락 메모: "타입이 파이프라인을 관통하면 무엇이 어려워지는가."

---

### Block 11 — Stage 1 종합 회고

**할 일**
1. C++ 보강 표가 채워졌는지 확인. 빈 줄이 많으면 Stage 2 들어가기 전 30분 발췌 보강.
2. 아래 셋을 자기 말로 5분 안에 설명할 수 있는지 자가 점검:
   - `.td`로 op을 정의하면 C++이 어떻게 생기나
   - fold / canonicalize / dialect conversion이 어떻게 다른가
   - Toy의 전체 lowering chain
3. 막히는 항목이 있으면 그 chapter만 재독.

**산출물**: `week05.md` 마무리 + Stage 2 진입 직전 메모.

---

## Stage 1 종료 조건

- Toy Ch2~6은 끝났다 (Ch7은 선택, Ch1은 이미 끝).
- `toy.neg` 추가 + lowering이 동작한다.
- rewrite 1개 + 테스트가 있다.
- C++ 보강 표가 절반 이상 채워져 있다.
- ConversionTarget / Pattern / TypeConverter를 자기 말로 설명할 수 있다.

이 다섯 개가 안 되면 Stage 2로 안 넘어간다. Stage 2의 IREE 코드는 Stage 1의 기초 위에서만 의미 있다.
