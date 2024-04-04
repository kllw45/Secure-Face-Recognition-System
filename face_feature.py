import numpy as np
from pq import *
import cv2
import time
import mxnet as mx
import mxnet.ndarray as nd
from sklearn import preprocessing

def load_model(prefix = './static/model/insightFace_model/model', epoch = 0, batch_size=10):
    symbol, arg_params, auxiliary_params = mx.model.load_checkpoint(prefix, epoch)
    all_layers = symbol.get_internals()
    output_layer = all_layers['fc1_output']
    # context = mx.gpu(0)
    context = mx.cpu(0)
    model = mx.mod.Module(symbol=output_layer, context=context, label_names=None)
    model.bind(data_shapes=[('data', (batch_size, 3, 112, 112))])
    model.set_params(arg_params, auxiliary_params)
    print('执行了一次face_feature模型加载')

    return model


# class FaceVectorizer
class FaceVectorizer(object):
    def __init__(self):
        self.batch_size = 1
        self.model = None
     
    def get_feedData(self, image_4d_array):
        image_list = []
        for image_3d_array in image_4d_array:
            height, width, _ = image_3d_array.shape
            if height!= 112 or width != 112:
                image_3d_array = cv2.resize(image_3d_array, (112, 112))
            image_list.append(image_3d_array)
        image_4d_array_1 = np.array(image_list)
        image_4d_array_2 = np.transpose(image_4d_array_1, [0, 3, 1, 2])
        image_4D_Array = nd.array(image_4d_array_2)
        image_quantity = len(image_list)
        label_1D_Array = nd.ones((image_quantity, ))
        feed_data = mx.io.DataBatch(data=(image_4D_Array,), label=(label_1D_Array,))
        return feed_data

    def get_feature_2d_array(self, image_4d_array):
        if len(image_4d_array.shape) ==  3:
            image_4d_array = np.expand_dims(image_4d_array, 0)
        assert len(image_4d_array.shape) == 4, 'image_ndarray shape length is not 4'
        image_quantity = len(image_4d_array)
        if image_quantity != self.batch_size or not self.model:
            self.batch_size = image_quantity
            self.model = load_model(batch_size=self.batch_size)
        feed_data = self.get_feedData(image_4d_array)
        self.model.forward(feed_data, is_train=False)
        outputs = self.model.get_outputs()
        print('13')
        output_2D_Array = outputs[0]
        print(output_2D_Array)
        print('14')
        output_2d_array = output_2D_Array.asnumpy()
        print('12')
        feature_2d_array = preprocessing.normalize(output_2d_array)
        return feature_2d_array

# class FaceRecognizer
class FaceRecognizer(object):
    def __init__(self):
        self.feature_dimension = 512
        self.face_vectorizer = FaceVectorizer()

    # 人脸数据库, 返回用户人脸特征数组
    def load_database(self, image_3d_array: np.ndarray):
        personId_list = [0]
        print('2')
        self.personId_1d_array = np.array(personId_list)
        self.bincount_1d_array = np.bincount(self.personId_1d_array)
        self.person_quantity = 1
        self.image_quantity = 1
        print('3')
        startTime = time.time()
        batch_size = 1
        imageData_list = []
        count = 0
        print('4')
        self.database_2d_array = np.empty((self.image_quantity, self.feature_dimension))
        imageData_list.append(image_3d_array)
        print('5')
        count += 1
        if count % batch_size == 0:
            print('6')
            image_4d_array = np.array(imageData_list)
            imageData_list.clear()
            print('7')
            self.database_2d_array[count-batch_size: count] = self.face_vectorizer.get_feature_2d_array(image_4d_array)
            print('8')
        if count % batch_size != 0:
            print('6')
            image_4d_array = np.array(imageData_list)
            remainder = count % batch_size
            print('7')
            self.database_2d_array[count-remainder: count] = self.face_vectorizer.get_feature_2d_array(image_4d_array)
            print('8')
        usedTime = time.time() - startTime
        return self.database_2d_array
