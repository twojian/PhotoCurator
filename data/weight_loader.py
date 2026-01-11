import numpy as np
import os

def load_weights(path: str) -> dict:
    if not os.path.exists(path):
        print("[WARN] weights.bin not found, using dummy weights for V1.1")

        return {
            "w1": np.random.randn(512, 256).astype("float32") * 0.01,
            "b1": np.zeros((256,), dtype="float32"),
            "w2": np.random.randn(256, 128).astype("float32") * 0.01,
            "b2": np.zeros((128,), dtype="float32"),
        }

    data = np.fromfile(path, dtype=np.float32)
    offset = 0

    def take(shape):
        nonlocal offset
        size = int(np.prod(shape))
        out = data[offset:offset+size].reshape(shape)
        offset += size
        return out

    return {
        "w1": take((512, 256)),
        "b1": take((256,)),
        "w2": take((256, 128)),
        "b2": take((128,))
    }
