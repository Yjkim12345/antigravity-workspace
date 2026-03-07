import os
import sys
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import Supabase client
try:
    from supabase_client import db
except ImportError:
    print("Error: supabase_client.py not found. Make sure you are in the scratch directory.")
    sys.exit(1)

# Config and ENV loading
load_dotenv()

home_dir = os.path.expanduser("~")
config_path1 = os.path.join(home_dir, '.gemini', 'antigravity', 'mcp_settings.json')
config_path2 = os.path.join(home_dir, '.gemini', 'antigravity', 'mcp_config.json')

config_path = config_path1 if os.path.exists(config_path1) else (config_path2 if os.path.exists(config_path2) else None)

if config_path:
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config = json.load(f)
            GEMINI_API_KEY = config.get("geminiApiKey", config.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", "")))
            if GEMINI_API_KEY:
                os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
        except json.JSONDecodeError:
            pass

client = genai.Client()

def get_query_embedding(query_text: str) -> list[float]:
    """Gemini API를 사용하여 검색어(Query)를 768차원 벡터로 변환합니다."""
    print(f"[*] 임베딩 생성 중: '{query_text}'")
    response = client.models.embed_content(
        model='gemini-embedding-001',
        contents=query_text,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    return response.embeddings[0].values

def hybrid_search(query: str, match_count: int = 5, match_threshold: float = 0.0, filters: dict = None) -> list[dict]:
    """
    Supabase의 match_legal_knowledge (RPC) 함수를 호출하여
    하이브리드 검색(Vector + Metadata)을 수행합니다.
    
    :param query: 사용자 질문 또는 검색어
    :param match_count: 가져올 최대 문서 수 (K)
    :param match_threshold: 최소 유사도 점수 (0~1, 높을수록 엄격)
    :param filters: 딕셔너리 형태의 메타데이터 필터 (예: {'filter_case_type': '민사'})
    :return: 검색된 문서들 (dict 리스트)
    """
    if db is None:
        print("[-] Supabase client not initialized. Check .env file.")
        return []

    try:
        query_embedding = get_query_embedding(query)
    except Exception as e:
        print(f"[-] 임베딩 생성 실패: {e}")
        return []

    # RPC 함수 호출 파라미터 구성
    rpc_params = {
        "query_embedding": query_embedding,
        "match_count": match_count,
        "match_threshold": match_threshold
    }
    
    if filters:
        rpc_params.update(filters)
        
    print(f"[*] Supabase 하이브리드 검색 요청 중... (Threshold: {match_threshold}, Filters: {filters})")
    try:
        response = db.rpc('match_legal_knowledge', rpc_params).execute()
        results = response.data
        print(f"[+] 검색 완료: 총 {len(results)}건의 관련 지식을 찾았습니다.\n")
        return results
    except Exception as e:
        print(f"\n[-] Supabase 검색 실패! 오류: {e}")
        error_msg = str(e)
        if "Could not find the function" in error_msg or "function match_legal_knowledge" in error_msg:
             print("\n[!] 주의: Supabase에 'match_legal_knowledge' 함수가 없습니다.")
             print("hybrid_search_rpc.sql 파일의 SQL 구문을 Supabase SQL Editor에서 실행해주어야 합니다.")
        return []

if __name__ == "__main__":
    test_query = "손해배상청구 소멸시효 기산점"
    if len(sys.argv) > 1:
        test_query = sys.argv[1]
        
    # 예시: 특정 메타데이터만 필터링하고 싶을 때 주석 해제하여 사용
    # test_filters = {"filter_case_type": "민사"}
    test_filters = {}
    
    # 임계값(Threshold)을 0.0으로 주면 유사도가 낮아도 일단 다 가져옵니다.
    # 실전에서는 0.6 등으로 높여서 정확한 결과만 가져오도록 튜닝합니다.
    print(f"============================================================")
    print(f"[*] 법률 지식 DB 하이브리드 검색 테스트 (RAG Phase 3)")
    print(f"============================================================")
    
    search_results = hybrid_search(test_query, match_count=3, match_threshold=0.0, filters=test_filters)
    
    if not search_results:
        print("결과가 없습니다.")
    else:
        for i, res in enumerate(search_results):
            similarity = res.get('similarity', 0)
            percentage = similarity * 100
            print(f"[{i+1}] 매칭률: {percentage:.2f}% (제목: {res.get('title')})")
            print(f"    - 요약: {res.get('summary')}")
            print(f"    - 메타데이터: {res.get('metadata')}")
            print(f"    - 출처/사건번호: {res.get('source')}")
            print("-" * 60)
