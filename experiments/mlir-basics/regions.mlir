func.func @nested_regions(%n: index) -> index {
  %c0 = arith.constant 0 : index
  %c1 = arith.constant 1 : index
  %result = scf.for %i = %c0 to %n step %c1 iter_args(%acc = %c0) -> (index) {
    %flag = arith.cmpi slt, %i, %n : index
    %next = scf.if %flag -> (index) {
      %tmp = arith.addi %acc, %i : index
      scf.yield %tmp : index
    } else {
      scf.yield %acc : index
    }
    scf.yield %next : index
  }
  return %result : index
}
