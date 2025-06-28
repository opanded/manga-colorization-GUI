"""
Definition of the FFDNet model and its custom layers

Copyright (C) 2018, Matias Tassano <matias.tassano@parisdescartes.fr>

This program is free software: you can use, modify and/or
redistribute it under the terms of the GNU General Public
License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later
version. You should have received a copy of this license along
this program. If not, see <http://www.gnu.org/licenses/>.
"""
import torch.nn as nn
from torch.autograd import Variable
import denoising.functions as functions
    
# UpSampleFeatures：FFDNet最后一层，负责特征上采样
class UpSampleFeatures(nn.Module):
    def __init__(self):
        super(UpSampleFeatures, self).__init__()
    def forward(self, x):
        return functions.upsamplefeatures(x)

# IntermediateDnCNN：FFDNet中间部分，核心为多层卷积+BN+ReLU
class IntermediateDnCNN(nn.Module):
    def __init__(self, input_features, middle_features, num_conv_layers):
        super(IntermediateDnCNN, self).__init__()
        self.kernel_size = 3
        self.padding = 1
        self.input_features = input_features
        self.num_conv_layers = num_conv_layers
        self.middle_features = middle_features
        if self.input_features == 5:
            self.output_features = 4 # 灰度图
        elif self.input_features == 15:
            self.output_features = 12 # RGB图
        else:
            raise Exception('Invalid number of input features')
        layers = []
        layers.append(nn.Conv2d(in_channels=self.input_features,\
                                out_channels=self.middle_features,\
                                kernel_size=self.kernel_size,\
                                padding=self.padding,\
                                bias=False))
        layers.append(nn.ReLU(inplace=True))
        for _ in range(self.num_conv_layers-2):
            layers.append(nn.Conv2d(in_channels=self.middle_features,\
                                    out_channels=self.middle_features,\
                                    kernel_size=self.kernel_size,\
                                    padding=self.padding,\
                                    bias=False))
            layers.append(nn.BatchNorm2d(self.middle_features))
            layers.append(nn.ReLU(inplace=True))
        layers.append(nn.Conv2d(in_channels=self.middle_features,\
                                out_channels=self.output_features,\
                                kernel_size=self.kernel_size,\
                                padding=self.padding,\
                                bias=False))
        self.itermediate_dncnn = nn.Sequential(*layers)
    def forward(self, x):
        out = self.itermediate_dncnn(x)
        return out

# FFDNet：FFDNet主结构，支持灰度和RGB，输入拼接噪声图，输出噪声估计
class FFDNet(nn.Module):
    def __init__(self, num_input_channels):
        super(FFDNet, self).__init__()
        self.num_input_channels = num_input_channels
        if self.num_input_channels == 1:
            # 灰度图
            self.num_feature_maps = 64
            self.num_conv_layers = 15
            self.downsampled_channels = 5
            self.output_features = 4
        elif self.num_input_channels == 3:
            # RGB图
            self.num_feature_maps = 96
            self.num_conv_layers = 12
            self.downsampled_channels = 15
            self.output_features = 12
        else:
            raise Exception('Invalid number of input features')
        self.intermediate_dncnn = IntermediateDnCNN(\
                input_features=self.downsampled_channels,\
                middle_features=self.num_feature_maps,\
                num_conv_layers=self.num_conv_layers)
        self.upsamplefeatures = UpSampleFeatures()
    def forward(self, x, noise_sigma):
        # 拼接噪声图，前向推理
        concat_noise_x = functions.concatenate_input_noise_map(x.data, noise_sigma.data)
        concat_noise_x = Variable(concat_noise_x)
        h_dncnn = self.intermediate_dncnn(concat_noise_x)
        pred_noise = self.upsamplefeatures(h_dncnn)
        return pred_noise
