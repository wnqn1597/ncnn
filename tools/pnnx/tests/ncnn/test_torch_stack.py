# Tencent is pleased to support the open source community by making ncnn available.
#
# Copyright (C) 2023 THL A29 Limited, a Tencent company. All rights reserved.
#
# Licensed under the BSD 3-Clause License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# https://opensource.org/licenses/BSD-3-Clause
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import torch
import torch.nn as nn
import torch.nn.functional as F

class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()

    def forward(self, x, y, z, w):
        out0 = torch.stack((x, y), dim=0)
        out1 = torch.stack((x, y), dim=2)
        out2 = torch.stack((z, w), dim=2)
        out3 = torch.stack((z, w), dim=-1)
        out0.relu_()
        out1.relu_()
        out2.relu_()
        out3.relu_()
        return out0, out1, out2, out3

def test():
    net = Model()
    net.eval()

    torch.manual_seed(0)
    x = torch.rand(3, 16)
    y = torch.rand(3, 16)
    z = torch.rand(5, 9, 3)
    w = torch.rand(5, 9, 3)

    a = net(x, y, z, w)

    # export torchscript
    mod = torch.jit.trace(net, (x, y, z, w))
    mod.save("test_torch_stack.pt")

    # torchscript to pnnx
    import os
    os.system("../../src/pnnx test_torch_stack.pt inputshape=[3,16],[3,16],[5,9,3],[5,9,3]")

    # ncnn inference
    import test_torch_stack_ncnn
    b = test_torch_stack_ncnn.test_inference()

    # pnnx inference cpp
    os.system("mkdir -p build && cd build && cmake .. -DFNAME=test_torch_stack_ncnn && make")
    os.system("./build/test_torch_stack_ncnn")
    c = list(torch.jit.load("out.pt").parameters())

    for a0, b0 in zip(a, b):
        if not torch.allclose(a0, b0, 1e-4, 1e-4):
            return False
    for a0, c0 in zip(a, c):
        if not torch.allclose(a0, c0, 1e-4, 1e-4):
            return False
    return True

if __name__ == "__main__":
    if test():
        exit(0)
    else:
        exit(1)
