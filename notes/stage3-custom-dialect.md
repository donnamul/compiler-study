# Stage 3 — Custom Dialect + Linalg Lowering + Bufferization  ★

> **상위 plan**: `notes/full_plan_for compiler_study.md`
> **선행 조건**: Stage 2 종료 조건 + Stage 2.5 종료 조건 (cuda-tile 디자인 결정 표) 모두 충족.
> **핵심 입력**: `stage2_5-cuda-tile-design-notes.md`의 디자인 결정 표. mini dialect의 첫 디자인 결정은 거기서 빌려 시작한다.

---

## 왜 핵심인가

HyperAccel LPU에서 하는 일이 결국 *custom dialect 디자인 + lowering + bufferization*이다. Stage 1~2.5는 이 stage를 위한 준비였다.

## 목표

- out-of-tree mini dialect 한 개를 ODS로 직접 만든다.
- 그 dialect의 lowering pass 한 개를 작성해서 Linalg/arith/tensor 로 내린다.
- bufferization pass를 끼워 tensor → memref 전환을 직접 관찰한다.

"production-grade dialect"가 목표가 아님. *동작하는 미니 dialect*가 목표.

---

## 진행 단위

### Block 1 — out-of-tree skeleton 만들기

**할 일**
1. `experiments/mini-dialect/`에 CMake 기반 out-of-tree MLIR 프로젝트 skeleton.
   - 참고: `llvm-project/mlir/examples/standalone/` (있다면) 또는 IREE의 외부 dialect 예시.
2. 빈 dialect `chip`를 등록하고 `chip-opt` 바이너리가 빌드되는 것까지.
3. `chip-opt < /dev/null` 같은 sanity check.

**산출물**: 빌드되는 빈 dialect.

---

### Block 2 — Op 정의 (ODS)

**할 일**
1. op 3~5개를 ODS로 정의:
   - `chip.matmul (tensor<MxKxf32>, tensor<KxNxf32>) -> tensor<MxNxf32>`
   - `chip.elementwise_add (tensor, tensor) -> tensor`
   - `chip.layout_convert (tensor) -> tensor` (attribute로 layout 표현)
2. 적절한 Traits 한두 개 (`Pure`, `SameOperandsAndResultElementType` 등) 붙임.
3. `.td`에서 `assemblyFormat` 직접 작성해 IR이 사람 읽을 수 있게.

**산출물**: `chip` dialect의 op 정의 + IR 예시 파일 한 개 (`chip-opt`로 round-trip 확인).

---

### Block 3 — Verifier + Type inference (간소)

**할 일**
1. `chip.matmul`에 verifier 추가 (shape 호환성 확인).
2. shape inference interface 한 op에만 시범적으로 붙임 (Stage 1 Ch4 복습).
3. 잘못된 입력으로 verifier가 동작하는지 FileCheck 테스트 한 개.

**산출물**: verifier + 실패하는 케이스의 FileCheck.

---

### Block 4 — Lowering pass: `chip` → Linalg

**할 일**
1. `chip.matmul → linalg.matmul`, `chip.elementwise_add → linalg.generic` 변환 pattern 작성.
2. ConversionTarget을 `chip` dialect는 illegal, `linalg`/`arith`/`tensor`는 legal로 설정.
3. 작은 입력으로 변환 확인:
   ```bash
   chip-opt --chip-to-linalg input.mlir
   ```
4. Stage 1 Ch5의 Toy lowering 구조와 *나란히* 비교 메모.

**산출물**: lowering pass 코드 + before/after IR.

---

### Block 5 — Bufferization 끼우기

**할 일**
1. lowering 결과를 표준 bufferization pipeline에 통과:
   ```
   chip-opt input.mlir \
     --chip-to-linalg \
     --one-shot-bufferize \
     --convert-linalg-to-loops
   ```
2. tensor → memref 전환 지점을 IR에서 직접 본다.
3. 필요시 `chip` op 중 하나에 `BufferizableOpInterface`를 시범적으로 구현 (선택).
4. 어디서 alloc이 박히고 어디서 dealloc이 박히는지 메모.

**산출물**: bufferize 후 IR + "alloc 위치 결정 원리" 짧은 메모.

---

### Block 6 — Stage 3 회고

**할 일**
1. `stage3-custom-dialect.md` 끝에 종합 회고:
   - 새 dialect를 디자인할 때 가장 먼저 결정할 것 (op 단위, 타입, 메모리 모델, layout 표현 위치)
   - lowering 경로를 선택하는 기준
   - bufferization을 *언제* 박는지가 무엇을 결정하는지
2. HyperAccel Legato와 *구조적으로* 매핑되는 부분 한 단락 (회사 자산은 안 적음 — 일반론으로).

**산출물**: 회고 메모 + Stage 4 진입 직전 정리.

---

## Stage 3 종료 조건

- `experiments/mini-dialect/`가 빌드되고 `chip-opt`가 동작한다.
- `chip.matmul` 외 2개 이상의 op이 있고, verifier가 있다.
- `chip → linalg` lowering이 동작한다.
- bufferization 후 IR을 *읽고 설명할 수 있다*.
- 새 dialect 디자인 시 결정 순서를 자기 말로 정리했다.

이 다섯이 되면 너는 "MLIR을 안다"고 말할 수 있다.

---

## Stage 3 이후

`notes/full_plan_for compiler_study.md`의 Stage 4 회고로. 추가 학습은 그때 결정.
