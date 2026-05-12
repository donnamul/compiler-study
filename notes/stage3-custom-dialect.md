# Stage 3 — out-of-tree mini conversion pass (A→B)  ★ 핵심

> **상위 plan**: `notes/full_plan_for compiler_study.md` (v5.2)
> **선행 조건**: Stage 2 (TTIR source) + Stage 2.5 (cuda-tile target) + Stage 2.7 (production conversion pass 정독) 종료. 특히 Stage 2.7의 "Stage 3에서 따라할 구조" 결정이 있어야 한다.
> **핵심 입력**: `stage2_7-triton-to-tile-deep-read.md` 의 패턴 골격 + `stage2_5-cuda-tile-design-notes.md` 의 디자인 결정 표.

---

## v5.2 reframe — 무엇이 바뀌었나

v5.1의 Stage 3는 "out-of-tree mini *dialect* 만들기"였다. v5.2에서는 **mini dialect-to-dialect *conversion pass* 짜기**가 중심이다. dialect 자체는 conversion pass의 source/target 으로 *필요한 만큼만* 정의한다.

이유: 학습 종착점이 `Triton-to-tile-IR` 기여 — 거기서 손댈 곳은 conversion pattern이지 새 dialect가 아니다. *production에서 자기가 짤 코드*가 conversion pass 모양이라면 연습도 conversion pass여야 한다.

---

## 왜 핵심인가

Stage 2.7에서 본 production conversion pass의 *축소 모델*을 자기 손으로 짠다. 이 행위가:
- ConversionTarget / TypeConverter / OpConversionPattern 등록 / `populate*Patterns` 의 골격을 손에 박는다
- layout / encoding 변환을 작은 규모에서 직접 다룬다
- bufferization 진입을 직접 본다
- 새 패턴 추가가 어떤 작업인지 *몸으로* 안다 — Stage 4의 첫 기여를 가능하게 한다

"production-grade conversion"이 목표가 아님. **동작하는 미니 conversion pass**가 목표.

---

## 디자인 (Stage 2.5 / 2.7 입력을 받아 결정)

### Source dialect: `chip`

TTIR의 *축소 모델*. 3개 op만:
- `chip.matmul (tensor<MxKxf32>, tensor<KxNxf32>) -> tensor<MxNxf32>` — `tt.dot` 의 microcosm
- `chip.elementwise_add (tensor, tensor) -> tensor` — elementwise op 대표
- `chip.layout_convert (tensor) -> tensor` (attribute로 layout) — TritonGPU `convert_layout` 의 microcosm

### Target dialect: `tile`

cuda-tile의 *축소 모델*. 2~3개 op만:
- `tile.mma` — `chip.matmul` 의 target
- `tile.elementwise` — `chip.elementwise_add` 의 target
- (선택) `tile.layout_convert`

### 핵심 변환: `ChipToTile` conversion pass

`TritonToCudaTile.*` 의 축소 모델. Stage 2.7에서 본 골격을 그대로 따라간다:
- ConversionTarget: `chip` illegal, `tile` legal
- TypeConverter: tensor type을 (선택) tile 타입 또는 encoding을 가진 tensor 타입으로 변환
- OpConversionPattern 3개: matmul / elementwise / layout_convert 각각

### Layout encoding 결정

Stage 2.5의 디자인 결정 표 + Stage 2의 TritonGPU encoding 학습에서 *하나만* 빌려서 적용. 후보:
- attribute로 layout 표현 (TritonGPU 스타일)
- 타입에 layout 인코딩 (cuda-tile 일부 케이스)
- 그냥 dense layout으로 무시 (mini scale에서는 OK)

학습 목적상 *최소 한 번은* layout이 보이는 변환을 짜본다 — 그래야 `convert_layout` 패턴이 손에 박힌다.

---

## C++ 메모

Stage 3은 *처음으로 production 규모의 conversion pass를 자기 손으로 쓰는* 자리. Stage 1에서 *한 패턴* 짠 것과 다르게, 여기서는:
- 자기 dialect 둘 (`chip`, `tile`) 의 ODS 정의 → 생성된 C++ 사용
- `TypeConverter` 직접 등록 (Stage 1에서는 거의 안 짰음 — Toy 의 NegOp lowering은 type 변환이 trivial)
- `populate*Patterns` 함수 자체를 직접 작성
- CMake / out-of-tree build setup

새로 손에 박을 C++ 패턴 (Stage 1 글로서리에 누적):
- **CMake 의 `add_mlir_dialect(...)`, `add_mlir_doc(...)` 매크로**: out-of-tree dialect의 표준 빌드 설정. 한 번 설정해두면 거의 안 건드림. 막히면 `mlir/examples/standalone/` 의 CMakeLists를 거의 그대로 베낌.
- **`TypeConverter` 의 `addConversion([&](TensorType t) { ... return newType; });`**: Block 4의 핵심. lambda로 *"이 타입을 이렇게 바꾼다"* 를 등록. Stage 2.7에서 본 패턴을 *직접 작성*.
- **`addSourceMaterialization` / `addTargetMaterialization` / `addArgumentMaterialization`**: TypeConverter가 *변환된 type과 원래 type 사이에 cast op을 끼워야 할 때* 호출되는 callback. 처음 만나면 헷갈림 — *언제 호출되는지* 가 핵심. Block 4 에서 막히면 MLIR docs의 "Dialect Conversion" 페이지 발췌.
- **`populate*Patterns(RewritePatternSet &patterns, TypeConverter &typeConverter, ...)`**: out-parameter 패턴 — Python의 return 값 대신 *주어진 컨테이너에 추가*. 이게 MLIR 전반의 표준 형태. 한 번 짜면 손에 박힘.
- **CMake error vs C++ link error vs C++ compile error**: Stage 3 초반에 세 종류 모두 한 번씩 봄. 각각 어떻게 생겼는지 *익숙해지는* 것이 production 작업의 토대.

**자가 점검**: Block 4 끝나고도 위 다섯 패턴 중 *셋 이상* 자기 말로 설명 못 하면, Stage 4 (실제 기여) 가 어려움. 그 경우 Stage 2.7로 잠깐 돌아가서 production 코드 한 패턴 더 정독.

---

## 진행 단위

### Block 1 — out-of-tree skeleton 만들기

**할 일**
1. `experiments/mini-conversion/`에 CMake 기반 out-of-tree MLIR 프로젝트 skeleton.
   - 참고: `llvm-project/mlir/examples/standalone/` (있다면) 또는 최근 standalone 예시.
2. 빈 dialect 두 개 (`chip`, `tile`) 등록.
3. `mini-opt` (또는 동등) 바이너리가 빌드되고 `--help` 가 동작.
4. `mini-opt < /dev/null` sanity.

**산출물**: 빌드되는 빈 두 dialect.

---

### Block 2 — source dialect `chip` 정의

**할 일**
1. `chip` 의 3개 op을 ODS로 정의.
2. 적절한 traits (`Pure`, `SameOperandsAndResultElementType` 등) 한두 개.
3. `assemblyFormat` 직접 작성 — IR이 사람이 읽을 수 있게.
4. `chip.layout_convert` 의 layout attribute 정의 (간소화된 BlockedEncoding 비슷한 것).

**산출물**: `chip` op 정의 + IR 예시 파일 (`mini-opt`로 round-trip 확인).

---

### Block 3 — target dialect `tile` 정의 (cuda-tile microcosm)

**할 일**
1. `tile` 의 2~3개 op을 ODS로 정의.
2. (선택) cuda-tile의 *디자인 결정 하나* 빌려옴 — 예: layout을 type 안에 인코딩하기, 또는 attribute로 분리하기. 어느 쪽이든 *왜 그렇게 했는지* Stage 2.5 메모에서 가져온다.
3. `tile` 의 IR 예시 한 개 만들고 round-trip.

**산출물**: `tile` op 정의 + IR 예시. Stage 2.5 디자인 결정과의 연결 한 줄 메모.

---

### Block 4 — `ChipToTile` conversion pass ★ 가장 중요

**할 일**
1. Stage 2.7에서 본 `TritonToCudaTile` 골격을 *그대로* 따라간다.
2. pass 클래스 + `runOnOperation()`:
   - `ConversionTarget`: `chip` illegal, `tile`/`arith`/`tensor` legal
   - `TypeConverter`: tensor → tensor-with-encoding (또는 tile 타입)
   - `RewritePatternSet patterns`
   - `populateChipToTilePatterns(patterns, typeConverter)` 함수 별도로
   - `applyPartialConversion`
3. 3개 OpConversionPattern 구현:
   - `ChipMatmulToTileMma` — operand type 변환, attribute 매핑, result type
   - `ChipElementwiseAddToTileElementwise` — 단순 매핑이지만 type converter 통과 확인
   - `ChipLayoutConvertToTile` — layout attribute 변환 ★ (encoding 처리 손에 박히는 자리)
4. 작은 입력으로 변환 확인:
   ```bash
   mini-opt --chip-to-tile input.mlir
   ```
5. Stage 2.7에서 본 패턴 3개의 골격과 *나란히* 비교 메모. 차이가 있다면 왜 그런지.

**왜 가장 중요한가**: Stage 2.7 정독을 *행위*로 바꾸는 자리. 여기를 안 짜면 Stage 2.7은 머리에서만 산다.

**산출물**: `ChipToTile` pass 코드 + before/after IR + Stage 2.7 골격과의 비교 메모.

---

### Block 5 — Bufferization 끼우기

**할 일**
1. `chip → tile` 후의 IR을 표준 bufferization pipeline에 통과:
   ```
   mini-opt input.mlir \
     --chip-to-tile \
     --one-shot-bufferize \
     [--convert-...-to-loops 등 필요한 것]
   ```
2. tensor → memref 전환 지점을 IR에서 직접 본다.
3. 필요시 `tile` op 중 하나에 `BufferizableOpInterface`를 시범적으로 구현 (선택).
4. 어디서 alloc이 박히고 어디서 dealloc이 박히는지 메모.

**왜 끼우는가**: cuda-tile은 결국 메모리 모델을 노출한다 (`unordered memory model`, `memory token`). 작은 규모에서 bufferization 진입을 직접 보지 않으면 cuda-tile의 메모리 의사결정이 추상적으로만 남는다.

**산출물**: bufferize 후 IR + "alloc 위치 결정 원리" 짧은 메모.

---

### Block 6 — Stage 3 회고: 자기 손으로 짠 conversion pass 메모

**할 일**
1. `stage3-mini-conversion-retro.md` 종합 회고:
   - `ChipToTile` 짤 때 *가장 헷갈렸던* 부분 (대개 TypeConverter 또는 layout 처리)
   - Stage 2.7 골격과 *나란히 짚어보면서* 보였던 production 코드의 의도
   - 새 OpConversionPattern을 추가하라는 task를 받았을 때 어떤 순서로 손댈지 — 자기 말로 4~6단계
2. Stage 2.7 산출물 `stage2_7-contribution-candidates.md` 를 다시 펴고, 각 후보에 대해:
   - "이제 어디를 손대야 하는지 보이는가" 자기 평가
   - 보인다면 다음에 *어느 후보부터* 손댈지

**산출물**: `stage3-mini-conversion-retro.md` + 갱신된 contribution-candidates 목록.

---

## Stage 3 종료 조건

- `experiments/mini-conversion/` 가 빌드되고 `mini-opt` 가 동작한다.
- `chip` op 3개와 `tile` op 2~3개가 ODS로 정의되어 있고 round-trip 한다.
- `ChipToTile` conversion pass가 동작하고 IR 변환 결과가 의도대로 나온다.
- layout / encoding 처리를 *최소 한 번은* 직접 다뤘다.
- bufferization을 끼워 tensor → memref 전환 IR을 읽고 설명할 수 있다.
- Stage 2.7의 contribution candidate 목록 중 *최소 한 개*는 손댈 위치가 보인다.

이 여섯이 되면 Stage 4 진입. 그 시점에서 너는 "production conversion pass의 패턴 추가가 가능한 상태"다.

---

## 의도적으로 빼는 것

- **production-grade dialect 디자인**. `chip` / `tile` 둘 다 학습용 microcosm. 완성도 추구하지 않는다.
- **Linalg으로 내리기**. v5.1 plan에 있던 chip → Linalg 경로는 *학습 종착점이 바뀌었으므로* 빠진다. 굳이 보고 싶으면 Stage 4 이후 선택.
- **HyperAccel LPU 매핑**. v5.1에 있던 Legato 매핑 메모는 secondary motivation으로 격하 — 이 stage는 OSS triton-to-tile-IR 기여 준비에 집중. LPU 회사 자산도 적지 않는다.
- **여러 conversion pass 만들기**. 하나(`ChipToTile`)만. 두 번째를 짤 시간이 있으면 그건 Stage 4 이후의 실제 기여 작업.
- **`tile` 의 모든 cuda-tile 특성 재현**. bytecode, 모든 trait, 모든 interface — 다 무시. 학습 목적상 필요한 *디자인 결정 한 개*만 빌려옴.
