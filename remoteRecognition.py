import time

from seal import *

parms = EncryptionParameters(scheme_type.ckks)
parms.load('./keys/parms.bin')
context = SEALContext(parms)

evaluator = Evaluator(context)
rl_key = RelinKeys()
rl_key.load(context, './keys/rl_key.bin')
gal_key = GaloisKeys()
gal_key.load(context, './keys/gal_key.bin')


# 人脸相似度计算部分
def compute_diff_cipher(file_byte1, file_byte2):
    start = time.clock()
    cipher1 = Ciphertext()
    cipher2 = Ciphertext()
    cipher1.load_bytes(context, file_byte1)
    cipher2.load_bytes(context, file_byte2)
    end = time.clock()
    print('服务端密文载入用时{}'.format(end - start))

    start = time.clock()
    diff = evaluator.sub(cipher1, cipher2)
    evaluator.square_inplace(diff)  # 计算平方
    evaluator.relinearize_inplace(diff, rl_key)  # 使用rl_key可以减少noise budget损耗
    evaluator.rescale_to_next_inplace(diff)  # scale平方后变成了2 ^ 80, 太大了, rescale至2 ^ 40左右

    step = 512
    while True:
        step /= 2
        cipher_temp = evaluator.rotate_vector(diff, int(step), gal_key)
        diff = evaluator.add(diff, cipher_temp)
        if step == 1:
            break
    end = time.clock()
    print('服务端密文计算用时{}'.format(end - start))

    return diff
