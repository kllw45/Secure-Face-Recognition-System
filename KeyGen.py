from seal import *
##  用于生成ckks中的参数和四个秘钥
#创建加密参数
parms = EncryptionParameters(scheme_type.ckks)
poly_modulus_degree = 4096  #对于4096阶多项式，多项式系数的模数不超过218比特
parms.set_poly_modulus_degree(poly_modulus_degree)
#设置加密参数的多项式系数模数，使用CoeffModulus.Create()可以方便地生成可用于Batch的素数
#Batch化的密文可以加速运算
parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, [36, 32, 36]))
#ckks需要设置缩放因数scale
#对于scale的选择，比较好的策略是：
# 1.	选择60bit的素数作为coeff_modulus的第一个素数，在解密时，这使得精度最高
# 2.	选择另一个60bit的素数作为coeff_modulus的最后一个素数，因为最后一个素数要求至少不小于比其它素数中最大的那个
# 3.	中间的素数彼此相近，即具有相同比特数
scale = 2.0 ** 32

#接下来创建SEALContext，这个类会检查加密参数有效性
context = SEALContext(parms)
#创建CKKS专有的Encoder，用于batch操作
ckks_encoder = CKKSEncoder(context)
#Batch化的CKKS有poly_modulus_degree / 2个槽
slot_count = ckks_encoder.slot_count()

#接着创建密钥
keygen = KeyGenerator(context)
public_key = keygen.create_public_key()
secret_key = keygen.secret_key()
rl_key = keygen.create_relin_keys()
gal_key = keygen.create_galois_keys()

parms.save('./keys/parms.bin')
print("保存parms成功...")
public_key.save('./keys/pub_key.bin')
print("保存公钥成功...")
secret_key.save('./keys/sec_key.bin')
print("保存私钥成功...")
rl_key.save("./keys/rl_key.bin")
print("保存RelinKey成功...")
gal_key.save("./keys/gal_key.bin")
print("保存GaloisKey成功...")