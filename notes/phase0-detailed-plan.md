# Phase 0: 환경 세팅 + MLIR 기초 감각 만들기 — 상세 계획

> **기간**: 2주 (1~2주차)
> **시간**: 주중 저녁 1~1.5시간 + 주말 3~4시간
> **핵심 산출물**: MLIR 빌드 완료, GitHub 학습 리포, Week 01~02 노트, MLIR 기초 예제

---

## Week 1: 빌드 + MLIR 기초 + 디렉토리 탐험

### Day 1 (주중 저녁, 1.5시간) — 사전 준비

**할 일:**
1. 빌드에 필요한 도구 설치 확인
   ```bash
   # Ubuntu
   sudo apt-get install cmake ninja-build ccache clang lld git python3-dev
   
   # macOS
   brew install cmake ninja ccache
   ```

2. 학습용 GitHub 리포 생성
   ```
   리포 이름: compiler-study (또는 mlir-journey 등)
   구조:
   ├── README.md          ← 학습 로드맵 + 진행 상황
   ├── notes/             ← 주간 학습 노트 (마크다운)
   │   ├── week01.md
   │   └── ...
   ├── blog-drafts/       ← 블로그 초안
   ├── experiments/        ← 실험 코드 (.mlir 파일, 작은 pass 등)
   │   ├── mlir-basics/
   │   └── triton-ir-dumps/
   └── diagrams/          ← 파이프라인 비교 다이어그램 등
   ```

3. `README.md` 초안 작성:
   - 자기소개 (AI compiler engineer at HyperAccel, Legato 컴파일러 개발)
   - 학습 목표 (MLIR C++ 레벨 이해 → 이후 MLIR 관련 프로젝트 기여)
   - 16주 로드맵 요약

**산출물:** GitHub 리포 생성 + README.md 커밋

---

### Day 2 (주중 저녁, 1.5시간) — MLIR 소스 클론 + 빌드 시작

**할 일:**
1. llvm-project 클론 (시간이 걸리니 백그라운드로)
   ```bash
   git clone https://github.com/llvm/llvm-project.git
   ```

2. 클론 기다리면서 MLIR 공식 사이트 읽기
   - https://mlir.llvm.org/ 메인 페이지
   - "MLIR: A Compiler Infrastructure for the End of Moore's Law" 논문의 abstract + intro만

3. 빌드 cmake 명령 준비 (아직 실행하지 않아도 됨)
   ```bash
   mkdir llvm-project/build && cd llvm-project/build
   cmake -G Ninja ../llvm \
     -DLLVM_ENABLE_PROJECTS=mlir \
     -DLLVM_BUILD_EXAMPLES=ON \
     -DLLVM_TARGETS_TO_BUILD="Native;NVPTX;AMDGPU" \
     -DCMAKE_BUILD_TYPE=Release \
     -DLLVM_ENABLE_ASSERTIONS=ON \
     -DCMAKE_C_COMPILER=clang \
     -DCMAKE_CXX_COMPILER=clang++ \
     -DLLVM_ENABLE_LLD=ON \
     -DLLVM_CCACHE_BUILD=ON
   ```

**빌드 팁:**
- `LLVM_TARGETS_TO_BUILD="Native"`만 해도 대부분 충분. NVPTX/AMDGPU는 나중에 필요하면 추가
- 메모리 부족 시: `-DLLVM_PARALLEL_LINK_JOBS=1` 추가 (링크 단계가 메모리를 많이 먹음)
- 전체 빌드 대신 필요한 타겟만: `cmake --build . -t mlir-opt mlir-translate` (훨씬 빠름)
- ccache 덕에 이후 재빌드는 첫 빌드보다 훨씬 빠름

**산출물:** 클론 완료, cmake configure 성공 (빌드는 밤새 돌려놓기)

---

### Day 3 (주중 저녁, 1시간) — 빌드 확인 + mlir-opt 첫 사용

**할 일:**
1. 빌드 결과 확인
   ```bash
   # 빌드 완료 확인
   ls build/bin/mlir-opt
   ls build/bin/toyc-ch7
   
   # MLIR 테스트 실행 (선택, 시간 오래 걸림)
   # cmake --build . --target check-mlir
   ```

2. `mlir-opt` 첫 사용 — 간단한 .mlir 파일 만들어서 돌리기
   ```bash
   # experiments/mlir-basics/hello.mlir
   cat << 'EOF' > hello.mlir
   func.func @add(%arg0: i32, %arg1: i32) -> i32 {
     %0 = arith.addi %arg0, %arg1 : i32
     return %0 : i32
   }
   EOF
   
   # 파싱 + 덤프 (round-trip 확인)
   ./build/bin/mlir-opt hello.mlir
   
   # CSE pass 적용해보기
   ./build/bin/mlir-opt --cse hello.mlir
   
   # 사용 가능한 pass 목록 보기
   ./build/bin/mlir-opt --help | head -100
   ```

3. 학습 노트에 기록: `notes/week01.md`
   - 빌드 과정에서 겪은 이슈
   - `mlir-opt`로 해본 것
   - 눈에 띈 MLIR 문법 요소들

**산출물:** `mlir-opt` 동작 확인 + `experiments/mlir-basics/hello.mlir` 커밋

---

### Day 4 (주중 저녁, 1.5시간) — MLIR IR 문법 익히기

**할 일:**
1. MLIR Language Reference 핵심 부분 읽기 (전부 읽지 말고 아래만):
   - Operations: 이름, operands, results, attributes, regions
   - Blocks: block arguments, terminators
   - Regions: SSACFG region vs Graph region
   - Types: built-in types (integer, float, tensor, memref)

2. 다양한 .mlir 예제 파일 작성하고 `mlir-opt`으로 확인
   ```
   experiments/mlir-basics/
   ├── hello.mlir            ← 간단한 함수
   ├── tensor_ops.mlir       ← tensor 타입 사용
   ├── control_flow.mlir     ← scf.for, scf.if
   └── memref_ops.mlir       ← memref 타입 사용
   ```


**산출물:** `.mlir` 예제 4개 읽고 MLIR 기본 개념 정리 메모 작성

---

### Day 5 (주중 저녁, 1시간) — 수업 자료와 MLIR 개념 연결

**할 일:**
1. 강의 PDF에서 IR/SSA/basic block 관련 장표 다시 보기
   - `01_Intro.pdf`
   - `09_Intermediate_Representation.pdf`
   - 필요하면 `17_SSA.pdf` 앞부분

2. 이미 만든 `.mlir` 예제를 다시 열어 아래 개념과 연결
   - operation
   - value
   - block
   - region
   - dialect

3. `notes/week01.md`에 자기 말로 정리
   - LangRef 용어 정리
   - block argument vs LLVM phi
   - attribute vs operand/result/type

**산출물:** `notes/week01.md`의 LangRef/기초 개념 정리

---

### Day 6~7 (주말, 3~4시간) — MLIR 기초 복습 + Toy 진입 준비

**Day 6 전반 (2시간) — MLIR 문서 + Toy 미리보기:**

1. MLIR 공식 문서에서 아래만 다시 읽기
   - LangRef의 operation / block / region / attribute / type
   - Toy Tutorial Ch1 서론

2. 목표
   - Phase 1 들어가기 전에 AST / IR / SSA / dialect 개념을 한 번 더 고정
   - "강의안 개념 → Toy 구현"으로 이어질 준비 만들기

**Day 6 후반 (1시간) — 예제 다시 읽기:**

이미 만든 `.mlir` 예제를 다시 열고 아래 질문에 답한다.

- 이 파일에서 operation은 무엇인가?
- value는 어디서 정의되고 어디서 쓰이는가?
- block argument는 어디서 보이는가?
- region이 필요한 이유는 무엇인가?

**Day 7 (1~2시간) — Week 1 정리 + Week 2 준비:**

1. `notes/week01.md` 최종 정리
2. `notes/week02.md`에 다음 주 질문 미리 적기
3. Toy Tutorial Ch1 진입용 메모 작성

**산출물:**
- `notes/week01.md` 정리 완료
- `notes/week02.md` 초안 준비
- Phase 1 진입 전 질문 목록

---

## Week 2: MLIR 핵심 개념 + LLVM C++ + 커뮤니티 진입

### Day 8 (주중 저녁, 1.5시간) — Operation / Block / Region 깊이 이해

**할 일:**
1. MLIR 공식 문서에서 아래 읽기:
   - "MLIR Language Reference" → Operations 섹션
   - Toy Tutorial Ch1 (읽기만, 코드 따라치기는 다음 Phase)

2. 아래 개념을 자기 말로 정리:

   **Operation** — MLIR의 기본 단위. "뭔가를 하는 것"
   ```
   %result = "dialect.op_name"(%operand1, %operand2) {attr = value} 
              : (input_types) -> output_types
   ```
   - Python 비유: 함수 호출 (`result = f(arg1, arg2, key=value)`)

   **Block** — operation의 선형 리스트 + block arguments
   ```
   ^bb0(%arg0: i32):
     %0 = arith.addi %arg0, %arg0 : i32
     return %0 : i32
   ```
   - Python 비유: 들여쓰기 된 코드 블록

   **Region** — block의 모음. Operation 안에 nested 가능
   ```
   func.func @f() {
     ^entry:           ← 이 블록들이 region을 구성
       ...
     ^loop_body:
       ...
   }
   ```
   - Python 비유: 함수 body, for 루프 body

   **Dialect** — 관련 operation, type, attribute의 묶음
   - Python 비유: 모듈/패키지 (`arith.addi`에서 `arith`가 dialect, `addi`가 op)

3. `.mlir` 파일로 직접 확인:
   ```
   experiments/mlir-basics/
   ├── regions.mlir      ← nested region 예시 (scf.for 안에 scf.if)
   └── blocks.mlir       ← 여러 block + branch 예시
   ```

**산출물:** 개념 정리 메모 + .mlir 예제 2개

---

### Day 9 (주중 저녁, 1시간) — LLVM 스타일 C++ 첫 만남

**할 일:**
1. `llvm-project/mlir/examples/toy/Ch2/` 디렉토리 열기

2. 아래 파일들을 "Python 개발자 시선"으로 훑기 (전부 이해하려 하지 말 것):
   - `include/toy/Ops.td`: op 정의 (TableGen 문법)
   - `mlir/MLIRGen.cpp`: AST → MLIR 변환 로직
   - `mlir/Dialect.cpp`: dialect 등록

3. **만나는 C++ 패턴 3개만 집중:**

   (a) `llvm::isa / cast / dyn_cast`:
   ```cpp
   // C++
   if (auto addOp = dyn_cast<arith::AddIOp>(op)) {
     // addOp를 사용
   }
   
   // Python 대응
   if isinstance(op, arith.AddIOp):
       # op를 사용
   ```

   (b) `SmallVector`:
   ```cpp
   // C++ — 스택에 4개까지, 그 이후 heap
   SmallVector<Value, 4> operands;
   operands.push_back(lhs);
   
   // Python 대응
   operands = []
   operands.append(lhs)
   ```

   (c) Builder 패턴:
   ```cpp
   // C++ — IR 노드를 만드는 factory
   auto constOp = builder.create<arith::ConstantIntOp>(loc, 42, 32);
   
   // Python 대응 (Legato에서도 비슷한 패턴 쓸 것)
   const_op = builder.create_constant(42, dtype=i32)
   ```

**산출물:** "LLVM C++ 패턴 치트시트" (notes/week02.md에 정리)

---

### Day 10 (주중 저녁, 1.5시간) — TableGen/ODS 첫 인상

**할 일:**
1. Toy Ch2의 `Ops.td` 파일을 열고 `TransposeOp` 정의 읽기:
   ```tablegen
   def TransposeOp : Toy_Op<"transpose"> {
     let summary = "transpose operation";
     let arguments = (ins F64Tensor:$input);
     let results = (outs F64Tensor);
     // ...
   }
   ```

2. **빌드 디렉토리에서 생성된 코드 확인:**
   ```bash
   # .td에서 자동 생성된 C++ 코드 찾기
   find build/ -name "*.inc" | grep -i toy
   # 생성된 파일을 열어서 TransposeOp에 해당하는 부분 찾기
   ```
   핵심 통찰: `.td` 파일은 "선언"이고, `mlir-tblgen`이 "구현"을 자동 생성한다.
   Python의 dataclass나 Pydantic 모델에서 선언만 하면 메서드가 자동 생성되는 것과 비슷.

3. **비교 읽기 — StableHLO의 .td 파일:**
   `openxla/stablehlo` 리포에서 `StablehloOps.td`를 GitHub에서 열어보기.
   Toy의 단순한 op 정의와 StableHLO의 production-level op 정의가 어떻게 다른지 비교:
   - verifier 복잡도
   - type inference
   - attribute 종류

**산출물:** "TableGen은 Python의 XXX와 비슷하다" 비유 정리

---

### Day 11 (주중 저녁, 1시간) — Toy Tutorial 진입 준비

**할 일:**
1. Toy Tutorial Ch1~2 목차를 훑고 다음 주 흐름 미리 보기
2. `01_Intro.pdf`, `09_Intermediate_Representation.pdf`, `17_SSA.pdf`에서
   다음 주에 연결할 부분 표시
3. `notes/week02.md`에 "Phase 1에 들어가기 전에 꼭 확인할 질문" 추가

**산출물:** Phase 1 진입 체크 메모

---

### Day 12 (주중 저녁, 1시간) — 커뮤니티 진입 + PR 문화 관찰

**할 일:**
1. LLVM Discourse 가입 + `[mlir]` 태그 구독
2. LLVM Discord 가입 + `#mlir` 채널 입장
3. OpenXLA Discord 가입
4. GitHub Watch 설정: `llvm/llvm-project`, `openxla/stablehlo`, `iree-org/iree`

5. **관찰 과제 (읽기만):**
   - StableHLO 또는 IREE의 최근 PR 3개 열어보기
     - 어떤 파일이 변경됐는지
     - 리뷰어가 어떤 코멘트를 다는지
     - 커밋 메시지 스타일
   - MLIR upstream의 최근 PR 3개 열어보기
     - `good first issue` 태그 이슈 3개 읽기
     - NFC (Non-Functional Change) PR이 뭔지 확인

**산출물:** "오픈소스 PR 관찰 메모" (커밋 메시지 컨벤션, 리뷰 문화)

---

### Day 13~14 (주말, 3~4시간) — 종합 정리 + Phase 1 진입 준비

**Day 13 전반 (2시간) — MLIR 기초 총정리:**

1. `week01.md`, `week02.md`에서 중복 정리
2. 아래 질문에 답할 수 있는지 확인
   - operation / block / region / dialect를 자기 말로 설명 가능한가?
   - block argument와 LLVM phi의 차이를 설명 가능한가?
   - attribute와 operand/result/type의 차이를 설명 가능한가?
   - Toy Ch1에 들어가도 AST / IR / SSA 연결이 머리에 잡혀 있는가?

**Day 13 후반 (1시간) — 계획 재정리:**

- Phase 1에서 볼 강의 PDF 우선순위 재확인
- Week 3 시작 체크리스트 작성

**Day 14 (1~2시간) — 최종 정리 + 커밋:**

1. `notes/week01.md`, `notes/week02.md` 최종 정리
2. Week 3 시작 전 체크리스트 정리
3. GitHub 리포에 전체 커밋:
   ```
   compiler-study/
   ├── README.md                              ← 업데이트
   ├── notes/
   │   ├── week01.md                          ← MLIR 빌드, IR 문법, 디렉토리 구조
   │   └── week02.md                          ← C++ 패턴, TableGen, Phase 1 준비
   ├── experiments/
    │   ├── mlir-basics/
   │   │   ├── hello.mlir
   │   │   ├── tensor_ops.mlir
   │   │   ├── control_flow.mlir
   │   │   ├── memref_ops.mlir
   │   │   ├── regions.mlir
   │   │   └── blocks.mlir
    └── diagrams/
        └── ai-compiler-ecosystem.md           ← 큰 그림 메모 (선택)
   ```

4. 블로그 게시 (선택지):
   - 개인 블로그 / Velog / Medium
   - 또는 GitHub README에 직접 게시해도 됨

---

## Phase 0 완료 체크리스트

| # | 항목 | 완료? |
|---|------|-------|
| 1 | MLIR 소스 빌드 성공, `mlir-opt` 동작 확인 | ☐ |
| 2 | `compiler-study` GitHub 리포 생성 + 첫 커밋들 | ☐ |
| 3 | .mlir 예제 파일 6개+ 작성 및 `mlir-opt`으로 확인 | ☐ |
| 4 | MLIR Operation/Block/Region/Dialect 개념 자기 말로 설명 가능 | ☐ |
| 5 | LLVM C++ 패턴 3개 (isa/cast, SmallVector, Builder) 인식 가능 | ☐ |
| 6 | TableGen `.td` 파일이 뭐하는 건지 감 잡기 | ☐ |
| 7 | notes/week01.md + week02.md 정리 완료 | ☐ |
| 8 | 강의안의 IR/SSA/CFG 개념과 MLIR 예제를 연결해서 설명 가능 | ☐ |
| 9 | 커뮤니티 가입 (Discourse, Discord, GitHub Watch) | ☐ |
| 10 | 오픈소스 PR 관찰 (MLIR / StableHLO / IREE 중심) | ☐ |

---

## Phase 0에서 Phase 1로 넘어갈 때의 상태

Phase 0이 끝나면 넌 이런 상태여야 해:

- `mlir-opt`에 .mlir 파일을 넣고 결과를 읽을 수 있다
- MLIR의 기본 구조 (Operation, Block, Region, Dialect)를 설명할 수 있다
- Toy Tutorial Phase 1을 시작할 준비가 되어 있다
- 강의안의 IR/SSA/CFG 개념을 MLIR 예제와 연결할 수 있다
- LLVM C++ 코드를 봤을 때 "완전 외계어"가 아니라 "아 이건 Python의 XX랑 비슷하네" 수준
- GitHub에 공개 학습 리포가 있고, 주간 노트가 정리되어 있다
- 오픈소스 커뮤니티에 가입되어 있고, PR 문화를 관찰했다

**이 상태가 아니면 Phase 1로 넘어가지 말고 더 시간을 쓸 것.**
Phase 1의 Toy Tutorial은 이 기초 위에서 훨씬 빠르게 진행된다.
