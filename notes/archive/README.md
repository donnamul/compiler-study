# archive

`notes/archive/`는 더 이상 활성 로드맵이 아닌 옛 plan 파일을 보관한다.

현재 활성 plan은 다음 4개:

- `notes/full_plan_for compiler_study.md` — Stage 0~4 마스터
- `notes/stage1-toy-mlir.md` — Toy Tutorial + C++ 보강
- `notes/stage2-iree-deep-read.md` — IREE 한 개를 깊게
- `notes/stage3-custom-dialect.md` — Custom dialect + Linalg lowering + Bufferization

여기에 보관된 파일은 *참고용으로만* 본다. 일정/블록 번호/체크리스트는 활성 plan을 따른다.

## 보관 사유

| 파일 | 보관 사유 |
|------|----------|
| `phase0-detailed-plan.md` | Phase 0은 산출물 기준으로 거의 완료됨. 1~16 Block 구조는 활성 plan에서 Stage 0 (완료) 한 줄로 흡수. |
| `phase1-detailed-plan.md` | 강의 PDF 22개 의무 병행, Kaleidoscope 선택 참고, Triton 후반 확장, 3개 프로젝트 동시 비교, 16주 데드라인을 모두 가정했다. 현재 plan의 전제(컴파일러 어느 정도 알고 있음, C++ 보강 필요, MLIR 자체 익히기가 목표, Legato가 Inductor 자리라 Torch-MLIR 경로 직접 매핑 안 됨)와 맞지 않아 활성에서 제외. |
