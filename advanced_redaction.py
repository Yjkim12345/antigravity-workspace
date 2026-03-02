import os
import glob
import re
import json
from collections import OrderedDict

# Global Mapping Table
mapping_table = OrderedDict()
counters = {
    "이름": 1,
    "주민번호": 1,
    "전화번호": 1,
    "주소": 1,
    "상세주소": 1,
    "로펌/법인": 1,
    "사건번호": 1,
    "국가/기관/지자체": 1,
    "단체/회사": 1,
    "이메일": 1,
    "대리인": 1,
    "원고": 1,
    "설비업자": 1
}

def get_placeholder(type_val, original_text):
    global mapping_table, counters
    # Check if original_text already has a placeholder
    for placeholder, original in mapping_table.items():
        if original == original_text:
            return placeholder
    
    # Create new placeholder
    cnt = counters[type_val]
    placeholder = f"[{type_val} {cnt}]"
    counters[type_val] += 1
    mapping_table[placeholder] = original_text
    return placeholder

def process_rule_6_boilerplate(text):
    # Rule 6: Boilderplate Removal
    pattern = r'개인정보유출주의\s*제출자:.*?다운로드일시:\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}'
    return re.sub(pattern, '[전자소송 식별메타데이터 삭제]', text)

def apply_redaction(text):
    # Process text for rules 1-9
    redacted = text

    # Exact phrases from user request with and without spaces
    exact_phrases = {
        "원고 소송대리인 변호사 김도훈": "대리인",
        "원고 소송대리인 변호사김도훈": "대리인",
        "원고 주식회사 스파헤움": "원고",
        "원고 주식회사스파헤움": "원고",
        "원고 ㈜스파헤움": "원고",
        "원고 ㈜ 스파헤움": "원고",
        "설비업자 김성용": "설비업자",
        "‘더 뭉티기’ 식당": "단체/회사",
        "‘그 우동집’ 식당": "단체/회사",
        "101더뭉티기": "단체/회사",
        "104우동집": "단체/회사",
        "㈜스파헤움": "단체/회사",
        "스파헤움": "단체/회사",
        "로즈1타워 관리단": "단체/회사",
        "로즈1타워 빌딩": "단체/회사",
        "로즈1타워": "단체/회사",
        "kdhyonsei@nate.com": "이메일",
        "김도훈": "이름",
        "김성용": "이름",
        "조동식": "이름",
        "이민우": "이름",
        "곽혜린": "이름",
        "더뭉티기": "단체/회사",
        "더 뭉티기": "단체/회사",
        "그우동집": "단체/회사",
        "그 우동집": "단체/회사"
    }

    for phrase, category in exact_phrases.items():
        if phrase in redacted:
            ph = get_placeholder(category, phrase)
            redacted = redacted.replace(phrase, ph)
    
    # Rule 6
    redacted = process_rule_6_boilerplate(redacted)
    
    # Rule 2: ID
    pattern_id = r'\b(\d{6}[-\s]*[1-4]\d{6})\b'
    for match in re.finditer(pattern_id, redacted):
        original = match.group(1)
        ph = get_placeholder("주민번호", original)
        redacted = redacted.replace(original, ph)
        
    # Rule 3: Phone / Contact
    pattern_phone = r'\b(010[-\s]?\d{3,4}[-\s]?\d{4}|0[2-9]{1,2}[-\s]?\d{3,4}[-\s]?\d{4})\b'
    for match in re.finditer(pattern_phone, redacted):
        original = match.group(1)
        ph = get_placeholder("전화번호", original)
        redacted = redacted.replace(original, ph)
        
    # Rule 7: Case Numbers
    pattern_case = r'\b(\d{2,4}[가-힣]{1,2}\d{3,6})\b'
    for match in re.finditer(pattern_case, redacted):
        original = match.group(1)
        ph = get_placeholder("사건번호", original)
        redacted = redacted.replace(original, ph)
        
    # Rule 5: Law firms
    pattern_lawfirm = r'\b(법무법인\s*\(유한\)\s*[가-힣]+|법무법인\s*[가-힣]+|정부법무공단)\b'
    for match in re.finditer(pattern_lawfirm, redacted):
        original = match.group(1)
        ph = get_placeholder("로펌/법인", original)
        redacted = redacted.replace(original, ph)
        
    # Rule 9: Corporate / Orgs
    pattern_corp = r'(사단법인\s*[가-힣0-9a-zA-Z]+|재단법인\s*[가-힣0-9a-zA-Z]+|주식회사\s*[가-힣0-9a-zA-Z]+|[가-힣0-9a-zA-Z]+\s*주식회사|로즈1타워\s*관리단|로즈1타워\s*빌딩|로즈1타워|101더뭉티기|104우동집|더뭉티기|더\s*뭉티기|그우동집|그\s*우동집|스파헤움|㈜스파헤움|‘더 뭉티기’ 식당|‘그 우동집’ 식당)'
    for match in re.finditer(pattern_corp, redacted):
        original = match.group(1)
        if "법무법인" in original or "정부법무공단" in original:
            continue
        ph = get_placeholder("단체/회사", original)
        redacted = redacted.replace(original, ph)

    # Rule 8: Gov / Agencies
    pattern_gov = r'\b(대한민국|서울중앙지방법원|국방부장관|국방부|교육부장관|교육부|한강유역환경청|용산구청장|용산구청|용산구|서울특별시|서울시장|서울시|강남구)\b'
    for match in re.finditer(pattern_gov, redacted):
        original = match.group(1)
        ph = get_placeholder("국가/기관/지자체", original)
        redacted = redacted.replace(original, ph)

    # Rule 10: Emails
    pattern_email = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    for match in re.finditer(pattern_email, redacted):
        original = match.group(0)
        ph = get_placeholder("이메일", original)
        redacted = redacted.replace(original, ph)

    # Rule 1: Names (Heuristic Context)
    # look for specific keywords followed by names
    pattern_name = r'(?:원고|피고|소송대리인|신청인|담당변호사|변호사|수사관|고소인|사내이사|관리소장|소외|설비업자)\s*:?\s*([가-힣]{2,4})(?:[\s\W]|$)'
    # Finding uniquely
    found_names = set()
    for match in re.finditer(pattern_name, redacted):
        original = match.group(1)
        # Avoid matching common words or parsed entities
        if len(original) >= 2 and "[" not in original:
            found_names.add(original)
            
    # Also explicitly add known names from filenames if available
    # explicitly adding some names from mapping requests
    specific_names = {"김도훈", "김성용", "조동식", "이민우", "곽혜린"}
    for name in found_names.union(specific_names):
        ph = get_placeholder("이름", name)
        # Use simple replace because \b does not work reliably with Korean unicode
        redacted = redacted.replace(name, ph)

    # Rule 4: Addresses
    # Simple heuristic for this specific case based on the text
    pattern_address = r'(서울(?:\s*특별시)?\s+[가-힣]+구\s+[가-힣0-9]+(?:로|길)\s+[0-9-]+(?:,\s*지하\d+층\s*\d+호|\s*\d+~\d+층)?(?:\([^)]+\))?)'
    for match in re.finditer(pattern_address, redacted):
        original = match.group(1)
        ph = get_placeholder("주소", original)
        redacted = redacted.replace(original, ph)
        
    # Additional specific addresses seen
    addr_extras = [
        "언주로 311", "반포대로26길 70", "테헤란로108길 12", "한강로3가 40-976"
    ]
    for ext in addr_extras:
        if ext in redacted:
            ph = get_placeholder("상세주소", ext)
            redacted = redacted.replace(ext, ph)

    return redacted

def main():
    input_dir = r"C:\Users\user\변환자료\스파헤움 항소심\extracted_text"
    output_dir = r"C:\Users\user\변환자료\스파헤움 항소심\redacted_output"
    os.makedirs(output_dir, exist_ok=True)
    
    txt_files = glob.glob(os.path.join(input_dir, '*.txt'))
    print(f"Redacting {len(txt_files)} files...")
    
    for txt_path in txt_files:
        filename = os.path.basename(txt_path)
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        redacted_text = apply_redaction(text)
        
        # Another pass for names that might have been missed but are in mapping_table
        for placeholder, original in mapping_table.items():
            if "이름" in placeholder and original in redacted_text:
                redacted_text = redacted_text.replace(original, placeholder)
        
        out_path = os.path.join(output_dir, filename.replace('.txt', '_redacted.txt'))
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(redacted_text)
            
    # Save Mapping Table
    map_path = os.path.join(output_dir, "mapping_table.json")
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_table, f, ensure_ascii=False, indent=4)
        
    print(f"Redaction complete. Output saved to {output_dir}")
    print(f"Mapping table saved to {map_path}")

if __name__ == '__main__':
    main()
