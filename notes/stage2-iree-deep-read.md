# Stage 2 — IREE 한 개를 깊게 읽기

> **상위 plan**: `notes/full_plan_for compiler_study.md`
> **선행 조건**: Stage 1 종료 조건 5개 모두 충족.

---

## 왜 IREE인가

- accelerator backend 구조 (dispatch 형성, target dialect, bufferization, codegen)가 HyperAccel LPU 작업과 *구조적으로* 가장 가깝다.
- XLA는 HLO가 메인 IR이고 MLIR 비중이 부분적. 규모 대비 MLIR 학습 효율이 낮음.
- StableHLO는 *op set 디자인*은 좋지만 *백엔드 구조*가 없다 — IREE가 그 자리.
- Triton은 이미 깊이 본 영역이라 제외.

## 목표

**한 op이 LLVM IR까지 내려가는 경로 하나를 정확히 추적할 수 있다.**

"IREE 전체 이해" 같은 욕심 X. 한 trace만 깔끔하게.

---

## 진행 단위

### Block 1 — IREE 클론 + 빌드 + 위치 파악

**할 일**
1. `~/dev/compiler-sources/iree`에 클론 (이 repo 안에 두지 않음 — `.gitignore`에 명시되어 있는 정신과 동일).
2. README의 build instruction으로 최소 빌드 (`iree-compile`, `iree-opt`, `iree-run-module`).
3. 디렉토리 지도:
   - `compiler/src/iree/compiler/InputConversion/` — frontend (StableHLO/TOSA → IREE)
   - `compiler/src/iree/compiler/Dialect/Flow/` — dispatch 형성
   - `compiler/src/iree/compiler/Dialect/HAL/` — hardware abstraction
   - `compiler/src/iree/compiler/Codegen/` — target 별 codegen
4. 빌드된 `iree-opt`로 hello world `.mlir` 한 번 돌려서 동작 확인.

**산출물**: 디렉토리 4개 짧은 설명 + 빌드 성공 표시.

---

### Block 2 — Trace 대상 op 선택 + 입력 작성

**할 일**
1. trace 대상 op 하나 결정. 추천: `linalg.matmul` 또는 `stablehlo.dot_general`. 처음엔 `linalg.matmul`이 더 직선적.
2. 작은 입력 `.mlir`을 작성 (예: `linalg.matmul`만 들어있는 함수 하나).
3. `iree-compile`에 `--mlir-print-ir-after-all`을 붙여 전체 pass dump를 파일로:
   ```bash
   iree-compile --iree-hal-target-backends=llvm-cpu \
                --mlir-print-ir-after-all input.mlir \
                -o output.vmfb 2> trace.log
   ```
4. `trace.log` 길이만 본다 (보통 수천 줄). 다 안 읽는다.

**산출물**: 입력 `.mlir` + `trace.log` 보관.

---

### Block 3 — Trace를 phase 단위로 끊기

**할 일**
1. `trace.log`에서 dialect가 바뀌는 지점만 표시:
   - `linalg` → `flow` → `stream` → `hal` → `vm` 또는 LLVM
   - 어느 pass가 그 변환을 주도하는지 pass 이름 메모
2. 각 dialect의 1줄 요약을 IREE 문서에서 가져옴 (자기 말로 다시 쓴다).
3. 변환 지점 4~6개를 골라 *before/after 2~3줄*만 캡처.

**산출물**: 변환 phase 도식 (dialect 흐름 + 주요 pass 이름) — `stage2-iree-trace.md`에 그림 1장으로.

---

### Block 4 — Conversion pattern 한 개를 코드로 따라가기

**할 일**
1. Block 3에서 본 변환 중 *하나*만 골라 실제 C++ pattern 코드 위치를 찾아간다.
   - 예: `linalg.matmul` → `flow.dispatch.workgroups` 변환
2. pattern 파일을 열어 다음 셋만 짚는다:
   - `ConversionTarget` 어디서 설정되나
   - `Pattern`이 어떻게 등록되나
   - `TypeConverter`가 있다면 무엇을 변환하나
3. Stage 1의 Toy Ch5 코드 구조와 *동일한 뼈대*인지 확인. 다른 부분만 메모.

**산출물**: pattern 1개 분석 (10~20줄) + Toy와의 구조 비교 한 단락.

---

### Block 5 — Bufferization 진입 지점 관찰

**할 일**
1. `trace.log`에서 `tensor → memref`로 바뀌는 지점을 찾는다.
2. IREE의 bufferization 단계가 어디 들어가는지 (대개 `Flow` → `Stream` 또는 `HAL` 사이) 파악.
3. One-Shot Bufferize / BufferizableOpInterface 공식 문서를 *발췌*로 읽고 IREE에서 어떤 op이 BufferizableOpInterface를 구현하는지 한두 개만 확인.

**산출물**: bufferization 진입 지점 도식 + interface 사용 op 2~3개 이름.

---

### Block 6 — Stage 2 회고 메모

**할 일**
1. `stage2-iree-trace.md`에 종합 trace를 그림 1장 + 텍스트 1페이지로.
2. 다음 셋 자기 말로:
   - IREE의 dialect 계층 (`linalg → flow → stream → hal → vm/llvm`)이 각각 무엇을 결정하나
   - 왜 dispatch region을 따로 형성하나 (HyperAccel LPU 관점)
   - bufferization을 *언제* 하느냐가 왜 중요한가
3. Stage 3 (custom dialect)에서 어떤 부분을 IREE를 참고할지 5줄로 메모.

**산출물**: `stage2-iree-trace.md` 완성 + Stage 3 입력 메모.

---

## Stage 2 종료 조건

- `iree-compile`이 동작한다.
- 한 op의 lowering trace를 dialect 5개 단위로 설명할 수 있다.
- Conversion pattern 1개 코드를 열어 ConversionTarget / Pattern / TypeConverter 위치를 짚을 수 있다.
- Bufferization 진입 지점과 BufferizableOpInterface 개념을 안다.

전부 안 되면 Stage 3 진입 X. Stage 3은 이 위에서만 의미 있다.
