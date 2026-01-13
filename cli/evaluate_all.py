import os
import subprocess
import glob
import sys

def main():
    summary_dir = os.path.join("cli", "output")
    reference_dir = os.path.join("cli", "test_data", "booksum", "reference")
    source_dir = os.path.join("cli", "test_data", "booksum", "source") # New source path
    eval_script = os.path.join("cli", "eval.py")
    judge_script = os.path.join("cli", "llm_judge.py") # New judge script path
    results_file = os.path.join("cli", "all_eval_results.txt")

    # Use current Python path to ensure subprocess finds venv packages
    python_exe = sys.executable

    # Delete existing results file to ensure fresh results
    if os.path.exists(results_file):
        os.remove(results_file)

    # Get all generated summary files
    summary_files = glob.glob(os.path.join(summary_dir, "*.txt"))
    
    if not summary_files:
        print(f"No .txt files found in {summary_dir}.")
        return

    print(f"Found {len(summary_files)} summary files, starting evaluation...")

    for summary_path in summary_files:
        base_name = os.path.basename(summary_path)
        
        # Assume file name format is sample_1_...
        # Map to reference file sample_1.txt
        sample_id = base_name.split("_")[0] + "_" + base_name.split("_")[1] # Get "sample_1"
        ref_path = os.path.join(reference_dir, f"{sample_id}.txt")

        if not os.path.exists(ref_path):
            print(f"Skipping {base_name}: Reference file not found {ref_path}")
            continue

        # 1. Execute numerical evaluation (ROUGE/BLEU)
        print(f"Executing numerical evaluation for {base_name} ...")
        cmd_eval = [
            python_exe, eval_script,
            "--orginal_file", ref_path,
            "--summary_file", summary_path,
            "--output_dir", results_file
        ]
        
        try:
            subprocess.run(cmd_eval, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during numerical evaluation for {base_name}: {e}")

        # 2. Execute LLM-as-a-Judge evaluation
        # Find original text path (e.g. cli/test_data/booksum/source/sample_1.txt)
        source_path = os.path.join(source_dir, f"{sample_id}.txt")
        if os.path.exists(source_path):
            print(f"Executing LLM judge for {base_name} ...")
            cmd_judge = [
                python_exe, judge_script,
                "--original_file", source_path,
                "--summary_file", summary_path,
                "--output_dir", results_file
            ]
            try:
                subprocess.run(cmd_judge, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error during LLM judge for {base_name}: {e}")
        else:
            print(f"Skipping LLM judge: Original file not found {source_path}")

    print(f"\nEvaluation complete! Check results in: {results_file}")

if __name__ == "__main__":
    main()

