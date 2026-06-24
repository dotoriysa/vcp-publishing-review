"""
[기준 7] console.log 미제거 규칙
배포 코드에 console.log / debugger 등이 잔류한 경우를 찾아냅니다.
"""
import re
from typing import Dict, List, Any
from src.rules.base_rule import BaseRule


# 감지할 패턴
CONSOLE_PATTERN = re.compile(
    r'\b(console\s*\.\s*(log|error|warn|debug|info|trace|dir|table|group|groupEnd|time|timeEnd))\s*\(',
    re.IGNORECASE
)
DEBUGGER_PATTERN = re.compile(r'\bdebugger\b')

# 테스트/스토리파일은 제외
EXCLUDE_PATTERNS = ['.test.', '.spec.', '.stories.', '__tests__', '__mocks__']


class ConsoleLogRule(BaseRule):
    """console.log 미제거 규칙"""

    name = 'console.log 미제거 규칙'
    description = '배포 코드에 console.log, debugger 등이 남아있는지 검사합니다'
    category = 'console.log'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues = []

        for filepath, content in files.items():
            # JS/TS 계열만 검사
            if not any(filepath.endswith(ext) for ext in ('.tsx', '.jsx', '.ts', '.js')):
                continue
            # 테스트/스토리 파일 제외
            if any(pat in filepath for pat in EXCLUDE_PATTERNS):
                continue

            console_occs = []
            debugger_occs = []

            for line_num, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                # 순수 주석 라인은 무시
                if stripped.startswith('//') or stripped.startswith('*'):
                    continue
                if CONSOLE_PATTERN.search(line):
                    console_occs.append({'line': line_num, 'code': line.strip()})
                if DEBUGGER_PATTERN.search(line):
                    debugger_occs.append({'line': line_num, 'code': line.strip()})

            # debugger는 1개라도 즉시 critical
            if debugger_occs:
                issues.append(self._make_issue(
                    file=filepath,
                    line=debugger_occs[0]['line'],
                    description=(
                        f'debugger 구문이 {len(debugger_occs)}곳에 남아있습니다. '
                        '배포 코드에서는 반드시 제거해야 합니다.'
                    ),
                    before=debugger_occs[0]['code'],
                    after='해당 줄을 완전히 삭제하세요.',
                    reason=(
                        'debugger는 브라우저 개발자 도구가 열려있을 때 실행을 강제로 멈춥니다. '
                        '배포 환경에서 사용자 브라우저가 멈추는 치명적 결함이 됩니다.'
                    ),
                    severity='critical',
                    occurrences=debugger_occs,
                ))

            # console은 3개 이상이면 warning, 10개 이상이면 critical
            if len(console_occs) >= 3:
                sev = 'critical' if len(console_occs) >= 10 else 'warning'
                issues.append(self._make_issue(
                    file=filepath,
                    line=console_occs[0]['line'],
                    description=(
                        f'console.log 등 디버그 출력이 {len(console_occs)}곳에 남아있습니다. '
                        '배포 전 반드시 제거해야 합니다.'
                    ),
                    before=console_occs[0]['code'],
                    after='해당 줄을 삭제하거나, 필요한 경우 로깅 유틸리티로 교체하세요.',
                    reason=(
                        'console.log는 배포 코드에서 민감한 데이터를 노출할 수 있고, '
                        '브라우저 콘솔을 오염시켜 디버깅을 어렵게 합니다. '
                        '현대오토에버 납품 코드에서는 반드시 제거해야 합니다.'
                    ),
                    severity=sev,
                    occurrences=console_occs,
                ))

        return issues
