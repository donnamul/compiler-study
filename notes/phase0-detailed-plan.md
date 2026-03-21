# Phase 0: 환경 세팅 + AI 컴파일러 생태계 조감 — 상세 계획

> **기간**: 2주 (1~2주차)
> **시간**: 주중 저녁 1~1.5시간 + 주말 3~4시간
> **핵심 산출물**: MLIR 빌드 완료, GitHub 학습 리포, 블로그 글 1편, 생태계 조감도

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
   - 학습 목표 (MLIR C++ 레벨 이해 → Triton-to-tile-IR 기여)
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

3. **torch.compile 연결 포인트 정리:**
   네가 이미 잘 아는 torch.compile 파이프라인을 MLIR 개념으로 다시 매핑:

   ```
   [torch.compile 파이프라인]              [MLIR 대응 개념]
   ──────────────────────────              ───────────────────
   Python 코드                            Source language
   TorchDynamo (FX Graph 추출)            Frontend (AST → IR)
   FX Graph                               High-level dialect (like Toy)
   AOTAutograd (forward/backward 분리)     Graph transformation pass
   Inductor IR (inner_fn, loop 구조)       Mid-level dialect (like Linalg)
   Triton 커널 / C++ 코드                  Low-level dialect → codegen
   ```

**산출물:** .mlir 예제 4개 + "torch.compile ↔ MLIR 개념 매핑" 메모

---

### Day 5 (주중 저녁, 1시간) — Triton-to-tile-IR 클론 + 탐험

**할 일:**
1. Triton-to-tile-IR 클론 + 빌드 시도
   ```bash
   git clone https://github.com/triton-lang/Triton-to-tile-IR.git
   cd Triton-to-tile-IR
   pip install -e .  # GPU 없어도 빌드 자체는 될 수 있음
   ```

2. 디렉토리 구조 탐험 (빌드 실패해도 코드는 읽을 수 있음)
   ```
   Triton-to-tile-IR/
   ├── lib/                          ← C++ 핵심 코드
   │   ├── Dialect/                  ← dialect 정의
   │   └── Conversion/              ← ★ TritonToCudaTile 여기!
   ├── include/                      ← 헤더 파일
   ├── python/                       ← Python frontend
   │   └── triton/                   ← compiler.py, driver.py 등
   ├── third_party/
   │   ├── nvidia/                   ← 기존 PTX 백엔드
   │   └── tileir/                   ← ★ TileIR 백엔드
   │       ├── backend/             
   │       │   ├── compiler.py       ← ★ TileIR 컴파일 파이프라인
   │       │   └── driver.py
   │       └── PerformanceTuningTips.md
   └── test/                         ← 테스트 파일
   ```

3. 핵심 파일 3개만 열어서 구조 확인 (내용 이해 X, 구조만):
   - `third_party/tileir/backend/compiler.py`: Python에서 컴파일 단계가 어떻게 정의되는지
   - `lib/` 아래에서 `TritonToCudaTile` 관련 파일 찾기
   - `third_party/nvidia/backend/compiler.py`: 기존 PTX 백엔드와 구조 비교

**산출물:** "Triton-to-tile-IR 디렉토리 구조 메모" (notes/week01.md에 추가)

---

### Day 6~7 (주말, 3~4시간) — 생태계 조감도 + torch.compile 심화

**Day 6 전반 (2시간) — 참고 프로젝트 README 읽기:**

각 프로젝트의 README를 읽고 아래 질문에 답:

| 프로젝트 | 읽을 것 | 답할 질문 |
|----------|---------|----------|
| Triton 메인 | README.md | Triton의 컴파일 단계는 몇 개? 각 단계에서 뭘 하는가? |
| cuTile Python | README.md + 공식 문서 intro | cuTile은 Triton과 어떤 레벨에서 다른가? |
| StableHLO | README.md | StableHLO의 목표는 뭔가? 어떤 프레임워크/컴파일러와 연결되나? |
| NVIDIA/cuda-tile | README.md | CUDA Tile IR dialect은 뭘 정의하나? |
| TileGym | README.md | 어떤 커널 예제가 있나? (matmul, attention 등) |

**Day 6 후반 (1시간) — torch.compile과 이 생태계의 연결:**

Legato/torch.compile 경험을 기반으로 "왜 이 생태계가 이렇게 생겼는지" 정리:

```
torch.compile의 세계:
  Python → Dynamo (FX Graph) → AOTAutograd → Backend

Backend 선택지:
  1. TorchInductor → Triton 커널 (기존)
  2. TorchInductor → Triton → CUDA Tile IR (Triton-to-tile-IR)
  3. XLA backend → StableHLO → XLA 최적화 (PyTorch/XLA)
  4. Legato backend → Legato IR → HyperAccel 하드웨어 (네가 만드는 것)
  5. (미래) TorchInductor → cuTile → CUDA Tile IR

핵심 통찰: torch.compile의 backend은 "교체 가능한 모듈"이고,
각 backend은 결국 MLIR dialect conversion의 다른 인스턴스다.
Triton-to-tile-IR은 이 "교체"의 구체적인 예시.
```

**Day 7 (1~2시간) — Triton IR 덤프 실험 + 블로그 초안:**

1. Triton IR 덤프 실험 (GPU 있으면):
   ```python
   # experiments/triton-ir-dumps/vector_add.py
   import triton
   import triton.language as tl
   import torch
   
   @triton.jit
   def add_kernel(x_ptr, y_ptr, out_ptr, n, BLOCK: tl.constexpr):
       pid = tl.program_id(0)
       offs = pid * BLOCK + tl.arange(0, BLOCK)
       mask = offs < n
       x = tl.load(x_ptr + offs, mask=mask)
       y = tl.load(y_ptr + offs, mask=mask)
       tl.store(out_ptr + offs, x + y, mask=mask)
   
   x = torch.randn(1024, device='cuda')
   y = torch.randn(1024, device='cuda')
   out = torch.empty_like(x)
   k = add_kernel[(1,)](x, y, out, 1024, BLOCK=1024)
   
   # IR 덤프
   print("=== TTIR ===")
   print(k.asm['ttir'])
   print("=== TTGIR ===")
   print(k.asm['ttgir'])
   ```
   GPU 없으면: PyTorch 블로그의 "Triton Kernel Compilation Stages" 글에서 예시 IR 복사해서 읽기 연습

2. **torch.compile backend에서 Triton이 어떻게 호출되는지 복습:**
   ```python
   # 네가 이미 아는 코드지만, MLIR 관점에서 다시 보기
   @torch.compile
   def f(x):
       return x * 2 + 1
   
   # 내부적으로:
   # 1. Dynamo가 FX Graph 추출
   # 2. AOTAutograd가 forward/backward 분리
   # 3. Inductor가 Triton 커널 생성
   # 4. Triton이 TTIR → TTGIR → LLVM → PTX 컴파일
   #
   # Triton-to-tile-IR가 바꾸는 부분:
   # 4. Triton이 TTIR → CUDA Tile IR → tileiras → GPU binary
   ```

3. **블로그 초안 시작** (`blog-drafts/01-ai-compiler-landscape.md`):

   제목: "AI 컴파일러 생태계를 torch.compile 개발자 시선으로 정리하기"

   ```markdown
   # AI 컴파일러 생태계를 torch.compile 개발자 시선으로 정리하기
   
   ## 동기
   torch.compile backend를 만들면서 자연스럽게 AI 컴파일러 세계에 들어왔다.
   Backend 하나를 만드는 건 할 수 있는데, 전체 생태계가 어떻게 연결되는지는 
   의외로 정리된 자료가 없어서 직접 정리해본다.
   
   ## torch.compile의 구조 복습
   (Dynamo → AOTAutograd → Backend 간단 설명)
   
   ## Backend의 선택지들
   - TorchInductor + Triton (기본)
   - XLA + StableHLO (Google/TPU)
   - Triton + CUDA Tile IR (NVIDIA 신규)
   - Custom backend (Legato 같은)
   
   ## 각 경로에서 MLIR이 어떻게 쓰이는지
   (파이프라인 다이어그램)
   
   ## 왜 "dialect conversion"이 핵심인지
   
   ## 마무리: 이걸 알면 뭐가 좋은가
   ```

**산출물:**
- 생태계 조감도 다이어그램 (diagrams/ 에 커밋)
- 블로그 초안 v0.1 (blog-drafts/ 에 커밋)
- notes/week01.md 정리 완료

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

### Day 11 (주중 저녁, 1시간) — Triton 컴파일 파이프라인 조감

**할 일:**
1. Triton 메인 리포의 `third_party/nvidia/backend/compiler.py` 읽기
   
   이 파일에서 찾을 것:
   - `make_ttir()`: 어떤 pass들이 적용되는지 (CSE, DCE, Canonicalize...)
   - `make_ttgir()`: layout encoding이 어떻게 추가되는지
   - `make_llir()`: LLVM IR로 어떻게 변환되는지
   - `make_ptx()`, `make_cubin()`: 최종 코드 생성

2. Triton-to-tile-IR의 `third_party/tileir/backend/compiler.py`와 비교:
   - 어떤 단계가 같고 어떤 단계가 다른지
   - `ENABLE_TILE=1`일 때 어떤 분기가 활성화되는지

3. **torch.compile에서 Triton이 호출되는 지점 복습:**
   네가 이미 공부한 TorchInductor의 Triton codegen이 정확히 어디서
   `make_ttir()` → `make_ttgir()` → ... 체인을 시작하는지 정리

**산출물:** "Triton PTX 파이프라인 vs TileIR 파이프라인" 비교 메모

---

### Day 12 (주중 저녁, 1시간) — 커뮤니티 진입 + PR 문화 관찰

**할 일:**
1. LLVM Discourse 가입 + `[mlir]` 태그 구독
2. LLVM Discord 가입 + `#mlir` 채널 입장
3. GPU MODE Discord 가입
4. GitHub Watch 설정: `triton-lang/Triton-to-tile-IR`, `triton-lang/triton`

5. **관찰 과제 (읽기만):**
   - Triton-to-tile-IR의 최근 PR 3개 열어보기
     - 어떤 파일이 변경됐는지
     - 리뷰어가 어떤 코멘트를 다는지
     - 커밋 메시지 스타일
   - MLIR upstream의 최근 PR 3개 열어보기
     - `good first issue` 태그 이슈 3개 읽기
     - NFC (Non-Functional Change) PR이 뭔지 확인

**산출물:** "오픈소스 PR 관찰 메모" (커밋 메시지 컨벤션, 리뷰 문화)

---

### Day 13~14 (주말, 3~4시간) — 종합 정리 + 블로그 완성 + torch.compile 연결 심화

**Day 13 전반 (2시간) — torch.compile 관련 심화 정리:**

1. **Legato backend의 위치를 생태계에서 매핑:**
   ```
   [일반적인 torch.compile backend 구조]
   
   class MyBackend:
       def compile(self, gm: GraphModule, inputs):
           # 1. FX Graph 받기
           # 2. 내 IR로 변환 (= MLIR의 "dialect conversion")
           # 3. 최적화 pass 적용 (= MLIR의 "transformation passes")
           # 4. 하드웨어 코드 생성 (= MLIR의 "lowering to target")
           return compiled_fn
   
   [Legato가 하는 것]
   FX Graph → Legato IR (Python eDSL + MLIR) → HyperAccel binary
   
   [Triton-to-tile-IR가 하는 것]
   TTIR → CUDA Tile IR → tileiras → GPU binary
   
   [StableHLO/XLA가 하는 것]
   StableHLO → HLO → XLA optimized HLO → LLVM/PTX
   
   공통점: 전부 "higher-level IR → lower-level IR" 변환의 반복
   ```

2. **torch.compile의 "guard + recompile" 메커니즘을 MLIR 관점에서 재해석:**
   - Dynamo의 guard = MLIR의 "pre-condition for a compiled artifact"
   - Graph break = MLIR의 "partial compilation boundary"
   - AOTAutograd의 min-cut = 그래프 파티셔닝 (MLIR에서도 동일 문제 발생)

3. **실험: torch.compile의 FX Graph와 Triton TTIR 비교**
   ```python
   # experiments/torch-compile-to-triton/
   
   import torch
   from torch._dynamo import optimize
   
   def f(x, y):
       return x @ y + x
   
   # FX Graph 확인
   from torch.fx import symbolic_trace
   traced = symbolic_trace(f)
   print(traced.graph)
   
   # 이 FX Graph가 Inductor를 거쳐 Triton 커널이 되면
   # TTIR에서는 tt.dot + arith.addf 같은 형태가 됨
   ```

**Day 13 후반 (1시간) — 블로그 글 완성:**

블로그 초안을 다듬어서 게시 가능한 수준으로:

```markdown
# AI 컴파일러 생태계를 torch.compile 개발자 시선으로 정리하기

## 1. 왜 이 글을 쓰는가
- torch.compile backend 개발자로서 MLIR 세계에 입문
- 프로젝트가 너무 많아서 정리가 필요했음

## 2. torch.compile 복습 (짧게)
- Dynamo → AOTAutograd → Backend
- Backend는 교체 가능한 모듈

## 3. Backend별 컴파일 경로 비교
- TorchInductor + Triton (기본 경로)
- XLA + StableHLO (Google/TPU 경로)
- Triton + CUDA Tile IR (NVIDIA 새 경로)
- Custom backend (Legato 등)
(파이프라인 다이어그램 포함)

## 4. 공통 패턴: "dialect conversion"
- 모든 경로가 결국 "높은 수준 IR → 낮은 수준 IR" 변환의 반복
- MLIR이 이 패턴을 infrastructure로 제공

## 5. Triton-to-tile-IR: 구체적인 예시
- 기존 Triton PTX 경로 vs TileIR 경로
- 뭐가 바뀌고 뭐가 같은지

## 6. 마무리
- 이 조감도를 그리고 나니 MLIR 학습 방향이 명확해졌음
- 다음 글: MLIR Toy Tutorial 시작기
```

**Day 14 (1~2시간) — 최종 정리 + 커밋:**

1. `notes/week01.md`, `notes/week02.md` 최종 정리
2. 블로그 글 최종 검수 (오타, 다이어그램 확인)
3. GitHub 리포에 전체 커밋:
   ```
   compiler-study/
   ├── README.md                              ← 업데이트
   ├── notes/
   │   ├── week01.md                          ← MLIR 빌드, IR 문법, 디렉토리 구조
   │   └── week02.md                          ← C++ 패턴, TableGen, Triton 파이프라인
   ├── blog-drafts/
   │   └── 01-ai-compiler-landscape.md        ← 블로그 글 완성본
   ├── experiments/
   │   ├── mlir-basics/
   │   │   ├── hello.mlir
   │   │   ├── tensor_ops.mlir
   │   │   ├── control_flow.mlir
   │   │   ├── memref_ops.mlir
   │   │   ├── regions.mlir
   │   │   └── blocks.mlir
   │   ├── triton-ir-dumps/
   │   │   └── vector_add.py                  ← (GPU 있으면 IR 덤프 포함)
   │   └── torch-compile-to-triton/
   │       └── fx_to_triton.py
   └── diagrams/
       ├── ai-compiler-ecosystem.md           ← 생태계 조감도 (Mermaid 또는 ASCII)
       ├── torch-compile-to-mlir-mapping.md   ← torch.compile ↔ MLIR 매핑
       └── triton-ptx-vs-tileir.md            ← 두 파이프라인 비교
   ```

4. 블로그 게시 (선택지):
   - 개인 블로그 / Velog / Medium
   - 또는 GitHub README에 직접 게시해도 됨

---

## Phase 0 완료 체크리스트

| # | 항목 | 완료? |
|---|------|-------|
| 1 | MLIR 소스 빌드 성공, `mlir-opt` 동작 확인 | ☐ |
| 2 | Triton-to-tile-IR 클론 + 디렉토리 구조 파악 | ☐ |
| 3 | `compiler-study` GitHub 리포 생성 + 첫 커밋들 | ☐ |
| 4 | .mlir 예제 파일 6개+ 작성 및 `mlir-opt`으로 확인 | ☐ |
| 5 | MLIR Operation/Block/Region/Dialect 개념 자기 말로 설명 가능 | ☐ |
| 6 | LLVM C++ 패턴 3개 (isa/cast, SmallVector, Builder) 인식 가능 | ☐ |
| 7 | TableGen `.td` 파일이 뭐하는 건지 감 잡기 | ☐ |
| 8 | Triton PTX 파이프라인 vs TileIR 파이프라인 비교 정리 | ☐ |
| 9 | torch.compile ↔ MLIR 개념 매핑 정리 | ☐ |
| 10 | AI 컴파일러 생태계 조감도 다이어그램 | ☐ |
| 11 | 커뮤니티 가입 (Discourse, Discord, GitHub Watch) | ☐ |
| 12 | 오픈소스 PR 관찰 (Triton-to-tile-IR 3개, MLIR 3개) | ☐ |
| 13 | 블로그 글 1편 완성 | ☐ |
| 14 | notes/week01.md + week02.md 정리 완료 | ☐ |

---

## Phase 0에서 Phase 1로 넘어갈 때의 상태

Phase 0이 끝나면 넌 이런 상태여야 해:

- `mlir-opt`에 .mlir 파일을 넣고 결과를 읽을 수 있다
- MLIR의 기본 구조 (Operation, Block, Region, Dialect)를 설명할 수 있다
- Triton-to-tile-IR의 디렉토리 구조를 알고, 핵심 파일이 어디 있는지 안다
- 5개 프로젝트의 위치와 역할을 설명할 수 있다
- LLVM C++ 코드를 봤을 때 "완전 외계어"가 아니라 "아 이건 Python의 XX랑 비슷하네" 수준
- torch.compile 파이프라인과 MLIR 개념의 대응 관계를 설명할 수 있다
- GitHub에 공개 학습 리포가 있고, 블로그 글 1편이 게시되어 있다
- 오픈소스 커뮤니티에 가입되어 있고, PR 문화를 관찰했다

**이 상태가 아니면 Phase 1로 넘어가지 말고 더 시간을 쓸 것.**
Phase 1의 Toy Tutorial은 이 기초 위에서 훨씬 빠르게 진행된다.
