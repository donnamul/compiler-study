# Phase 1: 컴파일러 기초 + MLIR Toy Tutorial + 실전 프로젝트 교차 — 상세 계획

> **기간**: 4주 (3~6주차)
> **시간**: 주중 저녁 1~1.5시간 + 주말 3~4시간
> **핵심 산출물**: Toy Tutorial 완주, 수업 자료 핵심 개념 정리, custom op 추가 경험, 실전 프로젝트 교차 분석, 블로그 2편, GitHub 리포 업데이트

---

## Phase 1 전체 구조

```
Week 3: Ch1~2 + 01/09/17 강의  → "IR/SSA와 dialect가 연결된다"
Week 4: Ch3   + 02~07/22 강의  → "front-end와 rewrite가 이어진다"  
Week 5: Ch4~5 + 11/12 강의     → "lowering, CFG, analysis가 연결된다" ★
Week 6: Ch6~7 + 17 재복습      → "전체 파이프라인이 하나로 보인다"
```

★ Week 5가 가장 중요. `TritonToCudaTile.cpp`를 처음 진지하게 읽는 주.

---

## Phase 1 업데이트 전제

이 Phase는 이제 아래 세 축을 병행한다.

1. **수업 자료**: `/Users/juntaek/Documents/Cmp./Cmp`
2. **학습용 구현**: `llvm-project/mlir/examples/toy/`
3. **실전 코드**: Triton / Triton-to-tile-IR / StableHLO

### 수업 자료를 붙이는 이유

- Toy는 구현을 보여주지만, parsing/semantic analysis/SSA/CFG를 체계적으로 설명하지는 않는다.
- 반대로 강의 자료는 이론을 주지만, MLIR/Triton 코드와 바로 연결되지는 않는다.
- 따라서 Phase 1에서는 "강의에서 개념을 잡고 → Toy에서 구조를 보고 → 실전 프로젝트에서 확장된 형태를 읽는" 흐름으로 간다.

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
- 구현은 여전히 Toy/Triton 중심으로 한다. 수업 자료는 보조 축이다.

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

### Day 19 (주중 저녁, 1시간) — 교차 읽기: 실전 프로젝트의 Op 정의

**할 일:**
1. **Triton의 Op 정의** (`triton/include/triton/Dialect/Triton/IR/TritonOps.td`):
   GitHub에서 열어서 `tt.load`, `tt.store`, `tt.dot` 정의 구조 확인.
   Toy의 단순 op과 비교:
   - Triton op에는 `memory_order`, `cache` 같은 attribute가 있음
   - type constraint가 더 복잡 (pointer type, tensor of pointers 등)

2. **StableHLO의 Op 정의** (`stablehlo/dialect/StablehloOps.td`):
   GitHub에서 `DotGeneralOp` (matmul) 정의 확인:
   - `dot_dimension_numbers` attribute
   - 정교한 verifier와 type inference
   - 100개+ op이 체계적으로 정의되어 있음

3. **NVIDIA/cuda-tile의 Op 정의**:
   GitHub에서 `.td` 파일 찾아서 CUDA Tile dialect의 op 구조 확인

**비교 정리:**
| 프로젝트 | Op 수 | Verifier 복잡도 | Type Inference | 특이사항 |
|----------|-------|----------------|----------------|----------|
| Toy | ~5 | 거의 없음 | 없음 | 학습용 |
| Triton | ~30 | 중간 | 있음 | memory semantics |
| StableHLO | ~100 | 높음 | 정교함 | 완전한 spec |
| CUDA Tile | ? | ? | ? | 이번에 확인 |

**산출물:** "프로젝트별 Op 정의 스타일 비교" 메모

### Week 3 종료 체크

- [ ] `01_Intro.pdf`를 읽고 Toy의 AST 위치를 설명할 수 있다
- [ ] `09_Intermediate_Representation.pdf`를 읽고 AST와 IR의 차이를 설명할 수 있다
- [ ] `17_SSA.pdf`를 읽고 MLIR의 `%0`, `%1`가 왜 자연스러운지 설명할 수 있다
- [ ] Toy Ch1~2에서 AST → MLIR로 넘어가는 흐름을 말할 수 있다

---

### Day 20~21 (주말, 3~4시간) — Ch2 복습 + torch.compile 연결 + 정리

**Day 20 (2시간) — torch.compile에서의 "Op 정의"와 비교:**

1. **FX Graph의 Op과 MLIR Op의 대응:**
   ```python
   # torch.compile이 만드는 FX Graph:
   # call_function: aten.mm.default(arg0, arg1)
   # call_function: aten.add.Tensor(mm, arg2)
   
   # 이것이 Triton TTIR에서는:
   # %0 = tt.dot %arg0, %arg1 : tensor<...> -> tensor<...>
   # %1 = arith.addf %0, %arg2 : tensor<...>
   
   # 이것이 StableHLO에서는:
   # %0 = stablehlo.dot_general %arg0, %arg1, ...
   # %1 = stablehlo.add %0, %arg2 : tensor<...>
   
   # Legato에서는:
   # legato.matmul(%arg0, %arg1) 같은 형태일 것
   ```

2. **ATen Op → Triton Op 매핑 정리:**
   네가 이미 공부한 TorchInductor의 lowering과 연결:
   - `aten.mm` → Triton `tt.dot`
   - `aten.add` → Triton `arith.addf`
   - `aten.relu` → Triton `arith.maximumf` (with 0)
   
   이 매핑이 바로 "dialect conversion"의 구체적 인스턴스!

3. **실험:** Inductor가 생성하는 Triton 코드에서 Op을 식별
   ```python
   # experiments/torch-compile-to-triton/op_mapping.py
   import torch
   
   @torch.compile(backend="inductor")
   def f(x, y):
       return torch.relu(x @ y)
   
   x = torch.randn(32, 32, device='cuda')
   y = torch.randn(32, 32, device='cuda')
   result = f(x, y)
   
   # TORCH_COMPILE_DEBUG=1 로 실행하면 생성된 Triton 코드 확인 가능
   ```

**Day 21 (1~2시간) — Week 3 종합 정리:**

1. `notes/week03.md` 완성:
   ```markdown
   # Week 3: MLIR Op 정의의 세계
   
   ## 배운 것
   - Toy Ch1: AST 구조, Lexer/Parser
   - Toy Ch2: MLIR IR 생성, ODS/TableGen
   - NegOp 직접 추가해봄
   
   ## 교차 읽기
   - Triton vs StableHLO vs CUDA Tile의 Op 정의 비교
   
   ## torch.compile 연결
   - ATen Op → Triton Op 매핑 = dialect conversion
   - FX Graph의 node가 MLIR의 Operation에 대응
   
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
   ├── mlir-basics/              ← Phase 0에서 만든 것
   └── torch-compile-to-triton/
       └── op_mapping.py         ← ATen→Triton Op 매핑 실험
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
1. **Triton의 `RemoveLayoutConversions` pass:**
   `lib/Dialect/TritonGPU/Transforms/RemoveLayoutConversions.cpp`
   
   이건 Triton에서 가장 중요한 최적화 중 하나:
   - TritonGPU dialect에서 `ttg.convert_layout` op이 과다 생성됨
   - 이 pass가 불필요한 layout conversion을 제거
   - 4-phase 알고리즘: anchor 결정 → 전파 → 최적 layout 선택 → 변환
   
   지금은 전체 알고리즘을 이해할 필요 없고, `matchAndRewrite` 패턴이
   Toy Ch3에서 배운 것과 같은 구조인지만 확인.

2. **Triton-to-tile-IR의 `rewriteAssume` pass:**
   `lib/` 아래에서 `rewriteAssume` 관련 파일 찾기.
   - assume op을 CUDA Tile IR의 assume op으로 변환
   - 패턴 구조가 Toy의 TransposeTranspose 제거와 어떻게 비슷한지 확인

3. **StableHLO의 canonicalization:**
   `stablehlo/transforms/` 에서 canonicalization pass 파일 열어보기.
   - `stablehlo.add(x, 0) → x` 같은 fold가 정의되어 있는지 확인
   - 네가 방금 Toy에서 구현한 것과 같은 패턴!

**산출물:** "세 프로젝트의 rewrite 비교" 메모 (구조, 복잡도, 적용 방식)

---

### Day 26~28 (주말 + 다음 주 첫날, 3~4시간) — 정리 + 블로그 초안

**Day 26 (주말 2시간):**

1. **torch.compile에서의 "rewrite"와 비교:**
   ```
   [torch.compile 세계의 rewrite들]
   
   1. FX Graph 수준:
      - Dynamo의 guard 기반 graph 캐싱
      - FX 수준 패턴 매칭 (subgraph_rewriter)
   
   2. Inductor IR 수준:
      - Post-grad fusion pass
      - Pointwise op fusion
   
   3. Triton 수준:
      - MLIR canonicalize, CSE
      - RemoveLayoutConversions
   
   [MLIR 세계의 rewrite들]
   
   1. Fold: 단일 op의 상수 정리
   2. Canonicalization pattern: op 정규화
   3. Dialect conversion pattern: dialect 간 변환 (다음 주 배움)
   
   핵심 차이: torch.compile은 여러 레벨에서 ad-hoc 최적화를 하지만,
   MLIR은 단일 rewrite 프레임워크로 모든 레벨의 변환을 표현할 수 있음.
   ```

2. 블로그 초안 시작 (`blog-drafts/02-mlir-rewrite-patterns.md`):
   ```markdown
   # MLIR의 Pattern Rewrite: torch.compile 개발자가 보는 관점
   
   ## fold와 pattern의 차이
   ## transpose(transpose(x)) → x 를 직접 구현해보다
   ## Triton의 RemoveLayoutConversions도 같은 구조다
   ## torch.compile의 최적화와 비교하면
   ```

**Day 27~28:**
- notes/week04.md 정리
- 실험 코드 + 테스트 최종 커밋
- 블로그 초안 다듬기 (게시는 Phase 1 끝에)

**산출물:** notes/week04.md + 블로그 초안 + rewrite 실험 코드

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

   torch.compile 비유:
   ```python
   # Inductor에서도 비슷한 일이 일어남:
   # - aten.mm → triton 커널로 lower (illegal → legal)
   # - aten.embedding → fallback으로 남김 (legal 유지)
   # 이게 바로 "partial lowering"!
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

### Day 32 (주중 저녁, 1.5시간) — ★ TritonToCudaTile.cpp 첫 진지한 읽기

**할 일:**
이번 날이 Phase 1의 핵심 전환점. Ch5에서 배운 dialect conversion을 실전에서 확인.

1. **`TritonToCudaTile` 관련 파일 열기:**
   Triton-to-tile-IR 리포에서 `lib/Conversion/` 또는 관련 디렉토리를 탐색

2. **읽기 목표 (전부 이해 X, 구조만):**

   **(a) ConversionTarget 설정 찾기:**
   ```cpp
   // 이런 형태가 있을 것:
   target.addLegalDialect<cuda_tile::CudaTileDialect>();
   target.addIllegalDialect<triton::TritonDialect>();
   ```
   → Triton op은 illegal, CUDA Tile op은 legal

   **(b) 개별 conversion 패턴 2~3개 읽기:**
   - 가장 단순한 elementwise op 변환 (예: add)
   - `tt.load` → CUDA Tile load 변환 (더 복잡)
   - `tt.dot` → CUDA Tile matmul 변환 (가장 복잡)

   **(c) Toy Ch5의 패턴과 구조 비교:**
   ```
   Toy:     toy.transpose → affine loops     (간단)
   Triton:  tt.dot → cuda_tile.dot           (복잡하지만 구조는 같음!)
   
   둘 다:
   1. matchAndRewrite 메서드
   2. operands 추출
   3. 새 op 생성 (rewriter.create<>)
   4. 원래 op 교체 (rewriter.replaceOp)
   ```

3. **못 읽은 부분 기록:**
   - "이 부분은 모르겠다" → notes에 정직하게 기록
   - 특히 type conversion, TMA 관련 코드는 아직 이해 못해도 정상

**산출물:** "TritonToCudaTile 첫 인상" 메모 — 구조, 읽은 패턴 2~3개, 모르는 부분

---

### Day 33~35 (주말 + 월요일) — Dialect Conversion 문서 + 교차 읽기 + 정리

**Day 33 (주말 2시간):**

1. **Dialect Conversion 공식 문서 정독:**
   - Full conversion vs Partial conversion vs Analysis conversion
   - Type conversion과 materialization
   - Legalization: "모든 illegal op이 변환될 때까지 반복"

2. **교차 읽기 — 세 프로젝트의 dialect conversion 비교:**

   | | Toy Ch5 | TritonToCudaTile | StableHLO→Linalg |
   |---|---------|-----------------|------------------|
   | Source dialect | Toy | Triton (TTIR) | StableHLO |
   | Target dialect | Affine + Arith | CUDA Tile | Linalg + Arith |
   | Conversion 종류 | Partial | Full (?) | Full |
   | Type conversion | tensor→memref | tensor→tile(?) | tensor→tensor |
   | 복잡도 | 간단 | 중간~높음 | 높음 |

3. **Triton 메인의 `ConvertTritonToTritonGPU` 도 비교:**
   - TTIR → TTGIR 변환: layout encoding attribute를 추가하는 변환
   - 이것도 같은 dialect conversion 프레임워크 사용

**Day 34 (주말 1~2시간):**

1. **torch.compile 연결:**
   ```
   [torch.compile의 "lowering" 단계들]
   
   Python → FX Graph                    ≈ Source → High-level dialect
   FX Graph → Inductor IR              ≈ High-level → Mid-level dialect  
   Inductor IR → Triton kernel code    ≈ Mid-level → Low-level dialect
   Triton TTIR → TTGIR → PTX           ≈ Dialect conversion chain
   
   [핵심 통찰]
   torch.compile의 각 lowering 단계가 MLIR의 dialect conversion과 1:1 대응.
   다만 torch.compile은 각 단계가 서로 다른 프레임워크로 구현되어 있고,
   MLIR은 단일 프레임워크 안에서 모든 변환을 표현.
   
   Legato가 하는 것:
   FX Graph → (torch.compile backend) → Legato IR → MLIR → HyperAccel binary
   = 결국 dialect conversion chain의 커스텀 인스턴스
   ```

**Day 35:**
- `notes/week05.md` 정리 (Week 5 = Phase 1에서 가장 중요한 주)
- 블로그 초안 02에 dialect conversion 내용 추가
- 실험 코드 커밋 (NegOp lowering, before/after IR)

**산출물:** notes/week05.md + "세 프로젝트의 dialect conversion 비교" + NegOp lowering 코드

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
   - [ ] 위 패턴이 Triton-to-tile-IR에서 어떻게 쓰이는지 대략 설명할 수 있다

2. 못 대답하는 항목 → 해당 문서/코드 다시 확인

**산출물:** 자가 테스트 결과 + 부족한 부분 메모

---

### Day 39 (주중 저녁, 1시간) — Triton 5개 파이프라인 비교 다이어그램

**할 일:**
1. Phase 0에서 그린 생태계 조감도를 더 구체화:

   ```
   [Toy 파이프라인]
   Toy DSL → Toy dialect → Affine+Arith → LLVM dialect → LLVM IR
   
   [Triton PTX 파이프라인]
   Python DSL → TTIR → TTGIR(+layout) → LLVM IR(+NVVM) → PTX → CUBIN
   
   [Triton TileIR 파이프라인]
   Python DSL → TTIR → CUDA Tile IR → tileiras → GPU binary
   
   [XLA 파이프라인]
   JAX/TF → StableHLO → HLO → XLA passes → LLVM/Triton → binary
   
   [cuTile 파이프라인]
   Python DSL → CUDA Tile IR → tileiras → GPU binary
   ```

2. 각 파이프라인에서 "dialect conversion이 일어나는 지점"을 화살표로 표시

**산출물:** `diagrams/pipeline-comparison-v2.md` — 5개 파이프라인 비교 다이어그램

---

### Day 40~42 (주말 + 월요일) — 블로그 완성 + Phase 1 종합

**Day 40 (주말 2시간) — 블로그 글 2편 완성:**

**블로그 #2:** "MLIR Toy Tutorial을 끝내고 나서: AI 컴파일러에서 반복되는 3가지 패턴"

```markdown
# MLIR Toy Tutorial을 끝내고: AI 컴파일러에서 반복되는 3가지 패턴

## 들어가며
Toy Tutorial 7개 챕터를 완주했다.
직접 NegOp을 추가하고, rewrite 패턴을 쓰고, lowering pass를 구현했다.
그리고 나서 Triton, StableHLO, CUDA Tile 코드를 열어봤더니,
같은 패턴이 계속 반복되고 있었다.

## 패턴 1: Op 정의는 선언적으로 (ODS/TableGen)
- Toy의 .td vs Triton의 .td vs StableHLO의 .td
- 복잡도는 다르지만 구조는 동일

## 패턴 2: 변환은 match-and-rewrite로 (Pattern Rewrite)
- transpose(transpose(x)) → x (Toy)
- RemoveLayoutConversions (Triton)
- Canonicalization (StableHLO)

## 패턴 3: Lowering은 dialect conversion으로
- Toy → Affine → LLVM
- TTIR → CUDA Tile IR (Triton-to-tile-IR)
- StableHLO → Linalg (IREE)

## torch.compile 개발자의 시선으로
이 3가지 패턴이 torch.compile의 각 단계와 어떻게 대응하는지

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
| 7 | TritonToCudaTile.cpp 구조 파악 (완전 이해 아님) | ☐ |
| 8 | 3개 프로젝트의 Op 정의 비교 | ☐ |
| 9 | 3개 프로젝트의 Rewrite 비교 | ☐ |
| 10 | 3개 프로젝트의 Dialect Conversion 비교 | ☐ |
| 11 | torch.compile ↔ MLIR 변환의 대응 관계 정리 | ☐ |
| 12 | 5개 파이프라인 비교 다이어그램 | ☐ |
| 13 | 블로그 글 1편 완성 (총 2편째) | ☐ |
| 14 | notes/week03~06.md 전체 정리 | ☐ |

---

## Phase 1에서 Phase 2로 넘어갈 때의 상태

- `.td`로 op을 정의하고, TableGen이 C++ 코드를 생성하는 흐름을 이해한다
- fold와 pattern rewrite를 직접 구현해봤다
- dialect conversion의 세 구성요소 (Target, Pattern, TypeConverter)를 설명할 수 있다
- TritonToCudaTile.cpp의 구조를 대략 알고, 개별 패턴 2~3개를 읽었다
- 5개 AI 컴파일러 프로젝트의 파이프라인을 비교할 수 있다
- torch.compile의 각 단계가 MLIR의 어떤 메커니즘에 대응하는지 설명할 수 있다
- GitHub에 실험 코드가 쌓이고 있고, 블로그 글이 2편이다

**다음 Phase 2에서는:**
- 나만의 custom dialect을 C++로 만든다 (Toy가 아닌 독립 프로젝트)
- TritonToCudaTile.cpp를 체계적으로 분석한다
- Bufferization과 메모리 모델을 배운다
