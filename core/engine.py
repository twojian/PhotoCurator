import numpy as np
from core.operators import linear, relu, l2_normalize
from PIL import Image  # 需要 pip install pillow

def load_and_vectorize(image_path: str, size=(32, 32)) -> np.ndarray:
    """
    读取图片并转为固定向量，用于 V1.2 推理引擎
    """
    try:
        img = Image.open(image_path).convert("L")  # 转灰度
        img = img.resize(size)
        arr = np.array(img, dtype=np.float32) / 255.0  # 归一化到 [0,1]
        return arr.flatten()  # 转为 1D 向量
    except Exception as e:
        print(f"[WARN] 加载图片失败 {image_path}: {e}")
        return np.zeros(size[0]*size[1], dtype=np.float32)
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
