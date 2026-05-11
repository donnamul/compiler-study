# Stage 2.5 — NVIDIA/cuda-tile dialect 디자인 분석

> **상위 plan**: `notes/full_plan_for compiler_study.md`
> **선행 조건**: Stage 2 종료 조건 4개 모두 충족.
> **위치 근거**: Stage 2(IREE)는 *backend pipeline* 관점, 이 stage는 *dialect 자체 디자인* 관점. 두 관점을 묶으면 학습 흐름이 흐려지고, Stage 3 (mini dialect 직접 설계) 들어가기 직전의 입력으로는 dialect 디자인이 본질이라 분리.

---

## 왜 cuda-tile인가

`NVIDIA/cuda-tile` (github.com/NVIDIA/cuda-tile, CUDA Toolkit 13.1과 함께 2025-11 공개) 은 reference로 *특별히* 좋다.

| 척도 | cuda-tile | Toy | IREE | llvm-project |
|------|-----------|-----|------|--------------|
| 소스 크기 | **~1 MB** | KB 단위 | 수십~수백 MB | 수 GB |
| MLIR 비중 | **100%** (dialect 자체) | 100% | 부분 | 일부 |
| 공개 시점 | 2025-11 (6개월) | 안정 | 수년 | 수십년 |
| 표준 ODS 구조 | `Ops`/`Types`/`AttrDefs`/`Interfaces`/`Passes`/`Bytecode` 분리 | 단순화 | 분산 | 분산 |

→ **production quality + 한 사람이 거의 다 이해 가능한 사이즈**의 흔치 않은 조합.

HyperAccel LPU 작업과 매핑이 직접적:
- `tile` 타입 정의 방식 (`Types.td`)
- layout / memory hierarchy를 attribute에 인코딩 (`AttrDefs.td`)
- op interface 설계 (`Interfaces.td`)
- bytecode 직렬화 (`BytecodeOpcodes.td`) — runtime에 IR 던질 때의 인터페이스

이미 본 영역 (CuTe, CUTLASS, Triton autotuning, Helion 같은 *kernel writer* 관점)이 아니라 *dialect designer* 관점이라 새로움.

---

## 목표

cuda-tile의 디자인 결정 5~7개를 추출해서, Stage 3에서 만들 `chip` mini dialect의 디자인 결정 입력으로 사용한다.

"cuda-tile을 다 이해"가 아님. **디자인 결정과 그 근거를 짚는다**가 목표.

---

## 진행 단위

### Block 1 — 클론 + 빌드 + 표면 훑기

**할 일**
1. `~/dev/compiler-sources/cuda-tile`에 클론 (`.gitignore` 정신과 동일하게 sibling workspace).
2. README의 quick-start로 최소 빌드. LLVM/MLIR sources는 build에서 자동 다운로드되니 비활성화 없이 진행. Python bindings는 처음엔 off로 두고 시간 남을 때 켜기.
3. 디렉토리 지도:
   - `include/cuda_tile/Dialect/CudaTile/IR/` — ODS 핵심
   - `include/cuda_tile/Dialect/CudaTile/Transforms/` — pass 선언
   - `lib/Dialect/CudaTile/IR/OpsCanonicalization.td` — fold/rewrite
   - `python/cuda_tile/` — Python bindings
   - `test/` — IR 예시 + FileCheck (실제 dialect IR 보기 좋음)
4. `test/` 디렉토리에서 작은 `.mlir` 파일 하나 골라 *눈으로* 한번 읽어본다. 한 op의 dump가 어떻게 생겼는지 감.

**산출물**: 디렉토리 지도 4~5줄 + test에서 본 dialect IR 한 줄 예시.

---

### Block 2 — `Dialect.td` + `Ops.td` 훑고 op 분류

**할 일**
1. `Dialect.td`에서 dialect 이름, dependent dialect, hasOperation 등 메타 설정 확인.
2. `Ops.td`를 처음부터 끝까지 빠르게 *훑는다*. 모든 op을 이해하지 않는다.
3. op을 **3~4 카테고리로 분류**:
   - compute (matmul, mma, elementwise, reduction)
   - memory / data movement (load / store / copy)
   - layout / tile manipulation (transpose, reshape, broadcast)
   - control / structural (region 가진 op들)
4. 각 카테고리 대표 op 1개씩 골라 ODS 정의를 자세히 본다 — `summary`, `arguments`, `results`, `assemblyFormat`.

**산출물**: op 카테고리 표 + 대표 op 4개의 ODS 발췌 메모.

---

### Block 3 — `Types.td` + `AttrDefs.td`: tile 타입과 layout encoding  ★

**할 일**
1. `Types.td`에서 핵심 타입 정의 확인. 특히:
   - tile 타입 자체 (shape, element type을 어떻게 인코딩)
   - 메모리 공간 / register-resident인지 표현 방식
2. `AttrDefs.td`에서 다음을 짚는다:
   - layout 정보가 어디에 들어가는가 (타입 안 vs attribute로 따로)
   - memory hierarchy 표현 (shared / global / register 등)
   - tile size를 컴파일 타임 / 런타임 중 어느 쪽으로 다루는가
3. 자기 dialect에서 같은 결정을 어떻게 내릴지 한 줄씩 메모.

**왜 핵심인가**: dialect 디자인의 가장 어려운 결정들. Stage 3에서 `chip.layout_convert` 또는 그 자리에 들어갈 op을 정의할 때 직접 입력.

**산출물**: 디자인 결정 표 — `cuda-tile은 X로 했다 / 이유 / chip dialect에선 Y로 할 것 같다`.

---

### Block 4 — `Interfaces.td` + Traits 사용

**할 일**
1. `Interfaces.td`에서 op interface 목록 + 메서드 시그니처 확인.
2. `Ops.td`에서 op이 어떤 interface / trait을 implement하는지 짚어본다. 빈도 높은 interface 2~3개 위주.
3. MLIR upstream의 `OpAsmOpInterface`, `SymbolOpInterface`, `MemoryEffectOpInterface` 같은 표준 interface와 cuda-tile 고유 interface가 어떻게 섞이는지 본다.

**산출물**: interface 사용 패턴 메모 — 표준 vs 고유, 어디에 어떤 trait이 붙는지.

---

### Block 5 — Canonicalization + Pass 한 개의 깊이

**할 일**
1. `lib/Dialect/CudaTile/IR/OpsCanonicalization.td`에서 fold / rewrite 패턴 2~3개 골라 읽기. Toy Ch3 / IREE canonicalization과 같은 뼈대인지 확인.
2. `include/cuda_tile/Dialect/CudaTile/Transforms/Passes.td`에서 pass 목록 훑기. 이름만으로도 어떤 변환을 하는지 추정.
3. 그 중 *하나*만 골라 실제 C++ 구현 파일을 열어 `runOnOperation()`의 구조를 짚는다 — 전부 이해 X, ConversionTarget / Pattern / TypeConverter / RewritePatternSet 어디 있는지만.

**산출물**: 패턴 2~3개 발췌 + pass 1개의 골격 메모.

---

### Block 6 — (선택) Bytecode serialization

**할 일**
1. `BytecodeOpcodes.td`, `BytecodeTypeOpcodes.td`를 훑고 bytecode와 textual IR이 어떻게 매핑되는지 감만 잡는다.
2. MLIR upstream의 bytecode infrastructure 위에 어떻게 dialect-specific opcode를 얹는지 본다.
3. 이게 왜 필요한가에 대한 한 줄 — "runtime이 textual IR을 파싱하지 않고 IR을 받기 위해".

Legato가 LPU runtime에 IR을 던질 때 같은 결정이 필요한지 떠올려본다.

**산출물**: bytecode 사용 이유 한 단락 + Legato와의 대응 가설 메모.

---

### Block 7 — Stage 2.5 회고: dialect 디자인 결정 5~7개 추출

**할 일**
종합 메모를 `stage2_5-cuda-tile-design-notes.md`로 새로 작성. 각 결정에 대해:
- cuda-tile은 어떻게 했나
- 왜 그렇게 했나 (추정해도 됨)
- `chip` mini dialect (Stage 3)에서는 어떻게 할지 잠정 결정

후보 결정:
1. tile 타입을 *built-in* 타입으로 둘 것인가 *dialect 고유* 타입으로 둘 것인가
2. layout 정보를 타입 안에 인코딩할 것인가 attribute로 분리할 것인가
3. memory space를 어떻게 표현할 것인가 (`memref` 메모리 공간 차용 vs 고유 attribute)
4. tile size를 컴파일 타임 상수로만 받을 것인가, dynamic size까지 허용할 것인가
5. op 단위를 어디까지 작게 / 어디까지 묶을 것인가 (matmul을 한 op vs load+mma+store 분리)
6. region을 가진 op (loop-like)을 어떻게 표현할 것인가
7. textual IR 외에 bytecode 직렬화를 가질 것인가

전부 답할 필요 없음. *답 가능한 것만* 답해도 큰 진전.

**산출물**: `stage2_5-cuda-tile-design-notes.md` — Stage 3 진입 직전 디자인 결정 표.

---

## Stage 2.5 종료 조건

- cuda-tile이 빌드되고 test가 돌아간다 (혹은 빌드는 시간 없으면 스킵, ODS 읽기만으로도 OK).
- op 카테고리 분류가 끝났다.
- 디자인 결정 표가 5개 이상의 항목으로 채워져 있다.
- 그 중 최소 3개에 대해 chip dialect에서의 잠정 결정이 적혀 있다.

이 4개가 되면 Stage 3 진입 — 그때 mini dialect의 *첫 번째 디자인 결정*은 이미 있는 셈.

---

## 의도적으로 빼는 것

- **kernel writing 관점** (어떻게 빠른 matmul을 쓰는가, autotuning 등) — 이미 본 영역.
- **Python bindings 깊이** — 학습 본질 아님. Legato가 Python eDSL이라 frontend 패턴 참고가 필요하면 Block 6 끝나고 30분 추가.
- **PTX / runtime / tileiras** — MLIR 밖이라 학습 트랙 외부.
- **cuda-tile의 모든 op 이해** — 분량 폭발. 카테고리당 1개 깊이.
