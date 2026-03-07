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
  embedding vector(768),            -- 임베딩 벡터 저장 (768 차원)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. 빠른 유사도 검색을 위한 인덱스 생성 (hnsw 인덱스)
create index on public.legal_knowledge using hnsw (embedding vector_cosine_ops);

-- 4. 로컬 스크립트 연결을 위한 RLS 임시 비활성화
alter table public.legal_knowledge disable row level security;
