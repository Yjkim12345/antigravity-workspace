import os
import json
import re

input_dir = r"C:\Users\user\변환자료\스파헤움 항소심\step1_output"
output_dir = r"C:\Users\user\변환자료\스파헤움 항소심\step3_final_output"
os.makedirs(output_dir, exist_ok=True)

step1_map_file = r"C:\Users\user\변환자료\스파헤움 항소심\step1_output\mapping_table_step1.json"
final_map_file = r"C:\Users\user\변환자료\스파헤움 항소심\final_mapping_table.json"

# Targets specified by user that are safe for global string replacement
targets_global = [
    "그 우동집", "그우동집", "더 뭉티기", "더뭉티기",
    "강남구", "곽혜린", "김도훈", "노원구", "서울시", "서흥빌딩",
    "이민우", "조동식", "스파헤움", "제민", "우면"
]

counters = {
    '식당': 1,
    '지역': 1,
    '이름': 1,
    '빌딩': 1,
    '법무법인': 1,
    '주식회사': 1,
}

placeholder_map = {}

def get_placeholder(word):
    if word in placeholder_map:
        return placeholder_map[word]
    
    if word in ["그 우동집", "그우동집"]:
        if "그 우동집" not in placeholder_map:
            p = f"식당{counters['식당']}"
            counters['식당'] += 1
            placeholder_map["그 우동집"] = p
            placeholder_map["그우동집"] = p
        return placeholder_map[word]
        
    if word in ["더 뭉티기", "더뭉티기"]:
        if "더 뭉티기" not in placeholder_map:
            p = f"식당{counters['식당']}"
            counters['식당'] += 1
            placeholder_map["더 뭉티기"] = p
            placeholder_map["더뭉티기"] = p
        return placeholder_map[word]
        
    if "구" in word and len(word) == 3:
        p = f"지역{counters['지역']}구"
        counters['지역'] += 1
    elif "시" in word and len(word) == 3:
        p = f"지역{counters['지역']}시"
        counters['지역'] += 1
    elif "빌딩" in word:
        p = f"빌딩{counters['빌딩']}"
        counters['빌딩'] += 1
    elif word in ["곽혜린", "김도훈", "이민우", "조동식"]:
        p = f"이름{counters['이름']}"
        counters['이름'] += 1
    elif word == "스파헤움":
        p = f"회사{counters['주식회사']}"
        counters['주식회사'] += 1
    elif word in ["제민", "우면", "영"]:
        p = f"로펌{counters['법무법인']}"
        counters['법무법인'] += 1
    else:
        p = f"고유명사{counters['이름']}"
        counters['이름'] += 1
        
    placeholder_map[word] = p
    return p

# Ensure targets are sorted to replace longer matches first
targets_global.sort(key=len, reverse=True)

# Generate placeholders
for t in targets_global:
    get_placeholder(t)

# Manually register "영"
placeholder_map["영"] = get_placeholder("영")

def apply_step3(text):
    for t in targets_global:
        text = text.replace(t, placeholder_map[t])
        
    # Safe replacement for "영" to avoid replacing it inside common words
    text = re.sub(r'(법무법인(?:\s*\(\s*유한\s*\))?\s*)영([\s\.,\n]|$)', r'\1' + placeholder_map["영"] + r'\2', text)
    
    return text

if __name__ == "__main__":
    if not os.path.exists(input_dir):
        print("Input directory not found.")
        exit()
        
    processed_files = 0
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            in_path = os.path.join(input_dir, filename)
            out_path = os.path.join(output_dir, filename)
            
            with open(in_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            redacted = apply_step3(content)
            
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(redacted)
            processed_files += 1
                
    # Merge mappings
    combined_mapping = {}
    if os.path.exists(step1_map_file):
        with open(step1_map_file, 'r', encoding='utf-8') as f:
            combined_mapping = json.load(f)
            
    # Add step3 mappings, overriding any conflicts softly
    for k, v in placeholder_map.items():
        combined_mapping[k] = v
        
    with open(final_map_file, 'w', encoding='utf-8') as f:
        json.dump(combined_mapping, f, ensure_ascii=False, indent=4)
        
    print(f"Step 3 complete. Processed {processed_files} files.")
    print(f"Redacted txts in: {output_dir}")
    print(f"Final combined mapping table in: {final_map_file}")
