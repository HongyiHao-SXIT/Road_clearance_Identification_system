const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const originalPreview = document.getElementById('originalPreview');
const annotatedPreview = document.getElementById('annotatedPreview');
const resultArea = document.getElementById('resultArea');
const resultContent = document.getElementById('resultContent');
const latInput = document.getElementById('latInput');
const lngInput = document.getElementById('lngInput');
const detectBtn = document.getElementById("detectBtn");
const resetBtn = document.getElementById('resetBtn');

let selectedFile = null;


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


document.getElementById('randomLocBtn').addEventListener('click', () => {
    latInput.value = (Math.random() * (35 - 30) + 30).toFixed(6);
    lngInput.value = (Math.random() * (115 - 110) + 110).toFixed(6);
    checkDetectAvailable();
});

document.getElementById('clearLocBtn').addEventListener('click', () => {
    latInput.value = '';
    lngInput.value = '';
    checkDetectAvailable();
});


function handleFileUpload(file) {
    const allowedExts = ['png', 'jpg', 'jpeg', 'gif'];
    const fileExt = file.name.split('.').pop().toLowerCase();

    if (!allowedExts.includes(fileExt)) {
        showResult('error', '不支持的文件格式！仅支持 png、jpg、jpeg、gif。');
        return;
    }

    const maxSize = 16 * 1024 * 1024;
    if (file.size > maxSize) {
        showResult('error', '文件大小超过限制！最大支持 16MB。');
        return;
    }

    selectedFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        originalPreview.src = e.target.result;
        originalPreview.style.display = 'block';
    };
    reader.readAsDataURL(file);

    annotatedPreview.style.display = 'none';
    resultArea.style.display = 'none';

    checkDetectAvailable();
}


function checkDetectAvailable() {
    const lat = latInput.value.trim();
    const lng = lngInput.value.trim();

    detectBtn.disabled = !(selectedFile && !(lat === '' && lng === ''));
}

latInput.addEventListener('input', checkDetectAvailable);
lngInput.addEventListener('input', checkDetectAvailable);


detectBtn.addEventListener('click', () => {
    if (!selectedFile) {
        alert('请先选择图片');
        return;
    }

    const lat = latInput.value.trim();
    const lng = lngInput.value.trim();

    if (lat === '' && lng === '') {
        alert('请至少填写一个位置信息');
        return;
    }

    const formData = new FormData();
    formData.append('image', selectedFile);
    if (lat) formData.append('latitude', lat);
    if (lng) formData.append('longitude', lng);

    resultArea.style.display = 'block';
    resultContent.innerHTML = '<p style="color:#6b7280;">正在识别中，请稍候...</p>';
    detectBtn.disabled = true;

    fetch('/api/detect', {
        method: 'POST',
        body: formData
    })
    .then(res => {
        if (!res.ok) throw new Error('服务器响应异常');
        return res.json();
    })
    .then(data => {
        detectBtn.disabled = false;

        if (data.status === 'success') {
            let html = '';

            if (!data.result || data.result.length === 0) {
                html = '<p class="success-text">未识别到垃圾类别</p>';
            } else {
                data.result.forEach((item, i) => {
                    html += `
                        <div class="result-item">
                            <p><b>类别 ${i + 1}：</b>${item.class_name}</p>
                            <p><b>置信度：</b>${item.confidence}</p>
                            <p><b>检测框：</b>[${item.bbox.map(n => Math.round(n)).join(', ')}]</p>
                        </div>
                    `;
                });
            }

            resultContent.innerHTML = html;

            if (data.annotated_image_path) {
                annotatedPreview.src = '/' + data.annotated_image_path + '?t=' + Date.now();
                annotatedPreview.style.display = 'block';
            }
        } else {
            showResult('error', data.message);
        }
    })
    .catch(err => {
        detectBtn.disabled = false;
        showResult('error', err.message);
    });
});


resetBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    latInput.value = '';
    lngInput.value = '';

    originalPreview.style.display = 'none';
    annotatedPreview.style.display = 'none';
    resultArea.style.display = 'none';

    detectBtn.disabled = true;
});


function showResult(type, message) {
    resultArea.style.display = 'block';
    resultContent.innerHTML = `<p class="${type}-text">${message}</p>`;
}
