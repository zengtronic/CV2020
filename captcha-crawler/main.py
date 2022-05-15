#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
from itertools import cycle
import os
import time
import cv2
import argparse

DIR_RAW_CAPTCHAS = "data/raw"
DIR_DEFECTIVE_CAPTCHAS = "data/defective"

CAPTCHA_GOAL = 2000

request_urls = [
    "PLACE_A_AMAZON_PRODUCTLINK_HERE",
]
request_change = 500    # Switching proxy after this count of requests
request_cnt = 0         # Count of requests in this cycle
request_headers = {
    "User-Agent": "bot"
}

proxies = [
    {"http": "INSERT_URL_OF_HTTP_PROXY", "https": "INSERT_URL_OF_HTTPS_PROXY"},
]
use_proxy = False

delay = 1   # Pause between two requests (in seconds)

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
parser = argparse.ArgumentParser(description='Crawls specified Amazon Link for captchas')
parser.add_argument('--dir_raw', type=str, dest='raw', default=None, help='Directory for crawled captchas')
parser.add_argument('--dir_defective', type=str, dest='defective', default=None, help='Directory for defective captchas')
parser.add_argument('--useproxy', type=bool, dest='useproxy', default=False, help='Use proxy or not')
parser.add_argument('--proxies', type=str, dest='proxylist', default=None, help='List of proxies. Full URLs with protocol and port, seperated by semicolon (;)')
parser.add_argument('--items', type=str, dest='itemlist', default=None, help='List of products (Amazon URL) which should be crawled, seperated by semicolon (;)')
parser.add_argument('--delay', type=float, dest='delay', default=None, help='Pause between two requests, in seconds')

args = parser.parse_args()
if args.raw is not None:
    DIR_RAW_CAPTCHAS = args.raw
if args.defective is not None:
    DIR_DEFECTIVE_CAPTCHAS = args.defective
if args.itemlist is not None:
    request_urls = args.itemlist.split(";")
if args.useproxy:
    if args.proxylist is not None:
        temp = args.proxylist.split(";")
        proxies = []
        for proxy in temp:
            proxies.append({"http": proxy, "https": proxy})
        use_proxy = True
if args.delay is not None:
    delay = args.delay


#create dirs on startup
os.makedirs(DIR_RAW_CAPTCHAS, exist_ok=True)
os.makedirs(DIR_DEFECTIVE_CAPTCHAS, exist_ok=True)


request_url_cycle = cycle(request_urls)
if use_proxy:
    request_proxy_cycle = cycle(proxies)
    request_proxy = next(request_proxy_cycle)
    print("Using Proxy: ", request_proxy)
else:
    request_proxy_cycle = None
    request_proxy = None

while len(os.listdir(DIR_RAW_CAPTCHAS)) < CAPTCHA_GOAL:
    request_ok = True
    print(".", end='')
    if use_proxy:
        # cycle the proxies
        request_cnt += 1
        if request_cnt > request_change:
            request_cnt = 0
            request_proxy = next(request_proxy_cycle)
            print("Using Proxy: ", request_proxy)

    # cycle the request url
    request_url = next(request_url_cycle)
    try:
        if use_proxy:
            request = requests.get(request_url, proxies=request_proxy)
        else:
            request = requests.get(request_url)
    except Exception as e:
        print("Error while requesting site", e.__context__)
        request_ok = False
    if request_ok:
        web_content = request.text

        soup = BeautifulSoup(web_content, 'html.parser')

        if "bot" in soup.title.text.lower():
            print("Found Captcha")
            with open("blocked.html", 'w') as file:
                file.writelines(str(soup))
                file.close()
            imgs = soup.findAll("img")
            for img in imgs:
                img_src = str(img["src"])
                if "captcha" in img_src.lower():
                    try:
                        # Downloading Captcha
                        print("Downloading the Captcha image:  " + img_src)
                        image_name = DIR_RAW_CAPTCHAS + "/" + str(time.time()) + ".jpg"
                        if use_proxy:
                            r = requests.get(img_src, stream=True, proxies=request_proxy)
                        else:
                            r = requests.get(img_src, stream=True)
                        with open(image_name, 'wb') as f:
                            for chunk in r.iter_content():
                                f.write(chunk)
                        print("Saved: " + image_name)

                        # Image invalid
                        if not check_image(image_name):
                            os.rename(image_name, DIR_DEFECTIVE_CAPTCHAS + "/" + str(time.time()) + ".jpg")
                            print("Image was invalid! Moved to defective folder!")
                    except Exception as e:
                        print("Error while downloading captcha", e.__context__)

    time.sleep(delay)


