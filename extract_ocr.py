import fitz
import pytesseract
from PIL import Image
import io
import os
import sys

# Set tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image_pdf(pdf_path, output_txt_path):
    doc = fitz.open(pdf_path)
    full_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Get image list on the page
        image_list = page.get_images(full=True)
        print(f"Page {page_num + 1}: Found {len(image_list)} images.")
        
        page_text = []
        for img_index, img in enumerate(image_list, start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            try:
                # Convert bytes to PIL Image
                image = Image.open(io.BytesIO(image_bytes))
                
                # Pre-processing to improve Tesseract accuracy on screenshots
                # 1. Convert to grayscale
                image = image.convert('L')
                
                # 2. Resize (upscale) by 3x since Tesseract needs text to be larger (e.g. 30px height)
                width, height = image.size
                image = image.resize((width * 3, height * 3), Image.LANCZOS)
                
                # Run OCR with Korean language 
                # (Assuming kor lang is installed. Tesseract windows installer usually installs eng. If kor is missing, it will fail or we can specify 'kor+eng')
                text = pytesseract.image_to_string(image, config='--psm 6', lang='kor')
                page_text.append(text)
                print(f"  -> OCR extracted {len(text)} chars from image {img_index}.")
            except Exception as e:
                print(f"  -> Error running OCR on image {img_index}: {e}")
                
        # Also grab any embedded text just in case
        embedded_text = page.get_text()
        if embedded_text.strip():
            page_text.append(embedded_text)
            
        full_text.append("\n".join(page_text))
        
    doc.close()
    
    with open(output_txt_path, 'w', encoding='utf-8') as f:
        f.write("\n\n--- Page Break ---\n\n".join(full_text))
        
    print(f"\nSaved extracted text to {output_txt_path}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python extract_ocr.py <pdf_path> <output_txt_path>")
        sys.exit(1)
    
    pdf_in = sys.argv[1]
    txt_out = sys.argv[2]
    extract_text_from_image_pdf(pdf_in, txt_out)
