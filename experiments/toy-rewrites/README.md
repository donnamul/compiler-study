# toy-rewrites

Stage 1 Block 5 산출물 — Toy Ch3에 canonicalization 패턴 `SimplifyMulByOne`
(`mul(x, 1) → x`)을 직접 추가한 변경분 + FileCheck 테스트.

작업은 `~/dev/compiler-sources/llvm-project/mlir/examples/toy/Ch3/`에서 했고,
이 repo에는 *변경 diff*와 *테스트*만 보관한다 (llvm-project는 sibling, 체크인 X).

## mul-by-one.patch

`x * 1`(과 commutative인 `1 * x`)에서 `toy.mul`을 지우는 canonicalization 패턴. 건드린 파일 2개:

| 파일 | 무엇을 |
|------|--------|
| `include/toy/Ops.td` | `MulOp`에 `let hasCanonicalizer = 1;` — `MulOp::getCanonicalizationPatterns` 선언을 자동 생성 |
| `mlir/ToyCombine.cpp` | `SimplifyMulByOne` 패턴(`OpRewritePattern<MulOp>`) 정의 + `getCanonicalizationPatterns`에 등록 |

**핵심 로직**: 두 operand 중 defining op이 `ConstantOp`이고 그 값이 **splat 1.0**이면,
반대쪽 operand로 `replaceOp`. `getSplatValue` 전에 **`isSplat()` 가드** 필수 —
non-splat 상수(`[[1,2],[3,4]]`)에 바로 호출하면 assertion으로 죽는다.

## 적용 방법

```bash
cd ~/dev/compiler-sources/llvm-project
git apply ~/dev/compiler-study/experiments/toy-rewrites/mul-by-one.patch
cmake --build build -t toyc-ch3
```

## 동작 확인

```bash
TOYC=~/dev/compiler-sources/llvm-project/build/bin/toyc-ch3
$TOYC mul_by_one.toy -emit=mlir       # before: toy.mul 있음
$TOYC mul_by_one.toy -emit=mlir -opt  # after:  toy.return %arg0 (mul 소멸)
```

| 입력 | `-opt` 결과 |
|------|-------------|
| `a * 1` | `toy.return %arg0` (mul 소멸) |
| `1 * a` | `toy.return %arg0` (commutative) |
| `a * [[1,2],[3,4]]` | 유지 — splat 아니라 매칭 안 됨 (크래시 없음) |

## FileCheck

```bash
cmake --build build -t FileCheck   # 1회
FC=~/dev/compiler-sources/llvm-project/build/bin/FileCheck
$TOYC mul_by_one.toy -emit=mlir -opt 2>&1 | $FC mul_by_one.toy   # PASS (exit 0)
```

`mul_by_one.toy` 안의 `# RUN:` 줄이 lit 스위트에서 쓰이는 표준 형식.
여기서는 lit 없이 파이프로 직접 실행 (`check-mlir` 전체는 안 돌림).
