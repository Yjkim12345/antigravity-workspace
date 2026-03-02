import os
import glob
import re
import json

def extract_candidates(text):
    candidates = set()
    
    # 1. 고유명사 뒤에 붙은 불필요한 조사 제거를 위한 유틸리티 함수
    def clean_candidate(word):
        word = word.strip()
        # 자주 붙는 조사/어미 제거
        suffixes = ['은', '는', '이', '가', '을', '를', '과', '와', '의', '에', '에게', '에서', '로', '으로', '부터', '께서', '조차', '마저', '까지', '로서', '로써', '며', '만']
        for suffix in sorted(suffixes, key=len, reverse=True):
            if word.endswith(suffix) and len(word) > len(suffix):
                word = word[:-len(suffix)]
                break
        return word.strip()

    # Heuristics based on keyword proximity for names
    pattern_name = r'(?:원고|피고|소송대리인|신청인|담당변호사|변호사|수사관|고소인|사내이사|관리소장|소외|설비업자)\s*:?\s*([가-힣]{2,4})(?:[\s\W]|$)'
    for match in re.finditer(pattern_name, text):
        name = match.group(1)
        if len(name) >= 2 and "[" not in name:
            candidates.add(clean_candidate(name))
            
    # Entities ending in specific suffixes that likely denote organizations/companies
    pattern_corp = r'(사단법인\s*[가-힣A-Za-z]+|재단법인\s*[가-힣A-Za-z]+|주식회사\s*[가-힣A-Za-z]+|[가-힣A-Za-z]+\s*주식회사|[가-힣A-Za-z0-9]+\s*관리단|[가-힣A-Za-z0-9]+\s*빌딩|‘[^’]+’\s*식당)'
    for match in re.finditer(pattern_corp, text):
        corp = match.group(1)
        # filter out generic prefixes like '가진 관리단', '각 관리단', '한 관리단'
        if not any(corp.startswith(x) for x in ['가진 ', '각 ', '감사가 ', '감사는 ', '감사를 ', '거처 ', '검토하고 ', '것을 ', '결과 ', '결의로 ', '결의와 ', '경우 ', '경우로서 ', '고 ', '고용하는 ', '공유자는 ', '관련하여 ', '관리는 ', '관리단은 ', '관리위원회는 ', '관리인은 ', '관리인이 ', '구분소유자가 ', '구분소유자는 ', '구분소유자등은 ', '규약과 ', '규정이나 ', '그러나 ', '날을 ', '대리인 ', '대표권은 ', '등 ', '따라 ', '따른 ', '또는 ', '라 ', '로즈1', '및 ', '밖에 ', '받아 ', '밝혀 ', '별첨도는 ', '보고로서 ', '분을 ', '불구하고 ', '상가 ', '설립된 ', '소재지를 ', '소집하려면 ', '않아 ', '여 ', '연장자가 ', '외에는 ', '우 ', '우체국에 ', '위원장이 ', '위하여 ', '유자가 ', '의사록은 ', '의장은 ', '이상이 ', '이외에 ', '일부관리단은 ', '임시 ', '작성하여 ', '장 ', '장소에 ', '전자투표는 ', '점유자에게 ', '정기 ', '정하여 ', '제정하려는 ', '주의로 ', '직계존비속은 ', '집합건물이며 ', '출석하여 ', '폐지는 ', '피고 ', '하여 ', '하여금 ', '한 ', '합의하면 ', '항의 ', '행사는 ', '회계장부와 ', '후 ']):
            candidates.add(clean_candidate(corp))
        
    # Entities that look like government or agency names based on suffix
    pattern_gov = r'\b([가-힣]+법원|[가-힣]+부장관|[가-힣]+부|[가-힣]+환경청|[가-힣]+구청장|[가-힣]+구청|[가-힣]+광역시|[가-힣]+특별시|[가-힣]+시장|[가-힣]{2,4}시|[가-힣]{2,4}구|[가-힣]{2,4}동)\b'
    for match in re.finditer(pattern_gov, text):
        gov = match.group(1)
        # Exclude common single syllables matching the regex accidentally if any
        if len(gov) > 2:
            candidates.add(clean_candidate(gov))

    # Law firms
    pattern_lawfirm = r'\b(법무법인\s*\(유한\)\s*[가-힣]+|법무법인\s*[가-힣]+|정부법무공단)\b'
    for match in re.finditer(pattern_lawfirm, text):
        lawfirm = match.group(1)
        candidates.add(clean_candidate(lawfirm))
    
    return list(candidates)

def main():
    input_dir = r"C:\Users\user\변환자료\스파헤움 항소심\step1_output"
    output_path = r"C:\Users\user\변환자료\스파헤움 항소심\candidates.json"
    
    txt_files = glob.glob(os.path.join(input_dir, '*.txt'))
    print(f"Extracting candidates from {len(txt_files)} files...")
    
    all_candidates = set()
    
    for txt_path in txt_files:
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        file_candidates = extract_candidates(text)
        all_candidates.update(file_candidates)
        
    # Filters to remove overly generic words that were accidentally picked up or already anonymized placeholders
    filtered_candidates = sorted([
        c for c in all_candidates 
        if c and "[" not in c and "]" not in c and len(c) > 1 and "주식회사" != c and "법무법인" != c
    ])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_candidates, f, ensure_ascii=False, indent=4)
        
    print(f"Extracted {len(filtered_candidates)} unique candidates.")
    print(f"Candidates saved to {output_path}")

if __name__ == '__main__':
    main()
