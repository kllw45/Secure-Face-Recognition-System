from localRegister import face_detect
from seal import *
from anti_spoofing import *
import math
import requests
import numpy as np
import base64

parms = EncryptionParameters(scheme_type.ckks)
parms.load('./keys/parms.bin')
context = SEALContext(parms)

secret_key = SecretKey()
secret_key.load(context, './keys/sec_key.bin')
ckks_encoder = CKKSEncoder(context)
decryptor = Decryptor(context, secret_key)


def face_recognise(fileName):
    flag_ati = PersonTest(fileName, "./static/model/anti_spoof_models", 0)
    if flag_ati == 0 :
        print("非活体")
        return {'code': 1, 'msg': '非活体'}  #非活体

    #人脸检测
    label = face_detect(fileName)
    if label == 1:
        return {'code': 2, 'msg': '没有检测到人脸'}  #没有检测到人脸

    #将密文发送至远程服务器
    with open('./cipher.bin', 'rb') as f:
        data = {'label': label}
        files = {'file': f}
        header = {'User-Agent':
                      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'}
        url = 'http://127.0.0.1:5000/serverRecFace'
        resp = requests.post(url, headers=header, data=data, files=files).json()
    if resp['code'] == 0:  #获取到数据
        id = resp['id']
        file = resp['file']
        distance = []

        start = time.clock()
        num = 0
        for i in range(0, len(id)):
            file_data = base64.b64decode(file[i].encode('utf-8'))
            cipher = Ciphertext()
            cipher.load_bytes(context, file_data)
            plain = decryptor.decrypt(cipher)
            ret = ckks_encoder.decode(plain)
            flag_diff = math.sqrt(ret[0])
            distance.append(flag_diff)

            num+=1
            print("decrypted distance (square): {0} \n decrypted distance (root): {1}".format(ret[0], flag_diff))
        print(num)
        end = time.clock()
        print('客户端全同态部分用时: {} s'.format(end - start))
        if len(distance) == 0:  #如果没有数据
            return {'code': 3, 'msg': '没有匹配人脸'}  #没有匹配的人脸

        index = np.argmin(distance)  #找出阈值最小的
        if distance[index] < 0.8:  #人脸识别阈值
            return {'code': 0, 'id': id[index]}

    return {'code': 3, 'msg': '没有匹配人脸'}

def decrypt_cipher(fileName):
    cipher = Ciphertext()
    cipher.load(context, fileName)
    plain = decryptor.decrypt(cipher)
    ret = ckks_encoder.decode(plain)

    return ret
