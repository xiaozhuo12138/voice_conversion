import numpy as np
import torch.nn as nn
import torch.nn.functional as F
import torch
from torch.autograd import Variable

def get_grad(net):
    for p in net.parameters():
       print(torch.sum(p.grad), p.size())
    return

def conv(c_in, c_out, kernel_size, stride=1, pad=True, bn=True):
    layers = []
    if pad:
        layers.append(
            nn.ReflectionPad2d(kernel_size[0] // 2)
        )
    layers.append(nn.Conv2d(c_in, c_out, kernel_size, stride=stride))
    if bn:
        layers.append(nn.BatchNorm2d(c_out))
    return nn.Sequential(*layers)

class Encoder(nn.Module):
    def __init__(self, c_in, c_out):
        super(Encoder, self).__init__()
        self.conv1 = conv(c_in, 128, kernel_size=(5, 5), stride=1, pad=True, bn=False)
        self.conv2 = conv(128 + c_in, 256, kernel_size=(5, 5), stride=1, pad=True, bn=False)
        self.conv3 = conv(256 + c_in, 128, kernel_size=(5, 5), stride=1, pad=True, bn=False)
        self.conv4 = conv(128 + c_in, c_out, kernel_size=(5, 5), stride=1, pad=True, bn=False)

    def forward(self, x):
        out = self.conv1(x)
        out = F.leaky_relu(out)
        out = torch.cat((out, x), 1)
        out = self.conv2(out)
        out = F.leaky_relu(out)
        out = torch.cat((out, x), 1)
        out = self.conv3(out)
        out = F.leaky_relu(out)
        out = torch.cat((out, x), 1)
        out = self.conv4(out)
        out = F.leaky_relu(out)
        return out

class Discriminator(nn.Module):
    def __init__(self, c_in, image_size=(257, 64)):
        super(Discriminator, self).__init__()
        self.conv1 = conv(c_in, 64, kernel_size=(5, 5), stride=2, bn=False, pad=True)
        self.conv2 = conv(64, 128, kernel_size=(5, 5), stride=2, bn=True, pad=True)
        self.conv3 = conv(128, 256, kernel_size=(5, 5), stride=2, bn=True, pad=True)
        self.conv4 = conv(256, 512, kernel_size=(5, 5), stride=2, bn=True, pad=True)
        self.fc = conv(512, 1, (int(image_size[0] / 16 + 1), int(image_size[1] / 16)), bn=False, pad=False)

    def forward(self, e1, e2):
        e = torch.cat([e1, e2], dim=1)
        out = self.conv1(e)
        out = F.leaky_relu(out)
        out = self.conv2(out)
        out = F.leaky_relu(out)
        out = self.conv3(out)
        out = F.leaky_relu(out)
        out = self.conv4(out)
        out = F.leaky_relu(out)
        out = self.fc(out).squeeze()
        out = F.sigmoid(out)
        return out

if __name__ == '__main__':
    E_s = Encoder(1, 1).cuda()
    total = Variable(torch.Tensor([0])).cuda()
    E_c = Encoder(1, 1).cuda()
    D = Encoder(2, 1).cuda()
    C = Discriminator(2).cuda()
    np.random.seed(0)
    d1 = Variable(torch.from_numpy(np.random.rand(16, 1, 257, 64))).type(torch.FloatTensor).cuda()
    d2 = Variable(torch.from_numpy(np.random.rand(16, 1, 257, 64))).type(torch.FloatTensor).cuda()
    e1 = E_s(d1)
    print(e1.data)
    e2 = E_s(d2)
    e3 = E_c(d2)
    print(e3.data)
    dec1 = D(torch.cat((e1, e3), dim=1))
    print(dec1.data)
    print(dec1.requires_grad)
    loss_sim = torch.sum((e2 - e1) ** 2) / 16
    loss_rec = torch.sum((dec1 - d2) ** 2) / 16
    print(loss_rec.data[0])
    E_s.zero_grad()
    loss_rec.backward()
    get_grad(E_s)
