# Stage 2.7 — Triton-to-tile-IR production conversion pass 정독  ★ 핵심

> **상위 plan**: `notes/full_plan_for compiler_study.md` (v5.2)
> **선행 조건**: Stage 1 종료(특히 Toy Ch5~7 Dialect Conversion), Stage 2 종료(TTIR source side 요약), Stage 2.5 종료(cuda-tile target side 디자인 결정 표). 셋 다 있어야 코드가 *예측 가능하게* 읽힌다.
> **위치 근거**: 이 stage가 학습 종착점에 가장 가깝다. 양 끝 dialect를 보고난 뒤에야 conversion 코드가 "어떤 일을 하는지"가 아니라 "어떻게 하는지"로 읽힌다.

---

## 대상 레포

`https://github.com/triton-lang/Triton-to-tile-IR` — Triton에 CUDA Tile IR backend를 추가하는 인큐베이터 fork. `ENABLE_TILE=1` 환경변수로 활성화. 기본 backend는 OSS PTX backend (Triton 3.6); fallback 경로가 박혀 있음.

핵심 코드 위치 (README 기준):
- `third_party/tileir/` — cuda-tile backend 본체
- `TritonToCudaTile.*` — TTIR을 CUDA Tile IR로 내리는 메인 conversion pass ★
- `rewriteAssume.*` — TTIR / LLVM IR의 assume op을 CUDA Tile IR의 assume op으로 변환

Triton core 쪽 변경 (참고만 — 깊게 읽지 않음):
- `driver.py`, `compiler.py` — `ENABLE_TILE=1` 시 default target 전환
- `jit.py`, `nvidia/backend/driver.py` — bug 발생 시 NVIDIA PTX backend fallback
- `core.py`, `semantic.py`, `tensor_descriptor.py` — host TMA → cuda-tile device TMA API 매핑

---

## 목표

- `TritonToCudaTile.*` 안의 conversion pass 골격 (ConversionTarget / TypeConverter / OpConversionPattern 등록 / `populate*Patterns`) 을 자기 말로 설명한다.
- 대표 OpConversionPattern 2~3개의 `matchAndRewrite` 를 줄 단위로 따라간다.
- "이 자리에 새 패턴을 추가하면 어디를 건드려야 하나" 가 머릿속에 그려진다.
- 잠재적 기여 entry point 후보 3~5개를 목록화한다 (README의 Known functional/performance issues + 코드 안의 TODO).

"전부 이해"가 아님. **기여 가능한 지점이 보이는 상태**가 기준.

---

## C++ 메모

Stage 2.7은 *production C++ 정독* 의 자리. Stage 1에서 손에 박은 패턴이 *그대로 자주* 등장한다 — `OpConversionPattern`, `matchAndRewrite`, `adaptor`, `rewriter.replaceOpWithNewOp`, `ConversionTarget`, `TypeConverter`, `applyPartialConversion`. **막히면 Stage 1 글로서리 먼저**.

이 stage에서 새로 등장할 가능성이 높은 패턴:
- **Lambda 와 `std::function`**: `target.addDynamicallyLegalOp<...>([&](Op op) { return ...; });` 형태. Python의 lambda와 같은 자리. `[&]` 는 "주변 변수를 reference로 캡처". 깊게 안 봐도 됨 — *Python lambda 라고 읽으면* 대부분 통과.
- **`SmallVector<Type, 4>` / `SmallVector<Value, 4>`**: 결과 타입 / 결과 value 모을 때. `N` (여기 4) 은 *스택에 inline 보관할 개수* — 작은 vector면 heap allocation 없음. Python `list` 와 동일하게 읽으면 됨.
- **`llvm::TypeSwitch`**: `dyn_cast` 체인을 깔끔하게 쓰는 helper. `TypeSwitch<Op*, LogicalResult>(op).Case<AddOp>([](auto op) {...}).Case<MulOp>(...)` 형태. Python의 match-case (`match op: case AddOp(): ...`) 와 같은 자리.
- **PIMPL / opaque type**: 큰 프로젝트는 implementation detail을 cpp로 숨김. 헤더에서 `class Impl;` 만 보이고 cpp에 본체. *깊게 안 봄*, 그냥 "여기는 implementation detail이다" 표시로 읽음.
- **`mlir::TypedValue<T>`**: `mlir::Value` 의 타입 안전 wrapper. `TypedValue<TensorType>` 이면 "tensor type임이 보장된 value". Stage 1의 `Value` 와 함께 글로서리에 추가.

**읽다가 막히는 C++** 이 있으면 Stage 1 Block 11의 자가 점검 5개 다시. 그 5개로 막히면 production code 의 70%는 안 풀린다.

---

## 진행 단위

### Block 1 — 클론 + README 정독 + 디렉토리 정찰

**할 일**
1. `~/dev/compiler-sources/Triton-to-tile-IR`에 클론. 이 repo 안에 넣지 않는다.
2. README 정독 (이미 한 번 봤어도 다시). 특히:
   - "ChangeList" 섹션 — Triton core 변경 목록과 cuda-tile backend 추가 항목
   - "Known functional issues" / "Known performance issues" — 기여 entry point 후보의 1차 소스
   - `ENABLE_TILE=1` flow + PTX fallback 경로
3. 디렉토리 지도 작성. 특히 `third_party/tileir/` 안에서 다음을 찾는다:
   - `TritonToCudaTile.*` (cpp + h)
   - `rewriteAssume.*`
   - `Passes.td` 또는 동등한 pass 선언
   - `BUILD` / `CMakeLists.txt` — 어떤 의존성이 걸려 있는지
4. **빌드는 강하게 선택**. CUDA 13.1 + Blackwell GPU 의존이 큼 — 코드 정독이 1순위. 환경이 맞으면 시도해도 좋지만 stage 진행을 막지 않는다.

**산출물**: README ChangeList 자기 말 요약 (5~7줄) + `third_party/tileir/` 디렉토리 지도.

---

### Block 2 — 변환 진입점 추적: 어디서 호출되나

**할 일**
1. `ENABLE_TILE=1` 이 켜졌을 때 default target이 어디서 cuda-tile로 바뀌는지 `driver.py` / `compiler.py` 에서 추적. Python side는 *호출 지점만* 보고 깊이 안 들어감.
2. C++ side: `TritonToCudaTile` pass가 어떤 pass manager / pipeline에서 등록되는지 찾는다.
3. 그 진입점이 받는 입력 IR이 *TTIR인지 TritonGPU인지* 확인. Stage 2에서 본 두 dialect 중 어느 쪽이 source인지가 분명해져야 함.

**산출물**: "Python 진입 → C++ pipeline → TritonToCudaTile pass" 호출 chain 4~6줄 메모. 입력 dialect 확정.

---

### Block 3 — `TritonToCudaTile.*` 골격 ★

**할 일**
1. `TritonToCudaTile.cpp` (또는 동등) 의 *상단* 만 읽는다 — include, namespace, pass 클래스 선언.
2. `runOnOperation()` 의 골격을 짚는다. Toy Ch5~7와 동일 구조일 가능성 높음:
   - `ConversionTarget target(...)` 설정
   - `TypeConverter typeConverter` 설정 (tensor → cuda-tile tile 타입 매핑)
   - `RewritePatternSet patterns(...)`
   - `populate*ConversionPatterns(...)` 호출 — *어디서_ 패턴을 모으는가
   - `applyPartialConversion` / `applyFullConversion` 둘 중 어느 쪽인가
3. `populate*` 함수 안에서 등록되는 OpConversionPattern 목록을 *이름만* 죽 적는다. 카테고리별로 묶어보면 Stage 2의 TTIR op 카테고리 / Stage 2.5의 cuda-tile op 카테고리와 어떻게 대응되는지 보임.

**산출물**: pass 골격 도식 1장 + 등록된 패턴 목록 (카테고리별 그룹).

---

### Block 4 — 대표 패턴 2~3개 줄 단위 정독

**할 일**
1. Block 3의 패턴 목록에서 *대표 2~3개* 고른다. 선정 기준:
   - 하나는 elementwise / 단순 op (dot보다 쉬운 것)
   - 하나는 `tt.dot` 또는 동등한 MMA 변환 — cuda-tile의 mma op과 매핑되어 핵심
   - 하나는 layout / memory 관련 (load/store 또는 layout conversion)
2. 각 패턴의 `matchAndRewrite` 를 *줄 단위로* 따라간다. 다음 4가지를 추적:
   - source op에서 어떤 정보를 뽑는가 (operand, attribute, type)
   - 그걸 cuda-tile op으로 어떻게 매핑하는가
   - layout / encoding 처리가 어디서 끼는가 (Stage 2의 TritonGPU encoding ↔ Stage 2.5의 cuda-tile layout)
   - rewriter API 사용 패턴 (`rewriter.replaceOpWithNewOp`, `rewriter.create`, type materialization 등)
3. 각 패턴에 대해 "TTIR side X → cuda-tile side Y, 매핑 규칙 한 줄" 형식으로 정리.

**산출물**: 3개 패턴의 줄 단위 주석 (자기 코드베이스 안에 사본 두지 않음 — 메모에 발췌만) + 매핑 규칙 표.

---

### Block 5 — `rewriteAssume.*` 와 TMA / occupancy specific 처리

**할 일**
1. `rewriteAssume.*` 가 무엇을 하는지 한 단락. assume op이 왜 별도 rewrite를 필요로 하는지 (TTIR / LLVM IR ↔ cuda-tile assume op의 차이).
2. TMA (Tensor Memory Accelerator) host API → cuda-tile device API 매핑이 어디서 이뤄지는지 *코드 위치만* 짚는다. 본격 정독은 안 함.
3. `occupancy` hint, `num_ctas`, `num_warps` 같은 cuda-tile-specific 설정이 conversion 안에서 어떻게 흘러가는지 (혹은 어디서 ignore 되는지) 확인.

**산출물**: `rewriteAssume` 한 단락 요약 + TMA 매핑 위치 한 줄 + occupancy/num_ctas 처리 위치 한 줄.

---

### Block 6 — 잠재적 기여 entry point 후보 추출 ★

**할 일**
1. README의 "Known functional issues" / "Known performance issues" / "Potential future solutions" 를 다시 읽고, Block 3~5에서 본 코드와 매칭. 각 항목에 대해:
   - 관련 코드가 어디 있나 (또는 *없음* — 새로 추가해야 할 영역인가)
   - 난이도 추정 (한 패턴 추가 / 새 pass / API 확장 중 어느 쪽)
2. 코드 안의 `TODO` / `FIXME` / `XXX` 주석을 grep해서 추가 후보 수집.
3. 후보 3~5개를 *난이도 낮은 순서*로 정렬해서 목록화. 각 후보에 대해:
   - 어떤 변경이 필요한가 (한 줄)
   - 무엇을 모르면 손댈 수 없는가 (선행 학습 항목)
   - upstream에 제안 형태로 낼 만한 것인가, 아니면 issue 단계인가

**산출물**: `notes/stage2_7-contribution-candidates.md` — 후보 목록. Stage 4에서 그 중 하나를 선택해서 실행으로 옮긴다.

---

### Block 7 — Stage 2.7 회고

**할 일**
1. `notes/stage2_7-triton-to-tile-deep-read.md` 종합 회고:
   - `TritonToCudaTile.*` 의 골격을 자기 말로 한 단락
   - 본 패턴 3개에서 *공통* 패턴 추출 (대부분의 conversion pattern이 같은 구조를 따른다는 confirmation)
   - 본 패턴 3개에서 *차이* 가 있는 부분 (특히 layout / type conversion 처리)
2. Stage 2 (TTIR source) + Stage 2.5 (cuda-tile target) + Stage 2.7 (production conversion) 세 stage 입력이 어떻게 합쳐졌는지 한 단락.
3. Stage 3 (자기 손으로 mini conversion pass) 에서 *어떤 구조를 따라야 하는지* 결정 사항 적기 — Stage 3의 직접 입력이 됨.

**산출물**: `stage2_7-triton-to-tile-deep-read.md` — Stage 3 진입 직전 production conversion pass 요약 + Stage 3 디자인 입력.

---

## Stage 2.7 종료 조건

- `Triton-to-tile-IR` repo가 클론되어 있고 디렉토리 지도 + ChangeList 자기 말 요약이 있다.
- `TritonToCudaTile.*` 의 pass 골격을 자기 말로 그릴 수 있다.
- 대표 OpConversionPattern 2~3개를 줄 단위로 따라가서 매핑 규칙을 한 줄씩 적었다.
- 잠재적 기여 entry point 후보가 3~5개 목록으로 있다.
- Stage 3에서 따라할 *구조*가 결정되어 있다.

이 다섯이 되면 Stage 3 진입. 그때 자기 손으로 짤 mini conversion pass의 *모양*은 이미 있는 셈.

---

## 의도적으로 빼는 것

- **레포 전체 빌드 / 실행 의무**. CUDA 13.1 + Blackwell GPU 의존성이 큼. 가능하면 좋지만 stage 진행을 막지 않는다.
- **Triton core 변경 사항 추적 깊이**. README ChangeList 한 번 읽기로 충분. v3.6 core diff를 따라가지 않는다.
- **성능 튜닝 / 벤치마크**. Stage 2.7은 *어디를 건드릴 수 있는가*를 보는 게 목적. occupancy 튜닝 가이드는 별도 영역.
- **Helion 사용법 / TileIR backend 사용자 가이드**. README의 Helion Hackathon 섹션은 *사용자* 관점이라 학습 대상 아님.
- **PTX / tileiras 같은 cuda-tile 하위**. MLIR 밖이라 외부.
- **`TritonToCudaTile` *대신* TritonToTritonGPU 깊게**. 그건 Stage 2에서 얕게 본 걸로 충분. 이번 stage의 본 대상은 cuda-tile 변환.
