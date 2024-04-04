from face_detection import *
from face_feature import *
from pq import *
from PIL import Image
from seal import *
import pymysql

## 人脸检测部分
# 解析传入的参数
in_dirPath = 'E:/download/img_align_celeba' # 人脸数据库读取文件夹
out_dirPath = './data/person'
margin = 8
## 标签提取并做特征压缩
N, Nt, D = 10000, 2000, 8
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
#创建一个数组，用于存储需要加密的信息
data = []
#连接数据库
db=pymysql.connect(host="localhost",port=3306,user="root",password="root")   ###对应端口，用户，密码记得改
cursor=db.cursor()   ###创建游标对象来执行sql语句
#选定对应的数据库
sql="use face;"
cursor.execute(sql)

# 遍历输入文件夹中的每一个图片文件
num = 1000
while num < 2000:
    if num < 10:
        name = '00000'+str(num)
        fileName = name+'.jpg'
    elif  num in range(10, 100, 1):
        name = '0000'+str(num)
        fileName = name+'.jpg'
    else:
        name = '00'+str(num)
        fileName = name+'.jpg'
    num+=1
    in_filePath = os.path.join(in_dirPath, fileName)  #获取in_dirPath文件夹中第一个文件
    out_filePath = os.path.join(out_dirPath, fileName)  #获取out_filePath文件夹中第一个文件
    image_3d_array = np.array(Image.open(in_filePath))  #将图像数组转化为numpy数组

    # 人脸框、关键点检测
    box_2d_array, point_2d_array = face_detetor.detect_image(image_3d_array, margin)
    face_quantity = len(box_2d_array)
    if face_quantity > 1 or face_quantity == 0:
        print('文件路径为%s的图片检测出的人脸数目等于%d，' %(in_filePath, face_quantity))
        continue
    if face_quantity == 0:
        print('没有检测到人脸')  #没有检测到人脸
        continue

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

    ## 数据库保存部分
    #查询最大的id值
    sql_attain="select MAX(Id) from face"
    cursor.execute(sql_attain)
    result=cursor.fetchall()
    if result[0][0]: #判断数据库中是否有数据
        id=result[0][0]+1
    else:
        id=1
    ##存入二进制文件
    filepath="E:/file/SecureGame/demo0604/cipher.bin"  ###必须是绝对路径
    #添加
    sql_insert="insert into face(Id,name,label,face_data) values ('{}','{}','{}',LOAD_FILE('{}'))".format(id,name,label,filepath)
    cursor.execute(sql_insert)

    ## 删除一些运行过程中的临时文件
    os.remove('cipher.bin')
    os.remove(out_filePath)
    print('成功保存'+fileName+'图片')

print('保存人脸数据库程序运行结束')
