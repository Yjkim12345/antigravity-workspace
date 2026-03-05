import os
import glob
import re
import json
from collections import OrderedDict, defaultdict

# Global Mapping Table for Step 1
mapping_table = OrderedDict()
counters = defaultdict(lambda: 1)

def get_placeholder(type_val, original_text):
    global mapping_table, counters
    # Check if original_text already has a placeholder
    for placeholder, original in mapping_table.items():
        if original == original_text:
            return placeholder
    
    # Create new placeholder
    cnt = counters[type_val]
    placeholder = f"[{type_val} {cnt}]"
    counters[type_val] += 1
    mapping_table[placeholder] = original_text
    return placeholder

def load_rules():
    rules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anonymization_rules.json")
    if not os.path.exists(rules_path):
        print(f"Error: {rules_path} not found.")
        return {"deletions": [], "replacements": []}
    with open(rules_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def apply_format_redaction(text, rules):
    redacted = text
    
    # 1. Apply Deletions (Boilerplates)
    for del_pattern in rules.get("deletions", []):
        redacted = re.sub(del_pattern, '', redacted, flags=re.DOTALL)
        
    # 2. Apply Replacements
    for rule in rules.get("replacements", []):
        tag = rule.get("tag")
        
        # Apply regex rules
        for pattern in rule.get("regex", []):
            # Using re.finditer to avoid overlapping matches infinite loops
            for match in re.finditer(pattern, redacted):
                original = match.group(1) if match.groups() else match.group(0)
                ph = get_placeholder(tag, original)
                redacted = redacted.replace(original, ph)
                
        # Apply literal string rules
        for literal in rule.get("literals", []):
            if literal in redacted:
                ph = get_placeholder(tag, literal)
                redacted = redacted.replace(literal, ph)

    return redacted

def main(target_dir):
    input_dir = os.path.join(target_dir, "extracted_text")
    output_dir = os.path.join(target_dir, "step1_output")
    os.makedirs(output_dir, exist_ok=True)
    
    txt_files = glob.glob(os.path.join(input_dir, '*.txt'))
    print(f"Phase 1 Redacting {len(txt_files)} files...")
    
    rules = load_rules()
    
    for txt_path in txt_files:
        filename = os.path.basename(txt_path)
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        redacted_text = apply_format_redaction(text, rules)
        
        out_path = os.path.join(output_dir, filename.replace('.txt', '_step1.txt'))
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(redacted_text)
            
    # Save Mapping Table
    map_path = os.path.join(output_dir, "step1_mapping.json")
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_table, f, ensure_ascii=False, indent=4)
        
    print(f"Phase 1 Redaction complete. Output saved to {output_dir}")
    print(f"Mapping table saved to {map_path}")

if __name__ == '__main__':
    import sys
    target_dir = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\user\변환자료\이경헌"
    main(target_dir)
