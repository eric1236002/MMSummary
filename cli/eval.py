from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import os,argparse
def calculate_rouge_scores(original, summary):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    scores = scorer.score(" ".join(original), " ".join(summary))
    return scores

def calculate_bleu_score(original, summary):
    # split text into word list
    reference = [original.split()]
    candidate = summary.split()
    # calculate BLEU score
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
            
    with open(args.output_dir, "a+", encoding="utf-8") as f:
        f.write("\n")
        f.write(f"file: {args.summary_file.split('/')[-1].split('.')[0]} \nROUGE Scores:\n")
        print("ROUGE Scores:")
        for key, score in rouge_scores.items():
            f.write(f"{key}: {score}\n")
            print(f"{key}: {score}")
        f.write(f"BLEU Score: {bleu_score}\n")
        print(f"BLEU Score: {bleu_score}")
if __name__ == "__main__":
    main()
