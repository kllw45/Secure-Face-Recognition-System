from flask import Flask, render_template, jsonify, request
import os

import localRecognition
from localRegister import face_detect
from localRecognition import face_recognise
from anti_spoofing import PersonTest
import requests
import time

app = Flask(__name__)
app.jinja_env.variable_start_string = '<<'
app.jinja_env.variable_end_string = '>>'    #改变{{}}，不然报错

ret = []  #人脸标签
face_feature = []  #人脸明文特征
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/recognition')
def recognition():
    return render_template('recognition.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/saveFace', methods=['POST'])
def save_face():
    UPLOAD_FOLDER = './data/face'
    username = request.form.get('username')
    res = {'code': 1, 'msg': 'not post'}
    if request.method == 'POST':
        # 如果没有file属性，则返回
        if 'file' not in request.files:
            res['code'] = 1
            res['msg'] = "请上传文件"
            return jsonify(res)
        file = request.files['file']
        # 如果文用户没有上传文件
        if file.filename == '':
            res['code'] = 1
            res['msg'] = '没有文件名'
            return jsonify(res)
        if file:
            file.filename = 'registerpic.jpg'
            print(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
            print("保存图片成功")

            flag_ati = PersonTest(file.filename, "./static/model/anti_spoof_models", 0)
            if flag_ati == 0:
                res['code'] = 1
                res['msg'] = '请不要使用照片注册'
                return jsonify(res)

            start = time.clock()    #开始检测人脸

            global ret, face_feature
            ret, face_feature = face_detect(file.filename)
            if ret == 1:
                res['code'] = 2
                res['msg'] = '未检测到人脸'
                return jsonify(res)
            else:
                #向远程服务器发送人脸数据
                with open('cipher.bin', 'rb') as f:
                    data = {'username': username, 'label': ret}
                    files = {'file': f}
                    header = {'User-Agent':
                                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'}
                    url = 'http://127.0.0.1:5000/serverSaveData'
                    resp = requests.post(url, headers=header, data=data, files=files).json()
                    resp['label'] = ret

                end = time.clock()
                print('注册用时: {} s'.format(end - start))

                return resp

    return jsonify(res)

@app.route('/upload', methods=['POST'])
# @cross_origin()
def upload():
    UPLOAD_FOLDER = './data/face'
    res = {'code': 1, 'msg': 'not post'}
    if request.method == 'POST':
        # 如果没有file属性，则返回
        if 'file' not in request.files:
            res['code'] = 1
            res['msg'] = "请上传文件"
            return jsonify(res)
        file = request.files['file']
        # 如果文用户没有上传文件
        if file.filename == '':
            res['code'] = 1
            res['msg'] = '没有文件名'
            return jsonify(res)
        if file:
            global username
            file.filename=username+'.jpg'
            print(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
            print("保存图片成功")
            return jsonify(res)
    return jsonify(res)

@app.route('/face_re', methods=['POST'])
def face_re():
    UPLOAD_FOLDER = './data/face'
    res = {'code': 1, 'msg': 'not post'}
    if request.method == 'POST':
        # 如果没有file属性，则返回
        if 'file' not in request.files:
            res['code'] = 1
            res['msg'] = "请拍摄照片"
            return jsonify(res)
        file = request.files['file']
        # 如果文用户没有上传文件
        if file.filename == '':
            res['code'] = 1
            res['msg'] = '没有文件名'
            return jsonify(res)
        if file:
            file.filename = 'recognitionpic.jpg'
            print(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))

            start = time.clock()   #开始计时

            ret = face_recognise(file.filename)
            print("识别结果：{}".format(ret))

            end = time.clock()
            print('识别用时: {} s'.format(end - start))

            return jsonify(ret)

    return jsonify(res)

@app.route('/getById', methods=['GET'])
def get_by_id():
    id = int(request.args.get('id'))
    url = 'http://127.0.0.1:5000/serverGetById'
    params = {'id': id}
    resp = requests.get(url, params=params).json()

    return resp

@app.route('/getLabel', methods=['GET'])
def get_label():
    global ret
    return jsonify(ret)

@app.route('/getFaceFeature', methods=['GET'])
def get_face_feature():
    global face_feature
    return jsonify(face_feature)

@app.route('/getCipher', methods=['GET'])
def get_cipher():
    with open('./cipher.bin', 'rb') as f:
        file_data = base64.b64encode(f.read()).decode('utf-8')  # 网络中传输小文件通过base64
    return jsonify(file_data)

@app.route('/decryptCipher', methods=['GET'])
def decrypt_cipher():
    result = localRecognition.decrypt_cipher('./cipher.bin')
    result = result.tolist()

    return jsonify(result[:512])
################远程服务器部分################
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, union
import difflib
import base64
from remoteRecognition import compute_diff_cipher

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost:3306/face'   #连接数据库，face为数据库名
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False   #不回显数据库操作
#关联app
db = SQLAlchemy(app)
#将数据库中face表映射为一个类
class FaceRecord(db.Model):
    # 指定表名
    __tablename__ = 'face'  # 不指定表名的话默认为类名小写
    # 主键
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    label = db.Column(db.String(255))
    face_data = db.Column(db.LargeBinary(65536))
@app.route('/serverSaveData', methods=['POST'])
def server_save_data():
    res = {'code': 1, 'msg': 'not post'}
    if request.method == 'POST':
        if 'file' not in request.files:
            res['code'] = 1
            res['msg'] = '没有文件'
            return jsonify(res)
        file = request.files['file']
        if file.filename == '':
            res['code'] = 1
            res['msg'] = '没有文件名'
            return jsonify(res)
        if file:
            ids = db.session.query(FaceRecord.id).order_by(desc(FaceRecord.id)).all()
            name = request.form.get('username')
            label = request.form.get('label')
            file_data = file.read()  #读取二进制流
            if len(ids) == 0:
                id = 1
            else:
                id = ids[0][0] + 1
            one_record = FaceRecord(id=id, name=name, label=label, face_data=file_data)
            db.session.add(one_record)
            db.session.commit()
            res['code'] = 0
            res['msg'] = 'ok'
            return jsonify(res)

    return jsonify(res)
@app.route('/serverRecFace', methods=['POST'])
def server_rec_face():
    res = {'code': 1, 'msg': 'not post'}
    if request.method == 'POST':
        if 'file' not in request.files:
            res['code'] = 1
            res['msg'] = '没有文件'
            return jsonify(res)
        file = request.files['file']
        if file.filename == '':
            res['code'] = 1
            res['msg'] = '没有文件名'
            return jsonify(res)
        if file:
            # 保存待识别的人脸密文
            # file.save('./cipher1.bin')
            file = file.stream.read()
            label = request.form.get('label')
            allLabel = db.session.query(FaceRecord.id, FaceRecord.label).all()
            data = {'code': 0, 'id': [], 'file': []}
            query_id = []

            for i in range(0, len(allLabel)):
                # 比较标签是否相似，进行预分类
                flag = difflib.SequenceMatcher(None, label, allLabel[i][1]).quick_ratio()
                print("预分类flag: {}".format(flag))
                if flag > 0.8:
                    query_id.append(allLabel[i][0])

            start = time.clock()
            # 读取并存储到bin文件
            ret_face = db.session.query(FaceRecord.id, FaceRecord.face_data)\
                        .filter(FaceRecord.id.in_(query_id)).all()
            end = time.clock()
            print('服务端查询耗时: {} s'.format(end - start))

            start = time.clock()
            for i in range(0, len(ret_face)):
                data['id'].append(ret_face[i][0])
                diff = compute_diff_cipher(file, ret_face[i][1])
                file_data = base64.b64encode(diff.to_string()).decode('utf-8')  # 网络中传输小文件通过base64
                data['file'].append(file_data)

            end = time.clock()
            print('服务端全同态部分耗时: {} s'.format(end - start))
            print(query_id)
            return jsonify(data)

    return jsonify(res)
@app.route('/serverGetById', methods=['GET'])
def server_get_by_id():
    id = int(request.args.get('id'))
    result = db.session.query(FaceRecord.id, FaceRecord.name).filter(FaceRecord.id == id).one()
    ret = {}
    ret['username'] = result[1]

    return jsonify(ret)
################远程服务器部分################

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)