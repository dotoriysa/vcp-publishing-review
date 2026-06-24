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

# HAE Design System 팔레트 토큰 전체 매핑 (hex 소문자 → CSS 커스텀 프로퍼티)
# 출처: https://ux-standard.hyundai-autoever.com/react/1.1.1 (Design Tokens / Variables)
# ※ 477개 토큰 중 직접 hex 매핑 가능한 팔레트 토큰 전부 포함
#   시멘틱 토큰(--color-light-text-* 등)은 hex 값이 테마에 따라 가변이므로 별도 안내
HAE_COLOR_TOKENS: dict = {
    # ── Common Blue (20 steps) ─────────────────────────────────────────────
    '#001133': 'var(--color-common-blue-10)',
    '#001642': 'var(--color-common-blue-15)',
    '#002061': 'var(--color-common-blue-20)',
    '#00287a': 'var(--color-common-blue-25)',
    '#003399': 'var(--color-common-blue-30)',
    '#003cb2': 'var(--color-common-blue-35)',
    '#0045cc': 'var(--color-common-blue-40)',
    '#004de5': 'var(--color-common-blue-45)',
    '#0056ff': 'var(--color-common-blue-50)',
    '#1a67ff': 'var(--color-common-blue-55)',
    '#3378ff': 'var(--color-common-blue-60)',
    '#5289ff': 'var(--color-common-blue-65)',
    '#6b9aff': 'var(--color-common-blue-70)',
    '#85abff': 'var(--color-common-blue-75)',
    '#9ebdff': 'var(--color-common-blue-80)',
    '#b8cdff': 'var(--color-common-blue-85)',
    '#c7d8ff': 'var(--color-common-blue-90)',
    '#d6e2ff': 'var(--color-common-blue-92)',
    '#e5edff': 'var(--color-common-blue-95)',
    '#f5f8ff': 'var(--color-common-blue-98)',
    # ── Common Gray (20 steps) ─────────────────────────────────────────────
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
    # ── Common Green (20 steps) ────────────────────────────────────────────
    '#002418': 'var(--color-common-green-10)',
    '#003322': 'var(--color-common-green-15)',
    '#01412b': 'var(--color-common-green-20)',
    '#005236': 'var(--color-common-green-25)',
    '#006141': 'var(--color-common-green-30)',
    '#02744e': 'var(--color-common-green-35)',
    '#09865c': 'var(--color-common-green-40)',
    '#17966c': 'var(--color-common-green-45)',
    '#24a67b': 'var(--color-common-green-50)',
    '#2ab486': 'var(--color-common-green-55)',
    '#48c198': 'var(--color-common-green-60)',
    '#63caa8': 'var(--color-common-green-65)',
    '#76d0b2': 'var(--color-common-green-70)',
    '#8ed7bf': 'var(--color-common-green-75)',
    '#a9e0cf': 'var(--color-common-green-80)',
    '#bae8da': 'var(--color-common-green-85)',
    '#cdefe3': 'var(--color-common-green-90)',
    '#ddf3eb': 'var(--color-common-green-92)',
    '#e8f7f2': 'var(--color-common-green-95)',
    '#f4faf8': 'var(--color-common-green-98)',
    # ── Common Lime (20 steps) ─────────────────────────────────────────────
    '#162108': 'var(--color-common-lime-10)',
    '#24350d': 'var(--color-common-lime-15)',
    '#354e13': 'var(--color-common-lime-20)',
    '#436218': 'var(--color-common-lime-25)',
    '#547a1f': 'var(--color-common-lime-30)',
    '#628f24': 'var(--color-common-lime-35)',
    '#70a329': 'var(--color-common-lime-40)',
    '#7eb82e': 'var(--color-common-lime-45)',
    '#8ccc33': 'var(--color-common-lime-50)',
    '#98d147': 'var(--color-common-lime-55)',
    '#a3d65c': 'var(--color-common-lime-60)',
    '#afdb70': 'var(--color-common-lime-65)',
    '#bae085': 'var(--color-common-lime-70)',
    '#c8e79d': 'var(--color-common-lime-75)',
    '#d1ebad': 'var(--color-common-lime-80)',
    '#daefbe': 'var(--color-common-lime-85)',
    '#e6f4d2': 'var(--color-common-lime-90)',
    '#edf7de': 'var(--color-common-lime-92)',
    '#f4faeb': 'var(--color-common-lime-95)',
    '#f8fcf3': 'var(--color-common-lime-98)',
    # ── Common Magenta (20 steps) ──────────────────────────────────────────
    '#310221': 'var(--color-common-magenta-10)',
    '#490432': 'var(--color-common-magenta-15)',
    '#610542': 'var(--color-common-magenta-20)',
    '#790653': 'var(--color-common-magenta-25)',
    '#920764': 'var(--color-common-magenta-30)',
    '#aa0974': 'var(--color-common-magenta-35)',
    '#b8097e': 'var(--color-common-magenta-40)',
    '#c70a88': 'var(--color-common-magenta-45)',
    '#db0a96': 'var(--color-common-magenta-50)',
    '#e90c9f': 'var(--color-common-magenta-55)',
    '#f425af': 'var(--color-common-magenta-60)',
    '#f647bb': 'var(--color-common-magenta-65)',
    '#f764c6': 'var(--color-common-magenta-70)',
    '#f87ccf': 'var(--color-common-magenta-75)',
    '#fa9edb': 'var(--color-common-magenta-80)',
    '#fbb6e4': 'var(--color-common-magenta-85)',
    '#fdceed': 'var(--color-common-magenta-90)',
    '#fdd8f1': 'var(--color-common-magenta-92)',
    '#fee7f6': 'var(--color-common-magenta-95)',
    '#fff5fb': 'var(--color-common-magenta-98)',
    # ── Common Orange (20 steps) ───────────────────────────────────────────
    '#331600': 'var(--color-common-orange-10)',
    '#4d2100': 'var(--color-common-orange-15)',
    '#662c00': 'var(--color-common-orange-20)',
    '#803700': 'var(--color-common-orange-25)',
    '#994200': 'var(--color-common-orange-30)',
    '#b24d00': 'var(--color-common-orange-35)',
    '#cc5800': 'var(--color-common-orange-40)',
    '#e56300': 'var(--color-common-orange-45)',
    '#fe6e00': 'var(--color-common-orange-50)',
    '#ff7d1a': 'var(--color-common-orange-55)',
    '#ff8b33': 'var(--color-common-orange-60)',
    '#ff9a4d': 'var(--color-common-orange-65)',
    '#ffa866': 'var(--color-common-orange-70)',
    '#ffb780': 'var(--color-common-orange-75)',
    '#ffc599': 'var(--color-common-orange-80)',
    '#ffd4b2': 'var(--color-common-orange-85)',
    '#ffdfc7': 'var(--color-common-orange-90)',
    '#ffe8d6': 'var(--color-common-orange-92)',
    '#ffeee0': 'var(--color-common-orange-95)',
    '#fff6f0': 'var(--color-common-orange-98)',
    # ── Common Purple (20 steps) ───────────────────────────────────────────
    '#2d0637': 'var(--color-common-purple-10)',
    '#40094e': 'var(--color-common-purple-15)',
    '#4f0b60': 'var(--color-common-purple-20)',
    '#5e0d73': 'var(--color-common-purple-25)',
    '#710f8a': 'var(--color-common-purple-30)',
    '#8412a1': 'var(--color-common-purple-35)',
    '#9714b8': 'var(--color-common-purple-40)',
    '#aa17cf': 'var(--color-common-purple-45)',
    '#be1ee6': 'var(--color-common-purple-50)',
    '#c330e8': 'var(--color-common-purple-55)',
    '#ca47eb': 'var(--color-common-purple-60)',
    '#d15eed': 'var(--color-common-purple-65)',
    '#d775f0': 'var(--color-common-purple-70)',
    '#de8cf2': 'var(--color-common-purple-75)',
    '#e4a3f5': 'var(--color-common-purple-80)',
    '#ebbaf7': 'var(--color-common-purple-85)',
    '#f0cdf9': 'var(--color-common-purple-90)',
    '#f4dafb': 'var(--color-common-purple-92)',
    '#f8e8fc': 'var(--color-common-purple-95)',
    '#fcf7fd': 'var(--color-common-purple-98)',
    # ── Common Red (20 steps) ──────────────────────────────────────────────
    '#380101': 'var(--color-common-red-10)',
    '#5b0101': 'var(--color-common-red-15)',
    '#740101': 'var(--color-common-red-20)',
    '#920101': 'var(--color-common-red-25)',
    '#ac0202': 'var(--color-common-red-30)',
    '#bf0303': 'var(--color-common-red-35)',
    '#d30303': 'var(--color-common-red-40)',
    '#e70404': 'var(--color-common-red-45)',
    '#fa0505': 'var(--color-common-red-50)',
    '#fb2d2d': 'var(--color-common-red-55)',
    '#fb4646': 'var(--color-common-red-60)',
    '#fb5a5a': 'var(--color-common-red-65)',
    '#fc7878': 'var(--color-common-red-70)',
    '#fd9191': 'var(--color-common-red-75)',
    '#fdaaaa': 'var(--color-common-red-80)',
    '#fec3c3': 'var(--color-common-red-85)',
    '#fed7d7': 'var(--color-common-red-90)',
    '#fee1e1': 'var(--color-common-red-92)',
    '#feeaea': 'var(--color-common-red-95)',
    '#fef4f4': 'var(--color-common-red-98)',
    # ── Common Teal (20 steps) ─────────────────────────────────────────────
    '#061c23': 'var(--color-common-teal-10)',
    '#0a2d38': 'var(--color-common-teal-15)',
    '#0f4152': 'var(--color-common-teal-20)',
    '#13566d': 'var(--color-common-teal-25)',
    '#176782': 'var(--color-common-teal-30)',
    '#1b7898': 'var(--color-common-teal-35)',
    '#1f8aad': 'var(--color-common-teal-40)',
    '#229bc3': 'var(--color-common-teal-45)',
    '#26acd9': 'var(--color-common-teal-50)',
    '#3cb4dd': 'var(--color-common-teal-55)',
    '#52bde0': 'var(--color-common-teal-60)',
    '#67c5e4': 'var(--color-common-teal-65)',
    '#7dcde8': 'var(--color-common-teal-70)',
    '#93d6ec': 'var(--color-common-teal-75)',
    '#a8def0': 'var(--color-common-teal-80)',
    '#bee6f4': 'var(--color-common-teal-85)',
    '#cfedf7': 'var(--color-common-teal-90)',
    '#dcf2f9': 'var(--color-common-teal-92)',
    '#e9f7fb': 'var(--color-common-teal-95)',
    '#f6fcfd': 'var(--color-common-teal-98)',
    # ── Common Violet (20 steps) ───────────────────────────────────────────
    '#1f0042': 'var(--color-common-violet-10)',
    '#300066': 'var(--color-common-violet-15)',
    '#3c027d': 'var(--color-common-violet-20)',
    '#480396': 'var(--color-common-violet-25)',
    '#5103ab': 'var(--color-common-violet-30)',
    '#5d03c4': 'var(--color-common-violet-35)',
    '#6903dd': 'var(--color-common-violet-40)',
    '#7504f6': 'var(--color-common-violet-45)',
    '#8219fa': 'var(--color-common-violet-50)',
    '#8c32fb': 'var(--color-common-violet-55)',
    '#9648fb': 'var(--color-common-violet-60)',
    '#a666ff': 'var(--color-common-violet-65)',
    '#b180ff': 'var(--color-common-violet-70)',
    '#be99ff': 'var(--color-common-violet-75)',
    '#cbb1fc': 'var(--color-common-violet-80)',
    '#d7c5fb': 'var(--color-common-violet-85)',
    '#e2d5fb': 'var(--color-common-violet-90)',
    '#e7dffc': 'var(--color-common-violet-92)',
    '#f0ecfd': 'var(--color-common-violet-95)',
    '#f8f7fd': 'var(--color-common-violet-98)',
    # ── Common Yellow (20 steps) ───────────────────────────────────────────
    '#332600': 'var(--color-common-yellow-10)',
    '#523d00': 'var(--color-common-yellow-15)',
    '#7a5c00': 'var(--color-common-yellow-20)',
    '#997300': 'var(--color-common-yellow-25)',
    '#b28600': 'var(--color-common-yellow-30)',
    '#c79500': 'var(--color-common-yellow-35)',
    '#d6a000': 'var(--color-common-yellow-40)',
    '#e8af02': 'var(--color-common-yellow-45)',
    '#f4b806': 'var(--color-common-yellow-50)',
    '#f9c11a': 'var(--color-common-yellow-55)',
    '#fac833': 'var(--color-common-yellow-60)',
    '#facf4c': 'var(--color-common-yellow-65)',
    '#fbd460': 'var(--color-common-yellow-70)',
    '#fbda74': 'var(--color-common-yellow-75)',
    '#fcdf88': 'var(--color-common-yellow-80)',
    '#fce49c': 'var(--color-common-yellow-85)',
    '#fdeaaf': 'var(--color-common-yellow-90)',
    '#fdefc3': 'var(--color-common-yellow-92)',
    '#fef4d7': 'var(--color-common-yellow-95)',
    '#fefaeb': 'var(--color-common-yellow-98)',
    # ── Genesis Primary (20 steps) ────────────────────────────────────────
    '#111111': 'var(--color-genesis-primary-10)',
    '#252527': 'var(--color-genesis-primary-15)',
    '#323234': 'var(--color-genesis-primary-20)',
    '#3e3e41': 'var(--color-genesis-primary-25)',
    '#4b4b4e': 'var(--color-genesis-primary-30)',
    '#57575b': 'var(--color-genesis-primary-35)',
    '#646468': 'var(--color-genesis-primary-40)',
    '#707075': 'var(--color-genesis-primary-45)',
    '#7d7d83': 'var(--color-genesis-primary-50)',
    '#8a8a8f': 'var(--color-genesis-primary-55)',
    '#97979b': 'var(--color-genesis-primary-60)',
    '#a4a4a8': 'var(--color-genesis-primary-65)',
    '#b1b1b5': 'var(--color-genesis-primary-70)',
    '#bebec1': 'var(--color-genesis-primary-75)',
    '#cccccc': 'var(--color-genesis-primary-80)',
    '#d9d9d9': 'var(--color-genesis-primary-85)',
    '#e3e3e3': 'var(--color-genesis-primary-90)',
    '#ebebeb': 'var(--color-genesis-primary-92)',
    '#f2f2f2': 'var(--color-genesis-primary-95)',
    '#fafafb': 'var(--color-genesis-primary-98)',
    # ── Genesis Secondary (20 steps) ──────────────────────────────────────
    '#190e0b': 'var(--color-genesis-secondary-10)',
    '#2f1a14': 'var(--color-genesis-secondary-15)',
    '#44271d': 'var(--color-genesis-secondary-20)',
    '#563124': 'var(--color-genesis-secondary-25)',
    '#6c3d2d': 'var(--color-genesis-secondary-30)',
    '#7d4735': 'var(--color-genesis-secondary-35)',
    '#90513c': 'var(--color-genesis-secondary-40)',
    '#a15b44': 'var(--color-genesis-secondary-45)',
    '#af6249': 'var(--color-genesis-secondary-50)',
    '#bb755d': 'var(--color-genesis-secondary-55)',
    '#c3846f': 'var(--color-genesis-secondary-60)',
    '#ca9381': 'var(--color-genesis-secondary-65)',
    '#d2a393': 'var(--color-genesis-secondary-70)',
    '#d9b2a5': 'var(--color-genesis-secondary-75)',
    '#e1c2b7': 'var(--color-genesis-secondary-80)',
    '#e8d1c9': 'var(--color-genesis-secondary-85)',
    '#ede8d8': 'var(--color-genesis-secondary-90)',
    '#f4e7e2': 'var(--color-genesis-secondary-92)',
    '#f9f0ec': 'var(--color-genesis-secondary-95)',
    '#fdf9f7': 'var(--color-genesis-secondary-98)',
    # ── Hyundai Primary (20 steps) — VCP 대표 브랜드 ──────────────────────
    '#001124': 'var(--color-hyundai-primary-10)',
    '#001833': 'var(--color-hyundai-primary-15)',
    '#00244d': 'var(--color-hyundai-primary-20)',
    '#002c5f': 'var(--color-hyundai-primary-25)',   # ★ 현대 대표 브랜드 블루
    '#00397a': 'var(--color-hyundai-primary-30)',
    '#004799': 'var(--color-hyundai-primary-35)',
    '#0053b2': 'var(--color-hyundai-primary-40)',
    '#005fcc': 'var(--color-hyundai-primary-45)',
    '#006be5': 'var(--color-hyundai-primary-50)',
    '#0177ff': 'var(--color-hyundai-primary-55)',
    '#1984ff': 'var(--color-hyundai-primary-60)',
    '#3392ff': 'var(--color-hyundai-primary-65)',
    '#4ca0ff': 'var(--color-hyundai-primary-70)',
    '#66adff': 'var(--color-hyundai-primary-75)',
    '#85beff': 'var(--color-hyundai-primary-80)',
    '#a3ceff': 'var(--color-hyundai-primary-85)',
    '#bddcff': 'var(--color-hyundai-primary-90)',
    '#d1e7ff': 'var(--color-hyundai-primary-92)',
    '#e5f1ff': 'var(--color-hyundai-primary-95)',
    '#f5faff': 'var(--color-hyundai-primary-98)',
    # ── Hyundai Secondary (20 steps) ──────────────────────────────────────
    '#002129': 'var(--color-hyundai-secondary-10)',
    '#002a33': 'var(--color-hyundai-secondary-15)',
    '#003642': 'var(--color-hyundai-secondary-20)',
    '#004352': 'var(--color-hyundai-secondary-25)',
    '#005366': 'var(--color-hyundai-secondary-30)',
    '#006980': 'var(--color-hyundai-secondary-35)',
    '#007d99': 'var(--color-hyundai-secondary-40)',
    '#0092b3': 'var(--color-hyundai-secondary-45)',
    '#00aad2': 'var(--color-hyundai-secondary-50)',
    '#04c1ec': 'var(--color-hyundai-secondary-55)',
    '#1fd1f9': 'var(--color-hyundai-secondary-60)',
    '#51dbfb': 'var(--color-hyundai-secondary-65)',
    '#6ae1fb': 'var(--color-hyundai-secondary-70)',
    '#85e4fa': 'var(--color-hyundai-secondary-75)',
    '#9deafb': 'var(--color-hyundai-secondary-80)',
    '#b7effb': 'var(--color-hyundai-secondary-85)',
    '#caf3fc': 'var(--color-hyundai-secondary-90)',
    '#d8f6fd': 'var(--color-hyundai-secondary-92)',
    '#e6f9fe': 'var(--color-hyundai-secondary-95)',
    '#f5fcfe': 'var(--color-hyundai-secondary-98)',
    # ── KIA Primary (20 steps) ────────────────────────────────────────────
    '#05141f': 'var(--color-kia-primary-10)',
    '#172430': 'var(--color-kia-primary-15)',
    '#25313c': 'var(--color-kia-primary-20)',
    '#303c47': 'var(--color-kia-primary-25)',
    '#3f4b55': 'var(--color-kia-primary-30)',
    '#49555f': 'var(--color-kia-primary-35)',
    '#636b74': 'var(--color-kia-primary-40)',
    '#6a737c': 'var(--color-kia-primary-45)',
    '#778088': 'var(--color-kia-primary-50)',
    '#828a90': 'var(--color-kia-primary-55)',
    '#919aa1': 'var(--color-kia-primary-60)',
    '#9ba2a9': 'var(--color-kia-primary-65)',
    '#b2b8bd': 'var(--color-kia-primary-70)',
    '#bbc0c4': 'var(--color-kia-primary-75)',
    '#ccd0d3': 'var(--color-kia-primary-80)',
    '#dbdee1': 'var(--color-kia-primary-85)',
    '#e7e9ec': 'var(--color-kia-primary-90)',
    '#edf0f2': 'var(--color-kia-primary-92)',
    '#f2f4f6': 'var(--color-kia-primary-95)',
    # ── KIA Secondary (20 steps) ──────────────────────────────────────────
    '#0f2009': 'var(--color-kia-secondary-10)',
    '#18350d': 'var(--color-kia-secondary-15)',
    '#244e13': 'var(--color-kia-secondary-20)',
    '#33691e': 'var(--color-kia-secondary-25)',
    '#3f7a1f': 'var(--color-kia-secondary-30)',
    '#468f13': 'var(--color-kia-secondary-35)',
    '#509b17': 'var(--color-kia-secondary-40)',
    '#5fa91e': 'var(--color-kia-secondary-45)',
    '#77b239': 'var(--color-kia-secondary-50)',
    '#8bc34a': 'var(--color-kia-secondary-55)',
    '#9dcc66': 'var(--color-kia-secondary-60)',
    '#a9d279': 'var(--color-kia-secondary-65)',
    '#b8da90': 'var(--color-kia-secondary-70)',
    '#c5e1a5': 'var(--color-kia-secondary-75)',
    '#cee6b2': 'var(--color-kia-secondary-80)',
    '#d5eabe': 'var(--color-kia-secondary-85)',
    '#dcedc8': 'var(--color-kia-secondary-90)',
    '#e7f2d9': 'var(--color-kia-secondary-92)',
    '#f1f8e9': 'var(--color-kia-secondary-95)',
    '#f8fcf4': 'var(--color-kia-secondary-98)',
    # ── 기타 (White / Black / Expressive) ────────────────────────────────
    '#ffffff': 'var(--color-genesis-alpha-white) 또는 #fff 직접 사용 가능',
    '#000000': 'var(--color-genesis-alpha-gray) 또는 #000 직접 사용 가능',
}

# 하위 호환용 alias
HMG_DESIGN_COLORS = HAE_COLOR_TOKENS

# 색상 패턴 (3자리 또는 6자리 hex)
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
                suggestion = HAE_COLOR_TOKENS.get(color, HAE_COLOR_TOKENS.get(color_upper, ''))
                after_text = (
                    f'HAE Design System 토큰 사용: {suggestion}'
                    if suggestion
                    else 'HAE Design System 시멘틱 토큰 사용 권고 (예: var(--color-light-text-neutral-strongest))'
                )
                occurrences = [
                    {'line': ln, 'code': code, 'file': fp}
                    for fp, ln, code in usages[:300]
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
                        'HAE Design System의 CSS 커스텀 프로퍼티를 사용하면 한 번만 바꾸면 됩니다.'
                    ),
                    severity='critical' if len(usages) >= MAX_COLOR_DUPLICATES * 2 else 'warning',
                    occurrences=occurrences,
                ))

            # 규칙 2-2: HAE 디자인 시스템 색상을 직접 입력한 경우 (2회 이상)
            elif color in HAE_COLOR_TOKENS or color_upper in HAE_COLOR_TOKENS:
                suggestion = HAE_COLOR_TOKENS.get(color) or HAE_COLOR_TOKENS.get(color_upper, '')
                if len(usages) > 1:
                    occurrences = [
                        {'line': ln, 'code': code, 'file': fp}
                        for fp, ln, code in usages[:300]
                    ]
                    issues.append(self._make_issue(
                        file=usages[0][0],
                        line=usages[0][1],
                        description=(
                            f'HAE Design System 색상 "{color}"이(가) '
                            f'{len(usages)}번 직접 입력되었습니다.'
                        ),
                        before=usages[0][2],
                        after=(
                            f'/* CSS */\n'
                            f'color: {suggestion};\n\n'
                            f'/* MUI sx prop */\n'
                            f"sx={{{{ color: '{suggestion}' }}}}"
                        ),
                        reason=(
                            f'이 색상({color})은 HAE Design System 토큰({suggestion})과 일치합니다. '
                            '직접 입력 대신 CSS 커스텀 프로퍼티를 사용하면 브랜드 가이드라인 준수 및 '
                            '테마 전환이 용이해집니다.'
                        ),
                        severity='warning',
                        occurrences=occurrences,
                    ))

        return issues
