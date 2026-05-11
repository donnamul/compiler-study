# Compiler Study 로드맵 — Stage 0~4 (v5, 2026-05-11 재정렬)

> **목표**: MLIR을 익힌다. 그게 전부다.
> **전제**:
> - 컴파일러 이론은 어느 정도 안다 (lexer / parser / SSA / CFG / data-flow). 강의 자료는 의무 트랙이 아니라 *막힐 때 발췌*.
> - C++은 약하다. 그래서 Stage 1 전반에 C++ 보강 트랙을 평행으로 둔다.
> - HyperAccel에서 LPU용 컴파일러를 만든다. Legato는 PyTorch stack에서 Inductor 자리에 들어가서 FX graph를 받아 자체 MLIR IR로 내린다. 따라서 `torch-mlir`의 `torch` dialect 경유 경로는 직접 매핑되지 않는다 — 별도 stage로 안 둔다.
> - Triton 내부, `torch.compile` 내부, GPU 커널 포팅(Helion, CuTe, ROCm 등)은 이미 깊이 본 영역이라 학습 트랙에서 제외.
> - 16주 데드라인 / 첫 PR / 블로그 N편 같은 외부 산출물 강제 없음. 학습이 끝났을 때 어떤 상태인지가 기준.

---

## v4 → v5 변경 요약

| 영역 | v4 (이전) | v5 (현재) |
|------|----------|-----------|
| Phase 수 | 0~5 (16주) | Stage 0~4 (시간 라벨 없음) |
| 강의 PDF | 22개 의무 병행 | 막힐 때 발췌 |
| Kaleidoscope | 선택 참고 | 제외 |
| Triton 트랙 | Phase 1 후반 + Phase 4 심화 | 제외 (이미 본 영역) |
| Production MLIR | StableHLO + IREE + Triton + cuTile 동시 비교 | IREE 단일 깊이 |
| Torch-MLIR | 암묵적 가정 | 제외 (Legato가 Inductor 자리) |
| Custom dialect | Phase 2 짧게 | Stage 3 ★ 핵심으로 승격 |
| Bufferization | 9주차 가볍게 | Stage 3에 본격 |
| C++ 보강 | LLVM 패턴 표 한 장 | Stage 1 전반에 평행 트랙 |
| 첫 PR / 블로그 | Phase 5 의무 | 제외 (관심 생기면 Stage 4 이후) |

---

## Stage 0 — MLIR 환경 + 기초 감각  [거의 완료]

**상태**: 빌드 성공, `mlir-opt` 동작 확인, `experiments/mlir-basics/` 6개 (`hello`, `tensor_ops`, `control_flow`, `memref_ops`, `regions`, `blocks`), `notes/week01.md`에 LangRef + Toy Ch1 진입 메모 정리됨.

**남은 일**: 별도 없음. Stage 1로 진입하면서 C++ 보강 트랙을 시작.

**상세 plan**: 없음. 옛 `phase0-detailed-plan.md`는 `archive/`에 보관.

---

## Stage 1 — Toy Tutorial로 MLIR 핵심 메커니즘 익히기 + C++ 보강

**무엇을 익히나**:
- `.td` (ODS/TableGen)로 op 정의하고 TableGen이 C++ 코드를 생성하는 흐름
- fold / canonicalization / pattern rewrite
- Dialect Conversion (ConversionTarget / Pattern / TypeConverter — 가장 중요)
- LLVM dialect로의 lowering chain
- LLVM 스타일 C++ 패턴: `isa/cast/dyn_cast`, `SmallVector`, `OpRewritePattern`, Builder, CRTP

**진행 단위**: Toy Ch1 → Ch7. 각 Chapter당 1~3 block.

**C++ 보강 트랙**: 각 block에서 Toy 코드를 읽으면서 만나는 패턴을 Python 대응으로 메모. 분리된 학습 시간이 아니라 *Toy 코드를 읽는 행위 자체*가 C++ 공부.

**직접 구현 (최소)**:
- `toy.neg` op 추가 (Ops.td + MLIRGen.cpp + lowering)
- rewrite pattern 1개만 직접 (`add(x, 0) → x` 같은 거)

3개 의무 안 둠. 하나 제대로가 셋 대충보다 낫다.

**산출물**: `notes/week03.md` ~ `notes/week05.md`, `experiments/toy-custom-ops/`, `experiments/toy-rewrites/`.

**상세 plan**: `notes/stage1-toy-mlir.md`

---

## Stage 2 — IREE 한 개를 깊게 읽기

**왜 IREE인가**:
- accelerator backend 구조(dispatch 형성, target dialect, bufferization)가 HyperAccel LPU 작업과 *구조적으로* 가장 가까움.
- XLA는 MLIR 비중이 부분적이고 규모가 너무 큼.
- StableHLO는 op set 디자인 관점에선 좋지만 *백엔드 구조*는 IREE가 봐야 함.

**무엇을 본다**:
- StableHLO/TOSA → Linalg lowering 한 경로를 trace
- IREE의 dispatch region 형성
- bufferization 진입 지점
- target dialect (Vulkan / LLVM-CPU 중 하나만) lowering 일부

**금지**:
- "IREE 코드베이스 전부 이해" 같은 욕심. 한 op (예: `linalg.matmul` 또는 `stablehlo.dot_general`) 가 LLVM IR까지 내려가는 경로 *하나*만 따라가는 게 목표.
- StableHLO 트랙을 의무로 끼지 않는다. op 정의 비교가 필요해지면 그때 1회만 발췌.

**산출물**: `notes/stage2-iree-trace.md` — 한 op의 lowering chain을 IR dump를 끼워서 단계별로 정리. dialect conversion 지점을 표시한 도식 1장.

**상세 plan**: `notes/stage2-iree-deep-read.md`

---

## Stage 3 — Custom Dialect + Linalg Lowering + Bufferization  ★ 핵심

**왜 핵심인가**: 너 일이 LPU dialect 디자인 + lowering이다. Stage 1~2가 모두 이 stage를 위한 준비.

**무엇을 만든다**:
- out-of-tree mini dialect (Toy 빼고 처음부터, ODS로 op 3~5개)
  - 예시: `chip.matmul`, `chip.elementwise`, `chip.layout_convert`
  - verifier, type inference, custom assembly format 한 번씩 다뤄봄
- 이 dialect → Linalg / arith / tensor / memref 로 가는 lowering pass 1개
- bufferization pass를 끼워 tensor → memref 변환을 직접 관찰

**MLIR LangRef / 공식 문서를 다시 깊게**:
- Op interface, Traits (`Pure`, `SameOperandsAndResultType`, etc.)
- Dialect Conversion 깊이 (TypeConverter, materialization, 1:N conversion)
- Bufferization (One-Shot Bufferize, BufferizableOpInterface)

**산출물**:
- `experiments/mini-dialect/` — out-of-tree dialect 소스 (CMake 포함)
- `notes/stage3-custom-dialect.md` 내부의 회고 메모

**상세 plan**: `notes/stage3-custom-dialect.md`

---

## Stage 4 — 회고 + 다음 선택

Stage 1~3을 끝낸 시점에서:
- MLIR을 자기 말로 설명할 수 있는가
- 새 dialect를 설계할 때 어떤 결정을 먼저 내려야 하는지 감이 잡혔는가
- production MLIR 코드를 읽을 때 *예측 가능한* 부분이 50% 이상인가

이 셋 중 약한 게 있으면 거기를 보강.

남는 관심사:
- OSS 기여 (MLIR upstream `good first issue`, IREE `documentation`, StableHLO `RFC`)
- 블로그/발표
- Polyhedral / Affine dialect / Linalg transform 깊게
- XLA / 다른 production compiler 비교 (이 시점이면 비교가 의미 있음)

이들은 *원하면* 한다. 의무 아님.

---

## 활성 plan 파일 맵

| 파일 | 용도 |
|------|------|
| `notes/full_plan_for compiler_study.md` (이 파일) | Stage 0~4 마스터 |
| `notes/stage1-toy-mlir.md` | Stage 1 상세 |
| `notes/stage2-iree-deep-read.md` | Stage 2 상세 |
| `notes/stage3-custom-dialect.md` | Stage 3 상세 |
| `notes/week01.md` | Stage 0 학습 로그 (LangRef + Toy Ch1 진입) |
| `notes/week02.md` | 복귀 메모 + Stage 1 진입 직전 |
| `notes/week03.md~` | Stage 1 진행 중 학습 로그 |
| `notes/archive/` | 옛 phase plan 보관소 |

---

## 학습 원칙 (v4에서 유지)

- 한 session에서 하나는 남긴다: 노트, 다이어그램, 작은 실험, 비교 메모 중 하나.
- 외부 자료는 인덱싱하지 말고 *내 말로 다시 적기*가 학습.
- 상위 source(`llvm-project`, `iree`)는 *이 repo에 체크아웃하지 않는다* — `~/dev/compiler-sources/`에 둔다.
- 헷갈리는 게 나오면 강의 PDF에서 15~30분 발췌. 챕터 단위로 끝내려 하지 않는다.
- 블록 단위 진행. 시간 라벨/데드라인은 없다. 한 블록 끝나면 다음 블록.
