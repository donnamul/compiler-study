# Week 01

## Environment

- OS: macOS 15.7 arm64
- Compiler: Apple clang 17
- Python: 3.9.6
- Tools: `cmake`, `ninja`, `ccache`

---

## 2026-03-21(~B4)

### MLIR LangRef 첫 독해

ref: https://mlir.llvm.org/docs/LangRef/

#### 핵심 구조 개념

containment hierarchy: `Operation → Region → Block → Operation`

##### Phase 0용 빠른 요약

- `Dialect`: MLIR 확장의 단위. op / type / attribute를 namespace처럼 묶는다.
- `Operation`: MLIR의 기본 단위. operand/result/attribute/type을 가지고 필요하면 region/successor도 가진다.
- `Block`: 순서 있는 operation 리스트. SSACFG region에서는 basic block처럼 읽고 마지막은 terminator여야 한다.
- `Region`: ordered list of blocks. 의미는 region을 가진 operation이 정한다.
- `Value`: SSA 값. source는 operation result 또는 block argument뿐이다.
- `Attribute`: SSA value가 아닌 정적 constant data. op에 붙는 key-value 정보.

---

##### Operation

MLIR 의미론의 기본 단위. 아래 필드를 가진다:

| 필드 | 설명 |
|---|---|
| result | op이 생산하는 SSA value (0개 이상) |
| operand | op이 소비하는 SSA value |
| attribute | SSA value가 아닌 정적 constant data. op에 붙는 key-value 정보 |
| type | operand/result에 붙는 타입 정보 |
| region | 중첩 body가 필요한 op에만 존재 |
| successor | 분기 대상 block (terminator op에만) |

```mlir
// result 1개, operand 2개
%sum = arith.addi %a, %b : i32

// result 없음, operand 여러 개 (`%val`, `%buf`, `%i`)
memref.store %val, %buf[%i] : memref<8xi32>

// region을 가지는 op — scf.for 자체가 하나의 operation
%result = scf.for %i = %lo to %hi step %step
          iter_args(%acc = %init) -> f32 {
  // ... body는 이 region 안의 block
  scf.yield %next : f32
}
```

---

##### Block

순서 있는 operation 리스트. 두 가지 요소로 구성된다:

- **block argument**: block 헤더에 선언된 SSA value (phi 역할, 아래 별도 설명)
- **operation list**: 마지막은 반드시 **terminator**여야 함

```mlir
// ^bb0 : block 이름 (^로 시작)
// (%arg0: i32, %arg1: i32) : block argument
^bb0(%arg0: i32, %arg1: i32):
  %sum = arith.addi %arg0, %arg1 : i32
  return %sum : i32          // terminator
```

SSACFG region에서 terminator가 없으면 ill-formed. `return`, `scf.yield`, `cf.br`, `cf.cond_br` 등이 terminator.

**Entry block 제약**: SSACFG region의 첫 번째 block(entry block)으로는 `cf.br`로 jump할 수 없다.
Entry block은 predecessor가 없어야 하며, 그 argument는 region 외부에서 주입된다
(= `func.func`의 경우 함수 인자가 entry block argument로 들어온다).

```mlir
func.func @foo(%a: i32, %b: i32) -> i32 {
//                                         ↑ entry block argument = %a, %b
  cf.br ^entry(%a, %b : i32, i32)  // ERROR: entry block은 branch 대상이 될 수 없음
^entry(%x: i32, %y: i32):
  ...
}
```

---

##### Region

operation 안에만 존재하는 block들의 묶음. 두 종류가 있다:

| 종류 | 설명 | 예 |
|---|---|---|
| **SSACFG region** | block 간 control flow 허용. 첫 block = entry. | `func.func` body |
| **Graph region** | block 간 순서/흐름 없음. 대부분 block 하나. | `module`, `hw.module` |

```mlir
func.func @example(%x: i32) -> i32 {
  // 여기서부터가 func.func op의 region
  // 첫 번째 block이 entry block — %x는 이 block의 argument
  %c1 = arith.constant 1 : i32
  %r  = arith.addi %x, %c1 : i32
  return %r : i32
  // region 끝
}
```

`scf.for` 처럼 op이 region을 가지면 → 그 op은 단순 연산이 아니라 **계층 구조**를 표현한다.

---

##### Value / SSA

`Value`의 source는 정확히 두 가지뿐:

1. **operation result** — `%sum = arith.addi ...` 에서 `%sum`
2. **block argument** — `^bb(%arg: i32):` 에서 `%arg`

```mlir
func.func @ssa_example(%a: i32) -> i32 {
//                      ^^
//                      block argument (entry block) = Value source ②

  %b = arith.constant 42 : i32
//^^
//  operation result = Value source ①

  %c = arith.addi %a, %b : i32   // %a, %b 둘 다 위에서 정의된 Value
  return %c : i32
}
```

SSA 규칙: 한 Value는 정확히 한 번만 정의되고, 정의 이후에만 사용 가능.
타입 예시: `i32`, `index`, `f32`, `tensor<4xf32>`, `memref<8x8xf32>`.

---

##### Value Scope와 Dominance

어떤 value가 어떤 operation에서 사용 가능한지는 두 규칙으로 결정된다.

**① 같은 region 안 — 표준 SSA dominance**

- SSACFG region: A block이 B block을 dominate해야 A의 결과를 B에서 사용 가능
- Graph region: 순서 없음 → 같은 block 안이면 어디서든 참조 가능

**② region 경계 — op의 trait에 따라 결정**

| trait | 내부에서 외부 value 참조 | 예 |
|---|---|---|
| `IsolatedFromAbove` 있음 | 불가 | `func.func` |
| `IsolatedFromAbove` 없음 | 가능 | `scf.for`, `scf.if` |

```mlir
%outer = arith.constant 10 : i32

// scf.if: IsolatedFromAbove 아님 → %outer 직접 캡처 가능
%r = scf.if %cond -> i32 {
  %x = arith.addi %outer, %outer : i32   // OK
  scf.yield %x : i32
} else {
  scf.yield %outer : i32                 // OK
}

// func.func: IsolatedFromAbove → %outer 직접 참조 불가
func.func @bad() -> i32 {
  return %outer : i32   // ERROR: dominance violation across isolated region
}
```

`func.func`가 `IsolatedFromAbove`인 이유: 함수를 독립 컴파일·분석 단위로 만들기 위해.
외부 값이 필요하면 인자로 받거나 `func.call`로 명시 전달해야 한다.

---

##### Attribute

attribute는 operand/result처럼 `%name`으로 흐르는 SSA 값이 아니라, operation에 붙는 정적 constant data.
비교 predicate, constant literal, symbol visibility, affine map 같은 정보를 표현할 때 쓴다.

```mlir
// operand/result는 없고, value attr만 있음
%0 = "arith.constant"() {value = 42 : i32} : () -> i32

// module에 붙는 visibility attr
module attributes {sym_visibility = "public"} {
}

// 비교 방식도 attr로 들어감
%1 = "arith.cmpi"(%lhs, %rhs) {predicate = 2 : i64} : (i32, i32) -> i1
```

- `%lhs`, `%rhs` -> operand
- `%0`, `%1` -> result
- `i32`, `tensor<4xf32>` -> type
- `{value = 42 : i32}`, `{predicate = 2 : i64}` -> attribute dictionary
- `{ ... }` body 자체는 attribute가 아니라 region

attribute value로 들어갈 수 있는 것:

- integer / float
- string
- type
- dense elements
- array / dictionary
- dialect-specific attribute

LangRef 기준으로는 operation의 attribute dictionary가 top-level `{ ... }` 형태로 붙는다.
최근 문서에서는 properties와 attribute를 구분하기도 하지만, 지금 Phase 0에서는
"attribute = op에 붙는 정적 데이터" 정도로 잡으면 충분.

---

##### Dialect

관련 op / type / attribute를 namespace처럼 묶는 확장 단위.
`<dialect>.<op>` 형태로 표기. 한 함수 안에 여러 dialect 혼용 가능.
pass는 특정 dialect를 생산/소비하고, MLIR은 dialect 사이 변환 framework도 제공한다.

| dialect | 담당 |
|---|---|
| `func` | 함수 정의/호출 (`func.func`, `func.call`, `func.return`) |
| `arith` | scalar 산술 (`arith.addi`, `arith.mulf`, `arith.cmpi`) |
| `scf` | structured control flow (`scf.for`, `scf.if`, `scf.yield`) |
| `cf` | low-level control flow (`cf.br`, `cf.cond_br`) |
| `tensor` | immutable tensor 조작 (`tensor.insert`, `tensor.extract`) |
| `memref` | mutable 메모리 버퍼 (`memref.load`, `memref.store`, `memref.alloc`) |
| `linalg` | named/generic 선형대수 op |
| `llvm` | LLVM IR에 1:1 대응하는 low-level op |

```mlir
// 한 함수 안에서 여러 dialect가 섞이는 일반적인 패턴
func.func @mixed(%A: memref<4xf32>) -> f32 {
  %c0  = arith.constant 0 : index
  %c4  = arith.constant 4 : index
  %c1  = arith.constant 1 : index
  %acc0 = arith.constant 0.0 : f32

  %result = scf.for %i = %c0 to %c4 step %c1
            iter_args(%acc = %acc0) -> f32 {
    %val  = memref.load %A[%i] : memref<4xf32>
    %next = arith.addf %acc, %val : f32
    scf.yield %next : f32
  }
  return %result : f32
}
```

---

#### LLVM phi vs MLIR block argument

| 관점 | LLVM `phi` | MLIR block argument |
|---|---|---|
| **위치** | block *안*의 operation | block *헤더*에 선언, op 아님 |
| **방향** | merge 지점에서 pull | predecessor가 push |
| **SSA source** | operation result | block argument (별도 분류) |
| **function arg** | 별도 ABI 처리 | entry block argument로 통합 |
| **uniformity** | phi는 block 맨 앞에만 올 수 있다는 관례 필요 | 구조 자체에 내장 → 모든 value source가 두 가지로 통일 |

**if-else merge** (`x = cond ? a : b`)

```llvm
; LLVM IR — merge 지점의 phi가 출처를 기록
define i32 @select(i1 %cond, i32 %a, i32 %b) {
entry:
  br i1 %cond, label %then, label %else
then:
  br label %merge
else:
  br label %merge
merge:
  %x = phi i32 [ %a, %then ], [ %b, %else ]
  ret i32 %x
}
```

```mlir
// MLIR — predecessor가 값을 push, block argument로 받음
func.func @select(%cond: i1, %a: i32, %b: i32) -> i32 {
  cf.cond_br %cond, ^then, ^else
^then:
  cf.br ^merge(%a : i32)
^else:
  cf.br ^merge(%b : i32)
^merge(%x: i32):
  return %x : i32
}
```

**loop-carried value** (`sum = 0; for i in 0..4: sum += i`)

```llvm
; LLVM IR — header block에 phi 두 개가 쌓임
define i32 @loop_sum() {
entry:
  br label %header
header:
  %i   = phi i32 [ 0, %entry ], [ %i_next, %body ]
  %sum = phi i32 [ 0, %entry ], [ %sum_next, %body ]
  %cond = icmp slt i32 %i, 4
  br i1 %cond, label %body, label %exit
body:
  %sum_next = add i32 %sum, %i
  %i_next   = add i32 %i, 1
  br label %header
exit:
  ret i32 %sum
}
```

```mlir
// MLIR — iter_args로 초기값 선언, scf.yield로 다음 iteration에 push
// body region 첫 block은 암묵적으로 (%i: index, %sum: i32) block argument를 가짐
func.func @loop_sum() -> i32 {
  %c0   = arith.constant 0 : i32
  %c0_i = arith.constant 0 : index
  %c4   = arith.constant 4 : index
  %c1   = arith.constant 1 : index
  %sum_final = scf.for %i = %c0_i to %c4 step %c1
               iter_args(%sum = %c0) -> i32 {
    %i_i32    = arith.index_cast %i : index to i32
    %sum_next = arith.addi %sum, %i_i32 : i32
    scf.yield %sum_next : i32
  }
  return %sum_final : i32
}
```

LLVM으로 낮아질 때 block argument → phi로 변환됨.

---


## 2026-03-21 (~B8)

### Lexical analysis
- 소스 코드를 문자 단위로 읽어 의미 있는 단위인 **토큰(token)** 으로 변환하는 단계.
- `if (x > 0)` 같은 코드를 `IF`, `LPAREN`, `ID(x)`, `GT`, `NUM(0)`, `RPAREN` 등으로 쪼갬.
- 공백, 주석 제거도 이 단계에서 처리하며, 결과물인 토큰 스트림을 파서에 넘김.

### Parsing
- 토큰 스트림이 언어의 **문법(grammar)** 규칙에 맞는지 검사하고, **AST(Abstract Syntax Tree)** 를 생성하는 단계.
- 예를 들어 `x = 1 + 2` 는 대입 노드 아래 좌변 `x`와 우변 덧셈 노드가 붙는 트리로 표현됨.
- 문법 오류(e.g. 괄호 불일치)는 이 단계에서 탐지됨.

### Semantic analysis
- 문법적으로는 맞더라도 **의미적으로 올바른지** 검사하는 단계 (타입 검사, 스코프 분석 등).
- `int x = "hello"` 처럼 타입 불일치나, 선언하지 않은 변수 사용 등을 여기서 잡아냄.
- 분석 결과는 **심볼 테이블(symbol table)** 에 기록되며, 이후 코드 생성 단계의 기반이 됨.

### SSA (Static Single Assignment)
- 각 변수가 정확히 한 번만 정의되는 IR 형태. 모든 use는 단 하나의 def를 가리킨다.
- 분기 merge 지점에서 값이 합쳐질 때 φ(phi) 함수를 삽입해 어느 predecessor에서 왔는지 표현한다.
- 데이터 흐름 분석·최적화(상수 전파, dead code 제거 등)가 단순해지는 것이 핵심 이점.

### AST (Abstract Syntax Tree)
- 파싱 결과를 트리로 표현한 것. 문법의 구체적 표기(괄호, 세미콜론 등)는 제거하고 의미 구조만 남긴다.
- 노드: 연산자/제어구조/함수 호출 등. 리프: 리터럴·식별자.
- semantic analysis, IR 생성, 최적화의 출발점. MLIR에서는 AST → MLIR dialect로 lower한다.

### Toy Tutorial ch1
- MLIR 공식 튜토리얼 첫 번째 챕터. 간단한 toy 언어의 AST 정의와 파서를 직접 구현한다.
- 입력: toy 언어 소스 → 출력: `ToyAST` (Decl / Proto / Expr 노드 구조)
- 목표: AST 노드 구조 이해 + MLIR dialect로 lower하기 위한 출발점 파악.
- ref: https://mlir.llvm.org/docs/Tutorials/Toy/Ch-1/