# 새로운 검수 기준 추가 방법

새로운 피드백을 받았을 때 검수 기준을 추가하는 방법입니다.

## 1단계: 규칙 파일 만들기

`src/rules/` 폴더에 새 파일을 만듭니다.
파일 이름은 영어로 짓습니다 (예: `new_rule.py`).

```python
# src/rules/new_rule.py
"""
[기준 N] 새로운 규칙 이름
규칙에 대한 설명을 여기에 씁니다.
"""
from typing import Dict, List, Any
from src.rules.base_rule import BaseRule


class NewRule(BaseRule):
    """새로운 규칙"""

    name = '새로운 규칙 이름'
    description = '이 규칙이 무엇을 검사하는지 설명'
    category = '카테고리명'

    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        issues = []

        for filepath, content in files.items():
            # 여기에 검사 로직을 작성합니다
            if '검사할 패턴' in content:
                issues.append(self._make_issue(
                    file=filepath,
                    line=1,
                    description='무엇이 문제인지 설명 (기획자가 이해할 수 있게)',
                    before='수정 전 코드 예시',
                    after='수정 후 코드 예시',
                    reason='왜 수정해야 하는지 이유',
                    severity='warning',  # 'critical' 또는 'warning'
                ))

        return issues
```

## 2단계: 검수 엔진에 등록하기

`src/reviewer.py` 파일을 열어 두 줄을 추가합니다:

```python
# 1. import 추가 (파일 상단)
from src.rules.new_rule import NewRule

# 2. RULE_MAP에 추가
RULE_MAP = {
    'typography': TypographyRule,
    'color': ColorRule,
    'important': ImportantRule,
    'scrollbar': ScrollbarRule,
    'new_rule': NewRule,  # ← 이 줄 추가
}
```

## 3단계: UI에 추가하기 (선택사항)

`templates/index.html`에서 규칙 선택 목록에 추가:

```html
<label class="rule-item">
    <input type="checkbox" name="rules" value="new_rule" checked>
    <div class="rule-content">
        <span class="rule-icon">🆕</span>
        <span class="rule-name">새로운 규칙</span>
        <span class="rule-desc">이 규칙이 무엇을 검사하는지 한 줄 설명</span>
    </div>
</label>
```

## 4단계: 문서 업데이트

`docs/standards/` 폴더에 새 기준을 설명하는 문서를 추가하거나
기존 `autoever_feedback.md`를 업데이트합니다.

---

**tip**: 새로운 피드백 메일이 올 때마다 이 과정을 반복하면 됩니다!
