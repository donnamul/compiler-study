# toy-custom-ops

Stage 1 Block 3 산출물 — Toy Ch2에 `toy.neg` op을 직접 추가한 변경분.

작업은 `~/dev/compiler-sources/llvm-project/mlir/examples/toy/Ch2/`에서 했고,
이 repo에는 *변경 diff*만 보관한다 (llvm-project는 sibling workspace, 여기 체크인하지 않음).

## neg-op.patch

`toy.neg` (element-wise negation) op을 추가하는 패치. 건드린 파일 3개:

| 파일 | 무엇을 |
|------|--------|
| `include/toy/Ops.td` | `NegOp` ODS 정의 (unary, `F64Tensor` 입력/출력). `TransposeOp` 템플릿을 변용하되 `hasVerifier`는 뺌 — neg는 shape 안 바꾸는 element-wise라 별도 verifier 불필요 |
| `mlir/Dialect.cpp` | `NegOp::build` 몸체 — 결과를 `UnrankedTensorType`(f64)로 두고 operand 하나 추가. Ch2엔 shape inference가 없어 unranked가 맞음 (transpose와 동일 전략) |
| `mlir/MLIRGen.cpp` | `mlirGen(CallExprAST&)`의 `transpose` 분기 옆에 `neg` 분기 추가. arg 1개 검사 후 `NegOp::create` |

## 적용 방법

```bash
cd ~/dev/compiler-sources/llvm-project
git apply ~/dev/compiler-study/experiments/toy-custom-ops/neg-op.patch
cmake --build build -t toyc-ch2
```

## 동작 확인

```toy
def main() {
  var a = [[1, 2], [3, 4]];
  var b = neg(a);
  print(b);
}
```

```
$ toyc-ch2 test_neg.toy -emit=mlir
module {
  toy.func @main() {
    %0 = toy.constant dense<[[1.0, 2.0], [3.0, 4.0]]> : tensor<2x2xf64>
    %1 = toy.neg(%0 : tensor<2x2xf64>) to tensor<*xf64>
    toy.print %1 : tensor<*xf64>
    toy.return
  }
}
```

`neg(a, a)`처럼 인자 2개를 주면 MLIRGen 단계에서 에러:
`error: MLIR codegen encountered an error: toy.neg does not accept multiple arguments`
