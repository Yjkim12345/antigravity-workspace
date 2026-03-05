import os
import glob
import json
import traceback

try:
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

def create_pdf(text, output_path):
    if not HAS_REPORTLAB:
        print("Warning: reportlab not installed. Cannot generate PDF.")
        return
        
    font_path = r"C:\Windows\Fonts\malgun.ttf"
    if not os.path.exists(font_path):
        print(f"Warning: Korean font {font_path} not found. Generated PDF might have broken characters.")
        font_name = "Helvetica"
    else:
        try:
            pdfmetrics.registerFont(TTFont('Malgun', font_path))
            font_name = 'Malgun'
        except Exception as e:
            print(f"Failed to register font: {e}")
            font_name = "Helvetica"

    c = canvas.Canvas(output_path, pagesize=A4)
    c.setFont(font_name, 10)
    
    width, height = A4
    margin = 20 * mm
    line_height = 14
    
    text_object = c.beginText()
    text_object.setTextOrigin(margin, height - margin)
    text_object.setFont(font_name, 10)
    
    lines = text.split('\n')
    
    for line in lines:
        text_object.textLine(line)
        if text_object.getY() < margin:
            c.drawText(text_object)
            c.showPage()
            text_object = c.beginText()
            text_object.setTextOrigin(margin, height - margin)
            text_object.setFont(font_name, 10)
            
    c.drawText(text_object)
    c.save()

def apply_step3(target_dir):
    step1_dir = os.path.join(target_dir, "step1_output")
    output_dir = os.path.join(target_dir, "step3_final_output")
    map_file = os.path.join(target_dir, "final_mapping_table.json")
    
    if not os.path.exists(step1_dir):
        print(f"Error: Step 1 output directory '{step1_dir}' not found.")
        sys.exit(1)
        
    if not os.path.exists(map_file):
        print(f"Error: Final mapping table '{map_file}' not found.")
        print("Please review the candidates using the Review Dashboard first to generate the final mapping.")
        sys.exit(1)
        
    os.makedirs(output_dir, exist_ok=True)
    
    with open(map_file, 'r', encoding='utf-8') as f:
        final_mapping = json.load(f)
        
    # Sort mapping by key length (longest first)
    sorted_keys = sorted(final_mapping.keys(), key=len, reverse=True)
        
    txt_files = glob.glob(os.path.join(step1_dir, '*_step1.txt'))
    print(f"Phase 3: Finalizing Redaction for {len(txt_files)} files...")
    
    processed_files = 0
    for txt_path in txt_files:
        filename = os.path.basename(txt_path)
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        redacted_text = text
        for original_word in sorted_keys:
            tag = final_mapping[original_word]
            redacted_text = redacted_text.replace(original_word, tag)
            
        base_name = filename.replace('_step1', '')
        
        # Save TXT
        out_txt_path = os.path.join(output_dir, base_name)
        with open(out_txt_path, 'w', encoding='utf-8') as f:
            f.write(redacted_text)
            
        # Save PDF
        out_pdf_path = os.path.join(output_dir, base_name.replace('.txt', '.pdf'))
        try:
            create_pdf(redacted_text, out_pdf_path)
        except Exception as e:
            print(f"Failed to generate PDF for {base_name}: {e}")
            traceback.print_exc()
            
        processed_files += 1
            
    # Also save a copy of the mapping tables to the output dir for safekeeping
    import shutil
    shutil.copy2(map_file, os.path.join(output_dir, "final_mapping_backup.json"))
            
    print(f"Step 3 complete. Processed {processed_files} files.")
    print(f"Final anonymized TXTs and PDFs saved to: {output_dir}")

if __name__ == "__main__":
    import sys
    target_dir = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\user\변환자료\이경헌"
    apply_step3(target_dir)
