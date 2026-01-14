
import torch

def export(model, path):
    with open(path, "wb") as f:
        for name, param in model.state_dict().items():
            f.write(name.encode())
            f.write(param.cpu().numpy().tobytes())
import torch
def export(model, path):
    with open(path, "wb") as f:
        for name, param in model.state_dict().items():
            f.write(name.encode())
            f.write(param.cpu().numpy().tobytes())
