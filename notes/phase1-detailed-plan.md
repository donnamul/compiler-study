# Phase 1: 컴파일러 기초 + MLIR Toy Tutorial + 강의안 중심 실습 — 상세 계획

> **기간**: 4주 (3~6주차)
> **시간**: 주중 저녁 1~1.5시간 + 주말 3~4시간
> **핵심 산출물**: Toy Tutorial 완주, 수업 자료 핵심 개념 정리, custom op 추가 경험, production MLIR 예시 비교 메모, GitHub 리포 업데이트

---

## Phase 1 전체 구조

```
Week 3: Ch1~2 + 01/09/17 강의  → "IR/SSA와 dialect가 연결된다"
Week 4: Ch3   + 02~07/22 강의  → "front-end와 rewrite가 이어진다"  
Week 5: Ch4~5 + 11/12 강의     → "lowering, CFG, analysis가 연결된다" ★
Week 6: Ch6~7 + 17 재복습      → "전체 파이프라인이 하나로 보인다"
```

★ Week 5가 가장 중요. Toy의 dialect conversion과 lowering이 production MLIR 코드와 연결되는 주.

---

## Phase 1 업데이트 전제

이 Phase는 이제 아래 세 축을 병행한다.

1. **수업 자료**: `/Users/juntaek/Documents/Cmp./Cmp`
2. **학습용 구현**: `llvm-project/mlir/examples/toy/`
3. **실전 코드**: StableHLO / IREE (Triton은 Week 5~6의 후반 확장)

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
- 각 주차의 Toy 주제와 직접 연결되는 PDF만 먼저 본다.
- 구현은 Toy 중심으로 한다. StableHLO/IREE는 보조 예시이고, Triton은 후반 확장이다.

---

## Week 3: Ch1~2 — AST → MLIR, Op 정의, ODS (3주차)

### Week 3 핵심 질문

- AST와 MLIR Operation은 무엇이 같고 무엇이 다른가?
- "IR"이라는 말은 왜 필요한가?
- SSA value가 MLIR에서 왜 자연스럽게 보이는가?

### Week 3 병행 읽기

- `01_Intro.pdf`
- `09_Intermediate_Representation.pdf`
- `17_SSA.pdf`

### Day 15 (주중 저녁, 1.5시간) — Toy Ch1: 언어와 AST

**할 일:**
0. **수업 자료 먼저 20~30분 읽기:**
   - `01_Intro.pdf`: compiler pipeline 전체 그림
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
   
   Python 비유: `ast.parse("x + 1")` 이 하는 것과 같음

**산출물:** `notes/week03.md` 시작 — "Toy 언어 요약, AST 구조, compiler pipeline과 AST의 위치"

---

### Day 16 (주중 저녁, 1.5시간) — Toy Ch2 (1): MLIR IR 생성

**할 일:**
0. **수업 자료 먼저 20~30분 읽기:**
   - `09_Intermediate_Representation.pdf`
   - 목표: AST와 IR의 차이, machine-independent IR의 역할 정리

1. Toy Tutorial Ch2 문서 정독 (전반부):
   - Operation의 해부학: name, operands, results, attributes, regions, location
   - "MLIR은 확장 가능하게 설계되었다" — Toy dialect을 등록하는 이유

2. MLIR Operation 구조를 Toy 코드에서 확인:
   ```
   %t_tensor = "toy.transpose"(%tensor) {inplace = true}
                : (tensor<2x3xf64>) -> tensor<3x2xf64>
                loc("example/file/path":12:1)
   
   분해:
   - %t_tensor          ← result (SSA value)
   - "toy.transpose"    ← op name (dialect.mnemonic)
   - (%tensor)          ← operand
   - {inplace = true}   ← attribute
   - (tensor<2x3xf64>)  ← input type
   - tensor<3x2xf64>    ← output type
   - loc(...)           ← source location
   ```

3. `toyc-ch2` 빌드 + 실행:
   ```bash
   cmake --build . -t toyc-ch2
   ./build/bin/toyc-ch2 /tmp/test.toy -emit=mlir
   ```
   출력된 MLIR IR을 한 줄씩 읽으면서 AST와 대응시키기.

**산출물:** Toy AST 출력 vs MLIR IR 출력 나란히 비교 메모 + "왜 IR이 필요한가" 한 단락

---

### Day 17 (주중 저녁, 1.5시간) — Toy Ch2 (2): ODS/TableGen으로 Op 정의

**할 일:**
0. **수업 자료 먼저 20~30분 읽기:**
   - `17_SSA.pdf`
   - 목표: SSA variable, definition-use, phi의 필요성을 이해하고 Toy/MLIR의 `%0`, `%1` 표기와 연결

1. Ch2 문서 후반부 정독:
   - ODS (Operation Definition Specification) 프레임워크
   - `.td` 파일에서 Op을 선언적으로 정의하는 방법

2. **`Ops.td` 파일 분석** (`examples/toy/Ch2/include/toy/Ops.td`):
   ```tablegen
   // TransposeOp 정의 예시
   def TransposeOp : Toy_Op<"transpose"> {
     let summary = "transpose operation";
     let description = [{...}];
     let arguments = (ins F64Tensor:$input);
     let results = (outs F64Tensor);
     let assemblyFormat = [{
       `(` $input `:` type($input) `)` attr-dict `:` type(results)
     }];
   }
   ```
   
   Python 비유:
   ```python
   # 이건 마치 Python dataclass로 op을 정의하는 것과 비슷
   @dataclass
   class TransposeOp:
       input: F64Tensor        # arguments
       result: F64Tensor       # results
       # summary, description = 문서화
       # assemblyFormat = __str__ / __repr__
   ```

3. **자동 생성된 코드 확인:**
   ```bash
   find build/ -path "*/toy/*.inc" | head -10
   # 생성된 .inc 파일을 열어서 TransposeOp 관련 코드 찾기
   # 생성된 C++ 코드가 .td 파일과 어떻게 대응되는지 확인
   ```

**산출물:** `.td 정의 → 생성된 C++ 코드` 대응표 메모 + "SSA와 MLIR result value" 연결 메모

---

### Day 18 (주중 저녁, 1시간) — 직접 해보기: toy.neg op 추가

**할 일:**
1. `Ops.td`에 `NegOp` 추가:
   ```tablegen
   def NegOp : Toy_Op<"neg"> {
     let summary = "negation operation";
     let description = [{
       Returns the element-wise negation of the input tensor.
     }];
     let arguments = (ins F64Tensor:$input);
     let results = (outs F64Tensor);
     let assemblyFormat = [{
       `(` $input `:` type($input) `)` attr-dict `:` type(results)
     }];
   }
   ```

2. `MLIRGen.cpp`에서 `neg` 함수 호출 시 `NegOp`을 생성하도록 추가

3. 빌드 + 테스트:
   ```bash
   cmake --build . -t toyc-ch2
   
   cat << 'EOF' > /tmp/neg_test.toy
   def main() {
     var a = [[1, 2], [3, 4]];
     var b = neg(a);
     print(b);
   }
   EOF
   
   ./build/bin/toyc-ch2 /tmp/neg_test.toy -emit=mlir
   # toy.neg 연산이 IR에 나타나는지 확인
   ```

**빌드 실패 시 디버깅 팁:**
- TableGen 에러: `.td` 파일 문법 확인 (세미콜론, 괄호)
- 링크 에러: `MLIRGen.cpp`에서 `NegOp` 헤더가 include 되었는지 확인
- 런타임 에러: `mlir-opt`으로 생성된 IR이 valid한지 확인

**산출물:** `NegOp` 추가 완료 — 코드 변경분을 `experiments/toy-custom-ops/` 에 커밋

---

### Day 19 (주중 저녁, 1시간) — 교차 읽기: production MLIR의 Op 정의

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

**비교 정리:**
| 프로젝트 | Op 수 | Verifier 복잡도 | Type Inference | 특이사항 |
|----------|-------|----------------|----------------|----------|
| Toy | ~5 | 거의 없음 | 없음 | 학습용 |
| StableHLO | ~100 | 높음 | 정교함 | 완전한 spec |
| IREE/Linalg | 다수 | 중간~높음 | 구조적 | lowering 친화적 |
| Triton | ~30 | 중간 | 있음 | 후반 확장 예시 |

**산출물:** "프로젝트별 Op 정의 스타일 비교" 메모

### Week 3 종료 체크

- [ ] `01_Intro.pdf`를 읽고 Toy의 AST 위치를 설명할 수 있다
- [ ] `09_Intermediate_Representation.pdf`를 읽고 AST와 IR의 차이를 설명할 수 있다
- [ ] `17_SSA.pdf`를 읽고 MLIR의 `%0`, `%1`가 왜 자연스러운지 설명할 수 있다
- [ ] Toy Ch1~2에서 AST → MLIR로 넘어가는 흐름을 말할 수 있다

---

### Day 20~21 (주말, 3~4시간) — Ch2 복습 + 강의안 연결 + 정리

**Day 20 (2시간) — 강의안에서의 IR 개념과 Toy 연결:**

1. `09_Intermediate_Representation.pdf`, `17_SSA.pdf`를 다시 보며
   AST / IR / SSA의 역할 정리

2. Toy Ch1~2 출력물(AST dump, MLIR IR)을 나란히 놓고 대응 관계 적기

3. StableHLO의 op 하나를 골라 Toy op 정의와 비교 메모 작성

**Day 21 (1~2시간) — Week 3 종합 정리:**

1. `notes/week03.md` 완성:
   ```markdown
   # Week 3: MLIR Op 정의의 세계
   
   ## 배운 것
   - Toy Ch1: AST 구조, Lexer/Parser
   - Toy Ch2: MLIR IR 생성, ODS/TableGen
   - NegOp 직접 추가해봄
   
    ## 교차 읽기
    - StableHLO / IREE / (선택) Triton의 Op 정의 비교
   
   ## 헷갈리는 것
   - (여기에 정직하게 적기)
   
   ## 다음 주 할 것
   - Ch3: Pattern rewrite
   ```

2. GitHub 리포 업데이트:
   ```
   experiments/
   ├── toy-custom-ops/
   │   └── neg_op/               ← NegOp 추가 변경분
    └── mlir-basics/              ← Phase 0에서 만든 것
   ```

**산출물:** notes/week03.md + 실험 코드 커밋

---

## Week 4: Ch3 — 패턴 리라이팅 + Canonicalization (4주차)

### Week 4 병행 읽기

- `02_Lexical_Analysis.pdf` ~ `07_Semantic_Analysis_II.pdf` 중 필요한 부분만 발췌
- `22_Preliminary_Transformations.pdf`

이번 주의 포인트는 front-end 이론 전체를 깊게 끝내는 것이 아니라,
"프론트엔드가 만들어낸 IR를 왜 정규화해야 하는가"를 이해하는 것이다.

### Day 22 (주중 저녁, 1.5시간) — Ch3 문서 + Rewrite 기초

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

### Day 23 (주중 저녁, 1.5시간) — Quickstart Rewrites 문서 + fold vs pattern

**할 일:**
1. "Quickstart guide to adding MLIR graph rewrite" 문서 읽기

2. **두 가지 rewrite 메커니즘 이해:**

   **(a) Fold — 가벼운 상수 정리:**
   ```cpp
   // Op 클래스 안에 fold() 메서드 정의
   OpFoldResult ConstantOp::fold(FoldAdaptor adaptor) {
     return getValue();  // 상수를 그대로 반환
   }
   ```
   - 단일 op에 대한 단순 변환
   - 새 op을 만들지 않고, 기존 값을 반환하거나 attribute로 대체
   - Python 비유: `__hash__` 처럼 op에 직접 붙는 메서드

   **(b) Pattern — 구조적 변환:**
   ```cpp
   struct SimplifyRedundantTranspose 
       : public OpRewritePattern<TransposeOp> {
     LogicalResult matchAndRewrite(TransposeOp op,
                                    PatternRewriter &rewriter) const override {
       // transpose(transpose(x)) → x 검사
       auto transposeInput = op.getInput().getDefiningOp<TransposeOp>();
       if (!transposeInput) return failure();
       
       rewriter.replaceOp(op, {transposeInput.getInput()});
       return success();
     }
   };
   ```
   - 여러 op을 매칭해서 다른 op으로 교체
   - `matchAndRewrite` 패턴: match 성공하면 rewrite, 실패하면 다음 패턴으로
   - Python 비유: visitor 패턴 + 조건부 변환

3. **Canonicalization 문서 읽기:**
   - fold와 canonicalize pattern이 모두 canonicalizer pass에서 실행됨
   - `--canonicalize` pass가 모든 dialect의 등록된 패턴을 한꺼번에 적용

**산출물:** "fold vs pattern 비교" 정리 + 각각 언제 쓰는지 가이드

---

### Day 24 (주중 저녁, 1.5시간) — 직접 구현: Rewrite 3개

**할 일:**
1. Toy Ch3 코드를 기반으로 자기만의 rewrite 패턴 구현:

   **(a) `add(x, 0) → x`** (fold로 구현):
   ```cpp
   // AddOp의 fold 메서드
   OpFoldResult AddOp::fold(FoldAdaptor adaptor) {
     auto rhs = dyn_cast_or_null<DenseElementsAttr>(adaptor.getRhs());
     if (rhs && rhs.isSplat() && 
         rhs.getSplatValue<double>() == 0.0)
       return getLhs();
     return {};
   }
   ```

   **(b) `mul(x, 1) → x`** (fold로 구현):
   비슷한 패턴으로 구현

   **(c) `reshape(reshape(x)) → reshape(x)`** (pattern으로 구현):
   transpose(transpose(x)) 패턴을 참고해서 reshape 버전 작성

2. lit/FileCheck 테스트 작성:
   ```
   // experiments/toy-rewrites/test_add_zero.mlir
   // RUN: toyc-ch3 %s -emit=mlir -opt | FileCheck %s
   
   func.func @main() {
     %0 = toy.constant dense<[[1.0, 2.0], [3.0, 4.0]]> : tensor<2x2xf64>
     %1 = toy.constant dense<[[0.0, 0.0], [0.0, 0.0]]> : tensor<2x2xf64>
     %2 = toy.add(%0, %1) : (tensor<2x2xf64>, tensor<2x2xf64>) -> tensor<2x2xf64>
     toy.print %2 : tensor<2x2xf64>
     // CHECK-NOT: toy.add
   }
   ```

**산출물:** rewrite 3개 구현 + FileCheck 테스트 2개+ → `experiments/toy-rewrites/` 커밋

---

### Day 25 (주중 저녁, 1시간) — 교차 읽기: 실전 프로젝트의 Rewrite

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

### Day 26~28 (주말 + 다음 주 첫날, 3~4시간) — 정리 + 주간 메모

**Day 26 (주말 2시간):**

1. `week04.md` 초안 작성
2. fold / canonicalization / dialect conversion 차이를 자기 말로 정리
3. Toy와 StableHLO 예시를 나란히 놓고 비교 메모 작성

**Day 27~28:**
- notes/week04.md 정리
- 실험 코드 + 테스트 최종 커밋
- 블로그 초안 다듬기 (게시는 Phase 1 끝에)

**산출물:** notes/week04.md + rewrite 실험 코드

---

## Week 5: Ch4~5 — Dialect Conversion + Lowering (5주차) ★ 가장 중요한 주

### Week 5 병행 읽기

- `11_Control_Flow.pdf`
- `12_Data_Flow.pdf`

이번 주부터는 "변환"뿐 아니라 "변환 이후 어떤 분석이 가능해지는가"를 함께 본다.

### Day 29 (주중 저녁, 1.5시간) — Ch4: Interfaces

**할 일:**
1. Toy Tutorial Ch4 문서 정독:
   - Shape inference interface
   - Op interface의 개념: "op이 특정 계약을 준수함을 선언"
   - Python 비유: Protocol/ABC (Abstract Base Class)

2. 핵심 코드:
   ```cpp
   // ShapeInferenceInterface — op이 output shape를 추론할 수 있음을 선언
   class ShapeInference {
     virtual void inferShapes() = 0;
   };
   
   // Python 대응
   class ShapeInference(Protocol):
       def infer_shapes(self) -> None: ...
   ```

3. `toyc-ch4` 빌드 + shape inference 확인:
   ```bash
   cmake --build . -t toyc-ch4
   ./build/bin/toyc-ch4 /tmp/test.toy -emit=mlir -opt
   # generic tensor → 구체적 shape (tensor<2x3xf64>)로 변환되는지 확인
   ```

**산출물:** "Interface = Protocol/ABC" 비유 정리

---

### Day 30 (주중 저녁, 1.5시간) — Ch5 (1): Partial Lowering 개념

**할 일:**
1. Toy Tutorial Ch5 문서 정독 (전반부):
   - "Partial lowering": 일부 op만 lower하고 나머지는 남겨둠
   - Dialect Conversion Framework의 세 가지 핵심 구성요소:
     - **ConversionTarget**: 어떤 op이 legal(유지)/illegal(변환 필요)인지
     - **Rewrite Patterns**: 어떻게 변환할지
     - **Type Converter**: 타입을 어떻게 변환할지

2. **핵심 개념을 코드에서 확인:**
   ```cpp
   // ConversionTarget 설정
   ConversionTarget target(getContext());
   target.addLegalDialect<affine::AffineDialect, 
                           arith::ArithDialect,
                           func::FuncDialect,
                           memref::MemRefDialect>();
   target.addIllegalDialect<ToyDialect>();  // Toy op은 전부 변환해야 함
   
   // 하지만 PrintOp은 아직 남겨둠 (partial)
   target.addLegalOp<toy::PrintOp>();
   ```

    비유:
    ```text
    모든 op를 한 번에 다 내리지 않고,
    지금 처리 가능한 op만 legal target으로 보내고
    나머지는 잠시 남겨두는 것이 partial lowering.
    ```

3. **`--mlir-print-ir-after-all` 플래그로 중간 IR 관찰:**
   ```bash
   ./build/bin/toyc-ch5 /tmp/test.toy -emit=mlir-affine -opt \
     2>&1 | head -200
   # 각 pass 후의 IR 변화를 관찰
   ```

**산출물:** "ConversionTarget / Pattern / TypeConverter" 핵심 정리

---

### Day 31 (주중 저녁, 1.5시간) — Ch5 (2): Lowering 패턴 분석 + 직접 작성

**할 일:**
1. Ch5의 lowering 패턴 코드 분석:
   ```cpp
   // toy.transpose → linalg.transpose (또는 affine loops)로 변환
   struct TransposeOpLowering : public ConversionPattern {
     LogicalResult matchAndRewrite(
         Operation *op, ArrayRef<Value> operands,
         ConversionPatternRewriter &rewriter) const override {
       // 1. 입력 op 분석
       // 2. 새로운 lower-level op 생성
       // 3. 원래 op를 새 op으로 교체
       rewriter.replaceOp(op, newOp);
       return success();
     }
   };
   ```

2. **Week 3에서 추가한 NegOp의 lowering 패턴 작성:**
   ```cpp
   // toy.neg(x) → arith.negf(x) 로 lower
   struct NegOpLowering : public ConversionPattern {
     // ...
     LogicalResult matchAndRewrite(...) const override {
       auto negOp = cast<toy::NegOp>(op);
       auto input = operands[0];
       auto negResult = rewriter.create<arith::NegFOp>(loc, input);
       rewriter.replaceOp(op, negResult);
       return success();
     }
   };
   ```

3. 빌드 + 테스트:
   ```bash
   # NegOp lowering이 동작하는지 확인
   # toy.neg가 arith.negf로 변환되는지 IR 확인
   ```

**산출물:** NegOp lowering 패턴 구현 + before/after IR 예제

---

### Day 32 (주중 저녁, 1.5시간) — ★ production lowering 첫 진지한 읽기

**할 일:**
이번 날이 Phase 1의 핵심 전환점. Ch5에서 배운 dialect conversion을 production MLIR 코드에 연결한다.

1. **StableHLO→Linalg lowering 관련 파일 열기:**
   `stablehlo/transforms/StablehloLegalizeToLinalgPass.cpp` 또는 대응 파일 탐색

2. **읽기 목표 (전부 이해 X, 구조만):**

   **(a) ConversionTarget 설정 찾기:**
   ```cpp
   // 이런 형태가 있을 것:
    target.addLegalDialect<linalg::LinalgDialect>();
    target.addIllegalDialect<stablehlo::StablehloDialect>();
    ```
    → source op은 illegal, target dialect op은 legal

   **(b) 개별 conversion 패턴 2~3개 읽기:**
    - elementwise op 변환
    - tensor/shape 관련 변환
    - matmul 계열 op 변환

   **(c) Toy Ch5의 패턴과 구조 비교:**
   ```
    Toy:        toy.transpose → affine loops     (간단)
    StableHLO:  dot_general → linalg.matmul      (복잡하지만 구조는 같음!)
   
   둘 다:
   1. matchAndRewrite 메서드
   2. operands 추출
   3. 새 op 생성 (rewriter.create<>)
   4. 원래 op 교체 (rewriter.replaceOp)
   ```

3. **TritonToCudaTile는 선택 확장:**
   시간이 남으면 `TritonToCudaTile.cpp`를 열어 같은 구조가 반복되는지만 본다.

**산출물:** production lowering 첫 인상 메모 — 구조, 읽은 패턴 2~3개, 모르는 부분

---

### Day 33~35 (주말 + 월요일) — Dialect Conversion 문서 + 교차 읽기 + 정리

**Day 33 (주말 2시간):**

1. **Dialect Conversion 공식 문서 정독:**
   - Full conversion vs Partial conversion vs Analysis conversion
   - Type conversion과 materialization
   - Legalization: "모든 illegal op이 변환될 때까지 반복"

2. **교차 읽기 — 세 프로젝트의 dialect conversion 비교:**

   | | Toy Ch5 | StableHLO→Linalg | TritonToCudaTile (선택) |
   |---|---------|------------------|------------------------|
   | Source dialect | Toy | StableHLO | Triton (TTIR) |
   | Target dialect | Affine + Arith | Linalg + Arith | CUDA Tile |
   | Conversion 종류 | Partial | Full | Full (?) |
   | Type conversion | tensor→memref | tensor→tensor | tensor→tile(?) |
   | 복잡도 | 간단 | 높음 | 중간~높음 |

3. **선택 확장:**
   Triton 메인의 `ConvertTritonToTritonGPU`, `TritonToCudaTile`도 같은 프레임워크를 쓰는지 확인

**Day 34 (주말 1~2시간):**

1. **선택 확장:**
   시간이 남으면 TritonToCudaTile / ConvertTritonToTritonGPU를 열어
   같은 프레임워크가 더 복잡한 곳에서 어떻게 쓰이는지 확인

**Day 35:**
- `notes/week05.md` 정리 (Week 5 = Phase 1에서 가장 중요한 주)
- dialect conversion 정리 메모 보강
- 실험 코드 커밋 (NegOp lowering, before/after IR)

**산출물:** notes/week05.md + "Toy / StableHLO / (선택) Triton dialect conversion 비교" + NegOp lowering 코드

---

## Week 6: Ch6~7 — LLVM Lowering + 전체 복습 + 블로그 완성 (6주차)

### Week 6 병행 읽기

- `17_SSA.pdf` 재복습
- `10_Instruction_Selection.pdf`는 선택적으로 읽되, LLVM IR 이후의 다음 단계가 어떤 문제를 다루는지 감만 잡는다

### Day 36 (주중 저녁, 1.5시간) — Ch6: LLVM Dialect으로 최종 Lowering

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

### Day 37 (주중 저녁, 1시간) — Ch7: Composite Type

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

### Day 38 (주중 저녁, 1.5시간) — 전체 파이프라인 복습 + 자가 테스트

**할 일:**
1. **자가 테스트 — 아래 질문에 대답할 수 있는지:**
   - [ ] Operation, Block, Region, Dialect을 각각 설명할 수 있다
   - [ ] ODS/TableGen으로 op을 정의하는 흐름을 설명할 수 있다
   - [ ] fold와 pattern의 차이를 설명할 수 있다
   - [ ] ConversionTarget, RewritePattern, TypeConverter의 역할을 설명할 수 있다
   - [ ] partial lowering이 왜 필요한지 설명할 수 있다
   - [ ] Toy 전체 파이프라인 (AST → Toy → Affine → LLVM → LLVM IR)을 그릴 수 있다
    - [ ] 위 패턴이 StableHLO/IREE 같은 production MLIR 코드에서 어떻게 쓰이는지 설명할 수 있다

2. 못 대답하는 항목 → 해당 문서/코드 다시 확인

**산출물:** 자가 테스트 결과 + 부족한 부분 메모

---

### Day 39 (주중 저녁, 1시간) — production MLIR 파이프라인 비교 다이어그램

**할 일:**
1. Phase 0에서 그린 생태계 조감도를 더 구체화:

   ```
   [Toy 파이프라인]
   Toy DSL → Toy dialect → Affine+Arith → LLVM dialect → LLVM IR
   
    [XLA 파이프라인]
    JAX/TF → StableHLO → HLO → XLA passes → LLVM/Triton → binary

    [IREE 파이프라인]
    StableHLO/TOSA → Linalg → Flow/HAL → LLVM → binary

    [Triton 파이프라인] (후반 확장)
    Python DSL → TTIR → TTGIR(+layout) → LLVM IR(+NVVM) → PTX → CUBIN
   
   [cuTile 파이프라인]
   Python DSL → CUDA Tile IR → tileiras → GPU binary
   ```

2. 각 파이프라인에서 "dialect conversion이 일어나는 지점"을 화살표로 표시

**산출물:** `diagrams/pipeline-comparison-v2.md` — 5개 파이프라인 비교 다이어그램

---

### Day 40~42 (주말 + 월요일) — 블로그 완성 + Phase 1 종합

**Day 40 (주말 2시간) — 블로그 글 2편 완성:**

**블로그 #2:** "MLIR Toy Tutorial을 끝내고 나서: 컴파일러에서 반복되는 3가지 패턴"

```markdown
# MLIR Toy Tutorial을 끝내고: AI 컴파일러에서 반복되는 3가지 패턴

## 들어가며
Toy Tutorial 7개 챕터를 완주했다.
직접 NegOp을 추가하고, rewrite 패턴을 쓰고, lowering pass를 구현했다.
그리고 나서 Triton, StableHLO, CUDA Tile 코드를 열어봤더니,
같은 패턴이 계속 반복되고 있었다.

## 패턴 1: Op 정의는 선언적으로 (ODS/TableGen)
- Toy의 .td vs StableHLO의 .td
- 복잡도는 다르지만 구조는 동일

## 패턴 2: 변환은 match-and-rewrite로 (Pattern Rewrite)
- transpose(transpose(x)) → x (Toy)
- Canonicalization (StableHLO)
- structured transform 예시 (IREE/Linalg)

## 패턴 3: Lowering은 dialect conversion으로
- Toy → Affine → LLVM
- StableHLO → Linalg (IREE)
- (후반 확장) TTIR → CUDA Tile IR

## 마무리
```

**Day 41 (주말 1~2시간) — 최종 정리:**

1. `notes/week06.md` 작성
2. GitHub 리포 최종 업데이트:
   ```
    compiler-study/
   ├── notes/
   │   ├── week03.md    ← Ch1~2, Op 정의
   │   ├── week04.md    ← Ch3, Rewrite
   │   ├── week05.md    ← Ch4~5, Dialect Conversion ★
   │   └── week06.md    ← Ch6~7, 전체 복습
   ├── blog-drafts/
   │   ├── 01-ai-compiler-landscape.md     ← (Phase 0)
   │   └── 02-toy-tutorial-three-patterns.md ← (Phase 1)
   ├── experiments/
   │   ├── toy-custom-ops/neg_op/          ← NegOp 추가
   │   ├── toy-rewrites/                   ← rewrite 3개 + 테스트
   │   ├── toy-lowering/                   ← NegOp lowering
   │   └── ir-dumps/                       ← 각 단계별 IR 덤프
   └── diagrams/
       └── pipeline-comparison-v2.md       ← 5개 파이프라인 비교
   ```

3. 블로그 2편 게시

**Day 42:**
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
