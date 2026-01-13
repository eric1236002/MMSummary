import os
from datasets import load_dataset

def save_samples(dataset_name, subset, split, num_samples=3):
    print(f"Downloading {dataset_name} dataset...")
    try:
        dataset = load_dataset(dataset_name, subset, split=split)
    except Exception as e:
        print(f"Download failed: {e}")
        return

    # Create directories
    base_path = os.path.join("cli", "test_data", dataset_name.split("/")[-1])
    source_dir = os.path.join(base_path, "source")
    reference_dir = os.path.join(base_path, "reference")
    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(reference_dir, exist_ok=True)

    # Get field names (specific to kmfoda/booksum)
    if "booksum" in dataset_name:
        text_key = "chapter"
        summary_key = "summary"
    else:
        text_key = "dialogue" if "samsum" in dataset_name else "transcript"
        summary_key = "summary"

    for i in range(min(num_samples, len(dataset))):
        sample = dataset[i]
        
        # Get content
        source_text = sample[text_key]
        reference_text = sample[summary_key]
        
        # Handle BookSum summary if it's a dict
        if isinstance(reference_text, dict):
            reference_text = reference_text.get("text", str(reference_text))

        # Save original text
        source_file = os.path.join(source_dir, f"sample_{i+1}.txt")
        with open(source_file, "w", encoding="utf-8") as f:
            f.write(source_text)
            
        # Save reference summary
        ref_file = os.path.join(reference_dir, f"sample_{i+1}.txt")
        with open(ref_file, "w", encoding="utf-8") as f:
            f.write(reference_text)
            
        print(f"Saved {dataset_name} sample {i+1} to {base_path}")

if __name__ == "__main__":
    # Download BookSum
    save_samples("kmfoda/booksum", None, "test", num_samples=3)

    print("\nDownload complete!")
    print("Test instructions:")
    print("1. Generate summary: python cli/cli.py --file cli/test_data/booksum/source/sample_1.txt --output_dir cli/output/")
    print("2. Evaluate data: python cli/eval.py --orginal_file cli/test_data/booksum/reference/sample_1.txt --summary_file cli/output/sample_1.txt --output_dir cli/eval_result.txt")
    print("3. LLM judge: python cli/llm_judge.py --original_file cli/test_data/booksum/source/sample_1.txt --summary_file cli/output/sample_1.txt")

