#PQ 乘积量化
import nanopq
import pymysql
import numpy as np
import pickle
"""
判断问题：
1.直接使用欧氏距离
2.余弦距离
3.KL散度
"""

##1.欧氏距离
def euclidean_distance(x,y):  ###x,y为数组
    d=np.sqrt(np.sum(pow(np.array(x)-np.array(y), 2)))
    return d
##2.余弦距离
def cosine_distance(x,y):
    inner_product = np.dot(np.array(x), np.array(y))  ##内积
    d = inner_product / ((np.sqrt(np.sum(pow(np.array(x), 2)))) * (np.sqrt(np.sum(pow(np.array(y), 2)))))
    return d
##3.KL散度
def kullback_leibler_divergence(x,y):
    vector1=np.array(x)
    vector2=np.array(y)
    vector12 = np.array(x + y)
    norm_vector1 = (vector1 - np.min(vector12)) / (np.max(vector12) - np.min(vector12))
    norm_vector2 = (vector2 - np.min(vector12)) / (np.max(vector12) - np.min(vector12))
    div = np.sum(norm_vector1 * (np.log2((norm_vector1 + 1e-7) / (norm_vector2 + 1e-7))))
    return div


###转化为数据库存储的字符串
def array_to_str(x):
    store_data = ""
    for data in x:
        store_data = store_data + str(data) + "|"
    store_data=store_data.strip("|")
    return store_data

###数据库中存储数据转化为数组,进行后续操作
def str_to_array(x):
    x=x.split("|")
    x = [int(val) for val in x]
    x=np.array(x)
    return x

#从文件中读取人脸数据标签
def getvalues(n,path):
    with open(path,"+r") as f:
        buf = f.read()
        buf = buf.strip('[').strip(']').split()
        arr1 = np.array(buf[:n])
        arr = arr1.reshape((1, n)).astype(np.float32)
        return arr
    
#从文件中读取需要加密的人脸数据
def getvalues2(n,path):
    with open(path,"+r") as f:
        buf = f.read()
        buf = buf.strip('[').strip(']').split()
        arr1 = np.array(buf[:n])
        arr = arr1.reshape((1, n)).astype(np.float)
        return arr
    
###找到三个最小候选向量,若要增加候选数量，继续补充即可
def FindList3MinNum(result,query_array):
    min1,min2,min3=None,None,None
    for l in result:
        if min1 is None or euclidean_distance(query_array,str_to_array(min1[0]))>euclidean_distance(query_array,str_to_array(l[0])):
            min1,l=l,min1
        if l is None:
            continue
        if min2 is None or euclidean_distance(query_array,str_to_array(min2[0]))>euclidean_distance(query_array,str_to_array(l[0])):
            min2,l=l,min2
        if l is None:
            continue
        if min3 is None or euclidean_distance(query_array,str_to_array(min3[0]))>euclidean_distance(query_array,str_to_array(l[0])):
            min3=l
    return [min1,min2,min3]