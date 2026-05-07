"""
[기준 2] 색상 규칙
특정 색상 코드가 코드베이스 전체에서 너무 많이 반복 사용된 경우를 찾아냅니다.
"""
import re
from collections import defaultdict
from typing import Dict, List, Any
from src.rules.base_rule import BaseRule


# 임계값: 이 숫자 이상 중복되면 경고
MAX_COLOR_DUPLICATES = 50

# HMG 디자인 시스템 주요 색상 (이 색상들을 직접 입력하면 경고)
HMG_DESIGN_COLORS = {
    '#111111': 'colors.gray900 (또는 colors.black)',
    '#e9eaec': 'colors.gray100',
    '#E9EAEC': 'colors.gray100',
    '#8333e6': 'colors.purple500 (또는 colors.primary)',
    '#8333E6': 'colors.purple500 (또는 colors.primary)',
    '#333333': 'colors.gray800',
    '#666666': 'colors.gray600',
    '#999999': 'colors.gray400',
    '#cccccc': 'colors.gray200',
    '#CCCCCC': 'colors.gray200',
    '#ffffff': 'colors.white',
    '#FFFFFF': 'colors.white',
    '#000000': 'colors.black',
}

# 색상 패턴 (hex 색상)
COLOR_PATTERN = re.compile(r'#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b')


class ColorRule(BaseRule):
    """색상 규칙"""

    name = '색상 규칙'
    description = '하드코딩된 색상 코드가 너무 많이 반복 사용된 경우를 검사합니다'
    category = '색상'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues = []
        # 색상별 사용 현황: {색상코드: [(파일, 줄번호, 줄내용), ...]}
        color_usage: Dict[str, List] = defaultdict(list)

        for filepath, content in files.items():
            for line_num, line in enumerate(content.splitlines(), start=1):
                for match in COLOR_PATTERN.finditer(line):
                    color = match.group(0).lower()
                    color_usage[color].append((filepath, line_num, line.strip()))

        # 각 색상 검사
        for color, usages in color_usage.items():
            color_upper = color.upper()

            # 규칙 2-1: 50개 이상 중복
            if len(usages) >= MAX_COLOR_DUPLICATES:
                suggestion = HMG_DESIGN_COLORS.get(color, HMG_DESIGN_COLORS.get(color_upper, ''))
                after_text = (
                    f'HMG Design System CSS 변수 사용 권고: {suggestion}'
                    if suggestion
                    else 'CSS 변수 또는 테마 색상 토큰으로 교체 권고'
                )
                issues.append(self._make_issue(
                    file=usages[0][0],
                    line=usages[0][1],
                    description=(
                        f'색상 코드 "{color}"이(가) 전체 코드에서 {len(usages)}번 사용됩니다. '
                        f'({MAX_COLOR_DUPLICATES}개 이상 권고 기준 초과)'
                    ),
                    before=f'{color} (직접 입력)',
                    after=after_text,
                    reason=(
                        f'같은 색상을 {len(usages)}곳에 직접 입력하면, '
                        '나중에 디자인팀이 색상을 변경할 때 모든 곳을 찾아 수정해야 합니다. '
                        'HMG Design System의 색상 변수를 사용하면 한 번만 바꾸면 됩니다.'
                    ),
                    severity='critical' if len(usages) >= MAX_COLOR_DUPLICATES * 2 else 'warning',
                ))

            # 규칙 2-2: HMG 디자인 시스템 색상을 직접 입력한 경우
            elif color in HMG_DESIGN_COLORS or color_upper in HMG_DESIGN_COLORS:
                suggestion = HMG_DESIGN_COLORS.get(color) or HMG_DESIGN_COLORS.get(color_upper, '')
                if len(usages) > 1:  # 2회 이상 사용 시 경고
                    issues.append(self._make_issue(
                        file=usages[0][0],
                        line=usages[0][1],
                        description=(
                            f'HMG 디자인 시스템 색상 "{color}"이(가) '
                            f'{len(usages)}번 직접 입력되었습니다.'
                        ),
                        before=f'{color} (직접 입력)',
                        after=f'import {{ colors }} from \'@/shared/theme\';\n{suggestion}',
                        reason=(
                            f'이 색상({color})은 HMG 디자인 시스템에 이미 정의된 색상입니다. '
                            '직접 입력 대신 테마 변수를 사용해야 디자인 일관성이 유지됩니다.'
                        ),
                        severity='warning',
                    ))

        return issues
