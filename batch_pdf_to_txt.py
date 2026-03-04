import os
import sys
import glob
import fitz  # PyMuPDF

def extract_text_from_pdfs(input_dir, output_dir, skip_cover=True, skip_toc=True):
    os.makedirs(output_dir, exist_ok=True)
    pdf_files = glob.glob(os.path.join(input_dir, '*.pdf'))
    
    total_files = len(pdf_files)
    print(f"Found {total_files} PDF files in {input_dir}")
    
    for i, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        txt_filename = os.path.splitext(filename)[0] + '.txt'
        txt_path = os.path.join(output_dir, txt_filename)
        
        print(f"[{i}/{total_files}] Processing: {filename}")
        try:
            doc = fitz.open(pdf_path)
            full_text = []
            for j, page in enumerate(doc):
                text = page.get_text()
                # Skip cover (but not for evidence files starting with '갑')
                if skip_cover and j == 0 and not filename.startswith("갑"):
                    print(f"  - Skipping page {j+1} (Cover assumed)")
                    continue
                # Skip TOC if found in early pages
                if skip_toc and j < 3 and any(word in text[:200].replace(" ", "") for word in ["목차", "차례"]):
                    print(f"  - Skipping page {j+1} (TOC assumed)")
                    continue
                
                full_text.append(text)
            doc.close()
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(full_text))
        except Exception as e:
            print(f"  -> Error processing {filename}: {e}")

if __name__ == '__main__':
    target_dir = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\user\변환자료\이경헌"
    out_dir = os.path.join(target_dir, "extracted_text")
    extract_text_from_pdfs(target_dir, out_dir)
