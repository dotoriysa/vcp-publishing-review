"""
[기준 9] 접근성(a11y) 규칙
웹 접근성 기본 요건을 위반한 코드를 찾아냅니다.
- outline: none / outline: 0 (키보드 접근성 파괴)
- <img> alt 속성 누락 (스크린리더 대응)
- <button> type 속성 누락 (form 내 의도치 않은 submit)
"""
import re
from typing import Dict, List, Any
from src.rules.base_rule import BaseRule


# outline 제거 패턴 (CSS / sx prop)
OUTLINE_NONE_CSS = re.compile(r'outline\s*:\s*(none|0)\b', re.IGNORECASE)
OUTLINE_NONE_SX = re.compile(r'\boutline\s*:\s*[\'"]?(none|0)[\'"]?', re.IGNORECASE)

# img 태그 + alt 없음 (JSX)
IMG_NO_ALT = re.compile(r'<img\b(?![^>]*\balt\s*=)[^>]*/?\s*>', re.IGNORECASE)
# img src만 있고 alt 없는 경우 (멀티라인 대비)
IMG_TAG_OPEN = re.compile(r'<img\b', re.IGNORECASE)
ALT_ATTR = re.compile(r'\balt\s*=', re.IGNORECASE)

# button type 없음 (form 내 submit 위험)
BUTTON_NO_TYPE = re.compile(r'<button\b(?![^>]*\btype\s*=)[^>]*>', re.IGNORECASE)


class AccessibilityRule(BaseRule):
    """접근성 규칙"""

    name = '접근성(a11y) 규칙'
    description = 'outline 제거, img alt 누락, button type 누락 등 접근성 위반을 검사합니다'
    category = '접근성'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues = []

        for filepath, content in files.items():
            is_jsx = filepath.endswith(('.tsx', '.jsx'))
            is_style = filepath.endswith(('.css', '.scss'))

            outline_occs = []
            img_alt_occs = []
            button_type_occs = []

            lines = content.splitlines()

            for line_num, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('*'):
                    continue

                # outline: none 감지 (CSS 파일 또는 JSX sx prop)
                if OUTLINE_NONE_CSS.search(line) or OUTLINE_NONE_SX.search(line):
                    outline_occs.append({'line': line_num, 'code': line.strip()})

                # img alt 누락 (JSX/HTML)
                if is_jsx and IMG_TAG_OPEN.search(line):
                    # 같은 줄에 alt가 없고, 줄이 /> 또는 >로 닫히면 누락으로 판정
                    if not ALT_ATTR.search(line) and ('>' in line or '/>' in line):
                        img_alt_occs.append({'line': line_num, 'code': line.strip()})

                # button type 누락 (JSX)
                if is_jsx and BUTTON_NO_TYPE.search(line):
                    button_type_occs.append({'line': line_num, 'code': line.strip()})

            # outline: none → critical (키보드 접근성 완전 파괴)
            if outline_occs:
                issues.append(self._make_issue(
                    file=filepath,
                    line=outline_occs[0]['line'],
                    description=(
                        f'outline: none / outline: 0이 {len(outline_occs)}곳에 사용되었습니다. '
                        '키보드 접근성을 파괴하는 위반 코드입니다.'
                    ),
                    before=outline_occs[0]['code'],
                    after=(
                        '/* outline 제거 대신 커스텀 포커스 스타일 적용 */\n'
                        '&:focus-visible {\n'
                        '  outline: 2px solid colors.primary;\n'
                        '  outline-offset: 2px;\n'
                        '}'
                    ),
                    reason=(
                        'outline: none은 키보드로만 탐색하는 사용자(시각장애인, 운동장애인)의 '
                        '포커스 위치를 완전히 숨겨버립니다. '
                        '장애인차별금지법 및 WCAG 2.1 기준 위반이며, 현대오토에버 검수에서 '
                        '반드시 지적되는 항목입니다. :focus-visible 로 대체하세요.'
                    ),
                    severity='critical',
                    occurrences=outline_occs,
                ))

            # img alt 누락 → critical
            if img_alt_occs:
                issues.append(self._make_issue(
                    file=filepath,
                    line=img_alt_occs[0]['line'],
                    description=(
                        f'<img> 태그에 alt 속성이 없는 경우가 {len(img_alt_occs)}곳 있습니다. '
                        '스크린리더 사용자가 이미지 내용을 전혀 알 수 없습니다.'
                    ),
                    before=img_alt_occs[0]['code'],
                    after=(
                        '/* 의미 있는 이미지 */\n'
                        '<img src={src} alt="차량 외관 이미지" />\n\n'
                        '/* 장식용 이미지(내용 없음)는 빈 문자열 */\n'
                        '<img src={src} alt="" role="presentation" />'
                    ),
                    reason=(
                        'alt 속성이 없으면 스크린리더가 파일명을 그대로 읽어 사용자에게 혼란을 줍니다. '
                        'WCAG 2.1 가이드라인 필수 항목이자 현대오토에버 검수 기준입니다.'
                    ),
                    severity='critical',
                    occurrences=img_alt_occs,
                ))

            # button type 누락 → warning
            if button_type_occs:
                issues.append(self._make_issue(
                    file=filepath,
                    line=button_type_occs[0]['line'],
                    description=(
                        f'<button> 태그에 type 속성이 없는 경우가 {len(button_type_occs)}곳 있습니다. '
                        'form 안에 있으면 의도치 않게 submit이 발생할 수 있습니다.'
                    ),
                    before=button_type_occs[0]['code'],
                    after=(
                        '<button type="button" onClick={handleClick}>클릭</button>\n'
                        '/* 폼 제출용: type="submit", 초기화용: type="reset" */'
                    ),
                    reason=(
                        '<button>의 기본 type은 "submit"입니다. form 안에 있을 경우 '
                        '클릭 시 의도치 않게 폼이 제출될 수 있습니다. '
                        '항상 type을 명시하는 것이 안전합니다.'
                    ),
                    severity='warning',
                    occurrences=button_type_occs,
                ))

        return issues
