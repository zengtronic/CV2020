#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import matplotlib.pyplot as plotter
import numpy as np
import json
alphabet = {
    "A": 0,
    "B": 0,
    "C": 0,
    "D": 0,
    "E": 0,
    "F": 0,
    "G": 0,
    "H": 0,
    "I": 0,
    "J": 0,
    "K": 0,
    "L": 0,
    "M": 0,
    "N": 0,
    "O": 0,
    "P": 0,
    "Q": 0,
    "R": 0,
    "S": 0,
    "T": 0,
    "U": 0,
    "V": 0,
    "W": 0,
    "X": 0,
    "Y": 0,
    "Z": 0,
}
total = 0

parser = argparse.ArgumentParser(description='Statistic of character distribution of filenames in a specific folder.')
parser.add_argument('--input', type=str, dest='input', help='Input directory')
parser.add_argument('--noui', type=bool, dest='noui', default=False, help='True: Only output on console.')

args = parser.parse_args()
inputFolder = args.input
noui = args.noui

if os.path.exists(inputFolder):
    for file in os.listdir(inputFolder):
        name = file.split(".")[0]
        for char in name:
            if char in alphabet:
                # count up known characters
                alphabet[char] += 1
                total += 1
            else:
                # add unknown character in plot... also a sign that something is wrong with the captchas
                # as there are only capital letters and only A-Z
                alphabet[char] = 1

    print("=== CHARACTER DISTRIBUTION ===")
    print(json.dumps(alphabet, indent=3))   # pretty-print that array
    print("Total chars: " + str(total))

    if not noui:
        # plot a nice bar chart
        y = alphabet.keys()
        y_pos = np.arange(len(y))
        x = []
        for char in alphabet:
            x.append(alphabet[char])
        plotter.bar(y_pos, x, align="center", color="#000000",edgecolor='#000000', alpha=0.75)
        plotter.xticks(y_pos, y)
        plotter.title("Captcha character distribution (Total: " + str(total) + " chars.)")
        plotter.ylabel("amount")
        plotter.show()
else:
    print("Folder not found!")