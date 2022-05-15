#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from PIL import Image
import argparse

# start arguments
parser = argparse.ArgumentParser(description='Prepares captcha for tesseract training. Every 5th picture will be testdata.')
parser.add_argument('--input', type=str, dest='input', required=True, help='Input directory (solved captchas)')
parser.add_argument('--output', type=str, dest='output', required=True, help='Output directory')
parser.add_argument('--name', type=str, dest='name', required=True, help='Name of the dataset')

args = parser.parse_args()
DIR_INPUT = args.input
DIR_OUTPUT = args.output
DATASET_NAME = args.name


# create dirs
os.makedirs(DIR_INPUT, exist_ok=True)
os.makedirs(DIR_OUTPUT + "/" + str(DATASET_NAME) + "-test/", exist_ok=True)
os.makedirs(DIR_OUTPUT + "/" + str(DATASET_NAME) + "-ground-truth/", exist_ok=True)

split_cnt = 0
i = 0
for file in os.listdir(DIR_INPUT):
    split_cnt += 1
    if split_cnt is 5:
        split_cnt = 0
        name = file.split(".")[0]
        image = Image.open(DIR_INPUT + "/" + file)
        image.save(DIR_OUTPUT + "/" + str(DATASET_NAME) + "-test/" + name + ".tif")
    else:
        i = i + 1
        name = file.split(".")[0]
        image = Image.open(DIR_INPUT + "/" + file)
        image.save(DIR_OUTPUT + "/" + str(DATASET_NAME) + "-ground-truth/" + str(i) + ".tif")
        f = open(DIR_OUTPUT + "/" + str(DATASET_NAME) + "-ground-truth/" + str(i) + ".gt.txt", "w")
        f.write(str(name))
        f.close()
