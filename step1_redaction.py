import os
import glob
import re
import json
from collections import OrderedDict

# Global Mapping Table for Step 1
mapping_table = OrderedDict()
counters = {
    "주민번호": 1,
    "전화번호": 1,
    "주소": 1,
    "상세주소": 1,
    "사건번호": 1,
    "이메일": 1,
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
    # Rule 6: Boilderplate Removal (Not saved to mapping as it's just deletion)
    pattern = r'개인정보유출주의\s*제출자:.*?다운로드일시:\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}'
    return re.sub(pattern, '[전자소송 식별메타데이터 삭제]', text)

def apply_format_redaction(text):
    redacted = text
    
    # Rule 6: Boilerplate
    redacted = process_rule_6_boilerplate(redacted)
    
    # 1. 주민등록번호
    pattern_id = r'\b(\d{6}[-\s]*[1-4]\d{6})\b'
    for match in re.finditer(pattern_id, redacted):
        original = match.group(1)
        ph = get_placeholder("주민번호", original)
        redacted = redacted.replace(original, ph)
        
    # 2. 전화번호/휴대폰번호
    pattern_phone = r'\b(010[-\s]?\d{3,4}[-\s]?\d{4}|0[2-9]{1,2}[-\s]?\d{3,4}[-\s]?\d{4})\b'
    for match in re.finditer(pattern_phone, redacted):
        original = match.group(1)
        ph = get_placeholder("전화번호", original)
        redacted = redacted.replace(original, ph)
        
    # 3. 사건번호
    pattern_case = r'\b(\d{2,4}[가-힣]{1,2}\d{3,6})\b'
    for match in re.finditer(pattern_case, redacted):
        original = match.group(1)
        ph = get_placeholder("사건번호", original)
        redacted = redacted.replace(original, ph)
        
    # 4. 이메일
    pattern_email = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    for match in re.finditer(pattern_email, redacted):
        original = match.group(0)
        ph = get_placeholder("이메일", original)
        redacted = redacted.replace(original, ph)

    # 5. 주소
    pattern_address = r'(서울(?:\s*특별시)?\s+[가-힣]+구\s+[가-힣0-9]+(?:로|길)\s+[0-9-]+(?:,\s*지하\d+층\s*\d+호|\s*\d+~\d+층)?(?:\([^)]+\))?)'
    for match in re.finditer(pattern_address, redacted):
        original = match.group(1)
        ph = get_placeholder("주소", original)
        redacted = redacted.replace(original, ph)
        
    # Additional specific addresses seen (optional, but good for completeness of Phase 1)
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
    output_dir = r"C:\Users\user\변환자료\스파헤움 항소심\step1_output"
    os.makedirs(output_dir, exist_ok=True)
    
    txt_files = glob.glob(os.path.join(input_dir, '*.txt'))
    print(f"Phase 1 Redacting {len(txt_files)} files...")
    
    for txt_path in txt_files:
        filename = os.path.basename(txt_path)
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        redacted_text = apply_format_redaction(text)
        
        out_path = os.path.join(output_dir, filename.replace('.txt', '_step1.txt'))
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(redacted_text)
            
    # Save Mapping Table
    map_path = os.path.join(output_dir, "step1_mapping.json")
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_table, f, ensure_ascii=False, indent=4)
        
    print(f"Phase 1 Redaction complete. Output saved to {output_dir}")
    print(f"Mapping table saved to {map_path}")

if __name__ == '__main__':
    main()
