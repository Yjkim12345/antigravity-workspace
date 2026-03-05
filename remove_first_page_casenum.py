import fitz
import re
import os

pdf_path = r"C:\Users\user\변환자료\스파헤움 항소심\step4_inplace_output\2024.12.18_판결문.pdf"
temp_out = r"C:\Users\user\변환자료\스파헤움 항소심\step4_inplace_output\2024.12.18_판결문_temp.pdf"

print(f"Opening: {pdf_path}")
try:
    doc = fitz.open(pdf_path)
    page = doc[0] # First page
    
    # Case number pattern (e.g., 2024가단12345, 2023나9876)
    case_pattern = r"\d{2,4}[가-힣]{1,2}\d{3,6}"
    
    page_text = page.get_text("text")
    redacted_count = 0
    for match in re.finditer(case_pattern, page_text):
        target_text = match.group(0)
        print(f"Found case number: {target_text}")
        
        insts = page.search_for(target_text)
        for inst in insts:
            page.add_redact_annot(inst, fill=(0, 0, 0))
            redacted_count += 1
            
    if redacted_count > 0:
        page.apply_redactions()
        doc.save(temp_out)
        doc.close()
        # Replace original
        os.remove(pdf_path)
        os.rename(temp_out, pdf_path)
        print(f"Successfully redacted {redacted_count} instances on page 1.")
    else:
        doc.close()
        print("No case numbers found on page 1.")

except Exception as e:
    print(f"Error processing PDF: {e}")
