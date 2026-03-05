import os
import sys
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Run the full anonymization pipeline")
    parser.add_argument("target_dir", help="The directory containing the files to process")
    parser.add_argument("--finalize", action="store_true", help="Run ONLY Phase 3 (Final Redaction & text PDF Gen) using the reviewed mapping table")
    parser.add_argument("--inplace", action="store_true", help="Run ONLY Phase 4 (In-place redaction on original PDF/HWP files)")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.target_dir)

    if not os.path.exists(target_dir):
        print(f"Error: Directory '{target_dir}' does not exist.")
        sys.exit(1)
        
    if not os.path.isdir(target_dir):
        print(f"Error: Path '{target_dir}' is not a directory.")
        sys.exit(1)

    print("="*60)
    print(f"Starting Anonymization Pipeline for: {target_dir}")
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if args.finalize:
        print("\n[Phase 3] Running Final Redaction & PDF Generation...")
        step3_script = os.path.join(script_dir, "step3_final_redaction.py")
        
        if not os.path.exists(step3_script):
            print(f"Error: Could not find {step3_script}")
            sys.exit(1)
            
        result3 = subprocess.run([sys.executable, step3_script, target_dir])
        if result3.returncode != 0:
            print("\n❌ Phase 3 failed.")
            sys.exit(result3.returncode)
            
        print("\n" + "="*60)
        print("Pipeline Phase 3 Completed Successfully!")
        print(f"Final output: Check the 'step3_final_output' folder inside '{target_dir}'")
        print("="*60)
        return
        
    if args.inplace:
        print("\n[Phase 4] Running In-place Document Redaction...")
        step4_script = os.path.join(script_dir, "step4_inplace_redaction.py")
        
        if not os.path.exists(step4_script):
            print(f"Error: Could not find {step4_script}")
            sys.exit(1)
            
        result4 = subprocess.run([sys.executable, step4_script, target_dir])
        if result4.returncode != 0:
            print("\n❌ Phase 4 failed.")
            sys.exit(result4.returncode)
            
        print("\n" + "="*60)
        print("Pipeline Phase 4 Completed Successfully!")
        print(f"Final output: Check the 'step4_inplace_output' folder inside '{target_dir}'")
        print("="*60)
        return

    # ---------------------------------------------------------
    # Run Step 0: Document Conversion
    # ---------------------------------------------------------
    print("\n[Phase 0] Running Document Conversion...")
    step0_script = os.path.join(script_dir, "step0_document_conversion.py")
    
    if os.path.exists(step0_script):
        result0 = subprocess.run([sys.executable, step0_script, target_dir])
        if result0.returncode != 0:
            print("\n❌ Phase 0 failed. Aborting pipeline.")
            sys.exit(result0.returncode)
    else:
        print(f"Warning: Could not find {step0_script}. Skipping document conversion.")
    
    # ---------------------------------------------------------
    # Run Step 1: Regex Redaction
    # ---------------------------------------------------------
    print("\n[Phase 1] Running Regex Redaction & Boilerplate Removal...")
    step1_script = os.path.join(script_dir, "step1_redaction.py")
    
    if not os.path.exists(step1_script):
        print(f"Error: Could not find {step1_script}")
        sys.exit(1)
        
    result1 = subprocess.run([sys.executable, step1_script, target_dir])
    
    if result1.returncode != 0:
        print("\n❌ Phase 1 failed. Aborting pipeline.")
        sys.exit(result1.returncode)

    # ---------------------------------------------------------
    # Run Step 2: LLM Candidate Extraction
    # ---------------------------------------------------------
    print("\n[Phase 2] Running LLM Context-Aware Candidate Extraction...")
    step2_script = os.path.join(script_dir, "step2_candidate_extract.py")
    
    if not os.path.exists(step2_script):
        print(f"Error: Could not find {step2_script}")
        sys.exit(1)
        
    result2 = subprocess.run([sys.executable, step2_script, target_dir])

    if result2.returncode != 0:
        print("\n❌ Phase 2 failed.")
        sys.exit(result2.returncode)

    # ---------------------------------------------------------
    # Pipeline Completion
    print("\n" + "="*60)
    print("Pipeline Phase 0-2 Completed Successfully!")
    print(f"Step 0 Output: Raw text in 'extracted_text' folder")
    print(f"Step 1 Output: Redacted text in 'step1_output' folder")
    print(f"Step 2 Output: LLM Candidates in 'candidates.json'")
    print("-" * 60)
    print("NEXT STEP: Please run the Review Dashboard to confirm candidates:")
    print(f"   python review_dashboard.py \"{target_dir}\"")
    print("AFTER REVIEW: Run this pipeline again with the --finalize flag (for text->PDF):")
    print(f"   python run_pipeline.py \"{target_dir}\" --finalize")
    print("OR run with the --inplace flag (for original document redaction):")
    print(f"   python run_pipeline.py \"{target_dir}\" --inplace")
    print("="*60)

if __name__ == "__main__":
    main()
