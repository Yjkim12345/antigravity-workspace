import os
import glob
import shutil

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

def extract_from_pdf(pdf_path):
    text = ""
    if HAS_PYMUPDF:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    else:
        text = "PyMuPDF (fitz) not installed. Please install it using 'pip install PyMuPDF'."
        print(f"Warning: {text}")
    return text

def extract_from_docx(docx_path):
    text = ""
    if HAS_DOCX:
        doc = docx.Document(docx_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    else:
        text = "python-docx not installed. Please install it using 'pip install python-docx'."
        print(f"Warning: {text}")
    return text

def main(target_dir):
    output_dir = os.path.join(target_dir, "extracted_text")
    os.makedirs(output_dir, exist_ok=True)
    
    # Get files in the target_dir (not subdirectories)
    files = []
    for ext in ['*.pdf', '*.docx', '*.txt']:
        files.extend(glob.glob(os.path.join(target_dir, ext)))
        
    print(f"Step 0: Found {len(files)} documents to convert in {target_dir}.")
    
    for file_path in files:
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        # Don't process files that happen to be extracted.txt already if any logic is flawed
        if filename.endswith("_step1.txt"):
            continue
            
        out_path = os.path.join(output_dir, f"{name}.txt")
        
        if ext == '.pdf':
            text = extract_from_pdf(file_path)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Converted: {filename}")
        elif ext == '.docx':
            text = extract_from_docx(file_path)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Converted: {filename}")
        elif ext == '.txt':
            # Copy to extracted_text
            shutil.copy2(file_path, out_path)
            print(f"Copied: {filename}")

if __name__ == '__main__':
    import sys
    target_dir = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\user\변환자료\이경헌"
    main(target_dir)
