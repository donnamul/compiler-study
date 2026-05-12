# Compiler Study 로드맵 — Stage 0~4 (v5.2, 2026-05-12)

> v5.1 → v5.2: 학습의 *종착점*을 `triton-lang/Triton-to-tile-IR` OSS 기여로 재정렬. Stage 2(IREE deep-read)를 강등하고, 변환 경로의 양 끝(TTIR source / cuda-tile target)과 production conversion pass 자체를 핵심 트랙으로 승격.

> **목표**: MLIR을 익혀서 `triton-lang/Triton-to-tile-IR` (TTIR → CUDA Tile IR 변환 backend 인큐베이터)에 기여할 수 있는 상태까지 간다.
> **전제**:
> - 컴파일러 이론은 어느 정도 안다 (lexer / parser / SSA / CFG / data-flow). 강의 자료는 의무 트랙이 아니라 *막힐 때 발췌*.
> - C++은 약하다. 그래서 Stage 1 전반에 C++ 보강 트랙을 평행으로 둔다.
> - 본업은 HyperAccel LPU 컴파일러지만, 이 로드맵의 *종착점*은 OSS triton-to-tile-IR 기여로 분리한다. LPU dialect 작업은 부수적 동기지 학습 plan을 지배하지 않는다.
> - Legato는 PyTorch stack에서 Inductor 자리에 들어가 FX graph를 받아 자체 MLIR IR로 내린다. `torch-mlir`의 `torch` dialect 경로는 직접 매핑되지 않아 stage 밖이다.
> - Triton 관련 학습은 **kernel writer 관점**(autotuning, kernel porting, Helion/CuTe 사용)은 이미 본 영역이라 제외, **IR 내부 관점**(TTIR/TritonGPU dialect, conversion pass)은 *핵심 학습 대상*. 이 둘은 같지 않다.
> - 16주 데드라인 / 의무 블로그 N편 같은 외부 산출물 강제 없음. 학습 종료 시점의 *상태*가 기준.

---

## v5.1 → v5.2 변경 요약

| 영역 | v5.1 (이전) | v5.2 (현재) |
|------|-------------|-------------|
| 학습 종착점 | "MLIR을 익힌다" + LPU dialect 작업 prerequisite | **`triton-lang/Triton-to-tile-IR` 기여**가 가능한 상태 |
| Stage 2 | IREE 단일 깊이 (backend pipeline 관점) | **TTIR / TritonGPU source dialect 이해**로 교체. IREE는 선택 보조 |
| Stage 2.5 | NVIDIA/cuda-tile (dialect 디자인 관점) | 동일 — 다만 *변환의 target dialect*로 재맥락화 |
| Stage 2.7 (신규) | — | `Triton-to-tile-IR` 레포의 `TritonToCudaTile.*` + `rewriteAssume.*` production conversion pass 정독 |
| Stage 3 | out-of-tree mini dialect 만들기 | out-of-tree **mini dialect-to-dialect conversion pass** (A→B 변환 자체가 중심) |
| Triton 내부 | "제외" | kernel writer 관점만 제외, IR 내부 관점은 학습 대상 |
| HyperAccel LPU | plan 정당화의 핵심 동기 | 부수적 동기로 격하 |

---

## Stage 구조 한 눈

```
Stage 0    MLIR 빌드 + LangRef + .mlir 6개                                  [완료]
Stage 1    Toy Ch1~7 + C++ 보강 트랙 — Dialect Conversion 메커니즘 ★
Stage 2    Triton TTIR / TritonGPU dialect 이해 (source side)
Stage 2.5  NVIDIA/cuda-tile dialect 이해 (target side)
Stage 2.7  Triton-to-tile-IR 레포의 conversion pass 정독 (production side)  ★
Stage 3    out-of-tree mini conversion pass (A→B)                           ★
Stage 4    회고 + triton-to-tile-IR 기여 entry point 탐색
```

전체 흐름: **양 끝 dialect 이해 → production 변환 코드 정독 → 자기 손으로 작은 변환 pass 한 개 → upstream entry point**.

IREE deep-read는 v5.2에서 **선택 보조**로 강등. "production backend pipeline 전체 관점"이 필요해질 때만 발췌. 상세 plan 파일 `notes/stage2-iree-deep-read.md`는 archive하지 않고 reference로 유지하되 활성 트랙은 아니다.

---

## Stage 0 — MLIR 환경 + 기초 감각  [거의 완료]

**상태**: 빌드 성공, `mlir-opt` 동작 확인, `experiments/mlir-basics/` 6개 (`hello`, `tensor_ops`, `control_flow`, `memref_ops`, `regions`, `blocks`), `notes/week01.md`에 LangRef + Toy Ch1 진입 메모 정리됨.

**남은 일**: 별도 없음.

---

## Stage 1 — Toy Tutorial + C++ 보강  ★ Dialect Conversion 메커니즘 학습

**왜 핵심인가**: triton-to-tile-IR의 `TritonToCudaTile.*`는 **MLIR Dialect Conversion**(ConversionTarget / Pattern / TypeConverter) 그 자체다. Toy Ch5~7에서 이 메커니즘을 손에 익히지 않으면 Stage 2.7에서 production 코드를 읽어도 골격이 안 보인다.

**무엇을 익히나**:
- `.td` (ODS/TableGen)로 op 정의하고 TableGen이 C++ 코드를 생성하는 흐름
- fold / canonicalization / pattern rewrite
- **Dialect Conversion** (ConversionTarget / Pattern / TypeConverter — Stage 2.7로 직접 연결)
- LLVM dialect로의 lowering chain
- LLVM 스타일 C++ 패턴: `isa/cast/dyn_cast`, `SmallVector`, `OpRewritePattern`, Builder, CRTP

**진행 단위**: Toy Ch1 → Ch7. 각 Chapter당 1~3 block.

**C++ 보강 트랙**: Toy 코드를 읽으면서 만나는 패턴을 Python 대응으로 메모. 분리된 학습 시간이 아니라 *Toy 코드 읽기 자체*가 C++ 공부.

**직접 구현 (최소)**:
- `toy.neg` op 추가 (Ops.td + MLIRGen.cpp + lowering)
- rewrite pattern 1개 직접 (`add(x, 0) → x` 같은 것)

**산출물**: `notes/week03.md` ~ `notes/week05.md`, `experiments/toy-custom-ops/`, `experiments/toy-rewrites/`.

**상세 plan**: `notes/stage1-toy-mlir.md`

---

## Stage 2 — Triton TTIR / TritonGPU dialect 이해 (source side)

**왜 IREE가 아니라 이쪽인가**: 학습 종착점이 triton-to-tile-IR 기여라면, 변환의 **source dialect**를 모르고는 conversion pass 변경/추가가 불가능. IREE는 *general* backend pipeline 경험으로는 가치 있지만 직접 path는 아님.

**무엇을 본다**:
- `triton/include/triton/Dialect/Triton/IR/` — TTIR op 정의 (`Dialect.td`, `Ops.td`, `Types.td`)
- `triton/include/triton/Dialect/TritonGPU/IR/` — TritonGPU layout encoding(blocked, mma, dot_operand 등) ★
- TTIR과 TritonGPU 두 layer의 관계 (어디서 어디로 lowering 되는지)
- conversion 진입점 한두 곳 살짝 — 본격적 정독은 Stage 2.7

**금지**:
- Triton "전부" 이해. op 카테고리당 대표 1개 깊이만.
- kernel writer 관점(autotuning, num_warps 튜닝, 실제 kernel 짜기). 이미 본 영역.
- `triton/python/` 쪽 DSL frontend. IR 내부와 분리.

**산출물**: `notes/stage2-ttir-source.md` — TTIR / TritonGPU 주요 op·type·attribute 표 1장, layout encoding 도식 1장.

**상세 plan**: (신규 작성 필요 — Stage 2 진입 직전에 `notes/stage2-ttir-source.md` 작성)

**IREE deep-read**: 선택 보조. `notes/stage2-iree-deep-read.md` 파일은 reference로 남겨두지만 활성 트랙 아님.

---

## Stage 2.5 — NVIDIA/cuda-tile dialect 이해 (target side)

**왜 cuda-tile인가**:
- triton-to-tile-IR의 **target dialect**가 정확히 NVIDIA의 CUDA Tile IR.
- 2025-11 공개된 ~1 MB짜리 MLIR-only dialect. **production quality + 한 사람이 거의 다 이해 가능한 사이즈**의 흔치 않은 조합.

**무엇을 본다**:
- `Dialect.td` + `Ops.td` 훑고 op 카테고리 분류 (compute / memory / layout / control)
- `Types.td` + `AttrDefs.td` — tile 타입 정의와 layout/memory encoding ★
- `Interfaces.td` — op interface 설계
- `OpsCanonicalization.td` — fold / rewrite 패턴 한두 개
- `Passes.td` 목록 + pass 한 개의 골격
- (선택) `BytecodeOpcodes.td` — IR 직렬화

**금지**:
- cuda-tile의 모든 op 이해. 카테고리당 1개 깊이만.
- kernel writing 관점. 이미 본 영역.
- PTX / runtime / tileiras. MLIR 밖.

**산출물**: `notes/stage2_5-cuda-tile-design-notes.md` — Stage 2.7 진입 직전 디자인 결정 표 (cuda-tile의 결정 + 그 이유 + 자기 말로 정리).

**상세 plan**: `notes/stage2_5-cuda-tile.md`

---

## Stage 2.7 — Triton-to-tile-IR production conversion pass 정독  ★ 핵심

**왜 핵심인가**: 학습 종착점이 이 레포에 기여하는 것. Stage 1~2.5는 모두 이 stage의 코드를 *예측 가능하게* 읽기 위한 준비다.

**대상 레포**: `https://github.com/triton-lang/Triton-to-tile-IR` — TTIR → CUDA Tile IR 변환 backend 인큐베이터.

**무엇을 본다**:
- `third_party/tileir/` 디렉토리 구조 정찰 (build, lib, include 분리 확인)
- **`TritonToCudaTile.*`** — TTIR을 cuda-tile로 내리는 메인 conversion pass ★
- **`rewriteAssume.*`** — assume op rewriting pass
- conversion entry point가 어디서 호출되는지 (`compiler.py`, `driver.py` 진입점)
- `ENABLE_TILE=1` flow와 NVIDIA PTX fallback 경로의 분기
- TMA, occupancy hint 같은 cuda-tile-specific 처리가 어디서 들어가는지

**금지**:
- 레포 전체 빌드/실행 욕심. CUDA 13.1 + Blackwell GPU 의존성이 크다 — 코드 정독이 1순위, 빌드는 가능하면 선택.
- Triton 본체의 v3.6 변경 사항 추적. core file 변경 목록(driver.py, compiler.py, jit.py)은 *어떤 hook이 걸리는지*만 확인하면 됨.
- 성능 튜닝/벤치마크. Stage 2.7은 *어디를 건드릴 수 있는가*를 보는 게 목적.

**산출물**: `notes/stage2_7-triton-to-tile-deep-read.md` — `TritonToCudaTile.*` 안의 패턴 매칭 구조 도식, 미해결/TODO 영역 목록(=잠재적 기여 entry point), 자기 말 요약.

**상세 plan**: (신규 작성 필요 — Stage 2.7 진입 직전에 `notes/stage2_7-triton-to-tile.md` 작성)

---

## Stage 3 — out-of-tree mini conversion pass

**v5.2 reframe**: v5.1의 "out-of-tree mini dialect"가 아니라 **mini dialect-to-dialect conversion pass**가 중심. dialect 자체는 보조 도구.

**무엇을 만든다**:
- 아주 작은 source dialect `chip.matmul` / `chip.elementwise` (3개 정도)
- 아주 작은 target dialect `tile.mma` / `tile.elementwise` (2~3개, cuda-tile의 microcosm)
- **`ChipToTile` conversion pass** — TritonToCudaTile의 *축소 모델*. ConversionTarget, OpConversionPattern, TypeConverter를 자기 손으로 다 짜본다.
- bufferization 진입(One-Shot Bufferize)으로 tensor → memref 변환 한 번 끼우기

**MLIR LangRef / 공식 문서를 다시 깊게**:
- Op interface, Traits (`Pure`, `SameOperandsAndResultType`, etc.)
- **Dialect Conversion 깊이** (TypeConverter, materialization, 1:N conversion) — Stage 2.7에서 본 패턴을 자기 손으로 재현
- Bufferization (One-Shot Bufferize, BufferizableOpInterface)

**산출물**:
- `experiments/mini-conversion/` — out-of-tree dialect + conversion pass 소스 (CMake 포함)
- `notes/stage3-custom-dialect.md` 내부의 회고 메모

**상세 plan**: `notes/stage3-custom-dialect.md` (v5.2 reframe 반영해서 재작성 필요)

---

## Stage 4 — 회고 + triton-to-tile-IR 기여 entry point

Stage 1~3을 끝낸 시점에서:
- triton-to-tile-IR의 `TritonToCudaTile.*` 안에서 *예측 가능한* 부분이 절반 이상인가
- 새 conversion pattern을 추가하라고 했을 때 어디부터 손댈지 그림이 그려지는가
- TTIR side / cuda-tile side 양쪽에서 op 한 개씩 골라 변환 규칙을 자기 말로 설명할 수 있는가

위 셋 중 약한 게 있으면 거기 보강. 충분히 자리 잡혔으면:

- `Triton-to-tile-IR` 레포의 **good-first 영역 탐색** — Known functional issues / Known performance issues / Potential future solutions 섹션은 시작점이 되어줄 후보.
- Triton 본체 `good first issue` 라벨.
- (관심 생기면) 블로그/발표, Polyhedral / Affine, XLA 비교 — *원하면* 한다. 의무 아님.

---

## 활성 plan 파일 맵

| 파일 | 용도 | 상태 |
|------|------|------|
| `notes/full_plan_for compiler_study.md` (이 파일) | Stage 0~4 마스터 | v5.2 |
| `notes/stage1-toy-mlir.md` | Stage 1 상세 | 활성 |
| `notes/stage2-ttir-source.md` | Stage 2 상세 (TTIR / TritonGPU) | 활성 |
| `notes/stage2-iree-deep-read.md` | (구) Stage 2 IREE deep-read | **참고용**, 활성 트랙 아님 |
| `notes/stage2_5-cuda-tile.md` | Stage 2.5 상세 | 활성 (target side 관점으로 재맥락화) |
| `notes/stage2_7-triton-to-tile.md` | Stage 2.7 상세 (production conversion pass) | 활성 |
| `notes/stage3-custom-dialect.md` | Stage 3 상세 | 활성 (v5.2 reframe 반영, mini conversion pass 중심) |
| `notes/week01.md` | Stage 0 학습 로그 | 완료 |
| `notes/week02.md` | 복귀 메모 + Stage 1 진입 직전 | 완료 |
| `notes/week03.md~` | Stage 1 진행 중 학습 로그 | 진행 |
| `notes/archive/` | 옛 phase plan 보관소 | 동결 |

---

## 학습 원칙 (v4에서 유지)

- 한 session에서 하나는 남긴다: 노트, 다이어그램, 작은 실험, 비교 메모 중 하나.
- 외부 자료는 인덱싱하지 말고 *내 말로 다시 적기*가 학습.
- 상위 source(`llvm-project`, `triton`, `Triton-to-tile-IR`, `cuda-tile`, `iree`)는 *이 repo에 체크아웃하지 않는다* — `~/dev/compiler-sources/`에 둔다.
- 헷갈리는 게 나오면 강의 PDF에서 15~30분 발췌. 챕터 단위로 끝내려 하지 않는다.
- 블록 단위 진행. 시간 라벨/데드라인은 없다. 한 블록 끝나면 다음 블록.
