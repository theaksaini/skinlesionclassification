
# coding: utf-8

# In[44]:

# Setting up
from __future__ import print_function, division
import os
import numpy as np
import torch
import pandas as pd
from skimage import io, transform

import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, utils

from training_utils import *
from data_loading import *


#transform_list = transforms.Compose([grey_world(),transforms.ToPILImage(),transforms.Scale(250),transforms.RandomHorizontalFlip() ,
#                                     transforms.RandomCrop(224), transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406],[0.229, 0.224, 0.225])])
#without color constancy 
transform_list = transforms.Compose([transforms.ToPILImage(),transforms.Scale(224),transforms.RandomCrop(224),
                                     transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406],[0.229, 0.224, 0.225])])


# transforms.RandomRotation(90, expand=True) and VerticalFlip() not working for some reason!!
#input_dir= '../datasets/'
input_dir = '/mnt/nfs/work1/lspector/aks/datasets/'

useSegmentation=False

train = SkinLesionDataset(csv_file=input_dir+'ISIC-2017_Training_Part3_GroundTruth.csv',
                                    root_dir=input_dir+'ISIC-2017_Training_Data/',segment_dir=input_dir+'ISIC-2017_Training_Part1_GroundTruth',useSegmentation = useSegmentation, transform=transform_list)
train_light = SkinLesionDataset(csv_file=input_dir+'ISIC-2017_Training_Part3_GroundTruth_light.csv',
                                    root_dir=input_dir+'ISIC-2017_Training_Data/',segment_dir=input_dir+'ISIC-2017_Training_Part1_GroundTruth',useSegmentation = useSegmentation, transform=transform_list)


validation  = SkinLesionDataset(csv_file=input_dir+'ISIC-2017_Validation_Part3_GroundTruth.csv',
                                    root_dir=input_dir+'ISIC-2017_Validation_Data/',segment_dir=input_dir+'ISIC-2017_Validation_Part1_GroundTruth', useSegmentation =useSegmentation,transform = transform_list)
test = SkinLesionDataset(csv_file=input_dir+'ISIC-2017_Test_v2_Part3_GroundTruth.csv',
                                    root_dir=input_dir+'ISIC-2017_Test_v2_Data/',segment_dir=input_dir+'ISIC-2017_Test_v2_Part1_GroundTruth', useSegmentation =useSegmentation,transform = transform_list)

train_data = DataLoader(train, batch_size=8,
                        shuffle=True, num_workers=1)
train_data_light = DataLoader(train_light, batch_size=8,
                        shuffle=True, num_workers=1)
val_data = DataLoader(validation, batch_size=8,
                        shuffle=True, num_workers=1)
test_data = DataLoader(test, batch_size=8,
                        shuffle=True, num_workers=1)

dataset_sizes = {'train':len(train),'val':len(validation),'test':len(test)}
print(dataset_sizes)

dataloaders = {'train':train_data,'val':val_data,'test':test_data}
get_ipython().magic(u'load_ext autoreload')
get_ipython().magic(u'autoreload 2')





# In[119]:

def masking(img, img_segment, level_of_opaqueness):
    #level_of_opaqueness: the more it it, the more opaque the object becomes, values between (0,255)
    img_modified = img
    img_modified[img_segment==0] =level_of_opaqueness
    return img_modified




# In[27]:

model_resnet = torchvision.models.resnet34(pretrained=True)
for param in model_resnet.parameters():
    param.requires_grad = False

# Parameters of newly constructed modules have requires_grad=True by default
num_ftrs = model_resnet.fc.in_features

#print(num_ftrs)
model_resnet.fc = nn.Linear(num_ftrs, 2)

criterion = nn.CrossEntropyLoss()

# Observe that only parameters of final layer are being optimized as
# opoosed to before.
optimizer_conv = optim.SGD(model_resnet.fc.parameters(), lr=1.13e-03, weight_decay = 5.37e-04, momentum=0.9)

# Decay LR by a factor of 0.1 every 7 epochs
exp_lr_scheduler = lr_scheduler.StepLR(optimizer_conv, step_size=7, gamma=0.1)




# In[3]:

model_vgg = torchvision.models.vgg19_bn(pretrained=True)
for param in model_vgg.parameters():
    param.requires_grad = False

# Parameters of newly constructed modules have requires_grad=True by default
num_ftrs = model_vgg.classifier[6].out_features#model_vgg.fc.in_features

#print(num_ftrs)
model_vgg.classifier.add_module("7",nn.ReLU())
model_vgg.classifier.add_module("8",nn.Linear(num_ftrs, 2))
criterion = nn.CrossEntropyLoss()

# Observe that only parameters of final layer are being optimized as
# opoosed to before.
optimizer_conv = optim.SGD(model_vgg.classifier[8].parameters(), lr=0.001, weight_decay = 5.37e-04, momentum=0.9)

# Decay LR by a factor of 0.1 every 7 epochs
exp_lr_scheduler = lr_scheduler.StepLR(optimizer_conv, step_size=7, gamma=0.1)


# In[60]:

#Hyper-parameter tuning
from numpy.random import uniform



# In[45]:

dataset_sizes1 = {'train':len(validation),'val':len(validation),'test':len(test)}
#print(dataset_sizes1)

dataloaders1 = {'train':val_data,'val':val_data,'test':test_data}

model_conv = train_model(model_resnet, criterion, optimizer_conv,
                         exp_lr_scheduler, dataloaders,dataset_sizes,num_epochs=1)

print("With using Normalization: ")
test_model(model_conv, criterion, dataloaders,dataset_sizes)

