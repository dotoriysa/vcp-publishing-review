"""
[기준 6] 스타일링 방식 통일 규칙
MUI 프로젝트에서 인라인 스타일, sx prop, makeStyles/withStyles(deprecated)가
혼용되는 경우를 검사합니다.
"""
import re
from typing import Dict, List, Any
from src.rules.base_rule import BaseRule


# 인라인 style={{ }} 패턴 (JSX/TSX)
INLINE_STYLE_PATTERN = re.compile(r'\bstyle\s*=\s*\{\s*\{')
# MUI sx prop
SX_PROP_PATTERN = re.compile(r'\bsx\s*=\s*[{\'"]')
# deprecated makeStyles / withStyles / createStyles
MAKESTYLES_PATTERN = re.compile(r'\b(makeStyles|withStyles|createStyles)\b')


class StyleMixingRule(BaseRule):
    """스타일링 방식 통일 규칙"""

    name = '스타일링 방식 통일 규칙'
    description = 'MUI sx prop과 인라인 스타일 혼용, deprecated makeStyles/withStyles 사용을 검사합니다'
    category = '스타일링 통일'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues = []

        for filepath, content in files.items():
            # TSX/JSX/TS/JS 파일만 검사
            if not any(filepath.endswith(ext) for ext in ('.tsx', '.jsx', '.ts', '.js')):
                continue

            has_sx = bool(SX_PROP_PATTERN.search(content))
            inline_occs = []
            makestyles_occs = []

            for line_num, line in enumerate(content.splitlines(), start=1):
                if INLINE_STYLE_PATTERN.search(line):
                    inline_occs.append({'line': line_num, 'code': line.strip()})
                if MAKESTYLES_PATTERN.search(line):
                    makestyles_occs.append({'line': line_num, 'code': line.strip()})

            # 인라인 style={{}} 과 sx prop 혼용
            if has_sx and len(inline_occs) >= 2:
                issues.append(self._make_issue(
                    file=filepath,
                    line=inline_occs[0]['line'],
                    description=(
                        f'MUI sx prop과 인라인 style={{{{}}}}이 혼용되어 있습니다 '
                        f'(인라인 {len(inline_occs)}곳). 스타일링 방식을 sx prop으로 통일해야 합니다.'
                    ),
                    before=inline_occs[0]['code'],
                    after='sx prop 방식으로 통일: sx={{ color: colors.gray900, fontSize: \'14px\' }}',
                    reason=(
                        '스타일링 방식이 혼용되면 코드 일관성이 떨어지고 유지보수가 어렵습니다. '
                        'MUI v5 프로젝트에서는 sx prop을 표준 방식으로 사용해야 합니다.'
                    ),
                    severity='warning',
                    occurrences=inline_occs,
                ))
            elif not has_sx and len(inline_occs) >= 3:
                # sx prop 없이 인라인만 많이 써도 경고
                issues.append(self._make_issue(
                    file=filepath,
                    line=inline_occs[0]['line'],
                    description=(
                        f'인라인 style={{{{}}}}이 {len(inline_occs)}곳에 사용되어 있습니다. '
                        'MUI v5 표준인 sx prop 방식으로 통일을 권고합니다.'
                    ),
                    before=inline_occs[0]['code'],
                    after='sx prop 방식으로 통일: sx={{ color: colors.gray900 }}',
                    reason='인라인 스타일 남용은 테마 시스템 활용을 방해하고 일관성을 해칩니다.',
                    severity='warning',
                    occurrences=inline_occs,
                ))

            # deprecated makeStyles / withStyles
            if makestyles_occs:
                issues.append(self._make_issue(
                    file=filepath,
                    line=makestyles_occs[0]['line'],
                    description=(
                        f'MUI v5에서 deprecated된 makeStyles/withStyles/createStyles가 사용되었습니다. '
                        f'({len(makestyles_occs)}곳)'
                    ),
                    before=makestyles_occs[0]['code'],
                    after=(
                        'sx prop 또는 styled() 컴포넌트 방식으로 교체하세요.\n'
                        '예: const StyledBox = styled(Box)(({ theme }) => ({ color: theme.palette.primary.main }));'
                    ),
                    reason=(
                        'makeStyles/withStyles는 MUI v4 방식으로 MUI v5에서는 공식 deprecated입니다. '
                        '향후 MUI 업그레이드 시 오류가 발생할 수 있습니다.'
                    ),
                    severity='warning',
                    occurrences=makestyles_occs,
                ))

        return issues
