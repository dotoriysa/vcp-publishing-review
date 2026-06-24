"""
[기준 8] z-index 매직넘버 규칙
z-index에 999, 9999 같은 임의의 큰 숫자를 직접 사용한 경우를 찾아냅니다.
MUI theme.zIndex 토큰을 사용해야 합니다.
"""
import re
from typing import Dict, List, Any
from src.rules.base_rule import BaseRule


# z-index 직접 입력 패턴 (CSS/SCSS/sx prop)
ZINDEX_CSS_PATTERN = re.compile(
    r'z-index\s*:\s*(\d+)',
    re.IGNORECASE
)
ZINDEX_SX_PATTERN = re.compile(
    r'\bzIndex\s*:\s*(\d+)'
)

# MUI zIndex 토큰 매핑 (값 → 토큰명)
MUI_ZINDEX_MAP = {
    range(0, 100): None,           # 낮은 값은 의도적 사용으로 허용
    range(100, 200): None,
    range(200, 1000): 'theme.zIndex.mobileStepper(1000)',
    range(1000, 1001): 'theme.zIndex.mobileStepper (1000)',
    range(1050, 1051): 'theme.zIndex.fab (1050)',
    range(1100, 1101): 'theme.zIndex.speedDial (1050)',
    range(1200, 1201): 'theme.zIndex.appBar (1200)',
    range(1300, 1301): 'theme.zIndex.drawer (1300)',
    range(1400, 1401): 'theme.zIndex.modal (1400)',
    range(1500, 1501): 'theme.zIndex.snackbar (1500)',
    range(1600, 1601): 'theme.zIndex.tooltip (1600)',
}

# 경고 임계값: 이 값 이상이면 매직넘버로 판단
MAGIC_THRESHOLD = 100


def _get_zindex_suggestion(value: int) -> str:
    """z-index 값에 맞는 MUI 토큰 제안"""
    if value >= 1600:
        return 'theme.zIndex.tooltip (1600) 이상 — MUI 레이어 구조 재검토 필요'
    elif value >= 1500:
        return 'theme.zIndex.snackbar (1500)'
    elif value >= 1400:
        return 'theme.zIndex.modal (1400)'
    elif value >= 1300:
        return 'theme.zIndex.drawer (1300)'
    elif value >= 1200:
        return 'theme.zIndex.appBar (1200)'
    elif value >= 1050:
        return 'theme.zIndex.fab (1050)'
    elif value >= 1000:
        return 'theme.zIndex.mobileStepper (1000)'
    else:
        return 'MUI theme.zIndex 토큰으로 교체하거나 낮은 값(1~10)으로 정리'


class ZIndexRule(BaseRule):
    """z-index 매직넘버 규칙"""

    name = 'z-index 매직넘버 규칙'
    description = 'z-index에 임의의 큰 숫자(100 이상)를 직접 사용한 경우를 검사합니다'
    category = 'z-index'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues = []

        for filepath, content in files.items():
            occurrences = []
            max_value = 0

            for line_num, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('*'):
                    continue

                for pattern in (ZINDEX_CSS_PATTERN, ZINDEX_SX_PATTERN):
                    for match in pattern.finditer(line):
                        value = int(match.group(1))
                        if value >= MAGIC_THRESHOLD:
                            occurrences.append({
                                'line': line_num,
                                'code': line.strip(),
                                'value': value,
                            })
                            max_value = max(max_value, value)

            if occurrences:
                suggestion = _get_zindex_suggestion(max_value)
                # 9999 이상이면 critical
                sev = 'critical' if max_value >= 9999 else 'warning'

                issues.append(self._make_issue(
                    file=filepath,
                    line=occurrences[0]['line'],
                    description=(
                        f'z-index에 임의의 큰 숫자가 {len(occurrences)}곳에 사용되었습니다 '
                        f'(최대값: {max_value}). MUI theme.zIndex 토큰을 사용해야 합니다.'
                    ),
                    before=occurrences[0]['code'],
                    after=(
                        f'MUI 권장 토큰: {suggestion}\n'
                        f'예: sx={{{{ zIndex: theme.zIndex.modal }}}}\n'
                        f'또는 styled(Box)({{ zIndex: theme.zIndex.appBar }})'
                    ),
                    reason=(
                        'z-index에 9999 같은 임의의 큰 숫자를 쓰면 MUI 컴포넌트(Modal, Drawer, Tooltip 등)의 '
                        '레이어 순서가 깨집니다. MUI theme.zIndex 토큰을 사용하면 '
                        'MUI 내부 레이어와 충돌 없이 올바른 순서를 보장합니다.'
                    ),
                    severity=sev,
                    occurrences=[{'line': o['line'], 'code': o['code']} for o in occurrences],
                ))

        return issues
