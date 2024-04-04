var nav = new Vue({
    el: "#nav",
    data: {
    }
});
var content = new Vue({
    el: "#content",
    data: {
        take_pic: true,    //用户是否在拍照，人脸识别后就为false
        retInfo: false,    //显示识别信息
        resultInfo_succ: true,   //数据库中是否有信息

        button_title: '开始识别',
        button_icon: 'el-icon-upload el-icon--right',
        button_disable: false,

        mediaStreamTrack: {},
        video_stream: '',  //视频stream
        videoWidth: 1920,
        videoHeight: 1080,
        canvas: null,
        context: null,

        imgSrc: '',  //拍照的图片
        get_photo: true,    //用户是否拍照了
        get_cam: false,    //是否获取了摄像头
        timer: null,    //timer是定时器，用于实时检测人脸

        autoRecognition: false,
        allow_upload: true,
        tabledata: [],
        try_times: 10   //尝试次数，当匹配10次还没有则弹出没有录入人脸的界面
    },
    mounted(){   //页面打开时加载faceapi
        Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri('../static/model/faceapi_models'),
            faceapi.nets.faceLandmark68TinyNet.loadFromUri('../static/model/faceapi_models'),
        ])
    },
    methods: {
        back_choice(page) {   //用户点击了返回按钮
            if(page == 1)
            {
                this.get_photo = true;
                this.take_pic = true;
                this.retInfo = false;
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
        setImage(){
            if(this.get_cam)
                this.get_photo = false;
        },
        //重拍
        reTake() {
            this.get_photo = true;
        },
        //打开摄像头
        openCamera: function() {
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
        async beginDetection() {  //检测人脸并画出框框
            if(!this.get_photo)  //如果已经拍照了，则直接返回
                return ;
            if(this.retInfo)  //如果已经有结果页面了则返回
                return ;
            //绘制摄像头的照片
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
            const canvas = this.$refs.overlay;
            canvas.getContext('2d').clearRect(0, 0, this.videoWidth, this.videoHeight);
            await faceapi.matchDimensions(canvas, displaySize);
            const resizedDetections = await faceapi.resizeResults(detections, displaySize);
            await faceapi.draw.drawDetections(canvas, resizedDetections);
            
            console.log(this.allow_upload);
            if (this.autoRecognition && this.allow_upload)
            {
                this.allow_upload = false;               
                await this.face_recognition(detections);                
            }
        },
        async face_recognition(detections){   //获取匹配器后进行人脸识别
            for(var i = 0; i < detections.length; ++i)
            {
                if(detections[i].detection.classScore < 0.9)
                    continue;
                console.log('执行recognition');
                if(!this.retInfo)  //如果没有返回结果则上传照片
                    await this.upLoad();
                break;
            }
            this.allow_upload = true;            
        },
        async getinfo(userid, ismatch){   //根据userid向数据库查询
            if(ismatch)
                await axios.get('/getById?id='+userid)   //后端返回的是{'len': len(ret), 'result': ret}这种格式的
                .then(response => {
                    this.tabledata = [];
                    this.tabledata.push(
                        {
                            username: response.data.username
                        }
                    );
                    this.try_times = 10;
                    this.take_pic = false;
                    if(this.get_cam)
                        this.closeCamera();  //关闭摄像头
                    this.retInfo = true;
                    this.resultInfo_succ = true;
                    this.$forceUpdate();   //更新页面 
                })
                .catch(error => {
                    this.$message.error('查询失败');
                });
            else
            {
                if(this.try_times-- > 0)
                {
                    this.$notify.info({
                        title: `第${10 - this.try_times}次匹配：`,
                        message: '没有匹配的人脸信息'
                      });
                }
                else   //尝试10次后没有信息则显示未匹配
                {
                    this.try_times = 10;
                    this.take_pic = false;  //关闭拍照界面
                    if(this.get_cam)
                        this.closeCamera();  //关闭摄像头
                    this.autoRecognition = false;   //关闭自动人脸识别
                    this.retInfo = true;
                    this.resultInfo_succ = false;
                }
            }
        },
        //上传图片
        async upLoad() {
            if(!this.autoRecognition && this.get_photo)
            {
                this.$message.error('还未拍照，请先拍照或者打开自动识别');
                return ;
            }

            //改变按钮状态
            this.button_title = '正在上传';
            this.button_icon = 'el-icon-loading  el-icon--right';
            this.button_disable = true;
            if(this.imgSrc) {
                const file = this.imgSrc;
                const filename = 'pic.jpg';
                const pic = this.dataURLtoFile(file, filename);
                var data = new FormData();
                data.append('file', pic);  //注意后台参数为file
                await axios.post('/face_re', data, {'Content-type':'multipart/form-data'})   //注意flask需要'Content-type':'multipart/form-data'
                .then(response => {
                    if(response.data['code'] == 0)
                    {
                        this.getinfo(response.data['id'], true);
                    }
                    else
                    {
                        this.getinfo(-1, false);
                    }
                })
                .catch(err => {
                    this.$message.error("照片上传失败，请检查网络连接");
                });
            }
            else {
                this.$message.error('还未拍照，请先打开摄像头拍照');
            }
            //改变按钮状态
            this.button_title = '开始识别';
            this.button_icon = 'el-icon-upload el-icon--right';
            this.button_disable = false;
        },
        //将dataURL转换为图片，代码来自http://www.manongjc.com/detail/23-xcimqtfllxhtqnm.html
        dataURLtoFile(dataurl, filename) {
            var arr = dataurl.split(',')
            var mime = arr[0].match(/:(.*?);/)[1]
            var bstr = atob(arr[1])
            var n = bstr.length
            var u8arr = new Uint8Array(n)
            while (n--) {
                u8arr[n] = bstr.charCodeAt(n)
            }
            return new File([u8arr], filename, { type: mime })
        }
    }
});