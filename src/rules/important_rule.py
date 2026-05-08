"""
[기준 3] !important 규칙
CSS !important 과다 사용을 검사합니다.
"""
import re
from typing import Dict, List, Any
from src.rules.base_rule import BaseRule


MAX_IMPORTANT_PER_FILE = 5    # 한 파일에 이것 이상이면 경고
MAX_IMPORTANT_TOTAL = 30      # 전체에 이것 이상이면 심각 경고

IMPORTANT_PATTERN = re.compile(r'!\s*important', re.IGNORECASE)


class ImportantRule(BaseRule):
    """!important 규칙"""

    name = '!important 규칙'
    description = 'CSS !important 과다 사용을 검사합니다'
    category = '!important'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues = []
        total_count = 0

        for filepath, content in files.items():
            # CSS/SCSS 파일만 검사 (또는 JS/TS 파일 내 스타일도 검사)
            file_matches = []
            for line_num, line in enumerate(content.splitlines(), start=1):
                if IMPORTANT_PATTERN.search(line):
                    file_matches.append((line_num, line.strip()))

            total_count += len(file_matches)

            if len(file_matches) >= MAX_IMPORTANT_PER_FILE:
                occurrences = [{'line': ln, 'code': code} for ln, code in file_matches]
                issues.append(self._make_issue(
                    file=filepath,
                    line=file_matches[0][0],
                    description=(
                        f'이 파일에 !important가 {len(file_matches)}번 사용되었습니다.'
                    ),
                    before=file_matches[0][1],
                    after='CSS 선택자 우선순위 조정으로 !important 없이 해결',
                    reason=(
                        '!important는 다른 모든 스타일을 강제로 덮어씁니다. '
                        '너무 많이 사용하면 나중에 스타일 수정이 매우 어려워집니다. '
                        '꼭 필요한 경우가 아니라면 사용하지 않는 것이 좋습니다.'
                    ),
                    severity='warning',
                    occurrences=occurrences,
                ))

        # 전체 합계 경고
        if total_count >= MAX_IMPORTANT_TOTAL:
            issues.append(self._make_issue(
                file='(전체 코드)',
                line=0,
                description=(
                    f'전체 코드에서 !important가 총 {total_count}번 사용되었습니다. '
                    f'({MAX_IMPORTANT_TOTAL}개 이상은 코드 품질 문제 신호입니다)'
                ),
                before=f'!important 총 {total_count}개',
                after='각 사용처를 검토하여 CSS 우선순위로 대체',
                reason='!important가 너무 많으면 스타일 버그가 생겼을 때 원인 찾기가 매우 어렵습니다.',
                severity='critical',
            ))

        return issues
