import sys
import pytesseract
import cv2
import os
import json
from difflib import SequenceMatcher as SQ
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageOps, ImageEnhance
import argparse

class predictListObject:
    def __init__(self, image_id):
        self.id = image_id
        self.is_tp = False
        self.score = 0


def precision_interpolated(prec_list, rec_list, cur_recall):
    greater_recall = rec_list >= cur_recall
    if greater_recall.sum() == 0:
        return 0
    return max(prec_list[greater_recall])

# mainly the same as in the kitti task
def plotPRC(pred_obj_list_total, gt_total):
    # sort the pred_obj_list by score desc.
    score_list = np.zeros(len(pred_obj_list_total))
    for i in range(len(score_list)):
        score_list[i] = pred_obj_list_total[i].score

    score_indexes = (-score_list).argsort()
    pred_obj_list_total_sorted = []
    for i in range(len(score_indexes)):
        pred_obj_list_total_sorted.append(pred_obj_list_total[score_indexes[i]])

    tplist = []
    for i in range(len(pred_obj_list_total_sorted)):
        tplist.append(1 if pred_obj_list_total_sorted[i].is_tp else 0)
    tplist_np = np.array(tplist, dtype = np.bool)
    TP = tplist_np
    FP = tplist_np == 0
    cumSumTP = TP.cumsum()  # cumulative sum of true positive
    cumSumFP = FP.cumsum()  # cumulative sum of false positive

    precision_list = cumSumTP / (cumSumTP + cumSumFP)
    recall_list = cumSumTP / gt_total
    print(recall_list)
    print(precision_list)
    plt.plot(recall_list, precision_list)
    plt.title("Precision-Recall-Curve")
    plt.xlabel('recall')
    plt.ylabel('precision')
    plt.show()
    
    interpol_points = [0]
    [interpol_points.append(r) for r in recall_list]

    precision_interpolated_list = [0]
    [precision_interpolated_list.append(e) for e in precision_list]

    for i in range(len(precision_interpolated_list) - 1, 0, -1):
        precision_interpolated_list[i - 1] = max(precision_interpolated_list[i - 1], precision_interpolated_list[i])

    plt.plot(recall_list, precision_list)
    plt.plot(interpol_points, precision_interpolated_list, '--r', label='Interpolated precision')
    plt.title("Precision-Recall-Curve w/ Smoothing")
    plt.xlabel('recall')
    plt.ylabel('precision')
    plt.legend(['Original','Smoothed'])
    plt.show()

    cp_ap = 0
    for i in range(1, len(precision_interpolated_list)):
        if interpol_points[i] - interpol_points[i - 1] != 0:
            cp_ap += (interpol_points[i] - interpol_points[i - 1]) * precision_interpolated_list[i]

    print(f"AP: {cp_ap}")

    # 11 point interpolation
    # generate 11 equally distanced points b/w 0 and 1
    interpol_points = np.linspace(0, 1, 11)
    precision_interpolated_list = [precision_interpolated(precision_list, recall_list, rec) for rec in interpol_points]


    plt.plot(recall_list, precision_list)
    plt.plot(interpol_points, precision_interpolated_list, 'or', label='11-point interpolated precision')
    plt.title("Precision-Recall-Curve w/ 11-Point-Interpolation")
    plt.xlabel('recall')
    plt.ylabel('precision')
    plt.legend(["Original", "Interpolated"])
    plt.show()

    cp_ap11 = 1 / 11 * sum(precision_interpolated_list)
    print(f"ap11: {cp_ap11}")

predictionList = []

# start arguments
parser = argparse.ArgumentParser(description='Test the trained tesseract.')
parser.add_argument('--input', type=str, dest='input', required=True, help='Testdata input directory')
parser.add_argument('--output', type=str, dest='output', required=True, help='Output directory for processed captchas')
parser.add_argument('--name', type=str, dest='name', required=True, help='Name of the tesseract ".traineddata"')

args = parser.parse_args()
DIR_INPUT = args.input
DIR_OUTPUT = args.output
DATASET_NAME = args.name


os.makedirs(DIR_INPUT, exist_ok=True)
os.makedirs(DIR_OUTPUT + "/success/", exist_ok=True)
os.makedirs(DIR_OUTPUT + "/failed/", exist_ok=True)

total = 0
images = 0
num_captchas_correct = 0
for file in os.listdir(DIR_INPUT):
    images += 1
    image = Image.open(DIR_INPUT + "/" + file)
    #image = ImageOps.invert(image)
    #image = ImageEnhance.Brightness(image).enhance(10)
    #imageArray = numpy.array(image)
    #imageArray = imageArray[:, :, ::-1].copy()
    #image.save("enhanced.tif")
    #PSM: 10 = Single character, 6 = block of text
    raw_text = pytesseract.image_to_string(image, lang=DATASET_NAME, config='--psm 7 --oem 3 -c tessedit_char_whitelist=ABCEFGHJKLMNPRTUXY ')
    target = file.split(".")[0]
    if str(raw_text) == str(target):
        num_captchas_correct += 1
#    print(f"Output: {raw_text} Percent coincidence: {round(SQ(None, target, raw_text).ratio()*100,2)}%")
    total += SQ(None, target, raw_text).ratio()
    tess_data = pytesseract.image_to_data(image, lang=DATASET_NAME, output_type=pytesseract.Output.DICT, config='--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHJKLMNPRSTUXY')
    data = tess_data
    n_boxes = len(data['level'])
    img = cv2.imread(DIR_INPUT + "/" + file)
    for i in range(n_boxes):
        if data['text'][i] is not "":
            prediction = predictListObject(target)
            prediction.is_tp = False
            if str(raw_text) == str(target):
                prediction.is_tp = True
            prediction.score = float(data['conf'][i])
            predictionList.append(prediction)
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, "conf: " + str(prediction.score), (0, 60), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 0))
        if str(raw_text) == str(target):
            cv2.imwrite(DIR_OUTPUT + "/success/" + target + ".tif", img)
        else:
            cv2.imwrite(DIR_OUTPUT + "/failed/" + target + ".tif", img)


    cv2.imshow("Test", img)
    #print(json.dumps(tess_data, indent=3))
    cv2.waitKey(50)


print(f"Total character correctness: {round((total/images)*100,2)}%")
print(f"Total captcha correctness: {round((num_captchas_correct/images)*100,2)}%")

print(predictionList)
plotPRC(predictionList, images)