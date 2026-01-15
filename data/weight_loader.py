import numpy as np
import os
import logging

logger = logging.getLogger(__name__)


def _dummy_weights():
    return {
        "w1": np.random.randn(512, 256).astype("float32") * 0.01,
        "b1": np.zeros((256,), dtype="float32"),
        "w2": np.random.randn(256, 128).astype("float32") * 0.01,
        "b2": np.zeros((128,), dtype="float32"),
    }


def load_weights(path: str) -> dict:
    """加载二进制权重并校验形状；若文件缺失或不完整，回退到 dummy weights。

    期望布局（按顺序）：
      w1: (512,256)
      b1: (256,)
      w2: (256,128)
      b2: (128,)
    """
    expected_shapes = [
        (512, 256),
        (256,),
        (256, 128),
        (128,)
    ]

    expected_count = sum(int(np.prod(s)) for s in expected_shapes)

    if not os.path.exists(path):
        logger.warning("weights.bin not found, using dummy weights for V1.1")
        return _dummy_weights()

    try:
        data = np.fromfile(path, dtype=np.float32)
    except Exception as e:
        logger.warning(f"failed to read weights file '{path}': {e}. Using dummy weights.")
        return _dummy_weights()

    if data.size < expected_count:
        logger.warning(
            f"weights file '{path}' is incomplete (got {data.size} floats, expected {expected_count})."
            " Using dummy weights instead."
        )
        return _dummy_weights()

    offset = 0

    def take(shape):
        nonlocal offset
        size = int(np.prod(shape))
        out = data[offset:offset+size].reshape(shape)
        offset += size
        return out

    try:
        w1 = take((512, 256))
        b1 = take((256,))
        w2 = take((256, 128))
        b2 = take((128,))
    except Exception as e:
        logger.warning(f"failed to parse weights '{path}': {e}. Using dummy weights.")
        return _dummy_weights()

    # 如果文件里还有额外数据，发出提示但继续使用前面的数据
    if offset < data.size:
        logger.info(f"weights file '{path}' contains extra data ({data.size-offset} floats) - ignoring.")

    return {
        "w1": w1,
        "b1": b1,
        "w2": w2,
        "b2": b2
    }
