import os
import sys
import json
import re

def apply_step3(target_dir):
    input_dir = os.path.join(target_dir, "step1_output")
    output_dir = os.path.join(target_dir, "step3_final_output")
    os.makedirs(output_dir, exist_ok=True)
    
    step1_map_file = os.path.join(input_dir, "step1_mapping.json")
    final_map_file = os.path.join(target_dir, "final_mapping_table.json")
    targets_file = os.path.join(target_dir, "final_targets_mapping.json")
    
    if not os.path.exists(targets_file):
        print(f"Error: Target mapping file not found: {targets_file}")
        sys.exit(1)
        
    with open(targets_file, 'r', encoding='utf-8') as f:
        raw_map = json.load(f)
        
    target_to_placeholder = {}
    normalized_mapping = {}  # placeholder -> orig_text
    
    for k, v in raw_map.items():
        if k.startswith('[') and k.endswith(']'):
            placeholder = k
            orig_text = v
        else:
            placeholder = v
            orig_text = k
            
        target_to_placeholder[orig_text] = placeholder
        normalized_mapping[placeholder] = orig_text
        
    targets_global = sorted(list(target_to_placeholder.keys()), key=len, reverse=True)
    
    def process_text(text):
        for t in targets_global:
            text = text.replace(t, target_to_placeholder[t])
        return text

    if not os.path.exists(input_dir):
        print(f"Input directory not found: {input_dir}")
        sys.exit(1)
        
    processed_files = 0
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            in_path = os.path.join(input_dir, filename)
            out_path = os.path.join(output_dir, filename)
            
            with open(in_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            redacted = process_text(content)
            
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(redacted)
            processed_files += 1
                
    # Merge mappings
    combined_mapping = {}
    if os.path.exists(step1_map_file):
        with open(step1_map_file, 'r', encoding='utf-8') as f:
            try:
                combined_mapping = json.load(f)
            except json.JSONDecodeError:
                pass
            
    # Add step3 mappings properly
    for p, orig in normalized_mapping.items():
        combined_mapping[p] = orig
        
    with open(final_map_file, 'w', encoding='utf-8') as f:
        json.dump(combined_mapping, f, ensure_ascii=False, indent=4)
        
    final_map_txt = os.path.join(target_dir, "final_mapping_table.txt")
    with open(final_map_txt, 'w', encoding='utf-8') as f:
        for p, orig in combined_mapping.items():
            f.write(f"{p}: {orig}\n")
        
    print(f"Step 3 complete. Processed {processed_files} files.")
    print(f"Redacted txts in: {output_dir}")
    print(f"Final combined mapping table in: {final_map_file}")
    print(f"Final read-only mapping table in: {final_map_txt}")

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\user\변환자료\이경헌"
    apply_step3(target_dir)
