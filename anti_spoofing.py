import os
import cv2
import numpy as np
import argparse
import warnings
import time
import torch

from static.anti_spoof_predict import AntiSpoofPredict
from static.generate_patches import CropImage
from static.utility import parse_model_name
warnings.filterwarnings('ignore')
torch.backends.cudnn.benchmark = True

SAMPLE_IMAGE_PATH = "./data/face/"

def PersonTest(image_name, model_dir, device_id):
    model_test = AntiSpoofPredict(device_id)
    image_cropper = CropImage()
    image = cv2.imread(SAMPLE_IMAGE_PATH + image_name)
    image_bbox = model_test.get_bbox(image)
    prediction = np.zeros((1, 3))
    test_speed = 0
    # sum the prediction from single model's result
    for model_name in os.listdir(model_dir):
        h_input, w_input, model_type, scale = parse_model_name(model_name)
        param = {
            "org_img": image,
            "bbox": image_bbox,
            "scale": scale,
            "out_w": w_input,
            "out_h": h_input,
            "crop": True,
        }
        if scale is None:
            param["crop"] = False
        img = image_cropper.crop(**param)
        start = time.time()
        prediction += model_test.predict(img, os.path.join(model_dir, model_name))
        test_speed += time.time()-start

    # draw result of prediction
    label = np.argmax(prediction)
    value = prediction[0][label]/2
    if label == 1:
        print("Image '{}' is Real Face. Score: {:.2f}.".format(image_name, value))
        return 1
    else:
        print("Image '{}' is Fake Face. Score: {:.2f}.".format(image_name, value))
        return 0
