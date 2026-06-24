"""
검수 엔진 - ZIP 파일을 압축 해제하고 각 규칙을 적용합니다
"""
import os
import zipfile
from typing import List, Dict, Any

from src.rules.typography_rule import TypographyRule
from src.rules.color_rule import ColorRule
from src.rules.important_rule import ImportantRule
from src.rules.scrollbar_rule import ScrollbarRule
from src.rules.gradient_rule import GradientRule
from src.rules.style_mixing_rule import StyleMixingRule
from src.rules.console_log_rule import ConsoleLogRule
from src.rules.zindex_rule import ZIndexRule
from src.rules.accessibility_rule import AccessibilityRule


SUPPORTED_EXTENSIONS = {'.tsx', '.ts', '.jsx', '.js', '.css', '.scss', '.html'}

RULE_MAP = {
    'typography': TypographyRule,
    'color': ColorRule,
    'important': ImportantRule,
    'scrollbar': ScrollbarRule,
    'gradient': GradientRule,
    'style_mixing': StyleMixingRule,
    'console_log': ConsoleLogRule,
    'zindex': ZIndexRule,
    'accessibility': AccessibilityRule,
}


class Reviewer:
    """퍼블리싱 코드 검수기"""

    def __init__(self, zip_path: str, selected_rules: List[str]):
        self.zip_path = zip_path
        self.selected_rules = selected_rules
        self.rules = [
            RULE_MAP[rule]()
            for rule in selected_rules
            if rule in RULE_MAP
        ]

    def run(self) -> Dict[str, Any]:
        """검수 실행"""
        # 1. ZIP 압축 해제
        files = self._extract_zip()
        self._files = files  # AI 수정 제안 컨텍스트용으로 보관

        # 2. 각 규칙 적용
        all_issues = []
        for rule in self.rules:
            issues = rule.check(files)
            all_issues.extend(issues)

        # 3. 결과 취합
        return self._build_report(files, all_issues)

    def get_files(self) -> Dict[str, str]:
        """검수에 사용된 파일 내용 반환 (AI 수정 제안 ±10줄 컨텍스트용)"""
        return getattr(self, '_files', {})

    def _extract_zip(self) -> Dict[str, str]:
        """ZIP 파일에서 소스 파일들을 추출합니다"""
        files = {}
        with zipfile.ZipFile(self.zip_path, 'r') as zf:
            for name in zf.namelist():
                _, ext = os.path.splitext(name)
                if ext.lower() in SUPPORTED_EXTENSIONS:
                    try:
                        content = zf.read(name).decode('utf-8', errors='ignore')
                        files[name] = content
                    except Exception:
                        pass
        return files

    MAX_OCCURRENCES_PER_ISSUE = 300  # 이슈당 최대 저장 건수 (메모리 보호)

    def _build_report(
        self, files: Dict[str, str], issues: List[Dict]
    ) -> Dict[str, Any]:
        """결과 리포트 생성"""
        critical = [i for i in issues if i.get('severity') == 'critical']
        warnings = [i for i in issues if i.get('severity') == 'warning']

        # 카테고리별 집계
        category_counts = {}
        for issue in issues:
            cat = issue.get('category', '기타')
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # occurrences 과다 적재 방지 (대용량 ZIP에서 MemoryError 예방)
        for issue in issues:
            occs = issue.get('occurrences', [])
            if len(occs) > self.MAX_OCCURRENCES_PER_ISSUE:
                issue['occurrences'] = occs[:self.MAX_OCCURRENCES_PER_ISSUE]

        return {
            'summary': {
                'total_files': len(files),
                'total_issues': len(issues),
                'critical': len(critical),
                'warnings': len(warnings),
                'by_category': category_counts,
            },
            'issues': issues,
        }
