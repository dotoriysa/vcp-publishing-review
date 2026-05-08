"""
검수 규칙 기본 클래스
새로운 규칙을 추가할 때 이 클래스를 상속받아 구현합니다.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseRule(ABC):
    """검수 규칙 기본 클래스"""

    # 규칙 이름 (한글)
    name: str = ''
    # 규칙 설명 (비개발자용)
    description: str = ''
    # 카테고리
    category: str = ''

    @abstractmethod
    def check(self, files: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        파일들을 검사하고 문제 목록을 반환합니다.

        Args:
            files: {파일경로: 파일내용} 딕셔너리

        Returns:
            문제 목록. 각 항목은:
            {
                'category': '카테고리',
                'severity': 'critical' | 'warning',
                'file': '파일 경로',
                'line': 줄 번호,
                'description': '문제 설명 (비개발자용)',
                'before': '수정 전 코드',
                'after': '수정 후 코드',
                'reason': '왜 수정해야 하는지 이유',
            }
        """
        pass

    def _make_issue(
        self,
        file: str,
        line: int,
        description: str,
        before: str = '',
        after: str = '',
        reason: str = '',
        severity: str = 'warning',
        occurrences: list = None,
    ) -> Dict[str, Any]:
        """문제 항목 생성 헬퍼
        occurrences: [{'line': 줄번호, 'code': 코드내용, 'file': 파일(선택)}, ...]
        """
        return {
            'category': self.category,
            'severity': severity,
            'file': file,
            'line': line,
            'description': description,
            'before': before,
            'after': after,
            'reason': reason,
            'occurrences': occurrences or [],
        }
