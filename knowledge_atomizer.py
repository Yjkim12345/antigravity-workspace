import os
import sys
import json
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from datetime import datetime

# Import the Supabase client
try:
    from supabase_client import db
except ImportError:
    print("Error: supabase_client.py not found. Make sure you are in the scratch directory.")
    sys.exit(1)

# ==========================================
# 0. CONFIGURATION
# ==========================================

home_dir = os.path.expanduser("~")
config_path1 = os.path.join(home_dir, '.gemini', 'antigravity', 'mcp_settings.json')
config_path2 = os.path.join(home_dir, '.gemini', 'antigravity', 'mcp_config.json')

config_path = config_path1 if os.path.exists(config_path1) else (config_path2 if os.path.exists(config_path2) else None)

if not config_path:
    print(f"Config file not found. Checked: \n{config_path1}\n{config_path2}")
    sys.exit(1)

with open(config_path, "r", encoding="utf-8") as f:
    try:
        config = json.load(f)
    except json.JSONDecodeError:
        config = {}

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_KEY = config.get("geminiApiKey", config.get("GEMINI_API_KEY", GEMINI_API_KEY))

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in config.")
    sys.exit(1)

os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
client = genai.Client()

# ==========================================
# 1. GEMINI SCHEMA DEFINITION
# ==========================================

class KnowledgeCard(BaseModel):
    title: str = Field(description="'~여부', '~요건' 등의 명사형 제목")
    summary: str = Field(description="단 1~3줄의 초응축된 핵심 법칙 (핵심 요약)")
    related_laws: str = Field(description="관련 법령 (예: '민법 제1008조, 상속세법 제4조')")
    keywords: list[str] = Field(description="검색용 핵심 키워드 문자열 리스트 (예: ['상속회복청구', '가분채권'])")
    source: str = Field(description="원문 출처 또는 사건번호 (예: '대법원 2025다212863')")
    card_type: str = Field(description="지식 유형. 다음 중 하나만 선택: '일반법리', '공격논리', '방어논리', '절차팁', '기재례', '소수설'")
    detailed_text: str = Field(description="이 법리를 도출해낸 원본 판결문/문서의 원문 발췌 단락 (상세 내용)")

class AtomizationResult(BaseModel):
    cards: list[KnowledgeCard] = Field(description="입력된 문서에서 추출된 핵심 법리 카드 목록 (문서 길이가 짧다면 반드시 1개, 아주 길고 복합적인 경우에만 2~3개 추출)")

SYSTEM_PROMPT = """당신은 대한민국의 최고참 파트너 변호사이자 Supabase 기반 지식 아키텍트입니다.

[지시사항]
사용자가 판례나 메모를 제공하면, 이를 분석하여 '독립적으로 재활용 가능한 추상화된 법리'로 정리하십시오.

[원자화 3대 원칙 및 💥제한사항💥]
1. (중요) 과도한 쪼개기(Over-atomization)를 엄격히 금지합니다. 비슷한 맥락이나 같은 판례 안에서 도출되는 연관된 법리들은 억지로 분리하지 말고, 가장 핵심이 되는 1개의 카드로 통합하여 굵직하게 뽑아내십시오.
2. 입력된 텍스트가 A4 반 페이지 이하의 짧은 판결요지나 단일 단락이라면, 무조건 '단 1개의 지식 카드'만 생성하십시오.
3. 사안의 구체적 사실관계와 추상화된 법리를 분리하되, 'summary'에는 결론을, 'detailed_text'에는 그 결론을 뒷받침하는 원문 전체를 풍부하게 담으십시오.
"""

def atomize_text(text: str) -> AtomizationResult:
    print(f"[*] Analyzing and atomizing text with Gemini 3.1 Pro (Length: {len(text)} chars)...")
    response = client.models.generate_content(
        model='gemini-3.1-pro-preview',
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=AtomizationResult,
            temperature=0.2,
        ),
    )
    
    return response.parsed

# ==========================================
# 2. SUPABASE INTEGRATION & EMBEDDING
# ==========================================

def get_embedding(text: str) -> list[float]:
    """Gemini API를 사용하여 텍스트를 768차원 벡터로 변환합니다."""
    print("[*] Generating 768-dim vector embedding...")
    response = client.models.embed_content(
        model='gemini-embedding-001',
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    # response.embeddings[0].values returns a list of floats
    return response.embeddings[0].values

def insert_to_supabase(card: KnowledgeCard):
    if db is None:
        print("[-] Supabase client not initialized. Check .env file.")
        return None
        
    # 텍스트 벡터화 (검색 시 의미 비교용으로 요약과 본문을 합쳐서 임베딩)
    text_for_embedding = f"[{card.title}]\n{card.summary}\n\n{card.detailed_text}"
    
    try:
        embedding_vector = get_embedding(text_for_embedding)
    except Exception as e:
        print(f"[-] Failed to generate embedding: {e}")
        return None

    # JSONB 메타데이터 (가이드라인 적용)
    metadata = {
        "card_type": card.card_type,
        "ai_confidence": 0.95,
        "author": "안셀로트(Auto)"
    }
    
    # Supabase Insert Payload
    data = {
        "title": card.title,
        "summary": card.summary,
        "content": card.detailed_text,
        "source": card.source,
        "related_laws": card.related_laws,
        "keywords": card.keywords, # PostgreSQL TEXT[] 배열로 자동 매핑됨
        "metadata": metadata,
        "embedding": embedding_vector
    }
    
    try:
        response = db.table("legal_knowledge").insert(data).execute()
        print(f"[+] Successfully inserted to Supabase: {card.title}")
        return response
    except Exception as e:
        print(f"[-] Failed to insert to Supabase. Error: {e}")
        return None

# ==========================================
# 3. MAIN EXECUTION
# ==========================================
def main(file_path: str):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    result = atomize_text(text)
    
    print(f"\n[*] Extracted {len(result.cards)} knowledge cards.")
    
    for i, card in enumerate(result.cards):
        print(f"\n--- Card {i+1}: {card.title} ---")
        print(f"Tags: {card.keywords} | Laws: {card.related_laws}")
        
        # Supabase 적재
        insert_to_supabase(card)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python knowledge_atomizer.py <path_to_document.txt>")
    else:
        main(sys.argv[1])

