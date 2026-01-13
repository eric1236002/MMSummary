from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import os,argparse
def calculate_rouge_scores(original, summary):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(original, summary)
    return scores

def calculate_stats(original, summary):
    return {
        "original_len": len(original),
        "summary_len": len(summary),
        "compression_ratio": round(len(summary) / len(original), 4) if len(original) > 0 else 0
    }

def calculate_bleu_score(original, summary):
    # Split text into word lists
    reference = [original.split()]
    candidate = summary.split()
    # Calculate BLEU score
    smoothing = SmoothingFunction().method1
    score = sentence_bleu(reference, candidate, smoothing_function=smoothing)
    return score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orginal_file", type=str, default=None, help="Input original file")
    parser.add_argument("--summary_file", type=str, default=None, help="Input summary file")
    parser.add_argument("--output_dir", type=str, default=None, help="output path")
    args=parser.parse_args()



    with open(args.orginal_file, "r",encoding="utf-8") as f:
        original = f.read()
    
    with open(args.summary_file, "r",encoding="utf-8") as f:
        summary = f.read()

    rouge_scores = calculate_rouge_scores(original, summary)
    bleu_score = calculate_bleu_score(original, summary)
    stats = calculate_stats(original, summary)
            
    with open(args.output_dir, "a+", encoding="utf-8") as f:
        f.write("\n" + "="*50 + "\n")
        f.write(f"File: {os.path.basename(args.summary_file)}\n")
        
        f.write("\n[Text Stats]\n")
        for key, val in stats.items():
            f.write(f"{key}: {val}\n")
            print(f"{key}: {val}")

        f.write("\n[ROUGE Scores]\n")
        print("\nROUGE Scores:")
        for key, score in rouge_scores.items():
            line = f"{key}: Precision={score.precision:.4f}, Recall={score.recall:.4f}, F1={score.fmeasure:.4f}"
            f.write(line + "\n")
            print(line)
            
        f.write(f"\nBLEU Score: {bleu_score:.4f}\n")
        print(f"BLEU Score: {bleu_score:.4f}")
if __name__ == "__main__":
    main()
