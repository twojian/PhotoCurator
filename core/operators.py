import numpy as np

def linear(x: np.ndarray, w: np.ndarray, b: np.ndarray) -> np.ndarray:
    return x @ w + b

def relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0, x)

def l2_normalize(x: np.ndarray, eps=1e-8) -> np.ndarray:
    norm = np.linalg.norm(x)
    return x / (norm + eps)
