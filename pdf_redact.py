import os
import re
import argparse

# --- 정규식(Regex) 기반 1차 비식별화 패턴 ---
# 1. 주민등록번호, 외국인등록번호
# 2. 휴대전화 번호, 일반 전화번호
# 3. 계좌번호 및 신용카드 번호 (기본적인 패턴)
REGEX_PATTERNS = [
    (r'\b\d{6}[- ]?[1-4]\d{6}\b', '[주민등록번호]'),
    (r'\b01[016789][- ]?\d{3,4}[- ]?\d{4}\b', '[휴대전화번호]'),
    (r'\b0[2-9]\d{0,1}[- ]?\d{3,4}[- ]?\d{4}\b', '[전화번호]'),
    (r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[신용카드번호]'),
    # 추가적인 계좌번호 패턴 등은 가이드라인에 맞춰 보완 가능
]

def apply_regex_redaction(text: str) -> str:
    """정규표현식을 이용한 빠르고 확실한 1차 비식별화"""
    redacted_text = text
    for pattern, replacement in REGEX_PATTERNS:
        redacted_text = re.sub(pattern, replacement, redacted_text)
    return redacted_text

def apply_llm_redaction(text: str) -> str:
    """
    LLM(또는 외부 API)을 활용한 2차 문맥 기반 가명처리
    현재는 임시 가이드라인(Mock)으로 비워져 있으며, 
    나중에 Gemini나 Claude API를 연동하여 '사람 이름', '법인명', '주소' 등을 문맥에서 찾아 치환합니다.
    """
    # TODO: 추후 LLM API 통신 코드 추가 (예: langchain, openai, gemini api 등)
    # prompt = "다음 텍스트에서 이름, 법인명, 상세 주소를 [원고], [회사A], [주소B] 등으로 가명처리 해줘."
    # redacted_text = call_llm(prompt, text)
    
    # 임시 반환 (단순 바이패스)
    return text

def process_pdf_to_txt(pdf_path: str, output_txt_path: str):
    """PDF에서 텍스트를 추출하고, 가명처리를 거쳐 TXT로 저장합니다."""
    # 1. PDF 텍스트 추출 (PyMuPDF - fitz 라이브러리 사용 권장)
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("ERROR: PyMuPDF 라이브러리가 설치되어 있지 않습니다. 'pip install PyMuPDF'를 실행해주세요.")
        return

    print(f"[1/4] '{pdf_path}'에서 텍스트 추출 중...")
    try:
        doc = fitz.open(pdf_path)
        raw_text = ""
        for page in doc:
            raw_text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"PDF 파싱 중 오류 발생: {e}")
        return

    if not raw_text.strip():
        print("경고: PDF에서 추출된 텍스트가 없습니다. (혹시 이미지형 PDF인가요?)")
        return

    print(f"[2/4] 정규표현식(Regex) 기반 1차 가명처리 중...")
    step1_text = apply_regex_redaction(raw_text)

    print(f"[3/4] LLM 기반 2차 문맥 가명처리 중... (현재 LLM 미연동 상태, 통과)")
    final_text = apply_llm_redaction(step1_text)

    print(f"[4/4] 결과 텍스트를 '{output_txt_path}'에 저장 중...")
    try:
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        print("=> 가명처리 완료 및 TXT 저장 성공!")
    except Exception as e:
        print(f"파일 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="법률 문서 PDF 가명처리 및 TXT 변환 도구")
    parser.add_argument("input_pdf", help="가명처리할 원본 PDF 파일 경로")
    parser.add_argument("output_txt", help="저장할 TXT 파일 경로")
    args = parser.parse_args()

    if not os.path.exists(args.input_pdf):
        print(f"오류: 입력 파일 '{args.input_pdf}'을 찾을 수 없습니다.")
    else:
        process_pdf_to_txt(args.input_pdf, args.output_txt)
