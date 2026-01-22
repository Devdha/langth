# V2 Enhancement Design - 세션 관리 및 UI 고도화

> **For Claude:** Use this design to implement the V2 enhancement features.

**Goal:** V2를 실제 언어치료사가 사용할 수 있는 프로덕션급 서비스로 고도화

**Architecture:** IndexedDB 기반 세션 관리 + 모던 UI 디자인 시스템

**Tech Stack:** Next.js 15, TypeScript, Tailwind CSS v4, Framer Motion, idb (IndexedDB wrapper)

---

## 1. 데이터 구조

### TherapySession
```typescript
interface TherapySession {
  id: string;                    // UUID
  name: string;                  // "홍길동 - ㄹ 연습"
  createdAt: number;             // timestamp
  updatedAt: number;             // timestamp
  settings: GameSettingsV2;      // 생성 설정
  items: TherapyItemV2[];        // 생성된 문장들
  metadata: {
    patientName?: string;        // 환자/아동 이름
    notes?: string;              // 메모
    color?: string;              // 세션 색상 태그
  };
}
```

## 2. 파일 구조

```
lib/
└── db/
    └── sessions.ts              # IndexedDB CRUD

components/v2/
├── SessionSidebar.tsx           # 세션 목록 사이드바
├── SessionCard.tsx              # 세션 카드 (목록용)
├── NewSessionModal.tsx          # 새 세션 모달
├── SessionHeader.tsx            # 현재 세션 헤더
├── EmptyState.tsx               # 빈 상태 화면
└── (기존 컴포넌트들)

types/
└── v2.ts                        # TherapySession 타입 추가
```

## 3. 핵심 기능

### 3.1 세션 CRUD (lib/db/sessions.ts)
- `createSession(name, settings)` - 새 세션 생성
- `getSession(id)` - 세션 불러오기
- `getAllSessions()` - 모든 세션 목록
- `updateSession(id, data)` - 세션 업데이트
- `deleteSession(id)` - 세션 삭제
- `duplicateSession(id)` - 세션 복제

### 3.2 세션 사이드바 (SessionSidebar.tsx)
- 세션 목록 표시 (최근 순)
- 세션 검색
- 새 세션 버튼
- 접기/펼치기

### 3.3 세션 헤더 (SessionHeader.tsx)
- 세션명 표시/수정
- 저장 상태 (저장됨/수정됨)
- 퀵 액션: 저장, 복제, 삭제

## 4. UI 개선

### 4.1 색상 팔레트
- Primary: Purple (#8B5CF6)
- Secondary: Pink (#EC4899)
- Accent: Indigo (#6366F1)
- Success: Emerald (#10B981)
- Warning: Amber (#F59E0B)

### 4.2 다크모드
- CSS 변수 기반
- 시스템 설정 따르기
- 수동 토글 옵션

### 4.3 애니메이션
- 페이지 전환: slide + fade
- 카드 등장: stagger animation
- 버튼 hover: scale + glow
