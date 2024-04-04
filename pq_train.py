from face_detection import *
from face_feature import *
from PIL import Image
import pymysql
import nanopq

## 人脸检测部分
# 解析传入的参数
in_dirPath = 'path' #  人脸数据库
out_dirPath = './data/person'
margin = 8
## 标签提取并做特征压缩
# 实例化人脸检测类FaceDetection的对象
face_detetor = FaceDetector()
# 人脸识别类
face_recognizer = FaceRecognizer()
#创建一个矩阵，用于存储需要加密的信息
data_train=np.array([[0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0]]).astype(np.float32)

# 遍历输入文件夹中的每一个图片文件
num = 1
while num < 10:
    if num < 10:
        name = '00000'+str(num)
        fileName = name+'.jpg'
    elif  num in range(10, 100, 1):
        name = '0000'+str(num)
        fileName = name+'.jpg'
    elif num in range(100,1000,1):
        name = '000'+str(num)
        fileName = name+'.jpg'
    else:
        name='00'+str(num)
        fileName= name+'.jpg'
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
    #temp2=np.array(result[0][:])
    #print(temp1)
    query = temp1.reshape((1, 128)).astype(np.float32)
    data_train=np.row_stack((data_train,query))           ##将人脸数据的前128维加入到矩阵中

    ## 数据库保存部分
    os.remove(out_filePath)
    #print('成功保存'+fileName+'图片')


print("训练数据准备完成")
#进行训练，并且将模型存储以便利用
pq0=nanopq.PQ(M=8)
pq0.fit(data_train)
pickle.dump(pq0, open('./static/model/pq_model.pkl', 'wb'))
print('模型训练完成')
