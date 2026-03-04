import fitz
import os
import sys
import google.generativeai as genai
from PIL import Image
import io

# Initialize Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable not found.")
    sys.exit(1)
genai.configure(api_key=api_key)

# Use gemini-1.5-flash which is good at multimodal tasks quickly
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_text_with_gemini(pdf_path, output_txt_path):
    print(f"Opening {pdf_path}...")
    doc = fitz.open(pdf_path)
    full_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        
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
                
                print(f"  -> Sending image {img_index} to Gemini Vision API...")
                prompt = "Please transcribe the Korean text in this screenshot exactly as it appears. It is a KakaoTalk conversation. Do not translate. Just output the text."
                response = model.generate_content([prompt, image])
                
                text = response.text
                page_text.append(text)
                print(f"  -> Gemini extracted text successfully.")
            except Exception as e:
                print(f"  -> Error running Gemini on image {img_index}: {e}")
                
        # Also grab any embedded text just in case
        embedded_text = page.get_text()
        if embedded_text.strip():
            page_text.append(embedded_text)
            
        full_text.append("\n".join(page_text))
        
    doc.close()
    
    with open(output_txt_path, 'w', encoding='utf-8') as f:
        f.write("\n\n--- Page Break ---\n\n".join(full_text))
        
    print(f"\nSaved Gemini extracted text to {output_txt_path}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python gemini_ocr.py <pdf_path> <output_txt_path>")
        sys.exit(1)
    
    pdf_in = sys.argv[1]
    txt_out = sys.argv[2]
    extract_text_with_gemini(pdf_in, txt_out)
