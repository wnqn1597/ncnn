# Tencent is pleased to support the open source community by making ncnn available.
#
# Copyright (C) 2021 THL A29 Limited, a Tencent company. All rights reserved.
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

    def forward(self, x):
        out0 = F.adaptive_avg_pool2d(x, output_size=(7,6))
        out1 = F.adaptive_avg_pool2d(x, output_size=1)
        out2 = F.adaptive_avg_pool2d(x, output_size=(None,3))
        out3 = F.adaptive_avg_pool2d(x, output_size=(5,None))
        return out0, out1, out2, out3

def test():
    net = Model()
    net.eval()

    torch.manual_seed(0)
    x = torch.rand(1, 12, 24, 64)

    a = net(x)

    # export torchscript
    mod = torch.jit.trace(net, x)
    mod.save("test_F_adaptive_avg_pool2d.pt")

    # torchscript to pnnx
    import os
    os.system("../../src/pnnx test_F_adaptive_avg_pool2d.pt inputshape=[1,12,24,64]")

    # ncnn inference
    import test_F_adaptive_avg_pool2d_ncnn
    b = test_F_adaptive_avg_pool2d_ncnn.test_inference()

    # ncnn cpp inference
    os.system("mkdir -p build && cd build && cmake .. -DFNAME=test_F_adaptive_avg_pool2d_ncnn && make")
    os.system("./build/test_F_adaptive_avg_pool2d_ncnn")
    c = list(torch.jit.load("out.pt").parameters())

    for a0, b0 in zip(a, b):
        b0 = b0.reshape_as(a0)
        if not torch.allclose(a0, b0, 1e-4, 1e-4):
            return False
    for a0, c0 in zip(a, c):
        c0 = c0.reshape_as(a0)
        if not torch.allclose(a0, c0, 1e-4, 1e-4):
            return False
    return True

if __name__ == "__main__":
    if test():
        exit(0)
    else:
        exit(1)
