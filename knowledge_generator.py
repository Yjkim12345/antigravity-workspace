import os
import sys
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 자체 모듈 임포트
from knowledge_retriever import hybrid_search

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

SYSTEM_PROMPT = """당신은 수만 건의 판례와 지식을 암기하고 있는 대한민국 최상위 파트너 변호사입니다.
사용자의 질문이 들어오면, 제가 [검색된 지식 컨텍스트 (Retrieved Knowledge Context)]를 제공해 드립니다.

[📝 답변(RAG) 작성 원칙]
1. [지식 의존성]: 당신이 기존에 학습한 지식보다, 반드시 제가 제공한 [컨텍스트]를 최우선으로 참고하여 답변을 작성하십시오.
2. [Grounding(출처 명시) 강제]: 변호사가 당신의 답변을 신뢰할 수 있도록, 주장에 대한 근거가 되는 문장이 끝날 때마다 괄호 안에 해당 지식의 [출처] 또는 [사건번호]를 반드시 명시하십시오. (예: "...입니다. (출처: 대법원 2025다212863)")
3. [논리적 추론 연계]: 메타데이터에 있는 '쟁점(legal_issues)'이나 '방어 전략(defense_strategy)' 필드를 읽고, 이를 바탕으로 질문자에게 유리한 소송 전략을 적극적으로 제안하십시오.
4. [보수적 답변]: 제공된 컨텍스트에 없는 내용을 지어내지 마십시오(Hallucination 금지). 정보가 부족하면 "현재 DB에 정확히 일치하는 판례가 부족합니다"라고 솔직하게 답변하십시오.
"""

def generate_legal_answer(query: str, filters: dict = None) -> str:
    print(f"\n============================================================")
    print(f"[*] 안티그래비티 법률 상담 AI (Powered by Gemini 3.1 Pro & Supabase)")
    print(f"============================================================")
    print(f"[1] 질문 분석 및 DB 검색 진행 중... (질문: '{query}')")
    
    # 1. 문서 검색 (Retriever) - 하이브리드 서치
    results = hybrid_search(query, match_count=4, match_threshold=0.3, filters=filters)
    
    if not results:
        return "관련된 법률 지식을 데이터베이스에서 찾지 못했습니다. 다른 키워드로 검색하거나 조건을 완화해보세요."
        
    print(f"\n[2] 검색된 {len(results)}건의 문서를 바탕으로 Gemini 3.1 Pro가 초안을 작성 중입니다...")
    
    # 2. 컨텍스트 구성
    context_text = "[검색된 지식 컨텍스트 (Retrieved Knowledge Context)]\n\n"
    for i, res in enumerate(results):
        context_text += f"--- 문서 {i+1} ---\n"
        context_text += f"- 제목: {res.get('title', '제목 없음')}\n"
        context_text += f"- 요약/결론: {res.get('summary', '')}\n"
        context_text += f"- 메타데이터 (유형, 쟁점, 방어전략 등): {res.get('metadata', {})}\n"
        context_text += f"- 본문 발췌: {res.get('content', '')}\n"
        context_text += f"- 출처/사건번호(Citation): {res.get('source', '')}\n\n"

    # 3. 프롬프트 조립
    final_prompt = f"질문: {query}\n\n{context_text}\n\n위 컨텍스트를 바탕으로 변호사가 의뢰인에게 브리핑할 수 있는 수준의 '검토 요약 보고서' 초안을 작성해주세요."
    
    # 4. Gemini 3.1 Pro 호출 (Generator)
    response = client.models.generate_content(
        model='gemini-3.1-pro-preview',
        contents=final_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3, # 보수적이고 정확한 RAG를 위해 낮은 온도 유지
        )
    )
    
    return response.text

if __name__ == "__main__":
    test_query = "상속재산분할 협의 시 채권도 나눌 수 있는지, 그리고 이 때 소멸시효 기산점은 언제가 되는지 관련 판례를 바탕으로 검토해줘."
    if len(sys.argv) > 1:
        test_query = sys.argv[1]
        
    answer = generate_legal_answer(test_query)
    
    print("\n==================== [*] 검토 보고서 초안 ====================")
    print(answer)
    print("==============================================================\n")
