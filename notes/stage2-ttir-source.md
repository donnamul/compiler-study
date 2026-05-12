# Stage 2 — Triton TTIR / TritonGPU dialect 이해 (source side)

> **상위 plan**: `notes/full_plan_for compiler_study.md` (v5.2)
> **선행 조건**: Stage 1 종료 조건. 최소한 Toy Ch5(Dialect Conversion 진입) 까지는 손에 익은 상태.
> **위치 근거**: 학습 종착점이 `triton-lang/Triton-to-tile-IR` 기여라면, 변환의 *source dialect*를 모르고는 conversion pass를 읽거나 수정할 수 없다. 이 stage는 그 source side를 IR 내부 관점에서 본다.

---

## 왜 IREE 대신 TTIR/TritonGPU인가

| 척도 | TTIR/TritonGPU | IREE |
|------|----------------|------|
| triton-to-tile-IR과의 거리 | **변환의 입력 그 자체** | 인접 영역 |
| 학습 종착점과의 직격 | ★ | △ |
| 소스 크기 | dialect 부분만 보면 manageable | 큼 |
| 이미 본 영역과의 중복 | kernel writer 관점만 빼면 새 영역 | 새 영역 |

IREE는 *production backend pipeline 전체 관점*이 필요해질 때 발췌. 활성 트랙 아님 (`stage2-iree-deep-read.md`는 reference로 남겨둠).

**주의**: "Triton 내부"라는 말은 두 관점이 섞여 있다.
- *kernel writer 관점* — autotuning, `tl.dot` 같은 high-level builtin 사용법, num_warps 튜닝. **이미 본 영역. 이 stage에선 빼고 간다.**
- *IR 내부 관점* — `triton` dialect의 op 정의, `triton_gpu` dialect의 layout encoding, conversion 진입점. **이 stage가 보는 대상.**

---

## 목표

- `triton` dialect (TTIR) 의 핵심 op 카테고리와 대표 op의 ODS 정의를 자기 말로 설명한다.
- `triton_gpu` dialect 의 layout encoding (blocked / mma / dot_operand 등) 이 *왜 attribute로* 들어가는지, 무엇을 표현하는지 설명한다.
- TTIR ↔ TritonGPU 사이의 conversion 진입점이 어디인지 짚는다 (본격 정독은 Stage 2.7).

"Triton 전부 이해"가 아님. **변환 입력으로서 필요한 만큼**이 기준.

---

## C++ 메모

Stage 2는 *읽기* 중심. 새 C++ 패턴은 거의 안 나옴 — Stage 1 글로서리가 거의 그대로 적용됨. 다만 두 가지가 새로 등장:

- **forward declaration / opaque pointer 더 적극적**: Triton 같은 큰 프로젝트는 헤더 의존성 줄이려고 `class Operation;` 처럼 *선언만* 하고 실제 정의는 cpp에서 include. "이 클래스가 어디 정의됐는지" 찾으려면 헤더의 include가 아니라 cpp의 include를 봐야 할 때가 있음.
- **`namespace mlir::triton`, `namespace mlir::triton::gpu`**: 중첩 namespace. C++17 부터 `namespace mlir::triton {}` 한 줄로 쓸 수 있어서 헷갈리지 않게 됨. Python의 모듈 경로 (`mlir.triton.gpu`) 와 같은 자리.

새 패턴 만나면 Stage 1 글로서리에 추가.

---

## 진행 단위

### Block 1 — 클론 + 디렉토리 지도 + test IR 한 번 읽기

**할 일**
1. `~/dev/compiler-sources/triton`에 클론 (`.gitignore` 정신과 동일하게 sibling workspace). 이 repo 안에 넣지 않는다.
2. 빌드는 *선택*. Stage 2의 목적은 ODS / 헤더 / test IR 읽기다. 빌드 안 되어도 진행 가능.
3. 디렉토리 지도 (대략 — 버전에 따라 변동 있음, 실제로 확인):
   - `include/triton/Dialect/Triton/IR/` — TTIR ODS 핵심
   - `include/triton/Dialect/TritonGPU/IR/` — TritonGPU ODS
   - `lib/Dialect/Triton/` — TTIR 구현
   - `lib/Dialect/TritonGPU/` — TritonGPU 구현
   - `lib/Conversion/TritonToTritonGPU/` — TTIR → TritonGPU 변환 진입점 ★
   - `test/Triton/`, `test/TritonGPU/` — IR 예시 + FileCheck
4. `test/` 에서 `.mlir` 파일 두 개 (TTIR 쪽 하나, TritonGPU 쪽 하나) 골라 *눈으로* 본다. 한 op의 dump가 어떻게 생겼는지 감만.

**산출물**: `notes/weekNN.md` 안에 디렉토리 지도 5~7줄 + TTIR/TritonGPU IR 발췌 각 한 줄.

---

### Block 2 — `triton` dialect (TTIR) op 분류

**할 일**
1. `include/triton/Dialect/Triton/IR/TritonOps.td` (또는 동등 파일) 을 *훑는다*. 모든 op 이해하지 않음.
2. op을 **3~4 카테고리로 분류**. 예상되는 분포:
   - compute / arithmetic (`tt.dot`, `tt.reduce`, elementwise math)
   - memory / pointer (`tt.load`, `tt.store`, `tt.addptr`, `tt.make_tensor_ptr`)
   - tensor / layout (`tt.broadcast`, `tt.expand_dims`, `tt.reshape`, `tt.trans`)
   - control / structural (region을 가진 op들, `tt.func` 등)
3. 각 카테고리 대표 op 1개씩 골라 ODS 정의를 자세히 본다 — `summary`, `arguments`, `results`, `assemblyFormat`, traits.
4. `tt.dot` 은 거의 무조건 한 번 깊게 본다. cuda-tile의 mma 계열과 직접 매칭될 op.

**산출물**: op 카테고리 표 + 대표 op 4개의 ODS 발췌 메모.

---

### Block 3 — `triton_gpu` dialect: layout encoding  ★ 핵심

**왜 핵심인가**: TritonGPU는 TTIR과 같은 op의 *GPU-specific 변형*을 다루면서 **layout을 type/attribute에 인코딩**한다. 이 encoding 체계가 cuda-tile의 layout/memory encoding과 매핑되어야 하고, `TritonToCudaTile.*`의 절반은 layout 변환이다.

**할 일**
1. `include/triton/Dialect/TritonGPU/IR/TritonGPUAttrDefs.td` (또는 동등 파일) 에서 layout attribute 정의 확인:
   - `BlockedEncoding` — thread/warp/CTA shape 표현
   - `MmaEncoding` — MMA instruction 결과 layout
   - `DotOperandEncoding` — dot operand의 위치(opIdx)와 parent layout
   - `SliceEncoding` — 차원 축소된 layout
2. `TritonGPUTypes.td` 에서 layout-aware 타입 (보통 `RankedTensorType` + encoding attribute) 이 어떻게 결합되는지 짚는다.
3. `TritonGPUOps.td` 에서 layout 변환 op (`triton_gpu.convert_layout` 등) 의 정의 확인.
4. test에서 `#blocked = #triton_gpu.blocked<...>` 같은 attribute 인스턴스 dump를 두세 개 *눈으로* 따라가본다. 어떤 thread가 어떤 element를 들고 있는지 머릿속에 그려질 정도까지.

**산출물**: layout encoding 4종 비교 표 (이름 / 무엇을 표현 / 언제 등장) + `convert_layout` IR 예시 한 개 자기 주석 달기.

---

### Block 4 — TTIR → TritonGPU 진입점 정찰 (얕게)

**할 일**
1. `lib/Conversion/TritonToTritonGPU/TritonToTritonGPUPass.cpp` (또는 동등 파일) 을 *얕게* 본다. 전체 코드 이해 X.
2. 짚을 것만:
   - `ConversionTarget` 설정: 무엇이 illegal로 잡히는가
   - `TypeConverter`: tensor type에 어떤 encoding이 붙는가
   - `populate*Patterns` 함수 호출 위치: 패턴 모음이 어디서 등록되는가
   - 대표 OpConversionPattern 1개 (예: `tt.dot` 변환) 의 골격 — `matchAndRewrite` 진입과 종료만
3. Toy Ch5/Ch6 lowering 구조와 *나란히* 비교하면서 한 줄씩 메모.

**왜 얕게 가는가**: TritonToTritonGPU 본격 정독은 의도적으로 *Stage 2.7과 묶지 않음*. Stage 2.7은 TritonToCudaTile이 본 대상. 여기선 "production conversion pass가 어떻게 생겼는지 한 번 본다" 정도면 됨.

**산출물**: 진입점 파일의 5줄 요약 + 1개 패턴의 골격 메모. Toy lowering과의 차이점 2~3개.

---

### Block 5 — Stage 2 회고: source side 정리

**할 일**
종합 메모를 `notes/stage2-ttir-source-summary.md` (또는 동등) 로 작성. Stage 2.7 진입 직전의 *입력 자료*가 되어야 함.

포함할 것:
1. TTIR op 카테고리 표 (Block 2).
2. TritonGPU layout encoding 비교 표 (Block 3).
3. `triton` ↔ `triton_gpu` 의 역할 분담을 자기 말로 한 단락.
4. Stage 2.7 진입 시 *이미 알고 있는* op / encoding 목록 — 이게 Stage 2.7에서 코드를 *예측 가능하게* 읽게 해주는 자산.
5. (선택) cuda-tile (Stage 2.5 산출물) 과의 잠정 매핑 — 알아본 만큼만 한두 줄.

**산출물**: `stage2-ttir-source-summary.md` — Stage 2.7 진입 직전 source-side 요약.

---

## Stage 2 종료 조건

- Triton repo가 클론되어 있고 디렉토리 지도가 있다 (빌드는 선택).
- TTIR op 카테고리 분류가 끝나 있다.
- TritonGPU의 layout encoding 4종 정도를 *자기 말로* 구분해서 설명할 수 있다.
- TritonToTritonGPU 진입점 파일을 한 번은 훑었고 골격을 안다.
- 위 네 가지가 `stage2-ttir-source-summary.md` 한 장에 정리되어 있다.

이 다섯이 되면 Stage 2.5(cuda-tile target side)로 진행하거나, 이미 끝났다면 Stage 2.7로 바로.

---

## 의도적으로 빼는 것

- **kernel writer 관점**. autotuning, `tl.dot` builtin 사용법, num_warps 튜닝, kernel porting — 이미 본 영역.
- **`triton/python/` DSL frontend**. eDSL 구현은 IR 내부와 분리된 학습 대상.
- **성능 / 벤치마크**. Stage 2의 목적은 "변환 입력으로서의 IR 이해"지 *어떻게 빠르게 도느냐*가 아님.
- **Triton 본체 빌드/실행 의무**. ODS와 헤더만 읽어도 stage 목표는 달성 가능. 시간 남으면 빌드.
- **`triton-shared` 등 외부 fork / mirror**. upstream `openai/triton` 또는 `triton-lang/triton` 한쪽만.
- **IREE 본격 정독**. v5.2에서 강등된 경로. 필요해지면 `stage2-iree-deep-read.md`를 발췌.
