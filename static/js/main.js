// 퍼블리싱 코드 검수 도구 - 프론트엔드 JavaScript

let selectedFile = null;

// 요소 참조
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileRemove = document.getElementById('fileRemove');
const startBtn = document.getElementById('startBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultSection = document.getElementById('resultSection');
const summaryCards = document.getElementById('summaryCards');
const issuesList = document.getElementById('issuesList');
const downloadBtn = document.getElementById('downloadBtn');
const resetBtn = document.getElementById('resetBtn');

// 드래그 앤 드롭
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.zip')) {
        setFile(file);
    } else {
        alert('ZIP 파일만 업로드 가능합니다.');
    }
});

dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) setFile(e.target.files[0]);
});

fileRemove.addEventListener('click', () => {
    selectedFile = null;
    fileInfo.classList.add('hidden');
    dropZone.classList.remove('hidden');
    startBtn.disabled = true;
    fileInput.value = '';
});

function setFile(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileInfo.classList.remove('hidden');
    dropZone.classList.add('hidden');
    startBtn.disabled = false;
}

// 검수 시작
startBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    const rules = [...document.querySelectorAll('input[name="rules"]:checked')]
        .map(el => el.value);

    if (rules.length === 0) {
        alert('최소 하나 이상의 검수 기준을 선택해주세요.');
        return;
    }

    // UI 업데이트
    startBtn.disabled = true;
    progressSection.classList.remove('hidden');
    resultSection.classList.add('hidden');

    // 진행 애니메이션
    animateProgress();

    // API 호출
    const formData = new FormData();
    formData.append('file', selectedFile);
    rules.forEach(rule => formData.append('rules', rule));

    try {
        const response = await fetch('/review', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (data.error) {
            alert(`오류: ${data.error}`);
            resetProgress();
            return;
        }

        showResults(data);
    } catch (error) {
        alert('서버 연결에 실패했습니다. 다시 시도해주세요.');
        resetProgress();
    }
});

// 진행 애니메이션
let progressInterval;
function animateProgress() {
    let progress = 0;
    const steps = [
        { target: 20, text: '파일 압축 해제 중...' },
        { target: 40, text: '타이포그래피 규칙 검사 중...' },
        { target: 60, text: '색상 규칙 검사 중...' },
        { target: 80, text: '코드 품질 검사 중...' },
        { target: 95, text: '결과 정리 중...' },
    ];
    let stepIdx = 0;

    progressInterval = setInterval(() => {
        if (stepIdx < steps.length) {
            const step = steps[stepIdx];
            if (progress < step.target) {
                progress += 2;
                progressFill.style.width = progress + '%';
                progressText.textContent = step.text;
            } else {
                stepIdx++;
            }
        }
    }, 100);
}

function resetProgress() {
    clearInterval(progressInterval);
    progressSection.classList.add('hidden');
    progressFill.style.width = '0%';
    startBtn.disabled = false;
}

// 결과 표시
function showResults(data) {
    clearInterval(progressInterval);
    progressFill.style.width = '100%';
    progressText.textContent = '완료!';

    setTimeout(() => {
        progressSection.classList.add('hidden');
        resultSection.classList.remove('hidden');

        renderSummary(data.summary);
        renderIssues(data.issues);
    }, 500);
}

function renderSummary(summary) {
    summaryCards.innerHTML = `
        <div class="summary-card">
            <div class="summary-count">${summary.total_files}</div>
            <div class="summary-label">검사한 파일 수</div>
        </div>
        <div class="summary-card critical">
            <div class="summary-count">${summary.critical}</div>
            <div class="summary-label">🔴 심각한 문제</div>
        </div>
        <div class="summary-card warning">
            <div class="summary-count">${summary.warnings}</div>
            <div class="summary-label">🟡 주의 사항</div>
        </div>
    `;
}

function renderIssues(issues) {
    if (issues.length === 0) {
        issuesList.innerHTML = '<p style="text-align:center;color:#6e6e73;padding:40px">문제가 발견되지 않았습니다! 🎉</p>';
        return;
    }

    // 심각도 순 정렬 (critical 먼저)
    const sorted = [...issues].sort((a, b) => {
        if (a.severity === 'critical' && b.severity !== 'critical') return -1;
        if (a.severity !== 'critical' && b.severity === 'critical') return 1;
        return 0;
    });

    issuesList.innerHTML = sorted.map((issue, idx) => `
        <div class="issue-item">
            <div class="issue-header" onclick="toggleIssue(${idx})">
                <span class="issue-severity ${issue.severity}">
                    ${issue.severity === 'critical' ? '🔴 심각' : '🟡 주의'}
                </span>
                <span class="issue-category">${issue.category}</span>
                <span class="issue-description">${issue.description}</span>
                <span class="issue-toggle" id="toggle-${idx}">▼ 자세히</span>
            </div>
            <div class="issue-detail hidden" id="detail-${idx}">
                <div class="issue-file">📁 ${issue.file}${issue.line ? ` (${issue.line}번째 줄)` : ''}</div>
                <div class="issue-reason">
                    <strong>💡 왜 수정해야 하나요?</strong><br>
                    ${issue.reason}
                </div>
                ${issue.before ? `
                <div class="code-block">
                    <div class="code-label">수정 전 (Before)</div>
                    <div class="code-content">${escapeHtml(issue.before)}</div>
                </div>` : ''}
                ${issue.after ? `
                <div class="code-block">
                    <div class="code-label">수정 후 (After)</div>
                    <div class="code-content">${escapeHtml(issue.after)}</div>
                </div>` : ''}
            </div>
        </div>
    `).join('');
}

function toggleIssue(idx) {
    const detail = document.getElementById(`detail-${idx}`);
    const toggle = document.getElementById(`toggle-${idx}`);
    if (detail.classList.contains('hidden')) {
        detail.classList.remove('hidden');
        toggle.textContent = '▲ 닫기';
    } else {
        detail.classList.add('hidden');
        toggle.textContent = '▼ 자세히';
    }
}

function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// 다운로드
downloadBtn.addEventListener('click', () => {
    const content = document.getElementById('resultSection').innerHTML;
    const html = `
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>퍼블리싱 코드 검수 결과</title>
    <style>
        body { font-family: sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; }
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <h1>퍼블리싱 코드 검수 결과</h1>
    <p>검수 파일: ${selectedFile ? selectedFile.name : ''} | 검수일: ${new Date().toLocaleDateString('ko-KR')}</p>
    ${content}
</body>
</html>`;

    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `검수결과_${new Date().toISOString().slice(0, 10)}.html`;
    a.click();
});

// 리셋
resetBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInfo.classList.add('hidden');
    dropZone.classList.remove('hidden');
    startBtn.disabled = true;
    fileInput.value = '';
    resultSection.classList.add('hidden');
    progressFill.style.width = '0%';
});
