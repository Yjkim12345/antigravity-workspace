import os
import glob
import json
import re
import sys
import google.generativeai as genai

def setup_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        try:
            with open(r'c:\Users\user\.gemini\antigravity\mcp_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get("GEMINI_API_KEY")
        except Exception:
            pass
            
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment or mcp_config.json.")
        print("Please set it before running this script.")
        sys.exit(1)
        
    genai.configure(api_key=api_key)
    # Using gemini-2.5-flash as the latest available model
    return genai.GenerativeModel('gemini-2.5-flash')

def extract_candidates_with_llm(model, text):
    prompt = """
    당신은 법률 문서의 가명처리를 돕는 전문가입니다.
    아래 텍스트는 1차 가명처리(정규식을 통해 주민번호, 전화번호 등이 [기호]로 변경된 상태)가 완료된 법률 문서입니다.
    이 문서를 읽고, 문맥을 파악하여 **아직 가명처리가 되지 않은 고유명사(추가 가명처리가 필요한 단어)**만 찾아내어 JSON 배열(List) 형태로 반환해주세요.

    [추출 대상 및 규칙]
    1. **인명**: 원고, 피고, 대리인, 관련자 등의 순수 이름만 추출 (예: "홍길동")
       - 직함이나 조사("변호사", "원고", "은", "는", "이", "가")는 제외하고 순수 이름표현만 뽑을 것.
    2. **법인/단체명**: 문맥상 등장하는 주식회사, 재단, 병원, 식당, 상가 건물명 등 특정 단체나 사업체 이름 (예: "스파헤움", "더 뭉티기", "로즈1타워")
       - "주식회사", "(주)", "사단법인" 같은 일반적인 접두/접미어는 빼고 고유명칭만 추출할 것.
       - "법무법인" 자체는 일반명사이므로 빼되 뒤에 붙은 고유명칭(예: "태평양")만 추출할 것.
    3. **지역/장소명**: 사건과 관련된 특정 동, 구, 건물명 등의 고유 지명 (시도 단위 말고 세부 지명)
    4. **제외 대상**: 
       - 기호 처리된 단어들 (예: [주소 1], [전화번호 1], [기호] 등 대괄호로 묶인 것은 절대 추출 금지)
       - 일상적인 일반명사 ("제출물", "식당", "법원", "계약서" 등)
       - 조사가 붙어있는 단어 (조사를 떼고 원형만 추출할 것)
       - **법령, 법안, 규칙 명칭** (예: "소득세법", "상속세 및 증여세법", "기획재정부령", "민법" 등은 절대 추출 금지)

    # 출력 형식:
    반드시 순수 JSON 배열만 출력하세요. 마크다운 기호(```json)나 부연 설명은 절대 금지합니다.
    예시: ["홍길동", "스파헤움", "더 뭉티기", "강남구", "로즈1타워"]
    """
    
    try:
        response = model.generate_content(prompt + "\n\n[문서 내용 시작]\n" + text + "\n[문서 내용 끝]")
        llm_output = response.text.strip()
        
        # Clean up markdown styling if the LLM hallucinated it despite instructions
        if llm_output.startswith("```json"):
            llm_output = llm_output[7:]
        if llm_output.startswith("```"):
            llm_output = llm_output[3:]
        if llm_output.endswith("```"):
            llm_output = llm_output[:-3]
        llm_output = llm_output.strip()
            
        return json.loads(llm_output)
    except json.JSONDecodeError as e:
        print(f"  -> JSON Parsing Error from LLM response: {e}")
        print(f"  -> Raw response: {response.text}")
        return []
    except Exception as e:
        print(f"  -> Gemini API Error: {e}")
        return []

def main(target_dir):
    input_dir = os.path.join(target_dir, "step1_output")
    output_path = os.path.join(target_dir, "candidates.json")
    
    txt_files = glob.glob(os.path.join(input_dir, '*.txt'))
    if not txt_files:
        print(f"No text files found in {input_dir}")
        return
        
    print(f"Extracting candidates from {len(txt_files)} files using LLM API...")
    
    model = setup_gemini()
    all_candidates = set()
    
    for txt_path in txt_files:
        print(f"Processing: {os.path.basename(txt_path)}")
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        # Due to context limits, we might need to chunk large files in production.
        # For typical legal docs (10-20 pages), gemini-1.5-pro can handle it easily.
        file_candidates = extract_candidates_with_llm(model, text)
        all_candidates.update(file_candidates)
        
    # Final cleanup to remove any accidental brackets or extremely short terms
    filtered_candidates = sorted([
        c.strip() for c in all_candidates 
        if c and type(c) == str and "[" not in c and "]" not in c and len(c.strip()) > 1
    ])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_candidates, f, ensure_ascii=False, indent=4)
        
    print(f"Extracted {len(filtered_candidates)} unique candidates.")
    print(f"Candidates saved to {output_path}")

if __name__ == '__main__':
    target_dir = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\user\변환자료\이경헌"
    main(target_dir)
