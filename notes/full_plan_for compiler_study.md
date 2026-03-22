# Compiler Study 로드맵 — 16주 통합 계획 (v4)

> **대상**: MLIR 기반 컴파일러를 더 깊게 이해하려는 풀타임 직장인
> **장기 목표**: MLIR C++/dialect conversion 실력을 만들고, 이후 MLIR 관련 프로젝트에 기여
> **학습 전략**: 컴파일러 수업 자료 + MLIR Toy + MLIR 실습을 먼저 굳히고, 이후 실전 프로젝트로 확장
> **시간**: 주중 저녁 1~1.5시간 + 주말 3~4시간 (주 8~11시간)

---

## 학습에 활용할 실전 프로젝트 지도

로드맵 전체에서 아래 프로젝트들을 "교과서"처럼 참고한다.
다만 초반 Phase의 중심은 강의 자료 + Toy + MLIR 공식 문서이고,
실전 프로젝트는 Phase가 뒤로 갈수록 비중을 높인다.

```
                     Compiler Theory + IR Basics
                  (AST / IR / SSA / CFG / Data Flow)
                                   │
                                   ▼
                               MLIR Core
                  (Operation / Region / Dialect / Lowering)
                                   │
               ┌───────────────────┼───────────────────┐
               ▼                   ▼                   ▼
          Toy Tutorial        StableHLO / IREE      Triton / TileIR
          (학습용 구현)        (중반 production)     (후반 backend 심화)
               │                   │                   │
               ▼                   ▼                   ▼
          LLVM Lowering       Linalg / LLVM       TTIR / TTGIR / TileIR
```

| 프로젝트 | 역할 | 왜 참고하나 | 핵심 파일/경로 |
|----------|------|------------|---------------|
| **Triton 메인** | tile-based GPU 컴파일러 | TTIR→TTGIR→LLVM→PTX 전체 파이프라인. dialect conversion의 가장 큰 실전 예시 | `third_party/nvidia/backend/compiler.py`, `lib/Dialect/` |
| **Triton-to-tile-IR** | 기여 대상 | TTIR→CUDA Tile IR conversion. Triton에 새 백엔드 붙이는 패턴 | `lib/`, `third_party/tileir/` |
| **XLA / StableHLO** | ML 컴파일러 표준 | 프레임워크-독립 op set 설계, MLIR dialect 간 lowering 패턴 | `openxla/stablehlo`, `openxla/xla` |
| **cuTile Python** | Tile 프로그래밍 DSL | Python DSL→CUDA Tile IR. Legato의 Python eDSL 구조와 직접 비교 가능 | `NVIDIA/cutile-python` |
| **NVIDIA/cuda-tile** | MLIR dialect | CUDA Tile IR의 op 정의, 타입 시스템. custom dialect 만들 때 참고 | `NVIDIA/cuda-tile` |
| **TileGym** | 커널 예제 라이브러리 | 실제 LLM 커널(matmul, attention, layernorm)이 Tile IR로 어떻게 표현되는지 | `NVIDIA/TileGym` |
| **IREE** | end-to-end ML 컴파일러 | StableHLO→Linalg→LLVM 파이프라인. bufferization, tiling의 실전 | `iree-org/iree` |
| **Stephen Diehl 시리즈** | 튜토리얼 | Python+MLIR 통합, GPU 컴파일 파이프라인 end-to-end | stephendiehl.com |

---

## 출발점 정리

**이미 가지고 있는 것:**
- PyTorch torch.compile 파이프라인 깊은 이해 (Dynamo, AOTAutograd, Inductor)
- Legato 컴파일러 실무 경험 (Python eDSL + MLIR)
- lit/FileCheck 테스트 경험
- Triton 커널, vLLM 내부 구조 학습 이력
- Python 고급, C++ 입문 단계

**부족한 것:**
- MLIR C++ 레벨 코드 읽기/쓰기
- TableGen/ODS 실전 감각
- GPU 하드웨어를 "컴파일러 의사결정" 관점에서 연결하는 능력
- AI 컴파일러 생태계 전체 조감 (XLA, Triton, IREE가 어떻게 다르고 뭘 공유하는지)
- 오픈소스 기여 경험

---

## 매주 공통 루틴 (16주 내내 유지)

| 활동 | 빈도 | 시간 | 내용 |
|------|------|------|------|
| 문서 읽기 | 주 3회 | 30~60분 | MLIR 공식 문서 + 수업 자료 |
| 코드 읽기 | 주 3회 | 30분 | Toy / MLIR 예제 → 이후 StableHLO/IREE → 나중에 Triton |
| 직접 구현 | 주 3회 | 1시간+ | 작은 rewrite / pass / custom op |
| 요약 노트 | 주 1회 | 30분 | 배운 것, 헷갈린 것, 강의 내용과 MLIR 연결 포인트 |

---

## 컴파일러 수업 자료 병행 원칙

`/Users/juntaek/Documents/Cmp./Cmp` 아래 22개 강의 PDF를 Phase 1부터 병행한다.
이 자료들은 MLIR을 대체하는 트랙이 아니라, MLIR 코드를 읽을 때 필요한
컴파일러 기본기(파싱, IR, SSA, CFG, data-flow)를 채워주는 기반 트랙이다.

### 우선순위 높은 강의

| 강의 | 역할 | 언제 붙일까 |
|------|------|-------------|
| `01_Intro.pdf` | 전체 컴파일러 파이프라인 관점 | Phase 1 시작 시 |
| `09_Intermediate_Representation.pdf` | IR 설계 감각 | Toy Ch2 직전/직후 |
| `17_SSA.pdf` | SSA 핵심 개념 | Toy IR 읽기 직후 |
| `11_Control_Flow.pdf` | basic block / CFG | Rewrite, lowering 전 |
| `12_Data_Flow.pdf` | analysis 기초 | Phase 1 후반, Phase 2 준비 |
| `22_Preliminary_Transformations.pdf` | canonicalization 감각 | Ch3 rewrite 주간 |
| `02~07_*.pdf` | lexing, parsing, semantic analysis | Week 3~4에 분산 |

### Phase 1 통합 원칙

- Toy Tutorial에서 "어떻게 구현되는지"를 배운다.
- 수업 자료에서 "왜 그런 구조가 필요한지"를 보충한다.
- StableHLO / IREE / 이후 Triton에서 "실전에서 어떻게 커지는지"를 확인한다.
- 강의 PDF는 한 번에 1개를 끝내려 하지 말고, 해당 주차와 직접 연결되는 부분만 15~30분씩 발췌해서 읽는다.

즉, 한 주 안에서 항상 세 층위를 연결한다:

1. 이론: 수업 PDF
2. 학습용 구현: Toy Tutorial
3. 실전 구현: StableHLO / IREE (Triton은 후반부)

---

## Phase 0: 환경 세팅 + MLIR 기초 감각 만들기 (1~2주차)

### 목표
- MLIR 소스 빌드
- MLIR IR 문법과 `mlir-opt` 사용 감각 확보
- 컴파일러 수업 자료와 MLIR의 연결 고리 만들기
- LLVM 스타일 C++ 패턴에 눈 익히기

### 할 일

**빌드 (주말 하루):**
```bash
# MLIR
git clone https://github.com/llvm/llvm-project.git
mkdir llvm-project/build && cd llvm-project/build
cmake -G Ninja ../llvm \
  -DLLVM_ENABLE_PROJECTS=mlir \
  -DLLVM_BUILD_EXAMPLES=ON \
  -DLLVM_TARGETS_TO_BUILD="Native;NVPTX;AMDGPU" \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_ENABLE_ASSERTIONS=ON \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
  -DLLVM_ENABLE_LLD=ON -DLLVM_CCACHE_BUILD=ON
cmake --build . --target check-mlir

```

**개념 조감도 그리기:**
아래 질문에 답할 수 있을 정도로 문서와 강의안을 읽는다:
- 왜 IR이 필요한가?
- AST / SSA / CFG는 각각 어떤 문제를 푸는가?
- MLIR의 operation / block / region / dialect는 기존 컴파일러 개념과 어떻게 대응되는가?
- StableHLO, IREE, Triton 같은 프로젝트는 MLIR 위에서 무엇을 다르게 하는가?

**LLVM 스타일 C++ 레퍼런스:**

| LLVM 패턴 | Python 대응 | 설명 |
|-----------|-------------|------|
| `llvm::StringRef` | `str`의 slice view | 복사 없는 문자열 참조 |
| `llvm::ArrayRef<T>` | `list`의 read-only view | 복사 없는 배열 참조 |
| `llvm::SmallVector<T, N>` | `list` | N개까지 스택 할당 |
| `llvm::isa<T>` / `cast<T>` / `dyn_cast<T>` | `isinstance` + 캐스팅 | LLVM식 RTTI |
| `llvm::TypeSwitch` | `match-case` | 패턴 매칭 |
| CRTP | — | 부모가 자식 타입을 템플릿 파라미터로 받음 |

**커뮤니티 진입:**
- LLVM Discourse → `[mlir]` 구독
- LLVM Discord → `#mlir`
- OpenXLA Discord (StableHLO/XLA 커뮤니티)
- GitHub Watch: `llvm/llvm-project`, `openxla/stablehlo`, `iree-org/iree`

### 산출물
- 빌드 성공
- `mlir-opt` 예제 실행 메모
- "컴파일러 이론 ↔ MLIR" 연결 메모 1장

---

## Phase 1: 컴파일러 기초 + MLIR Toy Tutorial + 강의안 중심 실습 (3~6주차)

> 원칙: 수업 자료로 개념 틀을 잡고, Toy에서 구현을 배우고, 실전 프로젝트에서
> "이게 실제로 어떻게 쓰이는지" 확인한다.

### Phase 1 주차별 축

| 주차 | Toy 축 | 수업 자료 축 | 실전 축 |
|------|--------|--------------|---------|
| 3주차 | Ch1~2 AST, IR, ODS | 01, 09, 17 | StableHLO / IREE op 정의 |
| 4주차 | Ch3 Rewrite | 02~07, 22 | StableHLO canonicalization, IREE/Linalg 참고 |
| 5주차 | Ch4~5 Lowering | 11, 12 | StableHLO→Linalg, Triton은 선택 확장 |
| 6주차 | Ch6~7 LLVM lowering | 10 복습용 선택, 17 재복습 | production pipeline 비교 |

### 3주차: Op 정의 + ODS/TableGen

**Toy:** Ch1~2 — AST→MLIR, Op 정의

**수업 자료:**
- `01_Intro.pdf`: 컴파일러 전체 구조 복습
- `09_Intermediate_Representation.pdf`: "왜 IR이 필요한가" 보강
- `17_SSA.pdf`: SSA value 개념 미리 잡기

**직접 해볼 것:** `toy.neg` op 추가

**실전 프로젝트 교차 읽기:**
- `openxla/stablehlo`의 `stablehlo/dialect/StablehloOps.td`: production-level op 정의
- IREE/Linalg 관련 op 정의: structured op가 실제 프로젝트에서 어떻게 쓰이는지
- `NVIDIA/cuda-tile`의 `.td` 파일은 선택 참고 자료로만 사용

**비교 포인트:** 세 프로젝트의 op 정의 스타일 차이 (얼마나 많은 정보를 `.td`에 넣는지, verifier 복잡도 등)

### 4주차: 패턴 리라이팅 + Canonicalization

**Toy:** Ch3 + Quickstart Rewrites 문서

**수업 자료:**
- `02_Lexical_Analysis.pdf` ~ `07_Semantic_Analysis_II.pdf`: front-end 감각 보강
- `22_Preliminary_Transformations.pdf`: canonicalization/정규화 감각 보강

**직접 구현:** `add(x,0)→x`, `mul(x,1)→x`, `reshape(reshape(x))→reshape(x)` + 자기만의 fold 1개

**실전 프로젝트 교차 읽기:**
- StableHLO의 canonicalization 패턴들: `stablehlo/transforms/`
- IREE/Linalg 쪽 canonicalization / transform 예시
- Triton pass는 이 주차의 필수가 아니라 Week 5 이후 선택 참고

**비교 포인트:** fold vs pattern vs dialect conversion — 세 메커니즘이 각 프로젝트에서 어떻게 쓰이는지

**산출물:** rewrite 2~3개 + lit/FileCheck 테스트 + "세 프로젝트의 rewrite 비교" 메모

### 5주차: Dialect Conversion / Lowering

**Toy:** Ch4~5 + Dialect Conversion 공식 문서

**수업 자료:**
- `11_Control_Flow.pdf`: basic block, CFG
- `12_Data_Flow.pdf`: 변환 이후 analysis가 왜 필요한지 감각 잡기

**실전 프로젝트 교차 읽기 (핵심 주차!):**
- **StableHLO→Linalg lowering** (`stablehlo/transforms/StablehloLegalizeToLinalgPass.cpp`): 이번 주 핵심
- IREE의 lowering / dispatch 형성 흐름: production lowering 감각 익히기
- `TritonToCudaTile.cpp`와 `ConvertTritonToTritonGPU`는 Week 5 후반의 선택 확장으로 밀기

**비교 포인트:** 같은 "dialect conversion" 메커니즘이지만, 대상 dialect과 변환 복잡도가 어떻게 다른지

**산출물:** before/after IR 예제 + "세 프로젝트의 dialect conversion 비교" 메모

### 6주차: 전체 파이프라인 조감 + 복습

**Toy:** Ch6~7 완주, 전체 설명 자가 테스트

**수업 자료:**
- `17_SSA.pdf` 재복습: lowering 이후에도 SSA가 유지되는 방식 확인
- `10_Instruction_Selection.pdf`는 선택적으로 읽되, LLVM lowering 이후의 "다음 단계"를 보는 용도에 그친다

**컴파일 파이프라인 비교 정리:**

```
[Triton 기존 경로]
Python DSL → TTIR → TTGIR → LLVM IR → PTX → CUBIN
                     ↑ layout 정보 추가 (make_ttgir)

[Triton-to-tile-IR 경로]  
Python DSL → TTIR → CUDA Tile IR → tileiras → GPU binary
                     ↑ TritonToCudaTile conversion

[XLA/StableHLO 경로]
JAX/TF/PyTorch → StableHLO → HLO → XLA 최적화 → LLVM IR → PTX
                                                    ↑ 또는 Triton MLIR

[cuTile 경로]
Python DSL → CUDA Tile IR → tileiras → GPU binary
             ↑ cuTile 자체가 Tile IR을 직접 생성

[IREE 경로]
StableHLO/TOSA → Linalg → Vector → LLVM → 다양한 타겟
```

**핵심 관찰:** Toy에서 배운 lowering / dialect conversion / LLVM lowering 패턴은 StableHLO, IREE, Triton 같은 production compiler에서도 반복된다.

**Triton 파이프라인 디버깅 실습:**
```bash
# Triton의 각 단계 IR 덤프해보기
TRITON_KERNEL_DUMP=1 TRITON_DUMP_DIR=./dump python your_triton_script.py
# dump/ 디렉토리에 .ttir, .ttgir, .llir, .ptx 파일 생성됨
```

**산출물:** Toy 파이프라인 다이어그램 + 5개 프로젝트 파이프라인 비교표

---

## Phase 2: Custom Dialect + Bufferization + production MLIR 읽기 (7~9주차)

### 7주차: Custom Dialect 만들기

**할 일:** ODS/TableGen으로 미니 dialect 제작

**예시 op:** `chip.matmul`, `chip.elementwise`, `chip.layout_convert`

**실전 프로젝트 참고:**
- `NVIDIA/cuda-tile`: CUDA Tile dialect의 실제 op 정의 구조
- StableHLO의 op 정의: verifier, type inference, attribute 설계가 체계적
- Triton의 `tt.dot` op: matmul이 AI 컴파일러에서 어떻게 표현되는지

**산출물:** custom op 2~3개 + verifier + 테스트

### 8주차: Lowering Pass + 실전 분석

**할 일:** custom op → linalg/arith/tensor lowering pass 1개

**실전 프로젝트 본격 분석:**
- `TritonToCudaTile.cpp` 체계적 분석:
  1. 전체 구조 (ConversionTarget, TypeConverter, 패턴 적용 순서)
  2. 개별 패턴 5개 이상 상세 분석
  3. 미지원 op 리스트와 대조 → 기여 후보 발굴

- Triton 메인의 `ConvertTritonGPUToLLVM` 비교:
  - TritonToCudaTile과 어떤 구조적 유사성/차이가 있는지

- StableHLO→Linalg lowering 비교:
  - 같은 op (예: dot_general → linalg.matmul)이 어떻게 변환되는지

**산출물:** lowering pass 1개 + "TritonToCudaTile 분석 노트" + "미지원 op 난이도 분류"

### 9주차: Bufferization + 메모리 모델 비교

**할 일:** Bufferization 공식 문서 읽기

**프로젝트별 메모리 모델 비교:**

| | Triton | CUDA Tile IR | StableHLO/XLA | IREE |
|---|--------|-------------|---------------|------|
| 기본 추상화 | tensor (tile) | tensor (tile) | tensor | tensor |
| 메모리 관리 | 컴파일러가 shared mem 자동 할당 | tileiras가 자동 관리 | XLA가 buffer 할당 | bufferization pass |
| 특이사항 | TTGIR에서 layout encoding 추가 | unordered memory model | 정적 shape 선호 | 명시적 bufferization 단계 |

**CUDA Tile IR의 unordered memory model 이해:**
- 기본적으로 global memory 접근 순서를 보장하지 않음
- memory aliasing / tile block 간 데이터 교환 시 문제 발생 가능
- memory token semantics로 명시적 순서 제어 (향후 Triton API 확장 예정)

**산출물:** "프로젝트별 메모리 모델 비교표" + "unordered memory model" 메모

---

## Phase 3: 하드웨어 + AI 컴파일러 최적화 (10~12주차)

### 10주차: CPU 하드웨어 — 컴파일러 관점

**키워드:** cache hierarchy, locality, SIMD, instruction throughput/latency, branch prediction

**컴파일러 질문:** loop interchange가 cache에 왜 중요한가? vectorization은 언제 유리한가?

**실습:** row-major vs column-major 순회, 작은 matmul loop order 변경

**IREE 연결:** IREE의 CPU 백엔드가 Linalg op을 tiling→vectorization→LLVM으로 내리는 흐름 참고

**산출물:** cache/locality 요약 + loop order 실험 결과

### 11주차: GPU 하드웨어 + SIMT vs Tile 모델

**SIMT 모델 (기존):**
- Grid/Block/Thread/Warp, Global/Shared/Register memory
- Occupancy, Coalescing, Register pressure

**Tile 모델 (새로운 패러다임):**
- 개발자가 data block(tile) 단위로 생각 → 컴파일러가 thread 매핑 자동 처리
- Tensor Core를 자연스럽게 활용
- PTX가 SIMT의 virtual ISA라면, Tile IR은 Tile 모델의 virtual ISA

**Triton-to-tile-IR 성능 힌트 이해:**
- `occupancy` (1~32): SM당 동시 실행 block 수. 컴퓨팅 집약 커널에서 튜닝 필수
- `num_ctas`: Blackwell 2CTA mode. `num_ctas=2`가 dense dot에서 필수
- `num_stages`: TileIR에서는 strict directive가 아닌 cost hint
- TMA API: `tl.load`보다 20%+ 빠름 (CUDA 13.1 tileiras 알려진 이슈)

**cuTile 코드 읽기:**
```python
# cuTile의 vector_add — Triton과 비교하며 읽기
@ct.kernel
def vector_add_kernel(a, b, result):
    block_id = ct.bid(0)
    a_tile = ct.load(a, index=(block_id,), shape=(TILE_SIZE,))
    b_tile = ct.load(b, index=(block_id,), shape=(TILE_SIZE,))
    ct.store(result, index=(block_id,), tile=a_tile + b_tile)
```
Triton의 같은 커널과 비교: 추상화 수준, tile 표현, 메모리 접근 패턴의 차이

**TileGym 읽기:**
- `src/tilegym/ops/`에서 matmul, attention 커널이 실제로 어떻게 작성되는지
- Llama 3.1 inference에 Tile 커널이 어떻게 통합되는지

**산출물:** "SIMT vs Tile 모델 비교" + "cuTile vs Triton 코드 비교" + 성능 힌트 메모

### 12주차: AI 컴파일러 최적화 패턴 종합

**Linalg 중심 학습:**
- Structured op, tiling, fusion, vectorization, bufferization 흐름
- Linalg가 XLA/IREE/Triton 에서 각각 어떤 역할을 하는지

**프로젝트별 matmul 최적화 비교:**

| 단계 | Triton PTX | Triton→TileIR | XLA GPU | IREE |
|------|-----------|--------------|---------|------|
| 표현 | `tt.dot` | `tt.dot` | `dot_general` | `linalg.matmul` |
| Tiling | TTGIR layout | tileiras 자동 | XLA tile assignment | Linalg tiling pass |
| 메모리 | shared mem (명시적) | tileiras 자동 | XLA buffer alloc | bufferization pass |
| 코드생성 | PTX inline asm | Tile IR bytecode | LLVM/PTX | LLVM |

**추가 학습 — 컴파일러 최적화 이론:**
- CSE, DCE → `mlir/lib/Transforms/CSE.cpp` 읽기
- Triton의 `TritonCombineOps`, `Canonicalize` pass가 실제로 뭘 하는지

**산출물:** "matmul lowering 4개 경로 비교" + tiling 의미 비교표

---

## Phase 4: Production MLIR 컴파일러 비교 + Triton 심화 (13~14주차)

### 13주차: Triton 컴파일러 내부 + Stephen Diehl

**Triton 메인 `compiler.py` 상세 분석:**
- `make_ttir()`: hardware-agnostic 최적화 (CSE, DCE, Canonicalize, LICM)
- `make_ttgir()`: layout encoding 추가, GPU-specific 최적화 (가장 복잡)
- `make_llir()`: LLVM IR 변환
- `make_ptx()`, `make_cubin()`: 최종 코드 생성

**TileIR 백엔드 `compiler.py`와 비교:**
- TTGIR 단계를 건너뛰고 TTIR→CUDA Tile IR 직행
- `ENABLE_TILE=1` 분기 로직
- PTX fallback 메커니즘

**cuTile Python의 컴파일 과정과 비교:**
- cuTile은 Triton과 달리 CUDA Tile IR을 직접 생성 (중간 IR 없음)
- cuTile의 `@ct.kernel` 데코레이터가 Python AST를 어떻게 처리하는지
- Legato의 Python eDSL→MLIR 과정과 구조적 유사성/차이

**Stephen Diehl MLIR 시리즈 (주말):**
- Part 0~1: 설치 + 기본 (빠르게)
- Part 4: linalg으로 선형대수
- Part 8: MLIR→PTX→GPU 실행 (Triton TileIR 경로와 비교 가능)

### 14주차: 기여 포인트 발굴

**Triton-to-tile-IR을 "기여자 시선"으로 종합 분석:**

1. **Python 레이어:** `core.py`, `semantic.py`, `tensor_descriptor.py`의 TMA API 변환
2. **C++ 레이어:** 미지원 op 난이도 최종 분류
3. **테스트 구조:** `test/` 디렉토리 커버리지 갭

**다른 프로젝트의 기여 가이드 비교:**
- Triton 메인: 활발한 PR 리뷰, 3rd Triton Developer Conference 자료 참고
- StableHLO: RFC 기반 의사결정, 체계적 spec 관리
- MLIR upstream: `good first issue`, NFC 패치 문화

**산출물:** "기여 후보 리스트" — Triton-to-tile-IR 3개 + (선택) MLIR upstream 2개

---

## Phase 5: 첫 기여 실행 (15~16주차)

### 15주차: 첫 기여 준비

**Triton-to-tile-IR 기여 우선순위:**
1. 테스트 추가 (기존 op의 edge case)
2. 문서/빌드 가이드 개선
3. 단순 미지원 op의 conversion 패턴 추가
4. Python 레이어 에러 핸들링 개선

**(선택) 다른 프로젝트 기여:**
- MLIR upstream: `good first issue` 태그
- StableHLO: 문서/테스트 개선
- Triton 메인: 작은 canonicalization 패턴

### 16주차: 첫 PR + 기술 글

**PR 제출**

**기술 글 주제 (하나 선택):**
- "Triton PTX vs TileIR 백엔드: 파이프라인 비교 분석"
- "AI 컴파일러 5개 프로젝트의 dialect conversion 비교"
- "SIMT에서 Tile로: GPU 컴파일러의 패러다임 전환"
- "StableHLO vs Triton IR: ML 컴파일러의 두 가지 접근"

**산출물:** PR 1개 + 기술 글 1개

---

## 16주 이후

### 단기
- Triton-to-tile-IR 미지원 op 구현 (중간 난이도)
- PTX vs TileIR 벤치마크 기여
- MLIR upstream 작은 패치

### 중기
- CUDA Tile IR memory token semantics 관련 작업
- cuTile 또는 TileGym 기여 (Python 강점 활용)
- Triton 메인 리포 기여 (layout optimization 등)

### 장기
- Triton-to-tile-IR → Triton 메인 통합 참여
- 자체 out-of-tree dialect 공개 프로젝트
- AI compiler 관련 발표/블로그 시리즈

---

## 추가 공부 영역 (병행)

**그래프 알고리즘:**
위상 정렬(스케줄링), 지배자 트리(SSA), 그래프 파티셔닝(AOTAutograd min-cut), 그래프 컬러링(레지스터 할당)

**컴파일러 최적화 이론:**
CSE, DCE, Loop tiling/fusion/interchange, Polyhedral model (Affine dialect 배경)

**디버깅 기법:**
- Triton: `TRITON_KERNEL_DUMP=1`, `MLIR_ENABLE_DUMP=1`, `MLIR_ENABLE_TIMING`
- MLIR: `--mlir-print-ir-after-all`, `-debug-only=dialect-conversion`
- Lei Mao 블로그의 Triton compiler development tips

---

## 핵심 리소스 정리

### 기여 대상
| 리소스 | URL |
|--------|-----|
| Triton-to-tile-IR | github.com/triton-lang/Triton-to-tile-IR |

### 참고 프로젝트
| 리소스 | URL |
|--------|-----|
| Triton 메인 | github.com/triton-lang/triton |
| NVIDIA/cuda-tile (MLIR dialect) | github.com/NVIDIA/cuda-tile |
| NVIDIA/cutile-python (Python DSL) | github.com/NVIDIA/cutile-python |
| NVIDIA/TileGym (커널 예제) | github.com/NVIDIA/TileGym |
| OpenXLA/StableHLO | github.com/openxla/stablehlo |
| OpenXLA/XLA | github.com/openxla/xla |
| IREE | github.com/iree-org/iree |

### 학습 자료
| 리소스 | URL |
|--------|-----|
| MLIR Toy Tutorial | mlir.llvm.org/docs/Tutorials/Toy/ |
| MLIR Getting Started | mlir.llvm.org/getting_started/ |
| Stephen Diehl MLIR 시리즈 | stephendiehl.com/posts/mlir_introduction/ |
| Triton Kernel Compilation (PyTorch 블로그) | pytorch.org/blog/triton-kernel-compilation-stages/ |
| Deep Dive Triton Internals (Kapil Sharma) | kapilsharma.dev/posts/deep-dive-into-triton-internals-3/ |
| Triton Compiler Dev Tips (Lei Mao) | lei.chat/posts/triton-compiler-development-tips/ |
| AMD Triton Compilation Deep Dive | medium.com/@nzhangnju |
| Triton DeepWiki | deepwiki.com/triton-lang/triton |
| cuTile 공식 문서 | docs.nvidia.com/cuda/cutile-python/ |
| CUDA Tile IR 블로그 | developer.nvidia.com/blog/advancing-gpu-programming-with-the-cuda-tile-ir-backend-for-openai-triton |
| jerinphilip/toy-mlir (챕터별 diff) | github.com/jerinphilip/toy-mlir |

### 커뮤니티
| 채널 | 용도 |
|------|------|
| LLVM Discourse | MLIR RFC, 디자인 논의 |
| LLVM Discord `#mlir` | 실시간 Q&A |
| GPU MODE Discord | Triton 커뮤니티 핵심 |
| OpenXLA Discord | StableHLO/XLA 논의 |

---

## Phase별 참고 프로젝트 매핑

| Phase | 주차 | 배우는 것 | Triton-to-tile-IR | 참고 프로젝트 |
|-------|------|----------|-------------------|-------------|
| 0 | 1~2 | 빌드, LangRef, .mlir 읽기 | 아직 안 봄 | LLVM / MLIR 공식 문서 |
| 1 | 3 | Op 정의, ODS | 선택 참고 | StableHLO `.td`, IREE/Linalg |
| 1 | 4 | Rewrite | 선택 참고 | StableHLO canonicalization, IREE transforms |
| 1 | 5 | Dialect conversion | 후반 확장 | StableHLO→Linalg |
| 1 | 6 | 전체 파이프라인 | 후반 비교 | Toy / StableHLO / IREE / Triton 비교 |
| 2 | 7 | Custom dialect | `NVIDIA/cuda-tile` 선택 | StableHLO op 설계 |
| 2 | 8 | Lowering pass | 체계적 분석 시작 | StableHLO→Linalg, Triton TTGIR→LLVM |
| 2 | 9 | Bufferization | unordered memory model 참고 | IREE bufferization, XLA buffer alloc |
| 3 | 10 | CPU 하드웨어 | — | IREE CPU backend |
| 3 | 11 | GPU + Tile 모델 | 성능 힌트 이해 | cuTile 코드, TileGym 커널 |
| 3 | 12 | 최적화 종합 | matmul lowering 비교 | 4개 프로젝트 matmul 경로 |
| 4 | 13 | Triton 내부 | compiler.py 비교 | cuTile 컴파일, Stephen Diehl |
| 4 | 14 | 기여 발굴 | 미지원 op 분류 | 다른 프로젝트 기여 가이드 |
| 5 | 15~16 | 첫 기여 | PR 제출 | — |

---

## 최종 목표: 16주 후 이것들이 있으면 성공

1. **MLIR 관련 프로젝트 PR 1개** — 테스트, 문서, 또는 간단한 conversion 패턴
2. **기술 글 1개** — 여러 프로젝트를 비교하는 관점의 글
3. **기여 후보 리스트** — 난이도별 다음 PR 후보 3~5개
4. **"AI 컴파일러 생태계 조감도"** — 자기 말로 정리한 비교 분석

이 4개가 있으면 "MLIR 공부 중인 사람"이 아니라
**"컴파일러 이론과 MLIR 실습을 바탕으로 production compiler를 읽고 기여 준비가 된 사람"**으로 보인다.
