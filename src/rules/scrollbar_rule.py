"""
[기준 4] 스크롤바 규칙
웹킷 전용 스크롤바 스타일만 있고 다른 브라우저 대응이 없는 경우를 찾아냅니다.
"""
import re
from typing import Dict, List, Any
from src.rules.base_rule import BaseRule


WEBKIT_SCROLLBAR = re.compile(r'::-webkit-scrollbar')
STANDARD_SCROLLBAR = re.compile(r'scrollbar-width|scrollbar-color')
SCROLLBAR_SX_IMPORT = re.compile(r'scrollbarSx')


class ScrollbarRule(BaseRule):
    """스크롤바 규칙"""

    name = '스크롤바 규칙'
    description = '브라우저 호환성 없는 스크롤바 스타일링을 검사합니다'
    category = '스크롤바'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues = []

        for filepath, content in files.items():
            has_webkit = bool(WEBKIT_SCROLLBAR.search(content))
            has_standard = bool(STANDARD_SCROLLBAR.search(content))
            has_scrollbar_sx = bool(SCROLLBAR_SX_IMPORT.search(content))

            if has_webkit and not has_standard and not has_scrollbar_sx:
                # 웹킷 스크롤바만 있고 표준 속성이 없는 경우
                line_num = 0
                before_code = ''
                for i, line in enumerate(content.splitlines(), start=1):
                    if '::-webkit-scrollbar' in line:
                        line_num = i
                        before_code = line.strip()
                        break

                issues.append(self._make_issue(
                    file=filepath,
                    line=line_num,
                    description=(
                        '스크롤바 스타일이 크롬/사파리(웹킷)에서만 적용됩니다. '
                        '파이어폭스 등 다른 브라우저에서는 스크롤바가 다르게 보일 수 있습니다.'
                    ),
                    before=before_code,
                    after=(
                        '방법 1: scrollbarWidth: \'thin\' 등 표준 CSS 속성 추가\n'
                        '방법 2: @/shared/theme에서 scrollbarSx 유틸리티 가져와 재사용'
                    ),
                    reason=(
                        '웹사이트는 다양한 브라우저(크롬, 파이어폭스, 엣지 등)에서 열립니다. '
                        'Chrome/Safari에서만 동작하는 스크롤바 스타일 대신 '
                        '모든 브라우저에서 동작하는 표준 방식을 함께 사용해야 합니다.'
                    ),
                    severity='warning',
                ))

        return issues
