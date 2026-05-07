"""
[기준 1] 타이포그래피 규칙
폰트 크기, 굵기, 줄간격 등이 코드에 직접 입력된 경우를 찾아냅니다.
"""
import re
from collections import defaultdict
from typing import Dict, List, Any
from src.rules.base_rule import BaseRule


# 임계값 설정
MAX_TYPOGRAPHY_PER_FILE = 10    # 한 파일에 타이포 속성이 이것 이상이면 경고
MAX_DUPLICATE_COMPONENTS = 5    # 동일 값이 이것 이상의 컴포넌트에서 사용되면 경고

# 타이포그래피 관련 속성 패턴
TYPOGRAPHY_PATTERNS = [
    # MUI sx prop: fontSize: '14px' or fontSize: 14
    r'fontSize\s*:\s*[\'"]?(\d+(?:\.\d+)?(?:px|rem|em)?)[\'"]?',
    r'fontWeight\s*:\s*[\'"]?(\d+|bold|normal|light|medium)[\'"]?',
    r'lineHeight\s*:\s*[\'"]?(\d+(?:\.\d+)?(?:px|rem|em)?)[\'"]?',
    # CSS: font-size: 14px
    r'font-size\s*:\s*(\d+(?:\.\d+)?(?:px|rem|em)?)',
    r'font-weight\s*:\s*(\d+|bold|normal|light|medium)',
    r'line-height\s*:\s*(\d+(?:\.\d+)?(?:px|rem|em)?)',
]

COMPILED_PATTERNS = [re.compile(p) for p in TYPOGRAPHY_PATTERNS]


class TypographyRule(BaseRule):
    """타이포그래피 규칙"""

    name = '타이포그래피 규칙'
    description = '폰트 크기/굵기/줄간격 값이 직접 입력된 경우를 검사합니다'
    category = '타이포그래피'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues = []
        # 전체 값 사용 현황 (값 → 파일 목록)
        value_usage: Dict[str, List[str]] = defaultdict(list)

        for filepath, content in files.items():
            lines = content.splitlines()
            file_matches = []

            for line_num, line in enumerate(lines, start=1):
                for pattern in COMPILED_PATTERNS:
                    matches = pattern.findall(line)
                    for match in matches:
                        file_matches.append((line_num, line.strip(), match))
                        value_usage[match].append(filepath)

            # 규칙 1-1: 한 파일에 타이포 속성이 너무 많은 경우
            if len(file_matches) >= MAX_TYPOGRAPHY_PER_FILE:
                issues.append(self._make_issue(
                    file=filepath,
                    line=file_matches[0][0],
                    description=(
                        f'이 파일에 폰트 관련 값이 {len(file_matches)}개 직접 입력되어 있습니다. '
                        f'({MAX_TYPOGRAPHY_PER_FILE}개 이상 권고 기준 초과)'
                    ),
                    before=file_matches[0][1],
                    after='디자인 시스템 타이포그래피 토큰 사용 권고\n예: typography.body2, typography.h3 등',
                    reason=(
                        '디자인 시스템에 이미 정해진 글자 크기/굵기가 있는데, '
                        '각 파일마다 직접 숫자를 입력하면 나중에 디자인이 바뀔 때 '
                        '모든 파일을 일일이 수정해야 합니다.'
                    ),
                    severity='critical' if len(file_matches) >= MAX_TYPOGRAPHY_PER_FILE * 2 else 'warning',
                ))

        # 규칙 1-2: 동일한 값이 여러 컴포넌트에서 반복
        for value, file_list in value_usage.items():
            unique_files = list(set(file_list))
            if len(unique_files) >= MAX_DUPLICATE_COMPONENTS:
                issues.append(self._make_issue(
                    file=unique_files[0],
                    line=0,
                    description=(
                        f'폰트 값 "{value}"이(가) {len(unique_files)}개 파일에서 중복 사용됩니다.'
                    ),
                    before=f'여러 파일에서 직접: fontSize: "{value}"',
                    after='공통 스타일 또는 테마 변수로 분리',
                    reason=(
                        f'같은 값이 {len(unique_files)}개 파일에 반복되면, '
                        '디자인 변경 시 모든 파일을 수정해야 합니다. '
                        '공통 변수 하나만 바꾸면 전체가 바뀌도록 개선이 필요합니다.'
                    ),
                    severity='warning',
                ))

        return issues
