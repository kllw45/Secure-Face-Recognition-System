from face_detection import *
from face_feature import *
from pq import *
from seal import *
from PIL import Image

## 人脸检测部分
in_dirPath = './data/face'  #原始照片路径
out_dirPath = './data/person'  #提取的人脸路径
margin = 8

# 实例化人脸检测类FaceDetection的对象
face_detetor = FaceDetector()
# 人脸识别类
face_recognizer = FaceRecognizer()
#加载模型
pq = pickle.load(open('./static/model/pq_model.pkl', 'rb'))

## 全同态加密部分
scale = 2.0 ** 32
# 创建空的加密参数
parms = EncryptionParameters(scheme_type.ckks)
parms.load('./keys/parms.bin')
# 接下来创建SEALContext，这个类会检查加密参数有效性
context = SEALContext(parms)
# 创建CKKS专有的Encoder，用于batch操作
ckks_encoder = CKKSEncoder(context)
# 导入公钥和私钥
public_key = PublicKey()
public_key.load(context, './keys/pub_key.bin')
# 创建encryptor用于加密，decryptor用于解密，evaluator用于操作(加乘)
encryptor = Encryptor(context, public_key)

def face_detect(fileName):
    # 遍历输入文件夹中的每一个图片文件
    in_filePath = os.path.join(in_dirPath, fileName)  #获取in_dirPath文件夹中第一个文件
    out_filePath = os.path.join(out_dirPath, fileName)  #获取out_filePath文件夹中第一个文件
    image_3d_array = np.array(Image.open(in_filePath))  #将图像数组转化为numpy数组

    # 人脸框、关键点检测
    box_2d_array, point_2d_array = face_detetor.detect_image(image_3d_array, margin)
    face_quantity = len(box_2d_array)
    if face_quantity > 1 or face_quantity == 0:
        print('文件路径为%s的图片检测出的人脸数目等于%d，' %(in_filePath, face_quantity))
    if face_quantity == 0:
        return 1  #没有检测到人脸

    box_1d_array = box_2d_array[0]
    point_1d_array = point_2d_array[0]
    # 人脸区域仿射变换
    affine_image_3d_array = get_affine_image_3d_array(image_3d_array,
            box_1d_array, point_1d_array)
    affine_image = Image.fromarray(affine_image_3d_array)
    # 变换后的图像保存--注册库
    affine_image.save(out_filePath)


    ## 人脸特征提取部分
    np.set_printoptions(threshold=6)
    result=face_recognizer.load_database(np.array(affine_image_3d_array))
    temp1=np.array(result[0][:128]) #设置两个临时变量存储人脸标签和人脸数据
    temp2=np.array(result[0][:])
    print(temp1)

    ## 标签提取并做特征压缩
    query=temp1.reshape((1, 128)).astype(np.float32)# 将人脸标签数据格式化

    #加密
    encoded_query=pq.encode(query) ##此时数据形式为[[]]双重中括号
    label=array_to_str(encoded_query[0])

    #读取需要加密的人脸数据
    res = temp2.reshape((1, 512)).astype(np.float)# 将人脸特征数据格式化
    data = res[0].tolist()
    #将数据编码为明文
    plain = ckks_encoder.encode(data, scale)
    #加密
    cipher = encryptor.encrypt(plain)
    cipher.save('./cipher.bin')

    return label, data  #提取了人脸数据并且加密成功
