func.func @replace_first(%input: tensor<4xf32>, %value: f32) -> tensor<4xf32> {
  %c0 = arith.constant 0 : index
  %0 = tensor.insert %value into %input[%c0] : tensor<4xf32>
  return %0 : tensor<4xf32>
}
