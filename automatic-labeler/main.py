#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from anticaptchaofficial.imagecaptcha import *
import os
from os import path
import time
import cv2
import argparse

DIR_SOLVED = "data/solved"
DIR_TO_SOLVE = "data/raw"
DIR_FAILED = "data/failed"
DIR_DEFECTIVE = "data/defective"
DIR_DOUBLE = "data/double"

'''
checks if captcha is useful
'''
def check_image(file):
    results = []   # array for results
    imgfile = cv2.imread(file)
    if imgfile is None:
        print("Image is empty!")
        return False

    image = cv2.cvtColor(imgfile, cv2.COLOR_BGR2HLS)
    (height, width) = image.shape[:2]

    # check image size
    if height > 0 and width > 0:
        results.append(True)
    else:
        print("Image is empty!")
        return False

    # if lightness in the right bottom is > ~98% => valid
    (h, l, s) = image[height - 5, width - 5]
    if l > 250:
        results.append(True)
    else:
        results.append(False)
        print("Imagefile is defective!")

    # check the first col of pixels if its not fully white => overlapping chars
    overlapping = False
    for i in range(0, height - 1):
        (h, l, s) = image[i, 0]
        if l < 250:
            overlapping = True
    if overlapping:
        results.append(False)
        print("Captcha chars overlaps!")
    else:
        results.append(True)

    # give back the result
    if all(results):
        return True
    else:
        return False


# start arguments
parser = argparse.ArgumentParser(description='Labels automatically the given captchas')
parser.add_argument('--key', type=str, dest='apikey', required=True, help='Your API key for anticaptcha.com')
parser.add_argument('--dir_raw', type=str, dest='raw', default=None, help='Directory for unprocessed captchas')
parser.add_argument('--dir_solved', type=str, dest='solved', default=None, help='Directory for solved captchas')
parser.add_argument('--dir_failed', type=str, dest='failed', default=None, help='Directory for failed captchas')
parser.add_argument('--dir_defective', type=str, dest='defective', default=None, help='Directory for defective captchas')

args = parser.parse_args()
key = args.apikey
if args.raw is not None:
    DIR_TO_SOLVE = args.raw
if args.defective is not None:
    DIR_DEFECTIVE = args.defective
if args.solved is not None:
    DIR_SOLVED = args.raw
if args.failed is not None:
    DIR_FAILED = args.defective
# create dirs
os.makedirs(DIR_SOLVED, exist_ok=True)
os.makedirs(DIR_TO_SOLVE, exist_ok=True)
os.makedirs(DIR_FAILED, exist_ok=True)
os.makedirs(DIR_DEFECTIVE, exist_ok=True)
os.makedirs(DIR_DOUBLE, exist_ok=True)

solver = imagecaptcha()
solver.set_verbose(1)
solver.set_key(key)

while True:
    files = os.listdir(DIR_TO_SOLVE)
    files_cnt = len(files)
    if files_cnt > 0:
        for file in os.listdir(DIR_TO_SOLVE):
            print("Solving " + file)
            if not check_image(DIR_TO_SOLVE + "/" + file):
                print("Image is invalid")
                if not path.exists(DIR_DEFECTIVE + "/" + file):
                    os.rename(DIR_TO_SOLVE + "/" + file, DIR_DEFECTIVE + "/" + file)
                else:
                    os.remove(DIR_TO_SOLVE + "/" + file)
                break
            status = ""
            text = ""

            ts_before = time.time()
            captcha_text = solver.solve_and_return_solution(DIR_TO_SOLVE + "/" + file)
            ts_after = time.time()
            if captcha_text != 0:
                print("Solved: Captcha code is " + str(captcha_text).upper() + ". Solved in " + str(round(ts_after - ts_before,2)) + "s")
                filename = str(captcha_text).upper()

                if not path.exists(DIR_SOLVED + "/" + filename + ".jpg"):
                    os.rename(DIR_TO_SOLVE + "/" + file, DIR_SOLVED + "/" + filename + ".jpg")
                else:
                    os.rename(DIR_TO_SOLVE + "/" + file, DIR_DOUBLE + "/" + filename + "." + str(time.time()) + ".jpg")
            else:
                print("task finished with error "+solver.error_code)
                if not path.exists(DIR_FAILED + "/" + file):
                    os.rename(DIR_TO_SOLVE + "/" + file, DIR_FAILED + "/" + file)
                else:
                    os.remove(DIR_TO_SOLVE + "/" + file)

    else:
        time.sleep(5)
