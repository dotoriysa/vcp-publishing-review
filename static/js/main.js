// 퍼블리싱 코드 검수 도구 - 프론트엔드 JavaScript

let selectedFile = null;
let currentIssues = [];
let lastReportData = null;  // 엑셀/메일용 원본 데이터 보관
let doneSet = new Set(); // 처리완료된 이슈 인덱스
let activeFilter = { severity: 'all', category: 'all', undoneOnly: false };
let viewMode = 'issue';

// AI 전체 검수 탭 상태
let aiFullFindings = [];
let aiFullEventSource = null;
let aiFullTotalFiles = 0;
let aiFullFoundCount = 0;
let aiFullIssueIndex = 0; // 전역 이슈 인덱스 (아코디언 ID용)

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
const downloadHtmlBtn = document.getElementById('downloadHtmlBtn');
const downloadExcelBtn = document.getElementById('downloadExcelBtn');
const draftMailBtn = document.getElementById('draftMailBtn');
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

        currentIssues = data.issues;
        lastReportData = data;
        doneSet = new Set();
        activeFilter = { severity: 'all', category: 'all', undoneOnly: false };
        viewMode = 'issue';

        renderSummary(data.summary);
        renderFilterBar(data.issues);
        applyFilters();
        fetchAiSummary(data);
        fetchAiDeepReview(data);
        updateAiTabStatus(data.summary.total_files);
    }, 500);
}

// AI 분석 요청
async function fetchAiSummary(data) {
    const aiBody = document.getElementById('aiBody');
    aiBody.innerHTML = `<div class="ai-loading"><span class="ai-spinner"></span> Claude가 코드를 분석하고 있습니다...</div>`;

    try {
        const res = await fetch('/api/ai-summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const result = await res.json();
        const s = result.summary;

        if (!s || res.status !== 200) {
            aiBody.innerHTML = `<div class="ai-error">AI 분석을 사용할 수 없습니다.</div>`;
            return;
        }

        const bulletsHtml = (s.bullets || []).length > 0
            ? `<ul class="ai-bullets">${s.bullets.map(b => `<li>${b}</li>`).join('')}</ul>`
            : '';

        aiBody.innerHTML = `
            <div class="ai-overall">${s.overall || ''}</div>
            ${bulletsHtml}
            ${s.action ? `<div class="ai-action"><strong>조치 요청:</strong> ${s.action}</div>` : ''}
        `;
    } catch {
        aiBody.innerHTML = `<div class="ai-error">AI 분석 중 오류가 발생했습니다.</div>`;
    }
}

// AI 직접 파일 분석 (규칙 엔진이 놓친 추가 이슈 발견)
async function fetchAiDeepReview(data) {
    const section = document.getElementById('aiDeepSection');
    const body = document.getElementById('aiDeepBody');
    section.classList.remove('hidden');
    body.innerHTML = `<div class="ai-loading"><span class="ai-spinner"></span> Claude가 파일을 직접 읽고 추가 이슈를 찾고 있습니다...</div>`;

    try {
        const res = await fetch('/api/ai-deep-review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ issues: data.issues }),
        });
        const result = await res.json();

        if (result.error) {
            section.classList.add('hidden');
            return;
        }

        const findings = result.findings || [];
        if (findings.length === 0) {
            body.innerHTML = `<div class="ai-deep-empty">규칙 엔진 외 추가 발견된 이슈가 없습니다.</div>`;
            return;
        }

        const html = findings.map(fileResult => {
            const issueRows = (fileResult.issues || []).map(issue => `
                <div class="ai-deep-issue">
                    <div class="ai-deep-issue-top">
                        <span class="issue-severity ${issue.severity}">${issue.severity === 'critical' ? '수정 필수' : '개선 권고'}</span>
                        <span class="issue-category">${escapeHtml(issue.category || '')}</span>
                        <span class="ai-deep-desc">${escapeHtml(issue.description || '')}</span>
                    </div>
                    ${issue.code ? `<pre class="ai-deep-code">L.${issue.line || '?'}  ${escapeHtml(issue.code)}</pre>` : ''}
                    ${issue.suggestion ? `<div class="ai-deep-suggestion">→ ${escapeHtml(issue.suggestion)}</div>` : ''}
                </div>
            `).join('');

            return `
                <div class="ai-deep-file-block">
                    <div class="ai-deep-file-name">${escapeHtml(fileResult.file)}</div>
                    ${issueRows}
                </div>`;
        }).join('');

        body.innerHTML = html;
    } catch (e) {
        body.innerHTML = `<div class="ai-deep-empty">AI 추가 분석 중 오류: ${e.message}</div>`;
    }
}

function renderSummary(summary) {
    summaryCards.innerHTML = `
        <div class="summary-card">
            <div class="summary-count">${summary.total_files}</div>
            <div class="summary-label">검사한 파일 수</div>
        </div>
        <div class="summary-card critical">
            <div class="summary-count">${summary.critical}</div>
            <div class="summary-label">심각한 문제</div>
        </div>
        <div class="summary-card warning">
            <div class="summary-count">${summary.warnings}</div>
            <div class="summary-label">주의 사항</div>
        </div>
    `;
}

// 필터 바 렌더링
function renderFilterBar(issues) {
    const toolbar = document.getElementById('filterToolbar');
    toolbar.style.display = 'flex';

    const categories = [...new Set(issues.map(i => i.category).filter(Boolean))];
    const criticalCount = issues.filter(i => i.severity === 'critical').length;
    const warningCount = issues.filter(i => i.severity === 'warning').length;

    document.getElementById('filterGroups').innerHTML = `
        <span class="filter-label">심각도</span>
        <button class="filter-btn active" data-sev="all" onclick="setSeverity('all', this)">전체 ${issues.length}</button>
        <button class="filter-btn" data-sev="critical" onclick="setSeverity('critical', this)">수정 필수 ${criticalCount}</button>
        <button class="filter-btn" data-sev="warning" onclick="setSeverity('warning', this)">개선 권고 ${warningCount}</button>
        <div class="filter-divider"></div>
        <span class="filter-label">카테고리</span>
        <button class="filter-btn active" data-cat="all" onclick="setCategory('all', this)">전체</button>
        ${categories.map(cat => `<button class="filter-btn" data-cat="${escapeHtml(cat)}" onclick="setCategory('${escapeHtml(cat)}', this)">${escapeHtml(cat)}</button>`).join('')}
        <div class="filter-divider"></div>
        <button class="filter-btn filter-btn-undone" id="filterUndoneBtn" onclick="toggleUndoneFilter(this)">미처리만 보기</button>
    `;

    document.getElementById('viewIssue').classList.add('active');
    document.getElementById('viewFile').classList.remove('active');
}

function setSeverity(sev, btn) {
    activeFilter.severity = sev;
    document.querySelectorAll('[data-sev]').forEach(b => {
        b.classList.remove('active', 'active-critical', 'active-warning');
    });
    if (sev === 'critical') btn.classList.add('active-critical');
    else if (sev === 'warning') btn.classList.add('active-warning');
    else btn.classList.add('active');
    applyFilters();
}

function setCategory(cat, btn) {
    activeFilter.category = cat;
    document.querySelectorAll('[data-cat]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    applyFilters();
}

function setView(mode) {
    viewMode = mode;
    document.getElementById('viewIssue').classList.toggle('active', mode === 'issue');
    document.getElementById('viewFile').classList.toggle('active', mode === 'file');
    applyFilters();
}

function toggleUndoneFilter(btn) {
    activeFilter.undoneOnly = !activeFilter.undoneOnly;
    btn.classList.toggle('active-undone', activeFilter.undoneOnly);
    applyFilters();
}

function applyFilters() {
    let filtered = currentIssues;
    if (activeFilter.severity !== 'all') {
        filtered = filtered.filter(i => i.severity === activeFilter.severity);
    }
    if (activeFilter.category !== 'all') {
        filtered = filtered.filter(i => i.category === activeFilter.category);
    }
    if (activeFilter.undoneOnly) {
        filtered = filtered.filter(i => !doneSet.has(currentIssues.indexOf(i)));
    }

    const countEl = document.getElementById('filterCount');
    const doneCount = [...doneSet].filter(idx => {
        const issue = currentIssues[idx];
        if (!issue) return false;
        if (activeFilter.severity !== 'all' && issue.severity !== activeFilter.severity) return false;
        if (activeFilter.category !== 'all' && issue.category !== activeFilter.category) return false;
        return true;
    }).length;
    countEl.textContent = filtered.length > 0
        ? `${filtered.length}건 중 ${doneCount}건 처리완료`
        : '';

    if (viewMode === 'file') {
        renderByFile(filtered);
    } else {
        renderIssues(filtered);
    }
}

function renderIssues(issues) {
    if (issues.length === 0) {
        issuesList.innerHTML = '<p style="text-align:center;color:#6e6e73;padding:40px">해당하는 이슈가 없습니다.</p>';
        return;
    }

    const sorted = [...issues].sort((a, b) => {
        const ai = currentIssues.indexOf(a);
        const bi = currentIssues.indexOf(b);
        if (a.severity === 'critical' && b.severity !== 'critical') return -1;
        if (a.severity !== 'critical' && b.severity === 'critical') return 1;
        return ai - bi;
    });

    issuesList.innerHTML = sorted.map(issue => {
        const idx = currentIssues.indexOf(issue);
        const isDone = doneSet.has(idx);
        return `
        <div class="issue-item${isDone ? ' done' : ''}" id="issue-item-${idx}">
            <div class="issue-header" onclick="toggleIssue(${idx})">
                <div class="issue-header-top">
                    <div class="issue-check" onclick="toggleDone(event, ${idx})">✓</div>
                    <span class="issue-severity ${issue.severity}">${issue.severity === 'critical' ? '수정 필수' : '개선 권고'}</span>
                    <span class="issue-category">${issue.category}</span>
                    <span class="issue-description">${issue.description}</span>
                    <span class="issue-done-badge">처리완료 ✓</span>
                    <span class="issue-toggle" id="toggle-${idx}">▼ 자세히</span>
                </div>
                <div class="issue-header-path">
                    <span class="issue-file-inline">${issue.file}${issue.line ? ` : ${issue.line}번째 줄` : ''}</span>
                </div>
            </div>
            <div class="issue-detail hidden" id="detail-${idx}">
                ${issueDetailHtml(issue, idx)}
            </div>
        </div>`;
    }).join('');
}

function renderByFile(issues) {
    if (issues.length === 0) {
        issuesList.innerHTML = '<p style="text-align:center;color:#6e6e73;padding:40px">해당하는 이슈가 없습니다.</p>';
        return;
    }

    // 파일별 그룹핑
    const groups = {};
    issues.forEach(issue => {
        const file = issue.file || '(파일 미상)';
        if (!groups[file]) groups[file] = [];
        groups[file].push(issue);
    });

    // 파일별 심각도 정렬 (critical 있는 파일 먼저)
    const sortedFiles = Object.keys(groups).sort((a, b) => {
        const aCritical = groups[a].some(i => i.severity === 'critical');
        const bCritical = groups[b].some(i => i.severity === 'critical');
        if (aCritical && !bCritical) return -1;
        if (!aCritical && bCritical) return 1;
        return groups[b].length - groups[a].length;
    });

    issuesList.innerHTML = sortedFiles.map(file => {
        const fileIssues = groups[file];
        const hasCritical = fileIssues.some(i => i.severity === 'critical');
        const critCount = fileIssues.filter(i => i.severity === 'critical').length;
        const warnCount = fileIssues.filter(i => i.severity === 'warning').length;

        const badgeClass = hasCritical ? 'has-critical' : 'only-warning';
        const badgeText = hasCritical
            ? `심각 ${critCount}건${warnCount ? ` · 주의 ${warnCount}건` : ''}`
            : `주의 ${warnCount}건`;

        const groupId = 'fg-' + file.replace(/[^a-zA-Z0-9]/g, '_');

        const issueRows = fileIssues.map(issue => {
            const idx = currentIssues.indexOf(issue);
            const isDone = doneSet.has(idx);
            return `
            <div class="issue-item${isDone ? ' done' : ''}" id="issue-item-${idx}" style="margin-bottom:8px">
                <div class="issue-header" onclick="toggleIssue(${idx})">
                    <div class="issue-header-top">
                        <div class="issue-check" onclick="toggleDone(event, ${idx})">✓</div>
                        <span class="issue-severity ${issue.severity}">${issue.severity === 'critical' ? '수정 필수' : '개선 권고'}</span>
                        <span class="issue-category">${issue.category}</span>
                        <span class="issue-description">${issue.description}</span>
                        <span class="issue-done-badge">처리완료 ✓</span>
                        <span class="issue-toggle" id="toggle-${idx}">▼ 자세히</span>
                    </div>
                    ${issue.line ? `<div class="issue-header-path"><span class="issue-file-inline">${issue.line}번째 줄</span></div>` : ''}
                </div>
                <div class="issue-detail hidden" id="detail-${idx}">
                    ${issueDetailHtml(issue, `f${idx}`)}
                </div>
            </div>`;
        }).join('');

        return `
        <div class="file-group">
            <div class="file-group-header" onclick="toggleFileGroup('${groupId}')">
                <span class="file-group-name">${file}</span>
                <span class="file-group-badge ${badgeClass}">${badgeText}</span>
                <span class="file-group-arrow open" id="arrow-${groupId}">▼</span>
            </div>
            <div class="file-group-issues" id="${groupId}">
                ${issueRows}
            </div>
        </div>`;
    }).join('');
}

function toggleFileGroup(groupId) {
    const body = document.getElementById(groupId);
    const arrow = document.getElementById('arrow-' + groupId);
    const isOpen = !body.classList.contains('hidden');
    body.classList.toggle('hidden', isOpen);
    arrow.classList.toggle('open', !isOpen);
}

function toggleDone(event, idx) {
    event.stopPropagation();
    const item = document.getElementById(`issue-item-${idx}`);
    if (doneSet.has(idx)) {
        doneSet.delete(idx);
        item.classList.remove('done');
    } else {
        doneSet.add(idx);
        item.classList.add('done');
    }
    // 카운트 업데이트
    applyFilters();
    // 현재 열려있는 detail은 유지
}

function toggleIssue(idx) {
    const item = document.getElementById(`issue-item-${idx}`);
    if (item && item.classList.contains('done')) return;
    const detail = document.getElementById(`detail-${idx}`);
    const toggle = document.getElementById(`toggle-${idx}`);
    if (!detail) return;
    if (detail.classList.contains('hidden')) {
        detail.classList.remove('hidden');
        toggle.textContent = '▲ 닫기';
    } else {
        detail.classList.add('hidden');
        toggle.textContent = '▼ 자세히';
    }
}

// 이슈 detail HTML 생성 (공통)
function issueDetailHtml(issue, idx) {
    const occHtml = renderOccurrences(issue.occurrences, `occ-${idx}`);
    return `
        <div class="issue-reason">
            <strong>왜 수정해야 하나요?</strong><br>
            ${issue.reason}
        </div>
        ${occHtml}
        <div class="fix-suggestion-block" id="fix-${idx}">
            <button class="fix-suggest-btn" onclick="loadFixSuggestion(event, '${idx}')">
                AI 수정 제안 보기
            </button>
        </div>`;
}

// AI 수정 제안 로드
async function loadFixSuggestion(event, idx) {
    event.stopPropagation();
    const block = document.getElementById(`fix-${idx}`);
    const issue = currentIssues[parseInt(idx)] || currentIssues.find((_, i) => String(i) === String(idx).replace('f',''));

    if (!issue) return;

    block.innerHTML = `<div class="fix-loading"><span class="ai-spinner" style="border-color:rgba(15,42,94,.2);border-top-color:#0f2a5e"></span> Claude가 수정 방법을 작성하고 있습니다...</div>`;

    try {
        const res = await fetch('/api/suggest-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: issue.category,
                file: issue.file,
                description: issue.description,
                reason: issue.reason,
                occurrences: issue.occurrences || [],
            }),
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        block.innerHTML = `
            <div class="fix-suggestion">
                <div class="fix-suggestion-label">AI 수정 제안</div>
                ${renderFixSections(data.suggestion)}
            </div>`;
    } catch (e) {
        block.innerHTML = `<div class="fix-error">수정 제안 생성 실패: ${e.message}</div>`;
    }
}

// ■ 섹션별로 파싱해 수정 전/후를 색상 구분하여 렌더링
function renderFixSections(text) {
    if (!text) return '';

    // ■ 기호 기준으로 섹션 분리
    const rawParts = text.split(/(?=■)/);
    let html = '<div class="fix-sections">';

    for (const part of rawParts) {
        const trimmed = part.trim();
        if (!trimmed) continue;

        const headerMatch = trimmed.match(/^■\s*(.+?)(?:\n|$)/);
        if (!headerMatch) {
            html += `<div class="fix-sec fix-sec-default"><pre class="fix-sec-body">${escapeHtml(trimmed)}</pre></div>`;
            continue;
        }

        const header = headerMatch[1].trim();
        const body = trimmed.slice(headerMatch[0].length).trim();

        let cls = 'fix-sec-default';
        if (/수정\s*전/.test(header)) cls = 'fix-sec-before';
        else if (/수정\s*후/.test(header)) cls = 'fix-sec-after';
        else if (/문제|위반/.test(header)) cls = 'fix-sec-problem';
        else if (/참고/.test(header)) cls = 'fix-sec-note';

        html += `
            <div class="fix-sec ${cls}">
                <div class="fix-sec-header">■ ${escapeHtml(header)}</div>
                ${body ? `<pre class="fix-sec-body">${escapeHtml(body)}</pre>` : ''}
            </div>`;
    }

    html += '</div>';
    return html;
}

// occurrences 렌더링 (줄번호 + 코드 + 말줄임표)
const SHOW_LIMIT = 5;

function renderOccurrences(occurrences, uid) {
    if (!occurrences || occurrences.length === 0) return '';

    const isMultiFile = occurrences.some(o => o.file);
    const total = occurrences.length;
    const visible = occurrences.slice(0, SHOW_LIMIT);
    const hidden = occurrences.slice(SHOW_LIMIT);

    function lineHtml(o) {
        const fileTag = (isMultiFile && o.file)
            ? `<div class="code-line-file">${escapeHtml(o.file)}</div>`
            : '';
        return `${fileTag}<li class="code-line">
            <span class="code-line-num">${o.line || ''}</span>
            <span class="code-line-text">${escapeHtml(o.code || '')}</span>
        </li>`;
    }

    const visibleHtml = visible.map(lineHtml).join('');
    const hiddenHtml = hidden.length > 0
        ? `<div id="more-${uid}" class="hidden">${hidden.map(lineHtml).join('')}</div>
           <button class="show-more-btn" onclick="expandMore('${uid}', this)">
               ··· ${hidden.length}개 더 보기 (전체 ${total}건)
           </button>`
        : '';

    return `<div class="code-block">
        <div class="code-label">위반 코드 전체 목록 (${total}건)</div>
        <div class="code-content">
            <ul class="code-lines">${visibleHtml}</ul>
            ${hiddenHtml}
        </div>
    </div>`;
}

function expandMore(uid, btn) {
    document.getElementById('more-' + uid).classList.remove('hidden');
    btn.remove();
}

function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// HTML 다운로드
downloadHtmlBtn.addEventListener('click', () => {
    const content = document.getElementById('resultSection').innerHTML;
    const today = new Date().toLocaleDateString('ko-KR');
    const html = `<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>VCP 퍼블리싱 코드 검수 결과</title>
    <style>
        body { font-family: '맑은 고딕', sans-serif; max-width: 1000px; margin: 40px auto; padding: 20px; color: #1d1d1f; }
        h1 { font-size: 22px; border-bottom: 2px solid #1d1d1f; padding-bottom: 12px; margin-bottom: 4px; }
        .meta { font-size: 13px; color: #666; margin-bottom: 32px; }
        .hidden { display: none !important; }
        .ai-section, .filter-toolbar, .action-btns { display: none !important; }
        .issue-check, .issue-done-badge { display: none !important; }
    </style>
</head>
<body>
    <h1>VCP 퍼블리싱 코드 검수 결과</h1>
    <p class="meta">검수 파일: ${selectedFile ? selectedFile.name : ''} &nbsp;|&nbsp; 검수일: ${today} &nbsp;|&nbsp; 작성: INNOCEAN</p>
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

// 엑셀 다운로드 (AI 수정 제안 일괄 생성 포함 - 1~2분 소요)
downloadExcelBtn.addEventListener('click', async () => {
    if (!lastReportData) return;
    downloadExcelBtn.disabled = true;

    // 진행 단계 표시
    const steps = [
        '이슈 분석 중...',
        'AI 수정 제안 생성 중...',
        'AI 수정 제안 생성 중.. (30초)',
        'AI 수정 제안 생성 중.. (60초)',
        '엑셀 파일 생성 중...',
    ];
    let stepIdx = 0;
    downloadExcelBtn.textContent = steps[0];
    const stepTimer = setInterval(() => {
        stepIdx = Math.min(stepIdx + 1, steps.length - 1);
        downloadExcelBtn.textContent = steps[stepIdx];
    }, 20000);

    try {
        const body = {
            ...lastReportData,
            filename: selectedFile ? selectedFile.name.replace('.zip', '') : 'VCP',
        };
        const res = await fetch('/api/download-excel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error('서버 오류');
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `VCP검수결과_${new Date().toISOString().slice(0, 10)}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        alert(`엑셀 생성에 실패했습니다: ${e.message}`);
    } finally {
        clearInterval(stepTimer);
        downloadExcelBtn.textContent = '엑셀 다운로드';
        downloadExcelBtn.disabled = false;
    }
});

// 메일 초안
let mailContent = '';

draftMailBtn.addEventListener('click', async () => {
    if (!lastReportData) return;
    openMailModal();
    document.getElementById('mailModalBody').innerHTML =
        `<div class="mail-loading"><span class="ai-spinner"></span> Claude가 메일을 작성하고 있습니다...</div>`;
    try {
        const body = { ...lastReportData, filename: selectedFile ? selectedFile.name.replace('.zip','') : 'VCP' };
        const res = await fetch('/api/draft-mail', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        mailContent = data.mail;
        document.getElementById('mailModalBody').innerHTML =
            `<div class="mail-text">${escapeHtml(mailContent)}</div>`;
    } catch (e) {
        document.getElementById('mailModalBody').innerHTML =
            `<div style="color:#c0392b;padding:20px">메일 초안 생성에 실패했습니다: ${e.message}</div>`;
    }
});

function openMailModal() {
    document.getElementById('mailModal').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeMailModal() {
    document.getElementById('mailModal').classList.add('hidden');
    document.body.style.overflow = '';
}

function copyMail() {
    if (!mailContent) return;
    navigator.clipboard.writeText(mailContent).then(() => {
        const btn = document.getElementById('copyMailBtn');
        btn.textContent = '복사 완료!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = '클립보드 복사';
            btn.classList.remove('copied');
        }, 2000);
    });
}

// ESC로 모달 닫기
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeMailModal();
});

// ─────────────────────────────────────────────────
//  탭 전환
// ─────────────────────────────────────────────────
function switchTab(name) {
    const isAuto = name === 'auto';
    document.getElementById('tabAuto').classList.toggle('hidden', !isAuto);
    document.getElementById('tabAi').classList.toggle('hidden', isAuto);
    document.getElementById('tabBtnAuto').classList.toggle('active', isAuto);
    document.getElementById('tabBtnAi').classList.toggle('active', !isAuto);
}

// ─────────────────────────────────────────────────
//  AI 전체 검수 탭 — 파일 상태 표시
// ─────────────────────────────────────────────────
function updateAiTabStatus(fileCount) {
    const statusEl = document.getElementById('aiFullFileStatus');
    const startBtn = document.getElementById('aiFullStartBtn');
    if (!statusEl || !startBtn) return;
    if (fileCount > 0) {
        statusEl.innerHTML = `<strong>${fileCount}개</strong> 파일이 로드되었습니다. AI 검수를 시작하면 파일별로 순차 분석합니다.`;
        startBtn.disabled = false;
    } else {
        statusEl.textContent = '자동 검수 탭에서 ZIP 파일을 먼저 업로드하고 검수를 실행해주세요.';
        startBtn.disabled = true;
    }
}

// ─────────────────────────────────────────────────
//  AI 전체 검수 — SSE 시작
// ─────────────────────────────────────────────────
function startAiFullReview() {
    if (aiFullEventSource) {
        aiFullEventSource.close();
        aiFullEventSource = null;
    }

    // 상태 초기화
    aiFullFindings = [];
    aiFullTotalFiles = 0;
    aiFullFoundCount = 0;
    aiFullIssueIndex = 0;

    document.getElementById('aiFullStartBtn').disabled = true;
    document.getElementById('aiFullProgressSection').classList.remove('hidden');
    document.getElementById('aiFullResults').classList.remove('hidden');
    document.getElementById('aiFullResults').innerHTML = '';
    document.getElementById('aiFullActionBtns').classList.add('hidden');
    document.getElementById('aiFullFoundCount').textContent = '';
    document.getElementById('aiFullProgressFile').textContent = '연결 중...';

    aiFullEventSource = new EventSource('/api/ai-full-review-stream');

    aiFullEventSource.onmessage = (event) => {
        let data;
        try { data = JSON.parse(event.data); } catch { return; }

        if (data.type === 'start') {
            aiFullTotalFiles = data.total;
            document.getElementById('aiFullProgressCount').textContent = `0 / ${data.total}`;
            document.getElementById('aiFullProgressFill').style.width = '0%';
        } else if (data.type === 'progress') {
            const pct = Math.round((data.current - 1) / data.total * 100);
            document.getElementById('aiFullProgressFill').style.width = pct + '%';
            document.getElementById('aiFullProgressCount').textContent = `${data.current} / ${data.total}`;
            document.getElementById('aiFullProgressFile').textContent = `분석 중: ${data.file}`;
        } else if (data.type === 'result') {
            aiFullFindings.push({ file: data.file, issues: data.issues });
            aiFullFoundCount += (data.issues || []).length;
            const pct = Math.round(data.current / data.total * 100);
            document.getElementById('aiFullProgressFill').style.width = pct + '%';
            document.getElementById('aiFullProgressCount').textContent = `${data.current} / ${data.total}`;
            document.getElementById('aiFullFoundCount').textContent = `현재까지 발견된 이슈: ${aiFullFoundCount}건`;
            renderAiFullFileResult(data.file, data.issues || []);
        } else if (data.type === 'done') {
            aiFullEventSource.close();
            aiFullEventSource = null;
            onAiFullDone();
        } else if (data.type === 'error') {
            aiFullEventSource.close();
            aiFullEventSource = null;
            showAiFullError(data.message);
        }
    };

    aiFullEventSource.onerror = () => {
        if (aiFullEventSource) {
            aiFullEventSource.close();
            aiFullEventSource = null;
        }
        showAiFullError('서버 연결이 끊겼습니다. 다시 시도해주세요.');
    };
}

function onAiFullDone() {
    document.getElementById('aiFullProgressFile').textContent = '검수 완료!';
    document.getElementById('aiFullProgressFill').style.width = '100%';
    document.getElementById('aiFullFoundCount').textContent = `총 발견된 이슈: ${aiFullFoundCount}건 (${aiFullTotalFiles}개 파일)`;
    document.getElementById('aiFullStartBtn').disabled = false;
    document.getElementById('aiFullActionBtns').classList.remove('hidden');
}

function showAiFullError(msg) {
    document.getElementById('aiFullProgressFile').textContent = `오류: ${msg}`;
    document.getElementById('aiFullStartBtn').disabled = false;
}

// ─────────────────────────────────────────────────
//  AI 전체 검수 — 파일 결과 렌더링 (실시간 추가)
// ─────────────────────────────────────────────────
function renderAiFullFileResult(filepath, issues) {
    const resultsEl = document.getElementById('aiFullResults');
    const critCount = issues.filter(i => i.severity === 'critical').length;
    const warnCount = issues.filter(i => i.severity === 'warning').length;

    const hasCritical = critCount > 0;
    const badgeClass = hasCritical ? 'has-critical' : (warnCount > 0 ? 'only-warning' : 'no-issue');
    const badgeText = issues.length === 0
        ? '이슈 없음'
        : (hasCritical
            ? `심각 ${critCount}건${warnCount ? ` · 주의 ${warnCount}건` : ''}`
            : `주의 ${warnCount}건`);

    const groupId = 'aif-' + filepath.replace(/[^a-zA-Z0-9]/g, '_');

    const issueCards = issues.map(issue => {
        const idx = aiFullIssueIndex++;
        const cardId = `aicard-${idx}`;
        const beforeHtml = issue.before
            ? `<div class="ai-full-code-label">수정 전</div><pre class="ai-full-before">${escapeHtml(issue.before)}</pre>`
            : '';
        const afterHtml = issue.after
            ? `<div class="ai-full-code-label">수정 후</div><pre class="ai-full-after">${escapeHtml(issue.after)}</pre>`
            : '';
        return `
            <div class="ai-full-issue-card" id="${cardId}">
                <div class="ai-full-issue-top">
                    <span class="issue-severity ${issue.severity || 'warning'}">${issue.severity === 'critical' ? '수정 필수' : '개선 권고'}</span>
                    <span class="issue-category">${escapeHtml(issue.category || '')}</span>
                    <span class="ai-full-line">L.${issue.line || '?'}</span>
                    <span class="ai-full-desc">${escapeHtml(issue.description || '')}</span>
                </div>
                ${beforeHtml}${afterHtml}
            </div>`;
    }).join('');

    const noIssueHtml = issues.length === 0
        ? '<div class="ai-full-no-issue">이 파일에서 발견된 추가 이슈 없음</div>'
        : '';

    const fileBlock = document.createElement('div');
    fileBlock.className = 'ai-full-file';
    fileBlock.id = 'aifile-' + groupId;
    fileBlock.innerHTML = `
        <div class="ai-full-file-header" onclick="toggleAiFullFile('${groupId}')">
            <span class="ai-full-file-name">${escapeHtml(filepath)}</span>
            <span class="file-group-badge ${badgeClass}">${badgeText}</span>
            <span class="file-group-arrow open" id="arrow-${groupId}">▼</span>
        </div>
        <div class="ai-full-file-body" id="${groupId}">
            ${issueCards}${noIssueHtml}
        </div>`;

    resultsEl.appendChild(fileBlock);
}

function toggleAiFullFile(groupId) {
    const body = document.getElementById(groupId);
    const arrow = document.getElementById('arrow-' + groupId);
    const isOpen = !body.classList.contains('hidden');
    body.classList.toggle('hidden', isOpen);
    if (arrow) arrow.classList.toggle('open', !isOpen);
}

// ─────────────────────────────────────────────────
//  AI 전체 검수 — 메일 초안
// ─────────────────────────────────────────────────
async function draftAiFullMail() {
    openMailModal();
    document.getElementById('mailModalBody').innerHTML =
        `<div class="mail-loading"><span class="ai-spinner"></span> Claude가 메일을 작성하고 있습니다...</div>`;
    try {
        const body = {
            findings: aiFullFindings,
            filename: selectedFile ? selectedFile.name.replace('.zip', '') : 'VCP',
        };
        const res = await fetch('/api/ai-full-mail', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        mailContent = data.mail;
        document.getElementById('mailModalBody').innerHTML =
            `<div class="mail-text">${escapeHtml(mailContent)}</div>`;
    } catch (e) {
        document.getElementById('mailModalBody').innerHTML =
            `<div style="color:#c0392b;padding:20px">메일 초안 생성에 실패했습니다: ${e.message}</div>`;
    }
}

// ─────────────────────────────────────────────────
//  AI 전체 검수 — 리셋
// ─────────────────────────────────────────────────
function resetAiFullReview() {
    if (aiFullEventSource) {
        aiFullEventSource.close();
        aiFullEventSource = null;
    }
    aiFullFindings = [];
    aiFullFoundCount = 0;
    aiFullTotalFiles = 0;
    aiFullIssueIndex = 0;

    document.getElementById('aiFullProgressSection').classList.add('hidden');
    document.getElementById('aiFullResults').classList.add('hidden');
    document.getElementById('aiFullResults').innerHTML = '';
    document.getElementById('aiFullActionBtns').classList.add('hidden');
    document.getElementById('aiFullStartBtn').disabled = !lastReportData;
}

// 리셋
resetBtn.addEventListener('click', () => {
    selectedFile = null;
    lastReportData = null;
    currentIssues = [];
    fileInfo.classList.add('hidden');
    dropZone.classList.remove('hidden');
    startBtn.disabled = true;
    fileInput.value = '';
    resultSection.classList.add('hidden');
    progressFill.style.width = '0%';
    document.getElementById('filterToolbar').style.display = 'none';
});
