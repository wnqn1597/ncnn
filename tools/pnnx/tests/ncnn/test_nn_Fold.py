# Tencent is pleased to support the open source community by making ncnn available.
#
# Copyright (C) 2022 THL A29 Limited, a Tencent company. All rights reserved.
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
from packaging import version

class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()

        self.fold_0 = nn.Fold(output_size=22, kernel_size=3)
        self.fold_1 = nn.Fold(output_size=(17,18), kernel_size=(2,4), stride=(2,1), padding=2, dilation=1)
        self.fold_2 = nn.Fold(output_size=(5,11), kernel_size=(2,3), stride=1, padding=(2,4), dilation=(1,2))

    def forward(self, x, y, z):
        x = self.fold_0(x)
        y = self.fold_1(y)
        z = self.fold_2(z)

        return x, y, z

def test():
    net = Model()
    net.eval()

    torch.manual_seed(0)
    x = torch.rand(1, 108, 400)
    y = torch.rand(1, 96, 190)
    z = torch.rand(1, 36, 120)

    a = net(x, y, z)

    # export torchscript
    mod = torch.jit.trace(net, (x, y, z))
    mod.save("test_nn_Fold.pt")

    # torchscript to pnnx
    import os
    os.system("../../src/pnnx test_nn_Fold.pt inputshape=[1,108,400],[1,96,190],[1,36,120]")

    # ncnn inference
    import test_nn_Fold_ncnn
    b = test_nn_Fold_ncnn.test_inference()

    # pnnx inference cpp
    os.system("mkdir -p build && cd build && cmake .. -DFNAME=test_nn_Fold_ncnn && make")
    os.system("./build/test_nn_Fold_ncnn")
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
