import os
import sys
import json
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from datetime import datetime

# ==========================================
# 0. CONFIGURATION
# ==========================================

# TODO: Load from mcp_config.json or ENV
with open(r"c:\Users\user\.gemini\antigravity\mcp_config.json", "r") as f:
    config = json.load(f)
    os.environ["GEMINI_API_KEY"] = config["GEMINI_API_KEY"]
    # NOTION_API_KEY is buried in the headers string
    headers_str = config["mcpServers"]["notion-mcp-server"]["env"]["OPENAPI_MCP_HEADERS"]
    headers_dict = json.loads(headers_str)
    NOTION_API_KEY = headers_dict["Authorization"].replace("Bearer ", "")

NOTION_DB_ID = "31b063a28bb180b1a135ebc3f6813a3c"

client = genai.Client()

# ==========================================
# 1. GEMINI SCHEMA DEFINITION
# ==========================================

class KnowledgeCard(BaseModel):
    title: str = Field(description="'~여부', '~요건' 등의 명사형 제목")
    one_line_principle: str = Field(description="단 1~3줄의 초응축된 핵심 법칙 (한줄법리)")
    related_laws: str = Field(description="관련 법령 (예: '민법 제1008조, 상속세법 제4조')")
    keywords: str = Field(description="검색용 핵심 키워드 (예: '#상속회복청구 #가분채권')")
    source: str = Field(description="원문 출처 또는 사건번호 (예: '대법원 2025다212863')")
    card_type: str = Field(description="지식 유형. 다음 중 하나만 선택: '일반법리', '공격논리', '방어논리', '절차팁', '기재례', '소수설'")
    detailed_text: str = Field(description="이 한줄법리를 도출해낸 원본 판결문/문서의 원문 발췌 단락 (상세 내용)")

class AtomizationResult(BaseModel):
    cards: list[KnowledgeCard] = Field(description="입력된 문서에서 추출된 핵심 법리 카드 목록 (문서 길이가 짧다면 반드시 1개, 아주 길고 복합적인 경우에만 최대 2~3개 추출. 과도한 쪼개기 금지.)")


SYSTEM_PROMPT = """당신은 대한민국의 최고참 파트너 변호사이자 제텔카스텐(Zettelkasten) 지식 아키텍트입니다.

[지시사항]
사용자가 판례나 법리를 제공하면, 이를 분석하여 '독립적으로 재활용 가능한 추상화된 법리'로 정리하십시오.

[원자화 3대 원칙 및 💥제한사항💥]
1. (중요) 과도한 쪼개기(Over-atomization)를 엄격히 금지합니다. 비슷한 맥락이나 같은 판례 안에서 도출되는 연관된 법리들은 억지로 분리하지 말고, 가장 핵심이 되는 1개의 카드로 통합하여 굵직하게 뽑아내십시오.
2. 입력된 텍스트가 A4 반 페이지 이하의 짧은 판결요지나 단일 단락이라면, 무조건 '단 1개의 지식 카드'만 생성하십시오.
3. 사안의 구체적 사실관계와 추상화된 법리를 분리하되, '한줄법리'에는 결론을, '상세내용'에는 그 결론을 뒷받침하는 원문 전체를 풍부하게 담으십시오.
"""

def atomize_text(text: str) -> AtomizationResult:
    print(f"[*] Analyzing and atomizing text with Gemini (Length: {len(text)} chars)...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
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
# 2. NOTION API INTEGRATION
# ==========================================
import urllib.request
import urllib.error

def create_notion_page(card: KnowledgeCard):
    url = "https://api.notion.com/v1/pages"
    
    # 텍스트 길이 제한 등 방어 로직 (Notion rich_text limit is 2000 chars)
    one_line = card.one_line_principle[:2000]
    laws = card.related_laws[:2000]
    tags = card.keywords[:2000]
    source = card.source[:2000]
    card_type = card.card_type if card.card_type in ["일반법리", "공격논리", "방어논리", "절차팁", "기재례", "소수설"] else "일반법리"
    
    # Payload
    data = {
        "parent": { "database_id": NOTION_DB_ID },
        "properties": {
            "이름": {
                "title": [
                    { "text": { "content": card.title } }
                ]
            },
            "한줄법리": {
                "rich_text": [
                    { "text": { "content": one_line } }
                ]
            },
            "관련 법령": {
                "rich_text": [
                    { "text": { "content": laws } }
                ]
            },
            "키워드": {
                "rich_text": [
                    { "text": { "content": tags } }
                ]
            },
            "사건번호/출처": {
                "rich_text": [
                    { "text": { "content": source } }
                ]
            },
            "Type": {
                "select": { "name": card_type }
            }
        },
        "children": [
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "📖 상세 내용 (원문 발췌)"}}]
                }
            },
            {
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": card.detailed_text[:2000]}}]
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "🧠 변호사 코멘트 / 실무 적용 메모"}}]
                }
            }
        ]
    }
    
    req = urllib.request.Request(url, method="POST")
    req.add_header("Authorization", f"Bearer {NOTION_API_KEY}")
    req.add_header("Notion-Version", "2022-06-28")
    req.add_header("Content-Type", "application/json")
    
    try:
        response = urllib.request.urlopen(req, data=json.dumps(data).encode("utf-8"))
        res_data = json.loads(response.read())
        print(f"[+] Successfully created Notion page: {card.title}")
        return res_data
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        print(f"[-] Failed to create Notion page. Status: {e.code}, Error: {err_msg}")
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
        print(f"Type: {card.card_type} | Laws: {card.related_laws}")
        
        # 실제 노션 푸시
        create_notion_page(card)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python knowledge_atomizer.py <path_to_document.txt>")
    else:
        main(sys.argv[1])
