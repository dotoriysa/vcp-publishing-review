# 오토에버 피드백 기반 검수 기준 정리

> 원본 파일: `검수 기준 파일/FW VCP 퍼블리싱 코드 전달 시 요청 사항의 건.htm`
> 발신: Geun O Park (현대오토에버, geunopak@hyundai-autoever.com)
> 수신: INNOCEAN (sh.lee@innocean.com)
> 날짜: 2026년 4월 28일

---

## 1. 폰트 관련 정리

타이포그래피 관련 속성(fontSize, fontWeight, lineHeight 등)을 삽입 시:
- 내부에 **10개 이상**의 리스트가 있는 경우
- **5개 이상**의 컴포넌트에서 중복 타입 속성이 사용되는 경우

→ 컴포넌트화, 모듈 경로 변경 등 수정이 필요합니다.

추가로:
- 중복된 스타일 속성이 반복되는 경우, 같은 UI가 여러 곳에서 정의되는지 확인

---

## 2. 색상 관련

`#111111`, `#E9EAEC`, `#8333E6` 관련 색상 코드 기준:
- 전체 코드에서 **50개 이상** 사용된 경우

→ HMG Design System CSS 변수를 사용하도록 교체가 필요합니다.

---

## 3. !important

- `!important` 사용 횟수 집계
- 과도한 사용 시 리팩토링 필요

---

## 4. 스크롤바 스타일링 (코드 예시)

### Before
```scss
// webkit 전용만 있는 경우
'&::-webkit-scrollbar': { width: '8px' },
'&::-webkit-scrollbar-track': { background: 'transparent' },
'&::-webkit-scrollbar-thumb': { background: 'transparent', borderRadius: '4px' },
'&:hover::-webkit-scrollbar-thumb': { background: 'rgba(0, 0, 0, 0.2)' },
scrollbarWidth: 'thin',
```

### After
```tsx
import { scrollbarSx } from '@/shared/theme';

<Box sx={{ overflowY: 'auto', ...scrollbarSx }}>...</Box>
```

---

## 5. 그라디언트/색상 하드코딩

### Before
```tsx
// src/pages/ProjectDetail.tsx L789
// src/components/ContentSettingsDialog.tsx L111
background: 'linear-gradient(180deg, #8333E6 40%, rgba(131, 51, 230, 0.85) 100%)'
```

### After
```tsx
import { gradients } from '@/shared/theme';

<Box sx={{ background: gradients.purpleVertical }}>...</Box>
```

---

*이 문서는 추가 피드백이 올 때마다 업데이트됩니다.*
