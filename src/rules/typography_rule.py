"""
[기준 1] 타이포그래피 규칙 (HAE Design System 기준)

HAE Design System의 타이포그래피 CSS 커스텀 프로퍼티(--typo-*)를 사용하지 않고
직접 폰트 관련 값을 입력한 경우를 찾아냅니다.

── HAE 타이포 토큰 체계 ──────────────────────────────────────────────────
 폰트 패밀리  : Asta Sans  →  var(--typo-font-family-asta-sans)
 폰트 굵기   : 300(light) / 400(regular) / 600(semibold) / 700(bold)
 허용 크기(px): 11 12 13 14 15 16 17 18 19 20 21 23 24 25 29 32 36 37 41 45 48 56

 ┌─────────────────────────────────────────────────────────────────────┐
 │ 카테고리     크기(px)        사용 굵기                              │
 │ body        11-20  regular+bold / 21-37 bold only                   │
 │ title       11-23  bold + semibold                                  │
 │ headline    24-37  bold / semibold / light / regular                │
 │ display     41-56  bold / semibold / regular / light                │
 │ label       small(11) / medium(13) / large(14)  regular + bold     │
 └─────────────────────────────────────────────────────────────────────┘

 사용 예:
   CSS :  font: var(--typo-body-13-regular);
   MUI :  <Typography className="typo-body-13-regular">
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from src.rules.base_rule import BaseRule


# ── HAE Design System 타이포그래피 토큰 전체 목록 ────────────────────────────
# (token_name → (font-size px, line-height px, weight_label))
HAE_TYPO_TOKENS: dict = {
    # ── Body regular (11~20px) ───────────────────────────────────────────────
    '--typo-body-11-regular': (11, 16, 'regular'),
    '--typo-body-12-regular': (12, 16, 'regular'),
    '--typo-body-13-regular': (13, 18, 'regular'),
    '--typo-body-14-regular': (14, 20, 'regular'),
    '--typo-body-15-regular': (15, 20, 'regular'),
    '--typo-body-16-regular': (16, 24, 'regular'),
    '--typo-body-17-regular': (17, 24, 'regular'),
    '--typo-body-18-regular': (18, 26, 'regular'),
    '--typo-body-19-regular': (19, 26, 'regular'),
    '--typo-body-20-regular': (20, 28, 'regular'),
    # ── Body bold (11~37px) ──────────────────────────────────────────────────
    '--typo-body-11-bold': (11, 16, 'bold'),
    '--typo-body-12-bold': (12, 16, 'bold'),
    '--typo-body-13-bold': (13, 18, 'bold'),
    '--typo-body-14-bold': (14, 20, 'bold'),
    '--typo-body-15-bold': (15, 20, 'bold'),
    '--typo-body-16-bold': (16, 24, 'bold'),
    '--typo-body-17-bold': (17, 24, 'bold'),
    '--typo-body-18-bold': (18, 26, 'bold'),
    '--typo-body-19-bold': (19, 26, 'bold'),
    '--typo-body-20-bold': (20, 28, 'bold'),
    '--typo-body-21-bold': (21, 28, 'bold'),
    '--typo-body-23-bold': (23, 30, 'bold'),
    '--typo-body-24-bold': (24, 32, 'bold'),
    '--typo-body-25-bold': (25, 36, 'bold'),
    '--typo-body-29-bold': (29, 42, 'bold'),
    '--typo-body-32-bold': (32, 40, 'bold'),
    '--typo-body-36-bold': (36, 44, 'bold'),
    '--typo-body-37-bold': (37, 54, 'bold'),
    # ── Title bold (11~23px) ─────────────────────────────────────────────────
    '--typo-title-11-bold': (11, 16, 'bold'),
    '--typo-title-12-bold': (12, 16, 'bold'),
    '--typo-title-13-bold': (13, 18, 'bold'),
    '--typo-title-14-bold': (14, 20, 'bold'),
    '--typo-title-15-bold': (15, 20, 'bold'),
    '--typo-title-16-bold': (16, 24, 'bold'),
    '--typo-title-17-bold': (17, 24, 'bold'),
    '--typo-title-18-bold': (18, 26, 'bold'),
    '--typo-title-19-bold': (19, 26, 'bold'),
    '--typo-title-20-bold': (20, 28, 'bold'),
    '--typo-title-21-bold': (21, 28, 'bold'),
    '--typo-title-23-bold': (23, 30, 'bold'),
    # ── Title semibold (11~23px) ─────────────────────────────────────────────
    '--typo-title-11-semibold': (11, 16, 'semibold'),
    '--typo-title-12-semibold': (12, 16, 'semibold'),
    '--typo-title-13-semibold': (13, 18, 'semibold'),
    '--typo-title-14-semibold': (14, 20, 'semibold'),
    '--typo-title-15-semibold': (15, 20, 'semibold'),
    '--typo-title-16-semibold': (16, 24, 'semibold'),
    '--typo-title-17-semibold': (17, 24, 'semibold'),
    '--typo-title-18-semibold': (18, 26, 'semibold'),
    '--typo-title-19-semibold': (19, 26, 'semibold'),
    '--typo-title-20-semibold': (20, 28, 'semibold'),
    '--typo-title-21-semibold': (21, 28, 'semibold'),
    '--typo-title-23-semibold': (23, 30, 'semibold'),
    # ── Headline bold / semibold / light / regular (24~37px) ─────────────────
    '--typo-headline-24-bold':     (24, 32, 'bold'),
    '--typo-headline-25-bold':     (25, 36, 'bold'),
    '--typo-headline-29-bold':     (29, 42, 'bold'),
    '--typo-headline-32-bold':     (32, 40, 'bold'),
    '--typo-headline-36-bold':     (36, 44, 'bold'),
    '--typo-headline-37-bold':     (37, 54, 'bold'),
    '--typo-headline-24-semibold': (24, 32, 'semibold'),
    '--typo-headline-25-semibold': (25, 36, 'semibold'),
    '--typo-headline-29-semibold': (29, 42, 'semibold'),
    '--typo-headline-32-semibold': (32, 40, 'semibold'),
    '--typo-headline-36-semibold': (36, 44, 'semibold'),
    '--typo-headline-37-semibold': (37, 54, 'semibold'),
    '--typo-headline-24-light':    (24, 32, 'light'),
    '--typo-headline-25-light':    (25, 36, 'light'),
    '--typo-headline-29-light':    (29, 42, 'light'),
    '--typo-headline-32-light':    (32, 40, 'light'),
    '--typo-headline-36-light':    (36, 44, 'light'),
    '--typo-headline-37-light':    (37, 54, 'light'),
    '--typo-headline-24-regular':  (24, 32, 'regular'),
    '--typo-headline-25-regular':  (25, 36, 'regular'),
    '--typo-headline-29-regular':  (29, 42, 'regular'),
    '--typo-headline-32-regular':  (32, 40, 'regular'),
    '--typo-headline-36-regular':  (36, 44, 'regular'),
    '--typo-headline-37-regular':  (37, 54, 'regular'),
    # ── Display bold / semibold / regular / light (41~56px) ──────────────────
    '--typo-display-41-bold':     (41, 56, 'bold'),
    '--typo-display-41-regular':  (41, 56, 'regular'),
    '--typo-display-41-light':    (41, 56, 'light'),
    '--typo-display-45-bold':     (45, 62, 'bold'),
    '--typo-display-45-regular':  (45, 62, 'regular'),
    '--typo-display-45-light':    (45, 62, 'light'),
    '--typo-display-48-bold':     (48, 56, 'bold'),
    '--typo-display-48-semibold': (48, 56, 'semibold'),
    '--typo-display-48-regular':  (48, 56, 'regular'),
    '--typo-display-48-light':    (48, 56, 'light'),
    '--typo-display-56-bold':     (56, 64, 'bold'),
    '--typo-display-56-semibold': (56, 64, 'semibold'),
    '--typo-display-56-regular':  (56, 64, 'regular'),
    '--typo-display-56-light':    (56, 64, 'light'),
    # ── Label (small=11px / medium=13px / large=14px) ────────────────────────
    '--typo-label-small-regular':  (11, 16, 'regular'),
    '--typo-label-medium-regular': (13, 18, 'regular'),
    '--typo-label-large-regular':  (14, 20, 'regular'),
    '--typo-label-small-bold':     (11, 16, 'bold'),
    '--typo-label-medium-bold':    (13, 18, 'bold'),
    '--typo-label-large-bold':     (14, 20, 'bold'),
}

# HAE 허용 font-size (px 정수)
HAE_VALID_SIZES_PX = frozenset({
    11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23,
    24, 25, 29, 32, 36, 37,
    41, 45, 48, 56,
})

# HAE 허용 font-weight → weight 레이블
WEIGHT_LABEL: dict = {
    '300': 'light',    'light': 'light',
    '400': 'regular',  'regular': 'regular',  'normal': 'regular',
    '600': 'semibold', 'semibold': 'semibold',
    '700': 'bold',     'bold': 'bold',
}
HAE_VALID_WEIGHTS = frozenset(WEIGHT_LABEL.keys())

# HAE 공식 폰트 패밀리에 포함되는 키워드 (소문자)
HAE_FONT_KEYWORDS = {'asta', 'asta sans', 'asta-sans'}


# ── 검출 패턴 ────────────────────────────────────────────────────────────────
_PAT_ALREADY_TOKEN  = re.compile(r'var\s*\(\s*--typo-')           # 토큰 이미 사용
_PAT_CLASS_TOKEN    = re.compile(r'typo-(?:body|title|headline|display|label)-')  # 클래스로 사용
_PAT_COMMENT_LINE   = re.compile(r'^\s*(?://|/\*|\*)')            # 주석 줄

# font-size
_PAT_FS_CSS = re.compile(r'font-size\s*:\s*(\d+(?:\.\d+)?)(px|rem|em)\b', re.I)
_PAT_FS_JSX = re.compile(r'fontSize\s*:\s*["\']?(\d+(?:\.\d+)?)(px|rem|em)?["\']?')

# font-weight
_PAT_FW_CSS = re.compile(r'font-weight\s*:\s*(\d+|bold|normal|bolder|lighter|semibold|light)\b', re.I)
_PAT_FW_JSX = re.compile(r'fontWeight\s*:\s*["\']?(\d+|bold|normal|bolder|lighter|semibold|light)["\']?', re.I)

# font-family  (var() 이미 쓴 경우 제외)
_PAT_FF_CSS = re.compile(r'font-family\s*:\s*(?!var\s*\()([^;{}\n]+)', re.I)
_PAT_FF_JSX = re.compile(r'fontFamily\s*:\s*["\']([^"\']+)["\']', re.I)


def _suggest_token(size_px: int, weight_label: str = 'regular') -> str:
    """크기·굵기에 맞는 HAE 타이포 토큰 제안 문자열 반환."""
    w = weight_label if weight_label in ('bold', 'semibold', 'regular', 'light') else 'regular'

    if size_px >= 41:                          # display
        if size_px in (41, 45):
            w2 = w if w in ('bold', 'regular', 'light') else 'bold'
        else:                                  # 48, 56
            w2 = w
        return f'var(--typo-display-{size_px}-{w2})'

    if 24 <= size_px <= 37:                    # headline
        if size_px in (24, 25, 29, 32, 36, 37):
            return f'var(--typo-headline-{size_px}-{w})'
        # 비표준 크기 → 가장 근접한 headline 크기
        closest = min({24, 25, 29, 32, 36, 37}, key=lambda x: abs(x - size_px))
        return f'var(--typo-headline-{closest}-{w})  /* {size_px}px → HAE 근접 크기 {closest}px */'

    if 11 <= size_px <= 23:                    # body / title
        if size_px in (21, 23):
            return f'var(--typo-body-{size_px}-bold)  /* {size_px}px는 bold만 지원 */'
        if w in ('bold',):
            return f'var(--typo-body-{size_px}-bold)  /* 제목류라면 var(--typo-title-{size_px}-bold) */'
        if w == 'semibold':
            return f'var(--typo-title-{size_px}-semibold)'
        return f'var(--typo-body-{size_px}-regular)'

    # 아예 HAE 범위를 벗어난 크기
    closest = min(HAE_VALID_SIZES_PX, key=lambda x: abs(x - size_px))
    return f'var(--typo-body-{closest}-{w})  /* {size_px}px는 HAE에 없음, 근접 크기 {closest}px 권고 */'


class TypographyRule(BaseRule):
    """HAE Design System 타이포그래피 토큰 미사용 검사 규칙"""

    name = '타이포그래피 규칙'
    description = ('HAE Design System 타이포그래피 토큰(--typo-*) 미사용 및 '
                   '비표준 폰트 크기·굵기·패밀리 검사')
    category = '타이포그래피'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        for filepath, content in files.items():
            ext = filepath.rsplit('.', 1)[-1].lower()
            is_css = ext in ('css', 'scss', 'sass', 'less')
            lines = content.splitlines()

            for line_num, line in enumerate(lines, 1):
                # 주석 · 빈 줄 · 이미 토큰 사용 → skip
                if _PAT_COMMENT_LINE.match(line):
                    continue
                if not line.strip():
                    continue
                if _PAT_ALREADY_TOKEN.search(line):
                    continue
                if _PAT_CLASS_TOKEN.search(line):
                    continue

                # ── Check 1: 하드코딩된 font-size ──────────────────────────
                fs_pats = [_PAT_FS_CSS] if is_css else [_PAT_FS_JSX, _PAT_FS_CSS]
                for pat in fs_pats:
                    for m in pat.finditer(line):
                        raw_val = float(m.group(1))
                        unit = (m.group(2) or 'px').lower()

                        # px로 환산 (rem=16px, 그 외는 대략적 처리)
                        if unit == 'rem':
                            px_val = raw_val * 16
                        elif unit == 'em':
                            px_val = raw_val * 16  # 기본값 기준
                        else:
                            px_val = raw_val

                        size_int = int(round(px_val))

                        # 무시할 값 (0, 또는 매우 작은 상수)
                        if size_int <= 0:
                            continue

                        in_hae = size_int in HAE_VALID_SIZES_PX
                        suggestion = _suggest_token(size_int)

                        prop_text = f'font-size: {m.group(0).split(":")[-1].strip()}' if is_css else m.group(0).strip()

                        issues.append(self._make_issue(
                            file=filepath,
                            line=line_num,
                            description=(
                                f'font-size {m.group(1)}{unit} 직접 사용 — '
                                + ('HAE Design System 토큰으로 교체 권고'
                                   if in_hae else
                                   f'⚠ {size_int}px는 HAE Design System에 없는 크기 (가장 근접 사이즈로 변경 필요)')
                            ),
                            before=line.strip(),
                            after=(
                                f'/* CSS: font shorthand 토큰 사용 */\n'
                                f'font: {suggestion};\n\n'
                                f'/* MUI: className 적용 */\n'
                                f'<Typography className="{suggestion.split("(")[1].rstrip(")/*").strip()}">'
                            ),
                            reason=(
                                'HAE Design System은 --typo-* CSS 커스텀 프로퍼티로 '
                                '폰트 크기·굵기·줄간격을 일괄 관리합니다. '
                                '하드코딩 값 사용 시 디자인 변경 대응이 어렵습니다.'
                            ),
                            severity='critical' if not in_hae else 'warning',
                        ))

                # ── Check 2: 비표준 font-weight ────────────────────────────
                fw_pats = [_PAT_FW_CSS] if is_css else [_PAT_FW_JSX, _PAT_FW_CSS]
                for pat in fw_pats:
                    for m in pat.finditer(line):
                        val = m.group(1).lower()
                        if val in HAE_VALID_WEIGHTS:
                            continue  # HAE 허용 값
                        # bolder / lighter / 500 / 800 / 900 등 비표준
                        issues.append(self._make_issue(
                            file=filepath,
                            line=line_num,
                            description=(
                                f'font-weight "{m.group(1)}"은 HAE Design System 허용 값이 아닙니다 '
                                f'(허용: 300/light · 400/regular · 600/semibold · 700/bold)'
                            ),
                            before=line.strip(),
                            after=(
                                'font-weight: 300;  /* light   */\n'
                                'font-weight: 400;  /* regular */\n'
                                'font-weight: 600;  /* semibold */\n'
                                'font-weight: 700;  /* bold    */\n\n'
                                '/* 또는 토큰 사용 */\n'
                                'font: var(--typo-body-{size}-bold);  /* 굵기 포함 */'
                            ),
                            reason=(
                                'HAE Design System은 300(light)/400(regular)/600(semibold)/700(bold) '
                                '4단계 굵기만 지원합니다. 500·800·900 등은 사용 불가합니다.'
                            ),
                            severity='critical',
                        ))

                # ── Check 3: HAE 폰트 패밀리가 아닌 경우 ──────────────────
                ff_pats = [_PAT_FF_CSS] if is_css else [_PAT_FF_JSX, _PAT_FF_CSS]
                for pat in ff_pats:
                    for m in pat.finditer(line):
                        ff_val = m.group(1).lower().strip().strip('"\'')
                        # HAE 폰트 키워드가 포함된 경우 skip
                        if any(kw in ff_val for kw in HAE_FONT_KEYWORDS):
                            continue
                        # inherit / initial / unset / var( 는 skip
                        if any(ff_val.startswith(kw) for kw in ('inherit', 'initial', 'unset', 'var(')):
                            continue

                        issues.append(self._make_issue(
                            file=filepath,
                            line=line_num,
                            description=(
                                f'font-family "{m.group(1).strip()}" — '
                                'HAE Design System 공식 폰트(Asta Sans)가 아닙니다'
                            ),
                            before=line.strip(),
                            after=(
                                '/* CSS */\n'
                                'font-family: var(--typo-font-family-asta-sans);\n\n'
                                '/* 또는 font 단축 토큰 사용 (자동 포함) */\n'
                                'font: var(--typo-body-15-regular);'
                            ),
                            reason=(
                                'HAE Design System의 공식 폰트는 "Asta Sans"입니다. '
                                'Arial, Roboto, Noto Sans 등 타 폰트 사용은 디자인 일관성을 해칩니다. '
                                '--typo-* 단축 토큰에는 폰트 패밀리가 이미 포함되어 있습니다.'
                            ),
                            severity='warning',
                        ))

        return issues
