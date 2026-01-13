import os
import argparse
import sys
# Import backend init_llm for consistency
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.core import init_llm
from langchain.prompts import PromptTemplate

JUDGE_PROMPT = """
You are a professional summarization quality evaluation expert. Please provide an objective score for the "Original Text" and the "Generated Summary" provided below.

【Original Text (Excerpt)】
{original_text}

【Generated Summary】
{summary_text}

---
Please score according to the following three dimensions (1-5 points, 5 is highest), and give a short reason:

1. **Faithfulness**: Does the summary content completely align with the original text? Are there any fabricated facts or hallucinations?
2. **Relevance**: Does the summary include all key points from the original text? Does it contain irrelevant information?
3. **Coherence**: Is the summary itself smooth, logically clear, and easy to read?

Finally, please provide an **Overall Score**.

Please strictly output in the following JSON format:
{{
    "faithfulness": {{ "score": 0, "reason": "" }},
    "relevance": {{ "score": 0, "reason": "" }},
    "coherence": {{ "score": 0, "reason": "" }},
    "overall_score": 0,
    "final_verdict": ""
}}
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original_file", type=str, required=True, help="Path to original text file")
    parser.add_argument("--summary_file", type=str, required=True, help="Path to generated summary file")
    parser.add_argument("--model", type=str, default="gpt-5.2", help="Model to use as judge")
    parser.add_argument("--output_dir", type=str, default="cli/all_eval_results.txt", help="Output result path")
    args = parser.parse_args()

    # Read files
    with open(args.original_file, "r", encoding="utf-8") as f:
        original = f.read()
    with open(args.summary_file, "r", encoding="utf-8") as f:
        summary = f.read()

    print(f"Using {args.model} for evaluation...")
    
    # Initialize Judge LLM
    llm = init_llm(temperature=0, model=args.model, max_tokens=2000)
    
    prompt = PromptTemplate.from_template(JUDGE_PROMPT)
    chain = prompt | llm
    
    try:
        # Increase extraction length to prevent Judge from missing later parts of the text
        response = chain.invoke({
            "original_text": original, 
            "summary_text": summary
        })
        
        result_text = response.content
        
        # Write to result file in append mode
        with open(args.output_dir, "a+", encoding="utf-8") as f:
            f.write("\n[LLM-as-a-Judge Score]\n")
            f.write(result_text + "\n")
            
        print("\n=== Evaluation Results ===")
        print(result_text)
        print(f"\nResult appended to: {args.output_dir}")
        
    except Exception as e:
        print(f"An error occurred during evaluation: {e}")

if __name__ == "__main__":
    main()

