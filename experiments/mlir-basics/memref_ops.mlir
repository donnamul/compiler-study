func.func @fill(%buffer: memref<4xf32>) {
  %c0 = arith.constant 0 : index
  %c4 = arith.constant 4 : index
  %c1 = arith.constant 1 : index
  %value = arith.constant 1.0 : f32
  scf.for %i = %c0 to %c4 step %c1 {
    memref.store %value, %buffer[%i] : memref<4xf32>
  }
  return
}
