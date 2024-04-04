var nav = new Vue({
    el: "#nav",
    data: {
    }
});
var content = new Vue({
    el: "#content",
    data: {
        uploadpic: false,   //用于网页显示的，如果uploadpic为true说明用户点击了上传文件，则显示文件上传按钮
        takepic: false,   //用于网页显示的，如果takepic为true说明用户点击了拍照，则显示拍照按钮
        user_choice: true,    //用于网页显示的，如果user_choice为true说明用点了返回，则显示图片上传或拍照选择
        resultInfo: false,     //用于网页显示的，如果resultInfo为true说明用户上传了信息，展现结果
        resultInfo_succ: false,   //信息录入成功与否的结果界面
        infoAdd: false,   //当检测到人脸时，用户登记信息的界面      
        fileList: [],

        button_title: '上传信息',
        button_icon: 'el-icon-upload2',
        button_disable: false,

        username: '',
        imgSrc: '',  //待上传的照片
        imgSrc2:'',  //用于信息填写界面的头像

        mediaStreamTrack: {},
        video_stream: '',  //视频stream
        videoWidth: 1920,
        videoHeight: 1080,
        canvas: null,   //摄像头拍照的canvas
        context: null,    //用于画摄像头照片的
        cav2: null,   //信息填写界面的canvas

        get_photo: true,    //用户是否拍照了
        get_cam: false,    //是否获取了摄像头
        timer: null,    //timer是定时器，用于实时检测人脸

        autoDetect: false,    //自动识别并显示结果
        autoDetect_dev: false,    //自动识别并显示结果(测试使用)

        multi_up: false,  //批量上传
        upload_num: 1,

        name_label: [],
        face_feature: [],
        face_encrypt: [],
        face_decrypt: [],
        encrypt_base64: null,
        button_feature: false,
        button_encrypt: false,
        button_decrypt: false,
        loadtip: '加载更多'
    },
    async mounted(){   //页面打开时加载faceapi
        await Promise.all([
            /*this.$loading({
                lock: true,
                text: '正在加载神经网络',
                spinner: 'el-icon-loading',
                background: 'rgba(0, 0, 0, 0.7)'
              }),*/
            faceapi.nets.tinyFaceDetector.loadFromUri('/static/model/faceapi_models'),    //人脸检测网络
            faceapi.nets.faceLandmark68TinyNet.loadFromUri('/static/model/faceapi_models'),   //人脸特征标记网络       
        ]).then(this.$message.success('前端人脸识别神经网络加载成功！'));
        await faceapi.detectAllFaces(document.getElementById('cav2'), new faceapi.TinyFaceDetectorOptions())
                    .withFaceLandmarks(true);
        // this.$loading().close();
    },
    methods: {
        pic_upload() {    //用户点击了上传图片
            this.uploadpic = true;
            this.user_choice = false;
        },
        take_pic() {   //用户选择了拍照
            this.takepic = true;
            this.user_choice = false;
        },
        changenum(s) {
            if(s)
            {
                this.upload_num = 100;
            }
            else{
                this.upload_num = 1;
            }
        },
        handleRemove(file, fileList) {
            console.log(file, fileList);
        },
        handlePreview(file) {
            console.log(file);
        },
        handleExceed(files, fileList) {
            this.$message.warning(`仅允许上传1个文件，当前选择了 ${files.length} 个文件，共选择了 ${files.length + fileList.length} 个文件`);
        },
        submit(){
            this.$refs.upload.submit();   //这个会触发addInfo()
        },
        handleSuccess(res, file, fileList){
            if(res.data['code'] == 0) {
                this.$message.success("文件上传成功");
            }
            else {
                this.$message.error("文件上传失败");
            }
        },
        handelError(res, file, fileList) {
            this.$message.error("文件上传失败，请检查网络连接");
        },
        waiting: function() {
            this.$message('敬请期待');
        },
        back_choice(page) {   //用户点击了返回按钮
            if(page == 1)   //从上传图片点击的返回
            {
                this.uploadpic = false;
            }
            else if(page == 2)
            {
                this.takepic = false;
                this.closeCamera();
            }
            else if(page == 3)
            {
                this.infoAdd = false;  //关闭用户信息填写界面
            }
            this.resultInfo = false;
            this.user_choice = true;
        },
        //用户选择图片并填写信息
        addInfo(parms) {
            console.log(parms.file);
            const fr = new FileReader();
            fr.readAsDataURL(parms.file);
            fr.onload = async (fileURL) => {
                //将人脸图片放入img标签，方便检测人脸
                var user_img = document.getElementById("userFile");
                user_img.src = fileURL.target.result;
                //检测人脸
                const detections = await faceapi.detectAllFaces(user_img, new faceapi.TinyFaceDetectorOptions())
                    .withFaceLandmarks(true)
                    .withFaceDescriptors();
                console.log(detections.length);
                //绘制用户头像
                var ret = await this.drawPhoto(detections, user_img);
                if(ret == 0)
                {
                    this.imgSrc = user_img.src;   //用户选择的图像文件
                    this.imgSrc2 = this.cav2.toDataURL('image/jpeg');   //信息填写界面用户头像
                    this.uploadpic = false;   //关闭图像上传界面
                    this.infoAdd = true;   //显示用户信息填写界面
                }
                else
                {
                    this.$message.warning('您选择的图片中没有检测到清晰的人脸，请重新选择');                    
                }
            }
        },
        getCamera(){
            //获取canvas画布
            this.canvas = document.getElementById('canvasCamera');
            this.context = this.canvas.getContext('2d');
            //旧版本浏览器可能不支持mediaDevices，先设置空的对象
            if(navigator.mediaDevices === undefined) {
                navigator.mediaDevices = {};
            }
            //支持的版本
            navigator.mediaDevices
            .getUserMedia({
                audio:false,
                video:true
            })
            .then((stream) => {
                //调用摄像头成功
                this.mediaStreamTrack = typeof stream.stop === "function" ? stream : stream.getTracks()[0];
                this.video_stream = stream;
                this.$refs.video.srcObject = stream;
                this.$refs.video.play();
                this.get_photo = true;
                this.get_cam = true;
                this.timer = setInterval(() => {this.beginDetection()}, 200);   //开始实时人脸检测
            })
            .catch(err => {
                console.log(err);
            });
        },
        //手动拍照
        setImage(){
            console.log('拍照');
            if(this.get_cam)
                this.get_photo = false;
        },
        //重拍
        reTake() {
            this.get_photo = true;
        },
        //打开摄像头
        openCamera() {
            if(!this.get_cam)
            {
                console.log('打开摄像头');
                this.getCamera();                
            }
        },
        //关闭摄像头
        closeCamera() {
            if(this.get_cam)
            {
                clearInterval(this.timer);   //关闭实时人脸检测
                this.$refs.video.srcObject.getTracks()[0].stop();
                this.get_cam = false;
            }
        },
        async beginDetection(){  //检测人脸并画出框框
            if(!this.get_photo)  //如果已经拍照了，则直接返回
                return ;
            if(this.resultInfo)  //如果已经有结果页面了则返回
                return ;
            //将摄像头照片绘制
            this.context.drawImage(
                this.$refs.video,
                0,
                0,
                this.videoWidth,
                this.videoHeight
            );
            //获取图片base64链接
            this.imgSrc = this.canvas.toDataURL('image/jpeg');

            const input = this.canvas;
            const detections = await faceapi.detectAllFaces(input, new faceapi.TinyFaceDetectorOptions())
                                            .withFaceLandmarks(true);
            const displaySize = { width: input.width, height: input.height };
            const canvas = this.$refs.overlay;   //用于画人脸上的方框的
            canvas.getContext('2d').clearRect(0, 0, this.videoWidth, this.videoHeight);
            await faceapi.matchDimensions(canvas, displaySize);
            const resizedDetections = await faceapi.resizeResults(detections, displaySize);
            await faceapi.draw.drawDetections(canvas, resizedDetections);
            if(this.autoDetect)   //如果开启了自动拍照就在检测出人脸后弹出信息填写界面
            {
                var ret = await this.drawPhoto(detections, input);
                if(ret == 0)  //有人脸并已经绘制到cav2上面，则弹出信息填写界面
                {
                    this.imgSrc2 = this.cav2.toDataURL('image/jpeg');  //用户信息填写界面的头像
                    this.closeCamera();
                    this.takepic = false;    //关闭摄像头页面
                    this.infoAdd = true;    //打开信息填写页面
                }
            }
            //以下代码供方便测试
            if(this.autoDetect_dev)
            {
                var ret = await this.drawPhoto(detections, input);
                if(ret == 0)  //有人脸并已经绘制到cav2上面，则弹出信息填写界面
                {
                    this.get_photo = false;
                }               
            }
            //随时删除
        },
        //检测到人脸后绘制用户头像
        //return 0表示有识别度不小于0.9的头像并绘制成功，1表示没有头像被绘制
        async drawPhoto(detections, input) {
            this.cav2 = document.getElementById("cav2");
            const cav2 = this.cav2.getContext("2d");
            for(var i = 0; i < detections.length; ++i)
            {
                if(detections[i].detection.classScore < 0.9)  //如果人脸识别度小于0.9就继续
                    continue;
                var x = detections[i].detection.box.x;
                var y = detections[i].detection.box.y;
                var width = detections[i].detection.box.width;
                var height = detections[i].detection.box.height;
                var add_w = 0;
                var add_h = 0;
                if(width < 210)   //截取210 * 294尺寸的头像
                {
                    add_w = (210 - width) / 2;
                    x -= add_w;
                    width = 210;
                } else if(width > 210)
                {
                    x -= 10;  //稍微往左一点
                    width +=10;
                }
                if(height < 294)
                {
                    add_h = (294 - height) / 2;
                    y -= add_h;
                    height = 294;
                } else if(height > 294)
                {
                    y -= 10;   //稍微往上一点
                    height += 10;
                }
                this.cav2.width = width;
                this.cav2.height = height;
                cav2.drawImage(input, x, y, width, height, 0, 0, width, height);
                // this.imgSrc = document.getElementById("cav2").toDataURL('image/jpeg');

                return 0;  //绘制完成
            }

            return 1;   //没有东西被绘制
        },
        addInfo2(){   //手动拍照时填写信息
            if(this.imgSrc){
                //随时删除
                if(this.autoDetect_dev)
                {
                    this.imgSrc2 = this.cav2.toDataURL('image/jpeg');
                    this.get_photo = true;
                }
                //随时删除上面的
                this.closeCamera();
                this.takepic = false;    //关闭摄像头页面
                this.infoAdd = true;    //打开信息填写页面
            }
            else{
                this.$message.warning('还未拍照，请先拍照');
            }
        },
        async uploadInfo(){   //上传信息
            if(!this.imgSrc)
            {
                this.$message.warning('未获取到照片，请先拍照或者上传图片');
                return ;
            }
            if(this.username.length == 0)
            {
                this.$message.warning('需要填写姓名');
                return ;
            }
            //改变按钮状态
            this.button_title = '正在上传';
            this.button_icon = 'el-icon-loading';
            this.button_disable = true;
            const file = this.imgSrc;
            const filename = 'pic.jpg';
            const pic = this.dataURLtoFile(file, filename);
            var data = new FormData();
            data.append('file', pic);  //注意后台参数为file
            data.append('username', this.username);
            await axios.post('/saveFace', data, {'Content-type':'multipart/form-data'})
            .then(response => {
                if(response.status == 200)
                {
                    if(response.data.code == 0){ 
                        this.resultInfo_succ = true;
                        this.$message.success(`feedback: ${response.data.msg}`);
                        this.putData(response.data.label);
                    }
                    else{
                        this.resultInfo_succ = false;
                        this.$message.error(`feedback: ${response.data.msg}`);
                    }
                }
                else {
                    this.resultInfo_succ = false;
                    this.$message.error('服务器出错');
                }
                this.infoAdd = false;
                this.resultInfo = true;
                this.username = '';                
            })
            .catch(error => {
                this.$message.error('网络连接错误');
            });
            //改变按钮状态
            this.button_title = '上传信息';
            this.button_icon = 'el-icon-upload2';
            this.button_disable = false;
        },
        //上传图片
        upLoad() {
            if(this.imgSrc) {
                const file = this.imgSrc;
                const filename = 'pic.jpg';
                const pic = this.dataURLtoFile(file, filename);
                var data = new FormData();
                data.append('file', pic);  //注意后台参数为file
                axios.post('/upload', data, {'Content-type':'multipart/form-data'})   //注意flask需要'Content-type':'multipart/form-data'
                .then(response => {
                    if(response.data['code'] == 0)
                    {
                        console.log(response.data['msg']);
                        this.$message.success("照片上传成功");
                    }
                    else
                    {
                        this.$message.error("照片上传失败：\n" + response.data['msg']);
                    }
                })
                .catch(err => {
                    this.$message.error("照片上传失败，请检查网络连接");
                });
            }
            else {
                this.$message.error('没有图像被上传');
            }
        },
        //将dataURL转换为图片，代码来自http://www.manongjc.com/detail/23-xcimqtfllxhtqnm.html
        dataURLtoFile(dataurl, filename) {
            var arr = dataurl.split(',')
            var mime = arr[0].match(/:(.*?);/)[1]
            var bstr = atob(arr[1])   //base64解码
            var n = bstr.length
            var u8arr = new Uint8Array(n)
            while (n--) {
                u8arr[n] = bstr.charCodeAt(n)
            }
            return new File([u8arr], filename, { type: mime })
        },
        putData(label){
            this.name_label.push({username: this.username, label: label});
        },
        async getPlainFeature(){
            if(this.face_feature.length > 0)
                return ;
            this.button_feature = true;   //把按钮改成加载中
            await axios.get('/getFaceFeature')
            .then((response) => {
                var feature = '['
                for(var i = 0; i < response.data.length; ++i)
                {   
                    if(i > 9)
                        if(i % 10 == 0)
                            feature += '<br />';
                    feature += response.data[i].toFixed(6);
                    if(i < response.data.length - 1)
                        feature += ', '
                }
                feature += ']';
                this.face_feature.push({face_feature: feature});
            })
            .catch((error) => {
                this.$message.error('获取人脸特征失败');
            });
            this.button_feature = false;   //解除加载中
        },
        async getEncryptData(){
            if(this.face_encrypt.length > 0)
                return ;
            this.button_encrypt = true;   //把按钮改成加载中
            if(this.face_feature.length == 0)
            {
                this.$message.warning('请先获取明文数据');
            }
            else{
                await axios.get('/getCipher')
                .then((response) => {
                    this.loadtip = '加载更多';
                    this.encrypt_base64 = response.data;
                    this.face_encrypt.push({face_encrypt: this.encrypt_base64.substring(0, 512)});  //显示前512 base64编码
                })
                .catch((error) => {
                    this.$message.error('获取加密数据失败');
                });
            }
            this.button_encrypt = false;  //解除加载中
        },
        async getDecryptData(){
            if(this.face_decrypt.length > 0)
                return ;
            this.button_decrypt = true;   //把按钮改成加载中
            if(this.face_encrypt.length == 0)
            {
                this.$message.warning('请先获取密文数据');
            }
            else {
                await axios.get('/decryptCipher')
                .then((response) => {
                    var feature = '['
                    for(var i = 0; i < response.data.length; ++i)
                    {
                        if(i > 9)
                            if(i % 10 == 0)
                                feature += '<br />';
                        feature += response.data[i].toFixed(6);
                        if(i < response.data.length - 1)
                            feature += ', '
                    }
                    feature += ']';
                    this.face_decrypt.push({face_decrypt: feature});
                })
                .catch((error) => {
                    this.$message.error('获取解密数据失败');
                });
            }
            this.button_decrypt = false;  //解除加载中
        },
        loadmore(){
            if(this.face_encrypt[0].face_encrypt.length < this.encrypt_base64.length)
                this.face_encrypt[0].face_encrypt += this.encrypt_base64
                                            .substring(this.face_encrypt[0].face_encrypt.length, this.face_encrypt[0].face_encrypt.length + 40000);
            else
            {
                console.log('加载完毕');
                this.loadtip = '加载完毕';
                this.$forceUpdate();
            }
        }
    }
});