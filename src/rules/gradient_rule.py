"""
[기준 5] 그라데이션 규칙
CSS 그라데이션 값을 직접 하드코딩한 경우를 찾아냅니다.
"""
import re
from typing import Dict, List, Any
from src.rules.base_rule import BaseRule


GRADIENT_PATTERN = re.compile(
    r'(linear-gradient|radial-gradient|conic-gradient)\s*\(',
    re.IGNORECASE
)


class GradientRule(BaseRule):
    """그라데이션 규칙"""

    name = '그라데이션 규칙'
    description = 'CSS 그라데이션 값이 직접 하드코딩된 경우를 검사합니다'
    category = '그라데이션'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues = []

        for filepath, content in files.items():
            occurrences = []
            for line_num, line in enumerate(content.splitlines(), start=1):
                if GRADIENT_PATTERN.search(line):
                    occurrences.append({'line': line_num, 'code': line.strip()})

            if len(occurrences) >= 2:
                issues.append(self._make_issue(
                    file=filepath,
                    line=occurrences[0]['line'],
                    description=(
                        f'그라데이션 값이 {len(occurrences)}곳에 직접 하드코딩되어 있습니다. '
                        'HMG 디자인 시스템 변수나 공통 상수로 분리해야 합니다.'
                    ),
                    before=occurrences[0]['code'],
                    after=(
                        'HMG 디자인 시스템 그라데이션 변수 또는 프로젝트 공통 상수로 분리\n'
                        '예: const GRADIENT_MAIN = \'linear-gradient(...)\';\n'
                        '    sx={{ background: GRADIENT_MAIN }}'
                    ),
                    reason=(
                        '그라데이션 값을 여러 곳에 직접 입력하면 디자인 변경 시 '
                        '모든 파일을 찾아 수동으로 수정해야 합니다. '
                        '공통 변수로 분리하면 한 곳만 수정해도 됩니다.'
                    ),
                    severity='warning',
                    occurrences=occurrences,
                ))
            elif len(occurrences) == 1:
                # 1개도 하드코딩이면 경고 (단, warning 수준)
                issues.append(self._make_issue(
                    file=filepath,
                    line=occurrences[0]['line'],
                    description=(
                        '그라데이션 값이 직접 하드코딩되어 있습니다. '
                        'HMG 디자인 시스템 변수나 공통 상수로 분리를 권고합니다.'
                    ),
                    before=occurrences[0]['code'],
                    after=(
                        'HMG 디자인 시스템 그라데이션 변수 또는 공통 상수 참조'
                    ),
                    reason='그라데이션 값을 직접 입력하면 디자인 변경 시 수동 수정이 필요합니다.',
                    severity='warning',
                    occurrences=occurrences,
                ))

        return issues
