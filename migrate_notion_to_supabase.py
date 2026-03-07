import os
import json
import requests
from knowledge_atomizer import get_embedding, insert_to_supabase, KnowledgeCard

# Parse Notion API key from mcp_config.json
home_dir = os.path.expanduser("~")
mcp_config_path = os.path.join(home_dir, '.gemini', 'antigravity', 'mcp_config.json')

notion_token = None
try:
    with open(mcp_config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        auth_string = config.get("mcpServers", {}).get("notion-mcp-server", {}).get("env", {}).get("OPENAPI_MCP_HEADERS", "")
        if auth_string:
            headers = json.loads(auth_string)
            bearer = headers.get("Authorization", "")
            if bearer.startswith("Bearer "):
                notion_token = bearer[7:]
except Exception as e:
    print(f"Error loading Notion Token from mcp_config: {e}")

if not notion_token:
    # Try environment variable fallback
    from dotenv import load_dotenv
    load_dotenv()
    notion_token = os.getenv("NOTION_API_KEY")

if not notion_token:
    raise ValueError("NOTION_API_KEY를 mcp_config.json 또는 .env에서 찾을 수 없습니다.")

# Target Notion Database ID (법리모음)
DATABASE_ID = "31b063a2-8bb1-80b1-a135-ebc3f6813a3c"

def get_rich_text_content(property_data):
    """Rich Text 속성에서 일반 텍스트 추출"""
    if not property_data or 'rich_text' not in property_data:
        return ""
    return "".join([rt.get('plain_text', '') for rt in property_data['rich_text']])

def get_title_content(property_data):
    """Title 속성에서 일반 텍스트 추출"""
    if not property_data or 'title' not in property_data:
        return ""
    return "".join([t.get('plain_text', '') for t in property_data['title']])

def get_select_content(property_data):
    """Select 속성에서 텍스트 추출"""
    if not property_data or 'select' not in property_data or not property_data['select']:
        return ""
    return property_data['select'].get('name', '')

def fetch_notion_db_pages(db_id):
    """노션 DB에서 모든 페이지 페치 (Pagination 지원)"""
    all_results = []
    has_more = True
    next_cursor = None

    print(f"[*] 노션 DB({db_id})에서 데이터를 가져오는 중...")
    
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    while has_more:
        payload = {}
        if next_cursor:
            payload["start_cursor"] = next_cursor
            
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"[-] Notion API Error: {response.text}")
            break
            
        data = response.json()
        all_results.extend(data.get("results", []))
        
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")
        
    print(f"[+] 총 {len(all_results)}개의 페이지를 가져왔습니다.")
    return all_results

def process_and_migrate():
    print("============================================================")
    print("[*] [노션 -> Supabase] 법리모음DB 일괄 마이그레이션 시작")
    print("============================================================")
    
    pages = fetch_notion_db_pages(DATABASE_ID)
    
    success_count = 0
    fail_count = 0
    
    for idx, page in enumerate(pages, 1):
        try:
            props = page.get('properties', {})
            
            # Extract basic properties based on the search result schema
            title = get_title_content(props.get('이름'))
            one_line_rule = get_rich_text_content(props.get('한줄법리'))
            keywords = get_rich_text_content(props.get('키워드'))
            doc_type = get_select_content(props.get('Type'))
            related_laws = get_rich_text_content(props.get('관련법령'))
            source = get_rich_text_content(props.get('사건번호/출처'))
            
            if not title:
                print(f"[-] {idx}/{len(pages)}: 제목이 없는 페이지 스킵 (ID: {page['id']})")
                continue
                
            print(f"[*] {idx}/{len(pages)} 처리 중: '{title}'")
            
            # 노션에서는 본문을 따로 가져오려면 page ID로 block children을 조회해야 함.
            # 하지만 임시로, '한줄법리'와 '제목'을 바탕으로 메인 텍스트 구성
            # (만약 노션 본문(page content)이 매우 길다면 get_block_children API로 긁어오는 로직 추가 필요)
            
            # Combine content for vectorization
            combined_text = f"제목: {title}\n"
            if source: combined_text += f"출처: {source}\n"
            if doc_type: combined_text += f"종류: {doc_type}\n"
            if related_laws: combined_text += f"관련 법령: {related_laws}\n"
            if keywords: combined_text += f"키워드: {keywords}\n"
            if one_line_rule: combined_text += f"\n내용(법리):\n{one_line_rule}\n"
            
            # Create KnowledgeCard object
            card = KnowledgeCard(
                title=title,
                summary=one_line_rule if one_line_rule else title,
                related_laws=related_laws,
                keywords=[k.strip() for k in keywords.split() if k.strip().startswith('#')],
                source=source,
                card_type=doc_type if doc_type else "일반법리",
                detailed_text=combined_text
            )
            
            # Insert into Supabase
            insert_to_supabase(card)
            success_count += 1
            
        except Exception as e:
            print(f"[-] 요약/적재 중 에러 발생 ('{page.get('id', 'unknown')}'): {e}")
            fail_count += 1
            
    print("============================================================")
    print(f"[*] 마이그레이션 완료! (성공: {success_count}건, 실패: {fail_count}건)")
    print("============================================================")

if __name__ == "__main__":
    process_and_migrate()
