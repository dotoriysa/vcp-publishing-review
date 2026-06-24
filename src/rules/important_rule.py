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
# 한 줄에 !important가 2개 이상인 패턴
MULTI_IMPORTANT_LINE = re.compile(r'(!\s*important.*?){2,}', re.IGNORECASE)


class ImportantRule(BaseRule):
    """!important 규칙"""

    name = '!important 규칙'
    description = 'CSS !important 과다 사용을 검사합니다'
    category = '!important'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues = []
        total_count = 0

        for filepath, content in files.items():
            file_matches = []
            multi_important_occs = []

            for line_num, line in enumerate(content.splitlines(), start=1):
                if IMPORTANT_PATTERN.search(line):
                    file_matches.append((line_num, line.strip()))
                    # 한 줄에 !important가 2개 이상인 경우 별도 감지
                    if len(IMPORTANT_PATTERN.findall(line)) >= 2:
                        multi_important_occs.append({'line': line_num, 'code': line.strip()})

            total_count += len(file_matches)

            # 한 줄에 !important 2개 이상 → 즉시 경고 (파일당 임계값 무관)
            if multi_important_occs:
                issues.append(self._make_issue(
                    file=filepath,
                    line=multi_important_occs[0]['line'],
                    description=(
                        f'한 줄에 !important가 2개 이상 사용된 코드가 {len(multi_important_occs)}건 있습니다. '
                        '이는 CSS 구조 설계가 잘못된 신호입니다.'
                    ),
                    before=multi_important_occs[0]['code'],
                    after='각 속성을 별도 줄로 분리하고 !important 사용 자체를 제거하세요.',
                    reason=(
                        '한 줄에 !important를 여러 번 쓰는 것은 CSS specificity 구조가 근본적으로 '
                        '잘못되었다는 신호입니다. 반드시 구조를 재검토해야 합니다.'
                    ),
                    severity='critical',
                    occurrences=multi_important_occs,
                ))

            if len(file_matches) >= MAX_IMPORTANT_PER_FILE:
                occurrences = [{'line': ln, 'code': code} for ln, code in file_matches]
                issues.append(self._make_issue(
                    file=filepath,
                    line=file_matches[0][0],
                    description=(
                        f'이 파일에 !important가 {len(file_matches)}번 사용되었습니다. '
                        f'({MAX_IMPORTANT_PER_FILE}개 이상은 기준 위반입니다)'
                    ),
                    before=file_matches[0][1],
                    after='CSS 선택자 명시도(specificity)를 높여 !important 없이 해결',
                    reason=(
                        '!important는 모든 스타일 규칙을 강제로 덮어씁니다. '
                        '많이 사용할수록 스타일 버그 발생 시 원인 파악이 불가능에 가까워집니다. '
                        '꼭 필요한 경우 1개 파일에 1~2개로 제한하세요.'
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
