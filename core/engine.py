import numpy as np
from core.operators import linear, relu, l2_normalize

class InferenceEngine:
    """
    V1.1 手写推理引擎
    输入：图片特征向量（假定已预处理）
    输出：Embedding（归一化）
    """

    def __init__(self, weights: dict):
        self.w1 = weights["w1"]
        self.b1 = weights["b1"]
        self.w2 = weights["w2"]
        self.b2 = weights["b2"]

    def infer(self, x: np.ndarray) -> np.ndarray:
        x = linear(x, self.w1, self.b1)
        x = relu(x)
        x = linear(x, self.w2, self.b2)
        x = l2_normalize(x)
        return x
