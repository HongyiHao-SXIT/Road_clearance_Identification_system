const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const originalPreview = document.getElementById('originalPreview');
const annotatedPreview = document.getElementById('annotatedPreview');
const resultArea = document.getElementById('resultArea');
const resultContent = document.getElementById('resultContent');

uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#2563eb';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = '#d1d5db';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#d1d5db';
    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFileUpload(fileInput.files[0]);
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        handleFileUpload(fileInput.files[0]);
    }
});

function handleFileUpload(file) {
    const allowedExts = ['png', 'jpg', 'jpeg', 'gif'];
    const fileExt = file.name.split('.').pop().toLowerCase();
    if (!allowedExts.includes(fileExt)) {
        showResult('error', '不支持的文件格式！仅支持png、jpg、jpeg、gif。');
        return;
    }

    const maxSize = 16 * 1024 * 1024;
    if (file.size > maxSize) {
        showResult('error', '文件大小超过限制！最大支持16MB。');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        originalPreview.src = e.target.result;
        originalPreview.style.display = 'block';
    };
    reader.readAsDataURL(file);

    const formData = new FormData();
    formData.append('image', file);

    resultArea.style.display = 'none';
    annotatedPreview.style.display = 'none';
    annotatedPreview.src = '';
    resultContent.innerHTML = '<p style="color:#6b7280;">正在识别中，请稍候...</p>';
    resultArea.style.display = 'block';

    fetch('/api/detect', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) throw new Error('服务器响应异常');
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                let resultHtml = '';
                if (!data.result || data.result.length === 0) {
                    resultHtml = '<p class="success-text">未识别到垃圾类别</p>';
                } else {
                    data.result.forEach((item, index) => {
                        resultHtml += `
                <div class="result-item">
                  <p><b>类别 ${index + 1}：</b>${item.class_name}</p>
                  <p><b>置信度：</b>${item.confidence}</p>
                  <p><b>检测框坐标：</b>[${item.bbox.map(n => Math.round(n)).join(', ')}]</p>
                </div>
              `;
                    });
                }
                resultContent.innerHTML = resultHtml;

                if (data.annotated_image_path) {
                    const timestamp = new Date().getTime();
                    const imageSrc = '/' + data.annotated_image_path + '?t=' + timestamp;

                    console.log("加载图片地址:", imageSrc);

                    annotatedPreview.src = imageSrc;
                    annotatedPreview.onload = () => {
                        annotatedPreview.style.display = 'block';
                    };
                    annotatedPreview.onerror = () => {
                        console.error("图片路径无效:", imageSrc);
                        annotatedPreview.style.display = 'none';
                    };
                }
            } else {
                showResult('error', `识别失败：${data.message}`);
            }
        })
        .catch(error => {
            showResult('error', `请求异常：${error.message}`);
        });
}

function showResult(type, message) {
    resultArea.style.display = 'block';
    resultContent.innerHTML = `<p class="${type}-text">${message}</p>`;
}