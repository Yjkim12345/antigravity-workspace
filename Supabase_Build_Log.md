# 수파베이스(Supabase) 구축 및 작업 로그 (Legal_DataBase)

이 문서는 "거대 법률 데이터베이스(Legal_DataBase)"를 Supabase에 구축하는 전 과정(Phase 1 ~ Phase 4)의 액션 가이드와 실제 작업된 코드/결과물을 누적 기록하는 공간입니다.

---

## [Phase 1] 기초 공사: 인프라 세팅 및 스키마 설계

**목표:** Supabase 프로젝트를 생성하고, 안전하게 연결을 확보한 뒤 임베딩(Vector) 검색을 위한 기초 데이터베이스 구조를 짭니다.

### 1-1. 프로젝트 생성 및 환경 변수 연동
*   **액션 가이드:** Supabase 웹사이트에서 프로젝트(`Legal_DataBase`)를 생성 후, 연결에 필요한 3대장(Project URL, anon public key, service_role secret key)을 확보합니다.
*   **작업 결과 (완료):**
    *   사용자로부터 URL, Publishable Key, Secret Key를 전달받아 프로젝트 루트의 `.env` 파일에 저장 완료.
    *   파이썬 라이브러리 `supabase` 및 `python-dotenv` 설치 완료.
    *   `test_supabase_connection.py` 스크립트를 통해 Supabase 원격 DB와 안티그래비티 간의 정상 통신 여부 검증 완료.

### 1-2. pgvector 익스텐션 및 메인 테이블 스키마 설계
*   **액션 가이드:** Supabase의 `SQL Editor`에 접속하여 벡터 데이터베이스로서 작동하기 위한 플러그인을 켜고, 판례 원문과 AI 임베딩이 들어갈 테이블을 생성합니다.
*   **작업 결과 (작성 완료, 실행 대기):**
    *   AI 시맨틱 검색을 위한 스키마 `.sql` 파일 구성 완료. 아래는 실제 적용되는 쿼리문입니다.

```sql
-- 1. pgvector 익스텐션 활성화 (벡터 데이터 저장을 위해 필수)
create extension if not exists vector;

-- 2. legal_knowledge 테이블 생성 (노션 스키마 기반 최적화)
create table if not exists public.legal_knowledge (
  id uuid default gen_random_uuid() primary key,
  title text not null,               -- 법리 제목, 사건 번호, 요지 등 (기존 '이름')
  summary text,                      -- 핵심 요약 (기존 '한줄법리')
  content text not null,             -- 원문, 판결문 등 상세 내용
  source text,                       -- 사건번호 / 출처 URL 등
  related_laws text,                 -- 관련 법령 (민법 제00조 등)
  keywords text[],                   -- 검색용 키워드/태그 배열 (예: ['손해배상', '채무불이행'])
  metadata jsonb default '{}'::jsonb, -- 기타 유연한 속성 추가용 (Type 속성 등 포함)
  embedding vector(1536),            -- 임베딩 벡터 저장 (1536 차원)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. 빠른 유사도 검색을 위한 인덱스 생성 (hnsw 인덱스)
create index on public.legal_knowledge using hnsw (embedding vector_cosine_ops);

-- 4. 로컬 스크립트 연결을 위한 RLS 임시 비활성화
alter table public.legal_knowledge disable row level security;
```

---

## [Phase 2] 파이프라인 개조: 데이터 적재 자동화 시스템 구축

**목표:** 지식을 추출하고 가공하는 핵심 스크립트(`knowledge_atomizer.py`)가 Notion 대신 Supabase를 바라보도록 전면 개조하고, 텍스트를 벡터로 변환하는 임베딩 절차를 추가합니다.

*   **작업 결과 (완료):**
    *   **공통 모듈 생성:** 여러 스크립트에서 재사용할 수 있도록 Supabase 연결을 담당하는 `supabase_client.py` 생성 및 `.env` 파일 연동.
    *   **임베딩 로직 추가:** `knowledge_atomizer.py` 내에 Google Gemini API(`text-embedding-004`)를 호출하여 법리 및 요약 텍스트를 768차원 백터(`list[float]`)로 변환하는 `get_embedding` 함수 구현.
    *   **스키마 변경 대응:** 모델 차원을 맞추기 위해 1536차원 벡터 스키마를 **768차원**(`vector(768)`)으로 SQL에서 수정 조치 완료.
    *   **백엔드 교체:** 추출된 지식 카드(`KnowledgeCard`) 데이터를 Notion API 대신 `db.table("legal_knowledge").insert(data)` 형식으로 바로 투입. 메타데이터 가이드라인(`card_type`, `ai_confidence`)도 적용됨.

## [Phase 3] RAG 엔진 장착: 안티그래비티 검색 및 추론 통합
*(향후 작업 진행 후 결과물 및 코드 기록 예정)*

---

## [Phase 4] 실전 투입 및 고급화
*(향후 작업 진행 후 결과물 및 코드 기록 예정)*
