-- hybrid_search_rpc.sql
-- 하이브리드 검색(벡터 기반 시맨틱 검색 + 메타데이터 하드 필터링)을 위한 Supabase Function (RPC)

CREATE OR REPLACE FUNCTION match_legal_knowledge(
  query_embedding vector(768),
  match_threshold float DEFAULT 0.0,
  match_count int DEFAULT 5,
  filter_doc_type text DEFAULT NULL,
  filter_case_type text DEFAULT NULL,
  filter_result text DEFAULT NULL,
  filter_author text DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  title text,
  summary text,
  content text,
  source text,
  keywords text[],
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    lk.id,
    lk.title,
    lk.summary,
    lk.content,
    lk.source,
    lk.keywords,
    lk.metadata,
    1 - (lk.embedding <=> query_embedding) AS similarity
  FROM legal_knowledge lk
  WHERE 1 - (lk.embedding <=> query_embedding) > match_threshold
    AND (filter_doc_type IS NULL OR lk.metadata->>'doc_type' = filter_doc_type)
    AND (filter_case_type IS NULL OR lk.metadata->>'case_type' = filter_case_type)
    AND (filter_result IS NULL OR lk.metadata->>'result' = filter_result)
    AND (filter_author IS NULL OR lk.metadata->>'author' = filter_author)
  ORDER BY lk.embedding <=> query_embedding DESC
  LIMIT match_count;
END;
$$;
