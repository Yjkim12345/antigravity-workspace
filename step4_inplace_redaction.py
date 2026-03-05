import os
import glob
import json
import traceback
import re

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

def load_rules():
    rules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anonymization_rules.json")
    if not os.path.exists(rules_path):
        return {"deletions": [], "replacements": []}
    with open(rules_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def redact_pdf(input_path, output_path, mapping, rules):
    if not HAS_PYMUPDF:
        print("Warning: PyMuPDF (fitz) not installed. Cannot redact PDF in-place.")
        return False
        
    try:
        doc = fitz.open(input_path)
        
        # Sort keys by length descending
        sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
        
        for page in doc:
            # 1. Apply Deletion Rules (Headers/Footers/Boilerplate)
            page_text = page.get_text("text")
            for pattern in rules.get("deletions", []):
                for match in re.finditer(pattern, page_text):
                    matched_str = match.group(0)
                    # Redact each line of the matched string individually
                    for line in matched_str.split('\n'):
                        clean_line = line.strip()
                        if len(clean_line) > 1:
                            insts = page.search_for(clean_line)
                            for inst in insts:
                                page.add_redact_annot(inst, fill=(0, 0, 0))

            # 2. Apply Mapping Table Redactions
            for original_text in sorted_keys:
                tag = mapping[original_text]
                
                # Search for the original text on the page
                text_instances = page.search_for(original_text)
                
                # Add redaction annotations for each instance
                for inst in text_instances:
                    # add_redact_annot returns an Annot object
                    annot = page.add_redact_annot(inst, text=tag, fill=(0, 0, 0))
                    # Optional: customize font, text color etc. 
                    # Default uses white text on black background if fill=(0,0,0) is provided.
                    # Note: PyMuPDF default redaction text rendering might not support Korean natively
                    # unless a font is specified during redaction application, 
                    # but simple blacking out is universally safe.
                    
            # Apply all redactions on this page
            page.apply_redactions()
            
        doc.save(output_path)
        doc.close()
        return True
    except Exception as e:
        print(f"Failed to redact PDF {input_path}: {e}")
        return False

def apply_step4(target_dir):
    output_dir = os.path.join(target_dir, "step4_inplace_output")
    map_file = os.path.join(target_dir, "final_mapping_table.json")
    
    if not os.path.exists(map_file):
        print(f"Error: Final mapping table '{map_file}' not found.")
        print("Please run Phase 0-2 and Review Dashboard first.")
        return
        
    os.makedirs(output_dir, exist_ok=True)
    
    with open(map_file, 'r', encoding='utf-8') as f:
        final_mapping = json.load(f)
        
    rules = load_rules()
        
    # Get original PDF files from target_dir
    files = []
    for ext in ['*.pdf']:
        files.extend(glob.glob(os.path.join(target_dir, ext)))
        
    print(f"Phase 4: In-place Redaction for {len(files)} original files...")
    
    processed = 0
    for file_path in files:
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        out_path = os.path.join(output_dir, f"{name}_redacted{ext}")
        
        if os.path.exists(out_path):
            print(f"Skipping already processed: {filename}")
            processed += 1
            continue
            
        success = False
        if ext == '.pdf':
            print(f"Redacting PDF: {filename}...")
            success = redact_pdf(file_path, out_path, final_mapping, rules)
            
        if success:
            processed += 1
            
    print(f"\nPhase 4 Complete. Processed {processed}/{len(files)} files.")
    print(f"In-place redacted files saved to: {output_dir}")

if __name__ == '__main__':
    import sys
    target_dir = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\user\변환자료\이경헌"
    apply_step4(target_dir)
