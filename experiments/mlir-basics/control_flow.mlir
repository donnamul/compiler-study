func.func @sum_to_n(%n: index) -> index {
  %c0 = arith.constant 0 : index
  %c1 = arith.constant 1 : index
  %sum = scf.for %i = %c0 to %n step %c1 iter_args(%acc = %c0) -> (index) {
    %next = arith.addi %acc, %i : index
    scf.yield %next : index
  }
  return %sum : index
}
