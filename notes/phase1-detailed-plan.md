# Phase 1: 컴파일러 기초 + MLIR Toy Tutorial + 강의안 중심 실습 — 상세 계획

> **기간**: Phase 1 순서형 Block 17~44
> **진행 단위**: 순서형 Block (45~120분)
> **핵심 산출물**: Toy Tutorial 완주, 수업 자료 핵심 개념 정리, custom op 추가 경험, production MLIR 예시 비교 메모, GitHub 리포 업데이트
> **운영 원칙**: 날짜보다 순서를 따른다. 한 block이 밀리면 다음 날짜로 넘기지 말고, 같은 순서에서 이어서 한다.

---

## Phase 1 전체 구조

```
Blocks 17~23: Ch1~2 + 01/09/17 강의 → "IR/SSA와 dialect가 연결된다"
Blocks 24~30: Ch3 + 02~07/22 강의   → "front-end와 rewrite가 이어진다"
Blocks 31~37: Ch4~5 + 11/12 강의    → "lowering, CFG, analysis가 연결된다" ★
Blocks 38~44: Ch6~7 + 17 재복습     → "전체 파이프라인이 하나로 보인다"
```

★ Blocks 31~37이 가장 중요. Toy의 dialect conversion과 lowering이 production MLIR 코드와 연결되는 구간.

---

## Phase 1 업데이트 전제

이 Phase는 이제 아래 세 축을 병행한다.

1. **수업 자료**: `/Users/juntaek/Documents/Cmp./Cmp`
2. **학습용 구현**: `llvm-project/mlir/examples/toy/`
3. **실전 코드**: StableHLO / IREE (Triton은 Blocks 31~44의 후반 확장)

### 수업 자료를 붙이는 이유

- Toy는 구현을 보여주지만, parsing/semantic analysis/SSA/CFG를 체계적으로 설명하지는 않는다.
- 반대로 강의 자료는 이론을 주지만, MLIR 코드와 바로 연결되지는 않는다.
- 따라서 Phase 1에서는 "강의에서 개념을 잡고 → Toy에서 구조를 보고 → StableHLO/IREE 같은 production MLIR 예시로 확장"하는 흐름으로 간다.

### Phase 1에서 우선순위 높은 강의

| PDF | Phase 1 역할 |
|-----|--------------|
| `01_Intro.pdf` | 전체 컴파일러 구조 복습 |
| `09_Intermediate_Representation.pdf` | IR 설계 관점 보강 |
| `17_SSA.pdf` | SSA value와 dominance 감각 |
| `11_Control_Flow.pdf` | basic block / CFG |
| `12_Data_Flow.pdf` | analysis 기본 감각 |
| `22_Preliminary_Transformations.pdf` | canonicalization / 정규화 감각 |
| `02~07_*.pdf` | lexer / parser / semantic analysis 백그라운드 |

### 현실적인 적용 원칙

- 수업 PDF를 모두 순서대로 다 보지 않는다.
- 각 block group의 Toy 주제와 직접 연결되는 PDF만 먼저 본다.
- 구현은 Toy 중심으로 한다. StableHLO/IREE는 보조 예시이고, Triton은 후반 확장이다.
- 강의 PDF는 하루 15~30분 분량으로 쪼개서 읽고, 한 번에 1개 전체를 끝내려 하지 않는다.
- LLVM Kaleidoscope는 메인 트랙으로 넣지 않고, Toy와 frontend 구조를 비교하고 싶을 때만 선택 참고로 본다.

---

## Blocks 17~23: Ch1~2 — AST → MLIR, Op 정의, ODS

### Blocks 17~23 핵심 질문

- AST와 MLIR Operation은 무엇이 같고 무엇이 다른가?
- "IR"이라는 말은 왜 필요한가?
- SSA value가 MLIR에서 왜 자연스럽게 보이는가?

### Blocks 17~23 병행 읽기

- `01_Intro.pdf` 발췌
- `09_Intermediate_Representation.pdf` 발췌
- `17_SSA.pdf` 발췌
- (선택) Kaleidoscope `LangImpl02` - AST / parser / frontend 흐름 비교용

### Block 17 (60~90분) — Toy Ch1: 언어와 AST

**할 일:**
0. **수업 자료 먼저 20~30분 읽기:**
   - `01_Intro.pdf` 전체를 읽지 말고 아래만 발췌:
     - compiler pipeline 전체 그림
     - front-end / IR / backend 구분
     - optimization이 pipeline 어디에 들어가는지
   - 목표: lexer → parser → semantic analysis → IR → optimization → codegen 흐름을 머리에 다시 올리기

1. Toy Tutorial Ch1 문서 정독: https://mlir.llvm.org/docs/Tutorials/Toy/Ch-1/
   - Toy 언어의 문법 이해 (tensor 기반, double만, 불변)
   - AST 구조 훑기

2. Toy 소스 코드 위치 확인 + 빌드:
   ```bash
   # 소스 위치
   ls llvm-project/mlir/examples/toy/
   # Ch1  Ch2  Ch3  Ch4  Ch5  Ch6  Ch7
   
   # Ch1 빌드 (이미 MLIR 빌드 시 포함되었을 수 있음)
   cd llvm-project/build
   cmake --build . -t toyc-ch1
   ```

3. Toy 예제 실행:
   ```bash
   # Toy 소스 파일 작성
   cat << 'EOF' > /tmp/test.toy
   def main() {
     var a = [[1, 2, 3], [4, 5, 6]];
     var b = transpose(a);
     print(b);
   }
   EOF
   
   # AST 덤프
   ./build/bin/toyc-ch1 /tmp/test.toy -emit=ast
   ```

4. **Lexer/Parser 코드 훑기** (C++ 깊이 이해 불필요, 구조만):
   - `examples/toy/Ch1/include/toy/Lexer.h`: 토큰 분류
   - `examples/toy/Ch1/include/toy/Parser.h`: recursive descent parser
   - 필요하면 Kaleidoscope Ch2를 열어 AST / parser 구조만 비교

**산출물:** `notes/week03.md` 시작 — "Toy 언어 요약, AST 구조, compiler pipeline과 AST의 위치"

---

### Block 18 (60~90분) — Toy Ch2 (1): MLIR IR 생성

**할 일:**
0. **수업 자료 먼저 20~30분 읽기:**
   - `09_Intermediate_Representation.pdf` 전체를 읽지 말고 아래만 발췌:
     - 왜 IR이 필요한가
     - AST와 IR의 차이
     - machine-independent IR의 역할
   - 목표: AST와 IR의 차이, machine-independent IR의 역할 정리

1. Toy Tutorial Ch2 문서 정독 (전반부):
   - Operation의 해부학: name, operands, results, attributes, regions, location
   - "MLIR은 확장 가능하게 설계되었다" — Toy dialect을 등록하는 이유

2. Toy가 출력한 MLIR IR에서 아래만 직접 짚기
   - result
   - op name
   - operand
   - attribute
   - type
   - location

3. `toyc-ch2` 빌드 + 실행:
   ```bash
   cmake --build . -t toyc-ch2
   ./build/bin/toyc-ch2 /tmp/test.toy -emit=mlir
   ```
   출력된 MLIR IR을 한 줄씩 읽으면서 AST와 대응시키기.

**산출물:** Toy AST 출력 vs MLIR IR 출력 나란히 비교 메모 + "왜 IR이 필요한가" 한 단락

---

### Block 19 (60~90분) — Toy Ch2 (2): ODS/TableGen으로 Op 정의

**할 일:**
0. **수업 자료 먼저 20~30분 읽기:**
   - `17_SSA.pdf` 전체를 읽지 말고 아래만 발췌:
     - single assignment 아이디어
     - def-use chain
     - phi가 왜 필요한지에 대한 직관
   - 목표: SSA variable, definition-use, phi의 필요성을 이해하고 Toy/MLIR의 `%0`, `%1` 표기와 연결

1. Ch2 문서 후반부 정독:
   - ODS (Operation Definition Specification) 프레임워크
   - `.td` 파일에서 Op을 선언적으로 정의하는 방법

2. **`Ops.td` 파일 분석** (`examples/toy/Ch2/include/toy/Ops.td`):
   - `summary`, `arguments`, `results`, `assemblyFormat`만 확인

3. **자동 생성된 코드 확인:**
   - 생성된 `.inc` 파일 위치 찾기
   - `TransposeOp` 관련 코드가 생기는지만 확인

**산출물:** `.td 정의 → 생성된 C++ 코드` 대응표 메모 + "SSA와 MLIR result value" 연결 메모

---

### Block 20 (45~60분) — 직접 해보기: toy.neg op 추가

**할 일:**
1. `Ops.td`에 `NegOp` 추가
2. `MLIRGen.cpp`에서 `neg` 함수 호출 시 `NegOp` 생성하도록 추가
3. 빌드 후 `toy.neg`가 IR에 나타나는지만 확인

**산출물:** `NegOp` 추가 완료 — 코드 변경분을 `experiments/toy-custom-ops/` 에 커밋

---

### Block 21 (45~60분) — 교차 읽기: production MLIR의 Op 정의

**할 일:**
1. **StableHLO의 Op 정의** (`stablehlo/dialect/StablehloOps.td`):
   GitHub에서 `DotGeneralOp` (matmul) 정의 확인:
   - `dot_dimension_numbers` attribute
   - 정교한 verifier와 type inference
   - 100개+ op이 체계적으로 정의되어 있음

2. **IREE / Linalg 관련 op 정의**:
   structured op가 실제 production compiler에서 어떻게 선언되는지 확인

3. **Triton의 Op 정의**는 선택 참고:
   `tt.load`, `tt.store`, `tt.dot`을 훑되, 이번 주의 필수는 아님

**산출물:** StableHLO / IREE / Triton op 정의 스타일 비교 메모 (5~10줄)

### Blocks 17~23 종료 체크

- [ ] `01_Intro.pdf`를 읽고 Toy의 AST 위치를 설명할 수 있다
- [ ] `09_Intermediate_Representation.pdf`를 읽고 AST와 IR의 차이를 설명할 수 있다
- [ ] `17_SSA.pdf`를 읽고 MLIR의 `%0`, `%1`가 왜 자연스러운지 설명할 수 있다
- [ ] Toy Ch1~2에서 AST → MLIR로 넘어가는 흐름을 말할 수 있다

---

### Blocks 22~23 (총 2~4시간) — Ch2 복습 + 강의안 연결 + 정리

**Block 22 (60~120분) — 강의안에서의 IR 개념과 Toy 연결:**

1. `09_Intermediate_Representation.pdf`, `17_SSA.pdf`를 다시 보며
   AST / IR / SSA의 역할 정리

2. Toy Ch1~2 출력물(AST dump, MLIR IR)을 나란히 놓고 대응 관계 적기

3. StableHLO의 op 하나를 골라 Toy op 정의와 비교 메모 작성

**Block 23 (60~90분) — Blocks 17~23 종합 정리:**

1. `notes/week03.md` 완성:
   - 배운 것
   - 교차 읽기
   - 헷갈리는 것
   - 다음 블록 할 것

2. GitHub 리포 업데이트

**산출물:** notes/week03.md + 실험 코드 커밋

---

## Blocks 24~30: Ch3 — 패턴 리라이팅 + Canonicalization

### Blocks 24~30 병행 읽기

- `02_Lexical_Analysis.pdf` ~ `07_Semantic_Analysis_II.pdf` 중 필요한 부분만 발췌
- `22_Preliminary_Transformations.pdf`

이번 주의 포인트는 front-end 이론 전체를 깊게 끝내는 것이 아니라,
"프론트엔드가 만들어낸 IR를 왜 정규화해야 하는가"를 이해하는 것이다.

### Block 24 (60~90분) — Ch3 문서 + Rewrite 기초

**할 일:**
1. Toy Tutorial Ch3 문서 정독
   - Pattern rewrite system이 MLIR의 핵심 변환 메커니즘인 이유
   - `TransposeTransposeOptPattern`: transpose(transpose(x)) → x
   - Canonicalization의 의미: "정규형으로 만들기"

2. **핵심 코드 읽기** (`examples/toy/Ch3/`):
   - `ToyCombine.cpp` (또는 `.td`): rewrite 패턴 정의
   - `Dialect.cpp`: canonicalization 등록

3. `toyc-ch3` 빌드 + 실행:
   ```bash
   cmake --build . -t toyc-ch3
   
   cat << 'EOF' > /tmp/rewrite_test.toy
   def main() {
     var a = [[1, 2, 3], [4, 5, 6]];
     var b = transpose(transpose(a));
     print(b);
   }
   EOF
   
   # 최적화 전
   ./build/bin/toyc-ch3 /tmp/rewrite_test.toy -emit=mlir
   # 최적화 후 (canonicalize pass 적용)
   ./build/bin/toyc-ch3 /tmp/rewrite_test.toy -emit=mlir -opt
   ```
   출력을 비교해서 `transpose(transpose(x))`가 실제로 제거되는지 확인.

**산출물:** 최적화 전/후 IR 비교 메모

---

### Block 25 (60~90분) — Quickstart Rewrites 문서 + fold vs pattern

**할 일:**
1. "Quickstart guide to adding MLIR graph rewrite" 문서 읽기

2. **두 가지 rewrite 메커니즘 이해:**
   - fold
   - pattern rewrite
   차이는 짧게 메모만 한다.

3. **Canonicalization 문서 읽기:**
   - fold와 canonicalize pattern이 모두 canonicalizer pass에서 실행됨
   - `--canonicalize` pass가 모든 dialect의 등록된 패턴을 한꺼번에 적용

**산출물:** "fold vs pattern" 차이 정리 (5~10줄)

---

### Block 26 (60~90분) — 직접 구현: Rewrite 3개

**할 일:**
1. Toy Ch3 코드를 기반으로 아래 3개 구현
   - `add(x, 0) -> x`
   - `mul(x, 1) -> x`
   - `reshape(reshape(x)) -> reshape(x)`

2. lit/FileCheck 테스트 2개 이상 작성

**산출물:** rewrite 3개 구현 + FileCheck 테스트 2개+ → `experiments/toy-rewrites/` 커밋

---

### Block 27 (45~60분) — 교차 읽기: 실전 프로젝트의 Rewrite

**할 일:**
1. **StableHLO의 canonicalization:**
   `stablehlo/transforms/` 에서 canonicalization pass 파일 열어보기.
   - `stablehlo.add(x, 0) → x` 같은 fold가 정의되어 있는지 확인
   - 네가 방금 Toy에서 구현한 것과 같은 패턴!

2. **IREE/Linalg 쪽 canonicalization/transform 예시 읽기:**
   structured op가 어떤 식으로 정리되는지 확인

3. **Triton pass는 선택 참고:**
   `RemoveLayoutConversions`를 훑으면서 "Toy Ch3의 패턴과 구조가 같은지" 정도만 확인

**산출물:** "Toy / StableHLO / IREE rewrite 비교" 메모 (구조, 복잡도, 적용 방식)

---

### Blocks 28~30 (총 2~4시간) — 정리 + 주간 메모

**Block 28 (60~120분):**

1. `week04.md` 초안 작성
2. fold / canonicalization / dialect conversion 차이를 자기 말로 정리
3. Toy와 StableHLO 예시를 나란히 놓고 비교 메모 작성

**Blocks 29~30:**
- notes/week04.md 정리
- 실험 코드 + 테스트 최종 커밋
- 블로그 초안 다듬기 (게시는 Phase 1 끝에)

**산출물:** notes/week04.md + rewrite 실험 코드

---

## Blocks 31~37: Ch4~5 — Dialect Conversion + Lowering ★ 가장 중요한 구간

### Blocks 31~37 병행 읽기

- `11_Control_Flow.pdf`
- `12_Data_Flow.pdf`

이번 주부터는 "변환"뿐 아니라 "변환 이후 어떤 분석이 가능해지는가"를 함께 본다.

### Block 31 (60~90분) — Ch4: Interfaces

**할 일:**
1. Toy Tutorial Ch4 문서 정독:
   - Shape inference interface
   - Op interface의 개념: "op이 특정 계약을 준수함을 선언"

2. `toyc-ch4` 빌드 + shape inference 확인:
   ```bash
   cmake --build . -t toyc-ch4
   ./build/bin/toyc-ch4 /tmp/test.toy -emit=mlir -opt
   # generic tensor → 구체적 shape (tensor<2x3xf64>)로 변환되는지 확인
   ```

**산출물:** interface가 왜 필요한지 짧은 메모

---

### Block 32 (60~90분) — Ch5 (1): Partial Lowering 개념

**할 일:**
1. Toy Tutorial Ch5 문서 정독 (전반부):
   - "Partial lowering": 일부 op만 lower하고 나머지는 남겨둠
   - Dialect Conversion Framework의 세 가지 핵심 구성요소:
     - **ConversionTarget**: 어떤 op이 legal(유지)/illegal(변환 필요)인지
     - **Rewrite Patterns**: 어떻게 변환할지
     - **Type Converter**: 타입을 어떻게 변환할지

2. **핵심 개념을 코드에서 확인:**
   - ConversionTarget
   - Rewrite Pattern
   - Type Converter

3. **`--mlir-print-ir-after-all` 플래그로 중간 IR 관찰:**
   ```bash
   ./build/bin/toyc-ch5 /tmp/test.toy -emit=mlir-affine -opt \
     2>&1 | head -200
   # 각 pass 후의 IR 변화를 관찰
   ```

**산출물:** "ConversionTarget / Pattern / TypeConverter" 핵심 정리

---

### Block 33 (60~90분) — Ch5 (2): Lowering 패턴 분석 + 직접 작성

**할 일:**
1. Ch5 lowering 패턴 코드에서 흐름만 본다
   - 입력 op 분석
   - 새 op 생성
   - 원래 op 교체

2. **Blocks 17~23에서 추가한 NegOp의 lowering 패턴 작성**

3. 빌드 후 `toy.neg -> arith.negf`로 바뀌는지만 확인

**산출물:** NegOp lowering 패턴 구현 + before/after IR 예제

---

### Block 34 (60~90분) — ★ production lowering 첫 진지한 읽기

**할 일:**
이번 날이 Phase 1의 핵심 전환점. Ch5에서 배운 dialect conversion을 production MLIR 코드에 연결한다.

1. **StableHLO→Linalg lowering 관련 파일 열기:**
   `stablehlo/transforms/StablehloLegalizeToLinalgPass.cpp` 또는 대응 파일 탐색

2. **읽기 목표 (전부 이해 X, 구조만):**
   - ConversionTarget 설정 찾기
   - 개별 conversion 패턴 2~3개 읽기
   - Toy Ch5와 구조 비교

3. **TritonToCudaTile는 선택 확장:**
   시간이 남으면 `TritonToCudaTile.cpp`를 열어 같은 구조가 반복되는지만 본다.

**산출물:** production lowering 첫 인상 메모 — 구조, 읽은 패턴 2~3개, 모르는 부분

---

### Blocks 35~37 (총 2~4시간) — Dialect Conversion 문서 + 교차 읽기 + 정리

**Block 35 (60~120분):**

1. **Dialect Conversion 공식 문서 정독:**
   - Full conversion vs Partial conversion vs Analysis conversion
   - Type conversion과 materialization
   - Legalization: "모든 illegal op이 변환될 때까지 반복"

2. **교차 읽기 — 세 프로젝트의 dialect conversion 비교:**
   - source dialect
   - target dialect
   - full / partial conversion
   - type conversion 복잡도

3. **선택 확장:**
   Triton 메인의 `ConvertTritonToTritonGPU`, `TritonToCudaTile`도 같은 프레임워크를 쓰는지 확인

**Block 36 (60~90분):**

1. **선택 확장:**
   시간이 남으면 TritonToCudaTile / ConvertTritonToTritonGPU를 열어
   같은 프레임워크가 더 복잡한 곳에서 어떻게 쓰이는지 확인

**Block 37:**
- `notes/week05.md` 정리 (Blocks 31~37 = Phase 1에서 가장 중요한 구간)
- dialect conversion 정리 메모 보강
- 실험 코드 커밋 (NegOp lowering, before/after IR)

**산출물:** notes/week05.md + "Toy / StableHLO / (선택) Triton dialect conversion 비교" + NegOp lowering 코드

---

## Blocks 38~44: Ch6~7 — LLVM Lowering + 전체 복습 + 블로그 완성

### Blocks 38~44 병행 읽기

- `17_SSA.pdf` 재복습
- `10_Instruction_Selection.pdf`는 선택적으로 읽되, LLVM IR 이후의 다음 단계가 어떤 문제를 다루는지 감만 잡는다

### Block 38 (60~90분) — Ch6: LLVM Dialect으로 최종 Lowering

**할 일:**
1. Toy Tutorial Ch6 문서 정독:
   - LLVM dialect: MLIR 안에서 LLVM IR을 표현하는 dialect
   - 전체 lowering chain: Toy → Affine/Arith → LLVM dialect → LLVM IR

2. `toyc-ch6` 빌드 + LLVM IR 생성:
   ```bash
   cmake --build . -t toyc-ch6
   ./build/bin/toyc-ch6 /tmp/test.toy -emit=llvm
   # LLVM IR이 출력됨 — C 코드와 비슷한 저수준 IR
   ```

3. 전체 lowering chain 관찰:
   ```bash
   # 각 단계별 IR 확인
   ./build/bin/toyc-ch6 /tmp/test.toy -emit=mlir          # Toy dialect
   ./build/bin/toyc-ch6 /tmp/test.toy -emit=mlir-affine   # Affine dialect
   ./build/bin/toyc-ch6 /tmp/test.toy -emit=mlir-llvm     # LLVM dialect
   ./build/bin/toyc-ch6 /tmp/test.toy -emit=llvm          # LLVM IR
   ```

**산출물:** 4단계 IR 덤프를 나란히 놓은 비교

---

### Block 39 (45~60분) — Ch7: Composite Type

**할 일:**
1. Toy Tutorial Ch7 문서 정독:
   - 커스텀 타입 (struct) 추가
   - 타입이 파이프라인 전체를 관통하는 방법

2. `toyc-ch7` 빌드 + struct 사용 예제 실행:
   ```bash
   cmake --build . -t toyc-ch7
   # struct 사용하는 .toy 파일 작성 + 실행
   ```

3. **타입 시스템 관점에서 프로젝트 비교:**
   - Toy: F64Tensor만 + struct 추가
   - Triton: tensor, pointer, tensor-of-pointers 등
   - StableHLO: tensor, token, complex 등 풍부한 타입
   - CUDA Tile: tile 타입 (tensor와 다른 추상화)

**산출물:** "프로젝트별 타입 시스템 비교" 메모

---

### Block 40 (60~90분) — 전체 파이프라인 복습 + 자가 테스트

**할 일:**
1. 핵심 질문만 자가 점검
   - ODS/TableGen
   - fold vs pattern
   - dialect conversion
   - Toy 전체 파이프라인
   - production MLIR 연결

2. 막히는 항목만 다시 확인

**산출물:** 자가 테스트 결과 + 부족한 부분 메모

---

### Block 41 (45~60분) — production MLIR 파이프라인 비교 다이어그램

**할 일:**
1. 기존 다이어그램을 더 구체화
   - Toy
   - XLA
   - IREE
   - Triton (후반 확장)
   - cuTile

2. 각 파이프라인에서 dialect conversion 지점 표시

**산출물:** `diagrams/pipeline-comparison-v2.md` — 5개 파이프라인 비교 다이어그램

---

### Blocks 42~44 (총 2~4시간) — 블로그 완성 + Phase 1 종합

**Block 42 (60~120분) — 블로그 글 2편 완성:**

**블로그 #2:** "MLIR Toy Tutorial을 끝내고 나서: 컴파일러에서 반복되는 3가지 패턴"
핵심 목차만 잡고 초안 완성:
- ODS/TableGen
- Pattern Rewrite
- Dialect Conversion

**Block 43 (60~90분) — 최종 정리:**

1. `notes/week06.md` 작성
2. GitHub 리포 최종 업데이트
3. 블로그 2편 게시 여부 결정

**Block 44:**
- Phase 1 → Phase 2 전환 준비
- Phase 2에서 만들 custom dialect 구상 시작

---

## Phase 1 완료 체크리스트

| # | 항목 | 완료? |
|---|------|-------|
| 1 | Toy Ch1~7 전체 문서 읽기 + 코드 따라치기 | ☐ |
| 2 | NegOp 추가 (Op 정의 + MLIRGen + lowering) | ☐ |
| 3 | Rewrite 패턴 3개 직접 구현 | ☐ |
| 4 | FileCheck 테스트 2개+ 작성 | ☐ |
| 5 | NegOp lowering pass 구현 | ☐ |
| 6 | Toy 전체 파이프라인 설명 가능 | ☐ |
| 7 | production MLIR lowering 예시 1개 이상 읽기 | ☐ |
| 8 | 3개 프로젝트의 Op 정의 비교 | ☐ |
| 9 | 3개 프로젝트의 Rewrite 비교 | ☐ |
| 10 | 3개 프로젝트의 Dialect Conversion 비교 | ☐ |
| 11 | production MLIR 파이프라인 비교 다이어그램 | ☐ |
| 12 | Triton은 후반 확장 주제로 위치를 이해 | ☐ |
| 13 | 블로그 글 1편 완성 (총 2편째) | ☐ |
| 14 | notes/week03~06.md 전체 정리 | ☐ |

---

## Phase 1에서 Phase 2로 넘어갈 때의 상태

- `.td`로 op을 정의하고, TableGen이 C++ 코드를 생성하는 흐름을 이해한다
- fold와 pattern rewrite를 직접 구현해봤다
- dialect conversion의 세 구성요소 (Target, Pattern, TypeConverter)를 설명할 수 있다
- StableHLO/IREE 같은 production MLIR 코드가 Toy와 어떻게 이어지는지 설명할 수 있다
- production compiler 파이프라인을 비교할 수 있다
- GitHub에 실험 코드가 쌓이고 있고, 블로그 글이 2편이다

**다음 Phase 2에서는:**
- 나만의 custom dialect을 C++로 만든다 (Toy가 아닌 독립 프로젝트)
- Triton과 같은 production backend를 후반 Phase에서 본격 분석한다
- Bufferization과 메모리 모델을 배운다
