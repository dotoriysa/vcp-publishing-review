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

# HAE Design System 토큰 매핑 (hex 소문자 → CSS 커스텀 프로퍼티)
# 출처: https://ux-standard.hyundai-autoever.com/react/1.1.1 (Design Tokens / Variables)
HAE_COLOR_TOKENS: dict = {
    # ── Common Gray ──────────────────────────────────────
    '#131416': 'var(--color-common-gray-10)',
    '#1e2024': 'var(--color-common-gray-15)',
    '#272a2f': 'var(--color-common-gray-20)',
    '#33363d': 'var(--color-common-gray-25)',
    '#41454e': 'var(--color-common-gray-30)',
    '#4d525c': 'var(--color-common-gray-35)',
    '#585e6a': 'var(--color-common-gray-40)',
    '#646a78': 'var(--color-common-gray-45)',
    '#6b7280': 'var(--color-common-gray-50)',
    '#777e8d': 'var(--color-common-gray-55)',
    '#878e9b': 'var(--color-common-gray-60)',
    '#959ba7': 'var(--color-common-gray-65)',
    '#a6abb5': 'var(--color-common-gray-70)',
    '#b7bbc3': 'var(--color-common-gray-75)',
    '#c5c8ce': 'var(--color-common-gray-80)',
    '#d3d5da': 'var(--color-common-gray-85)',
    '#dedfe3': 'var(--color-common-gray-90)',
    '#e6e7ea': 'var(--color-common-gray-92)',
    '#eff0f1': 'var(--color-common-gray-95)',
    '#f9fafa': 'var(--color-common-gray-98)',
    # ── Common Blue ──────────────────────────────────────
    '#001133': 'var(--color-common-blue-10)',
    '#001642': 'var(--color-common-blue-15)',
    '#002061': 'var(--color-common-blue-20)',
    '#003399': 'var(--color-common-blue-30)',
    '#0045cc': 'var(--color-common-blue-40)',
    '#0056ff': 'var(--color-common-blue-50)',
    '#1a67ff': 'var(--color-common-blue-55)',
    '#3378ff': 'var(--color-common-blue-60)',
    '#5289ff': 'var(--color-common-blue-65)',
    '#6b9aff': 'var(--color-common-blue-70)',
    '#85abff': 'var(--color-common-blue-75)',
    '#9ebdff': 'var(--color-common-blue-80)',
    '#e5edff': 'var(--color-common-blue-95)',
    '#f5f8ff': 'var(--color-common-blue-98)',
    # ── Hyundai Primary (VCP 현대차 브랜드) ──────────────
    '#001124': 'var(--color-hyundai-primary-10)',
    '#001833': 'var(--color-hyundai-primary-15)',
    '#00244d': 'var(--color-hyundai-primary-20)',
    '#002c5f': 'var(--color-hyundai-primary-25)',   # 현대 대표 브랜드 블루
    '#00397a': 'var(--color-hyundai-primary-30)',
    '#006be5': 'var(--color-hyundai-primary-50)',
    '#0177ff': 'var(--color-hyundai-primary-55)',
    '#1984ff': 'var(--color-hyundai-primary-60)',
    # ── Genesis Primary ──────────────────────────────────
    '#111111': 'var(--color-genesis-primary-10)',
    '#252527': 'var(--color-genesis-primary-15)',
    '#323234': 'var(--color-genesis-primary-20)',
    '#cccccc': 'var(--color-genesis-primary-80)',
    '#d9d9d9': 'var(--color-genesis-primary-85)',
    '#e3e3e3': 'var(--color-genesis-primary-90)',
    '#f2f2f2': 'var(--color-genesis-primary-95)',
    # ── Common Red (오류/위험) ────────────────────────────
    '#fa0505': 'var(--color-common-red-50)',
    '#e70404': 'var(--color-common-red-45)',
    '#fb2d2d': 'var(--color-common-red-55)',
    '#feeaea': 'var(--color-common-red-95)',
    # ── Common Green (성공) ──────────────────────────────
    '#24a67b': 'var(--color-common-green-50)',
    '#48c198': 'var(--color-common-green-60)',
    # ── 기타 ────────────────────────────────────────────
    '#ffffff': 'var(--color-genesis-alpha-white) 또는 #fff 직접 사용 가능',
    '#000000': 'var(--color-genesis-alpha-gray) 또는 #000 직접 사용 가능',
}

# 하위 호환: 기존 코드 참조용 (내부 로직에서 사용)
HMG_DESIGN_COLORS = HAE_COLOR_TOKENS

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
                    f'HAE Design System 토큰 사용: {suggestion}'
                    if suggestion
                    else 'HAE Design System 시멘틱 토큰 사용 권고 (예: var(--color-light-text-neutral-strongest))'
                )
                occurrences = [
                    {'line': ln, 'code': code, 'file': fp}
                    for fp, ln, code in usages[:300]  # 최대 300건만 저장
                ]
                issues.append(self._make_issue(
                    file=usages[0][0],
                    line=usages[0][1],
                    description=(
                        f'색상 코드 "{color}"이(가) 전체 코드에서 {len(usages)}번 사용됩니다. '
                        f'({MAX_COLOR_DUPLICATES}개 이상 권고 기준 초과)'
                    ),
                    before=usages[0][2],
                    after=after_text,
                    reason=(
                        f'같은 색상을 {len(usages)}곳에 직접 입력하면, '
                        '나중에 디자인팀이 색상을 변경할 때 모든 곳을 찾아 수정해야 합니다. '
                        'HMG Design System의 색상 변수를 사용하면 한 번만 바꾸면 됩니다.'
                    ),
                    severity='critical' if len(usages) >= MAX_COLOR_DUPLICATES * 2 else 'warning',
                    occurrences=occurrences,
                ))

            # 규칙 2-2: HMG 디자인 시스템 색상을 직접 입력한 경우
            elif color in HMG_DESIGN_COLORS or color_upper in HMG_DESIGN_COLORS:
                suggestion = HMG_DESIGN_COLORS.get(color) or HMG_DESIGN_COLORS.get(color_upper, '')
                if len(usages) > 1:  # 2회 이상 사용 시 경고
                    occurrences = [
                        {'line': ln, 'code': code, 'file': fp}
                        for fp, ln, code in usages[:300]  # 최대 300건만 저장
                    ]
                    issues.append(self._make_issue(
                        file=usages[0][0],
                        line=usages[0][1],
                        description=(
                            f'HMG 디자인 시스템 색상 "{color}"이(가) '
                            f'{len(usages)}번 직접 입력되었습니다.'
                        ),
                        before=usages[0][2],
                        after=(
                            f'/* {suggestion} */\n'
                            f'color: {suggestion};  /* CSS */\n'
                            f'sx={{{{ color: \'{suggestion}\' }}}}  /* MUI sx prop */'
                        ),
                        reason=(
                            f'이 색상({color})은 HAE Design System에 정의된 토큰({suggestion})과 일치합니다. '
                            '직접 입력 대신 CSS 커스텀 프로퍼티를 사용하면 브랜드 가이드라인 준수 및 '
                            '테마 전환이 용이해집니다.'
                        ),
                        severity='warning',
                        occurrences=occurrences,
                    ))

        return issues
