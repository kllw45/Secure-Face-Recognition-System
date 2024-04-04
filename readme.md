##  项目说明

###  环境安装

基于python3.6进行环境搭建，所依赖的库见`requirements.txt`

###  数据库创建

使用`face.sql`创建一个名为face的数据库，库中有一个face的表，mysql版本为5.7.26

### 文件目录

```
│  appWeb.py
│  KeyGen.py
│  localRecognition.py
│  localRegister.py
│  pq_train.py
│  requirements.txt
│  saveImg.py
│  seal.pyd
│  
│          
├─data
│  ├─face
│  │      
│  └─person
│          
├─keys
│      
├─static
│  │  anti_spoof_predict.py
│  │  generate_patches.py
│  │  utility.py
│  │  
│  ├─css
│  │          
│  ├─data_io
│  │          
│  ├─ico
│  │          
│  ├─js
│  │      
│  ├─model
│  │  │  pq_model.pkl
│  │  │  
│  │  ├─anti_spoof_models
│  │  │      
│  │  ├─detection_model
│  │  │      
│  │  ├─faceapi_models
│  │  │      
│  │  ├─insightFace_model
│  │  │      
│  │  └─mtcnn_model
│  │          
│  ├─model_lib        
│  
│          
├─templates  

    
        
```

从上到下，项目目录中`appWeb.py`为项目的入口文件，可以启动服务器；`keyGen.py`是秘钥生成文件，能够生成项目中需要的秘钥；`localRecognition.py`是人脸识别文件，可以进行活体检测和人脸识别；`localResigter.py`是人脸录入文件，可以将人脸录入到数据库；`pq_train.py`文件是利用人脸数据库来进行基于乘积量化的特征压缩模型的训练的；`saveImg.py`可以将人脸图片批量录入到数据库中，形成人脸数据库，在启动整个项目前，需要先运行次文件，形成人脸数据库；`seal.pyd`是在python3.6环境下编译形成的seal库；`data`中放置项目运行中临时人脸文件；`keys`放置全部秘钥文件；`static`放置静态资源，包括了`css、js`等相关文件和前端图片以及项目模型。其中，`pq_model.pkl`是预分类中进行人脸特征压缩的模型，`anti_spoof_models`里面是活体检测的模型，`detection_model`是活体检测时用于确定人脸的模型，`faceapi_models`是前端页面中定位人脸和确定人脸清晰度的模型，`insightFace_model`是用于人脸特征提取的模型，`mtcnn_model`是人脸检测和对齐的模型；`templates  `中放置了前端的`html`文件。所有的模型文件需要另外下载，[下载链接](https://pan.baidu.com/s/1OjbYRnJLa71VXduK1gqCcg?pwd=s103 )，下载完成之后，把model文件夹放在static文件夹下即可。

###  项目运行

在项目根目录处终端输入命令`python appWeb.py`然后浏览器访问localhost:5000即可，须确保端口5000没有被占用，尽可能使用谷歌浏览器在光线不那么强的情况下实验

**人脸录入**时可以选择图片录入或是拍摄录入，选择图片录入后点击填写信息，会有**没有开启摄像头的报错**，不用管；拍摄录入时先打开摄像头，然后选择自动拍照，当人脸识别度大于0.9时就会自动拍摄并跳转到填入信息的界面，这时就可以填入信息进行录入，录入信息后等待一会，数据库中就会保存好信息，

**人脸识别**只有拍摄这一种方式，同样是会自动拍摄，流程是打开摄像头，然后选择自动拍摄，当人脸识别度大于0.9时就会自动拍摄并上传图片进行人脸识别，识别的结果会反馈到前端，识别成功会返回用户的姓名；识别不成功会返回人脸不匹配，10次不匹配就会让用户录入信息；如果是非活体会返回非活体信息。