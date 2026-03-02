import os
import glob
import fitz  # PyMuPDF

def extract_text_from_pdfs(input_dir, output_dir):
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
            for page in doc:
                full_text.append(page.get_text())
            doc.close()
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(full_text))
        except Exception as e:
            print(f"  -> Error processing {filename}: {e}")

if __name__ == '__main__':
    target_dir = r"C:\Users\user\변환자료\스파헤움 항소심"
    out_dir = os.path.join(target_dir, "extracted_text")
    extract_text_from_pdfs(target_dir, out_dir)
