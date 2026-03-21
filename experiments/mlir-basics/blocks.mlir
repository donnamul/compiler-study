func.func @branching(%arg0: i1, %arg1: i32) -> i32 {
  cf.cond_br %arg0, ^bb1(%arg1 : i32), ^bb2(%arg1 : i32)

^bb1(%x: i32):
  %0 = arith.addi %x, %x : i32
  cf.br ^bb3(%0 : i32)

^bb2(%y: i32):
  %1 = arith.muli %y, %y : i32
  cf.br ^bb3(%1 : i32)

^bb3(%z: i32):
  return %z : i32
}
